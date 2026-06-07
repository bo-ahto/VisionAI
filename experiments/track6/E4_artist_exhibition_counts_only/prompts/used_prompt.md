# E4 실험 프롬프트

- 실험 목적: 개인전, 그룹전, 아트페어 횟수가 가격 차이를 설명할 수 있는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 개인전 횟수: `artist_exhibition_solo_count` - 개인전 횟수만 사용
- 그룹전 횟수: `artist_exhibition_group_count` - 그룹전 횟수만 사용
- 아트페어 횟수: `artist_exhibition_fair_count` - 아트페어 횟수만 사용
- 전시 총횟수: `artist_exhibition_total_count` - 개인전/그룹전/아트페어 합산 횟수 사용
- 전시 횟수 묶음 + 결측: `artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_exhibition_available_count, artist_exhibition_solo_count_is_missing, artist_exhibition_group_count_is_missing, artist_exhibition_fair_count_is_missing` - 전시 횟수 3종과 정보 보유 상태를 함께 사용

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
