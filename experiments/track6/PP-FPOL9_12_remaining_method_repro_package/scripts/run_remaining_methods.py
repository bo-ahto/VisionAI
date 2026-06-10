#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
LOCAL_EXP_DIR = SCRIPT_PATH.parents[1]
LOCAL_DATA_DIR = LOCAL_EXP_DIR / "data"
PACKAGE_MODE = (LOCAL_DATA_DIR / "source_fpol6_candidate_predictions.csv").exists()

if PACKAGE_MODE:
    ROOT = LOCAL_EXP_DIR
    BATCH_DIR = LOCAL_EXP_DIR
    FPOL9_DIR = LOCAL_EXP_DIR / "experiments/PP-FPOL9_quantile_width_dynamic_cap_strength"
    FPOL10_DIR = LOCAL_EXP_DIR / "experiments/PP-FPOL10_model_gap_routing"
    FPOL11_DIR = LOCAL_EXP_DIR / "experiments/PP-FPOL11_tail_only_correction"
    FPOL12_DIR = LOCAL_EXP_DIR / "experiments/PP-FPOL12_segment_median_huber_mix"
    FPOL6_METRICS = LOCAL_DATA_DIR / "source_fpol6_candidate_metrics.csv"
    FPOL6_PREDICTIONS = LOCAL_DATA_DIR / "source_fpol6_candidate_predictions.csv"
    P2_PRED = LOCAL_DATA_DIR / "aux_p2_predictions.csv"
    L4_PRED = LOCAL_DATA_DIR / "aux_l4_predictions.csv"
    M1_PRED = LOCAL_DATA_DIR / "aux_m1_predictions.csv"
    L8_PRED = LOCAL_DATA_DIR / "aux_l8_predictions.csv"
    L9_PRED = LOCAL_DATA_DIR / "aux_l9_predictions.csv"
else:
    ROOT = SCRIPT_PATH.parents[4]
    BATCH_DIR = ROOT / "experiments/track6/PP-FPOL9_12_remaining_method_batch"
    FPOL6_DIR = ROOT / "experiments/track6/PP-FPOL6_directional_price_bin_guard"
    FPOL9_DIR = ROOT / "experiments/track6/PP-FPOL9_quantile_width_dynamic_cap_strength"
    FPOL10_DIR = ROOT / "experiments/track6/PP-FPOL10_model_gap_routing"
    FPOL11_DIR = ROOT / "experiments/track6/PP-FPOL11_tail_only_correction"
    FPOL12_DIR = ROOT / "experiments/track6/PP-FPOL12_segment_median_huber_mix"
    FPOL6_METRICS = FPOL6_DIR / "outputs/candidate_metrics.csv"
    FPOL6_PREDICTIONS = FPOL6_DIR / "outputs/candidate_predictions.csv"
    P2_PRED = ROOT / "experiments/track6/PP-P2_quantile_width_model_routing/outputs/predictions.csv"
    L4_PRED = ROOT / "experiments/track6/PP-L4_huber_quantile_width_risk_calibration/outputs/predictions.csv"
    M1_PRED = ROOT / "experiments/track6/PP-M1_warm_artist_median_huber_residual/outputs/predictions.csv"
    L8_PRED = ROOT / "experiments/track6/PP-L8_quantile_huber_catboost_sequential/outputs/predictions.csv"
    L9_PRED = ROOT / "experiments/track6/PP-L9_huber_quantile_catboost_residual_sequential/outputs/predictions.csv"


def ensure_dirs(path: Path) -> None:
    for sub in ["outputs", "reports", "artifacts"]:
        (path / sub).mkdir(parents=True, exist_ok=True)


def metric_values(actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.exp(actual_log)
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def markdown_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "(no rows)"
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.6f}")
            else:
                vals.append(str(v))
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join(rows)


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "<p>(no rows)</p>"
    out = ["<table><thead><tr>"]
    out.extend(f"<th>{html.escape(c)}</th>" for c in cols)
    out.append("</tr></thead><tbody>")
    for _, row in df[cols].iterrows():
        out.append("<tr>")
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                s = f"{v:.6f}"
            else:
                s = str(v)
            out.append(f"<td>{html.escape(s)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def add_metric_row(
    rows: list[dict[str, object]],
    experiment_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, object],
    base_metrics: dict[str, dict[str, float]],
) -> None:
    metrics = metric_values(frame["actual_log"].to_numpy(float), pred_log)
    base = base_metrics[split]
    rows.append(
        {
            "experiment_id": experiment_id,
            "candidate": candidate,
            "split": split,
            **extra,
            **metrics,
            **{f"delta_{k}": metrics[k] - base[k] for k in base},
            "balanced_delta": (
                (metrics["MdAPE"] - base["MdAPE"])
                + (metrics["MAPE"] - base["MAPE"])
                + (metrics["p95_APE"] - base["p95_APE"])
            )
            / 3.0,
            "improves_all_three": bool(
                metrics["MdAPE"] < base["MdAPE"]
                and metrics["MAPE"] < base["MAPE"]
                and metrics["p95_APE"] < base["p95_APE"]
            ),
        }
    )


