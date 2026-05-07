"""Progressive Sampling — Phase 0 holdout 봉인 + Phase 1 Stage 1 exploration.

Phase 0 mini-prereg freeze: docs/progressive_sampling_phase0_freeze_20260507.md
사용자 명시 instruction: 체크포인트 설정 후 A 옵션 진입
코덱스 사전 자문: 조건부 GO + 3 조건 (Stage 3 transfer filter / holdout decision-binding /
family cap·tie·stop rule)

본 script:
1. Phase 0: locked holdout 봉인 (stage4_full stratified artist 20% / random_state=42 /
   hash 저장 / parquet 봉인)
2. Phase 1 / Stage 1: stage1_200x20 exploration — 5 family 별 variant generation +
   100-seed LAO 평가 + Stage 1 retain 기준 적용 (Overall Δ ≤ -0.3%p AND Low Δ ≤ +0.2%p)

코덱스 framing 톤: exploratory uplift only / decision X / Stage 1 결과 ≠ 의사결정 근거.
"""

from __future__ import annotations

import hashlib
import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent.parent
CURATED = ROOT / "data" / "curated"
RESULTS = Path(__file__).parent / "results"
LOW_PRICE_KRW = 5_000_000
N_SEEDS = 100
HOLDOUT_SEED = 42
HOLDOUT_RATIO = 0.20
BIRTH_YEAR_CENTER = 1977.44

STAGE1 = CURATED / "stage1_200x20.parquet"
STAGE4 = CURATED / "stage4_full.parquet"
HOLDOUT_FILE = CURATED / "progressive_sampling_locked_holdout_v1.parquet"
HOLDOUT_HASH_FILE = CURATED / "progressive_sampling_locked_holdout_v1.hash.txt"


# ============================================================
# Phase 0 — Locked holdout 봉인
# ============================================================

def stratified_artist_holdout(df_full):
    """Artist 20% holdout, stratified by depth + median_price + low_share. Random seed 42 freeze."""
    rng = np.random.default_rng(HOLDOUT_SEED)
    artist_stats = df_full.groupby("artist_slug").agg(
        n_works=("artwork_id", "count"),
        median_price=("price_krw", "median"),
        low_share=("price_krw", lambda s: (s < LOW_PRICE_KRW).mean()),
    ).reset_index()

    # Strata 1: artist depth bucket
    def depth_bucket(n):
        if n == 1: return "1"
        if n == 2: return "2"
        if n <= 4: return "3-4"
        if n <= 9: return "5-9"
        if n <= 19: return "10-19"
        return "20+"
    artist_stats["depth_bucket"] = artist_stats.n_works.apply(depth_bucket)

    # Strata 2: median price bucket
    def price_bucket(p):
        if p < 5_000_000: return "<5M"
        if p < 20_000_000: return "5-20M"
        return "20M+"
    artist_stats["price_bucket"] = artist_stats.median_price.apply(price_bucket)

    # Strata 3: low share bucket
    def low_bucket(s):
        if s == 0: return "0%"
        if s < 0.51: return "1-50%"
        if s < 1.0: return "51-99%"
        return "100%"
    artist_stats["low_bucket"] = artist_stats.low_share.apply(low_bucket)

    # Combined strata
    artist_stats["stratum"] = artist_stats.depth_bucket + "|" + artist_stats.price_bucket + "|" + artist_stats.low_bucket

    # Stratified sampling — 각 stratum 에서 20% (round) holdout
    holdout_artists = []
    for stratum, group in artist_stats.groupby("stratum"):
        n = len(group)
        n_holdout = max(1, int(round(n * HOLDOUT_RATIO))) if n >= 5 else (1 if rng.random() < HOLDOUT_RATIO else 0)
        if n_holdout > 0:
            sampled = rng.choice(group.artist_slug.values, size=min(n_holdout, n), replace=False)
            holdout_artists.extend(sampled)

    return sorted(holdout_artists)


