"""Audit Track 4 primary-market raw unified dataset.

The goal is not to clean data yet. This script finds suspicious values so the
cleaning rules can be decided from evidence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DATA_PATH = REPO / "data" / "track4_primary_market_raw_unified.csv"
OUT_JSON = REPO / "data" / "track4_primary_market_column_audit.json"
OUT_MD = REPO / "docs" / "track4" / "dataset" / "primary_market_column_audit.md"

NUMERIC_COLS = [
    "year_made",
    "width_cm",
    "height_cm",
    "depth_cm",
    "has_depth",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "estimated_ho",
    "price_krw",
    "ln_price",
    "is_excluded_for_training",
]

TEXT_COLS = [
    "source",
    "source_file",
    "source_artwork_id",
    "artist_name_raw",
    "artist_slug",
    "title",
    "medium_raw",
    "medium_category",
    "support_category",
    "price_raw",
    "price_currency",
    "artwork_url",
    "image_url",
    "gallery_name",
    "gallery_tier",
    "exclude_reason",
]


def pct(n: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(n / total, 6)


def as_jsonable(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def row_sample(df: pd.DataFrame, mask: pd.Series, limit: int = 12) -> list[dict[str, Any]]:
    cols = [
        "source",
        "source_artwork_id",
        "artist_name_raw",
        "title",
        "medium_raw",
        "width_cm",
        "height_cm",
        "depth_cm",
        "price_krw",
        "price_raw",
        "artwork_url",
    ]
    cols = [c for c in cols if c in df.columns]
    sample = df.loc[mask, cols].head(limit)
    return [
        {col: as_jsonable(row[col]) for col in cols}
        for _, row in sample.iterrows()
    ]


def numeric_profile(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in NUMERIC_COLS:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        valid = s.dropna()
        profile: dict[str, Any] = {
            "missing_count": int(s.isna().sum()),
            "missing_rate": pct(int(s.isna().sum()), len(df)),
            "non_null_count": int(valid.size),
        }
        if len(valid):
            profile.update(
                {
                    "min": float(valid.min()),
                    "q01": float(valid.quantile(0.01)),
                    "q05": float(valid.quantile(0.05)),
                    "median": float(valid.median()),
                    "q95": float(valid.quantile(0.95)),
                    "q99": float(valid.quantile(0.99)),
                    "max": float(valid.max()),
                }
            )
        out[col] = profile
    return out


def text_profile(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in TEXT_COLS:
        if col not in df.columns:
            continue
        s = df[col]
        non_null = s.dropna().astype(str)
        blanks = non_null.str.strip().eq("").sum()
        top_values = non_null.value_counts(dropna=False).head(15)
        out[col] = {
            "missing_count": int(s.isna().sum()),
            "missing_rate": pct(int(s.isna().sum()), len(df)),
            "blank_count": int(blanks),
            "unique_count": int(non_null.nunique()),
            "top_values": {str(k): int(v) for k, v in top_values.items()},
        }
    return out


def issue_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    price = pd.to_numeric(df["price_krw"], errors="coerce")
    width = pd.to_numeric(df["width_cm"], errors="coerce")
    height = pd.to_numeric(df["height_cm"], errors="coerce")
    depth = pd.to_numeric(df["depth_cm"], errors="coerce")
    area = pd.to_numeric(df["area_cm2"], errors="coerce")
    aspect = pd.to_numeric(df["aspect_ratio"], errors="coerce")
    year = pd.to_numeric(df["year_made"], errors="coerce")
    title = df["title"].fillna("").astype(str)
    artist = df["artist_name_raw"].fillna("").astype(str)
    medium = df["medium_raw"].fillna("").astype(str)
    artwork_url = df["artwork_url"].fillna("").astype(str)
    image_url = df["image_url"].fillna("").astype(str)

    url_like = r"https?://|www\."
    price_like = r"₩|\\$|\\b(?:usd|krw|eur|gbp)\\b|\\d{1,3}(?:,\\d{3})+"
    size_like = r"\d+(?:\\.\\d+)?\\s*[x×]\\s*\\d+"

    return {
        "price_missing_or_non_positive": price.isna() | (price <= 0),
        "price_too_low_under_10000": price.notna() & (price < 10_000),
        "price_extreme_over_1b": price.notna() & (price > 1_000_000_000),
        "price_extreme_over_100m": price.notna() & (price > 100_000_000),
        "width_height_missing": width.isna() | height.isna(),
        "width_or_height_non_positive": (width.notna() & (width <= 0)) | (height.notna() & (height <= 0)),
        "width_or_height_extreme_over_1000cm": (width > 1000) | (height > 1000),
        "area_mismatch": area.notna() & width.notna() & height.notna() & ((width * height - area).abs() > 0.01),
        "aspect_extreme_under_0_05_or_over_20": aspect.notna() & ((aspect < 0.05) | (aspect > 20)),
        "depth_negative": depth.notna() & (depth < 0),
        "depth_extreme_over_300cm": depth.notna() & (depth > 300),
        "has_depth_mismatch": ((df["has_depth"] == 1) & (depth.fillna(0) <= 0)) | ((df["has_depth"] == 0) & (depth.fillna(0) > 0)),
        "year_future_after_2026": year.notna() & (year > 2026),
        "year_too_old_before_1000": year.notna() & (year < 1000),
        "artist_empty": artist.str.strip().eq(""),
        "artist_contains_price_or_size": artist.str.contains(price_like, case=False, regex=True) | artist.str.contains(size_like, case=False, regex=True),
        "title_empty": title.str.strip().eq(""),
        "title_contains_url": title.str.contains(url_like, case=False, regex=True),
        "medium_contains_price": medium.str.contains(price_like, case=False, regex=True),
        "medium_contains_url": medium.str.contains(url_like, case=False, regex=True),
        "artwork_url_not_url": artwork_url.ne("") & ~artwork_url.str.contains(url_like, case=False, regex=True),
        "image_url_not_url": image_url.ne("") & ~image_url.str.contains(url_like, case=False, regex=True),
    }


def issue_report(df: pd.DataFrame) -> dict[str, Any]:
    masks = issue_masks(df)
    out = {}
    for name, mask in masks.items():
        count = int(mask.sum())
        out[name] = {
            "count": count,
            "rate": pct(count, len(df)),
            "by_source": {str(k): int(v) for k, v in df.loc[mask, "source"].value_counts().items()},
            "samples": row_sample(df, mask),
        }
    return out


def duplicate_report(df: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if "source_artwork_id" in df.columns:
        mask = df.duplicated(["source", "source_artwork_id"], keep=False)
        result["source_artwork_id_duplicates"] = {
            "count": int(mask.sum()),
            "groups": int(df.loc[mask, ["source", "source_artwork_id"]].drop_duplicates().shape[0]),
            "samples": row_sample(df, mask),
        }

    key_cols = ["source", "artist_name_raw", "title", "price_krw", "width_cm", "height_cm"]
    mask = df.duplicated(key_cols, keep=False)
    result["semantic_duplicates"] = {
        "count": int(mask.sum()),
        "groups": int(df.loc[mask, key_cols].drop_duplicates().shape[0]),
        "samples": row_sample(df, mask),
    }
    return result


def source_report(df: pd.DataFrame) -> dict[str, Any]:
    out = {}
    for source, group in df.groupby("source"):
        price = pd.to_numeric(group["price_krw"], errors="coerce")
        out[str(source)] = {
            "rows": int(len(group)),
            "artists": int(group["artist_name_raw"].nunique()),
            "price_median": float(price.median()),
            "price_q25": float(price.quantile(0.25)),
            "price_q75": float(price.quantile(0.75)),
            "price_max": float(price.max()),
            "width_missing_rate": pct(int(group["width_cm"].isna().sum()), len(group)),
            "height_missing_rate": pct(int(group["height_cm"].isna().sum()), len(group)),
            "depth_missing_rate": pct(int(group["depth_cm"].isna().sum()), len(group)),
            "estimated_ho_missing_rate": pct(int(group["estimated_ho"].isna().sum()), len(group)),
        }
    return out


def render_md(audit: dict[str, Any]) -> str:
    issues = audit["issues"]
    high = sorted(issues.items(), key=lambda kv: kv[1]["count"], reverse=True)
    lines = [
        "# Track 4 1차 시장 raw 통합본 컬럼 감사",
        "",
        "- 목적: 크롤링/수집 데이터가 공통 schema로 들어오면서 컬럼 밀림, 오입력, 이상값이 생겼는지 점검",
        f"- 기준 파일: `{audit['input']}`",
        f"- 전체 rows: `{audit['n_rows']:,}`",
        f"- 전체 columns: `{audit['n_columns']}`",
        "",
        "## 1. 출처별 요약",
        "",
        "| 출처 | rows | 작가 수 | 가격 중앙값 | 가격 Q25 | 가격 Q75 | 최대 가격 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in audit["source_report"].items():
        lines.append(
            f"| {source} | `{item['rows']:,}` | `{item['artists']:,}` | "
            f"`{item['price_median']:,.0f}` | `{item['price_q25']:,.0f}` | "
            f"`{item['price_q75']:,.0f}` | `{item['price_max']:,.0f}` |"
        )

    lines += [
        "",
        "## 2. 주요 이상 신호",
        "",
        "| 점검 항목 | 건수 | 비율 | 주요 출처 | 해석 |",
        "|---|---:|---:|---|---|",
    ]
    explanations = {
        "price_extreme_over_100m": "고가 이상치 후보. gallery_primary와 일부 Artsy 가격대 확인 필요",
        "price_extreme_over_1b": "초고가 이상치 후보. 학습 제외 또는 별도 구간 검토 필요",
        "price_too_low_under_10000": "가격 파싱 오류 또는 테스트/자리표시값 가능성",
        "width_height_missing": "크기 파싱 실패 또는 원본 크기 결측",
        "width_or_height_extreme_over_1000cm": "크기 단위 오류 또는 컬럼 오입력 가능성",
        "aspect_extreme_under_0_05_or_over_20": "가로/세로 중 하나가 잘못 들어갔을 가능성",
        "depth_extreme_over_300cm": "깊이 단위 오류 또는 설치/조각 작품 가능성",
        "artist_contains_price_or_size": "작가명 컬럼에 가격/크기 문자열이 들어간 컬럼 밀림 의심",
        "medium_contains_price": "재료 컬럼에 가격 문자열이 들어간 컬럼 밀림 의심",
        "title_empty": "작품명 결측",
        "artwork_url_not_url": "URL 컬럼에 URL이 아닌 값이 들어감",
        "image_url_not_url": "이미지 URL 컬럼에 URL이 아닌 값이 들어감",
    }
    for name, item in high:
        if item["count"] == 0:
            continue
        by_source = ", ".join(f"{k}:{v}" for k, v in item["by_source"].items())
        lines.append(
            f"| `{name}` | `{item['count']:,}` | `{item['rate']:.2%}` | {by_source} | "
            f"{explanations.get(name, '확인 필요')} |"
        )

    lines += [
        "",
        "## 3. 컬럼별 결측률",
        "",
        "| 컬럼 | 결측 수 | 결측률 | unique/top 또는 범위 |",
        "|---|---:|---:|---|",
    ]
    for col, item in audit["numeric_profile"].items():
        desc = "-"
        if item["non_null_count"]:
            desc = f"min `{item['min']:,.3f}`, median `{item['median']:,.3f}`, max `{item['max']:,.3f}`"
        lines.append(f"| `{col}` | `{item['missing_count']:,}` | `{item['missing_rate']:.2%}` | {desc} |")
    for col, item in audit["text_profile"].items():
        tops = list(item["top_values"].items())[:3]
        desc = ", ".join(f"`{k}`:{v}" for k, v in tops)
        lines.append(f"| `{col}` | `{item['missing_count']:,}` | `{item['missing_rate']:.2%}` | {desc} |")

    lines += [
        "",
        "## 4. 중복 점검",
        "",
    ]
    for name, item in audit["duplicates"].items():
        lines.append(f"- `{name}`: rows `{item['count']:,}`, groups `{item['groups']:,}`")

    lines += [
        "",
        "## 5. 현재 판단",
        "",
        "- raw 통합본은 바로 학습에 쓰면 안 됨",
        "- 가격 이상치, 낮은 가격, 크기 이상값, URL 오입력, 출처별 가격대 차이를 먼저 정리해야 함",
        "- 컬럼 밀림으로 강하게 의심되는 항목은 현재 자동 점검 기준상 많지 않지만, 가격/크기/URL 이상값 샘플을 수동 확인해야 함",
        "- 다음 단계는 감사 결과를 기준으로 `track4_primary_market_cleaned_v1.csv` 생성 규칙을 확정하는 것임",
        "",
        "## 6. 원본 감사 JSON",
        "",
        f"- `{audit['json_output']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    audit = {
        "created_at": "2026-05-15",
        "input": str(DATA_PATH.relative_to(REPO)),
        "json_output": str(OUT_JSON.relative_to(REPO)),
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "columns": list(df.columns),
        "source_report": source_report(df),
        "numeric_profile": numeric_profile(df),
        "text_profile": text_profile(df),
        "issues": issue_report(df),
        "duplicates": duplicate_report(df),
    }
    OUT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(audit), encoding="utf-8")

    print("Track 4 primary-market column audit")
    print(f"input: {DATA_PATH.relative_to(REPO)}")
    print(f"json: {OUT_JSON.relative_to(REPO)}")
    print(f"md: {OUT_MD.relative_to(REPO)}")
    for name, item in sorted(audit["issues"].items(), key=lambda kv: kv[1]["count"], reverse=True)[:10]:
        print(f"{name}: {item['count']:,} ({item['rate']:.2%})")


if __name__ == "__main__":
    main()
