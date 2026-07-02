#!/usr/bin/env python3
"""Prioritize official v0.1 artist identity and external feature reviews.

This script does not modify operational feature caches. It joins:

- artist_identity_review_queue: likely false artist splits after DB migration
- external_feature_review_queue: blocked/improvement/duplicate feature candidates
- promotion_impact_rows.csv: prediction changes from the external cache dry-run

The output is a review priority table so identity merges are resolved before
external feature cache promotion.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
IMPACT_CSV = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_external_feature_promotion_impact"
    / "promotion_impact_rows.csv"
)
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_identity_external_review_priority"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_identity_external_review_priority.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_identity_external_review_priority.md"
CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")

BLOCKED_STATUSES = {
    "needs_human_review",
    "needs_improvement",
    "needs_review",
    "auto_reject_duplicate",
}


def load_json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with sqlite3.connect(DB_PATH) as conn:
        identity = pd.read_sql_query("SELECT * FROM artist_identity_review_queue", conn)
        external = pd.read_sql_query(
            """
            SELECT artist_key, review_status, duplicate_status, improvement_status,
                   quality_score, evidence_count
            FROM external_feature_review_queue
            """,
            conn,
        )
    impact = pd.read_csv(IMPACT_CSV) if IMPACT_CSV.exists() else pd.DataFrame()
    return identity, external, impact


def external_summary(external: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if external.empty:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for artist_key, group in external.groupby("artist_key", dropna=False):
        key = str(artist_key)
        status_counts = Counter(group["review_status"].fillna("").astype(str))
        duplicate_counts = Counter(group["duplicate_status"].fillna("").astype(str))
        improvement_counts = Counter(group["improvement_status"].fillna("").astype(str))
        rows[key] = {
            "external_candidate_rows": int(len(group)),
            "external_blocked_rows": int(sum(status_counts.get(status, 0) for status in BLOCKED_STATUSES)),
            "external_approved_rows": int(status_counts.get("approved_baseline", 0) + status_counts.get("approved", 0)),
            "external_status_counts": dict(status_counts),
            "external_duplicate_counts": dict(duplicate_counts),
            "external_improvement_counts": dict(improvement_counts),
            "max_quality_score": float(pd.to_numeric(group["quality_score"], errors="coerce").fillna(0).max()),
            "max_evidence_count": int(pd.to_numeric(group["evidence_count"], errors="coerce").fillna(0).max()),
        }
    return rows


def impact_summary(impact: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if impact.empty:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for _, row in impact.iterrows():
        key = str(row.get("artist_key") or "")
        if not key:
            continue
        rows[key] = {
            "impact_action": str(row.get("action") or ""),
            "abs_price_delta_pct": float(row.get("abs_price_delta_pct") or 0.0),
            "current_external_ready": bool(row.get("current_external_ready")),
            "promoted_external_ready": bool(row.get("promoted_external_ready")),
            "coverage_loss": bool(row.get("current_external_ready")) and not bool(row.get("promoted_external_ready")),
            "current_price_krw": int(row.get("current_price_krw") or 0),
            "promoted_candidate_price_krw": int(row.get("promoted_candidate_price_krw") or 0),
        }
    return rows


def aggregate_identity_groups(identity: pd.DataFrame) -> pd.DataFrame:
    """Collapse multiple alias conflicts that point to the same artist-key set."""
    if identity.empty:
        return identity
    rows: list[dict[str, Any]] = []
    for key_set, group in identity.groupby("candidate_artist_keys_json", dropna=False):
        ordered = group.sort_values(
            ["split_loss_price_count", "combined_valid_price_count", "identity_score"],
            ascending=[False, False, False],
        )
        representative = dict(ordered.iloc[0])
        aliases = sorted(set(group["normalized_alias"].dropna().astype(str)))
        recommendations = set(group["recommendation"].dropna().astype(str))
        statuses = set(group["review_status"].dropna().astype(str))
        representative["candidate_artist_keys_json"] = key_set
        representative["normalized_alias"] = aliases[0] if aliases else representative.get("normalized_alias")
        representative["normalized_aliases_json"] = json.dumps(aliases, ensure_ascii=False)
        representative["alias_group_rows"] = int(len(group))
        for value in [
            "likely_false_split_merge_candidate",
            "possible_false_split_review",
            "identity_review_required",
            "keep_separate_until_verified",
        ]:
            if value in recommendations:
                representative["recommendation"] = value
                break
        for value in ["needs_merge_review", "needs_human_review"]:
            if value in statuses:
                representative["review_status"] = value
                break
        rows.append(representative)
    return pd.DataFrame(rows)


def priority_tier(row: dict[str, Any]) -> str:
    recommendation = row["identity_recommendation"]
    split_loss = int(row["split_loss_price_count"])
    max_delta = float(row["max_abs_price_delta_pct"])
    blocked_rows = int(row["external_blocked_rows"])
    if recommendation == "likely_false_split_merge_candidate" and (split_loss >= 10 or max_delta >= 0.05):
        return "P0_identity_merge_first"
    if recommendation == "likely_false_split_merge_candidate":
        return "P1_identity_merge_review"
    if blocked_rows > 0 or max_delta >= 0.05:
        return "P2_human_review_before_promotion"
    return "P3_keep_or_low_impact_review"


def next_action(row: dict[str, Any]) -> str:
    tier = row["priority_tier"]
    if tier == "P0_identity_merge_first":
        return "동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정"
    if tier == "P1_identity_merge_review":
        return "동일 작가 병합 검수 후 canonical artist_key dry-run"
    if tier == "P2_human_review_before_promotion":
        return "실제 동명이인/출처 충돌 여부 확인 후 외부 피처 승인 또는 보류"
    return "분리 유지 가능성이 높으므로 외부 피처 보강 대상에서 후순위 처리"


def build_priorities(identity: pd.DataFrame, external: pd.DataFrame, impact: pd.DataFrame) -> pd.DataFrame:
    identity = aggregate_identity_groups(identity)
    ext_by_key = external_summary(external)
    impact_by_key = impact_summary(impact)
    rows: list[dict[str, Any]] = []
    for _, identity_row in identity.iterrows():
        keys = load_json_list(identity_row.get("candidate_artist_keys_json"))
        ext_rows = [ext_by_key.get(key, {}) for key in keys]
        impact_rows = [impact_by_key.get(key, {}) for key in keys]
        blocked = sum(int(item.get("external_blocked_rows", 0)) for item in ext_rows)
        approved = sum(int(item.get("external_approved_rows", 0)) for item in ext_rows)
        max_delta = max([float(item.get("abs_price_delta_pct", 0.0)) for item in impact_rows] or [0.0])
        coverage_loss_keys = [key for key in keys if impact_by_key.get(key, {}).get("coverage_loss")]
        status_counts: Counter[str] = Counter()
        duplicate_counts: Counter[str] = Counter()
        improvement_counts: Counter[str] = Counter()
        for item in ext_rows:
            status_counts.update(item.get("external_status_counts", {}))
            duplicate_counts.update(item.get("external_duplicate_counts", {}))
            improvement_counts.update(item.get("external_improvement_counts", {}))
        row = {
            "normalized_alias": identity_row.get("normalized_alias"),
            "normalized_aliases_json": identity_row.get("normalized_aliases_json"),
            "alias_group_rows": int(identity_row.get("alias_group_rows") or 1),
            "canonical_artist_key": identity_row.get("canonical_artist_key"),
            "candidate_artist_keys_json": identity_row.get("candidate_artist_keys_json"),
            "identity_recommendation": identity_row.get("recommendation"),
            "identity_review_status": identity_row.get("review_status"),
            "candidate_count": int(identity_row.get("candidate_count") or 0),
            "combined_valid_price_count": int(identity_row.get("combined_valid_price_count") or 0),
            "split_loss_price_count": int(identity_row.get("split_loss_price_count") or 0),
            "distinct_birth_years_json": identity_row.get("distinct_birth_years_json"),
            "identity_score": float(identity_row.get("identity_score") or 0.0),
            "external_blocked_rows": int(blocked),
            "external_approved_rows": int(approved),
            "external_status_counts_json": json.dumps(dict(status_counts), ensure_ascii=False, sort_keys=True),
            "external_duplicate_counts_json": json.dumps(dict(duplicate_counts), ensure_ascii=False, sort_keys=True),
            "external_improvement_counts_json": json.dumps(dict(improvement_counts), ensure_ascii=False, sort_keys=True),
            "max_abs_price_delta_pct": float(max_delta),
            "coverage_loss_artist_keys_json": json.dumps(coverage_loss_keys, ensure_ascii=False),
        }
        row["priority_score"] = (
            row["split_loss_price_count"] * 2.0
            + row["external_blocked_rows"] * 0.25
            + row["max_abs_price_delta_pct"] * 100.0
            + len(coverage_loss_keys) * 3.0
        )
        row["priority_tier"] = priority_tier(row)
        row["next_action"] = next_action(row)
        rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(
        ["priority_tier", "priority_score", "split_loss_price_count"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "- 없음\n"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].head(max_rows).iterrows():
        values = [str(row.get(col, "")).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(frame: pd.DataFrame) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "identity_external_review_priority.csv"
    frame.to_csv(csv_path, index=False)
    tier_counts = frame["priority_tier"].value_counts().to_dict() if not frame.empty else {}
    payload = {
        "created_at": CREATED_AT,
        "priority_rows": int(len(frame)),
        "tier_counts": {str(k): int(v) for k, v in tier_counts.items()},
        "p0_rows": int(frame["priority_tier"].eq("P0_identity_merge_first").sum()) if not frame.empty else 0,
        "p1_rows": int(frame["priority_tier"].eq("P1_identity_merge_review").sum()) if not frame.empty else 0,
        "p2_rows": int(frame["priority_tier"].eq("P2_human_review_before_promotion").sum()) if not frame.empty else 0,
        "p3_rows": int(frame["priority_tier"].eq("P3_keep_or_low_impact_review").sum()) if not frame.empty else 0,
        "priority_unit": "unique candidate_artist_keys_json",
        "output_csv": str(csv_path.relative_to(REPO)),
    }
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    columns = [
        "priority_tier",
        "normalized_alias",
        "normalized_aliases_json",
        "canonical_artist_key",
        "candidate_artist_keys_json",
        "combined_valid_price_count",
        "split_loss_price_count",
        "external_blocked_rows",
        "max_abs_price_delta_pct",
        "distinct_birth_years_json",
        "next_action",
    ]
    md = [
        "# 공식 v0.1 작가 식별자/외부 피처 검수 우선순위",
        "",
        f"- 작성일: {CREATED_AT}",
        f"- 우선순위 row: {payload['priority_rows']:,}건",
        "- 우선순위 단위: 같은 작가키 묶음을 공유하는 alias row를 합친 고유 작가키 묶음",
        f"- 최우선 병합 검수: {payload['p0_rows']:,}건",
        "",
        "## 1. 결론",
        "",
        "- 외부 피처 승격보다 작가 식별자 병합 검수를 먼저 진행한다.",
        "- 동일 작가가 분리된 후보는 Warm 이력 수, 작가 후보 표시, 외부 피처 매핑에 동시에 영향을 준다.",
        "- 자동 병합은 하지 않으며, P0/P1 후보를 검수한 뒤 canonical artist_key 적용 dry-run을 실행한다.",
        "",
        "## 2. 우선순위 기준",
        "",
        "| 등급 | 의미 | 처리 |",
        "|---|---|---|",
        "| P0_identity_merge_first | 잘못 분리 가능성이 높고 분리 손실 또는 예측 영향이 큼 | 동일 작가 병합 여부 먼저 검수 |",
        "| P1_identity_merge_review | 잘못 분리 가능성이 높지만 영향이 상대적으로 작음 | 병합 검수 후 dry-run |",
        "| P2_human_review_before_promotion | 실제 동명이인/출처 충돌 가능성 또는 외부 피처 영향 존재 | 사람 검수 후 승격 판단 |",
        "| P3_keep_or_low_impact_review | 분리 유지 가능성이 높거나 영향 낮음 | 후순위 처리 |",
        "",
        "## 3. 상위 검수 후보",
        "",
        markdown_table(frame, columns, 30),
        "",
        "## 4. 산출물",
        "",
        f"- CSV: `{payload['output_csv']}`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ]
    DOC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    identity, external, impact = load_inputs()
    frame = build_priorities(identity, external, impact)
    payload = write_outputs(frame)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
