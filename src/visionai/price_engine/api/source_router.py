"""Source-conditional Router (PR2A / default OFF).

Server-side row-level dispatch:
- matched + match.profile.source == "artsy" → artsy bundle
- matched + match.profile.source == "saatchi" → saatchi bundle
- 그 외 (unmatched / unknown / NaN / manual / web) → unified fallback

Rollout flags (env vars):
- SOURCE_ROUTER_MODE: off / shadow / canary / on (default: off)
- SOURCE_ROUTER_PERCENT: 0-100 (default: 0 / canary cohort %)
- SOURCE_ROUTER_RULE_VERSION: rule pinning (default: v1)

prereg = docs/operational_pr2a_prereg_20260509.md
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .primary_predictor import PrimaryPredictor

logger = logging.getLogger(__name__)

RouteVariant = Literal[
    "v3_filtered_tuned", "source_conditional_v1_artsy", "source_conditional_v1_saatchi"
]

UNIFIED_VARIANT: RouteVariant = "v3_filtered_tuned"
ARTSY_VARIANT: RouteVariant = "source_conditional_v1_artsy"
SAATCHI_VARIANT: RouteVariant = "source_conditional_v1_saatchi"

VALID_MODES = frozenset({"off", "shadow", "canary", "on"})


@dataclass(frozen=True)
class RouteDecision:
    """Routing decision (1 row)."""

    variant: RouteVariant
    routing_source: str  # "artsy" / "saatchi" / "unified"
    routing_reason: str  # "matched_artsy" / "unmatched_fallback" / "router_off" / 등
    cohort_in_canary: bool = False


def _cohort_hash(key: str) -> int:
    """Deterministic 0-99 cohort assignment."""
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100


def decide_route(
    is_matched: bool,
    match_profile_source: str | None,
    mode: str,
    percent: int = 0,
    cohort_key: str | None = None,
) -> RouteDecision:
    """Stateless routing decision (env-independent / fully testable).

    Args:
        is_matched: artist match success
        match_profile_source: matched profile.source ("artsy" / "saatchi" / 등)
                              — `None` if unmatched / external_collector source
                              영역 의 의무 영역 의 의무 X (권위적 X)
        mode: SOURCE_ROUTER_MODE (off / shadow / canary / on)
        percent: SOURCE_ROUTER_PERCENT (0-100, canary 영역 의 의무 영역 의 의무)
        cohort_key: deterministic cohort assignment key (artist_slug / fingerprint)
    """
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid SOURCE_ROUTER_MODE={mode!r} / valid: {sorted(VALID_MODES)}")

    # OFF: 모든 row → unified
    if mode == "off":
        return RouteDecision(
            variant=UNIFIED_VARIANT,
            routing_source="unified",
            routing_reason="router_off",
        )

    # SHADOW: serving = unified / shadow decision은 별도 logged
    # 본 함수 영역 의 의무 영역 의 의무 = primary serving decision 영역 의 의무 영역 의 의무
    if mode == "shadow":
        return RouteDecision(
            variant=UNIFIED_VARIANT,
            routing_source="unified",
            routing_reason="shadow_mode_primary_unified",
        )

    # CANARY: cohort hash < percent 영역 의 의무 영역 의 의무 영역 의 의무 routed
    in_cohort = True
    if mode == "canary":
        if percent <= 0:
            return RouteDecision(
                variant=UNIFIED_VARIANT,
                routing_source="unified",
                routing_reason="canary_zero_percent",
            )
        if cohort_key is None:
            return RouteDecision(
                variant=UNIFIED_VARIANT,
                routing_source="unified",
                routing_reason="canary_no_cohort_key",
            )
        in_cohort = True if percent >= 100 else _cohort_hash(cohort_key) < percent
        if not in_cohort:
            return RouteDecision(
                variant=UNIFIED_VARIANT,
                routing_source="unified",
                routing_reason="cohort_skipped",
                cohort_in_canary=False,
            )

    # ON or in_cohort=True: actual source-conditional routing
    # Authority: matched + match.profile.source 만 권위 (unmatched X / external X)
    if not is_matched:
        return RouteDecision(
            variant=UNIFIED_VARIANT,
            routing_source="unified",
            routing_reason="unmatched_fallback",
            cohort_in_canary=in_cohort,
        )

    if match_profile_source == "artsy":
        return RouteDecision(
            variant=ARTSY_VARIANT,
            routing_source="artsy",
            routing_reason="matched_artsy",
            cohort_in_canary=in_cohort,
        )

    if match_profile_source == "saatchi":
        return RouteDecision(
            variant=SAATCHI_VARIANT,
            routing_source="saatchi",
            routing_reason="matched_saatchi",
            cohort_in_canary=in_cohort,
        )

    # matched but unknown source (manual / web / NaN / 등) → unified fallback
    return RouteDecision(
        variant=UNIFIED_VARIANT,
        routing_source="unified",
        routing_reason="matched_unknown_source_fallback",
        cohort_in_canary=in_cohort,
    )


def simulate_route_on(
    is_matched: bool,
    match_profile_source: str | None,
    cohort_key: str | None = None,
) -> RouteDecision:
    """Shadow simulation: mode='on' decide_route 호출 (canary 100%).

    PR2B-prereq.1: mode=shadow 영역 의 의무 영역 의 의무 영역 의 의무 primary serving =
    unified / shadow_routed_variant 영역 의 의무 영역 의 의무 영역 의 의무 영역 = mode=on
    routing decision (100% routed).
    """
    return decide_route(
        is_matched=is_matched,
        match_profile_source=match_profile_source,
        mode="on",
        cohort_key=cohort_key,
    )


class SourceRouter:
    """3 predictor eager-load + row-level dispatch (PR2A scope).

    Default OFF: only unified predictor loaded. mode != "off" 영역 의 의무 영역 의 의무
    영역 의 의무 = artsy + saatchi predictor 영역 의 의무 영역 의 의무 추가 load.
    """

    def __init__(self, model_dir: Path | None = None):
        self.unified: PrimaryPredictor = PrimaryPredictor()
        self.artsy: PrimaryPredictor | None = None
        self.saatchi: PrimaryPredictor | None = None
        self.mode: str = os.environ.get("SOURCE_ROUTER_MODE", "off")
        self.percent: int = int(os.environ.get("SOURCE_ROUTER_PERCENT", "0"))
        self.rule_version: str = os.environ.get("SOURCE_ROUTER_RULE_VERSION", "v1")

        if self.mode not in VALID_MODES:
            raise RuntimeError(
                f"Invalid SOURCE_ROUTER_MODE={self.mode!r} / valid: {sorted(VALID_MODES)}"
            )

        if model_dir is not None:
            self.load_models(model_dir)

    def load_models(self, model_dir: Path) -> None:
        """Eager load + fail-closed.

        OFF mode: unified만 load (memory + startup time 절약).
        활성 mode (shadow/canary/on): 3 predictor 모두 load / artsy/saatchi 누락 →
        RuntimeError fail-closed.
        """
        # Unified always (default + fallback)
        self.unified.load_models(model_dir, variant=UNIFIED_VARIANT)
        logger.info("SourceRouter: unified loaded (variant=%s)", UNIFIED_VARIANT)

        if self.mode == "off":
            logger.info("SourceRouter: mode=off / artsy+saatchi load 영역 의 의무 영역 의 의무")
            return

        # Active modes: artsy + saatchi 영역 의 의무 영역 의 의무 추가 load (fail-closed)
        self.artsy = PrimaryPredictor()
        self.artsy.load_models(model_dir, variant=ARTSY_VARIANT)
        logger.info("SourceRouter: artsy loaded (variant=%s)", ARTSY_VARIANT)

        self.saatchi = PrimaryPredictor()
        self.saatchi.load_models(model_dir, variant=SAATCHI_VARIANT)
        logger.info("SourceRouter: saatchi loaded (variant=%s)", SAATCHI_VARIANT)

    def dispatch(
        self,
        is_matched: bool,
        match_profile_source: str | None,
        cohort_key: str | None = None,
    ) -> tuple[PrimaryPredictor, RouteDecision]:
        """Row-level dispatch: returns (predictor, decision)."""
        decision = decide_route(
            is_matched=is_matched,
            match_profile_source=match_profile_source,
            mode=self.mode,
            percent=self.percent,
            cohort_key=cohort_key,
        )
        if decision.variant == UNIFIED_VARIANT:
            return self.unified, decision
        if decision.variant == ARTSY_VARIANT:
            if self.artsy is None:
                raise RuntimeError(
                    "Routed to artsy bundle but artsy predictor not loaded "
                    f"(mode={self.mode!r} / fail-closed)"
                )
            return self.artsy, decision
        if decision.variant == SAATCHI_VARIANT:
            if self.saatchi is None:
                raise RuntimeError(
                    "Routed to saatchi bundle but saatchi predictor not loaded "
                    f"(mode={self.mode!r} / fail-closed)"
                )
            return self.saatchi, decision
        # unreachable
        raise RuntimeError(f"Unknown route variant: {decision.variant}")

    def get_predictor_for_variant(self, variant: str) -> PrimaryPredictor | None:
        """Get predictor instance for a routed variant (PR2B-prereq.1 / shadow inference).

        Returns None if predictor not loaded (mode=off + active variant requested).
        """
        if variant == UNIFIED_VARIANT:
            return self.unified
        if variant == ARTSY_VARIANT:
            return self.artsy
        if variant == SAATCHI_VARIANT:
            return self.saatchi
        return None
