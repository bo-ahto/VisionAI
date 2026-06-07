# A12 작품 정보 전체 확장 실험

## 실험 목적

- A11 기준 작품 정보에 depth/3D와 edition 정보를 추가했을 때 가격 예측 성능이 개선되는지 확인한다.
- 작가명은 사용하지 않고 작품 자체 정보만 사용한다.
- `signed`는 구조화 컬럼이 없으므로 제외한다.

## 기준 피처

- `ln_estimated_ho`
- `nant_material_idx`
- `nant_tool`
- `nant_support`
- `artwork_year`
- `artwork_age`
- `artwork_type_final`

## 추가 실험 변수

- depth/3D
  - `depth_cm`
  - `has_depth`
  - `is_3d_candidate`
- edition
  - `edition_class`
  - `is_edition`
  - `is_limited_edition`
  - `is_open_edition`
  - `is_unknown_edition`
  - `edition_info_available`

## 비교 조합

- A11 기준 피처 묶음
- A11 기준 피처 묶음 + depth/3D
- A11 기준 피처 묶음 + edition
- A11 기준 피처 묶음 + depth/3D + edition

## 제외 피처

- `signed`
- `edition_source`
- `artwork_type_source`
- `artwork_type_match_method`
- `artwork_year_source`
- `artwork_year_match_method`

## 데이터 정책

- split은 `data/track6_split_with_year_type_edition_size`로 고정한다.
- label은 학습 target과 평가 지표 계산에만 사용한다.
- feature 파일과 label 파일은 `_track6_row_id`로 연결한다.
- sampling 없이 전체 split을 사용한다.

## 모델 구성

- Warm A: Huber
- Warm B: Linear Regression
- Warm C: Ridge
- Cold D: Huber
- Cold E: Quantile-LAD
- Cold F: LightGBM

## 판단 기준

- A11 기준 피처 대비 MdAPE가 낮아지면 추가 피처가 도움이 된 것으로 본다.
- p95 APE가 낮아지면 큰 오차 감소에도 도움이 된 것으로 본다.
- depth/3D와 edition은 각각 단독 추가 효과와 동시 추가 효과를 따로 본다.
- Warm / Cold 결과는 따로 해석한다.
