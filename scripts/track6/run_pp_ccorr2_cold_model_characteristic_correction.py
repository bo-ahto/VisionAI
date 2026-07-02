#!/usr/bin/env python3
"""PP-CCORR2: Warm식 모델 특성 보정의 Cold 이식 검증.

Warm에서 성과를 낸 두 메커니즘을 현행 Cold 후보 위에서 검증한다.
(PP-Y11 meta는 구형 후보 pool 대상 보류 — 현행 v0.3 체인 구성요소 대상은 미검증)

A) V2식 meta-stack: 후보 7종 예측 + 합의도(평균/표준편차/범위) + qwidth를
   Huber meta에 투입, 후보 범위 ±0.03 clipping, research base와 가중 블렌드
B) PP148식 제한 라우팅: 위험 구간(qwidth_extreme / y18-v02 gap_extreme)에서만
   research base를 대안 후보(v02_def/y2/guard)로 제한 이동

게이트: validation artist-grouped OOF 선택 → 작가 80%/70% holdout 각 200회
(MAPE/p95 >=0.90, MdAPE >=0.50) → fixed test 1회. 0604 미사용.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupKFold

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
EXP = REPO / "experiments" / "track6" / "PP-CCORR2_cold_model_characteristic_correction"

PREDS = ["y2_pred_log", "y18_qwidth_pred_log", "guard_pred_log", "research_base_pred_log",
         "v02_representative_pred_log", "v02_defense_pred_log"]
META_W = [0.25, 0.50, 1.00]
ROUTE_ALTS = ["v02_defense_pred_log", "y2_pred_log", "guard_pred_log"]
ROUTE_W = [0.25, 0.50]
N_REPS = 200
FRACS = [0.80, 0.70]
SEED = 20260610


def mt(price, pred_log):
    pp = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    a = np.abs(pp - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(a)), "MAPE": float(np.mean(a)),
            "p95_APE": float(np.quantile(a, 0.95))}


def meta_features(df):
    p = df[PREDS].to_numpy(dtype=float)
    return np.column_stack([p, p.mean(1), p.std(1), p.max(1) - p.min(1),
                            df["quantile_width_log"].to_numpy(dtype=float)])


def meta_clip(pred, p):
    return np.clip(pred, p.min(1) - 0.03, p.max(1) + 0.03)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    df = pd.read_csv(CBASE)
    df["gap"] = (df["y18_qwidth_pred_log"] - df["v02_defense_pred_log"]).abs()
    val_m = (df["split"] == "validation").to_numpy()
    test_m = (df["split"] == "test").to_numpy()
    price = df["actual_price"].to_numpy(dtype=float)
    y = df["actual_log"].to_numpy(dtype=float)
    base = df["research_base_pred_log"].to_numpy(dtype=float)
    art = df["artist_key"].astype(str).to_numpy()
    X = meta_features(df)
    P = df[PREDS].to_numpy(dtype=float)
    qw90 = float(df.loc[val_m, "quantile_width_log"].quantile(0.90))
    gap90 = float(df.loc[val_m, "gap"].quantile(0.90))
    masks = {"qwidth_extreme": (df["quantile_width_log"] >= qw90).to_numpy(),
             "gap_extreme": (df["gap"] >= gap90).to_numpy()}

    # A) meta OOF
    vi = np.where(val_m)[0]
    meta_oof = np.zeros(len(df))
    for tr, va in GroupKFold(5).split(vi, groups=art[vi]):
        m = HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=3000).fit(X[vi[tr]], y[vi[tr]])
        meta_oof[vi[va]] = m.predict(X[vi[va]])
    meta_oof = meta_clip(meta_oof, P)
    audit = {"meta_oof_corr_vs_actual": float(np.corrcoef(meta_oof[vi], y[vi])[0, 1]),
             "base_corr_vs_actual": float(np.corrcoef(base[vi], y[vi])[0, 1])}

    bm_val = mt(price[val_m], base[val_m])
    rows = []
    for w in META_W:
        pred = (1 - w) * base + w * meta_oof
        m = mt(price[val_m], pred[val_m])
        rows.append({"kind": "meta", "param": f"w{w}", "mask": "all",
                     "val_dMAPE": m["MAPE"] - bm_val["MAPE"], "val_dp95": m["p95_APE"] - bm_val["p95_APE"],
                     "val_dMdAPE": m["MdAPE"] - bm_val["MdAPE"]})
    # B) routing (학습 없음, 경계만 frozen)
    for mname, mask in masks.items():
        for alt in ROUTE_ALTS:
            for w in ROUTE_W:
                pred = base.copy()
                pred[mask] = (1 - w) * base[mask] + w * df[alt].to_numpy(dtype=float)[mask]
                m = mt(price[val_m], pred[val_m])
                rows.append({"kind": "route", "param": f"{alt.split('_pred')[0]}_w{w}", "mask": mname,
                             "val_dMAPE": m["MAPE"] - bm_val["MAPE"], "val_dp95": m["p95_APE"] - bm_val["p95_APE"],
                             "val_dMdAPE": m["MdAPE"] - bm_val["MdAPE"]})
    oof = pd.DataFrame(rows).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dp95"] <= 0) & (oof["val_dMAPE"] < 0)].head(3).to_dict("records")

    # 게이트
    gate_rows = []
    uniq = np.unique(art[vi])
    for c in top:
        rec = dict(kind=c["kind"], param=c["param"], mask=c["mask"])
        ok = True
        for frac in FRACS:
            wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
            n = 0
            for _ in range(N_REPS):
                tr_a = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                in_tr = np.isin(art, list(tr_a))
                tr_r, ho = vi[in_tr[vi]], vi[~in_tr[vi]]
                if len(ho) < 30:
                    continue
                if c["kind"] == "meta":
                    w = float(c["param"][1:])
                    mm = HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=3000).fit(X[tr_r], y[tr_r])
                    pr = (1 - w) * base[ho] + w * meta_clip(mm.predict(X[ho]), P[ho])
                else:
                    alt, w = c["param"].rsplit("_w", 1)
                    qt = float(df["quantile_width_log"].iloc[tr_r].quantile(0.90))
                    gt = float(df["gap"].iloc[tr_r].quantile(0.90))
                    mk = (df["quantile_width_log"].iloc[ho] >= qt).to_numpy() if c["mask"] == "qwidth_extreme" \
                        else (df["gap"].iloc[ho] >= gt).to_numpy()
                    pr = base[ho].copy()
                    pr[mk] = (1 - float(w)) * base[ho][mk] + float(w) * df[alt + "_pred_log"].to_numpy(dtype=float)[ho][mk]
                bmh = mt(price[ho], base[ho])
                cmh = mt(price[ho], pr)
                n += 1
                wins["MAPE"] += cmh["MAPE"] < bmh["MAPE"]
                wins["p95"] += cmh["p95_APE"] < bmh["p95_APE"]
                wins["MdAPE"] += cmh["MdAPE"] <= bmh["MdAPE"]
            for k in wins:
                rec[f"p_{k}_{frac}"] = wins[k] / max(n, 1)
            ok &= rec[f"p_MAPE_{frac}"] >= 0.90 and rec[f"p_p95_{frac}"] >= 0.90 and rec[f"p_MdAPE_{frac}"] >= 0.50
        rec["gate_pass"] = bool(ok)
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    # fixed test
    test_rows = [{"candidate": "research_base", **mt(price[test_m], base[test_m])}]
    mfull = HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=3000).fit(X[vi], y[vi])
    meta_test = meta_clip(mfull.predict(X), P)
    for c in top:
        if c["kind"] == "meta":
            w = float(c["param"][1:])
            pred = (1 - w) * base + w * meta_test
        else:
            alt, w = c["param"].rsplit("_w", 1)
            pred = base.copy()
            mk = masks[c["mask"]]
            pred[mk] = (1 - float(w)) * base[mk] + float(w) * df[alt + "_pred_log"].to_numpy(dtype=float)[mk]
        test_rows.append({"candidate": f"{c['kind']}_{c['param']}_{c['mask']}", **mt(price[test_m], pred[test_m])})
    test_df = pd.DataFrame(test_rows)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    cfg = {"experiment_id": "PP-CCORR2", "preds": PREDS, "audit": audit,
           "bounds": {"qw90": qw90, "gap90": gap90}, "seed": SEED,
           "note": "PP-Y11(구형 pool meta 보류)과 달리 현행 v0.3 체인 후보 대상",
           "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "result_report.md").write_text("\n".join([
        "# PP-CCORR2 모델 특성 보정 (V2식 meta + PP148식 라우팅)", "",
        json.dumps(audit, ensure_ascii=False), "", oof.round(5).to_string(index=False), "",
        gate.round(4).to_string(index=False) if len(gate) else "(OOF 통과 후보 없음)", "",
        test_df.round(4).to_string(index=False)]), encoding="utf-8")

    print("audit:", {k: round(v, 4) for k, v in audit.items()})
    print(oof.head(8).round(5).to_string(index=False))
    print(gate.round(4).to_string(index=False) if len(gate) else "(no gate candidates)")
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
