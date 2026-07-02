#!/usr/bin/env python3
"""PP-WCUT1: Warm 라우팅 임계값(이력 5건)의 실증 — 작가 이력 절단 실험.

질문: 작가 train 이력이 1~4건일 때 Warm 경로가 Cold 경로보다 나은가?
(기존 근거는 split 설계·매칭 사다리 구조·5+ 구간 외삽뿐 — 직접 측정 부재)

설계:
- 평가행 = fixed warm test 607행 (작가 200+, 전원 train 이력 5+)
- k ∈ {1,2,3,4,5,8,full}: 각 warm test 작가의 train 행을 무작위 k건만 남김
- Warm proxy = WDOC1 7단 매칭 사다리(작가 L1~L3 min5 + 비작가 L4~L6 + 전체)
  통계 + 선형 Huber 6구성 앙상블 (PP-CBOOST 계열 재사용, 절단 train으로 재학습)
- Cold proxy = v0.2식 LGB Quantile(작가 미사용) rep+guard, 절단 train 재학습.
  서빙 동등 비교를 위해 미커버 상수(-0.0313, v0.4 활성)도 병기
- 산출: k별 Warm vs Cold 성능 곡선 + 작가 레벨 매칭률 → 교차점이 실증 임계값
한계: Warm proxy는 운영 svc_numeric_seed_mean+PPV8 blend가 아닌 선형 기준가
근사 — 절대값이 아니라 k에 따른 상대 비교(방향)가 결론. 0604 미사용.
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
cgrp = importlib.util.module_from_spec(_s); _s.loader.exec_module(_s and cgrp)
_s2 = importlib.util.spec_from_file_location("cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py")
cb1 = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(cb1)
_s3 = importlib.util.spec_from_file_location("cb3", SCRIPT_DIR / "run_pp_cboost3_cold_hetero_blend_gate_retry.py")
cb3 = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(cb3)

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WCUT1_warm_history_truncation"
KS = [1, 2, 3, 4, 5, 8, "full"]
SEED = 20260612
UNCOVERED_CONST = -0.031295
ARTIST_LADDER = [
    (["artist_key", "medium_support_bucket", "size_bucket"], 5),
    (["artist_key", "size_bucket"], 5),
    (["artist_key"], 5),
]


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    feats = artifact_features()["cold_lightgbm"]
    train, wval, wtest = load_scope("warm", feats + ["medium_support_bucket"])
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area",
                                       "price_krw", "artist_key"]))
    train = train[need].reset_index(drop=True)
    wval, wtest = wval.reset_index(drop=True), wtest.reset_index(drop=True)
    price = wtest["price_krw"].to_numpy(dtype=float)
    test_artists = set(wtest["artist_key"].astype(str))

    base_ladder = list(cgrp.LADDER)
    rows = []
    for k in KS:
        # 1) 절단 train
        if k == "full":
            tr_k = train
        else:
            keep_idx = []
            grp = train.groupby(train["artist_key"].astype(str)).indices
            for a, idx in grp.items():
                if a in test_artists and len(idx) > k:
                    keep_idx.append(rng.choice(idx, size=k, replace=False))
                else:
                    keep_idx.append(idx)
            tr_k = train.iloc[np.concatenate(keep_idx)].reset_index(drop=True)
        y = tr_k["ln_price_krw"].to_numpy(dtype=float)

        # 2) Warm proxy: 작가 사다리 포함 통계 + 선형 Huber 앙상블
        cgrp.LADDER = ARTIST_LADDER + base_ladder
        tr_s = cgrp.train_with_internal_stats(tr_k)
        te_s = cgrp.assign_group_stats(tr_k, wtest)
        artist_match = float((te_s["grp_match_level"] <= len(ARTIST_LADDER)).mean())
        warm_pred = cb3.fit_C_ens(tr_s, {"t": te_s})["t"]
        cgrp.LADDER = base_ladder

        # 3) Cold proxy: v0.2식 LGB rep+guard (작가 미사용), guard는 warm val 분포 label-free
        P = {q: np.asarray(cb1.lgb_pipe(feats, a, SEED).fit(tr_k[feats], y).predict(wtest[feats]),
                           dtype=float) for q, a in cb1.QUANTILES.items()}
        Pv = {q: np.asarray(cb1.lgb_pipe(feats, a, SEED).fit(tr_k[feats], y).predict(wval[feats]),
                            dtype=float) for q, a in cb1.QUANTILES.items()}
        guard = cb1.defense(Pv["q50"], Pv["q40"], Pv["q90"] - Pv["q10"])[1]
        cold_def, _ = cb1.defense(P["q50"], P["q40"], P["q90"] - P["q10"], guard)

        for name, pred in (("warm_proxy", warm_pred), ("cold_proxy_defense", cold_def),
                           ("cold_proxy_serving(+const)", cold_def + UNCOVERED_CONST)):
            rows.append({"k": str(k), "candidate": name,
                         "artist_match_rate": round(artist_match, 4) if name == "warm_proxy" else None,
                         **{m: round(v, 4) for m, v in cb1.mt(price, pred).items()}})
        print(f"[k={k}] artist_match={artist_match:.3f} "
              f"warm MdAPE={rows[-3]['MdAPE']} cold(serving) MdAPE={rows[-1]['MdAPE']}")

    out = pd.DataFrame(rows)
    out.to_csv(EXP / "outputs" / "truncation_curve.csv", index=False)
    cfg = {"experiment_id": "PP-WCUT1", "ks": [str(k) for k in KS], "seed": SEED,
           "warm_proxy": "7단 사다리(작가 L1~L3 min5 + 비작가) 통계 + 선형 Huber 6구성",
           "cold_proxy": "v0.2식 LGB Quantile rep+guard (+미커버 상수 서빙 변형)",
           "limitation": "Warm proxy는 운영 svc_numeric+PPV8 blend의 선형 근사 — k별 상대 비교가 결론",
           "prohibitions": ["0604 사용 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text(
        "# PP-WCUT1 Warm 이력 절단 실험\n\n" + out.to_string(index=False), encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
