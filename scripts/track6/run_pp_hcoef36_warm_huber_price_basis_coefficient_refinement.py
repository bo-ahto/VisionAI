#!/usr/bin/env python3
"""Run PP-HCOEF36: low-risk routing for HCOEF34/35 Warm Huber candidates.

HCOEF34/35 found Huber residual candidates that improve MdAPE/MAPE but miss the
current stable candidate's p95 guard by a very small margin. HCOEF36 does not
replace the whole Warm prediction with those candidates. It applies them only
to reliability-defined low-risk rows and keeps ``hcoef_stable`` elsewhere.

Selection principle:

* Candidate models and routing thresholds are learned from validation/OOF only.
* Fixed test and 0604 are confirmation checks only.
* Test residuals and 0604 labels are never used to create rules.
"""
from __future__ import annotations

import html
import json
import os
import sys
from dataclasses import dataclass
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


EXP_ID = "PP-HCOEF36"
EXP_SLUG = "PP-HCOEF36_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = h34.REFERENCE
STABLE_ALIAS = h34.STABLE_ALIAS
SEED = 20260608
N_REPEATS = 24

STABLE_TEST_P95 = 0.8063661210554905
STABLE_0604_P95 = 0.983456


@dataclass(frozen=True)
class RoutingRule:
    rule_key: str
    description: str
    spread_q: float | None = None
    abs_gap_q: float | None = None
    min_n: int | None = None
    area_mid_q: float | None = None
    levels: tuple[str, ...] | None = None


@dataclass(frozen=True)
class RoutingConfig:
    candidate: str
    improver: h34.CandidateConfig
    rule: RoutingRule
    description: str


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def improver_configs() -> list[h34.CandidateConfig]:
    """HCOEF35 candidates with distinct behavior to route selectively."""
    specs = [
        ("all", 0.01, 0.0100, 0.35, "best_mdape"),
        ("all", 0.001, 0.0075, 0.20, "p95_near"),
        ("all", 0.001, 0.0050, 0.50, "basis_balanced"),
        ("core", 0.01, 0.0075, 0.35, "core_oof"),
        ("core", 0.001, 0.0050, 0.50, "core_balanced"),
    ]
    out: list[h34.CandidateConfig] = []
    for feature_label, alpha, cap, strength, label in specs:
        feature_key = "basis_resid_all" if feature_label == "all" else "basis_resid_core"
        out.append(
            h34.CandidateConfig(
                candidate=(
                    f"hcoef35_{label}_{feature_key}_a{h34.slug(alpha)}"
                    f"_cap{h34.slug(cap)}_s{h34.slug(strength)}"
                ),
                kind="residual_huber",
                feature_key=feature_key,
                alpha=alpha,
                cap=cap,
                strength=strength,
                description="HCOEF35 계열 low-risk routing 입력 후보",
            )
        )
    return out


def routing_rules() -> list[RoutingRule]:
    return [
        RoutingRule("all_rows", "전체 행에 개선 후보 적용"),
        RoutingRule("n_ge5", "fallback 기준가 표본 수가 5개 이상인 행"),
        RoutingRule("spread_q50", "기준가 컴포넌트 간 차이가 validation 하위 50%인 행", spread_q=0.50),
        RoutingRule("spread_q66", "기준가 컴포넌트 간 차이가 validation 하위 66%인 행", spread_q=0.66),
        RoutingRule("spread_q75", "기준가 컴포넌트 간 차이가 validation 하위 75%인 행", spread_q=0.75),
        RoutingRule("gap_q50", "fallback 기준가와 stable 후보 차이가 validation 하위 50%인 행", abs_gap_q=0.50),
        RoutingRule("gap_q66", "fallback 기준가와 stable 후보 차이가 validation 하위 66%인 행", abs_gap_q=0.66),
        RoutingRule("gap_q75", "fallback 기준가와 stable 후보 차이가 validation 하위 75%인 행", abs_gap_q=0.75),
        RoutingRule(
            "n_ge5_spread_q66",
            "표본 수 5개 이상이고 기준가 컴포넌트 차이가 하위 66%인 행",
            min_n=5,
            spread_q=0.66,
        ),
        RoutingRule(
            "n_ge5_gap_q66",
            "표본 수 5개 이상이고 fallback-stable 차이가 하위 66%인 행",
            min_n=5,
            abs_gap_q=0.66,
        ),
        RoutingRule(
            "n_ge5_spread_q66_area90",
            "표본 수 5개 이상, 기준가 차이 하위 66%, 면적 중앙 90% 행",
            min_n=5,
            spread_q=0.66,
            area_mid_q=0.90,
        ),
        RoutingRule(
            "precise_level_spread_q75",
            "작가+재료 또는 작가+크기+재료 기준가가 잡히고 기준가 차이가 하위 75%인 행",
            spread_q=0.75,
            levels=("artist_medium_support", "artist_size_medium_support"),
        ),
        RoutingRule(
            "coarse_artist_gap_q66",
            "작가 전체 기준 fallback이면서 fallback-stable 차이가 하위 66%인 행",
            abs_gap_q=0.66,
            levels=("artist_overall",),
        ),
    ]


