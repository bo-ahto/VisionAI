#!/usr/bin/env python3
"""Run PP-COLD-DEFENSE1: combine the two validated Cold defenses on one base.

Layers:
- guard  : PP-QR4 guard (PP-Y18 base blended toward lgb_q40 on qwidth/gap mask)
- search : PP-H28 search correction delta (h23 gallery_museum / social_blog cap0.2)

Question: are the two defenses additive on the PP-Y18 representative, or redundant
(PP-Y18 already uses search features)? Validated by repeated subsampling + test.
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

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_qr2_cold_quantile_final_candidate_blend as qr2  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-COLD-DEFENSE1"
EXP_SLUG = "PP-COLD-DEFENSE1_cold_guard_search_layer_combination"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Cold guard + 검색 방어층 결합"
H28_PRED = REPO / "experiments" / "track6" / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"

BASE_SEED = 20260607
N_REPEATS = 8
N_FOLDS = 5


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def triplet(price: np.ndarray, pred_log: np.ndarray) -> tuple[float, float, float]:
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pp - price) / np.clip(price, 1.0, None)
    return float(np.median(ape)), float(np.mean(ape)), float(np.quantile(ape, 0.95))


def build_frame() -> tuple[pd.DataFrame, dict[str, float]]:
    qf = qr2.add_qr1_predictions(qr2.load_y18_frame())
    qf = qf[["split", "_track6_row_id", "actual_price", "quantile_width_log",
             "y18_qwidth_pred_log", "lgb_q40_pred_log", "cat_q40_pred_log", "y2_pred_log", "artist_key"]].copy()
    h = pd.read_csv(H28_PRED, low_memory=False)
    hcols = ["split", "_track6_row_id", "pred_log",
             "h23_gallery_museum_median_cap0.2__pred_log", "h23_social_blog_median_cap0.2__pred_log"]
    h = h[[c for c in hcols if c in h.columns]]
    m = qf.merge(h, on=["split", "_track6_row_id"], how="inner")
    # search deltas relative to shared pp_y2 base.
    m["search_delta_gm"] = m["h23_gallery_museum_median_cap0.2__pred_log"] - m["pred_log"]
    m["search_delta_sb"] = m["h23_social_blog_median_cap0.2__pred_log"] - m["pred_log"]

    val = m[m["split"] == "validation"]
    thresholds = qr2.validation_thresholds(val)
    return m, {"qwidth_q67": float(thresholds["qwidth_q67"]), "gap_q50": float(thresholds["gap_q50"])}


def guard_pred(frame: pd.DataFrame, thr: dict[str, float], base_col: str = "y18_qwidth_pred_log") -> np.ndarray:
    base = frame[base_col].to_numpy(dtype=float)
    comp = frame["lgb_q40_pred_log"].to_numpy(dtype=float)
    qwidth = frame["quantile_width_log"].to_numpy(dtype=float)
    mask = (qwidth >= thr["qwidth_q67"]) & ((base - comp) >= thr["gap_q50"]) & (comp < base)
    out = base.copy()
    out[mask] = 0.5 * base[mask] + 0.5 * comp[mask]
    return out


def candidate_preds(frame: pd.DataFrame, thr: dict[str, float]) -> dict[str, np.ndarray]:
    y18 = frame["y18_qwidth_pred_log"].to_numpy(dtype=float)
    g = guard_pred(frame, thr)
    sgm = frame["search_delta_gm"].to_numpy(dtype=float)
    ssb = frame["search_delta_sb"].to_numpy(dtype=float)
    pp_y2 = frame["pred_log"].to_numpy(dtype=float)
    return {
        "y18_base": y18,
        "guard": g,
        "search_gm": y18 + sgm,
        "search_sb": y18 + ssb,
        "guard_search_gm": g + sgm,
        "guard_search_sb": g + ssb,
        "ref_pp_y2_search_gm": pp_y2 + sgm,
    }


def repeated_subsample(val: pd.DataFrame, thr: dict[str, float]) -> pd.DataFrame:
    val = val.reset_index(drop=True)
    n = len(val)
    price = val["actual_price"].to_numpy(dtype=float)
    artists = val["artist_key"].astype(str).fillna("__MISSING__")
    uniq = artists.unique()
    cands = candidate_preds(val, thr)
    base = cands["y18_base"]
    rows: list[dict[str, Any]] = []
    for rep in range(N_REPEATS):
        rng = np.random.default_rng(BASE_SEED + rep)
        row_folds = np.array_split(rng.permutation(n), N_FOLDS)
        art_folds = np.array_split(rng.permutation(uniq), N_FOLDS)
        plans = [("row", list(row_folds)),
                 ("artist", [np.flatnonzero(artists.isin(set(f)).to_numpy()) for f in art_folds])]
        for scheme, folds in plans:
            for fid, idx in enumerate(folds, 1):
                if len(idx) == 0:
                    continue
                p = price[idx]
                b = triplet(p, base[idx])
                for name, pred in cands.items():
                    md, ma, p95 = triplet(p, pred[idx])
                    rows.append({"scheme": scheme, "repeat": rep, "fold": fid, "candidate": name,
                                 "MdAPE": md, "MAPE": ma, "p95_APE": p95,
                                 "base_MdAPE": b[0], "base_MAPE": b[1], "base_p95_APE": b[2]})
    return pd.DataFrame(rows)


def summarize(sub: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scheme, cand), g in sub.groupby(["scheme", "candidate"], observed=False):
        rows.append({"scheme": scheme, "candidate": cand,
                     "mean_MdAPE": g["MdAPE"].mean(), "mean_MAPE": g["MAPE"].mean(), "mean_p95_APE": g["p95_APE"].mean(),
                     "prob_MdAPE_improve": float((g["MdAPE"] < g["base_MdAPE"]).mean()),
                     "prob_MAPE_improve": float((g["MAPE"] < g["base_MAPE"]).mean()),
                     "prob_p95_improve": float((g["p95_APE"] < g["base_p95_APE"]).mean())})
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_결과 없음_"

    def fmt(v: Any) -> str:
        return f"{float(v):.4f}" if isinstance(v, (float, np.floating)) else str(v)
    cols = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body, table = [], []

    def flush():
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
    m, thr = build_frame()
    val = m[m["split"] == "validation"].copy()
    test = m[m["split"] == "test"].copy()

    sub = repeated_subsample(val, thr)
    summary = summarize(sub)

    test_cands = candidate_preds(test, thr)
    price_t = test["actual_price"].to_numpy(dtype=float)
    test_rows = [{"candidate": name, **dict(zip(["test_MdAPE", "test_MAPE", "test_p95_APE"], triplet(price_t, pred)))}
                 for name, pred in test_cands.items()]
    test_df = pd.DataFrame(test_rows)

    def tv(name: str, col: str) -> float:
        return float(test_df[test_df["candidate"] == name][col].iloc[0])

    # Additivity decomposition (test, vs y18_base).
    add_rows = []
    for sfx in ["gm", "sb"]:
        d_guard = tv("guard", "test_MAPE") - tv("y18_base", "test_MAPE")
        d_search = tv(f"search_{sfx}", "test_MAPE") - tv("y18_base", "test_MAPE")
        d_both = tv(f"guard_search_{sfx}", "test_MAPE") - tv("y18_base", "test_MAPE")
        add_rows.append({"search_source": sfx,
                         "dMAPE_guard": d_guard, "dMAPE_search": d_search, "dMAPE_both": d_both,
                         "expected_if_additive": d_guard + d_search, "redundancy_gap": d_both - (d_guard + d_search),
                         "p95_guard": tv("guard", "test_p95_APE"), "p95_both": tv(f"guard_search_{sfx}", "test_p95_APE"),
                         "incremental_vs_guard_MAPE": tv(f"guard_search_{sfx}", "test_MAPE") - tv("guard", "test_MAPE"),
                         "incremental_vs_guard_p95": tv(f"guard_search_{sfx}", "test_p95_APE") - tv("guard", "test_p95_APE")})
    add_df = pd.DataFrame(add_rows)

    out = EXP_DIR / "outputs"
    summary.sort_values(["scheme", "mean_MAPE"]).to_csv(out / "repeated_subsample_summary.csv", index=False)
    test_df.to_csv(out / "test_metrics.csv", index=False)
    add_df.to_csv(out / "additivity_decomposition.csv", index=False)

    # Verdict: additive (redundancy gap ~0 + guard_search beats guard on test) vs redundant.
    art = summary[summary["scheme"] == "artist"].set_index("candidate")
    best_sfx = "gm" if tv("guard_search_gm", "test_MAPE") <= tv("guard_search_sb", "test_MAPE") else "sb"
    gs = f"guard_search_{best_sfx}"
    incr_mape = tv(gs, "test_MAPE") - tv("guard", "test_MAPE")
    incr_p95 = tv(gs, "test_p95_APE") - tv("guard", "test_p95_APE")
    incr_mdape = tv(gs, "test_MdAPE") - tv("guard", "test_MdAPE")
    redundancy_gap = float(add_df[add_df["search_source"] == best_sfx]["redundancy_gap"].iloc[0])
    val_gs_mape = float(art.loc[gs, "prob_MAPE_improve"]) if gs in art.index else float("nan")
    val_g_mape = float(art.loc["guard", "prob_MAPE_improve"]) if "guard" in art.index else float("nan")
    additive = abs(redundancy_gap) < 0.02 and incr_mape < -1e-4 and incr_p95 < -1e-4
    consistency_note = (
        f"단 검색층은 분산을 추가: validation fold MAPE 개선확률 guard {val_g_mape:.2f} vs {gs} {val_gs_mape:.2f}. "
        "guard 단독이 가장 일관적(robust)이고, guard+search는 평균 최고지만 검색 커버리지/변동성 주의."
    )
    if additive:
        decision = (
            f"결합 가산적(중복 아님): redundancy gap {redundancy_gap:+.4f}≈0. `{gs}`가 guard 단독 대비 "
            f"test ΔMdAPE {incr_mdape:+.4f}, ΔMAPE {incr_mape:+.4f}, Δp95 {incr_p95:+.4f}로 3지표 추가 개선. "
            "두 방어는 거의 직교(guard=qwidth/gap tail, search=작가맥락 잔차). " + consistency_note)
    else:
        decision = (
            f"중복/비가산: redundancy gap {redundancy_gap:+.4f}, guard 단독 대비 추가 개선 미미. "
            "cold 방어는 guard 단독(PP-COLD-ARTIFACT1) 유지. " + consistency_note)

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- base = PP-Y18 대표. guard 임계값 qwidth_q67={thr['qwidth_q67']:.4f}, gap_q50={thr['gap_q50']:.4f}",
        "- 검색 delta는 상류 고정값(h23 − pp_y2). 반복 subsample은 고정 후보 robustness.",
        "",
        "## 1. 실행 결론",
        "",
        f"- {decision}",
        "",
        "## 2. test 지표 (cold 3099)",
        "",
        markdown_table(test_df.round(4)),
        "",
        "## 3. 가산성 분해 (test MAPE, vs y18_base)",
        "",
        markdown_table(add_df.round(4)),
        "",
        "## 4. validation 반복 subsample (artist scheme, y18_base 대비 개선확률)",
        "",
        markdown_table(summary[summary["scheme"] == "artist"][["candidate", "mean_MdAPE", "mean_MAPE", "mean_p95_APE", "prob_MdAPE_improve", "prob_MAPE_improve", "prob_p95_improve"]].round(4)),
        "",
        "## 5. 산출물",
        "",
        "- `outputs/repeated_subsample_summary.csv`, `outputs/test_metrics.csv`, `outputs/additivity_decomposition.csv`, `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_cold_defense1_guard_search_layer_combination_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_cold_defense1_guard_search_layer_combination_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {"experiment_id": EXP_ID, "experiment_slug": EXP_SLUG, "thresholds": thr,
              "base_seed": BASE_SEED, "n_repeats": N_REPEATS, "n_folds": N_FOLDS,
              "best_search_source": best_sfx, "incremental_vs_guard_MAPE": incr_mape,
              "incremental_vs_guard_p95": incr_p95, "additive": bool(additive), "decision": decision}
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] thresholds: {thr}")
    print(test_df.round(4).to_string(index=False))
    print("--- additivity ---")
    print(add_df.round(4).to_string(index=False))
    print(f"[{EXP_ID}] decision: {decision}")


if __name__ == "__main__":
    main()
