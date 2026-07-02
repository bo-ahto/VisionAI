#!/usr/bin/env python3
"""Run PP-SA2 Warm similar-artist prior correction validation.

PP-SA2 uses PP-SA1 similar-artist priors as a small post-prediction correction
on top of the selected Warm operational candidate. Candidate parameters are
selected on validation_oof and then evaluated once on the fixed warm test split.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-SA2"
EXP_SLUG = "PP-SA2_warm_similar_artist_prior_correction"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

BASE_PRED_PATH = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
SA1_PRED_PATH = REPO / "experiments" / "track6" / "PP-SA1_similar_artist_artwork_grouping" / "outputs" / "predictions.csv"
BASE_CANDIDATE = (
    "ppopt258_operational_pp252_narrow_refinement__"
    "source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05"
)


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def load_data() -> pd.DataFrame:
    base_cols = [
        "candidate",
        "split",
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "pred_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "component_prediction_spread",
        "stable_price_band",
    ]
    base = pd.read_csv(BASE_PRED_PATH, usecols=base_cols, low_memory=False)
    base = base[base["candidate"].astype(str).eq(BASE_CANDIDATE)].copy()
    if base.empty:
        raise RuntimeError(f"Base candidate not found: {BASE_CANDIDATE}")

    sa = pd.read_csv(SA1_PRED_PATH, low_memory=False)
    sa = sa[(sa["scope"].astype(str).eq("warm")) & (sa["split"].astype(str).isin(["validation", "test"]))].copy()
    wide = sa.pivot_table(index=["split", "_track6_row_id"], columns="candidate", values="pred_log", aggfunc="last").reset_index()
    meta = sa.drop_duplicates(["split", "_track6_row_id"])[
        ["split", "_track6_row_id", "sa_group_level", "sa_coverage_tier", "sa_group_n", "sa_artist_count"]
    ]
    priors = meta.merge(wide, on=["split", "_track6_row_id"], how="left")
    priors = priors.rename(
        columns={
            "same_artist_artwork_direct_median": "same_artist_prior_log",
            "similar_artist_artwork_direct_median": "similar_artist_prior_log",
        }
    )
    data = base.merge(priors, on=["split", "_track6_row_id"], how="inner")
    required = ["same_artist_prior_log", "similar_artist_prior_log"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise RuntimeError(f"Missing prior columns: {missing}")
    return data


def gate_mask(frame: pd.DataFrame, gate: str) -> np.ndarray:
    confidence = frame["confidence_tier"].astype(str)
    strict = frame["sa_group_level"].astype(str).eq("similar_artist_medium_support_size")
    medium_or_strict = frame["sa_group_level"].astype(str).isin(
        ["similar_artist_medium_support_size", "similar_artist_medium_size"]
    )
    low_svc = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0) < 15
    high_uncertainty = pd.to_numeric(frame["quantile_width"], errors="coerce").fillna(0) >= float(
        pd.to_numeric(frame["quantile_width"], errors="coerce").median()
    )
    if gate == "all":
        return np.ones(len(frame), dtype=bool)
    if gate == "strict_similar_artwork":
        return strict.to_numpy()
    if gate == "medium_or_strict_similar_artwork":
        return medium_or_strict.to_numpy()
    if gate == "low_svc":
        return low_svc.to_numpy()
    if gate == "low_confidence":
        return confidence.eq("low_confidence").to_numpy()
    if gate == "low_svc_and_strict":
        return (low_svc & strict).to_numpy()
    if gate == "high_uncertainty_and_strict":
        return (high_uncertainty & strict).to_numpy()
    if gate == "low_svc_or_low_confidence":
        return (low_svc | confidence.eq("low_confidence")).to_numpy()
    raise ValueError(gate)


def correction_delta(frame: pd.DataFrame, source: str) -> np.ndarray:
    if source == "similar_minus_base":
        return frame["similar_artist_prior_log"].to_numpy(dtype=float) - frame["pred_log"].to_numpy(dtype=float)
    if source == "similar_minus_same_artist":
        return frame["similar_artist_prior_log"].to_numpy(dtype=float) - frame["same_artist_prior_log"].to_numpy(dtype=float)
    if source == "blend15_minus_base":
        blend = 0.85 * frame["same_artist_prior_log"].to_numpy(dtype=float) + 0.15 * frame["similar_artist_prior_log"].to_numpy(dtype=float)
        return blend - frame["pred_log"].to_numpy(dtype=float)
    raise ValueError(source)


def apply_candidate(frame: pd.DataFrame, source: str, strength: float, cap: float, gate: str) -> np.ndarray:
    base = frame["pred_log"].to_numpy(dtype=float)
    delta = correction_delta(frame, source)
    gated = gate_mask(frame, gate)
    correction = strength * np.clip(delta, -cap, cap)
    correction[~gated] = 0.0
    return base + correction


def candidate_grid() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"candidate": "baseline_pp258_operational", "source": "none", "strength": 0.0, "cap": 0.0, "gate": "none"}
    ]
    for source in ["similar_minus_base", "similar_minus_same_artist", "blend15_minus_base"]:
        for gate in [
            "all",
            "strict_similar_artwork",
            "medium_or_strict_similar_artwork",
            "low_svc",
            "low_confidence",
            "low_svc_and_strict",
            "high_uncertainty_and_strict",
            "low_svc_or_low_confidence",
        ]:
            for strength in [0.02, 0.05, 0.08, 0.10, 0.15, 0.20]:
                for cap in [0.0025, 0.005, 0.01, 0.02, 0.03, 0.05]:
                    rows.append({
                        "candidate": f"sa2__{source}__gate={gate}__s={strength:g}__cap={cap:g}",
                        "source": source,
                        "strength": strength,
                        "cap": cap,
                        "gate": gate,
                    })
    return rows


def evaluate_candidates(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    for cfg in candidate_grid():
        for split, frame in data.groupby("split", dropna=False):
            if cfg["source"] == "none":
                pred_log = frame["pred_log"].to_numpy(dtype=float)
                gated_rows = 0
                mean_abs_correction = 0.0
            else:
                base = frame["pred_log"].to_numpy(dtype=float)
                pred_log = apply_candidate(frame, cfg["source"], cfg["strength"], cfg["cap"], cfg["gate"])
                gated_rows = int(gate_mask(frame, cfg["gate"]).sum())
                mean_abs_correction = float(np.mean(np.abs(pred_log - base)))
            row = {
                "experiment_id": EXP_ID,
                "candidate": cfg["candidate"],
                "source": cfg["source"],
                "gate": cfg["gate"],
                "strength": cfg["strength"],
                "cap": cfg["cap"],
                "split": split,
                "gated_rows": gated_rows,
                "mean_abs_correction_log": mean_abs_correction,
                **metric_values(frame, pred_log),
            }
            rows.append(row)
            if split in ["validation", "test"]:
                part = frame[
                    [
                        "_track6_row_id",
                        "artist_key",
                        "artist_name_ko",
                        "actual_log",
                        "actual_price",
                        "pred_log",
                        "same_artist_prior_log",
                        "similar_artist_prior_log",
                        "sa_group_level",
                        "sa_coverage_tier",
                        "sa_group_n",
                        "sa_artist_count",
                    ]
                ].copy()
                part["experiment_id"] = EXP_ID
                part["candidate"] = cfg["candidate"]
                part["split"] = split
                part["corrected_pred_log"] = pred_log
                part["correction_log"] = pred_log - frame["pred_log"].to_numpy(dtype=float)
                part["corrected_pred_price"] = np.clip(np.exp(pred_log), 1_000.0, None)
                predictions.append(part)
    return pd.DataFrame(rows), pd.concat(predictions, ignore_index=True)


def select_candidate(metrics: pd.DataFrame) -> pd.Series:
    val = metrics[metrics["split"].eq("validation")].copy()
    base = val[val["candidate"].eq("baseline_pp258_operational")].iloc[0]
    candidates = val.copy()
    candidates["delta_MdAPE"] = base["MdAPE"] - candidates["MdAPE"]
    candidates["delta_MAPE"] = base["MAPE"] - candidates["MAPE"]
    candidates["delta_p95_APE"] = base["p95_APE"] - candidates["p95_APE"]
    pass_rows = candidates[
        (candidates["delta_MAPE"] >= -0.0002)
        & (candidates["delta_p95_APE"] >= -0.0010)
        & (candidates["mean_abs_correction_log"] <= 0.005)
    ].copy()
    if pass_rows.empty:
        pass_rows = candidates.copy()
    pass_rows["selection_score"] = (
        pass_rows["delta_MdAPE"] * 1.0
        + pass_rows["delta_MAPE"] * 0.7
        + pass_rows["delta_p95_APE"] * 0.3
        - pass_rows["mean_abs_correction_log"] * 0.2
    )
    return pass_rows.sort_values(["selection_score", "delta_MdAPE", "delta_MAPE"], ascending=False).iloc[0]


def select_conservative_service_candidate(metrics: pd.DataFrame) -> pd.Series:
    val = metrics[metrics["split"].eq("validation")].copy()
    base = val[val["candidate"].eq("baseline_pp258_operational")].iloc[0]
    candidates = val[
        (val["source"].eq("similar_minus_same_artist"))
        & val["gate"].isin(["medium_or_strict_similar_artwork", "strict_similar_artwork", "high_uncertainty_and_strict"])
    ].copy()
    candidates["delta_MdAPE"] = base["MdAPE"] - candidates["MdAPE"]
    candidates["delta_MAPE"] = base["MAPE"] - candidates["MAPE"]
    candidates["delta_p95_APE"] = base["p95_APE"] - candidates["p95_APE"]
    pass_rows = candidates[
        (candidates["delta_MdAPE"] >= -1e-12)
        & (candidates["delta_MAPE"] >= -1e-12)
        & (candidates["delta_p95_APE"] >= -1e-12)
        & (candidates["mean_abs_correction_log"] <= 0.001)
    ].copy()
    if pass_rows.empty:
        return select_candidate(metrics)
    pass_rows["service_score"] = (
        pass_rows["delta_MdAPE"] * 1.0
        + pass_rows["delta_MAPE"] * 0.8
        + pass_rows["delta_p95_APE"] * 0.5
        - pass_rows["mean_abs_correction_log"] * 0.5
    )
    return pass_rows.sort_values(["service_score", "delta_MdAPE", "delta_p95_APE"], ascending=False).iloc[0]


def render_report(metrics: pd.DataFrame, selected: pd.Series, conservative: pd.Series) -> tuple[str, str]:
    val_base = metrics[(metrics["split"].eq("validation")) & (metrics["candidate"].eq("baseline_pp258_operational"))].iloc[0]
    test_base = metrics[(metrics["split"].eq("test")) & (metrics["candidate"].eq("baseline_pp258_operational"))].iloc[0]
    selected_test = metrics[(metrics["split"].eq("test")) & (metrics["candidate"].eq(selected["candidate"]))].iloc[0]
    conservative_val = metrics[(metrics["split"].eq("validation")) & (metrics["candidate"].eq(conservative["candidate"]))].iloc[0]
    conservative_test = metrics[(metrics["split"].eq("test")) & (metrics["candidate"].eq(conservative["candidate"]))].iloc[0]
    val_top = metrics[metrics["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)
    test_compare = metrics[
        (metrics["split"].eq("test"))
        & metrics["candidate"].isin(["baseline_pp258_operational", selected["candidate"], conservative["candidate"]])
    ].copy()
    def markdown_table(frame: pd.DataFrame) -> list[str]:
        cols = list(frame.columns)
        out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for row in frame.itertuples(index=False):
            vals = []
            for value in row:
                if isinstance(value, float):
                    vals.append(f"{value:.6f}")
                else:
                    vals.append(str(value))
            out.append("| " + " | ".join(vals) + " |")
        return out

    lines = [
        f"# {EXP_ID} Warm 유사 작가 기준가 보정 검증",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 기준 모델: Warm 운영 1순위 후보 `PP258 operational`",
        "- 목적: 유사 작가+작품 기준가를 최종 예측값 대체가 아니라 작은 로그 보정값으로 사용할 수 있는지 검증한다.",
        "- 선택 방식: validation_oof에서 보정식과 강도를 고르고 fixed test에서 한 번 평가한다.",
        "",
        "## 1. 보정식",
        "",
        "```text",
        "후보_보정예측로그가격",
        "  = 기존_Warm_운영예측로그가격",
        "  + strength * clip(유사작가_기준로그가격 - 비교기준로그가격, -cap, +cap)",
        "```",
        "",
        "- `strength`: 유사 작가 기준을 얼마나 반영할지 정하는 보정 강도",
        "- `cap`: 한 row에서 움직일 수 있는 최대 로그 보정 폭",
        "- `gate`: 모든 row가 아니라 특정 조건 row에만 보정을 적용하는 규칙",
        "",
        "## 2. Validation 선택 후보",
        "",
        f"- 선택 후보: `{selected['candidate']}`",
        f"- source: `{selected['source']}`",
        f"- gate: `{selected['gate']}`",
        f"- strength: {float(selected['strength']):.4f}",
        f"- cap: {float(selected['cap']):.4f}",
        f"- validation MdAPE/MAPE/p95: {selected['MdAPE']:.6f} / {selected['MAPE']:.6f} / {selected['p95_APE']:.6f}",
        f"- validation baseline MdAPE/MAPE/p95: {val_base['MdAPE']:.6f} / {val_base['MAPE']:.6f} / {val_base['p95_APE']:.6f}",
        "",
        "## 3. 보수적 서비스 후보",
        "",
        f"- 선택 후보: `{conservative['candidate']}`",
        f"- source: `{conservative['source']}`",
        f"- gate: `{conservative['gate']}`",
        f"- strength: {float(conservative['strength']):.4f}",
        f"- cap: {float(conservative['cap']):.4f}",
        f"- validation MdAPE/MAPE/p95: {conservative_val['MdAPE']:.6f} / {conservative_val['MAPE']:.6f} / {conservative_val['p95_APE']:.6f}",
        "- 선택 기준: 유사 작가 기준과 같은 작가 기준의 차이만 사용하고, 유사 작가+작품 조건이 중간 이상인 row에만 평균 0.001 로그 이하로 보정",
        "",
        "## 4. Fixed Test 결과",
        "",
        "| 후보 | n | MdAPE | MAPE | p95_APE | RMSE_log | 평균 보정폭 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| baseline | {int(test_base['n'])} | {test_base['MdAPE']:.6f} | {test_base['MAPE']:.6f} | "
            f"{test_base['p95_APE']:.6f} | {test_base['RMSE_log']:.6f} | {test_base['mean_abs_correction_log']:.6f} |"
        ),
        (
            f"| selected correction | {int(selected_test['n'])} | {selected_test['MdAPE']:.6f} | {selected_test['MAPE']:.6f} | "
            f"{selected_test['p95_APE']:.6f} | {selected_test['RMSE_log']:.6f} | {selected_test['mean_abs_correction_log']:.6f} |"
        ),
        (
            f"| conservative service candidate | {int(conservative_test['n'])} | {conservative_test['MdAPE']:.6f} | {conservative_test['MAPE']:.6f} | "
            f"{conservative_test['p95_APE']:.6f} | {conservative_test['RMSE_log']:.6f} | {conservative_test['mean_abs_correction_log']:.6f} |"
        ),
        "",
        "## 5. 해석",
    ]
    if selected_test["MdAPE"] < test_base["MdAPE"] and selected_test["MAPE"] <= test_base["MAPE"]:
        lines.append("- 유사 작가 기준가 보정이 fixed test에서도 대표 오차와 평균 오차를 함께 개선했다.")
        lines.append("- 다만 보정폭이 작으므로 운영 반영 전 반복 검증과 slice 검증이 필요하다.")
    elif selected_test["MdAPE"] < test_base["MdAPE"]:
        lines.append("- 대표 오차는 개선됐지만 평균/꼬리 오차는 함께 확인해야 한다.")
        lines.append("- 운영 적용은 전체 적용보다 제한적 gate 방식으로 검토하는 것이 맞다.")
    else:
        lines.append("- validation에서 선택한 유사 작가 보정이 fixed test에서는 baseline을 안정적으로 넘지 못했다.")
        lines.append("- 공격적 선택 후보는 최종 예측 보정으로 채택하지 않는다.")
    if (
        conservative_test["MAPE"] <= test_base["MAPE"]
        and conservative_test["p95_APE"] <= test_base["p95_APE"]
        and conservative_test["MdAPE"] <= test_base["MdAPE"] + 1e-12
    ):
        lines.append("- 보수적 서비스 후보는 MdAPE를 유지하면서 MAPE, p95, RMSE_log를 소폭 개선했다.")
        lines.append("- 다만 개선 폭이 작으므로 운영 채택보다는 다음 반복 검증 후보로 둔다.")
    else:
        lines.append("- 보수적 서비스 후보도 운영 채택 수준의 안정 개선은 아직 부족하다.")
    lines += [
        "",
        "## 6. Validation 상위 후보",
        "",
        *markdown_table(val_top),
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:32px;color:#1f2933;line-height:1.55}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}} th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code,pre{{background:#f3f4f6;border-radius:6px}} pre{{padding:12px;overflow:auto}}
</style></head><body>
<h1>{html.escape(EXP_ID)} Warm 유사 작가 기준가 보정 검증</h1>
<h2>Selected Candidate</h2>
<table><tr><th>source</th><th>gate</th><th>strength</th><th>cap</th></tr>
<tr><td>{html.escape(str(selected['source']))}</td><td>{html.escape(str(selected['gate']))}</td><td>{float(selected['strength']):.4f}</td><td>{float(selected['cap']):.4f}</td></tr></table>
<h2>Conservative Service Candidate</h2>
<table><tr><th>source</th><th>gate</th><th>strength</th><th>cap</th></tr>
<tr><td>{html.escape(str(conservative['source']))}</td><td>{html.escape(str(conservative['gate']))}</td><td>{float(conservative['strength']):.4f}</td><td>{float(conservative['cap']):.4f}</td></tr></table>
<h2>Fixed Test Compare</h2>{test_compare.to_html(index=False, escape=True)}
<h2>Validation Top 20</h2>{val_top.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    data = load_data()
    metrics, predictions = evaluate_candidates(data)
    selected = select_candidate(metrics)
    conservative = select_conservative_service_candidate(metrics)
    metrics.to_csv(EXP_DIR / "outputs" / "candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    pd.DataFrame([selected.to_dict()]).to_csv(EXP_DIR / "outputs" / "selected_validation_candidate.csv", index=False)
    pd.DataFrame([conservative.to_dict()]).to_csv(EXP_DIR / "outputs" / "selected_conservative_service_candidate.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "base_candidate": BASE_CANDIDATE,
        "base_prediction_path": str(BASE_PRED_PATH.relative_to(REPO)),
        "sa1_prediction_path": str(SA1_PRED_PATH.relative_to(REPO)),
        "selection_split": "validation",
        "evaluation_split": "test",
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics, selected, conservative)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_sa2_warm_similar_artist_prior_correction.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_sa2_warm_similar_artist_prior_correction.html").write_text(html_doc, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    print(f"{EXP_ID} completed: {EXP_DIR}")
    print("selected:", selected["candidate"])
    print("conservative:", conservative["candidate"])
    print(metrics[(metrics["split"].eq("test")) & metrics["candidate"].isin(["baseline_pp258_operational", selected["candidate"], conservative["candidate"]])].to_string(index=False))


if __name__ == "__main__":
    main()
