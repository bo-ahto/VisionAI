#!/usr/bin/env python3
"""Run PP-SVCSHRINK1: Empirical-Bayes shrinkage of the Warm comparable price prior.

PP-SVC8 diagnosed the svc comparable prior staleness as a variance problem (coarse/
small comparable groups blow up on the 0604 new-label set). With no transaction-date
field available, recency refresh is impossible; this experiment instead rebuilds the
prior with hierarchical EB shrinkage (small groups shrink toward parent levels) and
checks whether that reduces the 0604 variance/error.

Self-contained: comparable-group medians + shrinkage only (no model retrain, no deps).
Shrinkage strength k is selected on validation; test_warm and 0604 are confirmation.
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
EXP_ID = "PP-SVCSHRINK1"
EXP_SLUG = "PP-SVCSHRINK1_warm_comparable_prior_shrinkage"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Warm 비교군 prior shrinkage 갱신"

TRAIN = REPO / "data" / "track6_split" / "track6_train.csv"
VAL = REPO / "data" / "track6_split" / "track6_val_warm.csv"
TEST = REPO / "data" / "track6_split" / "track6_test_warm.csv"
OPS = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

N_SIZE_BINS = 5
RAW_MIN_N = 5
K_GRID = [5, 20, 50, 100]
LEVELS = ["L1_artist", "L2_artist_size", "L3_artist_medium_support_size"]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def norm(s: pd.Series) -> pd.Series:
    return s.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})


def prep(df: pd.DataFrame, size_edges: np.ndarray | None) -> tuple[pd.DataFrame, np.ndarray]:
    out = pd.DataFrame()
    out["artist_key"] = norm(df["artist_key"])
    out["medium_category"] = norm(df["medium_category"])
    out["support_category"] = norm(df["support_category"])
    area = pd.to_numeric(df["area_cm2"], errors="coerce").to_numpy(dtype=float)
    if size_edges is None:
        finite = area[np.isfinite(area) & (area > 0)]
        size_edges = np.quantile(finite, [i / N_SIZE_BINS for i in range(1, N_SIZE_BINS)])
    sb = np.digitize(np.nan_to_num(area, nan=-1.0), size_edges, right=False)
    out["size_bin"] = pd.Series(sb).astype(str).to_numpy()
    return out, size_edges


def level_key(frame: pd.DataFrame, level: str) -> pd.Series:
    if level == "L1_artist":
        cols = ["artist_key"]
    elif level == "L2_artist_size":
        cols = ["artist_key", "size_bin"]
    else:
        cols = ["artist_key", "medium_category", "support_category", "size_bin"]
    return frame[cols].astype(str).agg("||".join, axis=1)


def train_groups(train_keys: pd.DataFrame, y: np.ndarray) -> tuple[dict[str, dict[str, tuple[float, int]]], float]:
    groups: dict[str, dict[str, tuple[float, int]]] = {}
    work = train_keys.copy()
    work["_y"] = y
    for level in LEVELS:
        k = level_key(work, level)
        agg = work.assign(_k=k).groupby("_k")["_y"].agg(["median", "count"])
        groups[level] = {str(idx): (float(r["median"]), int(r["count"])) for idx, r in agg.iterrows()}
    global_median = float(np.median(y))
    return groups, global_median


def raw_prior(eval_keys: pd.DataFrame, groups: dict, global_median: float) -> np.ndarray:
    n = len(eval_keys)
    keys_by_level = {lv: level_key(eval_keys, lv).to_numpy() for lv in LEVELS}
    out = np.full(n, global_median, dtype=float)
    for i in range(n):
        val = global_median
        for level in LEVELS:  # general -> specific; keep most specific with enough n
            g = groups[level].get(keys_by_level[level][i])
            if g is not None and g[1] >= RAW_MIN_N:
                val = g[0]
        out[i] = val
    return out


def shrunk_prior(eval_keys: pd.DataFrame, groups: dict, global_median: float, k: float) -> np.ndarray:
    n = len(eval_keys)
    keys_by_level = {lv: level_key(eval_keys, lv).to_numpy() for lv in LEVELS}
    out = np.empty(n, dtype=float)
    for i in range(n):
        est = global_median
        for level in LEVELS:  # general -> specific hierarchical blend
            g = groups[level].get(keys_by_level[level][i])
            if g is not None:
                m, cnt = g
                w = cnt / (cnt + k)
                est = w * m + (1.0 - w) * est
        out[i] = est
    return out


def triplet(price: np.ndarray, pred_log: np.ndarray, actual_log: np.ndarray) -> dict[str, float]:
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pp - price) / np.clip(price, 1.0, None)
    resid = actual_log - np.asarray(pred_log, dtype=float)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95)), "resid_std": float(np.std(resid))}


def load_eval(path: pd.DataFrame | Path, size_edges: np.ndarray, is_ops: bool) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    df = pd.read_csv(path, low_memory=False)
    if is_ops:
        df = df[df["actual_price_krw"].notna()].copy()
        usd = pd.to_numeric(df.get("actual_price_usd_equiv"), errors="coerce")
        df = df[~(usd < 50.0)].copy()
        price = pd.to_numeric(df["actual_price_krw"], errors="coerce").to_numpy(dtype=float)
    else:
        price = pd.to_numeric(df["price_krw"], errors="coerce").to_numpy(dtype=float)
    keys, _ = prep(df, size_edges)
    actual_log = np.log(np.clip(price, 1.0, None))
    return keys, price, actual_log


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_결과 없음_"

    def fmt(v: Any) -> str:
        return f"{float(v):.4f}" if isinstance(v, (float, np.floating)) else str(v)
    cols = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for r in frame.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in r) + " |")
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
    train_df = pd.read_csv(TRAIN, low_memory=False)
    train_keys, size_edges = prep(train_df, None)
    y_train = pd.to_numeric(train_df["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    groups, global_median = train_groups(train_keys, y_train)

    val_keys, val_price, val_alog = load_eval(VAL, size_edges, is_ops=False)
    test_keys, test_price, test_alog = load_eval(TEST, size_edges, is_ops=False)
    ops_keys, ops_price, ops_alog = load_eval(OPS, size_edges, is_ops=True)

    # k selection on validation (raw vs shrunk).
    val_raw = raw_prior(val_keys, groups, global_median)
    sel_rows = [{"k": "raw", "val_MdAPE": triplet(val_price, val_raw, val_alog)["MdAPE"]}]
    best_k, best_md = None, np.inf
    for k in K_GRID:
        pred = shrunk_prior(val_keys, groups, global_median, float(k))
        md = triplet(val_price, pred, val_alog)["MdAPE"]
        sel_rows.append({"k": k, "val_MdAPE": md})
        if md < best_md:
            best_md, best_k = md, k
    sel_df = pd.DataFrame(sel_rows)

    # apply raw + shrunk(best_k) to all regions.
    regions = {"validation": (val_keys, val_price, val_alog),
               "test_warm": (test_keys, test_price, test_alog),
               "0604": (ops_keys, ops_price, ops_alog)}
    rows: list[dict[str, Any]] = []
    for region, (keys, price, alog) in regions.items():
        raw = raw_prior(keys, groups, global_median)
        shr = shrunk_prior(keys, groups, global_median, float(best_k))
        for name, pred in [("raw_prior", raw), (f"shrunk_prior_k{best_k}", shr)]:
            rows.append({"region": region, "candidate": name, "n": len(keys), **triplet(price, pred, alog)})
    metrics = pd.DataFrame(rows)

    # level coverage on 0604 (which level each row resolves to under raw).
    cov_rows: list[dict[str, Any]] = []
    for region, (keys, _, _) in regions.items():
        kb = {lv: level_key(keys, lv).to_numpy() for lv in LEVELS}
        resolved = []
        for i in range(len(keys)):
            lvl = "global"
            for level in LEVELS:
                g = groups[level].get(kb[level][i])
                if g is not None and g[1] >= RAW_MIN_N:
                    lvl = level
            resolved.append(lvl)
        vc = pd.Series(resolved).value_counts(normalize=True)
        cov_rows.append({"region": region, **{lv: round(float(vc.get(lv, 0.0)) * 100, 1) for lv in ["global", *LEVELS]}})
    cov_df = pd.DataFrame(cov_rows)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "region_prior_metrics.csv", index=False)
    sel_df.to_csv(out / "k_validation_selection.csv", index=False)
    cov_df.to_csv(out / "level_coverage.csv", index=False)

    def get(region: str, cand: str, col: str) -> float:
        r = metrics[(metrics["region"] == region) & (metrics["candidate"] == cand)]
        return float(r[col].iloc[0])

    shr_name = f"shrunk_prior_k{best_k}"
    ops_raw_std, ops_shr_std = get("0604", "raw_prior", "resid_std"), get("0604", shr_name, "resid_std")
    ops_raw_mape, ops_shr_mape = get("0604", "raw_prior", "MAPE"), get("0604", shr_name, "MAPE")
    ops_raw_p95, ops_shr_p95 = get("0604", "raw_prior", "p95_APE"), get("0604", shr_name, "p95_APE")
    ops_raw_md, ops_shr_md = get("0604", "raw_prior", "MdAPE"), get("0604", shr_name, "MdAPE")
    test_raw_md, test_shr_md = get("test_warm", "raw_prior", "MdAPE"), get("test_warm", shr_name, "MdAPE")

    helps_0604 = (ops_shr_std < ops_raw_std) and (ops_shr_mape <= ops_raw_mape) and (ops_shr_p95 <= ops_raw_p95) and (ops_shr_md <= ops_raw_md + 0.005)
    test_ok = test_shr_md <= test_raw_md + 0.005
    if helps_0604 and test_ok:
        decision = (f"채택: shrinkage(k={best_k})가 0604 staleness 완화 — residual std {ops_raw_std:.3f}→{ops_shr_std:.3f}, "
                    f"MAPE {ops_raw_mape:.3f}→{ops_shr_mape:.3f}, p95 {ops_raw_p95:.3f}→{ops_shr_p95:.3f}, MdAPE {ops_raw_md:.3f}→{ops_shr_md:.3f} (test 비악화). "
                    "svc 비교군 feature를 shrunk median으로 교체해 Warm Huber 재학습+반복검증 후속 권고.")
    elif ops_shr_std < ops_raw_std:
        decision = (f"부분: shrinkage가 0604 분산은 줄였으나({ops_raw_std:.3f}→{ops_shr_std:.3f}) 일부 지표 미개선. "
                    "분산 외 요인(매칭이동) 잔존 — 커버리지 확대 병행 필요.")
    else:
        decision = (f"중단: shrinkage가 0604를 개선하지 못함(std {ops_raw_std:.3f}→{ops_shr_std:.3f}). prior staleness는 shrinkage로 해소 불가.")

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- source pool: warm train {len(train_df)}, 계층 {LEVELS} (nested), size_bin {N_SIZE_BINS}분위",
        f"- k 선택(validation MdAPE): k={best_k}",
        "- 거래 시점 데이터 부재로 recency 갱신 불가 → EB 계층 shrinkage로 분산 완화 검증. raw 비교군 prior 컴포넌트 수준.",
        "",
        "## 1. 실행 결론",
        "",
        f"- {decision}",
        "",
        "## 2. raw vs shrunk prior (영역별)",
        "",
        markdown_table(metrics[["region", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "resid_std"]].round(4)),
        "",
        "## 3. k validation 선택",
        "",
        markdown_table(sel_df.round(4)),
        "",
        "## 4. 비교군 레벨 해소 분포 (raw, %)",
        "",
        markdown_table(cov_df),
        "",
        "## 5. 산출물",
        "",
        "- `outputs/region_prior_metrics.csv`, `outputs/k_validation_selection.csv`, `outputs/level_coverage.csv`, `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_svcshrink1_warm_comparable_prior_shrinkage_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_svcshrink1_warm_comparable_prior_shrinkage_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {"experiment_id": EXP_ID, "experiment_slug": EXP_SLUG, "levels": LEVELS,
              "n_size_bins": N_SIZE_BINS, "raw_min_n": RAW_MIN_N, "k_grid": K_GRID, "best_k": best_k,
              "size_edges": [float(x) for x in size_edges], "decision": decision}
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] best_k={best_k}")
    print(metrics[["region", "candidate", "MdAPE", "MAPE", "p95_APE", "resid_std"]].round(4).to_string(index=False))
    print("--- level coverage (raw) ---")
    print(cov_df.to_string(index=False))
    print(f"[{EXP_ID}] decision: {decision}")


if __name__ == "__main__":
    main()
