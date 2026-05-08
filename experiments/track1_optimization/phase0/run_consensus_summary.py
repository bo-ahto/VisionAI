"""Phase 0 — multi-method consensus summary (DROP candidate 식별).

prereg §3.1 B-1 정합. Decision binding ❌ X.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent
QUICK = json.loads((OUT_DIR / "phase0_importance_quick.json").read_text())
SHAP_PI = json.loads((OUT_DIR / "phase0_importance_shap_permutation.json").read_text())

FEATURES = QUICK["features"]
methods = {
    "catboost_fi_pvc": QUICK["catboost_fi_pvc"],
    "xgboost_gain": QUICK["xgboost_gain"],
    "catboost_shap": SHAP_PI["catboost_shap_pct"],
    "xgboost_shap": SHAP_PI["xgboost_shap_pct"],
    "permutation_catboost": SHAP_PI["permutation_catboost_pct"],
}

# rank 산출 (각 method 별)
ranks: dict[str, dict[str, int]] = {}
for name, vals in methods.items():
    sorted_feats = sorted(vals.items(), key=lambda x: -x[1])
    ranks[name] = {f: i + 1 for i, (f, _) in enumerate(sorted_feats)}

# 영역 별 영역 의 의무 vote (DROP candidate)
# §3.1 B-1: 2/4 method 이상 영역 에서 영향도 하위 5% (또는 ≤ 0.5%)
# 4/4 method = 0% → 즉시 후보
n = len(FEATURES)
threshold_5pct_rank = int(n * 0.95) + 1  # 하위 5% = rank > 30
threshold_low_pct = 0.5  # ≤ 0.5%

drop_votes: dict[str, list[str]] = {f: [] for f in FEATURES}
zero_votes: dict[str, list[str]] = {f: [] for f in FEATURES}
for name, vals in methods.items():
    if name == "xgboost_gain":
        continue  # quick 영역 의 의무 영역 / XGB gain 영역 의 의무 = SHAP 영역 의 의무 영역 의 의무 영역 의 의무 정합
    for f in FEATURES:
        v = vals.get(f, 0.0)
        if v <= threshold_low_pct:
            drop_votes[f].append(name)
        if v < 0.01:
            zero_votes[f].append(name)

# 4 method 중 (CB FI / CB SHAP / XGB SHAP / Permutation) 영역 의 의무 vote
relevant_methods = ["catboost_fi_pvc", "catboost_shap", "xgboost_shap", "permutation_catboost"]
relevant_methods_n = len(relevant_methods)

# DROP candidate consensus
drop_candidate_2of4 = sorted(
    [(f, len([m for m in drop_votes[f] if m in relevant_methods]), drop_votes[f])
     for f in FEATURES],
    key=lambda x: -x[1],
)
zero_4of4 = [f for f in FEATURES
             if len([m for m in zero_votes[f] if m in relevant_methods]) >= 3]

# importance summary 영역 의 의무 print
print("=" * 90)
print(f"{'feature':30s} {'CB_FI':>7s} {'CB_SHAP':>8s} {'XGB_SHAP':>8s} {'Perm':>6s} {'XGB_gain':>8s}")
print("-" * 90)
for f in FEATURES:
    cb_fi = methods["catboost_fi_pvc"].get(f, 0.0)
    cb_shap = methods["catboost_shap"].get(f, 0.0)
    xgb_shap = methods["xgboost_shap"].get(f, 0.0)
    perm = methods["permutation_catboost"].get(f, 0.0)
    xgb_gain = methods["xgboost_gain"].get(f, 0.0)
    print(f"{f:30s} {cb_fi:>7.2f} {cb_shap:>8.2f} {xgb_shap:>8.2f} {perm:>6.2f} {xgb_gain:>8.2f}")

print()
print("=" * 90)
print("DROP candidate consensus (§3.1 B-1: 2/4 method 이상 영역 의 의무 ≤ 0.5%)")
print("-" * 90)
for f, n_votes, voters in drop_candidate_2of4:
    if n_votes >= 2:
        print(f"  {f:30s} ({n_votes}/4 votes): {voters}")

print()
print("=" * 90)
print("ZERO consensus (3+ method 영역 의 의무 < 0.01% / DROP-A 즉시 후보)")
print("-" * 90)
for f in zero_4of4:
    voters = [m for m in zero_votes[f] if m in relevant_methods]
    print(f"  {f:30s} ({len(voters)}/4 votes): {voters}")

# JSON dump
out = {
    "phase": 0,
    "method": "multi-method consensus summary",
    "n_features": len(FEATURES),
    "features": FEATURES,
    "methods_pct": methods,
    "ranks": ranks,
    "drop_consensus_2of4": [
        {"feature": f, "votes": n_votes, "voters": voters}
        for f, n_votes, voters in drop_candidate_2of4 if n_votes >= 2
    ],
    "zero_consensus_3of4": zero_4of4,
    "drop_a_immediate_candidates": [
        f for f in FEATURES
        if methods["catboost_fi_pvc"].get(f, 0.0) < 0.01
        and methods["catboost_shap"].get(f, 0.0) < 0.5
        and methods["permutation_catboost"].get(f, 0.0) < 0.5
    ],
}
(OUT_DIR / "phase0_consensus_summary.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False)
)
print()
print(f"[OK] phase0_consensus_summary.json")
print(f"\nDROP-A 즉시 후보 (CB FI < 0.01% AND CB SHAP < 0.5% AND Perm < 0.5%):")
print(f"  {out['drop_a_immediate_candidates']}")
