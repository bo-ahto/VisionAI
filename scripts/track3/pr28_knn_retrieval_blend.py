"""Track 3 PR28 (F5 step 2-B) — KNN retrieval residual blend for Cold.

실험 목적 (Codex 1순위 권고):
  Cold V0 prediction에 train K-NN 작품의 median price를 blend.
  weak regime (Artue, pigment/mixed/other, 고가) 보정 시도.

설계:
  - Frozen Cold Benchmark (F6 PR26) 사용: mini_train (34,108) + cold_mini (751)
  - KNN feature: OneHot(medium/support/orientation) + StandardScale(log_area/estimated_ho/depth_cm)
  - Variants (6 cells, 단일 가설 "KNN blend 도움?"):
      V0 (baseline)
      knn5_a50, knn10_a30, knn10_a50, knn10_a70, knn20_a50
  - 평가: paired vs V0 (ape_array)

판정 기준 (Codex 보수화):
  paired median Δ < -0.005 + WR > 0.52 + Cohen's d < -0.05 + tail risk OK
→ 만족 시 release_split confirm (PR29)

산출물: data/track3_pr28_knn_results.json
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

# Frozen loader
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.track3._frozen_loader import load_frozen_benchmark

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
OUT_PATH = REPO / "data" / "track3_pr28_knn_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"

COLD_FEATS = ["medium_category", "support_category", "orientation",
               "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
               "medium_ho_bucket", "aspect_ratio", "artist_works_log"]
COLD_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

# KNN feature subset
KNN_CAT = ["medium_category", "support_category", "orientation"]
KNN_NUM = ["log_area", "estimated_ho", "depth_cm"]

VARIANTS = {
    "V0":         None,           # baseline (KNN 없음)
    "knn5_a50":   (5,  0.5),
    "knn10_a30":  (10, 0.3),
    "knn10_a50":  (10, 0.5),
    "knn10_a70":  (10, 0.7),
    "knn20_a50":  (20, 0.5),
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


def build_knn_features(df_train, df_test):
    """KNN용 feature matrix: train fit + test transform."""
    scaler = StandardScaler().fit(df_train[KNN_NUM])
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(df_train[KNN_CAT])
    X_tr_num = scaler.transform(df_train[KNN_NUM])
    X_tr_cat = ohe.transform(df_train[KNN_CAT])
    X_tr = np.hstack([X_tr_num, X_tr_cat])
    X_te_num = scaler.transform(df_test[KNN_NUM])
    X_te_cat = ohe.transform(df_test[KNN_CAT])
    X_te = np.hstack([X_te_num, X_te_cat])
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


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR28 (F5 step 2-B) — KNN retrieval blend")
    logger.info("=" * 70)

    # Frozen benchmark 로드
    mini_train, cold_mini, baseline_cache = load_frozen_benchmark()
    logger.info(f"mini_train {len(mini_train):,} / cold_mini {len(cold_mini):,}")

    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts)
    cm = make_features(cold_mini, counts)

    # V0 Cold LAD 학습 + 예측 (PR26 동일하게 재학습 — deterministic이라 동일 결과)
    logger.info("[V0 baseline] Cold LAD 학습")
    lad = build_lad(COLD_FEATS, COLD_CAT)
    lad.fit(tr[COLD_FEATS], tr[TARGET].values)
    v0_pred_ln = lad.predict(cm[COLD_FEATS])

    # KNN feature 구축
    logger.info("KNN feature 구축")
    X_tr, X_te = build_knn_features(tr, cm)
    logger.info(f"  KNN feature shape: train {X_tr.shape}, test {X_te.shape}")

    # K-NN prediction (여러 k)
    y_tr_ln = tr[TARGET].values
    knn_preds_by_k = {}
    for k in sorted(set(cfg[0] for cfg in VARIANTS.values() if cfg is not None)):
        logger.info(f"  KNN (k={k}) fit + lookup")
        nbrs = NearestNeighbors(n_neighbors=k, n_jobs=1).fit(X_tr)
        distances, indices = nbrs.kneighbors(X_te)
        knn_preds_by_k[k] = np.array([np.median(y_tr_ln[idx]) for idx in indices])

    # Variants 평가
    y_true_ln = cold_mini[TARGET].values
    results = {}
    for v_name, cfg in VARIANTS.items():
        if cfg is None:
            pred = v0_pred_ln
        else:
            k, alpha = cfg
            pred = alpha * v0_pred_ln + (1 - alpha) * knn_preds_by_k[k]
        results[v_name] = compute_metrics(y_true_ln, pred)
        logger.info(f"  {v_name}: med_APE={results[v_name]['median_ape']:.4f}")

    # Paired vs V0
    paired = {}
    for v_name in VARIANTS:
        if v_name == "V0": continue
        paired[v_name] = paired_stats(results["V0"]["ape_array"], results[v_name]["ape_array"])
        paired[v_name]["max_ape_rel_delta"] = (
            (results[v_name]["max_ape"] - results["V0"]["max_ape"]) / max(results["V0"]["max_ape"], 0.01))

    # 판정
    def judge(p):
        median_improved = p["median_delta"] < -0.005
        wr_strong = p["win_rate_variant"] > 0.52
        cohen_strong = p["cohen_d"] < -0.05
        tail_ok = p["max_ape_rel_delta"] <= 0.10
        candidate = median_improved and wr_strong and cohen_strong and tail_ok
        return {
            "median_improved": median_improved, "wr_strong": wr_strong,
            "cohen_strong": cohen_strong, "tail_ok": tail_ok,
            "candidate_for_release_split_confirm": candidate,
        }

    judgements = {v: judge(paired[v]) for v in paired}

    # 출력
    print()
    print("=" * 90)
    print("📊 PR28 — Cold V0 vs KNN retrieval blend (frozen benchmark n=751)")
    print("=" * 90)
    print(f"\n{'Variant':<14} {'med_APE':>9} {'mape':>10} {'W30':>7} {'p95':>8} {'max':>10}")
    for v in VARIANTS:
        r = results[v]
        marker = " (baseline)" if v == "V0" else ""
        print(f"{v:<14} {r['median_ape']:>9.4f} {r['mape']:>10.4e} {r['within_30pct']:>7.4f} "
              f"{r['p95_ape']:>8.4f} {r['max_ape']:>10.2f}{marker}")

    print()
    print("=" * 90)
    print("Paired delta vs V0 baseline")
    print("=" * 90)
    print(f"{'Variant':<14} {'med_Δ':>10} {'WR':>7} {'Cohen d':>9} {'CI95':>26} {'max_rel_Δ':>11}")
    for v, p in paired.items():
        print(f"{v:<14} {p['median_delta']:>+10.5f} {p['win_rate_variant']:>7.4f} "
              f"{p['cohen_d']:>+9.4f} [{p['ci95_low']:>+7.4f},{p['ci95_high']:>+7.4f}] "
              f"{p['max_ape_rel_delta']:>+11.4f}")

    print()
    print("=" * 90)
    print("⚖️ 판정")
    print("=" * 90)
    any_cand = False
    for v, j in judgements.items():
        mark = "✅" if j["candidate_for_release_split_confirm"] else "❌"
        passes = [k for k, val in j.items() if val and k != "candidate_for_release_split_confirm"]
        print(f"  {mark} {v}: candidate={j['candidate_for_release_split_confirm']}, passes={passes}")
        if j["candidate_for_release_split_confirm"]: any_cand = True

    print(f"\n📌 {'release_split confirm 후보 발견 → F5-B step A 진행 (PR29)' if any_cand else 'V0 유지, A (regime fallback) 진행 검토'}")

    # Save
    save = {
        "variants": list(VARIANTS.keys()),
        "config": {v: cfg for v, cfg in VARIANTS.items()},
        "results": {v: {k: vv for k, vv in r.items() if k != "ape_array"}
                    for v, r in results.items()},
        "paired_vs_V0": paired,
        "judgement": judgements,
        "any_candidate_found": bool(any_cand),
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