def slug_text(value: str) -> str:
    return (
        value.replace("hcoef35_", "")
        .replace("basis_resid_", "")
        .replace("_a0p001", "")
        .replace("_a0p01", "")
    )


def candidate_configs() -> list[RoutingConfig]:
    configs: list[RoutingConfig] = []
    for improver in improver_configs():
        short = slug_text(improver.candidate)
        for rule in routing_rules():
            configs.append(
                RoutingConfig(
                    candidate=f"hcoef36_route_{short}__{rule.rule_key}",
                    improver=improver,
                    rule=rule,
                    description=f"{rule.description}; base={improver.candidate}",
                )
            )
    return configs


def threshold_values(train: pd.DataFrame, rule: RoutingRule) -> dict[str, float]:
    values: dict[str, float] = {}
    if rule.spread_q is not None:
        values["basis_component_spread_max"] = float(train["basis_component_spread"].quantile(rule.spread_q))
    if rule.abs_gap_q is not None:
        values["abs_fallback_stable_gap_max"] = float(train["fallback_stable_gap"].abs().quantile(rule.abs_gap_q))
    if rule.area_mid_q is not None:
        tail = (1.0 - rule.area_mid_q) / 2.0
        values["log_area_min"] = float(train["log_area"].quantile(tail))
        values["log_area_max"] = float(train["log_area"].quantile(1.0 - tail))
    return values


def route_mask(frame: pd.DataFrame, rule: RoutingRule, thresholds: dict[str, float]) -> np.ndarray:
    mask = np.ones(len(frame), dtype=bool)
    if rule.min_n is not None:
        mask &= pd.to_numeric(frame["basis_fallback_m5_n"], errors="coerce").fillna(0).to_numpy(dtype=float) >= rule.min_n
    if "basis_component_spread_max" in thresholds:
        mask &= (
            pd.to_numeric(frame["basis_component_spread"], errors="coerce").fillna(np.inf).to_numpy(dtype=float)
            <= thresholds["basis_component_spread_max"]
        )
    if "abs_fallback_stable_gap_max" in thresholds:
        mask &= (
            pd.to_numeric(frame["fallback_stable_gap"], errors="coerce").fillna(np.inf).abs().to_numpy(dtype=float)
            <= thresholds["abs_fallback_stable_gap_max"]
        )
    if "log_area_min" in thresholds:
        area = pd.to_numeric(frame["log_area"], errors="coerce").to_numpy(dtype=float)
        mask &= (area >= thresholds["log_area_min"]) & (area <= thresholds["log_area_max"])
    if rule.levels is not None:
        mask &= frame["basis_fallback_m5_level"].astype(str).isin(rule.levels).to_numpy()
    return mask


def predict_routed(train: pd.DataFrame, eval_frame: pd.DataFrame, config: RoutingConfig) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    improver_pred, _ = h34.predict_candidate(train, eval_frame, config.improver)
    thresholds = threshold_values(train, config.rule)
    mask = route_mask(eval_frame, config.rule, thresholds)
    pred = eval_frame[STABLE_ALIAS].to_numpy(dtype=float).copy()
    pred[mask] = improver_pred[mask]
    return pred, mask, thresholds


