"""Track 3 — Depth feature ablation 실험 코드 (공유용).

================================================================================
실험 목적
================================================================================
미술 작품 가격 예측 모델에서 '깊이(depth)' 정보가 예측 정확도에 미치는 영향을
체계적으로 측정. 총 4가지 variant를 동일 데이터/동일 평가 protocol로 비교.

  D_none  : 깊이 정보 완전 제외 (baseline)
  A_has   : has_depth (binary, 깊이 유무만)
  B_cm    : depth_cm (실수, 실제 cm 값만)
  C_both  : has_depth + depth_cm (둘 다)

================================================================================
데이터 (release_split)
================================================================================
data/release_split/
  track3_train.csv     34,629 rows  /  1,932 artists  - 학습 전용
  track3_test_warm.csv  1,685 rows  /  1,685 artists  - 학습 작가의 신규 작품
  track3_test_cold.csv  3,823 rows  /    200 artists  - 완전 unseen 작가

핵심 보장:
  - train ∩ test_cold 작가 = 0 (작가 단위 완전 분리)
  - test_warm 작가는 모두 train에 ≥1건 남아 있음 (warm 평가 가능)

================================================================================
평가 protocol
================================================================================
1. Cold-start: test_cold (3,823건, 완전 신규 작가)
   - 모델: LAD (Quantile Regression q=0.5) — outlier-robust median regression
   - 작가 ID는 feature로 안 씀 (unseen이라 의미 없음)

2. Warm-start: test_warm (1,685건, 학습된 작가의 신규 작품)
   - 모델: Tuned LightGBM (PR1 단계에서 Optuna로 튜닝된 hyperparam)
   - 작가 ID(artist_name_ko) categorical feature로 사용

3. Leakage 방지:
   - train 데이터만 보고 fit (test 절대 보지 않음)
   - artist_works_log (작가별 작품 수)는 train 집계로만 계산
   - Categorical vocabulary, scaler 등 모든 transform fit은 train으로

================================================================================
사용법
================================================================================
$ python3 track3_depth_ablation.py

전제조건:
  - Python 3.10+
  - pip install pandas numpy scikit-learn lightgbm
  - data/release_split/ 디렉토리에 3개 CSV 파일 존재

출력:
  콘솔: variant별 metric 표 + breakdown
  data/track3_pr15_depth_results.json: 전체 결과 저장

================================================================================
결과 해석 가이드
================================================================================
주요 metric:
  median APE: 중간값 |예측-실제|/실제 (작을수록 좋음, 핵심 지표)
  W30 (Within-30%): 예측이 실제±30% 안에 들어간 비율 (클수록 좋음)
  MAPE: 평균 |예측-실제|/실제 (outlier에 민감)

해석 포인트:
  1. Overall (test_cold + test_warm) — variant별 일반 성능
  2. has_depth=1 (3D) vs has_depth=0 (2D) — 깊이 feature가
     2D 작품 예측에 부작용을 일으키는지 확인 (회화 작품 보호)
  3. medium별 breakdown — 어떤 매체에서 깊이가 가장 도움/방해되는지

================================================================================
"""
from __future__ import annotations

# ─────────── 표준 라이브러리 ───────────
import json
import logging
from pathlib import Path

# ─────────── 외부 라이브러리 ───────────
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import QuantileRegressor   # Cold model (LAD)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# 로깅 — 단계별 진행 상황 표시
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────────────────────────────────────
# 이 파일에서 부모 디렉토리 2단계 위가 repo root여야 함.
# (구조: REPO/data/share/track3_depth_ablation.py)
REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"           # 분리된 데이터셋 위치
OUT_PATH = REPO / "data" / "track3_pr15_depth_results.json"  # 결과 저장 경로

# ──────────────────────────────────────────────────────────────────────────────
# 학습/평가 상수
# ──────────────────────────────────────────────────────────────────────────────
ARTIST_COL = "artist_name_ko"          # 작가 ID 컬럼 (한글명)
TARGET = "ln_price_krw_unified"        # 예측 target (자연로그 변환된 가격)
PRICE_COL = "price_krw_unified"        # 평가 시 사용할 원본 KRW 가격
SEED = 42                              # 재현성을 위한 random seed

