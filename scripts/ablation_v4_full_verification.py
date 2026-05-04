"""코덱스 권고 1-3번 — 종합 검증.

검증 1: Artsy-only ablation (source proxy 가설 분리)
검증 2: Tier별 segment MdAPE (B/C/D 어디서 효과)
검증 3: XGBoost 동일 ablation

Usage: PYTHONPATH=src python3 scripts/ablation_v4_full_verification.py
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

from visionai.price_engine._eval_helpers import label_encode_xgb
from visionai.price_engine.api.primary_predictor import CAT_FEATURES, CB_FEATURES_BASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


def _mdape(y, p): return float(np.median(np.abs(y - p) / np.abs(y)) * 100)
def _w(y, p, t): return float(np.mean(np.abs(y - p) / np.abs(y) <= t) * 100)


def _summary(y_price, pred_price, n):
    return {
        "n": int(n),
        "MdAPE": round(_mdape(y_price, pred_price), 2),
        "W30": round(_w(y_price, pred_price, 0.30), 2),
        "W50": round(_w(y_price, pred_price, 0.50), 2),
    }


def _normalize(s):
    import re
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def attach_v4(df: pd.DataFrame) -> pd.DataFrame:
    alias_df = pd.read_csv(DATA / "gallery_alias_map.csv")
    alias = {_normalize(r["영문명"]): _normalize(r["한글명"]) for _, r in alias_df.iterrows()}
    v4 = pd.read_csv(DATA / "art_gallery_tier_list_v4.csv").dropna(subset=["명칭"])
    tier_lookup = {_normalize(r["명칭"]): str(r["티어"]).strip() for _, r in v4.iterrows()}

    def lookup(row):
        if row.get("source") == "saatchi":
            return "Tier E"
        n = _normalize(row.get("gallery_name"))
        if not n or n == "Saatchi Art":
            return "Tier E"
        kor = alias.get(n, n)
        return tier_lookup.get(_normalize(kor), "Tier E")

    df = df.copy()
    df["gallery_tier_v4"] = df.apply(lookup, axis=1)
    return df


def load_data(artsy_only: bool = False) -> pd.DataFrame:
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    if "source" not in artsy.columns:
        artsy["source"] = "artsy"
    for col in ("ho_price_level", "medium_price_level", "profile_completeness", "ln_area"):
        if col not in artsy.columns:
            if col == "ln_area":
                artsy[col] = np.log(artsy["area_cm2"].clip(lower=1))
            else:
                artsy[col] = 0.0
    if "has_birth_year" not in artsy.columns:
        artsy["has_birth_year"] = artsy["artist_birth_year"].notna().astype(int)
    if "support_factor" not in artsy.columns:
        from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
        artsy["support_factor"] = artsy["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
    if "ho_x_support" not in artsy.columns:
        artsy["ho_x_support"] = artsy["ho"] * artsy["support_factor"]

    if artsy_only:
        df = artsy[artsy["is_excluded_for_training"] == 0].copy()
    else:
        saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")
        if "source" not in saatchi.columns:
            saatchi["source"] = "saatchi"
        for col in ("ho_price_level", "medium_price_level", "profile_completeness", "ln_area"):
            if col not in saatchi.columns:
                if col == "ln_area":
                    saatchi[col] = np.log(saatchi["area_cm2"].clip(lower=1))
                else:
                    saatchi[col] = 0.0
        if "has_birth_year" not in saatchi.columns:
            saatchi["has_birth_year"] = saatchi["artist_birth_year"].notna().astype(int)
        if "support_factor" not in saatchi.columns:
            from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
            saatchi["support_factor"] = saatchi["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
        if "ho_x_support" not in saatchi.columns:
            saatchi["ho_x_support"] = saatchi["ho"] * saatchi["support_factor"]
        common = [c for c in artsy.columns if c in saatchi.columns]
        df = pd.concat([artsy[common], saatchi[common]], ignore_index=True)
        df = df[df["is_excluded_for_training"] == 0].copy()
    return df


def prepare_X(df, features, cat_features):
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


def cb_oof(X, y, splits, cat_idx):
    oof = np.zeros(len(y))
    for fold, (tr, te) in enumerate(splits, 1):
        cb = CatBoostRegressor(
            iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
            verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(Pool(X.iloc[tr], label=y[tr], cat_features=cat_idx))
        oof[te] = cb.predict(Pool(X.iloc[te], cat_features=cat_idx))
    return oof


def xgb_oof(X, y, splits, cat_features):
    oof = np.zeros(len(y))
    for fold, (tr, te) in enumerate(splits, 1):
        Xtr_e, Xte_e, _ = label_encode_xgb(X.iloc[tr], X.iloc[te], categorical_features=cat_features)
        dtrain = xgb.DMatrix(Xtr_e, label=y[tr])
        dtest = xgb.DMatrix(Xte_e, label=y[te])
        m = xgb.train(
            params={"objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=1000,
        )
        oof[te] = m.predict(dtest)
    return oof


def metrics_by_tier(y, oof, tier_arr, src_arr=None):
    """OOF 예측의 tier별 segment MdAPE."""
    out = {}
    y_p = np.exp(y)
    p_p = np.exp(oof)
    for tier in ["Tier A", "Tier B", "Tier C", "Tier D", "Tier E"]:
        mask = tier_arr == tier
        if mask.sum() == 0:
            continue
        out[tier] = _summary(y_p[mask], p_p[mask], int(mask.sum()))
        if src_arr is not None:
            for src in sorted(set(src_arr)):
                sm = mask & (src_arr == src)
                if sm.sum() > 5:
                    out[tier][src] = _summary(y_p[sm], p_p[sm], int(sm.sum()))
    return out


def run_one_condition(df, features, cat_features, label, model="catboost"):
    X = prepare_X(df, features, cat_features)
    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    source = df["source"].astype(str).to_numpy()
    tier_v4 = df["gallery_tier_v4"].astype(str).to_numpy() if "gallery_tier_v4" in df.columns else np.array(["?"] * len(df))

    out = {"label": label, "n": len(df)}
    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]

    # KFold (warm-style)
    kf = list(KFold(n_splits=5, shuffle=True, random_state=42).split(X))
    if model == "catboost":
        oof_kf = cb_oof(X, y, kf, cat_idx)
    else:
        oof_kf = xgb_oof(X, y, kf, cat_features)
    y_p = np.exp(y)
    p_p = np.exp(oof_kf)
    out["kfold"] = {"overall": _summary(y_p, p_p, len(y))}
    for src in sorted(set(source)):
        m = source == src
        if m.sum():
            out["kfold"][src] = _summary(y_p[m], p_p[m], int(m.sum()))
    out["kfold"]["by_tier_v4"] = metrics_by_tier(y, oof_kf, tier_v4, source)

    # GroupKFold (cold start)
    gkf = list(GroupKFold(n_splits=5).split(X, y, groups))
    if model == "catboost":
        oof_gkf = cb_oof(X, y, gkf, cat_idx)
    else:
        oof_gkf = xgb_oof(X, y, gkf, cat_features)
    p_p = np.exp(oof_gkf)
    out["groupkfold"] = {"overall": _summary(y_p, p_p, len(y))}
    for src in sorted(set(source)):
        m = source == src
        if m.sum():
            out["groupkfold"][src] = _summary(y_p[m], p_p[m], int(m.sum()))
    out["groupkfold"]["by_tier_v4"] = metrics_by_tier(y, oof_gkf, tier_v4, source)

    return out


def main():
    logger.info("=" * 60)
    logger.info("종합 검증: Artsy-only + Tier segment + XGBoost ablation")
    logger.info("=" * 60)

    feats_v4 = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats_v4 = CAT_FEATURES + ["gallery_tier_v4"]

    # ==== 검증 1: Artsy-only (source proxy 분리) ====
    logger.info("\n>>> 검증 1: Artsy-only ablation (n=7,289)")
    df_artsy = attach_v4(load_data(artsy_only=True))
    logger.info(f"  Artsy gallery_tier_v4 분포: {df_artsy['gallery_tier_v4'].value_counts().to_dict()}")

    artsy_cb_base = run_one_condition(df_artsy, CB_FEATURES_BASE, CAT_FEATURES, "artsy_only_cb_base", "catboost")
    artsy_cb_v4 = run_one_condition(df_artsy, feats_v4, cats_v4, "artsy_only_cb_v4", "catboost")
    artsy_xgb_base = run_one_condition(df_artsy, CB_FEATURES_BASE, CAT_FEATURES, "artsy_only_xgb_base", "xgboost")
    artsy_xgb_v4 = run_one_condition(df_artsy, feats_v4, cats_v4, "artsy_only_xgb_v4", "xgboost")

    # ==== 검증 3: XGBoost 동일 ablation (full data, 28K) ====
    logger.info("\n>>> 검증 3: XGBoost ablation on full data (n=28,376)")
    df_full = attach_v4(load_data(artsy_only=False))
    full_xgb_base = run_one_condition(df_full, CB_FEATURES_BASE, CAT_FEATURES, "full_xgb_base", "xgboost")
    full_xgb_v4 = run_one_condition(df_full, feats_v4, cats_v4, "full_xgb_v4", "xgboost")

    # ==== Tier segment 차이 (Artsy-only CatBoost) ====
    def delta_summary(base, v4):
        out = {}
        for cv in ["kfold", "groupkfold"]:
            d = {}
            for k in base[cv]:
                if k == "by_tier_v4":
                    d["by_tier_v4"] = {}
                    for tier in base[cv]["by_tier_v4"]:
                        if tier in v4[cv]["by_tier_v4"]:
                            b = base[cv]["by_tier_v4"][tier]
                            t = v4[cv]["by_tier_v4"][tier]
                            d["by_tier_v4"][tier] = {
                                "n": b["n"],
                                "MdAPE_base": b["MdAPE"],
                                "MdAPE_v4": t["MdAPE"],
                                "delta": round(t["MdAPE"] - b["MdAPE"], 2),
                            }
                elif isinstance(base[cv].get(k), dict) and "MdAPE" in base[cv][k]:
                    b = base[cv][k]
                    t = v4[cv].get(k, {})
                    if "MdAPE" in t:
                        d[k] = {
                            "n": b["n"],
                            "MdAPE_base": b["MdAPE"],
                            "MdAPE_v4": t["MdAPE"],
                            "delta": round(t["MdAPE"] - b["MdAPE"], 2),
                            "W30_delta": round(t["W30"] - b["W30"], 2),
                        }
            out[cv] = d
        return out

    result = {
        "v1_artsy_only": {
            "data": {"n": int(len(df_artsy)), "tier_v4_dist": df_artsy["gallery_tier_v4"].value_counts().to_dict()},
            "catboost": {"baseline": artsy_cb_base, "v4": artsy_cb_v4, "delta": delta_summary(artsy_cb_base, artsy_cb_v4)},
            "xgboost": {"baseline": artsy_xgb_base, "v4": artsy_xgb_v4, "delta": delta_summary(artsy_xgb_base, artsy_xgb_v4)},
        },
        "v3_xgboost_full": {
            "data": {"n": int(len(df_full))},
            "delta": delta_summary(full_xgb_base, full_xgb_v4),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "ablation_v4_full_verification.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved: {out_path}")

    # 요약 출력
    print("\n" + "=" * 70)
    print("종합 검증 요약")
    print("=" * 70)

    print("\n[검증 1: Artsy-only CatBoost — source proxy 분리]")
    for cv in ["kfold", "groupkfold"]:
        d = result["v1_artsy_only"]["catboost"]["delta"][cv]
        if "overall" in d:
            print(f"  {cv:<12s} overall: MdAPE {d['overall']['MdAPE_base']} → {d['overall']['MdAPE_v4']} (Δ{d['overall']['delta']:+.2f}), n={d['overall']['n']}")

    print("\n[검증 1: Artsy-only XGBoost]")
    for cv in ["kfold", "groupkfold"]:
        d = result["v1_artsy_only"]["xgboost"]["delta"][cv]
        if "overall" in d:
            print(f"  {cv:<12s} overall: MdAPE {d['overall']['MdAPE_base']} → {d['overall']['MdAPE_v4']} (Δ{d['overall']['delta']:+.2f}), n={d['overall']['n']}")

    print("\n[검증 2: Artsy-only Tier segment MdAPE (CatBoost KFold)]")
    for tier, d in result["v1_artsy_only"]["catboost"]["delta"]["kfold"]["by_tier_v4"].items():
        print(f"  {tier} (n={d['n']}): {d['MdAPE_base']} → {d['MdAPE_v4']} (Δ{d['delta']:+.2f})")
    print("\n[검증 2: Artsy-only Tier segment MdAPE (CatBoost GroupKFold)]")
    for tier, d in result["v1_artsy_only"]["catboost"]["delta"]["groupkfold"]["by_tier_v4"].items():
        print(f"  {tier} (n={d['n']}): {d['MdAPE_base']} → {d['MdAPE_v4']} (Δ{d['delta']:+.2f})")

    print("\n[검증 3: XGBoost full data ablation]")
    for cv in ["kfold", "groupkfold"]:
        d = result["v3_xgboost_full"]["delta"][cv]
        for src in ["overall", "artsy", "saatchi"]:
            if src in d:
                e = d[src]
                print(f"  {cv:<12s} {src:<8s}: MdAPE {e['MdAPE_base']} → {e['MdAPE_v4']} (Δ{e['delta']:+.2f}), n={e['n']}")


if __name__ == "__main__":
    main()
