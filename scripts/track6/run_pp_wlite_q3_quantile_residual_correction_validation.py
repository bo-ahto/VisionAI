#!/usr/bin/env python3
"""PP-WLITE-Q3: Warm-lite Quantile residual correction validation.

PP-WLITE-Q1/Q2에서 개선된 Warm-lite Quantile 후보 위에 트리 잔차 보정층을
붙여 추가 개선 여부를 확인한다.

누수 방지 설계:
- 잔차 target은 학습행의 in-sample q50이 아니라 5-fold OOF Quantile 예측으로 만든다.
- residual = 실제 로그가격 - OOF(q50 full/lean 평균)
- CatBoost/LightGBM residual 모델은 OOF Quantile 피처와 작품/작가 통계 피처로 residual을 학습한다.
- 평가행은 별도 final Quantile 모델 예측값 위에 residual 보정값을 clip해 더한다.

검증 축:
1. Q1-like: 실존 저이력 작가 leave-one-out (PP-WCUT5-equivalent)
2. Q2-like: warm fixed-test k=1~4 절단 검증 (PP-WCUT6-equivalent)
"""
from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", message="X does not have valid feature names")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_cgrp_spec = importlib.util.spec_from_file_location(
    "cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py"
)
cgrp = importlib.util.module_from_spec(_cgrp_spec)
_cgrp_spec.loader.exec_module(cgrp)

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)

_cb3_spec = importlib.util.spec_from_file_location(
    "cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py"
)
cb3 = importlib.util.module_from_spec(_cb3_spec)
_cb3_spec.loader.exec_module(cb3)


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WLITE-Q3_quantile_residual_correction_validation"
WARM_LITE_PREDICTOR = (
    REPO / "models" / "track6" / "warm_lite_v0.1" / "predict" / "predict_warm_lite_v0_1.py"
)

Q1_SEEDS = [20260612, 20260613, 20260614]
TRUNC_SEEDS = [20260612, 20260613, 20260614]
KS = [1, 2, 3, 4]
ROWS_MIN, ROWS_MAX = 2, 5
MODEL_SEED = 20260612
N_BOOT = 400
FORCE_RECOMPUTE = True

LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]

FULL_NUM = cb3.NUM_BASE + cgrp.GRP_FULL
LEAN_NUM = cb3.NUM_BASE + cgrp.GRP_LEAN
CAT_COLS = cb3.CAT_C
Q_COLS = ["lgbq_full_q10", "lgbq_full_q50", "lgbq_full_q90", "lgbq_lean_q50", "lgbq_full_lean_avg", "lgbq_width"]
RES_NUM = list(dict.fromkeys(FULL_NUM + Q_COLS))
RES_CAT = CAT_COLS
BASE_CANDIDATES = [
    "all6_current",
    "lgbq_full_q50",
    "lgbq_lean_q50",
    "lgbq_full_lean_avg",
]
RESIDUAL_CANDIDATES = [
    "qavg_cbres_s05_cap005",
    "qavg_cbres_s05_cap010",
    "qavg_cbres_s10_cap005",
    "qavg_lgbres_s05_cap005",
    "qavg_lgbres_s05_cap010",
    "qavg_lgbres_s10_cap005",
]
CANDIDATES = BASE_CANDIDATES + RESIDUAL_CANDIDATES


def load_warm_lite_module():
    spec = importlib.util.spec_from_file_location("warm_lite_v0_1", WARM_LITE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Warm-lite predictor from {WARM_LITE_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def add_price_proxy(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["grp_price_proxy"] = out["grp_unit_area_median"] + out["log_area"].clip(lower=0)
    return out


def quantile_pipeline(alpha: float, feature_set: str, seed: int) -> Pipeline:
    num_cols = FULL_NUM if feature_set == "full" else LEAN_NUM
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", SimpleImputer(strategy="median"), num_cols),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                    ]
                ),
            ),
            (
                "model",
                LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    n_estimators=320,
                    learning_rate=0.035,
                    num_leaves=31,
                    min_child_samples=20,
                    subsample=0.90,
                    colsample_bytree=0.90,
                    reg_lambda=0.10,
                    random_state=seed,
                    n_jobs=-1,
                    verbose=-1,
                ),
            ),
        ]
    )


