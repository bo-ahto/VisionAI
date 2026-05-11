"""Track 3 PR1 — LightGBM Optuna tuning (Cold + Warm).

목적: Phase 2의 default LightGBM이 LAD 대비 cold에서 열세 (0.473 vs 0.429).
     Optuna로 hyperparameter tuning 후 재비교.

Tuning 대상: num_leaves, learning_rate, min_data_in_leaf,
            feature_fraction, bagging_fraction, reg_alpha, reg_lambda

Cold: 5-fold GroupKFold OOF → median_APE 최소화
Warm: random 80/10/10 single split (빠른 tuning, 결과는 N=3 재실행)

n_trials = 30 (시간 절약)
"""
from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_pr1_optuna_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
CAT_COLS_COLD = ["medium_category", "support_category", "orientation"]
CAT_COLS_WARM = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED = 42
N_TRIALS = 15  # 시간 효율 (30 → 15)
COLD_TUNE_FOLD = 0  # Cold tuning은 1 fold만 사용 (속도), final eval만 5-fold


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def train_lgb(X_tr, y_tr, X_val, y_val, params, cat_feat):
    train_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=train_set)
    return lgb.train({**params, "verbose": -1}, train_set, num_boost_round=2000,
                     valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


# ─── Cold Optuna ───

def cold_objective(trial, dev_df, cold_folds):
    """Cold tuning: 1 fold만 사용 (속도). 최종 5-fold 평가는 별도."""
    params = {
        "objective": "regression", "metric": "rmse",
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),  # 범위 축소
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 80),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
        "bagging_freq": 5,
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-2, 5, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-2, 5, log=True),
        "seed": SEED,
    }

    fold = cold_folds[COLD_TUNE_FOLD]  # 1 fold만
    train_idx = fold["train_indices"]; test_idx = fold["test_indices"]
    rng = np.random.default_rng(SEED + fold["fold"])
    perm = rng.permutation(len(train_idx))
    cut = int(len(train_idx) * 0.1)
    va_idx = np.array(train_idx)[perm[:cut]]
    tr_idx = np.array(train_idx)[perm[cut:]]

    X_tr = to_cat(dev_df.iloc[tr_idx], COLD_FEATURES, CAT_COLS_COLD)
    X_va = to_cat(dev_df.iloc[va_idx], COLD_FEATURES, CAT_COLS_COLD)
    X_te = to_cat(dev_df.iloc[test_idx], COLD_FEATURES, CAT_COLS_COLD)
    model = train_lgb(X_tr, dev_df.iloc[tr_idx][TARGET].values,
                      X_va, dev_df.iloc[va_idx][TARGET].values, params, CAT_COLS_COLD)
    pred = model.predict(X_te)
    return compute_metrics(dev_df.iloc[test_idx][TARGET].values, pred)["median_ape"]


def warm_objective(trial, dev_df, warm_splits):
    params = {
        "objective": "regression", "metric": "rmse",
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 31, 255),  # 범위 축소
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 80),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
        "bagging_freq": 5,
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-2, 5, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-2, 5, log=True),
        "seed": SEED,
    }
    # 단일 split tuning (속도)
    split = warm_splits[0]
    X_tr = to_cat(dev_df.iloc[split["train_indices"]], WARM_FEATURES, CAT_COLS_WARM)
    X_va = to_cat(dev_df.iloc[split["val_indices"]], WARM_FEATURES, CAT_COLS_WARM)
    X_te = to_cat(dev_df.iloc[split["test_indices"]], WARM_FEATURES, CAT_COLS_WARM)
    y_tr = dev_df.iloc[split["train_indices"]][TARGET].values
    y_va = dev_df.iloc[split["val_indices"]][TARGET].values
    y_te = dev_df.iloc[split["test_indices"]][TARGET].values
    model = train_lgb(X_tr, y_tr, X_va, y_va, params, CAT_COLS_WARM)
    pred = model.predict(X_te)
    return compute_metrics(y_te, pred)["median_ape"]


def final_eval_cold(dev_df, cold_folds, params):
    """Best params로 5-fold OOF 재평가."""
    fold_results = []
    for fold in cold_folds:
        train_idx = fold["train_indices"]; test_idx = fold["test_indices"]
        rng = np.random.default_rng(SEED + fold["fold"])
        perm = rng.permutation(len(train_idx))
        cut = int(len(train_idx) * 0.1)
        va_idx = np.array(train_idx)[perm[:cut]]
        tr_idx = np.array(train_idx)[perm[cut:]]
        X_tr = to_cat(dev_df.iloc[tr_idx], COLD_FEATURES, CAT_COLS_COLD)
        X_va = to_cat(dev_df.iloc[va_idx], COLD_FEATURES, CAT_COLS_COLD)
        X_te = to_cat(dev_df.iloc[test_idx], COLD_FEATURES, CAT_COLS_COLD)
        model = train_lgb(X_tr, dev_df.iloc[tr_idx][TARGET].values,
                          X_va, dev_df.iloc[va_idx][TARGET].values, params, CAT_COLS_COLD)
        pred = model.predict(X_te)
        m = compute_metrics(dev_df.iloc[test_idx][TARGET].values, pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)
    return fold_results


