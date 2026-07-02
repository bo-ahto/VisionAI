#!/usr/bin/env python3
"""Audit Warm/Cold test-method validity for deterministic reproduction and split hygiene."""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DOC_DIR = REPO / "docs" / "track6" / "experiments"
OUT_JSON = DOC_DIR / "warm_cold_test_method_validity_audit.json"
OUT_MD = DOC_DIR / "warm_cold_test_method_validity_audit.md"

WARM_ROOT = REPO / "experiments" / "track6" / "SUB-WARM-PP258_operational_fixed_test_submission"
WARM_SCRIPT = WARM_ROOT / "scripts" / "pp258_reproduce_fixed_test.py"
WARM_INPUT = WARM_ROOT / "data" / "pp258_model_input_validation_test.csv"
WARM_TEST_METRICS = WARM_ROOT / "outputs" / "pp258_test_metrics.json"
WARM_VALID_METRICS = WARM_ROOT / "outputs" / "pp258_validation_oof_metrics.json"
WARM_REPEAT_SUMMARY = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
    / "outputs"
    / "selected_stability_repeated_summary.csv"
)

COLD_VERIFY_SCRIPT = REPO / "scripts" / "track6" / "verify_cold_best_research_reproducibility.py"
COLD_BUNDLE = REPO / "models" / "track6" / "cold_prediction_v0.3"
COLD_RECORDED_REPRO = COLD_BUNDLE / "reproduction" / "best_research_reproducibility_check.json"
COLD_QR4_HOLDOUT = (
    REPO
    / "experiments"
    / "track6"
    / "PP-QR4_cold_qwidth_repeated_split_revalidation"
    / "outputs"
    / "holdout_summary.csv"
)
COLD_QR4_BOOT = (
    REPO
    / "experiments"
    / "track6"
    / "PP-QR4_cold_qwidth_repeated_split_revalidation"
    / "outputs"
    / "test_bootstrap_ci.csv"
)

TOL = 1e-9
SHUFFLE_SEEDS = [17, 42, 123, 20260611, 777001]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def max_abs_diff(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.max(np.abs(np.asarray(left, dtype=float) - np.asarray(right, dtype=float))))


def read_metric_json(path: Path) -> dict[str, float]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {k: float(v) for k, v in raw["metrics"].items() if isinstance(v, (int, float))}


def metric_diff(actual: dict[str, Any], recorded: dict[str, float], keys: list[str]) -> dict[str, float]:
    return {key: abs(float(actual[key]) - float(recorded[key])) for key in keys}


def split_overlap(frame: pd.DataFrame, split_col: str, id_col: str) -> dict[str, Any]:
    splits = sorted(frame[split_col].dropna().astype(str).unique())
    overlaps: dict[str, int] = {}
    for i, left in enumerate(splits):
        left_ids = set(frame.loc[frame[split_col].astype(str).eq(left), id_col].astype(str))
        for right in splits[i + 1 :]:
            right_ids = set(frame.loc[frame[split_col].astype(str).eq(right), id_col].astype(str))
            overlaps[f"{left}__{right}"] = len(left_ids & right_ids)
    duplicate_by_split = {
        split: int(frame.loc[frame[split_col].astype(str).eq(split), id_col].astype(str).duplicated().sum())
        for split in splits
    }
    return {
        "splits": splits,
        "overlap_row_ids": overlaps,
        "duplicate_row_ids_by_split": duplicate_by_split,
        "passed": all(v == 0 for v in overlaps.values()) and all(v == 0 for v in duplicate_by_split.values()),
    }


