"""Stage 2 코덱스 권고 추가 테스트.

1. Forward selection (artist-group CV) — 변수 선택 빈도
2. Elastic Net (career_stage vs birth_year 자동 경쟁)
3. Interactions (제한적): log_area×tier, medium×tier, birth×year
4. Spline (artist_birth_year 3-knot restricted cubic spline)
5. Coefficient sign stability (fold별)
"""

from __future__ import annotations

import json
import logging
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "curated" / "stage2_500x50.parquet"
RESULTS = Path(__file__).parent / "results"

N_SEEDS = 30


def medium_family(c):
    if c == "oil":
        return "oil"
    if c == "acrylic":
        return "acrylic"
    if c in ("ink", "pigment", "watercolor"):
        return "paper"
    return "other"


def make_features(df):
    out = df.copy()
    out["log_area"] = np.log(out["area_cm2"].clip(lower=1))
    out["medium_family"] = out["medium_category"].apply(medium_family)
    out["year_made_centered"] = out["year_made"] - out["year_made"].mean()
    out["log_artist_total_works"] = np.log1p(out["artist_total_works"])
    out["log_solo"] = np.log1p(out["solo_count"])
    out["log_price"] = np.log(out["price_krw"].clip(lower=1))
    out["birth_year_centered"] = (
        out["artist_birth_year"] - out["artist_birth_year"].mean()
    )
    return out


def fit_predict(Xtr, ytr, Xte):
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    return Xte @ beta


def lao_eval(X, y, groups, n_seeds=30):
    """30-seed LAO holdout."""
    mdapes, r2s = [], []
    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        tr, te = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        Xte = X.iloc[te].values.astype(float)
        yte = y.iloc[te].values.astype(float)
        pred = fit_predict(Xtr, ytr, Xte)
        ape = np.abs(np.exp(pred) - np.exp(yte)) / np.exp(yte)
        mdapes.append(np.median(ape) * 100)
        ssr = ((yte - pred) ** 2).sum()
        sst = ((yte - yte.mean()) ** 2).sum()
        r2s.append(1 - ssr / sst if sst > 0 else 0)
    return float(np.mean(mdapes)), float(np.std(mdapes)), float(np.mean(r2s))


def build_X(df, cont, cat):
    parts = [df[cont].copy()] if cont else []
    if cat:
        parts.append(
            pd.get_dummies(df[cat].astype(str), drop_first=True).astype(float)
        )
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    return X


# ─────────────────────────────────────────────
# 1. Forward Selection (artist-group K-fold)
# ─────────────────────────────────────────────
def forward_selection(df, y, groups, candidates_cont, candidates_cat, k_folds=5):
    """Greedy forward selection — artist-group CV."""
    selected_cont, selected_cat = [], []
    pool_cont = list(candidates_cont)
    pool_cat = list(candidates_cat)
    history = []
    best_score = float("inf")

    while pool_cont or pool_cat:
        improvements = []
        # Try each candidate
        for col in pool_cont:
            X = build_X(df, selected_cont + [col], selected_cat)
            score, _, _ = lao_eval(X, y, groups, n_seeds=10)
            improvements.append((score, col, "cont"))
        for col in pool_cat:
            X = build_X(df, selected_cont, selected_cat + [col])
            score, _, _ = lao_eval(X, y, groups, n_seeds=10)
            improvements.append((score, col, "cat"))

        improvements.sort()
        best, col, kind = improvements[0]
        if best < best_score - 0.01:  # 0.01%p 이상 개선
            best_score = best
            if kind == "cont":
                selected_cont.append(col)
                pool_cont.remove(col)
            else:
                selected_cat.append(col)
                pool_cat.remove(col)
            history.append((len(selected_cont) + len(selected_cat), col, best))
        else:
            break

    return selected_cont, selected_cat, history


# ─────────────────────────────────────────────
# 2. Elastic Net (auto feature selection)
# ─────────────────────────────────────────────
def elastic_net_test(df, y, groups, candidates_cont, candidates_cat):
    """Elastic Net 으로 feature 자동 선택 + 30-seed 평균 채택률."""
    cat_dummies = pd.get_dummies(
        df[candidates_cat].astype(str), drop_first=True
    ).astype(float)
    X_full = pd.concat(
        [df[candidates_cont].copy(), cat_dummies], axis=1
    )
    feature_names = list(X_full.columns)

    selected_counts = Counter()
    for seed in range(42, 42 + N_SEEDS):
        gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        tr, _ = next(gss.split(X_full, y, groups))
        scaler = StandardScaler()
        Xtr_scaled = scaler.fit_transform(X_full.iloc[tr].values.astype(float))
        # Elastic Net 5-fold within train
        enet = ElasticNetCV(
            l1_ratio=[0.1, 0.5, 0.7, 0.9, 0.95, 0.99],
            cv=5,
            random_state=seed,
            max_iter=10000,
            n_jobs=1,
        )
        enet.fit(Xtr_scaled, y.iloc[tr].values.astype(float))
        # 0 이 아닌 coef 의 변수 카운트
        for name, coef in zip(feature_names, enet.coef_):
            if abs(coef) > 1e-6:
                selected_counts[name] += 1

    return [
        (name, count, count / N_SEEDS)
        for name, count in selected_counts.most_common()
    ]


