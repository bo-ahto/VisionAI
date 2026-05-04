"""v3 갤러리 리스트(88건) + Top30 검수 결과(30건) → v4 리스트(118건) 생성.

v4 schema (4 컬럼): 티어 / 분류 / 명칭 / 비고

분류 정규화 규칙:
- "기타(플랫폼)" → 분류="기타", 비고에 "플랫폼" 보존
- "기타(전시기획사)" → 분류="기타", 비고에 "전시기획사" 보존
- 단순 "기타" / "갤러리" / "기관" → 그대로

코덱스 자문 반영:
- 매핑 테이블은 별도 CSV로 외부화 (build_gallery_alias_map.py 참조)
- 본 스크립트는 v3 → v4 만 수행

Usage:
    python3 scripts/build_gallery_tier_v4.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

V3_CSV = DATA / "art_gallery_tier_list_v3.xlsx - 전체 리스트.csv"
TOP30_CSV = DATA / "top30_피드백.csv"
V4_CSV = DATA / "art_gallery_tier_list_v4.csv"


def normalize_classification(raw: str) -> tuple[str, str]:
    """분류 값을 정규화. 괄호 안 정보는 비고로 분리.

    Returns: (분류, 비고_조각)
    """
    if not isinstance(raw, str) or not raw.strip():
        return ("", "")
    raw = raw.strip()
    m = re.match(r"^(갤러리|기관|기타)\(([^)]+)\)$", raw)
    if m:
        return (m.group(1), m.group(2))
    if raw in {"갤러리", "기관", "기타"}:
        return (raw, "")
    return (raw, "")


def main() -> None:
    v3 = pd.read_csv(V3_CSV).dropna(subset=["명칭"])
    print(f"v3 리스트 로드: {len(v3)}건")

    top30 = pd.read_csv(TOP30_CSV)
    print(f"Top30 검수 로드: {len(top30)}건")

    rows = []
    for _, r in v3.iterrows():
        rows.append(
            {
                "티어": str(r["티어"]).strip(),
                "분류": str(r["분류"]).strip(),
                "명칭": str(r["명칭"]).strip(),
                "비고": "",
                "출처": "v3",
            }
        )

    skipped_no_yes = 0
    for _, r in top30.iterrows():
        if str(r.get("리스트_추가_여부", "")).strip().lower() != "yes":
            skipped_no_yes += 1
            continue
        cls_norm, sub = normalize_classification(str(r["분류"]))
        existing_note = str(r.get("비고", "") or "").strip()
        bigo_parts = [p for p in [sub, existing_note] if p]
        bigo = " · ".join(bigo_parts)
        rows.append(
            {
                "티어": str(r["티어"]).strip(),
                "분류": cls_norm,
                "명칭": str(r["명칭_한글_확정"]).strip(),
                "비고": bigo,
                "출처": "top30",
            }
        )

    if skipped_no_yes:
        print(f"⚠️ 리스트_추가_여부=no/공란 으로 skip: {skipped_no_yes}건")

    v4 = pd.DataFrame(rows)
    duplicated = v4["명칭"].duplicated(keep=False)
    if duplicated.any():
        print("⚠️ 중복 명칭 감지:")
        print(v4[duplicated][["명칭", "출처", "티어", "분류"]].to_string(index=False))

    v4 = v4.drop_duplicates(subset=["명칭"], keep="first")
    v4_out = v4[["티어", "분류", "명칭", "비고"]].reset_index(drop=True)
    v4_out.to_csv(V4_CSV, index=False, encoding="utf-8-sig")

    print(f"\nv4 리스트 출력: {V4_CSV}")
    print(f"  총 {len(v4_out)}건 (v3 {len(v3)} + top30 {len(top30) - skipped_no_yes} - 중복 {len(rows) - len(v4_out)})")
    print("\n=== 분류 분포 ===")
    print(v4_out["분류"].value_counts(dropna=False).to_string())
    print("\n=== 티어 분포 ===")
    print(v4_out["티어"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
