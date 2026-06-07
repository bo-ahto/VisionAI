# D1 log_area x 재료 숫자형 교차항 실험 프롬프트

- 실험 목적: 같은 면적이라도 재료에 따라 가격 증가 방식이 달라지는지 확인한다.
- 실험 변수: `log_area`, `nant_material_idx`, `nant_tool`
- 교차항 처리: `log_area`를 문자열로 바꾸지 않고 숫자형으로 유지한다.
- 교차항 생성: 학습 데이터 상위 재료 카테고리에 대해 `log_area * 해당 재료 여부` 숫자형 컬럼을 만든다.
- 비교 기준: `log_area + 재료` 기준 모델과 `log_area + 재료 + 숫자형 교차항` 모델을 비교한다.
- 모델: Warm은 Huber / Linear Regression / Ridge, Cold는 Huber / Quantile-LAD / LightGBM을 사용한다.
- 데이터: Track6 고정 split 전체를 사용하고 샘플링하지 않는다.
- 라벨 사용: label은 학습 target과 평가 지표 계산에만 사용한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE.
