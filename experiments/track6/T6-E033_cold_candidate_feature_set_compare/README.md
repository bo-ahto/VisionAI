# T6-E033 Cold 후보 피처 조합 비교

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G8 최종 운영 후보 확정
- 가설: Cold는 작가명 없이 호수, 재료, 지지체, 크기 파생 조합으로 성능을 개선할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `호수 only / 재료 / 지지체 / 크기 파생 / 작가 메타 조합`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: Cold 피처셋별 median/p95
- 유의미함 기준: Cold 최종 피처 후보 선정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