def fit_quantile_models(train_s: pd.DataFrame, seed: int = MODEL_SEED) -> dict[str, Pipeline]:
    y = train_s["ln_price_krw"].to_numpy(dtype=float)
    models = {
        "full_q10": quantile_pipeline(0.10, "full", seed),
        "full_q50": quantile_pipeline(0.50, "full", seed),
        "full_q90": quantile_pipeline(0.90, "full", seed),
        "lean_q50": quantile_pipeline(0.50, "lean", seed),
    }
    models["full_q10"].fit(train_s[FULL_NUM + CAT_COLS], y)
    models["full_q50"].fit(train_s[FULL_NUM + CAT_COLS], y)
    models["full_q90"].fit(train_s[FULL_NUM + CAT_COLS], y)
    models["lean_q50"].fit(train_s[LEAN_NUM + CAT_COLS], y)
    return models


def predict_quantiles(models: dict[str, Pipeline], frame: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["lgbq_full_q10"] = np.asarray(models["full_q10"].predict(frame[FULL_NUM + CAT_COLS]), dtype=float)
    out["lgbq_full_q50"] = np.asarray(models["full_q50"].predict(frame[FULL_NUM + CAT_COLS]), dtype=float)
    out["lgbq_full_q90"] = np.asarray(models["full_q90"].predict(frame[FULL_NUM + CAT_COLS]), dtype=float)
    out["lgbq_lean_q50"] = np.asarray(models["lean_q50"].predict(frame[LEAN_NUM + CAT_COLS]), dtype=float)
    out["lgbq_full_lean_avg"] = 0.50 * out["lgbq_full_q50"] + 0.50 * out["lgbq_lean_q50"]
    out["lgbq_width"] = np.maximum(out["lgbq_full_q90"] - out["lgbq_full_q10"], 0.0)
    return out


def oof_quantiles(train_s: pd.DataFrame, seed: int = MODEL_SEED) -> pd.DataFrame:
    out = pd.DataFrame(index=train_s.index, columns=Q_COLS, dtype=float)
    kf = KFold(n_splits=5, shuffle=True, random_state=seed)
    for fold, (tr_idx, va_idx) in enumerate(kf.split(train_s), start=1):
        models = fit_quantile_models(train_s.iloc[tr_idx].copy(), seed + fold)
        out.iloc[va_idx] = predict_quantiles(models, train_s.iloc[va_idx].copy()).to_numpy(dtype=float)
    return out.astype(float)


def residual_feature_frame(frame: pd.DataFrame, qpred: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in Q_COLS:
        out[col] = qpred[col].to_numpy(dtype=float)
    for col in RES_CAT:
        out[col] = out[col].astype(str).fillna("__MISSING__")
    return out[RES_NUM + RES_CAT]


def fit_residual_models(train_s: pd.DataFrame, q_oof: pd.DataFrame) -> dict[str, object]:
    y = train_s["ln_price_krw"].to_numpy(dtype=float)
    residual = y - q_oof["lgbq_full_lean_avg"].to_numpy(dtype=float)
    x = residual_feature_frame(train_s, q_oof)

    cat_features = [x.columns.get_loc(col) for col in RES_CAT]
    cb = CatBoostRegressor(
        loss_function="RMSE",
        iterations=320,
        depth=4,
        learning_rate=0.035,
        l2_leaf_reg=5.0,
        random_seed=MODEL_SEED,
        verbose=False,
        allow_writing_files=False,
    )
    cb.fit(x, residual, cat_features=cat_features)

    lgb = Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", SimpleImputer(strategy="median"), RES_NUM),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), RES_CAT),
                    ]
                ),
            ),
            (
                "model",
                LGBMRegressor(
                    objective="huber",
                    n_estimators=320,
                    learning_rate=0.035,
                    num_leaves=31,
                    min_child_samples=20,
                    subsample=0.90,
                    colsample_bytree=0.90,
                    reg_lambda=0.30,
                    random_state=MODEL_SEED,
                    n_jobs=-1,
                    verbose=-1,
                ),
            ),
        ]
    )
    lgb.fit(x, residual)
    return {"catboost": cb, "lightgbm": lgb}


