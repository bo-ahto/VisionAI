# T6-E105 작가명 x 3D/깊이 교차항 실험

- 상태: 계획
- 실험군: Group D
- 상사 기준 라벨: D5
- 가설: 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다르게 나타날 수 있다.
- 목적: 작가별 입체 작품 프리미엄을 확인한다.
- 학습 피처: `작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x has_depth/is_3d_candidate`
- 테스트 피처: `학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외`
- 모델: Warm: Huber/Linear/Ridge
- HTML 일지: `experiment_log.html`
