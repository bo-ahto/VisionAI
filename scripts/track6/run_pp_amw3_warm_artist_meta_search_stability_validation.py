#!/usr/bin/env python3
"""Run PP-AMW3 stability validation for AMW2 Warm residual stack candidates.

This script validates PP-AMW2 candidates without changing operational code.
It reconstructs selected AMW2 prediction rows from the frozen PP-V8 baseline
and the validation-fitted AMW1/H29 correction outputs, then runs paired row and
artist bootstrap checks on validation/test splits.

This is not a full repeated retraining experiment. It is a frozen-prediction
stability check for the post-model correction policy.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-AMW3"
EXP_SLUG = "PP-AMW3_warm_artist_meta_search_stability_validation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

AMW1_PRED_PATH = REPO / "experiments/track6/PP-AMW1_warm_artist_meta_residual_calibration/outputs/predictions.csv"
H29_PRED_PATH = REPO / "experiments/track6/PP-H29_warm_search_feature_calibration/outputs/candidate_predictions.csv"
AMW2_OUT = REPO / "experiments/track6/PP-AMW2_warm_artist_meta_search_residual_stack/outputs"
SPLIT_PATHS = {
    "validation": REPO / "data/track6_split/track6_val_warm.csv",
    "test": REPO / "data/track6_split/track6_test_warm.csv",
}

BASELINE = "baseline_ppv8_compact_blend_mape_guarded"
SEED = 20260606
BOOTSTRAP_ITERATIONS = 1000
ARTIST_SUBSAMPLE_RATE = 0.70


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def metrics_from_arrays(actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual = np.exp(actual_log)
    pred = np.exp(pred_log)
    ape = np.abs(pred - actual) / np.maximum(actual, 1e-9)
    ratio = pred / np.maximum(actual, 1e-9)
    return {
        "n": int(len(actual_log)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(pred_log - actual_log)))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "over_3x_n": int(np.sum(ratio > 3.0)),
        "under_1_3x_n": int(np.sum(ratio < (1.0 / 3.0))),
    }


def load_split_meta() -> pd.DataFrame:
    parts = []
    for split, path in SPLIT_PATHS.items():
        frame = pd.read_csv(path, low_memory=False)
        cols = ["_track6_row_id", "artist_key", "artist_name_ko", "title_raw"]
        parts.append(frame[cols].assign(split=split))
    return pd.concat(parts, ignore_index=True).drop_duplicates(["split", "_track6_row_id"])


def load_base() -> pd.DataFrame:
    pred = pd.read_csv(AMW1_PRED_PATH, low_memory=False)
    base = pred[pred["candidate"].eq(BASELINE)].copy()
    if base.empty:
        raise RuntimeError(f"Missing baseline candidate: {BASELINE}")
    keep = ["split", "_track6_row_id", "actual_log", "pred_log", "actual_price", "pred_price"]
    base = base[keep].drop_duplicates(["split", "_track6_row_id"], keep="first")
    base = base[base["split"].isin(SPLIT_PATHS)].copy()
    return base.merge(load_split_meta(), on=["split", "_track6_row_id"], how="left")


def select_candidates() -> pd.DataFrame:
    selected_metrics = pd.read_csv(AMW2_OUT / "selected_candidate_metrics.csv")
    conservative_metrics = pd.read_csv(AMW2_OUT / "conservative_balanced_candidate_metrics.csv")
    test_all_metric = pd.read_csv(AMW2_OUT / "test_all_metric_improved_candidates.csv")
    test_top = pd.read_csv(AMW2_OUT / "test_top_candidates.csv")

    rows: list[dict[str, Any]] = [{
        "candidate": BASELINE,
        "role": "baseline",
        "selection_basis": "PP-V8 compact blend 기준 후보",
    }]

    def pick(metrics: pd.DataFrame, role: str, selection_basis: str, sort_cols: list[str]) -> None:
        view = metrics[metrics["split"].eq("test")].copy() if "split" in metrics.columns else metrics.copy()
        view = view[~view["candidate"].eq(BASELINE)].sort_values(sort_cols)
        if not view.empty:
            rows.append({
                "candidate": str(view.iloc[0]["candidate"]),
                "role": role,
                "selection_basis": selection_basis,
            })

    pick(
        selected_metrics,
        "validation_mape_selected",
        "validation에서 MAPE 우선으로 선택한 후보",
        ["MAPE", "MdAPE", "p95_APE"],
    )
    pick(
        conservative_metrics,
        "conservative_balanced",
        "validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보",
        ["MAPE", "MdAPE", "p95_APE"],
    )
    pick(
        test_all_metric,
        "test_all_metric_exploratory",
        "test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보",
        ["MAPE", "MdAPE", "p95_APE"],
    )
    pick(
        test_top,
        "test_mape_exploratory",
        "test MAPE 기준 상위 탐색 후보",
        ["MAPE", "MdAPE", "p95_APE"],
    )
    return pd.DataFrame(rows).drop_duplicates("candidate", keep="first")


def correction_series(path: Path, candidate: str, base_index: pd.MultiIndex) -> pd.Series:
    pred = pd.read_csv(path, low_memory=False)
    part = pred[pred["candidate"].eq(candidate)].copy()
    if part.empty:
        raise RuntimeError(f"Missing correction candidate: {candidate}")
    part["correction_log"] = pd.to_numeric(part["corrected_pred_log"], errors="coerce") - pd.to_numeric(part["pred_log"], errors="coerce")
    series = part.set_index(["split", "_track6_row_id"])["correction_log"]
    return series.reindex(base_index).fillna(0.0).astype(float)


def reconstruct_predictions(base: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    combo_map = pd.read_csv(AMW2_OUT / "candidate_map.csv")
    combo_lookup = combo_map.set_index("candidate")
    base_index = pd.MultiIndex.from_frame(base[["split", "_track6_row_id"]])
    base_pred = base["pred_log"].to_numpy(dtype=float)
    parts = []

    correction_cache: dict[tuple[str, str], pd.Series] = {}

    def cached(kind: str, candidate: str) -> pd.Series:
        key = (kind, candidate)
        if key in correction_cache:
            return correction_cache[key]
        path = AMW1_PRED_PATH if kind == "amw" else H29_PRED_PATH
        correction_cache[key] = correction_series(path, candidate, base_index)
        return correction_cache[key]

    for row in candidates.itertuples(index=False):
        candidate = row.candidate
        frame = base.copy()
        frame["candidate"] = candidate
        frame["role"] = row.role
        frame["selection_basis"] = row.selection_basis
        if candidate == BASELINE:
            total_corr = np.zeros(len(base))
            pred_log = base_pred.copy()
            frame["artist_meta_candidate"] = ""
            frame["search_candidate"] = ""
            frame["artist_meta_weight"] = 0.0
            frame["search_weight"] = 0.0
            frame["total_correction_cap"] = 0.0
        else:
            combo = combo_lookup.loc[candidate]
            amw_candidate = str(combo["artist_meta_candidate"])
            h29_candidate = str(combo["search_candidate"])
            amw_corr = cached("amw", amw_candidate).to_numpy(dtype=float) * float(combo["artist_meta_weight"])
            h29_corr = cached("h29", h29_candidate).to_numpy(dtype=float) * float(combo["search_weight"])
            cap = float(combo["total_correction_cap"])
            total_corr = np.clip(amw_corr + h29_corr, -cap, cap)
            pred_log = base_pred + total_corr
            frame["artist_meta_candidate"] = amw_candidate
            frame["search_candidate"] = h29_candidate
            frame["artist_meta_weight"] = float(combo["artist_meta_weight"])
            frame["search_weight"] = float(combo["search_weight"])
            frame["total_correction_cap"] = cap
        frame["total_correction"] = total_corr
        frame["candidate_pred_log"] = pred_log
        frame["candidate_pred_price"] = np.exp(pred_log)
        frame["candidate_ape"] = np.abs(frame["candidate_pred_price"] - np.exp(frame["actual_log"])) / np.maximum(np.exp(frame["actual_log"]), 1e-9)
        parts.append(frame)
    return pd.concat(parts, ignore_index=True)


def point_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, split), group in predictions.groupby(["candidate", "split"], dropna=False):
        first = group.iloc[0]
        row = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "role": first["role"],
            "selection_basis": first["selection_basis"],
            "split": split,
            **metrics_from_arrays(group["actual_log"].to_numpy(dtype=float), group["candidate_pred_log"].to_numpy(dtype=float)),
        }
        rows.append(row)
    out = pd.DataFrame(rows)
    baseline = out[out["candidate"].eq(BASELINE)].set_index("split")
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"delta_vs_baseline_{metric}"] = out.apply(
            lambda row: row[metric] - baseline.loc[row["split"], metric],
            axis=1,
        )
    return out.sort_values(["split", "role", "candidate"])


def pivot_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["split", "_track6_row_id", "actual_log", "actual_price", "artist_key", "artist_name_ko", "title_raw"]
    base = predictions[base_cols].drop_duplicates(["split", "_track6_row_id"])
    wide = predictions.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="candidate_pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    return base.merge(wide, on=["split", "_track6_row_id"], how="inner")


def sample_indices_by_artist(df: pd.DataFrame, rng: np.random.Generator, mode: str) -> np.ndarray:
    row_indices = np.arange(len(df))
    if mode == "row_bootstrap":
        return rng.choice(row_indices, size=len(row_indices), replace=True)
    artists = df["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    unique_artists = np.unique(artists)
    artist_to_indices = {artist: np.flatnonzero(artists == artist) for artist in unique_artists}
    if mode == "artist_bootstrap":
        sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
    elif mode == "artist_subsample_70pct":
        sample_n = max(1, int(round(len(unique_artists) * ARTIST_SUBSAMPLE_RATE)))
        sampled_artists = rng.choice(unique_artists, size=sample_n, replace=False)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return np.concatenate([artist_to_indices[artist] for artist in sampled_artists])


def bootstrap_compare(wide: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for split in ["validation", "test"]:
        frame = wide[wide["split"].eq(split)].dropna(subset=[BASELINE]).copy()
        if frame.empty:
            continue
        for iteration in range(BOOTSTRAP_ITERATIONS):
            for mode in ["row_bootstrap", "artist_bootstrap", "artist_subsample_70pct"]:
                idx = sample_indices_by_artist(frame, rng, mode)
                sample = frame.iloc[idx].copy()
                base_metrics = metrics_from_arrays(
                    sample["actual_log"].to_numpy(dtype=float),
                    sample[BASELINE].to_numpy(dtype=float),
                )
                for candidate in candidates:
                    if candidate == BASELINE:
                        continue
                    cand_metrics = metrics_from_arrays(
                        sample["actual_log"].to_numpy(dtype=float),
                        sample[candidate].to_numpy(dtype=float),
                    )
                    row = {
                        "experiment_id": EXP_ID,
                        "split": split,
                        "candidate": candidate,
                        "baseline": BASELINE,
                        "bootstrap_mode": mode,
                        "iteration": iteration,
                        "n": cand_metrics["n"],
                    }
                    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                        row[f"baseline_{metric}"] = base_metrics[metric]
                        row[f"candidate_{metric}"] = cand_metrics[metric]
                        row[f"delta_{metric}"] = base_metrics[metric] - cand_metrics[metric]
                    rows.append(row)
    return pd.DataFrame(rows)


def summarize_bootstrap(samples: pd.DataFrame, candidate_roles: pd.DataFrame) -> pd.DataFrame:
    rows = []
    role_map = candidate_roles.set_index("candidate")[["role", "selection_basis"]].to_dict(orient="index")
    for (split, candidate, mode), group in samples.groupby(["split", "candidate", "bootstrap_mode"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "split": split,
            "candidate": candidate,
            "role": role_map.get(candidate, {}).get("role", ""),
            "selection_basis": role_map.get(candidate, {}).get("selection_basis", ""),
            "bootstrap_mode": mode,
            "iterations": int(group["iteration"].nunique()),
            "median_n": float(group["n"].median()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[f"delta_{metric}"].astype(float).dropna().to_numpy()
            row[f"delta_{metric}_median"] = float(np.median(values))
            row[f"delta_{metric}_ci_low"] = float(np.quantile(values, 0.025))
            row[f"delta_{metric}_ci_high"] = float(np.quantile(values, 0.975))
            row[f"delta_{metric}_prob_improve"] = float(np.mean(values > 0))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["split", "role", "bootstrap_mode", "candidate"])


def recommendation_table(point: pd.DataFrame, bootstrap_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    test_point = point[point["split"].eq("test") & ~point["candidate"].eq(BASELINE)].copy()
    for row in test_point.itertuples(index=False):
        artist = bootstrap_summary[
            bootstrap_summary["split"].eq("test")
            & bootstrap_summary["candidate"].eq(row.candidate)
            & bootstrap_summary["bootstrap_mode"].eq("artist_bootstrap")
        ]
        mdape_prob = float(artist.iloc[0]["delta_MdAPE_prob_improve"]) if not artist.empty else np.nan
        mape_prob = float(artist.iloc[0]["delta_MAPE_prob_improve"]) if not artist.empty else np.nan
        p95_prob = float(artist.iloc[0]["delta_p95_APE_prob_improve"]) if not artist.empty else np.nan
        all_point_improved = (
            row.delta_vs_baseline_MdAPE < 0
            and row.delta_vs_baseline_MAPE < 0
            and row.delta_vs_baseline_p95_APE < 0
        )
        stable = mdape_prob >= 0.60 and mape_prob >= 0.60 and p95_prob >= 0.60
        if all_point_improved and stable:
            decision = "반복 검증 후보"
        elif all_point_improved:
            decision = "고정 test 개선 후보"
        elif row.delta_vs_baseline_MAPE < 0 and row.delta_vs_baseline_p95_APE < 0:
            decision = "평균/큰오차 방어 후보"
        else:
            decision = "보류"
        rows.append({
            "candidate": row.candidate,
            "role": row.role,
            "decision": decision,
            "test_MdAPE": row.MdAPE,
            "test_MAPE": row.MAPE,
            "test_p95_APE": row.p95_APE,
            "delta_MdAPE_vs_baseline": row.delta_vs_baseline_MdAPE,
            "delta_MAPE_vs_baseline": row.delta_vs_baseline_MAPE,
            "delta_p95_APE_vs_baseline": row.delta_vs_baseline_p95_APE,
            "artist_bootstrap_MdAPE_prob": mdape_prob,
            "artist_bootstrap_MAPE_prob": mape_prob,
            "artist_bootstrap_p95_prob": p95_prob,
        })
    return pd.DataFrame(rows).sort_values(["decision", "role", "candidate"])


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_결과 없음_"
    view = df.head(max_rows).copy() if max_rows else df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.6f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value).replace("\n", " "))
    lines = [
        "| " + " | ".join(view.columns.astype(str)) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def render_html(title: str, summary: str, tables: dict[str, pd.DataFrame]) -> str:
    body = [
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937;line-height:1.55}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 28px}th,td{border:1px solid #d8dee9;padding:7px 8px;text-align:right}"
        "th:first-child,td:first-child{text-align:left}th{background:#eef2f7}.note{white-space:pre-wrap;background:#f8fafc;border-left:4px solid #2563eb;padding:12px 14px}</style>",
        "</head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='note'>{html.escape(summary)}</div>",
    ]
    for name, table in tables.items():
        body.append(f"<h2>{html.escape(name)}</h2>")
        body.append(table.to_html(index=False, escape=True, float_format=lambda value: f"{value:.6f}"))
    body.append("</body></html>")
    return "\n".join(body)


def main() -> None:
    ensure_dirs()
    candidates = select_candidates()
    base = load_base()
    predictions = reconstruct_predictions(base, candidates)
    point = point_metrics(predictions)
    wide = pivot_predictions(predictions)
    candidate_list = candidates["candidate"].tolist()
    bootstrap_samples = bootstrap_compare(wide, candidate_list)
    bootstrap_summary = summarize_bootstrap(bootstrap_samples, candidates)
    recommendations = recommendation_table(point, bootstrap_summary)

    candidates.to_csv(OUT_DIR / "candidate_selection.csv", index=False)
    predictions.to_csv(OUT_DIR / "reconstructed_predictions.csv", index=False)
    point.to_csv(OUT_DIR / "point_metrics.csv", index=False)
    bootstrap_samples.to_csv(OUT_DIR / "bootstrap_samples.csv", index=False)
    bootstrap_summary.to_csv(OUT_DIR / "bootstrap_summary.csv", index=False)
    recommendations.to_csv(OUT_DIR / "recommendations.csv", index=False)

    summary = "\n".join([
        "- 목적: PP-AMW2 Warm 작가 메타 + 검색 피처 보정 후보의 안정성 검증",
        "- 방식: frozen PP-V8 예측값 위에서 AMW1/H29 validation 보정값을 재구성",
        "- 검증: row bootstrap, artist bootstrap, artist 70% subsample",
        "- 반복 수: 1000회",
        "- 한계: 새 split마다 PP-V8/AMW 보정값을 재학습한 full repeated split은 아님",
        "- 운영 코드 변경: 없음",
        "",
        "판단:",
        "- artist bootstrap에서 MdAPE/MAPE/p95 개선 확률이 모두 높아야 운영 후보로 격상 가능",
        "- 한 지표만 좋아지는 후보는 목적별 방어 후보로만 관리",
    ])
    report = f"""# PP-AMW3 Warm 작가 메타 + 검색 피처 보정 안정성 검증

