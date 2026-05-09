"""Tests for source-conditional router (PR2A).

Coverage:
- decide_route() stateless decision matrix
- Mode validation
- Cohort hash determinism
- SourceRouter class (without actual artifact load — unit only)
"""

from __future__ import annotations

import pytest

from visionai.price_engine.api.source_router import (
    ARTSY_VARIANT,
    SAATCHI_VARIANT,
    UNIFIED_VARIANT,
    RouteDecision,
    _cohort_hash,
    decide_route,
)


class TestDecideRouteOff:
    def test_off_mode_matched_artsy_returns_unified(self):
        d = decide_route(is_matched=True, match_profile_source="artsy", mode="off")
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_source == "unified"
        assert d.routing_reason == "router_off"

    def test_off_mode_matched_saatchi_returns_unified(self):
        d = decide_route(is_matched=True, match_profile_source="saatchi", mode="off")
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "router_off"

    def test_off_mode_unmatched_returns_unified(self):
        d = decide_route(is_matched=False, match_profile_source=None, mode="off")
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "router_off"


class TestDecideRouteShadow:
    def test_shadow_mode_serving_remains_unified(self):
        """Shadow mode = serving은 unified / shadow decision은 별도 logged."""
        d = decide_route(is_matched=True, match_profile_source="artsy", mode="shadow")
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_source == "unified"
        assert "shadow" in d.routing_reason


class TestDecideRouteOn:
    def test_on_mode_matched_artsy(self):
        d = decide_route(is_matched=True, match_profile_source="artsy", mode="on")
        assert d.variant == ARTSY_VARIANT
        assert d.routing_source == "artsy"
        assert d.routing_reason == "matched_artsy"

    def test_on_mode_matched_saatchi(self):
        d = decide_route(is_matched=True, match_profile_source="saatchi", mode="on")
        assert d.variant == SAATCHI_VARIANT
        assert d.routing_source == "saatchi"
        assert d.routing_reason == "matched_saatchi"

    def test_on_mode_unmatched_fallback(self):
        d = decide_route(is_matched=False, match_profile_source=None, mode="on")
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_source == "unified"
        assert d.routing_reason == "unmatched_fallback"

    def test_on_mode_unmatched_with_external_source_ignored(self):
        """Authority: match.profile.source 영역 / unmatched X."""
        # is_matched=False / external collector source X / caller None pass.
        d = decide_route(is_matched=False, match_profile_source=None, mode="on")
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "unmatched_fallback"

    def test_on_mode_matched_unknown_source_fallback(self):
        """matched + manual/web/NaN → unified fallback."""
        for src in ["manual", "web", "external", "unknown", None]:
            d = decide_route(is_matched=True, match_profile_source=src, mode="on")
            assert d.variant == UNIFIED_VARIANT, f"src={src} should fallback"
            assert d.routing_reason == "matched_unknown_source_fallback"


class TestDecideRouteCanary:
    def test_canary_zero_percent_returns_unified(self):
        d = decide_route(
            is_matched=True,
            match_profile_source="artsy",
            mode="canary",
            percent=0,
            cohort_key="anything",
        )
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "canary_zero_percent"

    def test_canary_no_cohort_key_returns_unified(self):
        d = decide_route(
            is_matched=True,
            match_profile_source="artsy",
            mode="canary",
            percent=50,
            cohort_key=None,
        )
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "canary_no_cohort_key"

    def test_canary_100_percent_routes_all_matched(self):
        d = decide_route(
            is_matched=True,
            match_profile_source="artsy",
            mode="canary",
            percent=100,
            cohort_key="any-artist",
        )
        assert d.variant == ARTSY_VARIANT
        assert d.cohort_in_canary is True

    def test_canary_50_percent_deterministic_split(self):
        """동일 cohort_key → 동일 decision (deterministic)."""
        d1 = decide_route(
            is_matched=True,
            match_profile_source="artsy",
            mode="canary",
            percent=50,
            cohort_key="artist-A",
        )
        d2 = decide_route(
            is_matched=True,
            match_profile_source="artsy",
            mode="canary",
            percent=50,
            cohort_key="artist-A",
        )
        assert d1 == d2

    def test_canary_unmatched_fallback_in_cohort(self):
        """Canary cohort 영역 의 의무 영역 의 의무 영역 의 의무 unmatched → fallback."""
        d = decide_route(
            is_matched=False,
            match_profile_source=None,
            mode="canary",
            percent=100,
            cohort_key="any",
        )
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "unmatched_fallback"
        assert d.cohort_in_canary is True

    def test_canary_skipped_cohort_returns_unified(self):
        """Cohort 영역 = unified / cohort_in_canary=False."""
        # Find a cohort_key that hashes >= 5 (low percent)
        # _cohort_hash deterministic / find cohort_key 영역 의 의무 영역 의 의무 hash >= 5
        skip_key = None
        for i in range(100):
            key = f"test-key-{i}"
            if _cohort_hash(key) >= 5:
                skip_key = key
                break
        assert skip_key is not None
        d = decide_route(
            is_matched=True,
            match_profile_source="artsy",
            mode="canary",
            percent=5,
            cohort_key=skip_key,
        )
        assert d.variant == UNIFIED_VARIANT
        assert d.routing_reason == "cohort_skipped"
        assert d.cohort_in_canary is False


class TestModeValidation:
    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid SOURCE_ROUTER_MODE"):
            decide_route(is_matched=True, match_profile_source="artsy", mode="invalid")

    def test_valid_modes(self):
        # Should not raise
        for mode in ["off", "shadow", "canary", "on"]:
            decide_route(is_matched=False, match_profile_source=None, mode=mode)


class TestCohortHash:
    def test_cohort_hash_deterministic(self):
        assert _cohort_hash("artist-A") == _cohort_hash("artist-A")
        assert _cohort_hash("artist-B") == _cohort_hash("artist-B")

    def test_cohort_hash_different_keys_likely_different(self):
        h_a = _cohort_hash("artist-A")
        h_b = _cohort_hash("artist-B")
        # Not strictly required, but sanity
        assert isinstance(h_a, int)
        assert isinstance(h_b, int)
        assert 0 <= h_a < 100
        assert 0 <= h_b < 100

    def test_cohort_hash_distribution_50_percent(self):
        """1000 random keys / 50% threshold = roughly 500 (sanity check)."""
        below_50 = sum(1 for i in range(1000) if _cohort_hash(f"key-{i}") < 50)
        # Loose bound: distribution should be roughly uniform
        assert 400 <= below_50 <= 600, f"Distribution skewed: {below_50}/1000"


class TestRouteDecisionFields:
    def test_route_decision_default_cohort_in_canary_false(self):
        d = RouteDecision(
            variant=UNIFIED_VARIANT,
            routing_source="unified",
            routing_reason="test",
        )
        assert d.cohort_in_canary is False

    def test_route_decision_immutable(self):
        from dataclasses import FrozenInstanceError

        d = RouteDecision(
            variant=UNIFIED_VARIANT,
            routing_source="unified",
            routing_reason="test",
        )
        with pytest.raises(FrozenInstanceError):
            d.routing_reason = "changed"  # type: ignore
