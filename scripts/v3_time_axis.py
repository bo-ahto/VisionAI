"""v3 Group 1.10: Time-axis evaluation feasibility (limitation report + cohort observation).

본 진단의 정확한 scope:
- "Time-axis evaluation" 가능 여부 점검 + Artsy 작품 제작연도(year_made)별 cohort/age
  관찰. **시장 시점 (listing/sale time) stability 평가가 아님.**
- year_made = 작품이 만들어진 해 (cohort/age proxy). listing/sale time과 무관.
  → 본 결과는 market-time drift 진단이 아니라 "제작연도 cohort 관찰적 stratification".

배경 (v3 plan §2.1):
- 1차 시장 모델은 cross-sectional protocol (GroupKFold by artist + KFold).
- 진정한 temporal holdout (학습 시점 < 예측 시점) 평가는 다음 한계 때문에 어려움:
  · Saatchi (74% 작품 = 21,087건): year_made / 게시일 / 거래일 컬럼 없음
  · Artsy (26% 작품 = 7,289건): year_made 99.2% 가용 (정제 후 7,166 valid, 65 dirty 제외)
  · year_made 자체가 listing/sale time proxy가 아님 — 작품 제작연도일 뿐
- artwork_id (MongoDB ObjectId)의 timestamp는 crawl 시점이라 가격/상장 시점과 무관

이번 SOFT 진단:
- Production routing (warm=XGB / cold=CB+cell calibration) 으로 OOF 예측 구성
- Artsy year_made 정제 (≥2000, ≤2026) 후 year 단위 stratify
- 결과는 "Artsy slice 내 제작연도별 관찰적 cohort stratification" — temporal stability 아님

산출물:
    model_test_results/v3_diagnostics/time_axis.json
    model_test_results/v3_diagnostics/time_axis_mdape.png

Usage:
    PYTHONPATH=src python3 scripts/v3_time_axis.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import load_data, prepare_features

from visionai.price_engine._eval_helpers import (
    apply_cell_calibration as _apply_cell_calibration_helper,
)
from visionai.price_engine._eval_helpers import (
    cell_keys as _cell_keys_helper,
)
from visionai.price_engine._eval_helpers import (
    derive_target_market,
)
from visionai.price_engine._eval_helpers import (
    warm_mask as _warm_mask,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OUT_JSON = DIAG_DIR / "time_axis.json"
OUT_PNG = DIAG_DIR / "time_axis_mdape.png"

YEAR_MIN = 2000
YEAR_MAX = 2026


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def _apply_cell_calibration(
    pred_price: np.ndarray, cell: np.ndarray, factors: dict[str, float],
) -> np.ndarray:
    return _apply_cell_calibration_helper(pred_price, cell, factors)


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    oof = np.load(DIAG_DIR / "oof_predictions.npz", allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    warm_mask_full = oof["warm_mask"].astype(bool)
    xgb_kf_ln_warm = oof["xgb_preds_kf_ln"]  # warm slice (length = warm count)

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)
    source = df["source"].astype(str).to_numpy()
    target_market = derive_target_market(df["is_krw"])
    cell = _cell_keys_helper(source, target_market)

    # Production routing 예측 (warm=XGB OOF / cold=CB OOF + cold cell factor)
    cal = json.loads((OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json").read_text())
    cb_cold_price = np.exp(cb_gkf_ln)
    cb_cold_calibrated = _apply_cell_calibration(cb_cold_price, cell, cal["cold_factors"])
    prod_pred = cb_cold_calibrated.copy()  # 기본 cold path
    warm_full_idx = np.where(warm_mask_full)[0]
    if len(warm_full_idx) != len(xgb_kf_ln_warm):
        raise RuntimeError(
            f"warm_mask sum {len(warm_full_idx)} != xgb_kf_ln_warm length {len(xgb_kf_ln_warm)}"
        )
    prod_pred[warm_full_idx] = np.exp(xgb_kf_ln_warm)  # warm path 덮어쓰기 (no calibration)
    y_full_price = np.exp(y_actual_ln)

    # year_made 가용성 진단
    year_made = df["year_made"].to_numpy()
    valid_year = (
        (~np.isnan(year_made))
        & (year_made >= YEAR_MIN)
        & (year_made <= YEAR_MAX)
    )
    artsy_mask = source == "artsy"
    artsy_with_year = artsy_mask & valid_year
    saatchi_mask = source == "saatchi"

    coverage = {
        "total": int(len(df)),
        "artsy_total": int(artsy_mask.sum()),
        "saatchi_total": int(saatchi_mask.sum()),
        "artsy_with_valid_year": int(artsy_with_year.sum()),
        "artsy_with_valid_year_pct": float(artsy_with_year.sum() / artsy_mask.sum() * 100),
        "saatchi_with_year_made": int(((~np.isnan(year_made)) & saatchi_mask).sum()),
        "year_made_dirty_values_excluded": int(
            ((~np.isnan(year_made)) & ((year_made < YEAR_MIN) | (year_made > YEAR_MAX))).sum()
        ),
    }
    logger.info("Coverage: %s", coverage)

    # Artsy 전체 baseline (year stratify 비교용) — production routing 적용
    artsy_idx = np.where(artsy_mask)[0]
    artsy_baseline_mdape = mdape(y_full_price[artsy_idx], prod_pred[artsy_idx])

    # Year bucket 정의
    artsy_year = year_made[artsy_with_year]
    artsy_idx_with_year = np.where(artsy_with_year)[0]
    buckets = [
        ("2000-2014", 2000, 2014),
        ("2015-2019", 2015, 2019),
        ("2020", 2020, 2020),
        ("2021", 2021, 2021),
        ("2022", 2022, 2022),
        ("2023", 2023, 2023),
        ("2024", 2024, 2024),
        ("2025-2026", 2025, 2026),
    ]
    per_year: list[dict] = []
    for label, lo, hi in buckets:
        m_year = (artsy_year >= lo) & (artsy_year <= hi)
        idx = artsy_idx_with_year[m_year]
        if len(idx) < 30:
            per_year.append({
                "bucket": label,
                "n": int(len(idx)),
                "MdAPE": None,
                "W30": None,
                "skipped_reason": "n < 30",
            })
            continue
        per_year.append({
            "bucket": label,
            "n": int(len(idx)),
            "MdAPE": mdape(y_full_price[idx], prod_pred[idx]),
            "W30": w30(y_full_price[idx], prod_pred[idx]),
        })

    # warm vs cold 분리도 함께
    wmask = _warm_mask(groups)
    per_year_split: list[dict] = []
    for label, lo, hi in buckets:
        m_year = (artsy_year >= lo) & (artsy_year <= hi)
        idx = artsy_idx_with_year[m_year]
        if len(idx) < 30:
            continue
        warm_idx = idx[wmask[idx]]
        cold_idx = idx[~wmask[idx]]
        per_year_split.append({
            "bucket": label,
            "n_total": int(len(idx)),
            "n_warm": int(len(warm_idx)),
            "n_cold": int(len(cold_idx)),
            "overall_MdAPE": mdape(y_full_price[idx], prod_pred[idx]),
            "warm_MdAPE": mdape(y_full_price[warm_idx], prod_pred[warm_idx])
                          if len(warm_idx) >= 10 else None,
            "cold_MdAPE": mdape(y_full_price[cold_idx], prod_pred[cold_idx])
                          if len(cold_idx) >= 10 else None,
        })

    # 가용한 MdAPE 값 모아서 spread / range
    valid_mdapes = [p["MdAPE"] for p in per_year if p["MdAPE"] is not None]
    spread = {
        "min": float(np.min(valid_mdapes)),
        "max": float(np.max(valid_mdapes)),
        "range_pp": float(np.max(valid_mdapes) - np.min(valid_mdapes)),
        "std": float(np.std(valid_mdapes)),
        "artsy_baseline_mdape": float(artsy_baseline_mdape),
    }

    summary = {
        "config": {
            "purpose": (
                "Temporal-feasibility limitation report + Artsy year_made cohort/age "
                "observational stratification. (파일명에 'time_axis'가 들어 있으나 실제 분석은 "
                "market-time holdout이 아닌 cohort stratification — limitation 첫 항목 참조)"
            ),
            "title_clarification": (
                "이 산출물의 본질은 '진정한 temporal evaluation의 가능 범위 점검 + Artsy 제작연도 "
                "cohort 관찰'이며, market-time stability를 평가하지 않는다. v3.1에서 listing/sale "
                "time 컬럼 신규 수집 후 정식 temporal holdout 가능."
            ),
            "method": (
                "production routing OOF 예측 (warm=XGB / cold=CB+cell calibration)을 "
                "Artsy year_made 버킷으로 stratify. 진정한 temporal holdout 아님 — "
                "GroupKFold는 작가 단위 split, time split 아님. "
                "year_made = 작품 제작연도 (cohort/age). listing/sale time과 무관."
            ),
            "year_window": [YEAR_MIN, YEAR_MAX],
            "limitations": [
                "year_made 자체가 listing/sale time proxy 아님 — 작품 제작연도. "
                "본 분석은 market-time stability가 아니라 cohort/age stratification.",
                "Saatchi (74%, n=21,087): year_made / 게시일 / 거래일 컬럼 없음 — temporal eval 불가",
                "Artsy year_made: 99.2% 가용 (정제 후 7,166 valid, 65 dirty 제외, range guard ≥2000 ≤2026)",
                "artwork_id ObjectId timestamp는 crawl 시점 — 가격 형성 시점과 무관",
                "현재 OOF는 GroupKFold (artist split) — 작가별 cold-start 시뮬은 맞으나 time drift 시뮬 아님",
                "→ 진정한 temporal eval은 v3.1에서 가격 시점 (listing_date / sold_date) 컬럼 신규 수집 후 가능",
            ],
            "acceptance_gate": "SOFT (limitation report) — 1.10은 평가 가능 범위와 후속 작업 식별이 목표",
            "metric_note": (
                "MdAPE 표는 production-routed OOF 기준 (warm artist 행은 XGB, cold artist 행은 "
                "CB+cell calibration). 'cold MdAPE'는 별도 per_year_artsy_warm_cold_split에서 "
                "warm/cold 분리 결과로만 보고."
            ),
        },
        "data_coverage": coverage,
        "per_year_artsy_overall": per_year,
        "per_year_artsy_warm_cold_split": per_year_split,
        "spread_overall": spread,
        "v31_followup": [
            "listing_date / sold_date / first_seen_date 같은 time-aware 컬럼 신규 수집 (Artsy + Saatchi)",
            "수집 후 temporal holdout (year T 이전 train / year T 이후 test) 정식 평가",
            "ObjectId crawl timestamp 기반 data freshness drift 모니터링 (Saatchi 한정)",
            "year_made dirty value (4800 등) 클렌징 — Group 5 데이터 클렌징과 연계",
            "Bucket별 composition audit (medium / gallery / price band / warm-cold 비중) — "
            "2021/2023 연도 변동이 시간 효과인지 mix shift인지 분리",
        ],
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    # PNG: per year MdAPE
    valid_buckets = [p for p in per_year if p["MdAPE"] is not None]
    if valid_buckets:
        fig, ax = plt.subplots(figsize=(10, 5), facecolor="#1a1a1a")
        ax.set_facecolor("#1a1a1a")
        labels = [p["bucket"] for p in valid_buckets]
        mdapes = [p["MdAPE"] for p in valid_buckets]
        ns = [p["n"] for p in valid_buckets]
        x = np.arange(len(labels))
        bars = ax.bar(x, mdapes, color="#4FC3F7")
        ax.axhline(spread["artsy_baseline_mdape"], color="#FFB74D", linestyle="--", linewidth=1.5,
                   label=f"Artsy baseline ({spread['artsy_baseline_mdape']:.1f}%)")
        for xi, mi, ni in zip(x, mdapes, ns, strict=False):
            ax.annotate(f"n={ni}", (xi, mi), textcoords="offset points", xytext=(0, 4),
                        ha="center", color="white", fontsize=9)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, color="white")
        ax.set_ylabel("Production-routed MdAPE (%) — warm=XGB / cold=CB+calibration", color="white")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_color("white")
        ax.grid(alpha=0.2, axis="y")
        ax.legend(loc="upper right", framealpha=0.85, fontsize=9)
        fig.suptitle(
            "v3 Group 1.10 — Artsy year_made cohort stratification (NOT market-time holdout)",
            color="white", fontsize=12,
        )
        fig.tight_layout()
        fig.savefig(OUT_PNG, dpi=120, facecolor="#1a1a1a")
        plt.close(fig)
        logger.info("plot saved: %s", OUT_PNG)

    # Console summary
    print("\n" + "=" * 95)
    print("v3 Group 1.10 Time Axis Evaluation Summary")
    print("=" * 95)
    print("\n[Coverage]")
    for k, v in coverage.items():
        print(f"  {k}: {v}")
    print(f"\n[Limitations]")
    for lim in summary["config"]["limitations"]:
        print(f"  - {lim}")
    print(f"\n[Artsy year_made cohort stratification — observational, NOT market-time]")
    print(f"  baseline (Artsy 전체 production-routed OOF MdAPE): {spread['artsy_baseline_mdape']:.2f}%")
    print(f"\n  {'Bucket':<14} {'n':>5} {'MdAPE (prod)':>13} {'W30':>8}")
    for p in per_year:
        if p["MdAPE"] is None:
            print(f"  {p['bucket']:<14} {p['n']:>5}  {'(skipped: n<30)':>17}")
        else:
            print(f"  {p['bucket']:<14} {p['n']:>5} {p['MdAPE']:>12.2f}% {p['W30']:>7.2f}%")
    print(f"\n  spread: min={spread['min']:.2f}% max={spread['max']:.2f}% range={spread['range_pp']:.2f}%p std={spread['std']:.2f}%p")
    print(f"\n[warm/cold 분리 (per_year_artsy_warm_cold_split)]")
    print(f"  {'Bucket':<14} {'n_warm':>7} {'n_cold':>7} {'overall':>8} {'warm':>8} {'cold':>8}")
    for p in per_year_split:
        wm = f"{p['warm_MdAPE']:.2f}%" if p['warm_MdAPE'] is not None else "-"
        cm = f"{p['cold_MdAPE']:.2f}%" if p['cold_MdAPE'] is not None else "-"
        print(f"  {p['bucket']:<14} {p['n_warm']:>7} {p['n_cold']:>7} {p['overall_MdAPE']:>7.2f}% {wm:>8} {cm:>8}")
    print(f"\n[v3.1 후속]")
    for f in summary["v31_followup"]:
        print(f"  - {f}")
    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
