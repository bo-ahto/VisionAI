#!/usr/bin/env python3
"""PP-CSRCH1: 검색 delta 그룹 일반화 선행 검증 (Cold 로드맵 Phase 2-3a, 수집 없음).

PP-PCOLD1에서 신규 작가의 v0.3 검색 lookup 커버리지가 0.0임을 확인했다.
수집 확대 전에, 기존 372작가 frozen delta를 작가 단위 속성으로 일반화해
미커버 작가에 전이(guard-only fallback 대체)할 수 있는지 검증한다.

사전 관찰: lookup delta는 25/50/75 분위가 모두 -0.0313로 사실상
"상수 하향 보정 + 소수 outlier" 구조 → 상수 후보가 1차 가설.

- 비교 기준(=현재 fallback): guard-only
- 상한 참조: true per-artist delta (v0.3 연구 base)
- 후보: 상수(중앙값/평균) / 매체 그룹 / 예측가격대 그룹 / 저차원 Huber(메타 포함)
  × strength {0.5, 1.0}, delta cap ±0.2 (lookup과 동일)
- 선택: validation artist-grouped 5-fold OOF (p95 비악화 + MAPE 개선)
- 게이트: validation 작가 80%/70% holdout 각 200회, guard-only 대비
  MAPE/p95 개선확률 >=0.90, MdAPE >=0.50
- 최종 확인: test 작가 전원을 미커버로 가정(validation 작가로만 적합) 1회
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
LOOKUP = REPO / "models" / "track6" / "cold_prediction_v0.3" / "config" / "search_delta_lookup_v0_3.json"
EXP = REPO / "experiments" / "track6" / "PP-CSRCH1_cold_search_delta_generalization"

DELTA_CAP = 0.20
STRENGTHS = [0.5, 1.0]
N_REPS = 200
HOLDOUT_FRACS = [0.80, 0.70]
TOP_K_GATE = 3
SEED = 20260610
META_COLS = ["artist_meta_birth_year", "artist_meta_followers", "artist_meta_total_works"]


def metric_triplet(price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - price) / np.clip(price, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}


def build_artist_table(rows: pd.DataFrame, feats: pd.DataFrame, meta: pd.DataFrame,
                       lookup: dict[str, float]) -> pd.DataFrame:
    r = rows.merge(feats, on=["split", "_track6_row_id"], how="left", validate="one_to_one")
    agg = r.groupby("artist_key").agg(
        guard_pred_median=("guard_pred_log", "median"),
        qwidth_median=("quantile_width_log", "median"),
        log_area_median=("log_area", "median"),
        n_rows=("artist_key", "size"),
        medium_mode=("medium_category", lambda s: s.mode().iloc[0] if len(s.mode()) else "unknown"),
    ).reset_index()
    agg = agg.merge(meta, on="artist_key", how="left")
    agg["delta"] = agg["artist_key"].astype(str).map(lookup)
    return agg


class Candidate:
    """train 작가 테이블로 적합하고, 임의 작가 테이블에 delta_hat을 부여한다."""

    def __init__(self, name: str, kind: str):
        self.name, self.kind = name, kind

    def fit(self, tr: pd.DataFrame) -> "Candidate":
        d = tr["delta"].to_numpy(dtype=float)
        self.global_const_ = float(np.median(d)) if "median" in self.name else float(np.mean(d))
        if self.kind == "medium_group":
            self.map_ = tr.groupby("medium_mode")["delta"].median().to_dict()
        elif self.kind == "price_band":
            self.bins_ = tr["guard_pred_median"].quantile([0.33, 0.67]).to_numpy()
            tr = tr.assign(_band=np.digitize(tr["guard_pred_median"], self.bins_))
            self.map_ = tr.groupby("_band")["delta"].median().to_dict()
        elif self.kind == "huber":
            cols = ["guard_pred_median", "qwidth_median", "log_area_median", "n_rows"] + META_COLS
            x = tr[cols].astype(float)
            self.imputer_ = x.median()
            x = x.fillna(self.imputer_)
            self.mu_, self.sd_ = x.mean(), x.std().replace(0, 1.0)
            self.model_ = HuberRegressor(epsilon=1.35, alpha=1e-2, max_iter=2000).fit(
                ((x - self.mu_) / self.sd_).to_numpy(), tr["delta"].to_numpy(dtype=float))
            self.cols_ = cols
        return self

    def predict(self, te: pd.DataFrame) -> np.ndarray:
        if self.kind == "const":
            return np.full(len(te), self.global_const_)
        if self.kind == "medium_group":
            return te["medium_mode"].map(self.map_).fillna(self.global_const_).to_numpy(dtype=float)
        if self.kind == "price_band":
            band = np.digitize(te["guard_pred_median"], self.bins_)
            return pd.Series(band).map(self.map_).fillna(self.global_const_).to_numpy(dtype=float)
        x = te[self.cols_].astype(float).fillna(self.imputer_)
        return self.model_.predict(((x - self.mu_) / self.sd_).to_numpy())


def make_candidates() -> list[Candidate]:
    return [Candidate("const_median", "const"), Candidate("const_mean", "const"),
            Candidate("medium_group_median", "medium_group"),
            Candidate("price_band_median", "price_band"),
            Candidate("huber_lowdim_meta", "huber")]


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    rows = pd.read_csv(CBASE)
    lookup = {str(k): float(v) for k, v in
              json.loads(LOOKUP.read_text(encoding="utf-8"))["artist_delta"].items()}

    features = artifact_features()["cold_lightgbm"]
    _, fval, ftest = load_scope("cold", features)
    feats = pd.concat([fval.assign(split="validation"), ftest.assign(split="test")],
                      ignore_index=True)[["split", "_track6_row_id", "medium_category", "log_area"]]
    meta_raw = pd.concat([
        pd.read_csv(REPO / "data" / "track6_split" / "track6_val_cold.csv", low_memory=False),
        pd.read_csv(REPO / "data" / "track6_split" / "track6_test_cold.csv", low_memory=False),
    ], ignore_index=True)
    meta = meta_raw.groupby("artist_key")[META_COLS].first().reset_index()

    val_rows = rows[rows["split"] == "validation"].reset_index(drop=True)
    test_rows = rows[rows["split"] == "test"].reset_index(drop=True)
    val_art = build_artist_table(val_rows, feats, meta, lookup)
    test_art = build_artist_table(test_rows, feats, meta, lookup)
    assert val_art["delta"].notna().all() and test_art["delta"].notna().all()

    def eval_rows(part: pd.DataFrame, delta_by_artist: dict[str, float], strength: float) -> dict[str, float]:
        d = part["artist_key"].astype(str).map(delta_by_artist).fillna(0.0).to_numpy(dtype=float)
        pred = part["guard_pred_log"].to_numpy(dtype=float) + np.clip(strength * d, -DELTA_CAP, DELTA_CAP)
        return metric_triplet(part["actual_price"].to_numpy(dtype=float), pred)

    # ── validation artist-grouped 5-fold OOF
    base_val = metric_triplet(val_rows["actual_price"].to_numpy(),
                              val_rows["guard_pred_log"].to_numpy())
    oof_records = []
    gkf = GroupKFold(n_splits=5)
    art_keys = val_art["artist_key"].astype(str).to_numpy()
    for cand_proto in make_candidates():
        delta_hat = np.zeros(len(val_art))
        for tr, te in gkf.split(val_art, groups=art_keys):
            c = Candidate(cand_proto.name, cand_proto.kind).fit(val_art.iloc[tr])
            delta_hat[te] = c.predict(val_art.iloc[te])
        dmap = dict(zip(art_keys, delta_hat))
        for s in STRENGTHS:
            m = eval_rows(val_rows, dmap, s)
            oof_records.append({"candidate": cand_proto.name, "strength": s,
                                **{f"val_{k}": v for k, v in m.items()},
                                "val_dMAPE": m["MAPE"] - base_val["MAPE"],
                                "val_dp95": m["p95_APE"] - base_val["p95_APE"],
                                "val_dMdAPE": m["MdAPE"] - base_val["MdAPE"]})
    oof = pd.DataFrame(oof_records).sort_values("val_dMAPE")
    oof.to_csv(EXP / "outputs" / "oof_candidate_metrics.csv", index=False)
    top = oof[(oof["val_dp95"] <= 0) & (oof["val_dMAPE"] < 0)].head(TOP_K_GATE).to_dict("records")

    # ── artist 반복 holdout 게이트
    gate_rows = []
    uniq = val_art["artist_key"].astype(str).to_numpy()
    for c in top:
        rec = {"candidate": c["candidate"], "strength": c["strength"]}
        ok_all = True
        for frac in HOLDOUT_FRACS:
            wins = {"MAPE": 0, "p95": 0, "MdAPE": 0}
            n = 0
            for _ in range(N_REPS):
                tr_art = set(rng.choice(uniq, size=int(len(uniq) * frac), replace=False))
                tr_tab = val_art[val_art["artist_key"].astype(str).isin(tr_art)]
                ho_rows = val_rows[~val_rows["artist_key"].astype(str).isin(tr_art)]
                if len(tr_tab) < 20 or len(ho_rows) < 30:
                    continue
                model = Candidate(c["candidate"], next(
                    p.kind for p in make_candidates() if p.name == c["candidate"])).fit(tr_tab)
                ho_tab = val_art[~val_art["artist_key"].astype(str).isin(tr_art)]
                dmap = dict(zip(ho_tab["artist_key"].astype(str), model.predict(ho_tab)))
                cm = eval_rows(ho_rows, dmap, c["strength"])
                bm = metric_triplet(ho_rows["actual_price"].to_numpy(),
                                    ho_rows["guard_pred_log"].to_numpy())
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

    # ── test 최종 확인: test 작가 전원 미커버 가정 (validation 작가로만 적합)
    test_price = test_rows["actual_price"].to_numpy(dtype=float)
    guard_only = metric_triplet(test_price, test_rows["guard_pred_log"].to_numpy())
    true_delta = metric_triplet(test_price, test_rows["research_base_pred_log"].to_numpy())
    test_records = [
        {"candidate": "guard_only_fallback(현행)", **guard_only},
        {"candidate": "true_per_artist_delta(v0.3 상한)", **true_delta},
    ]
    for c in top:
        model = Candidate(c["candidate"], next(
            p.kind for p in make_candidates() if p.name == c["candidate"])).fit(val_art)
        dmap = dict(zip(test_art["artist_key"].astype(str), model.predict(test_art)))
        m = eval_rows(test_rows, dmap, c["strength"])
        recovered = ((guard_only["MAPE"] - m["MAPE"])
                     / max(guard_only["MAPE"] - true_delta["MAPE"], 1e-12))
        test_records.append({"candidate": f"{c['candidate']}_s{c['strength']}", **m,
                             "search_gain_recovered_MAPE": float(recovered)})
    test_df = pd.DataFrame(test_records)
    test_df.to_csv(EXP / "outputs" / "fixed_test_metrics.csv", index=False)

    delta_series = pd.Series(list(lookup.values()), dtype=float)
    config = {
        "experiment_id": "PP-CSRCH1",
        "purpose": "수집 없이 검색 delta를 그룹 일반화해 미커버 작가 fallback(guard-only)을 대체할 수 있는지 검증",
        "delta_lookup_stats": {k: float(v) for k, v in
                               delta_series.describe()[["mean", "std", "25%", "50%", "75%"]].items()},
        "delta_outlier_share_abs_gt_0.05": float((delta_series.abs() > 0.05).mean()),
        "candidates": [c.name for c in make_candidates()], "strengths": STRENGTHS,
        "delta_cap": DELTA_CAP,
        "meta_coverage_artist": {c: float(meta[c].notna().mean()) for c in META_COLS},
        "gate": f"artist {HOLDOUT_FRACS} holdout 각 {N_REPS}회 vs guard-only, MAPE/p95>=0.90, MdAPE>=0.50",
        "test_protocol": "test 작가 전원 미커버 가정, validation 작가로만 적합 (test delta 미사용)",
        "seed": SEED,
        "sources": {"base_rows": str(CBASE.relative_to(REPO)), "lookup": str(LOOKUP.relative_to(REPO))},
        "prohibitions": ["0604 사용 금지", "test 후보 선택 금지(최종 확인 1회)"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# PP-CSRCH1 검색 delta 그룹 일반화 (수집 없음)",
        "",
        "- 비교 기준 = guard-only(현행 미커버 fallback), 상한 = true per-artist delta(v0.3).",
        "",
        "## validation OOF",
        "",
        oof.round(5).to_string(index=False),
        "",
        "## artist 반복 holdout 게이트 (vs guard-only)",
        "",
        gate.round(4).to_string(index=False) if len(gate) else "(OOF 통과 후보 없음)",
        "",
        "## test 최종 확인 (미커버 시나리오)",
        "",
        test_df.round(4).to_string(index=False),
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(oof.round(5).to_string(index=False))
    print()
    print(gate.round(4).to_string(index=False) if len(gate) else "(no gate candidates)")
    print()
    print(test_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
