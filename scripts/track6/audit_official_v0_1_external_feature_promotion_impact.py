#!/usr/bin/env python3
"""Audit prediction impact of the approved external feature cache candidate.

This script does not modify the operational cache.  It compares Cold predictions
when the adapter uses the current external feature cache versus the approved
promotion candidate cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(REPO / ".cache" / "matplotlib"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

from visionai.price_engine.api.official_v0_1_report_adapters import (  # noqa: E402
    ReportModelProxyAdapter,
    _valid_normalized_search_name,
)
from visionai.price_engine.api.official_v0_1_schemas import PriceEstimateRequest  # noqa: E402


CURRENT_CACHE_PATH = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_artist_external_feature_cache.csv"
PROMOTED_CACHE_PATH = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_external_feature_promotion"
    / "approved_external_feature_cache_candidate.csv"
)
DIFF_PATH = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_external_feature_promotion"
    / "external_feature_promotion_diff.csv"
)
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_external_feature_promotion_impact"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_external_feature_promotion_impact.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_external_feature_promotion_impact.md"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def deterministic_rank(value: object) -> str:
    raw = str(value or "").encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def normalize_cache(cache: pd.DataFrame) -> pd.DataFrame:
    cache = cache.copy()
    for col in ["artist_name_ko_normalized", "artist_name_en_normalized"]:
        if col not in cache.columns:
            cache[col] = ""
        cache[col] = cache[col].map(_valid_normalized_search_name).astype("string").fillna("")
    if "artist_key" not in cache.columns:
        cache["artist_key"] = ""
    cache["artist_key"] = cache["artist_key"].astype("string").fillna("")
    return cache


def load_inputs(max_artists: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    current = normalize_cache(pd.read_csv(CURRENT_CACHE_PATH, low_memory=False))
    promoted = normalize_cache(pd.read_csv(PROMOTED_CACHE_PATH, low_memory=False))
    diff = pd.read_csv(DIFF_PATH, low_memory=False)
    diff["artist_key"] = diff["artist_key"].astype("string").fillna("")
    if max_artists and max_artists > 0 and len(diff) > max_artists:
        per_action = max(max_artists // max(diff["action"].nunique(), 1), 1)
        chunks = []
        for action, group in diff.groupby("action", dropna=False):
            ranked = group.assign(_rank=group["artist_key"].map(deterministic_rank)).sort_values("_rank")
            chunks.append(ranked.head(per_action).drop(columns=["_rank"]))
        sampled = pd.concat(chunks, ignore_index=True)
        if len(sampled) < max_artists:
            remaining = diff[~diff["artist_key"].isin(set(sampled["artist_key"]))]
            remaining = remaining.assign(_rank=remaining["artist_key"].map(deterministic_rank)).sort_values("_rank")
            sampled = pd.concat([sampled, remaining.head(max_artists - len(sampled)).drop(columns=["_rank"])], ignore_index=True)
        diff = sampled.head(max_artists)
    return current, promoted, diff


def request_for_artist(row: pd.Series) -> PriceEstimateRequest:
    name_ko = row.get("name_ko")
    name_en = row.get("name_en")
    artist_key = str(row.get("artist_key") or "")
    return PriceEstimateRequest(
        artwork={
            "title": "external feature promotion impact audit",
            "artist": {
                "artist_key": artist_key,
                "selected_artist_key": artist_key,
                "name_ko": None if pd.isna(name_ko) else str(name_ko),
                "name_en": None if pd.isna(name_en) else str(name_en),
            },
            "year": 2020,
            "category": "Painting",
            "dimensions": {"width_cm": 72.7, "height_cm": 60.6, "depth_cm": 0},
            "medium": {"medium_category": "painting", "support_category": "canvas"},
        },
        options={"include_debug_fields": True},
    )


def safe_pct_delta(left: int | None, right: int | None) -> float | None:
    if not left or left <= 0 or right is None:
        return None
    return (right - left) / left


def evaluate(max_artists: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    current, promoted, diff = load_inputs(max_artists)
    current_by_artist = current.set_index("artist_key", drop=False)
    promoted_by_artist = promoted.set_index("artist_key", drop=False)
    adapter = ReportModelProxyAdapter()
    rows: list[dict[str, Any]] = []
    warnings.filterwarnings("ignore", category=UserWarning)
    for _, diff_row in diff.iterrows():
        artist_key = str(diff_row["artist_key"])
        source_row = current_by_artist.loc[artist_key] if artist_key in current_by_artist.index else promoted_by_artist.loc[artist_key]
        if isinstance(source_row, pd.DataFrame):
            source_row = source_row.iloc[0]
        request = request_for_artist(source_row)

        adapter.cold_external_feature_cache = current
        current_result = adapter.predict_cold(request, artist_key)
        adapter.cold_external_feature_cache = promoted
        promoted_result = adapter.predict_cold(request, artist_key)

        current_price = current_result.price_krw
        promoted_price = promoted_result.price_krw
        pct_delta = safe_pct_delta(current_price, promoted_price)
        current_output = current_result.output
        promoted_output = promoted_result.output
        rows.append(
            {
                "artist_key": artist_key,
                "action": diff_row["action"],
                "name_ko": source_row.get("name_ko"),
                "name_en": source_row.get("name_en"),
                "current_price_krw": current_price,
                "promoted_candidate_price_krw": promoted_price,
                "price_delta_krw": None if current_price is None or promoted_price is None else promoted_price - current_price,
                "price_delta_pct": pct_delta,
                "abs_price_delta_pct": None if pct_delta is None else abs(pct_delta),
                "current_external_ready": current_output.get("external_feature_pipeline_ready"),
                "promoted_external_ready": promoted_output.get("external_feature_pipeline_ready"),
                "current_external_lookup_basis": current_output.get("external_feature_lookup_basis"),
                "promoted_external_lookup_basis": promoted_output.get("external_feature_lookup_basis"),
                "current_external_row_count": current_output.get("external_feature_row_count"),
                "promoted_external_row_count": promoted_output.get("external_feature_row_count"),
                "current_external_preview": json.dumps(current_output.get("external_feature_preview"), ensure_ascii=False, sort_keys=True),
                "promoted_external_preview": json.dumps(promoted_output.get("external_feature_preview"), ensure_ascii=False, sort_keys=True),
            }
        )

    result = pd.DataFrame(rows)
    valid = result["abs_price_delta_pct"].dropna()
    changed = result["price_delta_krw"].fillna(0).ne(0)
    external_loss = result["current_external_ready"].eq(True) & result["promoted_external_ready"].eq(False)
    summary = {
        "created_at": now_iso(),
        "mode": "sample" if max_artists and max_artists > 0 else "all",
        "max_artists": max_artists,
        "evaluated_rows": int(len(result)),
        "changed_prediction_rows": int(changed.sum()),
        "external_feature_loss_rows": int(external_loss.sum()),
        "mean_abs_price_delta_pct": float(valid.mean()) if not valid.empty else 0.0,
        "median_abs_price_delta_pct": float(valid.median()) if not valid.empty else 0.0,
        "p95_abs_price_delta_pct": float(valid.quantile(0.95)) if len(valid) > 1 else float(valid.max()) if not valid.empty else 0.0,
        "max_abs_price_delta_pct": float(valid.max()) if not valid.empty else 0.0,
        "rows_over_1pct_delta": int(result["abs_price_delta_pct"].fillna(0).gt(0.01).sum()),
        "rows_over_5pct_delta": int(result["abs_price_delta_pct"].fillna(0).gt(0.05).sum()),
        "current_cache_csv": str(CURRENT_CACHE_PATH.relative_to(REPO)),
        "promoted_cache_csv": str(PROMOTED_CACHE_PATH.relative_to(REPO)),
    }
    return result, summary


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# 공식 v0.1 외부 피처 승격 전 예측 영향 감사",
        "",
        f"- 작성일: {summary['created_at']}",
        f"- 실행 모드: `{summary['mode']}`",
        f"- 평가 row 수: {summary['evaluated_rows']:,}",
        "",
        "## 1. 결론",
        "",
        "- 운영 cache는 수정하지 않았다.",
        "- 현재 cache와 승인 후보 cache를 각각 사용해 같은 Cold 입력을 예측했다.",
        "- 승인 후보 cache에서 제외되는 작가는 전시/갤러리 외부 피처가 missing/default로 바뀔 수 있으므로, 실제 적용 전 전체 영향 감사를 먼저 봐야 한다.",
        "",
        "## 2. 영향 요약",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        f"| 예측값 변화 row | {summary['changed_prediction_rows']:,} |",
        f"| 외부 피처 coverage 상실 row | {summary['external_feature_loss_rows']:,} |",
        f"| 평균 절대 변화율 | {summary['mean_abs_price_delta_pct']:.4f} |",
        f"| 중앙 절대 변화율 | {summary['median_abs_price_delta_pct']:.4f} |",
        f"| p95 절대 변화율 | {summary['p95_abs_price_delta_pct']:.4f} |",
        f"| 최대 절대 변화율 | {summary['max_abs_price_delta_pct']:.4f} |",
        f"| 1% 초과 변화 row | {summary['rows_over_1pct_delta']:,} |",
        f"| 5% 초과 변화 row | {summary['rows_over_5pct_delta']:,} |",
        "",
        "## 3. 판단",
        "",
        "- 이 감사는 품질 낮은 외부 피처를 제거할 때 예측 가격이 얼마나 움직이는지 보는 사전 점검이다.",
        "- 변화폭이 크면 승인 후보 cache를 바로 적용하지 않고, 차단된 1,135건 중 실제로 개선 수집 가능한 작가를 먼저 보강한다.",
        "- 변화폭이 작고 안정적이면 `--apply` 적용 전 전체 작가 감사로 확장한다.",
        "",
        "## 4. 산출물",
        "",
        "- 상세 결과 CSV: `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion_impact/promotion_impact_rows.csv`",
        "- 감사 JSON: `docs/track6/experiments/price_prediction_official_v0_1_external_feature_promotion_impact.json`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-artists", type=int, default=300, help="0 means evaluate all artists in the promotion diff.")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    rows, summary = evaluate(args.max_artists)
    rows.to_csv(OUT_DIR / "promotion_impact_rows.csv", index=False)
    summary["impact_rows_csv"] = str((OUT_DIR / "promotion_impact_rows.csv").relative_to(REPO))
    summary["audit_json"] = str(DOC_JSON.relative_to(REPO))
    DOC_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
