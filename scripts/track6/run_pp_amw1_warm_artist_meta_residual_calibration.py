#!/usr/bin/env python3
"""Run PP-AMW1 Warm artist-meta residual calibration.

This experiment keeps the current strong Warm candidate fixed and learns only
small residual corrections from validation rows. It checks whether artist
metadata can improve Warm predictions as a post-model calibration signal.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
EXP_DIR = REPO / "experiments" / "track6" / "PP-AMW1_warm_artist_meta_residual_calibration"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

BASE_PREDICTIONS = REPO / "experiments/track6/PP-V8_warm_deployment_simplification/outputs/predictions.csv"
FEATURE_CANDIDATES = REPO / "data/track6/track6_feature_candidates_name_corrected.csv"

BASE_CANDIDATE = "compact_blend_mape_guarded"
SEED = 20260605

META_RAW = [
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_nationality_ko",
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_age",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
    "is_high_price_candidate",
]

META_NUMERIC = [
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_age",
    "artist_meta_career_stage",
    "artist_meta_total_works_log",
    "artist_meta_for_sale_works_log",
    "artist_meta_followers_log",
    "artist_meta_available_count",
    "artist_meta_completeness_score",
]

META_FLAGS = [
    "artist_meta_birth_year_missing",
    "artist_meta_total_works_missing",
    "artist_meta_for_sale_works_missing",
    "artist_meta_followers_missing",
    "artist_meta_for_sale_ratio_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_is_p1_flag",
    "artist_meta_has_international_flag",
    "is_high_price_candidate_flag",
]

META_CATEGORICAL = [
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_nationality_ko",
]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def boolish(values: pd.Series | None, index: pd.Index) -> pd.Series:
    if values is None:
        return pd.Series(0.0, index=index)
    return values.astype("string").str.lower().isin(["true", "1", "yes", "y"]).astype(float)


def load_artist_meta() -> pd.DataFrame:
    meta = pd.read_csv(
        FEATURE_CANDIDATES,
        low_memory=False,
        usecols=lambda col: col in {"track4_source_row_index", *META_RAW},
    ).rename(columns={"track4_source_row_index": "_track6_row_id"})
    meta["_track6_row_id"] = pd.to_numeric(meta["_track6_row_id"], errors="coerce")
    meta = meta.dropna(subset=["_track6_row_id"]).copy()
    meta["_track6_row_id"] = meta["_track6_row_id"].astype(int)
    meta = meta.drop_duplicates("_track6_row_id", keep="first")
    return engineer_artist_meta(meta)


def engineer_artist_meta(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
        "artist_meta_career_age",
        "artist_meta_career_stage",
    ]:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
        out[f"{col}_missing"] = out[col].isna().astype(float)
    out["artist_meta_total_works_log"] = np.log1p(out["artist_meta_total_works"].clip(lower=0))
    out["artist_meta_for_sale_works_log"] = np.log1p(out["artist_meta_for_sale_works"].clip(lower=0))
    out["artist_meta_followers_log"] = np.log1p(out["artist_meta_followers"].clip(lower=0))
    out["artist_meta_is_p1_flag"] = boolish(out.get("artist_meta_is_p1"), out.index)
    out["artist_meta_has_international_flag"] = boolish(out.get("artist_meta_has_international"), out.index)
    out["is_high_price_candidate_flag"] = boolish(out.get("is_high_price_candidate"), out.index)

    availability_cols = [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
        "artist_meta_career_stage",
    ]
    out["artist_meta_available_count"] = out[availability_cols].notna().sum(axis=1).astype(float)
    out["artist_meta_completeness_score"] = out["artist_meta_available_count"] / float(len(availability_cols))

    for col in META_CATEGORICAL:
        out[col] = out.get(col, pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__")
        out[col] = out[col].replace({"": "__MISSING__"})
    return out


def load_base_frame() -> pd.DataFrame:
    pred = pd.read_csv(BASE_PREDICTIONS, low_memory=False)
    pred = pred[pred["candidate"].eq(BASE_CANDIDATE)].copy()
    meta = load_artist_meta()
    merged = pred.merge(meta, on="_track6_row_id", how="left")
    merged["actual_price"] = pd.to_numeric(merged["actual_price"], errors="coerce")
    merged["actual_log"] = pd.to_numeric(merged["actual_log"], errors="coerce")
    merged["pred_log"] = pd.to_numeric(merged["pred_log"], errors="coerce")
    merged["pred_price"] = np.exp(merged["pred_log"])
    merged["residual_log"] = merged["actual_log"] - merged["pred_log"]
    return merged.dropna(subset=["actual_price", "actual_log", "pred_log"]).copy()


def metric_row(frame: pd.DataFrame, candidate: str, split: str, pred_col: str) -> dict[str, Any]:
    actual = frame["actual_price"].astype(float)
    pred = np.exp(frame[pred_col].astype(float))
    ape = ((pred - actual).abs() / actual).replace([np.inf, -np.inf], np.nan)
    ratio = (pred / actual).replace([np.inf, -np.inf], np.nan)
    valid = ape.notna() & ratio.notna() & actual.gt(0)
    log_error = frame.loc[valid, pred_col].astype(float) - frame.loc[valid, "actual_log"].astype(float)
    return {
        "experiment_id": "PP-AMW1",
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "n": int(valid.sum()),
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
        "MdAPE": float(ape.loc[valid].median()),
        "MAPE": float(ape.loc[valid].mean()),
        "p95_APE": float(ape.loc[valid].quantile(0.95)),
        "Within_30": float((ape.loc[valid] <= 0.30).mean()),
        "Within_50": float((ape.loc[valid] <= 0.50).mean()),
        "over_3x_n": int((ratio.loc[valid] > 3.0).sum()),
        "under_1_3x_n": int((ratio.loc[valid] < (1.0 / 3.0)).sum()),
        "median_ratio": float(ratio.loc[valid].median()),
    }


def add_equal_freq_bin(
    train_values: pd.Series,
    target_values: pd.Series,
    name: str,
    q: int = 3,
) -> pd.Series:
    clean = pd.to_numeric(train_values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if clean.nunique() < 2:
        return pd.Series(f"{name}_all", index=target_values.index, dtype="string")
    edges = np.unique(np.nanquantile(clean, np.linspace(0, 1, q + 1)))
    if len(edges) < 3:
        return pd.Series(f"{name}_all", index=target_values.index, dtype="string")
    edges[0] = -np.inf
    edges[-1] = np.inf
    labels = [f"{name}_q{i + 1}" for i in range(len(edges) - 1)]
    binned = pd.cut(pd.to_numeric(target_values, errors="coerce"), bins=edges, labels=labels, include_lowest=True)
    return binned.astype("string").fillna(f"{name}_missing")


def prepare_segments(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    val = out[out["split"].eq("validation")].copy()

    bin_specs = {
        "birth_year_bin": "artist_meta_birth_year",
        "total_works_bin": "artist_meta_total_works_log",
        "for_sale_bin": "artist_meta_for_sale_works_log",
        "followers_bin": "artist_meta_followers_log",
        "for_sale_ratio_bin": "artist_meta_for_sale_ratio",
        "career_age_bin": "artist_meta_career_age",
        "career_stage_bin": "artist_meta_career_stage",
        "meta_available_bin": "artist_meta_available_count",
        "meta_complete_bin": "artist_meta_completeness_score",
    }
    for new_col, raw_col in bin_specs.items():
        out[new_col] = add_equal_freq_bin(val[raw_col], out[raw_col], new_col)

    for raw_col in ["artist_meta_source", "artist_meta_nationality_ko"]:
        counts = val[raw_col].astype("string").fillna("__MISSING__").value_counts()
        top_values = set(counts[counts >= 20].index.tolist())
        out[f"{raw_col}_grouped"] = out[raw_col].astype("string").fillna("__MISSING__")
        out.loc[~out[f"{raw_col}_grouped"].isin(top_values), f"{raw_col}_grouped"] = "__OTHER__"

    out["p1_x_followers"] = out["artist_meta_is_p1_flag"].astype(str) + "__" + out["followers_bin"].astype(str)
    out["high_price_x_total_works"] = out["is_high_price_candidate_flag"].astype(str) + "__" + out["total_works_bin"].astype(str)
    out["source_x_meta_complete"] = out["artist_meta_source_grouped"].astype(str) + "__" + out["meta_complete_bin"].astype(str)
    out["career_x_followers"] = out["career_stage_bin"].astype(str) + "__" + out["followers_bin"].astype(str)
    out["birth_x_career"] = out["birth_year_bin"].astype(str) + "__" + out["career_stage_bin"].astype(str)
    return out


def build_correction(
    validation: pd.DataFrame,
    segment_col: str,
    min_rows: int,
    cap: float,
    shrink_k: float,
) -> tuple[dict[str, float], pd.DataFrame]:
    grouped = validation.groupby(segment_col, dropna=False)["residual_log"].agg(["count", "median"]).reset_index()
    grouped["raw_correction"] = grouped["median"].astype(float)
    grouped["shrink"] = grouped["count"] / (grouped["count"] + shrink_k)
    grouped["correction"] = (grouped["raw_correction"] * grouped["shrink"]).clip(lower=-cap, upper=cap)
    usable = grouped[grouped["count"].ge(min_rows)].copy()
    return dict(zip(usable[segment_col].astype(str), usable["correction"].astype(float), strict=False)), usable


def apply_segment_correction(
    frame: pd.DataFrame,
    segment_col: str,
    correction_map: dict[str, float],
) -> np.ndarray:
    corrections = frame[segment_col].astype(str).map(correction_map).fillna(0.0).to_numpy(dtype=float)
    return frame["pred_log"].to_numpy(dtype=float) + corrections


def residual_model_features() -> tuple[list[str], list[str]]:
    numeric = META_NUMERIC + META_FLAGS
    categorical = META_CATEGORICAL
    return numeric, categorical


def fit_residual_ridge(validation: pd.DataFrame, frame: pd.DataFrame, cap: float) -> np.ndarray:
    numeric, categorical = residual_model_features()
    train = validation.copy()
    apply_frame = frame.copy()
    usable_numeric = []
    for col in numeric:
        train[col] = pd.to_numeric(train.get(col), errors="coerce")
        apply_frame[col] = pd.to_numeric(apply_frame.get(col), errors="coerce")
        if train[col].notna().any():
            usable_numeric.append(col)
    for col in categorical:
        train[col] = train.get(col, pd.Series(index=train.index, dtype=object))
        apply_frame[col] = apply_frame.get(col, pd.Series(index=apply_frame.index, dtype=object))
        train[col] = train[col].where(train[col].notna(), "__MISSING__").astype(str)
        apply_frame[col] = apply_frame[col].where(apply_frame[col].notna(), "__MISSING__").astype(str)
    features = usable_numeric + categorical
    target = train["residual_log"].to_numpy(dtype=float)
    transformers = []
    if usable_numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), usable_numeric))
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=True)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=20)
    transformers.append(("cat", encoder, categorical))
    model = Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", Ridge(alpha=10.0, random_state=SEED)),
    ])
    model.fit(train[features], target)
    correction = np.asarray(model.predict(apply_frame[features]), dtype=float)
    correction = np.clip(correction, -cap, cap)
    return frame["pred_log"].to_numpy(dtype=float) + correction


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_결과 없음_"
    view = df.head(max_rows).copy() if max_rows else df.copy()
    formatted = view.copy()
    for col in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[col]):
            formatted[col] = formatted[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            formatted[col] = formatted[col].map(lambda x: "" if pd.isna(x) else str(x))
    lines = [
        "| " + " | ".join(formatted.columns.astype(str)) + " |",
        "| " + " | ".join("---" for _ in formatted.columns) + " |",
    ]
    for _, row in formatted.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("\n", " ") for col in formatted.columns) + " |")
    return "\n".join(lines)


def render_html(title: str, md_summary: str, tables: dict[str, pd.DataFrame]) -> str:
    body = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2933;line-height:1.55}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}th,td{border:1px solid #d8dee9;padding:7px 9px;text-align:right}"
        "th:first-child,td:first-child{text-align:left}th{background:#edf2f7}.summary{white-space:pre-wrap;background:#f8fafc;border-left:4px solid #2563eb;padding:12px}</style>",
        "</head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='summary'>{html.escape(md_summary)}</div>",
    ]
    for name, table in tables.items():
        body.append(f"<h2>{html.escape(name)}</h2>")
        body.append(table.to_html(index=False, escape=True, float_format=lambda x: f"{x:.4f}"))
    body.append("</body></html>")
    return "\n".join(body)


def main() -> None:
    ensure_dirs()
    frame = prepare_segments(load_base_frame())
    validation = frame[frame["split"].eq("validation")].copy()
    test = frame[frame["split"].eq("test")].copy()

    coverage_cols = META_NUMERIC + META_CATEGORICAL
    coverage = []
    for split_name, split_frame in [("validation", validation), ("test", test)]:
        row: dict[str, Any] = {"split": split_name, "n": len(split_frame)}
        for col in coverage_cols:
            row[f"{col}_coverage"] = float(split_frame[col].notna().mean())
        coverage.append(row)
    coverage_df = pd.DataFrame(coverage)

    segment_cols = [
        "birth_year_bin",
        "total_works_bin",
        "for_sale_bin",
        "followers_bin",
        "for_sale_ratio_bin",
        "career_age_bin",
        "career_stage_bin",
        "meta_available_bin",
        "meta_complete_bin",
        "artist_meta_source_grouped",
        "artist_meta_nationality_ko_grouped",
        "p1_x_followers",
        "high_price_x_total_works",
        "source_x_meta_complete",
        "career_x_followers",
        "birth_x_career",
    ]
    min_rows_values = [20, 30, 50]
    caps = [0.03, 0.05, 0.08, 0.10, 0.15]
    shrink_values = [20.0, 50.0]

    metrics_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []
    correction_tables: list[pd.DataFrame] = []

    for split_name, split_frame in [("validation", validation), ("test", test)]:
        split_frame = split_frame.copy()
        split_frame["baseline_pred_log"] = split_frame["pred_log"]
        metrics_rows.append(metric_row(split_frame, "baseline_ppv8_compact_blend_mape_guarded", split_name, "baseline_pred_log"))
        prediction_rows.append(split_frame.assign(candidate="baseline_ppv8_compact_blend_mape_guarded", corrected_pred_log=split_frame["baseline_pred_log"]))

    for segment_col in segment_cols:
        for min_rows in min_rows_values:
            for cap in caps:
                for shrink_k in shrink_values:
                    correction_map, detail = build_correction(validation, segment_col, min_rows, cap, shrink_k)
                    if detail.empty:
                        continue
                    candidate = f"seg_{segment_col}_min{min_rows}_cap{str(cap).replace('.', 'p')}_k{int(shrink_k)}"
                    detail = detail.copy()
                    detail["candidate"] = candidate
                    detail["segment_col"] = segment_col
                    detail["min_rows"] = min_rows
                    detail["cap"] = cap
                    detail["shrink_k"] = shrink_k
                    correction_tables.append(detail)
                    for split_name, split_frame in [("validation", validation), ("test", test)]:
                        tmp = split_frame.copy()
                        tmp["corrected_pred_log"] = apply_segment_correction(tmp, segment_col, correction_map)
                        metrics_rows.append(metric_row(tmp, candidate, split_name, "corrected_pred_log"))
                        prediction_rows.append(tmp.assign(candidate=candidate))

    for cap in [0.03, 0.05, 0.08, 0.10]:
        candidate = f"ridge_artist_meta_residual_cap{str(cap).replace('.', 'p')}"
        for split_name, split_frame in [("validation", validation), ("test", test)]:
            tmp = split_frame.copy()
            tmp["corrected_pred_log"] = fit_residual_ridge(validation, tmp, cap=cap)
            metrics_rows.append(metric_row(tmp, candidate, split_name, "corrected_pred_log"))
            prediction_rows.append(tmp.assign(candidate=candidate))

    metrics_df = pd.DataFrame(metrics_rows)
    corrections_df = pd.concat(correction_tables, ignore_index=True) if correction_tables else pd.DataFrame()
    predictions_df = pd.concat(prediction_rows, ignore_index=True)
    predictions_df["corrected_pred_price"] = np.exp(predictions_df["corrected_pred_log"].astype(float))
    predictions_df["corrected_ape"] = (predictions_df["corrected_pred_price"] - predictions_df["actual_price"]).abs() / predictions_df["actual_price"]

    baseline = metrics_df[metrics_df["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")].set_index("split")
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        metrics_df[f"delta_vs_baseline_{metric}"] = metrics_df.apply(
            lambda row: row[metric] - baseline.loc[row["split"], metric],
            axis=1,
        )

    validation_metrics = metrics_df[metrics_df["split"].eq("validation")].copy()
    validation_baseline = baseline.loc["validation"]
    guarded = validation_metrics[
        (validation_metrics["MdAPE"] <= validation_baseline["MdAPE"] + 0.003)
        & (validation_metrics["p95_APE"] <= validation_baseline["p95_APE"] + 0.005)
    ].copy()
    if guarded.empty:
        guarded = validation_metrics.copy()
    selected_candidates = guarded.sort_values(["MAPE", "MdAPE", "p95_APE"]).head(20)["candidate"].tolist()
    selected_metrics = metrics_df[metrics_df["candidate"].isin(selected_candidates + ["baseline_ppv8_compact_blend_mape_guarded"])].copy()

    test_top = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(25).copy()
    selected_test = selected_metrics[selected_metrics["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).copy()

    metrics_df.to_csv(OUT_DIR / "metrics.csv", index=False)
    selected_metrics.to_csv(OUT_DIR / "selected_candidate_metrics.csv", index=False)
    test_top.to_csv(OUT_DIR / "test_top_candidates.csv", index=False)
    coverage_df.to_csv(OUT_DIR / "artist_meta_coverage.csv", index=False)
    corrections_df.to_csv(OUT_DIR / "correction_maps.csv", index=False)
    predictions_df[[
        "candidate",
        "split",
        "_track6_row_id",
        "actual_log",
        "pred_log",
        "corrected_pred_log",
        "actual_price",
        "pred_price",
        "corrected_pred_price",
        "corrected_ape",
        "artist_meta_source",
        "artist_meta_nationality_ko",
        "artist_meta_available_count",
        "artist_meta_followers_log",
        "artist_meta_total_works_log",
        "is_high_price_candidate_flag",
    ]].to_csv(OUT_DIR / "predictions.csv", index=False)

    baseline_test = baseline.loc["test"]
    best_test = test_top.iloc[0]
    best_selected_test = selected_test.iloc[0]
    summary = "\n".join([
        "- 기준 후보: PP-V8 compact_blend_mape_guarded",
        "- 방식: validation 잔차 중앙값 또는 Ridge 잔차 모델로 작가 메타 기반 보정값 생성",
        "- test 정답은 보정값 생성에 사용하지 않음",
        "",
        "핵심 결과:",
        f"- 기준 test MdAPE {baseline_test['MdAPE']:.4f}, MAPE {baseline_test['MAPE']:.4f}, p95_APE {baseline_test['p95_APE']:.4f}",
        f"- 전체 후보 중 test MAPE 최선: {best_test['candidate']} / MdAPE {best_test['MdAPE']:.4f}, MAPE {best_test['MAPE']:.4f}, p95_APE {best_test['p95_APE']:.4f}",
        f"- validation 선택 후보 중 test 최선: {best_selected_test['candidate']} / MdAPE {best_selected_test['MdAPE']:.4f}, MAPE {best_selected_test['MAPE']:.4f}, p95_APE {best_selected_test['p95_APE']:.4f}",
        "",
        "판단:",
        "- 작가 메타 기반 보정은 일부 구간에서 개선 신호가 있는지 확인한다.",
        "- validation에서 선택한 후보가 test에서도 개선되면 후속 반복 split 검증 대상으로 둔다.",
        "- 개선이 test에서만 나타나거나 p95가 악화되면 운영 후보가 아니라 분석 근거로만 둔다.",
    ])

    report = f"""# PP-AMW1 Warm 작가 메타 기반 잔차 보정 실험 결과

