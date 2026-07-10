"""Tier CSV 의 계산 column 의 정합성 검수.

각 계산 column 의 정의 와 실제 값 의 정합 검증 + 이상치 / 결손 detection.
운영 saatchi_cleaned.parquet 변경 X / 본 cycle = 검수 자료 만.

Decision binding: ❌ X
"""

from __future__ import annotations

import json
import logging
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from saatchi_year_made_merger import (  # type: ignore  # noqa: E402
    WORK_AGE_REF_YEAR,
    add_has_year_made_flag,
    load_enrichment_year_map,
    merge_year_made,
    recompute_work_age,
)
from train_primary_market_v3_filtered import load_data  # type: ignore  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ENRICHMENT_JSONL = REPO / "data" / "saatchi_year_enrichment_artifact_20260501" / "raw.jsonl"
OUT = REPO / "experiments" / "structural_v1" / "results" / "dataset_computed_columns_verification_20260508.json"


def load_t0() -> pd.DataFrame:
    """T0 = 운영 dataset + Saatchi year_made enrichment 적용."""
    df = load_data()
    if not ENRICHMENT_JSONL.exists():
        import subprocess
        ENRICHMENT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.check_output(
            ["git", "show",
             "dce0dfa1fd5b3d7e6e43f651e921140e56b68a2b:"
             "model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl"],
            cwd=REPO,
        )
        ENRICHMENT_JSONL.write_bytes(blob)
    em = load_enrichment_year_map(ENRICHMENT_JSONL)
    df = merge_year_made(df, em, only_saatchi=True)
    df = add_has_year_made_flag(df)
    df = recompute_work_age(df, ref_year=WORK_AGE_REF_YEAR)
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    return df


