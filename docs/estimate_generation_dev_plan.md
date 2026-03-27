# 추정가 생성 엔진 — 개발 실행 계획서 v7.0

> **기반 문서**: `estimate_generation_plan.md` v8.0 (Codex 7회 리뷰 통과)
> **선행 문서**: `development_plan.md` v2.1 (Phase 1-2 개발 실행 계획서)
> **개발 주체**: Claude (직접 구현)
> **작성일**: 2026-03-27
> **Codex 리뷰**: 1회차 MAJOR → v2.0, 2회차 MAJOR → v3.0, 3회차 반영 → v4.0

---

## 0. 착수 전 준비

### 0.1 의존성 추가 (pyproject.toml) — Phase 3 전용

```toml
[project.optional-dependencies]
# Phase 3: 추정가 생성 엔진
estimate-engine = [
    "pandas>=2.1",
    "pyarrow>=14.0",
    "scikit-learn>=1.3",
    "catboost>=1.2",
    "numpy>=1.24",
]

# Phase 3 Sprint 3: 기존 엔진 재학습
estimate-engine-retrain = [
    "catboost>=1.2",
]
```

설치 명령:
```bash
pip install -e ".[price-engine-core,estimate-engine]"           # Sprint 0 착수 시
pip install -e ".[price-engine-core,estimate-engine,estimate-engine-retrain]"  # Sprint 3
```

### 0.2 디렉토리 구조

```
src/visionai/price_engine/
├── estimate_generator/               # Phase 3 신규 모듈
│   ├── __init__.py
│   ├── hedonic_features.py          # 추정가-독립 23개 피처 빌더
│   ├── quantile_model.py            # Model-A: CatBoost MultiQuantile
│   ├── estimate_model.py            # Model-B: CatBoost RMSE (추정가 재현)
│   ├── quantile_calibrator.py       # Prediction Interval calibration (additive shift)
│   ├── estimate_calibrator.py       # 세그먼트별 smearing + ratio 보정
│   ├── market_rounder.py            # 호 단위 라운딩 (Model-B 전용)
│   ├── cold_start.py                # 3-tier 계층적 fallback + Bayesian shrinkage
│   ├── selection_bias.py            # 유찰 selection bias 보정 (구간 확장)
│   └── generator.py                 # Model-A + Model-B 통합 파이프라인
├── features/
│   └── hedonic_stats.py             # 신규: artist_median, trend, unsold_rate 등 8개 피처
├── models/
│   └── target_transform_v2.py       # 기존 엔진 재학습 버전 (OOF 생성 추정가 기반)

tests/price_engine/
├── test_hedonic_features.py         # 23개 피처 생성 검증
├── test_quantile_model.py           # Model-A 학습/추론 검증
├── test_estimate_model.py           # Model-B 학습/추론 검증
├── test_quantile_calibrator.py      # coverage 보정 검증
├── test_estimate_calibrator.py      # smearing + ratio 검증
├── test_market_rounder.py           # 라운딩 로직 검증
├── test_cold_start_estimate.py      # 3-tier fallback + shrinkage 검증
├── test_selection_bias.py           # 구간 확장 로직 검증
├── test_estimate_generator.py       # 통합 테스트
├── test_estimate_leakage.py         # 8개 누수 방지 규칙 테스트
└── test_oof_pipeline.py             # OOF 생성 추정가 분포 정렬 검증

scripts/
├── train_estimate_models.py         # Model-A + Model-B 학습 실행
├── validate_estimate_models.py      # 개별 + 통합 평가 실행
├── calibrate_models.py              # Quantile + Segment calibration 실행
├── retrain_price_engine_v2.py       # 기존 엔진 OOF 재학습
└── check_estimate_gate.py           # 12개 게이트 자동 판정
```

### 0.3 Phase 1-2 코드 통합 지점

Phase 3은 기존 코드를 **재사용**하면서 추정가 의존성을 해소한다:

| Phase 1-2 모듈 | 재사용 방법 | Phase 3 연동 |
|---------------|-----------|-------------|
| `preprocessing/dimension_parser.py` | 그대로 사용 | `hedonic_features.py`에서 import |
| `preprocessing/medium_parser.py` | 그대로 사용 | `hedonic_features.py`에서 import |
| `preprocessing/year_parser.py` | 그대로 사용 | `hedonic_features.py`에서 import |
| `features/splits.py` | 4-way 분할로 **확장** | `splits.py`에 Calib 블록 추가 |
| `features/artist_stats_snapshot.py` | 그대로 사용 | `hedonic_stats.py`에서 import (strict cutoff 로직 동일) |
| `features/cold_start.py` | 3-tier로 **확장** | `estimate_generator/cold_start.py` 신규 구현 |
| `models/trainer.py` | CatBoost 학습 로직 참조 | `quantile_model.py`, `estimate_model.py` 신규 |
| `models/predictor.py` | 추론 로직 참조 | `generator.py`에서 통합 |
| `validation/metrics.py` | MAPE, R² 재사용 | Pinball Loss, Interval Score **추가** |
| `validation/calibration.py` | grade별 coverage 참조 | `quantile_calibrator.py` 신규 |
| `validation/bias_check.py` | 편향 검증 재사용 | `estimate_calibrator.py` 연동 |

### 0.4 착수 전 리스크 대응 준비

기획서 7장 리스크 12건 → 실행 태스크 매핑:

| # | 리스크 (기획서 7장) | 실행 태스크 | 소유 Sprint | 상태 |
|---|--------|-------------------|------------|------|
| 1 | 추정가 없이 R² 하락 | `hedonic_features.py`에 신규 8개 피처 구현 | Sprint 0 | 🟡 Active |
| 2 | 목적함수 불일치 (C1) | Model-A/B 분리 구현 | Sprint 1 | ✅ 설계 해소 |
| 3 | Covariate shift (C3) | OOF 재학습 v2 + PSI 검증 | Sprint 3 | 🟡 Active |
| 4 | Smearing 오용 (C2) | Model-A: smearing 없음, Model-B만 적용 코드 분리 | Sprint 2 | ✅ 설계 해소 |
| 5 | Cold Start fallback (C4) | 3-tier fallback + Bayesian shrinkage 구현 | Sprint 0 | 🟡 Active |
| 6 | 분위수 교차 (M5) | MultiQuantile + isotonic rearrangement fallback | Sprint 1 | ✅ 설계 해소 |
| 7 | 시계열 누수 (M6) | 8개 규칙 단위 테스트 | Sprint 0 + 전체 | 🟡 Active |
| 8 | 한국 시장 과소 반영 (M7) | size_ho, size_ho_above40, unsold_rate 피처 | Sprint 0 | ✅ 설계 해소 |
| 9 | 평가 지표 혼합 (M8) | A/B/C 그룹 분리 구현 | Sprint 1 | ✅ 설계 해소 |
| 10 | 호 라운딩 범위 왜곡 (m11) | Model-B low/mid/high 모두 라운딩 | Sprint 2 | ✅ 설계 해소 |
| 11 | 일정 리스크 (m13) | 12일 일정 + Sprint별 게이트 | 전체 | 🟡 Active |
| 12 | 유찰 selection bias | unsold_rate 피처 + 구간 1.3배 확장 + G11 게이트 | Sprint 0 + 2 | 🟡 Active |

> **상태 범례:** ✅ 설계 해소 = 기획서 리뷰에서 설계적으로 닫힘, 구현으로 확정. 🟡 Active = 구현 시 검증 필요.

### 0.5 데이터 분할 전략 (4-way)

기존 Phase 1-2의 3-way(Train/Valid/Test)를 **4-way로 확장**:

```
Train     : 초기 ~ 회차 N-3  (모델 학습)
Calib     : 회차 N-2         (후처리 파라미터 학습: smearing, ratio, quantile calibration)
Validation: 회차 N-1         (성능 평가 — 후처리 학습에 사용하지 않음)
Test      : 회차 N           (최종 검증)
```

**핵심 원칙:**
- 후처리 파라미터는 **Calib**에서만 학습하고, **Validation**에서 평가
- Test 평가 시: 모델은 Train+Calib로 재학습, 후처리는 **Validation(Calib_final)**에서 학습
- Test set 정보는 어떤 경로에서도 후처리 파라미터에 유입되지 않음

**평가 경로별 후처리 학습 위치:**

