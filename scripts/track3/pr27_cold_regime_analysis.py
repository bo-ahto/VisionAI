"""Track 3 PR27 (F5 step 1) — Cold regime 분석.

실험 목적 (Codex 권고):
  Cold model이 어디서 깨지는지 1차원 + 2차원 slice 분해.
  결과로 F5 step 2 (retrieval/KNN residual / regime-specific fallback) 방향 결정.

데이터:
  - production v1.2 Cold LAD (이미 학습됨)
  - release_split/track3_test_cold.csv (3,561 rows / 200 작가)
  - unified v3 (source_platform 등 메타 lookup)

분석 축:
  1차원: source / medium / price_tertile / 2D-3D / ho_bucket
  2차원: source × medium / price_tertile × medium / 2D-3D × medium

판정: 단순 보고용. weak regime 식별이 목적이지 채택/reject 아님.
산출물: data/track3_pr27_cold_regime_results.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
PROD = REPO / "data" / "production"
UNIFIED = REPO / "data" / "track3_unified_v3.parquet"
OUT_PATH = REPO / "data" / "track3_pr27_cold_regime_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"

COLD_FEATS = ["medium_category", "support_category", "orientation",
               "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
               "medium_ho_bucket", "aspect_ratio", "artist_works_log"]


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def slice_stats(ape, label, n_total):
    """slice 통계."""
    n = len(ape)
    return {
        "label": label,
        "n": int(n),
        "share_pct": float(100 * n / n_total),
        "median_ape": float(np.median(ape)) if n > 0 else float("nan"),
        "mape": float(np.mean(ape)) if n > 0 else float("nan"),
        "within_30pct": float(np.mean(ape < 0.30)) if n > 0 else float("nan"),
        "within_50pct": float(np.mean(ape < 0.50)) if n > 0 else float("nan"),
        "p75_ape": float(np.percentile(ape, 75)) if n > 0 else float("nan"),
        "p95_ape": float(np.percentile(ape, 95)) if n > 0 else float("nan"),
        "max_ape": float(np.max(ape)) if n > 0 else float("nan"),
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR27 (F5 step 1) — Cold regime 분석")
    logger.info("=" * 70)

    # 데이터 로드
    train = pd.read_csv(SPLIT / "track3_train.csv")
    tc = pd.read_csv(SPLIT / "track3_test_cold.csv")
    counts = train[ARTIST_COL].value_counts().to_dict()
    logger.info(f"train {len(train):,} / test_cold {len(tc):,}")

    # source_platform lookup (release_split CSV에는 없음)
    unified = pd.read_parquet(
        UNIFIED,
        columns=[ARTIST_COL, TARGET, "width_cm", "height_cm", "source_platform"],
    )
    # test_cold는 release_split이라 source 컬럼 제거됨 → unified에서 lookup
    # key: (artist_name_ko, ln_price, width, height) 조합
    # 동일 key가 복수 source에 걸치는 경우가 있어, 유일 매핑만 사용한다.
    join_keys = [ARTIST_COL, TARGET, "width_cm", "height_cm"]
    src_lookup = (
        unified.groupby(join_keys, dropna=False)["source_platform"]
        .agg(lambda s: s.dropna().iloc[0] if s.dropna().nunique() == 1 else np.nan)
        .reset_index()
    )
    ambiguous_keys = int(src_lookup["source_platform"].isna().sum())
    tc = tc.merge(src_lookup, on=join_keys, how="left")
    src_coverage = tc["source_platform"].notna().mean()
    logger.info(f"source lookup coverage: {src_coverage:.1%} (ambiguous keys excluded: {ambiguous_keys})")

    # Cold model 로드 + 예측
    cold_model = joblib.load(PROD / "track3_cold_lad.joblib")
    cm_feat = make_features(tc, counts)
    cold_pred_ln = cold_model.predict(cm_feat[COLD_FEATS])
    y_true_ln = tc[TARGET].values
    y_true = np.exp(y_true_ln); y_pred = np.exp(cold_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    logger.info(f"\nOverall Cold med_APE: {np.median(ape):.4f}")

    n_total = len(ape)
    results = {"overall": slice_stats(ape, "overall", n_total)}

    # ─── 1차원 slice ───
    # Source
    results["by_source"] = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = (tc["source_platform"] == src).values
        if mask.sum() > 0:
            results["by_source"][src] = slice_stats(ape[mask], f"source={src}", n_total)

    # Medium
    results["by_medium"] = {}
    for med in tc["medium_category"].value_counts().index:
        mask = (tc["medium_category"] == med).values
        if mask.sum() >= 20:
            results["by_medium"][med] = slice_stats(ape[mask], f"medium={med}", n_total)

    # Price tertile (실제 가격 기준 — train 통계로 cut 도출)
    price_q33 = train[PRICE_COL].quantile(0.33)
    price_q67 = train[PRICE_COL].quantile(0.67)
    tc["price_tertile"] = pd.cut(tc[PRICE_COL], bins=[-1, price_q33, price_q67, 1e15],
                                   labels=["low", "mid", "high"])
    results["by_price_tertile"] = {}
    for tier in ["low", "mid", "high"]:
        mask = (tc["price_tertile"] == tier).values
        results["by_price_tertile"][tier] = slice_stats(ape[mask], f"price={tier}", n_total)

    # 2D / 3D
    results["by_2d_3d"] = {}
    for is_3d, label in [(0, "2D"), (1, "3D")]:
        mask = ((tc["depth_cm"] > 0).astype(int) == is_3d).values
        results["by_2d_3d"][label] = slice_stats(ape[mask], label, n_total)

    # ho_bucket
    tc["ho_bucket"] = pd.cut(tc["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    results["by_ho_bucket"] = {}
    for ho in ["0-5", "5-20", "20-50", "50+"]:
        mask = (tc["ho_bucket"] == ho).values
        if mask.sum() >= 20:
            results["by_ho_bucket"][ho] = slice_stats(ape[mask], f"ho={ho}", n_total)

    # ─── 2차원 cross-tab ───
    # source × medium
    results["source_x_medium"] = {}
    for src in ["artsy", "saatchi", "artue"]:
        for med in tc["medium_category"].value_counts().head(6).index:
            mask = ((tc["source_platform"] == src) & (tc["medium_category"] == med)).values
            if mask.sum() >= 10:
                key = f"{src} × {med}"
                results["source_x_medium"][key] = slice_stats(ape[mask], key, n_total)

    # price × medium
    results["price_x_medium"] = {}
    for tier in ["low", "mid", "high"]:
        for med in tc["medium_category"].value_counts().head(6).index:
            mask = ((tc["price_tertile"] == tier) & (tc["medium_category"] == med)).values
            if mask.sum() >= 10:
                key = f"price_{tier} × {med}"
                results["price_x_medium"][key] = slice_stats(ape[mask], key, n_total)

    # 2D/3D × medium
    results["2d3d_x_medium"] = {}
    for is_3d, label in [(0, "2D"), (1, "3D")]:
        for med in tc["medium_category"].value_counts().head(6).index:
            mask = (((tc["depth_cm"] > 0).astype(int) == is_3d) &
                    (tc["medium_category"] == med)).values
            if mask.sum() >= 10:
                key = f"{label} × {med}"
                results[f"2d3d_x_medium"][key] = slice_stats(ape[mask], key, n_total)

    # ─── 출력 ───
    print()
    print("=" * 90)
    print(f"📊 PR27 — Cold regime 분석 (test_cold n={n_total}, V0 baseline)")
    print(f"   Overall med_APE: {results['overall']['median_ape']:.4f}, W30: {results['overall']['within_30pct']:.4f}")
    print("=" * 90)

    def print_dict(title, d, sort_key="median_ape", top=None):
        print(f"\n[{title}]")
        items = sorted(d.items(), key=lambda x: x[1][sort_key], reverse=True)
        if top: items = items[:top]
        print(f"  {'Slice':<28} {'n':>6} {'share':>6} {'med_APE':>9} {'W30':>7} {'p95':>8} {'max':>10}")
        for label, s in items:
            print(f"  {label:<28} {s['n']:>6} {s['share_pct']:>5.1f}% "
                  f"{s['median_ape']:>9.4f} {s['within_30pct']:>7.4f} {s['p95_ape']:>8.4f} {s['max_ape']:>10.2f}")

    print_dict("Source", results["by_source"])
    print_dict("Medium (n≥20)", results["by_medium"])
    print_dict("Price tertile", results["by_price_tertile"])
    print_dict("2D vs 3D", results["by_2d_3d"])
    print_dict("Ho bucket", results["by_ho_bucket"])
    print_dict("Source × Medium (n≥10, worst 8)", results["source_x_medium"], top=8)
    print_dict("Price × Medium (n≥10, worst 8)", results["price_x_medium"], top=8)

    # ─── Weak regime 자동 식별 ───
    print()
    print("=" * 90)
    print("⚠️ Weak regimes (med_APE > overall × 1.5)")
    print("=" * 90)
    threshold = results["overall"]["median_ape"] * 1.5
    weak = []
    for category, d in results.items():
        if category == "overall" or not isinstance(d, dict): continue
        for label, s in d.items():
            if isinstance(s, dict) and "median_ape" in s and s["median_ape"] > threshold:
                weak.append({"category": category, "label": label, **s})
    weak.sort(key=lambda x: -x["median_ape"])
    print(f"  Overall × 1.5 = {threshold:.4f}")
    for w in weak[:15]:
        print(f"  [{w['category']:<18}] {w['label']:<28} n={w['n']:>4} "
              f"med_APE={w['median_ape']:.4f} share={w['share_pct']:.1f}%")

    results["weak_regimes_top15"] = weak[:15]
    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=float))
    logger.info(f"\n✅ Saved: {OUT_PATH}")

    # ─── F5 step 2 권고 ───
    print()
    print("=" * 90)
    print("📌 F5 step 2 권고 (Cold weak regime fallback)")
    print("=" * 90)
    print("위 weak regime을 기반으로 다음 fallback 전략 검토:")
    print("  1. Regime-specific median fallback: weak regime에 train 작가 median 가격 사용")
    print("  2. KNN retrieval residual: cold 작품에 최근접 train 작품 lookup")
    print("  3. Regime-specific Cold LAD: weak regime에 별도 학습된 cold model")


if __name__ == "__main__":
    main()
