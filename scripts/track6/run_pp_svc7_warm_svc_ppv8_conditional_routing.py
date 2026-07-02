#!/usr/bin/env python3
"""Run PP-SVC7: Warm 70:30 vs operational pp_v8 conditional routing, validated on
both the fixed Track6 split and the 0604 new-label set.

Question: the report candidate ``PP-SVC3 70:30`` (0.70*svc + 0.30*pp_v8) wins on
the fixed test, while the operational default ``pp_v8`` wins on the 0604 new
labels. Can an operationally-computable routing signal (svc reliability / model
disagreement) pick between them so that BOTH regimes are covered at once?

Discipline:
- Routing weights / segments / disagreement thresholds are selected on the fixed
  validation split ONLY.
- The fixed test set and the 0604 set are confirmation regimes; never used to
  select the routing rule.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-SVC7"
EXP_SLUG = "PP-SVC7_warm_svc_ppv8_conditional_routing"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Warm 70:30 vs 운영 pp_v8 조건부 라우팅 + 0604 동시 검증"

FIXED_PREDICTIONS = REPO / "experiments" / "track6" / "PP-SVC2_warm_comparable_stats_stability" / "outputs" / "predictions.csv"
OPS_0604 = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

SVC_COL = "svc_numeric_seed_mean"
PPV8_COL = "pp_v8_compact_blend_mape_guarded"
WEIGHT_GRID = [0.0, 0.3, 0.5, 0.7]
BLEND_REFERENCE_W = 0.70
MIN_SEGMENT_ROWS = 30
SIGNALS = ["svc_coverage_tier", "svc_group_level", "disagree_bin"]
SWEEP = [round(0.1 * i, 1) for i in range(11)]
TOLERANCE = 0.003


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    pred = np.asarray(pred_log, dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
    }


def blend(frame: pd.DataFrame, w: float) -> np.ndarray:
    return w * frame[SVC_COL].to_numpy(dtype=float) + (1.0 - w) * frame[PPV8_COL].to_numpy(dtype=float)


def load_fixed() -> dict[str, pd.DataFrame]:
    long = pd.read_csv(FIXED_PREDICTIONS, low_memory=False)
    long = long[long["split"].isin(["validation", "test"])].copy()
    base = long[["split", "_track6_row_id", "actual_log", "actual_price",
                 "svc_coverage_tier", "svc_group_level", "svc_group_n"]].drop_duplicates(["split", "_track6_row_id"])
    wide = long.pivot_table(index=["split", "_track6_row_id"], columns="candidate",
                            values="pred_log", aggfunc="last").reset_index()
    wide.columns.name = None
    out = base.merge(wide[["split", "_track6_row_id", SVC_COL, PPV8_COL]], on=["split", "_track6_row_id"], how="inner")
    out = out.dropna(subset=[SVC_COL, PPV8_COL, "actual_price"]).copy()
    out["svc_coverage_tier"] = out["svc_coverage_tier"].fillna("__MISSING__").astype(str)
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__").astype(str)
    return {"validation": out[out["split"] == "validation"].reset_index(drop=True),
            "test": out[out["split"] == "test"].reset_index(drop=True)}


def load_0604() -> pd.DataFrame:
    df = pd.read_csv(OPS_0604, low_memory=False)
    df = df[df["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(df.get("actual_price_usd_equiv"), errors="coerce")
    df = df[~(usd < 50.0)].copy()  # exclude <$50 review labels (operational 평가 기준)
    out = pd.DataFrame({
        "_track6_row_id": df["_track6_row_id"].to_numpy(),
        SVC_COL: pd.to_numeric(df["svc_numeric_seed_mean_pred_log"], errors="coerce").to_numpy(),
        PPV8_COL: pd.to_numeric(df["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce").to_numpy(),
        "actual_price": pd.to_numeric(df["actual_price_krw"], errors="coerce").to_numpy(),
        "svc_coverage_tier": df["svc_coverage_tier"].fillna("__MISSING__").astype(str).to_numpy(),
        "svc_group_level": df["svc_group_level"].fillna("__MISSING__").astype(str).to_numpy(),
        "svc_group_n": pd.to_numeric(df.get("svc_group_n"), errors="coerce").to_numpy(),
    })
    out["actual_log"] = np.log(np.clip(out["actual_price"].to_numpy(dtype=float), 1.0, None))
    return out.dropna(subset=[SVC_COL, PPV8_COL, "actual_price"]).reset_index(drop=True)


def add_disagree_bin(frames: dict[str, pd.DataFrame], thresholds: tuple[float, float]) -> None:
    lo, hi = thresholds
    for frame in frames.values():
        diff = np.abs(frame[SVC_COL].to_numpy(dtype=float) - frame[PPV8_COL].to_numpy(dtype=float))
        frame["disagree_bin"] = np.where(diff <= lo, "low", np.where(diff <= hi, "mid", "high"))


def global_best_weight(val: pd.DataFrame) -> float:
    scored = [(w, metric(val, blend(val, w))["MdAPE"]) for w in WEIGHT_GRID]
    return min(scored, key=lambda x: x[1])[0]


def fit_router(val: pd.DataFrame, signal: str, global_w: float) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Pick best validation weight per signal segment; fallback to global weight."""
    seg_map: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    for seg, group in val.groupby(signal, observed=False):
        if len(group) < MIN_SEGMENT_ROWS:
            seg_map[str(seg)] = global_w
            rows.append({"signal": signal, "segment": str(seg), "n_val": len(group),
                         "selected_w": global_w, "reason": "fallback_global"})
            continue
        scored = [(w, metric(group, blend(group, w))["MdAPE"]) for w in WEIGHT_GRID]
        best_w = min(scored, key=lambda x: x[1])[0]
        seg_map[str(seg)] = best_w
        rows.append({"signal": signal, "segment": str(seg), "n_val": len(group),
                     "selected_w": best_w, "reason": "validation_mdape_min",
                     "val_mdape_at_best": min(scored, key=lambda x: x[1])[1]})
    return seg_map, rows


