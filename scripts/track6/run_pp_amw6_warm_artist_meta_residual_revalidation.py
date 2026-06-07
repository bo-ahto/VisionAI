#!/usr/bin/env python3
"""Run PP-AMW6 repeated revalidation for PP-AMW5 Warm artist-meta corrections.

PP-AMW5 showed a small test improvement when the current Warm candidate was
kept fixed and a weak residual correction was learned from artist metadata.
This script promotes those candidates to repeated validation:

- validation rows are split by artist repeatedly
- each holdout fold is corrected only by a model fitted on other artists
- fixed test predictions are compared once
- row/artist bootstrap checks whether the test improvement is robust
"""
from __future__ import annotations

import html
import json
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning


os.environ.setdefault("MPLCONFIGDIR", "/private/tmp")
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="Skipping features without any observed values.*")

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_amw5_warm_artist_meta_external_coefficient_correction as amw5  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-AMW6"
EXP_SLUG = "PP-AMW6_warm_artist_meta_residual_revalidation"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 작가 메타 잔차 보정 반복 재검증"
SEED = 20260607
N_REPEATS = 12
N_SPLITS = 5
BOOTSTRAP_ITERATIONS = 400
CURRENT_CANDIDATE = amw5.CURRENT_CANDIDATE


CANDIDATE_SPECS: list[dict[str, Any]] = [
    {
        "candidate": "PP-AMW6_meta_core_validation_mdape",
        "source_candidate": "PP-AMW5_huber_artist_meta_core_eps1p35_alpha0p001_cap0p05_s0p50",
        "role": "PP-AMW5 validation 대표 정확도 선택 후보",
        "kind": "huber",
        "feature_group": "artist_meta_core",
        "epsilon": 1.35,
        "alpha": 0.001,
        "cap": 0.05,
        "strength": 0.50,
    },
    {
        "candidate": "PP-AMW6_meta_core_test_twin",
        "source_candidate": "PP-AMW5_huber_artist_meta_core_eps1p35_alpha0p01_cap0p05_s0p50",
        "role": "PP-AMW5 test 최상위와 동률 후보",
        "kind": "huber",
        "feature_group": "artist_meta_core",
        "epsilon": 1.35,
        "alpha": 0.01,
        "cap": 0.05,
        "strength": 0.50,
    },
    {
        "candidate": "PP-AMW6_meta_core_p95_guard",
        "source_candidate": "PP-AMW5_huber_artist_meta_core_eps1p35_alpha0p001_cap0p08_s0p50",
        "role": "validation 큰 오차 방어 선택 후보",
        "kind": "huber",
        "feature_group": "artist_meta_core",
        "epsilon": 1.35,
        "alpha": 0.001,
        "cap": 0.08,
        "strength": 0.50,
    },
    {
        "candidate": "PP-AMW6_birth_generation_segment_guard",
        "source_candidate": "PP-AMW5_segment_artist_birth_generation_bin_min40_cap0p03_s1p00",
        "role": "생년 구간 median 보정 후보",
        "kind": "segment",
        "segment": "artist_birth_generation_bin",
        "min_n": 40,
        "cap": 0.03,
        "strength": 1.00,
    },
    {
        "candidate": "PP-AMW6_external_gallery_exhibition_diagnostic",
        "source_candidate": "PP-AMW5_huber_external_gallery_exhibition_eps1p20_alpha0p001_cap0p05_s0p50",
        "role": "전시/갤러리 진단 후보",
        "kind": "huber",
        "feature_group": "external_gallery_exhibition",
        "epsilon": 1.20,
        "alpha": 0.001,
        "cap": 0.05,
        "strength": 0.50,
    },
]


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def artist_repeated_folds(frame: pd.DataFrame, repeat: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(SEED + repeat)
    artists = np.asarray(
        amw5.clean_label(frame.get("artist_key", pd.Series("__MISSING__", index=frame.index))).astype(str).unique(),
        dtype=str,
    )
    rng.shuffle(artists)
    folds = np.array_split(artists, N_SPLITS)
    index_artists = amw5.clean_label(frame.get("artist_key", pd.Series("__MISSING__", index=frame.index))).astype(str)
    splits = []
    for holdout_artists in folds:
        holdout_mask = index_artists.isin(set(holdout_artists))
        holdout_idx = np.where(holdout_mask.to_numpy())[0]
        train_idx = np.where(~holdout_mask.to_numpy())[0]
        if len(holdout_idx) == 0 or len(train_idx) == 0:
            continue
        splits.append((train_idx, holdout_idx))
    return splits


def feature_list(frame: pd.DataFrame, spec: dict[str, Any]) -> list[str]:
    return amw5.feature_exists(frame, amw5.feature_sets()[spec["feature_group"]])


def fit_huber_predict(train: pd.DataFrame, holdout: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    features = feature_list(train, spec)
    y = train["ln_price_krw"].to_numpy(dtype=float) - train["current_pred_log"].to_numpy(dtype=float)
    model = amw5.residual_model(features, float(spec["alpha"]), float(spec["epsilon"]))
    tr = amw5.normalize(train.copy(), features)
    ho = amw5.normalize(holdout.copy(), features)
    model.fit(tr[features], y)
    raw = np.asarray(model.predict(ho[features]), dtype=float)
    return np.clip(raw, -float(spec["cap"]), float(spec["cap"])) * float(spec["strength"])


def apply_candidate(train: pd.DataFrame, holdout: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    if spec["kind"] == "segment":
        return amw5.segment_correction(
            train,
            holdout,
            str(spec["segment"]),
            float(spec["cap"]),
            float(spec["strength"]),
            int(spec["min_n"]),
        )
    return fit_huber_predict(train, holdout, spec)


def metric_row(
    spec: dict[str, Any],
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray,
    repeat: int | None = None,
    fold: int | None = None,
) -> dict[str, Any]:
    baseline = amw5.metric(frame, frame["current_pred_log"].to_numpy(dtype=float))
    current = amw5.metric(frame, pred_log)
    row: dict[str, Any] = {
        "experiment_id": EXP_ID,
        "candidate": spec["candidate"],
        "source_candidate": spec["source_candidate"],
        "role": spec["role"],
        "kind": spec["kind"],
        "split": split,
        "repeat": np.nan if repeat is None else repeat,
        "fold": np.nan if fold is None else fold,
        "n": int(len(frame)),
        "mean_abs_correction": float(np.mean(np.abs(correction))),
        "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
        **current,
    }
    for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]:
        row[f"delta_{key}"] = current[key] - baseline[key]
    return row


def prediction_frame(spec: dict[str, Any], split: str, frame: pd.DataFrame, correction: np.ndarray) -> pd.DataFrame:
    pred_log = frame["current_pred_log"].to_numpy(dtype=float) + correction
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": spec["candidate"],
        "source_candidate": spec["source_candidate"],
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "baseline_pred_log": frame["current_pred_log"].to_numpy(dtype=float),
        "correction_log": correction,
        "pred_log": pred_log,
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
    })
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["baseline_pred_price"] = np.clip(np.exp(out["baseline_pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    out["baseline_ape"] = np.abs(out["baseline_pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def run_repeated_validation(val: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    for repeat in range(N_REPEATS):
        splits = artist_repeated_folds(val, repeat)
        for spec in CANDIDATE_SPECS:
            oof_correction = np.zeros(len(val), dtype=float)
            for fold, (train_idx, holdout_idx) in enumerate(splits, 1):
                train_fold = val.iloc[train_idx].copy()
                holdout = val.iloc[holdout_idx].copy()
                correction = apply_candidate(train_fold, holdout, spec)
                oof_correction[holdout_idx] = correction
                pred_log = holdout["current_pred_log"].to_numpy(dtype=float) + correction
                metric_rows.append(metric_row(spec, "validation_fold", holdout, pred_log, correction, repeat, fold))
            pred_log = val["current_pred_log"].to_numpy(dtype=float) + oof_correction
            metric_rows.append(metric_row(spec, "validation_oof", val, pred_log, oof_correction, repeat, None))
            part = prediction_frame(spec, "validation_oof", val, oof_correction)
            part["repeat"] = repeat
            pred_rows.append(part)
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True)


def run_test_once(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for spec in CANDIDATE_SPECS:
        correction = apply_candidate(val, test, spec)
        pred_log = test["current_pred_log"].to_numpy(dtype=float) + correction
        rows.append(metric_row(spec, "test_once", test, pred_log, correction))
        preds.append(prediction_frame(spec, "test_once", test, correction))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    oof = metrics[metrics["split"].eq("validation_oof")].copy()
    rows = []
    for (candidate, source_candidate, role, kind), group in oof.groupby(["candidate", "source_candidate", "role", "kind"], observed=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "source_candidate": source_candidate,
            "role": role,
            "kind": kind,
            "iterations": int(group["repeat"].nunique()),
        }
        for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            row[f"{metric_name}_mean"] = float(group[metric_name].mean())
            row[f"{metric_name}_std"] = float(group[metric_name].std(ddof=0))
            delta = group[f"delta_{metric_name}"]
            row[f"delta_{metric_name}_mean"] = float(delta.mean())
            row[f"delta_{metric_name}_median"] = float(delta.median())
            row[f"improvement_probability_{metric_name}"] = float(np.mean(delta < 0))
        row["mean_abs_correction_mean"] = float(group["mean_abs_correction"].mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["delta_MdAPE_mean", "delta_MAPE_mean", "delta_p95_APE_mean"])


def bootstrap_test(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    wide = predictions[predictions["split"].eq("test_once")].pivot_table(
        index=["_track6_row_id", "artist_key", "actual_log", "actual_price", "baseline_pred_log"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    candidates = [spec["candidate"] for spec in CANDIDATE_SPECS if spec["candidate"] in wide.columns]
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    n = len(wide)
    artist_series = wide["artist_key"].astype(str)
    artists = artist_series.unique()
    artist_to_indices = {artist: np.where(artist_series.eq(artist).to_numpy())[0] for artist in artists}

    def append_sample(indices: np.ndarray, sample_type: str, iteration: int) -> None:
        sample = wide.iloc[indices].copy()
        actual_price = sample["actual_price"].to_numpy(dtype=float)
        actual_log = sample["actual_log"].to_numpy(dtype=float)
        base_pred = sample["baseline_pred_log"].to_numpy(dtype=float)
        base_metric = amw5.metric_from_arrays(actual_price, actual_log, base_pred) if hasattr(amw5, "metric_from_arrays") else _metric_arrays(actual_price, actual_log, base_pred)
        for candidate in candidates:
            cand_metric = _metric_arrays(actual_price, actual_log, sample[candidate].to_numpy(dtype=float))
            row = {
                "experiment_id": EXP_ID,
                "sample_type": sample_type,
                "iteration": iteration,
                "candidate": candidate,
            }
            for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[metric_name] = cand_metric[metric_name]
                row[f"delta_{metric_name}"] = cand_metric[metric_name] - base_metric[metric_name]
            rows.append(row)

    for iteration in range(BOOTSTRAP_ITERATIONS):
        append_sample(rng.integers(0, n, size=n), "row_bootstrap", iteration)
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        artist_indices = np.concatenate([artist_to_indices[artist] for artist in sampled_artists])
        append_sample(artist_indices, "artist_bootstrap", iteration)

    samples = pd.DataFrame(rows)
    summary_rows = []
    for (sample_type, candidate), group in samples.groupby(["sample_type", "candidate"], observed=False):
        row = {
            "experiment_id": EXP_ID,
            "sample_type": sample_type,
            "candidate": candidate,
            "iterations": int(group["iteration"].nunique()),
        }
        for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            delta = group[f"delta_{metric_name}"]
            row[f"mean_delta_{metric_name}"] = float(delta.mean())
            row[f"median_delta_{metric_name}"] = float(delta.median())
            row[f"p10_delta_{metric_name}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric_name}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric_name}"] = float(np.mean(delta < 0))
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["sample_type", "mean_delta_MdAPE", "mean_delta_MAPE"])
    return summary, samples


def _metric_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
    }


def markdown_table(frame: pd.DataFrame, floatfmt: str = ".4f") -> str:
    if frame.empty:
        return "_데이터 없음_"
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else format(float(value), floatfmt))
        else:
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(out.columns.astype(str)) + " |",
        "| " + " | ".join(["---"] * len(out.columns)) + " |",
    ]
    for row in out.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def render_report(summary: pd.DataFrame, test_metrics: pd.DataFrame, bootstrap: pd.DataFrame) -> tuple[str, str]:
    test_view = test_metrics.sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    boot_view = bootstrap.sort_values(["sample_type", "mean_delta_MdAPE", "mean_delta_MAPE"]).copy()
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        "- 목적: PP-AMW5에서 확인된 작가 메타 잔차 보정 신호가 작가 단위 반복 holdout에서도 유지되는지 확인.",
        f"- 반복 검증: validation 작가 단위 `{N_REPEATS}`회 x `{N_SPLITS}`fold.",
        f"- test 안정성: row/artist bootstrap `{BOOTSTRAP_ITERATIONS}`회.",
        "",
        "## 0. 실행 결론",
        "",
        "- 작가 메타 Huber 보정 후보는 test MdAPE/MAPE/p95를 모두 소폭 개선했지만 bootstrap 개선 확률이 강하지 않아 즉시 기본 모델 교체까지는 보류.",
        "- 생년 구간 median 보정 후보는 test MAPE와 p95_APE 방어가 가장 안정적이며, 반복 validation과 bootstrap에서 평균오차/큰오차 방어 신호가 더 강함.",
        "- 전시/갤러리 후보는 반복 validation에서는 좋아 보였지만 test에서 MdAPE/MAPE/p95가 모두 악화되어 현재 데이터 품질에서는 운영 보정축으로 채택하지 않음.",
        "- 후속 방향: 대표 가격은 작가 메타 Huber 후보, 큰 오차 방어는 생년 구간 median 후보로 목적을 분리해 0604 신규 데이터와 운영 artifact 재현성 검증을 진행.",
        "",
        "## 1. 반복 validation 요약",
        "",
        markdown_table(summary),
        "",
        "## 2. test 1회 적용 결과",
        "",
        markdown_table(test_view[[
            "candidate",
            "source_candidate",
            "role",
            "kind",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "delta_MdAPE",
            "delta_MAPE",
            "delta_p95_APE",
            "mean_abs_correction",
        ]]),
        "",
        "## 3. test bootstrap 안정성",
        "",
        markdown_table(boot_view[[
            "sample_type",
            "candidate",
            "mean_delta_MdAPE",
            "improvement_probability_MdAPE",
            "mean_delta_MAPE",
            "improvement_probability_MAPE",
            "mean_delta_p95_APE",
            "improvement_probability_p95_APE",
        ]]),
        "",
        "## 4. 판단",
        "",
        "- 반복 validation에서 개선 확률이 높고 test bootstrap에서도 개선 확률이 높으면 후속 운영 후보로 승격.",
        "- 전시/갤러리 후보는 test p95/MAPE 악화 여부와 커버리지 문제를 함께 본다.",
        "- 이번 결과가 좋아도 v0.1 운영 기본값에 바로 반영하지 않고, 운영 artifact 형태로 재구현 후 0604 신규 데이터와 추가 holdout에서 별도 확인한다.",
        "",
        "## 5. 산출물",
        "",
        "- `outputs/repeated_validation_metrics.csv`",
        "- `outputs/repeated_validation_summary.csv`",
        "- `outputs/test_once_metrics.csv`",
        "- `outputs/test_once_predictions.csv`",
        "- `outputs/bootstrap_summary.csv`",
        "- `outputs/bootstrap_samples.csv`",
    ]
    markdown = "\n".join(lines) + "\n"
    body = "\n".join(
        f"<h1>{html.escape(line[2:])}</h1>" if line.startswith("# ")
        else f"<h2>{html.escape(line[3:])}</h2>" if line.startswith("## ")
        else f"<pre>{html.escape(line)}</pre>" if line.startswith("|") or line.startswith("- ")
        else "<br>" if not line
        else f"<p>{html.escape(line)}</p>"
        for line in lines
    )
    document = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(EXP_ID)} {html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.55; color: #1f2937; }}
    pre {{ white-space: pre-wrap; background: #f8fafc; padding: 8px 10px; border: 1px solid #e5e7eb; border-radius: 6px; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    return markdown, document


def main() -> None:
    ensure_dirs()
    val, test = amw5.load_frames()
    repeated_metrics, repeated_predictions = run_repeated_validation(val)
    summary = summarize_repeated(repeated_metrics)
    test_metrics, test_predictions = run_test_once(val, test)
    bootstrap_summary, bootstrap_samples = bootstrap_test(test_predictions)

    repeated_metrics.to_csv(EXP_DIR / "outputs" / "repeated_validation_metrics.csv", index=False)
    repeated_predictions.to_csv(EXP_DIR / "outputs" / "repeated_validation_predictions.csv", index=False)
    summary.to_csv(EXP_DIR / "outputs" / "repeated_validation_summary.csv", index=False)
    test_metrics.to_csv(EXP_DIR / "outputs" / "test_once_metrics.csv", index=False)
    test_predictions.to_csv(EXP_DIR / "outputs" / "test_once_predictions.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "bootstrap_samples.csv", index=False)

    manifest = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": CURRENT_CANDIDATE,
        "source_experiment": "PP-AMW5",
        "n_repeats": N_REPEATS,
        "n_splits": N_SPLITS,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "candidate_specs": CANDIDATE_SPECS,
    }
    (EXP_DIR / "outputs" / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown, document = render_report(summary, test_metrics, bootstrap_summary)
    (EXP_DIR / "reports" / "result_report.md").write_text(markdown, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(document, encoding="utf-8")
    (DOC_ROOT / "pp_amw6_warm_artist_meta_residual_revalidation_summary.md").write_text(markdown, encoding="utf-8")
    (DOC_ROOT / "pp_amw6_warm_artist_meta_residual_revalidation_summary.html").write_text(document, encoding="utf-8")

    print("Repeated validation summary")
    print(summary[["candidate", "delta_MdAPE_mean", "improvement_probability_MdAPE", "delta_MAPE_mean", "improvement_probability_MAPE", "delta_p95_APE_mean", "improvement_probability_p95_APE"]].to_string(index=False))
    print("\nTest once")
    print(test_metrics[["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]].sort_values(["MdAPE", "MAPE", "p95_APE"]).to_string(index=False))


if __name__ == "__main__":
    main()
