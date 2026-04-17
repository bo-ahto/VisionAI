"""추정가-독립 23개 피처 빌더.

기존 파서 + artist_stats_snapshot + hedonic_stats를 통합하여
추정가 없이도 동작하는 피처셋을 생성한다.

Phase 3 추정가 생성 엔진 전용.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from visionai.price_engine.features.artist_stats_snapshot import (
    compute_artist_stats_snapshot,
)
from visionai.price_engine.features.hedonic_stats import (
    compute_artist_auctions_since_last,
    compute_artist_career_length,
    compute_artist_last_hammer,
    compute_artist_lot_count_trend,
    compute_artist_median_price,
    compute_artist_premium_ratio,
    compute_artist_price_momentum,
    compute_artist_price_trend,
    compute_artist_price_volatility,
    compute_artist_reappear_flag,
    compute_artist_recent_avg_price,
    compute_artist_sale_frequency,
    compute_artist_unsold_rate,
    compute_auction_type_factor,
    compute_comparable_sales,
    compute_market_price_index,
    compute_medium_avg_price,
    compute_medium_x_auction_avg,
    compute_size_ho,
    compute_size_ho_above40,
)
from visionai.price_engine.features.splits import assign_split_4way
from visionai.price_engine.preprocessing.dimension_parser import parse_dimension
from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.preprocessing.year_parser import parse_year

logger = logging.getLogger(__name__)

# Hedonic 피처 목록 (총 50개, 추정가 4개 제외).
# 순서 계약: 범주형 인덱스 = [0, 1, 2, 3, 4, 37, 41, 42, 49]
# (test_quantile_model::test_cat_feature_indices 및 HEDONIC_CAT_INDICES가 의존)
HEDONIC_FEATURES: list[str] = [
    # ── 0-4: 선두 범주형 (5 cat) ──
    "artist_clean",              # 0  작가 ID (cat)
    "medium_category",           # 1  매체 17분류 (cat)
    "support_category",          # 2  지지체 8분류 (cat)
    "is_3d",                     # 3  3D 여부 (cat bool)
    "is_untitled",               # 4  무제 플래그 (cat bool)
    # ── 5-36: 수치형 중심 블록 (32 num) ──
    "artist_avg_price",          # 5  작가 평균가
    "artist_median_price",       # 6  작가 중앙가 (shrinkage)
    "artist_max_price",          # 7  작가 최고가
    "artist_price_volatility",   # 8  작가 변동성
    "artist_total_sold",         # 9  작가 거래 건수
    "is_new_artist",             # 10 신규 작가 플래그
    "is_deceased",               # 11 작고 여부 (0/1)
    "artist_birth_year",         # 12 작가 출생 연도
    "artist_age_at_sale",        # 13 작가 나이
    "artist_medium_price_ratio", # 14 작가×매체 가격비
    "artist_medium_frequency",   # 15 작가×매체 출품 빈도
    "medium_size_avg_price",     # 16 매체×크기 평균가
    "medium_avg_price",          # 17 매체 평균가 (cutoff 이전)
    "price_segment_median",      # 18 매체별 기준가 (train split만)
    "auction_house_tier",        # 19 경매사 등급
    "ln_surface_area",           # 20 log 표면적
    "short_side_cm",             # 21 단변 크기
    "long_side_cm",              # 22 장변 크기
    "size_ho",                   # 23 호 환산 크기
    "size_ho_above40",           # 24 40호 초과 구간
    "aspect_ratio",              # 25 종횡비
    "market_price_index",        # 26 시장 시계열 앵커
    "artist_price_trend",        # 27 작가 추세
    "artist_price_momentum",     # 28 작가 모멘텀
    "artist_auctions_since_last",# 29 마지막 거래 경과
    "artist_last_hammer_price",  # 30 최근 낙찰가
    "artist_recent_avg_price",   # 31 최근 N회 작가 평균가
    "artist_sale_frequency",     # 32 연간 출품 빈도
    "artist_lot_count_trend",    # 33 작가 출품량 추세
    "artist_career_length",      # 34 작가 커리어 기간
    "artist_unsold_rate",        # 35 작가 유찰률
    "comp_artist_avg",           # 36 비교 작가 평균가
    # ── 37: 범주형 ──
    "title_subject",             # 37 주제 카테고리 (cat)
    # ── 38-40: 수치형 (3 num) ──
    "comp_weighted",             # 38 비교 매출 가중
    "comp_match_count",          # 39 비교 매칭 건수
    "comp_medium_avg",           # 40 비교 매체 평균
    # ── 41-42: 범주형 2개 ──
    "size_bucket",               # 41 크기 구간 (cat)
    "orientation",               # 42 방향 (cat)
    # ── 43-48: 수치형 (6 num) ──
    "comp_to_avg_ratio",         # 43 비교가-작가평균 비율
    "comp_match_level",          # 44 매칭 단계(1~4)
    "source_count",              # 45 출품 경매사 수
    "global_median_price",       # 46 글로벌 시장 중앙가
    "global_auction_count",      # 47 글로벌 경매 건수
    "has_global_price",          # 48 글로벌 데이터 가용 플래그
    # ── 49: 범주형 ──
    "artist_nationality",        # 49 작가 국적 KR/WS (cat)
]

CAT_FEATURE_NAMES: list[str] = [
    "artist_clean",
    "medium_category",
    "support_category",
    "is_3d",
    "is_untitled",
    "title_subject",
    "size_bucket",
    "orientation",
    "artist_nationality",
]


def _apply_parsers(df: pd.DataFrame) -> pd.DataFrame:
    """파서 3종을 적용하여 파생 컬럼을 추가한다.

    통합 스키마, 레거시, 클렌징 데이터 모두 지원.
    클렌징 데이터(medium_category 이미 존재)면 파서 스킵.
    """
    out = df.copy()

    # ── 클렌징 데이터 감지: medium_category가 이미 있으면 파서 스킵 ──
    is_cleansed = "medium_category" in out.columns and "width_cm" in out.columns

    if is_cleansed:
        logger.info("Cleansed data detected — skipping parsers")
        # -1 센티넬 → NaN 변환 (크기 없음 표시 → 내부 계산에서는 NaN 필요)
        for col in ["width_cm", "height_cm", "surface_area", "ho"]:
            if col in out.columns:
                out.loc[out[col] == -1, col] = np.nan

        # 작가 정리
        artist_col = "name_kor" if "name_kor" in out.columns else "artist"
        out["artist_clean"] = out[artist_col].fillna("__UNKNOWN__")
        out.loc[out["artist_clean"].str.strip() == "", "artist_clean"] = "__UNKNOWN__"
        out.loc[out["artist_clean"].str.contains("작가미상", na=False), "artist_clean"] = "__UNKNOWN__"

        # 클렌징 데이터에 없는 파생 컬럼 보충
        if "aspect_ratio" not in out.columns:
            w = out["width_cm"].fillna(0)
            h = out["height_cm"].fillna(0)
            out["aspect_ratio"] = np.where(w > 0, h / w, np.nan)
        if "is_3d" not in out.columns:
            out["is_3d"] = False
        if "is_size_imputed" not in out.columns:
            out["is_size_imputed"] = out["surface_area"].isna()
        if "depth_cm" not in out.columns:
            out["depth_cm"] = np.nan
        # 제목 파생 (cleansed: "title" / 레거시 한국어: "제목")
        _title_col = "title" if "title" in out.columns else ("제목" if "제목" in out.columns else None)
        if _title_col is not None:
            out["is_untitled"] = out[_title_col].astype(str).str.contains(
                r"무제|Untitled|untitled", na=False, regex=True
            )
        else:
            out["is_untitled"] = False
        # 컬럼 호환
        if "price" in out.columns and "낙찰가" not in out.columns:
            out["낙찰가"] = out["price"]
        if "materials" in out.columns and "재료" not in out.columns:
            out["재료"] = out["materials"]
        return out

    # ── 기존 파이프라인: 파서 적용 ──
    # 컬럼명 호환
    _col_map = {
        "size_raw": "크기", "material": "재료", "title": "제목",
        "artist": "작가", "price": "낙찰가", "sale_date": "sale_date",
    }
    for new_name, old_name in _col_map.items():
        if new_name in out.columns and old_name not in out.columns:
            out[old_name] = out[new_name]

    # 크기 파싱
    size_col = "크기" if "크기" in out.columns else "size_raw"
    dim_results = out[size_col].apply(parse_dimension)
    out["height_cm"] = dim_results.apply(lambda r: r.height_cm)
    out["width_cm"] = dim_results.apply(lambda r: r.width_cm)
    out["surface_area"] = dim_results.apply(lambda r: r.surface_area)
    out["aspect_ratio"] = dim_results.apply(lambda r: r.aspect_ratio)
    out["is_3d"] = dim_results.apply(lambda r: r.is_3d)
    out["is_size_imputed"] = dim_results.apply(lambda r: r.is_size_imputed)
    out["depth_cm"] = dim_results.apply(lambda r: r.depth_cm)

    # 재료 파싱
    mat_col = "재료" if "재료" in out.columns else "material"
    med_results = out[mat_col].apply(parse_medium)
    out["medium_category"] = med_results.apply(lambda r: r.medium_category)
    out["support_category"] = med_results.apply(lambda r: r.support_category)

    # 제작연도 파싱
    yr_col = "제작연도" if "제작연도" in out.columns else "year_created"
    if yr_col in out.columns:
        year_results = out[yr_col].apply(parse_year)
        out["year_created"] = year_results.apply(lambda r: r.year_created)
        out["is_year_missing"] = year_results.apply(lambda r: r.is_year_missing)
    else:
        out["year_created"] = None
        out["is_year_missing"] = True

    # 제목 파생
    title_col = "제목" if "제목" in out.columns else "title"
    out["is_untitled"] = out[title_col].str.contains(
        r"무제|Untitled|untitled", na=False, regex=True
    )

    # 작가 정리
    artist_col = "작가" if "작가" in out.columns else "artist"
    out["artist_clean"] = out[artist_col].fillna("__UNKNOWN__")
    out.loc[out["artist_clean"].str.strip() == "", "artist_clean"] = "__UNKNOWN__"
    out.loc[
        out["artist_clean"].str.contains("작자미상", na=False), "artist_clean"
    ] = "__UNKNOWN__"

    return out


def _join_artist_stats_and_hedonic(
    df: pd.DataFrame,
    works_full: pd.DataFrame,
) -> pd.DataFrame:
    """각 행에 기존 작가 통계 + 신규 8개 Hedonic 피처를 조인한다.

    기존 dataset_builder._join_artist_stats 패턴과 동일한 strict cutoff 적용.
    """
    out = df.copy()
    # M1: NaN 통일이 논리적으로 올바르나 성능 검증 결과 기존 0 기본값이 더 효과적.
    # CatBoost가 0을 "미판매" 시그널로 이미 학습하고 있었으며, NaN 변경 시 오히려 악화.
    out["artist_total_sold"] = 0
    out["artist_avg_price"] = 0.0
    out["artist_max_price"] = 0.0
    out["is_new_artist"] = False
    # Phase 3 신규 피처 초기화
    out["artist_median_price"] = np.nan
    out["artist_price_trend"] = np.nan
    out["medium_avg_price"] = np.nan
    out["artist_unsold_rate"] = np.nan
    # Phase 4 신규 피처 초기화
    out["artist_recent_avg_price"] = np.nan
    out["artist_price_momentum"] = np.nan
    out["artist_sale_frequency"] = np.nan
    out["artist_auctions_since_last"] = np.nan
    out["artist_price_volatility"] = np.nan
    out["artist_lot_count_trend"] = np.nan
    out["artist_last_hammer_price"] = np.nan
    out["artist_career_length"] = np.nan
    out["market_price_index"] = 0.0
    out["comp_artist_avg"] = np.nan
    out["comp_medium_avg"] = np.nan
    out["comp_weighted"] = np.nan
    out["comp_match_count"] = 0.0
    out["comp_to_avg_ratio"] = np.nan
    out["comp_match_level"] = 4.0
    # 외부 데이터
    out["global_median_price"] = np.nan
    out["global_auction_count"] = 0.0
    # 다중 출처 신규
    out["source_count"] = 0
    # 인터랙션 피처
    out["artist_medium_price_ratio"] = 1.0
    out["artist_medium_frequency"] = 0.0
    out["medium_size_avg_price"] = np.nan

    # 글로벌 통계 로드
    from visionai.price_engine.features.hedonic_stats import load_global_artist_stats

    global_stats = load_global_artist_stats()
    if global_stats is not None:
        for col_src, col_dst in [
            ("global_median_price_krw", "global_median_price"),
            ("global_auction_count", "global_auction_count"),
        ]:
            if col_src in global_stats.columns:
                mapped = out["artist_clean"].map(
                    global_stats[col_src]
                    if col_src in global_stats.columns
                    else pd.Series(dtype="float64")
                )
                out[col_dst] = mapped.values

    # global_median_price: NaN 보존 (CatBoost가 NaN을 "미등재" 신호로 활용)
    # 대신 has_global_price 바이너리 지표 추가
    out["has_global_price"] = out["global_median_price"].notna().astype(int)
    logger.info("has_global_price: %d/%d have global data (%.1f%%)",
                 out["has_global_price"].sum(), len(out),
                 out["has_global_price"].sum() / len(out) * 100)

    # auction_house_tier: 경매사 등급 (에러 분석 기반)
    if "source" in out.columns:
        _tier_map = {
            "서울옥션": 1, "케이옥션": 1, "에이옥션": 1,           # 메이저
            "아이옥션": 2, "마이아트옥션": 2, "토탈옥션": 2,       # 중견
        }
        out["auction_house_tier"] = out["source"].map(_tier_map).fillna(3).astype(int)
    else:
        out["auction_house_tier"] = 3

    # 날짜 기반 모드 감지: sale_date 컬럼이 있으면 날짜 모드
    use_date_mode = "sale_date" in out.columns
    session_col = "sale_date" if use_date_mode else "회차"
    type_col = "source" if "source" in out.columns else "타입"
    price_col = "낙찰가" if "낙찰가" in out.columns else "price"

    # 타입 의존 제거: auction_type=None으로 전체 데이터 사용
    # 성능 최적화: 날짜 모드에서는 월 단위로 cutoff 묶기
    # (1,025 고유 날짜 → ~75 월 윈도우로 13x 속도 향상)
    # ── 최적화: 날짜순 정렬 + 사전 인덱싱 ──
    # works_full을 날짜순 정렬하여 누적 slice로 cutoff 필터링 O(1)
    type_col_actual = "source" if "source" in works_full.columns else type_col

    if use_date_mode:
        dates_parsed = pd.to_datetime(out[session_col], errors="coerce")
        out["_month_key"] = dates_parsed.dt.to_period("M").astype(str)
        cutoff_values = sorted(out["_month_key"].dropna().unique())
        _month_to_date = {m: m + "-01" for m in cutoff_values}

        # works_full 날짜 파싱 + 정렬 (한 번만)
        wf = works_full.copy()
        wf["_dt"] = pd.to_datetime(wf[session_col], errors="coerce")
        wf = wf.sort_values("_dt").reset_index(drop=True)
        wf_sold = wf[wf[price_col] > 0]  # 낙찰 건만 사전 필터
    else:
        cutoff_values = sorted(out[session_col].dropna().unique())
        _month_to_date = None
        wf = works_full
        wf_sold = wf[wf[price_col] > 0]

    n_cutoffs = len(cutoff_values)
    logger.info("Feature loop: %d cutoff windows, %d rows", n_cutoffs, len(out))

    for i, cutoff_val in enumerate(cutoff_values):
        if use_date_mode:
            row_mask = out["_month_key"] == cutoff_val
            cutoff_date = _month_to_date[cutoff_val]
            # 사전 정렬된 데이터에서 cutoff 이전만 slice (핵심 최적화)
            cutoff_dt = pd.Timestamp(cutoff_date)
            past_sold = wf_sold[wf_sold["_dt"] < cutoff_dt]
        else:
            row_mask = out[session_col] == cutoff_val
            cutoff_date = cutoff_val
            past_sold = wf_sold[wf_sold[session_col] < cutoff_date]

        if not row_mask.any():
            continue
        artists_in_session = out.loc[row_mask, "artist_clean"]

        # 진행 로그 (10% 단위)
        if i % max(1, n_cutoffs // 10) == 0:
            logger.info("  cutoff %d/%d (%s)", i + 1, n_cutoffs, cutoff_date)

        # --- 기존 작가 통계 (past_sold 직접 사용, 함수 호출 대신) ---
        if not past_sold.empty:
            stats = past_sold.groupby("artist_clean")[price_col].agg(
                artist_total_sold="count",
                artist_avg_price="mean",
                artist_max_price="max",
            )
            for col in ["artist_total_sold", "artist_avg_price", "artist_max_price"]:
                out.loc[row_mask, col] = artists_in_session.map(stats[col]).fillna(0).values
            known = set(stats.index)
        else:
            known = set()
        is_new = ~artists_in_session.isin(known)
        out.loc[row_mask, "is_new_artist"] = is_new.values

        # --- source_count ---
        if "source" in past_sold.columns and not past_sold.empty:
            sc = past_sold.groupby("artist_clean")["source"].nunique()
            out.loc[row_mask, "source_count"] = artists_in_session.map(sc).fillna(0).values

        # --- Hedonic 피처 (원본 함수 + 실제 cutoff 전달) ---
        if past_sold.empty:
            continue

        status_col_actual = "status" if "status" in wf.columns else "상태"
        _kw = dict(
            cutoff=cutoff_date, auction_type=None,
            session_col=session_col, type_col=type_col_actual,
            price_col=price_col,
        )
        _status_kw = dict(
            cutoff=cutoff_date, auction_type=None,
            session_col=session_col, type_col=type_col_actual,
            status_col=status_col_actual,
        )

        # 작가별 hedonic 피처 — wf_sold 전달 + 실제 cutoff
        vals = compute_artist_median_price(wf_sold, **_kw)
        if not vals.empty:
            out.loc[row_mask, "artist_median_price"] = artists_in_session.map(vals).values

        vals = compute_artist_price_trend(wf_sold, **_kw)
        if not vals.empty:
            out.loc[row_mask, "artist_price_trend"] = artists_in_session.map(vals).values

        vals = compute_medium_avg_price(wf_sold, **_kw)
        if not vals.empty:
            out.loc[row_mask, "medium_avg_price"] = out.loc[
                row_mask, "medium_category"
            ].map(vals).values

        if status_col_actual in wf.columns:
            vals = compute_artist_unsold_rate(wf, **_status_kw)
            if not vals.empty:
                out.loc[row_mask, "artist_unsold_rate"] = artists_in_session.map(vals).values

        # Phase 4 price_col 기반 함수
        for col_name, func in [
            ("artist_recent_avg_price", compute_artist_recent_avg_price),
            ("artist_price_momentum", compute_artist_price_momentum),
            ("artist_auctions_since_last", compute_artist_auctions_since_last),
            ("artist_price_volatility", compute_artist_price_volatility),
            ("artist_last_hammer_price", compute_artist_last_hammer),
        ]:
            vals = func(wf_sold, **_kw)
            if not vals.empty:
                out.loc[row_mask, col_name] = artists_in_session.map(vals).values

        # Phase 4 status_col 기반 함수 (status 컬럼 있을 때만)
        if status_col_actual in wf.columns:
            for col_name, func in [
                ("artist_sale_frequency", compute_artist_sale_frequency),
                ("artist_lot_count_trend", compute_artist_lot_count_trend),
                ("artist_career_length", compute_artist_career_length),
            ]:
                vals = func(wf, **_status_kw)
                if not vals.empty:
                    out.loc[row_mask, col_name] = artists_in_session.map(vals).values

        # market_price_index
        mpi = compute_market_price_index(wf_sold, **_kw)
        out.loc[row_mask, "market_price_index"] = mpi

        # comparable sales + 인터랙션 피처
        from visionai.price_engine.features.hedonic_stats import (
            compute_artist_medium_features,
            compute_medium_size_avg_price,
        )

        for idx in out.index[row_mask]:
            artist = out.loc[idx, "artist_clean"]
            medium = out.loc[idx, "medium_category"]
            area = out.loc[idx, "surface_area"] if "surface_area" in out.columns else 0.0
            comp = compute_comparable_sales(
                wf_sold, cutoff=cutoff_date,
                target_artist=artist, target_medium=medium,
                target_surface_area=float(area) if pd.notna(area) else 0.0,
                auction_type=None,
                session_col=session_col, type_col=type_col_actual, price_col=price_col,
            )
            out.loc[idx, "comp_artist_avg"] = comp["comp_artist_avg"]
            out.loc[idx, "comp_medium_avg"] = comp["comp_medium_avg"]
            out.loc[idx, "comp_weighted"] = comp["comp_weighted"]
            out.loc[idx, "comp_match_count"] = comp["comp_match_count"]
            out.loc[idx, "comp_match_level"] = comp.get("comp_match_level", 4.0)

            # comp_to_avg_ratio: 비교거래가 작가 평균 대비 얼마나 높은/낮은가
            _ca = comp["comp_artist_avg"]
            _aa = out.loc[idx, "artist_avg_price"]
            if pd.notna(_ca) and _ca > 0 and _aa > 0:
                out.loc[idx, "comp_to_avg_ratio"] = float(np.log1p(_ca) - np.log1p(_aa))

            # 인터랙션 피처
            am_feats = compute_artist_medium_features(
                artist, medium, past_sold,
                artist_col="artist_clean", medium_col="medium_category",
                price_col=price_col,
            )
            out.loc[idx, "artist_medium_price_ratio"] = am_feats["artist_medium_price_ratio"]
            out.loc[idx, "artist_medium_frequency"] = am_feats["artist_medium_frequency"]

            size_bucket = out.loc[idx, "size_bucket"] if "size_bucket" in out.columns else ""
            out.loc[idx, "medium_size_avg_price"] = compute_medium_size_avg_price(
                medium, str(size_bucket), past_sold,
                medium_col="medium_category", size_col="size_bucket",
                price_col=price_col,
            )

    # 임시 컬럼 정리
    out = out.drop(columns=["_month_key"], errors="ignore")
    return out


def build_hedonic_features(
    works_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """CSV로부터 추정가-독립 57개 피처 DataFrame을 생성한다.

    Phase 3: 23개 + Phase 4: 16개 + Phase 4b: 3개 + Title NLP: 7개 + Phase 5 크기 개선: 8개.

    Args:
        works_path: k-auction-works CSV 경로.
        output_path: parquet 저장 경로 (None이면 저장하지 않음).

    Returns:
        57개 Hedonic 피처 + split 라벨 + 타깃 컬럼이 포함된 DataFrame.
    """
    logger.info("Loading works CSV: %s", works_path)
    works = pd.read_csv(works_path, encoding="utf-8-sig")
    logger.info("Loaded %d rows", len(works))

    # 데이터 클렌징: 비미술 항목 제거
    from visionai.price_engine.preprocessing.data_cleanser import cleanse_dataframe

    # 컬럼명 자동 감지 (통합 스키마 vs 레거시)
    title_col = "title" if "title" in works.columns else "제목"
    mat_col = "material" if "material" in works.columns else "재료"
    works, _removed = cleanse_dataframe(works, title_col=title_col, material_col=mat_col)

    # 파서 적용
    df = _apply_parsers(works)

    # source_type 기본값 (레거시 데이터용)
    if "source_type" not in df.columns:
        df["source_type"] = "auction"

    # 결측 면적 대체 (조건부 중앙값)

    area_missing = df["surface_area"].isna() | (df["surface_area"] <= 0)
    if area_missing.any():
        valid_areas = df.loc[~area_missing]
        for group_cols in [
            ["artist_clean", "medium_category"],  # P1: 작가×매체 최우선
            ["artist_clean"],                      # P1: 작가 전체
            ["is_3d", "source_type", "medium_category"],
            ["is_3d", "medium_category"],
            ["medium_category"],
        ]:
            still = df["surface_area"].isna() | (df["surface_area"] <= 0)
            if not still.any():
                break
            available = [c for c in group_cols if c in df.columns]
            if not available:
                continue
            medians = valid_areas.groupby(available)["surface_area"].median()
            for idx in df[still].index:
                key = tuple(df.loc[idx, available])
                if len(available) == 1:
                    key = key[0]  # 단일 컬럼: 튜플→스칼라로 변환
                if key in medians.index:
                    df.loc[idx, "surface_area"] = medians[key]
                    df.loc[idx, "is_size_imputed"] = True
        # 최종 fallback
        final_missing = df["surface_area"].isna() | (df["surface_area"] <= 0)
        if final_missing.any():
            global_med = valid_areas["surface_area"].median()
            df.loc[final_missing, "surface_area"] = global_med
            df.loc[final_missing, "is_size_imputed"] = True

    # 호수 피처 (시간 독립) — 기존 하위 호환
    df["size_ho"] = compute_size_ho(df["surface_area"])
    df["size_ho_above40"] = compute_size_ho_above40(df["size_ho"])

    # 신규 크기 피처 (Phase 5 개선)
    from visionai.price_engine.features.hedonic_stats import (
        compute_estimated_ho,
        compute_ln_surface_area,
        compute_orientation,
        compute_size_bucket,
    )

    # estimated_ho: 클렌징 데이터에 ho가 있으면 직접 사용
    if "ho" in df.columns:
        df["estimated_ho"] = df["ho"]
    else:
        df["estimated_ho"] = compute_estimated_ho(df["surface_area"])
    df["ln_surface_area"] = compute_ln_surface_area(df["surface_area"])
    df["size_bucket"] = compute_size_bucket(df["surface_area"])
    if "height_cm" in df.columns and "width_cm" in df.columns:
        h = df["height_cm"].fillna(0)
        w = df["width_cm"].fillna(0)
        df["orientation"] = compute_orientation(h, w)
        df["long_side_cm"] = df[["height_cm", "width_cm"]].max(axis=1)
        df["short_side_cm"] = df[["height_cm", "width_cm"]].min(axis=1)
    # 3D depth 피처 — depth_cm은 _apply_parsers에서 이미 추출됨 (m7-fix)
    df["bbox_volume"] = (
        df["height_cm"].fillna(0)
        * df["width_cm"].fillna(0)
        * df["depth_cm"].fillna(0)
    )

    # 제목 NLP 피처 (시간 독립)
    from visionai.price_engine.features.title_nlp import extract_title_features

    # 제목 NLP (통합 스키마 호환)
    title_src = "제목" if "제목" in df.columns else "title"
    title_feats = extract_title_features(df[title_src])
    for col in title_feats.columns:
        df[col] = title_feats[col]

    # 클렌징 파생 피처 (이미 있으면 유지, 없으면 기본값)
    if "artist_nationality" not in df.columns:
        df["artist_nationality"] = "UN"
    if "edition_number" not in df.columns:
        df["edition_number"] = np.nan

    # ── 작가 프로필 조인 (birth_year, is_deceased) ──
    profiles_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "artist_profiles.csv"
    artist_col = "artist_clean" if "artist_clean" in df.columns else "name_kor"
    if profiles_path.exists():
        profiles = pd.read_csv(profiles_path, encoding="utf-8-sig")
        prof_map = profiles.set_index("name_kor")[["birth_year", "death_year", "is_deceased"]].to_dict("index")

        birth_years = []
        death_years = []
        deceased_flags = []
        for name in df[artist_col]:
            info = prof_map.get(str(name), {})
            by = info.get("birth_year", -1)
            dy = info.get("death_year", -1)
            dec = info.get("is_deceased", False)
            birth_years.append(by if by > 0 else np.nan)
            death_years.append(dy if dy > 0 else np.nan)
            deceased_flags.append(bool(dec))

        df["artist_birth_year"] = birth_years
        df["is_deceased"] = deceased_flags

        # artist_age_at_sale: sale_year - birth_year (or year_created)
        # 레거시 CSV 대응: sale_date 컬럼이 없으면 .dt 접근이 AttributeError → 가드 필요.
        if "sale_date" in df.columns:
            sale_year = pd.to_datetime(df["sale_date"], errors="coerce").dt.year
        else:
            sale_year = pd.Series([np.nan] * len(df), index=df.index, dtype="float64")
        if sale_year.isna().all() and "year_created" in df.columns:
            sale_year = pd.to_numeric(df["year_created"], errors="coerce")
        df["artist_age_at_sale"] = sale_year - df["artist_birth_year"]
        df.loc[df["artist_age_at_sale"] <= 0, "artist_age_at_sale"] = np.nan

        matched = df["artist_birth_year"].notna().sum()
        logger.info("Artist profiles joined: %d/%d have birth_year, %d deceased",
                     matched, len(df), sum(deceased_flags))
    else:
        logger.warning("Artist profiles not found: %s", profiles_path)
        df["artist_birth_year"] = np.nan
        df["artist_age_at_sale"] = np.nan
        df["is_deceased"] = False

    # sale_month + sale_quarter (계절성 피처)
    if "sale_date" in df.columns:
        _dates = pd.to_datetime(df["sale_date"], errors="coerce")
        df["sale_month"] = _dates.dt.month.fillna(0).astype(int)
        df["sale_quarter"] = _dates.dt.quarter.fillna(0).astype(int)
    else:
        df["sale_month"] = 0
        df["sale_quarter"] = 0

    # 4-way split 라벨 — 날짜 기반 또는 레거시 (price_segment_median보다 먼저 할당해야 누수 방지)
    if "sale_date" in df.columns:
        from visionai.price_engine.features.splits import assign_split_by_date
        df["split"] = assign_split_by_date(df, date_col="sale_date")
    else:
        df["split"] = assign_split_4way(df)

    # price_segment_median: 매체별 중앙 가격 (가격대 참고용)
    # 누수 방지: train split 행의 가격으로만 매체별 median 계산 후 모든 행에 브로드캐스트.
    price_col_ps = "price" if "price" in df.columns else "낙찰가"
    _prices = pd.to_numeric(df[price_col_ps], errors="coerce")
    _train_mask = df["split"] == "train"
    if "medium_category" in df.columns:
        train_medians = (
            _prices.where(_train_mask & (_prices > 0))
            .groupby(df["medium_category"])
            .median()
        )
        global_train_median = float(_prices.where(_train_mask & (_prices > 0)).median())
        if not np.isfinite(global_train_median) or global_train_median <= 0:
            global_train_median = 1.0
        mapped = df["medium_category"].map(train_medians)
        mapped = mapped.where(mapped.notna() & (mapped > 0), global_train_median)
        df["price_segment_median"] = np.log(mapped.clip(lower=1))
    else:
        train_median = float(_prices.where(_train_mask & (_prices > 0)).median())
        df["price_segment_median"] = (
            np.log(train_median) if np.isfinite(train_median) and train_median > 0 else 0.0
        )

    # 작가 통계 + Hedonic 피처 조인
    df = _join_artist_stats_and_hedonic(df, works_full=df)

    # 타깃: ln(가격)
    price_col = "낙찰가" if "낙찰가" in df.columns else "price"
    price = pd.to_numeric(df[price_col], errors="coerce")
    df["ln_price"] = np.log(price.where(price > 0))

    # 추정가 타깃 (Model-B용): ln(추정가 중앙) — 있을 때만
    if "추정가(최저)" in df.columns and "추정가(최고)" in df.columns:
        est_low = pd.to_numeric(df["추정가(최저)"], errors="coerce")
        est_high = pd.to_numeric(df["추정가(최고)"], errors="coerce")
        est_mid = (est_low + est_high) / 2
        df["ln_estimate_mid_target"] = np.log(est_mid.where(est_mid > 0))

    # 피처 검증
    missing = [f for f in HEDONIC_FEATURES if f not in df.columns]
    if missing:
        logger.warning("Missing hedonic features: %s", missing)

    logger.info(
        "Built %d hedonic features for %d rows, split distribution: %s",
        len(HEDONIC_FEATURES),
        len(df),
        df["split"].value_counts().to_dict(),
    )

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info("Saved to %s", output_path)

    return df
