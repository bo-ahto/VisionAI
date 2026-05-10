"""D1.Z+alt: D1.Y per-seed 결과 재분석 (analysis-only / non-binding).

Prereg: docs/d1_z_alt_alternative_aggregation_prereg_20260510.md (R1 HOLD → R2/R3 LGTM amendment)
연계: D1.Y `d774938` HOLD_n32_default

R1 amendment 정합:
- Decision binding ❌ NO / analysis-only / hypothesis-generating
- Best outcome cap = HYPOTHESIS_GENERATING_for_relaxed_cycle
- Bootstrap = supplementary (cold_overall primary / hierarchical)
- 본 cycle 결과만으로 운영 채택 X / PASS 시 새 prospective cycle 권고

Method (training 없음 / D1.Y json load + numpy reanalysis):
1. Threshold sensitivity: G2/G3 +0.3 → +0.8, +1.0 (G1/G4 그대로)
2. Bootstrap CI on mean Δ (paired percentile bootstrap / 5000 iters / 95% CI)
3. Hierarchical interpretation (cold_overall primary)

Compute: ~1분 (numpy bootstrap).

Usage:
    python3 scripts/d1_z_alt_reanalysis.py
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
D1Y_VALIDATION_PATH = ARTIFACTS_DIR / "d1_y_validation.json"
RESULTS_PATH = ARTIFACTS_DIR / "d1_z_alt_results.json"

THRESHOLD_TIERS = [
    {"name": "strict (R1 / D1.Y baseline)", "g1": 0.0, "g2": 0.3, "g3": 0.3, "g4": 0.1},
    {"name": "lax-1 (G2/G3 +0.8)", "g1": 0.0, "g2": 0.8, "g3": 0.8, "g4": 0.1},
    {"name": "lax-2 (G2/G3 +1.0)", "g1": 0.0, "g2": 1.0, "g3": 1.0, "g4": 0.1},
]

N_BOOT = 5000
RNG_SEED = 42


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
    """R1 P1.1 strict aggregate (D1.Y 정합)."""
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
    """Paired percentile bootstrap CI on mean delta."""
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot_means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)  # with replacement
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


def _hierarchical_interpret(boot: dict[str, dict]) -> dict:
    """R1 Q3 hierarchical interpretation: cold_overall primary."""
    cold_o = boot["delta_cold_overall"]
    primary_status = (
        "PASS" if cold_o["ci_upper"] <= 0
        else ("INCONCLUSIVE" if cold_o["ci_upper"] <= 0.5
              else "FAIL")
    )
    secondary_flags = []
    for cell in ("delta_cold_artsy", "delta_cold_saatchi", "delta_warm"):
        c = boot[cell]
        if c["ci_upper"] > 0.5:
            secondary_flags.append(f"{cell}: CI upper {c['ci_upper']:+.3f} > 0.5 (guard concern)")
    return {
        "primary_metric": "delta_cold_overall",
        "primary_ci_upper": cold_o["ci_upper"],
        "primary_status": primary_status,
        "secondary_guard_flags": secondary_flags,
    }


def main() -> None:
    logger.info("=" * 70)
    logger.info("D1.Z+alt: D1.Y reanalysis (analysis-only / non-binding)")
    logger.info("=" * 70)

    if not D1Y_VALIDATION_PATH.exists():
        raise FileNotFoundError(f"D1.Y validation 없음 ({D1Y_VALIDATION_PATH})")
    with D1Y_VALIDATION_PATH.open() as f:
        d1y = json.load(f)

    per_seed = d1y["per_seed"]
    seeds = sorted(int(s) for s in per_seed)
    logger.info("D1.Y per-seed loaded: %d seeds = %s", len(seeds), seeds)

    # Extract deltas
    deltas_arr = {
        "delta_cold_overall": np.array([per_seed[str(s)]["deltas"]["delta_cold_overall"] for s in seeds]),
        "delta_cold_artsy": np.array([per_seed[str(s)]["deltas"]["delta_cold_artsy"] for s in seeds]),
        "delta_cold_saatchi": np.array([per_seed[str(s)]["deltas"]["delta_cold_saatchi"] for s in seeds]),
        "delta_warm": np.array([per_seed[str(s)]["deltas"]["delta_warm"] for s in seeds]),
    }

    # 1. Threshold sensitivity
    logger.info("=" * 60)
    logger.info("D1.Z: G threshold sensitivity (3 tiers)")
    logger.info("=" * 60)
    threshold_results = []
    for tier in THRESHOLD_TIERS:
        verdicts = [
            _verdict(per_seed[str(s)]["deltas"], tier) for s in seeds
        ]
        agg = _aggregate_n10_strict(verdicts)
        cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
        per_seed_v = {str(s): v for s, v in zip(seeds, verdicts, strict=False)}
        threshold_results.append({
            "name": tier["name"],
            "thresholds": {k: tier[k] for k in ("g1", "g2", "g3", "g4")},
            "verdict_counts": cnt,
            "aggregate": agg,
            "per_seed_verdicts": per_seed_v,
        })
        logger.info("  %s: PASS=%d INC=%d FAIL=%d → %s",
                    tier["name"], cnt["PASS"], cnt["INCONCLUSIVE"], cnt["FAIL"], agg)

    # 2. Bootstrap CI
    logger.info("=" * 60)
    logger.info("D1.alt: Paired percentile bootstrap CI (n_boot=%d / 95%%)", N_BOOT)
    logger.info("=" * 60)
    bootstrap_results = {}
    for cell, deltas in deltas_arr.items():
        ci = _bootstrap_ci(deltas)
        bootstrap_results[cell] = ci
        logger.info("  %-20s mean=%+.4f std=%.4f n=%d CI95=[%+.3f, %+.3f] %s",
                    cell, ci["mean"], ci["std"], ci["n"],
                    ci["ci_lower"], ci["ci_upper"],
                    "✅" if ci["ci_upper_negative"] else "⚠️")

    # 3. Hierarchical interpretation
    hierarchical = _hierarchical_interpret(bootstrap_results)
    logger.info("Hierarchical interpretation:")
    logger.info("  primary (delta_cold_overall) status: %s (CI upper=%+.3f)",
                hierarchical["primary_status"], hierarchical["primary_ci_upper"])
    for flag in hierarchical["secondary_guard_flags"]:
        logger.info("  ⚠️ secondary: %s", flag)

    # 4. Combined exploratory finding (R1 P1.2 amendment / cap at hypothesis-generating)
    relaxed_pass = any(
        tr["aggregate"] in ("PASS", "PASS_with_caveat")
        for tr in threshold_results
        if "lax" in tr["name"]
    )
    bootstrap_primary_pass = hierarchical["primary_status"] == "PASS"

    if relaxed_pass or bootstrap_primary_pass:
        finding = "HYPOTHESIS_GENERATING_for_relaxed_cycle"
        explanation = (
            "Population-level evidence + relaxed threshold sensitivity가 D1 retune의 추가 검증 가치 시사. "
            "단 본 cycle은 analysis-only / non-binding / 운영 채택 발동 X. "
            "후속 = 새 prospective cycle (fresh seeds + 새 threshold rule preregister)."
        )
    elif (not relaxed_pass) and not bootstrap_primary_pass:
        finding = "D1_axis_terminate_confirmed"
        explanation = (
            "Strict + relaxed threshold + bootstrap statistical evidence 모두 fail. "
            "D1 axis 종결 결정 (D1.Y commit d774938) confirmed. 추가 cycle 가치 낮음."
        )
    else:
        finding = "EXPLORATORY_INCONCLUSIVE"
        explanation = "분석 결과 mixed / 추가 분석 가치 검토."

    logger.info("=" * 60)
    logger.info("Combined exploratory finding: %s", finding)
    logger.info("=" * 60)

    output = {
        "version": "v1-d1-z-alt-reanalysis",
        "decision_binding": False,
        "cycle_type": "analysis-only / hypothesis-generating",
        "input_source": str(D1Y_VALIDATION_PATH.relative_to(REPO)),
        "n_seeds": len(seeds),
        "seeds": seeds,
        "threshold_sensitivity": threshold_results,
        "bootstrap_ci": bootstrap_results,
        "hierarchical_interpretation": hierarchical,
        "combined_exploratory_finding": finding,
        "explanation": explanation,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved results: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"D1.Z+alt SUMMARY (analysis-only / non-binding)")
    print(f"Finding: {finding}")
    print("=" * 70)
    print()
    print("D1.Z (threshold sensitivity):")
    for tr in threshold_results:
        print(f"  {tr['name']:30s}: PASS={tr['verdict_counts']['PASS']:2d} "
              f"INC={tr['verdict_counts']['INCONCLUSIVE']:2d} "
              f"FAIL={tr['verdict_counts']['FAIL']:2d} → {tr['aggregate']}")
    print()
    print("D1.alt (bootstrap CI / 95%):")
    for cell, ci in bootstrap_results.items():
        marker = "✅ CI upper ≤ 0" if ci["ci_upper_negative"] else (
            "⚠️ CI includes 0" if ci["ci_includes_zero"] else "❌ CI > 0"
        )
        print(f"  {cell:24s} mean={ci['mean']:+.4f} CI95=[{ci['ci_lower']:+.3f}, {ci['ci_upper']:+.3f}] {marker}")
    print()
    print(f"Hierarchical primary (delta_cold_overall): {hierarchical['primary_status']}")
    if hierarchical['secondary_guard_flags']:
        for f in hierarchical['secondary_guard_flags']:
            print(f"  ⚠️ {f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
