"""Phase 0.D — quick importance (CatBoost FI / XGBoost gain).

Decision binding ❌ X / read-only / 운영 artifact 영역 의 의무 변경 X.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import xgboost as xgb
from catboost import CatBoostRegressor

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from visionai.price_engine.api.primary_predictor import CB_FEATURES_BASE  # noqa: E402

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "phase0_importance_quick.json"


def cb_pvc(model_path: Path, features: list[str]) -> dict[str, float]:
    cb = CatBoostRegressor()
    cb.load_model(str(model_path))
    fi = cb.get_feature_importance(type="PredictionValuesChange")
    return {f: float(v) for f, v in zip(features, fi)}


def xgb_importance(model_path: Path, features: list[str]) -> dict[str, dict[str, float]]:
    booster = xgb.Booster()
    booster.load_model(str(model_path))
    out = {"gain": {}, "weight": {}, "cover": {}}
    for kind in out:
        score = booster.get_score(importance_type=kind)
        total = sum(score.values()) or 1.0
        normalized = {f: score.get(f, 0.0) / total * 100 for f in features}
        out[kind] = {f: float(v) for f, v in normalized.items()}
    return out


def main() -> None:
    cb_path = ARTIFACTS / "integrated_v3_filtered_tuned_catboost.cbm"
    xgb_path = ARTIFACTS / "integrated_v3_filtered_tuned_xgboost.json"

    cb_fi = cb_pvc(cb_path, CB_FEATURES_BASE)
    xgb_fi = xgb_importance(xgb_path, CB_FEATURES_BASE)

    # rank 산출
    cb_rank = {k: i + 1 for i, (k, _) in enumerate(sorted(cb_fi.items(), key=lambda x: -x[1]))}
    xgb_gain_rank = {k: i + 1 for i, (k, _) in enumerate(sorted(xgb_fi["gain"].items(), key=lambda x: -x[1]))}

    out = {
        "phase": 0,
        "method": "quick (CatBoost FI + XGBoost gain/weight/cover)",
        "n_features": len(CB_FEATURES_BASE),
        "features": CB_FEATURES_BASE,
        "catboost_fi_pvc": cb_fi,
        "catboost_rank": cb_rank,
        "xgboost_gain": xgb_fi["gain"],
        "xgboost_weight": xgb_fi["weight"],
        "xgboost_cover": xgb_fi["cover"],
        "xgboost_gain_rank": xgb_gain_rank,
    }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"[OK] {OUT.name}")
    print(f"\n=== CatBoost FI (top 10) ===")
    for f, v in sorted(cb_fi.items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:30s} {v:>7.2f}%")
    print(f"\n=== XGBoost gain (top 10) ===")
    for f, v in sorted(xgb_fi["gain"].items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:30s} {v:>7.2f}%")
    print(f"\n=== CatBoost FI = 0% (placeholder candidate) ===")
    zero_cb = [f for f, v in cb_fi.items() if v < 0.01]
    print(f"  {zero_cb}")


if __name__ == "__main__":
    main()