def train_stack(train_s: pd.DataFrame) -> dict[str, object]:
    train_s = add_price_proxy(train_s)
    q_oof = oof_quantiles(train_s)
    q_models = fit_quantile_models(train_s)
    residual_models = fit_residual_models(train_s, q_oof)
    return {"q_models": q_models, "residual_models": residual_models}


def apply_stack(frame: pd.DataFrame, stack: dict[str, object]) -> pd.DataFrame:
    fs = add_price_proxy(frame)
    qpred = predict_quantiles(stack["q_models"], fs)
    x = residual_feature_frame(fs, qpred)
    out = qpred.copy()
    out["cb_residual"] = np.asarray(stack["residual_models"]["catboost"].predict(x), dtype=float)
    out["lgb_residual"] = np.asarray(stack["residual_models"]["lightgbm"].predict(x), dtype=float)
    return out


def add_residual_candidates(out: pd.DataFrame, qpred: pd.DataFrame) -> None:
    out["lgbq_full_q50_pred_log"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
    out["lgbq_lean_q50_pred_log"] = qpred["lgbq_lean_q50"].to_numpy(dtype=float)
    out["lgbq_full_lean_avg_pred_log"] = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float)
    out["qavg_cbres_s05_cap005_pred_log"] = qpred["lgbq_full_lean_avg"] + np.clip(0.50 * qpred["cb_residual"], -0.05, 0.05)
    out["qavg_cbres_s05_cap010_pred_log"] = qpred["lgbq_full_lean_avg"] + np.clip(0.50 * qpred["cb_residual"], -0.10, 0.10)
    out["qavg_cbres_s10_cap005_pred_log"] = qpred["lgbq_full_lean_avg"] + np.clip(qpred["cb_residual"], -0.05, 0.05)
    out["qavg_lgbres_s05_cap005_pred_log"] = qpred["lgbq_full_lean_avg"] + np.clip(0.50 * qpred["lgb_residual"], -0.05, 0.05)
    out["qavg_lgbres_s05_cap010_pred_log"] = qpred["lgbq_full_lean_avg"] + np.clip(0.50 * qpred["lgb_residual"], -0.10, 0.10)
    out["qavg_lgbres_s10_cap005_pred_log"] = qpred["lgbq_full_lean_avg"] + np.clip(qpred["lgb_residual"], -0.05, 0.05)


def huber_component_predictions(train_s: pd.DataFrame, held_s: pd.DataFrame) -> pd.DataFrame:
    train_s = add_price_proxy(train_s)
    held_s = add_price_proxy(held_s)
    y = train_s["ln_price_krw"].to_numpy(dtype=float)
    out = pd.DataFrame(index=held_s.index)
    for i, cfg in enumerate(cb3.C_CONFIGS):
        num = cb3.NUM_BASE + cfg["extra"]
        pipe = Pipeline(
            [
                (
                    "prep",
                    ColumnTransformer(
                        [
                            (
                                "num",
                                Pipeline(
                                    [
                                        ("imputer", SimpleImputer(strategy="median")),
                                        ("scaler", StandardScaler()),
                                    ]
                                ),
                                num,
                            ),
                            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                        ]
                    ),
                ),
                ("model", HuberRegressor(epsilon=cfg["epsilon"], alpha=cfg["alpha"], max_iter=4000)),
            ]
        )
        pipe.fit(train_s[num + CAT_COLS], y)
        out[f"c{i}"] = np.asarray(pipe.predict(held_s[num + CAT_COLS]), dtype=float)
    return out


