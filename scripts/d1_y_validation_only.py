"""D1.Y: D1.X N=5 → N=10 multi-seed validation expansion (R1 amendment 반영).

Prereg: docs/d1_y_multiseed_n10_prereg_20260510.md (R1 NEEDS FIX → amendment)
Decision binding: ✅ YES — D1.X NEEDS_MORE_DATA (4/5 PASS / seed=113 outlier) 후속.

R1 amendment:
- P0 fix: dataset_fingerprint 동일 단일 snapshot 보장 / D1.X JSON 결합 X
- P1.2 fix: 모든 10 seed (D1.X 5 + 신규 5) 본 스크립트에서 fresh rerun
- P1.1 fix: aggregate strict — PASS_with_caveat = PASS×9+1 outlier OR PASS×8+INCONCLUSIVE×2 (FAIL×2 X)

Method:
- D1.X retuned params 재사용 (n32_champion_retuned_best_params.json / commit d06ea22)
- Validation: 10 seeds = D1.X 5 (97/113/199/223/257) + 신규 5 (313/367/439/491/587) / 단일 snapshot fresh run
- N=10 aggregate logic (R1 amendment strict)

Compute: ~8-10분 wall (10 seed × ~50s validation).

Usage:
    python3 scripts/d1_y_validation_only.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import optuna_n32_champion_retune as d1mod  # type: ignore
from optuna_n32_champion_retune import validate_seed  # type: ignore
from train_primary_market_v3_filtered import load_data, prepare_features  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
HOLDOUT_DIR = REPO / "data" / "d1_y_holdout_20260510"
RETUNED_PARAMS_PATH = ARTIFACTS_DIR / "n32_champion_retuned_best_params.json"
D1X_VALIDATION_PATH = ARTIFACTS_DIR / "d1_validation_20260510.json"
RESULTS_PATH = ARTIFACTS_DIR / "d1_y_validation.json"
AGGREGATE_PATH = ARTIFACTS_DIR / "d1_y_aggregate.json"

# R1 amendment: 모든 10 seed 단일 snapshot fresh run
# D1.X seeds (97/113/199/223/257) + 신규 5 (313/367/439/491/587)
ALL_SEEDS = (97, 113, 199, 223, 257, 313, 367, 439, 491, 587)
D1X_SEEDS = (97, 113, 199, 223, 257)
NEW_SEEDS = (313, 367, 439, 491, 587)


def _dataset_fingerprint(df: pd.DataFrame) -> str:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _aggregate_n10(per_seed_verdicts: list[str]) -> str:
    """N=10 multi-seed aggregate logic (R1 amendment / strict).

    R1 P1.1 amendment:
    - PASS_with_caveat = PASS×9 + 1 outlier (INCONCLUSIVE or FAIL) OR PASS×8 + INCONCLUSIVE×2
    - FAIL×2 → FAIL (champion swap risk premium / 이전 plan PASS×8+FAIL×2 → PASS_with_caveat 거부)
    """
    n = len(per_seed_verdicts)
    cnt = {v: per_seed_verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == n:
        return "PASS"
    # PASS × 9 + 1 outlier (INCONCLUSIVE or FAIL)
    if cnt["PASS"] == n - 1 and (cnt["INCONCLUSIVE"] + cnt["FAIL"]) == 1:
        return "PASS_with_caveat"
    # PASS × 8 + INCONCLUSIVE × 2 (FAIL 0)
    if cnt["PASS"] == n - 2 and cnt["INCONCLUSIVE"] == 2 and cnt["FAIL"] == 0:
        return "PASS_with_caveat"
    # FAIL × 2 이상 → FAIL (R1 amendment / champion swap risk premium)
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def main() -> None:
    logger.info("=" * 70)
    logger.info("D1.Y: D1.X N=5 → N=10 multi-seed validation expansion")
    logger.info("=" * 70)

    # D1.X retuned params load
    if not RETUNED_PARAMS_PATH.exists():
        raise FileNotFoundError(
            f"D1.X retuned params 없음 ({RETUNED_PARAMS_PATH}) — D1.X compliant rerun (commit d06ea22) 결과 필요"
        )
    with RETUNED_PARAMS_PATH.open() as f:
        d1x_data = json.load(f)
    cb_default = d1x_data["cb_default"]
    xgb_default = d1x_data["xgb_default"]
    cb_retuned = d1x_data["cb_retuned"]
    xgb_retuned = d1x_data["xgb_retuned"]
    logger.info("D1.X retuned params loaded:")
    logger.info("  CB retuned: iter=%s / depth=%s / lr=%.4f",
                cb_retuned.get("iterations"), cb_retuned.get("depth"), cb_retuned.get("learning_rate"))
    logger.info("  XGB retuned: boost=%s / depth=%s / lr=%.4f",
                xgb_retuned.get("num_boost_round"), xgb_retuned.get("max_depth"),
                xgb_retuned.get("learning_rate"))

    # D1.X validation context load (historical reference only / R1 amendment)
    d1x_historical = None
    if D1X_VALIDATION_PATH.exists():
        with D1X_VALIDATION_PATH.open() as f:
            d1x_historical = json.load(f)
        logger.info("D1.X validation loaded as HISTORICAL CONTEXT only (not stitched)")

    # Data load (single snapshot for all 10 seeds / R1 P0+P1.2 amendment)
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fingerprint=%s...",
                len(df), df["artist_slug"].nunique(), fingerprint[:12])

    if d1x_historical:
        d1x_fp = d1x_historical.get("dataset_fingerprint", "")
        if d1x_fp != fingerprint:
            logger.warning(
                "⚠️ Dataset fingerprint differs from D1.X / D1.X=%s... / D1.Y=%s... — historical 비교만 가능 (N=10 결합 X)",
                d1x_fp[:12], fingerprint[:12],
            )
        else:
            logger.info("✅ Dataset fingerprint match D1.X (historical comparison 가능)")

    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # Override HOLDOUT_DIR in D1.X module to D1.Y dir
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    d1mod.HOLDOUT_DIR = HOLDOUT_DIR

    # All 10 seeds validation in single snapshot (R1 P0+P1.2 amendment)
    logger.info("=" * 60)
    logger.info("D1.Y N=10 fresh validation (단일 snapshot)")
    logger.info("seeds=%s", ALL_SEEDS)
    logger.info("=" * 60)

    all_per_seed: dict[int, Any] = {}
    for seed in ALL_SEEDS:
        result = validate_seed(
            seed, X, y, groups, source, cb_default, xgb_default, cb_retuned, xgb_retuned,
        )
        all_per_seed[seed] = result

    combined_verdicts = [all_per_seed[s]["verdict"] for s in sorted(all_per_seed.keys())]
    aggregate = _aggregate_n10(combined_verdicts)

    # Overall verdict (prereg §2.6)
    if aggregate == "PASS":
        overall = "ADOPT_n32_champion_retune"
    elif aggregate == "PASS_with_caveat":
        overall = "ADOPT_canary_n32_champion_retune"
    elif aggregate == "FAIL":
        overall = "HOLD_n32_default"
    else:
        overall = "NEEDS_MORE_DATA"

    # Save validation result + N=10 aggregate (R1 amendment / single snapshot)
    d1x_fp_match = (d1x_historical and d1x_historical.get("dataset_fingerprint") == fingerprint) if d1x_historical else None
    d1y_output = {
        "version": "v2-d1-y-validation-amended",
        "validation_seeds": list(ALL_SEEDS),
        "validation_seeds_d1x_subset": list(D1X_SEEDS),
        "validation_seeds_new_subset": list(NEW_SEEDS),
        "n_seeds_total": len(all_per_seed),
        "cb_default": cb_default,
        "xgb_default": xgb_default,
        "cb_retuned": cb_retuned,
        "xgb_retuned": xgb_retuned,
        "dataset_fingerprint": fingerprint,
        "d1x_historical_fingerprint_match": d1x_fp_match,
        "per_seed": all_per_seed,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(d1y_output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved D1.Y validation: %s", RESULTS_PATH.name)

    aggregate_output = {
        "version": "v2-d1-n10-aggregate-amended",
        "n_seeds": len(all_per_seed),
        "per_seed": {str(k): all_per_seed[k] for k in sorted(all_per_seed.keys())},
        "verdicts": combined_verdicts,
        "verdict_counts": {
            v: combined_verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")
        },
        "aggregate": aggregate,
        "overall_verdict": overall,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    AGGREGATE_PATH.write_text(json.dumps(aggregate_output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved N=10 aggregate: %s", AGGREGATE_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"D1.Y N=10 SUMMARY (overall: {overall})")
    print("=" * 70)
    print(f"  Aggregate: {aggregate}")
    print(f"  Verdict counts: PASS={combined_verdicts.count('PASS')}, "
          f"INCONCLUSIVE={combined_verdicts.count('INCONCLUSIVE')}, "
          f"FAIL={combined_verdicts.count('FAIL')}")
    print(f"  N=10 seeds (single snapshot fresh): {sorted(all_per_seed.keys())}")
    print()
    for seed in sorted(all_per_seed.keys()):
        r = all_per_seed[seed]
        d = r.get("deltas", {})
        marker = " (D1.X)" if seed in D1X_SEEDS else " (D1.Y new)"
        print(f"  seed={seed:4d}{marker}: {r['verdict']:14s} | Δ_cold={d.get('delta_cold_overall',0):+.3f} "
              f"| Δ_artsy={d.get('delta_cold_artsy',0):+.3f} "
              f"| Δ_warm={d.get('delta_warm',0):+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
