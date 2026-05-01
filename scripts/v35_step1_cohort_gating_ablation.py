"""v3.5 step 1: cohort gating ablation (코덱스 권장).

배경 (v3.4-2 step 5 결과):
- V_year_only Δ-0.74%p overall (CI 0 미포함, p=0.018)
- 단 cold cohort 에서 +0.99%p worse (year_made 가 sparse cohort 에 spurious)
- 코덱스 권장: V_year_only 채택 + cohort gating (cold 차단)

본 step 의 3 gating variants:
- V_year_saatchi_only: saatchi rows 만 year 신호 (artsy disabled)
- V_year_warm_only: warm rows 만 (cold disabled)
- V_year_saatchi_warm: saatchi & warm intersect (가장 좁음)

평가 (코덱스 v3.5 plan step 1 selection rule):
- Primary: overall Δ ≤ -0.5%p
- Guardrail 1: cold Δ ≤ +0.3%p
- Guardrail 2: saatchi_online 10+ Δ ≤ -0.8%p

Selection rule:
1. saatchi-conditional 1순위 → V_year_saatchi_only 선호
2. 동률 시 cold 더 안전한 variant
3. 셋 다 미충족 → abort

비교 baseline:
- V0 (현재 production)
- V_year_only (v3.4-2 step 5 채택안, gating 없음)

Production routing: warm=xgb_kf, cold=cb_gkf (v3.4-2 와 동일)

Usage:
    # smoke (빠른 wiring 검증)
    PYTHONPATH=src:scripts python3 scripts/v35_step1_cohort_gating_ablation.py --smoke

    # full
    PYTHONPATH=src:scripts python3 scripts/v35_step1_cohort_gating_ablation.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from saatchi_year_made_merger import (
    build_variant,
    load_enrichment_year_map,
    merge_summary,
    variant_added_features,
)
from scipy.stats import wilcoxon
from train_primary_market_v3_filtered import (
    CB_FEATURES,
    _label_encode_xgb,
    _warm_mask,
    load_data,
)
from v3_extract_oof import _load_best_params

from visionai.price_engine._eval_helpers import derive_target_market

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results" / "v3_diagnostics"
OUT_JSON = OUT_DIR / "v35_step1_cohort_gating_ablation.json"

RANDOM_SEED = 42
N_BOOTSTRAP = 10_000

VARIANTS = [
    "V0",
    "V_year_only",
    "V_year_saatchi_only",
    "V_year_warm_only",
    "V_year_saatchi_warm",
]
CAT_FEATURES = [
    "support_type",
    "medium_category",
    "attribution_class",
    "gallery_type",
    "price_currency",
    "source",
]

# 코덱스 selection rule 임계
PRIMARY_THRESHOLD_PCT = -0.5
GUARDRAIL_COLD_PCT = 0.3
GUARDRAIL_SAATCHI_10P_PCT = -0.8


def prepare_features_with_extra(
    df: pd.DataFrame, extra_features: list[str]
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    feature_cols = CB_FEATURES + [c for c in extra_features if c not in CB_FEATURES]
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features: {missing}")
    X = df[feature_cols].copy()
    for col in CAT_FEATURES:
        if col in X.columns:
            X[col] = (
                X[col]
                .astype(str)
                .fillna("unknown")
                .replace({"nan": "unknown", "None": "unknown", "": "unknown"})
            )
    for col in feature_cols:
        if col not in CAT_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)
    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    return X, y, groups


def _cb_pool_dyn(X: pd.DataFrame, y: np.ndarray | None = None):
    from catboost import Pool

    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def gkf_oof_dyn(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, cb_p: dict, xgb_p: dict, n_splits: int
) -> tuple[np.ndarray, np.ndarray]:
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[GKF %d/%d] tr=%d te=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_p,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool_dyn(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool_dyn(X.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        xp = {k: v for k, v in xgb_p.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xp, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y[tr]),
            num_boost_round=xgb_p.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y[te]))
    return cb_preds, xgb_preds


def kf_oof_warm_dyn(
    X_warm: pd.DataFrame, y_warm: np.ndarray, cb_p: dict, xgb_p: dict, n_splits: int
) -> tuple[np.ndarray, np.ndarray]:
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    cb_preds = np.zeros(len(y_warm))
    xgb_preds = np.zeros(len(y_warm))
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[KF warm %d/%d] tr=%d te=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_p,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool_dyn(X_warm.iloc[tr], y_warm[tr]))
        cb_preds[te] = cb.predict(_cb_pool_dyn(X_warm.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        xp = {k: v for k, v in xgb_p.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xp, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y_warm[tr]),
            num_boost_round=xgb_p.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y_warm[te]))
    return cb_preds, xgb_preds


def production_routed_pred(
    cb_gkf_ln: np.ndarray, xgb_kf_ln_warm: np.ndarray, wmask: np.ndarray
) -> np.ndarray:
    assert int(wmask.sum()) == len(xgb_kf_ln_warm)
    pred_ln = cb_gkf_ln.copy()
    pred_ln[wmask] = xgb_kf_ln_warm
    return np.exp(pred_ln)


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.median(np.abs(y_true - y_pred) / y_true) * 100)


def cohort_mdape(y: np.ndarray, p: np.ndarray, mask: np.ndarray) -> dict:
    n = int(mask.sum())
    if n == 0:
        return {"n": 0, "skipped": True}
    return {"n": n, "mdape_pct": mdape(y[mask], p[mask])}


def evaluate_variant(
    df: pd.DataFrame, pred_price: np.ndarray, y_true_price: np.ndarray, wmask: np.ndarray
) -> dict:
    artists = df["artist_slug"].astype(str).to_numpy()
    art_count_map = pd.Series(artists).value_counts().to_dict()
    art_count = np.array([art_count_map[a] for a in artists])
    cold_mask = ~wmask
    cold_le2 = cold_mask & (art_count <= 2)
    warm_5_9 = wmask & (art_count >= 5) & (art_count <= 9)
    target_market = derive_target_market(df["is_krw"])
    saatchi_online = (df["source"].astype(str) == "saatchi").to_numpy() & (
        target_market == "online"
    )
    saatchi_online_10p = saatchi_online & (art_count >= 10)

    return {
        "primary": {"mdape_pct": mdape(y_true_price, pred_price), "n": len(y_true_price)},
        "guardrail": {
            "cold": cohort_mdape(y_true_price, pred_price, cold_mask),
            "cold_le2": cohort_mdape(y_true_price, pred_price, cold_le2),
            "warm_5_9": cohort_mdape(y_true_price, pred_price, warm_5_9),
            "saatchi_online": cohort_mdape(y_true_price, pred_price, saatchi_online),
            "saatchi_online_10p": cohort_mdape(y_true_price, pred_price, saatchi_online_10p),
        },
    }


def artist_cluster_bootstrap_ci(
    y: np.ndarray, pa: np.ndarray, pb: np.ndarray, artists: np.ndarray, n_boot: int
) -> dict:
    rng = np.random.default_rng(RANDOM_SEED)
    uniq = np.unique(artists)
    idx_map = {a: np.where(artists == a)[0] for a in uniq}
    diffs = np.zeros(n_boot)
    for b in range(n_boot):
        sampled = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_map[a] for a in sampled])
        diffs[b] = mdape(y[idx], pa[idx]) - mdape(y[idx], pb[idx])
    lo = float(np.percentile(diffs, 2.5))
    hi = float(np.percentile(diffs, 97.5))
    return {
        "diff_median_mdape_pct": float(np.median(diffs)),
        "ci_95_low": lo,
        "ci_95_high": hi,
        "ci_excludes_zero": lo * hi > 0,
        "n_bootstrap": n_boot,
    }


def paired_compare(a: dict, b: dict, artists: np.ndarray, label: str, n_boot: int) -> dict:
    y = a["_y"]
    pa = a["_pred"]
    pb = b["_pred"]
    diffs_per_row = np.abs(y - pa) / y * 100 - np.abs(y - pb) / y * 100
    bs = artist_cluster_bootstrap_ci(y, pa, pb, artists, n_boot)
    try:
        _, w_p = wilcoxon(diffs_per_row, zero_method="wilcox", alternative="two-sided")
    except Exception:
        w_p = None
    df_a = pd.DataFrame({"artist": artists, "diff": diffs_per_row})
    artist_diffs = df_a.groupby("artist")["diff"].median().to_numpy()
    try:
        _, wa_p = wilcoxon(artist_diffs, zero_method="wilcox", alternative="two-sided")
    except Exception:
        wa_p = None
    return {
        "label": label,
        "diff_mdape_pct": a["evaluation"]["primary"]["mdape_pct"]
        - b["evaluation"]["primary"]["mdape_pct"],
        "artist_cluster_bootstrap": bs,
        "wilcoxon_row_p": float(w_p) if w_p is not None else None,
        "wilcoxon_artist_p": float(wa_p) if wa_p is not None else None,
    }


def run_variant(
    df: pd.DataFrame,
    emap: dict,
    variant: str,
    cb_p: dict,
    xgb_p: dict,
    n_splits: int,
    wmask: np.ndarray,
) -> dict:
    t0 = time.time()
    if variant in ("V_year_warm_only", "V_year_saatchi_warm"):
        df_v = build_variant(df, emap, variant, warm_mask=wmask)
    else:
        df_v = build_variant(df, emap, variant)
    extras = variant_added_features(variant)
    X, y, groups = prepare_features_with_extra(df_v, extras)
    logger.info("[%s] features=%d (extras=%s)", variant, X.shape[1], extras)

    cb_gkf_ln, _ = gkf_oof_dyn(X, y, groups, cb_p, xgb_p, n_splits)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    _, xgb_kf_ln = kf_oof_warm_dyn(X_warm, y_warm, cb_p, xgb_p, n_splits)
    pred = production_routed_pred(cb_gkf_ln, xgb_kf_ln, wmask)
    y_price = np.exp(y)

    eval_r = evaluate_variant(df_v, pred, y_price, wmask)
    elapsed = time.time() - t0
    gr = eval_r["guardrail"]
    logger.info(
        "[%s] overall=%.3f  cold=%.3f  cold_le2=%.3f  warm_5_9=%.3f  sa_online=%.3f  sa_10p=%.3f  (%.0fs)",
        variant,
        eval_r["primary"]["mdape_pct"],
        gr["cold"]["mdape_pct"],
        gr["cold_le2"]["mdape_pct"],
        gr["warm_5_9"]["mdape_pct"],
        gr["saatchi_online"]["mdape_pct"],
        gr["saatchi_online_10p"]["mdape_pct"],
        elapsed,
    )
    return {
        "variant": variant,
        "extras": extras,
        "n_features": X.shape[1],
        "elapsed_sec": elapsed,
        "evaluation": eval_r,
        "_pred": pred,
        "_y": y_price,
    }


def selection_decision(results: dict, baseline: str = "V0") -> dict:
    """코덱스 selection rule 적용:
    1. saatchi-conditional 1순위
    2. 동률 시 cold guardrail 더 안전
    3. abort 조건: 셋 다 primary or guardrail 미충족
    """
    candidates = ["V_year_saatchi_only", "V_year_warm_only", "V_year_saatchi_warm"]
    base_eval = results[baseline]["evaluation"]
    base_overall = base_eval["primary"]["mdape_pct"]
    base_cold = base_eval["guardrail"]["cold"]["mdape_pct"]
    base_sa10 = base_eval["guardrail"]["saatchi_online_10p"]["mdape_pct"]

    decisions = []
    for v in candidates:
        ev = results[v]["evaluation"]
        d_overall = ev["primary"]["mdape_pct"] - base_overall
        d_cold = ev["guardrail"]["cold"]["mdape_pct"] - base_cold
        d_sa10 = ev["guardrail"]["saatchi_online_10p"]["mdape_pct"] - base_sa10
        passes_primary = d_overall <= PRIMARY_THRESHOLD_PCT
        passes_guard_cold = d_cold <= GUARDRAIL_COLD_PCT
        passes_guard_sa10 = d_sa10 <= GUARDRAIL_SAATCHI_10P_PCT
        all_pass = passes_primary and passes_guard_cold and passes_guard_sa10
        decisions.append(
            {
                "variant": v,
                "delta_overall_mdape_pct": d_overall,
                "delta_cold_mdape_pct": d_cold,
                "delta_saatchi_online_10p_mdape_pct": d_sa10,
                "passes_primary": passes_primary,
                "passes_guardrail_cold": passes_guard_cold,
                "passes_guardrail_saatchi_10p": passes_guard_sa10,
                "all_pass": all_pass,
            }
        )

    passing = [d for d in decisions if d["all_pass"]]
    chosen = None
    rationale = ""
    if not passing:
        chosen = None
        rationale = "abort: 어떤 gating variant 도 primary + guardrail 모두 충족 못함"
    elif len(passing) == 1:
        chosen = passing[0]["variant"]
        rationale = f"unique pass: {chosen}"
    else:
        # selection rule: saatchi-conditional 1순위
        priority = {"V_year_saatchi_only": 0, "V_year_warm_only": 1, "V_year_saatchi_warm": 2}
        passing_sorted = sorted(
            passing, key=lambda d: (priority[d["variant"]], d["delta_cold_mdape_pct"])
        )
        chosen = passing_sorted[0]["variant"]
        rationale = (
            f"multi-pass tiebreak (saatchi-conditional 1순위, cold guardrail 안전): {chosen}"
        )
    return {
        "thresholds": {
            "primary_pct": PRIMARY_THRESHOLD_PCT,
            "guardrail_cold_pct": GUARDRAIL_COLD_PCT,
            "guardrail_saatchi_online_10p_pct": GUARDRAIL_SAATCHI_10P_PCT,
        },
        "candidates": decisions,
        "chosen_variant": chosen,
        "rationale": rationale,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n_splits = 2 if args.smoke else 5
    n_boot = 1_000 if args.smoke else N_BOOTSTRAP
    cb_p, xgb_p = _load_best_params()
    if args.smoke:
        cb_p = {**cb_p, "iterations": min(cb_p.get("iterations", 1000), 100)}
        xgb_p = {**xgb_p, "num_boost_round": min(xgb_p.get("num_boost_round", 1000), 100)}
    logger.info(
        "Mode=%s n_splits=%d n_boot=%d CB iter=%d XGB iter=%d",
        "SMOKE" if args.smoke else "FULL",
        n_splits,
        n_boot,
        cb_p["iterations"],
        xgb_p["num_boost_round"],
    )

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    emap = load_enrichment_year_map()
    logger.info("enrichment_map size: %d", len(emap))

    summary_merge = merge_summary(df, emap)
    logger.info("merge: %s", json.dumps(summary_merge, indent=None))

    # warm_mask 사전 계산 (모든 variant 공통)
    from train_primary_market_v3_filtered import prepare_features as _prep

    _, _, groups_full = _prep(df)
    wmask = _warm_mask(groups_full)
    logger.info("warm_mask: warm=%d / cold=%d", int(wmask.sum()), int((~wmask).sum()))

    results = {}
    for v in VARIANTS:
        results[v] = run_variant(df, emap, v, cb_p, xgb_p, n_splits, wmask)

    artists_full = df["artist_slug"].astype(str).to_numpy()
    paired = {}
    for v in VARIANTS:
        if v == "V0":
            continue
        paired[f"{v}_vs_V0"] = paired_compare(
            results[v], results["V0"], artists_full, f"{v}_vs_V0", n_boot
        )

    decision = selection_decision(results, "V0")

    def _strip(d: dict) -> dict:
        return {k: vv for k, vv in d.items() if not k.startswith("_")}

    summary = {
        "config": {
            "scope": (
                "v3.5 step 1 cohort gating ablation. v3.4-2 step 5 V_year_only Δ-0.74%p 채택 "
                "후 cold cohort 차단 검증. 3 gating variants (saatchi-only / warm-only / "
                "saatchi-and-warm) + V0 baseline + V_year_only 비교."
            ),
            "mode": "SMOKE" if args.smoke else "FULL",
            "n_splits": n_splits,
            "n_bootstrap": n_boot,
            "random_seed": RANDOM_SEED,
            "production_routing": "warm=xgb_kf, cold=cb_gkf (no cell factor)",
            "variants": VARIANTS,
            "thresholds": {
                "primary_overall_delta_max": PRIMARY_THRESHOLD_PCT,
                "guardrail_cold_delta_max": GUARDRAIL_COLD_PCT,
                "guardrail_saatchi_10p_delta_max": GUARDRAIL_SAATCHI_10P_PCT,
            },
            "selection_rule": (
                "1) saatchi-conditional 1순위, 2) 동률 시 cold guardrail 더 안전, "
                "3) 셋 다 미충족 → abort"
            ),
        },
        "merge_summary": summary_merge,
        "variants": {v: _strip(results[v]) for v in VARIANTS},
        "paired_comparisons": paired,
        "decision": decision,
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print(f"v3.5 step 1 cohort gating ablation ({summary['config']['mode']})")
    print("=" * 100)
    print(
        f"\nMerge: saatchi {summary_merge['saatchi_year_after']}/{summary_merge['n_saatchi']} fill"
    )
    print("\nVariant overall + cohort breakdown:")
    print(
        f"  {'variant':<24} {'overall':>8} {'cold':>8} {'cold_le2':>8} {'warm_5_9':>8} {'sa_online':>10} {'sa_10p':>8}"
    )
    for v in VARIANTS:
        ev = results[v]["evaluation"]
        gr = ev["guardrail"]
        print(
            f"  {v:<24} {ev['primary']['mdape_pct']:>7.3f}% "
            f"{gr['cold']['mdape_pct']:>7.3f}% "
            f"{gr['cold_le2']['mdape_pct']:>7.3f}% "
            f"{gr['warm_5_9']['mdape_pct']:>7.3f}% "
            f"{gr['saatchi_online']['mdape_pct']:>9.3f}% "
            f"{gr['saatchi_online_10p']['mdape_pct']:>7.3f}%"
        )
    print("\nPaired vs V0 (artist-cluster CI95 + Wilcoxon artist p):")
    for label, comp in paired.items():
        bs = comp["artist_cluster_bootstrap"]
        print(
            f"  {label:<32} Δ={comp['diff_mdape_pct']:+.3f}%  "
            f"CI95=[{bs['ci_95_low']:+.3f}, {bs['ci_95_high']:+.3f}]  "
            f"excludes_zero={bs['ci_excludes_zero']}  "
            f"artist p={comp['wilcoxon_artist_p']}"
        )
    print("\nSelection decision (코덱스 v3.5 plan rule):")
    for cand in decision["candidates"]:
        print(
            f"  {cand['variant']:<24} "
            f"Δoverall={cand['delta_overall_mdape_pct']:+.3f}% (pass={cand['passes_primary']})  "
            f"Δcold={cand['delta_cold_mdape_pct']:+.3f}% (pass={cand['passes_guardrail_cold']})  "
            f"Δsa10p={cand['delta_saatchi_online_10p_mdape_pct']:+.3f}% (pass={cand['passes_guardrail_saatchi_10p']})  "
            f"all_pass={cand['all_pass']}"
        )
    print(f"\nChosen: {decision['chosen_variant']}")
    print(f"Rationale: {decision['rationale']}")
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
