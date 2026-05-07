"""Track 2 Baseline Sample Size + Composition Sensitivity Descriptive Analysis.

Mini-freeze: docs/sample_size_sensitivity_freeze_20260507.md (2026-05-07)
- Datasets: stage1_200x20 / stage2_500x50 / stage3_1000x100 / stage4_full
- Model: F4 + spline + Huber (track2_v1_20260507 운영 baseline)
- Split: artist-level LAO 20% holdout / 100-seed
- Metrics: Overall / Low / Mid-high MdAPE (descriptive — hard gate X)
  + Newly-warm = stage4 only
- 100-seed mean + median + std + IQR

코덱스 framing 톤: "sample size + composition sensitivity descriptive analysis"
(baseline 검증 X, decision-binding X, spec 변경 단독 trigger X).
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent.parent
CURATED = ROOT / "data" / "curated"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
N_SEEDS = 100

DATASETS = [
    ("stage1_200x20", CURATED / "stage1_200x20.parquet"),
    ("stage2_500x50", CURATED / "stage2_500x50.parquet"),
    ("stage3_1000x100", CURATED / "stage3_1000x100.parquet"),
    ("stage4_full", CURATED / "stage4_full.parquet"),
]
STAGE3 = CURATED / "stage3_1000x100.parquet"


def restricted_cubic_spline(x, knots):
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(len(knots) - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def build_f4_spline(df, knots=None):
    """F4 + log_area spline (운영 baseline 동일)."""
    out = df[["log_area", "birth_year_centered", "log_artist_total_works"]].copy().reset_index(drop=True)
    if knots is None:
        knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    out["log_area_spline"] = sp[:, 0]
    return out, knots


def fit_huber(Xtr, ytr, Xte):
    if len(ytr) < 5:
        return np.full(len(Xte), float(np.mean(ytr) if len(ytr) else 0.0))
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr, ytr)
    return Xte @ m.coef_ + m.intercept_


def mdape_log(yte, pred):
    if len(yte) == 0:
        return None
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def lao_split(df, seed):
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    return ~df["artist_slug"].isin(test_artists).values, df["artist_slug"].isin(test_artists).values


def eval_one_seed(df, y, seed, stage3_artists, dataset_name):
    train_mask, test_mask = lao_split(df, seed)
    df_tr = df[train_mask].reset_index(drop=True)
    df_te = df[test_mask].reset_index(drop=True)
    if len(df_tr) < 50 or len(df_te) < 5:
        return None

    feat_tr, knots = build_f4_spline(df_tr)
    feat_te, _ = build_f4_spline(df_te, knots=knots)
    y_tr = y[train_mask].values.astype(float)
    y_te = y[test_mask].values.astype(float)

    pred = fit_huber(feat_tr.values, y_tr, feat_te.values)

    is_low_te = (df_te["price_krw"].values < LOW_PRICE_KRW)
    overall = mdape_log(y_te, pred)
    low = mdape_log(y_te[is_low_te], pred[is_low_te]) if is_low_te.sum() else None
    high = mdape_log(y_te[~is_low_te], pred[~is_low_te]) if (~is_low_te).sum() else None

    # Newly-warm = stage4 only (코덱스 P0 — Stage 1/2/3 = curated cohort, Stage 3 cohort 기준 newly-warm 정의 부적합 → N/A)
    newly = None
    if dataset_name == "stage4_full":
        is_newly_warm_te = ~df_te["artist_slug"].isin(stage3_artists).values
        if is_newly_warm_te.sum():
            newly = mdape_log(y_te[is_newly_warm_te], pred[is_newly_warm_te])

    return {
        "seed": seed,
        "n_train": int(train_mask.sum()),
        "n_test": int(test_mask.sum()),
        "overall": overall,
        "low": low,
        "high": high,
        "newly_warm": newly,
    }


BIRTH_YEAR_CENTER = 1977.44  # stage4_full artist_birth_year mean — 운영 baseline 일관성


def ensure_derived_columns(df):
    """Stage 1/2/3 schema 에는 derived columns 없음 — 운영 spec 일관성 위해 계산."""
    if "log_price" not in df.columns:
        df = df.copy()
        df["log_price"] = np.log(df["price_krw"].astype(float))
    if "log_area" not in df.columns:
        df["log_area"] = np.log(df["area_cm2"].astype(float))
    if "birth_year_centered" not in df.columns:
        df["birth_year_centered"] = df["artist_birth_year"].astype(float) - BIRTH_YEAR_CENTER
    if "log_artist_total_works" not in df.columns:
        df["log_artist_total_works"] = np.log(df["artist_total_works"].astype(float))
    return df


def run_dataset(name, path, stage3_artists):
    df = pd.read_parquet(path)
    df = ensure_derived_columns(df)
    y = df["log_price"]

    n_artists = df.artist_slug.nunique()
    logger.info(f"\n=== {name} | rows {len(df):,} | artists {n_artists} ===")

    seed_results = []
    skipped = 0
    for s in range(N_SEEDS):
        try:
            r = eval_one_seed(df, y, s, stage3_artists, name)
            if r is None:
                skipped += 1
                continue
            seed_results.append(r)
        except Exception as e:
            skipped += 1
            logger.warning(f"  seed {s} FAIL: {e}")

    if not seed_results:
        return None

    def stats(key):
        vals = [r[key] for r in seed_results if r.get(key) is not None]
        if not vals:
            return None
        arr = np.array(vals)
        return {
            "n": len(arr),
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
            "std": float(arr.std()),
            "iqr": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            "min": float(arr.min()),
            "max": float(arr.max()),
        }

    overall = stats("overall")
    low = stats("low")
    high = stats("high")
    newly = stats("newly_warm")

    logger.info(f"  Overall MdAPE: mean {overall['mean']:.2f}%, median {overall['median']:.2f}%, std {overall['std']:.2f}%, IQR {overall['iqr']:.2f}%")
    if low:
        logger.info(f"  Low MdAPE:     mean {low['mean']:.2f}%, median {low['median']:.2f}%, std {low['std']:.2f}%, IQR {low['iqr']:.2f}% (n_seeds {low['n']})")
    if high:
        logger.info(f"  Mid/high:      mean {high['mean']:.2f}%, median {high['median']:.2f}%, std {high['std']:.2f}%, IQR {high['iqr']:.2f}% (n_seeds {high['n']})")
    if newly:
        logger.info(f"  Newly-warm:    mean {newly['mean']:.2f}%, median {newly['median']:.2f}%, std {newly['std']:.2f}%, IQR {newly['iqr']:.2f}% (n_seeds {newly['n']})")
    else:
        logger.info(f"  Newly-warm:    N/A (코덱스 P0 — Stage 3 cohort 외 정의 부적합 / stage4 만 적용)")

    return {
        "name": name,
        "n_rows": len(df),
        "n_artists": int(n_artists),
        "n_seeds_completed": len(seed_results),
        "n_seeds_skipped": skipped,
        "overall": overall,
        "low": low,
        "high": high,
        "newly_warm": newly,
    }


def run():
    stage3_artists = set(pd.read_parquet(STAGE3)["artist_slug"].unique())
    logger.info("=" * 80)
    logger.info("Track 2 Baseline Sample Size + Composition Sensitivity Descriptive Analysis")
    logger.info("=" * 80)
    logger.info(f"Stage 3 cohort artists (newly-warm 정의용): {len(stage3_artists)}")
    logger.info("Model: F4 + spline + Huber (track2_v1_20260507 운영 baseline)")
    logger.info("Split: artist-level LAO 20% holdout / 100-seed")
    logger.info("Framing: descriptive only — hard gate / decision rule X (코덱스 P0)")

    summaries = {}
    for name, path in DATASETS:
        summaries[name] = run_dataset(name, path, stage3_artists)

    # 종합 표 출력
    logger.info("\n" + "=" * 80)
    logger.info("종합 표 (descriptive)")
    logger.info("=" * 80)
    logger.info(f"{'Dataset':<20s} {'Rows':>6s} {'Art':>5s} {'Overall':>8s} {'Std':>7s} {'IQR':>7s} {'Low':>8s} {'High':>8s} {'Newly':>8s}")
    for name, s in summaries.items():
        if not s:
            continue
        ov = s["overall"]
        lo = s["low"]
        hi = s["high"]
        nw = s["newly_warm"]
        ov_str = f"{ov['mean']:.2f}%" if ov else "N/A"
        std_str = f"{ov['std']:.2f}%" if ov else "N/A"
        iqr_str = f"{ov['iqr']:.2f}%" if ov else "N/A"
        lo_str = f"{lo['mean']:.2f}%" if lo else "N/A"
        hi_str = f"{hi['mean']:.2f}%" if hi else "N/A"
        nw_str = f"{nw['mean']:.2f}%" if nw else "N/A"
        logger.info(f"{name:<20s} {s['n_rows']:>6d} {s['n_artists']:>5d} {ov_str:>8s} {std_str:>7s} {iqr_str:>7s} {lo_str:>8s} {hi_str:>8s} {nw_str:>8s}")

    out = RESULTS / "sample_size_sensitivity.json"
    RESULTS.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
