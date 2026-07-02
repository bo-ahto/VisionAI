#!/usr/bin/env python3
"""Audit official v0.1 artist identity migration quality.

The official v0.1 DB was built from the existing Track6 artist_key values.  Some
rows that look like one real artist can be split across multiple artist_key
variants, usually because of romanization order, spacing, or mixed Korean/English
labels.  This audit does not merge rows.  It creates a review queue that
separates likely false splits from real homonym/ambiguous cases.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_artist_identity_migration_audit"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_migration_audit.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_migration_audit.md"

CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")
PLACEHOLDER_NAMES = {"", "missing", "__missing__", "nan", "__nan__", "none", "null", "unknown", "미상", "없음"}

REVIEW_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS artist_identity_review_queue (
  identity_review_id TEXT PRIMARY KEY,
  normalized_alias TEXT NOT NULL,
  alias_texts_json TEXT,
  candidate_artist_keys_json TEXT NOT NULL,
  canonical_artist_key TEXT,
  candidate_count INTEGER,
  combined_valid_price_count INTEGER,
  max_single_valid_price_count INTEGER,
  split_loss_price_count INTEGER,
  distinct_birth_years_json TEXT,
  distinct_nationalities_json TEXT,
  distinct_mediums_json TEXT,
  median_price_ratio REAL,
  identity_score REAL,
  recommendation TEXT NOT NULL,
  review_status TEXT NOT NULL,
  review_reasons_json TEXT,
  sample_titles_json TEXT,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_artist_identity_review_alias
  ON artist_identity_review_queue(normalized_alias);
CREATE INDEX IF NOT EXISTS idx_artist_identity_review_status
  ON artist_identity_review_queue(review_status, recommendation);
CREATE INDEX IF NOT EXISTS idx_artist_identity_review_canonical
  ON artist_identity_review_queue(canonical_artist_key);

CREATE TABLE IF NOT EXISTS artist_identity_review_decisions (
  identity_decision_id TEXT PRIMARY KEY,
  identity_review_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  decision_reason TEXT,
  canonical_artist_key TEXT,
  reviewer TEXT,
  decided_at TEXT,
  FOREIGN KEY(identity_review_id) REFERENCES artist_identity_review_queue(identity_review_id)
);
"""


def normalize_name(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)


def stable_id(prefix: str, *parts: object) -> str:
    raw = "||".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def jdump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def normalized_nationality(value: object) -> str:
    text = normalize_name(value)
    aliases = {
        "southkorean": "korea",
        "southkorea": "korea",
        "republicofkorea": "korea",
        "korean": "korea",
        "korea": "korea",
        "southkorea": "korea",
        "southkorea": "korea",
    }
    text = text.replace("southkorea", "southkorea")
    return aliases.get(text, text)


def load_db() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with sqlite3.connect(DB_PATH) as conn:
        registry = pd.read_sql_query("SELECT * FROM artist_registry", conn)
        aliases = pd.read_sql_query("SELECT * FROM artist_aliases", conn)
        observations = pd.read_sql_query(
            """
            SELECT artist_key, title, price_krw, medium_category, support_category, source_artwork_id
            FROM artwork_price_observations
            WHERE artist_key IS NOT NULL
            """,
            conn,
        )
    return registry, aliases, observations


