# J5 실험 프롬프트

- 실험 목적: 작가의 활동량/인지도에 따라 면적 효과가 다르게 나타나는지 확인
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
- J5 기준: 활동량/인지도 + 면적: `log_area, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1` - 개별 효과만 사용
- J5 교차항: 활동량/인지도 x 면적: `log_area, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_total_works_x_log_area, artist_meta_for_sale_works_x_log_area, artist_meta_followers_x_log_area, artist_meta_is_p1_x_log_area` - 시장 노출 수준별 대형작 프리미엄 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
