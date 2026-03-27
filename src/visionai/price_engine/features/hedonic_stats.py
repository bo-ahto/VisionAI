"""Hedonic 피처 산출 — 추정가 없이 작품 가치를 설명하는 신규 피처.

Phase 3 추정가 생성 엔진용.
모든 시간 의존 피처는 strict < cutoff + auction_type 필터 규칙을 따른다.
학술 근거: Renneboog & Spaenjers (2013), Garay et al. (2022), Lee & Kim (2011).
"""
from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_SHRINKAGE_M = 10
_HO_UNIT_CM2 = 132.0
_HO_HINGE = 40.0


def _bayesian_shrinkage_ln(
    group_mean_ln: float,
    global_mean_ln: float,
    n: int,
    m: int = _SHRINKAGE_M,
) -> float:
    """Bayesian shrinkage on log-price scale."""
    return (n * group_mean_ln + m * global_mean_ln) / (n + m)


def _filter_by_cutoff_and_type(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    price_col: str = "낙찰가",
    require_sold: bool = True,
) -> pd.DataFrame:
    """strict < cutoff + auction_type 필터 공통 헬퍼."""
    mask = works[session_col] < cutoff
    if auction_type is not None:
        mask = mask & (works[type_col] == auction_type)
    if require_sold:
        mask = mask & (works[price_col] > 0)
    return works.loc[mask]


def compute_artist_median_price(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    artist_col: str = "artist_clean",
    price_col: str = "낙찰가",
) -> pd.Series:
    """strict < cutoff, auction_type별 작가 낙찰가 중앙값. 거래 < 3건: shrinkage."""
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type, session_col, type_col, price_col
    )
    if subset.empty:
        return pd.Series(dtype="float64", name="artist_median_price")

    global_median_ln = float(np.log(subset[price_col]).median())
    grouped = subset.groupby(artist_col)[price_col]
    medians = grouped.median()
    counts = grouped.count()

    result = pd.Series(dtype="float64", index=medians.index, name="artist_median_price")
    for artist in medians.index:
        n = int(counts[artist])
        if n >= 3:
            result[artist] = medians[artist]
        else:
            artist_ln = float(np.log(medians[artist]))
            result[artist] = np.exp(
                _bayesian_shrinkage_ln(artist_ln, global_median_ln, n)
            )
    return result


def compute_artist_price_trend(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    artist_col: str = "artist_clean",
    price_col: str = "낙찰가",
    recent_sessions: int = 5,
) -> pd.Series:
    """최근 N회차 vs 이전 평균 변화율. 거래 < 5건: NaN."""
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type, session_col, type_col, price_col
    )
    if subset.empty:
        return pd.Series(dtype="float64", name="artist_price_trend")

    recent_cutoff = cutoff - recent_sessions
    results: dict[str, float] = {}
    for artist, grp in subset.groupby(artist_col):
        if len(grp) < 5:
            results[artist] = np.nan
            continue
        recent = grp.loc[grp[session_col] >= recent_cutoff, price_col]
        earlier = grp.loc[grp[session_col] < recent_cutoff, price_col]
        if earlier.empty or recent.empty:
            results[artist] = np.nan
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            results[artist] = float(recent.mean() / earlier.mean() - 1.0)
    return pd.Series(results, name="artist_price_trend", dtype="float64")


def compute_medium_avg_price(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    medium_col: str = "medium_category",
    price_col: str = "낙찰가",
) -> pd.Series:
    """strict < cutoff, auction_type별 매체 평균 낙찰가. 그룹 < 30건: shrinkage.

    shrinkage는 log-price 스케일에서 수행: mean(log(price)), not log(mean(price)).
    """
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type, session_col, type_col, price_col
    )
    if subset.empty:
        return pd.Series(dtype="float64", name="medium_avg_price")

    global_mean_ln = float(np.log(subset[price_col]).mean())
    grouped = subset.groupby(medium_col)[price_col]
    means_ln = grouped.apply(lambda x: float(np.log(x).mean()))
    counts = grouped.count()

    result = pd.Series(dtype="float64", index=means_ln.index, name="medium_avg_price")
    for medium in means_ln.index:
        n = int(counts[medium])
        if n >= 30:
            result[medium] = np.exp(means_ln[medium])
        else:
            shrunk_ln = _bayesian_shrinkage_ln(means_ln[medium], global_mean_ln, n)
            result[medium] = np.exp(shrunk_ln)
    return result


def compute_size_ho(surface_area: pd.Series) -> pd.Series:
    """surface_area(cm2) -> 호수 변환. 시간 독립. 1호 = 132cm2."""
    return (surface_area / _HO_UNIT_CM2).rename("size_ho")


def compute_size_ho_above40(size_ho: pd.Series) -> pd.Series:
    """max(0, size_ho - 40): 40호 변곡점 hinge (Lee & Kim 2011)."""
    return (size_ho - _HO_HINGE).clip(lower=0.0).rename("size_ho_above40")


