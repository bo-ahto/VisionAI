#!/usr/bin/env python3
"""PP-CCORR1: Cold 잔여 보정 직교 결합 (Cold 로드맵 Phase 3).

연구 base(v0.3 guard+search)의 남은 잔차를 두 계열의 보수적 보정으로 검증한다.

1. resid_huber: 정답 미사용 저차원 신호(qwidth, 모델 gap, 검색 delta 크기,
   guard 발동, log_area, mixed_media)로 학습한 Huber residual + cap/strength
2. segment_median: PP-CDIAG1 위험 구간(qwidth bin × gap bin)별 fold-train
   잔차 중앙값 보정 (min_rows 미달 구간은 보정 0)

직교성 감사(PP-COLD-DEFENSE1 방식): 보정값이 기존 guard 이동량/검색 delta와
중복되지 않는지 상관으로 확인하고, 같은 후보를 guard-only base에 적용했을 때의
이득과 비교해 "새 정보인지 기존 층의 재발견인지"를 판별한다.

- 선택: validation artist-grouped 5-fold OOF (p95 비악화 + MAPE 개선)
- 게이트: validation 작가 80%/70% holdout 각 200회, MAPE/p95 >=0.90, MdAPE >=0.50
- fixed test 최종 1회. row-level router 금지(로드맵 §3 Phase 3 제약).
- 0604는 Warm 시험 제출 전용 — 사용하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupKFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
EXP = REPO / "experiments" / "track6" / "PP-CCORR1_cold_residual_orthogonal_correction"

CAPS = [0.05, 0.10, 0.20]
STRENGTHS = [0.25, 0.50, 1.00]
SEG_MIN_ROWS = 40
N_REPS = 200
HOLDOUT_FRACS = [0.80, 0.70]
TOP_K_GATE = 3
SEED = 20260610
SIGNALS = ["quantile_width_log", "model_gap_abs", "search_delta_abs",
           "guard_applied", "log_area", "is_mixed_media"]


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}


def fit_huber(x: np.ndarray, y: np.ndarray) -> HuberRegressor:
    return HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=2000).fit(x, y)


def seg_median_map(seg: np.ndarray, resid: np.ndarray) -> dict[int, float]:
    out = {}
    s = pd.Series(resid).groupby(seg)
    for k, grp in s:
        if len(grp) >= SEG_MIN_ROWS:
            out[int(k)] = float(grp.median())
    return out


def apply_policy(base_log: np.ndarray, raw_corr: np.ndarray, mask: np.ndarray,
                 cap: float, strength: float) -> np.ndarray:
    corr = np.clip(strength * raw_corr, -cap, cap)
    out = base_log.copy()
    out[mask] = base_log[mask] + corr[mask]
    return out


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    df = pd.read_csv(CBASE)
    features = artifact_features()["cold_lightgbm"]
    _, fval, ftest = load_scope("cold", features)
    feat = pd.concat([fval.assign(split="validation"), ftest.assign(split="test")],
                     ignore_index=True)[["split", "_track6_row_id", "medium_category", "log_area"]]
    df = df.merge(feat, on=["split", "_track6_row_id"], how="left", validate="one_to_one")

    df["model_gap_abs"] = (df["y18_qwidth_pred_log"] - df["v02_defense_pred_log"]).abs()
    df["search_delta_abs"] = (df["research_base_pred_log"] - df["guard_pred_log"]).abs()
    df["guard_applied"] = ((df["guard_pred_log"] - df["y18_qwidth_pred_log"]).abs() > 1e-12).astype(float)
    df["is_mixed_media"] = (df["medium_category"] == "mixed_media").astype(float)

    val_m = (df["split"] == "validation").to_numpy()
    test_m = (df["split"] == "test").to_numpy()
    price = df["actual_price"].to_numpy(dtype=float)
    actual_log = df["actual_log"].to_numpy(dtype=float)
    artists = df["artist_key"].astype(str).to_numpy()
    base_log = df["research_base_pred_log"].to_numpy(dtype=float)
    guard_log = df["guard_pred_log"].to_numpy(dtype=float)
    resid = actual_log - base_log

    x = df[SIGNALS].astype(float)
    mu, sd = x[val_m].mean(), x[val_m].std().replace(0, 1.0)
    X = ((x - mu) / sd).to_numpy()

    # validation 분위수 동결 경계
    qw = df["quantile_width_log"]
    qb = [float(qw[val_m].quantile(p)) for p in (0.33, 0.67, 0.90)]
    gap_q50 = float(df.loc[val_m, "model_gap_abs"].quantile(0.50))
    seg = (np.digitize(qw, qb) * 2 + (df["model_gap_abs"] >= gap_q50).astype(int)).to_numpy()
    masks = {
        "all": np.ones(len(df), dtype=bool),
        "qwidth_high_plus": (qw >= qb[1]).to_numpy(),
        "qwidth_extreme": (qw >= qb[2]).to_numpy(),
    }

    # ── validation artist-grouped 5-fold OOF raw corrections
    vi = np.where(val_m)[0]
    gkf = GroupKFold(n_splits=5)
    raw_oof = {"resid_huber": np.zeros(len(df)), "segment_median": np.zeros(len(df))}
    for tr, va in gkf.split(vi, groups=artists[vi]):
        tr_i, va_i = vi[tr], vi[va]
        raw_oof["resid_huber"][va_i] = fit_huber(X[tr_i], resid[tr_i]).predict(X[va_i])
        smap = seg_median_map(seg[tr_i], resid[tr_i])
        raw_oof["segment_median"][va_i] = pd.Series(seg[va_i]).map(smap).fillna(0.0).to_numpy()

    base_val = metric_triplet(price[val_m], base_log[val_m])
    rows = []
    for kind, raw in raw_oof.items():
        kind_masks = masks if kind == "resid_huber" else {"all": masks["all"]}
        for mname, mask in kind_masks.items():
            for cap in CAPS:
                for s in STRENGTHS:
                    pred = apply_policy(base_log, raw, mask, cap, s)
                    m = metric_triplet(price[val_m], pred[val_m])
                    rows.append({"kind": kind, "mask": mname, "cap": cap, "strength": s,
                                 **{f"val_{k}": v for k, v in m.items()},
                                 "val_dMAPE": m["MAPE"] - base_val["MAPE"],
                                 "val_dp95": m["p95_APE"] - base_val["p95_APE"],
                                 "val_dMdAPE": m["MdAPE"] - base_val["MdAPE"]})
    oof = pd.DataFrame(rows).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dp95"] <= 0) & (oof["val_dMAPE"] < 0)].head(TOP_K_GATE).to_dict("records")

    # ── 직교성 감사 (validation OOF 보정값 vs 기존 층)
    guard_shift = guard_log - df["y18_qwidth_pred_log"].to_numpy(dtype=float)
    search_delta = base_log - guard_log
    ortho = {}
    for kind, raw in raw_oof.items():
        c = raw[vi]
        ortho[kind] = {
            "corr_with_guard_shift": float(np.corrcoef(c, guard_shift[vi])[0, 1]),
            "corr_with_search_delta": float(np.corrcoef(c, search_delta[vi])[0, 1]),
            "oof_corr_pred_vs_actual_residual": float(np.corrcoef(c, resid[vi])[0, 1]),
        }

    # ── artist 반복 holdout 게이트 (top 후보)
    gate_rows = []
    uniq = np.unique(artists[vi])
    for c in top:
        rec = {"kind": c["kind"], "mask": c["mask"], "cap": c["cap"], "strength": c["strength"]}
        ok_all = True
        for frac in HOLDOUT_FRACS:
            wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
            n = 0
            for _ in range(N_REPS):
                tr_art = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                in_tr = np.isin(artists, list(tr_art))
                tr_rows = vi[in_tr[vi]]
                ho_rows = vi[~in_tr[vi]]
                if len(tr_rows) < 100 or len(ho_rows) < 30:
                    continue
                raw = np.zeros(len(df))
                if c["kind"] == "resid_huber":
                    raw[ho_rows] = fit_huber(X[tr_rows], resid[tr_rows]).predict(X[ho_rows])
                else:
                    smap = seg_median_map(seg[tr_rows], resid[tr_rows])
                    raw[ho_rows] = pd.Series(seg[ho_rows]).map(smap).fillna(0.0).to_numpy()
                pred = apply_policy(base_log, raw, masks[c["mask"]], c["cap"], c["strength"])
                bm = metric_triplet(price[ho_rows], base_log[ho_rows])
                cm = metric_triplet(price[ho_rows], pred[ho_rows])
                n += 1
                wins["MAPE"] += cm["MAPE"] < bm["MAPE"]
                wins["p95"] += cm["p95_APE"] < bm["p95_APE"]
                wins["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
            for k in wins:
                rec[f"p_{k}_{frac}"] = wins[k] / max(n, 1)
            ok_all &= (rec[f"p_MAPE_{frac}"] >= 0.90 and rec[f"p_p95_{frac}"] >= 0.90
                       and rec[f"p_MdAPE_{frac}"] >= 0.50)
        rec["gate_pass"] = bool(ok_all)
        gate_rows.append(rec)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    # ── fixed test 최종 1회 + guard-only base 직교성 비교
    test_records = []
    huber_full = fit_huber(X[vi], resid[vi])
    smap_full = seg_median_map(seg[vi], resid[vi])
    raw_test = {"resid_huber": np.zeros(len(df)), "segment_median": np.zeros(len(df))}
    ti = np.where(test_m)[0]
    raw_test["resid_huber"][ti] = huber_full.predict(X[ti])
    raw_test["segment_median"][ti] = pd.Series(seg[ti]).map(smap_full).fillna(0.0).to_numpy()
    bm = metric_triplet(price[test_m], base_log[test_m])
    test_records.append({"candidate": "research_base", **bm})
    for c in top:
        pred = apply_policy(base_log, raw_test[c["kind"]], masks[c["mask"]], c["cap"], c["strength"])
        m = metric_triplet(price[test_m], pred[test_m])
        # 같은 보정을 guard-only base에 적용한 이득 (직교성: 검색층 재발견 여부)
        pred_g = apply_policy(guard_log, raw_test[c["kind"]], masks[c["mask"]], c["cap"], c["strength"])
        gm_base = metric_triplet(price[test_m], guard_log[test_m])
        gm = metric_triplet(price[test_m], pred_g[test_m])
        test_records.append({
            "candidate": f"{c['kind']}_{c['mask']}_cap{c['cap']}_s{c['strength']}", **m,
            "gain_MAPE_on_research": bm["MAPE"] - m["MAPE"],
            "gain_MAPE_on_guard_only": gm_base["MAPE"] - gm["MAPE"],
        })
    test_df = pd.DataFrame(test_records)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    config = {
        "experiment_id": "PP-CCORR1",
        "purpose": "연구 base 잔여 보정(저차원 Huber/segment median)의 직교 결합 검증",
        "signals": SIGNALS, "segment": "qwidth bin(4, val q33/q67/q90) x gap bin(2, val q50)",
        "seg_min_rows": SEG_MIN_ROWS, "caps": CAPS, "strengths": STRENGTHS,
        "frozen_bounds": {"qwidth_q33": qb[0], "qwidth_q67": qb[1], "qwidth_q90": qb[2], "gap_q50": gap_q50},
        "orthogonality_audit": ortho,
        "gate": f"artist {HOLDOUT_FRACS} holdout 각 {N_REPS}회, MAPE/p95>=0.90, MdAPE>=0.50",
        "seed": SEED,
        "sources": {"base_rows": str(CBASE.relative_to(REPO))},
        "prohibitions": ["0604 사용 금지", "test 후보 선택 금지", "row-level router 금지(segment까지만)"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# PP-CCORR1 Cold 잔여 보정 직교 결합",
        "",
        "## 직교성 감사 (validation OOF)",
        "",
        json.dumps(ortho, ensure_ascii=False, indent=1),
        "",
        "## validation OOF 상위",
        "",
        oof.head(10).round(5).to_string(index=False),
        "",
        "## artist 반복 holdout 게이트",
        "",
        gate.round(4).to_string(index=False) if len(gate) else "(OOF 통과 후보 없음)",
        "",
        "## fixed test 최종 확인",
        "",
        test_df.round(4).to_string(index=False),
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(json.dumps(ortho, ensure_ascii=False, indent=1))
    print(oof.head(8).round(5).to_string(index=False))
    print()
    print(gate.round(4).to_string(index=False) if len(gate) else "(no gate candidates)")
    print()
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
