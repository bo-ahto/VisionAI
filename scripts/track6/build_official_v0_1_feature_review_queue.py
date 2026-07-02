#!/usr/bin/env python3
"""Build the official v0.1 external feature review queue.

The live collection pipeline must not write directly into prediction feature
caches.  This script creates a review queue that separates current accepted
baseline rows, duplicate/noisy rows, and candidates that need human review or
additional collection.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
EXTERNAL_CACHE_PATH = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_artist_external_feature_cache.csv"
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_feature_review_queue"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_feature_review_queue.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_feature_review_queue.md"

QUEUE_VERSION = "official_v0_1_feature_review_queue_20260612"
CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")

QUEUE_COLUMNS = [
    "review_candidate_id",
    "candidate_version",
    "candidate_type",
    "artist_key",
    "artist_name_ko",
    "artist_name_en",
    "normalized_artist_name",
    "source_system",
    "source_record_id",
    "source_url",
    "source_domain",
    "source_record_hash",
    "duplicate_group_key",
    "duplicate_status",
    "improvement_status",
    "existing_record_ref",
    "existing_record_hash",
    "quality_score",
    "evidence_count",
    "improved_fields_json",
    "conflict_fields_json",
    "candidate_payload_json",
    "review_status",
    "review_reasons_json",
    "created_at",
    "reviewed_at",
    "reviewed_by",
    "review_note",
]


REVIEW_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS external_feature_review_queue (
  review_candidate_id TEXT PRIMARY KEY,
  candidate_version TEXT NOT NULL,
  candidate_type TEXT NOT NULL,
  artist_key TEXT,
  artist_name_ko TEXT,
  artist_name_en TEXT,
  normalized_artist_name TEXT,
  source_system TEXT,
  source_record_id TEXT,
  source_url TEXT,
  source_domain TEXT,
  source_record_hash TEXT,
  duplicate_group_key TEXT,
  duplicate_status TEXT,
  improvement_status TEXT,
  existing_record_ref TEXT,
  existing_record_hash TEXT,
  quality_score REAL,
  evidence_count INTEGER,
  improved_fields_json TEXT,
  conflict_fields_json TEXT,
  candidate_payload_json TEXT,
  review_status TEXT NOT NULL,
  review_reasons_json TEXT,
  created_at TEXT,
  reviewed_at TEXT,
  reviewed_by TEXT,
  review_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_feature_review_status
  ON external_feature_review_queue(candidate_version, review_status);
CREATE INDEX IF NOT EXISTS idx_feature_review_artist
  ON external_feature_review_queue(artist_key);
CREATE INDEX IF NOT EXISTS idx_feature_review_duplicate
  ON external_feature_review_queue(duplicate_group_key, duplicate_status);
CREATE INDEX IF NOT EXISTS idx_feature_review_source_hash
  ON external_feature_review_queue(source_record_hash);

CREATE TABLE IF NOT EXISTS external_feature_review_decisions (
  review_decision_id TEXT PRIMARY KEY,
  review_candidate_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  decision_reason TEXT,
  reviewer TEXT,
  decided_at TEXT,
  promotion_target TEXT,
  promoted_record_id TEXT,
  FOREIGN KEY (review_candidate_id) REFERENCES external_feature_review_queue(review_candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_feature_review_decisions_candidate
  ON external_feature_review_decisions(review_candidate_id);
"""


def normalize_name(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)


def normalize_url(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"#.*$", "", text)
    return text


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def safe_int(value: object, default: int = 0) -> int:
    return int(round(safe_float(value, float(default))))


def stable_id(prefix: str, *parts: object) -> str:
    raw = "||".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return sha1(raw.encode("utf-8")).hexdigest()


