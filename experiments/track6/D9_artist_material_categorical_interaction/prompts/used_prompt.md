# D9 artist_name x 재료 범주형 조합 실험 프롬프트

- 실험 목적: 특정 작가가 특정 재료에서 가격 프리미엄을 갖는지 확인한다.
- 실험 변수: `artist_name_ko`, `nant_material_idx`, `nant_tool`
- 조합 처리: `artist_name_ko + nant_material_idx`, `artist_name_ko + nant_tool`을 범주형 조합 피처로 만든다.
- 비교 기준: `작가명 + 재료` 기준 모델과 `작가명 + 재료 + 조합 피처` 모델을 비교한다.
- 해석 중심: Warm 결과를 중심으로 판단하고 Cold 결과는 참고값으로만 둔다.
- 모델: Warm은 Huber / Linear Regression / Ridge, Cold는 Huber / Quantile-LAD / LightGBM을 사용한다.
- 데이터: Track6 고정 split 전체를 사용하고 샘플링하지 않는다.
- 라벨 사용: label은 학습 target과 평가 지표 계산에만 사용한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE.
