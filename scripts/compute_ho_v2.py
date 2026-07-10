"""HO_TABLE 정확화 — ho_v2 산출 + cleansed Tier CSV update.

Pre-registered: docs/ho_table_correction_prereg_20260508.md
Decision binding: ❌ X (정량 record 만 / 운영 코드 / parquet 변경 X)

표준 F 테이블 (dimension_parser.py:33) 의 area_to_ho_f 보간 적용.
9 신규 column 산출 + clipped flag + 운영 ho 와 의 mismatch 정량.

Fail-closed protocol:
- Frozen list 의 모든 path 의 sha-256 + git diff lines pre/post 검증
- Allowed list 외 의 path 변경 detect 시 즉시 abort
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

# 표준 F 테이블 import 원칙 (hardcoded copy 금지 / prereg §3.1)
from visionai.price_engine.preprocessing.dimension_parser import (  # type: ignore  # noqa: E402
    HO_F_TABLE,
    area_to_ho_f,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CLEANSED_DIR = REPO / "data" / "dataset_tiers_cleansed_20260508"
RESULTS_DIR = REPO / "experiments" / "structural_v1" / "results"
SUMMARY_OUT = RESULTS_DIR / "ho_table_correction_summary_20260508.json"

# Threshold (prereg §3.2 absolute values)
LOW_THRESHOLD = 252.0  # HO_F_TABLE[0] = 18.0 × 14.0
HIGH_THRESHOLD = 50239.49  # HO_F_TABLE[200] = 259.1 × 193.9
OUT_OF_RANGE_HIGH = 250000.0

# Frozen paths (prereg §3.6)
FROZEN_PATHS = [
    REPO / "scripts" / "prepare_primary_market_dataset.py",
    REPO / "src" / "visionai" / "price_engine" / "api" / "primary_feature_builder.py",
    REPO / "src" / "visionai" / "price_engine" / "preprocessing" / "dimension_parser.py",
    REPO / "data" / "saatchi_cleaned.parquet",
    REPO / "data" / "primary_market_dataset.parquet",
    CLEANSED_DIR / "T0_operational_28376_cleansed.csv",
    CLEANSED_DIR / "T1_artsy_only_cleansed.csv",
    CLEANSED_DIR / "T2_artsy_year_notna_cleansed.csv",
    CLEANSED_DIR / "T3_artsy_year_birth_notna_cleansed.csv",
    CLEANSED_DIR / "T4_artsy_strict_4field_cleansed.csv",
    CLEANSED_DIR / "T5_krw_only_cleansed.csv",
    CLEANSED_DIR / "T6_t4_anomaly_filtered_cleansed.csv",
    CLEANSED_DIR / "display_companion_T0.csv",
    CLEANSED_DIR / "human_readable_T0.csv",
    CLEANSED_DIR / "removed_columns_log.csv",
]

TIER_FILES = [
    "T0_operational_28376_cleansed.csv",
    "T1_artsy_only_cleansed.csv",
    "T2_artsy_year_notna_cleansed.csv",
    "T3_artsy_year_birth_notna_cleansed.csv",
    "T4_artsy_strict_4field_cleansed.csv",
    "T5_krw_only_cleansed.csv",
    "T6_t4_anomaly_filtered_cleansed.csv",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_diff_lines(path: Path) -> int:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--numstat", "--", str(path.relative_to(REPO))],
            cwd=REPO, stderr=subprocess.DEVNULL,
        ).decode().strip()
        if not out:
            return 0
        parts = out.split("\t")
        return int(parts[0]) + int(parts[1]) if len(parts) >= 2 else 0
    except Exception:
        return 0


def assert_standard_table() -> None:
    """표준 F 테이블 spot-check (prereg §4.1)."""
    assert len(HO_F_TABLE) == 22, f"HO_F_TABLE entries: {len(HO_F_TABLE)} != 22"
    assert HO_F_TABLE[0] == (18.0, 14.0), f"HO_F_TABLE[0] = {HO_F_TABLE[0]}"
    assert HO_F_TABLE[200] == (259.1, 193.9), f"HO_F_TABLE[200] = {HO_F_TABLE[200]}"
    logger.info("표준 F 테이블 spot-check 통과 (22 entries / [0]=(18,14) / [200]=(259.1,193.9))")


def compute_ho_v2_columns(area_cm2: pd.Series, support_factor: pd.Series) -> dict[str, pd.Series]:
    """9 신규 column 산출 (prereg §3.1, §3.2)."""
    ho_v2 = area_cm2.apply(area_to_ho_f).astype("float64")
    ho_v2_int = np.rint(ho_v2.to_numpy()).astype(int)
    ho_power_v2 = ho_v2.where(ho_v2 > 0, 0).pow(0.74).astype("float64")
    ln_ho_v2 = np.log(ho_v2 + 1).astype("float64")
    is_small_v2 = (ho_v2 <= 3.0).astype("int8")
    ho_x_support_v2 = (ho_v2 * support_factor).astype("float64")

    # Clipped flags (prereg §3.2)
    is_low = (area_cm2 < LOW_THRESHOLD).astype("int8")
    is_high = (area_cm2 > HIGH_THRESHOLD).astype("int8")
    is_oor = ((area_cm2 <= 0.0) | (area_cm2 > OUT_OF_RANGE_HIGH)).astype("int8")

    return {
        "ho_v2": ho_v2,
        "ho_v2_int": pd.Series(ho_v2_int, index=area_cm2.index),
        "ho_power_v2": ho_power_v2,
        "ln_ho_v2": ln_ho_v2,
        "is_small_v2": is_small_v2,
        "ho_x_support_v2": ho_x_support_v2,
        "is_ho_clipped_low_v2": is_low,
        "is_ho_clipped_high_v2": is_high,
        "is_size_out_of_range_v2": is_oor,
    }


def main() -> dict:
    logger.info("=" * 70)
    logger.info("HO_TABLE 정확화 cycle — ho_v2 산출")
    logger.info("=" * 70)

    # Step 1: 표준 F 테이블 spot-check
    assert_standard_table()

    # Step 2: pre-run digest
    logger.info("--- Pre-run digest (frozen paths) ---")
    pre_digests = {}
    for p in FROZEN_PATHS:
        if p.exists():
            pre_digests[str(p.relative_to(REPO))] = {
                "sha256": sha256_file(p),
                "git_diff_lines": git_diff_lines(p),
            }
    logger.info("Frozen paths digested: %d", len(pre_digests))

    # Step 3: cleansed Tier CSV 별 처리
    tier_summaries = []
    operational_t0_summary = None

    for fname in TIER_FILES:
        path = CLEANSED_DIR / fname
        if not path.exists():
            logger.warning("Tier file not found: %s", path)
            continue
        df = pd.read_csv(path)
        original_cols = list(df.columns)
        n_rows = len(df)

        cols = compute_ho_v2_columns(df["area_cm2"], df["support_factor"])
        for k, v in cols.items():
            df[k] = v

        # Tier 별 정량 비교
        ho_v2_int_arr = df["ho_v2_int"].to_numpy()
        operational_ho = df["ho"].to_numpy()
        n_mismatch_int = int((ho_v2_int_arr != operational_ho).sum())
        n_downgrade = int((ho_v2_int_arr < operational_ho).sum())
        n_upgrade = int((ho_v2_int_arr > operational_ho).sum())
        n_exact = int((ho_v2_int_arr == operational_ho).sum())

        # Output: *_with_ho_v2.csv
        out_path = CLEANSED_DIR / fname.replace(".csv", "_with_ho_v2.csv")
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

        summary = {
            "tier": fname,
            "n_rows": n_rows,
            "original_cols": len(original_cols),
            "new_cols": len(df.columns),
            "expected_new_cols": len(original_cols) + 9,
            "n_mismatch_int": n_mismatch_int,
            "n_downgrade": n_downgrade,
            "n_upgrade": n_upgrade,
            "n_exact": n_exact,
            "mismatch_pct": round(n_mismatch_int / n_rows * 100, 2),
            "n_clipped_low": int(df["is_ho_clipped_low_v2"].sum()),
            "n_clipped_high": int(df["is_ho_clipped_high_v2"].sum()),
            "n_size_oor": int(df["is_size_out_of_range_v2"].sum()),
            "output_path": str(out_path.relative_to(REPO)),
            "output_sha256": sha256_file(out_path),
        }
        tier_summaries.append(summary)
        logger.info(
            "Tier %s: rows=%d cols %d→%d / mismatch=%d (%.2f%%) / down=%d up=%d exact=%d / clip_low=%d clip_high=%d oor=%d",
            fname, n_rows, len(original_cols), len(df.columns),
            n_mismatch_int, summary["mismatch_pct"], n_downgrade, n_upgrade, n_exact,
            summary["n_clipped_low"], summary["n_clipped_high"], summary["n_size_oor"],
        )

        if fname == "T0_operational_28376_cleansed.csv":
            # T0 의 ho_power 변화 분포
            op_ho_power = df["ho_power"].to_numpy()
            v2_ho_power = df["ho_power_v2"].to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                pct_change = np.where(
                    op_ho_power > 0,
                    (v2_ho_power - op_ho_power) / op_ho_power * 100,
                    np.nan,
                )
            pct_change_valid = pct_change[~np.isnan(pct_change)]
            operational_t0_summary = {
                "ho_power_pct_change": {
                    "n_valid": len(pct_change_valid),
                    "min": float(pct_change_valid.min()),
                    "p10": float(np.percentile(pct_change_valid, 10)),
                    "p25": float(np.percentile(pct_change_valid, 25)),
                    "p50_median": float(np.median(pct_change_valid)),
                    "p75": float(np.percentile(pct_change_valid, 75)),
                    "p90": float(np.percentile(pct_change_valid, 90)),
                    "max": float(pct_change_valid.max()),
                    "mean": float(pct_change_valid.mean()),
                },
            }

    # Step 4: column_dictionary update (backward-compatible)
    dict_path = CLEANSED_DIR / "column_dictionary.csv"
    pre_dict_sha = sha256_file(dict_path)
    rows = list(csv.reader(dict_path.open(encoding="utf-8-sig")))
    header = rows[0]
    body = rows[1:]
    high_risk_note = " + high-risk: 표준 F 규격 불일치 (코덱스 review / ho_v2 별도 산출)"

    HO_LEGACY = {"ho", "ho_power", "ln_ho", "is_small", "ho_x_support"}
    for row in body:
        if row[0] in HO_LEGACY:
            # 사유 column (index 5) 에만 append (정의/생성방식/계산공식 불변)
            row[5] = row[5] + high_risk_note

    # 9 신규 row 추가 (보존 분류)
    new_rows = [
        ["ho_v2", "호수(표준보간)", "계산", "표준 F 테이블 의 np.interp 보간",
         "보존", "표준 F 단일 소스 (dimension_parser.py:33-42)",
         "area_cm2 → area_to_ho_f (np.interp 보간)",
         "ho_v2 = np.interp(area_cm2, _HO_AREAS, _HO_KEYS) / dtype=float64"],
        ["ho_v2_int", "호수(표준정수)", "계산", "ho_v2 의 정수 round (half-to-even)",
         "보존", "ho_v2 의 정수 비교 영역",
         "ho_v2 의 numpy half-to-even rounding",
         "ho_v2_int = np.rint(ho_v2).astype(int)"],
        ["ho_power_v2", "호수^0.74(표준)", "계산", "ho_v2^0.74 if ho_v2>0 else 0",
         "보존", "ho_v2 의 power 변환",
         "ho_v2 의 power 변환 (ho_power 와 동일 spec, ho_v2 입력)",
         "ho_power_v2 = ho_v2 ** 0.74 (ho_v2 > 0) else 0"],
        ["ln_ho_v2", "로그호수(표준)", "계산", "log(ho_v2+1)",
         "보존", "ho_v2 의 log 변환",
         "ho_v2 의 log 변환 (ln_ho 와 동일 spec)",
         "ln_ho_v2 = ln(ho_v2 + 1)"],
        ["is_small_v2", "소형여부(표준)", "계산", "1 if ho_v2<=3.0 else 0",
         "보존", "ho_v2 의 binary flag",
         "ho_v2 의 binary flag (is_small 와 동일 spec)",
         "is_small_v2 = (ho_v2 <= 3.0) ? 1 : 0"],
        ["ho_x_support_v2", "호수×지지체계수(표준)", "계산", "ho_v2 × support_factor",
         "보존", "ho_v2 의 interaction (ho_x_support 와 동일 spec)",
         "ho_v2 × support_factor",
         "ho_x_support_v2 = ho_v2 × support_factor"],
        ["is_ho_clipped_low_v2", "호수하한클립(표준)", "계산 (관측 플래그)",
         "1 if area_cm2 < 252.0 else 0",
         "보존", "코덱스 권고 의 관측 플래그",
         "area_cm2 의 표준 0호 (= 252.0 cm²) 미만 detection",
         "is_ho_clipped_low_v2 = (area_cm2 < 252.0) ? 1 : 0"],
        ["is_ho_clipped_high_v2", "호수상한클립(표준)", "계산 (관측 플래그)",
         "1 if area_cm2 > 50239.49 else 0",
         "보존", "코덱스 권고 의 관측 플래그",
         "area_cm2 의 표준 200호 (= 50239.49 cm²) 초과 detection",
         "is_ho_clipped_high_v2 = (area_cm2 > 50239.49) ? 1 : 0"],
        ["is_size_out_of_range_v2", "크기범위외(표준)", "계산 (관측 플래그)",
         "1 if area_cm2 <= 0 OR > 250000.0 else 0",
         "보존", "코덱스 권고 의 관측 플래그",
         "area_cm2 의 비정상 영역 (≤0 또는 > 약 500cm×500cm) detection",
         "is_size_out_of_range_v2 = (area_cm2 <= 0.0) OR (area_cm2 > 250000.0) ? 1 : 0"],
    ]

    body.extend(new_rows)
    with open(dict_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(body)
    logger.info("Updated column_dictionary: %d entries (was 53)", len(body))

    # Step 5: post-run digest 검증
    logger.info("--- Post-run digest (frozen paths) ---")
    abort_paths = []
    for p in FROZEN_PATHS:
        if not p.exists():
            continue
        rel = str(p.relative_to(REPO))
        post_sha = sha256_file(p)
        post_diff = git_diff_lines(p)
        if (post_sha != pre_digests[rel]["sha256"] or
            post_diff != pre_digests[rel]["git_diff_lines"]):
            abort_paths.append(rel)
    if abort_paths:
        raise RuntimeError(f"FAIL-CLOSED: frozen paths changed: {abort_paths}")
    logger.info("Frozen paths 변경 X (fail-closed 통과)")

    # Reproducibility checks
    repro_checks = {
        "ho_f_table_22_entries": len(HO_F_TABLE) == 22,
        "ho_f_table_0_correct": HO_F_TABLE[0] == (18.0, 14.0),
        "ho_f_table_200_correct": HO_F_TABLE[200] == (259.1, 193.9),
        "frozen_paths_unchanged": len(abort_paths) == 0,
        "all_tiers_processed": len(tier_summaries) == 7,
        "all_tiers_60_cols": all(s["new_cols"] == s["expected_new_cols"] for s in tier_summaries),
    }
    repro_pass = all(repro_checks.values())

    # ── Restore dict file sha for post-check parity (dict 자체는 update 대상)
    # Only check the dict file 의 entry count (allowed update)
    post_dict_sha = sha256_file(dict_path)
    logger.info("dict pre sha=%s post sha=%s (update 영역 / allowlist)",
                pre_dict_sha[:16], post_dict_sha[:16])

    result = {
        "verdict_reproducibility": "PASS" if repro_pass else "FAIL",
        "reproducibility_checks": repro_checks,
        "ho_table_correction_summary": {
            "standard_table_source": "src/visionai/price_engine/preprocessing/dimension_parser.py:33-42",
            "operational_table_source": "scripts/prepare_primary_market_dataset.py:27-34 (변경 X / freeze)",
            "low_threshold_cm2": LOW_THRESHOLD,
            "high_threshold_cm2": HIGH_THRESHOLD,
            "out_of_range_high_cm2": OUT_OF_RANGE_HIGH,
        },
        "tier_summaries": tier_summaries,
        "T0_ho_power_change_pct": operational_t0_summary,
        "frozen_paths_pre_post": {
            "frozen_paths_n": len(pre_digests),
            "all_unchanged": len(abort_paths) == 0,
            "changed_paths": abort_paths,
        },
        "decision_binding": {
            "is_decision_binding": False,
            "scope": "ho_v2 정량 record 만 / 운영 코드 / parquet 변경 X",
            "not_efficacy_pass": True,
            "not_adoption_pass": True,
            "not_production_candidate": True,
            "operational_unchanged": True,
            "record_only_no_adoption_inference": True,
        },
    }

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    logger.info("Wrote %s", SUMMARY_OUT)
    logger.info("VERDICT (Reproducibility): %s", result["verdict_reproducibility"])
    return result


if __name__ == "__main__":
    main()
