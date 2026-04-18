"""Phase 5 후속 과제 1 — MdAPE 개선.

개선 사항:
1. Similarity 피처를 Cold artist에만 적용 (Warm은 0)
2. PSI 높은 피처 정규화 (market_price_index, artist_career_length z-score)
3. CQR alpha 조정 (0.45→0.40) — Coverage 개선
4. Knowledge Distillation 실행 (Distilled 트랙)

Usage:
    PYTHONPATH=src python3 scripts/train_phase5_v2.py
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

# PSI가 높은 피처 → z-score 정규화 대상
HIGH_PSI_FEATURES = ["market_price_index", "artist_career_length", "medium_avg_price"]

# Cold artist 기준 (K-Auction 거래 < 5건)
_COLD_THRESHOLD = 5


def normalize_high_psi(df: pd.DataFrame, train_mask: np.ndarray) -> pd.DataFrame:
    """PSI 높은 피처를 train 기준 z-score 정규화."""
    out = df.copy()
    for feat in HIGH_PSI_FEATURES:
        if feat not in out.columns:
            continue
        vals = pd.to_numeric(out[feat], errors="coerce")
        train_vals = vals[train_mask]
        mean = float(train_vals.mean())
        std = float(train_vals.std())
        if std > 0:
            out[feat] = (vals - mean) / std
        else:
            out[feat] = 0.0
    return out


def apply_cold_only_similarity(df: pd.DataFrame) -> pd.DataFrame:
    """Similarity 피처를 Cold artist에만 적용, Warm은 0."""
    sim_cols = ["sim_avg_price_ln", "sim_weighted_price_ln", "sim_count", "sim_avg_distance"]
    out = df.copy()
    for col in sim_cols:
        if col not in out.columns:
            continue
        # Warm artist (total_sold >= threshold) → 0
        warm_mask = out["artist_total_sold"].fillna(0) >= _COLD_THRESHOLD
        out.loc[warm_mask, col] = 0.0
    return out


def main() -> None:
    # ─── 1. 피처 빌드 ───
    logger.info("=== Step 1: Hedonic Features ===")
    from visionai.price_engine.estimate_generator.hedonic_features import (
        build_hedonic_features,
    )

    df = build_hedonic_features(DATA_PATH)

    # ─── 2. 매크로 피처 ───
    logger.info("=== Step 2: Macro Features ===")
    from visionai.price_engine.features.macro_indicators import (
        join_macro_features,
        load_macro_session,
    )

    if MACRO_PATH.exists():
        macro = load_macro_session(MACRO_PATH)
        df = join_macro_features(df, macro, session_col="회차", lag_sessions=1)

    # ─── 3. Similarity 피처 (Cold-only) ───
    logger.info("=== Step 3: Similarity (Cold-only) ===")
    from visionai.price_engine.features.artist_similarity import (
        build_artist_feature_vectors,
        compute_similarity_features,
        find_similar_artists,
    )

    # Similarity donor: train split 행만 사용 (타입별 시간축 누수 방지)
    train_only = df[df["split"] == "train"]
    vectors = build_artist_feature_vectors(train_only, cutoff=999999)

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

    # Cold-only 적용
    df = apply_cold_only_similarity(df)
    logger.info("Similarity: Cold-only applied")

    # ─── 4. PSI 정규화 ───
    logger.info("=== Step 4: PSI Normalization ===")
    train_mask = (df["split"] == "train").values
    df = normalize_high_psi(df, train_mask)

    # ─── 5. Split ───
    train = df[df["split"] == "train"]
    calib = df[df["split"] == "calib"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]
    logger.info("Train=%d, Calib=%d, Valid=%d, Test=%d",
                len(train), len(calib), len(valid), len(test))

    # ─── 6. Model-A 학습 ───
    logger.info("=== Step 5: Model-A ===")
    from visionai.price_engine.estimate_generator.quantile_model import HedonicQuantileModel

    model_a = HedonicQuantileModel(iterations=2000, depth=8, learning_rate=0.05)
    model_a.fit(train, valid_df=calib, target_col="ln_price")
    model_a.save(OUTPUT_DIR / "model_a_quantile.cbm")

    # ─── 7. CQR (alpha=0.40 for better coverage) ───
    logger.info("=== Step 6: CQR (alpha=0.40) ===")
    from visionai.price_engine.estimate_generator.conformal_calibrator import (
        ConformalQuantileCalibrator,
    )

    raw_q_calib = model_a.predict_raw(calib)
    y_calib = calib["ln_price"].dropna()
    mask_calib = calib["ln_price"].notna()

    cqr = ConformalQuantileCalibrator(alpha=0.40)
    cqr.fit(y_calib.values, raw_q_calib[mask_calib.values])
    cqr.save(str(OUTPUT_DIR / "conformal_calibrator.pkl"))

    # ─── 8. Knowledge Distillation (Distilled 트랙) ───
    logger.info("=== Step 7: Knowledge Distillation ===")
    from visionai.price_engine.estimate_generator.distillation import DistillationTrainer

    teacher_path = OUTPUT_DIR / "target_transform_v1.cbm"
    distiller = DistillationTrainer(beta=0.8)

    if teacher_path.exists():
        logger.info("Generating teacher OOF predictions...")
        teacher_pred = distiller.generate_teacher_predictions_oof(
            df, teacher_model_path=teacher_path, n_folds=5,
        )
        has_teacher = np.isfinite(teacher_pred).sum()
        logger.info("Teacher OOF: %d/%d predictions", has_teacher, len(df))

        # Distilled target
        y_true = pd.to_numeric(df["낙찰가"], errors="coerce").values
        y_distilled = distiller.build_distilled_target(y_true, teacher_pred)

        # Train에서 distilled target으로 Student 학습
        train_distilled = y_distilled[df["split"].values == "train"]
        valid_y = np.log(pd.to_numeric(valid["낙찰가"], errors="coerce").values)

        student = distiller.fit_student(
            train, train_distilled, valid_df=valid, y_valid=valid_y,
        )
        student.save_model(str(OUTPUT_DIR / "distilled_student.cbm"))
        logger.info("Distilled student saved")
    else:
        logger.warning("Teacher model not found. Skipping distillation.")
        student = None

    # ─── 9. 평가 ───
    logger.info("=== Step 8: 평가 ===")

    def evaluate(split_df, split_name):
        raw_q = model_a.predict_raw(split_df)
        y = split_df["ln_price"].values
        mask = np.isfinite(y)

        cal_q = cqr.predict(raw_q[mask])
        price_mid = np.exp(cal_q[:, 1])
        price_low = np.exp(cal_q[:, 0])
        price_high = np.exp(cal_q[:, 2])
        y_true_price = np.exp(y[mask])

        ape = np.abs(price_mid - y_true_price) / y_true_price
        mdape = float(np.median(ape) * 100)
        within_30 = float(np.mean(ape <= 0.30) * 100)

        covered = (y_true_price >= price_low) & (y_true_price <= price_high)
        coverage = float(np.mean(covered))

        ss_res = np.sum((y_true_price - price_mid) ** 2)
        ss_tot = np.sum((y_true_price - np.mean(y_true_price)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0

        cold_mask = split_df["is_new_artist"].astype(bool).values[mask]
        cold_mdape = (
            float(np.median(ape[cold_mask]) * 100)
            if cold_mask.sum() > 0 else float("nan")
        )

        logger.info(
            "%s: MdAPE=%.2f%%, R2=%.4f, Coverage=%.1f%%, W30=%.1f%%, Cold=%.2f%%",
            split_name, mdape, r2, coverage * 100, within_30, cold_mdape,
        )
        return {
            "mdape": mdape, "r2": r2, "coverage": coverage,
            "within_30": within_30, "cold_mdape": cold_mdape,
        }

    v_result = evaluate(valid, "Valid")
    t_result = evaluate(test, "Test")
    gap = t_result["mdape"] - v_result["mdape"]
    mono = model_a.check_monotonicity(valid)

    logger.info("=" * 60)
    logger.info("Gap: %.2f%%p, Monotonicity: %.4f", gap, mono)
    logger.info("=" * 60)

    # ─── 10. 결과 저장 ───
    metrics = {
        "valid_mdape": v_result["mdape"],
        "test_mdape": t_result["mdape"],
        "gap": gap,
        "valid_r2": v_result["r2"],
        "test_r2": t_result["r2"],
        "valid_coverage": v_result["coverage"],
        "test_coverage": t_result["coverage"],
        "valid_within_30": v_result["within_30"],
        "test_within_30": t_result["within_30"],
        "cold_mdape": t_result["cold_mdape"],
        "monotonicity_rate": mono,
        "coverage_overall": t_result["coverage"],
        "hedonic_r2": v_result["r2"],
        "within_30_pct": t_result["within_30"],
        "improvements": [
            "similarity_cold_only",
            "psi_normalization",
            "cqr_alpha_0.40",
            "knowledge_distillation",
        ],
    }

    p5v2_path = OUTPUT_DIR / "phase5_v2_metrics.json"
    with open(p5v2_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved to %s", p5v2_path)

    # gap_diagnosis.json 갱신
    gap_path = OUTPUT_DIR / "gap_diagnosis.json"
    if gap_path.exists():
        with open(gap_path) as f:
            diag = json.load(f)
        diag["valid_mdape"] = v_result["mdape"]
        diag["test_mdape"] = t_result["mdape"]
        diag["gap"] = gap
        diag["within_30_pct"] = t_result["within_30"]
        with open(gap_path, "w") as f:
            json.dump(diag, f, indent=2, ensure_ascii=False, default=str)

    # estimate_metrics.json 갱신
    est_path = OUTPUT_DIR / "estimate_metrics.json"
    with open(est_path, "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
