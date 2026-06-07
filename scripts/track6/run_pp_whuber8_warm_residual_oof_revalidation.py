#!/usr/bin/env python3
"""Run PP-WHUBER8 repeated OOF revalidation for Warm residual Huber corrections.

PP-WHUBER7 found several promising residual correction policies. This script
does not search a wider grid. It revalidates selected candidates by repeatedly
splitting the validation set:

- fit residual Huber on calibration folds
- apply the candidate correction policy to the holdout fold
- compare corrected prediction against the fixed current Warm candidate

The goal is to check whether the PP-WHUBER7 improvement is stable enough to
be promoted to a versioned model candidate.
"""
from __future__ import annotations

import html
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import KFold


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402
import run_pp_whuber_warm_huber_loss_regularization_tuning as whuber  # noqa: E402
import run_pp_whuber7_warm_residual_correction_methods as whuber7  # noqa: E402


warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="Skipping features without any observed values.*")


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WHUBER8"
EXP_SLUG = "PP-WHUBER8_warm_residual_oof_revalidation"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm residual Huber 반복 split/OOF 재검증"
SEED = 20260606
N_SPLITS = 5
N_REPEATS = 8

CURRENT_CANDIDATE = wcoef.CURRENT_CANDIDATE


CANDIDATE_SPECS: list[dict[str, Any]] = [
    {
        "candidate": "PP-WHUBER7_mdape_best_predbin_mid_open_tail_guard",
        "source_candidate": "PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35",
        "role": "MdAPE 우선 후보",
        "feature_set": "pred_size_material_svc_artist",
        "epsilon": 1.60,
        "alpha": 0.001,
        "method": "pred_bin_cap",
        "cap": 0.06,
        "strength": 0.35,
        "policy": "mid_open_tail_guard",
    },
    {
        "candidate": "PP-WHUBER7_balanced_all_metric_predbin_mid_open_tail_guard",
        "source_candidate": "PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25",
        "role": "세 지표 균형 후보",
        "feature_set": "pred_size_material_svc_artist",
        "epsilon": 1.35,
        "alpha": 0.01,
        "method": "pred_bin_cap",
        "cap": 0.08,
        "strength": 0.25,
        "policy": "mid_open_tail_guard",
    },
    {
        "candidate": "PP-WHUBER7_tail_guard_directional_under",
        "source_candidate": "PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08",
        "role": "큰 오차 방어 후보",
        "feature_set": "pred_size_svc",
        "epsilon": 1.05,
        "alpha": 0.001,
        "method": "directional_strength",
        "cap": 0.08,
        "strength": np.nan,
        "policy": "under_guard",
    },
    {
        "candidate": "PP-WHUBER7_validation_mdape_predbin_mid_open_tail_guard",
        "source_candidate": "PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_predbin_mid_open_tail_guard_cap0p08_s0p35",
        "role": "validation MdAPE 선택 후보",
        "feature_set": "pred_size_svc",
        "epsilon": 1.05,
        "alpha": 0.001,
        "method": "pred_bin_cap",
        "cap": 0.08,
        "strength": 0.35,
        "policy": "mid_open_tail_guard",
    },
    {
        "candidate": "PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard",
        "source_candidate": "PP-WHUBER7_pred_size_svc_eps1.20_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p35",
        "role": "validation 균형 선택 후보",
        "feature_set": "pred_size_svc",
        "epsilon": 1.20,
        "alpha": 0.01,
        "method": "pred_bin_cap",
        "cap": 0.08,
        "strength": 0.35,
        "policy": "mid_open_tail_guard",
    },
]


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    return whuber7.load_reference_frames()


