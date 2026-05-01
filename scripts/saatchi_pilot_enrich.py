"""v3.4-2 step 3 pilot enrichment: 1,000 sample fetch + summary.

Usage:
    PYTHONPATH=scripts python3 scripts/saatchi_pilot_enrich.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from saatchi_detail_enricher import fetch_and_parse_saatchi_detail

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results" / "v3_diagnostics"
SAMPLE_PATH = OUT_DIR / "saatchi_pilot_sample_urls.json"
RAW_OUT_PATH = OUT_DIR / "saatchi_pilot_enrichment_raw.jsonl"  # incremental (재시작 안전)
SUMMARY_OUT_PATH = OUT_DIR / "saatchi_pilot_enrichment.json"
RATE_LIMIT_SEC = 0.6


def main() -> None:
    sample_data = json.loads(SAMPLE_PATH.read_text())
    samples = sample_data["samples"]
    logger.info("pilot sample n=%d", len(samples))

    # 재시작 안전: 이미 fetch 된 url skip
    fetched_urls: set[str] = set()
    if RAW_OUT_PATH.exists():
        for line in RAW_OUT_PATH.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                fetched_urls.add(rec["url"])
        logger.info("기존 fetched: %d (skip)", len(fetched_urls))

    started_at = time.time()
    n_fetched = 0
    with RAW_OUT_PATH.open("a") as f:
        for i, s in enumerate(samples):
            url = s["artwork_url"]
            if url in fetched_urls:
                continue
            result = fetch_and_parse_saatchi_detail(url, price_krw=s["price_krw"])
            rec = {
                **result.to_dict(),
                "fetched_at": datetime.now(UTC).isoformat(),
                "sample_meta": {
                    "artist_slug": s["artist_slug"],
                    "price_krw": s["price_krw"],
                    "medium_cat": s["medium_cat"],
                    "price_band": s["price_band"],
                    "work_count_bucket": s["work_count_bucket"],
                    "warm": s["warm"],
                    "target_reason": s["target_reason"],
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            n_fetched += 1
            if (i + 1) % 50 == 0:
                elapsed = time.time() - started_at
                rate = n_fetched / elapsed if elapsed > 0 else 0
                logger.info(
                    "[%d/%d] fetched=%d elapsed=%.1fs rate=%.2f req/s",
                    i + 1,
                    len(samples),
                    n_fetched,
                    elapsed,
                    rate,
                )
            time.sleep(RATE_LIMIT_SEC)

    # 모든 결과 로드 (이번 + 기존)
    all_results = []
    for line in RAW_OUT_PATH.read_text().splitlines():
        if line.strip():
            all_results.append(json.loads(line))

    # batch summary
    n = len(all_results)
    fetch_counter = Counter(r["fetch_status"] for r in all_results)
    src_counter = Counter(r["extraction_source"] for r in all_results)
    n_year_resolved = sum(1 for r in all_results if r["year_created"])
    n_year_unresolved = sum(1 for r in all_results if r["extraction_source"] == "unresolved")
    n_short = sum(1 for r in all_results if r["fetch_status"] == "short_response")
    n_blocked = sum(1 for r in all_results if r["fetch_status"] == "blocked")
    n_price_zero = sum(1 for r in all_results if r["price_zero_flag"])
    n_price_zero_sold_missing = sum(
        1 for r in all_results if "price_zero_isSoldOut_missing" in r["parse_warnings"]
    )
    n_sold_true = sum(1 for r in all_results if r.get("is_sold_out") is True)
    n_sold_false = sum(1 for r in all_results if r.get("is_sold_out") is False)
    n_sold_missing = sum(1 for r in all_results if r.get("is_sold_out") is None)

    # year 분포
    years = [r["year_created"] for r in all_results if r["year_created"]]
    year_summary = (
        {
            "min": min(years),
            "p10": int(sorted(years)[len(years) // 10]),
            "median": int(sorted(years)[len(years) // 2]),
            "p90": int(sorted(years)[int(len(years) * 0.9)]),
            "max": max(years),
        }
        if years
        else {}
    )

    # warning frequency
    warn_counter: Counter = Counter()
    for r in all_results:
        for w in r.get("parse_warnings", []):
            warn_counter[w] += 1

    # warm/cold breakdown
    warm_n = sum(1 for r in all_results if r["sample_meta"]["warm"])
    fill_rate_overall = n_year_resolved / n
    fill_rate_warm = sum(
        1 for r in all_results if r["sample_meta"]["warm"] and r["year_created"]
    ) / max(warm_n, 1)
    fill_rate_cold = sum(
        1 for r in all_results if not r["sample_meta"]["warm"] and r["year_created"]
    ) / max(n - warm_n, 1)

    # target_reason 별 fill rate
    by_reason: dict[str, dict] = {}
    for reason in {
        "cold_artist",
        "price_zero",
        "low_work_count_warm",
        "fill_diversity",
        "stratified_random",
        "stratified_fill",
    }:
        rows = [r for r in all_results if r["sample_meta"]["target_reason"] == reason]
        if not rows:
            continue
        by_reason[reason] = {
            "n": len(rows),
            "fill_rate_year": sum(1 for r in rows if r["year_created"]) / len(rows),
            "n_blocked": sum(1 for r in rows if r["fetch_status"] == "blocked"),
            "n_price_zero": sum(1 for r in rows if r["price_zero_flag"]),
        }

    summary = {
        "config": {
            "scope": "v3.4-2 step 3 pilot enrichment (650 target + 350 stratified random)",
            "n_total": n,
            "rate_limit_sec": RATE_LIMIT_SEC,
            "raw_jsonl_path": str(RAW_OUT_PATH.relative_to(ROOT)),
        },
        "fetch_status_distribution": dict(fetch_counter),
        "extraction_source_distribution": dict(src_counter),
        "year_created": {
            "resolved": n_year_resolved,
            "unresolved": n_year_unresolved,
            "fill_rate_overall": fill_rate_overall,
            "fill_rate_warm": fill_rate_warm,
            "fill_rate_cold": fill_rate_cold,
            "year_summary": year_summary,
        },
        "is_sold_out": {
            "true": n_sold_true,
            "false": n_sold_false,
            "missing": n_sold_missing,
        },
        "diagnostics_counts": {
            "n_short_response": n_short,
            "n_blocked": n_blocked,
            "n_price_zero_flag": n_price_zero,
            "n_price_zero_isSoldOut_missing": n_price_zero_sold_missing,
            "warning_distribution": dict(warn_counter),
        },
        "fill_rate_by_target_reason": by_reason,
        "interpretation": (
            "코덱스 권장 batch summary: fetch_status / extraction_source distribution / "
            "year unresolved / short_response / price_zero_flag / price_zero_isSoldOut_missing. "
            "hash drift rate 는 step 1 baseline 부재로 본 pilot 의 hash 만 저장 (raw jsonl), "
            "향후 monitor 시 baseline."
        ),
    }
    SUMMARY_OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("summary 저장: %s", SUMMARY_OUT_PATH)

    print("\n" + "=" * 100)
    print("v3.4-2 step 3 pilot enrichment 결과")
    print("=" * 100)
    print(f"\n총 sample n={n}")
    print(f"fetch_status: {dict(fetch_counter)}")
    print(f"extraction_source: {dict(src_counter)}")
    print(f"year_created fill: {n_year_resolved}/{n} ({fill_rate_overall * 100:.1f}%)")
    print(f"  warm fill: {fill_rate_warm * 100:.1f}% / cold fill: {fill_rate_cold * 100:.1f}%")
    print(f"is_sold_out: true={n_sold_true} / false={n_sold_false} / missing={n_sold_missing}")
    print(f"price_zero_flag: {n_price_zero}")
    print(f"warnings: {dict(warn_counter)}")
    print(f"year 분포: {year_summary}")
    print("\nFill rate by target_reason:")
    for reason, stats in by_reason.items():
        print(
            f"  {reason:<25} n={stats['n']:>4} fill={stats['fill_rate_year'] * 100:>5.1f}% "
            f"blocked={stats['n_blocked']} price_zero={stats['n_price_zero']}"
        )
    print(f"\n저장: {SUMMARY_OUT_PATH}")


if __name__ == "__main__":
    main()
