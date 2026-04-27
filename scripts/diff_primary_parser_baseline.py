"""A 모델(1차 시장) 분류 재설계 — 새 시트 룰 vs 현 영문 8-class 분류기 baseline.

산출물: data/primary_parser_baseline_diff_<YYYYMMDD>.csv

설명: docs/A모델_분류재설계_step0_노트.md 의 baseline 측정용. 코드 변경 없음.
- 입력 (A 학습 데이터):
  - data/artsy_kr_artworks.json (30,046 works, Painting 20,616)
  - data/saatchi_kr_artworks.json (30,607 works, painting 23,773)
- 새 분류 시트:
  - data/k-artmarket 1차 데이터 정제 - 지지체(바탕재) 분류.csv (36 leaves)
  - data/k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv (108 leaves)

본 스크립트는 시트 keyword 컬럼(한/영 혼합)을 단순 substring 매칭한다. 본격적인
파서(토큰화 + on/and 패턴 등)는 PR1에서 구현. 본 스크립트 결과는 "단순 keyword
substring으로 얼마까지 잡히는지"의 lower bound 및 입체 sneak-in 검출 용도다.

Usage:
    PYTHONPATH=src python3 scripts/diff_primary_parser_baseline.py
"""
from __future__ import annotations

import csv
import json
import logging
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SHEET_SUPPORT = DATA / "k-artmarket 1차 데이터 정제 - 지지체(바탕재) 분류.csv"
SHEET_TOOL = DATA / "k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv"
ARTSY_PATH = DATA / "artsy_kr_artworks.json"
SAATCHI_PATH = DATA / "saatchi_kr_artworks.json"
OUT_CSV = DATA / f"primary_parser_baseline_diff_{date.today().strftime('%Y%m%d')}.csv"

# 입체 sneak-in 검출 키워드 (Painting 카테고리 안에 들어 있을 가능성)
THREE_D_KEYWORDS = [
    # 영문
    r"\bbronze\b", r"\bporcelain\b", r"\bceramic\b", r"\bstoneware\b",
    r"\bterracotta\b", r"\bglass\b(?!\s*pigment)", r"\bstainless\b",
    r"\bsculpt", r"\bcarved\b", r"\bcarving\b", r"\binstallation\b",
    r"\bbas-relief\b", r"\brelief sculpture\b", r"\bcast\b(?!\s*iron)",
    r"\bfigurine\b", r"\bbust\b",
    # 한글
    r"조각", r"입체", r"브론즈", r"청동", r"도자", r"세라믹", r"백자", r"분청",
    r"옹기", r"태피스트리",
]
THREE_D_RE = re.compile("|".join(THREE_D_KEYWORDS), re.IGNORECASE)


def load_sheet_keywords(path: Path, name_col: int, keyword_col: int) -> list[tuple[str, str, str, list[str]]]:
    """시트에서 (대분류, 중분류, leaf, [keywords...]) 튜플 list 반환.

    각 keyword는 phrase 단위. "유화 oil" 같은 mixed phrase는 영문 단어 추출도 추가
    (한국어 substring 매칭 + 영문 word boundary 매칭 둘 다 가능하도록).
    """
    rules = []
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)
    for r in rows[1:]:  # skip header
        if len(r) < max(name_col, keyword_col) + 1:
            continue
        l1 = r[0].strip() if r[0].strip() else ""
        l2 = r[1].strip() if len(r) > 1 else ""
        leaf = r[name_col].strip() if r[name_col].strip() else ""
        kw_raw = r[keyword_col].strip() if r[keyword_col].strip() else ""
        if not leaf:
            continue
        keywords: list[str] = [leaf]
        if kw_raw:
            parts = re.split(r"[,，/]|\s+or\s+", kw_raw)
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                keywords.append(p)
                # phrase에 영문 단어가 섞여 있으면 영문 단어 자체도 keyword로
                # (예: "유화 oil" → ["유화 oil", "oil"])
                eng_words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", p)
                for ew in eng_words:
                    if ew.lower() not in {"on", "and", "with", "the", "of"}:
                        keywords.append(ew)
        # deduplicate (case-insensitive)
        seen, uniq = set(), []
        for k in keywords:
            kn = k.lower()
            if kn and kn not in seen:
                seen.add(kn)
                uniq.append(k)
        rules.append((l1, l2, leaf, uniq))
    return rules


