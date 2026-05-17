"""Audit column-level value consistency for Track 4 cleaned data."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track4_primary_market_cleaned_v2.csv"
OUT_SUMMARY_CSV = REPO / "data" / "track4_column_value_consistency_audit.csv"
OUT_SAMPLES_CSV = REPO / "data" / "track4_column_value_issue_samples.csv"
OUT_JSON = REPO / "data" / "track4_column_value_consistency_audit_summary.json"
OUT_MD = REPO / "docs" / "track4" / "audits" / "column_value_consistency_audit.md"

NUMERIC_RULES: dict[str, dict[str, float | None]] = {
    "track4_source_row_index": {"min": 0, "max": None},
    "price_amount_raw": {"min": 0, "max": None},
    "price_krw": {"min": 0, "max": None},
    "width_cm": {"min": 0, "max": 1000},
    "height_cm": {"min": 0, "max": 1000},
    "depth_cm": {"min": 0, "max": 1000},
    "area_cm2": {"min": 0, "max": 1_000_000},
    "aspect_ratio": {"min": 1, "max": 100},
    "birth_year": {"min": 1800, "max": 2026},
    "artist_total_works": {"min": 0, "max": None},
    "artist_followers": {"min": 0, "max": None},
    "artist_followers_log": {"min": 0, "max": None},
    "artist_meta_available_count": {"min": 0, "max": None},
    "artist_key_source_count": {"min": 1, "max": None},
    "artist_slug_name_count": {"min": 0, "max": None},
    "price_bucket_10k": {"min": 0, "max": None},
    "width_bucket_cm": {"min": 0, "max": None},
    "height_bucket_cm": {"min": 0, "max": None},
    "depth_bucket_cm": {"min": 0, "max": None},
    "area_bucket_100cm2": {"min": 0, "max": None},
    "same_source_id_count": {"min": 0, "max": None},
    "same_source_url_count": {"min": 0, "max": None},
    "same_source_image_count": {"min": 0, "max": None},
    "same_source_semantic_count": {"min": 0, "max": None},
    "cross_source_semantic_count": {"min": 0, "max": None},
    "loose_cross_source_count": {"min": 0, "max": None},
    "cross_source_semantic_source_count": {"min": 0, "max": None},
    "loose_cross_source_source_count": {"min": 0, "max": None},
    "ln_price_krw": {"min": 0, "max": None},
    "log_area": {"min": 0, "max": None},
    "artist_works_count_in_cleaned": {"min": 1, "max": None},
    "artist_works_log": {"min": 0, "max": None},
}

BOOLEAN_COLUMNS = {
    "has_depth",
    "is_3d_candidate",
    "is_cross_source_artist_key",
    "is_duplicate_representative",
    "is_training_candidate",
    "is_high_price_candidate",
    "is_extreme_aspect_ratio",
}

REQUIRED_COLUMNS = {
    "track4_source",
    "track4_source_file",
    "track4_source_row_index",
    "price_krw",
    "width_cm",
    "height_cm",
    "artist_name_standardized",
    "artist_name_ko",
    "artist_key",
    "medium_raw",
    "medium_category",
    "support_category",
    "title_raw",
    "is_training_candidate",
}

ALLOWED_VALUES: dict[str, set[str]] = {
    "track4_source": {"saatchi", "artsy", "artue", "gallery_primary"},
    "price_currency": {"", "KRW", "USD", "EUR", "GBP", "HKD"},
    "medium_category": {
        "oil",
        "acrylic",
        "watercolor",
        "ink",
        "gouache",
        "charcoal",
        "pencil",
        "pastel",
        "print",
        "photo",
        "digital",
        "ceramic",
        "sculpture_material",
        "textile",
        "collage",
        "painting_material",
        "mixed_media",
        "other",
        "unknown",
    },
    "support_category": {"canvas", "linen", "paper", "panel", "glass", "wood", "metal", "fabric", "unknown"},
    "gallery_audit_status": {"ok", "missing_gallery_name", "gallery_tier_unmatched", ""},
}

URL_COLUMNS = {"artwork_url", "image_url"}


def is_empty(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().eq("")


def as_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("", np.nan), errors="coerce")


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.lower().map({"true": True, "false": False})


def safe_log(series: pd.Series) -> pd.Series:
    values = series.astype(float).to_numpy()
    out = np.full(values.shape, np.nan, dtype=float)
    mask = np.isfinite(values) & (values > 0)
    out[mask] = np.log(values[mask])
    return pd.Series(out, index=series.index)


def safe_log1p(series: pd.Series) -> pd.Series:
    values = series.astype(float).to_numpy()
    out = np.full(values.shape, np.nan, dtype=float)
    mask = np.isfinite(values) & (values >= 0)
    out[mask] = np.log1p(values[mask])
    return pd.Series(out, index=series.index)


def add_issue_sample(samples: list[dict[str, Any]], df: pd.DataFrame, col: str, issue: str, mask: pd.Series) -> None:
    sample_cols = [
        "track4_source",
        "track4_source_row_index",
        "artist_name_standardized",
        "artist_name_ko",
        "title_raw",
        col,
    ]
    sample_cols = [c for c in sample_cols if c in df.columns]
    for _, row in df.loc[mask, sample_cols].head(10).iterrows():
        item = {"column": col, "issue": issue}
        item.update({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})
        samples.append(item)


def summarize_column(df: pd.DataFrame, col: str, samples: list[dict[str, Any]]) -> dict[str, Any]:
    s = df[col]
    empty = is_empty(s)
    issues: dict[str, int] = {}

    if col in REQUIRED_COLUMNS and empty.any():
        issues["missing_required"] = int(empty.sum())
        add_issue_sample(samples, df, col, "missing_required", empty)

    if col in NUMERIC_RULES:
        nonempty = ~empty
        num = as_number(s)
        invalid_number = nonempty & num.isna()
        if invalid_number.any():
            issues["numeric_parse_fail"] = int(invalid_number.sum())
            add_issue_sample(samples, df, col, "numeric_parse_fail", invalid_number)
        min_value = NUMERIC_RULES[col]["min"]
        max_value = NUMERIC_RULES[col]["max"]
        if min_value is not None:
            below = num.notna() & num.lt(float(min_value))
            if below.any():
                issues[f"below_min_{min_value:g}"] = int(below.sum())
                add_issue_sample(samples, df, col, f"below_min_{min_value:g}", below)
        if max_value is not None:
            above = num.notna() & num.gt(float(max_value))
            if above.any():
                issues[f"above_max_{max_value:g}"] = int(above.sum())
                add_issue_sample(samples, df, col, f"above_max_{max_value:g}", above)

    if col in BOOLEAN_COLUMNS:
        lower = s.fillna("").astype(str).str.strip().str.lower()
        invalid_bool = ~empty & ~lower.isin({"true", "false"})
        if invalid_bool.any():
            issues["boolean_parse_fail"] = int(invalid_bool.sum())
            add_issue_sample(samples, df, col, "boolean_parse_fail", invalid_bool)

    if col in ALLOWED_VALUES:
        invalid_value = ~empty & ~s.astype(str).isin(ALLOWED_VALUES[col])
        if invalid_value.any():
            issues["unexpected_category"] = int(invalid_value.sum())
            add_issue_sample(samples, df, col, "unexpected_category", invalid_value)

    if col in URL_COLUMNS:
        invalid_url = ~empty & ~s.astype(str).str.match(r"^https?://", na=False)
        if invalid_url.any():
            issues["invalid_url_format"] = int(invalid_url.sum())
            add_issue_sample(samples, df, col, "invalid_url_format", invalid_url)

    return {
        "column": col,
        "dtype": str(s.dtype),
        "rows": int(len(s)),
        "missing_rows": int(empty.sum()),
        "missing_rate": float(empty.mean()),
        "unique_values": int(s[~empty].nunique(dropna=True)),
        "issue_rows": int(sum(issues.values())),
        "issues": ";".join(f"{k}={v}" for k, v in sorted(issues.items())),
    }


def derived_checks(df: pd.DataFrame, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, mask: pd.Series, cols: list[str], tolerance_note: str) -> None:
        checks.append(
            {
                "check": name,
                "issue_rows": int(mask.sum()),
                "tolerance": tolerance_note,
            }
        )
        if mask.any():
            sample_cols = [c for c in ["track4_source", "track4_source_row_index", "artist_name_ko", "title_raw"] + cols if c in df.columns]
            for _, row in df.loc[mask, sample_cols].head(10).iterrows():
                item = {"column": "__derived__", "issue": name}
                item.update({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})
                samples.append(item)

    price = as_number(df["price_krw"])
    ln_price = as_number(df["ln_price_krw"])
    ln_expected = safe_log(price)
    add_check(
        "ln_price_krw_mismatch",
        price.notna() & price.gt(0) & ln_price.notna() & (ln_price - ln_expected).abs().gt(1e-6),
        ["price_krw", "ln_price_krw"],
        "abs(diff) > 1e-6",
    )

    width = as_number(df["width_cm"])
    height = as_number(df["height_cm"])
    area = as_number(df["area_cm2"])
    area_expected = width * height
    add_check(
        "area_cm2_mismatch",
        width.notna() & height.notna() & area.notna() & (area - area_expected).abs().gt(1e-6),
        ["width_cm", "height_cm", "area_cm2"],
        "abs(diff) > 1e-6",
    )

    log_area = as_number(df["log_area"])
    log_area_expected = safe_log(area)
    add_check(
        "log_area_mismatch",
        area.notna() & area.gt(0) & log_area.notna() & (log_area - log_area_expected).abs().gt(1e-6),
        ["area_cm2", "log_area"],
        "abs(diff) > 1e-6",
    )

    aspect = as_number(df["aspect_ratio"])
    aspect_expected = np.maximum(width, height) / np.minimum(width, height)
    add_check(
        "aspect_ratio_mismatch",
        width.notna() & height.notna() & width.gt(0) & height.gt(0) & aspect.notna() & (aspect - aspect_expected).abs().gt(1e-6),
        ["width_cm", "height_cm", "aspect_ratio"],
        "abs(diff) > 1e-6",
    )

    depth = as_number(df["depth_cm"])
    has_depth = as_bool(df["has_depth"])
    add_check(
        "has_depth_mismatch",
        has_depth.notna() & (has_depth != depth.fillna(0).gt(0)),
        ["depth_cm", "has_depth"],
        "depth_cm > 0 기준",
    )

    works_count = as_number(df["artist_works_count_in_cleaned"])
    works_log = as_number(df["artist_works_log"])
    works_log_expected = safe_log1p(works_count)
    add_check(
        "artist_works_log_mismatch",
        works_count.notna() & works_log.notna() & (works_log - works_log_expected).abs().gt(1e-6),
        ["artist_works_count_in_cleaned", "artist_works_log"],
        "abs(diff) > 1e-6",
    )

    bucket = df["medium_support_bucket"].fillna("").astype(str)
    expected_bucket = df["medium_category"].fillna("unknown").astype(str) + "__" + df["support_category"].fillna("unknown").astype(str)
    add_check(
        "medium_support_bucket_mismatch",
        bucket.ne(expected_bucket),
        ["medium_category", "support_category", "medium_support_bucket"],
        "medium_category__support_category 기준",
    )

    training = as_bool(df["is_training_candidate"])
    reasons_empty = is_empty(df["cleaning_exclude_reasons"])
    add_check(
        "training_candidate_reason_mismatch",
        training.notna() & (training != reasons_empty),
        ["is_training_candidate", "cleaning_exclude_reasons"],
        "exclude reason 없음 = 학습 후보",
    )

    return checks


def build_summary(df: pd.DataFrame, column_summary: pd.DataFrame, derived: list[dict[str, Any]]) -> dict[str, Any]:
    issue_cols = column_summary[column_summary["issue_rows"].gt(0)].copy()
    training = df[df["is_training_candidate"].fillna("").astype(str).str.lower().eq("true")]
    return {
        "created_at": "2026-05-15",
        "input": str(INPUT.relative_to(REPO)),
        "summary_csv": str(OUT_SUMMARY_CSV.relative_to(REPO)),
        "samples_csv": str(OUT_SAMPLES_CSV.relative_to(REPO)),
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns_with_issues": int(len(issue_cols)),
        "training_candidate_rows": int(len(training)),
        "training_candidate_missing_artist_ko": int(is_empty(training["artist_name_ko"]).sum()) if "artist_name_ko" in training else None,
        "training_candidate_missing_medium": int(training["medium_category"].eq("unknown").sum()) if "medium_category" in training else None,
        "training_candidate_missing_support": int(training["support_category"].eq("unknown").sum()) if "support_category" in training else None,
        "top_column_issues": issue_cols.sort_values("issue_rows", ascending=False).head(20).to_dict("records"),
        "derived_checks": derived,
    }


def render_md(summary: dict[str, Any], column_summary: pd.DataFrame) -> str:
    lines = [
        "# Track 4 컬럼별 값 정합성 감사",
        "",
        "- 목적: cleaned_v2 전체 컬럼에서 값 타입, 범위, 파생값 계산, 필수값 누락 여부를 재점검",
        f"- 입력: `{summary['input']}`",
        f"- 컬럼별 요약 CSV: `{summary['summary_csv']}`",
        f"- 이슈 샘플 CSV: `{summary['samples_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 전체 columns: `{summary['n_columns']:,}`",
        f"- 이슈가 있는 columns: `{summary['columns_with_issues']:,}`",
        "",
        "## 1. 핵심 결론",
        "",
        f"- 학습 후보 rows: `{summary['training_candidate_rows']:,}`",
        f"- 학습 후보 중 한글 작가명 누락: `{summary['training_candidate_missing_artist_ko']:,}`",
        f"- 학습 후보 중 `medium_category=unknown`: `{summary['training_candidate_missing_medium']:,}`",
        f"- 학습 후보 중 `support_category=unknown`: `{summary['training_candidate_missing_support']:,}`",
        "",
        "## 2. 컬럼별 주요 이슈",
        "",
        "| 컬럼 | 결측 rows | 고유값 수 | 이슈 rows | 이슈 내용 |",
        "|---|---:|---:|---:|---|",
    ]
    top = column_summary[column_summary["issue_rows"].gt(0)].sort_values("issue_rows", ascending=False).head(30)
    for _, row in top.iterrows():
        lines.append(
            f"| `{row['column']}` | `{int(row['missing_rows']):,}` | `{int(row['unique_values']):,}` | "
            f"`{int(row['issue_rows']):,}` | {row['issues'] or '-'} |"
        )

    lines += [
        "",
        "## 3. 파생값 계산 검증",
        "",
        "| 검증 항목 | 이슈 rows | 기준 |",
        "|---|---:|---|",
    ]
    for item in summary["derived_checks"]:
        lines.append(f"| `{item['check']}` | `{item['issue_rows']:,}` | {item['tolerance']} |")

    lines += [
        "",
        "## 4. 해석",
        "",
        "- `support_category=unknown`은 대량으로 남아 있어 모델 피처로 쓸 경우 별도 실험 또는 보수적 처리 필요",
        "- `gallery_audit_status`의 unmatched/missing은 갤러리 메타 참고용 이슈이며 현재 모델 피처에서는 제외",
        "- `depth_cm` 결측은 2D 작품에서 자연스러운 결측일 수 있으므로 단순 오류로 보지 않고 `has_depth`로 관리",
        "- 파생값 불일치가 0이면 클렌징 후 계산 컬럼은 재현 가능한 상태로 판단",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    df = pd.read_csv(INPUT, dtype="string", keep_default_na=False, low_memory=False)
    samples: list[dict[str, Any]] = []
    rows = [summarize_column(df, col, samples) for col in df.columns]
    column_summary = pd.DataFrame(rows)
    derived = derived_checks(df, samples)
    summary = build_summary(df, column_summary, derived)

    column_summary.to_csv(OUT_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    pd.DataFrame(samples).to_csv(OUT_SAMPLES_CSV, index=False, encoding="utf-8-sig")
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary, column_summary), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
