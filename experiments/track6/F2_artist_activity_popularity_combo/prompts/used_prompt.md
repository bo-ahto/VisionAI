# F2 실험 프롬프트

- 실험 목적: 작품 수, 판매 중 작품 수, 팔로워 수, 주요 작가 여부가 시장 노출 효과를 설명하는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 활동량 + 인지도: `artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1` - 등록/판매 노출량과 인지도 정보 조합
- 활동량 + 인지도 + 결측: `artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing` - 활동량/인지도 조합에 결측 상태를 함께 반영

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
