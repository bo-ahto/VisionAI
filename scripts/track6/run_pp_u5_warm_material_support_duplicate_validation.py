#!/usr/bin/env python3
"""Run PP-U5 Warm Huber material/support duplicate validation."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pp_u_experiments import BASE_EXP_DIR, artifact_features, run_experiment, unique  # noqa: E402


EXP_ID = "PP-U5"


def replace_summary_rows(new_rows: pd.DataFrame) -> None:
    summary_path = BASE_EXP_DIR / "PP-U_summary_metrics.csv"
    pp_u5_path = BASE_EXP_DIR / "PP-U5_summary_metrics.csv"
    new_rows.to_csv(pp_u5_path, index=False)
    if summary_path.exists():
        existing = pd.read_csv(summary_path)
        existing = existing[existing["experiment_id"] != EXP_ID]
        summary = pd.concat([existing, new_rows], ignore_index=True)
    else:
        summary = new_rows
    summary.to_csv(summary_path, index=False)


def build_pp_u5_info() -> dict[str, object]:
    warm_base = artifact_features()["warm"]
    material_cols = ["medium_category", "support_category", "medium_support_bucket"]

    base_without_material = [col for col in warm_base if col not in material_cols]
    all_three = warm_base
    raw_only = unique(base_without_material + ["medium_category", "support_category"])
    combo_only = unique(base_without_material + ["medium_support_bucket"])
    medium_only = unique(base_without_material + ["medium_category"])
    support_only = unique(base_without_material + ["support_category"])
    no_material = base_without_material

    candidates = [
        (
            "baseline_all_three",
            "현재 기준 구조",
            all_three,
            "현재 Warm Huber 기준 피처셋처럼 원본 재료, 원본 지지체, 조합 피처를 모두 사용",
        ),
        (
            "raw_medium_support_only",
            "원본 재료/지지체만 사용",
            raw_only,
            "조합 피처 없이 원본 재료와 지지체만으로 충분한지 확인",
        ),
        (
            "combo_bucket_only",
            "조합 피처만 사용",
            combo_only,
            "재료와 지지체를 각각 쓰지 않고 조합 bucket 하나로 설명 가능한지 확인",
        ),
        (
            "medium_only",
            "재료만 사용",
            medium_only,
            "재료 대분류만으로 보조 신호가 충분한지 확인",
        ),
        (
            "support_only",
            "지지체만 사용",
            support_only,
            "지지체 대분류만으로 보조 신호가 충분한지 확인",
        ),
        (
            "no_material_support",
            "재료/지지체 제거",
            no_material,
            "재료/지지체 정보 자체가 Warm Huber에서 필요한지 재확인",
        ),
    ]

    return {
        "slug": "PP-U5_warm_huber_material_support_duplicate_validation",
        "title": "Warm Huber 재료/지지체 중복 분리 검증",
        "scope": "warm",
        "model": "huber",
        "baseline_candidate": "baseline_all_three",
        "candidates": candidates,
    }


def main() -> None:
    start = time.time()
    info = build_pp_u5_info()
    metrics_df = run_experiment(EXP_ID, info)
    replace_summary_rows(metrics_df)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment": str((BASE_EXP_DIR / str(info["slug"])).relative_to(BASE_EXP_DIR.parents[1])),
        "summary": str((BASE_EXP_DIR / "PP-U5_summary_metrics.csv").relative_to(BASE_EXP_DIR.parents[1])),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
