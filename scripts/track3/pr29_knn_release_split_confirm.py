"""Track 3 PR29 (F5 step 2-B step A) — KNN blend release_split test 최종 confirm.

실험 목적:
  PR28 frozen benchmark에서 knn10_a50/knn10_a70 유력 신호 발견 (median Δ -0.014/-0.011, WR 0.53/0.55).
  Cohen's d는 outlier 1건이 지배해서 부적합 (Codex 진단).
  release_split test_cold (3,561 rows)에서 최종 paired confirm.

데이터:
  - release_split/track3_train.csv (학습)
  - release_split/track3_test_cold.csv (평가)

비교 variants:
  - V0 (현 운영)
  - knn10_a50 (V0 50% + KNN 50%)
  - knn10_a70 (V0 70% + KNN 30%)

판정 (Codex 진단 반영 — Cohen's d 제외):
  Cold: median Δ < -0.005 + WR > 0.52 + tail risk OK (max_ape +rel ≤ 10%, p99 +rel ≤ 10%)
→ 만족 시 채택 후보 (v1.3 운영 검토)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_pr29_knn_confirm_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEED = 42

COLD_FEATS = ["medium_category", "support_category", "orientation",
               "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
               "medium_ho_bucket", "aspect_ratio", "artist_works_log"]
COLD_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

KNN_CAT = ["medium_category", "support_category", "orientation"]
KNN_NUM = ["log_area", "estimated_ho", "depth_cm"]
K = 10


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


def build_knn_features(df_train, df_test):
    scaler = StandardScaler().fit(df_train[KNN_NUM])
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(df_train[KNN_CAT])
    X_tr = np.hstack([scaler.transform(df_train[KNN_NUM]), ohe.transform(df_train[KNN_CAT])])
    X_te = np.hstack([scaler.transform(df_test[KNN_NUM]), ohe.transform(df_test[KNN_CAT])])
    return X_tr, X_te


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
    logger.info("Track 3 PR29 (F5-B step A) — KNN blend release_split test confirm")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    tc = pd.read_csv(SPLIT / "track3_test_cold.csv")
    logger.info(f"train {len(train):,} / test_cold {len(tc):,}")

    counts = train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(train, counts)
    cm = make_features(tc, counts)

    # V0 Cold LAD
    logger.info("[V0] Cold LAD 학습")
    lad = build_lad(COLD_FEATS, COLD_CAT)
    lad.fit(tr[COLD_FEATS], tr[TARGET].values)
    v0_pred_ln = lad.predict(cm[COLD_FEATS])

    # KNN (k=10)
    logger.info(f"KNN (k={K}) fit + lookup")
    X_tr, X_te = build_knn_features(tr, cm)
    nbrs = NearestNeighbors(n_neighbors=K, n_jobs=1).fit(X_tr)
    _, indices = nbrs.kneighbors(X_te)
    y_tr_ln = tr[TARGET].values
    knn_pred_ln = np.array([np.median(y_tr_ln[idx]) for idx in indices])

    # Variants
    y_true_ln = tc[TARGET].values
    variants = {
        "V0":         v0_pred_ln,
        "knn10_a50":  0.5 * v0_pred_ln + 0.5 * knn_pred_ln,
        "knn10_a70":  0.7 * v0_pred_ln + 0.3 * knn_pred_ln,
    }
    results = {n: compute_metrics(y_true_ln, p) for n, p in variants.items()}

    # Paired vs V0
    paired = {}
    for v in ["knn10_a50", "knn10_a70"]:
        paired[v] = paired_stats(results["V0"]["ape_array"], results[v]["ape_array"])

    # 판정 (Codex 진단: Cohen's d 제외, median + WR + tail)
    def judge(p, v0_m, v1_m):
        median_improved = p["median_delta"] < -0.005
        wr_strong = p["win_rate_variant"] > 0.52
        tail_p99_ok = abs(v1_m["p99_ape"] - v0_m["p99_ape"]) / max(v0_m["p99_ape"], 0.01) <= 0.10
        tail_max_ok = ((v1_m["max_ape"] - v0_m["max_ape"]) / max(v0_m["max_ape"], 0.01)) <= 0.10
        tail_10x_ok = abs(v1_m["pct_10x_errors"] - v0_m["pct_10x_errors"]) <= 0.005
        adoptable = median_improved and wr_strong and tail_p99_ok and tail_max_ok and tail_10x_ok
        return {
            "median_improved": median_improved,
            "wr_strong": wr_strong,
            "tail_p99_ok": tail_p99_ok,
            "tail_max_ok": tail_max_ok,
            "tail_10x_ok": tail_10x_ok,
            "adoptable": adoptable,
        }

    judgement = {v: judge(paired[v], results["V0"], results[v]) for v in paired}

    # ─── 출력 ───
    print()
    print("=" * 90)
    print(f"📊 PR29 — V0 vs KNN blend (release_split test_cold n={results['V0']['n']:,})")
    print("=" * 90)

    print()
    print(f"  {'Metric':<18} {'V0':>10} {'knn10_a50':>10} {'knn10_a70':>10}")
    for k in ["median_ape", "mape", "within_30pct", "within_50pct",
              "p95_ape", "p99_ape", "max_ape", "n_10x_errors", "pct_10x_errors"]:
        v0 = results["V0"][k]
        v50 = results["knn10_a50"][k]
        v70 = results["knn10_a70"][k]
        print(f"  {k:<18} {v0:>10.4f} {v50:>10.4f} {v70:>10.4f}")

    print()
    print("Paired vs V0:")
    print(f"  {'Variant':<14} {'med_Δ':>10} {'WR':>7} {'Cohen d':>9} {'CI95':>26} {'better_10pp':>13} {'worse_10pp':>13}")
    for v, p in paired.items():
        print(f"  {v:<14} {p['median_delta']:>+10.5f} {p['win_rate_variant']:>7.4f} "
              f"{p['cohen_d']:>+9.4f} [{p['ci95_low']:>+8.4f},{p['ci95_high']:>+8.4f}] "
              f"{p['n_v_better_by_10pp']:>13} {p['n_v_worse_by_10pp']:>13}")

    print()
    print("⚖️ 판정 (Codex 진단 반영: Cohen's d 제외)")
    for v, j in judgement.items():
        mark = "✅" if j["adoptable"] else "❌"
        passes = [k for k, val in j.items() if val and k != "adoptable"]
        print(f"  {mark} {v}: adoptable={j['adoptable']}, passes={passes}")

    any_adopt = any(j["adoptable"] for j in judgement.values())
    print(f"\n📌 {'KNN blend 채택 후보 → v1.3 운영 검토' if any_adopt else 'V0 유지'}")

    save = {
        "config": {"k": K, "variants": list(variants.keys())},
        "results": {v: {k: vv for k, vv in r.items() if k != "ape_array"}
                    for v, r in results.items()},
        "paired_vs_V0": paired,
        "judgement": judgement,
        "any_adoptable": bool(any_adopt),
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
