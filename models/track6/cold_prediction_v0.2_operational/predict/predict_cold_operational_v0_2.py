#!/usr/bin/env python3
"""Cold prediction v0.2 (operational, search-free) — raw-input runnable predictor.

Unlike v0.1 (whose representative PP-Y18 depends on external search features),
this variant uses ONLY operational artwork features and serialized LightGBM
Quantile models, so it runs on raw inputs with NO external API dependency.

Inputs: a DataFrame with the 12 operational feature columns in FEATURES.
Outputs: quantile predictions, representative (q50), defense (guard blend toward
q40 for p95/MAPE safety), and a price range (q10..q90).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

BUNDLE = Path(__file__).resolve().parents[1]
MODELS_DIR = BUNDLE / "models"
CONFIG_DIR = BUNDLE / "config"

FEATURES = [
    "width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
    "has_depth", "is_3d_candidate", "medium_category", "support_category",
    "size_bucket", "support_size_bucket",
]
QUANTILES = ["q10", "q40", "q50", "q90"]


def load_models() -> dict:
    return {q: joblib.load(MODELS_DIR / f"lgbq_{q}.joblib") for q in QUANTILES}


def load_guard() -> dict:
    return json.loads((CONFIG_DIR / "guard_params_v0_2.json").read_text(encoding="utf-8"))


def predict(frame: pd.DataFrame, models: dict | None = None, guard: dict | None = None) -> pd.DataFrame:
    models = models or load_models()
    guard = guard or load_guard()
    x = frame[FEATURES]
    preds = {q: np.asarray(models[q].predict(x), dtype=float) for q in QUANTILES}

    width = preds["q90"] - preds["q10"]
    representative = preds["q50"]  # best-median point prediction

    base = representative
    comp = preds["q40"]
    w = float(guard["weight"])
    mask = (width >= float(guard["width_q67"])) & ((base - comp) >= float(guard["gap_q50"])) & (comp < base)
    defense = base.copy()
    defense[mask] = (1.0 - w) * base[mask] + w * comp[mask]

    out = frame.copy()
    for q in QUANTILES:
        out[f"{q}_pred_log"] = preds[q]
    out["qwidth_log"] = width
    out["representative_pred_log"] = representative
    out["defense_pred_log"] = defense
    out["representative_pred_price_krw"] = np.clip(np.exp(representative), 1_000.0, None)
    out["defense_pred_price_krw"] = np.clip(np.exp(defense), 1_000.0, None)
    out["range_low_price_krw"] = np.clip(np.exp(preds["q10"]), 1_000.0, None)
    out["range_high_price_krw"] = np.clip(np.exp(preds["q90"]), 1_000.0, None)
    return out


if __name__ == "__main__":
    print(f"Loaded cold v0.2 operational: models={list(load_models())}, guard={load_guard()}")
