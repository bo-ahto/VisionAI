from __future__ import annotations

import html
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[7]
EXP_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_amw5_warm_artist_meta_external_coefficient_correction as amw5  # noqa: E402
import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402
import run_pp_z_warm_coldstyle_extension_experiments as ppz  # noqa: E402


OP_PREDICTIONS = (
    REPO
    / "models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/operational_predictions_with_actual.csv"
)
OP_FEATURES = (
    REPO
    / "models/track6/price_prediction_v0.1/operational/outputs/0604_features/features_all_v0_1.csv"
)
PP_AMW6_TEST_METRICS = (
    REPO
    / "experiments/track6/PP-AMW6_warm_artist_meta_residual_revalidation/outputs/test_once_metrics.csv"
)
PP_AMW6_BOOTSTRAP = (
    REPO
    / "experiments/track6/PP-AMW6_warm_artist_meta_residual_revalidation/outputs/bootstrap_summary.csv"
)

FX_USD = 1380.0

BASELINES = {
    "service_primary_ppv8": "pp_v8_compact_blend_mape_guarded_pred_log",
    "report_70_30": "v01_operational_pred_log",
}

CANDIDATE_SPECS: list[dict[str, Any]] = [
    {
        "candidate": "meta_core_validation_mdape",
        "source_candidate": "PP-AMW6_meta_core_validation_mdape",
        "description": "작가 메타 계수 보정, validation 대표 정확도 후보",
        "kind": "huber",
        "feature_group": "artist_meta_core",
        "epsilon": 1.35,
        "alpha": 0.001,
        "cap": 0.05,
        "strength": 0.50,
    },
    {
        "candidate": "meta_core_test_twin",
        "source_candidate": "PP-AMW6_meta_core_test_twin",
        "description": "작가 메타 계수 보정, historical test 최상위 후보",
        "kind": "huber",
        "feature_group": "artist_meta_core",
        "epsilon": 1.35,
        "alpha": 0.01,
        "cap": 0.05,
        "strength": 0.50,
    },
    {
        "candidate": "birth_generation_segment_guard",
        "source_candidate": "PP-AMW6_birth_generation_segment_guard",
        "description": "작가 생년대 구간 중앙값 보정, 평균오차/큰오차 방어 후보",
        "kind": "segment",
        "segment": "artist_birth_generation_bin",
        "min_n": 40,
        "cap": 0.03,
        "strength": 1.00,
    },
    {
        "candidate": "external_gallery_exhibition_diagnostic",
        "source_candidate": "PP-AMW6_external_gallery_exhibition_diagnostic",
        "description": "전시/갤러리 정보 계수 보정, 운영 진단 후보",
        "kind": "huber",
        "feature_group": "external_gallery_exhibition",
        "epsilon": 1.20,
        "alpha": 0.001,
        "cap": 0.05,
        "strength": 0.50,
    },
]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metric_row(frame: pd.DataFrame, scope: str, candidate: str, pred_log_col: str) -> dict[str, Any]:
    actual = pd.to_numeric(frame["actual_price_krw"], errors="coerce")
    pred_log = pd.to_numeric(frame[pred_log_col], errors="coerce")
    pred = pd.Series(safe_exp(pred_log), index=frame.index)
    valid = actual.gt(0) & pred_log.notna()
    ape = ((pred.loc[valid] - actual.loc[valid]).abs() / actual.loc[valid]).replace([np.inf, -np.inf], np.nan).dropna()
    ratio = (pred.loc[valid] / actual.loc[valid]).replace([np.inf, -np.inf], np.nan).dropna()
    log_error = (pred_log.loc[valid] - np.log(actual.loc[valid])).replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "scope": scope,
        "candidate": candidate,
        "n": int(len(ape)),
        "MdAPE": float(ape.median()) if len(ape) else np.nan,
        "MAPE": float(ape.mean()) if len(ape) else np.nan,
        "p95_APE": float(ape.quantile(0.95)) if len(ape) else np.nan,
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))) if len(log_error) else np.nan,
        "median_ratio": float(ratio.median()) if len(ratio) else np.nan,
        "over_3x_n": int((ratio > 3.0).sum()) if len(ratio) else 0,
        "under_1_3x_n": int((ratio < (1.0 / 3.0)).sum()) if len(ratio) else 0,
        "within_30": float((ape <= 0.30).mean()) if len(ape) else np.nan,
        "within_50": float((ape <= 0.50).mean()) if len(ape) else np.nan,
    }


