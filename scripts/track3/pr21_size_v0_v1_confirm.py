"""Track 3 PR21 (F1 step A) — V0 vs V1_log_ho release_split test 최종 confirm.

실험 목적 (F1 follow-up, Codex 권고 A):
  PR20 5 seeds mini hold-out에서 V1_log_ho가 V0와 유력한 동등 후보로 식별됨.
  release_split test (Warm + Cold) 1회 paired comparison으로 최종 confirm.

추가 tail risk metric (Codex 권고): p95 / p99 / max APE, 10x 오차 (APE>1.0) 건수.

판정 기준:
  Warm + Cold 모두에서 |median Δ| 작음 + WR 0.48~0.52 + tail risk 비슷
    → V1_log_ho 채택 가능, production v1.3 학습 검토
  하나라도 미충족 → V0 유지

데이터: release_split/track3_train.csv (학습)
       release_split/track3_test_{warm,cold}.csv (평가)
산출물: data/track3_pr21_size_confirm_results.json
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
OUT_PATH = REPO / "data" / "track3_pr21_size_confirm_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEED = 42

# 공통 fixed
FIXED_BASE = ["medium_category", "support_category", "orientation", "depth_cm"]
FIXED_CAT = ["medium_category", "support_category", "orientation"]

# V0 vs V1 size feature sets
V0_SIZE = ["width_cm", "height_cm", "log_area", "estimated_ho"]
V1_SIZE = ["log_area", "estimated_ho"]

LGB_PARAMS_BASE = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
    "seed": SEED, "bagging_seed": SEED, "feature_fraction_seed": SEED,
    "data_random_seed": SEED, "drop_seed": SEED, "objective_seed": SEED,
}


def make_features(df, train_counts, derive_aspect, derive_medium_ho):
    df = df.copy()
    if derive_medium_ho:
        df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                                  labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
        df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    if derive_aspect:
        df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def get_features(variant, include_artist):
    """Returns (features, cat_cols, derive_flags)."""
    if variant == "V0":
        size = V0_SIZE
        derive_aspect = True
        derive_medium_ho = True
    elif variant == "V1":
        size = V1_SIZE
        derive_aspect = False
        derive_medium_ho = True
    feats = FIXED_BASE + size
    cat = FIXED_CAT.copy()
    if derive_medium_ho:
        feats.append("medium_ho_bucket"); cat.append("medium_ho_bucket")
    if derive_aspect:
        feats.append("aspect_ratio")
    feats.append("artist_works_log")
    if include_artist:
        feats.append(ARTIST_COL); cat.append(ARTIST_COL)
    return feats, cat, (derive_aspect, derive_medium_ho)


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


def train_lgb(df_train, features, cat_cols):
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    X_tr = to_cat(df_train.iloc[perm[cut:]], features, cat_cols)
    X_va = to_cat(df_train.iloc[perm[:cut]], features, cat_cols)
    y_tr = df_train.iloc[perm[cut:]][TARGET].values
    y_va = df_train.iloc[perm[:cut]][TARGET].values
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_cols)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=cat_cols, reference=tr_set)
    return lgb.train(LGB_PARAMS_BASE, tr_set, num_boost_round=2000,
                     valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def compute_metrics(y_true_ln, y_pred_ln):
    """기존 metric + tail risk (Codex 권고)."""
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
        # Tail risk (Codex 권고)
        "p95_ape": float(np.percentile(ape, 95)),
        "p99_ape": float(np.percentile(ape, 99)),
        "max_ape": float(np.max(ape)),
        "n_10x_errors": int((ape > 1.0).sum()),  # APE > 100% 건수
        "pct_10x_errors": float((ape > 1.0).mean()),
        "ape_array": ape.tolist(),
    }


def paired_stats(ape_b, ape_v, name=""):
    """Paired comparison + bootstrap CI."""
    ape_b = np.array(ape_b); ape_v = np.array(ape_v)
    delta = ape_v - ape_b
    rng = np.random.default_rng(0)
    boots = [np.mean(rng.choice(delta, size=len(delta), replace=True)) for _ in range(2000)]
    return {
        "name": name,
        "n": int(len(delta)),
        "mean_delta": float(np.mean(delta)),
        "median_delta": float(np.median(delta)),
        "win_rate_variant": float((ape_v < ape_b).mean()),
        "ci95_low": float(np.percentile(boots, 2.5)),
        "ci95_high": float(np.percentile(boots, 97.5)),
        "cohen_d": float(np.mean(delta) / np.std(delta, ddof=1)) if np.std(delta, ddof=1) > 0 else 0.0,
        # tail-aware
        "catastrophic_2x": float((ape_v > 2 * ape_b).mean()),
        "n_v_better_by_10pp": int(((ape_b - ape_v) > 0.1).sum()),   # v가 baseline보다 10%p 좋아진 건수
        "n_v_worse_by_10pp": int(((ape_v - ape_b) > 0.1).sum()),   # v가 baseline보다 10%p 나빠진 건수
    }


def train_and_predict_full(train, test, variant, model_type):
    """release_split train 전체 학습 + test 예측."""
    feats, cat, (da, dm) = get_features(variant, include_artist=(model_type == "warm"))
    counts = train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(train, counts, da, dm)
    te = make_features(test, counts, da, dm)

    if model_type == "cold":
        # cold는 작가 시그널 안 씀, ARTIST_COL 제외 확인
        assert ARTIST_COL not in feats, "Cold features should not include artist"
        model = build_lad(feats, cat)
        model.fit(tr[feats], tr[TARGET].values)
        return model.predict(te[feats])
    else:  # warm
        assert ARTIST_COL in feats
        model = train_lgb(tr, feats, cat)
        return model.predict(to_cat(te, feats, cat))


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR21 (F1 step A) — V0 vs V1_log_ho release_split test confirm")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    tw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    tc = pd.read_csv(SPLIT / "track3_test_cold.csv")
    logger.info(f"train {len(train):,} / test_warm {len(tw):,} / test_cold {len(tc):,}")

    # ── Cold (LAD) ──
    logger.info("\n[Cold] V0 학습 + 예측...")
    cold_pred_v0 = train_and_predict_full(train, tc, "V0", "cold")
    logger.info("[Cold] V1 학습 + 예측...")
    cold_pred_v1 = train_and_predict_full(train, tc, "V1", "cold")
    y_cold_ln = tc[TARGET].values

    cold_v0 = compute_metrics(y_cold_ln, cold_pred_v0)
    cold_v1 = compute_metrics(y_cold_ln, cold_pred_v1)
    cold_paired = paired_stats(cold_v0["ape_array"], cold_v1["ape_array"], "cold")

    # ── Warm (LGB) ──
    logger.info("\n[Warm] V0 학습 + 예측...")
    warm_pred_v0 = train_and_predict_full(train, tw, "V0", "warm")
    logger.info("[Warm] V1 학습 + 예측...")
    warm_pred_v1 = train_and_predict_full(train, tw, "V1", "warm")
    y_warm_ln = tw[TARGET].values

    warm_v0 = compute_metrics(y_warm_ln, warm_pred_v0)
    warm_v1 = compute_metrics(y_warm_ln, warm_pred_v1)
    warm_paired = paired_stats(warm_v0["ape_array"], warm_v1["ape_array"], "warm")

    # ── 출력 ──
    print()
    print("=" * 90)
    print("📊 PR21 — release_split test 최종 confirm (1회 paired)")
    print("=" * 90)

    print(f"\n[Cold] (test_cold n={cold_v0['n']:,})")
    print(f"  {'Metric':<18} {'V0_all':>10} {'V1_log_ho':>10} {'Δ':>10}")
    for k in ["median_ape", "mape", "within_30pct", "within_50pct",
              "p95_ape", "p99_ape", "max_ape", "n_10x_errors", "pct_10x_errors"]:
        d = cold_v1[k] - cold_v0[k]
        print(f"  {k:<18} {cold_v0[k]:>10.4f} {cold_v1[k]:>10.4f} {d:>+10.4f}")
    print(f"  Paired: med_Δ={cold_paired['median_delta']:+.5f}, "
          f"WR={cold_paired['win_rate_variant']:.4f}, "
          f"catastrophic_2x={cold_paired['catastrophic_2x']:.4f}, "
          f"v_better_10pp={cold_paired['n_v_better_by_10pp']}, "
          f"v_worse_10pp={cold_paired['n_v_worse_by_10pp']}")

    print(f"\n[Warm] (test_warm n={warm_v0['n']:,})")
    print(f"  {'Metric':<18} {'V0_all':>10} {'V1_log_ho':>10} {'Δ':>10}")
    for k in ["median_ape", "mape", "within_30pct", "within_50pct",
              "p95_ape", "p99_ape", "max_ape", "n_10x_errors", "pct_10x_errors"]:
        d = warm_v1[k] - warm_v0[k]
        print(f"  {k:<18} {warm_v0[k]:>10.4f} {warm_v1[k]:>10.4f} {d:>+10.4f}")
    print(f"  Paired: med_Δ={warm_paired['median_delta']:+.5f}, "
          f"WR={warm_paired['win_rate_variant']:.4f}, "
          f"catastrophic_2x={warm_paired['catastrophic_2x']:.4f}, "
          f"v_better_10pp={warm_paired['n_v_better_by_10pp']}, "
          f"v_worse_10pp={warm_paired['n_v_worse_by_10pp']}")

    # ── 판정 (Codex 권고) ──
    def judge(paired, v0_m, v1_m):
        # Codex 권고: WR 0.48~0.52 (문서 기준), max_ape도 판정 반영
        median_small = abs(paired["median_delta"]) <= 0.005
        wr_near = 0.48 <= paired["win_rate_variant"] <= 0.52
        # tail risk 유사 (p95/p99/max 차이 ≤ 10%, n_10x 비율 차이 ≤ 0.5%p)
        tail_p95_ok = abs(v1_m["p95_ape"] - v0_m["p95_ape"]) / max(v0_m["p95_ape"], 0.01) <= 0.10
        tail_p99_ok = abs(v1_m["p99_ape"] - v0_m["p99_ape"]) / max(v0_m["p99_ape"], 0.01) <= 0.10
        tail_max_ok = abs(v1_m["max_ape"] - v0_m["max_ape"]) / max(v0_m["max_ape"], 0.01) <= 0.10
        tail_10x_ok = abs(v1_m["pct_10x_errors"] - v0_m["pct_10x_errors"]) <= 0.005
        candidate = (median_small and wr_near and
                     tail_p95_ok and tail_p99_ok and tail_max_ok and tail_10x_ok)
        return {
            "median_delta_small": median_small,
            "wr_near_half": wr_near,
            "tail_p95_similar": tail_p95_ok,
            "tail_p99_similar": tail_p99_ok,
            "tail_max_similar": tail_max_ok,
            "tail_10x_similar": tail_10x_ok,
            "v1_acceptable": candidate,
        }

    judgement = {
        "cold": judge(cold_paired, cold_v0, cold_v1),
        "warm": judge(warm_paired, warm_v0, warm_v1),
    }

    print()
    print("=" * 90)
    print("⚖️ 판정 — V1_log_ho 채택 가능?")
    print("=" * 90)
    for slice_name, j in judgement.items():
        mark = "✅" if j["v1_acceptable"] else "❌"
        passes = [k for k, val in j.items() if val and k != "v1_acceptable"]
        print(f"  {mark} {slice_name}: v1_acceptable={j['v1_acceptable']}, passes={passes}")

    final = judgement["cold"]["v1_acceptable"] and judgement["warm"]["v1_acceptable"]
    print(f"\n📌 최종 판정: {'V1_log_ho 채택 검토 가능' if final else 'V0 유지'}")

    # Save
    save = {
        "cold": {"v0": {k: v for k, v in cold_v0.items() if k != "ape_array"},
                 "v1": {k: v for k, v in cold_v1.items() if k != "ape_array"},
                 "paired": cold_paired},
        "warm": {"v0": {k: v for k, v in warm_v0.items() if k != "ape_array"},
                 "v1": {k: v for k, v in warm_v1.items() if k != "ape_array"},
                 "paired": warm_paired},
        "judgement": judgement,
        "final_v1_adoptable": bool(final),
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
