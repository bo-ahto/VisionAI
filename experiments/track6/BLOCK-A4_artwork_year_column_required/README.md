# BLOCK-A4 제작연도 기반 실험 보류 일지

- 상태: 보류
- 실험군: Blocked
- 상사 기준 라벨: A4/A10/A11/C5/D5
- 가설: 제작연도와 작품 나이는 가격 예측에 영향을 줄 수 있다.
- 목적: 현재 데이터에 제작연도 명시 컬럼이 없어 실행 전 필요한 데이터 조건을 기록한다.
- 학습 피처: `artwork_year 또는 artwork_age 필요`
- 테스트 피처: `동일 컬럼 필요`
- 모델: Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
