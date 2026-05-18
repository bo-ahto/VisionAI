#!/usr/bin/env python3
"""Select Track6 validation candidates from completed experiments."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RESULT_DIR = REPO / "data" / "track6" / "results"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E006_validation_candidate_selection.md"
RESULT_JSON = RESULT_DIR / "t6_e006_validation_candidate_selection.json"


def read_metrics(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def render(result: dict[str, Any]) -> str:
    warm = result["selected"]["warm"]
    cold_median = result["selected"]["cold_median"]
    cold_tail = result["selected"]["cold_tail"]
    lines = [
        "# T6-E006 validation 기준 후보 선정",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H6`",
        "- 상태: 부분 검증",
        "- 목적: validation 결과만 보고 test에 올릴 Warm/Cold 후보를 고정",
        "- 사용 스크립트: `scripts/track6/run_t6_e006_select_validation_candidates.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        "",
        "## 1. 후보 선정 원칙",
        "",
        "- test 결과를 보기 전에 validation 결과만 사용해 후보를 고정",
        "- Warm과 Cold는 같은 후보로 묶지 않고 분리 선정",
        "- Cold는 대표 오차 후보와 큰 오차 위험 후보를 분리",
        "- 운영에서 만들 수 없는 피처는 후보에서 제외",
        "",
        "## 2. 선정 후보",
        "",
        "| 구분 | 모델 | 피처셋 | validation median APE | validation p95 APE | 선정 이유 |",
        "|---|---|---|---:|---:|---|",
        f"| Warm | `{warm['model']}` | `{warm['feature_set']}` | `{warm['median_ape']:.4f}` | `{warm['p95_ape']:.4f}` | Warm median APE 최저 |",
        f"| Cold 대표 오차 | `{cold_median['model']}` | `{cold_median['feature_set']}` | `{cold_median['median_ape']:.4f}` | `{cold_median['p95_ape']:.4f}` | Cold median APE 최저 |",
        f"| Cold 큰 오차 위험 | `{cold_tail['model']}` | `{cold_tail['feature_set']}` | `{cold_tail['median_ape']:.4f}` | `{cold_tail['p95_ape']:.4f}` | Cold p95 APE 최저 |",
        "",
        "## 3. 해석",
        "",
        "- Warm은 작가 식별값을 포함한 CatBoost가 유지 후보",
        "- Warm 피처는 `medium_category + size_bucket` 조합을 포함할 때 median APE가 가장 낮음",
        "- Cold는 대표값 기준으로 단순한 구조 피처가 가장 안정적",
        "- Cold의 큰 오차를 줄이는 목적이면 Huber + `size_bucket/shape_bucket` 후보가 더 적합",
        "",
        "## 4. 다음 단계",
        "",
        "- T6-E007에서 위 후보만 test 데이터에 적용",
        "- test 결과가 validation과 같은 방향인지 확인",
        "- test에서 급락하면 해당 후보는 최종 운영 후보에서 제외하거나 보류",
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
    marker = "| 2026-05-18 | T6-E005 |"
    path.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def update_docs(result: dict[str, Any]) -> None:
    warm = result["selected"]["warm"]
    cold_median = result["selected"]["cold_median"]
    cold_tail = result["selected"]["cold_tail"]

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    row = (
        "| T6-H6 | T6-G6 | 최종 후보는 validation뿐 아니라 test에서도 같은 방향의 성능을 보여야 한다 | "
        "validation에서 고른 후보만 test에 적용 | Track6 name-corrected split | 최종 후보 피처 | validation 성능 | test 성능 급락 없음 | "
        f"부분 검증 | validation 후보 선정 완료 | Warm `{warm['feature_set']}` `{warm['median_ape']:.4f}`, "
        f"Cold median `{cold_median['feature_set']}` `{cold_median['median_ape']:.4f}`, Cold p95 `{cold_tail['feature_set']}` `{cold_tail['p95_ape']:.4f}` | T6-E006 | T6-E007 test 확인 필요 |"
    )
    replace_row(hypo, "| T6-H6 |", row)

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    row = (
        f"| {result['created_at']} | T6-E006 | T6-H6 | 부분 검증 | Track6 name-corrected split | "
        "후보 선정 로직 | validation 후보 피처 | "
        f"Warm 후보 `{warm['median_ape']:.4f}` (`{warm['feature_set']}`) | "
        f"Cold 후보 median `{cold_median['median_ape']:.4f}`, p95 `{cold_tail['p95_ape']:.4f}` | "
        "test 전 후보 고정 | [기록](../experiments/2026-05-18_T6-E006_validation_candidate_selection.md) |"
    )
    replace_row(results, "| 2026-05-18 | T6-E006 |", row)

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    row = "| 2026-05-18 | T6-E006 | T6-H6 | 부분 검증 | validation 후보 선정 완료 | [기록](2026-05-18_T6-E006_validation_candidate_selection.md) |"
    replace_row(index, "| 2026-05-18 | T6-E006 |", row)


def main() -> None:
    combo = read_metrics(RESULT_DIR / "t6_e005_feature_combo_ablation_metrics.csv")
    warm = combo.loc[combo["split"].eq("val_warm")].sort_values(["median_ape", "p95_ape"]).iloc[0].to_dict()
    cold_median = combo.loc[combo["split"].eq("val_cold")].sort_values(["median_ape", "p95_ape"]).iloc[0].to_dict()
    cold_tail = combo.loc[combo["split"].eq("val_cold")].sort_values(["p95_ape", "median_ape"]).iloc[0].to_dict()
    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E006",
        "hypothesis_id": "T6-H6",
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "selected": {
            "warm": warm,
            "cold_median": cold_median,
            "cold_tail": cold_tail,
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps(result["selected"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
