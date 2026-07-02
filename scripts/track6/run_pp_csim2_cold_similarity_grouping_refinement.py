#!/usr/bin/env python3
"""PP-CSIM2: strict Cold similarity/grouping feature refinement.

Follow-up to PP-CSIM1 without routers.  This tests whether Cold accuracy can be
improved by changing the model inputs and comparable grouping logic:

- artwork nearest-neighbor reference stats with top-k grid
- market grouping ladder stats by medium/support/size
- combined nearest-neighbor + grouping stats

All train reference stats are out-of-fold. Validation/test stats use train only.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import candidate_defs, load_user_meta_frames  # noqa: E402
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    fit_quantile_bundle,
    html_table,
    json_clean,
    md_table,
)
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM2"
SLUG = "PP-CSIM2_cold_similarity_grouping_refinement"
TITLE = "Cold 유사작품/시장그룹 피처 정교화 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim2_cold_similarity_grouping_refinement_summary.md"

TOP_K_GRID = [20, 40, 80, 160]
OOF_SPLITS = 5

LADDER = [
    ("market_ref_medium_support_size", ["medium_support_bucket", "size_bucket"], 30),
    ("market_ref_medium_size", ["medium_category", "size_bucket"], 50),
    ("market_ref_support_size", ["support_category", "size_bucket"], 50),
    ("market_ref_size", ["size_bucket"], 80),
]

MARKET_REF_NUMERIC = [
    "market_ref_n",
    "market_ref_log_price_median",
    "market_ref_log_price_q25",
    "market_ref_log_price_q75",
    "market_ref_log_price_iqr",
    "market_ref_log_unit_area_median",
    "market_ref_log_unit_area_iqr",
]
MARKET_REF_FEATURES = MARKET_REF_NUMERIC + ["market_ref_level"]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def add_unit_area(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    area = np.maximum(pd.to_numeric(out.get("area_cm2", 0.0), errors="coerce").fillna(0.0).to_numpy(dtype=float), 1.0)
    out["_market_ref_log_unit_area"] = pd.to_numeric(out["ln_price_krw"], errors="coerce").to_numpy(dtype=float) - np.log(area)
    return out


def stats_table(source: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    src = add_unit_area(source)
    grouped = src.groupby(keys, dropna=False, observed=False)
    table = grouped.agg(
        market_ref_n=("ln_price_krw", "size"),
        market_ref_log_price_median=("ln_price_krw", "median"),
        market_ref_log_price_q25=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.25))),
        market_ref_log_price_q75=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.75))),
        market_ref_log_unit_area_median=("_market_ref_log_unit_area", "median"),
        market_ref_log_unit_area_q25=("_market_ref_log_unit_area", lambda x: float(np.quantile(x.astype(float), 0.25))),
        market_ref_log_unit_area_q75=("_market_ref_log_unit_area", lambda x: float(np.quantile(x.astype(float), 0.75))),
    ).reset_index()
    table["market_ref_log_price_iqr"] = table["market_ref_log_price_q75"] - table["market_ref_log_price_q25"]
    table["market_ref_log_unit_area_iqr"] = table["market_ref_log_unit_area_q75"] - table["market_ref_log_unit_area_q25"]
    return table.drop(columns=["market_ref_log_unit_area_q25", "market_ref_log_unit_area_q75"])


def global_stats(source: pd.DataFrame) -> dict[str, Any]:
    src = add_unit_area(source)
    prices = pd.to_numeric(src["ln_price_krw"], errors="coerce")
    unit = pd.to_numeric(src["_market_ref_log_unit_area"], errors="coerce")
    return {
        "market_ref_n": float(len(src)),
        "market_ref_log_price_median": float(prices.median()),
        "market_ref_log_price_q25": float(prices.quantile(0.25)),
        "market_ref_log_price_q75": float(prices.quantile(0.75)),
        "market_ref_log_price_iqr": float(prices.quantile(0.75) - prices.quantile(0.25)),
        "market_ref_log_unit_area_median": float(unit.median()),
        "market_ref_log_unit_area_iqr": float(unit.quantile(0.75) - unit.quantile(0.25)),
        "market_ref_level": "market_ref_global",
    }


def apply_market_ladder(source: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    out = target[["_track6_row_id"]].copy().reset_index(drop=True)
    remaining = pd.Series(True, index=out.index)
    target_work = target.reset_index(drop=True).copy()
    for level, keys, min_n in LADDER:
        table = stats_table(source, keys)
        table = table[pd.to_numeric(table["market_ref_n"], errors="coerce").fillna(0) >= min_n].copy()
        if table.empty:
            continue
        table["market_ref_level"] = level
        merged = target_work.loc[remaining, ["_track6_row_id", *keys]].merge(table, on=keys, how="left")
        hit = merged["market_ref_n"].notna().to_numpy()
        if hit.any():
            hit_ids = merged.loc[hit, "_track6_row_id"]
            hit_frame = merged.loc[hit, ["_track6_row_id", *MARKET_REF_FEATURES]]
            out = out.merge(hit_frame, on="_track6_row_id", how="left", suffixes=("", "_new"))
            for col in MARKET_REF_FEATURES:
                new_col = f"{col}_new"
                if new_col in out.columns:
                    out[col] = out[col].where(out[col].notna(), out[new_col])
                    out = out.drop(columns=[new_col])
            remaining &= ~target_work["_track6_row_id"].isin(hit_ids).to_numpy()
    if remaining.any():
        fallback = global_stats(source)
        for col in MARKET_REF_FEATURES:
            out.loc[remaining, col] = fallback[col]
    return out


def add_market_ladder_features(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_stats = pd.DataFrame()
    kf = KFold(n_splits=OOF_SPLITS, shuffle=True, random_state=SEED)
    pieces = []
    for ref_idx, target_idx in kf.split(train):
        stats = apply_market_ladder(train.iloc[ref_idx].copy(), train.iloc[target_idx].copy())
        pieces.append(stats)
    train_stats = pd.concat(pieces, ignore_index=True)
    val_stats = apply_market_ladder(train, val)
    test_stats = apply_market_ladder(train, test)
    return (
        train.merge(train_stats, on="_track6_row_id", how="left"),
        val.merge(val_stats, on="_track6_row_id", how="left"),
        test.merge(test_stats, on="_track6_row_id", how="left"),
    )


def prediction_rows(exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, bundle: dict[str, dict[str, np.ndarray]], policy: str, n_features: int) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "q10_log": bundle["q10"][split],
        "q90_log": bundle["q90"][split],
        "quantile_width_log": np.maximum(bundle["q90"][split] - bundle["q10"][split], 0.0),
        "policy": policy,
        "n_features": n_features,
    })


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, features: list[str], policy: str) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        "n_features": len(features),
    }


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES + ["size_bucket"])
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    for name, features in [("artwork_only", artwork_features), ("user_meta_core_bucket", core_features)]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if any(feature.startswith("search_") for feature in features):
            raise ValueError(f"{name} includes forbidden search_* feature")

    candidates: list[tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], str]] = [
        ("artwork_only", train, val, test, artwork_features, "작품 정보만"),
        ("user_meta_core_bucket", train, val, test, core_features, "작품+사용자 입력 작가 메타 bucket"),
    ]

    market_train, market_val, market_test = add_market_ladder_features(train, val, test)
    candidates.append((
        "market_group_ladder_stats",
        market_train,
        market_val,
        market_test,
        unique(core_features + MARKET_REF_FEATURES),
        "매체/지지체/크기 시장그룹 기준가격 통계 추가",
    ))

    art_ref_by_k: dict[int, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]] = {}
    for top_k in TOP_K_GRID:
        prefix = f"artwork_sim_k{top_k}"
        art_ref_by_k[top_k] = compute_reference_stats(train, val, test, ARTWORK_SIM_FEATURES, prefix=prefix, top_k=top_k)
        tr, va, te, ref_features = art_ref_by_k[top_k]
        candidates.append((
            f"artwork_similarity_k{top_k}",
            tr,
            va,
            te,
            unique(core_features + ref_features),
            f"작품 유사 비교군 top_k={top_k} 통계 추가",
        ))

    for top_k in [20, 40, 80]:
        art_tr, art_va, art_te, ref_features = art_ref_by_k[top_k]
        combo_tr = art_tr.merge(market_train[["_track6_row_id", *MARKET_REF_FEATURES]], on="_track6_row_id", how="left")
        combo_va = art_va.merge(market_val[["_track6_row_id", *MARKET_REF_FEATURES]], on="_track6_row_id", how="left")
        combo_te = art_te.merge(market_test[["_track6_row_id", *MARKET_REF_FEATURES]], on="_track6_row_id", how="left")
        candidates.append((
            f"artwork_k{top_k}_plus_market_ladder",
            combo_tr,
            combo_va,
            combo_te,
            unique(core_features + ref_features + MARKET_REF_FEATURES),
            f"작품 유사 top_k={top_k} + 시장그룹 기준가격 통계",
        ))

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for name, tr, va, te, features, policy in candidates:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if any(feature.startswith("search_") for feature in features):
            raise ValueError(f"{name} includes forbidden search_* feature")
        bundle = fit_quantile_bundle(tr, va, te, features)
        for split, frame in [("validation", va), ("test", te)]:
            pred = bundle["q50"][split]
            metric_rows.append(metric_row(name, split, frame, pred, features, policy))
            pred_frames.append(prediction_rows(EXP_ID, name, split, frame, pred, bundle, policy, len(features)))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    strict_audit = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_user_enterable_artist_meta": True,
        "uses_similarity_reference_stats": True,
        "uses_market_group_ladder_stats": True,
        "top_k_grid": TOP_K_GRID,
        "oof_splits": OOF_SPLITS,
        "router_used": False,
        "candidate_count": len(candidates),
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2), encoding="utf-8")

    cols = ["candidate", "split", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "n_features"]
    test_df = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    val_df = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    stable_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["p95_APE", "MAPE", "RMSE_log"]).iloc[0].to_dict()
    mdape_test = test_df.iloc[0].to_dict()

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {strict_audit['created_at']}",
        "- 목적: 라우터 없이 Cold 모델의 사용 피처와 유사 그룹핑 로직을 바꿔 성능 개선 가능성을 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 학습 행의 기준가격 통계는 KFold out-of-fold로 생성해 자기 가격 누수를 차단했다.",
        "- validation/test 기준가격 통계는 train 데이터만 기준으로 생성했다.",
        "",
        "## 1. Test 결과",
        md_table(test_df, cols),
        "",
        "## 2. Validation 결과",
        md_table(val_df, cols),
        "",
        "## 3. 해석",
        "",
        f"- test MdAPE 최상위 후보: `{mdape_test['candidate']}`.",
        f"- test p95/MAPE 안정성 최상위 후보: `{stable_test['candidate']}`.",
        "- 시장그룹 기준가격은 매체/지지체/크기 조합이 충분하면 그 그룹의 가격 분포를 쓰고, 부족하면 더 넓은 그룹으로 fallback한다.",
        "- 작품 유사 비교군은 top-k를 바꿔 비교군을 좁게/넓게 잡았을 때의 중앙 오차와 tail 변화를 확인한다.",
        "- `plus_market_ladder` 후보는 유사작품 통계와 사람이 설명 가능한 시장그룹 기준가격을 함께 쓰는 구조다.",
        "- 라우터는 사용하지 않았으므로, 이 결과는 후보 모델 자체의 피처/그룹핑 변경 효과로 해석한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}code{{background:#f3f4f6;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>라우터 없이 strict Cold 피처와 유사 그룹핑 구조 변경 효과를 검증했다.</p>
<h2>Test 결과</h2>{html_table(test_df, cols)}
<h2>Validation 결과</h2>{html_table(val_df, cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(strict_audit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
