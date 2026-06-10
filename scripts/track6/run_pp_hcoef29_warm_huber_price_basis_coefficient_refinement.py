#!/usr/bin/env python3
"""Run PP-HCOEF29: OOF Huber meta-coefficient blending for Warm candidates.

HCOEF28 confirmed that risk features such as quantile width and component
disagreement explain large-error risk, but risk-aware shrinkage did not produce
a repeated-validation-safe point prediction candidate. HCOEF29 therefore tests
a different Huber-specific route:

    residual = actual_log - hcoef_stable_log
    residual_hat = HuberRegressor(component_deltas, reliability_features)
    corrected_log = hcoef_stable_log + clip(strength * residual_hat, -cap, cap)

The model is cross-fitted on validation OOF rows before fixed test or 0604 are
read as confirmation checks. This keeps the experiment aligned with the Warm
Huber goal: interpretable low-dimensional coefficients, bounded corrections,
and no fixed-test-driven threshold selection.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef24_warm_huber_price_basis_coefficient_refinement as h24
from scripts.track6 import run_pp_hcoef28_warm_huber_price_basis_coefficient_refinement as h28


EXP_ID = "PP-HCOEF29"
EXP_SLUG = "PP-HCOEF29_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
H28_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF28_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)

BASELINE = h28.BASELINE
REFERENCE = h28.REFERENCE
PPV8 = h28.PPV8
SVC = h28.SVC
L10_COL = h28.L10_COL
L10_CANDIDATE = h28.L10_CANDIDATE
SEED = 20260608
N_REPEATS = h28.N_REPEATS
ROW_FRACTION = h28.ROW_FRACTION
ARTIST_FRACTION = h28.ARTIST_FRACTION

KEY_COLS = ["scope", "split", "_track6_row_id"]
BASE_COMPONENTS = [BASELINE, REFERENCE, PPV8, SVC, L10_CANDIDATE]
H26_FIXED = "hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1__pred_log"
H26_DIRECT = "hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1__pred_log"


@dataclass(frozen=True)
class FeatureSet:
    name: str
    features: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class CandidateConfig:
    feature_set: FeatureSet
    strength: float
    cap: float

    @property
    def candidate(self) -> str:
        return (
            f"hcoef29_{self.feature_set.name}"
            f"_s{slug_float(self.strength)}"
            f"_cap{slug_float(self.cap)}"
        )


def slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_seed_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load one row per artwork/scope plus base component rows for comparison."""
    if not H28_PREDICTIONS.exists():
        raise FileNotFoundError(f"Missing HCOEF28 predictions: {H28_PREDICTIONS}")
    raw = pd.read_csv(H28_PREDICTIONS, low_memory=False)
    base_rows = raw[raw["candidate"].eq(BASELINE)].drop_duplicates(KEY_COLS).copy()
    base_rows = h28.add_risk_features(base_rows)
    base_rows = add_meta_features(base_rows)
    existing = raw[raw["candidate"].isin(BASE_COMPONENTS)].copy()
    return base_rows, existing


