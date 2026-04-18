"""기존 가격 예측 엔진 v2 — OOF 생성 추정가 기반 재학습.

Phase 1-2의 Target Transform CatBoost를 OOF 추정가로 재학습.
warm-up 구간 처리, 22개 BASELINE_FEATURES 순서 유지.

기획서 4.2절, 개발기획서 Sprint 3 참조.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from visionai.price_engine.estimate_generator.estimate_calibrator import (
    EstimateCalibrator,
)
from visionai.price_engine.estimate_generator.estimate_model import (
    EstimateRegressorModel,
)
from visionai.price_engine.estimate_generator.market_rounder import round_to_market_unit
from visionai.price_engine.models.predictor import (
    BASELINE_FEATURES,
    CAT_FEATURE_INDICES,
)

logger = logging.getLogger(__name__)

# warm-up: 전체 회차의 첫 20%
_WARMUP_RATIO = 0.20


class PriceEngineV2:
    """기존 Target Transform CatBoost의 v2 버전.

    변경: 전문가 추정가 → OOF 생성 추정가로 대체
    유지: 동일한 22개 BASELINE_FEATURES, 동일한 Target Transform 방식
    """

    def __init__(
        self,
        iterations: int = 2000,
        depth: int = 8,
        learning_rate: float = 0.05,
        random_seed: int = 42,
    ) -> None:
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.random_seed = random_seed
        self._model: CatBoostRegressor | None = None

    def generate_oof_estimates(
        self,
        data: pd.DataFrame,
        n_folds: int = 5,
        session_col: str = "회차",
        target_col: str = "ln_estimate_mid_target",
    ) -> pd.DataFrame:
        """Expanding-Window K-Fold OOF 추정가 생성.

        warm-up(첫 20%) 이후 구간에만 OOF 추정가를 생성.
        Train_B에는 warm-up 포함, Predict에는 warm-up 미포함.

        Returns:
            DataFrame with est_low_oof, est_mid_oof, est_high_oof columns.
            warm-up 구간은 NaN.
        """
        result = pd.DataFrame(index=data.index)
        result["est_mid_oof"] = np.nan
        result["est_low_oof"] = np.nan
        result["est_high_oof"] = np.nan

        sessions = sorted(data[session_col].unique())
        warmup_idx = int(len(sessions) * _WARMUP_RATIO)
        warmup_end = sessions[warmup_idx - 1] if warmup_idx > 0 else sessions[0]
        post_warmup = [s for s in sessions if s > warmup_end]

        if len(post_warmup) == 0:
            logger.warning("No post-warmup sessions. Returning all NaN OOF.")
            return result
        if len(post_warmup) < n_folds:
            logger.warning("Not enough post-warmup sessions for %d folds.", n_folds)
            n_folds = max(1, len(post_warmup))

        fold_size = len(post_warmup) // n_folds

        for k in range(n_folds):
            predict_start = k * fold_size
            predict_end = (k + 1) * fold_size if k < n_folds - 1 else len(post_warmup)
            predict_sessions = set(post_warmup[predict_start:predict_end])

            # Calib: predict 직전 구간. fold 1이면 warm-up 구간을 calib으로 사용
            calib_start = max(0, predict_start - fold_size)
            calib_sessions = set(post_warmup[calib_start:predict_start])
            if not calib_sessions:
                # Fold 1: warm-up 구간 자체를 calib으로 사용
                calib_sessions = {s for s in sessions if s <= warmup_end}

            # Train_B: warm-up + predict 이전 구간 (calib 제외)
            train_sessions = {
                s
                for s in sessions
                if (
                    s not in predict_sessions
                    and s not in calib_sessions
                    and s < min(predict_sessions)
                )
            }

            train_mask = data[session_col].isin(train_sessions)
            calib_mask = data[session_col].isin(calib_sessions)
            predict_mask = data[session_col].isin(predict_sessions)

            if train_mask.sum() == 0 or predict_mask.sum() == 0:
                continue

            # Model-B_k 학습
            model_b_k = EstimateRegressorModel(
                iterations=self.iterations,
                depth=self.depth,
                learning_rate=self.learning_rate,
                random_seed=self.random_seed,
            )
            train_df = data.loc[train_mask]
            calib_df = data.loc[calib_mask] if calib_mask.sum() > 0 else None
            model_b_k.fit(train_df, valid_df=calib_df, target_col=target_col)

            # Fold-local 후처리 (Calib_B_k)
            calibrator_k = EstimateCalibrator()
            if calib_df is not None and len(calib_df) > 0:
                y_pred_calib = model_b_k.predict_raw(calib_df)
                y_actual_calib = calib_df[target_col].values
                est_low_c = (
                    pd.to_numeric(calib_df.get("추정가(최저)", 0), errors="coerce")
                    .fillna(0)
                    .values
                )
                est_high_c = (
                    pd.to_numeric(calib_df.get("추정가(최고)", 0), errors="coerce")
                    .fillna(0)
                    .values
                )
                est_mid_c = (est_low_c + est_high_c) / 2
                # NaN/inf 필터링
                calib_valid = (
                    np.isfinite(y_pred_calib)
                    & np.isfinite(y_actual_calib)
                    & np.isfinite(est_mid_c)
                )
                if calib_valid.sum() > 0:
                    calibrator_k.fit(
                        y_pred_calib[calib_valid],
                        y_actual_calib[calib_valid],
                        est_low_c[calib_valid],
                        est_mid_c[calib_valid],
                        est_high_c[calib_valid],
                    )

            # Predict 구간에 OOF 추정가 생성
            predict_df = data.loc[predict_mask]
            y_pred_raw = model_b_k.predict_raw(predict_df)

            if calibrator_k._fitted:
                estimates = calibrator_k.transform(y_pred_raw)
                est_mid = estimates["est_mid"]
                est_low = estimates["est_low"]
                est_high = estimates["est_high"]
            else:
                est_mid = np.exp(y_pred_raw)
                est_low = est_mid * 0.8
                est_high = est_mid * 1.2

            # 라운딩
            est_mid_r = np.array([round_to_market_unit(v) for v in est_mid])
            est_low_r = np.array([round_to_market_unit(v) for v in est_low])
            est_high_r = np.array([round_to_market_unit(v) for v in est_high])

            result.loc[predict_mask, "est_mid_oof"] = est_mid_r
            result.loc[predict_mask, "est_low_oof"] = est_low_r
            result.loc[predict_mask, "est_high_oof"] = est_high_r

            logger.info(
                "Fold %d: predict=%d, train=%d, calib=%d",
                k,
                predict_mask.sum(),
                train_mask.sum(),
                calib_mask.sum(),
            )

        return result

    def _prepare_v2_features(
        self,
        df: pd.DataFrame,
        oof_estimates: pd.DataFrame,
    ) -> pd.DataFrame:
        """v2 피처 구성: 22개 BASELINE_FEATURES 순서 유지, 추정가 4개 OOF 치환."""
        out = df.copy()
        est_mid = oof_estimates["est_mid_oof"].values
        est_low = oof_estimates["est_low_oof"].values
        est_high = oof_estimates["est_high_oof"].values

        out["estimate_mid"] = est_mid
        with np.errstate(divide="ignore", invalid="ignore"):
            out["ln_estimate_mid"] = np.where(est_mid > 0, np.log(est_mid), np.nan)
            out["estimate_range"] = est_high - est_low
            ratio = est_high / est_low
            ratio[est_low == 0] = np.nan
            out["estimate_ratio"] = ratio

        out["artist_sell_rate"] = 0

        return out[BASELINE_FEATURES]

    def fit(
        self,
        train_df: pd.DataFrame,
        oof_estimates: pd.DataFrame,
        valid_df: pd.DataFrame | None = None,
        valid_oof: pd.DataFrame | None = None,
    ) -> None:
        """OOF 추정가 기반 v2 학습.

        warm-up 구간(OOF NaN)은 자동 제외.
        """
        # warm-up 제외: OOF 추정가가 있는 행만
        has_oof = oof_estimates["est_mid_oof"].notna()
        if has_oof.sum() == 0:
            logger.warning("No OOF estimates available. v2 engine cannot be trained.")
            return
        train_df_v2 = train_df.loc[has_oof]
        oof_v2 = oof_estimates.loc[has_oof]

        x_train = self._prepare_v2_features(train_df_v2, oof_v2)
        est_mid = oof_v2["est_mid_oof"].values
        price = pd.to_numeric(train_df_v2["낙찰가"], errors="coerce").values

        # 타깃: ln(낙찰가 / est_mid_oof)
        with np.errstate(divide="ignore", invalid="ignore"):
            y_train = np.log(price / est_mid)
        valid_mask = np.isfinite(y_train)
        x_train = x_train[valid_mask]
        y_train = y_train[valid_mask]

        eval_set = None
        if valid_df is not None and valid_oof is not None:
            has_oof_v = valid_oof["est_mid_oof"].notna()
            if has_oof_v.sum() > 0:
                x_valid = self._prepare_v2_features(
                    valid_df.loc[has_oof_v], valid_oof.loc[has_oof_v]
                )
                price_v = pd.to_numeric(valid_df.loc[has_oof_v, "낙찰가"], errors="coerce").values
                est_mid_v = valid_oof.loc[has_oof_v, "est_mid_oof"].values
                y_valid = np.log(price_v / est_mid_v)
                v_mask = np.isfinite(y_valid)
                eval_set = (x_valid[v_mask], y_valid[v_mask])

        logger.info("Training v2 engine: train=%d (warm-up excluded)", len(x_train))

        # CatBoost 범주형을 str로 변환
        for col in [
            "artist_clean",
            "medium_category",
            "support_category",
            "타입",
            "is_3d",
            "is_untitled",
        ]:
            if col in x_train.columns:
                x_train[col] = x_train[col].astype(str)
        if eval_set is not None:
            x_v, y_v = eval_set
            for col in [
                "artist_clean",
                "medium_category",
                "support_category",
                "타입",
                "is_3d",
                "is_untitled",
            ]:
                if col in x_v.columns:
                    x_v[col] = x_v[col].astype(str)
            eval_set = (x_v, y_v)

        self._model = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            loss_function="RMSE",
            cat_features=CAT_FEATURE_INDICES,
            random_seed=self.random_seed,
            verbose=100,
            early_stopping_rounds=100,
        )
        self._model.fit(x_train, y_train, eval_set=eval_set, use_best_model=True)
        logger.info("v2 engine best iteration: %d", self._model.best_iteration_)

    def predict(
        self,
        df: pd.DataFrame,
        est_mid: np.ndarray,
        est_low: np.ndarray | None = None,
        est_high: np.ndarray | None = None,
    ) -> np.ndarray:
        """v2 추론: est_mid x exp(model.predict(X)).

        학습/서빙 입력 분포 일치를 위해 est_low/est_high도 전달해야 한다.
        estimate_range = est_high - est_low, estimate_ratio = est_high / est_low.
        """
        if self._model is None:
            msg = "v2 engine not fitted."
            raise RuntimeError(msg)

        if est_low is None:
            est_low = est_mid * 0.8
        if est_high is None:
            est_high = est_mid * 1.2

        out = df.copy()
        out["estimate_mid"] = est_mid
        with np.errstate(divide="ignore", invalid="ignore"):
            out["ln_estimate_mid"] = np.where(est_mid > 0, np.log(est_mid), np.nan)
            out["estimate_range"] = est_high - est_low
            ratio = est_high / est_low
            ratio[est_low == 0] = np.nan
            out["estimate_ratio"] = ratio
        out["artist_sell_rate"] = 0
        # BASELINE_FEATURES에 있지만 df에 없는 컬럼 기본값 채우기
        for col in BASELINE_FEATURES:
            if col not in out.columns:
                out[col] = 0
        x_feat = out[BASELINE_FEATURES].copy()
        for col in [
            "artist_clean",
            "medium_category",
            "support_category",
            "타입",
            "is_3d",
            "is_untitled",
        ]:
            if col in x_feat.columns:
                x_feat[col] = x_feat[col].astype(str)

        y_transform = self._model.predict(x_feat)
        return est_mid * np.exp(y_transform)
