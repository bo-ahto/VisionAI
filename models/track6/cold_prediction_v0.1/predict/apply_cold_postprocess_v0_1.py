#!/usr/bin/env python3
"""Cold prediction v0.1 post-processing layer (frozen).

Given the upstream component predictions for a Cold artwork, produce:
- representative point prediction  = PP-Y18 qwidth (passed through)
- MAPE/p95 defense prediction      = guard blend, validated by PP-QR4

The defense layer uses ONLY frozen parameters (thresholds + weight) stored in
``config/cold_postprocess_params_v0_1.json``. The underlying LightGBM Quantile
models that produce the component predictions are upstream (see reproduction/).

Inputs required per row:
- y18_qwidth_pred_log : PP-Y18 representative prediction (log KRW)
- lgb_q40_pred_log    : PP-QR1 LightGBM Quantile q40 prediction (log KRW)
- quantile_width_log  : prediction quantile width (log)

Frozen params:
- qwidth_q67 : validation 67th percentile of quantile_width_log
- gap_q50    : validation 50th percentile of (y18_qwidth - cat_q40) gap
- weight     : 0.50 (downward blend weight on the guard mask)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PARAMS_PATH = Path(__file__).resolve().parents[1] / "config" / "cold_postprocess_params_v0_1.json"


def load_params(path: Path = PARAMS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def representative_pred_log(y18_qwidth_pred_log: np.ndarray) -> np.ndarray:
    """Representative point prediction = PP-Y18 qwidth (unchanged)."""
    return np.asarray(y18_qwidth_pred_log, dtype=float)


def defense_pred_log(
    y18_qwidth_pred_log: np.ndarray,
    lgb_q40_pred_log: np.ndarray,
    quantile_width_log: np.ndarray,
    params: dict,
) -> np.ndarray:
    """MAPE/p95 defense guard blend using frozen validation thresholds."""
    base = np.asarray(y18_qwidth_pred_log, dtype=float)
    comp = np.asarray(lgb_q40_pred_log, dtype=float)
    qwidth = np.asarray(quantile_width_log, dtype=float)
    qwidth_q67 = float(params["thresholds"]["qwidth_q67"])
    gap_q50 = float(params["thresholds"]["gap_q50"])
    weight = float(params["weight"])
    mask = (qwidth >= qwidth_q67) & ((base - comp) >= gap_q50) & (comp < base)
    out = base.copy()
    out[mask] = (1.0 - weight) * base[mask] + weight * comp[mask]
    return out


def apply(frame: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
    """Add representative + defense prediction columns (log and KRW)."""
    params = params or load_params()
    out = frame.copy()
    rep = representative_pred_log(out["y18_qwidth_pred_log"].to_numpy(dtype=float))
    dfn = defense_pred_log(
        out["y18_qwidth_pred_log"].to_numpy(dtype=float),
        out["lgb_q40_pred_log"].to_numpy(dtype=float),
        out["quantile_width_log"].to_numpy(dtype=float),
        params,
    )
    out["cold_representative_pred_log"] = rep
    out["cold_defense_pred_log"] = dfn
    out["cold_representative_pred_price_krw"] = np.clip(np.exp(rep), 1_000.0, None)
    out["cold_defense_pred_price_krw"] = np.clip(np.exp(dfn), 1_000.0, None)
    return out


if __name__ == "__main__":
    print(f"Loaded frozen cold post-process params: {load_params()}")
