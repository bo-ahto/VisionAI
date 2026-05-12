"""Track 3 PR22 (F2) — 새 파생 변수 4개 단일-feature ablation.

실험 목적 (track3_experiment_plan_v1.md F2):
  4개 미검증 파생 변수 중 어느 것이 Warm 또는 Cold에 의미 있는 기여를 하는지 확인.
  한 번에 하나씩 추가 (single feature ablation).

검증 변수 (4개):
  medium_support_combo  : medium × support interaction (categorical)
  max_side_cm           : max(width, height) (float)
  is_square_like        : |aspect_ratio| < 0.2 → 1 else 0 (binary)
  area_depth_interaction: log_area × depth_cm (float)

사용 데이터: data/release_split/track3_train.csv (학습) + mini hold-out 5 seeds
검증 protocol: PR20과 동일 (5 seeds × 5 variants × Cold LAD/Warm LGB)
산출물: data/track3_pr22_new_features_results.json

후보 발굴 기준 (개선 신호):
  paired median Δ < -0.005 (Warm 또는 Cold)
  AND WR > 0.52
  AND 5 seeds 중 4/5 seeds Δ<0 (방향 일관)
  AND Cohen's d > 0.05 (Warm에 한정, Cold는 heavy-tail로 무시)
  AND tail risk 악화 없음 (max_ape Δ < 10%)
→ 만족 시 release_split confirm (F2 step A) 진행
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
OUT_PATH = REPO / "data" / "track3_pr22_new_features_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [42, 123, 7, 2024, 999]
N_COLD_MINI = 100
WARM_PER_ARTIST = 1

# V0 baseline features
V0_FEATS_BASE = ["medium_category", "support_category", "orientation",
                  "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho"]
V0_CAT_BASE = ["medium_category", "support_category", "orientation"]

# 새 파생 변수별 추가 사항
NEW_FEATURES = {
    "V0_base":           {"extra": [],                          "extra_cat": []},
    "F1_combo":          {"extra": ["medium_support_combo"],    "extra_cat": ["medium_support_combo"]},
    "F2_maxside":        {"extra": ["max_side_cm"],             "extra_cat": []},
    "F3_square":         {"extra": ["is_square_like"],          "extra_cat": []},
    "F4_area_depth":     {"extra": ["area_depth_interaction"],  "extra_cat": []},
}

LGB_PARAMS_BASE = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
}


def make_base_features(df, train_counts):
    """V0 baseline + 모든 신규 파생 변수 derive (variant별로 feature list만 다르게 선택)."""
    df = df.copy()
    # Standard derive
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    # New derive (모두 derive, 사용 여부는 feature list에서 결정)
    df["medium_support_combo"] = (df["medium_category"].astype(str) + "_"
                                  + df["support_category"].astype(str))
    df["max_side_cm"] = df[["width_cm", "height_cm"]].max(axis=1)
    df["is_square_like"] = (df["aspect_ratio"].abs() < 0.2).astype(int)
    df["area_depth_interaction"] = df["log_area"] * df["depth_cm"]
    return df


def get_variant_features(variant_name, include_artist):
    """Variant feature list 반환."""
    cfg = NEW_FEATURES[variant_name]
    feats = V0_FEATS_BASE + ["medium_ho_bucket", "aspect_ratio", "artist_works_log"] + cfg["extra"]
    cat = V0_CAT_BASE + ["medium_ho_bucket"] + cfg["extra_cat"]
    if include_artist:
        feats.append(ARTIST_COL); cat.append(ARTIST_COL)
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
    cold_feats, cold_cat = get_variant_features(variant, include_artist=False)
    warm_feats, warm_cat = get_variant_features(variant, include_artist=True)

    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_base_features(mini_train, counts)
    cm = make_base_features(cold_mini, counts)
    wm = make_base_features(warm_mini, counts)

    # Cold LAD
    assert not (set(cold_mini[ARTIST_COL]) & set(mini_train[ARTIST_COL])), "cold leak"
    lad = build_lad(cold_feats, cold_cat)
    lad.fit(tr[cold_feats], tr[TARGET].values)
    cold_pred = lad.predict(cm[cold_feats])

    # Warm LGB
    assert set(warm_mini[ARTIST_COL]).issubset(set(mini_train[ARTIST_COL])), "warm artist leak"
    lgbm = train_lgb(tr, warm_feats, warm_cat, seed)
    warm_pred = lgbm.predict(to_cat(wm, warm_feats, warm_cat))

    return cold_pred, warm_pred


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR22 (F2) — 새 파생 변수 4개 단일-feature ablation")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    seed_results = {}
    for seed in SEEDS:
        logger.info(f"\n=== Seed {seed} ===")
        mini_train, warm_mini, cold_mini = setup_mini_holdout(train, seed)
        logger.info(f"  mini {len(mini_train):,} / warm {len(warm_mini):,} / cold {len(cold_mini):,}")

        results = {}
        for v in NEW_FEATURES:
            logger.info(f"  [{v}] 학습")
            cold_pred, warm_pred = train_and_predict(mini_train, warm_mini, cold_mini, v, seed)
            results[v] = {
                "cold": compute_metrics(cold_mini[TARGET].values, cold_pred),
                "warm": compute_metrics(warm_mini[TARGET].values, warm_pred),
            }
        seed_results[str(seed)] = results

    # ─── 종합 ───
    def agg(variant, slice_name, metric):
        vals = [seed_results[str(s)][variant][slice_name][metric] for s in SEEDS]
        return float(np.mean(vals)), float(np.std(vals))

    # Paired stats vs V0_base
    paired = {}
    for v in NEW_FEATURES:
        if v == "V0_base": continue
        paired[v] = {}
        for slice_name in ["cold", "warm"]:
            ape_b_all = []; ape_v_all = []
            seed_medians = []; seed_wrs = []
            tail_max_rel_deltas = []  # V0 대비 상대값
            for s in SEEDS:
                v0 = seed_results[str(s)]["V0_base"][slice_name]
                vv = seed_results[str(s)][v][slice_name]
                ape_b = np.array(v0["ape_array"])
                ape_v = np.array(vv["ape_array"])
                ape_b_all.extend(ape_b.tolist())
                ape_v_all.extend(ape_v.tolist())
                seed_medians.append(float(np.median(ape_v - ape_b)))
                seed_wrs.append(float((ape_v < ape_b).mean()))
                tail_max_rel_deltas.append(
                    (vv["max_ape"] - v0["max_ape"]) / max(v0["max_ape"], 0.01))
            ps = paired_stats(ape_b_all, ape_v_all)
            ps["per_seed_median_delta"] = seed_medians
            ps["per_seed_win_rate"] = seed_wrs
            ps["seeds_negative_delta"] = sum(1 for d in seed_medians if d < 0)
            ps["seeds_wr_above_0.5"] = sum(1 for w in seed_wrs if w > 0.5)
            ps["mean_tail_max_rel_delta"] = float(np.mean(tail_max_rel_deltas))
            paired[v][slice_name] = ps

    # 판정 — 후보 발굴 기준
    def judge(p, slice_name):
        # 개선 signal: median Δ < -0.005, WR > 0.52, 4/5 seeds Δ<0
        median_improved = p["median_delta"] < -0.005
        wr_strong = p["win_rate_variant"] > 0.52
        seed_consistent = p["seeds_negative_delta"] >= 4
        # Warm은 Cohen's d 추가 (mean 안정)
        cohen_strong = abs(p["cohen_d"]) > 0.05 and p["cohen_d"] < 0
        # Tail risk 악화 없음 (V0 대비 max_ape 상대 증가 ≤ 10%)
        tail_ok = p["mean_tail_max_rel_delta"] <= 0.10
        if slice_name == "cold":
            candidate = median_improved and wr_strong and seed_consistent and tail_ok
        else:
            candidate = median_improved and wr_strong and seed_consistent and cohen_strong and tail_ok
        return {
            "median_improved": median_improved, "wr_strong": wr_strong,
            "seed_consistent": seed_consistent, "cohen_strong": cohen_strong,
            "tail_ok": tail_ok,
            "candidate_for_release_split_confirm": candidate,
        }

    judgements = {v: {s: judge(paired[v][s], s) for s in ["cold", "warm"]} for v in paired}

    # ─── 출력 ───
    print()
    print("=" * 90)
    print("📊 F2 — 5 seeds 평균 med_APE (Mean ± Std)")
    print("=" * 90)
    print(f"{'Variant':<16} {'Cold mean ± std':>22} {'Warm mean ± std':>22}")
    print("-" * 60)
    for v in NEW_FEATURES:
        cm_m, cm_s = agg(v, "cold", "median_ape")
        wm_m, wm_s = agg(v, "warm", "median_ape")
        marker = " (baseline)" if v == "V0_base" else ""
        print(f"{v:<16} {cm_m:>10.4f} ± {cm_s:>5.4f}   {wm_m:>10.4f} ± {wm_s:>5.4f}{marker}")

    print()
    print("=" * 90)
    print("Paired delta vs V0_base (5 seeds pooled)")
    print("=" * 90)
    print(f"{'Variant':<16} {'Slice':<6} {'med_Δ':>10} {'WR':>7} {'Cohen d':>9} "
          f"{'seeds Δ<0':>10} {'seeds WR>0.5':>13} {'max_rel_Δ':>11}")
    for v in paired:
        for slice_name in ["cold", "warm"]:
            p = paired[v][slice_name]
            print(f"{v:<16} {slice_name:<6} {p['median_delta']:>+10.5f} "
                  f"{p['win_rate_variant']:>7.4f} {p['cohen_d']:>+9.4f} "
                  f"{p['seeds_negative_delta']:>5}/5  "
                  f"{p['seeds_wr_above_0.5']:>5}/5     "
                  f"{p['mean_tail_max_rel_delta']:>+11.4f}")

    print()
    print("=" * 90)
    print("⚖️ 판정 — release_split confirm 후보?")
    print("=" * 90)
    any_candidate = False
    for v in judgements:
        for slice_name in ["cold", "warm"]:
            j = judgements[v][slice_name]
            mark = "✅" if j["candidate_for_release_split_confirm"] else "❌"
            passes = [k for k, val in j.items() if val and k != "candidate_for_release_split_confirm"]
            print(f"  {mark} {v} ({slice_name}): candidate={j['candidate_for_release_split_confirm']}, passes={passes}")
            if j["candidate_for_release_split_confirm"]:
                any_candidate = True

    print(f"\n📌 {'release_split confirm 후보 발견 → F2 step A 진행' if any_candidate else '후보 없음 → V0_base 유지, F3 진행 검토'}")

    save = {
        "seeds": SEEDS,
        "variants": list(NEW_FEATURES.keys()),
        "per_seed": {s: {v: {sl: {k: vv for k, vv in r[sl].items() if k != "ape_array"}
                              for sl in ["cold", "warm"]}
                          for v, r in seed_results[s].items()}
                     for s in seed_results},
        "paired_vs_V0": paired,
        "judgement": judgements,
        "any_candidate_found": bool(any_candidate),
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
