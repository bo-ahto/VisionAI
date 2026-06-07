# T6-E027 작가 기본 메타 피처 추가 실험

- 상태: 예정
- 실험 단계: 후속 실험
- 단계 설명: 기본 피처 정의 이후 진행할 후속 실험
- 세부 목표: T6-G3 Warm 성능 개선
- 가설: 작가 국적, 생년, 경력 연차 등 기본 메타 정보는 가격 예측을 개선할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + artist_meta_nationality + artist_meta_birth_year + artist_meta_career_age`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: baseline vs 작가 기본 메타 추가
- 유의미함 기준: 작가 DB 연동 가치 확인
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
