# E5 실험 프롬프트

- 실험 목적: 작가 국적 정보가 가격 차이를 설명할 수 있는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 국적 only: `artist_meta_nationality` - 작가 국적 범주값만 사용
- 국적 + 결측 여부: `artist_meta_nationality, artist_meta_nationality_is_missing` - 국적 값과 값이 없는 상태를 함께 사용

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
