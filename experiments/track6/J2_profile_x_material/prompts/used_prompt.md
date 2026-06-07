# J2 실험 프롬프트

- 실험 목적: 작가의 세대/경력 단계에 따라 재료 효과가 다르게 나타나는지 확인
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
- J2 기준: 세대/경력 + 재료: `artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, nant_material_idx, nant_tool` - 개별 효과만 사용
- J2 교차항: 세대/경력 x 재료: `artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, nant_material_idx, nant_tool` - 세대/경력별 재료 프리미엄 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
