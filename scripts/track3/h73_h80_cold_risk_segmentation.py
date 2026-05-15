"""Track 3 H73-H80 Cold risk segmentation.

Goal:
- Check whether Cold price-range width can be reduced by splitting Cold works
  into operationally definable low/high-risk groups.
- Risk definitions must not use test residuals.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from h34_h43_followup_validation import (
    ARTIST_COL,
    COLD_3D_FEATURES,
    COLD_BASE_FEATURES,
    REPO,
    SPLIT,
    TARGET,
    add_features,
    add_history,
    build_artist_history,
    build_lad,
    metric,
)
from h70_h72_operational_revalidation import split_cold_calibration


OUT_PATH = REPO / "data" / "track3_h73_h80_cold_risk_segmentation_results.json"
DATE = "2026-05-15"


def prepare(train_raw: pd.DataFrame, *frames: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    prepared = [add_history(add_features(frame), hist, global_values) for frame in frames]
    return train, prepared


def cold_h32_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    base = build_lad(COLD_BASE_FEATURES)
    base.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    base_pred = base.predict(test[COLD_BASE_FEATURES])

    model_3d = build_lad(COLD_3D_FEATURES)
    model_3d.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    pred_3d = model_3d.predict(test[COLD_3D_FEATURES])

    mask_3d = test["is_3d_work"].eq(1).to_numpy()
    pred = base_pred.copy()
    pred[mask_3d] = pred_3d[mask_3d]
    return pred


def abs_log_error(df: pd.DataFrame, pred: np.ndarray) -> np.ndarray:
    return np.abs(pred - df[TARGET].values)


def price_multiplier(width_abs_log: float) -> float:
    return float(np.exp(width_abs_log))


def train_thresholds(train: pd.DataFrame, cal_pred: np.ndarray | None = None) -> dict[str, float]:
    thresholds = {
        "log_area_q80": float(train["log_area"].quantile(0.80)),
        "log_area_q90": float(train["log_area"].quantile(0.90)),
        "ho_area_gap_q80": float(train["ho_area_gap_abs"].quantile(0.80)),
        "ho_area_gap_q90": float(train["ho_area_gap_abs"].quantile(0.90)),
        "estimated_ho_q80": float(train["estimated_ho"].quantile(0.80)),
        "estimated_ho_q90": float(train["estimated_ho"].quantile(0.90)),
    }
    if cal_pred is not None:
        thresholds["pred_ln_q20"] = float(np.quantile(cal_pred, 0.20))
        thresholds["pred_ln_q80"] = float(np.quantile(cal_pred, 0.80))
    return thresholds


def common_category_values(train: pd.DataFrame, col: str, min_count: int) -> set[str]:
    counts = train[col].fillna("unknown").astype(str).value_counts()
    return set(counts[counts >= min_count].index)


def candidate_masks(df: pd.DataFrame, thresholds: dict[str, float], common_mediums: set[str], common_supports: set[str], pred: np.ndarray) -> dict[str, dict]:
    is_3d = df["is_3d_work"].eq(1).to_numpy()
    large_ho = df["is_large_ho"].eq(1).to_numpy()
    extra_large_ho = df["is_extra_large_ho"].eq(1).to_numpy()
    very_large_area = df["is_very_large_area"].eq(1).to_numpy()
    extreme_area = df["log_area"].ge(thresholds["log_area_q90"]).to_numpy()
    large_area = df["log_area"].ge(thresholds["log_area_q80"]).to_numpy()
    high_gap = df["ho_area_gap_abs"].ge(thresholds["ho_area_gap_q80"]).to_numpy()
    extreme_gap = df["ho_area_gap_abs"].ge(thresholds["ho_area_gap_q90"]).to_numpy()
    high_pred = pred >= thresholds["pred_ln_q80"]
    low_pred = pred <= thresholds["pred_ln_q20"]
    common_medium = df["medium_category"].fillna("unknown").astype(str).isin(common_mediums).to_numpy()
    common_support = df["support_category"].fillna("unknown").astype(str).isin(common_supports).to_numpy()

    low_size = ~(large_ho | extra_large_ho | very_large_area | extreme_area)
    low_consistency = ~high_gap
    common_material = common_medium & common_support
    standard_2d = (~is_3d) & low_size
    standard_3d = is_3d & low_size
    mid_pred = ~(low_pred | high_pred)
    conservative_low = low_size & low_consistency & common_material & mid_pred

    risk_score = (
        large_ho.astype(int)
        + extra_large_ho.astype(int)
        + very_large_area.astype(int)
        + extreme_area.astype(int)
        + high_gap.astype(int)
        + high_pred.astype(int)
        + (~common_material).astype(int)
    )

    return {
        "all": {
            "hypothesis": "baseline",
            "description": "전체 Cold",
            "mask": np.ones(len(df), dtype=bool),
        },
        "H73_size_low_risk": {
            "hypothesis": "H73",
            "description": "대형 호수/초대형 면적/상위 10% 면적이 아닌 작품",
            "mask": low_size,
        },
        "H73_size_high_risk": {
            "hypothesis": "H73",
            "description": "대형 호수 또는 초대형 면적 또는 상위 10% 면적 작품",
            "mask": ~low_size,
        },
        "H74_standard_2d": {
            "hypothesis": "H74",
            "description": "2D이면서 크기 극단값이 아닌 작품",
            "mask": standard_2d,
        },
        "H74_standard_3d": {
            "hypothesis": "H74",
            "description": "3D이면서 크기 극단값이 아닌 작품",
            "mask": standard_3d,
        },
        "H75_common_material_low_risk": {
            "hypothesis": "H75",
            "description": "train에서 충분히 자주 나온 재료/바탕 조합",
            "mask": common_material,
        },
        "H75_rare_material_high_risk": {
            "hypothesis": "H75",
            "description": "희소 재료 또는 희소 바탕",
            "mask": ~common_material,
        },
        "H76_mid_pred_price": {
            "hypothesis": "H76",
            "description": "calibration 예측값 기준 중간 60% 가격대",
            "mask": mid_pred,
        },
        "H76_low_or_high_pred_price": {
            "hypothesis": "H76",
            "description": "calibration 예측값 기준 하위 20% 또는 상위 20% 가격대",
            "mask": low_pred | high_pred,
        },
        "H77_consistent_size_ho": {
            "hypothesis": "H77",
            "description": "면적-호수 불일치가 train 상위 20%가 아닌 작품",
            "mask": low_consistency,
        },
        "H77_inconsistent_size_ho": {
            "hypothesis": "H77",
            "description": "면적-호수 불일치가 train 상위 20% 이상인 작품",
            "mask": high_gap,
        },
        "H78_combined_low_risk": {
            "hypothesis": "H78",
            "description": "크기 안정 + 면적/호수 일관 + 흔한 재료/바탕 + 중간 예측 가격대",
            "mask": conservative_low,
        },
        "H78_combined_high_risk": {
            "hypothesis": "H78",
            "description": "복합 위험 점수 2점 이상",
            "mask": risk_score >= 2,
        },
        "H79_extreme_outlier_flag": {
            "hypothesis": "H79",
            "description": "면적/호수 불일치 상위 10% 또는 상위 10% 면적",
            "mask": extreme_gap | extreme_area,
        },
        "H80_selective_service_candidate": {
            "hypothesis": "H80",
            "description": "서비스 후보: 복합 low-risk 또는 표준 3D",
            "mask": conservative_low | standard_3d,
        },
    }


def evaluate_group(df: pd.DataFrame, pred: np.ndarray, mask: np.ndarray, cal_width: float | None = None) -> dict | None:
    n = int(mask.sum())
    if n < 20:
        return None
    err = abs_log_error(df.loc[mask], pred[mask])
    out = {
        "n": n,
        "share": float(n / len(df)),
        "metric": metric(df.loc[mask, TARGET].values, pred[mask]),
        "q80_abs_log_error": float(np.quantile(err, 0.80)),
        "q80_price_multiplier": price_multiplier(float(np.quantile(err, 0.80))),
        "q90_abs_log_error": float(np.quantile(err, 0.90)),
        "q90_price_multiplier": price_multiplier(float(np.quantile(err, 0.90))),
    }
    if cal_width is not None:
        out["cal_width_abs_log"] = float(cal_width)
        out["cal_price_multiplier"] = price_multiplier(cal_width)
        out["test_coverage_with_cal_width"] = float(np.mean(err <= cal_width))
    return out


def run() -> dict:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")

    cold_core_raw, cold_cal_raw = split_cold_calibration(train_raw)
    cold_core, [cold_cal] = prepare(cold_core_raw, cold_cal_raw)
    cal_pred = cold_h32_predict(cold_core, cold_cal)

    full_train, [cold] = prepare(train_raw, cold_raw)
    cold_pred = cold_h32_predict(full_train, cold)

    thresholds = train_thresholds(full_train, cal_pred=cal_pred)
    common_mediums = common_category_values(full_train, "medium_category", min_count=200)
    common_supports = common_category_values(full_train, "support_category", min_count=200)

    cal_masks = candidate_masks(cold_cal, thresholds, common_mediums, common_supports, cal_pred)
    test_masks = candidate_masks(cold, thresholds, common_mediums, common_supports, cold_pred)

    cal_widths = {}
    for name, item in cal_masks.items():
        mask = item["mask"]
        if int(mask.sum()) < 20:
            continue
        err = abs_log_error(cold_cal.loc[mask], cal_pred[mask])
        cal_widths[name] = float(np.quantile(err, 0.80))

    groups = {}
    for name, item in test_masks.items():
        row = evaluate_group(cold, cold_pred, item["mask"], cal_widths.get(name))
        if row is None:
            continue
        row["hypothesis"] = item["hypothesis"]
        row["description"] = item["description"]
        groups[name] = row

    all_width = groups["all"]["cal_price_multiplier"]
    service_candidates = {
        name: row
        for name, row in groups.items()
        if name != "all"
        and row["share"] >= 0.15
        and row.get("test_coverage_with_cal_width", 0) >= 0.75
        and row.get("cal_price_multiplier", 99) < all_width
    }
    best_by_width = sorted(
        service_candidates.items(),
        key=lambda kv: (kv[1]["cal_price_multiplier"], -kv[1]["share"]),
    )[:8]

    return {
        "experiment_id": "H73_H80_cold_risk_segmentation",
        "date": DATE,
        "data": {
            "train_rows": int(len(train_raw)),
            "cold_rows": int(len(cold_raw)),
            "internal_cold_calibration_rows": int(len(cold_cal)),
            "internal_cold_calibration_artists": int(cold_cal[ARTIST_COL].nunique()),
        },
        "model_policy": "H32 Cold conditional fallback",
        "thresholds_source": "train/calibration only; no test residuals used for group definitions",
        "thresholds": thresholds,
        "common_mediums_min_count_200": sorted(common_mediums),
        "common_supports_min_count_200": sorted(common_supports),
        "groups": groups,
        "best_service_candidates_by_width": [
            {"group": name, **row} for name, row in best_by_width
        ],
        "judgement": {
            "success_condition": "A low-risk group is useful if it keeps at least 15% of Cold rows, reaches >=0.75 test coverage with internal calibration width, and uses a narrower multiplier than all Cold.",
            "h73_h80": "Adopt only group definitions that meet the success condition and are explainable with production-available inputs.",
        },
    }


def main() -> None:
    result = run()
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("H73-H80 Cold risk segmentation")
    print(f"saved: {OUT_PATH}")
    print("all:", {
        "n": result["groups"]["all"]["n"],
        "cal_x": round(result["groups"]["all"]["cal_price_multiplier"], 3),
        "coverage": round(result["groups"]["all"]["test_coverage_with_cal_width"], 3),
    })
    print("best candidates:")
    for row in result["best_service_candidates_by_width"][:5]:
        print(
            row["group"],
            "n=", row["n"],
            "share=", round(row["share"], 3),
            "cal_x=", round(row["cal_price_multiplier"], 3),
            "cov=", round(row["test_coverage_with_cal_width"], 3),
            "medAPE=", round(row["metric"]["median_ape"], 4),
        )


if __name__ == "__main__":
    main()
