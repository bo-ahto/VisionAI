"""Phase A Shadow 배치 사전 점검 (offline) — 운영팀 D-1 실행.

코덱스 권고:
- offline parity (LLM 가능): 학습-재학습 동일 입력 → 동일 출력 검증
- fail-closed test cases 정의 (운영팀이 실제 환경에서 실행)
- latency baseline 측정 (단일 row 예측 시간 분포)

본 스크립트는 LLM 이 사전 작성 가능한 부분 (offline parity + fail-closed simulation)만 수행.
실제 in-environment parity (운영 dependency / config / runtime flag) 는 운영팀 직접 실행 필수.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
RESULTS = ROOT / "experiments" / "structural_v1" / "results"

MODEL_HASH = "track2_v1_20260507"
PIPELINE_VERSION = "f4_spline_v1_20260506"


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = out["artist_birth_year"] - out["artist_birth_year"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    return out


def restricted_cubic_spline(x, knots):
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(len(knots) - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def build_X(df):
    knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    return pd.DataFrame({
        "const": 1.0,
        "log_area": df["log_area"].values,
        "birth_year_centered": df["birth_year_centered"].values,
        "log_artist_total_works": df["log_artist_total_works"].values,
        "log_area_spline": sp[:, 0],
    })


def fit_huber(Xtr, ytr):
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr[:, 1:], ytr)
    return m


def predict_huber(m, X):
    return X[:, 1:] @ m.coef_ + m.intercept_


def hash_array(arr):
    return hashlib.sha256(arr.tobytes()).hexdigest()[:16]


# ─────────────────────────────────────
# 1. Self-parity (재현성)
# ─────────────────────────────────────
def test_self_parity(df_feat, y):
    logger.info("\n[1] Self-parity test (재현성)")
    X = build_X(df_feat)
    Xall = X.values.astype(float)
    yall = y.values.astype(float)

    m1 = fit_huber(Xall, yall)
    m2 = fit_huber(Xall, yall)
    pred1 = predict_huber(m1, Xall)
    pred2 = predict_huber(m2, Xall)
    diff_max = float(np.abs(pred1 - pred2).max())
    diff_mean = float(np.abs(pred1 - pred2).mean())
    coef_diff = float(np.abs(m1.coef_ - m2.coef_).max())

    pass_ = diff_max <= 1e-6
    logger.info(f"  재학습 동일 입력 동일 출력: max diff {diff_max:.2e}, mean diff {diff_mean:.2e}")
    logger.info(f"  계수 max diff: {coef_diff:.2e}")
    logger.info(f"  → {'✓ PASS' if pass_ else '✗ FAIL'} (요구: max diff ≤ 1e-6)")
    return {
        "test": "self_parity",
        "pass": pass_,
        "max_diff": diff_max,
        "coef_max_diff": coef_diff,
    }


# ─────────────────────────────────────
# 2. Feature pipeline 일관성
# ─────────────────────────────────────
def test_feature_pipeline(df_feat):
    logger.info("\n[2] Feature pipeline 일관성")
    X1 = build_X(df_feat).values.astype(float)
    X2 = build_X(df_feat).values.astype(float)
    diff = float(np.abs(X1 - X2).max())
    pass_ = diff <= 1e-9
    logger.info(f"  Feature 행렬 동일성: max diff {diff:.2e}")
    logger.info(f"  Feature hash: {hash_array(X1)}")
    logger.info(f"  → {'✓ PASS' if pass_ else '✗ FAIL'} (요구: deterministic)")
    return {
        "test": "feature_pipeline_deterministic",
        "pass": pass_,
        "max_diff": diff,
        "feature_hash": hash_array(X1),
    }


# ─────────────────────────────────────
# 3. Latency baseline (단일 row 예측 시간)
# ─────────────────────────────────────
def measure_latency(df_feat, y, n_iter=1000):
    logger.info(f"\n[3] Latency baseline ({n_iter} iter, single row predict)")
    X = build_X(df_feat).values.astype(float)
    m = fit_huber(X, y.values.astype(float))
    single = X[:1, 1:]

    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter_ns()
        _ = single @ m.coef_ + m.intercept_
        times.append(time.perf_counter_ns() - t0)

    arr = np.array(times)
    p50 = float(np.percentile(arr, 50)) / 1000  # μs
    p95 = float(np.percentile(arr, 95)) / 1000
    p99 = float(np.percentile(arr, 99)) / 1000
    logger.info(f"  Single row predict (μs): p50 {p50:.1f}, p95 {p95:.1f}, p99 {p99:.1f}")
    logger.info(f"  → 운영 latency p95 비교 baseline (V3 운영 환경에서 동일 측정 후 ratio 계산 필요)")
    return {
        "test": "latency_baseline_offline",
        "n_iter": n_iter,
        "p50_us": p50,
        "p95_us": p95,
        "p99_us": p99,
    }


# ─────────────────────────────────────
# 4. Fail-closed simulation (offline)
# ─────────────────────────────────────
def test_fail_closed_simulation():
    logger.info("\n[4] Fail-closed simulation (offline test cases)")

    cases = [
        {
            "name": "NO_BASELINE",
            "trigger": "학습-서빙 parity 검증 실패",
            "input": "동일 input → 학습 시 vs 운영 시 prediction 차이 > 1e-6",
            "expected": "Track 2 응답 X, V3 자동 라우팅, reason = 'NO_BASELINE'",
            "operational_test": "운영 환경에서 학습 모델 hash와 다른 hash 의도적 배포 → 자동 fallback 발동 확인",
        },
        {
            "name": "MODEL_ERROR",
            "trigger": "모델 응답 실패 / 의존성 장애",
            "input": "예측 함수에서 exception 발생",
            "expected": "Track 2 응답 X, V3 자동 라우팅, reason = 'MODEL_ERROR'",
            "operational_test": "예측 endpoint 강제 종료 → V3 fallback 5초 이내 발동 확인",
        },
        {
            "name": "PARITY_BREACH",
            "trigger": "학습 시 사용 변수 spec 과 운영 입력 불일치",
            "input": "필수 변수 결측 또는 단위 mismatch",
            "expected": "Track 2 응답 X, V3 자동 라우팅, reason = 'PARITY_BREACH'",
            "operational_test": "area_cm2 = None / birth_year = None 입력 → fallback 발동 확인",
        },
    ]

    logger.info(f"  Offline test 정의 (운영팀 D-1 실제 환경에서 실행 필수):")
    for c in cases:
        logger.info(f"    - {c['name']}: {c['trigger']}")
        logger.info(f"        입력: {c['input']}")
        logger.info(f"        기대: {c['expected']}")
        logger.info(f"        운영 테스트: {c['operational_test']}")

    return {
        "test": "fail_closed_test_cases",
        "cases": cases,
        "note": "Offline 정의 only. 실제 fail-closed 동작은 운영팀이 in-environment 에서 검증 필수.",
    }


# ─────────────────────────────────────
# 4.5. Sample parity 30 건 산출 (운영팀 in-environment 비교용 입력)
# ─────────────────────────────────────
def sample_parity_30(df_feat, y, n=30, seed=42):
    """첫 30 건 (또는 seed 기반 sample) 의 (input, expected_prediction) pairs 산출.
    운영팀이 in-environment 에서 동일 input → 동일 prediction 비교용."""
    logger.info(f"\n[4.5] Sample parity {n} 건 산출 (운영팀 비교용 입력 + 기대 출력)")
    X = build_X(df_feat).values.astype(float)
    y_arr = y.values.astype(float)
    m = fit_huber(X, y_arr)

    rng = np.random.default_rng(seed)
    idx = rng.choice(len(df_feat), size=min(n, len(df_feat)), replace=False)

    preds = X[idx, 1:] @ m.coef_ + m.intercept_

    samples = []
    for i, row_i in enumerate(idx):
        row = df_feat.iloc[row_i]
        samples.append({
            "row_idx": int(row_i),
            "input": {
                "artist_slug": str(row["artist_slug"]),
                "area_cm2": float(row["area_cm2"]),
                "artist_birth_year": int(row["artist_birth_year"]),
                "artist_total_works": int(row["artist_total_works"]),
            },
            "expected_log_prediction": float(preds[i]),
            "expected_prediction_krw": float(np.exp(preds[i])),
        })

    out = RESULTS / "phase_a_sample_parity_30.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump({"n": len(samples), "tolerance_max_diff": 1e-6,
                   "model_hash": MODEL_HASH, "samples": samples}, f, indent=2, ensure_ascii=False)
    logger.info(f"  → {out.relative_to(ROOT)} (운영팀: 동일 input → expected_log_prediction 비교, max diff ≤ 1e-6)")
    return {"test": "sample_parity_30_dataset", "n": len(samples), "output_path": str(out.relative_to(ROOT))}


# ─────────────────────────────────────
# 5. 운영팀 in-environment 점검 항목 (참고용 출력)
# ─────────────────────────────────────
def print_in_environment_checklist():
    logger.info("\n[5] 운영팀 in-environment 점검 (운영 환경 직접 실행 — 본 스크립트 범위 X)")
    items = [
        "운영 모델 artifact hash = 학습 시 hash 일치 (track2_v1_20260507)",
        "Feature pipeline version = 학습 시 version 일치 (f4_spline_v1_20260506)",
        "Dependency lock (requirements.txt / poetry.lock) 학습 환경과 동일",
        "Runtime flag / config 학습 시 가정과 동일 (KRW 환율 기준일 등)",
        "Fail-closed E2E 3종 (NO_BASELINE / MODEL_ERROR / PARITY_BREACH) 동작 확인",
        "Shadow log stream 분리 생성 (track2_shadow.log, V3 운영 로그와 구분)",
        "Slack alert 채널 연결 + 핵심 4종 alert (schema/latency/guardrail/fallback) 활성화 — 전체 8 rules 는 monitoring spec §2 참조",
        "Latency p95 ratio (track2 / V3) 측정 가능 — APM 연결",
    ]
    for i, item in enumerate(items, 1):
        logger.info(f"  [ ] {i}. {item}")


# ─────────────────────────────────────
# Main
# ─────────────────────────────────────
def run():
    logger.info("=" * 80)
    logger.info(f"Phase A Shadow Preflight (offline) — model_hash={MODEL_HASH}, pipeline={PIPELINE_VERSION}")
    logger.info("=" * 80)

    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]

    summary = {
        "model_hash": MODEL_HASH,
        "pipeline_version": PIPELINE_VERSION,
        "data_path": str(DATA.relative_to(ROOT)),
        "data_n_rows": int(len(df_feat)),
        "data_n_artists": int(df_feat["artist_slug"].nunique()),
        "tests": [],
    }

    summary["tests"].append(test_self_parity(df_feat, y))
    summary["tests"].append(test_feature_pipeline(df_feat))
    summary["tests"].append(measure_latency(df_feat, y))
    summary["tests"].append(test_fail_closed_simulation())
    summary["tests"].append(sample_parity_30(df_feat, y))
    print_in_environment_checklist()

    # 종합 판정
    parity_pass = all(t.get("pass", True) for t in summary["tests"] if "pass" in t)
    summary["offline_preflight_pass"] = parity_pass
    logger.info("\n" + "=" * 80)
    logger.info(f"Offline preflight: {'✓ PASS' if parity_pass else '✗ FAIL'}")
    logger.info(f"운영팀 in-environment 점검 + fail-closed 3종 운영 테스트 PASS 후 Phase A shadow 배치 가능")
    logger.info("=" * 80)

    out = RESULTS / "phase_a_preflight.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
