"""PR-28F-HF Stage 3 daily shadow metric report.

Runbook: docs/pr_29_hf_htw_stage_3_5_activation_runbook_20260511.md (§2.3)

PR-WARM-B 패턴 정합 + variant naming만 29_hf_htw로 매핑.
Codex R1 권고: non-inferior 기준 ("개선 입증"보다 "regression 부재 확인")

Usage:
    python3 scripts/pr_29_hf_htw_daily_shadow_metric.py --days 7

Output:
    Daily Δ_MdAPE distribution (primary vs shadow) + cold/warm slice + per-source.
    Compares primary (default v3_filtered_tuned, 32f) vs shadow (v3_filtered_tuned_29_hf_htw, 29_hf_htw).

Sign-off 기준 (Codex R1 / runbook §2.2):
- 7-day aggregate Δ_MdAPE ≤ +0.3pp (non-inferior)
- Cold slice (Artsy / Saatchi) Δ ≤ +0.5pp
- Warm slice Δ ≤ +0.5pp
- Latency P95 ≤ primary + 10%
- Error rate / empty-output regression 없음
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

# PR-WARM-B variant pattern과 동일. 본 29_hf_htw는 base replacement (32→28).
SHADOW_VARIANT = "v3_filtered_tuned_29_hf_htw"
PRIMARY_VARIANT = "v3_filtered_tuned"


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


def _fetch_daily_overall(conn, days: int) -> list[dict]:
    """Daily MdAPE per day (overall + cold/warm slice)."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            DATE(timestamp) AS day,
            COUNT(*) AS n_requests,
            -- Overall MdAPE (requires actual_price ground truth)
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(price_krw - actual_price) / NULLIF(actual_price, 0) * 100
            ) AS primary_mdape_overall,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(variant_shadow_prediction_price_krw - actual_price) /
                NULLIF(actual_price, 0) * 100
            ) AS shadow_mdape_overall,
            -- Cold slice
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(price_krw - actual_price) / NULLIF(actual_price, 0) * 100
            ) FILTER (WHERE is_warm_artist = false) AS primary_mdape_cold,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(variant_shadow_prediction_price_krw - actual_price) /
                NULLIF(actual_price, 0) * 100
            ) FILTER (WHERE is_warm_artist = false) AS shadow_mdape_cold,
            -- Warm slice
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(price_krw - actual_price) / NULLIF(actual_price, 0) * 100
            ) FILTER (WHERE is_warm_artist = true) AS primary_mdape_warm,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(variant_shadow_prediction_price_krw - actual_price) /
                NULLIF(actual_price, 0) * 100
            ) FILTER (WHERE is_warm_artist = true) AS shadow_mdape_warm,
            COUNT(CASE WHEN is_warm_artist = true THEN 1 END) AS n_warm,
            COUNT(CASE WHEN is_warm_artist = false THEN 1 END) AS n_cold
        FROM predict_logs
        WHERE variant_shadow_variant = %s
          AND timestamp >= NOW() - INTERVAL %s
          AND price_krw IS NOT NULL
          AND variant_shadow_prediction_price_krw IS NOT NULL
          AND actual_price IS NOT NULL
        GROUP BY DATE(timestamp)
        ORDER BY day DESC;
        """,
        (SHADOW_VARIANT, f"{days} days"),
    )
    rows = cur.fetchall()
    cols = (
        "day",
        "n_requests",
        "primary_mdape_overall",
        "shadow_mdape_overall",
        "primary_mdape_cold",
        "shadow_mdape_cold",
        "primary_mdape_warm",
        "shadow_mdape_warm",
        "n_warm",
        "n_cold",
    )
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _fetch_per_source_mdape(conn, days: int) -> list[dict]:
    """Per-source MdAPE delta (artsy / saatchi cohort breakdown)."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            DATE(timestamp) AS day,
            source,
            COUNT(*) AS n_requests,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(price_krw - actual_price) / NULLIF(actual_price, 0) * 100
            ) AS primary_mdape,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY ABS(variant_shadow_prediction_price_krw - actual_price) /
                NULLIF(actual_price, 0) * 100
            ) AS shadow_mdape
        FROM predict_logs
        WHERE variant_shadow_variant = %s
          AND timestamp >= NOW() - INTERVAL %s
          AND price_krw IS NOT NULL
          AND variant_shadow_prediction_price_krw IS NOT NULL
          AND actual_price IS NOT NULL
          AND source IS NOT NULL
        GROUP BY DATE(timestamp), source
        ORDER BY day DESC, source;
        """,
        (SHADOW_VARIANT, f"{days} days"),
    )
    rows = cur.fetchall()
    cols = ("day", "source", "n_requests", "primary_mdape", "shadow_mdape")
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _evaluate_sign_off(daily: list[dict]) -> dict:
    """Sign-off — Codex R1 non-inferior 기준."""
    if not daily:
        return {"verdict": "NO_DATA", "reason": "No daily metrics available"}

    overall_deltas, cold_deltas, warm_deltas = [], [], []
    for d in daily:
        p_o, s_o = d.get("primary_mdape_overall"), d.get("shadow_mdape_overall")
        p_c, s_c = d.get("primary_mdape_cold"), d.get("shadow_mdape_cold")
        p_w, s_w = d.get("primary_mdape_warm"), d.get("shadow_mdape_warm")
        if p_o is not None and s_o is not None:
            overall_deltas.append(float(s_o) - float(p_o))
        if p_c is not None and s_c is not None:
            cold_deltas.append(float(s_c) - float(p_c))
        if p_w is not None and s_w is not None:
            warm_deltas.append(float(s_w) - float(p_w))

    if not overall_deltas:
        return {"verdict": "NO_DATA", "reason": "No daily Δ available (missing actual_price?)"}

    agg_overall = float(np.mean(overall_deltas))
    agg_cold = float(np.mean(cold_deltas)) if cold_deltas else None
    agg_warm = float(np.mean(warm_deltas)) if warm_deltas else None

    max_overall = float(np.max(overall_deltas))
    max_cold = float(np.max(cold_deltas)) if cold_deltas else None
    max_warm = float(np.max(warm_deltas)) if warm_deltas else None

    criteria = {
        "n_days": len(overall_deltas),
        "7day_aggregate_delta_overall": agg_overall,
        "7day_aggregate_delta_cold": agg_cold,
        "7day_aggregate_delta_warm": agg_warm,
        "max_daily_delta_overall": max_overall,
        "max_daily_delta_cold": max_cold,
        "max_daily_delta_warm": max_warm,
    }

    # Codex R1 non-inferior 기준
    ok_overall = agg_overall <= 0.3
    ok_cold = (agg_cold is None) or (agg_cold <= 0.5)
    ok_warm = (agg_warm is None) or (agg_warm <= 0.5)
    ok_max_overall = max_overall <= 1.0  # no single day > +1pp

    sign_off_checks = {
        "aggregate_overall_le_plus_0p3": ok_overall,
        "aggregate_cold_le_plus_0p5": ok_cold,
        "aggregate_warm_le_plus_0p5": ok_warm,
        "max_daily_overall_le_plus_1p0": ok_max_overall,
    }

    if all(sign_off_checks.values()):
        verdict = "PASS"
    elif agg_overall <= 0.7 and max_overall <= 1.5:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "FAIL"

    return {
        "verdict": verdict,
        "criteria": criteria,
        "sign_off_checks": sign_off_checks,
        "per_day_overall_deltas": [round(d, 4) for d in overall_deltas],
        "per_day_cold_deltas": [round(d, 4) for d in cold_deltas] if cold_deltas else None,
        "per_day_warm_deltas": [round(d, 4) for d in warm_deltas] if warm_deltas else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Look-back window (default: 7 days / matches sign-off)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("model_test_results/pr_29_hf_htw_daily_shadow_report.json"),
    )
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("PR-28F-HF Stage 3 daily shadow metric report")
    logger.info("Primary: %s | Shadow: %s", PRIMARY_VARIANT, SHADOW_VARIANT)
    logger.info("Window: last %d days", args.days)
    logger.info("=" * 70)

    conn = _connect_db()
    try:
        daily = _fetch_daily_overall(conn, args.days)
        per_source = _fetch_per_source_mdape(conn, args.days)

        logger.info("Daily (overall + slice) — %d days", len(daily))
        for d in daily:
            p_o = d.get("primary_mdape_overall") or 0.0
            s_o = d.get("shadow_mdape_overall") or 0.0
            d_o = float(s_o) - float(p_o)
            marker = "✅" if d_o <= 0.3 else ("⚠️" if d_o <= 0.7 else "❌")
            logger.info(
                "  %s %s | n=%d | Δ_overall=%.3fpp | warm=%d / cold=%d",
                marker,
                d["day"],
                d["n_requests"],
                d_o,
                d["n_warm"],
                d["n_cold"],
            )

        logger.info("Per-source (artsy / saatchi)")
        for d in per_source:
            p, s = d.get("primary_mdape") or 0.0, d.get("shadow_mdape") or 0.0
            logger.info(
                "  %s %s | n=%d | primary=%.2f%% | shadow=%.2f%% | Δ=%.3fpp",
                d["day"],
                d["source"],
                d["n_requests"],
                float(p),
                float(s),
                float(s) - float(p),
            )

        sign_off = _evaluate_sign_off(daily)
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "window_days": args.days,
            "primary_variant": PRIMARY_VARIANT,
            "shadow_variant": SHADOW_VARIANT,
            "daily_overall": daily,
            "per_source": per_source,
            "sign_off": sign_off,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False))
        logger.info("Report saved: %s", args.output)
        logger.info("=" * 70)
        logger.info("SIGN-OFF VERDICT: %s", sign_off["verdict"])
        if sign_off["verdict"] != "NO_DATA":
            for check, passed in sign_off.get("sign_off_checks", {}).items():
                marker = "✅" if passed else "❌"
                logger.info("  %s %s", marker, check)
        logger.info("=" * 70)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
