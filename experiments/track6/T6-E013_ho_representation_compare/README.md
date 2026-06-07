# T6-E013 호수 표현 방식 비교

- 상태: 예정
- 실험 단계: 기본 피처 정의 상세 실험
- 단계 설명: 최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험
- 세부 목표: T6-G5 운영 가능 피처 선정
- 가설: 호수는 원값보다 로그값, 구간값, 대형 플래그 등으로 표현할 때 더 안정적일 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `estimated_ho / ln_estimated_ho / ho_bucket / is_large_ho / is_extra_large_ho`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 호수 표현별 Warm/Cold median APE
- 유의미함 기준: 후속 실험에서 사용할 호수 대표 표현 선정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