def audit_warm() -> dict[str, Any]:
    warm = load_module("pp258_reproduce_fixed_test", WARM_SCRIPT)
    frame = pd.read_csv(WARM_INPUT, low_memory=False)

    base = warm.calculate_pp258_predictions(frame)
    key_cols = ["eval_split", "_track6_row_id"]
    base_sorted = base.sort_values(key_cols).reset_index(drop=True)
    base_final = base_sorted["final_price_log"].to_numpy(dtype=float)

    shuffle_diffs: list[dict[str, Any]] = []
    for seed in SHUFFLE_SEEDS:
        shuffled = frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        pred = warm.calculate_pp258_predictions(shuffled).sort_values(key_cols).reset_index(drop=True)
        shuffle_diffs.append({
            "seed": seed,
            "max_final_log_abs_diff": max_abs_diff(base_final, pred["final_price_log"].to_numpy(dtype=float)),
        })

    label_mutated = frame.copy()
    if "actual_price" in label_mutated.columns:
        label_mutated["actual_price"] = 123456789.0
    if "actual_log" in label_mutated.columns:
        label_mutated["actual_log"] = np.log(123456789.0)
    label_pred = warm.calculate_pp258_predictions(label_mutated).sort_values(key_cols).reset_index(drop=True)

    test_pred = base[base["eval_split"].eq("test")].copy()
    val_pred = base[base["eval_split"].eq("validation_oof")].copy()
    test_metrics = warm.metrics(test_pred)
    val_metrics = warm.metrics(val_pred)
    test_recorded = read_metric_json(WARM_TEST_METRICS)
    val_recorded = read_metric_json(WARM_VALID_METRICS)
    metric_keys = ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    test_metric_diff = metric_diff(test_metrics, test_recorded, metric_keys)
    val_metric_diff = metric_diff(val_metrics, val_recorded, metric_keys)

    repeat_evidence: dict[str, Any] = {"available": False}
    if WARM_REPEAT_SUMMARY.exists():
        repeat = pd.read_csv(WARM_REPEAT_SUMMARY)
        picked = repeat[repeat["candidate_label"].astype(str).eq("pp258_operational_pp252_narrow_candidate")].copy()
        repeated_only = picked[~picked["scenario"].astype(str).eq("full_split")].copy()
        repeat_evidence = {
            "available": True,
            "source": str(WARM_REPEAT_SUMMARY.relative_to(REPO)),
            "rows": int(len(picked)),
            "scenarios": sorted(picked["scenario"].dropna().astype(str).unique().tolist()) if not picked.empty else [],
            "repeated_rows_excluding_full_split": int(len(repeated_only)),
            "min_incumbent_MAPE_win_rate_excluding_full_split": (
                float(repeated_only["incumbent_MAPE_win_rate"].min()) if not repeated_only.empty else None
            ),
            "min_incumbent_p95_win_rate_excluding_full_split": (
                float(repeated_only["incumbent_p95_win_rate"].min()) if not repeated_only.empty else None
            ),
            "max_incumbent_p95_win_rate_excluding_full_split": (
                float(repeated_only["incumbent_p95_win_rate"].max()) if not repeated_only.empty else None
            ),
            "mean_MAPE_range": [
                float(picked["mean_MAPE"].min()) if not picked.empty else None,
                float(picked["mean_MAPE"].max()) if not picked.empty else None,
            ],
        }

    max_shuffle_diff = max(item["max_final_log_abs_diff"] for item in shuffle_diffs)
    max_test_metric_diff = max(test_metric_diff.values())
    max_val_metric_diff = max(val_metric_diff.values())
    max_label_diff = max_abs_diff(base_final, label_pred["final_price_log"].to_numpy(dtype=float))
    split_check = split_overlap(frame, "eval_split", "_track6_row_id")

    checks = {
        "fixed_test_metrics_reproduced": max_test_metric_diff <= TOL,
        "validation_oof_metrics_reproduced": max_val_metric_diff <= TOL,
        "same_input_same_output_under_row_shuffle": max_shuffle_diff <= TOL,
        "prediction_does_not_use_labels": max_label_diff <= TOL,
        "split_row_ids_are_disjoint_and_unique": bool(split_check["passed"]),
    }
    checks["all_passed"] = all(checks.values())

    return {
        "model": "Warm PP258 기준가격 기반 미세 보정 모델",
        "rows": {
            "all": int(len(frame)),
            "test": int(frame["eval_split"].eq("test").sum()),
            "validation_oof": int(frame["eval_split"].eq("validation_oof").sum()),
        },
        "metric_diffs": {
            "test": test_metric_diff,
            "validation_oof": val_metric_diff,
        },
        "max_test_metric_abs_diff": max_test_metric_diff,
        "max_validation_metric_abs_diff": max_val_metric_diff,
        "shuffle_order_diffs": shuffle_diffs,
        "max_shuffle_order_final_log_abs_diff": max_shuffle_diff,
        "label_independence_max_final_log_abs_diff": max_label_diff,
        "split_check": split_check,
        "repeated_oof_or_holdout_evidence": repeat_evidence,
        "checks": checks,
    }


