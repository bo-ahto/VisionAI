#!/usr/bin/env python3
"""Audit gaps between the report-selected models and raw-input service use."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DOC_DIR = REPO / "docs" / "track6" / "experiments"

WARM_PACKAGE = REPO / "experiments" / "track6" / "SUB-WARM-PP258_operational_fixed_test_submission"
COLD_V03 = REPO / "models" / "track6" / "cold_prediction_v0.3"
WARM_V01 = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational"
COLD_V02 = REPO / "models" / "track6" / "cold_prediction_v0.2_operational"
COLD_V05 = REPO / "models" / "track6" / "cold_prediction_v0.5_operational"


WARM_REQUIRED = [
    ("pp252_log", "미세 보정 전 기준 로그가격", "PP252 기준가격 생성 모델/로직"),
    ("pp252_stability_log", "안정성 우선 기준 로그가격", "안정성 후보 생성 모델/로직"),
    ("prob_hist35_pp252", "기준가 대비 실제가격 상승 방향 확률", "방향 분류 모델"),
    ("resid_huber_pp252", "Huber 잔차 보정 후보", "Huber 잔차 모델"),
    ("quantile_width", "예측 불확실성 폭", "Quantile 범위 모델"),
    ("l10_price_range_ratio", "가격 범위 비율", "Quantile 하단/상단 기반 계산"),
    ("svc_group_n", "유사작품 통계 표본 수", "유사작품 통계 DB/cache"),
    ("component_prediction_spread", "후보 모델 간 예측 차이", "Warm 후보 예측값 생성기"),
    ("confidence_tier", "신뢰도 구간", "표본 수/예측 폭/매칭 신뢰도 정책"),
    ("stable_price_band", "안정 가격대 구간", "기준가격 bucket 정책"),
]

COLD_REQUIRED = [
    ("y18_qwidth_pred_log", "검색 피처 포함 대표 로그가격", "검색 포함 LightGBM Quantile 대표 후보"),
    ("lgb_q40_pred_log", "낮은쪽 40% 지점 로그가격", "LightGBM 40분위 모델"),
    ("quantile_width_log", "예측구간폭 로그값", "LightGBM q10/q90 또는 상류 보강값"),
    ("artist_key", "작가 검색 보정 lookup key", "작가 매칭/검색 기반 식별"),
    ("search_delta_lookup", "작가별 검색 기반 보정값", "frozen lookup 또는 DB snapshot"),
]


def read_csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def exists_map(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "path": rel(path),
            "exists": path.exists(),
            "type": "dir" if path.is_dir() else "file" if path.is_file() else "missing",
        }
        for key, path in paths.items()
    }


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def build_audit() -> dict[str, Any]:
    warm_input = WARM_PACKAGE / "data" / "pp258_model_input_validation_test.csv"
    warm_config = read_json(WARM_PACKAGE / "artifacts" / "model_config.json")
    cold_policy = read_json(COLD_V03 / "config" / "cold_model_policy_v0_3.json")
    cold_sources = read_json(COLD_V03 / "reproduction" / "upstream_sources.json")

    warm_header = read_csv_header(warm_input)
    warm_available = set(warm_header)
    warm_columns = [
        {
            "column": name,
            "meaning": meaning,
            "raw_input_dependency": dependency,
            "present_in_fixed_test_package": name in warm_available,
            "raw_input_runnable_now": False,
            "required_action": "상류 feature/model adapter 구축 필요",
        }
        for name, meaning, dependency in WARM_REQUIRED
    ]
    cold_columns = [
        {
            "column": name,
            "meaning": meaning,
            "raw_input_dependency": dependency,
            "present_in_v0_3_postprocessor_or_lookup": (
                name == "search_delta_lookup"
                and (COLD_V03 / "config" / "search_delta_lookup_v0_3.json").exists()
            ),
            "raw_input_runnable_now": False,
            "required_action": "검색 포함 Quantile 상류 생성기 구축 필요"
            if name != "search_delta_lookup"
            else "DB/cache fallback 정책 연결 필요",
        }
        for name, meaning, dependency in COLD_REQUIRED
    ]

    artifacts = exists_map(
        {
            "warm_pp258_reproduce_script": WARM_PACKAGE / "scripts" / "pp258_reproduce_fixed_test.py",
            "warm_pp258_fixed_test_input": warm_input,
            "warm_v01_raw_operational_root": WARM_V01,
            "cold_v03_postprocessor": COLD_V03 / "predict" / "apply_cold_postprocess_v0_3.py",
            "cold_v03_search_delta_lookup": COLD_V03 / "config" / "search_delta_lookup_v0_3.json",
            "cold_v02_raw_operational_root": COLD_V02,
            "cold_v05_raw_operational_root_excluded": COLD_V05,
        }
    )

    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "report_reference": "docs/track6/experiments/partner_warm_cold_best_model_report.md",
        "summary": {
            "warm_report_model": "Warm 기준가격 기반 미세 보정 모델",
            "warm_package_type": warm_config.get("package_type"),
            "warm_scope_note": warm_config.get("scope_note"),
            "cold_report_model": "Cold 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정",
            "cold_status": cold_policy.get("status"),
            "cold_operational_note": cold_policy.get("operational_note"),
            "decision": "보고서 모델 raw-input 서비스 적용에는 상류 feature/model adapter와 DB/cache가 필요",
        },
        "artifacts": artifacts,
        "warm_required_columns": warm_columns,
        "cold_required_columns": cold_columns,
        "cold_upstream_sources": cold_sources,
        "implementation_order": [
            "Warm/Cold required column dependency 확정",
            "local DB/cache schema 생성",
            "Warm PP258 상류 feature/model adapter 구현",
            "Cold 검색 포함 Quantile 상류 adapter 구현",
            "공식 테스트 v0.1 API와 테스트 화면 추가",
            "fixed-test parity 및 deterministic repeat 검증",
        ],
    }


def write_markdown(audit: dict[str, Any]) -> str:
    warm_rows = [
        [
            item["column"],
            item["meaning"],
            item["raw_input_dependency"],
            "예" if item["present_in_fixed_test_package"] else "아니오",
            "아니오",
            item["required_action"],
        ]
        for item in audit["warm_required_columns"]
    ]
    cold_rows = [
        [
            item["column"],
            item["meaning"],
            item["raw_input_dependency"],
            "예" if item["present_in_v0_3_postprocessor_or_lookup"] else "일부/아니오",
            "아니오",
            item["required_action"],
        ]
        for item in audit["cold_required_columns"]
    ]
    artifact_rows = [
        [name, data["path"], "예" if data["exists"] else "아니오", data["type"]]
        for name, data in audit["artifacts"].items()
    ]
    order_rows = [[idx + 1, item] for idx, item in enumerate(audit["implementation_order"])]

    lines = [
        "# 보고서 기준 모델 raw 입력 적용 gap 감사",
        "",
        f"- 작성일: {audit['created_at']}",
        f"- 기준 문서: `{audit['report_reference']}`",
        "",
        "## 1. 요약",
        "",
        f"- Warm 기준 모델: {audit['summary']['warm_report_model']}",
        f"- Warm 패키지 유형: `{audit['summary']['warm_package_type']}`",
        f"- Warm 범위 메모: {audit['summary']['warm_scope_note']}",
        f"- Cold 기준 모델: {audit['summary']['cold_report_model']}",
        f"- Cold 상태: `{audit['summary']['cold_status']}`",
        f"- Cold 운영 메모: {audit['summary']['cold_operational_note']}",
        f"- 판단: {audit['summary']['decision']}",
        "",
        "## 2. 현재 아티팩트 확인",
        "",
        table(["항목", "경로", "존재", "유형"], artifact_rows),
        "",
        "## 3. Warm required column gap",
        "",
        table(["컬럼", "의미", "raw 입력 의존 요소", "fixed-test 패키지 존재", "raw 실행 가능", "필요 작업"], warm_rows),
        "",
        "## 4. Cold required column gap",
        "",
        table(["컬럼", "의미", "raw 입력 의존 요소", "v0.3 현재 보유", "raw 실행 가능", "필요 작업"], cold_rows),
        "",
        "## 5. 구현 순서",
        "",
        table(["순서", "작업"], order_rows),
        "",
        "## 6. 결론",
        "",
        "- 보고서 기준 모델은 재현 가능하지만, 현재 상태 그대로 raw 입력 서비스에 붙일 수는 없음",
        "- Warm은 PP258 입력 컬럼을 만드는 상류 adapter가 필요",
        "- Cold는 검색 포함 Quantile 기준 예측을 만드는 상류 adapter가 필요",
        "- DB/cache는 선택이 아니라 운영 적용을 위한 필수 기반",
        "- 다음 구현은 local DB/cache schema와 adapter skeleton부터 진행하는 것이 맞음",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    audit = build_audit()
    json_path = DOC_DIR / "report_model_raw_input_gap_audit.json"
    md_path = DOC_DIR / "report_model_raw_input_gap_audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(write_markdown(audit), encoding="utf-8")
    print(f"wrote {rel(json_path)}")
    print(f"wrote {rel(md_path)}")


if __name__ == "__main__":
    main()
