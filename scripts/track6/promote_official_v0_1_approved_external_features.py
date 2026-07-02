#!/usr/bin/env python3
"""Build a promoted external feature cache candidate from approved review rows.

Default mode is a dry run.  It writes a candidate CSV and a diff report, but it
does not overwrite the operational cache unless --apply is explicitly passed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
CURRENT_CACHE_PATH = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_artist_external_feature_cache.csv"
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_external_feature_promotion"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_external_feature_promotion.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_external_feature_promotion.md"

APPROVED_QUEUE_STATUSES = {"approved_baseline"}
APPROVED_DECISIONS = {"approved"}
BLOCKED_DUPLICATE_STATUSES = {
    "same_artist_duplicate_url",
    "cross_artist_duplicate_url",
    "artist_name_conflict",
}
MIN_APPROVED_QUALITY_SCORE = 0.20
IGNORE_DIFF_COLUMNS = {"feature_cache_version", "created_at"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")


def parse_payload(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def ensure_table(conn: sqlite3.Connection, table: str) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    if not exists:
        raise RuntimeError(f"required table not found: {table}")


def load_approved_decisions(conn: sqlite3.Connection) -> set[str]:
    ensure_table(conn, "external_feature_review_decisions")
    rows = conn.execute(
        """
        SELECT review_candidate_id, decision
        FROM external_feature_review_decisions
        """
    ).fetchall()
    return {
        str(row[0])
        for row in rows
        if str(row[1] or "").strip().lower() in APPROVED_DECISIONS
    }


def load_review_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    ensure_table(conn, "external_feature_review_queue")
    return conn.execute(
        """
        SELECT *
        FROM external_feature_review_queue
        WHERE candidate_type = 'artist_external_feature_cache'
        """
    ).fetchall()


def select_approved_external_rows(
    review_rows: list[sqlite3.Row],
    approved_decisions: set[str],
    *,
    min_quality_score: float,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    selected: list[dict[str, Any]] = []
    blocked = {
        "not_approved_status": 0,
        "blocked_duplicate_status": 0,
        "low_quality_score": 0,
        "missing_artist_key": 0,
        "invalid_payload": 0,
    }
    for row in review_rows:
        review_candidate_id = str(row["review_candidate_id"])
        review_status = str(row["review_status"] or "")
        duplicate_status = str(row["duplicate_status"] or "")
        quality_score = safe_float(row["quality_score"], 0.0)
        approved_by_queue = review_status in APPROVED_QUEUE_STATUSES
        approved_by_decision = review_candidate_id in approved_decisions
        if not approved_by_queue and not approved_by_decision:
            blocked["not_approved_status"] += 1
            continue
        if duplicate_status in BLOCKED_DUPLICATE_STATUSES:
            blocked["blocked_duplicate_status"] += 1
            continue
        if quality_score < min_quality_score:
            blocked["low_quality_score"] += 1
            continue

        payload = parse_payload(row["candidate_payload_json"])
        artist_key = str(payload.get("artist_key") or row["artist_key"] or "").strip()
        if not artist_key:
            blocked["missing_artist_key"] += 1
            continue
        if not payload:
            blocked["invalid_payload"] += 1
            continue
        payload["artist_key"] = artist_key
        selected.append(
            {
                "review_candidate_id": review_candidate_id,
                "approval_source": "review_decision" if approved_by_decision else "queue_status",
                "review_status": review_status,
                "duplicate_status": duplicate_status,
                "quality_score": quality_score,
                "evidence_count": int(safe_float(row["evidence_count"], 0.0)),
                "created_at": str(row["created_at"] or ""),
                "payload": payload,
            }
        )
    return selected, {key: value for key, value in blocked.items() if value > 0}


def build_candidate_frame(selected: list[dict[str, Any]], columns: list[str]) -> tuple[pd.DataFrame, int]:
    if not selected:
        return pd.DataFrame(columns=columns), 0
    ranked = sorted(
        selected,
        key=lambda row: (
            str(row["payload"].get("artist_key") or ""),
            -float(row["quality_score"]),
            -int(row["evidence_count"]),
            0 if row["approval_source"] == "review_decision" else 1,
            str(row["created_at"]),
        ),
    )
    seen: set[str] = set()
    deduped_payloads: list[dict[str, Any]] = []
    duplicate_artist_rows = 0
    created_at = now_iso()
    for row in ranked:
        payload = dict(row["payload"])
        artist_key = str(payload.get("artist_key") or "")
        if artist_key in seen:
            duplicate_artist_rows += 1
            continue
        seen.add(artist_key)
        payload["feature_cache_version"] = "official_v0_1_artist_external_feature_cache_review_promoted_candidate"
        payload["created_at"] = created_at
        deduped_payloads.append(payload)

    frame = pd.DataFrame(deduped_payloads)
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame[columns].sort_values("artist_key").reset_index(drop=True), duplicate_artist_rows


def values_equal(left: object, right: object) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    return str(left) == str(right)


def diff_frames(current: pd.DataFrame, promoted: pd.DataFrame, selected: list[dict[str, Any]]) -> tuple[pd.DataFrame, dict[str, int]]:
    current = current.copy()
    promoted = promoted.copy()
    current["artist_key"] = current["artist_key"].astype("string").fillna("")
    promoted["artist_key"] = promoted["artist_key"].astype("string").fillna("")
    selected_meta = {
        str(row["payload"].get("artist_key") or ""): row
        for row in selected
        if str(row["payload"].get("artist_key") or "")
    }
    keys = sorted(set(current["artist_key"]) | set(promoted["artist_key"]))
    current_map = {str(row["artist_key"]): row for _, row in current.iterrows()}
    promoted_map = {str(row["artist_key"]): row for _, row in promoted.iterrows()}
    diff_rows: list[dict[str, Any]] = []
    counts = {
        "kept": 0,
        "candidate_only": 0,
        "current_only": 0,
        "changed": 0,
    }
    compare_columns = [col for col in current.columns if col in promoted.columns and col not in IGNORE_DIFF_COLUMNS]
    for key in keys:
        in_current = key in current_map
        in_promoted = key in promoted_map
        meta = selected_meta.get(key, {})
        changed_columns: list[str] = []
        if in_current and in_promoted:
            for column in compare_columns:
                if not values_equal(current_map[key].get(column), promoted_map[key].get(column)):
                    changed_columns.append(column)
            action = "changed" if changed_columns else "kept"
        elif in_promoted:
            action = "candidate_only"
        else:
            action = "current_only"
        counts[action] += 1
        diff_rows.append(
            {
                "artist_key": key,
                "action": action,
                "current_present": in_current,
                "promoted_present": in_promoted,
                "changed_columns": ",".join(changed_columns),
                "review_candidate_id": meta.get("review_candidate_id"),
                "approval_source": meta.get("approval_source"),
                "quality_score": meta.get("quality_score"),
                "evidence_count": meta.get("evidence_count"),
            }
        )
    return pd.DataFrame(diff_rows), counts


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    mode = "실제 적용" if payload["applied"] else "dry-run"
    lines = [
        "# 공식 v0.1 외부 피처 승인 후보 승격 리포트",
        "",
        f"- 작성일: {payload['created_at']}",
        f"- 실행 모드: `{mode}`",
        f"- 기존 운영 cache row 수: {payload['current_cache_rows']:,}",
        f"- 승인 후보 cache row 수: {payload['promoted_cache_rows']:,}",
        f"- 승격 gate 통과 여부: `{payload['gate_pass']}`",
        "",
        "## 1. 결론",
        "",
    ]
    if payload["gate_pass"]:
        lines.extend(
            [
                "- 승인된 외부 피처 후보만 승격 후보 cache에 포함됐다.",
                "- 중복 URL, 동명이인 충돌, 추가 수집 필요 후보는 승격 후보에서 제외됐다.",
                "- 기본 실행은 dry-run이므로 기존 운영 cache는 수정하지 않았다." if not payload["applied"] else "- 기존 운영 cache를 백업한 뒤 승인 후보 cache로 교체했다.",
            ]
        )
    else:
        lines.extend(
            [
                "- 승격 gate 위반이 발견되어 운영 cache를 수정하지 않는다.",
                "- 위반 사유를 먼저 검수한 뒤 다시 실행해야 한다.",
            ]
        )
    lines.extend(
        [
            "",
            "## 2. 후보 선별 결과",
            "",
            "| 항목 | 건수 |",
            "|---|---:|",
            f"| review queue 외부 피처 후보 | {payload['review_external_candidate_rows']:,} |",
            f"| 승인 조건 통과 후보 | {payload['selected_candidate_rows']:,} |",
            f"| 작가키 중복 제거 후 후보 | {payload['promoted_cache_rows']:,} |",
            f"| 승격 차단 후보 | {payload['blocked_candidate_rows']:,} |",
            f"| 작가키 중복으로 제외 | {payload['duplicate_artist_rows']:,} |",
            "",
            "## 3. 기존 cache 대비 차이",
            "",
            "| 구분 | 건수 |",
            "|---|---:|",
        ]
    )
    for key, value in payload["diff_counts"].items():
        lines.append(f"| `{key}` | {value:,} |")
    lines.extend(
        [
            "",
            "## 4. 차단 사유",
            "",
        ]
    )
    if payload["blocked_reasons"]:
        lines.extend(["| 사유 | 건수 |", "|---|---:|"])
        for key, value in payload["blocked_reasons"].items():
            lines.append(f"| `{key}` | {value:,} |")
    else:
        lines.append("- 차단 사유 없음")
    lines.extend(
        [
            "",
            "## 5. 산출물",
            "",
            f"- 승인 후보 cache CSV: `{payload['promoted_cache_csv']}`",
            f"- 기존 cache 대비 diff CSV: `{payload['diff_csv']}`",
            f"- 감사 JSON: `{payload['audit_json']}`",
        ]
    )
    if payload.get("backup_csv"):
        lines.append(f"- 적용 전 backup CSV: `{payload['backup_csv']}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Overwrite the operational external feature cache after backup.")
    parser.add_argument("--min-quality-score", type=float, default=MIN_APPROVED_QUALITY_SCORE)
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    if not CURRENT_CACHE_PATH.exists():
        raise FileNotFoundError(CURRENT_CACHE_PATH)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    current = pd.read_csv(CURRENT_CACHE_PATH, low_memory=False)
    if "artist_key" not in current.columns:
        raise RuntimeError("current external feature cache has no artist_key column")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        review_rows = load_review_rows(conn)
        approved_decisions = load_approved_decisions(conn)

    selected, blocked_reasons = select_approved_external_rows(
        review_rows,
        approved_decisions,
        min_quality_score=args.min_quality_score,
    )
    promoted, duplicate_artist_rows = build_candidate_frame(selected, list(current.columns))
    diff, diff_counts = diff_frames(current, promoted, selected)
    blocked_candidate_rows = len(review_rows) - len(selected)

    gate_pass = (
        len(promoted) == len(selected) - duplicate_artist_rows
        and blocked_reasons.get("blocked_duplicate_status", 0) == 0
        and blocked_reasons.get("low_quality_score", 0) == 0
        and not diff[diff["action"].eq("candidate_only") & diff["artist_key"].eq("")].shape[0]
    )

    promoted_csv = OUT_DIR / "approved_external_feature_cache_candidate.csv"
    diff_csv = OUT_DIR / "external_feature_promotion_diff.csv"
    promoted.to_csv(promoted_csv, index=False)
    diff.to_csv(diff_csv, index=False)

    backup_csv = None
    applied = False
    if args.apply:
        if not gate_pass:
            raise RuntimeError("promotion gate failed; refusing to apply")
        backup_path = CURRENT_CACHE_PATH.with_name(f"{CURRENT_CACHE_PATH.stem}.backup_{now_stamp()}{CURRENT_CACHE_PATH.suffix}")
        shutil.copy2(CURRENT_CACHE_PATH, backup_path)
        promoted.to_csv(CURRENT_CACHE_PATH, index=False)
        backup_csv = str(backup_path.relative_to(REPO))
        applied = True

    payload = {
        "created_at": now_iso(),
        "applied": applied,
        "gate_pass": bool(gate_pass),
        "db_path": str(DB_PATH.relative_to(REPO)),
        "current_cache_csv": str(CURRENT_CACHE_PATH.relative_to(REPO)),
        "current_cache_rows": int(len(current)),
        "review_external_candidate_rows": int(len(review_rows)),
        "selected_candidate_rows": int(len(selected)),
        "promoted_cache_rows": int(len(promoted)),
        "blocked_candidate_rows": int(blocked_candidate_rows),
        "duplicate_artist_rows": int(duplicate_artist_rows),
        "blocked_reasons": blocked_reasons,
        "diff_counts": {key: int(value) for key, value in diff_counts.items()},
        "promoted_cache_csv": str(promoted_csv.relative_to(REPO)),
        "diff_csv": str(diff_csv.relative_to(REPO)),
        "audit_json": str(DOC_JSON.relative_to(REPO)),
        "backup_csv": backup_csv,
    }
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
