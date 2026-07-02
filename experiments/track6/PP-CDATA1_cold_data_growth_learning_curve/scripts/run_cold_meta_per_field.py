#!/usr/bin/env python3
"""PP-CDATA3: Cold 메타를 '개수'가 아니라 '필드별'로 분해해 정확도 기여를 본다.

배경: 완성도 개수 tier에서 보통(3-4)이 풍부(5-6)/빈약(0-2)보다 오히려 나쁜
비단조 현상 → 개수는 거친 척도. 어떤 메타 필드가 실제로 정확도를 가르는지
필드 단위로 분해한다.

세 각도:
  (A) present/absent split  : 필드가 채워진 행 vs 빈 행의 cold test 정확도 (관측, 교란 가능)
  (B) ablation              : 전체 메타로 학습 후, 예측 시 한 필드(군)만 결측 처리해 악화폭 측정 (한계 기여)
  (C) 보통(3-4) 해부         : 3-4 구간에서 어떤 필드 조합이 흔한지 + 고가/outlier 집중 여부

입력/모델은 run_cold_meta_ceiling_depth.py와 동일(B모델, split_name train/test).
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
# 완성도 점검 필드(있음=1) — ceiling 실험과 동일
META_KEYS = {
    "생년": "artist_meta_birth_year",
    "경력": "artist_meta_career_stage",
    "팔로워": "artist_meta_followers",
    "작품수": "artist_meta_total_works",
    "전시": "artist_exhibition_total_count",
    "갤러리": "gallery_tier_any_available_flag",
}
# ablation 시 한 개념에 속한 모든 컬럼을 함께 결측 처리 (log 파생 포함)
CONCEPT_SUBSTR = {
    "생년": ["birth_year"],
    "경력": ["career"],
    "팔로워": ["followers"],
    "작품수": ["total_works"],
    "전시": ["exhibition"],
    "갤러리": ["gallery"],
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
        "n": int(len(ape)),
        "MdAPE": round(float(np.median(ape)), 4),
        "MAPE": round(float(np.mean(ape)), 4),
        "p95_APE": round(float(np.quantile(ape, 0.95)), 4),
    }


def present_mask(series, col):
    s = pd.to_numeric(series, errors="coerce")
    return (s > 0) if col.endswith("flag") else (s.notna() & (s != 0))


def main():
    df = pd.read_csv(STORE, low_memory=False)
    df["ln_price"] = np.log(pd.to_numeric(df["price_krw"], errors="coerce"))
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()

    feats_all = json.loads(SCHEMA.read_text())["pp_y2_feature_columns"]
    af = [
        f for f in feats_all
        if ("artist_meta" in f or "artist_exhibition" in f or "gallery" in f)
        and "search" not in f and f in df.columns
    ]
    feats = ARTWORK + af

    x, cats = prep(train, feats)
    model = LGBMRegressor(**{**LGB, "random_state": 20260617})
    model.fit(x, train["ln_price"].to_numpy(float), categorical_feature=cats)
    tx, _ = prep(test, feats)
    base_pred = model.predict(tx)

    out = {"meta_feature_columns_used": af, "baseline_test": metrics(test["ln_price"], base_pred)}

    # (A) present/absent split
    A = {}
    for ko, col in META_KEYS.items():
        m = present_mask(test[col], col).to_numpy()
        row = {"present_rate": round(float(m.mean()), 3)}
        if m.sum() > 0:
            row["present"] = metrics(test["ln_price"][m], base_pred[m])
        if (~m).sum() > 0:
            row["absent"] = metrics(test["ln_price"][~m], base_pred[~m])
        if "present" in row and "absent" in row:
            row["MdAPE_gap_absent_minus_present"] = round(
                row["absent"]["MdAPE"] - row["present"]["MdAPE"], 4
            )
        A[ko] = row
    out["A_present_absent"] = A

    # (B) ablation: 한 개념(군) 결측 처리 후 악화폭
    B = {}
    base_md = out["baseline_test"]["MdAPE"]
    for ko, subs in CONCEPT_SUBSTR.items():
        cols = [c for c in af if any(s in c for s in subs)]
        if not cols:
            continue
        tx_ab = tx.copy()
        for c in cols:
            if c.endswith("flag"):
                tx_ab[c] = 0
            else:
                tx_ab[c] = np.nan
        mm = metrics(test["ln_price"], model.predict(tx_ab))
        B[ko] = {
            "ablated_columns": cols,
            **mm,
            "MdAPE_delta_vs_baseline": round(mm["MdAPE"] - base_md, 4),
        }
    out["B_ablation"] = dict(sorted(B.items(), key=lambda kv: -kv[1]["MdAPE_delta_vs_baseline"]))

    # (C) 보통(3-4) 해부
    comp = np.zeros(len(test))
    flags = {}
    for ko, col in META_KEYS.items():
        p = present_mask(test[col], col).to_numpy().astype(int)
        flags[ko] = p
        comp += p
    test = test.copy()
    test["_comp"] = comp.astype(int)
    test["_ape"] = np.abs(
        np.clip(np.exp(base_pred), 1000.0, None) - np.exp(test["ln_price"].to_numpy(float))
    ) / np.clip(np.exp(test["ln_price"].to_numpy(float)), 1.0, None)
    C = {}
    for name, mask in {
        "빈약(0-2)": comp <= 2,
        "보통(3-4)": (comp >= 3) & (comp <= 4),
        "풍부(5-6)": comp >= 5,
    }.items():
        sub = test[mask]
        # 어떤 필드가 주로 채워져 있나 (해당 tier 내 present 비율)
        field_present = {ko: round(float(flags[ko][mask.to_numpy() if hasattr(mask, "to_numpy") else mask].mean()), 2) for ko in META_KEYS}
        C[name] = {
            "n": int(len(sub)),
            "median_price_krw": int(np.median(pd.to_numeric(sub["price_krw"], errors="coerce"))),
            "share_ape_over_2": round(float((sub["_ape"] > 2.0).mean()), 3),
            "field_present_rate": field_present,
        }
    out["C_tier_anatomy"] = C

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_per_field.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
