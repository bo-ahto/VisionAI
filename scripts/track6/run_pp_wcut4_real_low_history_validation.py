#!/usr/bin/env python3
"""PP-WCUT4: 실존 저이력 작가 leave-one-out 검증 (라우팅 재검증 1단계).

WCUT1/2의 한계(이력 5+ 작가의 절단 시뮬레이션)를 제거: train에 실존하는
이력 2~5건 작가 649명에서 작가당 1작품을 hold-out → 남은 이력 1~4건으로
Warm-lite vs Cold serving을 직접 비교한다.

- leakage 차단: Warm-lite·Cold 모두 hold-out 행을 제외한 train으로 재학습.
  Warm-lite 통계는 fold-제외(cgrp), 평가행 통계는 잔여 이력에서 계산
- hold-out seed 3개. **seed별 체크포인트**(outputs/preds_seed*.csv) — 중단 시
  재실행만으로 완료된 seed를 건너뛰고 이어서 진행
- 게이트: 통합 평가행에서 artist-cluster bootstrap 400회 — Warm-lite의
  MdAPE/MAPE/p95 개선확률 >= 0.90 (vs Cold serving)
- 산출: k(잔여 이력)별 성능, WCUT2 절단 시뮬과의 괴리, 데이터 해시 동결
- 0604 미사용.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_s = importlib.util.spec_from_file_location("cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py")
cgrp = importlib.util.module_from_spec(_s); _s.loader.exec_module(cgrp)
_s1 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s1); _s1.loader.exec_module(cb1)
_s3 = importlib.util.spec_from_file_location("cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py")
cb3 = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(cb3)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WCUT4_real_low_history_validation"
SEEDS = [20260612, 20260613, 20260614]
ROWS_MIN, ROWS_MAX = 2, 5
N_BOOT = 400
UNCOVERED_CONST = -0.031295
LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]
WCUT2_SIM_REF = {1: 0.2179, 2: 0.1739, 3: 0.1597, 4: 0.1457}


def sha_df(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).to_numpy().tobytes()).hexdigest()[:16]


def run_seed(seed: int, train: pd.DataFrame, feats: list[str], wval: pd.DataFrame,
             base_ladder: list) -> pd.DataFrame:
    """한 hold-out seed의 평가 예측을 계산 (체크포인트 단위)."""
    rng = np.random.default_rng(seed)
    counts = train.groupby("artist_key").size()
    low_artists = counts[(counts >= ROWS_MIN) & (counts <= ROWS_MAX)].index
    held_idx = []
    for a in low_artists:
        idx = np.where(train["artist_key"].to_numpy() == a)[0]
        held_idx.append(int(rng.choice(idx)))
    held = train.iloc[held_idx].reset_index(drop=True)
    tr_rest = train.drop(index=train.index[held_idx]).reset_index(drop=True)
    y = tr_rest["ln_price_krw"].to_numpy(dtype=float)

    # Warm-lite: min1 사다리 + fold-제외 통계로 재학습 → 평가행 통계는 잔여 이력
    cgrp.LADDER = LITE_LADDER + base_ladder
    tr_s = cgrp.train_with_internal_stats(tr_rest)
    he_s = cgrp.assign_group_stats(tr_rest, held)
    wlite = cb3.fit_C_ens(tr_s, {"h": he_s})["h"]
    artist_match = (he_s["grp_match_level"] <= len(LITE_LADDER)).to_numpy()
    cgrp.LADDER = base_ladder

    # Cold serving: 동일 잔여 train으로 LGB 재학습, guard는 warm val label-free
    P = {q: np.asarray(cb1.lgb_pipe(feats, a, seed).fit(tr_rest[feats], y)
                       .predict(held[feats]), dtype=float) for q, a in cb1.QUANTILES.items()}
    Pv = {q: np.asarray(cb1.lgb_pipe(feats, a, seed).fit(tr_rest[feats], y)
                        .predict(wval[feats]), dtype=float) for q, a in cb1.QUANTILES.items()}
    guard = cb1.defense(Pv["q50"], Pv["q40"], Pv["q90"] - Pv["q10"])[1]
    cold = cb1.defense(P["q50"], P["q40"], P["q90"] - P["q10"], guard)[0] + UNCOVERED_CONST

    hist_k = held["artist_key"].map(counts - 1).astype(int)
    return pd.DataFrame({
        "seed": seed, "_row": held_idx, "artist_key": held["artist_key"].to_numpy(),
        "history_k": hist_k.to_numpy(), "actual_price": held["price_krw"].to_numpy(dtype=float),
        "wlite_pred_log": wlite, "cold_pred_log": cold, "artist_match": artist_match,
    })


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    feats = artifact_features()["cold_lightgbm"]
    train, wval, _ = load_scope("warm", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw", "artist_key"]))
    train = train[need].reset_index(drop=True)
    wval = wval.reset_index(drop=True)
    base_ladder = list(cgrp.LADDER)

    # ── seed별 체크포인트 (중단 시 재실행으로 이어서 진행)
    parts = []
    for seed in SEEDS:
        ckpt = EXP / "outputs" / f"preds_seed{seed}.csv"
        if ckpt.exists():
            print(f"[resume] seed {seed} 체크포인트 발견 — 건너뜀")
            parts.append(pd.read_csv(ckpt))
            continue
        df = run_seed(seed, train, feats, wval, base_ladder)
        df.to_csv(ckpt, index=False)
        print(f"[done] seed {seed}: {len(df)}행 저장")
        parts.append(df)
    allp = pd.concat(parts, ignore_index=True)

    # ── 집계: k별 성능 + 시뮬 괴리
    rows = []
    for (seed, k), g in allp.groupby(["seed", "history_k"]):
        p = g["actual_price"].to_numpy(dtype=float)
        rows.append({"seed": seed, "k": int(k), "n": len(g),
                     **{f"wlite_{m}": round(v, 4) for m, v in cb1.mt(p, g["wlite_pred_log"].to_numpy()).items()},
                     **{f"cold_{m}": round(v, 4) for m, v in cb1.mt(p, g["cold_pred_log"].to_numpy()).items()},
                     "wcut2_sim_ref_MdAPE": WCUT2_SIM_REF.get(int(k))})
    perk = pd.DataFrame(rows).sort_values(["k", "seed"])
    perk.to_csv(EXP / "outputs" / "per_k_metrics.csv", index=False)

    # ── 게이트: artist-cluster bootstrap (전 seed 통합 행)
    rng = np.random.default_rng(20260612)
    price = allp["actual_price"].to_numpy(dtype=float)
    wl = allp["wlite_pred_log"].to_numpy(dtype=float)
    cd = allp["cold_pred_log"].to_numpy(dtype=float)
    groups = pd.Series(np.arange(len(allp))).groupby(allp["artist_key"].to_numpy()).apply(list)
    wins = {"MdAPE": 0, "MAPE": 0, "p95": 0}
    for _ in range(N_BOOT):
        a = rng.choice(len(groups), size=len(groups), replace=True)
        idx = np.concatenate([groups.iloc[g] for g in a])
        wm, cm = cb1.mt(price[idx], wl[idx]), cb1.mt(price[idx], cd[idx])
        wins["MdAPE"] += wm["MdAPE"] < cm["MdAPE"]
        wins["MAPE"] += wm["MAPE"] < cm["MAPE"]
        wins["p95"] += wm["p95_APE"] < cm["p95_APE"]
    gate = {f"p_{m}": v / N_BOOT for m, v in wins.items()}
    gate["gate_pass"] = all(gate[f"p_{m}"] >= 0.90 for m in ("MdAPE", "MAPE", "p95"))

    overall = {"wlite": cb1.mt(price, wl), "cold_serving": cb1.mt(price, cd),
               "artist_match_rate": float(allp["artist_match"].mean())}
    cfg = {"experiment_id": "PP-WCUT4",
           "eval_design": f"train 이력 {ROWS_MIN}~{ROWS_MAX}건 실존 작가 leave-one-out, hold-out seed {SEEDS}",
           "eval_rows_per_seed": int(len(allp) / len(SEEDS)),
           "train_data_hash": sha_df(train[["artist_key", "ln_price_krw"]]),
           "gate": gate, "overall": {k: ({m: round(x, 4) for m, x in v.items()} if isinstance(v, dict) else v)
                                     for k, v in overall.items()},
           "wcut2_sim_reference": WCUT2_SIM_REF,
           "resume": "outputs/preds_seed*.csv 체크포인트 — 재실행 시 완료 seed 자동 스킵",
           "prohibitions": ["0604 사용 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-WCUT4 실존 저이력 작가 검증\n\n" + json.dumps(cfg["overall"], ensure_ascii=False, indent=1)
        + "\n\n" + json.dumps(gate, ensure_ascii=False) + "\n\n" + perk.to_string(index=False), encoding="utf-8")
    print(json.dumps(cfg["overall"], ensure_ascii=False, indent=1))
    print(json.dumps(gate, ensure_ascii=False))
    print(perk.groupby("k")[["wlite_MdAPE", "cold_MdAPE", "wcut2_sim_ref_MdAPE"]].mean().round(4).to_string())


if __name__ == "__main__":
    main()
