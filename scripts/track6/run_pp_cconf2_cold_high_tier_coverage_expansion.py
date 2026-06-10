#!/usr/bin/env python3
"""PP-CCONF2: high tier 커버리지 확대 (Cold 개선 경로 ④).

점 예측 평균이 아니라 "신뢰 가능 구간의 비율"을 올린다. v0.4 동결 tier의
high(test 8.2%, p95 0.99)를 더 완화한 경계로 확장할 수 있는지 검증.

- 격자: qwidth percentile {0.33,0.40,0.50,0.60} × gap percentile {0.50,0.60,0.70,0.80}
- 선택(validation): high-tier p95 <= 1.0 제약 하에 share 최대
- 안정성: artist 반복 holdout 200회×{0.8,0.7} — 경계를 holdout-train 작가로
  재산정하고 holdout 작가에서 P(high p95 <= 1.5) >= 0.90 요구
- fixed test 1회 확인. 0604 미사용.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
EXP = REPO / "experiments" / "track6" / "PP-CCONF2_cold_high_tier_coverage_expansion"

QW_PCTS = [0.33, 0.40, 0.50, 0.60]
GAP_PCTS = [0.50, 0.60, 0.70, 0.80]
P95_CONSTRAINT_VAL = 1.0
P95_HOLDOUT_LIMIT = 1.5
N_REPS = 200
HOLDOUT_FRACS = [0.80, 0.70]
SEED = 20260610


def ape(price, pred_log):
    return np.abs(np.clip(np.exp(pred_log), 1_000.0, None) - price) / np.clip(price, 1.0, None)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    df = pd.read_csv(CBASE)
    df["gap"] = (df["y18_qwidth_pred_log"] - df["v02_defense_pred_log"]).abs()
    df["ape"] = ape(df["actual_price"].to_numpy(dtype=float),
                    df["research_base_pred_log"].to_numpy(dtype=float))
    val = df[df["split"] == "validation"].reset_index(drop=True)
    test = df[df["split"] == "test"].reset_index(drop=True)
    qw90 = float(val["quantile_width_log"].quantile(0.90))
    gap90 = float(val["gap"].quantile(0.90))

    def high_mask(part, qw_thr, gap_thr):
        low = (part["quantile_width_log"] >= qw90) | (part["gap"] >= gap90)
        return ((part["quantile_width_log"] <= qw_thr) & (part["gap"] <= gap_thr)
                & part["search_covered"].astype(bool) & ~low)

    rows = []
    for qp in QW_PCTS:
        for gp in GAP_PCTS:
            qt, gt = float(val["quantile_width_log"].quantile(qp)), float(val["gap"].quantile(gp))
            hm = high_mask(val, qt, gt)
            a = val.loc[hm, "ape"]
            rows.append({"qw_pct": qp, "gap_pct": gp, "qw_thr": qt, "gap_thr": gt,
                         "val_share": float(hm.mean()), "val_n": int(hm.sum()),
                         "val_MdAPE": float(a.median()), "val_p95": float(a.quantile(0.95))})
    grid = pd.DataFrame(rows)
    grid.to_csv(EXP / "outputs" / "grid_validation.csv", index=False)
    feasible = grid[grid["val_p95"] <= P95_CONSTRAINT_VAL].sort_values("val_share", ascending=False)
    top = feasible.head(3).to_dict("records")

    # 안정성: holdout-train 작가 경계 재산정 → holdout 작가 high tier p95/share
    gate_rows = []
    artists = val["artist_key"].astype(str).to_numpy()
    uniq = np.unique(artists)
    for c in top:
        rec = {"qw_pct": c["qw_pct"], "gap_pct": c["gap_pct"]}
        ok = True
        for frac in HOLDOUT_FRACS:
            p95s, shares = [], []
            for _ in range(N_REPS):
                tr_art = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                in_tr = np.isin(artists, list(tr_art))
                tr, ho = val[in_tr], val[~in_tr]
                if len(ho) < 30:
                    continue
                qt = float(tr["quantile_width_log"].quantile(c["qw_pct"]))
                gt = float(tr["gap"].quantile(c["gap_pct"]))
                hm = high_mask(ho, qt, gt)
                if hm.sum() < 5:
                    continue
                p95s.append(float(ho.loc[hm, "ape"].quantile(0.95)))
                shares.append(float(hm.mean()))
            rec[f"p_p95_le_{P95_HOLDOUT_LIMIT}_{frac}"] = float(np.mean(np.array(p95s) <= P95_HOLDOUT_LIMIT))
            rec[f"share_mean_{frac}"] = float(np.mean(shares))
            ok &= rec[f"p_p95_le_{P95_HOLDOUT_LIMIT}_{frac}"] >= 0.90
        rec["gate_pass"] = bool(ok)
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    # fixed test 1회 (v0.4 동결 tier와 비교)
    test_rows = []
    ref_hm = high_mask(test, float(val["quantile_width_log"].quantile(0.33)),
                       float(val["gap"].quantile(0.50)))
    a = test.loc[ref_hm, "ape"]
    test_rows.append({"candidate": "v0.4_frozen(q33,g50)", "test_share": float(ref_hm.mean()),
                      "test_MdAPE": float(a.median()), "test_p95": float(a.quantile(0.95))})
    for c in top:
        hm = high_mask(test, c["qw_thr"], c["gap_thr"])
        a = test.loc[hm, "ape"]
        test_rows.append({"candidate": f"q{c['qw_pct']}_g{c['gap_pct']}",
                          "test_share": float(hm.mean()),
                          "test_MdAPE": float(a.median()), "test_p95": float(a.quantile(0.95))})
    test_df = pd.DataFrame(test_rows)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    config = {"experiment_id": "PP-CCONF2",
              "purpose": "high tier 커버리지 확대 (p95 품질 유지 제약)",
              "grid": {"qw_pcts": QW_PCTS, "gap_pcts": GAP_PCTS},
              "constraints": {"val_high_p95": P95_CONSTRAINT_VAL,
                              "holdout": f"P(p95<={P95_HOLDOUT_LIMIT})>=0.90"},
              "seed": SEED, "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# PP-CCONF2 high tier 커버리지 확대", "",
              grid.round(4).to_string(index=False), "",
              gate.round(4).to_string(index=False) if len(gate) else "(feasible 후보 없음)", "",
              test_df.round(4).to_string(index=False)]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(feasible.head(5).round(4).to_string(index=False))
    print()
    print(gate.round(4).to_string(index=False) if len(gate) else "(no feasible)")
    print()
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
