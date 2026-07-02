#!/usr/bin/env python3
"""PP-CDATA6: 메타 부분집합 feature selection (재학습 + 부트스트랩 CI).

질문: 메타 필드 개수·종류를 골라 재학습하면 "전부 쓰기(full)"보다 유의하게 나은
조합이 있는가? (마스킹 proxy 아닌 진짜 재학습, 다중비교 과적합 방지 위해 가설
기반 소수 후보만, 차이는 부트스트랩 CI로 노이즈 초과 여부 판정.)

입력/모델: B모델(LightGBM Quantile q50), cold feature store, split_name train/test, test n=3,099.
산출: artifacts/meta_subset_search.json
"""
from __future__ import annotations

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
# 가설 기반 후보(개수·종류 다양) — KEEP할 개념
CANDIDATES = {
    "작품만(메타X)": [],
    "full(전체6)": list(SUB),
    "팔로워+경력": ["팔로워", "경력"],
    "팔로워+경력+전시": ["팔로워", "경력", "전시"],
    "팔로워+경력+갤러리": ["팔로워", "경력", "갤러리"],
    "팔로워+경력+작품수": ["팔로워", "경력", "작품수"],
    "팔로워+경력+전시+갤러리": ["팔로워", "경력", "전시", "갤러리"],
    "전시+갤러리": ["전시", "갤러리"],
    "팔로워": ["팔로워"],
    "경력": ["경력"],
}
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

    yte = te["ln"].to_numpy(float)
    ate = np.exp(yte)
    ape = {}
    for name, concepts in CANDIDATES.items():
        feats = ARTWORK + concept_cols(concepts)
        xtr, cats = prep(tr, feats)
        m = LGBMRegressor(**{**LGB, "random_state": SEED})
        m.fit(xtr, tr["ln"].to_numpy(float), categorical_feature=cats)
        xte, _ = prep(te, feats)
        p = np.clip(np.exp(m.predict(xte)), 1000.0, None)
        ape[name] = np.abs(p - ate) / np.clip(ate, 1.0, None)

    # 작가 단위(클러스터) 부트스트랩 — 독립 단위는 행이 아니라 작가(test 200명).
    # 행 부트스트랩은 작가 내 상관을 무시해 CI를 과소평가(codex 지적).
    rng = np.random.default_rng(SEED)
    artist = te["artist_key"].to_numpy()
    uniq = pd.unique(artist)
    n_art = len(uniq)
    groups = [np.where(artist == a)[0] for a in uniq]
    boot_idx = [np.concatenate([groups[i] for i in rng.integers(0, n_art, size=n_art)])
                for _ in range(B)]

    def boot_median(a):
        return np.array([np.median(a[ix]) for ix in boot_idx])

    full_boot = boot_median(ape["full(전체6)"])
    out = {"test_n": len(yte), "test_artists": int(n_art), "bootstrap": B,
           "bootstrap_unit": "artist_cluster", "results": {}}
    for name, a in ape.items():
        md = float(np.median(a)); p95 = float(np.quantile(a, 0.95))
        boot = boot_median(a)
        delta = boot - full_boot  # subset - full; 음수면 full보다 나음
        lo, hi = np.percentile(delta, [2.5, 97.5])
        out["results"][name] = {
            "MdAPE": round(md, 4),
            "p95_APE": round(p95, 4),
            "delta_vs_full_median": round(float(np.median(delta)), 4),
            "delta_ci95_artist_cluster": [round(float(lo), 4), round(float(hi), 4)],
            "better_than_full_sig": bool(hi < 0),   # 전 CI가 0 미만 = 유의하게 나음
            "worse_than_full_sig": bool(lo > 0),
        }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_subset_search.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
