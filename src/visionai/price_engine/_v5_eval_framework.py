"""V5 cycle evaluation framework — archive-derived utility (salvaged 2026-05-08).

본 모듈의 위치 (코덱스 권고 옵션 C, 잔존 작업 3번):
- 출처: V5 pilot cycle (Day 1-4 PILOT FAIL 3/5 종결, 2026-04 cycle).
- 본 PR 의 의미: V5 specific gate evaluator 와 generic helper 가 혼재된 현재
  형태를 그대로 main 에 salvage. **generic infra 1차 승격 X / archive-derived
  utility 복원** 만.
- 비범용 범위 명시:
  * `_v5_` prefix 유지 = V5 pilot cycle history reference 보존 (rename 보류 결정)
  * 본 모듈의 `bootstrap_delta_ci` / `evaluate_*_gate` 는 V5 pilot threshold 에
    묶여 있음 — Track 1 / Track 2 confirmatory 용 canonical infra 로 그대로 사용 X
  * Track 1 / Track 2 의 cluster bootstrap rule (artist-cluster, A.1 v2 fix) 와는
    별도 / single source of truth 분리 의무

재사용 가능 helper (코덱스 권고):
- `lao_split` (artist-level GroupShuffleSplit, hard gate overlap=0) — Track 1 Stage
  4 confirmatory holdout 등에서 재사용 가능
- `fit_pca_train_only` / modality leakage prevention helpers — train-only fit 정책
  의 공용 utility 가치 있음

비권고 재사용 (코덱스 권고):
- `bootstrap_delta_ci` — V5 threshold semantics / artist-cluster bootstrap 미반영
- `evaluate_a_gate / evaluate_c_lite_gate / evaluate_full_integration_gate` —
  V5 pilot threshold / Track 1-2 governance 와 직접 호환 X

후속 decision items (사용자 결정 영역):
- cluster bootstrap shared helper 분리 여부
- V5 specific gate evaluator 분리 여부
- 진짜 범용 rename (예: `_eval_framework.py`) 여부

문서 anchor: `docs/archive/2026-05-08-gallery-tier-v4-research-closeout.md` §4
사용자 결정 영역 3번 / `docs/structural_pricing/06_evaluation_framework.md`.

Usage:
    from visionai.price_engine._v5_eval_framework import (
        lao_split, compute_segment_grid, evaluate_pass_fail, bootstrap_delta_ci
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


# ─────────────────────────────────────────────────────────────────────
# 1. LAO split (artist-level holdout)
# ─────────────────────────────────────────────────────────────────────
def lao_split(
    df: pd.DataFrame, group_col: str = "artist_slug", test_size: float = 0.20, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """Leave-Artist-Out split with hard gate.

    Returns: (train_idx, test_idx)
    Hard gate: train/test 의 artist 교집합 = 0 (assert).
    """
    if group_col not in df.columns:
        raise ValueError(f"Group column '{group_col}' not in df")
    groups = df[group_col].astype(str).to_numpy()
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(df, np.zeros(len(df)), groups))

    # Hard gate (코덱스 Day 1 권고)
    train_artists = set(groups[train_idx])
    test_artists = set(groups[test_idx])
    overlap = train_artists & test_artists
    assert len(overlap) == 0, f"Artist overlap detected: {len(overlap)} artists"

    return train_idx, test_idx


def lao_repeated_splits(
    df: pd.DataFrame, seeds: list[int], **kwargs
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Multiple LAO splits with different seeds. Each split has artist overlap=0."""
    return [lao_split(df, seed=s, **kwargs) for s in seeds]


# ─────────────────────────────────────────────────────────────────────
# 2. Exposure bucket (artist 단위 학습 표본 수 기반)
# ─────────────────────────────────────────────────────────────────────
def assign_exposure_bucket(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    group_col: str = "artist_slug",
) -> pd.Series:
    """각 row 의 exposure bucket: train 셋에서 그 artist 의 작품 수 기반.

    Buckets: '0-shot' / '1-3' / '4-10' / '10+'
    train_idx 에 없는 artist 는 '0-shot'.
    """
    train_groups = df.iloc[train_idx][group_col].astype(str)
    counts = train_groups.value_counts()

    def bucket(g: str) -> str:
        c = int(counts.get(g, 0))
        if c == 0:
            return "0-shot"
        elif c <= 3:
            return "1-3"
        elif c <= 10:
            return "4-10"
        else:
            return "10+"

    groups = df[group_col].astype(str)
    return groups.map(bucket)