| 평가 경로 | 모델 학습 범위 | 후처리 학습 블록 | 평가 대상 |
|----------|--------------|----------------|----------|
| Validation 평가 | Train | **Calib** | Validation |
| Test 평가 | Train + Calib | **Validation** (Calib_final) | Test |

**게이트 판정 프로토콜 (Codex 1회차 MINOR 대응):**

| 단계 | Split | 용도 | 자동화 |
|------|-------|------|--------|
| 1. 개발 판단 | Validation | Sprint 완료 조건 확인, 하이퍼파라미터 조정 근거 | `validate_estimate_models.py --split=valid` |
| 2. 최종 게이트 | Test | 12개 게이트 공식 판정 (1회만 실행) | `check_estimate_gate.py --split=test` |
| 3. 보고 | Test | 게이트 결과 → 문서화 | 자동 생성 리포트 |

> **원칙:** Validation 결과로 코드를 수정한 후, Test는 **단 1회만** 실행한다. Test를 반복 실행하면 implicit overfitting이 발생한다.

---

## 1. Sprint 0: 피처 엔지니어링 (3일)

### 1.1 작업 목록

| # | 모듈 | 파일 | 내용 | 입력 → 출력 | 기획서 |
|---|------|------|------|------------|--------|
| 0-1a | features | `splits.py` 확장 | 4-way 분할 (Train/Calib/Valid/Test) 추가. 기존 3-way 함수는 하위 호환 유지 | auction_type별 회차 범위 → 4개 블록 인덱스 | 6.3 |
| 0-1b | features | `dataset_builder.py` 수정 | 4-way split 라벨 지원. `split_mode="3way"` (기존) / `"4way"` (Phase 3) 파라미터 추가 | split 컬럼에 "calib" 라벨 포함 | 6.3 |
| 0-1c | api | `server.py` 확인 | Phase 3 API는 별도 엔드포인트 추가 방식. 기존 `/api/v1/predict_price`는 변경 없음 | 하위 호환 보장 | — |
| 0-1d | validation | `calibration.py` 수정 | 4-way split의 Calib 블록을 calibration 학습 소스로 인식. 기존 3-way 경로도 유지 | — | — |
| 0-2 | features | `hedonic_stats.py` | 신규 8개 피처 산출 (strict cutoff) | works DataFrame + cutoff → 8개 피처 | 3.4 |
| 0-3 | estimate_generator | `hedonic_features.py` | 23개 피처 빌더 (추정가 4개 제거 + 신규 8개 추가) | CSV + 파서 + 스냅샷 → 23개 피처 parquet | 3.4 |
| 0-4 | estimate_generator | `cold_start.py` | 3-tier 계층적 fallback + Bayesian shrinkage (log-price) | artist_id + cutoff → tier별 fallback 값 | 2.5 |
| 0-5 | estimate_generator | `market_rounder.py` | 호 단위 라운딩 함수 (6단계 가격대별) | price(float) → rounded_price(int) | 3.6 |
| 0-6 | tests | `test_hedonic_features.py` | 23개 피처 생성 + 기존 15개 유지 검증 | — | 3.4 |
| 0-7 | tests | `test_cold_start_estimate.py` | 3-tier fallback 검증 + Bayesian shrinkage + min_count | — | 2.5 |
| 0-8 | tests | `test_market_rounder.py` | 6단계 라운딩 + 경계값 테스트 | — | 3.6 |
| 0-9 | tests | `test_estimate_leakage.py` | 8개 누수 방지 규칙 단위 테스트 | — | 6.3 |
| 0-10 | features | `hedonic_stats.py` 내 `parse_edition()` | 에디션 regex 파싱 시도: `(\d+)/(\d+)` 패턴 | 제목 문자열 → has_edition(bool) | 2.3 |

> **에디션 파싱 실험 (기획서 2.3절 대응):**
> Sprint 0에서 `(\d+)/(\d+)` regex 패턴으로 에디션 파싱을 시도한다.
> - 파싱 성공률 ≥ 80%: `has_edition` 이진 피처 추가 (23개 → **24개**)
> - 파싱 성공률 < 80%: 피처 제외, 23개 유지
> - 판단 기준: 판화/사진 카테고리 작품 중 에디션 파싱 성공률

### 1.2 파일 상세 명세

#### `features/hedonic_stats.py`

**목적**: 추정가 없이 작품 가치를 설명하는 신규 8개 피처 산출

**함수:**

```python
def compute_artist_median_price(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """strict < cutoff 작가별 낙찰가 중앙값. 거래 < 3건: Bayesian shrinkage (m=10)."""

def compute_artist_price_trend(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """최근 5회차 vs 이전 평균 변화율. 거래 < 5건: NaN."""

def compute_medium_avg_price(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """strict < cutoff 매체별 평균 낙찰가. 그룹 < 30건: 전체 평균으로 shrinkage."""

def compute_size_ho(surface_area: pd.Series) -> pd.Series:
    """surface_area → 호수 변환 (1호 ≈ 132cm²). 시간 독립."""

def compute_size_ho_above40(size_ho: pd.Series) -> pd.Series:
    """max(0, size_ho - 40): 40호 변곡점 반영 hinge 피처. 시간 독립."""

def compute_auction_type_factor(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """strict < cutoff 경매유형별 평균 낙찰가 비율. 그룹 < 30건: shrinkage."""

def compute_artist_unsold_rate(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """strict < cutoff 작가별 유찰률. 출품 < 3건: NaN."""

def compute_medium_x_auction_avg(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """strict < cutoff 매체×경매유형 교차그룹 평균 ln(낙찰가). Cold Start Tier 1 prior."""

def compute_group_unsold_rate(works: pd.DataFrame, cutoff: int) -> pd.Series:
    """strict < cutoff 매체×경매유형 그룹별 유찰률.
    selection_bias.py의 adjust_for_selection_bias()에서 group_unsold_rate로 사용.
    그룹 내 출품 < 10건이면 auction_type 전체 유찰률로 fallback."""

def parse_edition(title: str) -> bool | None:
    """제목에서 에디션 regex 파싱: (\\d+)/(\\d+) 패턴.
    성공률 ≥ 80% 시 has_edition 피처로 채택, 미달 시 제외.
    Returns: True(에디션 있음), False(에디션 없음), None(파싱 불가)."""
```

**Sparse-history 안정화 규칙:**
- `artist_price_trend`: 거래 < 5건 → NaN
- `artist_unsold_rate`: 출품 < 3건 → NaN
- `artist_median_price`, `artist_avg_price`, `artist_max_price`: 거래 < 3건 → Bayesian shrinkage (log-price, m=10)
- `auction_type_factor`, `medium_avg_price`, `medium_x_auction_avg`: 그룹 < 30건 → 전체 평균으로 shrinkage

#### `estimate_generator/hedonic_features.py`

**목적**: 23개 피처 빌더 — 기존 파서 + artist_stats_snapshot + hedonic_stats 통합

**함수:**

```python
def build_hedonic_features(
    raw_df: pd.DataFrame,
    cutoff: int,
    auction_type: str,
) -> pd.DataFrame:
    """추정가 제외 23개 피처 조립.

    유지 피처 15개: artist_clean, artist_avg_price, artist_max_price,
        artist_total_sold, is_new_artist, height_cm, width_cm,
        surface_area, aspect_ratio, is_size_imputed, medium_category,
        support_category, is_3d, 회차, is_untitled

    신규 피처 8개: artist_median_price, artist_price_trend,
        medium_avg_price, size_ho, size_ho_above40,
        auction_type_factor, artist_unsold_rate, medium_x_auction_avg

    Returns: DataFrame with 23 columns + target columns
    """
```

#### `estimate_generator/cold_start.py`

**목적**: 3-tier 계층적 fallback + Bayesian shrinkage (log-price 스케일)

**함수:**

