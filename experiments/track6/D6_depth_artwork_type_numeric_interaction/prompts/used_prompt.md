# D6 depth x 작품 유형 숫자형 교차항 실험 프롬프트

- 실험 목적: 작품 유형에 따라 깊이 정보의 가격 효과가 달라지는지 확인한다.
- 실험 변수: `depth_cm`, `has_depth`, `is_3d_candidate`, `artwork_type_final`, `artwork_type_final_major3`
- 교차항 처리: `depth_cm`을 문자열로 바꾸지 않고 숫자형으로 유지한다.
- 교차항 생성: 학습 데이터 작품 유형 카테고리에 대해 `depth_cm * 해당 작품 유형 여부` 숫자형 컬럼을 만든다.
- 비교 기준: `깊이 + 작품 유형` 기준 모델과 `깊이 + 작품 유형 + 숫자형 교차항` 모델을 비교한다.
- 모델: Warm은 Huber / Linear Regression / Ridge, Cold는 Huber / Quantile-LAD / LightGBM을 사용한다.
- 데이터: Track6 고정 split 전체를 사용하고 샘플링하지 않는다.
- 라벨 사용: label은 학습 target과 평가 지표 계산에만 사용한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE.
