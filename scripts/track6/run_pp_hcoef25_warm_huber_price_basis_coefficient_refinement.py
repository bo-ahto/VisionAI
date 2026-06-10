#!/usr/bin/env python3
"""Run PP-HCOEF25: conservative Huber coefficient tuning for Warm.

PP-HCOEF24 found useful MAPE signals from risk-shrunk comparable basis features,
but the best purpose candidates still missed the fixed-test p95 guard by a small
margin. HCOEF25 keeps the same data and validation-first evaluation protocol,
then tests smaller caps, softer strengths, and explicit high-risk fallback
signals so that MAPE/MdAPE gains do not come at the cost of large-error risk.

Fixed test and 0604 remain confirmation/stress checks only. No threshold is
chosen from their residuals.
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

from scripts.track6 import run_pp_hcoef24_warm_huber_price_basis_coefficient_refinement as h24


EXP_ID = "PP-HCOEF25"
EXP_SLUG = "PP-HCOEF25_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

BASELINE = h24.BASELINE
REFERENCE = h24.REFERENCE
PPV8 = h24.PPV8
SVC = h24.SVC
L10_COL = h24.L10_COL
POLICIES = h24.POLICIES
CandidateConfig = h24.CandidateConfig


def activate_experiment_namespace() -> None:
    """Make reused HCOEF24 helpers write HCOEF25 metadata and folders."""
    h24.EXP_ID = EXP_ID
    h24.EXP_SLUG = EXP_SLUG
    h24.EXP_DIR = EXP_DIR
    h24.DOC_ROOT = DOC_ROOT


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def slug_float(value: float) -> str:
    return h24.slug_float(value)


def add_hcoef25_guard_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    risk_score = pd.to_numeric(out["hcoef23_risk_score"], errors="coerce").fillna(0.0)
    high_risk = (
        out["risk_qwidth_extreme"].eq(1.0)
        | out["risk_gap_020_plus"].eq(1.0)
        | out["risk_spread_extreme"].eq(1.0)
        | risk_score.ge(2.0)
    )
    low_risk = risk_score.eq(0.0) & out["risk_low_n"].eq(0.0)

    out["hcoef25_low_risk_flag"] = low_risk.astype(float)
    out["hcoef25_high_risk_flag"] = high_risk.astype(float)
    out["hcoef25_guard_factor_lowrisk_only"] = low_risk.astype(float)
    out["hcoef25_guard_factor_no_extreme"] = np.where(
        high_risk,
        0.0,
        np.where(out["risk_n_10_19"].eq(1.0), 0.50, 1.0),
    )
    out["hcoef25_guard_factor_conservative"] = np.select(
        [risk_score.ge(3.0), risk_score.eq(2.0), risk_score.eq(1.0), out["risk_low_n"].eq(1.0)],
        [0.0, 0.20, 0.45, 0.50],
        default=1.0,
    )
    out["hcoef25_guard_factor_soft"] = np.select(
        [risk_score.ge(3.0), risk_score.eq(2.0), risk_score.eq(1.0), out["risk_low_n"].eq(1.0)],
        [0.15, 0.35, 0.65, 0.65],
        default=1.0,
    )

    guard_cols = [
        "hcoef25_guard_factor_lowrisk_only",
        "hcoef25_guard_factor_no_extreme",
        "hcoef25_guard_factor_conservative",
        "hcoef25_guard_factor_soft",
    ]
    for policy in POLICIES:
        for k_tag in ["k8", "k16"]:
            base_gap = f"{policy}_risk_shrunk_basis_{k_tag}_gap"
            if base_gap not in out.columns:
                continue
            for guard_col in guard_cols:
                suffix = guard_col.replace("hcoef25_guard_factor_", "")
                out[f"hcoef25_{policy}_{k_tag}_{suffix}_gap"] = (
                    pd.to_numeric(out[base_gap], errors="coerce").fillna(0.0)
                    * pd.to_numeric(out[guard_col], errors="coerce").fillna(0.0)
                )
    return out


def load_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    base, coverage = h24.load_basis_augmented_frame()
    return add_hcoef25_guard_features(base), coverage


def build_candidate_configs() -> list[CandidateConfig]:
    configs: list[CandidateConfig] = [
        CandidateConfig(BASELINE, "source", source_col=BASELINE, purpose="현재 HCOEF 안정 후보"),
        CandidateConfig(REFERENCE, "source", source_col=REFERENCE, purpose="서비스 v0.1 70:30 기준 후보"),
        CandidateConfig(PPV8, "source", source_col=PPV8, purpose="PP-V8/service component proxy"),
        CandidateConfig(SVC, "source", source_col=SVC, purpose="유사 작품 기반 가격 피처"),
        CandidateConfig("l10_seq_full_generated_bucket", "source", source_col=L10_COL, purpose="PP-L10 순차 component"),
    ]

    guard_suffixes = ["lowrisk_only", "no_extreme", "conservative", "soft"]
    for policy in POLICIES:
        for k_tag in ["k8", "k16"]:
            for guard in guard_suffixes:
                gap = f"hcoef25_{policy}_{k_tag}_{guard}_gap"
                for cap in [0.01, 0.015, 0.02, 0.03]:
                    for strength in [0.10, 0.25, 0.50]:
                        configs.append(
                            CandidateConfig(
                                candidate=(
                                    f"hcoef25_{policy}_{k_tag}_{guard}_"
                                    f"cap{slug_float(cap)}_s{slug_float(strength)}"
                                ),
                                method="basis_component",
                                gap_col=gap,
                                cap=cap,
                                strength=strength,
                                purpose="HCOEF24 기준가 이동을 위험 구간에서 더 보수적으로 제한한 후보",
                            )
                        )

        for guard in ["lowrisk_only", "no_extreme", "conservative"]:
            gap = f"hcoef25_{policy}_k8_{guard}_gap"
            feature_sets = {
                "guard_core": (
                    gap,
                    "current_minus_stable",
                    "ppv8_minus_stable",
                    "svc_minus_stable",
                    "pred_spread",
                    "quantile_width",
                    "svc_group_n_log",
                    "coverage_numeric",
                    "hcoef23_risk_score",
                    "hcoef25_high_risk_flag",
                    "hcoef25_low_risk_flag",
                ),
                "guard_reliability": (
                    gap,
                    f"{policy}_basis_first_n_log",
                    f"{policy}_basis_first_iqr",
                    f"{policy}_basis_risk_weight_k8",
                    "l10_price_range_ratio",
                    "pred_spread",
                    "quantile_width",
                    "hcoef23_risk_score",
                    "hcoef25_guard_factor_conservative",
                ),
            }
            for fs_name, features in feature_sets.items():
                for alpha in [0.001, 0.01]:
                    for cap in [0.01, 0.02, 0.03]:
                        for strength in [0.10, 0.25]:
                            configs.append(
                                CandidateConfig(
                                    candidate=(
                                        f"hcoef25_resid_huber_{policy}_{guard}_{fs_name}_"
                                        f"a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}"
                                    ),
                                    method="residual_huber",
                                    features=features,
                                    alpha=alpha,
                                    cap=cap,
                                    strength=strength,
                                    purpose="위험 guard와 작은 cap을 적용한 저차원 Huber 잔차 보정",
                                )
                            )

        direct_features = (
            BASELINE,
            REFERENCE,
            PPV8,
            SVC,
            L10_COL,
            f"hcoef25_{policy}_k8_lowrisk_only_gap",
            f"hcoef25_{policy}_k8_conservative_gap",
            f"{policy}_basis_first_n_log",
            "quantile_width",
            "pred_spread",
            "svc_group_n_log",
            "coverage_numeric",
            "hcoef23_risk_score",
            "hcoef25_high_risk_flag",
            "log_area_filled",
        )
        for alpha in [0.01]:
            for cap in [0.02, 0.03, 0.04]:
                for strength in [0.25, 0.50]:
                    configs.append(
                        CandidateConfig(
                            candidate=(
                                f"hcoef25_direct_huber_guarded_{policy}_"
                                f"a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}"
                            ),
                            method="direct_huber_capped",
                            features=direct_features,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            purpose="기준가/component를 직접 학습하되 위험 guard와 작은 cap으로 이동 제한",
                        )
                    )
    return configs


def feature_interpretation(feature: str) -> str:
    if feature.startswith("hcoef25_") and feature.endswith("_gap"):
        return "HCOEF24 기준가 이동분에 HCOEF23 위험 구간 guard를 곱한 보수적 기준가 차이다."
    if feature == "hcoef25_high_risk_flag":
        return "quantile 폭, 후보 간 gap, 예측 spread가 큰 고위험 구간 여부다."
    if feature == "hcoef25_low_risk_flag":
        return "HCOEF23 위험 신호가 없는 저위험 구간 여부다."
    if feature.startswith("hcoef25_guard_factor"):
        return "위험 구간에서 기준가 이동이나 잔차 보정 강도를 얼마나 줄일지 나타내는 계수다."
    return h24.feature_interpretation(feature)


def coefficient_table(validation: pd.DataFrame, configs: list[CandidateConfig], selected: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    focus = set(selected) | {BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket"}
    for config in configs:
        if config.candidate not in focus:
            continue
        if config.method == "source":
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": config.source_col,
                    "standardized_coefficient": 1.0,
                    "raw_role": "source_prediction",
                    "direction": "positive",
                    "interpretation": config.purpose,
                }
            )
            continue
        if config.method == "basis_component":
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": config.gap_col,
                    "standardized_coefficient": float(config.strength or 1.0),
                    "raw_role": "capped_guarded_basis_move",
                    "direction": "raises_or_lowers_with_basis",
                    "interpretation": "위험 guard가 적용된 기준가 차이를 작은 cap 안에서만 반영한다.",
                }
            )
            continue
        model = h24.fit_model(validation, config)
        final = model.steps[-1][1]
        coefs = getattr(final, "coef_", np.zeros(len(config.features)))
        for feature, coef in zip(config.features, coefs):
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": feature,
                    "standardized_coefficient": float(coef),
                    "raw_role": "residual_log" if config.method.startswith("residual_") else "actual_log_capped_to_stable",
                    "direction": "raises prediction" if coef > 0 else "lowers prediction" if coef < 0 else "neutral",
                    "interpretation": feature_interpretation(feature),
                }
            )
    return pd.DataFrame(rows)


def write_report(
    metrics_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    coefficients: pd.DataFrame,
    residuals: pd.DataFrame,
    coverage: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
) -> None:
    test = metrics_df[metrics_df["scope"].eq("fixed_confirmation")].copy()
    row_oof = metrics_df[metrics_df["scope"].eq("validation_oof_row")].copy()
    artist_oof = metrics_df[metrics_df["scope"].eq("validation_oof_artist")].copy()
    stress = metrics_df[metrics_df["scope"].eq("0604_stress")].copy()
    baseline_test = test[test["candidate"].eq(BASELINE)].iloc[0]
    ref_test = test[test["candidate"].eq(REFERENCE)].iloc[0]

    candidates_for_report = selected_df[
        ~selected_df["decision"].isin(["현재 기준 후보", "보류", "component 대조군", "최소 비교 기준"])
    ].copy()
    operating = candidates_for_report[candidates_for_report["decision"].isin(["운영 후보 검토", "반복 검증 통과 후보"])].copy()
    if not operating.empty:
        best = operating.iloc[0]
        best_line = (
            f"상위 운영 검토 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test MdAPE/MAPE/p95 "
            f"`{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`)."
        )
    elif not candidates_for_report.empty:
        best = candidates_for_report.iloc[0]
        best_line = (
            f"새 운영 기본 후보는 없음. 상위 목적별 후보는 `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test MdAPE/MAPE/p95 "
            f"`{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`). "
            "`hcoef_stable`은 계속 현재 기준 후보로 유지."
        )
    else:
        best_line = "새 운영 후보 또는 목적별 후보 없음. 현재 기준 후보 `hcoef_stable` 유지."

    top_cols = ["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable"]
    selected_cols = [
        "candidate",
        "decision",
        "row_oof_MdAPE",
        "row_oof_MAPE",
        "row_oof_p95_APE",
        "artist_oof_MdAPE",
        "artist_oof_MAPE",
        "artist_oof_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "bootstrap_all3_gate",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
    ]

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 보수적 계수/기준가 보정 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF24의 MAPE 개선 신호를 더 작은 cap, 보수적 strength, 위험 구간 fallback으로 안정화할 수 있는지 검증.",
            "- 현재 기준 후보: `hcoef_stable`.",
            "- 최소 비교 기준: `current_70_30`.",
            "- 선택 원칙: validation OOF/bootstrap에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 기준 fixed test: MdAPE `{baseline_test['MdAPE']:.4f}`, MAPE `{baseline_test['MAPE']:.4f}`, p95 `{baseline_test['p95_APE']:.4f}`, RMSE_log `{baseline_test['RMSE_log']:.4f}`.",
            f"- 최소 비교 기준 fixed test: MdAPE `{ref_test['MdAPE']:.4f}`, MAPE `{ref_test['MAPE']:.4f}`, p95 `{ref_test['p95_APE']:.4f}`, RMSE_log `{ref_test['RMSE_log']:.4f}`.",
            "- HCOEF25는 HCOEF24의 위험 완화 기준가를 그대로 키우지 않고, `lowrisk_only`, `no_extreme`, `conservative`, `soft` guard로 이동폭을 조정한 실험임.",
            "",
            "## 2. 후보 선택표",
            "",
            h24.md_table(selected_df[selected_cols].round(4), max_rows=35),
            "",
            "## 3. Validation OOF 상위 후보",
            "",
            "### Row OOF",
            "",
            h24.md_table(row_oof.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=20),
            "",
            "### Artist OOF",
            "",
            h24.md_table(artist_oof.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=20),
            "",
            "## 4. Fixed Test 상위 후보",
            "",
            h24.md_table(test.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=24),
            "",
            "## 5. 0604 Stress Test 상위 후보",
            "",
            h24.md_table(stress.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=20),
            "",
            "## 6. 주요 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준이며 방향성과 상대 영향 비교용.",
            "- HCOEF25의 핵심은 유사 작품 기준가가 좋은 구간에서는 작게 반영하고, 위험 구간에서는 `hcoef_stable` 쪽으로 되돌리는 것.",
            "- `hcoef25_guard_factor_*`는 기준가를 얼마나 믿을지 정하는 보수성 피처.",
            "",
            h24.md_table(coefficients.sort_values(["candidate", "standardized_coefficient"], ascending=[True, False]).round(5), max_rows=90),
            "",
            "## 7. 기준가 Coverage",
            "",
            h24.md_table(coverage.round(4), max_rows=54),
            "",
            "## 8. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=70),
            "",
            "## 9. Bootstrap 요약",
            "",
            h24.md_table(bootstrap_df.sort_values(["all3_improve_prob", "any2_improve_prob"], ascending=[False, False]).round(4), max_rows=45),
            "",
            "## 10. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/coverage_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef25_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef25_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(configs: list[CandidateConfig], coverage: pd.DataFrame) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": BASELINE,
        "reference": REFERENCE,
        "policies": list(POLICIES),
        "selection_rule": "validation/OOF/bootstrap first; fixed test and 0604 confirmation only",
        "hcoef25_design": [
            "smaller caps: 0.01, 0.015, 0.02, 0.03",
            "guarded comparable-basis gaps: lowrisk_only, no_extreme, conservative, soft",
            "low-dimensional residual Huber with risk guard features",
            "direct Huber capped candidates with small movement limits",
        ],
        "candidate_count": len(configs),
        "outputs": [
            "metrics.csv",
            "candidate_predictions.csv",
            "feature_coefficients.csv",
            "residual_analysis.csv",
            "bootstrap_or_repeated_split_summary.csv",
            "coverage_summary.csv",
            "selected_candidates.csv",
        ],
        "coverage_rows": int(len(coverage)),
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    activate_experiment_namespace()
    ensure_dirs()
    base, coverage = load_frame()
    configs = build_candidate_configs()
    metrics_df, predictions = h24.evaluate_all(base, configs)
    bootstrap_df = h24.bootstrap_summary(predictions, configs)
    selected_df = h24.selection_table(metrics_df, bootstrap_df)
    selected_names = selected_df.head(15)["candidate"].astype(str).tolist()
    validation = base[base["split"].eq("validation")].reset_index(drop=True)
    coefficients = coefficient_table(validation, configs, selected_names)
    residuals = h24.residual_analysis(predictions, selected_names)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    coverage.to_csv(EXP_DIR / "outputs" / "coverage_summary.csv", index=False)
    selected_df.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    write_config(configs, coverage)
    write_report(metrics_df, selected_df, coefficients, residuals, coverage, bootstrap_df)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
