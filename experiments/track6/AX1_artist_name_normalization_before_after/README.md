# AX1 작가명 한글화 전/후 비교

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX1
- 가설: 영문/한글 표기 정리가 Warm 성능과 작가 매칭 안정성을 개선할 수 있다.
- 목적: 작가명 자체 효과가 아니라 이름 정제 품질을 검증한다.
- 학습 피처: `artist_name_ko_orig vs artist_name_ko`
- 테스트 피처: `동일 비교 피처`
- 모델: Warm: Huber/Linear/Ridge
- HTML 일지: `experiment_log.html`
