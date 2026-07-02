#!/usr/bin/env python3
"""PP-WLITE-Q4: final comparison for Warm-lite Quantile candidates.

Q1/Q2/Q3 산출물을 같은 행 기준으로 병합해 마지막 후보 비교를 수행한다.

비교 질문:
- Q1-like 실존 저이력 leave-one-out에서는 단순 Quantile blend와 residual 보정 중 어느 쪽이 좋은가?
- Q2-like k절단 운영 시뮬레이션에서는 단순 Quantile과 residual 보정 중 어느 쪽이 좋은가?
- 운영 후보로 무엇을 권장할 수 있는가?
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WLITE-Q4_quantile_final_comparison"
N_BOOT = 800

Q1_PREV = REPO / "experiments" / "track6" / "PP-WLITE-Q1_warm_lite_quantile_candidate_validation" / "outputs" / "predictions_all_seeds.csv"
Q2_PREV = REPO / "experiments" / "track6" / "PP-WLITE-Q2_quantile_followup_truncation_validation" / "outputs" / "predictions_all_conditions.csv"
Q3_Q1 = REPO / "experiments" / "track6" / "PP-WLITE-Q3_quantile_residual_correction_validation" / "outputs" / "q1_predictions_all_seeds.csv"
Q3_Q2 = REPO / "experiments" / "track6" / "PP-WLITE-Q3_quantile_residual_correction_validation" / "outputs" / "q2_predictions_all_conditions.csv"


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def metric_triplet(frame: pd.DataFrame, pred_col: str) -> dict[str, float]:
    return {k: round(float(v), 6) for k, v in cb1.mt(frame["actual_price"].to_numpy(dtype=float), frame[pred_col].to_numpy(dtype=float)).items()}


def metric_table(frame: pd.DataFrame, candidates: dict[str, str]) -> pd.DataFrame:
    rows = []
    for candidate, col in candidates.items():
        rows.append({"candidate": candidate, "n": int(len(frame)), **metric_triplet(frame, col)})
    out = pd.DataFrame(rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out.sort_values(["MAPE", "p95_APE", "MdAPE"])


def by_k_table(frame: pd.DataFrame, candidates: dict[str, str], group_col: str) -> pd.DataFrame:
    rows = []
    for key, group in frame.groupby(group_col, sort=True):
        for candidate, col in candidates.items():
            rows.append({group_col: int(key), "candidate": candidate, "n": int(len(group)), **metric_triplet(group, col)})
    out = pd.DataFrame(rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        out[f"rank_{metric}"] = out.groupby(group_col)[metric].rank(method="min").astype(int)
    return out.sort_values([group_col, "MAPE", "p95_APE"])


def paired_bootstrap(
    frame: pd.DataFrame,
    a_name: str,
    a_col: str,
    b_name: str,
    b_col: str,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(20260615)
    rows = []
    group_iter = frame.groupby(group_cols, sort=True) if group_cols else [((), frame)]
    for key, part in group_iter:
        artist_groups = pd.Series(np.arange(len(part))).groupby(part["artist_key"].astype(str).to_numpy()).apply(list)
        price = part["actual_price"].to_numpy(dtype=float)
        a_pred = part[a_col].to_numpy(dtype=float)
        b_pred = part[b_col].to_numpy(dtype=float)
        wins_a = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
        wins_b = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
        for _ in range(N_BOOT):
            sampled = rng.choice(len(artist_groups), size=len(artist_groups), replace=True)
            idx = np.concatenate([artist_groups.iloc[i] for i in sampled])
            am = cb1.mt(price[idx], a_pred[idx])
            bm = cb1.mt(price[idx], b_pred[idx])
            for metric in wins_a:
                wins_a[metric] += am[metric] < bm[metric]
                wins_b[metric] += bm[metric] < am[metric]
        row = {"candidate_a": a_name, "candidate_b": b_name, "n_boot": N_BOOT}
        if group_cols:
            if not isinstance(key, tuple):
                key = (key,)
            for col, value in zip(group_cols, key):
                row[col] = int(value)
        for metric in wins_a:
            row[f"p_a_better_{metric}"] = wins_a[metric] / N_BOOT
            row[f"p_b_better_{metric}"] = wins_b[metric] / N_BOOT
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_summary(boot: pd.DataFrame) -> pd.DataFrame:
    if len(boot) == 1:
        return boot.copy()
    rows = []
    for (a, b), group in boot.groupby(["candidate_a", "candidate_b"], sort=True):
        row = {"candidate_a": a, "candidate_b": b, "conditions": int(len(group))}
        for metric in ("MdAPE", "MAPE", "p95_APE"):
            col = f"p_a_better_{metric}"
            row[f"mean_{col}"] = float(group[col].mean())
            row[f"min_{col}"] = float(group[col].min())
            row[f"conditions_{col}_ge_0_90"] = int((group[col] >= 0.90).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def table_md(frame: pd.DataFrame, columns: list[str]) -> str:
    view = frame[columns].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def load_q1() -> pd.DataFrame:
    q1 = pd.read_csv(Q1_PREV)
    q3 = pd.read_csv(Q3_Q1)
    keys = ["seed", "_row", "artist_key", "history_k", "actual_price", "actual_log"]
    q1_cols = keys + [
        "all6_current_pred_log",
        "all6_50_lgbq_full_50_pred_log",
        "lgbq_full_lean_avg_pred_log",
        "lgbq_full_q50_pred_log",
    ]
    q3_cols = keys + [
        "qavg_lgbres_s05_cap010_pred_log",
        "qavg_lgbres_s05_cap005_pred_log",
        "qavg_cbres_s05_cap010_pred_log",
        "lgbq_full_lean_avg_pred_log",
    ]
    merged = q1[q1_cols].merge(q3[q3_cols], on=keys, suffixes=("_q1", "_q3"), validate="one_to_one")
    merged = merged.rename(
        columns={
            "all6_current_pred_log": "all6_current",
            "all6_50_lgbq_full_50_pred_log": "simple_all6_q50_blend",
            "lgbq_full_q50_pred_log": "simple_q50_full",
            "lgbq_full_lean_avg_pred_log_q1": "simple_qavg_q1",
            "lgbq_full_lean_avg_pred_log_q3": "q3_simple_qavg",
            "qavg_lgbres_s05_cap010_pred_log": "residual_lgb_s05_cap010",
            "qavg_lgbres_s05_cap005_pred_log": "residual_lgb_s05_cap005",
            "qavg_cbres_s05_cap010_pred_log": "residual_cb_s05_cap010",
        }
    )
    return merged


def load_q2() -> pd.DataFrame:
    q2 = pd.read_csv(Q2_PREV)
    q3 = pd.read_csv(Q3_Q2)
    keys = ["trunc_seed", "k", "_track6_row_id", "artist_key", "actual_price", "actual_log", "artist_history_n"]
    q2_cols = keys + [
        "all6_current_pred_log",
        "lgbq_full_lean_avg_pred_log",
        "all6_50_lgbq_full_50_pred_log",
        "lgbq_full_q50_pred_log",
    ]
    q3_cols = keys + [
        "qavg_lgbres_s05_cap010_pred_log",
        "qavg_lgbres_s05_cap005_pred_log",
        "qavg_cbres_s05_cap010_pred_log",
        "lgbq_full_lean_avg_pred_log",
    ]
    merged = q2[q2_cols].merge(q3[q3_cols], on=keys, suffixes=("_q2", "_q3"), validate="one_to_one")
    merged = merged.rename(
        columns={
            "all6_current_pred_log": "all6_current",
            "lgbq_full_lean_avg_pred_log_q2": "simple_qavg_q2",
            "all6_50_lgbq_full_50_pred_log": "simple_all6_q50_blend",
            "lgbq_full_q50_pred_log": "simple_q50_full",
            "lgbq_full_lean_avg_pred_log_q3": "q3_simple_qavg",
            "qavg_lgbres_s05_cap010_pred_log": "residual_lgb_s05_cap010",
            "qavg_lgbres_s05_cap005_pred_log": "residual_lgb_s05_cap005",
            "qavg_cbres_s05_cap010_pred_log": "residual_cb_s05_cap010",
        }
    )
    return merged


def recommendation(q1_metrics: pd.DataFrame, q2_metrics: pd.DataFrame) -> dict:
    q1_simple = q1_metrics[q1_metrics["candidate"].eq("simple_all6_q50_blend")].iloc[0]
    q1_resid = q1_metrics[q1_metrics["candidate"].eq("residual_lgb_s05_cap010")].iloc[0]
    q2_simple = q2_metrics[q2_metrics["candidate"].eq("simple_qavg_q2")].iloc[0]
    q2_resid = q2_metrics[q2_metrics["candidate"].eq("residual_lgb_s05_cap010")].iloc[0]
    return {
        "recommended_candidate": "residual_lgb_s05_cap010",
        "candidate_formula": "lgbq_full_lean_avg + clip(0.50 * LightGBMHuberResidual, -0.10, +0.10)",
        "reason": [
            "Q2-like 운영 절단 검증에서 simple_qavg_q2보다 MdAPE/MAPE/p95가 모두 개선됨",
            "Q1-like에서는 simple_all6_q50_blend가 MdAPE/MAPE 우세이나 residual 후보가 p95를 크게 개선함",
            "운영 후보는 중앙오차만이 아니라 저이력 tail 안정성이 중요하므로 residual 후보를 우선 권장",
        ],
        "q1_tradeoff_vs_simple_all6_q50_blend": {
            "MdAPE_delta": float(q1_resid["MdAPE"] - q1_simple["MdAPE"]),
            "MAPE_delta": float(q1_resid["MAPE"] - q1_simple["MAPE"]),
            "p95_delta": float(q1_resid["p95_APE"] - q1_simple["p95_APE"]),
        },
        "q2_gain_vs_simple_qavg": {
            "MdAPE_delta": float(q2_resid["MdAPE"] - q2_simple["MdAPE"]),
            "MAPE_delta": float(q2_resid["MAPE"] - q2_simple["MAPE"]),
            "p95_delta": float(q2_resid["p95_APE"] - q2_simple["p95_APE"]),
        },
    }


def main() -> None:
    ensure_dirs()
    q1 = load_q1()
    q2 = load_q2()

    q1_candidates = {
        "all6_current": "all6_current",
        "simple_all6_q50_blend": "simple_all6_q50_blend",
        "simple_qavg_q1": "simple_qavg_q1",
        "residual_lgb_s05_cap010": "residual_lgb_s05_cap010",
        "residual_lgb_s05_cap005": "residual_lgb_s05_cap005",
        "residual_cb_s05_cap010": "residual_cb_s05_cap010",
    }
    q2_candidates = {
        "all6_current": "all6_current",
        "simple_qavg_q2": "simple_qavg_q2",
        "simple_all6_q50_blend": "simple_all6_q50_blend",
        "residual_lgb_s05_cap010": "residual_lgb_s05_cap010",
        "residual_lgb_s05_cap005": "residual_lgb_s05_cap005",
        "residual_cb_s05_cap010": "residual_cb_s05_cap010",
    }

    q1_metrics = metric_table(q1, q1_candidates)
    q2_metrics = metric_table(q2, q2_candidates)
    q1_by_k = by_k_table(q1, q1_candidates, "history_k")
    q2_by_k = by_k_table(q2, q2_candidates, "k")

    q1_boot_resid_vs_simple = paired_bootstrap(
        q1,
        "residual_lgb_s05_cap010",
        "residual_lgb_s05_cap010",
        "simple_all6_q50_blend",
        "simple_all6_q50_blend",
    )
    q2_boot_resid_vs_simple = paired_bootstrap(
        q2,
        "residual_lgb_s05_cap010",
        "residual_lgb_s05_cap010",
        "simple_qavg_q2",
        "simple_qavg_q2",
        ["trunc_seed", "k"],
    )
    q2_boot_resid_summary = bootstrap_summary(q2_boot_resid_vs_simple)

    q1.to_csv(EXP / "outputs" / "q1_final_comparison_rows.csv", index=False)
    q2.to_csv(EXP / "outputs" / "q2_final_comparison_rows.csv", index=False)
    q1_metrics.to_csv(EXP / "outputs" / "q1_metrics_overall.csv", index=False)
    q2_metrics.to_csv(EXP / "outputs" / "q2_metrics_overall.csv", index=False)
    q1_by_k.to_csv(EXP / "outputs" / "q1_metrics_by_history_k.csv", index=False)
    q2_by_k.to_csv(EXP / "outputs" / "q2_metrics_by_k.csv", index=False)
    q1_boot_resid_vs_simple.to_csv(EXP / "outputs" / "q1_boot_residual_vs_simple.csv", index=False)
    q2_boot_resid_vs_simple.to_csv(EXP / "outputs" / "q2_boot_residual_vs_simple_by_condition.csv", index=False)
    q2_boot_resid_summary.to_csv(EXP / "outputs" / "q2_boot_residual_vs_simple_summary.csv", index=False)

    rec = recommendation(q1_metrics, q2_metrics)
    config = {
        "experiment_id": "PP-WLITE-Q4",
        "experiment_slug": EXP.name,
        "source_experiments": [
            "PP-WLITE-Q1_warm_lite_quantile_candidate_validation",
            "PP-WLITE-Q2_quantile_followup_truncation_validation",
            "PP-WLITE-Q3_quantile_residual_correction_validation",
        ],
        "n_boot": N_BOOT,
        "recommendation": rec,
        "prohibitions": ["0604 사용 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# PP-WLITE-Q4 Warm-lite Quantile 최종 후보 비교",
        "",
        "## 1. 목적",
        "",
        "Q1/Q2/Q3 산출물을 같은 행 기준으로 병합해 단순 Quantile blend와 Quantile+LightGBM residual 보정 후보를 마지막으로 비교한다.",
        "",
        "## 2. Q1-like 실존 저이력 leave-one-out",
        "",
        table_md(q1_metrics, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"]),
        "",
        "## 3. Q1-like by history_k",
        "",
        table_md(
            q1_by_k[q1_by_k["candidate"].isin(["all6_current", "simple_all6_q50_blend", "residual_lgb_s05_cap010"])],
            ["history_k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"],
        ),
        "",
        "## 4. Q1 residual vs simple bootstrap",
        "",
        table_md(q1_boot_resid_vs_simple, ["candidate_a", "candidate_b", "n_boot", "p_a_better_MdAPE", "p_a_better_MAPE", "p_a_better_p95_APE", "p_b_better_MdAPE", "p_b_better_MAPE", "p_b_better_p95_APE"]),
        "",
        "## 5. Q2-like k절단 운영 시뮬레이션",
        "",
        table_md(q2_metrics, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"]),
        "",
        "## 6. Q2-like by k",
        "",
        table_md(
            q2_by_k[q2_by_k["candidate"].isin(["all6_current", "simple_qavg_q2", "residual_lgb_s05_cap010"])],
            ["k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"],
        ),
        "",
        "## 7. Q2 residual vs simple bootstrap summary",
        "",
        table_md(q2_boot_resid_summary, ["candidate_a", "candidate_b", "conditions", "mean_p_a_better_MdAPE", "mean_p_a_better_MAPE", "mean_p_a_better_p95_APE", "conditions_p_a_better_MdAPE_ge_0_90", "conditions_p_a_better_MAPE_ge_0_90", "conditions_p_a_better_p95_APE_ge_0_90"]),
        "",
        "## 8. 최종 판단",
        "",
        json.dumps(rec, ensure_ascii=False, indent=2),
        "",
        "## 9. Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print("[q1 overall]")
    print(q1_metrics.to_string(index=False))
    print("[q2 overall]")
    print(q2_metrics.to_string(index=False))
    print("[recommendation]")
    print(json.dumps(rec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
