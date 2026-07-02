#!/usr/bin/env python3
"""PP-H11D Phase 1: 검색 문맥 카운트의 중복 부풀림 영향도 측정.

같은 전시/작품을 다룬 서로 다른 기사가 여러 건 노출되면 검색 문맥 카운트
(search_exhibition_context_count 등)가 부풀려진다. 현재 파이프라인은 완전
동일 결과(url+title)만 제거하고, 의미적(같은 전시) 중복은 구분하지 않는다.

이 스크립트는 per-result 표준화 데이터에서 작가별 문맥 카운트를 4가지 기준으로
재집계해 부풀림 규모를 정량화한다:
  - raw          : 현재 방식 (per-result 합)
  - url_unique   : 동일 URL 1건 처리
  - domain_unique: 동일 도메인(언론사) 1건 처리
  - title_cluster: 제목+스니펫 토큰 Jaccard 군집 = 추정 distinct 사건 수

검증/선택 데이터에 손대지 않는 순수 측정 단계(test 무관).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
STD_PATH = (
    REPO
    / "data"
    / "track6"
    / "external_search"
    / "operational"
    / "track6_artist_search_operational_standardized_latest.csv"
)
OUT_DIR = Path(__file__).resolve().parents[1]
ART_DIR = OUT_DIR / "artifacts"
REP_DIR = OUT_DIR / "reports"

CONTEXTS = {
    "art": "is_art_context",
    "exhibition": "is_exhibition_context",
    "gallery": "is_gallery_context",
    "market": "is_market_context",
}
JACCARD_THRESHOLD = 0.6
_TOKEN_RE = re.compile(r"[0-9a-z가-힣]+")
_STOPWORDS = {
    "전시",
    "개인전",
    "단체전",
    "작가",
    "미술",
    "갤러리",
    "전",
    "展",
    "exhibition",
    "solo",
    "group",
    "art",
    "gallery",
    "the",
    "of",
    "at",
    "in",
    "and",
}


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def tokens(text: str) -> set[str]:
    toks = {t for t in _TOKEN_RE.findall(str(text).lower()) if len(t) > 1 and t not in _STOPWORDS}
    return toks


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def cluster_count(texts: list[str]) -> int:
    """그리디 토큰-Jaccard 군집으로 추정 distinct 사건 수 반환."""
    token_sets = [tokens(t) for t in texts]
    clusters: list[set[str]] = []
    for ts in token_sets:
        placed = False
        for c in clusters:
            if jaccard(ts, c) >= JACCARD_THRESHOLD:
                c |= ts  # 군집 대표 토큰 확장
                placed = True
                break
        if not placed:
            clusters.append(set(ts))
    return len(clusters)


def main() -> None:
    df = pd.read_csv(STD_PATH, low_memory=False)
    df = df[as_bool(df["has_result"])].copy()
    for ctx_col in CONTEXTS.values():
        df[ctx_col] = as_bool(df[ctx_col])
    df["title"] = df["title"].astype("string").fillna("")
    df["snippet"] = df["snippet"].astype("string").fillna("")
    df["url"] = df["url"].astype("string").fillna("")
    df["domain"] = df["domain"].astype("string").fillna("")
    df["cluster_text"] = (df["title"] + " " + df["snippet"]).str.strip()

    rows = []
    for artist, g in df.groupby("artist_search_name", dropna=False):
        rec: dict[str, object] = {"artist_search_name": artist, "result_count": len(g)}
        for name, col in CONTEXTS.items():
            sub = g[g[col]]
            raw = len(sub)
            url_u = int(sub["url"].replace("", np.nan).dropna().nunique())
            dom_u = int(sub["domain"].replace("", np.nan).dropna().nunique())
            clus = cluster_count(sub["cluster_text"].tolist()) if raw else 0
            rec[f"{name}_raw"] = raw
            rec[f"{name}_url_unique"] = url_u
            rec[f"{name}_domain_unique"] = dom_u
            rec[f"{name}_title_cluster"] = clus
        rows.append(rec)
    per_artist = pd.DataFrame(rows)

    # 집계 요약
    summary: dict[str, object] = {
        "experiment_id": "PP-H11D",
        "phase": 1,
        "title": "검색 문맥 카운트 중복 부풀림 영향도 측정",
        "source": str(STD_PATH.relative_to(REPO)),
        "n_artists": len(per_artist),
        "n_result_rows": len(df),
        "jaccard_threshold": JACCARD_THRESHOLD,
        "contexts": {},
    }
    for name in CONTEXTS:
        raw = per_artist[f"{name}_raw"]
        for variant in ["url_unique", "domain_unique", "title_cluster"]:
            ded = per_artist[f"{name}_{variant}"]
            affected = int((raw > ded).sum())
            artists_with_ctx = int((raw > 0).sum())
            total_raw = int(raw.sum())
            total_ded = int(ded.sum())
            # 부풀림 배수: ctx 보유 작가 한정 raw/ded 평균
            mask = raw > 0
            ratio = float((raw[mask] / ded[mask].clip(lower=1)).mean()) if mask.any() else 0.0
            summary["contexts"].setdefault(name, {})[variant] = {
                "artists_with_context": artists_with_ctx,
                "artists_inflated": affected,
                "inflated_share_of_ctx_artists": round(affected / artists_with_ctx, 4)
                if artists_with_ctx
                else 0.0,
                "total_raw_count": total_raw,
                "total_dedup_count": total_ded,
                "removed_count": total_raw - total_ded,
                "removed_share": round((total_raw - total_ded) / total_raw, 4)
                if total_raw
                else 0.0,
                "mean_inflation_ratio": round(ratio, 4),
            }

    ART_DIR.mkdir(parents=True, exist_ok=True)
    REP_DIR.mkdir(parents=True, exist_ok=True)
    per_artist.to_csv(ART_DIR / "per_artist_context_counts.csv", index=False)
    (ART_DIR / "dedup_impact_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
