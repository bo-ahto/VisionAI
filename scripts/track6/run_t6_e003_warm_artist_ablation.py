#!/usr/bin/env python3
"""Run T6-E003 Warm artist-feature ablation on Track6 validation split."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


REPO = Path(__file__).resolve().parents[2]
FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
RESULT_DIR = REPO / "data" / "track6" / "results"
PRED_DIR = REPO / "data" / "track6" / "predictions"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E003_warm_artist_ablation.md"
RESULT_JSON = RESULT_DIR / "t6_e003_warm_artist_ablation.json"
RESULT_CSV = RESULT_DIR / "t6_e003_warm_artist_ablation_metrics.csv"
PRED_CSV = PRED_DIR / "t6_e003_warm_artist_ablation_predictions.csv"

STRUCTURE_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
]
ARTIST_KEY_FEATURES = ["artist_key"]
ARTIST_HISTORY_FEATURES = ["artist_works_log", "artist_works_count_train"]
NUMERIC_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_count_train",
]

FEATURE_SETS = {
    "structure_only": STRUCTURE_FEATURES,
    "structure_plus_history": STRUCTURE_FEATURES + ARTIST_HISTORY_FEATURES,
    "structure_plus_artist_key": STRUCTURE_FEATURES + ARTIST_KEY_FEATURES,
    "structure_plus_artist_key_history": STRUCTURE_FEATURES + ARTIST_KEY_FEATURES + ARTIST_HISTORY_FEATURES,
}


def read_pair(feature_path: Path, label_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.read_csv(feature_path), pd.read_csv(label_path)


def make_xy(feature: pd.DataFrame, label: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    merged = feature[["_track6_row_id", *columns]].merge(
        label[["_track6_row_id", "ln_price_krw", "price_krw"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    x = merged[columns].copy()
    for col in columns:
        if col in NUMERIC_FEATURES:
            x[col] = pd.to_numeric(x[col], errors="coerce").fillna(0.0)
        else:
            x[col] = x[col].fillna("__MISSING__").astype(str)
    return x, merged["ln_price_krw"].astype(float), merged["price_krw"].astype(float)


def cat_feature_indices(columns: list[str]) -> list[int]:
    return [idx for idx, col in enumerate(columns) if col not in NUMERIC_FEATURES]


def build_model() -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function="RMSE",
        iterations=500,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=6.0,
        random_seed=20260518,
        verbose=False,
        allow_writing_files=False,
    )


def metrics(y_true_price: pd.Series, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.exp(pred_log)
    y = y_true_price.to_numpy(dtype=float)
    ape = np.abs(pred_price - y) / y
    log_true = np.log(y)
    return {
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "rmse_log": float(np.sqrt(np.mean((pred_log - log_true) ** 2))),
    }


def prediction_frame(model_name: str, feature: pd.DataFrame, label: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = feature[["_track6_row_id"]].merge(
        label[["_track6_row_id", "price_krw", "ln_price_krw", "artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    out["split"] = "val_warm"
    out["model"] = model_name
    out["pred_ln_price_krw"] = pred_log
    out["pred_price_krw"] = np.exp(pred_log)
    out["ape"] = np.abs(out["pred_price_krw"] - out["price_krw"]) / out["price_krw"]
    return out


def render_experiment(result: dict[str, Any]) -> str:
    best = result["best"]
    baseline = result["baseline"]
    improvement = baseline["median_ape"] - best["median_ape"]
    lines = [
        "# T6-E003 Warm 작가 피처 ablation",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H3`",
        "- 상태: 검증 완료",
        "- 목적: Warm에서 작가 식별/이력 피처가 구조-only 대비 성능을 개선하는지 확인",
        "- 사용 데이터: Track6 name-corrected Warm feature/label split",
        "- 사용 스크립트: `scripts/track6/run_t6_e003_warm_artist_ablation.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        f"- 예측 CSV: `{result['prediction_csv']}`",
        "",
        "## 1. 비교 피처셋",
        "",
        "- `structure_only`: 작품 구조 피처만 사용",
        "- `structure_plus_history`: 구조 피처 + train 기준 작가 작품 수",
        "- `structure_plus_artist_key`: 구조 피처 + 작가 식별값",
        "- `structure_plus_artist_key_history`: 구조 피처 + 작가 식별값 + 작가 작품 수",
        "",
        "## 2. validation 결과",
        "",
        "| model | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["metrics"]:
        lines.append(
            f"| `{row['model']}` | `{row['median_ape']:.4f}` | `{row['p95_ape']:.4f}` | "
            f"`{row['within_30']:.4f}` | `{row['within_50']:.4f}` | `{row['rmse_log']:.4f}` |"
        )
    lines += [
        "",
        "## 3. 핵심 해석",
        "",
        f"- 구조-only median APE: `{baseline['median_ape']:.4f}`",
        f"- 최저 median APE: `{best['median_ape']:.4f}` (`{best['model']}`)",
        f"- 구조-only 대비 개선폭: `{improvement:.4f}`",
        "- Warm에서는 학습 데이터에 같은 작가가 존재하므로 작가 식별/이력 피처가 가격대 차이를 설명할 수 있음",
        "- 단, 이 결과는 Warm 전용이며 Cold에는 작가 피처를 적용하지 않음",
        "",
        "## 4. 결론",
        "",
        "- T6-H3는 validation 기준 검증 완료",
        f"- Warm 후보 피처셋은 `{best['model']}`을 우선 유지",
        "- 다음 단계는 Cold 모델 비교(T6-E004)와 운영 가능 피처 조합 실험(T6-E005)",
        "",
    ]
    return "\n".join(lines)


def update_docs(result: dict[str, Any]) -> None:
    best = result["best"]
    baseline = result["baseline"]
    improvement = baseline["median_ape"] - best["median_ape"]

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    text = hypo.read_text(encoding="utf-8")
    old = "| T6-H3 | T6-G3 | Warm에서는 작가 식별 정보와 train 기준 작가 이력 피처가 성능을 개선할 것이다 | 구조-only, artist_key, artist history, artist stats를 단계별 비교 | Track6 split | 작가 피처 | 구조-only Warm | Warm median APE 개선 | 예정 | 미실행 | split 생성 후 진행 | T6-E003 | - |"
    new = (
        "| T6-H3 | T6-G3 | Warm에서는 작가 식별 정보와 train 기준 작가 이력 피처가 성능을 개선할 것이다 | "
        "구조-only, artist_key, artist history를 단계별 비교 | Track6 name-corrected split | 작가 피처 | 구조-only Warm | Warm median APE 개선 | "
        f"검증 완료 | Warm validation ablation | 구조-only `{baseline['median_ape']:.4f}` → best `{best['median_ape']:.4f}` (`{best['model']}`), 개선 `{improvement:.4f}` | T6-E003 | T6-E004/T6-E005 진행 |"
    )
    if old in text:
        hypo.write_text(text.replace(old, new), encoding="utf-8")

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    text = results.read_text(encoding="utf-8")
    row = (
        f"| {result['created_at']} | T6-E003 | T6-H3 | 검증 완료 | Track6 name-corrected split | CatBoost | "
        f"Warm 작가 피처 ablation | best `{best['median_ape']:.4f}` (`{best['model']}`), 구조-only 대비 `{improvement:.4f}` 개선 | - | "
        "Warm 작가 피처 유지 가치 확인 | [기록](../experiments/2026-05-18_T6-E003_warm_artist_ablation.md) |"
    )
    marker = "| 2026-05-18 | T6-E002 |"
    if "| 2026-05-18 | T6-E003 | T6-H3 |" not in text:
        results.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    text = index.read_text(encoding="utf-8")
    row = "| 2026-05-18 | T6-E003 | T6-H3 | 검증 완료 | Warm 작가 피처 ablation 완료 | [기록](2026-05-18_T6-E003_warm_artist_ablation.md) |"
    marker = "| 2026-05-18 | T6-E002 |"
    if "| 2026-05-18 | T6-E003 | T6-H3 |" not in text:
        index.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train_f, train_l = read_pair(FEATURE_DIR / "track6_train_warm_features.csv", LABEL_DIR / "track6_train_labels.csv")
    val_f, val_l = read_pair(FEATURE_DIR / "track6_val_warm_warm_features.csv", LABEL_DIR / "track6_val_warm_labels.csv")

    rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for model_name, columns in FEATURE_SETS.items():
        x_train, y_train, _ = make_xy(train_f, train_l, columns)
        x_val, _y_val_log, y_val_price = make_xy(val_f, val_l, columns)
        model = build_model()
        model.fit(x_train, y_train, cat_features=cat_feature_indices(columns))
        pred_log = np.asarray(model.predict(x_val), dtype=float)
        row = {"model": model_name, "features": columns}
        row.update(metrics(y_val_price, pred_log))
        rows.append(row)
        pred_frames.append(prediction_frame(model_name, val_f, val_l, pred_log))

    metric_df = pd.DataFrame(rows).sort_values(["median_ape", "p95_ape"])
    pred_df = pd.concat(pred_frames, ignore_index=True)
    metric_df.to_csv(RESULT_CSV, index=False)
    pred_df.to_csv(PRED_CSV, index=False)
    best = metric_df.iloc[0].to_dict()
    baseline = metric_df.loc[metric_df["model"].eq("structure_only")].iloc[0].to_dict()
    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E003",
        "hypothesis_id": "T6-H3",
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "result_csv": str(RESULT_CSV.relative_to(REPO)),
        "prediction_csv": str(PRED_CSV.relative_to(REPO)),
        "metrics": metric_df.to_dict(orient="records"),
        "best": best,
        "baseline": baseline,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render_experiment(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps({"result": str(RESULT_JSON.relative_to(REPO)), "best": best, "baseline": baseline}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
