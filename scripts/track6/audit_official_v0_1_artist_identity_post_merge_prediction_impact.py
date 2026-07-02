#!/usr/bin/env python3
"""Audit prediction impact of the post-merge cache rebuild shadow DB.

The official service stores prediction_events on estimate calls, so this script
copies both the current operational DB and the rebuilt shadow DB before running
the service. The operational DB is never modified.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SRC_DIR = REPO / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from visionai.price_engine.api.official_v0_1_schemas import (  # noqa: E402
    ArtistInput,
    ArtworkInput,
    Dimensions,
    MediumInput,
    PriceEstimateOptions,
    PriceEstimateRequest,
)
from visionai.price_engine.api.official_v0_1_service import OfficialV01Service  # noqa: E402


SOURCE_DB = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
REBUILT_SHADOW_DB = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild"
    / "price_prediction_v0_1_post_merge_cache_rebuild_shadow.sqlite"
)
COMPONENTS_CSV = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_artist_identity_merge_dry_run"
    / "artist_identity_merge_components_dry_run.csv"
)
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_artist_identity_post_merge_prediction_impact"
BEFORE_AUDIT_DB = OUT_DIR / "before_prediction_impact_audit.sqlite"
AFTER_AUDIT_DB = OUT_DIR / "after_prediction_impact_audit.sqlite"
IMPACT_CSV = OUT_DIR / "artist_identity_post_merge_prediction_impact.csv"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_post_merge_prediction_impact.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_post_merge_prediction_impact.md"
CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")


def load_json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def copy_audit_dbs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_DB.exists():
        raise FileNotFoundError(SOURCE_DB)
    if not REBUILT_SHADOW_DB.exists():
        raise FileNotFoundError(REBUILT_SHADOW_DB)
    for src, dst in [(SOURCE_DB, BEFORE_AUDIT_DB), (REBUILT_SHADOW_DB, AFTER_AUDIT_DB)]:
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)


def select_sample_artwork(conn: sqlite3.Connection, keys: list[str]) -> sqlite3.Row | None:
    placeholders = ",".join("?" for _ in keys)
    return conn.execute(
        f"""
        SELECT source_artwork_id, title, artist_name_ko, price_krw,
               width_cm, height_cm, depth_cm, medium_category, support_category
        FROM artwork_price_observations
        WHERE artist_key IN ({placeholders})
          AND width_cm IS NOT NULL
          AND height_cm IS NOT NULL
          AND width_cm > 0
          AND height_cm > 0
          AND medium_category IS NOT NULL
          AND support_category IS NOT NULL
          AND price_krw IS NOT NULL
        ORDER BY price_krw DESC
        LIMIT 1
        """,
        tuple(keys),
    ).fetchone()


def request_from_row(row: sqlite3.Row, artist: ArtistInput) -> PriceEstimateRequest:
    return PriceEstimateRequest(
        artwork=ArtworkInput(
            title=row["title"],
            artist=artist,
            dimensions=Dimensions(
                width_cm=float(row["width_cm"]),
                height_cm=float(row["height_cm"]),
                depth_cm=float(row["depth_cm"]) if row["depth_cm"] is not None else None,
            ),
            medium=MediumInput(
                medium_category=row["medium_category"],
                support_category=row["support_category"],
            ),
            source_artwork_id=row["source_artwork_id"],
        ),
        options=PriceEstimateOptions(
            include_comparable_samples=False,
            include_calculation_steps=True,
            max_comparable_samples=0,
        ),
    )


def pct_delta(before: int | None, after: int | None) -> float | None:
    if before is None or after is None or before == 0:
        return None
    return float(after - before) / float(before)


def estimate_pair(
    before_service: OfficialV01Service,
    after_service: OfficialV01Service,
    sample: sqlite3.Row,
    artist: ArtistInput,
    request_prefix: str,
) -> tuple[Any, Any]:
    request = request_from_row(sample, artist)
    before = before_service.estimate_price(f"{request_prefix}_before", request)
    after = after_service.estimate_price(f"{request_prefix}_after", request)
    return before, after


def basis(response: Any) -> dict[str, Any]:
    return {
        "route": response.route,
        "price_krw": response.prediction.price_krw,
        "same_artist_training_price_count": response.routing.same_artist_training_price_count,
        "similar_group_level": response.basis.similar_group_level,
        "similar_sample_count": response.basis.similar_sample_count,
        "confidence_level": response.prediction.confidence.level,
        "confidence_score": response.prediction.confidence.score,
    }


def run_audit() -> tuple[pd.DataFrame, dict[str, Any]]:
    copy_audit_dbs()
    components = pd.read_csv(COMPONENTS_CSV)
    before_service = OfficialV01Service(db_path=BEFORE_AUDIT_DB)
    after_service = OfficialV01Service(db_path=AFTER_AUDIT_DB)
    rows: list[dict[str, Any]] = []
    with sqlite3.connect(BEFORE_AUDIT_DB) as conn:
        conn.row_factory = sqlite3.Row
        for _, component in components.iterrows():
            keys = load_json_list(component.get("component_artist_keys_json"))
            aliases = load_json_list(component.get("aliases_for_review_json"))
            canonical = str(component.get("canonical_artist_key"))
            sample = select_sample_artwork(conn, keys)
            if not sample or not aliases:
                continue
            alias = aliases[0]
            before_resolve = before_service.resolve_artist(f"resolve_before_{component.get('component_id')}", ArtistInput(name_ko=alias))
            after_resolve = after_service.resolve_artist(f"resolve_after_{component.get('component_id')}", ArtistInput(name_ko=alias))
            alias_before, alias_after = estimate_pair(
                before_service,
                after_service,
                sample,
                ArtistInput(name_ko=alias),
                f"alias_{component.get('component_id')}",
            )
            direct_before, direct_after = estimate_pair(
                before_service,
                after_service,
                sample,
                ArtistInput(selected_artist_key=canonical, name_ko=alias),
                f"direct_{component.get('component_id')}",
            )
            alias_before_basis = basis(alias_before)
            alias_after_basis = basis(alias_after)
            direct_before_basis = basis(direct_before)
            direct_after_basis = basis(direct_after)
            rows.append(
                {
                    "component_id": component.get("component_id"),
                    "canonical_artist_key": canonical,
                    "aliases_for_review_json": json.dumps(aliases, ensure_ascii=False),
                    "component_artist_keys_json": json.dumps(keys, ensure_ascii=False),
                    "sample_artwork_id": sample["source_artwork_id"],
                    "sample_price_krw": sample["price_krw"],
                    "sample_medium": sample["medium_category"],
                    "sample_support": sample["support_category"],
                    "before_resolve_candidate_count": len(before_resolve.candidates),
                    "after_resolve_candidate_count": len(after_resolve.candidates),
                    "before_resolve_requires_selection": before_resolve.requires_selection,
                    "after_resolve_requires_selection": after_resolve.requires_selection,
                    "before_resolve_resolved": before_resolve.resolved,
                    "after_resolve_resolved": after_resolve.resolved,
                    "alias_before_route": alias_before_basis["route"],
                    "alias_after_route": alias_after_basis["route"],
                    "alias_before_price_krw": alias_before_basis["price_krw"],
                    "alias_after_price_krw": alias_after_basis["price_krw"],
                    "alias_price_delta_pct": pct_delta(alias_before_basis["price_krw"], alias_after_basis["price_krw"]),
                    "direct_before_route": direct_before_basis["route"],
                    "direct_after_route": direct_after_basis["route"],
                    "direct_before_price_krw": direct_before_basis["price_krw"],
                    "direct_after_price_krw": direct_after_basis["price_krw"],
                    "direct_price_delta_pct": pct_delta(direct_before_basis["price_krw"], direct_after_basis["price_krw"]),
                    "direct_before_same_artist_training_price_count": direct_before_basis["same_artist_training_price_count"],
                    "direct_after_same_artist_training_price_count": direct_after_basis["same_artist_training_price_count"],
                    "direct_before_similar_group_level": direct_before_basis["similar_group_level"],
                    "direct_after_similar_group_level": direct_after_basis["similar_group_level"],
                    "direct_before_similar_sample_count": direct_before_basis["similar_sample_count"],
                    "direct_after_similar_sample_count": direct_after_basis["similar_sample_count"],
                    "direct_before_confidence_level": direct_before_basis["confidence_level"],
                    "direct_after_confidence_level": direct_after_basis["confidence_level"],
                    "direct_before_confidence_score": direct_before_basis["confidence_score"],
                    "direct_after_confidence_score": direct_after_basis["confidence_score"],
                }
            )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["direct_abs_price_delta_pct"] = pd.to_numeric(frame["direct_price_delta_pct"], errors="coerce").abs()
        frame["alias_abs_price_delta_pct"] = pd.to_numeric(frame["alias_price_delta_pct"], errors="coerce").abs()
    payload = summary_from_frame(frame)
    return frame, payload


def summary_from_frame(frame: pd.DataFrame) -> dict[str, Any]:
    if not frame.empty:
        if "direct_abs_price_delta_pct" not in frame.columns:
            frame["direct_abs_price_delta_pct"] = pd.to_numeric(frame["direct_price_delta_pct"], errors="coerce").abs()
        if "alias_abs_price_delta_pct" not in frame.columns:
            frame["alias_abs_price_delta_pct"] = pd.to_numeric(frame["alias_price_delta_pct"], errors="coerce").abs()
    high_impact_mask = (
        pd.to_numeric(frame["direct_abs_price_delta_pct"], errors="coerce").fillna(0) >= 0.50
        if not frame.empty
        else pd.Series(dtype=bool)
    )
    direct_route_changed_mask = (
        frame["direct_before_route"].astype(str).ne(frame["direct_after_route"].astype(str))
        if not frame.empty
        else pd.Series(dtype=bool)
    )
    direct_cold_to_warm_mask = (
        frame["direct_before_route"].astype(str).eq("cold") & frame["direct_after_route"].astype(str).eq("warm")
        if not frame.empty
        else pd.Series(dtype=bool)
    )
    return {
        "created_at": CREATED_AT,
        "evaluated_components": int(len(frame)),
        "alias_candidate_count_reduced": int((frame["after_resolve_candidate_count"] < frame["before_resolve_candidate_count"]).sum()) if not frame.empty else 0,
        "alias_resolved_after_merge": int(frame["after_resolve_resolved"].sum()) if not frame.empty else 0,
        "alias_review_required_before": int(frame["before_resolve_requires_selection"].sum()) if not frame.empty else 0,
        "alias_review_required_after": int(frame["after_resolve_requires_selection"].sum()) if not frame.empty else 0,
        "alias_route_review_to_warm": int(((frame["alias_before_route"] == "review_required") & (frame["alias_after_route"] == "warm")).sum()) if not frame.empty else 0,
        "direct_route_changed_rows": int(direct_route_changed_mask.sum()) if not frame.empty else 0,
        "direct_cold_to_warm_rows": int(direct_cold_to_warm_mask.sum()) if not frame.empty else 0,
        "direct_price_changed_rows": int((pd.to_numeric(frame["direct_price_delta_pct"], errors="coerce").fillna(0).abs() > 1e-9).sum()) if not frame.empty else 0,
        "direct_high_impact_rows_abs_delta_gte_50pct": int(high_impact_mask.sum()) if not frame.empty else 0,
        "direct_price_delta_mean_abs_pct": float(frame["direct_abs_price_delta_pct"].mean()) if not frame.empty else 0.0,
        "direct_price_delta_p95_abs_pct": float(frame["direct_abs_price_delta_pct"].quantile(0.95)) if not frame.empty else 0.0,
        "direct_sample_count_increased_rows": int((frame["direct_after_similar_sample_count"].fillna(0) > frame["direct_before_similar_sample_count"].fillna(0)).sum()) if not frame.empty else 0,
        "operational_db_modified": False,
        "before_audit_db": str(BEFORE_AUDIT_DB.relative_to(REPO)),
        "after_audit_db": str(AFTER_AUDIT_DB.relative_to(REPO)),
    }


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "- 없음\n"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].head(max_rows).iterrows():
        values = [str(row.get(col, "")).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(frame: pd.DataFrame, payload: dict[str, Any]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(IMPACT_CSV, index=False)
    payload = {
        **payload,
        "impact_csv": str(IMPACT_CSV.relative_to(REPO)),
    }
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    sorted_frame = frame.sort_values("direct_abs_price_delta_pct", ascending=False) if not frame.empty else frame
    md = [
        "# 공식 v0.1 작가 병합 후 예측 영향 감사",
        "",
        f"- 작성일: {CREATED_AT}",
        "- 운영 DB 수정 여부: 수정하지 않음",
        f"- 평가 component: {payload['evaluated_components']:,}건",
        f"- 병합 후 alias 단일 resolve: {payload['alias_resolved_after_merge']:,}건",
        f"- alias review_required: {payload['alias_review_required_before']:,} -> {payload['alias_review_required_after']:,}",
        f"- direct 가격 변동 row: {payload['direct_price_changed_rows']:,}건",
        f"- direct route 변경 row: {payload['direct_route_changed_rows']:,}건",
        f"- direct cold -> warm row: {payload['direct_cold_to_warm_rows']:,}건",
        f"- direct 고영향 row(절대 변화율 50% 이상): {payload['direct_high_impact_rows_abs_delta_gte_50pct']:,}건",
        f"- direct 가격 평균 절대 변화율: {payload['direct_price_delta_mean_abs_pct']:.4%}",
        f"- direct 가격 p95 절대 변화율: {payload['direct_price_delta_p95_abs_pct']:.4%}",
        "",
        "## 1. 결론",
        "",
        "- 병합 전/후 DB를 감사용 복사본으로 만들어 같은 입력의 resolve와 가격 예측 변화를 비교했다.",
        "- 운영 DB에는 예측 이벤트를 남기지 않았다.",
        "- 병합 후 작가명 기반 후보 중복이 제거되어, 병합 후보 component는 단일 작가 후보로 resolve된다.",
        "- 가격 변동은 병합으로 같은 작가 이력과 유사작품 통계가 합쳐지기 때문에 발생한다.",
        "- 가격 변화가 큰 component는 자동 적용하지 않고 별도 보류 검수 대상으로 둔다.",
        "",
        "## 2. 가격 변동 상위",
        "",
        markdown_table(
            sorted_frame,
            [
                "component_id",
                "canonical_artist_key",
                "aliases_for_review_json",
                "direct_before_price_krw",
                "direct_after_price_krw",
                "direct_price_delta_pct",
                "direct_before_route",
                "direct_after_route",
                "direct_before_similar_sample_count",
                "direct_after_similar_sample_count",
                "direct_before_confidence_score",
                "direct_after_confidence_score",
            ],
            30,
        ),
        "",
        "## 3. 산출물",
        "",
        f"- Impact CSV: `{payload['impact_csv']}`",
        f"- Before audit DB: `{payload['before_audit_db']}`",
        f"- After audit DB: `{payload['after_audit_db']}`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ]
    DOC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse the existing impact CSV and only refresh summary documents.",
    )
    args = parser.parse_args()
    if args.reuse_existing:
        if not IMPACT_CSV.exists():
            raise FileNotFoundError(IMPACT_CSV)
        frame = pd.read_csv(IMPACT_CSV)
        payload = summary_from_frame(frame)
    else:
        frame, payload = run_audit()
    payload = write_outputs(frame, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
