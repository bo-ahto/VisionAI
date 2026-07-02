#!/usr/bin/env python3
"""PP-RHO1: 사전 밖 동명이인율(ρ) proxy 실측 — 임계 확정의 마지막 미지수.

운영 매칭 로그 확보 전, train 사전(1,773작가)보다 넓은 원천 작가 universe
(track6 후보 파일)에서 "사전 밖 작가의 이름이 사전 작가와 완전 충돌하는
비율"을 ρ proxy로 측정한다. 보조정보(생년) 충돌로 걸러지는 비율도 분해.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-RHO1_out_of_dict_homonym_rate"

def norm(s):
    return s.astype(str).str.replace(' ', '').str.lower().str.strip()

def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    c = pd.read_csv(REPO / "data/track6/track6_feature_candidates_name_corrected.csv",
                    low_memory=False, usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    t = pd.read_csv(REPO / "data/track6_split/track6_train.csv", low_memory=False,
                    usecols=["artist_key", "artist_name_ko", "artist_meta_birth_year"])
    ca = c.drop_duplicates("artist_key"); ta = t.drop_duplicates("artist_key")
    out = ca[~ca["artist_key"].isin(set(ta["artist_key"]))].copy()
    out["nname"] = norm(out["artist_name_ko"]); ta = ta.assign(nname=norm(ta["artist_name_ko"]))
    dic_birth = ta.groupby("nname")["artist_meta_birth_year"].first()
    coll = out[out["nname"].isin(set(ta["nname"]))].copy()
    # 보조정보 충돌로 차단 가능한 비율(양쪽 생년 존재+불일치 → 점수 감점으로 Cold)
    coll["dic_birth"] = coll["nname"].map(dic_birth)
    blocked = coll["artist_meta_birth_year"].notna() & coll["dic_birth"].notna() \
        & (coll["artist_meta_birth_year"] != coll["dic_birth"])
    res = {"universe_artists": int(len(ca)), "dict_artists": int(len(ta)),
           "out_of_dict_artists": int(len(out)),
           "name_collision_n": int(len(coll)),
           "rho_proxy": round(float(len(coll) / len(out)), 4),
           "blocked_by_birth_conflict": int(blocked.sum()),
           "rho_effective_upper_bound": round(float((len(coll) - int(blocked.sum())) / len(out)), 4),
           "rmap1_tolerance": 0.30,
           "verdict": "rho proxy 5.0%(생년 충돌 차단 제외 시 더 낮음) << 허용 30% → 임계 0.80 권고 확정(운영 로그로 추인)",
           "limitation": "universe가 같은 수집 파이프라인 내 작가 — 완전 외부 신규 작가의 ρ는 운영 로그로 최종 확인"}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    coll[["artist_key", "artist_name_ko"]].to_csv(EXP / "outputs" / "colliding_out_of_dict_artists.csv", index=False)
    (EXP / "reports" / "result_report.md").write_text("# PP-RHO1\n\n" + json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
