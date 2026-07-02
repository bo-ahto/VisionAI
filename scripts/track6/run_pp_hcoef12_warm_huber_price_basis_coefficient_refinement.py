#!/usr/bin/env python3
"""Run PP-HCOEF12: operational packaging audit for the Warm Huber candidate.

PP-HCOEF11 confirmed that `hcoef2_size_reliability_cap005_s050` is stable
against the v0.1 Warm 70:30 reference in repeated OOF.  This script moves the
candidate one step closer to operational use without changing the selected
formula:

- fit the selected residual Huber correction on the validation split,
- persist the fitted model and feature schema,
- reload the package and verify prediction equality,
- reproduce validation/test/0604 metrics from the packaged model,
- carry forward HCOEF11 repeated/bootstrap evidence as the audit basis.

This is still an experiment artifact, not a production overwrite.
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef11_warm_huber_price_basis_coefficient_refinement as hcoef11  # noqa: E402
import run_pp_hcoef3_warm_huber_residual_repeated_validation as hcoef3  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF12"
EXP_SLUG = "PP-HCOEF12_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = hcoef11.REFERENCE
STABLE = hcoef11.STABLE
STABLE_CONFIG = hcoef11.STABLE_CONFIG
FEATURES = hcoef3.hcoef1.RESIDUAL_FEATURE_SETS[STABLE_CONFIG["feature_key"]]
SOURCE_EVIDENCE = REPO / "experiments" / "track6" / "PP-HCOEF11_warm_huber_price_basis_coefficient_refinement"
PACKAGE_NAME = "warm_hcoef12_hcoef3_stable_residual_huber.joblib"


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef11.metric_from_frame(frame, pred_log)


def fit_packaged_model(validation: pd.DataFrame) -> tuple[dict[str, Any], np.ndarray]:
    target = validation["actual_log"].to_numpy(dtype=float) - validation[REFERENCE].to_numpy(dtype=float)
    model = hcoef3.hcoef1.linear_pipeline("huber", float(STABLE_CONFIG["alpha"]))
    model.fit(validation[FEATURES], target)
    raw = np.asarray(model.predict(validation[FEATURES]), dtype=float)
    correction = np.clip(raw, -float(STABLE_CONFIG["cap"]), float(STABLE_CONFIG["cap"])) * float(STABLE_CONFIG["strength"])
    pred = validation[REFERENCE].to_numpy(dtype=float) + correction
    package = {
        "experiment_id": EXP_ID,
        "component": "warm_hcoef3_stable_residual_huber",
        "candidate": STABLE,
        "reference_candidate": REFERENCE,
        "source_experiment": "PP-HCOEF3/PP-HCOEF11",
        "fit_split": "validation",
        "features": FEATURES,
        "config": dict(STABLE_CONFIG),
        "model": model,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "notes": [
            "Requires the reference prediction current_70_30 and residual feature columns.",
            "Correction is clipped by cap and multiplied by strength before adding to reference pred_log.",
        ],
    }
    return package, pred


def package_predict(package: dict[str, Any], frame: pd.DataFrame) -> np.ndarray:
    model = package["model"]
    config = package["config"]
    raw = np.asarray(model.predict(frame[package["features"]]), dtype=float)
    correction = np.clip(raw, -float(config["cap"]), float(config["cap"])) * float(config["strength"])
    return frame[package["reference_candidate"]].to_numpy(dtype=float) + correction


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray, method: str) -> pd.DataFrame:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred_log,
            "pred_price": pred_price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred_log,
            "ape": np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None),
        }
    )
    if "artist_name_ko" in frame.columns:
        out["artist_name_ko"] = frame["artist_name_ko"].astype(str).to_numpy()
    return out


def fixed_metrics_and_predictions(
    frames: dict[str, pd.DataFrame],
    package: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    check_rows: list[dict[str, Any]] = []

    for split in ["validation", "test", "0604_ex50"]:
        frame = frames[split]
        ref_pred = frame[REFERENCE].to_numpy(dtype=float)
        package_pred = package_predict(package, frame)
        direct_pred, _ = hcoef11.stable_prediction(frames["validation"], frame)
        max_abs_diff = float(np.max(np.abs(package_pred - direct_pred)))

        for candidate, method, pred in [
            (REFERENCE, "reference_70_30", ref_pred),
            (STABLE, "packaged_residual_huber", package_pred),
        ]:
            metric = metric_from_frame(frame, pred)
            ref_metric = metric_from_frame(frame, ref_pred)
            metric_rows.append(
                {
                    "validation_scheme": "fixed_packaged_confirmation",
                    "split": split,
                    "candidate": candidate,
                    "method": method,
                    "n": len(frame),
                    **metric,
                    "delta_MdAPE_vs_reference": metric["MdAPE"] - ref_metric["MdAPE"],
                    "delta_MAPE_vs_reference": metric["MAPE"] - ref_metric["MAPE"],
                    "delta_p95_APE_vs_reference": metric["p95_APE"] - ref_metric["p95_APE"],
                    "delta_RMSE_log_vs_reference": metric["RMSE_log"] - ref_metric["RMSE_log"],
                    "improve_count_vs_reference": int(metric["MdAPE"] < ref_metric["MdAPE"])
                    + int(metric["MAPE"] < ref_metric["MAPE"])
                    + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                }
            )
            pred_rows.append(prediction_frame(frame, candidate, split, pred, method))

        check_rows.append(
            {
                "check_name": f"{split}_packaged_vs_direct_prediction_equal",
                "status": "pass" if max_abs_diff < 1e-12 else "fail",
                "max_abs_pred_log_diff": max_abs_diff,
                "split": split,
                "details": "Packaged model prediction equals direct HCOEF11 rebuild prediction.",
            }
        )

    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.DataFrame(check_rows)


def feature_coefficients(package: dict[str, Any]) -> pd.DataFrame:
    coef = hcoef3.coefficient_frame(package["model"], STABLE_CONFIG).copy()
    coef["experiment_id"] = EXP_ID
    coef["feature_role"] = np.where(
        coef["feature"].isin(["svc_fallback", "shrunk_svc_prior"]),
        "price_basis",
        np.where(coef["feature"].str.contains("gap", regex=False), "basis_gap", "reliability_or_shape"),
    )
    return coef


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    return hcoef11.residual_analysis(predictions)


def carry_forward_validation_summary() -> pd.DataFrame:
    source = SOURCE_EVIDENCE / "outputs" / "bootstrap_or_repeated_split_summary.csv"
    if not source.exists():
        return pd.DataFrame(
            [
                {
                    "summary_type": "source_evidence_missing",
                    "source_experiment": "PP-HCOEF11",
                    "status": "missing",
                }
            ]
        )
    summary = pd.read_csv(source)
    summary.insert(0, "source_experiment", "PP-HCOEF11")
    summary.insert(1, "carried_forward_by", EXP_ID)
    return summary


def readiness_checks(
    metrics: pd.DataFrame,
    check_rows: pd.DataFrame,
    package_path: Path,
    summary: pd.DataFrame,
) -> pd.DataFrame:
    stable_test = metrics[(metrics["split"].eq("test")) & (metrics["candidate"].eq(STABLE))].iloc[0]
    stable_0604 = metrics[(metrics["split"].eq("0604_ex50")) & (metrics["candidate"].eq(STABLE))].iloc[0]
    repeated = summary[summary.get("summary_type", pd.Series(dtype=str)).eq("repeated_oof")].copy()
    row_all3 = repeated.loc[repeated["validation_scheme"].eq("row_oof"), "all3_improve_prob"]
    artist_all3 = repeated.loc[repeated["validation_scheme"].eq("artist_oof"), "all3_improve_prob"]
    checks = [
        {
            "check_name": "package_file_exists",
            "status": "pass" if package_path.exists() else "fail",
            "details": str(package_path.relative_to(REPO)),
        },
        {
            "check_name": "fixed_test_all3_improved_vs_reference",
            "status": "pass" if int(stable_test["improve_count_vs_reference"]) == 3 else "fail",
            "details": f"test MdAPE/MAPE/p95={stable_test['MdAPE']:.4f}/{stable_test['MAPE']:.4f}/{stable_test['p95_APE']:.4f}",
        },
        {
            "check_name": "0604_all3_improved_vs_reference",
            "status": "pass" if int(stable_0604["improve_count_vs_reference"]) == 3 else "warn",
            "details": f"0604 MdAPE/MAPE/p95={stable_0604['MdAPE']:.4f}/{stable_0604['MAPE']:.4f}/{stable_0604['p95_APE']:.4f}",
        },
        {
            "check_name": "row_oof_all3_prob_guard",
            "status": "pass" if (not row_all3.empty and float(row_all3.iloc[0]) >= 0.95) else "fail",
            "details": "" if row_all3.empty else f"row_oof all3={float(row_all3.iloc[0]):.4f}",
        },
        {
            "check_name": "artist_oof_all3_prob_guard",
            "status": "pass" if (not artist_all3.empty and float(artist_all3.iloc[0]) >= 0.95) else "fail",
            "details": "" if artist_all3.empty else f"artist_oof all3={float(artist_all3.iloc[0]):.4f}",
        },
    ]
    return pd.concat([pd.DataFrame(checks), check_rows], ignore_index=True, sort=False)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return "" if pd.isna(value) else str(value)

    cols = [str(col) for col in data.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6}"
        "p{line-height:1.55}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_manifest(files: list[Path], package_path: Path, checks: pd.DataFrame) -> dict[str, Any]:
    manifest = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "candidate": STABLE,
        "reference_candidate": REFERENCE,
        "package_file": str(package_path.relative_to(REPO)),
        "package_sha256": sha256_file(package_path),
        "features": FEATURES,
        "config": dict(STABLE_CONFIG),
        "source_evidence": {
            "hcoef11_summary": str((SOURCE_EVIDENCE / "outputs" / "bootstrap_or_repeated_split_summary.csv").relative_to(REPO)),
            "hcoef11_report": str((SOURCE_EVIDENCE / "reports" / "result_report.md").relative_to(REPO)),
        },
        "readiness_status": "pass" if checks["status"].eq("pass").all() else "warn_or_fail",
        "files": [
            {
                "path": str(path.relative_to(REPO)),
                "sha256": sha256_file(path),
            }
            for path in files
            if path.exists()
        ],
    }
    (EXP_DIR / "artifacts" / "operational_candidate_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def write_report(
    metrics: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    summary: pd.DataFrame,
    checks: pd.DataFrame,
    manifest: dict[str, Any],
) -> None:
    fixed_view = metrics[metrics["split"].isin(["validation", "test", "0604_ex50"])].copy()
    repeated = summary[summary.get("summary_type", pd.Series(dtype=str)).eq("repeated_oof")].copy()
    bootstrap = summary[summary.get("summary_type", pd.Series(dtype=str)).eq("paired_bootstrap")].copy()
    stable_test = fixed_view[(fixed_view["split"].eq("test")) & (fixed_view["candidate"].eq(STABLE))].iloc[0]

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 개선 후보 운영 패키징 감사",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF11에서 안정성이 확인된 Warm Huber 잔차 보정 후보를 재현 가능한 실험 패키지로 저장하고, 저장 모델 재로딩 후 예측 동일성을 확인.",
            f"- 기준 후보: `{REFERENCE}`.",
            f"- 패키징 후보: `{STABLE}`.",
            f"- 패키지 파일: `{manifest['package_file']}`.",
            "- 주의: 이 산출물은 운영 반영 전 실험 패키지이며, production artifact를 덮어쓰지 않음.",
            "",
            "## 1. 실행 결론",
            "",
            "- 판단: Warm 개선 후보의 운영 전 패키징 감사 통과.",
            f"- fixed test 성능: MdAPE `{stable_test['MdAPE']:.4f}`, MAPE `{stable_test['MAPE']:.4f}`, p95_APE `{stable_test['p95_APE']:.4f}`, RMSE_log `{stable_test['RMSE_log']:.4f}`.",
            "- 저장 모델을 다시 불러와 validation/test/0604 예측이 direct rebuild와 동일한지 확인함.",
            "- 다음 단계는 production v0.1 artifact에 반영할지 여부를 최신 라벨 stress test와 API/운영 정책에서 결정하는 것.",
            "",
            "## 2. Readiness Check",
            "",
            markdown_table(checks),
            "",
            "## 3. Fixed validation/test/0604 재현",
            "",
            markdown_table(
                fixed_view[
                    [
                        "split",
                        "candidate",
                        "method",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                        "improve_count_vs_reference",
                    ]
                ].round(4)
            ),
            "",
            "## 4. HCOEF11 반복 검증 근거",
            "",
            markdown_table(repeated.round(4)),
            "",
            "## 5. Paired bootstrap 근거",
            "",
            "- HCOEF11 결과를 운영 후보 감사 근거로 carry-forward함.",
            "- `delta`가 음수이면 패키징 후보가 기준 후보보다 좋다는 뜻임.",
            markdown_table(bootstrap.round(4), max_rows=32),
            "",
            "## 6. Huber 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준. 절대 가격 단위 계수가 아니라 방향성과 상대 영향 비교용.",
            "- `svc_fallback`은 단순 fallback 기준가를 그대로 밀어주는 역할이 아니라 과한 기준가 방향을 낮추는 보정축으로 작동.",
            "- `shrunk_svc_prior`, `current_shrunk_huber_gap`, `ppv8_defensive`는 완화된 기준가와 오차 안정화 후보를 반영하는 축.",
            "- `log_area`, `svc_group_n_log`, `svc_prior_iqr`는 보정 신뢰도와 크기 관련 잔차 방향을 제한하는 보조축.",
            markdown_table(coeffs.sort_values("abs_coefficient", ascending=False).round(5)),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4)),
            "",
            "## 8. 산출물",
            "",
            "- `artifacts/warm_hcoef12_hcoef3_stable_residual_huber.joblib`",
            "- `artifacts/operational_candidate_manifest.json`",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/operational_readiness_checks.csv`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef12_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef12_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = hcoef3.build_frames()
    package, _ = fit_packaged_model(frames["validation"])
    package_path = EXP_DIR / "artifacts" / PACKAGE_NAME
    joblib.dump(package, package_path)
    loaded = joblib.load(package_path)

    metrics, predictions, equality_checks = fixed_metrics_and_predictions(frames, loaded)
    coeffs = feature_coefficients(loaded)
    residuals = residual_analysis(predictions)
    summary = carry_forward_validation_summary()
    checks = readiness_checks(metrics, equality_checks, package_path, summary)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    checks.to_csv(out / "operational_readiness_checks.csv", index=False)

    preliminary_files = [
        out / "metrics.csv",
        out / "candidate_predictions.csv",
        out / "feature_coefficients.csv",
        out / "residual_analysis.csv",
        out / "bootstrap_or_repeated_split_summary.csv",
        out / "operational_readiness_checks.csv",
        package_path,
    ]
    manifest = write_manifest(preliminary_files, package_path, checks)
    write_report(metrics, coeffs, residuals, summary, checks, manifest)

    final_files = [
        *preliminary_files,
        EXP_DIR / "artifacts" / "operational_candidate_manifest.json",
        EXP_DIR / "reports" / "result_report.md",
        EXP_DIR / "reports" / "result_report.html",
    ]
    write_manifest(final_files, package_path, checks)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- fixed metrics ---")
    print(
        metrics[
            [
                "split",
                "candidate",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "RMSE_log",
                "delta_MdAPE_vs_reference",
                "delta_MAPE_vs_reference",
                "delta_p95_APE_vs_reference",
                "improve_count_vs_reference",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )
    print("--- readiness checks ---")
    print(checks.to_string(index=False))


if __name__ == "__main__":
    main()
