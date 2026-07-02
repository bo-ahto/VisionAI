#!/usr/bin/env python3
"""PP-CDIAG1: Cold base 잔차 진단 (Cold 로드맵 Phase 1).

Warm PP-HCOEF13/23 방법론을 모방해 PP-CBASE1 고정 base의 남은 오차를
validation 기준으로 구간 분해하고, 이후 타겟 실험이 노릴 Cold 위험 구간을
확정한다. 위험 구간 선정은 validation으로만 하고 test는 확인 표기용이다.
0604는 Warm 시험 제출 전용이므로 사용하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CBASE = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
EXP = REPO / "experiments" / "track6" / "PP-CDIAG1_cold_residual_diagnosis"

BASES = {
    "research": "research_base_pred_log",
    "operational": "v02_defense_pred_log",
}
RISK_MAPE_RATIO = 1.30   # 구간 MAPE가 전체의 1.3배 이상
RISK_P95_RATIO = 1.30    # 또는 구간 p95가 전체의 1.3배 이상
RISK_MIN_N = 80          # validation 최소 표본


def metric_triplet(ape: np.ndarray) -> dict[str, float]:
    return {
        "n": int(len(ape)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
    }


def add_segments(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    val = out[out["split"] == "validation"]

    # quantile width (validation 분위수 경계 고정)
    qw = val["quantile_width_log"]
    q33, q67, q90 = qw.quantile([0.33, 0.67, 0.90])
    out["seg_qwidth"] = pd.cut(out["quantile_width_log"], [-np.inf, q33, q67, q90, np.inf],
                               labels=["qwidth_low", "qwidth_mid", "qwidth_high", "qwidth_extreme"])

    # 예측 가격대 (research base 기준, 라벨 미사용)
    pred_price = np.exp(out["research_base_pred_log"])
    out["seg_pred_price"] = pd.cut(pred_price, [0, 1e6, 5e6, 2e7, np.inf],
                                   labels=["pred_lt_1m", "pred_1_5m", "pred_5_20m", "pred_ge_20m"])

    # 모델 간 의견차: y18(검색 기반 체인) vs v0.2(search-free)
    gap = (out["y18_qwidth_pred_log"] - out["v02_defense_pred_log"]).abs()
    g50, g90 = gap[out["split"] == "validation"].quantile([0.50, 0.90])
    out["seg_model_gap"] = pd.cut(gap, [-np.inf, g50, g90, np.inf],
                                  labels=["gap_low", "gap_high", "gap_extreme"])

    # guard 적용 여부 / 검색 delta 크기
    out["seg_guard_applied"] = np.where(
        (out["guard_pred_log"] - out["y18_qwidth_pred_log"]).abs() > 1e-12, "guard_on", "guard_off")
    sdelta = (out["research_base_pred_log"] - out["guard_pred_log"]).abs()
    s67 = sdelta[out["split"] == "validation"].quantile(0.67)
    out["seg_search_delta"] = pd.cut(sdelta, [-np.inf, 1e-12, s67, np.inf],
                                     labels=["sdelta_zero", "sdelta_small", "sdelta_large"])

    # split 내 작가 행수 (작가 쏠림 축)
    rows_per_artist = out.groupby(["split", "artist_key"])["artist_key"].transform("size")
    out["seg_artist_rows"] = pd.cut(rows_per_artist, [0, 2, 9, 49, np.inf],
                                    labels=["artist_rows_1_2", "artist_rows_3_9",
                                            "artist_rows_10_49", "artist_rows_50_plus"])
    return out


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    base_rows = pd.read_csv(CBASE)

    # 매체/크기 피처 조인
    features = artifact_features()["cold_lightgbm"]
    _, val, test = load_scope("cold", features)
    feat = pd.concat([
        val.assign(split="validation"), test.assign(split="test"),
    ], ignore_index=True)[["split", "_track6_row_id", "medium_category", "log_area"]]
    df = base_rows.merge(feat, on=["split", "_track6_row_id"], how="left", validate="one_to_one")

    for name, col in BASES.items():
        pred_price = np.clip(np.exp(df[col]), 1_000.0, None)
        df[f"ape_{name}"] = np.abs(pred_price - df["actual_price"]) / np.clip(df["actual_price"], 1.0, None)
        df[f"resid_{name}"] = df["actual_log"] - df[col]

    df = add_segments(df)
    area_q33, area_q67 = df.loc[df["split"] == "validation", "log_area"].quantile([0.33, 0.67])
    df["seg_size"] = pd.cut(df["log_area"], [-np.inf, area_q33, area_q67, np.inf],
                            labels=["size_small", "size_mid", "size_large"])
    top_medium = df.loc[df["split"] == "validation", "medium_category"].value_counts().head(6).index
    df["seg_medium"] = np.where(df["medium_category"].isin(top_medium),
                                df["medium_category"].astype(str), "medium_other")

    seg_cols = ["seg_qwidth", "seg_pred_price", "seg_model_gap", "seg_guard_applied",
                "seg_search_delta", "seg_artist_rows", "seg_size", "seg_medium"]

    rows = []
    overall = {}
    for split, part in df.groupby("split"):
        for base in BASES:
            overall[(split, base)] = metric_triplet(part[f"ape_{base}"].to_numpy())
    for seg in seg_cols:
        for split, part in df.groupby("split"):
            for level, sub in part.groupby(seg, observed=True):
                for base in BASES:
                    m = metric_triplet(sub[f"ape_{base}"].to_numpy())
                    ov = overall[(split, base)]
                    rows.append({
                        "segment_dim": seg, "segment": str(level), "split": split, "base": base,
                        **m,
                        "MAPE_ratio_vs_overall": m["MAPE"] / ov["MAPE"],
                        "p95_ratio_vs_overall": m["p95_APE"] / ov["p95_APE"],
                        "resid_mean": float(sub[f"resid_{base}"].mean()),
                    })
    breakdown = pd.DataFrame(rows)
    breakdown.to_csv(EXP / "outputs" / "segment_breakdown.csv", index=False)

    # 위험 구간: validation 기준, 두 base 중 하나라도 임계 초과 + 최소 표본
    vsel = breakdown[(breakdown["split"] == "validation") & (breakdown["n"] >= RISK_MIN_N)]
    flag = vsel[(vsel["MAPE_ratio_vs_overall"] >= RISK_MAPE_RATIO)
                | (vsel["p95_ratio_vs_overall"] >= RISK_P95_RATIO)]
    risk = (flag.groupby(["segment_dim", "segment"])
            .agg(bases_flagged=("base", lambda s: ",".join(sorted(set(s)))),
                 n_validation=("n", "max"),
                 max_MAPE_ratio=("MAPE_ratio_vs_overall", "max"),
                 max_p95_ratio=("p95_ratio_vs_overall", "max"),
                 resid_mean=("resid_mean", "mean"))
            .reset_index()
            .sort_values("max_MAPE_ratio", ascending=False))
    # test 확인 표기 (선정에는 미사용)
    tsel = breakdown[breakdown["split"] == "test"].set_index(["segment_dim", "segment", "base"])
    risk["test_MAPE_ratio_research"] = [
        float(tsel.loc[(d, s, "research"), "MAPE_ratio_vs_overall"]) if (d, s, "research") in tsel.index else np.nan
        for d, s in zip(risk["segment_dim"], risk["segment"])]
    risk.to_csv(EXP / "outputs" / "risk_segments.csv", index=False)

    # 잔차 크기 상관 감사 (HCOEF23식, validation/research base)
    vpart = df[df["split"] == "validation"]
    signals = {
        "quantile_width_log": vpart["quantile_width_log"],
        "model_gap_abs": (vpart["y18_qwidth_pred_log"] - vpart["v02_defense_pred_log"]).abs(),
        "search_delta_abs": (vpart["research_base_pred_log"] - vpart["guard_pred_log"]).abs(),
        "log_area": vpart["log_area"],
        "artist_rows_in_split": vpart.groupby("artist_key")["artist_key"].transform("size"),
    }
    corr = {k: float(np.corrcoef(v, vpart["ape_research"])[0, 1]) for k, v in signals.items()}

    config = {
        "experiment_id": "PP-CDIAG1",
        "purpose": "Cold 고정 base 잔차의 구간 분해 및 위험 구간 확정 (validation 기준)",
        "bases": BASES,
        "risk_rule": f"validation n>={RISK_MIN_N} & (MAPE ratio>={RISK_MAPE_RATIO} | p95 ratio>={RISK_P95_RATIO})",
        "overall_metrics": {f"{s}/{b}": m for (s, b), m in overall.items()},
        "ape_corr_validation_research_base": corr,
        "source": str(CBASE.relative_to(REPO)),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    risk_fmt = risk.copy()
    for c in ("max_MAPE_ratio", "max_p95_ratio", "resid_mean", "test_MAPE_ratio_research"):
        risk_fmt[c] = risk_fmt[c].map(lambda v: f"{v:.3f}" if pd.notna(v) else "-")
    report = [
        "# PP-CDIAG1 Cold base 잔차 진단",
        "",
        "- 위험 구간 선정: validation 기준만 사용. test ratio는 확인 표기.",
        "- 0604 미사용 (Warm 시험 제출 전용).",
        "",
        "## 전체 기준 (MdAPE/MAPE/p95)",
        "",
        json.dumps({f"{s}/{b}": {k: round(v, 4) for k, v in m.items()} for (s, b), m in overall.items()},
                   ensure_ascii=False, indent=2),
        "",
        "## 위험 구간 (validation)",
        "",
        risk_fmt.to_string(index=False),
        "",
        "## 잔차 크기 상관 (validation, 연구 base APE)",
        "",
        json.dumps({k: round(v, 4) for k, v in corr.items()}, ensure_ascii=False, indent=2),
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(report), encoding="utf-8")

    print(json.dumps({f"{s}/{b}": {k: round(v, 4) for k, v in m.items()} for (s, b), m in overall.items()},
                     ensure_ascii=False, indent=2))
    print(risk_fmt.to_string(index=False))
    print(json.dumps({k: round(v, 4) for k, v in corr.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
