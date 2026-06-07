#!/usr/bin/env python3
"""Run Track6 G10 low-history artist routing experiment.

G10 is a policy experiment, not a simple feature-addition experiment. It checks
whether Warm test rows with fewer train works are better handled by a Warm-style
artist model or a Cold-style artwork-only model.
"""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from fixed_variable_experiment_runner import calc_metrics, fit_predict


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size_artist_name"
EXP_DIR = REPO / "experiments" / "track6" / "G10_low_history_artist_routing"
OUT_DIR = EXP_DIR / "outputs"
DATA_DIR = EXP_DIR / "data"
SOURCE_DIR = EXP_DIR / "source_data"
PROMPT_DIR = EXP_DIR / "prompts"

ARTWORK_BASIC = ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"]
WARM_FEATURES = [*ARTWORK_BASIC, "artist_name_ko", "artist_works_log"]
COLD_FEATURES = ARTWORK_BASIC
NUMERIC_FEATURES = ["ln_estimated_ho", "artist_works_log"]


PATHS = {
    "train_features": SPLIT_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
    "train_labels": SPLIT_ROOT / "labels" / "track6_train_labels.csv",
    "warm_features": SPLIT_ROOT / "features" / "warm" / "track6_test_warm_warm_features.csv",
    "warm_labels": SPLIT_ROOT / "labels" / "track6_test_warm_labels.csv",
    "cold_features": SPLIT_ROOT / "features" / "cold" / "track6_test_cold_cold_features.csv",
    "cold_labels": SPLIT_ROOT / "labels" / "track6_test_cold_labels.csv",
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_join(feature_path: Path, label_path: Path, columns: list[str]) -> pd.DataFrame:
    features = pd.read_csv(feature_path, low_memory=False)
    missing = [col for col in columns if col not in features.columns]
    if missing:
        raise ValueError(f"{feature_path} missing columns: {missing}")
    labels = pd.read_csv(label_path, low_memory=False)
    frame = features.merge(labels[["_track6_row_id", "price_krw", "ln_price_krw"]], on="_track6_row_id", how="inner")
    frame["price_krw"] = pd.to_numeric(frame["price_krw"], errors="coerce")
    frame["ln_price_krw"] = pd.to_numeric(frame["ln_price_krw"], errors="coerce")
    return frame.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in features:
        if col in NUMERIC_FEATURES:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("string").fillna("__missing__").replace({"": "__missing__"})
            if col.endswith("_idx"):
                out[col] = out[col].str.replace(r"\.0$", "", regex=True)
    return out


def ape(actual: pd.Series, pred: np.ndarray) -> np.ndarray:
    pred = np.clip(np.asarray(pred, dtype=float), 1_000.0, None)
    return np.abs(pred - actual.to_numpy(dtype=float)) / actual.to_numpy(dtype=float)


def bin_count(value: float) -> str:
    if pd.isna(value):
        return "unknown"
    value = int(value)
    if value < 5:
        return "below_5"
    if value <= 9:
        return "5_to_9"
    if value <= 19:
        return "10_to_19"
    if value <= 49:
        return "20_to_49"
    return "50_plus"


def metrics_row(name: str, scope: str, frame: pd.DataFrame, pred: np.ndarray) -> dict[str, object]:
    metrics = calc_metrics(frame["price_krw"].to_numpy(), frame["ln_price_krw"].to_numpy(), pred)
    return {"case": name, "scope": scope, "n": int(len(frame)), **metrics}


def slice_rows(warm: pd.DataFrame, warm_pred: np.ndarray, cold_pred: np.ndarray) -> list[dict[str, object]]:
    out = []
    temp = warm[["_track6_row_id", "price_krw", "ln_price_krw", "artist_works_count_train"]].copy()
    temp["artist_count_bin"] = temp["artist_works_count_train"].map(bin_count)
    temp["warm_pred"] = warm_pred
    temp["cold_style_pred"] = cold_pred
    temp["warm_ape"] = ape(temp["price_krw"], warm_pred)
    temp["cold_style_ape"] = ape(temp["price_krw"], cold_pred)
    for bin_name, sub in temp.groupby("artist_count_bin", sort=False):
        for case, col in [("warm_artist_model", "warm_ape"), ("cold_style_model", "cold_style_ape")]:
            out.append(
                {
                    "artist_count_bin": bin_name,
                    "case": case,
                    "n": int(len(sub)),
                    "MdAPE": float(sub[col].median()),
                    "p95_APE": float(sub[col].quantile(0.95)),
                    "Within_30": float((sub[col] <= 0.30).mean()),
                    "Within_50": float((sub[col] <= 0.50).mean()),
                }
            )
    return out


def write_data_files(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> dict[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, frame, cols in [
        ("train_warm_strategy", train, WARM_FEATURES),
        ("train_cold_style", train, COLD_FEATURES),
        ("test_warm_warm_strategy", warm, [*WARM_FEATURES, "artist_works_count_train"]),
        ("test_warm_cold_style", warm, [*COLD_FEATURES, "artist_works_count_train"]),
        ("test_cold_cold_style", cold, COLD_FEATURES),
    ]:
        path = DATA_DIR / f"{name}_features.csv"
        frame[["_track6_row_id", *cols]].to_csv(path, index=False)
        files[path.stem] = rel(path)
    for name, frame in [("train", train), ("test_warm", warm), ("test_cold", cold)]:
        path = DATA_DIR / f"{name}_labels.csv"
        frame[["_track6_row_id", "price_krw", "ln_price_krw"]].to_csv(path, index=False)
        files[path.stem] = rel(path)
    return files


def copy_sources() -> dict[str, str]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    copied = {}
    for key, src in PATHS.items():
        dst = SOURCE_DIR / src.name
        shutil.copy2(src, dst)
        copied[key] = rel(dst)
    return copied


def table_html(frame: pd.DataFrame) -> str:
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in frame.columns)
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for value in row:
            if isinstance(value, float):
                value = f"{value:.4f}"
            cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def render_html(metrics: pd.DataFrame, slices: pd.DataFrame, files: dict[str, str], copied: dict[str, str]) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 G10 저이력 작가 라우팅 실험 결과</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    .card {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
  </style>
</head>
<body>
  <section class="card">
    <h1>Track6 G10 저이력 작가 라우팅 실험 결과</h1>
    <ul>
      <li>목적: 작가별 학습 작품 수가 적은 Warm 작품에서 Warm 작가 모델과 Cold 방식 모델 중 어느 쪽이 안정적인지 확인</li>
      <li>Warm 전략 피처: <code>{html.escape(', '.join(WARM_FEATURES))}</code></li>
      <li>Cold 방식 피처: <code>{html.escape(', '.join(COLD_FEATURES))}</code></li>
      <li>비교 모델: Warm 전략은 Huber, Cold 방식은 Quantile-LAD</li>
      <li>주의: 공식 Track6 Warm test는 Stable Warm 기준이라 학습 작품 수 5개 미만 구간은 거의 없거나 없을 수 있음</li>
    </ul>
  </section>
  <section class="card">
    <h2>전체 성능</h2>
    {table_html(metrics)}
  </section>
  <section class="card">
    <h2>작가별 학습 작품 수 구간별 Warm test 성능</h2>
    {table_html(slices)}
  </section>
  <section class="card">
    <h2>생성 데이터</h2>
    <ul>{''.join(f'<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>' for k, v in files.items())}</ul>
  </section>
  <section class="card">
    <h2>복사한 원본 데이터</h2>
    <ul>{''.join(f'<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>' for k, v in copied.items())}</ul>
  </section>
</body>
</html>
"""


def main() -> None:
    for path in [EXP_DIR, OUT_DIR, DATA_DIR, SOURCE_DIR, PROMPT_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    prompt = """# G10 실험 프롬프트

- 실험 목적: 학습 작품 수가 적은 Warm 작가에서 Warm 작가명 모델과 Cold 방식 모델 중 어느 쪽이 안정적인지 확인한다.
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- label은 `_track6_row_id` 기준으로만 결합하고, 모델 입력에는 사용하지 않는다.
- Warm 전략 모델: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_name_ko, artist_works_log`
- Cold 방식 모델: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support`
- Warm test를 `artist_works_count_train` 구간별로 나누어 MdAPE, p95 APE, Within-30/50을 비교한다.
- 공식 Warm test는 Stable Warm 기준이므로 5개 미만 구간이 없으면 그 한계를 결과에 명시한다.
"""
    prompt_path = PROMPT_DIR / "used_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    required = sorted(set([*WARM_FEATURES, *COLD_FEATURES, "artist_works_count_train"]))
    train = load_join(PATHS["train_features"], PATHS["train_labels"], required)
    warm = load_join(PATHS["warm_features"], PATHS["warm_labels"], required)
    cold = load_join(PATHS["cold_features"], PATHS["cold_labels"], COLD_FEATURES)
    train = normalize(train, required)
    warm = normalize(warm, required)
    cold = normalize(cold, COLD_FEATURES)

    files = write_data_files(train, warm, cold)
    copied = copy_sources()

    warm_pred_on_warm = fit_predict("huber", train, warm, WARM_FEATURES, NUMERIC_FEATURES)
    cold_style_pred_on_warm = fit_predict("quantile", train, warm, COLD_FEATURES, NUMERIC_FEATURES)
    cold_style_pred_on_cold = fit_predict("quantile", train, cold, COLD_FEATURES, NUMERIC_FEATURES)

    metrics = pd.DataFrame(
        [
            metrics_row("warm_artist_model_on_warm_test", "Warm", warm, warm_pred_on_warm),
            metrics_row("cold_style_model_on_warm_test", "Warm", warm, cold_style_pred_on_warm),
            metrics_row("cold_style_model_on_cold_test", "Cold", cold, cold_style_pred_on_cold),
        ]
    )
    slices = pd.DataFrame(slice_rows(warm, warm_pred_on_warm, cold_style_pred_on_warm))

    metrics.to_csv(OUT_DIR / "metrics_summary.csv", index=False)
    slices.to_csv(OUT_DIR / "warm_artist_count_slice_metrics.csv", index=False)
    (OUT_DIR / "result_sheet.html").write_text(render_html(metrics, slices, files, copied), encoding="utf-8")
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "G10",
        "runner_file": rel(Path(__file__)),
        "prompt_file": rel(prompt_path),
        "split_root": rel(SPLIT_ROOT),
        "generated_files": files,
        "copied_source_files": copied,
        "rows": {"train": len(train), "test_warm": len(warm), "test_cold": len(cold)},
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "README.md").write_text(
        f"""# Track6 G10 저이력 작가 라우팅 실험 결과

- 목적: 학습 작품 수가 적은 Warm 작가에서 Warm 작가 모델과 Cold 방식 모델 중 어느 쪽이 안정적인지 확인
- 사용 코드: `{rel(Path(__file__))}`
- 결과 HTML: `outputs/result_sheet.html`
- 전체 성능 CSV: `outputs/metrics_summary.csv`
- 구간별 성능 CSV: `outputs/warm_artist_count_slice_metrics.csv`
""",
        encoding="utf-8",
    )
    print(metrics.to_string(index=False))
    print(slices.to_string(index=False))


if __name__ == "__main__":
    main()
