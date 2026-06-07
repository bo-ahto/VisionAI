# T6-E016 Cold 기본 모델 비교

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G4 Cold 성능 개선
- 가설: Cold에서는 작가명 없이도 robust 선형 또는 단순 트리 모델이 호수 기반 예측을 안정화할 수 있다.
- 테스트 모델: Ridge / Huber / Quantile / LightGBM / CatBoost
- 학습에 사용된 피처: `ln_estimated_ho`
- 테스트에 사용된 피처: `ln_estimated_ho`
- 학습 정답값: `ln_price_krw`
- 비교 기준: Cold Ridge log baseline
- 유의미함 기준: Cold 기준 모델 후보 선정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
