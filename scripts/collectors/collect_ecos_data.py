"""한국은행 ECOS API 실수집 — KOSPI, USD/KRW 환율, CPI.

Usage:
    PYTHONPATH=src python3 scripts/collectors/collect_ecos_data.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = ROOT / "data" / "ecos_macro.csv"

ECOS_API_KEY = "WTIA71ADA3MWF93MQB4Q"
ECOS_BASE = "https://ecos.bok.or.kr/api/StatisticSearch"


def fetch_ecos(
    stat_code: str, item_code1: str, cycle: str,
    start: str, end: str,
) -> pd.DataFrame:
    """ECOS API 조회."""
    url = (
        f"{ECOS_BASE}/{ECOS_API_KEY}/json/kr/1/10000"
        f"/{stat_code}/{cycle}/{start}/{end}/{item_code1}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "StatisticSearch" not in data:
        logger.warning("No data for %s: %s", stat_code, data.get("RESULT", {}))
        return pd.DataFrame()

    rows = data["StatisticSearch"]["row"]
    return pd.DataFrame([{"time": r["TIME"], "value": r["DATA_VALUE"]} for r in rows])


def main() -> None:
    """ECOS 매크로 지표 수집."""
    logger.info("=== ECOS 매크로 지표 수집 ===")

    # 1. KOSPI (일별 → 월 평균)
    logger.info("1. KOSPI 일별...")
    kospi = fetch_ecos("802Y001", "0001000", "D", "20130101", "20260329")
    if not kospi.empty:
        kospi["value"] = pd.to_numeric(kospi["value"], errors="coerce")
        kospi["year_month"] = kospi["time"].str[:6]
        kospi_monthly = kospi.groupby("year_month")["value"].mean().reset_index()
        kospi_monthly.columns = ["year_month", "kospi_close"]
        logger.info("  KOSPI: %d months", len(kospi_monthly))
    else:
        kospi_monthly = pd.DataFrame(columns=["year_month", "kospi_close"])

    # 2. USD/KRW 환율 (일별 → 월 평균)
    logger.info("2. USD/KRW 환율 일별...")
    fx = fetch_ecos("731Y001", "0000001", "D", "20130101", "20260329")
    if not fx.empty:
        fx["value"] = pd.to_numeric(fx["value"], errors="coerce")
        fx["year_month"] = fx["time"].str[:6]
        fx_monthly = fx.groupby("year_month")["value"].mean().reset_index()
        fx_monthly.columns = ["year_month", "usd_krw"]
        logger.info("  FX: %d months", len(fx_monthly))
    else:
        fx_monthly = pd.DataFrame(columns=["year_month", "usd_krw"])

    # 3. CPI (월별)
    logger.info("3. CPI 월별...")
    cpi = fetch_ecos("901Y009", "0", "M", "201301", "202603")
    if not cpi.empty:
        cpi["value"] = pd.to_numeric(cpi["value"], errors="coerce")
        cpi = cpi.rename(columns={"time": "year_month", "value": "cpi"})
        logger.info("  CPI: %d months", len(cpi))
    else:
        cpi = pd.DataFrame(columns=["year_month", "cpi"])

    # 4. 병합
    merged = kospi_monthly
    if not fx_monthly.empty:
        merged = merged.merge(fx_monthly, on="year_month", how="outer")
    if not cpi.empty:
        merged = merged.merge(cpi[["year_month", "cpi"]], on="year_month", how="outer")

    merged = merged.sort_values("year_month").reset_index(drop=True)

    # 5. 기존 macro_monthly.csv 갱신
    macro_path = ROOT / "data" / "macro_monthly.csv"
    if macro_path.exists():
        existing = pd.read_csv(macro_path, dtype={"year_month": str})
        for col in ["kospi_close", "usd_krw", "cpi"]:
            if col in merged.columns:
                mapping = dict(zip(merged["year_month"], merged[col], strict=False))
                existing[col] = existing["year_month"].map(mapping)
                filled = existing[col].notna().sum()
                logger.info("  Updated %s: %d/%d months filled", col, filled, len(existing))
        existing.to_csv(macro_path, index=False)
        logger.info("Updated %s", macro_path)

    # 6. 별도 저장
    merged.to_csv(OUTPUT_PATH, index=False)
    logger.info("Saved to %s (%d rows)", OUTPUT_PATH, len(merged))

    # 요약
    logger.info("=== 수집 요약 ===")
    logger.info("KOSPI: %d months", len(kospi_monthly))
    logger.info("USD/KRW: %d months", len(fx_monthly))
    logger.info("CPI: %d months", len(cpi))


if __name__ == "__main__":
    main()
