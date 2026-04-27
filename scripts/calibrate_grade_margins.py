"""1차 시장 모델 — 등급별 실측 MdAPE + coverage 기반 마진(m) 재조정.

배경 (협력자 피드백 Q7 → Q-margin):
- 보고서 §6.2의 등급 마진 m (A=0.20, B=0.30, C=0.50, D=0.70)은 임의 휴리스틱.
- 보고서 §7.3의 "MdAPE (추정)" 표는 A 외에 실측 아님.
- 본 스크립트는 v3-filtered-tuned 모델로 등급별 실측 MdAPE + 현재 m 적용 시 coverage
  측정 + 목표 coverage 기반 m 재조정값을 산출한다.

산출물:
- model_test_results/grade_margin_calibration.json — 등급별 실측 + 권장 m
- model_test_results/grade_margin_calibration_report.md — 사람 친화 요약

Usage:
    PYTHONPATH=src python3 scripts/calibrate_grade_margins.py
    PYTHONPATH=src python3 scripts/calibrate_grade_margins.py --target-coverage 0.80
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import KFold, GroupKFold

# tune script와 같은 helper 사용
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_primary_market_v3_filtered import (
    CB_FEATURES, CAT_FEATURES, _cb_pool, _label_encode_xgb,
    _mdape, load_data, prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "model_test_results"

# 현재 운용 마진 (primary_predictor.determine_confidence)
CURRENT_MARGIN = {"A": 0.20, "B": 0.30, "C": 0.50, "D": 0.70}

# 등급 결정 임계값 (primary_predictor.determine_confidence와 동일)
A_MIN_TRAINING = 5  # matched + count >= 5 → A
B_MIN_TRAINING = 1  # matched + count >= 1 → B


def determine_grade_for_row(
    artist_train_count: int,
    has_birth_year: bool,
    has_manual_profile: bool = False,
) -> str:
    """primary_predictor.determine_confidence 로직과 동일.

    Args:
        artist_train_count: 학습 fold 안 해당 작가의 작품 수.
        has_birth_year: birth_year 존재 여부.
        has_manual_profile: 매뉴얼 프로필 입력 여부 (CV에서는 항상 False).
    """
    is_matched = artist_train_count > 0  # 학습 fold에 해당 작가 있으면 매칭
    if is_matched and artist_train_count >= A_MIN_TRAINING:
        return "A"
    if is_matched and artist_train_count >= B_MIN_TRAINING:
        return "B"
    if has_birth_year or has_manual_profile:
        return "C"
    return "D"


def _train_predict_fold(X_tr, y_tr, X_te, y_te, seed=42):
    """v3-filtered-tuned 사양으로 fold 학습 + 예측. ensemble (CatBoost + XGBoost) 반환."""
    cb = CatBoostRegressor(
        iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
        verbose=0, random_seed=seed, allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr), eval_set=_cb_pool(X_te, y_te), early_stopping_rounds=50)
    cb_pred = cb.predict(_cb_pool(X_te))

    Xtr_e, Xte_e, _ = _label_encode_xgb(X_tr, X_te)
    dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
    dtest = xgb.DMatrix(Xte_e, label=y_te)
    m = xgb.train(
        params={
            "objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 0,
            "seed": seed,
        },
        dtrain=dtrain, num_boost_round=1000,
        evals=[(dtest, "test")], early_stopping_rounds=50, verbose_eval=False,
    )
    xgb_pred = m.predict(dtest)
    # primary_predictor 라우팅: warm은 XGBoost, cold는 CatBoost.
    # 캘리브레이션은 ensemble 평균값으로 대표 사용 (per-row routing은 이후 분석 단계에서 적용).
    return cb_pred, xgb_pred


def calibrate(target_coverage: float = 0.80) -> dict:
    """등급별 실측 MdAPE + 현재 m 적용 coverage + 목표 coverage 기반 신규 m 산출."""
    logger.info("=" * 70)
    logger.info("등급별 마진 캘리브레이션 시작 — 목표 coverage %.0f%%", target_coverage * 100)
    logger.info("=" * 70)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy().reset_index(drop=True)
    X, y, groups = prepare_features(df)
    logger.info("Data: %d rows, %d artists", len(df), len(set(groups)))

    # 5-Fold KFold (작가가 fold에 걸쳐 분포 → 등급 결정에 자연스러움)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    all_records = []
    for fold_idx, (tr, te) in enumerate(kf.split(X), 1):
        logger.info("[Fold %d/5] train=%d test=%d", fold_idx, len(tr), len(te))
        cb_pred, xgb_pred = _train_predict_fold(X.iloc[tr], y[tr], X.iloc[te], y[te])

        # 학습 fold에 해당 작가가 몇 건 있는지 카운트 (등급 결정용)
        train_artist_counts = pd.Series(groups[tr]).value_counts()

        for i, te_idx in enumerate(te):
            artist = groups[te_idx]
            train_count = int(train_artist_counts.get(artist, 0))
            has_by = bool(X.iloc[te_idx]["has_birth_year"] >= 0.5)
            grade = determine_grade_for_row(train_count, has_by)

            actual_price = float(np.exp(y[te_idx]))
            cb_p = float(np.exp(cb_pred[i]))
            xgb_p = float(np.exp(xgb_pred[i]))
            # primary_predictor 라우팅 그대로
            use_xgb = grade in ("A", "B")  # matched (warm) → XGBoost
            pred_price = xgb_p if use_xgb else cb_p

            all_records.append({
                "fold": fold_idx,
                "grade": grade,
                "actual": actual_price,
                "pred": pred_price,
                "ape": abs(actual_price - pred_price) / actual_price,
            })

    df_eval = pd.DataFrame(all_records)
    logger.info("\nEval pool: %d rows (folds 1-5 합산)", len(df_eval))
    logger.info("Grade distribution:\n%s", df_eval["grade"].value_counts())

    # 등급별 통계
    result: dict = {
        "target_coverage": target_coverage,
        "n_total": int(len(df_eval)),
        "current_margin": CURRENT_MARGIN.copy(),
        "by_grade": {},
    }

    for g in ["A", "B", "C", "D"]:
        sub = df_eval[df_eval["grade"] == g]
        n = len(sub)
        if n == 0:
            result["by_grade"][g] = {"n": 0, "note": "no samples"}
            continue
        mdape = float(np.median(sub["ape"]) * 100)
        mean_ape = float(np.mean(sub["ape"]) * 100)
        # 현재 m으로 coverage 계산
        m_curr = CURRENT_MARGIN[g]
        coverage_curr = float(np.mean(sub["ape"] <= m_curr) * 100)
        # 목표 coverage 기반 m 권장값 = APE의 target quantile
        m_recommended = float(np.quantile(sub["ape"], target_coverage))
        # 보수적 보정 (5% 마진)
        m_with_safety = round(min(m_recommended * 1.05, 0.95), 3)

        result["by_grade"][g] = {
            "n": int(n),
            "mdape_pct": round(mdape, 1),
            "mean_ape_pct": round(mean_ape, 1),
            "current_m": m_curr,
            "current_coverage_pct": round(coverage_curr, 1),
            "recommended_m_raw": round(m_recommended, 3),
            "recommended_m": m_with_safety,
            "delta": round(m_with_safety - m_curr, 3),
        }
        logger.info(
            "[%s] n=%d  MdAPE=%.1f%%  현재m=%.2f→coverage=%.1f%%  권장m=%.3f (Δ%+.3f)",
            g, n, mdape, m_curr, coverage_curr, m_with_safety, m_with_safety - m_curr,
        )

    return result


def write_report(result: dict, out_md: Path) -> None:
    """사람 친화 요약 보고서 .md 작성."""
    target = int(result["target_coverage"] * 100)
    lines = [
        f"# 등급별 마진 실측 캘리브레이션 보고서 — 목표 coverage {target}%",
        "",
        f"- 총 평가 샘플: {result['n_total']:,}",
        f"- 목표 coverage: {target}% (가격이 예측 범위 안에 들어올 비율)",
        "",
        "## 등급별 결과",
        "",
        "| 등급 | 표본 | 실측 MdAPE | 현재 m | 현재 coverage | 권장 m | 변화 |",
        "|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    for g in ["A", "B", "C", "D"]:
        s = result["by_grade"].get(g, {})
        if s.get("n", 0) == 0:
            lines.append(f"| {g} | 0 | — | — | — | — | — |")
            continue
        lines.append(
            f"| {g} | {s['n']:,} | {s['mdape_pct']:.1f}% | "
            f"{s['current_m']:.2f} | {s['current_coverage_pct']:.1f}% | "
            f"**{s['recommended_m']:.3f}** | {s['delta']:+.3f} |"
        )
    lines.extend([
        "",
        "## 해석",
        "",
        "- **실측 MdAPE**: 5-Fold CV로 측정한 등급별 실제 오차율의 중앙값 (가격 기준).",
        "- **현재 coverage**: 현재 m 값으로 계산한 가격 범위에 실제 가격이 들어가는 비율.",
        f"  - {target}% 미만이면 m이 너무 좁음 (사용자에게 신뢰도 낮은 약속).",
        f"  - {target}% 훨씬 초과면 m이 너무 넓음 (불필요하게 보수적).",
        "- **권장 m**: 등급별 APE의 quantile_{}에 안전 마진 5% 추가.".format(target),
        "",
        "## 권장 적용",
        "",
        "1. `primary_predictor.determine_confidence`의 margin을 권장값으로 교체",
        "2. 보고서 §6.2 등급 마진 표 갱신 + 본 결과 인용",
        "3. 보고서 §7.3 \"MdAPE (추정)\" → 실측값으로 정정",
        "",
    ])
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target-coverage", type=float, default=0.80, help="목표 coverage (0~1)")
    args = p.parse_args()

    result = calibrate(target_coverage=args.target_coverage)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "grade_margin_calibration.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("Saved: %s", out_json)

    out_md = OUT_DIR / "grade_margin_calibration_report.md"
    write_report(result, out_md)
    logger.info("Saved: %s", out_md)

    # 콘솔 요약
    logger.info("=" * 70)
    logger.info("캘리브레이션 완료")
    logger.info("=" * 70)
    for g in ["A", "B", "C", "D"]:
        s = result["by_grade"].get(g, {})
        if s.get("n", 0) == 0:
            continue
        logger.info(
            "%s: 현재 m=%.2f → 권장 m=%.3f  (실측 MdAPE %.1f%%, 현재 coverage %.1f%%)",
            g, s["current_m"], s["recommended_m"], s["mdape_pct"], s["current_coverage_pct"],
        )


if __name__ == "__main__":
    main()