def clean_join_key(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().fillna("__missing__").replace({"": "__missing__"})


def mode_or_first(series: pd.Series) -> Any:
    values = series.dropna()
    if values.empty:
        return np.nan
    mode = values.mode(dropna=True)
    if not mode.empty:
        return mode.iloc[0]
    return values.iloc[0]


def build_artist_lookup() -> tuple[pd.DataFrame, pd.DataFrame]:
    train, val, test = wcoef.load_frames()
    hist = pd.concat([train, val, test], ignore_index=True, sort=False)
    ext = ppz.warm_external_row_map()
    hist = hist.merge(ext, on="_track6_row_id", how="left")
    hist = amw5.engineer_features(hist)
    hist["artist_key_join"] = clean_join_key(hist.get("artist_key", pd.Series("", index=hist.index)))

    lookup_cols = [
        *amw5.ARTIST_META_NUMERIC,
        *amw5.ARTIST_META_CATEGORICAL,
        *amw5.EXTERNAL_NUMERIC,
        *amw5.EXTERNAL_CATEGORICAL,
    ]
    lookup_cols = [col for col in dict.fromkeys(lookup_cols) if col in hist.columns]
    numeric = [col for col in lookup_cols if col in amw5.NUMERIC_FEATURES]
    categorical = [col for col in lookup_cols if col not in amw5.NUMERIC_FEATURES]

    agg: dict[str, Any] = {col: "median" for col in numeric}
    agg.update({col: mode_or_first for col in categorical})
    lookup = hist.groupby("artist_key_join", dropna=False).agg(agg).reset_index()

    coverage_rows = []
    for col in lookup_cols:
        coverage_rows.append(
            {
                "feature": col,
                "historical_artist_lookup_coverage": float(lookup[col].notna().mean()),
                "historical_artist_non_null_n": int(lookup[col].notna().sum()),
                "historical_artist_n": int(len(lookup)),
            }
        )
    return lookup, pd.DataFrame(coverage_rows)


def add_artist_lookup(target: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    out = target.copy()
    out["artist_key_join"] = clean_join_key(out.get("artist_key", pd.Series("", index=out.index)))
    out = out.merge(lookup, on="artist_key_join", how="left", suffixes=("", "__lookup"))
    for col in lookup.columns:
        if col == "artist_key_join":
            continue
        lookup_col = f"{col}__lookup"
        if lookup_col not in out.columns:
            continue
        if col in out.columns:
            out[col] = out[col].combine_first(out[lookup_col])
        else:
            out[col] = out[lookup_col]
        out = out.drop(columns=[lookup_col])
    return out


def add_operational_bins(frame: pd.DataFrame, train_reference: pd.DataFrame, baseline_log_col: str) -> pd.DataFrame:
    out = frame.copy()
    size_edges = wcoef.bin_edges(train_reference, "log_area", [0.25, 0.50, 0.75])
    pred_edges = wcoef.bin_edges(train_reference.rename(columns={"current_pred_log": "pred_for_bin"}), "pred_for_bin", [0.25, 0.50, 0.75])

    out["size_bin"] = wcoef.cut_with_edges(out["log_area"], size_edges, ["small", "mid_low", "mid_high", "large"]).fillna("missing")
    out["pred_log_bin"] = wcoef.cut_with_edges(out[baseline_log_col], pred_edges, ["low", "mid_low", "mid_high", "high"]).fillna("missing")

    n = pd.to_numeric(out.get("svc_group_n", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(0.0)
    iqr = pd.to_numeric(out.get("svc_group_log_price_iqr", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(99.0)
    rel = np.where((n >= 30) & (iqr <= 0.70), "high", np.where((n >= 10) & (iqr <= 1.20), "mid", "low"))
    rel = np.where(n <= 0, "missing", rel)
    out["svc_reliability_bin"] = pd.Series(rel, index=out.index).astype("string")
    return out


def load_training_validation() -> pd.DataFrame:
    val, _test = amw5.load_frames()
    return val.copy()


def load_operational_target(lookup: pd.DataFrame, validation_reference: pd.DataFrame, baseline_name: str, baseline_col: str) -> pd.DataFrame:
    features = pd.read_csv(OP_FEATURES, low_memory=False)
    predictions = pd.read_csv(OP_PREDICTIONS, low_memory=False)
    prediction_cols = [
        "_v01_row_id",
        "actual_price_krw",
        "actual_price_usd_equiv",
        "actual_currency",
        "service_primary_pred_log",
        "pp_v8_compact_blend_mape_guarded_pred_log",
        "v01_operational_pred_log",
        "svc_numeric_seed_mean_pred_log",
        "service_confidence_tier",
        "prediction_status",
    ]
    prediction_cols = [col for col in prediction_cols if col in predictions.columns]
    target = features.merge(predictions[prediction_cols], on="_v01_row_id", how="left")
    target = target[target["warm_cold_route"].astype(str).eq("warm")].copy()
    target = target[target["actual_price_krw"].notna()].copy()
    target["actual_price_krw"] = pd.to_numeric(target["actual_price_krw"], errors="coerce")
    target = target[target["actual_price_krw"] > 0].copy()
    target["ln_price_krw"] = np.log(target["actual_price_krw"])
    target["price_krw"] = target["actual_price_krw"]

    target = add_artist_lookup(target, lookup)
    if "aspect_ratio" not in target.columns:
        width = pd.to_numeric(target.get("width_cm"), errors="coerce")
        height = pd.to_numeric(target.get("height_cm"), errors="coerce")
        target["aspect_ratio"] = width / height.replace(0, np.nan)
    if "svc_group_n_log" not in target.columns:
        target["svc_group_n_log"] = np.log1p(pd.to_numeric(target.get("svc_group_n"), errors="coerce").clip(lower=0).fillna(0.0))

    target["current_pred_log"] = pd.to_numeric(target[baseline_col], errors="coerce")
    target["ppv8_pred_log"] = pd.to_numeric(target["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce")
    target["fallback_pred_log"] = pd.to_numeric(target["svc_numeric_seed_mean_pred_log"], errors="coerce")
    target["current_ppv8_gap_abs"] = (target["current_pred_log"] - target["ppv8_pred_log"]).abs()
    target["current_fallback_gap_abs"] = (target["current_pred_log"] - target["fallback_pred_log"]).abs()
    target = add_operational_bins(target, validation_reference, "current_pred_log")
    target = amw5.engineer_features(target)
    target["baseline_name"] = baseline_name
    return target


def prepare_training_for_baseline(val: pd.DataFrame, baseline_name: str) -> pd.DataFrame:
    out = val.copy()
    if baseline_name == "service_primary_ppv8":
        out["current_pred_log"] = pd.to_numeric(out["ppv8_pred_log"], errors="coerce")
    elif baseline_name == "report_70_30":
        out["current_pred_log"] = pd.to_numeric(out["current_pred_log"], errors="coerce")
    else:
        raise ValueError(f"unknown baseline: {baseline_name}")
    out["current_ppv8_gap_abs"] = (out["current_pred_log"] - out["ppv8_pred_log"]).abs()
    out["current_fallback_gap_abs"] = (out["current_pred_log"] - out["fallback_pred_log"]).abs()
    pred_edges = wcoef.bin_edges(out.rename(columns={"current_pred_log": "pred_for_bin"}), "pred_for_bin", [0.25, 0.50, 0.75])
    out["pred_log_bin"] = wcoef.cut_with_edges(out["current_pred_log"], pred_edges, ["low", "mid_low", "mid_high", "high"]).fillna("missing")
    return amw5.engineer_features(out)


def fit_huber_predict(train: pd.DataFrame, target: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    features = amw5.feature_exists(train, amw5.feature_sets()[spec["feature_group"]])
    for col in features:
        if col not in target.columns:
            target[col] = np.nan if col in amw5.NUMERIC_FEATURES else "__MISSING__"
    y = train["ln_price_krw"].to_numpy(dtype=float) - train["current_pred_log"].to_numpy(dtype=float)
    model = amw5.residual_model(features, float(spec["alpha"]), float(spec["epsilon"]))
    train_norm = amw5.normalize(train.copy(), features)
    target_norm = amw5.normalize(target.copy(), features)
    model.fit(train_norm[features], y)
    raw = np.asarray(model.predict(target_norm[features]), dtype=float)
    return np.clip(raw, -float(spec["cap"]), float(spec["cap"])) * float(spec["strength"])


def apply_candidate(train: pd.DataFrame, target: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    if spec["kind"] == "segment":
        segment = str(spec["segment"])
        if segment not in target.columns:
            target[segment] = "__MISSING__"
        return amw5.segment_correction(
            train,
            target,
            segment,
            float(spec["cap"]),
            float(spec["strength"]),
            int(spec["min_n"]),
        )
    return fit_huber_predict(train, target, spec)


def add_candidate_predictions(target: pd.DataFrame, train: pd.DataFrame, baseline_name: str) -> tuple[pd.DataFrame, list[str]]:
    out = target.copy()
    candidate_cols = [f"{baseline_name}__baseline_log"]
    out[f"{baseline_name}__baseline_log"] = out["current_pred_log"]
    for spec in CANDIDATE_SPECS:
        correction = apply_candidate(train, out, spec)
        log_col = f"{baseline_name}__{spec['candidate']}_log"
        corr_col = f"{baseline_name}__{spec['candidate']}_correction_log"
        out[corr_col] = correction
        out[log_col] = out["current_pred_log"].to_numpy(dtype=float) + correction
        candidate_cols.append(log_col)
    return out, candidate_cols


def evaluate_candidates(frame: pd.DataFrame, candidate_cols: list[str], baseline_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes = {
        f"0604_all_numeric:{baseline_name}": frame.copy(),
        f"0604_excluding_under_50_usd:{baseline_name}": frame[
            pd.to_numeric(frame["actual_price_usd_equiv"], errors="coerce") >= 50
        ].copy(),
    }
    for scope, scope_frame in scopes.items():
        for col in candidate_cols:
            rows.append(metric_row(scope_frame, scope, col.removesuffix("_log"), col))
    metrics = pd.DataFrame(rows)
    baseline_rows = metrics[metrics["candidate"].str.endswith("__baseline")].copy()
    baseline_lookup = baseline_rows.set_index("scope")
    for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "within_50"]:
        metrics[f"delta_{key}"] = metrics.apply(
            lambda row: row[key] - baseline_lookup.loc[row["scope"], key],
            axis=1,
        )
    return metrics


def coverage_table(targets: list[pd.DataFrame], lookup_coverage: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_exhibition_total_count",
        "gallery_tier_raw_numeric",
        "gallery_tier_validated_score",
    ]
    rows = []
    for target in targets:
        label = str(target["baseline_name"].iloc[0])
        for col in cols:
            if col not in target.columns:
                continue
            rows.append(
                {
                    "scope": f"0604:{label}",
                    "feature": col,
                    "coverage": float(target[col].notna().mean()),
                    "non_null_n": int(target[col].notna().sum()),
                    "n": int(len(target)),
                }
            )
    return pd.concat([lookup_coverage.rename(columns={"historical_artist_lookup_coverage": "coverage", "historical_artist_non_null_n": "non_null_n", "historical_artist_n": "n"}).assign(scope="historical_artist_lookup"), pd.DataFrame(rows)], ignore_index=True, sort=False)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_데이터 없음_"
    view = frame.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value))
    rows = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
    ]
    rows.extend("| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None))
    return "\n".join(rows)


def simple_html(title: str, markdown_text: str, tables: dict[str, pd.DataFrame]) -> str:
    body = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:32px;color:#1f2937}table{border-collapse:collapse;width:100%;margin:18px 0;font-size:13px}th,td{border:1px solid #d8dee9;padding:7px 9px;text-align:left}th{background:#eef2f7}.num{text-align:right}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}pre{white-space:pre-wrap;background:#f8fafc;padding:16px;border:1px solid #e5e7eb}</style>",
        "</head><body>",
        f"<h1>{html.escape(title)}</h1>",
        "<pre>",
        html.escape(markdown_text),
        "</pre>",
    ]
    for name, table in tables.items():
        body.append(f"<h2>{html.escape(name)}</h2>")
        body.append(table.to_html(index=False, escape=False, float_format=lambda value: f"{value:.4f}", classes="data"))
    body.append("</body></html>")
    return "\n".join(body)


def load_reference_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    test_metrics = pd.read_csv(PP_AMW6_TEST_METRICS) if PP_AMW6_TEST_METRICS.exists() else pd.DataFrame()
    bootstrap = pd.read_csv(PP_AMW6_BOOTSTRAP) if PP_AMW6_BOOTSTRAP.exists() else pd.DataFrame()
    return test_metrics, bootstrap


def main() -> None:
    ensure_dirs()
    lookup, lookup_coverage = build_artist_lookup()
    validation_reference = load_training_validation()

    all_predictions: list[pd.DataFrame] = []
    all_metrics: list[pd.DataFrame] = []
    targets: list[pd.DataFrame] = []
    for baseline_name, baseline_col in BASELINES.items():
        train = prepare_training_for_baseline(validation_reference, baseline_name)
        target = load_operational_target(lookup, train, baseline_name, baseline_col)
        target_with_candidates, candidate_cols = add_candidate_predictions(target, train, baseline_name)
        all_predictions.append(target_with_candidates)
        all_metrics.append(evaluate_candidates(target_with_candidates, candidate_cols, baseline_name))
        targets.append(target)

    predictions = pd.concat(all_predictions, ignore_index=True, sort=False)
    metrics = pd.concat(all_metrics, ignore_index=True, sort=False)
    coverage = coverage_table(targets, lookup_coverage)
    test_metrics, bootstrap = load_reference_tables()

    predictions.to_csv(OUT_DIR / "0604_predictions_with_amw6_candidates.csv", index=False)
    metrics.to_csv(OUT_DIR / "0604_candidate_metrics.csv", index=False)
    coverage.to_csv(OUT_DIR / "feature_coverage.csv", index=False)
    test_metrics.to_csv(OUT_DIR / "pp_amw6_historical_test_once_metrics.csv", index=False)
    bootstrap.to_csv(OUT_DIR / "pp_amw6_historical_bootstrap_summary.csv", index=False)

    key_scope = "0604_excluding_under_50_usd:service_primary_ppv8"
    key = metrics[metrics["scope"].eq(key_scope)].sort_values(["MAPE", "MdAPE", "p95_APE"]).copy()
    report_scope = "0604_excluding_under_50_usd:report_70_30"
    report_key = metrics[metrics["scope"].eq(report_scope)].sort_values(["MAPE", "MdAPE", "p95_APE"]).copy()
    all_numeric = metrics[metrics["scope"].str.startswith("0604_all_numeric")].copy()

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "OP-V01-CAL-07_warm_amw6_operational_revalidation",
        "operational_predictions": str(OP_PREDICTIONS.relative_to(REPO)),
        "operational_features": str(OP_FEATURES.relative_to(REPO)),
        "prediction_output": str((OUT_DIR / "0604_predictions_with_amw6_candidates.csv").relative_to(REPO)),
        "metrics_output": str((OUT_DIR / "0604_candidate_metrics.csv").relative_to(REPO)),
        "n_predictions": int(len(predictions)),
        "n_metrics": int(len(metrics)),
    }
    (OUT_DIR / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    conclusion = "- 0604 신규 라벨은 학습에 쓰지 않은 외부 확인용이다.\n"
    if not key.empty:
        baseline = key[key["candidate"].eq("service_primary_ppv8__baseline")]
        best = key.iloc[0]
        if not baseline.empty:
            b = baseline.iloc[0]
            conclusion += (
                f"- service_primary 기준 baseline MdAPE/MAPE/p95: {b['MdAPE']:.4f}/{b['MAPE']:.4f}/{b['p95_APE']:.4f}.\n"
                f"- service_primary 기준 0604 최상위 후보: {best['candidate']} "
                f"MdAPE/MAPE/p95 {best['MdAPE']:.4f}/{best['MAPE']:.4f}/{best['p95_APE']:.4f}.\n"
            )
    if not report_key.empty:
        best = report_key.iloc[0]
        conclusion += (
            f"- report_70_30 기준 0604 최상위 후보: {best['candidate']} "
            f"MdAPE/MAPE/p95 {best['MdAPE']:.4f}/{best['MAPE']:.4f}/{best['p95_APE']:.4f}.\n"
        )
    conclusion += "- 판단은 MdAPE 단독이 아니라 MAPE와 p95_APE 안정성을 함께 보고 내린다.\n"

    report = f"""# OP-V01-CAL-07 Warm 작가 메타 보정 운영 재검증 결과

## 1. 실행 요약

- 작성일: {summary['created_at']}
- 실험 목적: PP-AMW6 반복 재검증 후보를 v0.1 운영 0604 출력 기준으로 재확인
- 학습 데이터: 기존 Warm validation split
- 외부 확인 데이터: 0604 신규 라벨 Warm 행
- 0604 라벨 사용 방식: 보정 학습에는 사용하지 않고 평가에만 사용

## 2. 핵심 판단

{conclusion}

## 3. service_primary 기준 0604 후보 순위

{markdown_table(key[['scope', 'candidate', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'over_3x_n', 'under_1_3x_n']].head(12))}

## 4. report_70_30 기준 0604 후보 순위

{markdown_table(report_key[['scope', 'candidate', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'over_3x_n', 'under_1_3x_n']].head(12))}

## 5. 50달러 미만 포함 지표

{markdown_table(all_numeric[['scope', 'candidate', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE']].sort_values(['scope', 'MAPE', 'MdAPE']).head(16))}

## 6. 피처 커버리지

{markdown_table(coverage[coverage['feature'].isin(['artist_meta_birth_year', 'artist_meta_total_works', 'artist_meta_for_sale_works', 'artist_meta_followers', 'artist_exhibition_total_count', 'gallery_tier_raw_numeric', 'gallery_tier_validated_score'])].head(40))}

## 7. 산출물

- `outputs/0604_candidate_metrics.csv`
- `outputs/0604_predictions_with_amw6_candidates.csv`
- `outputs/feature_coverage.csv`
- `outputs/pp_amw6_historical_test_once_metrics.csv`
- `outputs/pp_amw6_historical_bootstrap_summary.csv`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(
        simple_html(
            "OP-V01-CAL-07 Warm 작가 메타 보정 운영 재검증 결과",
            report,
            {
                "service_primary 0604 후보": key.head(12),
                "report_70_30 0604 후보": report_key.head(12),
                "피처 커버리지": coverage.head(80),
            },
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
