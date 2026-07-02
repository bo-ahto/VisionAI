"""Audit Track 4 artist identity and metadata consistency."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.track3.build_unified_dataset import build_artist_ko_map, lookup_artist_name_ko  # noqa: E402

RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
OUT_CSV = REPO / "data" / "track4_artist_consistency_audit.csv"
OUT_JSON = REPO / "data" / "track4_artist_consistency_audit_summary.json"
OUT_MD = REPO / "docs" / "track4" / "audits" / "artist_consistency_audit.md"


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKC", clean(value))
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" \t\r\n,.;:")
    return text


def artist_key(value: object) -> str:
    text = normalize_name(value).lower()
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value: object) -> float | None:
    text = clean(value).replace(",", "")
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def source_artist(row: pd.Series) -> dict[str, Any]:
    source = row["track4_source"]
    if source == "saatchi":
        return {
            "artist_name_raw": clean(row.get("saatchi__artist_name")),
            "artist_slug": clean(row.get("saatchi__artist_slug")),
            "artist_name_ko_raw": "",
            "artist_name_en_raw": clean(row.get("saatchi__artist_name")),
            "nationality_raw": "",
            "birth_year": parse_number(row.get("saatchi__artist_birth_year")),
            "artist_total_works": parse_number(row.get("saatchi__artist_total_works")),
            "artist_followers": None,
            "artist_followers_log": parse_number(row.get("saatchi__ln_followers")),
            "artist_for_sale": None,
            "gallery_name_raw": clean(row.get("saatchi__gallery_name")),
        }
    if source == "artsy":
        return {
            "artist_name_raw": clean(row.get("artsy__artist_name")),
            "artist_slug": clean(row.get("artsy__artist_slug")),
            "artist_name_ko_raw": "",
            "artist_name_en_raw": clean(row.get("artsy__artist_name")),
            "nationality_raw": clean(row.get("artsy__artist_nationality")),
            "birth_year": parse_number(row.get("artsy__artist_birth_year")),
            "artist_total_works": parse_number(row.get("artsy__artist_total_works")),
            "artist_followers": parse_number(row.get("artsy__artist_followers")),
            "artist_followers_log": None,
            "artist_for_sale": parse_number(row.get("artsy__artist_for_sale")),
            "gallery_name_raw": clean(row.get("artsy__gallery_name")),
        }
    if source == "artue":
        return {
            "artist_name_raw": clean(row.get("artue__Artist")),
            "artist_slug": clean(row.get("artue__Handle")),
            "artist_name_ko_raw": "",
            "artist_name_en_raw": clean(row.get("artue__Artist")),
            "nationality_raw": clean(row.get("artue__Nationality")) or clean(row.get("artue__Nationality KO")),
            "birth_year": None,
            "artist_total_works": None,
            "artist_followers": None,
            "artist_followers_log": None,
            "artist_for_sale": None,
            "gallery_name_raw": "",
        }
    if source == "gallery_primary":
        ko = clean(row.get("gallery_primary__name_kor"))
        en = clean(row.get("gallery_primary__name_eng"))
        return {
            "artist_name_raw": ko or en,
            "artist_slug": "",
            "artist_name_ko_raw": ko,
            "artist_name_en_raw": en,
            "nationality_raw": clean(row.get("gallery_primary__국적")),
            "birth_year": parse_number(row.get("gallery_primary__birth_year")),
            "artist_total_works": None,
            "artist_followers": None,
            "artist_followers_log": None,
            "artist_for_sale": None,
            "gallery_name_raw": clean(row.get("gallery_primary__gallery_name(KR)")) or clean(row.get("gallery_primary__gallery_name(EN)")),
        }
    return {
        "artist_name_raw": "",
        "artist_slug": "",
        "artist_name_ko_raw": "",
        "artist_name_en_raw": "",
        "nationality_raw": "",
        "birth_year": None,
        "artist_total_works": None,
        "artist_followers": None,
        "artist_followers_log": None,
        "artist_for_sale": None,
        "gallery_name_raw": "",
    }


def make_audit_frame(df: pd.DataFrame) -> pd.DataFrame:
    artist_ko_map = build_artist_ko_map(REPO / "data")
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        artist = source_artist(row)
        name = normalize_name(artist["artist_name_raw"])
        key = artist_key(name)
        mapped_ko = artist["artist_name_ko_raw"] or lookup_artist_name_ko(name, artist_ko_map) or ""
        artist_name_ko_source = "raw_ko" if artist["artist_name_ko_raw"] else ("track3_mapping" if mapped_ko else "")
        birth_year = artist["birth_year"]
        status: list[str] = []

        if not name:
            status.append("missing_artist_name")
        if len(name) == 1:
            status.append("single_char_artist_name")
        if re.search(r"https?://|www\.", name, flags=re.IGNORECASE):
            status.append("artist_name_looks_url")
        if re.search(r"₩|\\$|krw|usd", name, flags=re.IGNORECASE):
            status.append("artist_name_looks_price")
        if key and key.isdigit():
            status.append("artist_name_numeric_only")

        if birth_year is not None:
            if birth_year < 1800 or birth_year > 2026:
                status.append("birth_year_out_of_range")
            elif birth_year > 2015:
                status.append("birth_year_too_recent")

        meta_fields = [
            artist["nationality_raw"],
            artist["birth_year"],
            artist["artist_total_works"],
            artist["artist_followers"],
            artist["artist_followers_log"],
            artist["artist_for_sale"],
            artist["gallery_name_raw"],
        ]
        meta_available_count = sum(1 for value in meta_fields if value not in [None, ""])

        rows.append(
            {
                "track4_source": row["track4_source"],
                "track4_source_file": row["track4_source_file"],
                "track4_source_row_index": int(row["track4_source_row_index"]),
                "artist_name_raw": artist["artist_name_raw"],
                "artist_name_standardized": name,
                "artist_name_ko": mapped_ko,
                "artist_name_ko_source": artist_name_ko_source,
                "artist_key": key,
                "artist_slug": artist["artist_slug"],
                "artist_name_ko_raw": artist["artist_name_ko_raw"],
                "artist_name_en_raw": artist["artist_name_en_raw"],
                "nationality_raw": artist["nationality_raw"],
                "birth_year": birth_year,
                "artist_total_works": artist["artist_total_works"],
                "artist_followers": artist["artist_followers"],
                "artist_followers_log": artist["artist_followers_log"],
                "artist_for_sale": artist["artist_for_sale"],
                "gallery_name_raw": artist["gallery_name_raw"],
                "artist_meta_available_count": meta_available_count,
                "artist_audit_status": "ok" if not status else ";".join(status),
            }
        )

    audit = pd.DataFrame(rows)
    name_source_counts = audit.groupby("artist_key")["track4_source"].nunique()
    slug_name_counts = audit.loc[audit["artist_slug"].ne("")].groupby("artist_slug")["artist_key"].nunique()
    audit["artist_key_source_count"] = audit["artist_key"].map(name_source_counts).fillna(0).astype(int)
    audit["artist_slug_name_count"] = audit["artist_slug"].map(slug_name_counts).fillna(0).astype(int)

    cross_source = audit["artist_key"].ne("") & audit["artist_key_source_count"].gt(1)
    slug_conflict = audit["artist_slug"].ne("") & audit["artist_slug_name_count"].gt(1)
    audit["is_cross_source_artist_key"] = cross_source
    audit.loc[slug_conflict, "artist_audit_status"] = audit.loc[slug_conflict, "artist_audit_status"].mask(
        audit.loc[slug_conflict, "artist_audit_status"].eq("ok"),
        "slug_maps_to_multiple_names",
    )
    audit.loc[slug_conflict & ~audit["artist_audit_status"].str.contains("slug_maps_to_multiple_names", regex=False), "artist_audit_status"] += ";slug_maps_to_multiple_names"
    return audit


def sample_records(df: pd.DataFrame, status: str, limit: int = 10) -> list[dict[str, Any]]:
    mask = df["artist_audit_status"].str.contains(status, regex=False, na=False)
    cols = [
        "track4_source",
        "track4_source_row_index",
        "artist_name_raw",
        "artist_name_standardized",
        "artist_key",
        "artist_slug",
        "nationality_raw",
        "birth_year",
        "artist_audit_status",
    ]
    return df.loc[mask, cols].head(limit).replace({np.nan: None}).to_dict("records")


def build_summary(audit: pd.DataFrame) -> dict[str, Any]:
    issue_counts: dict[str, int] = {}
    for value in audit["artist_audit_status"]:
        if value == "ok":
            continue
        for issue in str(value).split(";"):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    by_source = {}
    for source, group in audit.groupby("track4_source"):
        by_source[source] = {
            "rows": int(len(group)),
            "ok_rows": int(group["artist_audit_status"].eq("ok").sum()),
            "issue_rows": int((~group["artist_audit_status"].eq("ok")).sum()),
            "unique_artist_keys": int(group["artist_key"].replace("", pd.NA).nunique(dropna=True)),
            "missing_artist_name": int(group["artist_audit_status"].str.contains("missing_artist_name", regex=False).sum()),
            "birth_year_available": int(group["birth_year"].notna().sum()),
            "nationality_available": int(group["nationality_raw"].ne("").sum()),
            "artist_name_ko_available": int(group["artist_name_ko"].ne("").sum()),
            "slug_available": int(group["artist_slug"].ne("").sum()),
            "meta_available_avg": float(group["artist_meta_available_count"].mean()),
        }

    unique_artists = audit.loc[audit["artist_key"].ne(""), "artist_key"].nunique()
    cross_source_artists = audit.loc[audit["artist_key_source_count"].gt(1), "artist_key"].nunique()
    meta_coverage = {
        "birth_year": int(audit["birth_year"].notna().sum()),
        "nationality": int(audit["nationality_raw"].ne("").sum()),
        "artist_total_works": int(audit["artist_total_works"].notna().sum()),
        "artist_followers": int(audit["artist_followers"].notna().sum()),
        "artist_followers_log": int(audit["artist_followers_log"].notna().sum()),
        "artist_for_sale": int(audit["artist_for_sale"].notna().sum()),
        "gallery_name": int(audit["gallery_name_raw"].ne("").sum()),
    }

    return {
        "created_at": "2026-05-15",
        "input": str(RAW_COLLECTED.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(audit)),
        "ok_rows": int(audit["artist_audit_status"].eq("ok").sum()),
        "issue_rows": int((~audit["artist_audit_status"].eq("ok")).sum()),
        "unique_artist_keys": int(unique_artists),
        "cross_source_artist_keys": int(cross_source_artists),
        "cross_source_artist_rows": int(audit["is_cross_source_artist_key"].sum()),
        "artist_name_ko_available": int(audit["artist_name_ko"].ne("").sum()),
        "artist_name_ko_source_counts": {str(k): int(v) for k, v in audit["artist_name_ko_source"].replace("", "missing").value_counts().items()},
        "issue_counts": issue_counts,
        "meta_coverage": meta_coverage,
        "by_source": by_source,
        "samples": {
            issue: sample_records(audit, issue)
            for issue in [
                "missing_artist_name",
                "single_char_artist_name",
                "artist_name_looks_url",
                "artist_name_looks_price",
                "birth_year_out_of_range",
                "birth_year_too_recent",
                "slug_maps_to_multiple_names",
            ]
        },
    }


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 작가명/작가 메타데이터 정합성 감사",
        "",
        "- 목적: Warm/Cold split 기준이 되는 작가 식별값과 작가 메타데이터 피처 후보를 분리해서 점검",
        f"- 입력: `{summary['input']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 정상 rows: `{summary['ok_rows']:,}`",
        f"- 이슈 rows: `{summary['issue_rows']:,}`",
        f"- 표준 작가 key 수: `{summary['unique_artist_keys']:,}`",
        f"- 한글 작가명 매핑 rows: `{summary['artist_name_ko_available']:,}`",
        f"- 여러 출처에 걸친 작가 key 수: `{summary['cross_source_artist_keys']:,}`",
        f"- 여러 출처에 걸친 작가 row 수: `{summary['cross_source_artist_rows']:,}`",
        "",
        "## 1. 출처별 작가 요약",
        "",
        "| 출처 | rows | 정상 | 이슈 | 작가 key 수 | 한글명 있음 | 이름 결측 | slug 있음 | 출생연도 있음 | 국적 있음 | 메타 평균 개수 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in summary["by_source"].items():
        lines.append(
            f"| {source} | `{item['rows']:,}` | `{item['ok_rows']:,}` | `{item['issue_rows']:,}` | "
            f"`{item['unique_artist_keys']:,}` | `{item['artist_name_ko_available']:,}` | `{item['missing_artist_name']:,}` | `{item['slug_available']:,}` | "
            f"`{item['birth_year_available']:,}` | `{item['nationality_available']:,}` | `{item['meta_available_avg']:.2f}` |"
        )

    lines += [
        "",
        "## 2. 한글 작가명 매핑 출처",
        "",
        "| 매핑 출처 | rows |",
        "|---|---:|",
    ]
    for source, count in summary["artist_name_ko_source_counts"].items():
        lines.append(f"| `{source}` | `{count:,}` |")

    lines += [
        "",
        "## 3. 작가 메타데이터 커버리지",
        "",
        "| 메타데이터 | 값 있음 | 활용 판단 |",
        "|---|---:|---|",
    ]
    usage = {
        "birth_year": "운영 입력으로 받을 수 있으면 피처 후보, 없으면 결측 flag와 함께 보조 사용",
        "nationality": "표준화 난이도가 있어 바로 모델 피처로 쓰기보다 분포 확인용",
        "artist_total_works": "출처 종속성이 커서 raw 피처보다 학습 데이터 기반 count 피처 우선",
        "artist_followers": "출처 종속성이 크고 운영 재현성이 낮아 기본 피처에서 제외",
        "artist_followers_log": "Saatchi 전용 파생값이므로 기본 피처에서 제외",
        "artist_for_sale": "Artsy 전용 메타라 기본 피처에서 제외",
        "gallery_name": "작가 소속/판매처 정보로 누수와 운영 재현성 검토 후 별도 사용",
    }
    for key, count in summary["meta_coverage"].items():
        lines.append(f"| `{key}` | `{count:,}` | {usage[key]} |")

    lines += [
        "",
        "## 4. 이슈 카운트",
        "",
        "| 이슈 | 건수 | 해석 |",
        "|---|---:|---|",
    ]
    explanations = {
        "missing_artist_name": "작가명이 없어 Warm/Cold split 기준으로 쓰기 어려움",
        "single_char_artist_name": "한 글자 이름, 실제 작가명인지 확인 필요",
        "artist_name_looks_url": "작가명 위치에 URL이 들어간 후보",
        "artist_name_looks_price": "작가명 위치에 가격 문자열이 들어간 후보",
        "artist_name_numeric_only": "작가명이 숫자만 있는 후보",
        "birth_year_out_of_range": "출생연도 범위 오류 후보",
        "birth_year_too_recent": "출생연도가 지나치게 최근인 후보",
        "slug_maps_to_multiple_names": "동일 slug가 여러 이름에 연결됨",
    }
    for issue, count in sorted(summary["issue_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| `{issue}` | `{count:,}` | {explanations.get(issue, '확인 필요')} |")

    lines += [
        "",
        "## 5. 현재 판단",
        "",
        "- Warm/Cold split에는 `artist_name_standardized`와 `artist_key`를 우선 사용함",
        "- 표시/리포트용 작가명은 `artist_name_ko`를 우선 사용함",
        "- `artist_name_ko`는 Track 3 한글명 매핑 로직을 재사용해 생성함",
        "- slug는 출처 내부 식별 보조값으로 사용하되, 출처 간 공통 artist id로 바로 쓰지 않음",
        "- 작가 메타데이터는 출처별 커버리지와 생성 방식이 달라 모델 피처로 바로 넣으면 출처 누수 위험이 있음",
        "- 운영에서 다시 만들 수 있는 작가 메타데이터와, 수집 출처에만 있는 메타데이터를 분리해야 함",
        "- `artist_total_works`, `followers`, `for_sale`은 플랫폼 지표이므로 기본 모델 피처가 아니라 후보/비교 실험 대상으로 둠",
        "- 기본 Warm 피처는 원본 메타보다 학습 데이터에서 계산 가능한 `artist_works_log` 같은 이력 기반 피처가 더 안전함",
        "",
        "## 6. 제안 클렌징 규칙",
        "",
        "- 작가명이 없으면 Warm/Cold split 대상에서 제외하거나 작가 미상 그룹으로 별도 관리",
        "- 작가명은 공백/대소문자/특수문자만 정리한 `artist_name_standardized`를 생성",
        "- 작가 한글명은 `artist_name_ko`로 별도 생성",
        "- 원본에 한글명이 있으면 원본 한글명을 우선 사용",
        "- 원본 한글명이 없으면 Track 3 매핑/음역 로직을 사용",
        "- split용 key는 `artist_key`로 고정하되, 한글/영문 동명이인 병합 위험은 audit flag로 관리",
        "- 출생연도는 1800~2026 범위만 유지하고, 2015년 이후는 수동 검토 후보로 관리",
        "- 국적은 원본 보존 후 표준화 사전이 생기기 전까지 모델 피처로 쓰지 않음",
        "- followers/for_sale/플랫폼 total works는 출처 종속 메타로 분류하고 기본 학습 피처에서 제외",
        "- 작가 DB가 확보되면 별도 `artist_master` 테이블로 관리하고 작품 데이터에는 `artist_master_id`만 연결",
        "",
        "## 7. 작가 메타데이터 운영 방향",
        "",
        "- 1단계: 작품 raw 데이터에서는 작가명 원본과 표준 key만 안정화",
        "- 2단계: 작가 DB는 별도 테이블로 분리",
        "- 3단계: 작가 DB에 출생연도, 국적, 작고 여부, 활동 시작 연도, 전속/소속 여부를 관리",
        "- 4단계: 모델에는 운영 시점에 재현 가능한 메타데이터만 투입",
        "- 5단계: 출처별 플랫폼 지표는 성능 개선 실험용으로만 검토하고 최종 운영 피처는 보류",
        "",
        "## 8. 다음 단계",
        "",
        "- 위 규칙을 `standardized_v1` 또는 `cleaned_v2` 생성 스크립트에 반영",
        "- 작가명 정합성 이후 재료/지지체 정합성 `T4-C3` 진행",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    raw = pd.read_csv(RAW_COLLECTED, dtype="string", keep_default_na=False)
    audit = make_audit_frame(raw)
    audit.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    summary = build_summary(audit)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary), encoding="utf-8")

    print("Track 4 artist consistency audit")
    print(f"rows: {summary['n_rows']:,}")
    print(f"ok: {summary['ok_rows']:,}")
    print(f"issues: {summary['issue_rows']:,}")
    print(f"unique_artist_keys: {summary['unique_artist_keys']:,}")
    print(f"cross_source_artist_keys: {summary['cross_source_artist_keys']:,}")
    print(f"issue_counts: {summary['issue_counts']}")


if __name__ == "__main__":
    main()
