# AX7 작가 가격대 과적합 점검

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX7
- 가설: 작가명만으로 좋아진 성능은 작품 정보를 설명한 것이 아니라 가격대를 외운 결과일 수 있다.
- 목적: 작가명 효과의 신뢰성을 검증한다.
- 학습 피처: `artist_name_ko only vs artist_name_ko + 작품 기본 피처 묶음`
- 테스트 피처: `Random split / GroupKFold by artist 비교`
- 모델: Warm: Huber/Linear/Ridge
- HTML 일지: `experiment_log.html`
