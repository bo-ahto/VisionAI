#!/usr/bin/env python3
"""Run PP-HCOEF19: operational feature-pipeline reconciliation for Warm Huber.

PP-HCOEF16~18 found useful signals around the service PP-V8 component and
quantile width, but those signals did not pass the repeated validation gates as
new point-prediction candidates. Before adding more coefficient refinements, this
experiment audits whether the research prediction columns and the runnable v0.1
operational pipeline produce the same component values on the 0604 stress set.

No new coefficient or threshold is selected from 0604. The output is an audit
package that tells the next HCOEF experiment whether it is safe to compare
research candidates against operational predictions.
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
EXP_ID = "PP-HCOEF19"
EXP_SLUG = "PP-HCOEF19_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

HCOEF18_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF18_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
HCOEF18_BOOTSTRAP = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF18_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "bootstrap_or_repeated_split_summary.csv"
)
OP_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational"
OP_MANIFEST = OP_ROOT / "artifacts" / "operational_policy_manifest.json"
OP_FEATURES = OP_ROOT / "outputs" / "0604_features" / "warm_features_v0_1.csv"
OP_PREDICTIONS = OP_ROOT / "outputs" / "0604_predictions" / "predictions_all.csv"
OP_EVALUATION = OP_ROOT / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

REFERENCE = "current_70_30"
STABLE = "hcoef_stable"
PPV8 = "ppv8_service_proxy"
SVC = "svc_numeric_seed_mean"
L10 = "l10_seq_full_generated_bucket"

FX_USD = 1380.0
LOG_TOLERANCE = 1e-8


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    return np.exp(np.clip(np.asarray(values, dtype=float), np.log(1_000.0), np.log(1_000_000_000_000.0)))


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_price = safe_exp(pred_log)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((actual_log - pred_log) ** 2))),
        "Within_30": float(np.nanmean(ape <= 0.30)),
        "Within_50": float(np.nanmean(ape <= 0.50)),
        "over_2x_n": int(np.nansum(pred_price >= actual_price * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual_price * 0.5)),
    }


def metric(frame: pd.DataFrame, pred_log_col: str) -> dict[str, float]:
    return metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        frame[pred_log_col].to_numpy(dtype=float),
    )


def load_manifest() -> dict[str, Any]:
    return json.loads(OP_MANIFEST.read_text(encoding="utf-8"))


def load_research_base() -> pd.DataFrame:
    preds = pd.read_csv(HCOEF18_PREDICTIONS, low_memory=False)
    base = preds[preds["candidate"].eq(STABLE)].copy()
    cols = [
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        STABLE,
        REFERENCE,
        PPV8,
        SVC,
        "l10_seq_pred_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "title",
        "medium_support_bucket",
        "width_cm",
        "height_cm",
        "area_cm2",
        "log_area",
    ]
    cols = [col for col in cols if col in base.columns]
    return base[cols].drop_duplicates(["split", "_track6_row_id"]).reset_index(drop=True)


def load_operational_0604() -> pd.DataFrame:
    op = pd.read_csv(OP_EVALUATION, low_memory=False)
    op = op[
        (pd.to_numeric(op["actual_price_krw"], errors="coerce").notna())
        & (pd.to_numeric(op["actual_price_usd_equiv"], errors="coerce") >= 50.0)
        & (op["warm_cold_route"].astype(str).eq("warm"))
    ].copy()
    op["actual_price"] = pd.to_numeric(op["actual_price_krw"], errors="coerce")
    op["actual_log"] = np.log(op["actual_price"].clip(lower=1.0))
    op_cols = [
        "_v01_row_id",
        "_track6_row_id",
        "artist_key",
        "artist_name",
        "artist_match_status",
        "warm_cold_route",
        "actual_price",
        "actual_log",
        "actual_price_usd_equiv",
        "svc_numeric_seed_mean_pred_log",
        "l10_generated_bucket_seq_pred_log",
        "l10_q10_pred_log",
        "l10_q50_pred_log",
        "l10_q90_pred_log",
        "l10_quantile_width",
        "l10_price_range_ratio",
        "pp_v2_defensive_pred_log",
        "pp_v8_compact_blend_mape_guarded_pred_log",
        "v01_operational_pred_log",
        "service_primary_pred_log",
        "service_confidence_tier",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "title",
        "medium_support_bucket",
        "width_cm",
        "height_cm",
        "area_cm2",
        "log_area",
    ]
    op_cols = [col for col in op_cols if col in op.columns]
    return op[op_cols].drop_duplicates("_track6_row_id").reset_index(drop=True)


def joined_0604(research: pd.DataFrame, operational: pd.DataFrame) -> pd.DataFrame:
    r = research[research["split"].eq("0604_ex50")].copy()
    merged = r.merge(
        operational,
        on="_track6_row_id",
        how="inner",
        suffixes=("_research", "_operational"),
    )
    # Use operational labels as authoritative for 0604 service-style evaluation.
    merged["actual_price"] = pd.to_numeric(merged["actual_price_operational"], errors="coerce")
    merged["actual_log"] = pd.to_numeric(merged["actual_log_operational"], errors="coerce")
    return merged


def diff_summary(frame: pd.DataFrame, left: str, right: str, check_name: str) -> dict[str, Any]:
    valid = frame[[left, right]].apply(pd.to_numeric, errors="coerce").dropna()
    if valid.empty:
        return {
            "check_name": check_name,
            "left_column": left,
            "right_column": right,
            "n": 0,
            "status": "missing",
            "max_abs_log_diff": np.nan,
            "mean_abs_log_diff": np.nan,
            "median_abs_log_diff": np.nan,
            "p95_abs_log_diff": np.nan,
            "exact_match_rate_1e8": np.nan,
        }
    diff = (valid[left] - valid[right]).abs()
    return {
        "check_name": check_name,
        "left_column": left,
        "right_column": right,
        "n": int(len(diff)),
        "status": "pass" if float(diff.max()) <= LOG_TOLERANCE else "review",
        "max_abs_log_diff": float(diff.max()),
        "mean_abs_log_diff": float(diff.mean()),
        "median_abs_log_diff": float(diff.median()),
        "p95_abs_log_diff": float(diff.quantile(0.95)),
        "exact_match_rate_1e8": float((diff <= LOG_TOLERANCE).mean()),
    }


def component_reconciliation(frame: pd.DataFrame) -> pd.DataFrame:
    checks = [
        (SVC, "svc_numeric_seed_mean_pred_log", "svc_research_vs_operational"),
        (PPV8, "pp_v8_compact_blend_mape_guarded_pred_log", "ppv8_research_vs_operational"),
        (REFERENCE, "v01_operational_pred_log", "current70_30_research_vs_operational"),
        ("l10_seq_pred_log", "l10_generated_bucket_seq_pred_log", "l10_research_vs_operational"),
        ("quantile_width", "l10_quantile_width", "quantile_width_research_vs_operational"),
        ("l10_price_range_ratio_research", "l10_price_range_ratio_operational", "price_range_ratio_research_vs_operational"),
    ]
    rows = []
    for left, right, name in checks:
        if left in frame.columns and right in frame.columns:
            rows.append(diff_summary(frame, left, right, name))
        else:
            rows.append(
                {
                    "check_name": name,
                    "left_column": left,
                    "right_column": right,
                    "n": 0,
                    "status": "missing",
                    "max_abs_log_diff": np.nan,
                    "mean_abs_log_diff": np.nan,
                    "median_abs_log_diff": np.nan,
                    "p95_abs_log_diff": np.nan,
                    "exact_match_rate_1e8": np.nan,
                }
            )
    return pd.DataFrame(rows)


def formula_checks(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["formula_operational_ppv8"] = (
        0.75 * pd.to_numeric(out["pp_v2_defensive_pred_log"], errors="coerce")
        + 0.25 * pd.to_numeric(out["l10_generated_bucket_seq_pred_log"], errors="coerce")
    )
    out["formula_operational_v01"] = (
        0.70 * pd.to_numeric(out["svc_numeric_seed_mean_pred_log"], errors="coerce")
        + 0.30 * pd.to_numeric(out["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce")
    )
    out["formula_research_v01"] = 0.70 * pd.to_numeric(out[SVC], errors="coerce") + 0.30 * pd.to_numeric(out[PPV8], errors="coerce")
    checks = [
        diff_summary(out, "formula_operational_ppv8", "pp_v8_compact_blend_mape_guarded_pred_log", "operational_ppv8_formula"),
        diff_summary(out, "formula_operational_v01", "v01_operational_pred_log", "operational_70_30_formula"),
        diff_summary(out, "formula_research_v01", REFERENCE, "research_70_30_formula"),
        diff_summary(out, "service_primary_pred_log", "pp_v8_compact_blend_mape_guarded_pred_log", "service_primary_equals_ppv8"),
    ]
    return pd.DataFrame(checks)


def feature_pipeline_audit(manifest: dict[str, Any]) -> pd.DataFrame:
    features = pd.read_csv(OP_FEATURES, low_memory=False)
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "audit_type": "row_count",
            "feature": "__rows__",
            "required_by": "operational_feature_file",
            "status": "info",
            "n_rows": int(len(features)),
            "missing_rate": np.nan,
            "details": "Warm route feature rows available for operational prediction.",
        }
    )
    if "artist_key.1" in features.columns and "artist_key" in features.columns:
        mismatch = (
            features["artist_key"].astype(str).fillna("")
            != features["artist_key.1"].astype(str).fillna("")
        )
        rows.append(
            {
                "audit_type": "duplicate_artist_key_column",
                "feature": "artist_key.1",
                "required_by": "feature_extractor",
                "status": "review" if bool(mismatch.any()) else "pass",
                "n_rows": int(len(features)),
                "missing_rate": float(features["artist_key.1"].isna().mean()),
                "details": f"artist_key vs artist_key.1 mismatch rows: {int(mismatch.sum())}",
            }
        )

    required_by_component: dict[str, set[str]] = {}
    derived_by_component: dict[str, set[str]] = {}
    for component, info in manifest.get("components", {}).items():
        if component == "l10_generated_bucket_seq":
            # q10/q50/q90/quantile_width/price_range_ratio are generated inside
            # predict_operational_v0_1.py, so they are not expected in the raw
            # operational warm feature file.
            for feature in info.get("base_features", []) if isinstance(info.get("base_features"), list) else []:
                required_by_component.setdefault(feature, set()).add(component)
            base = set(info.get("base_features", []) if isinstance(info.get("base_features"), list) else [])
            enriched = set(info.get("enriched_features", []) if isinstance(info.get("enriched_features"), list) else [])
            for feature in sorted(enriched - base):
                derived_by_component.setdefault(feature, set()).add(component)
            continue
        for feature in info.get("features", []) if isinstance(info.get("features"), list) else []:
            required_by_component.setdefault(feature, set()).add(component)
    for feature, components in sorted(required_by_component.items()):
        if feature in features.columns:
            series = features[feature]
            missing_rate = float(series.isna().mean())
            if series.dtype == object:
                missing_rate = float(series.astype(str).replace({"": np.nan, "nan": np.nan, "__MISSING__": np.nan}).isna().mean())
            status = "pass" if missing_rate < 0.20 else "review"
            detail = "present"
        else:
            missing_rate = 1.0
            status = "missing"
            detail = "required feature missing from operational warm feature file"
        rows.append(
            {
                "audit_type": "required_feature",
                "feature": feature,
                "required_by": ",".join(sorted(components)),
                "status": status,
                "n_rows": int(len(features)),
                "missing_rate": missing_rate,
                "details": detail,
            }
        )
    for feature, components in sorted(derived_by_component.items()):
        rows.append(
            {
                "audit_type": "derived_prediction_feature",
                "feature": feature,
                "required_by": ",".join(sorted(components)),
                "status": "generated",
                "n_rows": int(len(features)),
                "missing_rate": np.nan,
                "details": "Generated during operational prediction, not expected in warm_features_v0_1.csv.",
            }
        )
    for feature in [
        "artist_key",
        "artist_match_status",
        "svc_group_n",
        "svc_group_level",
        "svc_coverage_tier",
        "medium_support_bucket",
        "log_area",
    ]:
        if feature in features.columns:
            value_counts = features[feature].astype(str).value_counts(dropna=False).head(8).to_dict()
            rows.append(
                {
                    "audit_type": "operational_distribution",
                    "feature": feature,
                    "required_by": "diagnostic",
                    "status": "info",
                    "n_rows": int(len(features)),
                    "missing_rate": float(features[feature].isna().mean()),
                    "details": json.dumps(value_counts, ensure_ascii=False),
                }
            )
    return pd.DataFrame(rows)


def metric_rows(research: pd.DataFrame, merged_0604: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    candidate_cols = [
        ("hcoef_stable", STABLE, "research_hcoef_stable"),
        ("current_70_30", REFERENCE, "research_report_70_30"),
        ("ppv8_service_proxy", PPV8, "research_ppv8_proxy"),
        ("svc_numeric_seed_mean", SVC, "research_svc_component"),
        ("l10_seq_full_generated_bucket", "l10_seq_pred_log", "research_l10_component"),
    ]
    for split in ["validation", "test"]:
        frame = research[research["split"].eq(split)].copy()
        for candidate, col, method in candidate_cols:
            if col not in frame.columns:
                continue
            m = metric(frame, col)
            rows.append({"scope": "research_fixed", "split": split, "candidate": candidate, "method": method, "n": len(frame), **m})

    op_candidates = [
        ("hcoef_stable", STABLE, "research_hcoef_stable_on_0604"),
        ("current_70_30_research", REFERENCE, "research_70_30_on_0604"),
        ("current_70_30_operational", "v01_operational_pred_log", "operational_70_30_on_0604"),
        ("ppv8_research", PPV8, "research_ppv8_on_0604"),
        ("ppv8_operational_service_primary", "service_primary_pred_log", "operational_service_primary_on_0604"),
        ("svc_research", SVC, "research_svc_on_0604"),
        ("svc_operational", "svc_numeric_seed_mean_pred_log", "operational_svc_on_0604"),
        ("l10_research", "l10_seq_pred_log", "research_l10_on_0604"),
        ("l10_operational", "l10_generated_bucket_seq_pred_log", "operational_l10_on_0604"),
    ]
    for candidate, col, method in op_candidates:
        if col not in merged_0604.columns:
            continue
        m = metric(merged_0604, col)
        rows.append({"scope": "0604_reconciled_ex50", "split": "0604_ex50", "candidate": candidate, "method": method, "n": len(merged_0604), **m})
    out = pd.DataFrame(rows)
    stable = out[out["candidate"].eq("hcoef_stable")][["scope", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].rename(
        columns={
            "MdAPE": "stable_MdAPE",
            "MAPE": "stable_MAPE",
            "p95_APE": "stable_p95_APE",
            "RMSE_log": "stable_RMSE_log",
        }
    )
    out = out.merge(stable, on=["scope", "split"], how="left")
    for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"delta_{metric_name}_vs_hcoef_stable"] = out[metric_name] - out[f"stable_{metric_name}"]
    return out


def candidate_predictions(research: pd.DataFrame, merged_0604: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []

    def append_prediction(frame: pd.DataFrame, split: str, candidate: str, col: str, method: str, source: str) -> None:
        if col not in frame.columns:
            return
        pred_log = pd.to_numeric(frame[col], errors="coerce")
        actual_price = pd.to_numeric(frame["actual_price"], errors="coerce")
        actual_log = pd.to_numeric(frame["actual_log"], errors="coerce")
        pred_price = safe_exp(pred_log)
        out = pd.DataFrame(
            {
                "experiment_id": EXP_ID,
                "source": source,
                "split": split,
                "candidate": candidate,
                "method": method,
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "artist_key": frame.get("artist_key_research", frame.get("artist_key", pd.Series("", index=frame.index))).astype(str).to_numpy(),
                "actual_log": actual_log.to_numpy(dtype=float),
                "actual_price": actual_price.to_numpy(dtype=float),
                "pred_log": pred_log.to_numpy(dtype=float),
                "pred_price": pred_price,
                "residual_log": actual_log.to_numpy(dtype=float) - pred_log.to_numpy(dtype=float),
                "ape": np.abs(pred_price - actual_price.to_numpy(dtype=float)) / np.clip(actual_price.to_numpy(dtype=float), 1.0, None),
            }
        )
        for extra in ["svc_group_level", "svc_coverage_tier", "svc_group_n", "service_confidence_tier", "medium_support_bucket", "log_area"]:
            if extra in frame.columns:
                out[extra] = frame[extra].to_numpy()
            elif f"{extra}_research" in frame.columns:
                out[extra] = frame[f"{extra}_research"].to_numpy()
            elif f"{extra}_operational" in frame.columns:
                out[extra] = frame[f"{extra}_operational"].to_numpy()
        rows.append(out)

    for split in ["validation", "test"]:
        frame = research[research["split"].eq(split)].copy()
        for candidate, col, method in [
            ("hcoef_stable", STABLE, "research_hcoef_stable"),
            ("current_70_30", REFERENCE, "research_report_70_30"),
            ("ppv8_service_proxy", PPV8, "research_ppv8_proxy"),
            ("svc_numeric_seed_mean", SVC, "research_svc_component"),
            ("l10_seq_full_generated_bucket", "l10_seq_pred_log", "research_l10_component"),
        ]:
            append_prediction(frame, split, candidate, col, method, "research_fixed")

    for candidate, col, method in [
        ("hcoef_stable", STABLE, "research_hcoef_stable_on_0604"),
        ("current_70_30_research", REFERENCE, "research_70_30_on_0604"),
        ("current_70_30_operational", "v01_operational_pred_log", "operational_70_30_on_0604"),
        ("ppv8_research", PPV8, "research_ppv8_on_0604"),
        ("ppv8_operational_service_primary", "service_primary_pred_log", "operational_service_primary_on_0604"),
        ("svc_research", SVC, "research_svc_on_0604"),
        ("svc_operational", "svc_numeric_seed_mean_pred_log", "operational_svc_on_0604"),
        ("l10_research", "l10_seq_pred_log", "research_l10_on_0604"),
        ("l10_operational", "l10_generated_bucket_seq_pred_log", "operational_l10_on_0604"),
    ]:
        append_prediction(merged_0604, "0604_ex50", candidate, col, method, "0604_reconciled")
    return pd.concat(rows, ignore_index=True)


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    segment_cols = ["svc_coverage_tier", "svc_group_level", "service_confidence_tier"]
    predictions = predictions.copy()
    predictions["svc_group_n"] = pd.to_numeric(predictions.get("svc_group_n"), errors="coerce").fillna(0.0)
    predictions["svc_group_n_band"] = pd.cut(
        predictions["svc_group_n"],
        bins=[-0.1, 4, 9, 19, 49, np.inf],
        labels=["n_0_4", "n_5_9", "n_10_19", "n_20_49", "n_50_plus"],
    ).astype(str)
    segment_cols.append("svc_group_n_band")
    for col in segment_cols:
        if col not in predictions.columns:
            continue
        grouped = predictions.groupby(["source", "split", "candidate", col], dropna=False)
        for (source, split, candidate, value), group in grouped:
            if len(group) < 5:
                continue
            rows.append(
                {
                    "source": source,
                    "split": split,
                    "candidate": candidate,
                    "segment_col": col,
                    "segment_value": value,
                    "n": len(group),
                    "MdAPE": float(group["ape"].median()),
                    "MAPE": float(group["ape"].mean()),
                    "p95_APE": float(group["ape"].quantile(0.95)),
                    "median_residual_log": float(group["residual_log"].median()),
                    "mean_residual_log": float(group["residual_log"].mean()),
                }
            )
    return pd.DataFrame(rows)


def feature_coefficients() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_or_formula": "current_70_30",
                "feature": "svc_numeric_seed_mean",
                "weight_or_role": 0.70,
                "direction": "positive",
                "interpretation": "유사 작품 기반 가격 피처가 높으면 최종 로그 가격을 올린다.",
            },
            {
                "candidate_or_formula": "current_70_30",
                "feature": "pp_v8_compact_blend_mape_guarded",
                "weight_or_role": 0.30,
                "direction": "positive",
                "interpretation": "오차 안정화 component가 높으면 최종 로그 가격을 올린다.",
            },
            {
                "candidate_or_formula": "pp_v8_compact_blend_mape_guarded",
                "feature": "pp_v2_defensive_component",
                "weight_or_role": 0.75,
                "direction": "positive",
                "interpretation": "큰 오차를 방어하도록 만든 방어형 component가 PP-V8의 중심축이다.",
            },
            {
                "candidate_or_formula": "pp_v8_compact_blend_mape_guarded",
                "feature": "l10_generated_bucket_seq",
                "weight_or_role": 0.25,
                "direction": "positive",
                "interpretation": "Quantile-Huber-CatBoost 순차 component를 보조축으로 사용한다.",
            },
            {
                "candidate_or_formula": "hcoef_stable",
                "feature": "current_70_30 residual correction",
                "weight_or_role": "capped_huber_residual",
                "direction": "signed",
                "interpretation": "검증 split에서 학습한 Huber 잔차를 작은 cap 안에서만 더해 70:30 후보를 보정한다.",
            },
            {
                "candidate_or_formula": "service_range_confidence",
                "feature": "l10_quantile_width",
                "weight_or_role": "range/confidence signal",
                "direction": "wider means lower confidence",
                "interpretation": "HCOEF18 결과상 점 예측 이동보다 가격 범위와 신뢰도 표시용으로 적합하다.",
            },
        ]
    )


def carried_forward_bootstrap() -> pd.DataFrame:
    if HCOEF18_BOOTSTRAP.exists():
        boot = pd.read_csv(HCOEF18_BOOTSTRAP, low_memory=False)
        focus = boot[boot["candidate"].isin([STABLE, REFERENCE])].copy()
        if focus.empty:
            focus = boot.head(0).copy()
        focus.insert(0, "carried_forward_by", EXP_ID)
        focus.insert(1, "source_experiment", "PP-HCOEF18")
        focus["note"] = "HCOEF19 is a pipeline audit; no new OOF candidate is selected."
        return focus
    return pd.DataFrame(
        [
            {
                "carried_forward_by": EXP_ID,
                "source_experiment": "PP-HCOEF18",
                "candidate": "__not_applicable__",
                "note": "Source bootstrap file missing; HCOEF19 selected no new candidate.",
            }
        ]
    )


def policy_map(reconciliation: pd.DataFrame, formula: pd.DataFrame, feature_audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_recon_pass = bool(reconciliation["status"].isin(["pass"]).all())
    formula_pass = bool(formula["status"].isin(["pass"]).all())
    required_missing = int((feature_audit["status"].eq("missing")).sum())
    rows.append(
        {
            "policy_item": "component_reconciliation",
            "status": "pass" if all_recon_pass else "review",
            "details": "Research and operational component logs match on common 0604 rows." if all_recon_pass else "At least one research/operational component differs; inspect component_reconciliation.csv.",
        }
    )
    rows.append(
        {
            "policy_item": "formula_checks",
            "status": "pass" if formula_pass else "review",
            "details": "Operational formulas reproduce saved prediction columns." if formula_pass else "Formula output differs from saved columns.",
        }
    )
    rows.append(
        {
            "policy_item": "feature_schema",
            "status": "pass" if required_missing == 0 else "review",
            "details": f"Missing required operational features: {required_missing}",
        }
    )
    rows.append(
        {
            "policy_item": "next_experiment",
            "status": "ready" if all_recon_pass and formula_pass and required_missing == 0 else "review_first",
            "details": "If ready, continue with HCOEF20 coefficient/range policy experiments without changing test-derived thresholds.",
        }
    )
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    view = frame.copy()
    if max_rows is not None and len(view) > max_rows:
        view = view.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.6f}")
        else:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(x))
    return "\n".join(
        [
            "| " + " | ".join(view.columns) + " |",
            "| " + " | ".join("---" for _ in view.columns) + " |",
            *["| " + " | ".join(row) + " |" for row in view.itertuples(index=False, name=None)],
        ]
    )


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []
    in_code = False
    code: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("```"):
            flush_table()
            if in_code:
                body.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937;line-height:1.55}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6} h1,h2,h3{margin-top:24px} code{background:#f3f4f6;padding:1px 4px}"
        "pre{background:#111827;color:#f9fafb;padding:14px;overflow:auto}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    metrics: pd.DataFrame,
    reconciliation: pd.DataFrame,
    formulas: pd.DataFrame,
    feature_audit: pd.DataFrame,
    policies: pd.DataFrame,
) -> str:
    component_status = "통과" if reconciliation["status"].eq("pass").all() else "검토 필요"
    formula_status = "통과" if formulas["status"].eq("pass").all() else "검토 필요"
    missing_required = int(feature_audit["status"].eq("missing").sum())
    op_0604 = metrics[
        (metrics["scope"].eq("0604_reconciled_ex50"))
        & (metrics["candidate"].isin(["hcoef_stable", "current_70_30_operational", "ppv8_operational_service_primary"]))
    ].sort_values(["MdAPE", "MAPE", "p95_APE"])

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 운영 피처 파이프라인 재현성 검증",
            "",
            "## 1. 실험 목적",
            "",
            "- HCOEF16~18에서 사용한 연구용 component와 v0.1 운영 pipeline component가 같은 값을 내는지 확인.",
            "- 새 보정값을 test/0604에서 만들지 않고, 다음 Huber 계수 실험 전에 입력 피처 재현성을 검증.",
            "- 결론은 성능 후보 채택이 아니라, 다음 HCOEF 실험을 진행해도 되는지에 대한 감사 결과.",
            "",
            "## 2. 핵심 결론",
            "",
            f"- component reconciliation: {component_status}.",
            f"- formula check: {formula_status}.",
            f"- 운영 Warm feature file의 필수 피처 누락 수: {missing_required}.",
            "- HCOEF19에서는 새 운영 후보를 채택하지 않음.",
            "- quantile width는 HCOEF18 결론대로 점 예측 이동보다 가격 범위/신뢰도 정책 검증에 우선 사용.",
            "",
            "## 3. 0604 공통 행 후보 성능",
            "",
            markdown_table(op_0604.round(6), max_rows=20),
            "",
            "## 4. 연구 산출물과 운영 산출물 component 비교",
            "",
            markdown_table(reconciliation.round(8)),
            "",
            "## 5. 운영 예측식 검증",
            "",
            markdown_table(formulas.round(8)),
            "",
            "## 6. 운영 피처 파일 감사 요약",
            "",
            markdown_table(feature_audit[feature_audit["status"].isin(["missing", "review"])].head(40).round(6), max_rows=40),
            "",
            "## 7. 정책 판단",
            "",
            markdown_table(policies),
            "",
            "## 8. 다음 보정 방향",
            "",
            "- component/formula/feature schema가 모두 통과하면 HCOEF20에서 저차원 Huber 계수 재탐색 또는 가격 범위/신뢰도 정책 검증을 진행.",
            "- component 불일치가 있으면 새 모델 실험보다 먼저 해당 column mapping과 피처 생성 로직을 수정.",
            "- 운영 기본 후보 변경은 HCOEF19 결과만으로 결정하지 않음.",
        ]
    )
    report_path = EXP_DIR / "reports" / "result_report.md"
    report_path.write_text(md + "\n", encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef19_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md + "\n", encoding="utf-8")
    (DOC_ROOT / "pp_hcoef19_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")
    return md


def main() -> None:
    ensure_dirs()
    manifest = load_manifest()
    research = load_research_base()
    operational = load_operational_0604()
    merged = joined_0604(research, operational)

    reconciliation = component_reconciliation(merged)
    formulas = formula_checks(merged)
    feature_audit = feature_pipeline_audit(manifest)
    metrics = metric_rows(research, merged)
    predictions = candidate_predictions(research, merged)
    residuals = residual_analysis(predictions)
    coefficients = feature_coefficients()
    bootstrap = carried_forward_bootstrap()
    policies = policy_map(reconciliation, formulas, feature_audit)

    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    reconciliation.to_csv(EXP_DIR / "outputs" / "component_reconciliation.csv", index=False)
    formulas.to_csv(EXP_DIR / "outputs" / "formula_checks.csv", index=False)
    feature_audit.to_csv(EXP_DIR / "outputs" / "feature_pipeline_audit.csv", index=False)
    policies.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Warm Huber service feature-pipeline reconciliation before further coefficient tuning.",
        "inputs": {
            "hcoef18_predictions": str(HCOEF18_PREDICTIONS.relative_to(REPO)),
            "operational_manifest": str(OP_MANIFEST.relative_to(REPO)),
            "operational_features": str(OP_FEATURES.relative_to(REPO)),
            "operational_predictions": str(OP_PREDICTIONS.relative_to(REPO)),
            "operational_evaluation": str(OP_EVALUATION.relative_to(REPO)),
        },
        "selection_policy": "No new candidate selected from 0604. This is an operational reproducibility audit.",
        "log_tolerance": LOG_TOLERANCE,
        "common_0604_rows": int(len(merged)),
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics, reconciliation, formulas, feature_audit, policies)
    print(json.dumps({"status": "completed", "experiment": EXP_ID, "common_0604_rows": int(len(merged)), "output_dir": str(EXP_DIR.relative_to(REPO))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
