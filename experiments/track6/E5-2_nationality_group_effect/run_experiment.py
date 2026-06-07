#!/usr/bin/env python3
"""E5-2 nationality group effect analysis.

This experiment answers a narrower question than E5-1:
after controlling artwork size/material/support, which nationality groups show
different price levels or prediction error changes?
"""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, QuantileRegressor
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[3]
EXP_DIR = REPO / "experiments" / "track6" / "E5-2_nationality_group_effect"
SPLIT_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size_artist_name"
SEED = 20260521

BASE_FEATURES = ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"]
NATIONALITY_FEATURES = [*BASE_FEATURES, "artist_meta_nationality_norm", "artist_meta_nationality_is_missing"]
NUMERIC_FEATURES = ["ln_estimated_ho", "artist_meta_nationality_is_missing"]
LABEL_COLS = ["_track6_row_id", "price_krw", "ln_price_krw"]


def paths() -> dict[str, Path]:
    return {
        "train_features": SPLIT_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
        "train_labels": SPLIT_ROOT / "labels" / "track6_train_labels.csv",
        "warm_features": SPLIT_ROOT / "features" / "warm" / "track6_test_warm_warm_features.csv",
        "warm_labels": SPLIT_ROOT / "labels" / "track6_test_warm_labels.csv",
        "cold_features": SPLIT_ROOT / "features" / "cold" / "track6_test_cold_cold_features.csv",
        "cold_labels": SPLIT_ROOT / "labels" / "track6_test_cold_labels.csv",
    }


def copy_sources(srcs: dict[str, Path]) -> None:
    target = EXP_DIR / "source_data"
    target.mkdir(parents=True, exist_ok=True)
    for src in srcs.values():
        shutil.copy2(src, target / src.name)