```python
def compute_bayesian_shrinkage(
    group_mean_ln: float, global_mean_ln: float, n: int, m: int = 10
) -> float:
    """Bayesian shrinkage: (n × group_mean_ln + m × global_mean_ln) / (n + m)"""

def get_cold_start_fallback(
    medium_category: str, auction_type: str,
    works: pd.DataFrame, cutoff: int,
) -> dict:
    """3-tier fallback:
    Tier 1: medium_category × auction_type (min_count ≥ 30) + shrinkage
    Tier 2: medium_category (min_count ≥ 50) + shrinkage
    Tier 3: auction_type (항상 가용) — 전체 ln(price) 평균

    Returns: {tier: int, fallback_ln_price: float, group_size: int}
    """

def compute_cold_start_features(
    works: pd.DataFrame, cutoff: int
) -> pd.DataFrame:
    """전체 데이터에 대해 Cold Start 관련 피처 일괄 산출.
    is_new_artist, medium_x_auction_avg 포함."""

def assign_confidence_grade(
    artist_total_sold: int,
    is_new_artist: bool,
    cold_start_tier: int,
    artist_unsold_rate: float | None,
    group_unsold_rate: float | None,
) -> str:
    """Cold Start 포함 신뢰도 등급 결정 규칙.

    **기존 코드 통합 (Codex 2회차 MAJOR 대응):**
    Phase 1-2의 `validation/confidence_grade.py`의 `assign_grade()` 함수를 **대체하지 않음**.
    - Phase 1-2 경로: 기존 `assign_grade()` 유지 (estimate_mid 기반, sold≥20 + est 30M~1B 기준)
    - Phase 3 경로: 본 함수 사용 (cold_start_tier + unsold_rate 기반, 추정가 없이 동작)
    - generator.py에서 시나리오에 따라 적절한 등급 함수 호출:
      - 추정가 있는 경우 (시나리오 B/C): Phase 1-2 등급 함수 사용 가능
      - 추정가 없는 경우 (시나리오 A/D): 본 함수 사용
    - 두 함수 모두 'A'/'B'/'C'/'D' 문자열 반환, 동일 인터페이스

    등급 기준:
    - **A등급**: artist_total_sold ≥ 20 AND cold_start_tier == 0 (충분한 이력)
    - **B등급**: 5 ≤ artist_total_sold < 20 (중간 이력)
    - **C등급**: 1 ≤ artist_total_sold < 5 (희소 이력)
              OR artist_unsold_rate > 50% OR group_unsold_rate > 40%
              (selection bias 보정 대상)
    - **D등급**: is_new_artist == True (거래 0건)
              OR cold_start_tier ≥ 2 (Tier 2/3 fallback 사용)

    D등급 추가 규칙:
    - D등급 작가는 예측값에 '참고용' 라벨 부여
    - 위클리 경매 + D등급: 별도 slice 분석 대상
    - MdAPE > 100% 하위그룹: '예측 불가' 처리 (Sprint 4 리포트에서 결정)

    Returns: 'A' | 'B' | 'C' | 'D'
    """
```

#### `estimate_generator/market_rounder.py`

**목적**: K-Auction 추정가 관행 라운딩 — Model-B 출력 전용

**함수:**

```python
def round_to_market_unit(price: float) -> int:
    """6단계 가격대별 라운딩:
    < 100만: 10만 단위
    100~500만: 50만 단위
    500~1000만: 100만 단위
    1000~5000만: 500만 단위
    5000만~1억: 1000만 단위
    1억 이상: 5000만 단위
    """
```

### 1.3 테스트 명세

#### `test_hedonic_features.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_feature_count | 출력 DataFrame 컬럼 수 | 23개 |
| test_no_estimate_features | estimate_mid/range/ratio/ln_estimate_mid 미포함 | 4개 피처 부재 확인 |
| test_existing_features_preserved | 기존 15개 피처 값 동일 | Phase 1 출력과 비교 |
| test_new_features_not_null | 신규 8개 피처 생성 여부 | NaN 허용 범위 내 |
| test_strict_cutoff | artist 통계가 cutoff 이전 데이터만 사용 | 미래 데이터 미포함 |
| test_sparse_history_rules | 거래 < 3건 작가 shrinkage, < 5건 trend NaN | 안정화 규칙 적용 |
| test_size_ho_conversion | surface_area → 호수 변환 | 132cm² = 1호 |
| test_size_ho_above40 | 40호 hinge 피처 | 30호 → 0, 50호 → 10 |

#### `test_cold_start_estimate.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_tier1_fallback | medium × auction_type 그룹 ≥ 30건 | Tier 1 발동, shrinkage 적용 |
| test_tier2_fallback | Tier 1 미달 → medium 그룹 ≥ 50건 | Tier 2 발동 |
| test_tier3_fallback | Tier 1, 2 미달 → auction_type 전체 평균 | Tier 3 발동 |
| test_bayesian_shrinkage | shrinkage 공식 검증 (log-price 스케일) | (n×x̄ + m×μ₀)/(n+m) 일치 |
| test_new_artist_flag | 거래 0건 작가 is_new_artist=True | 100% 생성 보장 |
| test_min_count_tier1 | Tier 1 그룹 크기 < 30 → Tier 2로 fallback | 정확한 tier 전환 |
| test_min_count_tier2 | Tier 2 그룹 크기 < 50 → Tier 3로 fallback | 정확한 tier 전환 |

#### `test_market_rounder.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_under_1m | < 100만 가격 | 10만 단위 라운딩 |
| test_1m_to_5m | 100~500만 | 50만 단위 라운딩 |
| test_5m_to_10m | 500~1000만 | 100만 단위 라운딩 |
| test_10m_to_50m | 1000~5000만 | 500만 단위 라운딩 |
| test_50m_to_100m | 5000만~1억 | 1000만 단위 라운딩 |
| test_over_100m | 1억 이상 | 5000만 단위 라운딩 |
| test_boundary_values | 경계값 (100만, 500만 등) | 올바른 구간 선택 |

#### `test_estimate_leakage.py` — 8개 누수 방지 규칙

| 규칙 | 테스트 | 검증 |
|------|--------|------|
| 피처 규칙 1 | test_artist_stats_strict_cutoff | 작가 통계가 strict < cutoff만 사용 |
| 피처 규칙 2 | test_no_same_round_leak | 동일 회차 내 타 lot 정보 미혼입 |
| 피처 규칙 3 | test_no_test_target_in_train | Test set 낙찰가/추정가가 Train에 미유입 |
| 피처 규칙 4 | test_model_b_target_evaluation_only | Model-B 추정가 타깃은 평가에만 사용 |
| 후처리 규칙 5 | test_smearing_from_calib_only | smearing_factor가 Calib에서만 산출 |
| 후처리 규칙 6 | test_ratio_from_calib_only | segment_ratios가 Calib에서만 산출 |
| 후처리 규칙 7 | test_quantile_calib_from_calib_only | quantile calibration이 Calib에서만 산출 |
| 후처리 규칙 8 | test_oof_no_self_prediction | OOF 추정가: 학습 데이터에 자기 예측 미포함 |

### 1.4 Sprint 0 완료 조건

```
□ 23개 피처 빌더 구현 (15 유지 + 8 신규)
□ 추정가 4개 피처 제거 확인
□ 4-way 분할 구현 (Train/Calib/Valid/Test)
□ 3-tier Cold Start fallback 구현 + Bayesian shrinkage (log-price)
□ 호 단위 라운딩 구현 (6단계)
□ Sparse-history 안정화 규칙 적용
□ 8개 누수 방지 규칙 단위 테스트 전체 통과
□ Cold Start fallback 그룹 크기 검증 (Tier 1 ≥ 30, Tier 2 ≥ 50)
□ data/hedonic_features.parquet 생성 (23개 피처)
□ ruff check + mypy 통과
□ 전체 테스트 통과 (pytest)
```

### 1.5 병렬화 가능 작업

```
병렬 가능:
  0-1(splits 확장) | 0-5(market_rounder)           ← 서로 독립
  0-6(test_hedonic) | 0-7(test_cold_start) | 0-8(test_rounder) ← 테스트 독립

순차 필수:
  0-1(splits) → 0-2(hedonic_stats) → 0-3(hedonic_features)
  0-2(hedonic_stats) → 0-4(cold_start)
  모든 모듈 → 0-9(leakage test)
```

---

## 2. Sprint 1: Model-A + Model-B 학습 + 개별 평가 (3일)

### 2.1 작업 목록

