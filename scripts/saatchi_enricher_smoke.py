"""v3.4-2 step 2 smoke verification: 새 parser 로 step 1 의 26 sample 재실행.

목적:
- step 1 의 raw 결과 (saatchi_year_created_strat_validation.json) 의 year_created /
  isSoldOut / isReserved / availability 가 새 parser 와 동일한지 검증
- 모든 26 sample 의 extraction_source 가 'html_year_created' 인지 확인

Usage:
    PYTHONPATH=scripts python3 scripts/saatchi_enricher_smoke.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from saatchi_detail_enricher import fetch_and_parse_saatchi_detail

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STRAT_RESULTS_PATH = (
    ROOT / "model_test_results" / "v3_diagnostics" / "saatchi_year_created_strat_validation.json"
)
SMOKE_OUT_PATH = ROOT / "model_test_results" / "v3_diagnostics" / "saatchi_enricher_smoke.json"
RATE_LIMIT_SEC = 0.6


def main() -> None:
    if not STRAT_RESULTS_PATH.exists():
        raise SystemExit(
            f"step 1 raw results 가 없습니다: {STRAT_RESULTS_PATH}\n"
            "step 1 (v3.4-2 step 1) 먼저 실행하세요."
        )

    step1_results = json.loads(STRAT_RESULTS_PATH.read_text())
    logger.info("step 1 sample 수: %d", len(step1_results))

    # step 1 raw json 의 url_short 는 partial. saatchi_kr_artworks.json 에서 full URL 복구
    artworks = json.loads((ROOT / "docs" / "saatchi_kr_artworks.json").read_text())
    arts = artworks if isinstance(artworks, list) else artworks.get("artworks", [])
    by_short = {}
    for a in arts:
        url = str(a.get("artwork_url", ""))
        if "/art/" in url:
            short = url.split("/art/", 1)[1].split("/")[0]
            by_short[short] = (url, a.get("price_krw", 0))

    new_results = []
    mismatches = []

    for i, prev in enumerate(step1_results):
        short = prev["url_short"]
        url, price = by_short.get(short, (None, 0))
        if not url:
            logger.warning("URL not found for url_short=%s", short)
            continue
        result = fetch_and_parse_saatchi_detail(url, price_krw=price)

        # step 1 결과와 비교
        prev_year = prev.get("year_created")
        prev_year_int = int(prev_year) if prev_year is not None else None
        prev_sold = prev.get("isSoldOut")
        prev_sold_bool = None if prev_sold is None else (prev_sold == "true")

        match_year = result.year_created == prev_year_int
        match_sold = result.is_sold_out == prev_sold_bool
        if not (match_year and match_sold):
            mismatches.append(
                {
                    "idx": i,
                    "url_short": short,
                    "step1_year": prev_year_int,
                    "new_year": result.year_created,
                    "step1_sold": prev_sold_bool,
                    "new_sold": result.is_sold_out,
                }
            )

        new_results.append(
            {
                "idx": i,
                "stratum": prev.get("stratum"),
                "price_krw": price,
                "url_short": short,
                **result.to_dict(),
            }
        )
        logger.info(
            "[%2d/%d] %-22s year=%s src=%s sold=%s match_year=%s match_sold=%s",
            i + 1,
            len(step1_results),
            prev.get("stratum"),
            result.year_created,
            result.extraction_source,
            result.is_sold_out,
            match_year,
            match_sold,
        )
        time.sleep(RATE_LIMIT_SEC)

    # summary
    n = len(new_results)
    n_year = sum(1 for r in new_results if r["year_created"])
    src_counter = Counter(r["extraction_source"] for r in new_results)
    fetch_counter = Counter(r["fetch_status"] for r in new_results)
    n_warnings = sum(1 for r in new_results if r["parse_warnings"])
    n_price_zero = sum(1 for r in new_results if r["price_zero_flag"])

    summary = {
        "config": {
            "scope": "v3.4-2 step 2 smoke verification — 새 parser 로 step 1 26 sample 재실행",
            "step1_path": str(STRAT_RESULTS_PATH.relative_to(ROOT)),
            "rate_limit_sec": RATE_LIMIT_SEC,
        },
        "totals": {
            "n_sample": n,
            "year_created_extracted": n_year,
            "extraction_source_distribution": dict(src_counter),
            "fetch_status_distribution": dict(fetch_counter),
            "n_with_parse_warnings": n_warnings,
            "n_price_zero_flag": n_price_zero,
            "n_mismatches_vs_step1": len(mismatches),
        },
        "mismatches": mismatches,
        "results": new_results,
    }

    SMOKE_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SMOKE_OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("smoke 결과 저장: %s", SMOKE_OUT_PATH)

    print("\n" + "=" * 100)
    print("v3.4-2 step 2 smoke verification")
    print("=" * 100)
    print(f"\nsample n={n}")
    print(f"Year Created extracted: {n_year}/{n}")
    print(f"extraction_source: {dict(src_counter)}")
    print(f"fetch_status: {dict(fetch_counter)}")
    print(f"parse_warnings 있는 sample: {n_warnings}")
    print(f"price_zero_flag 작품: {n_price_zero}")
    print(f"step1 vs new mismatches: {len(mismatches)}")
    if mismatches:
        print("Mismatches:")
        for m in mismatches:
            print(f"  {m}")
    print(f"\n저장: {SMOKE_OUT_PATH}")


if __name__ == "__main__":
    main()
