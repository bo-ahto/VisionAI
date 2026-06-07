# T6-E026 지지체 x 재료 조합 실험

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G5 운영 가능 피처 선정
- 가설: 재료와 지지체의 조합은 단독 피처보다 가격을 더 잘 설명할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + nant_material_support_bucket + nant_support_nant_tool_bucket`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 단독 피처 vs 조합 피처
- 유의미함 기준: 운영 가능 조합 피처 후보 선정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
