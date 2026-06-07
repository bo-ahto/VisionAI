# F1 실험 프롬프트

- 실험 목적: 작가 생년과 전시 경력 횟수를 함께 쓰면 세대/경력 가격대 차이를 더 잘 설명하는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 생년 + 전시 경력: `artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count` - 생년과 개인전/그룹전/아트페어 횟수 조합
- 생년 + 전시 경력 + 결측: `artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_exhibition_available_count, artist_meta_birth_year_is_missing, artist_exhibition_solo_count_is_missing, artist_exhibition_group_count_is_missing, artist_exhibition_fair_count_is_missing` - 생년/전시 횟수 조합에 결측 상태를 함께 반영

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