| # | 모듈 | 파일 | 내용 | 기획서 |
|---|------|------|------|--------|
| 1-1 | estimate_generator | `quantile_model.py` | Model-A: CatBoost MultiQuantile (τ=0.25,0.50,0.75) | 3.2 |
| 1-2 | estimate_generator | `estimate_model.py` | Model-B: CatBoost RMSE (ln(추정가 중앙) 타깃) | 3.3 |
| 1-3 | validation | `metrics.py` 확장 | Pinball Loss, Interval Score, Coverage Rate, Range Width 추가 | 5.1 |
| 1-4 | estimate_generator | `selection_bias.py` | 저유동성 작가 구간 확장 (1.3배) + 신뢰도 하향 | 7장 #12 |
| 1-5 | tests | `test_quantile_model.py` | Model-A 학습/추론 + monotonicity 검증 | — |
| 1-6 | tests | `test_estimate_model.py` | Model-B 학습/추론 + smearing 없음 확인 | — |
| 1-7 | tests | `test_selection_bias.py` | 구간 확장 로직 + 등급 하향 검증 | — |
| 1-8 | scripts | `train_estimate_models.py` | Model-A + Model-B 학습 실행 스크립트 | — |

### 2.2 파일 상세 명세

#### `estimate_generator/quantile_model.py`

**목적**: CatBoost MultiQuantile (τ=0.25, 0.50, 0.75) 학습/추론

**함수:**

```python
class HedonicQuantileModel:
    """Model-A: 낙찰가 분위수 예측 (추정가 없이).

    타깃: y = ln(낙찰가)
    손실: MultiQuantile:alpha=0.25,0.5,0.75
    역변환: exp() 직접 역변환 (smearing 없음)
    """

    def __init__(self, iterations=2000, depth=8, learning_rate=0.05): ...

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series,
            cat_features: list[int], eval_set=None) -> None:
        """CatBoost MultiQuantile 학습. early_stopping_rounds=100."""

    def predict_raw(self, X: pd.DataFrame) -> np.ndarray:
        """Raw quantile 예측 (log scale). shape: (n, 3) = [q25, q50, q75]."""

    def predict(self, X: pd.DataFrame) -> dict:
        """exp 역변환된 가격 예측.
        Returns: {price_low, price_mid, price_high} (연속값, 라운딩 없음)
        """

    def check_monotonicity(self, predictions: np.ndarray) -> float:
        """q25 ≤ q50 ≤ q75 만족 비율 반환. MultiQuantile 미지원 시 isotonic 적용."""
```

#### `estimate_generator/estimate_model.py`

**목적**: CatBoost RMSE로 전문가 추정가 중앙값 재현

**함수:**

```python
class EstimateRegressorModel:
    """Model-B: 전문가 추정가 재현.

    타깃: y = ln(추정가 중앙) = ln((추정가_최저 + 추정가_최고) / 2)
    손실: RMSE
    역변환: exp(ŷ) × smearing_factor (세그먼트별 Duan smearing)
    """

    def __init__(self, iterations=2000, depth=8, learning_rate=0.05): ...

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series,
            cat_features: list[int], eval_set=None) -> None:
        """CatBoost RMSE 학습."""

    def predict_raw(self, X: pd.DataFrame) -> np.ndarray:
        """Raw 예측 (log scale). shape: (n,)."""

    def predict(self, X: pd.DataFrame, smearing_factor: float = 1.0) -> np.ndarray:
        """exp 역변환 + smearing 적용된 추정가 중앙값."""
```

#### `estimate_generator/selection_bias.py`

**목적**: 유찰 selection bias 보정 — 저유동성 작가 구간 확장

**함수:**

```python
def adjust_for_selection_bias(
    price_low: float, price_mid: float, price_high: float,
    artist_unsold_rate: float, group_unsold_rate: float,
    confidence_grade: str,
) -> tuple[float, float, float, str]:
    """저유동성 작가(unsold_rate > 50% or group_unsold_rate > 40%):
    - 예측 구간 1.3배 확장
    - 신뢰도 C등급 이하로 하향

    Returns: (adjusted_low, adjusted_mid, adjusted_high, adjusted_grade)
    """
```

### 2.3 Model-A 평가 지표

| # | 지표 | 구현 위치 | 정의 |
|---|------|----------|------|
| A1 | Pinball Loss (주 지표) | `metrics.py` | Σᵢ ρ_τ(yᵢ - q̂_τ,ᵢ), τ별 합산. **Raw quantile 기준** |
| A2 | Interval Score | `metrics.py` | IS = (q̂₇₅ - q̂₂₅) + (2/α)(q̂₂₅ - y)⁺ + (2/α)(y - q̂₇₅)⁺. **Calibrated 기준** |
| A3 | Coverage Rate | `metrics.py` | P(q̂₂₅ ≤ y ≤ q̂₇₅). **Calibrated 기준** |
| A4 | Hedonic R² (보조) | `metrics.py` | q50 예측의 R² |
| A5 | Range Width | `metrics.py` | (exp(q̂₇₅) - exp(q̂₂₅)) / exp(q̂₅₀). **Calibrated 기준** |
| A6 | Quantile Calibration | `metrics.py` | 실제 coverage ≈ 이론적 coverage. **Raw quantile 기준** |

### 2.4 Model-B 평가 지표

| # | 지표 | 구현 위치 | 정의 |
|---|------|----------|------|
| B1 | Estimate MAPE | `metrics.py` | \|생성 중앙 - 실제 추정가 중앙\| / 실제 추정가 중앙 |
| B2 | Estimate Bias | `metrics.py` | median(생성 / 실제) 가격대별 |
| B3 | 통합 MAPE | `metrics.py` | 생성 추정가 → v2 엔진 → 최종 낙찰가 MAPE (Sprint 3) |

### 2.5 Sprint 1 완료 조건

```
□ Model-A (MultiQuantile) 학습 완료
□ Model-B (RMSE) 학습 완료
□ Monotonicity: q25 ≤ q50 ≤ q75 100% (MultiQuantile or isotonic)
□ Model-A Raw Pinball Loss 산출
□ Model-A Raw Quantile Calibration 확인 (각 τ별 실제 coverage ≈ 이론적 coverage)
□ Model-B Estimate MAPE 산출
□ Hedonic R² (q50) ≥ 0.65 (게이트 G3)
□ Selection bias 보정 로직 구현
□ Feature importance 보고 (size_ho_above40 기여도 확인)
□ 모델 파일 저장: model_a_v{날짜}.cbm, model_b_v{날짜}.cbm
□ 전체 테스트 통과
```

---

## 3. Sprint 2: Calibration + 라운딩 + Cold Start 보고 (2일)

### 3.1 작업 목록

| # | 모듈 | 파일 | 내용 | 기획서 |
|---|------|------|------|--------|
| 2-1 | estimate_generator | `quantile_calibrator.py` | Prediction Interval calibration (additive shift) | 3.2.1 |
| 2-2 | estimate_generator | `estimate_calibrator.py` | 세그먼트별 smearing + ratio 보정 | 3.3 |
| 2-3 | tests | `test_quantile_calibrator.py` | coverage 보정 전/후 비교 | — |
| 2-4 | tests | `test_estimate_calibrator.py` | smearing factor + ratio 검증 | — |
| 2-5 | scripts | `calibrate_models.py` | Calib set 기반 보정 실행 | — |

### 3.2 파일 상세 명세

#### `estimate_generator/quantile_calibrator.py`

**목적**: Calib set에서 additive shift를 학습하여 목표 coverage(≥ 55%) 달성

**함수:**

```python
class QuantileCalibrator:
    """Prediction Interval calibration.

    Raw Quantile → Calibrated Prediction Interval:
    - 보정 하한 = q̂₀.₂₅ + Δ_low
    - 보정 상한 = q̂₀.₇₅ + Δ_high
    - 보정 중앙 = q̂₀.₅₀ + Δ_mid
    """

    def fit(self, y_calib: np.ndarray, q_pred_calib: np.ndarray,
            target_coverage: float = 0.55) -> None:
        """Calib set에서 Δ_low, Δ_high, Δ_mid 산출.

        1. τ별 잔차: r = y - q̂_τ(X)
        2. 목표 coverage 달성하도록 α_low, α_high grid search
        3. Δ_low = quantile(r₀.₂₅, α_low)
        4. Δ_high = quantile(r₀.₇₅, α_high)
        5. Δ_mid = median(r₀.₅₀)
        """

    def transform(self, q_pred: np.ndarray) -> np.ndarray:
        """Raw quantile에 additive shift 적용.
        Returns: calibrated prediction interval (n, 3)."""

    def validate_coverage(self, y_valid: np.ndarray,
                          q_pred_valid: np.ndarray) -> dict:
        """Validation set에서 calibrated coverage 검증.
        Returns: {coverage_overall, coverage_major, coverage_weekly, ...}"""
```

