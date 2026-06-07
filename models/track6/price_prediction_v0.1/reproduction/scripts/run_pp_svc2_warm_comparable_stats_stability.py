#!/usr/bin/env python3
"""Run PP-SVC2 Warm comparable-stat stability validation."""
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
from sklearn.model_selection import KFold


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SVC2"
EXP_SLUG = "PP-SVC2_warm_comparable_stats_stability"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 비교군 통계 피처 안정성 검증"
SEEDS = list(range(202606030, 202606040))
BOOTSTRAP_ITERATIONS = 500

REFERENCE_CANDIDATES = [
    {
        "label": "pp_v6_fine_blend_mape_guarded",
        "source": "PP-V6",
        "path": EXP_ROOT / "PP-V6_warm_l10_refreshed_fine_blend" / "outputs" / "predictions.csv",
        "candidate": "fine_blend_mape_guarded",
    },
    {
        "label": "pp_v8_compact_blend_mape_guarded",
        "source": "PP-V8",
        "path": EXP_ROOT / "PP-V8_warm_deployment_simplification" / "outputs" / "predictions.csv",
        "candidate": "compact_blend_mape_guarded",
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def crossfit_train_stats(train: pd.DataFrame, seed: int) -> pd.DataFrame:
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    parts: list[pd.DataFrame] = []
    for source_idx, holdout_idx in kfold.split(train):
        source = train.iloc[source_idx].copy()
        target = train.iloc[holdout_idx].copy()
        parts.append(svc1.apply_comparable_stats(source, target))
    return pd.concat(parts, ignore_index=True)


def add_service_features_seed(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_stats = crossfit_train_stats(train, seed)
    val_stats = svc1.apply_comparable_stats(train, val)
    test_stats = svc1.apply_comparable_stats(train, test)
    return (
        train.merge(train_stats, on="_track6_row_id", how="left"),
        val.merge(val_stats, on="_track6_row_id", how="left"),
        test.merge(test_stats, on="_track6_row_id", how="left"),
    )


def metric_row(
    experiment_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    seed: int | None,
    base_candidate: str,
    source: str,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "candidate": candidate,
        "base_candidate": base_candidate,
        "split": split,
        "scope": "warm",
        "source": source,
        "seed": seed,
        **svc1.metric_values(frame, pred_log),
    }


def prediction_rows(
    experiment_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    seed: int | None,
    base_candidate: str,
    source: str,
) -> pd.DataFrame:
    out = svc1.prediction_frame(experiment_id, candidate, "warm", split, frame, pred_log)
    out["seed"] = seed
    out["base_candidate"] = base_candidate
    out["source"] = source
    return out


def load_reference_predictions() -> list[pd.DataFrame]:
    refs: list[pd.DataFrame] = []
    for cfg in REFERENCE_CANDIDATES:
        path = Path(cfg["path"])
        if not path.exists():
            continue
        df = pd.read_csv(path, low_memory=False)
        if "scope" in df.columns:
            df = df[df["scope"].astype(str).eq("warm")].copy()
        df = df[
            df["split"].astype(str).isin(["validation", "test"])
            & df["candidate"].astype(str).eq(cfg["candidate"])
        ].copy()
        if df.empty:
            continue
        part = df[["split", "_track6_row_id", "actual_log", "pred_log", "actual_price", "pred_price", "residual_log", "ape"]].copy()
        part["ln_price_krw"] = part["actual_log"]
        part["price_krw"] = part["actual_price"]
        part["experiment_id"] = EXP_ID
        part["candidate"] = cfg["label"]
        part["scope"] = "warm"
        part["seed"] = np.nan
        part["base_candidate"] = cfg["label"]
        part["source"] = cfg["source"]
        part["svc_group_level"] = ""
        part["svc_coverage_tier"] = ""
        part["svc_group_n"] = np.nan
        refs.append(part)
    return refs


def load_warm_meta() -> pd.DataFrame:
    frames = []
    for split, filename in [("validation", "track6_val_warm.csv"), ("test", "track6_test_warm.csv")]:
        df = pd.read_csv(REPO / "data" / "track6_split" / filename, low_memory=False)
        keep = [col for col in ["_track6_row_id", "artist_key", "artist_name_ko", "artist_works_count_train"] if col in df.columns]
        part = df[keep].drop_duplicates("_track6_row_id").copy()
        part["split"] = split
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def make_seed_mean_predictions(pred_df: pd.DataFrame, frame_by_split: dict[str, pd.DataFrame], base_candidate: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    seed_candidates = pred_df[pred_df["base_candidate"].eq(base_candidate)].copy()
    if seed_candidates.empty:
        return rows, preds
    for split, group in seed_candidates.groupby("split", dropna=False):
        pivot = group.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last")
        mean_pred = pivot.mean(axis=1).rename("pred_log").reset_index()
        frame = frame_by_split[split].merge(mean_pred, on="_track6_row_id", how="inner")
        label = f"{base_candidate}_seed_mean"
        pred_log = frame["pred_log"].to_numpy(dtype=float)
        rows.append(metric_row(EXP_ID, label, split, frame, pred_log, None, base_candidate, "seed_mean"))
        preds.append(prediction_rows(EXP_ID, label, split, frame, pred_log, None, base_candidate, "seed_mean"))
    return rows, preds


def metric_values_for_bootstrap(frame: pd.DataFrame, pred_col: str) -> dict[str, float]:
    pred = frame[pred_col].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
    }


def bootstrap_compare(pred_df: pd.DataFrame, baseline: str, candidates: list[str]) -> pd.DataFrame:
    test = pred_df[pred_df["split"].eq("test")].copy()
    base = test[["split", "_track6_row_id", "actual_log", "actual_price", "artist_key"]].drop_duplicates(["split", "_track6_row_id"])
    wide = test.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last").reset_index()
    data = base.merge(wide, on="_track6_row_id", how="inner")
    data = data.dropna(subset=[baseline])
    rng = np.random.default_rng(20260603)
    row_indices = np.arange(len(data))
    artist_keys = data["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    unique_artists = np.unique(artist_keys)
    artist_to_indices = {artist: np.flatnonzero(artist_keys == artist) for artist in unique_artists}
    rows: list[dict[str, Any]] = []
    for iteration in range(BOOTSTRAP_ITERATIONS):
        row_sample = rng.choice(row_indices, size=len(row_indices), replace=True)
        artist_sample_keys = rng.choice(unique_artists, size=len(unique_artists), replace=True)
        artist_sample = np.concatenate([artist_to_indices[artist] for artist in artist_sample_keys])
        for mode, indices in [("row_bootstrap", row_sample), ("artist_bootstrap", artist_sample)]:
            sample = data.iloc[indices].copy()
            for candidate in candidates:
                if candidate == baseline or candidate not in sample.columns:
                    continue
                usable = sample.dropna(subset=[candidate, baseline])
                if usable.empty:
                    continue
                base_metrics = metric_values_for_bootstrap(usable, baseline)
                cand_metrics = metric_values_for_bootstrap(usable, candidate)
                row: dict[str, Any] = {
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "baseline": baseline,
                    "bootstrap_mode": mode,
                    "iteration": iteration,
                    "n": int(len(usable)),
                }
                for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                    row[f"baseline_{metric}"] = base_metrics[metric]
                    row[f"candidate_{metric}"] = cand_metrics[metric]
                    row[f"delta_{metric}"] = base_metrics[metric] - cand_metrics[metric]
                rows.append(row)
    return pd.DataFrame(rows)


def summarize_bootstrap(bootstrap: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if bootstrap.empty:
        return pd.DataFrame()
    for (candidate, mode), group in bootstrap.groupby(["candidate", "bootstrap_mode"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
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
    return pd.DataFrame(rows)


def slice_metrics(pred_df: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    test = pred_df[pred_df["split"].eq("test")].copy()
    for candidate in candidates:
        part = test[test["candidate"].eq(candidate)].copy()
        if part.empty:
            continue
        for col in ["svc_group_level", "svc_coverage_tier"]:
            if col not in part.columns:
                continue
            for value, group in part.groupby(col, dropna=False):
                if str(value) == "":
                    continue
                pred_log = group["pred_log"].to_numpy(dtype=float)
                actual_log = group["actual_log"].to_numpy(dtype=float)
                actual_price = group["actual_price"].to_numpy(dtype=float)
                pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
                ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "slice_column": col,
                    "slice_value": value,
                    "n": int(len(group)),
                    "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
                    "MdAPE": float(np.median(ape)),
                    "MAPE": float(np.mean(ape)),
                    "p95_APE": float(np.quantile(ape, 0.95)),
                    "Within_30": float(np.mean(ape <= 0.30)),
                    "Within_50": float(np.mean(ape <= 0.50)),
                })
    return pd.DataFrame(rows)


def seed_stability(metrics_df: pd.DataFrame) -> pd.DataFrame:
    seed_metrics = metrics_df[
        metrics_df["split"].eq("test")
        & metrics_df["base_candidate"].isin(["svc_numeric", "svc_full"])
        & metrics_df["seed"].notna()
    ].copy()
    rows: list[dict[str, Any]] = []
    for base_candidate, group in seed_metrics.groupby("base_candidate", dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "base_candidate": base_candidate,
            "seeds": int(group["seed"].nunique()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[metric].astype(float).to_numpy()
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_std"] = float(np.std(values, ddof=0))
            row[f"{metric}_min"] = float(np.min(values))
            row[f"{metric}_max"] = float(np.max(values))
        rows.append(row)
    return pd.DataFrame(rows)


def render_report(metrics: pd.DataFrame, stability: pd.DataFrame, bootstrap_summary: pd.DataFrame, slices: pd.DataFrame) -> tuple[str, str]:
    test = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: `PP-SVC1-W`의 비교군 통계 피처 개선이 fold seed와 후보 비교에서 안정적인지 확인한다.",
        "- 방식: Warm Huber에 비교군 통계 피처를 넣고 OOF fold seed 10개로 반복 재학습했다.",
        "",
        "## 1. Test 결과",
        "",
        "| 후보 | source | seed | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in test.itertuples():
        seed = "" if pd.isna(row.seed) else str(int(row.seed))
        lines.append(
            f"| `{row.candidate}` | {row.source} | {seed} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += ["", "## 2. Seed 안정성", "", "| 후보 | seeds | MdAPE mean/std | MAPE mean/std | p95 mean/std |", "|---|---:|---:|---:|---:|"]
    for row in stability.itertuples():
        lines.append(
            f"| `{row.base_candidate}` | {row.seeds} | {row.MdAPE_mean:.4f} / {row.MdAPE_std:.4f} | "
            f"{row.MAPE_mean:.4f} / {row.MAPE_std:.4f} | {row.p95_APE_mean:.4f} / {row.p95_APE_std:.4f} |"
        )
    lines += ["", "## 3. PP-V6 대비 bootstrap", "", "| 후보 | mode | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | MdAPE delta 중앙값 |", "|---|---|---:|---:|---:|---:|"]
    for row in bootstrap_summary.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.bootstrap_mode} | {row.delta_MdAPE_prob_improve:.3f} | "
            f"{row.delta_MAPE_prob_improve:.3f} | {row.delta_p95_APE_prob_improve:.3f} | {row.delta_MdAPE_median:.4f} |"
        )
    lines += ["", "## 4. Slice 결과", "", "| 후보 | slice | value | n | MdAPE | MAPE | p95_APE |", "|---|---|---|---:|---:|---:|---:|"]
    for row in slices.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.slice_column} | `{row.slice_value}` | {row.n} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 5. 해석",
        "",
        "- seed별 성능 편차가 작다면 비교군 통계 피처는 OOF fold 우연에 덜 민감하다고 본다.",
        "- `svc_full_seed_mean`이 `PP-V6`보다 bootstrap 개선확률이 높으면 Warm 최종 후보 재검증 대상으로 올린다.",
        "- 직접 비교군 중앙값 후보가 약하면, 개선 원인은 중앙값 직접 대체가 아니라 Huber가 비교군 통계를 설명 변수로 사용한 효과로 해석한다.",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>Metrics</h2>{metrics.to_html(index=False, escape=True)}
<h2>Seed Stability</h2>{stability.to_html(index=False, escape=True)}
<h2>Bootstrap Summary</h2>{bootstrap_summary.to_html(index=False, escape=True)}
<h2>Slice Metrics</h2>{slices.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = time.time()
    ensure_dirs()
    features = artifact_features()["warm"]
    requested = list(dict.fromkeys([*features, *svc1.GROUPING_FEATURES]))
    train_base, val_base, test_base = load_scope("warm", requested)
    feature_sets = {
        "baseline_huber": list(features),
        "svc_numeric": list(dict.fromkeys([*features, *svc1.SVC_NUMERIC])),
        "svc_full": list(dict.fromkeys([*features, *svc1.SVC_NUMERIC, *svc1.SVC_CATEGORICAL])),
    }
    metrics_rows: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    frame_by_split: dict[str, pd.DataFrame] = {}

    # Baseline is seed-independent.
    train0, val0, test0 = add_service_features_seed(train_base, val_base, test_base, SEEDS[0])
    frame_by_split = {"validation": val0, "test": test0}
    base_features = feature_sets["baseline_huber"]
    train_n = svc1.normalize(train0, base_features)
    val_n = svc1.normalize(val0, base_features)
    test_n = svc1.normalize(test0, base_features)
    base_pred = svc1.fit_predict("huber", train_n, val_n, test_n, base_features)
    for split, frame, pred_log in [("validation", val_n, base_pred["validation"]), ("test", test_n, base_pred["test"])]:
        metrics_rows.append(metric_row(EXP_ID, "baseline_huber", split, frame, pred_log, None, "baseline_huber", "PP-SVC2"))
        predictions.append(prediction_rows(EXP_ID, "baseline_huber", split, frame, pred_log, None, "baseline_huber", "PP-SVC2"))

    # Direct service prior is seed-independent.
    for split, frame in [("validation", val0), ("test", test0)]:
        pred_log = frame["svc_group_log_price_median"].to_numpy(dtype=float)
        metrics_rows.append(metric_row(EXP_ID, "direct_group_median", split, frame, pred_log, None, "direct_group_median", "service_prior"))
        predictions.append(prediction_rows(EXP_ID, "direct_group_median", split, frame, pred_log, None, "direct_group_median", "service_prior"))

    for seed in SEEDS:
        train_s, val_s, test_s = add_service_features_seed(train_base, val_base, test_base, seed)
        for base_candidate in ["svc_numeric", "svc_full"]:
            candidate = f"{base_candidate}_seed_{seed}"
            cols = feature_sets[base_candidate]
            train_n = svc1.normalize(train_s, cols)
            val_n = svc1.normalize(val_s, cols)
            test_n = svc1.normalize(test_s, cols)
            pred = svc1.fit_predict("huber", train_n, val_n, test_n, cols)
            for split, frame, pred_log in [("validation", val_n, pred["validation"]), ("test", test_n, pred["test"])]:
                metrics_rows.append(metric_row(EXP_ID, candidate, split, frame, pred_log, seed, base_candidate, "PP-SVC2_seed_repeat"))
                predictions.append(prediction_rows(EXP_ID, candidate, split, frame, pred_log, seed, base_candidate, "PP-SVC2_seed_repeat"))

    pred_df = pd.concat(predictions, ignore_index=True)
    for base_candidate in ["svc_numeric", "svc_full"]:
        mean_rows, mean_preds = make_seed_mean_predictions(pred_df, frame_by_split, base_candidate)
        metrics_rows.extend(mean_rows)
        pred_df = pd.concat([pred_df, *mean_preds], ignore_index=True)

    ref_preds = load_reference_predictions()
    if ref_preds:
        pred_df = pd.concat([pred_df, *ref_preds], ignore_index=True)
        for ref in ref_preds:
            for (candidate, split), group in ref.groupby(["candidate", "split"], dropna=False):
                metrics_rows.append(metric_row(EXP_ID, candidate, split, group, group["pred_log"].to_numpy(dtype=float), None, candidate, str(group["source"].iloc[0])))

    meta = load_warm_meta()
    pred_df = pred_df.merge(meta, on=["split", "_track6_row_id"], how="left")
    metrics_df = pd.DataFrame(metrics_rows)
    stability_df = seed_stability(metrics_df)
    bootstrap_candidates = [
        "svc_full_seed_mean",
        "svc_numeric_seed_mean",
        "baseline_huber",
        "direct_group_median",
        "pp_v8_compact_blend_mape_guarded",
    ]
    bootstrap_df = bootstrap_compare(pred_df, "pp_v6_fine_blend_mape_guarded", bootstrap_candidates)
    bootstrap_summary = summarize_bootstrap(bootstrap_df)
    slice_df = slice_metrics(pred_df, ["svc_full_seed_mean", "svc_numeric_seed_mean", "baseline_huber", "direct_group_median"])

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    stability_df.to_csv(EXP_DIR / "outputs" / "seed_stability.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_samples.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_summary.csv", index=False)
    slice_df.to_csv(EXP_DIR / "outputs" / "slice_metrics.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seeds": SEEDS,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "feature_sets": feature_sets,
        "reference_candidates": [
            {**cfg, "path": str(Path(cfg["path"]).relative_to(REPO))}
            for cfg in REFERENCE_CANDIDATES
        ],
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "feature_manifest.json").write_text(json.dumps(feature_sets, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, stability_df, bootstrap_summary, slice_df)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_svc2_warm_comparable_stats_stability_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_svc2_warm_comparable_stats_stability_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
