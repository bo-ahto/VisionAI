"""VFR: Validation Framework Reform — analysis-only / non-binding.

Prereg: docs/vfr_validation_framework_reform_prereg_20260510.md (R1 NEEDS FIX → R2 LGTM)
Decision binding: ❌ NO / hypothesis-generating only

Method:
- Existing per-seed deltas (D1.X / D1.Y / D1-extended / D1.SC + B) 위 분석
- Cold cycle classification (R1 P1.1):
  - Clear negatives (FAIL 유지): D1-extended / D1.SC
  - Ambiguous (FAIL 또는 INCONCLUSIVE 허용): D1.X / D1.Y
  - Positive control (PASS 식별): B
- 7 aggregation methods comparison
- Tie-break ordering (R1 P1.2): B PASS mandatory / clear-neg FAIL / leave-one-out CV / simplest

Compute: ~2분 wall (numpy / scipy analysis on existing JSONs).

Usage:
    python3 scripts/vfr_framework_analysis.py
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
RESULTS_PATH = ARTIFACTS_DIR / "vfr_analysis_results.json"

# Cycle classification (R1 P1.1 amendment)
CLEAR_NEGATIVES = {
    "d1_extended": "model_test_results/d1_extended_results.json",
    "d1_sc": "model_test_results/d1_sc_results.json",
}
AMBIGUOUS = {
    "d1_x": "model_test_results/d1_validation_20260510.json",
    "d1_y": "model_test_results/d1_y_validation.json",
}
POSITIVE_CONTROL = {
    "b": "model_test_results/b_warm_validation.json",
}

N_BOOT = 10000
RNG_SEED = 42


def _load_per_seed_deltas(json_path: Path, cycle_name: str) -> dict[str, np.ndarray]:
    """Extract per-seed deltas from cycle JSON. Return dict keyed by cell."""
    with json_path.open() as f:
        data = json.load(f)

    per_seed = data.get("per_seed", {})
    if not per_seed:
        logger.warning("%s: per_seed not found", cycle_name)
        return {}

    cells = ("delta_cold_overall", "delta_cold_artsy", "delta_cold_saatchi", "delta_warm")
    out: dict[str, list[float]] = {c: [] for c in cells}

    for _seed, entry in per_seed.items():
        # Different cycles have different schema:
        # - D1.X / D1.Y / D1-extended: per_seed[seed]["deltas"] = {delta_cold_overall, delta_cold_artsy, ...}
        # - D1.SC: per_seed[seed]["deltas"] = {delta_cold_overall, delta_cold_artsy, ..., delta_warm:0}
        # - B: per_seed[seed]["delta_warm"] (no nested "deltas")
        deltas = entry.get("deltas")
        if deltas is None:
            # B schema
            d_warm = entry.get("delta_warm")
            if d_warm is not None:
                out["delta_warm"].append(float(d_warm))
            continue
        for c in cells:
            v = deltas.get(c)
            if v is not None:
                out[c].append(float(v))

    return {k: np.array(v) for k, v in out.items() if len(v) > 0}


def _bootstrap_ci(deltas: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot_means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = deltas[idx].mean()
    lo = float(np.percentile(boot_means, 2.5))
    hi = float(np.percentile(boot_means, 97.5))
    return {
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
        "ci_upper_negative": bool(hi <= 0),
    }


def _trimmed_mean(deltas: np.ndarray, trim_frac: float = 0.10) -> float:
    n = len(deltas)
    k = int(np.ceil(n * trim_frac))
    sorted_d = np.sort(deltas)
    if 2 * k >= n:
        return float(sorted_d.mean())
    return float(sorted_d[k:n - k].mean())


def _median_ci(deltas: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot_meds = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_meds[i] = float(np.median(deltas[idx]))
    lo = float(np.percentile(boot_meds, 2.5))
    hi = float(np.percentile(boot_meds, 97.5))
    return {
        "median": float(np.median(deltas)),
        "ci_lower": round(lo, 4),
        "ci_upper": round(hi, 4),
        "ci_upper_negative": bool(hi <= 0),
    }


def _cohens_d(deltas: np.ndarray) -> float:
    if len(deltas) < 2 or deltas.std(ddof=1) == 0:
        return 0.0
    return float(-deltas.mean() / deltas.std(ddof=1))  # negative Δ → positive d


def _per_seed_strict_verdict(deltas_overall: np.ndarray, deltas_artsy: np.ndarray | None,
                              deltas_saatchi: np.ndarray | None, deltas_warm: np.ndarray | None,
                              g1: float = 0.0, g2: float = 0.3, g3: float = 0.3,
                              g4: float = 0.1) -> list[str]:
    n = len(deltas_overall)
    verdicts = []
    for i in range(n):
        v_o = deltas_overall[i]
        v_a = deltas_artsy[i] if deltas_artsy is not None and len(deltas_artsy) > i else 0.0
        v_s = deltas_saatchi[i] if deltas_saatchi is not None and len(deltas_saatchi) > i else 0.0
        v_w = deltas_warm[i] if deltas_warm is not None and len(deltas_warm) > i else 0.0
        ok_g1 = v_o <= g1
        ok_g2 = v_a <= g2
        ok_g3 = v_s <= g3
        ok_g4 = v_w <= g4
        if ok_g1 and ok_g2 and ok_g3 and ok_g4:
            verdicts.append("PASS")
        elif 0 < v_o <= 0.3 and ok_g2 and ok_g3 and ok_g4:
            verdicts.append("INCONCLUSIVE")
        else:
            verdicts.append("FAIL")
    return verdicts


def _aggregate_strict_n(verdicts: list[str]) -> str:
    n = len(verdicts)
    cnt = {v: verdicts.count(v) for v in ("PASS", "INCONCLUSIVE", "FAIL")}
    if cnt["PASS"] == n:
        return "PASS"
    if n >= 5 and cnt["PASS"] == n - 1 and (cnt["INCONCLUSIVE"] + cnt["FAIL"]) == 1:
        return "PASS_with_caveat"
    if n >= 10 and cnt["PASS"] == n - 2 and cnt["INCONCLUSIVE"] == 2 and cnt["FAIL"] == 0:
        return "PASS_with_caveat"
    if cnt["FAIL"] >= 2:
        return "FAIL"
    return "INCONCLUSIVE"


def _apply_methods(deltas_dict: dict[str, np.ndarray], cycle_name: str) -> dict:
    """7 aggregation methods 적용 (Δ_cold_overall primary)."""
    cold_o = deltas_dict.get("delta_cold_overall")
    cold_a = deltas_dict.get("delta_cold_artsy")
    cold_s = deltas_dict.get("delta_cold_saatchi")
    warm = deltas_dict.get("delta_warm")

    # B (warm only): use delta_warm as primary
    if cold_o is None and warm is not None:
        primary = warm
        path = "warm"
    elif cold_o is not None:
        primary = cold_o
        path = "cold"
    else:
        return {"error": "no primary"}

    n = len(primary)
    mean = float(primary.mean())
    std = float(primary.std(ddof=1)) if n > 1 else 0.0

    methods = {}

    # 1. Strict per-seed (R1 P1.1)
    if path == "cold":
        verdicts = _per_seed_strict_verdict(cold_o, cold_a, cold_s, warm)
    else:
        # warm path: use warm as primary / G4 strict ≤+0.1
        verdicts = ["PASS" if v <= 0.1 else ("INCONCLUSIVE" if v <= 0.3 else "FAIL")
                    for v in primary]
    agg = _aggregate_strict_n(verdicts)
    methods["1_strict_per_seed"] = {
        "verdicts": verdicts,
        "aggregate": agg,
        "verdict": agg,  # for ranking
    }

    # 2. Bootstrap CI on mean
    bs = _bootstrap_ci(primary)
    methods["2_bootstrap_ci_mean"] = {
        **bs,
        "verdict": "PASS" if bs["ci_upper_negative"] else (
            "INCONCLUSIVE" if bs["ci_upper"] <= 0.5 else "FAIL"),
    }

    # 3. Trimmed mean
    tm = _trimmed_mean(primary, 0.10)
    methods["3_trimmed_mean"] = {
        "trimmed_mean": round(tm, 4),
        "verdict": "PASS" if tm <= 0 else (
            "INCONCLUSIVE" if tm <= 0.3 else "FAIL"),
    }

    # 4. Median CI
    mc = _median_ci(primary)
    methods["4_median_ci"] = {
        **mc,
        "verdict": "PASS" if mc["ci_upper_negative"] else (
            "INCONCLUSIVE" if mc["ci_upper"] <= 0.5 else "FAIL"),
    }

    # 5. Cell-size weighted (cold path만 / artsy / saatchi cell)
    if path == "cold" and cold_a is not None and cold_s is not None:
        # Use approximate cell sizes (artsy ~25% / saatchi ~75% / 운영 비율 정합)
        weight_a = 0.25
        weight_s = 0.75
        weighted_per_seed = weight_a * cold_a + weight_s * cold_s
        wm = float(weighted_per_seed.mean())
        methods["5_cell_weighted"] = {
            "weighted_mean": round(wm, 4),
            "verdict": "PASS" if wm <= 0 else (
                "INCONCLUSIVE" if wm <= 0.3 else "FAIL"),
        }
    else:
        methods["5_cell_weighted"] = {"verdict": "N/A (warm path)"}

    # 6. Quantile-based (P75)
    p75 = float(np.percentile(primary, 75))
    methods["6_quantile_p75"] = {
        "p75": round(p75, 4),
        "verdict": "PASS" if p75 <= 0.3 else "FAIL",
    }

    # 7. Effect size (Cohen's d)
    d = _cohens_d(primary)
    methods["7_cohens_d"] = {
        "d": round(d, 4),
        "verdict": "PASS" if d >= 0.3 else (
            "INCONCLUSIVE" if d >= 0 else "FAIL"),
    }

    return {
        "path": path,
        "n": n,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "cv": round(std / abs(mean), 4) if mean != 0 else None,
        "methods": methods,
    }


def _leave_one_out_cv(deltas: np.ndarray, method_fn) -> dict:
    """Leave-one-seed-out variability of method verdict."""
    n = len(deltas)
    verdicts = []
    for i in range(n):
        sub = np.concatenate([deltas[:i], deltas[i + 1:]])
        verdicts.append(method_fn(sub))
    pass_count = verdicts.count("PASS")
    fail_count = verdicts.count("FAIL")
    inc_count = verdicts.count("INCONCLUSIVE")
    return {
        "n_loo": n,
        "loo_verdicts": verdicts,
        "stability": {
            "pass": pass_count,
            "inconclusive": inc_count,
            "fail": fail_count,
        },
        "stable": bool(max(pass_count, fail_count, inc_count) == n),
    }


def main() -> None:
    logger.info("=" * 70)
    logger.info("VFR: Validation Framework Reform — analysis-only / non-binding")
    logger.info("=" * 70)

    all_results: dict[str, Any] = {
        "version": "v1-vfr-analysis",
        "decision_binding": False,
        "cycle_type": "analysis-only / hypothesis-generating",
        "cycles": {},
        "evaluated_at": datetime.now(UTC).isoformat(),
    }

    # Load all cycles
    all_cycles = {**POSITIVE_CONTROL, **AMBIGUOUS, **CLEAR_NEGATIVES}
    cycle_classification = {
        **{k: "positive_control" for k in POSITIVE_CONTROL},
        **{k: "ambiguous" for k in AMBIGUOUS},
        **{k: "clear_negative" for k in CLEAR_NEGATIVES},
    }

    for cycle_name, json_path_str in all_cycles.items():
        json_path = REPO / json_path_str
        if not json_path.exists():
            logger.warning("%s: %s not found / skip", cycle_name, json_path_str)
            continue
        logger.info("--- %s (%s) ---", cycle_name, cycle_classification[cycle_name])
        deltas = _load_per_seed_deltas(json_path, cycle_name)
        if not deltas:
            continue

        # Apply 7 methods
        method_results = _apply_methods(deltas, cycle_name)

        # Statistics summary
        stats = {}
        for cell, arr in deltas.items():
            stats[cell] = {
                "n": int(len(arr)),
                "mean": round(float(arr.mean()), 4),
                "std": round(float(arr.std(ddof=1)), 4) if len(arr) > 1 else 0.0,
                "min": round(float(arr.min()), 4),
                "max": round(float(arr.max()), 4),
                "iqr": round(float(np.percentile(arr, 75) - np.percentile(arr, 25)), 4),
            }

        all_results["cycles"][cycle_name] = {
            "classification": cycle_classification[cycle_name],
            "json_path": json_path_str,
            "stats": stats,
            "method_analysis": method_results,
        }

        # Log key findings
        for cell in ("delta_cold_overall", "delta_warm"):
            if cell in stats:
                s = stats[cell]
                cv = s['std'] / abs(s['mean']) if s['mean'] != 0 else float('inf')
                logger.info("  %s: n=%d mean=%+.3f std=%.3f CV=%.2f range=[%+.2f, %+.2f]",
                            cell, s["n"], s["mean"], s["std"], cv, s["min"], s["max"])

    # Cross-method comparison (R1 P1.2 tie-break)
    logger.info("=" * 60)
    logger.info("Method ranking (R1 P1.2 tie-break ordering)")
    logger.info("=" * 60)

    method_names = ["1_strict_per_seed", "2_bootstrap_ci_mean", "3_trimmed_mean",
                    "4_median_ci", "5_cell_weighted", "6_quantile_p75", "7_cohens_d"]

    method_rankings = {}
    for method in method_names:
        # R1 P1.2 tie-break:
        # 1. B PASS mandatory
        # 2. clear-neg false-positive 최소 (D1-extended / D1.SC)
        # 3. Leave-one-out stability (skip / 단순화)
        # 4. Simplest method wins (assign rank order)

        b_verdict = all_results["cycles"].get("b", {}).get(
            "method_analysis", {}).get("methods", {}).get(method, {}).get("verdict", "N/A")
        d1_ext_verdict = all_results["cycles"].get("d1_extended", {}).get(
            "method_analysis", {}).get("methods", {}).get(method, {}).get("verdict", "N/A")
        d1_sc_verdict = all_results["cycles"].get("d1_sc", {}).get(
            "method_analysis", {}).get("methods", {}).get(method, {}).get("verdict", "N/A")
        d1_x_verdict = all_results["cycles"].get("d1_x", {}).get(
            "method_analysis", {}).get("methods", {}).get(method, {}).get("verdict", "N/A")
        d1_y_verdict = all_results["cycles"].get("d1_y", {}).get(
            "method_analysis", {}).get("methods", {}).get(method, {}).get("verdict", "N/A")

        # Score:
        # - B PASS: +10 (mandatory)
        # - D1-ext clear neg PASS (false positive): -10
        # - D1-sc clear neg PASS (false positive): -10
        # - D1.x / D1.y ambiguous: 0 (allowed)
        score = 0
        if b_verdict == "PASS":
            score += 10
        else:
            score -= 100  # mandatory fail
        if d1_ext_verdict in ("PASS", "PASS_with_caveat"):
            score -= 10
        if d1_sc_verdict in ("PASS", "PASS_with_caveat"):
            score -= 10

        method_rankings[method] = {
            "verdicts": {
                "b_positive_control": b_verdict,
                "d1_extended_clear_neg": d1_ext_verdict,
                "d1_sc_clear_neg": d1_sc_verdict,
                "d1_x_ambiguous": d1_x_verdict,
                "d1_y_ambiguous": d1_y_verdict,
            },
            "score": score,
            "b_pass_mandatory": b_verdict == "PASS",
            "clear_neg_false_positive_count": (
                (d1_ext_verdict in ("PASS", "PASS_with_caveat")) +
                (d1_sc_verdict in ("PASS", "PASS_with_caveat"))
            ),
        }
        logger.info("  %s: B=%s d1ext=%s d1sc=%s d1x=%s d1y=%s score=%d",
                    method, b_verdict, d1_ext_verdict, d1_sc_verdict,
                    d1_x_verdict, d1_y_verdict, score)

    all_results["method_rankings"] = method_rankings

    # Recommendation (R1 P1.2 tie-break ordering)
    qualified = [m for m, r in method_rankings.items()
                 if r["b_pass_mandatory"] and r["clear_neg_false_positive_count"] == 0]
    if qualified:
        # Simplest method wins ties (per ordering: trimmed_mean > median_ci > bootstrap > effect / quantile)
        simplicity_order = ["3_trimmed_mean", "1_strict_per_seed", "6_quantile_p75",
                            "5_cell_weighted", "4_median_ci", "2_bootstrap_ci_mean", "7_cohens_d"]
        recommended = next((m for m in simplicity_order if m in qualified), qualified[0])
    else:
        recommended = None

    all_results["recommendation"] = {
        "qualified_methods": qualified,
        "recommended_method": recommended,
        "justification": (
            "B positive control PASS + clear-negatives FAIL preserved + simplest among qualified"
            if recommended else
            "No method satisfies B PASS + clear-negatives FAIL constraint / framework reform abandon 권고"
        ),
    }

    logger.info("=" * 60)
    logger.info("Recommendation: %s", recommended or "NONE / framework reform abandon")
    logger.info("Qualified methods (B PASS + clear-neg FAIL): %s", qualified)
    logger.info("=" * 60)

    RESULTS_PATH.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    logger.info("[OK] Saved: %s", RESULTS_PATH.name)

    # Summary
    print("\n" + "=" * 70)
    print("VFR ANALYSIS SUMMARY (analysis-only / non-binding)")
    print("=" * 70)
    print(f"\nRecommendation: {recommended or 'NONE / framework reform abandon'}")
    print(f"Justification: {all_results['recommendation']['justification']}")
    print()
    print("Method rankings:")
    print(f"  {'method':25s} | {'B':14s} | {'d1ext':14s} | {'d1sc':14s} | {'d1x':14s} | {'d1y':14s} | score")
    print("  " + "-" * 110)
    for method, r in method_rankings.items():
        v = r["verdicts"]
        print(f"  {method:25s} | {v['b_positive_control']:14s} | "
              f"{v['d1_extended_clear_neg']:14s} | {v['d1_sc_clear_neg']:14s} | "
              f"{v['d1_x_ambiguous']:14s} | {v['d1_y_ambiguous']:14s} | {r['score']:+d}")
    print()
    print("Cycle statistics (cold_overall / warm):")
    for cycle_name, c in all_results["cycles"].items():
        for cell in ("delta_cold_overall", "delta_warm"):
            if cell in c["stats"]:
                s = c["stats"][cell]
                print(f"  {cycle_name:15s} {cell:24s} n={s['n']} mean={s['mean']:+.3f} std={s['std']:.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