#### `estimate_generator/estimate_calibrator.py`

**목적**: Model-B의 세그먼트별 smearing factor + ratio 산출 (Calib set 기반)

**함수:**

```python
class EstimateCalibrator:
    """세그먼트별 Duan smearing + 추정가 범위 ratio 보정.

    Adaptive quantile bin (5-quantile):
    S1(<Q20), S2(Q20~Q40), S3(Q40~Q60), S4(Q60~Q80), S5(≥Q80)
    """

    def fit(self, y_calib: np.ndarray, y_pred_calib: np.ndarray,
            est_low_actual: np.ndarray, est_mid_actual: np.ndarray,
            est_high_actual: np.ndarray) -> None:
        """Calib set에서 세그먼트별 파라미터 산출:
        1. Adaptive quantile bin 경계 설정 (Calib set 분위수)
        2. smearing_factor(s) = (1/nₛ) × Σᵢ∈s exp(êᵢ) (ê = y - ŷ)
        3. ratio_low(s) = median(est_low / est_mid) per segment
        4. ratio_high(s) = median(est_high / est_mid) per segment
        5. Fallback: nₛ < 30이면 인접 bin 병합
        """

    def transform(self, y_pred_raw: np.ndarray) -> dict:
        """Raw 예측에 smearing + ratio 적용.
        Returns: {est_low, est_mid, est_high} (라운딩 전)
        """

    def validate_stability(self) -> dict:
        """세그먼트별 smearing factor의 bootstrap 95% CI.
        CI 폭 ±0.1 이내 확인."""
```

### 3.3 테스트 명세

#### `test_quantile_calibrator.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_coverage_improvement | 보정 후 coverage ≥ 55% (Calib set) | 목표 달성 |
| test_coverage_on_validation | Validation set에서도 coverage ≥ 55% | 일반화 확인 |
| test_major_coverage | 메이저 slice coverage ≥ 58% (G2) | 게이트 충족 |
| test_delta_finite | Δ_low, Δ_high, Δ_mid가 유한값 | NaN/Inf 없음 |
| test_monotonicity_preserved | 보정 후에도 low ≤ mid ≤ high | 100% |

#### `test_estimate_calibrator.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_segment_bin_balance | 각 bin에 ~20% 데이터 | nₛ ≈ N/5 |
| test_smearing_factor_positive | 모든 세그먼트 smearing > 0 | 양수 보장 |
| test_smearing_bootstrap_ci | bootstrap 95% CI 폭 ≤ ±0.1 | 안정성 |
| test_ratio_range | ratio_low < 1.0, ratio_high > 1.0 | 합리적 범위 |
| test_small_bin_merge | nₛ < 30이면 인접 bin 병합 | fallback 동작 |
| test_segment_boundary_cv | Fold별 세그먼트 경계 변동률 CV < 0.2 | 안정성 |

### 3.4 Sprint 2 완료 조건

```
□ Quantile Calibration 완료: coverage ≥ 55% (전체), ≥ 58% (메이저) (G1, G2)
□ Validation에서 calibrated coverage 유효성 검증 통과
□ Segment Calibration 완료: 5-quantile bin, smearing factor 산출
□ smearing factor bootstrap CI ≤ ±0.1
□ Segment boundary CV < 0.2
□ Model-B 추정가 생성: low/mid/high + 호 단위 라운딩 적용
□ Estimate MAPE < 35% (전체, G5), < 25% (메이저, G6)
□ Range Width: 0.3 ≤ median ≤ 1.2 (G4)
□ Cold Start MAPE < 60% (G9)
□ 저유동성 작가 slice MAPE < 50% (G11)
□ Monotonicity: low ≤ mid ≤ high 100% (G12)
□ Selection bias 구간 확장 (unsold_rate > 50%) 확인
□ 전체 테스트 통과
```

---

## 4. Sprint 3: 기존 엔진 재학습(v2) + OOF 파이프라인 (2일)

### 4.1 작업 목록

| # | 모듈 | 파일 | 내용 | 기획서 |
|---|------|------|------|--------|
| 3-1 | models | `target_transform_v2.py` | 기존 엔진 재학습 (OOF 생성 추정가 기반) | 4.2 |
| 3-2 | estimate_generator | `generator.py` | Model-A + Model-B 통합 파이프라인 | 3.5 |
| 3-3 | tests | `test_oof_pipeline.py` | OOF 생성 추정가 분포 정렬 검증 | 4.2.1 |
| 3-4 | tests | `test_estimate_generator.py` | 통합 파이프라인 E2E 테스트 | — |
| 3-5 | scripts | `retrain_price_engine_v2.py` | OOF 재학습 실행 | — |

### 4.2 파일 상세 명세

#### `models/target_transform_v2.py`

**목적**: OOF 생성 추정가로 기존 가격 예측 엔진 재학습

**함수:**

```python
class PriceEngineV2:
    """기존 Target Transform CatBoost의 v2 버전.

    변경: 전문가 추정가 → OOF 생성 추정가로 대체
    유지: 동일한 Target Transform 방식

    **v2 피처 스키마 (22개 — 현행 BASELINE_FEATURES 기준):**
    현행 predictor.py의 BASELINE_FEATURES는 22개(artist_sell_rate=0 고정 포함).
    v2에서도 동일한 22개 피처 순서를 유지하되, 추정가 4개를 OOF 생성값으로 치환:
    - artist_clean, medium_category, support_category, 타입, is_3d, is_untitled
    - ln_estimate_mid ← ln(est_mid_oof)
    - estimate_ratio ← est_high_oof / est_low_oof
    - estimate_range ← est_high_oof - est_low_oof
    - height_cm, width_cm, surface_area, aspect_ratio, is_size_imputed
    - artist_avg_price, artist_max_price, artist_total_sold
    - Lot, 회차, is_year_missing, is_new_artist, artist_sell_rate(=0 고정)
    """

    def generate_oof_estimates(
        self, data: pd.DataFrame, n_folds: int = 5,
    ) -> pd.DataFrame:
        """Expanding-Window K-Fold OOF 추정가 생성.

        각 Fold k:
        1. Train_B_k로 Model-B_k 학습
        2. Calib_B_k에서 fold-local 후처리 파라미터 산출
           (smearing_factor_k, ratio_low_k, ratio_high_k)
        3. Predict 구간에 Model-B_k + fold-local 후처리 적용
        4. round_to_market_unit(est_low, est_mid, est_high)

        Returns: DataFrame with est_low_oof, est_mid_oof, est_high_oof
        """

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series,
            oof_estimates: pd.DataFrame) -> None:
        """OOF 추정가 기반 v2 학습.

        피처 치환 (22개 중 4개 → OOF 값):
        - ln_estimate_mid = ln(est_mid_oof)
        - estimate_range = est_high_oof - est_low_oof
        - estimate_ratio = est_high_oof / est_low_oof  (est_low_oof=0 시 NaN)
        - estimate_mid = est_mid_oof  (내부 계산용)
        + 나머지 18개: 현행 BASELINE_FEATURES 순서 그대로 (artist_sell_rate=0 고정 포함)

        타깃: ln(낙찰가 / est_mid_oof)
        """

    def predict(self, X: pd.DataFrame, est_mid: np.ndarray) -> np.ndarray:
        """v2 추론: est_mid × exp(model.predict(X))"""
```

#### `estimate_generator/generator.py`

**목적**: Model-A + Model-B + Calibration + Rounding 통합

**함수:**

