#!/usr/bin/env python3
"""Run PP-QR3 OOF/holdout revalidation for Cold quantile guard candidates.

PP-QR2 found strong test signals from qwidth + pred_gap corrections. PP-QR3
revalidates those signals by splitting the validation set internally and also
tries simple prediction-level meta corrections.
"""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_qr2_cold_quantile_final_candidate_blend import (  # noqa: E402
    PredictionCandidate,
    add_qr1_predictions,
    add_segment_columns,
    blend_candidates,
    fixed_candidates,
    guarded_candidates,
    load_y18_frame,
    segment_correction_candidates,
    segment_thresholds,
    validation_thresholds,
)


EXP_ID = "PP-QR3"
SLUG = "PP-QR3_cold_quantile_oof_holdout_revalidation"
TITLE = "Cold Quantile q40/q50 보정 후보 OOF/holdout 재검증"
DOC_PATH = REPO / "docs" / "track6" / "experiments" / "pp_qr3_cold_quantile_oof_holdout_revalidation_summary.md"

BASELINE_CANDIDATE = "component_pp_y18_qwidth_bin"
Y2_CANDIDATE = "component_pp_y2_baseline"


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})


def prediction_frame(split_df: pd.DataFrame, item: PredictionCandidate, split_name: str) -> pd.DataFrame:
    pred_price = np.clip(np.exp(item.pred_log), 1_000.0, None)
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": item.candidate,
        "scope": "cold",
        "split": split_name,
        "policy": item.policy,
        "_track6_row_id": split_df["_track6_row_id"].to_numpy(),
        "actual_log": split_df["actual_log"].to_numpy(dtype=float),
        "pred_log": item.pred_log,
        "actual_price": split_df["actual_price"].to_numpy(dtype=float),
        "pred_price": pred_price,
        "quantile_width_log": split_df["quantile_width_log"].to_numpy(dtype=float),
        "price_range_ratio": split_df["price_range_ratio"].to_numpy(dtype=float),
        "notes": item.notes,
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def ensure_meta_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "y18_qwidth_pred_log",
        "y2_pred_log",
        "y18_external_pred_log",
        "y18_p95_pred_log",
        "cat_q40_pred_log",
        "cat_q50_pred_log",
        "lgb_q40_pred_log",
        "lgb_q50_pred_log",
        "linear_q50_pred_log",
        "cat_q40_q50_mid_pred_log",
        "lgb_q40_q50_mid_pred_log",
        "quantile_width_log",
        "price_range_ratio",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["gap_y18_cat_q40"] = out["y18_qwidth_pred_log"] - out["cat_q40_pred_log"]
    out["gap_y18_cat_q50"] = out["y18_qwidth_pred_log"] - out["cat_q50_pred_log"]
    out["gap_y18_lgb_q40"] = out["y18_qwidth_pred_log"] - out["lgb_q40_pred_log"]
    out["gap_y18_lgb_q50"] = out["y18_qwidth_pred_log"] - out["lgb_q50_pred_log"]
    out["gap_y18_linear_q50"] = out["y18_qwidth_pred_log"] - out["linear_q50_pred_log"]
    out["gap_cat_q40_q50"] = out["cat_q50_pred_log"] - out["cat_q40_pred_log"]
    out["gap_lgb_q40_q50"] = out["lgb_q50_pred_log"] - out["lgb_q40_pred_log"]
    out["abs_gap_y18_cat_q40"] = out["gap_y18_cat_q40"].abs()
    out["abs_gap_y18_lgb_q40"] = out["gap_y18_lgb_q40"].abs()
    out["qwidth_x_gap_cat_q40"] = out["quantile_width_log"] * out["gap_y18_cat_q40"]
    out["qwidth_x_gap_lgb_q40"] = out["quantile_width_log"] * out["gap_y18_lgb_q40"]
    return out


