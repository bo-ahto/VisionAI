"""Stage 2 OLS Hedonic 1차 fit — Track 2 (Interpretable Challenger).

Core 5 / Main 7 / Sensitivity feature set 비교 + 3-seed LAO holdout.
numpy/scipy 직접 구현 (statsmodels Python 3.14 호환 회피).

연계 plan: docs/데이터클렌징_단계계획_20260506.md
연계 schedule: Week 2 (5/13~5/19) — feature set freeze 후보 검증
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage2_500x50.parquet"
RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 123, 7777]
TEST_SIZE = 0.20


def medium_family(category: str) -> str:
    if category == "oil":
        return "oil"
    if category == "acrylic":
        return "acrylic"
    if category in ("ink", "pigment", "watercolor"):
        return "paper"
    return "other"


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["medium_family"] = out["medium_category"].apply(medium_family)
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    return out


def build_design(
    df: pd.DataFrame, feature_set: str
) -> tuple[pd.DataFrame, pd.Series]:
    y = df["log_price"]

    if feature_set == "core5":
        cols_continuous = ["log_area", "year_made_centered", "career_stage"]
        cols_categorical = ["medium_family", "gallery_tier"]
    elif feature_set == "main7":
        cols_continuous = [
            "log_area",
            "year_made_centered",
            "career_stage",
            "log_artist_total_works",
            "career_age",
        ]
        cols_categorical = ["medium_family", "gallery_tier"]
    elif feature_set == "sensitivity":
        cols_continuous = [
            "log_area",
            "year_made_centered",
            "career_stage",
            "log_artist_total_works",
            "career_age",
            "ln_followers",
        ]
        cols_categorical = ["medium_family", "gallery_tier", "has_seoul"]
    else:
        raise ValueError(feature_set)

    X_cont = df[cols_continuous].copy()
    X_cat = pd.get_dummies(
        df[cols_categorical].astype(str), drop_first=True
    ).astype(int)
    X = pd.concat([X_cont, X_cat], axis=1)
    # Add constant
    X.insert(0, "const", 1.0)
    return X, y


class OLSResult:
    """경량 OLS 결과 — numpy 기반."""

    def __init__(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]):
        self.X = X
        self.y = y
        self.feature_names = feature_names
        self.n, self.k = X.shape
        # β̂ = (X'X)^-1 X'y
        XtX = X.T @ X
        self.XtX_inv = np.linalg.inv(XtX)
        self.beta = self.XtX_inv @ X.T @ y
        # residuals
        self.fitted = X @ self.beta
        self.resid = y - self.fitted
        # σ² = SSR / (n-k)
        ssr = (self.resid**2).sum()
        self.sigma2 = ssr / (self.n - self.k)
        # SE(β) = sqrt(diag(σ² (X'X)^-1))
        self.se = np.sqrt(np.diag(self.sigma2 * self.XtX_inv))
        # t-stat + p-value
        self.t = self.beta / self.se
        self.p = 2 * (1 - stats.t.cdf(np.abs(self.t), df=self.n - self.k))
        # R²
        ss_total = ((y - y.mean()) ** 2).sum()
        self.r_squared = 1 - ssr / ss_total
        self.adj_r_squared = 1 - (1 - self.r_squared) * (self.n - 1) / (
            self.n - self.k
        )
        # AIC / BIC (linear regression formulas)
        self.log_lik = (
            -self.n / 2 * (np.log(2 * np.pi) + np.log(ssr / self.n) + 1)
        )
        self.aic = 2 * self.k - 2 * self.log_lik
        self.bic = self.k * np.log(self.n) - 2 * self.log_lik

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        return X_new @ self.beta

    def coef_table(self) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "coef": self.beta,
                "se": self.se,
                "t": self.t,
                "p_value": self.p,
            },
            index=self.feature_names,
        )
        df["sig"] = df["p_value"].apply(
            lambda p: "***"
            if p < 0.001
            else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
        )
        return df


def fit_holdout(
    X: pd.DataFrame, y: pd.Series, groups: np.ndarray, seed: int
) -> dict:
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
    train_idx, test_idx = next(gss.split(X, y, groups))

    train_artists = set(groups[train_idx])
    test_artists = set(groups[test_idx])
    assert len(train_artists & test_artists) == 0

    X_tr = X.iloc[train_idx].values.astype(float)
    y_tr = y.iloc[train_idx].values.astype(float)
    X_te = X.iloc[test_idx].values.astype(float)
    y_te = y.iloc[test_idx].values.astype(float)

    model = OLSResult(X_tr, y_tr, list(X.columns))
    y_pred = model.predict(X_te)

    log_resid = y_te - y_pred
    mae_log = np.abs(log_resid).mean()

    pred_price = np.exp(y_pred)
    true_price = np.exp(y_te)
    ape = np.abs(pred_price - true_price) / true_price
    mdape = np.median(ape) * 100
    w30 = (ape <= 0.30).mean() * 100
    w50 = (ape <= 0.50).mean() * 100

    return {
        "seed": seed,
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "n_train_artists": int(len(train_artists)),
        "n_test_artists": int(len(test_artists)),
        "r_squared": float(model.r_squared),
        "adj_r_squared": float(model.adj_r_squared),
        "aic": float(model.aic),
        "bic": float(model.bic),
        "mae_log": float(mae_log),
        "mdape_pct": float(mdape),
        "w30_pct": float(w30),
        "w50_pct": float(w50),
        "n_features": X.shape[1] - 1,
    }


def run() -> dict:
    df = pd.read_parquet(DATA)
    logger.info(
        f"Loaded Stage 2: {len(df)} rows / {df['artist_slug'].nunique()} artists"
    )

    df_feat = make_features(df)
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    summary = {"feature_sets": {}}

    for fs in ["core5", "main7", "sensitivity"]:
        logger.info(f"\n=== Feature set: {fs} ===")
        X, y = build_design(df_feat, fs)
        logger.info(f"  Design: X={X.shape}, features={X.shape[1] - 1}")

        # Full-sample
        model_full = OLSResult(X.values.astype(float), y.values.astype(float), list(X.columns))
        coef_df = model_full.coef_table()
        coef_df.to_csv(RESULTS / f"stage2_coef_{fs}.csv", encoding="utf-8-sig")
        logger.info(
            f"  Full R² = {model_full.r_squared:.3f} / "
            f"Adj R² = {model_full.adj_r_squared:.3f}"
        )

        # 3-seed holdout
        seed_results = []
        for seed in SEEDS:
            res = fit_holdout(X, y, groups, seed)
            seed_results.append(res)
            logger.info(
                f"  seed={seed}: MdAPE={res['mdape_pct']:.1f}% / "
                f"W30={res['w30_pct']:.1f}% / W50={res['w50_pct']:.1f}% / "
                f"R²={res['r_squared']:.3f}"
            )

        agg = {
            metric: {
                "mean": float(np.mean([r[metric] for r in seed_results])),
                "std": float(np.std([r[metric] for r in seed_results])),
                "values": [r[metric] for r in seed_results],
            }
            for metric in [
                "mdape_pct",
                "w30_pct",
                "w50_pct",
                "r_squared",
                "adj_r_squared",
                "aic",
            ]
        }

        summary["feature_sets"][fs] = {
            "n_features": int(X.shape[1] - 1),
            "n_observations": int(len(y)),
            "full_r_squared": float(model_full.r_squared),
            "full_adj_r_squared": float(model_full.adj_r_squared),
            "seed_results": seed_results,
            "aggregate": agg,
        }

        logger.info(
            f"  → MdAPE mean ± std: {agg['mdape_pct']['mean']:.2f} ± "
            f"{agg['mdape_pct']['std']:.2f}%"
        )

    # 비교 표
    logger.info("\n" + "=" * 70)
    logger.info("Stage 2 OLS Hedonic — feature set 비교 (3-seed holdout)")
    logger.info("=" * 70)
    logger.info(
        f"{'feature_set':<13} {'n_feat':>6} "
        f"{'MdAPE %':>13} {'W30 %':>13} {'W50 %':>13} {'R²':>8}"
    )
    for fs in ["core5", "main7", "sensitivity"]:
        agg = summary["feature_sets"][fs]["aggregate"]
        n = summary["feature_sets"][fs]["n_features"]
        logger.info(
            f"{fs:<13} {n:>6} "
            f"{agg['mdape_pct']['mean']:>6.2f}±{agg['mdape_pct']['std']:>5.2f} "
            f"{agg['w30_pct']['mean']:>6.2f}±{agg['w30_pct']['std']:>5.2f} "
            f"{agg['w50_pct']['mean']:>6.2f}±{agg['w50_pct']['std']:>5.2f} "
            f"{agg['r_squared']['mean']:>6.3f}"
        )

    # Save
    with (RESULTS / "stage2_ols_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSummary saved: {(RESULTS / 'stage2_ols_summary.json').relative_to(ROOT)}"
    )

    return summary


if __name__ == "__main__":
    run()