def add_meta_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in [
        BASELINE,
        REFERENCE,
        PPV8,
        SVC,
        L10_COL,
        H26_FIXED,
        H26_DIRECT,
        "svc_group_n",
        "quantile_width",
        "l10_price_range_ratio",
        "log_area",
        "hcoef23_risk_score",
        "risk_norm",
        "pred_spread_numeric",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    # Component deltas keep the Huber target interpretable as a correction over
    # the current stable Warm prediction.
    out["current_delta"] = out[REFERENCE] - out[BASELINE]
    out["ppv8_delta"] = out[PPV8] - out[BASELINE]
    out["svc_delta"] = out[SVC] - out[BASELINE]
    out["l10_delta"] = out[L10_COL] - out[BASELINE]
    out["h26_fixed_delta"] = out[H26_FIXED] - out[BASELINE] if H26_FIXED in out else 0.0
    out["h26_direct_delta"] = out[H26_DIRECT] - out[BASELINE] if H26_DIRECT in out else 0.0

    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0).clip(lower=0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"])
    out["svc_reliability"] = (out["svc_group_n_log"] / np.log1p(80.0)).clip(0.0, 1.0)
    out["is_svc_artist_fallback"] = out["svc_group_level"].astype(str).eq("artist").astype(float)
    out["is_svc_low_n"] = out["svc_group_n"].lt(10).astype(float)
    out["is_svc_high_n"] = out["svc_group_n"].ge(30).astype(float)
    out["risk_norm"] = pd.to_numeric(out.get("risk_norm", 0.0), errors="coerce").fillna(0.0).clip(0.0, 1.0)
    out["safe_weight"] = 1.0 - out["risk_norm"]

    # Interactions are still linear Huber features, but they let the coefficient
    # react differently when a component is reliable or risky.
    out["svc_delta_reliable"] = out["svc_delta"] * out["svc_reliability"]
    out["svc_delta_low_n"] = out["svc_delta"] * out["is_svc_low_n"]
    out["ppv8_delta_safe"] = out["ppv8_delta"] * out["safe_weight"]
    out["current_delta_safe"] = out["current_delta"] * out["safe_weight"]
    out["h26_fixed_delta_safe"] = out["h26_fixed_delta"] * out["safe_weight"]
    out["h26_direct_delta_safe"] = out["h26_direct_delta"] * out["safe_weight"]

    for col in out.columns:
        if col.endswith("_delta") or col.endswith("_safe") or col.endswith("_reliable") or col.endswith("_low_n"):
            out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def feature_sets() -> list[FeatureSet]:
    return [
        FeatureSet(
            name="core_component_delta",
            features=("current_delta", "ppv8_delta", "svc_delta", "l10_delta"),
            purpose="기존 70:30/PP-V8/유사 작품 기준가/quantile component가 stable 대비 얼마나 움직여야 하는지 Huber가 재학습",
        ),
        FeatureSet(
            name="svc_reliability_delta",
            features=(
                "svc_delta",
                "svc_delta_reliable",
                "svc_delta_low_n",
                "svc_group_n_log",
                "is_svc_artist_fallback",
                "is_svc_high_n",
            ),
            purpose="유사 작품 기반 가격 피처의 표본 수와 fallback 수준에 따라 보정 계수를 다르게 학습",
        ),
        FeatureSet(
            name="risk_guarded_component",
            features=(
                "current_delta",
                "ppv8_delta",
                "svc_delta",
                "l10_delta",
                "quantile_width",
                "l10_price_range_ratio",
                "pred_spread_numeric",
                "hcoef23_risk_score",
                "risk_norm",
                "svc_group_n_log",
            ),
            purpose="component 이동 신호와 HCOEF28에서 확인된 큰 오차 위험 신호를 함께 학습",
        ),
        FeatureSet(
            name="h26_candidate_delta",
            features=(
                "h26_fixed_delta",
                "h26_direct_delta",
                "h26_fixed_delta_safe",
                "h26_direct_delta_safe",
                "risk_norm",
                "svc_group_n_log",
            ),
            purpose="HCOEF26 fixed 후보와 direct 후보의 이동분을 OOF Huber가 다시 계수화",
        ),
        FeatureSet(
            name="all_lowdim_signal",
            features=(
                "current_delta",
                "ppv8_delta",
                "svc_delta",
                "l10_delta",
                "h26_fixed_delta",
                "h26_direct_delta",
                "svc_delta_reliable",
                "ppv8_delta_safe",
                "current_delta_safe",
                "quantile_width",
                "pred_spread_numeric",
                "risk_norm",
                "svc_group_n_log",
                "is_svc_artist_fallback",
            ),
            purpose="저차원 component, 신뢰도, 위험도 신호를 모두 사용하되 correction cap으로 과한 이동 방어",
        ),
    ]


def build_configs() -> list[CandidateConfig]:
    configs: list[CandidateConfig] = []
    for fset in feature_sets():
        for strength in [0.50, 0.75, 1.00]:
            for cap in [0.02, 0.03, 0.05, 0.08]:
                configs.append(CandidateConfig(fset, strength, cap))
    return configs


def make_model() -> Any:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000),
    )


def fit_model(X: np.ndarray, y: np.ndarray) -> Any:
    model = make_model()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        try:
            model.fit(X, y)
            return model
        except Exception:
            fallback = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
            fallback.fit(X, y)
            return fallback


def matrix(frame: pd.DataFrame, features: tuple[str, ...]) -> np.ndarray:
    return frame[list(features)].replace([np.inf, -np.inf], np.nan).to_numpy(dtype=float)


def target(frame: pd.DataFrame) -> np.ndarray:
    return (
        pd.to_numeric(frame["actual_log"], errors="coerce")
        - pd.to_numeric(frame[BASELINE], errors="coerce")
    ).fillna(0.0).to_numpy(dtype=float)


