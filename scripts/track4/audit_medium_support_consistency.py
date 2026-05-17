"""Audit Track 4 medium/support consistency and first-pass mapping."""
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
OUT_CSV = REPO / "data" / "track4_medium_support_consistency_audit.csv"
OUT_JSON = REPO / "data" / "track4_medium_support_consistency_audit_summary.json"
OUT_MD = REPO / "docs" / "track4" / "audits" / "medium_support_consistency_audit.md"


MEDIUM_RULES: list[tuple[str, str]] = [
    ("oil", r"\boil\b|유채|유화"),
    ("acrylic", r"acrylic|아크릴"),
    ("watercolor", r"watercolor|watercolour|수채"),
    ("ink", r"\bink\b|먹|잉크|chinese ink"),
    ("gouache", r"gouache|과슈"),
    ("charcoal", r"charcoal|목탄"),
    ("pencil", r"pencil|graphite|colored pencil|color pencil|연필|색연필|흑연"),
    ("pastel", r"pastel|파스텔"),
    ("print", r"print|pigmentprint|pigment print|archival pigment|lithograph|silkscreen|screenprint|serigraph|woodcut|edition|lenticular|프린트|판화"),
    ("photo", r"photograph|photography|photo|c-?print|사진"),
    ("digital", r"digital|video|generative|gan|nft|uv print|ipad|디지털|영상"),
    ("ceramic", r"ceramic|porcelain|clay|도자|세라믹"),
    ("sculpture_material", r"sculpture|bronze|steel|iron|aluminum|aluminium|copper|brass|wood|glass|resin|stone|granite|marble|plaster|lead|zinc|조각|브론즈|철|동|나무|유리|레진|석고"),
    ("textile", r"embroidery|fabric|textile|thread|silk|cotton|섬유|자수"),
    ("collage", r"collage|콜라주"),
    ("painting_material", r"\bpainting\b|\bpaint\b|pigment|color|colour|lacquer|ottchil|crayon|pen\b|tempera|gesso|airbrush|powdered pigment|분채|안료|옻"),
    ("mixed_media", r"mixed media|mixed|혼합|복합"),
]

SUPPORT_RULES: list[tuple[str, str]] = [
    ("canvas", r"canvas|캔버스"),
    ("linen", r"linen|리넨"),
    ("paper", r"paper|hanji|xuan|dongba|종이|한지|장지"),
    ("panel", r"panel|board|cardboard|wood panel|basswood|패널|보드|판넬|목판"),
    ("glass", r"glass|유리"),
    ("wood", r"\bwood\b|나무"),
    ("metal", r"steel|iron|aluminum|copper|brass|lead|zinc|금속|철|동"),
    ("fabric", r"fabric|textile|silk|cotton|천|섬유"),
]


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", clean(value))
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def source_medium(row: pd.Series) -> dict[str, Any]:
    source = row["track4_source"]
    if source == "saatchi":
        raw = clean(row.get("saatchi__medium"))
        return {
            "medium_raw": raw,
            "medium_source_category": clean(row.get("saatchi__medium_category")),
            "medium_l1": clean(row.get("saatchi__medium_l1")),
            "medium_leaf": clean(row.get("saatchi__medium_leaf")),
            "support_source_category": clean(row.get("saatchi__support_type")),
            "support_l1": clean(row.get("saatchi__support_l1")),
            "support_leaf": clean(row.get("saatchi__support_leaf")),
            "medium_origin": "source_medium_with_existing_categories",
        }
    if source == "artsy":
        raw = clean(row.get("artsy__medium"))
        return {
            "medium_raw": raw,
            "medium_source_category": clean(row.get("artsy__category")) or clean(row.get("artsy__medium_type")),
            "medium_l1": "",
            "medium_leaf": "",
            "support_source_category": "",
            "support_l1": "",
            "support_leaf": "",
            "medium_origin": "source_medium_text",
        }
    if source == "artue":
        raw = clean(row.get("artue__Medium (EN)")) or clean(row.get("artue__Medium (KO)"))
        return {
            "medium_raw": raw,
            "medium_source_category": "",
            "medium_l1": "",
            "medium_leaf": "",
            "support_source_category": "",
            "support_l1": "",
            "support_leaf": "",
            "medium_origin": "source_medium_text",
        }
    if source == "gallery_primary":
        raw = clean(row.get("gallery_primary__materials"))
        return {
            "medium_raw": raw,
            "medium_source_category": "",
            "medium_l1": "",
            "medium_leaf": "",
            "support_source_category": "",
            "support_l1": "",
            "support_leaf": "",
            "medium_origin": "source_materials_text",
        }
    return {
        "medium_raw": "",
        "medium_source_category": "",
        "medium_l1": "",
        "medium_leaf": "",
        "support_source_category": "",
        "support_l1": "",
        "support_leaf": "",
        "medium_origin": "unknown",
    }