# ─────────────────────────────────────────────
# 3. Interactions
# ─────────────────────────────────────────────
def test_interactions(df, y, groups):
    """제한적 interaction 추가 테스트."""
    base_cont = ["log_area", "year_made_centered", "career_stage"]
    base_cat = ["medium_family", "gallery_tier"]

    base_X = build_X(df, base_cont, base_cat)
    base_score, base_std, _ = lao_eval(base_X, y, groups)

    sets = {}
    sets["base"] = (base_score, base_std)

    # 1. log_area × gallery_tier
    X1 = base_X.copy()
    for tier in ["3", "4"]:
        col_name = f"area_x_tier{tier}"
        tier_dum = (df["gallery_tier"].astype(str) == tier).astype(float)
        X1[col_name] = df["log_area"].values * tier_dum.values
    sets["+area_x_tier"] = lao_eval(X1, y, groups)[:2]

    # 2. medium × gallery_tier
    X2 = base_X.copy()
    for med in ["oil", "paper", "other"]:
        for tier in ["3", "4"]:
            mask = (df["medium_family"] == med).astype(float) * (
                df["gallery_tier"].astype(str) == tier
            ).astype(float)
            X2[f"{med}_x_tier{tier}"] = mask.values
    sets["+medium_x_tier"] = lao_eval(X2, y, groups)[:2]

    # 3. birth_year × year_made
    base_with_birth = base_cont + ["birth_year_centered"]
    X3 = build_X(df, base_with_birth, base_cat)
    X3["birth_x_year"] = (
        df["birth_year_centered"].values * df["year_made_centered"].values
    )
    sets["+birth_x_year (with birth)"] = lao_eval(X3, y, groups)[:2]

    return sets


# ─────────────────────────────────────────────
# 4. Spline (artist_birth_year)
# ─────────────────────────────────────────────
def restricted_cubic_spline(x: np.ndarray, knots: np.ndarray) -> np.ndarray:
    """3-knot restricted cubic spline → 2개 추가 변수 반환."""
    k = len(knots)
    assert k >= 3
    x = x.astype(float)
    # Last knot 차이로 정규화
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


def test_spline(df, y, groups):
    base_cont = ["log_area", "year_made_centered", "career_stage"]
    base_cat = ["medium_family", "gallery_tier"]

    sets = {}
    base_X = build_X(df, base_cont, base_cat)
    sets["base"] = lao_eval(base_X, y, groups)[:2]

    # birth_year spline
    bx = df["artist_birth_year"].values
    knots = np.percentile(bx, [10, 50, 90])
    spline = restricted_cubic_spline(bx, knots)

    X_spline = build_X(df, base_cont, base_cat).copy()
    X_spline["birth_spline_1"] = spline[:, 0]
    sets["+birth_spline (3-knot)"] = lao_eval(X_spline, y, groups)[:2]

    # year_made spline
    yx = df["year_made"].values
    knots_y = np.percentile(yx, [10, 50, 90])
    spline_y = restricted_cubic_spline(yx, knots_y)
    X_spline_y = build_X(df, base_cont, base_cat).copy()
    X_spline_y["year_spline_1"] = spline_y[:, 0]
    sets["+year_spline (3-knot)"] = lao_eval(X_spline_y, y, groups)[:2]

    return sets


