"""Stage 3 — 코덱스 P1 5건 통합 실험.

1. Spline (log_area / birth_year / year_made restricted cubic)
2. Interaction (size × medium, period × medium)
3. Artist FE / Gallery FE
4. 2,903 전체 모집단 확장
5. Ridge / Elastic Net 안정화

비교 대상: F4 baseline (24.59% MdAPE)
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV, LinearRegression, ElasticNetCV
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA_STAGE3 = ROOT / "data" / "curated" / "stage3_1000x100.parquet"
DATA_FULL_PARQUET = ROOT / "data" / "primary_market_dataset.parquet"
RESULTS = Path(__file__).parent / "results"

N_SEEDS = 30
TEST_SIZE = 0.20


def make_features_full(df):
    """확장 모집단용 features."""
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["birth_year_centered"] = (
        out["artist_birth_year"] - out["artist_birth_year"].mean()
    )
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_followers"] = np.log1p(np.maximum(out["ln_followers"], 0))
    out["log_solo"] = np.log1p(out["solo_count"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    return out


def restricted_cubic_spline(x: np.ndarray, knots: np.ndarray) -> np.ndarray:
    """3-knot RCS → 1 추가 컬럼."""
    k = len(knots)
    last_k = knots[-1]
    pre_last_k = knots[-2]
    denom = (last_k - knots[0]) ** 2
    out = []
    for i in range(k - 2):
        ti = knots[i]
        cube = lambda u: np.maximum(u, 0) ** 3
        spline = (
            cube(x - ti)
            - cube(x - pre_last_k) * (last_k - ti) / (last_k - pre_last_k)
            + cube(x - last_k) * (pre_last_k - ti) / (last_k - pre_last_k)
        )
        out.append(spline / denom)
    return np.column_stack(out)


def medium_family(c):
    if c == "oil":
        return "oil"
    if c == "acrylic":
        return "acrylic"
    if c in ("ink", "pigment", "watercolor"):
        return "paper"
    return "other"


def build_X(
    df: pd.DataFrame,
    *,
    cont: list[str],
    cat: list[str] | None = None,
    splines: list[tuple[str, list[float]]] | None = None,
    interactions: list[tuple[str, str]] | None = None,
    artist_fe: bool = False,
    medium_fam: bool = False,
) -> pd.DataFrame:
    parts = []
    if cont:
        parts.append(df[cont].copy())
    if medium_fam:
        df = df.copy()
        df["medium_family"] = df["medium_category"].apply(medium_family)
    if cat:
        cat_df = pd.get_dummies(
            df[cat].astype(str), drop_first=True
        ).astype(float)
        parts.append(cat_df)
    X = pd.concat(parts, axis=1) if parts else pd.DataFrame()

    # Splines
    if splines:
        for col, knots in splines:
            sp = restricted_cubic_spline(df[col].values.astype(float), np.array(knots))
            for i in range(sp.shape[1]):
                X[f"{col}_spline_{i+1}"] = sp[:, i]

    # Interactions (continuous × categorical)
    if interactions:
        for c1, c2 in interactions:
            if c2 in df.columns and not pd.api.types.is_numeric_dtype(df[c2]):
                cat_dum = pd.get_dummies(
                    df[c2].astype(str), prefix=f"{c1}_x_{c2}", drop_first=True
                ).astype(float)
                for col in cat_dum.columns:
                    X[col] = df[c1].values.astype(float) * cat_dum[col].values

    # Artist FE
    if artist_fe:
        artist_dum = pd.get_dummies(
            df["artist_slug"].astype(str), prefix="artist", drop_first=True
        ).astype(float)
        X = pd.concat([X, artist_dum], axis=1)

    X.insert(0, "const", 1.0)
    return X


def fit_predict_ols(Xtr, ytr, Xte):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return Xte @ beta


def fit_predict_ridge(Xtr, ytr, Xte, alphas=(0.01, 0.1, 1.0, 10.0, 100.0)):
    """Ridge with CV + standardization."""
    scaler = StandardScaler()
    Xtr_s = scaler.fit_transform(Xtr[:, 1:])  # exclude const
    Xte_s = scaler.transform(Xte[:, 1:])
    model = RidgeCV(alphas=alphas, cv=5)
    model.fit(Xtr_s, ytr)
    pred = model.predict(Xte_s)
    return pred


def metrics(yte, pred):
    ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
    return {
        "mdape": float(np.median(ape) * 100),
        "w30": float((ape <= 0.30).mean() * 100),
        "w50": float((ape <= 0.50).mean() * 100),
    }


def lao_eval(
    X: pd.DataFrame,
    y: pd.Series,
    groups: np.ndarray,
    n_seeds: int,
    use_ridge: bool = False,
) -> dict:
    mdapes, w30s, w50s = [], [], []
    X_arr = X.values.astype(float)
    y_arr = y.values.astype(float)
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr, ytr = X_arr[tr], y_arr[tr]
        Xte, yte = X_arr[te], y_arr[te]
        if use_ridge:
            pred = fit_predict_ridge(Xtr, ytr, Xte)
        else:
            pred = fit_predict_ols(Xtr, ytr, Xte)
        m = metrics(yte, pred)
        mdapes.append(m["mdape"])
        w30s.append(m["w30"])
        w50s.append(m["w50"])
    return {
        "mdape_mean": float(np.mean(mdapes)),
        "mdape_std": float(np.std(mdapes)),
        "w30_mean": float(np.mean(w30s)),
        "w50_mean": float(np.mean(w50s)),
    }


# ─────────────────────────────────────────────
# Main experiments
# ─────────────────────────────────────────────
def run():
    summary = {}

    # 1. Stage 3 (1378/100) baseline
    df3 = pd.read_parquet(DATA_STAGE3)
    df3_feat = make_features_full(df3)
    y3 = df3_feat["log_price"]
    g3 = df3_feat["artist_slug"].astype(str).to_numpy()

    logger.info("=" * 80)
    logger.info("Baseline — F4 (3 features OLS)")
    logger.info("=" * 80)
    X_base = build_X(
        df3_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
    )
    res_base = lao_eval(X_base, y3, g3, N_SEEDS)
    logger.info(
        f"  F4 baseline: MdAPE {res_base['mdape_mean']:.2f}±{res_base['mdape_std']:.2f}% / "
        f"W30 {res_base['w30_mean']:.1f} / W50 {res_base['w50_mean']:.1f}"
    )
    summary["baseline_f4"] = res_base

    # 2. F4 + Spline (log_area)
    logger.info("\n" + "=" * 80)
    logger.info("P1-1. Spline (log_area RCS)")
    logger.info("=" * 80)
    knots_area = np.percentile(df3_feat["log_area"].values, [10, 50, 90]).tolist()
    X_spline_area = build_X(
        df3_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
        splines=[("log_area", knots_area)],
    )
    res = lao_eval(X_spline_area, y3, g3, N_SEEDS)
    logger.info(f"  + log_area spline: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p1_spline_area"] = res

    knots_birth = np.percentile(df3_feat["birth_year_centered"].values, [10, 50, 90]).tolist()
    X_spline_both = build_X(
        df3_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
        splines=[("log_area", knots_area), ("birth_year_centered", knots_birth)],
    )
    res = lao_eval(X_spline_both, y3, g3, N_SEEDS)
    logger.info(f"  + log_area + birth spline: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p1_spline_both"] = res

    # 3. F4 + Interaction
    logger.info("\n" + "=" * 80)
    logger.info("P1-2. Interaction (size × medium)")
    logger.info("=" * 80)
    X_inter = build_X(
        df3_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
        cat=["medium_category"],
        interactions=[("log_area", "medium_category")],
    )
    res = lao_eval(X_inter, y3, g3, N_SEEDS)
    logger.info(f"  + size × medium: MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p1_interaction"] = res

    # 4. F4 + Spline + Interaction + Ridge
    logger.info("\n" + "=" * 80)
    logger.info("P1-5. Spline + Interaction + Ridge (안정화)")
    logger.info("=" * 80)
    X_combined = build_X(
        df3_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
        cat=["medium_category"],
        splines=[("log_area", knots_area), ("birth_year_centered", knots_birth)],
        interactions=[("log_area", "medium_category")],
    )
    res = lao_eval(X_combined, y3, g3, N_SEEDS, use_ridge=False)
    logger.info(f"  combined OLS:   MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}% (k={X_combined.shape[1]-1})")
    summary["p1_combined_ols"] = res

    res_ridge = lao_eval(X_combined, y3, g3, N_SEEDS, use_ridge=True)
    logger.info(f"  combined Ridge: MdAPE {res_ridge['mdape_mean']:.2f}±{res_ridge['mdape_std']:.2f}%")
    summary["p1_combined_ridge"] = res_ridge

    # 5. 2,903 전체 모집단 확장
    logger.info("\n" + "=" * 80)
    logger.info("P1-4. 전체 모집단 확장 (2,903 records)")
    logger.info("=" * 80)

    # 전체 모집단 = build_curated 의 cleansing 룰 통과 후 전체
    # 직접 적용 (script 의 load_eligible 룰 동일)
    df_all = pd.read_parquet(DATA_FULL_PARQUET)
    df_all = df_all[(df_all["is_excluded_for_training"] == 0) & (df_all["price_krw"] > 1)]
    required = [
        "artist_slug", "area_cm2", "medium_category", "year_made",
        "gallery_tier", "price_krw", "artist_birth_year", "career_age",
        "image_url",
    ]
    for col in required:
        s = df_all[col].astype(str).str.strip()
        df_all = df_all[
            df_all[col].notna() & (s != "") & (s.str.lower() != "nan")
        ]
    df_all = df_all[df_all["area_cm2"] > 0]
    df_all = df_all[(df_all["year_made"] >= 1900) & (df_all["year_made"] <= 2026)]
    medium_str = df_all["medium"].astype(str).str.strip()
    df_all = df_all[~medium_str.str.fullmatch(r"\d+(\.\d+)?", na=False)]
    for col in ["medium_l1", "support_l1", "support_leaf"]:
        s = df_all[col].astype(str).str.strip()
        df_all = df_all[df_all[col].notna() & (s != "")]
    for col in ["mediums_json", "supports_json"]:
        s = df_all[col].astype(str).str.strip()
        df_all = df_all[(s != "") & (s != "[]")]
    df_all["title"] = df_all["title"].astype(str).str.strip()
    df_all = df_all[df_all["title"].str.contains(r"[a-zA-Z가-힣]", regex=True, na=False)]
    df_all = df_all[(df_all["year_made"] - df_all["artist_birth_year"]) >= 15]
    df_all = df_all[df_all["aspect_ratio"].between(0.1, 10)]
    df_all = df_all.drop_duplicates(
        subset=["artist_slug", "title", "year_made", "area_cm2", "medium_category"],
        keep="first"
    ).reset_index(drop=True)
    counts = df_all["artist_slug"].value_counts()
    df_all = df_all[df_all["artist_slug"].isin(counts[counts >= 10].index)].reset_index(drop=True)

    logger.info(f"  전체 모집단 (rule-passed): {len(df_all)} / artists {df_all['artist_slug'].nunique()}")

    df_all_feat = make_features_full(df_all)
    y_all = df_all_feat["log_price"]
    g_all = df_all_feat["artist_slug"].astype(str).to_numpy()

    # F4 baseline on full
    X_full_base = build_X(
        df_all_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
    )
    res = lao_eval(X_full_base, y_all, g_all, N_SEEDS)
    logger.info(f"  F4 baseline (전체): MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p1_full_f4"] = res

    # F4 + spline + interaction + ridge on full
    knots_area_full = np.percentile(df_all_feat["log_area"].values, [10, 50, 90]).tolist()
    knots_birth_full = np.percentile(
        df_all_feat["birth_year_centered"].values, [10, 50, 90]
    ).tolist()
    X_full_combined = build_X(
        df_all_feat,
        cont=["log_area", "birth_year_centered", "log_artist_total_works"],
        cat=["medium_category"],
        splines=[
            ("log_area", knots_area_full),
            ("birth_year_centered", knots_birth_full),
        ],
        interactions=[("log_area", "medium_category")],
    )
    res = lao_eval(X_full_combined, y_all, g_all, N_SEEDS, use_ridge=True)
    logger.info(f"  combined Ridge (전체): MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}% (k={X_full_combined.shape[1]-1})")
    summary["p1_full_combined_ridge"] = res

    # 6. + 추가 변수 (followers, solo) on full
    X_full_extended = build_X(
        df_all_feat,
        cont=[
            "log_area", "birth_year_centered", "log_artist_total_works",
            "log_followers", "log_solo",
        ],
        cat=["medium_category"],
        splines=[
            ("log_area", knots_area_full),
            ("birth_year_centered", knots_birth_full),
        ],
        interactions=[("log_area", "medium_category")],
    )
    res = lao_eval(X_full_extended, y_all, g_all, N_SEEDS, use_ridge=True)
    logger.info(f"  + followers/solo (전체): MdAPE {res['mdape_mean']:.2f}±{res['mdape_std']:.2f}%")
    summary["p1_full_extended"] = res

    # Save
    with (RESULTS / "stage3_p1_improvements.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage3_p1_improvements.json').relative_to(ROOT)}"
    )

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("최종 비교")
    logger.info("=" * 80)
    logger.info(f"{'Method':<40} {'MdAPE':>14} {'개선':>10}")
    base_mdape = summary["baseline_f4"]["mdape_mean"]
    for name, m in summary.items():
        diff = m["mdape_mean"] - base_mdape
        logger.info(
            f"{name:<40} {m['mdape_mean']:>6.2f}±{m['mdape_std']:>4.2f}% "
            f"{diff:>+5.2f}%p"
        )


if __name__ == "__main__":
    run()