def lock_holdout(df_full):
    """Phase 0: holdout 생성 → hash 저장 → parquet 봉인."""
    if HOLDOUT_FILE.exists() and HOLDOUT_HASH_FILE.exists():
        logger.info(f"Holdout already locked: {HOLDOUT_FILE.relative_to(ROOT)}")
        existing = pd.read_parquet(HOLDOUT_FILE)
        h = HOLDOUT_HASH_FILE.read_text().strip()
        logger.info(f"  Hash: {h}")
        logger.info(f"  Holdout artists: {len(existing)}")
        return set(existing.artist_slug.values)

    logger.info("Phase 0: Locking holdout (stratified artist 20%, seed 42)")
    holdout_artists = stratified_artist_holdout(df_full)
    holdout_set = set(holdout_artists)

    # Holdout sample = stage4_full 의 holdout artists
    df_holdout = df_full[df_full.artist_slug.isin(holdout_set)].reset_index(drop=True)

    # Hash
    artist_str = "\n".join(sorted(holdout_artists))
    artist_hash = hashlib.sha256(artist_str.encode()).hexdigest()[:16]

    # Save
    df_holdout[["artwork_id", "artist_slug"]].to_parquet(HOLDOUT_FILE, index=False)
    HOLDOUT_HASH_FILE.write_text(artist_hash)

    n_holdout_rows = len(df_holdout)
    n_holdout_artists = len(holdout_set)
    logger.info(f"  Holdout: {n_holdout_artists} artists / {n_holdout_rows} rows")
    logger.info(f"  Hash (SHA-16): {artist_hash}")
    logger.info(f"  Saved: {HOLDOUT_FILE.relative_to(ROOT)}")
    return holdout_set


# ============================================================
# Phase 1 / Stage 1 — Family-별 variant exploration
# ============================================================