def match_categories(text: str, rules: list[tuple[str, str]]) -> list[str]:
    matched: list[str] = []
    for category, pattern in rules:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matched.append(category)
    return matched


def primary_medium(matches: list[str], text: str) -> str:
    if not matches:
        if not text:
            return "unknown"
        if re.fullmatch(r"-+|n/?a|none|unknown|기타", text.strip(), flags=re.IGNORECASE):
            return "unknown"
        return "other"
    if "mixed_media" in matches or len(matches) >= 2:
        return "mixed_media"
    return matches[0]


def primary_support(matches: list[str]) -> str:
    if not matches:
        return "unknown"
    return matches[0]


def normalize_support_label(value: str) -> str:
    text = normalize_text(value).lower()
    if text in {"canvas", "캔버스"}:
        return "canvas"
    if text in {"paper", "종이", "한지", "장지"}:
        return "paper"
    if text in {"panel", "board", "패널", "판넬", "보드", "나무"}:
        return "panel"
    if text in {"linen", "리넨"}:
        return "linen"
    if text in {"silk", "fabric", "섬유", "비단"}:
        return "fabric"
    if text in {"metal", "금속"}:
        return "metal"
    if text in {"glass", "유리"}:
        return "glass"
    return ""


def make_audit_frame(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        source = source_medium(row)
        raw = normalize_text(source["medium_raw"])
        raw_lower = raw.lower()
        medium_matches = match_categories(raw_lower, MEDIUM_RULES)
        support_matches = match_categories(raw_lower, SUPPORT_RULES)
        medium_category = primary_medium(medium_matches, raw_lower)
        support_category = primary_support(support_matches)
        support_from_source = normalize_support_label(source["support_source_category"]) or normalize_support_label(source["support_l1"]) or normalize_support_label(source["support_leaf"])
        if support_category == "unknown" and support_from_source:
            support_category = support_from_source

        status: list[str] = []
        warning: list[str] = []
        if not raw:
            status.append("missing_medium_raw")
        if raw in {"-", "--"}:
            status.append("placeholder_medium_raw")
        if medium_category in {"other", "unknown"}:
            status.append("medium_unmapped")
        if support_category == "unknown":
            warning.append("support_unmapped")
        if len(medium_matches) >= 2:
            warning.append("multiple_medium_matches")
        if len(support_matches) >= 2:
            warning.append("multiple_support_matches")

        source_medium_category = normalize_text(source["medium_source_category"]).lower()
        if source_medium_category and medium_category not in {"other", "unknown"}:
            if source_medium_category not in medium_category and medium_category not in source_medium_category:
                warning.append("source_category_differs")

        rows.append(
            {
                "track4_source": row["track4_source"],
                "track4_source_file": row["track4_source_file"],
                "track4_source_row_index": int(row["track4_source_row_index"]),
                "medium_raw": raw,
                "medium_source_category": source["medium_source_category"],
                "medium_l1": source["medium_l1"],
                "medium_leaf": source["medium_leaf"],
                "support_source_category": source["support_source_category"],
                "support_l1": source["support_l1"],
                "support_leaf": source["support_leaf"],
                "medium_category": medium_category,
                "support_category": support_category,
                "support_from_source": support_from_source,
                "medium_match_labels": ",".join(medium_matches),
                "support_match_labels": ",".join(support_matches),
                "medium_origin": source["medium_origin"],
                "medium_support_warning_status": "ok" if not warning else ";".join(warning),
                "medium_support_audit_status": "ok" if not status else ";".join(status),
            }
        )
    return pd.DataFrame(rows)


def top_values(df: pd.DataFrame, col: str, limit: int = 15) -> list[dict[str, Any]]:
    counts = df[col].fillna("").replace("", pd.NA).dropna().value_counts().head(limit)
    return [{"value": str(idx), "count": int(value)} for idx, value in counts.items()]


def sample_records(df: pd.DataFrame, status: str, limit: int = 10) -> list[dict[str, Any]]:
    mask = df["medium_support_audit_status"].str.contains(status, regex=False, na=False)
    cols = [
        "track4_source",
        "track4_source_row_index",
        "medium_raw",
        "medium_category",
        "support_category",
        "medium_match_labels",
        "support_match_labels",
        "medium_support_warning_status",
        "medium_support_audit_status",
    ]
    return df.loc[mask, cols].head(limit).replace({np.nan: None}).to_dict("records")


def build_summary(audit: pd.DataFrame) -> dict[str, Any]:
    issue_counts: dict[str, int] = {}
    for value in audit["medium_support_audit_status"]:
        if value == "ok":
            continue
        for issue in str(value).split(";"):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    by_source = {}
    for source, group in audit.groupby("track4_source"):
        by_source[source] = {
            "rows": int(len(group)),
            "ok_rows": int(group["medium_support_audit_status"].eq("ok").sum()),
            "issue_rows": int((~group["medium_support_audit_status"].eq("ok")).sum()),
            "missing_medium_raw": int(group["medium_support_audit_status"].str.contains("missing_medium_raw", regex=False).sum()),
            "medium_unmapped": int(group["medium_support_audit_status"].str.contains("medium_unmapped", regex=False).sum()),
            "multiple_medium_matches": int(group["medium_support_warning_status"].str.contains("multiple_medium_matches", regex=False).sum()),
            "multiple_support_matches": int(group["medium_support_warning_status"].str.contains("multiple_support_matches", regex=False).sum()),
            "support_unmapped": int(group["medium_support_warning_status"].str.contains("support_unmapped", regex=False).sum()),
            "source_category_differs": int(group["medium_support_warning_status"].str.contains("source_category_differs", regex=False).sum()),
            "top_medium_categories": top_values(group, "medium_category", 8),
            "top_support_categories": top_values(group, "support_category", 8),
        }

    return {
        "created_at": "2026-05-15",
        "input": str(RAW_COLLECTED.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(audit)),
        "ok_rows": int(audit["medium_support_audit_status"].eq("ok").sum()),
        "issue_rows": int((~audit["medium_support_audit_status"].eq("ok")).sum()),
        "issue_counts": issue_counts,
        "medium_category_counts": top_values(audit, "medium_category", 20),
        "support_category_counts": top_values(audit, "support_category", 20),
        "by_source": by_source,
        "samples": {
            issue: sample_records(audit, issue)
            for issue in [
                "missing_medium_raw",
                "placeholder_medium_raw",
                "medium_unmapped",
                "support_unmapped",
                "multiple_medium_matches",
                "multiple_support_matches",
                "source_category_differs",
            ]
        },
    }


def render_top(items: list[dict[str, Any]]) -> str:
    return ", ".join(f"{item['value']} `{item['count']:,}`" for item in items)


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 재료/지지체 정합성 감사",
        "",
        "- 목적: 출처별로 다른 재료 표현을 표준 재료/지지체 카테고리로 묶을 수 있는지 점검",
        f"- 입력: `{summary['input']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 정상 rows: `{summary['ok_rows']:,}`",
        f"- 이슈 rows: `{summary['issue_rows']:,}`",
        "",
        "## 1. 출처별 요약",
        "",
        "| 출처 | rows | 정상 | 이슈 | 재료 미분류 | 지지체 미분류 | 다중 재료 | 다중 지지체 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in summary["by_source"].items():
        lines.append(
            f"| {source} | `{item['rows']:,}` | `{item['ok_rows']:,}` | `{item['issue_rows']:,}` | "
            f"`{item['medium_unmapped']:,}` | `{item['support_unmapped']:,}` | "
            f"`{item['multiple_medium_matches']:,}` | `{item['multiple_support_matches']:,}` |"
        )

    lines += [
        "",
        "## 2. 표준 재료 카테고리 상위",
        "",
        f"- {render_top(summary['medium_category_counts'])}",
        "",
        "## 3. 표준 지지체 카테고리 상위",
        "",
        f"- {render_top(summary['support_category_counts'])}",
        "",
        "## 4. 이슈 카운트",
        "",
        "| 이슈 | 건수 | 해석 |",
        "|---|---:|---|",
    ]
    explanations = {
        "missing_medium_raw": "원본 재료 문자열 없음",
        "placeholder_medium_raw": "`-` 같은 자리표시값",
        "medium_unmapped": "현재 규칙으로 재료 대분류를 정하지 못함",
        "support_unmapped": "현재 규칙으로 지지체를 정하지 못함",
        "multiple_medium_matches": "여러 재료가 함께 등장함",
        "multiple_support_matches": "여러 지지체가 함께 등장함",
        "source_category_differs": "원천 분류와 1차 매핑 결과가 다름",
    }
    for issue, count in sorted(summary["issue_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| `{issue}` | `{count:,}` | {explanations.get(issue, '확인 필요')} |")

    lines += [
        "",
        "## 5. 현재 판단",
        "",
        "- 원본 재료 문자열은 반드시 `medium_raw`로 보존함",
        "- 모델 피처는 원본 문자열을 그대로 쓰기보다 `medium_category`, `support_category`로 단순화하는 것이 안전함",
        "- `Oil on canvas`, `캔버스에 유채`, `oil on Canvas`는 모두 `medium_category=oil`, `support_category=canvas`로 묶을 수 있음",
        "- `Acrylic on canvas`, `아크릴`, `Airbrushed acrylics on canvas`는 `medium_category=acrylic`으로 묶을 수 있음",
        "- `Mixed media`, `Oil and acrylic`, 재료 3개 이상 조합은 `mixed_media`로 묶는 것이 1차 기준으로 적절함",
        "- 지지체가 없는 조각/도자/디지털 작품은 `support_category=unknown`이 오류가 아닐 수 있음",
        "- Saatchi의 기존 category 컬럼은 참고용으로만 쓰고, 전체 출처 공통 규칙을 우선함",
        "",
        "## 6. 제안 매칭 규칙",
        "",
        "- 재료 표준 카테고리",
        "- `oil`, `acrylic`, `watercolor`, `ink`, `gouache`, `charcoal`, `pencil`, `pastel`, `print`, `photo`, `digital`, `ceramic`, `sculpture_material`, `textile`, `collage`, `mixed_media`, `other`, `unknown`",
        "- 지지체 표준 카테고리",
        "- `canvas`, `linen`, `paper`, `panel`, `glass`, `wood`, `metal`, `fabric`, `unknown`",
        "- 매칭 방식",
        "- 원본 문자열을 소문자/공백 정리함",
        "- 재료 키워드와 지지체 키워드를 따로 찾음",
        "- 재료가 여러 개이거나 `mixed media`가 있으면 `mixed_media`로 우선 묶음",
        "- 지지체는 첫 번째 명확한 지지체를 대표값으로 둠",
        "- 미분류 원문 상위값을 보고 규칙을 반복 보완함",
        "",
        "## 7. 클렌징 규칙 제안",
        "",
        "- `medium_raw`가 없거나 `-`이면 재료 결측 flag를 남김",
        "- `medium_category=other/unknown`은 기본 학습에서 제외하지 않고 미분류 flag로 관리",
        "- `support_category=unknown`은 조각/도자/디지털 작품일 수 있으므로 제외하지 않음",
        "- 다중 재료는 `mixed_media`로 대표화하되 원본 매칭 목록을 보존함",
        "- 다중 지지체는 대표 support와 전체 support match 목록을 함께 보존함",
        "",
        "## 8. 다음 단계",
        "",
        "- 미분류 상위 원문을 확인해 매핑 규칙 2차 보완",
        "- 이후 중복 정합성 `T4-C5` 진행",
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

    print("Track 4 medium/support consistency audit")
    print(f"rows: {summary['n_rows']:,}")
    print(f"ok: {summary['ok_rows']:,}")
    print(f"issues: {summary['issue_rows']:,}")
    print(f"issue_counts: {summary['issue_counts']}")


if __name__ == "__main__":
    main()
