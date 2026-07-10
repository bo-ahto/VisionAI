"""B-2: 트랙 1 운영 artifact reproducibility cycle.

Pre-registered: docs/track1_artifact_reproduction_b2_prereg_20260508.md
Decision binding: ❌ X (artifact integrity gate 만)

목표: 운영 reported metric (cold baseline 39.38% / cold calibrated guarded 38.29%)
의 동일 환경 (thread_count=1 deterministic) 재현 가능 여부 확인.

PASS 조건 (모두 충족):
- Total N = 28,376 (exact)
- Cell N = 868 / 6,421 / 21,087 (exact)
- cold baseline MdAPE ∈ [39.18, 39.58]
- cold calibrated cross-fit guarded MdAPE ∈ [38.09, 38.49]
- per-cell applied_factor direction (skipped vs applied) operational 동일
- per-cell applied factor 값 ±0.005 of operational
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

# operational helper imports
from train_primary_market_v3_filtered import (  # type: ignore  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    load_data,
    prepare_features,
)
from calibrate_source_bias import (  # type: ignore  # noqa: E402
    _cell_key,
    _compute_factor,
    _cross_fit_eval,
    _mdape,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACT_DIR = REPO / "model_test_results"
RESULTS_DIR = REPO / "experiments" / "structural_v1" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Operational reported (frozen reference)
OPERATIONAL = {
    "n_total": 28376,
    "cell_n": {"artsy_gallery": 868, "artsy_online": 6421, "saatchi_online": 21087},
    "cold_baseline_mdape": 39.3767703371767,
    "cold_calibrated_guarded_mdape": 38.28973677147977,
    "applied_factors": {
        "artsy_gallery": 1.0,
        "artsy_online": 0.9425943416620021,
        "saatchi_online": 0.9568847727800011,
    },
    "skipped_due_to_regression": {
        "artsy_gallery": True,
        "artsy_online": False,
        "saatchi_online": False,
    },
}

PASS_TOLERANCE = {
    "mdape": 0.20,  # ±0.20%p (prereg §1)
    "factor": 0.005,  # ±0.005 (prereg §4.1)
}


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def cold_oof_thread1(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, cb_params: dict, n_splits: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """GroupKFold OOF with thread_count=1 deterministic freeze (B-2 prereg §3.1)."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    fold_ids = np.full(len(y), -1, dtype=int)
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups)):
        logger.info("[Cold fold %d/%d] train=%d test=%d", fold + 1, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params,
            loss_function="RMSE",
            verbose=0,
            random_seed=42,
            thread_count=1,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))
        fold_ids[te] = fold
    return cb_preds, fold_ids


