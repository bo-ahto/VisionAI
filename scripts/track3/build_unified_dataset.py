"""Track 3 — Unified dataset builder (Artsy + Saatchi + Artue).

Codex schema v1 정합. 본 세션 Track 1 교훈 반영:
- artist_slug overlap=0 인 source는 explicit source_platform tag (학습용)
- 신규 작가 unmatched 시 수집 어려운 features 배제 (followers/total_works/gallery 등)
- Missing detection flags (has_year_made, has_birth_year, has_depth)
- Hedonic + GBM hybrid 학습 대상

운영 원칙 (필수 제약): 운영 수집 가능 / missingness explicit / source neutral.
평가 기준 (parsimony): 모델 선택 시 적은 피처로 동등 성능이면 그쪽 선호.

Schema v3 (User feedback 누적):
- v2 DROP: year_made / has_year_made / age_years (Saatchi raw에 없음)
- v2 DROP: artist_birth_year / has_birth_year / artist_age_at_execution (Saatchi/Artue raw)
- v2 DROP: attribution_class (Saatchi/Artue raw에 없음, 추정만)
- v3 DROP: nationality_region (98.4% korea, 변별력 없음)
- v3 DROP: has_nationality (100% = 1, constant)

Cold-start core (9):
- medium_category / support_category
- width_cm / height_cm / depth_cm / has_depth
- area_cm2 / log_area / orientation

Target:
- price_krw / ln_price_krw

Filters (Track 1 정합):
- price_krw 100K ~ 5B (이상치 제거)
- width_cm > 1, height_cm > 1

Output:
- data/track3_unified_v1.parquet
- data/track3_unified_v1_summary.json (row counts, distribution)

Usage:
    PYTHONPATH=src python3 scripts/track3/build_unified_dataset.py
"""
from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO / "data"
OUT_DIR = DATA_DIR
OUT_PATH = OUT_DIR / "track3_unified_v1.parquet"
OUT_SUMMARY = OUT_DIR / "track3_unified_v1_summary.json"

CURRENT_YEAR = 2026  # listing year baseline (Track 1과 동일)
PRICE_MIN_KRW = 100_000
PRICE_MAX_KRW = 5_000_000_000

# Unified FX rates (Track 1 + Artsy raw 정합).
# 외화 → KRW 통일 환율. KRW는 1.0 (identity).
UNIFIED_FX_TO_KRW = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "KRW": 1.0,
}

# 작가 한글명 매핑 source files (모두 통합).
# Schema: 각 file 의 영문명(name_eng) + 한글명(name_kor) column 추출.
ARTIST_KO_MAP_SOURCES = [
    ("artist_profiles.csv", "name_eng", "name_kor"),
    ("artist_slug_mapping_expanded.csv", "en_name", "ko_name"),
    ("merged_artist_profiles.csv", "name_eng", "name_kor"),
    ("kada_artist_profiles.csv", "name_eng", "name_kor"),
    ("wikidata_korean_artists.csv", "name_en", "name_ko"),
]
# kada에서 placeholder로 사용된 한글명 — 제외
KO_NAME_PLACEHOLDERS = {"중견작가", "신진작가", "원로작가", "작고작가", "Unknown"}
HANGUL_PATTERN = re.compile(r"[가-힣]")


# ─── Medium / Support 분류 (Track 1 정합) ───
SUPPORT_RULES = [
    ("canvas", ["canvas"]),
    ("paper", ["paper", "korean paper", "jangji", "hanji", "washi"]),
    ("linen", ["linen"]),
    ("panel", ["panel", "wood", "board", "mdf"]),
    ("silk", ["silk"]),
    ("metal", ["aluminum", "aluminium", "stainless", "copper", "brass"]),
]
MEDIUM_RULES = [
    ("oil", ["oil"]),
    ("acrylic", ["acrylic"]),
    ("ink", ["ink", "sumi"]),
    ("watercolor", ["watercolor", "gouache", "aquarelle"]),
    ("pigment", ["pigment", "color on"]),
    ("mixed", ["mixed media", "mixed technique"]),
    ("pastel", ["pastel"]),
    ("pencil", ["pencil", "graphite", "charcoal"]),
]


