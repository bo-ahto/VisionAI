"""Saatchi artist_birth_year regex 확장 pilot — restoration coverage 측정.

Pre-registered: docs/saatchi_birthyear_regex_pilot_prereg_20260508.md
Decision binding: ❌ X (pilot 측정 만 / 운영 코드 freeze)

목표:
- 운영 prepare_saatchi_dataset.py:101 의 extract_birth_year 의 기존 5 패턴
  + 사전 정의 P_NEW_1 / P_NEW_2 추가 시 의 회수율 증분 + precision 측정
- 832 unique artists 전체 의 old-only vs pilot-old-subset 정확 동일 검증
- 추가 추출 작가 의 6-field evidence record 산출 (사용자 수동 검수 입력)

Fail-closed protocol:
- 운영 prepare_saatchi_dataset.py 변경 X (import 만)
- 운영 saatchi_cleaned.parquet 변경 X (read 만)
- 실행 시작 / 실행 직후 sha-256 + git diff 검증
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from prepare_saatchi_dataset import extract_birth_year as old_extract_birth_year  # type: ignore  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OPERATIONAL_PREPARE = REPO / "scripts" / "prepare_saatchi_dataset.py"
OPERATIONAL_SAATCHI = REPO / "data" / "saatchi_cleaned.parquet"
ARTISTS_JSON = REPO / "data" / "saatchi_kr_artists.json"

RESULTS_DIR = REPO / "experiments" / "structural_v1" / "results"
SUMMARY_OUT = RESULTS_DIR / "saatchi_birthyear_regex_pilot_20260508.json"
EVIDENCE_OUT = RESULTS_DIR / "saatchi_birthyear_regex_pilot_evidence_20260508.json"

# Validity range (prereg §2.3)
VALIDITY_MIN = 1920
VALIDITY_MAX = 2005

# Pre-registered new patterns (prereg §3.1)
P_NEW_1 = re.compile(
    r"(?i)\bborn\s+in\s+[\w\s,'\-\.]{1,40}?\s+(?:in\s+)?(19[2-9]\d|200[0-5])\b"
)
P_NEW_2 = re.compile(
    r"\b(19[2-9]\d|200[0-5])\s+year\s+birth\b"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_diff_lines(path: Path) -> int:
    """Lines of diff for a path (0 = no change)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--numstat", "--", str(path.relative_to(REPO))],
            cwd=REPO, stderr=subprocess.DEVNULL,
        ).decode().strip()
        if not out:
            return 0
        # numstat format: "<add>\t<del>\t<path>"
        parts = out.split("\t")
        return int(parts[0]) + int(parts[1]) if len(parts) >= 2 else 0
    except Exception:
        return 0


def pilot_extract_birth_year(bio: str) -> tuple[float | None, str | None, str | None]:
    """기존 5 패턴 + P_NEW_1 / P_NEW_2 의 순차 적용.

    Returns:
        (year, pattern_label, matched_span)
        - pattern_label: "old" | "P_NEW_1" | "P_NEW_2" | None
        - matched_span: regex 의 첫 매칭 의 group(0) (None 시 매칭 없음)
    """
    if not bio:
        return None, None, None

    # Step 1: 기존 5 패턴 (운영 함수 호출)
    year_old = old_extract_birth_year(bio)
    if year_old is not None:
        return year_old, "old", None  # span 은 운영 함수 영역 외 / 본 cycle 미사용

    # Step 2: P_NEW_1
    m1 = P_NEW_1.search(bio)
    if m1:
        year = int(m1.group(1))
        if VALIDITY_MIN <= year <= VALIDITY_MAX:
            return float(year), "P_NEW_1", m1.group(0)

    # Step 3: P_NEW_2
    m2 = P_NEW_2.search(bio)
    if m2:
        year = int(m2.group(1))
        if VALIDITY_MIN <= year <= VALIDITY_MAX:
            return float(year), "P_NEW_2", m2.group(0)

    return None, None, None