def crossfit_residual(frame: pd.DataFrame, features: tuple[str, ...], mode: str) -> tuple[np.ndarray, Any]:
    X = matrix(frame, features)
    y = target(frame)
    pred = np.zeros(len(frame), dtype=float)
    if mode == "artist":
        groups = frame["artist_key"].fillna("unknown").astype(str).to_numpy()
        unique_groups = np.unique(groups)
        n_splits = min(5, len(unique_groups))
        if n_splits < 2:
            splitter = KFold(n_splits=5, shuffle=True, random_state=SEED)
            splits = splitter.split(X)
        else:
            splitter = GroupKFold(n_splits=n_splits)
            splits = splitter.split(X, y, groups)
    else:
        splitter = KFold(n_splits=5, shuffle=True, random_state=SEED)
        splits = splitter.split(X)

    for train_idx, hold_idx in splits:
        model = fit_model(X[train_idx], y[train_idx])
        pred[hold_idx] = model.predict(X[hold_idx])
    full_model = fit_model(X, y)
    return pred, full_model


def coefficient_rows(model: Any, config: CandidateConfig, model_label: str) -> list[dict[str, Any]]:
    estimator = model.named_steps.get("huberregressor") or model.named_steps.get("ridge")
    coefs = getattr(estimator, "coef_", np.zeros(len(config.feature_set.features)))
    rows: list[dict[str, Any]] = []
    for feature, coef in zip(config.feature_set.features, coefs):
        rows.append(
            {
                "candidate": config.candidate,
                "model_label": model_label,
                "feature_set": config.feature_set.name,
                "feature": feature,
                "coefficient": float(coef),
                "direction": "가격 상승 보정 방향" if coef > 0 else "가격 하락 보정 방향",
                "interpretation": feature_interpretation(feature, float(coef)),
            }
        )
    return rows


def feature_interpretation(feature: str, coef: float) -> str:
    direction = "높일 때 실제 가격이 stable보다 높았던 방향" if coef > 0 else "높일 때 실제 가격이 stable보다 낮았던 방향"
    mapping = {
        "current_delta": "기존 70:30 후보가 stable보다 높거나 낮게 보는 정도",
        "ppv8_delta": "오차 안정화 component가 stable보다 높거나 낮게 보는 정도",
        "svc_delta": "유사 작품 기반 가격 피처가 stable보다 높거나 낮게 보는 정도",
        "l10_delta": "quantile 계열 component가 stable보다 높거나 낮게 보는 정도",
        "h26_fixed_delta": "HCOEF26 fixed 확인 후보의 이동분",
        "h26_direct_delta": "HCOEF26 direct 후보의 이동분",
        "svc_delta_reliable": "유사 작품 표본 수가 많을 때의 유사 작품 기준가 이동분",
        "svc_delta_low_n": "유사 작품 표본 수가 부족할 때의 유사 작품 기준가 이동분",
        "ppv8_delta_safe": "risk가 낮을 때의 오차 안정화 component 이동분",
        "current_delta_safe": "risk가 낮을 때의 기존 70:30 후보 이동분",
        "h26_fixed_delta_safe": "risk가 낮을 때의 HCOEF26 fixed 후보 이동분",
        "h26_direct_delta_safe": "risk가 낮을 때의 HCOEF26 direct 후보 이동분",
        "quantile_width": "예측 가격 범위가 넓은 정도",
        "l10_price_range_ratio": "q10~q90 가격 범위가 중앙값 대비 얼마나 넓은지",
        "pred_spread_numeric": "주요 후보 예측값 사이의 벌어짐",
        "hcoef23_risk_score": "이전 실험에서 확인한 큰 오차 위험 신호 합",
        "risk_norm": "HCOEF28 Huber risk model의 정규화된 위험도",
        "svc_group_n_log": "유사 작품 표본 수의 로그값",
        "is_svc_artist_fallback": "세부 조건 표본이 부족해 작가 전체 기준으로 fallback된 여부",
        "is_svc_high_n": "유사 작품 표본 수가 충분한지 여부",
    }
    return f"{mapping.get(feature, feature)}; 계수 기준 {direction}"


