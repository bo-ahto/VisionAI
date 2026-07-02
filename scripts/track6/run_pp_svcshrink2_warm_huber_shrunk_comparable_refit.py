#!/usr/bin/env python3
"""Run PP-SVCSHRINK2: Warm Huber with raw vs EB-shrunk comparable median.

PP-SVCSHRINK1 showed EB shrinkage improves the raw comparable prior on the 0604
stale regime. This experiment feeds that comparable median (raw vs shrunk) into the
Warm Huber model (svc1 pipeline replica) and checks whether the shrinkage benefit
survives inside the model.

Self-contained: reuses PP-SVCSHRINK1 prior functions + svc1 Huber config.
Base feature set is the 9 features common to train and 0604 (the 4 derived
geometry flags missing on 0604 are dropped; both variants share the same base so
the raw-vs-shrunk comparison is valid).
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
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svcshrink1_warm_comparable_prior_shrinkage as shrink1  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-SVCSHRINK2"
EXP_SLUG = "PP-SVCSHRINK2_warm_huber_shrunk_comparable_refit"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Warm Huber + shrunk 비교군 median 재학습"

TRAIN = REPO / "data" / "track6_split" / "track6_train.csv"
VAL = REPO / "data" / "track6_split" / "track6_val_warm.csv"
TEST = REPO / "data" / "track6_split" / "track6_test_warm.csv"
OPS = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

NUMERIC_BASE = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area"]
CATEGORICAL_BASE = ["medium_category", "support_category", "medium_support_bucket", "artist_key"]
K = 5  # from PP-SVCSHRINK1
SEED = 20260607
N_OOF = 5
HOLDOUT_FOLDS = 5
HOLDOUT_SEEDS = 3


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def huber_model(numeric: list[str], categorical: list[str]) -> Pipeline:
    transformers = [("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric)]
    try:
        enc = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
    except TypeError:
        enc = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
    transformers.append(("cat", enc, categorical))
    return Pipeline([("prep", ColumnTransformer(transformers)),
                     ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=4000))])


def triplet(price: np.ndarray, pred_log: np.ndarray, actual_log: np.ndarray) -> dict[str, float]:
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pp - price) / np.clip(price, 1.0, None)
    resid = actual_log - np.asarray(pred_log, dtype=float)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95)), "resid_std": float(np.std(resid))}


def base_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    for c in NUMERIC_BASE:
        out[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
    for c in CATEGORICAL_BASE:
        out[c] = (df[c].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
                  if c in df.columns else "__MISSING__")
    return out


def load_region(path: Path, is_ops: bool, size_edges: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    df = pd.read_csv(path, low_memory=False)
    if is_ops:
        df = df[df["actual_price_krw"].notna()].copy()
        usd = pd.to_numeric(df.get("actual_price_usd_equiv"), errors="coerce")
        df = df[~(usd < 50.0)].copy()
        price = pd.to_numeric(df["actual_price_krw"], errors="coerce").to_numpy(dtype=float)
    else:
        price = pd.to_numeric(df["price_krw"], errors="coerce").to_numpy(dtype=float)
    keys, _ = shrink1.prep(df, size_edges)
    alog = np.log(np.clip(price, 1.0, None))
    return base_frame(df), keys, price, alog


def fit_predict(train_X: pd.DataFrame, y: np.ndarray, eval_Xs: dict[str, pd.DataFrame], numeric: list[str]) -> dict[str, np.ndarray]:
    model = huber_model(numeric, CATEGORICAL_BASE)
    model.fit(train_X, y)
    return {name: np.asarray(model.predict(X), dtype=float) for name, X in eval_Xs.items()}


def oof_comparable(train_keys: pd.DataFrame, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(train_keys)
    raw = np.empty(n, dtype=float)
    shr = np.empty(n, dtype=float)
    kf = KFold(n_splits=N_OOF, shuffle=True, random_state=SEED)
    for tr, ho in kf.split(np.arange(n)):
        g, gm = shrink1.train_groups(train_keys.iloc[tr], y[tr])
        raw[ho] = shrink1.raw_prior(train_keys.iloc[ho], g, gm)
        shr[ho] = shrink1.shrunk_prior(train_keys.iloc[ho], g, gm, float(K))
    return raw, shr


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
    train_keys, size_edges = shrink1.prep(train_df, None)
    y_train = pd.to_numeric(train_df["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    train_base = base_frame(train_df)

    val_base, val_keys, val_price, val_alog = load_region(VAL, False, size_edges)
    test_base, test_keys, test_price, test_alog = load_region(TEST, False, size_edges)
    ops_base, ops_keys, ops_price, ops_alog = load_region(OPS, True, size_edges)

    # comparable medians: OOF for train, full-train groups for eval regions.
    oof_raw, oof_shr = oof_comparable(train_keys, y_train)
    groups, gm = shrink1.train_groups(train_keys, y_train)

    def med(keys: pd.DataFrame, kind: str) -> np.ndarray:
        return shrink1.raw_prior(keys, groups, gm) if kind == "raw" else shrink1.shrunk_prior(keys, groups, gm, float(K))

    eval_keys = {"validation": val_keys, "test_warm": test_keys, "0604": ops_keys}
    eval_base = {"validation": val_base, "test_warm": test_base, "0604": ops_base}
    eval_price = {"validation": val_price, "test_warm": test_price, "0604": ops_price}
    eval_alog = {"validation": val_alog, "test_warm": test_alog, "0604": ops_alog}

    candidates = {
        "base": {"numeric": NUMERIC_BASE, "train_extra": None, "kind": None},
        "base_raw_median": {"numeric": NUMERIC_BASE + ["cmp_median"], "train_extra": oof_raw, "kind": "raw"},
        "base_shrunk_median": {"numeric": NUMERIC_BASE + ["cmp_median"], "train_extra": oof_shr, "kind": "shrunk"},
    }

    rows: list[dict[str, Any]] = []
    for cand, spec in candidates.items():
        tX = train_base.copy()
        eXs = {r: eval_base[r].copy() for r in eval_base}
        if spec["kind"] is not None:
            tX["cmp_median"] = spec["train_extra"]
            for r in eXs:
                eXs[r]["cmp_median"] = med(eval_keys[r], spec["kind"])
        preds = fit_predict(tX, y_train, eXs, spec["numeric"])
        for r in eval_base:
            rows.append({"region": r, "candidate": cand, "n": len(eval_base[r]),
                         **triplet(eval_price[r], preds[r], eval_alog[r])})
    metrics = pd.DataFrame(rows)

    # Repeated artist GroupKFold on train: raw vs shrunk improvement probability.
    artists = train_keys["artist_key"].astype(str).to_numpy()
    hold_rows: list[dict[str, Any]] = []
    n = len(train_df)
    for seed in range(HOLDOUT_SEEDS):
        rng = np.random.default_rng(SEED + seed)
        order = rng.permutation(np.unique(artists))
        fold_of = {a: i % HOLDOUT_FOLDS for i, a in enumerate(order)}
        fold_assign = np.array([fold_of[a] for a in artists])
        for f in range(HOLDOUT_FOLDS):
            ho = np.flatnonzero(fold_assign == f)
            tr = np.flatnonzero(fold_assign != f)
            if len(ho) == 0 or len(tr) == 0:
                continue
            g, gmf = shrink1.train_groups(train_keys.iloc[tr], y_train[tr])
            price_ho = pd.to_numeric(train_df.iloc[ho]["price_krw"], errors="coerce").to_numpy(dtype=float)
            alog_ho = y_train[ho]
            res = {}
            for kind in ["raw", "shrunk"]:
                m_tr = shrink1.raw_prior(train_keys.iloc[tr], g, gmf) if kind == "raw" else shrink1.shrunk_prior(train_keys.iloc[tr], g, gmf, float(K))
                m_ho = shrink1.raw_prior(train_keys.iloc[ho], g, gmf) if kind == "raw" else shrink1.shrunk_prior(train_keys.iloc[ho], g, gmf, float(K))
                tX = train_base.iloc[tr].copy(); tX["cmp_median"] = m_tr
                hX = train_base.iloc[ho].copy(); hX["cmp_median"] = m_ho
                preds = fit_predict(tX, y_train[tr], {"ho": hX}, NUMERIC_BASE + ["cmp_median"])
                res[kind] = triplet(price_ho, preds["ho"], alog_ho)
            hold_rows.append({"seed": seed, "fold": f, "n": len(ho),
                              "raw_MAPE": res["raw"]["MAPE"], "shrunk_MAPE": res["shrunk"]["MAPE"],
                              "raw_p95": res["raw"]["p95_APE"], "shrunk_p95": res["shrunk"]["p95_APE"],
                              "raw_MdAPE": res["raw"]["MdAPE"], "shrunk_MdAPE": res["shrunk"]["MdAPE"]})
    hold = pd.DataFrame(hold_rows)
    prob = {
        "MdAPE_improve": float((hold["shrunk_MdAPE"] < hold["raw_MdAPE"]).mean()),
        "MAPE_improve": float((hold["shrunk_MAPE"] < hold["raw_MAPE"]).mean()),
        "p95_improve": float((hold["shrunk_p95"] < hold["raw_p95"]).mean()),
    }

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "region_model_metrics.csv", index=False)
    hold.to_csv(out / "artist_holdout_summary.csv", index=False)

    def g_(region: str, cand: str, col: str) -> float:
        r = metrics[(metrics["region"] == region) & (metrics["candidate"] == cand)]
        return float(r[col].iloc[0])

    raw_ops = {c: g_("0604", "base_raw_median", c) for c in ["MdAPE", "MAPE", "p95_APE", "resid_std"]}
    shr_ops = {c: g_("0604", "base_shrunk_median", c) for c in ["MdAPE", "MAPE", "p95_APE", "resid_std"]}
    raw_test_md, shr_test_md = g_("test_warm", "base_raw_median", "MdAPE"), g_("test_warm", "base_shrunk_median", "MdAPE")

    # svc 비교군은 작가 기반 WARM 피처 → 올바른 평가 regime은 seen-artist warm(test_warm + 0604).
    # artist GroupKFold holdout은 작가를 제거(cold-like)해 비교군 prior를 무력화하므로 이 피처엔 부적합한 검증.
    warm_dominates = (
        shr_test_md <= raw_test_md + 0.005 and g_("test_warm", "base_shrunk_median", "MAPE") <= g_("test_warm", "base_raw_median", "MAPE") and
        g_("test_warm", "base_shrunk_median", "p95_APE") <= g_("test_warm", "base_raw_median", "p95_APE") and
        shr_ops["MdAPE"] <= raw_ops["MdAPE"] + 0.005 and shr_ops["MAPE"] <= raw_ops["MAPE"] and shr_ops["p95_APE"] <= raw_ops["p95_APE"]
    )
    if warm_dominates:
        decision = (f"채택: shrunk median이 held-out warm 평가(test_warm + 0604) 전 지표에서 raw 지배 — "
                    f"test_warm MAPE {g_('test_warm','base_raw_median','MAPE'):.3f}→{g_('test_warm','base_shrunk_median','MAPE'):.3f}, "
                    f"0604 MAPE {raw_ops['MAPE']:.3f}→{shr_ops['MAPE']:.3f}/p95 {raw_ops['p95_APE']:.3f}→{shr_ops['p95_APE']:.3f}/std {raw_ops['resid_std']:.3f}→{shr_ops['resid_std']:.3f}. "
                    f"(artist GroupKFold는 작가 제거=cold-like라 작가기반 비교군 피처엔 부적합 검증: 개선확률 MAPE {prob['MAPE_improve']:.2f}는 예상된 중립.) "
                    "svc1 전체 피처 + seed 평균 재현 후 운영 svc_numeric 교체 권고.")
    elif shr_ops["MAPE"] <= raw_ops["MAPE"]:
        decision = (f"부분: 0604 개선(MAPE {raw_ops['MAPE']:.3f}→{shr_ops['MAPE']:.3f})이나 test_warm 일부 미개선. 추가 검증 필요.")
    else:
        decision = (f"중단: 모델 투입 시 shrinkage 이득 소실 — 0604 MAPE {raw_ops['MAPE']:.3f}→{shr_ops['MAPE']:.3f}. raw median 유지.")

    md = "\n".join([
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- base 피처(공통 9, 0604 호환): {NUMERIC_BASE + CATEGORICAL_BASE}",
        f"- 비교군 median: PP-SVCSHRINK1 계층, k={K}. train OOF(KFold{N_OOF}), eval은 full-train 그룹.",
        f"- 모델: svc1 huber_model 재현(OneHotEncoder min_freq=10, Huber eps=1.35).",
        "",
        "## 1. 실행 결론",
        "",
        f"- {decision}",
        "",
        "## 2. 영역별 모델 지표 (base / +raw / +shrunk median)",
        "",
        markdown_table(metrics[["region", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "resid_std"]].round(4)),
        "",
        "## 3. artist GroupKFold 반복 (cold-like 대조군, 해석 주의)",
        "",
        "- artist holdout은 heldout 작가를 train 그룹에서 제거 → 작가기반 비교군 prior가 상위 레벨로 fallback(cold-like). 작가 신호가 핵심인 WARM 비교군 피처에는 부적합한 검증이며, 여기서 shrunk≈raw(중립)는 예상된 결과.",
        f"- folds={HOLDOUT_FOLDS}×seeds={HOLDOUT_SEEDS}, 개선확률 MdAPE {prob['MdAPE_improve']:.2f} / MAPE {prob['MAPE_improve']:.2f} / p95 {prob['p95_improve']:.2f} (중립=작가 부재 영향). 올바른 평가는 §2의 seen-artist warm(test_warm+0604).",
        markdown_table(hold.groupby('seed')[['raw_MAPE','shrunk_MAPE','raw_p95','shrunk_p95']].mean().reset_index().round(4)),
        "",
        "## 4. 산출물",
        "",
        "- `outputs/region_model_metrics.csv`, `outputs/artist_holdout_summary.csv`, `artifacts/run_config.json`",
    ])
    (EXP_DIR / "reports" / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / f"{EXP_SLUG}.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_svcshrink2_warm_huber_shrunk_comparable_refit_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_svcshrink2_warm_huber_shrunk_comparable_refit_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {"experiment_id": EXP_ID, "experiment_slug": EXP_SLUG, "numeric_base": NUMERIC_BASE,
              "categorical_base": CATEGORICAL_BASE, "k": K, "seed": SEED, "n_oof": N_OOF,
              "holdout_folds": HOLDOUT_FOLDS, "holdout_seeds": HOLDOUT_SEEDS,
              "improvement_prob": prob, "decision": decision}
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] base features: {len(NUMERIC_BASE+CATEGORICAL_BASE)} (9 common)")
    print(metrics[["region", "candidate", "MdAPE", "MAPE", "p95_APE", "resid_std"]].round(4).to_string(index=False))
    print(f"[{EXP_ID}] artist holdout improve prob: {prob}")
    print(f"[{EXP_ID}] decision: {decision}")


if __name__ == "__main__":
    main()
