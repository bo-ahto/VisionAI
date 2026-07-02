#!/usr/bin/env python3
"""PP-WMIN9D: forced Warm/Warm-lite boundary checks.

This experiment answers two presentation-facing questions:

1. What happens if Warm-lite is forcibly evaluated on the 5+ Warm fixed-test set?
2. What is the best available evidence for using a Warm-like path on k=1?

Warm-lite's production API intentionally rejects k outside 1..4. This script
does not change that contract; it calls the frozen feature-stat builder and
frozen Huber ensemble directly to measure the counterfactual.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WMIN9D_forced_warm_warmlite_boundary"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin9d_forced_warm_warmlite_boundary_summary.md"
WARM_LITE_PREDICTOR = (
    REPO / "models" / "track6" / "warm_lite_v0.1" / "predict" / "predict_warm_lite_v0_1.py"
)
WMIN8_SELECTED = (
    REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "artifacts"
    / "wmin8_selected_candidate_predictions.csv"
)
WMIN9C_COMPARISON = (
    REPO / "experiments" / "track6" / "PP-WMIN9C_warm_lite_vs_wmin8_lowhistory"
    / "outputs" / "comparison.csv"
)


def load_warm_lite_module():
    spec = importlib.util.spec_from_file_location("warm_lite_v0_1", WARM_LITE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Warm-lite predictor from {WARM_LITE_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metrics(actual_price: np.ndarray, pred_log: np.ndarray, actual_log: np.ndarray | None = None) -> dict[str, float]:
    actual_price = np.asarray(actual_price, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    if actual_log is None:
        actual_log = np.log(np.clip(actual_price, 1.0, None))
    else:
        actual_log = np.asarray(actual_log, dtype=float)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
    }


def metric_row(candidate: str, frame: pd.DataFrame, pred_col: str) -> dict[str, object]:
    mt = metrics(
        frame["actual_price"].to_numpy(dtype=float),
        frame[pred_col].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
    )
    return {
        "candidate": candidate,
        "n": int(len(frame)),
        "MdAPE": mt["MdAPE"],
        "MAPE": mt["MAPE"],
        "p95_APE": mt["p95_APE"],
        "RMSE_log": mt["RMSE_log"],
    }


def round_metric_dict(row: dict[str, object], ndigits: int = 6) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in row.items():
        out[key] = round(float(value), ndigits) if isinstance(value, (float, np.floating)) else value
    return out


def force_warm_lite_on_warm_test() -> pd.DataFrame:
    warm_lite = load_warm_lite_module()
    params = warm_lite.load_params()
    models = warm_lite.load_models()

    warm_features = artifact_features()["warm"]
    train, _, test = load_scope("warm", warm_features)
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)

    missing = [c for c in warm_lite.REQUIRED if c not in test.columns]
    if missing:
        raise RuntimeError(f"Warm fixed-test is missing Warm-lite columns: {missing}")

    train_by_artist = {str(k): g.copy() for k, g in train.groupby("artist_key", sort=False)}
    parts: list[pd.DataFrame] = []
    for artist_key, group in test.groupby("artist_key", sort=False):
        artist_history = train_by_artist.get(str(artist_key))
        if artist_history is None:
            raise RuntimeError(f"Missing train history for artist_key={artist_key!r}")
        if len(artist_history) < 5:
            raise RuntimeError(f"Expected 5+ history for warm test artist_key={artist_key!r}, got {len(artist_history)}")

        fs = warm_lite.assign_stats(group.copy(), artist_history, params)
        pred_log = np.mean(
            [
                np.asarray(model.predict(fs[num_cols + params["huber_cat_cols"]]), dtype=float)
                for model, num_cols in zip(models, params["huber_num_cols"])
            ],
            axis=0,
        )
        out = group[
            ["_track6_row_id", "artist_key", "artist_name_ko", "price_krw", "ln_price_krw"]
        ].copy()
        out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
        out["artist_history_n"] = int(len(artist_history))
        out["forced_warm_lite_pred_log"] = pred_log
        out["forced_warm_lite_pred_price"] = np.clip(np.exp(pred_log), 1_000.0, None)
        parts.append(out)

    forced = pd.concat(parts, ignore_index=True)

    selected = pd.read_csv(WMIN8_SELECTED)
    selected = selected[selected["eval_split"].eq("test")].copy()
    if selected["_track6_row_id"].duplicated().any():
        labels = sorted(selected["candidate_label"].dropna().unique().tolist())
        if len(labels) == 1:
            selected = selected[selected["candidate_label"].eq(labels[0])].copy()
        if selected["_track6_row_id"].duplicated().any():
            raise RuntimeError("WMIN8 selected predictions contain duplicate test row ids")

    wmin8_cols = ["_track6_row_id", "pred_log", "pred_price", "candidate_label"]
    merged = forced.merge(selected[wmin8_cols], on="_track6_row_id", how="left", validate="one_to_one")
    if merged["pred_log"].isna().any():
        missing = int(merged["pred_log"].isna().sum())
        raise RuntimeError(f"Missing WMIN8 predictions for {missing} forced Warm-lite rows")
    merged = merged.rename(
        columns={
            "pred_log": "wmin8_pred_log",
            "pred_price": "wmin8_pred_price",
            "candidate_label": "wmin8_candidate_label",
        }
    )
    merged["history_bin"] = pd.cut(
        merged["artist_history_n"],
        bins=[4, 9, 19, 49, np.inf],
        labels=["5_to_9", "10_to_19", "20_to_49", "50_plus"],
        right=True,
    ).astype(str)
    return merged


def load_k1_warm_evidence() -> tuple[pd.DataFrame, pd.DataFrame]:
    comp = pd.read_csv(WMIN9C_COMPARISON)
    k1 = comp[comp["k"].astype(str).eq("1")].copy()
    overall = comp[comp["k"].astype(str).eq("all")].copy()
    if k1.empty or overall.empty:
        raise RuntimeError(f"Missing k=1 or overall rows in {WMIN9C_COMPARISON}")
    return k1, overall


def table_md(frame: pd.DataFrame, cols: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    view = frame[cols].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda v: f"{v:.6f}")
    header = "| " + " | ".join(view.columns.astype(str)) + " |"
    sep = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = [
        "| " + " | ".join(str(row[col]) for col in view.columns) + " |"
        for _, row in view.iterrows()
    ]
    return "\n".join([header, sep, *rows])


def write_reports(
    forced: pd.DataFrame,
    overall_metrics: pd.DataFrame,
    by_bin: pd.DataFrame,
    k1: pd.DataFrame,
    low_history_overall: pd.DataFrame,
    decision: dict[str, object],
) -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    forced.to_csv(EXP / "outputs" / "forced_warm_lite_on_5plus_predictions.csv", index=False)
    overall_metrics.to_csv(EXP / "outputs" / "forced_warm_lite_on_5plus_metrics.csv", index=False)
    by_bin.to_csv(EXP / "outputs" / "forced_warm_lite_on_5plus_by_history_bin.csv", index=False)
    k1.to_csv(EXP / "outputs" / "warm_like_on_k1_from_wmin9c.csv", index=False)
    low_history_overall.to_csv(EXP / "outputs" / "low_history_overall_from_wmin9c.csv", index=False)
    pd.DataFrame([decision]).to_csv(EXP / "outputs" / "boundary_experiment_decision.csv", index=False)

    config = {
        "experiment_id": "PP-WMIN9D",
        "purpose": "Counterfactual boundary check for Warm/Warm-lite split.",
        "forced_warm_lite_scope": "607-row Warm fixed test where all artists have 5+ train histories.",
        "forced_warm_lite_note": "Production Warm-lite API remains 1..4 only; this script bypasses only for measurement.",
        "k1_warm_like_source": str(WMIN9C_COMPARISON.relative_to(REPO)),
        "k1_warm_like_note": "WMIN9C uses WMIN8 svc-core proxy, not full WMIN8 router.",
        "decision": decision,
    }
    (EXP / "artifacts" / "run_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = "\n".join(
        [
            "# PP-WMIN9D forced Warm/Warm-lite boundary check",
            "",
            "## 1. Purpose",
            "",
            "- Check whether 5+ history should stay on Warm by forcing the frozen Warm-lite ensemble onto the Warm fixed-test rows.",
            "- Reuse the existing same-row low-history experiment for the k=1 Warm-like question.",
            "",
            "## 2. Forced Warm-lite on 5+ Warm fixed test",
            "",
            table_md(overall_metrics, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]),
            "",
            "## 3. Forced Warm-lite on 5+ by history bin",
            "",
            table_md(by_bin, ["history_bin", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]),
            "",
            "## 4. k=1 Warm-like evidence from PP-WMIN9C",
            "",
            table_md(k1, ["candidate", "k", "n", "MdAPE", "MAPE", "p95_APE"]),
            "",
            "## 5. Low-history overall evidence from PP-WMIN9C",
            "",
            table_md(low_history_overall, ["candidate", "k", "n", "MdAPE", "MAPE", "p95_APE"]),
            "",
            "## 6. Decision",
            "",
            json.dumps(decision, ensure_ascii=False, indent=2),
            "",
        ]
    )
    (EXP / "reports" / "result_report.md").write_text(report, encoding="utf-8")

    doc = "\n".join(
        [
            "# PP-WMIN9D Warm/Warm-lite boundary forced comparison summary",
            "",
            "## Summary",
            "",
            "- 5+ history rows: forced Warm-lite is compared against the selected WMIN8 Warm prediction on the same 607 fixed-test rows.",
            "- k=1 rows: existing PP-WMIN9C same-row low-history comparison is reused because full WMIN8 is a 5+ router; the comparable Warm-like evidence is WMIN8 svc-core proxy.",
            "",
            "## 5+ history same-row result",
            "",
            table_md(overall_metrics, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]),
            "",
            "## 5+ history by train-history bin",
            "",
            table_md(by_bin, ["history_bin", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]),
            "",
            "## k=1 Warm-like result",
            "",
            table_md(k1, ["candidate", "k", "n", "MdAPE", "MAPE", "p95_APE"]),
            "",
            "## Interpretation",
            "",
            f"- {decision['five_plus_interpretation']}",
            f"- {decision['k1_interpretation']}",
            "",
            "## Caveats",
            "",
            "- Forced Warm-lite on 5+ is a counterfactual measurement, not a valid production route.",
            "- k=1 Warm-like evidence uses WMIN8 svc-core proxy from PP-WMIN9C, not full WMIN8.",
            "",
        ]
    )
    DOC_SUMMARY.write_text(doc, encoding="utf-8")


def main() -> None:
    forced = force_warm_lite_on_warm_test()

    rows = [
        metric_row("forced_warm_lite_on_5plus", forced, "forced_warm_lite_pred_log"),
        metric_row("wmin8_warm_selected", forced, "wmin8_pred_log"),
    ]
    overall_metrics = pd.DataFrame([round_metric_dict(row) for row in rows])

    bin_rows: list[dict[str, object]] = []
    for history_bin, group in forced.groupby("history_bin", sort=False):
        for candidate, pred_col in (
            ("forced_warm_lite_on_5plus", "forced_warm_lite_pred_log"),
            ("wmin8_warm_selected", "wmin8_pred_log"),
        ):
            row = metric_row(candidate, group, pred_col)
            row["history_bin"] = history_bin
            bin_rows.append(round_metric_dict(row))
    by_bin = pd.DataFrame(bin_rows)[
        ["history_bin", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ]

    k1, low_history_overall = load_k1_warm_evidence()

    wm = overall_metrics.set_index("candidate")
    forced_row = wm.loc["forced_warm_lite_on_5plus"]
    warm_row = wm.loc["wmin8_warm_selected"]
    force_worse_all = bool(
        forced_row["MdAPE"] > warm_row["MdAPE"]
        and forced_row["MAPE"] > warm_row["MAPE"]
        and forced_row["p95_APE"] > warm_row["p95_APE"]
    )

    k1_pivot = k1.set_index("candidate")
    warm_lite_k1 = k1_pivot.loc["warm_lite"]
    warm_like_k1 = k1_pivot.loc["wmin8_svc_core"]
    k1_warm_lite_wins_mdape = bool(warm_lite_k1["MdAPE"] < warm_like_k1["MdAPE"])
    k1_warm_lite_wins_p95 = bool(warm_lite_k1["p95_APE"] < warm_like_k1["p95_APE"])
    k1_warm_lite_wins_mape = bool(warm_lite_k1["MAPE"] < warm_like_k1["MAPE"])

    decision = {
        "five_plus_forced_warm_lite_worse_than_wmin8_all_primary_metrics": force_worse_all,
        "five_plus_interpretation": (
            "5+ same-row fixed-test shows forced Warm-lite is worse than WMIN8 on MdAPE, MAPE, and p95_APE."
            if force_worse_all
            else "5+ same-row fixed-test does not show forced Warm-lite is worse on all primary metrics; review metric trade-offs."
        ),
        "k1_warm_lite_wins_MdAPE": k1_warm_lite_wins_mdape,
        "k1_warm_lite_wins_MAPE": k1_warm_lite_wins_mape,
        "k1_warm_lite_wins_p95_APE": k1_warm_lite_wins_p95,
        "k1_interpretation": (
            "For k=1, Warm-lite beats WMIN8 svc-core proxy on MdAPE and p95_APE; MAPE is checked separately because the two are nearly tied."
        ),
    }

    write_reports(forced, overall_metrics, by_bin, k1, low_history_overall, decision)

    print(overall_metrics.to_string(index=False))
    print()
    print(by_bin.to_string(index=False))
    print()
    print(k1.to_string(index=False))
    print()
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
