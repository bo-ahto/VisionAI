#!/usr/bin/env python3
"""PP-CDATA5: 운영 수동 메타 입력의 상한 — 어느 필드를 넣어야 회복되나.

질문: 운영자가 메타 없는 작가에 메타를 직접 입력하면 정확도가 오르나? 어느 필드?
설계(개입): 메타 풍부(5-6) 작가에서 메타를 전부 가린 뒤(=미지작가), 특정 필드 묶음만
'복원'해 cold test MdAPE 회복폭 측정 = 수동 입력의 상한.

입력/모델: run_cold_meta_ceiling_depth.py와 동일(B모델, split_name train/test, n=3,099).
산출: artifacts/manual_meta_entry.json
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
META_KEYS = {
    "생년": "artist_meta_birth_year", "경력": "artist_meta_career_stage",
    "팔로워": "artist_meta_followers", "작품수": "artist_meta_total_works",
    "전시": "artist_exhibition_total_count", "갤러리": "gallery_tier_any_available_flag",
}
SUB = {
    "생년": ["birth_year"], "경력": ["career"], "팔로워": ["followers"],
    "작품수": ["total_works"], "전시": ["exhibition"], "갤러리": ["gallery"],
}
ALL = list(META_KEYS)


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
    feats = ARTWORK + af

    xtr, cats = prep(tr, feats)
    m = LGBMRegressor(**{**LGB, "random_state": 20260617})
    m.fit(xtr, tr["ln"].to_numpy(float), categorical_feature=cats)
    tx, _ = prep(te, feats)

    comp = np.zeros(len(te))
    for _, col in META_KEYS.items():
        s = pd.to_numeric(te[col], errors="coerce")
        comp += ((s > 0) if col.endswith("flag") else (s.notna() & (s != 0))).to_numpy().astype(int)
    rich = comp >= 5

    def mask(concepts):
        out = tx.copy(); subs = [s for c in concepts for s in SUB[c]]
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

    def md(maskarr, pred):
        a = np.exp(te["ln"].to_numpy(float)[maskarr]); p = np.clip(np.exp(pred[maskarr]), 1000, None)
        ape = np.abs(p - a) / np.clip(a, 1, None)
        return round(float(np.median(ape)), 4)

    # 시나리오 = KEEP할 개념; mask = 보수집합
    keep = {
        "full": ALL,
        "none": [],
        "팔로워·경력": ["팔로워", "경력"],
        "팔로워·경력·작품수": ["팔로워", "경력", "작품수"],
        "검색가능(전시·갤러리·생년)": ["전시", "갤러리", "생년"],
        "팔로워만": ["팔로워"],
        "경력만": ["경력"],
    }
    res = {}
    for name, kp in keep.items():
        mk = [c for c in ALL if c not in kp]
        res[name] = md(rich, m.predict(mask(mk)) if mk else m.predict(tx))
    full, none = res["full"], res["none"]
    out = {"n_rich": int(rich.sum()), "full": full, "none": none, "scenarios": {}}
    for name, v in res.items():
        if name in ("full", "none"):
            continue
        out["scenarios"][name] = {
            "MdAPE": v,
            "recover_vs_none": round(none - v, 4),
            "pct_of_gap": round(100 * (none - v) / (none - full)) if none != full else 0,
        }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manual_meta_entry.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
