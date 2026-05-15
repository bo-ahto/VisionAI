"""Audit Track 4 price consistency from source-preserving raw data."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
OUT_CSV = REPO / "data" / "track4_price_consistency_audit.csv"
OUT_JSON = REPO / "data" / "track4_price_consistency_audit_summary.json"
OUT_MD = REPO / "docs" / "track4_price_consistency_audit.md"


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


def parse_currency(value: object, fallback: str = "") -> str:
    text = clean(value).upper()
    if text in {"KRW", "USD", "EUR", "GBP", "HKD"}:
        return text
    raw = clean(value)
    if "₩" in raw or "KRW" in raw.upper():
        return "KRW"
    if "$" in raw or "US$" in raw.upper() or "USD" in raw.upper():
        return "USD"
    if "€" in raw or "EUR" in raw.upper():
        return "EUR"
    if "£" in raw or "GBP" in raw.upper():
        return "GBP"
    return fallback


def source_price(row: pd.Series) -> dict[str, Any]:
    source = row["track4_source"]
    if source == "saatchi":
        return {
            "price_raw": clean(row.get("saatchi__price_raw")),
            "price_krw": parse_number(row.get("saatchi__price_krw")),
            "price_amount_raw": parse_number(row.get("saatchi__price_raw")),
            "currency": parse_currency(row.get("saatchi__price_currency"), parse_currency(row.get("saatchi__price_raw"))),
            "price_origin": "source_converted_krw",
        }
    if source == "artsy":
        return {
            "price_raw": clean(row.get("artsy__price_raw")),
            "price_krw": parse_number(row.get("artsy__price_krw")),
            "price_amount_raw": parse_number(row.get("artsy__price_amount")) or parse_number(row.get("artsy__price_raw")),
            "currency": parse_currency(row.get("artsy__price_currency"), parse_currency(row.get("artsy__price_raw"))),
            "price_origin": "source_converted_krw",
        }
    if source == "artue":
        price_krw = parse_number(row.get("artue__Price (KRW)"))
        price_usd = parse_number(row.get("artue__Price (USD)"))
        return {
            "price_raw": clean(row.get("artue__Price (KRW)")) or clean(row.get("artue__Price (USD)")),
            "price_krw": price_krw,
            "price_amount_raw": price_krw if price_krw is not None else price_usd,
            "currency": "KRW" if price_krw is not None else ("USD" if price_usd is not None else ""),
            "price_origin": "source_krw" if price_krw is not None else "source_usd_no_krw",
        }
    if source == "gallery_primary":
        return {
            "price_raw": clean(row.get("gallery_primary__price")) or clean(row.get("gallery_primary__price_raw")),
            "price_krw": parse_number(row.get("gallery_primary__price")) or parse_number(row.get("gallery_primary__price_raw")),
            "price_amount_raw": parse_number(row.get("gallery_primary__price")) or parse_number(row.get("gallery_primary__price_raw")),
            "currency": "KRW",
            "price_origin": "parsed_krw_from_raw",
        }
    return {"price_raw": "", "price_krw": None, "price_amount_raw": None, "currency": "", "price_origin": "unknown"}


def make_audit_frame(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        price = source_price(row)
        price_krw = price["price_krw"]
        status: list[str] = []
        if price_krw is None:
            status.append("missing_price_krw")
        else:
            if price_krw <= 0:
                status.append("non_positive_price")
            if price_krw < 10_000:
                status.append("price_under_10000")
            if price_krw > 100_000_000:
                status.append("price_over_100m")
            if price_krw > 1_000_000_000:
                status.append("price_over_1b")

        if not price["price_raw"]:
            status.append("missing_price_raw")
        if not price["currency"]:
            status.append("missing_currency")
        if price["currency"] == "KRW" and price["price_amount_raw"] is not None and price_krw is not None:
            # KRW raw amount and normalized KRW should be nearly identical.
            if abs(float(price["price_amount_raw"]) - float(price_krw)) > 1:
                status.append("krw_raw_normalized_mismatch")

        rows.append(
            {
                "track4_source": row["track4_source"],
                "track4_source_file": row["track4_source_file"],
                "track4_source_row_index": int(row["track4_source_row_index"]),
                "price_raw": price["price_raw"],
                "price_amount_raw": price["price_amount_raw"],
                "price_currency": price["currency"],
                "price_krw": price_krw,
                "price_origin": price["price_origin"],
                "price_audit_status": "ok" if not status else ";".join(status),
            }
        )
    return pd.DataFrame(rows)


def sample_records(df: pd.DataFrame, status: str, limit: int = 10) -> list[dict[str, Any]]:
    mask = df["price_audit_status"].str.contains(status, regex=False, na=False)
    cols = [
        "track4_source",
        "track4_source_row_index",
        "price_raw",
        "price_amount_raw",
        "price_currency",
        "price_krw",
        "price_origin",
        "price_audit_status",
    ]
    return df.loc[mask, cols].head(limit).replace({np.nan: None}).to_dict("records")


def build_summary(audit: pd.DataFrame) -> dict[str, Any]:
    issue_counts: dict[str, int] = {}
    for value in audit["price_audit_status"]:
        if value == "ok":
            continue
        for issue in str(value).split(";"):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    by_source = {}
    for source, group in audit.groupby("track4_source"):
        price = pd.to_numeric(group["price_krw"], errors="coerce")
        by_source[source] = {
            "rows": int(len(group)),
            "ok_rows": int(group["price_audit_status"].eq("ok").sum()),
            "issue_rows": int((~group["price_audit_status"].eq("ok")).sum()),
            "missing_price_krw": int(group["price_audit_status"].str.contains("missing_price_krw", regex=False).sum()),
            "under_10000": int(group["price_audit_status"].str.contains("price_under_10000", regex=False).sum()),
            "over_100m": int(group["price_audit_status"].str.contains("price_over_100m", regex=False).sum()),
            "over_1b": int(group["price_audit_status"].str.contains("price_over_1b", regex=False).sum()),
            "median": float(price.median()) if price.notna().any() else None,
            "q25": float(price.quantile(0.25)) if price.notna().any() else None,
            "q75": float(price.quantile(0.75)) if price.notna().any() else None,
            "max": float(price.max()) if price.notna().any() else None,
        }

    return {
        "created_at": "2026-05-15",
        "input": str(RAW_COLLECTED.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(audit)),
        "ok_rows": int(audit["price_audit_status"].eq("ok").sum()),
        "issue_rows": int((~audit["price_audit_status"].eq("ok")).sum()),
        "issue_counts": issue_counts,
        "by_source": by_source,
        "samples": {
            issue: sample_records(audit, issue)
            for issue in [
                "missing_price_krw",
                "price_under_10000",
                "price_over_100m",
                "price_over_1b",
                "krw_raw_normalized_mismatch",
            ]
        },
    }


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 가격 정합성 감사",
        "",
        "- 목적: `raw_collected` 기준으로 가격 컬럼이 학습 target으로 쓸 수 있는지 점검",
        f"- 입력: `{summary['input']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 정상 rows: `{summary['ok_rows']:,}`",
        f"- 이슈 rows: `{summary['issue_rows']:,}`",
        "",
        "## 1. 출처별 가격 요약",
        "",
        "| 출처 | rows | 정상 | 이슈 | 1만원 미만 | 1억 초과 | 10억 초과 | 중앙값 | Q25 | Q75 | 최대 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in summary["by_source"].items():
        lines.append(
            f"| {source} | `{item['rows']:,}` | `{item['ok_rows']:,}` | `{item['issue_rows']:,}` | "
            f"`{item['under_10000']:,}` | `{item['over_100m']:,}` | `{item['over_1b']:,}` | "
            f"`{item['median']:,.0f}` | `{item['q25']:,.0f}` | `{item['q75']:,.0f}` | `{item['max']:,.0f}` |"
        )

    lines += [
        "",
        "## 2. 이슈 카운트",
        "",
        "| 이슈 | 건수 | 해석 |",
        "|---|---:|---|",
    ]
    explanations = {
        "missing_price_krw": "표준 KRW 가격이 없음",
        "price_under_10000": "가격 파싱 오류 또는 자리표시값 가능성",
        "price_over_100m": "고가 작품 또는 이상치 후보",
        "price_over_1b": "초고가 이상치 후보, 기본 학습 후보에서는 제외 검토",
        "krw_raw_normalized_mismatch": "KRW 원본값과 표준 KRW 값이 다름",
        "missing_price_raw": "원본 가격 문자열 없음",
        "missing_currency": "통화 정보 없음",
    }
    for issue, count in sorted(summary["issue_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| `{issue}` | `{count:,}` | {explanations.get(issue, '확인 필요')} |")

    lines += [
        "",
        "## 3. 현재 판단",
        "",
        "- 가격 컬럼은 출처별 생성 방식이 다름",
        "- Saatchi / Artsy는 원본 통화 가격과 환산 KRW가 함께 있음",
        "- Artue / Gallery primary는 KRW 가격을 직접 target 후보로 볼 수 있음",
        "- `price_under_10000`은 기본 학습 후보에서 제외하는 것이 안전함",
        "- `price_over_1b`은 기본 학습 후보에서 제외하고 별도 고가 구간 검토 대상으로 두는 것이 안전함",
        "- `price_over_100m`은 무조건 제외가 아니라 고가 구간 flag로 먼저 관리하는 것이 적절함",
        "",
        "## 4. 제안 클렌징 규칙",
        "",
        "- `price_krw`가 없거나 0 이하이면 제외",
        "- `price_krw < 10,000`이면 제외",
        "- `price_krw > 1,000,000,000`이면 기본 학습 후보에서 제외하고 고가 별도 검토",
        "- `100,000,000 < price_krw <= 1,000,000,000`은 제외하지 않고 `is_high_price_candidate` flag로 관리",
        "- KRW 원본값과 표준 KRW 값이 불일치하면 수동 확인 후보로 관리",
        "",
        "## 5. 다음 단계",
        "",
        "- 위 규칙을 `standardized_v1` 또는 `cleaned_v2` 생성 스크립트에 반영",
        "- 가격 클렌징 후 크기 정합성 `T4-C2` 진행",
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

    print("Track 4 price consistency audit")
    print(f"rows: {summary['n_rows']:,}")
    print(f"ok: {summary['ok_rows']:,}")
    print(f"issues: {summary['issue_rows']:,}")
    print(f"issue_counts: {summary['issue_counts']}")


if __name__ == "__main__":
    main()
