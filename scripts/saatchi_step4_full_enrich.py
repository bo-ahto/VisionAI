"""v3.4-2 step 4: 학습 데이터 saatchi 21,087 전수 enrichment + retry 2-pass.

코덱스 v3.4-2 step 4 권장:
- cohort: 학습 데이터 saatchi 21,087 (production-relevant)
- run mode: 1차 fetch + failure-only 2-pass retry
- retry 대상: 5xx / network_error / timeout (404 non-retry)
- retry pass 1: 2-5s 랜덤 backoff
- retry pass 2: 5-15s 랜덤 backoff
- append-safe jsonl (재시작 안전)
- success criterion: 최종 unresolved 를 residual transient bucket 으로 고정

비용 추정:
- 1차: 21,087 × 0.6 sec ≈ 7 hr
- retry pass 1+2: ~10-30 min (실패건 ~80~200건 × 5-15s)
- 총 ~7-8 hr

Usage:
    PYTHONPATH=scripts python3 scripts/saatchi_step4_full_enrich.py
    # 또는 chunk 단위:
    PYTHONPATH=scripts python3 scripts/saatchi_step4_full_enrich.py --start 0 --end 1000
    # nohup 으로 detached:
    nohup env PYTHONPATH=scripts python3 -u scripts/saatchi_step4_full_enrich.py \
        > /tmp/step4.log 2>&1 &

Note: pilot (step 3) 의 saatchi_pilot_enrichment_raw.jsonl 은 별도 file. 본 step 4 는
새 jsonl (saatchi_step4_full_enrichment_raw.jsonl) 사용 — pilot 결과 와 분리.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from saatchi_detail_enricher import fetch_and_parse_saatchi_detail
from train_primary_market_v3_filtered import load_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results" / "v3_diagnostics"
RAW_OUT_PATH = OUT_DIR / "saatchi_step4_full_enrichment_raw.jsonl"
SUMMARY_OUT_PATH = OUT_DIR / "saatchi_step4_full_enrichment.json"

RATE_LIMIT_SEC = 0.6
RETRYABLE_STATUSES = {"5xx", "network_error", "timeout"}
RNG_SEED = 42


def _load_url_list() -> list[dict]:
    """학습 데이터 saatchi 21,087 의 URL + price + artist_slug list 반환."""
    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    saatchi = df[df["source"] == "saatchi"].copy().reset_index(drop=True)
    return [
        {
            "artwork_url": r["artwork_url"],
            "artist_slug": str(r["artist_slug"]),
            "price_krw": float(r["price_krw"]),
        }
        for _, r in saatchi.iterrows()
    ]


def _load_existing_results() -> dict[str, dict]:
    """기존 jsonl 의 url → 가장 최근 result 매핑 (재시작 안전)."""
    if not RAW_OUT_PATH.exists():
        return {}
    by_url: dict[str, dict] = {}
    for line in RAW_OUT_PATH.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            by_url[rec["url"]] = rec  # 마지막 entry 가 가장 최근 (append order)
    return by_url


def _append_result(rec: dict) -> None:
    with RAW_OUT_PATH.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def _enrich_one(url: str, price: float | None) -> dict:
    result = fetch_and_parse_saatchi_detail(url, price_krw=price)
    return {
        **result.to_dict(),
        "fetched_at": datetime.now(UTC).isoformat(),
        "sample_meta": {"price_krw": price},
    }


def _main_pass(samples: list[dict], start: int, end: int | None) -> None:
    """1차 본수집 — RATE_LIMIT_SEC 고정 간격."""
    if end is None:
        end = len(samples)
    end = min(end, len(samples))
    existing = _load_existing_results()
    fetched_urls = {url for url, rec in existing.items() if rec["fetch_status"] == "ok"}
    logger.info(
        "[main pass] start=%d end=%d total=%d 기존 ok=%d (skip)",
        start,
        end,
        len(samples),
        len(fetched_urls),
    )
    started_at = time.time()
    n_fetched = 0
    n_skipped = 0
    for i in range(start, end):
        s = samples[i]
        url = s["artwork_url"]
        if url in fetched_urls:
            n_skipped += 1
            continue
        rec = _enrich_one(url, s["price_krw"])
        rec["sample_meta"] = {
            "artist_slug": s["artist_slug"],
            "price_krw": s["price_krw"],
            "pass": "main",
        }
        _append_result(rec)
        n_fetched += 1
        if n_fetched % 100 == 0:
            elapsed = time.time() - started_at
            rate = n_fetched / elapsed if elapsed > 0 else 0
            eta_sec = (end - start - n_skipped - n_fetched) / max(rate, 0.01)
            logger.info(
                "[main %d/%d] fetched=%d skipped=%d elapsed=%.0fs rate=%.2f req/s ETA %.0f min",
                i + 1,
                end,
                n_fetched,
                n_skipped,
                elapsed,
                rate,
                eta_sec / 60,
            )
        time.sleep(RATE_LIMIT_SEC)
    logger.info("[main pass] done: fetched=%d skipped=%d", n_fetched, n_skipped)


def _retry_pass(
    samples: list[dict],
    pass_label: str,
    backoff_min: float,
    backoff_max: float,
    rng: random.Random,
) -> int:
    """failure-only retry — 현재 fetch_status 가 RETRYABLE 인 url 만.

    Returns:
        실패 → 성공 으로 회복된 건수
    """
    existing = _load_existing_results()
    failed_urls = [
        url for url, rec in existing.items() if rec["fetch_status"] in RETRYABLE_STATUSES
    ]
    by_meta = {s["artwork_url"]: s for s in samples}
    target_set = [url for url in failed_urls if url in by_meta]
    logger.info(
        "[%s] retryable urls: %d (failed total=%d, in-scope=%d)",
        pass_label,
        len(target_set),
        len(failed_urls),
        len(target_set),
    )
    if not target_set:
        return 0

    n_recovered = 0
    for i, url in enumerate(target_set):
        s = by_meta[url]
        rec = _enrich_one(url, s["price_krw"])
        rec["sample_meta"] = {
            "artist_slug": s["artist_slug"],
            "price_krw": s["price_krw"],
            "pass": pass_label,
        }
        _append_result(rec)
        if rec["fetch_status"] == "ok":
            n_recovered += 1
        backoff = rng.uniform(backoff_min, backoff_max)
        logger.info(
            "[%s %d/%d] %s -> %s (backoff %.1fs)",
            pass_label,
            i + 1,
            len(target_set),
            rec.get("fetch_status"),
            "OK" if rec["fetch_status"] == "ok" else "FAIL",
            backoff,
        )
        time.sleep(backoff)
    logger.info("[%s] recovered=%d / total=%d", pass_label, n_recovered, len(target_set))
    return n_recovered


def _generate_summary(samples: list[dict]) -> None:
    existing = _load_existing_results()
    n_total = len(samples)
    by_url = {s["artwork_url"]: s for s in samples}

    fetch_counter: Counter = Counter()
    src_counter: Counter = Counter()
    n_year = 0
    n_unresolved = 0
    n_blocked = 0
    n_short = 0
    n_price_zero = 0
    n_sold_true = 0
    n_sold_false = 0
    n_sold_missing = 0
    warn_counter: Counter = Counter()
    not_attempted: list[str] = []
    years: list[int] = []

    for s in samples:
        url = s["artwork_url"]
        rec = existing.get(url)
        if rec is None:
            not_attempted.append(url)
            continue
        fetch_counter[rec["fetch_status"]] += 1
        src_counter[rec["extraction_source"]] += 1
        if rec.get("year_created"):
            n_year += 1
            years.append(int(rec["year_created"]))
        if rec["extraction_source"] == "unresolved":
            n_unresolved += 1
        if rec["fetch_status"] == "blocked":
            n_blocked += 1
        if rec["fetch_status"] == "short_response":
            n_short += 1
        if rec.get("price_zero_flag"):
            n_price_zero += 1
        if rec.get("is_sold_out") is True:
            n_sold_true += 1
        elif rec.get("is_sold_out") is False:
            n_sold_false += 1
        else:
            n_sold_missing += 1
        for w in rec.get("parse_warnings", []):
            warn_counter[w] += 1

    year_summary = {}
    if years:
        years_sorted = sorted(years)
        year_summary = {
            "min": years_sorted[0],
            "p10": years_sorted[len(years_sorted) // 10],
            "median": years_sorted[len(years_sorted) // 2],
            "p90": years_sorted[int(len(years_sorted) * 0.9)],
            "max": years_sorted[-1],
        }

    summary = {
        "config": {
            "scope": "v3.4-2 step 4 full saatchi enrichment (21,087 training-relevant)",
            "n_total": n_total,
            "rate_limit_sec": RATE_LIMIT_SEC,
            "raw_jsonl_path": str(RAW_OUT_PATH.relative_to(ROOT)),
            "retry_policy": {
                "retryable": list(RETRYABLE_STATUSES),
                "pass_1_backoff_sec": [2, 5],
                "pass_2_backoff_sec": [5, 15],
            },
        },
        "totals": {
            "n_attempted": n_total - len(not_attempted),
            "n_not_attempted": len(not_attempted),
            "year_created_resolved": n_year,
            "year_created_unresolved": n_unresolved,
            "fill_rate_year": n_year / max(n_total, 1),
        },
        "fetch_status_distribution": dict(fetch_counter),
        "extraction_source_distribution": dict(src_counter),
        "is_sold_out": {"true": n_sold_true, "false": n_sold_false, "missing": n_sold_missing},
        "diagnostics_counts": {
            "n_short_response": n_short,
            "n_blocked": n_blocked,
            "n_price_zero_flag": n_price_zero,
            "warning_distribution": dict(warn_counter),
        },
        "year_distribution": year_summary,
        "interpretation": (
            "최종 unresolved 는 residual transient bucket. retry 2-pass 후에도 실패한 url 은 "
            "fetch failure 영구 케이스 — step 5 ablation 에서는 has_year_made flag 로 분리."
        ),
    }

    SUMMARY_OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("summary 저장: %s", SUMMARY_OUT_PATH)
    print("\n" + "=" * 100)
    print("v3.4-2 step 4 full enrichment summary")
    print("=" * 100)
    print(f"n_total={n_total} attempted={n_total - len(not_attempted)}")
    print(f"year_created fill: {n_year}/{n_total} ({n_year / max(n_total, 1) * 100:.2f}%)")
    print(f"fetch_status: {dict(fetch_counter)}")
    print(f"extraction_source: {dict(src_counter)}")
    print(f"is_sold_out: true={n_sold_true} false={n_sold_false} missing={n_sold_missing}")
    print(f"warnings: {dict(warn_counter)}")
    print(f"year 분포: {year_summary}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0, help="main pass 시작 idx (chunk 분할 용)")
    parser.add_argument("--end", type=int, default=None, help="main pass 끝 idx (None=전체)")
    parser.add_argument(
        "--skip-main", action="store_true", help="main pass 건너뛰고 retry 만 실행"
    )
    parser.add_argument("--skip-retry", action="store_true", help="main pass 만, retry 건너뛰기")
    parser.add_argument("--summary-only", action="store_true", help="summary 만 재생성")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = _load_url_list()
    logger.info("training-relevant saatchi URL list: %d", len(samples))

    if args.summary_only:
        _generate_summary(samples)
        return

    rng = random.Random(RNG_SEED)

    if not args.skip_main:
        _main_pass(samples, args.start, args.end)

    if not args.skip_retry:
        # 코덱스 권장: pass 1 = 2-5s, pass 2 = 5-15s backoff
        n_recovered_1 = _retry_pass(samples, "retry_1", 2.0, 5.0, rng)
        n_recovered_2 = _retry_pass(samples, "retry_2", 5.0, 15.0, rng)
        logger.info(
            "retry 종료: pass1 recovered=%d, pass2 recovered=%d",
            n_recovered_1,
            n_recovered_2,
        )

    _generate_summary(samples)


if __name__ == "__main__":
    main()