def run_q1_seed(seed: int, train: pd.DataFrame, base_ladder: list) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = train.groupby("artist_key").size()
    low_artists = counts[(counts >= ROWS_MIN) & (counts <= ROWS_MAX)].index

    held_idx = []
    for artist in low_artists:
        idx = np.where(train["artist_key"].to_numpy() == artist)[0]
        held_idx.append(int(rng.choice(idx)))

    held = train.iloc[held_idx].reset_index(drop=True)
    tr_rest = train.drop(index=train.index[held_idx]).reset_index(drop=True)

    cgrp.LADDER = LITE_LADDER + base_ladder
    tr_s = cgrp.train_with_internal_stats(tr_rest)
    held_s = cgrp.assign_group_stats(tr_rest, held)
    cgrp.LADDER = base_ladder

    stack = train_stack(tr_s)
    qpred = apply_stack(held_s, stack)
    huber_preds = huber_component_predictions(tr_s, held_s)

    out = pd.DataFrame(
        {
            "seed": seed,
            "_row": held_idx,
            "artist_key": held["artist_key"].to_numpy(),
            "history_k": held["artist_key"].map(counts - 1).astype(int).to_numpy(),
            "actual_price": held["price_krw"].to_numpy(dtype=float),
            "actual_log": held["ln_price_krw"].to_numpy(dtype=float),
        }
    )
    out["all6_current_pred_log"] = huber_preds[[f"c{i}" for i in range(6)]].mean(axis=1).to_numpy(dtype=float)
    add_residual_candidates(out, qpred)
    return out