def classify_support(text: str) -> str:
    if pd.isna(text):
        return "other"
    t = str(text).lower()
    for label, keywords in SUPPORT_RULES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def classify_medium(text: str) -> str:
    if pd.isna(text):
        return "other"
    t = str(text).lower()
    for label, keywords in MEDIUM_RULES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def parse_year(value) -> int | None:
    """Parse year from date / year string. Returns int or None."""
    if pd.isna(value):
        return None
    s = str(value)
    m = re.search(r"(\d{4})", s)
    if m:
        y = int(m.group(1))
        if 1800 <= y <= 2030:
            return y
    return None


def orientation_from_dims(w: float, h: float) -> str:
    if pd.isna(w) or pd.isna(h) or w <= 0 or h <= 0:
        return "unknown"
    ratio = h / w
    if abs(ratio - 1.0) < 0.1:
        return "square"
    return "portrait" if ratio > 1 else "landscape"


def _norm_en_variants(name: str) -> set[str]:
    """영문명 정규화 + 순서 swap variants (한국식 vs 서양식).

    예: "Lee Ufan" → {"leeufan", "ufanlee"}
    """
    if name is None or pd.isna(name) or str(name).strip() == "":
        return set()
    cleaned = re.sub(r"[^a-z\s]", "", str(name).lower())
    tokens = [t for t in cleaned.split() if t]
    if not tokens:
        return set()
    variants = {"".join(tokens)}
    if len(tokens) >= 2:
        variants.add("".join(tokens[::-1]))  # last-first ↔ first-last
    return variants


def build_artist_ko_map(data_dir: Path) -> dict[str, str]:
    """모든 매핑 source 통합 → {en_norm_variant: ko_name} dict."""
    mapping: dict[str, str] = {}
    total_rows = 0
    for fname, en_col, ko_col in ARTIST_KO_MAP_SOURCES:
        path = data_dir / fname
        if not path.exists():
            logger.warning(f"  매핑 source 없음: {fname}")
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
        except Exception as e:
            logger.warning(f"  매핑 source load 실패 {fname}: {e}")
            continue
        if en_col not in df.columns or ko_col not in df.columns:
            logger.warning(f"  매핑 source col 누락 {fname}: {en_col}/{ko_col}")
            continue
        sub = df[[en_col, ko_col]].dropna()
        # 한글 character 있어야 + placeholder 제외
        sub = sub[~sub[ko_col].astype(str).isin(KO_NAME_PLACEHOLDERS)]
        sub = sub[sub[ko_col].astype(str).str.contains(HANGUL_PATTERN, na=False)]
        total_rows += len(sub)
        for _, row in sub.iterrows():
            en, ko = str(row[en_col]), str(row[ko_col])
            for variant in _norm_en_variants(en):
                if variant and variant not in mapping:
                    mapping[variant] = ko
    logger.info(f"  artist_name_ko mapping: {len(mapping)} entries (raw {total_rows})")
    return mapping


def lookup_artist_name_ko(name: str, ko_map: dict[str, str]) -> str | None:
    """artist_name_raw → name_ko. (1) 매핑 시도 / (2) raw에 한글 있으면 추출."""
    if name is None or pd.isna(name):
        return None
    name_str = str(name)
    # (1) 매핑 lookup (영문 + name-order swap)
    for variant in _norm_en_variants(name_str):
        if variant in ko_map:
            return ko_map[variant]
    # (2) raw 자체에 한글 있으면 추출
    hangul_chars = HANGUL_PATTERN.findall(name_str)
    if hangul_chars:
        # 연속된 한글 부분만 추출
        match = re.search(r"[가-힣\s]+", name_str)
        if match:
            return match.group(0).strip()
    return None


