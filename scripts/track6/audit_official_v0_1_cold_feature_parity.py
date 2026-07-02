#!/usr/bin/env python3
"""Audit Cold official v0.1 service-feature parity against fixed-test features."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sqlite3
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
SCRIPT_DIR = REPO / "scripts" / "track6"
for path in [SRC, SCRIPT_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

os.environ.setdefault("MPLCONFIGDIR", str(REPO / ".cache" / "matplotlib"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")
warnings.filterwarnings("ignore", message="X does not have valid feature names")

from visionai.price_engine.api.official_v0_1_report_adapters import ReportModelProxyAdapter  # noqa: E402
from visionai.price_engine.api.official_v0_1_schemas import (  # noqa: E402
    ArtistInput,
    ArtworkInput,
    Dimensions,
    MediumInput,
    PriceEstimateRequest,
)

import run_pp_y_cold_combination_experiments as ycombo  # noqa: E402


FEATURE_SCHEMA = REPO / "models" / "track6" / "cold_v03_research_upstream_refreeze_candidate" / "artifacts" / "feature_schema.json"
SPLIT_TEST = REPO / "data" / "track6_split" / "track6_test_cold.csv"
OFFICIAL_DB = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
EXTERNAL_CACHE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_artist_external_feature_cache.csv"
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_cold_feature_parity_audit"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_cold_feature_parity_audit.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_cold_feature_parity_audit.md"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def metric_triplet(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(actual_price)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(np.asarray(pred_log, dtype=float) - actual_log)))),
    }


def feature_group(col: str) -> str:
    if col in {
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "log_area",
        "aspect_ratio",
        "has_depth",
        "is_3d_candidate",
        "medium_category",
        "support_category",
        "size_bucket",
        "support_size_bucket",
    }:
        return "artwork_base"
    if col.startswith("artist_meta_") or col in {"is_high_price_candidate_flag"}:
        return "artist_meta"
    if col.startswith("search_"):
        return "search"
    if (
        col.startswith("artist_exhibition_")
        or col.startswith("gallery_")
        or col.startswith("exhibition_")
    ):
        return "exhibition_gallery"
    return "generated_or_other"


def request_from_row(row: pd.Series) -> PriceEstimateRequest:
    artist_key = str(row.get("artist_key") or "").strip()
    return PriceEstimateRequest(
        artwork=ArtworkInput(
            title=str(row.get("title_raw") or "Untitled"),
            artist=ArtistInput(
                artist_key=artist_key,
                selected_artist_key=artist_key,
                name_ko=str(row.get("artist_name_ko") or "").strip(),
            ),
            year=None,
            category="Sculpture" if bool(row.get("is_3d_candidate")) else "Painting",
            dimensions=Dimensions(
                width_cm=safe_float(row.get("width_cm"), 1.0),
                height_cm=safe_float(row.get("height_cm"), 1.0),
                depth_cm=max(safe_float(row.get("depth_cm"), 0.0), 0.0),
            ),
            medium=MediumInput(
                medium_category=str(row.get("medium_category") or "unknown"),
                support_category=str(row.get("support_category") or "unknown"),
            ),
            artwork_url=str(row.get("artwork_url") or "") or None,
            source_artwork_id=str(row.get("source_artwork_id") or "") or None,
        )
    )


def load_exact_fixed_test(features: list[str]) -> pd.DataFrame:
    search_df = ycombo.load_search_df()
    _, _, test = ycombo.load_cold_full(features, search_df)
    test = ycombo.normalize_frame(test, features)
    return test.drop_duplicates("_track6_row_id", keep="first").copy()


def build_service_feature_frame(
    adapter: ReportModelProxyAdapter,
    source_rows: pd.DataFrame,
    features: list[str],
    max_rows: int | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    statuses: list[dict[str, Any]] = []
    rows = source_rows.copy()
    if max_rows is not None:
        rows = rows.head(max_rows)
    for idx, row in rows.iterrows():
        if idx and idx % 250 == 0:
            print(f"built service features: {idx}/{len(rows)}", flush=True)
        request = request_from_row(row)
        artist_key = str(row.get("artist_key") or "").strip()
        frame, search_status, external_status = adapter._build_cold_refreeze_feature_frame(request, artist_key)
        frame = frame.reindex(columns=features)
        frame.insert(0, "_track6_row_id", int(row["_track6_row_id"]))
        frames.append(frame)
        statuses.append({
            "_track6_row_id": int(row["_track6_row_id"]),
            "artist_key": artist_key,
            "cold_feature_store_hit": bool(external_status.get("cold_feature_store_hit")),
            "search_found": bool(search_status.get("found")),
            "search_lookup_basis": search_status.get("lookup_basis"),
            "external_found": bool(external_status.get("found")),
            "external_lookup_basis": external_status.get("lookup_basis"),
            "external_row_count": int(external_status.get("row_count") or 0),
            **{f"external_{k}": v for k, v in (external_status.get("feature_preview") or {}).items()},
        })
    if not frames:
        raise RuntimeError("No service rows generated.")
    return pd.concat(frames, ignore_index=True), pd.DataFrame(statuses)


def compare_features(exact: pd.DataFrame, service: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    numeric_cols, categorical_cols = ycombo.split_types(features)
    rows: list[dict[str, Any]] = []
    merged = exact[["_track6_row_id", *features]].merge(
        service[["_track6_row_id", *features]],
        on="_track6_row_id",
        suffixes=("_exact", "_service"),
        how="inner",
    )
    for col in features:
        group = feature_group(col)
        exact_col = f"{col}_exact"
        service_col = f"{col}_service"
        if col in numeric_cols:
            a = pd.to_numeric(merged[exact_col], errors="coerce")
            b = pd.to_numeric(merged[service_col], errors="coerce")
            both_nan = a.isna() & b.isna()
            diff = (a - b).abs()
            match = both_nan | diff.le(1e-9)
            finite_diff = diff[~both_nan].dropna()
            rows.append({
                "feature": col,
                "group": group,
                "type": "numeric",
                "match_rate": float(match.mean()),
                "mean_abs_diff": float(finite_diff.mean()) if len(finite_diff) else 0.0,
                "p95_abs_diff": float(finite_diff.quantile(0.95)) if len(finite_diff) else 0.0,
                "max_abs_diff": float(finite_diff.max()) if len(finite_diff) else 0.0,
                "exact_non_missing_rate": float(a.notna().mean()),
                "service_non_missing_rate": float(b.notna().mean()),
            })
        else:
            a = merged[exact_col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
            b = merged[service_col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
            match = a.eq(b)
            rows.append({
                "feature": col,
                "group": group,
                "type": "categorical",
                "match_rate": float(match.mean()),
                "mean_abs_diff": None,
                "p95_abs_diff": None,
                "max_abs_diff": None,
                "exact_non_missing_rate": float(a.ne("__MISSING__").mean()),
                "service_non_missing_rate": float(b.ne("__MISSING__").mean()),
            })
    feature_report = pd.DataFrame(rows).sort_values(["group", "match_rate", "feature"]).reset_index(drop=True)
    group_report = (
        feature_report
        .groupby(["group", "type"], as_index=False)
        .agg(
            feature_count=("feature", "count"),
            mean_match_rate=("match_rate", "mean"),
            min_match_rate=("match_rate", "min"),
            mean_exact_non_missing_rate=("exact_non_missing_rate", "mean"),
            mean_service_non_missing_rate=("service_non_missing_rate", "mean"),
        )
        .sort_values(["group", "type"])
    )
    return feature_report, group_report


def predict_bundle(adapter: ReportModelProxyAdapter, frame: pd.DataFrame, artist_keys: pd.Series) -> pd.DataFrame:
    y2_q10 = np.asarray(adapter.cold_y2_models["q10"].predict(frame), dtype=float)
    y2_q50 = np.asarray(adapter.cold_y2_models["q50"].predict(frame), dtype=float)
    y2_q90 = np.asarray(adapter.cold_y2_models["q90"].predict(frame), dtype=float)
    q40 = np.asarray(adapter.cold_qr1_q40_model.predict(frame), dtype=float)
    qwidth = np.maximum(y2_q90 - y2_q10, 0.0)
    representative = np.asarray([
        adapter._apply_cold_y16_segment_correction(float(q50), float(width))
        for q50, width in zip(y2_q50, qwidth)
    ], dtype=float)
    v03_input = pd.DataFrame({
        "y18_qwidth_pred_log": representative,
        "lgb_q40_pred_log": q40,
        "quantile_width_log": qwidth,
        "artist_key": artist_keys.astype(str).to_numpy(),
    })
    final = adapter.cold_v03.apply(v03_input, params=adapter.cold_v03_params, lookup=adapter.cold_v03_lookup)
    return pd.DataFrame({
        "_track6_row_id": frame["_track6_row_id"].to_numpy(dtype=int),
        "q10_log": y2_q10,
        "q50_log": y2_q50,
        "q90_log": y2_q90,
        "q40_log": q40,
        "quantile_width_log": qwidth,
        "representative_log": representative,
        "final_log": final["cold_defense_pred_log"].to_numpy(dtype=float),
        "search_delta_log": final["search_delta_applied"].to_numpy(dtype=float),
        "search_covered": final["search_covered"].astype(bool).to_numpy(),
    })


def summarize_prediction_delta(exact_pred: pd.DataFrame, service_pred: pd.DataFrame) -> dict[str, Any]:
    merged = exact_pred.merge(service_pred, on="_track6_row_id", suffixes=("_exact", "_service"), how="inner")
    out: dict[str, Any] = {"n": int(len(merged))}
    for col in ["q50_log", "q40_log", "quantile_width_log", "representative_log", "final_log"]:
        diff = (merged[f"{col}_service"] - merged[f"{col}_exact"]).abs()
        out[col] = {
            "mean_abs_diff": float(diff.mean()),
            "p95_abs_diff": float(diff.quantile(0.95)),
            "max_abs_diff": float(diff.max()),
            "allclose_1e_9": bool(np.allclose(
                merged[f"{col}_service"].to_numpy(dtype=float),
                merged[f"{col}_exact"].to_numpy(dtype=float),
                rtol=0.0,
                atol=1e-9,
                equal_nan=True,
            )),
        }
    return out


def status_positive_rate(statuses: pd.DataFrame, col: str) -> float:
    if col not in statuses.columns:
        return 0.0
    return float(pd.to_numeric(statuses[col], errors="coerce").fillna(0.0).gt(0).mean())


def artist_namespace_overlap(test_artist_keys: pd.Series) -> dict[str, Any]:
    fixed_test = set(test_artist_keys.astype(str).str.strip())
    external_artists: set[str] = set()
    search_artists: set[str] = set()
    if EXTERNAL_CACHE.exists():
        cache = pd.read_csv(EXTERNAL_CACHE, usecols=["artist_key"], low_memory=False)
        external_artists = set(cache["artist_key"].astype(str).str.strip())
    if OFFICIAL_DB.exists():
        with sqlite3.connect(OFFICIAL_DB) as conn:
            search = pd.read_sql_query(
                "SELECT DISTINCT artist_key FROM artist_search_feature_snapshots WHERE artist_key IS NOT NULL",
                conn,
            )
        search_artists = set(search["artist_key"].astype(str).str.strip())
    return {
        "fixed_test_artist_count": len(fixed_test),
        "external_cache_artist_count": len(external_artists),
        "external_cache_overlap_artist_count": len(fixed_test & external_artists),
        "search_snapshot_artist_count": len(search_artists),
        "search_snapshot_overlap_artist_count": len(fixed_test & search_artists),
    }


def markdown(payload: dict[str, Any], feature_group: pd.DataFrame, feature_report: pd.DataFrame) -> str:
    lines = [
        "# 공식 v0.1 Cold feature parity 감사",
        "",
        f"- 작성일: {payload['created_at']}",
        f"- 비교 범위: fixed-test Cold {payload['n_rows']}건",
        "- 비교 대상: 실험 feature 생성 결과 vs 공식 v0.1 서비스 adapter feature 생성 결과",
        "",
        "## 1. 결론",
        "",
        f"- exact feature parity 통과: {'예' if payload['exact_feature_parity_passed'] else '아니오'}",
        f"- exact prediction parity 통과: {'예' if payload['exact_prediction_parity_passed'] else '아니오'}",
        f"- 서비스 adapter 의미: {payload['service_adapter_interpretation']}",
        f"- fixed-test 작가 수: {payload['artist_namespace_overlap']['fixed_test_artist_count']}명",
        f"- row-level Cold feature store hit rate: {payload['coverage']['cold_feature_store_hit_rate']:.4f}",
        f"- 공식 전시/갤러리 cache 작가 수: {payload['artist_namespace_overlap']['external_cache_artist_count']}명, fixed-test 교집합: {payload['artist_namespace_overlap']['external_cache_overlap_artist_count']}명",
        f"- 공식 검색 snapshot 작가 수: {payload['artist_namespace_overlap']['search_snapshot_artist_count']}명, fixed-test 교집합: {payload['artist_namespace_overlap']['search_snapshot_overlap_artist_count']}명",
        "- 해석: row-level feature store가 적중한 행은 실험 당시 Cold 입력 피처를 그대로 재사용한다. 미적중 행은 공식 서비스 cache 기반 proxy feature로 계산한다.",
        "",
        "## 2. Feature 그룹별 일치율",
        "",
        "| 그룹 | 타입 | 피처 수 | 평균 일치율 | 최소 일치율 | 실험 non-missing | 서비스 non-missing |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in feature_group.iterrows():
        lines.append(
            f"| {row['group']} | {row['type']} | {int(row['feature_count'])} | "
            f"{row['mean_match_rate']:.4f} | {row['min_match_rate']:.4f} | "
            f"{row['mean_exact_non_missing_rate']:.4f} | {row['mean_service_non_missing_rate']:.4f} |"
        )
    worst = feature_report.sort_values("match_rate").head(15)
    lines.extend([
        "",
        "## 3. 불일치가 큰 피처",
        "",
        "| 피처 | 그룹 | 타입 | 일치율 | 평균 차이 | p95 차이 |",
        "|---|---|---|---:|---:|---:|",
    ])
    for _, row in worst.iterrows():
        mean = "" if pd.isna(row.get("mean_abs_diff")) else f"{row['mean_abs_diff']:.6f}"
        p95 = "" if pd.isna(row.get("p95_abs_diff")) else f"{row['p95_abs_diff']:.6f}"
        lines.append(f"| {row['feature']} | {row['group']} | {row['type']} | {row['match_rate']:.4f} | {mean} | {p95} |")
    lines.extend([
        "",
        "## 4. 예측값 영향",
        "",
        "| 항목 | 실험 feature 기준 | 서비스 feature 기준 |",
        "|---|---:|---:|",
    ])
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        lines.append(
            f"| {metric} | {payload['metrics_exact_features'][metric]:.6f} | {payload['metrics_service_features'][metric]:.6f} |"
        )
    lines.extend([
        "",
        "## 5. 판단",
        "",
        "- 현재 서비스 adapter는 검색 snapshot과 전시/갤러리 작가 단위 cache를 사용해 Cold 최고 경로의 입력을 생성할 수 있습니다.",
        "- 다만 fixed-test와 완전히 같은 row-level feature parity는 아직 아닙니다.",
        "- 완전 parity가 필요하면 실험에서 사용한 row-level 전시/갤러리 및 검색 feature store를 운영 DB에 동일 스키마로 저장하고, 신규 입력에는 같은 builder를 적용해야 합니다.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()

    OUT_DIR.joinpath("outputs").mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    features = load_json(FEATURE_SCHEMA)["pp_y2_feature_columns"]
    exact = load_exact_fixed_test(features)
    source = pd.read_csv(SPLIT_TEST, low_memory=False)
    source = source.merge(
        exact[["_track6_row_id"]],
        on="_track6_row_id",
        how="inner",
    ).sort_values("_track6_row_id").reset_index(drop=True)
    exact = exact.merge(source[["_track6_row_id"]], on="_track6_row_id", how="inner")
    exact = exact.sort_values("_track6_row_id").reset_index(drop=True)
    if args.max_rows is not None:
        source = source.head(args.max_rows).copy()
        exact = exact[exact["_track6_row_id"].isin(source["_track6_row_id"])].copy()

    adapter = ReportModelProxyAdapter()
    service, statuses = build_service_feature_frame(adapter, source, features, args.max_rows)
    service = service.sort_values("_track6_row_id").reset_index(drop=True)
    exact = exact.sort_values("_track6_row_id").reset_index(drop=True)

    feature_report, group_report = compare_features(exact, service, features)
    exact_pred = predict_bundle(adapter, exact[["_track6_row_id", *features]], exact["artist_key"])
    service_pred = predict_bundle(adapter, service[["_track6_row_id", *features]], source["artist_key"].astype(str).str.strip())
    exact_pred = exact_pred.sort_values("_track6_row_id").reset_index(drop=True)
    service_pred = service_pred.sort_values("_track6_row_id").reset_index(drop=True)

    actual = exact[["_track6_row_id", "price_krw", "ln_price_krw"]].merge(exact_pred, on="_track6_row_id")
    service_actual = exact[["_track6_row_id", "price_krw", "ln_price_krw"]].merge(service_pred, on="_track6_row_id")
    metrics_exact = metric_triplet(
        actual["price_krw"].to_numpy(dtype=float),
        actual["ln_price_krw"].to_numpy(dtype=float),
        actual["final_log"].to_numpy(dtype=float),
    )
    metrics_service = metric_triplet(
        service_actual["price_krw"].to_numpy(dtype=float),
        service_actual["ln_price_krw"].to_numpy(dtype=float),
        service_actual["final_log"].to_numpy(dtype=float),
    )
    prediction_delta = summarize_prediction_delta(exact_pred, service_pred)
    exact_feature_pass = bool((feature_report["match_rate"] >= 0.999999).all())
    exact_prediction_pass = bool(prediction_delta["final_log"]["allclose_1e_9"])
    payload = {
        "created_at": now(),
        "n_rows": int(len(exact)),
        "exact_feature_parity_passed": exact_feature_pass,
        "exact_prediction_parity_passed": exact_prediction_pass,
        "service_adapter_interpretation": (
            "operational_bridge_cache_ready_not_exact_fixed_test_parity"
            if not exact_prediction_pass
            else "exact_fixed_test_parity"
        ),
        "coverage": {
            "cold_feature_store_hit_rate": float(statuses["cold_feature_store_hit"].mean()),
            "search_found_rate": float(statuses["search_found"].mean()),
            "external_found_rate": float(statuses["external_found"].mean()),
            "external_has_exhibition_rate": status_positive_rate(statuses, "external_artist_exhibition_available_count"),
            "external_has_gallery_rate": status_positive_rate(statuses, "external_gallery_tier_any_available_flag"),
        },
        "artist_namespace_overlap": artist_namespace_overlap(source["artist_key"]),
        "metrics_exact_features": metrics_exact,
        "metrics_service_features": metrics_service,
        "prediction_delta": prediction_delta,
        "outputs": {
            "feature_report": rel(OUT_DIR / "outputs" / "feature_parity_by_column.csv"),
            "group_report": rel(OUT_DIR / "outputs" / "feature_parity_by_group.csv"),
            "status_report": rel(OUT_DIR / "outputs" / "service_lookup_status_by_row.csv"),
            "exact_predictions": rel(OUT_DIR / "outputs" / "exact_feature_predictions.csv"),
            "service_predictions": rel(OUT_DIR / "outputs" / "service_feature_predictions.csv"),
        },
    }

    feature_report.to_csv(OUT_DIR / "outputs" / "feature_parity_by_column.csv", index=False)
    group_report.to_csv(OUT_DIR / "outputs" / "feature_parity_by_group.csv", index=False)
    statuses.to_csv(OUT_DIR / "outputs" / "service_lookup_status_by_row.csv", index=False)
    exact_pred.to_csv(OUT_DIR / "outputs" / "exact_feature_predictions.csv", index=False)
    service_pred.to_csv(OUT_DIR / "outputs" / "service_feature_predictions.csv", index=False)
    (OUT_DIR / "outputs" / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(markdown(payload, group_report, feature_report), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
