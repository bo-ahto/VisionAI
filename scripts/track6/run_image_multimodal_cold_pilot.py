#!/usr/bin/env python3
"""Run a Cold Track6 image/tabular multimodal pilot on sampled CLIP embeddings."""
from __future__ import annotations

import html
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    BASE_NUMERIC,
    REPO,
    SEED,
    artifact_features,
    fit_predict,
    load_scope,
    metrics,
)


EXP_ID = "IMG-P1"
EXP_SLUG = "IMG-P1_cold_clip_multimodal_pilot"
BASE_DIR = REPO / "data" / "track6" / "image_multimodal"
EMBED_PATH = BASE_DIR / "track6_clip_cold_pilot_600_embeddings.npy"
INDEX_PATH = BASE_DIR / "track6_clip_cold_pilot_600_index.csv"
EXP_DIR = BASE_EXP_DIR / EXP_SLUG


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default=EXP_ID)
    parser.add_argument("--experiment-slug", default=EXP_SLUG)
    parser.add_argument("--embedding-path", type=Path, default=EMBED_PATH)
    parser.add_argument("--index-path", type=Path, default=INDEX_PATH)
    return parser.parse_args()


def split_types_for_image(features: list[str], image_features: set[str]) -> tuple[list[str], list[str]]:
    numeric = [col for col in features if col in set(BASE_NUMERIC) or col in image_features]
    categorical = [col for col in features if col not in numeric]
    return numeric, categorical


def lgbm_model(features: list[str], image_features: set[str]) -> Pipeline:
    numeric, categorical = split_types_for_image(features, image_features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="regression",
            n_estimators=260,
            learning_rate=0.04,
            num_leaves=15,
            min_child_samples=10,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.5,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def load_embedding_index() -> tuple[pd.DataFrame, np.ndarray]:
    embeddings = np.load(EMBED_PATH)
    index = pd.read_csv(INDEX_PATH, low_memory=False)
    if len(index) != len(embeddings):
        raise ValueError(f"index rows {len(index)} != embedding rows {len(embeddings)}")
    index = index.copy()
    index["embedding_pos"] = np.arange(len(index))
    return index, embeddings


def join_embeddings(frame: pd.DataFrame, index: pd.DataFrame, embeddings: np.ndarray, split: str) -> tuple[pd.DataFrame, np.ndarray]:
    split_index = index[index["split"].eq(split)].copy()
    out = frame.merge(split_index[["_track6_row_id", "embedding_pos", "resolved_source_bucket"]], on="_track6_row_id", how="inner")
    out = out.sort_values("_track6_row_id").reset_index(drop=True)
    emb = embeddings[out["embedding_pos"].to_numpy(dtype=int)]
    return out, emb


def add_pca_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    train_emb: np.ndarray,
    val_emb: np.ndarray,
    test_emb: np.ndarray,
    n_components: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    pca = PCA(n_components=n_components, random_state=SEED)
    train_pca = pca.fit_transform(train_emb)
    val_pca = pca.transform(val_emb)
    test_pca = pca.transform(test_emb)
    cols = [f"clip_pca_{idx + 1:03d}" for idx in range(n_components)]

    def attach(frame: pd.DataFrame, values: np.ndarray) -> pd.DataFrame:
        out = frame.copy()
        for idx, col in enumerate(cols):
            out[col] = values[:, idx]
        return out

    return attach(train, train_pca), attach(val, val_pca), attach(test, test_pca), cols


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    note: str,
    train_scope: str,
) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "train_scope": train_scope,
        "note": note,
        "n_eval": int(len(frame)),
        **metrics(frame[["_track6_row_id", "price_krw", "ln_price_krw"]], pred_log),
    }
    rows.append(row)


def prediction_frame(exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    actual_price = frame["price_krw"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": actual_price,
        "pred_price": pred_price,
        "source": frame.get("resolved_source_bucket", pd.Series([""] * len(frame))).to_numpy(),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def fit_predict_lgb(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str], image_features: set[str]) -> dict[str, np.ndarray]:
    model = lgbm_model(features, image_features)
    model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }


