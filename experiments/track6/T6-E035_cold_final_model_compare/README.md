# T6-E035 Cold 최종 후보 모델 비교

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G8 최종 운영 후보 확정
- 가설: 최종 Cold 피처셋에서는 robust 선형 또는 단순 트리 모델이 가장 안정적일 수 있다.
- 테스트 모델: Ridge / Huber / Quantile / CatBoost / LightGBM
- 학습에 사용된 피처: `T6-E033 선정 Cold 피처셋`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 최종 Cold 모델 후보 전체
- 유의미함 기준: Cold 최종 모델 확정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
