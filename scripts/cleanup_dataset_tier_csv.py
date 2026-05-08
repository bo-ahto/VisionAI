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
    # 식별자 (보존)
    ("artwork_id", "작품ID", "identifier", "Source 의 작품 식별자", "보존", "식별자"),
    ("artist_slug", "작가식별자", "identifier", "Source 의 작가 식별자", "보존", "식별자"),
    ("artist_name", "작가명", "수집", "Source 의 작가 표시명", "보존", "수집 raw"),
    ("title", "작품제목", "수집", "Source 의 작품 제목", "보존", "수집 raw"),
    ("image_url", "이미지URL", "수집", "Source 의 이미지 URL", "보존", "수집 raw"),
    ("artwork_url", "작품URL", "수집", "Source 의 작품 페이지 URL", "보존", "수집 raw"),
    # 가격 (보존)
    ("price_krw", "가격(KRW)", "수집+환산", "Source 가격 → KRW 환산", "보존", "수집+환산 (target precursor)"),
    ("price_raw", "원본가격표기", "수집", "Source 의 원본 가격 문자열", "보존", "수집 raw / display"),
    ("price_currency", "가격통화", "수집", "Source 의 가격 통화", "보존", "수집 raw"),
    ("is_krw", "원화여부", "계산", "1 if price_currency=='KRW' else 0", "보존", "계산 EXACT 검증"),
    ("ln_price", "로그가격", "계산", "log(price_krw)", "보존", "계산 EXACT 검증 / 학습 target"),
    # 크기 (보존)
    ("dimensions_cm", "크기표기(원본)", "수집", "Source 의 dimensions 원본", "보존", "수집 raw"),
    ("area_cm2", "면적(cm²)", "계산", "width × height", "보존", "계산 (raw width/height 의 derivation)"),
    ("aspect_ratio", "가로세로비", "계산", "long-axis / short-axis", "보존", "계산"),
    ("ln_area", "로그면적", "계산", "log(area_cm2.clip(lower=1))", "보존", "계산 EXACT 검증"),
    ("ho", "호수", "계산", "area→호수 mapping", "보존", "계산 (한국 미술 표준 mapping)"),
    ("ho_power", "호수^0.74", "계산", "ho^0.74 if ho>0 else 0", "보존", "계산 EXACT 검증"),
    ("ln_ho", "로그호수", "계산", "log(ho+1)", "보존", "계산 EXACT 검증"),
    ("is_small", "소형여부", "계산", "1 if ho<=3 else 0", "보존", "계산 EXACT 검증"),
    ("ho_x_support", "호수×지지체계수", "계산", "ho * support_factor", "보존", "계산 EXACT 검증"),
    # 매체/지지체 (보존)
    ("medium", "매체(원본)", "수집", "Source 의 medium 원본", "보존", "수집 raw"),
    ("medium_category", "매체분류", "categorical 정규화", "표준 분류 (oil/acrylic/...)", "보존", "categorical 분포 OK"),
    ("medium_l1", "매체대분류", "categorical 정규화", "1차 분류", "보존", "categorical"),
    ("medium_leaf", "매체소분류", "categorical 정규화", "leaf 분류", "보존", "categorical"),
    ("support_type", "지지체분류", "categorical 정규화", "표준 분류 (canvas/paper/...)", "보존", "categorical 분포 OK"),
    ("support_l1", "지지체대분류", "categorical 정규화", "1차 분류", "보존", "categorical"),
    ("support_leaf", "지지체소분류", "categorical 정규화", "leaf 분류", "보존", "categorical"),
    ("support_factor", "지지체계수", "계산", "support_type → 가격 계수", "보존", "계산"),
    ("has_multimedia", "복합매체여부", "계산", "1 if mediums_json 길이>1", "보존", "계산"),
    # 제작연도 / 작가 시기 (보존)
    ("year_made", "제작연도", "수집/enrichment", "Artsy=수집 / Saatchi=PR #51 enrichment", "보존", "수집 + enrichment (PR #51)"),
    ("has_year_made", "제작연도여부", "계산", "1 if year_made notna", "보존", "계산 EXACT 검증"),
    ("work_age", "작품연한", "계산", "2026 - year_made", "보존", "계산 EXACT 검증"),
    # 작가 프로필 (보존)
    ("artist_birth_year", "작가생년", "수집/regex추출", "Artsy=수집 / Saatchi=bio regex", "보존", "수집 + regex (PR #52 pilot 미적용)"),
    ("has_birth_year", "생년여부", "계산", "1 if artist_birth_year notna", "보존", "계산 EXACT 검증"),
    ("career_age", "활동연수", "계산", "year_made - first_exhibition_year", "보존", "계산 (Artsy only)"),
    ("career_stage", "경력단계점수", "계산", "multi-factor v2 score (0-8)", "보존", "계산"),
    ("artist_total_works", "작가총작품수", "수집", "Source 의 작가 총 작품 수", "보존", "수집"),
    ("for_sale_ratio", "판매중비율", "계산", "for_sale / total_works", "보존", "계산"),
    ("solo_count", "개인전수", "수집→정규화", "exhibitions/bio 추정", "보존", "수집→정규화"),
    ("group_count", "단체전수", "수집→정규화", "exhibitions/bio 추정", "보존", "수집→정규화"),
    ("fair_count", "아트페어수", "수집→정규화", "exhibitions/bio 추정", "보존", "수집→정규화"),
    ("attribution_class", "유일성분류", "categorical 정규화", "Unique / Limited edition / ...", "보존", "categorical 분포 OK"),
    ("is_unique", "유일작품여부", "계산", "1 if 'Unique' else 0", "보존", "계산 EXACT 검증"),
    ("is_edition", "에디션여부", "계산", "1 if 'Limited edition' else 0", "보존", "계산 EXACT 검증"),
    # 갤러리 (보존)
    ("gallery_name", "갤러리명", "수집", "Source 의 갤러리 이름", "보존", "수집"),
    ("gallery_type", "갤러리유형", "수집", "Gallery / Online Gallery", "보존", "수집 (분포 OK)"),
    ("gallery_tier", "갤러리티어", "계산", "gallery_alias_map 매핑", "보존", "계산"),
    ("gallery_city_count", "갤러리도시수", "계산", "count(gallery_cities)", "보존", "계산"),
    ("has_international", "해외갤러리여부", "계산 (source-conditional)", "Artsy: city_count>=2 / Saatchi: 항상 1 (source policy)", "보존+정의명시", "정의 source-conditional 명시 의무 (코덱스)"),
    # 메타 (보존)
    ("source", "데이터소스", "수집/구분", "artsy / saatchi", "보존", "구분자"),
    ("is_excluded_for_training", "학습제외여부", "training_metadata", "운영 학습 제외 flag", "보존", "training metadata"),
    # ─── 분리 (display companion 별도 산출) ──────────────────────
    ("mediums_json", "매체배열(JSON)", "categorical 정규화", "복수 medium 의 JSON 배열", "분리", "코덱스: UI 표시 용 / cleansed CSV 본체 미포함"),
    ("supports_json", "지지체배열(JSON)", "categorical 정규화", "복수 support 의 JSON 배열", "분리", "코덱스: UI 표시 용 / cleansed CSV 본체 미포함"),
    # ─── 제거 ────────────────────────────────────────────────
    ("ho_price_level", "호수가격레벨", "placeholder", "operational 0.0 fill", "제거", "100% zero / placeholder (코덱스)"),
    ("medium_price_level", "매체가격레벨", "placeholder", "operational 0.0 fill", "제거", "100% zero / placeholder (코덱스)"),
    ("profile_completeness", "프로필완성도", "placeholder", "operational 0.0 fill", "제거", "100% zero / placeholder (코덱스)"),
    ("request_ratio", "가격문의비율", "계산 (sparse)", "'Price on request' 비율 (Artsy 만)", "제거", "94.69% zero / sparse / Artsy only (코덱스)"),
    ("artist_is_p1", "P1작가여부", "categorical 정규화", "운영 P1 분류", "제거", "99.68% False / sparse (코덱스)"),
    ("has_special_finish", "특수마감여부", "계산 (sparse)", "특수 finish binary", "제거", "99.59% zero / source audit 결손 (코덱스)"),
    ("vintage_premium", "vintage 프리미엄", "계산 (미작동)", "career_stage_int >= 3 의 work_age", "제거", "99.93% zero / 사실상 미작동 (코덱스)"),
    ("freshness_discount", "freshness 디스카운트", "계산 (검수불가)", "career_stage_int < 3 의 work_age", "제거", "career_stage_int 미포함 / 검수 불가 (코덱스)"),
    ("value_grade_note", "가치등급노트", "training_metadata (sparse)", "manual annotation", "제거", "99.09% empty (코덱스)"),
    ("exclude_reason", "제외사유", "training_metadata", "T0 filter 후 100% empty", "제거", "T0 = filter 후 / 100% empty (코덱스)"),
    ("has_seoul", "서울갤러리여부", "계산 (검수불가)", "gallery_cities 'Seoul' 포함", "제거", "raw gallery_cities 미포함 / 검수 불가 (코덱스 audit backlog)"),
    ("ln_followers", "로그팔로워", "계산 (검수불가)", "log(artist_followers+1)", "제거", "raw artist_followers 미포함 / 검수 불가 (코덱스 audit backlog)"),
    ("has_depth", "깊이여부", "계산 (검수불가)", "depth_cm notna", "제거", "raw depth_cm 미포함 / 검수 불가 (코덱스 audit backlog)"),
]

KEEP_COLS = [c[0] for c in COLUMN_DECISIONS if c[4] == "보존" or c[4] == "보존+정의명시"]
SEPARATE_COLS = [c[0] for c in COLUMN_DECISIONS if c[4] == "분리"]
REMOVE_COLS = [c[0] for c in COLUMN_DECISIONS if c[4] == "제거"]
HAN_MAP = {c[0]: c[1] for c in COLUMN_DECISIONS}


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

    # ─── column_dictionary.csv ─────────────────────────────────
    out_dict = OUT_DIR / "column_dictionary.csv"
    with open(out_dict, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["영문명", "한글명", "분류", "정의", "처리결정", "사유"])
        for col, ko, cat, defn, decision, reason in COLUMN_DECISIONS:
            w.writerow([col, ko, cat, defn, decision, reason])
    logger.info("Wrote column dictionary: %s", out_dict)

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
        f"| `column_dictionary.csv` | {len(COLUMN_DECISIONS)} entries | 6 | (영문/한글/분류/정의/처리결정/사유) |\n",
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
