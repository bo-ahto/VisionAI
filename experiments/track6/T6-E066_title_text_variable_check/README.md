# T6-E066 작품 제목 문구 변수 영향 확인

- 단계: 기본 피처 정의 - 개별 변수 확인
- 가설: 작품 제목에서 만든 키워드 변수는 에디션, 세트, 포스터 같은 가격 차이를 설명한다.
- 확인 변수: `title_raw`
- 테스트 모델: Warm `Huber / Linear Regression / Ridge`, Cold `Huber / Quantile-LAD / LightGBM`
- Warm 기준 모델 학습 피처: `artist_name_ko + ln_estimated_ho`
- Warm 변수 추가 모델 학습 피처: `artist_name_ko + ln_estimated_ho + title_raw keyword flags`
- Warm 테스트 피처: 학습 피처와 같은 컬럼 사용
- Cold 기준 모델 학습 피처: `ln_estimated_ho`
- Cold 변수 추가 모델 학습 피처: `ln_estimated_ho + title_raw keyword flags`
- Cold 테스트 피처: 학습 피처와 같은 컬럼 사용, `artist_name_ko` 제외
- 연결 키: `_track6_row_id`
- HTML 일지: `experiment_log.html`


## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