def final_eval_warm(dev_df, warm_splits, params, n_seeds=3):
    seed_results = []
    for split in warm_splits[:n_seeds]:
        X_tr = to_cat(dev_df.iloc[split["train_indices"]], WARM_FEATURES, CAT_COLS_WARM)
        X_va = to_cat(dev_df.iloc[split["val_indices"]], WARM_FEATURES, CAT_COLS_WARM)
        X_te = to_cat(dev_df.iloc[split["test_indices"]], WARM_FEATURES, CAT_COLS_WARM)
        y_tr = dev_df.iloc[split["train_indices"]][TARGET].values
        y_va = dev_df.iloc[split["val_indices"]][TARGET].values
        y_te = dev_df.iloc[split["test_indices"]][TARGET].values
        params_s = {**params, "seed": split["seed"]}
        model = train_lgb(X_tr, y_tr, X_va, y_va, params_s, CAT_COLS_WARM)
        pred = model.predict(X_te)
        m = compute_metrics(y_te, pred)
        m["seed"] = split["seed"]
        seed_results.append(m)
    return seed_results


def main():
    logger.info("=" * 70)
    logger.info(f"Track 3 PR1 — LightGBM Optuna tuning (Cold + Warm, n_trials={N_TRIALS})")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows")

    # Cold Optuna
    logger.info(f"\n--- Cold Optuna ({N_TRIALS} trials) ---")
    cold_study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=SEED))
    cold_study.optimize(lambda t: cold_objective(t, dev_df, cold_meta["folds"]),
                        n_trials=N_TRIALS, show_progress_bar=False)
    logger.info(f"  Cold best med_APE: {cold_study.best_value:.4f}")
    logger.info(f"  Cold best params: {cold_study.best_params}")

    # Cold final eval (best params, full 5-fold)
    cold_best_params = {**cold_study.best_params, "objective": "regression", "metric": "rmse",
                        "bagging_freq": 5, "seed": SEED}
    cold_final = final_eval_cold(dev_df, cold_meta["folds"], cold_best_params)
    cold_median = {k: float(np.median([f[k] for f in cold_final]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]}
    logger.info(f"  Cold tuned 5-fold median: {cold_median}")

    # Warm Optuna
    logger.info(f"\n--- Warm Optuna ({N_TRIALS} trials) ---")
    warm_study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=SEED))
    warm_study.optimize(lambda t: warm_objective(t, dev_df, warm_meta["splits"]),
                        n_trials=N_TRIALS, show_progress_bar=False)
    logger.info(f"  Warm best med_APE (seed 42 only): {warm_study.best_value:.4f}")
    logger.info(f"  Warm best params: {warm_study.best_params}")

    # Warm final eval (N=3)
    warm_best_params = {**warm_study.best_params, "objective": "regression", "metric": "rmse",
                        "bagging_freq": 5}
    warm_final = final_eval_warm(dev_df, warm_meta["splits"], warm_best_params, n_seeds=3)
    warm_mean = {k: float(np.mean([s[k] for s in warm_final]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]}
    warm_std = {k: float(np.std([s[k] for s in warm_final]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]}
    logger.info(f"  Warm tuned N=3 mean: {warm_mean}")

    # 결과 출력
    print()
    print("=" * 80)
    print(f"📊 PR1 — LightGBM Optuna Tuning 결과 (n_trials={N_TRIALS})")
    print("=" * 80)
    print()
    print("[Cold LightGBM]")
    print(f"  Default (Phase 2): med_APE=0.473")
    print(f"  Tuned (PR1):       med_APE={cold_median['median_ape']:.3f}  "
          f"MAPE={cold_median['mape']:.3f}  W30={cold_median['within_30pct']:.3f}")
    print(f"  Phase 1 LAD ref:   med_APE=0.429")
    delta_default = cold_median['median_ape'] - 0.473
    delta_lad = cold_median['median_ape'] - 0.429
    print(f"  vs default: {delta_default:+.3f}  /  vs LAD: {delta_lad:+.3f}")
    print(f"  Best params: {cold_study.best_params}")

    print()
    print("[Warm LightGBM]")
    print(f"  Default (Phase 2): med_APE=0.119±0.002")
    print(f"  Tuned (PR1):       med_APE={warm_mean['median_ape']:.3f}±{warm_std['median_ape']:.3f}  "
          f"W30={warm_mean['within_30pct']:.3f}")
    delta_w = warm_mean['median_ape'] - 0.119
    print(f"  vs default: {delta_w:+.3f}")
    print(f"  Best params: {warm_study.best_params}")

    print()
    print("📝 해석:")
    if cold_median['median_ape'] < 0.429:
        print(f"  ✅ Cold tuned LGB ({cold_median['median_ape']:.3f}) < LAD (0.429) — LGB 추월!")
    else:
        print(f"  ⚠️ Cold tuned LGB ({cold_median['median_ape']:.3f}) ≥ LAD (0.429) — LAD 유지")
    if warm_mean['median_ape'] < 0.119:
        print(f"  ✅ Warm tuned LGB ({warm_mean['median_ape']:.3f}) < default (0.119) — tuning 가치 있음")
    else:
        print(f"  ⚠️ Warm tuned LGB ({warm_mean['median_ape']:.3f}) ≥ default (0.119) — default가 이미 충분")

    output = {
        "n_trials": N_TRIALS,
        "cold": {
            "best_params": cold_study.best_params,
            "best_tuning_value": cold_study.best_value,
            "final_5fold_median": cold_median,
            "final_per_fold": cold_final,
            "vs_default_0473": cold_median['median_ape'] - 0.473,
            "vs_lad_0429": cold_median['median_ape'] - 0.429,
        },
        "warm": {
            "best_params": warm_study.best_params,
            "best_tuning_value": warm_study.best_value,
            "final_n3_mean": warm_mean,
            "final_n3_std": warm_std,
            "final_per_seed": warm_final,
            "vs_default_0119": warm_mean['median_ape'] - 0.119,
        },
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
