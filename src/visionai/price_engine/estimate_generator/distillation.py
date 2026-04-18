"""Knowledge Distillation: Teacher(추정가 포함) → Student(추정가 없음).

Phase 5 Sprint 3 기획서 참조.
Teacher: Phase 1-2 CatBoost (BASELINE_FEATURES 22개, 추정가 포함)
Student: Phase 3+ CatBoost (HEDONIC_FEATURES 49+개, 추정가 없음)
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.estimate_generator.hedonic_features import (
    CAT_FEATURE_NAMES,
)
from visionai.price_engine.features.track_config import (
    STRICT_FEATURES,
    Track,
)

logger = logging.getLogger(__name__)

_WARMUP_RATIO = 0.20


class DistillationTrainer:
    """Knowledge Distillation trainer.

    Teacher의 soft prediction을 student 학습 타깃에 혼합.
    y_distill = β * y_true + (1-β) * y_teacher
    """

    def __init__(self, beta: float = 0.8) -> None:
        """Args:
            beta: hard target 비율. 1.0이면 pure hard, 0.0이면 pure teacher.
        """
        self.beta = beta
        self._student: CatBoostRegressor | None = None

    def generate_teacher_predictions_oof(
        self,
        df: pd.DataFrame,
        teacher_model_path: str | Path | None = None,
        n_folds: int = 5,
        session_col: str = "회차",
        target_col: str = "낙찰가",
    ) -> np.ndarray:
        """OOF expanding window로 teacher 예측 생성.

        각 fold에서 teacher를 해당 fold의 train 데이터로 재학습한 뒤
        predict 구간에만 예측. warm-up(첫 20%)는 NaN으로 제외.

        **미래 데이터 미사용 보장**: 각 fold의 teacher는 predict 구간 이전
        데이터만으로 학습됨.

        Returns:
            teacher_pred: shape (n,). warm-up 구간은 NaN.
        """
        from visionai.price_engine.models.predictor import (
            BASELINE_FEATURES,
            CAT_FEATURE_INDICES,
            prepare_features,
        )

        result = np.full(len(df), np.nan)

        # 필요 컬럼 확인 — teacher는 추정가가 필요
        df_work = df.copy()
        required = set(BASELINE_FEATURES)
        missing = required - set(df_work.columns)
        if missing:
            logger.warning(
                "Teacher requires %d missing columns: %s. Filling with 0.",
                len(missing), list(missing)[:5],
            )
            for col in missing:
                df_work[col] = 0

        # 타입별 독립 시간축 OOF
        # 각 타입 내에서 session 기준으로 expanding window 적용
        type_col = "타입"
        auction_types = df_work[type_col].unique() if type_col in df_work.columns else ["all"]

        for atype in auction_types:
            if type_col in df_work.columns:
                type_mask = df_work[type_col] == atype
            else:
                type_mask = pd.Series(True, index=df_work.index)

            type_df = df_work.loc[type_mask]
            sessions = sorted(type_df[session_col].unique())
            warmup_idx = int(len(sessions) * _WARMUP_RATIO)
            warmup_end = sessions[warmup_idx - 1] if warmup_idx > 0 else sessions[0]
            post_warmup = [s for s in sessions if s > warmup_end]

            if len(post_warmup) == 0:
                continue

            fold_size = max(1, len(post_warmup) // n_folds)

            for k in range(n_folds):
                pred_start = k * fold_size
                pred_end = (k + 1) * fold_size if k < n_folds - 1 else len(post_warmup)
                predict_sessions = set(post_warmup[pred_start:pred_end])

                if not predict_sessions:
                    continue

                # Train: 동일 타입 내에서 predict 이전 세션만
                max_pred_sess = min(predict_sessions)
                train_mask = type_mask & (df_work[session_col] < max_pred_sess)
                predict_mask = type_mask & df_work[session_col].isin(predict_sessions)

                if train_mask.sum() == 0 or predict_mask.sum() == 0:
                    continue

                # Teacher 재학습 (fold-local, 타입 내)
                train_df = df_work.loc[train_mask]
                y_train = pd.to_numeric(train_df[target_col], errors="coerce")
                valid_train = y_train > 0
                if valid_train.sum() < 10:
                    continue

                try:
                    x_train = prepare_features(train_df.loc[valid_train])
                    y_log = np.log(y_train[valid_train].values)

                    teacher_k = CatBoostRegressor(
                        iterations=500,
                        depth=6,
                        learning_rate=0.05,
                        loss_function="RMSE",
                        cat_features=CAT_FEATURE_INDICES,
                        random_seed=42,
                        verbose=0,
                    )
                    teacher_k.fit(x_train, y_log)

                    x_pred = prepare_features(df_work.loc[predict_mask])
                    pred = teacher_k.predict(x_pred)
                    result[predict_mask.values] = np.exp(pred)
                except Exception:
                    logger.warning("Teacher %s fold %d failed", atype, k)

                logger.info(
                    "Teacher OOF %s fold %d: train=%d, predict=%d",
                    atype, k, valid_train.sum(), predict_mask.sum(),
                )

        return result

    def build_distilled_target(
        self,
        y_true: np.ndarray,
        teacher_pred: np.ndarray,
    ) -> np.ndarray:
        """Distilled target 생성.

        y_distill = β * ln(y_true) + (1-β) * ln(teacher_pred)
        NaN (warm-up, 미낙찰 등)은 ln(y_true)로 대체.
        """
        ln_true = np.where(y_true > 0, np.log(y_true), np.nan)
        ln_teacher = np.where(
            np.isfinite(teacher_pred) & (teacher_pred > 0),
            np.log(teacher_pred),
            np.nan,
        )

        distilled = self.beta * ln_true + (1 - self.beta) * ln_teacher

        # NaN → hard target으로 대체
        nan_mask = ~np.isfinite(distilled)
        distilled[nan_mask] = ln_true[nan_mask]

        return distilled

    def fit_student(
        self,
        train_df: pd.DataFrame,
        y_distilled: np.ndarray,
        valid_df: pd.DataFrame | None = None,
        y_valid: np.ndarray | None = None,
        track: Track = Track.DISTILLED,
        iterations: int = 2000,
        depth: int = 8,
        learning_rate: float = 0.05,
    ) -> CatBoostRegressor:
        """Distilled target으로 Student 학습.

        Student는 STRICT_FEATURES만 사용 (추정가 피처 없음).
        """
        features = STRICT_FEATURES
        cat_features = [
            i for i, f in enumerate(features)
            if f in CAT_FEATURE_NAMES
        ]

        # 피처 준비
        x_train = train_df[features].copy()
        for col in CAT_FEATURE_NAMES:
            if col in x_train.columns:
                x_train[col] = x_train[col].astype(str)

        # NaN 타깃 제외
        valid_mask = np.isfinite(y_distilled)
        x_train = x_train[valid_mask]
        y_train = y_distilled[valid_mask]

        eval_set = None
        if valid_df is not None and y_valid is not None:
            x_val = valid_df[features].copy()
            for col in CAT_FEATURE_NAMES:
                if col in x_val.columns:
                    x_val[col] = x_val[col].astype(str)
            v_mask = np.isfinite(y_valid)
            if v_mask.sum() > 0:
                eval_set = (x_val[v_mask], y_valid[v_mask])

        logger.info(
            "Training %s student: %d samples, %d features",
            track.value, len(x_train), len(features),
        )

        self._student = CatBoostRegressor(
            iterations=iterations,
            depth=depth,
            learning_rate=learning_rate,
            loss_function="RMSE",
            cat_features=cat_features,
            random_seed=42,
            verbose=100,
            early_stopping_rounds=100,
        )
        self._student.fit(x_train, y_train, eval_set=eval_set, use_best_model=True)
        logger.info("Student best iteration: %d", self._student.best_iteration_)

        return self._student