def main() -> dict:
    logger.info("=" * 70)
    logger.info("B-2: Track 1 artifact reproducibility cycle (thread_count=1)")
    logger.info("=" * 70)

    # 1. load + filter
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    n_total = len(df)
    logger.info("After filter is_excluded_for_training==0: n=%d", n_total)
    assert n_total == OPERATIONAL["n_total"], (
        f"Total N mismatch: {n_total} != {OPERATIONAL['n_total']}"
    )

    # 2. cell breakdown sanity
    target_market = np.where(
        df["is_krw"].fillna(0).astype(int) == 1, "gallery", "online"
    )
    source = df["source"].astype(str).to_numpy()
    cells = np.array([_cell_key(s, tm) for s, tm in zip(source, target_market)])
    cell_n = {str(c): int((cells == c).sum()) for c in sorted(set(cells))}
    logger.info("Cell N: %s", cell_n)
    assert cell_n == OPERATIONAL["cell_n"], (
        f"Cell N mismatch: {cell_n} != {OPERATIONAL['cell_n']}"
    )

    # 3. load operational best_params
    with open(ARTIFACT_DIR / "integrated_v3_filtered_tuned_best_params.json") as f:
        best_params = json.load(f)
    cb_params = best_params["catboost"]
    logger.info("CatBoost best_params: %s", cb_params)

    # 4. GroupKFold cold OOF
    X, y, groups = prepare_features(df)
    logger.info("--- Cold CatBoost OOF (GroupKFold 5, thread_count=1) ---")
    cb_preds_ln, cold_fold_ids = cold_oof_thread1(X, y, groups, cb_params)

    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds_ln)

    # 5. cross-fit calibration eval
    logger.info("--- Cold cross-fit evaluation ---")
    cold_factors, cold_baseline, cold_calibrated, cold_calibrated_pred = _cross_fit_eval(
        y_price, cb_pred_price, cells, cold_fold_ids
    )
    logger.info(
        "Cold baseline=%.4f → cross-fit unguarded=%.4f", cold_baseline, cold_calibrated
    )
    logger.info("Cold final factors: %s", cold_factors)

    # 6. per-cell breakdown + guard
    cold_breakdown: dict[str, dict] = {}
    cold_applied_factors: dict[str, float] = {}
    for cell in sorted(set(cells)):
        cell_str = str(cell)
        mask = cells == cell
        b = _mdape(y_price[mask], cb_pred_price[mask])
        c = _mdape(y_price[mask], cold_calibrated_pred[mask])
        proposed_factor = cold_factors.get(cell, 1.0)
        applied_factor = proposed_factor if c <= b else 1.0
        cold_breakdown[cell_str] = {
            "n": int(mask.sum()),
            "proposed_factor": proposed_factor,
            "applied_factor": applied_factor,
            "baseline_mdape": b,
            "calibrated_mdape_cross_fit": c,
            "skipped_due_to_regression": applied_factor == 1.0 and proposed_factor != 1.0,
        }
        cold_applied_factors[cell_str] = applied_factor

    # 7. guarded overall MdAPE
    cold_pred_guarded = cb_pred_price.copy()
    for cell in set(cells):
        if cold_applied_factors.get(str(cell), 1.0) != 1.0:
            mask = cells == cell
            cold_pred_guarded[mask] = cold_calibrated_pred[mask]
    cold_guarded_mdape = _mdape(y_price, cold_pred_guarded)
    logger.info("Cold guarded overall MdAPE=%.4f", cold_guarded_mdape)

    # Secondary sanity metrics (W30/W50/ratio on baseline OOF — operational reported reference)
    # operational `train_primary_market_v3_filtered.py:46-53` 의 _within_pct + _ratio 정확 동일
    abs_pct_err = np.abs(y_price - cb_pred_price) / np.abs(y_price)
    w30 = float((abs_pct_err <= 0.30).mean() * 100)
    w50 = float((abs_pct_err <= 0.50).mean() * 100)
    ratio = float(np.mean(cb_pred_price / y_price))
    logger.info(
        "Cold baseline secondary: W30=%.2f W50=%.2f ratio=%.2f", w30, w50, ratio
    )

    # 8. PASS / FAIL
    checks = {
        "n_total_exact": n_total == OPERATIONAL["n_total"],
        "cell_n_exact": cell_n == OPERATIONAL["cell_n"],
        "cold_baseline_in_range": (
            OPERATIONAL["cold_baseline_mdape"] - PASS_TOLERANCE["mdape"]
            <= cold_baseline
            <= OPERATIONAL["cold_baseline_mdape"] + PASS_TOLERANCE["mdape"]
        ),
        "cold_guarded_in_range": (
            OPERATIONAL["cold_calibrated_guarded_mdape"] - PASS_TOLERANCE["mdape"]
            <= cold_guarded_mdape
            <= OPERATIONAL["cold_calibrated_guarded_mdape"] + PASS_TOLERANCE["mdape"]
        ),
    }

    factor_checks: dict[str, dict] = {}
    for cell, op_factor in OPERATIONAL["applied_factors"].items():
        repro_factor = cold_applied_factors.get(str(cell), float("nan"))
        op_skipped = OPERATIONAL["skipped_due_to_regression"][cell]
        repro_skipped = cold_breakdown[str(cell)]["skipped_due_to_regression"]
        direction_match = op_skipped == repro_skipped
        value_in_range = abs(repro_factor - op_factor) <= PASS_TOLERANCE["factor"]
        factor_checks[cell] = {
            "operational_factor": op_factor,
            "reproduction_factor": repro_factor,
            "operational_skipped": op_skipped,
            "reproduction_skipped": repro_skipped,
            "direction_match": direction_match,
            "value_in_range": value_in_range,
        }

    all_factor_directions_match = all(c["direction_match"] for c in factor_checks.values())
    all_factor_values_in_range = all(c["value_in_range"] for c in factor_checks.values())

    pass_overall = (
        all(checks.values()) and all_factor_directions_match and all_factor_values_in_range
    )

    result = {
        "verdict": "PASS" if pass_overall else "FAIL",
        "n_total": n_total,
        "cell_n": cell_n,
        "cold_baseline_mdape": cold_baseline,
        "cold_calibrated_guarded_mdape": cold_guarded_mdape,
        "cold_baseline_secondary": {"W30": w30, "W50": w50, "ratio": ratio},
        "cold_breakdown": cold_breakdown,
        "checks": checks,
        "factor_checks": factor_checks,
        "operational_reference": OPERATIONAL,
        "tolerance": PASS_TOLERANCE,
        "environment": {
            "python": sys.version.split()[0],
            "catboost_thread_count": 1,
            "random_seed": 42,
            "groupkfold_n_splits": 5,
        },
    }

    out = RESULTS_DIR / "track1_artifact_reproduction_b2.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    logger.info("Wrote %s", out)
    logger.info("VERDICT: %s", result["verdict"])
    return result


if __name__ == "__main__":
    main()
