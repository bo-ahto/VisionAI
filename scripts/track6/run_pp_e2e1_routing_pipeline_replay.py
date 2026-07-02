#!/usr/bin/env python3
"""PP-E2E1 v2: 라우팅 end-to-end replay (codex 리뷰 P1 수정판).

수정 사항(2026-06-12 codex review):
- P1 누수: warm-lite 스트림(WCUT4 hold-out) 행은 사전 hist_n에서 held 1건을
  차감해 서빙 시점 이력으로 라우팅 (이전: full train 카운트 → 5건 작가 오라우팅)
- P1 임계: THRESH 파라미터화 + tolerance(1e-6), 0.80/0.90 양쪽을 in-repo로 스윕
- P1 동명이인: 완전일치 후보 중 생년 일치 후보 우선 선택
- P2 비용: warm-lite 정매칭 비용을 행별 실제 이력 k로 청구
스트림: warm test 607(정답 Warm) + WCUT4 hold-out seed0 649(정답 Warm-lite)
+ cold test 3,099(정답 Cold). 시나리오 clean/dirty × 임계 0.80/0.90,
체크포인트 단위 재개. 0604 미사용.
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
_m = importlib.util.spec_from_file_location("mcal", SCRIPT_DIR / "run_pp_mcal1_matching_calibration.py")
mcal = importlib.util.module_from_spec(_m); _m.loader.exec_module(mcal)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-E2E1_routing_pipeline_replay"
SEED = 20260612
TOL = 1e-6
THRESHOLDS = [0.80, 0.90]
COSTS = {"warm": 0.2699, "warm_lite": {1: 0.3415, 2: 0.2707, 3: 0.2541, 4: 0.2557},
         "cold": 0.9946, "mismatch": 2.69}


def build_dictionary() -> pd.DataFrame:
    t = pd.read_csv(REPO / "data/track6_split/track6_train.csv", low_memory=False,
                    usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    d = t.drop_duplicates("artist_key").reset_index(drop=True)
    d["nname"] = d["artist_name_ko"].map(mcal.norm)
    d["hist_n"] = d["artist_key"].map(t.groupby("artist_key").size())
    nc = d["nname"].value_counts()
    d["is_homonym"] = d["nname"].map(nc) > 1
    return d


def match(name: str, birth, dic: pd.DataFrame) -> tuple[float, object]:
    nn = mcal.norm(name)
    cand = dic[dic["nname"] == nn]
    if len(cand) == 0:
        sims = dic["nname"].map(lambda x: mcal.fuzzy(nn, x))
        if sims.max() < 0.85:
            return 0.0, None
        cand = dic[sims >= 0.85]
        best = cand.loc[sims[cand.index].idxmax()]
        sim = float(sims[cand.index].max())
    else:
        # P1 수정: 동명이인 완전일치 — 생년 일치 후보 우선
        best = cand.iloc[0]
        if pd.notna(birth):
            bm = cand[cand["artist_meta_birth_year"] == birth]
            if len(bm):
                best = bm.iloc[0]
        sim = 1.0
    homo = 1.0 if (len(cand) > 1 or bool(best["is_homonym"])) else 0.0
    if pd.notna(birth) and pd.notna(best["artist_meta_birth_year"]):
        aux, conflict = (1.0, 0.0) if birth == best["artist_meta_birth_year"] else (0.0, 1.0)
    else:
        aux, conflict = 0.0, 0.0
    # 생년 일치로 동명이인이 해소된 경우 위험 감점 면제 (aux=1이면 homo*(1-aux)=0)
    return mcal.score_pair(sim, aux, 1.0, homo * (1 - aux), conflict), best


def route(score: float, best, held_adjust: int, thresh: float) -> tuple[str, int]:
    if best is None or score < thresh - TOL:
        return "cold", 0
    hist_eff = int(best["hist_n"]) - int(held_adjust)  # P1 수정: 서빙 시점 이력
    return ("warm", hist_eff) if hist_eff >= 5 else ("warm_lite", hist_eff)


def run_scenario(name: str, stream: pd.DataFrame, dic: pd.DataFrame,
                 dirty: bool, thresh: float) -> pd.DataFrame:
    ckpt = EXP / "outputs" / f"replay_v2_{name}_th{int(round(thresh * 100))}.csv"
    if ckpt.exists():
        print(f"[resume] {ckpt.name} — 스킵")
        return pd.read_csv(ckpt)
    rng = np.random.default_rng(SEED)
    rows = []
    for _, r in stream.iterrows():
        nm, birth = str(r["artist_name_ko"]), r.get("birth")
        if dirty and rng.random() < 0.30:
            nm = mcal.perturb(nm, rng)[int(rng.integers(1, 4))][1] if len(nm) >= 2 else nm
            if rng.random() < 0.5:
                birth = np.nan
        sc, best = match(nm, birth, dic)
        rt, k_eff = route(sc, best, int(r["held_adjust"]), thresh)
        correct = (best is not None and str(best["artist_key"]) == str(r["artist_key"]))
        rows.append({"true_route": r["true_route"], "routed": rt, "score": round(sc, 3),
                     "k_eff": k_eff, "matched_correct_key": bool(correct)})
    out = pd.DataFrame(rows)
    out.to_csv(ckpt, index=False)
    print(f"[done] {ckpt.name}")
    return out


def expected_cost(df: pd.DataFrame) -> float:
    c = np.where(df["routed"] == "cold", COSTS["cold"],
                 np.where(~df["matched_correct_key"], COSTS["mismatch"],
                          np.where(df["routed"] == "warm", COSTS["warm"],
                                   df["k_eff"].clip(1, 4).map(COSTS["warm_lite"]))))
    return float(np.mean(c.astype(float)))


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    dic = build_dictionary()

    wt = pd.read_csv(REPO / "data/track6_split/track6_test_warm.csv", low_memory=False,
                     usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    wt = wt.rename(columns={"artist_meta_birth_year": "birth"}).assign(
        true_route="warm", held_adjust=0)
    held = pd.read_csv(REPO / "experiments/track6/PP-WCUT4_real_low_history_validation/outputs/preds_seed20260612.csv")
    lm = dic.set_index("artist_key")
    wl = pd.DataFrame({"artist_key": held["artist_key"],
                       "artist_name_ko": held["artist_key"].map(lm["artist_name_ko"]),
                       "birth": held["artist_key"].map(lm["artist_meta_birth_year"]),
                       "true_route": "warm_lite", "held_adjust": 1})
    ct = pd.read_csv(REPO / "data/track6_split/track6_test_cold.csv", low_memory=False,
                     usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    ct = ct.rename(columns={"artist_meta_birth_year": "birth"}).assign(
        true_route="cold", held_adjust=0)
    stream = pd.concat([wt, wl, ct], ignore_index=True)

    results = {}
    for th in THRESHOLDS:
        for scen, dirty in (("clean", False), ("dirty", True)):
            df = run_scenario(scen, stream, dic, dirty, th)
            up = df[df["true_route"].isin(["warm", "warm_lite"])]
            down = df[df["true_route"] == "cold"]
            upper = df[df["routed"] != "cold"]
            results[f"{scen}_th{th}"] = {
                "routing_accuracy": round(float((df["true_route"] == df["routed"]).mean()), 4),
                "eligible_leak_to_cold": round(float((up["routed"] == "cold").mean()), 4),
                "cold_leak_to_upper": round(float((down["routed"] != "cold").mean()), 4),
                "wrong_key_in_upper_route": round(float((~upper["matched_correct_key"]).mean()), 4)
                if len(upper) else 0.0,
                "expected_MAPE": round(expected_cost(df), 4),
            }
            print(f"{scen}_th{th}", json.dumps(results[f"{scen}_th{th}"], ensure_ascii=False))

    cfg = {"experiment_id": "PP-E2E1", "version": "v2 (codex P1 수정)",
           "thresholds": THRESHOLDS, "tolerance": TOL, "costs": COSTS, "seed": SEED,
           "fixes": ["held_adjust로 LOO 이력 누수 제거", "임계 파라미터화+tolerance(0.80/0.90 in-repo 스윕)",
                     "동명이인 생년 우선 선택", "warm-lite 비용 행별 k 청구"],
           "stream": {"warm": len(wt), "warm_lite": len(wl), "cold": len(ct)},
           "results": results, "prohibitions": ["0604 사용 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-E2E1 v2 라우팅 replay (codex P1 수정판)\n\n" + json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
