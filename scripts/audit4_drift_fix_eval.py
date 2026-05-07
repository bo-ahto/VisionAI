"""Track 1 Audit 4 — drift fix variant (23 features) OOF rerun.

Amendment memo: docs/track1_amendment_drift_fix_20260507.md (2026-05-07)
사용자 결정: Option A (drift fix 우선 + baseline 재산출)
코덱스 사전 자문: 옵션 B (별도 script) + 운영 best params 그대로 + 3-split + audit4 prefix

Fix set (제거 9 features):
- 7 severe drift: is_unique / is_edition / has_depth / gallery_city_count /
  has_seoul / has_international / attribution_class
- 2 dead (학습도 0): ho_price_level / medium_price_level

평가 protocol (Phase 0 §1.4):
- GroupKFold cold-start Overall MdAPE
- Source slice: Artsy / Saatchi
- Warm KFold non-regression

운영 best params (`integrated_v3_filtered_tuned_best_params.json`) 그대로 적용.
Tuning 재실행 X (변수 하나만 변경하여 해석 선명, 코덱스 P1).

Usage:
    PYTHONPATH=src python3 scripts/audit4_drift_fix_eval.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold, KFold

# train script helpers 재사용
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_primary_market_v3_filtered import _mdape, _summary, load_data as _raw_load_data


def load_data():
    """입체 필터 적용 — operational anchor baseline 과 동일 28,376 rows."""
    df = _raw_load_data()
    if "is_excluded_for_training" in df.columns:
        n_total = len(df)
        df = df[df["is_excluded_for_training"] == 0].copy()
        logger = logging.getLogger(__name__)
        logger.info(f"입체 필터 적용: {n_total} → {len(df)} rows (-{n_total-len(df)})")
    return df

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "model_test_results"

# ─── Audit 4 features (23) — 코덱스 권고 fix set 적용 ───────────────────
AUDIT4_FEATURES_23 = [
    # 크기 (7) — is_small 유지 (drift X) / is_unique·is_edition·has_depth 제거
    "ho", "ho_power", "ln_ho", "area_cm2", "ln_area", "aspect_ratio", "is_small",
    "support_factor", "ho_x_support",
    # 작가 (6)
    "artist_birth_year", "has_birth_year", "career_stage",
    "ln_followers", "artist_total_works", "for_sale_ratio",
    # 프로필 (1)
    "profile_completeness",
    # 갤러리 (2) — gallery_city_count·has_seoul·has_international 제거 / gallery_tier·gallery_type 유지
    "gallery_tier",
    # currency (1)
    "is_krw",
    # categorical (5) — attribution_class 제거
    "support_type", "medium_category", "gallery_type", "price_currency", "source",
]

AUDIT4_CAT_FEATURES = [
    "support_type", "medium_category", "gallery_type", "price_currency", "source",
]

assert len(AUDIT4_FEATURES_23) == 23, f"Expected 23 features, got {len(AUDIT4_FEATURES_23)}"


def prepare_features_audit4(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Audit 4 23 features — train script prepare_features 와 동일 logic, features list 만 변경."""
    missing = [c for c in AUDIT4_FEATURES_23 if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in dataset: {missing}")

    X = df[AUDIT4_FEATURES_23].copy()
    for col in AUDIT4_CAT_FEATURES:
        X[col] = X[col].astype(str).fillna("unknown").replace(
            {"nan": "unknown", "None": "unknown", "": "unknown"}
        )
    for col in AUDIT4_FEATURES_23:
        if col not in AUDIT4_CAT_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    source = df["source"].astype(str).to_numpy() if "source" in df.columns else np.full(len(df), "unknown")
    return X, y, groups, source


def _cb_pool_audit4(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in AUDIT4_CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _label_encode_xgb_audit4(X_train: pd.DataFrame, X_test: pd.DataFrame):
    from visionai.price_engine._eval_helpers import label_encode_xgb
    return label_encode_xgb(X_train, X_test, categorical_features=AUDIT4_CAT_FEATURES)


def cv_groupkfold_audit4(X, y, groups, source, params: dict, n_splits: int = 3) -> dict:
    """GroupKFold cold-start — 운영 best params 적용."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))

    cb_p = params["catboost"]
    xgb_p = params["xgboost"]

    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info(f"[GroupKFold {fold}/{n_splits}] train={len(tr)} test={len(te)}")
        X_tr, X_te = X.iloc[tr], X.iloc[te]
        y_tr = y[tr]

        cb = CatBoostRegressor(
            iterations=cb_p["iterations"], learning_rate=cb_p["learning_rate"],
            depth=cb_p["depth"], l2_leaf_reg=cb_p["l2_leaf_reg"],
            bagging_temperature=cb_p["bagging_temperature"],
            loss_function="RMSE", verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(_cb_pool_audit4(X_tr, y_tr))
        cb_preds[te] = cb.predict(_cb_pool_audit4(X_te))

        Xtr_e, Xte_e, _ = _label_encode_xgb_audit4(X_tr, X_te)
        dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
        dtest = xgb.DMatrix(Xte_e)
        xgbm = xgb.train(
            params={
                "objective": "reg:squarederror", "eta": xgb_p["eta"], "max_depth": xgb_p["max_depth"],
                "gamma": xgb_p["gamma"], "reg_alpha": xgb_p["reg_alpha"], "reg_lambda": xgb_p["reg_lambda"],
                "subsample": xgb_p["subsample"], "colsample_bytree": xgb_p["colsample_bytree"],
                "verbosity": 0, "seed": 42,
            },
            dtrain=dtrain, num_boost_round=xgb_p["num_boost_round"],
        )
        xgb_preds[te] = xgbm.predict(dtest)

    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds)
    xgb_pred_price = np.exp(xgb_preds)
    ens_price = np.exp((cb_preds + xgb_preds) / 2)
    baseline_pred = np.full_like(y_price, np.median(y_price))

    n = len(y)
    out = {
        "baseline": _summary(y_price, baseline_pred, n),
        "catboost_audit4_drift_fix_v1": _summary(y_price, cb_pred_price, n),
        "xgboost_audit4_drift_fix_v1": _summary(y_price, xgb_pred_price, n),
        "ensemble": _summary(y_price, ens_price, n),
    }
    for src_name in sorted(set(source)):
        mask = source == src_name
        if mask.sum() == 0:
            continue
        out[src_name] = {
            "baseline": _summary(y_price[mask], baseline_pred[mask], int(mask.sum())),
            "catboost_audit4_drift_fix_v1": _summary(y_price[mask], cb_pred_price[mask], int(mask.sum())),
            "xgboost_audit4_drift_fix_v1": _summary(y_price[mask], xgb_pred_price[mask], int(mask.sum())),
            "ensemble": _summary(y_price[mask], ens_price[mask], int(mask.sum())),
        }
    return out, cb_preds, xgb_preds


def cv_kfold_audit4(X, y, groups, source, params: dict, n_splits: int = 3) -> dict:
    """Warm KFold non-regression — 같은 artist 다른 작품, 운영 best params."""
    from visionai.price_engine._eval_helpers import warm_mask as _warm_mask, WARM_MIN_COUNT
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))

    cb_p = params["catboost"]
    xgb_p = params["xgboost"]

    for fold, (tr, te) in enumerate(kf.split(X), 1):
        logger.info(f"[KFold {fold}/{n_splits}] train={len(tr)} test={len(te)}")
        X_tr, X_te = X.iloc[tr], X.iloc[te]
        y_tr = y[tr]

        cb = CatBoostRegressor(
            iterations=cb_p["iterations"], learning_rate=cb_p["learning_rate"],
            depth=cb_p["depth"], l2_leaf_reg=cb_p["l2_leaf_reg"],
            bagging_temperature=cb_p["bagging_temperature"],
            loss_function="RMSE", verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(_cb_pool_audit4(X_tr, y_tr))
        cb_preds[te] = cb.predict(_cb_pool_audit4(X_te))

        Xtr_e, Xte_e, _ = _label_encode_xgb_audit4(X_tr, X_te)
        dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
        dtest = xgb.DMatrix(Xte_e)
        xgbm = xgb.train(
            params={
                "objective": "reg:squarederror", "eta": xgb_p["eta"], "max_depth": xgb_p["max_depth"],
                "gamma": xgb_p["gamma"], "reg_alpha": xgb_p["reg_alpha"], "reg_lambda": xgb_p["reg_lambda"],
                "subsample": xgb_p["subsample"], "colsample_bytree": xgb_p["colsample_bytree"],
                "verbosity": 0, "seed": 42,
            },
            dtrain=dtrain, num_boost_round=xgb_p["num_boost_round"],
        )
        xgb_preds[te] = xgbm.predict(dtest)

    y_price = np.exp(y)
    cb_pred_price = np.exp(cb_preds)
    xgb_pred_price = np.exp(xgb_preds)
    ens_price = np.exp((cb_preds + xgb_preds) / 2)

    n = len(y)
    out = {
        "catboost_audit4_drift_fix_v1": _summary(y_price, cb_pred_price, n),
        "xgboost_audit4_drift_fix_v1": _summary(y_price, xgb_pred_price, n),
        "ensemble": _summary(y_price, ens_price, n),
    }
    # warm slice
    if groups is not None:
        warm = _warm_mask(groups, WARM_MIN_COUNT)
        if warm.sum() > 0:
            out["warm_slice"] = {
                "catboost_audit4_drift_fix_v1": _summary(y_price[warm], cb_pred_price[warm], int(warm.sum())),
                "xgboost_audit4_drift_fix_v1": _summary(y_price[warm], xgb_pred_price[warm], int(warm.sum())),
                "ensemble": _summary(y_price[warm], ens_price[warm], int(warm.sum())),
            }
    if source is not None:
        for src_name in sorted(set(source)):
            mask = source == src_name
            if mask.sum() == 0:
                continue
            out[src_name] = {
                "catboost_audit4_drift_fix_v1": _summary(y_price[mask], cb_pred_price[mask], int(mask.sum())),
                "xgboost_audit4_drift_fix_v1": _summary(y_price[mask], xgb_pred_price[mask], int(mask.sum())),
                "ensemble": _summary(y_price[mask], ens_price[mask], int(mask.sum())),
            }
    return out


def run_variant(variant_name: str, features: list, cat_features: list, params: dict, df) -> dict:
    """단일 variant (32f baseline 또는 23f drift_fix_v1) OOF eval."""
    global AUDIT4_FEATURES_23, AUDIT4_CAT_FEATURES
    saved_feat, saved_cat = AUDIT4_FEATURES_23, AUDIT4_CAT_FEATURES
    AUDIT4_FEATURES_23 = features
    AUDIT4_CAT_FEATURES = cat_features
    try:
        X, y, groups, source = prepare_features_audit4(df)
        logger.info(f"\n[{variant_name}] features={len(features)} / cat={len(cat_features)}")
        gkf_metrics, cb_oof, xgb_oof = cv_groupkfold_audit4(X, y, groups, source, params, n_splits=3)
        kf_metrics = cv_kfold_audit4(X, y, groups, source, params, n_splits=3)
        return {"groupkfold": gkf_metrics, "kfold": kf_metrics, "cb_oof": cb_oof, "xgb_oof": xgb_oof, "groups": groups, "source": source, "y": y}
    finally:
        AUDIT4_FEATURES_23, AUDIT4_CAT_FEATURES = saved_feat, saved_cat


def main() -> None:
    logger.info("=" * 80)
    logger.info("Track 1 Audit 4 — drift_fix_v1 (23f) vs baseline (32f) 3-split OOF 비교")
    logger.info("=" * 80)
    logger.info(f"Splits: GroupKFold/KFold n_splits=3 (코덱스 권고 — 두 variant 정합 비교)")
    logger.info(f"입체 필터 적용 — operational anchor 28,376 rows / 1,551 artists 와 정합")

    # 운영 best params 로드
    best_params_path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    with best_params_path.open(encoding="utf-8") as f:
        params = json.load(f)
    logger.info(f"Best params from: {best_params_path.name}")

    # Data (입체 필터 적용)
    df = load_data()
    logger.info(f"Data: rows={len(df)} / artists={df['artist_slug'].nunique()}")

    # 32f baseline (operational anchor) 3-split 재산출
    BASELINE_32F = [
        "ho", "ho_power", "ln_ho", "area_cm2", "ln_area", "aspect_ratio", "is_small",
        "support_factor", "ho_x_support", "is_unique", "is_edition", "has_depth",
        "artist_birth_year", "has_birth_year", "career_stage",
        "ln_followers", "artist_total_works", "for_sale_ratio",
        "ho_price_level", "medium_price_level", "profile_completeness",
        "gallery_tier", "gallery_city_count", "has_seoul", "has_international",
        "is_krw", "support_type", "medium_category", "attribution_class",
        "gallery_type", "price_currency", "source",
    ]
    BASELINE_CAT = ["support_type", "medium_category", "attribution_class", "gallery_type", "price_currency", "source"]

    logger.info("\n=== Variant 1: baseline 32f (operational anchor, 3-split) ===")
    res_32f = run_variant("baseline_32f", BASELINE_32F, BASELINE_CAT, params, df)

    logger.info("\n=== Variant 2: drift_fix_v1 23f (3-split) ===")
    res_23f = run_variant("drift_fix_v1_23f", AUDIT4_FEATURES_23, AUDIT4_CAT_FEATURES, params, df)

    # 정합 비교용 alias
    gkf_metrics = res_23f["groupkfold"]
    kf_metrics = res_23f["kfold"]
    cb_oof_gkf = res_23f["cb_oof"]
    xgb_oof_gkf = res_23f["xgb_oof"]
    groups = res_23f["groups"]
    source = res_23f["source"]
    y = res_23f["y"]

    # Manifest
    manifest = {
        "variant": "audit4_drift_fix_v1",
        "features_count": len(AUDIT4_FEATURES_23),
        "features": AUDIT4_FEATURES_23,
        "cat_features": AUDIT4_CAT_FEATURES,
        "removed_features": [
            "is_unique", "is_edition", "has_depth", "gallery_city_count",
            "has_seoul", "has_international", "attribution_class",
            "ho_price_level", "medium_price_level"
        ],
        "removal_reason": {
            "drift_severe (7)": ["is_unique", "is_edition", "has_depth", "gallery_city_count",
                                 "has_seoul", "has_international", "attribution_class"],
            "dead (2, 학습도 0)": ["ho_price_level", "medium_price_level"],
        },
        "params_source": "integrated_v3_filtered_tuned_best_params.json (운영 그대로)",
        "split_spec": {"groupkfold_splits": 3, "kfold_splits": 3, "kfold_seed": 42},
        "n_rows": len(df),
        "n_artists": len(set(groups)),
        "framing": "exploratory diagnostic (Phase 0 §1.8) / 운영 spec 변경 단독 trigger X",
    }

    output = {
        "manifest": manifest,
        "baseline_32f_3split": {"groupkfold": res_32f["groupkfold"], "kfold": res_32f["kfold"]},
        "drift_fix_v1_23f_3split": {"groupkfold": gkf_metrics, "kfold": kf_metrics},
    }

    # Print summary - 32f vs 23f 비교
    logger.info("\n" + "=" * 80)
    logger.info("Summary — baseline 32f (3-split) vs drift_fix_v1 23f (3-split)")
    logger.info("=" * 80)

    def _m(d, key):
        if key not in d: return None
        return d[key].get("MdAPE")

    g32 = res_32f["groupkfold"]
    g23 = res_23f["groupkfold"]
    k32 = res_32f["kfold"]
    k23 = res_23f["kfold"]

    logger.info(f"\n{'Metric':<40s} {'32f baseline':>14s} {'23f drift_fix':>14s} {'Δ':>10s}")
    for label, k32_key, k23_key, src in [
        ("GroupKFold Overall CatBoost", "catboost_audit4_drift_fix_v1", "catboost_audit4_drift_fix_v1", None),
        ("GroupKFold Overall XGBoost", "xgboost_audit4_drift_fix_v1", "xgboost_audit4_drift_fix_v1", None),
        ("GroupKFold Overall Ensemble", "ensemble", "ensemble", None),
        ("GroupKFold Artsy Ensemble", "ensemble", "ensemble", "artsy"),
        ("GroupKFold Saatchi Ensemble", "ensemble", "ensemble", "saatchi"),
    ]:
        v32 = (g32[src][k32_key] if src and src in g32 else g32.get(k32_key, {})).get("MdAPE")
        v23 = (g23[src][k23_key] if src and src in g23 else g23.get(k23_key, {})).get("MdAPE")
        if v32 is None or v23 is None: continue
        d = v23 - v32
        logger.info(f"{label:<40s} {v32:>13.2f}% {v23:>13.2f}% {d:>+9.2f}%p")

    if "warm_slice" in k23:
        v32 = k32["warm_slice"]["xgboost_audit4_drift_fix_v1"]["MdAPE"]
        v23 = k23["warm_slice"]["xgboost_audit4_drift_fix_v1"]["MdAPE"]
        logger.info(f"{'KFold Warm slice XGBoost':<40s} {v32:>13.2f}% {v23:>13.2f}% {v23-v32:>+9.2f}%p")

    out_path = OUT_DIR / "audit4_drift_fix_v1_metrics.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out_path.relative_to(ROOT)}")

    # OOF dump (코덱스 P2 — 이후 calibration 재현용)
    oof_path = OUT_DIR / "audit4_drift_fix_v1_oof_groupkfold.parquet"
    oof_df = pd.DataFrame({
        "artist_slug": groups,
        "source": source,
        "y_ln_price": y,
        "cb_pred_ln_price": cb_oof_gkf,
        "xgb_pred_ln_price": xgb_oof_gkf,
    })
    oof_df.to_parquet(oof_path, index=False)
    logger.info(f"Saved OOF: {oof_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
