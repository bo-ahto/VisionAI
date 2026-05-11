"""Tests for canary_cohort utility (PR-WARM-B Stage 4)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from canary_cohort import (  # type: ignore  # noqa: E402
    STAGE_4_1_CANARY_10PCT,
    STAGE_4_2_CANARY_50PCT,
    STAGE_4_3_CANARY_100PCT,
    _hash_to_bucket,
    cohort_bucket,
    get_stage_4_cohort,
    is_canary,
    resolve_variant_for_request,
)

# ---- _hash_to_bucket determinism / range ----


def test_hash_to_bucket_deterministic():
    """동일 input → 동일 bucket (재현성)."""
    assert _hash_to_bucket("kim-hyun-su") == _hash_to_bucket("kim-hyun-su")


def test_hash_to_bucket_range():
    """Bucket 항상 [0, 9] (default n_buckets=10)."""
    for name in ["a", "b", "kim", "saatchi-artist", "unknown-12345"]:
        b = _hash_to_bucket(name)
        assert 0 <= b < 10


def test_hash_to_bucket_n_buckets_param():
    """n_buckets 변경 시 range 확장."""
    for name in ["a", "b", "kim"]:
        assert 0 <= _hash_to_bucket(name, n_buckets=100) < 100


def test_hash_to_bucket_empty_string():
    """빈 문자열 → bucket 0 (safe default)."""
    assert _hash_to_bucket("") == 0


def test_hash_to_bucket_distribution():
    """100 random strings → 모든 10 buckets 분포 (대략)."""
    import random
    random.seed(42)
    counts = [0] * 10
    for _ in range(1000):
        key = f"artist-{random.randint(1, 100000)}"
        counts[_hash_to_bucket(key)] += 1
    # 모든 bucket non-zero (1000 samples / 10 buckets ≈ 100 each)
    assert all(c > 0 for c in counts), f"bucket distribution skewed: {counts}"
    # Loose uniformity check
    assert min(counts) > 50, f"min bucket too small: {counts}"
    assert max(counts) < 200, f"max bucket too large: {counts}"


# ---- cohort_bucket primary/fallback logic ----


def test_cohort_bucket_artist_slug_primary():
    """artist_slug primary path (R1 amendment)."""
    b1 = cohort_bucket(artist_slug="kim-hyun-su", request_id="req-12345")
    b2 = cohort_bucket(artist_slug="kim-hyun-su", request_id="other-req-98765")
    assert b1 == b2  # same artist → same bucket regardless of request_id


def test_cohort_bucket_request_id_fallback():
    """artist_slug None → request_id fallback."""
    b = cohort_bucket(artist_slug=None, request_id="req-12345")
    assert 0 <= b < 10


def test_cohort_bucket_artist_slug_empty_fallback():
    """artist_slug 빈 문자열 → request_id fallback."""
    b1 = cohort_bucket(artist_slug="", request_id="req-12345")
    b2 = cohort_bucket(artist_slug=None, request_id="req-12345")
    assert b1 == b2


def test_cohort_bucket_neither_raises():
    """둘 다 None → ValueError."""
    with pytest.raises(ValueError):
        cohort_bucket(artist_slug=None, request_id=None)
    with pytest.raises(ValueError):
        cohort_bucket(artist_slug="", request_id="")


# ---- is_canary ----


def test_is_canary_in_set():
    assert is_canary(0, {0}) is True
    assert is_canary(0, {0, 1, 2}) is True
    assert is_canary(5, range(0, 5)) is False
    assert is_canary(3, range(0, 5)) is True


def test_is_canary_empty_set():
    """canary_buckets 빈 set → 모두 False."""
    assert is_canary(0, set()) is False
    assert is_canary(5, []) is False


# ---- Stage 4 constants ----


def test_stage_4_1_is_10pct():
    """STAGE_4_1_CANARY_10PCT = {0}."""
    assert frozenset({0}) == STAGE_4_1_CANARY_10PCT


def test_stage_4_2_is_50pct():
    """STAGE_4_2_CANARY_50PCT = {0,1,2,3,4}."""
    assert frozenset({0, 1, 2, 3, 4}) == STAGE_4_2_CANARY_50PCT


def test_stage_4_3_is_100pct():
    """STAGE_4_3_CANARY_100PCT = {0-9}."""
    assert frozenset(range(0, 10)) == STAGE_4_3_CANARY_100PCT


def test_get_stage_4_cohort_aliases():
    """다양한 stage 이름 입력 형식."""
    assert get_stage_4_cohort("4.1") == STAGE_4_1_CANARY_10PCT
    assert get_stage_4_cohort("4.2") == STAGE_4_2_CANARY_50PCT
    assert get_stage_4_cohort("4.3") == STAGE_4_3_CANARY_100PCT
    assert get_stage_4_cohort("10pct") == STAGE_4_1_CANARY_10PCT
    assert get_stage_4_cohort("50pct") == STAGE_4_2_CANARY_50PCT
    assert get_stage_4_cohort("100pct") == STAGE_4_3_CANARY_100PCT
    assert get_stage_4_cohort("10%") == STAGE_4_1_CANARY_10PCT


def test_get_stage_4_cohort_unknown_raises():
    with pytest.raises(ValueError, match="Unknown stage"):
        get_stage_4_cohort("9.9")
    with pytest.raises(ValueError, match="Unknown stage"):
        get_stage_4_cohort("random_string")


# ---- resolve_variant_for_request (high-level) ----


def test_resolve_variant_canary_stage_4_1():
    """Stage 4.1 (10%) — bucket 0만 canary."""
    # 임의 artist / 10 random samples / 약 10% canary 예상
    canary_count = 0
    for i in range(100):
        v, b, is_can = resolve_variant_for_request(
            artist_slug=f"artist-{i}", request_id=None, stage="4.1",
        )
        if is_can:
            assert v == "v3_filtered_tuned_b_warm"
            canary_count += 1
        else:
            assert v == "v3_filtered_tuned"
    # 100 samples x 10% ≈ 10 (range 5-20 acceptable)
    assert 5 <= canary_count <= 20, f"Stage 4.1 canary count out of range: {canary_count}"


def test_resolve_variant_canary_stage_4_2():
    """Stage 4.2 (50%) — buckets 0-4 canary."""
    canary_count = 0
    for i in range(100):
        _, _, is_can = resolve_variant_for_request(
            artist_slug=f"artist-{i}", request_id=None, stage="4.2",
        )
        if is_can:
            canary_count += 1
    # 100 x 50% ≈ 50 (range 35-65 acceptable)
    assert 35 <= canary_count <= 65, f"Stage 4.2 canary count out of range: {canary_count}"


def test_resolve_variant_canary_stage_4_3():
    """Stage 4.3 (100%) — 모든 cohort canary."""
    for i in range(20):
        v, _, is_can = resolve_variant_for_request(
            artist_slug=f"artist-{i}", request_id=None, stage="4.3",
        )
        assert is_can is True
        assert v == "v3_filtered_tuned_b_warm"


def test_resolve_variant_same_artist_consistent():
    """동일 artist는 stage 동안 일관된 variant 받음 (R1 P0 amendment / artist-level cohort)."""
    for stage in ["4.1", "4.2"]:
        v1, b1, is_can1 = resolve_variant_for_request(
            artist_slug="kim-hyun-su", request_id="req-1", stage=stage,
        )
        v2, b2, is_can2 = resolve_variant_for_request(
            artist_slug="kim-hyun-su", request_id="req-2", stage=stage,
        )
        assert v1 == v2
        assert b1 == b2
        assert is_can1 == is_can2


def test_resolve_variant_fallback_request_id():
    """artist_slug None → request_id fallback / 동일 request_id 동일 variant."""
    v1, b1, _ = resolve_variant_for_request(
        artist_slug=None, request_id="req-12345", stage="4.1",
    )
    v2, b2, _ = resolve_variant_for_request(
        artist_slug=None, request_id="req-12345", stage="4.1",
    )
    assert v1 == v2
    assert b1 == b2


def test_resolve_variant_custom_variants():
    """canary_variant / control_variant 인자로 customize 가능."""
    v, _, is_can = resolve_variant_for_request(
        artist_slug="kim-hyun-su", request_id=None, stage="4.3",
        canary_variant="custom_canary",
        control_variant="custom_control",
    )
    assert v == "custom_canary"  # Stage 4.3 = 100% canary
    assert is_can is True
