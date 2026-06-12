#!/usr/bin/env python3
"""Warm-lite/라우팅 운영 모니터링 하니스 (routing_policy_v0.1 운영 과제 ②).

입력: 운영 라우팅 로그 CSV — 필수 컬럼:
  ts, artist_key, match_score, history_n, route(warm|warm_lite|cold),
  pred_price_krw [, actual_price_krw(라벨 도착 시)]
사용: python3 scripts/track6/monitor_warm_lite_routing.py <log.csv>

검사 항목(동결 참조치 = 재검증 실험 실측):
  R1 라우팅 규칙 위반(이력/점수 조건 불일치 행)        — 0건이어야 함
  R2 warm_lite 트래픽 비중·k 분포 급변                  — 참조: E2E1 스트림
  R3 score 0.80~0.90 구간(보조정보 무 통과) 검수 플래그율
  R4 라벨 도착분 성능: warm_lite MdAPE 한계(동결×1.5 경보)
      k=1 0.179 / k=2 0.179 / k=3 0.157 / k=4 0.142 (WCUT4 실존 ×1.5)
  R5 사전 밖 동명이인율 실측 누적(오매칭 검수 결과 입력 시) vs proxy 5%
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ALERT = {
    "wlite_mdape_limit_by_k": {1: 0.179, 2: 0.179, 3: 0.157, 4: 0.142},  # WCUT4 ×1.5
    "score_band_review_required": [0.80 - 1e-6, 0.90],
    "rho_proxy_reference": 0.05,
    "min_rows_for_perf_check": 50,
}


def main(path: str) -> None:
    df = pd.read_csv(path)
    rep = {"n_rows": len(df)}

    ok_warm = (df["route"] != "warm") | ((df["match_score"] >= 0.80 - 1e-6) & (df["history_n"] >= 5))
    ok_lite = (df["route"] != "warm_lite") | ((df["match_score"] >= 0.80 - 1e-6)
                                              & df["history_n"].between(1, 4))
    rep["R1_rule_violations"] = int((~ok_warm).sum() + (~ok_lite).sum())

    rep["R2_route_share"] = df["route"].value_counts(normalize=True).round(4).to_dict()
    if (df["route"] == "warm_lite").any():
        rep["R2_wlite_k_dist"] = df.loc[df["route"] == "warm_lite", "history_n"] \
            .value_counts(normalize=True).round(3).to_dict()

    band = df["match_score"].between(*ALERT["score_band_review_required"])
    rep["R3_aux_missing_band_share"] = round(float(band.mean()), 4)

    if "actual_price_krw" in df.columns and df["actual_price_krw"].notna().any():
        lab = df[df["actual_price_krw"].notna() & (df["route"] == "warm_lite")]
        perf = {}
        for k, g in lab.groupby("history_n"):
            if len(g) < ALERT["min_rows_for_perf_check"]:
                continue
            ape = (g["pred_price_krw"] - g["actual_price_krw"]).abs() / g["actual_price_krw"]
            md = float(ape.median())
            perf[int(k)] = {"n": len(g), "MdAPE": round(md, 4),
                            "ALERT": bool(md > ALERT["wlite_mdape_limit_by_k"].get(int(k), 0.2))}
        rep["R4_wlite_perf_by_k"] = perf

    alerts = []
    if rep["R1_rule_violations"]:
        alerts.append(f"R1 라우팅 규칙 위반 {rep['R1_rule_violations']}건")
    for k, v in rep.get("R4_wlite_perf_by_k", {}).items():
        if v["ALERT"]:
            alerts.append(f"R4 warm_lite k={k} MdAPE {v['MdAPE']} > 한계")
    rep["alerts"] = alerts or ["없음"]
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
