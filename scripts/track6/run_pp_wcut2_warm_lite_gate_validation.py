#!/usr/bin/env python3
"""PP-WCUT2: Warm-lite(이력 1~4건) 경로의 게이트 검증 (PP-WCUT1 후속).

WCUT1의 min1 사다리 결과(이력 1건부터 Cold 압도)를 운영 반영 기준으로 검증:
- 절단 seed 3개 × k ∈ {1,2,3,4}: Warm-lite(min1 사다리 + 선형 Huber 6구성)
  vs Cold serving(LGB+guard+미커버 상수)을 각 조합에서 재학습 비교
- 평가행 = warm test 607 (고정) + warm validation 519 (보조 확인)
- 게이트: 각 (seed,k)에서 warm test artist-cluster bootstrap 400회 —
  Warm-lite의 MdAPE/MAPE 개선확률 >= 0.90 AND p95 개선확률 >= 0.90.
  전 조합 통과 시 pass (k=1은 별도 판정 — tail 차등 정책 근거)
- 0604 미사용. 한계: 5+ 보유 작가의 절단 시뮬레이션(진짜 저이력 작가와
  분포 차이 가능)은 WCUT1과 동일 — 운영 반영 시 모니터링 전제.
"""
from __future__ import annotations

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
EXP = REPO / "experiments" / "track6" / "PP-WCUT2_warm_lite_gate_validation"
KS = [1, 2, 3, 4]
TRUNC_SEEDS = [20260612, 20260613, 20260614]
N_BOOT = 400
UNCOVERED_CONST = -0.031295
LITE_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 1),
    (["artist_key", "size_bucket"], 1),
    (["artist_key"], 1),
]


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    boot_rng = np.random.default_rng(20260612)

    feats = artifact_features()["cold_lightgbm"]
    train, wval, wtest = load_scope("warm", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw", "artist_key"]))
    train = train[need].reset_index(drop=True)
    wval, wtest = wval.reset_index(drop=True), wtest.reset_index(drop=True)
    price_t = wtest["price_krw"].to_numpy(dtype=float)
    price_v = wval["price_krw"].to_numpy(dtype=float)
    test_artists = set(wtest["artist_key"].astype(str))
    groups = pd.Series(np.arange(len(wtest))).groupby(wtest["artist_key"].astype(str).to_numpy()).apply(list)
    base_ladder = list(cgrp.LADDER)

    rows, boot_rows = [], []
    for seed in TRUNC_SEEDS:
        rng = np.random.default_rng(seed)
        for k in KS:
            keep = []
            for a, idx in train.groupby(train["artist_key"].astype(str)).indices.items():
                keep.append(rng.choice(idx, size=k, replace=False)
                            if (a in test_artists and len(idx) > k) else idx)
            tr_k = train.iloc[np.concatenate(keep)].reset_index(drop=True)
            y = tr_k["ln_price_krw"].to_numpy(dtype=float)

            # Warm-lite
            cgrp.LADDER = LITE_LADDER + base_ladder
            tr_s = cgrp.train_with_internal_stats(tr_k)
            te_s = cgrp.assign_group_stats(tr_k, wtest)
            va_s = cgrp.assign_group_stats(tr_k, wval)
            preds = cb3.fit_C_ens(tr_s, {"t": te_s, "v": va_s})
            cgrp.LADDER = base_ladder
            wlite_t, wlite_v = preds["t"], preds["v"]

            # Cold serving
            P = {q: np.asarray(cb1.lgb_pipe(feats, a, seed).fit(tr_k[feats], y)
                               .predict(wtest[feats]), dtype=float) for q, a in cb1.QUANTILES.items()}
            Pv = {q: np.asarray(cb1.lgb_pipe(feats, a, seed).fit(tr_k[feats], y)
                                .predict(wval[feats]), dtype=float) for q, a in cb1.QUANTILES.items()}
            guard = cb1.defense(Pv["q50"], Pv["q40"], Pv["q90"] - Pv["q10"])[1]
            cold_t = cb1.defense(P["q50"], P["q40"], P["q90"] - P["q10"], guard)[0] + UNCOVERED_CONST
            cold_v = cb1.defense(Pv["q50"], Pv["q40"], Pv["q90"] - Pv["q10"], guard)[0] + UNCOVERED_CONST

            for split, pr, wl, pc in (("test", price_t, wlite_t, cold_t),
                                      ("validation", price_v, wlite_v, cold_v)):
                rows.append({"seed": seed, "k": k, "split": split,
                             **{f"wlite_{m}": round(v, 4) for m, v in cb1.mt(pr, wl).items()},
                             **{f"cold_{m}": round(v, 4) for m, v in cb1.mt(pr, pc).items()}})

            wins = {"MdAPE": 0, "MAPE": 0, "p95": 0}
            for _ in range(N_BOOT):
                a = boot_rng.choice(len(groups), size=len(groups), replace=True)
                idx = np.concatenate([groups.iloc[g] for g in a])
                wm, cm = cb1.mt(price_t[idx], wlite_t[idx]), cb1.mt(price_t[idx], cold_t[idx])
                wins["MdAPE"] += wm["MdAPE"] < cm["MdAPE"]
                wins["MAPE"] += wm["MAPE"] < cm["MAPE"]
                wins["p95"] += wm["p95_APE"] < cm["p95_APE"]
            rec = {"seed": seed, "k": k, **{f"p_{m}": v / N_BOOT for m, v in wins.items()}}
            rec["pass"] = all(rec[f"p_{m}"] >= 0.90 for m in ("MdAPE", "MAPE", "p95"))
            boot_rows.append(rec)
            print(f"[seed={seed} k={k}] " + " ".join(f"p_{m}={rec[f'p_{m}']:.3f}" for m in ("MdAPE", "MAPE", "p95")))

    metrics = pd.DataFrame(rows)
    gate = pd.DataFrame(boot_rows)
    metrics.to_csv(EXP / "outputs" / "metrics_by_seed_k.csv", index=False)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    gate_k2plus = bool(gate[gate["k"] >= 2]["pass"].all())
    gate_k1 = bool(gate[gate["k"] == 1]["pass"].all())
    verdict = {"gate_pass_k2_4_all_seeds": gate_k2plus, "gate_pass_k1_all_seeds": gate_k1,
               "min_probs_k2_4": {m: float(gate[gate["k"] >= 2][f"p_{m}"].min())
                                  for m in ("MdAPE", "MAPE", "p95")},
               "min_probs_k1": {m: float(gate[gate["k"] == 1][f"p_{m}"].min())
                                for m in ("MdAPE", "MAPE", "p95")}}
    cfg = {"experiment_id": "PP-WCUT2", "ks": KS, "trunc_seeds": TRUNC_SEEDS,
           "gate": "각 (seed,k) artist-cluster bootstrap 400회 — MdAPE/MAPE/p95 개선확률 전부 >=0.90",
           "verdict": verdict,
           "limitation": "5+ 보유 작가 절단 시뮬레이션(진짜 저이력 작가와 분포 차이 가능), 선형 proxy",
           "prohibitions": ["0604 사용 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-WCUT2 Warm-lite 게이트 검증\n\n" + metrics.to_string(index=False)
        + "\n\n" + gate.round(4).to_string(index=False)
        + "\n\n" + json.dumps(verdict, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(verdict, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
