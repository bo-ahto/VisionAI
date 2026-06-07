# AX3 작가 DB 매칭 성공/실패 구간 비교

- 상태: 계획
- 실험군: AX
- 상사 기준 라벨: AX3
- 가설: 작가 DB 매칭 성공 여부는 예측 오차와 신뢰도 판단에 영향을 줄 수 있다.
- 목적: 메타 변수 효과가 아니라 DB 커버리지 리스크를 확인한다.
- 학습 피처: `artist_db_match_flag + 작품 기본 피처 묶음`
- 테스트 피처: `학습 피처와 동일`
- 모델: Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM
- HTML 일지: `experiment_log.html`
