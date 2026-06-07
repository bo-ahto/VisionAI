#!/usr/bin/env python3
"""Run PP-SVC9: svc fine-match-only gate.

PP-SVC8 showed svc beats pp_v8 ONLY at the finest comparable match level
(``artist_medium_support_size``) and blows up (2-3x variance) at coarser levels.
PP-SVC9 tests whether using svc only at that finest level (pp_v8 elsewhere)
strictly dominates the operational default pp_v8 on BOTH the fixed test and the
0604 new-label set.

Discipline:
- The gate level set is fixed by the PP-SVC8 variance argument (NOT selected on 0604).
- Only the in-gate weight ``w_fine`` is selected on the fixed validation finest subset.
- Fixed test and 0604 are confirmation regimes.
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
EXP_ID = "PP-SVC9"
EXP_SLUG = "PP-SVC9_warm_svc_fine_match_gate"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Warm svc 최정밀 매칭 게이트 (fine-match-only)"

FIXED_PREDICTIONS = REPO / "experiments" / "track6" / "PP-SVC2_warm_comparable_stats_stability" / "outputs" / "predictions.csv"
OPS_0604 = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

SVC_COL = "svc_numeric_seed_mean"
PPV8_COL = "pp_v8_compact_blend_mape_guarded"
FINE_LEVEL = "artist_medium_support_size"            # structural, from PP-SVC8
W_FINE_GRID = [0.5, 0.7, 1.0]
BLEND_REFERENCE_W = 0.70
TOLERANCE = 1e-9


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {"n": int(len(frame)), "MdAPE": float(np.median(ape)),
            "MAPE": float(np.mean(ape)), "p95_APE": float(np.quantile(ape, 0.95))}


def load_fixed() -> dict[str, pd.DataFrame]:
    long = pd.read_csv(FIXED_PREDICTIONS, low_memory=False)
    long = long[long["split"].isin(["validation", "test"])].copy()
    base = long[["split", "_track6_row_id", "actual_log", "actual_price", "svc_group_level"]].drop_duplicates(["split", "_track6_row_id"])
    wide = long.pivot_table(index=["split", "_track6_row_id"], columns="candidate", values="pred_log", aggfunc="last").reset_index()
    wide.columns.name = None
    out = base.merge(wide[["split", "_track6_row_id", SVC_COL, PPV8_COL]], on=["split", "_track6_row_id"], how="inner")
    out = out.rename(columns={SVC_COL: "svc", PPV8_COL: "ppv8"}).dropna(subset=["svc", "ppv8", "actual_price"])
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__").astype(str)
    return {"validation": out[out["split"] == "validation"].reset_index(drop=True),
            "test": out[out["split"] == "test"].reset_index(drop=True)}


def load_0604() -> pd.DataFrame:
    df = pd.read_csv(OPS_0604, low_memory=False)
    df = df[df["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(df.get("actual_price_usd_equiv"), errors="coerce")
    df = df[~(usd < 50.0)].copy()
    out = pd.DataFrame({
        "actual_price": pd.to_numeric(df["actual_price_krw"], errors="coerce"),
        "svc": pd.to_numeric(df["svc_numeric_seed_mean_pred_log"], errors="coerce"),
        "ppv8": pd.to_numeric(df["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce"),
        "svc_group_level": df["svc_group_level"].fillna("__MISSING__").astype(str),
    })
    out["actual_log"] = np.log(np.clip(out["actual_price"].to_numpy(dtype=float), 1.0, None))
    return out.dropna(subset=["svc", "ppv8", "actual_price"]).reset_index(drop=True)


def gate_pred(frame: pd.DataFrame, gate_levels: set[str], w_fine: float) -> np.ndarray:
    in_gate = frame["svc_group_level"].isin(gate_levels).to_numpy()
    svc = frame["svc"].to_numpy(dtype=float)
    ppv8 = frame["ppv8"].to_numpy(dtype=float)
    blended = w_fine * svc + (1.0 - w_fine) * ppv8
    return np.where(in_gate, blended, ppv8)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_결과 없음_"

    def fmt(v: Any) -> str:
        if isinstance(v, (float, np.floating)):
            return f"{float(v):.4f}"
        return str(v)

    cols = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush() -> None:
        if not table:
            return
        rows = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line); continue
        flush()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush()
    style = "body{font-family:-apple-system,Segoe UI,sans-serif;margin:32px;color:#1f2937}table{border-collapse:collapse;margin:12px 0}th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}th{background:#f3f4f6}"
    return f"<!doctype html><html lang=ko><head><meta charset=utf-8><title>{html.escape(EXP_ID)}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def main() -> None:
    ensure_dirs()
    fixed = load_fixed()
    frames = {"validation": fixed["validation"], "test": fixed["test"], "0604": load_0604()}

    # Select w_fine on fixed validation finest subset only.
    val = frames["validation"]
    val_fine = val[val["svc_group_level"] == FINE_LEVEL]
    sel_rows: list[dict[str, Any]] = []
    for w in W_FINE_GRID:
        pred = w * val_fine["svc"].to_numpy(dtype=float) + (1.0 - w) * val_fine["ppv8"].to_numpy(dtype=float)
        m = metric(val_fine, pred)
        sel_rows.append({"w_fine": w, "val_fine_n": m["n"], "val_fine_MdAPE": m["MdAPE"], "val_fine_MAPE": m["MAPE"]})
    sel_df = pd.DataFrame(sel_rows)
    w_fine = float(sel_df.sort_values(["val_fine_MdAPE", "val_fine_MAPE"]).iloc[0]["w_fine"])

    gate_levels = {FINE_LEVEL}
    gate_plus = {FINE_LEVEL, "artist_size"}

    candidates: dict[str, dict[str, np.ndarray]] = {
        "pp_v8": {r: f["ppv8"].to_numpy(dtype=float) for r, f in frames.items()},
        f"blend_{BLEND_REFERENCE_W:.2f}": {r: BLEND_REFERENCE_W * f["svc"].to_numpy(dtype=float) + (1 - BLEND_REFERENCE_W) * f["ppv8"].to_numpy(dtype=float) for r, f in frames.items()},
        f"fine_gate_w{w_fine:.2f}": {r: gate_pred(f, gate_levels, w_fine) for r, f in frames.items()},
        f"fine_gate_plus_artist_size_w{w_fine:.2f}": {r: gate_pred(f, gate_plus, w_fine) for r, f in frames.items()},
    }

    metric_rows: list[dict[str, Any]] = []
    for cand, region_preds in candidates.items():
        for region, pred in region_preds.items():
            metric_rows.append({"candidate": cand, "region": region, **metric(frames[region], pred)})
    metrics_df = pd.DataFrame(metric_rows)

    # Gate-applied subset comparison (svc vs pp_v8 on the gated rows only).
    sub_rows: list[dict[str, Any]] = []
    for region, f in frames.items():
        g = f[f["svc_group_level"] == FINE_LEVEL]
        if g.empty:
            continue
        svc_pred = w_fine * g["svc"].to_numpy(dtype=float) + (1 - w_fine) * g["ppv8"].to_numpy(dtype=float)
        sub_rows.append({
            "region": region, "fine_n": int(len(g)), "fine_share_pct": round(100 * len(g) / len(f), 1),
            "gate_MdAPE": metric(g, svc_pred)["MdAPE"], "ppv8_MdAPE": metric(g, g["ppv8"].to_numpy())["MdAPE"],
            "gate_MAPE": metric(g, svc_pred)["MAPE"], "ppv8_MAPE": metric(g, g["ppv8"].to_numpy())["MAPE"],
        })
    sub_df = pd.DataFrame(sub_rows)

    out = EXP_DIR / "outputs"
    metrics_df.to_csv(out / "region_candidate_metrics.csv", index=False)
    sub_df.to_csv(out / "gate_applied_subset_compare.csv", index=False)
    sel_df.to_csv(out / "w_fine_validation_selection.csv", index=False)

    pivot = metrics_df.pivot(index="candidate", columns="region", values="MdAPE").reset_index()[["candidate", "validation", "test", "0604"]]
    mape_pivot = metrics_df.pivot(index="candidate", columns="region", values="MAPE").reset_index()[["candidate", "validation", "test", "0604"]]

    gate_name = f"fine_gate_w{w_fine:.2f}"

    def region_val(cand: str, region: str, col: str) -> float:
        r = metrics_df[(metrics_df["candidate"] == cand) & (metrics_df["region"] == region)]
        return float(r[col].iloc[0])

    # Verdict: gate vs pp_v8 on test and 0604 (MdAPE + MAPE non-worse).
    checks = {}
    for region in ["test", "0604"]:
        checks[region] = {
            "mdape_delta": region_val(gate_name, region, "MdAPE") - region_val("pp_v8", region, "MdAPE"),
            "mape_delta": region_val(gate_name, region, "MAPE") - region_val("pp_v8", region, "MAPE"),
        }
    test_ok = checks["test"]["mdape_delta"] <= TOLERANCE and checks["test"]["mape_delta"] <= TOLERANCE
    ops_ok = checks["0604"]["mdape_delta"] <= TOLERANCE and checks["0604"]["mape_delta"] <= TOLERANCE
    improves = (checks["test"]["mdape_delta"] < -TOLERANCE) or (checks["0604"]["mdape_delta"] < -TOLERANCE)
    if test_ok and ops_ok and improves:
        strong = checks["test"]["mdape_delta"] < -TOLERANCE and checks["0604"]["mdape_delta"] < -TOLERANCE
        verdict = "강한 채택: pp_v8 순지배(두 영역 MdAPE 개선)" if strong else "채택: pp_v8 비악화 + 최소 한 영역 개선"
    elif ops_ok and improves:
        verdict = "보조 채택: 0604 개선, 고정 test 비악화"
    else:
        verdict = "중단: 한 영역에서 pp_v8 대비 악화"

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 게이트 레벨(구조적, PP-SVC8): `{FINE_LEVEL}`",
        f"- in-gate weight w_fine = {w_fine} (고정 validation 최정밀 subset에서 선택)",
        "- 비교 기준: 운영 기본값 pp_v8. (70:30은 0604에서 붕괴하므로 비교 목표 아님)",
        "",
        "## 1. 실행 결론",
        "",
        f"- 판정: **{verdict}**",
        f"- 게이트 vs pp_v8 — 고정 test: ΔMdAPE {checks['test']['mdape_delta']:+.4f}, ΔMAPE {checks['test']['mape_delta']:+.4f}",
        f"- 게이트 vs pp_v8 — 0604: ΔMdAPE {checks['0604']['mdape_delta']:+.4f}, ΔMAPE {checks['0604']['mape_delta']:+.4f}",
        "- 핵심 해석: 0604 최정밀 subset에서 svc는 MdAPE(중앙값)는 개선하나 MAPE(평균)는 악화 = staleness가 최정밀 매칭에서도 꼬리(tail) 위험으로 잔존. 어떤 svc 가중치도 0604에서 pp_v8을 중앙값·평균 동시 지배 못함. 고정 test(과거)는 svc가 깨끗해 게이트가 pp_v8보다 개선되지만, 신규 0604에서는 median-vs-tail 트레이드오프라 순지배 실패.",
        "",
        "## 2. 후보 × 영역 MdAPE",
        "",
        markdown_table(pivot),
        "",
        "## 3. 후보 × 영역 MAPE",
        "",
        markdown_table(mape_pivot),
        "",
        "## 4. 게이트 적용 구간(최정밀 매칭) svc vs pp_v8",
        "",
        markdown_table(sub_df),
        "",
        "## 5. w_fine validation 선택",
        "",
        markdown_table(sel_df),
        "",
        "## 6. 산출물",
        "",
        "- `outputs/region_candidate_metrics.csv`, `outputs/gate_applied_subset_compare.csv`, `outputs/w_fine_validation_selection.csv`",
        "- `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_svc9_warm_svc_fine_match_gate_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_svc9_warm_svc_fine_match_gate_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {
        "experiment_id": EXP_ID, "experiment_slug": EXP_SLUG,
        "fine_level": FINE_LEVEL, "w_fine_grid": W_FINE_GRID, "w_fine_selected": w_fine,
        "blend_reference_w": BLEND_REFERENCE_W,
        "fixed_predictions": str(FIXED_PREDICTIONS.relative_to(REPO)),
        "ops_0604": str(OPS_0604.relative_to(REPO)),
        "region_n": {r: int(len(f)) for r, f in frames.items()},
        "gate_vs_ppv8": checks, "verdict": verdict,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] w_fine selected (validation): {w_fine}")
    print(f"[{EXP_ID}] region sizes: " + ", ".join(f"{r}={len(f)}" for r, f in frames.items()))
    print("--- MdAPE ---")
    print(pivot.to_string(index=False))
    print("--- gate vs pp_v8 deltas ---")
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    print(f"[{EXP_ID}] verdict: {verdict}")


if __name__ == "__main__":
    main()
