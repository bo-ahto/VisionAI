#!/usr/bin/env python3
"""PP-E2E1: 라우팅 end-to-end replay (라우팅 재검증 3단계).

입력 작가명 → 매칭(파트너 문서 산식, MCAL1 구현 재사용) → 3-경로 라우팅까지
전체를 실데이터 스트림으로 replay해 오라우팅률과 그 기대 비용을 측정한다.

스트림(정답 라벨 자명):
- Warm행: warm test 607 (사전 내 5+ 작가 → 정답 Warm)
- Warm-lite행: WCUT4 hold-out seed0 649 (사전 내 1~4건 작가 → 정답 Warm-lite)
- Cold행: cold test 3,099 (사전 밖 작가 → 정답 Cold)
시나리오: clean(원형 이름) / dirty(30% 행에 공백·오탈자 변형 + 보조정보 50% 결측)
- 체크포인트: outputs/replay_<scenario>.csv — 재실행 시 스킵. 0604 미사용.
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
THRESH = 0.90
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
        best = cand.iloc[0]
        sim = 1.0
    homo = 1.0 if (len(cand) > 1 or bool(best["is_homonym"])) else 0.0
    if pd.notna(birth) and pd.notna(best["artist_meta_birth_year"]):
        aux, conflict = (1.0, 0.0) if birth == best["artist_meta_birth_year"] else (0.0, 1.0)
    else:
        aux, conflict = 0.0, 0.0
    return mcal.score_pair(sim, aux, 1.0, homo * (1 - aux), conflict), best


def route(score: float, best) -> str:
    if score < THRESH or best is None:
        return "cold"
    return "warm" if int(best["hist_n"]) >= 5 else "warm_lite"


def run_scenario(name: str, stream: pd.DataFrame, dic: pd.DataFrame, dirty: bool) -> pd.DataFrame:
    ckpt = EXP / "outputs" / f"replay_{name}.csv"
    if ckpt.exists():
        print(f"[resume] {name} 체크포인트 — 스킵")
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
        rt = route(sc, best)
        correct_key = (best is not None and str(best["artist_key"]) == str(r["artist_key"]))
        rows.append({"true_route": r["true_route"], "routed": rt, "score": round(sc, 3),
                     "matched_correct_key": bool(correct_key)})
        if len(rows) % 1000 == 0:
            print(f"  {name}: {len(rows)}행")
    out = pd.DataFrame(rows)
    out.to_csv(ckpt, index=False)
    return out


def expected_cost(df: pd.DataFrame) -> float:
    c = 0.0
    for _, r in df.iterrows():
        if r["routed"] == "cold":
            c += COSTS["cold"]
        elif r["matched_correct_key"]:
            c += COSTS["warm"] if r["routed"] == "warm" else COSTS["warm_lite"][3]
        else:
            c += COSTS["mismatch"]
    return c / len(df)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    dic = build_dictionary()

    wt = pd.read_csv(REPO / "data/track6_split/track6_test_warm.csv", low_memory=False,
                     usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    wt = wt.rename(columns={"artist_meta_birth_year": "birth"}).assign(true_route="warm")
    held = pd.read_csv(REPO / "experiments/track6/PP-WCUT4_real_low_history_validation/outputs/preds_seed20260612.csv")
    lm = dic.set_index("artist_key")
    wl = pd.DataFrame({"artist_key": held["artist_key"],
                       "artist_name_ko": held["artist_key"].map(lm["artist_name_ko"]),
                       "birth": held["artist_key"].map(lm["artist_meta_birth_year"]),
                       "true_route": "warm_lite"})
    ct = pd.read_csv(REPO / "data/track6_split/track6_test_cold.csv", low_memory=False,
                     usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    ct = ct.rename(columns={"artist_meta_birth_year": "birth"}).assign(true_route="cold")
    stream = pd.concat([wt, wl, ct], ignore_index=True)

    results = {}
    for scen, dirty in (("clean", False), ("dirty", True)):
        df = run_scenario(scen, stream, dic, dirty)
        conf = df.groupby(["true_route", "routed"]).size().unstack(fill_value=0)
        acc = float((df["true_route"] == df["routed"]).mean())
        # 자격(warm/warm_lite) 행이 cold로 새는 비율 / cold 자격이 상위 경로로 새는 비율
        up = df[df["true_route"].isin(["warm", "warm_lite"])]
        down = df[df["true_route"] == "cold"]
        results[scen] = {
            "routing_accuracy": round(acc, 4),
            "eligible_leak_to_cold": round(float((up["routed"] == "cold").mean()), 4),
            "cold_leak_to_upper": round(float((down["routed"] != "cold").mean()), 4),
            "wrong_key_in_upper_route": round(float((~df[df["routed"] != "cold"]["matched_correct_key"]).mean()), 4),
            "expected_MAPE": round(expected_cost(df), 4),
            "confusion": conf.to_dict(),
        }
        print(scen, json.dumps({k: v for k, v in results[scen].items() if k != "confusion"}, ensure_ascii=False))

    cfg = {"experiment_id": "PP-E2E1", "threshold": THRESH, "costs": COSTS, "seed": SEED,
           "stream": {"warm": len(wt), "warm_lite": len(wl), "cold": len(ct)},
           "results": results,
           "resume": "outputs/replay_<scenario>.csv 체크포인트", "prohibitions": ["0604 사용 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-E2E1 라우팅 end-to-end replay\n\n" + json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
