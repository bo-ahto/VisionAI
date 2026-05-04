"""Ablation: gallery_tier_v4 피처 추가 시 MdAPE 변화 측정.

코덱스 자문 반영:
- baseline: 같은 filtered split (7,289건)에서 재현 — integrated_v3_metrics.json (7,640건) 직접 비교 X
- 게이트: 분리도 통계가 아닌 OOF MdAPE 개선 (incremental gain)
- 기존 gallery_tier 피처와의 incremental gain 측정

빠른 검증용 — CatBoost 5-fold KFold (warm 포함). XGBoost는 본 retraining에서.

Usage:
    PYTHONPATH=src python3 scripts/ablation_gallery_tier_v4.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import GroupKFold, KFold

from visionai.price_engine.api.primary_predictor import CAT_FEATURES, CB_FEATURES_BASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


def _mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.median(np.abs(y_true - y_pred) / np.abs(y_true)) * 100)


def _within_pct(y_true: np.ndarray, y_pred: np.ndarray, t: float) -> float:
    return float(np.mean(np.abs(y_true - y_pred) / np.abs(y_true) <= t) * 100)


def _summary(y_true: np.ndarray, y_pred: np.ndarray, n: int) -> dict:
    return {
        "n": n,
        "MdAPE": round(_mdape(y_true, y_pred), 2),
        "W30": round(_within_pct(y_true, y_pred, 0.30), 2),
        "W50": round(_within_pct(y_true, y_pred, 0.50), 2),
    }


def _normalize(s) -> str:
    import re
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def attach_gallery_tier_v4(df: pd.DataFrame) -> pd.DataFrame:
    """df 의 gallery_name → gallery_tier_v4 컬럼 attach.

    분석 스크립트 (analyze_gallery_tier_coverage.py) 의 매핑 로직 재사용:
    - alias_map (data/gallery_alias_map.csv): 영문→한글 43건
    - tier_lookup (data/art_gallery_tier_list_v4.csv): 한글→tier 118건
    - 미매칭 → "Tier E"
    - Saatchi → "Tier E" (온라인 플랫폼)
    """
    alias_df = pd.read_csv(DATA / "gallery_alias_map.csv")
    alias = {_normalize(r["영문명"]): _normalize(r["한글명"]) for _, r in alias_df.iterrows()}
    v4 = pd.read_csv(DATA / "art_gallery_tier_list_v4.csv").dropna(subset=["명칭"])
    tier_lookup = {_normalize(r["명칭"]): str(r["티어"]).strip() for _, r in v4.iterrows()}

    def lookup(row):
        if row.get("source") == "saatchi":
            return "Tier E"
        n = _normalize(row.get("gallery_name"))
        if not n:
            return "Tier E"
        if n == "Saatchi Art":
            return "Tier E"
        kor = alias.get(n, n)
        return tier_lookup.get(_normalize(kor), "Tier E")

    df = df.copy()
    df["gallery_tier_v4"] = df.apply(lookup, axis=1)
    return df


def load_data() -> pd.DataFrame:
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")
    if "source" not in artsy.columns:
        artsy["source"] = "artsy"
    if "source" not in saatchi.columns:
        saatchi["source"] = "saatchi"

    for col in ("ho_price_level", "medium_price_level", "profile_completeness", "ln_area"):
        for df in (artsy, saatchi):
            if col not in df.columns:
                if col == "ln_area":
                    df[col] = np.log(df["area_cm2"].clip(lower=1))
                else:
                    df[col] = 0.0
    for df in (artsy, saatchi):
        if "has_birth_year" not in df.columns:
            df["has_birth_year"] = df["artist_birth_year"].notna().astype(int)
        if "support_factor" not in df.columns:
            from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
            df["support_factor"] = df["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
        if "ho_x_support" not in df.columns:
            df["ho_x_support"] = df["ho"] * df["support_factor"]

    common = [c for c in artsy.columns if c in saatchi.columns]
    df = pd.concat([artsy[common], saatchi[common]], ignore_index=True)
    df = df[df["is_excluded_for_training"] == 0].copy()
    return df


def prepare_X(df: pd.DataFrame, features: list[str], cat_features: list[str]) -> pd.DataFrame:
    X = df[features].copy()
    for col in cat_features:
        if col in X.columns:
            X[col] = X[col].astype(str).fillna("unknown").replace(
                {"nan": "unknown", "None": "unknown", "": "unknown"}
            )
    for col in features:
        if col not in cat_features:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)
    return X


def cb_cv(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cat_features: list[str], cv_type: str = "kfold", n_splits: int = 5,
) -> tuple[dict, np.ndarray]:
    """CatBoost CV — kfold (warm, full data) or groupkfold (cold start).

    Returns: (metrics_dict, oof_predictions)
    """
    if cv_type == "groupkfold":
        splitter = GroupKFold(n_splits=n_splits)
        splits = list(splitter.split(X, y, groups))
    else:
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        splits = list(splitter.split(X))

    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
    oof = np.zeros(len(y))

    for fold, (tr, te) in enumerate(splits, 1):
        cb = CatBoostRegressor(
            iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
            verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(Pool(X.iloc[tr], label=y[tr], cat_features=cat_idx))
        oof[te] = cb.predict(Pool(X.iloc[te], cat_features=cat_idx))
        logger.info(f"  [{cv_type} {fold}/{n_splits}] train={len(tr)} test={len(te)}")

    y_price = np.exp(y)
    pred_price = np.exp(oof)

    out = {"overall": _summary(y_price, pred_price, len(y))}
    for src in sorted(set(source)):
        m = source == src
        if m.sum() == 0:
            continue
        out[src] = _summary(y_price[m], pred_price[m], int(m.sum()))
    return out, oof


def feature_importance(X: pd.DataFrame, y: np.ndarray, cat_features: list[str]) -> pd.DataFrame:
    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
    cb = CatBoostRegressor(
        iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
        verbose=0, random_seed=42, allow_writing_files=False,
    )
    cb.fit(Pool(X, label=y, cat_features=cat_idx))
    imp = cb.get_feature_importance(prettified=True)
    return imp


def main() -> None:
    logger.info("=" * 60)
    logger.info("Ablation: gallery_tier_v4 incremental gain")
    logger.info("=" * 60)

    df = load_data()
    df = attach_gallery_tier_v4(df)
    logger.info(f"학습 데이터 {len(df)}건 (Artsy {(df['source']=='artsy').sum()} + Saatchi {(df['source']=='saatchi').sum()})")
    logger.info(f"gallery_tier_v4 분포: {df['gallery_tier_v4'].value_counts().to_dict()}")

    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    source = df["source"].astype(str).to_numpy()

    # ─── Baseline (CB_FEATURES_BASE = 32, 기존 gallery_tier 포함) ─────────
    logger.info("\n--- Baseline: 32 features (기존 gallery_tier만) ---")
    X_base = prepare_X(df, CB_FEATURES_BASE, CAT_FEATURES)

    # ─── Treated (CB_FEATURES_BASE + gallery_tier_v4 = 33) ────────────────
    feats_v4 = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats_v4 = CAT_FEATURES + ["gallery_tier_v4"]
    logger.info("\n--- Treated: 33 features (+ gallery_tier_v4) ---")
    X_v4 = prepare_X(df, feats_v4, cats_v4)

    # KFold (warm/full data CV — 서빙 라우팅 일치)
    logger.info("\n=== KFold 5-fold (warm-style) ===")
    logger.info("[Baseline]")
    base_kf, base_oof = cb_cv(X_base, y, groups, source, CAT_FEATURES, cv_type="kfold")
    logger.info("[+ gallery_tier_v4]")
    v4_kf, v4_oof = cb_cv(X_v4, y, groups, source, cats_v4, cv_type="kfold")

    # GroupKFold (cold start CV)
    logger.info("\n=== GroupKFold 5-fold (cold start) ===")
    logger.info("[Baseline]")
    base_gkf, _ = cb_cv(X_base, y, groups, source, CAT_FEATURES, cv_type="groupkfold")
    logger.info("[+ gallery_tier_v4]")
    v4_gkf, _ = cb_cv(X_v4, y, groups, source, cats_v4, cv_type="groupkfold")

    # Feature importance (full data)
    logger.info("\n=== Feature importance (full data, with gallery_tier_v4) ===")
    imp = feature_importance(X_v4, y, cats_v4)
    imp_top = imp.head(10).to_dict("records")
    v4_rank = imp[imp["Feature Id"] == "gallery_tier_v4"].index.tolist()
    v4_imp = imp[imp["Feature Id"] == "gallery_tier_v4"]["Importances"].iloc[0] if v4_rank else None
    gallery_tier_imp = imp[imp["Feature Id"] == "gallery_tier"]["Importances"].iloc[0] if "gallery_tier" in imp["Feature Id"].values else None

    # 결과 정리
    def delta(a: dict, b: dict) -> dict:
        out = {}
        for src in a:
            if src in b:
                out[src] = {
                    "n": a[src]["n"],
                    "MdAPE_baseline": a[src]["MdAPE"],
                    "MdAPE_v4": b[src]["MdAPE"],
                    "MdAPE_delta": round(b[src]["MdAPE"] - a[src]["MdAPE"], 2),
                    "W30_delta": round(b[src]["W30"] - a[src]["W30"], 2),
                    "W50_delta": round(b[src]["W50"] - a[src]["W50"], 2),
                }
        return out

    result = {
        "data": {
            "n_total": int(len(df)),
            "n_artsy": int((source == "artsy").sum()),
            "n_saatchi": int((source == "saatchi").sum()),
            "gallery_tier_v4_dist": df["gallery_tier_v4"].value_counts().to_dict(),
        },
        "kfold": {
            "baseline": base_kf,
            "with_gallery_tier_v4": v4_kf,
            "delta_v4_minus_baseline": delta(base_kf, v4_kf),
        },
        "groupkfold": {
            "baseline": base_gkf,
            "with_gallery_tier_v4": v4_gkf,
            "delta_v4_minus_baseline": delta(base_gkf, v4_gkf),
        },
        "feature_importance": {
            "top10_with_v4": imp_top,
            "gallery_tier_v4_importance": float(v4_imp) if v4_imp is not None else None,
            "gallery_tier_existing_importance": float(gallery_tier_imp) if gallery_tier_imp is not None else None,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "ablation_gallery_tier_v4.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved: {out_path}")

    # 요약 출력
    print("\n" + "=" * 60)
    print("ABLATION 결과 요약")
    print("=" * 60)
    print("\n[KFold 5-fold]")
    for src in ["overall", "artsy", "saatchi"]:
        if src in base_kf:
            d = result["kfold"]["delta_v4_minus_baseline"][src]
            sign = "↓" if d["MdAPE_delta"] < 0 else "↑"
            print(f"  {src:<10s}: MdAPE {d['MdAPE_baseline']} → {d['MdAPE_v4']} ({sign}{abs(d['MdAPE_delta'])}), W30 Δ{d['W30_delta']:+.2f}, n={d['n']}")
    print("\n[GroupKFold 5-fold (cold start)]")
    for src in ["overall", "artsy", "saatchi"]:
        if src in base_gkf:
            d = result["groupkfold"]["delta_v4_minus_baseline"][src]
            sign = "↓" if d["MdAPE_delta"] < 0 else "↑"
            print(f"  {src:<10s}: MdAPE {d['MdAPE_baseline']} → {d['MdAPE_v4']} ({sign}{abs(d['MdAPE_delta'])}), W30 Δ{d['W30_delta']:+.2f}, n={d['n']}")
    print(f"\n[Feature Importance]")
    print(f"  gallery_tier_v4: {v4_imp}")
    print(f"  gallery_tier (existing): {gallery_tier_imp}")


if __name__ == "__main__":
    main()
