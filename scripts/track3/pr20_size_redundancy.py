"""Track 3 PR20 (F1) — 크기 변수 redundancy ablation.

실험 목적 (track3_experiment_plan_v1.md F1):
  width_cm / height_cm / log_area / estimated_ho 4개가 같은 크기 축의 다른 표현인지 검증.
  대표 조합으로 줄여도 성능 유지되면 모델 단순화 + 안정성 ↑.

사용 데이터: data/release_split/track3_train.csv (학습) + test_warm/test_cold (최종 confirm)
검증 protocol: 5 seeds mini hold-out paired + Cold LAD / Warm Tuned LGB
산출물: data/track3_pr20_size_redundancy_results.json

Variant 5개 (depth_cm 모든 variant 유지 — 입체성 축):
  V0_all     : 4개 모두 (현 운영) + aspect_ratio + medium_ho_bucket
  V1_log_ho  : log_area + estimated_ho (raw 제외, medium_ho_bucket 유지)
  V2_log_only: log_area만 (가장 단순)
  V3_wh_only : width + height + aspect_ratio (raw 만)
  V4_ho_only : estimated_ho + medium_ho_bucket (한국 호수만)

판정 기준 (paired delta vs V0):
  채택 후보: |delta| ≤ 0.005 (Warm/Cold 모두) + WinRate 0.48~0.52 + Cohen's d <0.05
    → 동등 성능 + 단순화 효과 → 운영 채택 검토
  현 유지: V0이 유의하게 우수 (Cohen's d > 0.05 OR delta < -0.005)
  제외: variant가 명확히 worse
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_pr20_size_redundancy_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [42, 123, 7, 2024, 999]
N_COLD_MINI = 100
WARM_PER_ARTIST = 1

# 공통 fixed features (크기 변수 ablation 외)
FIXED_BASE = ["medium_category", "support_category", "orientation", "depth_cm"]
FIXED_CAT = ["medium_category", "support_category", "orientation"]

# 5 variants — 크기 input + 가능한 derive
VARIANTS = {
    "V0_all":      {"size": ["width_cm", "height_cm", "log_area", "estimated_ho"],
                    "derive_aspect": True,  "derive_medium_ho": True},
    "V1_log_ho":   {"size": ["log_area", "estimated_ho"],
                    "derive_aspect": False, "derive_medium_ho": True},
    "V2_log_only": {"size": ["log_area"],
                    "derive_aspect": False, "derive_medium_ho": False},
    "V3_wh_only":  {"size": ["width_cm", "height_cm"],
                    "derive_aspect": True,  "derive_medium_ho": False},
    "V4_ho_only":  {"size": ["estimated_ho"],
                    "derive_aspect": False, "derive_medium_ho": True},
}

# LGB hyperparam — deterministic + 운영 동일 (PR1 Optuna 결과)
LGB_PARAMS_BASE = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
}


def make_features(df, train_counts, derive_aspect, derive_medium_ho):
    """Variant별 derive 추가."""
    df = df.copy()
    if derive_medium_ho:
        df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                                  labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
        df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    if derive_aspect:
        df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def get_variant_features(variant_name, include_artist=False):
    """Variant feature list 생성."""
    cfg = VARIANTS[variant_name]
    feats = FIXED_BASE + cfg["size"]
    cat = FIXED_CAT.copy()
    if cfg["derive_medium_ho"]:
        feats.append("medium_ho_bucket")
        cat.append("medium_ho_bucket")
    if cfg["derive_aspect"]:
        feats.append("aspect_ratio")
    feats.append("artist_works_log")
    if include_artist:
        feats.append(ARTIST_COL)
        cat.append(ARTIST_COL)
    return feats, cat


def build_lad(features, cat_cols):
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", pre),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns: df[c] = df[c].astype("category")
    return df


def train_lgb(df_train, features, cat_cols, seed):
    p = {**LGB_PARAMS_BASE,
         "seed": seed, "bagging_seed": seed, "feature_fraction_seed": seed,
         "data_random_seed": seed, "drop_seed": seed, "objective_seed": seed}
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    X_tr = to_cat(df_train.iloc[perm[cut:]], features, cat_cols)
    X_va = to_cat(df_train.iloc[perm[:cut]], features, cat_cols)
    y_tr = df_train.iloc[perm[cut:]][TARGET].values
    y_va = df_train.iloc[perm[:cut]][TARGET].values
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_cols)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=cat_cols, reference=tr_set)
    return lgb.train(p, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
        "ape_array": ape.tolist(),
    }


def paired_stats(ape_baseline, ape_variant):
    ape_b = np.array(ape_baseline); ape_v = np.array(ape_variant)
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
    cold_mini = train_df[train_df[ARTIST_COL].isin(cold_set)].copy()
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
    return mini_train, warm_mini, cold_mini


def train_and_predict(mini_train, warm_mini, cold_mini, variant, seed):
    cfg = VARIANTS[variant]
    cold_feats, cold_cat = get_variant_features(variant, include_artist=False)
    warm_feats, warm_cat = get_variant_features(variant, include_artist=True)

    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts, cfg["derive_aspect"], cfg["derive_medium_ho"])
    cm = make_features(cold_mini, counts, cfg["derive_aspect"], cfg["derive_medium_ho"])
    wm = make_features(warm_mini, counts, cfg["derive_aspect"], cfg["derive_medium_ho"])

    # Cold LAD
    assert not (set(cold_mini[ARTIST_COL]) & set(mini_train[ARTIST_COL])), "cold leak"
    lad = build_lad(cold_feats, cold_cat)
    lad.fit(tr[cold_feats], tr[TARGET].values)
    cold_pred = lad.predict(cm[cold_feats])

    # Warm LGB
    assert set(warm_mini[ARTIST_COL]).issubset(set(mini_train[ARTIST_COL])), "warm: all artists must be in mini_train"
    lgbm = train_lgb(tr, warm_feats, warm_cat, seed)
    warm_pred = lgbm.predict(to_cat(wm, warm_feats, warm_cat))

    return cold_pred, warm_pred


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR20 (F1) — 크기 변수 redundancy ablation")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    # ── 5 seeds × 5 variants ──
    seed_results = {}
    for seed in SEEDS:
        logger.info(f"\n=== Seed {seed} ===")
        mini_train, warm_mini, cold_mini = setup_mini_holdout(train, seed)
        logger.info(f"  mini_train {len(mini_train):,} / warm {len(warm_mini):,} / cold {len(cold_mini):,}")

        results = {}
        for v in VARIANTS:
            logger.info(f"  [{v}] 학습")
            cold_pred, warm_pred = train_and_predict(mini_train, warm_mini, cold_mini, v, seed)
            results[v] = {
                "cold": compute_metrics(cold_mini[TARGET].values, cold_pred),
                "warm": compute_metrics(warm_mini[TARGET].values, warm_pred),
            }
        seed_results[str(seed)] = results

    # ── 종합 분석 ──
    def aggregate(variant, slice_name, metric):
        vals = [seed_results[str(s)][variant][slice_name][metric] for s in SEEDS]
        return float(np.mean(vals)), float(np.std(vals))

    # Paired stats: each variant vs V0_all (per slice, pooled 5 seeds)
    paired = {}
    for v in VARIANTS:
        if v == "V0_all": continue
        paired[v] = {}
        for slice_name in ["cold", "warm"]:
            ape_b_all = []; ape_v_all = []
            seed_medians = []; seed_wrs = []
            for s in SEEDS:
                ape_b = np.array(seed_results[str(s)]["V0_all"][slice_name]["ape_array"])
                ape_v = np.array(seed_results[str(s)][v][slice_name]["ape_array"])
                ape_b_all.extend(ape_b.tolist())
                ape_v_all.extend(ape_v.tolist())
                seed_medians.append(float(np.median(ape_v - ape_b)))
                seed_wrs.append(float((ape_v < ape_b).mean()))
            ps = paired_stats(ape_b_all, ape_v_all)
            ps["per_seed_median_delta"] = seed_medians
            ps["per_seed_win_rate"] = seed_wrs
            ps["seeds_negative_delta"] = sum(1 for d in seed_medians if d < 0)
            ps["seeds_wr_above_0.5"] = sum(1 for w in seed_wrs if w > 0.5)
            paired[v][slice_name] = ps

    # 판정 — Codex 2차 권고:
    # Cold APE는 heavy-tail이라 mean_delta / Cohen's d 비신뢰.
    # Cold는 median + WR + seed consistency 기반.
    # Warm은 mean도 의미 있으니 모두 사용.
    def judge(p, slice_name):
        median_small = abs(p["median_delta"]) <= 0.005
        wr_near_half = 0.48 <= p["win_rate_variant"] <= 0.52
        seed_consistent = 2 <= p["seeds_negative_delta"] <= 3  # 5 seeds 중 2-3개 음수 (균등)
        if slice_name == "cold":
            # Cold: median + WR + seed consistency 만 사용 (mean/Cohen 무시)
            candidate = median_small and wr_near_half and seed_consistent
            return {
                "small_median_delta": median_small,
                "wr_near_half": wr_near_half,
                "seed_consistent": seed_consistent,
                "equivalent_simplification_candidate": candidate,
            }
        else:
            mean_small = abs(p["mean_delta"]) <= 0.005
            cohen_small = abs(p["cohen_d"]) < 0.05
            candidate = mean_small and median_small and cohen_small and wr_near_half
            return {
                "small_mean_delta": mean_small,
                "small_median_delta": median_small,
                "small_cohen_d": cohen_small,
                "wr_near_half": wr_near_half,
                "seed_consistent": seed_consistent,
                "equivalent_simplification_candidate": candidate,
            }

    judgements = {v: {s: judge(paired[v][s], s) for s in ["cold", "warm"]} for v in paired}

    # ── 출력 ──
    print()
    print("=" * 90)
    print("📊 F1 — 5 seeds 평균 med_APE (Mean ± Std)")
    print("=" * 90)
    print(f"{'Variant':<14} {'Cold mean ± std':>22} {'Warm mean ± std':>22}")
    print("-" * 60)
    for v in VARIANTS:
        cm_m, cm_s = aggregate(v, "cold", "median_ape")
        wm_m, wm_s = aggregate(v, "warm", "median_ape")
        marker = " (baseline)" if v == "V0_all" else ""
        print(f"{v:<14}  {cm_m:>10.4f} ± {cm_s:>5.4f}   {wm_m:>10.4f} ± {wm_s:>5.4f}{marker}")

    print()
    print("=" * 90)
    print("Paired delta vs V0_all (mean of pooled rows)")
    print("=" * 90)
    print(f"{'Variant':<14} {'Slice':<6} {'mean_Δ':>10} {'med_Δ':>10} {'CI95':>22} {'WR':>7} {'Cohen d':>9} {'seeds Δ<0':>10}")
    for v in paired:
        for slice_name in ["cold", "warm"]:
            p = paired[v][slice_name]
            print(f"{v:<14} {slice_name:<6} {p['mean_delta']:>+10.5f} {p['median_delta']:>+10.5f} "
                  f"[{p['ci95_low']:>+7.4f},{p['ci95_high']:>+7.4f}] "
                  f"{p['win_rate_variant']:>7.4f} {p['cohen_d']:>+9.4f} "
                  f"{p['seeds_negative_delta']:>5}/5")

    print()
    print("=" * 90)
    print("⚖️ 판정 — 동등 성능 + 단순화 가능?")
    print("=" * 90)
    for v in judgements:
        for slice_name in ["cold", "warm"]:
            j = judgements[v][slice_name]
            mark = "✅" if j["equivalent_simplification_candidate"] else "❌"
            passes = [k for k, val in j.items() if val and k != "equivalent_simplification_candidate"]
            print(f"  {mark} {v} ({slice_name}): candidate={j['equivalent_simplification_candidate']}, passes={passes}")

    # Save
    save = {
        "seeds": SEEDS,
        "variants": list(VARIANTS.keys()),
        "per_seed": {s: {v: {sl: {k: vv for k, vv in r[sl].items() if k != "ape_array"}
                              for sl in ["cold", "warm"]}
                          for v, r in seed_results[s].items()}
                     for s in seed_results},
        "paired_vs_V0": paired,
        "judgement": judgements,
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
