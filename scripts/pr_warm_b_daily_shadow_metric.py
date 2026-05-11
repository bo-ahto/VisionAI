"""PR-WARM-B Stage 3 daily shadow metric report.

Runbook: docs/pr_warm_b_stage_3_5_activation_runbook_20260511.md (§1.3)

Usage:
    python3 scripts/pr_warm_b_daily_shadow_metric.py --days 7

Output:
    Daily Δ_warm distribution + per-source breakdown for last N days.
    Compares primary (default v3_filtered_tuned) vs shadow (v3_filtered_tuned_b_warm).

Sign-off 기준 (R1 amendment / runbook §1.2):
- 7-day aggregate Δ_warm ≤ -0.8pp
- 5/7 daily medians Δ_warm ≤ -0.5pp
- no day Δ_warm > +0.3pp
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _connect_db():
    """DB connection — config via PRICE_LOG_DB_URL env var."""
    db_url = os.environ.get("PRICE_LOG_DB_URL")
    if not db_url:
        logger.error("PRICE_LOG_DB_URL env var 미설정 / 본 script은 predict_logs DB 필요")
        sys.exit(1)
    try:
        import psycopg2  # type: ignore
        return psycopg2.connect(db_url)
    except ImportError:
        logger.error("psycopg2 미설치 / pip install psycopg2-binary")
        sys.exit(1)


def _fetch_daily_metrics(conn, days: int) -> list[dict]:
    """Fetch daily shadow vs primary comparison."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            DATE(timestamp) AS day,
            COUNT(*) AS n_requests,
            AVG(ABS(price_krw - shadow_prediction_price_krw)) AS mean_abs_diff,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY price_krw - shadow_prediction_price_krw
            ) AS median_diff,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(price_krw - shadow_prediction_price_krw) /
                NULLIF(price_krw, 0) * 100
            ) AS median_pct_diff,
            COUNT(CASE WHEN is_warm_artist = true THEN 1 END) AS n_warm,
            COUNT(CASE WHEN is_warm_artist = false THEN 1 END) AS n_cold
        FROM predict_logs
        WHERE shadow_variant = 'v3_filtered_tuned_b_warm'
          AND timestamp >= NOW() - INTERVAL %s
          AND price_krw IS NOT NULL
          AND shadow_prediction_price_krw IS NOT NULL
        GROUP BY DATE(timestamp)
        ORDER BY day DESC;
        """,
        (f"{days} days",),
    )
    rows = cur.fetchall()
    cols = ("day", "n_requests", "mean_abs_diff", "median_diff",
            "median_pct_diff", "n_warm", "n_cold")
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _fetch_warm_subset_mdape(conn, days: int) -> list[dict]:
    """Fetch warm-only MdAPE per day for both primary and shadow."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            DATE(timestamp) AS day,
            COUNT(*) AS n_warm_requests,
            -- Primary MdAPE (warm-only / requires actual_price for ground truth)
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(price_krw - actual_price) / NULLIF(actual_price, 0) * 100
            ) AS primary_mdape_warm,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(shadow_prediction_price_krw - actual_price) /
                NULLIF(actual_price, 0) * 100
            ) AS shadow_mdape_warm
        FROM predict_logs
        WHERE shadow_variant = 'v3_filtered_tuned_b_warm'
          AND is_warm_artist = true
          AND timestamp >= NOW() - INTERVAL %s
          AND price_krw IS NOT NULL
          AND shadow_prediction_price_krw IS NOT NULL
          AND actual_price IS NOT NULL
        GROUP BY DATE(timestamp)
        ORDER BY day DESC;
        """,
        (f"{days} days",),
    )
    rows = cur.fetchall()
    cols = ("day", "n_warm_requests", "primary_mdape_warm", "shadow_mdape_warm")
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _evaluate_sign_off(daily_warm: list[dict]) -> dict:
    """Evaluate Stage 3 sign-off criteria (R1 amendment / runbook §1.2)."""
    if not daily_warm:
        return {
            "verdict": "NO_DATA",
            "reason": "No daily warm metrics available",
        }
    deltas = []
    for d in daily_warm:
        p = d.get("primary_mdape_warm")
        s = d.get("shadow_mdape_warm")
        if p is not None and s is not None:
            deltas.append(float(s) - float(p))
    if not deltas:
        return {
            "verdict": "NO_DATA",
            "reason": "No daily Δ_warm available (missing actual_price?)",
        }

    aggregate_mean = float(np.mean(deltas))
    days_pass = sum(1 for d in deltas if d <= -0.5)
    days_bad = sum(1 for d in deltas if d > 0.3)

    criteria = {
        "7day_aggregate_delta_warm": aggregate_mean,
        "days_with_delta_le_minus_0p5": days_pass,
        "days_with_delta_gt_plus_0p3": days_bad,
        "n_days": len(deltas),
    }

    # Sign-off (R1 amendment)
    ok_aggregate = aggregate_mean <= -0.8
    ok_majority = days_pass >= 5
    ok_no_bad_day = days_bad == 0

    if ok_aggregate and ok_majority and ok_no_bad_day:
        verdict = "PASS"
    elif aggregate_mean <= -0.3 and days_bad <= 1:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "FAIL"

    return {
        "verdict": verdict,
        "criteria": criteria,
        "sign_off_checks": {
            "aggregate_delta_warm_le_minus_0p8": ok_aggregate,
            "5_of_7_days_le_minus_0p5": ok_majority,
            "no_day_gt_plus_0p3": ok_no_bad_day,
        },
        "per_day_deltas": [round(d, 4) for d in deltas],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7,
                        help="Look-back window (default: 7 days / matches sign-off)")
    parser.add_argument("--output", type=Path,
                        default=Path("model_test_results/pr_warm_b_daily_shadow_report.json"))
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("PR-WARM-B Stage 3 daily shadow metric report")
    logger.info("Window: last %d days", args.days)
    logger.info("=" * 70)

    conn = _connect_db()
    try:
        daily_diff = _fetch_daily_metrics(conn, args.days)
        daily_warm = _fetch_warm_subset_mdape(conn, args.days)

        logger.info("Daily diff (primary vs shadow) — %d days", len(daily_diff))
        for d in daily_diff:
            logger.info("  %s | n=%d | median_pct_diff=%.3f%% | warm=%d / cold=%d",
                        d["day"], d["n_requests"],
                        d["median_pct_diff"] or 0.0,
                        d["n_warm"], d["n_cold"])

        logger.info("Daily MdAPE (warm subset) — %d days", len(daily_warm))
        for d in daily_warm:
            p = d.get("primary_mdape_warm") or 0.0
            s = d.get("shadow_mdape_warm") or 0.0
            delta = float(s) - float(p)
            marker = "✅" if delta <= -0.5 else ("⚠️" if delta <= 0.3 else "❌")
            logger.info("  %s | n_warm=%d | primary=%.3f%% | shadow=%.3f%% | Δ=%+.3f %s",
                        d["day"], d["n_warm_requests"], float(p), float(s), delta, marker)

        sign_off = _evaluate_sign_off(daily_warm)
        logger.info("=" * 60)
        logger.info("Sign-off verdict: %s", sign_off["verdict"])
        for k, v in sign_off.get("sign_off_checks", {}).items():
            logger.info("  %s: %s", k, "✅" if v else "❌")
        logger.info("=" * 60)

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "window_days": args.days,
            "daily_diff": [
                {**d, "day": str(d["day"]),
                 "mean_abs_diff": float(d["mean_abs_diff"]) if d["mean_abs_diff"] else None,
                 "median_diff": float(d["median_diff"]) if d["median_diff"] else None,
                 "median_pct_diff": float(d["median_pct_diff"]) if d["median_pct_diff"] else None}
                for d in daily_diff
            ],
            "daily_warm_mdape": [
                {**d, "day": str(d["day"]),
                 "primary_mdape_warm": float(d["primary_mdape_warm"]) if d["primary_mdape_warm"] else None,
                 "shadow_mdape_warm": float(d["shadow_mdape_warm"]) if d["shadow_mdape_warm"] else None}
                for d in daily_warm
            ],
            "sign_off": sign_off,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        logger.info("[OK] Saved report: %s", args.output)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