```python
class EstimateGenerator:
    """추정가 생성 엔진 통합 파이프라인.

    시나리오 A: 독립 가치 평가 (추정가 없는 경우) → Model-A
    시나리오 B: 추정가 검증 (추정가 있는 경우) → Model-B vs K-Auction
    시나리오 C: 기존 엔진 연동 → Model-B → v2
    시나리오 D: 사전 가치 평가 → Model-A
    """

    def __init__(self, model_a, model_b,
                 quantile_calibrator, estimate_calibrator,
                 price_engine_v2=None): ...

    def generate(self, X: pd.DataFrame, works_hist: pd.DataFrame = None) -> dict:
        """전체 생성 파이프라인.

        Args:
            X: 23개 모델 피처 DataFrame
            works_hist: 과거 거래 데이터 (group_unsold_rate 계산용, 캐시 가능)

        Returns: {
            'price_range': (low, mid, high),      # Model-A: 연속값
            'estimate': (est_low, est_mid, est_high),  # Model-B: 라운딩됨
            'confidence_grade': str,              # A/B/C/D
            'cold_start_tier': int,               # 0/1/2/3
            'metadata': {
                'group_unsold_rate': float | None,  # selection bias 보정용
                'artist_unsold_rate': float | None,
                'selection_bias_applied': bool,
                'interval_expansion_factor': float,  # 1.0 또는 1.3
            }
        }

        group_unsold_rate 경로:
        1. works_hist에서 compute_group_unsold_rate() 호출 (hedonic_stats.py)
        2. confidence_grade 판정에 사용 (C등급: group_unsold_rate > 40%)
        3. selection_bias.py에서 구간 확장 여부 결정
        4. metadata로 반환 (모델 피처 아님, inference metadata)
        서빙 시: works_hist는 주기적으로 캐시 갱신 (월 1회 재학습 시점)
        """

    def validate_estimate(self, X: pd.DataFrame,
                          kauction_estimate: float) -> dict:
        """시나리오 B: AI 추정가 vs K-Auction 추정가 비교.
        세그먼트별 차등 경고 기준:
        - 메이저 + 고가(>3000만): 괴리율 > 20%
        - 프리미엄: 괴리율 > 30%
        - 위클리 + 저가(<500만): 괴리율 > 40%
        """
```

### 4.3 OOF 절차 상세

```
Step 0. Warm-up prefix 정의 (earliest session 처리)
   - 전체 회차의 첫 20%를 warm-up prefix로 지정
   - Warm-up prefix의 역할:
     (a) Model-B 학습 시: 학습 데이터에 **포함** (Expanding Window의 초기 Train 구간)
     (b) OOF 추정가 생성: warm-up 구간에 대해서는 OOF 추정가를 **생성하지 않음**
     (c) v2 엔진 학습: warm-up 구간은 **완전 제외** (OOF 추정가가 없으므로)
   - 정리: Model-B 학습에는 사용하되, v2 학습 데이터에서는 제외
   - 데이터 감소(~20%)에 의한 성능 하락은 Validation에서 모니터링
   - 예: 전체 100회차 → 회차 1~20은 warm-up, 회차 21~ 부터 OOF 생성

   **Warm-up 검증 테스트 (test_oof_pipeline.py에 추가):**
   - warm-up 비중 민감도: 10% / 20% / 30%에서 **Validation** MAPE 비교 (Test 사용 금지)
   - warm-up vs post-warm-up PSI: OOF 구간 추정가 분포 vs 서빙 시 추정가 분포 < 0.1
   - v2 학습 데이터에 warm-up 구간 미포함 확인 (leakage 테스트)

Step 1. Expanding-Window 5-Fold (OOF 대상: warm-up 이후 구간만)
   Fold 1: Train_B=[회차 1~N1],     Calib_B=[N1+1~N2],   Predict=[N2+1~N3]
   Fold 2: Train_B=[회차 1~N3],     Calib_B=[N3+1~N4],   Predict=[N4+1~N5]
   ...
   ※ Train_B에는 warm-up 구간(회차 1~W)이 **포함**됨 (Model-B 학습용)
   ※ Predict 구간은 반드시 회차 W+1 이후부터 시작 (warm-up에는 OOF 미생성)

Step 2. 각 Fold k:
   a. Train_B_k → Model-B_k 학습 (RMSE, ln(추정가 중앙))
   b. Calib_B_k → fold-local 후처리:
      - smearing_factor_k(segment)
      - ratio_low_k(segment), ratio_high_k(segment)
   c. Predict → Model-B_k + fold-local 후처리:
      - est_mid = exp(ŷ) × smearing_factor_k
      - est_low = est_mid × ratio_low_k
      - est_high = est_mid × ratio_high_k
      - round_to_market_unit(all)

Step 3. OOF 추정가 할당 (warm-up **제외** 구간에만)
   - warm-up 구간(회차 1~W): OOF 추정가 없음 → v2 학습에서 제외
   - post-warm-up 구간(회차 W+1~): 각 Fold의 Predict에서 생성한 OOF 추정가 할당

Step 4. v2 학습 (post-warm-up 구간만 사용)
   - 입력: OOF 추정가가 있는 행만 사용 (warm-up 행 제외)
   - 기존 엔진 구조 유지, 추정가만 OOF로 대체

Step 5. Validation/Test 평가 (4-way 분할과 일관된 경로):

   === Validation 평가 경로 ===
   a. Model-B_full: Train으로 학습
   b. 후처리 파라미터: Calib에서만 산출 (smearing_factor, ratio_low/high, segment 경계)
   c. Model-B_full + Calib 후처리 → Validation에 적용하여 성능 평가
   d. Validation 결과로 게이트 판단 및 모델 선택

   === Test 평가 경로 (게이트 통과 후) ===
   e. Model-B_final: Train + Calib로 재학습 (Validation/Test 미포함)
   f. Calib_final = Validation: 후처리 파라미터 재산출
      - smearing_factor_final(segment)
      - ratio_low_final(segment), ratio_high_final(segment)
   g. Model-B_final + Calib_final 후처리 → Test에 적용하여 최종 성능 평가
   h. Test set 정보는 어떤 경로에서도 후처리 파라미터에 유입되지 않음

   > **핵심:** Validation은 성능 평가에만 사용한다. Model-B_final의 Test 경로에서
   > Calib_final로 Validation 데이터를 사용하는 것은 모델 학습에 Validation을
   > 포함하지 않기 때문에 정보 누수가 아니다. 이 구조는 시계열 expanding window의 표준 관행이다.
```

### 4.4 테스트 명세

#### `test_oof_pipeline.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_oof_no_self_prediction | 각 샘플이 자기 모델에서 예측되지 않음 | 100% |
| test_oof_distribution_psi | OOF 추정가 vs 실제 추정가 PSI | < 0.1 |
| test_oof_segment_median | 세그먼트별 median(OOF/실제) | 합리적 범위 |
| test_fold_smearing_cv | Fold별 smearing_factor 변동 CV | < 0.15 |
| test_v2_feature_structure | v2가 기존 22개 피처 구조(BASELINE_FEATURES) 유지 | 동일 구조 (추정가 4개 OOF 치환, artist_sell_rate=0 고정 포함) |
| test_v2_target_transform | v2 타깃 = ln(낙찰가/est_mid_oof) | 올바른 변환 |

#### `test_estimate_generator.py`

| 테스트 | 검증 내용 | 기대 결과 |
|--------|----------|----------|
| test_e2e_pipeline | 입력 → 출력 전체 흐름 | 에러 없이 완료 |
| test_model_a_no_rounding | Model-A 출력이 연속값 | 라운딩 미적용 |
| test_model_b_rounded | Model-B 출력이 라운딩됨 | 시장 단위 |
| test_cold_start_generation | 거래 0건 작가도 예측 가능 | 100% 생성 |
| test_confidence_grade | 등급 산정 정확성 | A/B/C/D |
| test_validate_estimate | 괴리율 경고 기준 (세그먼트별) | 차등 기준 |

### 4.5 Sprint 3 완료 조건

```
□ OOF 생성 추정가 파이프라인 구현 (Expanding-Window 5-Fold)
□ OOF 분포 정렬: PSI < 0.1
□ Fold별 smearing_factor CV < 0.15
□ 기존 엔진 v2 재학습 완료
□ 통합 MAPE < 32% (G7)
□ 통합 파이프라인 (generator.py) 구현
□ 4개 시나리오 (A/B/C/D) 동작 검증
□ 전체 테스트 통과
```

---

## 5. Sprint 4: API 확장 + 최종 검증 + 게이트 판정 + 문서화 (2일)

### 5.1 작업 목록

| # | 모듈 | 파일 | 내용 | 기획서 |
|---|------|------|------|--------|
| 4-1 | scripts | `validate_estimate_models.py` | 전체 지표 일괄 평가 | 5.1 |
| 4-2 | scripts | `check_estimate_gate.py` | 12개 게이트 자동 판정 | 5.2 |
| 4-3 | reporting | Cold Start / D등급 리포트 | Tier별 MAPE + fallback 발동률 + 위클리 slice | 2.5 |
| 4-4 | reporting | Feature importance 리포트 | 23개(+1) 피처 기여도 + ablation | 3.4 |
| 4-5 | reporting | Champion 비교 | Model-A q50 vs v2 재학습 MAPE 비교 | 4.2 |
| 4-6 | api | `server.py` 확장 | 추정가 생성 엔드포인트 추가 | 6.1 |
| 4-7 | api | `schemas.py` 확장 | EstimateRequest/Response 스키마 추가 | 6.1 |
| 4-8 | tests | `test_estimate_api.py` | API 엔드포인트 통합 테스트 | — |

