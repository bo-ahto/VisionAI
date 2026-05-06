"""Stage 2 확장 feature 조합 테스트 — 의미 있는 변수 set 탐색.

테스트 카테고리:
A. Core 5 baseline
B. Size variants
C. Career variants
D. Artist meta additions
E. Gallery variants
F. Interactions
G. Minimal/Reduced
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
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_solo"] = np.log1p(out["solo_count"])
    out["log_group"] = np.log1p(out["group_count"])
    out["log_fair"] = np.log1p(out["fair_count"])
    out["medium_family"] = out["medium_category"].apply(medium_family)
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    # Interaction: log_area × medium_family
    return out


def build_design(
    df: pd.DataFrame,
    cont: list[str],
    cat: list[str],
    interactions: list[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    parts = []
    if cont:
        parts.append(df[cont].copy())
    if cat:
        cat_df = pd.get_dummies(
            df[cat].astype(str), drop_first=True
        ).astype(float)
        parts.append(cat_df)
    X = pd.concat(parts, axis=1) if parts else pd.DataFrame()
    # Interactions
    if interactions:
        for c1, c2 in interactions:
            is_text = not pd.api.types.is_numeric_dtype(df[c2])
            if is_text:
                cat_dum = pd.get_dummies(
                    df[c2].astype(str), prefix=f"{c1}_x_{c2}", drop_first=True
                ).astype(float)
                for col in cat_dum.columns:
                    X[col] = df[c1].values.astype(float) * cat_dum[col].values
            else:
                X[f"{c1}_x_{c2}"] = (
                    df[c1].values.astype(float) * df[c2].values.astype(float)
                )
    X.insert(0, "const", 1.0)
    return X


def fit_predict(X_tr, y_tr, X_te):
    beta, *_ = np.linalg.lstsq(X_tr, y_tr, rcond=None)
    return X_te @ beta


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
        pred = fit_predict(Xtr, ytr, Xte)
        ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
        mdapes.append(np.median(ape) * 100)
        w30s.append((ape <= 0.30).mean() * 100)
        w50s.append((ape <= 0.50).mean() * 100)
        ssr = ((yte - pred) ** 2).sum()
        sst = ((yte - yte.mean()) ** 2).sum()
        r2s.append(1 - ssr / sst if sst > 0 else 0)
    return {
        "mdape": (float(np.mean(mdapes)), float(np.std(mdapes))),
        "w30": (float(np.mean(w30s)), float(np.std(w30s))),
        "w50": (float(np.mean(w50s)), float(np.std(w50s))),
        "r2": (float(np.mean(r2s)), float(np.std(r2s))),
    }


def vif_max(X: pd.DataFrame) -> float:
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


# Feature 조합 정의
SETS = {
    # === A. Core 5 baseline ===
    "A_core5": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
    },
    # === B. Size variants ===
    "B1_area_aspect": {
        "cont": ["log_area", "aspect_ratio", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "B2_area_only_no_year": {
        "cont": ["log_area", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
    },
    # === C. Career variants ===
    "C1_career_age": {
        "cont": ["log_area", "year_made_centered", "career_age"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "C2_career_both": {
        "cont": ["log_area", "year_made_centered", "career_stage", "career_age"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "C3_birth_year": {
        "cont": ["log_area", "year_made_centered", "career_stage", "artist_birth_year"],
        "cat": ["medium_family", "gallery_tier"],
    },
    # === D. Artist meta +1 ===
    "D1_total_works": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "log_artist_total_works",
        ],
        "cat": ["medium_family", "gallery_tier"],
    },
    "D2_followers": {
        "cont": ["log_area", "year_made_centered", "career_stage", "ln_followers"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "D3_solo": {
        "cont": ["log_area", "year_made_centered", "career_stage", "log_solo"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "D4_for_sale": {
        "cont": ["log_area", "year_made_centered", "career_stage", "for_sale_ratio"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "D5_request": {
        "cont": ["log_area", "year_made_centered", "career_stage", "request_ratio"],
        "cat": ["medium_family", "gallery_tier"],
    },
    # === E. Gallery variants ===
    "E1_seoul_only": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "has_seoul"],
    },
    "E2_intl_only": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "has_international"],
    },
    "E3_city_count": {
        "cont": [
            "log_area", "year_made_centered", "career_stage", "gallery_city_count",
        ],
        "cat": ["medium_family", "gallery_tier"],
    },
    "E4_tier_seoul": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier", "has_seoul"],
    },
    # === F. Interactions ===
    "F1_area_x_medium": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
        "inter": [("log_area", "medium_family")],
    },
    # === G. Minimal/Reduced ===
    "G1_minimal_3": {
        "cont": ["log_area", "career_stage"],
        "cat": ["medium_family"],
    },
    "G2_no_year": {
        "cont": ["log_area", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
    },
    "G3_no_career": {
        "cont": ["log_area", "year_made_centered"],
        "cat": ["medium_family", "gallery_tier"],
    },
    # === H. Top 6 best variables ===
    "H1_top6": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "log_artist_total_works",
        ],
        "cat": ["medium_family", "gallery_tier", "has_seoul"],
    },
    "H2_top7": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "log_artist_total_works", "log_solo",
        ],
        "cat": ["medium_family", "gallery_tier"],
    },
}


def run() -> dict:
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    logger.info(
        f"Stage 2: {len(df)} rows / {df['artist_slug'].nunique()} artists / "
        f"{N_SEEDS}-seed LAO"
    )
    logger.info("=" * 95)
    logger.info(
        f"{'set':<28} {'k':>3} {'MdAPE%':>14} {'W30%':>7} {'W50%':>7} "
        f"{'R²':>10} {'VIF':>6}"
    )
    logger.info("-" * 95)

    summary = {}
    for name, fs in SETS.items():
        X = build_design(
            df_feat, fs["cont"], fs["cat"], fs.get("inter")
        )
        result = lao_holdout(X, y, groups, N_SEEDS)
        max_vif = vif_max(X)

        mdape_m, mdape_s = result["mdape"]
        r2_m, r2_s = result["r2"]
        vif_str = f"{max_vif:.1f}" if not np.isinf(max_vif) else "inf"

        logger.info(
            f"{name:<28} {X.shape[1] - 1:>3} "
            f"{mdape_m:>6.2f}±{mdape_s:>5.2f} "
            f"{result['w30'][0]:>6.2f} "
            f"{result['w50'][0]:>6.2f} "
            f"{r2_m:>6.3f}±{r2_s:.3f} "
            f"{vif_str:>5}"
        )

        summary[name] = {
            "n_features": int(X.shape[1] - 1),
            "mdape_mean": mdape_m,
            "mdape_std": mdape_s,
            "w30": result["w30"][0],
            "w50": result["w50"][0],
            "r2_mean": r2_m,
            "r2_std": r2_s,
            "max_vif": float(max_vif) if not np.isinf(max_vif) else None,
            "features_continuous": fs["cont"],
            "features_categorical": fs["cat"],
            "interactions": fs.get("inter", []),
        }

    logger.info("=" * 95)

    # 정렬 (mdape 기준)
    sorted_sets = sorted(
        summary.items(), key=lambda x: x[1]["mdape_mean"]
    )
    logger.info("\n=== Top 5 (MdAPE 기준) ===")
    for name, s in sorted_sets[:5]:
        logger.info(
            f"  {name}: k={s['n_features']} / "
            f"MdAPE={s['mdape_mean']:.2f}±{s['mdape_std']:.2f}% / "
            f"R²={s['r2_mean']:.3f} / VIF={s['max_vif']:.1f}"
        )

    with (RESULTS / "stage2_feature_extensive.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage2_feature_extensive.json').relative_to(ROOT)}"
    )
    return summary


if __name__ == "__main__":
    run()
