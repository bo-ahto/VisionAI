#!/usr/bin/env python3
"""Run PP-HCOEF5: repeated validation for basis-Huber blend candidates.

PP-HCOEF4 found a loose comparable-basis Huber candidate with better MdAPE/MAPE
but worse fixed-test p95. This follow-up checks whether a capped blend on top of
the existing HCOEF3 stable candidate preserves p95 while keeping the gains.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_hcoef4_warm_basis_generation_refinement as hcoef4  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF5"
EXP_SLUG = "PP-HCOEF5_warm_basis_hcoef_blend_repeated_validation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = "current_70_30"
STABLE = "hcoef2_size_reliability_cap005_s050"
N_FOLDS = 5
N_REPEATS = 12
SEED = 20260608

BASIS_CONFIGS = [
    {
        "name": "loose_basis_core_huber_alpha0p1",
        "policy": "loose",
        "feature_key": "basis_core",
        "kind": "huber",
        "alpha": 0.1,
        "source": "PP-HCOEF4 mape_guarded selected candidate",
    },
    {
        "name": "loose_basis_core_huber_alpha0p01",
        "policy": "loose",
        "feature_key": "basis_core",
        "kind": "huber",
        "alpha": 0.01,
        "source": "PP-HCOEF4 fixed test top neighbour",
    },
    {
        "name": "loose_basis_gap_huber_alpha0p1",
        "policy": "loose",
        "feature_key": "basis_gap_reliability",
        "kind": "huber",
        "alpha": 0.1,
        "source": "PP-HCOEF4 gap/reliability variant",
    },
]

CAP_BLEND_GRID = [
    {"cap": cap, "strength": strength}
    for cap in [0.03, 0.05, 0.08]
    for strength in [0.25, 0.50, 0.75, 1.00]
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def build_frames() -> dict[str, pd.DataFrame]:
    base = hcoef4.build_eval_frames()
    basis = hcoef4.build_basis_features("loose")
    return hcoef4.merge_policy_frames(base, basis, "loose")


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef1.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def hcoef2_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    features = hcoef1.RESIDUAL_FEATURE_SETS["resid_basis_size_reliability"]
    target = train["actual_log"].to_numpy(dtype=float) - train[REFERENCE].to_numpy(dtype=float)
    model = hcoef1.linear_pipeline("huber", 0.01)
    model.fit(train[features], target)
    raw = np.asarray(model.predict(eval_frame[features]), dtype=float)
    pred = eval_frame[REFERENCE].to_numpy(dtype=float) + np.clip(raw, -0.05, 0.05) * 0.50
    return pred, model


def basis_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, Any]:
    features = hcoef4.BASIS_FEATURE_SETS[str(config["feature_key"])]
    target = train["actual_log"].to_numpy(dtype=float)
    model = hcoef4.linear_pipeline(str(config["kind"]), float(config["alpha"]))
    model.fit(train[features], target)
    pred = np.asarray(model.predict(eval_frame[features]), dtype=float)
    return pred, model


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.arange(n))
    folds = np.array_split(order, N_FOLDS)
    all_idx = np.arange(n)
    return [(np.setdiff1d(all_idx, hold, assume_unique=False), hold) for hold in folds]


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    artists = frame["artist_key"].astype(str).to_numpy()
    unique = rng.permutation(np.unique(artists))
    fold_of = {artist: idx % N_FOLDS for idx, artist in enumerate(unique)}
    all_idx = np.arange(len(frame))
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for fold_id in range(N_FOLDS):
        hold = np.flatnonzero([fold_of[artist] == fold_id for artist in artists])
        out.append((np.setdiff1d(all_idx, hold, assume_unique=False), hold))
    return out


def candidate_predictions_from_pair(stable_pred: np.ndarray, basis_pred: np.ndarray, basis_name: str) -> dict[str, np.ndarray]:
    out = {
        STABLE: stable_pred,
        basis_name: basis_pred,
    }
    diff = basis_pred - stable_pred
    for item in CAP_BLEND_GRID:
        cap = float(item["cap"])
        strength = float(item["strength"])
        name = f"{basis_name}_on_hcoef2_cap{cap:.2f}_s{strength:.2f}"
        out[name] = stable_pred + np.clip(diff, -cap, cap) * strength
    return out


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = row_folds(len(validation), seed) if scheme == "row_oof" else artist_folds(validation, seed)
            oof: dict[str, np.ndarray] = {}

            for fold_id, (train_idx, hold_idx) in enumerate(folds):
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                stable_pred, _ = hcoef2_prediction(train, hold)
                for config in BASIS_CONFIGS:
                    basis_pred, _ = basis_prediction(train, hold, config)
                    fold_preds = candidate_predictions_from_pair(stable_pred, basis_pred, str(config["name"]))
                    for candidate, pred in fold_preds.items():
                        if candidate not in oof:
                            oof[candidate] = np.full(len(validation), np.nan, dtype=float)
                        oof[candidate][hold_idx] = pred
                if STABLE not in oof:
                    oof[STABLE] = np.full(len(validation), np.nan, dtype=float)
                oof[STABLE][hold_idx] = stable_pred

            ref_metric = metric_from_frame(validation, oof[STABLE])
            for candidate, pred in oof.items():
                metric = metric_from_frame(validation, pred)
                metric_rows.append(
                    {
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "candidate": candidate,
                        "n": len(validation),
                        **metric,
                        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - ref_metric["MdAPE"],
                        "delta_MAPE_vs_hcoef2": metric["MAPE"] - ref_metric["MAPE"],
                        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - ref_metric["p95_APE"],
                        "improve_count_vs_hcoef2": int(metric["MdAPE"] < ref_metric["MdAPE"])
                        + int(metric["MAPE"] < ref_metric["MAPE"])
                        + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                    }
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, candidate, f"validation_{scheme}_repeat0", pred))
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    residual_rows: list[dict[str, Any]] = []

    stable_models: dict[str, np.ndarray] = {}
    for split in ["validation", "test", "0604_ex50"]:
        pred, stable_model = hcoef2_prediction(validation, frames[split])
        stable_models[split] = pred
        metric_rows.append(metric_row(split, STABLE, "current_stable_hcoef2", frames[split], pred, pred))
        pred_rows.append(prediction_frame(frames[split], STABLE, split, pred))

    for config in BASIS_CONFIGS:
        basis_by_split: dict[str, np.ndarray] = {}
        fitted_model = None
        for split in ["validation", "test", "0604_ex50"]:
            pred, model = basis_prediction(validation, frames[split], config)
            basis_by_split[split] = pred
            fitted_model = model
            metric_rows.append(metric_row(split, str(config["name"]), "basis_huber_full_validation", frames[split], pred, stable_models[split]))
            pred_rows.append(prediction_frame(frames[split], str(config["name"]), split, pred))
        if fitted_model is not None:
            coef_rows.append(hcoef4.coef_frame(fitted_model, str(config["name"]), hcoef4.BASIS_FEATURE_SETS[str(config["feature_key"])], str(config["kind"]), "actual_log"))

        for item in CAP_BLEND_GRID:
            cap = float(item["cap"])
            strength = float(item["strength"])
            candidate = f"{config['name']}_on_hcoef2_cap{cap:.2f}_s{strength:.2f}"
            for split in ["validation", "test", "0604_ex50"]:
                diff = basis_by_split[split] - stable_models[split]
                pred = stable_models[split] + np.clip(diff, -cap, cap) * strength
                metric_rows.append(metric_row(split, candidate, "basis_on_hcoef2_capped_blend", frames[split], pred, stable_models[split]))
                pred_rows.append(prediction_frame(frames[split], candidate, split, pred))

    predictions = pd.concat(pred_rows, ignore_index=True)
    for (split, candidate), group in predictions.groupby(["split", "candidate"], observed=False):
        residual_rows.append(
            {
                "split": split,
                "candidate": candidate,
                "median_residual_log": float(group["residual_log"].median()),
                "mean_residual_log": float(group["residual_log"].mean()),
                "residual_std": float(group["residual_log"].std()),
                "over_2x_n": int((group["pred_price"] >= group["actual_price"] * 2.0).sum()),
                "under_half_n": int((group["pred_price"] <= group["actual_price"] * 0.5).sum()),
                "ape_gt_100pct_n": int((group["ape"] > 1.0).sum()),
            }
        )
    return pd.DataFrame(metric_rows), predictions, pd.concat(coef_rows, ignore_index=True), pd.DataFrame(residual_rows)


def metric_row(split: str, candidate: str, method: str, frame: pd.DataFrame, pred: np.ndarray, stable_pred: np.ndarray) -> dict[str, Any]:
    metric = metric_from_frame(frame, pred)
    stable = metric_from_frame(frame, stable_pred)
    return {
        "validation_scheme": "fixed_confirmation",
        "repeat": -1,
        "candidate": candidate,
        "method": method,
        "split": split,
        "n": len(frame),
        **metric,
        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - stable["MdAPE"],
        "delta_MAPE_vs_hcoef2": metric["MAPE"] - stable["MAPE"],
        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - stable["p95_APE"],
        "improve_count_vs_hcoef2": int(metric["MdAPE"] < stable["MdAPE"])
        + int(metric["MAPE"] < stable["MAPE"])
        + int(metric["p95_APE"] < stable["p95_APE"]),
    }


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred: np.ndarray) -> pd.DataFrame:
    pred = np.asarray(pred, dtype=float)
    price = np.clip(np.exp(pred), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual,
            "pred_log": pred,
            "pred_price": price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred,
            "ape": np.abs(price - actual) / np.clip(actual, 1.0, None),
        }
    )


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    repeat_metrics = metrics[metrics["repeat"].ge(0)].copy()
    for (scheme, candidate), group in repeat_metrics.groupby(["validation_scheme", "candidate"], observed=False):
        rows.append(
            {
                "validation_scheme": scheme,
                "candidate": candidate,
                "mean_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].mean()),
                "mean_delta_MAPE_vs_hcoef2": float(group["delta_MAPE_vs_hcoef2"].mean()),
                "mean_delta_p95_APE_vs_hcoef2": float(group["delta_p95_APE_vs_hcoef2"].mean()),
                "std_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].std()),
                "MdAPE_improve_prob_vs_hcoef2": float((group["delta_MdAPE_vs_hcoef2"] < 0).mean()),
                "MAPE_improve_prob_vs_hcoef2": float((group["delta_MAPE_vs_hcoef2"] < 0).mean()),
                "p95_improve_prob_vs_hcoef2": float((group["delta_p95_APE_vs_hcoef2"] < 0).mean()),
                "all3_improve_prob_vs_hcoef2": float((group["improve_count_vs_hcoef2"] == 3).mean()),
                "mean_improve_count_vs_hcoef2": float(group["improve_count_vs_hcoef2"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["all3_improve_prob_vs_hcoef2", "mean_delta_MdAPE_vs_hcoef2", "mean_delta_MAPE_vs_hcoef2"],
        ascending=[False, True, True],
    )


def select_candidate(summary: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    row = summary[summary["validation_scheme"].eq("row_oof")].set_index("candidate")
    artist = summary[summary["validation_scheme"].eq("artist_oof")].set_index("candidate")
    fixed_test = fixed[fixed["split"].eq("test")].set_index("candidate")
    fixed_ops = fixed[fixed["split"].eq("0604_ex50")].set_index("candidate")
    candidates = sorted(set(row.index) & set(artist.index) & set(fixed_test.index))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "candidate": candidate,
                "row_all3_prob": row.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "artist_all3_prob": artist.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "row_delta_MdAPE": row.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "artist_delta_MdAPE": artist.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "test_delta_MdAPE": fixed_test.loc[candidate, "delta_MdAPE_vs_hcoef2"],
                "test_delta_MAPE": fixed_test.loc[candidate, "delta_MAPE_vs_hcoef2"],
                "test_delta_p95_APE": fixed_test.loc[candidate, "delta_p95_APE_vs_hcoef2"],
                "ops0604_delta_MdAPE": fixed_ops.loc[candidate, "delta_MdAPE_vs_hcoef2"] if candidate in fixed_ops.index else np.nan,
                "ops0604_delta_MAPE": fixed_ops.loc[candidate, "delta_MAPE_vs_hcoef2"] if candidate in fixed_ops.index else np.nan,
                "ops0604_delta_p95_APE": fixed_ops.loc[candidate, "delta_p95_APE_vs_hcoef2"] if candidate in fixed_ops.index else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["passes_repeat_gate"] = (
        out["row_all3_prob"].ge(0.90)
        & out["artist_all3_prob"].ge(0.90)
        & out["row_delta_MdAPE"].lt(0)
        & out["artist_delta_MdAPE"].lt(0)
    )
    out["passes_fixed_guard"] = out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].lt(0) & out["test_delta_p95_APE"].le(0.02)
    return out.sort_values(["passes_repeat_gate", "passes_fixed_guard", "test_delta_MdAPE"], ascending=[False, False, True])


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return str(value)

    lines = ["| " + " | ".join(map(str, data.columns)) + " |", "| " + " | ".join(["---"] * len(data.columns)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
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
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(summary: pd.DataFrame, fixed: pd.DataFrame, selection: pd.DataFrame, coeffs: pd.DataFrame, residuals: pd.DataFrame) -> None:
    fixed_test = fixed[fixed["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    decision = "채택 후보 없음"
    if not selection.empty:
        best = selection.iloc[0]
        if bool(best["passes_repeat_gate"]) and bool(best["passes_fixed_guard"]):
            decision = f"Warm 반복 검증 후보: `{best['candidate']}`"
        elif bool(best["passes_repeat_gate"]):
            decision = f"반복 OOF 신호는 있으나 fixed guard 미통과: `{best['candidate']}`"
        else:
            decision = "HCOEF4 basis 후보는 반복 검증 또는 fixed p95 guard를 통과하지 못해 보류"
    md = "\n".join(
        [
            f"# {EXP_ID} Warm 기준가-HCOEF 안정 결합 반복 검증",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF4의 loose 기준가 Huber 후보를 HCOEF3 안정 후보 위에 제한적으로 결합해 p95 악화 없이 MdAPE/MAPE를 개선할 수 있는지 확인.",
            "- 기준 후보: `hcoef2_size_reliability_cap005_s050`.",
            "- 검증 방식: validation row OOF 12회, artist OOF 12회, 각 5 folds. fixed test/0604는 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}",
            "- fixed test만 좋은 후보는 채택하지 않고 반복 OOF와 p95 guard를 함께 본다.",
            "",
            "## 2. 반복 OOF 요약",
            "",
            markdown_table(summary.round(4), max_rows=28),
            "",
            "## 3. 후보 선택표",
            "",
            markdown_table(selection.round(4), max_rows=20),
            "",
            "## 4. Fixed test 상위 후보",
            "",
            markdown_table(fixed_test[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_hcoef2", "delta_MAPE_vs_hcoef2", "delta_p95_APE_vs_hcoef2"]].round(4), max_rows=20),
            "",
            "## 5. 주요 계수",
            "",
            "- 계수는 표준화된 피처 기준이다. basis-Huber 후보의 방향성 해석용이다.",
            markdown_table(coeffs.head(50).round(5)),
            "",
            "## 6. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=40),
            "",
            "## 7. 산출물",
            "",
            "- `outputs/repeated_validation_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/fixed_confirmation_metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef5_warm_basis_hcoef_blend_repeated_validation_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef5_warm_basis_hcoef_blend_repeated_validation_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"])
    summary = summarize_repeated(repeated_metrics)
    fixed_metrics, fixed_predictions, coeffs, residuals = fixed_confirmation(frames)
    selection = select_candidate(summary, fixed_metrics)

    out = EXP_DIR / "outputs"
    repeated_metrics.to_csv(out / "repeated_validation_metrics.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    fixed_metrics.to_csv(out / "fixed_confirmation_metrics.csv", index=False)
    pd.concat([repeated_predictions, fixed_predictions], ignore_index=True).to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    selection.to_csv(out / "selected_candidates.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": STABLE,
        "basis_configs": BASIS_CONFIGS,
        "cap_blend_grid": CAP_BLEND_GRID,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "seed": SEED,
        "selection_policy": "row/artist repeated OOF first; fixed test p95 guard second",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, fixed_metrics, selection, coeffs, residuals)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selection top ---")
    print(selection.head(12).round(4).to_string(index=False))
    print("--- fixed test top ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(12)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_vs_hcoef2", "delta_MAPE_vs_hcoef2", "delta_p95_APE_vs_hcoef2"]]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
