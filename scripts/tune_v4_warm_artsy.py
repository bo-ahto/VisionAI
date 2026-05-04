"""검증 5: 하이퍼파라미터 재튜닝 — warm Artsy +0.50 regression 해소 시도.

코덱스 자문 §B (Q1): "재튜닝은 가능성은 있지만 우선순위는 낮다 — 변화폭이 구조적 원인"
하지만 보수적 검증 차원에서 limited Optuna 진행 (20 trials × 5-fold).

비교:
- baseline (32 features) — 현재 하이퍼 (1000 iter, lr 0.05, depth 6)
- v4 (33 features) — Optuna로 튜닝
- 동일 metric (warm KFold Artsy MdAPE) 로 비교

Usage: PYTHONPATH=src python3 scripts/tune_v4_warm_artsy.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import KFold

from visionai.price_engine.api.primary_predictor import CAT_FEATURES, CB_FEATURES_BASE

logging.basicConfig(level=logging.WARNING)
optuna.logging.set_verbosity(optuna.logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

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
        for df in (artsy, saatchi):
            if col not in df.columns:
                if col == "ln_area":
                    df[col] = np.log(df["area_cm2"].clip(lower=1))
                else:
                    df[col] = 0.0
    for df in (artsy, saatchi):
        if "has_birth_year" not in df.columns:
            df["has_birth_year"] = df["artist_birth_year"].notna().astype(int)
        if "support_factor" not in df.columns:
            from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
            df["support_factor"] = df["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
        if "ho_x_support" not in df.columns:
            df["ho_x_support"] = df["ho"] * df["support_factor"]
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


def cv_artsy_warm_mdape(X, y, source, params):
    """warm KFold OOF Artsy MdAPE — 튜닝 objective."""
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES + ["gallery_tier_v4"] if c in X.columns]
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    oof = np.zeros(len(y))
    for tr, te in kf.split(X):
        cb = CatBoostRegressor(**params, verbose=0, random_seed=42, allow_writing_files=False)
        cb.fit(Pool(X.iloc[tr], label=y[tr], cat_features=cat_idx))
        oof[te] = cb.predict(Pool(X.iloc[te], cat_features=cat_idx))
    y_p = np.exp(y)
    p_p = np.exp(oof)
    artsy_m = source == "artsy"
    mdape_artsy = float(np.median(np.abs(y_p[artsy_m] - p_p[artsy_m]) / np.abs(y_p[artsy_m])) * 100)
    mdape_overall = float(np.median(np.abs(y_p - p_p) / np.abs(y_p)) * 100)
    return mdape_artsy, mdape_overall


def main():
    logger.info("=" * 60)
    logger.info("검증 5: 하이퍼파라미터 재튜닝 (warm Artsy regression)")
    logger.info("=" * 60)

    df = attach_v4(load_data_full())
    feats = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats = CAT_FEATURES + ["gallery_tier_v4"]
    X = prepare_X(df, feats, cats)
    y = df["ln_price"].to_numpy()
    source = df["source"].astype(str).to_numpy()

    # Baseline (현재 하이퍼) — 33 features
    logger.info("Baseline 측정 (33 features, 현재 하이퍼)...")
    base_params = {"iterations": 1000, "learning_rate": 0.05, "depth": 6, "loss_function": "RMSE"}
    base_artsy_mdape, base_overall = cv_artsy_warm_mdape(X, y, source, base_params)
    logger.info(f"  Baseline (current hyperparams): Artsy MdAPE {base_artsy_mdape:.3f}, Overall {base_overall:.3f}")

    def objective(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 500, 2000, step=250),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "depth": trial.suggest_int("depth", 4, 9),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "loss_function": "RMSE",
        }
        artsy_mdape, _ = cv_artsy_warm_mdape(X, y, source, params)
        return artsy_mdape

    logger.info("Optuna 20 trials 시작 (warm Artsy MdAPE 최소화)...")
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=20, show_progress_bar=False)

    best_artsy_mdape = study.best_value
    best_params = study.best_params
    logger.info(f"  Best Artsy MdAPE: {best_artsy_mdape:.3f}")
    logger.info(f"  Best params: {best_params}")

    # Best 하이퍼로 overall 다시 측정
    final_params = {**best_params, "loss_function": "RMSE"}
    final_artsy_mdape, final_overall = cv_artsy_warm_mdape(X, y, source, final_params)

    result = {
        "baseline_33features_current_hyperparams": {
            "artsy_warm_mdape": round(base_artsy_mdape, 2),
            "overall_warm_mdape": round(base_overall, 2),
            "params": base_params,
        },
        "tuned_33features": {
            "artsy_warm_mdape": round(final_artsy_mdape, 2),
            "overall_warm_mdape": round(final_overall, 2),
            "params": final_params,
            "delta_artsy_vs_baseline": round(final_artsy_mdape - base_artsy_mdape, 2),
            "n_trials": 20,
        },
        "context": {
            "previous_baseline_32features_warm_artsy_mdape": 16.99,
            "previous_v4_33features_default_hyperparams_warm_artsy_mdape": 17.49,
            "regression_to_resolve": 0.50,
        },
        "interpretation": (
            "튜닝으로 v4 33-feature warm Artsy regression 해소 가능 여부 검증. "
            "Baseline (33 features 현재 하이퍼) 부터 측정 후, Optuna 20 trials 로 비교. "
            "구조적 원인 (source proxy) 이면 튜닝으로 해소 안 됨. 단순 sub-optimal 이면 해소 가능."
        ),
    }

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / "tune_v4_warm_artsy.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("재튜닝 결과")
    print("=" * 60)
    print(f"이전 32-feature baseline:  Artsy warm MdAPE = 16.99 (이번 검증 비교 기준)")
    print(f"33-feature current hyper:  Artsy warm MdAPE = {base_artsy_mdape:.2f}")
    print(f"33-feature tuned (best):   Artsy warm MdAPE = {final_artsy_mdape:.2f}")
    print(f"Δ regression resolved:     {16.99 - final_artsy_mdape:+.2f} (음수 → 해소, 양수 → 잔존)")
    print(f"\nBest params: {best_params}")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
