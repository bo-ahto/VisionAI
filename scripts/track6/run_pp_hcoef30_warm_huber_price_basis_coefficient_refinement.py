#!/usr/bin/env python3
"""Run PP-HCOEF30: validation-consensus gated Huber meta residual policies.

HCOEF29 showed a clear pattern: OOF Huber meta residual candidates can improve
validation OOF and repeated subsamples, but the same movement may worsen fixed
test MdAPE/p95. HCOEF30 does not tune on fixed test. It audits HCOEF29 source
candidates on validation row OOF and validation artist OOF segments, then only
allows a source candidate to move away from ``hcoef_stable`` when both
validation views agree that the segment improved.

Formula:

    if row matches selected validation-consensus rule:
        corrected_log = hcoef_stable + weight * (source_candidate - hcoef_stable)
    else:
        corrected_log = hcoef_stable

The selected rules are derived from validation row/artist OOF only. Fixed test
and 0604 are confirmation/stress checks.
"""
from __future__ import annotations

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

from scripts.track6 import run_pp_hcoef24_warm_huber_price_basis_coefficient_refinement as h24
from scripts.track6 import run_pp_hcoef28_warm_huber_price_basis_coefficient_refinement as h28


EXP_ID = "PP-HCOEF30"
EXP_SLUG = "PP-HCOEF30_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
H29_DIR = REPO / "experiments" / "track6" / "PP-HCOEF29_warm_huber_price_basis_coefficient_refinement"
H29_PREDICTIONS = H29_DIR / "outputs" / "candidate_predictions.csv"
H29_SELECTED = H29_DIR / "outputs" / "selected_candidates.csv"

BASELINE = h28.BASELINE
REFERENCE = h28.REFERENCE
PPV8 = h28.PPV8
SVC = h28.SVC
L10_CANDIDATE = h28.L10_CANDIDATE
BASE_COMPONENTS = [BASELINE, REFERENCE, PPV8, SVC, L10_CANDIDATE]
KEY_COLS = ["scope", "split", "_track6_row_id"]

SOURCE_LIMIT = 10
MIN_SEGMENT_N = 25
SELECTION_SCOPES = ["validation_oof_row", "validation_oof_artist"]
SEGMENT_GROUPS = [
    ("qwidth", ("qwidth_band",)),
    ("n", ("svc_group_n_band",)),
    ("gap", ("gap_band",)),
    ("spread", ("pred_spread_band",)),
    ("confidence", ("service_confidence_tier",)),
    ("level", ("svc_group_level",)),
    ("qwidth_gap", ("qwidth_band", "gap_band")),
    ("qwidth_n", ("qwidth_band", "svc_group_n_band")),
    ("level_qwidth", ("svc_group_level", "qwidth_band")),
    ("level_gap", ("svc_group_level", "gap_band")),
    ("spread_gap", ("pred_spread_band", "gap_band")),
]


@dataclass(frozen=True)
class Policy:
    source_candidate: str
    source_tag: str
    objective: str
    top_n: int
    weight: float

    @property
    def candidate(self) -> str:
        return (
            f"hcoef30_{self.source_tag}_{self.objective}"
            f"_top{self.top_n}_w{slug_float(self.weight)}"
        )


def slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric(frame: pd.DataFrame, pred_col: str | np.ndarray) -> dict[str, float]:
    pred = frame[pred_col].to_numpy(dtype=float) if isinstance(pred_col, str) else np.asarray(pred_col, dtype=float)
    return h28.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        pred,
    )


def choose_sources() -> pd.DataFrame:
    selected = pd.read_csv(H29_SELECTED)
    blocked = set(BASE_COMPONENTS)
    candidates = selected[
        ~selected["candidate"].isin(blocked)
        & selected["candidate"].astype(str).str.startswith("hcoef29_")
    ].copy()
    candidates = candidates.sort_values(
        ["repeated_min_any2_improve_prob", "repeated_min_all3_improve_prob", "row_oof_p95_APE"],
        ascending=[False, False, True],
    ).head(SOURCE_LIMIT)
    rows = []
    for idx, row in candidates.reset_index(drop=True).iterrows():
        rows.append(
            {
                "source_candidate": row["candidate"],
                "source_tag": f"s{idx + 1:02d}",
                "source_reason": (
                    f"HCOEF29 repeated any2 {row['repeated_min_any2_improve_prob']:.3f}, "
                    f"all3 {row['repeated_min_all3_improve_prob']:.3f}; "
                    f"fixed {row['test_MdAPE']:.4f}/{row['test_MAPE']:.4f}/{row['test_p95_APE']:.4f}"
                ),
            }
        )
    return pd.DataFrame(rows)


