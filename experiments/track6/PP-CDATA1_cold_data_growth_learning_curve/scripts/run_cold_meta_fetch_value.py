#!/usr/bin/env python3
"""PP-CDATA4 (Stage 0): 서빙 시점 '메타 fetch'의 인과 가치 측정.

질문: 미지 작가의 메타를 (검색이든 플랫폼이든) 가져오면 가격 예측이 실제로 좋아지나?
설계(개입, 관측 아님): 메타 ground truth가 있는 작가에서 메타를 '가려(=미지 작가)' 예측 vs
'채워' 예측을 같은 행에서 비교 → delta가 fetch의 상한 가치.

시나리오(모델은 작품+메타로 학습한 B모델 하나, 서빙 입력만 바꿈):
  full            : 메타 전부 있음 (fetch 완벽 성공)
  none            : 메타 전부 결측 (미지 작가, fetch 없음)
  search_realistic: 검색으로 얻을 수 있는 것만(전시·갤러리·생년) 있음,
                    플랫폼 전용(작품수·팔로워·경력)은 결측

모집단: (a) 전체 cold test, (b) 메타 풍부(5-6) 작가 = ground truth 완전, 개입 깨끗.
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
    colsample_bytree=0.9, reg_alpha=0.0, reg_lambda=1.2, max_depth=-1,
    n_jobs=-1, verbose=-1,
)
META_KEYS = {
    "생년": "artist_meta_birth_year", "경력": "artist_meta_career_stage",
    "팔로워": "artist_meta_followers", "작품수": "artist_meta_total_works",
    "전시": "artist_exhibition_total_count", "갤러리": "gallery_tier_any_available_flag",
}
CONCEPT_SUBSTR = {
    "생년": ["birth_year"], "경력": ["career"], "팔로워": ["followers"],
    "작품수": ["total_works"], "전시": ["exhibition"], "갤러리": ["gallery"],
}
SEARCHABLE = ["전시", "갤러리", "생년"]          # 검색으로 얻을 수 있다고 가정
PLATFORM_ONLY = ["작품수", "팔로워", "경력"]      # 플랫폼 전용


def prep(df, feats):
    x = df[feats].copy()
    cats = []
    for c in feats:
        if x[c].dtype == object or str(x[c].dtype) == "string":
            x[c] = x[c].astype("category"); cats.append(c)
        else:
            x[c] = pd.to_numeric(x[c], errors="coerce")
    return x, cats


def metrics(actual_log, pred_log):
    actual = np.exp(np.asarray(actual_log, float))
    pred = np.clip(np.exp(np.asarray(pred_log, float)), 1000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {"n": int(len(ape)), "MdAPE": round(float(np.median(ape)), 4),
            "MAPE": round(float(np.mean(ape)), 4), "p95": round(float(np.quantile(ape, 0.95)), 4)}


def mask_concepts(tx, af, concepts):
    """주어진 개념들의 메타를 '결측'으로 만든다(미지 작가 시뮬레이션)."""
    out = tx.copy()
    subs = [s for c in concepts for s in CONCEPT_SUBSTR[c]]
    for col in af:
        if not any(s in col for s in subs):
            continue
        if col.endswith("_missing"):
            out[col] = 1
        elif col.endswith("flag"):
            out[col] = 0
        else:
            out[col] = np.nan
    return out


def main():
    df = pd.read_csv(STORE, low_memory=False)
    df["ln_price"] = np.log(pd.to_numeric(df["price_krw"], errors="coerce"))
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()
    feats_all = json.loads(SCHEMA.read_text())["pp_y2_feature_columns"]
    af = [f for f in feats_all if ("artist_meta" in f or "artist_exhibition" in f or "gallery" in f)
          and "search" not in f and f in df.columns]
    feats = ARTWORK + af

    x, cats = prep(train, feats)
    model = LGBMRegressor(**{**LGB, "random_state": 20260617})
    model.fit(x, train["ln_price"].to_numpy(float), categorical_feature=cats)
    tx, _ = prep(test, feats)

    # 메타 완성도 → 풍부(5-6) subset
    comp = np.zeros(len(test))
    for _, col in META_KEYS.items():
        s = pd.to_numeric(test[col], errors="coerce")
        comp += ((s > 0) if col.endswith("flag") else (s.notna() & (s != 0))).to_numpy().astype(int)
    rich = comp >= 5

    scenarios = {
        "full": [],
        "none": list(META_KEYS),
        "search_realistic(플랫폼전용 결측)": PLATFORM_ONLY,
    }
    out = {}
    for pop_name, popmask in {"전체_test": np.ones(len(test), bool), "메타풍부_5-6": rich}.items():
        sub = tx[popmask]; subln = test["ln_price"].to_numpy(float)[popmask]
        res = {}
        for sname, concepts in scenarios.items():
            txx = mask_concepts(sub, af, concepts) if concepts else sub
            res[sname] = metrics(subln, model.predict(txx))
        base = res["full"]["MdAPE"]
        for sname in res:
            res[sname]["MdAPE_delta_vs_full"] = round(res[sname]["MdAPE"] - base, 4)
        out[pop_name] = res

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_fetch_value.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
