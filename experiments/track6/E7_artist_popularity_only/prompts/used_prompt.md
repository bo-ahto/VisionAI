# E7 실험 프롬프트

- 실험 목적: 팔로워 수와 주요 작가 여부가 가격 예측에 도움 되는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 팔로워 수: `artist_meta_followers` - 플랫폼 팔로워 수만 사용
- 주요 작가 여부: `artist_meta_is_p1` - 플랫폼이 표시한 주요 작가 여부만 사용
- 인지도 묶음 + 결측: `artist_meta_followers, artist_meta_is_p1, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing` - 팔로워 수, 주요 작가 여부, 결측 상태를 함께 사용

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
