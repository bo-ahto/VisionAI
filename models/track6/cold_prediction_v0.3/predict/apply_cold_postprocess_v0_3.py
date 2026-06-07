#!/usr/bin/env python3
"""Cold prediction v0.3 post-processing layer (guard + search 2-layer defense).

Extends v0.1 (guard only) with the PP-H28/PP-COLD-DEFENSE1-validated search
correction layer, applied per artist with a coverage fallback:
- representative point = PP-Y18 qwidth (passed through)
- defense layer 1 (guard)  : blend toward lgb_q40 on qwidth/gap mask (PP-QR4)
- defense layer 2 (search) : add per-artist frozen search delta where the artist
                             is covered; otherwise guard-only (fallback)
- review flag              : low-confidence rows (no search prior OR wide interval)

The search delta lookup is a frozen per-artist snapshot derived from search
features; it is NOT live search. Underlying quantile models are upstream.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path(__file__).resolve().parents[1]
CONFIG_DIR = BUNDLE / "config"


def load_params() -> dict:
    return json.loads((CONFIG_DIR / "cold_postprocess_params_v0_3.json").read_text(encoding="utf-8"))


def load_search_lookup() -> dict:
    raw = json.loads((CONFIG_DIR / "search_delta_lookup_v0_3.json").read_text(encoding="utf-8"))
    return {str(k): float(v) for k, v in raw["artist_delta"].items()}


def guard_pred_log(y18: np.ndarray, lgb_q40: np.ndarray, qwidth: np.ndarray, params: dict) -> np.ndarray:
    qwidth_q67 = float(params["guard"]["qwidth_q67"])
    gap_q50 = float(params["guard"]["gap_q50"])
    w = float(params["guard"]["weight"])
    mask = (qwidth >= qwidth_q67) & ((y18 - lgb_q40) >= gap_q50) & (lgb_q40 < y18)
    out = y18.copy()
    out[mask] = (1.0 - w) * y18[mask] + w * lgb_q40[mask]
    return out


def apply(frame: pd.DataFrame, params: dict | None = None, lookup: dict | None = None) -> pd.DataFrame:
    params = params or load_params()
    lookup = load_search_lookup() if lookup is None else lookup

    y18 = frame["y18_qwidth_pred_log"].to_numpy(dtype=float)
    lgb_q40 = frame["lgb_q40_pred_log"].to_numpy(dtype=float)
    qwidth = frame["quantile_width_log"].to_numpy(dtype=float)
    artist = frame["artist_key"].astype(str).to_numpy()

    rep = y18
    guard = guard_pred_log(y18, lgb_q40, qwidth, params)

    covered = np.array([a in lookup for a in artist])
    search_delta = np.array([lookup.get(a, 0.0) for a in artist], dtype=float)
    defense = guard + search_delta  # uncovered → delta 0 → guard only (fallback)

    qwidth_q67 = float(params["guard"]["qwidth_q67"])
    review_flag = (~covered) | (qwidth >= qwidth_q67)
    confidence = np.where(qwidth >= qwidth_q67, "low", np.where(covered, "medium", "low"))

    out = frame.copy()
    out["cold_representative_pred_log"] = rep
    out["cold_defense_pred_log"] = defense
    out["search_covered"] = covered
    out["search_delta_applied"] = search_delta
    out["cold_review_flag"] = review_flag
    out["cold_confidence_tier"] = confidence
    out["cold_representative_pred_price_krw"] = np.clip(np.exp(rep), 1_000.0, None)
    out["cold_defense_pred_price_krw"] = np.clip(np.exp(defense), 1_000.0, None)
    return out


if __name__ == "__main__":
    p = load_params()
    lk = load_search_lookup()
    print(f"v0.3 loaded: guard={p['guard']}, search source={p['search']['source']}, lookup artists={len(lk)}")