def fit_predict_ridge_image(train_emb: np.ndarray, val_emb: np.ndarray, test_emb: np.ndarray, train: pd.DataFrame) -> dict[str, np.ndarray]:
    model = Pipeline([
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=10.0, random_state=SEED)),
    ])
    model.fit(train_emb, train["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val_emb), dtype=float),
        "test": np.asarray(model.predict(test_emb), dtype=float),
    }


def render_report(metrics_df: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    ordered = metrics_df.sort_values(["split", "MdAPE", "MAPE", "p95_APE"])
    train_rows = config["sample_rows"]["train"]
    val_rows = config["sample_rows"]["validation"]
    test_rows = config["sample_rows"]["test"]
    md_lines = [
        f"# {config['experiment_id']} Cold CLIP 이미지 결합 파일럿",
        "",
        "- 목적: Cold 가격 예측에서 작품 이미지 임베딩이 추가 신호를 갖는지 파일럿으로 확인한다.",
        "- 기준: 기존 Track6 Cold split을 유지하되, 이미지 임베딩이 생성된 Saatchi/Artsy 샘플만 사용한다.",
        f"- 샘플 규모: train `{train_rows}`건, validation `{val_rows}`건, test `{test_rows}`건.",
        "- 주의: 이번 결과는 샘플 기반 파일럿이므로 최종 성능 결론이 아니라 전체 확장 여부 판단용이다.",
        "",
        "## 실험 구성",
        "",
        f"- `sample_tabular_lgb`: 이미지 임베딩이 있는 train `{train_rows}`건만 사용한 정형 피처 기준.",
        "- `image_pca*_ridge`: CLIP 이미지 임베딩만 사용한 기준.",
        "- `sample_tabular_lgb_clip_pca*`: 정형 피처와 CLIP PCA 피처를 결합한 기준.",
        "- `full_tabular_*_reference`: 기존 전체 Cold train으로 학습한 정형 모델을 같은 이미지 샘플 val/test에 평가한 참고 기준.",
        "",
        "## 결과",
        "",
        "| split | candidate | train_scope | n_eval | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | note |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in ordered.itertuples():
        md_lines.append(
            f"| {row.split} | `{row.candidate}` | {row.train_scope} | {row.n_eval} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | {row.Within_30:.4f} | {row.note} |"
        )
    md_lines += [
        "",
        "## 해석 기준",
        "",
        "- 이미지 단독 후보가 샘플 정형 후보보다 의미 있게 낮으면 이미지 자체에 가격 신호가 있다는 근거가 된다.",
        "- 정형+이미지 후보가 샘플 정형 후보보다 낮으면 이미지 결합의 파일럿 개선 가능성이 있다.",
        "- 전체 정형 참고 기준은 train 규모가 다르므로 샘플 후보와 직접 공정 비교하지 않고 운영 기준과의 거리만 본다.",
        "- 다음 단계는 train 표본을 늘리고 같은 구조로 재검증하는 것이다.",
        "",
        "## 설정",
        "",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
    ]
    md = "\n".join(md_lines) + "\n"
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(config['experiment_id'])} Cold CLIP 파일럿</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}.note{{background:#fff8db;border:1px solid #e5d28a;padding:12px;margin:12px 0}}
</style></head><body>
<h1>{html.escape(config['experiment_id'])} Cold CLIP 이미지 결합 파일럿</h1>
<div class="note">600건 샘플 기반 파일럿입니다. 전체 모델 성능 결론이 아니라 이미지 실험을 확장할지 판단하는 중간 결과입니다.</div>
{ordered.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    args = parse_args()
    global EXP_ID, EXP_SLUG, EMBED_PATH, INDEX_PATH, EXP_DIR
    EXP_ID = args.experiment_id
    EXP_SLUG = args.experiment_slug
    EMBED_PATH = args.embedding_path if args.embedding_path.is_absolute() else REPO / args.embedding_path
    INDEX_PATH = args.index_path if args.index_path.is_absolute() else REPO / args.index_path
    EXP_DIR = BASE_EXP_DIR / EXP_SLUG

    features = artifact_features()
    lgb_features = features["cold_lightgbm"]
    cb_features = features["cold_catboost"]

    full_train_lgb, full_val_lgb, full_test_lgb = load_scope("cold", lgb_features)
    full_train_cb, full_val_cb, full_test_cb = load_scope("cold", cb_features)
    index, embeddings = load_embedding_index()

    train, train_emb = join_embeddings(full_train_lgb, index, embeddings, "train")
    val, val_emb = join_embeddings(full_val_lgb, index, embeddings, "val_cold")
    test, test_emb = join_embeddings(full_test_lgb, index, embeddings, "test_cold")

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []

    sample_pred = fit_predict_lgb(train, val, test, lgb_features, set())
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, EXP_ID, "sample_tabular_lgb", split, frame, sample_pred[split], "샘플 train만 사용한 정형 피처 기준", "image_sample_train")
        preds.append(prediction_frame(EXP_ID, "sample_tabular_lgb", split, frame, sample_pred[split]))

    for n_components in [16, 32, 64]:
        train_pca, val_pca, test_pca, pca_cols = add_pca_features(train, val, test, train_emb, val_emb, test_emb, n_components)
        image_features = set(pca_cols)
        image_pred = fit_predict_ridge_image(train_pca[pca_cols].to_numpy(), val_pca[pca_cols].to_numpy(), test_pca[pca_cols].to_numpy(), train_pca)
        candidate = f"image_pca{n_components}_ridge"
        for split, frame in [("validation", val_pca), ("test", test_pca)]:
            add_metric(rows, EXP_ID, candidate, split, frame, image_pred[split], "CLIP 이미지만 사용한 Ridge 기준", "image_sample_train")
            preds.append(prediction_frame(EXP_ID, candidate, split, frame, image_pred[split]))

        combo_features = lgb_features + pca_cols
        combo_pred = fit_predict_lgb(train_pca, val_pca, test_pca, combo_features, image_features)
        candidate = f"sample_tabular_lgb_clip_pca{n_components}"
        for split, frame in [("validation", val_pca), ("test", test_pca)]:
            add_metric(rows, EXP_ID, candidate, split, frame, combo_pred[split], "샘플 train에서 정형 피처와 CLIP PCA 결합", "image_sample_train")
            preds.append(prediction_frame(EXP_ID, candidate, split, frame, combo_pred[split]))

    full_ref_lgb = fit_predict("lightgbm", full_train_lgb, val, test, lgb_features)
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, EXP_ID, "full_tabular_lgb_reference", split, frame, full_ref_lgb[split], "전체 Cold train으로 학습한 LightGBM 참고 기준", "full_cold_train")
        preds.append(prediction_frame(EXP_ID, "full_tabular_lgb_reference", split, frame, full_ref_lgb[split]))

    val_cb_eval = full_val_cb.merge(val[["_track6_row_id", "resolved_source_bucket"]], on="_track6_row_id", how="inner").sort_values("_track6_row_id").reset_index(drop=True)
    test_cb_eval = full_test_cb.merge(test[["_track6_row_id", "resolved_source_bucket"]], on="_track6_row_id", how="inner").sort_values("_track6_row_id").reset_index(drop=True)
    full_ref_cb = fit_predict("catboost", full_train_cb, val_cb_eval, test_cb_eval, cb_features)
    for split, frame in [("validation", val_cb_eval), ("test", test_cb_eval)]:
        add_metric(rows, EXP_ID, "full_tabular_catboost_reference", split, frame, full_ref_cb[split], "전체 Cold train으로 학습한 CatBoost 참고 기준", "full_cold_train")
        preds.append(prediction_frame(EXP_ID, "full_tabular_catboost_reference", split, frame, full_ref_cb[split]))

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in ["outputs", "reports", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True)
    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "embedding_path": str(EMBED_PATH.relative_to(REPO)),
        "index_path": str(INDEX_PATH.relative_to(REPO)),
        "sample_rows": {"train": len(train), "validation": len(val), "test": len(test)},
        "lgb_features": lgb_features,
        "catboost_features": cb_features,
        "seed": SEED,
    }
    (EXP_DIR / "data" / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, config)
    report_md = EXP_DIR / "reports" / f"{EXP_ID}_cold_clip_multimodal_pilot.md"
    report_html = EXP_DIR / "reports" / f"{EXP_ID}_cold_clip_multimodal_pilot.html"
    report_md.write_text(md, encoding="utf-8")
    report_html.write_text(html_doc, encoding="utf-8")
    docs_report = REPO / "docs" / "track6" / "experiments" / f"{EXP_ID}_cold_clip_multimodal_pilot.md"
    docs_report.write_text(md, encoding="utf-8")
    print(f"wrote {EXP_DIR.relative_to(REPO)}/outputs/metrics.csv")
    print(f"wrote {report_md.relative_to(REPO)}")
    print(f"wrote {report_html.relative_to(REPO)}")
    print(f"wrote {docs_report.relative_to(REPO)}")
    print(metrics_df.sort_values(["split", "MdAPE", "MAPE"]).to_string(index=False))


if __name__ == "__main__":
    main()
