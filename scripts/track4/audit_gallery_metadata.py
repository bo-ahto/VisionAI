"""Audit Track 4 gallery metadata and tier reference coverage."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
ARTIST = REPO / "data" / "track4_artist_consistency_audit.csv"
TIER_REF = REPO / "data" / "art_gallery_tier_list_v3.xlsx - 전체 리스트.csv"
OUT_CSV = REPO / "data" / "track4_gallery_metadata_audit.csv"
OUT_JSON = REPO / "data" / "track4_gallery_metadata_audit_summary.json"
OUT_MD = REPO / "docs" / "track4_gallery_metadata_audit.md"


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def key(value: object) -> str:
    text = unicodedata.normalize("NFKC", clean(value)).lower()
    text = re.sub(r"갤러리|gallery|화랑|미술관|museum", " ", text)
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_reference() -> pd.DataFrame:
    ref = pd.read_csv(TIER_REF, dtype="string", keep_default_na=False)
    ref["gallery_key"] = ref["명칭"].map(key)
    return ref


def make_audit_frame() -> pd.DataFrame:
    artist = pd.read_csv(
        ARTIST,
        usecols=["track4_source", "track4_source_file", "track4_source_row_index", "gallery_name_raw"],
        dtype="string",
        keep_default_na=False,
    )
    artist["track4_source_row_index"] = artist["track4_source_row_index"].astype(int)
    ref = load_reference()
    tier_map = ref.drop_duplicates("gallery_key").set_index("gallery_key")[["티어", "분류", "명칭"]].to_dict("index")

    rows: list[dict[str, Any]] = []
    for _, row in artist.iterrows():
        name = clean(row["gallery_name_raw"])
        gkey = key(name)
        match = tier_map.get(gkey)
        status: list[str] = []
        if not name:
            status.append("missing_gallery_name")
        elif match is None:
            status.append("gallery_tier_unmatched")
        rows.append(
            {
                "track4_source": row["track4_source"],
                "track4_source_file": row["track4_source_file"],
                "track4_source_row_index": int(row["track4_source_row_index"]),
                "gallery_name_raw": name,
                "gallery_key": gkey,
                "gallery_tier_validated": match["티어"] if match else "",
                "gallery_ref_type": match["분류"] if match else "",
                "gallery_ref_name": match["명칭"] if match else "",
                "gallery_audit_status": "ok" if not status else ";".join(status),
            }
        )
    return pd.DataFrame(rows)


def top_unmatched(audit: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    mask = audit["gallery_audit_status"].str.contains("gallery_tier_unmatched", regex=False, na=False)
    counts = audit.loc[mask & audit["gallery_name_raw"].ne(""), "gallery_name_raw"].value_counts().head(limit)
    return [{"gallery_name": str(k), "count": int(v)} for k, v in counts.items()]


def build_summary(audit: pd.DataFrame) -> dict[str, Any]:
    by_source = {}
    for source, g in audit.groupby("track4_source"):
        by_source[str(source)] = {
            "rows": int(len(g)),
            "name_available": int(g["gallery_name_raw"].ne("").sum()),
            "matched": int(g["gallery_audit_status"].eq("ok").sum()),
            "missing": int(g["gallery_audit_status"].str.contains("missing_gallery_name", regex=False).sum()),
            "unmatched": int(g["gallery_audit_status"].str.contains("gallery_tier_unmatched", regex=False).sum()),
        }
    return {
        "created_at": "2026-05-15",
        "input": str(ARTIST.relative_to(REPO)),
        "tier_reference": str(TIER_REF.relative_to(REPO)),
        "audit_csv": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(audit)),
        "matched_rows": int(audit["gallery_audit_status"].eq("ok").sum()),
        "missing_rows": int(audit["gallery_audit_status"].str.contains("missing_gallery_name", regex=False).sum()),
        "unmatched_rows": int(audit["gallery_audit_status"].str.contains("gallery_tier_unmatched", regex=False).sum()),
        "by_source": by_source,
        "top_unmatched": top_unmatched(audit),
    }


def render_md(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 4 갤러리 메타데이터 점검",
        "",
        "- 목적: 갤러리명과 티어 기준표 매칭 가능성을 확인",
        "- 결론: 갤러리/티어는 기본 모델 피처가 아니라 보조 메타데이터로 보류",
        f"- 입력: `{summary['input']}`",
        f"- 티어 기준표: `{summary['tier_reference']}`",
        f"- 감사 CSV: `{summary['audit_csv']}`",
        f"- 전체 rows: `{summary['n_rows']:,}`",
        f"- 티어 매칭 rows: `{summary['matched_rows']:,}`",
        f"- 갤러리명 결측 rows: `{summary['missing_rows']:,}`",
        f"- 티어 미매칭 rows: `{summary['unmatched_rows']:,}`",
        "",
        "## 1. 출처별 요약",
        "",
        "| 출처 | rows | 갤러리명 있음 | 티어 매칭 | 결측 | 미매칭 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source, row in summary["by_source"].items():
        lines.append(
            f"| {source} | `{row['rows']:,}` | `{row['name_available']:,}` | `{row['matched']:,}` | "
            f"`{row['missing']:,}` | `{row['unmatched']:,}` |"
        )
    lines += [
        "",
        "## 2. 미매칭 상위 갤러리명",
        "",
    ]
    for item in summary["top_unmatched"]:
        lines.append(f"- `{item['gallery_name']}`: `{item['count']:,}`")
    lines += [
        "",
        "## 3. 현재 판단",
        "",
        "- 갤러리명은 출처별 결측과 표기 차이가 큼",
        "- 티어 기준표 매칭률이 충분히 높지 않으면 모델 피처로 쓰기 어려움",
        "- 실제 운영에서 갤러리 정보를 항상 입력받는 구조가 아니라면 기본 피처에서 제외해야 함",
        "- 갤러리/티어는 데이터 품질 확인, 작가 DB 보완, 후속 실험 후보로 보류함",
        "",
        "## 4. 클렌징 반영 원칙",
        "",
        "- `gallery_name_raw`는 원본 추적용으로 유지",
        "- `gallery_tier_validated`는 기준표 매칭이 된 경우만 보조 컬럼으로 유지",
        "- 최종 feature 후보 파일에서는 갤러리/티어를 기본 입력 피처에서 제외",
        "- 별도 가설에서 갤러리 정보를 운영 입력으로 받을 수 있는 경우에만 실험",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    audit = make_audit_frame()
    audit.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    summary = build_summary(audit)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary), encoding="utf-8")
    print("Track 4 gallery metadata audit")
    print(json.dumps({k: summary[k] for k in ["n_rows", "matched_rows", "missing_rows", "unmatched_rows"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