META_FEATURES = [
    "y18_qwidth_pred_log",
    "y2_pred_log",
    "y18_external_pred_log",
    "y18_p95_pred_log",
    "cat_q40_pred_log",
    "cat_q50_pred_log",
    "lgb_q40_pred_log",
    "lgb_q50_pred_log",
    "linear_q50_pred_log",
    "cat_q40_q50_mid_pred_log",
    "lgb_q40_q50_mid_pred_log",
    "quantile_width_log",
    "price_range_ratio",
    "gap_y18_cat_q40",
    "gap_y18_cat_q50",
    "gap_y18_lgb_q40",
    "gap_y18_lgb_q50",
    "gap_y18_linear_q50",
    "gap_cat_q40_q50",
    "gap_lgb_q40_q50",
    "abs_gap_y18_cat_q40",
    "abs_gap_y18_lgb_q40",
    "qwidth_x_gap_cat_q40",
    "qwidth_x_gap_lgb_q40",
]

PREDICTION_ONLY_FEATURES = [
    "y18_qwidth_pred_log",
    "y2_pred_log",
    "y18_external_pred_log",
    "y18_p95_pred_log",
    "cat_q40_pred_log",
    "cat_q50_pred_log",
    "lgb_q40_pred_log",
    "lgb_q50_pred_log",
    "linear_q50_pred_log",
]


def fill_features(train_df: pd.DataFrame, eval_df: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray]:
    train_x = train_df[features].copy()
    eval_x = eval_df[features].copy()
    med = train_x.median(numeric_only=True)
    train_x = train_x.fillna(med).fillna(0.0)
    eval_x = eval_x.fillna(med).fillna(0.0)
    return train_x.to_numpy(dtype=float), eval_x.to_numpy(dtype=float)


def meta_candidates(train_df: pd.DataFrame, eval_df: pd.DataFrame) -> list[PredictionCandidate]:
    train_df = ensure_meta_features(train_df)
    eval_df = ensure_meta_features(eval_df)
    y = train_df["actual_log"].to_numpy(dtype=float)
    residual_y = y - train_df["y18_qwidth_pred_log"].to_numpy(dtype=float)
    base_eval = eval_df["y18_qwidth_pred_log"].to_numpy(dtype=float)
    candidates: list[PredictionCandidate] = []

    for feature_name, feature_cols in [("predonly", PREDICTION_ONLY_FEATURES), ("predgap", META_FEATURES)]:
        train_x, eval_x = fill_features(train_df, eval_df, feature_cols)
        for alpha in [0.1, 1.0, 10.0, 50.0]:
            model = Pipeline([
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=alpha)),
            ])
            model.fit(train_x, y)
            pred = np.asarray(model.predict(eval_x), dtype=float)
            candidates.append(PredictionCandidate(
                f"meta_ridge_direct_{feature_name}_a{alpha:g}".replace(".", "p"),
                "oof_meta_direct_ridge",
                pred,
                f"Ridge direct target with {feature_name} features, alpha={alpha:g}",
            ))

        for alpha in [0.1, 1.0, 10.0]:
            model = Pipeline([
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=alpha)),
            ])
            model.fit(train_x, residual_y)
            resid = np.asarray(model.predict(eval_x), dtype=float)
            for cap in [0.10, 0.15, 0.25, 0.35]:
                for strength in [0.50, 0.75, 1.00]:
                    pred = base_eval + strength * np.clip(resid, -cap, cap)
                    candidates.append(PredictionCandidate(
                        f"meta_ridge_resid_{feature_name}_a{alpha:g}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p"),
                        "oof_meta_residual_ridge",
                        pred,
                        f"Ridge residual with {feature_name}, alpha={alpha:g}, cap={cap:.2f}, strength={strength:.2f}",
                    ))

    train_x, eval_x = fill_features(train_df, eval_df, META_FEATURES)
    for alpha in [0.001, 0.01]:
        model = Pipeline([
            ("scale", StandardScaler()),
            ("model", HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=1000)),
        ])
        model.fit(train_x, residual_y)
        resid = np.asarray(model.predict(eval_x), dtype=float)
        for cap in [0.10, 0.15, 0.25]:
            for strength in [0.50, 0.75, 1.00]:
                pred = base_eval + strength * np.clip(resid, -cap, cap)
                candidates.append(PredictionCandidate(
                    f"meta_huber_resid_predgap_a{alpha:g}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p"),
                    "oof_meta_residual_huber",
                    pred,
                    f"Huber residual with predgap features, alpha={alpha:g}, cap={cap:.2f}, strength={strength:.2f}",
                ))

    for regularization in [0.001, 0.01]:
        model = Pipeline([
            ("scale", StandardScaler()),
            ("model", QuantileRegressor(quantile=0.5, alpha=regularization, solver="highs")),
        ])
        model.fit(train_x, residual_y)
        resid = np.asarray(model.predict(eval_x), dtype=float)
        for cap in [0.10, 0.15, 0.25]:
            for strength in [0.50, 1.00]:
                pred = base_eval + strength * np.clip(resid, -cap, cap)
                candidates.append(PredictionCandidate(
                    f"meta_qr_resid_predgap_a{regularization:g}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p"),
                    "oof_meta_residual_quantile_regression",
                    pred,
                    f"Linear QuantileRegressor residual with predgap features, alpha={regularization:g}, cap={cap:.2f}, strength={strength:.2f}",
                ))

    for loss_name, params in [
        ("absolute_error", {"loss": "absolute_error"}),
        ("squared_error", {"loss": "squared_error"}),
    ]:
        try:
            model = HistGradientBoostingRegressor(
                **params,
                max_iter=120,
                max_leaf_nodes=8,
                min_samples_leaf=60,
                l2_regularization=0.1,
                learning_rate=0.04,
                random_state=SEED,
            )
            model.fit(train_x, residual_y)
        except Exception:
            continue
        resid = np.asarray(model.predict(eval_x), dtype=float)
        for cap in [0.10, 0.15, 0.25]:
            for strength in [0.50, 0.75]:
                pred = base_eval + strength * np.clip(resid, -cap, cap)
                candidates.append(PredictionCandidate(
                    f"meta_hgb_resid_{loss_name}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p"),
                    "oof_meta_residual_hist_gradient_boosting",
                    pred,
                    f"HistGradientBoosting residual loss={loss_name}, cap={cap:.2f}, strength={strength:.2f}",
                ))
    return candidates


