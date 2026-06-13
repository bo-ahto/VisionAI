#!/usr/bin/env python3
"""PP-MONLIVE1: 실서비스 매칭 로그 연동 + R5까지 모니터 실행.

data/track6/service_v0_1/price_prediction_v0_1.sqlite의 운영 테이블을
monitor_warm_lite_routing 스키마로 매핑해 R1~R5를 실행한다.

매핑:
- 라우팅 로그 ← prediction_events (route, artist_match_score,
  same_artist_training_price_count, prediction_price_krw, created_at)
- 라벨 ← sale_price_feedback (actual_sale_price_krw, prediction_id join)
- R5 ← artist_identity_review_decisions(오매칭 결정) / _queue(대기)

정직 표기: 운영 데이터가 아직 적으면(라벨/검수 결정 부족) R4/R5는 측정
불가로 보고하고 proxy를 유지한다. 데이터 조작 없이 현재 상태 그대로 출력.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
_m = importlib.util.spec_from_file_location("mon", SCRIPT_DIR / "monitor_warm_lite_routing.py")
mon = importlib.util.module_from_spec(_m); _m.loader.exec_module(mon)

REPO = Path(__file__).resolve().parents[2]
DB = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
EXP = REPO / "experiments" / "track6" / "PP-MONLIVE1_service_log_monitor"


def main() -> None:
    for sub in ("outputs", "reports", "artifacts"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)

    pe = pd.read_sql_query(
        "SELECT prediction_id, created_at, artist_key, route, artist_match_score, "
        "same_artist_training_price_count, prediction_price_krw FROM prediction_events", c)
    fb = pd.read_sql_query(
        "SELECT prediction_id, actual_sale_price_krw, review_status FROM sale_price_feedback", c)
    # 확정 라벨만 사용 (needs_review 제외)
    fb_ok = fb[fb["review_status"].isin(["confirmed", "approved", "accepted"])]

    df = pd.DataFrame({
        "ts": pe["created_at"],
        "artist_key": pe["artist_key"].fillna("__none__"),
        "match_score": pd.to_numeric(pe["artist_match_score"], errors="coerce").fillna(0.0),
        "history_n": pd.to_numeric(pe["same_artist_training_price_count"], errors="coerce").fillna(0).astype(int),
        "route": pe["route"],
        "pred_price_krw": pd.to_numeric(pe["prediction_price_krw"], errors="coerce"),
    })
    lab = pe[["prediction_id"]].merge(fb_ok, on="prediction_id", how="left")
    df["actual_price_krw"] = pd.to_numeric(lab["actual_sale_price_krw"], errors="coerce").to_numpy()

    # R5: 동명이인 검수 결정에서 오매칭율
    n_dec = c.execute("SELECT COUNT(*) FROM artist_identity_review_decisions").fetchone()[0]
    n_mis = c.execute(
        "SELECT COUNT(*) FROM artist_identity_review_decisions "
        "WHERE decision IN ('split','different_artist','mismatch','reject')").fetchone()[0]
    n_queue = c.execute("SELECT COUNT(*) FROM artist_identity_review_queue").fetchone()[0]
    c.close()
    r5 = mon.r5_homonym_rate(n_dec, n_mis, n_queue)

    df.to_csv(EXP / "outputs" / "service_routing_log.csv", index=False)
    rep = mon.run(df, r5=r5)
    rep["_data_provenance"] = {
        "source": "data/track6/service_v0_1/price_prediction_v0_1.sqlite",
        "prediction_events": int(len(pe)),
        "confirmed_sale_labels": int(len(fb_ok)),
        "raw_sale_feedback": int(len(fb)),
        "identity_review_decisions": int(n_dec),
        "identity_review_queue_pending": int(n_queue),
    }
    (EXP / "artifacts" / "monitor_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-MONLIVE1 실서비스 로그 모니터 (R1~R5)\n\n```json\n"
        + json.dumps(rep, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
