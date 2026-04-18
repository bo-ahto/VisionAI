"""Phase 5 통합 모델 학습 — 전 전략 적용.

Sprint 0~3 산출물을 통합하여 재학습 + 성능 측정.
결과: model_test_results/phase5_metrics.json

Usage:
    PYTHONPATH=src python3 scripts/train_phase5_integrated.py
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
MACRO_PATH = ROOT / "data" / "macro_session.csv"
OUTPUT_DIR = ROOT / "model_test_results"


def main() -> None:
    # ─── 1. Hedonic Features 빌드 ───
    logger.info("=== Step 1: Hedonic Features ===")
    from visionai.price_engine.estimate_generator.hedonic_features import (
        HEDONIC_FEATURES,
        build_hedonic_features,
    )

    df = build_hedonic_features(DATA_PATH)
    logger.info("Features: %d rows, %d features", len(df), len(HEDONIC_FEATURES))

    # ─── 2. 매크로 피처 조인 ───
    logger.info("=== Step 2: Macro Features ===")
    from visionai.price_engine.features.macro_indicators import (
        join_macro_features,
        load_macro_session,
    )

    if MACRO_PATH.exists():
        macro = load_macro_session(MACRO_PATH)
        df = join_macro_features(df, macro, session_col="회차", lag_sessions=1)
        logger.info("Macro features joined")
    else:
        logger.warning("macro_session.csv not found, skipping macro")

    # ─── 3. Artist Similarity 피처 ───
    logger.info("=== Step 3: Artist Similarity ===")
    from visionai.price_engine.features.artist_similarity import (
        build_artist_feature_vectors,
        compute_similarity_features,
        find_similar_artists,
    )

    train = df[df["split"] == "train"]
    # 작가 벡터는 train에서만 구축
    max_train_session = int(train["회차"].max())
    vectors = build_artist_feature_vectors(df, cutoff=max_train_session + 1)
    logger.info("Artist vectors: %d artists", len(vectors))

    # 전체 데이터에 similarity 피처 추가
    sim_features = []
    for _, row in df.iterrows():
        artist = row.get("artist_clean", "")
        medium = row.get("medium_category", None)
        similar = find_similar_artists(
            str(artist), vectors, k=5, medium_filter=str(medium) if medium else None,
        )
        feats = compute_similarity_features(str(artist), similar)
        sim_features.append(feats)

    sim_df = pd.DataFrame(sim_features, index=df.index)
    for col in sim_df.columns:
        df[col] = sim_df[col]
    logger.info("Similarity features added: %s", list(sim_df.columns))

    # ─── 4. Split ───
    train = df[df["split"] == "train"]
    calib = df[df["split"] == "calib"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]
    logger.info(
        "Train=%d, Calib=%d, Valid=%d, Test=%d",
        len(train), len(calib), len(valid), len(test),
    )

    # ─── 5. Model-A 학습 (MultiQuantile) ───
    logger.info("=== Step 4: Model-A 학습 ===")
    from visionai.price_engine.estimate_generator.quantile_model import (
        HedonicQuantileModel,
    )

    model_a = HedonicQuantileModel(iterations=2000, depth=8, learning_rate=0.05)
    model_a.fit(train, valid_df=calib, target_col="ln_price")
    model_a.save(OUTPUT_DIR / "model_a_quantile.cbm")

    # ─── 6. CQR Calibration ───
    logger.info("=== Step 5: CQR Calibration ===")
    from visionai.price_engine.estimate_generator.conformal_calibrator import (
        ConformalQuantileCalibrator,
    )

    raw_q_calib = model_a.predict_raw(calib)
    y_calib = calib["ln_price"].dropna()
    mask_calib = calib["ln_price"].notna()

    cqr = ConformalQuantileCalibrator(alpha=0.45)
    cqr.fit(y_calib.values, raw_q_calib[mask_calib.values])
    cqr.save(str(OUTPUT_DIR / "conformal_calibrator.pkl"))

    # ─── 7. Validation 평가 ───
    logger.info("=== Step 6: Validation 평가 ===")
    raw_q_valid = model_a.predict_raw(valid)
    y_valid = valid["ln_price"].values
    mask_v = np.isfinite(y_valid)

    # CQR calibrated
    cal_q_valid = cqr.predict(raw_q_valid[mask_v])
    price_low = np.exp(cal_q_valid[:, 0])
    price_mid = np.exp(cal_q_valid[:, 1])
    price_high = np.exp(cal_q_valid[:, 2])
    y_true_price = np.exp(y_valid[mask_v])

    # Coverage
    covered = (y_true_price >= price_low) & (y_true_price <= price_high)
    coverage = float(np.mean(covered))

    # MdAPE
    ape_v = np.abs(price_mid - y_true_price) / y_true_price
    v_mdape = float(np.median(ape_v) * 100)
    within_30_v = float(np.mean(ape_v <= 0.30) * 100)

    # R²
    ss_res = np.sum((y_true_price - price_mid) ** 2)
    ss_tot = np.sum((y_true_price - np.mean(y_true_price)) ** 2)
    v_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0

    logger.info("Valid MdAPE: %.2f%%, R2: %.4f, Coverage: %.1f%%", v_mdape, v_r2, coverage * 100)
    logger.info("Valid Within 30%%: %.1f%%", within_30_v)

    # ─── 8. Test 평가 ───
    logger.info("=== Step 7: Test 평가 ===")
    raw_q_test = model_a.predict_raw(test)
    y_test = test["ln_price"].values
    mask_t = np.isfinite(y_test)

    cal_q_test = cqr.predict(raw_q_test[mask_t])
    t_price_mid = np.exp(cal_q_test[:, 1])
    t_price_low = np.exp(cal_q_test[:, 0])
    t_price_high = np.exp(cal_q_test[:, 2])
    y_true_test = np.exp(y_test[mask_t])

    ape_t = np.abs(t_price_mid - y_true_test) / y_true_test
    t_mdape = float(np.median(ape_t) * 100)
    t_within_30 = float(np.mean(ape_t <= 0.30) * 100)

    t_covered = (y_true_test >= t_price_low) & (y_true_test <= t_price_high)
    t_coverage = float(np.mean(t_covered))

    ss_res_t = np.sum((y_true_test - t_price_mid) ** 2)
    ss_tot_t = np.sum((y_true_test - np.mean(y_true_test)) ** 2)
    t_r2 = float(1 - ss_res_t / ss_tot_t) if ss_tot_t > 0 else 0

    gap = t_mdape - v_mdape

    # Cold MdAPE
    cold_mask = test["is_new_artist"].astype(bool).values[mask_t]
    cold_mdape = float("nan")
    if cold_mask.sum() > 0:
        cold_ape = ape_t[cold_mask]
        cold_mdape = float(np.median(cold_ape) * 100)

    # Monotonicity
    mono = model_a.check_monotonicity(valid)

    logger.info("=" * 60)
    logger.info("Test MdAPE: %.2f%%, R2: %.4f", t_mdape, t_r2)
    logger.info("Test Coverage: %.1f%%, Within 30%%: %.1f%%", t_coverage * 100, t_within_30)
    logger.info("Val-Test Gap: %.2f%%p", gap)
    logger.info("Cold MdAPE: %.2f%%", cold_mdape)
    logger.info("Monotonicity: %.4f", mono)
    logger.info("=" * 60)

    # ─── 9. 결과 저장 ───
    coverage_overall = t_coverage
    within_30_pct = t_within_30

    metrics = {
        "valid_mdape": v_mdape,
        "test_mdape": t_mdape,
        "gap": gap,
        "valid_r2": v_r2,
        "test_r2": t_r2,
        "valid_coverage": coverage,
        "test_coverage": t_coverage,
        "valid_within_30": within_30_v,
        "test_within_30": t_within_30,
        "cold_mdape": cold_mdape,
        "monotonicity_rate": mono,
        "coverage_overall": coverage_overall,
        "hedonic_r2": v_r2,
        "within_30_pct": within_30_pct,
    }

    # gap_diagnosis.json 갱신
    gap_path = OUTPUT_DIR / "gap_diagnosis.json"
    if gap_path.exists():
        with open(gap_path) as f:
            diag = json.load(f)
        diag["valid_mdape"] = v_mdape
        diag["test_mdape"] = t_mdape
        diag["gap"] = gap
        diag["within_30_pct"] = t_within_30
        with open(gap_path, "w") as f:
            json.dump(diag, f, indent=2, ensure_ascii=False, default=str)

    # estimate_metrics.json 갱신
    metrics_path = OUTPUT_DIR / "estimate_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # phase5_metrics.json
    p5_path = OUTPUT_DIR / "phase5_metrics.json"
    with open(p5_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved to %s", p5_path)


if __name__ == "__main__":
    main()
