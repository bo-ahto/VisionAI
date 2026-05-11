"""Track 3 unified dataset validation — quality checks + integrity verification.

본 script은 build_unified_dataset.py 산출물 검증.

Usage:
    PYTHONPATH=src python3 scripts/track3/validate_unified_dataset.py

Exit code:
    0 = PASS (모든 check 통과)
    1 = FAIL (어느 check든 실패)
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1.parquet"
SUMMARY_PATH = REPO / "data" / "track3_unified_v1_summary.json"

EXPECTED_COLS = [
    # IDs
    "source_platform",
    "source_listing_id",
    "artist_entity_id_raw",
    "artist_name_raw",
    "artist_name_ko",
    # Cold-start core (10) — width/height/area + estimated_ho
    "medium_category",
    "support_category",
    "width_cm",
    "height_cm",
    "depth_cm",
    "has_depth",
    "area_cm2",
    "log_area",
    "estimated_ho",
    "orientation",
    # Hybrid 가격 (4)
    "price_amount_raw",
    "price_currency_raw",
    "price_krw",
    "was_converted",
    # Target (2) — unified 학습용
    "price_krw_unified",
    "ln_price_krw_unified",
]
EXPECTED_SOURCES = {"artsy", "saatchi", "artue"}
EXPECTED_ORIENTATIONS = {"portrait", "landscape", "square", "unknown"}
PRICE_MIN_KRW = 100_000
PRICE_MAX_KRW = 5_000_000_000


def check_file_exists() -> tuple[bool, str]:
    if not DATA_PATH.exists():
        return False, f"Missing dataset: {DATA_PATH}"
    if not SUMMARY_PATH.exists():
        return False, f"Missing summary: {SUMMARY_PATH}"
    return True, f"{DATA_PATH.name} ({DATA_PATH.stat().st_size:,} bytes)"


def check_schema(df: pd.DataFrame) -> tuple[bool, str]:
    got = list(df.columns)
    if got != EXPECTED_COLS:
        extra = set(got) - set(EXPECTED_COLS)
        missing = set(EXPECTED_COLS) - set(got)
        return False, f"Schema mismatch: extra={extra} / missing={missing}"
    return True, f"All {len(EXPECTED_COLS)} columns present in correct order"


def check_row_count(df: pd.DataFrame) -> tuple[bool, str]:
    if len(df) < 1000:
        return False, f"Row count too low: {len(df)}"
    return True, f"{len(df):,} rows"


def check_sources(df: pd.DataFrame) -> tuple[bool, str]:
    sources = set(df["source_platform"].unique())
    if sources != EXPECTED_SOURCES:
        return False, f"Source mismatch: got={sources} expected={EXPECTED_SOURCES}"
    counts = df["source_platform"].value_counts().to_dict()
    return True, f"Sources: {counts}"


def check_price_range(df: pd.DataFrame) -> tuple[bool, str]:
    p = df["price_krw_unified"]
    if (p < PRICE_MIN_KRW).any():
        return False, f"price_krw_unified < {PRICE_MIN_KRW:,}: {(p < PRICE_MIN_KRW).sum()}"
    if (p > PRICE_MAX_KRW).any():
        return False, f"price_krw_unified > {PRICE_MAX_KRW:,}: {(p > PRICE_MAX_KRW).sum()}"
    return True, (f"unified ∈ [{p.min():,.0f}, {p.max():,.0f}] / median={p.median():,.0f}")


def check_ln_price_consistency(df: pd.DataFrame) -> tuple[bool, str]:
    expected = np.log(df["price_krw_unified"])
    diff = (df["ln_price_krw_unified"] - expected).abs().max()
    if diff > 1e-6:
        return False, f"ln_price_krw_unified mismatch: max diff {diff}"
    return True, f"ln_price_krw_unified consistent (max diff {diff:.2e})"


def check_size(df: pd.DataFrame) -> tuple[bool, str]:
    if (df["width_cm"] <= 1).any() or (df["height_cm"] <= 1).any():
        return False, "width/height ≤ 1 found"
    if not (df["area_cm2"] == df["width_cm"] * df["height_cm"]).all():
        return False, "area_cm2 != width*height"
    return True, (
        f"size OK / width median {df['width_cm'].median():.0f}cm / "
        f"height median {df['height_cm'].median():.0f}cm"
    )


def check_categorical_values(df: pd.DataFrame) -> tuple[bool, str]:
    o = set(df["orientation"].unique())
    if not o.issubset(EXPECTED_ORIENTATIONS):
        return False, f"orientation extra: {o - EXPECTED_ORIENTATIONS}"
    return True, f"orientation {dict(df['orientation'].value_counts())}"


def check_flag_consistency(df: pd.DataFrame) -> tuple[bool, str]:
    """has_X flags should agree with underlying value (schema v2: has_depth only)."""
    inconsistent = ((df["has_depth"] == 1) != (df["depth_cm"] > 0)).sum()
    if inconsistent > 0:
        return False, f"has_depth: {inconsistent} inconsistent"
    return True, "has_depth flag consistent with depth_cm > 0"


def check_missingness_rates(df: pd.DataFrame) -> tuple[bool, str]:
    """Report missingness per source (informational, always PASS)."""
    rates = []
    for src in sorted(df["source_platform"].unique()):
        sub = df[df["source_platform"] == src]
        n = len(sub)
        rates.append(f"{src}({n:,}): depth {100*sub['has_depth'].sum()/n:.0f}%")
    return True, "; ".join(rates)


def check_no_null(df: pd.DataFrame) -> tuple[bool, str]:
    """price_amount_raw, artist_name_ko는 nullable 허용."""
    nullable_allowed = {"price_amount_raw", "artist_name_ko"}
    null_cols = []
    for col in df.columns:
        if col in nullable_allowed:
            continue
        n_null = df[col].isna().sum()
        if n_null > 0:
            null_cols.append(f"{col}({n_null})")
    if null_cols:
        return False, f"Null found: {null_cols}"
    return True, "No null in critical columns (price_amount_raw nullable allowed)"


def check_hybrid_price_consistency(df: pd.DataFrame) -> tuple[bool, str]:
    """Hybrid 가격 일관성: KRW source → was_converted=0, 외화 → was_converted=1."""
    krw_rows = df[df["price_currency_raw"].str.upper() == "KRW"]
    if (krw_rows["was_converted"] != 0).any():
        return False, f"KRW source에 was_converted=1: {(krw_rows['was_converted'] != 0).sum()}"
    non_krw = df[df["price_currency_raw"].str.upper() != "KRW"]
    if (non_krw["was_converted"] != 1).any():
        return False, f"외화 source에 was_converted=0: {(non_krw['was_converted'] != 1).sum()}"
    return True, (
        f"was_converted consistent: KRW {len(krw_rows):,} (0) / 외화 {len(non_krw):,} (1)"
    )


CHECKS = [
    ("1. File existence", check_file_exists, False),
    ("2. Schema (column names + order)", check_schema, True),
    ("3. Row count (≥ 1,000)", check_row_count, True),
    ("4. Source distribution", check_sources, True),
    ("5. Price range filter (unified)", check_price_range, True),
    ("6. ln_price_krw_unified consistency", check_ln_price_consistency, True),
    ("7. Size (width/height/area)", check_size, True),
    ("8. Categorical values (orientation)", check_categorical_values, True),
    ("9. has_X flag consistency", check_flag_consistency, True),
    ("10. Missingness rates (informational)", check_missingness_rates, True),
    ("11. No null in critical columns", check_no_null, True),
    ("12. Hybrid 가격 (was_converted) consistency", check_hybrid_price_consistency, True),
]


def main() -> int:
    logger.info("=" * 70)
    logger.info("Track 3 unified dataset v1 — validation")
    logger.info("=" * 70)

    # First check file exists
    ok, msg = check_file_exists()
    marker = "✅" if ok else "❌"
    logger.info("%s 1. File existence — %s", marker, msg)
    if not ok:
        return 1

    df = pd.read_parquet(DATA_PATH)
    summary = json.loads(SUMMARY_PATH.read_text())
    logger.info("Loaded dataset: %d rows, %d cols", len(df), len(df.columns))
    logger.info("Loaded summary: by_source=%s", summary.get("by_source"))
    logger.info("")

    all_pass = True
    for name, fn, needs_df in CHECKS[1:]:
        try:
            if needs_df:
                ok, msg = fn(df)
            else:
                ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"exception: {e}"
        if not ok:
            all_pass = False
        marker = "✅" if ok else "❌"
        logger.info("%s %s — %s", marker, name, msg)

    logger.info("=" * 70)
    if all_pass:
        logger.info("VERDICT: ✅ PASS (모든 check 통과 — 데이터셋 공유 준비됨)")
        return 0
    else:
        logger.error("VERDICT: ❌ FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
