"""Phase 0 — multi-method consensus summary (DROP candidate 식별).

prereg §3.1 B-1 정합. Decision binding ❌ X.

코덱스 Phase 0 검수 P1 fix:
- prereg 4 method = CatBoost FI / XGBoost gain / SHAP (TreeSHAP) / Permutation
- SHAP 영역 의 의무 영역 = CB SHAP + XGB SHAP 영역 의 의무 평균 (단일 method 정합)
- DROP-A immediate = literal 4/4 = 0% (placeholder rule 정합)
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent
QUICK = json.loads((OUT_DIR / "phase0_importance_quick.json").read_text())
SHAP_PI = json.loads((OUT_DIR / "phase0_importance_shap_permutation.json").read_text())

FEATURES = QUICK["features"]

# SHAP 영역 의 의무 영역 의 의무 = CB + XGB 평균 (단일 method 영역 의 의무 정합)
shap_avg = {f: (SHAP_PI["catboost_shap_pct"][f] + SHAP_PI["xgboost_shap_pct"][f]) / 2.0
            for f in FEATURES}

# prereg 4 method 영역 의 의무 정합
methods = {
    "catboost_fi_pvc": QUICK["catboost_fi_pvc"],
    "xgboost_gain": QUICK["xgboost_gain"],
    "shap_treeshap_avg": shap_avg,  # CB SHAP + XGB SHAP 평균
    "permutation_catboost": SHAP_PI["permutation_catboost_pct"],
}
# 부가 산출 (record only / consensus 영역 의 의무 영역 의 의무 X)
extra_methods = {
    "catboost_shap": SHAP_PI["catboost_shap_pct"],
    "xgboost_shap": SHAP_PI["xgboost_shap_pct"],
    "xgboost_weight": QUICK["xgboost_weight"],
    "xgboost_cover": QUICK["xgboost_cover"],
}

# rank 산출 (각 method 별)
ranks: dict[str, dict[str, int]] = {}
for name, vals in {**methods, **extra_methods}.items():
    sorted_feats = sorted(vals.items(), key=lambda x: -x[1])
    ranks[name] = {f: i + 1 for i, (f, _) in enumerate(sorted_feats)}

# §3.1 B-1: 2/4 method 이상 영역 에서 영향도 하위 5% (또는 ≤ 0.5%)
# 4/4 method = 0% → 즉시 후보 (literal 0%)
threshold_low_pct = 0.5
threshold_zero = 0.01  # literal 0%

drop_votes: dict[str, list[str]] = {f: [] for f in FEATURES}
zero_votes: dict[str, list[str]] = {f: [] for f in FEATURES}
for name, vals in methods.items():
    for f in FEATURES:
        v = vals.get(f, 0.0)
        if v <= threshold_low_pct:
            drop_votes[f].append(name)
        if v < threshold_zero:
            zero_votes[f].append(name)

# DROP candidate consensus (prereg 4 method 영역 의 의무 정합)
drop_candidate_2of4 = sorted(
    [(f, len(drop_votes[f]), drop_votes[f]) for f in FEATURES],
    key=lambda x: -x[1],
)
# DROP-A immediate = literal 4/4 = 0% (prereg "placeholder 영역 (4/4 모두 = 0%)" 정합)
zero_4of4_strict = [f for f in FEATURES if len(zero_votes[f]) == 4]

# importance summary 영역 의 의무 print (prereg 4 method)
print("=" * 100)
print(f"{'feature':30s} {'CB_FI':>7s} {'XGB_gain':>9s} {'SHAP_avg':>9s} {'Perm':>7s}  | {'CB_SHAP':>8s} {'XGB_SHAP':>9s}")
print("-" * 100)
for f in FEATURES:
    cb_fi = methods["catboost_fi_pvc"].get(f, 0.0)
    xgb_gain = methods["xgboost_gain"].get(f, 0.0)
    shap = methods["shap_treeshap_avg"].get(f, 0.0)
    perm = methods["permutation_catboost"].get(f, 0.0)
    cb_shap = extra_methods["catboost_shap"].get(f, 0.0)
    xgb_shap = extra_methods["xgboost_shap"].get(f, 0.0)
    print(f"{f:30s} {cb_fi:>7.2f} {xgb_gain:>9.2f} {shap:>9.2f} {perm:>7.2f}  | {cb_shap:>8.2f} {xgb_shap:>9.2f}")

print()
print("=" * 100)
print("DROP candidate consensus (§3.1 B-1: 2/4 method 이상 영역 의 의무 ≤ 0.5%)")
print("prereg 4 method = CB FI / XGB gain / SHAP (CB+XGB 평균) / Permutation")
print("-" * 100)
for f, n_votes, voters in drop_candidate_2of4:
    if n_votes >= 2:
        print(f"  {f:30s} ({n_votes}/4 votes): {voters}")

print()
print("=" * 100)
print("DROP-A immediate (literal 4/4 모두 = 0% / prereg placeholder rule)")
print("-" * 100)
for f in zero_4of4_strict:
    print(f"  {f:30s} (4/4 zero): {zero_votes[f]}")

# JSON dump
out = {
    "phase": 0,
    "method": "multi-method consensus summary (P1 fix: prereg 4 method 정합)",
    "n_features": len(FEATURES),
    "features": FEATURES,
    "consensus_methods": list(methods.keys()),
    "methods_pct": methods,
    "extra_methods_pct": extra_methods,
    "ranks": ranks,
    "drop_consensus_2of4": [
        {"feature": f, "votes": n_votes, "voters": voters}
        for f, n_votes, voters in drop_candidate_2of4 if n_votes >= 2
    ],
    "zero_4of4_strict": zero_4of4_strict,
    "drop_a_immediate_candidates": zero_4of4_strict,  # prereg literal 4/4 zero
    "drop_b_low_candidates": [
        f for f in FEATURES if len(drop_votes[f]) >= 2 and f not in zero_4of4_strict
    ],
}
(OUT_DIR / "phase0_consensus_summary.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False)
)
print()
print(f"[OK] phase0_consensus_summary.json")
print(f"\nDROP-A 즉시 후보 (literal 4/4 모두 = 0%):")
print(f"  {out['drop_a_immediate_candidates']}")
print(f"\nDROP-B low 후보 (2/4 이상 ≤ 0.5% / DROP-A 외):")
print(f"  {out['drop_b_low_candidates']}")
