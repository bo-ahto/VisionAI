"""코덱스 Q1 후속 — Saatchi → 별도 category 매핑 실험.

가설: CatBoost 가 Saatchi=Tier E 21K 를 ordered target statistics 로
강하게 prior 학습 → source proxy 효과 → Artsy warm regression

실험: Saatchi → "UNKNOWN_SAATCHI" 별도 category 로 변경하고
CatBoost ablation 재실행. 가설 맞으면 Artsy warm regression 사라져야.

비교:
- Original: Saatchi → "Tier E"
- Remap: Saatchi → "UNKNOWN_SAATCHI"

Usage: PYTHONPATH=src python3 scripts/saatchi_remap_experiment.py
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


def _normalize(s):
    import re
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def attach_v4(df, saatchi_map: str = "Tier E"):
    """saatchi_map: 'Tier E' (original) or 'UNKNOWN_SAATCHI' (remap)."""
    alias_df = pd.read_csv(DATA / "gallery_alias_map.csv")
    alias = {_normalize(r["영문명"]): _normalize(r["한글명"]) for _, r in alias_df.iterrows()}
    v4 = pd.read_csv(DATA / "art_gallery_tier_list_v4.csv").dropna(subset=["명칭"])
    tier_lookup = {_normalize(r["명칭"]): str(r["티어"]).strip() for _, r in v4.iterrows()}

    def lookup(row):
        if row.get("source") == "saatchi":
            return saatchi_map
        n = _normalize(row.get("gallery_name"))
        if not n or n == "Saatchi Art":
            return saatchi_map  # Saatchi 직접 매칭도 동일 처리
        kor = alias.get(n, n)
        return tier_lookup.get(_normalize(kor), "Tier E")

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


def cb_oof(X, y, splits, cat_idx):
    oof = np.zeros(len(y))
    for tr, te in splits:
        cb = CatBoostRegressor(
            iterations=1000, learning_rate=0.05, depth=6, loss_function="RMSE",
            verbose=0, random_seed=42, allow_writing_files=False,
        )
        cb.fit(Pool(X.iloc[tr], label=y[tr], cat_features=cat_idx))
        oof[te] = cb.predict(Pool(X.iloc[te], cat_features=cat_idx))
    return oof


def metrics(y_log, oof_log, source):
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
    return out


def main():
    logger.info("=" * 70)
    logger.info("Saatchi remap 실험 — Tier E vs UNKNOWN_SAATCHI")
    logger.info("=" * 70)

    df_base = load_data()
    feats = CB_FEATURES_BASE + ["gallery_tier_v4"]
    cats = CAT_FEATURES + ["gallery_tier_v4"]
    y = df_base["ln_price"].to_numpy()
    groups = df_base["artist_slug"].astype(str).to_numpy()
    source = df_base["source"].astype(str).to_numpy()

    kf = list(KFold(n_splits=5, shuffle=True, random_state=42).split(df_base))
    gkf = list(GroupKFold(n_splits=5).split(df_base, y, groups))

    # ─── 32-feature baseline (no v4) for control ─────────
    logger.info("\n[Control] 32-feature baseline (no v4)")
    X_base = prepare_X(df_base, CB_FEATURES_BASE, CAT_FEATURES)
    cat_idx = [X_base.columns.get_loc(c) for c in CAT_FEATURES if c in X_base.columns]
    base_kf_oof = cb_oof(X_base, y, kf, cat_idx)
    base_gkf_oof = cb_oof(X_base, y, gkf, cat_idx)

    # ─── Original Saatchi → Tier E ─────────
    logger.info("\n[v4-original] Saatchi → 'Tier E'")
    df_orig = attach_v4(df_base, saatchi_map="Tier E")
    X_orig = prepare_X(df_orig, feats, cats)
    cat_idx_v4 = [X_orig.columns.get_loc(c) for c in cats if c in X_orig.columns]
    orig_kf_oof = cb_oof(X_orig, y, kf, cat_idx_v4)
    orig_gkf_oof = cb_oof(X_orig, y, gkf, cat_idx_v4)

    # ─── Remap Saatchi → UNKNOWN_SAATCHI ─────────
    logger.info("\n[v4-remap] Saatchi → 'UNKNOWN_SAATCHI'")
    df_remap = attach_v4(df_base, saatchi_map="UNKNOWN_SAATCHI")
    X_remap = prepare_X(df_remap, feats, cats)
    cat_idx_remap = [X_remap.columns.get_loc(c) for c in cats if c in X_remap.columns]
    remap_kf_oof = cb_oof(X_remap, y, kf, cat_idx_remap)
    remap_gkf_oof = cb_oof(X_remap, y, gkf, cat_idx_remap)

    result = {
        "kfold": {
            "baseline_32": metrics(y, base_kf_oof, source),
            "v4_saatchi_TierE": metrics(y, orig_kf_oof, source),
            "v4_saatchi_UNKNOWN": metrics(y, remap_kf_oof, source),
        },
        "groupkfold": {
            "baseline_32": metrics(y, base_gkf_oof, source),
            "v4_saatchi_TierE": metrics(y, orig_gkf_oof, source),
            "v4_saatchi_UNKNOWN": metrics(y, remap_gkf_oof, source),
        },
    }

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / "saatchi_remap_experiment.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("Saatchi remap 실험 결과 (CatBoost)")
    print("=" * 70)
    for cv in ["kfold", "groupkfold"]:
        print(f"\n[{cv.upper()}]")
        for key in ["baseline_32", "v4_saatchi_TierE", "v4_saatchi_UNKNOWN"]:
            r = result[cv][key]
            line = f"  {key:<22s}: "
            for src in ["overall", "artsy", "saatchi"]:
                if src in r:
                    line += f"{src}={r[src]['MdAPE']:.2f}({r[src]['n']}) "
            print(line)
        # Δ vs baseline_32
        print("  Δ MdAPE (vs baseline_32):")
        for key in ["v4_saatchi_TierE", "v4_saatchi_UNKNOWN"]:
            for src in ["overall", "artsy", "saatchi"]:
                if src in result[cv][key] and src in result[cv]["baseline_32"]:
                    d = result[cv][key][src]["MdAPE"] - result[cv]["baseline_32"][src]["MdAPE"]
                    sign = "↓" if d < 0 else "↑"
                    print(f"    {key:<22s} {src:<8s}: {sign}{abs(d):.2f}")

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
