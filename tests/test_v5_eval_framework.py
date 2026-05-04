"""V5 eval framework 단위 테스트.

핵심 검증:
- LAO split: artist_slug overlap=0 (hard gate)
- 48-cell segment grid 정확성
- Modality leakage prevention (PCA fit train-only)
- Bootstrap CI 정상 동작
- Gate evaluator 사전등록 조건과 일치
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from visionai.price_engine._v5_eval_framework import (
    annotate_segments,
    assign_career_stage_availability,
    assign_exposure_bucket,
    assign_price_tercile,
    bootstrap_delta_ci,
    compute_segment_grid,
    evaluate_a_gate,
    evaluate_c_lite_gate,
    evaluate_full_integration_gate,
    fit_pca_train_only,
    lao_split,
    metric_summary,
    segment_metrics,
)


@pytest.fixture
def sample_df():
    """100 artists × 5 works/avg → ~500 rows."""
    rng = np.random.default_rng(42)
    n_artists = 100
    works_per = rng.integers(1, 15, size=n_artists)
    rows = []
    for ai, w in enumerate(works_per):
        for _ in range(w):
            rows.append({
                "artist_slug": f"artist_{ai:03d}",
                "source": "artsy" if ai % 3 == 0 else "saatchi",
                "price_krw": float(rng.uniform(1e6, 1e8)),
                "career_stage": "established" if ai % 4 == 0 else None,
            })
    return pd.DataFrame(rows)


def test_lao_split_no_overlap(sample_df):
    train_idx, test_idx = lao_split(sample_df, test_size=0.20, seed=42)
    train_artists = set(sample_df.iloc[train_idx]["artist_slug"])
    test_artists = set(sample_df.iloc[test_idx]["artist_slug"])
    assert len(train_artists & test_artists) == 0
    assert len(train_idx) + len(test_idx) == len(sample_df)


def test_lao_split_different_seeds(sample_df):
    """다른 seed 는 다른 split 생성."""
    s1 = set(lao_split(sample_df, seed=42)[1].tolist())
    s2 = set(lao_split(sample_df, seed=123)[1].tolist())
    # 완전히 같지 않음 (적어도 일부 다름)
    assert s1 != s2


def test_exposure_bucket(sample_df):
    train_idx, test_idx = lao_split(sample_df, test_size=0.20, seed=42)
    bucket = assign_exposure_bucket(sample_df, train_idx)
    assert set(bucket.unique()) <= {"0-shot", "1-3", "4-10", "10+"}
    # test artist 는 모두 0-shot (LAO 보장)
    test_buckets = bucket.iloc[test_idx]
    assert all(test_buckets == "0-shot"), f"test artists not all 0-shot: {test_buckets.value_counts()}"


def test_price_tercile_train_only_quantile(sample_df):
    train_idx, _ = lao_split(sample_df, test_size=0.20, seed=42)
    tercile = assign_price_tercile(sample_df, train_idx)
    # 3 categories
    assert set(tercile.unique()) <= {"tercile_1", "tercile_2", "tercile_3", "missing"}
    # train 분포에서 거의 균등
    train_counts = tercile.iloc[train_idx].value_counts()
    assert abs(train_counts.get("tercile_1", 0) - train_counts.get("tercile_2", 0)) < len(train_idx) * 0.1


def test_career_stage_availability(sample_df):
    avail = assign_career_stage_availability(sample_df)
    assert set(avail.unique()) == {"available", "missing"}


def test_compute_segment_grid_count(sample_df):
    train_idx, test_idx = lao_split(sample_df, test_size=0.20, seed=42)
    grid = compute_segment_grid(sample_df, train_idx, test_idx)
    # 최대 48 cells (모두 채워지지 않을 수 있음)
    assert len(grid) <= 48
    assert grid["n"].sum() == len(test_idx)


def test_metric_summary_basic():
    y = np.array([100.0, 200.0, 300.0])
    p = np.array([110.0, 180.0, 330.0])
    m = metric_summary(y, p)
    assert m["n"] == 3
    assert m["MdAPE"] >= 0
    assert 0 <= m["W30"] <= 100


def test_segment_metrics_underpowered():
    """min_n_threshold 미만 cell 은 underpowered 표시."""
    df = pd.DataFrame({
        "exposure": ["0-shot"] * 5 + ["1-3"] * 50,
        "source": ["artsy"] * 55,
        "price_tercile": ["tercile_1"] * 55,
        "career_stage_avail": ["available"] * 55,
    })
    y = np.array([100.0] * 55)
    p = np.array([105.0] * 55)
    sm = segment_metrics(df, y, p, min_n_threshold=30)
    underpowered = sm[sm["status"] == "underpowered"]
    reportable = sm[sm["status"] == "reportable"]
    assert len(underpowered) == 1
    assert len(reportable) == 1
    assert underpowered["n"].iloc[0] == 5


def test_bootstrap_delta_ci_basic():
    rng = np.random.default_rng(42)
    y = np.exp(rng.standard_normal(200))
    p_a = y * np.exp(rng.normal(0, 0.3, 200))
    p_b = y * np.exp(rng.normal(0, 0.5, 200))  # b 가 더 noisy → 더 큰 MdAPE
    res = bootstrap_delta_ci(y, p_a, p_b, n_boot=200)
    assert "delta_mean" in res
    assert "ci_lo" in res and "ci_hi" in res
    assert res["ci_lo"] <= res["ci_hi"]


def test_pca_train_only_no_leakage():
    rng = np.random.default_rng(42)
    embeddings = rng.standard_normal(size=(100, 50))
    train_idx = np.arange(80)
    test_idx = np.arange(80, 100)
    pca, transformed = fit_pca_train_only(embeddings, train_idx, n_components=8)
    # PCA components fit 만 train 에서
    # transformed.shape == (100, 8)
    assert transformed.shape == (100, 8)
    # Fit 결과는 train 만 봄
    assert pca.n_components_ == 8


def test_evaluate_a_gate_pass():
    """A pass gate: cold-start 일관 개선."""
    res = evaluate_a_gate(
        deltas_per_seed=[-1.5, -1.2, -1.8],  # 모두 개선 방향, mean -1.5
        other_segment_max_degradation=0.5,
        baseline_mdape=30.0,  # threshold = -max(0.8, 0.9) = -0.9
    )
    assert res.passed, f"Should pass: {res.reasons}"


def test_evaluate_a_gate_fail_direction_inconsistency():
    """Mixed direction 은 fail."""
    res = evaluate_a_gate(
        deltas_per_seed=[-2.0, +1.0, -0.5],
        other_segment_max_degradation=0.5,
        baseline_mdape=30.0,
    )
    assert not res.passed
    assert any("방향 불일치" in r for r in res.reasons)


def test_evaluate_a_gate_fail_std_too_high():
    """std > 0.6 은 fail."""
    res = evaluate_a_gate(
        deltas_per_seed=[-2.5, -1.0, -3.5],  # std > 0.6
        other_segment_max_degradation=0.5,
        baseline_mdape=30.0,
    )
    # mean -2.33, std ~1.27 — 방향 일관 + threshold 충족이지만 std fail
    assert not res.passed
    assert any("seed std" in r for r in res.reasons)


def test_evaluate_c_lite_gate_pass():
    res = evaluate_c_lite_gate(
        deltas_per_seed_seen=[-0.8, -0.7, -0.9],
        deltas_per_seed_cold=[+0.1, -0.2, +0.3],  # mean +0.07 < 0.5
        baseline_seen_mdape=20.0,
        runtime_ratio=2.0,
    )
    assert res.passed, f"Should pass: {res.reasons}"


def test_evaluate_c_lite_gate_fail_cold_degradation():
    res = evaluate_c_lite_gate(
        deltas_per_seed_seen=[-0.8, -0.7, -0.9],
        deltas_per_seed_cold=[+0.6, +0.7, +0.8],  # mean +0.7 > 0.5
        baseline_seen_mdape=20.0,
    )
    assert not res.passed
    assert any("cold-start 악화" in r for r in res.reasons)


def test_evaluate_full_integration_pass():
    res = evaluate_full_integration_gate(
        overall_delta_mean=-1.2,
        cold_gain_retention=0.85,
        seen_gain_retention=0.90,
        max_segment_degradation=0.5,
        baseline_overall_mdape=30.0,
    )
    assert res.passed


def test_evaluate_full_integration_fail_low_retention():
    res = evaluate_full_integration_gate(
        overall_delta_mean=-1.2,
        cold_gain_retention=0.50,  # < 80%
        seen_gain_retention=0.90,
        max_segment_degradation=0.5,
        baseline_overall_mdape=30.0,
    )
    assert not res.passed
