"""D1-extended: D1.Z2 + D1.split + D1.alt2 combined prospective cycle (R1 HOLD → R2/R3 LGTM amendment).

Prereg: docs/d1_extended_prospective_prereg_20260510.md
Decision binding: ✅ YES (R1 amendment / strict primary preserved / bootstrap secondary corroboration)

R1 amendment 정합:
- Strict per-seed aggregate (D1.Y rule) = Primary binding (codex P0 / decision object 보존)
- Bootstrap CI = Secondary corroboration (not binding alone / codex P0)
- N=10 fresh seeds (codex P1.1 / under-power 회피)
- ADOPT_canary 최소 조건 = strict PASS_with_caveat + bootstrap PASS + lax-1 PASS (codex P1.2)
- D1.Y rule R1 P1.1 strict aggregate (FAIL × 2 이상 → FAIL)

Method:
- 10 fresh seeds {631, 661, 691, 727, 757, 787, 821, 853, 877, 907} (이전 cycle 비중복)
- D1.X retuned params 재사용 (n32_champion_retuned_best_params.json)
- 각 seed: validate_seed (D1.Y / optuna_n32_champion_retune.validate_seed)
- Strict primary aggregate (D1.Y rule) + bootstrap CI secondary (10000 iters / 95% CI / hierarchical) + threshold sensitivity (strict / lax-1 / lax-2) + per-source decomposition

Compute: ~10분 wall (10 seed × ~50s validation).

Usage:
    python3 scripts/d1_extended_validation.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
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
HOLDOUT_DIR = REPO / "data" / "d1_extended_holdout_20260510"
RETUNED_PARAMS_PATH = ARTIFACTS_DIR / "n32_champion_retuned_best_params.json"
RESULTS_PATH = ARTIFACTS_DIR / "d1_extended_results.json"

# R1 amendment: 10 fresh seeds (이전 cycle 비중복: D1.X/D1.Y 97-587 / B 541-947 / D3 127-419 / D3.B 149-449)
ALL_SEEDS = (631, 661, 691, 727, 757, 787, 821, 853, 877, 907)

THRESHOLD_TIERS = [
    {"name": "strict (Primary)", "g1": 0.0, "g2": 0.3, "g3": 0.3, "g4": 0.1},
    {"name": "lax-1 (G2/G3 +0.8)", "g1": 0.0, "g2": 0.8, "g3": 0.8, "g4": 0.1},
    {"name": "lax-2 (G2/G3 +1.0)", "g1": 0.0, "g2": 1.0, "g3": 1.0, "g4": 0.1},
]

N_BOOT = 10000
RNG_SEED = 42


def _dataset_fingerprint(df: pd.DataFrame) -> str:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verdict(d: dict, tier: dict) -> str:
    g1 = d["delta_cold_overall"] <= tier["g1"]
    g2 = d["delta_cold_artsy"] <= tier["g2"]
    g3 = d["delta_cold_saatchi"] <= tier["g3"]
    g4 = d["delta_warm"] <= tier["g4"]
    if g1 and g2 and g3 and g4:
        return "PASS"
    if 0 < d["delta_cold_overall"] <= 0.3 and g2 and g3 and g4:
        return "INCONCLUSIVE"
    return "FAIL"


def _aggregate_n10_strict(verdicts: list[str]) -> str:
    """D1.Y R1 P1.1 strict aggregate."""
    n = len(verdicts)
    cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == n:
        return "PASS"
    if cnt["PASS"] == n - 1 and (cnt["INCONCLUSIVE"] + cnt["FAIL"]) == 1:
        return "PASS_with_caveat"
    if cnt["PASS"] == n - 2 and cnt["INCONCLUSIVE"] == 2 and cnt["FAIL"] == 0:
        return "PASS_with_caveat"
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def _bootstrap_ci(deltas: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED,
                  ci_level: float = 0.95) -> dict:
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot_means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = deltas[idx].mean()
    alpha = (1.0 - ci_level) / 2.0
    lo = float(np.percentile(boot_means, alpha * 100))
    hi = float(np.percentile(boot_means, (1 - alpha) * 100))
    return {
        "mean": float(deltas.mean()),
        "std": float(deltas.std(ddof=1)),
        "n": int(n),
        "ci_level": ci_level,
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
        "ci_includes_zero": bool(lo <= 0 <= hi),
        "ci_upper_negative": bool(hi <= 0),
    }


def _per_source_decompose(per_seed: dict, source_filter: str) -> np.ndarray:
    """Per-source mean delta extraction for D1.split tertiary."""
    deltas = []
    for s in sorted(per_seed.keys()):
        m = per_seed[s].get("metrics", {})
        ens_def = m.get("ens_default", {})
        ens_ret = m.get("ens_retuned", {})
        key = f"cold_{source_filter}"
        d_def = ens_def.get(key)
        d_ret = ens_ret.get(key)
        if d_def is not None and d_ret is not None:
            deltas.append(d_ret - d_def)
    return np.array(deltas)


def _combined_decision(strict_agg: str, bootstrap_status: str, lax1_agg: str) -> str:
    """R1 amendment / codex P0+P1.2 combined decision rule."""
    if strict_agg == "FAIL":
        return "HOLD_D1_axis_abandon"
    if strict_agg == "PASS":
        if bootstrap_status == "bootstrap_PASS":
            return "ADOPT_full_migration"
        return "ADOPT_canary_strict_only"
    if strict_agg == "PASS_with_caveat":
        if bootstrap_status == "bootstrap_PASS" and lax1_agg in ("PASS", "PASS_with_caveat"):
            return "ADOPT_canary_3way_confirmation"
        return "NEEDS_MORE_DATA_lax1_minimum_unmet"
    return "NEEDS_MORE_DATA_inconclusive"


def main() -> None:
    logger.info("=" * 70)
    logger.info("D1-extended: fresh N=10 prospective cycle (strict primary + bootstrap secondary)")
    logger.info("=" * 70)

    # D1.X retuned params load
    if not RETUNED_PARAMS_PATH.exists():
        raise FileNotFoundError(f"D1.X retuned params 없음 ({RETUNED_PARAMS_PATH})")
    with RETUNED_PARAMS_PATH.open() as f:
        d1x_data = json.load(f)
    cb_default = d1x_data["cb_default"]
    xgb_default = d1x_data["xgb_default"]
    cb_retuned = d1x_data["cb_retuned"]
    xgb_retuned = d1x_data["xgb_retuned"]
    logger.info("D1 retuned params loaded (commit d06ea22 / D1.Y 정합)")

    # Data load
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    fingerprint = _dataset_fingerprint(df)
    logger.info("rows=%d / artists=%d / fingerprint=%s...",
                len(df), df["artist_slug"].nunique(), fingerprint[:12])

    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # Override HOLDOUT_DIR
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    d1mod.HOLDOUT_DIR = HOLDOUT_DIR

    # Validation: 10 fresh seeds
    logger.info("=" * 60)
    logger.info("Validation: 10 fresh seeds=%s", ALL_SEEDS)
    logger.info("=" * 60)
    per_seed: dict[int, Any] = {}
    for seed in ALL_SEEDS:
        per_seed[seed] = validate_seed(
            seed, X, y, groups, source, cb_default, xgb_default, cb_retuned, xgb_retuned,
        )

    # 1. Strict primary (D1.Y rule)
    logger.info("=" * 60)
    logger.info("Primary (strict per-seed aggregate / D1.Y rule)")
    logger.info("=" * 60)
    threshold_results = []
    for tier in THRESHOLD_TIERS:
        verdicts = [_verdict(per_seed[s]["deltas"], tier) for s in ALL_SEEDS]
        agg = _aggregate_n10_strict(verdicts)
        cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
        threshold_results.append({
            "name": tier["name"],
            "thresholds": {k: tier[k] for k in ("g1", "g2", "g3", "g4")},
            "verdict_counts": cnt,
            "aggregate": agg,
            "per_seed_verdicts": {str(s): v for s, v in zip(ALL_SEEDS, verdicts, strict=False)},
        })
        logger.info("  %s: PASS=%d INC=%d FAIL=%d → %s",
                    tier["name"], cnt["PASS"], cnt["INCONCLUSIVE"], cnt["FAIL"], agg)

    strict_aggregate = threshold_results[0]["aggregate"]
    lax1_aggregate = threshold_results[1]["aggregate"]

    # 2. Bootstrap CI secondary corroboration
    logger.info("=" * 60)
    logger.info("Bootstrap CI secondary corroboration (n_boot=%d / 95%% / hierarchical)", N_BOOT)
    logger.info("=" * 60)
    deltas_arr = {
        cell: np.array([per_seed[s]["deltas"][cell] for s in ALL_SEEDS])
        for cell in ("delta_cold_overall", "delta_cold_artsy", "delta_cold_saatchi", "delta_warm")
    }
    bootstrap_ci = {cell: _bootstrap_ci(d) for cell, d in deltas_arr.items()}
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        logger.info("  %-22s mean=%+.4f CI95=[%+.3f, %+.3f] %s",
                    cell, ci["mean"], ci["ci_lower"], ci["ci_upper"], marker)

    cold_o_ci = bootstrap_ci["delta_cold_overall"]
    if cold_o_ci["ci_upper"] <= 0:
        bootstrap_status = "bootstrap_PASS"
    elif cold_o_ci["ci_upper"] <= 0.5:
        bootstrap_status = "bootstrap_INCONCLUSIVE"
    else:
        bootstrap_status = "bootstrap_FAIL"

    # 3. Per-source decomposition (tertiary informational)
    logger.info("=" * 60)
    logger.info("Per-source decomposition (D1.split tertiary informational)")
    logger.info("=" * 60)
    per_source = {}
    for src in ("artsy", "saatchi"):
        deltas = _per_source_decompose(per_seed, src)
        if len(deltas) > 0:
            ci = _bootstrap_ci(deltas)
            per_source[src] = ci
            marker = "✅" if ci["ci_upper_negative"] else "⚠️"
            logger.info("  cold_%s: mean=%+.4f CI95=[%+.3f, %+.3f] %s",
                        src, ci["mean"], ci["ci_lower"], ci["ci_upper"], marker)

    # 4. Combined decision (R1 amendment)
    decision = _combined_decision(strict_aggregate, bootstrap_status, lax1_aggregate)
    logger.info("=" * 60)
    logger.info("Combined decision: %s", decision)
    logger.info("  strict primary: %s", strict_aggregate)
    logger.info("  bootstrap secondary: %s", bootstrap_status)
    logger.info("  lax-1 (canary minimum): %s", lax1_aggregate)
    logger.info("=" * 60)

    # Save
    output = {
        "version": "v1-d1-extended-prospective",
        "decision_binding": True,
        "n_seeds": len(ALL_SEEDS),
        "seeds": list(ALL_SEEDS),
        "cb_retuned": cb_retuned,
        "xgb_retuned": xgb_retuned,
        "dataset_fingerprint": fingerprint,
        "per_seed": {str(s): per_seed[s] for s in ALL_SEEDS},
        "strict_primary_aggregate": strict_aggregate,
        "bootstrap_secondary_status": bootstrap_status,
        "bootstrap_ci_per_cell": bootstrap_ci,
        "threshold_sensitivity": threshold_results,
        "per_source_decomposition": per_source,
        "combined_decision": decision,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"D1-extended SUMMARY (combined decision: {decision})")
    print("=" * 70)
    print()
    print("Strict primary (D1.Y rule):")
    for tr in threshold_results:
        print(f"  {tr['name']:24s}: PASS={tr['verdict_counts']['PASS']:2d} "
              f"INC={tr['verdict_counts']['INCONCLUSIVE']:2d} "
              f"FAIL={tr['verdict_counts']['FAIL']:2d} → {tr['aggregate']}")
    print()
    print("Bootstrap CI (95% / hierarchical / cold_overall primary):")
    for cell, ci in bootstrap_ci.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        print(f"  {cell:24s} mean={ci['mean']:+.4f} CI95=[{ci['ci_lower']:+.3f}, {ci['ci_upper']:+.3f}] {marker}")
    print()
    print("Per-source decomposition:")
    for src, ci in per_source.items():
        marker = "✅" if ci["ci_upper_negative"] else "⚠️"
        print(f"  cold_{src:8s} mean={ci['mean']:+.4f} CI95=[{ci['ci_lower']:+.3f}, {ci['ci_upper']:+.3f}] {marker}")
    print()
    print(f"Final decision: {decision}")
    print("=" * 70)


if __name__ == "__main__":
    main()