def main() -> None:
    df = load_t0()
    n = len(df)
    logger.info("T0 loaded: n=%d", n)

    checks = {}

    # ─── 1. ln_price = log(price_krw) ────────────────────────────────
    expected = np.log(df["price_krw"])
    actual = df["ln_price"]
    diff = (expected - actual).abs()
    checks["ln_price"] = {
        "definition": "log(price_krw)",
        "n_total": n,
        "exact_match": int((diff < 1e-9).sum()),
        "max_abs_diff": float(diff.max()),
        "mean_abs_diff": float(diff.mean()),
        "verdict": "EXACT" if diff.max() < 1e-9 else f"MISMATCH max_diff={diff.max():.6f}",
    }

    # ─── 2. ln_area = log(area_cm2.clip(lower=1)) — operational fill ─
    # operational train_primary_market_v3_filtered.py: ln_area = log(area_cm2.clip(lower=1))
    expected_lnarea = np.log(df["area_cm2"].clip(lower=1))
    actual_lnarea = df["ln_area"]
    # operational의 fill: artsy 직접 / saatchi 의 경우 load_data 가 fill (없으면)
    # source_data 에 ln_area 가 있으면 그것 / 없으면 0.0 fill
    n_zero = int((actual_lnarea == 0).sum())
    diff_nz = (expected_lnarea[actual_lnarea > 0] - actual_lnarea[actual_lnarea > 0]).abs()
    checks["ln_area"] = {
        "definition": "log(area_cm2.clip(lower=1)) — operational load_data fill",
        "n_total": n,
        "n_zero": n_zero,
        "n_nonzero": n - n_zero,
        "max_abs_diff_nonzero": float(diff_nz.max()) if len(diff_nz) > 0 else 0,
        "verdict": "EXACT (nonzero subset)" if len(diff_nz) == 0 or diff_nz.max() < 1e-6 else f"MISMATCH max={diff_nz.max():.6f}",
    }

    # ─── 3. ln_ho = log(ho + 1) ──────────────────────────────────────
    expected = np.log(df["ho"] + 1)
    actual = df["ln_ho"]
    diff = (expected - actual).abs()
    checks["ln_ho"] = {
        "definition": "log(ho + 1)",
        "n_total": n,
        "max_abs_diff": float(diff.max()),
        "verdict": "EXACT" if diff.max() < 1e-9 else f"MISMATCH max={diff.max():.6f}",
    }

    # ─── 4. ho_power = ho^0.74 (ho>0) / 0 (ho<=0) ────────────────────
    expected = df["ho"].apply(lambda h: h ** 0.74 if h > 0 else 0)
    actual = df["ho_power"]
    diff = (expected - actual).abs()
    checks["ho_power"] = {
        "definition": "ho^0.74 (ho>0) else 0",
        "n_total": n,
        "max_abs_diff": float(diff.max()),
        "verdict": "EXACT" if diff.max() < 1e-9 else f"MISMATCH max={diff.max():.6f}",
    }

    # ─── 5. is_small = (ho <= 3) ─────────────────────────────────────
    expected = (df["ho"] <= 3).astype(int)
    actual = df["is_small"]
    n_mismatch = int((expected != actual).sum())
    checks["is_small"] = {
        "definition": "1 if ho <= 3 else 0",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 6. is_unique = (attribution_class == "Unique") ──────────────
    expected = (df["attribution_class"] == "Unique").astype(int)
    actual = df["is_unique"]
    n_mismatch = int((expected != actual).sum())
    checks["is_unique"] = {
        "definition": "1 if attribution_class == 'Unique' else 0",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 7. is_edition = (attribution_class == "Limited edition") ────
    expected = (df["attribution_class"] == "Limited edition").astype(int)
    actual = df["is_edition"]
    n_mismatch = int((expected != actual).sum())
    checks["is_edition"] = {
        "definition": "1 if attribution_class == 'Limited edition' else 0",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 8. is_krw = (price_currency == "KRW") ───────────────────────
    expected = (df["price_currency"] == "KRW").astype(int)
    actual = df["is_krw"]
    n_mismatch = int((expected != actual).sum())
    checks["is_krw"] = {
        "definition": "1 if price_currency == 'KRW' else 0",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 9. work_age = 2026 - year_made (notna) ──────────────────────
    notna_mask = df["year_made"].notna()
    expected = (WORK_AGE_REF_YEAR - df.loc[notna_mask, "year_made"]).astype(float)
    actual = df.loc[notna_mask, "work_age"].astype(float)
    diff = (expected - actual).abs()
    n_total_notna = int(notna_mask.sum())
    n_mismatch = int((diff > 1e-9).sum())
    checks["work_age"] = {
        "definition": "2026 - year_made (year_made notna 영역 만)",
        "n_total_notna": n_total_notna,
        "n_mismatch": n_mismatch,
        "max_abs_diff": float(diff.max()) if len(diff) > 0 else 0,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 10. has_year_made = year_made.notna() ───────────────────────
    if "has_year_made" in df.columns:
        expected = df["year_made"].notna().astype(int)
        actual = df["has_year_made"]
        n_mismatch = int((expected != actual).sum())
        checks["has_year_made"] = {
            "definition": "1 if year_made notna else 0",
            "n_total": n,
            "n_mismatch": n_mismatch,
            "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
        }

    # ─── 11. has_birth_year = artist_birth_year.notna() ──────────────
    expected = df["artist_birth_year"].notna().astype(int)
    actual = df["has_birth_year"]
    n_mismatch = int((expected != actual).sum())
    checks["has_birth_year"] = {
        "definition": "1 if artist_birth_year notna else 0",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 12. ho_x_support = ho * support_factor ──────────────────────
    expected = df["ho"] * df["support_factor"]
    actual = df["ho_x_support"]
    diff = (expected - actual).abs()
    n_mismatch = int((diff > 1e-9).sum())
    checks["ho_x_support"] = {
        "definition": "ho * support_factor",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "max_abs_diff": float(diff.max()),
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch}",
    }

    # ─── 13. has_seoul = gallery_cities contains 'Seoul' ─────────────
    # operational definition: gallery_cities (raw text) contains 'Seoul'
    # 본 dataset 에 gallery_cities 직접 컬럼 X / has_seoul 만 있음 → check via gallery_name?
    # 운영 has_seoul 의 정의 검수 = gallery_cities 영역 의 source-level audit (별도 cycle)
    checks["has_seoul"] = {
        "definition": "1 if gallery_cities contains 'Seoul' (parsed from source)",
        "n_total": n,
        "n_one": int((df["has_seoul"] == 1).sum()),
        "verdict": "REQUIRES_SOURCE_AUDIT (gallery_cities raw column not in dataset)",
    }

    # ─── 14. has_international = (gallery_city_count >= 2) ───────────
    expected = (df["gallery_city_count"] >= 2).astype(int)
    actual = df["has_international"]
    n_mismatch = int((expected != actual).sum())
    checks["has_international"] = {
        "definition": "1 if gallery_city_count >= 2 else 0",
        "n_total": n,
        "n_mismatch": n_mismatch,
        "verdict": "EXACT" if n_mismatch == 0 else f"MISMATCH n={n_mismatch} (Saatchi 의 gallery_city_count == 1 + has_international == 1 의 정의 mismatch 영역 가능)",
    }

    # ─── 15. ln_followers = log(artist_followers + 1) ────────────────
    # artist_followers 는 column 에 없음 (raw 영역) → 검수 영역 X
    checks["ln_followers"] = {
        "definition": "log(artist_followers + 1) — raw artist_followers column 미포함",
        "n_total": n,
        "n_zero": int((df["ln_followers"] == 0).sum()),
        "verdict": "REQUIRES_SOURCE_AUDIT (artist_followers raw column not in dataset)",
    }

    # ─── 16. has_depth = (depth_cm.notna()) ──────────────────────────
    # depth_cm 도 column 에 없음
    checks["has_depth"] = {
        "definition": "1 if depth_cm notna else 0 — raw depth_cm column 미포함",
        "n_total": n,
        "n_one": int((df["has_depth"] == 1).sum()),
        "verdict": "REQUIRES_SOURCE_AUDIT (depth_cm raw column not in dataset)",
    }

    # ─── 17. vintage_premium logic check (career_stage_int 기반) ────
    # operational: vintage_premium = work_age if (career_stage_int >= 3 and work_age) else 0
    # career_stage_int 도 본 dataset 에 없음
    n_vp_zero = int((df["vintage_premium"] == 0).sum())
    n_vp_pos = int((df["vintage_premium"] > 0).sum())
    checks["vintage_premium"] = {
        "definition": "work_age if career_stage_int >= 3 else 0",
        "n_total": n,
        "n_zero": n_vp_zero,
        "n_positive": n_vp_pos,
        "zero_pct": round(n_vp_zero / n * 100, 2),
        "verdict": "REQUIRES_SOURCE_AUDIT (career_stage_int missing) / 99.93% zero = 사실상 미작동",
    }

    n_fd_zero = int((df["freshness_discount"] == 0).sum())
    n_fd_pos = int((df["freshness_discount"] > 0).sum())
    checks["freshness_discount"] = {
        "definition": "work_age if career_stage_int < 3 else 0",
        "n_total": n,
        "n_zero": n_fd_zero,
        "n_positive": n_fd_pos,
        "zero_pct": round(n_fd_zero / n * 100, 2),
        "verdict": "REQUIRES_SOURCE_AUDIT (career_stage_int missing)",
    }

    # ─── 18. placeholder columns (100% zero) ─────────────────────────
    for col in ["ho_price_level", "medium_price_level", "profile_completeness"]:
        n_zero = int((df[col] == 0).sum())
        checks[col] = {
            "definition": "operational load_data() 가 0.0 fill / source 미존재",
            "n_total": n,
            "n_zero": n_zero,
            "zero_pct": round(n_zero / n * 100, 2),
            "verdict": "PLACEHOLDER (100% zero / 모델 noise feature)",
        }

    # ─── 19. sparse columns (low variance) ──────────────────────────
    # for_sale_ratio / request_ratio 영역 정합 — Saatchi 영역 의 0 fill 의무
    saatchi_mask = df["source"] == "saatchi"
    n_saatchi = int(saatchi_mask.sum())
    for col in ["request_ratio", "artist_is_p1", "has_special_finish"]:
        n_zero_or_false = int(
            (df[col] == 0).sum() if pd.api.types.is_numeric_dtype(df[col])
            else (df[col] == False).sum()
        )
        checks[col] = {
            "n_total": n,
            "n_zero_or_false": n_zero_or_false,
            "pct": round(n_zero_or_false / n * 100, 2),
            "verdict": "SPARSE (변별력 거의 없음)",
        }

    # ─── 20. categorical 정규화 column 의 분포 sanity ───────────────
    for col in ["medium_category", "support_type", "gallery_type", "attribution_class"]:
        n_other = int((df[col].astype(str).str.lower() == "other").sum())
        n_unknown = int((df[col].astype(str).str.lower() == "unknown").sum())
        n_unique_vals = int(df[col].nunique())
        checks[col + "_distribution"] = {
            "n_total": n,
            "n_unique_values": n_unique_vals,
            "n_other": n_other,
            "n_unknown": n_unknown,
            "verdict": "OK" if n_unique_vals >= 2 else "LOW_VARIANCE",
        }

    # ─── Summary ──────────────────────────────────────────────────────
    summary = {
        "scope": "T0 (28,376 rows / Saatchi year_made enrichment 적용)",
        "decision_binding": False,
        "checks": checks,
        "categories": {
            "EXACT": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("EXACT")],
            "MISMATCH": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("MISMATCH")],
            "PLACEHOLDER": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("PLACEHOLDER")],
            "SPARSE": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("SPARSE")],
            "REQUIRES_SOURCE_AUDIT": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("REQUIRES_SOURCE_AUDIT")],
            "OK_distribution": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("OK")],
            "LOW_VARIANCE": [k for k, v in checks.items() if str(v.get("verdict", "")).startswith("LOW_VARIANCE")],
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    logger.info("Wrote %s", OUT)

    # Print summary
    print("\n=== Summary ===")
    for cat, cols in summary["categories"].items():
        print(f"  {cat}: {len(cols)} → {cols}")


if __name__ == "__main__":
    main()
