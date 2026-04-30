"""v3 Group 1.8: Leave-one-gallery-out CV.

특정 Artsy 갤러리의 작품 전체를 학습에서 제외하고, 그 갤러리의 작품을 예측 → MdAPE
산출. "새 갤러리에 대한 일반화 능력" 진단.

방법:
- Top-N (default 10) Artsy 갤러리 by n_works
- 각 G에 대해:
  · 학습 데이터: (전체 28,376) - (gallery_name == G 작품)
  · 평가 데이터: gallery_name == G 작품
- Production routing (primary_predictor.py 와 정합):
  · warm (작가 본인 작품수 ≥ 5건 [학습 후]): XGBoost only, no calibration
  · cold: CatBoost only + cold cell factors
- 메트릭 per gallery: n_total / n_warm / n_cold / overall MdAPE / warm MdAPE / cold MdAPE / W30
- Aggregate: MdAPE 평균 ± std, baseline (full GroupKFold OOF) 대비 차이

산출물:
    model_test_results/v3_diagnostics/loo_gallery.json
    model_test_results/v3_diagnostics/loo_gallery_mdape.png

Usage:
    PYTHONPATH=src python3 scripts/v3_loo_gallery.py
    # 기본 N=10. N=5로 빠르게 돌리려면 LOO_N=5 환경변수.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import (
    CB_FEATURES, CAT_FEATURES, _cb_pool, _label_encode_xgb,
    WARM_MIN_COUNT, load_data, prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OUT_JSON = DIAG_DIR / "loo_gallery.json"
OUT_PNG = DIAG_DIR / "loo_gallery_mdape.png"
RANDOM_SEED = 42

LOO_N = int(os.environ.get("LOO_N", 10))


def _load_best_params() -> tuple[dict, dict]:
    path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["catboost"], data["xgboost"]


def _load_cold_factors() -> dict[str, float]:
    path = OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json"
    return json.loads(path.read_text())["cold_factors"]


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def _train_cb_xgb(
    X_tr: pd.DataFrame, y_tr: np.ndarray, cb_params: dict, xgb_params: dict,
) -> tuple[CatBoostRegressor, xgb.Booster, dict]:
    """Train CB and XGB on full training data (no fold split)."""
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=0,
        random_seed=RANDOM_SEED, allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr))

    Xtr_e, _, label_maps = _label_encode_xgb(X_tr, X_tr.iloc[:1])
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
        dtrain=xgb.DMatrix(Xtr_e, label=y_tr),
        num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    return cb, booster, label_maps


def _predict_production(
    cb: CatBoostRegressor, booster: xgb.Booster, label_maps: dict,
    X_te: pd.DataFrame, source_te: np.ndarray, target_market_te: np.ndarray,
    is_warm_te: np.ndarray, cold_factors: dict[str, float],
) -> np.ndarray:
    """Production routing 예측 (예측가격 KRW)."""
    # Cold: CB
    cb_ln = cb.predict(_cb_pool(X_te))
    # Warm: XGB
    Xte_e = X_te.copy()
    for col in CAT_FEATURES:
        mapping = label_maps.get(col, {})
        unseen = len(mapping)
        Xte_e[col] = Xte_e[col].astype(str).map(
            lambda v, m=mapping, u=unseen: m.get(str(v), u)
        ).astype(float)
    xgb_ln = booster.predict(xgb.DMatrix(Xte_e))

    # 라우팅
    pred_ln = np.where(is_warm_te, xgb_ln, cb_ln)
    pred_price = np.exp(pred_ln)

    # cold cell calibration (cold만)
    cell = np.array([f"{s}_{t}" for s, t in zip(source_te, target_market_te)])
    cold_mask = ~is_warm_te
    for k, f in cold_factors.items():
        m = cold_mask & (cell == k)
        if m.any():
            pred_price[m] = pred_price[m] * f
    return pred_price


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    cb_params, xgb_params = _load_best_params()
    cold_factors = _load_cold_factors()
    logger.info("Best params: CB iter=%d / XGB n_boost=%d", cb_params["iterations"], xgb_params["num_boost_round"])
    logger.info("Cold factors: %s", cold_factors)

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y, groups = prepare_features(df)
    df["_idx"] = np.arange(len(df))
    source = df["source"].astype(str).to_numpy()
    target_market = np.where(df["is_krw"].astype(int) == 1, "gallery", "online")
    gallery = df["gallery_name"].astype(str).to_numpy()

    # Top-N Artsy 갤러리 선정
    artsy_mask = source == "artsy"
    g_counts = pd.Series(gallery[artsy_mask]).value_counts()
    top_galleries = g_counts.head(LOO_N).index.tolist()
    logger.info("Top-%d Artsy galleries (총 n_works=%d):", LOO_N, sum(g_counts.head(LOO_N).values))
    for g, n in g_counts.head(LOO_N).items():
        logger.info("  %s: n=%d", g, n)

    overall_start = time.time()
    results: list[dict] = []
    for i, g in enumerate(top_galleries, 1):
        held_out_mask = (source == "artsy") & (gallery == g)
        n_held = int(held_out_mask.sum())
        if n_held == 0:
            continue

        train_idx = np.where(~held_out_mask)[0]
        test_idx = np.where(held_out_mask)[0]

        # 학습 후 warm 정의: train fold에서 작품수 ≥ 5인 작가
        train_groups = groups[train_idx]
        artist_counts_train = pd.Series(train_groups).value_counts()
        warm_set = set(artist_counts_train[artist_counts_train >= WARM_MIN_COUNT].index)
        test_groups = groups[test_idx]
        is_warm_te = np.array([str(a) in warm_set for a in test_groups])

        n_warm = int(is_warm_te.sum())
        n_cold = int((~is_warm_te).sum())

        logger.info("=" * 80)
        logger.info("[%d/%d] gallery=%s n_test=%d (warm=%d cold=%d) n_train=%d",
                    i, LOO_N, g, n_held, n_warm, n_cold, len(train_idx))

        t0 = time.time()
        X_tr = X.iloc[train_idx]
        y_tr = y[train_idx]
        cb, booster, label_maps = _train_cb_xgb(X_tr, y_tr, cb_params, xgb_params)
        train_wall = time.time() - t0

        X_te = X.iloc[test_idx]
        y_te = np.exp(y[test_idx])
        pred = _predict_production(
            cb, booster, label_maps, X_te,
            source[test_idx], target_market[test_idx], is_warm_te, cold_factors,
        )

        overall_mdape = mdape(y_te, pred)
        overall_w30 = w30(y_te, pred)
        warm_mdape = mdape(y_te[is_warm_te], pred[is_warm_te]) if n_warm else None
        cold_mdape = mdape(y_te[~is_warm_te], pred[~is_warm_te]) if n_cold else None
        warm_w30 = w30(y_te[is_warm_te], pred[is_warm_te]) if n_warm else None
        cold_w30 = w30(y_te[~is_warm_te], pred[~is_warm_te]) if n_cold else None

        logger.info("[%s] overall MdAPE=%.2f%% W30=%.2f%% (warm=%s cold=%s, train=%.0fs)",
                    g, overall_mdape, overall_w30,
                    f"{warm_mdape:.2f}" if warm_mdape is not None else "-",
                    f"{cold_mdape:.2f}" if cold_mdape is not None else "-",
                    train_wall)

        results.append({
            "gallery": g,
            "n_total": n_held,
            "n_warm": n_warm,
            "n_cold": n_cold,
            "n_train": int(len(train_idx)),
            "train_seconds": float(train_wall),
            "overall": {"MdAPE": overall_mdape, "W30": overall_w30},
            "warm": {"MdAPE": warm_mdape, "W30": warm_w30, "n": n_warm},
            "cold": {"MdAPE": cold_mdape, "W30": cold_w30, "n": n_cold},
        })

    total_wall = time.time() - overall_start

    # Aggregate
    overall_mdapes = np.array([r["overall"]["MdAPE"] for r in results])
    cold_mdapes = np.array([r["cold"]["MdAPE"] for r in results if r["cold"]["MdAPE"] is not None])
    warm_mdapes = np.array([r["warm"]["MdAPE"] for r in results if r["warm"]["MdAPE"] is not None])

    # Baseline 비교 (production cold/warm overall MdAPE — calibration JSON 참조)
    cal = json.loads((OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text())
    baseline_cold = cal["cold_overall"]["calibrated_mdape_cross_fit_guarded"]
    baseline_warm = cal["warm_overall"]["baseline_mdape"]

    summary = {
        "config": {
            "loo_n": LOO_N,
            "rng_seed": RANDOM_SEED,
            "warm_min_count": WARM_MIN_COUNT,
            "evaluation": "production routing (warm=XGB / cold=CB+cell calibration)",
            "baseline_cold_full_groupkfold": baseline_cold,
            "baseline_warm_full_kfold": baseline_warm,
            "interpretation": (
                "각 갤러리를 학습에서 제외 후 그 갤러리 작품 예측. baseline (full OOF) 보다 "
                "MdAPE가 크게 악화되면 모델이 갤러리별 패턴에 과도하게 의존했다는 신호. "
                "MdAPE가 비슷하면 새 갤러리에도 일반화 가능. "
                "Scope: top-N Artsy 갤러리 (거래량 ~60% 차지) 한정 — 66개 전체 일반화 결론으로 확장 금지. "
                "Warm 비교 caveat: baseline warm 9.7%는 KFold이고 이번 LOO warm은 '같은 작가라도 해당 "
                "갤러리 작품은 전부 제거된 더 어려운 과제'라 직접 apples-to-apples 비교 아님. "
                "정확한 해석: warm cross-gallery transfer 가 baseline warm 보다 더 어려움."
            ),
            "acceptance_gate": "SOFT (observe-and-report) — 운영 gate가 아니라 관찰/리포트용 진단",
        },
        "per_gallery": results,
        "aggregate": {
            "n_galleries": len(results),
            "overall_mdape_mean": float(np.mean(overall_mdapes)),
            "overall_mdape_std": float(np.std(overall_mdapes)),
            "overall_mdape_min": float(np.min(overall_mdapes)),
            "overall_mdape_max": float(np.max(overall_mdapes)),
            "cold_mdape_mean": float(np.mean(cold_mdapes)) if len(cold_mdapes) else None,
            "cold_mdape_std": float(np.std(cold_mdapes)) if len(cold_mdapes) else None,
            "warm_mdape_mean": float(np.mean(warm_mdapes)) if len(warm_mdapes) else None,
            "warm_mdape_std": float(np.std(warm_mdapes)) if len(warm_mdapes) else None,
        },
        "wall_seconds_total": float(total_wall),
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    # PNG: bar chart of MdAPE per gallery
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    galleries = [r["gallery"][:30] for r in results]
    overalls = [r["overall"]["MdAPE"] for r in results]
    colds = [r["cold"]["MdAPE"] if r["cold"]["MdAPE"] is not None else 0 for r in results]
    warms = [r["warm"]["MdAPE"] if r["warm"]["MdAPE"] is not None else 0 for r in results]
    x = np.arange(len(galleries))
    w = 0.27
    ax.bar(x - w, overalls, width=w, color="#4FC3F7", label="overall")
    ax.bar(x, colds, width=w, color="#E57373", label="cold")
    ax.bar(x + w, warms, width=w, color="#81C784", label="warm")
    ax.axhline(baseline_cold, color="#E57373", linestyle="--", linewidth=1, alpha=0.7,
               label=f"baseline cold ({baseline_cold:.1f}%)")
    ax.axhline(baseline_warm, color="#81C784", linestyle="--", linewidth=1, alpha=0.7,
               label=f"baseline warm ({baseline_warm:.1f}%)")
    ax.set_xticks(x)
    ax.set_xticklabels(galleries, rotation=35, ha="right", color="white", fontsize=9)
    ax.set_ylabel("MdAPE (%)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")
    ax.grid(alpha=0.2, axis="y")
    ax.legend(loc="upper right", framealpha=0.85, fontsize=9)
    fig.suptitle(
        f"v3 Group 1.8 Leave-one-gallery-out CV (top-{LOO_N} Artsy galleries, production routing)",
        color="white", fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=120, facecolor="#1a1a1a")
    plt.close(fig)
    logger.info("plot saved: %s", OUT_PNG)

    # Console summary
    print("\n" + "=" * 100)
    print(f"v3 Group 1.8 Leave-one-gallery-out CV Summary (top-{LOO_N} Artsy galleries)")
    print("=" * 100)
    print(f"\n{'Gallery':<35} {'n':>5} {'warm':>5} {'cold':>5} {'MdAPE':>8} {'cold MdAPE':>11} {'warm MdAPE':>11}")
    print("-" * 100)
    for r in results:
        cm = f"{r['cold']['MdAPE']:>8.2f}%" if r["cold"]["MdAPE"] is not None else f"{'-':>9}"
        wm = f"{r['warm']['MdAPE']:>8.2f}%" if r["warm"]["MdAPE"] is not None else f"{'-':>9}"
        print(f"{r['gallery'][:34]:<35} {r['n_total']:>5} {r['n_warm']:>5} {r['n_cold']:>5} "
              f"{r['overall']['MdAPE']:>7.2f}% {cm:>11} {wm:>11}")
    agg = summary["aggregate"]
    print("\n" + "-" * 100)
    print(f"Overall MdAPE: mean={agg['overall_mdape_mean']:.2f}% std={agg['overall_mdape_std']:.2f}% "
          f"range=[{agg['overall_mdape_min']:.2f}%, {agg['overall_mdape_max']:.2f}%]")
    if agg["cold_mdape_mean"] is not None:
        print(f"Cold MdAPE:    mean={agg['cold_mdape_mean']:.2f}% std={agg['cold_mdape_std']:.2f}% "
              f"(baseline {baseline_cold:.2f}% per cross-fit guarded)")
    if agg["warm_mdape_mean"] is not None:
        print(f"Warm MdAPE:    mean={agg['warm_mdape_mean']:.2f}% std={agg['warm_mdape_std']:.2f}% "
              f"(baseline {baseline_warm:.2f}% per warm KFold)")
    print(f"\nTotal wall: {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print(f"저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