### 5.1.1 API 확장 상세

기존 `src/visionai/price_engine/api/server.py`와 `schemas.py`에 추정가 생성 엔드포인트를 추가한다.

**`schemas.py` 확장:**
```python
class EstimateRequest(BaseModel):
    """추정가 생성 요청 스키마."""
    artist_name: str
    medium: str
    height_cm: float
    width_cm: float
    year: int | None = None
    auction_type: str  # "위클리" | "프리미엄" | "메이저" (현행 AuctionType Enum과 동일)

class EstimateResponse(BaseModel):
    """추정가 생성 응답 스키마."""
    # Model-A: 독립 가치 평가 (연속값)
    price_range: dict  # {low, mid, high}
    # Model-B: 추정가 재현 (라운딩됨)
    estimate: dict  # {low, mid, high}
    confidence_grade: str  # A/B/C/D
    cold_start_tier: int | None
    warnings: list[str]  # 괴리율 경고 등
```

**`server.py` 확장:**
```python
@app.post("/api/v1/estimate", response_model=EstimateResponse)
async def generate_estimate(req: EstimateRequest) -> EstimateResponse:
    """추정가 생성 API — Model-A + Model-B 통합 파이프라인."""

@app.post("/api/v1/estimate/validate")
async def validate_estimate(req: EstimateValidateRequest) -> dict:
    """추정가 검증 API — AI 추정가 vs K-Auction 추정가 비교.
    시나리오 B: 세그먼트별 차등 경고 기준 적용."""
```

**기존 API 공존 전략 (Codex 2회차 MAJOR 대응):**
- 기존 `/api/v1/predict_price` 엔드포인트는 **변경 없이 유지** (Phase 1-2, estimate_low/high 필수)
- 새로운 `/api/v1/estimate` 엔드포인트 추가 (Phase 3 전용, 추정가 없이 동작)
- **v2 모드는 별도 엔드포인트로 분리** (기존 스키마를 수정하지 않음):

```python
# 신규 스키마 명세
class EstimateRequest(BaseModel):
    """추정가 생성 요청 — 추정가 입력 불필요."""
    artist: str
    medium: str           # "유화", "수채", "판화" 등
    width_cm: float
    height_cm: float
    year: int | None = None
    auction_type: str = "프리미엄"  # "위클리" | "프리미엄" | "메이저"

class EstimateValidateRequest(EstimateRequest):
    """추정가 검증 요청 — K-Auction 추정가와 비교."""
    kauction_estimate_low: int
    kauction_estimate_high: int

class PredictWithEstimateRequest(BaseModel):
    """v2 모드: 생성 추정가 기반 낙찰가 예측."""
    artist: str
    medium: str
    width_cm: float
    height_cm: float
    year: int | None = None
    auction_type: str = "프리미엄"
    # 추정가 미입력 시 Model-B가 자동 생성
    estimate_low: int | None = None
    estimate_high: int | None = None
```

**엔드포인트 정리:**

| 엔드포인트 | 용도 | 추정가 입력 | Phase |
|-----------|------|-----------|-------|
| `POST /api/v1/predict_price` | 기존 낙찰가 예측 | 필수 | 1-2 (변경 없음) |
| `POST /api/v1/estimate` | 추정가 생성 | 불필요 | 3 신규 |
| `POST /api/v1/estimate/validate` | 추정가 검증 | K-Auction 추정가 입력 | 3 신규 |
| `POST /api/v1/predict_v2` | v2 낙찰가 예측 | 선택 (없으면 자동 생성) | 3 신규 |

### 5.2 게이트 조건 (12개) 자동 판정

```python
# check_estimate_gate.py 판정 기준

gates = {
    # Model-A 게이트
    "G1": coverage_overall >= 0.55,          # Coverage Rate (전체)
    "G2": coverage_major >= 0.58,            # Coverage Rate (메이저)
    "G3": hedonic_r2 >= 0.65,                # Hedonic R² (보조)
    "G4": 0.3 <= range_width_median <= 1.2,  # Range Width 적정성

    # Model-B 게이트
    "G5": estimate_mape_all < 0.35,          # Estimate MAPE (전체)
    "G6": estimate_mape_major < 0.25,        # Estimate MAPE (메이저)
    "G7": integrated_mape < 0.32,            # 통합 MAPE

    # Cold Start / 품질 게이트
    "G8": cold_start_generation == 1.0,      # 100% 생성 보장
    "G9": cold_start_mape < 0.60,            # Cold Start MAPE 하한
    "G10": leakage_test_all_pass,            # 8개 누수 테스트 전체 통과
    "G11": low_liquidity_mape < 0.50,        # 저유동성 작가 slice MAPE
    "G12": monotonicity_rate == 1.0,         # low ≤ mid ≤ high 100%
}
```

### 5.3 Champion 비교 매트릭스

| 후보 | 방법 | 평가 지표 |
|------|------|----------|
| Model-A q50 | 직접 예측 (추정가 불필요) | 낙찰가 MAPE, MdAPE |
| v2 재학습 | Model-B OOF → 기존 엔진 v2 | 낙찰가 MAPE, MdAPE |

Champion 선택: 낙찰가 MAPE가 더 낮은 쪽을 채택. 타입별(메이저/프리미엄/위클리) 세분화 비교도 수행.

### 5.4 Sprint 4 완료 조건

```
□ 12개 게이트 전체 자동 판정 완료
□ 필수 12개 게이트 전체 통과
□ Champion 비교 완료 (Model-A q50 vs v2 MAPE)
□ Cold Start Tier별 MAPE 보고 (Tier 1/2/3)
□ Fallback 발동률 보고 (전체 Test set 중 Tier 1/2/3 비율)
□ Feature importance 리포트 생성
□ 타입별(메이저/프리미엄/위클리) MAPE 보고
□ 가격대별(5-segment) MAPE 보고
□ 저유동성 작가 slice 분석 완료
□ 전체 테스트 통과 (pytest)
□ ruff check + mypy 통과
□ git commit + 최종 검증 결과 보고
```

---

## 6. 실행 순서 + 의존성 그래프

```
준비 (0.1~0.5)
  ├── pyproject.toml 수정 (estimate-engine)
  ├── 디렉토리 구조 생성
  ├── Phase 1-2 코드 통합 지점 확인
  └── 4-way 분할 설계
      │
Sprint 0 (3일) ──────────────────────────────────────
  │
  ├── [병렬] 0-1 splits 확장 (4-way)
  ├── [병렬] 0-5 market_rounder
  │         │
  │         ▼
  ├── [순차] 0-2 hedonic_stats (splits 필요)
  ├── [순차] 0-4 cold_start (hedonic_stats 필요)
  ├── [순차] 0-3 hedonic_features (모두 필요)
  │         │
  │         ▼
  ├── [병렬] 0-6~0-8 테스트 코드 (모듈과 함께)
  └── [순차] 0-9 leakage test (전체 필요)
      │
Sprint 1 (3일) ──────────────────────────────────────
  │
  ├── [병렬] 1-1 quantile_model (Model-A)
  ├── [병렬] 1-2 estimate_model (Model-B)
  ├── [병렬] 1-3 metrics 확장
  ├── [병렬] 1-4 selection_bias
  │         │
  │         ▼
  ├── [순차] 1-5~1-7 테스트 코드
  └── [순차] 1-8 train_estimate_models.py
      │
Sprint 2 (2일) ──────────────────────────────────────
  │
  ├── [선행] 2-1 quantile_calibrator (Model-A Calib)
  ├── [선행] 2-2 estimate_calibrator (Model-B Calib)
  │         │
  │         ▼
  ├── [순차] 2-3~2-4 테스트 코드
  └── [순차] 2-5 calibrate_models.py
      │
Sprint 3 (2일) ──────────────────────────────────────
  │
  ├── [선행] 3-1 target_transform_v2 (OOF 재학습)
  ├── [선행] 3-2 generator.py (통합 파이프라인)
  │         │
  │         ▼
  ├── [순차] 3-3~3-4 테스트 코드
  └── [순차] 3-5 retrain_price_engine_v2.py
      │
Sprint 4 (2일) ──────────────────────────────────────
  │
  ├── [순차] 4-1 validate_estimate_models.py
  ├── [순차] 4-2 check_estimate_gate.py → 12개 게이트 자동 판정
  ├── [병렬] 4-3 Cold Start 리포트
  ├── [병렬] 4-4 Feature importance 리포트
  └── [최종] 4-5 Champion 비교 → 최종 결과 보고
```

