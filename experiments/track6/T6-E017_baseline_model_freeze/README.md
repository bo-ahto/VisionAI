# T6-E017 기본 피처 기반 Warm/Cold 후보 모델 선정

- 상태: 실행 완료
- 실험 단계: 기본 피처로 후보 모델 비교
- 세부 목표: 1차 후보 전체 비교 후 Warm/Cold 상위 후보 압축
- 가설: 같은 후보 모델군을 Warm과 Cold에 모두 적용하면 모델별 강점과 약점을 공정하게 비교할 수 있다.
- 학습 정답값: `ln_price_krw`
- HTML 일지: `experiment_log.html`

## 기본 피처

- Warm 최소 피처: `artist_name_ko`, `ln_estimated_ho`
- Warm 기본 피처: `artist_name_ko`, `ln_estimated_ho`, `nant_material_idx`, `nant_tool`, `support_category`
- Cold 최소 피처: `ln_estimated_ho`
- Cold 기본 피처: `ln_estimated_ho`, `nant_material_idx`, `nant_tool`, `support_category`

## 기본 피처 선정 기준

- 운영에서 사용자가 입력하거나 시스템이 안정적으로 만들 수 있어야 함
- 가격 정보나 출처 정보가 섞여 누수가 생기면 안 됨
- Warm과 Cold의 차이는 작가명 사용 가능 여부로만 먼저 둠
- 작품 자체 피처는 Warm과 Cold에 최대한 공통 적용함
- 크기 대표값은 우선 `ln_estimated_ho` 하나로 시작함
- `width_cm`, `height_cm`, `log_area`, `aspect_ratio`는 크기 파생 후속 실험에서 검증함
- `depth_cm`, `has_depth`, `is_3d_candidate`는 3D 약점 구간 보완 후보로 후속 검증함
- `nant_material_idx`, `nant_tool`은 재료 세분화 후보로 후속 검증함

## 공통 후보 모델

- 선형 계열 모델
- Linear Regression
- Ridge
- Huber
- Quantile / LAD
- 트리 계열 모델
- LightGBM
- XGBoost
- CatBoost
- HistGradientBoosting

## 중복 후보 제거 기준

- `Hedonic Huber`와 `Huber`처럼 같은 estimator, 같은 전처리, 같은 피처를 쓰는 후보는 분리하지 않음
- `Hedonic Ridge`와 `Ridge`처럼 실행 결과가 원리상 동일한 후보는 하나만 유지함
- `Hedonic Quantile`과 `LAD / Quantile`처럼 같은 QuantileRegressor를 쓰는 후보는 하나만 유지함
- `Hedonic`은 별도 모델명이 아니라 “작품 가격을 작가명, 호수, 재료 같은 설명 변수로 설명하는 회귀 실험 방식”으로 문서에서만 사용함

## 후보 모델 설명

- Linear Regression: 작가명, 호수, 재료 같은 설명 변수로 가격을 설명하는 가장 기본 선형 모델
- Ridge: 기본 선형 회귀에 규제를 넣어 과적합을 줄인 모델
- Huber: 큰 오차값의 영향을 줄여 이상치에 더 강한 선형 모델
- Quantile / LAD 계열: 절대오차 또는 분위값 기준으로 학습해 큰 오차에 덜 흔들리는 모델
- LightGBM: 여러 개의 작은 트리를 조합해 비선형 관계를 잘 잡는 모델
- CatBoost: 범주형 피처 처리에 강한 트리 기반 모델
- XGBoost: 성능이 강한 트리 기반 모델로, 복잡한 피처 조합을 잘 학습할 수 있는 모델
- HistGradientBoosting: scikit-learn 기반 트리 모델로 빠르게 비선형 기준 성능을 확인하기 좋은 모델

## 실행 전략

- 1차 비교: 모든 후보 모델을 기본 설정으로 1회 실행
- 1차 목적: 가능성이 낮은 모델을 빠르게 제외
- 2차 압축: Warm 상위 2~3개, Cold 상위 2~3개 선정
- 3차 검증: 압축된 후보만 반복 실행, 세부 설정값 조정, slice별 안정성 확인
- 주의: 처음부터 모든 모델을 튜닝하지 않음

## 판단 기준

- 1순위: Warm/Cold 각각 median APE가 낮은 모델
- 2순위: p95 APE가 과도하게 높지 않은 모델
- 3순위: Within-30 / Within-50이 높은 모델
- 4순위: 같은 성능이면 단순하고 재현 가능한 모델
- 5순위: 실행 시간이 과도하게 길지 않은 모델

## 결과 산출물

- `outputs/metrics.csv`: 모델별 Warm/Cold 지표
- `outputs/predictions.csv`: 예측값과 실제값
- `outputs/slice_metrics.csv`: 구간별 오차
- `outputs/selected_models.json`: Warm 상위 후보 2~3개, Cold 상위 후보 2~3개
- `outputs/summary.md`: 후보 선정 이유
