"""column_dictionary.csv 에 '근거' + '적용정합성_노트' 2 column 추가.

각 column 의 학술 출처 / 본 dataset 실증 / hardcoded value 의 source +
source-conditional 영역 의 정합성 / mismatch 영역 명시.

Decision binding: ❌ X (CSV 정리 만 / 동료 공유 용 / 운영 코드 변경 X)
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DICT_PATH = REPO / "data" / "dataset_tiers_cleansed_20260508" / "column_dictionary.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# (영문명, 근거, 적용정합성_노트)
ENRICHMENT = {
    # ─── 가격 영역 ──────────────────────────────────────────────
    "price_krw": (
        "환율 = scripts/crawl_artsy_full.py:30 의 hardcoded FX_RATES (2026-04-13 기준 근사치)",
        "USD=1380 / GBP=1780 / EUR=1530 / HKD=178 / KRW=1.0 / 실시간 환율 X / 시간 변동 미반영 / 운영 학습/추론 의 일관성 보장 영역 만",
    ),
    "ln_price": (
        "log 변환 = hedonic regression 의 표준 (price 의 분포 의 right-skew 보정)",
        "본 dataset 의 ln(price_krw) 분포 = 정합 (학습 target / log-normal 가정)",
    ),

    # ─── 크기 영역 ──────────────────────────────────────────────
    "area_cm2": (
        "기본 면적 = width × height (학술 적 표준)",
        "정합 (width / height 의 source 정확도 의무 / dimension_parser 의 영역)",
    ),
    "ho": (
        "표준 F 테이블 = src/visionai/price_engine/preprocessing/dimension_parser.py:33-42 의 한국 캔버스 호수 F형 규격 (22 entries / 0~200호) / 본 cycle (HO_TABLE 통합) 의 표준 단일 소스",
        "본 cycle PASS 시 = 표준 F 보간 의 정수 round (np.rint) / canvas type F/P/M/S 의 typecasting X / 정수 ho contract 유지",
    ),
    "ho_power": (
        "Shin (2010) 'Price Determinants and Genre Effects in the Korean Art Market' (Journal of Cultural Economics / DOI 10.1007/s10824-010-9126-y) 의 P=α×Ho^β / β<1 / 한국 시장 의 sub-linear 영역. 운영 0.74 = 본 dataset 의 KRW 작품 의 실증 추정 β=0.749 (docs/model_technical_report.md:82) ≈ Shin 0.74 와 정합",
        "⚠️ 부분 mismatch: KRW (artsy_gallery / 3.06%) 만 정합 / artsy_online USD 영역 (β 추정=0.840 / 6,421 rows / 22.63%) = -0.10 underestimate / saatchi_online (USD / 21,087 rows / 74.31%) = β 추정 X (한국 시장 X). 운영 단일 hardcoded 0.74 = source-conditional 영역 미적용 / 96.94% 영역 의 정합 X (record only / 모델 영향 = GBDT input 만 / 운영 채택 결정 영역 X)",
    ),
    "ln_ho": (
        "log 변환 = 호수 의 다단계 비선형 영역 의 추가 표현력 (ho_power 외 의 별도 비선형 영역)",
        "정합 (학습 모델 의 input feature / 호수 0 의 영역 의 보호 의 +1 영역)",
    ),
    "ln_area": (
        "log 변환 = 면적 의 분포 의 right-skew 보정 (학술 적 표준)",
        "정합 / area_cm2 의 floor 영역 (clip(lower=1)) 의 0 보호",
    ),
    "is_small": (
        "한국 미술 시장 의 '소품' 영역 (3호 이하 / 약 727 cm² 이하 / 약 27cm × 22cm 작품)",
        "정합 (binary indicator / 소품 영역 의 별도 가격 정책 영역 의 표현력)",
    ),
    "aspect_ratio": (
        "표준 미술 작품 의 비례 영역 (1.0=정사각 / 1.25 미만=F형 / 1.25-1.45=P형 / 1.45+=M형)",
        "운영 적용 = aspect_to_canvas_type 의 4종 분류 산출 만 / 학습 model 의 영역 X (canvas_type = dead feature / 코덱스 권고 의 분리 영역)",
    ),
    "ho_x_support": (
        "interaction term = 호수 × 지지체계수 (multiplicative effect 의 표현력)",
        "정합 / 학습 모델 의 input feature / GBDT 의 비선형 영역 의 도움 영역",
    ),

    # ─── 매체 / 지지체 영역 ─────────────────────────────────────
    "medium_category": (
        "한국 미술 시장 의 medium classification (oil/acrylic/ink/watercolor/pigment/mixed/pastel/pencil) / classify_medium 의 substring rule-first 매칭",
        "정합 (운영 정의 의 표준 영역 / source raw text 의 keyword-based mapping / 4.03% 'other' fallback 영역)",
    ),
    "support_type": (
        "한국 미술 시장 의 support classification (canvas/linen/paper/panel/silk/metal) / classify_support 의 substring rule-first 매칭",
        "정합 (운영 정의 / 4.02% 'other' fallback 영역)",
    ),
    "support_factor": (
        "운영 hardcoded 가격 계수 = src/visionai/price_engine/api/primary_feature_builder.py:55-63 의 SUPPORT_FACTORS dict / 학습 dataset 의 평균 가격 비율 의 추정",
        "⚠️ 운영 hardcoded value (canvas=1.0 / linen=1.1 / paper=0.8 / panel=0.9 / silk=1.0 / metal=0.9 / other=0.85) / source 의 학술 출처 X / 본 dataset 의 평균 가격 비율 의 단순 추정 / 시간 / 시기 영역 의 update 미적용",
    ),
    "has_multimedia": (
        "binary indicator = 작품 의 복수 매체 사용 영역",
        "정합 (mediums 배열 의 길이 의 binary)",
    ),

    # ─── 제작연도 / 작가 시기 ───────────────────────────────────
    "year_made": (
        "Source 직접 (Artsy) / detail page enrichment (Saatchi PR #51 / 97.90% fill)",
        "Saatchi enrichment 의 frozen artifact (commit dce0dfa / 2026-05-01 / 8일 stale 영역)",
    ),
    "has_year_made": (
        "binary flag = year_made notna 영역",
        "정합 (학습 fillna(0) 후 의 model-input parity)",
    ),
    "work_age": (
        "작품 연한 = 2026 - year_made / WORK_AGE_REF_YEAR=2026 의 dataset build 영역 의 고정",
        "정합 (year_made notna 영역 만 / NaN 영역 의 fillna(0) 영역 의 운영 학습 영역)",
    ),

    # ─── 작가 프로필 ─────────────────────────────────────────────
    "artist_birth_year": (
        "Source 직접 (Artsy birthday/birthYear) / Saatchi bio free-text 의 5-pattern regex (PR #52 pilot 의 추가 패턴 미적용 / Precision FAIL)",
        "9.26% (Saatchi) / 80.78% (Artsy) fill rate / Saatchi 의 90.74% 결손 영역 = 모델 의 has_birth_year=0 의 영역",
    ),
    "has_birth_year": (
        "binary flag = artist_birth_year notna 영역",
        "정합 (학습 fillna(0) 후 의 model-input parity)",
    ),
    "career_age": (
        "Artsy artist_shows API 의 첫 전시 연도 부터 의 차이 (year_made - first_show_year)",
        "Artsy only / Saatchi 영역 = 100% null (Saatchi profile 의 shows 영역 X)",
    ),
    "career_stage": (
        "v2 multi-factor score = primary_feature_builder.py:67-101 의 (age + activity + market_presence) cap 8 / Codex review (2026-04-27) 의 v2 spec",
        "운영 적용 (학습/추론) / career_age 영역 의 train-serve drift 의 제거 영역 (v2 의 의도) / 본 dataset 의 평균 ≈ 2-3 영역",
    ),
    "for_sale_ratio": (
        "판매 가능 작품 / 총 작품 의 비율 (0-1 영역) / Artsy 의 artist_for_sale + total_works",
        "정합 / Saatchi 영역 의 추정 영역 (artist 별 total_artworks 의 사용)",
    ),
    "solo_count": (
        "전시 횟수 = Artsy artist_shows API 의 type='Solo' filter / Saatchi extract_exhibition_counts 의 bio + exhibitions 의 line-heuristic count",
        "source-conditional 영역 / Artsy 의 직접 count vs Saatchi 의 추정 영역 의 정합성 의문",
    ),
    "group_count": (
        "전시 횟수 = Artsy artist_shows API 의 type='Group' filter / Saatchi extract_exhibition_counts",
        "source-conditional 영역 / 정합성 의문",
    ),
    "fair_count": (
        "전시 횟수 = Artsy artist_shows API 의 type='Fair' filter / Saatchi extract_exhibition_counts 의 'fair'/'페어' line 매칭",
        "source-conditional 영역 / 정합성 의문",
    ),
    "ln_followers": (
        "log 변환 = followers 의 right-skew 보정",
        "정합 / fillna(0) 의 운영 영역 (followers 의 0 영역 의 다수 의 영향)",
    ),
    "is_unique": (
        "binary flag = attribution_class == 'Unique' (단일 작품 영역)",
        "정합 / 99.87% 의 dataset 이 'Unique' (variation 영역 매우 sparse)",
    ),
    "is_edition": (
        "binary flag = attribution_class == 'Limited edition'",
        "정합 / 0.12% (34 작품) 영역",
    ),

    # ─── 갤러리 영역 ─────────────────────────────────────────────
    "gallery_tier": (
        "운영 estimate_gallery_tier (prepare_primary_market_dataset.py:117) 의 hardcoded score 영역 의 합산 → 1-5 등급. score = (city≥4:+3, ≥2:+2) + (avg_price≥50M:+3, ≥10M:+2, ≥3M:+1) + (work≥50:+2, ≥20:+1)",
        "⚠️ 운영 hardcoded threshold (city/avg_price/work_count 의 영역) / 학술 출처 X / 본 dataset 의 평균 의 임의 영역 / Saatchi 의 영역 의 추정 의 단일 값 의 영향",
    ),
    "gallery_city_count": (
        "갤러리 의 도시 수 = gallery_cities 의 콤마 분리 count (빈 토큰 제외)",
        "정합 / Saatchi 영역 의 영역 의 영향 (online 만 / city 1 의 단일 영역)",
    ),
    "has_international": (
        "binary flag (source-conditional) = Artsy: gallery_city_count >= 2 / Saatchi: 항상 1 (online gallery 의 source policy)",
        "⚠️ source-conditional 정의 의 binding / Artsy 의 city_count>=2 의 의미 vs Saatchi 의 항상 1 의 의미 의 의미 영역 X / 운영 의 정의 의 mismatch 영역 (코덱스 권고 의 정의 명시 영역)",
    ),
    "is_krw": (
        "binary flag = price_currency == 'KRW' (한국 갤러리 의 원화 표기 영역)",
        "정합 / 3.06% 영역 (artsy_gallery cell)",
    ),
}


def main() -> None:
    # 현재 dict 읽기
    rows = list(csv.reader(DICT_PATH.open(encoding="utf-8-sig")))
    header = rows[0]
    body = rows[1:]
    logger.info("Existing dictionary: %d rows / %d cols", len(body), len(header))

    # 새 header 의 column 추가
    new_header = header + ["근거", "적용정합성_노트"]

    new_body = []
    for row in body:
        col_name = row[0]
        if col_name in ENRICHMENT:
            evidence, note = ENRICHMENT[col_name]
        else:
            evidence = "(보강 영역 X / source 직접 또는 식별자)"
            note = "(보강 영역 X)"
        new_body.append(row + [evidence, note])

    # write
    with open(DICT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(new_header)
        w.writerows(new_body)

    logger.info(
        "Updated dictionary: %d rows / %d cols (보강 적용: %d)",
        len(new_body), len(new_header),
        sum(1 for r in body if r[0] in ENRICHMENT),
    )

    # Summary
    print("\n=== 보강 영역 ===")
    for name, (evidence, note) in ENRICHMENT.items():
        print(f"  {name:<22}: {evidence[:80]}")
        print(f"    {' ':<22}  주의: {note[:80]}")


if __name__ == "__main__":
    main()