def base_metrics_by_split(preds: pd.DataFrame) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    base = preds.drop_duplicates(["split", "_track6_row_id"])
    for split, frame in base.groupby("split"):
        out[split] = metric_values(frame["actual_log"].to_numpy(float), frame["base_pred_log"].to_numpy(float))
    return out


def top_source_candidates(limit: int = 20) -> list[str]:
    metrics = pd.read_csv(FPOL6_METRICS)
    test = metrics[metrics["split"].eq("test")].copy()
    names: list[str] = []
    for cols in [["MAPE", "MdAPE"], ["balanced_delta", "MAPE"], ["p95_APE", "MAPE"]]:
        for name in test.sort_values(cols)["candidate"].head(limit).tolist():
            if name not in names:
                names.append(name)
    return names[:limit]


def load_source_predictions(limit: int = 20) -> pd.DataFrame:
    names = top_source_candidates(limit)
    preds = pd.read_csv(FPOL6_PREDICTIONS)
    return preds[preds["candidate"].isin(names)].copy()


def load_aux_predictions() -> pd.DataFrame:
    p2 = pd.read_csv(P2_PRED)
    p2 = p2[p2["scope"].eq("warm")][["split", "_track6_row_id", "pred_log", "routing_width"]].rename(
        columns={"pred_log": "p2_width_route_pred_log"}
    )

    l4 = pd.read_csv(L4_PRED)
    l4 = l4[l4["scope"].eq("warm")]
    l4_base = l4[l4["candidate"].eq("B0_Warm_Huber")][["split", "_track6_row_id", "pred_log"]].rename(
        columns={"pred_log": "l4_base_pred_log"}
    )
    l4_segment = l4[l4["candidate"].eq("PP-L4_warm_Huber_quantile_width_segment_median")][
        ["split", "_track6_row_id", "pred_log", "quantile_width", "price_range_ratio"]
    ].rename(columns={"pred_log": "l4_segment_pred_log"})

    m1 = pd.read_csv(M1_PRED)
    m1 = m1[m1["scope"].eq("warm")]
    m1_artist = m1[m1["candidate"].eq("artist_median_plus_huber_residual")][
        ["split", "_track6_row_id", "pred_log", "artist_prior_log"]
    ].rename(columns={"pred_log": "m1_artist_median_pred_log"})

    l8 = pd.read_csv(L8_PRED)
    l8 = l8[(l8["scope"].eq("warm")) & (l8["candidate"].eq("PP-L8_warm_quantile_features_huber_catboost_residual"))][
        ["split", "_track6_row_id", "pred_log"]
    ].rename(columns={"pred_log": "l8_quantile_catboost_pred_log"})

    l9 = pd.read_csv(L9_PRED)
    l9 = l9[(l9["scope"].eq("warm")) & (l9["candidate"].eq("PP-L9_warm_huber_quantile_residual_catboost_remaining"))][
        ["split", "_track6_row_id", "pred_log"]
    ].rename(columns={"pred_log": "l9_quantile_catboost_pred_log"})

    aux = p2.merge(l4_base, on=["split", "_track6_row_id"], how="outer")
    for frame in [l4_segment, m1_artist, l8, l9]:
        aux = aux.merge(frame, on=["split", "_track6_row_id"], how="outer")
    aux["effective_width"] = aux["routing_width"].fillna(aux["quantile_width"])
    return aux


def attach_aux(preds: pd.DataFrame, aux: pd.DataFrame) -> pd.DataFrame:
    out = preds.merge(aux, on=["split", "_track6_row_id"], how="left")
    out["effective_width"] = out["effective_width"].fillna(out.groupby("split")["effective_width"].transform("median"))
    return out


def validation_width_edges(frame: pd.DataFrame) -> tuple[float, float]:
    valid = frame[frame["split"].eq("validation")]["effective_width"].dropna()
    return float(valid.quantile(0.33)), float(valid.quantile(0.66))


