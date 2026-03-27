"""전체 피처 조립 파이프라인.

CSV 원본 → 파서 → 스냅샷 → Cold Start → 21개 피처 DataFrame → parquet.
기획서 참조: 3.1, 3.3
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from visionai.price_engine.features.artist_stats_snapshot import (
    compute_artist_stats_snapshot,
)
from visionai.price_engine.features.cold_start import (
    build_cold_start_fallback,
    compute_estimate_tier,
)
from visionai.price_engine.features.estimate_features import build_estimate_features
from visionai.price_engine.features.splits import assign_split
from visionai.price_engine.preprocessing.dimension_parser import (
    parse_dimension,
)
from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.preprocessing.year_parser import parse_year

logger = logging.getLogger(__name__)


def _apply_parsers(df: pd.DataFrame) -> pd.DataFrame:
    """파서 3종을 적용하여 파생 컬럼을 추가한다."""
    out = df.copy()

    # 크기 파싱
    dim_results = out["크기"].apply(parse_dimension)
    out["height_cm"] = dim_results.apply(lambda r: r.height_cm)
    out["width_cm"] = dim_results.apply(lambda r: r.width_cm)
    out["surface_area"] = dim_results.apply(lambda r: r.surface_area)
    out["aspect_ratio"] = dim_results.apply(lambda r: r.aspect_ratio)
    out["is_3d"] = dim_results.apply(lambda r: r.is_3d)
    out["is_size_imputed"] = dim_results.apply(lambda r: r.is_size_imputed)

    # 재료 파싱
    med_results = out["재료"].apply(parse_medium)
    out["medium_category"] = med_results.apply(lambda r: r.medium_category)
    out["support_category"] = med_results.apply(lambda r: r.support_category)

    # 제작연도 파싱
    year_results = out["제작연도"].apply(parse_year)
    out["year_created"] = year_results.apply(lambda r: r.year_created)
    out["is_year_missing"] = year_results.apply(lambda r: r.is_year_missing)

    # 제목 파생
    out["is_untitled"] = out["제목"].str.contains(
        r"무제|Untitled|untitled", na=False, regex=True
    )

    # 작가 정리
    out["artist_clean"] = out["작가"].fillna("__UNKNOWN__")
    out.loc[out["artist_clean"].str.strip() == "", "artist_clean"] = "__UNKNOWN__"
    out.loc[
        out["artist_clean"].str.contains("작자미상", na=False), "artist_clean"
    ] = "__UNKNOWN__"

    return out


def _join_artist_stats(
    df: pd.DataFrame, works_full: pd.DataFrame
) -> pd.DataFrame:
    """각 행에 대해 해당 회차 이전의 작가 통계를 조인한다.

    기획서 3.3 규칙 1: fold별이 아닌 행별 cutoff으로 엄격 적용.
    성능을 위해 auction_type별로 배치 처리한다.
    """
    out = df.copy()
    out["artist_total_sold"] = 0
    out["artist_avg_price"] = 0
    out["artist_max_price"] = 0
    out["is_new_artist"] = False

    for atype in out["타입"].unique():
        type_mask = out["타입"] == atype
        type_works = works_full[works_full["타입"] == atype]

        # 타입별 고유 회차 기준으로 스냅샷 캐시
        sessions = sorted(out.loc[type_mask, "회차"].unique())

        for session in sessions:
            snapshot = compute_artist_stats_snapshot(
                type_works,
                cutoff_session=session,
                auction_type=atype,
                artist_col="artist_clean",  # artist_clean 키 통일
            )

            row_mask = type_mask & (out["회차"] == session)
            artists_in_session = out.loc[row_mask, "artist_clean"]

            for col in ["artist_total_sold", "artist_avg_price", "artist_max_price"]:
                mapped = artists_in_session.map(
                    snapshot[col] if col in snapshot.columns else pd.Series(dtype=float)
                )
                out.loc[row_mask, col] = mapped.fillna(0).values

            # 스냅샷에 없는 작가 = new artist
            known = set(snapshot.index) if not snapshot.empty else set()
            is_new = ~artists_in_session.isin(known)
            out.loc[row_mask, "is_new_artist"] = is_new.values

            # Cold Start fallback: 신규 작가에 그룹 평균 대체
            new_idx = out.index[row_mask][is_new.values]
            if len(new_idx) > 0:
                fallback = build_cold_start_fallback(
                    works_full, cutoff_session=session
                )
                if not fallback.empty:
                    for idx in new_idx:
                        est_mid_val = out.loc[idx, "estimate_mid"] if "estimate_mid" in out.columns else 0
                        tier = compute_estimate_tier(pd.Series([est_mid_val])).iloc[0]
                        key = (tier, atype)
                        if key in fallback.index:
                            fb = fallback.loc[key]
                            out.loc[idx, "artist_avg_price"] = fb["fallback_avg_price"]
                            out.loc[idx, "artist_max_price"] = fb["fallback_max_price"]
                            out.loc[idx, "artist_total_sold"] = 0

    return out


def build_dataset(
    works_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """CSV로부터 21개 피처 DataFrame을 생성한다.

    Args:
        works_path: k-auction-works CSV 경로.
        output_path: parquet 저장 경로 (None이면 저장하지 않음).

    Returns:
        21개 피처 + split 라벨이 포함된 DataFrame.
    """
    logger.info("Loading works CSV: %s", works_path)
    works = pd.read_csv(works_path, encoding="utf-8-sig")
    logger.info("Loaded %d rows", len(works))

    # 파서 적용
    logger.info("Applying parsers...")
    df = _apply_parsers(works)

    # 추정가 파생 피처
    logger.info("Building estimate features...")
    df = build_estimate_features(df)

    # 시계열 분할
    logger.info("Assigning splits...")
    df["split"] = assign_split(df)

    # 작가 통계 (fold별 snapshot)
    logger.info("Computing artist stats snapshots (this may take a while)...")
    df = _join_artist_stats(df, works_full=df)

    # 타겟
    df["ln_price"] = np.where(
        df["낙찰가"] > 0, np.log(df["낙찰가"].astype(float)), np.nan
    )

    # 파싱 통계 보고
    total = len(df)
    dim_parsed = df["surface_area"].notna().sum()
    dim_rate = dim_parsed / total * 100
    logger.info("Dimension parsing rate: %.1f%% (%d/%d)", dim_rate, dim_parsed, total)

    year_parsed = (~df["is_year_missing"]).sum()
    year_rate = year_parsed / total * 100
    logger.info("Year parsing rate: %.1f%% (%d/%d)", year_rate, year_parsed, total)

    new_artist_count = df["is_new_artist"].sum()
    logger.info("New artist (cold start) count: %d (%.1f%%)", new_artist_count, new_artist_count / total * 100)

    # parquet 저장
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info("Saved to %s (%d rows)", output_path, len(df))

    return df
