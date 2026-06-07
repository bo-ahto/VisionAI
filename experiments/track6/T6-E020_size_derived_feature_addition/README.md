# T6-E020 크기 파생 피처 추가 실험

- 상태: 예정
- 실험 단계: 기본 피처 정의 상세 실험
- 단계 설명: 최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험
- 세부 목표: T6-G5 운영 가능 피처 선정
- 가설: 호수 외 면적, 가로/세로, 비율 피처가 추가 설명력을 줄 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + area_cm2 + log_area + width_cm + height_cm + aspect_ratio`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 호수 only vs 크기 파생 추가
- 유의미함 기준: 호수만 쓸지, 크기 파생을 유지할지 결정
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
