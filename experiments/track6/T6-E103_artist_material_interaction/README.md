# T6-E103 작가명 x 난트 재료 교차항 실험

- 상태: 계획
- 실험군: Group D
- 상사 기준 라벨: D3
- 가설: 같은 재료라도 특정 작가에게서 가격 프리미엄이 다르게 나타날 수 있다.
- 목적: 작가별 특정 재료 프리미엄을 확인한다.
- 학습 피처: `작품 기본 피처 묶음 + artist_name_ko + artist_name_ko x nant_material_idx`
- 테스트 피처: `학습 피처와 동일. Cold에서는 artist_name_ko 교차항 제외`
- 모델: Warm: Huber/Linear/Ridge
- HTML 일지: `experiment_log.html`
