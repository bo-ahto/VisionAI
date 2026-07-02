#!/usr/bin/env python3
"""Audit the official v0.1 external feature review promotion gate.

This is a dry-run guard.  It verifies that only approved candidates can be
promoted from the review queue to operational feature caches.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_feature_review_gate_audit"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_feature_review_gate_audit.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_feature_review_gate_audit.md"

APPROVED_QUEUE_STATUSES = {"approved_baseline"}
APPROVED_DECISIONS = {"approved"}
BLOCKED_QUEUE_STATUSES = {
    "needs_improvement",
    "needs_human_review",
    "needs_review",
    "auto_reject_duplicate",
    "rejected",
}
BLOCKED_DUPLICATE_STATUSES = {
    "same_artist_duplicate_url",
    "cross_artist_duplicate_url",
    "artist_name_conflict",
}
MIN_APPROVED_QUALITY_SCORE = 0.20


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_table(conn: sqlite3.Connection, table: str) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    if not exists:
        raise RuntimeError(f"required table not found: {table}")


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in row.keys()} for row in rows]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "review_candidate_id",
        "candidate_type",
        "artist_key",
        "artist_name_ko",
        "artist_name_en",
        "source_system",
        "source_record_id",
        "duplicate_status",
        "improvement_status",
        "quality_score",
        "evidence_count",
        "review_status",
        "approval_source",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    status_counts = payload["review_status_counts"]
    duplicate_counts = payload["duplicate_status_counts"]
    violations = payload["violations"]
    lines = [
        "# 공식 v0.1 외부 피처 승격 gate 감사",
        "",
        f"- 작성일: {payload['created_at']}",
        f"- gate 통과 여부: `{payload['gate_pass']}`",
        f"- 승격 dry-run 후보 수: {payload['promotion_candidate_count']:,}건",
        f"- 승격 차단 후보 수: {payload['blocked_candidate_count']:,}건",
        "",
        "## 1. 결론",
        "",
    ]
    if payload["gate_pass"]:
        lines.extend(
            [
                "- 승인 후보만 승격 대상으로 선별됐다.",
                "- 중복 후보, 동명이인 충돌 후보, 추가 수집 필요 후보는 승격 대상에 포함되지 않았다.",
                "- 이 감사는 cache를 수정하지 않는 dry-run 검증이다.",
            ]
        )
    else:
        lines.extend(
            [
                "- gate 위반 후보가 발견됐다.",
                "- 위반 후보를 반려하거나 상태를 수정하기 전까지 feature cache 승격을 진행하지 않는다.",
            ]
        )
    lines.extend(
        [
            "",
            "## 2. 검수 상태별 수량",
            "",
            "| 상태 | 건수 |",
            "|---|---:|",
        ]
    )
    for status, count in status_counts.items():
        lines.append(f"| `{status}` | {count:,} |")
    lines.extend(
        [
            "",
            "## 3. 중복 상태별 수량",
            "",
            "| 상태 | 건수 |",
            "|---|---:|",
        ]
    )
    for status, count in duplicate_counts.items():
        lines.append(f"| `{status}` | {count:,} |")
    lines.extend(
        [
            "",
            "## 4. 승격 규칙",
            "",
            "- `review_status = approved_baseline` 후보만 자동 승격 가능",
            "- 검수 결정 테이블에서 `decision = approved`가 된 후보만 추가 승격 가능",
            "- `same_artist_duplicate_url`, `cross_artist_duplicate_url`, `artist_name_conflict` 후보는 승격 불가",
            f"- 승인 후보의 최소 품질 점수 기준: `{MIN_APPROVED_QUALITY_SCORE}` 이상",
            "- 이 스크립트는 승인 후보 목록만 생성하고 운영 cache는 수정하지 않음",
            "",
            "## 5. 위반 내역",
            "",
        ]
    )
    if violations:
        lines.extend(["| 유형 | 건수 |", "|---|---:|"])
        for key, value in violations.items():
            lines.append(f"| `{key}` | {value:,} |")
    else:
        lines.append("- 위반 없음")
    lines.extend(
        [
            "",
            "## 6. 산출물",
            "",
            f"- 승격 dry-run CSV: `{payload['promotion_candidates_csv']}`",
            f"- 감사 JSON: `{payload['audit_json']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_table(conn, "external_feature_review_queue")
    ensure_table(conn, "external_feature_review_decisions")

    queue_rows = rows_to_dicts(conn.execute("SELECT * FROM external_feature_review_queue").fetchall())
    decision_rows = rows_to_dicts(conn.execute("SELECT * FROM external_feature_review_decisions").fetchall())

    approved_by_decision = {
        row["review_candidate_id"]
        for row in decision_rows
        if str(row.get("decision") or "").lower() in APPROVED_DECISIONS
    }
    promotion_candidates: list[dict[str, Any]] = []
    blocked_count = 0
    violations = {
        "blocked_status_in_promotion": 0,
        "duplicate_status_in_promotion": 0,
        "low_quality_in_promotion": 0,
    }
    status_counts: dict[str, int] = {}
    duplicate_counts: dict[str, int] = {}

    for row in queue_rows:
        review_status = str(row.get("review_status") or "")
        duplicate_status = str(row.get("duplicate_status") or "")
        status_counts[review_status] = status_counts.get(review_status, 0) + 1
        duplicate_counts[duplicate_status] = duplicate_counts.get(duplicate_status, 0) + 1

        approval_source = ""
        if review_status in APPROVED_QUEUE_STATUSES:
            approval_source = "queue_status"
        elif row["review_candidate_id"] in approved_by_decision:
            approval_source = "review_decision"

        if not approval_source:
            blocked_count += 1
            continue

        out = dict(row)
        out["approval_source"] = approval_source
        promotion_candidates.append(out)

        if review_status in BLOCKED_QUEUE_STATUSES:
            violations["blocked_status_in_promotion"] += 1
        if duplicate_status in BLOCKED_DUPLICATE_STATUSES:
            violations["duplicate_status_in_promotion"] += 1
        if float(row.get("quality_score") or 0.0) < MIN_APPROVED_QUALITY_SCORE:
            violations["low_quality_in_promotion"] += 1

    violations = {key: value for key, value in violations.items() if value > 0}
    promotion_csv = OUT_DIR / "promotion_candidates_dry_run.csv"
    write_csv(promotion_csv, promotion_candidates)

    payload = {
        "created_at": now_iso(),
        "db_path": str(DB_PATH.relative_to(REPO)),
        "gate_pass": not violations,
        "promotion_candidate_count": len(promotion_candidates),
        "blocked_candidate_count": blocked_count,
        "review_status_counts": dict(sorted(status_counts.items())),
        "duplicate_status_counts": dict(sorted(duplicate_counts.items())),
        "violations": violations,
        "promotion_candidates_csv": str(promotion_csv.relative_to(REPO)),
        "audit_json": str(DOC_JSON.relative_to(REPO)),
    }
    write_json(DOC_JSON, payload)
    write_md(DOC_MD, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
