#!/usr/bin/env python3
"""PP-H11D Phase 2/3: URL dedup이 모델 입력 검색 피처를 얼마나 흔드는지 측정.

build_snapshot의 집계 산식을 그대로 재현하되, 카운팅 직전에 작가+URL 중복을
1건으로 줄이는 dedup 유무를 비교한다. standardized_latest(캐시)에서 순수
재계산하므로 검색 API 호출이 없다. 동결 Cold 모델 입력으로 들어가는 피처
(개수·로그·비율·품질점수·등급)의 변화량을 정량화해 가격 영향 상한을 가늠한다.
"""

from __future__ import annotations

import json
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
ART_DIR = Path(__file__).resolve().parents[1] / "artifacts"

CTX = {
    "art": "is_art_context",
    "exhibition": "is_exhibition_context",
    "gallery": "is_gallery_context",
    "market": "is_market_context",
}


def as_bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(["true", "1", "1.0"])


def ratio(n: float, d: float) -> float:
    return float(n / d) if d > 0 else 0.0


def build_snapshot(df: pd.DataFrame, url_dedup: bool) -> pd.DataFrame:
    """run_pp_h11.build_snapshot 핵심 산식 재현 (+선택적 URL dedup)."""
    rows = []
    for artist, group in df.groupby("artist_search_name", dropna=False):
        rg = group[group["has_result"]].copy()
        if url_dedup:
            # 작가 내 동일 URL 1건 처리 (빈 URL은 보존)
            has_url = rg["url"].astype(str).str.len() > 0
            rg = pd.concat(
                [
                    rg[has_url].drop_duplicates(subset=["url"], keep="first"),
                    rg[~has_url],
                ],
                ignore_index=True,
            )
        total = float(len(rg))
        art = float(rg["is_art_context"].sum())
        exh = float(rg["is_exhibition_context"].sum())
        gal = float(rg["is_gallery_context"].sum())
        mkt = float(rg["is_market_context"].sum())
        hom = float(rg["is_homonym_context"].sum())
        trusted = float(rg["is_trusted_domain"].sum())
        recent = float(rg["is_recent_context"].sum())
        name_match = float(rg["artist_name_in_result"].sum())
        uniq_dom = float(rg["domain"].replace("", np.nan).dropna().nunique())
        # provider coverage (작가 group 전체 기준, dedup 무관)
        prov_succ = group.groupby("provider")["has_result"].max()
        prov_cov = ratio(float(prov_succ.sum()), max(float(len(prov_succ)), 1.0))

        art_match_ratio = ratio(art, total)
        exhibition_ratio = ratio(exh, total)
        market_ratio = ratio(mkt, total)
        trusted_ratio = ratio(trusted, total)
        recent_ratio = ratio(recent, total)
        homonym_ratio = ratio(hom, total)
        name_match_ratio = ratio(name_match, total)
        score = float(
            np.clip(
                0.30 * art_match_ratio
                + 0.20 * trusted_ratio
                + 0.15 * exhibition_ratio
                + 0.15 * market_ratio
                + 0.10 * recent_ratio
                + 0.10 * prov_cov
                + 0.10 * name_match_ratio
                - 0.30 * homonym_ratio,
                0.0,
                1.0,
            )
        )
        rows.append(
            {
                "artist_search_name": artist,
                "search_result_count": total,
                "search_art_context_count": art,
                "search_exhibition_context_count": exh,
                "search_gallery_context_count": gal,
                "search_market_context_count": mkt,
                "search_source_count": uniq_dom,
                "search_art_match_ratio": art_match_ratio,
                "search_exhibition_ratio": exhibition_ratio,
                "search_quality_score": score,
                "search_result_count_log": float(np.log1p(total)),
                "search_art_context_count_log": float(np.log1p(art)),
                "search_exhibition_context_count_log": float(np.log1p(exh)),
            }
        )
    return pd.DataFrame(rows).set_index("artist_search_name")


def main() -> None:
    df = pd.read_csv(STD_PATH, low_memory=False)
    df = df[as_bool(df["has_result"])].copy()
    for c in [
        *list(CTX.values()),
        "is_homonym_context",
        "is_trusted_domain",
        "is_recent_context",
        "artist_name_in_result",
    ]:
        df[c] = as_bool(df[c])
    df["has_result"] = True
    df["url"] = df["url"].astype("string").fillna("")
    df["domain"] = df["domain"].astype("string").fillna("")

    base = build_snapshot(df, url_dedup=False)
    dedup = build_snapshot(df, url_dedup=True)

    # 모델 입력으로 들어가는 피처들의 변화량
    feats = [
        "search_quality_score",
        "search_exhibition_ratio",
        "search_art_match_ratio",
        "search_exhibition_context_count_log",
        "search_art_context_count_log",
        "search_result_count_log",
        "search_exhibition_context_count",
        "search_art_context_count",
    ]
    report: dict[str, object] = {
        "experiment_id": "PP-H11D",
        "phase": "2/3",
        "n_artists": len(base),
        "feature_shift": {},
    }
    for f in feats:
        delta = (dedup[f] - base[f]).astype(float)
        report["feature_shift"][f] = {
            "mean_abs_delta": round(float(delta.abs().mean()), 4),
            "median_abs_delta": round(float(delta.abs().median()), 4),
            "max_abs_delta": round(float(delta.abs().max()), 4),
            "n_changed": int((delta.abs() > 1e-9).sum()),
            "share_changed": round(float((delta.abs() > 1e-9).mean()), 4),
            "mean_signed_delta": round(float(delta.mean()), 4),
        }
    ART_DIR.mkdir(parents=True, exist_ok=True)
    (ART_DIR / "feature_shift_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    base.join(dedup, lsuffix="_base", rsuffix="_dedup").to_csv(
        ART_DIR / "feature_base_vs_dedup.csv"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