def compute_auction_type_factor(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    price_col: str = "낙찰가",
) -> pd.Series:
    """strict < cutoff 경매유형별 평균 낙찰가 비율.

    주의: 비율 계산은 반드시 **전체 auction_type**에서 수행해야 한다.
    auction_type으로 사전 필터링하면 1개 그룹만 남아 비율이 항상 1.0이 된다.
    따라서 auction_type 파라미터는 무시하고 전체 데이터(cutoff만 적용)를 사용한다.
    """
    # 전체 타입에서 비율 계산 (auction_type 필터 적용하지 않음)
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type=None, session_col=session_col,
        type_col=type_col, price_col=price_col,
    )
    if subset.empty:
        return pd.Series(dtype="float64", name="auction_type_factor")

    global_mean_ln = float(np.log(subset[price_col]).mean())
    grouped = subset.groupby(type_col)[price_col]
    means_ln = grouped.apply(lambda x: float(np.log(x).mean()))
    counts = grouped.count()

    result = pd.Series(dtype="float64", index=means_ln.index, name="auction_type_factor")
    for atype in means_ln.index:
        n = int(counts[atype])
        if n >= 30:
            result[atype] = np.exp(means_ln[atype]) / np.exp(global_mean_ln)
        else:
            shrunk_ln = _bayesian_shrinkage_ln(means_ln[atype], global_mean_ln, n)
            result[atype] = np.exp(shrunk_ln) / np.exp(global_mean_ln)
    return result


def compute_artist_unsold_rate(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    artist_col: str = "artist_clean",
    status_col: str = "상태",
) -> pd.Series:
    """strict < cutoff, auction_type별 작가 유찰률. 출품 < 3건: NaN."""
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type, session_col, type_col,
        price_col=status_col, require_sold=False,
    )
    if subset.empty:
        return pd.Series(dtype="float64", name="artist_unsold_rate")

    total = subset.groupby(artist_col)[status_col].count()
    unsold = (
        subset.loc[subset[status_col].str.contains("유찰", na=False)]
        .groupby(artist_col)[status_col]
        .count()
    )
    rate = (unsold / total).reindex(total.index, fill_value=0.0)
    rate = rate.where(total >= 3, np.nan)
    return rate.rename("artist_unsold_rate")


def compute_medium_x_auction_avg(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    medium_col: str = "medium_category",
    price_col: str = "낙찰가",
) -> pd.DataFrame:
    """strict < cutoff 매체x경매유형 교차그룹 평균 ln(낙찰가).

    Cold Start Tier 1 prior. 그룹 < 30건: medium 평균(Tier 2) 방향으로 shrinkage.
    """
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type, session_col, type_col, price_col
    )
    if subset.empty:
        return pd.DataFrame(columns=["medium_x_auction_avg"])

    # medium-level prior (Tier 2 방향 shrinkage)
    medium_means_ln = subset.groupby(medium_col)[price_col].apply(
        lambda x: float(np.log(x).mean())
    )
    global_mean_ln = float(np.log(subset[price_col]).mean())

    grouped = subset.groupby([medium_col, type_col])
    means_ln = grouped[price_col].apply(lambda x: float(np.log(x).mean()))
    counts = grouped[price_col].count()

    result = pd.Series(dtype="float64", index=means_ln.index, name="medium_x_auction_avg")
    for idx in means_ln.index:
        medium_cat = idx[0]
        n = int(counts[idx])
        # Tier 2 prior = medium-level mean (not global)
        tier2_prior = medium_means_ln.get(medium_cat, global_mean_ln)
        if n >= 30:
            result[idx] = means_ln[idx]
        else:
            result[idx] = _bayesian_shrinkage_ln(float(means_ln[idx]), tier2_prior, n)
    return result.to_frame()


def compute_group_unsold_rate(
    works: pd.DataFrame,
    cutoff: int,
    auction_type: str | None = None,
    session_col: str = "회차",
    type_col: str = "타입",
    medium_col: str = "medium_category",
    status_col: str = "상태",
) -> pd.DataFrame:
    """strict < cutoff 매체x경매유형 그룹별 유찰률.

    selection_bias.py + confidence_grade에서 사용 (모델 피처 아님, inference metadata).
    그룹 내 출품 < 10건이면 auction_type 전체 유찰률로 fallback.
    """
    subset = _filter_by_cutoff_and_type(
        works, cutoff, auction_type, session_col, type_col,
        price_col=status_col, require_sold=False,
    )
    if subset.empty:
        return pd.DataFrame(columns=["group_unsold_rate"])

    grouped = subset.groupby([medium_col, type_col])
    total = grouped[status_col].count()
    unsold = (
        subset.loc[subset[status_col].str.contains("유찰", na=False)]
        .groupby([medium_col, type_col])[status_col]
        .count()
    )
    rate = (unsold / total).reindex(total.index, fill_value=0.0)

    # 그룹 < 10건: auction_type 전체 유찰률로 fallback
    atype_total = subset.groupby(type_col)[status_col].count()
    atype_unsold = (
        subset.loc[subset[status_col].str.contains("유찰", na=False)]
        .groupby(type_col)[status_col]
        .count()
    )
    atype_rate = (atype_unsold / atype_total).reindex(atype_total.index, fill_value=0.0)

    for idx in rate.index:
        if total[idx] < 10:
            atype = idx[1]
            rate[idx] = atype_rate.get(atype, 0.0)

    return rate.rename("group_unsold_rate").to_frame()


def parse_edition(title: str) -> bool | None:
    """제목에서 에디션 regex 파싱: (d+)/(d+) 패턴."""
    if not title or not isinstance(title, str):
        return None
    return bool(re.search(r"\d+\s*/\s*\d+", title))


def compute_edition_adoption_rate(
    works: pd.DataFrame,
    medium_col: str = "medium_category",
    title_col: str = "제목",
    target_mediums: tuple[str, ...] = ("판화", "사진/디지털"),
) -> float:
    """판화/사진 카테고리에서 에디션 파싱 성공률 계산. >= 80%이면 채택."""
    target = works.loc[works[medium_col].isin(target_mediums)]
    if target.empty:
        return 0.0
    parsed = target[title_col].apply(parse_edition)
    success = parsed.notna() & (parsed != False)  # noqa: E712
    return float(success.sum() / len(target))
