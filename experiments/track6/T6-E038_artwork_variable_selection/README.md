# T6-E038 작품 변수 선정 실험 일지

- 상태: 예정
- 목적: 작품 변수 후보의 유의미성 검증
- 기준 데이터: `data/track6/track6_feature_candidates_name_corrected.csv`
- HTML 일지: `experiment_log.html`
- 기본 비교 모델군: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM

## 핵심 가설

- 가설 1: 호수는 작가명 없이도 가격대 구분에 도움이 됨
- 가설 2: 작품 변수는 호수만으로 설명되지 않는 가격 차이를 보완할 수 있음
- 가설 3: Warm과 Cold는 효과적인 작품 변수 조합이 다를 수 있음

## 작품 변수 선정 가설

- H1: 호수는 작가명 없이도 가격대 구분에 도움이 됨
- H2: 실제 크기 정보는 호수만 사용할 때보다 가격 예측을 개선함
- H3: 재료 정보는 기준 모델보다 가격 예측을 개선함
- H4: 지지체 정보는 기준 모델 + 재료 피처보다 가격 예측을 개선함
- H5: 깊이/3D 정보는 2D와 3D 작품을 구분해 예측하는 데 도움이 됨
- H6: 재료와 크기 조합 피처는 재료와 크기를 따로 넣는 것보다 가격 예측을 개선함
- H7: 단계적 피처 선택 방식은 전체 조합 탐색 없이도 기준 모델보다 좋은 피처 조합을 찾을 수 있음
- H8: Warm과 Cold는 동일한 작품 피처 조합보다 각각 다른 피처 조합을 사용할 때 성능이 좋아질 수 있음
- H9: 크기 대표값 중심 피처는 전체 크기 피처를 모두 쓰는 방식보다 예측 오차를 줄일 수 있음
- H10: 원본 재료 문구에는 표준 재료 분류가 담지 못한 가격 차이 설명 정보가 있을 수 있음
- H11: 작품 제목에는 에디션, 세트, 포스터 등 가격 차이를 설명하는 정보가 있을 수 있음
- H12: 극단적인 가로세로 비율 작품은 일반 작품과 가격 예측 오차 패턴이 다를 수 있음
- H13: 0에 가까운 깊이와 실제 3D에 가까운 깊이는 가격 차이를 다르게 설명할 수 있음
- H14: 난트 재료 분류 번호가 너무 세분화되어 있으면 그룹화했을 때 더 안정적인 가격 예측이 가능할 수 있음
- H15: 가격 예측에는 면적보다 긴 변 또는 짧은 변 정보가 더 도움이 될 수 있음

## 가설별 실험 일지

- 목록 페이지: `docs/track6/journals/artwork_feature_selection.html`
- `T6-E039`: H1 호수 기준 신호 확인
- `T6-E040`: H2 실제 크기 정보 추가 실험
- `T6-E041`: H3 재료 정보 추가 실험
- `T6-E042`: H4 지지체 정보 추가 실험
- `T6-E043`: H5 깊이/3D 정보 추가 실험
- `T6-E044`: H6 재료 x 크기 조합 피처 실험
- `T6-E045`: H7 단계적 피처 선택 절차 실험
- `T6-E046`: H8 Warm/Cold 작품 피처 분리 실험
- `T6-E047`: H9 크기 대표값 vs 전체 크기 피처 실험
- `T6-E048`: H10 원본 재료 문구 키워드 추가 실험
- `T6-E049`: H11 작품 제목 키워드 피처 실험
- `T6-E050`: H12 극단 가로세로 비율 플래그 실험
- `T6-E051`: H13 깊이 구간화 피처 실험
- `T6-E052`: H14 난트 재료 분류 그룹화 실험
- `T6-E053`: H15 긴 변/짧은 변 크기 피처 실험

## 정제 데이터 기준 변수 목록

- 기준 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 전체 컬럼: 48개
- 작가 관련 후보 변수: 11개
- 그림 관련 후보 변수: 15개
- 상세 목록: `outputs/variable_inventory.csv`

## 작가 관련 후보 변수

- `artist_name_ko`
- `artist_name_standardized`
- `artist_works_log`
- `artist_meta_nationality`
- `artist_meta_birth_year`
- `artist_meta_total_works`
- `artist_meta_for_sale_works`
- `artist_meta_followers`
- `artist_meta_career_stage`
- `artist_meta_is_p1`
- `artist_meta_has_international`

## 그림 관련 후보 변수

- `width_cm`
- `height_cm`
- `depth_cm`
- `area_cm2`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`
- `support_category`
- `nant_material_support_bucket`
- `is_extreme_aspect_ratio`
- `nant_support`
- `nant_tool`
- `nant_material_idx`

## 학습 입력 제외 변수

- 가격 정답: `price_krw`, `ln_price_krw`
- 가격 기반 위험 변수: `is_high_price_candidate`
- 출처/URL 변수: `track4_source`, `source_artwork_id`, `artwork_url`, `image_url`
- 관리 변수: `is_training_candidate`, `cleaning_exclude_reasons`, `nant_material_match_method`

## 실험 목적

- 호수 기준 신호 확인
- 실제 크기, 재료, 지지체, 깊이/3D 피처의 추가 효과 확인
- 같은 피처셋 안에서 모델 비교
- 피처 변환 효과와 모델 효과 분리
- Warm / Cold 모델 분리 필요 여부 확인
- Warm의 `artist_name_ko`는 작품 피처 실험 대상이 아니라 기준 모델 고정 조건으로만 사용

## 기준 모델

- Warm 기준 모델: `Huber`, `Linear Regression`, `Ridge`
- Cold 기준 모델: `Huber`, `Quantile / LAD`, `LightGBM`
- 기준 모델 선정 근거: T6-E017의 같은 피처셋 기준 결과
- Warm / Cold 분리 이유: 난이도와 사용 가능한 피처가 다름

## 결과 판단 기준

- 1순위: `median APE`가 낮아지는지 확인
- 2순위: `p95 APE`가 줄어드는지 확인
- 3순위: `Within-30`, `Within-50`이 높아지는지 확인
- 4순위: Warm / Cold에서 같은 방향으로 개선되는지 확인
- 5순위: 운영에서 입력 가능한 변수인지 확인

## 예정 산출물

- `data/warm_train_raw.csv`
- `data/warm_train_log.csv`
- `data/warm_test_raw.csv`
- `data/warm_test_log.csv`
- `data/cold_train_raw.csv`
- `data/cold_train_log.csv`
- `data/cold_test_raw.csv`
- `data/cold_test_log.csv`
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