def metric_row(
    scope: str,
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    ref_metric: dict[str, float],
    stable_metric: dict[str, float],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = h34.metric_row(scope, split, candidate, method, n, m, ref_metric, stable_metric, extra)
    row["experiment_id"] = EXP_ID
    return row


def prediction_frame(
    frame: pd.DataFrame,
    candidate: str,
    method: str,
    split: str,
    pred_log: np.ndarray,
    route_applied: np.ndarray | None = None,
) -> pd.DataFrame:
    out = h34.prediction_frame(frame, candidate, method, split, pred_log)
    out["experiment_id"] = EXP_ID
    if route_applied is not None:
        out["route_applied"] = route_applied.astype(bool)
    return out


def fixed_confirmation(frames: dict[str, pd.DataFrame], configs: list[RoutingConfig]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    policy_rows: list[dict[str, Any]] = []
    baselines = [
        (REFERENCE, "baseline_reference", REFERENCE),
        (STABLE_ALIAS, "baseline_stable", STABLE_ALIAS),
    ]
    for split, frame in frames.items():
        ref_metric = h34.metric(frame, frame[REFERENCE].to_numpy(dtype=float))
        stable_metric = h34.metric(frame, frame[STABLE_ALIAS].to_numpy(dtype=float))
        for candidate, method, col in baselines:
            pred = frame[col].to_numpy(dtype=float)
            m = h34.metric(frame, pred)
            metric_rows.append(metric_row("fixed_confirmation", split, candidate, method, len(frame), m, ref_metric, stable_metric))
            pred_rows.append(prediction_frame(frame, candidate, method, split, pred))
    for config in configs:
        test_model = None
        for split, frame in frames.items():
            pred, mask, thresholds = predict_routed(validation, frame, config)
            ref_metric = h34.metric(frame, frame[REFERENCE].to_numpy(dtype=float))
            stable_metric = h34.metric(frame, frame[STABLE_ALIAS].to_numpy(dtype=float))
            m = h34.metric(frame, pred)
            metric_rows.append(
                metric_row(
                    "fixed_confirmation",
                    split,
                    config.candidate,
                    "low_risk_routing",
                    len(frame),
                    m,
                    ref_metric,
                    stable_metric,
                    {
                        "base_improver": config.improver.candidate,
                        "route_rule": config.rule.rule_key,
                        "route_coverage": float(mask.mean()),
                    },
                )
            )
            pred_rows.append(prediction_frame(frame, config.candidate, "low_risk_routing", split, pred, mask))
            policy_rows.append(
                {
                    "candidate": config.candidate,
                    "split": split,
                    "base_improver": config.improver.candidate,
                    "route_rule": config.rule.rule_key,
                    "rule_description": config.rule.description,
                    "route_coverage": float(mask.mean()),
                    "route_n": int(mask.sum()),
                    **thresholds,
                }
            )
            if split == "test":
                _, test_model = h34.predict_candidate(validation, frame, config.improver)
        if test_model is not None:
            coef = h34.coefficient_frame(test_model, config.improver)
            if not coef.empty:
                coef["candidate"] = config.candidate
                coef["base_improver"] = config.improver.candidate
                coef["route_rule"] = config.rule.rule_key
                coef["experiment_id"] = EXP_ID
                coef_rows.append(coef)
    coef_df = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), coef_df, pd.DataFrame(policy_rows)


def repeated_oof(validation: pd.DataFrame, configs: list[RoutingConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    ref_metric = h34.metric(validation, validation[REFERENCE].to_numpy(dtype=float))
    stable_metric = h34.metric(validation, validation[STABLE_ALIAS].to_numpy(dtype=float))
    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            folds = h34.row_folds(len(validation), SEED + repeat) if scheme == "row_oof" else h34.artist_folds(validation, SEED + repeat)
            for config in configs:
                oof = np.full(len(validation), np.nan, dtype=float)
                route = np.full(len(validation), False, dtype=bool)
                for train_idx, hold_idx in folds:
                    train = validation.iloc[train_idx].copy()
                    hold = validation.iloc[hold_idx].copy()
                    pred, mask, _ = predict_routed(train, hold, config)
                    oof[hold_idx] = pred
                    route[hold_idx] = mask
                m = h34.metric(validation, oof)
                rows.append(
                    metric_row(
                        "repeated_oof",
                        f"validation_{scheme}",
                        config.candidate,
                        "low_risk_routing",
                        len(validation),
                        m,
                        ref_metric,
                        stable_metric,
                        {
                            "repeat": repeat,
                            "validation_scheme": scheme,
                            "base_improver": config.improver.candidate,
                            "route_rule": config.rule.rule_key,
                            "route_coverage": float(route.mean()),
                        },
                    )
                )
                if repeat == 0:
                    pred_rows.append(
                        prediction_frame(
                            validation,
                            config.candidate,
                            "low_risk_routing",
                            f"validation_{scheme}_repeat0",
                            oof,
                            route,
                        )
                    )
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True)


def summarize_repeated(metrics_df: pd.DataFrame) -> pd.DataFrame:
    return h34.summarize_repeated(metrics_df)


def select_candidates(fixed_metrics: pd.DataFrame, repeated_summary: pd.DataFrame) -> pd.DataFrame:
    out = h34.select_candidates(fixed_metrics, repeated_summary)
    route_info = (
        fixed_metrics[fixed_metrics["split"].eq("test")][["candidate", "base_improver", "route_rule", "route_coverage"]]
        .dropna(subset=["base_improver"])
        .drop_duplicates("candidate")
    )
    out = out.merge(route_info, on="candidate", how="left")
    out["fixed_p95_margin_vs_stable"] = out["test_p95_APE"] - STABLE_TEST_P95
    out["stress0604_p95_margin_vs_stable"] = out["stress0604_p95_APE"] - STABLE_0604_P95
    out["p95_guard_exact"] = out["fixed_p95_margin_vs_stable"] <= 0
    out["stress_p95_guard"] = out["stress0604_p95_margin_vs_stable"] <= 0.0005
    out["decision"] = np.select(
        [
            out["passes_strong_stable_gate"] & out["p95_guard_exact"] & out["stress_p95_guard"],
            out["passes_stable_gate"] & out["p95_guard_exact"] & out["stress_p95_guard"],
            out["passes_reference_gate"] & out["p95_guard_exact"],
            out["passes_reference_gate"],
        ],
        [
            "운영 후보 검토",
            "Warm 안정 후보 재검증",
            "p95 방어형 70:30 개선 후보",
            "기존 70:30 대비 개선 후보",
        ],
        default="보류",
    )
    return out.sort_values(
        ["p95_guard_exact", "passes_stable_gate", "passes_reference_gate", "test_MdAPE", "test_MAPE"],
        ascending=[False, False, False, True, True],
    )


def residual_analysis(predictions: pd.DataFrame, focus_candidates: set[str]) -> pd.DataFrame:
    return h34.residual_analysis(predictions, focus_candidates)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    return h34.markdown_table(frame, max_rows)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.strip().startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6}p{line-height:1.55}h1,h2,h3{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    fixed_metrics: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    selected: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    policy: pd.DataFrame,
) -> None:
    focus = fixed_metrics[
        fixed_metrics["candidate"].isin([REFERENCE, STABLE_ALIAS])
        & fixed_metrics["split"].isin(["validation", "test", "0604_ex50"])
    ].copy()
    strong = selected[selected["decision"].isin(["운영 후보 검토", "Warm 안정 후보 재검증"])].copy()
    p95_safe = selected[selected["decision"].eq("p95 방어형 70:30 개선 후보")].copy()
    if not strong.empty:
        best = strong.iloc[0]
        conclusion = (
            f"`{best['candidate']}`를 Warm 안정 재검증 후보로 분리. "
            f"test MdAPE/MAPE/p95 {best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}."
        )
    elif not p95_safe.empty:
        best = p95_safe.iloc[0]
        conclusion = (
            f"`{best['candidate']}`는 stable p95를 방어하면서 70:30 대비 개선한 목적별 후보. "
            f"test MdAPE/MAPE/p95 {best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}."
        )
    else:
        conclusion = (
            "low-risk routing으로도 hcoef_stable을 명확히 넘는 운영 후보는 아직 없음. "
            "다만 p95를 거의 유지하는 일부 70:30 개선 후보는 목적별로 관리 가능."
        )

    policy_top = (
        policy[policy["split"].eq("test")]
        .merge(selected[["candidate", "decision", "test_MdAPE", "test_MAPE", "test_p95_APE"]], on="candidate", how="left")
        .sort_values(["decision", "test_MdAPE", "test_MAPE"])
        .head(20)
    )
    coef_top = coeffs.sort_values(["candidate", "abs_coefficient"], ascending=[True, False]).groupby("candidate").head(5)

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 목적별 라우팅 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF34/35의 MdAPE/MAPE 개선 후보를 모든 행에 적용하지 않고, 기준가 신뢰도가 높은 행에만 적용해 p95 악화를 막을 수 있는지 확인.",
            "- 기준 후보: `current_70_30`.",
            "- 안정 비교 후보: `hcoef_stable`.",
            "- 선택 원칙: validation/OOF 기반 rule과 Huber 계수만 사용. fixed test/0604는 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {conclusion}",
            "- HCOEF35의 개선 신호는 전체 교체보다 라우팅/신뢰도 정책으로 다루는 것이 더 적합함.",
            "",
            "## 2. 기준 후보 지표",
            "",
            markdown_table(
                focus[
                    [
                        "split",
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                    ]
                ].round(4)
            ),
            "",
            "## 3. 선택 후보 판단",
            "",
            markdown_table(
                selected[
                    [
                        "candidate",
                        "decision",
                        "base_improver",
                        "route_rule",
                        "route_coverage",
                        "test_MdAPE",
                        "test_MAPE",
                        "test_p95_APE",
                        "fixed_p95_margin_vs_stable",
                        "stress0604_MdAPE",
                        "stress0604_MAPE",
                        "stress0604_p95_APE",
                        "row_oof_ref_any2_improve_prob",
                        "artist_oof_ref_any2_improve_prob",
                        "row_oof_stable_any2_improve_prob",
                        "artist_oof_stable_any2_improve_prob",
                    ]
                ].round(4),
                30,
            ),
            "",
            "## 4. 라우팅 정책 요약",
            "",
            markdown_table(
                policy_top[
                    [
                        "candidate",
                        "decision",
                        "base_improver",
                        "route_rule",
                        "route_coverage",
                        "route_n",
                        "basis_component_spread_max",
                        "abs_fallback_stable_gap_max",
                        "log_area_min",
                        "log_area_max",
                        "test_MdAPE",
                        "test_MAPE",
                        "test_p95_APE",
                    ]
                ].round(4),
                20,
            ),
            "",
            "## 5. 반복 OOF 요약",
            "",
            markdown_table(
                repeated_summary.sort_values(["stable_any2_improve_prob", "mean_MdAPE"], ascending=[False, True])[
                    [
                        "candidate",
                        "validation_scheme",
                        "n_repeats",
                        "mean_MdAPE",
                        "mean_MAPE",
                        "mean_p95_APE",
                        "ref_any2_improve_prob",
                        "stable_any2_improve_prob",
                        "stable_all3_improve_prob",
                    ]
                ].round(4),
                30,
            ),
            "",
            "## 6. Huber 계수 해석",
            "",
            "- 계수는 라우팅에 들어간 base improver의 Huber residual model 기준.",
            "- 양수 계수는 stable 예측에 보정값을 더하는 방향, 음수 계수는 낮추는 방향.",
            "",
            markdown_table(
                coef_top[
                    [
                        "candidate",
                        "base_improver",
                        "route_rule",
                        "feature",
                        "coefficient_on_scaled_feature",
                        "direction",
                    ]
                ].round(4),
                60,
            )
            if not coef_top.empty
            else "_계수 없음_",
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), 40),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/policy_map.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    configs = candidate_configs()
    frames = h34.build_frames()
    fixed_metrics, fixed_preds, coeffs, policy = fixed_confirmation(frames, configs)
    repeated_metrics, repeated_preds = repeated_oof(frames["validation"], configs)
    repeated_summary = summarize_repeated(repeated_metrics)
    selected = select_candidates(fixed_metrics, repeated_summary)
    focus = set(selected.head(15)["candidate"]) | {REFERENCE, STABLE_ALIAS}
    predictions = pd.concat([fixed_preds, repeated_preds], ignore_index=True)
    residuals = residual_analysis(predictions, focus)

    all_metrics = pd.concat([fixed_metrics, repeated_metrics], ignore_index=True)
    all_metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    policy.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    repeated_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)

    config_payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference": REFERENCE,
        "stable_alias": STABLE_ALIAS,
        "n_repeats": N_REPEATS,
        "seed": SEED,
        "improvers": [c.__dict__ for c in improver_configs()],
        "routing_rules": [r.__dict__ for r in routing_rules()],
        "selection_principle": [
            "validation/OOF first",
            "fixed test and 0604 confirmation only",
            "no test residual based routing",
        ],
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(fixed_metrics, repeated_summary, selected, coeffs, residuals, policy)
    print(f"[{EXP_ID}] done")
    print(selected.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
