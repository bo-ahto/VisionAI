"""Track 3 PR4 — Multi-seed Cold LAD (GroupShuffleSplit).

목적: Phase 5 5-fold GroupKFold는 deterministic이라 single estimate.
     Split uncertainty (작가 sampling variance) 정량화 필요.

설계:
- GroupShuffleSplit(n_splits=10, test_size=0.20, groups=artist) 10회 반복
- 매번 다른 작가 sampling → split variance 측정
- Bootstrap 95% CI 산출
- median APE 분포 + Phase 5 single estimate와 비교
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_pr4_multiseed_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
CAT_COLS = ["medium_category", "support_category", "orientation"]
N_SPLITS = 10  # GroupShuffleSplit 반복 횟수
TEST_SIZE = 0.20


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30))}


def build_lad():
    cat = [c for c in COLD_FEATURES if c in CAT_COLS]
    num = [c for c in COLD_FEATURES if c not in CAT_COLS]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", preprocess),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def bootstrap_ci(values, n_boot=5000, ci=0.95, seed=42):
    rng = np.random.default_rng(seed)
    boots = [np.median(rng.choice(values, size=len(values), replace=True))
             for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [(1-ci)*50, (1+ci)*50])
    return float(lo), float(hi)


def main():
    logger.info("=" * 70)
    logger.info(f"Track 3 PR4 — Multi-seed Cold LAD (GroupShuffleSplit × {N_SPLITS})")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    split_results = []
    for seed in range(N_SPLITS):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        train_idx, test_idx = next(gss.split(dev_df, groups=dev_df[ARTIST_COL]))
        tr_df = dev_df.iloc[train_idx]
        te_df = dev_df.iloc[test_idx]

        model = build_lad()
        model.fit(tr_df[COLD_FEATURES], tr_df[TARGET].values)
        pred = model.predict(te_df[COLD_FEATURES])

        m = compute_metrics(te_df[TARGET].values, pred)
        m["seed"] = seed
        m["n_test"] = int(len(test_idx))
        m["n_test_artists"] = int(te_df[ARTIST_COL].nunique())
        split_results.append(m)
        logger.info(f"  seed={seed}: med_APE={m['median_ape']:.3f}, "
                    f"W30={m['within_30pct']:.3f}, n={m['n_test']:,}, "
                    f"artists={m['n_test_artists']:,}")

    # Aggregate
    medians = [s["median_ape"] for s in split_results]
    mapes = [s["mape"] for s in split_results]
    w30s = [s["within_30pct"] for s in split_results]

    ci_lo, ci_hi = bootstrap_ci(medians)
    summary = {
        "n_splits": N_SPLITS,
        "test_size": TEST_SIZE,
        "per_split": split_results,
        "median_ape_mean": float(np.mean(medians)),
        "median_ape_std": float(np.std(medians)),
        "median_ape_min": float(np.min(medians)),
        "median_ape_max": float(np.max(medians)),
        "median_ape_95ci": [ci_lo, ci_hi],
        "mape_mean": float(np.mean(mapes)),
        "w30_mean": float(np.mean(w30s)),
        "w30_std": float(np.std(w30s)),
    }

    print()
    print("=" * 80)
    print(f"📊 PR4 — Multi-seed Cold LAD (GroupShuffleSplit × {N_SPLITS}, test 20%)")
    print("=" * 80)
    print()
    print(f"Phase 5 single 5-fold OOF: med_APE = 0.429 (95% CI [0.393, 0.540])")
    print(f"PR4 GroupShuffleSplit:      med_APE = {summary['median_ape_mean']:.3f}±{summary['median_ape_std']:.3f}")
    print(f"                            range [{summary['median_ape_min']:.3f}, {summary['median_ape_max']:.3f}]")
    print(f"                            95% CI bootstrap = [{ci_lo:.3f}, {ci_hi:.3f}]")
    print(f"                            W30 = {summary['w30_mean']:.3f}±{summary['w30_std']:.3f}")

    print()
    print("Per-split detail:")
    print(f"{'seed':>4} {'n_test':>7} {'artists':>7} {'med_APE':>8} {'MAPE':>7} {'W30':>7}")
    for s in split_results:
        print(f"{s['seed']:>4} {s['n_test']:>7,} {s['n_test_artists']:>7,} "
              f"{s['median_ape']:>8.3f} {s['mape']:>7.3f} {s['within_30pct']:>7.3f}")

    OUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
