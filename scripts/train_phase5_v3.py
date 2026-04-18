"""Phase 5 최종 — 5가지 개선 통합.

1. CQR alpha 0.38 (Coverage G5 달성)
2. Distilled Student로 예측 (MdAPE 개선)
3. ECOS 실데이터 매크로 반영 (Gap 감소)
4. Feature Importance 기반 선별 (과적합 감소)
5. Warm/Cold 분리 평가

Usage:
    PYTHONPATH=src python3 scripts/train_phase5_v3.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
MACRO_PATH = ROOT / "data" / "macro_session.csv"
OUTPUT_DIR = ROOT / "model_test_results"

_COLD_THRESHOLD = 5
HIGH_PSI_FEATURES = ["market_price_index", "artist_career_length", "medium_avg_price"]


def normalize_high_psi(df: pd.DataFrame, train_mask: np.ndarray) -> pd.DataFrame:
    """PSI 높은 피처를 train 기준 z-score 정규화."""
    out = df.copy()
    for feat in HIGH_PSI_FEATURES:
        if feat not in out.columns:
            continue
        vals = pd.to_numeric(out[feat], errors="coerce")
        train_vals = vals[train_mask]
        mean, std = float(train_vals.mean()), float(train_vals.std())
        out[feat] = (vals - mean) / std if std > 0 else 0.0
    return out


def apply_cold_only_similarity(df: pd.DataFrame) -> pd.DataFrame:
    """Similarity 피처를 Cold artist에만 적용."""
    sim_cols = [
        "sim_avg_price_ln", "sim_weighted_price_ln",
        "sim_count", "sim_avg_distance",
    ]
    out = df.copy()
    for col in sim_cols:
        if col in out.columns:
            warm = out["artist_total_sold"].fillna(0) >= _COLD_THRESHOLD
            out.loc[warm, col] = 0.0
    return out


def select_features_by_importance(
    model: CatBoostRegressor, features: list[str], top_n: int = 40,
) -> list[str]:
    """Feature importance 기반 상위 N개 선별."""
    importances = model.get_feature_importance()
    feat_imp = sorted(
        zip(features, importances, strict=False),
        key=lambda x: x[1], reverse=True,
    )
    selected = [f for f, _ in feat_imp[:top_n]]
    dropped = [f for f, _ in feat_imp[top_n:]]
    logger.info("Selected %d features, dropped %d: %s", top_n, len(dropped), dropped)
    return selected


def evaluate_split(
    model_a, cqr, student, split_df, split_name, features,
) -> dict:
    """Model-A(CQR) + Distilled Student 통합 평가."""
    from visionai.price_engine.estimate_generator.hedonic_features import (
        CAT_FEATURE_NAMES,
    )

    y = split_df["ln_price"].values
    mask = np.isfinite(y)
    y_true_price = np.exp(y[mask])

    # Model-A + CQR: coverage
    raw_q = model_a.predict_raw(split_df)
    cal_q = cqr.predict(raw_q[mask])
    price_low = np.exp(cal_q[:, 0])
    price_mid_a = np.exp(cal_q[:, 1])
    price_high = np.exp(cal_q[:, 2])

    covered = (y_true_price >= price_low) & (y_true_price <= price_high)
    coverage = float(np.mean(covered))

    # Distilled Student: point prediction
    if student is not None and features:
        x_feat = split_df[features].copy()
        for col in CAT_FEATURE_NAMES:
            if col in x_feat.columns:
                x_feat[col] = x_feat[col].astype(str)
        x_valid = x_feat.iloc[np.where(mask)[0]]
        student_pred_log = student.predict(x_valid)
        price_mid = np.exp(student_pred_log)
    else:
        price_mid = price_mid_a

    ape = np.abs(price_mid - y_true_price) / y_true_price
    mdape = float(np.median(ape) * 100)
    within_30 = float(np.mean(ape <= 0.30) * 100)

    ss_res = np.sum((y_true_price - price_mid) ** 2)
    ss_tot = np.sum((y_true_price - np.mean(y_true_price)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0

    cold_mask = split_df["is_new_artist"].astype(bool).values[mask]
    cold_mdape = (
        float(np.median(ape[cold_mask]) * 100)
        if cold_mask.sum() > 0 else float("nan")
    )
    warm_mdape = (
        float(np.median(ape[~cold_mask]) * 100)
        if (~cold_mask).sum() > 0 else float("nan")
    )

    logger.info(
        "%s: MdAPE=%.2f%% (W=%.2f%% C=%.2f%%), R2=%.4f, Cov=%.1f%%, W30=%.1f%%",
        split_name, mdape, warm_mdape, cold_mdape, r2, coverage * 100, within_30,
    )
    return {
        "mdape": mdape, "warm_mdape": warm_mdape, "cold_mdape": cold_mdape,
        "r2": r2, "coverage": coverage, "within_30": within_30,
    }


def main() -> None:
    # ─── 1. 피처 빌드 ───
    logger.info("=== Step 1: Hedonic Features ===")
    from visionai.price_engine.estimate_generator.hedonic_features import (
        build_hedonic_features,
    )

    df = build_hedonic_features(DATA_PATH)

    # ─── 2. 매크로 (ECOS 실데이터 반영됨) ───
    logger.info("=== Step 2: Macro (with ECOS) ===")
    from visionai.price_engine.features.macro_indicators import (
        join_macro_features,
        load_macro_session,
    )

    if MACRO_PATH.exists():
        macro = load_macro_session(MACRO_PATH)
        df = join_macro_features(df, macro, session_col="회차", lag_sessions=1)

    # ─── 3. Similarity (Cold-only, warm-only donor) ───
    logger.info("=== Step 3: Similarity ===")
    from visionai.price_engine.features.artist_similarity import (
        build_artist_feature_vectors,
        compute_similarity_features,
        find_similar_artists,
    )

    train_only = df[df["split"] == "train"]
    vectors = build_artist_feature_vectors(train_only, cutoff=999999)

    sim_features = []
    for _, row in df.iterrows():
        artist = row.get("artist_clean", "")
        medium = row.get("medium_category", None)
        similar = find_similar_artists(
            str(artist), vectors, k=5,
            medium_filter=str(medium) if medium else None,
        )
        sim_features.append(compute_similarity_features(str(artist), similar))

    sim_df = pd.DataFrame(sim_features, index=df.index)
    for col in sim_df.columns:
        df[col] = sim_df[col]
    df = apply_cold_only_similarity(df)

    # ─── 4. PSI 정규화 ───
    logger.info("=== Step 4: PSI Normalization ===")
    train_mask = (df["split"] == "train").values
    df = normalize_high_psi(df, train_mask)

    # ─── 5. Split ───
    train = df[df["split"] == "train"]
    calib = df[df["split"] == "calib"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]
    logger.info("T=%d C=%d V=%d Te=%d", len(train), len(calib), len(valid), len(test))

    # ─── 6. Model-A ───
    logger.info("=== Step 5: Model-A ===")
    from visionai.price_engine.estimate_generator.quantile_model import (
        HedonicQuantileModel,
    )

    # 코덱스 P1 (2026-04-18): macro/similarity/PSI 피처를 실제 학습에 넘기도록 extra_features 추가.
    # 이전엔 위 단계에서 컬럼은 추가되지만 Model-A가 기본 HEDONIC_FEATURES만 학습해서 dead code였음.
    from visionai.price_engine.features.macro_indicators import MACRO_FEATURES
    _sim_cols = ["sim_avg_price_ln", "sim_weighted_price_ln", "sim_count", "sim_avg_distance"]
    extra_features = [c for c in (list(MACRO_FEATURES) + _sim_cols) if c in train.columns]
    logger.info("Model-A extra_features: %d개 (%s)", len(extra_features), extra_features)

    model_a = HedonicQuantileModel(iterations=2000, depth=8, learning_rate=0.05)
    model_a.fit(train, valid_df=calib, target_col="ln_price", extra_features=extra_features)
    model_a.save(OUTPUT_DIR / "model_a_quantile.cbm")

    # ─── 7. CQR alpha=0.38 (Coverage G5) ───
    logger.info("=== Step 6: CQR (alpha=0.38) ===")
    from visionai.price_engine.estimate_generator.conformal_calibrator import (
        ConformalQuantileCalibrator,
    )

    raw_q_calib = model_a.predict_raw(calib)
    y_calib = calib["ln_price"].dropna()
    mask_calib = calib["ln_price"].notna()

    cqr = ConformalQuantileCalibrator(alpha=0.38)
    cqr.fit(y_calib.values, raw_q_calib[mask_calib.values])
    cqr.save(str(OUTPUT_DIR / "conformal_calibrator.pkl"))

    # ─── 8. Knowledge Distillation ───
    logger.info("=== Step 7: Knowledge Distillation ===")
    from visionai.price_engine.estimate_generator.distillation import (
        DistillationTrainer,
    )

    teacher_path = OUTPUT_DIR / "target_transform_v1.cbm"
    distiller = DistillationTrainer(beta=0.8)
    student = None

    if teacher_path.exists():
        teacher_pred = distiller.generate_teacher_predictions_oof(
            df, teacher_model_path=teacher_path, n_folds=5,
        )
        y_true = pd.to_numeric(df["낙찰가"], errors="coerce").values
        y_distilled = distiller.build_distilled_target(y_true, teacher_pred)

        # ─── 9. Feature Selection ───
        logger.info("=== Step 8: Feature Selection ===")
        # 먼저 전체 피처로 임시 모델 학습 → importance 추출
        from visionai.price_engine.estimate_generator.hedonic_features import (
            CAT_FEATURE_NAMES,
        )
        from visionai.price_engine.features.track_config import STRICT_FEATURES

        all_features = STRICT_FEATURES
        cat_idx = [i for i, f in enumerate(all_features) if f in CAT_FEATURE_NAMES]
        x_temp = train[all_features].copy()
        for col in CAT_FEATURE_NAMES:
            if col in x_temp.columns:
                x_temp[col] = x_temp[col].astype(str)

        train_distilled = y_distilled[df["split"].values == "train"]
        valid_mask_d = np.isfinite(train_distilled)

        temp_model = CatBoostRegressor(
            iterations=500, depth=6, learning_rate=0.05,
            loss_function="RMSE", cat_features=cat_idx,
            random_seed=42, verbose=0,
        )
        temp_model.fit(x_temp[valid_mask_d], train_distilled[valid_mask_d])

        selected = select_features_by_importance(temp_model, all_features, top_n=35)
        logger.info("Top features: %s", selected[:10])

        # 코덱스 P2 (2026-04-18): 실제로 selected를 student에 전달. 이전엔 선별 결과가
        # 사용되지 않아 feature_selection_top35가 no-op였음.
        valid_y = np.log(
            pd.to_numeric(valid["낙찰가"], errors="coerce").values
        )
        student = distiller.fit_student(
            train, train_distilled, valid_df=valid, y_valid=valid_y,
            features=selected,
        )
        student.save_model(str(OUTPUT_DIR / "distilled_student.cbm"))

        student_features = selected
    else:
        logger.warning("Teacher not found.")
        student_features = []

    # ─── 10. 평가 ───
    logger.info("=== Step 9: 평가 ===")
    v = evaluate_split(model_a, cqr, student, valid, "Valid", student_features)
    t = evaluate_split(model_a, cqr, student, test, "Test", student_features)

    gap = t["mdape"] - v["mdape"]
    mono = model_a.check_monotonicity(valid)

    logger.info("=" * 60)
    logger.info("Gap: %.2f%%p, Monotonicity: %.4f", gap, mono)
    logger.info("=" * 60)

    # ─── 11. Gate 판정 ───
    logger.info("=== Gate 판정 ===")
    gates = {
        "G1 Test MdAPE ≤32%": t["mdape"] <= 32,
        "G2 Gap ≤2.5%p": abs(gap) <= 2.5,
        "G3 Test R² ≥0.40": t["r2"] >= 0.40,
        "G4 Cold ≤58%": t["cold_mdape"] <= 58,
        "G5 Coverage ≥55%": t["coverage"] >= 0.55,
        "G6 Within30 ≥53%": t["within_30"] >= 53,
        "G8 Monotonicity ≥0.99": mono >= 0.99,
    }
    for name, passed in gates.items():
        status = "PASS" if passed else "FAIL"
        logger.info("  %s: %s", name, status)

    passed_count = sum(gates.values())
    logger.info("Gate: %d/%d passed", passed_count, len(gates))

    # ─── 12. 저장 ───
    metrics = {
        "valid_mdape": v["mdape"], "test_mdape": t["mdape"], "gap": gap,
        "valid_r2": v["r2"], "test_r2": t["r2"],
        "valid_coverage": v["coverage"], "test_coverage": t["coverage"],
        "valid_within_30": v["within_30"], "test_within_30": t["within_30"],
        "cold_mdape": t["cold_mdape"], "warm_mdape": t["warm_mdape"],
        "monotonicity_rate": mono,
        "coverage_overall": t["coverage"],
        "within_30_pct": t["within_30"],
        "gates": gates,
        "improvements": [
            "cqr_alpha_0.38", "distilled_student_prediction",
            "ecos_real_data", "feature_selection_top35",
            "cold_only_similarity", "psi_normalization",
        ],
    }

    p = OUTPUT_DIR / "phase5_v3_metrics.json"
    with open(p, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info("Saved to %s", p)

    # gap_diagnosis + estimate_metrics 갱신
    for path_name in ["gap_diagnosis.json", "estimate_metrics.json"]:
        fpath = OUTPUT_DIR / path_name
        if fpath.exists():
            with open(fpath) as f:
                existing = json.load(f)
            existing.update({
                "valid_mdape": v["mdape"], "test_mdape": t["mdape"],
                "gap": gap, "within_30_pct": t["within_30"],
                "coverage_overall": t["coverage"],
            })
            with open(fpath, "w") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
