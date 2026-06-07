#!/usr/bin/env python3
"""Run PP-H29 Warm search-feature residual calibration.

This experiment checks whether the operational artist-search features collected
in PP-H11 can still improve the already-strong Warm deployment candidates.
Correction values are fitted only on the Warm validation split and then applied
to Warm validation/test predictions.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED  # noqa: E402


EXP_ID = "PP-H29"
EXP_SLUG = "PP-H29_warm_search_feature_calibration"
TITLE = "Warm 검색 피처 기반 잔차 보정 검증"

PRED_PATH = REPO / "experiments" / "track6" / "PP-V8_warm_deployment_simplification" / "outputs" / "predictions.csv"
SEARCH_SNAPSHOT_PATH = REPO / "data" / "track6" / "external_search" / "operational" / "track6_artist_search_operational_snapshot_latest.csv"
SEARCH_STANDARDIZED_PATH = REPO / "data" / "track6" / "external_search" / "operational" / "track6_artist_search_operational_standardized_latest.csv"
SPLIT_PATHS = {
    "validation": REPO / "data" / "track6_split" / "track6_val_warm.csv",
    "test": REPO / "data" / "track6_split" / "track6_test_warm.csv",
}

BASE_CANDIDATES = [
    ("v8_single_mdape", "deployment_single_mdape", "V8 단일 MdAPE 후보"),
    ("v8_compact_mdape", "compact_blend_mdape", "V8 compact blend MdAPE 후보"),
    ("v8_compact_mape", "compact_blend_mape_guarded", "V8 compact blend MAPE 방어 후보"),
]

FEATURE_SPECS = [
    ("search_quality_score", "quality", "검색 품질 점수"),
    ("search_name_match_ratio", "name_match", "작가명 일치 비중"),
    ("search_homonym_risk_ratio", "homonym", "동명이인 위험 비중"),
    ("source_group_gallery_museum_ratio", "gallery", "갤러리/미술관 출처 비중"),
    ("source_group_news_ratio", "news", "뉴스 출처 비중"),
    ("source_group_social_blog_ratio", "social_blog", "블로그/소셜 출처 비중"),
    ("source_group_market_ratio", "market", "시장/경매 출처 비중"),
    ("provider_coverage_count", "provider_cov", "검색 제공자 커버리지 수"),
]

CAPS = [0.05, 0.10, 0.15]
MIN_SEGMENT_ROWS = 18


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = re.sub(r"_[A-Z]+$", "", value).strip()
    return re.sub(r"\s+", " ", value)


def cap_label(cap: float) -> str:
    return str(cap).replace(".", "p")


def metrics(actual_log: pd.Series, pred_log: pd.Series) -> dict[str, float]:
    actual_log = pd.Series(actual_log, dtype=float)
    pred_log = pd.Series(pred_log, dtype=float)
    actual = np.exp(actual_log)
    pred = np.exp(pred_log)
    ape = np.abs(actual - pred) / np.maximum(actual, 1e-9)
    return {
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def load_warm_predictions() -> pd.DataFrame:
    preds = pd.read_csv(PRED_PATH)
    wanted = {candidate for _label, candidate, _note in BASE_CANDIDATES}
    preds = preds[(preds["scope"] == "warm") & (preds["candidate"].isin(wanted)) & (preds["split"].isin(["validation", "test"]))].copy()
    if preds.empty:
        raise RuntimeError(f"No Warm predictions found in {PRED_PATH}")

    split_frames = []
    for split, path in SPLIT_PATHS.items():
        frame = pd.read_csv(path, low_memory=False)
        split_frames.append(frame[["_track6_row_id", "artist_name_ko"]].assign(split=split))
    names = pd.concat(split_frames, ignore_index=True)
    names["artist_search_name"] = names["artist_name_ko"].map(clean_artist_name)
    preds = preds.merge(names, on=["_track6_row_id", "split"], how="left")
    return preds


def load_search_snapshot() -> pd.DataFrame:
    if not SEARCH_SNAPSHOT_PATH.exists():
        raise RuntimeError(f"Missing search snapshot: {SEARCH_SNAPSHOT_PATH}")
    snapshot = pd.read_csv(SEARCH_SNAPSHOT_PATH, low_memory=False)
    snapshot["artist_search_name"] = snapshot["artist_search_name"].map(clean_artist_name)
    if SEARCH_STANDARDIZED_PATH.exists():
        standard = pd.read_csv(SEARCH_STANDARDIZED_PATH, low_memory=False)
        if {"artist_search_name", "source_group"}.issubset(standard.columns):
            standard["artist_search_name"] = standard["artist_search_name"].map(clean_artist_name)
            source_counts = standard.groupby(["artist_search_name", "source_group"], dropna=False).size().unstack(fill_value=0)
            source_total = source_counts.sum(axis=1).replace(0, np.nan)
            for source_group in ["gallery_museum", "news", "social_blog", "market"]:
                if source_group not in source_counts.columns:
                    source_counts[source_group] = 0
                source_counts[f"source_group_{source_group}_ratio"] = source_counts[source_group] / source_total
            source_features = source_counts[[f"source_group_{group}_ratio" for group in ["gallery_museum", "news", "social_blog", "market"]]].reset_index()
            snapshot = snapshot.drop(columns=[col for col in source_features.columns if col != "artist_search_name" and col in snapshot.columns], errors="ignore")
            snapshot = snapshot.merge(source_features, on="artist_search_name", how="left")
    needed_cols = ["artist_search_name"] + [feature for feature, _short, _label in FEATURE_SPECS]
    for col in needed_cols:
        if col not in snapshot.columns:
            snapshot[col] = np.nan
    return snapshot[needed_cols].drop_duplicates("artist_search_name", keep="last")


def attach_search_features(preds: pd.DataFrame, snapshot: pd.DataFrame) -> pd.DataFrame:
    frame = preds.merge(snapshot, on="artist_search_name", how="left")
    frame["has_search_feature"] = frame["search_quality_score"].notna()
    for feature, _short, _label in FEATURE_SPECS:
        frame[feature] = pd.to_numeric(frame[feature], errors="coerce")
    return frame


def build_segments(validation: pd.DataFrame, frame: pd.DataFrame, feature: str) -> tuple[pd.Series, dict[str, Any]]:
    valid = validation[validation["has_search_feature"] & validation[feature].notna()].copy()
    info: dict[str, Any] = {
        "feature": feature,
        "valid_validation_rows": int(len(valid)),
        "mode": "quantile_33_66",
    }
    if valid[feature].nunique(dropna=True) < 3:
        threshold = float(valid[feature].median()) if len(valid) else 0.0
        info.update({"mode": "median_binary", "threshold": threshold})

        def assign_binary(row: pd.Series) -> str:
            if not bool(row["has_search_feature"]) or pd.isna(row[feature]):
                return "no_search"
            return "high" if float(row[feature]) >= threshold else "low"

        return frame.apply(assign_binary, axis=1), info

    q33, q66 = valid[feature].quantile([0.33, 0.66]).tolist()
    if not np.isfinite(q33) or not np.isfinite(q66) or q33 == q66:
        threshold = float(valid[feature].median())
        info.update({"mode": "median_binary", "threshold": threshold})

        def assign_fallback(row: pd.Series) -> str:
            if not bool(row["has_search_feature"]) or pd.isna(row[feature]):
                return "no_search"
            return "high" if float(row[feature]) >= threshold else "low"

        return frame.apply(assign_fallback, axis=1), info

    info.update({"q33": float(q33), "q66": float(q66)})

    def assign_quantile(row: pd.Series) -> str:
        if not bool(row["has_search_feature"]) or pd.isna(row[feature]):
            return "no_search"
        value = float(row[feature])
        if value <= q33:
            return "low"
        if value <= q66:
            return "mid"
        return "high"

    return frame.apply(assign_quantile, axis=1), info


def fit_corrections(validation: pd.DataFrame, cap: float) -> pd.DataFrame:
    rows = []
    for segment, group in validation.groupby("search_segment", dropna=False):
        count = int(len(group))
        raw = float(group["residual_log"].median()) if count >= MIN_SEGMENT_ROWS and segment != "no_search" else 0.0
        rows.append({
            "search_segment": segment,
            "segment_row_count": count,
            "raw_correction": raw,
            "correction": float(np.clip(raw, -cap, cap)),
            "cap": cap,
            "min_segment_rows": MIN_SEGMENT_ROWS,
        })
    return pd.DataFrame(rows)


def run_candidates(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    prediction_frames = []
    correction_frames = []
    segment_info_rows = []
    base_note = {candidate: note for _label, candidate, note in BASE_CANDIDATES}
    base_label = {candidate: label for label, candidate, _note in BASE_CANDIDATES}

    for base_candidate in [candidate for _label, candidate, _note in BASE_CANDIDATES]:
        base = frame[frame["candidate"] == base_candidate].copy()
        for split, group in base.groupby("split"):
            metric_rows.append({
                "experiment_id": EXP_ID,
                "candidate": f"baseline__{base_label[base_candidate]}",
                "base_candidate": base_candidate,
                "feature": "none",
                "split": split,
                "policy": "baseline_from_pp_v8",
                "cap": 0.0,
                "note": base_note[base_candidate],
                **metrics(group["actual_log"], group["pred_log"]),
            })

        for feature, feature_short, feature_label in FEATURE_SPECS:
            validation = base[base["split"] == "validation"].copy()
            segments, segment_info = build_segments(validation, base, feature)
            base = base.assign(search_segment=segments.values)
            validation = base[base["split"] == "validation"].copy()
            segment_info_rows.append({
                "base_candidate": base_candidate,
                "feature": feature,
                "feature_label": feature_label,
                **segment_info,
            })

            for cap in CAPS:
                correction_map = fit_corrections(validation, cap)
                candidate_name = f"h29_{base_label[base_candidate]}_{feature_short}_median_cap{cap_label(cap)}"
                corrected = base.merge(correction_map[["search_segment", "correction"]], on="search_segment", how="left")
                corrected["correction"] = corrected["correction"].fillna(0.0)
                corrected["corrected_pred_log"] = corrected["pred_log"] + corrected["correction"]
                corrected["corrected_pred_price"] = np.exp(corrected["corrected_pred_log"])
                corrected["corrected_ape"] = np.abs(np.exp(corrected["actual_log"]) - corrected["corrected_pred_price"]) / np.maximum(np.exp(corrected["actual_log"]), 1e-9)

                for split, group in corrected.groupby("split"):
                    metric_rows.append({
                        "experiment_id": EXP_ID,
                        "candidate": candidate_name,
                        "base_candidate": base_candidate,
                        "feature": feature,
                        "feature_label": feature_label,
                        "split": split,
                        "policy": "validation_segment_median_residual_correction",
                        "cap": cap,
                        "note": f"{feature_label} 구간별 Warm validation 잔차 중앙값 보정",
                        **metrics(group["actual_log"], group["corrected_pred_log"]),
                    })

                prediction_frames.append(corrected[[
                    "experiment_id",
                    "candidate",
                    "scope",
                    "split",
                    "_track6_row_id",
                    "artist_search_name",
                    "actual_log",
                    "pred_log",
                    "corrected_pred_log",
                    "actual_price",
                    "pred_price",
                    "corrected_pred_price",
                    "residual_log",
                    "ape",
                    "corrected_ape",
                    "has_search_feature",
                    "search_segment",
                    "correction",
                ]].assign(experiment_id=EXP_ID, candidate=candidate_name))
                correction_frames.append(correction_map.assign(
                    candidate=candidate_name,
                    base_candidate=base_candidate,
                    feature=feature,
                    feature_label=feature_label,
                ))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    corrections_df = pd.concat(correction_frames, ignore_index=True) if correction_frames else pd.DataFrame()
    segment_info_df = pd.DataFrame(segment_info_rows)
    return metrics_df, predictions_df, corrections_df, segment_info_df


def coverage_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, group in frame.groupby("split"):
        rows.append({
            "split": split,
            "row_n": int(len(group)),
            "unique_artist_n": int(group["artist_search_name"].nunique()),
            "search_covered_row_n": int(group["has_search_feature"].sum()),
            "search_covered_row_rate": float(group["has_search_feature"].mean()),
            "search_covered_artist_n": int(group.loc[group["has_search_feature"], "artist_search_name"].nunique()),
        })
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    copy = df.copy()
    for col in copy.columns:
        if pd.api.types.is_float_dtype(copy[col]):
            copy[col] = copy[col].map(lambda value: "" if pd.isna(value) else f"{value:.6f}")
        else:
            copy[col] = copy[col].map(lambda value: "" if pd.isna(value) else str(value))
    headers = [str(col) for col in copy.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in copy.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def render_report(metrics_df: pd.DataFrame, coverage_df: pd.DataFrame, corrections_df: pd.DataFrame, segment_info_df: pd.DataFrame) -> tuple[str, str]:
    top_validation = metrics_df[metrics_df["split"] == "validation"].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(12)
    top_test = metrics_df[metrics_df["split"] == "test"].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(12)
    base_test = metrics_df[(metrics_df["split"] == "test") & (metrics_df["policy"] == "baseline_from_pp_v8")].sort_values("MdAPE")
    best_test = top_test.iloc[0].to_dict() if not top_test.empty else {}
    best_val = top_validation.iloc[0].to_dict() if not top_validation.empty else {}

    md = f"""# {TITLE}

