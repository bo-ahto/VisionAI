#!/usr/bin/env python3
"""Run Warm-lite unified current without fixed replay feature store.

목적:
    `fixed_replay_feature_store.csv`를 전혀 쓰지 않고, 현재 official 0.1v
    Warm-lite unified current 모델을 기존 Warm fixed test 607건에 대해 실행한다.

평가 데이터:
    `data/track6_split/track6_test_warm.csv`는 테스트 입력과 정답 라벨로만 쓴다.
    모델 입력 feature는 이 CSV의 저장된 feature row를 그대로 쓰지 않고,
    PriceEstimateRequest 형태로 다시 만든 뒤 adapter의 운영 feature builder가
    새로 계산한다.

차단한 경로:
    ReportModelProxyAdapter 초기화 후 `warm_lite_unified_feature_store`를 빈
    DataFrame으로 덮어쓴다. 따라서 `_lookup_warm_lite_unified_feature_store_row`
    는 항상 feature_store_not_available 상태가 되고, fixed replay row를
    사용할 수 없다.

사용되는 경로:
    - 사용자 입력값에서 width/height/depth/medium/support bucket 재계산
    - SQLite DB의 `artwork_price_observations` train 이력 조회
    - warm_lite_unified current 예측
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from visionai.price_engine.api.official_v0_1_report_adapters import ReportModelProxyAdapter  # noqa: E402
from visionai.price_engine.api.official_v0_1_schemas import (  # noqa: E402
    ArtistInput,
    ArtworkInput,
    Dimensions,
    MediumInput,
    PriceEstimateOptions,
    PriceEstimateRequest,
)


EXP = REPO / "experiments" / "track6" / "PP-WLITE-NOREPLAY_operational_feature_path"
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
TEST_CSV = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "data"
    / "training"
    / "track6_split"
    / "track6_test_warm.csv"
)
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def request_from_row(row: pd.Series) -> PriceEstimateRequest:
    """Build a service-style request without source_artwork_id.

    `source_artwork_id`와 `external_artwork_id`를 일부러 넣지 않는다.
    row id를 넣으면 fixed replay feature store lookup 조건이 될 수 있기 때문이다.
    """

    return PriceEstimateRequest(
        artwork=ArtworkInput(
            title=str(row.get("title_raw") or "") or None,
            artist=ArtistInput(
                artist_key=str(row["artist_key"]),
                selected_artist_key=str(row["artist_key"]),
                name_ko=str(row.get("artist_name_ko") or "") or None,
            ),
            year=None,
            category="Sculpture" if bool(row.get("is_3d_candidate")) else "Painting",
            dimensions=Dimensions(
                width_cm=safe_float(row.get("width_cm")),
                height_cm=safe_float(row.get("height_cm")),
                depth_cm=safe_float(row.get("depth_cm")),
            ),
            medium=MediumInput(
                medium_category=str(row.get("medium_category") or "unknown"),
                support_category=str(row.get("support_category") or "unknown"),
            ),
            artwork_url=None,
            source_artwork_id=None,
            external_artwork_id=None,
        ),
        options=PriceEstimateOptions(
            currency="KRW",
            include_comparable_samples=False,
            max_comparable_samples=0,
            include_calculation_steps=True,
            include_debug_fields=True,
        ),
    )


def metrics(frame: pd.DataFrame, pred_col: str = "pred_log") -> dict[str, Any]:
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_log = frame[pred_col].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log - actual_log) ** 2))),
        "APE_gt_1": int(np.sum(ape > 1.0)),
        "APE_gt_5": int(np.sum(ape > 5.0)),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    os.environ["PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY"] = "warm_lite_unified_current"

    test = pd.read_csv(TEST_CSV, low_memory=False)
    test = test[pd.to_numeric(test["artist_works_count_train"], errors="coerce").fillna(0) >= 1].copy()
    test = test.sort_values("_track6_row_id").reset_index(drop=True)

    adapter = ReportModelProxyAdapter(db_path=DB_PATH)

    # 핵심 차단: fixed_replay_feature_store.csv를 로드했더라도 이 실험에서는 쓰지 않는다.
    adapter.warm_lite_unified_feature_store = pd.DataFrame()

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, row in test.iterrows():
        request = request_from_row(row)
        try:
            result = adapter.predict_warm_lite_unified_current(request, str(row["artist_key"]))
            output = result.output
            store_status = output.get("fixed_replay_feature_store") or {}
            rows.append(
                {
                    "_track6_row_id": int(row["_track6_row_id"]),
                    "artist_key": str(row["artist_key"]),
                    "artist_name_ko": str(row.get("artist_name_ko") or ""),
                    "actual_price": float(row["price_krw"]),
                    "actual_log": float(row["ln_price_krw"]),
                    "pred_log": float(output["warm_lite_unified_current_pred_log"]),
                    "pred_price": int(output["warm_lite_unified_current_pred_price_krw"]),
                    "current_pred_log": float(output["current_pred_log"]),
                    "lgbq_full_q50": float(output["lgbq_full_q50"]),
                    "lgbq_lean_q50": float(output["lgbq_lean_q50"]),
                    "lgbq_full_lean_avg": float(output["lgbq_full_lean_avg"]),
                    "lgb_huber_residual_log": float(output["lgb_huber_residual_log"]),
                    "artist_history_n": int(output["artist_history_n"]),
                    "feature_store_found": bool(store_status.get("found")),
                    "feature_store_lookup_basis": str(store_status.get("lookup_basis") or ""),
                    "range_low_krw": result.low_krw,
                    "range_high_krw": result.high_krw,
                    "confidence_tier": result.confidence_tier,
                }
            )
        except Exception as exc:  # noqa: BLE001 - audit output should keep row-level failures
            errors.append(
                {
                    "idx": int(idx),
                    "_track6_row_id": int(row["_track6_row_id"]),
                    "artist_key": str(row["artist_key"]),
                    "error": repr(exc),
                }
            )

    pred = pd.DataFrame(rows)
    err = pd.DataFrame(errors)
    if not pred.empty:
        pred["abs_error_price"] = (pred["pred_price"] - pred["actual_price"]).abs()
        pred["APE"] = pred["abs_error_price"] / pred["actual_price"].clip(lower=1.0)
        pred["abs_log_error"] = (pred["pred_log"] - pred["actual_log"]).abs()

    summary = {
        "experiment_id": "PP-WLITE-NOREPLAY",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Warm-lite unified current fixed-test evaluation without fixed_replay_feature_store.csv",
        "test_csv_used_only_as_input_and_label": str(TEST_CSV.relative_to(REPO)),
        "db_path": str(DB_PATH.relative_to(REPO)),
        "fixed_replay_feature_store_disabled": True,
        "route_policy": "warm_lite_unified_current",
        "input_rows": int(len(test)),
        "predicted_rows": int(len(pred)),
        "error_rows": int(len(err)),
        "feature_store_hit_rows": int(pred["feature_store_found"].sum()) if not pred.empty else 0,
        "metrics": metrics(pred) if not pred.empty else {},
    }

    pred.to_csv(OUT / "no_replay_predictions.csv", index=False)
    err.to_csv(OUT / "no_replay_errors.csv", index=False)
    (ARTIFACTS / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-WLITE-NOREPLAY operational feature path",
            "",
            "## 목적",
            "",
            "`fixed_replay_feature_store.csv`를 쓰지 않고 Warm-lite unified current 모델을 실행했다.",
            "테스트 CSV는 평가 입력과 정답 라벨로만 사용했고, 모델 입력 feature는 API adapter의 운영 feature builder로 다시 계산했다.",
            "",
            "## 핵심 설정",
            "",
            "- fixed replay feature store: disabled by `adapter.warm_lite_unified_feature_store = pd.DataFrame()`",
            "- route policy: `warm_lite_unified_current`",
            f"- input rows: `{summary['input_rows']}`",
            f"- predicted rows: `{summary['predicted_rows']}`",
            f"- error rows: `{summary['error_rows']}`",
            f"- feature store hit rows: `{summary['feature_store_hit_rows']}`",
            "",
            "## Metrics",
            "",
            "```json",
            json.dumps(summary["metrics"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Outputs",
            "",
            "- `outputs/no_replay_predictions.csv`",
            "- `outputs/no_replay_errors.csv`",
            "- `artifacts/summary.json`",
            "",
        ]
    )
    (REPORTS / "result_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if len(err) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