def nationality_to_region(nat) -> str:
    """간단 region bucket — high-cardinality 방지."""
    if pd.isna(nat):
        return "unknown"
    t = str(nat).lower().strip()
    if any(k in t for k in ["korea", "korean", "대한민국"]):
        return "korea"
    if any(
        k in t
        for k in [
            "china",
            "chinese",
            "taiwan",
            "japan",
            "japanese",
            "vietnam",
            "thai",
            "indonesia",
            "philippines",
            "malaysia",
            "singapore",
            "asian",
        ]
    ):
        return "asia_other"
    if any(k in t for k in ["united states", "american", "usa", "u.s."]):
        return "north_america"
    if any(
        k in t
        for k in [
            "united kingdom",
            "british",
            "german",
            "french",
            "italian",
            "spanish",
            "dutch",
            "european",
            "swedish",
            "swiss",
            "polish",
        ]
    ):
        return "europe"
    return "other"


# ─── Source별 mapping ───


def load_artsy() -> pd.DataFrame:
    logger.info("Loading Artsy raw…")
    a = pd.read_csv(DATA_DIR / "artsy_kr_artworks.csv", low_memory=False)
    logger.info(f"  Artsy raw: {len(a)} rows")

    df = pd.DataFrame({"source_listing_id": a["artwork_id"].astype(str).values})
    df["source_platform"] = "artsy"
    df["medium_category"] = a["medium"].apply(classify_medium)
    df["support_category"] = a["medium"].apply(classify_support)
    df["width_cm"] = pd.to_numeric(a["width_cm"], errors="coerce")
    df["height_cm"] = pd.to_numeric(a["height_cm"], errors="coerce")
    df["depth_cm"] = pd.to_numeric(a["depth_cm"], errors="coerce")
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["price_krw"] = pd.to_numeric(a["price_krw"], errors="coerce")
    # Hybrid 가격 — 원본 + 통일 환율
    df["price_amount_raw"] = pd.to_numeric(a["price_amount"], errors="coerce")
    df["price_currency_raw"] = a["price_currency"].fillna("USD").astype(str)
    df["artist_entity_id_raw"] = a["artist_slug"].astype(str)
    df["artist_name_raw"] = a["artist_name"].astype(str)
    return df


def load_saatchi() -> pd.DataFrame:
    logger.info("Loading Saatchi raw…")
    s = pd.read_csv(DATA_DIR / "saatchi_kr_artworks.csv", low_memory=False)
    logger.info(f"  Saatchi raw: {len(s)} rows")

    df = pd.DataFrame({"source_listing_id": s["artwork_id"].astype(str).values})
    df["source_platform"] = "saatchi"
    df["medium_category"] = s["mediums"].apply(classify_medium)
    df["support_category"] = s["materials"].apply(classify_support)
    df["width_cm"] = pd.to_numeric(s["width_cm"], errors="coerce")
    df["height_cm"] = pd.to_numeric(s["height_cm"], errors="coerce")
    df["depth_cm"] = pd.to_numeric(s["depth_cm"], errors="coerce")
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["price_krw"] = pd.to_numeric(s["price_krw"], errors="coerce")
    # Hybrid 가격 — Saatchi는 USD 단일 (확인됨, 100%)
    df["price_amount_raw"] = pd.to_numeric(s["price_usd"], errors="coerce")
    df["price_currency_raw"] = "USD"
    df["artist_entity_id_raw"] = s["artist_id"].astype(str)
    df["artist_name_raw"] = (
        s["artist_first_name"].fillna("") + " " + s["artist_last_name"].fillna("")
    ).str.strip()
    return df


