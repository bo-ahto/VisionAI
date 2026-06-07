# T6-E012 작가명 only Warm 기준 실험

- 상태: 예정
- 실험 단계: 기본 피처 정의 상세 실험
- 단계 설명: 최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험
- 세부 목표: T6-G3 Warm 성능 개선
- 가설: Warm에서는 작가명만으로도 작가별 기본 가격대를 상당 부분 설명할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `artist_name_ko`
- 테스트에 사용된 피처: `artist_name_ko`
- 학습 정답값: `ln_price_krw`
- 비교 기준: artist_name_ko only vs artist_name_ko + ln_estimated_ho
- 유의미함 기준: 작가명 효과와 크기 효과를 분리 설명
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