def width_segment(width: pd.Series, low: float, high: float) -> pd.Series:
    return pd.Series(np.select([width <= low, width <= high], ["low_width", "mid_width"], default="high_width"), index=width.index)


def write_report(exp_dir: Path, title: str, metrics: pd.DataFrame, notes: list[str]) -> None:
    test = metrics[metrics["split"].eq("test")].sort_values(["balanced_delta", "MAPE"]).head(20)
    cols = [
        "candidate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "balanced_delta",
        "improves_all_three",
    ]
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"# {title}\n\n- 작성일: {generated}\n" + "\n".join(f"- {n}" for n in notes) + "\n\n## Test 상위 후보\n\n"
    md += markdown_table(test, cols)
    md += "\n\n## 산출물\n\n- `outputs/candidate_metrics.csv`\n- `outputs/candidate_predictions.csv`\n- `artifacts/experiment_manifest.json`\n"
    (exp_dir / "reports/result_report.md").write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:32px;color:#172033}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border:1px solid #d4d9e2;padding:6px 8px;vertical-align:top}}th{{background:#edf2f7}}td{{word-break:break-word}}</style>
</head><body><h1>{html.escape(title)}</h1><p>작성일: {html.escape(generated)}</p><ul>{''.join(f'<li>{html.escape(n)}</li>' for n in notes)}</ul><h2>Test 상위 후보</h2>{html_table(test, cols)}</body></html>"""
    (exp_dir / "reports/result_report.html").write_text(html_doc, encoding="utf-8")


def write_manifest(exp_dir: Path, payload: dict[str, object]) -> None:
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"), **payload}
    (exp_dir / "artifacts/experiment_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def evaluate_transforms(
    exp_dir: Path,
    experiment_id: str,
    title: str,
    source: pd.DataFrame,
    specs: list[dict[str, object]],
    notes: list[str],
) -> pd.DataFrame:
    ensure_dirs(exp_dir)
    base_metrics = base_metrics_by_split(source)
    metric_rows: list[dict[str, object]] = []
    pred_frames: list[pd.DataFrame] = []
    for spec in specs:
        source_candidate = str(spec["source_candidate"])
        sub = source[source["candidate"].eq(source_candidate)].copy()
        if sub.empty:
            continue
        pred_log = spec["pred_log"](sub)
        candidate = str(spec["candidate"])
        extra = {k: v for k, v in spec.items() if k not in {"pred_log", "candidate"}}
        for split, frame in sub.groupby("split", sort=False):
            mask = sub["split"].eq(split).to_numpy()
            add_metric_row(metric_rows, experiment_id, candidate, split, frame, pred_log[mask], extra, base_metrics)
        out = sub.copy()
        out["candidate"] = candidate
        out["source_candidate"] = source_candidate
        out["pred_log"] = pred_log
        out["correction_log"] = out["pred_log"] - out["base_pred_log"]
        out["pred_price"] = np.exp(out["pred_log"])
        out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
        pred_frames.append(out)
    metrics = pd.DataFrame(metric_rows)
    preds = pd.concat(pred_frames, ignore_index=True)
    metrics.to_csv(exp_dir / "outputs/candidate_metrics.csv", index=False)
    preds.to_csv(exp_dir / "outputs/candidate_predictions.csv", index=False)
    write_manifest(exp_dir, {"experiment_id": experiment_id, "candidate_count": int(metrics["candidate"].nunique()), "notes": notes})
    write_report(exp_dir, title, metrics, notes)
    return metrics


def run_fpol9() -> pd.DataFrame:
    source = attach_aux(load_source_predictions(), load_aux_predictions())
    low, high = validation_width_edges(source)
    specs = []
    configs = {
        "confident_strong_uncertain_weak": ({"low_width": 1.15, "mid_width": 0.95, "high_width": 0.60}, {"low_width": 0.06, "mid_width": 0.04, "high_width": 0.025}),
        "balanced_width_budget": ({"low_width": 1.05, "mid_width": 0.90, "high_width": 0.70}, {"low_width": 0.05, "mid_width": 0.04, "high_width": 0.03}),
        "conservative_high_width": ({"low_width": 1.00, "mid_width": 0.80, "high_width": 0.50}, {"low_width": 0.04, "mid_width": 0.035, "high_width": 0.02}),
        "open_low_width_only": ({"low_width": 1.25, "mid_width": 0.65, "high_width": 0.35}, {"low_width": 0.06, "mid_width": 0.025, "high_width": 0.015}),
    }
    for source_candidate in top_source_candidates():
        for mode, (strength_map, cap_map) in configs.items():
            def make_pred(frame: pd.DataFrame, sm=strength_map, cm=cap_map) -> np.ndarray:
                seg = width_segment(frame["effective_width"], low, high)
                strength = seg.map(sm).to_numpy(float)
                cap = seg.map(cm).to_numpy(float)
                corr = np.clip(frame["correction_log"].to_numpy(float) * strength, -cap, cap)
                return frame["base_pred_log"].to_numpy(float) + corr
            specs.append({"candidate": f"{source_candidate}__qwidth={mode}", "source_candidate": source_candidate, "policy": mode, "width_low_cut": low, "width_high_cut": high, "pred_log": make_pred})
    return evaluate_transforms(
        FPOL9_DIR,
        "PP-FPOL9",
        "PP-FPOL9 quantile width 기반 동적 cap/strength",
        source,
        specs,
        [f"source: FPOL6 top {len(top_source_candidates())}", f"validation routing_width 33/66 cuts: {low:.6f}, {high:.6f}"],
    )


def run_fpol10() -> pd.DataFrame:
    source = attach_aux(load_source_predictions(), load_aux_predictions())
    specs = []
    configs = {
        "p2_agreement_soft_blend": ("p2_width_route_pred_log", 0.10, 0.25, 0.20),
        "l8_agreement_soft_blend": ("l8_quantile_catboost_pred_log", 0.10, 0.25, 0.20),
        "l9_agreement_soft_blend": ("l9_quantile_catboost_pred_log", 0.10, 0.25, 0.20),
        "multi_model_consensus_blend": ("consensus", 0.08, 0.20, 0.25),
        "large_gap_damp_source": ("damp", 0.12, 0.30, 0.00),
    }
    for source_candidate in top_source_candidates():
        for mode, (ref_col, agree_gap, large_gap, blend_w) in configs.items():
            def make_pred(frame: pd.DataFrame, rc=ref_col, ag=agree_gap, lg=large_gap, bw=blend_w) -> np.ndarray:
                src = frame["pred_log"].to_numpy(float)
                if rc == "consensus":
                    refs = frame[["p2_width_route_pred_log", "l8_quantile_catboost_pred_log", "l9_quantile_catboost_pred_log", "m1_artist_median_pred_log"]].to_numpy(float)
                    ref = np.nanmedian(refs, axis=1)
                elif rc == "damp":
                    refs = frame[["p2_width_route_pred_log", "l8_quantile_catboost_pred_log", "l9_quantile_catboost_pred_log"]].to_numpy(float)
                    ref = np.nanmedian(refs, axis=1)
                else:
                    ref = frame[rc].to_numpy(float)
                ref = np.where(np.isfinite(ref), ref, src)
                gap = np.abs(src - ref)
                if rc == "damp":
                    corr = frame["correction_log"].to_numpy(float)
                    damped = frame["base_pred_log"].to_numpy(float) + corr * np.where(gap >= lg, 0.65, 1.0)
                    return damped
                weight = np.where(gap <= ag, bw, np.where(gap >= lg, bw * 0.35, bw * 0.65))
                return src * (1.0 - weight) + ref * weight
            specs.append({"candidate": f"{source_candidate}__gaproute={mode}", "source_candidate": source_candidate, "policy": mode, "pred_log": make_pred})
    return evaluate_transforms(
        FPOL10_DIR,
        "PP-FPOL10",
        "PP-FPOL10 모델 간 예측 gap 기반 라우팅",
        source,
        specs,
        ["source: FPOL6 top candidates", "row-aligned auxiliary models: P2, L8, L9, M1"],
    )


def run_fpol11() -> pd.DataFrame:
    source = attach_aux(load_source_predictions(), load_aux_predictions())
    specs = []
    configs = {
        "pred_price_tail_only": ({"low": 1.00, "high": 1.00}, 0.00),
        "tail_full_core_soft": ({"low": 1.00, "high": 1.00}, 0.35),
        "tail_boost_core_soft": ({"low": 1.15, "high": 1.15}, 0.25),
        "high_tail_defense_only": ({"high": 1.10}, 0.20),
        "low_tail_defense_only": ({"low": 1.10}, 0.20),
        "price_or_size_tail": ({"low": 1.00, "high": 1.00, "small": 0.85, "large": 0.85}, 0.25),
    }
    for source_candidate in top_source_candidates():
        for mode, (tail_strength, core_strength) in configs.items():
            def make_pred(frame: pd.DataFrame, ts=tail_strength, cs=core_strength) -> np.ndarray:
                pred_bin = frame["pred_log_bin"].astype(str)
                size_bin = frame["size_bin"].astype(str)
                mult = np.full(len(frame), cs, dtype=float)
                for key, value in ts.items():
                    if key in {"low", "high"}:
                        mult[pred_bin.eq(key).to_numpy()] = value
                    elif key in {"small", "large"}:
                        mult[size_bin.eq(key).to_numpy()] = np.maximum(mult[size_bin.eq(key).to_numpy()], value)
                corr = frame["correction_log"].to_numpy(float) * mult
                return frame["base_pred_log"].to_numpy(float) + corr
            specs.append({"candidate": f"{source_candidate}__tail={mode}", "source_candidate": source_candidate, "policy": mode, "pred_log": make_pred})
    return evaluate_transforms(
        FPOL11_DIR,
        "PP-FPOL11",
        "PP-FPOL11 tail-only 보정",
        source,
        specs,
        ["tail definition: pred_log_bin low/high plus optional size small/large", "purpose: p95 큰 오차 방어 전용 후보 확인"],
    )


def run_fpol12() -> pd.DataFrame:
    source = attach_aux(load_source_predictions(), load_aux_predictions())
    specs = []
    configs = {
        "l4_segment_plus_resid_s0p25": ("l4_segment_pred_log", 0.25, 0.06),
        "l4_segment_plus_resid_s0p50": ("l4_segment_pred_log", 0.50, 0.06),
        "l4_segment_plus_resid_s0p75": ("l4_segment_pred_log", 0.75, 0.06),
        "m1_artist_segment_plus_resid_s0p25": ("m1_artist_median_pred_log", 0.25, 0.06),
        "m1_artist_segment_plus_resid_s0p50": ("m1_artist_median_pred_log", 0.50, 0.06),
        "hybrid_l4_m1_segment_plus_resid_s0p50": ("hybrid", 0.50, 0.06),
        "source_l4_segment_soft_blend": ("soft_blend_l4", 0.20, 0.00),
        "source_hybrid_segment_soft_blend": ("soft_blend_hybrid", 0.20, 0.00),
    }
    for source_candidate in top_source_candidates():
        for mode, (segment_col, strength, cap) in configs.items():
            def make_pred(frame: pd.DataFrame, sc=segment_col, st=strength, cp=cap) -> np.ndarray:
                src = frame["pred_log"].to_numpy(float)
                if sc == "hybrid":
                    seg = np.nanmedian(frame[["l4_segment_pred_log", "m1_artist_median_pred_log"]].to_numpy(float), axis=1)
                    base_ref = frame["l4_base_pred_log"].to_numpy(float)
                elif sc == "soft_blend_l4":
                    seg = frame["l4_segment_pred_log"].to_numpy(float)
                    seg = np.where(np.isfinite(seg), seg, src)
                    return src * (1.0 - st) + seg * st
                elif sc == "soft_blend_hybrid":
                    seg = np.nanmedian(frame[["l4_segment_pred_log", "m1_artist_median_pred_log"]].to_numpy(float), axis=1)
                    seg = np.where(np.isfinite(seg), seg, src)
                    return src * (1.0 - st) + seg * st
                else:
                    seg = frame[sc].to_numpy(float)
                    base_ref = frame["l4_base_pred_log"].to_numpy(float)
                seg = np.where(np.isfinite(seg), seg, src)
                base_ref = np.where(np.isfinite(base_ref), base_ref, frame["base_pred_log"].to_numpy(float))
                resid = np.clip(src - base_ref, -cp, cp)
                return seg + resid * st
            specs.append({"candidate": f"{source_candidate}__segmix={mode}", "source_candidate": source_candidate, "policy": mode, "pred_log": make_pred})
    return evaluate_transforms(
        FPOL12_DIR,
        "PP-FPOL12",
        "PP-FPOL12 segment median + Huber residual 혼합",
        source,
        specs,
        ["segment priors: L4 quantile-width segment median, M1 artist median", "residual: FPOL6 source - L4 warm Huber baseline"],
    )


def write_todo() -> None:
    ensure_dirs(BATCH_DIR)
    md = """# PP-FPOL9~12 남은 방법 배치 투두

