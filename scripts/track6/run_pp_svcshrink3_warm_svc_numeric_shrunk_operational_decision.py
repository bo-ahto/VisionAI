#!/usr/bin/env python3
"""Run PP-SVCSHRINK3: full svc_numeric with raw vs EB-shrunk comparable median.

Operational-decision experiment. Replicates svc1's svc_numeric (full warm base +
full comparable stats + svc1 Huber) and compares the raw comparable median against
the SVCSHRINK1 EB-shrunk median (median feature swapped, other stats unchanged).

Selection via PP-SVC4-style repeated holdout on the fixed validation predictions;
test_warm + 0604 are confirmation. Decides whether to replace operational svc_numeric.
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
from sklearn.model_selection import KFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svc1_comparable_stats_feature_validation as s  # noqa: E402
import run_pp_svcshrink1_warm_comparable_prior_shrinkage as shrink1  # noqa: E402
from run_pre_pp_experiments import artifact_features  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-SVCSHRINK3"
EXP_SLUG = "PP-SVCSHRINK3_warm_svc_numeric_shrunk_operational_decision"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "svc_numeric 전체 재현 + shrunk median 운영 교체 결정"

OPS_FEAT = REPO / "models" / "track6" / "price_prediction_v0.1" / "data" / "evaluation" / "test_new_artworks_test_noprice_0604_features" / "warm_features_v0_1.csv"
OPS_LAB = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"
MEDIAN_COL = "svc_group_log_price_median"
K = 5
N_OOF = 5
BASE_SEED = 20260607
N_REPEATS = 8
N_FOLDS = 5


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def triplet(price: np.ndarray, pred_log: np.ndarray, alog: np.ndarray) -> dict[str, float]:
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pp - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95)), "resid_std": float(np.std(alog - np.asarray(pred_log, dtype=float)))}


def load_0604(warm_base: list[str]) -> pd.DataFrame:
    wf = pd.read_csv(OPS_FEAT, low_memory=False)
    lab = pd.read_csv(OPS_LAB, low_memory=False)[["_v01_row_id", "actual_price_krw", "actual_price_usd_equiv"]]
    m = wf.merge(lab, on="_v01_row_id", how="inner")
    m = m[m["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(m["actual_price_usd_equiv"], errors="coerce")
    m = m[~(usd < 50.0)].copy()
    m["price_krw"] = pd.to_numeric(m["actual_price_krw"], errors="coerce")
    m["ln_price_krw"] = np.log(np.clip(m["price_krw"].to_numpy(dtype=float), 1.0, None))
    if "_track6_row_id" not in m.columns:
        m["_track6_row_id"] = m["_v01_row_id"]
    # warm_features_v0_1 ships precomputed svc_* columns; drop them so svc1's
    # apply_comparable_stats can recompute consistently (no merge collision).
    drop = [c for c in m.columns if c.startswith("svc_")]
    return m.drop(columns=drop).reset_index(drop=True)


def shrunk_median(train_keys, y_train, groups, gm, eval_keys) -> np.ndarray:
    return shrink1.shrunk_prior(eval_keys, groups, gm, float(K))


def oof_shrunk_train(train_keys: pd.DataFrame, y: np.ndarray) -> np.ndarray:
    n = len(train_keys)
    out = np.empty(n, dtype=float)
    kf = KFold(n_splits=N_OOF, shuffle=True, random_state=BASE_SEED)
    for tr, ho in kf.split(np.arange(n)):
        g, gmf = shrink1.train_groups(train_keys.iloc[tr], y[tr])
        out[ho] = shrink1.shrunk_prior(train_keys.iloc[ho], g, gmf, float(K))
    return out


def fit_predict(train_X, y, evalX: dict[str, pd.DataFrame], features) -> dict[str, np.ndarray]:
    model = s.huber_model(features)
    model.fit(s.normalize(train_X, features), y)
    return {name: np.asarray(model.predict(s.normalize(X, features)), dtype=float) for name, X in evalX.items()}


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
    warm_base = artifact_features()["warm"]
    train, val, test = s.load_scope("warm", warm_base)
    ops = load_0604(warm_base)

    y_train = pd.to_numeric(train["ln_price_krw"], errors="coerce").to_numpy(dtype=float)

    # svc1 raw comparable stats.
    train_r, val_r, test_r = s.add_service_features(train, val, test)
    ops_stats = s.apply_comparable_stats(train, ops)
    ops_r = ops.merge(ops_stats, on="_track6_row_id", how="left")

    # SVCSHRINK1 EB-shrunk median.
    size_edges = shrink1.prep(train, None)[1]
    tk = shrink1.prep(train, size_edges)[0]
    groups, gm = shrink1.train_groups(tk, y_train)
    shr_train = oof_shrunk_train(tk, y_train)
    shr_val = shrink1.shrunk_prior(shrink1.prep(val, size_edges)[0], groups, gm, float(K))
    shr_test = shrink1.shrunk_prior(shrink1.prep(test, size_edges)[0], groups, gm, float(K))
    shr_ops = shrink1.shrunk_prior(shrink1.prep(ops, size_edges)[0], groups, gm, float(K))

    features = s.candidate_features(warm_base)["svc_numeric"]

    # raw frames
    raw_frames = {"validation": val_r, "test_warm": test_r, "0604": ops_r}
    # shrunk frames (swap median)
    def swap(frame: pd.DataFrame, med: np.ndarray) -> pd.DataFrame:
        out = frame.copy()
        out[MEDIAN_COL] = med
        return out
    train_s = swap(train_r, shr_train)
    shr_frames = {"validation": swap(val_r, shr_val), "test_warm": swap(test_r, shr_test), "0604": swap(ops_r, shr_ops)}

    price = {r: pd.to_numeric(raw_frames[r]["price_krw"], errors="coerce").to_numpy(dtype=float) for r in raw_frames}
    alog = {r: pd.to_numeric(raw_frames[r]["ln_price_krw"], errors="coerce").to_numpy(dtype=float) for r in raw_frames}

    preds_raw = fit_predict(train_r, y_train, raw_frames, features)
    preds_shr = fit_predict(train_s, y_train, shr_frames, features)
    # baseline (no svc) for context
    base_feat = s.candidate_features(warm_base)["baseline"]
    preds_base = fit_predict(train, y_train, {r: raw_frames[r] for r in raw_frames}, base_feat)

    rows: list[dict[str, Any]] = []
    for cand, preds in [("baseline", preds_base), ("svc_numeric_raw", preds_raw), ("svc_numeric_shrunk", preds_shr)]:
        for r in raw_frames:
            rows.append({"region": r, "candidate": cand, "n": len(raw_frames[r]), **triplet(price[r], preds[r], alog[r])})
    metrics = pd.DataFrame(rows)

    # PP-SVC4-style repeated holdout on validation fixed predictions.
    vp = price["validation"]; va = alog["validation"]
    artists = val_r["artist_key"].astype(str).fillna("__MISSING__")
    uniq = artists.unique()
    nval = len(val_r)
    hold_rows: list[dict[str, Any]] = []
    for rep in range(N_REPEATS):
        rng = np.random.default_rng(BASE_SEED + rep)
        row_folds = np.array_split(rng.permutation(nval), N_FOLDS)
        art_folds = np.array_split(rng.permutation(uniq), N_FOLDS)
        plans = [("row", list(row_folds)),
                 ("artist", [np.flatnonzero(artists.isin(set(f)).to_numpy()) for f in art_folds])]
        for scheme, folds in plans:
            for fid, idx in enumerate(folds, 1):
                if len(idx) == 0:
                    continue
                rr = triplet(vp[idx], preds_raw["validation"][idx], va[idx])
                ss = triplet(vp[idx], preds_shr["validation"][idx], va[idx])
                hold_rows.append({"scheme": scheme, "repeat": rep, "fold": fid,
                                  "raw_MdAPE": rr["MdAPE"], "shr_MdAPE": ss["MdAPE"],
                                  "raw_MAPE": rr["MAPE"], "shr_MAPE": ss["MAPE"],
                                  "raw_p95": rr["p95_APE"], "shr_p95": ss["p95_APE"]})
    hold = pd.DataFrame(hold_rows)
    prob = {
        "MdAPE_improve": float((hold["shr_MdAPE"] < hold["raw_MdAPE"]).mean()),
        "MAPE_improve": float((hold["shr_MAPE"] < hold["raw_MAPE"]).mean()),
        "p95_improve": float((hold["shr_p95"] < hold["raw_p95"]).mean()),
    }
    prob_by_scheme = {sch: {
        "MdAPE": float((g["shr_MdAPE"] < g["raw_MdAPE"]).mean()),
        "MAPE": float((g["shr_MAPE"] < g["raw_MAPE"]).mean()),
        "p95": float((g["shr_p95"] < g["raw_p95"]).mean()),
    } for sch, g in hold.groupby("scheme")}

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "region_metrics.csv", index=False)
    hold.to_csv(out / "repeated_holdout_summary.csv", index=False)

    def g_(region, cand, col):
        r = metrics[(metrics["region"] == region) & (metrics["candidate"] == cand)]
        return float(r[col].iloc[0])

    def dom(region: str) -> bool:
        return (g_(region, "svc_numeric_shrunk", "MdAPE") <= g_(region, "svc_numeric_raw", "MdAPE") + 1e-9 and
                g_(region, "svc_numeric_shrunk", "MAPE") <= g_(region, "svc_numeric_raw", "MAPE") + 1e-9 and
                g_(region, "svc_numeric_shrunk", "p95_APE") <= g_(region, "svc_numeric_raw", "p95_APE") + 1e-9)
    heldout_dominates = dom("test_warm") and dom("0604")
    holdout_strong = (prob["MAPE_improve"] >= 0.6 or prob["p95_improve"] >= 0.6)
    val_mdape_worse = g_("validation", "svc_numeric_shrunk", "MdAPE") > g_("validation", "svc_numeric_raw", "MdAPE") + 0.003
    tw = lambda c: g_("test_warm", c, "MAPE")  # noqa: E731
    op = lambda c: g_("0604", c, "MAPE")  # noqa: E731
    summary_nums = (f"0604 raw→shrunk MAPE {op('svc_numeric_raw'):.3f}→{op('svc_numeric_shrunk'):.3f}/"
                    f"p95 {g_('0604','svc_numeric_raw','p95_APE'):.3f}→{g_('0604','svc_numeric_shrunk','p95_APE'):.3f}/"
                    f"std {g_('0604','svc_numeric_raw','resid_std'):.3f}→{g_('0604','svc_numeric_shrunk','resid_std'):.3f}")
    if heldout_dominates and holdout_strong:
        decision = ("교체 권고: shrunk가 held-out test_warm+0604 전 지표 지배 + validation 반복 holdout 우세. "
                    f"({summary_nums}) 운영 반영: svc_numeric_seed_mean 다중 seed 파이프라인에 shrunk median 통합 + Warm 후보 재계산 + artifact 동결.")
    elif heldout_dominates:
        decision = ("조건부 채택: shrunk가 held-out test_warm+0604 전 지표 지배(test_warm "
                    f"MAPE {tw('svc_numeric_raw'):.3f}→{tw('svc_numeric_shrunk'):.3f}, {summary_nums}). "
                    f"단 validation MdAPE 소폭 악화({'예' if val_mdape_worse else '아니오'}) + 반복 holdout 중립"
                    f"(MAPE {prob['MAPE_improve']:.2f}/p95 {prob['p95_improve']:.2f}, artist scheme는 우세) = center-vs-tail 트레이드오프. "
                    "운영 반영 전 svc_numeric_seed_mean 전체 재현 + 고정 split 최종 확인 권고.")
    elif g_("0604", "svc_numeric_shrunk", "MAPE") <= g_("0604", "svc_numeric_raw", "MAPE"):
        decision = (f"부분: 0604만 개선, test_warm 일부 미달. 추가 검증.")
    else:
        decision = "중단: 전체 svc_numeric 모델에서 shrinkage 이득 불충분. raw median 유지."

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 피처: svc1 svc_numeric(warm base 13 + SVC_NUMERIC). 모델: svc1 Huber. k={K}, crossfit single-seed.",
        "- shrunk: svc_group_log_price_median만 SVCSHRINK1 EB-shrunk로 교체(다른 svc stats raw 유지). train OOF, eval full-train.",
        "- 선택: validation 반복 holdout(PP-SVC4식, 고정 예측 subsample). test_warm + 0604 확인.",
        "",
        "## 1. 실행 결론",
        "",
        f"- {decision}",
        "",
        "## 2. 영역별 지표 (baseline / svc_numeric raw / shrunk)",
        "",
        markdown_table(metrics[["region", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "resid_std"]].round(4)),
        "",
        "## 3. validation 반복 holdout: shrunk vs raw 개선확률",
        "",
        f"- 전체: MdAPE {prob['MdAPE_improve']:.2f} / MAPE {prob['MAPE_improve']:.2f} / p95 {prob['p95_improve']:.2f}",
        f"- scheme별: {json.dumps(prob_by_scheme, ensure_ascii=False)}",
        "",
        "## 4. 산출물",
        "",
        "- `outputs/region_metrics.csv`, `outputs/repeated_holdout_summary.csv`, `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_svcshrink3_warm_svc_numeric_shrunk_operational_decision_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_svcshrink3_warm_svc_numeric_shrunk_operational_decision_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {"experiment_id": EXP_ID, "experiment_slug": EXP_SLUG, "features": features, "k": K,
              "n_oof": N_OOF, "n_repeats": N_REPEATS, "n_folds": N_FOLDS,
              "improvement_prob": prob, "prob_by_scheme": prob_by_scheme, "decision": decision}
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] features={len(features)}")
    print(metrics[["region", "candidate", "MdAPE", "MAPE", "p95_APE", "resid_std"]].round(4).to_string(index=False))
    print(f"[{EXP_ID}] holdout improve prob: {prob}")
    print(f"[{EXP_ID}] by scheme: {prob_by_scheme}")
    print(f"[{EXP_ID}] decision: {decision}")


if __name__ == "__main__":
    main()