def load_join(features_path: Path, labels_path: Path) -> pd.DataFrame:
    source_features = [*BASE_FEATURES, "artist_meta_nationality", "artist_meta_nationality_is_missing"]
    cols = sorted(set(["_track6_row_id", "estimated_ho", *source_features]))
    features = pd.read_csv(features_path, low_memory=False)
    labels = pd.read_csv(labels_path, low_memory=False)
    missing = [c for c in cols if c not in features.columns]
    if missing:
        raise ValueError(f"{features_path} missing columns: {missing}")
    df = features[cols].merge(labels[LABEL_COLS], on="_track6_row_id", how="inner")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    return df.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def normalize_frames(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    frames = [train.copy(), warm.copy(), cold.copy()]
    for frame in frames:
        for col in ["estimated_ho", "ln_estimated_ho", "artist_meta_nationality_is_missing"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        for col in ["nant_material_idx", "nant_tool", "nant_support", "artist_meta_nationality"]:
            frame[col] = frame[col].astype("string").fillna("__missing__").replace({"": "__missing__"})
            if col.endswith("_idx"):
                frame[col] = frame[col].str.replace(r"\.0$", "", regex=True)
        frame["artist_meta_nationality_norm"] = frame["artist_meta_nationality"].map(normalize_nationality)
        frame["ho_control_bucket"] = frame["estimated_ho"].map(make_ho_bucket)
        frame["control_key"] = (
            frame["ho_control_bucket"].astype(str)
            + " | material="
            + frame["nant_material_idx"].astype(str)
            + " | tool="
            + frame["nant_tool"].astype(str)
            + " | support="
            + frame["nant_support"].astype(str)
        )
    return tuple(frames)


def normalize_nationality(value: object) -> str:
    text = str(value).strip()
    lowered = text.lower().replace(",", " ")
    lowered = " ".join(lowered.split())
    if not lowered or lowered in {"nan", "none", "__missing__", "missing"}:
        return "__missing__"
    if "korea" in lowered or "korean" in lowered:
        return "Korea"
    if "japan" in lowered or "japanese" in lowered:
        return "Japan"
    if "thai" in lowered or "thailand" in lowered:
        return "Thailand"
    if "china" in lowered or "chinese" in lowered:
        return "China"
    if "usa" in lowered or "united states" in lowered or "american" in lowered:
        return "USA"
    if "france" in lowered or "french" in lowered:
        return "France"
    if "germany" in lowered or "german" in lowered:
        return "Germany"
    if "italy" in lowered or "italian" in lowered:
        return "Italy"
    return text


def make_ho_bucket(value: object) -> str:
    ho = pd.to_numeric(value, errors="coerce")
    if pd.isna(ho):
        return "missing_ho"
    if ho <= 5:
        return "ho_000_005"
    if ho <= 10:
        return "ho_006_010"
    if ho <= 30:
        return "ho_011_030"
    if ho <= 50:
        return "ho_031_050"
    if ho <= 100:
        return "ho_051_100"
    return "ho_101_plus"


def make_preprocess(features: list[str]) -> ColumnTransformer:
    numeric = [f for f in features if f in NUMERIC_FEATURES]
    categorical = [f for f in features if f not in numeric]
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    transformers = []
    if categorical:
        transformers.append(("cat", encoder, categorical))
    if numeric:
        transformers.append(
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric,
            )
        )
    return ColumnTransformer(transformers)


def fit_predict(model_kind: str, train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> np.ndarray:
    if model_kind == "Huber":
        model = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000)
    elif model_kind == "Quantile-LAD":
        model = QuantileRegressor(quantile=0.5, alpha=0.001, solver="highs")
    else:
        raise ValueError(model_kind)
    pipe = Pipeline([("preprocess", make_preprocess(features)), ("model", model)])
    pipe.fit(train[features], train["ln_price_krw"].to_numpy())
    return np.exp(pipe.predict(test[features]))


def add_predictions(train: pd.DataFrame, test: pd.DataFrame, scope: str, model_kind: str) -> pd.DataFrame:
    frame = test.copy()
    frame["scope"] = scope
    frame["model_name"] = model_kind
    for name, features in [("base", BASE_FEATURES), ("nationality", NATIONALITY_FEATURES)]:
        pred = np.clip(fit_predict(model_kind, train, frame, features), 1_000.0, None)
        frame[f"pred_{name}"] = pred
        frame[f"ape_{name}"] = np.abs(pred - frame["price_krw"].to_numpy()) / frame["price_krw"].to_numpy()
        frame[f"log_error_{name}"] = np.log(pred) - frame["ln_price_krw"].to_numpy()
    frame["ape_improvement"] = frame["ape_base"] - frame["ape_nationality"]
    return frame


def metrics(actual_price: pd.Series, actual_log: pd.Series, pred: pd.Series) -> dict[str, float]:
    pred = np.clip(pred.astype(float).to_numpy(), 1_000.0, None)
    price = actual_price.astype(float).to_numpy()
    pred_log = np.log(pred)
    ape = np.abs(pred - price) / price
    return {
        "R2": float(r2_score(actual_log.astype(float).to_numpy(), pred_log)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log.astype(float).to_numpy()) ** 2))),
        "MdAPE": float(np.median(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "MAPE": float(np.mean(ape)),
    }


def summarize_overall(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, sub in predictions.groupby("scope"):
        for model_col, label in [("pred_base", "통제 기준"), ("pred_nationality", "통제 기준 + 국적")]:
            rows.append(
                {
                    "scope": scope,
                    "model_name": sub["model_name"].iloc[0],
                    "comparison": label,
                    "n": len(sub),
                    **metrics(sub["price_krw"], sub["ln_price_krw"], sub[model_col]),
                }
            )
    return pd.DataFrame(rows)


def summarize_nationality(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (scope, nationality), sub in predictions.groupby(["scope", "artist_meta_nationality_norm"], dropna=False):
        if len(sub) < 5:
            continue
        rows.append(
            {
                "scope": scope,
                "artist_meta_nationality_norm": nationality,
                "n": int(len(sub)),
                "actual_median_price": float(sub["price_krw"].median()),
                "base_MdAPE": float(sub["ape_base"].median()),
                "nationality_MdAPE": float(sub["ape_nationality"].median()),
                "MdAPE_improvement": float(sub["ape_base"].median() - sub["ape_nationality"].median()),
                "base_p95_APE": float(np.quantile(sub["ape_base"], 0.95)),
                "nationality_p95_APE": float(np.quantile(sub["ape_nationality"], 0.95)),
                "Within_30_base": float(np.mean(sub["ape_base"] <= 0.30)),
                "Within_30_nationality": float(np.mean(sub["ape_nationality"] <= 0.30)),
            }
        )
    return pd.DataFrame(rows).sort_values(["scope", "n"], ascending=[True, False])


def summarize_within_control(predictions: pd.DataFrame) -> pd.DataFrame:
    comparable = predictions.groupby(["scope", "control_key"])["artist_meta_nationality_norm"].nunique()
    comparable = comparable[comparable >= 2].index
    filt = predictions.set_index(["scope", "control_key"]).loc[comparable].reset_index()
    rows = []
    for (scope, control_key, nationality), sub in filt.groupby(
        ["scope", "control_key", "artist_meta_nationality_norm"], dropna=False
    ):
        if len(sub) < 5:
            continue
        rows.append(
            {
                "scope": scope,
                "control_key": control_key,
                "artist_meta_nationality_norm": nationality,
                "n": int(len(sub)),
                "actual_median_price": float(sub["price_krw"].median()),
                "base_MdAPE": float(sub["ape_base"].median()),
                "nationality_MdAPE": float(sub["ape_nationality"].median()),
                "MdAPE_improvement": float(sub["ape_base"].median() - sub["ape_nationality"].median()),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["scope", "control_key", "n"], ascending=[True, True, False])


def fmt(value: float) -> str:
    return f"{value:.4f}" if pd.notna(value) else ""


def table_html(df: pd.DataFrame, limit: int | None = None) -> str:
    if df.empty:
        return "<p>표시할 데이터가 없습니다.</p>"
    use = df.head(limit) if limit else df
    header = "".join(f"<th>{html.escape(str(c))}</th>" for c in use.columns)
    body = []
    for row in use.itertuples(index=False):
        cells = []
        for value in row:
            if isinstance(value, float):
                value = fmt(value)
            cells.append(f"<td>{html.escape(str(value))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_html(overall: pd.DataFrame, by_nat: pd.DataFrame, within: pd.DataFrame, manifest: dict) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 E5-2 국적별 가격 차이와 오차 차이 확인</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    section {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    h1 {{ font-size: 34px; margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; margin-top: 14px; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 8px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
    li {{ margin: 7px 0; }}
  </style>
</head>
<body>
  <section>
    <h1>Track6 E5-2 국적별 가격 차이와 오차 차이 확인</h1>
    <ul>
      <li>목적: 국적값 자체에 따라 가격대와 예측 오차가 어떻게 달라지는지 확인</li>
      <li>기준 모델: <code>ln_estimated_ho + nant_material_idx + nant_tool + nant_support</code></li>
      <li>비교 모델: 기준 모델 + <code>artist_meta_nationality + artist_meta_nationality_is_missing</code></li>
      <li>Warm 모델: <code>Huber</code></li>
      <li>Cold 모델: <code>Quantile-LAD</code></li>
      <li>생성일: <code>{html.escape(manifest['created_at'])}</code></li>
    </ul>
  </section>
  <section>
    <h2>전체 비교</h2>
    {table_html(overall)}
  </section>
  <section>
    <h2>국적별 결과</h2>
    <ul>
      <li><code>MdAPE_improvement</code>가 양수면 국적 추가 후 대표 오차가 줄어든 것입니다.</li>
      <li>표본 수가 작은 국적은 참고용으로만 봅니다.</li>
    </ul>
    {table_html(by_nat, 80)}
  </section>
  <section>
    <h2>같은 작품 조건 안에서의 국적별 결과</h2>
    <ul>
      <li>조건 묶음: 호수 구간 + 난트 재료 + 난트 도구 + 난트 지지체</li>
      <li>같은 조건 묶음 안에 2개 이상의 국적이 있을 때만 표시합니다.</li>
    </ul>
    {table_html(within, 120)}
  </section>
</body>
</html>
"""


def write_data_files(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> dict[str, str]:
    data_dir = EXP_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    feature_cols = [
        "_track6_row_id",
        "estimated_ho",
        "artist_meta_nationality",
        *NATIONALITY_FEATURES,
        "ho_control_bucket",
        "control_key",
    ]
    files = {}
    for name, frame in [("train", train), ("test_warm", warm), ("test_cold", cold)]:
        feature_path = data_dir / f"{name}_features.csv"
        label_path = data_dir / f"{name}_labels.csv"
        frame[feature_cols].to_csv(feature_path, index=False)
        frame[LABEL_COLS].to_csv(label_path, index=False)
        files[f"{name}_features"] = str(feature_path.relative_to(REPO))
        files[f"{name}_labels"] = str(label_path.relative_to(REPO))
    return files


def main() -> None:
    for path in [EXP_DIR / "outputs", EXP_DIR / "logs", EXP_DIR / "data", EXP_DIR / "source_data"]:
        path.mkdir(parents=True, exist_ok=True)
    srcs = paths()
    copy_sources(srcs)
    train = load_join(srcs["train_features"], srcs["train_labels"])
    warm = load_join(srcs["warm_features"], srcs["warm_labels"])
    cold = load_join(srcs["cold_features"], srcs["cold_labels"])
    train, warm, cold = normalize_frames(train, warm, cold)
    generated_files = write_data_files(train, warm, cold)

    warm_pred = add_predictions(train, warm, "Warm", "Huber")
    cold_pred = add_predictions(train, cold, "Cold", "Quantile-LAD")
    predictions = pd.concat([warm_pred, cold_pred], ignore_index=True)

    overall = summarize_overall(predictions)
    by_nat = summarize_nationality(predictions)
    within = summarize_within_control(predictions)

    out = EXP_DIR / "outputs"
    predictions.to_csv(out / "predictions_with_nationality_effect.csv", index=False)
    overall.to_csv(out / "overall_comparison.csv", index=False)
    by_nat.to_csv(out / "nationality_group_summary.csv", index=False)
    within.to_csv(out / "controlled_condition_nationality_summary.csv", index=False)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "E5-2",
        "run_mode": "full_split_no_sampling",
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "seed": SEED,
        "base_features": BASE_FEATURES,
        "nationality_features": NATIONALITY_FEATURES,
        "nationality_feature_note": "artist_meta_nationality 원문을 artist_meta_nationality_norm으로 정규화해 사용했다.",
        "numeric_features": NUMERIC_FEATURES,
        "models": {"Warm": "Huber", "Cold": "Quantile-LAD"},
        "generated_files": generated_files,
        "source_files": {k: str(v.relative_to(REPO)) for k, v in srcs.items()},
        "rows": {"train": len(train), "test_warm": len(warm), "test_cold": len(cold)},
    }
    (out / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "result_sheet.html").write_text(render_html(overall, by_nat, within, manifest), encoding="utf-8")
    (EXP_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Track6 E5-2 국적별 가격 차이와 오차 차이 확인",
                "",
                f"- 학습 데이터: `{len(train):,}`건",
                f"- Warm 테스트: `{len(warm):,}`건",
                f"- Cold 테스트: `{len(cold):,}`건",
                "- 기준 모델: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support`",
                "- 비교 모델: 기준 모델 + `artist_meta_nationality + artist_meta_nationality_is_missing`",
                "- Warm 모델: `Huber`",
                "- Cold 모델: `Quantile-LAD`",
                "- 결과 HTML: `outputs/result_sheet.html`",
                "- 국적별 요약 CSV: `outputs/nationality_group_summary.csv`",
                "- 같은 조건 국적별 요약 CSV: `outputs/controlled_condition_nationality_summary.csv`",
                "",
                "## 해석 기준",
                "",
                "- `MdAPE_improvement`가 양수면 국적 추가 후 대표 오차가 줄어든 것이다.",
                "- 국적별 표본 수가 작으면 참고용으로만 본다.",
                "- 국적은 원인으로 단정하지 않고 후속 후보 피처로 판단한다.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (EXP_DIR / "logs" / "run.log").write_text(
        f"{manifest['created_at']} E5-2 nationality group effect completed. rows={manifest['rows']}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