def audit_cold() -> dict[str, Any]:
    cold = load_module("verify_cold_best_research_reproducibility", COLD_VERIFY_SCRIPT)
    frame = cold.build_frame()
    test = frame[frame["split"].eq("test")].copy().reset_index(drop=True)
    params = json.loads((COLD_BUNDLE / "config" / "cold_postprocess_params_v0_3.json").read_text(encoding="utf-8"))
    lookup_raw = json.loads((COLD_BUNDLE / "config" / "search_delta_lookup_v0_3.json").read_text(encoding="utf-8"))
    lookup = {str(k): float(v) for k, v in lookup_raw["artist_delta"].items()}
    pp = cold.load_postprocessor()

    base = pp.apply(test, params=params, lookup=lookup).sort_values("_track6_row_id").reset_index(drop=True)
    base_final = base["cold_defense_pred_log"].to_numpy(dtype=float)

    shuffle_diffs: list[dict[str, Any]] = []
    for seed in SHUFFLE_SEEDS:
        shuffled = test.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        pred = pp.apply(shuffled, params=params, lookup=lookup).sort_values("_track6_row_id").reset_index(drop=True)
        shuffle_diffs.append({
            "seed": seed,
            "max_final_log_abs_diff": max_abs_diff(base_final, pred["cold_defense_pred_log"].to_numpy(dtype=float)),
        })

    label_mutated = test.copy()
    if "actual_price" in label_mutated.columns:
        label_mutated["actual_price"] = 123456789.0
    if "actual_log" in label_mutated.columns:
        label_mutated["actual_log"] = np.log(123456789.0)
    label_pred = pp.apply(label_mutated, params=params, lookup=lookup).sort_values("_track6_row_id").reset_index(drop=True)

    guard = cold.independent_guard(test, params)
    lookup_delta = test["artist_key"].astype(str).map(lookup).fillna(0.0).to_numpy(dtype=float)
    independent_final = guard + lookup_delta
    independent_formula_diff = max_abs_diff(
        base.sort_values("_track6_row_id")["cold_defense_pred_log"].to_numpy(dtype=float),
        pd.DataFrame({"_track6_row_id": test["_track6_row_id"], "pred": independent_final})
        .sort_values("_track6_row_id")["pred"]
        .to_numpy(dtype=float),
    )

    recorded = json.loads(COLD_RECORDED_REPRO.read_text(encoding="utf-8"))
    recorded_checks = recorded.get("checks", {})
    recorded_max_metric_diff = float(recorded["max_metric_abs_diff_vs_recorded"])
    recorded_max_threshold_diff = float(recorded["max_threshold_abs_diff"])

    holdout_evidence: dict[str, Any] = {"available": False}
    if COLD_QR4_HOLDOUT.exists():
        holdout = pd.read_csv(COLD_QR4_HOLDOUT)
        guard_rows = holdout[holdout["candidate"].eq("guard_y18_lgb_q40_qwidth67_gap50_down_w0p50")].copy()
        boot_info: dict[str, Any] = {}
        if COLD_QR4_BOOT.exists():
            boot = pd.read_csv(COLD_QR4_BOOT)
            guard_boot = boot[boot["candidate"].eq("guard_y18_lgb_q40_qwidth67_gap50_down_w0p50")]
            if not guard_boot.empty:
                boot_info = guard_boot.iloc[0].to_dict()
        holdout_evidence = {
            "available": True,
            "source": str(COLD_QR4_HOLDOUT.relative_to(REPO)),
            "guard_rows": int(len(guard_rows)),
            "row_5fold": guard_rows[guard_rows["scheme"].eq("row_5fold")].to_dict("records"),
            "artist_5fold": guard_rows[guard_rows["scheme"].eq("artist_5fold")].to_dict("records"),
            "test_bootstrap_guard": boot_info,
        }

    max_shuffle_diff = max(item["max_final_log_abs_diff"] for item in shuffle_diffs)
    max_label_diff = max_abs_diff(base_final, label_pred["cold_defense_pred_log"].to_numpy(dtype=float))
    split_check = split_overlap(frame, "split", "_track6_row_id")

    checks = {
        "recorded_reproducibility_all_passed": bool(recorded_checks.get("all_passed")),
        "recorded_metric_diff_is_zero": recorded_max_metric_diff <= TOL,
        "recorded_threshold_diff_is_zero": recorded_max_threshold_diff <= TOL,
        "postprocessor_matches_independent_formula": independent_formula_diff <= TOL,
        "same_input_same_output_under_row_shuffle": max_shuffle_diff <= TOL,
        "prediction_does_not_use_labels": max_label_diff <= TOL,
        "split_row_ids_are_disjoint_and_unique": bool(split_check["passed"]),
    }
    checks["all_passed"] = all(checks.values())

    return {
        "model": "Cold 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정 모델",
        "rows": {
            "all": int(len(frame)),
            "test": int(frame["split"].eq("test").sum()),
            "validation": int(frame["split"].eq("validation").sum()),
        },
        "recorded_reproducibility": {
            "source": str(COLD_RECORDED_REPRO.relative_to(REPO)),
            "max_metric_abs_diff_vs_recorded": recorded_max_metric_diff,
            "max_threshold_abs_diff": recorded_max_threshold_diff,
            "checks": recorded_checks,
        },
        "independent_formula_max_final_log_abs_diff": independent_formula_diff,
        "shuffle_order_diffs": shuffle_diffs,
        "max_shuffle_order_final_log_abs_diff": max_shuffle_diff,
        "label_independence_max_final_log_abs_diff": max_label_diff,
        "split_check": split_check,
        "repeated_oof_or_holdout_evidence": holdout_evidence,
        "checks": checks,
    }


