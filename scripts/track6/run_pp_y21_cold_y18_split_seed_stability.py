#!/usr/bin/env python3
"""Run PP-Y21 repeated holdout stability checks for the PP-Y18 Cold candidate.

This does not retrain the base models. It reuses the frozen PP-Y18 prediction
artifacts and repeatedly changes the evaluation holdout composition by row and
artist. The purpose is to test whether the PP-Y18 improvement is robust to
evaluation composition before it is treated as a service candidate.
"""
from __future__ import annotations

import html
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
EXP_ID = "PP-Y21"
EXP_SLUG = "PP-Y21_cold_y18_split_seed_stability"
TITLE = "Cold PP-Y18 추가 split/seed 안정성 검증"
SEED = 20260603
N_SPLITS = 80
HOLDOUT_RATE = 0.30

PRED_PATH = BASE_EXP_DIR / "PP-Y18_cold_y16_top_candidate_stability" / "outputs" / "predictions.csv"
METRICS_PATH = BASE_EXP_DIR / "PP-Y18_cold_y16_top_candidate_stability" / "outputs" / "metrics.csv"
SUMMARY_PATH = BASE_EXP_DIR / "PP-Y21_cold_y18_split_seed_stability_summary_metrics.csv"

BASE_CANDIDATE = "component_pp_y2_baseline"
FOCUS_CANDIDATES = [
    "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25",
    "stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25",
    "stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35",
    "stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15",
]


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def load_candidate_pool() -> tuple[pd.DataFrame, list[str]]:
    pred = pd.read_csv(PRED_PATH, low_memory=False)
    existing = set(pred["candidate"].astype(str).unique())
    candidates = [candidate for candidate in FOCUS_CANDIDATES if candidate in existing]
    for candidate in sorted(existing):
        if candidate.startswith("stability_") and candidate not in candidates:
            candidates.append(candidate)
    if BASE_CANDIDATE not in existing:
        raise ValueError(f"missing baseline candidate: {BASE_CANDIDATE}")
    if not candidates:
        raise ValueError("missing PP-Y18 focus candidates")

    base = pred[pred["candidate"].eq(BASE_CANDIDATE)].copy()
    keep = ["_track6_row_id", "split", "actual_log", "actual_price", "pred_log", "artist_key"]
    base = base[keep].rename(columns={"pred_log": "base_pred_log"})
    merged = base.drop_duplicates(["_track6_row_id", "split"])
    for candidate in candidates:
        cand = pred[pred["candidate"].eq(candidate)][["_track6_row_id", "split", "pred_log"]].copy()
        cand = cand.drop_duplicates(["_track6_row_id", "split"]).rename(columns={"pred_log": f"{candidate}__pred_log"})
        merged = merged.merge(cand, on=["_track6_row_id", "split"], how="inner")
    if merged.empty:
        raise ValueError("empty merged candidate pool")
    return merged.reset_index(drop=True), candidates


