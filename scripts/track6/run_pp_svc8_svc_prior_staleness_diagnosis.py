#!/usr/bin/env python3
"""Run PP-SVC8: diagnose why the svc comparable-price prior degrades on the 0604
new-label set (the cause behind PP-SVC7's regime conflict).

Decomposes the svc degradation into:
- bias (systematic temporal offset)            -> oracle bias-removal diagnostic
- within-group dispersion increase (staleness)  -> level-controlled dispersion
- coverage matching shift (coarser matches)     -> mix shift + mix/within decomposition

All oracle corrections use the region's own labels and are UPPER-BOUND diagnostics,
not deployable candidates.
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
EXP_ID = "PP-SVC8"
EXP_SLUG = "PP-SVC8_svc_prior_staleness_diagnosis"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "svc 비교가격 prior의 0604 악화 원인 분해"

FIXED_PREDICTIONS = REPO / "experiments" / "track6" / "PP-SVC2_warm_comparable_stats_stability" / "outputs" / "predictions.csv"
OPS_0604 = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

SVC_COL = "svc_numeric_seed_mean"
PPV8_COL = "pp_v8_compact_blend_mape_guarded"
RESAMPLE_SEED = 20260607
RESAMPLE_DRAWS = 200


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def ape_from_log(actual_log: np.ndarray, pred_log: np.ndarray) -> np.ndarray:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    actual_price = np.exp(np.asarray(actual_log, dtype=float))
    return np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)


def metric_block(actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    ape = ape_from_log(actual_log, pred_log)
    return {"n": int(len(ape)), "MdAPE": float(np.median(ape)),
            "MAPE": float(np.mean(ape)), "p95_APE": float(np.quantile(ape, 0.95))}


def load_fixed_test() -> pd.DataFrame:
    long = pd.read_csv(FIXED_PREDICTIONS, low_memory=False)
    long = long[long["split"] == "test"].copy()
    base = long[["_track6_row_id", "actual_log", "svc_coverage_tier", "svc_group_level", "svc_group_n"]].drop_duplicates("_track6_row_id")
    wide = long.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last").reset_index()
    wide.columns.name = None
    out = base.merge(wide[["_track6_row_id", SVC_COL, PPV8_COL]], on="_track6_row_id", how="inner")
    out = out.rename(columns={SVC_COL: "svc", PPV8_COL: "ppv8"}).dropna(subset=["svc", "ppv8", "actual_log"])
    out["svc_coverage_tier"] = out["svc_coverage_tier"].fillna("__MISSING__").astype(str)
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__").astype(str)
    return out.reset_index(drop=True)


def load_0604() -> pd.DataFrame:
    df = pd.read_csv(OPS_0604, low_memory=False)
    df = df[df["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(df.get("actual_price_usd_equiv"), errors="coerce")
    df = df[~(usd < 50.0)].copy()
    out = pd.DataFrame({
        "actual_log": np.log(np.clip(pd.to_numeric(df["actual_price_krw"], errors="coerce"), 1.0, None)),
        "svc": pd.to_numeric(df["svc_numeric_seed_mean_pred_log"], errors="coerce"),
        "ppv8": pd.to_numeric(df["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce"),
        "svc_coverage_tier": df["svc_coverage_tier"].fillna("__MISSING__").astype(str),
        "svc_group_level": df["svc_group_level"].fillna("__MISSING__").astype(str),
        "svc_group_n": pd.to_numeric(df.get("svc_group_n"), errors="coerce"),
    })
    return out.dropna(subset=["svc", "ppv8", "actual_log"]).reset_index(drop=True)


def residual_summary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for region, f in frames.items():
        for model in ["svc", "ppv8"]:
            resid = f["actual_log"].to_numpy(dtype=float) - f[model].to_numpy(dtype=float)
            m = metric_block(f["actual_log"].to_numpy(), f[model].to_numpy())
            rows.append({
                "region": region, "model": model, "n": m["n"],
                "bias_median": float(np.median(resid)),
                "IQR": float(np.quantile(resid, 0.75) - np.quantile(resid, 0.25)),
                "std": float(np.std(resid)),
                "MdAPE": m["MdAPE"], "MAPE": m["MAPE"], "p95_APE": m["p95_APE"],
            })
    return pd.DataFrame(rows)


def bias_removal_oracle(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Upper-bound diagnostic: remove region/level median residual from svc."""
    rows: list[dict[str, Any]] = []
    for region, f in frames.items():
        actual = f["actual_log"].to_numpy(dtype=float)
        svc = f["svc"].to_numpy(dtype=float)
        base = metric_block(actual, svc)
        # global region bias
        gbias = float(np.median(actual - svc))
        gm = metric_block(actual, svc + gbias)
        # per group_level bias
        lvl_corr = svc.copy().astype(float)
        for lvl, idx in f.groupby("svc_group_level", observed=False).groups.items():
            ii = np.asarray(list(idx))
            lvl_corr[ii] = svc[ii] + float(np.median(actual[ii] - svc[ii]))
        lm = metric_block(actual, lvl_corr)
        rows.append({
            "region": region, "svc_MdAPE": base["MdAPE"], "svc_MAPE": base["MAPE"],
            "global_bias": gbias,
            "svc_plus_global_bias_MdAPE": gm["MdAPE"], "svc_plus_global_bias_MAPE": gm["MAPE"],
            "svc_plus_level_bias_MdAPE": lm["MdAPE"], "svc_plus_level_bias_MAPE": lm["MAPE"],
        })
    return pd.DataFrame(rows)


