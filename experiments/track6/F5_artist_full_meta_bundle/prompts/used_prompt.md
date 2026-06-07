# F5 실험 프롬프트

- 실험 목적: 작가명 없이 전체 작가 메타 묶음만으로 가격 예측이 가능한지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 전체 작가 메타 묶음: `artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_exhibition_available_count, artist_meta_birth_year_is_missing, artist_exhibition_solo_count_is_missing, artist_exhibition_group_count_is_missing, artist_exhibition_fair_count_is_missing, artist_meta_nationality_is_missing, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing` - 생년/전시/국적/활동량/인지도/정보량 전체 조합

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
