# A11 작품 기본 피처 묶음 + 제작연도 + 작품 유형 실험

## 실험 목적

- A10 기준 작품 정보에 작품 유형을 추가했을 때 가격 예측 성능이 개선되는지 확인한다.
- 작가명은 사용하지 않고 작품 자체 정보만 사용한다.
- 작품 유형 전체 구분과 대분류 중 어떤 표현이 더 안정적인지 확인한다.

## 기준 피처

- `ln_estimated_ho`
- `nant_material_idx`
- `nant_tool`
- `nant_support`
- `artwork_year`
- `artwork_age`

## 추가 실험 변수

- `artwork_type_final`
  - 회화, 판화, 조각, 드로잉, 사진 등 작품 유형 전체 구분
- `artwork_type_final_major3`
  - 회화 / 판화 / 조각 / 기타 대분류

## 비교 조합

- A10 기준 피처 묶음
- A10 기준 피처 묶음 + `artwork_type_final`
- A10 기준 피처 묶음 + `artwork_type_final_major3`

## 제외 피처

- `artwork_type_source`
- `artwork_type_match_method`
- `artwork_type_raw`
- `artwork_type_confidence`

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

- A10 기준 피처 대비 MdAPE가 낮아지면 작품 유형이 도움이 된 것으로 본다.
- p95 APE가 낮아지면 큰 오차 감소에도 도움이 된 것으로 본다.
- Warm / Cold 결과는 따로 해석한다.