---

## 7. 착수 첫 작업 (순서)

```
1. pyproject.toml에 estimate-engine 의존성 추가 + pip install
2. 디렉토리 구조 생성 (__init__.py 포함)
3. features/splits.py에 4-way 분할 함수 추가
4. features/hedonic_stats.py (신규 8개 피처 산출 함수)
5. estimate_generator/cold_start.py (3-tier fallback + Bayesian shrinkage)
6. estimate_generator/hedonic_features.py (23개 피처 빌더)
7. estimate_generator/market_rounder.py (호 단위 라운딩)
8. tests/test_hedonic_features.py + test_cold_start_estimate.py + test_market_rounder.py
9. tests/test_estimate_leakage.py (8개 누수 규칙)
10. hedonic_features.parquet 생성 + Sprint 0 완료 조건 확인
11. Model-A (quantile_model.py) + Model-B (estimate_model.py) 학습
12. metrics.py 확장 (Pinball Loss, Interval Score 등)
13. selection_bias.py (유찰 보정)
14. Sprint 1 완료 조건 확인
```

---

## 8. 기획서 설계 → 코드 매핑

기획서(estimate_generation_plan.md v8.0)의 모든 설계 요소가 코드로 구현되는 위치:

| 기획서 절 | 설계 내용 | 구현 파일 | Sprint |
|----------|----------|----------|--------|
| 1.2 | 목적 분리 (Model-A/B) | quantile_model.py, estimate_model.py | 1 |
| 2.5 | 3-tier Cold Start fallback | cold_start.py | 0 |
| 3.2 | Model-A MultiQuantile | quantile_model.py | 1 |
| 3.2.1 | Prediction Interval Calibration | quantile_calibrator.py | 2 |
| 3.3 | Model-B RMSE + smearing | estimate_model.py, estimate_calibrator.py | 1, 2 |
| 3.4 | 23개 피처 (15 유지 + 8 신규) | hedonic_features.py, hedonic_stats.py | 0 |
| 3.5 | 추정가 범위 생성 | generator.py | 3 |
| 3.6 | 호 단위 라운딩 | market_rounder.py | 0 |
| 4.2.1 | OOF 생성 추정가 절차 | target_transform_v2.py | 3 |
| 5.1 | 평가 지표 (A/B/C) | metrics.py | 1 |
| 5.2 | 12개 게이트 조건 | check_estimate_gate.py | 4 |
| 6.3 | 4-way 분할 + 8개 누수 규칙 | splits.py, test_estimate_leakage.py | 0 |
| 7장 #12 | Selection bias 보정 | selection_bias.py | 1 |

---

## 9. 리스크 관리

### 9.1 기술 리스크 및 완화

| # | 리스크 | 확률 | 영향 | 완화 전략 | 발견 Sprint |
|---|--------|------|------|----------|------------|
| R1 | MultiQuantile 미지원 | 낮음 | 중간 | isotonic rearrangement fallback 구현 | Sprint 1 |
| R2 | Hedonic R² < 0.65 | 중간 | 높음 | 피처 추가 실험 (에디션 파싱, 제목 키워드) | Sprint 1 |
| R3 | Cold Start MAPE > 60% | 중간 | 중간 | Tier 조건 완화 or 그룹 세분화 | Sprint 2 |
| R4 | OOF-서빙 분포 불일치 (PSI > 0.1) | 중간 | 높음 | Fold 수 조정, 후처리 체인 점검 | Sprint 3 |
| R5 | 통합 MAPE > 32% | 중간 | 높음 | Model-A q50 직접 예측 fallback | Sprint 3 |
| R6 | Calibration 불안정 (Validation에서 coverage 미달) | 중간 | 중간 | Calib 크기 확대, slice별 보정 | Sprint 2 |
| R7 | Smearing factor 불안정 (bootstrap CI > ±0.1) | 낮음 | 중간 | 세그먼트 수 감소 (5 → 3) | Sprint 2 |

### 9.2 품질 방어 게이트 (Sprint별)

| Sprint | 게이트 | 실패 시 대응 |
|--------|--------|------------|
| Sprint 0 | 누수 테스트 전체 통과 | 코드 수정 후 재실행 |
| Sprint 1 | Hedonic R² ≥ 0.65 | 피처 추가/변경 실험 |
| Sprint 2 | Coverage ≥ 55%, MAPE < 35% | Calibration 재조정 |
| Sprint 3 | PSI < 0.1, 통합 MAPE < 32% | OOF 절차 수정 |
| Sprint 4 | 12개 게이트 전체 통과 | 미달 게이트 개별 대응 |

### 9.3 리스크 폐쇄 결정규칙 (Codex 4회차 대응)

**리스크 상태 전이 규칙:**

| 현재 상태 | 전이 조건 | 다음 상태 |
|----------|----------|----------|
| 🟡 Active | 해당 Sprint 게이트 통과 + 코드 구현 완료 | ✅ Resolved |
| 🟡 Active | Sprint 게이트 실패 + 완화 전략 1차 적용 후 재시도 통과 | ✅ Resolved |
| 🟡 Active | Sprint 게이트 실패 + 완화 전략 2회 실패 | 🔴 Escalated |
| 🔴 Escalated | 설계 변경 또는 게이트 기준 완화 결정 | 🟡 Active (재작업) |

**Escalation 프로토콜:**
- 🔴 Escalated 리스크 발생 시 Sprint를 중단하고 설계 재검토
- R2(R² < 0.65) Escalation: 피처 추가 실험 2회 실패 → 목표 R² 0.60으로 하향 검토
- R5(통합 MAPE > 32%) Escalation: Model-A q50 직접 예측을 Champion으로 전환
- 기타: 기획서(estimate_generation_plan.md) 수정 후 재착수

**0.4절 리스크 표 ↔ 9.1절 R표 대응:**

| 0.4절 # | 9.1절 R# | 설명 |
|---------|---------|------|
| 1 | R2 | R² 하락 |
| 3 | R4, R5 | Covariate shift → OOF PSI, 통합 MAPE |
| 5 | R3 | Cold Start MAPE |
| 7 | — | 누수 방지 (Sprint 0 게이트로 직접 검증) |
| 11 | — | 일정 리스크 (Sprint별 게이트로 관리) |
| 12 | R3 일부 | Selection bias (G11 게이트로 검증) |

---

*본 계획서는 `estimate_generation_plan.md` v8.0의 아키텍처(Model-A/B 분리), 피처 설계(23개), 평가 전략(12개 게이트), 데이터 분할(4-way + OOF), 누수 방지(8개 규칙), Cold Start(3-tier fallback), 라운딩(Model-B 전용), 리스크(12건)를 실행 가능한 태스크로 분해한 것이다. Phase 3(Sprint 0~4, 12일)은 Claude가 직접 구현하며, 각 Sprint 완료 시 git commit + 검증 결과를 보고한다.*

---

## 10. Codex 리뷰 이력

| 회차 | 결과 | 주요 피드백 | 대응 |
|------|------|-----------|------|
| 1회 | MAJOR | 1C (OOF 초기구간), 4M (4-way 마이그레이션, v2 스키마, group_unsold_rate 경로, API 불일치), 2m (게이트 프로토콜, 리스크 추적) | v2.0 |
| 2회 | MAJOR | 에이전트 이전 수정 반영 | v3.0 |
| 3회 | MAJOR | 3M (OOF warm-up 분포혼합, confidence_grade 통합, API 계약), 1m (리스크 폐쇄루프) | v4.0 |
| 4회 | MAJOR | 1M (OOF warm-up Option B 잔존 → Test 사용 모순), 1m (리스크 결정규칙) | v5.0 |
| 5회 | MAJOR | 1M (warm-up 문구 모순), 1m (리스크 폐쇄규칙 부재) | v6.0 |
| 6회 | MAJOR | 2M (Fold Train_B에 warm-up 미포함, Step 3 문구 충돌) → 수정 | v7.0 |
