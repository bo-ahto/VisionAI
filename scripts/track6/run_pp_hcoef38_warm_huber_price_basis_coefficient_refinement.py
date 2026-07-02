#!/usr/bin/env python3
"""Run PP-HCOEF38: stricter low-risk routing for Warm Huber HCOEF candidates.

HCOEF37 confirmed that the best HCOEF36 low-risk routing candidates improve
fixed test metrics and have strong any2 repeated stability, but all3 stability
is still weak. This experiment does not use fixed test or 0604 residuals to
create new rules. It tightens validation-defined routing masks to see whether a
smaller, more reliable application area can improve MdAPE/MAPE/p95 together.
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


EXP_ID = "PP-HCOEF38"
EXP_SLUG = "PP-HCOEF38_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
SEED = 20260609
N_REPEATS = 60

REFERENCE = h34.REFERENCE
STABLE_ALIAS = h34.STABLE_ALIAS
STABLE_TEST_P95 = h36.STABLE_TEST_P95
STABLE_0604_P95 = h36.STABLE_0604_P95


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)


def strict_improvers() -> list[tuple[str, h34.CandidateConfig]]:
    by_name = {config.candidate: config for config in h36.improver_configs()}
    specs = [
        ("basis_balanced_all_cap0p005_s0p5", "hcoef35_basis_balanced_basis_resid_all_a0p001_cap0p005_s0p5"),
        ("best_mdape_all_cap0p01_s0p35", "hcoef35_best_mdape_basis_resid_all_a0p01_cap0p01_s0p35"),
        ("p95_near_all_cap0p0075_s0p2", "hcoef35_p95_near_basis_resid_all_a0p001_cap0p0075_s0p2"),
    ]
    missing = [name for _, name in specs if name not in by_name]
    if missing:
        raise KeyError(f"Missing HCOEF35 improver configs: {missing}")
    return [(label, by_name[name]) for label, name in specs]


def strict_rules() -> list[h36.RoutingRule]:
    """Validation-defined rules stricter than HCOEF36/37.

    The rules are intentionally low dimensional and interpretable:
    - spread: disagreement among basis components
    - gap: distance between fallback basis and stable prediction
    - n: fallback comparable sample count
    - area: avoid extreme sizes
    - precise level: use only artist+condition basis levels
    """
    return [
        h36.RoutingRule(
            "spread_q50",
            "기준가 컴포넌트 차이가 validation 하위 50%인 행",
            spread_q=0.50,
        ),
        h36.RoutingRule(
            "n_ge5_spread_q50",
            "표본 수 5개 이상이고 기준가 컴포넌트 차이가 하위 50%인 행",
            min_n=5,
            spread_q=0.50,
        ),
        h36.RoutingRule(
            "n_ge10_spread_q50",
            "표본 수 10개 이상이고 기준가 컴포넌트 차이가 하위 50%인 행",
            min_n=10,
            spread_q=0.50,
        ),
        h36.RoutingRule(
            "n_ge5_spread_q50_gap_q50",
            "표본 수 5개 이상, 기준가 차이 하위 50%, fallback-stable gap 하위 50%인 행",
            min_n=5,
            spread_q=0.50,
            abs_gap_q=0.50,
        ),
        h36.RoutingRule(
            "n_ge10_spread_q50_gap_q50",
            "표본 수 10개 이상, 기준가 차이 하위 50%, fallback-stable gap 하위 50%인 행",
            min_n=10,
            spread_q=0.50,
            abs_gap_q=0.50,
        ),
        h36.RoutingRule(
            "n_ge5_spread_q50_area80",
            "표본 수 5개 이상, 기준가 차이 하위 50%, 면적 중앙 80%인 행",
            min_n=5,
            spread_q=0.50,
            area_mid_q=0.80,
        ),
        h36.RoutingRule(
            "n_ge10_spread_q66_area80",
            "표본 수 10개 이상, 기준가 차이 하위 66%, 면적 중앙 80%인 행",
            min_n=10,
            spread_q=0.66,
            area_mid_q=0.80,
        ),
        h36.RoutingRule(
            "precise_level_spread_q50",
            "작가+재료 또는 작가+크기+재료 기준가가 있고 기준가 차이가 하위 50%인 행",
            spread_q=0.50,
            levels=("artist_medium_support", "artist_size_medium_support"),
        ),
        h36.RoutingRule(
            "precise_level_spread_q66_gap_q50",
            "정밀 기준가 level이 있고 기준가 차이 하위 66%, fallback-stable gap 하위 50%인 행",
            spread_q=0.66,
            abs_gap_q=0.50,
            levels=("artist_medium_support", "artist_size_medium_support"),
        ),
    ]


def candidate_configs() -> list[h36.RoutingConfig]:
    configs: list[h36.RoutingConfig] = []
    for label, improver in strict_improvers():
        for rule in strict_rules():
            configs.append(
                h36.RoutingConfig(
                    candidate=f"hcoef38_route_{label}__{rule.rule_key}",
                    improver=improver,
                    rule=rule,
                    description=f"{rule.description}; base={improver.candidate}",
                )
            )
    return configs


def patch_h36_runtime() -> None:
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
    decision_order = {
        "운영 후보 검토": 0,
        "강한 반복 검증 후보": 1,
        "Warm 안정 반복 검증 후보": 2,
        "기존 70:30 대비 p95 방어 후보": 3,
        "보류": 4,
    }
    out["_decision_order"] = out["extended_repeat_decision"].map(decision_order).fillna(9)
    return out.sort_values(
        [
            "_decision_order",
            "min_stable_all3_improve_prob",
            "min_stable_any2_improve_prob",
            "test_MdAPE",
            "test_MAPE",
        ],
        ascending=[True, False, False, True, True],
    ).drop(columns=["_decision_order"])


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
    configs: list[h36.RoutingConfig],
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

    focus_candidates = selected.head(12)["candidate"].tolist()
    md = "\n".join(
        [
            "# PP-HCOEF38 Warm Huber stricter low-risk routing 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF37에서 any2 안정성은 확인됐지만 all3가 약했던 low-risk routing 후보를 더 엄격한 구간에만 적용해 all3 안정성이 올라가는지 확인.",
            "- 기준 후보: `current_70_30`.",
            "- 운영 비교 후보: `hcoef_stable`.",
            f"- 반복 수: row OOF `{N_REPEATS}`회, artist OOF `{N_REPEATS}`회.",
            "- 선택 원칙: 라우팅 경계는 validation/OOF 기반 quantile과 표본 수 조건만 사용. fixed test/0604 residual은 사용하지 않음.",
            "",
            "## 1. 실행 결론",
            "",
            conclusion,
            "- HCOEF38은 더 많은 피처를 넣는 실험이 아니라 적용 구간을 더 보수적으로 줄이는 실험이다.",
            "",
            "## 2. fixed test / 0604 확인 지표",
            "",
            h36.markdown_table(short_metric_table(fixed_metrics, focus_candidates).round(4), 60),
            "",
            "## 3. 후보 판단",
            "",
            h36.markdown_table(selected[report_cols].round(4), 30),
            "",
            "## 4. 반복 OOF 요약",
            "",
            h36.markdown_table(
                repeated_summary[repeated_summary["candidate"].isin(focus_candidates)][repeated_cols].round(4),
                40,
            ),
            "",
            "## 5. 라우팅 정책",
            "",
            h36.markdown_table(policy[policy["candidate"].isin(focus_candidates)][policy_cols].round(4), 50),
            "",
            "## 6. Huber 계수 해석",
            "",
            "- 계수는 HCOEF35 base improver의 residual Huber 모델 기준이다.",
            "- 양수 계수는 stable 예측에 보정값을 더하는 방향이다.",
            "- 음수 계수는 stable 예측에서 보정값을 빼는 방향이다.",
            "",
            h36.markdown_table(
                coeffs[coeffs["candidate"].isin(focus_candidates)]
                .sort_values("abs_coefficient", ascending=False)[coef_cols]
                .round(4),
                40,
            )
            if not coeffs.empty
            else "_계수 없음_",
            "",
            "## 7. 잔차와 큰 오차 확인",
            "",
            h36.markdown_table(residuals.round(4), 40),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/policy_map.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/repeated_validation_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h36.md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    patch_h36_runtime()
    configs = candidate_configs()
    frames = h34.build_frames()
    fixed_metrics, fixed_preds, coeffs, policy = h36.fixed_confirmation(frames, configs)
    repeated_metrics, repeated_preds = h36.repeated_oof(frames["validation"], configs)
    repeated_summary = h36.summarize_repeated(repeated_metrics)
    selected = add_repeat_gates(h36.select_candidates(fixed_metrics, repeated_summary))
    focus = set(selected.head(15)["candidate"]) | {REFERENCE, STABLE_ALIAS}
    predictions = pd.concat([fixed_preds, repeated_preds], ignore_index=True)
    residuals = h36.residual_analysis(predictions, focus)

    all_metrics = pd.concat([fixed_metrics, repeated_metrics], ignore_index=True)
    out = EXP_DIR / "outputs"
    all_metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    policy.to_csv(out / "policy_map.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    repeated_summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    repeated_summary.to_csv(out / "repeated_validation_summary.csv", index=False)
    selected.to_csv(out / "selected_candidates.csv", index=False)

    config_payload: dict[str, Any] = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference": REFERENCE,
        "stable_alias": STABLE_ALIAS,
        "n_repeats": N_REPEATS,
        "seed": SEED,
        "n_candidates": len(configs),
        "improvers": [
            {"label": label, **improver.__dict__}
            for label, improver in strict_improvers()
        ],
        "routing_rules": [rule.__dict__ for rule in strict_rules()],
        "selection_policy": [
            "validation/OOF first",
            "fixed test and 0604 confirmation only",
            "stricter routing after HCOEF37 any2-only stability",
            "no test residual based routing",
        ],
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(fixed_metrics, repeated_summary, selected, coeffs, residuals, policy, configs)
    print(f"[{EXP_ID}] done -> {EXP_DIR}")
    print(selected.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
