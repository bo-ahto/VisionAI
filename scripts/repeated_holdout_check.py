"""코덱스 1순위 — Repeated artist-level holdout 재현성 검증.

목적: tune_fairness_check.py 의 single split 결과 (CB+v4 cold-start Artsy -2.95
        / XGB+v4 +3.89) 의 재현성 확인.

프로토콜:
- 3개 seed: 42, 123, 7777
- 각 seed 마다 GroupShuffleSplit 80/20 (artist-level)
- 4 conditions: CB-32, CB-33, XGB-32, XGB-33
- Optuna 15 trials inner 5-fold (fairness check 보다 trial 수 25% 감축 — 시간 단축)
- 최종 비교: 80% 학습 → 20% holdout MdAPE 평균 ± std

Usage: PYTHONPATH=src python3 scripts/repeated_holdout_check.py
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

SEEDS = [42, 123, 7777]
N_TRIALS = 15  # 시간 단축 (fairness check 의 20에서 감축)


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


def load_data():
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


def metrics_holdout(y_te_log, pred_log, source_te):
    y_p = np.exp(y_te_log)
    p_p = np.exp(pred_log)
    out = {}
    for src in ["overall", "artsy", "saatchi"]:
        m = (source_te == src) if src != "overall" else np.ones(len(y_p), dtype=bool)
        if m.sum():
            ape = np.abs(y_p[m] - p_p[m]) / np.abs(y_p[m])
            out[src] = {
                "n": int(m.sum()),
                "MdAPE": round(float(np.median(ape) * 100), 2),
                "W30": round(float(np.mean(ape <= 0.30) * 100), 2),
            }
    return out


def cb_inner_artsy_mdape(X_tr, y_tr, source_tr, params, cat_features):
    cat_idx = [X_tr.columns.get_loc(c) for c in cat_features if c in X_tr.columns]
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
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


def xgb_inner_artsy_mdape(X_tr, y_tr, source_tr, params, cat_features):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
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


def tune_cb(X_tr, y_tr, source_tr, X_te, y_te, source_te, cat_features, label, n_trials, seed_offset=0):
    t0 = time.time()
    def obj(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 500, 2000, step=250),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "depth": trial.suggest_int("depth", 4, 9),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "loss_function": "RMSE",
        }
        return cb_inner_artsy_mdape(X_tr, y_tr, source_tr, params, cat_features)

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42 + seed_offset))
    study.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    best_params = {**study.best_params, "loss_function": "RMSE"}

    cat_idx = [X_tr.columns.get_loc(c) for c in cat_features if c in X_tr.columns]
    cb = CatBoostRegressor(**best_params, verbose=0, random_seed=42, allow_writing_files=False)
    cb.fit(Pool(X_tr, label=y_tr, cat_features=cat_idx))
    pred = cb.predict(Pool(X_te, cat_features=cat_idx))

    holdout = metrics_holdout(y_te, pred, source_te)
    elapsed = time.time() - t0
    logger.info(f"    {label}: inner_artsy={study.best_value:.2f}, holdout_overall={holdout.get('overall', {}).get('MdAPE')}, time={elapsed:.0f}s")
    return {"best_params": best_params, "inner_artsy_mdape": round(study.best_value, 2), "holdout": holdout, "elapsed_sec": round(elapsed, 1)}


def tune_xgb(X_tr, y_tr, source_tr, X_te, y_te, source_te, cat_features, label, n_trials, seed_offset=0):
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
        return xgb_inner_artsy_mdape(X_tr, y_tr, source_tr, params, cat_features)

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42 + seed_offset))
    study.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    best_params = {**study.best_params, "objective": "reg:squarederror", "verbosity": 0, "seed": 42}

    Xtr_e, Xte_e, _ = label_encode_xgb(X_tr, X_te, categorical_features=cat_features)
    d_tr = xgb.DMatrix(Xtr_e, label=y_tr)
    d_te = xgb.DMatrix(Xte_e, label=y_te)
    m = xgb.train(params=best_params, dtrain=d_tr, num_boost_round=best_params["num_boost_round"])
    pred = m.predict(d_te)

    holdout = metrics_holdout(y_te, pred, source_te)
    elapsed = time.time() - t0
    logger.info(f"    {label}: inner_artsy={study.best_value:.2f}, holdout_overall={holdout.get('overall', {}).get('MdAPE')}, time={elapsed:.0f}s")
    return {"best_params": best_params, "inner_artsy_mdape": round(study.best_value, 2), "holdout": holdout, "elapsed_sec": round(elapsed, 1)}


def run_one_seed(df_full, seed):
    logger.info(f"\n{'=' * 60}")
    logger.info(f"SEED {seed}")
    logger.info('=' * 60)

    feats_v4 = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats_v4 = CAT_FEATURES + ["gallery_tier_v4"]

    y = df_full["ln_price"].to_numpy()
    groups = df_full["artist_slug"].astype(str).to_numpy()
    source = df_full["source"].astype(str).to_numpy()

    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    train_idx, test_idx = next(gss.split(df_full, y, groups))
    df_tr = df_full.iloc[train_idx].reset_index(drop=True)
    df_te = df_full.iloc[test_idx].reset_index(drop=True)
    src_tr = source[train_idx]
    src_te = source[test_idx]
    y_tr = y[train_idx]
    y_te = y[test_idx]
    logger.info(f"  Train: {len(train_idx)} (artsy {(src_tr=='artsy').sum()} / saatchi {(src_tr=='saatchi').sum()})")
    logger.info(f"  Holdout: {len(test_idx)} (artsy {(src_te=='artsy').sum()} / saatchi {(src_te=='saatchi').sum()})")

    X_tr_32 = prepare_X(df_tr, CB_FEATURES_BASE, CAT_FEATURES)
    X_te_32 = prepare_X(df_te, CB_FEATURES_BASE, CAT_FEATURES)
    X_tr_33 = prepare_X(df_tr, feats_v4, cats_v4)
    X_te_33 = prepare_X(df_te, feats_v4, cats_v4)

    res = {"seed": seed, "split": {
        "train_n": int(len(train_idx)), "holdout_n": int(len(test_idx)),
        "train_artsy_n": int((src_tr=='artsy').sum()), "train_saatchi_n": int((src_tr=='saatchi').sum()),
        "holdout_artsy_n": int((src_te=='artsy').sum()), "holdout_saatchi_n": int((src_te=='saatchi').sum()),
    }}

    logger.info("  --- CatBoost ---")
    res["catboost_32"] = tune_cb(X_tr_32, y_tr, src_tr, X_te_32, y_te, src_te, CAT_FEATURES, "CB-32", N_TRIALS)
    res["catboost_33"] = tune_cb(X_tr_33, y_tr, src_tr, X_te_33, y_te, src_te, cats_v4, "CB-33", N_TRIALS)

    logger.info("  --- XGBoost ---")
    res["xgboost_32"] = tune_xgb(X_tr_32, y_tr, src_tr, X_te_32, y_te, src_te, CAT_FEATURES, "XGB-32", N_TRIALS)
    res["xgboost_33"] = tune_xgb(X_tr_33, y_tr, src_tr, X_te_33, y_te, src_te, cats_v4, "XGB-33", N_TRIALS)

    return res


def main():
    logger.info("=" * 70)
    logger.info(f"Repeated artist-level holdout — seeds {SEEDS}, N_TRIALS={N_TRIALS}")
    logger.info("=" * 70)

    df_full = attach_v4(load_data())

    all_results = {"seeds": SEEDS, "n_trials_per_condition": N_TRIALS, "runs": []}
    for seed in SEEDS:
        r = run_one_seed(df_full, seed)
        all_results["runs"].append(r)
        # Save intermediate
        OUT_DIR.mkdir(exist_ok=True)
        with (OUT_DIR / "repeated_holdout_check.json").open("w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

    # ─── 통계 산출 ─────────
    def aggregate(condition_key, segment="overall", metric="MdAPE"):
        vals = []
        for run in all_results["runs"]:
            v = run[condition_key]["holdout"].get(segment, {}).get(metric)
            if v is not None:
                vals.append(v)
        if not vals:
            return None
        return {"mean": round(float(np.mean(vals)), 2), "std": round(float(np.std(vals, ddof=1)), 2), "min": min(vals), "max": max(vals), "values": vals}

    summary = {}
    for cond in ["catboost_32", "catboost_33", "xgboost_32", "xgboost_33"]:
        summary[cond] = {}
        for seg in ["overall", "artsy", "saatchi"]:
            summary[cond][seg] = aggregate(cond, seg, "MdAPE")

    # Δ (33 - 32) per model, with paired CIs
    deltas = {}
    for model in ["catboost", "xgboost"]:
        deltas[model] = {}
        for seg in ["overall", "artsy", "saatchi"]:
            d_per_seed = []
            for run in all_results["runs"]:
                v32 = run[f"{model}_32"]["holdout"].get(seg, {}).get("MdAPE")
                v33 = run[f"{model}_33"]["holdout"].get(seg, {}).get("MdAPE")
                if v32 is not None and v33 is not None:
                    d_per_seed.append(v33 - v32)
            if d_per_seed:
                deltas[model][seg] = {
                    "mean": round(float(np.mean(d_per_seed)), 2),
                    "std": round(float(np.std(d_per_seed, ddof=1)), 2),
                    "values": [round(v, 2) for v in d_per_seed],
                    "all_negative": all(v < 0 for v in d_per_seed),
                    "all_positive": all(v > 0 for v in d_per_seed),
                }

    all_results["aggregated_summary"] = summary
    all_results["deltas_v4_minus_baseline"] = deltas

    with (OUT_DIR / "repeated_holdout_check.json").open("w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"REPEATED HOLDOUT — {len(SEEDS)} seeds aggregate")
    print("=" * 70)
    for cond in ["catboost_32", "catboost_33", "xgboost_32", "xgboost_33"]:
        print(f"\n[{cond.upper()}]")
        for seg in ["overall", "artsy", "saatchi"]:
            s = summary[cond][seg]
            if s:
                print(f"  {seg:<8s}: MdAPE mean={s['mean']:.2f} ± {s['std']:.2f} (range {s['min']}–{s['max']}), values={s['values']}")

    print("\n" + "=" * 70)
    print("Δ MdAPE (33 - 32) per seed + reproducibility")
    print("=" * 70)
    for model in ["catboost", "xgboost"]:
        print(f"\n[{model.upper()}]")
        for seg in ["overall", "artsy", "saatchi"]:
            d = deltas[model].get(seg)
            if d:
                consistent = "✓ all_neg" if d["all_negative"] else ("✓ all_pos" if d["all_positive"] else "⚠ mixed")
                print(f"  {seg:<8s}: Δ mean={d['mean']:+.2f} ± {d['std']:.2f}, values={d['values']}, {consistent}")

    print(f"\nSaved: {OUT_DIR / 'repeated_holdout_check.json'}")


if __name__ == "__main__":
    main()
