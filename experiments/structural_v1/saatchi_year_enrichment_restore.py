"""Saatchi year_made enrichment 복원 — restoration reproducibility cycle.

Pre-registered: docs/saatchi_year_enrichment_restore_prereg_20260508.md
Decision binding: ❌ X (restoration coverage 검증 만 / 모델 효과 / 운영 채택 영역 X)

목표: commit dce0dfa (2026-05-01) 의 enrichment artifact 의 git history 복원
+ saatchi_year_made_merger 적용 → enriched parquet (별도 file) 생성 +
restoration coverage 정량 검증.

Fail-closed protocol:
- 운영 saatchi_cleaned.parquet sha-256 pre/post 정확 동일 의무
- output path != input path assert
- 위반 detect 시 즉시 abort
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from saatchi_year_made_merger import (  # type: ignore  # noqa: E402
    WORK_AGE_REF_YEAR,
    add_has_year_made_flag,
    load_enrichment_year_map,
    merge_year_made,
    recompute_work_age,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DCE0DFA = "dce0dfa1fd5b3d7e6e43f651e921140e56b68a2b"
ARTIFACT_DIR = REPO / "data" / "saatchi_year_enrichment_artifact_20260501"
OPERATIONAL_SAATCHI = REPO / "data" / "saatchi_cleaned.parquet"
ENRICHED_OUT = REPO / "data" / "saatchi_year_enriched.parquet"
RESULTS_DIR = REPO / "experiments" / "structural_v1" / "results"
SUMMARY_OUT = RESULTS_DIR / "saatchi_year_enrichment_summary_20260508.json"

EXPECTED_BLOB_RAW = "4fb8b53d9242ee62a49fb826c34276d7104c3870"
EXPECTED_BLOB_SUMMARY = "dc8c07d090af88576c614272009ef54c64cbbf18"
EXPECTED_BLOB_DOC = "e1dcae48574d41ca3871c707dbddad6b30b84b81"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_id(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path)], cwd=REPO
    ).decode().strip()


def restore_artifact(blob_path: str, out_path: Path) -> None:
    """git show dce0dfa:blob_path > out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    blob = subprocess.check_output(
        ["git", "show", f"{DCE0DFA}:{blob_path}"], cwd=REPO
    )
    out_path.write_bytes(blob)


