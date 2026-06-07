#!/usr/bin/env python3
"""Prepare the 2026-06-04 new artwork test set and audit current policy readiness.

This script intentionally does not pretend that the old deployable Track6
artifact is the current midterm-report winner. It separates labels from the
new operational-style input, checks Warm/Cold routing coverage, and records
whether the midterm-report candidates are directly runnable on unseen rows.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "OP-0604"
EXP_SLUG = "OP-0604_new_artworks_current_policy_readiness"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
INPUT_PATH = REPO / "data" / "test_new_artworks_test_0604.csv"
TRAIN_PATH = REPO / "data" / "track6_split" / "track6_train.csv"
ARTIFACT_MANIFEST = REPO / "data" / "track6" / "artifacts" / "track6_artifact_manifest.json"

FX_TO_KRW = {
    "KRW": 1.0,
    "USD": 1380.0,
    "EUR": 1530.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "JPY": 9.5,
}

LABEL_COLUMNS = [
    "_new_test_row_id",
    "slug",
    "title",
    "artist_name",
    "matched_train_artist",
    "sale_message",
    "price_currency",
    "price_native",
    "fx_to_krw",
    "price_krw",
    "ln_price_krw",
    "price_label_status",
    "label_parse_status",
]

MODEL_POLICY = [
    {
        "policy_area": "Warm current primary",
        "candidate": "PP-SVC3 blend_svcnum_ppv8_wsvc_0.70",
        "midterm_role": "현재 Warm 1순위",
        "intended_use": "Warm route의 주 예측가",
        "direct_runnable_status": "not_directly_runnable",
        "reason": (
            "svc_numeric_seed_mean과 pp_v8_compact_blend_mape_guarded 예측값을 70:30으로 결합한 정책이다. "
            "현재 저장소에는 기존 validation/test 예측 CSV는 있으나 신규 데이터에 바로 적용할 단일 추론 artifact가 없다."
        ),
        "action_for_0604_test": "정확한 현재 후보 평가 전 PP-SVC3 추론 artifact 재현/고정 필요",
    },
    {
        "policy_area": "Warm comparable-price component",
        "candidate": "svc_numeric_seed_mean",
        "midterm_role": "PP-SVC3의 70% 축",
        "intended_use": "유사 작품 기반 가격 피처를 Huber에 넣은 Warm 예측",
        "direct_runnable_status": "runnable_by_refit_not_frozen",
        "reason": "학습 split에서 재학습하면 만들 수 있지만, 배포용으로 고정 저장된 artifact는 아직 없다.",
        "action_for_0604_test": "운영 실험에서는 artifact화 후 사용하거나 refit 결과임을 명시",
    },
    {
        "policy_area": "Warm error-stabilization component",
        "candidate": "pp_v8_compact_blend_mape_guarded",
        "midterm_role": "PP-SVC3의 30% 축",
        "intended_use": "평균오차를 방어하는 Warm 보조 예측",
        "direct_runnable_status": "not_directly_runnable",
        "reason": "여러 이전 Warm 후보 예측 파일의 compact blend 결과이며 신규 데이터용 개별 component artifact가 없다.",
        "action_for_0604_test": "PP-V8 component chain을 재현 가능한 추론 모듈로 고정 필요",
    },
    {
        "policy_area": "Cold current reference",
        "candidate": "PP-Y18 qwidth_bin_oof_min30_cap0.25",
        "midterm_role": "Cold 참고 예측 정책",
        "intended_use": "Cold route의 참고 예측가와 넓은 가격 범위",
        "direct_runnable_status": "not_directly_runnable_as_single_artifact",
        "reason": "LightGBM Quantile 예측과 qwidth 구간 보정 결과가 실험 예측 파일 중심으로 남아 있어 단일 신규 추론 artifact는 없다.",
        "action_for_0604_test": "Cold 신규 샘플 평가 전 LightGBM Quantile + qwidth 보정 artifact 필요",
    },
    {
        "policy_area": "Legacy warm artifact",
        "candidate": "data/track6/artifacts/track6_warm_huber.joblib",
        "midterm_role": "이전 baseline",
        "intended_use": "데이터 파이프라인 smoke test 또는 비교 기준",
        "direct_runnable_status": "runnable_baseline",
        "reason": "저장된 joblib artifact는 있으나 중간 리포트의 Warm 1순위 후보가 아니다.",
        "action_for_0604_test": "필요 시 baseline으로만 별도 표기",
    },
    {
        "policy_area": "Legacy cold artifacts",
        "candidate": "track6_cold_lightgbm.joblib / track6_cold_catboost.cbm",
        "midterm_role": "이전 baseline",
        "intended_use": "Cold baseline 비교",
        "direct_runnable_status": "runnable_baseline",
        "reason": "저장된 artifact는 있으나 중간 리포트의 Cold reference 정책과는 다르다.",
        "action_for_0604_test": "필요 시 baseline으로만 별도 표기",
    },
]


def ensure_dirs() -> None:
    for subdir in ["data", "outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)


def parse_price(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    if not match:
        return np.nan
    return float(match.group(0).replace(",", ""))


def price_label_status(value: Any) -> str:
    if pd.isna(value) or not str(value).strip():
        return "missing_sale_message"
    text = str(value).strip().lower()
    if re.search(r"\d", text):
        return "explicit_price"
    if text == "sold":
        return "sold_no_price"
    if "price on request" in text:
        return "price_on_request"
    if "hold" in text:
        return "on_hold_no_price"
    if "loan" in text:
        return "on_loan_no_price"
    if "inquire" in text:
        return "inquire_no_price"
    return "non_numeric_sale_message"


def load_train_artist_keys() -> set[str]:
    train = pd.read_csv(TRAIN_PATH, usecols=["artist_key"], low_memory=False)
    return set(train["artist_key"].dropna().astype(str))


def artifact_status() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.append({
        "artifact": str(ARTIFACT_MANIFEST.relative_to(REPO)),
        "exists": ARTIFACT_MANIFEST.exists(),
        "role": "legacy artifact manifest",
    })
    if ARTIFACT_MANIFEST.exists():
        manifest = json.loads(ARTIFACT_MANIFEST.read_text(encoding="utf-8"))
        for item in manifest.get("artifacts", []):
            path = REPO / item.get("path", "")
            rows.append({
                "artifact": item.get("path", ""),
                "exists": path.exists(),
                "role": item.get("key", ""),
                "model": item.get("model", ""),
                "feature_set": item.get("feature_set", ""),
            })
    expected_prediction_sources = [
        "experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/selected_candidate_metrics.csv",
        "experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/predictions.csv",
        "experiments/track6/PP-V8_warm_deployment_simplification/outputs/predictions.csv",
        "experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/metrics.csv",
        "experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv",
    ]
    for rel in expected_prediction_sources:
        rows.append({
            "artifact": rel,
            "exists": (REPO / rel).exists(),
            "role": "experiment prediction/metric source",
        })
    return pd.DataFrame(rows)


def make_labels_and_operational_input(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw.copy()
    df.insert(0, "_new_test_row_id", np.arange(len(df), dtype=int))
    df["price_label_status"] = df["sale_message"].map(price_label_status)
    df["price_native"] = df["sale_message"].map(parse_price)
    df["fx_to_krw"] = df["price_currency"].astype(str).map(FX_TO_KRW)
    df["price_krw"] = df["price_native"] * df["fx_to_krw"]
    df["ln_price_krw"] = np.where(df["price_krw"] > 0, np.log(df["price_krw"]), np.nan)
    df["label_parse_status"] = np.where(
        df["price_native"].notna() & df["fx_to_krw"].notna() & df["ln_price_krw"].notna(),
        "parsed",
        "label_parse_failed",
    )
    labels = df[LABEL_COLUMNS].copy()
    operational = df.drop(columns=[
        "sale_message",
        "price_currency",
        "price_native",
        "fx_to_krw",
        "price_krw",
        "ln_price_krw",
        "price_label_status",
        "label_parse_status",
    ])
    return labels, operational


def route_summary(raw: pd.DataFrame, labels: pd.DataFrame, train_artist_keys: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = raw.copy()
    frame["_new_test_row_id"] = np.arange(len(frame), dtype=int)
    frame["matched_train_artist"] = frame["matched_train_artist"].fillna("").astype(str)
    frame["in_train_artist_key"] = frame["matched_train_artist"].isin(train_artist_keys)
    frame["route_by_current_match"] = np.where(frame["in_train_artist_key"], "warm", "cold")
    frame = frame.merge(labels[["_new_test_row_id", "price_label_status", "label_parse_status", "price_krw"]], on="_new_test_row_id", how="left")
    summary_rows = [
        {"metric": "total_rows", "value": int(len(frame))},
        {"metric": "label_parsed_rows", "value": int(frame["label_parse_status"].eq("parsed").sum())},
        {"metric": "warm_route_rows", "value": int(frame["route_by_current_match"].eq("warm").sum())},
        {"metric": "cold_route_rows", "value": int(frame["route_by_current_match"].eq("cold").sum())},
        {"metric": "matched_train_artist_nonempty_rows", "value": int(frame["matched_train_artist"].ne("").sum())},
        {"metric": "matched_artist_in_train_key_rows", "value": int(frame["in_train_artist_key"].sum())},
        {"metric": "median_label_price_krw", "value": float(frame["price_krw"].median())},
        {"metric": "p10_label_price_krw", "value": float(frame["price_krw"].quantile(0.10))},
        {"metric": "p90_label_price_krw", "value": float(frame["price_krw"].quantile(0.90))},
    ]
    route = pd.DataFrame(summary_rows)
    by_currency = frame.groupby("price_currency", dropna=False).size().reset_index(name="rows")
    by_currency.insert(0, "group_type", "currency")
    by_route = frame.groupby("route_by_current_match", dropna=False).size().reset_index(name="rows")
    by_route.insert(0, "group_type", "route")
    by_label_status = frame.groupby("price_label_status", dropna=False).size().reset_index(name="rows")
    by_label_status.insert(0, "group_type", "price_label_status")
    top_artists = (
        frame.groupby(["route_by_current_match", "matched_train_artist"], dropna=False)
        .size()
        .reset_index(name="rows")
        .sort_values("rows", ascending=False)
        .head(30)
    )
    top_artists.insert(0, "group_type", "top_artist")
    detail = pd.concat([by_currency, by_route, by_label_status, top_artists], ignore_index=True, sort=False)
    return route, detail


def write_report(
    labels: pd.DataFrame,
    route: pd.DataFrame,
    detail: pd.DataFrame,
    policy: pd.DataFrame,
    artifacts: pd.DataFrame,
) -> None:
    parsed_rate = labels["label_parse_status"].eq("parsed").mean()
    parsed_rows = int(labels["label_parse_status"].eq("parsed").sum())
    total_rows = int(len(labels))
    warm_rows = int(route.loc[route["metric"].eq("warm_route_rows"), "value"].iloc[0])
    cold_rows = int(route.loc[route["metric"].eq("cold_route_rows"), "value"].iloc[0])
    ready_exact = False
    lines = [
        f"# {EXP_ID} 신규 테스트 데이터 현재 정책 적용 전 점검",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 입력 파일: `{INPUT_PATH.relative_to(REPO)}`",
        "- 목적: 2026-06-04 신규 운영형 데이터를 가격 라벨과 입력 데이터로 분리하고, 중간 리포트 기준 후보를 그대로 적용할 수 있는지 확인",
        "",
        "## 1. 결론",
        "",
        "- 새 데이터는 가격 라벨을 분리한 뒤 운영 입력 형태로 평가하는 방식이 맞음",
        f"- 명시 가격 라벨 행: {parsed_rows:,}/{total_rows:,}건, 라벨 파싱 성공률: {parsed_rate:.3f}",
        "- `Sold`, `Price on request`, 빈값 등은 가격 평가 라벨로 사용할 수 없고 운영 입력 샘플로만 사용",
        f"- 현재 `matched_train_artist` 기준 라우팅: Warm {warm_rows:,}건, Cold {cold_rows:,}건",
        "- 중간 리포트의 Warm 1순위 후보를 기준으로 평가하는 것이 맞지만, 현재 저장소에는 해당 결합 후보의 신규 데이터용 단일 추론 artifact가 없음",
        "- 따라서 예전 `track6_warm_huber.joblib` 결과를 현재 Warm 1순위 결과로 보고하면 안 됨",
        "- 다음 실행은 PP-SVC3와 PP-Y18을 신규 데이터에 적용 가능한 artifact 또는 재현 스크립트로 고정한 뒤 진행하는 것이 맞음",
        "",
        "## 2. 생성 파일",
        "",
        "| 파일 | 의미 |",
        "|---|---|",
        f"| `experiments/track6/{EXP_SLUG}/data/raw_input_with_id.csv` | 원본 데이터에 내부 행 ID를 붙인 파일 |",
        f"| `experiments/track6/{EXP_SLUG}/data/operational_input.csv` | 가격 라벨 컬럼을 제거한 운영 입력용 파일 |",
        f"| `experiments/track6/{EXP_SLUG}/data/labels.csv` | 가격 평가용 라벨 파일 |",
        f"| `experiments/track6/{EXP_SLUG}/outputs/model_policy_readiness.csv` | 중간 리포트 기준 후보 실행 가능성 점검표 |",
        f"| `experiments/track6/{EXP_SLUG}/outputs/route_summary.csv` | Warm/Cold 라우팅 요약 |",
        "",
        "## 3. 라우팅/라벨 요약",
        "",
        dataframe_to_markdown(route),
        "",
        "## 4. 세부 분포",
        "",
        dataframe_to_markdown(detail),
        "",
        "## 5. 모델 정책 실행 가능성",
        "",
        dataframe_to_markdown(policy),
        "",
        "## 6. Artifact 점검",
        "",
        dataframe_to_markdown(artifacts),
        "",
        "## 7. 진행 판단",
        "",
        f"- exact_current_policy_runnable: `{str(ready_exact).lower()}`",
        "- 지금 바로 성능표를 만들려면 두 가지를 분리해야 함",
        "- 1안: 현재 중간 리포트 후보를 재현 가능한 추론 artifact로 먼저 고정한 뒤 신규 테스트 평가",
        "- 2안: 기존 artifact를 baseline smoke test로만 실행하고, 결과명에 `legacy baseline`을 명확히 표기",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:12px;margin:12px 0}}
</style></head><body>
<h1>{html.escape(EXP_ID)} 신규 테스트 데이터 현재 정책 적용 전 점검</h1>
<div class="note">중간 리포트의 현재 후보와 저장된 legacy artifact가 다르므로, 기존 artifact 결과를 현재 후보 결과로 해석하면 안 됩니다.</div>
<h2>Route Summary</h2>{route.to_html(index=False, escape=True)}
<h2>Detail Distribution</h2>{detail.to_html(index=False, escape=True)}
<h2>Model Policy Readiness</h2>{policy.to_html(index=False, escape=True)}
<h2>Artifact Status</h2>{artifacts.to_html(index=False, escape=True)}
</body></html>"""
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")


def markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = [str(col) for col in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(markdown_cell(value) for value in row) + " |")
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    raw = pd.read_csv(INPUT_PATH, low_memory=False)
    raw_with_id = raw.copy()
    raw_with_id.insert(0, "_new_test_row_id", np.arange(len(raw_with_id), dtype=int))
    labels, operational = make_labels_and_operational_input(raw)
    train_artist_keys = load_train_artist_keys()
    route, detail = route_summary(raw, labels, train_artist_keys)
    policy = pd.DataFrame(MODEL_POLICY)
    artifacts = artifact_status()

    raw_with_id.to_csv(EXP_DIR / "data" / "raw_input_with_id.csv", index=False)
    operational.to_csv(EXP_DIR / "data" / "operational_input.csv", index=False)
    labels.to_csv(EXP_DIR / "data" / "labels.csv", index=False)
    route.to_csv(EXP_DIR / "outputs" / "route_summary.csv", index=False)
    detail.to_csv(EXP_DIR / "outputs" / "route_detail_distribution.csv", index=False)
    policy.to_csv(EXP_DIR / "outputs" / "model_policy_readiness.csv", index=False)
    artifacts.to_csv(EXP_DIR / "outputs" / "artifact_status.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_path": str(INPUT_PATH.relative_to(REPO)),
        "train_path": str(TRAIN_PATH.relative_to(REPO)),
        "fx_to_krw": FX_TO_KRW,
        "decision": {
            "use_midterm_policy_as_target": True,
            "legacy_artifact_is_current_policy": False,
            "exact_current_policy_runnable_now": False,
            "reason": "PP-SVC3/PP-Y18 are experiment prediction policies, not frozen single inference artifacts.",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(labels, route, detail, policy, artifacts)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} completed\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "rows": int(len(raw)),
        "label_parsed_rows": int(labels["label_parse_status"].eq("parsed").sum()),
        "warm_route_rows": int(route.loc[route["metric"].eq("warm_route_rows"), "value"].iloc[0]),
        "cold_route_rows": int(route.loc[route["metric"].eq("cold_route_rows"), "value"].iloc[0]),
        "exact_current_policy_runnable_now": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
