"""Track 3 PR18 — Branch × Depth feature 12 조합 매트릭스 + multi-seed.

Codex 권고 반영:
  - PR17 caveat 1: LGB_PARAMS_SMALL의 min_data_in_leaf를 75 유지(보수적)
  - PR17 caveat 3: ape_array 저장 (재현성)
  - 분기 모델에서 has_depth degenerate 처리 (effective_variant 표시)
  - multi-seed (5 seeds) → 1회 결과 우연성 제거
  - 12 cells 모두 보여주되 effective 동일한 그룹 명시

차원:
  Model variant (4): V0/V1/V2/V3
  Depth variant (3): cm_only / has_only / both
  Seeds (5)
  Slice: warm/cold × 2D/3D

핵심 통찰 (Codex):
  V0 (단일): cm_only ≠ has_only ≠ both (3 unique 학습)
  V1/V2/V3 (분기):
    cm_only ≡ both (branch 내 has_depth는 constant → 무시됨)
    has_only ≡ no_depth_signal (branch 내 has_depth 도 constant → depth signal 0)
  → 분기 모델당 2 unique = V1+V2+V3 × 2 = 6 unique
  → 총 9 unique 학습 × 5 seeds = 45 학습

평가: train 내부 mini hold-out (release_split design 축소판). release_split test 사용하지 않음.

산출물: data/track3_pr18_matrix_results.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_pr18_matrix_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEEDS = [42, 123, 7, 2024, 999]
N_COLD_MINI = 100
WARM_PER_ARTIST = 1

BASE_NO_DEPTH = ["medium_category", "support_category",
                  "log_area", "estimated_ho", "orientation",
                  "medium_ho_bucket", "aspect_ratio"]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

# 보수적 hyperparam (Codex caveat 1 fix: min_data_in_leaf 75 유지)
# Codex 코드 리뷰 caveat fix:
#   - deterministic=True: thread 순서에 따른 미세 변동 제거
#   - num_threads=1: 결정적 학습 (속도 trade-off)
#   - bagging_seed / feature_fraction_seed / data_random_seed: 모든 random 경로에 seed 전달
LGB_PARAMS_FULL = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
}
LGB_PARAMS_SMALL = {
    **LGB_PARAMS_FULL,
    "num_leaves": 64, "min_data_in_leaf": 75,
    "feature_fraction": 0.95, "bagging_fraction": 0.95,
}

# Depth feature mapping: (model_variant, depth_variant) → effective key
# 분기 모델은 has_depth가 branch 내 constant라 "depth_active" / "no_depth" 둘로 collapse
EFFECTIVE = {
    ("V0", "cm_only"): "V0_cm",
    ("V0", "has_only"): "V0_has",
    ("V0", "both"): "V0_both",
    ("V1", "cm_only"): "V1_depth_active",
    ("V1", "has_only"): "V1_no_depth",
    ("V1", "both"): "V1_depth_active",
    ("V2", "cm_only"): "V2_depth_active",
    ("V2", "has_only"): "V2_no_depth",
    ("V2", "both"): "V2_depth_active",
    ("V3", "cm_only"): "V3_depth_active",
    ("V3", "has_only"): "V3_no_depth",
    ("V3", "both"): "V3_depth_active",
}


def add_depth_features(df):
    df = df.copy()
    df["has_depth"] = (df["depth_cm"] > 0).astype(int)
    return df


def make_features(df, artist_counts, count_col="artist_works_log"):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df[count_col] = np.log1p(df[ARTIST_COL].map(artist_counts).fillna(0))
    return df


def build_lad(features, cat_cols):
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", preprocess),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def train_lgb(df_train, features, cat_cols, params, seed):
    # Codex fix: 모든 random 경로에 명시적 seed 전달 + deterministic
    p = {**params,
         "seed": seed,
         "bagging_seed": seed,
         "feature_fraction_seed": seed,
         "data_random_seed": seed,
         "drop_seed": seed,
         "objective_seed": seed}
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    va_idx = perm[:cut]; tr_idx = perm[cut:]
    X_tr = to_cat(df_train.iloc[tr_idx], features, cat_cols)
    X_va = to_cat(df_train.iloc[va_idx], features, cat_cols)
    y_tr = df_train.iloc[tr_idx][TARGET].values
    y_va = df_train.iloc[va_idx][TARGET].values
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_cols)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=cat_cols, reference=tr_set)
    return lgb.train(p, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def compute_metrics(y_true_ln, y_pred_ln):
    """PR17과 동일 schema 보장 (Codex caveat 4 fix)."""
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
        "ape_array": ape.tolist(),
    }


def setup_mini_holdout(train_df, seed):
    """Train 내부 mini hold-out 생성.

    명칭상 'stratified'지만 실제로는 작가 작품수 구간 (low/mid/high)에 대한
    **quota 샘플링**임 (Codex caveat 3). 가격대 / 2D-3D 비율 / medium 등은 통제하지 않음.

    Stability:
      - input row order 의존성 제거 위해 train_df를 (artist, source_listing_id 또는 index) 기준
        stable sort 한 뒤 진행 (Codex caveat 2 fix).
      - 각 strata의 artist 풀도 정렬해서 rng.choice 결과가 row order에 의존 안 하게.

    Returns: (mini_train, warm_mini, cold_mini) — 각각 is_3d 컬럼 추가됨.
    """
    # Stable sort: artist_name_ko + price (또는 ln_price) 로 정렬해 row order 의존성 제거
    train_df = train_df.sort_values(
        by=[ARTIST_COL, "ln_price_krw_unified", "log_area"],
        kind="mergesort",
    ).reset_index(drop=True)

    rng = np.random.default_rng(seed)
    artist_counts = train_df.groupby(ARTIST_COL).size().sort_values()
    # artists 풀을 정렬해서 rng.choice의 결과가 dict 순서에 의존 안 하게
    artists_low = sorted([a for a in artist_counts.index if artist_counts[a] <= 2])
    artists_mid = sorted([a for a in artist_counts.index if 3 <= artist_counts[a] <= 10])
    artists_high = sorted([a for a in artist_counts.index if artist_counts[a] > 10])

    n_low = int(N_COLD_MINI * 0.5)
    n_mid = int(N_COLD_MINI * 0.3)
    n_high = N_COLD_MINI - n_low - n_mid
    # 각 strata 풀 크기 보장 (현재 데이터에선 low 516 / mid 820 / high 796 모두 충분)
    assert len(artists_low) >= n_low, f"low strata 부족: {len(artists_low)} < {n_low}"
    assert len(artists_mid) >= n_mid, f"mid strata 부족: {len(artists_mid)} < {n_mid}"
    assert len(artists_high) >= n_high, f"high strata 부족: {len(artists_high)} < {n_high}"

    cold_artists = (
        list(rng.choice(artists_low, size=n_low, replace=False)) +
        list(rng.choice(artists_mid, size=n_mid, replace=False)) +
        list(rng.choice(artists_high, size=n_high, replace=False))
    )
    assert len(cold_artists) == N_COLD_MINI, f"cold quota 미충족: {len(cold_artists)}"
    cold_set = set(cold_artists)

    cold_mini = train_df[train_df[ARTIST_COL].isin(cold_set)].copy()
    remaining = train_df[~train_df[ARTIST_COL].isin(cold_set)].copy()
    rem_counts = remaining.groupby(ARTIST_COL).size()
    multi_artists = sorted(rem_counts[rem_counts >= 2].index.tolist())  # sorted for stability
    warm_idx = []
    for artist in multi_artists:
        rows = remaining[remaining[ARTIST_COL] == artist]
        sampled = rng.choice(rows.index.values, size=WARM_PER_ARTIST, replace=False)
        warm_idx.extend(sampled.tolist())
    warm_mini = remaining.loc[warm_idx].copy()
    mini_train = remaining.drop(warm_idx).copy()
    for d in [mini_train, warm_mini, cold_mini]:
        d["is_3d"] = (d["depth_cm"] > 0).astype(int)
    return mini_train, warm_mini, cold_mini


def get_depth_feats_v0(depth_variant):
    """단일 V0: 3 가지 모두 의미."""
    if depth_variant == "cm_only":
        return ["depth_cm"]
    elif depth_variant == "has_only":
        return ["has_depth"]
    elif depth_variant == "both":
        return ["depth_cm", "has_depth"]


def predict_cold_unified(mini_train, test, depth_variant, seed):
    depth_feats = get_depth_feats_v0(depth_variant)
    feats = BASE_NO_DEPTH + depth_feats + ["artist_works_log"]
    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts)
    te = make_features(test, counts)
    model = build_lad(feats, BASE_CAT)
    model.fit(tr[feats], tr[TARGET].values)
    return model.predict(te[feats])


def predict_warm_unified(mini_train, test, depth_variant, seed):
    depth_feats = get_depth_feats_v0(depth_variant)
    feats = BASE_NO_DEPTH + depth_feats + ["artist_works_log", ARTIST_COL]
    cat = BASE_CAT + [ARTIST_COL]
    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts)
    te = make_features(test, counts)
    model = train_lgb(tr, feats, cat, LGB_PARAMS_FULL, seed)
    return model.predict(to_cat(te, feats, cat))


def predict_cold_branched(mini_train, test, depth_active, seed):
    """분기 Cold (V2/V3). depth_active=True면 3D branch에 depth_cm 추가, False면 둘 다 no depth."""
    pred = np.zeros(len(test))
    for is3d in [0, 1]:
        tr = mini_train[mini_train["is_3d"] == is3d].copy()
        te_mask = (test["is_3d"] == is3d).values
        te = test[te_mask].copy()
        if len(te) == 0:
            continue
        branch_counts = tr[ARTIST_COL].value_counts().to_dict()
        depth_extra = ["depth_cm"] if (depth_active and is3d) else []
        feats = BASE_NO_DEPTH + depth_extra + ["artist_works_log_branch"]
        tr_f = make_features(tr, branch_counts, count_col="artist_works_log_branch")
        te_f = make_features(te, branch_counts, count_col="artist_works_log_branch")
        model = build_lad(feats, BASE_CAT)
        model.fit(tr_f[feats], tr_f[TARGET].values)
        pred[te_mask] = model.predict(te_f[feats])
    return pred


def predict_warm_branched(mini_train, test, depth_active, seed):
    """분기 Warm (V1/V3) + 라우팅 fallback. depth_active 동일.

    Contract (Codex caveat fix):
      test 의 모든 작가는 mini_train (global)에 ≥1건 있어야 함 (global_seen).
      만약 global_unseen이 섞이면 함수가 조용히 branch Cold로 보내버리므로
      assert로 명시적 차단. 호출자 (run_cell)는 warm_mini만 넘겨야 함.
    """
    global_artists = set(mini_train[ARTIST_COL])
    test_artists = set(test[ARTIST_COL])
    unseen = test_artists - global_artists
    assert not unseen, (
        f"predict_warm_branched는 global_seen artists만 받음. "
        f"unseen {len(unseen)}명 발견: {sorted(unseen)[:5]}..."
    )
    pred = np.full(len(test), np.nan)
    test = test.reset_index(drop=True).copy()
    test["_orig_idx"] = np.arange(len(test))

    branch_warm_models = {}
    branch_cold_fallback = {}
    for is3d in [0, 1]:
        tr = mini_train[mini_train["is_3d"] == is3d].copy()
        branch_counts = tr[ARTIST_COL].value_counts().to_dict()
        depth_extra = ["depth_cm"] if (depth_active and is3d) else []
        feats_w = BASE_NO_DEPTH + depth_extra + ["artist_works_log_branch", ARTIST_COL]
        cat_w = BASE_CAT + [ARTIST_COL]
        feats_c = BASE_NO_DEPTH + depth_extra + ["artist_works_log_branch"]
        tr_f = make_features(tr, branch_counts, count_col="artist_works_log_branch")
        params = LGB_PARAMS_SMALL if is3d == 0 else LGB_PARAMS_FULL
        warm_m = train_lgb(tr_f, feats_w, cat_w, params, seed)
        cold_m = build_lad(feats_c, BASE_CAT)
        cold_m.fit(tr_f[feats_c], tr_f[TARGET].values)
        branch_warm_models[is3d] = (warm_m, feats_w, cat_w, branch_counts)
        branch_cold_fallback[is3d] = (cold_m, feats_c, branch_counts)

    for is3d in [0, 1]:
        te_branch = test[test["is_3d"] == is3d].copy()
        if len(te_branch) == 0:
            continue
        warm_m, feats_w, cat_w, branch_counts = branch_warm_models[is3d]
        cold_m, feats_c, _ = branch_cold_fallback[is3d]
        te_feat = make_features(te_branch, branch_counts, count_col="artist_works_log_branch")
        seen_mask = te_feat[ARTIST_COL].map(branch_counts).fillna(0) > 0
        if seen_mask.any():
            seen_rows = te_feat[seen_mask]
            preds_w = warm_m.predict(to_cat(seen_rows, feats_w, cat_w))
            for i, idx in enumerate(seen_rows["_orig_idx"]):
                pred[idx] = preds_w[i]
        if (~seen_mask).any():
            unseen_rows = te_feat[~seen_mask]
            preds_c = cold_m.predict(unseen_rows[feats_c])
            for i, idx in enumerate(unseen_rows["_orig_idx"]):
                pred[idx] = preds_c[i]
    return pred


def run_cell(model_variant, depth_variant, mini_train, warm_mini, cold_mini, seed):
    """한 (V, D) 조합 실행."""
    depth_active = depth_variant in ("cm_only", "both")  # 분기 모델용

    if model_variant == "V0":
        warm_pred = predict_warm_unified(mini_train, warm_mini, depth_variant, seed)
        cold_pred = predict_cold_unified(mini_train, cold_mini, depth_variant, seed)
    elif model_variant == "V1":
        warm_pred = predict_warm_branched(mini_train, warm_mini, depth_active, seed)
        cold_pred = predict_cold_unified(mini_train, cold_mini, depth_variant, seed)
        # V1에서 Cold는 단일이라 depth_variant 그대로 의미 — 단 분기 가설은 Cold 단일이므로 V0의 Cold와 같은 효과
    elif model_variant == "V2":
        warm_pred = predict_warm_unified(mini_train, warm_mini, depth_variant, seed)
        cold_pred = predict_cold_branched(mini_train, cold_mini, depth_active, seed)
    elif model_variant == "V3":
        warm_pred = predict_warm_branched(mini_train, warm_mini, depth_active, seed)
        cold_pred = predict_cold_branched(mini_train, cold_mini, depth_active, seed)
    return warm_pred, cold_pred


def paired_compare(ape_b, ape_v):
    ape_b = np.array(ape_b); ape_v = np.array(ape_v)
    delta = ape_v - ape_b
    return {
        "delta_median_ape": float(np.median(delta)),
        "win_rate_variant": float((ape_v < ape_b).mean()),
        "catastrophic_2x": float((ape_v > 2 * ape_b).mean()),
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR18 — Branch × Depth 12조합 매트릭스 × 5 seeds")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    train = add_depth_features(train)
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    # results[seed][cell_key] = {"warm": {...}, "cold": {...}}
    all_results = {}
    for seed in SEEDS:
        logger.info(f"\n=== Seed {seed} ===")
        mini_train, warm_mini, cold_mini = setup_mini_holdout(train, seed=seed)
        logger.info(f"  mini_train {len(mini_train):,} / warm_mini {len(warm_mini):,} "
                    f"/ cold_mini {len(cold_mini):,}")
        seed_results = {}
        for model_variant in ["V0", "V1", "V2", "V3"]:
            for depth_variant in ["cm_only", "has_only", "both"]:
                cell_key = f"{model_variant}_{depth_variant}"
                eff = EFFECTIVE[(model_variant, depth_variant)]
                logger.info(f"  [{cell_key} → effective={eff}] 학습")
                warm_pred, cold_pred = run_cell(
                    model_variant, depth_variant,
                    mini_train, warm_mini, cold_mini, seed
                )
                warm_m = compute_metrics(warm_mini[TARGET].values, warm_pred)
                cold_m = compute_metrics(cold_mini[TARGET].values, cold_pred)
                warm_m["is_3d"] = warm_mini["is_3d"].tolist()
                cold_m["is_3d"] = cold_mini["is_3d"].tolist()
                seed_results[cell_key] = {
                    "effective": eff,
                    "warm": warm_m,
                    "cold": cold_m,
                }
        all_results[seed] = seed_results

    # 출력
    print()
    print("=" * 100)
    print("📊 PR18 — Matrix 결과 (5 seeds 평균, train 내부 mini hold-out)")
    print("=" * 100)

    cells = [f"{v}_{d}" for v in ["V0", "V1", "V2", "V3"] for d in ["cm_only", "has_only", "both"]]

    def agg_metric(cell, slice_name, metric):
        vals = [all_results[s][cell][slice_name][metric] for s in SEEDS]
        return float(np.mean(vals)), float(np.std(vals))

    print()
    print(f"{'Cell':<14} {'Effective':<20} {'Warm med_APE (mean±std)':>27} {'Cold med_APE (mean±std)':>27}")
    print("-" * 92)
    for cell in cells:
        eff = all_results[SEEDS[0]][cell]["effective"]
        wm, ws = agg_metric(cell, "warm", "median_ape")
        cm, cs = agg_metric(cell, "cold", "median_ape")
        marker = ""
        if "no_depth" in eff and cell.endswith("has_only"):
            marker = " (=no_depth_signal)"
        elif "depth_active" in eff and cell.endswith("both"):
            marker = " (≡cm_only)"
        print(f"{cell:<14} {eff:<20} {wm:>10.4f} ± {ws:>5.4f}      {cm:>10.4f} ± {cs:>5.4f}{marker}")

    # Paired vs V0_cm_only (현 운영) — 5 seed delta median
    print()
    print("=" * 100)
    print("Paired delta vs V0_cm_only (현 운영 baseline) — 5 seeds 평균")
    print("=" * 100)
    print(f"{'Cell':<14} {'Slice':<6} {'Δmed_APE (mean±std)':>22} {'WinRate (mean)':>15} {'Catastrophic 2x':>17}")
    print("-" * 75)
    for cell in cells:
        if cell == "V0_cm_only":
            continue
        for slice_name in ["warm", "cold"]:
            deltas = []; wrs = []; cats = []
            for seed in SEEDS:
                base = all_results[seed]["V0_cm_only"][slice_name]["ape_array"]
                var = all_results[seed][cell][slice_name]["ape_array"]
                p = paired_compare(base, var)
                deltas.append(p["delta_median_ape"])
                wrs.append(p["win_rate_variant"])
                cats.append(p["catastrophic_2x"])
            print(f"{cell:<14} {slice_name:<6} {np.mean(deltas):>+10.4f} ± {np.std(deltas):>6.4f}  "
                  f"{np.mean(wrs):>12.4f}     {np.mean(cats):>12.4f}")

    # 2D / 3D slice (V0_cm_only baseline) — 가장 흥미로운 cell만
    print()
    print("=" * 100)
    print("2D/3D slice — V0_cm_only baseline vs 주요 후보")
    print("=" * 100)
    interesting_cells = ["V0_has_only", "V0_both", "V2_cm_only", "V3_cm_only"]
    print(f"{'Cell':<14} {'Slice':<10} {'V0_med':>9} {'Cell_med':>9} {'Δ':>9} {'WinRate':>9}")
    print("-" * 75)
    for cell in interesting_cells:
        for slice_name in ["warm", "cold"]:
            for is3d, label in [(0, "2D"), (1, "3D")]:
                v0_ape_all = []
                cell_ape_all = []
                for seed in SEEDS:
                    is_3d_arr = np.array(all_results[seed]["V0_cm_only"][slice_name]["is_3d"])
                    mask = is_3d_arr == is3d
                    if mask.sum() == 0:
                        continue
                    v0_ape = np.array(all_results[seed]["V0_cm_only"][slice_name]["ape_array"])[mask]
                    cell_ape = np.array(all_results[seed][cell][slice_name]["ape_array"])[mask]
                    v0_ape_all.extend(v0_ape); cell_ape_all.extend(cell_ape)
                v0_ape_all = np.array(v0_ape_all); cell_ape_all = np.array(cell_ape_all)
                if len(v0_ape_all) == 0:
                    continue
                delta = float(np.median(cell_ape_all - v0_ape_all))
                wr = float((cell_ape_all < v0_ape_all).mean())
                print(f"{cell:<14} {slice_name:<3} {label:<3} "
                      f"{np.median(v0_ape_all):>9.4f} {np.median(cell_ape_all):>9.4f} "
                      f"{delta:>+9.4f} {wr:>9.4f}")

    # Save (ape_array 보존)
    save = {}
    for seed, seed_res in all_results.items():
        save[str(seed)] = {}
        for cell, r in seed_res.items():
            save[str(seed)][cell] = {
                "effective": r["effective"],
                "warm": {k: v for k, v in r["warm"].items()},
                "cold": {k: v for k, v in r["cold"].items()},
            }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