def build_conflict_groups(registry: pd.DataFrame, aliases: pd.DataFrame) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    valid_aliases = aliases.copy()
    valid_aliases["alias_normalized"] = valid_aliases["alias_normalized"].map(normalize_name)
    valid_aliases = valid_aliases[~valid_aliases["alias_normalized"].isin(PLACEHOLDER_NAMES)]
    for alias, group in valid_aliases.groupby("alias_normalized", dropna=False):
        keys = sorted(set(group["artist_key"].dropna().astype(str)))
        if len(keys) <= 1:
            continue
        groups[str(alias)] = {
            "normalized_alias": str(alias),
            "artist_keys": keys,
            "alias_texts": sorted(set(group["alias_text"].dropna().astype(str))),
            "sources": sorted(set(group["source"].dropna().astype(str))),
            "basis": "artist_aliases",
        }

    for name_col in ["name_ko", "name_en"]:
        data = registry[["artist_key", name_col]].copy()
        data["normalized"] = data[name_col].map(normalize_name)
        data = data[~data["normalized"].isin(PLACEHOLDER_NAMES)]
        for alias, group in data.groupby("normalized", dropna=False):
            keys = sorted(set(group["artist_key"].dropna().astype(str)))
            if len(keys) <= 1:
                continue
            current = groups.setdefault(
                str(alias),
                {
                    "normalized_alias": str(alias),
                    "artist_keys": [],
                    "alias_texts": [],
                    "sources": [],
                    "basis": "artist_registry",
                },
            )
            current["artist_keys"] = sorted(set(current["artist_keys"]) | set(keys))
            current["alias_texts"] = sorted(set(current["alias_texts"]) | set(group[name_col].dropna().astype(str)))
    return groups


def group_observation_summary(observations: pd.DataFrame, keys: list[str]) -> dict[str, Any]:
    group = observations[observations["artist_key"].astype(str).isin(keys)].copy()
    samples: dict[str, list[dict[str, Any]]] = {}
    for artist_key, rows in group.groupby("artist_key", dropna=False):
        sample_rows = rows.sort_values("price_krw", ascending=False).head(3)
        samples[str(artist_key)] = [
            {
                "title": row.get("title"),
                "price_krw": row.get("price_krw"),
                "medium": row.get("medium_category"),
                "support": row.get("support_category"),
                "source_artwork_id": row.get("source_artwork_id"),
            }
            for _, row in sample_rows.iterrows()
        ]
    return {
        "row_count": int(len(group)),
        "samples": samples,
    }


def score_group(artists: pd.DataFrame, alias: str) -> tuple[float, str, str, list[str]]:
    reasons: list[str] = []
    birth_years = sorted({int(v) for v in pd.to_numeric(artists["birth_year"], errors="coerce").dropna().tolist()})
    homonym_flags = pd.to_numeric(artists["is_homonym"], errors="coerce").fillna(0).astype(int).tolist()
    entity_suffixes = sorted({str(v) for v in artists["entity_suffix"].dropna().tolist() if str(v).strip()})
    nationalities = sorted({normalized_nationality(v) for v in artists["nationality"].dropna().tolist() if normalized_nationality(v)})
    valid_counts = pd.to_numeric(artists["valid_price_count"], errors="coerce").fillna(0).astype(int).tolist()
    medians = [v for v in pd.to_numeric(artists["median_price_krw"], errors="coerce").dropna().tolist() if v > 0]
    price_ratio = max(medians) / min(medians) if len(medians) >= 2 and min(medians) > 0 else None

    score = 0.40
    if len(birth_years) <= 1:
        score += 0.22
        reasons.append("birth year does not conflict")
    else:
        score -= 0.35
        reasons.append("birth year conflict")

    if not any(homonym_flags) and not entity_suffixes:
        score += 0.16
        reasons.append("no homonym flag or entity suffix")
    else:
        score -= 0.20
        reasons.append("homonym flag or entity suffix exists")

    if len(nationalities) <= 1:
        score += 0.10
        reasons.append("nationality does not conflict")
    else:
        score -= 0.10
        reasons.append("nationality conflict")

    if price_ratio is None or price_ratio <= 8:
        score += 0.07
        reasons.append("median price ratio is not extreme")
    elif price_ratio > 30:
        score -= 0.15
        reasons.append("median price ratio is extreme")
    else:
        reasons.append("median price ratio needs review")

    if sum(valid_counts) >= 5:
        score += 0.05
        reasons.append("combined price history is meaningful")

    score = max(0.0, min(1.0, score))
    if len(birth_years) > 1:
        return score, "keep_separate_until_verified", "needs_human_review", reasons
    if any(homonym_flags) or entity_suffixes:
        return score, "identity_review_required", "needs_human_review", reasons
    if score >= 0.80:
        return score, "likely_false_split_merge_candidate", "needs_merge_review", reasons
    if score >= 0.60:
        return score, "possible_false_split_review", "needs_human_review", reasons
    return score, "keep_separate_until_verified", "needs_human_review", reasons


