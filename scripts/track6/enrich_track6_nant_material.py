#!/usr/bin/env python3
"""Attach NANT material/tool classification to Track6 clean dataset.

The reference CSV has two tables. The right-side table maps collected material
strings to NANT support/tool labels. This script applies only exact raw-material
matching first, then applies conservative English/Korean material parsing rules.
Remaining unmatched materials are exported for manual review.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"
RAW = REPO / "data" / "track4_primary_market_raw_collected.csv"
REFERENCE = REPO / "data" / "track6" / "k-artmarket 1차 데이터 정제 - 실험데이터분류.csv"
OUT = INPUT
OUT_SUMMARY = REPO / "data" / "track6" / "quality" / "track6_nant_material_enrichment_summary.json"
OUT_REPORT = REPO / "docs" / "track6" / "dataset" / "nant_material_enrichment_report.md"
OUT_UNMATCHED = REPO / "data" / "track6" / "quality" / "track6_nant_material_unmatched_review.csv"

KEYS = ["track4_source", "track4_source_row_index"]
NANT_COLUMNS = [
    "collected_material_raw",
    "nant_material_idx",
    "nant_support",
    "nant_tool",
    "nant_material_note",
    "nant_material_match_method",
]

def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return re.sub(r"\s+", " ", text)


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKC", clean_text(value)).lower()
    text = re.sub(r"[\u200b\ufeff]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_raw_material(row: pd.Series) -> str:
    source = clean_text(row.get("track4_source"))
    if source == "saatchi":
        return clean_text(row.get("saatchi__medium"))
    if source == "artsy":
        return clean_text(row.get("artsy__medium"))
    if source == "artue":
        return clean_text(row.get("artue__Medium (KO)")) or clean_text(row.get("artue__Medium (EN)"))
    if source == "gallery_primary":
        return clean_text(row.get("gallery_primary__materials"))
    return ""


def load_reference_mapping() -> pd.DataFrame:
    ref = pd.read_csv(REFERENCE, header=1, low_memory=False)
    mapping = ref.loc[:, ["idx.1", "수집 재료", "난트 기준 재료(지지체)", "난트 기준 도구(매체)", "비고"]].copy()
    mapping = mapping.dropna(subset=["수집 재료"])
    mapping = mapping.rename(
        columns={
            "idx.1": "nant_material_idx",
            "수집 재료": "collected_material_raw",
            "난트 기준 재료(지지체)": "nant_support",
            "난트 기준 도구(매체)": "nant_tool",
            "비고": "nant_material_note",
        }
    )
    for col in ["collected_material_raw", "nant_support", "nant_tool", "nant_material_note"]:
        mapping[col] = mapping[col].map(clean_text)
    mapping["nant_material_idx"] = pd.to_numeric(mapping["nant_material_idx"], errors="coerce").astype("Int64")
    mapping["_material_norm"] = mapping["collected_material_raw"].map(norm)
    mapping = mapping.sort_values("nant_material_idx").drop_duplicates("_material_norm", keep="first")
    return mapping


def load_nant_class_index() -> pd.DataFrame:
    ref = pd.read_csv(REFERENCE, header=1, low_memory=False)
    classes = ref.loc[:, ["idx", "재료(지지체)", "도구(매체)", "건수"]].copy()
    classes = classes.dropna(subset=["idx"])
    classes = classes[pd.to_numeric(classes["idx"], errors="coerce").notna()]
    classes = classes.rename(
        columns={
            "idx": "nant_material_idx",
            "재료(지지체)": "nant_support",
            "도구(매체)": "nant_tool",
            "건수": "nant_class_count_reference",
        }
    )
    classes["nant_material_idx"] = pd.to_numeric(classes["nant_material_idx"], errors="coerce").astype("Int64")
    for col in ["nant_support", "nant_tool"]:
        classes[col] = classes[col].map(clean_text)
    if classes.duplicated(["nant_support", "nant_tool"]).any():
        raise ValueError("duplicate NANT support/tool class")
    return classes


def build_raw_materials() -> pd.DataFrame:
    raw = pd.read_csv(RAW, low_memory=False)
    raw["collected_material_raw"] = raw.apply(extract_raw_material, axis=1)
    out = raw.loc[:, KEYS + ["collected_material_raw"]].copy()
    if out.duplicated(KEYS).any():
        raise ValueError("raw material join keys are not unique")
    return out


def rule_support(material: object) -> str:
    text = norm(material)
    if not text:
        return ""
    if any(token in text for token in ["canvas", "캔버스"]):
        return "캔버스"
    if any(token in text for token in ["korean paper", "mulberry paper", "hanji", "jangji", "paper", "종이", "지본", "한지", "장지"]):
        return "종이"
    if any(token in text for token in ["silk", "비단"]):
        return "비단"
    if any(token in text for token in ["wood", "wooden", "panel", "나무", "목재"]):
        return "목재"
    if any(token in text for token in ["metal", "steel", "aluminium", "aluminum", "iron", "bronze", "copper", "금속", "철", "동"]):
        return "금속"
    if any(token in text for token in ["glass", "유리"]):
        return "기타"
    if any(token in text for token in ["linen", "fabric", "textile", "cotton", "cloth", "천", "섬유", "패브릭"]):
        # Existing NANT table maps oil/acrylic on linen to canvas.
        return "캔버스"
    return ""


def rule_tool(material: object) -> str:
    text = norm(material)
    if not text:
        return ""
    if any(token in text for token in ["mixed media", "mixed-media", "mixed material", "혼합재료", "혼합 재료", "collage", "콜라주"]):
        return "혼합재료"
    if any(token in text for token in ["silkscreen", "silk screen", "screenprint", "screen print", "실크스크린"]):
        return "실크스크린"
    if any(token in text for token in ["lithograph", "woodcut", "etching", "engraving", "giclee", "pigment print", "archival pigment", "print", "석판", "판화", "프린트", "인쇄"]):
        return "판화"
    if any(token in text for token in ["photo", "digital", "diasec", "photograph", "사진", "디지털"]):
        return "사진/디지털"
    if any(token in text for token in ["ceramic", "porcelain", "stoneware", "clay", "도자"]):
        return "도자"
    if any(token in text for token in ["sculpture", "resin", "bronze", "steel", "metal", "glass", "조각"]):
        return "조각"
    if any(token in text for token in ["lacquer", "ottchil", "옻칠", "래커"]):
        return "옻칠/래커"
    if any(token in text for token in ["oil", "유채", "유화"]):
        return "유화"
    if any(token in text for token in ["acrylic", "아크릴"]):
        return "아크릴"
    if any(token in text for token in ["watercolor", "watercolour", "gouache", "수채", "과슈"]):
        return "수채"
    if any(token in text for token in ["ink", "먹", "수묵", "묵서", "묵"]):
        return "수묵"
    if any(token in text for token in ["color", "colour", "채색"]):
        return "채색"
    if any(token in text for token in ["pencil", "charcoal", "crayon", "pastel", "graphite", "연필", "드로잉", "파스텔", "목탄"]):
        return "연필/드로잉"
    if any(token in text for token in ["textile", "fabric", "thread", "embroidery", "섬유"]):
        return "섬유"
    if text in {"painting", "paint", "other", "기타"}:
        return "기타"
    return ""


def support_category_to_nant(value: object) -> str:
    support = clean_text(value)
    return {
        "canvas": "캔버스",
        "paper": "종이",
        "linen": "캔버스",
        "fabric": "섬유",
        "wood": "목재",
        "panel": "목재",
        "metal": "금속",
        "glass": "기타",
    }.get(support, "")


def align_to_nant_class(row: pd.Series, valid_combos: set[tuple[str, str]]) -> tuple[str, str]:
    support = clean_text(row.get("nant_support"))
    tool = clean_text(row.get("nant_tool"))
    if not support and not tool:
        return support, tool
    if (support, tool) in valid_combos:
        return support, tool

    if not tool and support:
        if (support, "기타") in valid_combos:
            return support, "기타"
        return "기타", "기타"

    if not support and tool:
        if tool in {"조각", "도자"} and ("없음", tool) in valid_combos:
            return "없음", tool
        if tool in {"판화", "실크스크린", "인쇄/복제"} and ("종이", tool) in valid_combos:
            return "종이", tool
        if ("기타", tool) in valid_combos:
            return "기타", tool
        return "기타", "기타"

    if support == "목재" and tool == "조각" and ("목재", "기타") in valid_combos:
        return "목재", "기타"
    if support == "기타" and tool in {"조각", "도자"} and ("없음", tool) in valid_combos:
        return "없음", tool
    if support == "기타" and tool in {"판화", "실크스크린", "인쇄/복제"} and ("종이", tool) in valid_combos:
        return "종이", tool
    if (support, "기타") in valid_combos:
        return support, "기타"
    if ("기타", tool) in valid_combos:
        return "기타", tool
    return "기타", "기타"


def render_report(summary: dict) -> str:
    lines = [
        "# Track 6 난트 기준 재료/도구 보강 보고서",
        "",
        f"- 생성일: `{summary['created_at']}`",
        f"- 정제 데이터: `{summary['input']}`",
        f"- 참고 파일: `{summary['reference']}`",
        f"- 출력: `{summary['output']}`",
        f"- 전체 rows: `{summary['rows']:,}`",
        "",
        "## 1. 추가 컬럼",
        "",
        "- `collected_material_raw`: 수집 원문 재료",
        "- `nant_material_idx`: 난트 기준 95개 재료/도구 조합 idx",
        "- `nant_support`: 난트 기준 재료/지지체",
        "- `nant_tool`: 난트 기준 도구/매체",
        "- `nant_material_note`: 참고표 비고",
        "- `nant_material_match_method`: 매칭 방식",
        "",
        "## 2. 매칭 방식",
        "",
        "- `exact_reference`: 참고표의 `수집 재료`와 원문 재료가 정확히 매칭됨",
        "- `rule_material_parse`: exact 매칭 실패 후 영문/한글 재료 표현을 규칙으로 해석함",
        "- `nant_material_idx`는 6049개 원문 조합 idx가 아니라 왼쪽 95개 난트 기준 조합 idx를 사용함",
        "- `unmatched`: 참고표와 규칙으로도 분류되지 않아 검토 목록으로 분리함",
        "",
        "## 3. 매칭 결과",
        "",
        "| method | rows |",
        "|---|---:|",
    ]
    for method, count in summary["match_method_counts"].items():
        lines.append(f"| `{method}` | `{count:,}` |")
    lines += [
        "",
        "## 4. 출처별 결과",
        "",
        "| source | rows | exact | rule | unmatched |",
        "|---|---:|---:|---:|---:|",
    ]
    for source, item in summary["source_summary"].items():
        lines.append(
            f"| `{source}` | `{item['rows']:,}` | `{item.get('exact_reference', 0):,}` | "
            f"`{item.get('rule_material_parse', 0):,}` | `{item.get('unmatched', 0):,}` |"
        )
    lines += [
        "",
        "## 5. 주의",
        "",
        "- 참고표 exact 매칭이 가장 신뢰도가 높음",
        "- rule 기반 매칭은 영문 표기 문제를 줄이기 위한 보조 기준이므로 `nant_material_match_method`로 구분함",
        f"- 미매칭 원문 재료 검토 파일: `{summary['unmatched_review_csv']}`",
        "- 미매칭은 사람이 참고표에 추가한 뒤 이 스크립트를 다시 실행하는 방식으로 관리",
        "- `nant_` 컬럼은 현재 feature export에서 기본 제외되며, 별도 가설 실험에서 명시적으로 사용할 예정",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(INPUT, low_memory=False)
    df = df.drop(columns=[col for col in NANT_COLUMNS if col in df.columns], errors="ignore")
    raw_material = build_raw_materials()
    mapping = load_reference_mapping()
    class_index = load_nant_class_index()

    out = df.merge(raw_material, on=KEYS, how="left", validate="one_to_one")
    out["_material_norm"] = out["collected_material_raw"].map(norm)
    mapped = out.merge(
        mapping.loc[:, ["_material_norm", "nant_support", "nant_tool", "nant_material_note"]],
        on="_material_norm",
        how="left",
        validate="many_to_one",
    )

    exact = mapped["nant_support"].fillna("").astype(str).str.strip().ne("") | mapped["nant_tool"].fillna("").astype(str).str.strip().ne("")
    mapped["nant_material_match_method"] = "unmatched"
    mapped.loc[exact, "nant_material_match_method"] = "exact_reference"

    need_rule = ~exact
    parsed_support = mapped.loc[need_rule, "collected_material_raw"].map(rule_support)
    parsed_tool = mapped.loc[need_rule, "collected_material_raw"].map(rule_tool)
    support_from_category = mapped.loc[need_rule, "support_category"].map(support_category_to_nant)
    parsed_support = parsed_support.where(parsed_support.ne(""), support_from_category)
    parsed_any = parsed_support.ne("") | parsed_tool.ne("")
    parsed_idx = mapped.loc[need_rule].index[parsed_any]
    mapped.loc[parsed_idx, "nant_support"] = parsed_support.loc[parsed_any].values
    mapped.loc[parsed_idx, "nant_tool"] = parsed_tool.loc[parsed_any].values
    mapped.loc[parsed_idx, "nant_material_note"] = "rule_based_material_parse"
    mapped.loc[parsed_idx, "nant_material_match_method"] = "rule_material_parse"

    mapped = mapped.drop(columns=["_material_norm"])
    valid_combos = set(zip(class_index["nant_support"], class_index["nant_tool"], strict=False))
    aligned = mapped.apply(lambda row: align_to_nant_class(row, valid_combos), axis=1)
    mapped["nant_support"] = [item[0] for item in aligned]
    mapped["nant_tool"] = [item[1] for item in aligned]
    mapped = mapped.merge(
        class_index.loc[:, ["nant_material_idx", "nant_support", "nant_tool"]],
        on=["nant_support", "nant_tool"],
        how="left",
        validate="many_to_one",
    )
    mapped["nant_material_idx"] = mapped["nant_material_idx"].astype("Int64")
    mapped.to_csv(OUT, index=False, encoding="utf-8-sig")

    unmatched = (
        mapped.loc[mapped["nant_material_match_method"].eq("unmatched")]
        .groupby(["collected_material_raw", "medium_category", "support_category"], dropna=False)
        .agg(
            rows=("track4_source", "size"),
            sources=("track4_source", lambda x: ",".join(sorted(set(map(str, x))))),
            sample_artist=("artist_name_ko", "first"),
            sample_title=("title_raw", "first"),
        )
        .reset_index()
        .sort_values(["rows", "collected_material_raw"], ascending=[False, True])
    )
    unmatched.insert(0, "review_status", "needs_mapping")
    unmatched.insert(1, "suggested_nant_support", "")
    unmatched.insert(2, "suggested_nant_tool", "")
    unmatched.insert(3, "review_note", "")
    unmatched.to_csv(OUT_UNMATCHED, index=False, encoding="utf-8-sig")

    method_counts = mapped["nant_material_match_method"].value_counts().to_dict()
    source_summary = {}
    for source, group in mapped.groupby("track4_source", dropna=False):
        counts = group["nant_material_match_method"].value_counts().to_dict()
        source_summary[str(source)] = {"rows": int(len(group)), **{k: int(v) for k, v in counts.items()}}

    summary = {
        "created_at": date.today().isoformat(),
        "input": str(INPUT.relative_to(REPO)),
        "raw": str(RAW.relative_to(REPO)),
        "reference": str(REFERENCE.relative_to(REPO)),
        "output": str(OUT.relative_to(REPO)),
        "rows": int(len(mapped)),
        "match_method_counts": {str(k): int(v) for k, v in method_counts.items()},
        "source_summary": source_summary,
        "columns_added": NANT_COLUMNS,
        "unmatched_review_csv": str(OUT_UNMATCHED.relative_to(REPO)),
        "unmatched_unique_materials": int(len(unmatched)),
        "unmatched_rows": int(mapped["nant_material_match_method"].eq("unmatched").sum()),
    }
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_REPORT.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
