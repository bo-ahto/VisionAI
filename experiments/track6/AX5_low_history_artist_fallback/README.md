# AX5 저이력 작가 전용 fallback 실험

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX5
- 가설: 학습 작품 수가 적은 작가는 Warm 모델보다 Cold 모델이 더 안정적일 수 있다.
- 목적: Warm/Cold 경계 작가의 모델 선택 정책을 검증한다.
- 학습 피처: `작품 기본 피처 묶음 + artist_works_log 구간`
- 테스트 피처: `저이력 Warm slice`
- 모델: Warm 후보 vs Cold 후보
- HTML 일지: `experiment_log.html`
