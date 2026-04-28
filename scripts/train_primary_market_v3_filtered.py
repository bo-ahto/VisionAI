"""1차 시장(A 모델) 재학습 — v3 사양 + 입체 필터 적용.

배경 (Codex Provenance Audit §5):
- 배포 중인 v3 모델(`integrated_v3_*`)을 생성한 학습 스크립트가 repo에 없음.
- 본 스크립트는 v3 메트릭(`model_test_results/integrated_v3_metrics.json`) 기준으로
  같은 데이터·피처·모델 조합을 재현하면서 `is_excluded_for_training=1` 입체 후보를
  학습에서 제외한다.

산출물:
- model_test_results/integrated_v3_filtered_catboost.cbm
- model_test_results/integrated_v3_filtered_xgboost.json
- model_test_results/integrated_v3_filtered_metrics.json

비교 대상: integrated_v3_metrics.json (v3 baseline)

Usage:
    PYTHONPATH=src python3 scripts/train_primary_market_v3_filtered.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold, KFold

from visionai.price_engine.api.primary_predictor import CB_FEATURES, CAT_FEATURES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"

# ─── 메트릭 함수 ────────────────────────────────────────────────────
def _mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Median Absolute Percentage Error (price 기준, % 단위)."""
    return float(np.median(np.abs(y_true - y_pred) / np.abs(y_true)) * 100)


def _within_pct(y_true: np.ndarray, y_pred: np.ndarray, threshold: float) -> float:
    """예측값이 실제값의 ±threshold% 안에 들어오는 비율 (%)."""
    return float(np.mean(np.abs(y_true - y_pred) / np.abs(y_true) <= threshold) * 100)


