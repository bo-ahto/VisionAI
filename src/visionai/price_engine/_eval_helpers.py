"""Shared helpers for primary-market price model training & evaluation.

코덱스 하네스 리뷰 P2 (2026-04-30): scripts/v3_*.py 와 학습 스크립트에 중복된
routing / cell calibration / target_market derive / warm mask 로직을 단일 진실원으로
끌어올려 production server 와 진단 스크립트 간 의도치 않은 어긋남을 방지.

Production routing 정합 기준 (`primary_predictor.py:328-371`):
- warm artist (warm_artist_slugs 등재): XGBoost only, no calibration
- cold artist: CatBoost only + cold cell factor (artsy_gallery=1.0 / artsy_online /
  saatchi_online; saatchi_gallery undefined)
- target_market 유도: is_krw==1 → 'gallery', else → 'online'
- cell key: f"{source}_{target_market}"

본 모듈은 학습/진단 단계용 NumPy/pandas 벡터화 helper 를 제공한다. 단일 행 inference
는 `primary_predictor.PricePredictor.predict()` 를 사용한다.
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

WARM_MIN_COUNT = 5
"""warm 라우팅 임계: 학습 fold 내 artist 작품수 ≥ 5 (server warm_artist_slugs 일치)."""

CATEGORICAL_NORMALIZE_MAP = {"nan": "unknown", "None": "unknown", "": "unknown"}
"""학습/서빙 categorical 정규화 (nan/None/empty → 'unknown'). server 와 정합."""


# ─── warm mask ─────────────────────────────────────────────────────────


def warm_mask(groups: np.ndarray, min_count: int = WARM_MIN_COUNT) -> np.ndarray:
    """artist 별 작품수 ≥ min_count 인 행은 True. server warm 라우팅과 정합.

    Args:
        groups: artist_slug array (n,)
        min_count: warm 임계 (default 5)

    Returns:
        boolean mask (n,)
    """
    counts = pd.Series(groups).value_counts()
    warm_set = set(counts[counts >= min_count].index)
    return np.array([g in warm_set for g in groups])


# ─── target_market / cell key ──────────────────────────────────────────


def derive_target_market(is_krw: pd.Series | np.ndarray) -> np.ndarray:
    """is_krw 컬럼에서 target_market 유도. server 정합.

    Args:
        is_krw: 0/1 또는 boolean array. 1=한국 갤러리 (KRW 가격), 0=온라인 마켓.

    Returns:
        np.ndarray of {'gallery', 'online'} dtype=object
    """
    arr = np.asarray(is_krw)
    # int/bool/float 통합 처리
    return np.where(arr.astype(int) == 1, "gallery", "online")


def cell_key(source: str, target_market: str) -> str:
    """단일 행 cell key. server (`primary_predictor.py:371`) 와 동일 format."""
    return f"{source}_{target_market}"


def cell_keys(source: np.ndarray, target_market: np.ndarray) -> np.ndarray:
    """벡터화 cell key. 학습/진단용."""
    return np.array([f"{s}_{t}" for s, t in zip(source, target_market, strict=False)])


def apply_cell_calibration(
    pred_price: np.ndarray,
    cell: np.ndarray,
    factors: dict[str, float],
    *,
    only_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Cell 기반 multiplicative calibration. server `primary_predictor.py:359-373` 정합.

    Args:
        pred_price: KRW 가격 array (n,) - exp 후 가격 단위.
        cell: cell key array (n,) - `cell_keys()` 결과.
        factors: dict of cell -> factor (e.g. {"artsy_online": 0.9426}).
                 cell 미존재 시 factor=1.0 (변경 없음).
        only_mask: optional boolean mask - True 행만 보정 (e.g. cold path 만 적용
                   하고 싶을 때). None 이면 모든 행에 적용.

    Returns:
        보정된 가격 array (n,) - 입력 dtype 보존.
    """
    out = pred_price.copy()
    for k, f in factors.items():
        m = cell == k
        if only_mask is not None:
            m = m & only_mask
        if m.any():
            out[m] = pred_price[m] * f
    return out


# ─── categorical normalization ─────────────────────────────────────────


