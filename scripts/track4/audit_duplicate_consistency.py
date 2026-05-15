"""Audit Track 4 duplicate candidates across source-preserving raw data."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
PRICE_AUDIT = REPO / "data" / "track4_price_consistency_audit.csv"
SIZE_AUDIT = REPO / "data" / "track4_size_consistency_audit.csv"
ARTIST_AUDIT = REPO / "data" / "track4_artist_consistency_audit.csv"
OUT_CSV = REPO / "data" / "track4_duplicate_consistency_audit.csv"
OUT_JSON = REPO / "data" / "track4_duplicate_consistency_audit_summary.json"
OUT_MD = REPO / "docs" / "track4_duplicate_consistency_audit.md"


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def norm_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", clean(value)).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_intish(value: object) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def round_or_none(value: object, base: int = 1) -> int | None:
    try:
        if pd.isna(value):
            return None
        return int(round(float(value) / base) * base)
    except (TypeError, ValueError):
        return None


def source_identity(row: pd.Series) -> dict[str, Any]:
    source = row["track4_source"]
    if source == "saatchi":
        return {
            "source_artwork_id": clean(row.get("saatchi__artwork_id")),
            "title_raw": clean(row.get("saatchi__title")),
            "artwork_url": clean(row.get("saatchi__artwork_url")),
            "image_url": clean(row.get("saatchi__image_url")),
        }
    if source == "artsy":
        return {
            "source_artwork_id": clean(row.get("artsy__artwork_id")),
            "title_raw": clean(row.get("artsy__title")),
            "artwork_url": clean(row.get("artsy__artwork_url")),
            "image_url": clean(row.get("artsy__image_url")),
        }
    if source == "artue":
        return {
            "source_artwork_id": clean(row.get("artue__Handle")),
            "title_raw": clean(row.get("artue__Title")),
            "artwork_url": clean(row.get("artue__URL")),
            "image_url": "",
        }
    if source == "gallery_primary":
        return {
            "source_artwork_id": clean(row.get("gallery_primary__idx")),
            "title_raw": clean(row.get("gallery_primary__title")),
            "artwork_url": "",
            "image_url": clean(row.get("gallery_primary__img_src")),
        }
    return {"source_artwork_id": "", "title_raw": "", "artwork_url": "", "image_url": ""}


def load_base_frame() -> pd.DataFrame:
    raw = pd.read_csv(RAW_COLLECTED, dtype="string", keep_default_na=False)
    price = pd.read_csv(
        PRICE_AUDIT,
        usecols=["track4_source", "track4_source_row_index", "price_krw"],
    )
    size = pd.read_csv(
        SIZE_AUDIT,
        usecols=["track4_source", "track4_source_row_index", "width_cm", "height_cm", "depth_cm", "area_cm2"],
    )
    artist = pd.read_csv(
        ARTIST_AUDIT,
        usecols=["track4_source", "track4_source_row_index", "artist_name_standardized", "artist_name_ko", "artist_key"],
        dtype={"track4_source": "string", "artist_name_standardized": "string", "artist_key": "string"},
        keep_default_na=False,
    )
    raw["track4_source_row_index"] = raw["track4_source_row_index"].astype(int)
    merged = raw.merge(price, on=["track4_source", "track4_source_row_index"], how="left")
    merged = merged.merge(size, on=["track4_source", "track4_source_row_index"], how="left")
    merged = merged.merge(artist, on=["track4_source", "track4_source_row_index"], how="left")
    return merged


def make_audit_frame(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        ident = source_identity(row)
        price_bucket = round_or_none(row.get("price_krw"), 10_000)
        width_bucket = round_or_none(row.get("width_cm"), 1)
        height_bucket = round_or_none(row.get("height_cm"), 1)
        depth_bucket = round_or_none(row.get("depth_cm"), 1)
        area_bucket = round_or_none(row.get("area_cm2"), 100)
        title_key = norm_text(ident["title_raw"])
        artist_key = clean(row.get("artist_key"))

        same_source_semantic_key = "|".join(
            [
                clean(row["track4_source"]),
                artist_key,
                title_key,
                str(price_bucket or ""),
                str(width_bucket or ""),
                str(height_bucket or ""),
                str(depth_bucket or ""),
            ]
        )
        cross_source_semantic_key = "|".join(
            [
                artist_key,
                title_key,
                str(price_bucket or ""),
                str(width_bucket or ""),
                str(height_bucket or ""),
                str(depth_bucket or ""),
            ]
        )
        loose_cross_source_key = "|".join(
            [
                artist_key,
                title_key,
                str(width_bucket or ""),
                str(height_bucket or ""),
            ]
        )

        rows.append(
            {
                "track4_source": row["track4_source"],
                "track4_source_file": row["track4_source_file"],
                "track4_source_row_index": int(row["track4_source_row_index"]),
                "source_artwork_id": ident["source_artwork_id"],
                "title_raw": ident["title_raw"],
                "title_key": title_key,
                "artist_name_standardized": clean(row.get("artist_name_standardized")),
                "artist_name_ko": clean(row.get("artist_name_ko")),
                "artist_key": artist_key,
                "price_krw": row.get("price_krw"),
                "price_bucket_10k": price_bucket,
                "width_cm": row.get("width_cm"),
                "height_cm": row.get("height_cm"),
                "depth_cm": row.get("depth_cm"),
                "area_cm2": row.get("area_cm2"),
                "width_bucket_cm": width_bucket,
                "height_bucket_cm": height_bucket,
                "depth_bucket_cm": depth_bucket,
                "area_bucket_100cm2": area_bucket,
                "artwork_url": ident["artwork_url"],
                "image_url": ident["image_url"],
                "same_source_id_key": clean(row["track4_source"]) + "|" + ident["source_artwork_id"],
                "same_source_url_key": clean(row["track4_source"]) + "|" + ident["artwork_url"],
                "same_source_image_key": clean(row["track4_source"]) + "|" + ident["image_url"],
                "same_source_semantic_key": same_source_semantic_key,
                "cross_source_semantic_key": cross_source_semantic_key,
                "loose_cross_source_key": loose_cross_source_key,
            }
        )

    audit = pd.DataFrame(rows)
    count_specs = {
        "same_source_id_count": "same_source_id_key",
        "same_source_url_count": "same_source_url_key",
        "same_source_image_count": "same_source_image_key",
        "same_source_semantic_count": "same_source_semantic_key",
        "cross_source_semantic_count": "cross_source_semantic_key",
        "loose_cross_source_count": "loose_cross_source_key",
    }
    for out_col, key_col in count_specs.items():
        valid = audit[key_col].ne("") & ~audit[key_col].str.endswith("|")
        counts = audit.loc[valid].groupby(key_col)[key_col].transform("size")
        audit[out_col] = 0
        audit.loc[valid, out_col] = counts.astype(int)

    cross_source_nunique = audit.groupby("cross_source_semantic_key")["track4_source"].nunique()
    loose_cross_source_nunique = audit.groupby("loose_cross_source_key")["track4_source"].nunique()
    audit["cross_source_semantic_source_count"] = audit["cross_source_semantic_key"].map(cross_source_nunique).fillna(0).astype(int)
    audit["loose_cross_source_source_count"] = audit["loose_cross_source_key"].map(loose_cross_source_nunique).fillna(0).astype(int)

    statuses: list[str] = []
    for _, row in audit.iterrows():
        status: list[str] = []
        if not row["source_artwork_id"]:
            status.append("missing_source_artwork_id")
        if not row["title_key"]:
            status.append("missing_title_key")
        if not row["artist_key"]:
            status.append("missing_artist_key")
        if row["same_source_id_count"] > 1 and row["source_artwork_id"]:
            status.append("same_source_id_duplicate")
        if row["same_source_url_count"] > 1 and row["artwork_url"]:
            status.append("same_source_url_duplicate")
        if row["same_source_image_count"] > 1 and row["image_url"]:
            status.append("same_source_image_duplicate")
        if row["same_source_semantic_count"] > 1 and row["title_key"] and row["artist_key"]:
            status.append("same_source_semantic_duplicate")
        if row["cross_source_semantic_count"] > 1 and row["cross_source_semantic_source_count"] > 1 and row["title_key"] and row["artist_key"]:
            status.append("cross_source_semantic_duplicate")
        if row["loose_cross_source_count"] > 1 and row["loose_cross_source_source_count"] > 1 and row["title_key"] and row["artist_key"]:
            status.append("loose_cross_source_candidate")
        statuses.append("ok" if not status else ";".join(status))
    audit["duplicate_audit_status"] = statuses
    return audit


def issue_counts(audit: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in audit["duplicate_audit_status"]:
        if value == "ok":
            continue
        for issue in str(value).split(";"):
            counts[issue] = counts.get(issue, 0) + 1
    return counts


def duplicate_group_count(audit: pd.DataFrame, key_col: str, count_col: str) -> int:
    mask = audit[count_col].gt(1) & audit[key_col].ne("")
    return int(audit.loc[mask, key_col].nunique())


def cross_source_group_count(audit: pd.DataFrame, key_col: str, count_col: str, source_count_col: str) -> int:
    mask = audit[count_col].gt(1) & audit[source_count_col].gt(1) & audit[key_col].ne("")
    return int(audit.loc[mask, key_col].nunique())


def sample_records(audit: pd.DataFrame, status: str, limit: int = 10) -> list[dict[str, Any]]:
    mask = audit["duplicate_audit_status"].str.contains(status, regex=False, na=False)
    cols = [
        "track4_source",
        "track4_source_row_index",
        "source_artwork_id",
        "artist_name_standardized",
        "title_raw",
        "price_krw",
        "width_cm",
        "height_cm",
        "duplicate_audit_status",
    ]
    return audit.loc[mask, cols].head(limit).replace({np.nan: None}).to_dict("records")


def build_summary(audit: pd.DataFrame) -> dict[str, Any]:
    counts = issue_counts(audit)
    by_source = {}
    for source, group in audit.groupby("track4_source"):
        by_source[source] = {
            "rows": int(len(group)),
            "ok_rows": int(group["duplicate_audit_status"].eq("ok").sum()),
            "issue_rows": int((~group["duplicate_audit_status"].eq("ok")).sum()),
            "same_source_id_duplicate": int(group["duplicate_audit_status"].str.contains("same_source_id_duplicate", regex=False).sum()),
            "same_source_semantic_duplicate": int(group["duplicate_audit_status"].str.contains("same_source_semantic_duplicate", regex=False).sum()),
            "cross_source_semantic_duplicate": int(group["duplicate_audit_status"].str.contains("cross_source_semantic_duplicate", regex=False).sum()),
            "loose_cross_source_candidate": int(group["duplicate_audit_status"].str.contains("loose_cross_source_candidate", regex=False).sum()),
        }
    return {
        "created_at": "2026-05-15",
        "input": str(RAW_COLLECTED.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(audit)),
        "ok_rows": int(audit["duplicate_audit_status"].eq("ok").sum()),
        "issue_rows": int((~audit["duplicate_audit_status"].eq("ok")).sum()),
        "issue_counts": counts,
        "duplicate_group_counts": {
            "same_source_id_groups": duplicate_group_count(audit, "same_source_id_key", "same_source_id_count"),
            "same_source_url_groups": duplicate_group_count(audit, "same_source_url_key", "same_source_url_count"),
            "same_source_image_groups": duplicate_group_count(audit, "same_source_image_key", "same_source_image_count"),
            "same_source_semantic_groups": duplicate_group_count(audit, "same_source_semantic_key", "same_source_semantic_count"),
            "cross_source_semantic_groups": cross_source_group_count(audit, "cross_source_semantic_key", "cross_source_semantic_count", "cross_source_semantic_source_count"),
            "loose_cross_source_groups": cross_source_group_count(audit, "loose_cross_source_key", "loose_cross_source_count", "loose_cross_source_source_count"),
        },
        "by_source": by_source,
        "samples": {
            issue: sample_records(audit, issue)
            for issue in [
                "same_source_id_duplicate",
                "same_source_url_duplicate",
                "same_source_image_duplicate",
                "same_source_semantic_duplicate",
                "cross_source_semantic_duplicate",
                "loose_cross_source_candidate",
            ]
        },
    }


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 중복 정합성 감사",
        "",
        "- 목적: 동일 작품 중복 후보를 원본 ID, URL, 이미지, 의미 기반 기준으로 분리해서 점검",
        f"- 입력: `{summary['input']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 중복/검토 flag 없음: `{summary['ok_rows']:,}`",
        f"- 중복/검토 flag 있음: `{summary['issue_rows']:,}`",
        "",
        "## 1. 출처별 요약",
        "",
        "| 출처 | rows | flag 없음 | flag 있음 | ID 중복 | 같은 출처 의미 중복 | 출처 간 엄격 중복 | 출처 간 느슨한 후보 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in summary["by_source"].items():
        lines.append(
            f"| {source} | `{item['rows']:,}` | `{item['ok_rows']:,}` | `{item['issue_rows']:,}` | "
            f"`{item['same_source_id_duplicate']:,}` | `{item['same_source_semantic_duplicate']:,}` | "
            f"`{item['cross_source_semantic_duplicate']:,}` | `{item['loose_cross_source_candidate']:,}` |"
        )

    lines += [
        "",
        "## 2. 중복 그룹 수",
        "",
        "| 기준 | 그룹 수 | 해석 |",
        "|---|---:|---|",
    ]
    labels = {
        "same_source_id_groups": "같은 출처 안에서 원본 작품 ID가 같은 그룹",
        "same_source_url_groups": "같은 출처 안에서 작품 URL이 같은 그룹",
        "same_source_image_groups": "같은 출처 안에서 이미지 URL이 같은 그룹",
        "same_source_semantic_groups": "같은 출처 안에서 작가+제목+가격+크기가 같은 그룹",
        "cross_source_semantic_groups": "출처가 달라도 작가+제목+가격+크기가 같은 그룹",
        "loose_cross_source_groups": "출처가 달라도 작가+제목+크기가 같은 후보 그룹",
    }
    for key, value in summary["duplicate_group_counts"].items():
        lines.append(f"| `{key}` | `{value:,}` | {labels[key]} |")

    lines += [
        "",
        "## 3. 이슈 카운트",
        "",
        "| 이슈 | 건수 | 해석 |",
        "|---|---:|---|",
    ]
    explanations = {
        "missing_source_artwork_id": "원본 작품 ID 없음",
        "missing_title_key": "제목 key 없음",
        "missing_artist_key": "작가 key 없음",
        "same_source_id_duplicate": "같은 출처 안에서 원본 작품 ID 중복",
        "same_source_url_duplicate": "같은 출처 안에서 URL 중복",
        "same_source_image_duplicate": "같은 출처 안에서 이미지 URL 중복",
        "same_source_semantic_duplicate": "같은 출처 안에서 작가+제목+가격+크기 중복",
        "cross_source_semantic_duplicate": "출처 간 작가+제목+가격+크기 중복",
        "loose_cross_source_candidate": "출처 간 작가+제목+크기 기준 중복 후보",
    }
    for issue, count in sorted(summary["issue_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| `{issue}` | `{count:,}` | {explanations.get(issue, '확인 필요')} |")

    lines += [
        "",
        "## 4. 현재 판단",
        "",
        "- 같은 출처의 원본 ID/URL 중복은 실제 중복 가능성이 높음",
        "- 이미지 URL 중복은 같은 작품일 수도 있지만, 대표 이미지 재사용 가능성이 있어 수동 검토가 필요함",
        "- 작가+제목+가격+크기가 같은 경우는 학습에서 가중치가 중복될 수 있으므로 flag로 관리해야 함",
        "- 출처 간 중복은 삭제보다 우선순위 정책이 필요함",
        "- 가격이나 크기가 조금 다른 출처 간 후보는 별도 검토 후 하나만 대표 row로 선택해야 함",
        "",
        "## 5. 제안 클렌징 규칙",
        "",
        "- 원본 ID가 같은 같은 출처 중복은 대표 1건만 학습 후보로 유지",
        "- URL이 같은 같은 출처 중복도 대표 1건만 학습 후보로 유지",
        "- 같은 출처의 의미 중복은 가격/크기/이미지 샘플 확인 후 대표 1건만 유지",
        "- 출처 간 엄격 중복은 데이터 품질 우선순위를 정해 대표 row를 선택",
        "- 출처 간 느슨한 후보는 자동 삭제하지 않고 `duplicate_review_candidate`로 관리",
        "- 중복 제외 row는 삭제하지 않고 `is_training_candidate=false`, `exclude_reason=duplicate_*`로 남김",
        "",
        "## 6. 다음 단계",
        "",
        "- 중복 대표 row 선택 우선순위 정의",
        "- 이후 출처별 시장 차이 `T4-C6` 감사 진행",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    base = load_base_frame()
    audit = make_audit_frame(base)
    audit.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    summary = build_summary(audit)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary), encoding="utf-8")

    print("Track 4 duplicate consistency audit")
    print(f"rows: {summary['n_rows']:,}")
    print(f"ok: {summary['ok_rows']:,}")
    print(f"issues: {summary['issue_rows']:,}")
    print(f"issue_counts: {summary['issue_counts']}")
    print(f"duplicate_group_counts: {summary['duplicate_group_counts']}")


if __name__ == "__main__":
    main()