def load_artue() -> pd.DataFrame:
    logger.info("Loading Artue raw…")
    a = pd.read_csv(DATA_DIR / "artue_테스트_가격포함.csv", low_memory=False)
    logger.info(f"  Artue raw: {len(a)} rows")

    df = pd.DataFrame({"source_listing_id": a["Handle"].astype(str).values})
    df["source_platform"] = "artue"
    df["medium_category"] = a["Medium (EN)"].apply(classify_medium)
    df["support_category"] = a["Medium (EN)"].apply(classify_support)
    df["width_cm"] = pd.to_numeric(a["Width (cm)"], errors="coerce")
    df["height_cm"] = pd.to_numeric(a["Height (cm)"], errors="coerce")
    df["depth_cm"] = pd.to_numeric(a["Depth (cm)"], errors="coerce")
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["price_krw"] = pd.to_numeric(a["Price (KRW)"], errors="coerce")
    # Hybrid 가격 — Artue는 USD 표기 (확인됨, 100%)
    df["price_amount_raw"] = pd.to_numeric(a["Price (USD)"], errors="coerce")
    df["price_currency_raw"] = "USD"
    df["artist_entity_id_raw"] = a["Handle"].astype(str)
    df["artist_name_raw"] = a["Artist"].astype(str)
    return df


# ─── Derived features + filter ───


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """area_cm2 / log_area / orientation + Hybrid 가격 (price_krw_unified, was_converted)."""
    df["area_cm2"] = df["width_cm"] * df["height_cm"]
    df["log_area"] = df["area_cm2"].apply(
        lambda v: math.log(v) if pd.notna(v) and v > 0 else float("nan")
    )
    df["orientation"] = df.apply(
        lambda r: orientation_from_dims(r["width_cm"], r["height_cm"]),
        axis=1,
    )
    # depth NaN → 0 (has_depth가 missingness 표시)
    df["depth_cm"] = df["depth_cm"].fillna(0)

    # Hybrid 가격:
    # - 원래 KRW면 그대로 (price_krw 사용), was_converted=0
    # - 외화면 통일 환율 (UNIFIED_FX_TO_KRW) 적용, was_converted=1
    def compute_unified(row):
        cur = str(row["price_currency_raw"]).upper().strip()
        amount = row["price_amount_raw"]
        if cur == "KRW":
            return row["price_krw"] if pd.notna(row["price_krw"]) else float("nan")
        if pd.isna(amount) or amount <= 0:
            return float("nan")
        rate = UNIFIED_FX_TO_KRW.get(cur)
        if rate is None:
            return float("nan")  # unknown currency
        return float(amount) * rate

    df["price_krw_unified"] = df.apply(compute_unified, axis=1)
    df["was_converted"] = (df["price_currency_raw"].str.upper().str.strip() != "KRW").astype(int)
    return df


def apply_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """가격/크기 필터. price_krw_unified 기준 (학습 target)."""
    n0 = len(df)
    drops = {}

    # price filter — unified 기준 (학습 target)
    mask = df["price_krw_unified"].notna() & (df["price_krw_unified"] > 0)
    drops["price_null_or_zero"] = (~mask).sum()
    df = df[mask].copy()

    mask = (df["price_krw_unified"] >= PRICE_MIN_KRW) & (df["price_krw_unified"] <= PRICE_MAX_KRW)
    drops["price_out_of_range"] = (~mask).sum()
    df = df[mask].copy()

    # size filter
    mask = (
        df["width_cm"].notna()
        & (df["width_cm"] > 1)
        & df["height_cm"].notna()
        & (df["height_cm"] > 1)
    )
    drops["size_invalid"] = (~mask).sum()
    df = df[mask].copy()

    # ln_price — unified 기준 (학습 target)
    df["ln_price_krw_unified"] = np.log(df["price_krw_unified"])

    drops["total_in"] = n0
    drops["total_kept"] = len(df)
    drops["kept_pct"] = round(100 * len(df) / max(n0, 1), 2)

    return df, drops


