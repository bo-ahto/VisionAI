"""v3.4-2 step 5 ablation: year_made enrichment 의 model signal upper-bound 측정.

코덱스 v3.4-2 step 5 권장 (research framing):
- "현재 production 후보 평가" 가 아니라 **"year signal upper-bound 측정"**
- production CB_FEATURES 에서 work_age/career_age/vintage/freshness 가 이미 제거됨
  (Codex 4차 P1 train/serve drift). 본 ablation 은 **"reintroduce drift-prone
  features"** 실험. deploy 즉시 가능 X.

Variants (3개):
- V0: 현재 production (CB_FEATURES 그대로, year_made 의존 feature 0개)
- V_year_only: + year_made + has_year_made + work_age
- V_full: + vintage_premium + freshness_discount + career_age

Production routing (cell calibration 없이 raw GBDT OOF — fair feature ablation):
- warm rows: xgb_kf (warm slice KFold OOF)
- cold rows: cb_gkf (GroupKFold OOF, no cell factor)

Primary endpoint:
- overall MdAPE — artist-cluster bootstrap CI95 (primary).
  paired Wilcoxon (row-level) 은 보조 표기 — row 독립 가정 깨짐 (코덱스 P1).

Guardrail (다중비교 줄이기 위해 보조 정보만):
- cold (warm 미포함) MdAPE
- cold_le2: cold ∩ artist row_count ≤ 2 (catastrophic cold)
- warm_5_9: wmask ∩ artist row_count 5-9
- saatchi_online MdAPE

Sentinel only (interpretation, decision X):
- has_year_made=1 vs 0 split (saatchi 만)
- D10 saatchi_online (n 작아 검정력 약함)

Note (코덱스 P1 R4):
- prepare_saatchi_dataset.py 가 career_stage_int 를 출력 안함 → V_full 의 saatchi-side
  vintage_premium 은 0 (default). freshness_discount 만 활성. artsy 는 정상.

Usage:
    # smoke (n_splits=2, fast wiring 검증)
    PYTHONPATH=src:scripts python3 scripts/v34_2_step5_year_made_ablation.py --smoke

    # full (n_splits=5, ~1-2 hr)
    PYTHONPATH=src:scripts python3 scripts/v34_2_step5_year_made_ablation.py
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import xgboost as xgb
from catboost import CatBoostRegressor
from saatchi_year_made_merger import (
    build_variant,
    load_enrichment_year_map,
    merge_summary,
    variant_added_features,
)
from scipy.stats import wilcoxon
from sklearn.model_selection import GroupKFold, KFold
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
OUT_JSON = OUT_DIR / "v34_2_step5_year_made_ablation.json"

RANDOM_SEED = 42
N_BOOTSTRAP = 10_000

VARIANTS = ["V0", "V_year_only", "V_full"]
CAT_FEATURES = [
    "support_type",
    "medium_category",
    "attribution_class",
    "gallery_type",
    "price_currency",
    "source",
]


def prepare_features_with_extra(
    df: pd.DataFrame, extra_features: list[str]
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """variant-aware prepare_features. CB_FEATURES + extra 만 selected."""
    feature_cols = CB_FEATURES + [c for c in extra_features if c not in CB_FEATURES]
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in dataset: {missing}")

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
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    cb_params: dict,
    xgb_params: dict,
    n_splits: int,
) -> tuple[np.ndarray, np.ndarray]:
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[GKF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool_dyn(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool_dyn(X.iloc[te]))

        Xtr_e, Xte_e, _enc = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y[tr]),
            num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y[te]))
    return cb_preds, xgb_preds


def kf_oof_warm_dyn(
    X_warm: pd.DataFrame,
    y_warm: np.ndarray,
    cb_params: dict,
    xgb_params: dict,
    n_splits: int,
) -> tuple[np.ndarray, np.ndarray]:
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    cb_preds = np.zeros(len(y_warm))
    xgb_preds = np.zeros(len(y_warm))
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[KF warm %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **cb_params,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool_dyn(X_warm.iloc[tr], y_warm[tr]))
        cb_preds[te] = cb.predict(_cb_pool_dyn(X_warm.iloc[te]))

        Xtr_e, Xte_e, _enc = _label_encode_xgb(X_warm.iloc[tr], X_warm.iloc[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y_warm[tr]),
            num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y_warm[te]))
    return cb_preds, xgb_preds


def production_routed_pred(
    cb_gkf_ln: np.ndarray,
    xgb_kf_ln_warm: np.ndarray,
    wmask: np.ndarray,
) -> np.ndarray:
    """Production routing: warm=xgb_kf, cold=cb_gkf (raw, no cell factor)."""
    assert int(wmask.sum()) == len(xgb_kf_ln_warm)
    pred_ln = cb_gkf_ln.copy()  # cold default
    pred_ln[wmask] = xgb_kf_ln_warm
    return np.exp(pred_ln)


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.median(np.abs(y_true - y_pred) / y_true) * 100)


def artist_cluster_bootstrap_ci(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    artists: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
    rng_seed: int = RANDOM_SEED,
) -> dict:
    """V_a 와 V_b 의 paired MdAPE 차이 (a − b) 의 artist-cluster bootstrap CI."""
    rng = np.random.default_rng(rng_seed)
    unique_artists = np.unique(artists)
    artist_to_idx = {a: np.where(artists == a)[0] for a in unique_artists}
    diffs = np.zeros(n_boot)
    for b in range(n_boot):
        sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
        idx = np.concatenate([artist_to_idx[a] for a in sampled_artists])
        m_a = mdape(y_true[idx], y_pred_a[idx])
        m_b = mdape(y_true[idx], y_pred_b[idx])
        diffs[b] = m_a - m_b
    ci_low = float(np.percentile(diffs, 2.5))
    ci_high = float(np.percentile(diffs, 97.5))
    return {
        "diff_median_mdape_pct": float(np.median(diffs)),
        "diff_mean_mdape_pct": float(np.mean(diffs)),
        "ci_95_low": ci_low,
        "ci_95_high": ci_high,
        "n_bootstrap": n_boot,
        "ci_excludes_zero": ci_low * ci_high > 0,
    }


def cohort_mdape(
    df: pd.DataFrame,
    y_true_price: np.ndarray,
    pred_price: np.ndarray,
    cohort_mask: np.ndarray,
) -> dict:
    n = int(cohort_mask.sum())
    if n == 0:
        return {"n": 0, "skipped": True}
    y = y_true_price[cohort_mask]
    p = pred_price[cohort_mask]
    return {
        "n": n,
        "mdape_pct": mdape(y, p),
    }


def evaluate_variant(
    df: pd.DataFrame,
    pred_price: np.ndarray,
    y_true_price: np.ndarray,
    wmask: np.ndarray,
) -> dict:
    """variant 별 cohort 평가 (코덱스 P0 R1 fix: cohort 정의 분리).

    cohort:
    - cold: ~wmask (warm 미포함, production routing 의 cold path)
    - cold_le2: cold ∩ artist row_count ≤ 2 (catastrophic cold subset)
    - warm_5_9: wmask ∩ artist row_count 5-9 (warm 안에서 year signal sniff)
    - saatchi_online: source=saatchi & target_market=online
    - saatchi_online × work_count bucket: production-routed 평균 희석 검증
    """
    artists = df["artist_slug"].astype(str).to_numpy()
    artist_counts_map = pd.Series(artists).value_counts().to_dict()
    artist_count_arr = np.array([artist_counts_map[a] for a in artists])

    cold_mask = ~wmask
    cold_le2_mask = cold_mask & (artist_count_arr <= 2)
    warm_5_9_mask = wmask & (artist_count_arr >= 5) & (artist_count_arr <= 9)
    target_market = derive_target_market(df["is_krw"])
    saatchi_online_mask = (df["source"].astype(str) == "saatchi").to_numpy() & (
        target_market == "online"
    )

    overall = mdape(y_true_price, pred_price)
    cold = cohort_mdape(df, y_true_price, pred_price, cold_mask)
    cold_le2 = cohort_mdape(df, y_true_price, pred_price, cold_le2_mask)
    warm_5_9 = cohort_mdape(df, y_true_price, pred_price, warm_5_9_mask)
    saatchi_online = cohort_mdape(df, y_true_price, pred_price, saatchi_online_mask)

    # saatchi_online × work_count bucket (코덱스 R4)
    so_strat: dict[str, dict] = {}
    for label, lo, hi in [("1-2", 1, 2), ("3-4", 3, 4), ("5-9", 5, 9), ("10+", 10, 10**9)]:
        sub = saatchi_online_mask & (artist_count_arr >= lo) & (artist_count_arr <= hi)
        so_strat[label] = cohort_mdape(df, y_true_price, pred_price, sub)

    return {
        "primary": {"mdape_pct": overall, "n": len(y_true_price)},
        "guardrail": {
            "cold": cold,
            "cold_le2": cold_le2,
            "warm_5_9": warm_5_9,
            "saatchi_online": saatchi_online,
        },
        "saatchi_online_by_work_count": so_strat,
    }


def run_variant(
    df: pd.DataFrame,
    enrichment_map: dict[str, int],
    variant: str,
    cb_params: dict,
    xgb_params: dict,
    n_splits: int,
) -> dict:
    """Variant 별 OOF + 평가."""
    t0 = time.time()
    df_v = build_variant(df, enrichment_map, variant)
    extras = variant_added_features(variant)
    X, y, groups = prepare_features_with_extra(df_v, extras)
    logger.info("[%s] features=%d (extras=%s)", variant, X.shape[1], extras)

    # GroupKFold OOF (전체 cold path 평가)
    cb_gkf_ln, _xgb_gkf_ln = gkf_oof_dyn(X, y, groups, cb_params, xgb_params, n_splits)

    # warm slice KFold OOF
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    _cb_kf_ln, xgb_kf_ln = kf_oof_warm_dyn(X_warm, y_warm, cb_params, xgb_params, n_splits)

    pred_routed = production_routed_pred(cb_gkf_ln, xgb_kf_ln, wmask)
    y_true_price = np.exp(y)
    eval_result = evaluate_variant(df_v, pred_routed, y_true_price, wmask)
    elapsed = time.time() - t0
    logger.info(
        "[%s] overall=%.3f%%  cold=%.3f%%  cold_le2=%.3f%%  warm_5_9=%.3f%%  saatchi_online=%.3f%%  (%.0fs)",
        variant,
        eval_result["primary"]["mdape_pct"],
        eval_result["guardrail"]["cold"]["mdape_pct"],
        eval_result["guardrail"]["cold_le2"]["mdape_pct"],
        eval_result["guardrail"]["warm_5_9"]["mdape_pct"],
        eval_result["guardrail"]["saatchi_online"]["mdape_pct"],
        elapsed,
    )

    return {
        "variant": variant,
        "extras": extras,
        "n_features": X.shape[1],
        "elapsed_sec": elapsed,
        "evaluation": eval_result,
        "_pred_price": pred_routed,
        "_y_true_price": y_true_price,
        "_artists": groups,
        "_wmask": wmask,
    }


def paired_compare(
    a: dict, b: dict, artists: np.ndarray, label: str, n_boot: int = N_BOOTSTRAP
) -> dict:
    """V_a vs V_b paired comparison.

    Primary: artist-cluster bootstrap CI95 (cluster-aware, decision basis).
    Auxiliary: Wilcoxon — row-level + artist-level. row-level 은 cluster 무시 (코덱스 P1).
    """
    y = a["_y_true_price"]
    pa = a["_pred_price"]
    pb = b["_pred_price"]
    abs_pct_a = np.abs(y - pa) / y * 100
    abs_pct_b = np.abs(y - pb) / y * 100
    diffs_per_row = abs_pct_a - abs_pct_b

    bootstrap = artist_cluster_bootstrap_ci(y, pa, pb, artists, n_boot=n_boot)

    # row-level Wilcoxon (보조) — artist cluster 독립 가정 깨짐
    try:
        w_stat, w_p = wilcoxon(diffs_per_row, zero_method="wilcox", alternative="two-sided")
        wilcoxon_row = {
            "statistic": float(w_stat),
            "p_value": float(w_p),
            "n": len(diffs_per_row),
            "caveat": "row-level, artist cluster 무시 — CI 가 primary",
        }
    except Exception as e:
        wilcoxon_row = {"error": str(e)}

    # artist-level aggregate Wilcoxon — cluster-aware 보조 (코덱스 P1)
    try:
        df_artist = pd.DataFrame({"artist": artists, "diff": diffs_per_row})
        artist_diffs = df_artist.groupby("artist")["diff"].median().to_numpy()
        if len(artist_diffs) >= 6:
            w_stat_a, w_p_a = wilcoxon(artist_diffs, zero_method="wilcox", alternative="two-sided")
            wilcoxon_artist = {
                "statistic": float(w_stat_a),
                "p_value": float(w_p_a),
                "n_artists": len(artist_diffs),
                "note": "artist-level aggregate (median per artist), cluster-aware",
            }
        else:
            wilcoxon_artist = {"skipped": True, "n_artists": len(artist_diffs)}
    except Exception as e:
        wilcoxon_artist = {"error": str(e)}

    return {
        "label": label,
        "a_overall_mdape": a["evaluation"]["primary"]["mdape_pct"],
        "b_overall_mdape": b["evaluation"]["primary"]["mdape_pct"],
        "diff_mdape_pct": a["evaluation"]["primary"]["mdape_pct"]
        - b["evaluation"]["primary"]["mdape_pct"],
        "artist_cluster_bootstrap": bootstrap,
        "wilcoxon_row_level_auxiliary": wilcoxon_row,
        "wilcoxon_artist_level_auxiliary": wilcoxon_artist,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="smoke mode: n_splits=2 + smaller n_bootstrap (빠른 wiring 검증)",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n_splits = 2 if args.smoke else 5
    n_boot = 1_000 if args.smoke else N_BOOTSTRAP

    cb_params, xgb_params = _load_best_params()
    if args.smoke:
        # smoke: 학습 빠르게
        cb_params = {**cb_params, "iterations": min(cb_params.get("iterations", 1000), 100)}
        xgb_params = {
            **xgb_params,
            "num_boost_round": min(xgb_params.get("num_boost_round", 1000), 100),
        }
    logger.info(
        "Mode: %s, n_splits=%d, n_bootstrap=%d, CB iter=%d / XGB iter=%d",
        "SMOKE" if args.smoke else "FULL",
        n_splits,
        n_boot,
        cb_params["iterations"],
        xgb_params["num_boost_round"],
    )

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    enrichment_map = load_enrichment_year_map()
    logger.info("enrichment_map size: %d", len(enrichment_map))

    summary_merge = merge_summary(df, enrichment_map)
    logger.info("merge summary: %s", json.dumps(summary_merge, indent=None))

    # 3 variants
    results: dict[str, dict] = {}
    for variant in VARIANTS:
        results[variant] = run_variant(
            df, enrichment_map, variant, cb_params, xgb_params, n_splits
        )

    # paired comparisons
    artists_full = df["artist_slug"].astype(str).to_numpy()
    comp_yo_v0 = paired_compare(
        results["V_year_only"], results["V0"], artists_full, "V_year_only_vs_V0", n_boot=n_boot
    )
    comp_full_v0 = paired_compare(
        results["V_full"], results["V0"], artists_full, "V_full_vs_V0", n_boot=n_boot
    )
    comp_full_yo = paired_compare(
        results["V_full"],
        results["V_year_only"],
        artists_full,
        "V_full_vs_V_year_only",
        n_boot=n_boot,
    )

    # serialize-safe summary (drop _ private keys)
    def _strip(d: dict) -> dict:
        return {k: v for k, v in d.items() if not k.startswith("_")}

    summary = {
        "config": {
            "scope": (
                "v3.4-2 step 5 research ablation: year_made enrichment의 model signal "
                "upper-bound 측정. CB_FEATURES 의 work_age/career_age/vintage/freshness 가 이미 "
                "production drift 정합 위해 제거되어 있어, 본 ablation 은 'reintroduce drift-prone "
                "features' 실험 — deploy 즉시 가능 X."
            ),
            "framing": "research only, not deployable",
            "mode": "SMOKE" if args.smoke else "FULL",
            "n_splits": n_splits,
            "n_bootstrap": n_boot,
            "random_seed": RANDOM_SEED,
            "production_routing": "warm=xgb_kf, cold=cb_gkf (no cell factor, fair feature ablation)",
            "primary_endpoint": (
                "overall MdAPE — artist-cluster bootstrap CI95. "
                "Wilcoxon (row-level + artist-level) 보조."
            ),
            "guardrail": ["cold", "cold_le2", "warm_5_9", "saatchi_online"],
            "variants": VARIANTS,
            "extras_per_variant": {v: variant_added_features(v) for v in VARIANTS},
            "saatchi_career_stage_int_caveat": (
                "prepare_saatchi_dataset.py 가 career_stage_int 를 출력 안하므로 V_full 의 saatchi-side "
                "vintage_premium 은 항상 0. freshness_discount 만 활성. (코덱스 P1 R4)"
            ),
        },
        "merge_summary": summary_merge,
        "variants": {v: _strip(results[v]) for v in VARIANTS},
        "paired_comparisons": {
            "V_year_only_vs_V0": comp_yo_v0,
            "V_full_vs_V0": comp_full_v0,
            "V_full_vs_V_year_only": comp_full_yo,
        },
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print(f"v3.4-2 step 5 ablation ({summary['config']['mode']})")
    print("=" * 100)
    print(f"\nMerge summary:")
    for k, v in summary_merge.items():
        print(f"  {k}: {v}")
    print("\nVariant overall MdAPE (cohort breakdown):")
    for v in VARIANTS:
        eval_v = results[v]["evaluation"]
        gr = eval_v["guardrail"]
        print(
            f"  {v:<15} overall={eval_v['primary']['mdape_pct']:>6.3f}%  "
            f"cold={gr['cold']['mdape_pct']:>6.3f}% (n={gr['cold']['n']})  "
            f"cold_le2={gr['cold_le2']['mdape_pct']:>6.3f}% (n={gr['cold_le2']['n']})  "
            f"warm_5_9={gr['warm_5_9']['mdape_pct']:>6.3f}% (n={gr['warm_5_9']['n']})  "
            f"saatchi_online={gr['saatchi_online']['mdape_pct']:>6.3f}%"
        )
    print("\nsaatchi_online × work_count bucket:")
    for v in VARIANTS:
        so = results[v]["evaluation"]["saatchi_online_by_work_count"]
        parts = [
            f"{lbl}: {so[lbl].get('mdape_pct', 0):.2f}% (n={so[lbl].get('n', 0)})"
            for lbl in ["1-2", "3-4", "5-9", "10+"]
        ]
        print(f"  {v:<15} {' / '.join(parts)}")
    print("\nPaired comparisons (CI95 primary, Wilcoxon 보조):")
    for label, comp in summary["paired_comparisons"].items():
        b = comp["artist_cluster_bootstrap"]
        wr = comp["wilcoxon_row_level_auxiliary"]
        wa = comp["wilcoxon_artist_level_auxiliary"]
        wa_p = wa.get("p_value", "N/A") if isinstance(wa, dict) else "N/A"
        wr_p = wr.get("p_value", "N/A") if isinstance(wr, dict) else "N/A"
        print(
            f"  [{label}] Δ={comp['diff_mdape_pct']:+.3f}%  "
            f"CI95=[{b['ci_95_low']:+.3f}, {b['ci_95_high']:+.3f}]  "
            f"excludes_zero={b['ci_excludes_zero']}  "
            f"Wilcoxon row p={wr_p}  artist p={wa_p}"
        )
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
