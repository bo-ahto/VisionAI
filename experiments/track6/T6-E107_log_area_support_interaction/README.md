# T6-E107 면적 x 난트 지지체 교차항 실험

- 상태: 계획
- 실험군: Group D
- 상사 기준 라벨: old-D2
- 가설: 같은 면적이라도 지지체가 캔버스인지 종이인지에 따라 가격 효과가 다를 수 있다.
- 목적: 큰 캔버스와 큰 종이 작품의 가격 차이를 확인한다.
- 학습 피처: `작품 기본 피처 묶음 + log_area x nant_support`
- 테스트 피처: `학습 피처와 동일`
- 모델: Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
