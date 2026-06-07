#!/usr/bin/env python3
"""Run PP-QR4: repeated split / artist holdout / test bootstrap revalidation of the
two PP-QR3 test-surviving Cold candidates.

PP-QR3 left an explicit open item: its two test survivors (a qwidth+pred_gap
segment correction and a q40 guard blend) should be checked once more under
repeated splits before any final swap. PP-QR4 does that with the same protocol
used for the Warm side (PP-AMW6): row 5-fold x 12 seeds, artist GroupKFold 5-fold
x 12 seeds, plus a 400x test bootstrap.

Discipline:
- Correction maps / thresholds are refit on each fold's calibration part only.
- The fixed test set is used once for the final bootstrap confirmation.
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
EXP_ID = "PP-QR4"
EXP_SLUG = "PP-QR4_cold_qwidth_repeated_split_revalidation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Cold qwidth/guard 생존 후보 반복 split·artist holdout 재검증"

BASELINE = "component_pp_y18_qwidth_bin"
Y2 = "component_pp_y2_baseline"
SEGMENT_CAND = "segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50"
GUARD_CAND = "guard_y18_lgb_q40_qwidth67_gap50_down_w0p50"
TARGETS = [BASELINE, Y2, SEGMENT_CAND, GUARD_CAND]

BASE_SEED = 20260607
N_REPEATS = 12
N_FOLDS = 5
N_BOOTSTRAP = 400
BASELINE_TEST_MDAPE = 0.4247  # PP-Y18 reference point estimate


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_triplet(actual_price: np.ndarray, pred_log: np.ndarray) -> tuple[float, float, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return float(np.median(ape)), float(np.mean(ape)), float(np.quantile(ape, 0.95))


def build_targets(train: pd.DataFrame, eval_df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Refit thresholds/corrections on train, build only the 4 target candidates on eval."""
    thresholds = qr2.validation_thresholds(train)
    seg_th = qr2.segment_thresholds(train)
    train_b = qr2.add_segment_columns(train, seg_th)
    eval_b = qr2.add_segment_columns(eval_df, seg_th)
    pool: dict[str, np.ndarray] = {}
    for c in qr2.fixed_candidates(eval_df):
        pool[c.candidate] = np.asarray(c.pred_log, dtype=float)
    for c in qr2.guarded_candidates(eval_df, thresholds):
        if c.candidate in TARGETS:
            pool[c.candidate] = np.asarray(c.pred_log, dtype=float)
    for c in qr2.segment_correction_candidates(eval_df, train_b, eval_b):
        if c.candidate in TARGETS:
            pool[c.candidate] = np.asarray(c.pred_log, dtype=float)
    return {name: pool[name] for name in TARGETS if name in pool}


def repeated_holdout(val: pd.DataFrame) -> pd.DataFrame:
    val = val.reset_index(drop=True)
    n = len(val)
    artists = val["artist_key"].astype(str).fillna("__MISSING__")
    uniq = artists.unique()
    rows: list[dict[str, Any]] = []

    for repeat in range(N_REPEATS):
        rng = np.random.default_rng(BASE_SEED + repeat)
        # row 5-fold
        row_folds = np.array_split(rng.permutation(n), N_FOLDS)
        # artist 5-fold
        art_folds = np.array_split(rng.permutation(uniq), N_FOLDS)

        plans = [("row_5fold", [(np.setdiff1d(np.arange(n), f), f) for f in row_folds])]
        art_plan = []
        for f in art_folds:
            hold_mask = artists.isin(set(f)).to_numpy()
            art_plan.append((np.flatnonzero(~hold_mask), np.flatnonzero(hold_mask)))
        plans.append(("artist_5fold", art_plan))

        for scheme, folds in plans:
            for fold_id, (tr_idx, ho_idx) in enumerate(folds, start=1):
                train = val.iloc[tr_idx].reset_index(drop=True)
                hold = val.iloc[ho_idx].reset_index(drop=True)
                if train.empty or hold.empty:
                    continue
                actual = hold["actual_price"].to_numpy(dtype=float)
                preds = build_targets(train, hold)
                base_md, base_ma, base_p95 = metric_triplet(actual, preds[BASELINE])
                for name, pred in preds.items():
                    md, ma, p95 = metric_triplet(actual, pred)
                    rows.append({
                        "scheme": scheme, "repeat": repeat, "fold": fold_id, "candidate": name,
                        "n": len(hold), "MdAPE": md, "MAPE": ma, "p95_APE": p95,
                        "base_MdAPE": base_md, "base_MAPE": base_ma, "base_p95_APE": base_p95,
                    })
    return pd.DataFrame(rows)


