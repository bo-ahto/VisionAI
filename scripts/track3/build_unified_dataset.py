"""Track 3 — Unified dataset builder (Artsy + Saatchi + Artue).

Codex schema v1 정합. 본 세션 Track 1 교훈 반영:
- artist_slug overlap=0 인 source는 explicit source_platform tag (학습용)
- 신규 작가 unmatched 시 수집 어려운 features 배제 (followers/total_works/gallery 등)
- Missing detection flags (has_year_made, has_birth_year, has_depth)
- Hedonic + GBM hybrid 학습 대상

운영 원칙 (필수 제약): 운영 수집 가능 / missingness explicit / source neutral.
평가 기준 (parsimony): 모델 선택 시 적은 피처로 동등 성능이면 그쪽 선호.

Schema v2 (User feedback: 3 source 모두 공통인 columns만 유지):
- DROP: year_made / has_year_made / age_years (Saatchi raw에 없음)
- DROP: artist_birth_year / has_birth_year / artist_age_at_execution (Saatchi/Artue raw에 없음)
- DROP: attribution_class (Saatchi/Artue raw에 없음, 추정만 가능)

Cold-start core (9):
- medium_category / support_category
- width_cm / height_cm / depth_cm / has_depth
- area_cm2 / log_area / orientation

Enrichment (2):
- nationality_region / has_nationality

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
    df["nationality_region"] = a["artist_nationality"].apply(nationality_to_region)
    df["has_nationality"] = (
        a["artist_nationality"].notna() & (a["artist_nationality"] != "")
    ).astype(int)
    df["price_krw"] = pd.to_numeric(a["price_krw"], errors="coerce")
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
    df["nationality_region"] = s["country"].apply(nationality_to_region)
    df["has_nationality"] = (s["country"].notna() & (s["country"] != "")).astype(int)
    df["price_krw"] = pd.to_numeric(s["price_krw"], errors="coerce")
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
    df["nationality_region"] = a["Nationality"].apply(nationality_to_region)
    df["has_nationality"] = (a["Nationality"].notna() & (a["Nationality"] != "")).astype(int)
    df["price_krw"] = pd.to_numeric(a["Price (KRW)"], errors="coerce")
    df["artist_entity_id_raw"] = a["Handle"].astype(str)
    df["artist_name_raw"] = a["Artist"].astype(str)
    return df


# ─── Derived features + filter ───


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Schema v2: area_cm2 / log_area / orientation only."""
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
    return df


def apply_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """가격/크기 필터 (Track 1 정합)."""
    n0 = len(df)
    drops = {}

    # price filter
    mask = df["price_krw"].notna() & (df["price_krw"] > 0)
    drops["price_null_or_zero"] = (~mask).sum()
    df = df[mask].copy()

    mask = (df["price_krw"] >= PRICE_MIN_KRW) & (df["price_krw"] <= PRICE_MAX_KRW)
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

    # ln_price
    df["ln_price_krw"] = np.log(df["price_krw"])

    drops["total_in"] = n0
    drops["total_kept"] = len(df)
    drops["kept_pct"] = round(100 * len(df) / max(n0, 1), 2)

    return df, drops


# ─── Main ───


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 unified dataset builder (Artsy + Saatchi + Artue)")
    logger.info("=" * 70)

    a = load_artsy()
    s = load_saatchi()
    artue = load_artue()

    unified = pd.concat([a, s, artue], ignore_index=True)
    logger.info(f"\nConcat: {len(unified)} rows total")

    unified = add_derived(unified)
    unified, drops = apply_filters(unified)
    logger.info(f"After filter: {len(unified)} rows kept (drops={drops})")

    # column order — schema v2 (3 source 공통 features only / 17 cols)
    cols = [
        # IDs (학습 비feature)
        "source_platform",
        "source_listing_id",
        "artist_entity_id_raw",
        "artist_name_raw",
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
        # Enrichment (2)
        "nationality_region",
        "has_nationality",
        # Target (2)
        "price_krw",
        "ln_price_krw",
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
        "price_stats": {
            "median_krw": int(unified["price_krw"].median()),
            "mean_krw": int(unified["price_krw"].mean()),
            "q05": int(unified["price_krw"].quantile(0.05)),
            "q95": int(unified["price_krw"].quantile(0.95)),
        },
        "missingness_flags": {
            "has_depth": int(unified["has_depth"].sum()),
            "has_nationality": int(unified["has_nationality"].sum()),
        },
        "missingness_flags_by_source": {
            src: {
                "has_depth": int(unified[unified["source_platform"] == src]["has_depth"].sum()),
                "has_nationality": int(
                    unified[unified["source_platform"] == src]["has_nationality"].sum()
                ),
                "n_rows": int((unified["source_platform"] == src).sum()),
            }
            for src in unified["source_platform"].unique()
        },
        "medium_category_top5": unified["medium_category"].value_counts().head(5).to_dict(),
        "support_category_top5": unified["support_category"].value_counts().head(5).to_dict(),
        "nationality_region": unified["nationality_region"].value_counts().to_dict(),
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
        f"Price (KRW): median={summary['price_stats']['median_krw']:,}, mean={summary['price_stats']['mean_krw']:,}"
    )
    print(f"Missingness (has_X=1 count):")
    for k, v in summary["missingness_flags"].items():
        pct = 100 * v / len(unified)
        print(f"  {k}: {v:,} ({pct:.1f}%)")
    print(f"\nPer-source missingness:")
    for src, stats in summary["missingness_flags_by_source"].items():
        n = stats["n_rows"]
        print(f"  {src} (n={n:,}):")
        for k in ["has_depth", "has_nationality"]:
            print(f"    {k}: {stats[k]:,} ({100*stats[k]/n:.1f}%)")


if __name__ == "__main__":
    main()
