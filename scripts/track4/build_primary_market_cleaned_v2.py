"""Build Track 4 cleaned_v2 from raw_collected audit outputs."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
OUT_CSV = REPO / "data" / "track4_primary_market_cleaned_v2.csv"
OUT_FEATURE_CSV = REPO / "data" / "track4_primary_market_feature_candidates_v1.csv"
OUT_JSON = REPO / "data" / "track4_primary_market_cleaned_v2_summary.json"
OUT_MD = REPO / "docs" / "track4_primary_market_cleaned_v2_report.md"

PRICE = REPO / "data" / "track4_price_consistency_audit.csv"
SIZE = REPO / "data" / "track4_size_consistency_audit.csv"
ARTIST = REPO / "data" / "track4_artist_consistency_audit.csv"
MEDIUM = REPO / "data" / "track4_medium_support_consistency_audit.csv"
DUP = REPO / "data" / "track4_duplicate_consistency_audit.csv"
GALLERY = REPO / "data" / "track4_gallery_metadata_audit.csv"


KEY = ["track4_source", "track4_source_row_index"]


def read_csv(path: Path, cols: list[str] | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=cols, dtype="string", keep_default_na=False, low_memory=False)
    df["track4_source_row_index"] = df["track4_source_row_index"].astype(int)
    return df


def load() -> pd.DataFrame:
    price = read_csv(PRICE)
    size = read_csv(SIZE)
    artist = read_csv(ARTIST)
    medium = read_csv(MEDIUM)
    dup = read_csv(DUP)
    gallery = read_csv(GALLERY)

    df = price
    for part in [size, artist, medium, dup, gallery]:
        drop_cols = [c for c in part.columns if c in df.columns and c not in KEY]
        df = df.merge(part.drop(columns=drop_cols), on=KEY, how="left")
    return df


def add_representative_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_duplicate_representative"] = True
    sort_cols = ["price_krw", "width_cm", "height_cm", "artwork_url", "title_raw"]
    tmp = df.copy()
    tmp["_has_price"] = pd.to_numeric(tmp["price_krw"], errors="coerce").notna()
    tmp["_has_size"] = pd.to_numeric(tmp["width_cm"], errors="coerce").notna() & pd.to_numeric(tmp["height_cm"], errors="coerce").notna()
    tmp["_has_url"] = tmp["artwork_url"].fillna("").astype(str).ne("")
    tmp = tmp.sort_values(["_has_price", "_has_size", "_has_url", "track4_source_row_index"], ascending=[False, False, False, True])

    duplicate_keys = [
        ("same_source_semantic_key", "same_source_semantic_duplicate"),
        ("cross_source_semantic_key", "cross_source_semantic_duplicate"),
    ]
    non_rep_idx: set[int] = set()
    for key_col, status_name in duplicate_keys:
        valid = tmp[key_col].fillna("").astype(str).ne("") & tmp["duplicate_audit_status"].fillna("").str.contains(status_name, regex=False)
        counts = tmp.loc[valid, key_col].value_counts()
        dup_keys = set(counts[counts > 1].index)
        for _, group in tmp.loc[tmp[key_col].isin(dup_keys)].groupby(key_col, sort=False):
            keep = group.index[0]
            non_rep_idx.update(int(i) for i in group.index if i != keep)
    df.loc[df.index.isin(non_rep_idx), "is_duplicate_representative"] = False
    return df


def reason_list(row: pd.Series) -> list[str]:
    reasons: list[str] = []
    price = pd.to_numeric(row.get("price_krw"), errors="coerce")
    width = pd.to_numeric(row.get("width_cm"), errors="coerce")
    height = pd.to_numeric(row.get("height_cm"), errors="coerce")
    area = pd.to_numeric(row.get("area_cm2"), errors="coerce")

    if pd.isna(price):
        reasons.append("missing_price_krw")
    else:
        if price <= 0:
            reasons.append("non_positive_price")
        if price < 10_000:
            reasons.append("price_under_10000")
        if price > 1_000_000_000:
            reasons.append("price_over_1b")

    if pd.isna(width) or pd.isna(height):
        reasons.append("missing_core_size")
    else:
        if width <= 0 or height <= 0:
            reasons.append("non_positive_size")
    if not pd.isna(area):
        if area < 10:
            reasons.append("area_under_10cm2")
        if area > 1_000_000:
            reasons.append("area_over_1m_cm2")

    if str(row.get("medium_support_audit_status", "ok")) != "ok":
        if "missing_medium_raw" in str(row.get("medium_support_audit_status")):
            reasons.append("missing_medium_raw")

    if str(row.get("artist_audit_status", "ok")) != "ok":
        reasons.append("artist_audit_issue")

    if not bool(row.get("is_duplicate_representative", True)):
        reasons.append("duplicate_non_representative")

    return reasons


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    price = pd.to_numeric(df["price_krw"], errors="coerce").astype(float)
    area = pd.to_numeric(df["area_cm2"], errors="coerce").astype(float)
    width = pd.to_numeric(df["width_cm"], errors="coerce").astype(float)
    height = pd.to_numeric(df["height_cm"], errors="coerce").astype(float)
    df["ln_price_krw"] = np.log(price.where(price > 0))
    df["log_area"] = np.log(area.where(area > 0))
    df["aspect_ratio"] = np.maximum(width, height) / np.minimum(width, height)
    df["is_high_price_candidate"] = price.gt(100_000_000) & price.le(1_000_000_000)
    df["is_extreme_aspect_ratio"] = df["aspect_ratio"].gt(10)
    df["artist_works_count_in_cleaned"] = df.groupby("artist_key")["artist_key"].transform("size")
    df["artist_works_log"] = np.log1p(df["artist_works_count_in_cleaned"])
    df["medium_support_bucket"] = df["medium_category"].fillna("unknown").astype(str) + "__" + df["support_category"].fillna("unknown").astype(str)
    return df


def build() -> pd.DataFrame:
    df = load()
    df = add_representative_flags(df)
    df["cleaning_exclude_reasons"] = df.apply(lambda row: ";".join(reason_list(row)), axis=1)
    df["is_training_candidate"] = df["cleaning_exclude_reasons"].eq("")
    df = add_features(df)
    return df


def write_outputs(df: pd.DataFrame) -> dict:
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    feature_cols = [
        "artist_key",
        "artist_name_ko",
        "artist_name_standardized",
        "title_raw",
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
        "medium_support_bucket",
        "artist_works_log",
        "is_high_price_candidate",
        "is_extreme_aspect_ratio",
        "is_training_candidate",
        "cleaning_exclude_reasons",
    ]
    df.loc[:, feature_cols].to_csv(OUT_FEATURE_CSV, index=False, encoding="utf-8-sig")
    reasons: dict[str, int] = {}
    for value in df["cleaning_exclude_reasons"]:
        if not value:
            continue
        for reason in str(value).split(";"):
            reasons[reason] = reasons.get(reason, 0) + 1
    summary = {
        "created_at": "2026-05-15",
        "cleaned_csv": str(OUT_CSV.relative_to(REPO)),
        "feature_candidates_csv": str(OUT_FEATURE_CSV.relative_to(REPO)),
        "n_rows": int(len(df)),
        "training_candidates": int(df["is_training_candidate"].sum()),
        "excluded_rows": int((~df["is_training_candidate"]).sum()),
        "artist_name_ko_rows": int(df["artist_name_ko"].fillna("").astype(str).ne("").sum()),
        "source_counts": {str(k): int(v) for k, v in df["track4_source"].value_counts().items()},
        "training_candidate_source_counts": {str(k): int(v) for k, v in df.loc[df["is_training_candidate"], "track4_source"].value_counts().items()},
        "exclude_reasons": dict(sorted(reasons.items(), key=lambda kv: kv[1], reverse=True)),
        "model_feature_exclusions": ["track4_source", "track4_source_file", "source_artwork_id", "gallery_name_raw", "gallery_tier_validated"],
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary), encoding="utf-8")
    return summary


def render_md(summary: dict) -> str:
    lines = [
        "# Track 4 cleaned_v2 생성 보고서",
        "",
        "- 목적: 가격/크기/작가/재료/중복/출처/갤러리 감사 결과를 반영한 학습 후보 데이터 생성",
        f"- cleaned 파일: `{summary['cleaned_csv']}`",
        f"- feature 후보 파일: `{summary['feature_candidates_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 학습 후보 rows: `{summary['training_candidates']:,}`",
        f"- 제외 rows: `{summary['excluded_rows']:,}`",
        f"- 한글 작가명 rows: `{summary['artist_name_ko_rows']:,}`",
        "",
        "## 1. 출처별 row 수",
        "",
        "| 출처 | 전체 | 학습 후보 |",
        "|---|---:|---:|",
    ]
    for source, count in summary["source_counts"].items():
        cand = summary["training_candidate_source_counts"].get(source, 0)
        lines.append(f"| {source} | `{count:,}` | `{cand:,}` |")
    lines += [
        "",
        "## 2. 제외 사유",
        "",
        "| 사유 | rows |",
        "|---|---:|",
    ]
    for reason, count in summary["exclude_reasons"].items():
        lines.append(f"| `{reason}` | `{count:,}` |")
    lines += [
        "",
        "## 3. 모델 피처 제외 원칙",
        "",
        "- source 계열 컬럼은 feature 후보 파일에서 제외함",
        "- gallery_name / gallery_tier는 기본 feature 후보에서 제외함",
        "- source와 gallery 정보는 원본 추적과 품질 감사 용도로만 사용함",
        "",
        "## 4. 다음 단계",
        "",
        "- `track4_primary_market_feature_candidates_v1.csv` 기준으로 Warm/Cold split 생성",
        "- split 생성 시 `artist_key` 기준으로 Cold 작가를 분리",
        "- 모델 실험 전 feature 후보 컬럼 결측률을 다시 점검",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = build()
    summary = write_outputs(df)
    print("Track 4 cleaned_v2")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
