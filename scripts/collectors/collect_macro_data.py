"""Phase 5 Sprint 1 — 매크로 지표 수집.

K-Auction 내부 회차별 통계 + 공공 API(ECOS/KOSIS) 매크로 지표.
공공 API 키가 없으면 내부 통계만 생성.

Usage:
    PYTHONPATH=src python3 scripts/collectors/collect_macro_data.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT / "data" / "k-auction-works-20260325.csv"
OUTPUT_PATH = ROOT / "data" / "macro_monthly.csv"
SESSION_OUTPUT_PATH = ROOT / "data" / "macro_session.csv"


def compute_kauction_session_stats(df: pd.DataFrame) -> pd.DataFrame:
    """K-Auction 회차별 통계 계산.

    Returns:
        DataFrame with columns: session, year_month, sold_rate, avg_price, total_lots.
    """
    rows = []
    for sess in sorted(df["회차"].unique()):
        sess_df = df[df["회차"] == sess]
        total = len(sess_df)
        sold = pd.to_numeric(sess_df["낙찰가"], errors="coerce")
        sold_positive = sold[sold > 0]
        sold_count = len(sold_positive)
        sold_rate = sold_count / total if total > 0 else 0
        avg_price = float(sold_positive.mean()) if sold_count > 0 else 0

        # 회차 → 대략적 year_month 매핑 (K-Auction 2013~2026, ~486 회차)
        # 연 ~37회차 기준으로 근사
        base_year = 2013
        sessions_per_year = 37
        approx_year = base_year + int(sess) // sessions_per_year
        month_idx = (int(sess) % sessions_per_year) * 12 // sessions_per_year + 1
        approx_month = max(1, min(12, month_idx))
        ym = f"{approx_year}{approx_month:02d}"

        rows.append({
            "session": int(sess),
            "year_month": ym,
            "kauction_sold_rate": round(sold_rate, 4),
            "kauction_avg_price": round(avg_price),
            "kauction_total_lots": total,
        })
    return pd.DataFrame(rows)


def build_macro_monthly(kauction_stats: pd.DataFrame) -> pd.DataFrame:
    """매크로 월별 지표 DataFrame 생성.

    K-Auction 내부 통계 기반. 공공 API 데이터는 향후 추가.
    현재: 회차별 통계를 월별로 집계 + 3개월 이동평균.

    Returns:
        DataFrame: year_month, kospi_close, usd_krw, apartment_index, cpi,
                   kauction_sold_rate_prev, kauction_avg_price_prev,
                   kauction_avg_price_mom_3m.
    """
    # 월별 집계
    monthly = kauction_stats.groupby("year_month").agg(
        kauction_sold_rate=("kauction_sold_rate", "mean"),
        kauction_avg_price=("kauction_avg_price", "mean"),
        kauction_total_lots=("kauction_total_lots", "sum"),
    ).reset_index()

    monthly = monthly.sort_values("year_month").reset_index(drop=True)

    # 3개월 이동평균
    monthly["kauction_avg_price_mom_3m"] = (
        monthly["kauction_avg_price"].rolling(3, min_periods=1).mean()
    )

    # 매크로 지표 placeholder (공공 API 연동 시 교체)
    # 현재는 NaN으로 두고 피처 모듈에서 forward-fill 처리
    monthly["kospi_close"] = np.nan
    monthly["usd_krw"] = np.nan
    monthly["apartment_index"] = np.nan
    monthly["cpi"] = np.nan

    return monthly


def main() -> None:
    """매크로 지표 생성 실행."""
    logger.info("=== 매크로 지표 수집 ===")

    logger.info("Loading K-Auction data: %s", DATA_PATH)
    df = pd.read_csv(DATA_PATH, low_memory=False)
    logger.info("Loaded %d rows", len(df))

    # 회차별 통계
    kauction_stats = compute_kauction_session_stats(df)
    logger.info("Session stats: %d sessions", len(kauction_stats))

    # 월별 매크로
    macro = build_macro_monthly(kauction_stats)
    logger.info("Monthly macro: %d months", len(macro))

    # 저장 — 월별 + 회차별 양쪽 모두
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    macro.to_csv(OUTPUT_PATH, index=False)
    logger.info("Saved monthly to %s", OUTPUT_PATH)

    kauction_stats.to_csv(SESSION_OUTPUT_PATH, index=False)
    logger.info("Saved session-level to %s", SESSION_OUTPUT_PATH)


if __name__ == "__main__":
    main()
