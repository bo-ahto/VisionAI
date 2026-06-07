# T6-E014 헤도닉 선형 모델군 비교

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G6 모델 안정성 확인
- 가설: 같은 피처에서는 Ridge 외 Huber/Quantile 계열이 tail risk를 줄일 수 있다.
- 테스트 모델: Linear / Ridge / Lasso / ElasticNet / Huber / Quantile
- 학습에 사용된 피처: `artist_name_ko, ln_estimated_ho`
- 테스트에 사용된 피처: `artist_name_ko, ln_estimated_ho`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 선형 모델군 Warm/Cold 성능
- 유의미함 기준: 기준 선형 모델 후보 확정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
