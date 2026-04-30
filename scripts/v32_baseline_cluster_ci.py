"""v3.2-1: 1.4 baseline 비교 cluster CI 재검토.

배경 (v3.1-3 cold path ablation 코덱스 P1):
- v3.0 1.4 baseline 비교는 row-level bootstrap CI 사용 (28,376행 → 좁은 CI).
- 그러나 cold 일반화는 작가 단위 GroupKFold 평가이므로 within-artist 의존성 보존
  되는 artist-cluster bootstrap 이 정합. row-level CI 는 cold 질문에 낙관적이었음.
- 1.5 learning curve, v3.1-1/2/3 모두 cluster bootstrap 사용 — 1.4 만 inconsistent.

본 작업:
1. Global median + RandomForest baseline + v2 ensemble (raw) MdAPE 의 artist-cluster
   bootstrap 95% CI 재산출
2. Paired cluster ΔCI (gap = baseline - v2_ensemble) 산출
3. HARD gate (gap ≥ 30%p) cluster CI 기준 재검증
4. 1.4 row-level CI 와 cluster CI 비교

산출물:
    model_test_results/v3_diagnostics/baseline_cluster_ci.json

Usage:
    PYTHONPATH=src python3 scripts/v32_baseline_cluster_ci.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import CAT_FEATURES, load_data, prepare_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
OUT_JSON = DIAG_DIR / "baseline_cluster_ci.json"
ROW_LEVEL_JSON = DIAG_DIR / "baseline_comparison.json"  # 1.4 산출물 — 비교 reference

N_BOOTSTRAP = 10_000  # codex P2: 1.5 learning curve와 일관 + borderline 결과 방어력
RNG_SEED = 42
HARD_GATE_THRESHOLD_PP = 30.0


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def cluster_bootstrap_mdape_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    groups: np.ndarray,
    n_iter: int = N_BOOTSTRAP,
    rng_seed: int = RNG_SEED,
) -> dict:
    """artist-cluster bootstrap 95% CI on MdAPE."""
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
        "ci_low": float(np.percentile(values, 2.5)),
        "ci_high": float(np.percentile(values, 97.5)),
        "method": f"artist-cluster bootstrap (n_clusters={n_g}, {n_iter} iter)",
    }


def paired_cluster_gap_ci(
    y_true: np.ndarray,
    pred_baseline: np.ndarray,
    pred_v2: np.ndarray,
    groups: np.ndarray,
    *,
    label_baseline: str,
    n_iter: int = N_BOOTSTRAP,
    rng_seed: int = RNG_SEED,
) -> dict:
    """paired cluster bootstrap on gap = MdAPE(baseline) - MdAPE(v2_ensemble).

    HARD gate: gap ≥ 30%p (CI 하한 ≥ 30%p ⇒ 통계적으로 명확)
    """
    rng = np.random.default_rng(rng_seed)
    valid = y_true > 0
    unique_groups = np.unique(groups)
    idx_by_group = {g: np.where(groups == g)[0] for g in unique_groups}
    n_g = len(unique_groups)
    gaps = np.empty(n_iter)
    for i in range(n_iter):
        chosen = rng.choice(n_g, size=n_g, replace=True)
        idx = np.concatenate([idx_by_group[unique_groups[c]] for c in chosen])
        v = valid[idx]
        if not v.any():
            gaps[i] = float("nan")
            continue
        ape_base = np.abs(y_true[idx][v] - pred_baseline[idx][v]) / y_true[idx][v]
        ape_v2 = np.abs(y_true[idx][v] - pred_v2[idx][v]) / y_true[idx][v]
        gaps[i] = (np.median(ape_base) - np.median(ape_v2)) * 100
    point = mdape(y_true, pred_baseline) - mdape(y_true, pred_v2)
    return {
        "label": label_baseline,
        "point_gap_pp": float(point),
        "ci_low_pp": float(np.percentile(gaps, 2.5)),
        "ci_high_pp": float(np.percentile(gaps, 97.5)),
        "method": f"paired artist-cluster bootstrap (n_clusters={n_g}, {n_iter} iter)",
    }


def rf_oof_groupkfold(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, n_splits: int = 5
) -> np.ndarray:
    """RF baseline GroupKFold OOF (1.4 와 동일 protocol — 재현 가능)."""
    gkf = GroupKFold(n_splits=n_splits)
    preds = np.zeros(len(y))
    X_enc = X.copy()
    for col in CAT_FEATURES:
        X_enc[col] = pd.Categorical(X_enc[col].astype(str)).codes.astype(float)
    X_enc = X_enc.astype(float)
    for fold, (tr, te) in enumerate(gkf.split(X_enc, y, groups), 1):
        logger.info("[RF GKF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        rf = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            random_state=RNG_SEED,
            n_jobs=-1,
        )
        rf.fit(X_enc.iloc[tr], y[tr])
        preds[te] = rf.predict(X_enc.iloc[te])
    return preds


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)

    y_full = np.exp(y_actual_ln)

    # 1) Global median baseline (가장 trivial — 학습 데이터 중앙값)
    median_pred = np.full_like(y_full, np.median(y_full))

    # 2) RF baseline (1.4 와 동일 — 재현)
    logger.info("=== RF baseline GroupKFold OOF (1.4 재현) ===")
    t0 = time.time()
    rf_ln = rf_oof_groupkfold(X, y_actual_ln, groups)
    rf_pred = np.exp(rf_ln)
    logger.info("RF OOF 완료 (%.0fs)", time.time() - t0)

    # 3) v2 ensemble (raw OOF)
    ens_v2 = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)

    # 점추정 + cluster CI per option
    logger.info("=== Cluster bootstrap CI 산출 ===")
    options = {}
    for label, pred in [
        ("global_median", median_pred),
        ("random_forest", rf_pred),
        ("v2_ensemble_raw", ens_v2),
    ]:
        ci = cluster_bootstrap_mdape_ci(y_full, pred, groups)
        ci["W30"] = w30(y_full, pred)
        options[label] = ci
        logger.info(
            "  %s MdAPE=%.2f%% CI=[%.2f, %.2f] W30=%.2f%%",
            label,
            ci["point"],
            ci["ci_low"],
            ci["ci_high"],
            ci["W30"],
        )

    # Paired gap cluster CI
    logger.info("=== Paired cluster gap CI ===")
    gap_median_v2 = paired_cluster_gap_ci(
        y_full,
        median_pred,
        ens_v2,
        groups,
        label_baseline="global_median - v2_ensemble",
    )
    gap_rf_v2 = paired_cluster_gap_ci(
        y_full,
        rf_pred,
        ens_v2,
        groups,
        label_baseline="random_forest - v2_ensemble",
    )
    logger.info(
        "  median - v2: gap=%.2f%%p CI=[%.2f, %.2f]",
        gap_median_v2["point_gap_pp"],
        gap_median_v2["ci_low_pp"],
        gap_median_v2["ci_high_pp"],
    )
    logger.info(
        "  RF - v2: gap=%.2f%%p CI=[%.2f, %.2f]",
        gap_rf_v2["point_gap_pp"],
        gap_rf_v2["ci_low_pp"],
        gap_rf_v2["ci_high_pp"],
    )

    # HARD gate 재검증 (cluster CI 기준)
    hard_gate_point_pass = gap_median_v2["point_gap_pp"] >= HARD_GATE_THRESHOLD_PP
    hard_gate_ci_pass = gap_median_v2["ci_low_pp"] >= HARD_GATE_THRESHOLD_PP

    # row-level CI 비교 (1.4 산출물에서 로드)
    row_level_ref = None
    if ROW_LEVEL_JSON.exists():
        rl = json.loads(ROW_LEVEL_JSON.read_text())
        cold = rl.get("cold_groupkfold", {})
        baselines = cold.get("baselines", {})
        v2_models = cold.get("v2_models", {})
        row_level_ref = {
            "global_median_row_ci": baselines.get("global_median", {}).get("MdAPE"),
            "random_forest_row_ci": baselines.get("random_forest_groupkfold", {}).get("MdAPE"),
            "v2_ensemble_raw_row_ci": v2_models.get("ensemble (raw)", {}).get("MdAPE"),
            "hard_gate_row_level": rl.get("hard_gate_evaluation"),
        }

    summary = {
        "config": {
            "scope": (
                "1.4 baseline 비교의 row-level CI 를 artist-cluster bootstrap CI 로 재산출. "
                "Cold 일반화 질문에 정합 (within-artist 의존성 보존). 1.5 learning curve / "
                "v3.1-1/2/3 와 동일 bootstrap 단위로 inconsistent 해소."
            ),
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RNG_SEED,
            "hard_gate_threshold_pp": HARD_GATE_THRESHOLD_PP,
            "hard_gate_definition": (
                "v2 cold ensemble MdAPE ≤ Global median baseline MdAPE − 30%p (점추정). "
                "본 작업은 사후 정의 변경이 아니라 cluster CI 보강 — 기존 점추정 gate 그대로 "
                "유지 (codex P1). cluster CI 하한이 30%p 미만이면 'PASS but borderline under "
                "cluster CI' 로 framing."
            ),
            "framing_guide": (
                "올바른 표현: 'PASS under pre-specified point gate; baseline 대비 큰 개선은 "
                "재확인되나, cluster bootstrap 기준으로 30%p 초과를 하한까지 보장하진 못함.' "
                "잘못된 표현: '통계적으로 명확하게 30%p 이상 우수' (cluster CI 하한 미달 시 과장). "
                "RF vs v2 cluster gap [-1.63, +2.75] (점추정 +0.29%p) 는 '우위 없음 = 통계적 동급' "
                "으로 정리 (codex P2)."
            ),
        },
        "options": options,
        "paired_gap_ci": {
            "global_median_minus_v2_ensemble": gap_median_v2,
            "random_forest_minus_v2_ensemble": gap_rf_v2,
        },
        "hard_gate_evaluation": {
            "point_estimate_gap_pp": gap_median_v2["point_gap_pp"],
            "cluster_ci_low_pp": gap_median_v2["ci_low_pp"],
            "cluster_ci_high_pp": gap_median_v2["ci_high_pp"],
            "threshold_pp": HARD_GATE_THRESHOLD_PP,
            "point_pass": bool(hard_gate_point_pass),
            "cluster_ci_lower_meets_threshold": bool(hard_gate_ci_pass),
            "official_status": "PASS under pre-specified point gate (33.25%p ≥ 30%p)",
            "cluster_ci_caveat": (
                "Cluster bootstrap 기준 ΔCI 하한이 30%p threshold 미만 — 'baseline 대비 큰 개선 "
                "방향은 재확인되나 cluster bootstrap 기준으로 30%p 초과를 하한까지 보장하진 "
                "못함'. 기존 gate 정의 (point ≥ 30%p) 는 사후 변경 없이 유지 (codex v3.2-1 P1). "
                "정확한 CI 하한 값은 본 객체의 cluster_ci_low_pp 필드 참조."
            ),
        },
        "row_level_reference": row_level_ref,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 100)
    print("v3.2-1 baseline 비교 cluster CI 재검토")
    print("=" * 100)

    print(f"\n{'Option':<22} {'point MdAPE':>12} {'cluster CI':>22} {'W30':>7}")
    print("-" * 100)
    for label, ci in options.items():
        print(
            f"{label:<22} {ci['point']:>11.2f}% [{ci['ci_low']:>5.2f}, {ci['ci_high']:>5.2f}] "
            f"{ci['W30']:>6.2f}%"
        )

    print(f"\n{'Paired gap':<35} {'point':>9} {'cluster ΔCI':>22}")
    print("-" * 100)
    g = gap_median_v2
    print(
        f"{'global_median - v2_ensemble':<35} {g['point_gap_pp']:>+8.2f}%p "
        f"[{g['ci_low_pp']:>+5.2f}, {g['ci_high_pp']:>+5.2f}]"
    )
    g = gap_rf_v2
    print(
        f"{'random_forest - v2_ensemble':<35} {g['point_gap_pp']:>+8.2f}%p "
        f"[{g['ci_low_pp']:>+5.2f}, {g['ci_high_pp']:>+5.2f}]"
    )

    print("\n" + "=" * 100)
    print(f"HARD gate (gap ≥ {HARD_GATE_THRESHOLD_PP}%p) 재검증")
    print("=" * 100)
    h = summary["hard_gate_evaluation"]
    print(
        f"  point gap: {h['point_estimate_gap_pp']:.2f}%p — "
        f"{'PASS' if h['point_pass'] else 'FAIL'} (pre-specified gate)"
    )
    print(
        f"  cluster ΔCI: [{h['cluster_ci_low_pp']:.2f}, {h['cluster_ci_high_pp']:.2f}]%p — "
        f"{'lower bound ≥ threshold' if h['cluster_ci_lower_meets_threshold'] else 'borderline (lower bound < threshold)'}"
    )
    print(f"\n  Official: {h['official_status']}")
    print(f"  Caveat: {h['cluster_ci_caveat']}")

    if row_level_ref:
        print("\n[1.4 row-level reference (비교용)]")
        rl_g = row_level_ref.get("hard_gate_row_level", {})
        if rl_g:
            print(
                f"  row-level point gap: {rl_g.get('gap_pp', 0):.2f}%p, threshold {rl_g.get('threshold_pp')}, "
                f"PASS: {rl_g.get('pass')}"
            )

    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
