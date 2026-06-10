#!/usr/bin/env python3
"""Run PP-HCOEF26: gated reuse of HCOEF25 Warm Huber candidates.

HCOEF25 improved MdAPE/MAPE slightly, but its best purpose candidates missed the
fixed-test p95 guard by a small margin. HCOEF26 does not tune from fixed-test
residuals. Instead, it reuses HCOEF25 validation-first candidates and tests
whether their movement should be applied only in low-risk/reliable segments while
falling back to the current stable Warm candidate elsewhere.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef24_warm_huber_price_basis_coefficient_refinement as h24
from scripts.track6 import run_pp_hcoef25_warm_huber_price_basis_coefficient_refinement as h25


EXP_ID = "PP-HCOEF26"
EXP_SLUG = "PP-HCOEF26_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
H25_DIR = REPO / "experiments" / "track6" / "PP-HCOEF25_warm_huber_price_basis_coefficient_refinement"

BASELINE = h25.BASELINE
REFERENCE = h25.REFERENCE
PPV8 = h25.PPV8
SVC = h25.SVC
L10_COL = h25.L10_COL
SEED = h24.SEED
N_BOOTSTRAP = h24.N_BOOTSTRAP

META_COLS = [
    "experiment_id",
    "scope",
    "split",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "actual_log",
    "actual_price",
    BASELINE,
    REFERENCE,
    PPV8,
    SVC,
    L10_COL,
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "svc_coverage_tier",
    "svc_group_level",
    "service_confidence_tier",
    "qwidth_band",
    "svc_group_n_band",
    "gap_band",
    "pred_spread_band",
    "stable_pred_price_band",
    "medium_support_bucket",
    "log_area",
    "hcoef23_risk_score",
    "hcoef23_risk_factor",
]


@dataclass(frozen=True)
class HybridConfig:
    candidate: str
    method: str
    source_candidate: str
    mask_name: str
    strength: float
    cap: float | None
    purpose: str


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def slug_float(value: float) -> str:
    return h24.slug_float(value)


def metric_from_pred(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return h24.h20.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def select_h25_source_candidates(limit: int = 14) -> list[str]:
    """Choose HCOEF25 sources by validation evidence, not fixed-test residuals."""
    metrics = pd.read_csv(H25_DIR / "outputs" / "metrics.csv")
    row = metrics[metrics["scope"].eq("validation_oof_row")].copy()
    artist = metrics[metrics["scope"].eq("validation_oof_artist")].copy()
    cols = [
        "candidate",
        "method",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "delta_MdAPE_vs_stable",
        "delta_MAPE_vs_stable",
        "delta_p95_APE_vs_stable",
        "improve_count_vs_stable",
    ]
    merged = row[cols].rename(columns={c: f"row_{c}" for c in cols if c not in {"candidate", "method"}})
    merged = merged.merge(
        artist[cols].drop(columns=["method"]).rename(columns={c: f"artist_{c}" for c in cols if c != "candidate"}),
        on="candidate",
        how="inner",
    )
    merged = merged[~merged["method"].eq("source")].copy()
    merged = merged[
        (merged["row_improve_count_vs_stable"] >= 2)
        & (merged["artist_improve_count_vs_stable"] >= 2)
        & (
            (merged["row_delta_MdAPE_vs_stable"] < 0)
            | (merged["row_delta_MAPE_vs_stable"] < 0)
            | (merged["artist_delta_MdAPE_vs_stable"] < 0)
            | (merged["artist_delta_MAPE_vs_stable"] < 0)
        )
    ].copy()
    merged["validation_score"] = (
        merged["row_delta_MdAPE_vs_stable"]
        + merged["row_delta_MAPE_vs_stable"]
        + merged["row_delta_p95_APE_vs_stable"]
        + merged["artist_delta_MdAPE_vs_stable"]
        + merged["artist_delta_MAPE_vs_stable"]
        + merged["artist_delta_p95_APE_vs_stable"]
    )
    ordered = merged.sort_values(
        ["validation_score", "row_MAPE", "artist_MAPE", "row_MdAPE", "artist_MdAPE", "candidate"]
    )["candidate"].tolist()

    known = "hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25"
    out = list(dict.fromkeys(([known] if known in set(row["candidate"]) else []) + ordered[:limit]))
    return out[:limit]


def load_h25_predictions(source_candidates: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    keep_candidates = [BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket", *source_candidates]
    usecols = list(dict.fromkeys([*META_COLS, "candidate", "method", "pred_log", "pred_price", "policy_move_log"]))
    pred = pd.read_csv(H25_DIR / "outputs" / "candidate_predictions.csv", usecols=lambda c: c in usecols)
    pred = pred[pred["candidate"].isin(keep_candidates)].copy()
    meta = pred[pred["candidate"].eq(BASELINE)].copy()
    meta = meta[META_COLS].drop_duplicates(["scope", "_track6_row_id"]).reset_index(drop=True)
    wide = pred.pivot_table(
        index=["scope", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="first",
    ).reset_index()
    base = meta.merge(wide, on=["scope", "_track6_row_id"], how="left", suffixes=("", "_pred"))
    return base, pred


def add_policy_masks(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    risk_score = pd.to_numeric(out["hcoef23_risk_score"], errors="coerce").fillna(0.0)
    svc_n = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0)
    qwidth = out["qwidth_band"].astype(str)
    gap = out["gap_band"].astype(str)
    spread = out["pred_spread_band"].astype(str)
    conf = out["service_confidence_tier"].astype(str)

    hard_risk = (
        qwidth.eq("qwidth_extreme")
        | gap.eq("gap_020_plus")
        | spread.eq("spread_extreme")
        | risk_score.ge(2.0)
    )
    out["mask_hard_risk_fallback"] = (~hard_risk).astype(float)
    out["mask_lowrisk_only"] = (risk_score.eq(0.0) & svc_n.ge(10.0)).astype(float)
    out["mask_reliable_lowrisk"] = (
        risk_score.eq(0.0)
        & svc_n.ge(20.0)
        & qwidth.isin(["qwidth_low", "qwidth_mid"])
        & spread.eq("spread_low_mid")
    ).astype(float)
    out["mask_no_extreme_reliable"] = (
        ~hard_risk
        & svc_n.ge(10.0)
        & qwidth.isin(["qwidth_low", "qwidth_mid", "qwidth_high"])
        & ~gap.eq("gap_020_plus")
    ).astype(float)
    out["mask_confidence_medium_plus"] = (
        ~hard_risk
        & svc_n.ge(10.0)
        & (conf.isin(["medium", "high"]) | conf.eq("__MISSING__"))
    ).astype(float)
    out["mask_qwidth_gap_safe"] = (
        risk_score.le(1.0)
        & svc_n.ge(10.0)
        & qwidth.isin(["qwidth_low", "qwidth_mid"])
        & gap.isin(["gap_000_003", "gap_003_005", "gap_005_010"])
    ).astype(float)
    out["mask_p95_defense_core"] = (
        risk_score.le(1.0)
        & svc_n.ge(10.0)
        & qwidth.ne("qwidth_extreme")
        & gap.ne("gap_020_plus")
        & spread.ne("spread_extreme")
    ).astype(float)
    return out


def build_hybrid_configs(source_candidates: list[str]) -> list[HybridConfig]:
    configs = [
        HybridConfig(BASELINE, "source", BASELINE, "all", 1.0, None, "현재 HCOEF 안정 후보"),
        HybridConfig(REFERENCE, "source", REFERENCE, "all", 1.0, None, "서비스 v0.1 70:30 기준 후보"),
        HybridConfig(PPV8, "source", PPV8, "all", 1.0, None, "PP-V8/service component proxy"),
        HybridConfig(SVC, "source", SVC, "all", 1.0, None, "유사 작품 기반 가격 피처"),
        HybridConfig("l10_seq_full_generated_bucket", "source", "l10_seq_full_generated_bucket", "all", 1.0, None, "PP-L10 순차 component"),
    ]
    masks = [
        ("lowrisk_only", "위험 신호가 없고 유사 표본 수가 10개 이상인 구간에만 HCOEF25 이동 적용"),
        ("reliable_lowrisk", "표본 수 20개 이상, 낮은/중간 quantile 폭, 낮은 spread 구간에만 적용"),
        ("no_extreme_reliable", "극단 위험 구간을 제외하고 표본 수 10개 이상인 구간에만 적용"),
        ("confidence_medium_plus", "운영 신뢰도 medium 이상 또는 누락이지만 hard risk가 아닌 구간에만 적용"),
        ("qwidth_gap_safe", "quantile 폭과 후보 간 gap이 모두 안정적인 구간에만 적용"),
        ("p95_defense_core", "p95 방어용 핵심 안전 구간에만 적용"),
    ]
    strengths = [0.25, 0.50, 0.75, 1.00]
    caps = [None, 0.0025, 0.005, 0.0075]
    for source in source_candidates:
        short_source = source.replace("hcoef25_", "h25_").replace("resid_huber_", "rh_")
        for mask, purpose in masks:
            for strength in strengths:
                for cap in caps:
                    cap_tag = "nocap" if cap is None else f"cap{slug_float(cap)}"
                    configs.append(
                        HybridConfig(
                            candidate=f"hcoef26_{short_source}_{mask}_{cap_tag}_s{slug_float(strength)}",
                            method="gated_h25_candidate",
                            source_candidate=source,
                            mask_name=mask,
                            strength=strength,
                            cap=cap,
                            purpose=purpose,
                        )
                    )
    return configs


def predict_config(frame: pd.DataFrame, config: HybridConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    baseline = pd.to_numeric(frame[BASELINE], errors="coerce").to_numpy(dtype=float)
    if config.method == "source":
        pred = pd.to_numeric(frame[config.source_candidate], errors="coerce").fillna(pd.Series(baseline)).to_numpy(dtype=float)
        return pred, pred - baseline, np.ones(len(frame), dtype=float)

    source = pd.to_numeric(frame[config.source_candidate], errors="coerce").to_numpy(dtype=float)
    raw_move = np.where(np.isfinite(source), source - baseline, 0.0)
    if config.cap is not None:
        raw_move = np.clip(raw_move, -float(config.cap), float(config.cap))
    mask = pd.to_numeric(frame[f"mask_{config.mask_name}"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    move = raw_move * float(config.strength) * mask
    return baseline + move, move, mask


def prediction_rows(scope_frame: pd.DataFrame, config: HybridConfig, pred: np.ndarray, move: np.ndarray, mask: np.ndarray) -> pd.DataFrame:
    pred_price = h24.safe_exp(pred)
    actual_price = scope_frame["actual_price"].to_numpy(dtype=float)
    out = scope_frame[[col for col in META_COLS if col != "experiment_id"]].copy()
    out.insert(0, "experiment_id", EXP_ID)
    out["candidate"] = config.candidate
    out["method"] = config.method
    out["source_candidate"] = config.source_candidate
    out["mask_name"] = config.mask_name
    out["mask_applied"] = mask
    out["strength"] = config.strength
    out["cap"] = np.nan if config.cap is None else config.cap
    out["pred_log"] = pred
    out["pred_price"] = pred_price
    out["policy_move_log"] = move
    out["residual_log"] = out["actual_log"].to_numpy(dtype=float) - pred
    out["ape"] = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return out


def evaluate_all(base: pd.DataFrame, configs: list[HybridConfig]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    policy_rows: list[dict[str, Any]] = []
    for scope, scope_frame in base.groupby("scope", sort=False):
        scope_frame = scope_frame.reset_index(drop=True)
        stable_pred, stable_move, _ = predict_config(scope_frame, configs[0])
        reference_pred, _, _ = predict_config(scope_frame, configs[1])
        stable_metric = metric_from_pred(scope_frame, stable_pred)
        reference_metric = metric_from_pred(scope_frame, reference_pred)
        split = scope_frame["split"].iloc[0]
        for config in configs:
            pred, move, mask = predict_config(scope_frame, config)
            m = metric_from_pred(scope_frame, pred)
            method_for_table = config.method
            metric_rows.append(
                h24.metric_row(
                    scope,
                    split,
                    config.candidate,
                    method_for_table,
                    len(scope_frame),
                    m,
                    stable_metric,
                    reference_metric,
                    move,
                )
                | {
                    "source_candidate": config.source_candidate,
                    "mask_name": config.mask_name,
                    "mask_applied_share": float(np.nanmean(mask)),
                    "strength": config.strength,
                    "cap": np.nan if config.cap is None else config.cap,
                }
            )
            pred_frames.append(prediction_rows(scope_frame, config, pred, move, mask))
            policy_rows.append(
                {
                    "scope": scope,
                    "candidate": config.candidate,
                    "source_candidate": config.source_candidate,
                    "mask_name": config.mask_name,
                    "method": config.method,
                    "strength": config.strength,
                    "cap": np.nan if config.cap is None else config.cap,
                    "applied_rows": int(np.nansum(mask)),
                    "rows": int(len(scope_frame)),
                    "applied_share": float(np.nanmean(mask)),
                    "mean_abs_move_log": float(np.nanmean(np.abs(move))),
                    "purpose": config.purpose,
                }
            )
    return pd.DataFrame(metric_rows), pd.concat(pred_frames, ignore_index=True), pd.DataFrame(policy_rows)


def bootstrap_summary(predictions: pd.DataFrame, configs: list[HybridConfig]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(SEED)
    candidates = [config.candidate for config in configs]
    config_method = {config.candidate: config.method for config in configs}
    for scope in ["validation_oof_row", "validation_oof_artist"]:
        focus = predictions[predictions["scope"].eq(scope)].copy()
        if focus.empty:
            continue
        pivot = focus.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="first")
        meta = focus.drop_duplicates("_track6_row_id").set_index("_track6_row_id")
        common = pivot.index[pivot[BASELINE].notna()]
        pivot = pivot.loc[common]
        meta = meta.loc[common]
        actual_price = meta["actual_price"].to_numpy(dtype=float)
        actual_log = meta["actual_log"].to_numpy(dtype=float)
        artists = meta["artist_key"].astype(str).to_numpy()
        unique_artists = np.unique(artists)
        stable_pred = pivot[BASELINE].to_numpy(dtype=float)
        for scheme in ["row_bootstrap", "artist_bootstrap"]:
            deltas: dict[str, list[tuple[float, float, float, float]]] = {candidate: [] for candidate in candidates}
            for _ in range(N_BOOTSTRAP):
                if scheme == "row_bootstrap":
                    idx = rng.integers(0, len(pivot), len(pivot))
                else:
                    sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                    idx = np.concatenate([np.flatnonzero(artists == artist) for artist in sampled_artists])
                    if len(idx) == 0:
                        continue
                stable_m = h24.h20.metric_from_arrays(actual_price[idx], actual_log[idx], stable_pred[idx])
                for candidate in candidates:
                    pred = pivot[candidate].to_numpy(dtype=float)
                    m = h24.h20.metric_from_arrays(actual_price[idx], actual_log[idx], pred[idx])
                    deltas[candidate].append(
                        (
                            m["MdAPE"] - stable_m["MdAPE"],
                            m["MAPE"] - stable_m["MAPE"],
                            m["p95_APE"] - stable_m["p95_APE"],
                            m["RMSE_log"] - stable_m["RMSE_log"],
                        )
                    )
            for candidate in candidates:
                arr = np.asarray(deltas[candidate], dtype=float)
                if arr.size == 0:
                    continue
                rows.append(
                    {
                        "source_scope": scope,
                        "validation_scheme": scheme,
                        "candidate": candidate,
                        "method": config_method[candidate],
                        "n_bootstrap": len(arr),
                        "mean_delta_MdAPE_vs_stable": float(arr[:, 0].mean()),
                        "mean_delta_MAPE_vs_stable": float(arr[:, 1].mean()),
                        "mean_delta_p95_APE_vs_stable": float(arr[:, 2].mean()),
                        "mean_delta_RMSE_log_vs_stable": float(arr[:, 3].mean()),
                        "MdAPE_improve_prob": float((arr[:, 0] < 0).mean()),
                        "MAPE_improve_prob": float((arr[:, 1] < 0).mean()),
                        "p95_improve_prob": float((arr[:, 2] < 0).mean()),
                        "all3_improve_prob": float(((arr[:, 0] < 0) & (arr[:, 1] < 0) & (arr[:, 2] < 0)).mean()),
                        "any2_improve_prob": float(
                            (
                                (arr[:, 0] < 0).astype(int)
                                + (arr[:, 1] < 0).astype(int)
                                + (arr[:, 2] < 0).astype(int)
                                >= 2
                            ).mean()
                        ),
                    }
                )
    return pd.DataFrame(rows)


def selection_table(metrics_df: pd.DataFrame, bootstrap_df: pd.DataFrame) -> pd.DataFrame:
    return h24.selection_table(metrics_df, bootstrap_df)


def feature_coefficients(configs: list[HybridConfig]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for config in configs:
        rows.append(
            {
                "candidate": config.candidate,
                "method": config.method,
                "feature": config.source_candidate,
                "coefficient_or_weight": 1.0 if config.method == "source" else config.strength,
                "cap": np.nan if config.cap is None else config.cap,
                "mask_name": config.mask_name,
                "direction": "source prediction move applied where mask=1",
                "interpretation": config.purpose,
            }
        )
        if config.method != "source":
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": f"mask_{config.mask_name}",
                    "coefficient_or_weight": 1.0,
                    "cap": np.nan,
                    "mask_name": config.mask_name,
                    "direction": "enables_or_blocks_candidate_move",
                    "interpretation": "이 조건을 만족한 행에만 HCOEF25 후보와 hcoef_stable의 차이를 적용한다.",
                }
            )
    return pd.DataFrame(rows)


def mask_coverage_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    focus = predictions.drop_duplicates(["scope", "_track6_row_id"]).copy()
    rows: list[dict[str, Any]] = []
    mask_cols = [c for c in focus.columns if c.startswith("mask_")]
    for scope, group in focus.groupby("scope"):
        for col in mask_cols:
            values = pd.to_numeric(group[col], errors="coerce").fillna(0.0)
            rows.append({"scope": scope, "mask_name": col.replace("mask_", ""), "rows": len(group), "covered_rows": int(values.sum()), "covered_share": float(values.mean())})
    return pd.DataFrame(rows)


def write_report(
    metrics_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    coefficients: pd.DataFrame,
    residuals: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    policy_map: pd.DataFrame,
    mask_coverage: pd.DataFrame,
    source_candidates: list[str],
) -> None:
    test = metrics_df[metrics_df["scope"].eq("fixed_confirmation")].copy()
    row_oof = metrics_df[metrics_df["scope"].eq("validation_oof_row")].copy()
    artist_oof = metrics_df[metrics_df["scope"].eq("validation_oof_artist")].copy()
    stress = metrics_df[metrics_df["scope"].eq("0604_stress")].copy()
    baseline_test = test[test["candidate"].eq(BASELINE)].iloc[0]
    ref_test = test[test["candidate"].eq(REFERENCE)].iloc[0]
    report_candidates = selected_df[
        ~selected_df["decision"].isin(["현재 기준 후보", "보류", "component 대조군", "최소 비교 기준"])
    ].copy()
    if report_candidates.empty:
        best_line = "새 운영 후보 또는 목적별 후보 없음. 현재 기준 후보 `hcoef_stable` 유지."
    else:
        best = report_candidates.iloc[0]
        best_line = (
            f"상위 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test MdAPE/MAPE/p95 "
            f"`{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`)."
        )

    top_cols = [
        "candidate",
        "method",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE_vs_stable",
        "delta_MAPE_vs_stable",
        "delta_p95_APE_vs_stable",
        "mask_applied_share",
    ]
    selected_cols = [
        "candidate",
        "decision",
        "row_oof_MdAPE",
        "row_oof_MAPE",
        "row_oof_p95_APE",
        "artist_oof_MdAPE",
        "artist_oof_MAPE",
        "artist_oof_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "bootstrap_all3_gate",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
    ]

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber low-risk 적용/p95 fallback 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF25 MAPE 개선 후보를 전체에 적용하지 않고, 위험이 낮은 구간에만 제한 적용했을 때 p95를 방어할 수 있는지 검증.",
            "- 현재 기준 후보: `hcoef_stable`.",
            "- 최소 비교 기준: `current_70_30`.",
            "- 선택 원칙: HCOEF25 source 후보는 validation OOF 기준으로 고르고, fixed test/0604 residual은 경계값 선택에 사용하지 않음.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 기준 fixed test: MdAPE `{baseline_test['MdAPE']:.4f}`, MAPE `{baseline_test['MAPE']:.4f}`, p95 `{baseline_test['p95_APE']:.4f}`, RMSE_log `{baseline_test['RMSE_log']:.4f}`.",
            f"- 최소 비교 기준 fixed test: MdAPE `{ref_test['MdAPE']:.4f}`, MAPE `{ref_test['MAPE']:.4f}`, p95 `{ref_test['p95_APE']:.4f}`, RMSE_log `{ref_test['RMSE_log']:.4f}`.",
            "- HCOEF26은 새 기준가를 test에 맞춰 만들지 않고, HCOEF25 후보 이동분을 사전에 정의한 안전 구간에만 적용한 실험임.",
            "",
            "## 2. 사용한 HCOEF25 source 후보",
            "",
            h24.md_table(pd.DataFrame({"source_candidate": source_candidates}), max_rows=30),
            "",
            "## 3. 후보 선택표",
            "",
            h24.md_table(selected_df[selected_cols].round(4), max_rows=40),
            "",
            "## 4. Validation OOF 상위 후보",
            "",
            "### Row OOF",
            "",
            h24.md_table(row_oof.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=25),
            "",
            "### Artist OOF",
            "",
            h24.md_table(artist_oof.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=25),
            "",
            "## 5. Fixed Test 상위 후보",
            "",
            h24.md_table(test.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=30),
            "",
            "## 6. 0604 Stress Test 상위 후보",
            "",
            h24.md_table(stress.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=25),
            "",
            "## 7. 적용 구간 coverage",
            "",
            h24.md_table(mask_coverage.round(4), max_rows=80),
            "",
            "## 8. 계수/정책 해석",
            "",
            "- `source_candidate`: HCOEF25에서 가져온 평균오차 개선 후보.",
            "- `mask_*`: 해당 후보를 실제로 적용할 수 있는 구간. 조건을 만족하지 않으면 `hcoef_stable`로 fallback.",
            "- `strength`: HCOEF25 후보 이동분을 얼마나 반영할지 정한 가중치.",
            "- `cap`: 한 작품에서 허용하는 최대 로그 이동폭. cap이 작을수록 p95 방어에 유리하지만 개선폭은 작아짐.",
            "",
            h24.md_table(coefficients.round(5), max_rows=100),
            "",
            "## 9. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=80),
            "",
            "## 10. Bootstrap 요약",
            "",
            h24.md_table(bootstrap_df.sort_values(["all3_improve_prob", "any2_improve_prob"], ascending=[False, False]).round(4), max_rows=50),
            "",
            "## 11. 적용 정책 상세",
            "",
            h24.md_table(policy_map.round(5), max_rows=100),
            "",
            "## 12. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/policy_map.csv`",
            "- `outputs/mask_coverage_summary.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef26_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef26_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(configs: list[HybridConfig], source_candidates: list[str]) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": BASELINE,
        "reference": REFERENCE,
        "source_experiment": "PP-HCOEF25",
        "source_candidates": source_candidates,
        "selection_rule": "HCOEF25 source candidates chosen from validation OOF; HCOEF26 fixed test and 0604 are confirmation only",
        "design": [
            "hard-risk fallback to hcoef_stable",
            "apply HCOEF25 movement only in predefined low-risk/reliable masks",
            "strength grid: 0.25, 0.50, 0.75, 1.00",
            "movement cap grid: none, 0.0025, 0.005, 0.0075",
        ],
        "candidate_count": len(configs),
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    source_candidates = select_h25_source_candidates()
    base, _ = load_h25_predictions(source_candidates)
    base = add_policy_masks(base)
    configs = build_hybrid_configs(source_candidates)
    metrics_df, predictions, policy_map = evaluate_all(base, configs)
    bootstrap_df = bootstrap_summary(predictions, configs)
    selected_df = selection_table(metrics_df, bootstrap_df)
    selected_names = selected_df.head(20)["candidate"].astype(str).tolist()
    coefficients = feature_coefficients([config for config in configs if config.candidate in set(selected_names)])
    residuals = h24.residual_analysis(predictions, selected_names)
    mask_coverage = mask_coverage_summary(base)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    policy_map.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)
    mask_coverage.to_csv(EXP_DIR / "outputs" / "mask_coverage_summary.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selected_df.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    write_config(configs, source_candidates)
    write_report(metrics_df, selected_df, coefficients, residuals, bootstrap_df, policy_map, mask_coverage, source_candidates)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
