"""v3 Group 1.2: v1 vs v2 메트릭 비교 (paired test 한계 명시).

이상적으로는 v1과 v2의 동일 sample OOF 예측 쌍에 paired Wilcoxon을 적용해야
하나, **v1 OOF raw 예측이 산출물에 보존되지 않아 엄밀 paired test 불가**.
대안으로 다음을 산출:

1. v2 OOF에서 MdAPE Bootstrap 95% CI 산출 (10,000 resample)
2. v1 metrics.json의 점추정 MdAPE를 v2 CI에 비교 (CI 비겹침 여부)
3. 차이의 통계적 유의성을 CI 비겹침으로 간접 추정

한계:
- 학습 데이터가 다름: v1 n=29,361 (입체 포함), v2 n=28,376 (입체 985건 제외)
- v1 OOF raw 부재로 paired Wilcoxon 미실시 (Group 2.2 또는 후속에서 v1 재학습 필요)

v3.0 acceptance gate 정책 (§6 Group 1.2): SOFT gate — 결과를 정직 보고

산출물:
    model_test_results/v3_diagnostics/v1_v2_comparison.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
V1_PATH = ROOT / "model_test_results" / "integrated_v3_metrics.json"
V2_PATH = ROOT / "model_test_results" / "integrated_v3_filtered_tuned_metrics.json"
OOF_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "oof_predictions.npz"
OUT_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "v1_v2_comparison.json"
N_BOOTSTRAP = 10_000
RNG_SEED = 42


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def bootstrap_metric(
    y_true: np.ndarray, y_pred: np.ndarray, metric_fn,
    n_iter: int = N_BOOTSTRAP, alpha: float = 0.05,
) -> dict:
    rng = np.random.default_rng(RNG_SEED)
    n = len(y_true)
    values = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        values[i] = metric_fn(y_true[idx], y_pred[idx])
    return {
        "point": float(metric_fn(y_true, y_pred)),
        "ci_low": float(np.percentile(values, 100 * alpha / 2)),
        "ci_high": float(np.percentile(values, 100 * (1 - alpha / 2))),
        "ci_width": float(np.percentile(values, 100 * (1 - alpha / 2)) -
                          np.percentile(values, 100 * alpha / 2)),
    }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # v1 metrics 로드
    with V1_PATH.open() as f:
        v1 = json.load(f)
    # v2 metrics 로드 (참고용)
    with V2_PATH.open() as f:
        v2 = json.load(f)

    # v2 OOF 로드
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_kf_ln = oof["cb_preds_kf_ln"]
    xgb_kf_ln = oof["xgb_preds_kf_ln"]
    source_warm = oof["source_warm"]

    # ln → 원 가격 공간 변환
    y_actual = np.exp(y_actual_ln)
    cb_gkf = np.exp(cb_gkf_ln)
    xgb_gkf = np.exp(xgb_gkf_ln)
    ens_gkf = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)

    y_warm = np.exp(y_warm_ln)
    cb_kf = np.exp(cb_kf_ln)
    xgb_kf = np.exp(xgb_kf_ln)
    ens_kf = np.exp((cb_kf_ln + xgb_kf_ln) / 2)

    # v1 점추정 추출 (data: 29,361건)
    v1_summary = {
        "n": 29361,
        "data_note": v1.get("data", "29361 = Artsy+Artue 7640 + Saatchi 21721"),
        "groupkfold": {
            "catboost_v3": {"MdAPE": v1["groupkfold"]["catboost_v3"]["MdAPE"]},
            "xgboost_v3": {"MdAPE": v1["groupkfold"]["xgboost_v3"]["MdAPE"]},
            "ensemble": {"MdAPE": v1["groupkfold"]["ensemble"]["MdAPE"]},
            "baseline": {"MdAPE": v1["groupkfold"]["baseline"]["MdAPE"]},
        },
    }

    # v2 Bootstrap CI 산출 (cold path, GroupKFold, n=28,376)
    logger.info("Computing v2 Bootstrap CI for cold path (n=%d, %d iters)", len(y_actual), N_BOOTSTRAP)
    v2_cold = {
        "n": int(len(y_actual)),
        "catboost_v2_filtered_tuned": {
            "MdAPE": bootstrap_metric(y_actual, cb_gkf, mdape),
            "W30": bootstrap_metric(y_actual, cb_gkf, w30),
        },
        "xgboost_v2_filtered_tuned": {
            "MdAPE": bootstrap_metric(y_actual, xgb_gkf, mdape),
            "W30": bootstrap_metric(y_actual, xgb_gkf, w30),
        },
        "ensemble": {
            "MdAPE": bootstrap_metric(y_actual, ens_gkf, mdape),
            "W30": bootstrap_metric(y_actual, ens_gkf, w30),
        },
    }

    logger.info("Computing v2 Bootstrap CI for warm slice (n=%d)", len(y_warm))
    v2_warm = {
        "n": int(len(y_warm)),
        "catboost_v2_filtered_tuned": {
            "MdAPE": bootstrap_metric(y_warm, cb_kf, mdape),
            "W30": bootstrap_metric(y_warm, cb_kf, w30),
        },
        "xgboost_v2_filtered_tuned": {
            "MdAPE": bootstrap_metric(y_warm, xgb_kf, mdape),
            "W30": bootstrap_metric(y_warm, xgb_kf, w30),
        },
        "ensemble": {
            "MdAPE": bootstrap_metric(y_warm, ens_kf, mdape),
            "W30": bootstrap_metric(y_warm, ens_kf, w30),
        },
    }

    # warm Artsy slice
    artsy_mask = source_warm == "artsy"
    v2_warm_artsy = {
        "n": int(artsy_mask.sum()),
        "xgboost_v2_filtered_tuned": {
            "MdAPE": bootstrap_metric(y_warm[artsy_mask], xgb_kf[artsy_mask], mdape),
        },
        "ensemble": {
            "MdAPE": bootstrap_metric(y_warm[artsy_mask], ens_kf[artsy_mask], mdape),
        },
    }
    v2_warm["artsy"] = v2_warm_artsy

    # v1 점추정이 v2 95% CI에 들어가는지 비교 (cold path, ensemble)
    # v1 ensemble cold MdAPE = 38.7%
    # v2 ensemble cold MdAPE 95% CI (위)
    v1_ens_cold = v1["groupkfold"]["ensemble"]["MdAPE"]
    v2_ens_cold_ci = v2_cold["ensemble"]["MdAPE"]
    v1_in_v2_ci_ens_cold = (
        v2_ens_cold_ci["ci_low"] <= v1_ens_cold <= v2_ens_cold_ci["ci_high"]
    )

    v1_cb_cold = v1["groupkfold"]["catboost_v3"]["MdAPE"]
    v2_cb_cold_ci = v2_cold["catboost_v2_filtered_tuned"]["MdAPE"]
    v1_in_v2_ci_cb_cold = (
        v2_cb_cold_ci["ci_low"] <= v1_cb_cold <= v2_cb_cold_ci["ci_high"]
    )

    v1_xgb_cold = v1["groupkfold"]["xgboost_v3"]["MdAPE"]
    v2_xgb_cold_ci = v2_cold["xgboost_v2_filtered_tuned"]["MdAPE"]
    v1_in_v2_ci_xgb_cold = (
        v2_xgb_cold_ci["ci_low"] <= v1_xgb_cold <= v2_xgb_cold_ci["ci_high"]
    )

    output = {
        "config": {
            "method": "v1 point estimates compared to v2 OOF Bootstrap 95% CI",
            "limitation": (
                "v1 OOF raw predictions are not preserved in artifacts; rigorous paired "
                "Wilcoxon signed-rank test cannot be performed without re-training v1 on "
                "matched 28,376-row subset. v3 Group 2 후속에서 v1 재학습 + 정확한 paired "
                "test 시행 예정."
            ),
            "v1_data": "29,361건 (입체 포함)",
            "v2_data": "28,376건 (입체 985건 제외)",
            "data_subset_caveat": (
                "v1과 v2 학습 데이터가 985건 다름. v1 OOF가 985건 입체 작품에서 어떻게 "
                "동작하는지 알 수 없으므로 직접 비교는 conservative bound."
            ),
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RNG_SEED,
        },
        "v1_point_estimates": v1_summary,
        "v2_bootstrap_ci": {
            "cold_path_groupkfold": v2_cold,
            "warm_slice_kfold": v2_warm,
        },
        "comparison": {
            "cold_path_catboost": {
                "v1_point": v1_cb_cold,
                "v2_ci_low": v2_cb_cold_ci["ci_low"],
                "v2_ci_high": v2_cb_cold_ci["ci_high"],
                "v1_in_v2_ci": bool(v1_in_v2_ci_cb_cold),
                "interpretation": (
                    "v1 점추정이 v2 95% CI 외부 → 차이가 두드러질 가능성 (proxy 비교, formal test 아님)"
                    if not v1_in_v2_ci_cb_cold else
                    "v1 점추정이 v2 95% CI 내부 → 이 proxy 비교에서는 차이가 통계적으로 명확하지 않음 (formal paired test로 power 보강 필요)"
                ),
            },
            "cold_path_xgboost": {
                "v1_point": v1_xgb_cold,
                "v2_ci_low": v2_xgb_cold_ci["ci_low"],
                "v2_ci_high": v2_xgb_cold_ci["ci_high"],
                "v1_in_v2_ci": bool(v1_in_v2_ci_xgb_cold),
                "interpretation": (
                    "v1 점추정이 v2 95% CI 외부 → 차이가 두드러질 가능성 (proxy 비교, formal test 아님)"
                    if not v1_in_v2_ci_xgb_cold else
                    "v1 점추정이 v2 95% CI 내부 → 이 proxy 비교에서는 차이가 통계적으로 명확하지 않음 (formal paired test로 power 보강 필요)"
                ),
            },
            "cold_path_ensemble": {
                "v1_point": v1_ens_cold,
                "v2_ci_low": v2_ens_cold_ci["ci_low"],
                "v2_ci_high": v2_ens_cold_ci["ci_high"],
                "v1_in_v2_ci": bool(v1_in_v2_ci_ens_cold),
                "interpretation": (
                    "v1 점추정이 v2 95% CI 외부 → 차이가 두드러질 가능성 (proxy 비교, formal test 아님)"
                    if not v1_in_v2_ci_ens_cold else
                    "v1 점추정이 v2 95% CI 내부 → 이 proxy 비교에서는 차이가 통계적으로 명확하지 않음 (formal paired test로 power 보강 필요)"
                ),
            },
        },
    }

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Console summary
    print("\n=== v1 vs v2 Comparison (limitations apply, see JSON) ===\n")
    print(f"{'Slice':<28} {'Model':<22} {'v1 point':>10} {'v2 mean':>10} {'v2 95% CI':>22} {'v1 in CI?':>10}")
    print("-" * 105)
    for model_v1, model_v2 in [
        ("catboost_v3", "catboost_v2_filtered_tuned"),
        ("xgboost_v3", "xgboost_v2_filtered_tuned"),
        ("ensemble", "ensemble"),
    ]:
        v1_pt = v1["groupkfold"][model_v1]["MdAPE"]
        v2_ci = v2_cold[model_v2]["MdAPE"]
        in_ci = v2_ci["ci_low"] <= v1_pt <= v2_ci["ci_high"]
        print(f"{'Cold (GroupKFold)':<28} {model_v1.replace('_v3',''):<22} "
              f"{v1_pt:>9.2f}% {v2_ci['point']:>9.2f}% "
              f"[{v2_ci['ci_low']:>5.2f}, {v2_ci['ci_high']:>5.2f}] "
              f"{'YES' if in_ci else 'NO':>10}")

    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
