#!/usr/bin/env python3
"""PP-CDATA7: 메타 부분집합 '전수' 탐색 (2^6=64 조합) + 작가-클러스터 부트스트랩.

PP-CDATA6은 손으로 고른 10개만 봤다(편향). 여기선 6개 메타 개념의 모든 부분집합
(64개)을 각각 재학습해 full 대비 MdAPE delta를 작가-클러스터 CI로 판정.
주의: 64개 동시 비교 = 다중비교. 95% CI면 우연히 ~2~3개가 "유의"로 나올 수 있으니
"full을 이기는 조합" 개수를 그 기대치와 비교해 해석.

산출: artifacts/meta_subset_exhaustive.json
"""
from __future__ import annotations

import itertools
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[4]
STORE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"
SCHEMA = (
    REPO / "models" / "track6" / "cold_v03_research_upstream_refreeze_candidate"
    / "artifacts" / "feature_schema.json"
)
OUT = Path(__file__).resolve().parents[1] / "artifacts"

ARTWORK = [
    "width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
    "has_depth", "is_3d_candidate", "medium_category", "support_category",
    "size_bucket", "support_size_bucket",
]
LGB = dict(
    objective="quantile", alpha=0.5, n_estimators=430, num_leaves=31,
    learning_rate=0.035, min_child_samples=35, subsample=0.9, subsample_freq=1,
    colsample_bytree=0.9, reg_lambda=1.2, n_jobs=-1, verbose=-1,
)
SUB = {
    "생년": ["birth_year"], "경력": ["career"], "팔로워": ["followers"],
    "작품수": ["total_works"], "전시": ["exhibition"], "갤러리": ["gallery"],
}
CONCEPTS = list(SUB)
B = 2000
SEED = 20260618


def prep(d, f):
    x = d[f].copy(); cats = []
    for c in f:
        if x[c].dtype == object or str(x[c].dtype) == "string":
            x[c] = x[c].astype("category"); cats.append(c)
        else:
            x[c] = pd.to_numeric(x[c], errors="coerce")
    return x, cats


def main():
    df = pd.read_csv(STORE, low_memory=False)
    df["ln"] = np.log(pd.to_numeric(df["price_krw"], errors="coerce"))
    tr = df[(df.split_name == "train") & df.ln.notna()].copy()
    te = df[(df.split_name == "test") & df.ln.notna()].copy()
    cols = json.loads(SCHEMA.read_text())["pp_y2_feature_columns"]
    af = [f for f in cols if ("artist_meta" in f or "artist_exhibition" in f or "gallery" in f)
          and "search" not in f and f in df.columns]

    def concept_cols(concepts):
        subs = [s for c in concepts for s in SUB[c]]
        return [c for c in af if any(s in c for s in subs)]

    yte = te["ln"].to_numpy(float); ate = np.exp(yte)

    # 모든 64개 부분집합 재학습 → ape
    subsets = []
    for r in range(len(CONCEPTS) + 1):
        subsets.extend(itertools.combinations(CONCEPTS, r))
    ape = {}
    for sset in subsets:
        feats = ARTWORK + concept_cols(list(sset))
        xtr, cats = prep(tr, feats)
        m = LGBMRegressor(**{**LGB, "random_state": SEED})
        m.fit(xtr, tr["ln"].to_numpy(float), categorical_feature=cats)
        xte, _ = prep(te, feats)
        p = np.clip(np.exp(m.predict(xte)), 1000.0, None)
        ape["+".join(sset) if sset else "작품만"] = np.abs(p - ate) / np.clip(ate, 1.0, None)

    full_key = "+".join(CONCEPTS)
    # 작가-클러스터 부트스트랩 (모든 조합 동일 resample 인덱스)
    rng = np.random.default_rng(SEED)
    artist = te["artist_key"].to_numpy()
    uniq = pd.unique(artist); n_art = len(uniq)
    groups = [np.where(artist == a)[0] for a in uniq]
    boot_idx = [np.concatenate([groups[i] for i in rng.integers(0, n_art, size=n_art)])
                for _ in range(B)]

    def boot_median(a):
        return np.array([np.median(a[ix]) for ix in boot_idx])

    full_boot = boot_median(ape[full_key])
    rows = []
    for name, a in ape.items():
        boot = boot_median(a); delta = boot - full_boot
        lo, hi = np.percentile(delta, [2.5, 97.5])
        rows.append({
            "subset": name,
            "k": 0 if name == "작품만" else name.count("+") + 1,
            "MdAPE": round(float(np.median(a)), 4),
            "p95_APE": round(float(np.quantile(a, 0.95)), 4),
            "delta_vs_full": round(float(np.median(delta)), 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "beats_full_sig": bool(hi < 0),
            "worse_than_full_sig": bool(lo > 0),
        })
    rows.sort(key=lambda r: r["MdAPE"])
    n_beat = sum(r["beats_full_sig"] for r in rows)
    out = {
        "test_n": len(yte), "test_artists": int(n_art), "n_subsets": len(rows),
        "bootstrap": B, "bootstrap_unit": "artist_cluster",
        "full_MdAPE": round(float(np.median(ape[full_key])), 4),
        "n_subsets_beating_full_sig": n_beat,
        "expected_false_sig_at_95pct": round(0.025 * len(rows), 1),
        "ranked": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_subset_exhaustive.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"subsets={len(rows)}, full MdAPE={out['full_MdAPE']}, "
          f"full을 유의하게 이김={n_beat} (95%CI 다중비교 기대 거짓양성 ~{out['expected_false_sig_at_95pct']})")
    print(f"\n{'subset':<34}{'k':>2}{'MdAPE':>8}{'p95':>8}{'Δfull':>9}{'CI95':>20} {'판정'}")
    for r in rows[:14]:
        ci = f"[{r['ci95'][0]:+.4f},{r['ci95'][1]:+.4f}]"
        v = "유의↑" if r["beats_full_sig"] else ("유의↓" if r["worse_than_full_sig"] else "무의")
        print(f"{r['subset']:<34}{r['k']:>2}{r['MdAPE']:>8}{r['p95_APE']:>8}{r['delta_vs_full']:>+9.4f}{ci:>20} {v}")


if __name__ == "__main__":
    main()