# ─────────────────────────────────────────────
# 5. Coefficient sign stability
# ─────────────────────────────────────────────
def coef_sign_stability(df, y, groups, cont, cat, n_seeds=30):
    X = build_X(df, cont, cat)
    feature_names = list(X.columns)
    sign_history = {fn: [] for fn in feature_names}
    coef_history = {fn: [] for fn in feature_names}

    for seed in range(42, 42 + n_seeds):
        gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
        tr, _ = next(gss.split(X, y, groups))
        Xtr = X.iloc[tr].values.astype(float)
        ytr = y.iloc[tr].values.astype(float)
        beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
        for fn, b in zip(feature_names, beta):
            sign_history[fn].append(np.sign(b))
            coef_history[fn].append(b)

    stability = {}
    for fn in feature_names:
        signs = sign_history[fn]
        n_pos = sum(1 for s in signs if s > 0)
        n_neg = sum(1 for s in signs if s < 0)
        consistency = max(n_pos, n_neg) / len(signs) * 100
        stability[fn] = {
            "mean_coef": float(np.mean(coef_history[fn])),
            "std_coef": float(np.std(coef_history[fn])),
            "sign_consistency_pct": float(consistency),
        }
    return stability


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def run():
    df = pd.read_parquet(DATA)
    df_feat = make_features(df)
    y = df_feat["log_price"]
    groups = df_feat["artist_slug"].astype(str).to_numpy()

    summary = {}

    logger.info("=" * 80)
    logger.info("1. Forward Selection (artist-group CV)")
    logger.info("=" * 80)
    candidates_cont = [
        "log_area",
        "year_made_centered",
        "career_stage",
        "career_age",
        "birth_year_centered",
        "log_artist_total_works",
        "log_solo",
        "ln_followers",
        "for_sale_ratio",
    ]
    candidates_cat = [
        "medium_family",
        "gallery_tier",
        "has_seoul",
        "has_international",
    ]
    sel_cont, sel_cat, history = forward_selection(
        df_feat, y, groups, candidates_cont, candidates_cat
    )
    logger.info(f"\n선택된 continuous: {sel_cont}")
    logger.info(f"선택된 categorical: {sel_cat}")
    logger.info("\n선택 history (k → 추가 변수 → MdAPE):")
    for k, col, score in history:
        logger.info(f"  step {k}: +{col} → {score:.2f}%")
    summary["forward_selection"] = {
        "selected_cont": sel_cont,
        "selected_cat": sel_cat,
        "history": [(k, c, s) for k, c, s in history],
    }

    logger.info("\n" + "=" * 80)
    logger.info("2. Elastic Net 변수 채택률 (30-seed)")
    logger.info("=" * 80)
    enet_results = elastic_net_test(df_feat, y, groups, candidates_cont, candidates_cat)
    logger.info("\n채택률 (>50% 이상 표시):")
    for name, count, pct in enet_results:
        if pct > 0.50:
            logger.info(f"  {name}: {count}/{N_SEEDS} ({pct * 100:.0f}%)")
    summary["elastic_net"] = [
        {"feature": n, "count": c, "pct": p} for n, c, p in enet_results
    ]

    logger.info("\n" + "=" * 80)
    logger.info("3. Interactions (제한적)")
    logger.info("=" * 80)
    inter_results = test_interactions(df_feat, y, groups)
    for name, (m, s) in inter_results.items():
        logger.info(f"  {name}: MdAPE={m:.2f}±{s:.2f}%")
    summary["interactions"] = {
        n: {"mdape_mean": m, "mdape_std": s}
        for n, (m, s) in inter_results.items()
    }

    logger.info("\n" + "=" * 80)
    logger.info("4. Spline (3-knot restricted cubic)")
    logger.info("=" * 80)
    spline_results = test_spline(df_feat, y, groups)
    for name, (m, s) in spline_results.items():
        logger.info(f"  {name}: MdAPE={m:.2f}±{s:.2f}%")
    summary["spline"] = {
        n: {"mdape_mean": m, "mdape_std": s}
        for n, (m, s) in spline_results.items()
    }

    logger.info("\n" + "=" * 80)
    logger.info("5. N6 Coefficient sign stability (30-seed)")
    logger.info("=" * 80)
    stability_n6 = coef_sign_stability(
        df_feat,
        y,
        groups,
        cont=["log_area", "year_made_centered", "artist_birth_year"],
        cat=["medium_family", "gallery_tier"],
    )
    logger.info(f"\n{'feature':<35} {'mean β':>10} {'std β':>10} {'부호 일관 %':>14}")
    for fn, s in stability_n6.items():
        logger.info(
            f"{fn:<35} {s['mean_coef']:>10.4f} {s['std_coef']:>10.4f} "
            f"{s['sign_consistency_pct']:>10.1f}%"
        )
    summary["n6_sign_stability"] = stability_n6

    with (RESULTS / "stage2_advanced_tests.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(
        f"\nSaved: {(RESULTS / 'stage2_advanced_tests.json').relative_to(ROOT)}"
    )


if __name__ == "__main__":
    run()
