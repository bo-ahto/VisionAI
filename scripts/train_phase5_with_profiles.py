"""Phase 5 최종+프로필 — Artsy 61명 프로필 피처 통합.

기존 Phase 5 Final (Model-A q50 + CQR 0.38) + Artsy 프로필 피처 추가.

Usage:
    PYTHONPATH=src python3 scripts/train_phase5_with_profiles.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
MACRO_PATH = ROOT / "data" / "macro_session.csv"
PROFILE_PATH = ROOT / "data" / "artsy_artist_profiles.csv"
OUTPUT_DIR = ROOT / "model_test_results"

_COLD_THRESHOLD = 5
HIGH_PSI = ["market_price_index", "artist_career_length", "medium_avg_price"]

PROFILE_FEATURES = [
    "profile_birth_year",
    "profile_artworks_count",
    "profile_review_count",
    "profile_has_solo_show",
    "profile_has_museum_collection",
    "profile_is_korean",
]


def join_artsy_profiles(df: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """Artsy 프로필 피처를 작품 DataFrame에 조인."""
    out = df.copy()

    # 프로필 피처 준비
    prof = profiles[profiles["found"] == True].copy()  # noqa: E712
    prof["profile_birth_year"] = pd.to_numeric(prof["birth_year"], errors="coerce").fillna(0)
    prof["profile_artworks_count"] = prof["artworks_count"].fillna(0)
    prof["profile_review_count"] = prof["review_count"].fillna(0)
    prof["profile_has_solo_show"] = (prof["solo_show_institution"].fillna("") != "").astype(int)
    has_museum = prof["museum_collection"].fillna("") != ""
    prof["profile_has_museum_collection"] = has_museum.astype(int)
    nat = prof["nationality"].fillna("")
    prof["profile_is_korean"] = nat.str.contains("Korean", case=False).astype(int)

    # ko_name → artist_clean 매핑
    prof_map = prof.set_index("ko_name")[PROFILE_FEATURES].to_dict("index")

    for feat in PROFILE_FEATURES:
        out[feat] = out["artist_clean"].map(
            {k: v[feat] for k, v in prof_map.items()}
        ).fillna(0)

    matched = (out["profile_artworks_count"] > 0).sum()
    logger.info("Profile joined: %d/%d rows matched", matched, len(out))
    return out


def main() -> None:
    # ─── 1. 피처 빌드 ───
    logger.info("=== Step 1: Features ===")
    from visionai.price_engine.estimate_generator.hedonic_features import (
        build_hedonic_features,
    )

    df = build_hedonic_features(DATA_PATH)

    # ─── 2. 매크로 ───
    logger.info("=== Step 2: Macro ===")
    from visionai.price_engine.features.macro_indicators import (
        join_macro_features,
        load_macro_session,
    )

    if MACRO_PATH.exists():
        macro = load_macro_session(MACRO_PATH)
        df = join_macro_features(df, macro, session_col="회차", lag_sessions=1)

    # ─── 3. Similarity (Cold-only) ───
    logger.info("=== Step 3: Similarity ===")
    from visionai.price_engine.features.artist_similarity import (
        build_artist_feature_vectors,
        compute_similarity_features,
        find_similar_artists,
    )

    train_only = df[df["split"] == "train"]
    vectors = build_artist_feature_vectors(train_only, cutoff=999999)

    sim_features = []
    for _, row in df.iterrows():
        artist = row.get("artist_clean", "")
        medium = row.get("medium_category", None)
        similar = find_similar_artists(
            str(artist), vectors, k=5,
            medium_filter=str(medium) if medium else None,
        )
        sim_features.append(compute_similarity_features(str(artist), similar))

    sim_df = pd.DataFrame(sim_features, index=df.index)
    for col in sim_df.columns:
        df[col] = sim_df[col]

    # Cold-only
    sim_cols = ["sim_avg_price_ln", "sim_weighted_price_ln",
                "sim_count", "sim_avg_distance"]
    for col in sim_cols:
        if col in df.columns:
            warm = df["artist_total_sold"].fillna(0) >= _COLD_THRESHOLD
            df.loc[warm, col] = 0.0

    # ─── 4. Artsy 프로필 ───
    logger.info("=== Step 4: Artsy Profiles ===")
    if PROFILE_PATH.exists():
        profiles = pd.read_csv(PROFILE_PATH)
        df = join_artsy_profiles(df, profiles)
    else:
        logger.warning("Profile data not found")
        for feat in PROFILE_FEATURES:
            df[feat] = 0

    # ─── 5. PSI 정규화 ───
    train_mask = (df["split"] == "train").values
    for feat in HIGH_PSI:
        if feat not in df.columns:
            continue
        vals = pd.to_numeric(df[feat], errors="coerce")
        mean, std = float(vals[train_mask].mean()), float(vals[train_mask].std())
        df[feat] = (vals - mean) / std if std > 0 else 0.0

    # ─── 6. Split ───
    train = df[df["split"] == "train"]
    calib = df[df["split"] == "calib"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]

    # ─── 7. Model-A ───
    logger.info("=== Step 5: Model-A ===")
    from visionai.price_engine.estimate_generator.quantile_model import (
        HedonicQuantileModel,
    )

    model_a = HedonicQuantileModel(iterations=2000, depth=8, learning_rate=0.05)
    model_a.fit(
        train, valid_df=calib, target_col="ln_price",
        extra_features=PROFILE_FEATURES,
    )
    model_a.save(OUTPUT_DIR / "model_a_quantile.cbm")

    # ─── 8. CQR alpha=0.38 ───
    logger.info("=== Step 6: CQR ===")
    from visionai.price_engine.estimate_generator.conformal_calibrator import (
        ConformalQuantileCalibrator,
    )

    raw_q_c = model_a.predict_raw(calib)
    y_c = calib["ln_price"].dropna()
    mask_c = calib["ln_price"].notna()

    cqr = ConformalQuantileCalibrator(alpha=0.38)
    cqr.fit(y_c.values, raw_q_c[mask_c.values])
    cqr.save(str(OUTPUT_DIR / "conformal_calibrator.pkl"))

    # ─── 9. 평가 ───
    logger.info("=== Step 7: 평가 ===")

    def evaluate(split_df, name):
        raw_q = model_a.predict_raw(split_df)
        y = split_df["ln_price"].values
        mask = np.isfinite(y)
        cal_q = cqr.predict(raw_q[mask])
        p_l, p_m, p_h = np.exp(cal_q[:, 0]), np.exp(cal_q[:, 1]), np.exp(cal_q[:, 2])
        y_t = np.exp(y[mask])

        ape = np.abs(p_m - y_t) / y_t
        mdape = float(np.median(ape) * 100)
        w30 = float(np.mean(ape <= 0.30) * 100)
        cov = float(np.mean((y_t >= p_l) & (y_t <= p_h)))
        ss_r = np.sum((y_t - p_m) ** 2)
        ss_t = np.sum((y_t - np.mean(y_t)) ** 2)
        r2 = float(1 - ss_r / ss_t) if ss_t > 0 else 0

        cold = split_df["is_new_artist"].astype(bool).values[mask]
        c_md = float(np.median(ape[cold]) * 100) if cold.sum() > 0 else float("nan")
        w_md = float(np.median(ape[~cold]) * 100) if (~cold).sum() > 0 else float("nan")

        logger.info(
            "%s: MdAPE=%.2f%% (W=%.2f%% C=%.2f%%) R2=%.4f Cov=%.1f%% W30=%.1f%%",
            name, mdape, w_md, c_md, r2, cov * 100, w30,
        )
        return {
            "mdape": mdape, "warm_mdape": w_md, "cold_mdape": c_md,
            "r2": r2, "coverage": cov, "within_30": w30,
        }

    v = evaluate(valid, "Valid")
    t = evaluate(test, "Test")
    gap = t["mdape"] - v["mdape"]
    mono = model_a.check_monotonicity(valid)

    # Gate
    logger.info("=" * 60)
    gates = {
        "G1 MdAPE<=32%": t["mdape"] <= 32,
        "G2 Gap<=2.5%p": abs(gap) <= 2.5,
        "G3 R2>=0.40": t["r2"] >= 0.40,
        "G4 Cold<=58%": t["cold_mdape"] <= 58,
        "G5 Cov>=55%": t["coverage"] >= 0.55,
        "G6 W30>=53%": t["within_30"] >= 53,
        "G8 Mono>=0.99": mono >= 0.99,
    }
    for g, ok in gates.items():
        logger.info("  %s: %s", g, "PASS" if ok else "FAIL")
    logger.info("Gate: %d/%d", sum(gates.values()), len(gates))
    logger.info("=" * 60)

    # 저장
    metrics = {
        "valid_mdape": v["mdape"], "test_mdape": t["mdape"], "gap": gap,
        "valid_r2": v["r2"], "test_r2": t["r2"],
        "valid_coverage": v["coverage"], "test_coverage": t["coverage"],
        "valid_within_30": v["within_30"], "test_within_30": t["within_30"],
        "cold_mdape": t["cold_mdape"], "warm_mdape": t["warm_mdape"],
        "monotonicity_rate": mono,
        "coverage_overall": t["coverage"], "within_30_pct": t["within_30"],
        "gates": gates,
        "model": "Model-A q50 + CQR 0.38 + Artsy profiles",
        "profile_features": PROFILE_FEATURES,
    }
    for name in ["phase5_profile_metrics.json", "estimate_metrics.json"]:
        with open(OUTPUT_DIR / name, "w") as f:
            json.dump(metrics, f, indent=2, default=str)

    gap_p = OUTPUT_DIR / "gap_diagnosis.json"
    if gap_p.exists():
        with open(gap_p) as f:
            diag = json.load(f)
        diag.update({
            "valid_mdape": v["mdape"], "test_mdape": t["mdape"],
            "gap": gap, "within_30_pct": t["within_30"],
            "coverage_overall": t["coverage"],
        })
        with open(gap_p, "w") as f:
            json.dump(diag, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Saved to %s", OUTPUT_DIR / "phase5_profile_metrics.json")


if __name__ == "__main__":
    main()