# ─────────────────────────────────────────────────────────────────────
# 3. Price tercile (train-only 분포 기반, leakage 방지)
# ─────────────────────────────────────────────────────────────────────
def assign_price_tercile(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    price_col: str = "price_krw",
) -> pd.Series:
    """Price tercile (1/2/3) — train-only quantile 기반.

    코덱스 권고: PCA/tokenizer/embedding norm/neighbor index 모두 train-only fit.
    여기서도 동일 — quantile 은 train 에서 fit, 전체에 적용.
    """
    train_prices = df.iloc[train_idx][price_col].dropna()
    q1 = train_prices.quantile(1 / 3)
    q2 = train_prices.quantile(2 / 3)

    def tercile(p: float) -> str:
        if pd.isna(p):
            return "missing"
        if p <= q1:
            return "tercile_1"
        elif p <= q2:
            return "tercile_2"
        else:
            return "tercile_3"

    return df[price_col].map(tercile)


# ─────────────────────────────────────────────────────────────────────
# 4. Career stage availability
# ─────────────────────────────────────────────────────────────────────
def assign_career_stage_availability(
    df: pd.DataFrame, career_col: str = "career_stage"
) -> pd.Series:
    """career_stage 결측 여부."""
    if career_col not in df.columns:
        return pd.Series(["missing"] * len(df), index=df.index)
    return df[career_col].apply(
        lambda v: "available" if (isinstance(v, str) and v.strip() and v != "unknown") else "missing"
    )


# ─────────────────────────────────────────────────────────────────────
# 5. 48-cell segment grid (exposure × source × price tercile × career_stage)
# ─────────────────────────────────────────────────────────────────────
def compute_segment_grid(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    source_col: str = "source",
    group_col: str = "artist_slug",
    price_col: str = "price_krw",
    career_col: str = "career_stage",
) -> pd.DataFrame:
    """48-cell segment 정의 (test set 기준).

    4 (exposure) × 2 (source) × 3 (price tercile) × 2 (career_stage avail) = 48 cells

    Returns: DataFrame with columns
        [exposure, source, price_tercile, career_stage_avail, n, segment_id]
    """
    test_df = df.iloc[test_idx].copy()
    test_df["exposure"] = assign_exposure_bucket(df, train_idx, group_col).iloc[test_idx].values
    test_df["price_tercile"] = assign_price_tercile(df, train_idx, price_col).iloc[test_idx].values
    test_df["career_stage_avail"] = assign_career_stage_availability(df, career_col).iloc[test_idx].values

    # source 정규화
    if source_col in test_df.columns:
        test_df["source"] = test_df[source_col].astype(str)
    else:
        test_df["source"] = "unknown"

    # Group counts
    grid = (
        test_df.groupby(["exposure", "source", "price_tercile", "career_stage_avail"], dropna=False)
        .size()
        .reset_index(name="n")
    )
    grid["segment_id"] = (
        grid["exposure"].astype(str) + " | " + grid["source"].astype(str) + " | "
        + grid["price_tercile"].astype(str) + " | " + grid["career_stage_avail"].astype(str)
    )
    return grid


def annotate_segments(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    **kwargs,
) -> pd.DataFrame:
    """각 row 에 segment 라벨 부여 (test set 만)."""
    test_df = df.iloc[test_idx].copy().reset_index(drop=True)
    test_df["exposure"] = assign_exposure_bucket(df, train_idx, kwargs.get("group_col", "artist_slug")).iloc[test_idx].values
    test_df["price_tercile"] = assign_price_tercile(df, train_idx, kwargs.get("price_col", "price_krw")).iloc[test_idx].values
    test_df["career_stage_avail"] = assign_career_stage_availability(df, kwargs.get("career_col", "career_stage")).iloc[test_idx].values
    if "source" in test_df.columns:
        test_df["source"] = test_df["source"].astype(str)
    return test_df


# ─────────────────────────────────────────────────────────────────────
# 6. Metrics
# ─────────────────────────────────────────────────────────────────────
def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.median(np.abs(y_true - y_pred) / np.abs(y_true)) * 100)


def w_within(y_true: np.ndarray, y_pred: np.ndarray, threshold: float) -> float:
    return float(np.mean(np.abs(y_true - y_pred) / np.abs(y_true) <= threshold) * 100)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def metric_summary(y_true: np.ndarray, y_pred: np.ndarray, n: int | None = None) -> dict:
    """Standard metric 패키지: n / MdAPE / W30 / W50 / MAE."""
    return {
        "n": int(n if n is not None else len(y_true)),
        "MdAPE": round(mdape(y_true, y_pred), 2),
        "W30": round(w_within(y_true, y_pred, 0.30), 2),
        "W50": round(w_within(y_true, y_pred, 0.50), 2),
        "MAE": round(mae(y_true, y_pred), 2),
    }


