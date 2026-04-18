"""Phase 5 Sprint 0 — Val-Test Gap 진단.

PSI, missingness drift, 세그먼트별 성능, 시점별 성능 곡선, leak audit.
결과: model_test_results/gap_diagnosis.json

Usage:
    PYTHONPATH=src python3 scripts/diagnose_gap.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
OUTPUT_DIR = ROOT / "model_test_results"


def compute_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index 계산.

    Args:
        expected: 기준 분포 (validation set).
        actual: 비교 분포 (test set).
        bins: 히스토그램 bin 수.

    Returns:
        PSI 값. > 0.2이면 significant drift.
    """
    # 공통 bin edge 사용
    eps = 1e-6
    combined = np.concatenate([expected, actual])
    finite_mask = np.isfinite(combined)
    if finite_mask.sum() < bins:
        return 0.0
    _, bin_edges = np.histogram(combined[finite_mask], bins=bins)

    exp_hist, _ = np.histogram(expected[np.isfinite(expected)], bins=bin_edges)
    act_hist, _ = np.histogram(actual[np.isfinite(actual)], bins=bin_edges)

    # 비율 계산
    exp_pct = (exp_hist + eps) / (exp_hist.sum() + eps * bins)
    act_pct = (act_hist + eps) / (act_hist.sum() + eps * bins)

    psi = float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))
    return psi


def compute_missingness_drift(
    df_valid: pd.DataFrame, df_test: pd.DataFrame, features: list[str],
) -> pd.DataFrame:
    """피처별 결측률 변화 계산.

    Returns:
        DataFrame with columns: feature, valid_missing_rate, test_missing_rate, drift.
    """
    rows = []
    for feat in features:
        v_rate = df_valid[feat].isna().mean() if feat in df_valid.columns else 1.0
        t_rate = df_test[feat].isna().mean() if feat in df_test.columns else 1.0
        rows.append({
            "feature": feat,
            "valid_missing_rate": float(v_rate),
            "test_missing_rate": float(t_rate),
            "drift": float(t_rate - v_rate),
        })
    return pd.DataFrame(rows)