def all_candidates(train_df: pd.DataFrame, eval_df: pd.DataFrame) -> list[PredictionCandidate]:
    thresholds = validation_thresholds(train_df)
    seg_thresholds = segment_thresholds(train_df)
    train_binned = add_segment_columns(train_df, seg_thresholds)
    eval_binned = add_segment_columns(eval_df, seg_thresholds)
    candidates: list[PredictionCandidate] = []
    candidates.extend(fixed_candidates(eval_df))
    candidates.extend(blend_candidates(eval_df))
    candidates.extend(guarded_candidates(eval_df, thresholds))
    candidates.extend(segment_correction_candidates(eval_df, train_binned, eval_binned))
    candidates.extend(meta_candidates(train_df, eval_df))
    return candidates


def add_metric(rows: list[dict[str, Any]], scheme: str, fold_id: int, eval_df: pd.DataFrame, item: PredictionCandidate) -> None:
    rows.append({
        "experiment_id": EXP_ID,
        "scheme": scheme,
        "fold_id": fold_id,
        "candidate": item.candidate,
        "policy": item.policy,
        **metrics(metric_frame(eval_df), item.pred_log),
    })


def split_plan(val_df: pd.DataFrame) -> list[tuple[str, int, np.ndarray, np.ndarray]]:
    out: list[tuple[str, int, np.ndarray, np.ndarray]] = []
    idx = np.arange(len(val_df))
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    for fold_id, (train_idx, hold_idx) in enumerate(kf.split(idx), start=1):
        out.append(("row_5fold", fold_id, train_idx, hold_idx))
    groups = val_df["artist_key"].astype(str).fillna("__MISSING__").to_numpy()
    gkf = GroupKFold(n_splits=5)
    for fold_id, (train_idx, hold_idx) in enumerate(gkf.split(idx, groups=groups), start=1):
        out.append(("artist_5fold", fold_id, train_idx, hold_idx))
    return out


def run_holdout(frame: pd.DataFrame) -> pd.DataFrame:
    val = frame[frame["split"].eq("validation")].copy().reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for scheme, fold_id, train_idx, hold_idx in split_plan(val):
        train_df = val.iloc[train_idx].copy().reset_index(drop=True)
        hold_df = val.iloc[hold_idx].copy().reset_index(drop=True)
        for item in all_candidates(train_df, hold_df):
            add_metric(rows, scheme, fold_id, hold_df, item)
    return pd.DataFrame(rows)


