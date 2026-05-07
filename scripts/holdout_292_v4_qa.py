"""검증 4 (lightweight): 292건 외부 데이터에 대한 v4 매핑 QA.

본 모델 inference는 feature engineering 재현 필요로 별도 PR 권장.
본 스크립트는 alias QA + tier 분포 + coverage 점검까지.

Usage: python3 scripts/holdout_292_v4_qa.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


def _normalize(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def main():
    df = pd.read_csv(DATA / "1차 시장 데이터 - 전달본_260504.csv")
    print(f"292 데이터: {len(df)}건")

    # 한글명 매핑 (이미 KR로 표기됨)
    v4 = pd.read_csv(DATA / "art_gallery_tier_list_v4.csv").dropna(subset=["명칭"])
    tier_lookup = {_normalize(r["명칭"]): (str(r["티어"]).strip(), str(r["분류"]).strip()) for _, r in v4.iterrows()}

    # 영문 alias map (Artsy 학습 데이터용 — 292는 한글이라 직접 매칭 시도)
    alias_df = pd.read_csv(DATA / "gallery_alias_map.csv")
    alias_kr_to_kr = {}  # 일부 한글이 v4와 다른 경우 alias 추가 가능
    # 292의 한글명이 v4와 다르면 alias로 매칭

    rows = []
    for _, r in df.iterrows():
        kr = _normalize(r["gallery_name(KR)"])
        en = _normalize(r["gallery_name(EN)"])
        # 1차 시도: 한글 직접 매칭
        if kr in tier_lookup:
            tier, cls = tier_lookup[kr]
            match_type = "kr_direct"
        # 2차: alias map (영문→한글) 후 매칭 (Artsy alias 활용)
        else:
            mapped = None
            for _, a in alias_df.iterrows():
                if _normalize(a["영문명"]) == en:
                    mapped = _normalize(a["한글명"])
                    break
            if mapped and mapped in tier_lookup:
                tier, cls = tier_lookup[mapped]
                match_type = f"en_alias({mapped})"
            else:
                tier, cls = "Tier E (미매칭)", "미매칭"
                match_type = "unmatched"
        rows.append({
            "gallery_kr": kr, "gallery_en": en, "tier": tier, "class": cls, "match_type": match_type,
        })

    res = pd.DataFrame(rows)
    print("\n=== 292 작품의 갤러리별 매칭 결과 ===")
    by_gallery = res.groupby(["gallery_kr", "tier", "match_type"]).size().reset_index(name="작품수")
    print(by_gallery.sort_values("작품수", ascending=False).to_string(index=False))

    print("\n=== Tier 분포 ===")
    print(res["tier"].value_counts(dropna=False).to_string())

    print("\n=== match_type 분포 ===")
    print(res["match_type"].value_counts(dropna=False).to_string())

    # 미매칭 갤러리만 따로
    unmatched = res[res["match_type"] == "unmatched"]
    if len(unmatched):
        print("\n=== 미매칭 갤러리 (검수 필요) ===")
        u = unmatched.groupby(["gallery_kr", "gallery_en"]).size().reset_index(name="작품수").sort_values("작품수", ascending=False)
        print(u.to_string(index=False))

    # 가격 통계 (Tier별, 매칭 케이스만)
    df_aug = df.copy()
    df_aug["tier_v4"] = res["tier"].values
    df_aug["price_won"] = df_aug["price"].str.replace("₩", "").str.replace(",", "").astype(float)

    print("\n=== Tier별 가격 통계 (292 holdout) ===")
    stats = df_aug.groupby("tier_v4")["price_won"].agg(["count", "median", "mean"]).round(0)
    print(stats.to_string())

    # 산출물
    OUT_DIR.mkdir(exist_ok=True)
    summary = {
        "n_total": len(df),
        "n_galleries": int(df["gallery_name(KR)"].nunique()),
        "tier_distribution": res["tier"].value_counts().to_dict(),
        "match_type_distribution": res["match_type"].value_counts().to_dict(),
        "matching_rate_pct": round(100 * (res["match_type"] != "unmatched").sum() / len(res), 1),
        "unmatched_galleries": [
            {"kr": k, "en": e, "n": int(n)}
            for (k, e), n in res[res["match_type"] == "unmatched"].groupby(["gallery_kr", "gallery_en"]).size().items()
        ],
        "price_by_tier_v4": {
            tier: {
                "n": int(stats.loc[tier, "count"]),
                "median": float(stats.loc[tier, "median"]),
                "mean": float(stats.loc[tier, "mean"]),
            }
            for tier in stats.index
        },
        "note": "본 모델 inference 미수행 — feature engineering (ho, artist profile, etc.) 재현 별도 PR 권장. 본 결과는 alias QA + tier 분포 검증.",
    }
    out_path = OUT_DIR / "holdout_292_v4_qa.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