# ─── Main ───


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 unified dataset builder (Artsy + Saatchi + Artue)")
    logger.info("=" * 70)

    # 작가 한글명 매핑 build
    logger.info("Building artist_name_ko mapping...")
    ko_map = build_artist_ko_map(DATA_DIR)

    a = load_artsy()
    s = load_saatchi()
    artue = load_artue()

    unified = pd.concat([a, s, artue], ignore_index=True)
    logger.info(f"\nConcat: {len(unified)} rows total")

    # artist_name_ko apply
    unified["artist_name_ko"] = unified["artist_name_raw"].apply(
        lambda n: lookup_artist_name_ko(n, ko_map)
    )
    n_ko = unified["artist_name_ko"].notna().sum()
    logger.info(f"  artist_name_ko matched: {n_ko:,}/{len(unified):,} ({100*n_ko/len(unified):.1f}%)")

    unified = add_derived(unified)
    unified, drops = apply_filters(unified)
    logger.info(f"After filter: {len(unified)} rows kept (drops={drops})")

    # column order — schema v5 (artist_name_ko 추가 / 20 cols)
    cols = [
        # IDs (학습 비feature)
        "source_platform",
        "source_listing_id",
        "artist_entity_id_raw",
        "artist_name_raw",
        "artist_name_ko",
        # Cold-start core (9)
        "medium_category",
        "support_category",
        "width_cm",
        "height_cm",
        "depth_cm",
        "has_depth",
        "area_cm2",
        "log_area",
        "orientation",
        # Hybrid 가격 (4) — 원본 + 통일 환율 + 환전 flag
        "price_amount_raw",
        "price_currency_raw",
        "price_krw",
        "was_converted",
        # Target (2) — 학습용 unified
        "price_krw_unified",
        "ln_price_krw_unified",
    ]
    unified = unified[cols]

    # Save
    unified.to_parquet(OUT_PATH, index=False)
    logger.info(f"\n✅ Saved: {OUT_PATH} ({len(unified)} rows / {len(cols)} cols)")

    # Summary
    summary = {
        "rows": int(len(unified)),
        "cols": int(len(cols)),
        "by_source": unified["source_platform"].value_counts().to_dict(),
        "price_stats_unified": {
            "median_krw": int(unified["price_krw_unified"].median()),
            "mean_krw": int(unified["price_krw_unified"].mean()),
            "q05": int(unified["price_krw_unified"].quantile(0.05)),
            "q95": int(unified["price_krw_unified"].quantile(0.95)),
        },
        "fx_rates_unified": UNIFIED_FX_TO_KRW,
        "was_converted_counts": unified["was_converted"].value_counts().to_dict(),
        "currency_distribution": unified["price_currency_raw"].value_counts().to_dict(),
        "missingness_flags": {
            "has_depth": int(unified["has_depth"].sum()),
        },
        "missingness_flags_by_source": {
            src: {
                "has_depth": int(unified[unified["source_platform"] == src]["has_depth"].sum()),
                "n_rows": int((unified["source_platform"] == src).sum()),
            }
            for src in unified["source_platform"].unique()
        },
        "medium_category_top5": unified["medium_category"].value_counts().head(5).to_dict(),
        "support_category_top5": unified["support_category"].value_counts().head(5).to_dict(),
        "orientation": unified["orientation"].value_counts().to_dict(),
        "filter_drops": drops,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    logger.info(f"✅ Summary: {OUT_SUMMARY}")

    # Print summary
    print("\n" + "=" * 70)
    print(f"Track 3 unified dataset v1 — {len(unified):,} rows / {len(cols)} cols")
    print("=" * 70)
    print(f"\nBy source: {summary['by_source']}")
    print(
        f"Price (KRW unified): median={summary['price_stats_unified']['median_krw']:,}, "
        f"mean={summary['price_stats_unified']['mean_krw']:,}"
    )
    print(f"Currency distribution: {summary['currency_distribution']}")
    print(f"Was converted (0=KRW raw / 1=외화 환전): {summary['was_converted_counts']}")
    print(f"FX rates applied: {summary['fx_rates_unified']}")
    print(f"Missingness (has_X=1 count):")
    for k, v in summary["missingness_flags"].items():
        pct = 100 * v / len(unified)
        print(f"  {k}: {v:,} ({pct:.1f}%)")
    print(f"\nPer-source missingness:")
    for src, stats in summary["missingness_flags_by_source"].items():
        n = stats["n_rows"]
        print(f"  {src} (n={n:,}): has_depth {stats['has_depth']:,} ({100*stats['has_depth']/n:.1f}%)")


if __name__ == "__main__":
    main()
