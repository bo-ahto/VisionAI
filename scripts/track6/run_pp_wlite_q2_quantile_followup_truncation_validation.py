#!/usr/bin/env python3
"""PP-WLITE-Q2: Warm-lite Quantile follow-up truncation validation.

PP-WLITE-Q1에서 개선 신호가 있었던 Warm-lite Quantile 보완 후보를
PP-WCUT6와 같은 k-truncation 구조로 후속 검증한다.

- 학습: full train + Warm-lite min1 작가 사다리 fold-제외 통계
- 기준: 동결된 Warm-lite v0.1 huber_c0..c5 all6 평균
- 후보: LightGBM Quantile q50(full/lean), all6+q50 blend
- 검증: warm fixed-test 607행, 같은 작가 train 이력을 k=1~4로 절단
- 반복: truncation seed 3개, Quantile model seed 3개 평균
- 0604 미사용
"""
from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


warnings.filterwarnings("ignore", message="X does not have valid feature names")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_cgrp_spec = importlib.util.spec_from_file_location(
    "cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py"
)
cgrp = importlib.util.module_from_spec(_cgrp_spec)
_cgrp_spec.loader.exec_module(cgrp)

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)

_cb3_spec = importlib.util.spec_from_file_location(
    "cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py"
)
cb3 = importlib.util.module_from_spec(_cb3_spec)
_cb3_spec.loader.exec_module(cb3)


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WLITE-Q2_quantile_followup_truncation_validation"
WARM_LITE_PREDICTOR = (
    REPO / "models" / "track6" / "warm_lite_v0.1" / "predict" / "predict_warm_lite_v0_1.py"
)
KS = [1, 2, 3, 4]
TRUNC_SEEDS = [20260612, 20260613, 20260614]
MODEL_SEEDS = [20260612, 20260613, 20260614]
N_BOOT = 400
FORCE_RECOMPUTE = True

LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]

FULL_NUM = cb3.NUM_BASE + cgrp.GRP_FULL
LEAN_NUM = cb3.NUM_BASE + cgrp.GRP_LEAN
CAT_COLS = cb3.CAT_C

CANDIDATES = [
    "all6_current",
    "lgbq_full_q50",
    "lgbq_lean_q50",
    "lgbq_full_lean_avg",
    "all6_75_lgbq_full_25",
    "all6_50_lgbq_full_50",
]
QUANTILE_CANDIDATES = [c for c in CANDIDATES if c != "all6_current"]


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


def truncate_train(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep = []
    for artist, idx in train.groupby(train["artist_key"].astype(str)).indices.items():
        if artist in target_artists and len(idx) > k:
            keep.append(rng.choice(idx, size=k, replace=False))
        else:
            keep.append(idx)
    return train.iloc[np.concatenate(keep)].reset_index(drop=True)


def quantile_pipeline(alpha: float, feature_set: str, seed: int) -> Pipeline:
    num_cols = FULL_NUM if feature_set == "full" else LEAN_NUM
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", SimpleImputer(strategy="median"), num_cols),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                    ]
                ),
            ),
            (
                "model",
                LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    n_estimators=420,
                    learning_rate=0.03,
                    num_leaves=31,
                    min_child_samples=20,
                    subsample=0.90,
                    colsample_bytree=0.90,
                    reg_lambda=0.15,
                    random_state=seed,
                    n_jobs=-1,
                    verbose=-1,
                ),
            ),
        ]
    )


def train_quantile_models(train_s: pd.DataFrame, seed: int) -> dict[str, Pipeline]:
    y = train_s["ln_price_krw"].to_numpy(dtype=float)
    models = {
        "full_q10": quantile_pipeline(0.10, "full", seed),
        "full_q50": quantile_pipeline(0.50, "full", seed),
        "full_q90": quantile_pipeline(0.90, "full", seed),
        "lean_q50": quantile_pipeline(0.50, "lean", seed),
    }
    models["full_q10"].fit(train_s[FULL_NUM + CAT_COLS], y)
    models["full_q50"].fit(train_s[FULL_NUM + CAT_COLS], y)
    models["full_q90"].fit(train_s[FULL_NUM + CAT_COLS], y)
    models["lean_q50"].fit(train_s[LEAN_NUM + CAT_COLS], y)
    return models


