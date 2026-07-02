#!/usr/bin/env python3
"""PP-WCUT5: Warm-lite Huber 6구성 근거 확인 ablation.

PP-WCUT4와 같은 실존 저이력 작가 leave-one-out 설계를 사용해 Warm-lite의
Huber 6구성 평균이 단일 구성, full 구성만, lean 구성만보다 실제로 안정적인지
확인한다.

- 평가행: train 이력 2~5건 실존 작가에서 seed별 작가당 1작품 hold-out
- 예측: hold-out 제외 train으로 min1 작가 사다리 통계 생성 후 Huber 구성별 학습
- 후보:
  c0~c5 단일 구성, full4(c0~c3), lean2(c4~c5), all6(c0~c5 현재 Warm-lite)
- 산출: overall/k별 지표, all6 대비 bootstrap 승률, 구성 메타데이터
- 0604 미사용.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_s = importlib.util.spec_from_file_location("cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py")
cgrp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(cgrp)
_s1 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s1)
_s1.loader.exec_module(cb1)
_s3 = importlib.util.spec_from_file_location("cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py")
cb3 = importlib.util.module_from_spec(_s3)
_s3.loader.exec_module(cb3)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WCUT5_warm_lite_huber_component_ablation"
SEEDS = [20260612, 20260613, 20260614]
ROWS_MIN, ROWS_MAX = 2, 5
N_BOOT = 400
LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]

COMPONENT_LABELS = {
    "c0": "full_alpha1e-4_eps1.35",
    "c1": "full_alpha1e-3_eps1.35",
    "c2": "full_alpha1e-4_eps1.20",
    "c3": "full_alpha1e-4_eps1.50",
    "c4": "lean_alpha1e-4_eps1.35",
    "c5": "lean_alpha1e-3_eps1.50",
}

CANDIDATES = {
    "all6_current": ["c0", "c1", "c2", "c3", "c4", "c5"],
    "full4_only": ["c0", "c1", "c2", "c3"],
    "lean2_only": ["c4", "c5"],
    "c0_full_default": ["c0"],
    "c1_full_more_regularized": ["c1"],
    "c2_full_low_epsilon": ["c2"],
    "c3_full_high_epsilon": ["c3"],
    "c4_lean_default": ["c4"],
    "c5_lean_regularized_high_epsilon": ["c5"],
}


def component_metadata() -> pd.DataFrame:
    rows = []
    for i, cfg in enumerate(cb3.C_CONFIGS):
        extra = cfg["extra"]
        if extra == cgrp.GRP_FULL:
            feature_set = "full"
        elif extra == cgrp.GRP_LEAN:
            feature_set = "lean"
        else:
            feature_set = "custom"
        rows.append({
            "component": f"c{i}",
            "label": COMPONENT_LABELS[f"c{i}"],
            "feature_set": feature_set,
            "alpha": cfg["alpha"],
            "epsilon": cfg["epsilon"],
            "n_num_cols": len(cb3.NUM_BASE + extra),
            "uses_q25_q75": "grp_log_price_q25" in extra and "grp_log_price_q75" in extra,
            "uses_unit_area_iqr": "grp_unit_area_iqr" in extra,
        })
    return pd.DataFrame(rows)


def fit_component_predictions(train_s: pd.DataFrame, held_s: pd.DataFrame) -> pd.DataFrame:
    """Huber 6개 구성 각각의 hold-out 예측 로그가격을 반환."""
    train_s = train_s.copy()
    held_s = held_s.copy()
    for frame in (train_s, held_s):
        frame["grp_price_proxy"] = frame["grp_unit_area_median"] + frame["log_area"].clip(lower=0)
    y = train_s["ln_price_krw"].to_numpy(dtype=float)

    out = pd.DataFrame(index=held_s.index)
    for i, cfg in enumerate(cb3.C_CONFIGS):
        num = cb3.NUM_BASE + cfg["extra"]
        pipe = Pipeline([
            ("prep", ColumnTransformer([
                ("num", Pipeline([
                    ("i", SimpleImputer(strategy="median")),
                    ("s", StandardScaler()),
                ]), num),
                ("cat", OneHotEncoder(handle_unknown="ignore"), cb3.CAT_C),
            ])),
            ("m", HuberRegressor(epsilon=cfg["epsilon"], alpha=cfg["alpha"], max_iter=4000)),
        ])
        pipe.fit(train_s[num + cb3.CAT_C], y)
        out[f"c{i}"] = np.asarray(pipe.predict(held_s[num + cb3.CAT_C]), dtype=float)
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
    component_preds = fit_component_predictions(tr_s, held_s)
    artist_match = (held_s["grp_match_level"] <= len(LITE_LADDER)).to_numpy()
    cgrp.LADDER = base_ladder

    out = pd.DataFrame({
        "seed": seed,
        "_row": held_idx,
        "artist_key": held["artist_key"].to_numpy(),
        "history_k": held["artist_key"].map(counts - 1).astype(int).to_numpy(),
        "actual_price": held["price_krw"].to_numpy(dtype=float),
        "artist_match": artist_match,
    })
    for comp in component_preds.columns:
        out[comp] = component_preds[comp].to_numpy(dtype=float)
    for candidate, comps in CANDIDATES.items():
        out[f"{candidate}_pred_log"] = component_preds[comps].mean(axis=1).to_numpy(dtype=float)
    return out


def metric_rows(preds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall_rows = []
    by_k_rows = []
    for candidate in CANDIDATES:
        col = f"{candidate}_pred_log"
        m = cb1.mt(preds["actual_price"].to_numpy(dtype=float), preds[col].to_numpy(dtype=float))
        overall_rows.append({
            "candidate": candidate,
            "components": ",".join(CANDIDATES[candidate]),
            "n": len(preds),
            **{k: round(v, 6) for k, v in m.items()},
        })
        for k, group in preds.groupby("history_k"):
            gm = cb1.mt(group["actual_price"].to_numpy(dtype=float), group[col].to_numpy(dtype=float))
            by_k_rows.append({
                "candidate": candidate,
                "history_k": int(k),
                "n": len(group),
                **{mk: round(v, 6) for mk, v in gm.items()},
            })
    overall = pd.DataFrame(overall_rows)
    for metric in ("MdAPE", "MAPE", "p95_APE"):
        overall[f"rank_{metric}"] = overall[metric].rank(method="min").astype(int)
        base = float(overall.loc[overall["candidate"].eq("all6_current"), metric].iloc[0])
        overall[f"delta_{metric}_minus_all6"] = overall[metric] - base
    return overall.sort_values(["MAPE", "p95_APE", "MdAPE"]), pd.DataFrame(by_k_rows).sort_values(["history_k", "candidate"])


def bootstrap_rows(preds: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    groups = pd.Series(np.arange(len(preds))).groupby(preds["artist_key"].to_numpy()).apply(list)
    price = preds["actual_price"].to_numpy(dtype=float)
    base = preds["all6_current_pred_log"].to_numpy(dtype=float)
    rows = []
    for candidate in CANDIDATES:
        if candidate == "all6_current":
            continue
        cand = preds[f"{candidate}_pred_log"].to_numpy(dtype=float)
        wins = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
        ties = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
        for _ in range(N_BOOT):
            sampled = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[g] for g in sampled])
            bm = cb1.mt(price[idx], base[idx])
            cm = cb1.mt(price[idx], cand[idx])
            for metric in wins:
                wins[metric] += bm[metric] < cm[metric]
                ties[metric] += bm[metric] == cm[metric]
        row = {
            "comparison": f"all6_current_vs_{candidate}",
            "candidate": candidate,
            "n_boot": N_BOOT,
        }
        for metric in wins:
            row[f"p_all6_better_{metric}"] = wins[metric] / N_BOOT
            row[f"p_tie_{metric}"] = ties[metric] / N_BOOT
        rows.append(row)
    return pd.DataFrame(rows).sort_values("candidate")


def write_report(overall: pd.DataFrame, by_k: pd.DataFrame, boot: pd.DataFrame, meta: pd.DataFrame, config: dict) -> None:
    lines = [
        "# PP-WCUT5 Warm-lite Huber 6구성 ablation",
        "",
        "## 실험 목적",
        "",
        "Warm-lite의 현재 6개 Huber 구성 평균이 단일 구성, full 구성만, lean 구성만보다 안정적인지 확인한다.",
        "",
        "## 구성 메타데이터",
        "",
        meta.to_string(index=False),
        "",
        "## Overall metrics",
        "",
        overall.to_string(index=False),
        "",
        "## Metrics by history_k",
        "",
        by_k.to_string(index=False),
        "",
        "## all6 vs ablations bootstrap",
        "",
        boot.round(4).to_string(index=False),
        "",
        "## Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    feats = artifact_features()["cold_lightgbm"]
    train, _, _ = load_scope("warm", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + [
        "medium_support_bucket",
        "ln_price_krw",
        "log_area",
        "price_krw",
        "artist_key",
    ]))
    train = train[need].reset_index(drop=True)
    base_ladder = list(cgrp.LADDER)

    parts = []
    for seed in SEEDS:
        checkpoint = EXP / "outputs" / f"preds_seed{seed}.csv"
        if checkpoint.exists():
            print(f"[resume] seed {seed} checkpoint found")
            parts.append(pd.read_csv(checkpoint))
            continue
        part = run_seed(seed, train, base_ladder)
        part.to_csv(checkpoint, index=False)
        print(f"[done] seed {seed}: {len(part)} rows")
        parts.append(part)

    preds = pd.concat(parts, ignore_index=True)
    preds.to_csv(EXP / "outputs" / "predictions_all_seeds.csv", index=False)

    meta = component_metadata()
    overall, by_k = metric_rows(preds)
    boot = bootstrap_rows(preds)
    meta.to_csv(EXP / "outputs" / "component_metadata.csv", index=False)
    overall.to_csv(EXP / "outputs" / "candidate_metrics_overall.csv", index=False)
    by_k.to_csv(EXP / "outputs" / "candidate_metrics_by_k.csv", index=False)
    boot.to_csv(EXP / "outputs" / "all6_vs_ablation_bootstrap.csv", index=False)

    all6 = overall[overall["candidate"].eq("all6_current")].iloc[0]
    best_by_metric = {
        metric: str(overall.sort_values(metric).iloc[0]["candidate"])
        for metric in ("MdAPE", "MAPE", "p95_APE")
    }
    config = {
        "experiment_id": "PP-WCUT5",
        "eval_design": f"PP-WCUT4 same real low-history leave-one-out, train history {ROWS_MIN}~{ROWS_MAX}, seeds {SEEDS}",
        "rows": int(len(preds)),
        "artist_count": int(preds["artist_key"].nunique()),
        "candidates": CANDIDATES,
        "all6_current_metrics": {m: float(all6[m]) for m in ("MdAPE", "MAPE", "p95_APE")},
        "best_by_metric": best_by_metric,
        "bootstrap": "artist-cluster bootstrap comparing all6_current vs each ablation",
        "n_boot": N_BOOT,
        "prohibitions": ["0604 사용 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(overall, by_k, boot, meta, config)

    print("[overall]")
    print(overall[["candidate", "components", "n", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_minus_all6", "delta_MAPE_minus_all6", "delta_p95_APE_minus_all6"]].to_string(index=False))
    print("[bootstrap]")
    print(boot.round(4).to_string(index=False))
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
