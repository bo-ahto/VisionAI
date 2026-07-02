#!/usr/bin/env python3
"""PP-CGATE1: Cold dual-output dynamic gated correction.

Warm에서 효과가 있었던 "기준가 + 조건부 보정" 구조를 Cold에 맞게 축소해
검증한다. 핵심은 Cold의 unseen-artist 일반화 리스크 때문에 보정은 작게,
적용 조건은 넓은 구간/방향 일치 중심으로 제한하는 것이다.

Inputs
- PP-CBASE1 fixed cold base rows: research v0.3, guard, operational v0.2
- frozen v0.5 operational hetero blend predictor: p95 defense candidate

Selection rule
- 후보 ranking은 validation 기준으로만 수행한다.
- fixed test는 최종 확인 용도로만 보고한다.
- 0604 데이터는 사용하지 않는다.
"""
from __future__ import annotations

import html
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-CGATE1_cold_dual_output_dynamic_gate"
BASE_ROWS = REPO / "experiments" / "track6" / "PP-CBASE1_cold_base_lock" / "outputs" / "fixed_cold_base_rows.csv"
PRED5 = REPO / "models" / "track6" / "cold_prediction_v0.5_operational" / "predict" / "predict_cold_operational_v0_5.py"

warnings.filterwarnings("ignore", message="X does not have valid feature names")


def load_v05_predictor():
    spec = importlib.util.spec_from_file_location("cold_v05", PRED5)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def metric_triplet(actual_price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(actual_price - pred_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((np.log(actual_price) - pred_log) ** 2))),
        "within_30": float(np.mean(ape <= 0.30)),
        "over_50pct_error_rate": float(np.mean(ape > 0.50)),
    }