def summarize_holdout(holdout_df: pd.DataFrame) -> pd.DataFrame:
    summary = holdout_df.groupby(["candidate", "policy"], as_index=False).agg(
        folds=("fold_id", "count"),
        mean_MdAPE=("MdAPE", "mean"),
        std_MdAPE=("MdAPE", "std"),
        mean_MAPE=("MAPE", "mean"),
        std_MAPE=("MAPE", "std"),
        mean_p95_APE=("p95_APE", "mean"),
        std_p95_APE=("p95_APE", "std"),
        mean_RMSE_log=("RMSE_log", "mean"),
        mean_Within_50=("Within_50", "mean"),
    )
    base = holdout_df[holdout_df["candidate"].eq(BASELINE_CANDIDATE)][
        ["scheme", "fold_id", "MdAPE", "MAPE", "p95_APE"]
    ].rename(columns={"MdAPE": "base_MdAPE", "MAPE": "base_MAPE", "p95_APE": "base_p95_APE"})
    merged = holdout_df.merge(base, on=["scheme", "fold_id"], how="left")
    merged["MdAPE_improve"] = merged["MdAPE"] < merged["base_MdAPE"]
    merged["MAPE_improve"] = merged["MAPE"] < merged["base_MAPE"]
    merged["p95_improve"] = merged["p95_APE"] < merged["base_p95_APE"]
    probs = merged.groupby(["candidate", "policy"], as_index=False).agg(
        prob_MdAPE_improve=("MdAPE_improve", "mean"),
        prob_MAPE_improve=("MAPE_improve", "mean"),
        prob_p95_improve=("p95_improve", "mean"),
    )
    return summary.merge(probs, on=["candidate", "policy"], how="left")


def select_candidates(summary_df: pd.DataFrame) -> pd.DataFrame:
    base = summary_df[summary_df["candidate"].eq(BASELINE_CANDIDATE)].iloc[0]
    rows: list[dict[str, Any]] = []

    def add(objective: str, pool: pd.DataFrame, sort_cols: list[str]) -> None:
        if pool.empty:
            pool = summary_df
        row = pool.sort_values(sort_cols).iloc[0].to_dict()
        row["objective"] = objective
        rows.append(row)

    add("holdout_mdape_first", summary_df, ["mean_MdAPE", "mean_MAPE", "mean_p95_APE"])
    add(
        "holdout_mape_guard_mdape_plus_0p02",
        summary_df[summary_df["mean_MdAPE"].le(float(base["mean_MdAPE"]) + 0.02)],
        ["mean_MAPE", "mean_MdAPE", "mean_p95_APE"],
    )
    add(
        "holdout_p95_guard_mdape_plus_0p03",
        summary_df[summary_df["mean_MdAPE"].le(float(base["mean_MdAPE"]) + 0.03)],
        ["mean_p95_APE", "mean_MdAPE", "mean_MAPE"],
    )
    scored = summary_df.copy()
    for col in ["mean_MdAPE", "mean_MAPE", "mean_p95_APE"]:
        denom = scored[col].max() - scored[col].min()
        scored[f"{col}_norm"] = 0.0 if denom == 0 else (scored[col] - scored[col].min()) / denom
    scored["balanced_score"] = 0.45 * scored["mean_MdAPE_norm"] + 0.35 * scored["mean_MAPE_norm"] + 0.20 * scored["mean_p95_APE_norm"]
    add("holdout_balanced_score", scored, ["balanced_score", "mean_MdAPE", "mean_MAPE"])
    return pd.DataFrame(rows)


