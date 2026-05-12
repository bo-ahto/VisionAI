"""Track 3 PR25 (F4) — Rare-artist Warm/Cold blend.

실험 목적 (Codex 1순위 권고):
  현 운영 라우팅 (train_count>=1 → Warm 100%)에서 rare artist (1건/2건)는 신호 약함.
  rare artist를 Cold 모델과 blend하면 Warm tail risk 감소 + 안정성 ↑?

검증 protocol:
  - 5 seeds mini hold-out
  - mini_train으로 Warm LGB + Cold LAD 학습 (1회씩)
  - warm_mini 각 row에 대해 Warm/Cold 예측 둘 다 계산 후 4 variants 후처리 blend
  - V0_pure_warm (현 운영) baseline, F4_b1~b4 variants

판정 기준 (Codex 보수화):
  paired median Δ < -0.005 + WR > 0.52 + 5 seeds 4/5 일관
  + Cohen's d < -0.05 + tail risk 악화 없음 (max_ape 상대 Δ ≤ 10%)
→ 만족 시 release_split confirm 진행

산출물: data/track3_pr25_blend_results.json
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
OUT_PATH = REPO / "data" / "track3_pr25_blend_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [42, 123, 7, 2024, 999]
N_COLD_MINI = 100
WARM_PER_ARTIST = 1

# Cold feature set (현 운영 v1.2)
COLD_FEATS = ["medium_category", "support_category", "orientation",
               "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
               "medium_ho_bucket", "aspect_ratio", "artist_works_log"]
COLD_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

# Warm feature set (Cold + artist_name_ko)
WARM_FEATS = COLD_FEATS + [ARTIST_COL]
WARM_CAT = COLD_CAT + [ARTIST_COL]

LGB_PARAMS_BASE = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
}

# Blend variants: (count_threshold, alpha) → train_count<=threshold면 alpha·Warm + (1-alpha)·Cold
BLEND_VARIANTS = {
    "V0_pure_warm":    None,                  # baseline (현 운영)
    "F4_b1_count1_a50": (1, 0.5),
    "F4_b2_count1_a30": (1, 0.3),
    "F4_b3_count2_a50": (2, 0.5),
    "F4_b4_count5_a50": (5, 0.5),
}


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


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


def apply_blend(warm_pred, cold_pred, train_counts_for_test, threshold, alpha):
    """train_counts_for_test: test 작가별 train count array (warm_mini와 동일 길이).
    Returns blended prediction (ln scale)."""
    blend_mask = train_counts_for_test <= threshold
    blended = warm_pred.copy()
    blended[blend_mask] = alpha * warm_pred[blend_mask] + (1 - alpha) * cold_pred[blend_mask]
    return blended


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR25 (F4) — Rare-artist Warm/Cold blend")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    seed_results = {}
    train_count_dist = {}  # warm_mini의 train_count 분포

    for seed in SEEDS:
        logger.info(f"\n=== Seed {seed} ===")
        mini_train, warm_mini = setup_mini_holdout(train, seed)
        counts = mini_train[ARTIST_COL].value_counts().to_dict()
        train_counts_for_warm = np.array([counts.get(a, 0) for a in warm_mini[ARTIST_COL]])
        train_count_dist[str(seed)] = {
            "count_1": int((train_counts_for_warm == 1).sum()),
            "count_2": int((train_counts_for_warm == 2).sum()),
            "count_3_5": int(((train_counts_for_warm >= 3) & (train_counts_for_warm <= 5)).sum()),
            "count_gt5": int((train_counts_for_warm > 5).sum()),
            "total": int(len(train_counts_for_warm)),
        }
        logger.info(f"  warm_mini train_count: 1건={train_count_dist[str(seed)]['count_1']}, "
                    f"2건={train_count_dist[str(seed)]['count_2']}, "
                    f"3-5건={train_count_dist[str(seed)]['count_3_5']}, "
                    f">5건={train_count_dist[str(seed)]['count_gt5']}")

        tr = make_features(mini_train, counts)
        wm = make_features(warm_mini, counts)

        # Warm LGB 학습
        logger.info("  Warm LGB 학습")
        lgb_model = train_lgb(tr, seed)
        warm_pred_raw = lgb_model.predict(to_cat(wm, WARM_FEATS, WARM_CAT))

        # Cold LAD 학습 (artist 정보 무시한 prediction)
        logger.info("  Cold LAD 학습")
        cold_model = build_lad(COLD_FEATS, COLD_CAT)
        cold_model.fit(tr[COLD_FEATS], tr[TARGET].values)
        # warm_mini를 Cold model로 예측 (artist_works_log는 mini_train 기준 그대로 사용)
        cold_pred_raw = cold_model.predict(wm[COLD_FEATS])

        # 5 variants 적용
        y_warm_ln = warm_mini[TARGET].values
        results = {}
        for v_name, cfg in BLEND_VARIANTS.items():
            if cfg is None:
                pred = warm_pred_raw  # V0: 순수 Warm
            else:
                threshold, alpha = cfg
                pred = apply_blend(warm_pred_raw, cold_pred_raw, train_counts_for_warm, threshold, alpha)
            results[v_name] = compute_metrics(y_warm_ln, pred)
        seed_results[str(seed)] = results
        for v_name in BLEND_VARIANTS:
            logger.info(f"  {v_name}: med_APE={results[v_name]['median_ape']:.4f}")

    # ─── 종합 ───
    def agg(variant, metric):
        vals = [seed_results[str(s)][variant][metric] for s in SEEDS]
        return float(np.mean(vals)), float(np.std(vals))

    # Paired stats vs V0_pure_warm
    paired = {}
    for v in BLEND_VARIANTS:
        if v == "V0_pure_warm": continue
        ape_b_all = []; ape_v_all = []
        seed_medians = []; seed_wrs = []; tail_max_rel_deltas = []
        for s in SEEDS:
            v0 = seed_results[str(s)]["V0_pure_warm"]
            vv = seed_results[str(s)][v]
            ape_b = np.array(v0["ape_array"])
            ape_v = np.array(vv["ape_array"])
            ape_b_all.extend(ape_b.tolist())
            ape_v_all.extend(ape_v.tolist())
            seed_medians.append(float(np.median(ape_v - ape_b)))
            seed_wrs.append(float((ape_v < ape_b).mean()))
            tail_max_rel_deltas.append((vv["max_ape"] - v0["max_ape"]) / max(v0["max_ape"], 0.01))
        ps = paired_stats(ape_b_all, ape_v_all)
        ps["per_seed_median_delta"] = seed_medians
        ps["per_seed_win_rate"] = seed_wrs
        ps["seeds_negative_delta"] = sum(1 for d in seed_medians if d < 0)
        ps["seeds_wr_above_0.5"] = sum(1 for w in seed_wrs if w > 0.5)
        ps["mean_tail_max_rel_delta"] = float(np.mean(tail_max_rel_deltas))
        paired[v] = ps

    # 판정 (Codex 보수화)
    def judge(p):
        median_improved = p["median_delta"] < -0.005
        wr_strong = p["win_rate_variant"] > 0.52
        seed_consistent = p["seeds_negative_delta"] >= 4
        cohen_strong = p["cohen_d"] < -0.05
        tail_ok = p["mean_tail_max_rel_delta"] <= 0.10
        candidate = median_improved and wr_strong and seed_consistent and cohen_strong and tail_ok
        return {
            "median_improved": median_improved, "wr_strong": wr_strong,
            "seed_consistent": seed_consistent, "cohen_strong": cohen_strong,
            "tail_ok": tail_ok,
            "candidate_for_release_split_confirm": candidate,
        }

    judgements = {v: judge(paired[v]) for v in paired}

    # ─── 출력 ───
    print()
    print("=" * 90)
    print("📊 F4 — Warm med_APE (5 seeds 평균)")
    print("=" * 90)
    for v in BLEND_VARIANTS:
        m, s = agg(v, "median_ape")
        marker = " (baseline)" if v == "V0_pure_warm" else ""
        print(f"  {v:<22} {m:.4f} ± {s:.4f}{marker}")

    print()
    print("=" * 90)
    print("Paired delta vs V0_pure_warm (5 seeds pooled)")
    print("=" * 90)
    print(f"{'Variant':<22} {'med_Δ':>10} {'WR':>7} {'Cohen d':>9} {'seeds Δ<0':>10} {'seeds WR>0.5':>13} {'max_rel_Δ':>11}")
    for v in paired:
        p = paired[v]
        print(f"{v:<22} {p['median_delta']:>+10.5f} {p['win_rate_variant']:>7.4f} "
              f"{p['cohen_d']:>+9.4f} {p['seeds_negative_delta']:>5}/5  "
              f"{p['seeds_wr_above_0.5']:>5}/5     {p['mean_tail_max_rel_delta']:>+11.4f}")

    print()
    print("=" * 90)
    print("⚖️ 판정 — release_split confirm 후보?")
    print("=" * 90)
    any_candidate = False
    for v, j in judgements.items():
        mark = "✅" if j["candidate_for_release_split_confirm"] else "❌"
        passes = [k for k, val in j.items() if val and k != "candidate_for_release_split_confirm"]
        print(f"  {mark} {v}: candidate={j['candidate_for_release_split_confirm']}, passes={passes}")
        if j["candidate_for_release_split_confirm"]: any_candidate = True

    print(f"\n📌 {'release_split confirm 후보 발견 → F4 step A 진행' if any_candidate else 'V0_pure_warm 유지'}")

    save = {
        "seeds": SEEDS,
        "variants": list(BLEND_VARIANTS.keys()),
        "blend_config": {v: cfg for v, cfg in BLEND_VARIANTS.items()},
        "warm_mini_train_count_dist": train_count_dist,
        "per_seed": {s: {v: {k: vv for k, vv in r.items() if k != "ape_array"}
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
