"""추정가-독립 23개 피처 빌더.

기존 파서 + artist_stats_snapshot + hedonic_stats를 통합하여
추정가 없이도 동작하는 피처셋을 생성한다.

Phase 3 추정가 생성 엔진 전용.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from visionai.price_engine.features.artist_stats_snapshot import (
    compute_artist_stats_snapshot,
)
from visionai.price_engine.features.hedonic_stats import (
    compute_artist_auctions_since_last,
    compute_artist_career_length,
    compute_artist_last_hammer,
    compute_artist_lot_count_trend,
    compute_artist_median_price,
    compute_artist_premium_ratio,
    compute_artist_price_momentum,
    compute_artist_price_trend,
    compute_artist_price_volatility,
    compute_artist_reappear_flag,
    compute_artist_recent_avg_price,
    compute_artist_sale_frequency,
    compute_artist_unsold_rate,
    compute_auction_type_factor,
    compute_comparable_sales,
    compute_market_price_index,
    compute_medium_avg_price,
    compute_medium_x_auction_avg,
    compute_size_ho,
    compute_size_ho_above40,
)
from visionai.price_engine.features.splits import assign_split_4way
from visionai.price_engine.preprocessing.dimension_parser import parse_dimension
from visionai.price_engine.preprocessing.medium_parser import parse_medium
from visionai.price_engine.preprocessing.year_parser import parse_year

logger = logging.getLogger(__name__)

# Hedonic 피처 목록 (Phase 3: 23개 + Phase 4: 16개 + Phase 4b: 3개 = 42개)
# 추정가 4개(estimate_mid/range/ratio/ln_estimate_mid) 제거.
HEDONIC_FEATURES: list[str] = [
    # 범주형 (5) — 기획서 유지 피처
    "artist_clean",
    "medium_category",
    "support_category",
    "is_3d",
    "is_untitled",
    # 기존 작가 통계 (4) — 기획서 유지 피처
    "artist_avg_price",
    "artist_max_price",
    "artist_total_sold",
    "is_new_artist",
    # 물리적 속성 (5) — 기획서 유지 피처
    "height_cm",
    "width_cm",
    "surface_area",
    "aspect_ratio",
    "is_size_imputed",
    # 시간 (1) — 기획서 유지 피처
    "회차",
    # 신규 Hedonic 피처 (8) — Phase 3
    "artist_median_price",
    "artist_price_trend",
    "medium_avg_price",
    "size_ho",
    "size_ho_above40",
    "auction_type_factor",
    "artist_unsold_rate",
    "medium_x_auction_avg",
    # Phase 4 고도화 피처 (15)
    "artist_recent_avg_price",
    "artist_price_momentum",
    "artist_sale_frequency",
    "artist_auctions_since_last",
    "artist_price_volatility",
    "artist_lot_count_trend",
    "artist_premium_ratio",
    "artist_reappear_flag",
    "artist_last_hammer_price",
    "artist_career_length",
    "market_price_index",
    "comp_artist_avg",
    "comp_medium_avg",
    "comp_weighted",
    "comp_match_level",
    "comp_match_count",
    # Phase 4b: 외부 데이터 (Artsy 글로벌 경매 통계)
    "global_avg_price",
    "global_median_price",
    "global_auction_count",
]

CAT_FEATURE_NAMES: list[str] = [
    "artist_clean",
    "medium_category",
    "support_category",
    "타입",
    "is_3d",
    "is_untitled",
]


def _apply_parsers(df: pd.DataFrame) -> pd.DataFrame:
    """파서 3종을 적용하여 파생 컬럼을 추가한다 (dataset_builder.py와 동일 로직)."""
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


def _join_artist_stats_and_hedonic(
    df: pd.DataFrame,
    works_full: pd.DataFrame,
) -> pd.DataFrame:
    """각 행에 기존 작가 통계 + 신규 8개 Hedonic 피처를 조인한다.

    기존 dataset_builder._join_artist_stats 패턴과 동일한 strict cutoff 적용.
    """
    out = df.copy()
    out["artist_total_sold"] = 0
    out["artist_avg_price"] = 0.0
    out["artist_max_price"] = 0.0
    out["is_new_artist"] = False
    # Phase 3 신규 피처 초기화
    out["artist_median_price"] = np.nan
    out["artist_price_trend"] = np.nan
    out["medium_avg_price"] = np.nan
    out["auction_type_factor"] = np.nan
    out["artist_unsold_rate"] = np.nan
    out["medium_x_auction_avg"] = np.nan
    # Phase 4 신규 피처 초기화
    out["artist_recent_avg_price"] = np.nan
    out["artist_price_momentum"] = np.nan
    out["artist_sale_frequency"] = np.nan
    out["artist_auctions_since_last"] = np.nan
    out["artist_price_volatility"] = np.nan
    out["artist_lot_count_trend"] = np.nan
    out["artist_premium_ratio"] = np.nan
    out["artist_reappear_flag"] = False
    out["artist_last_hammer_price"] = np.nan
    out["artist_career_length"] = np.nan
    out["market_price_index"] = 0.0
    out["comp_artist_avg"] = np.nan
    out["comp_medium_avg"] = np.nan
    out["comp_weighted"] = np.nan
    out["comp_match_level"] = 4.0
    out["comp_match_count"] = 0.0
    # Phase 4b: 외부 데이터
    out["global_avg_price"] = np.nan
    out["global_median_price"] = np.nan
    out["global_auction_count"] = 0.0

    # 글로벌 통계 로드
    from visionai.price_engine.features.hedonic_stats import load_global_artist_stats

    global_stats = load_global_artist_stats()
    if global_stats is not None:
        for col_src, col_dst in [
            ("global_avg_price_krw", "global_avg_price"),
            ("global_median_price_krw", "global_median_price"),
            ("global_auction_count", "global_auction_count"),
        ]:
            if col_src in global_stats.columns:
                mapped = out["artist_clean"].map(
                    global_stats[col_src]
                    if col_src in global_stats.columns
                    else pd.Series(dtype="float64")
                )
                out[col_dst] = mapped.values

    for atype in out["타입"].unique():
        type_mask = out["타입"] == atype
        type_works = works_full[works_full["타입"] == atype]
        sessions = sorted(out.loc[type_mask, "회차"].unique())

        for session in sessions:
            row_mask = type_mask & (out["회차"] == session)
            artists_in_session = out.loc[row_mask, "artist_clean"]

            # --- 기존 작가 통계 (Phase 1-2 재사용) ---
            snapshot = compute_artist_stats_snapshot(
                type_works,
                cutoff_session=session,
                auction_type=atype,
                artist_col="artist_clean",
            )

            for col in ["artist_total_sold", "artist_avg_price", "artist_max_price"]:
                if col in snapshot.columns:
                    mapped = artists_in_session.map(snapshot[col])
                    out.loc[row_mask, col] = mapped.fillna(0).values

            known = set(snapshot.index) if not snapshot.empty else set()
            is_new = ~artists_in_session.isin(known)
            out.loc[row_mask, "is_new_artist"] = is_new.values

            # --- 신규 Hedonic 피처 (auction_type 필터 적용) ---
            # artist_median_price
            median_prices = compute_artist_median_price(
                works_full, cutoff=session, auction_type=atype
            )
            if not median_prices.empty:
                mapped = artists_in_session.map(median_prices)
                out.loc[row_mask, "artist_median_price"] = mapped.values

            # artist_price_trend
            trends = compute_artist_price_trend(
                works_full, cutoff=session, auction_type=atype
            )
            if not trends.empty:
                mapped = artists_in_session.map(trends)
                out.loc[row_mask, "artist_price_trend"] = mapped.values

            # medium_avg_price
            med_prices = compute_medium_avg_price(
                works_full, cutoff=session, auction_type=atype
            )
            if not med_prices.empty:
                mediums_in_session = out.loc[row_mask, "medium_category"]
                mapped = mediums_in_session.map(med_prices)
                out.loc[row_mask, "medium_avg_price"] = mapped.values

            # auction_type_factor
            atf = compute_auction_type_factor(
                works_full, cutoff=session, auction_type=atype
            )
            if atype in atf.index:
                out.loc[row_mask, "auction_type_factor"] = atf[atype]

            # artist_unsold_rate
            unsold = compute_artist_unsold_rate(
                works_full, cutoff=session, auction_type=atype
            )
            if not unsold.empty:
                mapped = artists_in_session.map(unsold)
                out.loc[row_mask, "artist_unsold_rate"] = mapped.values

            # medium_x_auction_avg
            mxa = compute_medium_x_auction_avg(
                works_full, cutoff=session, auction_type=atype
            )
            if not mxa.empty:
                mediums_in_session = out.loc[row_mask, "medium_category"]
                for idx in out.index[row_mask]:
                    med = out.loc[idx, "medium_category"]
                    key = (med, atype)
                    if key in mxa.index:
                        out.loc[idx, "medium_x_auction_avg"] = mxa.loc[
                            key, "medium_x_auction_avg"
                        ]

            # --- Phase 4 고도화 피처 (auction_type 필터 적용) ---
            _p4_artist_funcs = [
                ("artist_recent_avg_price", compute_artist_recent_avg_price),
                ("artist_price_momentum", compute_artist_price_momentum),
                ("artist_sale_frequency", compute_artist_sale_frequency),
                ("artist_auctions_since_last", compute_artist_auctions_since_last),
                ("artist_price_volatility", compute_artist_price_volatility),
                ("artist_lot_count_trend", compute_artist_lot_count_trend),
                ("artist_last_hammer_price", compute_artist_last_hammer),
                ("artist_career_length", compute_artist_career_length),
            ]
            for col_name, func in _p4_artist_funcs:
                vals = func(works_full, cutoff=session, auction_type=atype)
                if not vals.empty:
                    mapped = artists_in_session.map(vals)
                    out.loc[row_mask, col_name] = mapped.values

            # artist_premium_ratio (전체 타입에서 계산)
            prem = compute_artist_premium_ratio(works_full, cutoff=session)
            if not prem.empty:
                mapped = artists_in_session.map(prem)
                out.loc[row_mask, "artist_premium_ratio"] = mapped.values

            # artist_reappear_flag
            reappear = compute_artist_reappear_flag(
                works_full, cutoff=session, auction_type=atype
            )
            if not reappear.empty:
                mapped = artists_in_session.map(reappear)
                out.loc[row_mask, "artist_reappear_flag"] = mapped.fillna(False).values

            # market_price_index
            mpi = compute_market_price_index(
                works_full, cutoff=session, auction_type=atype
            )
            out.loc[row_mask, "market_price_index"] = mpi

            # comparable sales (행별 계산)
            for idx in out.index[row_mask]:
                artist = out.loc[idx, "artist_clean"]
                medium = out.loc[idx, "medium_category"]
                area = out.loc[idx, "surface_area"] if "surface_area" in out.columns else 0
                comp = compute_comparable_sales(
                    works_full, cutoff=session,
                    target_artist=artist, target_medium=medium,
                    target_surface_area=float(area) if pd.notna(area) else 0.0,
                    auction_type=atype,
                )
                out.loc[idx, "comp_artist_avg"] = comp["comp_artist_avg"]
                out.loc[idx, "comp_medium_avg"] = comp["comp_medium_avg"]
                out.loc[idx, "comp_weighted"] = comp["comp_weighted"]
                out.loc[idx, "comp_match_level"] = comp["comp_match_level"]
                out.loc[idx, "comp_match_count"] = comp["comp_match_count"]

    return out


def build_hedonic_features(
    works_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """CSV로부터 추정가-독립 38개 피처 DataFrame을 생성한다 (Phase 3: 23개 + Phase 4: 15개).

    Args:
        works_path: k-auction-works CSV 경로.
        output_path: parquet 저장 경로 (None이면 저장하지 않음).

    Returns:
        23개 Hedonic 피처 + split 라벨 + 타깃 컬럼이 포함된 DataFrame.
    """
    logger.info("Loading works CSV: %s", works_path)
    works = pd.read_csv(works_path, encoding="utf-8-sig")
    logger.info("Loaded %d rows", len(works))

    # 파서 적용
    df = _apply_parsers(works)

    # 호수 피처 (시간 독립)
    df["size_ho"] = compute_size_ho(df["surface_area"].fillna(0))
    df["size_ho_above40"] = compute_size_ho_above40(df["size_ho"])

    # 4-way split 라벨
    df["split"] = assign_split_4way(df)

    # 작가 통계 + Hedonic 피처 조인
    df = _join_artist_stats_and_hedonic(df, works_full=df)

    # 타깃: ln(낙찰가)
    price = pd.to_numeric(df["낙찰가"], errors="coerce")
    df["ln_price"] = np.log(price.where(price > 0))

    # 추정가 타깃 (Model-B용): ln(추정가 중앙)
    est_low = pd.to_numeric(df["추정가(최저)"], errors="coerce")
    est_high = pd.to_numeric(df["추정가(최고)"], errors="coerce")
    est_mid = (est_low + est_high) / 2
    df["ln_estimate_mid_target"] = np.log(est_mid.where(est_mid > 0))

    # 피처 검증
    missing = [f for f in HEDONIC_FEATURES if f not in df.columns]
    if missing:
        logger.warning("Missing hedonic features: %s", missing)

    logger.info(
        "Built %d hedonic features for %d rows, split distribution: %s",
        len(HEDONIC_FEATURES),
        len(df),
        df["split"].value_counts().to_dict(),
    )

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info("Saved to %s", output_path)

    return df
