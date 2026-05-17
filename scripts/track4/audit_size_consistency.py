"""Audit Track 4 size consistency from source-preserving raw data."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
OUT_CSV = REPO / "data" / "track4_size_consistency_audit.csv"
OUT_JSON = REPO / "data" / "track4_size_consistency_audit_summary.json"
OUT_MD = REPO / "docs" / "track4" / "audits" / "size_consistency_audit.md"


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_number(value: object) -> float | None:
    text = clean(value)
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_dimension_values_cm(value: object) -> list[float]:
    text = clean(value)
    if not text:
        return []
    if re.search(r"\bdiameter\b|지름", text, flags=re.IGNORECASE):
        diameter = parse_number(text)
        if diameter is not None:
            return [diameter, diameter]
    cm_part = re.split(r"\(| in\b| inches\b", text, flags=re.IGNORECASE)[0]
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", cm_part.replace(",", ""))]


def normalize_dimensions(
    values: list[float],
    *,
    source_order: str,
) -> tuple[float | None, float | None, float | None, str]:
    """Return width/height/depth and a normalization note.

    크롤링 원본은 출처마다 `height x width x depth` 또는 `width x height x depth`
    순서가 섞인다. 특히 2D 작품은 세 값 중 하나가 2~5cm 두께로 들어오는 경우가
    많으므로, 명확한 얇은 값을 depth로 재배치한다.
    """
    if len(values) >= 3:
        first, second, third = values[:3]
        dims = [first, second, third]
        small = [v for v in dims if 0 < v <= 10]
        large = [v for v in dims if v > 10]
        if len(small) == 1 and len(large) == 2:
            return large[0], large[1], small[0], "thin_dimension_reordered_to_depth"
        if source_order == "height_width_depth":
            return second, first, third, "source_height_width_depth"
        return first, second, third, "source_width_height_depth"
    if len(values) == 2:
        first, second = values[:2]
        if source_order == "height_width_depth":
            return second, first, None, "source_height_width"
        return first, second, None, "source_width_height"
    if len(values) == 1:
        return values[0], None, None, "single_dimension"
    return None, None, None, "missing"


def parse_dimensions_cm(value: object, *, source_order: str = "width_height_depth") -> tuple[float | None, float | None, float | None, str]:
    values = parse_dimension_values_cm(value)
    return normalize_dimensions(values, source_order=source_order)


def source_size(row: pd.Series) -> dict[str, Any]:
    source = row["track4_source"]
    if source == "saatchi":
        w, h, d, note = parse_dimensions_cm(row.get("saatchi__dimensions_cm"), source_order="height_width_depth")
        return {
            "size_raw": clean(row.get("saatchi__dimensions_cm")),
            "width_cm": w,
            "height_cm": h,
            "depth_cm": d,
            "size_origin": f"parsed_dimensions_cm:{note}",
        }
    if source == "artsy":
        parsed_w, parsed_h, parsed_d, note = parse_dimensions_cm(row.get("artsy__dimensions_cm"), source_order="width_height_depth")
        source_w = parse_number(row.get("artsy__width_cm"))
        source_h = parse_number(row.get("artsy__height_cm"))
        source_d = parse_number(row.get("artsy__depth_cm"))
        if note == "thin_dimension_reordered_to_depth":
            width, height, depth = parsed_w, parsed_h, parsed_d
        else:
            width = source_w or parsed_w
            height = source_h or parsed_h
            depth = source_d or parsed_d
        return {
            "size_raw": clean(row.get("artsy__dimensions_cm")),
            "width_cm": width,
            "height_cm": height,
            "depth_cm": depth,
            "size_origin": f"source_width_height_depth:{note}",
        }
    if source == "artue":
        return {
            "size_raw": "",
            "width_cm": parse_number(row.get("artue__Width (cm)")),
            "height_cm": parse_number(row.get("artue__Height (cm)")),
            "depth_cm": parse_number(row.get("artue__Depth (cm)")),
            "size_origin": "source_width_height_depth",
        }
    if source == "gallery_primary":
        return {
            "size_raw": clean(row.get("gallery_primary__size_raw")),
            "width_cm": parse_number(row.get("gallery_primary__width")),
            "height_cm": parse_number(row.get("gallery_primary__height")),
            "depth_cm": None,
            "size_origin": "source_width_height",
        }
    return {"size_raw": "", "width_cm": None, "height_cm": None, "depth_cm": None, "size_origin": "unknown"}


def make_audit_frame(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        size = source_size(row)
        width = size["width_cm"]
        height = size["height_cm"]
        depth = size["depth_cm"]

        status: list[str] = []
        if width is None:
            status.append("missing_width_cm")
        if height is None:
            status.append("missing_height_cm")
        if width is not None and width <= 0:
            status.append("non_positive_width")
        if height is not None and height <= 0:
            status.append("non_positive_height")
        if depth is not None and depth < 0:
            status.append("negative_depth")

        if width is not None and width > 1_000:
            status.append("width_over_1000cm")
        if height is not None and height > 1_000:
            status.append("height_over_1000cm")
        if depth is not None and depth > 1_000:
            status.append("depth_over_1000cm")

        area = None
        aspect_ratio = None
        has_depth = False
        is_3d_candidate = False
        if width is not None and height is not None and width > 0 and height > 0:
            area = width * height
            long_side = max(width, height)
            short_side = min(width, height)
            aspect_ratio = long_side / short_side if short_side else None
            if area < 10:
                status.append("area_under_10cm2")
            if area > 1_000_000:
                status.append("area_over_1m_cm2")
            if aspect_ratio is not None and aspect_ratio > 10:
                status.append("aspect_ratio_over_10")

        if depth is not None and depth > 0:
            has_depth = True
            if width is not None and height is not None and width > 0 and height > 0:
                short_side = min(width, height)
                if depth >= short_side * 0.5:
                    is_3d_candidate = True
            if depth > 100:
                status.append("depth_over_100cm")

        if not size["size_raw"] and size["size_origin"] in {"parsed_dimensions_cm", "source_width_height"}:
            status.append("missing_size_raw")

        rows.append(
            {
                "track4_source": row["track4_source"],
                "track4_source_file": row["track4_source_file"],
                "track4_source_row_index": int(row["track4_source_row_index"]),
                "size_raw": size["size_raw"],
                "width_cm": width,
                "height_cm": height,
                "depth_cm": depth,
                "area_cm2": area,
                "aspect_ratio": aspect_ratio,
                "has_depth": has_depth,
                "is_3d_candidate": is_3d_candidate,
                "size_origin": size["size_origin"],
                "size_audit_status": "ok" if not status else ";".join(status),
            }
        )
    return pd.DataFrame(rows)


def sample_records(df: pd.DataFrame, status: str, limit: int = 10) -> list[dict[str, Any]]:
    mask = df["size_audit_status"].str.contains(status, regex=False, na=False)
    cols = [
        "track4_source",
        "track4_source_row_index",
        "size_raw",
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "aspect_ratio",
        "size_audit_status",
    ]
    return df.loc[mask, cols].head(limit).replace({np.nan: None}).to_dict("records")


def build_summary(audit: pd.DataFrame) -> dict[str, Any]:
    issue_counts: dict[str, int] = {}
    for value in audit["size_audit_status"]:
        if value == "ok":
            continue
        for issue in str(value).split(";"):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    by_source = {}
    for source, group in audit.groupby("track4_source"):
        width = pd.to_numeric(group["width_cm"], errors="coerce")
        height = pd.to_numeric(group["height_cm"], errors="coerce")
        area = pd.to_numeric(group["area_cm2"], errors="coerce")
        by_source[source] = {
            "rows": int(len(group)),
            "ok_rows": int(group["size_audit_status"].eq("ok").sum()),
            "issue_rows": int((~group["size_audit_status"].eq("ok")).sum()),
            "missing_width": int(group["size_audit_status"].str.contains("missing_width_cm", regex=False).sum()),
            "missing_height": int(group["size_audit_status"].str.contains("missing_height_cm", regex=False).sum()),
            "aspect_over_10": int(group["size_audit_status"].str.contains("aspect_ratio_over_10", regex=False).sum()),
            "area_under_10": int(group["size_audit_status"].str.contains("area_under_10cm2", regex=False).sum()),
            "area_over_1m": int(group["size_audit_status"].str.contains("area_over_1m_cm2", regex=False).sum()),
            "depth_over_100": int(group["size_audit_status"].str.contains("depth_over_100cm", regex=False).sum()),
            "has_depth": int(group["has_depth"].sum()),
            "is_3d_candidate": int(group["is_3d_candidate"].sum()),
            "width_median": float(width.median()) if width.notna().any() else None,
            "height_median": float(height.median()) if height.notna().any() else None,
            "area_median": float(area.median()) if area.notna().any() else None,
            "area_max": float(area.max()) if area.notna().any() else None,
        }

    return {
        "created_at": "2026-05-15",
        "input": str(RAW_COLLECTED.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(audit)),
        "ok_rows": int(audit["size_audit_status"].eq("ok").sum()),
        "issue_rows": int((~audit["size_audit_status"].eq("ok")).sum()),
        "issue_counts": issue_counts,
        "by_source": by_source,
        "samples": {
            issue: sample_records(audit, issue)
            for issue in [
                "missing_width_cm",
                "missing_height_cm",
                "area_under_10cm2",
                "area_over_1m_cm2",
                "aspect_ratio_over_10",
                "depth_over_100cm",
            ]
        },
    }


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}"


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 크기 정합성 감사",
        "",
        "- 목적: `raw_collected` 기준으로 크기 컬럼이 면적/호수/3D 피처로 쓸 수 있는지 점검",
        f"- 입력: `{summary['input']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 정상 rows: `{summary['ok_rows']:,}`",
        f"- 이슈 rows: `{summary['issue_rows']:,}`",
        "",
        "## 1. 출처별 크기 요약",
        "",
        "| 출처 | rows | 정상 | 이슈 | width 중앙값 | height 중앙값 | 면적 중앙값 | 면적 최대 | depth 있음 | 3D 후보 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in summary["by_source"].items():
        lines.append(
            f"| {source} | `{item['rows']:,}` | `{item['ok_rows']:,}` | `{item['issue_rows']:,}` | "
            f"`{fmt(item['width_median'])}` | `{fmt(item['height_median'])}` | `{fmt(item['area_median'])}` | "
            f"`{fmt(item['area_max'])}` | `{item['has_depth']:,}` | `{item['is_3d_candidate']:,}` |"
        )

    lines += [
        "",
        "## 2. 이슈 카운트",
        "",
        "| 이슈 | 건수 | 해석 |",
        "|---|---:|---|",
    ]
    explanations = {
        "missing_width_cm": "표준 가로값이 없음",
        "missing_height_cm": "표준 세로값이 없음",
        "non_positive_width": "가로가 0 이하",
        "non_positive_height": "세로가 0 이하",
        "negative_depth": "깊이가 음수",
        "width_over_1000cm": "가로 10m 초과, 파싱 오류 또는 특수 대형 작품 후보",
        "height_over_1000cm": "세로 10m 초과, 파싱 오류 또는 특수 대형 작품 후보",
        "depth_over_1000cm": "깊이 10m 초과, 파싱 오류 후보",
        "depth_over_100cm": "깊이 1m 초과, 3D/설치 작품 또는 파싱 오류 후보",
        "area_under_10cm2": "면적 10cm2 미만, 파싱 오류 또는 초소형 후보",
        "area_over_1m_cm2": "면적 1,000,000cm2 초과, 파싱 오류 또는 초대형 후보",
        "aspect_ratio_over_10": "긴 변이 짧은 변의 10배 초과",
        "missing_size_raw": "원본 크기 문자열 없음",
    }
    for issue, count in sorted(summary["issue_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| `{issue}` | `{count:,}` | {explanations.get(issue, '확인 필요')} |")

    lines += [
        "",
        "## 3. 현재 판단",
        "",
        "- width/height가 모두 있는 행은 면적 피처 후보로 사용할 수 있음",
        "- depth는 출처별 의미가 다를 수 있어 2D/3D 판단 보조값으로 먼저 사용함",
        "- `aspect_ratio_over_10`은 무조건 제외가 아니라 길쭉한 작품과 파싱 오류를 나누어 샘플 확인이 필요함",
        "- `area_under_10cm2`와 `area_over_1m_cm2`은 기본 학습 후보에서 제외하거나 수동 검토 flag로 관리하는 것이 안전함",
        "- Gallery primary의 `unit` 컬럼에는 에디션 정보가 들어가 있어 크기 단위로 쓰면 안 됨",
        "",
        "## 4. 제안 클렌징 규칙",
        "",
        "- width/height가 없거나 0 이하이면 크기 기반 피처 생성 대상에서 제외",
        "- width/height/depth가 1000cm를 넘으면 수동 검토 후보로 관리",
        "- `area_cm2 < 10`이면 기본 학습 후보에서 제외",
        "- `area_cm2 > 1,000,000`이면 기본 학습 후보에서 제외하고 초대형 별도 검토",
        "- `aspect_ratio > 10`이면 제외하지 않고 `is_extreme_aspect_ratio` flag로 관리",
        "- `depth_cm > 0`이면 `has_depth`를 만들고, depth가 짧은 변의 50% 이상이면 `is_3d_candidate`로 관리",
        "",
        "## 5. 다음 단계",
        "",
        "- 위 규칙을 `standardized_v1` 또는 `cleaned_v2` 생성 스크립트에 반영",
        "- 크기 클렌징 후 작가명 정합성 `T4-C4` 진행",
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

    print("Track 4 size consistency audit")
    print(f"rows: {summary['n_rows']:,}")
    print(f"ok: {summary['ok_rows']:,}")
    print(f"issues: {summary['issue_rows']:,}")
    print(f"issue_counts: {summary['issue_counts']}")


if __name__ == "__main__":
    main()
