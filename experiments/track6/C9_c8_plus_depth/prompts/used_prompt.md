# C9 C8 + 깊이/입체성 정보 실험 지시 기록

- 실험 목적:
  - C8 누적 기준선에 깊이와 입체성 정보를 추가했을 때 가격 예측 성능이 개선되는지 확인한다.

- 기준선:
  - `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + nant_support + artwork_year + artwork_age + artwork_type_final + artwork_type_final_major3`

- 비교 피처:
  - C8 기준선
  - C8 + `has_depth`
  - C8 + `depth_cm`
  - C8 + `depth_cm + has_depth`
  - C8 + `depth_cm + has_depth + is_3d_candidate`

- 구현 조건:
  - 공통 실행기 `scripts/track6/fixed_variable_experiment_runner.py`를 사용한다.
  - `_track6_row_id` 기준으로 feature와 label을 연결한다.
  - label은 학습 target과 metric 계산에만 사용한다.
  - `depth_cm`은 숫자형으로 처리하고 `StandardScaler`를 적용한다.
  - `has_depth`, `is_3d_candidate`는 범주형으로 처리한다.
  - sampling 없이 전체 split을 사용한다.

- 평가 모델:
  - Warm: Huber / Linear Regression / Ridge
  - Cold: Huber / Quantile-LAD / LightGBM

- 해석 기준:
  - Warm 결과를 중심으로 판단한다.
  - Cold 결과는 참고값으로만 본다.
  - 3D 후보 표본이 작으므로 전체 성능 개선이 작더라도 slice 해석이 필요할 수 있다.
