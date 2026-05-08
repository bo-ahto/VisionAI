"""Tier CSV 의 column schema 정리 — 한글명 + 분류 (수집/계산/...) + 설명.

산출: data/dataset_tiers_20260508/SCHEMA.csv + 한글 마크다운 표.

분류 카테고리:
- collected: source 에서 수집된 raw 값 (Artsy / Saatchi profile / Constructor.io API)
- enrichment: 별도 fetch + 추출 (PR #51 Saatchi year_made detail page)
- computed: 코드 계산 (수집 값 의 derivation)
- categorical_normalized: 수집된 raw text 의 분류 mapping
- placeholder: 운영 코드 가 0.0 fill (audit 에서 식별 / 모델 input 의 noise feature)
- training_metadata: 운영 학습 의 가공 메타 (exclude_reason 등)
- target: 학습 target (price_krw / ln_price)
- identifier: 식별자 (id / slug / url)
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "dataset_tiers_20260508"
OUT_CSV = OUT_DIR / "SCHEMA.csv"
OUT_MD = OUT_DIR / "SCHEMA.md"

# (column_en, korean_name, category, description)
SCHEMA = [
    # ─── 식별자 ────────────────────────────────────────────────────
    ("artwork_id", "작품ID", "identifier (수집)", "Source 의 작품 식별자 (Artsy artwork_id / Saatchi artwork_id)"),
    ("artist_slug", "작가식별자", "identifier (수집)", "Source 의 작가 식별자 (Artsy slug / Saatchi artist_id)"),
    ("artist_name", "작가명", "수집", "Source 의 작가 표시명"),
    ("title", "작품제목", "수집", "Source 의 작품 제목"),
    ("image_url", "이미지URL", "수집", "Source 의 이미지 URL"),
    ("artwork_url", "작품URL", "수집", "Source 의 작품 페이지 URL"),
    # ─── 가격 ──────────────────────────────────────────────────────
    ("price_krw", "가격(KRW)", "수집+환산", "Source 가격 → KRW 환산 (USD/EUR/GBP 의 경우 환율 적용 / KRW 면 그대로)"),
    ("price_raw", "원본가격표기", "수집", "Source 의 원본 가격 문자열 (예: 'US$3,900')"),
    ("price_currency", "가격통화", "수집", "Source 의 가격 통화 (USD/KRW/GBP/EUR/HKD)"),
    ("is_krw", "원화여부", "계산 (1=KRW / 0=그외)", "price_currency == 'KRW' 의 binary flag"),
    ("ln_price", "로그가격", "계산 = log(price_krw)", "학습 target / 자연로그 변환"),
    # ─── 크기 ──────────────────────────────────────────────────────
    ("dimensions_cm", "크기표기(원본)", "수집", "Source 의 dimensions 원본 문자열 (예: '90.9 × 60.6 cm')"),
    ("area_cm2", "면적(cm²)", "계산 = width × height", "dimensions_cm 의 width × height"),
    ("aspect_ratio", "가로세로비", "계산 = width / height", "dimensions 의 long-axis / short-axis"),
    ("ln_area", "로그면적", "계산 = log(area_cm2)", "면적 의 자연로그 변환 (operational fill 시 0)"),
    ("ho", "호수", "계산 = area→호수 mapping", "한국 미술 의 표준 호수 mapping (area_cm2 영역 의 closest match)"),
    ("ho_power", "호수^0.74", "계산 = ho^0.74", "호수 의 power 변환 (가격 sub-linear 영역)"),
    ("ln_ho", "로그호수", "계산 = log(ho+1)", "호수 의 자연로그 변환"),
    ("is_small", "소형여부", "계산 (1=ho≤3)", "호수 ≤ 3 의 binary flag"),
    ("has_depth", "깊이여부", "계산 (1=depth_cm 있음)", "depth_cm 가 입력 된 binary flag"),
    ("ho_x_support", "호수×지지체계수", "계산 = ho × support_factor", "호수 × support_factor 의 interaction"),
    # ─── 매체/지지체 ──────────────────────────────────────────────
    ("medium", "매체(원본)", "수집", "Source 의 medium 원본 문자열 (예: 'Oil and soft pastel on linen')"),
    ("medium_category", "매체분류", "categorical 정규화", "medium 의 표준 분류 (oil/acrylic/ink/...)"),
    ("medium_l1", "매체대분류", "categorical 정규화", "1차 분류 (회화/조각/사진/...)"),
    ("medium_leaf", "매체소분류", "categorical 정규화", "leaf 분류 (유채/아크릴/...)"),
    ("mediums_json", "매체배열(JSON)", "categorical 정규화", "복수 medium 의 JSON 배열"),
    ("support_type", "지지체분류", "categorical 정규화", "지지체 표준 분류 (canvas/paper/linen/...)"),
    ("support_l1", "지지체대분류", "categorical 정규화", "1차 분류 (섬유/종이/금속/...)"),
    ("support_leaf", "지지체소분류", "categorical 정규화", "leaf 분류 (캔버스/한지/...)"),
    ("supports_json", "지지체배열(JSON)", "categorical 정규화", "복수 support 의 JSON 배열"),
    ("support_factor", "지지체계수", "계산 = support_type→가격계수", "지지체 별 가격 계수 (canvas=1.0 등)"),
    ("has_multimedia", "복합매체여부", "계산 (1=multi-medium)", "mediums_json 의 길이 > 1 의 binary flag"),
    ("has_special_finish", "특수마감여부", "계산", "특수 finish (gold leaf 등) 의 binary flag"),
    # ─── 제작연도 / 작가 시기 ─────────────────────────────────────
    ("year_made", "제작연도", "수집(Artsy) / enrichment(Saatchi PR #51)", "Artsy = source 직접 / Saatchi = detail page enrichment (97.90% fill)"),
    ("has_year_made", "제작연도여부", "계산 (1=year_made notna)", "year_made 가 채워진 binary flag (PR #51 enrichment 후)"),
    ("work_age", "작품연한", "계산 = 2026 - year_made", "제작 후 경과 연도 (operational WORK_AGE_REF_YEAR=2026)"),
    ("vintage_premium", "vintage 프리미엄", "계산 (work_age × stage 조건)", "career_stage_int ≥ 3 의 작가 의 work_age (그 외 0)"),
    ("freshness_discount", "freshness 디스카운트", "계산 (work_age × stage 조건)", "career_stage_int < 3 의 작가 의 work_age (그 외 0)"),
    # ─── 작가 프로필 ──────────────────────────────────────────────
    ("artist_birth_year", "작가생년", "수집(Artsy) / regex 추출(Saatchi bio)", "Artsy = source 직접 / Saatchi = bio 의 regex 추출 (9.26% / PR #52 pilot 미적용)"),
    ("has_birth_year", "생년여부", "계산 (1=birth_year notna)", "artist_birth_year 채워진 binary flag"),
    ("career_age", "활동연수", "계산 = year_made - first_exhibition_year", "첫 전시 연도 부터 경과 (Artsy only)"),
    ("career_stage", "경력단계점수", "계산 (multi-factor v2 score)", "0-8 연속 점수 (Saatchi 도 일부 적용)"),
    ("ln_followers", "로그팔로워", "계산 = log(followers+1)", "Source 의 artist_followers 의 자연로그 변환"),
    ("artist_total_works", "작가총작품수", "수집", "Source 의 작가 별 총 작품 수"),
    ("for_sale_ratio", "판매중비율", "계산 = for_sale / total_works", "판매 가능 작품 비율 (0-1)"),
    ("request_ratio", "가격문의비율", "계산", "'Price on request' 작품 비율 (Artsy 만)"),
    ("solo_count", "개인전수", "수집(텍스트)→정규화", "exhibitions/bio 의 개인전 횟수 추정"),
    ("group_count", "단체전수", "수집(텍스트)→정규화", "exhibitions/bio 의 단체전 횟수 추정"),
    ("fair_count", "아트페어수", "수집(텍스트)→정규화", "exhibitions/bio 의 아트페어 횟수 추정"),
    ("artist_is_p1", "P1작가여부", "categorical 정규화", "운영 의 P1 작가 분류 (대부분 False)"),
    ("attribution_class", "유일성분류", "categorical 정규화", "Unique / Limited edition / Open edition / Unknown edition"),
    ("is_unique", "유일작품여부", "계산 (1=Unique)", "attribution_class == 'Unique' 의 binary flag"),
    ("is_edition", "에디션여부", "계산 (1=Limited edition)", "Limited edition binary flag"),
    # ─── 갤러리 ───────────────────────────────────────────────────
    ("gallery_name", "갤러리명", "수집", "Source 의 갤러리 이름"),
    ("gallery_type", "갤러리유형", "수집", "Gallery / Online Gallery"),
    ("gallery_tier", "갤러리티어", "계산 (gallery_alias_map 매핑)", "운영 의 갤러리 티어 (1-5 / 한국 갤러리 영역)"),
    ("gallery_city_count", "갤러리도시수", "계산 = count(gallery_cities)", "갤러리 의 도시 수"),
    ("has_seoul", "서울갤러리여부", "계산 (1=Seoul 포함)", "gallery_cities 에 'Seoul' 포함 binary flag"),
    ("has_international", "해외갤러리여부", "계산 (1=city_count≥2)", "gallery_city_count ≥ 2 의 binary flag"),
    # ─── 기타 메타 ────────────────────────────────────────────────
    ("source", "데이터소스", "수집/구분", "artsy / saatchi 의 출처 식별자"),
    ("is_excluded_for_training", "학습제외여부", "training_metadata", "운영 학습 시 제외 여부 (1=제외 / 985 rows)"),
    ("exclude_reason", "제외사유", "training_metadata", "support_excluded / keyword_3d:* 등"),
    ("value_grade_note", "가치등급노트", "training_metadata (sparse)", "운영 의 manual annotation (99.09% empty)"),
    # ─── Placeholder (운영 fill) ───────────────────────────────────
    ("ho_price_level", "호수가격레벨(미사용)", "placeholder (100% zero)", "운영 load_data() 가 0.0 fill / source 미존재 / 모델 noise feature"),
    ("medium_price_level", "매체가격레벨(미사용)", "placeholder (100% zero)", "운영 load_data() 가 0.0 fill / source 미존재"),
    ("profile_completeness", "프로필완성도(미사용)", "placeholder (100% zero)", "운영 load_data() 가 0.0 fill / source 미존재"),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # CSV
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["column_en", "한글명", "분류", "설명"])
        for col, ko, cat, desc in SCHEMA:
            w.writerow([col, ko, cat, desc])

    # Markdown
    lines = [
        "# Dataset Tier CSV — 컬럼 schema (한글명 + 계산/수집 분류)\n\n",
        "Tier CSV (T0-T6 / extra_*) 의 모든 컬럼 의 의미.\n\n",
        "## 분류 카테고리\n\n",
        "| 분류 | 의미 |\n",
        "|---|---|\n",
        "| **수집** | Source (Artsy / Saatchi profile / Constructor.io API) 에서 직접 수집 한 raw 값 |\n",
        "| **계산** | 코드 가 수집 값 으로 산출 한 derivation (예: area_cm2 = width × height) |\n",
        "| **enrichment** | 별도 fetch + 추출 (PR #51 Saatchi year_made detail page) |\n",
        "| **categorical 정규화** | 수집 raw text 의 표준 분류 mapping (예: medium → 'oil') |\n",
        "| **placeholder** | 운영 코드 가 0.0 fill / source 미존재 / 모델 noise feature (audit 식별) |\n",
        "| **training_metadata** | 운영 학습 의 가공 메타 (exclude_reason 등) |\n",
        "| **target** | 학습 target (price_krw → ln_price) |\n",
        "| **identifier** | 식별자 (id / slug / url) |\n\n",
        "## 컬럼 사전\n\n",
        "| column | 한글명 | 분류 | 설명 |\n",
        "|---|---|---|---|\n",
    ]
    for col, ko, cat, desc in SCHEMA:
        lines.append(f"| `{col}` | {ko} | {cat} | {desc} |\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote {OUT_CSV} ({len(SCHEMA)} columns)")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
