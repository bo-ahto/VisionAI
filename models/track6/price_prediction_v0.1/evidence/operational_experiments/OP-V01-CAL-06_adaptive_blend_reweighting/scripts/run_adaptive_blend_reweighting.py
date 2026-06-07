from __future__ import annotations

import html
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[7]
EXP_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

HISTORICAL_PREDICTIONS = (
    REPO
    / "experiments/track6/PP-SVC6_warm_fallback_ppv8_blend_stability/outputs/predictions.csv"
)
OPERATIONAL_0604 = (
    REPO
    / "models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/operational_predictions_with_actual.csv"
)

BASELINE = "pp_v8"
SVC = "svc"
WEIGHTS = [round(x, 2) for x in np.arange(0.0, 1.0001, 0.05)]
MIN_N_THRESHOLDS = [5, 10, 20, 50, 100]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def metric_row(frame: pd.DataFrame, scope: str, candidate: str, pred_col: str) -> dict[str, object]:
    actual = frame["actual_price"].astype(float)
    pred = np.exp(frame[pred_col].astype(float))
    ape = ((pred - actual).abs() / actual).replace([np.inf, -np.inf], np.nan)
    ratio = (pred / actual).replace([np.inf, -np.inf], np.nan)
    valid = ape.notna() & ratio.notna() & actual.gt(0)
    if valid.sum() == 0:
        return {
            "scope": scope,
            "candidate": candidate,
            "n": 0,
            "MdAPE": np.nan,
            "MAPE": np.nan,
            "p95_APE": np.nan,
            "RMSE_log": np.nan,
            "median_ratio": np.nan,
            "over_3x_n": 0,
            "under_1_3x_n": 0,
            "within_30": np.nan,
            "within_50": np.nan,
        }
    log_error = frame.loc[valid, pred_col].astype(float) - np.log(actual.loc[valid])
    ape_valid = ape.loc[valid]
    ratio_valid = ratio.loc[valid]
    return {
        "scope": scope,
        "candidate": candidate,
        "n": int(valid.sum()),
        "MdAPE": float(ape_valid.median()),
        "MAPE": float(ape_valid.mean()),
        "p95_APE": float(ape_valid.quantile(0.95)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
        "median_ratio": float(ratio_valid.median()),
        "over_3x_n": int((ratio_valid > 3.0).sum()),
        "under_1_3x_n": int((ratio_valid < (1.0 / 3.0)).sum()),
        "within_30": float((ape_valid <= 0.30).mean()),
        "within_50": float((ape_valid <= 0.50).mean()),
    }


def load_historical_wide() -> pd.DataFrame:
    raw = pd.read_csv(HISTORICAL_PREDICTIONS)
    keep_candidates = {
        "pp_v8_compact_blend_mape_guarded": BASELINE,
        "fallback_numeric": SVC,
    }
    raw = raw[raw["candidate"].isin(keep_candidates)].copy()
    raw["component"] = raw["candidate"].map(keep_candidates)
    index_cols = [
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]
    wide = raw.pivot_table(
        index=index_cols,
        columns="component",
        values="pred_log",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.dropna(subset=[BASELINE, SVC, "actual_price"]).copy()
    wide["source_scope"] = "historical"
    return wide


def load_0604_wide() -> pd.DataFrame:
    raw = pd.read_csv(OPERATIONAL_0604)
    actual = pd.to_numeric(raw["actual_price_krw"], errors="coerce")
    actual_usd = pd.to_numeric(raw["actual_price_usd_equiv"], errors="coerce")
    wide = pd.DataFrame(
        {
            "split": "0604_labeled",
            "_track6_row_id": raw.get("_track6_row_id"),
            "actual_price": actual,
            "actual_usd_equiv": actual_usd,
            "artist_key": raw.get("artist_key"),
            "artist_name_ko": raw.get("artist_name"),
            "svc_group_level": raw.get("svc_group_level"),
            "svc_coverage_tier": raw.get("svc_coverage_tier"),
            "svc_group_n": pd.to_numeric(raw.get("svc_group_n"), errors="coerce"),
            BASELINE: pd.to_numeric(raw["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce"),
            SVC: pd.to_numeric(raw["svc_numeric_seed_mean_pred_log"], errors="coerce"),
        }
    )
    wide = wide.dropna(subset=[BASELINE, SVC, "actual_price"]).copy()
    wide = wide[wide["actual_price"] > 0].copy()
    wide["source_scope"] = "0604"
    return wide


def add_candidate_predictions(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    out = frame.copy()
    candidate_cols: list[str] = []
    out["cand_ppv8_baseline"] = out[BASELINE]
    out["cand_svc_only"] = out[SVC]
    candidate_cols.extend(["cand_ppv8_baseline", "cand_svc_only"])

    for weight in WEIGHTS:
        name = f"cand_global_svc_w{weight:.2f}"
        out[name] = weight * out[SVC] + (1.0 - weight) * out[BASELINE]
        candidate_cols.append(name)

    svc_group_n = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0)
    coverage = out["svc_coverage_tier"].astype(str).str.lower()
    coverage_ok = ~coverage.isin({"low", "none", "nan", ""})

    for min_n in MIN_N_THRESHOLDS:
        for weight in [0.50, 0.60, 0.70, 0.80]:
            blend = weight * out[SVC] + (1.0 - weight) * out[BASELINE]
            name = f"cand_gate_n{min_n}_svc_w{weight:.2f}"
            out[name] = np.where(svc_group_n >= min_n, blend, out[BASELINE])
            candidate_cols.append(name)

            name_cov = f"cand_gate_n{min_n}_covok_svc_w{weight:.2f}"
            out[name_cov] = np.where((svc_group_n >= min_n) & coverage_ok, blend, out[BASELINE])
            candidate_cols.append(name_cov)

    return out, candidate_cols


def evaluate(frame: pd.DataFrame, candidate_cols: Iterable[str], scope_prefix: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split, split_frame in frame.groupby("split"):
        for candidate in candidate_cols:
            rows.append(metric_row(split_frame, f"{scope_prefix}:{split}", candidate, candidate))

    if "actual_usd_equiv" in frame.columns:
        core = frame[pd.to_numeric(frame["actual_usd_equiv"], errors="coerce") >= 50].copy()
        for candidate in candidate_cols:
            rows.append(metric_row(core, f"{scope_prefix}:0604_excluding_under_50_usd", candidate, candidate))

    return pd.DataFrame(rows)


def select_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    validation = metrics[metrics["scope"].eq("historical:validation")].copy()
    test = metrics[metrics["scope"].eq("historical:test")].copy()
    if validation.empty:
        return pd.DataFrame()

    baseline = validation[validation["candidate"].eq("cand_ppv8_baseline")].iloc[0]
    guarded = validation[
        (validation["MdAPE"] <= baseline["MdAPE"] + 0.005)
        & (validation["p95_APE"] <= baseline["p95_APE"] + 0.005)
    ].copy()
    if guarded.empty:
        guarded = validation.copy()

    selected = guarded.sort_values(["MAPE", "MdAPE", "p95_APE"]).head(10).copy()
    selected["selection_rule"] = "validation_mape_with_mdape_p95_guard"

    test_lookup = test.set_index("candidate")
    rows = []
    for row in selected.to_dict("records"):
        candidate = row["candidate"]
        merged = {
            "candidate": candidate,
            "selection_rule": row["selection_rule"],
            "validation_MdAPE": row["MdAPE"],
            "validation_MAPE": row["MAPE"],
            "validation_p95_APE": row["p95_APE"],
        }
        if candidate in test_lookup.index:
            t = test_lookup.loc[candidate]
            merged.update(
                {
                    "test_MdAPE": t["MdAPE"],
                    "test_MAPE": t["MAPE"],
                    "test_p95_APE": t["p95_APE"],
                    "test_over_3x_n": t["over_3x_n"],
                    "test_under_1_3x_n": t["under_1_3x_n"],
                }
            )
        rows.append(merged)
    return pd.DataFrame(rows)


def simple_html(title: str, markdown_text: str, tables: dict[str, pd.DataFrame]) -> str:
    body = ["<!doctype html><html><head><meta charset='utf-8'>"]
    body.append(
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:32px;color:#1f2933}"
        "h1,h2{color:#111827}table{border-collapse:collapse;width:100%;margin:16px 0;font-size:13px}"
        "th,td{border:1px solid #d8dee9;padding:7px 9px;text-align:right}th:first-child,td:first-child{text-align:left}"
        "th{background:#edf2f7}.note{background:#f8fafc;border-left:4px solid #4f46e5;padding:12px 14px;white-space:pre-wrap}</style>"
    )
    body.append(f"<title>{html.escape(title)}</title></head><body>")
    body.append(f"<h1>{html.escape(title)}</h1>")
    body.append(f"<div class='note'>{html.escape(markdown_text)}</div>")
    for table_title, df in tables.items():
        body.append(f"<h2>{html.escape(table_title)}</h2>")
        body.append(df.to_html(index=False, escape=True, float_format=lambda x: f"{x:.4f}"))
    body.append("</body></html>")
    return "\n".join(body)


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_결과 없음_"
    view = df.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    formatted = view.copy()
    for col in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[col]):
            formatted[col] = formatted[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            formatted[col] = formatted[col].map(lambda x: "" if pd.isna(x) else str(x))
    columns = [str(col) for col in formatted.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in formatted.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in formatted.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()

    historical = load_historical_wide()
    operational_0604 = load_0604_wide()

    historical_candidates, candidate_cols = add_candidate_predictions(historical)
    operational_candidates, _ = add_candidate_predictions(operational_0604)

    historical_metrics = evaluate(historical_candidates, candidate_cols, "historical")
    operational_metrics = evaluate(operational_candidates, candidate_cols, "0604")
    all_metrics = pd.concat([historical_metrics, operational_metrics], ignore_index=True)

    selected = select_candidates(all_metrics)

    baseline_rows = all_metrics[all_metrics["candidate"].eq("cand_ppv8_baseline")].copy()
    selected_candidates = set(selected["candidate"].tolist()) | {"cand_ppv8_baseline", "cand_svc_only", "cand_global_svc_w0.70"}
    selected_metric_rows = all_metrics[all_metrics["candidate"].isin(selected_candidates)].copy()

    # 0604에서는 라벨 검수 전 전체 MAPE보다 50달러 미만 제외 지표를 우선 확인한다.
    op_core = all_metrics[
        all_metrics["scope"].eq("0604:0604_excluding_under_50_usd")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"])

    all_metrics.to_csv(OUT_DIR / "candidate_metrics_all_scopes.csv", index=False)
    selected.to_csv(OUT_DIR / "validation_selected_candidates.csv", index=False)
    selected_metric_rows.to_csv(OUT_DIR / "selected_candidate_metrics_all_scopes.csv", index=False)
    op_core.head(30).to_csv(OUT_DIR / "0604_core_top_candidates.csv", index=False)
    baseline_rows.to_csv(OUT_DIR / "baseline_metrics.csv", index=False)

    hist_baseline_test = all_metrics[
        all_metrics["scope"].eq("historical:test")
        & all_metrics["candidate"].eq("cand_ppv8_baseline")
    ].iloc[0]
    hist_best_test = selected.sort_values(["test_MAPE", "test_MdAPE"]).iloc[0] if not selected.empty else None
    op_baseline = op_core[op_core["candidate"].eq("cand_ppv8_baseline")].iloc[0]
    op_best = op_core.iloc[0]

    summary_lines = [
        "- 기준 후보: PP-V8 compact_blend_mape_guarded",
        "- 비교 방향: 유사 작품 기반 예측값과 PP-V8의 로그 가격 결합",
        "- 후보 선택: historical validation에서 MAPE를 우선하되 MdAPE/p95 악화 제한",
        "- 0604 신규 라벨: 후보 선택에는 사용하지 않고 외부 확인용으로만 사용",
        "",
        "핵심 결과:",
        f"- historical test PP-V8 기준 MAPE: {hist_baseline_test['MAPE']:.4f}, MdAPE: {hist_baseline_test['MdAPE']:.4f}, p95_APE: {hist_baseline_test['p95_APE']:.4f}",
    ]
    if hist_best_test is not None:
        summary_lines.append(
            f"- validation 선택 후보 중 historical test 최선: {hist_best_test['candidate']} / "
            f"MAPE {hist_best_test['test_MAPE']:.4f}, MdAPE {hist_best_test['test_MdAPE']:.4f}, p95_APE {hist_best_test['test_p95_APE']:.4f}"
        )
    summary_lines.extend(
        [
            f"- 0604 50달러 미만 제외 PP-V8 기준 MAPE: {op_baseline['MAPE']:.4f}, MdAPE: {op_baseline['MdAPE']:.4f}, p95_APE: {op_baseline['p95_APE']:.4f}",
            f"- 0604 50달러 미만 제외 단순 스캔 최선: {op_best['candidate']} / MAPE {op_best['MAPE']:.4f}, MdAPE {op_best['MdAPE']:.4f}, p95_APE {op_best['p95_APE']:.4f}",
            "",
            "판단:",
            "- historical split에서는 결합 비율 재조정으로 성능 개선 여지가 있다.",
            "- 0604에서는 PP-V8 단독 또는 PP-V8에 가까운 낮은 결합 비율이 유리한지 확인이 필요하다.",
            "- 따라서 이 실험 결과만으로 v0.1 기본 점가격을 바꾸지 않는다.",
            "- 다음 보정은 전체 결합이 아니라 표본 수/coverage 조건부 결합 후보만 별도 API 후보로 내려 비교하는 방식이 안전하다.",
        ]
    )
    summary_text = "\n".join(summary_lines)

    report = f"""# OP-V01-CAL-06 유사 작품 기반 예측값 결합 비율 재검증 결과

## 1. 실행 요약

{summary_text}

## 2. validation 선택 후보

{dataframe_to_markdown(selected)}

## 3. 선택 후보 전체 scope 지표

{dataframe_to_markdown(selected_metric_rows.sort_values(["scope", "MAPE", "MdAPE"]))}

## 4. 0604 50달러 미만 제외 상위 후보

{dataframe_to_markdown(op_core, max_rows=20)}

## 5. 산출물

- `outputs/candidate_metrics_all_scopes.csv`
- `outputs/validation_selected_candidates.csv`
- `outputs/selected_candidate_metrics_all_scopes.csv`
- `outputs/0604_core_top_candidates.csv`
- `outputs/baseline_metrics.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")

    html_report = simple_html(
        "OP-V01-CAL-06 유사 작품 기반 예측값 결합 비율 재검증 결과",
        summary_text,
        {
            "validation 선택 후보": selected,
            "선택 후보 전체 scope 지표": selected_metric_rows.sort_values(["scope", "MAPE", "MdAPE"]),
            "0604 50달러 미만 제외 상위 후보": op_core.head(20),
        },
    )
    (REPORT_DIR / "result_report.html").write_text(html_report, encoding="utf-8")


if __name__ == "__main__":
    main()
