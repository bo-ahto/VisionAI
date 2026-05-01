"""v3.4-2 step 5 merge module: saatchi enrichment → 학습 df 통합.

코덱스 v3.4-2 step 5 권장 (b): merge module 단위 테스트 우선, OOF 학습은 그 다음.

기능:
- step 4 jsonl 의 url → year_created 매핑
- 학습 df 의 saatchi rows 만 update (artsy 는 그대로 보존)
- `has_year_made` flag 부여 (saatchi unresolved 또는 artsy NaN 도 일관 처리)
- `work_age`, `vintage_premium`, `freshness_discount`, `career_age` 재계산 헬퍼

Variant 정의:
- V0: enrichment 미적용 (현재 production baseline)
- V_year_only: year_made + has_year_made + work_age 추가
- V_full: V_year_only + vintage_premium + freshness_discount + career_age 추가

설계 원칙 (코덱스 P0 R4):
- work_age = 2026 - year_made (`prepare_primary_market_dataset.py:254` 정의 그대로)
- source-conditional 변경 금지 (학습 정의 통일)
- vintage_premium / freshness_discount 는 career_stage_int 와 결합
  (`prepare_primary_market_dataset.py:321-326` 참조)

Note: 단위 테스트 위주 — 실제 OOF 학습은 별도 스크립트 (v34_2_step5_year_made_ablation.py).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
ENRICHMENT_PATH = (
    ROOT / "model_test_results" / "v3_diagnostics" / "saatchi_step4_full_enrichment_raw.jsonl"
)

# 학습 데이터 정의 그대로 (prepare_primary_market_dataset.py:254)
WORK_AGE_REF_YEAR = 2026

VariantName = Literal["V0", "V_year_only", "V_full"]


def load_enrichment_year_map(path: Path = ENRICHMENT_PATH) -> dict[str, int]:
    """jsonl → {artwork_url: year_created} 매핑.

    같은 url 의 multiple entries (retry pass) 가 있으면 마지막 entry 사용.
    fetch_status='ok' + year_created 있는 경우만 포함.
    """
    if not path.exists():
        return {}
    by_url: dict[str, int] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        url = rec.get("url")
        if not url:
            continue
        year = rec.get("year_created")
        status = rec.get("fetch_status")
        if status == "ok" and year is not None:
            by_url[url] = int(year)
        elif url in by_url and status != "ok":
            # 이전 ok 결과 가 있는 url 의 retry 가 fail 이면 ok 결과 유지
            continue
    return by_url


def merge_year_made(
    df: pd.DataFrame,
    enrichment_map: dict[str, int],
    *,
    only_saatchi: bool = True,
) -> pd.DataFrame:
    """saatchi rows 의 year_made 를 enrichment 결과로 update.

    Args:
        df: 학습 데이터 (artwork_url, source, year_made 등 컬럼 보유)
        enrichment_map: {artwork_url: year_created}
        only_saatchi: True 면 saatchi rows 만 update (artsy 보존)

    Returns:
        df_new: year_made 가 enrichment 결과로 update 된 copy
    """
    df_new = df.copy()
    if "year_made" not in df_new.columns:
        df_new["year_made"] = np.nan
    saatchi_mask = df_new["source"].astype(str) == "saatchi"
    target_mask = saatchi_mask if only_saatchi else pd.Series(True, index=df_new.index)
    urls = df_new["artwork_url"].astype(str)
    enriched_year = urls.map(enrichment_map)
    # target_mask 안의 enriched 가능 행만 update
    update_mask = target_mask & enriched_year.notna()
    df_new.loc[update_mask, "year_made"] = enriched_year[update_mask].astype(float)
    logger.info(
        "year_made merge: %d rows updated (target n=%d)",
        int(update_mask.sum()),
        int(target_mask.sum()),
    )
    return df_new


def add_has_year_made_flag(df: pd.DataFrame) -> pd.DataFrame:
    """has_year_made 0/1 flag 부여 (year_made notnull → 1)."""
    df_new = df.copy()
    df_new["has_year_made"] = df_new["year_made"].notna().astype(int)
    return df_new


def recompute_work_age(df: pd.DataFrame, ref_year: int = WORK_AGE_REF_YEAR) -> pd.DataFrame:
    """work_age = ref_year - year_made (결측은 0).

    `prepare_primary_market_dataset.py:254` 와 일관 — 단 fillna(0) 추가
    (현재 학습 데이터는 NaN 으로 두지만 CB_FEATURES 에서 빠진 후 다시 추가 시 필요).
    """
    df_new = df.copy()
    df_new["work_age"] = df_new["year_made"].apply(lambda y: ref_year - y if pd.notna(y) else 0.0)
    return df_new


def recompute_vintage_freshness(df: pd.DataFrame) -> pd.DataFrame:
    """vintage_premium / freshness_discount 재계산 (career_stage_int 결합).

    `prepare_primary_market_dataset.py:321-326`:
    - vintage_premium = work_age if career_stage_int >= 3 else 0
    - freshness_discount = work_age if career_stage_int < 3 else 0

    career_stage_int 가 df 에 없으면 0 으로 치환.

    **Saatchi caveat (코덱스 P1 R4)**: `prepare_saatchi_dataset.py:381-393` 의 출력
    컬럼에 `career_stage_int` 가 없음 → saatchi rows 의 csi default=0 → vintage_premium
    항상 0, freshness_discount 만 활성. V_full 의 saatchi-side vintage signal 은
    설계상 "사실상 죽음". artsy rows 는 prepare_primary_market_dataset.py 에서 csi
    계산되어 정상 동작.
    """
    df_new = df.copy()
    csi = df_new.get("career_stage_int", pd.Series(0, index=df_new.index)).fillna(0)
    work_age = df_new["work_age"].fillna(0)
    df_new["vintage_premium"] = np.where(csi >= 3, work_age, 0.0)
    df_new["freshness_discount"] = np.where(csi < 3, work_age, 0.0)
    return df_new


def recompute_career_age(df: pd.DataFrame) -> pd.DataFrame:
    """career_age = max(year_made - artist_birth_year, 0).

    year_made + artist_birth_year 둘 다 있어야 의미. 결측은 0.
    """
    df_new = df.copy()
    by = df_new.get("artist_birth_year", pd.Series(np.nan, index=df_new.index))
    ym = df_new.get("year_made", pd.Series(np.nan, index=df_new.index))

    def _calc(row_ym: float, row_by: float) -> float:
        if pd.isna(row_ym) or pd.isna(row_by):
            return 0.0
        return max(row_ym - row_by, 0.0)

    df_new["career_age"] = [_calc(ym.iloc[i], by.iloc[i]) for i in range(len(df_new))]
    return df_new


def build_variant(
    df: pd.DataFrame,
    enrichment_map: dict[str, int],
    variant: VariantName,
) -> pd.DataFrame:
    """Variant 별 feature df 생성.

    V0: enrichment 미적용 (year_made 그대로)
    V_year_only: year_made update + has_year_made flag + work_age
    V_full: V_year_only + vintage_premium + freshness_discount + career_age
    """
    if variant == "V0":
        # baseline: enrichment 미적용. has_year_made 도 추가 X (CB_FEATURES 그대로)
        return df.copy()

    df_new = merge_year_made(df, enrichment_map, only_saatchi=True)
    df_new = add_has_year_made_flag(df_new)
    df_new = recompute_work_age(df_new)

    if variant == "V_year_only":
        return df_new

    if variant == "V_full":
        df_new = recompute_vintage_freshness(df_new)
        df_new = recompute_career_age(df_new)
        return df_new

    raise ValueError(f"Unknown variant: {variant}")


def variant_added_features(variant: VariantName) -> list[str]:
    """Variant 별 CB_FEATURES 에 추가할 컬럼."""
    if variant == "V0":
        return []
    if variant == "V_year_only":
        return ["year_made", "has_year_made", "work_age"]
    if variant == "V_full":
        return [
            "year_made",
            "has_year_made",
            "work_age",
            "vintage_premium",
            "freshness_discount",
            "career_age",
        ]
    raise ValueError(f"Unknown variant: {variant}")


def merge_summary(df: pd.DataFrame, enrichment_map: dict[str, int]) -> dict:
    """merge 진단 — fill rate / saatchi 한정 / artsy row-level invariant 검증.

    `artsy_value_invariant` (코덱스 P0 강화): artsy rows 의 year_made value 완전 보존
    검증. NaN 위치 + 값 모두 일치. 이전 count-only invariant (`artsy_count_invariant`)
    는 약한 검증 (값이 바뀌어도 count 같으면 True). 둘 다 노출.
    """
    saatchi_mask = df["source"].astype(str) == "saatchi"
    artsy_mask = df["source"].astype(str) == "artsy"
    n_saatchi = int(saatchi_mask.sum())
    n_artsy = int(artsy_mask.sum())

    if "year_made" in df.columns:
        n_saatchi_year_before = int((saatchi_mask & df["year_made"].notna()).sum())
        n_artsy_year_before = int((artsy_mask & df["year_made"].notna()).sum())
    else:
        n_saatchi_year_before = 0
        n_artsy_year_before = 0

    df_after = merge_year_made(df, enrichment_map, only_saatchi=True)
    n_saatchi_year_after = int((saatchi_mask & df_after["year_made"].notna()).sum())
    n_artsy_year_after = int((artsy_mask & df_after["year_made"].notna()).sum())

    # 강한 invariant: artsy rows year_made value 완전 보존
    if "year_made" in df.columns:
        artsy_before = df.loc[artsy_mask, "year_made"]
        artsy_after = df_after.loc[artsy_mask, "year_made"]
        notna_match = bool((artsy_before.notna() == artsy_after.notna()).all())
        # NaN 위치가 같다는 가정 하에 finite 값들만 정확히 비교
        finite_match = bool(
            np.allclose(
                artsy_before.dropna().to_numpy(),
                artsy_after.dropna().to_numpy(),
            )
            if artsy_before.notna().any()
            else True
        )
        artsy_value_unchanged = notna_match and finite_match
    else:
        # year_made 컬럼 자체 부재면 after 도 artsy NaN 이어야 함
        artsy_value_unchanged = bool(df_after.loc[artsy_mask, "year_made"].isna().all())

    return {
        "n_saatchi": n_saatchi,
        "n_artsy": n_artsy,
        "saatchi_year_before": n_saatchi_year_before,
        "saatchi_year_after": n_saatchi_year_after,
        "saatchi_fill_rate_before": n_saatchi_year_before / max(n_saatchi, 1),
        "saatchi_fill_rate_after": n_saatchi_year_after / max(n_saatchi, 1),
        "artsy_year_before": n_artsy_year_before,
        "artsy_year_after": n_artsy_year_after,
        "artsy_count_invariant": n_artsy_year_before == n_artsy_year_after,
        "artsy_value_invariant": artsy_value_unchanged,
        "enrichment_map_size": len(enrichment_map),
    }