def _ratio(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """평균 예측/실제 비율."""
    return float(np.mean(y_pred / y_true))


def _summary(y_true: np.ndarray, y_pred: np.ndarray, n: int) -> dict:
    """v3 메트릭 형식과 동일하게 요약 (price 단위)."""
    return {
        "n": n,
        "MdAPE": round(_mdape(y_true, y_pred), 1),
        "W30": round(_within_pct(y_true, y_pred, 0.30), 1),
        "W50": round(_within_pct(y_true, y_pred, 0.50), 1),
        "ratio": round(_ratio(y_true, y_pred), 2),
    }


# ─── 데이터 로드 ────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    """Artsy + Saatchi 통합 dataset 로드."""
    artsy_path = DATA / "primary_market_dataset.parquet"
    saatchi_path = DATA / "saatchi_cleaned.parquet"

    artsy = pd.read_parquet(artsy_path)
    saatchi = pd.read_parquet(saatchi_path)

    # source 컬럼 보장 (CB_FEATURES에 포함)
    if "source" not in artsy.columns:
        artsy["source"] = "artsy"
    if "source" not in saatchi.columns:
        saatchi["source"] = "saatchi"

    # 누락 가능 컬럼 보장 (CB_FEATURES 호환)
    for col in ("ho_price_level", "medium_price_level", "profile_completeness", "ln_area"):
        for df in (artsy, saatchi):
            if col not in df.columns:
                if col == "ln_area":
                    df[col] = np.log(df["area_cm2"].clip(lower=1))
                else:
                    df[col] = 0.0
    # has_birth_year 플래그
    for df in (artsy, saatchi):
        if "has_birth_year" not in df.columns:
            df["has_birth_year"] = df["artist_birth_year"].notna().astype(int)
    # support_factor / ho_x_support 보장
    for df in (artsy, saatchi):
        if "support_factor" not in df.columns:
            from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
            df["support_factor"] = df["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
        if "ho_x_support" not in df.columns:
            df["ho_x_support"] = df["ho"] * df["support_factor"]

    # 공통 컬럼만 유지
    common = [c for c in artsy.columns if c in saatchi.columns]
    df = pd.concat([artsy[common], saatchi[common]], ignore_index=True)

    logger.info("Loaded %d rows (Artsy %d + Saatchi %d)", len(df), len(artsy), len(saatchi))
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """피처/타겟/group 분리."""
    # 누락된 피처 확인
    missing = [c for c in CB_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in dataset: {missing}")

    X = df[CB_FEATURES].copy()
    # 범주형: 결측치 → 'unknown' 문자열
    for col in CAT_FEATURES:
        X[col] = X[col].astype(str).fillna("unknown").replace({"nan": "unknown", "None": "unknown"})
    # 수치형: NaN → 0 (artist_birth_year 같은 컬럼은 has_birth_year 플래그가 보완)
    for col in CB_FEATURES:
        if col not in CAT_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    return X, y, groups


# ─── 학습 + CV ──────────────────────────────────────────────────────
def _cb_pool(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    """CatBoost Pool with categorical indices and optional label."""
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _label_encode_xgb(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    """XGBoost용 categorical label encoding.

    Codex review: train fold만으로 매핑 빌드. test fold의 unseen 카테고리는
    sentinel 인덱스(=len(mapping))로 매핑하여 leakage 방지.
    """
    X_train_e = X_train.copy()
    X_test_e = X_test.copy()
    label_maps: dict[str, dict[str, int]] = {}
    for col in CAT_FEATURES:
        train_vals = X_train_e[col].unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals))}
        unseen_idx = len(mapping)  # train에 없는 test 값은 동일 sentinel로
        label_maps[col] = mapping
        X_train_e[col] = X_train_e[col].map(mapping).astype(float)
        X_test_e[col] = X_test_e[col].map(mapping).fillna(unseen_idx).astype(float)
    return X_train_e, X_test_e, label_maps


def cv_groupkfold(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray, n_splits: int = 5,
) -> dict:
    """GroupKFold (cold start) — artist 단위 분할."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))

    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[GroupKFold %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        X_tr, X_te = X.iloc[tr], X.iloc[te]
        y_tr, y_te = y[tr], y[te]

        # CatBoost
        cb = CatBoostRegressor(
            iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
            verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(_cb_pool(X_tr, y_tr))  # Codex P1: leakage 방지
        cb_preds[te] = cb.predict(_cb_pool(X_te))

        # XGBoost
        Xtr_e, Xte_e, _ = _label_encode_xgb(X_tr, X_te)
        dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
        dtest = xgb.DMatrix(Xte_e, label=y_te)
        xgbm = xgb.train(
            params={
                "objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 0,
                "seed": 42,
            },
            dtrain=dtrain, num_boost_round=1000,
        )
        xgb_preds[te] = xgbm.predict(dtest)

    # ln_price → price
    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds)
    xgb_pred_price = np.exp(xgb_preds)
    ens_price = np.exp((cb_preds + xgb_preds) / 2)

    # baseline: 전체 학습 데이터의 중앙값을 모든 예측으로
    baseline_pred = np.full_like(y_price, np.median(y_price))

    n = len(y)
    out: dict = {
        "baseline": _summary(y_price, baseline_pred, n),
        "catboost_v3_filtered": _summary(y_price, cb_pred_price, n),
        "xgboost_v3_filtered": _summary(y_price, xgb_pred_price, n),
        "ensemble": _summary(y_price, ens_price, n),
    }
    # source별 분리
    for src_name in sorted(set(source)):
        mask = source == src_name
        if mask.sum() == 0:
            continue
        out[src_name] = {
            "baseline": _summary(y_price[mask], baseline_pred[mask], int(mask.sum())),
            "catboost_v3_filtered": _summary(y_price[mask], cb_pred_price[mask], int(mask.sum())),
            "xgboost_v3_filtered": _summary(y_price[mask], xgb_pred_price[mask], int(mask.sum())),
            "ensemble": _summary(y_price[mask], ens_price[mask], int(mask.sum())),
        }
    return out


WARM_MIN_COUNT = 5


def _warm_mask(groups: np.ndarray) -> np.ndarray:
    """artist별 작품 수 >= WARM_MIN_COUNT 인 행만 True (서빙 라우팅 일치)."""
    counts = pd.Series(groups).value_counts()
    warm_set = set(counts[counts >= WARM_MIN_COUNT].index)
    return np.array([g in warm_set for g in groups])


def cv_kfold(
    X: pd.DataFrame, y: np.ndarray,
    groups: np.ndarray | None = None,
    source: np.ndarray | None = None,
    n_splits: int = 5,
) -> dict:
    """KFold (warm — 같은 작가의 다른 작품 학습).

    Codex review: warm slice (artist_count>=5)와 by-source 분리 메트릭 추가.
    서빙 라우팅(XGBoost on training_count>=5)과 일치한 평가.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))

    for fold, (tr, te) in enumerate(kf.split(X), 1):
        logger.info("[KFold %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        X_tr, X_te = X.iloc[tr], X.iloc[te]
        y_tr, y_te = y[tr], y[te]

        cb = CatBoostRegressor(
            iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
            verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(_cb_pool(X_tr, y_tr))  # Codex P1: leakage 방지
        cb_preds[te] = cb.predict(_cb_pool(X_te))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X_tr, X_te)
        dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
        dtest = xgb.DMatrix(Xte_e, label=y_te)
        xgbm = xgb.train(
            params={
                "objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 0,
                "seed": 42,
            },
            dtrain=dtrain, num_boost_round=1000,
        )
        xgb_preds[te] = xgbm.predict(dtest)

    y_price = np.exp(y)
    cb_pred = np.exp(cb_preds)
    xgb_pred = np.exp(xgb_preds)
    ens = np.exp((cb_preds + xgb_preds) / 2)
    n = len(y)
    out = {
        "catboost_v3_filtered": _summary(y_price, cb_pred, n),
        "xgboost_v3_filtered": _summary(y_price, xgb_pred, n),
        "ensemble": _summary(y_price, ens, n),
    }

    # by-source split
    if source is not None:
        for src_name in sorted(set(source)):
            mask = source == src_name
            if mask.sum() == 0:
                continue
            out[src_name] = {
                "catboost_v3_filtered": _summary(y_price[mask], cb_pred[mask], int(mask.sum())),
                "xgboost_v3_filtered": _summary(y_price[mask], xgb_pred[mask], int(mask.sum())),
                "ensemble": _summary(y_price[mask], ens[mask], int(mask.sum())),
            }

    # 위 warm subset은 'XGB trained on full data, evaluated on warm subset' — 서빙과 다름.
    # 서빙 라우팅 일치 평가는 cv_kfold_warm()에서 별도 수행 (XGB warm-only 학습).
    return out


def cv_kfold_warm(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    source: np.ndarray | None = None, n_splits: int = 5,
) -> dict:
    """warm slice (artist_count>=5) 만으로 XGBoost CV 학습/평가.

    서빙 라우팅(XGBoost on artist_count>=5)과 완전 정렬. tune script와 동일 정책.
    """
    wmask = _warm_mask(groups)
    if wmask.sum() == 0:
        return {}
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    src_warm = source[wmask] if source is not None else None
    n_warm = len(y_warm)

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    xgb_preds = np.zeros(n_warm)
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[KFold-warm %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y_warm[tr])
        dtest = xgb.DMatrix(Xte_e, label=y_warm[te])
        xgbm = xgb.train(
            params={
                "objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 0,
                "seed": 42,
            },
            dtrain=dtrain, num_boost_round=1000,
        )
        xgb_preds[te] = xgbm.predict(dtest)

    y_price = np.exp(y_warm)
    xgb_pred = np.exp(xgb_preds)
    out = {
        "n": n_warm,
        "n_artists": int(pd.Series(groups[wmask]).nunique()),
        "xgboost_v3_filtered": _summary(y_price, xgb_pred, n_warm),
        "_note": "Trained and evaluated on warm slice only (artist_count>=5) — 서빙 라우팅 일치",
    }
    if src_warm is not None:
        for src_name in sorted(set(src_warm)):
            smask = src_warm == src_name
            if smask.sum() == 0:
                continue
            out[src_name] = {
                "xgboost_v3_filtered": _summary(y_price[smask], xgb_pred[smask], int(smask.sum())),
            }
    return out


def train_final_models(
    X: pd.DataFrame, y: np.ndarray,
    X_warm: pd.DataFrame | None = None, y_warm: np.ndarray | None = None,
) -> tuple[CatBoostRegressor, xgb.Booster, dict]:
    """최종 모델 학습.

    서빙 라우팅 일치 (tune script와 동일 정책):
    - CatBoost: 전체 데이터 (cold start route)
    - XGBoost: warm slice 데이터 (artist_count >= 5, warm route)
    """
    cb = CatBoostRegressor(
        iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
        verbose=100, random_seed=42, allow_writing_files=False,
    )
    cb.fit(_cb_pool(X, y))

    # XGBoost는 warm slice로 학습 (없으면 전체 fallback)
    X_xgb = X_warm if X_warm is not None else X
    y_xgb = y_warm if y_warm is not None else y
    Xe, _, label_maps = _label_encode_xgb(X_xgb, X_xgb.iloc[:1])
    dtrain = xgb.DMatrix(Xe, label=y_xgb)
    xgbm = xgb.train(
        params={
            "objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 1,
            "seed": 42,
        },
        dtrain=dtrain, num_boost_round=1000,
    )
    return cb, xgbm, label_maps


# ─── main ────────────────────────────────────────────────────────────
def main() -> None:
    logger.info("=" * 60)
    logger.info("1차 시장 v3-filtered 재학습 시작")
    logger.info("=" * 60)

    df = load_data()
    n_total = len(df)
    n_excluded = int((df["is_excluded_for_training"] == 1).sum())
    logger.info("전체: %d, 입체 제외 후보: %d (%.1f%%)", n_total, n_excluded, 100 * n_excluded / n_total)

    df_train = df[df["is_excluded_for_training"] == 0].copy()
    logger.info("학습 데이터: %d (제외 후)", len(df_train))

    X, y, groups = prepare_features(df_train)
    source = df_train["source"].astype(str).to_numpy()
    artists = pd.unique(groups)
    logger.info("Features: %d, target ln_price range %.2f~%.2f, artists: %d",
                len(CB_FEATURES), y.min(), y.max(), len(artists))

    logger.info("--- GroupKFold CV (Cold Start, 새 작가) ---")
    gkf_metrics = cv_groupkfold(X, y, groups, source)

    logger.info("--- KFold CV (full data — CatBoost 학습/평가용) ---")
    kf_metrics = cv_kfold(X, y, groups=groups, source=source)

    logger.info("--- KFold CV (warm slice — XGBoost 서빙 라우팅 일치) ---")
    kf_warm_metrics = cv_kfold_warm(X, y, groups, source=source)
    kf_metrics["warm_slice"] = kf_warm_metrics  # 서빙 라우팅과 일치한 metric 덮어쓰기

    logger.info("--- 전체 데이터로 최종 모델 학습 ---")
    # 서빙 라우팅 일치: XGBoost는 warm slice로 학습 (tune script와 동일)
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    cb_final, xgb_final, label_maps = train_final_models(X, y, X_warm, y_warm)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cb_path = OUT_DIR / "integrated_v3_filtered_catboost.cbm"
    xgb_path = OUT_DIR / "integrated_v3_filtered_xgboost.json"
    label_maps_path = OUT_DIR / "integrated_v3_filtered_xgboost_label_maps.json"
    metrics_path = OUT_DIR / "integrated_v3_filtered_metrics.json"
    cb_final.save_model(str(cb_path))
    xgb_final.save_model(str(xgb_path))
    logger.info("CatBoost saved: %s", cb_path)
    logger.info("XGBoost saved: %s", xgb_path)
    # Codex review: XGBoost label_maps를 별도 아티팩트로 저장 (PrimaryPredictor 호환)
    with label_maps_path.open("w", encoding="utf-8") as f:
        json.dump(label_maps, f, ensure_ascii=False, indent=2)
    logger.info("XGBoost label maps saved: %s", label_maps_path)
    # Codex 5차 P1: 학습 시 warm artist slug list 저장 → 서빙 라우팅이 동일 기준 사용
    warm_artists_set = sorted(set(groups[wmask].tolist()))
    warm_artists_path = OUT_DIR / "integrated_v3_filtered_warm_artists.json"
    with warm_artists_path.open("w", encoding="utf-8") as f:
        json.dump({
            "warm_artist_slugs": warm_artists_set,
            "n_artists": len(warm_artists_set),
            "n_warm_works": int(wmask.sum()),
            "min_count": int(WARM_MIN_COUNT),
            "note": "학습 시 artist_count>=5 (filtered) 작가 목록. 서빙 라우팅 시 lookup",
        }, f, ensure_ascii=False, indent=2)
    logger.info("Warm artists saved: %d artists", len(warm_artists_set))

    metrics_doc = {
        "model": "integrated_v3_filtered",
        "data": f"{len(df_train)} = Artsy {(source=='artsy').sum()} + Saatchi {(source=='saatchi').sum()} (filtered from {n_total}, excluded={n_excluded})",
        "features": len(CB_FEATURES),
        "artists": int(len(artists)),
        "groupkfold": gkf_metrics,
        "kfold": kf_metrics,
        "label_maps": label_maps,
    }
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics_doc, f, ensure_ascii=False, indent=2)
    logger.info("Metrics saved: %s", metrics_path)

    logger.info("=" * 60)
    logger.info("학습 완료")
    logger.info("=" * 60)
    logger.info("GroupKFold ensemble: MdAPE=%.1f%%, W30=%.1f%%, W50=%.1f%%",
                gkf_metrics["ensemble"]["MdAPE"], gkf_metrics["ensemble"]["W30"], gkf_metrics["ensemble"]["W50"])
    logger.info("GroupKFold CatBoost (cold serving):  All=%.1f / Artsy=%.1f / Saatchi=%.1f",
                gkf_metrics["catboost_v3_filtered"]["MdAPE"],
                gkf_metrics.get("artsy", {}).get("catboost_v3_filtered", {}).get("MdAPE", float('nan')),
                gkf_metrics.get("saatchi", {}).get("catboost_v3_filtered", {}).get("MdAPE", float('nan')))
    if "warm_slice" in kf_metrics and kf_metrics["warm_slice"]:
        ws = kf_metrics["warm_slice"]
        logger.info("KFold warm-slice XGBoost (warm serving, warm-only train): All=%.1f / Artsy=%.1f / Saatchi=%.1f (n=%d, artists=%d)",
                    ws["xgboost_v3_filtered"]["MdAPE"],
                    ws.get("artsy", {}).get("xgboost_v3_filtered", {}).get("MdAPE", float('nan')),
                    ws.get("saatchi", {}).get("xgboost_v3_filtered", {}).get("MdAPE", float('nan')),
                    ws["n"], ws["n_artists"])
    logger.info("KFold ensemble:      MdAPE=%.1f%%, W30=%.1f%%, W50=%.1f%%",
                kf_metrics["ensemble"]["MdAPE"], kf_metrics["ensemble"]["W30"], kf_metrics["ensemble"]["W50"])


if __name__ == "__main__":
    main()
