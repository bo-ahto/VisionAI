# I5 실험 프롬프트

- 실험 목적: 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인
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
- I5 기준: 작품 기본 피처: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support` - 호수 + 난트 재료/도구/지지체
- I5 후보: 작품 기본 피처 + 시장 노출/정보량: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score` - 활동량/인지도와 메타 정보량 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