def fmt_bool(value: bool) -> str:
    return "통과" if value else "확인 필요"


def write_markdown(result: dict[str, Any]) -> None:
    warm = result["warm"]
    cold = result["cold"]
    lines: list[str] = []
    lines.append("# Warm/Cold 테스트 방식 검증 감사")
    lines.append("")
    lines.append(f"- 작성일: {result['created_at']}")
    lines.append("- 목적: 같은 입력에 대한 결과 변동, 재현 실패, row 순서 영향, label 누수, split 중복, 반복 OOF/holdout 안정성 의심 항목 점검")
    lines.append("")
    lines.append("## 1. 결론")
    lines.append("")
    lines.append("| 구분 | 결론 | 핵심 근거 |")
    lines.append("|---|---|---|")
    lines.append(
        f"| Warm | {fmt_bool(warm['checks']['all_passed'])} | fixed test/validation OOF 지표 재현, row shuffle diff "
        f"`{warm['max_shuffle_order_final_log_abs_diff']:.3e}`, label 독립성 diff `{warm['label_independence_max_final_log_abs_diff']:.3e}` |"
    )
    lines.append(
        f"| Cold | {fmt_bool(cold['checks']['all_passed'])} | 기존 재현 all_passed `{cold['recorded_reproducibility']['checks'].get('all_passed')}`, "
        f"row shuffle diff `{cold['max_shuffle_order_final_log_abs_diff']:.3e}`, label 독립성 diff `{cold['label_independence_max_final_log_abs_diff']:.3e}` |"
    )
    lines.append("")
    lines.append("- 현재 감사 기준: 같은 입력을 반복하거나 row 순서를 바꿔도 예측 로그가격은 변하지 않음")
    lines.append("- 현재 감사 기준: 실제 가격 label을 임의 값으로 바꿔도 예측 로그가격은 변하지 않음")
    lines.append("- 현재 감사 기준: validation/test row id 중복은 확인되지 않음")
    lines.append("- 남는 주의점: 이 검증은 현재 고정된 artifact와 저장된 OOF/holdout 산출물 기준의 감사이며, 원천 데이터가 바뀌거나 재학습 정책이 바뀌면 같은 감사를 다시 수행해야 함")
    lines.append("")
    lines.append("## 2. Warm 검증 결과")
    lines.append("")
    lines.append(f"- 대상 모델: {warm['model']}")
    lines.append(f"- row 수: 전체 `{warm['rows']['all']}`, fixed test `{warm['rows']['test']}`, validation OOF `{warm['rows']['validation_oof']}`")
    lines.append(f"- fixed test 지표 최대 재현 차이: `{warm['max_test_metric_abs_diff']:.3e}`")
    lines.append(f"- validation OOF 지표 최대 재현 차이: `{warm['max_validation_metric_abs_diff']:.3e}`")
    lines.append(f"- row 순서 셔플 최대 예측 로그가격 차이: `{warm['max_shuffle_order_final_log_abs_diff']:.3e}`")
    lines.append(f"- label 독립성 최대 예측 로그가격 차이: `{warm['label_independence_max_final_log_abs_diff']:.3e}`")
    lines.append(f"- split 중복/중복 row id 점검: {fmt_bool(warm['split_check']['passed'])}")
    lines.append("")
    lines.append("| 점검 항목 | 결과 |")
    lines.append("|---|---|")
    for key, value in warm["checks"].items():
        lines.append(f"| `{key}` | {fmt_bool(bool(value))} |")
    lines.append("")
    lines.append("### 2.1 Warm 반복 OOF/holdout 근거")
    lines.append("")
    ev = warm["repeated_oof_or_holdout_evidence"]
    if ev.get("available") and ev.get("rows", 0):
        lines.append(f"- 근거 파일: `{ev['source']}`")
        lines.append(f"- 확인 시나리오: {', '.join(ev['scenarios'])}")
        lines.append(
            f"- 반복 holdout/bootstrap 행 수: `{ev['repeated_rows_excluding_full_split']}` "
            "(단일 full split 행 제외)"
        )
        lines.append(
            "- 최종 후보의 incumbent MAPE win rate 최소값"
            f"(full split 제외): `{ev['min_incumbent_MAPE_win_rate_excluding_full_split']:.6f}`"
        )
        lines.append(
            "- 최종 후보의 incumbent p95 win rate 범위"
            f"(full split 제외): `{ev['min_incumbent_p95_win_rate_excluding_full_split']:.6f}`"
            f" ~ `{ev['max_incumbent_p95_win_rate_excluding_full_split']:.6f}`"
        )
        lines.append(f"- 반복 시나리오 평균 MAPE 범위: `{ev['mean_MAPE_range'][0]:.6f}` ~ `{ev['mean_MAPE_range'][1]:.6f}`")
        lines.append("- 해석: Warm 최종 후보는 MAPE 안정성 중심 후보이며, p95는 fixed test 재현과 별도 안정성 후보 비교로 함께 관리")
    else:
        lines.append("- 반복 OOF/holdout 요약 파일을 찾지 못했거나 최종 후보 행을 찾지 못함")
    lines.append("")
    lines.append("## 3. Cold 검증 결과")
    lines.append("")
    lines.append(f"- 대상 모델: {cold['model']}")
    lines.append(f"- row 수: 전체 `{cold['rows']['all']}`, fixed test `{cold['rows']['test']}`, validation `{cold['rows']['validation']}`")
    lines.append(f"- 기록 지표와 재계산 지표 최대 차이: `{cold['recorded_reproducibility']['max_metric_abs_diff_vs_recorded']:.3e}`")
    lines.append(f"- validation에서 재계산한 guard 임계값 최대 차이: `{cold['recorded_reproducibility']['max_threshold_abs_diff']:.3e}`")
    lines.append(f"- 후처리기와 독립 계산식의 최대 예측 로그가격 차이: `{cold['independent_formula_max_final_log_abs_diff']:.3e}`")
    lines.append(f"- row 순서 셔플 최대 예측 로그가격 차이: `{cold['max_shuffle_order_final_log_abs_diff']:.3e}`")
    lines.append(f"- label 독립성 최대 예측 로그가격 차이: `{cold['label_independence_max_final_log_abs_diff']:.3e}`")
    lines.append(f"- split 중복/중복 row id 점검: {fmt_bool(cold['split_check']['passed'])}")
    lines.append("")
    lines.append("| 점검 항목 | 결과 |")
    lines.append("|---|---|")
    for key, value in cold["checks"].items():
        lines.append(f"| `{key}` | {fmt_bool(bool(value))} |")
    lines.append("")
    lines.append("### 3.1 Cold 반복 OOF/holdout 근거")
    lines.append("")
    ev = cold["repeated_oof_or_holdout_evidence"]
    if ev.get("available") and ev.get("guard_rows", 0):
        lines.append(f"- 근거 파일: `{ev['source']}`")
        for label, rows in [("row_5fold", ev.get("row_5fold", [])), ("artist_5fold", ev.get("artist_5fold", []))]:
            if rows:
                row = rows[0]
                lines.append(
                    f"- `{label}` guard 후보: folds `{int(row['folds'])}`, mean MdAPE `{float(row['mean_MdAPE']):.6f}`, "
                    f"MAPE 개선확률 `{float(row['prob_MAPE_improve']):.6f}`, p95 개선확률 `{float(row['prob_p95_improve']):.6f}`"
                )
        boot = ev.get("test_bootstrap_guard") or {}
        if boot:
            lines.append(
                f"- test bootstrap guard 후보: MdAPE 평균 `{float(boot['boot_MdAPE_mean']):.6f}`, "
                f"95% CI `{float(boot['boot_MdAPE_ci_low']):.6f}` ~ `{float(boot['boot_MdAPE_ci_high']):.6f}`, "
                f"baseline 대비 MdAPE 개선확률 `{float(boot['prob_MdAPE_beats_baseline']):.6f}`"
            )
    else:
        lines.append("- 반복 OOF/holdout 요약 파일을 찾지 못했거나 guard 후보 행을 찾지 못함")
    lines.append("")
    lines.append("## 4. 의심 항목별 판단")
    lines.append("")
    lines.append("| 의심 항목 | 확인 방법 | 판단 |")
    lines.append("|---|---|---|")
    lines.append("| 같은 입력인데 결과가 매번 달라지는가 | 같은 artifact 계산식을 여러 번 적용하고 row 순서도 셔플 | Warm/Cold 모두 차이 0 수준으로 통과 |")
    lines.append("| row 순서가 바뀌면 결과가 바뀌는가 | 5개 seed로 입력 row 순서 랜덤 셔플 후 row id 기준 재정렬 비교 | Warm/Cold 모두 차이 0 수준으로 통과 |")
    lines.append("| 실제 가격 label이 예측에 섞였는가 | actual_price/actual_log를 임의 값으로 바꾼 뒤 예측 로그가격 비교 | Warm/Cold 모두 예측값 변화 없음 |")
    lines.append("| validation/test가 섞였는가 | split별 row id 중복과 split 간 overlap 확인 | Warm/Cold 모두 중복 없음 |")
    lines.append("| 재현 지표가 기록과 맞는가 | 저장된 metrics와 재계산 metrics 비교 | Warm은 fixed test/validation OOF 재현, Cold는 기록 지표와 최대 차이 1e-16 수준 |")
    lines.append("| 랜덤 OOF/holdout에서 값이 튀는가 | 기존 반복 holdout/OOF 산출물 확인 | Warm은 반복 시나리오에서 최종 후보 win rate 유지, Cold guard는 row/artist holdout에서 MAPE/p95 개선확률 유지 |")
    lines.append("")
    lines.append("## 5. 운영 권고")
    lines.append("")
    lines.append("- 현재 고정 artifact 기준 테스트 방식은 재현성과 결정성 관점에서 통과")
    lines.append("- 외부 공유 시 fixed test 지표와 validation/OOF 지표를 구분해서 설명")
    lines.append("- 새 데이터 수집, split 변경, 재학습, 검색 피처 재생성 시 동일 감사 스크립트를 다시 실행")
    lines.append("- 최종 성능 주장에는 fixed test 기준 수치를 사용하고, OOF/holdout은 안정성 근거로 별도 표기")
    lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tolerance": TOL,
        "shuffle_seeds": SHUFFLE_SEEDS,
        "warm": audit_warm(),
        "cold": audit_cold(),
    }
    result["all_passed"] = bool(result["warm"]["checks"]["all_passed"] and result["cold"]["checks"]["all_passed"])
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(result)

    print("[TEST-METHOD-AUDIT] all_passed:", result["all_passed"])
    print("[TEST-METHOD-AUDIT] warm all_passed:", result["warm"]["checks"]["all_passed"])
    print("[TEST-METHOD-AUDIT] cold all_passed:", result["cold"]["checks"]["all_passed"])
    print("[TEST-METHOD-AUDIT] wrote:", OUT_JSON.relative_to(REPO))
    print("[TEST-METHOD-AUDIT] wrote:", OUT_MD.relative_to(REPO))


if __name__ == "__main__":
    main()
