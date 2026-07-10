"""Tier 별 CSV 산출 — 데이터셋 의사결정 입력 자료.

운영 28,376 rows + Saatchi year_made enrichment 적용 후 의 7 Tier (T0-T6)
+ Saatchi enriched-only + KRW-only 의 CSV 산출.

각 CSV = `data/dataset_tiers_20260508/` 영역.

Decision binding: ❌ X (정리 자료 만 / 운영 채택 결정 X / Cycle 1 verdict 무관).
"""

from __future__ import annotations

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

OUT_DIR = REPO / "data" / "dataset_tiers_20260508"
ENRICHMENT_JSONL = REPO / "data" / "saatchi_year_enrichment_artifact_20260501" / "raw.jsonl"
CURRENT_YEAR = 2026


def apply_saatchi_enrichment(df: pd.DataFrame) -> pd.DataFrame:
    """Saatchi rows 에 dce0dfa enrichment 적용 (year_made + has_year_made + work_age)."""
    if not ENRICHMENT_JSONL.exists():
        # Restore from git history if not present
        import subprocess
        ENRICHMENT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.check_output(
            [
                "git", "show",
                "dce0dfa1fd5b3d7e6e43f651e921140e56b68a2b:"
                "model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl",
            ],
            cwd=REPO,
        )
        ENRICHMENT_JSONL.write_bytes(blob)
        logger.info("Restored enrichment jsonl from git history: %s", ENRICHMENT_JSONL)

    enrichment_map = load_enrichment_year_map(ENRICHMENT_JSONL)
    df_after = merge_year_made(df, enrichment_map, only_saatchi=True)
    df_after = add_has_year_made_flag(df_after)
    df_after = recompute_work_age(df_after, ref_year=WORK_AGE_REF_YEAR)
    return df_after


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load + apply enrichment
    logger.info("Loading operational dataset...")
    df_full = load_data()  # raw 29,361
    df_full = apply_saatchi_enrichment(df_full)
    logger.info("After enrichment: n=%d", len(df_full))

    # Step 2: Filter to T0 (28,376 = operational training set)
    df_t0 = df_full[df_full["is_excluded_for_training"] == 0].reset_index(drop=True)
    logger.info("T0 (is_excluded_for_training==0): n=%d", len(df_t0))

    # Common helper
    def export(df: pd.DataFrame, name: str, description: str) -> dict:
        out = OUT_DIR / f"{name}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        size_mb = out.stat().st_size / 1024 / 1024
        n_artists = int(df["artist_slug"].nunique()) if "artist_slug" in df.columns else 0
        n_year_notna = int(df["year_made"].notna().sum()) if "year_made" in df.columns else 0
        n_birth_notna = int(df["artist_birth_year"].notna().sum()) if "artist_birth_year" in df.columns else 0
        info = {
            "name": name,
            "description": description,
            "path": str(out.relative_to(REPO)),
            "size_mb": round(size_mb, 2),
            "n_rows": len(df),
            "n_artists": n_artists,
            "year_made_notna": n_year_notna,
            "year_made_notna_pct": round(n_year_notna / len(df) * 100, 2) if len(df) else 0,
            "artist_birth_year_notna": n_birth_notna,
            "artist_birth_year_notna_pct": round(n_birth_notna / len(df) * 100, 2) if len(df) else 0,
        }
        if "source" in df.columns:
            info["source_dist"] = {k: int(v) for k, v in df["source"].value_counts().items()}
        logger.info(
            "Exported %s: n=%d artists=%d year=%d (%.2f%%) birth=%d (%.2f%%) size=%.2fMB",
            name, len(df), n_artists, n_year_notna, info["year_made_notna_pct"],
            n_birth_notna, info["artist_birth_year_notna_pct"], size_mb,
        )
        return info

    summaries = []

    # T0: 운영 채택 (28,376 / 운영 production 영역)
    summaries.append(export(
        df_t0, "T0_operational_28376",
        "T0: 운영 채택 = Artsy 7,289 + Saatchi 21,087 (Saatchi year_made enrichment 적용 후)"
    ))

    # T1: Artsy only
    df_t1 = df_t0[df_t0["source"] == "artsy"].reset_index(drop=True)
    summaries.append(export(
        df_t1, "T1_artsy_only",
        "T1: Artsy source 통일 (7,289)"
    ))

    # T2: Artsy + year_made notna
    df_t2 = df_t1[df_t1["year_made"].notna()].reset_index(drop=True)
    summaries.append(export(
        df_t2, "T2_artsy_year_notna",
        "T2: Artsy + year_made notna (7,231)"
    ))

    # T3: Artsy + year + birth notna
    df_t3 = df_t2[df_t2["artist_birth_year"].notna()].reset_index(drop=True)
    summaries.append(export(
        df_t3, "T3_artsy_year_birth_notna",
        "T3: Artsy + year_made + artist_birth_year 둘 다 notna (5,845)"
    ))

    # T4: Artsy + 4-field strict
    df_t4 = df_t3[df_t3["career_age"].notna() & df_t3["work_age"].notna()].reset_index(drop=True)
    summaries.append(export(
        df_t4, "T4_artsy_strict_4field",
        "T4: Artsy + 4-field 전체 notna (year + birth + career + work_age, 4,628)"
    ))

    # T5: KRW only
    df_t5 = df_t0[df_t0["is_krw"] == 1].reset_index(drop=True)
    summaries.append(export(
        df_t5, "T5_krw_only",
        "T5: KRW only (price_currency='KRW' / artsy_gallery cell, 868)"
    ))

    # T6: T4 + 본 audit rule-filter
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
    summaries.append(export(
        df_t6, "T6_t4_anomaly_filtered",
        "T6: T4 + 본 audit (PR #50) 의 rule-filter 적용 (4,460 예상)"
    ))

    # 추가: Saatchi only (enriched 21,087)
    df_saatchi_in_filter = df_t0[df_t0["source"] == "saatchi"].reset_index(drop=True)
    summaries.append(export(
        df_saatchi_in_filter, "extra_saatchi_only_in_filter",
        "추가: Saatchi only (in-filter, year_made enriched, 21,087)"
    ))

    # Saatchi raw (21,721 / pre-filter, enriched)
    df_saatchi_raw = df_full[df_full["source"] == "saatchi"].reset_index(drop=True)
    summaries.append(export(
        df_saatchi_raw, "extra_saatchi_raw_enriched",
        "추가: Saatchi raw (21,721 / pre-filter / year_made enriched)"
    ))

    # Step 3: Summary index
    summary_path = OUT_DIR / "INDEX.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "scope": "Tier 별 CSV 산출 — 데이터셋 의사결정 입력 자료",
            "decision_binding": False,
            "operational_unchanged": True,
            "saatchi_year_enrichment_applied": True,
            "saatchi_birthyear_pilot_NOT_applied": True,
            "tiers": summaries,
        }, f, indent=2, ensure_ascii=False)
    logger.info("Wrote INDEX: %s", summary_path)

    # Markdown table
    md_path = OUT_DIR / "INDEX.md"
    lines = [
        "# Dataset Tiers (2026-05-08)\n\n",
        "Saatchi year_made enrichment 적용 (PR #51) / birthyear regex pilot 미적용 (PR #52 = Precision FAIL)\n\n",
        "**Decision binding**: ❌ X (정리 자료 만)\n\n",
        "| Tier | n_rows | n_artists | year notna | birth_year notna | size MB | path |\n",
        "|---|---:|---:|---:|---:|---:|---|\n",
    ]
    for s in summaries:
        lines.append(
            f"| {s['name']} | {s['n_rows']:,} | {s['n_artists']:,} | "
            f"{s['year_made_notna']:,} ({s['year_made_notna_pct']}%) | "
            f"{s['artist_birth_year_notna']:,} ({s['artist_birth_year_notna_pct']}%) | "
            f"{s['size_mb']} | `{s['path']}` |\n"
        )
    md_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Wrote MD: %s", md_path)


if __name__ == "__main__":
    main()
