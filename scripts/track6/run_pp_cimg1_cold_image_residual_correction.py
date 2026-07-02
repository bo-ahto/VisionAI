#!/usr/bin/env python3
"""PP-CIMG1: Cold 이미지 임베딩 residual 보정 (Cold 로드맵 Phase 2-2).

IMG-P4 결론(이미지는 기본 예측 대체가 아니라 고위험 구간 한정 보정 후보)과
PP-CDIAG1 위험 구간(qwidth_extreme, 저행수 작가)/PP-CCONF1 low tier를 결합해,
CLIP ViT-B/32 임베딩 PCA 기반 저차원 residual 보정을 구간 한정으로 검증한다.

- residual target = actual_log - base_pred_log (연구/운영 base 각각)
- 보정 모델: train-scope 임베딩으로 PCA(512→32) 동결 → validation에서
  artist-grouped 5-fold OOF Huber residual
- 적용 정책 = (마스크, cap, strength) 격자. 미커버(이미지 없음) 행은 보정 0
- 후보 선택: validation OOF (p95 비악화 + MAPE 개선)
- 채택 게이트: PP-CBASE1 기준 — validation 작가 80%/70% holdout 각 200회,
  base 대비 MAPE/p95 개선확률 >=0.90, MdAPE >=0.50. fixed test는 최종 1회.
- 0604는 Warm 시험 제출 전용 — 사용하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import GroupKFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
CCONF_TIERS = REPO / "experiments" / "track6" / "PP-CCONF1_cold_confidence_tier_policy" / "outputs" / "tier_assignments.csv"
IMG_DIR = REPO / "data" / "track6" / "image_multimodal"
EMB_PATH = IMG_DIR / "track6_clip_cold_full_saatchi_artsy_embeddings.npy"
IDX_PATH = IMG_DIR / "track6_clip_cold_full_saatchi_artsy_index.csv"
EXP = REPO / "experiments" / "track6" / "PP-CIMG1_cold_image_residual_correction"

BASES = {"research": "research_base_pred_log", "operational": "v02_defense_pred_log"}
QWIDTH_COL = {"research": "quantile_width_log", "operational": "v02_qwidth_log"}
PCA_DIM = 32
CAPS = [0.05, 0.10, 0.20]
STRENGTHS = [0.25, 0.50, 1.00]
N_REPS = 200
HOLDOUT_FRACS = [0.80, 0.70]
TOP_K_GATE = 2
SEED = 20260610
SPLIT_MAP = {"val_cold": "validation", "test_cold": "test"}


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}


def fit_huber(x: np.ndarray, y: np.ndarray) -> HuberRegressor:
    return HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=2000).fit(x, y)


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
    tiers = pd.read_csv(CCONF_TIERS)[["split", "_track6_row_id", "tier_research"]]
    df = df.merge(tiers, on=["split", "_track6_row_id"], how="left", validate="one_to_one")

    idx = pd.read_csv(IDX_PATH, low_memory=False)
    emb = np.load(EMB_PATH)
    idx["embedding_pos"] = np.arange(len(idx))
    idx["split"] = idx["split"].map(SPLIT_MAP).fillna(idx["split"])
    idx = idx.drop_duplicates(subset=["_track6_row_id"], keep="first")

    # PCA는 train-scope 임베딩으로 동결 (라벨 미사용, validation 작가와 무관)
    train_pos = idx.loc[idx["split"] == "train", "embedding_pos"].to_numpy()
    pca = PCA(n_components=PCA_DIM, random_state=SEED).fit(emb[train_pos])

    df = df.merge(idx[["split", "_track6_row_id", "embedding_pos"]],
                  on=["split", "_track6_row_id"], how="left", validate="one_to_one")
    df["img_covered"] = df["embedding_pos"].notna()
    feats = np.zeros((len(df), PCA_DIM), dtype=float)
    cov = df["img_covered"].to_numpy()
    feats[cov] = pca.transform(emb[df.loc[cov, "embedding_pos"].astype(int).to_numpy()])

    val_m = (df["split"] == "validation").to_numpy()
    test_m = (df["split"] == "test").to_numpy()
    coverage = {s: float(df.loc[df["split"] == s, "img_covered"].mean()) for s in ("validation", "test")}

    # 마스크 정의 (validation 분위수 동결)
    masks: dict[str, dict[str, np.ndarray]] = {}
    bounds: dict[str, float] = {}
    for tgt in BASES:
        qcol = QWIDTH_COL[tgt]
        q67 = float(df.loc[val_m, qcol].quantile(0.67))
        q90 = float(df.loc[val_m, qcol].quantile(0.90))
        bounds[f"{tgt}_qwidth_q67"], bounds[f"{tgt}_qwidth_q90"] = q67, q90
        m = {
            "all": np.ones(len(df), dtype=bool),
            "qwidth_extreme": (df[qcol] >= q90).to_numpy(),
            "qwidth_high_plus": (df[qcol] >= q67).to_numpy(),
        }
        if tgt == "research":
            m["low_tier"] = (df["tier_research"] == "low").to_numpy()
            m["low_tier_or_qwx"] = m["low_tier"] | m["qwidth_extreme"]
        masks[tgt] = {k: v & cov for k, v in m.items()}  # 미커버 행은 보정 0

    price = df["actual_price"].to_numpy(dtype=float)
    actual_log = df["actual_log"].to_numpy(dtype=float)
    artists = df["artist_key"].astype(str).to_numpy()

    # ── validation artist-grouped 5-fold OOF raw correction (target별 1회)
    raw_corr_oof: dict[str, np.ndarray] = {}
    for tgt, col in BASES.items():
        resid = actual_log - df[col].to_numpy(dtype=float)
        corr = np.zeros(len(df), dtype=float)
        vi = np.where(val_m & cov)[0]
        gkf = GroupKFold(n_splits=5)
        for tr, va in gkf.split(vi, groups=artists[vi]):
            model = fit_huber(feats[vi[tr]], resid[vi[tr]])
            corr[vi[va]] = model.predict(feats[vi[va]])
        raw_corr_oof[tgt] = corr

    # 신호 자체의 예측력 감사: OOF 보정값 vs 실제 잔차 상관 (작가 경계 일반화 검증)
    signal_audit = {}
    vi_all = np.where(val_m & cov)[0]
    for tgt, col in BASES.items():
        resid = actual_log - df[col].to_numpy(dtype=float)
        c = raw_corr_oof[tgt][vi_all]
        signal_audit[tgt] = {
            "oof_corr_pred_vs_actual_residual": float(np.corrcoef(c, resid[vi_all])[0, 1]),
            "corr_std_over_resid_std": float(c.std() / resid[vi_all].std()),
        }

    # ── OOF 후보 격자 평가 (validation)
    rows = []
    for tgt, col in BASES.items():
        base_log = df[col].to_numpy(dtype=float)
        base_val = metric_triplet(price[val_m], base_log[val_m])
        for mname, mask in masks[tgt].items():
            for cap in CAPS:
                for s in STRENGTHS:
                    pred = apply_policy(base_log, raw_corr_oof[tgt], mask, cap, s)
                    m = metric_triplet(price[val_m], pred[val_m])
                    rows.append({
                        "target": tgt, "mask": mname, "cap": cap, "strength": s,
                        "applied_share_val": float(mask[val_m].mean()),
                        **{f"val_{k}": v for k, v in m.items()},
                        "val_dMAPE": m["MAPE"] - base_val["MAPE"],
                        "val_dp95": m["p95_APE"] - base_val["p95_APE"],
                        "val_dMdAPE": m["MdAPE"] - base_val["MdAPE"],
                    })
    oof = pd.DataFrame(rows)
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)

    # 후보 선택: p95 비악화 + MAPE 개선, MAPE 개선폭 순
    top = {}
    for tgt in BASES:
        sel = oof[(oof["target"] == tgt) & (oof["val_dp95"] <= 0) & (oof["val_dMAPE"] < 0)]
        top[tgt] = sel.nsmallest(TOP_K_GATE, "val_dMAPE").to_dict("records")

    # ── artist 반복 holdout 게이트 (top 후보만)
    gate_rows = []
    val_idx = np.where(val_m & cov)[0]
    val_all_idx = np.where(val_m)[0]
    uniq_artists = np.unique(artists[val_all_idx])
    for tgt, col in BASES.items():
        if not top[tgt]:
            continue
        base_log = df[col].to_numpy(dtype=float)
        resid = actual_log - base_log
        stats = {id(c): {"MAPE": 0, "p95": 0, "MdAPE": 0, "n": 0} for c in top[tgt]}
        for frac in HOLDOUT_FRACS:
            for c in top[tgt]:
                stats[id(c)][f"frac{frac}"] = {"MAPE": 0, "p95": 0, "MdAPE": 0, "n": 0}
            for _ in range(N_REPS):
                tr_artists = set(rng.choice(uniq_artists, size=int(len(uniq_artists) * frac), replace=False))
                in_tr = np.isin(artists, list(tr_artists))
                tr_rows = val_idx[in_tr[val_idx]]
                ho_rows = val_all_idx[~in_tr[val_all_idx]]
                if len(tr_rows) < 50 or len(ho_rows) < 30:
                    continue
                model = fit_huber(feats[tr_rows], resid[tr_rows])
                raw = np.zeros(len(df), dtype=float)
                ho_cov = ho_rows[cov[ho_rows]]
                raw[ho_cov] = model.predict(feats[ho_cov])
                bm = metric_triplet(price[ho_rows], base_log[ho_rows])
                for c in top[tgt]:
                    pred = apply_policy(base_log, raw, masks[tgt][c["mask"]], c["cap"], c["strength"])
                    cm = metric_triplet(price[ho_rows], pred[ho_rows])
                    st = stats[id(c)][f"frac{frac}"]
                    st["n"] += 1
                    st["MAPE"] += cm["MAPE"] < bm["MAPE"]
                    st["p95"] += cm["p95_APE"] < bm["p95_APE"]
                    st["MdAPE"] += cm["MdAPE"] <= bm["MdAPE"]
        for c in top[tgt]:
            row = {"target": tgt, "mask": c["mask"], "cap": c["cap"], "strength": c["strength"]}
            probs = []
            for frac in HOLDOUT_FRACS:
                st = stats[id(c)][f"frac{frac}"]
                n = max(st["n"], 1)
                row[f"p_MAPE_{frac}"] = st["MAPE"] / n
                row[f"p_p95_{frac}"] = st["p95"] / n
                row[f"p_MdAPE_{frac}"] = st["MdAPE"] / n
                probs.append((st["MAPE"] / n, st["p95"] / n, st["MdAPE"] / n))
            row["gate_pass"] = bool(all(p[0] >= 0.90 and p[1] >= 0.90 and p[2] >= 0.50 for p in probs))
            gate_rows.append(row)
    gate = pd.DataFrame(gate_rows)
    gate.to_csv(EXP / "outputs" / "gate_results.csv", index=False)

    # ── fixed test 최종 확인 1회 (top 후보, 전체 validation 학습)
    test_rows = []
    for tgt, col in BASES.items():
        base_log = df[col].to_numpy(dtype=float)
        resid = actual_log - base_log
        model = fit_huber(feats[val_idx], resid[val_idx])
        raw = np.zeros(len(df), dtype=float)
        tc = np.where(test_m & cov)[0]
        raw[tc] = model.predict(feats[tc])
        bm = metric_triplet(price[test_m], base_log[test_m])
        test_rows.append({"target": tgt, "candidate": "base", **bm})
        for c in top[tgt]:
            pred = apply_policy(base_log, raw, masks[tgt][c["mask"]], c["cap"], c["strength"])
            m = metric_triplet(price[test_m], pred[test_m])
            test_rows.append({"target": tgt,
                              "candidate": f"{c['mask']}_cap{c['cap']}_s{c['strength']}",
                              **m,
                              "applied_share_test": float(masks[tgt][c["mask"]][test_m].mean())})
    test_df = pd.DataFrame(test_rows)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    config = {
        "experiment_id": "PP-CIMG1",
        "purpose": "CLIP 임베딩 PCA 저차원 Huber residual의 위험 구간 한정 보정 검증",
        "embeddings": str(EMB_PATH.relative_to(REPO)),
        "pca_dim": PCA_DIM, "pca_fit": "train-scope 임베딩 동결 (라벨/validation 작가 무관)",
        "image_coverage": coverage,
        "mask_bounds_frozen_from_validation": bounds,
        "grid": {"caps": CAPS, "strengths": STRENGTHS, "masks": {t: list(m) for t, m in masks.items()}},
        "selection": "validation OOF p95 비악화 + MAPE 개선, 상위 2/target",
        "gate": f"artist {HOLDOUT_FRACS} holdout 각 {N_REPS}회, MAPE/p95 >=0.90, MdAPE >=0.50",
        "seed": SEED,
        "signal_audit_validation_oof": signal_audit,
        "sources": {"base_rows": str(CBASE.relative_to(REPO)), "tiers": str(CCONF_TIERS.relative_to(REPO))},
        "prohibitions": ["0604 사용 금지", "test 후보 선택 금지(최종 확인 1회)"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# PP-CIMG1 Cold 이미지 residual 보정",
        "",
        f"- 이미지 커버리지: validation {coverage['validation']:.3f} / test {coverage['test']:.3f} (미커버 행 보정 0)",
        "",
        "## 신호 예측력 감사 (validation OOF, 작가 경계 일반화)",
        "",
        json.dumps(signal_audit, ensure_ascii=False, indent=1),
        "",
        "## validation OOF 상위 후보",
        "",
        json.dumps(top, ensure_ascii=False, indent=1, default=str),
        "",
        "## artist 반복 holdout 게이트",
        "",
        gate.to_string(index=False) if len(gate) else "(OOF 통과 후보 없음)",
        "",
        "## fixed test 최종 확인",
        "",
        test_df.to_string(index=False),
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print("coverage:", coverage)
    print("\n=== OOF top candidates ===")
    for tgt, cands in top.items():
        for c in cands:
            print(tgt, c["mask"], c["cap"], c["strength"],
                  f"dMAPE={c['val_dMAPE']:.5f} dp95={c['val_dp95']:.5f} dMdAPE={c['val_dMdAPE']:.5f}")
    print("\n=== gate ===")
    print(gate.to_string(index=False) if len(gate) else "(none)")
    print("\n=== fixed test ===")
    print(test_df.to_string(index=False))


if __name__ == "__main__":
    main()
