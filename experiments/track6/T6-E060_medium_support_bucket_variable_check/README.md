# T6-E060 재료+지지체 조합 변수 영향 확인

- 단계: 기본 피처 정의 - 개별 변수 확인
- 가설: 재료와 지지체 조합 변수는 재료나 지지체를 따로 쓰는 것보다 가격 예측에 영향을 미친다.
- 확인 변수: `nant_material_support_bucket`
- 테스트 모델: Warm `Huber / Linear Regression / Ridge`, Cold `Huber / Quantile-LAD / LightGBM`
- Warm 기준 모델 학습 피처: `artist_name_ko + ln_estimated_ho + nant_material_idx + nant_tool + support_category`
- Warm 변수 추가 모델 학습 피처: `artist_name_ko + ln_estimated_ho + nant_material_support_bucket`
- Warm 테스트 피처: 학습 피처와 같은 컬럼 사용
- Cold 기준 모델 학습 피처: `ln_estimated_ho + nant_material_idx + nant_tool + support_category`
- Cold 변수 추가 모델 학습 피처: `ln_estimated_ho + nant_material_support_bucket`
- Cold 테스트 피처: 학습 피처와 같은 컬럼 사용, `artist_name_ko` 제외
- 연결 키: `_track6_row_id`
- HTML 일지: `experiment_log.html`


## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