def build_review_rows(registry: pd.DataFrame, aliases: pd.DataFrame, observations: pd.DataFrame) -> list[dict[str, Any]]:
    groups = build_conflict_groups(registry, aliases)
    registry_by_key = registry.set_index("artist_key", drop=False)
    rows: list[dict[str, Any]] = []
    for alias, group in groups.items():
        keys = [key for key in group["artist_keys"] if key in registry_by_key.index]
        if len(keys) <= 1:
            continue
        artists = registry_by_key.loc[keys].copy()
        if isinstance(artists, pd.Series):
            artists = artists.to_frame().T
        artists = artists.reset_index(drop=True)
        artists["valid_price_count"] = pd.to_numeric(artists["valid_price_count"], errors="coerce").fillna(0).astype(int)
        canonical = str(artists.sort_values(["valid_price_count", "artist_key"], ascending=[False, True]).iloc[0]["artist_key"])
        combined = int(artists["valid_price_count"].sum())
        max_single = int(artists["valid_price_count"].max())
        score, recommendation, review_status, reasons = score_group(artists, alias)
        medians = [v for v in pd.to_numeric(artists["median_price_krw"], errors="coerce").dropna().tolist() if v > 0]
        price_ratio = max(medians) / min(medians) if len(medians) >= 2 and min(medians) > 0 else None
        obs_summary = group_observation_summary(observations, keys)
        row = {
            "identity_review_id": stable_id("artistident", alias, ",".join(keys)),
            "normalized_alias": alias,
            "alias_texts_json": jdump(group["alias_texts"]),
            "candidate_artist_keys_json": jdump(keys),
            "canonical_artist_key": canonical,
            "candidate_count": len(keys),
            "combined_valid_price_count": combined,
            "max_single_valid_price_count": max_single,
            "split_loss_price_count": combined - max_single,
            "distinct_birth_years_json": jdump(sorted({int(v) for v in pd.to_numeric(artists["birth_year"], errors="coerce").dropna().tolist()})),
            "distinct_nationalities_json": jdump(sorted({normalized_nationality(v) for v in artists["nationality"].dropna().tolist() if normalized_nationality(v)})),
            "distinct_mediums_json": jdump(sorted({str(v) for v in artists["primary_medium_category"].dropna().tolist() if str(v).strip()})),
            "median_price_ratio": price_ratio,
            "identity_score": score,
            "recommendation": recommendation,
            "review_status": review_status,
            "review_reasons_json": jdump(reasons),
            "sample_titles_json": jdump(obs_summary["samples"]),
            "created_at": CREATED_AT,
        }
        rows.append(row)
    return sorted(rows, key=lambda r: (-float(r["identity_score"]), -int(r["split_loss_price_count"]), r["normalized_alias"]))


