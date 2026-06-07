# T6-E011 호수 only Warm/Cold 기준 실험

- 상태: 예정
- 실험 단계: 기본 피처 정의 상세 실험
- 단계 설명: 최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험
- 세부 목표: T6-G2 기본 예측 가능성 확인
- 가설: 작가명 없이 호수만으로도 Warm/Cold 가격대의 최소 신호를 확인할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `ln_estimated_ho`
- 테스트에 사용된 피처: `ln_estimated_ho`
- 학습 정답값: `ln_price_krw`
- 비교 기준: T6-E010 Warm log / Cold log
- 유의미함 기준: 작가명 제거 후 성능 하락 폭을 수치화하고, 호수 단독 baseline을 확정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
