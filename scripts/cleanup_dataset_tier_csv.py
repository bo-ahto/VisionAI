"""Tier CSV cleanup — 검수 결과 + 코덱스 의견 반영.

산출:
1. data/dataset_tiers_cleansed_20260508/T*_cleansed.csv (51 columns)
2. data/dataset_tiers_cleansed_20260508/column_dictionary.csv (영문/한글/분류/정의/처리결정)
3. data/dataset_tiers_cleansed_20260508/display_companion_T0.csv (mediums_json/supports_json 별도)
4. data/dataset_tiers_cleansed_20260508/human_readable_T0.csv (한글 column 명 사람용 파생본)

제거 (13): placeholder 3 + sparse 3 + 미작동 2 + empty 2 + REQUIRES_SOURCE_AUDIT 3
분리 (2): mediums_json / supports_json
보존+정의명시 (1): has_international (source-conditional)
보존 (50): 검증 완료 + raw + categorical normalized

Decision binding: ❌ X (정리 자료 만 / 운영 코드 / parquet 변경 X)
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from saatchi_year_made_merger import (  # type: ignore  # noqa: E402
    WORK_AGE_REF_YEAR,
    add_has_year_made_flag,
    load_enrichment_year_map,
    merge_year_made,
    recompute_work_age,
)
from train_primary_market_v3_filtered import load_data  # type: ignore  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = REPO / "data" / "dataset_tiers_cleansed_20260508"
ENRICHMENT_JSONL = REPO / "data" / "saatchi_year_enrichment_artifact_20260501" / "raw.jsonl"
CURRENT_YEAR = 2026

# ─── 처리 결정 (코덱스 의견 반영) ─────────────────────────────────
# (column, 한글명, 분류, 정의, 처리결정, 사유)
COLUMN_DECISIONS = [
    # ─── 보존 columns (51) ──────────────────────────────────────────
    # tuple: (영문, 한글, 분류, 정의, 처리결정, 사유, 생성방식, 계산공식)

    # 식별자 (6)
    ("artwork_id", "작품ID", "identifier", "Source 의 작품 식별자",
     "보존", "식별자",
     "Source API 직접 수집 (Artsy: artwork id / Saatchi: artwork_id)",
     "변환 X (raw 그대로)"),
    ("artist_slug", "작가식별자", "identifier", "Source 의 작가 식별자",
     "보존", "식별자",
     "Source API 직접 수집 (Artsy: slug / Saatchi: artist_id)",
     "변환 X"),
    ("artist_name", "작가명", "수집", "Source 의 작가 표시명",
     "보존", "수집 raw",
     "Source API 직접 수집",
     "변환 X"),
    ("title", "작품제목", "수집", "Source 의 작품 제목",
     "보존", "수집 raw",
     "Source API 직접 수집",
     "변환 X"),
    ("image_url", "이미지URL", "수집", "Source 의 이미지 URL",
     "보존", "수집 raw",
     "Source API 직접 수집",
     "변환 X"),
    ("artwork_url", "작품URL", "수집", "Source 의 작품 페이지 URL",
     "보존", "수집 raw",
     "Source API 직접 수집",
     "변환 X"),

    # 가격 (5)
    ("price_krw", "가격(KRW)", "수집+환산", "Source 가격 → KRW 환산",
     "보존", "수집+환산 (target precursor)",
     "Source 가격 (price_raw) 의 통화 변환",
     "USD/EUR/GBP/HKD → KRW 환율 적용 / KRW 면 직접"),
    ("price_raw", "원본가격표기", "수집", "Source 의 원본 가격 문자열",
     "보존", "수집 raw / display",
     "Source API 직접 수집",
     "변환 X (예: 'US$3,900')"),
    ("price_currency", "가격통화", "수집", "Source 의 가격 통화",
     "보존", "수집 raw",
     "Source 의 currency 코드",
     "변환 X (USD/KRW/GBP/EUR/HKD)"),
    ("is_krw", "원화여부", "계산", "1 if price_currency=='KRW' else 0",
     "보존", "계산 EXACT 검증",
     "price_currency 의 binary flag",
     "is_krw = (price_currency == 'KRW') ? 1 : 0"),
    ("ln_price", "로그가격", "계산", "log(price_krw)",
     "보존", "계산 EXACT 검증 / 학습 target",
     "price_krw 의 자연로그",
     "ln_price = ln(price_krw)"),

    # 크기 (9)
    ("dimensions_cm", "크기표기(원본)", "수집", "Source 의 dimensions 원본",
     "보존", "수집 raw",
     "Source API 직접 수집",
     "변환 X (예: '90.9 × 60.6 cm')"),
    ("area_cm2", "면적(cm²)", "계산", "width × height",
     "보존", "계산 (raw width/height 의 derivation)",
     "dimensions_cm 의 width/height 추출 후 곱",
     "area_cm2 = width_cm × height_cm"),
    ("aspect_ratio", "가로세로비", "계산", "long-axis / short-axis",
     "보존", "계산",
     "width / height 비율 (long / short)",
     "aspect_ratio = max(w, h) / max(min(w, h), 0.1)"),
    ("ln_area", "로그면적", "계산", "log(area_cm2.clip(lower=1))",
     "보존", "계산 EXACT 검증",
     "area_cm2 의 자연로그 (1 미만 floor)",
     "ln_area = ln(max(area_cm2, 1))"),
    ("ho", "호수", "계산", "area→호수 mapping",
     "보존", "계산 (한국 미술 표준 mapping)",
     "area_cm2 와 가장 가까운 HO_TABLE_F 의 ref_area 의 호수",
     "ho = argmin_h |area_cm2 - HO_TABLE_F[h]| (F형 기준 / 0~200호 23단계)"),
    ("ho_power", "호수^0.74", "계산", "ho^0.74 if ho>0 else 0",
     "보존", "계산 EXACT 검증",
     "ho 의 power 변환 (가격 sub-linear 영역)",
     "ho_power = ho ** 0.74 (ho > 0) else 0"),
    ("ln_ho", "로그호수", "계산", "log(ho+1)",
     "보존", "계산 EXACT 검증",
     "ho 의 자연로그 (+1 shift)",
     "ln_ho = ln(ho + 1)"),
    ("is_small", "소형여부", "계산", "1 if ho<=3 else 0",
     "보존", "계산 EXACT 검증",
     "ho 의 binary flag (3호 이하 = 소형)",
     "is_small = (ho <= 3) ? 1 : 0"),
    ("ho_x_support", "호수×지지체계수", "계산", "ho * support_factor",
     "보존", "계산 EXACT 검증",
     "ho × support_factor 의 interaction term",
     "ho_x_support = ho × support_factor"),

    # 매체/지지체 (9)
    ("medium", "매체(원본)", "수집", "Source 의 medium 원본",
     "보존", "수집 raw",
     "Source API 직접 수집",
     "변환 X (예: 'Oil and soft pastel on linen')"),
    ("medium_category", "매체분류", "categorical 정규화", "표준 분류 (oil/acrylic/...)",
     "보존", "categorical 분포 OK",
     "medium 텍스트 의 substring rule-first 매칭 (운영 classify_medium / prepare_primary_market_dataset.py:84)",
     "for label, kws in MEDIUM_RULES: if any(kw in medium.lower() for kw in kws): return label / fallback 'other'"),
    ("medium_l1", "매체대분류", "categorical 정규화", "1차 분류",
     "보존", "categorical",
     "visionai parser 의 한국어 1차 분류",
     "회화/드로잉/조각/사진/판화 등 (parser rule based)"),
    ("medium_leaf", "매체소분류", "categorical 정규화", "leaf 분류",
     "보존", "categorical",
     "visionai parser 의 한국어 leaf 분류",
     "유채/아크릴/수채 등 (parser rule based)"),
    ("support_type", "지지체분류", "categorical 정규화", "표준 분류 (canvas/paper/...)",
     "보존", "categorical 분포 OK",
     "medium 텍스트 의 substring rule-first 매칭 (운영 classify_support / prepare_primary_market_dataset.py:84)",
     "for label, kws in SUPPORT_RULES: if any(kw in medium.lower() for kw in kws): return label / fallback 'other'"),
    ("support_l1", "지지체대분류", "categorical 정규화", "1차 분류",
     "보존", "categorical",
     "visionai parser 의 한국어 1차 분류",
     "섬유/종이/금속/목재 등 (parser rule based)"),
    ("support_leaf", "지지체소분류", "categorical 정규화", "leaf 분류",
     "보존", "categorical",
     "visionai parser 의 한국어 leaf 분류",
     "캔버스/한지 등 (parser rule based)"),
    ("support_factor", "지지체계수", "계산", "support_type → 가격 계수",
     "보존", "계산",
     "support_type 의 가격 계수 mapping (SUPPORT_FACTORS dict)",
     "canvas=1.0 / linen=1.1 / paper=0.8 / panel=0.9 / silk=1.0 / metal=0.9 / other=0.85"),
    ("has_multimedia", "복합매체여부", "계산", "1 if mediums_json 길이>1",
     "보존", "계산",
     "mediums_json 배열 의 length binary flag",
     "has_multimedia = (len(mediums_json) > 1) ? 1 : 0"),

    # 제작연도 / 작가 시기 (3)
    ("year_made", "제작연도", "수집/enrichment", "Artsy=수집 / Saatchi=PR #51 enrichment",
     "보존", "수집 + enrichment (PR #51)",
     "Artsy: source API 직접 / Saatchi: detail page HTML primary regex + JSON fallback (PR #51 / 97.90% fill)",
     "Saatchi: scripts/saatchi_detail_enricher.py:46 (primary HTML pattern + camelCase JSON + snake_case JSON 의 sequential fallback)"),
    ("has_year_made", "제작연도여부", "계산", "1 if year_made notna",
     "보존", "계산 EXACT 검증",
     "year_made 의 binary flag",
     "has_year_made = year_made.notna() ? 1 : 0"),
    ("work_age", "작품연한", "계산", "2026 - year_made",
     "보존", "계산 EXACT 검증",
     "WORK_AGE_REF_YEAR(=2026) - year_made (notna 영역 만)",
     "work_age = 2026 - year_made"),

    # 작가 프로필 (12)
    ("artist_birth_year", "작가생년", "수집/regex추출", "Artsy=수집 / Saatchi=bio regex",
     "보존", "수집 + regex (PR #52 pilot 미적용)",
     "Artsy: source API 의 birthday/birthYear / Saatchi: bio free-text 의 5 regex pattern sequential 매칭 + 1920-2005 validity range",
     "Saatchi: scripts/prepare_saatchi_dataset.py:101-118 (5 pattern 순차 적용 / 첫 매칭 의 year / 9.26% fill)"),
    ("has_birth_year", "생년여부", "계산", "1 if artist_birth_year notna",
     "보존", "계산 EXACT 검증",
     "artist_birth_year 의 binary flag",
     "has_birth_year = artist_birth_year.notna() ? 1 : 0"),
    ("career_age", "활동연수", "계산", "year_made - first_exhibition_year",
     "보존", "계산 (Artsy only)",
     "Artsy artist_shows 의 첫 전시 연도 부터 year_made 까지 의 차이",
     "career_age = year_made - min(artist_shows.year_started)"),
    ("career_stage", "경력단계점수", "계산", "multi-factor v2 score (0-8)",
     "보존", "계산",
     "career_stage_v2_score (primary_feature_builder.py:66) 의 3 component 합계",
     "score = clip((age-30)/12, 0, 3) + min(log1p(solo+0.7×fair+0.3×group), 3) + min(ln_followers/6, 2) / age=2026-birth_year"),
    ("artist_total_works", "작가총작품수", "수집", "Source 의 작가 총 작품 수",
     "보존", "수집",
     "Source API 직접 수집 (Artsy: total_works / Saatchi: total_artworks)",
     "변환 X"),
    ("for_sale_ratio", "판매중비율", "계산", "for_sale / total_works",
     "보존", "계산",
     "판매 가능 작품 / 총 작품 (0 보호)",
     "for_sale_ratio = artist_for_sale / max(artist_total_works, 1)"),
    ("solo_count", "개인전수", "수집/source-conditional", "Artsy=shows_data 직접 / Saatchi=텍스트 추정",
     "보존", "수집 / source-conditional 정규화",
     "Artsy: artist_shows API 의 solo show count 직접 / Saatchi: bio + exhibitions 텍스트 의 line-heuristic count",
     "Artsy: shows_data[slug]['shows'] 의 type='Solo' filter / Saatchi: extract_exhibition_counts (prepare_saatchi_dataset.py:117) 의 line 매칭"),
    ("group_count", "단체전수", "수집/source-conditional", "Artsy=shows_data 직접 / Saatchi=텍스트 추정",
     "보존", "수집 / source-conditional 정규화",
     "Artsy: artist_shows API 의 group show count 직접 / Saatchi: bio + exhibitions 텍스트 의 line-heuristic count",
     "Artsy: shows_data[slug]['shows'] 의 type='Group' filter / Saatchi: extract_exhibition_counts 의 line 매칭"),
    ("fair_count", "아트페어수", "수집/source-conditional", "Artsy=shows_data 직접 / Saatchi=텍스트 추정",
     "보존", "수집 / source-conditional 정규화",
     "Artsy: artist_shows API 의 fair count 직접 / Saatchi: bio + exhibitions 텍스트 의 line-heuristic count",
     "Artsy: shows_data[slug]['shows'] 의 type='Fair' filter / Saatchi: extract_exhibition_counts 의 'fair'/'페어' line 매칭"),
    ("attribution_class", "유일성분류", "categorical 정규화", "Unique / Limited edition / ...",
     "보존", "categorical 분포 OK",
     "Source 의 attribution → 4-class 정규화 (Unique / Limited edition / Open edition / Unknown edition)",
     "rule-based mapping (Source 의 edition 영역 의 직접 분류)"),
    ("is_unique", "유일작품여부", "계산", "1 if 'Unique' else 0",
     "보존", "계산 EXACT 검증",
     "attribution_class 의 binary flag",
     "is_unique = (attribution_class == 'Unique') ? 1 : 0"),
    ("is_edition", "에디션여부", "계산", "1 if 'Limited edition' else 0",
     "보존", "계산 EXACT 검증",
     "attribution_class 의 binary flag",
     "is_edition = (attribution_class == 'Limited edition') ? 1 : 0"),

    # 갤러리 (5)
    ("gallery_name", "갤러리명", "수집", "Source 의 갤러리 이름",
     "보존", "수집",
     "Source API 직접 수집",
     "변환 X"),
    ("gallery_type", "갤러리유형", "수집", "Gallery / Online Gallery",
     "보존", "수집 (분포 OK)",
     "Source API 직접 수집 (Artsy: 'Gallery' / Saatchi: 'Online Gallery')",
     "변환 X"),
    ("gallery_tier", "갤러리티어", "계산", "estimate_gallery_tier 의 score 기반 1-5",
     "보존", "계산",
     "갤러리 statistics + city_count + avg_price + work_count 의 합산 score → 1-5 등급",
     "score = (city≥4:+3, ≥2:+2) + (avg_price≥50M:+3, ≥10M:+2, ≥3M:+1) + (work≥50:+2, ≥20:+1) → tier (≥7=1 / ≥5=2 / ≥3=3 / ≥1=4 / <1=5)"),
    ("gallery_city_count", "갤러리도시수", "계산", "count(gallery_cities) — 빈 토큰 제외",
     "보존", "계산",
     "gallery_cities 문자열 의 콤마 분리 count (운영 정의 = 빈 토큰 제외)",
     "gallery_city_count = len([c for c in gallery_cities.split(',') if c.strip()]) (prepare_primary_market_dataset.py:352)"),
    ("has_international", "해외갤러리여부", "계산 (source-conditional)",
     "Artsy: gallery_city_count >= 2 / Saatchi: 항상 1 (source policy)",
     "보존+정의명시", "정의 source-conditional 명시 의무 (코덱스)",
     "Source 별 다른 정의 의 source-conditional flag",
     "Artsy: has_international = (gallery_city_count >= 2) ? 1 : 0 / Saatchi: 항상 1 (online gallery 의 source policy)"),

    # 메타 (2)
    ("source", "데이터소스", "수집/구분", "artsy / saatchi",
     "보존", "구분자",
     "운영 load_data() 의 source 식별자",
     "Artsy parquet rows: source='artsy' / Saatchi parquet rows: source='saatchi'"),
    ("is_excluded_for_training", "학습제외여부", "training_metadata", "운영 학습 제외 flag",
     "보존", "training metadata",
     "운영 의 prepare_*_dataset.py 에서 결정 (support_excluded / keyword_3d:* 등)",
     "is_excluded_for_training = (exclude_reason != '') ? 1 : 0"),

    # ─── 분리 (display companion 별도 산출) (2) ───────────────────
    ("mediums_json", "매체배열(JSON)", "categorical 정규화", "복수 medium 의 JSON 배열",
     "분리", "코덱스: UI 표시 용 / cleansed CSV 본체 미포함",
     "parse_artsy_medium / parse_saatchi_medium 의 mediums 리스트 의 JSON 직렬화",
     "mediums_json = json.dumps(parsed.mediums) / 예: '[\"유채\", \"파스텔\"]' (primary_medium_parser.py:897)"),
    ("supports_json", "지지체배열(JSON)", "categorical 정규화", "복수 support 의 JSON 배열",
     "분리", "코덱스: UI 표시 용 / cleansed CSV 본체 미포함",
     "parse_artsy_medium / parse_saatchi_medium 의 supports 리스트 의 JSON 직렬화",
     "supports_json = json.dumps(parsed.supports) / 예: '[\"캔버스\"]' (primary_medium_parser.py:902)"),
]

KEEP_COLS = [c[0] for c in COLUMN_DECISIONS if c[4] == "보존" or c[4] == "보존+정의명시"]
SEPARATE_COLS = [c[0] for c in COLUMN_DECISIONS if c[4] == "분리"]
HAN_MAP = {c[0]: c[1] for c in COLUMN_DECISIONS}

# 제거 columns (dictionary 에서 row 자체 삭제 / 사유 만 record)
REMOVE_COLS_RECORD = [
    ("ho_price_level", "100% zero / placeholder (operational load_data 가 0.0 fill)"),
    ("medium_price_level", "100% zero / placeholder"),
    ("profile_completeness", "100% zero / placeholder"),
    ("request_ratio", "94.69% zero / sparse / Artsy only"),
    ("artist_is_p1", "99.68% False / sparse"),
    ("has_special_finish", "99.59% zero / sparse"),
    ("vintage_premium", "99.93% zero / 사실상 미작동 / career_stage_int 미포함"),
    ("freshness_discount", "career_stage_int 미포함 / 검수 불가"),
    ("value_grade_note", "99.09% empty"),
    ("exclude_reason", "T0 = filter 후 100% empty"),
    ("has_seoul", "raw gallery_cities 미포함 / 검수 불가 (audit backlog)"),
    ("ln_followers", "raw artist_followers 미포함 / 검수 불가 (audit backlog)"),
    ("has_depth", "raw depth_cm 미포함 / 검수 불가 (audit backlog)"),
]
REMOVE_COLS = [c[0] for c in REMOVE_COLS_RECORD]


def load_t0() -> pd.DataFrame:
    df = load_data()
    if not ENRICHMENT_JSONL.exists():
        import subprocess
        ENRICHMENT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.check_output(
            ["git", "show",
             "dce0dfa1fd5b3d7e6e43f651e921140e56b68a2b:"
             "model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl"],
            cwd=REPO,
        )
        ENRICHMENT_JSONL.write_bytes(blob)
    em = load_enrichment_year_map(ENRICHMENT_JSONL)
    df = merge_year_made(df, em, only_saatchi=True)
    df = add_has_year_made_flag(df)
    df = recompute_work_age(df, ref_year=WORK_AGE_REF_YEAR)
    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df_full = load_t0()
    df_t0 = df_full[df_full["is_excluded_for_training"] == 0].reset_index(drop=True)
    logger.info("T0 loaded: %d rows / %d columns", len(df_t0), len(df_t0.columns))

    # Validation: all KEEP/SEPARATE/REMOVE cols are in dataset
    all_decided = set(KEEP_COLS + SEPARATE_COLS + REMOVE_COLS)
    actual = set(df_t0.columns)
    missing_in_decisions = actual - all_decided
    extra_in_decisions = all_decided - actual
    logger.info("Columns in dataset but not decided: %s", missing_in_decisions)
    logger.info("Columns in decisions but not in dataset: %s", extra_in_decisions)
    assert not missing_in_decisions, f"Missing decisions: {missing_in_decisions}"
    assert not extra_in_decisions, f"Extra decisions: {extra_in_decisions}"
    assert len(KEEP_COLS) + len(SEPARATE_COLS) + len(REMOVE_COLS) == len(actual), (
        f"Total mismatch: {len(KEEP_COLS)} + {len(SEPARATE_COLS)} + {len(REMOVE_COLS)} != {len(actual)}"
    )

    # ─── Cleansed Tier CSVs ───────────────────────────────────────
    def cleansed(df: pd.DataFrame) -> pd.DataFrame:
        cols = [c for c in KEEP_COLS if c in df.columns]
        return df[cols].copy()

    tiers = {}
    df_t0_clean = cleansed(df_t0)
    tiers["T0_operational_28376_cleansed"] = df_t0_clean

    df_t1 = df_t0[df_t0["source"] == "artsy"].reset_index(drop=True)
    tiers["T1_artsy_only_cleansed"] = cleansed(df_t1)

    df_t2 = df_t1[df_t1["year_made"].notna()].reset_index(drop=True)
    tiers["T2_artsy_year_notna_cleansed"] = cleansed(df_t2)

    df_t3 = df_t2[df_t2["artist_birth_year"].notna()].reset_index(drop=True)
    tiers["T3_artsy_year_birth_notna_cleansed"] = cleansed(df_t3)

    df_t4 = df_t3[df_t3["career_age"].notna() & df_t3["work_age"].notna()].reset_index(drop=True)
    tiers["T4_artsy_strict_4field_cleansed"] = cleansed(df_t4)

    df_t5 = df_t0[df_t0["is_krw"] == 1].reset_index(drop=True)
    tiers["T5_krw_only_cleansed"] = cleansed(df_t5)

    t6_mask = (
        df_t4["price_krw"].between(100_001, 999_999_999, inclusive="both")
        & df_t4["area_cm2"].between(101, 49_999, inclusive="both")
        & df_t4["aspect_ratio"].between(0.0001, 10, inclusive="right")
        & df_t4["ho"].between(1, 200, inclusive="both")
        & df_t4["year_made"].between(1950, CURRENT_YEAR, inclusive="both")
        & ((df_t4["year_made"] - df_t4["artist_birth_year"]) >= 10)
        & df_t4["work_age"].between(0, 100, inclusive="both")
        & (df_t4["artist_total_works"] > 0)
        & (df_t4["gallery_city_count"] > 0)
    )
    df_t6 = df_t4[t6_mask].reset_index(drop=True)
    tiers["T6_t4_anomaly_filtered_cleansed"] = cleansed(df_t6)

    summaries = []
    for name, df in tiers.items():
        out = OUT_DIR / f"{name}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        summaries.append({
            "name": name,
            "n_rows": len(df),
            "n_cols": len(df.columns),
            "size_mb": round(out.stat().st_size / 1024 / 1024, 2),
        })
        logger.info("Wrote %s: %d rows / %d cols / %.2f MB",
                    name, len(df), len(df.columns), out.stat().st_size / 1024 / 1024)

    # ─── Display companion (mediums_json / supports_json 별도) ───
    companion_cols = ["artwork_id", "artist_slug", "title"] + [c for c in SEPARATE_COLS if c in df_t0.columns]
    df_companion = df_t0[companion_cols].copy()
    out_companion = OUT_DIR / "display_companion_T0.csv"
    df_companion.to_csv(out_companion, index=False, encoding="utf-8-sig")
    logger.info("Wrote display companion: %s (%d rows / %d cols)",
                out_companion, len(df_companion), len(df_companion.columns))

    # ─── Human-readable T0 (한글 column 명) ─────────────────────
    df_human = df_t0_clean.copy()
    df_human.columns = [HAN_MAP.get(c, c) for c in df_human.columns]
    out_human = OUT_DIR / "human_readable_T0.csv"
    df_human.to_csv(out_human, index=False, encoding="utf-8-sig")
    logger.info("Wrote human-readable: %s", out_human)

    # ─── column_dictionary.csv (제거 row 삭제 / 새 컬럼 추가) ───
    out_dict = OUT_DIR / "column_dictionary.csv"
    with open(out_dict, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["영문명", "한글명", "분류", "정의", "처리결정", "사유", "생성방식", "계산공식"])
        for entry in COLUMN_DECISIONS:
            col, ko, cat, defn, decision, reason, how, formula = entry
            w.writerow([col, ko, cat, defn, decision, reason, how, formula])
    logger.info("Wrote column dictionary: %s (%d rows / 8 columns)",
                out_dict, len(COLUMN_DECISIONS))

    # ─── removed_columns_log.csv (제거된 column 의 record / 별도) ──
    out_removed = OUT_DIR / "removed_columns_log.csv"
    with open(out_removed, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["영문명", "제거사유"])
        for col, reason in REMOVE_COLS_RECORD:
            w.writerow([col, reason])
    logger.info("Wrote removed columns log: %s (%d rows)", out_removed, len(REMOVE_COLS_RECORD))

    # ─── INDEX.json + INDEX.md ─────────────────────────────────
    out_index = OUT_DIR / "INDEX.json"
    with open(out_index, "w", encoding="utf-8") as f:
        json.dump({
            "scope": "Tier CSV cleanup — 검수 + 코덱스 의견 반영",
            "decision_binding": False,
            "operational_unchanged": True,
            "cleanup_summary": {
                "total_columns_original": 66,
                "kept": len(KEEP_COLS),
                "separated": len(SEPARATE_COLS),
                "removed": len(REMOVE_COLS),
            },
            "tiers": summaries,
            "note": ("본 cycle 산출물 = Tier CSV 계산 컬럼 검수 + 정리 자료. "
                     "decision-binding 결과물 X / 운영 코드 / parquet / load_data() / "
                     "feature generation 로직 변경 X / 운영 채택 = 별도 검증 + 사용자 결정"),
        }, f, indent=2, ensure_ascii=False)

    # MD
    out_md = OUT_DIR / "INDEX.md"
    lines = [
        "# Cleansed Dataset Tiers (2026-05-08)\n\n",
        "**Decision binding**: ❌ X (정리 자료 만 / 운영 코드 / parquet 변경 X)\n\n",
        "## 검수 + 코덱스 의견 반영\n\n",
        f"- 원본 column 수: 66\n",
        f"- 보존 (KEEP): {len(KEEP_COLS)} columns\n",
        f"- 분리 (SEPARATE / display companion): {len(SEPARATE_COLS)} columns\n",
        f"- 제거 (REMOVE): {len(REMOVE_COLS)} columns\n\n",
        "## 산출 파일\n\n",
        "| 파일 | rows | cols | 크기 |\n",
        "|---|---:|---:|---:|\n",
    ]
    for s in summaries:
        lines.append(f"| `{s['name']}.csv` | {s['n_rows']:,} | {s['n_cols']} | {s['size_mb']} MB |\n")
    lines += [
        f"| `display_companion_T0.csv` | {len(df_companion):,} | {len(df_companion.columns)} | (mediums_json / supports_json 분리 보존) |\n",
        f"| `human_readable_T0.csv` | {len(df_human):,} | {len(df_human.columns)} | (한글 column 명 사람용 파생본) |\n",
        f"| `column_dictionary.csv` | {len(COLUMN_DECISIONS)} entries | 8 | (영문/한글/분류/정의/처리결정/사유/생성방식/계산공식 — 제거 row 미포함) |\n",
        f"| `removed_columns_log.csv` | {len(REMOVE_COLS_RECORD)} entries | 2 | (제거된 column 의 영문명 + 사유 record) |\n",
    ]
    out_md.write_text("".join(lines), encoding="utf-8")
    logger.info("Wrote INDEX: %s + %s", out_index, out_md)

    print("\n=== Cleanup Summary ===")
    print(f"  Original cols: 66")
    print(f"  Kept: {len(KEEP_COLS)} → cleansed CSV body")
    print(f"  Separated: {len(SEPARATE_COLS)} → display companion")
    print(f"  Removed: {len(REMOVE_COLS)} → out (placeholder/sparse/unused)")


if __name__ == "__main__":
    main()
