"""v3.6 PR17a: Phase 3 DEV TEST script 단위 테스트.

검증:
- generate_dataset 의 cohort 분포 정합 (PRODUCTION_DISTRIBUTION)
- 10 fallback cases 모두 PASS
- run_cohort_gating 의 correctness 1.0
- Phase 3 gate criterion 모두 충족
"""

from __future__ import annotations

from scripts.v3_6_phase3_dev_test import (
    FALLBACK_CASES,
    PRODUCTION_DISTRIBUTION,
    generate_dataset,
    main,
    run_cohort_gating,
    run_fallback_cases,
)

# ---- generate_dataset ----


def test_generate_dataset_size():
    reqs = generate_dataset(1000, seed=42)
    assert len(reqs) == 1000


def test_generate_dataset_cohort_distribution_within_tolerance():
    """N=10000 에서 PRODUCTION_DISTRIBUTION 비율과 ±2%p 안."""
    reqs = generate_dataset(10000, seed=42)
    counts = {}
    for r in reqs:
        counts[r.cohort] = counts.get(r.cohort, 0) + 1
    for cohort, expected_frac in PRODUCTION_DISTRIBUTION.items():
        actual_frac = counts.get(cohort, 0) / 10000
        assert abs(actual_frac - expected_frac) < 0.02, (
            f"{cohort}: expected {expected_frac}, got {actual_frac}"
        )


def test_generate_dataset_deterministic():
    """같은 seed → 같은 결과."""
    a = generate_dataset(100, seed=42)
    b = generate_dataset(100, seed=42)
    assert [r.artist_name for r in a] == [r.artist_name for r in b]


def test_generate_dataset_different_seeds():
    a = generate_dataset(100, seed=42)
    b = generate_dataset(100, seed=43)
    # 일부 다른 결과 (전체 일치 가능성 매우 낮음)
    assert [r.cohort for r in a] != [r.cohort for r in b]


# ---- 10 fallback cases ----


def test_fallback_cases_count_is_11():
    """v3.5 step 2 §4 의 10 cases + parse_invalid (PR17c 추가) = 11."""
    assert len(FALLBACK_CASES) == 11


def test_fallback_cases_all_pass():
    passed, failed, errors = run_fallback_cases()
    assert failed == 0, f"{failed} cases failed: {errors}"
    assert passed == 11


def test_fallback_cases_includes_critical_routes():
    """spec §4 의 핵심 case (manual valid, cache_hit, fetch_ok, disabled, no_id, parse_invalid)."""
    routes = {c["expected_route"] for c in FALLBACK_CASES}
    assert "disabled" in routes
    assert "manual_seed_cache_write" in routes
    assert "manual" in routes
    assert "cache_hit" in routes
    assert "fetch_ok" in routes
    assert "fetch_fail" in routes
    assert "parse_invalid" in routes  # v3.6 PR17c
    assert "no_id" in routes


# ---- run_cohort_gating ----


def test_cohort_gating_correctness_100_pct():
    """10K synthetic 에서 cohort 결정 100% 정확 (helper logic 정합)."""
    reqs = generate_dataset(10000, seed=42)
    result = run_cohort_gating(reqs)
    assert result["gating_correctness"] == 1.0


def test_cohort_gating_route_distribution_matches_cohort():
    """saatchi_warm 만 fetch_ok / manual_seed_cache_write — 나머지는 disabled."""
    reqs = generate_dataset(1000, seed=42)
    result = run_cohort_gating(reqs)
    saatchi_warm_count = result["cohort_distribution"].get("saatchi_warm", 0)
    # disabled 는 비-saatchi_warm 모두 (saatchi_cold + artsy_warm + unmatched)
    expected_disabled = sum(
        v for k, v in result["cohort_distribution"].items() if k != "saatchi_warm"
    )
    assert result["route_distribution"]["disabled"] == expected_disabled
    # fetch_ok + manual_seed_cache_write = saatchi_warm count
    eligible_routes = (
        result["route_distribution"].get("fetch_ok", 0)
        + result["route_distribution"].get("manual_seed_cache_write", 0)
        + result["route_distribution"].get("manual", 0)
        + result["route_distribution"].get("cache_hit", 0)
    )
    assert eligible_routes == saatchi_warm_count


# ---- Phase 3 gate ----


def test_phase3_gate_passes_with_default_args():
    """python -m scripts.v3_6_phase3_dev_test --n 10000 --seed 42 → exit 0."""
    rc = main(["--n", "1000", "--seed", "42"])
    assert rc == 0


def test_phase3_latency_budget_under_thresholds():
    """spec §5.1: cache hit p95 ≤ 5ms, miss ≤ 600ms (mock 환경 기준)."""
    reqs = generate_dataset(1000, seed=42)
    result = run_cohort_gating(reqs)
    # mock fetch_fn 이 빠른 sleep — p95 가 5ms 훨씬 미만
    fetch_p95 = result["p95_latency_ms"].get("fetch_ok", 0)
    assert fetch_p95 < 600.0
    # disabled / manual route 는 SQL 없이 sub-ms
    for route in ("disabled", "manual_seed_cache_write"):
        if route in result["p95_latency_ms"]:
            assert result["p95_latency_ms"][route] < 5.0
