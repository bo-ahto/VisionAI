"""career_age 변형 테스트 — birth_year vs career_age 비교.

핵심 가설:
- career_age 는 year_made 와 거의 독립 (-0.025 상관) → 추가 정보
- artist_birth_year 는 career_stage 와 강한 음의 상관 (-0.877) → 다중공선성
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage2_500x50.parquet"
RESULTS = Path(__file__).parent / "results"

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


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["medium_family"] = out["medium_category"].apply(medium_family)
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    return out


def build_design(df, cont, cat):
    parts = [df[cont].copy()] if cont else []
    if cat:
        parts.append(
            pd.get_dummies(df[cat].astype(str), drop_first=True).astype(float)
        )
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    return X


def lao_holdout(X, y, groups, n_seeds):
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
        beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
        pred = Xte @ beta
        ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
        mdapes.append(np.median(ape) * 100)
        w30s.append((ape <= 0.30).mean() * 100)
        w50s.append((ape <= 0.50).mean() * 100)
        ssr = ((yte - pred) ** 2).sum()
        sst = ((yte - yte.mean()) ** 2).sum()
        r2s.append(1 - ssr / sst if sst > 0 else 0)
    return {
        "mdape_m": float(np.mean(mdapes)),
        "mdape_s": float(np.std(mdapes)),
        "w30": float(np.mean(w30s)),
        "w50": float(np.mean(w50s)),
        "r2_m": float(np.mean(r2s)),
    }


def vif_max(X):
    cols = [c for c in X.columns if c != "const"]
    max_vif = 0.0
    for col in cols:
        Xj = X[cols].drop(columns=[col]).values.astype(float)
        Xj = np.column_stack([np.ones(len(Xj)), Xj])
        yj = X[col].values.astype(float)
        try:
            beta, *_ = np.linalg.lstsq(Xj, yj, rcond=None)
            yp = Xj @ beta
            ssr = ((yj - yp) ** 2).sum()
            sst = ((yj - yj.mean()) ** 2).sum()
            r2 = 1 - ssr / sst if sst > 0 else 0
            v = 1 / (1 - r2) if r2 < 0.9999 else float("inf")
            if not np.isinf(v):
                max_vif = max(max_vif, v)
        except Exception:
            pass
    return max_vif


SETS = {
    # Baseline
    "A_core5": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
        "note": "기존 baseline",
    },
    "C3_birth_year": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "artist_birth_year",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "note": "Core 5 + birth_year (이전 1위)",
    },
    # === career_age 변형 ===
    "N1_career_age_replace_year": {
        "cont": ["log_area", "career_age", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
        "note": "year_made → career_age 로 대체",
    },
    "N2_core5_plus_career_age": {
        "cont": [
            "log_area", "year_made_centered", "career_stage", "career_age",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "note": "Core 5 + career_age (둘 다 사용, 상관 -0.025)",
    },
    "N3_career_age_no_stage": {
        "cont": ["log_area", "year_made_centered", "career_age"],
        "cat": ["medium_family", "gallery_tier"],
        "note": "career_stage 빼고 career_age 만",
    },
    "N4_career_age_and_birth": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "career_age", "artist_birth_year",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "note": "Core 5 + career_age + birth_year (다 추가)",
    },
    "N5_career_age_replace_stage": {
        "cont": ["log_area", "year_made_centered", "career_age"],
        "cat": ["medium_family", "gallery_tier"],
        "note": "career_stage → career_age 대체",
    },
    "N6_birth_only_no_stage": {
        "cont": ["log_area", "year_made_centered", "artist_birth_year"],
        "cat": ["medium_family", "gallery_tier"],
        "note": "career_stage → birth_year 대체",
    },
    "N7_career_age_centered_year": {
        "cont": [
            "log_area", "year_made_centered", "career_stage", "career_age",
        ],
        "cat": ["medium_family", "gallery_tier", "has_seoul"],
        "note": "Core 5 + career_age + has_seoul",
    },
}


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    logger.info(f"Stage 2 — career_age 변형 ({N_SEEDS}-seed LAO)")
    logger.info("=" * 100)
    logger.info(
        f"{'set':<32} {'k':>3} {'MdAPE %':>13} {'W30':>6} {'W50':>6} "
        f"{'R²':>7} {'VIF':>6}  설명"
    )
    logger.info("-" * 100)

    summary = {}
    for name, fs in SETS.items():
        X = build_design(df_feat, fs["cont"], fs["cat"])
        result = lao_holdout(X, y, groups, N_SEEDS)
        max_vif = vif_max(X)

        logger.info(
            f"{name:<32} {X.shape[1] - 1:>3} "
            f"{result['mdape_m']:>6.2f}±{result['mdape_s']:>4.2f} "
            f"{result['w30']:>6.1f} {result['w50']:>6.1f} "
            f"{result['r2_m']:>6.3f} {max_vif:>5.1f}  {fs['note']}"
        )
        summary[name] = {
            "n_features": int(X.shape[1] - 1),
            **result,
            "max_vif": float(max_vif) if not np.isinf(max_vif) else None,
            "note": fs["note"],
        }

    logger.info("=" * 100)

    # Top 5
    sorted_sets = sorted(summary.items(), key=lambda x: x[1]["mdape_m"])
    logger.info("\n=== Top 5 ===")
    for name, s in sorted_sets[:5]:
        logger.info(
            f"  {name}: k={s['n_features']} / "
            f"MdAPE={s['mdape_m']:.2f}±{s['mdape_s']:.2f}% / "
            f"R²={s['r2_m']:.3f} / VIF={s['max_vif']:.1f}"
        )

    with (RESULTS / "stage2_career_age_test.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    run()
