#!/usr/bin/env python3
"""Audit deterministic Cold feature generation for official v0.1 new inputs."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ.setdefault("MPLCONFIGDIR", str(REPO / ".cache" / "matplotlib"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")
warnings.filterwarnings("ignore", message="X does not have valid feature names")

from visionai.price_engine.api.official_v0_1_report_adapters import ReportModelProxyAdapter  # noqa: E402
from visionai.price_engine.api.official_v0_1_schemas import (  # noqa: E402
    ArtistInput,
    ArtworkInput,
    Dimensions,
    MediumInput,
    PriceEstimateRequest,
)


OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_cold_new_input_pipeline_audit"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_cold_new_input_pipeline_audit.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_cold_new_input_pipeline_audit.md"
SPLIT_TEST_COLD = REPO / "data" / "track6_split" / "track6_test_cold.csv"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def clean(value: object, default: object = None) -> object:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    return value


def request(
    *,
    artist_key: str | None,
    name_ko: str | None,
    name_en: str | None = None,
    source_artwork_id: str | None = None,
    artwork_url: str | None = None,
    title: str = "Cold pipeline audit sample",
    width_cm: float = 72.7,
    height_cm: float = 60.6,
    depth_cm: float = 0.0,
    medium_category: str = "painting",
    support_category: str = "canvas",
) -> PriceEstimateRequest:
    return PriceEstimateRequest(
        artwork=ArtworkInput(
            title=title,
            artist=ArtistInput(
                artist_key=artist_key,
                selected_artist_key=artist_key,
                name_ko=name_ko,
                name_en=name_en,
            ),
            category="Sculpture" if depth_cm > 0 else "Painting",
            dimensions=Dimensions(width_cm=width_cm, height_cm=height_cm, depth_cm=depth_cm),
            medium=MediumInput(medium_category=medium_category, support_category=support_category),
            artwork_url=artwork_url,
            source_artwork_id=source_artwork_id,
        )
    )


def fixed_test_replay_case() -> dict[str, Any]:
    source = pd.read_csv(SPLIT_TEST_COLD, low_memory=False)
    row = source[source["_track6_row_id"].eq(54557)].iloc[0]
    return {
        "case_id": "fixed_test_replay_source_id",
        "expected_mode": "row_feature_store_replay",
        "artist_key": str(row["artist_key"]),
        "request": request(
            artist_key=str(row["artist_key"]),
            name_ko=str(clean(row.get("artist_name_ko"), row["artist_key"])),
            source_artwork_id=str(row["source_artwork_id"]),
            title=str(clean(row.get("title_raw"), "Untitled")),
            width_cm=float(row["width_cm"]),
            height_cm=float(row["height_cm"]),
            depth_cm=float(clean(row.get("depth_cm"), 0.0)),
            medium_category=str(clean(row.get("medium_category"), "unknown")),
            support_category=str(clean(row.get("support_category"), "unknown")),
        ),
    }


def audit_case(adapter: ReportModelProxyAdapter, case: dict[str, Any], repeat: int = 3) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for _ in range(repeat):
        result = adapter.predict_cold(case["request"], case["artist_key"])
        output = result.output
        comparable = {
            "price_krw": result.price_krw,
            "low_krw": result.low_krw,
            "high_krw": result.high_krw,
            "confidence_tier": result.confidence_tier,
            "cold_feature_input_mode": output.get("cold_feature_input_mode"),
            "cold_feature_store_hit": output.get("cold_feature_store_hit"),
            "search_feature_pipeline_ready": output.get("search_feature_pipeline_ready"),
            "search_feature_lookup_basis": output.get("search_feature_lookup_basis"),
            "external_feature_pipeline_ready": output.get("external_feature_pipeline_ready"),
            "external_feature_lookup_basis": output.get("external_feature_lookup_basis"),
            "quantile_width_log": output.get("quantile_width_log"),
            "guard_search_final_log_price": output.get("guard_search_final_log_price"),
        }
        digest = hashlib.sha1(json.dumps(comparable, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        comparable["result_hash"] = digest
        runs.append(comparable)
    hashes = {run["result_hash"] for run in runs}
    modes = {run["cold_feature_input_mode"] for run in runs}
    return {
        "case_id": case["case_id"],
        "expected_mode": case["expected_mode"],
        "repeat": repeat,
        "deterministic": len(hashes) == 1,
        "mode_matched": modes == {case["expected_mode"]},
        "first_run": runs[0],
        "run_hashes": [run["result_hash"] for run in runs],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 공식 v0.1 Cold 신규 입력 feature pipeline 감사",
        "",
        f"- 작성일: {payload['created_at']}",
        "- 목적: feature store에 없는 신규 입력도 deterministic하게 Cold 피처를 생성하는지 확인",
        "",
        "## 1. 결론",
        "",
        f"- 전체 deterministic 통과: {'예' if payload['all_deterministic'] else '아니오'}",
        f"- 전체 feature input mode 기대값 일치: {'예' if payload['all_modes_matched'] else '아니오'}",
        "- 해석: row-level feature store가 없으면 공식 DB search snapshot, 작가 단위 전시/갤러리 cache, missing/default 순서로 피처를 생성한다.",
        "",
        "## 2. 케이스별 결과",
        "",
        "| 케이스 | 기대 모드 | 실제 모드 | deterministic | 가격 | search basis | external basis |",
        "|---|---|---|---|---:|---|---|",
    ]
    for case in payload["cases"]:
        first = case["first_run"]
        lines.append(
            f"| {case['case_id']} | {case['expected_mode']} | {first['cold_feature_input_mode']} | "
            f"{'예' if case['deterministic'] else '아니오'} | {first['price_krw']} | "
            f"{first['search_feature_lookup_basis']} | {first['external_feature_lookup_basis']} |"
        )
    lines.extend([
        "",
        "## 3. 모드 정의",
        "",
        "| 모드 | 의미 |",
        "|---|---|",
        "| `row_feature_store_replay` | `artwork_url` 또는 `source_artwork_id`가 row-level Cold feature store에 적중해 실험 입력 피처를 그대로 재사용 |",
        "| `service_search_external_cache` | 신규 입력이지만 검색 snapshot과 전시/갤러리 cache가 모두 적중 |",
        "| `service_search_cache` | 신규 입력에서 검색 snapshot만 적중 |",
        "| `service_external_cache` | 신규 입력에서 전시/갤러리 cache만 적중 |",
        "| `service_default_missing` | 신규 입력에서 검색/외부 cache가 없어 missing/default 피처로 계산 |",
        "",
        "## 4. 산출물",
        "",
        f"- JSON: `{rel(DOC_JSON)}`",
        f"- 상세 결과: `{rel(OUT_DIR / 'outputs' / 'case_results.json')}`",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.joinpath("outputs").mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    adapter = ReportModelProxyAdapter()
    cases = [
        fixed_test_replay_case(),
        {
            "case_id": "new_input_search_cache",
            "expected_mode": "service_search_external_cache",
            "artist_key": "jeong zik seong",
            "request": request(artist_key="jeong zik seong", name_ko="정직성", medium_category="painting", support_category="canvas"),
        },
        {
            "case_id": "new_input_external_cache",
            "expected_mode": "service_external_cache",
            "artist_key": "a byeol jang",
            "request": request(artist_key="a byeol jang", name_ko="장아브여르", medium_category="painting", support_category="canvas"),
        },
        {
            "case_id": "new_input_default_missing",
            "expected_mode": "service_default_missing",
            "artist_key": "new cold audit artist",
            "request": request(artist_key="new cold audit artist", name_ko="신규콜드감사작가", medium_category="painting", support_category="canvas"),
        },
    ]
    results = [audit_case(adapter, case) for case in cases]
    payload = {
        "created_at": now(),
        "service_version": "price_prediction_v0.1",
        "all_deterministic": all(case["deterministic"] for case in results),
        "all_modes_matched": all(case["mode_matched"] for case in results),
        "cases": results,
    }
    (OUT_DIR / "outputs" / "case_results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
