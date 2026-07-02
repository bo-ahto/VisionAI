#!/usr/bin/env python3
"""PP-WLITE-Q1: Warm-lite Quantile candidate validation.

현재 Warm-lite v0.1의 Huber 6구성 평균(all6_current)을 기준으로,
저이력 1~4건 구간에 LightGBM Quantile 후보를 직접 적용하면 점예측 성능이
개선되는지 확인한다.

평가 설계는 PP-WCUT5와 같은 실존 저이력 작가 leave-one-out이다.

- 평가행: train 이력 2~5건 실존 작가에서 seed별 작가당 1작품 hold-out
- 피처: Warm-lite와 같은 작가 이력 사다리 통계 + 작품 크기/매체/지지체 피처
- 기준: Huber 6구성 평균(all6_current)
- 후보: LightGBM Quantile q50(full/lean), full+lean 평균, all6와 q50 blend
- q10/q90은 full 피처 기준으로 함께 학습해 quantile_width 진단에 사용
- 0604 미사용
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_cgrp_spec = importlib.util.spec_from_file_location(
    "cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py"
)
cgrp = importlib.util.module_from_spec(_cgrp_spec)
_cgrp_spec.loader.exec_module(cgrp)

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)

_cb3_spec = importlib.util.spec_from_file_location(
    "cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py"
)
cb3 = importlib.util.module_from_spec(_cb3_spec)
_cb3_spec.loader.exec_module(cb3)


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WLITE-Q1_warm_lite_quantile_candidate_validation"
SEEDS = [20260612, 20260613, 20260614]
ROWS_MIN, ROWS_MAX = 2, 5
N_BOOT = 400
FORCE_RECOMPUTE = True

LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]

FULL_NUM = cb3.NUM_BASE + cgrp.GRP_FULL
LEAN_NUM = cb3.NUM_BASE + cgrp.GRP_LEAN
CAT_COLS = cb3.CAT_C

HUBER_CANDIDATES = {
    "all6_current": ["c0", "c1", "c2", "c3", "c4", "c5"],
}

QUANTILE_CANDIDATES = [
    "lgbq_full_q50",
    "lgbq_lean_q50",
    "lgbq_full_lean_avg",
    "all6_75_lgbq_full_25",
    "all6_50_lgbq_full_50",
]

ALL_CANDIDATES = ["all6_current"] + QUANTILE_CANDIDATES


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def huber_component_predictions(train_s: pd.DataFrame, held_s: pd.DataFrame) -> pd.DataFrame:
    train_s = train_s.copy()
    held_s = held_s.copy()
    for frame in (train_s, held_s):
        frame["grp_price_proxy"] = frame["grp_unit_area_median"] + frame["log_area"].clip(lower=0)
    y = train_s["ln_price_krw"].to_numpy(dtype=float)

    out = pd.DataFrame(index=held_s.index)
    for i, cfg in enumerate(cb3.C_CONFIGS):
        num = cb3.NUM_BASE + cfg["extra"]
        pipe = Pipeline(
            [
                (
                    "prep",
                    ColumnTransformer(
                        [
                            (
                                "num",
                                Pipeline(
                                    [
                                        ("imputer", SimpleImputer(strategy="median")),
                                        ("scaler", StandardScaler()),
                                    ]
                                ),
                                num,
                            ),
                            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                        ]
                    ),
                ),
                ("model", HuberRegressor(epsilon=cfg["epsilon"], alpha=cfg["alpha"], max_iter=4000)),
            ]
        )
        pipe.fit(train_s[num + CAT_COLS], y)
        out[f"c{i}"] = np.asarray(pipe.predict(held_s[num + CAT_COLS]), dtype=float)
    return out


def quantile_pipeline(alpha: float, seed: int) -> Pipeline:
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", SimpleImputer(strategy="median"), FULL_NUM),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                    ]
                ),
            ),
            (
                "model",
                LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    n_estimators=320,
                    learning_rate=0.035,
                    num_leaves=31,
                    min_child_samples=20,
                    subsample=0.90,
                    colsample_bytree=0.90,
                    reg_lambda=0.10,
                    random_state=seed,
                    n_jobs=-1,
                    verbose=-1,
                ),
            ),
        ]
    )


def quantile_q50_pipeline(feature_set: str, seed: int) -> Pipeline:
    num_cols = FULL_NUM if feature_set == "full" else LEAN_NUM
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", SimpleImputer(strategy="median"), num_cols),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                    ]
                ),
            ),
            (
                "model",
                LGBMRegressor(
                    objective="quantile",
                    alpha=0.50,
                    n_estimators=320,
                    learning_rate=0.035,
                    num_leaves=31,
                    min_child_samples=20,
                    subsample=0.90,
                    colsample_bytree=0.90,
                    reg_lambda=0.10,
                    random_state=seed,
                    n_jobs=-1,
                    verbose=-1,
                ),
            ),
        ]
    )


def quantile_predictions(train_s: pd.DataFrame, held_s: pd.DataFrame, seed: int) -> pd.DataFrame:
    train_s = train_s.copy()
    held_s = held_s.copy()
    for frame in (train_s, held_s):
        frame["grp_price_proxy"] = frame["grp_unit_area_median"] + frame["log_area"].clip(lower=0)
    y = train_s["ln_price_krw"].to_numpy(dtype=float)

    full_q10 = quantile_pipeline(0.10, seed)
    full_q50 = quantile_pipeline(0.50, seed)
    full_q90 = quantile_pipeline(0.90, seed)
    lean_q50 = quantile_q50_pipeline("lean", seed)

    full_q10.fit(train_s[FULL_NUM + CAT_COLS], y)
    full_q50.fit(train_s[FULL_NUM + CAT_COLS], y)
    full_q90.fit(train_s[FULL_NUM + CAT_COLS], y)
    lean_q50.fit(train_s[LEAN_NUM + CAT_COLS], y)

    out = pd.DataFrame(index=held_s.index)
    out["lgbq_full_q10"] = np.asarray(full_q10.predict(held_s[FULL_NUM + CAT_COLS]), dtype=float)
    out["lgbq_full_q50"] = np.asarray(full_q50.predict(held_s[FULL_NUM + CAT_COLS]), dtype=float)
    out["lgbq_full_q90"] = np.asarray(full_q90.predict(held_s[FULL_NUM + CAT_COLS]), dtype=float)
    out["lgbq_lean_q50"] = np.asarray(lean_q50.predict(held_s[LEAN_NUM + CAT_COLS]), dtype=float)
    out["lgbq_width"] = np.maximum(out["lgbq_full_q90"] - out["lgbq_full_q10"], 0.0)
    out["lgbq_crossed"] = out["lgbq_full_q90"] < out["lgbq_full_q10"]
    return out


def run_seed(seed: int, train: pd.DataFrame, base_ladder: list) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = train.groupby("artist_key").size()
    low_artists = counts[(counts >= ROWS_MIN) & (counts <= ROWS_MAX)].index

    held_idx = []
    for artist in low_artists:
        idx = np.where(train["artist_key"].to_numpy() == artist)[0]
        held_idx.append(int(rng.choice(idx)))

    held = train.iloc[held_idx].reset_index(drop=True)
    tr_rest = train.drop(index=train.index[held_idx]).reset_index(drop=True)

    cgrp.LADDER = LITE_LADDER + base_ladder
    tr_s = cgrp.train_with_internal_stats(tr_rest)
    held_s = cgrp.assign_group_stats(tr_rest, held)
    cgrp.LADDER = base_ladder

    huber_preds = huber_component_predictions(tr_s, held_s)
    q_preds = quantile_predictions(tr_s, held_s, seed)

    out = pd.DataFrame(
        {
            "seed": seed,
            "_row": held_idx,
            "artist_key": held["artist_key"].to_numpy(),
            "history_k": held["artist_key"].map(counts - 1).astype(int).to_numpy(),
            "actual_price": held["price_krw"].to_numpy(dtype=float),
            "actual_log": held["ln_price_krw"].to_numpy(dtype=float),
            "artist_match": (held_s["grp_match_level"] <= len(LITE_LADDER)).to_numpy(),
        }
    )

    for comp in huber_preds.columns:
        out[f"{comp}_pred_log"] = huber_preds[comp].to_numpy(dtype=float)
    out["all6_current_pred_log"] = huber_preds[HUBER_CANDIDATES["all6_current"]].mean(axis=1).to_numpy(dtype=float)

    for col in q_preds.columns:
        out[col] = q_preds[col].to_numpy()
    out["lgbq_full_q50_pred_log"] = out["lgbq_full_q50"]
    out["lgbq_lean_q50_pred_log"] = out["lgbq_lean_q50"]
    out["lgbq_full_lean_avg_pred_log"] = 0.50 * out["lgbq_full_q50"] + 0.50 * out["lgbq_lean_q50"]
    out["all6_75_lgbq_full_25_pred_log"] = 0.75 * out["all6_current_pred_log"] + 0.25 * out["lgbq_full_q50"]
    out["all6_50_lgbq_full_50_pred_log"] = 0.50 * out["all6_current_pred_log"] + 0.50 * out["lgbq_full_q50"]
    return out


def metric_rows(preds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall_rows = []
    by_k_rows = []
    for candidate in ALL_CANDIDATES:
        col = f"{candidate}_pred_log"
        mt = cb1.mt(preds["actual_price"].to_numpy(dtype=float), preds[col].to_numpy(dtype=float))
        overall_rows.append(
            {
                "candidate": candidate,
                "n": int(len(preds)),
                **{metric: round(float(value), 6) for metric, value in mt.items()},
            }
        )
        for k, group in preds.groupby("history_k", sort=True):
            gmt = cb1.mt(group["actual_price"].to_numpy(dtype=float), group[col].to_numpy(dtype=float))
            by_k_rows.append(
                {
                    "history_k": int(k),
                    "candidate": candidate,
                    "n": int(len(group)),
                    **{metric: round(float(value), 6) for metric, value in gmt.items()},
                }
            )

    overall = pd.DataFrame(overall_rows)
    by_k = pd.DataFrame(by_k_rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        base = float(overall.loc[overall["candidate"].eq("all6_current"), metric].iloc[0])
        overall[f"rank_{metric}"] = overall[metric].rank(method="min").astype(int)
        overall[f"delta_{metric}_minus_all6"] = overall[metric] - base
        by_k[f"rank_{metric}"] = by_k.groupby("history_k")[metric].rank(method="min").astype(int)
    return overall.sort_values(["MAPE", "p95_APE", "MdAPE"]), by_k.sort_values(["history_k", "MAPE", "p95_APE"])


def bootstrap_rows(preds: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    groups = pd.Series(np.arange(len(preds))).groupby(preds["artist_key"].astype(str).to_numpy()).apply(list)
    price = preds["actual_price"].to_numpy(dtype=float)
    base = preds["all6_current_pred_log"].to_numpy(dtype=float)
    rows = []
    for candidate in QUANTILE_CANDIDATES:
        cand = preds[f"{candidate}_pred_log"].to_numpy(dtype=float)
        wins_candidate = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
        wins_all6 = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
        for _ in range(N_BOOT):
            sampled = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[g] for g in sampled])
            cm = cb1.mt(price[idx], cand[idx])
            bm = cb1.mt(price[idx], base[idx])
            for metric in wins_candidate:
                wins_candidate[metric] += cm[metric] < bm[metric]
                wins_all6[metric] += bm[metric] < cm[metric]
        row = {"candidate": candidate, "n_boot": N_BOOT}
        for metric in wins_candidate:
            row[f"p_candidate_better_all6_{metric}"] = wins_candidate[metric] / N_BOOT
            row[f"p_all6_better_candidate_{metric}"] = wins_all6[metric] / N_BOOT
        rows.append(row)
    return pd.DataFrame(rows).sort_values("candidate")


def width_diagnostics(preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    finite = preds[np.isfinite(preds["lgbq_width"])].copy()
    finite["width_bin"] = pd.qcut(finite["lgbq_width"], q=4, labels=["q1_low", "q2", "q3", "q4_high"], duplicates="drop")
    for width_bin, group in finite.groupby("width_bin", observed=True):
        row = {
            "width_bin": str(width_bin),
            "n": int(len(group)),
            "width_min": float(group["lgbq_width"].min()),
            "width_max": float(group["lgbq_width"].max()),
        }
        for candidate in ("all6_current", "lgbq_full_q50"):
            mt = cb1.mt(group["actual_price"].to_numpy(dtype=float), group[f"{candidate}_pred_log"].to_numpy(dtype=float))
            row[f"{candidate}_MdAPE"] = float(mt["MdAPE"])
            row[f"{candidate}_MAPE"] = float(mt["MAPE"])
            row[f"{candidate}_p95_APE"] = float(mt["p95_APE"])
        rows.append(row)
    return pd.DataFrame(rows)


def table_md(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    view = frame[columns].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    overall: pd.DataFrame,
    by_k: pd.DataFrame,
    boot: pd.DataFrame,
    width_diag: pd.DataFrame,
    config: dict,
) -> None:
    lines = [
        "# PP-WLITE-Q1 Warm-lite Quantile 후보 검증",
        "",
        "## 1. 목적",
        "",
        "Warm-lite v0.1의 현재 Huber 6구성 평균(all6_current)에 Quantile 회귀 후보를 적용할 근거가 있는지 확인한다.",
        "",
        "## 2. 평가 설계",
        "",
        "- PP-WCUT5와 같은 실존 저이력 작가 leave-one-out 설계",
        "- train 이력 2~5건 작가에서 seed별 작가당 1작품 hold-out",
        "- hold-out 작품 자기 가격은 작가 이력 통계에서 제외",
        "- LightGBM Quantile q50을 full/lean 피처 구성으로 학습",
        "- q10/q90은 full 피처 기준 quantile_width 진단용으로 산출",
        "",
        "## 3. Overall metrics",
        "",
        table_md(
            overall,
            [
                "candidate",
                "n",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "rank_MdAPE",
                "rank_MAPE",
                "rank_p95_APE",
                "delta_MdAPE_minus_all6",
                "delta_MAPE_minus_all6",
                "delta_p95_APE_minus_all6",
            ],
        ),
        "",
        "## 4. Metrics by history_k",
        "",
        table_md(
            by_k,
            ["history_k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "rank_MdAPE", "rank_MAPE", "rank_p95_APE"],
        ),
        "",
        "## 5. Bootstrap vs all6_current",
        "",
        table_md(
            boot,
            [
                "candidate",
                "n_boot",
                "p_candidate_better_all6_MdAPE",
                "p_candidate_better_all6_MAPE",
                "p_candidate_better_all6_p95_APE",
                "p_all6_better_candidate_MdAPE",
                "p_all6_better_candidate_MAPE",
                "p_all6_better_candidate_p95_APE",
            ],
        ),
        "",
        "## 6. Quantile width diagnostics",
        "",
        table_md(
            width_diag,
            [
                "width_bin",
                "n",
                "width_min",
                "width_max",
                "all6_current_MdAPE",
                "all6_current_MAPE",
                "all6_current_p95_APE",
                "lgbq_full_q50_MdAPE",
                "lgbq_full_q50_MAPE",
                "lgbq_full_q50_p95_APE",
            ],
        ),
        "",
        "## 7. Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    feats = artifact_features()["cold_lightgbm"]
    train, _, _ = load_scope("warm", feats + ["medium_support_bucket"])
    needed = list(
        dict.fromkeys(
            feats
            + [
                "medium_support_bucket",
                "ln_price_krw",
                "log_area",
                "price_krw",
                "artist_key",
            ]
        )
    )
    train = train[needed].reset_index(drop=True)
    base_ladder = list(cgrp.LADDER)

    parts = []
    for seed in SEEDS:
        checkpoint = EXP / "outputs" / f"preds_seed{seed}.csv"
        if checkpoint.exists() and not FORCE_RECOMPUTE:
            print(f"[resume] seed={seed} checkpoint found", flush=True)
            parts.append(pd.read_csv(checkpoint))
            continue
        part = run_seed(seed, train, base_ladder)
        part.to_csv(checkpoint, index=False)
        print(f"[done] seed={seed}: {len(part)} rows", flush=True)
        parts.append(part)

    preds = pd.concat(parts, ignore_index=True)
    preds.to_csv(EXP / "outputs" / "predictions_all_seeds.csv", index=False)

    overall, by_k = metric_rows(preds)
    boot = bootstrap_rows(preds)
    width_diag = width_diagnostics(preds)

    overall.to_csv(EXP / "outputs" / "candidate_metrics_overall.csv", index=False)
    by_k.to_csv(EXP / "outputs" / "candidate_metrics_by_k.csv", index=False)
    boot.to_csv(EXP / "outputs" / "candidate_bootstrap_vs_all6.csv", index=False)
    width_diag.to_csv(EXP / "outputs" / "quantile_width_diagnostics.csv", index=False)

    all6 = overall[overall["candidate"].eq("all6_current")].iloc[0]
    best_by_metric = {
        metric: str(overall.sort_values(metric).iloc[0]["candidate"])
        for metric in ("MdAPE", "MAPE", "p95_APE")
    }
    config = {
        "experiment_id": "PP-WLITE-Q1",
        "experiment_slug": EXP.name,
        "eval_design": f"PP-WCUT5-equivalent real low-history leave-one-out, train history {ROWS_MIN}~{ROWS_MAX}, seeds {SEEDS}",
        "rows": int(len(preds)),
        "artist_count": int(preds["artist_key"].nunique()),
        "baseline": "all6_current",
        "quantile_model": "LightGBM objective=quantile, q10/q50/q90 full features, q50 lean features",
        "candidates": ALL_CANDIDATES,
        "all6_current_metrics": {metric: float(all6[metric]) for metric in ("MdAPE", "MAPE", "p95_APE")},
        "best_by_metric": best_by_metric,
        "n_boot": N_BOOT,
        "prohibitions": ["0604 사용 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(overall, by_k, boot, width_diag, config)

    print("[overall]", flush=True)
    print(
        overall[
            [
                "candidate",
                "n",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "delta_MdAPE_minus_all6",
                "delta_MAPE_minus_all6",
                "delta_p95_APE_minus_all6",
            ]
        ].to_string(index=False),
        flush=True,
    )
    print("[bootstrap]", flush=True)
    print(boot.round(4).to_string(index=False), flush=True)
    print(json.dumps(config, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
