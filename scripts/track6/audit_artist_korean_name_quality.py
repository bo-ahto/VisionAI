#!/usr/bin/env python3
"""Track6 artist_name_ko 품질 감사.

목적:
- `improve_artist_korean_names.py` 적용 후에도 남아 있는 어색한 한글 음역을 찾는다.
- 자동 수정하지 않고, 수동 검토 우선순위를 CSV와 Markdown으로 남긴다.

기준:
- `흐`, `운그`, `우르`, `페르`처럼 영어 철자를 기계적으로 끊어 읽은 흔적
- 한글 음절 수가 과도하게 긴 이름
- studio/gallery/official 등 브랜드성 이름인데 공백 없이 붙은 한글 표기

출력:
- data/track6/quality/track6_artist_name_ko_quality_audit.csv
- docs/track6/dataset/artist_name_ko_quality_audit.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track6" / "quality" / "track6_artist_name_ko_review_candidates.csv"
OUT_CSV = REPO / "data" / "track6" / "quality" / "track6_artist_name_ko_quality_audit.csv"
OUT_MD = REPO / "docs" / "track6" / "dataset" / "artist_name_ko_quality_audit.md"

AWKWARD_PATTERNS = [
    "흐",
    "운그",
    "우르",
    "에예",
    "쿠엔",
    "페르",
    "엑스응",
    "다이",
    "그와",
    "프하",
    "브브",
    "크흐",
]
BRAND_HINT_RE = re.compile(r"(studio|gallery|official|artist|digital|day|pen|stepper|label)", re.I)


def hangul_only(value: object) -> str:
    return re.sub(r"[^가-힣]", "", str(value or ""))


def risk(row: pd.Series) -> tuple[int, list[str]]:
    ko = str(row.get("current_artist_name_ko") or "")
    key = str(row.get("artist_key") or "")
    score = 0
    reasons: list[str] = []

    if len(hangul_only(ko)) >= 8:
        score += 1
        reasons.append("long_hangul_ge_8")

    for pattern in AWKWARD_PATTERNS:
        if pattern in ko:
            score += 1
            reasons.append(f"awkward_{pattern}")

    if BRAND_HINT_RE.search(key) and " " not in ko and len(hangul_only(ko)) >= 5:
        score += 1
        reasons.append("brand_or_studio_spacing_review")

    return score, reasons


def main() -> None:
    df = pd.read_csv(INPUT, low_memory=False)
    rows = []
    for _, row in df.iterrows():
        score, reasons = risk(row)
        if score <= 0:
            continue
        item = row.to_dict()
        item["quality_risk_score"] = score
        item["quality_risk_reasons"] = ",".join(reasons)
        rows.append(item)

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["quality_risk_score", "rows", "artist_key"], ascending=[False, False, True])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    lines = [
        "# Track6 artist_name_ko 품질 감사",
        "",
        f"- 입력: `{INPUT.relative_to(REPO)}`",
        f"- 출력: `{OUT_CSV.relative_to(REPO)}`",
        f"- 위험 후보 artist_key 수: `{out['artist_key'].nunique() if not out.empty else 0:,}`",
        f"- 위험 후보 rows 합계: `{int(out['rows'].sum()) if not out.empty else 0:,}`",
        "",
        "## 상위 후보",
        "",
        "| rows | artist_key | 현재 한글명 | risk | reasons |",
        "|---:|---|---|---:|---|",
    ]
    for _, row in out.head(80).iterrows():
        lines.append(
            f"| `{int(row['rows']):,}` | `{row['artist_key']}` | {row['current_artist_name_ko']} | "
            f"`{int(row['quality_risk_score'])}` | `{row['quality_risk_reasons']}` |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print({
        "risk_artist_keys": int(out["artist_key"].nunique()) if not out.empty else 0,
        "risk_rows": int(out["rows"].sum()) if not out.empty else 0,
        "output": str(OUT_CSV.relative_to(REPO)),
    })


if __name__ == "__main__":
    main()
