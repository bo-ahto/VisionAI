# T6-E018 재료 피처 추가 실험

- 상태: 예정
- 실험 단계: 기본 피처 정의 상세 실험
- 단계 설명: 최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험
- 세부 목표: T6-G5 운영 가능 피처 선정
- 가설: 재료 정보는 작품 가격 예측에서 크기 외 추가 설명력을 제공한다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + nant_material_idx + nant_tool`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: baseline vs 재료 추가
- 유의미함 기준: Warm/Cold별 재료 피처 유지 여부 결정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