def coverage_mix_shift(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for field in ["svc_group_level", "svc_coverage_tier"]:
        cats = set()
        for f in frames.values():
            cats |= set(f[field].unique())
        for cat in sorted(cats):
            row = {"field": field, "category": cat}
            for region, f in frames.items():
                row[f"{region}_pct"] = round(float((f[field] == cat).mean()) * 100, 2)
            rows.append(row)
    return pd.DataFrame(rows)


def level_controlled_dispersion(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    levels = set(frames["test"]["svc_group_level"]) & set(frames["0604"]["svc_group_level"])
    rows: list[dict[str, Any]] = []
    for lvl in sorted(levels):
        row: dict[str, Any] = {"svc_group_level": lvl}
        for region, f in frames.items():
            g = f[f["svc_group_level"] == lvl]
            resid = g["actual_log"].to_numpy(dtype=float) - g["svc"].to_numpy(dtype=float)
            row[f"{region}_n"] = int(len(g))
            row[f"{region}_svc_IQR"] = float(np.quantile(resid, 0.75) - np.quantile(resid, 0.25)) if len(g) else np.nan
            row[f"{region}_svc_std"] = float(np.std(resid)) if len(g) else np.nan
            row[f"{region}_svc_MdAPE"] = metric_block(g["actual_log"].to_numpy(), g["svc"].to_numpy())["MdAPE"] if len(g) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def mix_within_decomposition(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Reweight 0604 rows to the fixed-test group_level mix to isolate mix vs within."""
    fixed = frames["test"]
    ops = frames["0604"]
    fixed_mix = fixed["svc_group_level"].value_counts(normalize=True).to_dict()

    actual_svc = metric_block(ops["actual_log"].to_numpy(), ops["svc"].to_numpy())

    rng = np.random.default_rng(RESAMPLE_SEED)
    groups = {lvl: ops[ops["svc_group_level"] == lvl] for lvl in ops["svc_group_level"].unique()}
    shared = [lvl for lvl in groups if lvl in fixed_mix and fixed_mix[lvl] > 0]
    weights = np.array([fixed_mix[lvl] for lvl in shared], dtype=float)
    weights = weights / weights.sum()

    n_draw = len(ops)
    md_list, ma_list = [], []
    for _ in range(RESAMPLE_DRAWS):
        chosen_levels = rng.choice(shared, size=n_draw, p=weights)
        parts = []
        for lvl in shared:
            k = int(np.sum(chosen_levels == lvl))
            if k == 0:
                continue
            g = groups[lvl]
            idx = rng.integers(0, len(g), size=k)
            parts.append(g.iloc[idx])
        sample = pd.concat(parts, ignore_index=True)
        m = metric_block(sample["actual_log"].to_numpy(), sample["svc"].to_numpy())
        md_list.append(m["MdAPE"]); ma_list.append(m["MAPE"])

    cf_md = float(np.mean(md_list)); cf_ma = float(np.mean(ma_list))
    fixed_svc = metric_block(fixed["actual_log"].to_numpy(), fixed["svc"].to_numpy())
    total_gap = actual_svc["MdAPE"] - fixed_svc["MdAPE"]
    mix_part = actual_svc["MdAPE"] - cf_md           # removed by moving 0604 to fixed mix
    within_part = cf_md - fixed_svc["MdAPE"]          # residual after mix matched
    return pd.DataFrame([{
        "fixed_test_svc_MdAPE": fixed_svc["MdAPE"],
        "ops_0604_svc_MdAPE": actual_svc["MdAPE"],
        "ops_0604_svc_at_fixed_mix_MdAPE": cf_md,
        "ops_0604_svc_at_fixed_mix_MAPE": cf_ma,
        "total_gap_MdAPE": total_gap,
        "mix_shift_part_MdAPE": mix_part,
        "within_level_part_MdAPE": within_part,
        "mix_share_pct": round(100 * mix_part / total_gap, 1) if total_gap else np.nan,
        "within_share_pct": round(100 * within_part / total_gap, 1) if total_gap else np.nan,
        "resample_draws": RESAMPLE_DRAWS,
    }])


def robustness_by_level(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ops = frames["0604"]
    rows: list[dict[str, Any]] = []
    for lvl, g in ops.groupby("svc_group_level", observed=False):
        rs = g["actual_log"].to_numpy(dtype=float) - g["svc"].to_numpy(dtype=float)
        rp = g["actual_log"].to_numpy(dtype=float) - g["ppv8"].to_numpy(dtype=float)
        rows.append({
            "svc_group_level": str(lvl), "n": int(len(g)),
            "svc_std": float(np.std(rs)), "ppv8_std": float(np.std(rp)),
            "svc_over_ppv8_std": float(np.std(rs) / np.std(rp)) if np.std(rp) else np.nan,
            "svc_MdAPE": metric_block(g["actual_log"].to_numpy(), g["svc"].to_numpy())["MdAPE"],
            "ppv8_MdAPE": metric_block(g["actual_log"].to_numpy(), g["ppv8"].to_numpy())["MdAPE"],
        })
    return pd.DataFrame(rows).sort_values("n", ascending=False)


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
    frames = {"test": load_fixed_test(), "0604": load_0604()}

    resid = residual_summary(frames)
    bias = bias_removal_oracle(frames)
    mix = coverage_mix_shift(frames)
    disp = level_controlled_dispersion(frames)
    decomp = mix_within_decomposition(frames)
    robust = robustness_by_level(frames)

    out = EXP_DIR / "outputs"
    resid.to_csv(out / "region_residual_summary.csv", index=False)
    bias.to_csv(out / "bias_removal_oracle.csv", index=False)
    mix.to_csv(out / "coverage_mix_shift.csv", index=False)
    disp.to_csv(out / "level_controlled_dispersion.csv", index=False)
    decomp.to_csv(out / "mix_within_decomposition.csv", index=False)
    robust.to_csv(out / "svc_vs_ppv8_robustness_by_level.csv", index=False)

    d = decomp.iloc[0]
    b0604 = bias[bias["region"] == "0604"].iloc[0]
    bias_fixes = b0604["svc_plus_global_bias_MdAPE"] < b0604["svc_MdAPE"]
    # Build verdict.
    cause = []
    if not bias_fixes:
        cause.append("편향 아님(전역 bias 제거가 0604 MdAPE를 개선하지 못함)")
    if d["within_share_pct"] >= d["mix_share_pct"]:
        cause.append(f"그룹내 분산(staleness) 주도({d['within_share_pct']:.0f}%)")
    else:
        cause.append(f"매칭 이동(coverage shift) 주도({d['mix_share_pct']:.0f}%)")
    verdict = "; ".join(cause)

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: svc 비교가격 prior가 0604 신규 라벨에서 악화된 원인을 편향/분산/매칭이동으로 분해",
        "- 주의: oracle bias 보정은 해당 영역 라벨을 사용한 상한 진단이며 배포 후보가 아님",
        "",
        "## 1. 진단 결론",
        "",
        f"- 원인 귀속: **{verdict}**",
        f"- 0604 svc MdAPE 악화 {d['total_gap_MdAPE']:.4f} 중 매칭이동 {d['mix_shift_part_MdAPE']:.4f}({d['mix_share_pct']:.0f}%), 그룹내 분산 {d['within_level_part_MdAPE']:.4f}({d['within_share_pct']:.0f}%)",
        f"- 전역 bias 제거 후 0604 svc MdAPE: {b0604['svc_plus_global_bias_MdAPE']:.4f} (원본 {b0604['svc_MdAPE']:.4f}) → 편향 보정으로 회복 {'불가' if not bias_fixes else '가능'}",
        "- 함의: svc prior는 신규 작품에서 거친 매칭+고분산으로 점예측 직접 반영이 위험. 운영 기본값 pp_v8 유지가 타당. 개선은 비교군 prior 갱신/신뢰도 약화 후속 실험에서.",
        "",
        "## 2. 영역 residual 요약 (svc vs pp_v8)",
        "",
        markdown_table(resid),
        "",
        "## 3. 편향 제거 oracle (상한 진단, 비배포)",
        "",
        markdown_table(bias),
        "",
        "## 4. 매칭 레벨/커버리지 이동",
        "",
        markdown_table(mix),
        "",
        "## 5. 레벨 통제 분산 (매칭 이동 통제 후 staleness)",
        "",
        markdown_table(disp),
        "",
        "## 6. mix vs within 분해",
        "",
        markdown_table(decomp),
        "",
        "## 7. 0604 레벨별 svc vs pp_v8 강건성",
        "",
        markdown_table(robust),
        "",
        "## 8. 산출물",
        "",
        "- `outputs/region_residual_summary.csv`, `outputs/bias_removal_oracle.csv`, `outputs/coverage_mix_shift.csv`",
        "- `outputs/level_controlled_dispersion.csv`, `outputs/mix_within_decomposition.csv`, `outputs/svc_vs_ppv8_robustness_by_level.csv`",
        "- `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_svc8_svc_prior_staleness_diagnosis_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_svc8_svc_prior_staleness_diagnosis_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {
        "experiment_id": EXP_ID, "experiment_slug": EXP_SLUG,
        "svc_col": SVC_COL, "ppv8_col": PPV8_COL,
        "resample_seed": RESAMPLE_SEED, "resample_draws": RESAMPLE_DRAWS,
        "fixed_predictions": str(FIXED_PREDICTIONS.relative_to(REPO)),
        "ops_0604": str(OPS_0604.relative_to(REPO)),
        "region_n": {r: int(len(f)) for r, f in frames.items()},
        "verdict": verdict,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] regions: " + ", ".join(f"{r}={len(f)}" for r, f in frames.items()))
    print("--- residual summary ---")
    print(resid.to_string(index=False))
    print("--- mix/within decomposition ---")
    print(decomp.to_string(index=False))
    print(f"[{EXP_ID}] verdict: {verdict}")


if __name__ == "__main__":
    main()