def normalize_categoricals(
    df: pd.DataFrame, categorical_features: Iterable[str],
) -> pd.DataFrame:
    """categorical 컬럼 정규화 (nan/None/empty → 'unknown'). server `primary_predictor.py:316`
    + 학습 `train_primary_market_v3_filtered.py:120` 와 정합. df 를 in-place 변경하지
    않고 새 DataFrame 반환.
    """
    out = df.copy()
    for col in categorical_features:
        if col not in out.columns:
            continue
        out[col] = (
            out[col]
            .astype(str)
            .fillna("unknown")
            .replace(CATEGORICAL_NORMALIZE_MAP)
        )
    return out


# ─── XGBoost label encoding ─────────────────────────────────────────────


def label_encode_xgb(  # (sklearn 관례: X_train, X_test capitalization)
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    *,
    categorical_features: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    """XGBoost용 categorical label encoding. train fold 만으로 매핑 빌드,
    unseen 카테고리는 sentinel 인덱스(=len(mapping))로 매핑.

    Codex `train_primary_market_v3_filtered.py:140-160` 의 `_label_encode_xgb` 와
    의미 동일 — sentinel index leakage 방지.

    Returns:
        (X_train_encoded, X_test_encoded, label_maps)
        label_maps: dict of column → {value_str → index_int}
    """
    X_train_e = X_train.copy()
    X_test_e = X_test.copy()
    label_maps: dict[str, dict[str, int]] = {}
    for col in categorical_features:
        if col not in X_train_e.columns:
            continue
        train_vals = X_train_e[col].astype(str).unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals))}
        unseen_idx = len(mapping)
        label_maps[col] = mapping
        X_train_e[col] = X_train_e[col].astype(str).map(mapping).astype(float)
        X_test_e[col] = (
            X_test_e[col].astype(str).map(mapping).fillna(unseen_idx).astype(float)
        )
    return X_train_e, X_test_e, label_maps


# ─── OOF artifact loading ──────────────────────────────────────────────


def load_oof_predictions(npz_path) -> dict[str, np.ndarray]:
    """oof_predictions.npz 로드 helper (load_data 와 정합 검증 caller 책임).

    Args:
        npz_path: pathlib.Path 또는 str

    Returns:
        dict of npz key → ndarray (e.g. y_actual_ln, cb_preds_gkf_ln,
        xgb_preds_gkf_ln, groups, source, warm_mask, ...)

    Raises:
        FileNotFoundError: npz 부재
    """
    data = np.load(npz_path, allow_pickle=True)
    return {k: data[k] for k in data.files}


# ─── Production routing 시뮬레이션 (벡터화) ────────────────────────────


def production_routed_predictions(
    *,
    cb_pred_ln_full: np.ndarray,
    xgb_pred_ln_warm: np.ndarray,
    warm_mask_full: np.ndarray,
    source: np.ndarray,
    target_market: np.ndarray,
    cold_factors: dict[str, float],
) -> np.ndarray:
    """Production routing 정합 예측 (KRW 가격 단위).

    routing rule (server `primary_predictor.py:328-373`):
    - warm row → exp(xgb_pred_ln) (no calibration)
    - cold row → exp(cb_pred_ln) × cold_factors[cell] (factor 미정의 시 1.0)

    Args:
        cb_pred_ln_full: (n,) CB OOF ln-price 예측 (전체 행)
        xgb_pred_ln_warm: (warm_count,) XGB OOF ln-price 예측 (warm slice 만)
        warm_mask_full: (n,) boolean — True면 warm
        source: (n,) source array (e.g. 'artsy', 'saatchi')
        target_market: (n,) target_market array (e.g. 'gallery', 'online')
        cold_factors: cell → factor mapping

    Returns:
        (n,) production-routed KRW 가격 array

    Raises:
        ValueError: warm_mask sum != xgb_pred_ln_warm length
    """
    warm_idx = np.where(warm_mask_full)[0]
    if len(warm_idx) != len(xgb_pred_ln_warm):
        raise ValueError(
            f"warm_mask sum ({len(warm_idx)}) != xgb_pred_ln_warm length "
            f"({len(xgb_pred_ln_warm)}). caller 가 warm slice 정합을 보장해야 함."
        )
    # cold path baseline (모든 행에 CB 적용 → cold cells 보정)
    cell = cell_keys(source, target_market)
    pred_price = np.exp(cb_pred_ln_full)
    cold_mask = ~warm_mask_full
    pred_price = apply_cell_calibration(
        pred_price, cell, cold_factors, only_mask=cold_mask,
    )
    # warm 행은 XGB 로 덮어쓰기 (no calibration)
    pred_price[warm_idx] = np.exp(xgb_pred_ln_warm)
    return pred_price
