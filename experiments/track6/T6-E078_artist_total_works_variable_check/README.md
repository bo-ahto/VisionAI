# T6-E078 작가 등록 작품 수 변수 영향 확인

- 단계: 기본 피처 정의 - 개별 변수 확인
- 가설: 작가 등록 작품 수 변수는 가격 예측에 영향을 미친다.
- 확인 변수: `artist_meta_total_works`
- 테스트 모델: Warm `Huber / Linear Regression / Ridge`, Cold `Huber / Quantile-LAD / LightGBM`
- Warm 기준 모델 학습 피처: `artist_name_ko + ln_estimated_ho`
- Warm 변수 추가 모델 학습 피처: `artist_name_ko + ln_estimated_ho + artist_meta_total_works`
- Warm 테스트 피처: 학습 피처와 같은 컬럼 사용
- Cold 기준 모델 학습 피처: `ln_estimated_ho`
- Cold 변수 추가 모델 학습 피처: `ln_estimated_ho + artist_meta_total_works`
- Cold 테스트 피처: 학습 피처와 같은 컬럼 사용, `artist_name_ko` 제외
- 연결 키: `_track6_row_id`
- HTML 일지: `experiment_log.html`
- 작가 메타 데이터셋: 기본 split은 유지하고, 메타 결측 때문에 작품을 제거하지 않음
- 작가 메타 원값 피처: `artist_meta_total_works`
- 작가 메타 결측 피처: `artist_meta_total_works_is_missing`
- 결측 비교: 전체 / artist_meta_total_works 값이 있는 작품 / artist_meta_total_works 값이 비어 있는 작품 구간 성능을 따로 기록
- 작가 메타 판단: 예측 성능 개선이 확인될 때만 결측 처리와 추가 수집을 검토


## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
