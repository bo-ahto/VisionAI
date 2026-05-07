"""Stage 2 feature set 비교 — Core 5 vs Hedonic-5R + 변형들.

코덱스 권고 (ln_ho 가 area_cm2 보다 강함, medium_leaf 권고) 검증.
LAO split (artist-level holdout) + 30-seed 안정성 평가.
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

N_SEEDS = 30
TEST_SIZE = 0.20


def medium_family(c: str) -> str:
    if c == "oil":
        return "oil"
    if c == "acrylic":
        return "acrylic"
    if c in ("ink", "pigment", "watercolor"):
        return "paper"
    return "other"


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    # ln_ho 는 이미 데이터에 있음 (= log(ho))
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["medium_family"] = out["medium_category"].apply(medium_family)
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    return out


def build_design(df: pd.DataFrame, fs: dict) -> pd.DataFrame:
    """fs = {'continuous': [...], 'categorical': [...]}"""
    parts = []
    if fs["continuous"]:
        parts.append(df[fs["continuous"]].copy())
    if fs["categorical"]:
        cat = pd.get_dummies(
            df[fs["categorical"]].astype(str), drop_first=True
        ).astype(float)
        parts.append(cat)
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    return X


def fit_predict(X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray):
    beta, *_ = np.linalg.lstsq(X_tr, y_tr, rcond=None)
    return X_te @ beta, beta


def vif(X: pd.DataFrame) -> pd.Series:
    """간이 VIF (constant 제외)."""
    cols = [c for c in X.columns if c != "const"]
    vifs = {}
    for col in cols:
        Xj = X[cols].drop(columns=[col]).values.astype(float)
        Xj = np.column_stack([np.ones(len(Xj)), Xj])
        yj = X[col].values.astype(float)
        try:
            beta, *_ = np.linalg.lstsq(Xj, yj, rcond=None)
            yp = Xj @ beta
            ss_r = ((yj - yp) ** 2).sum()
            ss_t = ((yj - yj.mean()) ** 2).sum()
            r2 = 1 - ss_r / ss_t if ss_t > 0 else 0
            vifs[col] = 1 / (1 - r2) if r2 < 0.9999 else float("inf")
        except Exception:
            vifs[col] = float("nan")
    return pd.Series(vifs)


def lao_holdout(
    X: pd.DataFrame, y: pd.Series, groups: np.ndarray, n_seeds: int
) -> dict:
    mdapes, w30s, w50s, r2s = [], [], [], []
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(
            n_splits=1, test_size=TEST_SIZE, random_state=seed
        )
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        pred, _ = fit_predict(Xtr, ytr, Xte)

        true_p = np.exp(yte)
        pred_p = np.exp(pred)
        ape = np.abs(pred_p - true_p) / true_p
        mdapes.append(np.median(ape) * 100)
        w30s.append((ape <= 0.30).mean() * 100)
        w50s.append((ape <= 0.50).mean() * 100)

        # Test R² (1 - SSR/SS_total based on log scale)
        ssr = ((yte - pred) ** 2).sum()
        sst = ((yte - yte.mean()) ** 2).sum()
        r2s.append(1 - ssr / sst if sst > 0 else 0)

    return {
        "mdape_mean": float(np.mean(mdapes)),
        "mdape_std": float(np.std(mdapes)),
        "w30_mean": float(np.mean(w30s)),
        "w50_mean": float(np.mean(w50s)),
        "r2_mean": float(np.mean(r2s)),
        "r2_std": float(np.std(r2s)),
    }


# Feature set 정의
SETS = {
    "core5_area": {
        "continuous": ["log_area", "year_made_centered", "career_stage"],
        "categorical": ["medium_family", "gallery_tier"],
        "note": "현재 baseline — Core 5 with log_area",
    },
    "hedonic5R_ho": {
        "continuous": ["ln_ho", "year_made_centered", "career_stage"],
        "categorical": ["medium_family", "gallery_tier"],
        "note": "코덱스 권고 — log_area → ln_ho",
    },
    "hedonic5R_leaf": {
        "continuous": ["ln_ho", "year_made_centered", "career_stage"],
        "categorical": ["medium_leaf", "gallery_tier"],
        "note": "ln_ho + medium_leaf (세분화)",
    },
    "hedonic4_minimal": {
        "continuous": ["ln_ho", "year_made_centered", "career_stage"],
        "categorical": ["medium_family"],
        "note": "최소 4 — gallery_tier 제거",
    },
    "hedonic6_intl": {
        "continuous": ["ln_ho", "year_made_centered", "career_stage"],
        "categorical": ["medium_family", "has_international"],
        "note": "gallery_tier 대신 has_international",
    },
    "hedonic6_artist": {
        "continuous": [
            "ln_ho",
            "year_made_centered",
            "career_stage",
            "log_artist_total_works",
        ],
        "categorical": ["medium_family", "gallery_tier"],
        "note": "Main 7 변형 — ln_ho + total_works",
    },
}


def run() -> dict:
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    logger.info(
        f"Stage 2: {len(df)} rows / {df['artist_slug'].nunique()} artists / "
        f"{N_SEEDS}-seed LAO holdout"
    )
    logger.info("=" * 90)
    logger.info(
        f"{'set':<22} {'k':>3} {'MdAPE %':>14} {'W30 %':>7} {'W50 %':>7} {'R²':>10} {'maxVIF':>7}"
    )
    logger.info("-" * 90)

    summary = {}
    for name, fs in SETS.items():
        X = build_design(df_feat, fs)
        result = lao_holdout(X, y, groups, N_SEEDS)
        vif_series = vif(X)
        max_vif = vif_series[~np.isinf(vif_series)].max()

        logger.info(
            f"{name:<22} {X.shape[1] - 1:>3} "
            f"{result['mdape_mean']:>6.2f}±{result['mdape_std']:>5.2f} "
            f"{result['w30_mean']:>6.2f} "
            f"{result['w50_mean']:>6.2f} "
            f"{result['r2_mean']:>6.3f}±{result['r2_std']:.3f} "
            f"{max_vif:>6.2f}"
        )

        summary[name] = {
            "n_features": int(X.shape[1] - 1),
            "note": fs["note"],
            **result,
            "max_vif": float(max_vif),
            "vif": vif_series.round(2).to_dict(),
        }

    logger.info("=" * 90)

    with (RESULTS / "stage2_feature_compare.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage2_feature_compare.json').relative_to(ROOT)}"
    )

    return summary


if __name__ == "__main__":
    run()
