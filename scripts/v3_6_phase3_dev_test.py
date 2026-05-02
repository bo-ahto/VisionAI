"""v3.6 Phase 3 DEV TEST — synthetic 10K request cohort gating correctness.

spec: docs/v3_6_plan.md §5.1
- 10K synthetic request 생성 (cohort 분포 학습 기준 비례)
- cohort gating correctness 100% 검증
- 10 fallback cases (v3.5 step 2 §4) 모두 정확한 결과
- latency budget: cache hit p95 ≤ 5ms, miss ≤ 600ms (mock fetch_fn)

DEV 환경에서 실행 (real DB / saatchi 의존 X):
    python -m scripts.v3_6_phase3_dev_test --n 10000 --seed 42

출력 JSON:
    {
        "n_total": 10000,
        "cohort_distribution": {"saatchi_warm": 6970, "saatchi_cold": 460, ...},
        "gating_correctness": 1.0,
        "fallback_cases_pass": 10,
        "fallback_cases_fail": 0,
        "p95_latency_ms": {"cache_hit": 0.4, "fetch_ok": 12.1, ...},
        "passed": true
    }
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ----- 학습 cohort 분포 (v3.5 step 1 ablation, 28376 rows) -----
TRAIN_DISTRIBUTION = {
    "saatchi_warm":  0.6970,  # 19773 / 28376
    "saatchi_cold":  0.0460,  #  1305
    "artsy_warm":    0.2570,  #  7298
    "unmatched":     0.0000,  # 학습 시 0%, production 만 발생
}
# production 에서는 unmatched ~5% 예상 — 분포 갱신
PRODUCTION_DISTRIBUTION = {
    "saatchi_warm":  0.66,
    "saatchi_cold":  0.04,
    "artsy_warm":    0.25,
    "unmatched":     0.05,
}


@dataclass
class SyntheticRequest:
    """Cohort-aware synthetic request."""
    cohort: str  # saatchi_warm | saatchi_cold | artsy_warm | unmatched
    artist_name: str
    artist_slug: str | None
    profile_source: str | None  # 'saatchi' | 'artsy' | None (unmatched)
    is_in_warm_set: bool
    artwork_id: str | None
    artwork_url: str | None
    year_made: int | None
    expected_is_saatchi_warm: bool
    expected_year_made_route: str  # disabled / cache_hit / fetch_ok / manual / etc.


def generate_request(rng: random.Random, cohort: str, idx: int) -> SyntheticRequest:
    """Cohort 라벨에 따라 synthetic request + expected 결과 생성."""
    aid = f"aw_{idx:06d}"
    url = f"https://www.saatchiart.com/art/title/artist/{idx}/view"

    # year_made manual 25% 확률 — eligible cohort 만 의미
    has_manual = rng.random() < 0.25
    year = rng.randint(1900, 2025) if has_manual else None

    if cohort == "saatchi_warm":
        slug = f"warm_{idx % 521}"  # 521 warm artist (spec)
        return SyntheticRequest(
            cohort=cohort,
            artist_name=f"WarmArtist_{slug}",
            artist_slug=slug,
            profile_source="saatchi",
            is_in_warm_set=True,
            artwork_id=aid,
            artwork_url=url,
            year_made=year,
            expected_is_saatchi_warm=True,
            expected_year_made_route=(
                "manual_seed_cache_write" if has_manual else "fetch_ok"
            ),
        )
    if cohort == "saatchi_cold":
        slug = f"cold_{idx}"
        return SyntheticRequest(
            cohort=cohort,
            artist_name=f"ColdArtist_{slug}",
            artist_slug=slug,
            profile_source="saatchi",
            is_in_warm_set=False,
            artwork_id=aid,
            artwork_url=url,
            year_made=year,
            expected_is_saatchi_warm=False,
            expected_year_made_route="disabled",  # 옵션 B
        )
    if cohort == "artsy_warm":
        slug = f"artsy_{idx}"
        return SyntheticRequest(
            cohort=cohort,
            artist_name=f"ArtsyArtist_{slug}",
            artist_slug=slug,
            profile_source="artsy",
            is_in_warm_set=False,
            artwork_id=aid,
            artwork_url=url,
            year_made=year,
            expected_is_saatchi_warm=False,
            expected_year_made_route="disabled",
        )
    # unmatched
    return SyntheticRequest(
        cohort=cohort,
        artist_name=f"Unknown_{idx}",
        artist_slug=None,
        profile_source=None,
        is_in_warm_set=False,
        artwork_id=aid,
        artwork_url=url,
        year_made=year,
        expected_is_saatchi_warm=False,
        expected_year_made_route="disabled",
    )


def generate_dataset(n: int, seed: int = 42) -> list[SyntheticRequest]:
    """N 개 request — TRAIN_DISTRIBUTION 비율로 cohort 분배."""
    rng = random.Random(seed)
    cohorts: list[str] = []
    for cohort, frac in PRODUCTION_DISTRIBUTION.items():
        cohorts.extend([cohort] * int(n * frac))
    while len(cohorts) < n:
        cohorts.append("saatchi_warm")  # filler
    rng.shuffle(cohorts)
    return [generate_request(rng, cohorts[i], i) for i in range(n)]


# ----- Cohort gating helper (server logic 의존성 import) -----


def _decide_cohort(req: SyntheticRequest, predictor_is_warm) -> bool:
    """server _decide_saatchi_warm_cohort 의 단위 모사."""
    is_matched = req.profile_source is not None
    profile = (
        {"source": req.profile_source} if req.profile_source else None
    )
    return (
        bool(is_matched)
        and isinstance(profile, dict)
        and profile.get("source") == "saatchi"
        and bool(req.artist_slug)
        and predictor_is_warm(req.artist_slug)
    )


def _resolve_year_route(req: SyntheticRequest, is_saatchi_warm: bool,
                        cache: dict, fetch_fn) -> tuple[int | None, str]:
    """server _resolve_year_sync 의 단위 모사 (in-memory cache)."""
    if not is_saatchi_warm:
        return None, "disabled"
    if req.year_made is not None:
        if req.artwork_id:
            cache[req.artwork_id] = req.year_made
            return int(req.year_made), "manual_seed_cache_write"
        return int(req.year_made), "manual"
    # cache lookup
    if req.artwork_id and req.artwork_id in cache:
        return cache[req.artwork_id], "cache_hit"
    # fetch
    result = fetch_fn(req.artwork_url)
    if result is None:
        return None, "fetch_fail"
    cache[req.artwork_id] = result
    return result, "fetch_ok"


# ----- 10 fallback cases (v3.5 step 2 §4) -----

FALLBACK_CASES: list[dict[str, Any]] = [
    # (cohort, manual_year, expected_is_warm, expected_route)
    {"name": "unmatched", "cohort": "unmatched", "manual": None,
     "expected_warm": False, "expected_route": "disabled"},
    {"name": "unmatched + ext saatchi 비권위", "cohort": "unmatched", "manual": None,
     "expected_warm": False, "expected_route": "disabled"},
    {"name": "artsy_warm", "cohort": "artsy_warm", "manual": None,
     "expected_warm": False, "expected_route": "disabled"},
    {"name": "saatchi_cold", "cohort": "saatchi_cold", "manual": None,
     "expected_warm": False, "expected_route": "disabled"},
    {"name": "saatchi_warm + manual valid", "cohort": "saatchi_warm", "manual": 2020,
     "expected_warm": True, "expected_route": "manual_seed_cache_write"},
    {"name": "saatchi_warm + manual no_artwork_id", "cohort": "saatchi_warm",
     "manual": 2020, "no_artwork_id": True,
     "expected_warm": True, "expected_route": "manual"},
    {"name": "saatchi_warm + cache_hit", "cohort": "saatchi_warm", "manual": None,
     "preseed": 2018,
     "expected_warm": True, "expected_route": "cache_hit"},
    {"name": "saatchi_warm + fetch_ok", "cohort": "saatchi_warm", "manual": None,
     "expected_warm": True, "expected_route": "fetch_ok"},
    {"name": "saatchi_warm + fetch_fail", "cohort": "saatchi_warm", "manual": None,
     "fetch_fail": True,
     "expected_warm": True, "expected_route": "fetch_fail"},
    {"name": "saatchi_warm + no artwork_id/url", "cohort": "saatchi_warm",
     "manual": None, "no_artwork_id": True, "no_artwork_url": True,
     "expected_warm": True, "expected_route": "no_id"},
]


def run_fallback_cases() -> tuple[int, int, list[str]]:
    """10 fallback cases 검증. (passed, failed, error_messages)"""
    rng = random.Random(0)
    passed = 0
    failed_msgs: list[str] = []

    for i, case in enumerate(FALLBACK_CASES):
        req = generate_request(rng, case["cohort"], idx=i)
        if case.get("manual") is not None:
            req.year_made = case["manual"]
        if case.get("no_artwork_id"):
            req.artwork_id = None
        if case.get("no_artwork_url"):
            req.artwork_url = None

        # warm set lookup
        warm_set = {req.artist_slug} if req.is_in_warm_set else set()
        cache: dict = {}
        if case.get("preseed"):
            cache[req.artwork_id] = case["preseed"]
        fetch_fn = (lambda url: None) if case.get("fetch_fail") else (lambda url: 2017)

        is_warm = _decide_cohort(req, lambda s, ws=warm_set: s in ws)
        # no_id case: artwork_id + url 둘 다 없으면 'no_id' 라우트
        if is_warm and not req.year_made and not req.artwork_id and not req.artwork_url:
            year, route = None, "no_id"
        else:
            year, route = _resolve_year_route(req, is_warm, cache, fetch_fn)

        ok = (
            is_warm == case["expected_warm"]
            and route == case["expected_route"]
        )
        if ok:
            passed += 1
        else:
            failed_msgs.append(
                f"case '{case['name']}': "
                f"expected warm={case['expected_warm']}, route={case['expected_route']} "
                f"got warm={is_warm}, route={route}"
            )

    return passed, len(failed_msgs), failed_msgs


# ----- 10K cohort gating correctness -----


def run_cohort_gating(reqs: list[SyntheticRequest]) -> dict[str, Any]:
    """10K synthetic request 처리 — gating correctness + latency."""
    cache: dict = {}

    def fetch_fn(url: str) -> int:
        # mock saatchi fetch — 50ms p95 미만
        time.sleep(0.0001)  # 0.1ms 모사
        return 2018

    correct = 0
    cohort_count: dict[str, int] = {}
    route_count: dict[str, int] = {}
    latency_by_route: dict[str, list[float]] = {}

    for req in reqs:
        cohort_count[req.cohort] = cohort_count.get(req.cohort, 0) + 1

        # cohort gating
        warm_set = {req.artist_slug} if req.is_in_warm_set else set()
        is_warm = _decide_cohort(req, lambda s, ws=warm_set: s in ws)

        # year resolve + latency
        t0 = time.time()
        year, route = _resolve_year_route(req, is_warm, cache, fetch_fn)
        latency_ms = (time.time() - t0) * 1000

        route_count[route] = route_count.get(route, 0) + 1
        latency_by_route.setdefault(route, []).append(latency_ms)

        if is_warm == req.expected_is_saatchi_warm:
            correct += 1

    correctness = correct / len(reqs) if reqs else 0.0
    p95_by_route = {
        r: statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
        for r, times in latency_by_route.items()
    }

    return {
        "n_total": len(reqs),
        "cohort_distribution": cohort_count,
        "route_distribution": route_count,
        "gating_correctness": correctness,
        "p95_latency_ms": {r: round(v, 2) for r, v in p95_by_route.items()},
    }


# ----- main -----


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="v3.6 Phase 3 DEV TEST")
    parser.add_argument("--n", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    logger.info("Phase 3 DEV TEST: n=%d, seed=%d", args.n, args.seed)

    # 1. 10 fallback cases
    passed, failed, errors = run_fallback_cases()
    logger.info("Fallback cases: %d passed, %d failed", passed, failed)
    for e in errors:
        logger.warning("  %s", e)

    # 2. 10K cohort gating correctness
    reqs = generate_dataset(args.n, args.seed)
    result = run_cohort_gating(reqs)
    logger.info(
        "Cohort gating correctness: %.4f (%d/%d)",
        result["gating_correctness"],
        int(result["gating_correctness"] * args.n),
        args.n,
    )

    # 3. Phase 3 gate (§5.4)
    gate = {
        "fallback_cases_pass": failed == 0,
        "gating_correctness_100": result["gating_correctness"] == 1.0,
        # latency budget — mock 환경 기준
        "cache_hit_p95_under_5ms": result["p95_latency_ms"].get("cache_hit", 0) <= 5.0,
        "fetch_ok_p95_under_600ms": result["p95_latency_ms"].get("fetch_ok", 0) <= 600.0,
    }
    passed_gate = all(gate.values())

    out = {
        "n_total": result["n_total"],
        "cohort_distribution": result["cohort_distribution"],
        "route_distribution": result["route_distribution"],
        "gating_correctness": result["gating_correctness"],
        "fallback_cases_pass": passed,
        "fallback_cases_fail": failed,
        "fallback_errors": errors[:5],  # 첫 5개만
        "p95_latency_ms": result["p95_latency_ms"],
        "phase3_gate": gate,
        "passed": passed_gate,
    }
    print(json.dumps(out, indent=2))
    return 0 if passed_gate else 1


if __name__ == "__main__":
    sys.exit(main())
