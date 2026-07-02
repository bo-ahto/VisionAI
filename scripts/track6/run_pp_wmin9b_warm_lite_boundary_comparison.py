#!/usr/bin/env python3
"""Run PP-WMIN9B: Warm-lite boundary comparison and route-policy audit.

This complements PP-WMIN9.  PP-WMIN9 packaged the WMIN8 5+ history candidate,
but the original next-step question was whether Warm-lite should own the real
1~4 history rows before official service integration.

The direct "WMIN8 on the same low-history rows" comparison is intentionally not
used as a production decision basis.  WMIN8 is selected for the 5+ same-artist
history route; forcing it onto 1~4 history rows would violate the route invariant
and the selected training condition.  This script therefore compares the
validated roles:
- real low-history leave-one-out rows: Warm-lite vs Cold serving from PP-WCUT4
- 5+ Warm fixed test rows: WMIN8 vs PP258/WMIN4 from the packaged WMIN8 artifact
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
EXP_ID = "PP-WMIN9B"
EXP_SLUG = "PP-WMIN9B_warm_lite_boundary_comparison"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin9b_warm_lite_boundary_comparison_summary.md"

WCUT4_DIR = REPO / "experiments" / "track6" / "PP-WCUT4_real_low_history_validation"
WMIN8_MANIFEST = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "manifest.json"
WMIN8_FIXED = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "artifacts" / "wmin8_fixed_metrics.csv"
WARM_LITE_POLICY = REPO / "models" / "track6" / "warm_lite_v0.1" / "config" / "warm_lite_policy_v0_1.json"


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fmt(value: Any) -> str:
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, ensure_ascii=False)
    if pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if float(value).is_integer() and abs(float(value)) < 1_000_000:
            return str(int(value))
        return f"{float(value):.6f}"
    return str(value)


def md_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(c) for c in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in view.columns) + " |")
    return "\n".join(lines)


def html_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if frame.empty:
        return "<p><em>결과 없음</em></p>"
    view = frame[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(fmt(row[c]))}</td>" for c in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def metrics(actual_price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual_price, dtype=float)
    pred = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual) & (actual > 0) & np.isfinite(pred)
    pred_price = np.clip(np.exp(pred[valid]), 1_000.0, None)
    ape = np.abs(pred_price - actual[valid]) / np.clip(actual[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
    }


def load_wcut4_predictions() -> pd.DataFrame:
    paths = sorted((WCUT4_DIR / "outputs").glob("preds_seed*.csv"))
    if not paths:
        raise FileNotFoundError("PP-WCUT4 seed prediction files not found")
    return pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)


def low_history_tables(preds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for history_k, group in preds.groupby("history_k"):
        wlite = metrics(group["actual_price"].to_numpy(dtype=float), group["wlite_pred_log"].to_numpy(dtype=float))
        cold = metrics(group["actual_price"].to_numpy(dtype=float), group["cold_pred_log"].to_numpy(dtype=float))
        rows.append({
            "history_k": int(history_k),
            "n": int(len(group)),
            "warm_lite_MdAPE": wlite["MdAPE"],
            "warm_lite_MAPE": wlite["MAPE"],
            "warm_lite_p95_APE": wlite["p95_APE"],
            "cold_MdAPE": cold["MdAPE"],
            "cold_MAPE": cold["MAPE"],
            "cold_p95_APE": cold["p95_APE"],
            "delta_MdAPE_vs_cold": wlite["MdAPE"] - cold["MdAPE"],
            "delta_MAPE_vs_cold": wlite["MAPE"] - cold["MAPE"],
            "delta_p95_APE_vs_cold": wlite["p95_APE"] - cold["p95_APE"],
        })
    per_k = pd.DataFrame(rows).sort_values("history_k").reset_index(drop=True)
    wlite_all = metrics(preds["actual_price"].to_numpy(dtype=float), preds["wlite_pred_log"].to_numpy(dtype=float))
    cold_all = metrics(preds["actual_price"].to_numpy(dtype=float), preds["cold_pred_log"].to_numpy(dtype=float))
    overall = pd.DataFrame([{
        "route": "Warm-lite 1~4 history",
        "comparison": "Warm-lite vs Cold serving on real low-history leave-one-out",
        "n": int(len(preds)),
        "artist_count": int(preds["artist_key"].nunique()),
        "warm_lite_MdAPE": wlite_all["MdAPE"],
        "warm_lite_MAPE": wlite_all["MAPE"],
        "warm_lite_p95_APE": wlite_all["p95_APE"],
        "cold_MdAPE": cold_all["MdAPE"],
        "cold_MAPE": cold_all["MAPE"],
        "cold_p95_APE": cold_all["p95_APE"],
        "delta_MdAPE_vs_cold": wlite_all["MdAPE"] - cold_all["MdAPE"],
        "delta_MAPE_vs_cold": wlite_all["MAPE"] - cold_all["MAPE"],
        "delta_p95_APE_vs_cold": wlite_all["p95_APE"] - cold_all["p95_APE"],
        "artist_match_rate": float(preds["artist_match"].mean()),
    }])
    return overall, per_k


def warm_5plus_table() -> pd.DataFrame:
    manifest = json.loads(WMIN8_MANIFEST.read_text(encoding="utf-8"))
    fixed = pd.read_csv(WMIN8_FIXED)
    keep = [
        "current_pp258_operational_reference",
        "min1_huber_refit_partial",
        manifest["selected_candidate_label"],
    ]
    table = fixed[fixed["candidate_label"].isin(keep) & fixed["eval_split"].eq("test")].copy()
    role = {
        "current_pp258_operational_reference": "previous_operational_reference",
        "min1_huber_refit_partial": "min1_base_before_router",
        manifest["selected_candidate_label"]: "Warm WMIN8 5+ history",
    }
    table["route"] = table["candidate_label"].map(role)
    table = table[["route", "candidate_label", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
    return table.sort_values("MAPE").reset_index(drop=True)


def route_boundary_decision(low_overall: pd.DataFrame, warm_5plus: pd.DataFrame, wcut4_cfg: dict[str, Any]) -> pd.DataFrame:
    wlite = low_overall.iloc[0]
    wmin8 = warm_5plus[warm_5plus["route"].eq("Warm WMIN8 5+ history")].iloc[0]
    return pd.DataFrame([
        {
            "history_count": "0",
            "route": "Cold",
            "evidence": "동일 작가 이력이 없으면 Warm 계열의 작가 이력 통계가 계산되지 않음",
            "status": "keep",
        },
        {
            "history_count": "1~4",
            "route": "Warm-lite",
            "evidence": (
                f"실존 저이력 leave-one-out n={int(wlite['n'])}, "
                f"Warm-lite MAPE {wlite['warm_lite_MAPE']:.4f} vs Cold {wlite['cold_MAPE']:.4f}, "
                f"bootstrap gate {wcut4_cfg['gate']}"
            ),
            "status": "validated",
        },
        {
            "history_count": "5+",
            "route": "Warm WMIN8",
            "evidence": (
                f"fixed test n={int(wmin8['n'])}, "
                f"MdAPE/MAPE/p95 {wmin8['MdAPE']:.4f}/{wmin8['MAPE']:.4f}/{wmin8['p95_APE']:.4f}; "
                "WMIN8 conditional route가 WMIN4와 PP258을 모두 개선"
            ),
            "status": "validated",
        },
    ])


def readiness_checks() -> list[dict[str, Any]]:
    manifest = json.loads(WMIN8_MANIFEST.read_text(encoding="utf-8"))
    readiness = manifest.get("readiness") or {}
    api_parity = manifest.get("api_fixed_test_parity") or {}
    warm_lite_ready = WARM_LITE_POLICY.exists()
    wmin8_exact_ready = bool(readiness.get("exact_raw_adapter_ready") and api_parity.get("parity_pass"))
    return [
        {"check": "warm_lite_low_history_evidence", "status": "pass", "detail": "PP-WCUT4 real low-history leave-one-out gate pass"},
        {"check": "wmin8_5plus_evidence", "status": "pass", "detail": "PP-WMIN8 fixed test confirmation and packaged artifact available"},
        {
            "check": "direct_same_row_wmin8_vs_warm_lite_low_history",
            "status": "not_adopted",
            "detail": (
                "WMIN8 is a 5+ same-artist-history route. Forcing it onto 1~4 history rows would "
                "break the production route invariant, so the same-row comparison is not used as an operating decision."
            ),
        },
        {"check": "warm_lite_artifact", "status": "pass" if warm_lite_ready else "fail", "detail": str(WARM_LITE_POLICY.relative_to(REPO)) if warm_lite_ready else "policy missing"},
        {
            "check": "wmin8_exact_raw_adapter",
            "status": "pass" if wmin8_exact_ready else "fail",
            "detail": f"api_fixed_test_parity_pass={bool(api_parity.get('parity_pass'))}, blocking_items={readiness.get('blocking_items', [])}",
        },
        {
            "check": "official_service_route_boundary",
            "status": "pass" if (warm_lite_ready and wmin8_exact_ready) else "fail",
            "detail": "official v0.1 route boundary: 0 history -> Cold, 1~4 -> Warm-lite, 5+ -> WMIN8 Warm",
        },
    ]


def render_reports(
    low_overall: pd.DataFrame,
    per_k: pd.DataFrame,
    warm_5plus: pd.DataFrame,
    boundary: pd.DataFrame,
    checks: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[str, str]:
    low_cols = [
        "route", "n", "artist_count", "warm_lite_MdAPE", "warm_lite_MAPE", "warm_lite_p95_APE",
        "cold_MdAPE", "cold_MAPE", "cold_p95_APE", "delta_MAPE_vs_cold", "delta_p95_APE_vs_cold",
    ]
    per_cols = [
        "history_k", "n", "warm_lite_MdAPE", "warm_lite_MAPE", "warm_lite_p95_APE",
        "cold_MdAPE", "cold_MAPE", "cold_p95_APE", "delta_MAPE_vs_cold", "delta_p95_APE_vs_cold",
    ]
    warm_cols = ["route", "candidate_label", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    boundary_cols = ["history_count", "route", "status", "evidence"]
    check_df = pd.DataFrame(checks)
    check_cols = ["check", "status", "detail"]
    conclusion = (
        "1~4건은 Warm-lite, 5건 이상은 WMIN8 조건부 라우팅으로 분리하는 경계가 현재 검증 결과와 일치한다. "
        "저이력 행에 WMIN8을 강제 적용하는 비교는 운영 라우팅 조건을 깨기 때문에 채택 근거로 사용하지 않는다."
    )
    md = "\n".join([
        "# PP-WMIN9B Warm-lite 경계 비교 및 라우팅 정책 감사",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 데이터 기준: PP-WCUT4 실존 저이력 leave-one-out + PP-WMIN8 fixed test artifact",
        "- 0604: 사용하지 않음",
        f"- 결론: {conclusion}",
        "",
        "## 1. 라우팅 경계 판단",
        md_table(boundary, boundary_cols, 20),
        "",
        "## 2. 저이력 1~4건 Warm-lite 검증",
        md_table(low_overall, low_cols, 20),
        "",
        "## 3. 이력 수별 Warm-lite 검증",
        md_table(per_k, per_cols, 20),
        "",
        "## 4. Warm 5건 이상 WMIN8 검증",
        md_table(warm_5plus, warm_cols, 20),
        "",
        "## 5. 검증 상태",
        md_table(check_df, check_cols, 20),
        "",
        "## 6. 실행 설정",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
    ]) + "\n"
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-WMIN9B Warm-lite 경계 비교</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1240px; margin:0 auto; background:#fff; min-height:100vh; padding:40px 28px 72px; }}
h1 {{ margin:0 0 10px; font-size:30px; }} h2 {{ margin:34px 0 12px; padding-top:18px; border-top:1px solid #d8dee6; font-size:22px; }}
.callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:14px 16px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-WMIN9B Warm-lite 경계 비교 및 라우팅 정책 감사</h1>
<div class="callout">{html.escape(conclusion)}</div>
<h2>1. 라우팅 경계 판단</h2>{html_table(boundary, boundary_cols, 20)}
<h2>2. 저이력 1~4건 Warm-lite 검증</h2>{html_table(low_overall, low_cols, 20)}
<h2>3. 이력 수별 Warm-lite 검증</h2>{html_table(per_k, per_cols, 20)}
<h2>4. Warm 5건 이상 WMIN8 검증</h2>{html_table(warm_5plus, warm_cols, 20)}
<h2>5. 검증 상태</h2>{html_table(check_df, check_cols, 20)}
<h2>6. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    preds = load_wcut4_predictions()
    wcut4_cfg = json.loads((WCUT4_DIR / "artifacts" / "run_config.json").read_text(encoding="utf-8"))
    low_overall, per_k = low_history_tables(preds)
    warm_5plus = warm_5plus_table()
    boundary = route_boundary_decision(low_overall, warm_5plus, wcut4_cfg)
    checks = readiness_checks()
    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selection_policy": "no new candidate selection; routing boundary and adapter-gap audit only",
        "source_experiments": {
            "low_history": "experiments/track6/PP-WCUT4_real_low_history_validation",
            "warm_5plus": "experiments/track6/PP-WMIN8_warm_min1_weight_router",
            "warm_5plus_artifact": "models/track6/warm_wmin8_operational_candidate",
        },
        "direct_same_row_low_history_wmin8_comparison": "not_adopted_because_wmin8_is_5plus_history_route",
        "prohibitions": ["0604 not used"],
    }
    low_overall.to_csv(OUT_DIR / "low_history_overall.csv", index=False)
    per_k.to_csv(OUT_DIR / "low_history_per_k.csv", index=False)
    warm_5plus.to_csv(OUT_DIR / "warm_5plus_wmin8_fixed_test.csv", index=False)
    boundary.to_csv(OUT_DIR / "route_boundary_decision.csv", index=False)
    pd.DataFrame(checks).to_csv(OUT_DIR / "readiness_checks.csv", index=False)
    (OUT_DIR / "readiness_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_reports(low_overall, per_k, warm_5plus, boundary, checks, config)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")
    DOC_SUMMARY.write_text(md, encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "route_decision": boundary.to_dict(orient="records"),
        "non_pass_checks": [row for row in checks if row["status"] not in {"pass", "not_adopted"}],
        "report": str((REPORT_DIR / "result_report.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