- 실험 ID: `{EXP_ID}`
- 실행 시각: {datetime.now().isoformat(timespec="seconds")}
- 목적: Warm 최종 후보 예측값에 외부 검색 피처별 잔차 보정을 적용했을 때, 이미 강한 Warm 모델도 추가 개선 여지가 있는지 확인한다.
- 보정 학습 기준: Warm validation split의 `actual_log - pred_log` 중앙값
- 적용 기준: validation에서 만든 보정값을 validation/test에 동일 적용
- 보정 강도: log 가격 기준 `±0.05`, `±0.10`, `±0.15`

## 검색 피처 커버리지

{markdown_table(coverage_df)}

## 기준 후보 test 성능

{markdown_table(base_test)}

## validation 상위 후보

{markdown_table(top_validation)}

## test 상위 후보

{markdown_table(top_test)}

## 해석

- validation 최상위 후보: `{best_val.get("candidate", "")}` / MdAPE `{best_val.get("MdAPE", np.nan):.6f}` / MAPE `{best_val.get("MAPE", np.nan):.6f}`
- test 최상위 후보: `{best_test.get("candidate", "")}` / MdAPE `{best_test.get("MdAPE", np.nan):.6f}` / MAPE `{best_test.get("MAPE", np.nan):.6f}`
- 이 실험은 검색 피처를 모델 학습 피처로 직접 투입하는 것이 아니라, Warm 예측값이 남긴 오차를 검색 피처 구간별로 보정하는 후처리 실험이다.
- 따라서 효과가 있으면 “Warm 모델의 기본 가격 구조는 유지하되, 외부 인지도/출처 성격에 따라 반복되는 잔차만 작게 조정할 수 있다”는 근거가 된다.
- 반대로 test 개선이 없거나 validation만 좋아지면, Warm에서는 검색 피처가 이미 작가/크기/작품 이력 피처에 상당 부분 흡수됐거나 평가셋 커버리지가 아직 부족하다는 의미다.

