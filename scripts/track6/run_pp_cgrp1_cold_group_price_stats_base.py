#!/usr/bin/env python3
"""PP-CGRP1: 비교군 그룹 가격 통계의 Cold base 투입 (Cold 성능 개선 경로 ①).

Warm 기준가에서 가장 강력했던 비교군 가격 통계(svc_group_*)의 작가 미사용
버전을 Cold base에 처음으로 투입한다. PP-Y 라인은 전시/갤러리/검색/작가메타
축만 검증했고 그룹 가격 통계는 미검증 갭(2026-06-10 확인).

- 매칭 사다리(작가 미사용, Warm L4~L7과 동일 구조):
    L1 medium_support_bucket + size_bucket (min 30)
    L2 medium_category + support_category + size_bucket (min 30)
    L3 medium_category + size_bucket (min 50)
    L4 전체 train fallback
- leakage 차단: train 행의 통계는 5-fold 내부에서 자기 fold 제외로 계산.
  validation/test/pseudo-cold의 통계는 (해당 학습 train) 전체 기준.
- 후보: base12 / base12+grp_full(8피처) / base12+grp_lean(4피처)
- 경량 게이트(base 재학습용): validation 3지표 + artist-cluster bootstrap
  (400회, MAPE/p95 개선확률 >=0.90) + seed 3 학습분산 + pseudo-cold(PP-PCOLD1
  마스크 3 seed) delta 방향 일치 + fixed test 1회.
- 0604는 Warm 시험 제출 전용 — 사용하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-CGRP1_cold_group_price_stats_base"

LADDER = [
    (["medium_support_bucket", "size_bucket"], 30),
    (["medium_category", "support_category", "size_bucket"], 30),
    (["medium_category", "size_bucket"], 50),
]
GRP_FULL = ["grp_log_price_median", "grp_log_price_q25", "grp_log_price_q75",
            "grp_log_price_iqr", "grp_unit_area_median", "grp_unit_area_iqr",
            "grp_n_log", "grp_match_level"]
GRP_LEAN = ["grp_log_price_median", "grp_log_price_iqr", "grp_n_log", "grp_match_level"]
CATEGORICAL = {"medium_category", "support_category", "size_bucket", "support_size_bucket"}
QUANTILES = {"q10": 0.10, "q40": 0.40, "q50": 0.50, "q90": 0.90}
SEEDS = [20260610, 20260611, 20260612]
PCOLD_SEEDS = [20260610, 20260611, 20260612]
N_BOOT = 400
N_ESTIMATORS = 900


def quantile_pipeline(features: list[str], alpha: float, seed: int) -> Pipeline:
    numeric = [f for f in features if f not in CATEGORICAL]
    categorical = [f for f in features if f in CATEGORICAL]
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(objective="quantile", alpha=alpha, n_estimators=N_ESTIMATORS,
                                learning_rate=0.035, num_leaves=31, min_child_samples=35,
                                subsample=0.9, colsample_bytree=0.9, reg_lambda=1.2,
                                random_state=seed, verbosity=-1)),
    ])


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}


def group_stat_table(ref: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g = ref.assign(_unit=ref["ln_price_krw"] - ref["log_area"].clip(lower=0)).groupby(keys)
    t = g.agg(grp_log_price_median=("ln_price_krw", "median"),
              grp_log_price_q25=("ln_price_krw", lambda s: s.quantile(0.25)),
              grp_log_price_q75=("ln_price_krw", lambda s: s.quantile(0.75)),
              grp_unit_area_median=("_unit", "median"),
              grp_unit_area_q25=("_unit", lambda s: s.quantile(0.25)),
              grp_unit_area_q75=("_unit", lambda s: s.quantile(0.75)),
              grp_n=("ln_price_krw", "size")).reset_index()
    t["grp_log_price_iqr"] = t["grp_log_price_q75"] - t["grp_log_price_q25"]
    t["grp_unit_area_iqr"] = t["grp_unit_area_q75"] - t["grp_unit_area_q25"]
    return t


def assign_group_stats(ref: pd.DataFrame, query: pd.DataFrame) -> pd.DataFrame:
    out = query.copy()
    for c in GRP_FULL:
        out[c] = np.nan
    unassigned = pd.Series(True, index=out.index)
    for level, (keys, min_n) in enumerate(LADDER, start=1):
        if not unassigned.any():
            break
        t = group_stat_table(ref, keys)
        t = t[t["grp_n"] >= min_n]
        merged = out.loc[unassigned, keys].merge(t, on=keys, how="left")
        merged.index = out.index[unassigned]
        hit = merged["grp_n"].notna()
        idx = merged.index[hit]
        for c in ["grp_log_price_median", "grp_log_price_q25", "grp_log_price_q75",
                  "grp_log_price_iqr", "grp_unit_area_median", "grp_unit_area_iqr"]:
            out.loc[idx, c] = merged.loc[hit, c].to_numpy()
        out.loc[idx, "grp_n_log"] = np.log1p(merged.loc[hit, "grp_n"].to_numpy(dtype=float))
        out.loc[idx, "grp_match_level"] = float(level)
        unassigned.loc[idx] = False
    if unassigned.any():  # 전체 train fallback
        out.loc[unassigned, "grp_log_price_median"] = ref["ln_price_krw"].median()
        out.loc[unassigned, "grp_log_price_q25"] = ref["ln_price_krw"].quantile(0.25)
        out.loc[unassigned, "grp_log_price_q75"] = ref["ln_price_krw"].quantile(0.75)
        out.loc[unassigned, "grp_log_price_iqr"] = (out.loc[unassigned, "grp_log_price_q75"]
                                                    - out.loc[unassigned, "grp_log_price_q25"])
        unit = ref["ln_price_krw"] - ref["log_area"].clip(lower=0)
        out.loc[unassigned, "grp_unit_area_median"] = unit.median()
        out.loc[unassigned, "grp_unit_area_iqr"] = unit.quantile(0.75) - unit.quantile(0.25)
        out.loc[unassigned, "grp_n_log"] = np.log1p(len(ref))
        out.loc[unassigned, "grp_match_level"] = float(len(LADDER) + 1)
    return out


def train_with_internal_stats(train: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for tr_idx, va_idx in KFold(n_splits=5, shuffle=True, random_state=20260610).split(train):
        parts.append(assign_group_stats(train.iloc[tr_idx], train.iloc[va_idx]))
    return pd.concat(parts).loc[train.index]


def fit_predict(train: pd.DataFrame, evals: dict[str, pd.DataFrame],
                features: list[str], seed: int) -> dict[str, dict[str, np.ndarray]]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    models = {q: quantile_pipeline(features, a, seed).fit(train[features], y)
              for q, a in QUANTILES.items()}
    return {name: {q: np.asarray(m.predict(f[features]), dtype=float) for q, m in models.items()}
            for name, f in evals.items()}


def rep_and_defense(preds: dict[str, np.ndarray], guard: dict | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    rep, comp = preds["q50"], preds["q40"]
    width = preds["q90"] - preds["q10"]
    if guard is None:
        guard = {"width_q67": float(np.quantile(width, 0.67)),
                 "gap_q50": float(np.quantile(rep - comp, 0.50))}
    mask = (width >= guard["width_q67"]) & ((rep - comp) >= guard["gap_q50"]) & (comp < rep)
    defense = rep.copy()
    defense[mask] = 0.5 * rep[mask] + 0.5 * comp[mask]
    return rep, defense, guard


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260610)

    base_feats = artifact_features()["cold_lightgbm"]
    train, val, test = load_scope("cold", base_feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(
        base_feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                      "price_krw", "_track6_row_id"]
        + (["artist_key"] if "artist_key" in train.columns else [])))
    train = train[need].reset_index(drop=True)
    val = val.reset_index(drop=True)
    test = test.reset_index(drop=True)

    train_s = train_with_internal_stats(train)
    val_s = assign_group_stats(train, val)
    test_s = assign_group_stats(train, test)

    candidates = {"base12": base_feats,
                  "base12_grp_full": base_feats + GRP_FULL,
                  "base12_grp_lean": base_feats + GRP_LEAN}

    # ── seed 3 학습, validation/test rep+defense (guard는 validation label-free)
    preds_store: dict[str, dict[str, list[np.ndarray]]] = {
        c: {"val_rep": [], "val_def": [], "test_rep": [], "test_def": []} for c in candidates}
    for seed in SEEDS:
        for cname, feats in candidates.items():
            p = fit_predict(train_s, {"val": val_s, "test": test_s}, feats, seed)
            vrep, vdef, guard = rep_and_defense(p["val"])
            trep, tdef, _ = rep_and_defense(p["test"], guard)
            preds_store[cname]["val_rep"].append(vrep)
            preds_store[cname]["val_def"].append(vdef)
            preds_store[cname]["test_rep"].append(trep)
            preds_store[cname]["test_def"].append(tdef)

    def seed_mean(c, k):
        return np.mean(preds_store[c][k], axis=0)

    rows = []
    for cname in candidates:
        for split, frame, kr, kd in (("validation", val, "val_rep", "val_def"),
                                     ("test", test, "test_rep", "test_def")):
            price = frame["price_krw"].to_numpy(dtype=float)
            for role, key in (("representative", kr), ("defense", kd)):
                per_seed = [metric_triplet(price, p)["MAPE"] for p in preds_store[cname][key]]
                rows.append({"candidate": cname, "split": split, "role": role,
                             **metric_triplet(price, seed_mean(cname, key)),
                             "seed_MAPE_std": float(np.std(per_seed))})
    summary = pd.DataFrame(rows)
    summary.to_csv(EXP / "outputs" / "candidate_metrics.csv", index=False)

    # ── validation artist-cluster bootstrap (defense, seed-mean, base12 대비)
    val_price = val["price_krw"].to_numpy(dtype=float)
    val_art = val["artist_key"].astype(str).to_numpy() if "artist_key" in val.columns else None
    art_groups = pd.Series(np.arange(len(val))).groupby(val_art).apply(list) if val_art is not None else None
    boot_rows = []
    base_def = seed_mean("base12", "val_def")
    for cname in ("base12_grp_full", "base12_grp_lean"):
        cand_def = seed_mean(cname, "val_def")
        wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
        for _ in range(N_BOOT):
            arts = rng.choice(len(art_groups), size=len(art_groups), replace=True)
            idx = np.concatenate([art_groups.iloc[a] for a in arts])
            bm = metric_triplet(val_price[idx], base_def[idx])
            cm = metric_triplet(val_price[idx], cand_def[idx])
            wins["MAPE"] += cm["MAPE"] < bm["MAPE"]
            wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
            wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
        boot_rows.append({"candidate": cname,
                          **{f"p_{k}": v / N_BOOT for k, v in wins.items()}})
    boot = pd.DataFrame(boot_rows)
    boot.to_csv(EXP / "outputs" / "validation_artist_bootstrap.csv", index=False)

    # ── pseudo-cold 외부 검증 (PP-PCOLD1 마스크 규칙 재현, delta 방향)
    counts = train.groupby("artist_key").size()
    pool = counts[(counts >= 3) & (counts <= 10)].index.to_numpy()
    pc_rows = []
    for pseed in PCOLD_SEEDS:
        prng = np.random.default_rng(pseed)
        order = prng.permutation(pool)
        masked, total = [], 0
        for a in order:
            if total >= 1200 or len(masked) >= 250:
                break
            masked.append(a)
            total += int(counts[a])
        is_m = train["artist_key"].isin(set(masked))
        tr_m, pseudo = train[~is_m], train[is_m]
        tr_ms = train_with_internal_stats(tr_m)
        pseudo_s = assign_group_stats(tr_m, pseudo)
        val_ms = assign_group_stats(tr_m, val)
        price = pseudo["price_krw"].to_numpy(dtype=float)
        for cname in ("base12", "base12_grp_lean", "base12_grp_full"):
            p = fit_predict(tr_ms, {"pseudo": pseudo_s, "val": val_ms}, candidates[cname], SEEDS[0])
            _, _, guard = rep_and_defense(p["val"])
            _, pdef, _ = rep_and_defense(p["pseudo"], guard)
            pc_rows.append({"pcold_seed": pseed, "candidate": cname,
                            **metric_triplet(price, pdef)})
    pc = pd.DataFrame(pc_rows)
    pc.to_csv(EXP / "outputs" / "pseudo_cold_metrics.csv", index=False)
    pc_dir = []
    for pseed, part in pc.groupby("pcold_seed"):
        m = part.set_index("candidate")
        pc_dir.append({"pcold_seed": int(pseed),
                       "lean_improves_MAPE": bool(m.loc["base12_grp_lean", "MAPE"] < m.loc["base12", "MAPE"]),
                       "full_improves_MAPE": bool(m.loc["base12_grp_full", "MAPE"] < m.loc["base12", "MAPE"])})

    match_share = val_s["grp_match_level"].value_counts(normalize=True).sort_index().to_dict()
    config = {
        "experiment_id": "PP-CGRP1",
        "purpose": "작가 미사용 비교군 그룹 가격 통계의 Cold base 투입 (PP-Y 라인 미검증 갭)",
        "ladder": [{"keys": k, "min_n": n} for k, n in LADDER],
        "leakage_control": "train 통계는 5-fold 자기 fold 제외, val/test/pseudo는 학습 train 전체 기준",
        "candidates": {k: len(v) for k, v in candidates.items()},
        "seeds": SEEDS, "n_boot_artist_cluster": N_BOOT,
        "val_match_level_share": {str(k): float(v) for k, v in match_share.items()},
        "gate": "validation 3지표 + artist-cluster bootstrap MAPE/p95>=0.90 + pseudo-cold 3seed 방향 일치 + fixed test 1회",
        "pseudo_cold_direction": pc_dir,
        "prohibitions": ["0604 사용 금지", "test 후보 선택 금지(최종 확인 1회)"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = ["# PP-CGRP1 비교군 그룹 가격 통계 base 투입", "",
              "## 후보 지표 (seed 3 평균 예측)", "", summary.round(4).to_string(index=False), "",
              "## validation artist-cluster bootstrap (defense, vs base12)", "",
              boot.round(4).to_string(index=False), "",
              "## pseudo-cold (PP-PCOLD1 마스크)", "", pc.round(4).to_string(index=False), "",
              json.dumps(pc_dir, ensure_ascii=False)]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(summary.round(4).to_string(index=False))
    print()
    print(boot.round(4).to_string(index=False))
    print()
    print(pc.round(4).to_string(index=False))
    print(json.dumps(pc_dir, ensure_ascii=False))
    print("val match level share:", {str(k): round(float(v), 3) for k, v in match_share.items()})


if __name__ == "__main__":
    main()
