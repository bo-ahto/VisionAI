# AX2 동명이인 분리 전/후 비교

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX2
- 가설: 동명이인이 섞이면 작가명 피처 성능이 왜곡될 수 있다.
- 목적: 작가명 효과가 실제 작가 효과인지 데이터 혼합 효과인지 분리한다.
- 학습 피처: `artist_name_ko before/after homonym correction`
- 테스트 피처: `동일 비교 피처`
- 모델: Warm: Huber/Linear/Ridge
- HTML 일지: `experiment_log.html`