## 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/correction_maps.csv`
- `outputs/segment_info.csv`
- `reports/result_report.html`
"""

    sections = [
        ("검색 피처 커버리지", coverage_df),
        ("기준 후보 test 성능", base_test),
        ("validation 상위 후보", top_validation),
        ("test 상위 후보", top_test),
        ("보정 구간 정보", segment_info_df.head(40)),
        ("보정값 샘플", corrections_df.head(80)),
    ]
    body = "\n".join(
        f"<section><h2>{html.escape(title)}</h2>{df.to_html(index=False, escape=True)}</section>"
        for title, df in sections
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ margin-bottom: 8px; }}
    h2 {{ margin-top: 32px; border-bottom: 1px solid #d8dee9; padding-bottom: 8px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin-top: 12px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 7px 8px; text-align: left; }}
    th {{ background: #eef2f7; }}
    .note {{ background: #f8fafc; border: 1px solid #d8dee9; padding: 14px 16px; border-radius: 6px; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{html.escape(TITLE)}</h1>
  <div class="note">
    <p><strong>목적:</strong> Warm 최종 후보 예측값에 외부 검색 피처별 잔차 보정을 얹어 추가 개선 가능성을 검증한다.</p>
    <p><strong>핵심 원칙:</strong> 보정값은 validation에서만 만들고 test에는 그대로 적용한다.</p>
  </div>
  {body}
</body>
</html>
"""
    return md, html_doc


