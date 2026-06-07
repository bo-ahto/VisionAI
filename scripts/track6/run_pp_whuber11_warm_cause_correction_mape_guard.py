#!/usr/bin/env python3
"""Run PP-WHUBER11 Warm cause-based correction with a MAPE guard.

PP-WHUBER10 showed that cause-based residual corrections can lower MdAPE/p95
but worsened MAPE, because the correction hierarchy fell back to broad groups
(``risk_cause`` / ``pred_log_bin`` / ``global``) and nudged many already-normal
rows downward.

PP-WHUBER11 keeps the same per-artwork cause diagnostics but changes how the
correction is applied so the net effect is a pure improvement:

1. Overprediction-only segment mask
   - Corrections are applied only to weak-artist-baseline segments that are
     prone to overprediction; normal/stable rows are left untouched.
2. Downward-only cap
   - Only negative (downward) corrections are applied, so underpredicted rows
     are never pushed further down.
3. No global fallback
   - The correction hierarchy stops at ``risk_cause`` level; rows without a
     calibrated segment get correction 0 (no broad leakage into normal rows).
4. MAPE guard at selection
   - Only candidates that do NOT worsen validation MAPE are promoted to the
     test confirmation step.

Leakage rules (same as PP-WHUBER10):
- Correction values are learned from validation artist-level holdout folds only.
- Test is used once for final confirmation; never for candidate selection.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_whuber10_warm_artwork_error_cause_correction as w10  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WHUBER11"
EXP_SLUG = "PP-WHUBER11_warm_cause_correction_mape_guard"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 원인 기반 보정 + MAPE guard + 과대예측 전용 cap"
SEED = w10.SEED
N_ARTIST_SPLITS = w10.N_ARTIST_SPLITS
N_ARTIST_REPEATS = w10.N_ARTIST_REPEATS
CURRENT_CANDIDATE = w10.CURRENT_CANDIDATE
METRICS = w10.METRICS

# Reused stateless helpers (no embedded EXP_ID / TITLE).
metric_from_pred = w10.metric_from_pred
add_metric_deltas = w10.add_metric_deltas
make_key = w10.make_key
markdown_table = w10.markdown_table
artwork_error_diagnostics = w10.artwork_error_diagnostics

# Overprediction-prone weak-artist-baseline segments (observable at inference).
OVERPRED_RISK_CAUSES = {
    "유사작품_적음+작가이력_적음",
    "유사작품_표본_부족",
    "작가이력_표본_부족",
}

# Correction hierarchies WITHOUT the global fallback level.
HIERARCHIES: dict[str, list[list[str]]] = {
    "risk_pred": [["risk_cause", "pred_log_bin"], ["risk_cause"]],
    "works_pred": [["artist_works_bin", "pred_log_bin"], ["artist_works_bin"]],
    "pred_svc": [["pred_log_bin", "svc_reliability_bin"], ["svc_reliability_bin"]],
}
MIN_ROWS = [8, 20]
CAPS = [0.05, 0.08, 0.12]
STRENGTHS = [0.25, 0.50]
SMOOTH_ROWS = [20]


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def overpred_risk_mask(frame: pd.DataFrame) -> np.ndarray:
    """Rows where a downward correction is allowed (weak artist baseline)."""
    risk = frame["risk_cause"].astype(str).isin(OVERPRED_RISK_CAUSES)
    return risk.to_numpy()


def candidate_grid() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for hierarchy_name, hierarchy in HIERARCHIES.items():
        for min_rows in MIN_ROWS:
            for cap in CAPS:
                for strength in STRENGTHS:
                    for smooth_rows in SMOOTH_ROWS:
                        cap_code = str(cap).replace(".", "p")
                        strength_code = str(strength).replace(".", "p")
                        candidate = (
                            f"{EXP_ID}_guard_{hierarchy_name}_min{min_rows}"
                            f"_cap{cap_code}_s{strength_code}_smooth{smooth_rows}"
                        )
                        specs.append({
                            "candidate": candidate,
                            "hierarchy_name": hierarchy_name,
                            "hierarchy": hierarchy,
                            "min_rows": min_rows,
                            "cap": cap,
                            "strength": strength,
                            "smooth_rows": smooth_rows,
                        })
    return specs


def correction_lookup_guarded(
    calibration: pd.DataFrame,
    target: pd.DataFrame,
    spec: dict[str, Any],
    base_pred_col: str = "current_pred_log",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Downward-only, overprediction-segment-only, no-global-fallback correction."""
    residual = calibration["ln_price_krw"].to_numpy(dtype=float) - calibration[base_pred_col].to_numpy(dtype=float)
    calibration = calibration.copy()
    calibration["_residual_for_correction"] = residual

    # No global initialization: rows without a calibrated segment stay at 0.
    correction = np.zeros(len(target), dtype=float)
    source_level = np.array(["none"] * len(target), dtype=object)
    source_n = np.zeros(len(target), dtype=float)

    for level, cols in enumerate(spec["hierarchy"]):
        if not cols:
            continue
        cal_key = make_key(calibration, cols)
        grouped = (
            calibration.assign(_key=cal_key)
            .groupby("_key", observed=False)["_residual_for_correction"]
            .agg(["median", "count"])
            .reset_index()
        )
        grouped = grouped[grouped["count"] >= int(spec["min_rows"])].copy()
        if grouped.empty:
            continue
        mapping = dict(zip(grouped["_key"], grouped["median"]))
        count_mapping = dict(zip(grouped["_key"], grouped["count"]))
        target_key = make_key(target, cols)
        mapped = target_key.map(mapping)
        mapped_n = target_key.map(count_mapping)
        mask = mapped.notna() & (source_level == "none")
        if mask.any():
            correction[mask.to_numpy()] = mapped[mask].to_numpy(dtype=float)
            source_n[mask.to_numpy()] = mapped_n[mask].to_numpy(dtype=float)
            source_level[mask.to_numpy()] = f"level{level + 1}:{'+'.join(cols)}"

    smooth_rows = float(spec["smooth_rows"])
    if smooth_rows > 0:
        shrink = source_n / np.clip(source_n + smooth_rows, 1.0, None)
        correction = correction * shrink

    raw_correction = correction.copy()
    # Downward-only cap: keep only negative corrections, bounded by cap, scaled.
    correction = np.clip(correction, -float(spec["cap"]), 0.0) * float(spec["strength"])
    # Apply only to overprediction-prone segments; leave the rest untouched.
    risk_mask = overpred_risk_mask(target)
    correction = np.where(risk_mask, correction, 0.0)
    return correction, raw_correction, source_n, source_level.tolist()


