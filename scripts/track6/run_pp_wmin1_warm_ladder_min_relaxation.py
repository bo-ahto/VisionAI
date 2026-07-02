#!/usr/bin/env python3
"""PP-WMIN1: Warm(이력 5+) 작가 사다리 최소 표본 완화 검증.

배경: warm test 행의 41.2%가 최정밀 비교군(작가+재료/지지체+크기) 1~4건을
보유하나 현행 min5에 걸려 거친 레벨로 fallback. min을 낮추면 정밀 매칭이
살아나는 대신 소표본 중앙값의 분산이 유입 — 정밀도 vs 분산 트레이드오프를
proxy(선형 Huber 6구성 + 사다리 통계)로 검증한다.

- 변형: min5(현행) / min2 / min1 — 작가 레벨 3단의 min_n만 변경
- 선택: warm validation 519행 (test 선택 금지 원칙) + artist-cluster
  bootstrap 400회 vs min5 (MdAPE/MAPE/p95 개선확률 >= 0.90)
- test 607행은 최종 확인 1회. 변형별 체크포인트(중단 시 재실행으로 재개)
- 주의: proxy 결과는 방향 신호 — 운영 svc 파이프라인 반영은 별도 결정
  (Codex Warm 라인 보정 스택 재검증 필요). 0604 미사용.
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
_s3 = importlib.util.spec_from_file_location("cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py")
cb3 = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(cb3)
_s1 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s1); _s1.loader.exec_module(cb1)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WMIN1_warm_ladder_min_relaxation"
VARIANTS = {"min5": 5, "min2": 2, "min1": 1}
N_BOOT = 400


def artist_ladder(min_n: int) -> list:
    return [(["artist_key", "medium_support_bucket", "size_bucket"], min_n),
            (["artist_key", "size_bucket"], min_n),
            (["artist_key"], min_n)]


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260612)

    feats = artifact_features()["cold_lightgbm"]
    train, wval, wtest = load_scope("warm", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw", "artist_key"]))
    train = train[need].reset_index(drop=True)
    wval, wtest = wval.reset_index(drop=True), wtest.reset_index(drop=True)
    base_ladder = list(cgrp.LADDER)

    preds = {}
    for name, mn in VARIANTS.items():
        ckpt = EXP / "outputs" / f"preds_{name}.csv"
        if ckpt.exists():
            print(f"[resume] {name} — 스킵")
            preds[name] = pd.read_csv(ckpt)
            continue
        cgrp.LADDER = artist_ladder(mn) + base_ladder
        tr_s = cgrp.train_with_internal_stats(train)
        va_s = cgrp.assign_group_stats(train, wval)
        te_s = cgrp.assign_group_stats(train, wtest)
        out = cb3.fit_C_ens(tr_s, {"val": va_s, "test": te_s})
        cgrp.LADDER = base_ladder
        df = pd.DataFrame({
            "split": ["validation"] * len(wval) + ["test"] * len(wtest),
            "artist_key": pd.concat([wval["artist_key"], wtest["artist_key"]]).to_numpy(),
            "actual_price": pd.concat([wval["price_krw"], wtest["price_krw"]]).to_numpy(dtype=float),
            "pred_log": np.concatenate([out["val"], out["test"]]),
            "fine_match": np.concatenate([(va_s["grp_match_level"] == 1.0).to_numpy(),
                                          (te_s["grp_match_level"] == 1.0).to_numpy()]),
        })
        df.to_csv(ckpt, index=False)
        preds[name] = df
        print(f"[done] {name}: L1 정밀매칭률 val "
              f"{df[df.split=='validation']['fine_match'].mean():.3f} / test "
              f"{df[df.split=='test']['fine_match'].mean():.3f}")

    # ── validation 비교 + bootstrap 게이트 (vs min5)
    rows, gate_rows = [], []
    base = preds["min5"]
    for name, df in preds.items():
        for split in ("validation", "test"):
            part = df[df["split"] == split]
            m = cb1.mt(part["actual_price"].to_numpy(), part["pred_log"].to_numpy())
            rows.append({"variant": name, "split": split,
                         "fine_match_rate": round(float(part["fine_match"].mean()), 3),
                         **{k: round(v, 4) for k, v in m.items()}})
    metrics = pd.DataFrame(rows)
    metrics.to_csv(EXP / "outputs" / "variant_metrics.csv", index=False)

    bv = base[base["split"] == "validation"].reset_index(drop=True)
    groups = pd.Series(np.arange(len(bv))).groupby(bv["artist_key"].to_numpy()).apply(list)
    for name in ("min2", "min1"):
        cv = preds[name][preds[name]["split"] == "validation"].reset_index(drop=True)
        wins = {"MdAPE": 0, "MAPE": 0, "p95": 0}
        price = bv["actual_price"].to_numpy()
        bp, cp = bv["pred_log"].to_numpy(), cv["pred_log"].to_numpy()
        for _ in range(N_BOOT):
            a = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[g] for g in a])
            bm, cm = cb1.mt(price[idx], bp[idx]), cb1.mt(price[idx], cp[idx])
            wins["MdAPE"] += cm["MdAPE"] < bm["MdAPE"]
            wins["MAPE"] += cm["MAPE"] < bm["MAPE"]
            wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
        rec = {"variant": name, **{f"p_{k}": v / N_BOOT for k, v in wins.items()}}
        rec["gate_pass"] = all(rec[f"p_{k}"] >= 0.90 for k in ("MdAPE", "MAPE", "p95"))
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    cfg = {"experiment_id": "PP-WMIN1",
           "design": "작가 사다리 min_n {5,2,1} proxy 비교 — validation 선택+bootstrap 게이트, test 1회",
           "addressable": "warm test 41.2%가 정밀 그룹 1~4건 보유(min5 폐기)",
           "gate": "artist-cluster bootstrap 400 vs min5, MdAPE/MAPE/p95 >= 0.90",
           "caveat": "proxy 방향 신호 — 운영 svc 반영은 별도 결정(보정 스택 재검증)",
           "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-WMIN1\n\n" + metrics.to_string(index=False) + "\n\n" + gate.round(4).to_string(index=False),
        encoding="utf-8")
    print(metrics.to_string(index=False))
    print(gate.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