# ─────────────────────────────────────────────────────────────────────
# 7. Segment-wise metrics
# ─────────────────────────────────────────────────────────────────────
def segment_metrics(
    test_segments_df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    min_n_threshold: int = 30,
    segment_cols: tuple[str, ...] = ("exposure", "source", "price_tercile", "career_stage_avail"),
) -> pd.DataFrame:
    """각 48 cell 별 metric. min_n_threshold 미만 cell 은 'underpowered' 표시.

    Returns: DataFrame [segment_id, n, MdAPE, W30, W50, MAE, status]
        status: 'reportable' / 'underpowered (dropped from pass/fail)'
    """
    df = test_segments_df.copy().reset_index(drop=True)
    df["y_true"] = y_true
    df["y_pred"] = y_pred

    grouped = df.groupby(list(segment_cols), dropna=False, observed=True)
    rows = []
    for keys, sub in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        n = len(sub)
        if n < min_n_threshold:
            status = "underpowered"
            mp = w30 = w50 = m = float("nan")
        else:
            status = "reportable"
            mp = mdape(sub["y_true"].to_numpy(), sub["y_pred"].to_numpy())
            w30 = w_within(sub["y_true"].to_numpy(), sub["y_pred"].to_numpy(), 0.30)
            w50 = w_within(sub["y_true"].to_numpy(), sub["y_pred"].to_numpy(), 0.50)
            m = mae(sub["y_true"].to_numpy(), sub["y_pred"].to_numpy())
        seg_dict = dict(zip(segment_cols, keys))
        rows.append({**seg_dict, "n": n, "MdAPE": mp, "W30": w30, "W50": w50, "MAE": m, "status": status})
    return pd.DataFrame(rows).sort_values(list(segment_cols)).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────
