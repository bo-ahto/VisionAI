# T6-E031 Cold 위험 구간 분석

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G7 신뢰도/가격 범위 정책
- 가설: Cold 큰 오차는 특정 크기, 재료, 호수 구간에 집중될 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `Cold 후보 피처`
- 테스트에 사용된 피처: `Cold 후보 피처`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 전체 Cold vs 위험 slice
- 유의미함 기준: 서비스 신뢰도 경고 후보 구간 정의
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