def summarize(holdout: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scheme, candidate), g in holdout.groupby(["scheme", "candidate"], observed=False):
        rows.append({
            "scheme": scheme, "candidate": candidate, "folds": len(g),
            "mean_MdAPE": g["MdAPE"].mean(), "std_MdAPE": g["MdAPE"].std(),
            "mean_MAPE": g["MAPE"].mean(), "mean_p95_APE": g["p95_APE"].mean(),
            "prob_MdAPE_improve": float((g["MdAPE"] < g["base_MdAPE"]).mean()),
            "prob_MAPE_improve": float((g["MAPE"] < g["base_MAPE"]).mean()),
            "prob_p95_improve": float((g["p95_APE"] < g["base_p95_APE"]).mean()),
        })
    return pd.DataFrame(rows).sort_values(["scheme", "mean_MdAPE"])


def test_bootstrap(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    preds = build_targets(val, test)
    actual = test["actual_price"].to_numpy(dtype=float)
    n = len(test)

    point_rows: list[dict[str, Any]] = []
    for name, pred in preds.items():
        md, ma, p95 = metric_triplet(actual, pred)
        point_rows.append({"candidate": name, "test_MdAPE": md, "test_MAPE": ma, "test_p95_APE": p95})
    point_df = pd.DataFrame(point_rows)

    rng = np.random.default_rng(BASE_SEED + 999)
    boot: dict[str, dict[str, list[float]]] = {name: {"MdAPE": [], "MAPE": [], "p95_APE": [], "md_improve": []} for name in preds}
    base_pred = preds[BASELINE]
    for _ in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, size=n)
        a = actual[idx]
        base_md = metric_triplet(a, base_pred[idx])[0]
        for name, pred in preds.items():
            md, ma, p95 = metric_triplet(a, pred[idx])
            boot[name]["MdAPE"].append(md); boot[name]["MAPE"].append(ma); boot[name]["p95_APE"].append(p95)
            boot[name]["md_improve"].append(1.0 if md < base_md else 0.0)

    ci_rows: list[dict[str, Any]] = []
    for name, d in boot.items():
        md = np.array(d["MdAPE"])
        ci_rows.append({
            "candidate": name,
            "boot_MdAPE_mean": float(md.mean()),
            "boot_MdAPE_ci_low": float(np.quantile(md, 0.025)),
            "boot_MdAPE_ci_high": float(np.quantile(md, 0.975)),
            "boot_MAPE_mean": float(np.mean(d["MAPE"])),
            "boot_p95_mean": float(np.mean(d["p95_APE"])),
            "prob_MdAPE_beats_baseline": float(np.mean(d["md_improve"])),
            "ci_high_le_baseline_ref": bool(np.quantile(md, 0.975) <= BASELINE_TEST_MDAPE),
        })
    return point_df, pd.DataFrame(ci_rows)


