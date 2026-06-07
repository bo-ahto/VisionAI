# AX6 작가 메타 결측 패턴별 성능 실험

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX6
- 가설: 생년/국적/활동량 정보가 비어 있는 작가군은 예측 오차가 커질 수 있다.
- 목적: 메타 값을 넣는 실험이 아니라 결측 자체의 위험도를 확인한다.
- 학습 피처: `artist_meta_missing_flags + artist_meta_completeness_score`
- 테스트 피처: `학습 피처와 동일`
- 모델: Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