def main() -> None:
    np.random.seed(SEED)
    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for subdir in ["outputs", "reports", "logs", "artifacts"]:
        (exp_dir / subdir).mkdir(parents=True, exist_ok=True)

    preds = load_warm_predictions()
    snapshot = load_search_snapshot()
    frame = attach_search_features(preds, snapshot)
    coverage_df = coverage_table(frame.drop_duplicates(["split", "_track6_row_id"]))
    metrics_df, predictions_df, corrections_df, segment_info_df = run_candidates(frame)

    metrics_df = metrics_df.sort_values(["split", "MdAPE", "MAPE", "p95_APE", "candidate"]).reset_index(drop=True)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    predictions_df.to_csv(exp_dir / "outputs" / "candidate_predictions.csv", index=False)
    corrections_df.to_csv(exp_dir / "outputs" / "correction_maps.csv", index=False)
    segment_info_df.to_csv(exp_dir / "outputs" / "segment_info.csv", index=False)
    coverage_df.to_csv(exp_dir / "outputs" / "coverage.csv", index=False)

    md, html_doc = render_report(metrics_df, coverage_df, corrections_df, segment_info_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    (exp_dir / "artifacts" / "input_paths.json").write_text(json.dumps({
        "prediction_path": str(PRED_PATH.relative_to(REPO)),
        "search_snapshot_path": str(SEARCH_SNAPSHOT_PATH.relative_to(REPO)),
        "search_standardized_path": str(SEARCH_STANDARDIZED_PATH.relative_to(REPO)),
        "split_paths": {split: str(path.relative_to(REPO)) for split, path in SPLIT_PATHS.items()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    best_test = metrics_df[metrics_df["split"] == "test"].sort_values(["MdAPE", "MAPE"]).head(5)
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(exp_dir.relative_to(REPO)),
        "best_test": best_test[["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