def main() -> dict:
    logger.info("=" * 70)
    logger.info("Saatchi artist_birth_year regex 확장 pilot")
    logger.info("=" * 70)

    # ─── Step 1: pre-run digest 기록 ──────────────────────────────────
    logger.info("--- Step 1: pre-run digest ---")
    pre_prepare_sha = sha256_file(OPERATIONAL_PREPARE)
    pre_saatchi_sha = sha256_file(OPERATIONAL_SAATCHI)
    pre_prepare_diff = git_diff_lines(OPERATIONAL_PREPARE)
    pre_saatchi_diff = git_diff_lines(OPERATIONAL_SAATCHI)
    logger.info("prepare_saatchi_dataset.py sha=%s git_diff_lines=%d",
                pre_prepare_sha[:16], pre_prepare_diff)
    logger.info("saatchi_cleaned.parquet     sha=%s git_diff_lines=%d",
                pre_saatchi_sha[:16], pre_saatchi_diff)

    # ─── Step 2: 운영 saatchi unique artists ─────────────────────────
    logger.info("--- Step 2: 운영 saatchi unique artists ---")
    df_saatchi = pd.read_parquet(OPERATIONAL_SAATCHI)
    op_artist_slugs = set(df_saatchi["artist_slug"].astype(str))
    n_unique_artists = len(op_artist_slugs)
    logger.info("운영 saatchi unique artists: %d", n_unique_artists)

    # ─── Step 3: load saatchi_kr_artists.json ────────────────────────
    logger.info("--- Step 3: load saatchi_kr_artists.json ---")
    with open(ARTISTS_JSON) as f:
        artists_json = json.load(f)
    matched = [a for a in artists_json if str(a.get("artist_id", "")) in op_artist_slugs]
    matched_aids = set(str(a["artist_id"]) for a in matched)
    logger.info("JSON matched artists: %d / 운영 missing: %d",
                len(matched), n_unique_artists - len(matched_aids))

    # ─── Step 4: regression-free check (832 전수 비교) ───────────────
    logger.info("--- Step 4: regression-free check (832 전수) ---")
    # old-only 결과 (운영 함수 만)
    old_only_results = {}
    pilot_old_subset_results = {}
    for aid in op_artist_slugs:
        # JSON 매칭 작가 만 bio 있음. 매칭 X 면 None
        bio = ""
        for a in matched:
            if str(a["artist_id"]) == aid:
                bio = a.get("bio", "") or ""
                break
        old_only_results[aid] = old_extract_birth_year(bio)
        # pilot 의 old subset = pilot_extract_birth_year 의 pattern_label='old' 영역
        py, plabel, _ = pilot_extract_birth_year(bio)
        pilot_old_subset_results[aid] = py if plabel == "old" else None

    regression_mismatches = []
    for aid in op_artist_slugs:
        if old_only_results[aid] != pilot_old_subset_results[aid]:
            regression_mismatches.append({
                "aid": aid, "old": old_only_results[aid], "pilot_old": pilot_old_subset_results[aid]
            })
    n_old_extracted = sum(1 for v in old_only_results.values() if v is not None)
    logger.info("old-only extracted (832 전수): %d", n_old_extracted)
    logger.info("regression mismatches: %d", len(regression_mismatches))

    # ─── Step 5: pilot full 추출 (old + P_NEW_1 + P_NEW_2) ───────────
    logger.info("--- Step 5: pilot full 추출 ---")
    pilot_results = {}  # aid -> (year, pattern_label, span, bio)
    for a in matched:
        aid = str(a["artist_id"])
        bio = a.get("bio", "") or ""
        py, plabel, span = pilot_extract_birth_year(bio)
        pilot_results[aid] = {
            "year": py,
            "pattern_label": plabel,
            "span": span,
            "bio": bio,
            "display_name": a.get("display_name", ""),
        }

    # 추가 추출 = pilot 만 (pattern_label in P_NEW_1 / P_NEW_2)
    added_artists = [
        {"aid": aid, **info}
        for aid, info in pilot_results.items()
        if info["pattern_label"] in ("P_NEW_1", "P_NEW_2")
    ]
    n_added_artists = len(added_artists)
    n_pilot_extracted = sum(1 for r in pilot_results.values() if r["year"] is not None)
    logger.info("pilot extracted (820 매칭 영역): %d", n_pilot_extracted)
    logger.info("added artists (P_NEW_1 + P_NEW_2): %d", n_added_artists)

    # 추가 추출 작가 의 6-field evidence record
    evidence_records = []
    for a in added_artists:
        evidence_records.append({
            "artist_id": a["aid"],
            "display_name": a["display_name"],
            "bio_full": a["bio"],
            "extracted_span": a["span"],
            "extracted_year": int(a["year"]) if a["year"] is not None else None,
            "pattern_label": a["pattern_label"],
            "manual_judgment": None,  # 사용자 입력 영역
            "judgment_reason": None,  # 사용자 입력 영역
        })

    # validity range check
    out_of_range = [
        e for e in evidence_records
        if e["extracted_year"] is not None
        and not (VALIDITY_MIN <= e["extracted_year"] <= VALIDITY_MAX)
    ]
    logger.info("validity range out: %d", len(out_of_range))

    # 회수율 증분 (보고값)
    # artist 단위
    increment_n_artist = n_added_artists
    increment_pct_artist = increment_n_artist / n_unique_artists * 100
    # artwork 단위 (added artists 의 작품 수)
    added_aids = set(a["aid"] for a in added_artists)
    artwork_added_n = int(df_saatchi["artist_slug"].astype(str).isin(added_aids).sum())
    increment_pct_artwork = artwork_added_n / len(df_saatchi) * 100

    logger.info(
        "coverage increment (보고값): artist=%d (+%.4f%%p) / artwork=%d (+%.4f%%p)",
        increment_n_artist, increment_pct_artist, artwork_added_n, increment_pct_artwork,
    )

    # ─── Step 6: post-run digest 검증 (fail-closed) ─────────────────
    logger.info("--- Step 6: post-run digest 검증 ---")
    post_prepare_sha = sha256_file(OPERATIONAL_PREPARE)
    post_saatchi_sha = sha256_file(OPERATIONAL_SAATCHI)
    post_prepare_diff = git_diff_lines(OPERATIONAL_PREPARE)
    post_saatchi_diff = git_diff_lines(OPERATIONAL_SAATCHI)

    if pre_prepare_sha != post_prepare_sha or pre_prepare_diff != post_prepare_diff:
        raise RuntimeError(
            f"FAIL-CLOSED: prepare_saatchi_dataset.py changed during pilot"
        )
    if pre_saatchi_sha != post_saatchi_sha or pre_saatchi_diff != post_saatchi_diff:
        raise RuntimeError(
            f"FAIL-CLOSED: saatchi_cleaned.parquet changed during pilot"
        )
    logger.info("운영 source 변경 X (fail-closed 통과)")

    # ─── Step 7: PASS / FAIL 판정 ─────────────────────────────────────
    # Reproducibility checks
    repro_checks = {
        "regression_free_832_artists": len(regression_mismatches) == 0,
        "validity_range_all_in_1920_2005": len(out_of_range) == 0,
        "operational_prepare_unchanged": (pre_prepare_sha == post_prepare_sha and pre_prepare_diff == 0 and post_prepare_diff == 0),
        "operational_saatchi_unchanged": (pre_saatchi_sha == post_saatchi_sha and pre_saatchi_diff == 0 and post_saatchi_diff == 0),
    }

    # Precision: PASS rule 은 사용자 검수 후 의 별도 cycle / 본 자동 실행 = 자동 PASS X
    # 본 단계 = evidence record 생성 만 / TP rate 판정 = 사용자 검수 후 보고서 단계
    repro_pass = all(repro_checks.values())

    result = {
        "verdict_reproducibility": "PASS" if repro_pass else "FAIL",
        "verdict_precision_pending_manual_review": True,
        "reproducibility_checks": repro_checks,
        "regression_mismatches": regression_mismatches,
        "validity_range_out": out_of_range,
        "coverage_increment": {
            "denominator_artists": n_unique_artists,
            "old_extracted_n": n_old_extracted,
            "new_extracted_n_pilot_full": n_pilot_extracted,
            "added_artists_n": n_added_artists,
            "increment_pct_artist": round(increment_pct_artist, 4),
            "denominator_artworks": len(df_saatchi),
            "added_artwork_n": artwork_added_n,
            "increment_pct_artwork": round(increment_pct_artwork, 4),
        },
        "sample_frame": {
            "scope": "운영 saatchi 832 unique artists / saatchi_kr_artists.json 매칭 820",
            "operational_artists": n_unique_artists,
            "json_matched_artists": len(matched),
        },
        "pre_digest": {
            "prepare_saatchi_dataset_py_sha256": pre_prepare_sha,
            "prepare_saatchi_dataset_py_git_diff_lines": pre_prepare_diff,
            "saatchi_cleaned_parquet_sha256": pre_saatchi_sha,
            "saatchi_cleaned_parquet_git_diff_lines": pre_saatchi_diff,
        },
        "post_digest": {
            "prepare_saatchi_dataset_py_sha256": post_prepare_sha,
            "prepare_saatchi_dataset_py_git_diff_lines": post_prepare_diff,
            "saatchi_cleaned_parquet_sha256": post_saatchi_sha,
            "saatchi_cleaned_parquet_git_diff_lines": post_saatchi_diff,
        },
        "decision_binding": {
            "is_decision_binding": False,
            "scope": "pilot 측정 reproducibility 만",
            "not_efficacy_pass": True,
            "not_adoption_pass": True,
            "not_production_candidate": True,
            "operational_code_unchanged": True,
            "operational_data_unchanged": True,
        },
    }

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    EVIDENCE_OUT.write_text(json.dumps(evidence_records, indent=2, ensure_ascii=False))
    logger.info("Wrote %s", SUMMARY_OUT)
    logger.info("Wrote %s", EVIDENCE_OUT)
    logger.info("VERDICT (reproducibility): %s", result["verdict_reproducibility"])
    logger.info("Precision verdict pending manual review of %d evidence records",
                len(evidence_records))
    return result


if __name__ == "__main__":
    main()
