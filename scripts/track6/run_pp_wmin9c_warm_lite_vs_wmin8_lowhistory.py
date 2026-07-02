#!/usr/bin/env python3
"""PP-WMIN9C: Warm-lite vs WMIN8 svc-core 저이력 직접 비교 (9B 보류 항목 해소 시도).

WMIN9B는 "WMIN8은 5+ 전용 경로라 1~4건 강제 적용은 라우팅 불변식 위반"으로 직접
비교를 보류했다. 본 실험은 그 경계가 자의적이지 않음을 실증한다: WMIN8의 핵심
작가 신호 컴포넌트(min1 svc_numeric, 70% 축)를 PP-WCUT4 실존 저이력 leave-one-out
행에 직접 적용해 Warm-lite와 동일 행에서 비교한다.

정직한 범위:
- WMIN8 full(svc + ppv8 blend + huber refit + router)이 아니라 svc-core(min1
  svc_numeric Huber)만 비교. ppv8/router는 5+ 작가용 상류 컴포넌트라 저이력
  leave-one-out에서 충실 재현 불가(Codex 상류 파이프라인 영역) → svc-core가
  Warm-lite보다 낮으면, ppv8/router를 얹어도 저이력에서 Warm-lite를 넘기 어렵다는
  하한 근거. svc-core가 Warm-lite를 이기면 추가 검증 필요.
- 평가행/seed는 PP-WCUT4와 동일(seed 20260612/13/14, 이력 2~5 작가 1행 hold-out).
  Warm-lite 예측은 WCUT4 preds_seed*.csv에서 동일 행 join.
- 0604 미사용.
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
import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pre_pp_experiments import artifact_features  # noqa: E402
_s1 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s1); _s1.loader.exec_module(cb1)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WMIN9C_warm_lite_vs_wmin8_lowhistory"
WCUT4 = REPO / "experiments" / "track6" / "PP-WCUT4_real_low_history_validation" / "outputs"
SEEDS = [20260612, 20260613, 20260614]
ROWS_MIN, ROWS_MAX = 2, 5


def patch_min1():
    """artist_key 포함 비교군 단계의 min_n을 1로 (WMIN2 규칙)."""
    for gd in svc1.GROUP_DEFS:
        if "artist_key" in gd["keys"]:
            gd["min_n"] = 1


def svc_core_predict(tr_rest: pd.DataFrame, held: pd.DataFrame, features: list[str]) -> np.ndarray:
    # crossfit train comparable stats (자기 fold 제외) + held는 전체 masked-train source
    tr_stats = svc1.crossfit_train_stats(tr_rest)
    tr_full = tr_rest.merge(tr_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    held_stats = svc1.apply_comparable_stats(tr_rest, held)
    held_full = held.merge(held_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    out = svc1.fit_predict("huber", tr_full, held_full, held_full, features)
    return out["validation"]


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    warm_base = artifact_features()["warm"]
    train, _, _ = svc1.load_scope("warm", warm_base)
    train = train.reset_index(drop=True)
    features = svc1.candidate_features(warm_base)["svc_numeric"]
    patch_min1()

    counts = train.groupby("artist_key").size()
    low_artists = counts[(counts >= ROWS_MIN) & (counts <= ROWS_MAX)].index

    parts = []
    for seed in SEEDS:
        ckpt = EXP / "outputs" / f"svccore_seed{seed}.csv"
        wl = pd.read_csv(WCUT4 / f"preds_seed{seed}.csv")  # _row, history_k, actual_price, wlite_pred_log
        if ckpt.exists():
            print(f"[resume] svc-core seed {seed}")
            parts.append(pd.read_csv(ckpt))
            continue
        rng = np.random.default_rng(seed)
        held_idx = []
        for a in low_artists:
            idx = np.where(train["artist_key"].to_numpy() == a)[0]
            held_idx.append(int(rng.choice(idx)))
        held = train.iloc[held_idx].reset_index(drop=True)
        tr_rest = train.drop(index=train.index[held_idx]).reset_index(drop=True)
        svc_pred = svc_core_predict(tr_rest, held, features)
        # WCUT4 행과 동일 순서(_row=held_idx) 보장 → join 검증
        wl_map = dict(zip(wl["_row"], wl["wlite_pred_log"]))
        kmap = dict(zip(wl["_row"], wl["history_k"]))
        df = pd.DataFrame({
            "seed": seed, "_row": held_idx,
            "history_k": [kmap.get(r, np.nan) for r in held_idx],
            "actual_price": held["price_krw"].to_numpy(dtype=float),
            "svccore_pred_log": svc_pred,
            "wlite_pred_log": [wl_map.get(r, np.nan) for r in held_idx],
        })
        df.to_csv(ckpt, index=False)
        parts.append(df)
        print(f"[done] svc-core seed {seed}: {len(df)}행, join 결측 {int(df['wlite_pred_log'].isna().sum())}")

    allp = pd.concat(parts, ignore_index=True).dropna(subset=["wlite_pred_log", "history_k"])
    allp["history_k"] = allp["history_k"].astype(int)
    price = allp["actual_price"].to_numpy(dtype=float)

    rows = []
    for label, col in (("warm_lite", "wlite_pred_log"), ("wmin8_svc_core", "svccore_pred_log")):
        rows.append({"candidate": label, "k": "all", "n": len(allp),
                     **{m: round(v, 4) for m, v in cb1.mt(price, allp[col].to_numpy()).items()}})
        for k, g in allp.groupby("history_k"):
            rows.append({"candidate": label, "k": int(k), "n": len(g),
                         **{m: round(v, 4) for m, v in cb1.mt(g["actual_price"].to_numpy(), g[col].to_numpy()).items()}})
    res = pd.DataFrame(rows).sort_values(["k", "candidate"])
    res.to_csv(EXP / "outputs" / "comparison.csv", index=False)

    wl_all = cb1.mt(price, allp["wlite_pred_log"].to_numpy())
    sc_all = cb1.mt(price, allp["svccore_pred_log"].to_numpy())
    verdict = {
        "warm_lite_overall": {k: round(v, 4) for k, v in wl_all.items()},
        "wmin8_svc_core_overall": {k: round(v, 4) for k, v in sc_all.items()},
        "warm_lite_wins_MdAPE": bool(wl_all["MdAPE"] < sc_all["MdAPE"]),
        "warm_lite_wins_MAPE": bool(wl_all["MAPE"] < sc_all["MAPE"]),
        "warm_lite_wins_p95": bool(wl_all["p95_APE"] < sc_all["p95_APE"]),
        "boundary_confirmed": bool(wl_all["MAPE"] < sc_all["MAPE"] and wl_all["p95_APE"] < sc_all["p95_APE"]),
    }
    cfg = {"experiment_id": "PP-WMIN9C", "seeds": SEEDS, "rows": int(len(allp)),
           "scope": "WMIN8 svc-core(min1 svc_numeric Huber, 70% 축) vs Warm-lite, 동일 LOO 저이력 행",
           "limitation": "ppv8 blend/router 제외(상류 5+ 컴포넌트 LOO 재현 불가) — svc-core는 WMIN8 하한 proxy",
           "verdict": verdict, "prohibitions": ["0604 사용 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-WMIN9C Warm-lite vs WMIN8 svc-core (저이력 직접 비교)\n\n"
        + res.to_string(index=False) + "\n\n" + json.dumps(verdict, ensure_ascii=False, indent=1), encoding="utf-8")
    print(res.to_string(index=False))
    print(json.dumps(verdict, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
