"""Unit tests for saatchi_year_made_merger (v3.4-2 step 5).

분기 검증:
- load_enrichment_year_map: 마지막 entry / ok+year 만 / retry pattern
- merge_year_made: saatchi only update / artsy 보존
- add_has_year_made_flag: notna → 1, NaN → 0
- recompute_work_age: 2026 - year_made / NaN → 0
- recompute_vintage_freshness: career_stage_int 분기
- recompute_career_age: max(year_made - birth_year, 0) / 결측 → 0
- build_variant: V0 / V_year_only / V_full 의 각 컬럼 추가
- variant_added_features
- merge_summary: artsy 행 변화 X 검증
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from saatchi_year_made_merger import (  # noqa: E402
    add_has_year_made_flag,
    build_variant,
    load_enrichment_year_map,
    merge_summary,
    merge_year_made,
    recompute_career_age,
    recompute_vintage_freshness,
    recompute_work_age,
    variant_added_features,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "artwork_url": [
                "https://www.saatchiart.com/art/A/1/2/view",
                "https://www.saatchiart.com/art/B/1/3/view",
                "https://www.saatchiart.com/art/C/2/4/view",  # enrichment 없음
                "https://www.artsy.net/artwork/x",
                "https://www.artsy.net/artwork/y",
            ],
            "source": ["saatchi", "saatchi", "saatchi", "artsy", "artsy"],
            "year_made": [np.nan, np.nan, np.nan, 2018.0, np.nan],
            "artist_birth_year": [1980.0, np.nan, 1990.0, 1975.0, 2000.0],
            "career_stage_int": [4, 2, 3, 4, 1],
        }
    )


def _enrichment() -> dict[str, int]:
    return {
        "https://www.saatchiart.com/art/A/1/2/view": 2020,
        "https://www.saatchiart.com/art/B/1/3/view": 2015,
        # C 는 없음
    }


# ---- load_enrichment_year_map ----


def test_load_enrichment_year_map_filters_ok_with_year(tmp_path: Path):
    p = tmp_path / "raw.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"url": "u1", "fetch_status": "ok", "year_created": 2020}),
                json.dumps({"url": "u2", "fetch_status": "5xx", "year_created": None}),
                json.dumps({"url": "u3", "fetch_status": "ok", "year_created": None}),
            ]
        )
    )
    m = load_enrichment_year_map(p)
    assert m == {"u1": 2020}


def test_load_enrichment_year_map_keeps_ok_after_retry_fail(tmp_path: Path):
    """ok 결과 후 retry 가 5xx 여도 ok year 유지."""
    p = tmp_path / "raw.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"url": "u1", "fetch_status": "ok", "year_created": 2018}),
                json.dumps({"url": "u1", "fetch_status": "5xx", "year_created": None}),
            ]
        )
    )
    m = load_enrichment_year_map(p)
    assert m["u1"] == 2018


def test_load_enrichment_year_map_last_ok_wins(tmp_path: Path):
    """여러 ok entry 가 있을 때 마지막 ok wins (코덱스 P2 강화)."""
    p = tmp_path / "raw.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"url": "u1", "fetch_status": "ok", "year_created": 2010}),
                json.dumps({"url": "u1", "fetch_status": "ok", "year_created": 2020}),
            ]
        )
    )
    m = load_enrichment_year_map(p)
    assert m["u1"] == 2020


def test_load_enrichment_year_map_missing_file(tmp_path: Path):
    assert load_enrichment_year_map(tmp_path / "nope.jsonl") == {}


# ---- merge_year_made ----


def test_merge_year_made_updates_saatchi_only():
    df = _sample_df()
    out = merge_year_made(df, _enrichment(), only_saatchi=True)
    # saatchi A,B 채워짐, C 그대로 NaN
    assert out.loc[0, "year_made"] == 2020.0
    assert out.loc[1, "year_made"] == 2015.0
    assert pd.isna(out.loc[2, "year_made"])
    # artsy 보존
    assert out.loc[3, "year_made"] == 2018.0
    assert pd.isna(out.loc[4, "year_made"])


def test_merge_year_made_does_not_mutate_input():
    df = _sample_df()
    original = df.copy()
    _ = merge_year_made(df, _enrichment())
    pd.testing.assert_frame_equal(df, original)


# ---- add_has_year_made_flag ----


def test_has_year_made_flag():
    df = pd.DataFrame({"year_made": [2020.0, np.nan, 2010.0]})
    out = add_has_year_made_flag(df)
    assert out["has_year_made"].tolist() == [1, 0, 1]


# ---- recompute_work_age ----


def test_recompute_work_age_default_2026():
    df = pd.DataFrame({"year_made": [2020.0, np.nan, 2010.0]})
    out = recompute_work_age(df)
    assert out.loc[0, "work_age"] == 6.0
    assert out.loc[1, "work_age"] == 0.0
    assert out.loc[2, "work_age"] == 16.0


def test_recompute_work_age_custom_ref():
    df = pd.DataFrame({"year_made": [2020.0]})
    out = recompute_work_age(df, ref_year=2025)
    assert out.loc[0, "work_age"] == 5.0


# ---- recompute_vintage_freshness ----


def test_vintage_freshness_branch_by_career_stage():
    df = pd.DataFrame(
        {
            "year_made": [2020.0, 2020.0, 2020.0, np.nan],
            "career_stage_int": [4, 2, 3, 4],
        }
    )
    df = recompute_work_age(df)
    out = recompute_vintage_freshness(df)
    # csi >= 3 → vintage = work_age, freshness = 0
    assert out.loc[0, "vintage_premium"] == 6.0
    assert out.loc[0, "freshness_discount"] == 0.0
    # csi < 3 → freshness = work_age, vintage = 0
    assert out.loc[1, "vintage_premium"] == 0.0
    assert out.loc[1, "freshness_discount"] == 6.0
    # csi == 3 → vintage 분기
    assert out.loc[2, "vintage_premium"] == 6.0
    assert out.loc[2, "freshness_discount"] == 0.0
    # year_made NaN → work_age 0 → 둘 다 0
    assert out.loc[3, "vintage_premium"] == 0.0
    assert out.loc[3, "freshness_discount"] == 0.0


def test_vintage_freshness_handles_missing_career_stage_int():
    """career_stage_int 컬럼 없으면 0 으로 치환."""
    df = pd.DataFrame({"year_made": [2020.0, 2020.0]})
    df = recompute_work_age(df)
    out = recompute_vintage_freshness(df)
    # csi=0 < 3 → freshness 만
    assert out.loc[0, "vintage_premium"] == 0.0
    assert out.loc[0, "freshness_discount"] == 6.0


# ---- recompute_career_age ----


def test_career_age_basic():
    df = pd.DataFrame(
        {
            "year_made": [2020.0, np.nan, 2010.0, 2000.0],
            "artist_birth_year": [1980.0, 1990.0, np.nan, 2010.0],
        }
    )
    out = recompute_career_age(df)
    # 정상 case
    assert out.loc[0, "career_age"] == 40.0
    # year_made 결측 → 0
    assert out.loc[1, "career_age"] == 0.0
    # birth_year 결측 → 0
    assert out.loc[2, "career_age"] == 0.0
    # year_made < birth_year → max 0
    assert out.loc[3, "career_age"] == 0.0


# ---- build_variant ----


def test_build_variant_v0_unchanged():
    df = _sample_df()
    out = build_variant(df, _enrichment(), "V0")
    assert "has_year_made" not in out.columns
    # year_made saatchi A,B 그대로 NaN (V0 = enrichment 미적용)
    assert pd.isna(out.loc[0, "year_made"])


def test_build_variant_v_year_only_adds_three():
    df = _sample_df()
    out = build_variant(df, _enrichment(), "V_year_only")
    assert "year_made" in out.columns
    assert "has_year_made" in out.columns
    assert "work_age" in out.columns
    # V_full 컬럼 X
    assert "vintage_premium" not in out.columns
    assert "career_age" not in out.columns
    # saatchi A → year=2020, has=1, work_age=6
    assert out.loc[0, "year_made"] == 2020.0
    assert out.loc[0, "has_year_made"] == 1
    assert out.loc[0, "work_age"] == 6.0
    # saatchi C → 결측 그대로, has=0, work_age=0
    assert pd.isna(out.loc[2, "year_made"])
    assert out.loc[2, "has_year_made"] == 0
    assert out.loc[2, "work_age"] == 0.0


def test_build_variant_v_full_adds_six():
    df = _sample_df()
    out = build_variant(df, _enrichment(), "V_full")
    expected = {
        "year_made",
        "has_year_made",
        "work_age",
        "vintage_premium",
        "freshness_discount",
        "career_age",
    }
    assert expected.issubset(out.columns)
    # saatchi A: year=2020, csi=4, by=1980 → vintage=6, freshness=0, career_age=40
    assert out.loc[0, "vintage_premium"] == 6.0
    assert out.loc[0, "freshness_discount"] == 0.0
    assert out.loc[0, "career_age"] == 40.0


def test_build_variant_unknown_raises():
    df = _sample_df()
    try:
        build_variant(df, _enrichment(), "V_unknown")  # type: ignore[arg-type]
    except ValueError as e:
        assert "Unknown variant" in str(e)
    else:
        raise AssertionError("expected ValueError")


# ---- variant_added_features ----


def test_variant_added_features():
    assert variant_added_features("V0") == []
    assert variant_added_features("V_year_only") == ["year_made", "has_year_made", "work_age"]
    f_full = variant_added_features("V_full")
    assert "year_made" in f_full
    assert "vintage_premium" in f_full
    assert "career_age" in f_full
    assert len(f_full) == 6


# ---- merge_summary (artsy 보존 검증) ----


def test_merge_summary_artsy_invariants():
    """count + value invariant 둘 다 검증 (코덱스 P0 강화)."""
    df = _sample_df()
    s = merge_summary(df, _enrichment())
    assert s["n_saatchi"] == 3
    assert s["n_artsy"] == 2
    assert s["artsy_year_before"] == 1
    assert s["artsy_year_after"] == 1
    # 약한 invariant (count) + 강한 invariant (value)
    assert s["artsy_count_invariant"] is True
    assert s["artsy_value_invariant"] is True
    assert s["saatchi_year_before"] == 0
    assert s["saatchi_year_after"] == 2


def test_merge_summary_no_enrichment_no_change():
    df = _sample_df()
    s = merge_summary(df, {})
    assert s["saatchi_year_before"] == s["saatchi_year_after"]
    assert s["artsy_count_invariant"] is True
    assert s["artsy_value_invariant"] is True


def test_merge_summary_value_invariant_catches_artsy_pollution():
    """artsy 에 의도하지 않은 enrichment 가 들어가면 value_invariant False (코덱스 P0)."""
    df = _sample_df()
    # artsy URL 을 enrichment 에 잘못 넣음 (실제로는 only_saatchi=True 라 update X)
    bad_map = {**_enrichment(), "https://www.artsy.net/artwork/y": 2010}
    s = merge_summary(df, bad_map)
    # artsy 의 NaN 위치 (idx 4) 가 update 안되어야 → value_invariant True 그대로
    assert s["artsy_value_invariant"] is True
    # idx 3 의 2018 도 변하면 안됨
    assert s["artsy_year_after"] == 1
