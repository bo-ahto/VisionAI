#!/usr/bin/env python3
"""PP-MCAL1: 작가 매칭 점수 캘리브레이션 1차 (라우팅 재검증 — 수집 없는 선행판).

질문: 매칭 점수 임계 0.90이 "실제 정확도 ~85%+(PP-WMATCH1 최소선)"를 보장하는가?

설계 (합성 + 실데이터 결합, 신규 라벨링 0):
- 양성 쌍: train 작가명에 변형(공백 삽입/제거, 오탈자 1자, 보조정보 유/무
  시나리오) → 정답 artist_key 매칭, label=1
- 음성 쌍: ① 실제 동명이인(train 정규화 한글명 충돌 117 key — 진짜 hard case)
  ② 유사 이름 타작가(fuzzy 0.85~0.97) ③ 무작위 타작가, label=0
- 점수: 파트너 문서 산식(0.70 이름일치 + 0.20 보조정보 + 0.10 등록
  − 0.15 동명이인위험 − 0.20 핵심충돌, clip 0~0.95; key 직접일치 1.0)
- 산출: 점수 구간별 실제 정확도 곡선 + WMATCH1 비용(MAPE: 정매칭 0.2485 /
  오매칭 2.69 / Cold 0.6746) 결합 기대손실 → 최적 임계 도출
- 체크포인트: outputs/match_pairs.csv 생성 후 재실행 시 재사용
- 한계(명시): 합성 분포 ≠ 실서비스 입력 분포 — 1차 추정, 운영 로그로 보정.
"""
from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-MCAL1_matching_calibration"
SEED = 20260612
N_POS_ARTISTS = 800
COST = {"warm_correct": 0.2485, "warm_mismatch": 2.69, "cold": 0.6746}  # MAPE (PP-WMATCH1/WCUT1)