def jdump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def read_sql(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def artist_name_conflicts(registry: pd.DataFrame) -> set[str]:
    names: dict[str, set[str]] = defaultdict(set)
    for _, row in registry.iterrows():
        for col in ["name_ko", "name_en", "artist_key"]:
            norm = normalize_name(row.get(col))
            if norm:
                names[norm].add(str(row.get("artist_key") or ""))
    return {name for name, artists in names.items() if len(artists) > 1}


def base_candidate(
    *,
    candidate_type: str,
    artist_key: str | None,
    artist_name_ko: str | None,
    artist_name_en: str | None,
    source_system: str,
    source_record_id: str,
    payload: dict[str, Any],
    quality_score: float,
    evidence_count: int,
    duplicate_group_key: str,
    duplicate_status: str,
    improvement_status: str,
    review_status: str,
    review_reasons: list[str],
    improved_fields: dict[str, Any] | None = None,
    conflict_fields: dict[str, Any] | None = None,
    source_url: str | None = None,
    source_domain: str | None = None,
    existing_record_ref: str | None = None,
) -> dict[str, Any]:
    normalized_artist = normalize_name(artist_name_ko or artist_name_en or artist_key)
    record_hash = payload_hash(payload)
    return {
        "review_candidate_id": stable_id("reviewcand", QUEUE_VERSION, candidate_type, source_record_id, record_hash),
        "candidate_version": QUEUE_VERSION,
        "candidate_type": candidate_type,
        "artist_key": artist_key,
        "artist_name_ko": artist_name_ko,
        "artist_name_en": artist_name_en,
        "normalized_artist_name": normalized_artist,
        "source_system": source_system,
        "source_record_id": source_record_id,
        "source_url": source_url,
        "source_domain": source_domain,
        "source_record_hash": record_hash,
        "duplicate_group_key": duplicate_group_key,
        "duplicate_status": duplicate_status,
        "improvement_status": improvement_status,
        "existing_record_ref": existing_record_ref or source_record_id,
        "existing_record_hash": record_hash if existing_record_ref else None,
        "quality_score": float(max(0.0, min(1.0, quality_score))),
        "evidence_count": int(max(0, evidence_count)),
        "improved_fields_json": jdump(improved_fields or {}),
        "conflict_fields_json": jdump(conflict_fields or {}),
        "candidate_payload_json": jdump(payload),
        "review_status": review_status,
        "review_reasons_json": jdump(review_reasons),
        "created_at": CREATED_AT,
        "reviewed_at": None,
        "reviewed_by": None,
        "review_note": None,
    }


def build_search_snapshot_candidates(search: pd.DataFrame, registry: pd.DataFrame, conflict_names: set[str]) -> list[dict[str, Any]]:
    if search.empty:
        return []
    names = registry.set_index("artist_key")[["name_ko", "name_en"]].to_dict("index") if not registry.empty else {}
    rows: list[dict[str, Any]] = []
    for _, row in search.iterrows():
        artist_key = str(row.get("artist_key") or "")
        artist_names = names.get(artist_key, {})
        name_ko = artist_names.get("name_ko") or row.get("artist_search_name")
        name_en = artist_names.get("name_en")
        normalized = normalize_name(row.get("artist_search_name") or name_ko or artist_key)
        quality = safe_float(row.get("search_quality_score"), 0.0)
        evidence = safe_int(row.get("search_result_count"), 0)
        reasons: list[str] = []
        duplicate_status = "unique"
        if normalized in conflict_names:
            duplicate_status = "artist_name_conflict"
            reasons.append("normalized artist name maps to multiple artist keys")
        if safe_int(row.get("search_collected_flag"), 0) <= 0 or safe_int(row.get("search_success_flag"), 0) <= 0:
            reasons.append("search collection did not fully succeed")
        if quality < 0.20:
            reasons.append("search quality score below 0.20")
        if str(row.get("search_homonym_risk_grade") or "").lower() not in {"clear", "low", ""}:
            reasons.append("homonym risk requires human review")

        if duplicate_status != "unique" or any("homonym" in reason for reason in reasons):
            review_status = "needs_human_review"
        elif reasons:
            review_status = "needs_improvement"
        else:
            review_status = "approved_baseline"

        improved = {
            "search_result_count": evidence,
            "search_source_count": safe_int(row.get("search_source_count"), 0),
            "search_art_context_count": safe_int(row.get("search_art_context_count"), 0),
            "search_exhibition_context_count": safe_int(row.get("search_exhibition_context_count"), 0),
            "search_quality_score": quality,
        }
        payload = {key: row.get(key) for key in row.index}
        rows.append(base_candidate(
            candidate_type="artist_search_snapshot",
            artist_key=artist_key,
            artist_name_ko=name_ko,
            artist_name_en=name_en,
            source_system="artist_search_feature_snapshots",
            source_record_id=str(row.get("search_snapshot_id") or ""),
            payload=payload,
            quality_score=quality,
            evidence_count=evidence,
            duplicate_group_key=f"artist_name:{normalized}",
            duplicate_status=duplicate_status,
            improvement_status="baseline_enough" if review_status == "approved_baseline" else "needs_better_search_evidence",
            review_status=review_status,
            review_reasons=reasons or ["accepted baseline search snapshot"],
            improved_fields=improved,
            conflict_fields={"normalized_artist_name": normalized} if duplicate_status != "unique" else {},
        ))
    return rows


def build_external_cache_candidates(cache: pd.DataFrame, conflict_names: set[str]) -> list[dict[str, Any]]:
    if cache.empty:
        return []
    rows: list[dict[str, Any]] = []
    for _, row in cache.iterrows():
        artist_key = str(row.get("artist_key") or "")
        name_ko = str(row.get("name_ko") or "") or None
        name_en = str(row.get("name_en") or "") or None
        normalized = normalize_name(name_ko or name_en or artist_key)
        gallery = safe_float(row.get("gallery_tier_any_available_flag"), 0.0)
        exhibition = safe_float(row.get("artist_exhibition_available_count"), 0.0)
        evidence = safe_int(row.get("external_feature_row_count"), 0)
        has_identity = bool(row.get("birth_year") or row.get("nationality"))
        quality = (
            0.35 * min(evidence / 5.0, 1.0)
            + 0.30 * min(exhibition / 3.0, 1.0)
            + 0.25 * min(gallery, 1.0)
            + 0.10 * (1.0 if has_identity else 0.0)
        )
        reasons: list[str] = []
        duplicate_status = "unique"
        if normalized in conflict_names:
            duplicate_status = "artist_name_conflict"
            reasons.append("normalized artist name maps to multiple artist keys")
        if gallery <= 0:
            reasons.append("gallery tier evidence missing")
        if exhibition <= 0:
            reasons.append("exhibition count evidence missing")
        if evidence <= 0:
            reasons.append("no external evidence rows")

        if duplicate_status != "unique":
            review_status = "needs_human_review"
        elif gallery <= 0 and exhibition <= 0:
            review_status = "needs_improvement"
        else:
            review_status = "approved_baseline"

        payload = {key: row.get(key) for key in row.index}
        improved = {
            "artist_exhibition_available_count": exhibition,
            "gallery_tier_any_available_flag": gallery,
            "external_feature_row_count": evidence,
            "gallery_feature_source": row.get("gallery_feature_source"),
        }
        rows.append(base_candidate(
            candidate_type="artist_external_feature_cache",
            artist_key=artist_key,
            artist_name_ko=name_ko,
            artist_name_en=name_en,
            source_system="official_v0_1_artist_external_feature_cache",
            source_record_id=artist_key,
            payload=payload,
            quality_score=quality,
            evidence_count=evidence,
            duplicate_group_key=f"artist_name:{normalized}",
            duplicate_status=duplicate_status,
            improvement_status="baseline_enough" if review_status == "approved_baseline" else "needs_live_collection",
            review_status=review_status,
            review_reasons=reasons or ["accepted baseline external feature cache"],
            improved_fields=improved,
            conflict_fields={"normalized_artist_name": normalized} if duplicate_status != "unique" else {},
        ))
    return rows


def build_duplicate_url_candidates(results: pd.DataFrame) -> list[dict[str, Any]]:
    if results.empty or "url" not in results:
        return []
    data = results.copy()
    data["normalized_url"] = data["url"].map(normalize_url)
    data = data[data["normalized_url"].ne("")]
    group_sizes = data.groupby("normalized_url").size()
    duplicate_urls = set(group_sizes[group_sizes > 1].index)
    rows: list[dict[str, Any]] = []
    if not duplicate_urls:
        return rows
    for url, group in data[data["normalized_url"].isin(duplicate_urls)].groupby("normalized_url"):
        artist_names = set(group["artist_search_name"].fillna("").astype(str))
        cross_artist = len({normalize_name(name) for name in artist_names if normalize_name(name)}) > 1
        duplicate_status = "cross_artist_duplicate_url" if cross_artist else "same_artist_duplicate_url"
        review_status = "needs_human_review" if cross_artist else "auto_reject_duplicate"
        reason = (
            "same URL appears across multiple artist searches"
            if cross_artist
            else "same URL repeated inside the same artist search result set"
        )
        for _, row in group.iterrows():
            payload = {key: row.get(key) for key in row.index if key != "normalized_url"}
            rows.append(base_candidate(
                candidate_type="search_result_url_duplicate",
                artist_key=None,
                artist_name_ko=row.get("artist_search_name"),
                artist_name_en=None,
                source_system="artist_search_results",
                source_record_id=str(row.get("result_id") or ""),
                payload=payload,
                quality_score=0.0,
                evidence_count=int(len(group)),
                duplicate_group_key=f"url:{sha1(url.encode('utf-8')).hexdigest()[:20]}",
                duplicate_status=duplicate_status,
                improvement_status="duplicate_noise",
                review_status=review_status,
                review_reasons=[reason],
                conflict_fields={
                    "normalized_url": url,
                    "duplicate_count": int(len(group)),
                    "cross_artist": cross_artist,
                },
                source_url=row.get("url"),
                source_domain=row.get("domain"),
            ))
    return rows


def build_sale_feedback_candidates(feedback: pd.DataFrame, prediction_events: pd.DataFrame) -> list[dict[str, Any]]:
    if feedback.empty:
        return []
    events = prediction_events.set_index("prediction_id").to_dict("index") if not prediction_events.empty else {}
    rows: list[dict[str, Any]] = []
    for _, row in feedback.iterrows():
        event = events.get(str(row.get("prediction_id") or ""), {})
        evidence_status = str(row.get("evidence_status") or "partial")
        quality = {"verified": 0.95, "partial": 0.55, "none": 0.20}.get(evidence_status, 0.40)
        review_status = str(row.get("review_status") or "needs_review")
        payload = {key: row.get(key) for key in row.index}
        rows.append(base_candidate(
            candidate_type="sale_price_feedback",
            artist_key=event.get("artist_key"),
            artist_name_ko=None,
            artist_name_en=None,
            source_system="sale_price_feedback",
            source_record_id=str(row.get("feedback_id") or ""),
            payload=payload,
            quality_score=quality,
            evidence_count=1,
            duplicate_group_key=f"prediction:{row.get('prediction_id')}",
            duplicate_status="unique",
            improvement_status="adds_actual_sale_price",
            review_status=review_status,
            review_reasons=["actual sale price must be human-reviewed before training promotion"],
            improved_fields={
                "actual_sale_price_krw": row.get("actual_sale_price_krw"),
                "evidence_status": evidence_status,
                "route_at_prediction": event.get("route"),
            },
            existing_record_ref=str(row.get("prediction_id") or ""),
        ))
    return rows


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(REVIEW_SCHEMA_SQL)


def write_queue(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    ensure_schema(conn)
    conn.execute("DELETE FROM external_feature_review_queue WHERE candidate_version = ?", (QUEUE_VERSION,))
    placeholders = ",".join("?" for _ in QUEUE_COLUMNS)
    sql = f"""
        INSERT OR REPLACE INTO external_feature_review_queue
        ({",".join(QUEUE_COLUMNS)})
        VALUES ({placeholders})
    """
    conn.executemany(sql, [[row.get(col) for col in QUEUE_COLUMNS] for row in rows])
    conn.commit()


def summary_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {"created_at": CREATED_AT, "candidate_version": QUEUE_VERSION, "total_candidates": 0}
    return {
        "created_at": CREATED_AT,
        "candidate_version": QUEUE_VERSION,
        "total_candidates": int(len(frame)),
        "candidate_type_counts": {str(k): int(v) for k, v in frame["candidate_type"].value_counts().to_dict().items()},
        "review_status_counts": {str(k): int(v) for k, v in frame["review_status"].value_counts().to_dict().items()},
        "duplicate_status_counts": {str(k): int(v) for k, v in frame["duplicate_status"].value_counts().to_dict().items()},
        "improvement_status_counts": {str(k): int(v) for k, v in frame["improvement_status"].value_counts().to_dict().items()},
        "needs_human_review_count": int(frame["review_status"].eq("needs_human_review").sum()),
        "needs_improvement_count": int(frame["review_status"].eq("needs_improvement").sum()),
        "auto_reject_duplicate_count": int(frame["review_status"].eq("auto_reject_duplicate").sum()),
        "approved_baseline_count": int(frame["review_status"].eq("approved_baseline").sum()),
        "output_csv": str((OUT_DIR / "outputs" / "feature_review_queue.csv").relative_to(REPO)),
        "output_db": str(DB_PATH.relative_to(REPO)),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 공식 v0.1 외부 피처 검수 큐",
        "",
        f"- 작성일: {payload['created_at']}",
        f"- 큐 버전: `{payload['candidate_version']}`",
        f"- 전체 후보 수: {payload['total_candidates']:,}건",
        "",
        "## 1. 결론",
        "",
        f"- 승인된 baseline 후보: {payload.get('approved_baseline_count', 0):,}건",
        f"- 개선 수집 필요 후보: {payload.get('needs_improvement_count', 0):,}건",
        f"- 사람 검수 필요 후보: {payload.get('needs_human_review_count', 0):,}건",
        f"- 자동 중복 제외 후보: {payload.get('auto_reject_duplicate_count', 0):,}건",
        "- 운영 원칙: `approved_baseline` 또는 별도 검수 결정에서 `approved`가 된 후보만 feature cache 승격 대상",
        "",
        "## 2. 검수 상태별 수량",
        "",
        "| 상태 | 건수 |",
        "|---|---:|",
    ]
    for key, value in payload.get("review_status_counts", {}).items():
        lines.append(f"| `{key}` | {value:,} |")
    lines.extend([
        "",
        "## 3. 중복 판정 기준",
        "",
        "| 기준 | 처리 |",
        "|---|---|",
        "| 같은 URL이 같은 작가 검색 내 반복 | `auto_reject_duplicate` |",
        "| 같은 URL이 여러 작가 검색에 반복 | `needs_human_review` |",
        "| 정규화 작가명이 여러 artist_key에 매핑 | `needs_human_review` |",
        "| 동일 source hash 재수집 | 기존 승인 row와 비교 후 중복 제외 |",
        "",
        "## 4. 개선 판정 기준",
        "",
        "| 기준 | 처리 |",
        "|---|---|",
        "| 검색 품질 점수 낮음 또는 수집 실패 | `needs_improvement` |",
        "| 전시/갤러리 evidence 없음 | `needs_improvement` |",
        "| 실제 판매가 feedback | `needs_review` 후 학습 후보 승격 |",
        "| gallery/exhibition/source_count 증가 | 기존 cache보다 개선된 후보로 검수 대상 |",
        "",
        "## 5. 산출물",
        "",
        f"- CSV: `{payload.get('output_csv')}`",
        f"- DB: `{payload.get('output_db')}` table `external_feature_review_queue`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    OUT_DIR.joinpath("outputs").mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        registry = read_sql(conn, "artist_registry")
        search = read_sql(conn, "artist_search_feature_snapshots")
        search_results = read_sql(conn, "artist_search_results")
        feedback = read_sql(conn, "sale_price_feedback")
        prediction_events = read_sql(conn, "prediction_events")
        conflict_names = artist_name_conflicts(registry)
        external_cache = pd.read_csv(EXTERNAL_CACHE_PATH, low_memory=False) if EXTERNAL_CACHE_PATH.exists() else pd.DataFrame()
        rows = []
        rows.extend(build_search_snapshot_candidates(search, registry, conflict_names))
        rows.extend(build_external_cache_candidates(external_cache, conflict_names))
        rows.extend(build_duplicate_url_candidates(search_results))
        rows.extend(build_sale_feedback_candidates(feedback, prediction_events))
        write_queue(conn, rows)

    frame = pd.DataFrame(rows)
    frame.to_csv(OUT_DIR / "outputs" / "feature_review_queue.csv", index=False)
    payload = summary_payload(rows)
    (OUT_DIR / "outputs" / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
