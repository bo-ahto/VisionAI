#!/usr/bin/env python3
"""Validate Track 6 split files at column level.

This check runs before model experiments. It verifies schema consistency,
required values, numeric ranges, derived-column consistency, split leakage,
and category domains for the fixed Track6 datasets.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track6_split"
OUT_DIR = REPO / "data" / "track6" / "quality"
OUT_JSON = OUT_DIR / "track6_column_quality_report.json"
OUT_MD = REPO / "docs" / "track6" / "dataset" / "column_quality_report.md"
OUT_ISSUES = OUT_DIR / "track6_column_quality_issues.csv"

SPLITS = ["train", "val_warm", "test_warm", "val_cold", "test_cold"]
ESSENTIAL_COLUMNS = [
    "artist_key",
    "artist_name_ko",
    "artist_name_ko_orig",
    "price_krw",
    "ln_price_krw",
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "artist_works_log",
    "artist_works_count_train",
    "_track6_row_id",
]
BOOLEAN_COLUMNS = [
    "has_depth",
    "is_3d_candidate",
    "is_high_price_candidate",
    "is_extreme_aspect_ratio",
    "is_training_candidate",
    "is_homonym",
]
CATEGORY_COLUMNS = ["medium_category", "support_category", "medium_support_bucket"]
TRACKING_ONLY_COLUMNS = [
    "track4_source",
    "track4_source_row_index",
    "source_artwork_id",
    "artwork_url",
    "image_url",
]
PRICE_MIN = 10_000
PRICE_MAX = 1_000_000_000
WIDTH_HEIGHT_REVIEW_MAX = 500
DEPTH_REVIEW_MAX = 500
ASPECT_REVIEW_MAX = 8
FORMULA_TOL = 1e-6


def load_splits() -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(SPLIT_DIR / f"track6_{name}.csv", low_memory=False) for name in SPLITS}


def load_full_cleaned() -> pd.DataFrame:
    return pd.read_csv(REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv", low_memory=False)


def bool_bad_count(series: pd.Series) -> int:
    values = series.dropna().astype(str).str.lower().str.strip()
    return int((~values.isin(["true", "false"])).sum())


def issue(split: str, column: str, check: str, count: int, severity: str, note: str = "") -> dict[str, Any]:
    return {
        "split": split,
        "column": column,
        "check": check,
        "count": int(count),
        "severity": severity,
        "note": note,
    }


def validate_split(name: str, df: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    info: dict[str, Any] = {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()) if "artist_key" in df else None,
        "columns": int(len(df.columns)),
        "missing": {},
        "numeric": {},
        "categories": {},
    }

    missing_cols = [col for col in ESSENTIAL_COLUMNS if col not in df.columns]
    for col in missing_cols:
        issues.append(issue(name, col, "required_column_missing", len(df), "fail"))
    if missing_cols:
        return info, issues

    for col in ESSENTIAL_COLUMNS:
        if col == "depth_cm":
            has_depth = df["has_depth"].astype(str).str.lower().eq("true")
            missing_mask = df[col].isna() | df[col].astype(str).str.strip().eq("")
            missing = int((missing_mask & has_depth).sum())
            info["missing"]["depth_cm_all_rows_blank"] = int(missing_mask.sum())
        else:
            missing = int(df[col].isna().sum() + df[col].astype(str).str.strip().eq("").sum())
        info["missing"][col] = missing
        if missing:
            issues.append(issue(name, col, "essential_missing_or_blank", missing, "fail"))

    if "title_raw" in df.columns:
        title_missing = int(df["title_raw"].isna().sum() + df["title_raw"].astype(str).str.strip().eq("").sum())
        info["missing"]["title_raw"] = title_missing
        if title_missing:
            issues.append(issue(name, "title_raw", "title_missing_or_blank", title_missing, "review", "모델 피처는 아니지만 중복/감사용 확인 필요"))

    for col in ["price_krw", "ln_price_krw", "width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if col == "depth_cm":
            has_depth = df["has_depth"].astype(str).str.lower().eq("true")
            non_numeric = int(numeric[has_depth].isna().sum())
            finite_bad = int((~np.isfinite(numeric[has_depth])).sum())
        else:
            non_numeric = int(numeric.isna().sum())
            finite_bad = int((~np.isfinite(numeric)).sum())
        info["numeric"][col] = {
            "min": float(numeric.min()) if len(numeric) else None,
            "median": float(numeric.median()) if len(numeric) else None,
            "p90": float(numeric.quantile(0.90)) if len(numeric) else None,
            "max": float(numeric.max()) if len(numeric) else None,
        }
        if non_numeric:
            issues.append(issue(name, col, "non_numeric_or_missing", non_numeric, "fail"))
        if finite_bad:
            issues.append(issue(name, col, "non_finite", finite_bad, "fail"))

    price = pd.to_numeric(df["price_krw"], errors="coerce")
    low_price = int((price < PRICE_MIN).sum())
    high_price = int((price > PRICE_MAX).sum())
    if low_price:
        issues.append(issue(name, "price_krw", "below_price_min", low_price, "fail", f"< {PRICE_MIN:,}"))
    if high_price:
        issues.append(issue(name, "price_krw", "above_price_max", high_price, "fail", f"> {PRICE_MAX:,}"))

    width = pd.to_numeric(df["width_cm"], errors="coerce")
    height = pd.to_numeric(df["height_cm"], errors="coerce")
    depth = pd.to_numeric(df["depth_cm"], errors="coerce")
    area = pd.to_numeric(df["area_cm2"], errors="coerce")
    log_area = pd.to_numeric(df["log_area"], errors="coerce")
    aspect = pd.to_numeric(df["aspect_ratio"], errors="coerce")
    ln_price = pd.to_numeric(df["ln_price_krw"], errors="coerce")

    aspect_expected = np.maximum(width / height, height / width)
    has_depth = df["has_depth"].astype(str).str.lower().eq("true")
    checks = {
        "width_non_positive": int((width <= 0).sum()),
        "height_non_positive": int((height <= 0).sum()),
        "depth_negative": int((depth[has_depth] < 0).sum()),
        "area_non_positive": int((area <= 0).sum()),
        "log_area_mismatch": int((np.abs(log_area - np.log(area)) > FORMULA_TOL).sum()),
        "area_mismatch": int((np.abs(area - (width * height)) > 1e-4).sum()),
        "aspect_ratio_mismatch": int((np.abs(aspect - aspect_expected) > FORMULA_TOL).sum()),
        "ln_price_mismatch": int((np.abs(ln_price - np.log(price)) > FORMULA_TOL).sum()),
    }
    for check, count in checks.items():
        if count:
            column = check.split("_")[0]
            issues.append(issue(name, column, check, count, "fail"))
    info["formula_checks"] = checks

    review_ranges = {
        "width_above_review_max": int((width > WIDTH_HEIGHT_REVIEW_MAX).sum()),
        "height_above_review_max": int((height > WIDTH_HEIGHT_REVIEW_MAX).sum()),
        "depth_above_review_max": int((depth[has_depth] > DEPTH_REVIEW_MAX).sum()),
        "aspect_ratio_above_review_max": int((aspect > ASPECT_REVIEW_MAX).sum()),
    }
    info["review_range_checks"] = review_ranges
    for check, count in review_ranges.items():
        if count:
            column = check.split("_above")[0]
            issues.append(issue(name, column, check, count, "review", "극단값 후보. 모델 제외가 아니라 slice 확인 대상"))

    for col in BOOLEAN_COLUMNS:
        if col not in df.columns:
            continue
        bad = bool_bad_count(df[col])
        if bad:
            issues.append(issue(name, col, "boolean_domain_invalid", bad, "fail"))

    for col in CATEGORY_COLUMNS:
        if col not in df.columns:
            continue
        values = df[col].fillna("").astype(str).str.strip()
        unknown = int(values.str.lower().isin(["", "unknown", "nan", "none"]).sum())
        info["categories"][col] = {
            "unique": int(values.nunique()),
            "unknown_or_blank": unknown,
            "top_values": values.value_counts().head(10).to_dict(),
        }
        if unknown:
            severity = "review" if col in ["support_category", "medium_category"] else "info"
            issues.append(issue(name, col, "unknown_or_blank_category", unknown, severity))

    duplicate_row_ids = int(df["_track6_row_id"].duplicated().sum())
    if duplicate_row_ids:
        issues.append(issue(name, "_track6_row_id", "duplicate_within_split", duplicate_row_ids, "fail"))

    return info, issues


def validate_cross_split(splits: dict[str, pd.DataFrame]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    train = splits["train"]
    train_keys = set(train["artist_key"].astype(str))
    train_names = set(train["artist_name_ko"].dropna().astype(str))
    train_orig_names = set(train["artist_name_ko_orig"].dropna().astype(str))

    all_membership = pd.concat(
        [frame[["_track6_row_id"]].assign(split=name) for name, frame in splits.items()],
        ignore_index=True,
    )
    repeated_rows = int(all_membership["_track6_row_id"].duplicated().sum())
    if repeated_rows:
        issues.append(issue("all", "_track6_row_id", "duplicate_across_splits", repeated_rows, "fail"))

    checks: dict[str, Any] = {"duplicate_across_splits": repeated_rows}
    for name in ["val_warm", "test_warm"]:
        frame = splits[name]
        warm_artist_missing = int((~frame["artist_key"].astype(str).isin(train_keys)).sum())
        min_train_count = int(frame["artist_works_count_train"].min()) if len(frame) else 0
        one_work_artists = int((frame["artist_key"].value_counts() == 1).sum())
        checks[f"{name}_artist_missing_from_train"] = warm_artist_missing
        checks[f"{name}_min_train_count"] = min_train_count
        checks[f"{name}_one_work_artists"] = one_work_artists
        if warm_artist_missing:
            issues.append(issue(name, "artist_key", "warm_artist_missing_from_train", warm_artist_missing, "fail"))
        if min_train_count < 5:
            issues.append(issue(name, "artist_works_count_train", "stable_warm_train_count_below_5", min_train_count, "fail"))
        if one_work_artists:
            issues.append(issue(name, "artist_key", "warm_one_work_artist", one_work_artists, "fail"))

    for name in ["val_cold", "test_cold"]:
        frame = splits[name]
        artist_overlap = len(set(frame["artist_key"].astype(str)) & train_keys)
        name_overlap = len(set(frame["artist_name_ko"].dropna().astype(str)) & train_names)
        orig_name_overlap = len(set(frame["artist_name_ko_orig"].dropna().astype(str)) & train_orig_names)
        nonzero_history = int((frame["artist_works_count_train"] > 0).sum())
        checks[f"{name}_artist_overlap"] = int(artist_overlap)
        checks[f"{name}_name_overlap"] = int(name_overlap)
        checks[f"{name}_orig_name_overlap"] = int(orig_name_overlap)
        checks[f"{name}_nonzero_artist_history"] = nonzero_history
        for check, count in [
            ("cold_artist_overlap_train", artist_overlap),
            ("cold_name_overlap_train", name_overlap),
            ("cold_orig_name_overlap_train", orig_name_overlap),
            ("cold_nonzero_artist_history", nonzero_history),
        ]:
            if count:
                issues.append(issue(name, "artist_key", check, count, "fail"))

    return checks, issues


def training_candidate_audit(df: pd.DataFrame) -> dict[str, Any]:
    candidate = df["is_training_candidate"].astype(str).str.lower().str.strip().isin(["true", "1"])
    reasons = df["cleaning_exclude_reasons"].fillna("").astype(str).str.strip()
    reason_empty = reasons.eq("")
    mismatch = candidate.ne(reason_empty)
    false_reasons = reasons.loc[~candidate]
    reason_counts: dict[str, int] = {}
    for value in false_reasons:
        for reason in str(value).split(";"):
            reason = reason.strip()
            if reason:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "total_rows": int(len(df)),
        "training_candidate_true": int(candidate.sum()),
        "training_candidate_false": int((~candidate).sum()),
        "false_reason_blank_rows": int((~candidate & reason_empty).sum()),
        "true_reason_nonblank_rows": int((candidate & ~reason_empty).sum()),
        "candidate_reason_mismatch_rows": int(mismatch.sum()),
        "reason_counts": dict(sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))),
    }


def render_markdown(report: dict[str, Any], issues: list[dict[str, Any]]) -> str:
    fail_count = sum(1 for item in issues if item["severity"] == "fail")
    review_count = sum(1 for item in issues if item["severity"] == "review")
    lines = [
        "# Track 6 컬럼 품질 검증 보고서",
        "",
        f"- 생성일: `{report['created_at']}`",
        f"- 상태: `{report['status']}`",
        f"- fail 이슈: `{fail_count}`",
        f"- review 이슈: `{review_count}`",
        f"- 이슈 CSV: `data/track6/quality/track6_column_quality_issues.csv`",
        "",
        "## 1. 검증 범위",
        "",
        "- 대상 파일: `track6_train`, `track6_val_warm`, `track6_test_warm`, `track6_val_cold`, `track6_test_cold`",
        "- 확인 항목: 스키마, 필수 컬럼 결측, 숫자 범위, 파생값 계산 일치, 카테고리 unknown, Warm/Cold 누수",
        "- 원본 추적 컬럼은 보존하되 모델 피처에서는 제외함",
        "",
        "## 2. split 요약",
        "",
        "| split | rows | artists | columns | medium unknown | support unknown |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, item in report["splits"].items():
        medium_unknown = item["categories"].get("medium_category", {}).get("unknown_or_blank", 0)
        support_unknown = item["categories"].get("support_category", {}).get("unknown_or_blank", 0)
        lines.append(
            f"| `{name}` | `{item['rows']:,}` | `{item['artists']:,}` | `{item['columns']}` | "
            f"`{medium_unknown:,}` | `{support_unknown:,}` |"
        )

    lines += [
        "",
        "## 3. 핵심 통과 항목",
        "",
        f"- split 간 `_track6_row_id` 중복: `{report['cross_split_checks']['duplicate_across_splits']}`",
        f"- val_warm 작가 train 누락 rows: `{report['cross_split_checks']['val_warm_artist_missing_from_train']}`",
        f"- test_warm 작가 train 누락 rows: `{report['cross_split_checks']['test_warm_artist_missing_from_train']}`",
        f"- val_warm 최소 train 작품 수: `{report['cross_split_checks']['val_warm_min_train_count']}`",
        f"- test_warm 최소 train 작품 수: `{report['cross_split_checks']['test_warm_min_train_count']}`",
        f"- val_warm 1작품 작가 수: `{report['cross_split_checks']['val_warm_one_work_artists']}`",
        f"- test_warm 1작품 작가 수: `{report['cross_split_checks']['test_warm_one_work_artists']}`",
        f"- val_cold train 작가명 겹침: `{report['cross_split_checks']['val_cold_orig_name_overlap']}`",
        f"- test_cold train 작가명 겹침: `{report['cross_split_checks']['test_cold_orig_name_overlap']}`",
        f"- val_cold artist history nonzero rows: `{report['cross_split_checks']['val_cold_nonzero_artist_history']}`",
        f"- test_cold artist history nonzero rows: `{report['cross_split_checks']['test_cold_nonzero_artist_history']}`",
        "",
        "## 4. 학습 후보 제외 사유 점검",
        "",
        f"- 전체 정제 rows: `{report['training_candidate_audit']['total_rows']:,}`",
        f"- `is_training_candidate=true`: `{report['training_candidate_audit']['training_candidate_true']:,}`",
        f"- `is_training_candidate=false`: `{report['training_candidate_audit']['training_candidate_false']:,}`",
        f"- false인데 제외 사유가 빈 rows: `{report['training_candidate_audit']['false_reason_blank_rows']}`",
        f"- true인데 제외 사유가 있는 rows: `{report['training_candidate_audit']['true_reason_nonblank_rows']}`",
        f"- 후보 플래그와 제외 사유 불일치 rows: `{report['training_candidate_audit']['candidate_reason_mismatch_rows']}`",
        "",
        "제외 사유별 rows:",
        "",
        "| reason | rows |",
        "|---|---:|",
    ]
    for reason, count in report["training_candidate_audit"]["reason_counts"].items():
        lines.append(f"| `{reason}` | `{count:,}` |")

    lines += [
        "",
        "## 5. 검토 필요 항목",
        "",
    ]
    visible_issues = [item for item in issues if item["severity"] in {"fail", "review"}]
    if visible_issues:
        lines += [
            "| split | column | check | count | severity | note |",
            "|---|---|---|---:|---|---|",
        ]
        for item in visible_issues:
            lines.append(
                f"| `{item['split']}` | `{item['column']}` | `{item['check']}` | "
                f"`{item['count']:,}` | `{item['severity']}` | {item['note']} |"
            )
    else:
        lines.append("- fail/review 이슈 없음")

    lines += [
        "",
        "## 6. 해석",
        "",
        "- 모델 실험을 막는 fail 이슈가 없으면 T6-E002 baseline으로 진행 가능",
        "- `is_training_candidate=false`는 `cleaning_exclude_reasons`가 있는 row와 일치해야 함",
        "- `support_category=unknown`은 일부 남아 있으므로 모델 입력 시 unknown 카테고리로 유지하고 slice 성능을 따로 확인",
        "- `track4_source`, URL, image URL, source artwork ID는 품질 감사용이며 모델 피처로 사용하지 않음",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    splits = load_splits()
    report: dict[str, Any] = {
        "created_at": date.today().isoformat(),
        "status": "pass",
        "splits": {},
        "cross_split_checks": {},
        "training_candidate_audit": {},
        "tracking_only_columns": TRACKING_ONLY_COLUMNS,
    }
    all_issues: list[dict[str, Any]] = []
    for name, df in splits.items():
        info, split_issues = validate_split(name, df)
        report["splits"][name] = info
        all_issues.extend(split_issues)
    cross_checks, cross_issues = validate_cross_split(splits)
    report["cross_split_checks"] = cross_checks
    all_issues.extend(cross_issues)
    report["training_candidate_audit"] = training_candidate_audit(load_full_cleaned())
    if report["training_candidate_audit"]["candidate_reason_mismatch_rows"]:
        all_issues.append(
            issue(
                "full_cleaned",
                "is_training_candidate",
                "candidate_reason_mismatch",
                report["training_candidate_audit"]["candidate_reason_mismatch_rows"],
                "fail",
                "is_training_candidate=true iff cleaning_exclude_reasons is blank",
            )
        )

    if any(item["severity"] == "fail" for item in all_issues):
        report["status"] = "fail"
    elif any(item["severity"] == "review" for item in all_issues):
        report["status"] = "review"

    OUT_JSON.write_text(json.dumps({"report": report, "issues": all_issues}, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(all_issues).to_csv(OUT_ISSUES, index=False)
    OUT_MD.write_text(render_markdown(report, all_issues), encoding="utf-8")
    print(OUT_JSON)
    print(OUT_MD)
    print(json.dumps({"status": report["status"], "issues": len(all_issues)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