def restricted_cubic_spline(x, knots):
    last_k, pre_last_k = knots[-1], knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(len(knots) - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def ensure_derived_columns(df):
    df = df.copy()
    if "log_price" not in df.columns:
        df["log_price"] = np.log(df["price_krw"].astype(float))
    if "log_area" not in df.columns:
        df["log_area"] = np.log(df["area_cm2"].astype(float))
    if "birth_year_centered" not in df.columns:
        df["birth_year_centered"] = df["artist_birth_year"].astype(float) - BIRTH_YEAR_CENTER
    if "log_artist_total_works" not in df.columns:
        df["log_artist_total_works"] = np.log(df["artist_total_works"].astype(float))
    return df


def build_baseline(df, knots=None):
    out = df[["log_area", "birth_year_centered", "log_artist_total_works"]].copy().reset_index(drop=True)
    if knots is None:
        knots = np.percentile(df["log_area"].values, [10, 50, 90])
    sp = restricted_cubic_spline(df["log_area"].values, knots)
    out["log_area_spline"] = sp[:, 0]
    return out.values, knots


def _aspect_ratio(df):
    """Stage 1 (aspect_ratio column 직접) vs Stage 4 (width/height) 호환."""
    if "aspect_ratio" in df.columns:
        ar = df["aspect_ratio"].astype(float).values
        return np.log(np.maximum(ar, 1e-6))
    if "width_cm" in df.columns and "height_cm" in df.columns:
        w = df["width_cm"].astype(float).values
        h = df["height_cm"].astype(float).values
        return np.log(np.maximum(w, 1e-6)) - np.log(np.maximum(h, 1e-6))
    return None


def _is_3d(df):
    """Stage 1 (has_depth column) vs Stage 4 (depth_cm) 호환."""
    if "has_depth" in df.columns:
        return df["has_depth"].astype(float).values
    if "depth_cm" in df.columns:
        d = df["depth_cm"].astype(float).values
        return ((~np.isnan(d)) & (d > 0)).astype(float)
    return None


def _log_depth(df):
    """log_depth (Stage 4 만, Stage 1 없음 → None)."""
    if "depth_cm" in df.columns:
        d = df["depth_cm"].astype(float).values
        is_3d = ((~np.isnan(d)) & (d > 0)).astype(float)
        return np.where(is_3d == 1, np.log(np.maximum(d, 1e-6)), 0.0)
    return None


def build_variant(df, variant_name, train_top_k=None):
    """Family 별 variant feature engineering. df 에서 numeric matrix return.
    train_top_k: cross_artist_cat 용 train fold 기준 top-K (test fold 도 동일 set 사용)
    """
    if variant_name == "geom_aspect_poly":
        ar = _aspect_ratio(df)
        if ar is None: return None
        return np.column_stack([ar, ar ** 2])
    elif variant_name == "geom_aspect_is3d":
        ar = _aspect_ratio(df)
        is_3d = _is_3d(df)
        if ar is None or is_3d is None: return None
        return np.column_stack([ar, is_3d, ar * is_3d])
    elif variant_name == "geom_depth_spline":
        log_d = _log_depth(df)
        is_3d = _is_3d(df)
        if log_d is None or is_3d is None: return None  # Stage 1 SKIP (depth_cm 없음)
        if (is_3d == 1).sum() > 5:
            knots3 = np.percentile(log_d[is_3d == 1], [10, 50, 90])
            sp_d = restricted_cubic_spline(log_d, knots3)
            return np.column_stack([is_3d, log_d, sp_d[:, 0]])
        return np.column_stack([is_3d, log_d, np.zeros_like(log_d)])
    elif variant_name == "geom_max_dim":
        # Stage 1: area_cm2 sqrt 사용 / Stage 4: max(w,h,d)
        if "width_cm" in df.columns and "height_cm" in df.columns:
            w = df["width_cm"].astype(float).values
            h = df["height_cm"].astype(float).values
            d = df["depth_cm"].fillna(0).astype(float).values if "depth_cm" in df.columns else np.zeros(len(df))
            max_dim = np.log(np.maximum(np.maximum(w, h), np.maximum(d, 1e-6)))
        else:
            # Stage 1 fallback — sqrt(area) ~ representative dim
            area = df["area_cm2"].astype(float).values
            max_dim = 0.5 * np.log(np.maximum(area, 1e-6))
        return max_dim.reshape(-1, 1)
    elif variant_name == "geom_full":
        ar = _aspect_ratio(df)
        is_3d = _is_3d(df)
        if ar is None or is_3d is None: return None
        log_d3d = _log_depth(df)
        if log_d3d is None:
            log_d3d = np.zeros(len(df))  # Stage 1 fallback
        return np.column_stack([ar, ar ** 2, is_3d, log_d3d, ar * is_3d])

    elif variant_name == "temp_year_birth":
        ym = df["year_made"].astype(float).fillna(df["artist_birth_year"].astype(float) + 30).values
        by = df["artist_birth_year"].astype(float).values
        return np.column_stack([ym - 2000, ym - by, (ym - by) ** 2])
    elif variant_name == "temp_career_age":
        career = df["career_age"].astype(float).fillna(0).values if "career_age" in df.columns else np.zeros(len(df))
        return career.reshape(-1, 1)
    elif variant_name == "temp_decade":
        ym = df["year_made"].astype(float).fillna(2010).values
        decade = (ym // 10) * 10 - 1980
        return decade.reshape(-1, 1)
    elif variant_name == "temp_age_x_area":
        ym = df["year_made"].astype(float).fillna(2010).values
        by = df["artist_birth_year"].astype(float).values
        age = ym - by
        return (age * df["log_area"].values).reshape(-1, 1)

    elif variant_name == "cat_gallery_x_category":
        cat = df["medium_category"].astype(str).fillna("unknown").values if "medium_category" in df.columns else df["category"].astype(str).fillna("unknown").values if "category" in df.columns else np.array(["unknown"] * len(df))
        gallery = df["gallery_name"].astype(str).fillna("unknown").values if "gallery_name" in df.columns else np.array(["unknown"] * len(df))
        # Top-K from train_top_k (fold-stable)
        if train_top_k is None:
            top_g = pd.Series(gallery).value_counts().index[:5].tolist()
            top_c = pd.Series(cat).value_counts().index[:5].tolist()
        else:
            top_g, top_c = train_top_k.get("g", []), train_top_k.get("c", [])
        out = []
        for g in top_g:
            for c in top_c:
                out.append(((gallery == g) & (cat == c)).astype(float))
        return np.column_stack(out) if out else np.zeros((len(df), 1))
    elif variant_name == "cat_city_medium":
        # Top-3 city × top-3 medium one-hot
        if "gallery_city_count" in df.columns:
            city = df["gallery_city_count"].astype(int).clip(0, 3).values.reshape(-1, 1)
        else:
            city = np.zeros((len(df), 1))
        return city.astype(float)
    elif variant_name == "cat_attribution_x_3d":
        if "support_type" not in df.columns:
            return np.zeros((len(df), 1))
        sup = df["support_type"].astype(str).fillna("unknown").values
        d = df["depth_cm"].astype(float).values
        is_3d = ((~np.isnan(d)) & (d > 0)).astype(float)
        return np.column_stack([(sup == "canvas").astype(float) * is_3d])

    elif variant_name == "artist_popularity":
        if "ln_followers" in df.columns:
            return df["ln_followers"].astype(float).fillna(0).values.reshape(-1, 1)
        if "artist_followers" in df.columns:
            return np.log1p(df["artist_followers"].astype(float).fillna(0).values).reshape(-1, 1)
        return np.zeros((len(df), 1))
    elif variant_name == "artist_for_sale":
        if "for_sale_ratio" in df.columns:
            return df["for_sale_ratio"].astype(float).fillna(0).values.reshape(-1, 1)
        return np.zeros((len(df), 1))
    elif variant_name == "artist_median_proxy":
        # 운영 model 기존 log_artist_total_works 와 redundant — re-test
        if "ln_followers" in df.columns and "for_sale_ratio" in df.columns:
            return np.column_stack([df["ln_followers"].fillna(0).values, df["for_sale_ratio"].fillna(0).values])
        return np.zeros((len(df), 1))

    elif variant_name == "miss_year_made":
        return df["year_made"].isna().astype(float).values.reshape(-1, 1)
    elif variant_name == "miss_depth":
        return df["depth_cm"].isna().astype(float).values.reshape(-1, 1)
    elif variant_name == "miss_proxy_USD":
        if "is_krw" in df.columns:
            return (1.0 - df["is_krw"].astype(float).fillna(1)).values.reshape(-1, 1)
        return np.zeros((len(df), 1))

    raise ValueError(f"Unknown variant: {variant_name}")


FAMILY_VARIANTS = {
    "geometry": ["geom_aspect_poly", "geom_aspect_is3d", "geom_depth_spline", "geom_max_dim", "geom_full"],
    "temporal": ["temp_year_birth", "temp_career_age", "temp_decade", "temp_age_x_area"],
    "cross_artist_cat": ["cat_gallery_x_category", "cat_city_medium", "cat_attribution_x_3d"],
    "artist_stats": ["artist_popularity", "artist_for_sale", "artist_median_proxy"],
    "missingness": ["miss_year_made", "miss_depth", "miss_proxy_USD"],
}


def fit_huber(Xtr, ytr, Xte):
    if len(ytr) < 5:
        return np.full(len(Xte), float(np.mean(ytr) if len(ytr) else 0.0))
    m = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=2000)
    m.fit(Xtr, ytr)
    return Xte @ m.coef_ + m.intercept_


def mdape_log(yte, pred):
    if len(yte) == 0:
        return None
    return float(np.median(np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)) * 100)


