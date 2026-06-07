# T6-E029 Cold 재료 + 크기 모델 실험

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G4 Cold 성능 개선
- 가설: Cold에서는 작가명 대신 재료와 크기 정보가 예측 성능을 보완할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `ln_estimated_ho + nant_material_idx + nant_tool + support_category + nant_material_idx`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: Cold ho only vs 재료+크기
- 유의미함 기준: Cold median APE와 p95 APE 개선
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
