# F4 실험 프롬프트

- 실험 목적: 활동량/인지도 정보에 메타 정보량 피처를 더하면 가격 예측과 신뢰도 판단에 도움이 되는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 활동량 + 인지도 + 정보량: `artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing` - F2 조합에 작가 메타 보유 개수와 완성도 점수를 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
