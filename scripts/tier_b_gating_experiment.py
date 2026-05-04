"""코덱스 Q2 후속 — Tier B gating 실험.

가설: Tier B 는 너무 넓고 이질적인 bucket → v4 추가 시 과도한 shrinkage
운영 규칙: Tier B 에는 v4 미적용 gating 이 실용적

실험 (4 조건):
1. 32 features (no v4) — control
2. 33 features (+v4 모든 tier) — full v4
3. 33 features (+v4, Tier B 만 gallery_tier_v4="OTHER") — Tier B gated
4. 33 features (+v4 사용, Tier B 만 학습 시 v4 컬럼 NaN→"unknown") — soft gating

XGBoost 만 (코덱스 권고: XGBoost = 운영 후보).

Usage: PYTHONPATH=src python3 scripts/tier_b_gating_experiment.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupKFold, KFold

from visionai.price_engine._eval_helpers import label_encode_xgb
from visionai.price_engine.api.primary_predictor import CAT_FEATURES, CB_FEATURES_BASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


def _normalize(s):
    import re
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def attach_v4(df, gate_tier_b: bool = False):
    """gate_tier_b=True: Tier B → 'OTHER' 로 변경 (gating)."""
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
        t = tier_lookup.get(_normalize(kor), "Tier E")
        if gate_tier_b and t == "Tier B":
            return "OTHER"  # Gated
        return t

    df = df.copy()
    df["gallery_tier_v4"] = df.apply(lookup, axis=1)
    return df


def load_data():
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")
    if "source" not in artsy.columns:
        artsy["source"] = "artsy"
    if "source" not in saatchi.columns:
        saatchi["source"] = "saatchi"
    for col in ("ho_price_level", "medium_price_level", "profile_completeness", "ln_area"):
        for d in (artsy, saatchi):
            if col not in d.columns:
                if col == "ln_area":
                    d[col] = np.log(d["area_cm2"].clip(lower=1))
                else:
                    d[col] = 0.0
    for d in (artsy, saatchi):
        if "has_birth_year" not in d.columns:
            d["has_birth_year"] = d["artist_birth_year"].notna().astype(int)
        if "support_factor" not in d.columns:
            from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
            d["support_factor"] = d["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
        if "ho_x_support" not in d.columns:
            d["ho_x_support"] = d["ho"] * d["support_factor"]
    common = [c for c in artsy.columns if c in saatchi.columns]
    df = pd.concat([artsy[common], saatchi[common]], ignore_index=True)
    return df[df["is_excluded_for_training"] == 0].copy()


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


def xgb_oof(X, y, splits, cat_features):
    oof = np.zeros(len(y))
    for tr, te in splits:
        Xtr_e, Xte_e, _ = label_encode_xgb(X.iloc[tr], X.iloc[te], categorical_features=cat_features)
        d_tr = xgb.DMatrix(Xtr_e, label=y[tr])
        d_te = xgb.DMatrix(Xte_e, label=y[te])
        m = xgb.train(
            params={"objective": "reg:squarederror", "eta": 0.05, "max_depth": 6, "verbosity": 0, "seed": 42},
            dtrain=d_tr, num_boost_round=1000,
        )
        oof[te] = m.predict(d_te)
    return oof


def metrics_by_tier(y_log, oof_log, source, tier_v4_arr):
    y_p = np.exp(y_log)
    p_p = np.exp(oof_log)
    out = {}
    for src in ["overall", "artsy", "saatchi"]:
        m = (source == src) if src != "overall" else np.ones(len(y_p), dtype=bool)
        if m.sum():
            ape = np.abs(y_p[m] - p_p[m]) / np.abs(y_p[m])
            out[src] = {
                "n": int(m.sum()),
                "MdAPE": round(float(np.median(ape) * 100), 2),
                "W30": round(float(np.mean(ape <= 0.30) * 100), 2),
            }
    out["by_tier_v4"] = {}
    for tier in sorted(set(tier_v4_arr)):
        m = tier_v4_arr == tier
        if m.sum() < 10:
            continue
        ape = np.abs(y_p[m] - p_p[m]) / np.abs(y_p[m])
        out["by_tier_v4"][tier] = {
            "n": int(m.sum()),
            "MdAPE": round(float(np.median(ape) * 100), 2),
            "W30": round(float(np.mean(ape <= 0.30) * 100), 2),
        }
    return out


def main():
    logger.info("=" * 70)
    logger.info("Tier B gating 실험 (XGBoost)")
    logger.info("=" * 70)

    df = load_data()
    feats_v4 = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats_v4 = CAT_FEATURES + ["gallery_tier_v4"]
    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    source = df["source"].astype(str).to_numpy()
    kf = list(KFold(n_splits=5, shuffle=True, random_state=42).split(df))
    gkf = list(GroupKFold(n_splits=5).split(df, y, groups))

    # Reference tier_v4 (full, no gating) for segment metrics
    df_full = attach_v4(df, gate_tier_b=False)
    tier_v4_full = df_full["gallery_tier_v4"].astype(str).to_numpy()

    result = {}

    # 1. 32 features (control)
    logger.info("\n[1/3] 32 features (control)")
    X = prepare_X(df, CB_FEATURES_BASE, CAT_FEATURES)
    kf_oof = xgb_oof(X, y, kf, CAT_FEATURES)
    gkf_oof = xgb_oof(X, y, gkf, CAT_FEATURES)
    result["control_32"] = {
        "kfold": metrics_by_tier(y, kf_oof, source, tier_v4_full),
        "groupkfold": metrics_by_tier(y, gkf_oof, source, tier_v4_full),
    }

    # 2. 33 features (+v4, full)
    logger.info("\n[2/3] 33 features (+v4, no gating)")
    df_v4 = attach_v4(df, gate_tier_b=False)
    X_v4 = prepare_X(df_v4, feats_v4, cats_v4)
    kf_oof = xgb_oof(X_v4, y, kf, cats_v4)
    gkf_oof = xgb_oof(X_v4, y, gkf, cats_v4)
    result["v4_full"] = {
        "kfold": metrics_by_tier(y, kf_oof, source, tier_v4_full),
        "groupkfold": metrics_by_tier(y, gkf_oof, source, tier_v4_full),
    }

    # 3. 33 features (+v4, Tier B gated to "OTHER")
    logger.info("\n[3/3] 33 features (+v4, Tier B → OTHER gated)")
    df_gated = attach_v4(df, gate_tier_b=True)
    X_gated = prepare_X(df_gated, feats_v4, cats_v4)
    kf_oof = xgb_oof(X_gated, y, kf, cats_v4)
    gkf_oof = xgb_oof(X_gated, y, gkf, cats_v4)
    result["v4_tier_b_gated"] = {
        "kfold": metrics_by_tier(y, kf_oof, source, tier_v4_full),
        "groupkfold": metrics_by_tier(y, gkf_oof, source, tier_v4_full),
    }

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / "tier_b_gating_experiment.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("Tier B gating 결과 (XGBoost)")
    print("=" * 70)
    for cv in ["kfold", "groupkfold"]:
        print(f"\n[{cv.upper()}]")
        for cond in ["control_32", "v4_full", "v4_tier_b_gated"]:
            r = result[cond][cv]
            line = f"  {cond:<20s}: "
            for src in ["overall", "artsy", "saatchi"]:
                if src in r:
                    line += f"{src}={r[src]['MdAPE']:.2f} "
            print(line)
        # Tier B/E segment 비교
        print("\n  by_tier_v4 (Tier B/E):")
        for cond in ["control_32", "v4_full", "v4_tier_b_gated"]:
            r = result[cond][cv]["by_tier_v4"]
            tb = r.get("Tier B", {}).get("MdAPE", "—")
            te = r.get("Tier E", {}).get("MdAPE", "—")
            print(f"    {cond:<20s}: Tier B={tb}, Tier E={te}")

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
