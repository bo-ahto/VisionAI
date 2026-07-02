#!/usr/bin/env python3
"""PP-WMIN11: low-history clean WMIN8 direct-test pilot.

This script starts the leakage-free full-WMIN8 comparison requested for 1~4
history artists.  It deliberately does not call frozen PPV8/WMIN8 predictions on
held-out train rows, because those upstream models may have seen the held row.

What this pilot does:
- Reuse the PP-WCUT4 low-history leave-one-out row selection.
- Recompute WMIN8 svc-core(min1 comparable-stat Huber) after removing held rows.
- Recompute the L10 generated-bucket sequential component after removing held
  rows.
- Build a WMIN8-shell candidate from the clean svc-core and clean L10 component.

What remains blocked for a true full-WMIN8 result:
- PPV8's V2 defensive component depends on many upstream Warm component
  predictions.  Those sources must also be retrained against the same held-out
  rows before the result can be called "full WMIN8".
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_l10_warm_l8_feature_variant_experiments as l10  # noqa: E402
import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)  # type: ignore[union-attr]

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WMIN11_lowhistory_full_wmin8_clean_pilot"
WCUT4_OUT = REPO / "experiments" / "track6" / "PP-WCUT4_real_low_history_validation" / "outputs"

ROWS_MIN = 2
ROWS_MAX = 5
DEFAULT_SEED = 20260612
WMIN8_ROUTE_THRESHOLD = 0.2534165869100283
WMIN8_ROUTE_GAP = 0.005


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "logs"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def patch_min1() -> None:
    for group_def in svc1.GROUP_DEFS:
        if "artist_key" in group_def["keys"]:
            group_def["min_n"] = 1


def metric_from_price(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((np.asarray(pred_log, dtype=float) - actual_log) ** 2))),
    }


def select_held_rows(train: pd.DataFrame, seed: int, max_artists_per_k: int | None) -> list[int]:
    rng = np.random.default_rng(seed)
    counts = train.groupby("artist_key").size()
    low_artists = counts[(counts >= ROWS_MIN) & (counts <= ROWS_MAX)].index.to_numpy()
    full_held: list[tuple[Any, int]] = []
    artist_arr = train["artist_key"].to_numpy()
    for artist in low_artists:
        idx = np.where(artist_arr == artist)[0]
        full_held.append((artist, int(rng.choice(idx))))
    if max_artists_per_k is None:
        return [row_idx for _artist, row_idx in full_held]

    selected: list[int] = []
    for total_n in range(ROWS_MIN, ROWS_MAX + 1):
        candidates = [(artist, row_idx) for artist, row_idx in full_held if int(counts.loc[artist]) == total_n]
        if not candidates:
            continue
        order = np.random.default_rng(seed + total_n).permutation(len(candidates))[:max_artists_per_k]
        selected.extend([candidates[int(i)][1] for i in order])
    return selected


def svc_core_predictions(tr_rest: pd.DataFrame, held: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, pd.DataFrame]:
    patch_min1()
    tr_stats = svc1.crossfit_train_stats(tr_rest)
    tr_full = tr_rest.merge(tr_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    held_stats = svc1.apply_comparable_stats(tr_rest, held)
    held_full = held.merge(held_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    out = svc1.fit_predict("huber", tr_full, held_full, held_full, features)
    return out["validation"], held_full


def run_clean_l10(tr_rest: pd.DataFrame, held: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    feature_map = {name: features for name, _strategy, features, _hypothesis in l10.feature_candidates()}
    features = feature_map["full_plus_generated_buckets"]
    rows, preds, _feature_info = l10.run_candidate(
        name="full_plus_generated_buckets",
        strategy="기준 피처셋+생성 bucket",
        features=features,
        hypothesis="PP-WMIN11 clean low-history pilot",
        base_train=tr_rest,
        base_val=held,
        base_test=held,
    )
    pred = pd.concat(preds, ignore_index=True)
    seq = pred[
        pred["candidate"].eq("l8_seq__full_plus_generated_buckets")
        & pred["split"].eq("validation")
    ].copy()
    if len(seq) != len(held):
        raise RuntimeError(f"L10 prediction row mismatch: got {len(seq)} expected {len(held)}")
    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(EXP / "outputs" / "clean_l10_internal_metrics.csv", index=False)
    return seq["pred_log"].to_numpy(dtype=float), seq


def wmin8_shell_route(
    held: pd.DataFrame,
    svc_pred: np.ndarray,
    l10_pred: np.ndarray,
    l10_quantile_width: np.ndarray,
    history_k: np.ndarray,
) -> tuple[np.ndarray, pd.DataFrame]:
    base_w700 = 0.70 * svc_pred + 0.30 * l10_pred
    alt_w850 = 0.85 * svc_pred + 0.15 * l10_pred
    component_spread = np.abs(svc_pred - l10_pred)
    current_vs_stable_gap_abs = np.abs(base_w700 - l10_pred)

    qwidth_score = np.clip((l10_quantile_width - 1.20) / 1.20, 0.0, 1.0)
    spread_score = np.clip(component_spread / 0.18, 0.0, 1.0)
    gap_score = np.clip(current_vs_stable_gap_abs / 0.06, 0.0, 1.0)
    low_conf_score = np.where(history_k <= 1, 1.0, 0.35)
    price_band_score = np.where(base_w700 >= np.nanquantile(base_w700, 0.90), 1.0, 0.0)
    risk_score = (
        0.38 * qwidth_score
        + 0.22 * spread_score
        + 0.14 * gap_score
        + 0.16 * low_conf_score
        + 0.10 * price_band_score
    )
    route_mask = (
        (risk_score >= WMIN8_ROUTE_THRESHOLD)
        & (alt_w850 < base_w700)
        & ((base_w700 - alt_w850) >= WMIN8_ROUTE_GAP)
    )
    routed = np.where(route_mask, alt_w850, base_w700)
    audit = pd.DataFrame(
        {
            "_track6_row_id": held["_track6_row_id"].to_numpy(),
            "history_k": history_k,
            "svc_pred_log": svc_pred,
            "clean_l10_pred_log": l10_pred,
            "l10_quantile_width": l10_quantile_width,
            "base_w700_l10_surrogate_log": base_w700,
            "alt_w850_l10_surrogate_log": alt_w850,
            "risk_score_surrogate": risk_score,
            "route_to_alt": route_mask,
            "routed_l10_surrogate_log": routed,
            "component_prediction_spread_surrogate": component_spread,
            "current_vs_stable_gap_abs_surrogate": current_vs_stable_gap_abs,
        }
    )
    return routed, audit


def summarize(preds: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, group in preds.groupby("candidate", dropna=False):
        for label, part in [("all", group), *[(f"k={k}", g) for k, g in group.groupby("history_k")]]:
            actual_price = part["actual_price"].to_numpy(dtype=float)
            actual_log = part["actual_log"].to_numpy(dtype=float)
            pred_log = part["pred_log"].to_numpy(dtype=float)
            rows.append(
                {
                    "candidate": candidate,
                    "segment": label,
                    "n": int(len(part)),
                    **metric_from_price(actual_price, actual_log, pred_log),
                }
            )
    return pd.DataFrame(rows).sort_values(["segment", "candidate"])


def write_report(summary: pd.DataFrame, config: dict[str, Any]) -> None:
    lines = [
        "# PP-WMIN11 Low-History Clean WMIN8 Pilot",
        "",
        f"- created_at: {config['created_at']}",
        f"- seed: {config['seed']}",
        f"- held_rows: {config['held_rows']}",
        f"- mode: {config['mode']}",
        "",
        "## Status",
        "",
        "- This is a leakage-free pilot for the regeneratable WMIN8 axes.",
        "- It is not yet a true full-WMIN8 result because PPV8/V2 defensive upstream components are not fully regenerated.",
        "- Frozen full-WMIN8 or frozen PPV8 predictions are intentionally not used.",
        "",
        "## Metrics",
        "",
        summary.to_csv(index=False),
        "",
        "## Remaining Full-WMIN8 Blockers",
        "",
        "- Regenerate V2 defensive candidate inputs on the same held-out train.",
        "- Rebuild PPV8 = 0.75 * V2_defensive + 0.25 * L10_generated_bucket_seq with no held-row exposure.",
        "- Recompute exact WMIN8 Huber refit features using the regenerated PPV8 axis.",
        "- Apply the original WMIN8 router using exact feature columns instead of the pilot surrogate risk inputs.",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def add_warm_lite_deltas(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    base = out[out["candidate"].eq("warm_lite_wcut4")][
        ["segment", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(
        columns={
            "MdAPE": "warm_lite_MdAPE",
            "MAPE": "warm_lite_MAPE",
            "p95_APE": "warm_lite_p95_APE",
            "RMSE_log": "warm_lite_RMSE_log",
        }
    )
    out = out.merge(base, on="segment", how="left")
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"delta_{metric}_vs_warm_lite"] = out[metric] - out[f"warm_lite_{metric}"]
    return out


def aggregate_existing_seed_outputs() -> pd.DataFrame | None:
    files = sorted((EXP / "outputs").glob("predictions_seed*.csv"))
    if not files:
        return None
    predictions = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    predictions.to_csv(EXP / "outputs" / "predictions_all_seeds.csv", index=False)
    summary = summarize(predictions.dropna(subset=["pred_log"]))
    summary_with_delta = add_warm_lite_deltas(summary)
    summary_with_delta.to_csv(EXP / "outputs" / "summary_all_seeds.csv", index=False)

    configs = []
    for path in sorted((EXP / "artifacts").glob("run_config_seed*.json")):
        configs.append(json.loads(path.read_text(encoding="utf-8")))
    seeds = sorted({int(x) for x in predictions["seed"].dropna().unique()})
    total_rows = int(
        predictions[["seed", "_track6_row_id"]].drop_duplicates().shape[0]
    )
    lines = [
        "# PP-WMIN11 Low-History Clean WMIN8 Pilot",
        "",
        f"- updated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- seeds: {seeds}",
        f"- unique evaluation rows: {total_rows}",
        "- status: partial clean WMIN8 shell, not true full WMIN8",
        "- frozen full WMIN8 used: false",
        "- frozen PPV8 used: false",
        "",
        "## Combined Metrics",
        "",
        summary_with_delta.to_csv(index=False),
        "",
        "## Interpretation",
        "",
        "- `warm_lite_wcut4` is the existing leakage-free Warm-lite checkpoint from PP-WCUT4.",
        "- `wmin8_clean_svc_core` recomputes the WMIN8 min1 comparable-stat Huber axis after removing held rows.",
        "- `clean_l10_generated_bucket_seq` retrains the L10 generated-bucket sequential axis after removing held rows.",
        "- `wmin8_clean_shell_*_l10_surrogate` replaces PPV8 with the clean L10 axis, so it is a clean shell comparison, not full WMIN8.",
        "",
        "## Remaining Full-WMIN8 Blockers",
        "",
        "- Regenerate V2 defensive candidate inputs on the same held-out train.",
        "- Rebuild exact `PPV8 = 0.75 * V2_defensive + 0.25 * L10_generated_bucket_seq` with no held-row exposure.",
        "- Recompute exact WMIN8 runtime feature set for low-history held rows.",
        "- Apply the original WMIN8 router using exact feature columns instead of the pilot surrogate risk inputs.",
    ]
    if configs:
        lines += ["", "## Seed Runtime Configs", "", json.dumps(configs, ensure_ascii=False, indent=2)]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")
    return summary_with_delta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-artists-per-k", type=int, default=25)
    parser.add_argument("--full-seed", action="store_true", help="use all low-history artists for this seed")
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="rebuild all-seed summary from existing prediction files without retraining",
    )
    args = parser.parse_args()

    start = time.time()
    ensure_dirs()
    if args.aggregate_only:
        combined = aggregate_existing_seed_outputs()
        if combined is None:
            print("No seed prediction files found.")
        else:
            print(combined.to_string(index=False))
        return

    warm_base = artifact_features()["warm"]
    train, _val, _test = load_scope("warm", warm_base)
    train = train.reset_index(drop=True)
    features = svc1.candidate_features(warm_base)["svc_numeric"]

    max_per_k = None if args.full_seed else int(args.max_artists_per_k)
    held_idx = select_held_rows(train, args.seed, max_per_k)
    held = train.iloc[held_idx].reset_index(drop=True)
    tr_rest = train.drop(index=train.index[held_idx]).reset_index(drop=True)
    counts_before_holdout = train.groupby("artist_key").size()
    history_k = held["artist_key"].map(counts_before_holdout - 1).astype(int).to_numpy()

    svc_pred, held_svc = svc_core_predictions(tr_rest, held, features)
    l10_pred, l10_seq = run_clean_l10(tr_rest, held)
    l10_width = l10_seq["quantile_width"].to_numpy(dtype=float)
    routed, route_audit = wmin8_shell_route(held, svc_pred, l10_pred, l10_width, history_k)

    wcut = pd.read_csv(WCUT4_OUT / f"preds_seed{args.seed}.csv")
    wlite = held[["_track6_row_id"]].copy()
    wlite["_row"] = held_idx
    wlite = wlite.merge(wcut[["_row", "wlite_pred_log"]], on="_row", how="left")

    base_cols = {
        "warm_lite_wcut4": wlite["wlite_pred_log"].to_numpy(dtype=float),
        "wmin8_clean_svc_core": svc_pred,
        "clean_l10_generated_bucket_seq": l10_pred,
        "wmin8_clean_shell_w700_l10_surrogate": 0.70 * svc_pred + 0.30 * l10_pred,
        "wmin8_clean_shell_w850_l10_surrogate": 0.85 * svc_pred + 0.15 * l10_pred,
        "wmin8_clean_shell_routed_l10_surrogate": routed,
    }
    pred_parts: list[pd.DataFrame] = []
    for candidate, pred_log in base_cols.items():
        pred_parts.append(
            pd.DataFrame(
                {
                    "seed": args.seed,
                    "_row": held_idx,
                    "_track6_row_id": held["_track6_row_id"].to_numpy(),
                    "artist_key": held["artist_key"].to_numpy(),
                    "history_k": history_k,
                    "candidate": candidate,
                    "actual_log": held["ln_price_krw"].to_numpy(dtype=float),
                    "actual_price": held["price_krw"].to_numpy(dtype=float),
                    "pred_log": pred_log,
                }
            )
        )
    predictions = pd.concat(pred_parts, ignore_index=True)
    predictions.to_csv(EXP / "outputs" / f"predictions_seed{args.seed}.csv", index=False)

    route_audit = route_audit.merge(
        held_svc[["_track6_row_id", "svc_group_level", "svc_coverage_tier", "svc_group_n"]],
        on="_track6_row_id",
        how="left",
    )
    route_audit.to_csv(EXP / "outputs" / f"route_audit_seed{args.seed}.csv", index=False)
    summary = summarize(predictions.dropna(subset=["pred_log"]))
    summary.to_csv(EXP / "outputs" / f"summary_seed{args.seed}.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-WMIN11",
        "seed": int(args.seed),
        "held_rows": int(len(held)),
        "mode": "full_seed" if args.full_seed else f"pilot_max_{max_per_k}_artists_per_total_history_n",
        "train_rows_after_holdout": int(len(tr_rest)),
        "route_threshold": WMIN8_ROUTE_THRESHOLD,
        "route_gap": WMIN8_ROUTE_GAP,
        "status": "partial_clean_wmin8_shell_not_full_wmin8",
        "frozen_full_wmin8_used": False,
        "frozen_ppv8_used": False,
        "clean_components": [
            "warm_lite_wcut4_checkpoint",
            "wmin8_svc_core_min1_recomputed",
            "l10_generated_bucket_seq_retrained",
            "wmin8_w700_w850_shell_with_l10_surrogate",
        ],
        "blocked_full_components": [
            "V2 defensive PPV8 upstream component regeneration",
            "exact PPV8 0.75*V2 + 0.25*L10 regeneration",
            "exact WMIN8 runtime feature set for low-history held rows",
        ],
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / f"run_config_seed{args.seed}.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(summary, config)
    combined = aggregate_existing_seed_outputs()
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print(summary.to_string(index=False))
    if combined is not None:
        print("\n[combined]")
        print(combined.to_string(index=False))


if __name__ == "__main__":
    main()
