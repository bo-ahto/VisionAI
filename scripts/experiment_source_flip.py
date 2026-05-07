"""Source label flip 통제 실험.

같은 작품 features에 대해 source='artsy' / source='saatchi' 두 라벨로
각각 예측하여 출처 효과를 분리 측정한다.

3개 코호트 × 10명 = 30개 작품. 각 작품 2번 예측 = 60 prediction.

코호트:
    A. Both         — Artsy ∩ Saatchi 학습셋 작가
    B. Artsy only   — Artsy 학습셋에만 있는 작가
    C. Saatchi only — Saatchi 학습셋에만 있는 작가

target_market='online' 고정 (Saatchi 학습이 100% online — 다른 셀은 OOD).

산출물:
    model_test_results/source_flip_results.json  — raw 데이터 + 통계
    model_test_results/source_flip_report.md     — 사람용 요약 표
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from visionai.price_engine.api.primary_feature_builder import SUPPORT_FACTORS
from visionai.price_engine.api.primary_predictor import (
    CAT_FEATURES, CB_FEATURES, PrimaryPredictor,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"
SEED = 42
N_PER_COHORT = 10
TARGET_MARKET = "online"
WARM_ONLY = os.getenv("WARM_ONLY", "0") == "1"  # True면 warm 라우팅 작가만 코호트에 포함


def _load_warm_slugs() -> set[str]:
    path = OUT_DIR / "integrated_v3_filtered_tuned_warm_artists.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return set(str(s) for s in data.get("warm_artist_slugs", []))


def _norm_name(s: Any) -> str | None:
    if pd.isna(s):
        return None
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _ensure_features(df: pd.DataFrame, default_source: str) -> pd.DataFrame:
    """학습 시 load_data()와 동일하게 누락 피처를 채운다."""
    df = df.copy()
    if "source" not in df.columns:
        df["source"] = default_source
    if "ln_area" not in df.columns:
        df["ln_area"] = np.log(df["area_cm2"].clip(lower=1))
    if "support_factor" not in df.columns:
        df["support_factor"] = df["support_type"].map(SUPPORT_FACTORS).fillna(0.85)
    if "ho_x_support" not in df.columns:
        df["ho_x_support"] = df["ho"] * df["support_factor"]
    if "has_birth_year" not in df.columns:
        df["has_birth_year"] = df["artist_birth_year"].notna().astype(int)
    for col in ("ho_price_level", "medium_price_level", "profile_completeness"):
        if col not in df.columns:
            df[col] = 0.0
    return df


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")
    artsy = _ensure_features(artsy, default_source="artsy")
    saatchi = _ensure_features(saatchi, default_source="saatchi")
    artsy["name_norm"] = artsy["artist_name"].apply(_norm_name)
    saatchi["name_norm"] = saatchi["artist_name"].apply(_norm_name)
    return artsy, saatchi


def pick_representative_artwork(df_artist: pd.DataFrame) -> pd.Series:
    """작가 작품 중 ln_price 중앙값에 가장 가까운 1점을 대표로 선정."""
    median_ln = df_artist["ln_price"].median()
    idx = (df_artist["ln_price"] - median_ln).abs().idxmin()
    return df_artist.loc[idx]


def build_cohorts(
    artsy: pd.DataFrame,
    saatchi: pd.DataFrame,
    warm_slugs: set[str] | None = None,
) -> dict[str, list[dict]]:
    """3개 코호트 각각 10명 작가 + 작품 1점 추출.

    warm_slugs가 주어지면, 각 작품 행의 artist_slug가 warm_slugs에 포함된
    경우만 통과시킨다 — 즉 학습 시 warm slice(≥5작품)에 들어간 작가의 작품만
    코호트 후보가 된다. 작가 단위 라우팅은 predictor가 다시 결정.
    """
    a_online = artsy[artsy["is_krw"] == 0].copy()
    s_online = saatchi[saatchi["is_krw"] == 0].copy()

    if warm_slugs is not None:
        a_online = a_online[a_online["artist_slug"].astype(str).isin(warm_slugs)]
        s_online = s_online[s_online["artist_slug"].astype(str).isin(warm_slugs)]
        logger.info(
            "warm 필터 적용: Artsy %d rows, Saatchi %d rows",
            len(a_online), len(s_online),
        )

    a_names = set(a_online["name_norm"].dropna().unique())
    s_names = set(s_online["name_norm"].dropna().unique())

    both = sorted(a_names & s_names)
    only_a = sorted(a_names - s_names)
    only_s = sorted(s_names - a_names)

    logger.info(
        "코호트 후보: both=%d, artsy_only=%d, saatchi_only=%d",
        len(both), len(only_a), len(only_s),
    )

    rng = np.random.RandomState(SEED)

    def _pick(names: list[str], n: int) -> list[str]:
        names = list(names)
        rng.shuffle(names)
        return names[:n]

    cohort_specs = {
        "both": (_pick(both, N_PER_COHORT), s_online, "saatchi"),
        "artsy_only": (_pick(only_a, N_PER_COHORT), a_online, "artsy"),
        "saatchi_only": (_pick(only_s, N_PER_COHORT), s_online, "saatchi"),
    }

    cohorts: dict[str, list[dict]] = {}
    for cohort_name, (names, source_df, side) in cohort_specs.items():
        rows = []
        for n in names:
            artist_rows = source_df[source_df["name_norm"] == n]
            if artist_rows.empty:
                logger.warning("%s: %r 작품 0건 — skip", cohort_name, n)
                continue
            artwork = pick_representative_artwork(artist_rows)
            rows.append({
                "name_norm": n,
                "artist_name": artwork["artist_name"],
                "artist_slug": str(artwork["artist_slug"]),
                "source_side": side,
                "actual_ln_price": float(artwork["ln_price"]),
                "actual_price_krw": int(np.exp(artwork["ln_price"])),
                "row": artwork,
            })
        cohorts[cohort_name] = rows
        logger.info("Cohort %s: %d artists picked", cohort_name, len(rows))
    return cohorts


def features_dict_from_row(row: pd.Series) -> dict:
    """CB_FEATURES만 추려 dict로. categorical은 str 변환."""
    feat: dict = {}
    for col in CB_FEATURES:
        v = row.get(col)
        if col in CAT_FEATURES:
            feat[col] = "unknown" if pd.isna(v) else str(v)
        else:
            feat[col] = float(v) if not pd.isna(v) else 0.0
    return feat


def diagnostic_fields(row: pd.Series) -> dict:
    """리포트에 함께 표시할 작가/작품 진단 피처."""
    def _get(col, default=None):
        v = row.get(col)
        if pd.isna(v):
            return default
        return v
    return {
        "ho": _get("ho"),
        "area_cm2": _get("area_cm2"),
        "support_type": _get("support_type"),
        "medium_category": _get("medium_category"),
        "attribution_class": _get("attribution_class"),
        "is_unique": int(_get("is_unique", 0)),
        "is_edition": int(_get("is_edition", 0)),
        "artist_birth_year": _get("artist_birth_year"),
        "career_stage": _get("career_stage"),
        "ln_followers": _get("ln_followers"),
        "artist_total_works": _get("artist_total_works"),
        "for_sale_ratio": _get("for_sale_ratio"),
        "gallery_tier": _get("gallery_tier"),
    }


def count_training_works(name_norm: str, artsy: pd.DataFrame, saatchi: pd.DataFrame) -> dict:
    """작가의 학습 작품 수 (출처별).

    artist_slug는 출처마다 형식이 달라(Artsy: 하이픈, Saatchi: 숫자 ID) 같은 작가도
    다른 slug를 가짐. 따라서 정규화된 artist_name으로 카운트해야 양쪽 진짜 작품 수가 나온다.
    """
    a_count = int((artsy["name_norm"] == name_norm).sum())
    s_count = int((saatchi["name_norm"] == name_norm).sum())
    return {"artsy_works": a_count, "saatchi_works": s_count, "total_works": a_count + s_count}


def predict_with_source(
    predictor: PrimaryPredictor,
    base_features: dict,
    artist_slug: str,
    source: str,
) -> dict:
    """주어진 source 라벨로 예측. 다른 모든 입력은 동일."""
    features = {**base_features, "source": source}
    is_matched = predictor.is_warm_artist(artist_slug)
    # training_count는 라우팅엔 영향 없음 (warm_artist_slugs 우선) — 0으로 둠
    result = predictor.predict(
        features=features,
        is_matched=True,
        training_count=0,
        target_market=TARGET_MARKET,
        has_manual_profile=False,
        artist_slug=artist_slug,
    )
    # 적용된 cell factor 추출 (cold일 때만)
    cell = f"{source}_{TARGET_MARKET}"
    factor = predictor._cold_calibration_factors.get(cell, 1.0) if "catboost" in result["model_type"] else 1.0
    result["applied_cell_factor"] = factor
    return result


def run_experiment() -> dict:
    artsy, saatchi = load_sources()
    warm_slugs = _load_warm_slugs() if WARM_ONLY else None
    if WARM_ONLY:
        logger.info("WARM_ONLY=1 — warm 라우팅 작가만 코호트에 포함 (n=%d slugs)", len(warm_slugs))
    cohorts = build_cohorts(artsy, saatchi, warm_slugs=warm_slugs)

    predictor = PrimaryPredictor()
    predictor.load_models(OUT_DIR)

    results: dict[str, list[dict]] = {}
    for cohort_name, rows in cohorts.items():
        cohort_out = []
        for r in rows:
            base = features_dict_from_row(r["row"])
            pred_artsy = predict_with_source(predictor, base, r["artist_slug"], "artsy")
            pred_saatchi = predict_with_source(predictor, base, r["artist_slug"], "saatchi")

            p_a = pred_artsy["price_krw"]
            p_s = pred_saatchi["price_krw"]
            f_a = pred_artsy["applied_cell_factor"]
            f_s = pred_saatchi["applied_cell_factor"]
            # raw 가격 = calibration 적용 전 (cell factor 역산)
            raw_a = p_a / f_a if f_a > 0 else p_a
            raw_s = p_s / f_s if f_s > 0 else p_s

            tcounts = count_training_works(r["name_norm"], artsy, saatchi)
            diag = diagnostic_fields(r["row"])

            cohort_out.append({
                "artist_name": r["artist_name"],
                "artist_slug": r["artist_slug"],
                "source_side_origin": r["source_side"],
                "training_count_artsy": tcounts["artsy_works"],
                "training_count_saatchi": tcounts["saatchi_works"],
                "training_count_total": tcounts["total_works"],
                "actual_price_krw": r["actual_price_krw"],
                "actual_ln_price": r["actual_ln_price"],
                # calibrated (서빙 출력)
                "price_krw_artsy": p_a,
                "price_krw_saatchi": p_s,
                # raw (cell calibration 적용 전 = pure 모델 출력)
                "raw_price_krw_artsy": int(round(raw_a)),
                "raw_price_krw_saatchi": int(round(raw_s)),
                # 비교 지표
                "ratio_saatchi_over_artsy": p_s / p_a if p_a > 0 else None,
                "delta_pct": (p_s - p_a) / p_a * 100 if p_a > 0 else None,
                "raw_ratio_saatchi_over_artsy": raw_s / raw_a if raw_a > 0 else None,
                "raw_delta_pct": (raw_s - raw_a) / raw_a * 100 if raw_a > 0 else None,
                # 라우팅 / 보정
                "model_type": pred_artsy["model_type"],
                "applied_cell_factor_artsy": f_a,
                "applied_cell_factor_saatchi": f_s,
                "model_type_artsy": pred_artsy["model_type"],
                "model_type_saatchi": pred_saatchi["model_type"],
                # 진단 피처
                "diagnostic": diag,
            })
        results[cohort_name] = cohort_out

    return results


def _quantiles(values: list[float], qs: list[float]) -> dict[str, float]:
    if not values:
        return {f"p{int(q*100)}": None for q in qs}
    arr = np.asarray(values, dtype=float)
    return {f"p{int(q*100)}": float(np.quantile(arr, q)) for q in qs}


def _mad(values: list[float]) -> float:
    if not values:
        return 0.0
    arr = np.asarray(values, dtype=float)
    return float(np.median(np.abs(arr - np.median(arr))))


def _sign_distribution(deltas: list[float], thr: float = 0.1) -> dict[str, int]:
    """delta% 부호 분포 — abs ≤ thr는 zero로 간주."""
    pos = sum(1 for d in deltas if d > thr)
    neg = sum(1 for d in deltas if d < -thr)
    zero = sum(1 for d in deltas if -thr <= d <= thr)
    return {"positive": pos, "near_zero": zero, "negative": neg}


def _delta_histogram(deltas: list[float]) -> dict[str, int]:
    """delta% 분포를 7개 버킷으로 카운트."""
    buckets = {
        "<-5%": 0, "-5~-2%": 0, "-2~-0.5%": 0,
        "-0.5~+0.5%": 0, "+0.5~+2%": 0, "+2~+5%": 0, ">+5%": 0,
    }
    for d in deltas:
        if d < -5: buckets["<-5%"] += 1
        elif d < -2: buckets["-5~-2%"] += 1
        elif d < -0.5: buckets["-2~-0.5%"] += 1
        elif d <= 0.5: buckets["-0.5~+0.5%"] += 1
        elif d <= 2: buckets["+0.5~+2%"] += 1
        elif d <= 5: buckets["+2~+5%"] += 1
        else: buckets[">+5%"] += 1
    return buckets


def summarize(results: dict[str, list[dict]]) -> dict:
    summary = {}
    for cohort_name, rows in results.items():
        ratios = [r["ratio_saatchi_over_artsy"] for r in rows if r["ratio_saatchi_over_artsy"] is not None]
        deltas = [r["delta_pct"] for r in rows if r["delta_pct"] is not None]
        raw_deltas = [r["raw_delta_pct"] for r in rows if r["raw_delta_pct"] is not None]
        abs_deltas = [abs(d) for d in deltas]
        model_types = sorted({r["model_type"] for r in rows})
        same_routing = all(r["model_type_artsy"] == r["model_type_saatchi"] for r in rows)
        summary[cohort_name] = {
            "n": len(rows),
            # ratio (calibrated)
            "ratio_mean": float(np.mean(ratios)) if ratios else None,
            "ratio_median": float(np.median(ratios)) if ratios else None,
            "ratio_std": float(np.std(ratios, ddof=1)) if len(ratios) > 1 else 0.0,
            "ratio_min": float(np.min(ratios)) if ratios else None,
            "ratio_max": float(np.max(ratios)) if ratios else None,
            # delta% (calibrated)
            "delta_pct_mean": float(np.mean(deltas)) if deltas else None,
            "delta_pct_median": float(np.median(deltas)) if deltas else None,
            "delta_pct_std": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
            "delta_pct_mad": _mad(deltas),
            "delta_pct_quantiles": _quantiles(deltas, [0.1, 0.25, 0.5, 0.75, 0.9]),
            "abs_delta_pct_mean": float(np.mean(abs_deltas)) if abs_deltas else None,
            "abs_delta_pct_max": float(np.max(abs_deltas)) if abs_deltas else None,
            # raw (calibration 제외, 순수 모델 효과)
            "raw_delta_pct_mean": float(np.mean(raw_deltas)) if raw_deltas else None,
            "raw_delta_pct_median": float(np.median(raw_deltas)) if raw_deltas else None,
            # 부호 분포 (|d|≤0.1% = near_zero)
            "sign_distribution": _sign_distribution(deltas, thr=0.1),
            # 히스토그램
            "delta_histogram": _delta_histogram(deltas),
            # 라우팅
            "model_types_seen": model_types,
            "routing_invariant_under_flip": same_routing,
        }
    return summary


def _render_histogram(buckets: dict[str, int], width: int = 30) -> list[str]:
    """delta% 히스토그램 텍스트 시각화."""
    total = sum(buckets.values()) or 1
    max_count = max(buckets.values()) or 1
    out = []
    for label, count in buckets.items():
        bar_len = int(count / max_count * width)
        bar = "█" * bar_len
        pct = count / total * 100
        out.append(f"  {label:>10s} | {bar:<{width}s} {count:>3d}건 ({pct:5.1f}%)")
    return out


def write_report(results: dict[str, list[dict]], summary: dict, out_md: Path) -> None:
    lines: list[str] = []
    title_suffix = " (warm-only)" if WARM_ONLY else ""
    lines.append(f"# Source Flip Experiment — Artsy ↔ Saatchi{title_suffix}\n")
    lines.append(f"- 실험: 같은 작품 features에 source 라벨만 플립")
    lines.append(f"- target_market: `{TARGET_MARKET}` 고정")
    lines.append(f"- random_state: {SEED}")
    lines.append(f"- 작품 선정: 작가별 ln_price 중앙값에 가장 가까운 1점")
    lines.append(f"- WARM_ONLY: `{WARM_ONLY}`\n")

    cohort_titles = {
        "both": "코호트 A — Artsy ∩ Saatchi (양쪽 학습)",
        "artsy_only": "코호트 B — Artsy only (Artsy 학습에만)",
        "saatchi_only": "코호트 C — Saatchi only (Saatchi 학습에만)",
    }

    # ─── 1. 코호트별 핵심 요약 ────────────────────────────────────────
    lines.append("## 1. 코호트별 핵심 요약\n")
    lines.append("| 코호트 | n | ratio 평균 | ratio 중앙 | ratio σ | delta% 평균 | delta% 중앙 | |delta|% 평균 | |delta|% 최대 | 라우팅 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for k, title in cohort_titles.items():
        s = summary[k]
        routing = ", ".join(s["model_types_seen"])
        lines.append(
            f"| {title} | {s['n']} | {s['ratio_mean']:.4f} | {s['ratio_median']:.4f} | {s['ratio_std']:.4f} "
            f"| {s['delta_pct_mean']:+.2f}% | {s['delta_pct_median']:+.2f}% "
            f"| {s['abs_delta_pct_mean']:.2f}% | {s['abs_delta_pct_max']:.2f}% | {routing} |"
        )
    lines.append("")
    lines.append("> ratio = price(source=saatchi) / price(source=artsy)  ·  delta% = (saatchi − artsy) / artsy × 100")
    lines.append("> raw vs calibrated: cold 라우팅(CatBoost)일 때만 cell calibration 적용. raw_delta는 calibration 제거 후 순수 모델 효과.\n")

    # ─── 2. 분포 통계 ────────────────────────────────────────────────
    lines.append("## 2. delta% 분포 통계\n")
    lines.append("| 코호트 | p10 | p25 | p50 | p75 | p90 | std | MAD | raw delta 평균 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for k, title in cohort_titles.items():
        s = summary[k]
        q = s["delta_pct_quantiles"]
        lines.append(
            f"| {title} "
            f"| {q['p10']:+.2f}% | {q['p25']:+.2f}% | {q['p50']:+.2f}% | {q['p75']:+.2f}% | {q['p90']:+.2f}% "
            f"| {s['delta_pct_std']:.2f}% | {s['delta_pct_mad']:.2f}% | {s['raw_delta_pct_mean']:+.2f}% |"
        )
    lines.append("")

    # ─── 3. 부호 분포 ────────────────────────────────────────────────
    lines.append("## 3. 부호 분포 (|delta|≤0.1%는 near_zero)\n")
    lines.append("| 코호트 | n | saatchi↑ (positive) | ≈0 (near_zero) | saatchi↓ (negative) |")
    lines.append("|---|---|---|---|---|")
    for k, title in cohort_titles.items():
        s = summary[k]
        sd = s["sign_distribution"]
        n = s["n"]
        lines.append(
            f"| {title} | {n} "
            f"| {sd['positive']} ({sd['positive']/n*100:.0f}%) "
            f"| {sd['near_zero']} ({sd['near_zero']/n*100:.0f}%) "
            f"| {sd['negative']} ({sd['negative']/n*100:.0f}%) |"
        )
    lines.append("")

    # ─── 4. delta% 히스토그램 ────────────────────────────────────────
    lines.append("## 4. delta% 히스토그램 (코호트별)\n")
    for k, title in cohort_titles.items():
        s = summary[k]
        lines.append(f"### {title}\n")
        lines.append("```")
        lines.extend(_render_histogram(s["delta_histogram"]))
        lines.append("```\n")

    # ─── 5. 작가별 상세 (진단 피처 포함) ──────────────────────────────
    lines.append("## 5. 작가별 상세 (진단 피처 포함)\n")
    for k, title in cohort_titles.items():
        lines.append(f"### {title}\n")
        lines.append(
            "| 작가 | slug | tr.cnt(a/s) | model | actual | "
            "price(artsy) | price(saatchi) | delta% | "
            "raw delta% | factor(a) | factor(s) | "
            "ho | medium | birth | career | ln_followers |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in results[k]:
            d = r["diagnostic"]
            tc_a = r["training_count_artsy"]
            tc_s = r["training_count_saatchi"]
            birth = int(d["artist_birth_year"]) if d["artist_birth_year"] else "-"
            lnf = f"{d['ln_followers']:.2f}" if d["ln_followers"] is not None else "-"
            lines.append(
                f"| {r['artist_name']} | `{r['artist_slug']}` | {tc_a}/{tc_s} | {r['model_type'].replace('_v3_filtered_tuned','')} "
                f"| {r['actual_price_krw']:,} | {r['price_krw_artsy']:,} | {r['price_krw_saatchi']:,} "
                f"| {r['delta_pct']:+.2f}% | {r['raw_delta_pct']:+.2f}% "
                f"| {r['applied_cell_factor_artsy']:.4f} | {r['applied_cell_factor_saatchi']:.4f} "
                f"| {d['ho']} | {d['medium_category']} | {birth} | {d['career_stage']} | {lnf} |"
            )
        lines.append("")

    # ─── 6. 가장 영향 큰/작은 작가 Top 5 ──────────────────────────────
    lines.append("## 6. |delta|% 기준 Top 5 (영향 가장 큰 작가)\n")
    all_rows = []
    for k, rows in results.items():
        for r in rows:
            all_rows.append({**r, "_cohort": k})
    top5 = sorted(all_rows, key=lambda x: abs(x["delta_pct"] or 0), reverse=True)[:5]
    bottom5 = sorted(all_rows, key=lambda x: abs(x["delta_pct"] or 0))[:5]

    def _mini_table(rows: list[dict]) -> list[str]:
        out = ["| 코호트 | 작가 | model | delta% | raw delta% |",
               "|---|---|---|---|---|"]
        for r in rows:
            cohort_short = {"both":"A", "artsy_only":"B", "saatchi_only":"C"}[r["_cohort"]]
            mt = r["model_type"].replace("_v3_filtered_tuned", "")
            out.append(
                f"| {cohort_short} | {r['artist_name']} | {mt} "
                f"| {r['delta_pct']:+.2f}% | {r['raw_delta_pct']:+.2f}% |"
            )
        return out

    lines.extend(_mini_table(top5))
    lines.append("")
    lines.append("## 7. |delta|% 기준 Bottom 5 (영향 가장 작은 작가)\n")
    lines.extend(_mini_table(bottom5))
    lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Report 저장: %s", out_md)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    results = run_experiment()
    summary = summarize(results)

    suffix = "_warm" if WARM_ONLY else ""
    out_json = OUT_DIR / f"source_flip_results{suffix}.json"
    payload = {
        "config": {
            "seed": SEED,
            "n_per_cohort": N_PER_COHORT,
            "target_market": TARGET_MARKET,
            "warm_only": WARM_ONLY,
        },
        "summary": summary,
        "results": results,
    }
    out_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("JSON 저장: %s", out_json)

    write_report(results, summary, OUT_DIR / f"source_flip_report{suffix}.md")

    # 콘솔 요약
    print("\n=== Summary ===")
    for k, s in summary.items():
        print(f"[{k}] n={s['n']}  ratio mean={s['ratio_mean']:.4f}  "
              f"delta%={s['delta_pct_mean']:+.2f}  routing={','.join(s['model_types_seen'])}")


if __name__ == "__main__":
    main()