def add_price_proxy(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["grp_price_proxy"] = out["grp_unit_area_median"] + out["log_area"].clip(lower=0)
    return out


def predict_quantile_seed_average(fs: pd.DataFrame, model_sets: dict[int, dict[str, Pipeline]]) -> pd.DataFrame:
    q10, q50_full, q90, q50_lean = [], [], [], []
    for models in model_sets.values():
        q10.append(np.asarray(models["full_q10"].predict(fs[FULL_NUM + CAT_COLS]), dtype=float))
        q50_full.append(np.asarray(models["full_q50"].predict(fs[FULL_NUM + CAT_COLS]), dtype=float))
        q90.append(np.asarray(models["full_q90"].predict(fs[FULL_NUM + CAT_COLS]), dtype=float))
        q50_lean.append(np.asarray(models["lean_q50"].predict(fs[LEAN_NUM + CAT_COLS]), dtype=float))
    out = pd.DataFrame(index=fs.index)
    out["lgbq_full_q10"] = np.mean(q10, axis=0)
    out["lgbq_full_q50"] = np.mean(q50_full, axis=0)
    out["lgbq_full_q90"] = np.mean(q90, axis=0)
    out["lgbq_lean_q50"] = np.mean(q50_lean, axis=0)
    out["lgbq_width"] = np.maximum(out["lgbq_full_q90"] - out["lgbq_full_q10"], 0.0)
    return out


def predict_condition(
    warm_lite,
    params: dict,
    huber_models: list,
    q_models: dict[int, dict[str, Pipeline]],
    train_k: pd.DataFrame,
    test: pd.DataFrame,
    trunc_seed: int,
    k: int,
) -> pd.DataFrame:
    train_by_artist = {str(artist): group.copy() for artist, group in train_k.groupby("artist_key", sort=False)}
    parts = []
    for artist_key, group in test.groupby(test["artist_key"].astype(str), sort=False):
        artist_history = train_by_artist.get(str(artist_key))
        if artist_history is None or len(artist_history) < 1:
            raise RuntimeError(f"Missing truncated artist history for artist_key={artist_key!r}")
        fs = warm_lite.assign_stats(group.copy(), artist_history, params)
        fs = add_price_proxy(fs)

        out = group[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
        out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
        out.insert(0, "k", k)
        out.insert(0, "trunc_seed", trunc_seed)
        out["artist_history_n"] = int(len(artist_history))

        huber_comp = []
        for model, cols in zip(huber_models, params["huber_num_cols"]):
            huber_comp.append(np.asarray(model.predict(fs[cols + params["huber_cat_cols"]]), dtype=float))
        out["all6_current_pred_log"] = np.mean(huber_comp, axis=0)

        qpred = predict_quantile_seed_average(fs, q_models)
        out["lgbq_full_q10"] = qpred["lgbq_full_q10"].to_numpy(dtype=float)
        out["lgbq_full_q90"] = qpred["lgbq_full_q90"].to_numpy(dtype=float)
        out["lgbq_width"] = qpred["lgbq_width"].to_numpy(dtype=float)
        out["lgbq_full_q50_pred_log"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
        out["lgbq_lean_q50_pred_log"] = qpred["lgbq_lean_q50"].to_numpy(dtype=float)
        out["lgbq_full_lean_avg_pred_log"] = 0.50 * out["lgbq_full_q50_pred_log"] + 0.50 * out["lgbq_lean_q50_pred_log"]
        out["all6_75_lgbq_full_25_pred_log"] = 0.75 * out["all6_current_pred_log"] + 0.25 * out["lgbq_full_q50_pred_log"]
        out["all6_50_lgbq_full_50_pred_log"] = 0.50 * out["all6_current_pred_log"] + 0.50 * out["lgbq_full_q50_pred_log"]
        parts.append(out)
    return pd.concat(parts, ignore_index=True)


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
    overall = pd.DataFrame(overall_rows)
    by_k = pd.DataFrame(by_k_rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        by_k[f"rank_{metric}"] = by_k.groupby("k")[metric].rank(method="min").astype(int)
        overall[f"rank_{metric}"] = overall[metric].rank(method="min").astype(int)
        all6_value = float(overall.loc[overall["candidate"].eq("all6_current"), metric].iloc[0])
        overall[f"delta_{metric}_minus_all6"] = overall[metric] - all6_value
    return by_k.sort_values(["k", "MAPE", "p95_APE"]), overall.sort_values(["MAPE", "p95_APE"])


def bootstrap_rows(preds: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    rows = []
    for (trunc_seed, k), group in preds.groupby(["trunc_seed", "k"], sort=True):
        price = group["actual_price"].to_numpy(dtype=float)
        groups = pd.Series(np.arange(len(group))).groupby(group["artist_key"].astype(str).to_numpy()).apply(list)
        all6 = group["all6_current_pred_log"].to_numpy(dtype=float)
        for candidate in QUANTILE_CANDIDATES:
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
            row = {"trunc_seed": int(trunc_seed), "k": int(k), "candidate": candidate, "n_boot": N_BOOT}
            for metric in wins_candidate:
                row[f"p_candidate_better_all6_{metric}"] = wins_candidate[metric] / N_BOOT
                row[f"p_all6_better_candidate_{metric}"] = wins_all6[metric] / N_BOOT
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "trunc_seed", "candidate"])


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


def width_diagnostics(preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    finite = preds[np.isfinite(preds["lgbq_width"])].copy()
    finite["width_bin"] = pd.qcut(finite["lgbq_width"], q=4, labels=["q1_low", "q2", "q3", "q4_high"], duplicates="drop")
    for width_bin, group in finite.groupby("width_bin", observed=True):
        row = {
            "width_bin": str(width_bin),
            "n": int(len(group)),
            "width_min": float(group["lgbq_width"].min()),
            "width_max": float(group["lgbq_width"].max()),
        }
        for candidate in ("all6_current", "lgbq_full_q50", "all6_50_lgbq_full_50"):
            mt = cb1.mt(group["actual_price"].to_numpy(dtype=float), group[f"{candidate}_pred_log"].to_numpy(dtype=float))
            row[f"{candidate}_MdAPE"] = float(mt["MdAPE"])
            row[f"{candidate}_MAPE"] = float(mt["MAPE"])
            row[f"{candidate}_p95_APE"] = float(mt["p95_APE"])
        rows.append(row)
    return pd.DataFrame(rows)


def table_md(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    view = frame[columns].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    by_k: pd.DataFrame,
    overall: pd.DataFrame,
    boot_sum: pd.DataFrame,
    width_diag: pd.DataFrame,
    config: dict,
) -> None:
    focused = ["all6_current", "lgbq_full_q50", "all6_75_lgbq_full_25", "all6_50_lgbq_full_50"]
    lines = [
        "# PP-WLITE-Q2 Warm-lite Quantile 후속 절단 검증",
        "",
        "## 1. 목적",
        "",
        "PP-WLITE-Q1에서 개선 신호가 있었던 Quantile 보완 후보가 PP-WCUT6와 같은 k-truncation 구조에서도 유지되는지 확인한다.",
        "",
        "## 2. 평가 설계",
        "",
        "- 기준: 동결된 Warm-lite v0.1 Huber all6",
        "- 후보: full train에서 학습한 LightGBM Quantile q50과 all6 blend",
        "- 평가: warm fixed-test 607행에 대해 같은 작가 train 이력을 k=1~4로 절단",
        "- 반복: truncation seed 3개, Quantile model seed 3개 평균",
        "- 주의: Quantile 후보는 아직 운영 번들로 동결하지 않은 follow-up 후보",
        "",
        "## 3. Overall metrics",
        "",
        table_md(
            overall,
            [
                "candidate",
                "n",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "rank_MdAPE",
                "rank_MAPE",
                "rank_p95_APE",
                "delta_MdAPE_minus_all6",
                "delta_MAPE_minus_all6",
                "delta_p95_APE_minus_all6",
            ],
        ),
        "",
        "## 4. Metrics by k",
        "",
        table_md(
            by_k[by_k["candidate"].isin(focused)],
            ["k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"],
        ),
        "",
        "## 5. Bootstrap summary vs all6_current",
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
        "## 6. Quantile width diagnostics",
        "",
        table_md(
            width_diag,
            [
                "width_bin",
                "n",
                "width_min",
                "width_max",
                "all6_current_MdAPE",
                "all6_current_MAPE",
                "all6_current_p95_APE",
                "lgbq_full_q50_MdAPE",
                "lgbq_full_q50_MAPE",
                "lgbq_full_q50_p95_APE",
                "all6_50_lgbq_full_50_MdAPE",
                "all6_50_lgbq_full_50_MAPE",
                "all6_50_lgbq_full_50_p95_APE",
            ],
        ),
        "",
        "## 7. Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    warm_lite = load_warm_lite_module()
    params = warm_lite.load_params()
    huber_models = warm_lite.load_models()

    warm_features = artifact_features()["warm"]
    needed = list(
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
    train, _, test = load_scope("warm", needed)
    train = train[needed].reset_index(drop=True)
    test = test[needed].reset_index(drop=True)
    test_artists = set(test["artist_key"].astype(str))

    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = LITE_LADDER + base_ladder
    train_s = cgrp.train_with_internal_stats(train)
    cgrp.LADDER = base_ladder
    train_s = add_price_proxy(train_s)

    print("[train] quantile model seeds", MODEL_SEEDS, flush=True)
    q_models = {seed: train_quantile_models(train_s, seed) for seed in MODEL_SEEDS}

    parts = []
    for trunc_seed in TRUNC_SEEDS:
        for k in KS:
            checkpoint = EXP / "outputs" / f"preds_trunc{trunc_seed}_k{k}.csv"
            if checkpoint.exists() and not FORCE_RECOMPUTE:
                print(f"[resume] trunc_seed={trunc_seed} k={k}", flush=True)
                parts.append(pd.read_csv(checkpoint))
                continue
            train_k = truncate_train(train, test_artists, trunc_seed, k)
            part = predict_condition(warm_lite, params, huber_models, q_models, train_k, test, trunc_seed, k)
            part.to_csv(checkpoint, index=False)
            print(f"[done] trunc_seed={trunc_seed} k={k}: {len(part)} rows", flush=True)
            parts.append(part)

    preds = pd.concat(parts, ignore_index=True)
    preds.to_csv(EXP / "outputs" / "predictions_all_conditions.csv", index=False)

    by_k, overall = metric_rows(preds)
    boot = bootstrap_rows(preds)
    boot_sum = bootstrap_summary(boot)
    width_diag = width_diagnostics(preds)

    by_k.to_csv(EXP / "outputs" / "candidate_metrics_by_k.csv", index=False)
    overall.to_csv(EXP / "outputs" / "candidate_metrics_overall.csv", index=False)
    boot.to_csv(EXP / "outputs" / "candidate_bootstrap_by_seed_k.csv", index=False)
    boot_sum.to_csv(EXP / "outputs" / "candidate_bootstrap_summary.csv", index=False)
    width_diag.to_csv(EXP / "outputs" / "quantile_width_diagnostics.csv", index=False)

    all6 = overall[overall["candidate"].eq("all6_current")].iloc[0]
    config = {
        "experiment_id": "PP-WLITE-Q2",
        "experiment_slug": EXP.name,
        "eval_design": "PP-WCUT6-equivalent frozen Warm-lite k-truncation follow-up.",
        "model_seeds": MODEL_SEEDS,
        "truncation_seeds": TRUNC_SEEDS,
        "ks": KS,
        "rows_per_condition": int(len(test)),
        "total_rows": int(len(preds)),
        "baseline": "frozen warm_lite_v0.1 all6_current",
        "quantile_model": "LightGBM objective=quantile, q10/q50/q90 full features, q50 lean features, seed-averaged",
        "candidates": CANDIDATES,
        "all6_current_metrics": {metric: float(all6[metric]) for metric in ("MdAPE", "MAPE", "p95_APE")},
        "best_candidate_by_metric": {
            metric: str(overall.sort_values(metric).iloc[0]["candidate"])
            for metric in ("MdAPE", "MAPE", "p95_APE")
        },
        "n_boot": N_BOOT,
        "prohibitions": ["0604 사용 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(by_k, overall, boot_sum, width_diag, config)

    print("[overall]", flush=True)
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
                "delta_MdAPE_minus_all6",
                "delta_MAPE_minus_all6",
                "delta_p95_APE_minus_all6",
            ]
        ].to_string(index=False),
        flush=True,
    )
    print("[bootstrap summary]", flush=True)
    print(boot_sum.round(4).to_string(index=False), flush=True)
    print(json.dumps(config, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
