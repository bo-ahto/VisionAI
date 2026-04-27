"""B 모델(경매 낙찰가) 분류 재설계 — 현 파서 vs 새 분류 시트 baseline diff.

산출물: data/medium_parser_baseline_diff_<YYYYMMDD>.csv

설명: docs/B모델_분류재설계_step0_노트.md §1 (baseline 재집계) 재현용 스크립트.
- 입력: data/k-artmarket 1차 데이터 정제 - 실험데이터분류(데이터 수정).csv
- 6,049개 unique 재료 문자열에 대해 현 medium_parser.parse_medium() 호출
- 시트 라벨(난트 기준 재료/도구)과 비교한 diff CSV 생성
- L1 일치율, 다중 매체 분포, 입체 후보, 미매칭 통계 출력

Usage:
    PYTHONPATH=src python3 scripts/diff_medium_parser_baseline.py
"""
from __future__ import annotations

import csv
import logging
from collections import Counter
from datetime import date
from pathlib import Path

from visionai.price_engine.preprocessing.medium_parser import parse_medium

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "k-artmarket 1차 데이터 정제 - 실험데이터분류(데이터 수정).csv"
OUTPUT_PATH = ROOT / "data" / f"medium_parser_baseline_diff_{date.today().strftime('%Y%m%d')}.csv"

# 시트 컬럼 인덱스 (G..N = 6..13): idx, 수집 재료, 건수, 난트 기준 재료(지지체),
# 난트 기준 도구(매체), 비고, 비고2, 비고3
SHEET_RIGHT_TABLE_START = 6


def _norm(s: str) -> str:
    return s.replace(" ", "").lower()


def _to_int(s: str) -> int:
    try:
        return int(float(s)) if s.strip() else 0
    except ValueError:
        return 0


def main() -> None:
    with INPUT_PATH.open(encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    # row 0 = blank, row 1 = header, row 2+ = data
    records = []
    for r in rows[2:]:
        if len(r) < SHEET_RIGHT_TABLE_START + 8:
            continue
        idx_raw, raw, cnt_raw, sup, tool, note1, note2, note3 = r[
            SHEET_RIGHT_TABLE_START : SHEET_RIGHT_TABLE_START + 8
        ]
        if not raw or not raw.strip():
            continue

        parsed = parse_medium(raw.strip())
        sup_first = sup.split(",")[0].strip() if sup else ""
        tool_first = tool.split(",")[0].strip() if tool else ""

        records.append(
            {
                "idx": idx_raw.strip(),
                "raw_material": raw.strip(),
                "count": _to_int(cnt_raw),
                "sheet_support": sup.strip(),
                "sheet_tool": tool.strip(),
                "sheet_support_first": sup_first,
                "sheet_tool_first": tool_first,
                "sheet_support_is_multi": "," in sup,
                "sheet_tool_is_multi": "," in tool,
                "parser_support": parsed.support_category,
                "parser_medium": parsed.medium_category,
                "support_match": "Y" if _norm(parsed.support_category) == _norm(sup_first) else "N",
                "medium_match": "Y" if _norm(parsed.medium_category) == _norm(tool_first) else "N",
                "sheet_note_unmatched": note1.strip(),
                "sheet_note_excluded": note2.strip(),
                "sheet_note_extra": note3.strip(),
            }
        )

    fieldnames = [
        "idx", "raw_material", "count",
        "sheet_support", "sheet_tool",
        "sheet_support_first", "sheet_tool_first",
        "sheet_support_is_multi", "sheet_tool_is_multi",
        "parser_support", "parser_medium",
        "support_match", "medium_match",
        "sheet_note_unmatched", "sheet_note_excluded", "sheet_note_extra",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in records:
            w.writerow(rec)

    _print_stats(records)
    logger.info("Wrote %s (%d rows)", OUTPUT_PATH, len(records))


def _print_stats(records: list[dict]) -> None:
    total = len(records)
    weighted = sum(r["count"] for r in records)

    def pct(n: int, d: int) -> str:
        return f"{100 * n / d:.1f}%" if d else "—"

    medium_match = sum(1 for r in records if r["medium_match"] == "Y")
    support_match = sum(1 for r in records if r["support_match"] == "Y")
    medium_match_w = sum(r["count"] for r in records if r["medium_match"] == "Y")
    support_match_w = sum(r["count"] for r in records if r["support_match"] == "Y")
    multi_tool = sum(1 for r in records if r["sheet_tool_is_multi"])
    multi_support = sum(1 for r in records if r["sheet_support_is_multi"])
    sheet_unmatched = sum(1 for r in records if r["sheet_note_unmatched"])
    sheet_excluded = sum(1 for r in records if r["sheet_note_excluded"])
    parser_other_medium = sum(1 for r in records if r["parser_medium"] == "기타")
    parser_other_support = sum(1 for r in records if r["parser_support"] == "기타")

    logger.info("=" * 60)
    logger.info("Total unique strings : %6d   weighted: %8d", total, weighted)
    logger.info(
        "Medium L1 match      : %6d (%s)   weighted: %6d (%s)",
        medium_match, pct(medium_match, total),
        medium_match_w, pct(medium_match_w, weighted),
    )
    logger.info(
        "Support L1 match     : %6d (%s)   weighted: %6d (%s)",
        support_match, pct(support_match, total),
        support_match_w, pct(support_match_w, weighted),
    )
    logger.info("Multi-tool rows      : %6d   Multi-support rows: %d", multi_tool, multi_support)
    logger.info("Sheet '분류 미매칭'  : %6d   Sheet '학습 제외': %d", sheet_unmatched, sheet_excluded)
    logger.info("Parser '기타' medium : %6d   Parser '기타' support: %d", parser_other_medium, parser_other_support)

    # Top mismatches
    medium_mis: Counter[tuple[str, str]] = Counter()
    for r in records:
        if r["medium_match"] == "N":
            medium_mis[(r["parser_medium"], r["sheet_tool_first"])] += r["count"]
    logger.info("Top 10 medium mismatches (parser → sheet, weighted):")
    for (p, s), c in medium_mis.most_common(10):
        logger.info("  %14s | %-14s | %6d", p, s, c)


if __name__ == "__main__":
    main()