# ──────────────────────────────────────────────────────────────────────────────
# Feature 정의 — 4가지 variant 공통 BASE
# ──────────────────────────────────────────────────────────────────────────────
# 깊이와 무관한 공통 feature 집합:
#   medium_category   — 매체 (oil, acrylic, watercolor 등) [categorical]
#   support_category  — 지지대 (canvas, paper, panel 등) [categorical]
#   log_area          — log(width × height) [실수, 작품 크기 robust scale]
#   estimated_ko_ho   — 추정 호수 (한국 미술시장 표준 크기 단위)
#   orientation       — 방향 (landscape/portrait/square) [categorical]
#   medium_ho_bucket  — medium × ho_bucket 교호작용 [categorical, derive]
#   artist_works_log  — log(1 + 학습 데이터에서 작가의 작품 수) [실수]
#   aspect_ratio      — log(width/height) [실수]
BASE_NO_DEPTH = [
    "medium_category", "support_category",
    "log_area", "estimated_ho", "orientation",
    "medium_ho_bucket", "artist_works_log", "aspect_ratio"
]
# OneHot encoding 대상 categorical 컬럼
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

# ──────────────────────────────────────────────────────────────────────────────
# 비교할 4가지 variant
# ──────────────────────────────────────────────────────────────────────────────
# 각 variant의 feature 구성 = BASE_NO_DEPTH + variants[name]
# 즉 BASE에 어떤 depth 관련 feature를 추가/제외하는지를 정의.
VARIANTS = {
    "D_none":  [],                        # baseline: 깊이 정보 완전 제외
    "A_has":   ["has_depth"],             # binary (0/1): 깊이 정보 유무
    "B_cm":    ["depth_cm"],              # 실수: 실제 cm 값 (없으면 0)
    "C_both":  ["has_depth", "depth_cm"], # 둘 다 사용
}


# ──────────────────────────────────────────────────────────────────────────────
# Feature engineering — train_counts를 인자로 받아 leakage 방지
# ──────────────────────────────────────────────────────────────────────────────
def make_features(df: pd.DataFrame, train_counts: dict) -> pd.DataFrame:
    """Raw 데이터 → engineered feature 생성.

    중요한 leakage 방지 설계:
      `artist_works_log`는 반드시 train으로 미리 계산한 train_counts dict를
      받아서 적용. test에서 직접 집계하면 leakage 발생.

    Args:
        df: 원본 데이터 (raw columns)
        train_counts: train 작가별 작품 수 dict (train만 보고 만들어진 것)

    Returns:
        feature column이 추가된 DataFrame.
    """
    df = df.copy()

    # ho_bucket: estimated_ho(추정 호수)를 4단계로 binning.
    # 미술시장에서 0-5호(소품), 5-20호(중품), 20-50호(대형), 50호+(특대)
    # 가격 분포가 비선형이라 bucket으로 묶는 게 회귀에 유리.
    df["ho_bucket"] = pd.cut(
        df["estimated_ho"],
        bins=[-0.1, 5, 20, 50, 200],
        labels=["0-5", "5-20", "20-50", "50+"]
    ).astype(str)

    # medium × ho_bucket 교호작용. 매체와 크기 조합의 가격 패턴 학습.
    # 예: oil_5-20 (소형 유화), sculpture_50+ (대형 조각)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]

    # aspect_ratio: log 변환된 가로/세로 비율.
    # log를 쓰면 가로/세로 대칭 (예: 16:9와 9:16이 -log 부호만 반대로 같은 크기)
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))

    # artist_works_log: train 집계만 사용. test 데이터로 fit하면 leakage.
    # 작가 작품수의 분포가 매우 skewed(많이 가진 작가 vs 1건뿐)이라 log1p로 압축.
    # train에 없는 작가(test_cold의 unseen 작가)는 0 → log1p(0)=0이 됨.
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))

    return df


