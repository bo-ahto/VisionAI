#!/usr/bin/env python3
"""Run PP-HCOEF32: ultra-micro p95-first directional correction.

HCOEF31 reduced HCOEF30's movement with direction checks and small caps, but
the fixed p95 guard was still missed by a very small margin. HCOEF32 keeps the
same validation-only selection principle and tests an even smaller coefficient
grid with a p95-first objective:

1. Direction check:
   A source candidate is allowed only when the segment's stable residual
   direction and the source movement direction agree in both row OOF and artist
   OOF.

2. Ultra-micro correction:
   Even when a segment is allowed, the movement is clipped to a tiny cap.

3. p95-first policy:
   Separate policy candidates are built only from validation row/artist segments
   where p95 is not worse than the stable baseline.

Formula:

    if validation row/artist segment is safe and direction-consistent:
        corrected_log = hcoef_stable + clip(weight * (source - hcoef_stable), -cap, cap)
    else:
        corrected_log = hcoef_stable

Fixed test and 0604 are confirmation checks only.
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
from scripts.track6 import run_pp_hcoef30_warm_huber_price_basis_coefficient_refinement as h30


EXP_ID = "PP-HCOEF32"
EXP_SLUG = "PP-HCOEF32_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

BASELINE = h28.BASELINE
REFERENCE = h28.REFERENCE
PPV8 = h28.PPV8
SVC = h28.SVC
L10_CANDIDATE = h28.L10_CANDIDATE
BASE_COMPONENTS = [BASELINE, REFERENCE, PPV8, SVC, L10_CANDIDATE]

SOURCE_LIMIT = 3
WEIGHTS = [0.025, 0.050]
CAPS = [0.0010, 0.0025, 0.0050]
TOP_NS = [1, 2]


@dataclass(frozen=True)
class Policy:
    source_candidate: str
    source_tag: str
    objective: str
    top_n: int
    weight: float
    cap: float

    @property
    def candidate(self) -> str:
        return (
            f"hcoef32_{self.source_tag}_{self.objective}"
            f"_top{self.top_n}_w{slug_float(self.weight)}"
            f"_cap{slug_float(self.cap)}"
        )


def slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def choose_sources() -> pd.DataFrame:
    return h30.choose_sources().head(SOURCE_LIMIT).copy()


def add_direction_stats(seed: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, rule in rules.iterrows():
        cols, values = h30.parse_rule(rule)
        source = str(rule["source_candidate"])
        source_col = f"{source}__pred_log"
        out = rule.to_dict()
        for suffix, scope in [("row", "validation_oof_row"), ("artist", "validation_oof_artist")]:
            scoped = seed[seed["scope"].eq(scope)].copy()
            mask = h30.rule_mask(scoped, cols, values)
            group = scoped[mask].copy()
            if group.empty:
                stable_resid = np.nan
                source_move = np.nan
                directional = False
                abs_improve = np.nan
            else:
                stable = pd.to_numeric(group[BASELINE], errors="coerce")
                source_pred = pd.to_numeric(group[source_col], errors="coerce").fillna(stable)
                actual = pd.to_numeric(group["actual_log"], errors="coerce")
                stable_resid_arr = actual - stable
                source_resid_arr = actual - source_pred
                move_arr = source_pred - stable
                stable_resid = float(np.nanmedian(stable_resid_arr))
                source_move = float(np.nanmedian(move_arr))
                directional = bool(stable_resid * source_move > 0)
                abs_improve = float(np.nanmedian(np.abs(source_resid_arr)) - np.nanmedian(np.abs(stable_resid_arr)))
            out[f"stable_residual_median_{suffix}"] = stable_resid
            out[f"source_move_median_{suffix}"] = source_move
            out[f"directional_{suffix}"] = directional
            out[f"median_abs_residual_delta_{suffix}"] = abs_improve
        out["directional_consensus"] = bool(out["directional_row"] and out["directional_artist"])
        out["median_abs_guard"] = bool(
            (out["median_abs_residual_delta_row"] <= 0)
            and (out["median_abs_residual_delta_artist"] <= 0)
        )
        out["p95_guarded"] = bool(out["p95_guard_row"] and out["p95_guard_artist"])
        out["directional_score"] = (
            out["score"]
            + out["median_abs_residual_delta_row"]
            + out["median_abs_residual_delta_artist"]
        )
        rows.append(out)
    return pd.DataFrame(rows).sort_values(
        ["source_candidate", "directional_score", "min_n"],
        ascending=[True, True, False],
    )


def build_policies(rules: pd.DataFrame, sources: pd.DataFrame) -> tuple[list[Policy], pd.DataFrame]:
    policies: list[Policy] = []
    rows: list[dict[str, Any]] = []
    tag_map = dict(zip(sources["source_candidate"], sources["source_tag"]))
    objective_map = {
        "p95_guarded": "p95_dir",
        "all3_safe": "all3_dir",
        "any2_safe": "any2_dir",
        "mape_guarded": "mape_dir",
    }
    eligible = rules[rules["directional_consensus"] & rules["median_abs_guard"]].copy()
    for source, source_rules in eligible.groupby("source_candidate", sort=False):
        for objective_col, objective_name in objective_map.items():
            obj_rules = source_rules[source_rules[objective_col]].sort_values(
                ["directional_score", "min_n"],
                ascending=[True, False],
            )
            if obj_rules.empty:
                continue
            for top_n in TOP_NS:
                if len(obj_rules) < top_n:
                    continue
                selected = obj_rules.head(top_n)
                for weight in WEIGHTS:
                    for cap in CAPS:
                        policy = Policy(source, tag_map[source], objective_name, top_n, weight, cap)
                        policies.append(policy)
                        rows.append(
                            {
                                "candidate": policy.candidate,
                                "source_candidate": source,
                                "source_tag": policy.source_tag,
                                "objective": objective_name,
                                "top_n": top_n,
                                "weight": weight,
                                "cap": cap,
                                "rule_count": len(selected),
                                "rules": " || ".join(selected["rule_key"].tolist()),
                                "mean_directional_score": float(selected["directional_score"].mean()),
                                "min_n": int(selected["min_n"].min()),
                                "formula": "stable + clipped directional micro move inside validation-consensus segments",
                            }
                        )
    return policies, pd.DataFrame(rows)


def generate_predictions(seed: pd.DataFrame, existing: pd.DataFrame, policies: list[Policy], policy_rows: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    records: list[pd.DataFrame] = [existing.copy()]
    policy_lookup = {row["candidate"]: row for _, row in policy_rows.iterrows()}
    objective_col = {
        "all3_dir": "all3_safe",
        "any2_dir": "any2_safe",
        "mape_dir": "mape_guarded",
        "p95_dir": "p95_guarded",
    }
    eligible = rules[rules["directional_consensus"] & rules["median_abs_guard"]].copy()
    for policy in policies:
        source_col = f"{policy.source_candidate}__pred_log"
        selected_rules = eligible[
            eligible["source_candidate"].eq(policy.source_candidate)
            & eligible[objective_col[policy.objective]]
        ].sort_values(["directional_score", "min_n"], ascending=[True, False]).head(policy.top_n)
        mask = pd.Series(False, index=seed.index)
        for _, rule in selected_rules.iterrows():
            cols, values = h30.parse_rule(rule)
            mask |= h30.rule_mask(seed, cols, values)
        out = seed.copy()
        stable = pd.to_numeric(out[BASELINE], errors="coerce").to_numpy(dtype=float)
        source_pred = pd.to_numeric(out[source_col], errors="coerce").fillna(pd.Series(stable, index=out.index)).to_numpy(dtype=float)
        raw_move = (source_pred - stable) * policy.weight
        clipped_move = np.clip(raw_move, -policy.cap, policy.cap)
        pred_log = np.where(mask.to_numpy(), stable + clipped_move, stable)
        out["candidate"] = policy.candidate
        out["method"] = "directional_ultra_micro_p95_first_gate"
        out["source_candidate"] = policy.source_candidate
        out["mask_name"] = policy.objective
        out["mask_applied"] = mask.astype(float)
        out["strength"] = policy.weight
        out["cap"] = policy.cap
        out["move_weight"] = np.where(mask.to_numpy(), policy.weight, 0.0)
        out["pred_log"] = pred_log
        out["pred_price"] = np.exp(np.clip(pred_log, 0, 30))
        out["policy_move_log"] = pred_log - stable
        out["residual_log"] = out["actual_log"] - out["pred_log"]
        out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"]
        out["policy_rules"] = policy_lookup[policy.candidate]["rules"]
        records.append(out)
    predictions = pd.concat(records, ignore_index=True, sort=False)
    predictions["experiment_id"] = EXP_ID
    return predictions


def feature_coefficients(rules: pd.DataFrame, policy_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, policy in policy_rows.iterrows():
        rule_set = set(str(policy["rules"]).split(" || "))
        subset = rules[rules["rule_key"].isin(rule_set)].copy()
        for _, rule in subset.iterrows():
            rows.append(
                {
                    "candidate": policy["candidate"],
                    "source_candidate": rule["source_candidate"],
                    "feature": rule["rule_key"],
                    "coefficient": float(-rule["directional_score"]),
                    "direction": "방향 일치 적용 구간",
                    "interpretation": (
                        "stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 "
                        "중앙 절대 잔차가 줄어든 segment. "
                        f"row residual/move {rule['stable_residual_median_row']:.4f}/{rule['source_move_median_row']:.4f}, "
                        f"artist residual/move {rule['stable_residual_median_artist']:.4f}/{rule['source_move_median_artist']:.4f}"
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
    best_line = "새 운영 후보 채택 없음."
    if not accepted.empty:
        best = accepted.iloc[0]
        best_line = (
            f"상위 확인 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed `{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`, "
            f"repeated min any2/all3 `{best['repeated_min_any2_improve_prob']:.4f}/{best['repeated_min_all3_improve_prob']:.4f}`)."
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
    metric_cols = [
        "scope",
        "candidate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE_vs_stable",
        "delta_MAPE_vs_stable",
        "delta_p95_APE_vs_stable",
        "mean_move_weight",
    ]
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
    top_repeat = repeated[repeat_cols].sort_values(["any2_improve_prob", "all3_improve_prob"], ascending=False).head(80)
    top_rules = rules.sort_values(["directional_score", "min_n"], ascending=[True, False]).head(80)

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber ultra-micro p95-first directional correction",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF31의 fixed p95 근소 악화를 줄이기 위해 더 작은 weight/cap과 p95-first segment를 검증.",
            "- 후보 선택: validation row/artist OOF segment consensus + residual direction consensus + p95 guard 후보를 사용.",
            "- fixed test와 0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 안정 기준 `hcoef_stable` fixed test: `{base['test_MdAPE']:.4f}/{base['test_MAPE']:.4f}/{base['test_p95_APE']:.4f}`.",
            "- p95를 지키는 초미세 이동만 허용했으므로, 개선폭이 작으면 운영 후보가 아니라 p95-neutral 참고 후보로만 분리.",
            "",
            "## 2. 보정 공식",
            "",
            "- 방향 확인: segment의 `actual_log - hcoef_stable` 중앙값과 `source - hcoef_stable` 중앙값의 부호가 row/artist OOF 양쪽에서 일치하는지 확인.",
            "- 적용식: `corrected_log = hcoef_stable + clip(weight * (source_candidate - hcoef_stable), -cap, cap)`.",
            "- p95-first 후보는 row/artist OOF segment 양쪽에서 p95가 기준보다 나빠지지 않는 rule만 사용.",
            "- 조건을 만족하지 않으면 `hcoef_stable`을 그대로 유지.",
            "",
            "## 3. 사용한 source 후보",
            "",
            h24.md_table(sources, max_rows=20),
            "",
            "## 4. 방향 일치 segment rule",
            "",
            h24.md_table(
                top_rules[
                    [
                        "source_candidate",
                        "group_name",
                        "rule_key",
                        "min_n",
                        "directional_score",
                        "stable_residual_median_row",
                        "source_move_median_row",
                        "stable_residual_median_artist",
                        "source_move_median_artist",
                        "median_abs_residual_delta_row",
                        "median_abs_residual_delta_artist",
                        "all3_safe",
                        "any2_safe",
                        "mape_guarded",
                    ]
                ].round(4),
                max_rows=80,
            ),
            "",
            "## 5. 정책 후보 설정",
            "",
            h24.md_table(policies.head(100), max_rows=100),
            "",
            "## 6. 선택 후보 요약",
            "",
            h24.md_table(selected[selected_cols].round(4), max_rows=100),
            "",
            "## 7. Scope별 metrics",
            "",
            h24.md_table(metrics[metric_cols].round(4), max_rows=140),
            "",
            "## 8. 반복 split/artist holdout 요약",
            "",
            h24.md_table(top_repeat.round(4), max_rows=80),
            "",
            "## 9. 계수/구간 해석",
            "",
            h24.md_table(coeffs.round(6), max_rows=120),
            "",
            "## 10. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=100),
            "",
            "## 11. 다음 방향",
            "",
            "- ultra-micro p95-first correction도 기준 후보를 넘지 못하면 점 예측 이동 추가 세분화는 중단.",
            "- 방향 일치 segment는 가격 범위, 신뢰도, 수동 검수 기준으로 재사용.",
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
    (DOC_ROOT / "pp_hcoef32_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef32_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(sources: pd.DataFrame, policies: pd.DataFrame) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiments": ["PP-HCOEF29", "PP-HCOEF30", "PP-HCOEF31"],
        "baseline": BASELINE,
        "reference": REFERENCE,
        "source_count": int(len(sources)),
        "policy_count": int(len(policies)),
        "weights": WEIGHTS,
        "caps": CAPS,
        "top_ns": TOP_NS,
        "selection_rule": "validation row/artist OOF segment consensus plus residual direction consensus and p95-first rule candidates; fixed test and 0604 confirmation only",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    sources = choose_sources()
    seed, existing = h30.load_frames(sources)
    segment_metrics = h30.segment_metric_rows(seed, sources)
    consensus = h30.consensus_rules(segment_metrics)
    rules = add_direction_stats(seed, consensus)
    policies, policy_rows = build_policies(rules, sources)
    if not policies:
        raise RuntimeError("No p95-neutral directional policies were generated.")

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