def write_db(rows: list[dict[str, Any]]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(REVIEW_SCHEMA_SQL)
        conn.execute("DELETE FROM artist_identity_review_queue")
        if rows:
            columns = list(rows[0].keys())
            placeholders = ",".join("?" for _ in columns)
            conn.executemany(
                f"INSERT OR REPLACE INTO artist_identity_review_queue ({','.join(columns)}) VALUES ({placeholders})",
                [[row.get(col) for col in columns] for row in rows],
            )
        conn.commit()


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "- 없음\n"
    data = frame[columns].head(max_rows).copy()
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in data.iterrows():
        values = [str(row.get(col, "")).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    csv_path = OUT_DIR / "artist_identity_review_queue.csv"
    frame.to_csv(csv_path, index=False)
    counts = frame["recommendation"].value_counts().to_dict() if not frame.empty else {}
    status_counts = frame["review_status"].value_counts().to_dict() if not frame.empty else {}
    payload = {
        "created_at": CREATED_AT,
        "total_conflict_groups": int(len(frame)),
        "recommendation_counts": {str(k): int(v) for k, v in counts.items()},
        "review_status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "likely_false_split_count": int(frame["recommendation"].eq("likely_false_split_merge_candidate").sum()) if not frame.empty else 0,
        "possible_false_split_count": int(frame["recommendation"].eq("possible_false_split_review").sum()) if not frame.empty else 0,
        "keep_separate_count": int(frame["recommendation"].eq("keep_separate_until_verified").sum()) if not frame.empty else 0,
        "total_split_loss_price_count": int(frame["split_loss_price_count"].sum()) if not frame.empty else 0,
        "likely_false_split_loss_price_count": int(frame.loc[frame["recommendation"].eq("likely_false_split_merge_candidate"), "split_loss_price_count"].sum()) if not frame.empty else 0,
        "output_csv": str(csv_path.relative_to(REPO)),
        "output_db": str(DB_PATH.relative_to(REPO)),
    }
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    likely = frame[frame["recommendation"].eq("likely_false_split_merge_candidate")] if not frame.empty else pd.DataFrame()
    review = frame[frame["recommendation"].eq("possible_false_split_review")] if not frame.empty else pd.DataFrame()
    keep = frame[frame["recommendation"].eq("keep_separate_until_verified")] if not frame.empty else pd.DataFrame()
    md = [
        "# 공식 v0.1 작가 식별자 이관 품질 감사",
        "",
        f"- 작성일: {CREATED_AT}",
        f"- 충돌 alias 그룹: {payload['total_conflict_groups']:,}건",
        f"- 높은 확률의 잘못 분리 후보: {payload['likely_false_split_count']:,}건",
        f"- 추가 확인 필요한 분리 후보: {payload['possible_false_split_count']:,}건",
        f"- 분리 유지 또는 확인 전 보류 후보: {payload['keep_separate_count']:,}건",
        "",
        "## 1. 결론",
        "",
        "- DB 이관 시 원본 `artist_key`를 그대로 사용하면서 같은 작가가 영문 표기 순서/띄어쓰기 차이로 분리된 후보가 확인됐다.",
        "- 자동 병합은 하지 않았다. `artist_identity_review_queue`에 후보와 근거를 저장했다.",
        "- 병합 후보는 서비스 라우팅, Warm 이력 수, 외부 피처 승격 판단에 영향을 주므로 검수 후 canonical artist_key로 정리해야 한다.",
        "",
        "## 2. 추천 상태별 수량",
        "",
        "| 추천 상태 | 건수 |",
        "|---|---:|",
    ]
    for key, value in payload["recommendation_counts"].items():
        md.append(f"| `{key}` | {value:,} |")
    md.extend([
        "",
        "## 3. 높은 확률의 잘못 분리 후보 상위",
        "",
        markdown_table(
            likely,
            [
                "normalized_alias",
                "candidate_count",
                "canonical_artist_key",
                "candidate_artist_keys_json",
                "combined_valid_price_count",
                "split_loss_price_count",
                "identity_score",
                "distinct_birth_years_json",
                "median_price_ratio",
            ],
            25,
        ),
        "",
        "## 4. 추가 확인 필요 후보 상위",
        "",
        markdown_table(
            review,
            [
                "normalized_alias",
                "candidate_count",
                "canonical_artist_key",
                "candidate_artist_keys_json",
                "combined_valid_price_count",
                "split_loss_price_count",
                "identity_score",
                "distinct_birth_years_json",
                "median_price_ratio",
            ],
            25,
        ),
        "",
        "## 5. 분리 유지 또는 확인 전 보류 후보 상위",
        "",
        markdown_table(
            keep,
            [
                "normalized_alias",
                "candidate_count",
                "canonical_artist_key",
                "candidate_artist_keys_json",
                "combined_valid_price_count",
                "split_loss_price_count",
                "identity_score",
                "distinct_birth_years_json",
                "median_price_ratio",
            ],
            25,
        ),
        "",
        "## 6. 산출물",
        "",
        f"- CSV: `{payload['output_csv']}`",
        f"- DB table: `{payload['output_db']}` table `artist_identity_review_queue`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ])
    DOC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    registry, aliases, observations = load_db()
    rows = build_review_rows(registry, aliases, observations)
    write_db(rows)
    payload = write_outputs(rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
