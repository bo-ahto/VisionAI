# AX4 작가별 학습 작품 수 기준 변경 실험

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX4
- 가설: Warm으로 볼 작가의 최소 학습 작품 수 기준에 따라 성능 안정성이 달라질 수 있다.
- 목적: 1개, 3개, 5개 이상 기준 중 어떤 Warm 기준이 안정적인지 확인한다.
- 학습 피처: `작품 기본 피처 묶음 + artist_name_ko`
- 테스트 피처: `Warm test를 학습 작품 수 기준별로 재구성`
- 모델: Warm: Huber/Linear/Ridge, fallback Cold 모델
- HTML 일지: `experiment_log.html`