def lao_split(df, seed):
    rng = np.random.default_rng(seed)
    artists = df["artist_slug"].unique()
    n_test = max(1, int(len(artists) * 0.2))
    test_artists = set(rng.choice(artists, size=n_test, replace=False))
    return ~df["artist_slug"].isin(test_artists).values, df["artist_slug"].isin(test_artists).values


def evaluate_variant(df, y, variant_name, n_seeds=N_SEEDS):
    """Variant 별 100-seed LAO 평가. baseline + variant features 추가."""
    diffs_overall = []
    diffs_low = []
    diffs_high = []
    for seed in range(n_seeds):
        train_mask, test_mask = lao_split(df, seed)
        df_tr = df[train_mask].reset_index(drop=True)
        df_te = df[test_mask].reset_index(drop=True)
        if len(df_tr) < 50 or len(df_te) < 5:
            continue

        Xtr_b, knots = build_baseline(df_tr)
        Xte_b, _ = build_baseline(df_te, knots=knots)
        y_tr = y[train_mask].values.astype(float)
        y_te = y[test_mask].values.astype(float)

        try:
            # Train-fold based top-K for cat variants (fold-stable)
            train_top_k = None
            if variant_name == "cat_gallery_x_category":
                cat_col = "medium_category" if "medium_category" in df_tr.columns else "category" if "category" in df_tr.columns else None
                if cat_col:
                    cats = df_tr[cat_col].astype(str).fillna("unknown").values
                    galls = df_tr["gallery_name"].astype(str).fillna("unknown").values if "gallery_name" in df_tr.columns else np.array(["unknown"] * len(df_tr))
                    train_top_k = {
                        "g": pd.Series(galls).value_counts().index[:5].tolist(),
                        "c": pd.Series(cats).value_counts().index[:5].tolist(),
                    }
            v_tr = build_variant(df_tr, variant_name, train_top_k=train_top_k)
            v_te = build_variant(df_te, variant_name, train_top_k=train_top_k)
            if v_tr is None or v_te is None:
                return None
            if v_tr.shape[1] != v_te.shape[1]:
                return None
        except Exception:
            return None

        Xtr = np.column_stack([Xtr_b, v_tr])
        Xte = np.column_stack([Xte_b, v_te])

        pred_b = fit_huber(Xtr_b, y_tr, Xte_b)
        pred_v = fit_huber(Xtr, y_tr, Xte)

        is_low = df_te["price_krw"].values < LOW_PRICE_KRW
        d_o = mdape_log(y_te, pred_v) - mdape_log(y_te, pred_b)
        diffs_overall.append(d_o)
        if is_low.sum():
            diffs_low.append(mdape_log(y_te[is_low], pred_v[is_low]) - mdape_log(y_te[is_low], pred_b[is_low]))
        if (~is_low).sum():
            diffs_high.append(mdape_log(y_te[~is_low], pred_v[~is_low]) - mdape_log(y_te[~is_low], pred_b[~is_low]))

    return {
        "n_seeds": len(diffs_overall),
        "overall_mean": float(np.mean(diffs_overall)) if diffs_overall else None,
        "overall_std": float(np.std(diffs_overall)) if diffs_overall else None,
        "low_mean": float(np.mean(diffs_low)) if diffs_low else None,
        "high_mean": float(np.mean(diffs_high)) if diffs_high else None,
    }


