# T6-E025 작가명 x 호수 조합 실험

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G3 Warm 성능 개선
- 가설: Warm에서는 작가별 크기 가격대 차이를 조합 피처로 반영할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + artist_ho_bucket`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: artist + ho vs artist x ho 조합
- 유의미함 기준: Warm 전용 조합 피처 효과 확인
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