# ──────────────────────────────────────────────────────────────────────────────
# Cold model 빌더 — LAD (Quantile Regression q=0.5, alpha=0)
# ──────────────────────────────────────────────────────────────────────────────
def build_cold_lad(features: list, cat_cols: list) -> Pipeline:
    """Cold-start용 LAD 모델 Pipeline 생성.

    선정 이유:
      - LAD (median regression)은 outlier에 robust
      - Cold-start는 작가 정보 없음 → 강한 baseline model 필요
      - Quantile q=0.5는 median을 예측 (RMSE 대신 MAE 최소화)
      - alpha=0 → regularization 없음 (작은 feature set이라 overfit risk 낮음)

    Args:
        features: 사용할 feature 컬럼 list
        cat_cols: features 중 categorical 컬럼 list (OneHot encode 대상)

    Returns:
        sklearn Pipeline (preprocess + LAD)
    """
    cat = [c for c in features if c in cat_cols]      # categorical features
    num = [c for c in features if c not in cat_cols]  # numeric features

    # ColumnTransformer로 categorical은 OneHot, numeric은 StandardScale.
    # max_categories=100: 카테고리 폭주 방지 (희귀 값은 "infrequent"로 묶음).
    # drop="first": 첫 카테고리 dummy 제거로 다중공선성 회피.
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first",
                              max_categories=100), cat),
        ("num", StandardScaler(), num),
    ])

    return Pipeline([
        ("prep", preprocess),
        ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0)),
    ])


# ──────────────────────────────────────────────────────────────────────────────
# Warm model — Tuned LightGBM (PR1 Optuna 튜닝 결과)
# ──────────────────────────────────────────────────────────────────────────────
def to_cat(df: pd.DataFrame, features: list, cat_cols: list) -> pd.DataFrame:
    """LightGBM에 넣기 전 categorical 컬럼을 pandas Categorical로 변환.

    LGB는 pd.Categorical을 자동으로 categorical_feature로 인식하므로
    OneHot encode 없이 그대로 학습 가능 (성능 + 메모리 효율).
    """
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def train_warm_lgb(df_train: pd.DataFrame, features: list, cat_cols: list,
                   train_counts: dict) -> lgb.Booster:
    """Warm-start용 Tuned LightGBM 학습.

    Hyperparam 출처: PR1 v1 cycle Optuna 튜닝 (15 trials, single-fold).
      learning_rate    = 0.04   (느린 learning + 많은 trees)
      num_leaves       = 198    (leaf-wise, 깊은 트리)
      min_data_in_leaf = 75     (overfit 방지)
      feature_fraction = 0.987  (거의 모든 feature 사용)
      bagging_fraction = 0.978
      reg_alpha        = 0.36   (L1)
      reg_lambda       = 4.75   (L2 강함)
      early_stopping   = 30 rounds

    Validation:
      train의 10%를 holdout으로 early stopping 모니터링.
      재현성을 위해 SEED=42로 permutation.
    """
    df_feat = make_features(df_train, train_counts)

    # train을 90/10 split (재현성 보장)
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(df_feat))
    cut = int(len(df_feat) * 0.1)
    va_idx = perm[:cut]  # holdout 10%
    tr_idx = perm[cut:]  # 학습 90%

    X_tr = to_cat(df_feat.iloc[tr_idx], features, cat_cols)
    X_va = to_cat(df_feat.iloc[va_idx], features, cat_cols)
    y_tr = df_feat.iloc[tr_idx][TARGET].values
    y_va = df_feat.iloc[va_idx][TARGET].values

    params = {
        "objective": "regression", "metric": "rmse",
        "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
        "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
        "reg_alpha": 0.36, "reg_lambda": 4.75,
        "verbose": -1, "seed": SEED,
    }

    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_cols)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=cat_cols, reference=tr_set)

    return lgb.train(
        params, tr_set,
        num_boost_round=2000,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(30, verbose=False)],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Metric 계산
# ──────────────────────────────────────────────────────────────────────────────
def compute_metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
    """예측 vs 실제 비교. 모든 입력/출력은 log(price) scale.

    내부에서 exp()로 원본 KRW scale로 복원해 % 기반 metric을 계산.

    Returns dict:
      n             : 샘플 수
      median_ape    : median |pred-true|/true (핵심 metric, outlier robust)
      mape          : mean |pred-true|/true (outlier 민감)
      rmse_log      : sqrt(mean((pred_ln - true_ln)²)) (log scale RMSE)
      within_30pct  : 예측이 실제±30% 안에 들어간 비율
    """
    y_true = np.exp(y_true_ln)   # ln(price) → KRW
    y_pred = np.exp(y_pred_ln)

    # APE (Absolute Percentage Error)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln  # log-scale 잔차

    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 단일 variant 실행 — 학습 → 예측 → metric 계산 → breakdown
