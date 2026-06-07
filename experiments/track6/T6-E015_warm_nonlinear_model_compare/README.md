# T6-E015 Warm 비선형 모델 비교

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G3 Warm 성능 개선
- 가설: Warm에서는 작가명과 크기 관계가 비선형이므로 트리 모델이 선형보다 나을 수 있다.
- 테스트 모델: LightGBM / CatBoost / XGBoost / HistGradientBoosting
- 학습에 사용된 피처: `artist_name_ko, ln_estimated_ho`
- 테스트에 사용된 피처: `artist_name_ko, ln_estimated_ho`
- 학습 정답값: `ln_price_krw`
- 비교 기준: Warm Ridge baseline
- 유의미함 기준: Warm 기준 모델 후보 선정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
