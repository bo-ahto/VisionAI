# C7 작가명 + 작품 기본 피처 묶음 + 제작연도 실험 지시 기록

- 실험 목적:
  - C6 작품 기본 피처 묶음에 제작연도 계열 변수를 추가했을 때 성능이 개선되는지 확인한다.
  - 운영에서 입력 가능한 제작연도 원값과 계산 가능한 작품 연한만 사용한다.

- 기준선:
  - `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + nant_support`

- 비교 피처:
  - C6 기준선
  - C6 + `artwork_year`
  - C6 + `artwork_age`
  - C6 + `artwork_year + artwork_age`

- 구현 조건:
  - 공통 실행기 `scripts/track6/fixed_variable_experiment_runner.py`를 사용한다.
  - `_track6_row_id` 기준으로 feature와 label을 연결한다.
  - label은 학습 target과 metric 계산에만 사용한다.
  - `ln_estimated_ho`, `artwork_year`, `artwork_age`는 숫자형으로 처리하고 `StandardScaler`를 적용한다.
  - 제작연도 출처, 보강 출처, 결측 flag는 모델 입력에서 제외한다.
  - sampling 없이 전체 split을 사용한다.

- 평가 모델:
  - Warm: Huber / Linear Regression / Ridge
  - Cold: Huber / Quantile-LAD / LightGBM

- 해석 기준:
  - Warm 결과를 중심으로 판단한다.
  - C6 기준선보다 Warm MdAPE 또는 RMSE(log)가 낮아지는지 확인한다.