def verdict_for(candidate: str, objective: str, summary: pd.DataFrame, ci: pd.DataFrame, point: pd.DataFrame) -> tuple[str, dict[str, Any]]:
    row_s = summary[(summary["scheme"] == "row_5fold") & (summary["candidate"] == candidate)]
    art_s = summary[(summary["scheme"] == "artist_5fold") & (summary["candidate"] == candidate)]
    c = ci[ci["candidate"] == candidate]
    p = point[point["candidate"] == candidate]
    if row_s.empty or art_s.empty or c.empty:
        return "데이터 없음", {}

    def g(df: pd.DataFrame, col: str) -> float:
        return float(df[col].iloc[0])

    info = {
        "objective": objective,
        "row_prob_MdAPE": g(row_s, "prob_MdAPE_improve"), "artist_prob_MdAPE": g(art_s, "prob_MdAPE_improve"),
        "row_prob_MAPE": g(row_s, "prob_MAPE_improve"), "artist_prob_MAPE": g(art_s, "prob_MAPE_improve"),
        "row_prob_p95": g(row_s, "prob_p95_improve"), "artist_prob_p95": g(art_s, "prob_p95_improve"),
        "boot_MdAPE_ci_high": g(c, "boot_MdAPE_ci_high"),
        "test_MdAPE": g(p, "test_MdAPE") if not p.empty else float("nan"),
    }

    if objective == "representative":
        # MdAPE 대표 후보: 양 holdout에서 MdAPE 개선확률 >= 0.7 필요.
        row_md, art_md = info["row_prob_MdAPE"], info["artist_prob_MdAPE"]
        if row_md >= 0.70 and art_md >= 0.70:
            v = "채택 (대표 MdAPE 개선, artifact 후보 승급)"
        elif min(row_md, art_md) < 0.40 < max(row_md, art_md):
            v = "보류 (row/artist holdout 불일치 — 작가 구성 의존)"
        else:
            v = "중단 (MdAPE 반복 holdout 기준 미달)"
    else:  # defense (MAPE/p95)
        mape_ok = info["row_prob_MAPE"] >= 0.70 and info["artist_prob_MAPE"] >= 0.70
        p95_ok = info["row_prob_p95"] >= 0.70 and info["artist_prob_p95"] >= 0.70
        mdape_not_worse = info["test_MdAPE"] <= BASELINE_TEST_MDAPE + 1e-9
        if mape_ok and p95_ok and mdape_not_worse:
            v = "채택 (MAPE/p95 방어 후보, MdAPE 비악화)"
        elif (mape_ok or p95_ok) and mdape_not_worse:
            v = "조건부 채택 (방어 일부 지표만 견고)"
        else:
            v = "중단 (방어 반복 holdout 기준 미달)"
    return v, info


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
    frame = qr2.add_qr1_predictions(qr2.load_y18_frame())
    val = frame[frame["split"] == "validation"].copy()
    test = frame[frame["split"] == "test"].copy()

    holdout = repeated_holdout(val)
    summary = summarize(holdout)
    point_df, ci_df = test_bootstrap(val, test)

    verdicts = {}
    objectives = {SEGMENT_CAND: "representative", GUARD_CAND: "defense"}
    for cand, obj in objectives.items():
        v, info = verdict_for(cand, obj, summary, ci_df, point_df)
        verdicts[cand] = {"verdict": v, **info}

    out = EXP_DIR / "outputs"
    holdout.to_csv(out / "repeated_holdout_metrics.csv", index=False)
    summary.to_csv(out / "holdout_summary.csv", index=False)
    point_df.to_csv(out / "test_point_metrics.csv", index=False)
    ci_df.to_csv(out / "test_bootstrap_ci.csv", index=False)

    # readable summary pivots
    md_pivot = summary.pivot(index="candidate", columns="scheme", values="prob_MdAPE_improve").reset_index()
    holdmd = summary.pivot(index="candidate", columns="scheme", values="mean_MdAPE").reset_index()

    config = {
        "experiment_id": EXP_ID, "experiment_slug": EXP_SLUG,
        "targets": TARGETS, "base_seed": BASE_SEED, "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS, "n_bootstrap": N_BOOTSTRAP,
        "baseline_test_mdape_ref": BASELINE_TEST_MDAPE,
        "val_n": int(len(val)), "test_n": int(len(test)),
        "verdicts": verdicts,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    v_lines = []
    for cand in [SEGMENT_CAND, GUARD_CAND]:
        info = verdicts[cand]
        v_lines.append(
            f"- `{cand}` [{info['objective']}] → **{info['verdict']}** "
            f"(row/artist MdAPE 개선확률 {info['row_prob_MdAPE']:.2f}/{info['artist_prob_MdAPE']:.2f}, "
            f"MAPE {info['row_prob_MAPE']:.2f}/{info['artist_prob_MAPE']:.2f}, "
            f"p95 {info['row_prob_p95']:.2f}/{info['artist_prob_p95']:.2f}, test MdAPE {info['test_MdAPE']:.4f})"
        )

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 검증 대상: `{SEGMENT_CAND}`(대표 개선), `{GUARD_CAND}`(MAPE/p95 방어)",
        f"- 기준선: `{BASELINE}` (PP-Y18 qwidth, test MdAPE 참고 {BASELINE_TEST_MDAPE})",
        f"- 프로토콜: row 5-fold x {N_REPEATS} seeds + artist GroupKFold 5-fold x {N_REPEATS} seeds + test bootstrap {N_BOOTSTRAP}회. 보정맵은 fold calibration에서만 재학습",
        "",
        "## 1. 실행 결론",
        "",
        *v_lines,
        "",
        "## 2. holdout MdAPE 개선확률 (vs PP-Y18, scheme별)",
        "",
        markdown_table(md_pivot),
        "",
        "## 3. holdout 평균 MdAPE (scheme별)",
        "",
        markdown_table(holdmd),
        "",
        "## 4. holdout 후보 요약 (scheme별 상세)",
        "",
        markdown_table(summary.round(4)),
        "",
        "## 5. test 점추정",
        "",
        markdown_table(point_df),
        "",
        "## 6. test bootstrap (400회) 95% CI",
        "",
        markdown_table(ci_df),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/repeated_holdout_metrics.csv`, `outputs/holdout_summary.csv`",
        "- `outputs/test_point_metrics.csv`, `outputs/test_bootstrap_ci.csv`, `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_qr4_cold_qwidth_repeated_split_revalidation_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_qr4_cold_qwidth_repeated_split_revalidation_summary.html").write_text(md_to_html(md), encoding="utf-8")

    print(f"[{EXP_ID}] val={len(val)} test={len(test)} holdout_rows={len(holdout)}")
    print("--- holdout MdAPE improvement prob (vs PP-Y18) ---")
    print(md_pivot.to_string(index=False))
    print("--- test point ---")
    print(point_df.to_string(index=False))
    print("--- test bootstrap CI ---")
    print(ci_df.to_string(index=False))
    for cand in [SEGMENT_CAND, GUARD_CAND]:
        print(f"[{EXP_ID}] {cand}: {verdicts[cand]['verdict']}")


if __name__ == "__main__":
    main()
