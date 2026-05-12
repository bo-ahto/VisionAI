"""Track 3 PR17 — Branch model 실험 (warm/cold × 2D/3D), Codex 검증 가이드라인 반영.

검증 protocol (Codex 권고):
  - release_split test는 사용하지 않음 (test overfitting 방지)
  - train 내부에 mini hold-out 생성 (release_split 와 동일 design 축소판)
    - cold-mini: 작가 100명 통째 hold-out
    - warm-mini: 나머지 작가 ≥2건에서 1건씩 hold-out
    - 학습: 나머지 (mini-train)
  - 4 variant 비교:
    V0 (baseline): 단일 모델 (현 운영 B_cm 재현)
    V1 (warm-only-split): Cold 단일 / Warm 2D & 3D 분기
    V2 (cold-only-split): Cold 2D & 3D 분기 / Warm 단일
    V3 (full-split): Cold 2D & 3D + Warm 2D & 3D 모두 분기

Codex 가이드 반영:
  - branch별 artist_works_log (`_branch`) — train branch only count
  - 2D branch에서 depth_cm constant 0이므로 feature 제거
  - Warm-2D 보수적 hyperparam (num_leaves 64, min_data_in_leaf 30)
  - 라우팅 fallback: global_seen but branch_unseen → Cold-branch
  - Paired metric: row-wise APE delta + win-rate + catastrophic regression (APE 2배)

Metric:
  per variant per slice (Cold/Warm × 2D/3D × medium):
    n / median APE / W30 / paired vs V0 (delta median APE, win-rate, catastrophic %)
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
OUT_PATH = REPO / "data" / "track3_pr17_branch_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEED = 42
N_COLD_MINI = 100      # train 내부 cold hold-out 작가 수
WARM_PER_ARTIST = 1     # 작가별 1건 hold-out

# Base features (depth 제외 — 2D/3D 공통)
BASE_NO_DEPTH = ["medium_category", "support_category",
                  "log_area", "estimated_ho", "orientation",
                  "medium_ho_bucket", "aspect_ratio"]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

# Codex 코드 리뷰 fix: deterministic 학습 + 모든 random seed 명시
LGB_PARAMS_FULL = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "seed": SEED, "bagging_seed": SEED, "feature_fraction_seed": SEED,
    "data_random_seed": SEED, "drop_seed": SEED, "objective_seed": SEED,
    "deterministic": True, "num_threads": 1,
}
# 2D subset (~7.4k rows) — 보수적 (PR18에서 min_data_in_leaf 75로 통일)
LGB_PARAMS_SMALL = {
    **LGB_PARAMS_FULL,
    "num_leaves": 64, "min_data_in_leaf": 75,
    "feature_fraction": 0.95, "bagging_fraction": 0.95,
}


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


def train_lgb(df_train, features, cat_cols, params):
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    va_idx = perm[:cut]; tr_idx = perm[cut:]
    X_tr = to_cat(df_train.iloc[tr_idx], features, cat_cols)
    X_va = to_cat(df_train.iloc[va_idx], features, cat_cols)
    y_tr = df_train.iloc[tr_idx][TARGET].values
    y_va = df_train.iloc[va_idx][TARGET].values
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_cols)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=cat_cols, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
        "ape_array": ape.tolist(),  # paired 비교용
    }


def paired_compare(ape_baseline, ape_variant):
    """row-wise paired 비교."""
    ape_b = np.array(ape_baseline)
    ape_v = np.array(ape_variant)
    delta = ape_v - ape_b
    return {
        "n": int(len(delta)),
        "delta_median_ape": float(np.median(delta)),
        "delta_mean_ape": float(np.mean(delta)),
        "win_rate_variant": float((ape_v < ape_b).mean()),   # variant가 더 정확한 비율
        "catastrophic_pct": float((ape_v > 2 * ape_b).mean()),  # APE 2배 이상 악화
        "improved_pct": float((ape_v < ape_b * 0.5).mean()),    # APE 50% 이상 개선
    }


def setup_mini_holdout(train_df):
    """Train 내부 hold-out 생성 (release_split design 축소판).

    명칭은 'stratified'지만 실제는 작가 작품수 구간 (low/mid/high) **quota 샘플링**.
    가격대/매체/2D-3D 비율은 통제 안 함 (Codex caveat 3).

    Stability (Codex caveat 2 fix): train_df row order 의존성 제거 위해 stable sort + 정렬 풀.
    """
    train_df = train_df.sort_values(
        by=[ARTIST_COL, "ln_price_krw_unified", "log_area"],
        kind="mergesort",
    ).reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    artist_counts = train_df.groupby(ARTIST_COL).size().sort_values()
    artists_low = sorted([a for a in artist_counts.index if artist_counts[a] <= 2])
    artists_mid = sorted([a for a in artist_counts.index if 3 <= artist_counts[a] <= 10])
    artists_high = sorted([a for a in artist_counts.index if artist_counts[a] > 10])
    n_low = int(N_COLD_MINI * 0.5); n_mid = int(N_COLD_MINI * 0.3); n_high = N_COLD_MINI - n_low - n_mid
    assert len(artists_low) >= n_low, f"low strata 부족: {len(artists_low)} < {n_low}"
    assert len(artists_mid) >= n_mid, f"mid strata 부족: {len(artists_mid)} < {n_mid}"
    assert len(artists_high) >= n_high, f"high strata 부족: {len(artists_high)} < {n_high}"
    cold_artists = (
        list(rng.choice(artists_low, size=n_low, replace=False)) +
        list(rng.choice(artists_mid, size=n_mid, replace=False)) +
        list(rng.choice(artists_high, size=n_high, replace=False))
    )
    cold_set = set(cold_artists)

    cold_mini = train_df[train_df[ARTIST_COL].isin(cold_set)].copy()
    remaining = train_df[~train_df[ARTIST_COL].isin(cold_set)].copy()

    rem_counts = remaining.groupby(ARTIST_COL).size()
    multi_artists = sorted(rem_counts[rem_counts >= 2].index.tolist())
    warm_idx = []
    for artist in multi_artists:
        rows = remaining[remaining[ARTIST_COL] == artist]
        sampled = rng.choice(rows.index.values, size=WARM_PER_ARTIST, replace=False)
        warm_idx.extend(sampled.tolist())
    warm_mini = remaining.loc[warm_idx].copy()
    mini_train = remaining.drop(warm_idx).copy()

    # Branch annotation
    for d in [mini_train, warm_mini, cold_mini]:
        d["is_3d"] = (d["depth_cm"] > 0).astype(int)

    return mini_train, warm_mini, cold_mini


def predict_cold_unified(mini_train, test, features=None):
    """V0/V1: Cold 단일 모델 (현 운영)."""
    feats = BASE_NO_DEPTH + ["depth_cm", "artist_works_log"]
    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts)
    te = make_features(test, counts)
    model = build_lad(feats, BASE_CAT)
    model.fit(tr[feats], tr[TARGET].values)
    return model.predict(te[feats])


def predict_cold_branched(mini_train, test):
    """V2/V3: Cold 2D/3D 분기. branch별 artist_works_log_branch."""
    pred = np.zeros(len(test))
    for is3d in [0, 1]:
        tr = mini_train[mini_train["is_3d"] == is3d].copy()
        te_mask = (test["is_3d"] == is3d).values
        te = test[te_mask].copy()
        if len(te) == 0:
            continue
        # branch-local count
        branch_counts = tr[ARTIST_COL].value_counts().to_dict()
        # 2D는 depth_cm 제거 (constant 0)
        feats = BASE_NO_DEPTH + (["depth_cm"] if is3d else []) + ["artist_works_log_branch"]
        tr_f = make_features(tr, branch_counts, count_col="artist_works_log_branch")
        te_f = make_features(te, branch_counts, count_col="artist_works_log_branch")
        model = build_lad(feats, BASE_CAT)
        model.fit(tr_f[feats], tr_f[TARGET].values)
        pred[te_mask] = model.predict(te_f[feats])
    return pred


def predict_warm_unified(mini_train, test):
    """V0/V2: Warm 단일 모델."""
    feats = BASE_NO_DEPTH + ["depth_cm", "artist_works_log", ARTIST_COL]
    cat = BASE_CAT + [ARTIST_COL]
    counts = mini_train[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train, counts)
    te = make_features(test, counts)
    model = train_lgb(tr, feats, cat, LGB_PARAMS_FULL)
    return model.predict(to_cat(te, feats, cat))


def predict_warm_branched_with_fallback(mini_train, test):
    """V1/V3: Warm 2D/3D 분기 + 라우팅 fallback.

    Contract: test 의 모든 작가는 mini_train (global) 에 ≥1건 있어야 함.

    라우팅:
      global_seen && branch_seen → branch Warm
      global_seen but branch_unseen → branch Cold (fallback)
      global_unseen → 호출 안 됨 (이미 cold_mini에 속함, assert로 차단)
    """
    # Codex caveat: 함수 계약 내부 강제 (호출자 의존 제거)
    global_artists = set(mini_train[ARTIST_COL])
    unseen = set(test[ARTIST_COL]) - global_artists
    assert not unseen, (
        f"predict_warm_branched_with_fallback는 global_seen artists만 받음. "
        f"unseen {len(unseen)}명: {sorted(unseen)[:5]}..."
    )
    pred = np.full(len(test), np.nan)
    test = test.reset_index(drop=True).copy()
    test["_orig_idx"] = np.arange(len(test))

    # Branch models 학습
    branch_warm_models = {}
    branch_cold_models_fallback = {}
    for is3d in [0, 1]:
        tr = mini_train[mini_train["is_3d"] == is3d].copy()
        branch_counts = tr[ARTIST_COL].value_counts().to_dict()
        feats_w = BASE_NO_DEPTH + (["depth_cm"] if is3d else []) + ["artist_works_log_branch", ARTIST_COL]
        cat_w = BASE_CAT + [ARTIST_COL]
        feats_c = BASE_NO_DEPTH + (["depth_cm"] if is3d else []) + ["artist_works_log_branch"]
        tr_f = make_features(tr, branch_counts, count_col="artist_works_log_branch")
        # Warm 모델 (보수적 hyperparam)
        params = LGB_PARAMS_SMALL if is3d == 0 else LGB_PARAMS_FULL
        warm_m = train_lgb(tr_f, feats_w, cat_w, params)
        # Cold fallback 모델
        cold_m = build_lad(feats_c, BASE_CAT)
        cold_m.fit(tr_f[feats_c], tr_f[TARGET].values)
        branch_warm_models[is3d] = (warm_m, feats_w, cat_w, branch_counts)
        branch_cold_models_fallback[is3d] = (cold_m, feats_c, branch_counts)

    # 라우팅 + 예측
    for is3d in [0, 1]:
        te_branch = test[test["is_3d"] == is3d].copy()
        if len(te_branch) == 0:
            continue
        warm_m, feats_w, cat_w, branch_counts = branch_warm_models[is3d]
        cold_m, feats_c, _ = branch_cold_models_fallback[is3d]
        te_feat = make_features(te_branch, branch_counts, count_col="artist_works_log_branch")
        # branch_seen 확인 (branch_count > 0)
        seen_mask = te_feat[ARTIST_COL].map(branch_counts).fillna(0) > 0
        # branch_seen → Warm-branch
        if seen_mask.any():
            seen_rows = te_feat[seen_mask]
            preds_w = warm_m.predict(to_cat(seen_rows, feats_w, cat_w))
            for i, idx in enumerate(seen_rows["_orig_idx"]):
                pred[idx] = preds_w[i]
        # branch_unseen → Cold-branch fallback
        if (~seen_mask).any():
            unseen_rows = te_feat[~seen_mask]
            preds_c = cold_m.predict(unseen_rows[feats_c])
            for i, idx in enumerate(unseen_rows["_orig_idx"]):
                pred[idx] = preds_c[i]
    return pred


def run_variant(name, mini_train, warm_mini, cold_mini):
    logger.info(f"[{name}] 학습 + 예측")
    if name == "V0":
        warm_pred = predict_warm_unified(mini_train, warm_mini)
        cold_pred = predict_cold_unified(mini_train, cold_mini)
    elif name == "V1":  # warm-only split
        warm_pred = predict_warm_branched_with_fallback(mini_train, warm_mini)
        cold_pred = predict_cold_unified(mini_train, cold_mini)
    elif name == "V2":  # cold-only split
        warm_pred = predict_warm_unified(mini_train, warm_mini)
        cold_pred = predict_cold_branched(mini_train, cold_mini)
    elif name == "V3":  # full split
        warm_pred = predict_warm_branched_with_fallback(mini_train, warm_mini)
        cold_pred = predict_cold_branched(mini_train, cold_mini)
    else:
        raise ValueError(name)

    warm_m = compute_metrics(warm_mini[TARGET].values, warm_pred)
    cold_m = compute_metrics(cold_mini[TARGET].values, cold_pred)
    return {"warm": warm_m, "cold": cold_m, "warm_pred": warm_pred.tolist(),
            "cold_pred": cold_pred.tolist()}


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR17 — Branch model 실험 (train 내부 mini hold-out)")
    logger.info("=" * 70)

    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    mini_train, warm_mini, cold_mini = setup_mini_holdout(train)
    logger.info(f"\nmini_train {len(mini_train):,} / warm_mini {len(warm_mini):,} / "
                f"cold_mini {len(cold_mini):,}")
    logger.info(f"  warm 2D/3D: {(warm_mini['is_3d']==0).sum()} / {(warm_mini['is_3d']==1).sum()}")
    logger.info(f"  cold 2D/3D: {(cold_mini['is_3d']==0).sum()} / {(cold_mini['is_3d']==1).sum()}")

    results = {}
    for variant in ["V0", "V1", "V2", "V3"]:
        results[variant] = run_variant(variant, mini_train, warm_mini, cold_mini)

    # Output
    print()
    print("=" * 90)
    print("📊 PR17 — Branch model 비교 (train 내부 mini hold-out)")
    print("=" * 90)
    print()
    print(f"{'Variant':<6} {'Warm n':>7} {'Warm med_APE':>13} {'Warm W30':>10} "
          f"{'Cold n':>7} {'Cold med_APE':>13} {'Cold W30':>10}")
    print("-" * 78)
    for v in ["V0", "V1", "V2", "V3"]:
        w = results[v]["warm"]; c = results[v]["cold"]
        print(f"{v:<6} {w['n']:>7,} {w['median_ape']:>13.4f} {w['within_30pct']:>10.4f} "
              f"{c['n']:>7,} {c['median_ape']:>13.4f} {c['within_30pct']:>10.4f}")

    # Paired comparison vs V0
    print()
    print("=" * 90)
    print("Paired vs V0 (baseline)")
    print("=" * 90)
    for v in ["V1", "V2", "V3"]:
        print(f"\n[{v}]")
        for slice_name in ["warm", "cold"]:
            p = paired_compare(
                results["V0"][slice_name]["ape_array"],
                results[v][slice_name]["ape_array"]
            )
            print(f"  {slice_name:<6} delta_med_ape={p['delta_median_ape']:+.4f}  "
                  f"win_rate={p['win_rate_variant']:.4f}  "
                  f"catastrophic(2x)={p['catastrophic_pct']:.4f}  "
                  f"improved(50%)={p['improved_pct']:.4f}")

    # 2D / 3D slice
    print()
    print("=" * 90)
    print("2D / 3D slice (V0 vs V3, full-split)")
    print("=" * 90)
    for slice_name, df_mini, key in [
        ("warm", warm_mini, "warm"), ("cold", cold_mini, "cold")
    ]:
        for is3d, label in [(0, "2D"), (1, "3D")]:
            mask = (df_mini["is_3d"] == is3d).values
            if mask.sum() == 0:
                continue
            v0_ape = np.array(results["V0"][key]["ape_array"])[mask]
            v3_ape = np.array(results["V3"][key]["ape_array"])[mask]
            delta = float(np.median(v3_ape - v0_ape))
            wr = float((v3_ape < v0_ape).mean())
            print(f"  {slice_name} {label}  n={mask.sum():>4,}  "
                  f"V0_med={np.median(v0_ape):.4f}  V3_med={np.median(v3_ape):.4f}  "
                  f"delta={delta:+.4f}  win_rate={wr:.4f}")

    # Save (ape_array 제외)
    save = {}
    for v, r in results.items():
        save[v] = {
            "warm": {k: vv for k, vv in r["warm"].items() if k != "ape_array"},
            "cold": {k: vv for k, vv in r["cold"].items() if k != "ape_array"},
        }
    OUT_PATH.write_text(json.dumps(save, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
