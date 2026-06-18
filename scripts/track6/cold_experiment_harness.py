#!/usr/bin/env python3
"""Common guardrails for Track6 Cold experiments.

Strict Cold means the target artist is not resolved to a usable artist identity
for prediction.  The model may use operationally collectable artist metadata
and search-derived features, but it must not use artist identity itself as a
feature or as a post-prediction lookup key.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


FORBIDDEN_STRICT_COLD_FEATURES = {
    "artist_key",
    "artist_works_count_train",
    "artist_works_log",
}

FORBIDDEN_STRICT_COLD_TERMS = {
    "search_delta_lookup",
    "artist_delta",
    "lookup_only",
    "guard_plus_lookup",
}


@dataclass(frozen=True)
class ColdHarnessPolicy:
    name: str = "strict_unresolved_artist_cold"
    allow_artist_identity_feature: bool = False
    allow_artist_key_lookup_postprocess: bool = False
    allowed_artist_feature_prefixes: tuple[str, ...] = (
        "artist_meta_",
        "artist_exhibition_",
    )
    notes: tuple[str, ...] = field(default_factory=tuple)


STRICT_UNRESOLVED_ARTIST_COLD = ColdHarnessPolicy()


def assert_strict_cold_features(features: Iterable[str], *, context: str = "cold experiment") -> None:
    feature_set = {str(feature) for feature in features}
    forbidden = sorted(feature_set & FORBIDDEN_STRICT_COLD_FEATURES)
    if forbidden:
        raise ValueError(
            f"{context} violates strict Cold harness: forbidden artist identity/history "
            f"features present: {forbidden}"
        )


def assert_no_artist_lookup_postprocess(
    *,
    uses_artist_key_lookup: bool,
    context: str = "cold experiment",
) -> None:
    if uses_artist_key_lookup:
        raise ValueError(
            f"{context} violates strict Cold harness: artist_key based lookup "
            "postprocess is not allowed for unresolved-artist Cold."
        )


def strict_cold_run_summary(extra: dict | None = None) -> dict:
    payload = {
        "cold_harness_policy": STRICT_UNRESOLVED_ARTIST_COLD.name,
        "uses_artist_identity_feature": False,
        "uses_same_artist_price_history": False,
        "uses_artist_key_lookup_postprocess": False,
        "allowed_artist_information": [
            "non-price artist_meta_* fields",
            "internet/search-derived context features",
            "exhibition/gallery features if collected independently of same-artist prices",
        ],
        "forbidden_artist_information": sorted(FORBIDDEN_STRICT_COLD_FEATURES),
        "forbidden_postprocess": [
            "search_delta_lookup[artist_key]",
            "any frozen per-artist correction keyed by artist identity",
        ],
    }
    if extra:
        payload.update(extra)
    return payload


def non_strict_artist_lookup_warning() -> dict:
    return {
        "cold_harness_policy": "non_strict_artist_lookup_diagnostic",
        "strict_cold_compliant": False,
        "reason": (
            "This diagnostic uses artist_key based frozen lookup postprocess. "
            "It must not be reported as unresolved-artist Cold performance."
        ),
    }