def _kw_matches(kw: str, text_l: str) -> bool:
    """keyword 매칭. 영문 단어는 word boundary, 한국어/혼합은 substring."""
    kw_l = kw.lower()
    if re.fullmatch(r"[a-z][a-z\-]*", kw_l):
        # pure English word → word boundary
        return bool(re.search(r"\b" + re.escape(kw_l) + r"\b", text_l))
    return kw_l in text_l


def match_first_leaf(text: str, rules: list[tuple[str, str, str, list[str]]]) -> Optional[tuple[str, str, str]]:
    """text에 키워드가 있는 첫 leaf 반환. (l1, l2, leaf)."""
    if not text:
        return None
    text_l = text.lower()
    for l1, l2, leaf, keywords in rules:
        for kw in keywords:
            if _kw_matches(kw, text_l):
                return (l1, l2, leaf)
    return None


def match_all_leaves(text: str, rules: list[tuple[str, str, str, list[str]]]) -> list[tuple[str, str, str]]:
    """text에 키워드가 있는 모든 leaf 반환 (중복 leaf는 제거)."""
    if not text:
        return []
    text_l = text.lower()
    seen = set()
    matches = []
    for l1, l2, leaf, keywords in rules:
        if leaf in seen:
            continue
        for kw in keywords:
            if _kw_matches(kw, text_l):
                matches.append((l1, l2, leaf))
                seen.add(leaf)
                break
    return matches


