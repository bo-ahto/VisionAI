# I1 실험 프롬프트

- 실험 목적: 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리
- 교차항은 설정 파일에 명시한 방식으로만 생성

## 사용 피처
- I1 기준: 호수 only: `ln_estimated_ho` - 최소 크기 피처만 사용
- I1 후보: 호수 + 세대/경력: `ln_estimated_ho, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count` - 작가명 없는 최소 메타 조합 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
