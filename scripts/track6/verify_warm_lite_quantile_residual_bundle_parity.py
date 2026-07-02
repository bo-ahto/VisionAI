#!/usr/bin/env python3
"""Replay parity for the frozen Warm-lite Quantile residual bundle."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_q3_spec = importlib.util.spec_from_file_location(
    "wlite_q3", SCRIPT_DIR / "run_pp_wlite_q3_quantile_residual_correction_validation.py"
)
q3 = importlib.util.module_from_spec(_q3_spec)
_q3_spec.loader.exec_module(q3)


REPO = Path(__file__).resolve().parents[2]
BUNDLE_PREDICTOR = (
    REPO
    / "models"
    / "track6"
    / "warm_lite_quantile_residual_v0.1"
    / "predict"
    / "predict_warm_lite_quantile_residual_v0_1.py"
)
REF_Q2 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-WLITE-Q3_quantile_residual_correction_validation"
    / "outputs"
    / "q2_predictions_all_conditions.csv"
)
OUT = REPO / "experiments" / "track6" / "PP-WLITE-Q5_quantile_residual_bundle_api_parity"


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)


def load_predictor():
    spec = importlib.util.spec_from_file_location("wlite_qres", BUNDLE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {BUNDLE_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ensure_dirs()
    if not REF_Q2.exists():
        raise FileNotFoundError(REF_Q2)
    ref = pd.read_csv(REF_Q2)
    predictor = load_predictor()
    params = predictor.load_params()
    models = predictor.load_models()

    warm_features = artifact_features()["warm"]
    needed = list(
        dict.fromkeys(
            warm_features
            + predictor.REQUIRED
            + [
                "_track6_row_id",
                "artist_key",
                "price_krw",
                "ln_price_krw",
                "log_area",
                "medium_support_bucket",
                "size_bucket",
                "medium_category",
                "support_category",
            ]
        )
    )
    train, _, test = load_scope("warm", needed)
    train = train[needed].reset_index(drop=True)
    test = test[needed].reset_index(drop=True)
    target_artists = set(test["artist_key"].astype(str))

    parts = []
    for trunc_seed in q3.TRUNC_SEEDS:
        for k in q3.KS:
            train_k = q3.truncate_train(train, target_artists, trunc_seed, k)
            train_by_artist = {
                str(artist): group.copy()
                for artist, group in train_k.groupby("artist_key", sort=False)
            }
            for artist_key, group in test.groupby(test["artist_key"].astype(str), sort=False):
                history = train_by_artist.get(str(artist_key))
                if history is None or len(history) < 1:
                    raise RuntimeError(f"Missing truncated artist history: {artist_key}")
                pred = predictor.predict(
                    group[predictor.REQUIRED].copy(),
                    history,
                    models=models,
                    params=params,
                )
                out = group[["_track6_row_id", "artist_key"]].copy()
                out.insert(0, "k", k)
                out.insert(0, "trunc_seed", trunc_seed)
                out["bundle_pred_log"] = pred["warm_lite_pred_log"].to_numpy(dtype=float)
                parts.append(out)

    replay = pd.concat(parts, ignore_index=True)
    merged = replay.merge(
        ref[
            [
                "trunc_seed",
                "k",
                "_track6_row_id",
                "artist_key",
                "qavg_lgbres_s05_cap010_pred_log",
            ]
        ],
        on=["trunc_seed", "k", "_track6_row_id", "artist_key"],
        how="inner",
        validate="one_to_one",
    )
    merged["abs_log_diff"] = np.abs(
        merged["bundle_pred_log"].to_numpy(dtype=float)
        - merged["qavg_lgbres_s05_cap010_pred_log"].to_numpy(dtype=float)
    )
    passed = bool(len(merged) == len(ref) and float(merged["abs_log_diff"].max()) <= 1e-10)
    summary = {
        "experiment_id": "PP-WLITE-Q5",
        "check": "bundle_replay_parity_vs_PP_WLITE_Q3_q2",
        "n_reference": int(len(ref)),
        "n_replayed": int(len(replay)),
        "n_merged": int(len(merged)),
        "max_abs_log_diff": float(merged["abs_log_diff"].max()),
        "mean_abs_log_diff": float(merged["abs_log_diff"].mean()),
        "passed": passed,
        "reference_column": "qavg_lgbres_s05_cap010_pred_log",
        "bundle": "models/track6/warm_lite_quantile_residual_v0.1",
    }
    merged.to_csv(OUT / "outputs" / "bundle_replay_parity_rows.csv", index=False)
    (OUT / "artifacts" / "bundle_replay_parity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-WLITE-Q5 bundle replay parity",
            "",
            f"- Passed: `{passed}`",
            f"- Rows: `{summary['n_merged']}` / reference `{summary['n_reference']}`",
            f"- Max abs log diff: `{summary['max_abs_log_diff']:.12g}`",
            f"- Mean abs log diff: `{summary['mean_abs_log_diff']:.12g}`",
            "",
        ]
    )
    (OUT / "reports" / "bundle_replay_parity_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