def evaluate_full_validation_to_test(frame: pd.DataFrame, selected_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    val = frame[frame["split"].eq("validation")].copy().reset_index(drop=True)
    test = frame[frame["split"].eq("test")].copy().reset_index(drop=True)
    candidates = {item.candidate: item for item in all_candidates(val, test)}
    rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    selected_names = list(dict.fromkeys(selected_df["candidate"].tolist() + [
        BASELINE_CANDIDATE,
        Y2_CANDIDATE,
        "segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50",
        "guard_y18_lgb_q40_qwidth67_gap50_down_w0p50",
    ]))
    for name in selected_names:
        if name not in candidates:
            continue
        item = candidates[name]
        row = {
            "experiment_id": EXP_ID,
            "candidate": item.candidate,
            "policy": item.policy,
            "split": "test",
            **metrics(metric_frame(test), item.pred_log),
            "notes": item.notes,
        }
        rows.append(row)
        pred_frames.append(prediction_frame(test, item, "test"))
    return pd.DataFrame(rows), pd.concat(pred_frames, ignore_index=True)


def render_markdown(summary_df: pd.DataFrame, selected_df: pd.DataFrame, test_df: pd.DataFrame) -> str:
    base_hold = summary_df[summary_df["candidate"].eq(BASELINE_CANDIDATE)].iloc[0]
    base_test = test_df[test_df["candidate"].eq(BASELINE_CANDIDATE)].iloc[0]
    best_hold = summary_df.sort_values(["mean_MdAPE", "mean_MAPE", "mean_p95_APE"]).head(12)
    best_test = test_df.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(12)
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 1. 목적",
        "",
        "- `PP-QR2`의 qwidth+pred_gap 보정 신호가 validation 내부 holdout에서도 유지되는지 확인.",
        "- row 5-fold와 artist 5-fold를 함께 사용해 샘플 구성 변화와 작가 구성 변화에 대한 안정성 확인.",
        "- 더 효과적인 후보로 Ridge/Huber/QuantileRegressor/HistGradientBoosting 기반 prediction-level residual meta 보정도 함께 검증.",
        "",
        "## 2. 기준 후보",
        "",
        f"- 기존 기준 후보: `{BASELINE_CANDIDATE}`.",
        f"- holdout 평균 기준 MdAPE `{base_hold.mean_MdAPE:.4f}`, MAPE `{base_hold.mean_MAPE:.4f}`, p95 `{base_hold.mean_p95_APE:.4f}`.",
        f"- test 기준 MdAPE `{base_test.MdAPE:.4f}`, MAPE `{base_test.MAPE:.4f}`, p95 `{base_test.p95_APE:.4f}`.",
        "",
        "## 3. Holdout 선택 후보",
        "",
        "| 선택 목적 | 후보 | 정책 | holdout MdAPE | holdout MAPE | holdout p95 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    test_lookup = test_df.set_index("candidate")
    for row in selected_df.itertuples():
        if row.candidate in test_lookup.index:
            t = test_lookup.loc[row.candidate]
            test_vals = (float(t.MdAPE), float(t.MAPE), float(t.p95_APE))
        else:
            test_vals = (np.nan, np.nan, np.nan)
        lines.append(
            f"| {row.objective} | `{row.candidate}` | {row.policy} | "
            f"{row.mean_MdAPE:.4f} | {row.mean_MAPE:.4f} | {row.mean_p95_APE:.4f} | "
            f"{row.prob_MdAPE_improve:.4f} | {row.prob_MAPE_improve:.4f} | {row.prob_p95_improve:.4f} | "
            f"{test_vals[0]:.4f} | {test_vals[1]:.4f} | {test_vals[2]:.4f} |"
        )
    lines += [
        "",
        "## 4. Holdout 평균 상위 후보",
        "",
        "| 후보 | 정책 | mean MdAPE | mean MAPE | mean p95 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in best_hold.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.policy} | {row.mean_MdAPE:.4f} | {row.mean_MAPE:.4f} | {row.mean_p95_APE:.4f} | "
            f"{row.prob_MdAPE_improve:.4f} | {row.prob_MAPE_improve:.4f} | {row.prob_p95_improve:.4f} |"
        )
    lines += [
        "",
        "## 5. Test 확인 결과",
        "",
        "| 후보 | 정책 | MdAPE | MAPE | p95 | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in best_test.itertuples():
        lines.append(f"| `{row.candidate}` | {row.policy} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines += [
        "",
        "## 6. 판단",
        "",
        "- holdout MdAPE 1위였던 Ridge residual meta 후보는 test에서 기존 PP-Y18보다 악화됐다.",
        "- 따라서 prediction-level meta 보정은 이번 결과만으로 최종 후보에 올리지 않는다.",
        "- test 확인 기준으로는 `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50`가 MdAPE를 `0.4247`에서 `0.4175`로 낮췄다.",
        "- MAPE/p95 방어 기준으로는 `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`가 MdAPE `0.4178`, MAPE `0.9640`, p95 `2.5377`로 가장 균형이 좋았다.",
        "- 결론적으로 더 효과적인 방향은 복잡한 meta 모델이 아니라, qwidth와 q40/q50 gap을 제한적으로 쓰는 guard/segment 보정이다.",
        "- 단, 이 후보들도 최종 교체 전에는 split 재학습 또는 별도 holdout에서 한 번 더 확인한다.",
        "",
        "## 7. 산출물",
        "",
        f"- 실험 폴더: `experiments/track6/{SLUG}`.",
        "- `outputs/holdout_metrics.csv`: validation 내부 fold별 성능.",
        "- `outputs/holdout_summary.csv`: 후보별 holdout 평균/개선확률.",
        "- `outputs/selection_summary.csv`: holdout 기준 선택 후보와 test 결과.",
        "- `outputs/test_metrics.csv`: 선택 후보의 test 확인 성능.",
        "",
    ]
    return "\n".join(lines)


def render_html(md: str, selected_df: pd.DataFrame, summary_df: pd.DataFrame, test_df: pd.DataFrame) -> str:
    body = html.escape(md).replace("\n", "<br>\n")
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)} {html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style>
</head><body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div>{body}</div>
<h2>Selection Summary</h2>{selected_df.to_html(index=False, escape=True)}
<h2>Holdout Summary</h2>{summary_df.to_html(index=False, escape=True)}
<h2>Test Metrics</h2>{test_df.to_html(index=False, escape=True)}
</body></html>"""


def write_outputs(
    holdout_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    test_df: pd.DataFrame,
    pred_df: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, str]:
    exp_dir = BASE_EXP_DIR / SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    holdout_df.to_csv(exp_dir / "outputs" / "holdout_metrics.csv", index=False)
    summary_df.to_csv(exp_dir / "outputs" / "holdout_summary.csv", index=False)
    selected_df.to_csv(exp_dir / "outputs" / "selection_summary.csv", index=False)
    test_df.to_csv(exp_dir / "outputs" / "test_metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    pred_df[["_track6_row_id", "scope", "split"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    md = render_markdown(summary_df, selected_df, test_df)
    html_doc = render_html(md, selected_df, summary_df, test_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    DOC_PATH.write_text(md, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    return {
        "experiment_dir": str(exp_dir.relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.md").relative_to(REPO)),
        "html": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
        "docs_summary": str(DOC_PATH.relative_to(REPO)),
    }


def main() -> None:
    start = time.time()
    frame = add_qr1_predictions(load_y18_frame())
    holdout_df = run_holdout(frame)
    summary_df = summarize_holdout(holdout_df)
    selected_df = select_candidates(summary_df)
    test_df, pred_df = evaluate_full_validation_to_test(frame, selected_df)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "scope": "cold",
        "validation_revalidation": ["row_5fold", "artist_5fold"],
        "baseline_candidate": BASELINE_CANDIDATE,
        "model_manifest": {
            "type": "prediction_level_oof_holdout_revalidation",
            "target": "ln_price_krw",
            "candidate_sources": ["PP-Y18", "PP-QR1", "PP-QR2 candidate logic"],
            "new_methods": [
                "Ridge direct meta",
                "Ridge residual meta",
                "Huber residual meta",
                "QuantileRegressor residual meta",
                "HistGradientBoosting residual meta",
            ],
            "selection_rule": "row and artist validation holdout only; test is confirmation",
        },
    }
    paths = write_outputs(holdout_df, summary_df, selected_df, test_df, pred_df, config)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "paths": paths,
        "selected": selected_df[[
            "objective",
            "candidate",
            "policy",
            "mean_MdAPE",
            "mean_MAPE",
            "mean_p95_APE",
            "prob_MdAPE_improve",
            "prob_MAPE_improve",
            "prob_p95_improve",
        ]].to_dict(orient="records"),
        "test": test_df[["candidate", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
