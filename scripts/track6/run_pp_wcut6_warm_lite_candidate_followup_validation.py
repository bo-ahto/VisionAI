#!/usr/bin/env python3
"""PP-WCUT6: frozen Warm-lite component candidate follow-up validation.

PP-WCUT5 checked the 6-Huber design with retrained Huber models on real
low-history leave-one-out rows. This follow-up checks the operational frozen
Warm-lite v0.1 components directly:

- use the PP-WCUT2 k-truncation setup on the warm fixed-test artists
- keep only k train histories per fixed-test artist
- build the same real-time Warm-lite artist statistics from that truncated
  history
- run frozen huber_c0..huber_c5 separately
- compare all6/current, full4, lean2, and single-component candidates

This isolates whether the current frozen 6-component average is supported by
the operational artifact itself. PP-WCUT2 remains the route-level evidence for
Warm-lite vs Cold; this script is only about component selection.
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
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WCUT6_warm_lite_candidate_followup_validation"
WARM_LITE_PREDICTOR = (
    REPO / "models" / "track6" / "warm_lite_v0.1" / "predict" / "predict_warm_lite_v0_1.py"
)
KS = [1, 2, 3, 4]
TRUNC_SEEDS = [20260612, 20260613, 20260614]
N_BOOT = 400
FORCE_RECOMPUTE = True

COMPONENT_LABELS = {
    "c0": "full_alpha1e-4_eps1.35",
    "c1": "full_alpha1e-3_eps1.35",
    "c2": "full_alpha1e-4_eps1.20",
    "c3": "full_alpha1e-4_eps1.50",
    "c4": "lean_alpha1e-4_eps1.35",
    "c5": "lean_alpha1e-3_eps1.50",
}

CANDIDATES = {
    "all6_current": ["c0", "c1", "c2", "c3", "c4", "c5"],
    "full4_only": ["c0", "c1", "c2", "c3"],
    "lean2_only": ["c4", "c5"],
    "c0_full_default": ["c0"],
    "c1_full_more_regularized": ["c1"],
    "c2_full_low_epsilon": ["c2"],
    "c3_full_high_epsilon": ["c3"],
    "c4_lean_default": ["c4"],
    "c5_lean_regularized_high_epsilon": ["c5"],
}


def load_warm_lite_module():
    spec = importlib.util.spec_from_file_location("warm_lite_v0_1", WARM_LITE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Warm-lite predictor from {WARM_LITE_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def component_metadata(params: dict) -> pd.DataFrame:
    rows = []
    for i, cols in enumerate(params["huber_num_cols"]):
        comp = f"c{i}"
        rows.append(
            {
                "component": comp,
                "label": COMPONENT_LABELS[comp],
                "feature_set": "full" if len(cols) >= 17 else "lean",
                "n_num_cols": len(cols),
                "uses_q25_q75": "grp_log_price_q25" in cols and "grp_log_price_q75" in cols,
                "uses_unit_area_iqr": "grp_unit_area_iqr" in cols,
            }
        )
    return pd.DataFrame(rows)


def truncate_train(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep = []
    for artist, idx in train.groupby(train["artist_key"].astype(str)).indices.items():
        if artist in target_artists and len(idx) > k:
            keep.append(rng.choice(idx, size=k, replace=False))
        else:
            keep.append(idx)
    return train.iloc[np.concatenate(keep)].reset_index(drop=True)


def predict_components_for_condition(
    warm_lite,
    params: dict,
    models: list,
    train_k: pd.DataFrame,
    test: pd.DataFrame,
    seed: int,
    k: int,
) -> pd.DataFrame:
    train_by_artist = {str(artist): group.copy() for artist, group in train_k.groupby("artist_key", sort=False)}
    parts = []
    for artist_key, group in test.groupby(test["artist_key"].astype(str), sort=False):
        artist_history = train_by_artist.get(str(artist_key))
        if artist_history is None or len(artist_history) < 1:
            raise RuntimeError(f"Missing truncated artist history for artist_key={artist_key!r}")
        fs = warm_lite.assign_stats(group.copy(), artist_history, params)

        out = group[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
        out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
        out.insert(0, "k", k)
        out.insert(0, "seed", seed)
        out["artist_history_n"] = int(len(artist_history))
        for i, (model, cols) in enumerate(zip(models, params["huber_num_cols"])):
            out[f"c{i}_pred_log"] = np.asarray(model.predict(fs[cols + params["huber_cat_cols"]]), dtype=float)
        parts.append(out)

    preds = pd.concat(parts, ignore_index=True)
    for candidate, comps in CANDIDATES.items():
        preds[f"{candidate}_pred_log"] = preds[[f"{comp}_pred_log" for comp in comps]].mean(axis=1)
    return preds


def metric_rows(preds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    by_k_rows = []
    overall_rows = []
    for k, group in preds.groupby("k", sort=True):
        price = group["actual_price"].to_numpy(dtype=float)
        for candidate in CANDIDATES:
            mt = cb1.mt(price, group[f"{candidate}_pred_log"].to_numpy(dtype=float))
            by_k_rows.append(
                {
                    "k": int(k),
                    "candidate": candidate,
                    "n": int(len(group)),
                    **{metric: round(float(value), 6) for metric, value in mt.items()},
                }
            )
    price_all = preds["actual_price"].to_numpy(dtype=float)
    for candidate in CANDIDATES:
        mt = cb1.mt(price_all, preds[f"{candidate}_pred_log"].to_numpy(dtype=float))
        overall_rows.append(
            {
                "candidate": candidate,
                "n": int(len(preds)),
                **{metric: round(float(value), 6) for metric, value in mt.items()},
            }
        )

    by_k = pd.DataFrame(by_k_rows)
    overall = pd.DataFrame(overall_rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        by_k[f"rank_{metric}"] = by_k.groupby("k")[metric].rank(method="min").astype(int)
        overall[f"rank_{metric}"] = overall[metric].rank(method="min").astype(int)
        all6_value = float(overall.loc[overall["candidate"].eq("all6_current"), metric].iloc[0])
        overall[f"delta_{metric}_minus_all6"] = overall[metric] - all6_value
    return by_k.sort_values(["k", "MAPE", "p95_APE"]), overall.sort_values(["MAPE", "p95_APE"])


def bootstrap_rows(preds: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    rows = []
    for (seed, k), group in preds.groupby(["seed", "k"], sort=True):
        price = group["actual_price"].to_numpy(dtype=float)
        groups = pd.Series(np.arange(len(group))).groupby(group["artist_key"].astype(str).to_numpy()).apply(list)
        all6 = group["all6_current_pred_log"].to_numpy(dtype=float)
        for candidate in CANDIDATES:
            cand = group[f"{candidate}_pred_log"].to_numpy(dtype=float)
            wins_candidate = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
            wins_all6 = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
            for _ in range(N_BOOT):
                sampled = rng.choice(len(groups), size=len(groups), replace=True)
                idx = np.concatenate([groups.iloc[g] for g in sampled])
                cm = cb1.mt(price[idx], cand[idx])
                bm = cb1.mt(price[idx], all6[idx])
                for metric in wins_candidate:
                    wins_candidate[metric] += cm[metric] < bm[metric]
                    wins_all6[metric] += bm[metric] < cm[metric]
            row = {"seed": int(seed), "k": int(k), "candidate": candidate, "n_boot": N_BOOT}
            for metric in wins_candidate:
                row[f"p_candidate_better_all6_{metric}"] = wins_candidate[metric] / N_BOOT
                row[f"p_all6_better_candidate_{metric}"] = wins_all6[metric] / N_BOOT
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "seed", "candidate"])


def bootstrap_summary(boot: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, group in boot.groupby("candidate", sort=True):
        row = {"candidate": candidate, "conditions": int(len(group))}
        for metric in ("MdAPE", "MAPE", "p95_APE"):
            col = f"p_candidate_better_all6_{metric}"
            row[f"mean_{col}"] = float(group[col].mean())
            row[f"min_{col}"] = float(group[col].min())
            row[f"conditions_{col}_ge_0_90"] = int((group[col] >= 0.90).sum())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("candidate")


def table_md(frame: pd.DataFrame, cols: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    view = frame[cols].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in cols) + " |")
    return "\n".join(lines)


def write_report(meta: pd.DataFrame, by_k: pd.DataFrame, overall: pd.DataFrame, boot_sum: pd.DataFrame, config: dict) -> None:
    focused = ["all6_current", "c2_full_low_epsilon", "full4_only", "c4_lean_default"]
    lines = [
        "# PP-WCUT6 frozen Warm-lite component follow-up validation",
        "",
        "## Purpose",
        "",
        "Check whether the frozen Warm-lite v0.1 6-component average is clearly better than simpler component selections under the PP-WCUT2 k-truncation setup.",
        "",
        "## Component metadata",
        "",
        meta.to_string(index=False),
        "",
        "## Overall metrics",
        "",
        table_md(
            overall[overall["candidate"].isin(focused)],
            ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE", "delta_MAPE_minus_all6"],
        ),
        "",
        "## Metrics by k",
        "",
        table_md(
            by_k[by_k["candidate"].isin(focused)],
            ["k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"],
        ),
        "",
        "## Bootstrap summary vs all6_current",
        "",
        table_md(
            boot_sum[boot_sum["candidate"].isin(focused)],
            [
                "candidate",
                "conditions",
                "mean_p_candidate_better_all6_MdAPE",
                "mean_p_candidate_better_all6_MAPE",
                "mean_p_candidate_better_all6_p95_APE",
                "conditions_p_candidate_better_all6_MdAPE_ge_0_90",
                "conditions_p_candidate_better_all6_MAPE_ge_0_90",
                "conditions_p_candidate_better_all6_p95_APE_ge_0_90",
            ],
        ),
        "",
        "## Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    warm_lite = load_warm_lite_module()
    params = warm_lite.load_params()
    models = warm_lite.load_models()

    warm_features = artifact_features()["warm"]
    needed_features = list(
        dict.fromkeys(
            warm_features
            + warm_lite.REQUIRED
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
    train, _, test = load_scope("warm", needed_features)
    train = train[needed_features].reset_index(drop=True)
    test = test[needed_features].reset_index(drop=True)
    test_artists = set(test["artist_key"].astype(str))

    parts = []
    for seed in TRUNC_SEEDS:
        for k in KS:
            checkpoint = EXP / "outputs" / f"preds_seed{seed}_k{k}.csv"
            if checkpoint.exists() and not FORCE_RECOMPUTE:
                print(f"[resume] seed={seed} k={k} checkpoint found", flush=True)
                parts.append(pd.read_csv(checkpoint))
                continue
            train_k = truncate_train(train, test_artists, seed, k)
            part = predict_components_for_condition(warm_lite, params, models, train_k, test, seed, k)
            part.to_csv(checkpoint, index=False)
            print(f"[done] seed={seed} k={k}: {len(part)} rows", flush=True)
            parts.append(part)

    preds = pd.concat(parts, ignore_index=True)
    preds.to_csv(EXP / "outputs" / "predictions_all_conditions.csv", index=False)

    meta = component_metadata(params)
    by_k, overall = metric_rows(preds)
    boot = bootstrap_rows(preds)
    boot_sum = bootstrap_summary(boot)

    meta.to_csv(EXP / "outputs" / "component_metadata.csv", index=False)
    by_k.to_csv(EXP / "outputs" / "candidate_metrics_by_k.csv", index=False)
    overall.to_csv(EXP / "outputs" / "candidate_metrics_overall.csv", index=False)
    boot.to_csv(EXP / "outputs" / "candidate_bootstrap_by_seed_k.csv", index=False)
    boot_sum.to_csv(EXP / "outputs" / "candidate_bootstrap_summary.csv", index=False)

    all6 = overall[overall["candidate"].eq("all6_current")].iloc[0]
    config = {
        "experiment_id": "PP-WCUT6",
        "eval_design": "Frozen Warm-lite v0.1 component comparison under PP-WCUT2 k-truncation setup.",
        "seeds": TRUNC_SEEDS,
        "ks": KS,
        "rows_per_condition": int(len(test)),
        "total_rows": int(len(preds)),
        "candidates": CANDIDATES,
        "all6_current_metrics": {metric: float(all6[metric]) for metric in ("MdAPE", "MAPE", "p95_APE")},
        "best_candidate_by_metric": {
            metric: str(overall.sort_values(metric).iloc[0]["candidate"])
            for metric in ("MdAPE", "MAPE", "p95_APE")
        },
        "n_boot": N_BOOT,
        "route_level_reference": "PP-WCUT2 remains the Warm-lite-vs-Cold route gate; PP-WCUT6 only validates component selection.",
        "prohibitions": ["0604 사용 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(meta, by_k, overall, boot_sum, config)

    print("[overall]")
    print(
        overall[
            [
                "candidate",
                "n",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "rank_MdAPE",
                "rank_MAPE",
                "rank_p95_APE",
                "delta_MAPE_minus_all6",
            ]
        ].to_string(index=False),
        flush=True,
    )
    print("[bootstrap summary]")
    print(boot_sum.round(4).to_string(index=False), flush=True)
    print(json.dumps(config, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