def stage1_explore(df_stage1):
    """Stage 1: family 별 variant evaluation + retain 기준 적용."""
    df = ensure_derived_columns(df_stage1)
    y = df["log_price"]

    logger.info(f"\n=== Phase 1 / Stage 1 (stage1_200x20) exploration ===")
    logger.info(f"Dataset: {len(df)} rows / {df.artist_slug.nunique()} artists")
    logger.info(f"Retain 기준: Overall Δ ≤ -0.3%p AND Low Δ ≤ +0.2%p (exploratory only)")
    logger.info(f"")

    results = {}
    for family, variants in FAMILY_VARIANTS.items():
        logger.info(f"--- Family: {family} ---")
        family_results = {}
        for v in variants:
            res = evaluate_variant(df, y, v)
            if res is None:
                logger.info(f"  {v:30s} | SKIP (variant unavailable)")
                continue
            family_results[v] = res
            o = res["overall_mean"]
            lo = res["low_mean"]
            hi = res["high_mean"]
            retain = (o is not None and lo is not None and o <= -0.3 and lo <= 0.2)
            logger.info(f"  {v:30s} | Δ_overall {o:+.2f}%p | Δ_low {lo:+.2f}%p | Δ_high {hi:+.2f}%p | retain {'✓' if retain else '✗'}")
        results[family] = family_results

    # Retain logic per family
    retained = {}
    for family, family_results in results.items():
        candidates = [
            (v, res) for v, res in family_results.items()
            if res["overall_mean"] is not None and res["low_mean"] is not None
            and res["overall_mean"] <= -0.3 and res["low_mean"] <= 0.2
        ]
        # Sort by overall improvement
        candidates.sort(key=lambda x: x[1]["overall_mean"])
        # retain best 1 (or tied 2 if tie defined; here = within 0.1%p)
        retained_for_family = []
        if candidates:
            best = candidates[0]
            retained_for_family.append(best)
            for v, res in candidates[1:]:
                if res["overall_mean"] - best[1]["overall_mean"] < 0.1:
                    retained_for_family.append((v, res))
                    if len(retained_for_family) >= 2:
                        break
        retained[family] = [v for v, _ in retained_for_family]

    logger.info(f"\n=== Stage 1 retained variants (family 별 best 1, tied 2) ===")
    for family, vs in retained.items():
        logger.info(f"  {family:20s}: {vs if vs else 'NONE (모두 retain 기준 미달)'}")

    return {"results": results, "retained": retained}


def run():
    logger.info("=" * 80)
    logger.info("Progressive Sampling — Phase 0 holdout 봉인 + Phase 1 / Stage 1 exploration")
    logger.info("=" * 80)
    logger.info("Mini-prereg: docs/progressive_sampling_phase0_freeze_20260507.md")
    logger.info("코덱스 framing 톤: Stage 1 결과 = exploratory only / decision X")

    # Phase 0: holdout 봉인
    df_full = pd.read_parquet(STAGE4)
    df_full = ensure_derived_columns(df_full)
    holdout_set = lock_holdout(df_full)

    # Phase 1: Stage 1 exploration
    df_stage1 = pd.read_parquet(STAGE1)
    stage1_summary = stage1_explore(df_stage1)

    # Output
    summary = {
        "phase0": {
            "holdout_file": str(HOLDOUT_FILE.relative_to(ROOT)),
            "holdout_hash_file": str(HOLDOUT_HASH_FILE.relative_to(ROOT)),
            "holdout_artists": len(holdout_set),
            "holdout_seed": HOLDOUT_SEED,
            "holdout_ratio": HOLDOUT_RATIO,
            "hash": HOLDOUT_HASH_FILE.read_text().strip() if HOLDOUT_HASH_FILE.exists() else None,
        },
        "stage1": stage1_summary,
        "retain_rule": "Stage 1: Overall Δ ≤ -0.3%p AND Low Δ ≤ +0.2%p (exploratory only)",
    }
    out = RESULTS / "progressive_sampling_stage1.json"
    RESULTS.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nSaved: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    run()