# ──────────────────────────────────────────────────────────────────────────────
def run_variant(name: str, depth_feats: list,
                train_df: pd.DataFrame,
                test_warm_df: pd.DataFrame,
                test_cold_df: pd.DataFrame,
                train_counts: dict) -> tuple[dict, np.ndarray, np.ndarray]:
    """한 variant에 대해 Cold/Warm 모두 학습하고 평가.

    Args:
        name: variant 이름 (D_none, A_has, B_cm, C_both)
        depth_feats: BASE에 추가할 depth feature list
        train_df: 학습 데이터 (release_split/track3_train.csv)
        test_warm_df: warm 평가 데이터
        test_cold_df: cold 평가 데이터
        train_counts: train 작가별 작품 수 dict

    Returns:
        result: 전체 metric + breakdown 결과 dict
        cold_pred: test_cold에 대한 예측 (ln scale)
        warm_pred: test_warm에 대한 예측 (ln scale)
    """
    # 이 variant의 최종 feature list
    cold_feats = BASE_NO_DEPTH + depth_feats
    warm_feats = cold_feats + [ARTIST_COL]           # Warm은 작가 ID 추가
    warm_cat = BASE_CAT + [ARTIST_COL]                # Warm categorical에도 추가

    logger.info(f"\n[{name}] features = BASE + {depth_feats}")

    # ── Cold model 학습 ──
    tr_feat = make_features(train_df, train_counts)
    cold_model = build_cold_lad(cold_feats, BASE_CAT)
    cold_model.fit(tr_feat[cold_feats], tr_feat[TARGET].values)

    # ── Warm model 학습 ──
    warm_model = train_warm_lgb(train_df, warm_feats, warm_cat, train_counts)

    # ── test_cold 예측 (Cold LAD) ──
    cold_feat = make_features(test_cold_df, train_counts)
    cold_pred = cold_model.predict(cold_feat[cold_feats])

    # ── test_warm 예측 (Warm LGB) ──
    warm_feat = make_features(test_warm_df, train_counts)
    X_warm = to_cat(warm_feat, warm_feats, warm_cat)
    warm_pred = warm_model.predict(X_warm)

    # ── Metric 결과 dict 구성 ──
    result = {
        "variant": name,
        "depth_feats": depth_feats,
        "cold_features_count": len(cold_feats),
        "warm_features_count": len(warm_feats),
        "test_cold": compute_metrics(test_cold_df[TARGET].values, cold_pred),
        "test_warm": compute_metrics(test_warm_df[TARGET].values, warm_pred),
    }

    # ── has_depth=1 (3D) vs has_depth=0 (2D) 분해 ──
    # 깊이 feature가 어느 subset에 도움/부작용 주는지 식별
    for label, mask in [
        ("test_cold_3d (has_depth=1)", test_cold_df["has_depth"] == 1),
        ("test_cold_2d (has_depth=0)", test_cold_df["has_depth"] == 0),
    ]:
        if mask.sum() > 0:
            result[label] = compute_metrics(
                test_cold_df.loc[mask, TARGET].values, cold_pred[mask.values])

    for label, mask in [
        ("test_warm_3d (has_depth=1)", test_warm_df["has_depth"] == 1),
        ("test_warm_2d (has_depth=0)", test_warm_df["has_depth"] == 0),
    ]:
        if mask.sum() > 0:
            result[label] = compute_metrics(
                test_warm_df.loc[mask, TARGET].values, warm_pred[mask.values])

    # ── medium별 breakdown (test_cold) ──
    # 매체별로 어디서 깊이가 가장 영향 있는지 확인 (회화 vs 조각/설치)
    # 최소 20건 이상인 medium만 통계적으로 의미 있다고 보고 reporting.
    medium_brk = {}
    for med in test_cold_df["medium_category"].unique():
        mask = (test_cold_df["medium_category"] == med).values
        if mask.sum() >= 20:
            medium_brk[str(med)] = compute_metrics(
                test_cold_df[TARGET].values[mask], cold_pred[mask])
    result["test_cold_by_medium"] = medium_brk

    return result, cold_pred, warm_pred


