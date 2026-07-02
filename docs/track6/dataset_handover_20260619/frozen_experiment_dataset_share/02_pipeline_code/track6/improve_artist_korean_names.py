#!/usr/bin/env python3
"""Apply high-confidence Track6 artist Korean-name corrections.

The script deliberately applies only reviewed overrides. Remaining long Korean
names are exported as review candidates instead of being auto-corrected.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track4_primary_market_feature_candidates_v1.csv"
OVERRIDES = REPO / "scripts" / "track6" / "artist_ko_overrides.csv"
OUT_CSV = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"
OUT_APPLIED = REPO / "data" / "track6" / "quality" / "track6_artist_name_ko_applied_overrides.csv"
OUT_REVIEW = REPO / "data" / "track6" / "quality" / "track6_artist_name_ko_review_candidates.csv"
OUT_SUMMARY = REPO / "data" / "track6" / "quality" / "track6_artist_name_ko_improvement_summary.json"
OUT_REPORT = REPO / "docs" / "track6" / "dataset" / "artist_name_ko_improvement_report.md"

ARTIST_COLS = [
    "artist_key",
    "artist_name_ko",
    "artist_name_ko_orig",
    "artist_name_standardized",
    "track4_source",
]


def norm_key(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def hangul_len(value: object) -> int:
    return len(re.sub(r"[^가-힣]", "", str(value or "")))


def load_overrides() -> pd.DataFrame:
    overrides = pd.read_csv(OVERRIDES, dtype="string", keep_default_na=False)
    required = {"artist_key", "artist_name_ko", "reason"}
    missing = required - set(overrides.columns)
    if missing:
        raise ValueError(f"override missing columns: {sorted(missing)}")
    overrides["artist_key_norm"] = overrides["artist_key"].map(norm_key)
    if overrides["artist_key_norm"].duplicated().any():
        dupes = overrides.loc[overrides["artist_key_norm"].duplicated(), "artist_key"].tolist()
        raise ValueError(f"duplicate override artist_key: {dupes}")
    return overrides


def build_review_candidates(df: pd.DataFrame, applied_keys: set[str]) -> pd.DataFrame:
    work = df.copy()
    base = work["artist_name_ko_orig"].where(work["artist_name_ko_orig"].astype(str).str.strip().ne(""), work["artist_name_ko"])
    work["_base_ko"] = base.astype(str).str.replace(r"_[A-Z]+$", "", regex=True).str.strip()
    work["_hangul_len"] = work["_base_ko"].map(hangul_len)
    work["_artist_key_norm"] = work["artist_key"].map(norm_key)

    candidates = work.loc[
        (work["_hangul_len"] >= 4)
        & (~work["_artist_key_norm"].isin(applied_keys))
    ]
    if candidates.empty:
        return pd.DataFrame(columns=[
            "rows",
            "artist_key",
            "artist_name_standardized",
            "current_artist_name_ko",
            "sources",
            "review_reason",
        ])

    agg = (
        candidates.groupby(["artist_key", "artist_name_standardized", "_base_ko"], dropna=False)
        .agg(
            rows=("artist_key", "size"),
            sources=("track4_source", lambda x: ",".join(sorted(set(map(str, x))))),
        )
        .reset_index()
        .rename(columns={"_base_ko": "current_artist_name_ko"})
        .sort_values(["rows", "artist_key"], ascending=[False, True])
    )
    agg["review_reason"] = "hangul_name_len_ge_4_not_overridden"
    return agg.loc[:, [
        "rows",
        "artist_key",
        "artist_name_standardized",
        "current_artist_name_ko",
        "sources",
        "review_reason",
    ]]


def render_report(summary: dict, applied_preview: pd.DataFrame, review_preview: pd.DataFrame) -> str:
    lines = [
        "# Track 6 작가 한글명 개선 보고서",
        "",
        "- 목적: 4글자 이상 한글식 이름 중 명백한 오표기 후보를 먼저 보정",
        f"- 입력: `{summary['input']}`",
        f"- 출력: `{summary['output']}`",
        f"- override 파일: `{summary['override_file']}`",
        f"- 적용 작가 key 수: `{summary['applied_artist_keys']:,}`",
        f"- 적용 rows: `{summary['applied_rows']:,}`",
        f"- 잔여 검토 후보 작가 key 수: `{summary['review_candidate_artist_keys']:,}`",
        f"- 잔여 검토 후보 rows: `{summary['review_candidate_rows']:,}`",
        "",
        "## 1. 처리 원칙",
        "",
        "- 자동 음역으로 다시 추정하지 않음",
        "- 확실한 한국식 이름만 `artist_ko_overrides.csv`에 등록해 적용함",
        "- 예명, 외국 작가명, 단체명, 갤러리명처럼 애매한 값은 검토 후보로 남김",
        "- `artist_name_ko_orig`는 보정 전 이름을 유지함",
        "- split은 보정된 `artist_name_ko` 기준으로 다시 생성해야 함",
        "",
        "## 2. 적용 예시",
        "",
        "| artist_key | 기존 한글명 | 보정 한글명 | rows | 사유 |",
        "|---|---|---|---:|---|",
    ]
    for _, row in applied_preview.iterrows():
        lines.append(
            f"| `{row['artist_key']}` | {row['old_artist_name_ko']} | {row['new_artist_name_ko']} | "
            f"`{int(row['rows']):,}` | `{row['reason']}` |"
        )
    lines += [
        "",
        "## 3. 잔여 검토 후보 상위",
        "",
        "| rows | artist_key | 현재 한글명 | 출처 |",
        "|---:|---|---|---|",
    ]
    for _, row in review_preview.iterrows():
        lines.append(
            f"| `{int(row['rows']):,}` | `{row['artist_key']}` | {row['current_artist_name_ko']} | `{row['sources']}` |"
        )
    lines += [
        "",
        "## 4. 다음 작업",
        "",
        "- `data/track6/track6_feature_candidates_name_corrected.csv` 기준으로 split 재생성",
        "- 컬럼 품질 검증과 feature/label 분리 재실행",
        "- 잔여 후보는 수동 검수 후 `scripts/track6/artist_ko_overrides.csv`에 추가",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(INPUT, dtype="string", keep_default_na=False, low_memory=False)
    for col in ARTIST_COLS:
        if col not in df.columns:
            raise ValueError(f"input missing column: {col}")

    overrides = load_overrides()
    override_map = dict(zip(overrides["artist_key_norm"], overrides["artist_name_ko"], strict=False))
    reason_map = dict(zip(overrides["artist_key_norm"], overrides["reason"], strict=False))

    df["artist_key_norm"] = df["artist_key"].map(norm_key)
    df["_old_artist_name_ko_for_audit"] = df["artist_name_ko"]
    apply_mask = df["artist_key_norm"].isin(override_map)
    df.loc[apply_mask, "artist_name_ko"] = df.loc[apply_mask, "artist_key_norm"].map(override_map)

    applied = (
        df.loc[apply_mask]
        .groupby(["artist_key", "_old_artist_name_ko_for_audit", "artist_name_ko"], dropna=False)
        .agg(rows=("artist_key", "size"))
        .reset_index()
        .rename(columns={
            "_old_artist_name_ko_for_audit": "old_artist_name_ko",
            "artist_name_ko": "new_artist_name_ko",
        })
        .sort_values(["rows", "artist_key"], ascending=[False, True])
    )
    applied["reason"] = applied["artist_key"].map(lambda x: reason_map.get(norm_key(x), "manual_override"))

    applied_keys = set(overrides["artist_key_norm"])
    review = build_review_candidates(df, applied_keys)

    df = df.drop(columns=["artist_key_norm", "_old_artist_name_ko_for_audit"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_APPLIED.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    applied.to_csv(OUT_APPLIED, index=False, encoding="utf-8-sig")
    review.to_csv(OUT_REVIEW, index=False, encoding="utf-8-sig")

    summary = {
        "created_at": "2026-05-18",
        "input": str(INPUT.relative_to(REPO)),
        "output": str(OUT_CSV.relative_to(REPO)),
        "override_file": str(OVERRIDES.relative_to(REPO)),
        "applied_artist_keys": int(overrides["artist_key_norm"].nunique()),
        "applied_rows": int(apply_mask.sum()),
        "review_candidate_artist_keys": int(review["artist_key"].nunique()) if not review.empty else 0,
        "review_candidate_rows": int(review["rows"].sum()) if not review.empty else 0,
        "applied_overrides_csv": str(OUT_APPLIED.relative_to(REPO)),
        "review_candidates_csv": str(OUT_REVIEW.relative_to(REPO)),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_REPORT.write_text(render_report(summary, applied.head(40), review.head(40)), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
