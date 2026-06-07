# T6-E024 재료 x 호수 조합 피처 실험

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G5 약점 구간 보완
- 가설: 같은 호수라도 재료에 따라 가격 증가 패턴이 다를 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + nant_material_idx_x_ho_bucket`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 단독 피처 vs 조합 피처
- 유의미함 기준: 재료-크기 조합 피처 유지 여부 결정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