def main() -> None:
    # Load sheet rules
    support_rules = load_sheet_keywords(SHEET_SUPPORT, name_col=2, keyword_col=3)
    tool_rules = load_sheet_keywords(SHEET_TOOL, name_col=2, keyword_col=3)
    logger.info("Loaded %d support leaves, %d tool leaves", len(support_rules), len(tool_rules))

    # Process Artsy
    with ARTSY_PATH.open(encoding="utf-8") as f:
        artsy = json.load(f)
    # Process Saatchi
    with SAATCHI_PATH.open(encoding="utf-8") as f:
        saatchi = json.load(f)

    rows_out = []

    # ARTSY
    for w in artsy:
        cat = w.get("category", "")
        med = (w.get("medium") or "").strip()
        sup_match = match_first_leaf(med, support_rules)
        tool_match = match_first_leaf(med, tool_rules)
        all_tools = match_all_leaves(med, tool_rules)
        all_supports = match_all_leaves(med, support_rules)
        sneak = bool(THREE_D_RE.search(med)) if med else False
        is_painting = cat == "Painting"

        rows_out.append({
            "source": "artsy",
            "id": w.get("id", "") or w.get("artsy_id", ""),
            "category": cat,
            "raw_materials": "",
            "raw_mediums": med,
            "support_l1": sup_match[0] if sup_match else "",
            "support_leaf": sup_match[2] if sup_match else "",
            "tool_l1": tool_match[0] if tool_match else "",
            "tool_leaf": tool_match[2] if tool_match else "",
            "tool_count": len(all_tools),
            "support_count": len(all_supports),
            "tool_leaves_all": "|".join(t[2] for t in all_tools),
            "support_leaves_all": "|".join(s[2] for s in all_supports),
            "has_3d_keyword": int(sneak),
            "is_painting": int(is_painting),
            "sneak_in_painting": int(is_painting and sneak),
        })

    # SAATCHI
    for w in saatchi:
        cat = (str(w.get("category") or "")).lower()
        mat = (w.get("materials") or "").strip()
        med = (w.get("mediums") or "").strip()
        # Saatchi support는 materials + mediums 합쳐서 매칭
        combined = f"{mat} {med}".strip()
        sup_match = match_first_leaf(mat, support_rules) or match_first_leaf(combined, support_rules)
        tool_match = match_first_leaf(med, tool_rules) or match_first_leaf(combined, tool_rules)
        all_tools = match_all_leaves(med, tool_rules)
        all_supports = match_all_leaves(mat, support_rules)
        sneak = bool(THREE_D_RE.search(combined)) if combined else False
        is_painting = cat == "painting"

        rows_out.append({
            "source": "saatchi",
            "id": w.get("id", ""),
            "category": cat,
            "raw_materials": mat,
            "raw_mediums": med,
            "support_l1": sup_match[0] if sup_match else "",
            "support_leaf": sup_match[2] if sup_match else "",
            "tool_l1": tool_match[0] if tool_match else "",
            "tool_leaf": tool_match[2] if tool_match else "",
            "tool_count": len(all_tools),
            "support_count": len(all_supports),
            "tool_leaves_all": "|".join(t[2] for t in all_tools),
            "support_leaves_all": "|".join(s[2] for s in all_supports),
            "has_3d_keyword": int(sneak),
            "is_painting": int(is_painting),
            "sneak_in_painting": int(is_painting and sneak),
        })

    # Write CSV
    fieldnames = [
        "source", "id", "category",
        "raw_materials", "raw_mediums",
        "support_l1", "support_leaf",
        "tool_l1", "tool_leaf",
        "tool_count", "support_count",
        "tool_leaves_all", "support_leaves_all",
        "has_3d_keyword", "is_painting", "sneak_in_painting",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in rows_out:
            w.writerow(rec)

    _print_stats(rows_out)
    logger.info("Wrote %s (%d rows)", OUT_CSV, len(rows_out))


def _print_stats(rows: list[dict]) -> None:
    artsy = [r for r in rows if r["source"] == "artsy"]
    saatchi = [r for r in rows if r["source"] == "saatchi"]

    def stats(name: str, sub: list[dict]) -> None:
        n = len(sub)
        if n == 0:
            return
        painting = sum(1 for r in sub if r["is_painting"])
        sup_match = sum(1 for r in sub if r["support_l1"])
        tool_match = sum(1 for r in sub if r["tool_l1"])
        sup_match_p = sum(1 for r in sub if r["is_painting"] and r["support_l1"])
        tool_match_p = sum(1 for r in sub if r["is_painting"] and r["tool_l1"])
        multi_tool = sum(1 for r in sub if r["tool_count"] >= 2)
        multi_supp = sum(1 for r in sub if r["support_count"] >= 2)
        sneak = sum(1 for r in sub if r["sneak_in_painting"])

        def pct(a, b):
            return f"{100*a/b:.1f}%" if b else "—"

        logger.info("=" * 60)
        logger.info(f"[{name}] {n} works (Painting subset: {painting})")
        logger.info("  Support sheet match (전체)   : %5d (%s)", sup_match, pct(sup_match, n))
        logger.info("  Tool sheet match (전체)      : %5d (%s)", tool_match, pct(tool_match, n))
        logger.info("  Support match (Painting only): %5d (%s)", sup_match_p, pct(sup_match_p, painting))
        logger.info("  Tool match (Painting only)   : %5d (%s)", tool_match_p, pct(tool_match_p, painting))
        logger.info("  Multi-tool (>=2 leaves)      : %5d (%s)", multi_tool, pct(multi_tool, n))
        logger.info("  Multi-support (>=2 leaves)   : %5d (%s)", multi_supp, pct(multi_supp, n))
        logger.info("  Painting + 3D keyword (sneak): %5d (%s)", sneak, pct(sneak, painting))

    stats("ARTSY", artsy)
    stats("SAATCHI", saatchi)

    # Top sneak-in mediums
    sneak_med = Counter()
    for r in rows:
        if r["sneak_in_painting"]:
            sneak_med[(r["source"], r["raw_mediums"][:80])] += 1
    if sneak_med:
        logger.info("\nTop 3D-keyword in Painting (sneak):")
        for (src, m), c in sneak_med.most_common(15):
            logger.info("  %5d | %-7s | %s", c, src, m)

    # Top unmatched (Painting + tool 미매칭)
    unmatched = Counter()
    for r in rows:
        if r["is_painting"] and not r["tool_l1"] and r["raw_mediums"]:
            unmatched[(r["source"], r["raw_mediums"][:80])] += 1
    if unmatched:
        logger.info("\nTop Painting + tool 미매칭:")
        for (src, m), c in unmatched.most_common(15):
            logger.info("  %5d | %-7s | %s", c, src, m)


if __name__ == "__main__":
    main()
