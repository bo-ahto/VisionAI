"""갤러리 티어 매핑 커버리지 분석 (Phase 1A).

배경:
- 협력자 제공 art_gallery_tier_list_v3는 한글 갤러리명 89개
- Artsy 데이터는 영문 66개, Saatchi는 "Saatchi Art" 단일
- 단순 매칭으로 0개 → 한글-영문 매핑 테이블 수기 작성 후 매칭률 측정

목적:
- 영문→한글 매핑 결과로 매칭 가능한 작품 비중 측정
- Tier 분포 분석
- Phase 1B(피처 도입) 진행 의미 있는지 판정 근거 자료

산출물:
- model_test_results/gallery_tier_coverage.json
- model_test_results/gallery_tier_coverage_report.md

Usage:
    PYTHONPATH=src python3 scripts/analyze_gallery_tier_coverage.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


# ─── 영문 갤러리명 → 협력자 리스트의 한글명 매핑 ──────────────────────────
# Artsy 데이터의 66개 갤러리 중 협력자 리스트(89개)와 매칭되는 케이스.
# 나머지 미매칭은 Tier E (리스트 미등재) 처리.
ARTSY_TO_KOR_GALLERY: dict[str, str] = {
    # 확인된 매칭 (협력자 리스트의 갤러리와 동일/유사)
    "Kimreeaa Gallery": "김리아갤러리",
    "Art Sohyang": "아트소향",
    "BHAK": "BHAK(비에이치에이케이)",
    "Gallery Planet": "갤러리 플래닛",
    "CHOI&CHOI": "초이앤초이 갤러리",
    "CYLINDER": "실린더",
    "Leehwaik Gallery": "이화익갤러리",
    "SPACE Willing N Dealing": "스페이스 윌링앤딜링",
    "ThisWeekendRoom": "디스위켄드룸",
    "FOUNDRY SEOUL": "파운드리 서울",
    "Artside Gallery": "아트사이드 갤러리",
    # 검증 필요한 추가 후보 (영문 ↔ 한글 단순 매칭 외 케이스 — 협력자 확인 필요):
    # "Kukje Gallery": "국제갤러리",  # Artsy 데이터에 없음
    # "Gana Art": "가나아트",          # Artsy 데이터에 없음
    # "Gallery Hyundai": "갤러리현대", # Artsy 데이터에 없음
    # 위 메인스트림 Tier A 갤러리들은 Artsy 데이터셋에 등록 안 됨 (Frieze/Art Basel 위주)
}


# ─── 협력자 리스트 한글명 → (Tier, Class) ──────────────────────────────
def load_tier_lookup() -> dict[str, tuple[str, str]]:
    """art_gallery_tier_list_v3.xlsx - 전체 리스트.csv 로드."""
    tier_csv = DATA / "art_gallery_tier_list_v3.xlsx - 전체 리스트.csv"
    df = pd.read_csv(tier_csv)
    lookup: dict[str, tuple[str, str]] = {}
    for _, row in df.iterrows():
        name = str(row["명칭"]).strip()
        tier = str(row["티어"]).strip()  # "Tier A" 등
        cls = str(row["분류"]).strip()
        lookup[name] = (tier, cls)
    return lookup


# Tier 라벨 → ordinal (높을수록 좋음 — 티어 A가 최상위)
TIER_ORDINAL = {"Tier A": 5, "Tier B": 4, "Tier C": 3, "Tier D": 2, "Tier E": 1}


def determine_gallery_tier_class(
    gallery_name: str | None, tier_lookup: dict[str, tuple[str, str]]
) -> tuple[str, str]:
    """gallery_name → (tier, class). 미매칭은 ("Tier E", "미분류")."""
    if not gallery_name or pd.isna(gallery_name):
        return ("Tier E", "미분류")
    gallery_name = str(gallery_name).strip()
    # Saatchi 단일값 — 별도 처리 (Online Platform → Tier E)
    if gallery_name == "Saatchi Art":
        return ("Tier E", "온라인 플랫폼")
    # 영문 → 한글 매핑 시도
    kor_name = ARTSY_TO_KOR_GALLERY.get(gallery_name, gallery_name)
    if kor_name in tier_lookup:
        tier, cls = tier_lookup[kor_name]
        return (tier, cls)
    # 미매칭 → E (리스트 미등재)
    return ("Tier E", "미분류")


def analyze() -> dict:
    """Artsy + Saatchi 데이터에 매핑 적용 후 커버리지 측정."""
    tier_lookup = load_tier_lookup()
    logger.info("Tier list loaded: %d 갤러리/기관", len(tier_lookup))

    # 데이터 로드
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")
    logger.info("Artsy: %d 작품, %d 갤러리", len(artsy), artsy["gallery_name"].nunique())
    logger.info("Saatchi: %d 작품, %d 갤러리", len(saatchi), saatchi["gallery_name"].nunique())

    # 갤러리별 매칭
    artsy_gallery_counts = artsy["gallery_name"].value_counts()
    matched_galleries = []
    unmatched_galleries = []
    for name, cnt in artsy_gallery_counts.items():
        kor_name = ARTSY_TO_KOR_GALLERY.get(str(name), str(name))
        if kor_name in tier_lookup:
            tier, cls = tier_lookup[kor_name]
            matched_galleries.append({"name": name, "kor": kor_name, "tier": tier, "class": cls, "n": int(cnt)})
        else:
            unmatched_galleries.append({"name": name, "n": int(cnt)})

    # 작품 수 기준 매칭 비중
    artsy_matched_works = sum(g["n"] for g in matched_galleries)
    artsy_unmatched_works = sum(g["n"] for g in unmatched_galleries)

    # Saatchi (Saatchi Art 단일 — 별도 처리)
    saatchi_works = len(saatchi)

    # 데이터 전체에 적용한 후 분포
    artsy = artsy.copy()
    artsy["gallery_tier_v3"] = artsy["gallery_name"].apply(
        lambda n: determine_gallery_tier_class(n, tier_lookup)[0]
    )
    artsy["gallery_class"] = artsy["gallery_name"].apply(
        lambda n: determine_gallery_tier_class(n, tier_lookup)[1]
    )
    saatchi = saatchi.copy()
    saatchi["gallery_tier_v3"] = "Tier E"
    saatchi["gallery_class"] = "온라인 플랫폼"

    # 통합
    combined_tier = pd.concat([artsy["gallery_tier_v3"], saatchi["gallery_tier_v3"]], ignore_index=True)
    combined_class = pd.concat([artsy["gallery_class"], saatchi["gallery_class"]], ignore_index=True)

    result = {
        "artsy": {
            "total_works": int(len(artsy)),
            "total_galleries": int(artsy["gallery_name"].nunique()),
            "matched_galleries_count": len(matched_galleries),
            "unmatched_galleries_count": len(unmatched_galleries),
            "matched_works": artsy_matched_works,
            "unmatched_works": artsy_unmatched_works,
            "matched_works_pct": round(100 * artsy_matched_works / len(artsy), 1),
            "tier_distribution": {k: int(v) for k, v in artsy["gallery_tier_v3"].value_counts().items()},
            "class_distribution": {k: int(v) for k, v in artsy["gallery_class"].value_counts().items()},
            "matched_galleries": matched_galleries,
            "unmatched_galleries_top": unmatched_galleries[:30],
        },
        "saatchi": {
            "total_works": saatchi_works,
            "tier_distribution": {"Tier E": saatchi_works},
            "class_distribution": {"온라인 플랫폼": saatchi_works},
            "note": "Saatchi Art 단일 — 갤러리 개념 미적용, 모두 Tier E (온라인 플랫폼)",
        },
        "combined": {
            "total_works": int(len(combined_tier)),
            "tier_distribution": {k: int(v) for k, v in combined_tier.value_counts().items()},
            "class_distribution": {k: int(v) for k, v in combined_class.value_counts().items()},
        },
    }
    return result


def write_report(result: dict, out_md: Path) -> None:
    artsy = result["artsy"]
    saatchi = result["saatchi"]
    combined = result["combined"]

    lines = [
        "# 갤러리 티어 매핑 커버리지 분석 (Phase 1A)",
        "",
        f"- 협력자 리스트: 89 갤러리/기관",
        f"- Artsy 데이터: {artsy['total_works']:,} 작품 / {artsy['total_galleries']} 갤러리",
        f"- Saatchi 데이터: {saatchi['total_works']:,} 작품 (Saatchi Art 단일)",
        "",
        "## Artsy 매칭 결과",
        "",
        f"- 매칭된 갤러리: **{artsy['matched_galleries_count']}/{artsy['total_galleries']}** ({100*artsy['matched_galleries_count']/artsy['total_galleries']:.0f}%)",
        f"- 매칭된 작품: **{artsy['matched_works']:,}/{artsy['total_works']:,}** ({artsy['matched_works_pct']}%)",
        "",
        "### 매칭된 갤러리 (작품 수 내림차순)",
        "",
        "| Artsy 영문명 | 한글 매칭 | Tier | Class | 작품 수 |",
        "|---|---|:---:|---|---:|",
    ]
    for g in sorted(artsy["matched_galleries"], key=lambda x: -x["n"]):
        lines.append(f"| {g['name']} | {g['kor']} | {g['tier']} | {g['class']} | {g['n']:,} |")

    lines.extend([
        "",
        "### Tier 분포 (Artsy)",
        "",
        "| Tier | 작품 수 | 비중 |",
        "|:---:|---:|---:|",
    ])
    for tier in ["Tier A", "Tier B", "Tier C", "Tier D", "Tier E"]:
        n = artsy["tier_distribution"].get(tier, 0)
        pct = 100 * n / artsy["total_works"] if artsy["total_works"] else 0
        lines.append(f"| {tier} | {n:,} | {pct:.1f}% |")

    lines.extend([
        "",
        "### Class 분포 (Artsy)",
        "",
        "| Class | 작품 수 | 비중 |",
        "|---|---:|---:|",
    ])
    for cls, n in sorted(artsy["class_distribution"].items(), key=lambda x: -x[1]):
        pct = 100 * n / artsy["total_works"]
        lines.append(f"| {cls} | {n:,} | {pct:.1f}% |")

    lines.extend([
        "",
        "## Saatchi",
        "",
        f"{saatchi['note']}",
        "",
        "## 통합 (Artsy + Saatchi)",
        "",
        "### Tier 분포",
        "",
        "| Tier | 작품 수 | 비중 |",
        "|:---:|---:|---:|",
    ])
    for tier in ["Tier A", "Tier B", "Tier C", "Tier D", "Tier E"]:
        n = combined["tier_distribution"].get(tier, 0)
        pct = 100 * n / combined["total_works"]
        lines.append(f"| {tier} | {n:,} | {pct:.1f}% |")

    lines.extend([
        "",
        "## 미매칭 갤러리 Top 30 (Artsy)",
        "",
        "| 영문명 | 작품 수 | 비고 |",
        "|---|---:|---|",
    ])
    for g in artsy["unmatched_galleries_top"]:
        lines.append(f"| {g['name']} | {g['n']:,} | — |")

    tier_ad_combined = sum(
        combined["tier_distribution"].get(t, 0) for t in ["Tier A", "Tier B", "Tier C", "Tier D"]
    )
    tier_a_n = combined["tier_distribution"].get("Tier A", 0)
    tier_d_n = combined["tier_distribution"].get("Tier D", 0)
    tier_b_n = combined["tier_distribution"].get("Tier B", 0)
    tier_c_n = combined["tier_distribution"].get("Tier C", 0)

    lines.extend([
        "",
        "## 결론 — Phase 1B 진행 판단",
        "",
        f"- **Artsy 매칭 비중**: {artsy['matched_works_pct']}% ({artsy['matched_works']:,}/{artsy['total_works']:,})",
        f"- **통합 Tier A~D**: {tier_ad_combined:,} / {combined['total_works']:,} "
        f"({100*tier_ad_combined/combined['total_works']:.1f}%)",
        f"- **Tier A**: {tier_a_n}건  /  **Tier D**: {tier_d_n}건",
        f"- **Tier B**: {tier_b_n}건  /  **Tier C**: {tier_c_n}건",
        f"- **Tier E**: {combined['tier_distribution'].get('Tier E', 0):,}건 "
        f"({100*combined['tier_distribution'].get('Tier E',0)/combined['total_works']:.1f}%)",
        "",
        "### 판정: **Phase 1B (피처 도입) 보류 권장**",
        "",
        "근거:",
        "1. **Tier A/D = 0건** — 분류 5단계 중 2단계가 학습 데이터에 존재하지 않음. "
        "사실상 binary 신호(`Tier B/C` vs `Tier E`)로 축소됨.",
        "2. **Tier E = 96.6%** — 통합 데이터의 96.6%가 미분류로 떨어짐 (Saatchi 21,721건 + "
        "Artsy 미매칭 6,641건). 압도적 대다수가 같은 값이면 모델이 신호로 학습할 정보량이 거의 없음.",
        "3. **Artsy 메인스트림 부재** — Tier A 갤러리(국제갤러리, 가나아트, 갤러리현대 등)는 "
        "Artsy 데이터셋에 등록되어 있지 않음(Frieze/Art Basel 메인 갤러리들은 별도 채널 사용). "
        "협력자 리스트의 핵심 변별력이 학습 데이터에 반영되지 않음.",
        "4. **이미 `gallery_tier` 피처 존재** — `primary_predictor.py`의 기존 `gallery_tier` "
        "(galleries_count 기반 휴리스틱)가 동일 신호의 일부를 이미 학습 중. "
        "v3 매핑 추가 효과는 한계.",
        "",
        "### 대안",
        "",
        "- **A. 데이터 확장**: Artsy 외 채널(갤러리 자체 사이트, 아트뉴스, 미술시장 데이터) 수집으로 "
        "Tier A 갤러리 데이터를 확보한 후 재시도.",
        "- **B. 협력자 검수**: 미매칭 Top 갤러리 30개에 대해 협력자가 한글명 매핑 또는 Tier 부여를 "
        "추가 검토 (현재 매핑 11개 → 30~40개로 확장 가능성).",
        "- **C. 다른 P0 액션 우선**: `MdAPE_개선_액션플랜_20260427.md`의 다른 항목 "
        "(career-stage v2, source-split-models, cold-start-data-enrichment)을 먼저 진행.",
        "",
        "### 다음 단계 권장",
        "",
        "- 본 리포트를 협력자에게 공유 → 미매칭 Top 갤러리 매핑 검수 요청",
        "- 그 사이 P0 다른 항목(career-stage v2 등)부터 진행",
        "",
    ])
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = analyze()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "gallery_tier_coverage.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("Saved: %s", out_json)

    out_md = OUT_DIR / "gallery_tier_coverage_report.md"
    write_report(result, out_md)
    logger.info("Saved: %s", out_md)

    # 요약 출력
    artsy = result["artsy"]
    combined = result["combined"]
    logger.info("=" * 60)
    logger.info("매핑 분석 결과")
    logger.info("=" * 60)
    logger.info("Artsy: %d/%d 갤러리 매칭 (%.0f%%), 작품 %d/%d (%.1f%%)",
                artsy["matched_galleries_count"], artsy["total_galleries"],
                100 * artsy["matched_galleries_count"] / artsy["total_galleries"],
                artsy["matched_works"], artsy["total_works"], artsy["matched_works_pct"])
    logger.info("통합 Tier 분포: %s", combined["tier_distribution"])


if __name__ == "__main__":
    main()
