#!/usr/bin/env python3
"""PP-ROUTE-CF2: Warm vs Warm-lite k=1..6 same-row counterfactual.

Purpose:
- Compare Warm-style and Warm-lite-style prediction when the same Warm fixed-test
  artworks are exposed to exactly k same-artist train-history rows.
- Use the same eligible rows for k=1..6 so the comparison is not distorted by
  different evaluation n.

Important scope note:
- Warm-lite forced k=1..6 uses the frozen Warm-lite Quantile + LightGBM Huber
  residual bundle. k=5..6 are out-of-route stress cases.
- Warm forced k=1..6 is a WMIN8-shell comparator: the same-artist comparable
  Huber axis is retrained after k-truncation, then passed through the frozen
  WMIN8 Huber/refit/router shell with the stable upstream context held fixed.
  This is not a full upstream WMIN8 retraining.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", message="X does not have valid feature names")

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF2_warm_vs_warm_lite_k1_to_k6_counterfactual"

WARM_FIXED_STORE = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate" / "artifacts" / "fixed_test_feature_store.csv"
WARM_RUNTIME = REPO / "models" / "track6" / "warm_wmin8_exact_runtime_candidate" / "artifacts" / "wmin8_huber_runtime.json"
WARM_OPERATIONAL = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "artifacts" / "wmin8_selected_candidate_predictions.csv"
WLITE_PREDICTOR = (
    REPO
    / "models"
    / "track6"
    / "warm_lite_quantile_residual_v0.1"
    / "predict"
    / "predict_warm_lite_quantile_residual_v0_1.py"
)

TRUNC_SEEDS = [20260612, 20260613, 20260614]
KS = [1, 2, 3, 4, 5, 6]
WMIN8_ROUTE_THRESHOLD = 0.2534165869100283
WMIN8_ROUTE_GAP = 0.005
WARM_CANDIDATE = "min1_route_w850_risk_q50_altlower_gap005"


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "logs", "scripts"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


def load_warm_lite_module():
    spec = importlib.util.spec_from_file_location("warm_lite_quantile_residual_v0_1", WLITE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Warm-lite predictor from {WLITE_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fmt(value: Any) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if np.isfinite(value):
            if abs(float(value) - round(float(value))) < 1e-9 and abs(float(value)) >= 1:
                return str(int(round(float(value))))
            return f"{float(value):.6f}"
        return ""
    return str(value)


def md_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 120) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in cols) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    pred_price = np.clip(np.exp(pred_log[valid]), 1_000.0, None)
    ape = np.abs(pred_price - actual_price[valid]) / np.clip(actual_price[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log[valid] - actual_log[valid]) ** 2))),
    }


def add_ape(frame: pd.DataFrame, pred_col: str, out_col: str) -> pd.DataFrame:
    out = frame.copy()
    pred_price = np.clip(np.exp(pd.to_numeric(out[pred_col], errors="coerce")), 1_000.0, None)
    actual = pd.to_numeric(out["actual_price"], errors="coerce")
    out[out_col] = np.abs(pred_price - actual) / np.clip(actual, 1.0, None)
    return out


def risk_score(meta: pd.DataFrame) -> np.ndarray:
    qwidth = pd.to_numeric(meta["quantile_width"], errors="coerce").fillna(1.50).to_numpy(dtype=float)
    spread = pd.to_numeric(meta["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(meta["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    confidence = meta["confidence_tier"].fillna("medium_confidence").astype(str)
    price = meta["stable_price_band"].fillna("unknown_price").astype(str)
    return np.clip(
        0.38 * np.clip((qwidth - 1.20) / 0.95, 0.0, 1.0)
        + 0.22 * np.clip(spread / 0.18, 0.0, 1.0)
        + 0.14 * np.clip(gap / 0.06, 0.0, 1.0)
        + 0.16 * confidence.eq("low_confidence").to_numpy(dtype=float)
        + 0.10 * price.eq("very_high_price").to_numpy(dtype=float),
        0.0,
        1.0,
    )


def patch_svc_min1() -> None:
    for group_def in svc1.GROUP_DEFS:
        if "artist_key" in group_def["keys"]:
            group_def["min_n"] = 1


def truncate_train(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep: list[np.ndarray] = []
    for artist, idx in train.groupby(train["artist_key"].astype(str), sort=False).indices.items():
        idx_arr = np.asarray(idx, dtype=int)
        if artist in target_artists and len(idx_arr) > k:
            keep.append(np.asarray(rng.choice(idx_arr, size=k, replace=False), dtype=int))
        else:
            keep.append(idx_arr)
    return train.iloc[np.concatenate(keep)].sort_values("_track6_row_id").reset_index(drop=True)


def load_operational_baseline(row_ids: set[int]) -> pd.DataFrame:
    raw = pd.read_csv(WARM_OPERATIONAL, low_memory=False)
    out = raw[
        raw["eval_split"].eq("test")
        & raw["candidate_label"].eq(WARM_CANDIDATE)
        & raw["_track6_row_id"].astype(int).isin(row_ids)
    ].copy()
    out = out[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "warm_wmin8_operational_pred_log"})
    if out["_track6_row_id"].nunique() != len(row_ids):
        raise RuntimeError(f"Operational baseline row mismatch: got {out['_track6_row_id'].nunique()} expected {len(row_ids)}")
    return out.sort_values("_track6_row_id").reset_index(drop=True)


def load_frames(warm_lite) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    warm_base = artifact_features()["warm"]
    requested = list(dict.fromkeys([*warm_base, *svc1.GROUPING_FEATURES, *warm_lite.REQUIRED]))
    train, _val, test = load_scope("warm", requested)

    fixed = pd.read_csv(WARM_FIXED_STORE, low_memory=False)
    fixed = fixed[fixed["eval_split"].eq("test")].copy()
    fixed["_track6_row_id"] = fixed["_track6_row_id"].astype(int)

    counts = train.groupby(train["artist_key"].astype(str)).size()
    test = test.copy()
    test["_track6_row_id"] = test["_track6_row_id"].astype(int)
    test["full_train_artist_history_n"] = test["artist_key"].astype(str).map(counts).fillna(0).astype(int)

    # Main table must support exact k=1..6 for every evaluated row.
    eligible_ids = set(test.loc[test["full_train_artist_history_n"] >= max(KS), "_track6_row_id"].astype(int))
    fixed = fixed[fixed["_track6_row_id"].isin(eligible_ids)].sort_values("_track6_row_id").reset_index(drop=True)
    test = test[test["_track6_row_id"].isin(eligible_ids)].sort_values("_track6_row_id").reset_index(drop=True)
    if len(test) != len(fixed) or set(test["_track6_row_id"]) != set(fixed["_track6_row_id"]):
        raise RuntimeError("Warm fixed store and warm test frame do not align after k=6 eligibility filtering")

    audit = {
        "warm_fixed_test_rows_total": 607,
        "exact_k1_to_k6_eligible_rows": int(len(test)),
        "excluded_rows_with_only_5_train_history": int(607 - len(test)),
        "min_full_train_artist_history_n": int(test["full_train_artist_history_n"].min()),
        "max_full_train_artist_history_n": int(test["full_train_artist_history_n"].max()),
    }
    return train.reset_index(drop=True), test.reset_index(drop=True), fixed.reset_index(drop=True), audit


def run_warm_lite_condition(
    warm_lite,
    params: dict[str, Any],
    models: dict[str, Any],
    train_k: pd.DataFrame,
    test: pd.DataFrame,
    trunc_seed: int,
    k: int,
) -> pd.DataFrame:
    train_by_artist = {str(artist): group.copy() for artist, group in train_k.groupby("artist_key", sort=False)}
    parts = []
    for artist_key, group in test.groupby(test["artist_key"].astype(str), sort=False):
        artist_history = train_by_artist.get(str(artist_key))
        if artist_history is None or len(artist_history) != k:
            raise RuntimeError(f"Expected exactly k={k} history rows for artist_key={artist_key!r}; got {0 if artist_history is None else len(artist_history)}")
        fs = warm_lite.assign_stats(group.copy(), artist_history, params)
        qpred = warm_lite._predict_quantiles(models, fs, params)
        residual_x = warm_lite._residual_feature_frame(fs, qpred, params)
        residual = np.asarray(models["lightgbm_residual"].predict(residual_x), dtype=float)
        raw_correction = float(params["residual_strength"]) * residual
        applied_correction = np.clip(
            raw_correction,
            -float(params["residual_cap_log"]),
            float(params["residual_cap_log"]),
        )
        pred_log = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + applied_correction

        out = group[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
        out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
        out["candidate"] = "Warm-lite forced"
        out["trunc_seed"] = trunc_seed
        out["k"] = k
        out["pred_log"] = pred_log
        out["artist_history_n"] = int(len(artist_history))
        out["q10_log"] = qpred["lgbq_full_q10"].to_numpy(dtype=float)
        out["q50_log"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
        out["q90_log"] = qpred["lgbq_full_q90"].to_numpy(dtype=float)
        out["quantile_uncertainty_width_log"] = qpred["lgbq_width"].to_numpy(dtype=float)
        out["raw_residual_correction_log"] = raw_correction
        out["applied_residual_correction_log"] = applied_correction
        parts.append(out)
    return pd.concat(parts, ignore_index=True).sort_values("_track6_row_id").reset_index(drop=True)


def refit_predict(model: Any, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    runtime = json.loads(WARM_RUNTIME.read_text(encoding="utf-8"))
    stable = runtime["stable_config"]
    raw = np.asarray(model.predict(frame[features]), dtype=float)
    correction = np.clip(raw, -float(stable["cap"]), float(stable["cap"]))
    correction = correction * float(stable["strength"])
    return frame["current_70_30"].to_numpy(dtype=float) + correction


def warm_refit_frame(
    fixed: pd.DataFrame,
    held_svc: pd.DataFrame,
    svc_pred: np.ndarray,
    current: np.ndarray,
) -> pd.DataFrame:
    frame = fixed.copy()
    frame["current_70_30"] = np.asarray(current, dtype=float)
    frame["svc_fallback"] = np.asarray(svc_pred, dtype=float)
    if "baseline_huber" not in frame.columns:
        frame["baseline_huber"] = pd.to_numeric(frame["ppv8_defensive"], errors="coerce")

    svc_cols = ["_track6_row_id", "svc_group_n", "svc_group_log_price_iqr", "svc_group_level", "svc_coverage_tier"]
    svc_view = held_svc[svc_cols].copy()
    frame = frame.drop(columns=[c for c in svc_cols if c in frame.columns and c != "_track6_row_id"], errors="ignore")
    frame = frame.merge(svc_view, on="_track6_row_id", how="left", validate="one_to_one")
    frame["svc_group_n_log"] = np.log1p(pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0.0))
    frame["svc_prior_iqr"] = pd.to_numeric(frame["svc_group_log_price_iqr"], errors="coerce")
    frame["svc_prior_iqr"] = frame["svc_prior_iqr"].fillna(frame["svc_prior_iqr"].median())
    return hcoef1.add_derived_features(frame, "test")


def run_warm_shell_condition(
    train_k: pd.DataFrame,
    test: pd.DataFrame,
    fixed: pd.DataFrame,
    runtime: dict[str, Any],
    models: dict[str, Any],
    features: list[str],
    trunc_seed: int,
    k: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    patch_svc_min1()
    train_stats = svc1.crossfit_train_stats(train_k)
    train_full = train_k.merge(train_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    held_stats = svc1.apply_comparable_stats(train_k, test)
    held_full = test.merge(held_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))

    pred = svc1.fit_predict("huber", train_full, held_full, held_full, features)
    svc_pred = np.asarray(pred["validation"], dtype=float)
    ppv8 = fixed["ppv8_defensive"].to_numpy(dtype=float)

    base_current = 0.70 * svc_pred + 0.30 * ppv8
    alt_current = 0.85 * svc_pred + 0.15 * ppv8
    base_frame = warm_refit_frame(fixed, held_full, svc_pred, base_current)
    alt_frame = warm_refit_frame(fixed, held_full, svc_pred, alt_current)

    feature_columns = runtime["feature_columns"]
    base_pred = refit_predict(models["base_w700"], base_frame, feature_columns)
    alt_pred = refit_predict(models["alternative_w850"], alt_frame, feature_columns)

    route_meta = fixed.copy()
    route_meta["component_prediction_spread"] = np.abs(svc_pred - ppv8)
    route_meta["current_vs_stable_gap_abs"] = np.abs(base_current - ppv8)
    risk = risk_score(route_meta)
    route_to_alt = (
        (risk >= WMIN8_ROUTE_THRESHOLD)
        & (alt_pred < base_pred)
        & ((base_pred - alt_pred) >= WMIN8_ROUTE_GAP)
    )
    routed = np.where(route_to_alt, alt_pred, base_pred)

    out = test[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
    out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
    out["candidate"] = "Warm WMIN8-shell forced"
    out["trunc_seed"] = trunc_seed
    out["k"] = k
    out["pred_log"] = routed
    out["artist_history_n"] = k
    out["svc_core_pred_log"] = svc_pred
    out["base_w700_pred_log"] = base_pred
    out["alternative_w850_pred_log"] = alt_pred
    out["route_to_alternative"] = route_to_alt
    out["risk_score"] = risk
    out["svc_group_level"] = held_full["svc_group_level"].to_numpy()
    out["svc_coverage_tier"] = held_full["svc_coverage_tier"].to_numpy()
    out["svc_group_n"] = held_full["svc_group_n"].to_numpy()

    audit = out[
        [
            "trunc_seed",
            "k",
            "_track6_row_id",
            "artist_key",
            "svc_core_pred_log",
            "base_w700_pred_log",
            "alternative_w850_pred_log",
            "route_to_alternative",
            "risk_score",
            "svc_group_level",
            "svc_coverage_tier",
            "svc_group_n",
        ]
    ].copy()
    return out.sort_values("_track6_row_id").reset_index(drop=True), audit.sort_values("_track6_row_id").reset_index(drop=True)


def repeated_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, seed, k), group in predictions.groupby(["candidate", "trunc_seed", "k"], sort=True):
        row = {"candidate": candidate, "trunc_seed": int(seed), "k": int(k)}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "candidate", "trunc_seed"]).reset_index(drop=True)


def seed_mean_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    return (
        predictions.groupby(["candidate", "k", "_track6_row_id"], as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values(["k", "candidate", "_track6_row_id"])
        .reset_index(drop=True)
    )


def same_n_metrics(seed_mean: pd.DataFrame, operational: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, k), group in seed_mean.groupby(["candidate", "k"], sort=True):
        row = {"candidate": candidate, "k": int(k), "condition": f"k={int(k)} seed-mean"}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)

    base = actual.merge(operational, on="_track6_row_id", how="left", validate="one_to_one")
    row = {"candidate": "Warm WMIN8 operational", "k": 0, "condition": "current 5+ route baseline"}
    row.update(metrics(base["actual_price"].to_numpy(), base["actual_log"].to_numpy(), base["warm_wmin8_operational_pred_log"].to_numpy()))
    rows.append(row)

    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out.sort_values(["k", "candidate"]).reset_index(drop=True)


def paired_by_k(seed_mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    warm = seed_mean[seed_mean["candidate"].eq("Warm WMIN8-shell forced")].rename(columns={"pred_log": "warm_pred_log"})
    lite = seed_mean[seed_mean["candidate"].eq("Warm-lite forced")].rename(columns={"pred_log": "warm_lite_pred_log"})
    wide = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "k", "warm_pred_log"]].merge(
        lite[["_track6_row_id", "k", "warm_lite_pred_log"]],
        on=["_track6_row_id", "k"],
        how="inner",
        validate="one_to_one",
    )
    wide = add_ape(wide, "warm_pred_log", "warm_ape")
    wide = add_ape(wide, "warm_lite_pred_log", "warm_lite_ape")
    rows = []
    for k, group in wide.groupby("k", sort=True):
        warm_ape = group["warm_ape"].to_numpy(dtype=float)
        lite_ape = group["warm_lite_ape"].to_numpy(dtype=float)
        rows.append(
            {
                "k": int(k),
                "n": int(len(group)),
                "warm_better_share": float(np.mean(warm_ape < lite_ape)),
                "warm_lite_better_share": float(np.mean(lite_ape < warm_ape)),
                "tie_share": float(np.mean(np.isclose(warm_ape, lite_ape))),
                "median_ape_delta_warm_minus_warm_lite": float(np.nanmedian(warm_ape - lite_ape)),
                "mean_ape_delta_warm_minus_warm_lite": float(np.nanmean(warm_ape - lite_ape)),
            }
        )
    return pd.DataFrame(rows), wide


def write_report(
    metrics_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
    paired_df: pd.DataFrame,
    route_audit: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    main = metrics_df[metrics_df["k"].ne(0)].copy()
    best_by_metric = {
        metric: str(main.sort_values(metric).iloc[0]["candidate"]) + " " + str(main.sort_values(metric).iloc[0]["condition"])
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    }
    warm_k6 = main[(main["candidate"].eq("Warm WMIN8-shell forced")) & (main["k"].eq(6))].iloc[0]
    lite_k6 = main[(main["candidate"].eq("Warm-lite forced")) & (main["k"].eq(6))].iloc[0]
    route_summary = (
        route_audit.groupby(["trunc_seed", "k"], as_index=False)
        .agg(route_to_alt_share=("route_to_alternative", "mean"), median_risk_score=("risk_score", "median"))
        .sort_values(["k", "trunc_seed"])
    )
    lines = [
        "# PP-ROUTE-CF2 Warm vs Warm-lite k=1~6 Same-Row Counterfactual",
        "",
        "## 1. 목적",
        "",
        "Warm fixed-test 작품 중 같은 작가 train 이력이 6건 이상 있는 동일 작품만 사용해, Warm과 Warm-lite를 각각 k=1~6 이력 노출 조건으로 비교한다.",
        "",
        "## 2. 해석 범위",
        "",
        "- 주 비교 n은 519개다. Warm fixed-test 607개 중 88개는 train 이력이 정확히 6건까지 없어서 k=1~6 동일 n 비교에서 제외했다.",
        "- Warm-lite forced k=1~6은 최신 Warm-lite Quantile + LightGBM Huber residual 번들을 강제 적용한 값이다. k=5~6은 실제 라우팅 범위 밖의 스트레스 비교다.",
        "- Warm WMIN8-shell forced k=1~6은 같은작가 비교군 Huber 축을 k건 이력으로 재학습하고, WMIN8의 Huber/refit/router shell에 통과시킨 비교용 값이다.",
        "- Warm WMIN8-shell은 PPV8/V2 등 상류 Warm stack 전체를 k별로 재학습한 완전한 full WMIN8이 아니다. 따라서 운영 확정 기준선은 `Warm WMIN8 operational`을 별도로 본다.",
        "",
        "## 3. Same-n seed-mean metrics",
        "",
        md_table(metrics_df, ["candidate", "condition", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 4. 관찰 요약",
        "",
        f"- Best by MdAPE: `{best_by_metric['MdAPE']}`.",
        f"- Best by MAPE: `{best_by_metric['MAPE']}`.",
        f"- Best by p95 APE: `{best_by_metric['p95_APE']}`.",
        f"- Best by RMSE log: `{best_by_metric['RMSE_log']}`.",
        f"- k=6에서 Warm WMIN8-shell vs Warm-lite: MdAPE `{warm_k6['MdAPE']:.6f}` vs `{lite_k6['MdAPE']:.6f}`, MAPE `{warm_k6['MAPE']:.6f}` vs `{lite_k6['MAPE']:.6f}`, p95 `{warm_k6['p95_APE']:.6f}` vs `{lite_k6['p95_APE']:.6f}`.",
        "",
        "## 5. Paired row-level comparison",
        "",
        md_table(paired_df, ["k", "n", "warm_better_share", "warm_lite_better_share", "median_ape_delta_warm_minus_warm_lite", "mean_ape_delta_warm_minus_warm_lite"], 20),
        "",
        "## 6. Repeated seed metrics",
        "",
        md_table(repeated_df, ["candidate", "trunc_seed", "k", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 80),
        "",
        "## 7. Warm shell route audit",
        "",
        md_table(route_summary, ["trunc_seed", "k", "route_to_alt_share", "median_risk_score"], 40),
        "",
        "## 8. 결론 사용법",
        "",
        "- 이 표는 Warm/Warm-lite 라우팅 경계 설명용 same-n 실험이다.",
        "- Warm-lite k=5~6이 좋아 보이더라도 실제 운영에서 5건 이상을 Warm-lite로 보내자는 결론으로 바로 연결하면 안 된다. k=5~6은 out-of-route 강제 적용이기 때문이다.",
        "- Warm WMIN8-shell이 좋아 보이더라도 full WMIN8 전체 재학습 결과는 아니다. 운영 모델 설명에서는 현행 Warm WMIN8 operational 성능과 함께 보조 근거로 사용한다.",
        "",
        "## 9. Config",
        "",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.time()
    ensure_dirs()

    warm_lite = load_warm_lite_module()
    wl_params = warm_lite.load_params()
    wl_models = warm_lite.load_models()
    train, test, fixed, eligibility_audit = load_frames(warm_lite)
    target_artists = set(test["artist_key"].astype(str))

    runtime = json.loads(WARM_RUNTIME.read_text(encoding="utf-8"))
    warm_model_root = WARM_RUNTIME.parents[1]
    warm_models = {
        "base_w700": joblib.load(warm_model_root / runtime["models"]["base_w700"]["model_file"]),
        "alternative_w850": joblib.load(warm_model_root / runtime["models"]["alternative_w850"]["model_file"]),
    }
    warm_features = svc1.candidate_features(artifact_features()["warm"])["svc_numeric"]
    actual = test[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].rename(
        columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"}
    )
    operational = load_operational_baseline(set(test["_track6_row_id"].astype(int)))

    pred_parts: list[pd.DataFrame] = []
    audit_parts: list[pd.DataFrame] = []
    for seed in TRUNC_SEEDS:
        for k in KS:
            condition_start = time.time()
            train_k = truncate_train(train, target_artists, seed, k)
            lite = run_warm_lite_condition(warm_lite, wl_params, wl_models, train_k, test, seed, k)
            warm, warm_audit = run_warm_shell_condition(train_k, test, fixed, runtime, warm_models, warm_features, seed, k)
            pred_parts.extend([lite, warm])
            audit_parts.append(warm_audit)
            print(
                json.dumps(
                    {
                        "done": "condition",
                        "seed": seed,
                        "k": k,
                        "rows": len(test),
                        "seconds": round(time.time() - condition_start, 2),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    predictions = pd.concat(pred_parts, ignore_index=True)
    route_audit = pd.concat(audit_parts, ignore_index=True)
    repeated_df = repeated_metrics(predictions)
    seed_mean = seed_mean_predictions(predictions)
    if not seed_mean["seed_n"].eq(len(TRUNC_SEEDS)).all():
        raise RuntimeError("Seed mean table has missing truncation seeds")
    metrics_df = same_n_metrics(seed_mean, operational, actual)
    paired_df, paired_rows = paired_by_k(seed_mean)

    predictions.to_csv(EXP / "outputs" / "predictions_all_conditions.csv", index=False)
    route_audit.to_csv(EXP / "outputs" / "warm_shell_route_audit.csv", index=False)
    repeated_df.to_csv(EXP / "outputs" / "repeated_condition_metrics.csv", index=False)
    seed_mean.to_csv(EXP / "outputs" / "seed_mean_predictions_by_k.csv", index=False)
    metrics_df.to_csv(EXP / "outputs" / "same_n_metrics_by_k.csv", index=False)
    paired_df.to_csv(EXP / "outputs" / "paired_warm_vs_warm_lite_by_k.csv", index=False)
    paired_rows.to_csv(EXP / "outputs" / "paired_row_level_ape_by_k.csv", index=False)
    operational.to_csv(EXP / "outputs" / "warm_operational_baseline_predictions.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF2",
        "experiment_slug": EXP.name,
        "trunc_seeds": TRUNC_SEEDS,
        "k_values": KS,
        "base_eval_set": "Warm fixed-test rows with >=6 same-artist train history rows",
        "eligibility_audit": eligibility_audit,
        "warm_lite_source": str(WLITE_PREDICTOR.relative_to(REPO)),
        "warm_lite_design": "frozen official v0.1 Warm-lite Quantile + LightGBM Huber residual bundle, forced to k=1..6; k=5..6 are out-of-route stress cases",
        "warm_shell_sources": {
            "fixed_feature_store": str(WARM_FIXED_STORE.relative_to(REPO)),
            "runtime": str(WARM_RUNTIME.relative_to(REPO)),
            "operational_baseline": str(WARM_OPERATIONAL.relative_to(REPO)),
        },
        "warm_shell_design": "SVC comparable-stat Huber axis retrained after k-truncating target artists; PPV8/shrinkage stable context held fixed; WMIN8 Huber refit and risk router applied",
        "route_threshold": WMIN8_ROUTE_THRESHOLD,
        "route_gap": WMIN8_ROUTE_GAP,
        "limitations": [
            "Warm WMIN8-shell forced k=1..6 is not full upstream WMIN8 retraining.",
            "Warm-lite forced k=5..6 is outside the official Warm-lite route and is used only for route-boundary stress comparison.",
            "Main same-n table excludes 88 Warm fixed-test rows with only 5 available same-artist train-history rows so every k=1..6 condition has exactly the same rows.",
        ],
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, repeated_df, paired_df, route_audit, config)

    print("[same-n metrics]")
    print(metrics_df.to_string(index=False))
    print("\n[paired by k]")
    print(paired_df.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