def main() -> dict:
    logger.info("=" * 70)
    logger.info("Saatchi year_made enrichment restoration cycle")
    logger.info("=" * 70)

    # ─── Step 1: git history 복원 ─────────────────────────────────────
    logger.info("--- Step 1: git history 복원 ---")
    raw_jsonl = ARTIFACT_DIR / "raw.jsonl"
    summary_json = ARTIFACT_DIR / "summary.json"
    doc_md = REPO / "docs" / "v3_4_2_step4_full_results.md"

    restore_artifact("model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl", raw_jsonl)
    restore_artifact("model_test_results/v3_diagnostics/saatchi_step4_full_enrichment.json", summary_json)
    if not doc_md.exists():
        restore_artifact("docs/v3_4_2_step4_full_results.md", doc_md)
    logger.info("Restored: %s, %s, %s", raw_jsonl.name, summary_json.name, doc_md.name)

    # ─── Step 2: provenance verification ──────────────────────────────
    logger.info("--- Step 2: provenance verification ---")
    blob_raw = git_blob_id(raw_jsonl)
    blob_summary = git_blob_id(summary_json)
    blob_doc = git_blob_id(doc_md)
    sha_raw = sha256_file(raw_jsonl)
    sha_summary = sha256_file(summary_json)
    sha_doc = sha256_file(doc_md)
    logger.info("raw.jsonl  : blob=%s sha256=%s", blob_raw, sha_raw)
    logger.info("summary.json: blob=%s sha256=%s", blob_summary, sha_summary)
    logger.info("doc.md     : blob=%s sha256=%s", blob_doc, sha_doc)

    assert blob_raw == EXPECTED_BLOB_RAW, f"raw.jsonl blob mismatch: {blob_raw}"
    assert blob_summary == EXPECTED_BLOB_SUMMARY, f"summary blob mismatch: {blob_summary}"
    assert blob_doc == EXPECTED_BLOB_DOC, f"doc blob mismatch: {blob_doc}"

    # ─── Step 3: jsonl structure verification ─────────────────────────
    logger.info("--- Step 3: jsonl structure verification ---")
    rows = []
    with open(raw_jsonl) as f:
        for line in f:
            rows.append(json.loads(line))
    n_rows = len(rows)
    unique_urls = set(r["url"] for r in rows if r.get("url"))
    valid_year_urls = set(
        r["url"] for r in rows
        if r.get("url") and r.get("fetch_status") == "ok" and r.get("year_created")
    )
    logger.info("jsonl rows: %d / unique URLs: %d / valid_year unique: %d",
                n_rows, len(unique_urls), len(valid_year_urls))
    assert n_rows == 21973, f"jsonl rows: {n_rows} != 21973"
    assert len(unique_urls) == 21087, f"unique URLs: {len(unique_urls)} != 21087"
    assert len(valid_year_urls) == 20644, f"valid_year unique: {len(valid_year_urls)} != 20644"

    # ─── Step 4: pre-run operational saatchi sha-256 ──────────────────
    logger.info("--- Step 4: pre-run operational saatchi digest ---")
    pre_sha = sha256_file(OPERATIONAL_SAATCHI)
    logger.info("operational saatchi pre-run sha-256: %s", pre_sha)

    # output path != input path assert (fail-closed)
    assert ENRICHED_OUT.resolve() != OPERATIONAL_SAATCHI.resolve(), (
        "Output path equals operational source — fail-closed abort"
    )

    # ─── Step 5: merger 적용 ──────────────────────────────────────────
    logger.info("--- Step 5: merger 적용 (V_year_only / saatchi only) ---")
    df = pd.read_parquet(OPERATIONAL_SAATCHI)
    if "source" not in df.columns:
        df["source"] = "saatchi"
    logger.info("operational saatchi rows (raw): %d", len(df))

    enrichment_map = load_enrichment_year_map(raw_jsonl)
    logger.info("enrichment map size: %d", len(enrichment_map))

    df_after = merge_year_made(df, enrichment_map, only_saatchi=True)
    df_after = add_has_year_made_flag(df_after)
    df_after = recompute_work_age(df_after, ref_year=WORK_AGE_REF_YEAR)

    # ─── Step 6: post-run digest verification (fail-closed) ──────────
    logger.info("--- Step 6: post-run digest verification ---")
    post_sha = sha256_file(OPERATIONAL_SAATCHI)
    if pre_sha != post_sha:
        raise RuntimeError(
            f"FAIL-CLOSED ABORT: operational saatchi changed during run "
            f"(pre={pre_sha} post={post_sha})"
        )
    logger.info("operational saatchi sha-256 unchanged: %s", post_sha)

    # ─── Step 7: write enriched parquet (별도 file) ───────────────────
    logger.info("--- Step 7: write enriched parquet ---")
    df_after.to_parquet(ENRICHED_OUT, index=False)
    enriched_sha = sha256_file(ENRICHED_OUT)
    logger.info("enriched parquet: %s (sha-256=%s)", ENRICHED_OUT, enriched_sha)

    # ─── Step 8: restoration coverage 검증 ───────────────────────────
    logger.info("--- Step 8: restoration coverage 검증 ---")

    # in-filter Saatchi rows 의 year_made notna count
    in_filter = df_after[df_after["is_excluded_for_training"] == 0]
    saatchi_in_filter = in_filter[in_filter["source"] == "saatchi"]
    n_saatchi_in_filter = len(saatchi_in_filter)
    n_year_filled = int(saatchi_in_filter["year_made"].notna().sum())
    logger.info(
        "Saatchi (in-filter): n=%d / year_made notna=%d (%.2f%%)",
        n_saatchi_in_filter, n_year_filled, n_year_filled / n_saatchi_in_filter * 100
    )

    # work_age = 2026 - year_made 정합 (notna 영역) — strict equality
    notna_mask = saatchi_in_filter["year_made"].notna()
    expected_work_age = (WORK_AGE_REF_YEAR - saatchi_in_filter.loc[notna_mask, "year_made"]).to_numpy()
    actual_work_age = saatchi_in_filter.loc[notna_mask, "work_age"].to_numpy()
    work_age_strict_equal = bool((expected_work_age == actual_work_age).all())
    work_age_n_mismatch = int((expected_work_age != actual_work_age).sum())
    logger.info(
        "work_age = 2026 - year_made (notna 영역): strict_equal=%s mismatch_n=%d",
        work_age_strict_equal, work_age_n_mismatch,
    )

    # URL set verification (jsonl unique URL == 운영 saatchi in-filter URL set)
    op_in_filter_urls = set(in_filter[in_filter["source"] == "saatchi"]["artwork_url"])
    url_set_equal = (unique_urls == op_in_filter_urls)
    n_jsonl_only = len(unique_urls - op_in_filter_urls)
    n_op_only = len(op_in_filter_urls - unique_urls)
    logger.info(
        "URL set check: jsonl_unique=%d / op_in_filter=%d / equal=%s / jsonl_only=%d / op_only=%d",
        len(unique_urls), len(op_in_filter_urls), url_set_equal, n_jsonl_only, n_op_only,
    )

    # ─── PASS/FAIL ────────────────────────────────────────────────────
    checks = {
        "jsonl_rows_exact_21973": n_rows == 21973,
        "jsonl_unique_urls_exact_21087": len(unique_urls) == 21087,
        "jsonl_valid_year_unique_exact_20644": len(valid_year_urls) == 20644,
        "blob_raw_exact": blob_raw == EXPECTED_BLOB_RAW,
        "blob_summary_exact": blob_summary == EXPECTED_BLOB_SUMMARY,
        "blob_doc_exact": blob_doc == EXPECTED_BLOB_DOC,
        "operational_unchanged": pre_sha == post_sha,
        "saatchi_in_filter_year_filled_exact_20644": n_year_filled == 20644,
        "work_age_strict_equal_recompute": work_age_strict_equal,
        "url_set_equal_jsonl_vs_in_filter": url_set_equal,
    }
    pass_overall = all(checks.values())

    result = {
        "verdict": "PASS" if pass_overall else "FAIL",
        "source_commit": DCE0DFA,
        "operational_saatchi_sha256_pre": pre_sha,
        "operational_saatchi_sha256_post": post_sha,
        "enriched_parquet_path": str(ENRICHED_OUT.relative_to(REPO)),
        "enriched_parquet_sha256": enriched_sha,
        "artifact_provenance": {
            "raw_jsonl": {
                "path": str(raw_jsonl.relative_to(REPO)),
                "git_blob_id": blob_raw,
                "sha256_file_digest": sha_raw,
                "rows": n_rows,
            },
            "summary_json": {
                "path": str(summary_json.relative_to(REPO)),
                "git_blob_id": blob_summary,
                "sha256_file_digest": sha_summary,
            },
            "doc_md": {
                "path": str(doc_md.relative_to(REPO)),
                "git_blob_id": blob_doc,
                "sha256_file_digest": sha_doc,
            },
        },
        "jsonl_structure": {
            "total_rows": n_rows,
            "unique_urls": len(unique_urls),
            "valid_year_unique_urls": len(valid_year_urls),
            "retry_duplicate_rows": n_rows - len(unique_urls),
        },
        "restoration_coverage": {
            "saatchi_in_filter_rows": n_saatchi_in_filter,
            "year_made_filled": n_year_filled,
            "fill_rate_pct_4dp": round(n_year_filled / n_saatchi_in_filter * 100, 4),
            "fill_rate_raw": n_year_filled / n_saatchi_in_filter,
            "year_made_unresolved": n_saatchi_in_filter - n_year_filled,
            "work_age_strict_equal": work_age_strict_equal,
            "work_age_mismatch_n": work_age_n_mismatch,
            "url_set_equal_jsonl_vs_in_filter": url_set_equal,
            "url_only_in_jsonl": n_jsonl_only,
            "url_only_in_op_in_filter": n_op_only,
        },
        "checks": checks,
        "decision_binding": {
            "is_decision_binding": False,
            "scope": "restoration reproducibility 만",
            "not_efficacy_pass": True,
            "not_adoption_pass": True,
            "not_production_candidate": True,
            "operational_saatchi_changed": False,
        },
    }

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    logger.info("Wrote %s", SUMMARY_OUT)
    logger.info("VERDICT: %s", result["verdict"])
    return result


if __name__ == "__main__":
    main()
