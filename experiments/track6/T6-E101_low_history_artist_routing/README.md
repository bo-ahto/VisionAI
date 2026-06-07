# T6-E101 작가별 학습 작품 수 구간별 라우팅 실험

- 상태: 계획
- 실험군: Group C
- 상사 기준 라벨: C10
- 가설: 학습 작품 수가 적은 작가는 Warm 모델보다 Cold 방식 또는 보수적 fallback이 더 안정적일 수 있다.
- 목적: 저이력 작가를 Warm으로 볼지 Cold로 볼지 결정하는 기준을 검증한다.
- 학습 피처: `작품 기본 피처 묶음 + artist_works_log 구간`
- 테스트 피처: `Warm test를 작가별 학습 작품 수 구간으로 나누어 평가`
- 모델: Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
