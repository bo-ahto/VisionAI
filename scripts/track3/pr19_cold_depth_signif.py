"""Track 3 PR19 — Cold model의 depth_cm 통계 유의성 5 seeds 재검증.

목적: 1회 release_split 검정에서 Cold + depth_cm 효과가 noise 수준 (CI [-0.007, +0.008]).
       이게 split-specific noise인지 구조적 결과인지 5 seeds로 확인.

설계:
  - PR18과 동일 mini hold-out (작가 100명 cold + warm 1건/작가)
  - Cold LAD만 학습 (Warm은 PR15에서 이미 유의 확인 — 재검증 불필요)
  - 비교: V0_no_depth (depth_cm 제외) vs V0_cm_only (현 운영)
  - 5 seeds × 2 models = 10 학습
  - Paired metric: row-level delta + bootstrap CI + seed-level sign + WinRate

판단 기준 (Codex 권고 3개):
  ① mean/median improvement ≈ 0 (CI 0 포함)
  ② seed 다수에서 win rate < 0.5
  ③ Cohen's d < 0.05

  3개 모두 만족 → Cold에서 depth_cm 제거 권고
  하나라도 미충족 → 현 v1.2 유지

산출물: data/track3_pr19_cold_depth_signif.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_pr19_cold_depth_signif.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [42, 123, 7, 2024, 999]
N_COLD_MINI = 100
WARM_PER_ARTIST = 1   # warm_mini는 안 쓰지만 mini-train 구성용으로 동일 protocol 유지

BASE_NO_DEPTH = ["medium_category", "support_category",
                  "log_area", "estimated_ho", "orientation",
                  "medium_ho_bucket", "artist_works_log", "aspect_ratio"]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]


def make_features(df, counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(counts).fillna(0))
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


def setup_mini_holdout(train_df, seed):
    """PR18과 동일 protocol. Stable sort + strata assert."""
    train_df = train_df.sort_values(
        by=[ARTIST_COL, "ln_price_krw_unified", "log_area"], kind="mergesort"
    ).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    counts = train_df.groupby(ARTIST_COL).size().sort_values()
    low = sorted([a for a in counts.index if counts[a] <= 2])
    mid = sorted([a for a in counts.index if 3 <= counts[a] <= 10])
    high = sorted([a for a in counts.index if counts[a] > 10])
    n_low = int(N_COLD_MINI * 0.5)
    n_mid = int(N_COLD_MINI * 0.3)
    n_high = N_COLD_MINI - n_low - n_mid
    assert len(low) >= n_low and len(mid) >= n_mid and len(high) >= n_high, \
        "strata 부족 (현 데이터에선 충분)"
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
    mini_train = remaining.drop(warm_idx).copy()
    cold_mini["is_3d"] = (cold_mini["depth_cm"] > 0).astype(int)
    return mini_train, cold_mini


def train_predict_cold(mini_train, cold_mini, include_depth_cm):
    """LAD Cold model 학습 + cold_mini 예측. Returns ape_array, predictions."""
    feats = BASE_NO_DEPTH + (["depth_cm"] if include_depth_cm else [])
    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts)
    te = make_features(cold_mini, counts)

    # Cold-start 조건 확인: cold_mini 작가는 mini_train에 없어야 함
    overlap = set(cold_mini[ARTIST_COL]) & set(mini_train[ARTIST_COL])
    assert not overlap, f"Cold-start 위반: {len(overlap)} artists overlap"

    model = build_lad(feats, BASE_CAT)
    model.fit(tr[feats], tr[TARGET].values)
    pred = model.predict(te[feats])

    y_true = np.exp(cold_mini[TARGET].values)
    y_pred = np.exp(pred)
    ape = np.abs(y_pred - y_true) / y_true
    return ape, pred


def paired_stats(ape_baseline, ape_variant):
    """Paired comparison + bootstrap CI."""
    ape_b = np.array(ape_baseline)
    ape_v = np.array(ape_variant)
    delta = ape_v - ape_b
    # bootstrap mean delta CI
    rng = np.random.default_rng(0)
    boots = [np.mean(rng.choice(delta, size=len(delta), replace=True))
             for _ in range(2000)]
    ci_low = float(np.percentile(boots, 2.5))
    ci_high = float(np.percentile(boots, 97.5))
    return {
        "n": int(len(delta)),
        "mean_delta": float(np.mean(delta)),
        "median_delta": float(np.median(delta)),
        "win_rate_variant": float((ape_v < ape_b).mean()),
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "cohen_d": float(np.mean(delta) / np.std(delta, ddof=1)) if np.std(delta, ddof=1) > 0 else 0.0,
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR19 — Cold + depth_cm 통계 유의성 5 seeds 재검증")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    seed_results = {}
    for seed in SEEDS:
        logger.info(f"\n=== Seed {seed} ===")
        mini_train, cold_mini = setup_mini_holdout(train, seed)
        logger.info(f"  mini_train {len(mini_train):,} / cold_mini {len(cold_mini):,} "
                    f"(2D={int((cold_mini['is_3d']==0).sum())}, 3D={int((cold_mini['is_3d']==1).sum())})")

        ape_nd, _ = train_predict_cold(mini_train, cold_mini, include_depth_cm=False)
        ape_cm, _ = train_predict_cold(mini_train, cold_mini, include_depth_cm=True)

        # Overall
        overall = paired_stats(ape_nd, ape_cm)
        overall["med_ape_no_depth"] = float(np.median(ape_nd))
        overall["med_ape_cm_only"] = float(np.median(ape_cm))

        # 2D / 3D slice
        is3d = cold_mini["is_3d"].values
        slice_2d = paired_stats(ape_nd[is3d == 0], ape_cm[is3d == 0]) if (is3d == 0).any() else None
        slice_3d = paired_stats(ape_nd[is3d == 1], ape_cm[is3d == 1]) if (is3d == 1).any() else None
        if slice_2d:
            slice_2d["med_ape_no_depth"] = float(np.median(ape_nd[is3d == 0]))
            slice_2d["med_ape_cm_only"] = float(np.median(ape_cm[is3d == 0]))
        if slice_3d:
            slice_3d["med_ape_no_depth"] = float(np.median(ape_nd[is3d == 1]))
            slice_3d["med_ape_cm_only"] = float(np.median(ape_cm[is3d == 1]))

        logger.info(f"  overall  med_APE: nd={overall['med_ape_no_depth']:.4f}, "
                    f"cm={overall['med_ape_cm_only']:.4f}, Δmean={overall['mean_delta']:+.5f}, "
                    f"WR={overall['win_rate_variant']:.4f}")

        seed_results[str(seed)] = {
            "overall": overall,
            "cold_2d": slice_2d,
            "cold_3d": slice_3d,
            "ape_no_depth": ape_nd.tolist(),
            "ape_cm_only": ape_cm.tolist(),
            "is_3d": is3d.tolist(),
        }

    # ─── 5 seeds 종합 ───
    def aggregate(slice_name):
        means = [seed_results[str(s)][slice_name]["mean_delta"] for s in SEEDS if seed_results[str(s)][slice_name]]
        meds = [seed_results[str(s)][slice_name]["median_delta"] for s in SEEDS if seed_results[str(s)][slice_name]]
        wrs = [seed_results[str(s)][slice_name]["win_rate_variant"] for s in SEEDS if seed_results[str(s)][slice_name]]
        cohens = [seed_results[str(s)][slice_name]["cohen_d"] for s in SEEDS if seed_results[str(s)][slice_name]]
        return {
            "n_seeds": len(means),
            "mean_delta": (float(np.mean(means)), float(np.std(means))),
            "median_delta": (float(np.mean(meds)), float(np.std(meds))),
            "win_rate": (float(np.mean(wrs)), float(np.std(wrs))),
            "cohen_d": (float(np.mean(cohens)), float(np.std(cohens))),
            "n_seeds_negative_delta": sum(1 for m in means if m < 0),
            "n_seeds_wr_above_0.5": sum(1 for w in wrs if w > 0.5),
        }

    agg = {
        "overall": aggregate("overall"),
        "cold_2d": aggregate("cold_2d"),
        "cold_3d": aggregate("cold_3d"),
    }

    # ─── 판정 (Codex 권고 3 기준) ───
    def judge(a):
        mean_zero = abs(a["mean_delta"][0]) < 0.005 and a["mean_delta"][1] > abs(a["mean_delta"][0])
        wr_below = a["n_seeds_wr_above_0.5"] < 3
        small_d = abs(a["cohen_d"][0]) < 0.05
        return {
            "criterion1_mean_zero": mean_zero,
            "criterion2_wr_minority_above_0.5": wr_below,
            "criterion3_cohen_d_small": small_d,
            "depth_cm_제거_권고": mean_zero and wr_below and small_d,
        }

    judgement = {
        "overall": judge(agg["overall"]),
        "cold_2d": judge(agg["cold_2d"]),
        "cold_3d": judge(agg["cold_3d"]),
    }

    # 출력
    print()
    print("=" * 90)
    print("📊 PR19 — Cold + depth_cm 5 seeds 재검증 결과")
    print("=" * 90)

    for slice_name, a in agg.items():
        print(f"\n[{slice_name}]")
        print(f"  Mean delta (5 seeds): {a['mean_delta'][0]:+.5f} ± {a['mean_delta'][1]:.5f}")
        print(f"  Median delta (5 seeds): {a['median_delta'][0]:+.5f} ± {a['median_delta'][1]:.5f}")
        print(f"  WinRate (5 seeds): {a['win_rate'][0]:.4f} ± {a['win_rate'][1]:.4f}")
        print(f"  Cohen's d (5 seeds): {a['cohen_d'][0]:+.4f} ± {a['cohen_d'][1]:.4f}")
        print(f"  Seeds with delta<0 (cm better): {a['n_seeds_negative_delta']}/5")
        print(f"  Seeds with WinRate>0.5: {a['n_seeds_wr_above_0.5']}/5")

    print()
    print("=" * 90)
    print("⚖️ 판정 (Codex 3 기준)")
    print("=" * 90)
    for slice_name, j in judgement.items():
        print(f"\n[{slice_name}]")
        for k, v in j.items():
            mark = "✅" if v else "❌"
            print(f"  {mark} {k}: {v}")

    # Save
    save = {
        "seeds": SEEDS,
        "per_seed": {s: {k: v for k, v in r.items() if k not in ["ape_no_depth", "ape_cm_only", "is_3d"]}
                     for s, r in seed_results.items()},
        "aggregate_5seeds": agg,
        "judgement_codex_criteria": judgement,
    }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