## 1. 실행 요약

{summary}

## 2. 작가 메타 커버리지

{dataframe_to_markdown(coverage_df)}

## 3. validation 선택 후보의 validation/test 지표

{dataframe_to_markdown(selected_metrics.sort_values(["candidate", "split"]))}

## 4. test 기준 상위 후보

{dataframe_to_markdown(test_top, max_rows=25)}

## 5. 산출물

- `outputs/metrics.csv`
- `outputs/selected_candidate_metrics.csv`
- `outputs/test_top_candidates.csv`
- `outputs/artist_meta_coverage.csv`
- `outputs/correction_maps.csv`
- `outputs/predictions.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(
        render_html(
            "PP-AMW1 Warm 작가 메타 기반 잔차 보정 실험 결과",
            summary,
            {
                "작가 메타 커버리지": coverage_df,
                "validation 선택 후보의 validation/test 지표": selected_metrics.sort_values(["candidate", "split"]),
                "test 기준 상위 후보": test_top,
            },
        ),
        encoding="utf-8",
    )
    manifest = {
        "experiment_id": "PP-AMW1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_predictions": str(BASE_PREDICTIONS.relative_to(REPO)),
        "base_candidate": BASE_CANDIDATE,
        "artist_meta_source": str(FEATURE_CANDIDATES.relative_to(REPO)),
        "method": "validation residual calibration using artist metadata segments and ridge residual model",
        "outputs": str(OUT_DIR.relative_to(REPO)),
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