def compute_segment_performance(
    df: pd.DataFrame, y_pred: np.ndarray, y_true: np.ndarray,
    segment_col: str,
) -> dict[str, dict[str, float]]:
    """세그먼트별 MdAPE, R², n 계산."""
    result: dict[str, dict[str, float]] = {}
    mask = np.isfinite(y_true) & np.isfinite(y_pred) & (y_true > 0)

    for seg_val in df[segment_col].unique():
        seg_mask = mask & (df[segment_col].values == seg_val)
        n = int(seg_mask.sum())
        if n == 0:
            result[str(seg_val)] = {"mdape": float("nan"), "r2": float("nan"), "n": 0}
            continue

        yt = y_true[seg_mask]
        yp = y_pred[seg_mask]
        ape = np.abs(yp - yt) / yt
        mdape = float(np.median(ape) * 100)

        ss_res = np.sum((yt - yp) ** 2)
        ss_tot = np.sum((yt - np.mean(yt)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        result[str(seg_val)] = {"mdape": mdape, "r2": r2, "n": n}

    return result


def compute_time_performance_curve(
    df: pd.DataFrame, y_pred: np.ndarray, y_true: np.ndarray,
    session_col: str = "회차",
) -> pd.DataFrame:
    """회차별 MdAPE 시계열 계산.

    Returns:
        DataFrame with columns: session, mdape, n.
    """
    mask = np.isfinite(y_true) & np.isfinite(y_pred) & (y_true > 0)
    sessions = sorted(df[session_col].unique())
    rows = []
    for sess in sessions:
        s_mask = mask & (df[session_col].values == sess)
        n = int(s_mask.sum())
        if n == 0:
            continue
        ape = np.abs(y_pred[s_mask] - y_true[s_mask]) / y_true[s_mask]
        rows.append({"session": int(sess), "mdape": float(np.median(ape) * 100), "n": n})
    return pd.DataFrame(rows).sort_values("session").reset_index(drop=True)


def run_leak_audit(
    df: pd.DataFrame, features: list[str], session_col: str = "회차",
) -> list[dict[str, str]]:
    """미래 정보 사용 의심 피처 탐지.

    검증 방법:
    1. 피처-세션 상관: 피처값과 세션(시간) 간 Pearson 상관이 |r| > 0.9이고,
       해당 피처가 cutoff 이전 데이터만으로 계산되어야 하는 경우 의심.
    2. 인과 역전: test 구간에서만 pierson 상관이 급변하면 의심.

    연속형 집계 피처(medium_avg_price 등)는 cutoff에 따라 값이 자연히 달라지므로
    단순 값 겹침 비교가 아닌 **상관 기반**으로 leak을 탐지한다.

    Returns:
        의심 피처 리스트 [{feature, reason}].
    """
    suspicious: list[dict[str, str]] = []

    train = df[df["split"] == "train"]
    test = df[df["split"] == "test"]

    if session_col not in df.columns:
        return suspicious

    for feat in features:
        if feat not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[feat]):
            continue

        # NaN이 아닌 값만
        train_vals = train[[feat, session_col]].dropna()
        test_vals = test[[feat, session_col]].dropna()

        if len(train_vals) < 30 or len(test_vals) < 30:
            continue

        # 1. 피처-세션 상관이 극도로 높으면 (|r| > 0.95) 세션 자체가 leak
        full_vals = df[[feat, session_col]].dropna()
        corr = full_vals[feat].corr(full_vals[session_col].astype(float))
        if abs(corr) > 0.95:
            suspicious.append({
                "feature": feat,
                "reason": f"피처-세션 상관 |r|={abs(corr):.3f} > 0.95 — 시간 인덱스 leak 의심",
            })
            continue

        # 2. Train 내 피처-target 상관 vs Test 내 상관 급변
        #    (target이 있는 경우만)
        if "낙찰가" in df.columns:
            train_with_target = train[[feat, "낙찰가"]].dropna()
            test_with_target = test[[feat, "낙찰가"]].dropna()

            if len(train_with_target) > 30 and len(test_with_target) > 30:
                train_price = pd.to_numeric(train_with_target["낙찰가"], errors="coerce")
                test_price = pd.to_numeric(test_with_target["낙찰가"], errors="coerce")

                corr_train = train_with_target[feat].corr(train_price)
                corr_test = test_with_target[feat].corr(test_price)

                if abs(corr_train) > 0.1 and abs(corr_test - corr_train) > 0.3:
                    suspicious.append({
                        "feature": feat,
                        "reason": (
                            f"피처-target 상관 급변: train r={corr_train:.3f}, "
                            f"test r={corr_test:.3f}"
                        ),
                    })

    return suspicious


def main() -> None:
    """Gap 진단 실행."""
    from visionai.price_engine.estimate_generator.hedonic_features import (
        HEDONIC_FEATURES,
        build_hedonic_features,
    )

    logger.info("=== Phase 5 Sprint 0: Val-Test Gap 진단 ===")

    # 1. 피처 빌드
    logger.info("Step 1: 피처 빌드")
    df = build_hedonic_features(DATA_PATH)

    valid = df[df["split"] == "valid"].copy()
    test = df[df["split"] == "test"].copy()

    # 2. 모델 예측 (기존 Model-A q50)
    logger.info("Step 2: Model-A 예측")
    from visionai.price_engine.estimate_generator.quantile_model import HedonicQuantileModel

    model_a_path = OUTPUT_DIR / "model_a_quantile.cbm"
    model_a = HedonicQuantileModel()
    model_a.load(model_a_path)

    # Valid 예측
    raw_q_valid = model_a.predict_raw(valid)
    y_pred_valid = np.exp(raw_q_valid[:, 1])  # q50
    y_true_valid = pd.to_numeric(valid["낙찰가"], errors="coerce").values

    # Test 예측
    raw_q_test = model_a.predict_raw(test)
    y_pred_test = np.exp(raw_q_test[:, 1])
    y_true_test = pd.to_numeric(test["낙찰가"], errors="coerce").values

    # 3. 전체 MdAPE
    v_mask = np.isfinite(y_true_valid) & (y_true_valid > 0)
    t_mask = np.isfinite(y_true_test) & (y_true_test > 0)
    v_ape = np.abs(y_pred_valid[v_mask] - y_true_valid[v_mask]) / y_true_valid[v_mask]
    t_ape = np.abs(y_pred_test[t_mask] - y_true_test[t_mask]) / y_true_test[t_mask]
    v_mdape = float(np.median(v_ape) * 100)
    t_mdape = float(np.median(t_ape) * 100)

    logger.info(
        "Valid MdAPE: %.2f%%, Test MdAPE: %.2f%%, Gap: %.2f%%p",
        v_mdape, t_mdape, t_mdape - v_mdape,
    )

    # 4. Feature PSI
    logger.info("Step 3: Feature PSI")
    numeric_features = [
        f for f in HEDONIC_FEATURES
        if f in valid.columns and pd.api.types.is_numeric_dtype(valid[f])
    ]
    psi_results = {}
    for feat in numeric_features:
        v_vals = valid[feat].dropna().values.astype(float)
        t_vals = test[feat].dropna().values.astype(float)
        if len(v_vals) > 10 and len(t_vals) > 10:
            psi_results[feat] = compute_psi(v_vals, t_vals)

    high_psi = {k: v for k, v in psi_results.items() if v > 0.2}
    logger.info("High PSI features (>0.2): %s", high_psi if high_psi else "None")

    # 5. Missingness drift
    logger.info("Step 4: Missingness drift")
    miss_drift = compute_missingness_drift(valid, test, HEDONIC_FEATURES)
    high_drift = miss_drift[miss_drift["drift"].abs() > 0.05]
    logger.info("High missingness drift: %d features", len(high_drift))

    # 6. 세그먼트별 성능
    logger.info("Step 5: 세그먼트별 성능")
    # 타입별
    seg_type_v = compute_segment_performance(valid, y_pred_valid, y_true_valid, "타입")
    seg_type_t = compute_segment_performance(test, y_pred_test, y_true_test, "타입")

    # Warm/Cold
    seg_cold_v = compute_segment_performance(valid, y_pred_valid, y_true_valid, "is_new_artist")
    seg_cold_t = compute_segment_performance(test, y_pred_test, y_true_test, "is_new_artist")

    for seg, metrics in seg_type_v.items():
        t_metrics = seg_type_t.get(seg, {})
        t_mdape_seg = t_metrics.get("mdape", 0)
        logger.info(
            "  %s: V=%.1f%% T=%.1f%% Gap=%.1f%%p",
            seg, metrics["mdape"], t_mdape_seg, t_mdape_seg - metrics["mdape"],
        )

    # 7. Cold 비중 변화
    cold_v = valid["is_new_artist"].astype(bool).mean()
    cold_t = test["is_new_artist"].astype(bool).mean()
    logger.info("Cold artist ratio: V=%.1f%% T=%.1f%%", cold_v * 100, cold_t * 100)

    # 8. 시점별 성능
    logger.info("Step 6: 시점별 성능 곡선")
    time_curve = compute_time_performance_curve(
        pd.concat([valid, test]),
        np.concatenate([y_pred_valid, y_pred_test]),
        np.concatenate([y_true_valid, y_true_test]),
    )

    # 9. Leak audit
    logger.info("Step 7: Leak audit")
    leak_results = run_leak_audit(df, numeric_features)
    logger.info("Suspicious features: %d", len(leak_results))

    # 10. 결과 저장
    diagnosis = {
        "valid_mdape": v_mdape,
        "test_mdape": t_mdape,
        "gap": t_mdape - v_mdape,
        "high_psi_features": high_psi,
        "high_missingness_drift": high_drift.to_dict("records") if len(high_drift) > 0 else [],
        "segment_type_valid": seg_type_v,
        "segment_type_test": seg_type_t,
        "segment_cold_valid": seg_cold_v,
        "segment_cold_test": seg_cold_t,
        "cold_ratio_valid": float(cold_v),
        "cold_ratio_test": float(cold_t),
        "time_curve": time_curve.to_dict("records"),
        "leak_audit": leak_results,
        "psi_all": {k: round(v, 4) for k, v in psi_results.items()},
    }

    output_path = OUTPUT_DIR / "gap_diagnosis.json"
    with open(output_path, "w") as f:
        json.dump(diagnosis, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Saved to %s", output_path)


if __name__ == "__main__":
    main()
