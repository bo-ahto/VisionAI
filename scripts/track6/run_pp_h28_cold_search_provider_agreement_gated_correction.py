#!/usr/bin/env python3
"""Run PP-H28: provider-agreement-gated Cold search correction validation.

Tests whether gating the PP-H23 search corrections by provider agreement makes
them a safe Cold improvement. Uses precomputed search-correction predictions and
per-artist provider agreement (no live search).

Finding-driven: provider agreement is only available for 78 artists, with NO high
grade (max score < 0.70), so "apply only on high agreement" is infeasible. This
experiment quantifies that, validates the ungated search correction as a defense
candidate via repeated subsampling, and reports an honest gating verdict.
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

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-H28"
EXP_SLUG = "PP-H28_cold_search_provider_agreement_gated_correction"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Cold 검색 provider agreement 기반 제한 보정 검증"

PRED_PATH = REPO / "experiments" / "track6" / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"
AGREE_PATH = REPO / "experiments" / "track6" / "PP-H22_provider_agreement_stability" / "outputs" / "provider_agreement_by_artist.csv"

BASE_COL = "pred_log"
SOURCE_GROUPS = ["gallery_museum", "social_blog", "exhibition", "art_general"]
CAPS = ["0.1", "0.2"]
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


def load() -> pd.DataFrame:
    pred = pd.read_csv(PRED_PATH, low_memory=False)
    ag = pd.read_csv(AGREE_PATH, low_memory=False)[[
        "artist_search_name", "provider_agreement_score", "provider_agreement_grade", "provider_disagreement_risk_flag"
    ]].drop_duplicates("artist_search_name")
    m = pred.merge(ag, on="artist_search_name", how="left")
    m["provider_agreement_grade"] = m["provider_agreement_grade"].fillna("missing")
    m["provider_disagreement_risk_flag"] = m["provider_disagreement_risk_flag"].fillna(True).astype(bool)
    return m


def candidate_cols(m: pd.DataFrame) -> dict[str, str]:
    out = {"base_pp_y2": BASE_COL}
    for g in SOURCE_GROUPS:
        for cap in CAPS:
            col = f"h23_{g}_median_cap{cap}__pred_log"
            if col in m.columns:
                out[f"ungated_{g}_cap{cap}"] = col
    return out


def gated_pred(m: pd.DataFrame, corr_col: str, mode: str) -> np.ndarray:
    base = m[BASE_COL].to_numpy(dtype=float)
    corr = m[corr_col].to_numpy(dtype=float)
    if mode == "not_risk":
        mask = ~m["provider_disagreement_risk_flag"].to_numpy()
    elif mode == "medium":
        mask = (m["provider_agreement_grade"] == "medium").to_numpy()
    else:
        raise ValueError(mode)
    out = base.copy()
    out[mask] = corr[mask]
    return out


def repeated_subsample(val: pd.DataFrame, cands: dict[str, np.ndarray]) -> pd.DataFrame:
    val = val.reset_index(drop=True)
    n = len(val)
    price = val["actual_price"].to_numpy(dtype=float)
    artists = val["artist_key"].astype(str).fillna("__MISSING__")
    uniq = artists.unique()
    base_pred = cands["base_pp_y2"]
    rows: list[dict[str, Any]] = []
    for rep in range(N_REPEATS):
        rng = np.random.default_rng(BASE_SEED + rep)
        row_folds = np.array_split(rng.permutation(n), N_FOLDS)
        art_folds = np.array_split(rng.permutation(uniq), N_FOLDS)
        plans = [("row", [f for f in row_folds]),
                 ("artist", [np.flatnonzero(artists.isin(set(f)).to_numpy()) for f in art_folds])]
        for scheme, folds in plans:
            for fold_id, idx in enumerate(folds, 1):
                if len(idx) == 0:
                    continue
                p = price[idx]
                b_md, b_ma, b_p95 = triplet(p, base_pred[idx])
                for name, pred in cands.items():
                    md, ma, p95 = triplet(p, pred[idx])
                    rows.append({"scheme": scheme, "repeat": rep, "fold": fold_id, "candidate": name,
                                 "MdAPE": md, "MAPE": ma, "p95_APE": p95,
                                 "base_MdAPE": b_md, "base_MAPE": b_ma, "base_p95_APE": b_p95})
    return pd.DataFrame(rows)


def summarize(sub: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scheme, cand), g in sub.groupby(["scheme", "candidate"], observed=False):
        rows.append({"scheme": scheme, "candidate": cand,
                     "mean_MdAPE": g["MdAPE"].mean(), "mean_MAPE": g["MAPE"].mean(), "mean_p95_APE": g["p95_APE"].mean(),
                     "prob_MdAPE_improve": float((g["MdAPE"] < g["base_MdAPE"]).mean()),
                     "prob_MAPE_improve": float((g["MAPE"] < g["base_MAPE"]).mean()),
                     "prob_p95_improve": float((g["p95_APE"] < g["base_p95_APE"]).mean())})
    return pd.DataFrame(rows).sort_values(["scheme", "mean_MAPE"])


def agreement_breakdown(m: pd.DataFrame, corr_col: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, s in m.groupby("split", observed=False):
        for grade, g in s.groupby("provider_agreement_grade", observed=False):
            price = g["actual_price"].to_numpy(dtype=float)
            b = triplet(price, g[BASE_COL].to_numpy())
            c = triplet(price, g[corr_col].to_numpy())
            rows.append({"split": split, "grade": str(grade), "n": len(g),
                         "base_MdAPE": b[0], "corr_MdAPE": c[0], "base_MAPE": b[1], "corr_MAPE": c[1],
                         "base_p95": b[2], "corr_p95": c[2]})
    return pd.DataFrame(rows)


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
    m = load()
    val = m[m["split"] == "validation"].copy()
    test = m[m["split"] == "test"].copy()

    cols = candidate_cols(m)
    # agreement coverage facts
    grade_counts = m["provider_agreement_grade"].value_counts().to_dict()
    n_high = int(grade_counts.get("high", 0))
    n_artists_with_agreement = int(m.loc[m["provider_agreement_grade"] != "missing", "artist_search_name"].nunique())

    # repeated subsample on validation (ungated + base)
    val_cands = {name: val[col].to_numpy(dtype=float) for name, col in cols.items()}
    sub = repeated_subsample(val, val_cands)
    summary = summarize(sub)

    # pick best ungated by balanced validation defense robustness (MdAPE non-worse),
    # using artist-scheme improvement probabilities across all three metrics.
    base_val_md = triplet(val["actual_price"].to_numpy(dtype=float), val[BASE_COL].to_numpy())[0]
    ung = summary[(summary["scheme"] == "artist") & (summary["candidate"].str.startswith("ungated"))].copy()
    ung["defense_score"] = ung["prob_MAPE_improve"] + ung["prob_p95_improve"] + ung["prob_MdAPE_improve"]
    ung_ok = ung[ung["mean_MdAPE"] <= base_val_md + 0.01].sort_values(["defense_score", "mean_MAPE"], ascending=[False, True])
    best_ungated = ung_ok["candidate"].iloc[0] if not ung_ok.empty else ung.sort_values("defense_score", ascending=False)["candidate"].iloc[0]
    best_source = best_ungated.replace("ungated_", "")  # e.g. gallery_museum_cap0.2
    best_corr_col = cols[best_ungated]

    # gate variants on the best source
    gate_not_risk = gated_pred(m, best_corr_col, "not_risk")
    gate_medium = gated_pred(m, best_corr_col, "medium")

    # test confirmation
    test_mask = (m["split"] == "test").to_numpy()
    price_t = test["actual_price"].to_numpy(dtype=float)
    test_rows: list[dict[str, Any]] = []
    test_cands = {"base_pp_y2": test[BASE_COL].to_numpy(dtype=float)}
    for name, col in cols.items():
        if name.startswith("ungated"):
            test_cands[name] = test[col].to_numpy(dtype=float)
    test_cands["gate_not_risk(on " + best_source + ")"] = gate_not_risk[test_mask]
    test_cands["gate_medium(on " + best_source + ")"] = gate_medium[test_mask]
    for name, pred in test_cands.items():
        md, ma, p95 = triplet(price_t, pred)
        test_rows.append({"candidate": name, "test_MdAPE": md, "test_MAPE": ma, "test_p95_APE": p95})
    test_df = pd.DataFrame(test_rows)

    breakdown = agreement_breakdown(m, best_corr_col)

    # how many test rows do the gates actually change?
    gate_changed = {"gate_not_risk": int(np.sum(gate_not_risk[test_mask] != test[BASE_COL].to_numpy())),
                    "gate_medium": int(np.sum(gate_medium[test_mask] != test[BASE_COL].to_numpy()))}

    out = EXP_DIR / "outputs"
    summary.to_csv(out / "repeated_subsample_summary.csv", index=False)
    breakdown.to_csv(out / "agreement_grade_breakdown.csv", index=False)
    test_df.to_csv(out / "test_metrics.csv", index=False)

    # verdict
    bs = summary[(summary["scheme"] == "artist") & (summary["candidate"] == best_ungated)].iloc[0]
    corr_defense_ok = bs["prob_MAPE_improve"] >= 0.70 and bs["prob_p95_improve"] >= 0.70
    gating_actionable = n_high > 0 and (gate_changed["gate_not_risk"] + gate_changed["gate_medium"]) > 0
    verdict = []
    verdict.append(f"검색 보정(`{best_ungated}`) 방어 유효: {corr_defense_ok} (artist subsample MAPE/p95 개선확률 {bs['prob_MAPE_improve']:.2f}/{bs['prob_p95_improve']:.2f})")
    verdict.append(f"provider agreement 게이팅 실행 가능: {gating_actionable} (high 등급 {n_high}개, agreement 보유 작가 {n_artists_with_agreement}명, test gate 변경행 {gate_changed})")
    if corr_defense_ok and not gating_actionable:
        decision = "검색 보정은 유효한 MAPE/p95 방어 후보이나, provider agreement 게이팅은 현 데이터로 비현실(high 등급 0, 커버리지 극소). 안전장치는 cap 기반 방어층 + 저신뢰 검수 플래그로, agreement 커버리지 확대는 별도 데이터 과제."
    elif corr_defense_ok and gating_actionable:
        decision = "검색 보정 방어 유효 + 게이팅 실행 가능. 제한 보정 정책 검토."
    else:
        decision = "검색 보정 방어 근거 부족. 보류."

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 데이터: precomputed 검색 보정 예측 + provider agreement (live 검색 불필요)",
        "- 주의: h23 검색 보정은 상류 고정 예측값. 반복 subsample은 fold refit이 아니라 고정 후보 robustness 평가.",
        "",
        "## 1. 실행 결론",
        "",
        f"- {decision}",
        *[f"- {v}" for v in verdict],
        "",
        "## 2. provider agreement 커버리지 사실",
        "",
        f"- agreement 보유 작가: {n_artists_with_agreement}명, grade 분포(전 행): {grade_counts}",
        f"- **high(≥0.70) 등급: {n_high}개** → 'high에서만 적용' 게이트 실행 불가",
        f"- test에서 gate 변경 행수: {gate_changed} (전체 test {len(test)}행)",
        "",
        "## 3. validation 반복 subsample 요약 (base 대비 개선확률)",
        "",
        markdown_table(summary[summary["scheme"] == "artist"][["candidate", "mean_MdAPE", "mean_MAPE", "mean_p95_APE", "prob_MdAPE_improve", "prob_MAPE_improve", "prob_p95_improve"]].round(4)),
        "",
        "## 4. test 확인",
        "",
        markdown_table(test_df),
        "",
        "## 5. agreement grade별 보정 효과 (선정 source)",
        "",
        f"- 선정 source: `{best_source}`",
        markdown_table(breakdown),
        "",
        "## 6. 산출물",
        "",
        "- `outputs/repeated_subsample_summary.csv`, `outputs/agreement_grade_breakdown.csv`, `outputs/test_metrics.csv`, `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_h28_cold_search_provider_agreement_gated_correction_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_h28_cold_search_provider_agreement_gated_correction_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {"experiment_id": EXP_ID, "experiment_slug": EXP_SLUG,
              "pred_path": str(PRED_PATH.relative_to(REPO)), "agree_path": str(AGREE_PATH.relative_to(REPO)),
              "base_seed": BASE_SEED, "n_repeats": N_REPEATS, "n_folds": N_FOLDS,
              "best_ungated": best_ungated, "n_high_grade": n_high,
              "n_artists_with_agreement": n_artists_with_agreement, "grade_counts": grade_counts,
              "gate_changed_rows_test": gate_changed, "corr_defense_ok": bool(corr_defense_ok),
              "gating_actionable": bool(gating_actionable), "decision": decision}
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] agreement artists={n_artists_with_agreement}, high grade={n_high}, grades={grade_counts}")
    print(f"[{EXP_ID}] best ungated (val MAPE defense): {best_ungated}")
    print(test_df.to_string(index=False))
    print(f"[{EXP_ID}] gate changed rows (test): {gate_changed}")
    print(f"[{EXP_ID}] decision: {decision}")


if __name__ == "__main__":
    main()
