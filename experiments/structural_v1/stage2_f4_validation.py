"""F4 추가 검증 (코덱스 Nit 4가지).

1. Artist-grouped K-fold CV (신규 작가 일반화)
2. 시기 분할 CV (시간 안정성)
3. Medium/tier level collapse 후 재시험
4. 잔차 분석 (고가 구간 편향)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage2_500x50.parquet"
RESULTS = Path(__file__).parent / "results"


def medium_family(c):
    if c == "oil":
        return "oil"
    if c == "acrylic":
        return "acrylic"
    if c in ("ink", "pigment", "watercolor"):
        return "paper"
    return "other"


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["medium_family"] = out["medium_category"].apply(medium_family)
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["birth_year_centered"] = (
        out["artist_birth_year"] - out["artist_birth_year"].mean()
    )
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    # binary collapse
    out["is_oil_or_acrylic"] = out["medium_family"].isin(["oil", "acrylic"]).astype(int)
    out["is_tier_high"] = (df["gallery_tier"].astype(str) == "2").astype(int)
    return out


def build_X(df, cont, cat=None):
    parts = [df[cont].copy()]
    if cat:
        parts.append(
            pd.get_dummies(df[cat].astype(str), drop_first=True).astype(float)
        )
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    return X


def fit_predict(Xtr, ytr, Xte):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return Xte @ beta, beta


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "w30": float((ape <= 0.30).mean() * 100),
        "w50": float((ape <= 0.50).mean() * 100),
    }


# F4 baseline cont
F4_CONT = ["log_area", "birth_year_centered", "log_artist_total_works"]


# ───────────────────────────────────────────
# 1. Artist-grouped K-fold CV
# ───────────────────────────────────────────
def kfold_grouped(df, y, groups, k_folds=10):
    """K-fold artist-grouped CV (다양한 fold 크기 / 작가 조합)."""
    X = build_X(df, F4_CONT)
    gkf = GroupKFold(n_splits=k_folds)
    fold_metrics = []
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups)):
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        pred, _ = fit_predict(Xtr, ytr, Xte)
        m = metrics(yte, pred)
        fold_metrics.append(m)

    summary = {
        metric: {
            "mean": float(np.mean([f[metric] for f in fold_metrics])),
            "std": float(np.std([f[metric] for f in fold_metrics])),
            "min": float(np.min([f[metric] for f in fold_metrics])),
            "max": float(np.max([f[metric] for f in fold_metrics])),
        }
        for metric in ["mdape", "w30", "w50"]
    }
    return summary, fold_metrics


# ───────────────────────────────────────────
# 2. 시기 분할 CV (시간 안정성)
# ───────────────────────────────────────────
def temporal_split(df, y):
    """제작연도 기준 train/test 분할."""
    X = build_X(df, F4_CONT)
    year_quantiles = df["year_made"].quantile([0.50, 0.70, 0.85])
    splits = {
        "≤2020 → 2021+": df["year_made"] <= 2020,
        "≤2022 → 2023+": df["year_made"] <= 2022,
        "≤2023 → 2024+": df["year_made"] <= 2023,
    }
    results = {}
    for name, train_mask in splits.items():
        tr = train_mask.values
        te = ~tr
        if te.sum() < 30 or tr.sum() < 30:
            continue
        Xtr = X[train_mask].values.astype(float)
        ytr = y[train_mask].values.astype(float)
        Xte = X[~train_mask].values.astype(float)
        yte = y[~train_mask].values.astype(float)
        pred, _ = fit_predict(Xtr, ytr, Xte)
        m = metrics(yte, pred)
        m["n_train"] = int(tr.sum())
        m["n_test"] = int(te.sum())
        results[name] = m
    return results


# ───────────────────────────────────────────
# 3. Medium/tier level collapse 후 재시험
# ───────────────────────────────────────────
def medium_tier_collapse(df, y, groups):
    """Medium/tier 합쳐서 binary 로 추가."""
    from sklearn.model_selection import GroupShuffleSplit

    sets = {
        "F4": (F4_CONT, []),
        "F4 + oil_or_acrylic": (F4_CONT + ["is_oil_or_acrylic"], []),
        "F4 + is_tier_high": (F4_CONT + ["is_tier_high"], []),
        "F4 + binary_both": (
            F4_CONT + ["is_oil_or_acrylic", "is_tier_high"],
            [],
        ),
    }
    results = {}
    for name, (cont, cat) in sets.items():
        X = build_X(df, cont, cat)
        mdapes = []
        for seed in range(42, 72):
            gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
            tr, te = next(gss.split(X, y, groups))
            Xtr = X.iloc[tr].values.astype(float)
            ytr = y.iloc[tr].values.astype(float)
            Xte = X.iloc[te].values.astype(float)
            yte = y.iloc[te].values.astype(float)
            pred, _ = fit_predict(Xtr, ytr, Xte)
            ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
            mdapes.append(np.median(ape) * 100)
        results[name] = {
            "mdape_mean": float(np.mean(mdapes)),
            "mdape_std": float(np.std(mdapes)),
            "n_features": int(X.shape[1] - 1),
        }
    return results


# ───────────────────────────────────────────
# 4. 잔차 분석 (가격대별 편향)
# ───────────────────────────────────────────
def residual_analysis(df, y, groups):
    """30-seed LAO 잔차의 가격대별 편향."""
    from sklearn.model_selection import GroupShuffleSplit

    X = build_X(df, F4_CONT)
    all_residuals = []
    all_true_log = []
    for seed in range(42, 72):
        gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        pred, _ = fit_predict(Xtr, ytr, Xte)
        all_residuals.extend((yte - pred).tolist())
        all_true_log.extend(yte.tolist())

    all_residuals = np.array(all_residuals)
    all_true_log = np.array(all_true_log)

    # 가격 분위별 잔차 평균/std
    prices = np.exp(all_true_log)
    quantiles = np.quantile(prices, [0.20, 0.40, 0.60, 0.80])
    bins = []
    cur_q = [-np.inf] + list(quantiles) + [np.inf]
    bin_labels = ["저가 (< 20%)", "20-40%", "40-60%", "60-80%", "고가 (>80%)"]
    seg_results = {}
    for i, label in enumerate(bin_labels):
        mask = (prices > cur_q[i]) & (prices <= cur_q[i + 1])
        if mask.sum() > 0:
            seg_residuals = all_residuals[mask]
            seg_results[label] = {
                "n": int(mask.sum()),
                "median_log_resid": float(np.median(seg_residuals)),
                "mean_log_resid": float(np.mean(seg_residuals)),
                "abs_mean_log_resid": float(np.mean(np.abs(seg_residuals))),
                "mdape_pct": float(
                    np.median(np.abs(np.exp(seg_residuals) - 1)) * 100
                ),
            }

    return seg_results, {
        "overall_mean_resid": float(np.mean(all_residuals)),
        "overall_std_resid": float(np.std(all_residuals)),
    }


# ───────────────────────────────────────────
# Main
# ───────────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    summary = {}

    logger.info("=" * 80)
    logger.info("1. Artist-grouped 10-fold CV (신규 작가 일반화)")
    logger.info("=" * 80)
    cv_summary, _ = kfold_grouped(df_feat, y, groups, k_folds=10)
    logger.info(f"  MdAPE: {cv_summary['mdape']['mean']:.2f}±{cv_summary['mdape']['std']:.2f}% "
                f"(min {cv_summary['mdape']['min']:.2f} / max {cv_summary['mdape']['max']:.2f})")
    logger.info(f"  W30: {cv_summary['w30']['mean']:.2f}±{cv_summary['w30']['std']:.2f}%")
    logger.info(f"  W50: {cv_summary['w50']['mean']:.2f}±{cv_summary['w50']['std']:.2f}%")
    summary["1_kfold_grouped_cv"] = cv_summary

    logger.info("\n" + "=" * 80)
    logger.info("2. 시기 분할 CV (시간 안정성)")
    logger.info("=" * 80)
    temporal = temporal_split(df_feat, y)
    for name, m in temporal.items():
        logger.info(
            f"  {name}: n_train={m['n_train']}, n_test={m['n_test']} → "
            f"MdAPE={m['mdape']:.2f}%, W30={m['w30']:.1f}%"
        )
    summary["2_temporal_split"] = temporal

    logger.info("\n" + "=" * 80)
    logger.info("3. Medium/tier level collapse 재시험")
    logger.info("=" * 80)
    collapse_results = medium_tier_collapse(df_feat, y, groups)
    for name, m in collapse_results.items():
        logger.info(
            f"  {name}: k={m['n_features']} → "
            f"MdAPE={m['mdape_mean']:.2f}±{m['mdape_std']:.2f}%"
        )
    summary["3_medium_tier_collapse"] = collapse_results

    logger.info("\n" + "=" * 80)
    logger.info("4. 잔차 분석 — 가격대별 편향")
    logger.info("=" * 80)
    seg_results, overall = residual_analysis(df_feat, y, groups)
    logger.info(
        f"  Overall: mean_resid={overall['overall_mean_resid']:.4f}, "
        f"std={overall['overall_std_resid']:.4f}"
    )
    logger.info(f"\n  {'segment':<20} {'n':>5} {'median_resid':>15} "
                f"{'abs_mean':>10} {'MdAPE':>8}")
    for name, m in seg_results.items():
        logger.info(
            f"  {name:<20} {m['n']:>5} "
            f"{m['median_log_resid']:>14.4f}  "
            f"{m['abs_mean_log_resid']:>9.4f} "
            f"{m['mdape_pct']:>6.2f}%"
        )
    summary["4_residual_analysis"] = {
        "overall": overall,
        "segments": seg_results,
    }

    with (RESULTS / "stage2_f4_validation.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage2_f4_validation.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
