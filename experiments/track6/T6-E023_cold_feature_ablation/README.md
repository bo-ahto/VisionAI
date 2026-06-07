# T6-E023 Cold 피처 제거 ablation

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G4 Cold 성능 개선
- 가설: Cold 후보 피처 중 일부는 신규 작가 예측에서 오히려 불안정할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `Cold 후보 전체 피처에서 하나씩 제거`
- 테스트에 사용된 피처: `동일 제거 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 전체 피처 vs one-drop 피처
- 유의미함 기준: 최종 Cold 필수 피처와 제외 피처 구분
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
