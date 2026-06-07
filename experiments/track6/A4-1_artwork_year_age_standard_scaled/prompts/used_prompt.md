# A4-1 artwork_year / artwork_age 단독 변수 효과 검증 실험

## 실험 목적

- 제작연도 관련 정보만으로 작품 가격 예측에 도움이 되는지 확인한다.
- 운영 환경에서 실제 입력 가능한 제작연도 정보만 사용한다.
- Warm / Cold split에서 제작연도 계열 변수의 일반화 성능 차이를 확인한다.
- support / material / artist 없이 제작연도 계열 변수 자체의 단독 설명력을 검증한다.

## 실험 변수

- `artwork_year`
  - 작품 제작연도 원값
  - 예: `1980`, `1995`, `2018`
- `artwork_age`
  - 기준연도 2026 기준 작품이 만들어진 후 경과한 연수
  - 계산식: `artwork_age = 2026 - artwork_year`
- `artwork_year + artwork_age`
  - 제작연도 원값과 작품 연한을 동시에 사용

## 중요 구현 조건

- `artwork_year`와 `artwork_age`는 연속형 숫자 변수로 처리한다.
- 문자열 변환 후 `OneHotEncoder` 방식으로 처리하지 않는다.
- 제작연도와 작품 연한의 연속성, 거리, 순서를 유지한다.
- 숫자형 피처는 `StandardScaler` 기반 preprocessing을 사용한다.
- 범주형 피처와 숫자형 피처 preprocessing을 분리한다.

## 전처리 정책

- `numeric_features`
  - `artwork_year`
  - `artwork_age`
- `categorical_features`
  - 없음
- 전처리 방식
  - numeric: `SimpleImputer(strategy="median")` + `StandardScaler`
  - categorical: `OneHotEncoder(handle_unknown="ignore")`

## 모델 구성

- Warm 평가
  - A: Huber
  - B: Linear Regression
  - C: Ridge
- Cold 평가
  - D: Huber
  - E: Quantile-LAD
  - F: LightGBM

## 데이터 정책

- train split 고정
- warm test split 고정
- cold test split 고정
- feature 파일과 label 파일은 `_track6_row_id` 기준으로 연결
- label은 학습 target 및 metric 계산에만 사용
- label leakage 금지
- sampling 없음
- 전체 split 사용

## 운영 입력 제한

- 운영에서 입력할 수 없는 제작연도 출처 정보는 사용하지 않는다.
- 제작연도 결측 여부 flag는 사용하지 않는다.
- HTML 보강 source는 모델 입력에서 제외한다.
- Saatchi 상세페이지 보강값은 검토용으로만 사용한다.

## 평가 지표

- `R2`
- `MdAPE`
- `p95_APE`
- `Within_30`
- `Within_50`
- `MAPE`

## 재현성 확인

- 같은 설정으로 실험을 2회 실행한다.
- `metrics_long.csv` 기준으로 전체 지표가 동일한지 비교한다.
- 비교 키는 `experiment_id`, `variable_block`, `scope`, `model_code`, `model_name`이다.