# ──────────────────────────────────────────────────────────────────────────────
# 전체 실험 orchestrator
# ──────────────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 70)
    logger.info("Track 3 — Depth feature ablation (release_split)")
    logger.info("=" * 70)

    # ── 데이터 로드 ──
    train_df = pd.read_csv(SPLIT / "track3_train.csv")
    test_warm_df = pd.read_csv(SPLIT / "track3_test_warm.csv")
    test_cold_df = pd.read_csv(SPLIT / "track3_test_cold.csv")
    logger.info(f"train {len(train_df):,} / test_warm {len(test_warm_df):,} "
                f"/ test_cold {len(test_cold_df):,}")

    # has_depth=1 (3D 가능 작품) 비중 — 데이터 sanity check
    for name, d in [("train", train_df),
                    ("test_warm", test_warm_df),
                    ("test_cold", test_cold_df)]:
        pct = 100 * (d["has_depth"] == 1).mean()
        logger.info(f"  {name}: has_depth=1 비중 {pct:.1f}%")

    # ── train 작가 작품수 사전 계산 (leakage 방지) ──
    # 이 dict는 모든 feature engineering에 재사용됨.
    train_counts = train_df[ARTIST_COL].value_counts().to_dict()

    # ── 4 variant 순차 실행 ──
    results = {}
    cold_preds = {}
    warm_preds = {}
    for name, depth_feats in VARIANTS.items():
        r, cp, wp = run_variant(name, depth_feats,
                                train_df, test_warm_df, test_cold_df,
                                train_counts)
        results[name] = r
        cold_preds[name] = cp
        warm_preds[name] = wp

    # ── 결과 출력: Overall metric ──
    print()
    print("=" * 90)
    print("📊 Depth feature ablation 결과 (Cold LAD + Warm Tuned LGB)")
    print("=" * 90)
    print()
    print(f"{'Variant':<12} {'Cold med_APE':>13} {'Cold W30':>10} "
          f"{'Warm med_APE':>13} {'Warm W30':>10}")
    print("-" * 70)
    for name in VARIANTS:
        r = results[name]
        c = r["test_cold"]; w = r["test_warm"]
        print(f"{name:<12} {c['median_ape']:>13.4f} {c['within_30pct']:>10.4f} "
              f"{w['median_ape']:>13.4f} {w['within_30pct']:>10.4f}")

    # ── Δ vs baseline (D_none) ──
    print()
    print("=" * 90)
    print("Δ vs D_none (깊이 무관 baseline) — 음수일수록 개선")
    print("=" * 90)
    base_c = results["D_none"]["test_cold"]["median_ape"]
    base_w = results["D_none"]["test_warm"]["median_ape"]
    print(f"{'Variant':<12} {'ΔCold':>10} {'ΔWarm':>10}")
    for name in ["A_has", "B_cm", "C_both"]:
        dc = results[name]["test_cold"]["median_ape"] - base_c
        dw = results[name]["test_warm"]["median_ape"] - base_w
        print(f"{name:<12} {dc:>+10.4f} {dw:>+10.4f}")

    # ── 3D vs 2D subset 분해 ──
    print()
    print("=" * 90)
    print("3D (has_depth=1) vs 2D (has_depth=0) subset 분해")
    print("=" * 90)
    print(f"{'Variant':<12} {'Cold3D':>10} {'Cold2D':>10} {'Warm3D':>10} {'Warm2D':>10}")
    for name in VARIANTS:
        r = results[name]
        c3 = r.get("test_cold_3d (has_depth=1)", {}).get("median_ape", float('nan'))
        c2 = r.get("test_cold_2d (has_depth=0)", {}).get("median_ape", float('nan'))
        w3 = r.get("test_warm_3d (has_depth=1)", {}).get("median_ape", float('nan'))
        w2 = r.get("test_warm_2d (has_depth=0)", {}).get("median_ape", float('nan'))
        print(f"{name:<12} {c3:>10.4f} {c2:>10.4f} {w3:>10.4f} {w2:>10.4f}")

    # ── medium별 cold breakdown ──
    print()
    print("=" * 90)
    print("test_cold per-medium (med_APE) — variant 차이")
    print("=" * 90)
    media_set = set()
    for name in VARIANTS:
        media_set.update(results[name]["test_cold_by_medium"].keys())
    media_sorted = sorted(media_set)
    header = f"{'Medium':<12}" + "".join([f"{name:>10}" for name in VARIANTS])
    print(header)
    for med in media_sorted:
        row = f"{med:<12}"
        for name in VARIANTS:
            v = results[name]["test_cold_by_medium"].get(med, {}).get("median_ape")
            row += f"{v:>10.4f}" if v is not None else f"{'':>10}"
        print(row)

    # ── 결과 JSON 저장 ──
    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
