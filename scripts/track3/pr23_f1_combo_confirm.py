"""Track 3 PR23 (F2 step A) — V0_base vs V0+medium_support_combo release_split confirm.

실험 목적:
  PR22 5 seeds mini hold-out에서 F1_combo (medium_support_combo 추가)가
  Cold에서 4/5 seeds 일관 개선 신호 (med_Δ -0.015, WR 0.547) 발견됨.
  release_split test 1회 paired comparison으로 최종 confirm.

판정 기준 (PR21 동일 형식):
  Cold: median Δ < -0.005 + WR > 0.52 + tail risk 유사 → 채택 가능
  Warm: 악화 없어야 (median Δ ≤ +0.005 + max_ape 변화 ≤ 10%)
  둘 다 만족 → V0 + medium_support_combo 채택 (v1.3 검토)

데이터: release_split/track3_train.csv (학습), test_warm/test_cold (평가)
산출물: data/track3_pr23_f1_combo_results.json
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
OUT_PATH = REPO / "data" / "track3_pr23_f1_combo_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEED = 42

# V0_base (현 운영)
V0_FEATS = ["medium_category", "support_category", "orientation",
             "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
             "medium_ho_bucket", "aspect_ratio", "artist_works_log"]
V0_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

# V0 + medium_support_combo
F1_FEATS = V0_FEATS + ["medium_support_combo"]
F1_CAT = V0_CAT + ["medium_support_combo"]

LGB_PARAMS = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
    "seed": SEED, "bagging_seed": SEED, "feature_fraction_seed": SEED,
    "data_random_seed": SEED, "drop_seed": SEED, "objective_seed": SEED,
}


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    df["medium_support_combo"] = (df["medium_category"].astype(str) + "_"
                                  + df["support_category"].astype(str))
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
    return lgb.train(LGB_PARAMS, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


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
        "n_10x_errors": int((ape > 1.0).sum()),
        "pct_10x_errors": float((ape > 1.0).mean()),
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
        "n_v_better_by_10pp": int(((ape_b - ape_v) > 0.1).sum()),
        "n_v_worse_by_10pp": int(((ape_v - ape_b) > 0.1).sum()),
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR23 (F2 step A) — V0_base vs V0+medium_support_combo confirm")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    tw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    tc = pd.read_csv(SPLIT / "track3_test_cold.csv")
    logger.info(f"train {len(train):,} / test_warm {len(tw):,} / test_cold {len(tc):,}")

    counts = train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(train, counts)
    cm = make_features(tc, counts)
    wm = make_features(tw, counts)

    # ── Cold (LAD) ──
    logger.info("\n[Cold] V0_base 학습...")
    lad_v0 = build_lad(V0_FEATS, V0_CAT)
    lad_v0.fit(tr[V0_FEATS], tr[TARGET].values)
    cold_pred_v0 = lad_v0.predict(cm[V0_FEATS])

    logger.info("[Cold] V0+combo 학습...")
    lad_f1 = build_lad(F1_FEATS, F1_CAT)
    lad_f1.fit(tr[F1_FEATS], tr[TARGET].values)
    cold_pred_f1 = lad_f1.predict(cm[F1_FEATS])

    y_cold_ln = tc[TARGET].values
    cold_v0 = compute_metrics(y_cold_ln, cold_pred_v0)
    cold_f1 = compute_metrics(y_cold_ln, cold_pred_f1)
    cold_paired = paired_stats(cold_v0["ape_array"], cold_f1["ape_array"])

    # ── Warm (LGB) ──
    logger.info("\n[Warm] V0_base 학습...")
    warm_v0_feats = V0_FEATS + [ARTIST_COL]
    warm_v0_cat = V0_CAT + [ARTIST_COL]
    lgb_v0 = train_lgb(tr, warm_v0_feats, warm_v0_cat)
    warm_pred_v0 = lgb_v0.predict(to_cat(wm, warm_v0_feats, warm_v0_cat))

    logger.info("[Warm] V0+combo 학습...")
    warm_f1_feats = F1_FEATS + [ARTIST_COL]
    warm_f1_cat = F1_CAT + [ARTIST_COL]
    lgb_f1 = train_lgb(tr, warm_f1_feats, warm_f1_cat)
    warm_pred_f1 = lgb_f1.predict(to_cat(wm, warm_f1_feats, warm_f1_cat))

    y_warm_ln = tw[TARGET].values
    warm_v0 = compute_metrics(y_warm_ln, warm_pred_v0)
    warm_f1 = compute_metrics(y_warm_ln, warm_pred_f1)
    warm_paired = paired_stats(warm_v0["ape_array"], warm_f1["ape_array"])

    # ── 출력 ──
    print()
    print("=" * 90)
    print("📊 PR23 — V0_base vs V0+medium_support_combo (release_split test, 1회 paired)")
    print("=" * 90)

    print(f"\n[Cold] (test_cold n={cold_v0['n']:,})")
    print(f"  {'Metric':<18} {'V0_base':>10} {'V0+combo':>10} {'Δ':>10}")
    for k in ["median_ape", "mape", "within_30pct", "within_50pct",
              "p95_ape", "p99_ape", "max_ape", "n_10x_errors", "pct_10x_errors"]:
        d = cold_f1[k] - cold_v0[k]
        print(f"  {k:<18} {cold_v0[k]:>10.4f} {cold_f1[k]:>10.4f} {d:>+10.4f}")
    print(f"  Paired: med_Δ={cold_paired['median_delta']:+.5f}, "
          f"WR={cold_paired['win_rate_variant']:.4f}, "
          f"catastrophic_2x={cold_paired['catastrophic_2x']:.4f}, "
          f"v_better_10pp={cold_paired['n_v_better_by_10pp']}, "
          f"v_worse_10pp={cold_paired['n_v_worse_by_10pp']}")

    print(f"\n[Warm] (test_warm n={warm_v0['n']:,})")
    print(f"  {'Metric':<18} {'V0_base':>10} {'V0+combo':>10} {'Δ':>10}")
    for k in ["median_ape", "mape", "within_30pct", "within_50pct",
              "p95_ape", "p99_ape", "max_ape", "n_10x_errors", "pct_10x_errors"]:
        d = warm_f1[k] - warm_v0[k]
        print(f"  {k:<18} {warm_v0[k]:>10.4f} {warm_f1[k]:>10.4f} {d:>+10.4f}")
    print(f"  Paired: med_Δ={warm_paired['median_delta']:+.5f}, "
          f"WR={warm_paired['win_rate_variant']:.4f}, "
          f"catastrophic_2x={warm_paired['catastrophic_2x']:.4f}, "
          f"v_better_10pp={warm_paired['n_v_better_by_10pp']}, "
          f"v_worse_10pp={warm_paired['n_v_worse_by_10pp']}")

    # ── 판정 ──
    def judge(paired, v0_m, v1_m, slice_name):
        if slice_name == "cold":
            # 개선 신호: median Δ < -0.005 + WR > 0.52 + tail risk 비슷
            median_improved = paired["median_delta"] < -0.005
            wr_strong = paired["win_rate_variant"] > 0.52
            tail_max_ok = abs(v1_m["max_ape"] - v0_m["max_ape"]) / max(v0_m["max_ape"], 0.01) <= 0.10
            tail_p99_ok = abs(v1_m["p99_ape"] - v0_m["p99_ape"]) / max(v0_m["p99_ape"], 0.01) <= 0.10
            tail_10x_ok = abs(v1_m["pct_10x_errors"] - v0_m["pct_10x_errors"]) <= 0.005
            adoptable = (median_improved and wr_strong and
                         tail_max_ok and tail_p99_ok and tail_10x_ok)
            return {
                "median_improved_for_cold": median_improved,
                "wr_strong_for_cold": wr_strong,
                "tail_max_similar": tail_max_ok,
                "tail_p99_similar": tail_p99_ok,
                "tail_10x_similar": tail_10x_ok,
                "adoptable": adoptable,
            }
        else:
            # Warm 악화 없으면 OK (median Δ >= -0.005 or 동등)
            no_worsening = paired["median_delta"] <= 0.005
            tail_max_ok = abs(v1_m["max_ape"] - v0_m["max_ape"]) / max(v0_m["max_ape"], 0.01) <= 0.10
            tail_10x_ok = abs(v1_m["pct_10x_errors"] - v0_m["pct_10x_errors"]) <= 0.005
            adoptable = no_worsening and tail_max_ok and tail_10x_ok
            return {
                "no_significant_worsening_warm": no_worsening,
                "tail_max_similar": tail_max_ok,
                "tail_10x_similar": tail_10x_ok,
                "adoptable": adoptable,
            }

    judgement = {
        "cold": judge(cold_paired, cold_v0, cold_f1, "cold"),
        "warm": judge(warm_paired, warm_v0, warm_f1, "warm"),
    }

    print()
    print("=" * 90)
    print("⚖️ 판정 — medium_support_combo 채택 가능?")
    print("=" * 90)
    for slice_name, j in judgement.items():
        mark = "✅" if j["adoptable"] else "❌"
        passes = [k for k, v in j.items() if v and k != "adoptable"]
        print(f"  {mark} {slice_name}: adoptable={j['adoptable']}, passes={passes}")

    final = judgement["cold"]["adoptable"] and judgement["warm"]["adoptable"]
    print(f"\n📌 최종 판정: {'F1_combo 채택 가능 (v1.3 검토)' if final else 'V0_base 유지'}")

    save = {
        "cold": {"v0": {k: v for k, v in cold_v0.items() if k != "ape_array"},
                 "v0_combo": {k: v for k, v in cold_f1.items() if k != "ape_array"},
                 "paired": cold_paired},
        "warm": {"v0": {k: v for k, v in warm_v0.items() if k != "ape_array"},
                 "v0_combo": {k: v for k, v in warm_f1.items() if k != "ape_array"},
                 "paired": warm_paired},
        "judgement": judgement,
        "final_adoptable": bool(final),
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