def fuzzy(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def norm(s: str) -> str:
    return str(s).replace(" ", "").lower().strip()


def perturb(name: str, rng) -> list[tuple[str, str]]:
    out = [("exact", name)]
    if len(name) >= 2:
        i = int(rng.integers(1, len(name)))
        out.append(("space_insert", name[:i] + " " + name[i:]))
        j = int(rng.integers(0, len(name)))
        out.append(("typo_del", name[:j] + name[j + 1:]))
        ch = chr(ord('가') + int(rng.integers(0, 11172)))
        out.append(("typo_sub", name[:j] + ch + name[j + 1:]))
    return out


def score_pair(name_sim: float, aux_match: float, registered: float,
               homonym_risk: float, conflict: float) -> float:
    name_score = 1.0 if name_sim >= 0.999 else (name_sim if name_sim >= 0.85 else 0.0)
    raw = 0.70 * name_score + 0.20 * aux_match + 0.10 * registered \
        - 0.15 * homonym_risk - 0.20 * conflict
    return float(np.clip(raw, 0.0, 0.95))


def build_pairs() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    t = pd.read_csv(REPO / "data/track6_split/track6_train.csv", low_memory=False,
                    usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    d = t.drop_duplicates("artist_key").reset_index(drop=True)
    d["nname"] = d["artist_name_ko"].map(norm)
    name_counts = d["nname"].value_counts()
    d["is_homonym"] = d["nname"].map(name_counts) > 1
    rows = []

    # 양성: 변형 × 보조정보 유/무
    for _, r in d.sample(min(N_POS_ARTISTS, len(d)), random_state=SEED).iterrows():
        homo = 1.0 if r["is_homonym"] else 0.0
        for kind, v in perturb(str(r["artist_name_ko"]), rng):
            sim = fuzzy(norm(v), r["nname"])
            for aux in ([1.0, 0.0] if pd.notna(r["artist_meta_birth_year"]) else [0.0]):
                rows.append({"pair_type": f"pos_{kind}", "label": 1,
                             "score": score_pair(sim, aux, 1.0, homo * (1 - aux), 0.0)})

    # 음성 ①: 실제 동명이인 — 같은 이름, 다른 key
    homon = d[d["is_homonym"]]
    for nm, g in homon.groupby("nname"):
        ks = g.reset_index(drop=True)
        for i in range(len(ks)):
            for j in range(len(ks)):
                if i == j:
                    continue
                by_i, by_j = ks.at[i, "artist_meta_birth_year"], ks.at[j, "artist_meta_birth_year"]
                conflict = 1.0 if (pd.notna(by_i) and pd.notna(by_j) and by_i != by_j) else 0.0
                aux = 0.0
                rows.append({"pair_type": "neg_homonym", "label": 0,
                             "score": score_pair(1.0, aux, 1.0, 1.0, conflict)})

    # 음성 ②: 유사 이름 타작가 (fuzzy 0.85~0.97)
    names = d["nname"].tolist()
    idx = rng.permutation(len(names))[:600]
    for i in idx:
        for j in rng.permutation(len(names))[:40]:
            if i == j or names[i] == names[j]:
                continue
            sim = fuzzy(names[i], names[j])
            if 0.85 <= sim <= 0.97:
                rows.append({"pair_type": "neg_similar", "label": 0,
                             "score": score_pair(sim, 0.0, 1.0, 0.5, 0.0)})
                break

    # 음성 ③: 무작위 타작가
    for _ in range(800):
        i, j = rng.integers(0, len(names), 2)
        if names[i] == names[j]:
            continue
        rows.append({"pair_type": "neg_random", "label": 0,
                     "score": score_pair(fuzzy(names[i], names[j]), 0.0, 1.0, 0.0, 0.0)})
    return pd.DataFrame(rows)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    ckpt = EXP / "outputs" / "match_pairs.csv"
    if ckpt.exists():
        print("[resume] match_pairs.csv 재사용")
        pairs = pd.read_csv(ckpt)
    else:
        pairs = build_pairs()
        pairs.to_csv(ckpt, index=False)

    # 점수 구간별 실제 정확도
    bins = [0, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.88, 0.90, 0.93, 0.951, 1.01]
    pairs["bin"] = pd.cut(pairs["score"], bins, right=False)
    cal = pairs.groupby("bin", observed=True).agg(n=("label", "size"),
                                                  accuracy=("label", "mean")).reset_index()
    cal["bin"] = cal["bin"].astype(str)
    cal.to_csv(EXP / "outputs" / "calibration_curve.csv", index=False)

    # 임계별: 통과 쌍의 정확도 + 기대 MAPE (Warm 라우팅) vs Cold
    th_rows = []
    for th in [0.70, 0.75, 0.80, 0.85, 0.88, 0.90, 0.93, 0.95]:
        sel = pairs[pairs["score"] >= th]
        if len(sel) < 30:
            continue
        acc = float(sel["label"].mean())
        e_warm = acc * COST["warm_correct"] + (1 - acc) * COST["warm_mismatch"]
        th_rows.append({"threshold": th, "n_pass": len(sel), "accuracy_among_pass": round(acc, 4),
                        "expected_MAPE_if_warm": round(e_warm, 4),
                        "warm_beats_cold": bool(e_warm < COST["cold"])})
    th_df = pd.DataFrame(th_rows)
    th_df.to_csv(EXP / "outputs" / "threshold_expected_loss.csv", index=False)

    ok = th_df[th_df["warm_beats_cold"]]
    verdict = {"min_threshold_where_warm_beats_cold": (float(ok["threshold"].min()) if len(ok) else None),
               "accuracy_at_0.90": float(th_df.loc[th_df["threshold"] == 0.90, "accuracy_among_pass"].iloc[0])
               if (th_df["threshold"] == 0.90).any() else None,
               "required_accuracy_floor": 0.85}
    cfg = {"experiment_id": "PP-MCAL1", "seed": SEED, "cost_model": COST,
           "pair_counts": pairs["pair_type"].value_counts().to_dict(),
           "verdict": verdict,
           "limitation": "합성+train 동명이인 기반 1차 캘리브레이션 — 실서비스 입력 분포와 다를 수 있음(운영 로그로 보정)",
           "resume": "outputs/match_pairs.csv 체크포인트"}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-MCAL1 매칭 캘리브레이션\n\n" + cal.to_string(index=False)
        + "\n\n" + th_df.to_string(index=False) + "\n\n" + json.dumps(verdict, ensure_ascii=False), encoding="utf-8")
    print(cal.to_string(index=False))
    print()
    print(th_df.to_string(index=False))
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
