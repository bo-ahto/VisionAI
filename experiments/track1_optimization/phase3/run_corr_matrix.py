"""Phase 3.B — corr matrix 산출 + |corr|>0.95 redundant 식별.

prereg §3.4 정합. Decision binding ❌ X.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    load_data,
    prepare_features,
)

OUT = Path(__file__).parent / "phase3_corr_matrix.json"
THRESHOLD = 0.95


def main() -> None:
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = prepare_features(df)
    print(f"Loaded {len(X)} rows, {len(CB_FEATURES)} features")

    # categorical → numeric encoding (label encode 영역 의 의무 영역 의 의무 corr 영역 의 의무 영역)
    X_num = X.copy()
    for col in CAT_FEATURES:
        if col in X_num.columns:
            X_num[col] = pd.Categorical(X_num[col]).codes.astype(float)

    corr = X_num[CB_FEATURES].corr().abs()

    # |corr| > 0.95 pair 식별 (자기 영역 의 의무 X)
    high_pairs = []
    n = len(CB_FEATURES)
    for i in range(n):
        for j in range(i + 1, n):
            f_i = CB_FEATURES[i]
            f_j = CB_FEATURES[j]
            c = corr.iloc[i, j]
            if c > THRESHOLD:
                high_pairs.append({"feature_a": f_i, "feature_b": f_j, "corr": float(c)})

    # SHAP avg load (tie-break primary / 영향 작은 영역 의 의무 제거)
    shap_data = json.loads((Path(__file__).parent.parent / "phase0/phase0_consensus_summary.json").read_text())
    shap_avg = shap_data["methods_pct"]["shap_treeshap_avg"]

    # pair 별 영역 의 의무 = 영향 작은 영역 의 의무 영역 의 의무 = drop candidate
    drop_candidates = []
    for pair in high_pairs:
        s_a = shap_avg.get(pair["feature_a"], 0.0)
        s_b = shap_avg.get(pair["feature_b"], 0.0)
        if s_a <= s_b:
            drop_candidates.append({
                "pair": (pair["feature_a"], pair["feature_b"]),
                "drop": pair["feature_a"], "keep": pair["feature_b"],
                "drop_shap": s_a, "keep_shap": s_b,
                "corr": pair["corr"],
            })
        else:
            drop_candidates.append({
                "pair": (pair["feature_a"], pair["feature_b"]),
                "drop": pair["feature_b"], "keep": pair["feature_a"],
                "drop_shap": s_b, "keep_shap": s_a,
                "corr": pair["corr"],
            })

    # 영역 의 의무 영역 = 동일 feature 영역 의 의무 영역 의 의무 multi-pair 영역 의 의무 = 1 회만 영역 의 의무 정렬
    drop_priority = {}
    for c in drop_candidates:
        f = c["drop"]
        if f not in drop_priority or c["drop_shap"] < drop_priority[f]["drop_shap"]:
            drop_priority[f] = c

    drop_ordered = sorted(drop_priority.values(), key=lambda x: x["drop_shap"])

    out = {
        "phase": 3,
        "method": "corr matrix |corr|>0.95 + SHAP avg tie-break",
        "threshold": THRESHOLD,
        "n_features": len(CB_FEATURES),
        "n_high_corr_pairs": len(high_pairs),
        "high_corr_pairs": high_pairs,
        "drop_candidates_unique": [
            {"drop": c["drop"], "keep": c["keep"], "corr": c["corr"],
             "drop_shap": c["drop_shap"], "keep_shap": c["keep_shap"]}
            for c in drop_ordered
        ],
        "drop_candidates_ordered_shap_asc": [c["drop"] for c in drop_ordered],
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print(f"\n=== |corr| > {THRESHOLD} pairs ({len(high_pairs)}) ===")
    for p in sorted(high_pairs, key=lambda x: -x["corr"]):
        print(f"  {p['feature_a']:25s} ↔ {p['feature_b']:25s}  |corr|={p['corr']:.4f}")

    print(f"\n=== DROP candidates (영향 작은 영역 / SHAP avg ASC) ===")
    for c in drop_ordered:
        print(f"  drop={c['drop']:25s} keep={c['keep']:25s} corr={c['corr']:.4f} "
              f"shap_drop={c['drop_shap']:.3f} shap_keep={c['keep_shap']:.3f}")

    print(f"\n[OK] {OUT.name}")


if __name__ == "__main__":
    main()
