"""PR-WARM-B Stage 4 canary cohort hash utility.

Runbook: docs/pr_warm_b_stage_3_5_activation_runbook_20260511.md (§2.1)

Usage:
    >>> from canary_cohort import cohort_bucket, is_canary
    >>> bucket = cohort_bucket(artist_slug="kim-hyun-su", request_id="req-12345")
    >>> is_canary(bucket, canary_buckets=range(0, 1))  # Stage 4.1 (10%)
    True/False

R1 amendment 정합 (codex P0 / Q4):
- Primary cohort key: artist_slug hash (artist 단위 일관 split)
- Fallback: request_id hash (artist 미매칭 시)
- mod 10 → bucket 0-9
- Stage 4.1: bucket {0} → canary (10%)
- Stage 4.2: bucket {0,1,2,3,4} → canary (50%)
- Stage 4.3: bucket {0-9} → canary (100%)
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def _hash_to_bucket(key: str, n_buckets: int = 10) -> int:
    """Stable hash → bucket index (0 to n_buckets-1).

    Uses SHA256 for stable distribution / no salt (deterministic / re-runable).
    """
    if not key:
        return 0
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    # First 4 bytes as unsigned int → mod n_buckets
    bucket = int.from_bytes(digest[:4], "big") % n_buckets
    return bucket


def cohort_bucket(
    artist_slug: str | None = None,
    request_id: str | None = None,
    n_buckets: int = 10,
) -> int:
    """Determine canary cohort bucket for a request.

    R1 amendment: primary = artist_slug hash / fallback = request_id hash.

    Args:
        artist_slug: matched artist slug (None if artist 미매칭)
        request_id: request id (fallback / uuid 또는 similar)
        n_buckets: total cohort bucket count (default 10 / mod 10)

    Returns:
        bucket index in [0, n_buckets-1]

    Raises:
        ValueError: 둘 다 None / 둘 다 빈 문자열

    Examples:
        >>> cohort_bucket(artist_slug="kim-hyun-su")
        # Stable bucket / 동일 artist 동일 cohort
        >>> cohort_bucket(request_id="req-12345")
        # artist 미매칭 / request fallback
    """
    if artist_slug:
        return _hash_to_bucket(artist_slug, n_buckets)
    if request_id:
        return _hash_to_bucket(request_id, n_buckets)
    raise ValueError("Either artist_slug or request_id must be provided")


def is_canary(bucket: int, canary_buckets: Iterable[int]) -> bool:
    """Check if bucket is in canary set.

    Args:
        bucket: cohort_bucket() result
        canary_buckets: iterable of canary bucket indices (e.g. {0} for 10%)

    Returns:
        True if bucket in canary_buckets

    Examples:
        >>> # Stage 4.1 (10%): only bucket 0
        >>> is_canary(0, {0})
        True
        >>> is_canary(5, {0})
        False

        >>> # Stage 4.2 (50%): buckets 0-4
        >>> is_canary(3, range(0, 5))
        True

        >>> # Stage 4.3 (100%): all buckets
        >>> is_canary(7, range(0, 10))
        True
    """
    return bucket in set(canary_buckets)


# Stage 4 standard cohort sets (R1 amendment 정합)
STAGE_4_1_CANARY_10PCT = frozenset({0})  # 10% — bucket 0
STAGE_4_2_CANARY_50PCT = frozenset({0, 1, 2, 3, 4})  # 50% — buckets 0-4
STAGE_4_3_CANARY_100PCT = frozenset(range(0, 10))  # 100% — all buckets


def get_stage_4_cohort(stage: str) -> frozenset[int]:
    """Get canary cohort set for Stage 4 sub-phases.

    Args:
        stage: "4.1" / "4.2" / "4.3" / "10pct" / "50pct" / "100pct"

    Returns:
        frozenset of canary bucket indices
    """
    norm = stage.lower().replace(".", "").replace("pct", "").replace("%", "")
    mapping = {
        "41": STAGE_4_1_CANARY_10PCT,
        "10": STAGE_4_1_CANARY_10PCT,
        "42": STAGE_4_2_CANARY_50PCT,
        "50": STAGE_4_2_CANARY_50PCT,
        "43": STAGE_4_3_CANARY_100PCT,
        "100": STAGE_4_3_CANARY_100PCT,
    }
    if norm not in mapping:
        raise ValueError(f"Unknown stage: {stage} / use 4.1 / 4.2 / 4.3 or 10pct / 50pct / 100pct")
    return mapping[norm]


def resolve_variant_for_request(
    artist_slug: str | None,
    request_id: str | None,
    stage: str,
    canary_variant: str = "v3_filtered_tuned_b_warm",
    control_variant: str = "v3_filtered_tuned",
) -> tuple[str, int, bool]:
    """High-level helper: request features → variant decision.

    Args:
        artist_slug: matched artist slug
        request_id: request id (fallback)
        stage: Stage 4 phase ("4.1" / "4.2" / "4.3")
        canary_variant: B-warm variant name
        control_variant: default variant name

    Returns:
        (variant, bucket, is_canary_flag) tuple

    Examples:
        >>> # Stage 4.1 (10%) request for warm artist
        >>> variant, bucket, is_can = resolve_variant_for_request(
        ...     artist_slug="kim-hyun-su",
        ...     request_id=None,
        ...     stage="4.1",
        ... )
        >>> # variant = "v3_filtered_tuned_b_warm" if bucket 0 else "v3_filtered_tuned"
    """
    bucket = cohort_bucket(artist_slug=artist_slug, request_id=request_id)
    canary_set = get_stage_4_cohort(stage)
    is_canary_flag = is_canary(bucket, canary_set)
    variant = canary_variant if is_canary_flag else control_variant
    return variant, bucket, is_canary_flag
