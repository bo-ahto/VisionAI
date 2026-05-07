"""Stage 2 최종 후보 set 검증.

Forward selection winner + interaction 후보 비교.
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
    return out


def build_X(df, cont, cat, interactions=None):
    parts = [df[cont].copy()] if cont else []
    if cat:
        parts.append(
            pd.get_dummies(df[cat].astype(str), drop_first=True).astype(float)
        )
    X = pd.concat(parts, axis=1) if parts else pd.DataFrame()
    if interactions:
        for ia in interactions:
            if ia == "medium_x_tier":
                for med in ["oil", "paper", "other"]:
                    for tier in ["3", "4"]:
                        col = f"med_{med}_x_tier{tier}"
                        m1 = (df["medium_family"] == med).astype(float)
                        m2 = (df["gallery_tier"].astype(str) == tier).astype(float)
                        X[col] = (m1 * m2).values
    X.insert(0, "const", 1.0)
    return X


def lao_eval(X, y, groups, n_seeds=30):
    mdapes, w30s, w50s, r2s = [], [], [], []
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
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
        "r2": float(np.mean(r2s)),
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
    # 기존 baseline
    "A_core5": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
        "note": "기존 baseline",
    },
    # 이전 1위
    "C3_birth": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "birth_year_centered",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "note": "Core 5 + birth_year",
    },
    # ⭐ Forward winner
    "F1_forward_4": {
        "cont": [
            "log_area",
            "birth_year_centered",
            "log_artist_total_works",
            "career_stage",
        ],
        "cat": [],
        "note": "Forward winner — 4 cont only",
    },
    # Forward + medium
    "F2_forward_5_medium": {
        "cont": [
            "log_area",
            "birth_year_centered",
            "log_artist_total_works",
            "career_stage",
        ],
        "cat": ["medium_family"],
        "note": "Forward + medium_family",
    },
    # Forward + medium + tier
    "F3_forward_6": {
        "cont": [
            "log_area",
            "birth_year_centered",
            "log_artist_total_works",
            "career_stage",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "note": "Forward + medium + tier (full)",
    },
    # Forward without career_stage (since elastic net dropped it)
    "F4_no_stage": {
        "cont": [
            "log_area",
            "birth_year_centered",
            "log_artist_total_works",
        ],
        "cat": [],
        "note": "Forward 3 (no career_stage)",
    },
    # Forward + year (since elastic net loved year too)
    "F5_with_year": {
        "cont": [
            "log_area",
            "birth_year_centered",
            "log_artist_total_works",
            "career_stage",
            "year_made_centered",
        ],
        "cat": [],
        "note": "Forward + year_made",
    },
    # Interaction
    "I1_core_plus_med_tier": {
        "cont": ["log_area", "year_made_centered", "career_stage"],
        "cat": ["medium_family", "gallery_tier"],
        "interactions": ["medium_x_tier"],
        "note": "Core 5 + medium × tier interaction",
    },
    "I2_birth_plus_med_tier": {
        "cont": [
            "log_area", "year_made_centered", "career_stage",
            "birth_year_centered",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "interactions": ["medium_x_tier"],
        "note": "C3 + medium × tier",
    },
    "I3_forward_plus_med_tier": {
        "cont": [
            "log_area",
            "birth_year_centered",
            "log_artist_total_works",
            "career_stage",
        ],
        "cat": ["medium_family", "gallery_tier"],
        "interactions": ["medium_x_tier"],
        "note": "Forward + medium × tier",
    },
}


def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    logger.info(f"Stage 2 — 최종 후보 검증 ({N_SEEDS}-seed LAO)")
    logger.info("=" * 105)
    logger.info(
        f"{'set':<28} {'k':>3} {'MdAPE %':>13} {'W30':>6} {'W50':>6} "
        f"{'R²':>7} {'VIF':>6}  설명"
    )
    logger.info("-" * 105)

    summary = {}
    for name, fs in SETS.items():
        X = build_X(df_feat, fs["cont"], fs["cat"], fs.get("interactions"))
        result = lao_eval(X, y, groups, N_SEEDS)
        max_vif = vif_max(X)
        vif_str = f"{max_vif:.1f}" if not np.isinf(max_vif) else "inf"

        logger.info(
            f"{name:<28} {X.shape[1] - 1:>3} "
            f"{result['mdape_m']:>6.2f}±{result['mdape_s']:>4.2f} "
            f"{result['w30']:>6.1f} {result['w50']:>6.1f} "
            f"{result['r2']:>6.3f} {vif_str:>5}  {fs['note']}"
        )
        summary[name] = {
            "n_features": int(X.shape[1] - 1),
            **result,
            "max_vif": float(max_vif) if not np.isinf(max_vif) else None,
            "note": fs["note"],
        }

    logger.info("=" * 105)

    sorted_sets = sorted(summary.items(), key=lambda x: x[1]["mdape_m"])
    logger.info("\n=== Top 5 (MdAPE) ===")
    for name, s in sorted_sets[:5]:
        logger.info(
            f"  {name}: k={s['n_features']} / "
            f"MdAPE={s['mdape_m']:.2f}±{s['mdape_s']:.2f}% / "
            f"R²={s['r2']:.3f} / VIF={s['max_vif']:.1f}"
        )

    with (RESULTS / "stage2_final_candidates.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    run()