def sign_agree(a: np.ndarray, b: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    sa = np.sign(np.where(np.abs(a) < eps, 0.0, a))
    sb = np.sign(np.where(np.abs(b) < eps, 0.0, b))
    return (sa != 0) & (sa == sb)


def add_context() -> pd.DataFrame:
    feats = artifact_features()["cold_lightgbm"]
    _, val_feat, test_feat = load_scope("cold", feats + ["medium_support_bucket"])
    features = pd.concat([
        val_feat.assign(split="validation"),
        test_feat.assign(split="test"),
    ], ignore_index=True)

    base = pd.read_csv(BASE_ROWS)
    merged = base.merge(
        features.drop(columns=["price_krw", "ln_price_krw"], errors="ignore"),
        on=["split", "_track6_row_id"],
        how="left",
        suffixes=("", "__feature"),
    )
    missing_features = merged["medium_support_bucket"].isna().sum()
    if missing_features:
        raise ValueError(f"feature merge failed for {missing_features} rows")

    pred5 = load_v05_predictor()
    v05 = pred5.predict(merged)
    merged["v05_representative_pred_log"] = v05["representative_pred_log"].to_numpy(dtype=float)
    merged["v05_defense_pred_log"] = v05["defense_pred_log"].to_numpy(dtype=float)
    merged["v05_qwidth_log"] = v05["qwidth_log"].to_numpy(dtype=float)
    merged["v05_q40_pred_log"] = v05["q40_pred_log"].to_numpy(dtype=float)
    merged["v05_q50_pred_log"] = v05["q50_pred_log"].to_numpy(dtype=float)
    return merged


def cap_array(qwidth: np.ndarray, q: dict[str, float], basecap: float, profile: str) -> np.ndarray:
    cap = np.full(len(qwidth), basecap, dtype=float)
    if profile == "flat":
        return cap
    if profile == "uncertainty_shrink":
        cap = np.where(qwidth > q["q90"], basecap * 0.25, cap)
        cap = np.where((qwidth > q["q66"]) & (qwidth <= q["q90"]), basecap * 0.40, cap)
        cap = np.where((qwidth > q["q33"]) & (qwidth <= q["q66"]), basecap * 0.70, cap)
        return cap
    if profile == "tail_defense":
        cap = np.where(qwidth <= q["q33"], basecap * 0.25, cap)
        cap = np.where((qwidth > q["q33"]) & (qwidth <= q["q66"]), basecap * 0.50, cap)
        cap = np.where((qwidth > q["q66"]) & (qwidth <= q["q90"]), basecap * 1.00, cap)
        cap = np.where(qwidth > q["q90"], basecap * 1.25, cap)
        return cap
    raise ValueError(profile)


def build_masks(frame: pd.DataFrame, q: dict[str, float]) -> dict[str, np.ndarray]:
    base = frame["research_base_pred_log"].to_numpy(dtype=float)
    d05 = frame["v05_defense_pred_log"].to_numpy(dtype=float) - base
    d02 = frame["v02_defense_pred_log"].to_numpy(dtype=float) - base
    dg = frame["guard_pred_log"].to_numpy(dtype=float) - base
    dy18 = frame["y18_qwidth_pred_log"].to_numpy(dtype=float) - base
    qw = frame["quantile_width_log"].to_numpy(dtype=float)
    gap05 = np.abs(d05)
    gap02 = np.abs(d02)
    agree_05_02 = sign_agree(d05, d02)
    agree_05_guard = sign_agree(d05, dg)
    agree_05_y18 = sign_agree(d05, dy18)
    down05 = d05 < 0
    up05 = d05 > 0

    return {
        "all": np.ones(len(frame), dtype=bool),
        "agree_v05_v02": agree_05_02,
        "agree_v05_guard": agree_05_guard,
        "agree_v05_y18": agree_05_y18,
        "agree_v05_v02_guard": agree_05_02 & agree_05_guard,
        "qwidth_high": qw > q["q66"],
        "qwidth_extreme": qw > q["q90"],
        "qwidth_mid_high": qw > q["q33"],
        "gap05_high": gap05 > q["gap05_q75"],
        "gap02_high": gap02 > q["gap02_q75"],
        "down_only_high_qwidth": down05 & (qw > q["q66"]),
        "down_only_gap_high": down05 & (gap05 > q["gap05_q75"]),
        "up_only_low_qwidth": up05 & (qw <= q["q33"]),
        "agree_down_risk": agree_05_02 & down05 & ((qw > q["q66"]) | (gap05 > q["gap05_q75"])),
        "agree_any_risk": agree_05_02 & ((qw > q["q66"]) | (gap05 > q["gap05_q75"])),
    }


def make_prediction(
    frame: pd.DataFrame,
    target_col: str,
    mask_name: str,
    strength: float,
    basecap: float,
    cap_profile: str,
    q: dict[str, float],
) -> tuple[np.ndarray, float]:
    base = frame["research_base_pred_log"].to_numpy(dtype=float)
    target = frame[target_col].to_numpy(dtype=float)
    delta = target - base
    masks = build_masks(frame, q)
    mask = masks[mask_name]
    cap = cap_array(frame["quantile_width_log"].to_numpy(dtype=float), q, basecap, cap_profile)
    clipped = np.clip(delta, -cap, cap)
    out = base.copy()
    out[mask] = out[mask] + strength * clipped[mask]
    return out, float(mask.mean())


def artist_bootstrap(
    frame: pd.DataFrame,
    base_pred: np.ndarray,
    cand_pred: np.ndarray,
    n: int = 400,
    seed: int = 20260610,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    actual = frame["actual_price"].to_numpy(dtype=float)
    artists = frame["artist_key"].astype(str).to_numpy()
    groups = pd.Series(np.arange(len(frame))).groupby(artists).apply(list)
    wins = {"MdAPE": 0, "MAPE": 0, "p95_APE": 0}
    deltas = {"MdAPE": [], "MAPE": [], "p95_APE": []}
    for _ in range(n):
        choice = rng.choice(len(groups), size=len(groups), replace=True)
        idx = np.concatenate([groups.iloc[i] for i in choice])
        bm = metric_triplet(actual[idx], base_pred[idx])
        cm = metric_triplet(actual[idx], cand_pred[idx])
        for k in wins:
            delta = cm[k] - bm[k]
            deltas[k].append(delta)
            wins[k] += delta <= 0.0
    out: dict[str, float] = {}
    for k in wins:
        arr = np.asarray(deltas[k], dtype=float)
        out[f"artist_boot_p_{k}_nonworse"] = float(wins[k] / n)
        out[f"artist_boot_delta_{k}_median"] = float(np.median(arr))
        out[f"artist_boot_delta_{k}_q05"] = float(np.quantile(arr, 0.05))
        out[f"artist_boot_delta_{k}_q95"] = float(np.quantile(arr, 0.95))
    return out


def write_html(markdown: str, path: Path) -> None:
    escaped = html.escape(markdown)
    body = escaped.replace("\n", "<br>\n")
    path.write_text(
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        "<title>PP-CGATE1 Cold Dual Output Dynamic Gate</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        "max-width:1100px;margin:36px auto;line-height:1.6;color:#111827}"
        "code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
        "pre{white-space:pre-wrap;background:#f3f4f6;padding:16px;border-radius:8px}"
        "</style></head><body><pre>"
        + escaped
        + "</pre></body></html>",
        encoding="utf-8",
    )


def md_table(frame: pd.DataFrame, max_col_width: int = 80) -> str:
    if frame.empty:
        return "(empty)"
    data = frame.copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.6f}")
        else:
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else str(x))
            data[col] = data[col].map(lambda x: x if len(x) <= max_col_width else x[: max_col_width - 1] + "…")
    headers = [str(c) for c in data.columns]
    rows = data.values.tolist()
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(str(v))) for w, v in zip(widths, row, strict=False)]

    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(str(v).ljust(w) for v, w in zip(row, widths, strict=False)) + " |"

    lines = [fmt(headers), "| " + " | ".join("-" * w for w in widths) + " |"]
    lines.extend(fmt([str(v) for v in row]) for row in rows)
    return "\n".join(lines)


