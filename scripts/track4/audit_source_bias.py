"""Audit Track 4 source bias for data quality only, not model features."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "track4_primary_market_raw_collected.csv"
PRICE = REPO / "data" / "track4_price_consistency_audit.csv"
SIZE = REPO / "data" / "track4_size_consistency_audit.csv"
MEDIUM = REPO / "data" / "track4_medium_support_consistency_audit.csv"
DUP = REPO / "data" / "track4_duplicate_consistency_audit.csv"
OUT_CSV = REPO / "data" / "track4_source_bias_audit.csv"
OUT_JSON = REPO / "data" / "track4_source_bias_audit_summary.json"
OUT_MD = REPO / "docs" / "track4_source_bias_audit.md"


def load_frame() -> pd.DataFrame:
    base = pd.read_csv(RAW, usecols=["track4_source", "track4_source_row_index"], dtype={"track4_source": "string"})
    base["track4_source_row_index"] = base["track4_source_row_index"].astype(int)
    parts = [
        pd.read_csv(PRICE, usecols=["track4_source", "track4_source_row_index", "price_krw", "price_audit_status"]),
        pd.read_csv(SIZE, usecols=["track4_source", "track4_source_row_index", "area_cm2", "has_depth", "is_3d_candidate", "size_audit_status"]),
        pd.read_csv(MEDIUM, usecols=["track4_source", "track4_source_row_index", "medium_category", "support_category", "medium_support_audit_status"]),
        pd.read_csv(DUP, usecols=["track4_source", "track4_source_row_index", "duplicate_audit_status"]),
    ]
    out = base
    for part in parts:
        part["track4_source_row_index"] = part["track4_source_row_index"].astype(int)
        out = out.merge(part, on=["track4_source", "track4_source_row_index"], how="left")
    return out


def pct(n: int, d: int) -> float:
    return round(n / d * 100, 2) if d else 0.0


def source_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, g in df.groupby("track4_source"):
        n = len(g)
        price = pd.to_numeric(g["price_krw"], errors="coerce")
        area = pd.to_numeric(g["area_cm2"], errors="coerce")
        rows.append(
            {
                "source": str(source),
                "rows": int(n),
                "price_available": int(price.notna().sum()),
                "price_available_pct": pct(int(price.notna().sum()), n),
                "price_median": float(price.median()) if price.notna().any() else None,
                "price_q75": float(price.quantile(0.75)) if price.notna().any() else None,
                "price_over_100m": int((price > 100_000_000).sum()),
                "area_available": int(area.notna().sum()),
                "area_median": float(area.median()) if area.notna().any() else None,
                "is_3d_candidate": int(g["is_3d_candidate"].fillna(False).astype(bool).sum()),
                "medium_top": str(g["medium_category"].mode().iloc[0]) if g["medium_category"].notna().any() else "",
                "support_top": str(g["support_category"].mode().iloc[0]) if g["support_category"].notna().any() else "",
                "price_issue_rows": int(~g["price_audit_status"].fillna("ok").eq("ok").sum()) if False else int((~g["price_audit_status"].fillna("ok").eq("ok")).sum()),
                "size_issue_rows": int((~g["size_audit_status"].fillna("ok").eq("ok")).sum()),
                "medium_issue_rows": int((~g["medium_support_audit_status"].fillna("ok").eq("ok")).sum()),
                "duplicate_flag_rows": int((~g["duplicate_audit_status"].fillna("ok").eq("ok")).sum()),
            }
        )
    return rows


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 출처 편향 점검",
        "",
        "- 목적: source를 모델 피처로 쓰지 않고도 출처별 데이터 품질 차이를 파악",
        "- 결론: source는 학습 피처에서 제외하고, 품질관리/원본추적 용도로만 사용",
        f"- 입력: `{summary['input']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        "",
        "## 1. 출처별 품질 요약",
        "",
        "| 출처 | rows | 가격 있음 | 가격 중앙값 | 1억 초과 | 면적 중앙값 | 3D 후보 | 대표 재료 | 가격 이슈 | 크기 이슈 | 재료 이슈 | 중복 flag |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary["by_source"]:
        lines.append(
            f"| {row['source']} | `{row['rows']:,}` | `{row['price_available']:,}` / `{row['price_available_pct']:.2f}%` | "
            f"`{row['price_median'] or 0:,.0f}` | `{row['price_over_100m']:,}` | `{row['area_median'] or 0:,.0f}` | "
            f"`{row['is_3d_candidate']:,}` | `{row['medium_top']}` | `{row['price_issue_rows']:,}` | "
            f"`{row['size_issue_rows']:,}` | `{row['medium_issue_rows']:,}` | `{row['duplicate_flag_rows']:,}` |"
        )
    lines += [
        "",
        "## 2. 현재 판단",
        "",
        "- 출처별 가격 결측률과 가격대가 다름",
        "- 이 차이는 모델이 배워야 하는 신호가 아니라 수집 경로 차이임",
        "- source를 피처로 쓰면 실제 운영에서 재현할 수 없는 성능이 나올 수 있음",
        "- 따라서 source는 학습 입력에서 제외하고, 감사/분포/중복 처리 기준으로만 사용함",
        "",
        "## 3. 클렌징 반영 원칙",
        "",
        "- source별로 오류율이 높은 항목을 확인하되 source 보정 피처를 만들지 않음",
        "- source별 결측/이상값이 큰 경우 해당 row에 구체적 audit flag를 남김",
        "- 최종 feature 후보 파일에는 source 계열 컬럼을 제외함",
        "- 원본 추적용 파일에는 source 계열 컬럼을 유지함",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = load_frame()
    rows = source_summary(df)
    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    summary = {
        "created_at": "2026-05-15",
        "input": str(RAW.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "by_source": rows,
        "model_feature_policy": "exclude_source",
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary), encoding="utf-8")
    print("Track 4 source bias audit")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
