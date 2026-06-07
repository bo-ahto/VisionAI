# D3 재료 x 지지체 범주형 조합 실험 프롬프트

- 실험 목적: 재료와 지지체 조합이 단독 재료/지지체보다 가격 예측을 개선하는지 확인한다.
- 실험 변수: `nant_material_idx`, `nant_tool`, `nant_support`
- 조합 처리: `nant_material_idx + nant_support`, `nant_tool + nant_support`를 범주형 조합 피처로 만든다.
- 비교 기준: `재료 + 지지체` 기준 모델과 `재료 + 지지체 + 조합 피처` 모델을 비교한다.
- 모델: Warm은 Huber / Linear Regression / Ridge, Cold는 Huber / Quantile-LAD / LightGBM을 사용한다.
- 데이터: Track6 고정 split 전체를 사용하고 샘플링하지 않는다.
- 라벨 사용: label은 학습 target과 평가 지표 계산에만 사용한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE.
