#!/usr/bin/env python3
"""Cold prediction v0.4 confidence/display policy layer.

v0.3(guard+search 점 예측)은 그대로 두고, PP-CCONF1이 검증한 신뢰도 tier와
표시/검수 정책, PP-CSRCH1의 미커버 작가 상수 delta fallback(기본 off)을 고정한다.

- confidence tier (research 신호: qwidth + 모델 gap + 검색 lookup 커버):
    low  : qwidth >= qw_q90  OR  |y18 - v02_defense| >= gap_q90
    high : qwidth <= qw_q33 AND |y18 - v02_defense| <= gap_q50 AND covered (low 아님)
    else medium
  PP-CCONF1 근거: test p95 분리 high 0.9904 vs low 2.9877 (전체 2.3465).
- 금지: v0.2 qwidth 단독 tier는 test에서 역전(과신)이 확인되어 제공하지 않는다.
- 검수 2단: review_flag_v03(재현율 축, qwidth>=q67 OR 미커버) +
  priority_review(정밀 축, low tier). 결합은 OR.
- uncovered_constant_delta (기본 off): 미커버 작가의 guard-only fallback에
  상수 delta를 더해 p95를 방어하는 운영 옵션. PP-CSRCH1 근거: holdout
  MAPE/p95 개선확률 0.97~1.0, 대가는 MdAPE 소폭 악화 (게이트 미통과로 기본 off).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path(__file__).resolve().parents[1]
CONFIG_DIR = BUNDLE / "config"

REQUIRED = ["quantile_width_log", "y18_qwidth_pred_log", "v02_defense_pred_log", "artist_key"]

DISPLAY = {
    "high": "point_estimate_with_narrow_range",
    "medium": "point_estimate_with_standard_range_q10_q90",
    "low": "wide_range_first_with_priority_review",
}


def load_params() -> dict:
    return json.loads((CONFIG_DIR / "confidence_tier_policy_v0_4.json").read_text(encoding="utf-8"))


def load_search_lookup() -> dict[str, float]:
    raw = json.loads((CONFIG_DIR / "search_delta_lookup_v0_4.json").read_text(encoding="utf-8"))
    return {str(k): float(v) for k, v in raw["artist_delta"].items()}


def apply(frame: pd.DataFrame, params: dict | None = None,
          lookup: dict[str, float] | None = None) -> pd.DataFrame:
    params = params or load_params()
    lookup = load_search_lookup() if lookup is None else lookup
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"required columns missing: {missing}")

    b = params["tier_bounds"]
    qw = frame["quantile_width_log"].to_numpy(dtype=float)
    gap = np.abs(frame["y18_qwidth_pred_log"].to_numpy(dtype=float)
                 - frame["v02_defense_pred_log"].to_numpy(dtype=float))
    artist = frame["artist_key"].astype(str).to_numpy()
    covered = np.array([a in lookup for a in artist])

    low = (qw >= b["qw_q90"]) | (gap >= b["gap_q90"])
    high = (qw <= b["qw_q33"]) & (gap <= b["gap_q50"]) & covered & ~low
    tier = np.select([low, high], ["low", "high"], default="medium")

    out = frame.copy()
    out["search_covered"] = covered
    out["confidence_tier"] = tier
    out["review_flag_v03"] = (qw >= float(params["review_flag_v03"]["qwidth_q67"])) | ~covered
    out["priority_review_flag"] = tier == "low"
    out["review_flag_combined"] = out["review_flag_v03"] | out["priority_review_flag"]
    out["display_policy"] = pd.Series(tier, index=out.index).map(DISPLAY)

    fb = params["uncovered_constant_delta"]
    if fb.get("enabled", False):
        if "guard_pred_log" not in frame.columns:
            raise ValueError("uncovered_constant_delta 모드에는 guard_pred_log 컬럼이 필요하다")
        guard = frame["guard_pred_log"].to_numpy(dtype=float)
        delta = np.array([lookup.get(a, float(fb["delta"])) for a in artist], dtype=float)
        out["cold_defense_with_uncovered_fallback_log"] = guard + np.clip(
            delta, -float(fb["cap"]), float(fb["cap"]))
    return out
