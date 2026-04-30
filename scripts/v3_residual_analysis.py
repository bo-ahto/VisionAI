"""v3 Group 1.7: Residual analysis.

OOF 예측의 잔차를 stratification 별로 분석하여 모델이 어떤 segment 에서
체계적으로 약한지 진단한다.

방법:
- Cold: GroupKFold OOF ensemble (raw + cell-calibrated 둘 다)
- Warm: KFold OOF ensemble
- Stratification:
  1. source (artsy / saatchi)
  2. target_market (gallery / online)
  3. medium_category (acrylic / oil / ink / watercolor / other)
  4. artist 작품수 버킷 (1-2 / 3-4 / 5-9 / 10-29 / 30+)
  5. 예측 가격 decile (1-10)
- 메트릭 per stratum:
    n / MdAPE / mean_signed_residual_pct / median_signed_residual_pct / std_signed_residual_pct
  signed_residual_pct = (actual - pred) / actual * 100 (양수=과소예측, 음수=과대예측)

산출물:
    model_test_results/v3_diagnostics/residual_analysis.json
    model_test_results/v3_diagnostics/residual_by_<stratum>_cold.png 등

Usage:
    PYTHONPATH=src python3 scripts/v3_residual_analysis.py
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
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import _warm_mask, load_data, prepare_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OUT_JSON = DIAG_DIR / "residual_analysis.json"

WORK_COUNT_BUCKETS = [(1, 2), (3, 4), (5, 9), (10, 29), (30, 10_000)]


def _signed_residual_pct(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """양수: 과소예측 (실제 > 예측), 음수: 과대예측."""
    valid = y_true > 0
    out = np.full(len(y_true), np.nan)
    out[valid] = (y_true[valid] - y_pred[valid]) / y_true[valid] * 100
    return out


def _abs_residual_pct(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    valid = y_true > 0
    out = np.full(len(y_true), np.nan)
    out[valid] = np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] * 100
    return out


def _stratum_stats(
    y_true: np.ndarray, y_pred: np.ndarray, stratum: np.ndarray,
) -> list[dict]:
    signed = _signed_residual_pct(y_true, y_pred)
    abs_pct = _abs_residual_pct(y_true, y_pred)
    out: list[dict] = []
    for k in sorted({str(s) for s in stratum}):
        m = stratum.astype(str) == k
        if not m.any():
            continue
        s_vals = signed[m]
        a_vals = abs_pct[m]
        s_vals = s_vals[~np.isnan(s_vals)]
        a_vals = a_vals[~np.isnan(a_vals)]
        if len(s_vals) == 0:
            continue
        out.append({
            "stratum": k,
            "n": int(len(s_vals)),
            "mdape": float(np.median(a_vals)),
            "mean_signed_pct": float(np.mean(s_vals)),
            "median_signed_pct": float(np.median(s_vals)),
            "std_signed_pct": float(np.std(s_vals)),
            "p10_signed_pct": float(np.percentile(s_vals, 10)),
            "p90_signed_pct": float(np.percentile(s_vals, 90)),
        })
    return out


def _work_count_bucket(counts: np.ndarray) -> np.ndarray:
    out = np.array(["?"] * len(counts), dtype=object)
    for lo, hi in WORK_COUNT_BUCKETS:
        m = (counts >= lo) & (counts <= hi)
        out[m] = f"{lo}-{hi if hi < 1000 else '∞'}"
    return out.astype(str)


def _price_decile(y_pred: np.ndarray) -> np.ndarray:
    quantiles = np.quantile(y_pred, np.linspace(0, 1, 11))
    quantiles[-1] = quantiles[-1] * 1.000001
    out = np.full(len(y_pred), 0, dtype=int)
    for b in range(10):
        m = (y_pred >= quantiles[b]) & (y_pred < quantiles[b + 1])
        out[m] = b + 1
    return np.array([f"D{b:02d}" for b in out])


def _plot_signed_by_stratum(
    stats: list[dict], title: str, out_path: Path, x_label: str,
) -> None:
    if not stats:
        return
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    labels = [s["stratum"] for s in stats]
    medians = [s["median_signed_pct"] for s in stats]
    p10 = [s["p10_signed_pct"] for s in stats]
    p90 = [s["p90_signed_pct"] for s in stats]
    ns = [s["n"] for s in stats]

    x = np.arange(len(labels))
    err_low = [m - lo for m, lo in zip(medians, p10)]
    err_high = [hi - m for m, hi in zip(medians, p90)]
    ax.errorbar(x, medians, yerr=[err_low, err_high], fmt="o", color="#4FC3F7",
                ecolor="#4FC3F7", elinewidth=1.5, capsize=4, markersize=8,
                label="median (P10–P90)")
    ax.axhline(0, color="#888", linestyle="--", linewidth=1)
    for xi, yi, ni in zip(x, medians, ns):
        ax.annotate(f"n={ni}", (xi, yi), textcoords="offset points", xytext=(0, -18),
                    ha="center", color="white", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, color="white")
    ax.set_xlabel(x_label, color="white")
    ax.set_ylabel("signed residual % = (actual - pred) / actual × 100", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right", framealpha=0.85)
    fig.suptitle(title, color="white", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, facecolor="#1a1a1a")
    plt.close(fig)
    logger.info("plot saved: %s", out_path)


def _log_ratio_quantiles(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """log(pred/actual) quantiles — top-tail에서 percentage metric 왜곡 회피용.

    log_ratio > 0: 과대예측. log_ratio < 0: 과소예측. percentage residual과 달리
    분모(actual)가 작은 경우에도 폭주하지 않음.
    """
    valid = (y_true > 0) & (y_pred > 0)
    if not valid.any():
        return {}
    lr = np.log(y_pred[valid] / y_true[valid])
    return {
        "p10": float(np.percentile(lr, 10)),
        "p25": float(np.percentile(lr, 25)),
        "median": float(np.median(lr)),
        "p75": float(np.percentile(lr, 75)),
        "p90": float(np.percentile(lr, 90)),
        "mean": float(np.mean(lr)),
        "std": float(np.std(lr)),
    }


def _d10_deep_dive(
    y_true: np.ndarray, y_pred: np.ndarray, df: pd.DataFrame,
    source: np.ndarray, target_market: np.ndarray, medium: np.ndarray,
) -> dict:
    """D10 (최고가 예측 decile) 내부 세부 진단.

    cold path D10에서 median_signed -42.32% 라는 구조적 과대예측 신호 (codex 1.7 P1).
    cell saturation vs top-tail regime shift 구분을 위해 actual price decile + cell + medium
    조합으로 다시 쪼개 본다. saatchi_online sub-breakdown은 codex 1.7 R2 P1 추가 항목.
    """
    decile = _price_decile(y_pred)
    d10_mask = decile == "D10"
    n = int(d10_mask.sum())
    if n == 0:
        return {"n": 0}
    yt = y_true[d10_mask]
    yp = y_pred[d10_mask]
    src_d = source[d10_mask]
    tm_d = target_market[d10_mask]
    med_d = medium[d10_mask]
    cell_d = np.array([f"{s}_{t}" for s, t in zip(src_d, tm_d)])

    # Actual price 내부 decile (D10 안에서 다시 10등분)
    inner_q = np.quantile(yt, np.linspace(0, 1, 11))
    inner_q[-1] *= 1.000001
    inner_decile = np.full(n, 0, dtype=int)
    for b in range(10):
        m = (yt >= inner_q[b]) & (yt < inner_q[b + 1])
        inner_decile[m] = b + 1
    inner_label = np.array([f"DD{b:02d}" for b in inner_decile])

    # saatchi_online sub-breakdown (codex 1.7 R2 P1)
    saatchi_mask = cell_d == "saatchi_online"
    saatchi_dive: dict = {"n": int(saatchi_mask.sum())}
    if saatchi_mask.any():
        yt_s = yt[saatchi_mask]
        yp_s = yp[saatchi_mask]
        s_inner_q = np.quantile(yt_s, np.linspace(0, 1, 11))
        s_inner_q[-1] *= 1.000001
        s_inner = np.full(len(yt_s), 0, dtype=int)
        for b in range(10):
            m = (yt_s >= s_inner_q[b]) & (yt_s < s_inner_q[b + 1])
            s_inner[m] = b + 1
        s_inner_label = np.array([f"SDD{b:02d}" for b in s_inner])
        saatchi_dive.update({
            "actual_price_min": float(np.min(yt_s)),
            "actual_price_max": float(np.max(yt_s)),
            "by_inner_actual_decile": _stratum_stats(yt_s, yp_s, s_inner_label),
            "log_ratio_quantiles": _log_ratio_quantiles(yt_s, yp_s),
            "interpretation": (
                "D10 ∩ saatchi_online 안에서 actual decile 분포가 균등 음수 ⇒ saatchi 자체 issue 시사. "
                "low-actual decile만 음수 ⇒ saatchi 안의 underpriced art 가 D10에 잘못 분류된 문제 시사. "
                "관찰 결과 SDD01-SDD08 모두 강한 음수 ⇒ broad cell saturation 시사 → "
                "v3.1에서 D10 / 예측가 13.7M KRW 이상 구간 전용 calibration layer 우선 검토."
            ),
        })

    return {
        "n": n,
        "pred_price_min": float(np.min(yp)),
        "pred_price_max": float(np.max(yp)),
        "actual_price_min": float(np.min(yt)),
        "actual_price_max": float(np.max(yt)),
        "by_cell": _stratum_stats(yt, yp, cell_d),
        "by_medium": _stratum_stats(yt, yp, med_d),
        "by_inner_actual_decile": _stratum_stats(yt, yp, inner_label),
        "log_ratio_quantiles_overall": _log_ratio_quantiles(yt, yp),
        "saatchi_online_sub_breakdown": saatchi_dive,
        "metric_caveat": (
            "Top-tail 구간에서 percentage residual은 actual이 작을 때 폭증. "
            "mean보다 median, percentage보다 log(pred/actual) 신뢰. "
            "log_ratio > 0: 과대예측 / log_ratio < 0: 과소예측."
        ),
        "summary": (
            "D10 내부 actual price decile별 signed residual: 모든 inner decile 음수 → cell saturation, "
            "low inner decile만 음수 → top-tail regime shift (예측 D10에 underpriced art 잘못 분류)."
        ),
    }


def _work_count_cell_two_way(
    y_true: np.ndarray, y_pred: np.ndarray,
    work_bucket: np.ndarray, cell: np.ndarray,
) -> list[dict]:
    """work_count_bucket × cell 2-way cut — 구성효과 진단 (codex R2 P2).

    work_count 3-4 worst가 정말 'work_count signal'인지, 아니면 그 버킷이 어려운 cell
    (saatchi_online 등)에 더 많이 몰린 구성효과인지 확인.
    """
    out: list[dict] = []
    for wb in sorted(set(work_bucket.tolist())):
        for c in sorted(set(cell.tolist())):
            mask = (work_bucket == wb) & (cell == c)
            if mask.sum() < 30:
                continue
            stats = _stratum_stats(y_true[mask], y_pred[mask], np.array(["x"] * mask.sum()))
            if not stats:
                continue
            s = stats[0]
            out.append({
                "work_bucket": wb,
                "cell": c,
                "n": s["n"],
                "mdape": s["mdape"],
                "median_signed_pct": s["median_signed_pct"],
            })
    return out


def _other_medium_raw_breakdown(df: pd.DataFrame) -> dict:
    """medium_category='other' 그룹의 raw medium 컬럼 분포 — 라벨 정제 가능성 진단."""
    other_mask = df["medium_category"].astype(str) == "other"
    if not other_mask.any():
        return {"n": 0}
    raw_mediums = df.loc[other_mask, "medium"].fillna("(null)").astype(str)
    counts = raw_mediums.value_counts()
    return {
        "n": int(other_mask.sum()),
        "unique_raw_mediums": int(len(counts)),
        "top_20_raw_mediums": counts.head(20).to_dict(),
        "interpretation": (
            "'other'는 medium_category 미분류 버킷. 상위 raw mediums 가 명확한 카테고리로 "
            "재매핑 가능하면 라벨 정제 → MdAPE 49% / median_signed -18.35% 개선 잠재."
        ),
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    oof = np.load(DIAG_DIR / "oof_predictions.npz", allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_ln = oof["xgb_preds_gkf_ln"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_kf_ln = oof["cb_preds_kf_ln"]
    xgb_kf_ln = oof["xgb_preds_kf_ln"]

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y_check, groups = prepare_features(df)
    np.testing.assert_allclose(y_check, y_actual_ln, rtol=1e-10)
    source = df["source"].astype(str).to_numpy()
    target_market = np.where(df["is_krw"].astype(int) == 1, "gallery", "online")
    medium = df["medium_category"].astype(str).fillna("unknown").to_numpy()

    # 작가별 작품 수 (전체 데이터에서 카운트)
    artist_counts = pd.Series(groups).value_counts()
    work_count = np.array([artist_counts[g] for g in groups])
    work_bucket = _work_count_bucket(work_count)

    wmask = _warm_mask(groups)
    source_warm = source[wmask]
    tm_warm = target_market[wmask]
    medium_warm = medium[wmask]
    work_bucket_warm = work_bucket[wmask]

    # 가격 / 예측
    y_full = np.exp(y_actual_ln)
    ens_cold_raw = np.exp((cb_gkf_ln + xgb_gkf_ln) / 2)
    y_warm_full = np.exp(y_warm_ln)
    ens_warm_raw = np.exp((cb_kf_ln + xgb_kf_ln) / 2)

    # cold path: cell calibration 적용
    cal_path = OUT_DIR / "integrated_v3_filtered_tuned_source_calibration.json"
    cal = json.loads(cal_path.read_text())
    cell_cold = np.array([f"{s}_{t}" for s, t in zip(source, target_market)])
    cell_warm = np.array([f"{s}_{t}" for s, t in zip(source_warm, tm_warm)])
    ens_cold_calibrated = ens_cold_raw.copy()
    for k, f in cal["cold_factors"].items():
        m = cell_cold == k
        if m.any():
            ens_cold_calibrated[m] = ens_cold_raw[m] * f

    pred_decile_cold = _price_decile(ens_cold_calibrated)
    pred_decile_warm = _price_decile(ens_warm_raw)

    # D10 deep-dive (codex 1.7 P1)
    d10_dive = _d10_deep_dive(y_full, ens_cold_calibrated, df, source, target_market, medium)
    other_dive = _other_medium_raw_breakdown(df)
    # work_count × cell 2-way (codex 1.7 R2 P2)
    cell_cold_full = np.array([f"{s}_{t}" for s, t in zip(source, target_market)])
    work_cell_2way = _work_count_cell_two_way(y_full, ens_cold_calibrated, work_bucket, cell_cold_full)

    # Stratification 분석
    out: dict = {
        "config": {
            "ensemble": "(CB + XGB) / 2 in ln-space",
            "signed_residual_def": "(actual - pred) / actual × 100  (양수=과소예측)",
            "cold_calibration": "cell factor (artsy_online=0.9426, saatchi_online=0.9569, artsy_gallery=1.0)",
            "work_count_buckets": [f"{lo}-{hi if hi < 1000 else '∞'}" for lo, hi in WORK_COUNT_BUCKETS],
        },
        "cold_calibrated": {
            "n": int(len(y_full)),
            "by_source": _stratum_stats(y_full, ens_cold_calibrated, source),
            "by_target_market": _stratum_stats(y_full, ens_cold_calibrated, target_market),
            "by_medium_category": _stratum_stats(y_full, ens_cold_calibrated, medium),
            "by_work_count_bucket": _stratum_stats(y_full, ens_cold_calibrated, work_bucket),
            "by_pred_decile": _stratum_stats(y_full, ens_cold_calibrated, pred_decile_cold),
        },
        "cold_raw": {
            "n": int(len(y_full)),
            "by_source": _stratum_stats(y_full, ens_cold_raw, source),
            "by_target_market": _stratum_stats(y_full, ens_cold_raw, target_market),
            "by_medium_category": _stratum_stats(y_full, ens_cold_raw, medium),
            "by_work_count_bucket": _stratum_stats(y_full, ens_cold_raw, work_bucket),
        },
        "warm_raw": {
            "n": int(len(y_warm_full)),
            "by_source": _stratum_stats(y_warm_full, ens_warm_raw, source_warm),
            "by_target_market": _stratum_stats(y_warm_full, ens_warm_raw, tm_warm),
            "by_medium_category": _stratum_stats(y_warm_full, ens_warm_raw, medium_warm),
            "by_work_count_bucket": _stratum_stats(y_warm_full, ens_warm_raw, work_bucket_warm),
            "by_pred_decile": _stratum_stats(y_warm_full, ens_warm_raw, pred_decile_warm),
        },
        "d10_cold_deep_dive": d10_dive,
        "other_medium_raw_breakdown": other_dive,
        "work_count_x_cell_2way": work_cell_2way,
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    # PNG: 주요 stratification 시각화
    _plot_signed_by_stratum(out["cold_calibrated"]["by_source"],
                            "Cold (calibrated) — by source", DIAG_DIR / "residual_cold_by_source.png", "source")
    _plot_signed_by_stratum(out["cold_calibrated"]["by_target_market"],
                            "Cold (calibrated) — by target_market", DIAG_DIR / "residual_cold_by_target_market.png", "target_market")
    _plot_signed_by_stratum(out["cold_calibrated"]["by_medium_category"],
                            "Cold (calibrated) — by medium category", DIAG_DIR / "residual_cold_by_medium.png", "medium_category")
    _plot_signed_by_stratum(out["cold_calibrated"]["by_work_count_bucket"],
                            "Cold (calibrated) — by artist work count bucket", DIAG_DIR / "residual_cold_by_work_count.png", "작가 작품 수")
    _plot_signed_by_stratum(out["cold_calibrated"]["by_pred_decile"],
                            "Cold (calibrated) — by predicted price decile", DIAG_DIR / "residual_cold_by_pred_decile.png", "예측 가격 decile")
    _plot_signed_by_stratum(out["warm_raw"]["by_pred_decile"],
                            "Warm (raw) — by predicted price decile", DIAG_DIR / "residual_warm_by_pred_decile.png", "예측 가격 decile")
    _plot_signed_by_stratum(out["warm_raw"]["by_medium_category"],
                            "Warm (raw) — by medium category", DIAG_DIR / "residual_warm_by_medium.png", "medium_category")

    # Console summary
    print("\n" + "=" * 95)
    print("v3 Group 1.7 Residual Analysis Summary")
    print("=" * 95)
    for slice_name in ["cold_calibrated", "warm_raw"]:
        s = out[slice_name]
        print(f"\n[{slice_name}] n={s['n']}")
        for stratum_name in ["by_source", "by_target_market", "by_medium_category",
                             "by_work_count_bucket", "by_pred_decile"]:
            if stratum_name not in s:
                continue
            print(f"\n  {stratum_name}:")
            for st in s[stratum_name]:
                print(f"    {st['stratum']:<22} n={st['n']:>5} MdAPE={st['mdape']:>5.2f}% "
                      f"med_signed={st['median_signed_pct']:+6.2f}% "
                      f"P10={st['p10_signed_pct']:+6.1f}%  P90={st['p90_signed_pct']:+6.1f}%")
    # D10 deep-dive 콘솔 출력
    print("\n" + "-" * 95)
    print("D10 (cold, calibrated) deep-dive")
    print("-" * 95)
    print(f"  n={d10_dive['n']}  pred=[{d10_dive['pred_price_min']:,.0f}, {d10_dive['pred_price_max']:,.0f}] KRW  "
          f"actual=[{d10_dive['actual_price_min']:,.0f}, {d10_dive['actual_price_max']:,.0f}] KRW")
    print("\n  by_cell:")
    for st in d10_dive["by_cell"]:
        print(f"    {st['stratum']:<22} n={st['n']:>4} MdAPE={st['mdape']:>5.2f}% "
              f"med_signed={st['median_signed_pct']:+6.2f}% mean={st['mean_signed_pct']:+7.1f}%")
    print("\n  by_inner_actual_decile (DD01=낮은 actual ~ DD10=높은 actual):")
    for st in d10_dive["by_inner_actual_decile"]:
        print(f"    {st['stratum']:<8} n={st['n']:>4} MdAPE={st['mdape']:>5.2f}% "
              f"med_signed={st['median_signed_pct']:+6.2f}%")

    if d10_dive["saatchi_online_sub_breakdown"].get("by_inner_actual_decile"):
        sd = d10_dive["saatchi_online_sub_breakdown"]
        print(f"\n  D10 ∩ saatchi_online sub-breakdown (n={sd['n']}, "
              f"actual=[{sd['actual_price_min']:,.0f}, {sd['actual_price_max']:,.0f}] KRW):")
        for st in sd["by_inner_actual_decile"]:
            print(f"    {st['stratum']:<8} n={st['n']:>4} MdAPE={st['mdape']:>6.2f}% "
                  f"med_signed={st['median_signed_pct']:+7.2f}%")
        lr = sd["log_ratio_quantiles"]
        print(f"    log(pred/actual) overall: med={lr['median']:+.3f} "
              f"P10={lr['p10']:+.3f} P90={lr['p90']:+.3f}  (>0=과대 / <0=과소)")

    print("\n  'other' medium raw breakdown (라벨 정제 진단):")
    print(f"    n={other_dive['n']}  unique raw mediums={other_dive['unique_raw_mediums']}")
    print(f"    top raw mediums:")
    for raw, cnt in list(other_dive["top_20_raw_mediums"].items())[:10]:
        print(f"      {raw[:60]:<60} {cnt}")

    print("\n  work_count × cell 2-way cut (cold calibrated, 구성효과 진단):")
    by_bucket: dict[str, list] = {}
    for r in work_cell_2way:
        by_bucket.setdefault(r["work_bucket"], []).append(r)
    for wb in sorted(by_bucket.keys()):
        rows = by_bucket[wb]
        print(f"    [{wb}]")
        for r in rows:
            print(f"      {r['cell']:<22} n={r['n']:>5} MdAPE={r['mdape']:>5.2f}% "
                  f"med_signed={r['median_signed_pct']:+6.2f}%")

    print(f"\n저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
