"""v3.6 Phase 1 PR4: feature builder year 3종 + 옵션 B disable 단위 테스트.

검증:
- Backward compat (is_saatchi_warm 기본 False → year features 0/0/0)
- Activation matrix (is_saatchi_warm x year_made x range)
- 옵션 B disable: 비대상 모두 0.0/0/0.0 (NaN 없음)
- Boundary years (1800, 2030)
- 학습 정합 (post-prepare model-input parity)
"""

from __future__ import annotations

import math

from visionai.price_engine.api.primary_feature_builder import build_features

# ---- Backward compat (is_saatchi_warm / year_made 기본값) ----


def test_build_features_backward_compat_default_disabled():
    """v3.6 변경 후에도 기존 호출 (PR8/9 변경 전) → year features 0/0/0."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="acrylic on canvas",
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0


def test_build_features_backward_compat_with_artist_profile():
    """기존 artist_profile 호출 정상 동작 + year features default 0."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artist_profile={"birth_year": 1980, "source": "saatchi"},
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0
    # 기존 features 정상
    assert features["artist_birth_year"] == 1980.0
    assert features["source"] == "saatchi"


# ---- Activation: saatchi-warm + valid year ----


def test_saatchi_warm_with_valid_year_activates():
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=True,
        year_made=2020,
    )
    assert features["year_made"] == 2020.0
    assert features["has_year_made"] == 1
    assert features["work_age"] == 6.0  # 2026 - 2020


def test_saatchi_warm_year_2018():
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=True,
        year_made=2018,
    )
    assert features["year_made"] == 2018.0
    assert features["work_age"] == 8.0


# ---- Boundary years ----


def test_year_made_boundary_min_1800_activates():
    features = build_features(
        width_cm=100, height_cm=80, medium="oil", is_saatchi_warm=True, year_made=1800
    )
    assert features["year_made"] == 1800.0
    assert features["has_year_made"] == 1
    assert features["work_age"] == 226.0


def test_year_made_boundary_max_2030_activates():
    features = build_features(
        width_cm=100, height_cm=80, medium="oil", is_saatchi_warm=True, year_made=2030
    )
    assert features["year_made"] == 2030.0
    assert features["has_year_made"] == 1
    assert features["work_age"] == -4.0  # 2026 - 2030


def test_year_made_below_1800_disabled():
    """validate range 외 → 옵션 B disable (caller 가 미리 reject 못한 경우 방어)."""
    features = build_features(
        width_cm=100, height_cm=80, medium="oil", is_saatchi_warm=True, year_made=1799
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0


def test_year_made_above_2030_disabled():
    features = build_features(
        width_cm=100, height_cm=80, medium="oil", is_saatchi_warm=True, year_made=2031
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0


# ---- Cohort gating: 비-saatchi-warm → disabled (옵션 B) ----


def test_cold_artist_with_year_disabled():
    """saatchi cold (is_saatchi_warm=False) + valid year → 옵션 B disable."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=False,
        year_made=2020,
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0


def test_artsy_artist_with_year_disabled():
    """artsy artist (is_saatchi_warm=False) + valid year → disabled."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="acrylic",
        artist_profile={"source": "artsy"},
        is_saatchi_warm=False,
        year_made=2018,
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0


def test_unmatched_with_year_disabled():
    """unmatched (artist_profile 없음) → 자동 disable."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=False,
        year_made=2020,
    )
    assert features["year_made"] == 0.0


# ---- year_made None → disabled ----


def test_saatchi_warm_with_none_year_disabled():
    """saatchi warm 이지만 enrichment fail / no manual → year_made=None → disable."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=True,
        year_made=None,
    )
    assert features["year_made"] == 0.0
    assert features["has_year_made"] == 0
    assert features["work_age"] == 0.0


# ---- 옵션 B contract: 모든 output 이 finite 0 (NaN 없음) ----


def test_disabled_output_all_finite_zeros():
    """옵션 B 단일 contract: 모든 disabled output 이 finite (NaN X)."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=False,
    )
    assert isinstance(features["year_made"], float)
    assert isinstance(features["has_year_made"], int)
    assert isinstance(features["work_age"], float)
    assert not math.isnan(features["year_made"])
    assert not math.isnan(features["work_age"])


def test_activated_output_all_finite():
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        is_saatchi_warm=True,
        year_made=2020,
    )
    assert isinstance(features["year_made"], float)
    assert isinstance(features["work_age"], float)
    assert not math.isnan(features["year_made"])
    assert not math.isnan(features["work_age"])


# ---- 기존 features 보존 (regression test) ----


def test_existing_features_preserved_in_activated_path():
    """year features 추가 후에도 기존 32 features 정상 동작."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="acrylic on canvas",
        artist_profile={"birth_year": 1980, "source": "saatchi"},
        is_saatchi_warm=True,
        year_made=2020,
    )
    # 기존 핵심 features
    assert "ho" in features
    assert "ho_power" in features
    assert "support_type" in features
    assert "medium_category" in features
    assert "source" in features
    assert features["source"] == "saatchi"
    assert features["artist_birth_year"] == 1980.0


def test_total_features_count_35():
    """v3.5 step 2: 32 (기존) + 3 (year_made / has_year_made / work_age) = 35"""
    features = build_features(
        width_cm=100, height_cm=80, medium="oil", is_saatchi_warm=True, year_made=2020
    )
    assert len(features) == 35
    assert "year_made" in features
    assert "has_year_made" in features
    assert "work_age" in features


# ---- target_market / manual override 와 결합 ----


def test_year_features_independent_of_target_market():
    """target_market='online' 이어도 year activation rule 동일."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        target_market="online",
        is_saatchi_warm=True,
        year_made=2020,
    )
    assert features["year_made"] == 2020.0
    assert features["has_year_made"] == 1


def test_manual_override_does_not_affect_year_features():
    """manual_overrides 의 birth_year 등이 year_made 에 영향 X."""
    features = build_features(
        width_cm=100,
        height_cm=80,
        medium="oil",
        manual_overrides={"artist_birth_year": 1990, "artist_total_works": 50},
        is_saatchi_warm=True,
        year_made=2020,
    )
    assert features["year_made"] == 2020.0  # year_made 만 영향
    assert features["has_year_made"] == 1
    assert features["artist_birth_year"] == 1990.0  # manual override 적용