def truncate_train(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep = []
    for artist, idx in train.groupby(train["artist_key"].astype(str)).indices.items():
        if artist in target_artists and len(idx) > k:
            keep.append(rng.choice(idx, size=k, replace=False))
        else:
            keep.append(idx)
    return train.iloc[np.concatenate(keep)].reset_index(drop=True)


def run_q2_condition(
    warm_lite,
    params: dict,
    huber_models: list,
    stack: dict[str, object],
    train_k: pd.DataFrame,
    test: pd.DataFrame,
    trunc_seed: int,
    k: int,
) -> pd.DataFrame:
    train_by_artist = {str(artist): group.copy() for artist, group in train_k.groupby("artist_key", sort=False)}
    parts = []
    for artist_key, group in test.groupby(test["artist_key"].astype(str), sort=False):
        artist_history = train_by_artist.get(str(artist_key))
        if artist_history is None or len(artist_history) < 1:
            raise RuntimeError(f"Missing truncated artist history for artist_key={artist_key!r}")
        fs = warm_lite.assign_stats(group.copy(), artist_history, params)
        qpred = apply_stack(fs, stack)

        out = group[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
        out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
        out.insert(0, "k", k)
        out.insert(0, "trunc_seed", trunc_seed)
        out["artist_history_n"] = int(len(artist_history))

        fs_pp = add_price_proxy(fs)
        huber_comp = []
        for model, cols in zip(huber_models, params["huber_num_cols"]):
            huber_comp.append(np.asarray(model.predict(fs_pp[cols + params["huber_cat_cols"]]), dtype=float))
        out["all6_current_pred_log"] = np.mean(huber_comp, axis=0)
        add_residual_candidates(out, qpred)
        parts.append(out)
    return pd.concat(parts, ignore_index=True)


def metric_rows(preds: pd.DataFrame, group_col: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    overall_rows = []
    for candidate in CANDIDATES:
        col = f"{candidate}_pred_log"
        mt = cb1.mt(preds["actual_price"].to_numpy(dtype=float), preds[col].to_numpy(dtype=float))
        overall_rows.append(
            {
                "candidate": candidate,
                "n": int(len(preds)),
                **{metric: round(float(value), 6) for metric, value in mt.items()},
            }
        )
    overall = pd.DataFrame(overall_rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        base = float(overall.loc[overall["candidate"].eq("all6_current"), metric].iloc[0])
        overall[f"rank_{metric}"] = overall[metric].rank(method="min").astype(int)
        overall[f"delta_{metric}_minus_all6"] = overall[metric] - base

    if group_col is None:
        return overall.sort_values(["MAPE", "p95_APE", "MdAPE"]), None

    grouped_rows = []
    for key, group in preds.groupby(group_col, sort=True):
        for candidate in CANDIDATES:
            mt = cb1.mt(group["actual_price"].to_numpy(dtype=float), group[f"{candidate}_pred_log"].to_numpy(dtype=float))
            grouped_rows.append(
                {
                    group_col: int(key),
                    "candidate": candidate,
                    "n": int(len(group)),
                    **{metric: round(float(value), 6) for metric, value in mt.items()},
                }
            )
    grouped = pd.DataFrame(grouped_rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        grouped[f"rank_{metric}"] = grouped.groupby(group_col)[metric].rank(method="min").astype(int)
    return overall.sort_values(["MAPE", "p95_APE", "MdAPE"]), grouped.sort_values([group_col, "MAPE", "p95_APE"])


def bootstrap_vs_all6(preds: pd.DataFrame, candidates: list[str], group_keys: list[str] | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    rows = []
    if group_keys:
        group_iter = preds.groupby(group_keys, sort=True)
    else:
        group_iter = [((), preds)]
    for key, frame in group_iter:
        price = frame["actual_price"].to_numpy(dtype=float)
        groups = pd.Series(np.arange(len(frame))).groupby(frame["artist_key"].astype(str).to_numpy()).apply(list)
        all6 = frame["all6_current_pred_log"].to_numpy(dtype=float)
        for candidate in candidates:
            cand = frame[f"{candidate}_pred_log"].to_numpy(dtype=float)
            wins_candidate = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
            wins_all6 = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
            for _ in range(N_BOOT):
                sampled = rng.choice(len(groups), size=len(groups), replace=True)
                idx = np.concatenate([groups.iloc[g] for g in sampled])
                cm = cb1.mt(price[idx], cand[idx])
                bm = cb1.mt(price[idx], all6[idx])
                for metric in wins_candidate:
                    wins_candidate[metric] += cm[metric] < bm[metric]
                    wins_all6[metric] += bm[metric] < cm[metric]
            row = {"candidate": candidate, "n_boot": N_BOOT}
            if group_keys:
                if not isinstance(key, tuple):
                    key = (key,)
                for col, value in zip(group_keys, key):
                    row[col] = int(value)
            for metric in wins_candidate:
                row[f"p_candidate_better_all6_{metric}"] = wins_candidate[metric] / N_BOOT
                row[f"p_all6_better_candidate_{metric}"] = wins_all6[metric] / N_BOOT
            rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_summary(boot: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, group in boot.groupby("candidate", sort=True):
        row = {"candidate": candidate, "conditions": int(len(group))}
        for metric in ("MdAPE", "MAPE", "p95_APE"):
            col = f"p_candidate_better_all6_{metric}"
            row[f"mean_{col}"] = float(group[col].mean())
            row[f"min_{col}"] = float(group[col].min())
            row[f"conditions_{col}_ge_0_90"] = int((group[col] >= 0.90).sum())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("candidate")


def table_md(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame is None or frame.empty:
        return "_No rows_"
    view = frame[columns].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    q1_overall: pd.DataFrame,
    q1_by_k: pd.DataFrame,
    q1_boot: pd.DataFrame,
    q2_overall: pd.DataFrame,
    q2_by_k: pd.DataFrame,
    q2_boot_sum: pd.DataFrame,
    config: dict,
) -> None:
    focus = ["all6_current", "lgbq_full_lean_avg", "qavg_cbres_s05_cap005", "qavg_lgbres_s05_cap005", "qavg_lgbres_s05_cap010"]
    lines = [
        "# PP-WLITE-Q3 Warm-lite Quantile 잔차 보정 검증",
        "",
        "## 1. 목적",
        "",
        "Warm-lite Quantile 후보 위에 CatBoost/LightGBM 잔차 보정층을 붙였을 때 Q1/Q2보다 추가 개선되는지 확인한다.",
        "",
        "## 2. 누수 방지 설계",
        "",
        "- 잔차 target은 in-sample q50이 아니라 5-fold OOF q50 full/lean 평균으로 계산",
        "- residual = 실제 로그가격 - OOF(q50 full/lean 평균)",
        "- 평가행에는 final Quantile 모델 예측값과 residual 모델 예측값을 사용",
        "- residual 보정값은 `clip(strength * residual_pred, -cap, +cap)`로 제한",
        "",
        "## 3. Q1-like 실존 저이력 leave-one-out overall",
        "",
        table_md(q1_overall, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE", "delta_MdAPE_minus_all6", "delta_MAPE_minus_all6", "delta_p95_APE_minus_all6"]),
        "",
        "## 4. Q1-like by history_k",
        "",
        table_md(q1_by_k[q1_by_k["candidate"].isin(focus)], ["history_k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"]),
        "",
        "## 5. Q1-like bootstrap vs all6_current",
        "",
        table_md(q1_boot, ["candidate", "n_boot", "p_candidate_better_all6_MdAPE", "p_candidate_better_all6_MAPE", "p_candidate_better_all6_p95_APE", "p_all6_better_candidate_MdAPE", "p_all6_better_candidate_MAPE", "p_all6_better_candidate_p95_APE"]),
        "",
        "## 6. Q2-like k-truncation overall",
        "",
        table_md(q2_overall, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE", "delta_MdAPE_minus_all6", "delta_MAPE_minus_all6", "delta_p95_APE_minus_all6"]),
        "",
        "## 7. Q2-like by k",
        "",
        table_md(q2_by_k[q2_by_k["candidate"].isin(focus)], ["k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"]),
        "",
        "## 8. Q2-like bootstrap summary vs all6_current",
        "",
        table_md(q2_boot_sum[q2_boot_sum["candidate"].isin(focus)], ["candidate", "conditions", "mean_p_candidate_better_all6_MdAPE", "mean_p_candidate_better_all6_MAPE", "mean_p_candidate_better_all6_p95_APE", "conditions_p_candidate_better_all6_MdAPE_ge_0_90", "conditions_p_candidate_better_all6_MAPE_ge_0_90", "conditions_p_candidate_better_all6_p95_APE_ge_0_90"]),
        "",
        "## 9. Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    feats = artifact_features()["cold_lightgbm"]
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "artist_key"]))
    train, _, _ = load_scope("warm", feats + ["medium_support_bucket"])
    train = train[need].reset_index(drop=True)
    base_ladder = list(cgrp.LADDER)

    q1_parts = []
    for seed in Q1_SEEDS:
        checkpoint = EXP / "outputs" / f"q1_preds_seed{seed}.csv"
        if checkpoint.exists() and not FORCE_RECOMPUTE:
            q1_parts.append(pd.read_csv(checkpoint))
            continue
        part = run_q1_seed(seed, train, base_ladder)
        part.to_csv(checkpoint, index=False)
        print(f"[q1 done] seed={seed}: {len(part)} rows", flush=True)
        q1_parts.append(part)
    q1_preds = pd.concat(q1_parts, ignore_index=True)
    q1_preds.to_csv(EXP / "outputs" / "q1_predictions_all_seeds.csv", index=False)
    q1_overall, q1_by_k = metric_rows(q1_preds, "history_k")
    q1_boot = bootstrap_vs_all6(q1_preds, [c for c in CANDIDATES if c != "all6_current"])
    q1_overall.to_csv(EXP / "outputs" / "q1_candidate_metrics_overall.csv", index=False)
    q1_by_k.to_csv(EXP / "outputs" / "q1_candidate_metrics_by_k.csv", index=False)
    q1_boot.to_csv(EXP / "outputs" / "q1_bootstrap_vs_all6.csv", index=False)

    warm_lite = load_warm_lite_module()
    params = warm_lite.load_params()
    huber_models = warm_lite.load_models()
    warm_features = artifact_features()["warm"]
    needed = list(dict.fromkeys(warm_features + warm_lite.REQUIRED + ["_track6_row_id", "artist_key", "price_krw", "ln_price_krw", "log_area", "medium_support_bucket", "size_bucket", "medium_category", "support_category"]))
    train_w, _, test = load_scope("warm", needed)
    train_w = train_w[needed].reset_index(drop=True)
    test = test[needed].reset_index(drop=True)
    cgrp.LADDER = LITE_LADDER + base_ladder
    train_w_s = cgrp.train_with_internal_stats(train_w)
    cgrp.LADDER = base_ladder
    q2_stack = train_stack(train_w_s)
    target_artists = set(test["artist_key"].astype(str))
    q2_parts = []
    for trunc_seed in TRUNC_SEEDS:
        for k in KS:
            checkpoint = EXP / "outputs" / f"q2_preds_trunc{trunc_seed}_k{k}.csv"
            if checkpoint.exists() and not FORCE_RECOMPUTE:
                q2_parts.append(pd.read_csv(checkpoint))
                continue
            train_k = truncate_train(train_w, target_artists, trunc_seed, k)
            part = run_q2_condition(warm_lite, params, huber_models, q2_stack, train_k, test, trunc_seed, k)
            part.to_csv(checkpoint, index=False)
            print(f"[q2 done] trunc_seed={trunc_seed} k={k}: {len(part)} rows", flush=True)
            q2_parts.append(part)
    q2_preds = pd.concat(q2_parts, ignore_index=True)
    q2_preds.to_csv(EXP / "outputs" / "q2_predictions_all_conditions.csv", index=False)
    q2_overall, q2_by_k = metric_rows(q2_preds, "k")
    q2_boot = bootstrap_vs_all6(q2_preds, [c for c in CANDIDATES if c != "all6_current"], ["trunc_seed", "k"])
    q2_boot_sum = bootstrap_summary(q2_boot)
    q2_overall.to_csv(EXP / "outputs" / "q2_candidate_metrics_overall.csv", index=False)
    q2_by_k.to_csv(EXP / "outputs" / "q2_candidate_metrics_by_k.csv", index=False)
    q2_boot.to_csv(EXP / "outputs" / "q2_bootstrap_by_seed_k.csv", index=False)
    q2_boot_sum.to_csv(EXP / "outputs" / "q2_bootstrap_summary.csv", index=False)

    config = {
        "experiment_id": "PP-WLITE-Q3",
        "experiment_slug": EXP.name,
        "model_seed": MODEL_SEED,
        "q1_design": f"PP-WCUT5-equivalent real low-history leave-one-out, seeds {Q1_SEEDS}",
        "q2_design": "PP-WCUT6-equivalent frozen Warm-lite k-truncation follow-up",
        "residual_target": "actual_log - OOF(lgbq_full_lean_avg)",
        "residual_models": ["CatBoostRegressor", "LightGBMRegressor objective=huber"],
        "residual_candidate_rule": "qavg + clip(strength * residual_pred, -cap, +cap)",
        "candidates": CANDIDATES,
        "q1_best_by_metric": {
            metric: str(q1_overall.sort_values(metric).iloc[0]["candidate"])
            for metric in ("MdAPE", "MAPE", "p95_APE")
        },
        "q2_best_by_metric": {
            metric: str(q2_overall.sort_values(metric).iloc[0]["candidate"])
            for metric in ("MdAPE", "MAPE", "p95_APE")
        },
        "n_boot": N_BOOT,
        "prohibitions": ["0604 사용 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(q1_overall, q1_by_k, q1_boot, q2_overall, q2_by_k, q2_boot_sum, config)
    print("[q1 overall]", flush=True)
    print(q1_overall[["candidate", "n", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_minus_all6", "delta_MAPE_minus_all6", "delta_p95_APE_minus_all6"]].to_string(index=False), flush=True)
    print("[q2 overall]", flush=True)
    print(q2_overall[["candidate", "n", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_minus_all6", "delta_MAPE_minus_all6", "delta_p95_APE_minus_all6"]].to_string(index=False), flush=True)
    print(json.dumps(config, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
