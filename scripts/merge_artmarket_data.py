"""k-artmarket 신규 데이터 + 기존 K-Auction 데이터 통합.

data_schema.py의 통합 스키마를 사용하여 다중 출처 데이터를 통합한다.

Usage:
    PYTHONPATH=src python3 scripts/merge_artmarket_data.py
"""
from __future__ import annotations

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OLD_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
NEW_PATH = ROOT / "data" / "k-artmarket 1차 데이터 정제 - k_artmarket_works.csv"
OUTPUT_PATH = ROOT / "data" / "k-auction-works-merged.csv"


def main() -> None:
    """메인: data_schema.py를 사용한 통합 파이프라인."""
    from visionai.price_engine.preprocessing.data_schema import merge_and_cleanse

    merged = merge_and_cleanse(OLD_PATH, NEW_PATH, OUTPUT_PATH)
    logger.info("=" * 60)
    logger.info("Final: %d rows", len(merged))
    if "source" in merged.columns:
        logger.info("Sources: %s", merged["source"].value_counts().to_dict())
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