def load_frames(sources: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(H29_PREDICTIONS, low_memory=False)
    keep_candidates = list(dict.fromkeys([*BASE_COMPONENTS, *sources["source_candidate"].tolist()]))
    existing = raw[raw["candidate"].isin(keep_candidates)].copy()
    seed = raw[raw["candidate"].eq(BASELINE)].drop_duplicates(KEY_COLS).copy()
    for source in sources["source_candidate"]:
        part = raw[raw["candidate"].eq(source)][[*KEY_COLS, "pred_log"]].rename(columns={"pred_log": f"{source}__pred_log"})
        seed = seed.merge(part, on=KEY_COLS, how="left", validate="one_to_one")
    return seed, existing


def rule_key(cols: tuple[str, ...], values: tuple[Any, ...]) -> str:
    return " & ".join(f"{col}={value}" for col, value in zip(cols, values))


def rule_mask(frame: pd.DataFrame, cols: tuple[str, ...], values: tuple[Any, ...]) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for col, value in zip(cols, values):
        mask &= frame[col].astype(str).eq(str(value))
    return mask


def segment_metric_rows(seed: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for source in sources["source_candidate"]:
        source_col = f"{source}__pred_log"
        for scope in SELECTION_SCOPES:
            scoped = seed[seed["scope"].eq(scope)].copy()
            for group_name, cols in SEGMENT_GROUPS:
                grouped = scoped.groupby(list(cols), dropna=False)
                for values, group in grouped:
                    values_tuple = values if isinstance(values, tuple) else (values,)
                    if len(group) < MIN_SEGMENT_N:
                        continue
                    base_m = metric(group, BASELINE)
                    src_m = metric(group, source_col)
                    improve_count = int(src_m["MdAPE"] < base_m["MdAPE"]) + int(src_m["MAPE"] < base_m["MAPE"]) + int(src_m["p95_APE"] <= base_m["p95_APE"])
                    rows.append(
                        {
                            "source_candidate": source,
                            "scope": scope,
                            "group_name": group_name,
                            "cols": "|".join(cols),
                            "values": "|".join(str(v) for v in values_tuple),
                            "rule_key": rule_key(cols, values_tuple),
                            "n": len(group),
                            "base_MdAPE": base_m["MdAPE"],
                            "base_MAPE": base_m["MAPE"],
                            "base_p95_APE": base_m["p95_APE"],
                            "source_MdAPE": src_m["MdAPE"],
                            "source_MAPE": src_m["MAPE"],
                            "source_p95_APE": src_m["p95_APE"],
                            "delta_MdAPE": src_m["MdAPE"] - base_m["MdAPE"],
                            "delta_MAPE": src_m["MAPE"] - base_m["MAPE"],
                            "delta_p95_APE": src_m["p95_APE"] - base_m["p95_APE"],
                            "improve_count": improve_count,
                            "p95_guard": src_m["p95_APE"] <= base_m["p95_APE"],
                            "mape_guard": src_m["MAPE"] <= base_m["MAPE"],
                            "mdape_guard": src_m["MdAPE"] <= base_m["MdAPE"],
                        }
                    )
    return pd.DataFrame(rows)


def consensus_rules(segment_metrics: pd.DataFrame) -> pd.DataFrame:
    row = segment_metrics[segment_metrics["scope"].eq("validation_oof_row")].copy()
    artist = segment_metrics[segment_metrics["scope"].eq("validation_oof_artist")].copy()
    keys = ["source_candidate", "group_name", "cols", "values", "rule_key"]
    merged = row.merge(
        artist,
        on=keys,
        suffixes=("_row", "_artist"),
        how="inner",
    )
    if merged.empty:
        return merged
    merged["all3_safe"] = (
        (merged["improve_count_row"] >= 3)
        & (merged["improve_count_artist"] >= 3)
        & merged["p95_guard_row"]
        & merged["p95_guard_artist"]
    )
    merged["any2_safe"] = (
        (merged["improve_count_row"] >= 2)
        & (merged["improve_count_artist"] >= 2)
        & merged["p95_guard_row"]
        & merged["p95_guard_artist"]
    )
    merged["mape_guarded"] = (
        merged["mape_guard_row"]
        & merged["mape_guard_artist"]
        & merged["p95_guard_row"]
        & merged["p95_guard_artist"]
    )
    merged["mdape_guarded"] = (
        merged["mdape_guard_row"]
        & merged["mdape_guard_artist"]
        & merged["p95_guard_row"]
        & merged["p95_guard_artist"]
    )
    merged["score"] = (
        merged["delta_MdAPE_row"]
        + merged["delta_MAPE_row"]
        + merged["delta_p95_APE_row"]
        + merged["delta_MdAPE_artist"]
        + merged["delta_MAPE_artist"]
        + merged["delta_p95_APE_artist"]
    )
    merged["min_n"] = merged[["n_row", "n_artist"]].min(axis=1)
    return merged.sort_values(["source_candidate", "score", "min_n"], ascending=[True, True, False])


def parse_rule(row: pd.Series) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return tuple(str(row["cols"]).split("|")), tuple(str(row["values"]).split("|"))


def build_policies(rules: pd.DataFrame, sources: pd.DataFrame) -> tuple[list[Policy], pd.DataFrame]:
    policies: list[Policy] = []
    policy_rows: list[dict[str, Any]] = []
    tag_map = dict(zip(sources["source_candidate"], sources["source_tag"]))
    objective_map = {
        "all3_safe": "all3",
        "any2_safe": "any2",
        "mape_guarded": "mape",
        "mdape_guarded": "mdape",
    }
    for source, source_rules in rules.groupby("source_candidate", sort=False):
        for objective_col, objective_name in objective_map.items():
            obj_rules = source_rules[source_rules[objective_col]].sort_values(["score", "min_n"], ascending=[True, False])
            if obj_rules.empty:
                continue
            for top_n in [1, 3, 5, 10]:
                if len(obj_rules) < top_n:
                    continue
                for weight in [0.50, 1.00]:
                    policy = Policy(source, tag_map[source], objective_name, top_n, weight)
                    policies.append(policy)
                    selected = obj_rules.head(top_n)
                    policy_rows.append(
                        {
                            "candidate": policy.candidate,
                            "source_candidate": source,
                            "source_tag": policy.source_tag,
                            "objective": objective_name,
                            "top_n": top_n,
                            "weight": weight,
                            "rule_count": len(selected),
                            "rules": " || ".join(selected["rule_key"].tolist()),
                            "mean_score": float(selected["score"].mean()),
                            "min_n": int(selected["min_n"].min()),
                            "formula": "stable + weight * (source - stable) inside selected validation-consensus segments",
                        }
                    )
    return policies, pd.DataFrame(policy_rows)


def generate_predictions(seed: pd.DataFrame, existing: pd.DataFrame, policies: list[Policy], policy_rows: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    records: list[pd.DataFrame] = [existing.copy()]
    policy_lookup = {row["candidate"]: row for _, row in policy_rows.iterrows()}
    for policy in policies:
        source_col = f"{policy.source_candidate}__pred_log"
        selected_rules = rules[
            rules["source_candidate"].eq(policy.source_candidate)
            & rules[{"all3": "all3_safe", "any2": "any2_safe", "mape": "mape_guarded", "mdape": "mdape_guarded"}[policy.objective]]
        ].sort_values(["score", "min_n"], ascending=[True, False]).head(policy.top_n)
        mask = pd.Series(False, index=seed.index)
        for _, rule in selected_rules.iterrows():
            cols, values = parse_rule(rule)
            mask |= rule_mask(seed, cols, values)
        out = seed.copy()
        source_pred = pd.to_numeric(out[source_col], errors="coerce").fillna(out[BASELINE]).to_numpy(dtype=float)
        stable = pd.to_numeric(out[BASELINE], errors="coerce").to_numpy(dtype=float)
        move = (source_pred - stable) * policy.weight
        pred_log = np.where(mask.to_numpy(), stable + move, stable)
        out["candidate"] = policy.candidate
        out["method"] = "validation_consensus_segment_gate"
        out["source_candidate"] = policy.source_candidate
        out["mask_name"] = policy.objective
        out["mask_applied"] = mask.astype(float)
        out["strength"] = policy.weight
        out["cap"] = np.nan
        out["move_weight"] = np.where(mask.to_numpy(), policy.weight, 0.0)
        out["pred_log"] = pred_log
        out["pred_price"] = np.exp(np.clip(pred_log, 0, 30))
        out["policy_move_log"] = pred_log - stable
        out["residual_log"] = out["actual_log"] - out["pred_log"]
        out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"]
        if policy.candidate in policy_lookup:
            out["policy_rules"] = policy_lookup[policy.candidate]["rules"]
        records.append(out)
    predictions = pd.concat(records, ignore_index=True, sort=False)
    predictions["experiment_id"] = EXP_ID
    return predictions


def feature_coefficients(rules: pd.DataFrame, policy_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    candidate_to_rules = {
        row["candidate"]: set(str(row["rules"]).split(" || "))
        for _, row in policy_rows.iterrows()
    }
    for candidate, rule_set in candidate_to_rules.items():
        subset = rules[rules["rule_key"].isin(rule_set)].copy()
        for _, rule in subset.iterrows():
            rows.append(
                {
                    "candidate": candidate,
                    "source_candidate": rule["source_candidate"],
                    "feature": rule["rule_key"],
                    "coefficient": float(-rule["score"]),
                    "direction": "적용 허용 구간",
                    "interpretation": (
                        "validation row/artist OOF 양쪽에서 source 후보가 hcoef_stable보다 "
                        f"안정적이었던 segment. row delta "
                        f"{rule['delta_MdAPE_row']:.4f}/{rule['delta_MAPE_row']:.4f}/{rule['delta_p95_APE_row']:.4f}, "
                        f"artist delta {rule['delta_MdAPE_artist']:.4f}/{rule['delta_MAPE_artist']:.4f}/{rule['delta_p95_APE_artist']:.4f}"
                    ),
                }
            )
    return pd.DataFrame(rows)


def write_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    repeated: pd.DataFrame,
    residuals: pd.DataFrame,
    rules: pd.DataFrame,
    policies: pd.DataFrame,
    coeffs: pd.DataFrame,
    sources: pd.DataFrame,
) -> None:
    base = selected[selected["candidate"].eq(BASELINE)].iloc[0]
    accepted = selected[selected["decision"].isin(["반복 검증 통과 후보", "반복 any2 검증 후보", "fixed 확인 후보"])].copy()
    if accepted.empty:
        best_line = "새 운영 후보 채택 없음."
    else:
        best = accepted.iloc[0]
        best_line = (
            f"상위 확인 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed `{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`, "
            f"repeated min any2 `{best.get('repeated_min_any2_improve_prob', np.nan):.4f}`, "
            f"min all3 `{best.get('repeated_min_all3_improve_prob', np.nan):.4f}`)."
        )

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
        "repeated_min_any2_improve_prob",
        "repeated_min_all3_improve_prob",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
        "test_mean_move_weight",
    ]
    metric_cols = ["scope", "candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "mean_move_weight"]
    repeat_cols = [
        "source_scope",
        "validation_scheme",
        "candidate",
        "mean_delta_MdAPE_vs_stable",
        "mean_delta_MAPE_vs_stable",
        "mean_delta_p95_APE_vs_stable",
        "MdAPE_improve_prob",
        "MAPE_improve_prob",
        "p95_improve_prob",
        "any2_improve_prob",
        "all3_improve_prob",
    ]
    top_repeat = repeated[repeat_cols].sort_values(["any2_improve_prob", "all3_improve_prob"], ascending=False).head(80) if not repeated.empty else repeated
    top_rules = rules.sort_values(["score", "min_n"], ascending=[True, False]).head(80)

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber validation-consensus segment gate 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF29의 OOF Huber meta residual 후보를 전체에 적용하지 않고, validation row/artist OOF가 동시에 동의한 segment에만 제한 적용.",
            "- 후보 선택: validation row/artist OOF segment consensus만 사용.",
            "- fixed test와 0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 안정 기준 `hcoef_stable` fixed test: `{base['test_MdAPE']:.4f}/{base['test_MAPE']:.4f}/{base['test_p95_APE']:.4f}`.",
            "- fixed test에서만 좋아진 후보는 운영 후보가 아니라 추가 재검증 후보로 분리.",
            "",
            "## 2. 보정 공식",
            "",
            "- 조건 생성: validation row OOF와 validation artist OOF에서 source 후보가 같은 segment에서 기준 후보보다 개선되는지 확인.",
            "- 적용식: `corrected_log = hcoef_stable + weight * (source_candidate - hcoef_stable)`.",
            "- segment 조건을 만족하지 않으면 `hcoef_stable`을 그대로 유지.",
            "",
            "## 3. 사용한 source 후보",
            "",
            h24.md_table(sources, max_rows=20),
            "",
            "## 4. 선택된 segment rule",
            "",
            h24.md_table(top_rules[["source_candidate", "group_name", "rule_key", "min_n", "score", "delta_MdAPE_row", "delta_MAPE_row", "delta_p95_APE_row", "delta_MdAPE_artist", "delta_MAPE_artist", "delta_p95_APE_artist", "all3_safe", "any2_safe", "mape_guarded", "mdape_guarded"]].round(4), max_rows=80),
            "",
            "## 5. 정책 후보 설정",
            "",
            h24.md_table(policies.head(80), max_rows=80),
            "",
            "## 6. 선택 후보 요약",
            "",
            h24.md_table(selected[selected_cols].round(4), max_rows=80),
            "",
            "## 7. Scope별 metrics",
            "",
            h24.md_table(metrics[metric_cols].round(4), max_rows=140),
            "",
            "## 8. 반복 split/artist holdout 요약",
            "",
            h24.md_table(top_repeat.round(4), max_rows=80),
            "",
            "## 9. Rule 해석",
            "",
            h24.md_table(coeffs.round(6), max_rows=120),
            "",
            "## 10. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=100),
            "",
            "## 11. 다음 방향",
            "",
            "- segment gate가 fixed p95를 방어하면서 repeated gate를 통과하면 후보를 축소해 HCOEF31에서 재검증.",
            "- gate를 걸어도 fixed/generalization이 개선되지 않으면 HCOEF29 계수 기반 점 보정은 중단하고, 위험도 피처를 신뢰도/범위 정책으로 분리.",
            "",
            "## 12. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/segment_rule_metrics.csv`",
            "- `outputs/consensus_rules.csv`",
            "- `outputs/repeated_iteration_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/policy_configurations.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef30_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef30_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(sources: pd.DataFrame, policies: pd.DataFrame) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-HCOEF29",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "source_count": int(len(sources)),
        "policy_count": int(len(policies)),
        "min_segment_n": MIN_SEGMENT_N,
        "segment_groups": [{"name": name, "cols": cols} for name, cols in SEGMENT_GROUPS],
        "selection_rule": "validation row/artist OOF segment consensus only; fixed test and 0604 confirmation only",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    sources = choose_sources()
    seed, existing = load_frames(sources)
    segment_metrics = segment_metric_rows(seed, sources)
    rules = consensus_rules(segment_metrics)
    policies, policy_rows = build_policies(rules, sources)
    if not policies:
        raise RuntimeError("No validation-consensus policies were generated.")
    predictions = generate_predictions(seed, existing, policies, policy_rows, rules)
    metrics = h28.point_metrics(predictions)
    detail, repeated = h28.repeated_validation(predictions)
    source_basis = policy_rows[["candidate", "formula"]].rename(columns={"candidate": "source_candidate", "formula": "source_reason"})
    selected = h28.selected_table(metrics, repeated, source_basis)
    residuals = h28.residual_analysis(predictions, selected)
    coeffs = feature_coefficients(rules, policy_rows)

    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    segment_metrics.to_csv(EXP_DIR / "outputs" / "segment_rule_metrics.csv", index=False)
    rules.to_csv(EXP_DIR / "outputs" / "consensus_rules.csv", index=False)
    detail.to_csv(EXP_DIR / "outputs" / "repeated_iteration_metrics.csv", index=False)
    repeated.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    policy_rows.to_csv(EXP_DIR / "outputs" / "policy_configurations.csv", index=False)
    sources.to_csv(EXP_DIR / "outputs" / "source_candidate_basis.csv", index=False)
    write_config(sources, policy_rows)
    write_report(metrics, selected, repeated, residuals, rules, policy_rows, coeffs, sources)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
