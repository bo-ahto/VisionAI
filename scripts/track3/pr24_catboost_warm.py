"""Track 3 PR24 (F3) — CatBoost vs LightGBM Warm 모델 head-to-head.

실험 목적 (track3_experiment_plan_v1.md F3, Codex 1순위 권고):
  Warm 모델에 LightGBM 대신 CatBoost가 더 적합한지 검증.
  Codex 권고 근거: high-cardinality categorical (artist_name_ko ~1,966명)에서
  CatBoost의 ordered target statistics가 더 자연스러울 가능성.

비교 모델:
  LGB (현 운영, Tuned): PR1 v1 Optuna 결과 그대로
  CatBoost (default + 가벼운 hyperparam)

검증 protocol: 5 seeds mini hold-out → 후보 발견 시 release_split confirm (step A)

판정 기준:
  paired median Δ < -0.005 (Warm)
  AND WR > 0.52
  AND 5 seeds 중 4/5 일관 (Δ<0)
  AND Cohen's d < -0.05
  AND tail risk 악화 없음 (max_ape 상대 Δ ≤ 10%)
→ 만족 시 release_split confirm

사용 변수: V0_base (현 운영 feature set) — Warm 모델만 변경
산출물: data/track3_pr24_catboost_results.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_pr24_catboost_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [42, 123, 7, 2024, 999]
N_COLD_MINI = 100
WARM_PER_ARTIST = 1

# V0_base Warm features (LGB 운영 동일)
WARM_FEATS = ["medium_category", "support_category", "orientation",
               "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
               "medium_ho_bucket", "aspect_ratio", "artist_works_log", ARTIST_COL]
WARM_CAT = ["medium_category", "support_category", "orientation",
             "medium_ho_bucket", ARTIST_COL]

# LGB params (운영 v1.2)
LGB_PARAMS_BASE = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
}

# CatBoost params (default + 가벼운 튜닝, LGB와 유사 규모로 보수적)
CATBOOST_PARAMS_BASE = {
    "iterations": 2000,
    "learning_rate": 0.04,
    "depth": 8,
    "l2_leaf_reg": 3.0,
    "loss_function": "RMSE",
    "verbose": False,
    "early_stopping_rounds": 30,
    "thread_count": 1,  # deterministic
}


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns: df[c] = df[c].astype("category")
    return df


def train_lgb(df_train, seed):
    p = {**LGB_PARAMS_BASE,
         "seed": seed, "bagging_seed": seed, "feature_fraction_seed": seed,
         "data_random_seed": seed, "drop_seed": seed, "objective_seed": seed}
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    X_tr = to_cat(df_train.iloc[perm[cut:]], WARM_FEATS, WARM_CAT)
    X_va = to_cat(df_train.iloc[perm[:cut]], WARM_FEATS, WARM_CAT)
    y_tr = df_train.iloc[perm[cut:]][TARGET].values
    y_va = df_train.iloc[perm[:cut]][TARGET].values
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=WARM_CAT)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=WARM_CAT, reference=tr_set)
    return lgb.train(p, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def train_catboost(df_train, seed):
    """CatBoost는 categorical을 native 처리. string으로 두면 자동 인식."""
    p = {**CATBOOST_PARAMS_BASE, "random_seed": seed}
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    X_tr = df_train.iloc[perm[cut:]][WARM_FEATS].copy()
    X_va = df_train.iloc[perm[:cut]][WARM_FEATS].copy()
    y_tr = df_train.iloc[perm[cut:]][TARGET].values
    y_va = df_train.iloc[perm[:cut]][TARGET].values
    # CatBoost는 categorical을 str로 받으면 자동 처리
    for c in WARM_CAT:
        X_tr[c] = X_tr[c].astype(str)
        X_va[c] = X_va[c].astype(str)
    cat_idx = [X_tr.columns.get_loc(c) for c in WARM_CAT]
    model = CatBoostRegressor(**p)
    model.fit(X_tr, y_tr, cat_features=cat_idx, eval_set=(X_va, y_va))
    return model, cat_idx


def predict_lgb(model, df_test):
    X = to_cat(df_test, WARM_FEATS, WARM_CAT)
    return model.predict(X)


def predict_catboost(model, df_test, cat_idx):
    X = df_test[WARM_FEATS].copy()
    for c in WARM_CAT:
        X[c] = X[c].astype(str)
    return model.predict(X)


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
        "p95_ape": float(np.percentile(ape, 95)),
        "p99_ape": float(np.percentile(ape, 99)),
        "max_ape": float(np.max(ape)),
        "ape_array": ape.tolist(),
    }


def paired_stats(ape_b, ape_v):
    ape_b = np.array(ape_b); ape_v = np.array(ape_v)
    delta = ape_v - ape_b
    rng = np.random.default_rng(0)
    boots = [np.mean(rng.choice(delta, size=len(delta), replace=True)) for _ in range(2000)]
    return {
        "n": int(len(delta)),
        "mean_delta": float(np.mean(delta)),
        "median_delta": float(np.median(delta)),
        "win_rate_variant": float((ape_v < ape_b).mean()),
        "ci95_low": float(np.percentile(boots, 2.5)),
        "ci95_high": float(np.percentile(boots, 97.5)),
        "cohen_d": float(np.mean(delta) / np.std(delta, ddof=1)) if np.std(delta, ddof=1) > 0 else 0.0,
        "catastrophic_2x": float((ape_v > 2 * ape_b).mean()),
    }


def setup_mini_holdout(train_df, seed):
    train_df = train_df.sort_values(
        by=[ARTIST_COL, "ln_price_krw_unified", "log_area"], kind="mergesort"
    ).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    counts = train_df.groupby(ARTIST_COL).size().sort_values()
    low = sorted([a for a in counts.index if counts[a] <= 2])
    mid = sorted([a for a in counts.index if 3 <= counts[a] <= 10])
    high = sorted([a for a in counts.index if counts[a] > 10])
    n_low = int(N_COLD_MINI * 0.5); n_mid = int(N_COLD_MINI * 0.3); n_high = N_COLD_MINI - n_low - n_mid
    assert len(low) >= n_low and len(mid) >= n_mid and len(high) >= n_high
    cold_artists = (
        list(rng.choice(low, size=n_low, replace=False)) +
        list(rng.choice(mid, size=n_mid, replace=False)) +
        list(rng.choice(high, size=n_high, replace=False))
    )
    cold_set = set(cold_artists)
    remaining = train_df[~train_df[ARTIST_COL].isin(cold_set)].copy()
    rem_counts = remaining.groupby(ARTIST_COL).size()
    multi = sorted(rem_counts[rem_counts >= 2].index.tolist())
    warm_idx = []
    for a in multi:
        rows = remaining[remaining[ARTIST_COL] == a]
        s = rng.choice(rows.index.values, size=WARM_PER_ARTIST, replace=False)
        warm_idx.extend(s.tolist())
    warm_mini = remaining.loc[warm_idx].copy()
    mini_train = remaining.drop(warm_idx).copy()
    return mini_train, warm_mini


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR24 (F3) — CatBoost vs LightGBM Warm head-to-head")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    seed_results = {}
    for seed in SEEDS:
        logger.info(f"\n=== Seed {seed} ===")
        mini_train, warm_mini = setup_mini_holdout(train, seed)
        logger.info(f"  mini_train {len(mini_train):,} / warm_mini {len(warm_mini):,}")

        counts = mini_train[ARTIST_COL].value_counts().to_dict()
        tr = make_features(mini_train, counts)
        wm = make_features(warm_mini, counts)

        # LGB
        logger.info("  [LGB] 학습")
        lgb_model = train_lgb(tr, seed)
        lgb_pred = predict_lgb(lgb_model, wm)

        # CatBoost
        logger.info("  [CatBoost] 학습")
        cb_model, cat_idx = train_catboost(tr, seed)
        cb_pred = predict_catboost(cb_model, wm, cat_idx)

        y_warm_ln = warm_mini[TARGET].values
        lgb_m = compute_metrics(y_warm_ln, lgb_pred)
        cb_m = compute_metrics(y_warm_ln, cb_pred)
        seed_results[str(seed)] = {"lgb": lgb_m, "catboost": cb_m}
        logger.info(f"  LGB med_APE={lgb_m['median_ape']:.4f} / CatBoost={cb_m['median_ape']:.4f}")

    # ─── 종합 ───
    def agg(model, metric):
        vals = [seed_results[str(s)][model][metric] for s in SEEDS]
        return float(np.mean(vals)), float(np.std(vals))

    # Paired stats — CatBoost vs LGB
    ape_lgb_all = []; ape_cb_all = []
    seed_medians = []; seed_wrs = []; tail_max_rel_deltas = []
    for s in SEEDS:
        lgb_r = seed_results[str(s)]["lgb"]
        cb_r = seed_results[str(s)]["catboost"]
        ape_lgb = np.array(lgb_r["ape_array"])
        ape_cb = np.array(cb_r["ape_array"])
        ape_lgb_all.extend(ape_lgb.tolist())
        ape_cb_all.extend(ape_cb.tolist())
        seed_medians.append(float(np.median(ape_cb - ape_lgb)))
        seed_wrs.append(float((ape_cb < ape_lgb).mean()))
        tail_max_rel_deltas.append((cb_r["max_ape"] - lgb_r["max_ape"]) / max(lgb_r["max_ape"], 0.01))
    paired = paired_stats(ape_lgb_all, ape_cb_all)
    paired["per_seed_median_delta"] = seed_medians
    paired["per_seed_win_rate"] = seed_wrs
    paired["seeds_negative_delta"] = sum(1 for d in seed_medians if d < 0)
    paired["seeds_wr_above_0.5"] = sum(1 for w in seed_wrs if w > 0.5)
    paired["mean_tail_max_rel_delta"] = float(np.mean(tail_max_rel_deltas))

    # 판정
    median_improved = paired["median_delta"] < -0.005
    wr_strong = paired["win_rate_variant"] > 0.52
    seed_consistent = paired["seeds_negative_delta"] >= 4
    cohen_strong = paired["cohen_d"] < -0.05
    tail_ok = paired["mean_tail_max_rel_delta"] <= 0.10
    candidate = median_improved and wr_strong and seed_consistent and cohen_strong and tail_ok

    # ─── 출력 ───
    print()
    print("=" * 70)
    print("📊 F3 — Warm: LGB (현 운영) vs CatBoost (5 seeds 평균)")
    print("=" * 70)
    lgb_m, lgb_s = agg("lgb", "median_ape")
    cb_m, cb_s = agg("catboost", "median_ape")
    print(f"  LGB med_APE     : {lgb_m:.4f} ± {lgb_s:.4f}")
    print(f"  CatBoost med_APE: {cb_m:.4f} ± {cb_s:.4f}")
    print()
    print(f"Paired (CatBoost vs LGB, 5 seeds pooled):")
    print(f"  median Δ:          {paired['median_delta']:+.5f}")
    print(f"  WinRate (CB < LGB): {paired['win_rate_variant']:.4f}")
    print(f"  Cohen's d:         {paired['cohen_d']:+.4f}")
    print(f"  Seeds Δ<0:         {paired['seeds_negative_delta']}/5")
    print(f"  Seeds WR>0.5:      {paired['seeds_wr_above_0.5']}/5")
    print(f"  Tail max rel Δ:    {paired['mean_tail_max_rel_delta']:+.4f}")
    print()
    print("=" * 70)
    print(f"⚖️ 판정: candidate={candidate}")
    print(f"  median_improved (< -0.005):    {median_improved}")
    print(f"  wr_strong (> 0.52):            {wr_strong}")
    print(f"  seed_consistent (≥4/5):        {seed_consistent}")
    print(f"  cohen_strong (< -0.05):        {cohen_strong}")
    print(f"  tail_ok (≤ 10%):               {tail_ok}")
    print()
    print(f"📌 {'release_split confirm 후보 → F3 step A 진행' if candidate else 'V0+LGB 유지, F4 진행 검토'}")

    save = {
        "seeds": SEEDS,
        "per_seed": {s: {m: {k: v for k, v in r[m].items() if k != "ape_array"}
                          for m in ["lgb", "catboost"]}
                     for s, r in seed_results.items()},
        "paired_catboost_vs_lgb": paired,
        "judgement_candidate": bool(candidate),
        "criteria": {
            "median_improved": median_improved, "wr_strong": wr_strong,
            "seed_consistent": seed_consistent, "cohen_strong": cohen_strong,
            "tail_ok": tail_ok,
        },
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
