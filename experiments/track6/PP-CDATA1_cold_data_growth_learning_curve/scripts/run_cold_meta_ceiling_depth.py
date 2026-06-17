#!/usr/bin/env python3
"""PP-CDATA2: Cold 메타 완성도 개선 상한 + breadth vs depth.

(1) 메타 완성도 상한: B모델(작품+메타) 100% 학습 후, cold test를 작가 메타 완성도
    (생년·경력·팔로워·작품수·전시·갤러리 중 채워진 개수)별로 나눠 정확도 측정.
    메타가 풍부한 작가가 얼마나 더 정확한지 = "신규 작가 메타를 채우면 도달 가능한 상한".

(2) breadth vs depth: 작가 100% 고정하고 작가당 학습 작품수를 1/3/5/all로 제한해 재학습.
    breadth(PP-CDATA1, 작가수 증가)와 대비해 Cold가 작가수(breadth)에 반응하는지
    작품수(depth)에 반응하는지 규명.
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
    REPO
    / "models"
    / "track6"
    / "cold_v03_research_upstream_refreeze_candidate"
    / "artifacts"
    / "feature_schema.json"
)
OUT = Path(__file__).resolve().parents[1] / "artifacts"

ARTWORK = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "size_bucket",
    "support_size_bucket",
]
LGB = dict(
    objective="quantile",
    alpha=0.5,
    n_estimators=430,
    num_leaves=31,
    learning_rate=0.035,
    min_child_samples=35,
    subsample=0.9,
    subsample_freq=1,
    colsample_bytree=0.9,
    reg_alpha=0.0,
    reg_lambda=1.2,
    max_depth=-1,
    n_jobs=-1,
    verbose=-1,
)
# 메타 완성도 점검 항목(있음=1)
META_KEYS = {
    "생년": "artist_meta_birth_year",
    "경력": "artist_meta_career_stage",
    "팔로워": "artist_meta_followers",
    "작품수": "artist_meta_total_works",
    "전시": "artist_exhibition_total_count",
    "갤러리": "gallery_tier_any_available_flag",
}


def prep(df, feats):
    x = df[feats].copy()
    cats = []
    for c in feats:
        if x[c].dtype == object or str(x[c].dtype) == "string":
            x[c] = x[c].astype("category")
            cats.append(c)
        else:
            x[c] = pd.to_numeric(x[c], errors="coerce")
    return x, cats


def metrics(actual_log, pred_log):
    actual = np.exp(np.asarray(actual_log, float))
    pred = np.clip(np.exp(np.asarray(pred_log, float)), 1000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "n": len(ape),
        "MdAPE": round(float(np.median(ape)), 4),
        "MAPE": round(float(np.mean(ape)), 4),
        "p95_APE": round(float(np.quantile(ape, 0.95)), 4),
    }


def main():
    df = pd.read_csv(STORE, low_memory=False)
    df["ln_price"] = np.log(pd.to_numeric(df["price_krw"], errors="coerce"))
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()
    feats_all = json.loads(SCHEMA.read_text())["pp_y2_feature_columns"]
    af = [
        f
        for f in feats_all
        if ("artist_meta" in f or "artist_exhibition" in f or "gallery" in f)
        and "search" not in f
        and f in df.columns
    ]
    feats = ARTWORK + af

    out = {}

    # (1) 메타 완성도 상한
    x, cats = prep(train, feats)
    model = LGBMRegressor(**{**LGB, "random_state": 20260617})
    model.fit(x, train["ln_price"].to_numpy(float), categorical_feature=cats)
    tx, _ = prep(test, feats)
    test = test.copy()
    test["pred_log"] = model.predict(tx)
    # 완성도 점수(0~6)
    comp = np.zeros(len(test))
    for _, col in META_KEYS.items():
        s = pd.to_numeric(test[col], errors="coerce")
        present = (s > 0) if col.endswith("flag") else (s.notna() & (s != 0))
        comp += present.to_numpy().astype(int)
    test["meta_completeness"] = comp.astype(int)
    tiers = {
        "빈약(0-2)": comp <= 2,
        "보통(3-4)": (comp >= 3) & (comp <= 4),
        "풍부(5-6)": comp >= 5,
    }
    out["meta_ceiling"] = {}
    for name, mask in tiers.items():
        if mask.sum() > 0:
            out["meta_ceiling"][name] = metrics(
                test.loc[mask, "ln_price"], test.loc[mask, "pred_log"]
            )
    out["meta_ceiling"]["전체"] = metrics(test["ln_price"], test["pred_log"])
    out["test_meta_coverage"] = {
        k: round(
            float(
                (
                    (pd.to_numeric(test[c], errors="coerce") > 0)
                    if c.endswith("flag")
                    else (
                        pd.to_numeric(test[c], errors="coerce").notna()
                        & (pd.to_numeric(test[c], errors="coerce") != 0)
                    )
                ).mean()
            ),
            2,
        )
        for k, c in META_KEYS.items()
    }

    # (2) depth: 작가 100% 고정, 작가당 작품수 cap
    out["depth"] = {}
    for cap in [1, 3, 5, 999]:
        shuffled = train.sample(frac=1.0, random_state=20260617)
        capped = shuffled[shuffled.groupby("artist_key").cumcount() < cap].copy()
        cx, ccats = prep(capped, feats)
        dm = LGBMRegressor(**{**LGB, "random_state": 20260617})
        dm.fit(cx, capped["ln_price"].to_numpy(float), categorical_feature=ccats)
        m = metrics(test["ln_price"], dm.predict(tx))
        out["depth"][f"작가당_최대{cap if cap < 999 else 'all'}작품"] = {
            "train_rows": len(capped),
            "train_artists": int(capped["artist_key"].nunique()),
            **m,
        }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_ceiling_depth.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