def apply_router(frame: pd.DataFrame, signal: str, seg_map: dict[str, float], global_w: float) -> np.ndarray:
    weights = frame[signal].astype(str).map(lambda s: seg_map.get(s, global_w)).to_numpy(dtype=float)
    return weights * frame[SVC_COL].to_numpy(dtype=float) + (1.0 - weights) * frame[PPV8_COL].to_numpy(dtype=float)


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
            table.append(line)
            continue
        flush()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush()
    style = "body{font-family:-apple-system,Segoe UI,sans-serif;margin:32px;color:#1f2937}table{border-collapse:collapse;margin:12px 0}th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}th{background:#f3f4f6}"
    return f"<!doctype html><html lang=ko><head><meta charset=utf-8><title>{html.escape(EXP_ID)}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def main() -> None:
    ensure_dirs()
    fixed = load_fixed()
    frames = {"validation": fixed["validation"], "test": fixed["test"], "0604": load_0604()}

    # disagreement bins from validation distribution.
    val_diff = np.abs(frames["validation"][SVC_COL].to_numpy(dtype=float) - frames["validation"][PPV8_COL].to_numpy(dtype=float))
    thresholds = (float(np.quantile(val_diff, 0.33)), float(np.quantile(val_diff, 0.66)))
    add_disagree_bin(frames, thresholds)

    global_w = global_best_weight(frames["validation"])

    # Fixed candidates.
    candidates: dict[str, dict[str, np.ndarray]] = {
        "pp_v8": {region: blend(f, 0.0) for region, f in frames.items()},
        f"blend_{BLEND_REFERENCE_W:.2f}": {region: blend(f, BLEND_REFERENCE_W) for region, f in frames.items()},
    }

    # Routers (selected on validation only).
    seg_map_rows: list[dict[str, Any]] = []
    seg_maps: dict[str, dict[str, float]] = {}
    for signal in SIGNALS:
        seg_map, rows = fit_router(frames["validation"], signal, global_w)
        seg_maps[signal] = seg_map
        seg_map_rows.extend(rows)
        candidates[f"router_{signal}"] = {region: apply_router(f, signal, seg_map, global_w) for region, f in frames.items()}

    # Region x candidate metrics.
    metric_rows: list[dict[str, Any]] = []
    for cand, region_preds in candidates.items():
        for region, pred in region_preds.items():
            m = metric(frames[region], pred)
            metric_rows.append({"candidate": cand, "region": region, **m})
    metrics_df = pd.DataFrame(metric_rows)

    # Global weight sweep per region.
    sweep_rows: list[dict[str, Any]] = []
    for w in SWEEP:
        for region, f in frames.items():
            m = metric(f, blend(f, w))
            sweep_rows.append({"w_svc": w, "region": region, **m})
    sweep_df = pd.DataFrame(sweep_rows)

    # 0604 router-vs-pp_v8 breakdown by svc_coverage_tier (diagnostic).
    f0604 = frames["0604"].copy()
    f0604["_router_pred"] = candidates["router_svc_coverage_tier"]["0604"]
    f0604["_ppv8_pred"] = candidates["pp_v8"]["0604"]
    breakdown_rows: list[dict[str, Any]] = []
    for seg, g in f0604.groupby("svc_coverage_tier", observed=False):
        breakdown_rows.append({
            "svc_coverage_tier": str(seg), "n": len(g),
            "selected_w": seg_maps["svc_coverage_tier"].get(str(seg), global_w),
            "router_MdAPE": metric(g, g["_router_pred"].to_numpy())["MdAPE"],
            "ppv8_MdAPE": metric(g, g["_ppv8_pred"].to_numpy())["MdAPE"],
        })
    breakdown_df = pd.DataFrame(breakdown_rows)

    # Verdict: does any router reach both regimes' best fixed candidate?
    def region_mdape(cand: str, region: str) -> float:
        r = metrics_df[(metrics_df["candidate"] == cand) & (metrics_df["region"] == region)]
        return float(r["MdAPE"].iloc[0])

    blend_name = f"blend_{BLEND_REFERENCE_W:.2f}"
    test_target = region_mdape(blend_name, "test")
    ops_target = region_mdape("pp_v8", "0604")
    verdict_rows: list[dict[str, Any]] = []
    adopted = []
    for signal in SIGNALS:
        cand = f"router_{signal}"
        test_ok = region_mdape(cand, "test") <= test_target + TOLERANCE
        ops_ok = region_mdape(cand, "0604") <= ops_target + TOLERANCE
        both = test_ok and ops_ok
        if both:
            adopted.append(cand)
        verdict_rows.append({
            "router": cand,
            "test_MdAPE": region_mdape(cand, "test"), "test_target(blend)": test_target, "test_ok": test_ok,
            "ops_MdAPE": region_mdape(cand, "0604"), "ops_target(pp_v8)": ops_target, "ops_ok": ops_ok,
            "reconciles_both": both,
        })
    verdict_df = pd.DataFrame(verdict_rows)

    # Save outputs.
    out = EXP_DIR / "outputs"
    metrics_df.to_csv(out / "region_candidate_metrics.csv", index=False)
    sweep_df.to_csv(out / "global_weight_sweep.csv", index=False)
    pd.DataFrame(seg_map_rows).to_csv(out / "router_segment_weight_map.csv", index=False)
    breakdown_df.to_csv(out / "router_0604_segment_breakdown.csv", index=False)
    verdict_df.to_csv(out / "router_verdict.csv", index=False)

    # Pivot for report readability.
    pivot = metrics_df.pivot(index="candidate", columns="region", values="MdAPE").reset_index()
    pivot = pivot[["candidate", "validation", "test", "0604"]]

    conclusion = (
        f"라우팅으로 두 영역을 동시에 잡는 후보 있음: {adopted}" if adopted
        else "어떤 라우터도 고정 test(70:30)와 0604(pp_v8)를 동시에 만족하지 못함 → 70:30 vs pp_v8 차이는 라우팅 불가한 영역(distribution shift) 차이로 결론"
    )

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- weight grid: {WEIGHT_GRID} (0.0=pp_v8, 0.70=70:30), validation 전역 best w = {global_w}",
        f"- disagreement 경계(validation |svc-ppv8| q33/q66): {thresholds[0]:.4f} / {thresholds[1]:.4f}",
        "- 라우팅 규칙은 고정 validation에서만 선택, 고정 test와 0604는 확인용",
        "",
        "## 1. 실행 결론",
        "",
        f"- {conclusion}",
        f"- 고정 test 목표(70:30): MdAPE {test_target:.4f} / 0604 목표(pp_v8): MdAPE {ops_target:.4f}",
        "",
        "## 2. 후보 × 영역 MdAPE",
        "",
        markdown_table(pivot),
        "",
        "## 3. 라우터 영역 통합 판정",
        "",
        markdown_table(verdict_df),
        "",
        "## 4. 전역 weight tradeoff (영역별 MdAPE)",
        "",
        markdown_table(sweep_df.pivot(index="w_svc", columns="region", values="MdAPE").reset_index()[["w_svc", "validation", "test", "0604"]]),
        "",
        "## 5. svc_coverage_tier 라우터: 선택 weight와 0604 segment 비교",
        "",
        markdown_table(breakdown_df),
        "",
        "## 6. 산출물",
        "",
        "- `outputs/region_candidate_metrics.csv`, `outputs/global_weight_sweep.csv`",
        "- `outputs/router_segment_weight_map.csv`, `outputs/router_0604_segment_breakdown.csv`, `outputs/router_verdict.csv`",
        "- `artifacts/run_config.json`",
    ])

    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_svc7_warm_svc_ppv8_conditional_routing_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_svc7_warm_svc_ppv8_conditional_routing_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {
        "experiment_id": EXP_ID, "experiment_slug": EXP_SLUG,
        "svc_col": SVC_COL, "ppv8_col": PPV8_COL,
        "weight_grid": WEIGHT_GRID, "blend_reference_w": BLEND_REFERENCE_W,
        "min_segment_rows": MIN_SEGMENT_ROWS, "signals": SIGNALS,
        "global_best_w_validation": global_w,
        "disagree_thresholds_q33_q66": list(thresholds),
        "tolerance": TOLERANCE,
        "fixed_predictions": str(FIXED_PREDICTIONS.relative_to(REPO)),
        "ops_0604": str(OPS_0604.relative_to(REPO)),
        "region_n": {region: int(len(f)) for region, f in frames.items()},
        "adopted_routers": adopted,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] region sizes: " + ", ".join(f"{r}={len(f)}" for r, f in frames.items()))
    print(f"[{EXP_ID}] global best w (validation) = {global_w}")
    print(pivot.to_string(index=False))
    print("--- verdict ---")
    print(verdict_df.to_string(index=False))
    print(f"[{EXP_ID}] conclusion: {conclusion}")


if __name__ == "__main__":
    main()
