"""v3.1-3: Cold path 채택 규칙 ablation (v3 plan Group 2.2).

배경:
- 1.4 baseline 비교에서 RF cold 38.95% vs v2 ensemble cold 38.66% CI 겹침 → cold
  GBDT 우위 약함. v2 production 은 CatBoost only + cell calibration 사용 (cross-fit
  guarded 38.29%). raw OOF 기준 ensemble cold 가 38.66% 로 CatBoost 39.38% 보다
  우수 — cold ensemble + cell calibration 조합 검토 가치 있음.
- v3 plan Group 2.2: cold path 채택 규칙을 사전 정의 4단계 tie-break 으로 결정.
  채택 결정 산출 자체가 acceptance gate.

방법:
1. Cold path 4 option 비교:
   A. CatBoost only (현재 production cold path, raw)
   B. CatBoost only + cell calibration (현재 production)
   C. XGBoost only (raw)
   D. Ensemble (CB+XGB)/2 raw
   E. Ensemble (CB+XGB)/2 + cell calibration (proposed candidate)
2. Bootstrap 95% CI (artist-cluster, 5,000 iter) per option
3. Source-level breakdown (artsy / saatchi)
4. 4단계 tie-break 적용:
   tier 1: MdAPE 차이 ≥ 0.5%p (next-best 보다 의미있는 개선)
   tier 2: 95% CI 비겹침 (통계적 우위)
   tier 3: Latency (운영 추론 속도)
   tier 4: 운영 단순성 (코드 / artifact 단순도)

산출물:
    model_test_results/v3_diagnostics/cold_path_ablation.json

Usage:
    PYTHONPATH=src python3 scripts/v31_cold_path_ablation.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import load_data, prepare_features

from visionai.price_engine._eval_helpers import (
    apply_cell_calibration,
    cell_keys,
    derive_target_market,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
OUT_JSON = DIAG_DIR / "cold_path_ablation.json"

N_BOOTSTRAP = 5_000
RNG_SEED = 42
TIER1_THRESHOLD_PP = 0.5  # MdAPE 차이 의미있음 임계


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def cluster_bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    groups: np.ndarray,
    n_iter: int = N_BOOTSTRAP,
    alpha: float = 0.05,
    rng_seed: int = RNG_SEED,
) -> dict:
    """Artist-cluster bootstrap 95% CI on MdAPE."""
    rng = np.random.default_rng(rng_seed)
    valid = y_true > 0
    unique_groups = np.unique(groups)
    idx_by_group = {g: np.where(groups == g)[0] for g in unique_groups}
    n_g = len(unique_groups)
    values = np.empty(n_iter)
    for i in range(n_iter):
        chosen = rng.choice(n_g, size=n_g, replace=True)
        idx = np.concatenate([idx_by_group[unique_groups[c]] for c in chosen])
        v = valid[idx]
        if not v.any():
            values[i] = float("nan")
            continue
        values[i] = float(
            np.median(np.abs(y_true[idx][v] - y_pred[idx][v]) / y_true[idx][v]) * 100
        )
    point = mdape(y_true, y_pred)
    return {
        "point": float(point),
        "ci_low": float(np.percentile(values, 100 * alpha / 2)),
        "ci_high": float(np.percentile(values, 100 * (1 - alpha / 2))),
        "method": f"artist-cluster bootstrap (n_clusters={n_g}, {n_iter} iter)",
    }


def paired_cluster_delta_ci(
    y_true: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    groups: np.ndarray,
    *,
    label_a: str = "A",
    label_b: str = "B",
    n_iter: int = N_BOOTSTRAP,
    alpha: float = 0.05,
    rng_seed: int = RNG_SEED,
) -> dict:
    """Paired artist-cluster bootstrap on Δ MdAPE = MdAPE(a) - MdAPE(b).

    음수면 a 가 더 정확. CI 상한 < 0 ⇒ a 가 통계적으로 명확히 우수.
    """
    rng = np.random.default_rng(rng_seed)
    valid = y_true > 0
    unique_groups = np.unique(groups)
    idx_by_group = {g: np.where(groups == g)[0] for g in unique_groups}
    n_g = len(unique_groups)
    diffs = np.empty(n_iter)
    for i in range(n_iter):
        chosen = rng.choice(n_g, size=n_g, replace=True)
        idx = np.concatenate([idx_by_group[unique_groups[c]] for c in chosen])
        v = valid[idx]
        if not v.any():
            diffs[i] = 0.0
            continue
        ape_a = np.abs(y_true[idx][v] - pred_a[idx][v]) / y_true[idx][v]
        ape_b = np.abs(y_true[idx][v] - pred_b[idx][v]) / y_true[idx][v]
        diffs[i] = (np.median(ape_a) - np.median(ape_b)) * 100
    point_a = mdape(y_true, pred_a)
    point_b = mdape(y_true, pred_b)
    return {
        "label_a": label_a,
        "label_b": label_b,
        "delta_pp": float(point_a - point_b),
        "ci_low": float(np.percentile(diffs, 100 * alpha / 2)),
        "ci_high": float(np.percentile(diffs, 100 * (1 - alpha / 2))),
        "method": "paired artist-cluster bootstrap, Δ = MdAPE(a) - MdAPE(b)",
    }


def evaluate_option(
    label: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    source: np.ndarray,
    groups: np.ndarray,
) -> dict:
    overall_ci = cluster_bootstrap_ci(y_true, y_pred, groups)
    by_source: dict = {}
    for src in sorted(set(source.tolist())):
        m = source == src
        if not m.any():
            continue
        by_source[src] = {
            "n": int(m.sum()),
            "MdAPE": mdape(y_true[m], y_pred[m]),
            "W30": w30(y_true[m], y_pred[m]),
        }
    return {
        "label": label,
        "n": len(y_true),
        "overall": {
            "MdAPE": overall_ci["point"],
            "MdAPE_95_CI": [overall_ci["ci_low"], overall_ci["ci_high"]],
            "W30": w30(y_true, y_pred),
        },
        "by_source": by_source,
    }


def ci_overlaps(a: dict, b: dict) -> bool:
    """두 옵션 95% CI 가 겹치는가."""
    a_lo, a_hi = a["overall"]["MdAPE_95_CI"]
    b_lo, b_hi = b["overall"]["MdAPE_95_CI"]
    return not (a_hi < b_lo or b_hi < a_lo)


def apply_tiebreak(options: list[dict]) -> dict:
    """사전 정의 4단계 tie-break 적용. 결정 + 근거 산출."""
    sorted_opts = sorted(options, key=lambda o: o["overall"]["MdAPE"])
    best = sorted_opts[0]
    second = sorted_opts[1]
    diff_pp = second["overall"]["MdAPE"] - best["overall"]["MdAPE"]

    rationale: list[str] = []
    decision_label = best["label"]
    decision_tier: str | None = None

    # Tier 1: MdAPE 차이 ≥ 0.5%p
    if diff_pp >= TIER1_THRESHOLD_PP:
        rationale.append(
            f"Tier 1 (MdAPE 차이 ≥ {TIER1_THRESHOLD_PP}%p): {best['label']} {best['overall']['MdAPE']:.2f}% "
            f"vs {second['label']} {second['overall']['MdAPE']:.2f}% = {diff_pp:.2f}%p ≥ {TIER1_THRESHOLD_PP}%p ⇒ "
            f"{best['label']} 채택"
        )
        decision_tier = "tier1_mdape_diff"
    else:
        rationale.append(
            f"Tier 1 (MdAPE 차이 ≥ {TIER1_THRESHOLD_PP}%p): {best['label']} vs {second['label']} = "
            f"{diff_pp:.2f}%p < {TIER1_THRESHOLD_PP}%p ⇒ tie. Tier 2 진행"
        )
        # Tier 2: 95% CI 비겹침
        if not ci_overlaps(best, second):
            rationale.append(
                f"Tier 2 (95% CI 비겹침): {best['label']} CI {best['overall']['MdAPE_95_CI']} "
                f"vs {second['label']} CI {second['overall']['MdAPE_95_CI']} ⇒ 비겹침, {best['label']} 채택"
            )
            decision_tier = "tier2_ci_disjoint"
        else:
            rationale.append(
                f"Tier 2 (95% CI 비겹침): {best['label']} CI {best['overall']['MdAPE_95_CI']} "
                f"vs {second['label']} CI {second['overall']['MdAPE_95_CI']} ⇒ 겹침, tie. Tier 3 진행"
            )
            # Tier 3: Latency (정성 — 명시적 데이터 측정 미수행)
            latency_priority = {
                "A_catboost_raw": 1,
                "B_catboost_calibrated": 1,
                "C_xgboost_raw": 2,
                "D_ensemble_raw": 3,
                "E_ensemble_calibrated": 3,
            }
            best_lat = latency_priority.get(best["label"], 99)
            second_lat = latency_priority.get(second["label"], 99)
            if best_lat < second_lat:
                rationale.append(
                    f"Tier 3 (Latency): {best['label']} 단일 모델 (낮은 latency) vs "
                    f"{second['label']} 더 높은 추론 비용 ⇒ {best['label']} 채택"
                )
                decision_tier = "tier3_latency"
            elif best_lat > second_lat:
                # 더 빠른 second 채택
                decision_label = second["label"]
                rationale.append(
                    f"Tier 3 (Latency): {best['label']} ({best['overall']['MdAPE']:.2f}%) 보다 "
                    f"{second['label']} 가 더 빠른 추론 ({second['overall']['MdAPE']:.2f}%, MdAPE tie) ⇒ "
                    f"운영 latency 우선해 {second['label']} 채택"
                )
                decision_tier = "tier3_latency"
            else:
                rationale.append(
                    f"Tier 3 (Latency): {best['label']} vs {second['label']} 동등 latency, tie. Tier 4 진행"
                )
                # Tier 4: 운영 단순성
                simplicity_priority = {
                    "A_catboost_raw": 1,
                    "B_catboost_calibrated": 2,
                    "C_xgboost_raw": 1,
                    "D_ensemble_raw": 3,
                    "E_ensemble_calibrated": 4,
                }
                best_simp = simplicity_priority.get(best["label"], 99)
                second_simp = simplicity_priority.get(second["label"], 99)
                if best_simp < second_simp:
                    rationale.append(f"Tier 4 (운영 단순성): {best['label']} 더 단순 ⇒ 채택")
                    decision_tier = "tier4_simplicity"
                else:
                    decision_label = second["label"]
                    rationale.append(
                        f"Tier 4 (운영 단순성): {second['label']} 더 단순 (MdAPE tie 상태) ⇒ "
                        f"{second['label']} 채택"
                    )
                    decision_tier = "tier4_simplicity"

    return {
        "decision_label": decision_label,
        "decision_tier": decision_tier,
        "best_mdape": best["overall"]["MdAPE"],
        "second_best": {
            "label": second["label"],
            "MdAPE": second["overall"]["MdAPE"],
            "diff_pp": diff_pp,
        },
        "all_sorted": [
            {
                "label": o["label"],
                "MdAPE": o["overall"]["MdAPE"],
                "CI": o["overall"]["MdAPE_95_CI"],
            }
            for o in sorted_opts
        ],
        "rationale": rationale,
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    _, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)
    source = df["source"].astype(str).to_numpy()
    target_market = derive_target_market(df["is_krw"])
    cell = cell_keys(source, target_market)

    # 가격 변환
    y_full_price = np.exp(y_actual_ln)
    cb_cold_raw = np.exp(cb_gkf_ln)
    xgb_cold_raw = np.exp(xgb_gkf_ln)
    ens_cold_raw = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)

    cal = json.loads(
        (OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text()
    )
    cold_factors = cal["cold_factors"]
    cb_cold_calibrated = apply_cell_calibration(cb_cold_raw, cell, cold_factors)
    ens_cold_calibrated = apply_cell_calibration(ens_cold_raw, cell, cold_factors)

    # 5 options 평가
    options = [
        evaluate_option("A_catboost_raw", y_full_price, cb_cold_raw, source, groups),
        evaluate_option("B_catboost_calibrated", y_full_price, cb_cold_calibrated, source, groups),
        evaluate_option("C_xgboost_raw", y_full_price, xgb_cold_raw, source, groups),
        evaluate_option("D_ensemble_raw", y_full_price, ens_cold_raw, source, groups),
        evaluate_option(
            "E_ensemble_calibrated", y_full_price, ens_cold_calibrated, source, groups
        ),
    ]

    for o in options:
        ci = o["overall"]["MdAPE_95_CI"]
        logger.info(
            "[%s] MdAPE=%.2f%% [%.2f, %.2f] / W30=%.2f%%",
            o["label"],
            o["overall"]["MdAPE"],
            ci[0],
            ci[1],
            o["overall"]["W30"],
        )

    decision = apply_tiebreak(options)

    # Paired artist-cluster bootstrap ΔCI between top option (E) and current production (B)
    # — codex P1: ablation winner 정당화 시 individual CI 보다 paired ΔCI 가 정합
    paired_e_vs_b = paired_cluster_delta_ci(
        y_full_price,
        ens_cold_calibrated,
        cb_cold_calibrated,
        groups,
        label_a="E_ensemble_calibrated",
        label_b="B_catboost_calibrated",
    )
    # Reference: B vs A (calibration 효과만)
    paired_b_vs_a = paired_cluster_delta_ci(
        y_full_price,
        cb_cold_calibrated,
        cb_cold_raw,
        groups,
        label_a="B_catboost_calibrated",
        label_b="A_catboost_raw",
    )
    # E vs D (calibration 효과 in ensemble)
    paired_e_vs_d = paired_cluster_delta_ci(
        y_full_price,
        ens_cold_calibrated,
        ens_cold_raw,
        groups,
        label_a="E_ensemble_calibrated",
        label_b="D_ensemble_raw",
    )
    paired_results = {
        "E_vs_B (winner vs current production)": paired_e_vs_b,
        "B_vs_A (calibration 효과 — current production validates calibration)": paired_b_vs_a,
        "E_vs_D (calibration 효과 in ensemble)": paired_e_vs_d,
    }
    logger.info("=== Paired cluster ΔCI ===")
    for k, v in paired_results.items():
        logger.info("  %s: Δ=%+.2f%%p [%+.2f, %+.2f]", k, v["delta_pp"], v["ci_low"], v["ci_high"])

    summary = {
        "config": {
            "scope": (
                "Cold path 채택 규칙 ablation. 5 options × overall + by_source breakdown + "
                "artist-cluster bootstrap 95% CI. 사전 정의 4단계 tie-break 적용. "
                "Paired ΔCI (E vs B 등) 별도 산출 — ablation winner 정당화."
            ),
            "deploy_caveats": [
                "P1 deploy 정당화: 본 ablation 결정 (E_ensemble_calibrated) 은 'research/"
                "ablation winner' 로만 한정. paired cluster ΔCI(E-B) 가 0 을 포함하면 production "
                "변경 정당화 약함. deploy 시 별도 paired test + regression test + shadow/A/B 필요.",
                "P1 1.4 baseline gap (33.25%p) 도 cluster CI 단위로 재검토 권고. row-level CI "
                "[38.03, 39.19] 는 cold 일반화 질문에 낙관적이었음.",
                "P2 Tier 3 latency 정성 우선순위만 — 실측 (p50/p95 추론시간 + artifact load) "
                "필요. 현재는 'priors' 로만.",
                "P2 D10 saatchi 잔존 이슈 (v3.1-1) — E 채택해도 saatchi 고가 segment broad cell "
                "saturation 문제 그대로. 본격 대응은 v3.2 트랙.",
            ],
            "options_definition": {
                "A_catboost_raw": "CatBoost OOF, no calibration",
                "B_catboost_calibrated": "CatBoost OOF × cold cell factor (현재 production)",
                "C_xgboost_raw": "XGBoost OOF, no calibration",
                "D_ensemble_raw": "(CB + XGB) / 2 in ln-space, no calibration",
                "E_ensemble_calibrated": "(CB + XGB) / 2 in ln-space × cold cell factor",
            },
            "tiebreak": {
                "tier1_mdape_diff": f"≥ {TIER1_THRESHOLD_PP}%p — 의미있는 차이",
                "tier2_ci_disjoint": "95% CI 비겹침 — 통계적 우위",
                "tier3_latency": "단일 모델 < ensemble (추론 속도)",
                "tier4_simplicity": "raw < calibrated (코드/artifact 단순성)",
            },
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RNG_SEED,
            "tier1_threshold_pp": TIER1_THRESHOLD_PP,
        },
        "options": options,
        "decision": decision,
        "paired_cluster_delta_ci": paired_results,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 110)
    print("v3.1-3 Cold path 채택 규칙 ablation")
    print("=" * 110)
    print(
        f"\n{'Option':<28} {'overall MdAPE':>14} {'95% CI (cluster)':>22} {'W30':>7} "
        f"{'artsy MdAPE':>12} {'saatchi MdAPE':>14}"
    )
    print("-" * 110)
    for o in options:
        ov = o["overall"]
        bs = o["by_source"]
        artsy = bs.get("artsy", {}).get("MdAPE", float("nan"))
        saa = bs.get("saatchi", {}).get("MdAPE", float("nan"))
        print(
            f"{o['label']:<28} {ov['MdAPE']:>13.2f}% "
            f"[{ov['MdAPE_95_CI'][0]:>5.2f}, {ov['MdAPE_95_CI'][1]:>5.2f}] "
            f"{ov['W30']:>6.2f}% {artsy:>11.2f}% {saa:>13.2f}%"
        )

    print("\n" + "=" * 110)
    print("결정 (사전 정의 4단계 tie-break)")
    print("=" * 110)
    print(f"\nDecision: {decision['decision_label']} (tier: {decision['decision_tier']})")
    print(
        f"Best MdAPE: {decision['best_mdape']:.2f}%, "
        f"second: {decision['second_best']['label']} {decision['second_best']['MdAPE']:.2f}% "
        f"(diff {decision['second_best']['diff_pp']:+.2f}%p)"
    )
    print("\nRationale:")
    for r in decision["rationale"]:
        print(f"  • {r}")

    print("\n" + "=" * 110)
    print("Paired artist-cluster bootstrap ΔCI (winner 정당화 — codex P1)")
    print("=" * 110)
    for k, v in paired_results.items():
        print(f"  {k}")
        print(
            f"    Δ={v['delta_pp']:+.2f}%p  95% CI=[{v['ci_low']:+.2f}, {v['ci_high']:+.2f}]  "
            f"({'명확' if v['ci_high'] < 0 else '0 포함, 명확하지 않음'})"
        )
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