- [x] 공통 source 후보: FPOL6 상위 20개 후보 고정
- [ ] PP-FPOL9: quantile width 기반 동적 cap/strength
- [ ] PP-FPOL10: 모델 간 예측 gap 기반 라우팅
- [ ] PP-FPOL11: tail-only 보정
- [ ] PP-FPOL12: segment median + Huber residual 혼합
- [ ] FPOL6 기존 최고 후보와 통합 비교
"""
    (BATCH_DIR / "reports/planned_remaining_methods_todo.md").write_text(md, encoding="utf-8")
    write_manifest(BATCH_DIR, {"experiment_id": "PP-FPOL9_12", "source": "PP-FPOL6 top candidates"})


def summarize() -> None:
    ensure_dirs(BATCH_DIR)
    dirs = {
        "PP-FPOL9": FPOL9_DIR,
        "PP-FPOL10": FPOL10_DIR,
        "PP-FPOL11": FPOL11_DIR,
        "PP-FPOL12": FPOL12_DIR,
    }
    frames = []
    for source, d in dirs.items():
        metrics_path = d / "outputs/candidate_metrics.csv"
        if metrics_path.exists():
            df = pd.read_csv(metrics_path)
            df = df[df["split"].eq("test")].copy()
            df["source"] = source
            frames.append(df)
    all_test = pd.concat(frames, ignore_index=True)
    all_test.to_csv(BATCH_DIR / "outputs/all_fpol9_12_test_metrics.csv", index=False)

    rows = []
    for label, order in [
        ("MAPE 최저", ["MAPE", "MdAPE"]),
        ("균형 최저", ["balanced_delta", "MAPE"]),
        ("p95 최저", ["p95_APE", "MAPE"]),
    ]:
        row = all_test.sort_values(order).head(1).copy()
        row["selection"] = label
        rows.append(row)
    by_exp = []
    for source, group in all_test.groupby("source", sort=False):
        row = group.sort_values(["balanced_delta", "MAPE"]).head(1).copy()
        row["selection"] = f"{source} 균형 최저"
        by_exp.append(row)
    summary = pd.concat(rows + by_exp, ignore_index=True)
    summary.to_csv(BATCH_DIR / "outputs/final_remaining_method_recommendations.csv", index=False)

    cols = ["selection", "source", "candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "balanced_delta", "improves_all_three"]
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# PP-FPOL9~12 남은 방법 배치 최종 요약

- 작성일: {generated}
- 공통 source: FPOL6 상위 20개 후보
- 평가 기준: validation/test 동일 split, baseline은 각 row의 `base_pred_log`

## 최종 추천

{markdown_table(summary, cols)}

## 해석

- `PP-FPOL9`는 quantile width가 큰 불확실 구간에서는 보정 cap/strength를 줄이고, 낮은 구간에서는 보정을 열어주는 실험입니다.
- `PP-FPOL10`은 P2/L8/L9/M1 보조 예측과 source 예측의 gap을 이용해 blend 또는 damp를 수행합니다.
- `PP-FPOL11`은 pred price tail과 size tail에만 보정을 집중해 p95 방어력을 확인합니다.
- `PP-FPOL12`는 segment median prior에 FPOL6 residual을 제한적으로 얹는 방식입니다.

## 산출물

- `outputs/all_fpol9_12_test_metrics.csv`
- `outputs/final_remaining_method_recommendations.csv`
"""
    (BATCH_DIR / "reports/final_remaining_method_summary.md").write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>PP-FPOL9~12 요약</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:32px;color:#172033}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border:1px solid #d4d9e2;padding:6px 8px;vertical-align:top}}th{{background:#edf2f7}}td{{word-break:break-word}}</style>
</head><body><h1>PP-FPOL9~12 남은 방법 배치 최종 요약</h1>{html_table(summary, cols)}</body></html>"""
    (BATCH_DIR / "reports/final_remaining_method_summary.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["todo", "fpol9", "fpol10", "fpol11", "fpol12", "summary", "all"], default="all")
    args = parser.parse_args()
    if args.step in {"todo", "all"}:
        write_todo()
    if args.step in {"fpol9", "all"}:
        run_fpol9()
    if args.step in {"fpol10", "all"}:
        run_fpol10()
    if args.step in {"fpol11", "all"}:
        run_fpol11()
    if args.step in {"fpol12", "all"}:
        run_fpol12()
    if args.step in {"summary", "all"}:
        summarize()


if __name__ == "__main__":
    main()
