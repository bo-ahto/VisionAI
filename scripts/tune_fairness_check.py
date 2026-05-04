"""검증 5 fairness 재검증 — 코덱스 Q3 권고.

문제: 17.49 → 10.90 결과는 두 가지 bias 동반
1. 32-feature baseline 미튜닝
2. 동일 5-fold 로 탐색+평가 = selection bias

해결 프로토콜 (코덱스 권고):
1. 32와 33 모두 동일 Optuna budget (20 trials)
2. outer CV / 고정 holdout 으로 최종 비교 (selection bias 제거)
3. Report: Artsy warm / Artsy cold / overall / W30

본 스크립트:
- artist-level 80/20 holdout split
- 80% inner 5-fold KFold 로 Optuna (탐색)
- Best params 로 80% 전체 재학습 → 20% holdout 평가 (최종 비교)
- 4 conditions: CB-32, CB-33, XGB-32, XGB-33

Usage: PYTHONPATH=src python3 scripts/tune_fairness_check.py
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupShuffleSplit, KFold

from visionai.price_engine._eval_helpers import label_encode_xgb
from visionai.price_engine.api.primary_predictor import CAT_FEATURES, CB_FEATURES_BASE

optuna.logging.set_verbosity(optuna.logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


def _normalize(s):
    import re
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def attach_v4(df):
    alias_df = pd.read_csv(DATA / "gallery_alias_map.csv")
    alias = {_normalize(r["영문명"]): _normalize(r["한글명"]) for _, r in alias_df.iterrows()}
    v4 = pd.read_csv(DATA / "art_gallery_tier_list_v4.csv").dropna(subset=["명칭"])
    tier_lookup = {_normalize(r["명칭"]): str(r["티어"]).strip() for _, r in v4.iterrows()}

    def lookup(row):
        if row.get("source") == "saatchi":
            return "Tier E"
        n = _normalize(row.get("gallery_name"))
        if not n or n == "Saatchi Art":
            return "Tier E"
        kor = alias.get(n, n)
        return tier_lookup.get(_normalize(kor), "Tier E")

    df = df.copy()
    df["gallery_tier_v4"] = df.apply(lookup, axis=1)
    return df


def load_data_full():
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")
    if "source" not in artsy.columns:
        artsy["source"] = "artsy"
    if "source" not in saatchi.columns:
        saatchi["source"] = "saatchi"
    for col in ("ho_price_level", "medium_price_level", "profile_completeness", "ln_area"):
        for d in (artsy, saatchi):
            if col not in d.columns:
                if col == "ln_area":
                    d[col] = np.log(d["area_cm2"].clip(lower=1))
                else:
                    d[col] = 0.0
    for d in (artsy, saatchi):
        if "has_birth_year" not in d.columns:
            d["has_birth_year"] = d["artist_birth_year"].notna().astype(int)
        if "support_factor" not in d.columns:
            from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
            d["support_factor"] = d["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
        if "ho_x_support" not in d.columns:
            d["ho_x_support"] = d["ho"] * d["support_factor"]
    common = [c for c in artsy.columns if c in saatchi.columns]
    df = pd.concat([artsy[common], saatchi[common]], ignore_index=True)
    return df[df["is_excluded_for_training"] == 0].copy()


def prepare_X(df, features, cat_features):
    X = df[features].copy()
    for col in cat_features:
        if col in X.columns:
            X[col] = X[col].astype(str).fillna("unknown").replace(
                {"nan": "unknown", "None": "unknown", "": "unknown"}
            )
    for col in features:
        if col not in cat_features:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)
    return X


def metrics(y_true_log, oof_log, source, mask_subset=None):
    y_p = np.exp(y_true_log)
    p_p = np.exp(oof_log)
    out = {}
    if mask_subset is None:
        m = np.ones(len(y_p), dtype=bool)
    else:
        m = mask_subset
    if m.sum() > 0:
        ape = np.abs(y_p[m] - p_p[m]) / np.abs(y_p[m])
        out["overall"] = {
            "n": int(m.sum()),
            "MdAPE": round(float(np.median(ape) * 100), 2),
            "W30": round(float(np.mean(ape <= 0.30) * 100), 2),
        }
        for src in ["artsy", "saatchi"]:
            sm = m & (source == src)
            if sm.sum():
                ape = np.abs(y_p[sm] - p_p[sm]) / np.abs(y_p[sm])
                out[src] = {
                    "n": int(sm.sum()),
                    "MdAPE": round(float(np.median(ape) * 100), 2),
                    "W30": round(float(np.mean(ape <= 0.30) * 100), 2),
                }
    return out


def cb_inner_cv_mdape(X_tr, y_tr, source_tr, params, cat_features, n_splits=5):
    """Inner KFold OOF MdAPE on training subset (Optuna objective)."""
    cat_idx = [X_tr.columns.get_loc(c) for c in cat_features if c in X_tr.columns]
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof = np.zeros(len(y_tr))
    for tr, te in kf.split(X_tr):
        cb = CatBoostRegressor(**params, verbose=0, random_seed=42, allow_writing_files=False)
        cb.fit(Pool(X_tr.iloc[tr], label=y_tr[tr], cat_features=cat_idx))
        oof[te] = cb.predict(Pool(X_tr.iloc[te], cat_features=cat_idx))
    y_p = np.exp(y_tr)
    p_p = np.exp(oof)
    artsy_m = source_tr == "artsy"
    if artsy_m.sum() == 0:
        return float("inf")
    return float(np.median(np.abs(y_p[artsy_m] - p_p[artsy_m]) / np.abs(y_p[artsy_m])) * 100)


def xgb_inner_cv_mdape(X_tr, y_tr, source_tr, params, cat_features, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof = np.zeros(len(y_tr))
    for tr, te in kf.split(X_tr):
        Xtr_e, Xte_e, _ = label_encode_xgb(X_tr.iloc[tr], X_tr.iloc[te], categorical_features=cat_features)
        d_tr = xgb.DMatrix(Xtr_e, label=y_tr[tr])
        d_te = xgb.DMatrix(Xte_e, label=y_tr[te])
        m = xgb.train(params=params, dtrain=d_tr, num_boost_round=params.get("num_boost_round", 1000))
        oof[te] = m.predict(d_te)
    y_p = np.exp(y_tr)
    p_p = np.exp(oof)
    artsy_m = source_tr == "artsy"
    if artsy_m.sum() == 0:
        return float("inf")
    return float(np.median(np.abs(y_p[artsy_m] - p_p[artsy_m]) / np.abs(y_p[artsy_m])) * 100)


def tune_and_eval_catboost(X_tr, y_tr, source_tr, X_te, y_te, source_te, cat_features, label, n_trials=20):
    logger.info(f"  [CatBoost] {label} Optuna {n_trials} trials...")
    t0 = time.time()

    def obj(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 500, 2000, step=250),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "depth": trial.suggest_int("depth", 4, 9),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "loss_function": "RMSE",
        }
        return cb_inner_cv_mdape(X_tr, y_tr, source_tr, params, cat_features)

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    best_params = {**study.best_params, "loss_function": "RMSE"}
    inner_best = study.best_value

    # Final retrain on full train + holdout eval
    cat_idx = [X_tr.columns.get_loc(c) for c in cat_features if c in X_tr.columns]
    cb = CatBoostRegressor(**best_params, verbose=0, random_seed=42, allow_writing_files=False)
    cb.fit(Pool(X_tr, label=y_tr, cat_features=cat_idx))
    pred = cb.predict(Pool(X_te, cat_features=cat_idx))

    holdout_metrics = metrics(y_te, pred, source_te)
    elapsed = time.time() - t0
    logger.info(f"    inner Artsy MdAPE: {inner_best:.2f}, holdout overall MdAPE: {holdout_metrics.get('overall', {}).get('MdAPE')}, time: {elapsed:.0f}s")
    return {
        "best_params": best_params,
        "inner_artsy_mdape": round(inner_best, 2),
        "holdout": holdout_metrics,
        "elapsed_sec": round(elapsed, 1),
    }


def tune_and_eval_xgboost(X_tr, y_tr, source_tr, X_te, y_te, source_te, cat_features, label, n_trials=20):
    logger.info(f"  [XGBoost] {label} Optuna {n_trials} trials...")
    t0 = time.time()

    def obj(trial):
        params = {
            "objective": "reg:squarederror",
            "eta": trial.suggest_float("eta", 0.02, 0.15, log=True),
            "max_depth": trial.suggest_int("max_depth", 4, 9),
            "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 10.0),
            "subsample": trial.suggest_float("subsample", 0.7, 1.0),
            "verbosity": 0, "seed": 42,
            "num_boost_round": trial.suggest_int("num_boost_round", 500, 2000, step=250),
        }
        return xgb_inner_cv_mdape(X_tr, y_tr, source_tr, params, cat_features)

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    best_params = {**study.best_params, "objective": "reg:squarederror", "verbosity": 0, "seed": 42}
    inner_best = study.best_value

    Xtr_e, Xte_e, _ = label_encode_xgb(X_tr, X_te, categorical_features=cat_features)
    d_tr = xgb.DMatrix(Xtr_e, label=y_tr)
    d_te = xgb.DMatrix(Xte_e, label=y_te)
    m = xgb.train(params=best_params, dtrain=d_tr, num_boost_round=best_params["num_boost_round"])
    pred = m.predict(d_te)

    holdout_metrics = metrics(y_te, pred, source_te)
    elapsed = time.time() - t0
    logger.info(f"    inner Artsy MdAPE: {inner_best:.2f}, holdout overall MdAPE: {holdout_metrics.get('overall', {}).get('MdAPE')}, time: {elapsed:.0f}s")
    return {
        "best_params": best_params,
        "inner_artsy_mdape": round(inner_best, 2),
        "holdout": holdout_metrics,
        "elapsed_sec": round(elapsed, 1),
    }


def main():
    logger.info("=" * 70)
    logger.info("튜닝 fairness 재검증 — 32 vs 33 budget-matched + holdout split")
    logger.info("=" * 70)

    df = attach_v4(load_data_full())
    feats_v4 = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats_v4 = CAT_FEATURES + ["gallery_tier_v4"]

    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    source = df["source"].astype(str).to_numpy()

    # Artist-level 80/20 holdout split (no leakage)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(gss.split(df, y, groups))
    logger.info(f"Train: {len(train_idx)} (artists {pd.Series(groups[train_idx]).nunique()}) / Holdout: {len(test_idx)} (artists {pd.Series(groups[test_idx]).nunique()})")
    logger.info(f"Train Artsy/Saatchi: {(source[train_idx]=='artsy').sum()}/{(source[train_idx]=='saatchi').sum()}")
    logger.info(f"Holdout Artsy/Saatchi: {(source[test_idx]=='artsy').sum()}/{(source[test_idx]=='saatchi').sum()}")

    df_tr = df.iloc[train_idx].reset_index(drop=True)
    df_te = df.iloc[test_idx].reset_index(drop=True)
    src_tr = source[train_idx]
    src_te = source[test_idx]
    y_tr = y[train_idx]
    y_te = y[test_idx]

    X_tr_32 = prepare_X(df_tr, CB_FEATURES_BASE, CAT_FEATURES)
    X_te_32 = prepare_X(df_te, CB_FEATURES_BASE, CAT_FEATURES)
    X_tr_33 = prepare_X(df_tr, feats_v4, cats_v4)
    X_te_33 = prepare_X(df_te, feats_v4, cats_v4)

    result = {"split_info": {
        "train_n": int(len(train_idx)),
        "holdout_n": int(len(test_idx)),
        "train_artsy_n": int((src_tr == "artsy").sum()),
        "train_saatchi_n": int((src_tr == "saatchi").sum()),
        "holdout_artsy_n": int((src_te == "artsy").sum()),
        "holdout_saatchi_n": int((src_te == "saatchi").sum()),
    }}

    logger.info("\n=== CatBoost ===")
    result["catboost_32"] = tune_and_eval_catboost(X_tr_32, y_tr, src_tr, X_te_32, y_te, src_te, CAT_FEATURES, "32 features")
    result["catboost_33"] = tune_and_eval_catboost(X_tr_33, y_tr, src_tr, X_te_33, y_te, src_te, cats_v4, "33 features (+v4)")

    logger.info("\n=== XGBoost ===")
    result["xgboost_32"] = tune_and_eval_xgboost(X_tr_32, y_tr, src_tr, X_te_32, y_te, src_te, CAT_FEATURES, "32 features")
    result["xgboost_33"] = tune_and_eval_xgboost(X_tr_33, y_tr, src_tr, X_te_33, y_te, src_te, cats_v4, "33 features (+v4)")

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / "tune_fairness_check.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("FAIRNESS 재검증 — Holdout MdAPE (Artist-level 80/20 split)")
    print("=" * 70)
    for model in ["catboost", "xgboost"]:
        for feats in ["32", "33"]:
            key = f"{model}_{feats}"
            r = result[key]
            print(f"\n[{model.upper()} {feats} features]")
            print(f"  Inner Artsy CV MdAPE (Optuna best): {r['inner_artsy_mdape']}")
            for src in ["overall", "artsy", "saatchi"]:
                if src in r["holdout"]:
                    print(f"  Holdout {src:<8s}: MdAPE {r['holdout'][src]['MdAPE']}, W30 {r['holdout'][src]['W30']}, n={r['holdout'][src]['n']}")
            print(f"  Best params: {r['best_params']}")

    print("\n" + "=" * 70)
    print("Δ (33 - 32) on Holdout")
    print("=" * 70)
    for model in ["catboost", "xgboost"]:
        r32, r33 = result[f"{model}_32"], result[f"{model}_33"]
        print(f"\n[{model.upper()}]")
        for src in ["overall", "artsy", "saatchi"]:
            if src in r32["holdout"] and src in r33["holdout"]:
                d_mdape = r33["holdout"][src]["MdAPE"] - r32["holdout"][src]["MdAPE"]
                d_w30 = r33["holdout"][src]["W30"] - r32["holdout"][src]["W30"]
                sign = "↓" if d_mdape < 0 else "↑"
                print(f"  {src:<8s}: MdAPE Δ{d_mdape:+.2f}, W30 Δ{d_w30:+.2f}")

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