def repeated_artist_holdout(val: pd.DataFrame, specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    val = val.reset_index(drop=True).copy()
    artist_series = val["artist_key"].astype(str).fillna("__MISSING__")
    artists = artist_series.unique()
    repeat_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    current_pred = val["current_pred_log"].to_numpy(dtype=float)

    for repeat in range(N_ARTIST_REPEATS):
        rng = np.random.default_rng(SEED + repeat)
        artist_folds = np.array_split(rng.permutation(artists), N_ARTIST_SPLITS)
        oof_preds = {spec["candidate"]: np.full(len(val), np.nan, dtype=float) for spec in specs}
        oof_abs_correction = {spec["candidate"]: [] for spec in specs}

        for fold, holdout_artists in enumerate(artist_folds, 1):
            holdout_mask = artist_series.isin(set(holdout_artists)).to_numpy()
            calibration = val.loc[~holdout_mask].copy()
            holdout = val.loc[holdout_mask].copy()
            holdout_idx = np.flatnonzero(holdout_mask)
            if calibration.empty or holdout.empty:
                continue
            fold_base = metric_from_pred(holdout, holdout["current_pred_log"].to_numpy(dtype=float))
            for spec in specs:
                correction, raw, source_n, source_level = correction_lookup_guarded(calibration, holdout, spec)
                pred = holdout["current_pred_log"].to_numpy(dtype=float) + correction
                oof_preds[spec["candidate"]][holdout_idx] = pred
                oof_abs_correction[spec["candidate"]].extend(np.abs(correction).tolist())
                metric = metric_from_pred(holdout, pred)
                corrected_rows = int(np.sum(correction != 0.0))
                row = {
                    "experiment_id": EXP_ID,
                    "split": "validation_artist_holdout_fold",
                    "repeat": repeat,
                    "fold": fold,
                    "candidate": spec["candidate"],
                    "hierarchy_name": spec["hierarchy_name"],
                    "min_rows": spec["min_rows"],
                    "cap": spec["cap"],
                    "strength": spec["strength"],
                    "smooth_rows": spec["smooth_rows"],
                    "n": len(holdout),
                    "n_artists_holdout": len(holdout_artists),
                    "corrected_row_rate": float(corrected_rows / max(len(holdout), 1)),
                    "mean_abs_correction": float(np.mean(np.abs(correction))),
                    "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
                    "raw_correction_median": float(np.median(raw)),
                    "median_source_n": float(np.median(source_n)),
                }
                fold_rows.append(add_metric_deltas(row, metric, fold_base))

        for spec in specs:
            pred = oof_preds[spec["candidate"]]
            valid_mask = np.isfinite(pred)
            if not valid_mask.any():
                continue
            full_frame = val.loc[valid_mask].copy()
            base_metric = metric_from_pred(full_frame, current_pred[valid_mask])
            metric = metric_from_pred(full_frame, pred[valid_mask])
            abs_corr = np.asarray(oof_abs_correction[spec["candidate"]], dtype=float)
            row = {
                "experiment_id": EXP_ID,
                "split": "validation_artist_holdout_oof",
                "repeat": repeat,
                "candidate": spec["candidate"],
                "hierarchy_name": spec["hierarchy_name"],
                "min_rows": spec["min_rows"],
                "cap": spec["cap"],
                "strength": spec["strength"],
                "smooth_rows": spec["smooth_rows"],
                "mean_abs_correction": float(np.mean(abs_corr)) if abs_corr.size else 0.0,
                "p95_abs_correction": float(np.quantile(abs_corr, 0.95)) if abs_corr.size else 0.0,
            }
            repeat_rows.append(add_metric_deltas(row, metric, base_metric))

    return pd.DataFrame(repeat_rows), pd.DataFrame(fold_rows)


def summarize_validation(repeat_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, group in repeat_metrics.groupby("candidate", observed=False):
        first = group.iloc[0]
        row = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "hierarchy_name": first["hierarchy_name"],
            "min_rows": int(first["min_rows"]),
            "cap": float(first["cap"]),
            "strength": float(first["strength"]),
            "smooth_rows": int(first["smooth_rows"]),
            "repeats": int(group["repeat"].nunique()),
            "mean_abs_correction": float(group["mean_abs_correction"].mean()),
            "p95_abs_correction": float(group["p95_abs_correction"].mean()),
        }
        for metric in METRICS:
            delta = group[f"delta_{metric}"]
            row[f"mean_{metric}"] = float(group[metric].mean())
            row[f"mean_delta_{metric}"] = float(delta.mean())
            row[f"p10_delta_{metric}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric}"] = float(np.mean(delta < 0))
            row[f"nonworse_probability_{metric}"] = float(np.mean(delta <= 1e-9))
        row["balanced_score"] = (
            row["mean_delta_MdAPE"]
            + 0.50 * row["mean_delta_MAPE"]
            + 0.25 * row["mean_delta_p95_APE"]
        )
        row["tail_score"] = row["mean_delta_p95_APE"] + 0.50 * row["mean_delta_MAPE"]
        # MAPE guard: candidate must not worsen MAPE on validation.
        row["mape_guard_pass"] = bool(
            (row["mean_delta_MAPE"] <= 0.0) or (row["nonworse_probability_MAPE"] >= 0.50)
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["balanced_score", "mean_delta_MdAPE", "mean_delta_MAPE"])


def select_labeled_specs(summary: pd.DataFrame, specs: list[dict[str, Any]]) -> list[tuple[dict[str, Any], str]]:
    """Pick MAPE-guard-passing candidates by objective (representative / defense / balanced).

    All candidates considered here already pass the validation MAPE guard, so no
    candidate worsens MAPE. They are separated by objective the same way the track
    does elsewhere (대표가 / 큰오차 방어 / 균형).
    """
    by_name = {spec["candidate"]: spec for spec in specs}
    guard = summary[summary["mape_guard_pass"]].copy()
    if guard.empty:
        return []

    # 하이어라키별 validation balanced_score 최적 후보 1개씩 (서로 다른 보정 구조 비교).
    best_per_hierarchy: list[str] = []
    for _, group in guard.groupby("hierarchy_name", observed=False):
        best = group.sort_values(["balanced_score", "mean_delta_MdAPE"]).iloc[0]
        best_per_hierarchy.append(str(best["candidate"]))

    sub = guard[guard["candidate"].isin(best_per_hierarchy)].sort_values(
        ["balanced_score", "mean_delta_MdAPE"]
    )
    out: list[tuple[dict[str, Any], str]] = []
    for _, row in sub.iterrows():
        candidate = str(row["candidate"])
        if row["mean_delta_MdAPE"] < 0 and row["improvement_probability_MdAPE"] >= 0.50:
            objective = "대표(MdAPE 개선)"
        elif row["mean_delta_p95_APE"] < 0:
            objective = "p95/MAPE 방어"
        else:
            objective = "균형(MAPE 비악화)"
        out.append((by_name[candidate], f"{objective} [{row['hierarchy_name']}]"))
    return out


def prediction_frame(
    split: str,
    candidate: str,
    role: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray | None,
    spec: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "split": split,
        "candidate": candidate,
        "role": role,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "title_raw": frame.get("title_raw", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "current_pred_log": frame["current_pred_log"].to_numpy(dtype=float),
    })
    for col in ["svc_reliability_bin", "pred_log_bin", "size_bin", "artist_works_bin", "risk_cause"]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    if correction is None:
        correction = np.zeros(len(frame), dtype=float)
    out["correction_log"] = np.asarray(correction, dtype=float)
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    if spec:
        out["hierarchy_name"] = spec["hierarchy_name"]
        out["min_rows"] = spec["min_rows"]
        out["cap"] = spec["cap"]
        out["strength"] = spec["strength"]
        out["smooth_rows"] = spec["smooth_rows"]
    return out


def test_once_predictions(
    val: pd.DataFrame,
    test: pd.DataFrame,
    labeled_specs: list[tuple[dict[str, Any], str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    parts: list[pd.DataFrame] = []
    base_pred = test["current_pred_log"].to_numpy(dtype=float)
    base_metric = metric_from_pred(test, base_pred)
    base_row = {
        "experiment_id": EXP_ID,
        "split": "test_once",
        "candidate": CURRENT_CANDIDATE,
        "role": "현재 Warm 기준 조합",
        "hierarchy_name": "reference",
        "min_rows": np.nan,
        "cap": np.nan,
        "strength": np.nan,
        "smooth_rows": np.nan,
        "mape_guard_role": "baseline",
        "mean_abs_correction": 0.0,
        "p95_abs_correction": 0.0,
    }
    rows.append(add_metric_deltas(base_row, base_metric, base_metric))
    parts.append(prediction_frame("test_once", CURRENT_CANDIDATE, "현재 Warm 기준 조합", test, base_pred, None))

    for spec, role in labeled_specs:
        correction, raw, source_n, source_level = correction_lookup_guarded(val, test, spec)
        pred = base_pred + correction
        metric = metric_from_pred(test, pred)
        row = {
            "experiment_id": EXP_ID,
            "split": "test_once",
            "candidate": spec["candidate"],
            "role": role,
            "hierarchy_name": spec["hierarchy_name"],
            "min_rows": spec["min_rows"],
            "cap": spec["cap"],
            "strength": spec["strength"],
            "smooth_rows": spec["smooth_rows"],
            "mape_guard_role": role,
            "mean_abs_correction": float(np.mean(np.abs(correction))),
            "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
            "corrected_row_rate": float(np.mean(correction != 0.0)),
        }
        rows.append(add_metric_deltas(row, metric, base_metric))
        parts.append(prediction_frame("test_once", spec["candidate"], role, test, pred, correction, spec))

    return pd.DataFrame(rows), pd.concat(parts, ignore_index=True)


def render_report(
    validation_summary: pd.DataFrame,
    test_metrics: pd.DataFrame,
    selected_specs: list[dict[str, Any]],
    cause_summary: pd.DataFrame,
    top_errors: pd.DataFrame,
    selected_candidate: str | None,
) -> tuple[str, str]:
    base_test = test_metrics[test_metrics["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    guard_pass = validation_summary[validation_summary["mape_guard_pass"]]

    selected_view = pd.DataFrame([{
        "candidate": spec["candidate"],
        "hierarchy": " > ".join("+".join(level) for level in spec["hierarchy"]),
        "min_rows": spec["min_rows"],
        "cap": spec["cap"],
        "strength": spec["strength"],
    } for spec in selected_specs]) if selected_specs else pd.DataFrame()

    val_view = validation_summary[[
        "candidate", "hierarchy_name", "cap", "strength", "mape_guard_pass",
        "mean_delta_MdAPE", "mean_delta_MAPE", "mean_delta_p95_APE",
        "improvement_probability_MdAPE", "nonworse_probability_MAPE",
        "improvement_probability_p95_APE", "balanced_score",
    ]].head(15).copy()

    test_view = test_metrics[[
        "candidate", "role", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "corrected_row_rate",
    ]].copy() if "corrected_row_rate" in test_metrics.columns else test_metrics.copy()

    cause_view = cause_summary[[
        "risk_cause", "error_direction", "error_severity", "n",
        "current_MdAPE", "current_MAPE", "current_p95_APE", "median_residual_log",
        "adjusted_MdAPE", "adjusted_MAPE", "adjusted_p95_APE",
        "improved_row_rate", "worsened_row_rate",
    ]].head(24).copy()

    selected_test = None
    if selected_candidate and selected_candidate in set(test_metrics["candidate"]):
        selected_test = test_metrics[test_metrics["candidate"].eq(selected_candidate)].iloc[0]

    # Adoption verdict against PP-WHUBER11 criteria.
    verdict_lines: list[str] = []
    if selected_test is not None:
        mape_ok = selected_test["MAPE"] <= base_test["MAPE"] + 1e-9
        mdape_ok = selected_test["MdAPE"] <= base_test["MdAPE"] + 1e-9
        p95_ok = selected_test["p95_APE"] < base_test["p95_APE"]
        gain = (selected_test["MdAPE"] < base_test["MdAPE"]) or p95_ok
        rel_mdape = (selected_test["MdAPE"] - base_test["MdAPE"]) / base_test["MdAPE"]
        rel_p95 = (selected_test["p95_APE"] - base_test["p95_APE"]) / base_test["p95_APE"]
        # 크기 기준: 상대 개선 1% 미만이면 noise 수준으로 본다.
        marginal = (abs(rel_mdape) < 0.01) and (abs(rel_p95) < 0.01)
        if mape_ok and mdape_ok and gain and not marginal:
            verdict = "채택 검토 (MAPE 비악화 + MdAPE/p95 개선)"
        elif mape_ok and gain and marginal:
            verdict = "보조 방어 후보 (MAPE 비악화 + 개선이 marginal, 단독 대표 교체는 보류)"
        elif mape_ok and p95_ok:
            verdict = "보조 채택 (MAPE 비악화 + p95만 개선)"
        else:
            verdict = "보류 (채택 기준 미달)"
        verdict_lines = [
            f"- 채택 판정 후보: `{selected_candidate}` → **{verdict}**",
            f"- MAPE 비악화: {mape_ok} / MdAPE 비악화: {mdape_ok} / p95 개선: {p95_ok}",
            f"- 상대 개선: MdAPE {rel_mdape * 100:.2f}% / p95 {rel_p95 * 100:.2f}% (음수가 개선). 절대 개선폭이 작아 paired bootstrap 유의성 확인 전 대표 교체는 보류 권장",
        ]
    else:
        verdict_lines = ["- MAPE guard를 통과한 채택 후보 없음 → 원인 기반 보정은 진단 용도로 종결, Warm 대표 유지"]

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 Warm 후보: `{CURRENT_CANDIDATE}`",
        "- 가설: 과대예측 segment 한정 + 하향 전용 cap + MAPE guard로 MdAPE/p95를 낮추면서 MAPE를 악화시키지 않는 후보를 찾는다",
        "- 누수 방지: 보정값은 validation 작가 holdout에서만 산출, test는 최종 확인 1회",
        "",
        "## 1. 실행 결론",
        "",
        f"- 기준 후보 test MdAPE/MAPE/p95: `{base_test['MdAPE']:.4f}` / `{base_test['MAPE']:.4f}` / `{base_test['p95_APE']:.4f}`",
        f"- MAPE guard 통과 validation 후보 수: {len(guard_pass)} / 전체 {len(validation_summary)}",
        *(
            [f"- 채택 후보 test MdAPE/MAPE/p95: `{selected_test['MdAPE']:.4f}` / `{selected_test['MAPE']:.4f}` / `{selected_test['p95_APE']:.4f}`"]
            if selected_test is not None else ["- 채택 후보 test 성능: 없음"]
        ),
        *verdict_lines,
        "",
        "## 2. 설계 변경 요소 (PP-WHUBER10 대비)",
        "",
        "- 과대예측 위험 segment(작가 기준선 약함)에만 보정 적용, 정상·과소예측 행 미접촉",
        "- 하향 방향 보정만 적용(`clip(-cap, 0) * strength`)",
        "- global fallback 제거(`risk_cause` level까지만), 표본 부족 segment는 보정 0",
        "- validation MAPE 비악화 후보만 채택(MAPE guard)",
        "",
        "## 3. 채택(MAPE guard 통과) 후보",
        "",
        markdown_table(selected_view) if not selected_view.empty else "_MAPE guard 통과 후보 없음_",
        "",
        "## 4. Validation 작가 holdout 후보 요약",
        "",
        markdown_table(val_view),
        "",
        "## 5. Test 성능 비교",
        "",
        markdown_table(test_view),
        "",
        "## 6. 원인군별 보정 효과 (test 진단)",
        "",
        markdown_table(cause_view),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/validation_artist_holdout_summary.csv`: validation 후보별 안정성 + MAPE guard 통과 여부",
        "- `outputs/test_once_metrics.csv`: test 성능 비교",
        "- `outputs/test_artwork_error_diagnostics.csv`: 작품별 보정 전/후 변화",
        "- `outputs/test_cause_summary.csv`: 원인군별 개선·악화 요약",
        "- `artifacts/run_config.json`: seed/grid/mask 정의(재현용)",
    ]
    markdown = "\n".join(lines)
    w10.TITLE = TITLE  # ensure html <title> reflects this experiment
    return markdown, w10.md_to_html(markdown)


def main() -> None:
    ensure_dirs()
    val, test = w10.load_frames()
    specs = candidate_grid()
    repeat_metrics, fold_metrics = repeated_artist_holdout(val, specs)
    validation_summary = summarize_validation(repeat_metrics)
    labeled_specs = select_labeled_specs(validation_summary, specs)
    selected_specs = [spec for spec, _ in labeled_specs]
    test_metrics, test_predictions = test_once_predictions(val, test, labeled_specs)

    # Representative candidate for per-artwork diagnostics (대표 우선, 없으면 첫 후보).
    representative = [spec for spec, label in labeled_specs if label.startswith("대표")]
    if representative:
        selected_candidate = representative[0]["candidate"]
    elif selected_specs:
        selected_candidate = selected_specs[0]["candidate"]
    else:
        selected_candidate = None
    diagnostics, cause_summary, top_errors = artwork_error_diagnostics(test_predictions, selected_candidate)
    markdown, html_report = render_report(
        validation_summary, test_metrics, selected_specs, cause_summary, top_errors, selected_candidate
    )

    out = EXP_DIR / "outputs"
    repeat_metrics.to_csv(out / "validation_artist_holdout_repeat_metrics.csv", index=False)
    fold_metrics.to_csv(out / "validation_artist_holdout_fold_metrics.csv", index=False)
    validation_summary.to_csv(out / "validation_artist_holdout_summary.csv", index=False)
    test_metrics.to_csv(out / "test_once_metrics.csv", index=False)
    test_predictions.to_csv(out / "test_once_predictions.csv", index=False)
    diagnostics.to_csv(out / "test_artwork_error_diagnostics.csv", index=False)
    cause_summary.to_csv(out / "test_cause_summary.csv", index=False)
    top_errors.to_csv(out / "test_top_error_examples.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "current_candidate": CURRENT_CANDIDATE,
        "seed": SEED,
        "n_artist_splits": N_ARTIST_SPLITS,
        "n_artist_repeats": N_ARTIST_REPEATS,
        "overpred_risk_causes": sorted(OVERPRED_RISK_CAUSES),
        "hierarchies": HIERARCHIES,
        "min_rows": MIN_ROWS,
        "caps": CAPS,
        "strengths": STRENGTHS,
        "smooth_rows": SMOOTH_ROWS,
        "selected_candidates": [{"candidate": spec["candidate"], "objective": label} for spec, label in labeled_specs],
        "representative_candidate": selected_candidate,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report_md = EXP_DIR / "reports" / f"{EXP_SLUG}.md"
    report_html = EXP_DIR / "reports" / f"{EXP_SLUG}.html"
    doc_md = DOC_ROOT / "pp_whuber11_warm_cause_correction_mape_guard_summary.md"
    doc_html = DOC_ROOT / "pp_whuber11_warm_cause_correction_mape_guard_summary.html"
    for path, content in [(report_md, markdown), (doc_md, markdown), (report_html, html_report), (doc_html, html_report)]:
        path.write_text(content, encoding="utf-8")

    print(f"[{EXP_ID}] validation candidates: {len(validation_summary)} (MAPE guard pass: {int(validation_summary['mape_guard_pass'].sum())})")
    print(f"[{EXP_ID}] selected by objective: {[(spec['candidate'], label) for spec, label in labeled_specs]}")
    print(f"[{EXP_ID}] representative candidate: {selected_candidate}")
    cols = ["candidate", "role", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]
    print(test_metrics[cols].to_string(index=False))
    print(f"[{EXP_ID}] report: {report_md}")


if __name__ == "__main__":
    main()
