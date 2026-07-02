#!/usr/bin/env python3
"""PP-COLD-QF2: revalidate QF1 conditional Cold guard.

QF1 found that a Warm-lite-style Cold model should not replace the current
Cold v0.3 chain, but a very limited "v0.3 down to qf1 when risky" guard can
reduce MAPE and p95 on fixed test with small MdAPE cost.

This follow-up checks whether that guard is stable under repeated validation
row folds and artist holdout folds. Candidate thresholds are recomputed from
each calibration fold without using labels.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

_qf1_spec = importlib.util.spec_from_file_location(
    "qf1", SCRIPT_DIR / "run_pp_cold_qf1_warm_lite_style_cold_followup.py"
)
qf1 = importlib.util.module_from_spec(_qf1_spec)
assert _qf1_spec.loader is not None
_qf1_spec.loader.exec_module(qf1)


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-COLD-QF2"
EXP_SLUG = "PP-COLD-QF2_conditional_guard_revalidation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

BASE_ROWS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-CBASE1_cold_base_lock"
    / "outputs"
    / "fixed_cold_base_rows.csv"
)

BASE_SEED = 20260616
N_REPEATS = 12
N_FOLDS = 5
N_BOOT = 400

WIDTH_QS = {"q50": 0.50, "q67": 0.67, "q80": 0.80, "q90": 0.90}
GAP_QS = {"q50": 0.50, "q67": 0.67, "q80": 0.80, "q90": 0.90}
WEIGHTS = [0.20, 0.35, 0.50]
CAPS = [0.050, 0.075, 0.100, 0.150]


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def candidate_name(width_key: str, gap_key: str, weight: float, cap: float) -> str:
    return f"v03_down_to_qf1__width_{width_key}__gap_{gap_key}__w{weight:g}__cap{cap:g}"


def candidate_grid() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for width_key in WIDTH_QS:
        for gap_key in GAP_QS:
            for weight in WEIGHTS:
                for cap in CAPS:
                    out.append(
                        {
                            "candidate": candidate_name(width_key, gap_key, weight, cap),
                            "width_key": width_key,
                            "gap_key": gap_key,
                            "weight": weight,
                            "cap": cap,
                        }
                    )
    return out


def metric_row(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return qf1.metric_row(
        frame["price_krw"].to_numpy(dtype=float),
        frame["ln_price_krw"].to_numpy(dtype=float),
        pred_log,
    )


def thresholds(cal: pd.DataFrame) -> dict[str, float]:
    gap = np.clip(
        cal["research_base_pred_log"].to_numpy(dtype=float) - cal["qf1_avg"].to_numpy(dtype=float),
        0.0,
        None,
    )
    out = {f"width_{k}": float(cal["quantile_width_log"].quantile(q)) for k, q in WIDTH_QS.items()}
    out.update({f"gap_{k}": float(np.quantile(gap, q)) for k, q in GAP_QS.items()})
    return out


def apply_candidate(frame: pd.DataFrame, cfg: dict[str, Any], th: dict[str, float]) -> tuple[np.ndarray, float]:
    base = frame["research_base_pred_log"].to_numpy(dtype=float)
    target = frame["qf1_avg"].to_numpy(dtype=float)
    gap_down = base - target
    mask = (
        (frame["quantile_width_log"].to_numpy(dtype=float) >= th[f"width_{cfg['width_key']}"])
        & (gap_down >= th[f"gap_{cfg['gap_key']}"])
        & (target < base)
    )
    move = np.clip(float(cfg["weight"]) * (target - base), -float(cfg["cap"]), 0.0)
    pred = base.copy()
    pred[mask] = base[mask] + move[mask]
    return pred, float(mask.mean())


def prepare_frames() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    base_features = qf1.artifact_features()["cold_lightgbm"]
    extra = ["medium_support_bucket"]
    train, val, test = qf1.load_scope("cold", list(dict.fromkeys(base_features + extra)))
    need = list(
        dict.fromkeys(
            base_features
            + extra
            + [
                "ln_price_krw",
                "price_krw",
                "log_area",
                "artist_key",
                "_track6_row_id",
                "medium_category",
                "support_category",
                "size_bucket",
            ]
        )
    )
    train = train[need].reset_index(drop=True)
    val = val[need].reset_index(drop=True)
    test = test[need].reset_index(drop=True)

    train_s = qf1.cgrp.train_with_internal_stats(train)
    val_s = qf1.cgrp.assign_group_stats(train, val)
    test_s = qf1.cgrp.assign_group_stats(train, test)
    train_s, val_s, test_s = qf1.add_group_price_proxy(train_s, val_s, test_s)

    full_features = list(dict.fromkeys(base_features + extra + qf1.cgrp.GRP_FULL + ["grp_price_proxy"]))
    lean_features = list(
        dict.fromkeys(
            [
                "log_area",
                "aspect_ratio",
                "has_depth",
                "is_3d_candidate",
                "medium_category",
                "support_category",
                "size_bucket",
            ]
            + qf1.cgrp.GRP_LEAN
            + ["grp_price_proxy"]
        )
    )

    full = qf1.fit_quantile_mean(
        train_s,
        {"validation": val_s, "test": test_s},
        full_features,
        {"q50": 0.50},
        qf1.SEEDS,
    )
    lean = qf1.fit_quantile_mean(
        train_s,
        {"validation": val_s, "test": test_s},
        lean_features,
        {"q50": 0.50},
        qf1.SEEDS,
    )

    base_rows = pd.read_csv(BASE_ROWS)
    out_frames: dict[str, pd.DataFrame] = {}
    for split, frame in (("validation", val_s), ("test", test_s)):
        base = base_rows[base_rows["split"].eq(split)][
            [
                "_track6_row_id",
                "research_base_pred_log",
                "quantile_width_log",
                "guard_pred_log",
                "y18_qwidth_pred_log",
                "v02_defense_pred_log",
            ]
        ].copy()
        merged = frame.merge(base, on="_track6_row_id", how="inner", validate="one_to_one")
        merged = merged.sort_values("_track6_row_id").reset_index(drop=True)
        qf1_avg = 0.5 * full[split]["q50"] + 0.5 * lean[split]["q50"]
        pred_frame = pd.DataFrame(
            {
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "full_q50": full[split]["q50"],
                "lean_q50": lean[split]["q50"],
                "qf1_avg": qf1_avg,
            }
        ).sort_values("_track6_row_id").reset_index(drop=True)
        if not np.array_equal(merged["_track6_row_id"].to_numpy(), pred_frame["_track6_row_id"].to_numpy()):
            raise ValueError(f"{split} qf1 prediction row order mismatch")
        merged["full_q50"] = pred_frame["full_q50"].to_numpy(dtype=float)
        merged["lean_q50"] = pred_frame["lean_q50"].to_numpy(dtype=float)
        merged["qf1_avg"] = pred_frame["qf1_avg"].to_numpy(dtype=float)
        out_frames[split] = merged

    config = {"full_features": full_features, "lean_features": lean_features, "seeds": qf1.SEEDS}
    return out_frames["validation"], out_frames["test"], config


def repeated_holdout(val: pd.DataFrame, configs: list[dict[str, Any]]) -> pd.DataFrame:
    val = val.reset_index(drop=True)
    n = len(val)
    artists = val["artist_key"].astype(str).fillna("__MISSING__")
    uniq = artists.unique()
    rows: list[dict[str, Any]] = []

    for repeat in range(N_REPEATS):
        rng = np.random.default_rng(BASE_SEED + repeat)
        row_folds = np.array_split(rng.permutation(n), N_FOLDS)
        art_folds = np.array_split(rng.permutation(uniq), N_FOLDS)

        plans = [("row_5fold", [(np.setdiff1d(np.arange(n), f), f) for f in row_folds])]
        art_plan = []
        for f in art_folds:
            mask = artists.isin(set(f)).to_numpy()
            art_plan.append((np.flatnonzero(~mask), np.flatnonzero(mask)))
        plans.append(("artist_5fold", art_plan))

        for scheme, folds in plans:
            for fold_id, (tr_idx, ho_idx) in enumerate(folds, start=1):
                cal = val.iloc[tr_idx].reset_index(drop=True)
                hold = val.iloc[ho_idx].reset_index(drop=True)
                th = thresholds(cal)
                base_pred = hold["research_base_pred_log"].to_numpy(dtype=float)
                base_m = metric_row(hold, base_pred)
                for cfg in configs:
                    pred, rate = apply_candidate(hold, cfg, th)
                    m = metric_row(hold, pred)
                    rows.append(
                        {
                            "scheme": scheme,
                            "repeat": repeat,
                            "fold": fold_id,
                            "candidate": cfg["candidate"],
                            "width_key": cfg["width_key"],
                            "gap_key": cfg["gap_key"],
                            "weight": cfg["weight"],
                            "cap": cfg["cap"],
                            "apply_rate": rate,
                            "n": int(len(hold)),
                            **m,
                            "base_MdAPE": base_m["MdAPE"],
                            "base_MAPE": base_m["MAPE"],
                            "base_p95_APE": base_m["p95_APE"],
                            "base_RMSE_log": base_m["RMSE_log"],
                        }
                    )
    out = pd.DataFrame(rows)
    for k in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        base_col = "base_p95_APE" if k == "p95_APE" else f"base_{k}"
        out[f"delta_{k}"] = out[k] - out[base_col]
        out[f"nonworse_{k}"] = out[k] <= out[base_col]
    return out


def summarize_holdout(holdout: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scheme, cand), g in holdout.groupby(["scheme", "candidate"], observed=False):
        first = g.iloc[0]
        rows.append(
            {
                "scheme": scheme,
                "candidate": cand,
                "folds": int(len(g)),
                "width_key": first["width_key"],
                "gap_key": first["gap_key"],
                "weight": float(first["weight"]),
                "cap": float(first["cap"]),
                "mean_apply_rate": float(g["apply_rate"].mean()),
                "mean_delta_MdAPE": float(g["delta_MdAPE"].mean()),
                "mean_delta_MAPE": float(g["delta_MAPE"].mean()),
                "mean_delta_p95_APE": float(g["delta_p95_APE"].mean()),
                "mean_delta_RMSE_log": float(g["delta_RMSE_log"].mean()),
                "prob_MdAPE_nonworse": float(g["nonworse_MdAPE"].mean()),
                "prob_MAPE_nonworse": float(g["nonworse_MAPE"].mean()),
                "prob_p95_nonworse": float(g["nonworse_p95_APE"].mean()),
                "prob_RMSE_nonworse": float(g["nonworse_RMSE_log"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    out["defense_score"] = (
        out["mean_delta_MAPE"]
        + 0.35 * out["mean_delta_p95_APE"]
        + 0.20 * np.maximum(out["mean_delta_MdAPE"], 0.0)
    )
    return out.sort_values(["scheme", "defense_score", "mean_delta_MdAPE"]).reset_index(drop=True)


def combined_summary(summary: pd.DataFrame) -> pd.DataFrame:
    pivots = []
    for cand, g in summary.groupby("candidate", observed=False):
        rec: dict[str, Any] = {"candidate": cand}
        first = g.iloc[0]
        for col in ["width_key", "gap_key", "weight", "cap"]:
            rec[col] = first[col]
        for _, r in g.iterrows():
            prefix = "row" if r["scheme"] == "row_5fold" else "artist"
            for col in [
                "mean_apply_rate",
                "mean_delta_MdAPE",
                "mean_delta_MAPE",
                "mean_delta_p95_APE",
                "prob_MdAPE_nonworse",
                "prob_MAPE_nonworse",
                "prob_p95_nonworse",
            ]:
                rec[f"{prefix}_{col}"] = r[col]
        rec["combined_score"] = (
            rec.get("row_mean_delta_MAPE", 0)
            + rec.get("artist_mean_delta_MAPE", 0)
            + 0.35 * (rec.get("row_mean_delta_p95_APE", 0) + rec.get("artist_mean_delta_p95_APE", 0))
            + 0.20
            * (
                max(rec.get("row_mean_delta_MdAPE", 0), 0)
                + max(rec.get("artist_mean_delta_MdAPE", 0), 0)
            )
        )
        rec["holdout_pass"] = bool(
            rec.get("row_prob_MAPE_nonworse", 0) >= 0.70
            and rec.get("artist_prob_MAPE_nonworse", 0) >= 0.70
            and rec.get("row_prob_p95_nonworse", 0) >= 0.70
            and rec.get("artist_prob_p95_nonworse", 0) >= 0.70
            and rec.get("row_prob_MdAPE_nonworse", 0) >= 0.45
            and rec.get("artist_prob_MdAPE_nonworse", 0) >= 0.45
        )
        pivots.append(rec)
    out = pd.DataFrame(pivots)
    return out.sort_values(["holdout_pass", "combined_score"], ascending=[False, True]).reset_index(drop=True)


def fixed_test_metrics(val: pd.DataFrame, test: pd.DataFrame, configs: list[dict[str, Any]]) -> pd.DataFrame:
    th = thresholds(val)
    base = metric_row(test, test["research_base_pred_log"].to_numpy(dtype=float))
    rows = [
        {
            "candidate": "current_v03_research_guard_search",
            "apply_rate": 1.0,
            **base,
            "delta_MdAPE": 0.0,
            "delta_MAPE": 0.0,
            "delta_p95_APE": 0.0,
            "delta_RMSE_log": 0.0,
        }
    ]
    for cfg in configs:
        pred, rate = apply_candidate(test, cfg, th)
        m = metric_row(test, pred)
        rows.append(
            {
                "candidate": cfg["candidate"],
                "apply_rate": rate,
                **m,
                "delta_MdAPE": m["MdAPE"] - base["MdAPE"],
                "delta_MAPE": m["MAPE"] - base["MAPE"],
                "delta_p95_APE": m["p95_APE"] - base["p95_APE"],
                "delta_RMSE_log": m["RMSE_log"] - base["RMSE_log"],
            }
        )
    return pd.DataFrame(rows)


def test_artist_bootstrap(test: pd.DataFrame, configs: list[dict[str, Any]], th: dict[str, float]) -> pd.DataFrame:
    rng = np.random.default_rng(BASE_SEED + 999)
    groups = pd.Series(np.arange(len(test))).groupby(test["artist_key"].astype(str).to_numpy()).apply(list)
    base_pred = test["research_base_pred_log"].to_numpy(dtype=float)
    preds = {}
    for cfg in configs:
        preds[cfg["candidate"]] = apply_candidate(test, cfg, th)[0]
    rows = []
    for cfg in configs:
        wins = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0, "RMSE_log": 0}
        deltas: dict[str, list[float]] = {k: [] for k in wins}
        pred = preds[cfg["candidate"]]
        for _ in range(N_BOOT):
            choice = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[i] for i in choice])
            part = test.iloc[idx].reset_index(drop=True)
            bm = metric_row(part, base_pred[idx])
            cm = metric_row(part, pred[idx])
            for k in wins:
                d = cm[k] - bm[k]
                deltas[k].append(d)
                wins[k] += d <= 0.0
        rec: dict[str, Any] = {"candidate": cfg["candidate"]}
        for k in wins:
            arr = np.asarray(deltas[k], dtype=float)
            rec[f"boot_prob_{k}_nonworse"] = float(wins[k] / N_BOOT)
            rec[f"boot_median_delta_{k}"] = float(np.median(arr))
            rec[f"boot_q05_delta_{k}"] = float(np.quantile(arr, 0.05))
            rec[f"boot_q95_delta_{k}"] = float(np.quantile(arr, 0.95))
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    configs = candidate_grid()
    val, test, prep_config = prepare_frames()

    holdout = repeated_holdout(val, configs)
    holdout.to_csv(EXP_DIR / "outputs" / "repeated_holdout_metrics.csv", index=False)
    summary = summarize_holdout(holdout)
    summary.to_csv(EXP_DIR / "outputs" / "holdout_summary.csv", index=False)
    combined = combined_summary(summary)
    combined.to_csv(EXP_DIR / "outputs" / "combined_holdout_summary.csv", index=False)

    top_configs = []
    config_by_name = {cfg["candidate"]: cfg for cfg in configs}
    for name in combined["candidate"].head(20).astype(str):
        top_configs.append(config_by_name[name])
    test_metrics = fixed_test_metrics(val, test, top_configs)
    test_metrics.to_csv(EXP_DIR / "outputs" / "fixed_test_top_metrics.csv", index=False)
    boot = test_artist_bootstrap(test, top_configs[:12], thresholds(val))
    boot.to_csv(EXP_DIR / "outputs" / "fixed_test_artist_bootstrap.csv", index=False)

    run_config = {
        "experiment_id": EXP_ID,
        "purpose": "Repeated row/artist holdout revalidation of QF1 conditional v0.3 down-to-qf1 guard",
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "n_bootstrap": N_BOOT,
        "width_quantiles": WIDTH_QS,
        "gap_quantiles": GAP_QS,
        "weights": WEIGHTS,
        "caps": CAPS,
        "preparation": prep_config,
        "selection": "validation repeated holdout ranking; fixed test reported after ranking",
        "prohibitions": ["0604 데이터 사용 금지", "test로 후보 선택 금지"],
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(
        json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    show_combined_cols = [
        "candidate",
        "holdout_pass",
        "row_mean_delta_MdAPE",
        "row_mean_delta_MAPE",
        "row_mean_delta_p95_APE",
        "artist_mean_delta_MdAPE",
        "artist_mean_delta_MAPE",
        "artist_mean_delta_p95_APE",
        "row_prob_MdAPE_nonworse",
        "row_prob_MAPE_nonworse",
        "row_prob_p95_nonworse",
        "artist_prob_MdAPE_nonworse",
        "artist_prob_MAPE_nonworse",
        "artist_prob_p95_nonworse",
        "combined_score",
    ]
    show_test_cols = [
        "candidate",
        "apply_rate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
    ]
    show_boot_cols = [
        "candidate",
        "boot_prob_MdAPE_nonworse",
        "boot_prob_MAPE_nonworse",
        "boot_prob_p95_APE_nonworse",
        "boot_median_delta_MdAPE",
        "boot_median_delta_MAPE",
        "boot_median_delta_p95_APE",
    ]

    best = combined.iloc[0]
    report = "\n".join(
        [
            "# PP-COLD-QF2 조건부 Cold guard 반복 검증",
            "",
            "## 목적",
            "- QF1에서 유망했던 `v0.3 예측을 qf1 평균 쪽으로 제한적으로 낮추는 guard`가 validation 반복 holdout에서도 유지되는지 확인했다.",
            "- threshold는 각 holdout의 calibration 구간에서 다시 계산했다. 정답값은 threshold 계산에 사용하지 않았다.",
            "- fixed test는 validation 반복 검증으로 상위 후보를 고른 뒤 확인용으로만 보고했다.",
            "",
            "## 반복 holdout 상위 후보",
            qf1.md_table(combined[show_combined_cols].head(12)),
            "",
            "## fixed test 확인",
            qf1.md_table(test_metrics[show_test_cols].head(21)),
            "",
            "## fixed test artist bootstrap",
            qf1.md_table(boot[show_boot_cols].head(12)),
            "",
            "## 현재 판단",
            f"- 반복 holdout 1위 후보: `{best['candidate']}`",
            f"- holdout 통과 여부: `{bool(best['holdout_pass'])}`",
            "- 통과 기준: row/artist 양쪽에서 MAPE와 p95 nonworse 확률 0.70 이상, MdAPE nonworse 확률 0.45 이상.",
            "- 통과 후보가 fixed test에서도 MAPE/p95를 낮추고 artist bootstrap에서 p95 nonworse 확률이 높으면 방어층 후보로 남긴다.",
            "- 단 MdAPE가 악화되면 대표 가격 교체가 아니라 low-risk/p95 방어 목적의 별도 정책 후보로만 해석한다.",
            "",
            "## 산출물",
            f"- 실험 폴더: `{EXP_DIR.relative_to(REPO)}`",
            "- `outputs/repeated_holdout_metrics.csv`: fold별 전체 후보 지표.",
            "- `outputs/holdout_summary.csv`: row/artist scheme별 요약.",
            "- `outputs/combined_holdout_summary.csv`: row+artist 통합 순위.",
            "- `outputs/fixed_test_top_metrics.csv`: validation 상위 후보 fixed test 확인.",
            "- `outputs/fixed_test_artist_bootstrap.csv`: test artist bootstrap 확인.",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    qf1.write_simple_html(report, EXP_DIR / "reports" / "result_report.html")
    (DOC_ROOT / "pp_cold_qf2_conditional_guard_revalidation_summary.md").write_text(report, encoding="utf-8")

    print(combined[show_combined_cols].head(12).round(6).to_string(index=False))
    print()
    print(test_metrics[show_test_cols].head(21).round(6).to_string(index=False))
    print()
    print(boot[show_boot_cols].head(12).round(6).to_string(index=False))
    print(f"\n[{EXP_ID}] wrote {EXP_DIR}")


if __name__ == "__main__":
    main()
