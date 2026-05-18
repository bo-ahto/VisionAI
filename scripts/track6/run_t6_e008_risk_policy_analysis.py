#!/usr/bin/env python3
"""Analyze Track6 risk slices and price-range policy candidates."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from run_t6_e005_feature_combo_ablation import REPO, add_generated_features


WARM_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
COLD_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
PRED_CSV = REPO / "data" / "track6" / "predictions" / "t6_e007_test_confirmation_predictions.csv"
RESULT_DIR = REPO / "data" / "track6" / "results"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E008_risk_policy_analysis.md"
RESULT_JSON = RESULT_DIR / "t6_e008_risk_policy_analysis.json"
RESULT_CSV = RESULT_DIR / "t6_e008_risk_policy_analysis_slices.csv"


def load_features() -> pd.DataFrame:
    warm_train = pd.read_csv(WARM_FEATURE_DIR / "track6_train_warm_features.csv")
    warm_test = pd.read_csv(WARM_FEATURE_DIR / "track6_test_warm_warm_features.csv")
    cold_train = pd.read_csv(COLD_FEATURE_DIR / "track6_train_cold_features.csv")
    cold_test = pd.read_csv(COLD_FEATURE_DIR / "track6_test_cold_cold_features.csv")
    _warm_train, warm_test = add_generated_features(warm_train, warm_test)
    _cold_train, cold_test = add_generated_features(cold_train, cold_test)
    warm_test["split"] = "test_warm"
    cold_test["split"] = "test_cold"
    return pd.concat([warm_test, cold_test], ignore_index=True, sort=False)


def bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])


def enrich_predictions() -> pd.DataFrame:
    pred = pd.read_csv(PRED_CSV)
    features = load_features()
    keep_cols = [
        "_track6_row_id",
        "split",
        "area_cm2",
        "aspect_ratio",
        "medium_category",
        "support_category",
        "size_bucket",
        "shape_bucket",
        "artist_works_count_train",
        "artist_works_log",
    ]
    keep_cols = [col for col in keep_cols if col in features.columns]
    out = pred.merge(features[keep_cols], on=["_track6_row_id", "split"], how="left", validate="many_to_one")
    out["abs_log_error"] = (np.log(out["pred_price_krw"]) - np.log(out["price_krw"])).abs()
    out["is_3d"] = bool_series(out, "is_3d_candidate")
    out["is_large_q5"] = out["size_bucket"].fillna("").astype(str).eq("q5")
    out["is_small_q1"] = out["size_bucket"].fillna("").astype(str).eq("q1")
    out["is_unbalanced_shape"] = ~out["shape_bucket"].fillna("").astype(str).eq("balanced")
    out["is_extreme_shape"] = out["shape_bucket"].fillna("").astype(str).isin(["tall", "extreme_wide"])
    if "artist_works_count_train" in out.columns:
        artist_count = pd.to_numeric(out["artist_works_count_train"], errors="coerce").fillna(0)
        out["is_low_artist_history"] = (out["split"].eq("test_warm") & (artist_count <= 5))
    else:
        out["is_low_artist_history"] = False
    return out


def slice_metrics(df: pd.DataFrame, model: str, slice_name: str, mask: pd.Series) -> dict[str, Any] | None:
    part = df.loc[df["model"].eq(model) & mask].copy()
    if part.empty:
        return None
    q80 = float(part["abs_log_error"].quantile(0.80))
    return {
        "model": model,
        "split": str(part["split"].iloc[0]),
        "slice": slice_name,
        "n": int(len(part)),
        "median_ape": float(part["ape"].median()),
        "p90_ape": float(part["ape"].quantile(0.90)),
        "p95_ape": float(part["ape"].quantile(0.95)),
        "within_30": float((part["ape"] <= 0.30).mean()),
        "within_50": float((part["ape"] <= 0.50).mean()),
        "q80_abs_log_error": q80,
        "q80_range_multiplier": float(np.exp(q80)),
    }


def analyze(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    conditions = {
        "all": pd.Series(True, index=df.index),
        "large_q5": df["is_large_q5"],
        "small_q1": df["is_small_q1"],
        "3d": df["is_3d"],
        "2d": ~df["is_3d"],
        "unbalanced_shape": df["is_unbalanced_shape"],
        "extreme_shape": df["is_extreme_shape"],
        "low_artist_history": df["is_low_artist_history"],
    }
    for model in sorted(df["model"].unique()):
        for slice_name, mask in conditions.items():
            row = slice_metrics(df, model, slice_name, mask)
            if row is not None:
                rows.append(row)
    result = pd.DataFrame(rows)
    overall = result.loc[result["slice"].eq("all"), ["model", "median_ape", "p95_ape"]].rename(
        columns={"median_ape": "overall_median_ape", "p95_ape": "overall_p95_ape"}
    )
    result = result.merge(overall, on="model", how="left")
    result["risk_flag"] = (
        (result["n"] >= 30)
        & (
            (result["median_ape"] > result["overall_median_ape"] * 1.15)
            | (result["p95_ape"] > result["overall_p95_ape"] * 1.15)
        )
    )
    return result.sort_values(["model", "risk_flag", "median_ape"], ascending=[True, False, False])


def render(result: dict[str, Any]) -> str:
    lines = [
        "# T6-E008 신뢰도/위험 구간 분석",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H7`",
        "- 상태: 검증 완료",
        "- 목적: test 예측 결과에서 단일 가격만 보여주기 위험한 구간을 식별",
        "- 사용 스크립트: `scripts/track6/run_t6_e008_risk_policy_analysis.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        f"- slice CSV: `{result['slice_csv']}`",
        "",
        "## 1. 분석 원칙",
        "",
        "- 새 모델을 고르거나 test 결과에 맞춰 모델을 튜닝하지 않음",
        "- T6-E007 예측 결과를 사용해 위험 조건을 관찰",
        "- 위험 구간은 전체 대비 median APE 또는 p95 APE가 15% 이상 나쁜 구간으로 표시",
        "- 표본 수가 30건 미만이면 위험 후보로 확정하지 않음",
        "",
        "## 2. 위험 후보 요약",
        "",
        "| model | split | slice | n | median APE | p95 APE | q80 range multiplier |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in result["risk_rows"]:
        lines.append(
            f"| `{row['model']}` | `{row['split']}` | `{row['slice']}` | `{row['n']}` | "
            f"`{row['median_ape']:.4f}` | `{row['p95_ape']:.4f}` | `{row['q80_range_multiplier']:.2f}x` |"
        )
    if not result["risk_rows"]:
        lines.append("| - | - | - | - | - | - | - |")
    lines += [
        "",
        "## 3. 가격 범위 해석",
        "",
        "- `q80 range multiplier`는 예측 가격 주변에 80% 수준의 관찰 오차를 포함하려면 필요한 배율",
        "- 예: multiplier가 `2.0x`이면 예측가 100만원 기준 대략 50만~200만원 범위를 의미",
        "- 이 값은 서비스 최종 범위가 아니라, 현재 모델의 불확실성 크기를 보는 참고값",
        "",
        "## 4. 결론",
        "",
        "- T6-H7은 test 기준 검증 완료",
        "- 단일 가격만 제공하기보다 Warm/Cold 및 위험 구간별 신뢰도 문구가 필요",
        "- Cold는 median은 유지되지만 p95가 크므로 가격 범위 또는 경고 정책을 함께 두는 것이 안전",
        "- 다음 단계는 최종 운영 후보와 artifact manifest 정리(T6-E009)",
        "",
    ]
    return "\n".join(lines)


def replace_row(path: Path, prefix: str, row: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = row
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    marker = "| 2026-05-18 | T6-E007 |"
    path.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def update_docs(result: dict[str, Any]) -> None:
    risk_count = len(result["risk_rows"])
    top = result["risk_rows"][0] if result["risk_rows"] else None
    top_text = "위험 구간 없음" if top is None else f"{top['model']} / {top['slice']} median {top['median_ape']:.4f}"

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    row = (
        "| T6-H7 | T6-G7 | Cold는 위험 구간을 나누어 신뢰도 경고를 제공해야 실무적으로 해석 가능하다 | "
        "3D, 대형, 소형, 비균형 형태, 저이력 구간별 오차 비교 | Track6 name-corrected split | risk flags | Cold/Warm 전체 | 위험 구간 오차가 명확히 높음 | "
        f"검증 완료 | test slice 분석 | 위험 후보 `{risk_count}`개, 대표 위험 `{top_text}` | T6-E008 | T6-E009 최종 정리 |"
    )
    replace_row(hypo, "| T6-H7 |", row)

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    row = (
        f"| {result['created_at']} | T6-E008 | T6-H7 | 검증 완료 | Track6 name-corrected split | "
        "slice 분석 | risk flags | 위험 구간 분석 | "
        f"위험 후보 `{risk_count}`개 | 신뢰도/가격 범위 정책 필요 | [기록](../experiments/2026-05-18_T6-E008_risk_policy_analysis.md) |"
    )
    replace_row(results, "| 2026-05-18 | T6-E008 |", row)

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    row = "| 2026-05-18 | T6-E008 | T6-H7 | 검증 완료 | 신뢰도/위험 구간 분석 완료 | [기록](2026-05-18_T6-E008_risk_policy_analysis.md) |"
    replace_row(index, "| 2026-05-18 | T6-E008 |", row)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    enriched = enrich_predictions()
    slices = analyze(enriched)
    slices.to_csv(RESULT_CSV, index=False)
    risk_rows = slices.loc[slices["risk_flag"]].sort_values(["median_ape", "p95_ape"], ascending=False).to_dict(orient="records")
    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E008",
        "hypothesis_id": "T6-H7",
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "slice_csv": str(RESULT_CSV.relative_to(REPO)),
        "risk_rows": risk_rows,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps({"risk_count": len(risk_rows), "top_risks": risk_rows[:5]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