def generate_candidates(seed: pd.DataFrame, existing: pd.DataFrame, configs: list[CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    row_val = seed[seed["scope"].eq("validation_oof_row")].copy()
    artist_val = seed[seed["scope"].eq("validation_oof_artist")].copy()
    records: list[pd.DataFrame] = [existing.copy()]
    coeff_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []

    for config in configs:
        row_oof, row_model = crossfit_residual(row_val, config.feature_set.features, mode="row")
        artist_oof, artist_model = crossfit_residual(artist_val, config.feature_set.features, mode="artist")
        coeff_rows.extend(coefficient_rows(row_model, config, "row_validation_full_for_fixed_and_0604"))
        coeff_rows.extend(coefficient_rows(artist_model, config, "artist_oof_full"))

        for scope, scope_frame in seed.groupby("scope", sort=False):
            out = scope_frame.copy()
            if scope == "validation_oof_row":
                residual_hat = row_oof
            elif scope == "validation_oof_artist":
                residual_hat = artist_oof
            else:
                residual_hat = row_model.predict(matrix(out, config.feature_set.features))
            correction = np.clip(config.strength * residual_hat, -config.cap, config.cap)
            pred_log = out[BASELINE].to_numpy(dtype=float) + correction
            out["candidate"] = config.candidate
            out["method"] = "oof_huber_meta_residual_cap"
            out["source_candidate"] = config.feature_set.name
            out["mask_name"] = config.feature_set.name
            out["mask_applied"] = 1.0
            out["strength"] = config.strength
            out["cap"] = config.cap
            out["move_weight"] = np.divide(correction, np.where(np.abs(residual_hat) < 1e-9, np.nan, residual_hat))
            out["pred_log"] = pred_log
            out["pred_price"] = np.exp(np.clip(pred_log, 0, 30))
            out["policy_move_log"] = correction
            out["residual_log"] = out["actual_log"] - out["pred_log"]
            out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"]
            records.append(out)

        policy_rows.append(
            {
                "candidate": config.candidate,
                "feature_set": config.feature_set.name,
                "features": ", ".join(config.feature_set.features),
                "strength": config.strength,
                "cap": config.cap,
                "formula": "hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap)",
                "purpose": config.feature_set.purpose,
            }
        )

    predictions = pd.concat(records, ignore_index=True, sort=False)
    predictions["experiment_id"] = EXP_ID
    return predictions, pd.DataFrame(coeff_rows), pd.DataFrame(policy_rows)


def selected_table(metrics: pd.DataFrame, repeated: pd.DataFrame, source_basis: pd.DataFrame) -> pd.DataFrame:
    out = h28.selected_table(metrics, repeated, source_basis)
    # Keep the original HCOEF28 decision labels, but add a concise candidate type
    # so reviewers can separate repeated-safe candidates from fixed-only probes.
    out["candidate_type"] = np.select(
        [
            out["candidate"].eq(BASELINE),
            out["candidate"].eq(REFERENCE),
            out["decision"].isin(["반복 검증 통과 후보", "반복 any2 검증 후보"]),
            out["decision"].eq("fixed 확인 후보"),
            out["decision"].eq("MAPE 목적 후보"),
        ],
        ["현재 안정 기준", "기존 70:30 기준", "재검증 우선 후보", "fixed 확인 후보", "MAPE 연구 후보"],
        default="보류",
    )
    return out


def write_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    repeated: pd.DataFrame,
    residuals: pd.DataFrame,
    coeffs: pd.DataFrame,
    policies: pd.DataFrame,
) -> None:
    base = selected[selected["candidate"].eq(BASELINE)].iloc[0]
    accepted = selected[selected["decision"].isin(["반복 검증 통과 후보", "반복 any2 검증 후보", "fixed 확인 후보"])].copy()
    if accepted.empty:
        best_line = "새 운영 후보 채택 없음."
    else:
        best = accepted.iloc[0]
        best_line = (
            f"상위 확인 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed `{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`, "
            f"repeated min any2 `{best.get('repeated_min_any2_improve_prob', np.nan):.4f}`, "
            f"min all3 `{best.get('repeated_min_all3_improve_prob', np.nan):.4f}`)."
        )

    selected_cols = [
        "candidate",
        "candidate_type",
        "decision",
        "row_oof_MdAPE",
        "row_oof_MAPE",
        "row_oof_p95_APE",
        "artist_oof_MdAPE",
        "artist_oof_MAPE",
        "artist_oof_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "repeated_min_any2_improve_prob",
        "repeated_min_all3_improve_prob",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
        "test_mean_move_weight",
    ]
    metric_cols = ["scope", "candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "mean_move_weight"]
    repeat_cols = [
        "source_scope",
        "validation_scheme",
        "candidate",
        "mean_delta_MdAPE_vs_stable",
        "mean_delta_MAPE_vs_stable",
        "mean_delta_p95_APE_vs_stable",
        "MdAPE_improve_prob",
        "MAPE_improve_prob",
        "p95_improve_prob",
        "any2_improve_prob",
        "all3_improve_prob",
    ]
    top_repeat = repeated[repeat_cols].sort_values(["any2_improve_prob", "all3_improve_prob"], ascending=False).head(80) if not repeated.empty else repeated
    coef_focus = coeffs.copy()
    coef_focus["abs_coefficient"] = coef_focus["coefficient"].abs()
    coef_focus = coef_focus.sort_values(["candidate", "model_label", "abs_coefficient"], ascending=[True, True, False]).head(160)

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber OOF meta coefficient 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: 현재 안정 후보 `hcoef_stable` 위에 component delta와 신뢰도 피처를 Huber로 다시 계수화해 고정 70:30보다 안정적인 보정 후보가 나오는지 확인.",
            "- 후보 선택: validation OOF와 반복 split/artist holdout 우선.",
            "- fixed test와 0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 안정 기준 `hcoef_stable` fixed test: `{base['test_MdAPE']:.4f}/{base['test_MAPE']:.4f}/{base['test_p95_APE']:.4f}`.",
            "- fixed test에서만 좋아진 후보는 운영 후보가 아니라 추가 재검증 후보로 분리.",
            "",
            "## 2. 보정 공식",
            "",
            "- 학습 target: `actual_log - hcoef_stable_log`.",
            "- Huber 입력: component delta, 유사 작품 표본 신뢰도, quantile/risk 피처.",
            "- 적용식: `corrected_log = hcoef_stable_log + clip(strength * HuberResidual, -cap, cap)`.",
            "- cap은 0.02/0.03/0.05/0.08 log 단위로 고정하고 fixed test에서 고르지 않음.",
            "",
            "## 3. 후보 설정",
            "",
            h24.md_table(policies, max_rows=80),
            "",
            "## 4. 선택 후보 요약",
            "",
            h24.md_table(selected[selected_cols].round(4), max_rows=80),
            "",
            "## 5. Scope별 metrics",
            "",
            h24.md_table(metrics[metric_cols].round(4), max_rows=140),
            "",
            "## 6. 반복 split/artist holdout 요약",
            "",
            h24.md_table(top_repeat.round(4), max_rows=80),
            "",
            "## 7. Huber 계수 해석",
            "",
            h24.md_table(coef_focus.drop(columns=["abs_coefficient"]).round(6), max_rows=160),
            "",
            "## 8. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=100),
            "",
            "## 9. 다음 방향",
            "",
            "- 반복 검증 후보가 있으면 HCOEF30에서 후보 수를 줄이고 artist-level holdout을 더 강하게 재검증.",
            "- fixed 확인 후보만 있으면 cap/strength를 더 세밀하게 조정하지 말고, 계수 방향을 기준으로 원인 구간을 별도 분석.",
            "- 새 후보가 없으면 Huber 계수 기반 점 보정보다 가격 범위/신뢰도 정책을 우선 반영.",
            "",
            "## 10. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/repeated_iteration_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/policy_configurations.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef29_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef29_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(configs: list[CandidateConfig]) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-HCOEF28",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "candidate_count": len(configs),
        "n_repeats": N_REPEATS,
        "row_fraction": ROW_FRACTION,
        "artist_fraction": ARTIST_FRACTION,
        "selection_rule": "validation OOF/repeated split first; fixed test and 0604 confirmation only",
        "formula": "hcoef_stable + clip(strength * Huber(features -> actual_log - hcoef_stable), -cap, cap)",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    seed, existing = load_seed_frame()
    configs = build_configs()
    predictions, coeffs, policies = generate_candidates(seed, existing, configs)
    metrics = h28.point_metrics(predictions)
    detail, repeated = h28.repeated_validation(predictions)
    source_basis = policies[["candidate", "purpose"]].rename(columns={"candidate": "source_candidate", "purpose": "source_reason"})
    selected = selected_table(metrics, repeated, source_basis)
    residuals = h28.residual_analysis(predictions, selected)

    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    detail.to_csv(EXP_DIR / "outputs" / "repeated_iteration_metrics.csv", index=False)
    repeated.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    policies.to_csv(EXP_DIR / "outputs" / "policy_configurations.csv", index=False)
    write_config(configs)
    write_report(metrics, selected, repeated, residuals, coeffs, policies)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