# 8. Bootstrap CI for ΔMdAPE (paired)
# ─────────────────────────────────────────────────────────────────────
def bootstrap_delta_ci(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Paired bootstrap CI on ΔMdAPE = MdAPE(b) - MdAPE(a).

    음수 = b 가 a 보다 좋음 (lower MdAPE).
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        ma = mdape(y_true[idx], y_pred_a[idx])
        mb = mdape(y_true[idx], y_pred_b[idx])
        deltas.append(mb - ma)
    deltas = np.array(deltas)
    return {
        "delta_mean": round(float(np.mean(deltas)), 3),
        "delta_median": round(float(np.median(deltas)), 3),
        "ci_lo": round(float(np.quantile(deltas, alpha / 2)), 3),
        "ci_hi": round(float(np.quantile(deltas, 1 - alpha / 2)), 3),
        "ci_excludes_zero": bool(np.quantile(deltas, alpha / 2) > 0 or np.quantile(deltas, 1 - alpha / 2) < 0),
    }


# ─────────────────────────────────────────────────────────────────────
# 9. Modality leakage prevention helpers
# ─────────────────────────────────────────────────────────────────────
def fit_pca_train_only(
    embeddings: np.ndarray,
    train_idx: np.ndarray,
    n_components: int = 32,
    random_state: int = 42,
):
    """PCA fit on train only (코덱스 권고: 모달리티 누수 방지).

    Returns: (pca, train_features, test_features)
    """
    from sklearn.decomposition import PCA
    pca = PCA(n_components=n_components, random_state=random_state)
    pca.fit(embeddings[train_idx])
    transformed = pca.transform(embeddings)
    return pca, transformed


def fit_scaler_train_only(values: np.ndarray, train_idx: np.ndarray):
    """StandardScaler fit on train only."""
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(values[train_idx].reshape(-1, 1) if values.ndim == 1 else values[train_idx])
    return scaler


# ─────────────────────────────────────────────────────────────────────
# 10. Pass/Fail gate evaluator (V5 cycle 사전등록 gate)
# ─────────────────────────────────────────────────────────────────────
@dataclass
class GateResult:
    name: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


def evaluate_a_gate(
    deltas_per_seed: list[float],  # ΔMdAPE per seed (cold-start, 33 - 32)
    other_segment_max_degradation: float,
    baseline_mdape: float,
) -> GateResult:
    """A pass gate (코덱스 권고):
    - cold-start mean ΔMdAPE ≤ -max(0.8pp, baseline*3%)
    - 3/3 seeds 같은 방향
    - seed std ≤ 0.6pp
    - 다른 segment 악화 ≤ +1.0pp
    """
    deltas = np.array(deltas_per_seed)
    mean_delta = float(np.mean(deltas))
    std_delta = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
    threshold = -max(0.8, baseline_mdape * 0.03)

    reasons = []
    passed = True
    if mean_delta > threshold:
        passed = False
        reasons.append(f"mean ΔMdAPE {mean_delta:.2f} > threshold {threshold:.2f}")
    if not (np.all(deltas < 0) or np.all(deltas > 0)):
        passed = False
        reasons.append(f"방향 불일치 (seeds={deltas.tolist()})")
    elif np.all(deltas > 0):
        passed = False
        reasons.append(f"3 seeds 모두 악화 (seeds={deltas.tolist()})")
    if std_delta > 0.6:
        passed = False
        reasons.append(f"seed std {std_delta:.2f} > 0.6")
    if other_segment_max_degradation > 1.0:
        passed = False
        reasons.append(f"다른 segment 악화 {other_segment_max_degradation:.2f} > 1.0pp")

    return GateResult(
        name="A_pass",
        passed=passed,
        details={
            "mean_delta": round(mean_delta, 3),
            "std_delta": round(std_delta, 3),
            "threshold": round(threshold, 3),
            "deltas_per_seed": [round(d, 2) for d in deltas],
            "max_other_segment_degradation": round(other_segment_max_degradation, 2),
        },
        reasons=reasons,
    )


def evaluate_c_lite_gate(
    deltas_per_seed_seen: list[float],
    deltas_per_seed_cold: list[float],
    baseline_seen_mdape: float,
    runtime_ratio: float = 1.0,
) -> GateResult:
    """C-lite pass gate (코덱스 권고):
    - seen-artist mean ΔMdAPE ≤ -max(0.5pp, baseline*2%)
    - 3/3 seeds 같은 방향
    - cold-start 악화 ≤ +0.5pp (3 seeds 평균)
    - runtime ≤ 4x baseline
    """
    seen_deltas = np.array(deltas_per_seed_seen)
    cold_deltas = np.array(deltas_per_seed_cold)
    mean_seen = float(np.mean(seen_deltas))
    threshold = -max(0.5, baseline_seen_mdape * 0.02)
    cold_mean = float(np.mean(cold_deltas))

    reasons = []
    passed = True
    if mean_seen > threshold:
        passed = False
        reasons.append(f"seen mean ΔMdAPE {mean_seen:.2f} > threshold {threshold:.2f}")
    if not np.all(seen_deltas < 0):
        passed = False
        reasons.append(f"seen direction 불일치 (seeds={seen_deltas.tolist()})")
    if cold_mean > 0.5:
        passed = False
        reasons.append(f"cold-start 악화 {cold_mean:.2f} > 0.5pp")
    if runtime_ratio > 4.0:
        passed = False
        reasons.append(f"runtime {runtime_ratio:.1f}x > 4x baseline")

    return GateResult(
        name="C_lite_pass",
        passed=passed,
        details={
            "seen_mean_delta": round(mean_seen, 3),
            "cold_mean_delta": round(cold_mean, 3),
            "runtime_ratio": round(runtime_ratio, 2),
            "threshold_seen": round(threshold, 3),
        },
        reasons=reasons,
    )


def evaluate_full_integration_gate(
    overall_delta_mean: float,
    cold_gain_retention: float,
    seen_gain_retention: float,
    max_segment_degradation: float,
    baseline_overall_mdape: float,
) -> GateResult:
    """통합 pass gate:
    - overall ΔMdAPE ≤ -max(0.8pp, baseline*3%)
    - cold-start gain ≥ 80% A 단독 유지
    - seen-artist gain ≥ 80% C-lite 단독 유지
    - max segment degradation ≤ +1.0pp
    """
    threshold = -max(0.8, baseline_overall_mdape * 0.03)
    reasons = []
    passed = True
    if overall_delta_mean > threshold:
        passed = False
        reasons.append(f"overall {overall_delta_mean:.2f} > threshold {threshold:.2f}")
    if cold_gain_retention < 0.80:
        passed = False
        reasons.append(f"cold gain retention {cold_gain_retention*100:.0f}% < 80%")
    if seen_gain_retention < 0.80:
        passed = False
        reasons.append(f"seen gain retention {seen_gain_retention*100:.0f}% < 80%")
    if max_segment_degradation > 1.0:
        passed = False
        reasons.append(f"max segment degradation {max_segment_degradation:.2f} > 1.0pp")

    return GateResult(
        name="Full_integration_pass",
        passed=passed,
        details={
            "overall_delta": round(overall_delta_mean, 3),
            "cold_retention": round(cold_gain_retention, 3),
            "seen_retention": round(seen_gain_retention, 3),
            "max_segment_degradation": round(max_segment_degradation, 2),
        },
        reasons=reasons,
    )
