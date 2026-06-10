#!/usr/bin/env python3
"""Run PP-HCOEF37: extended repeated validation for HCOEF36 routing candidates.

HCOEF36 produced a small fixed-test improvement over the stable Warm Huber
candidate by routing HCOEF35 basis-residual candidates only to low-risk rows.
The improvement was not strong enough in the 24-repeat all3 OOF gate. This
script does not tune new boundaries from test results. It revalidates the
predefined HCOEF36 routing candidates with more row/artist repeated splits.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef34_warm_huber_price_basis_coefficient_refinement as h34
from scripts.track6 import run_pp_hcoef36_warm_huber_price_basis_coefficient_refinement as h36


EXP_ID = "PP-HCOEF37"
EXP_SLUG = "PP-HCOEF37_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
SEED = 20260609
N_REPEATS = 60

REFERENCE = h34.REFERENCE
STABLE_ALIAS = h34.STABLE_ALIAS

FOCUS_CANDIDATES = [
    "hcoef36_route_basis_balanced_all_cap0p005_s0p5__spread_q66",
    "hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66",
    "hcoef36_route_basis_balanced_all_cap0p005_s0p5__n_ge5_spread_q66_area90",
    "hcoef36_route_p95_near_all_cap0p0075_s0p2__precise_level_spread_q75",
    "hcoef36_route_p95_near_all_cap0p0075_s0p2__gap_q75",
    "hcoef36_route_p95_near_all_cap0p0075_s0p2__n_ge5_spread_q66",
    "hcoef36_route_best_mdape_all_cap0p01_s0p35__spread_q66",
    "hcoef36_route_best_mdape_all_cap0p01_s0p35__n_ge5_spread_q66",
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)


def selected_configs() -> list[h36.RoutingConfig]:
    by_name = {config.candidate: config for config in h36.candidate_configs()}
    missing = [candidate for candidate in FOCUS_CANDIDATES if candidate not in by_name]
    if missing:
        raise KeyError(f"HCOEF36 candidate config missing: {missing}")
    return [by_name[candidate] for candidate in FOCUS_CANDIDATES]


def patch_h36_runtime() -> None:
    """Reuse HCOEF36 functions while writing HCOEF37 identifiers."""
    h36.EXP_ID = EXP_ID
    h36.N_REPEATS = N_REPEATS
    h36.SEED = SEED


def add_repeat_gates(selected: pd.DataFrame) -> pd.DataFrame:
    out = selected.copy()
    out["min_stable_any2_improve_prob"] = out[
        ["row_oof_stable_any2_improve_prob", "artist_oof_stable_any2_improve_prob"]
    ].min(axis=1)
    out["min_stable_all3_improve_prob"] = out[
        ["row_oof_stable_all3_improve_prob", "artist_oof_stable_all3_improve_prob"]
    ].min(axis=1)
    out["min_ref_any2_improve_prob"] = out[
        ["row_oof_ref_any2_improve_prob", "artist_oof_ref_any2_improve_prob"]
    ].min(axis=1)
    out["extended_repeat_decision"] = np.select(
        [
            (out["min_stable_all3_improve_prob"] >= 0.95)
            & (out["fixed_p95_margin_vs_stable"] <= 0)
            & (out["stress0604_p95_margin_vs_stable"] <= 0.0005),
            (out["min_stable_all3_improve_prob"] >= 0.90)
            & (out["fixed_p95_margin_vs_stable"] <= 0)
            & (out["stress0604_p95_margin_vs_stable"] <= 0.0005),
            (out["min_stable_any2_improve_prob"] >= 0.90)
            & (out["fixed_p95_margin_vs_stable"] <= 0)
            & (out["stress0604_p95_margin_vs_stable"] <= 0.0005),
            (out["min_ref_any2_improve_prob"] >= 0.90)
            & (out["fixed_p95_margin_vs_stable"] <= 0),
        ],
        [
            "운영 후보 검토",
            "강한 반복 검증 후보",
            "Warm 안정 반복 검증 후보",
            "기존 70:30 대비 p95 방어 후보",
        ],
        default="보류",
    )
    return out.sort_values(
        [
            "extended_repeat_decision",
            "min_stable_all3_improve_prob",
            "min_stable_any2_improve_prob",
            "test_MdAPE",
            "test_MAPE",
        ],
        ascending=[True, False, False, True, True],
    )


def short_metric_table(fixed_metrics: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    cols = [
        "split",
        "candidate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE_vs_stable",
        "delta_MAPE_vs_stable",
        "delta_p95_APE_vs_stable",
        "route_rule",
        "route_coverage",
    ]
    keep = [REFERENCE, STABLE_ALIAS, *candidates]
    return fixed_metrics[fixed_metrics["candidate"].isin(keep)][cols].copy()


def write_report(
    fixed_metrics: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    selected: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    policy: pd.DataFrame,
) -> None:
    top = selected.head(1)
    if top.empty:
        conclusion = "- 선택 후보 없음."
    else:
        row = top.iloc[0]
        conclusion = (
            f"- 최상위 후보: `{row['candidate']}`.\n"
            f"- 판단: {row['extended_repeat_decision']}.\n"
            f"- fixed test MdAPE/MAPE/p95: "
            f"`{row['test_MdAPE']:.6f}/{row['test_MAPE']:.6f}/{row['test_p95_APE']:.6f}`.\n"
            f"- hcoef_stable 대비 fixed delta MdAPE/MAPE/p95: "
            f"`{row['delta_MdAPE_vs_stable']:.6f}/{row['delta_MAPE_vs_stable']:.6f}/{row['delta_p95_APE_vs_stable']:.6f}`.\n"
            f"- row/artist min stable any2/all3: "
            f"`{row['min_stable_any2_improve_prob']:.4f}/{row['min_stable_all3_improve_prob']:.4f}`."
        )

    report_cols = [
        "candidate",
        "extended_repeat_decision",
        "base_improver",
        "route_rule",
        "route_coverage",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "min_stable_any2_improve_prob",
        "min_stable_all3_improve_prob",
        "fixed_p95_margin_vs_stable",
        "stress0604_p95_margin_vs_stable",
    ]
    repeated_cols = [
        "validation_scheme",
        "candidate",
        "n_repeats",
        "mean_MdAPE",
        "mean_MAPE",
        "mean_p95_APE",
        "mean_delta_MdAPE_vs_stable",
        "mean_delta_MAPE_vs_stable",
        "mean_delta_p95_APE_vs_stable",
        "stable_any2_improve_prob",
        "stable_all3_improve_prob",
        "stable_p95_improve_prob",
    ]
    coef_cols = [
        "candidate",
        "base_improver",
        "route_rule",
        "feature",
        "coefficient_on_scaled_feature",
        "direction",
    ]
    policy_cols = [
        "candidate",
        "split",
        "route_rule",
        "route_coverage",
        "route_n",
        "basis_component_spread_max",
        "abs_fallback_stable_gap_max",
        "log_area_min",
        "log_area_max",
    ]

    md = "\n".join(
        [
            "# PP-HCOEF37 Warm Huber 확장 반복 검증 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF36 상위 라우팅 후보가 fixed test에서만 우연히 좋아진 것인지, row/artist 반복 검증에서도 유지되는지 확인.",
            "- 기준 후보: `current_70_30`.",
            "- 운영 비교 후보: `hcoef_stable`.",
            f"- 반복 수: row OOF `{N_REPEATS}`회, artist OOF `{N_REPEATS}`회.",
            "- 선택 원칙: HCOEF36에서 이미 정의된 후보와 라우팅 경계만 사용. fixed test/0604 residual로 새 경계를 만들지 않음.",
            "",
            "## 1. 실행 결론",
            "",
            conclusion,
            "- HCOEF37은 새 피처 탐색 실험이 아니라 HCOEF36 후보의 안정성 재검증 실험이다.",
            "",
            "## 2. fixed test / 0604 확인 지표",
            "",
            h36.markdown_table(short_metric_table(fixed_metrics, FOCUS_CANDIDATES), 40),
            "",
            "## 3. 후보 판단",
            "",
            h36.markdown_table(selected[report_cols], 20),
            "",
            "## 4. 반복 OOF 요약",
            "",
            h36.markdown_table(
                repeated_summary[repeated_cols].sort_values(
                    ["stable_any2_improve_prob", "stable_all3_improve_prob", "mean_MdAPE"],
                    ascending=[False, False, True],
                ),
                30,
            ),
            "",
            "## 5. 라우팅 정책",
            "",
            h36.markdown_table(policy[policy_cols], 30),
            "",
            "## 6. Huber 계수 해석",
            "",
            "- 계수는 HCOEF35 base improver의 residual Huber 모델 기준이다.",
            "- 양수 계수는 stable 예측에 보정값을 더하는 방향이다.",
            "- 음수 계수는 stable 예측에서 보정값을 빼는 방향이다.",
            "",
            h36.markdown_table(coeffs.sort_values("abs_coefficient", ascending=False)[coef_cols], 40)
            if not coeffs.empty
            else "_계수 없음_",
            "",
            "## 7. 잔차와 큰 오차 확인",
            "",
            h36.markdown_table(residuals, 40),
            "",
            "## 8. 판단 기준",
            "",
            "- 운영 후보: min stable all3 `0.95` 이상, fixed/0604 p95 방어, fixed test 3지표 모두 동등 또는 개선.",
            "- 강한 반복 검증 후보: min stable all3 `0.90` 이상, fixed/0604 p95 방어.",
            "- Warm 안정 반복 검증 후보: min stable any2 `0.90` 이상, fixed/0604 p95 방어.",
            "- 기존 70:30 대비 p95 방어 후보: current_70_30 대비는 충분히 좋지만 hcoef_stable 반복 검증이 약한 후보.",
            "",
            "## 9. 산출물",
            "",
            "- `artifacts/experiment_config.json`",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/policy_map.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/repeated_iteration_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h36.md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    patch_h36_runtime()
    configs = selected_configs()
    frames = h34.build_frames()

    fixed_metrics, fixed_preds, coeffs, policy = h36.fixed_confirmation(frames, configs)
    repeated_metrics, repeated_preds = h36.repeated_oof(frames["validation"], configs)
    repeated_summary = h36.summarize_repeated(repeated_metrics)
    selected = add_repeat_gates(h36.select_candidates(fixed_metrics, repeated_summary))

    predictions = pd.concat([fixed_preds, repeated_preds], ignore_index=True)
    residuals = h36.residual_analysis(predictions, {REFERENCE, STABLE_ALIAS, *selected.head(8)["candidate"].tolist()})
    metrics = pd.concat([fixed_metrics, repeated_metrics], ignore_index=True)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    policy.to_csv(out / "policy_map.csv", index=False)
    repeated_metrics.to_csv(out / "repeated_iteration_metrics.csv", index=False)
    repeated_summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    selected.to_csv(out / "selected_candidates.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)

    config_payload: dict[str, Any] = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "n_repeats": N_REPEATS,
        "reference": REFERENCE,
        "stable_alias": STABLE_ALIAS,
        "focus_candidates": FOCUS_CANDIDATES,
        "selection_policy": "HCOEF36 candidates fixed; extended row/artist repeated OOF first; fixed test/0604 confirmation only",
        "no_leakage_policy": [
            "no fixed test residual tuning",
            "no 0604 residual tuning",
            "routing thresholds are inherited from HCOEF36 validation-only definitions",
        ],
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_report(fixed_metrics, repeated_summary, selected, coeffs, residuals, policy)
    print(f"[{EXP_ID}] done -> {EXP_DIR}")


if __name__ == "__main__":
    main()
