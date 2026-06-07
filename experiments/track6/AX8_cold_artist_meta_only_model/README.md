# AX8 신규 작가 메타만 사용한 Cold 모델 실험

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX8
- 가설: 작가명 없이도 생년/국적/활동량 같은 운영 가능 작가 메타가 Cold 예측을 개선할 수 있다.
- 목적: Cold에서 작가 DB로 얻을 수 있는 메타만의 가치를 확인한다.
- 학습 피처: `작품 기본 피처 묶음 + 운영 가능 작가 메타`
- 테스트 피처: `Cold test에서 artist_name_ko 제외, 작가 메타만 사용`
- 모델: Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