def full_metrics(pool: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split_name, frame in [*pool.groupby("split", dropna=False), ("eval_pool", pool)]:
        split_label = str(split_name)
        rows.append({
            "experiment_id": EXP_ID,
            "candidate": BASE_CANDIDATE,
            "split": split_label,
            "policy": "baseline",
            **metric_values(frame, frame["base_pred_log"].to_numpy(dtype=float)),
        })
        for candidate in candidates:
            rows.append({
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "split": split_label,
                "policy": "pp_y18_reuse_prediction",
                **metric_values(frame, frame[f"{candidate}__pred_log"].to_numpy(dtype=float)),
            })
    return pd.DataFrame(rows)


def repeated_holdout(pool: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    row_indices = np.arange(len(pool))
    artists = pool["artist_key"].astype(str).fillna("__MISSING__").to_numpy()
    unique_artists = np.unique(artists)
    artist_to_index = {artist: np.flatnonzero(artists == artist) for artist in unique_artists}
    base_pred = pool["base_pred_log"].to_numpy(dtype=float)

    for split_idx in range(N_SPLITS):
        row_holdout = rng.choice(row_indices, size=max(1, int(len(pool) * HOLDOUT_RATE)), replace=False)
        picked_artists = rng.choice(
            unique_artists,
            size=max(1, int(len(unique_artists) * HOLDOUT_RATE)),
            replace=False,
        )
        artist_holdout = np.concatenate([artist_to_index[artist] for artist in picked_artists])
        for mode, idx in [("row_holdout", row_holdout), ("artist_holdout", artist_holdout)]:
            frame = pool.iloc[idx].copy()
            base_m = metric_values(frame, base_pred[idx])
            for candidate in candidates:
                cand_pred = pool[f"{candidate}__pred_log"].to_numpy(dtype=float)
                cand_m = metric_values(frame, cand_pred[idx])
                row = {
                    "experiment_id": EXP_ID,
                    "split_mode": mode,
                    "split_idx": split_idx,
                    "candidate": candidate,
                    "n": cand_m["n"],
                }
                for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                    row[f"base_{key}"] = base_m[key]
                    row[f"candidate_{key}"] = cand_m[key]
                    row[f"delta_{key}"] = base_m[key] - cand_m[key]
                rows.append(row)
    return pd.DataFrame(rows)


def summarize_holdout(holdout: pd.DataFrame, full: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    test_lookup = (
        full[full["split"].eq("test")]
        .set_index("candidate")[["MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
        .to_dict(orient="index")
    )
    for (candidate, mode), group in holdout.groupby(["candidate", "split_mode"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "split_mode": mode,
            "n_splits": int(group["split_idx"].nunique()),
            "median_n": float(group["n"].median()),
        }
        for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[f"delta_{key}"].to_numpy(dtype=float)
            row[f"delta_{key}_median"] = float(np.median(values))
            row[f"delta_{key}_ci_low"] = float(np.quantile(values, 0.025))
            row[f"delta_{key}_ci_high"] = float(np.quantile(values, 0.975))
            row[f"delta_{key}_prob_improve"] = float(np.mean(values > 0))
            if candidate in test_lookup:
                row[f"test_{key}"] = float(test_lookup[candidate][key])
        rows.append(row)
    summary = pd.DataFrame(rows)

    decisions = []
    for candidate, group in summary.groupby("candidate", dropna=False):
        artist = group[group["split_mode"].eq("artist_holdout")]
        row = {"candidate": candidate}
        if not artist.empty:
            artist_row = artist.iloc[0]
            mdape_prob = float(artist_row["delta_MdAPE_prob_improve"])
            mape_prob = float(artist_row["delta_MAPE_prob_improve"])
            p95_prob = float(artist_row["delta_p95_APE_prob_improve"])
            if mdape_prob >= 0.80 and mape_prob >= 0.90 and p95_prob >= 0.80:
                decision = "채택 후보"
            elif mape_prob >= 0.90 and p95_prob >= 0.80:
                decision = "목적별 후보"
            else:
                decision = "보류"
            row.update({
                "artist_holdout_MdAPE_prob": mdape_prob,
                "artist_holdout_MAPE_prob": mape_prob,
                "artist_holdout_p95_prob": p95_prob,
                "decision": decision,
            })
        decisions.append(row)
    decision_df = pd.DataFrame(decisions)
    return summary.merge(decision_df, on="candidate", how="left")


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def render_report(full: pd.DataFrame, holdout_summary: pd.DataFrame) -> tuple[str, str]:
    test = full[full["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    key_cols = [
        "candidate",
        "split_mode",
        "delta_MdAPE_median",
        "delta_MdAPE_prob_improve",
        "delta_MAPE_median",
        "delta_MAPE_prob_improve",
        "delta_p95_APE_median",
        "delta_p95_APE_prob_improve",
        "decision",
    ]
    summary_view = holdout_summary[key_cols].sort_values(
        ["decision", "split_mode", "delta_MdAPE_prob_improve", "delta_MAPE_prob_improve"],
        ascending=[True, True, False, False],
    )
    decision = (
        holdout_summary[holdout_summary["split_mode"].eq("artist_holdout")]
        .sort_values(["decision", "delta_MdAPE_prob_improve", "delta_MAPE_prob_improve"], ascending=[True, False, False])
    )
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "- 목적: `PP-Y18 qwidth_bin` 후보가 특정 test 구성에서만 좋아진 것인지 확인한다.",
        "- 방식: 기존 PP-Y18 예측값은 고정하고, 평가 holdout을 row 기준과 artist 기준으로 80회 반복 재구성한다.",
        "- 주의: 이 검증은 모델 재학습 split 검증이 아니라, 이미 생성된 예측값의 평가 구성 안정성 검증이다.",
        "",
        "## Test 기준 결과",
        "",
        markdown_table(test[["candidate", "policy", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]], max_rows=20),
        "",
        "## 반복 holdout 안정성 요약",
        "",
        markdown_table(summary_view, max_rows=80),
        "",
        "## 채택 판단",
        "",
        markdown_table(decision[["candidate", "decision", "artist_holdout_MdAPE_prob", "artist_holdout_MAPE_prob", "artist_holdout_p95_prob"]], max_rows=20),
        "",
        "## 해석",
        "",
        "- `delta`는 `PP-Y2 기준 오차 - 후보 오차`이므로 양수일수록 후보가 좋다.",
        "- artist holdout 개선 확률이 row holdout보다 낮으면, 작가 구성이 바뀔 때 성능 변동이 있다는 뜻이다.",
        "- 채택 후보는 바로 서비스 확정이 아니라, Cold 개선 후보로 최종 정책 비교에 올릴 수 있다는 의미다.",
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<p>기존 PP-Y18 예측값을 고정하고 row/artist holdout을 반복 구성해 후보 개선의 안정성을 확인했습니다.</p>
<h2>Test 기준 결과</h2>{test.to_html(index=False, escape=True)}
<h2>반복 holdout 안정성 요약</h2>{holdout_summary.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = time.time()
    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    pool, candidates = load_candidate_pool()
    full = full_metrics(pool, candidates)
    holdout = repeated_holdout(pool, candidates)
    holdout_summary = summarize_holdout(holdout, full)

    full.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    holdout.to_csv(exp_dir / "outputs" / "repeated_holdout_results.csv", index=False)
    holdout_summary.to_csv(exp_dir / "outputs" / "holdout_summary.csv", index=False)
    full.to_csv(SUMMARY_PATH, index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "source_predictions": str(PRED_PATH.relative_to(REPO)),
        "source_metrics": str(METRICS_PATH.relative_to(REPO)),
        "n_splits": N_SPLITS,
        "holdout_rate": HOLDOUT_RATE,
        "seed": SEED,
        "note": "Frozen prediction repeated holdout check, not model retraining.",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(full, holdout_summary)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed in {time.time() - start:.2f}s\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment": str(exp_dir.relative_to(REPO)),
        "metrics": str((exp_dir / "outputs" / "metrics.csv").relative_to(REPO)),
        "holdout_summary": str((exp_dir / "outputs" / "holdout_summary.csv").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
