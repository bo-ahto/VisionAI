# T6-E106 작가 메타 결측 여부 변수 영향 확인

- 상태: 계획
- 실험군: Group B
- 상사 기준 라벨: B8
- 가설: 작가 메타 정보가 비어 있는 상태 자체가 예측 오차와 관련 있을 수 있다.
- 목적: 메타 값의 효과와 메타 결측 위험을 분리해서 본다.
- 학습 피처: `artist_meta_missing_flags + artist_meta_available_count + artist_meta_completeness_score`
- 테스트 피처: `학습 피처와 동일`
- 모델: Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
