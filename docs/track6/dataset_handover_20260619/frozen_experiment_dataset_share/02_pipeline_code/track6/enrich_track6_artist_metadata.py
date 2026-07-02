#!/usr/bin/env python3
"""Attach standardized collected artist metadata to the Track6 clean dataset.

The metadata is copied from raw collected source rows using
`track4_source + track4_source_row_index`. These columns are retained in the
full clean/split files for audit and later artist-DB feature experiments, but
the feature export script excludes the `artist_meta_` prefix by default.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"
RAW = REPO / "data" / "track4_primary_market_raw_collected.csv"
OUT = INPUT
OUT_SUMMARY = REPO / "data" / "track6" / "quality" / "track6_artist_metadata_enrichment_summary.json"
OUT_REPORT = REPO / "docs" / "track6" / "dataset" / "artist_metadata_enrichment_report.md"

KEYS = ["track4_source", "track4_source_row_index"]
META_COLUMNS = [
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_nationality_ko",
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_age",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
]


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return " ".join(text.split())


def first_nonempty(row: pd.Series, cols: list[str]) -> str:
    for col in cols:
        if col in row.index:
            value = clean_text(row[col])
            if value:
                return value
    return ""


def to_number(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null"}:
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def first_number(row: pd.Series, cols: list[str]) -> float:
    for col in cols:
        if col in row.index:
            value = to_number(row[col])
            if not np.isnan(value):
                return value
    return np.nan


def bool_or_na(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        if float(value) == 1.0:
            return True
        if float(value) == 0.0:
            return False
    text = str(value).strip().lower()
    if text in {"true", "1", "1.0", "yes", "y"}:
        return True
    if text in {"false", "0", "0.0", "no", "n"}:
        return False
    return pd.NA


def build_artist_meta(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        source = clean_text(row.get("track4_source"))
        meta = {
            "track4_source": source,
            "track4_source_row_index": row.get("track4_source_row_index"),
            "artist_meta_source": source,
            "artist_meta_nationality": "",
            "artist_meta_nationality_ko": "",
            "artist_meta_birth_year": np.nan,
            "artist_meta_total_works": np.nan,
            "artist_meta_for_sale_works": np.nan,
            "artist_meta_followers": np.nan,
            "artist_meta_for_sale_ratio": np.nan,
            "artist_meta_career_age": np.nan,
            "artist_meta_career_stage": "",
            "artist_meta_is_p1": pd.NA,
            "artist_meta_has_international": pd.NA,
        }

        if source == "saatchi":
            meta["artist_meta_birth_year"] = first_number(row, ["saatchi__artist_birth_year"])
            meta["artist_meta_total_works"] = first_number(row, ["saatchi__artist_total_works"])
            meta["artist_meta_for_sale_ratio"] = first_number(row, ["saatchi__for_sale_ratio"])
            meta["artist_meta_career_age"] = first_number(row, ["saatchi__career_age"])
            meta["artist_meta_career_stage"] = first_nonempty(row, ["saatchi__career_stage"])
            meta["artist_meta_is_p1"] = bool_or_na(row.get("saatchi__artist_is_p1"))
            meta["artist_meta_has_international"] = bool_or_na(row.get("saatchi__has_international"))
            ln_followers = first_number(row, ["saatchi__ln_followers"])
            if not np.isnan(ln_followers):
                meta["artist_meta_followers"] = max(0, round(float(np.expm1(ln_followers))))

        elif source == "artsy":
            meta["artist_meta_nationality"] = first_nonempty(row, ["artsy__artist_nationality"])
            meta["artist_meta_birth_year"] = first_number(row, ["artsy__artist_birth_year"])
            meta["artist_meta_total_works"] = first_number(row, ["artsy__artist_total_works"])
            meta["artist_meta_for_sale_works"] = first_number(row, ["artsy__artist_for_sale"])
            meta["artist_meta_followers"] = first_number(row, ["artsy__artist_followers"])
            meta["artist_meta_is_p1"] = bool_or_na(row.get("artsy__artist_is_p1"))

        elif source == "artue":
            meta["artist_meta_nationality"] = first_nonempty(row, ["artue__Nationality"])
            meta["artist_meta_nationality_ko"] = first_nonempty(row, ["artue__Nationality KO"])

        elif source == "gallery_primary":
            meta["artist_meta_nationality_ko"] = first_nonempty(row, ["gallery_primary__국적"])
            meta["artist_meta_birth_year"] = first_number(row, ["gallery_primary__birth_year"])

        rows.append(meta)

    meta_df = pd.DataFrame(rows)
    if meta_df.duplicated(KEYS).any():
        raise ValueError("artist metadata join keys are not unique")
    return meta_df


def render_report(summary: dict) -> str:
    lines = [
        "# Track 6 작가 메타데이터 보강 보고서",
        "",
        f"- 생성일: `{summary['created_at']}`",
        f"- 입력 정제 데이터: `{summary['input']}`",
        f"- 원본 raw 데이터: `{summary['raw']}`",
        f"- 출력: `{summary['output']}`",
        f"- 전체 rows: `{summary['rows']:,}`",
        f"- 작가 메타가 1개 이상 붙은 rows: `{summary['rows_with_any_artist_meta']:,}`",
        "",
        "## 1. 처리 원칙",
        "",
        "- raw 수집본의 `track4_source + track4_source_row_index`로 row 단위 매칭",
        "- source별 작가 정보 컬럼을 `artist_meta_` 표준 prefix로 통합",
        "- 팔로워/작품 수/판매 중 작품 수 등은 수집된 경우만 보존",
        "- 값이 없는 source는 빈칸으로 둠",
        "- 현재 모델 feature export에서는 `artist_meta_` 컬럼을 기본 제외함",
        "- 추후 작가 DB 연동 또는 별도 가설 실험에서만 명시적으로 사용",
        "",
        "## 2. 추가 컬럼",
        "",
    ]
    for col in META_COLUMNS:
        coverage = summary["coverage"].get(col, 0)
        lines.append(f"- `{col}`: `{coverage:,}` rows")
    lines += [
        "",
        "## 3. source별 작가 메타 보유 rows",
        "",
        "| source | rows | any artist meta rows |",
        "|---|---:|---:|",
    ]
    for source, item in summary["source_summary"].items():
        lines.append(f"| `{source}` | `{item['rows']:,}` | `{item['rows_with_any_artist_meta']:,}` |")
    lines += [
        "",
        "## 4. 주의",
        "",
        "- 이 컬럼들은 운영에서 항상 들어오는 입력값이 아님",
        "- 따라서 기본 모델에는 자동 투입하지 않음",
        "- 작가 DB가 준비되면 Warm 전용 또는 신뢰도 판단용 피처로 별도 실험 필요",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(INPUT, low_memory=False)
    raw = pd.read_csv(RAW, low_memory=False)
    missing = set(KEYS) - set(df.columns) | set(KEYS) - set(raw.columns)
    if missing:
        raise ValueError(f"missing join columns: {sorted(missing)}")

    base = df.drop(columns=[col for col in META_COLUMNS if col in df.columns], errors="ignore")
    meta = build_artist_meta(raw)
    out = base.merge(meta, on=KEYS, how="left", validate="one_to_one")

    has_any = out[META_COLUMNS].notna() & out[META_COLUMNS].astype(str).ne("")
    has_any_rows = has_any.any(axis=1)
    coverage = {col: int((out[col].notna() & out[col].astype(str).ne("")).sum()) for col in META_COLUMNS}
    source_summary = {}
    for source, group in out.groupby("track4_source", dropna=False):
        group_has_any = has_any_rows.loc[group.index]
        source_summary[str(source)] = {
            "rows": int(len(group)),
            "rows_with_any_artist_meta": int(group_has_any.sum()),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")

    summary = {
        "created_at": date.today().isoformat(),
        "input": str(INPUT.relative_to(REPO)),
        "raw": str(RAW.relative_to(REPO)),
        "output": str(OUT.relative_to(REPO)),
        "rows": int(len(out)),
        "rows_with_any_artist_meta": int(has_any_rows.sum()),
        "coverage": coverage,
        "source_summary": source_summary,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_REPORT.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