def metric_from_pred(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return wcoef.metric_values(frame, pred_log)


def candidate_features(spec: dict[str, Any], frame: pd.DataFrame) -> list[str]:
    raw_features = whuber7.feature_sets()[spec["feature_set"]]
    return whuber.feature_exists(frame, raw_features)


def fit_predict_raw(train: pd.DataFrame, holdout: pd.DataFrame, features: list[str], alpha: float, epsilon: float) -> np.ndarray:
    y = train["ln_price_krw"].to_numpy(dtype=float) - train["current_pred_log"].to_numpy(dtype=float)
    model = whuber.huber_model(features, alpha, epsilon)
    tr = whuber.normalize(train.copy(), features)
    ho = whuber.normalize(holdout.copy(), features)
    model.fit(tr[features], y)
    return np.asarray(model.predict(ho[features]), dtype=float)


def apply_correction(frame: pd.DataFrame, raw: np.ndarray, spec: dict[str, Any]) -> np.ndarray:
    raw = np.asarray(raw, dtype=float)
    cap = float(spec["cap"])
    method = spec["method"]
    policy = spec["policy"]
    strength = spec.get("strength", np.nan)
    if method == "hard_clip":
        return np.clip(raw, -cap, cap) * float(strength)
    if method == "soft_tanh_cap":
        return cap * np.tanh(raw / max(cap, 1e-6)) * float(strength)
    if method == "reliability_shrink":
        return np.clip(raw, -cap, cap) * float(strength) * whuber7.rel_multiplier(frame, policy)
    if method == "pred_bin_cap":
        caps = whuber7.pred_bin_cap(frame, cap, policy)
        return np.clip(raw, -caps, caps) * float(strength)
    if method == "directional_strength":
        clipped = np.clip(raw, -cap, cap)
        direction = whuber7.DIRECTIONAL_POLICIES[policy]
        return np.where(clipped >= 0, clipped * direction["positive"], clipped * direction["negative"])
    if method == "hybrid_rel_predbin":
        rel_policy, bin_policy = policy.split("+", 1)
        caps = whuber7.pred_bin_cap(frame, cap, bin_policy)
        return np.clip(raw, -caps, caps) * float(strength) * whuber7.rel_multiplier(frame, rel_policy)
    raise ValueError(f"unknown correction method: {method}")


def repeat_oof_revalidation(val: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    repeat_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []
    current_pred = val["current_pred_log"].to_numpy(dtype=float)
    features_by_candidate = {
        spec["candidate"]: candidate_features(spec, val)
        for spec in CANDIDATE_SPECS
    }

    for repeat in range(N_REPEATS):
        kfold = KFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + repeat)
        oof_preds = {
            spec["candidate"]: np.zeros(len(val), dtype=float)
            for spec in CANDIDATE_SPECS
        }
        oof_corrections = {
            spec["candidate"]: np.zeros(len(val), dtype=float)
            for spec in CANDIDATE_SPECS
        }

        for fold, (train_idx, holdout_idx) in enumerate(kfold.split(val), 1):
            train_fold = val.iloc[train_idx].copy()
            holdout = val.iloc[holdout_idx].copy()
            current_holdout = holdout["current_pred_log"].to_numpy(dtype=float)
            current_metric = metric_from_pred(holdout, current_holdout)
            for spec in CANDIDATE_SPECS:
                features = features_by_candidate[spec["candidate"]]
                raw = fit_predict_raw(train_fold, holdout, features, float(spec["alpha"]), float(spec["epsilon"]))
                correction = apply_correction(holdout, raw, spec)
                pred = current_holdout + correction
                oof_preds[spec["candidate"]][holdout_idx] = pred
                oof_corrections[spec["candidate"]][holdout_idx] = correction
                metric = metric_from_pred(holdout, pred)
                fold_row = {
                    "experiment_id": EXP_ID,
                    "repeat": repeat,
                    "fold": fold,
                    "candidate": spec["candidate"],
                    "source_candidate": spec["source_candidate"],
                    "role": spec["role"],
                    "method": spec["method"],
                    "feature_set": spec["feature_set"],
                    "epsilon": spec["epsilon"],
                    "alpha": spec["alpha"],
                    "correction_cap": spec["cap"],
                    "correction_strength": spec["strength"],
                    "correction_policy": spec["policy"],
                    "n": len(holdout),
                    "mean_abs_correction": float(np.mean(np.abs(correction))),
                }
                for name, value in metric.items():
                    fold_row[name] = value
                    fold_row[f"delta_{name}"] = value - current_metric[name]
                fold_rows.append(fold_row)

        current_metric = metric_from_pred(val, current_pred)
        for spec in CANDIDATE_SPECS:
            pred = oof_preds[spec["candidate"]]
            correction = oof_corrections[spec["candidate"]]
            metric = metric_from_pred(val, pred)
            repeat_row = {
                "experiment_id": EXP_ID,
                "repeat": repeat,
                "candidate": spec["candidate"],
                "source_candidate": spec["source_candidate"],
                "role": spec["role"],
                "method": spec["method"],
                "feature_set": spec["feature_set"],
                "epsilon": spec["epsilon"],
                "alpha": spec["alpha"],
                "correction_cap": spec["cap"],
                "correction_strength": spec["strength"],
                "correction_policy": spec["policy"],
                "mean_abs_correction": float(np.mean(np.abs(correction))),
                "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
            }
            for name, value in metric.items():
                repeat_row[name] = value
                repeat_row[f"delta_{name}"] = value - current_metric[name]
            repeat_rows.append(repeat_row)
            part = pd.DataFrame({
                "experiment_id": EXP_ID,
                "repeat": repeat,
                "split": "validation_oof",
                "candidate": spec["candidate"],
                "_track6_row_id": val["_track6_row_id"].to_numpy(),
                "actual_log": val["ln_price_krw"].to_numpy(dtype=float),
                "actual_price": val["price_krw"].to_numpy(dtype=float),
                "current_pred_log": current_pred,
                "pred_log": pred,
                "correction_log": correction,
                "artist_key": val.get("artist_key", pd.Series([""] * len(val))).astype(str).to_numpy(),
            })
            pred_price = np.clip(np.exp(part["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
            part["ape"] = np.abs(pred_price - part["actual_price"].to_numpy(dtype=float)) / np.clip(part["actual_price"].to_numpy(dtype=float), 1.0, None)
            prediction_rows.append(part)

    return pd.DataFrame(repeat_rows), pd.DataFrame(fold_rows), pd.concat(prediction_rows, ignore_index=True)


def test_once_metrics(val: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    current_test = metric_from_pred(test, test["current_pred_log"].to_numpy(dtype=float))
    for spec in CANDIDATE_SPECS:
        features = candidate_features(spec, val)
        raw = fit_predict_raw(val, test, features, float(spec["alpha"]), float(spec["epsilon"]))
        correction = apply_correction(test, raw, spec)
        pred = test["current_pred_log"].to_numpy(dtype=float) + correction
        metric = metric_from_pred(test, pred)
        row = {
            "experiment_id": EXP_ID,
            "split": "test_once",
            "candidate": spec["candidate"],
            "source_candidate": spec["source_candidate"],
            "role": spec["role"],
            "method": spec["method"],
            "feature_set": spec["feature_set"],
            "epsilon": spec["epsilon"],
            "alpha": spec["alpha"],
            "correction_cap": spec["cap"],
            "correction_strength": spec["strength"],
            "correction_policy": spec["policy"],
            "mean_abs_correction": float(np.mean(np.abs(correction))),
        }
        for name, value in metric.items():
            row[name] = value
            row[f"delta_{name}"] = value - current_test[name]
        rows.append(row)
    current_row = {
        "experiment_id": EXP_ID,
        "split": "test_once",
        "candidate": CURRENT_CANDIDATE,
        "source_candidate": CURRENT_CANDIDATE,
        "role": "기준 후보",
        "method": "reference",
        "feature_set": "reference",
        "epsilon": np.nan,
        "alpha": np.nan,
        "correction_cap": np.nan,
        "correction_strength": np.nan,
        "correction_policy": "",
        "mean_abs_correction": 0.0,
    }
    for name, value in current_test.items():
        current_row[name] = value
        current_row[f"delta_{name}"] = 0.0
    rows.append(current_row)
    return pd.DataFrame(rows)


def summarize_repeats(repeat_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, group in repeat_metrics.groupby("candidate", observed=False):
        first = group.iloc[0]
        row = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "source_candidate": first["source_candidate"],
            "role": first["role"],
            "method": first["method"],
            "feature_set": first["feature_set"],
            "epsilon": first["epsilon"],
            "alpha": first["alpha"],
            "correction_cap": first["correction_cap"],
            "correction_strength": first["correction_strength"],
            "correction_policy": first["correction_policy"],
            "repeats": int(group["repeat"].nunique()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]:
            row[f"mean_{metric}"] = float(group[metric].mean())
            row[f"std_{metric}"] = float(group[metric].std(ddof=0))
            delta = group[f"delta_{metric}"]
            row[f"mean_delta_{metric}"] = float(delta.mean())
            row[f"p10_delta_{metric}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric}"] = float(np.mean(delta < 0))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["mean_delta_MdAPE", "mean_delta_MAPE", "mean_delta_p95_APE"])


def render_report(summary: pd.DataFrame, repeat_metrics: pd.DataFrame, test_metrics: pd.DataFrame) -> tuple[str, str]:
    test_current = test_metrics[test_metrics["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    summary_view = summary.copy()
    test_view = test_metrics.sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    stable = summary[
        (summary["improvement_probability_MdAPE"] >= 0.70)
        & (summary["improvement_probability_MAPE"] >= 0.70)
        & (summary["improvement_probability_p95_APE"] >= 0.60)
    ].copy()
    best_oof = summary.iloc[0]

    def summary_row(candidate: str) -> pd.Series | None:
        rows = summary[summary["candidate"].eq(candidate)]
        if rows.empty:
            return None
        return rows.iloc[0]

    def test_row(candidate: str) -> pd.Series | None:
        rows = test_metrics[test_metrics["candidate"].eq(candidate)]
        if rows.empty:
            return None
        return rows.iloc[0]

    def format_oof(candidate: str) -> str:
        row = summary_row(candidate)
        if row is None:
            return "OOF 결과 없음"
        return (
            "OOF 평균 delta MdAPE/MAPE/p95 "
            f"`{row['mean_delta_MdAPE']:.5f}` / `{row['mean_delta_MAPE']:.5f}` / "
            f"`{row['mean_delta_p95_APE']:.5f}`, 개선 확률 "
            f"`{row['improvement_probability_MdAPE']:.3f}` / "
            f"`{row['improvement_probability_MAPE']:.3f}` / "
            f"`{row['improvement_probability_p95_APE']:.3f}`"
        )

    def format_test(candidate: str) -> str:
        row = test_row(candidate)
        if row is None:
            return "test 1회 결과 없음"
        return (
            f"test MdAPE/MAPE/p95 `{row['MdAPE']:.4f}` / `{row['MAPE']:.4f}` / "
            f"`{row['p95_APE']:.4f}`, delta `{row['delta_MdAPE']:.5f}` / "
            f"`{row['delta_MAPE']:.5f}` / `{row['delta_p95_APE']:.5f}`"
        )

    oof_stable_candidate = "PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard"
    test_balanced_candidate = "PP-WHUBER7_balanced_all_metric_predbin_mid_open_tail_guard"
    tail_guard_candidate = "PP-WHUBER7_tail_guard_directional_under"
    mdape_only_candidate = "PP-WHUBER7_mdape_best_predbin_mid_open_tail_guard"
    conclusion_notes = [
        (
            "운영 후보는 하나로 바로 교체하지 않고 목적별로 분리해서 판단한다.",
            "같은 Huber 잔차 보정이라도 대표 정확도, 평균 오차, 큰 오차 방어 중 어떤 지표를 우선하느냐에 따라 적합 후보가 다르기 때문이다.",
        ),
        (
            f"반복 OOF 안정성 1순위: `{oof_stable_candidate}`.",
            f"{format_oof(oof_stable_candidate)}. {format_test(oof_stable_candidate)}. 반복 검증은 가장 안정적이지만 test 1회 개선폭은 작아 보수형 안정성 후보로 둔다.",
        ),
        (
            f"test 세 지표 균형 후보: `{test_balanced_candidate}`.",
            f"{format_oof(test_balanced_candidate)}. {format_test(test_balanced_candidate)}. test에서는 MdAPE/MAPE/p95가 모두 개선됐지만 반복 OOF p95 개선 확률이 낮아 artist-level split 또는 추가 holdout 확인 후 반영한다.",
        ),
        (
            f"큰 오차 방어 후보: `{tail_guard_candidate}`.",
            f"{format_oof(tail_guard_candidate)}. {format_test(tail_guard_candidate)}. 대표값 개선은 작지만 p95와 MAPE 방어력이 가장 명확하므로 서비스에서 큰 오차를 줄이는 보조 정책 후보로 본다.",
        ),
        (
            f"MdAPE 우선 후보: `{mdape_only_candidate}`.",
            f"{format_test(mdape_only_candidate)}. 중앙 정확도는 가장 좋지만 p95_APE가 악화되어 운영 기본 후보로 바로 쓰지 않는다.",
        ),
    ]
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 반복 검증: `{N_REPEATS}` repeats x `{N_SPLITS}` folds",
        "- 목적: PP-WHUBER7 목적별 후보가 validation 내부 반복 OOF에서도 안정적으로 개선되는지 확인",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        "",
        "## 1. 실행 결론",
        "",
        f"- 반복 OOF 기준 최상위 후보: `{best_oof['candidate']}`",
        f"- 최상위 후보 평균 delta MdAPE/MAPE/p95: `{best_oof['mean_delta_MdAPE']:.5f}` / `{best_oof['mean_delta_MAPE']:.5f}` / `{best_oof['mean_delta_p95_APE']:.5f}`",
        f"- 최상위 후보 개선 확률 MdAPE/MAPE/p95: `{best_oof['improvement_probability_MdAPE']:.3f}` / `{best_oof['improvement_probability_MAPE']:.3f}` / `{best_oof['improvement_probability_p95_APE']:.3f}`",
        f"- 안정성 기준 통과 후보 수: `{len(stable)}`",
    ]
    for title, detail in conclusion_notes:
        lines.append(f"- {title} {detail}")
    lines += [
        "",
        "## 2. 반복 OOF 요약",
        "",
        "| 후보 | 역할 | 방식 | 평균 delta MdAPE | MdAPE 개선 확률 | 평균 delta MAPE | MAPE 개선 확률 | 평균 delta p95 | p95 개선 확률 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_view.itertuples(index=False):
        lines.append(
            f"| `{row.candidate}` | {row.role} | {row.method} | "
            f"{row.mean_delta_MdAPE:.5f} | {row.improvement_probability_MdAPE:.3f} | "
            f"{row.mean_delta_MAPE:.5f} | {row.improvement_probability_MAPE:.3f} | "
            f"{row.mean_delta_p95_APE:.5f} | {row.improvement_probability_p95_APE:.3f} |"
        )
    lines += [
        "",
        "## 3. Test 1회 확인",
        "",
        f"- 기준 test MdAPE/MAPE/p95: `{test_current['MdAPE']:.4f}` / `{test_current['MAPE']:.4f}` / `{test_current['p95_APE']:.4f}`",
        "",
        "| 후보 | 역할 | MdAPE | MAPE | p95_APE | delta MdAPE | delta MAPE | delta p95 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in test_view.itertuples(index=False):
        lines.append(
            f"| `{row.candidate}` | {row.role} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | "
            f"{row.delta_MdAPE:.5f} | {row.delta_MAPE:.5f} | {row.delta_p95_APE:.5f} |"
        )
    lines += [
        "",
        "## 4. 산출물",
        "",
        "- `outputs/repeated_oof_summary.csv`",
        "- `outputs/repeated_oof_metrics.csv`",
        "- `outputs/repeated_oof_fold_metrics.csv`",
        "- `outputs/repeated_oof_predictions.csv`",
        "- `outputs/test_once_metrics.csv`",
    ]
    md = "\n".join(lines) + "\n"

    conclusion_html = "\n".join(
        f"<li>{html.escape(title)} {html.escape(detail)}</li>"
        for title, detail in conclusion_notes
    )
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">PP-WHUBER7 후보를 validation 내부 반복 OOF로 재검증한 리포트.</div>
<h2>실행 결론</h2>
<ul>
<li>반복 OOF 기준 최상위 후보: <code>{html.escape(str(best_oof['candidate']))}</code></li>
<li>평균 delta MdAPE/MAPE/p95: {best_oof['mean_delta_MdAPE']:.5f} / {best_oof['mean_delta_MAPE']:.5f} / {best_oof['mean_delta_p95_APE']:.5f}</li>
<li>개선 확률 MdAPE/MAPE/p95: {best_oof['improvement_probability_MdAPE']:.3f} / {best_oof['improvement_probability_MAPE']:.3f} / {best_oof['improvement_probability_p95_APE']:.3f}</li>
<li>안정성 기준 통과 후보 수: {len(stable)}</li>
{conclusion_html}
</ul>
<h2>반복 OOF 요약</h2>{summary_view.to_html(index=False, escape=True)}
<h2>Test 1회 확인</h2>{test_view.to_html(index=False, escape=True)}
<h2>반복별 원자료</h2>{repeat_metrics.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    summary: pd.DataFrame,
    repeat_metrics: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    test_metrics: pd.DataFrame,
) -> None:
    summary.to_csv(EXP_DIR / "outputs" / "repeated_oof_summary.csv", index=False)
    repeat_metrics.to_csv(EXP_DIR / "outputs" / "repeated_oof_metrics.csv", index=False)
    fold_metrics.to_csv(EXP_DIR / "outputs" / "repeated_oof_fold_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "repeated_oof_predictions.csv", index=False)
    test_metrics.to_csv(EXP_DIR / "outputs" / "test_once_metrics.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "n_splits": N_SPLITS,
        "n_repeats": N_REPEATS,
        "current_candidate": CURRENT_CANDIDATE,
        "candidate_specs": CANDIDATE_SPECS,
        "leakage_control": {
            "oof": "each validation holdout is predicted by residual model fitted on the other validation folds",
            "test_once": "candidate residual model fitted on full validation and applied once to test",
            "base_prediction": "fixed current Warm candidate prediction",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(summary, repeat_metrics, test_metrics)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    val, test = load_frames()
    repeat_metrics, fold_metrics, predictions = repeat_oof_revalidation(val)
    summary = summarize_repeats(repeat_metrics)
    test_metrics = test_once_metrics(val, test)
    write_outputs(summary, repeat_metrics, fold_metrics, predictions, test_metrics)
    best = summary.iloc[0]
    print(f"[{EXP_ID}] completed")
    print(f"best repeated OOF candidate: {best['candidate']}")
    print(
        "best mean delta MdAPE/MAPE/p95: "
        f"{best['mean_delta_MdAPE']:.5f} / {best['mean_delta_MAPE']:.5f} / {best['mean_delta_p95_APE']:.5f}"
    )
    print(
        "best improvement probability MdAPE/MAPE/p95: "
        f"{best['improvement_probability_MdAPE']:.3f} / "
        f"{best['improvement_probability_MAPE']:.3f} / "
        f"{best['improvement_probability_p95_APE']:.3f}"
    )
    print(f"report: {EXP_DIR / 'reports' / 'result_report.html'}")


if __name__ == "__main__":
    main()