def main() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)

    frame = add_context()
    val = frame[frame["split"] == "validation"].reset_index(drop=True)
    test = frame[frame["split"] == "test"].reset_index(drop=True)
    q = {
        "q33": float(val["quantile_width_log"].quantile(0.33)),
        "q66": float(val["quantile_width_log"].quantile(0.66)),
        "q90": float(val["quantile_width_log"].quantile(0.90)),
        "gap05_q75": float((val["v05_defense_pred_log"] - val["research_base_pred_log"]).abs().quantile(0.75)),
        "gap02_q75": float((val["v02_defense_pred_log"] - val["research_base_pred_log"]).abs().quantile(0.75)),
    }

    baselines = {
        "research_v0_3_guard_search": "research_base_pred_log",
        "guard_only": "guard_pred_log",
        "y18_qwidth_bin": "y18_qwidth_pred_log",
        "operational_v0_2_defense": "v02_defense_pred_log",
        "operational_v0_5_hetero_defense": "v05_defense_pred_log",
    }
    rows: list[dict[str, object]] = []
    for name, col in baselines.items():
        for split, part in (("validation", val), ("test", test)):
            m = metric_triplet(part["actual_price"].to_numpy(dtype=float), part[col].to_numpy(dtype=float))
            rows.append({"candidate": name, "family": "baseline", "split": split, "target": col,
                         "mask": "all", "strength": 1.0, "cap": np.nan, "cap_profile": "none",
                         "apply_rate": 1.0, **m})

    target_cols = ["v05_defense_pred_log", "v02_defense_pred_log", "guard_pred_log", "y18_qwidth_pred_log"]
    mask_names = list(build_masks(val, q).keys())
    strengths = [0.20, 0.35, 0.50, 0.75, 1.00]
    caps = [0.015, 0.025, 0.05, 0.075, 0.10, 0.15, 0.25]
    profiles = ["flat", "uncertainty_shrink", "tail_defense"]

    candidate_preds: dict[str, dict[str, np.ndarray]] = {}
    for target_col in target_cols:
        for mask_name in mask_names:
            for strength in strengths:
                for cap in caps:
                    for profile in profiles:
                        cid = f"research_to_{target_col.replace('_pred_log','')}__{mask_name}__s{strength:g}__cap{cap:g}__{profile}"
                        vpred, vrate = make_prediction(val, target_col, mask_name, strength, cap, profile, q)
                        tpred, trate = make_prediction(test, target_col, mask_name, strength, cap, profile, q)
                        candidate_preds[cid] = {"validation": vpred, "test": tpred}
                        for split, part, pred, rate in (("validation", val, vpred, vrate), ("test", test, tpred, trate)):
                            m = metric_triplet(part["actual_price"].to_numpy(dtype=float), pred)
                            rows.append({"candidate": cid, "family": "gated_correction", "split": split,
                                         "target": target_col, "mask": mask_name, "strength": strength,
                                         "cap": cap, "cap_profile": profile, "apply_rate": rate, **m})

    metrics = pd.DataFrame(rows)
    metrics.to_csv(EXP / "outputs" / "candidate_metrics.csv", index=False)

    val_base = metrics[(metrics["split"] == "validation") & (metrics["candidate"] == "research_v0_3_guard_search")].iloc[0]
    test_base = metrics[(metrics["split"] == "test") & (metrics["candidate"] == "research_v0_3_guard_search")].iloc[0]

    val_cands = metrics[(metrics["split"] == "validation") & (metrics["family"] == "gated_correction")].copy()
    for k in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        val_cands[f"delta_{k}_vs_research"] = val_cands[k] - float(val_base[k])
    val_cands["selection_score"] = (
        val_cands["delta_MAPE_vs_research"]
        + 0.35 * val_cands["delta_p95_APE_vs_research"]
        + 0.15 * np.maximum(val_cands["delta_MdAPE_vs_research"], 0)
    )
    val_cands["all_metric_nonworse_val"] = (
        (val_cands["delta_MdAPE_vs_research"] <= 0)
        & (val_cands["delta_MAPE_vs_research"] <= 0)
        & (val_cands["delta_p95_APE_vs_research"] <= 0)
    )
    top = val_cands.sort_values(["all_metric_nonworse_val", "selection_score"], ascending=[False, True]).head(30)
    top.to_csv(EXP / "outputs" / "top_validation_candidates.csv", index=False)

    test_join = metrics[metrics["split"] == "test"].set_index("candidate")
    top_rows = []
    for _, r in top.head(12).iterrows():
        cand = str(r["candidate"])
        tr = test_join.loc[cand]
        rec = r.to_dict()
        for k in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "over_50pct_error_rate"]:
            rec[f"test_{k}"] = float(tr[k])
            rec[f"test_delta_{k}_vs_research"] = float(tr[k]) - float(test_base[k])
        rec.update(artist_bootstrap(val, val["research_base_pred_log"].to_numpy(dtype=float), candidate_preds[cand]["validation"]))
        top_rows.append(rec)
    top_detail = pd.DataFrame(top_rows)
    top_detail.to_csv(EXP / "outputs" / "top_candidate_validation_bootstrap_and_test.csv", index=False)

    pred_cols = {
        "research_v0_3_guard_search": frame["research_base_pred_log"].to_numpy(dtype=float),
        "operational_v0_2_defense": frame["v02_defense_pred_log"].to_numpy(dtype=float),
        "operational_v0_5_hetero_defense": frame["v05_defense_pred_log"].to_numpy(dtype=float),
    }
    for cand in top_detail["candidate"].head(3).astype(str).tolist() if len(top_detail) else []:
        vp = candidate_preds[cand]["validation"]
        tp = candidate_preds[cand]["test"]
        pred_cols[cand] = np.concatenate([vp, tp])
    pred_out = frame[["split", "_track6_row_id", "artist_key", "actual_price", "actual_log",
                      "quantile_width_log", "v02_qwidth_log", "v05_qwidth_log"]].copy()
    for name, pred in pred_cols.items():
        pred_out[f"{name}_log"] = pred
        pred_out[f"{name}_price"] = np.clip(np.exp(pred), 1_000.0, None)
    pred_out.to_csv(EXP / "outputs" / "top_candidate_predictions.csv", index=False)

    report_lines = [
        "# PP-CGATE1 Cold dual-output dynamic gate 결과",
        "",
        "## 목적",
        "- Warm식 `기준가 + 보정값` 구조를 Cold에 직접 복사하지 않고, unseen 작가 리스크에 맞춰 보정 강도와 적용 조건을 제한했다.",
        "- 기준 예측가는 `research_v0_3_guard_search`로 고정하고, v0.5 이종 blend / v0.2 defense / guard / qwidth 후보 방향으로 작은 보정을 시도했다.",
        "- 후보 선택은 validation 기준, fixed test는 확인 용도다. 0604 데이터는 사용하지 않았다.",
        "",
        "## Validation 기준 임계값",
        "```json",
        json.dumps(q, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 기준 모델 성능",
        md_table(metrics[metrics["family"] == "baseline"].round(6)),
        "",
        "## Validation 상위 후보 및 Test 확인",
    ]
    if len(top_detail):
        show_cols = [
            "candidate", "apply_rate", "MdAPE", "MAPE", "p95_APE",
            "delta_MdAPE_vs_research", "delta_MAPE_vs_research", "delta_p95_APE_vs_research",
            "test_MdAPE", "test_MAPE", "test_p95_APE",
            "test_delta_MdAPE_vs_research", "test_delta_MAPE_vs_research", "test_delta_p95_APE_vs_research",
            "artist_boot_p_MAPE_nonworse", "artist_boot_p_p95_APE_nonworse", "artist_boot_p_MdAPE_nonworse",
        ]
        report_lines.append(md_table(top_detail[show_cols].head(12).round(6)))
    else:
        report_lines.append("- 후보 없음")

    report_lines += [
        "",
        "## 해석",
    ]
    if len(top_detail):
        best = top_detail.iloc[0]
        report_lines += [
            f"- Validation 최상위 후보: `{best['candidate']}`",
            f"- validation 변화: MdAPE {best['delta_MdAPE_vs_research']:+.6f}, MAPE {best['delta_MAPE_vs_research']:+.6f}, p95 {best['delta_p95_APE_vs_research']:+.6f}",
            f"- fixed test 변화: MdAPE {best['test_delta_MdAPE_vs_research']:+.6f}, MAPE {best['test_delta_MAPE_vs_research']:+.6f}, p95 {best['test_delta_p95_APE_vs_research']:+.6f}",
        ]
        if best["test_delta_MAPE_vs_research"] < 0 and best["test_delta_p95_APE_vs_research"] < 0:
            report_lines.append("- test에서도 MAPE/p95가 같이 낮아져 후속 안정화 실험 가치가 있다.")
        else:
            report_lines.append("- test에서 개선 전이가 약하거나 일부 지표가 악화되어 운영 교체 후보로는 아직 부족하다.")
    report_lines += [
        "- Cold에서는 v0.3 research 기준이 이미 강해, v0.5/v0.2 방향으로 보정하면 대부분 중앙 정확도 또는 p95 중 하나를 희생한다.",
        "- 의미 있는 다음 단계는 전체 단일 예측가 교체보다 `대표가(v0.3) + 방어가(v0.5) + 신뢰도 표시`의 목적별 출력 정책을 명확히 하는 방향이다.",
    ]
    report = "\n".join(report_lines)
    (EXP / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    write_html(report, EXP / "reports" / "result_report.html")

    run_config = {
        "experiment_id": "PP-CGATE1",
        "base": "research_v0_3_guard_search",
        "targets": target_cols,
        "masks": mask_names,
        "strengths": strengths,
        "caps": caps,
        "cap_profiles": profiles,
        "thresholds": q,
        "selection": "validation only; fixed test reported once",
        "prohibitions": ["0604 데이터 사용 금지", "test로 후보 선택 금지"],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(metrics[metrics["family"] == "baseline"].round(4).to_string(index=False))
    print()
    if len(top_detail):
        print(top_detail[["candidate", "MAPE", "p95_APE", "test_MAPE", "test_p95_APE",
                          "test_delta_MAPE_vs_research", "test_delta_p95_APE_vs_research"]].head(10).round(5).to_string(index=False))
    print(f"\n[PP-CGATE1] wrote {EXP}")


if __name__ == "__main__":
    main()
