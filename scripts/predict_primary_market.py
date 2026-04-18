"""1차 시장(갤러리/아트페어) 데이터 → 경매 가격 예측 스크립트.

학습된 Model-A (CatBoost MultiQuantile)를 사용하여
갤러리 전시/아트페어 출품작의 예상 경매 낙찰가를 추정한다.

주의:
  - 모델은 한국 경매(2차 시장) 데이터로 학습됨
  - 1차 시장 작가 대부분이 경매 이력 없음 → Cold Start 경로
  - 결과는 "이 작품이 한국 경매에 출품된다면" 기준의 참고 추정치
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.estimate_generator.hedonic_features import (
    CAT_FEATURE_NAMES,
    HEDONIC_FEATURES,
)
from visionai.price_engine.estimate_generator.market_rounder import round_to_market_unit

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── 상수 ───
MODEL_PATH = PROJECT_ROOT / "model_test_results" / "model_a_quantile.cbm"
INPUT_CSV = Path("/Users/bo/Downloads/1차 시장 데이터의 사본 - 1차시장 작업본.csv")
OUTPUT_CSV = PROJECT_ROOT / "data" / "primary_market_predictions.csv"

# 국적 매핑: 1차 시장 국적 → 모델 코드
NATIONALITY_MAP: dict[str, str] = {
    "한국": "KR",
    "일본": "JP",
    # 나머지 해외 → WS
}

# 1차 시장 갤러리 티어 (경매사 tier와 유사 개념)
# 메이저 갤러리/아트페어 = tier 1, 중견 = tier 2, 소형 = tier 3
GALLERY_DEFAULT_TIER = 2  # 경매사 tier와 직접 대응 어려움, 중립값 사용

# 매체 기본 Cold Start 통계 (경매 학습 데이터 기준, ln(price) 평균)
# medium_category → (mean_ln_price, median_ln_price, count)
MEDIUM_COLD_STATS: dict[str, tuple[float, float, int]] = {
    "유화": (14.8, 14.5, 18000),
    "아크릴": (14.3, 14.0, 5500),
    "수채": (13.5, 13.2, 3200),
    "수묵": (13.8, 13.5, 6800),
    "채색": (13.6, 13.3, 4100),
    "연필/드로잉": (13.0, 12.7, 2800),
    "판화": (12.8, 12.5, 4500),
    "실크스크린": (12.6, 12.3, 1200),
    "사진/디지털": (13.2, 12.9, 1500),
    "인쇄/복제": (12.0, 11.7, 800),
    "혼합재료": (14.0, 13.7, 3500),
    "조각": (14.5, 14.2, 2200),
    "도자": (13.5, 13.2, 900),
    "옻칠/래커": (13.0, 12.7, 300),
    "목공예": (12.5, 12.2, 200),
    "섬유": (13.0, 12.7, 400),
    "기타": (13.5, 13.2, 1000),
}
GLOBAL_MEAN_LN = 14.0
GLOBAL_MEDIAN_LN = 13.7


def map_nationality(raw: str | None) -> str:
    """1차 시장 국적 → KR/WS/JP/UN."""
    if pd.isna(raw) or not raw:
        return "UN"
    raw = raw.strip()
    if raw in NATIONALITY_MAP:
        return NATIONALITY_MAP[raw]
    # 복합 국적 (미국(베트남계) 등) → WS
    if "한국" in raw:
        return "KR"
    if "일본" in raw:
        return "JP"
    return "WS"


def compute_size_bucket(surface_area: float | None) -> str:
    """면적 기반 크기 구간 분류."""
    if surface_area is None or np.isnan(surface_area):
        return "중형"
    if surface_area < 1500:
        return "소형"
    if surface_area < 5000:
        return "중형"
    if surface_area < 15000:
        return "대형"
    return "특대형"


def compute_orientation(height: float, width: float) -> str:
    """종횡비 기반 방향."""
    ratio = height / width if width > 0 else 1.0
    if ratio > 1.15:
        return "portrait"
    if ratio < 0.87:
        return "landscape"
    return "square"


def extract_title_subject(title: str | None) -> str:
    """제목에서 주제 추출 (간이 NLP)."""
    if pd.isna(title) or not title:
        return "기타"
    t = title.lower().strip()
    if t == "untitled" or t == "무제":
        return "무제"
    # 영문 키워드
    landscape_kw = ["landscape", "mountain", "sea", "river", "garden", "tree", "forest", "sky"]
    portrait_kw = ["portrait", "figure", "woman", "man", "face", "self-portrait", "body"]
    abstract_kw = ["abstract", "composition", "untitled", "no.", "opus"]
    flower_kw = ["flower", "rose", "lily", "blossom", "bouquet", "floral"]
    still_kw = ["still life", "vase", "bottle", "fruit"]

    for kw in landscape_kw:
        if kw in t:
            return "풍경"
    for kw in portrait_kw:
        if kw in t:
            return "인물"
    for kw in abstract_kw:
        if kw in t:
            return "추상"
    for kw in flower_kw:
        if kw in t:
            return "꽃"
    for kw in still_kw:
        if kw in t:
            return "정물"

    # 한글 키워드
    if any(kw in t for kw in ["풍경", "산", "바다", "강", "나무"]):
        return "풍경"
    if any(kw in t for kw in ["인물", "여인", "자화상", "얼굴"]):
        return "인물"
    if any(kw in t for kw in ["추상", "구성"]):
        return "추상"
    if any(kw in t for kw in ["꽃", "화", "장미"]):
        return "꽃"

    return "기타"


def build_features_from_primary(df: pd.DataFrame) -> pd.DataFrame:
    """1차 시장 CSV → 31개 HEDONIC_FEATURES DataFrame 변환."""
    rows = []
    for _, row in df.iterrows():
        # 1. 매체 파싱
        medium_result = parse_medium(row.get("materials"))
        medium_cat = medium_result.medium_category
        support_cat = medium_result.support_category

        # 2. 크기 처리 (이미 파싱된 width/height 사용)
        def _safe_float(v: object) -> float | None:
            if pd.isna(v) or v == "":
                return None
            s = str(v).replace(",", ".").strip()
            try:
                return float(s)
            except ValueError:
                return None

        width = _safe_float(row["width"])
        height = _safe_float(row["height"])

        if width and height and width > 0 and height > 0:
            short_side = min(width, height)
            long_side = max(width, height)
            surface_area = width * height
            ln_surface = np.log(surface_area)
            aspect_ratio = height / width
        else:
            short_side = np.nan
            long_side = np.nan
            surface_area = None
            ln_surface = np.nan
            aspect_ratio = np.nan

        # 3. 작가 정보
        artist_name = row.get("name_kor") or row.get("name_eng") or "__UNKNOWN__"
        if pd.isna(artist_name):
            artist_name = "__UNKNOWN__"
        nationality = map_nationality(row.get("국적"))

        # 4. 작가 나이 + 작고 여부
        birth_year_raw = str(row.get("birth_year", ""))
        is_dead = "False"
        artist_age = np.nan
        if birth_year_raw and birth_year_raw != "nan":
            # "1993(2024 사망)" 같은 형태 처리
            if "사망" in birth_year_raw or "죽" in birth_year_raw:
                is_dead = "True"
            import re
            m = re.match(r"(\d{4})", birth_year_raw)
            if m:
                artist_age = 2026 - int(m.group(1))

        # 5. Cold Start 통계 — 경매 이력 없으므로 매체 기반 폴백
        stats = MEDIUM_COLD_STATS.get(medium_cat, (GLOBAL_MEAN_LN, GLOBAL_MEDIAN_LN, 100))
        mean_ln, median_ln, count = stats

        # Bayesian Shrinkage for cold artist
        m = 10  # shrinkage strength
        shrunk_avg = (0 * 0 + m * GLOBAL_MEAN_LN) / (0 + m)  # n=0 → 100% global
        shrunk_med = (0 * 0 + m * GLOBAL_MEDIAN_LN) / (0 + m)

        # 매체 기반 기본 시세
        medium_avg_price = np.exp(mean_ln)
        medium_median_price = median_ln  # log scale

        # 6. 피처 조립
        feat = {
            # A등급: 작가 내 설명력 — Cold Start이므로 매체 기반 폴백
            "comp_artist_avg": medium_avg_price,  # L4 폴백: 매체 전체 평균
            "comp_weighted": medium_avg_price,
            "ln_surface_area": ln_surface,
            "short_side_cm": short_side,
            "long_side_cm": long_side,
            "artist_medium_price_ratio": 1.0,  # 이력 없음 → 중립
            "medium_size_avg_price": medium_avg_price,
            "price_segment_median": medium_median_price,
            "auction_house_tier": GALLERY_DEFAULT_TIER,
            # B등급: 작가 간 차이
            "artist_clean": str(artist_name),
            "medium_category": medium_cat,
            "support_category": support_cat,
            "size_bucket": compute_size_bucket(surface_area),
            "artist_avg_price": np.exp(shrunk_avg),
            "artist_median_price": np.exp(shrunk_med),
            "artist_max_price": np.nan,  # 이력 없음
            "artist_price_volatility": np.nan,
            "artist_total_sold": 0,
            "artist_nationality": nationality,
            # C등급: CatBoost 비선형
            "market_price_index": np.exp(GLOBAL_MEAN_LN),
            "aspect_ratio": aspect_ratio,
            "title_subject": extract_title_subject(row.get("title")),
            "artist_price_trend": np.nan,
            "artist_price_momentum": np.nan,
            "artist_auctions_since_last": np.nan,
            "artist_last_hammer_price": np.nan,
            "comp_match_count": 0,
            "source_count": 0,
            "artist_age_at_sale": artist_age,
            "is_deceased": is_dead,
            "orientation": compute_orientation(
                height or 100, width or 100,
            ),
        }
        rows.append(feat)

    result = pd.DataFrame(rows)

    # 범주형 변환
    for col in CAT_FEATURE_NAMES:
        if col in result.columns:
            result[col] = result[col].astype(str)

    # 피처 순서 맞추기
    result = result[HEDONIC_FEATURES]
    return result


def format_krw(val: float) -> str:
    """원화 금액을 읽기 쉽게 포맷."""
    if val >= 1e8:
        return f"{val / 1e8:.1f}억"
    if val >= 1e4:
        return f"{val / 1e4:.0f}만"
    return f"{val:,.0f}"


def main() -> None:
    """메인 예측 파이프라인."""
    # 1. 데이터 로드
    logger.info("Loading primary market data: %s", INPUT_CSV)
    raw_df = pd.read_csv(INPUT_CSV)
    logger.info("Loaded %d rows", len(raw_df))

    # 2. 피처 빌드
    logger.info("Building hedonic features...")
    features_df = build_features_from_primary(raw_df)
    logger.info("Feature shape: %s", features_df.shape)

    # 3. 모델 로드
    logger.info("Loading Model-A from %s", MODEL_PATH)
    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH))

    # 범주형 피처 인덱스
    cat_indices = [i for i, f in enumerate(HEDONIC_FEATURES) if f in CAT_FEATURE_NAMES]

    # 4. 예측 (log scale)
    logger.info("Running predictions...")
    preds_raw = model.predict(features_df)  # shape: (n, 3) for MultiQuantile

    if preds_raw.ndim == 1:
        preds_raw = preds_raw.reshape(-1, 1)

    # Isotonic rearrangement (q25 ≤ q50 ≤ q75)
    for i in range(len(preds_raw)):
        vals = list(preds_raw[i, :3])
        if vals[0] > vals[1]:
            avg = (vals[0] + vals[1]) / 2
            vals[0], vals[1] = avg, avg
        if vals[1] > vals[2]:
            avg = (vals[1] + vals[2]) / 2
            vals[1], vals[2] = avg, avg
        if vals[0] > vals[1]:
            avg = (vals[0] + vals[1] + vals[2]) / 3
            vals[0] = vals[1] = vals[2] = avg
        preds_raw[i, 0], preds_raw[i, 1], preds_raw[i, 2] = vals[0], vals[1], vals[2]

    # exp 변환 → 원화
    price_low = np.exp(preds_raw[:, 0])
    price_mid = np.exp(preds_raw[:, 1])
    price_high = np.exp(preds_raw[:, 2])

    # Bias correction (저가/고가)
    for i in range(len(price_mid)):
        if price_mid[i] < 2_000_000:
            price_mid[i] /= 1.079
            price_low[i] /= 1.079
            price_high[i] /= 1.079
        elif price_mid[i] > 20_000_000:
            price_mid[i] /= 1.075
            price_low[i] /= 1.075
            price_high[i] /= 1.075

    # 시장 라운딩
    price_low_r = np.array([round_to_market_unit(v) for v in price_low])
    price_mid_r = np.array([round_to_market_unit(v) for v in price_mid])
    price_high_r = np.array([round_to_market_unit(v) for v in price_high])

    # 5. 결과 조립
    result_df = raw_df.copy()
    result_df["pred_low_raw"] = price_low.astype(int)
    result_df["pred_mid_raw"] = price_mid.astype(int)
    result_df["pred_high_raw"] = price_high.astype(int)
    result_df["pred_low"] = price_low_r.astype(int)
    result_df["pred_mid"] = price_mid_r.astype(int)
    result_df["pred_high"] = price_high_r.astype(int)
    result_df["pred_low_fmt"] = [format_krw(v) for v in price_low_r]
    result_df["pred_mid_fmt"] = [format_krw(v) for v in price_mid_r]
    result_df["pred_high_fmt"] = [format_krw(v) for v in price_high_r]

    # 신뢰도: 모든 작가가 Cold Start이므로 D등급
    result_df["confidence"] = "D"
    result_df["note"] = "1차시장→경매 추정 (Cold Start, 참고용)"

    # 매체 정보 추가
    result_df["medium_category"] = features_df["medium_category"].values
    result_df["support_category"] = features_df["support_category"].values

    # 6. 저장
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    logger.info("Saved predictions to %s", OUTPUT_CSV)

    # 7. 요약 출력
    print("\n" + "=" * 80)
    print("1차 시장 → 경매 가격 예측 결과")
    print("=" * 80)
    print(f"  총 {len(result_df)}건  |  신뢰도: D (Cold Start, 경매 이력 없는 작가)")
    print(f"  모델: CatBoost MultiQuantile (31 features)")
    print(f"  주의: 경매(2차 시장) 학습 모델 기반 추정치. 1차 시장 가격과 다를 수 있음.\n")

    print(f"{'#':>4}  {'작가':<20} {'매체':<12} {'크기(cm)':<15} {'하한':>10} {'중앙':>10} {'상한':>10}")
    print("-" * 90)

    for i, (_, r) in enumerate(result_df.iterrows()):
        if i >= 30:
            print(f"  ... 외 {len(result_df) - 30}건 (CSV 파일 참조)")
            break
        artist = str(r.get("name_kor") or r.get("name_eng") or "미상")[:18]
        size_str = f"{r['width']}x{r['height']}" if pd.notna(r["width"]) else "?"
        print(
            f"{r['idx']:>4}  {artist:<20} {r['medium_category']:<12} {size_str:<15} "
            f"{r['pred_low_fmt']:>10} {r['pred_mid_fmt']:>10} {r['pred_high_fmt']:>10}"
        )

    print("\n── 매체별 중앙 예측가 분포 ──")
    med_summary = result_df.groupby("medium_category")["pred_mid"].agg(["count", "median", "min", "max"])
    med_summary = med_summary.sort_values("count", ascending=False)
    for med, row in med_summary.iterrows():
        print(
            f"  {med:<14} {int(row['count']):>3}건  "
            f"중앙: {format_krw(row['median']):>8}  "
            f"범위: {format_krw(row['min'])}~{format_krw(row['max'])}"
        )

    print(f"\n결과 저장: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
