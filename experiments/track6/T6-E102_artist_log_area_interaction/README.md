# T6-E102 작가명 x 면적 교차항 실험

- 상태: 계획
- 실험군: Group D
- 상사 기준 라벨: D2
- 가설: 같은 면적이라도 작가명에 따라 대형작 가격 프리미엄이 다를 수 있다.
- 목적: 작가별 대형작 프리미엄이 존재하는지 확인한다.
- 학습 피처: `작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x log_area`
- 테스트 피처: `학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외`
- 모델: Warm: Huber/Linear/Ridge
- HTML 일지: `experiment_log.html`