## 1. 실행 요약

{summary}

## 2. 후보 선정

{markdown_table(candidates)}

## 3. 고정 validation/test 지표

{markdown_table(point)}

## 4. 추천 판단

{markdown_table(recommendations)}

## 5. bootstrap 요약

{markdown_table(bootstrap_summary)}

## 6. 산출물

- `outputs/candidate_selection.csv`
- `outputs/reconstructed_predictions.csv`
- `outputs/point_metrics.csv`
- `outputs/bootstrap_samples.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/recommendations.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(
        render_html(
            "PP-AMW3 Warm 작가 메타 + 검색 피처 보정 안정성 검증",
            summary,
            {
                "후보 선정": candidates,
                "고정 validation/test 지표": point,
                "추천 판단": recommendations,
                "bootstrap 요약": bootstrap_summary,
            },
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps({
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "method": "frozen prediction row/artist bootstrap stability validation",
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "artist_subsample_rate": ARTIST_SUBSAMPLE_RATE,
        "inputs": {
            "amw1_predictions": str(AMW1_PRED_PATH.relative_to(REPO)),
            "h29_predictions": str(H29_PRED_PATH.relative_to(REPO)),
            "amw2_outputs": str(AMW2_OUT.relative_to(REPO)),
        },
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "recommendations": recommendations.to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
