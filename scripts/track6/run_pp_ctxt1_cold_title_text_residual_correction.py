#!/usr/bin/env python3
"""PP-CTXT1: 제목 텍스트 신호의 Cold residual 보정 검증 (Cold 개선 경로 ③).

신규 의존성 없이(TF-IDF char 2~4gram → TruncatedSVD 32) 작품 제목 텍스트가
Cold 연구 base 잔차에 작가 일반화 신호를 갖는지 PP-CIMG1과 동일한 하니스로
검증한다. (MiniLM 임베딩 캐시는 track6 row 매핑 부재로 제외 — TF-IDF는
재료/연작/숫자 등 제목 어휘 신호를 포착한다.)

- vectorizer/SVD는 train-scope 제목으로 동결(라벨/validation 작가 무관)
- residual target = actual_log - research_base_pred_log
- validation artist-grouped 5-fold OOF + 신호 예측력 감사 → 격자(p95 비악화
  + MAPE 개선) → artist 반복 holdout 게이트 → fixed test 1회
- 0604는 Warm 시험 제출 전용 — 사용하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupKFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
SPLIT = REPO / "data" / "track6_split"
EXP = REPO / "experiments" / "track6" / "PP-CTXT1_cold_title_text_residual_correction"

SVD_DIM = 32
CAPS = [0.05, 0.10, 0.20]
STRENGTHS = [0.25, 0.50, 1.00]
N_REPS = 200
HOLDOUT_FRACS = [0.80, 0.70]
SEED = 20260610


def metric_triplet(price, pred_log):
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}


def fit_huber(x, y):
    return HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=2000).fit(x, y)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    df = pd.read_csv(CBASE)
    titles = {}
    for name, split in (("track6_train", None), ("track6_val_cold", "validation"),
                        ("track6_test_cold", "test")):
        t = pd.read_csv(SPLIT / f"{name}.csv", low_memory=False,
                        usecols=["_track6_row_id", "title_raw"])
        titles[name] = t
        if split:
            df = df.merge(t.rename(columns={"title_raw": f"title_{split}"}),
                          on="_track6_row_id", how="left")
    df["title_raw"] = df["title_validation"].fillna(df["title_test"]).fillna("")

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=5, max_features=40000)
    xt_train = vec.fit_transform(titles["track6_train"]["title_raw"].fillna("").astype(str))
    svd = TruncatedSVD(n_components=SVD_DIM, random_state=SEED).fit(xt_train)
    feats = svd.transform(vec.transform(df["title_raw"].astype(str)))
    df["txt_covered"] = df["title_raw"].str.len() > 0
    coverage = {s: float(df.loc[df["split"] == s, "txt_covered"].mean()) for s in ("validation", "test")}

    val_m = (df["split"] == "validation").to_numpy()
    test_m = (df["split"] == "test").to_numpy()
    price = df["actual_price"].to_numpy(dtype=float)
    base_log = df["research_base_pred_log"].to_numpy(dtype=float)
    resid = df["actual_log"].to_numpy(dtype=float) - base_log
    artists = df["artist_key"].astype(str).to_numpy()
    cov = df["txt_covered"].to_numpy()

    vi = np.where(val_m & cov)[0]
    raw_oof = np.zeros(len(df))
    for tr, va in GroupKFold(5).split(vi, groups=artists[vi]):
        raw_oof[vi[va]] = fit_huber(feats[vi[tr]], resid[vi[tr]]).predict(feats[vi[va]])
    audit = {
        "oof_corr_pred_vs_actual_residual": float(np.corrcoef(raw_oof[vi], resid[vi])[0, 1]),
        "corr_std_over_resid_std": float(raw_oof[vi].std() / resid[vi].std()),
    }

    base_val = metric_triplet(price[val_m], base_log[val_m])
    rows = []
    for cap in CAPS:
        for s in STRENGTHS:
            pred = base_log.copy()
            pred[cov] = base_log[cov] + np.clip(s * raw_oof[cov], -cap, cap)
            m = metric_triplet(price[val_m], pred[val_m])
            rows.append({"cap": cap, "strength": s,
                         "val_dMAPE": m["MAPE"] - base_val["MAPE"],
                         "val_dp95": m["p95_APE"] - base_val["p95_APE"],
                         "val_dMdAPE": m["MdAPE"] - base_val["MdAPE"]})
    oof = pd.DataFrame(rows).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dp95"] <= 0) & (oof["val_dMAPE"] < 0)].head(2).to_dict("records")

    gate_rows = []
    val_all = np.where(val_m)[0]
    uniq = np.unique(artists[val_all])
    for c in top:
        rec = {"cap": c["cap"], "strength": c["strength"]}
        ok = True
        for frac in HOLDOUT_FRACS:
            wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
            n = 0
            for _ in range(N_REPS):
                tr_art = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                in_tr = np.isin(artists, list(tr_art))
                tr_rows = vi[in_tr[vi]]
                ho = val_all[~in_tr[val_all]]
                if len(tr_rows) < 100 or len(ho) < 30:
                    continue
                raw = np.zeros(len(df))
                hc = ho[cov[ho]]
                raw[hc] = fit_huber(feats[tr_rows], resid[tr_rows]).predict(feats[hc])
                pred = base_log.copy()
                pred[hc] = base_log[hc] + np.clip(c["strength"] * raw[hc], -c["cap"], c["cap"])
                bm = metric_triplet(price[ho], base_log[ho])
                cm = metric_triplet(price[ho], pred[ho])
                n += 1
                wins["MAPE"] += cm["MAPE"] < bm["MAPE"]
                wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
                wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
            for k in wins:
                rec[f"p_{k}_{frac}"] = wins[k] / max(n, 1)
            ok &= rec[f"p_MAPE_{frac}"] >= 0.90 and rec[f"p_p95_{frac}"] >= 0.90 and rec[f"p_MdAPE_{frac}"] >= 0.50
        rec["gate_pass"] = bool(ok)
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    test_records = [{"candidate": "research_base", **metric_triplet(price[test_m], base_log[test_m])}]
    if top:
        model = fit_huber(feats[vi], resid[vi])
        ti = np.where(test_m & cov)[0]
        raw = np.zeros(len(df))
        raw[ti] = model.predict(feats[ti])
        for c in top:
            pred = base_log.copy()
            pred[ti] = base_log[ti] + np.clip(c["strength"] * raw[ti], -c["cap"], c["cap"])
            test_records.append({"candidate": f"cap{c['cap']}_s{c['strength']}",
                                 **metric_triplet(price[test_m], pred[test_m])})
    test_df = pd.DataFrame(test_records)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    config = {"experiment_id": "PP-CTXT1",
              "purpose": "제목 텍스트(TF-IDF char2-4 + SVD32)의 Cold 잔차 작가 일반화 신호 검증",
              "text_coverage": coverage, "svd_dim": SVD_DIM, "caps": CAPS, "strengths": STRENGTHS,
              "signal_audit_validation_oof": audit, "seed": SEED,
              "note": "MiniLM 캐시는 track6 row 매핑 부재로 제외, 신규 의존성 없는 TF-IDF로 검증",
              "prohibitions": ["0604 사용 금지", "test 후보 선택 금지"]}
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# PP-CTXT1 제목 텍스트 residual 보정", "",
              json.dumps({"coverage": coverage, "signal_audit": audit}, ensure_ascii=False, indent=1), "",
              oof.round(5).to_string(index=False), "",
              gate.round(4).to_string(index=False) if len(gate) else "(OOF 통과 후보 없음)", "",
              test_df.round(4).to_string(index=False)]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print("coverage:", coverage, "| audit:", {k: round(v, 4) for k, v in audit.items()})
    print(oof.head(5).round(5).to_string(index=False))
    print(gate.round(4).to_string(index=False) if len(gate) else "(no gate candidates)")
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
