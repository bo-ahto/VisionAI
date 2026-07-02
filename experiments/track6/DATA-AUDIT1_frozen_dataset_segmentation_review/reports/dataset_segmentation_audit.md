# DATA-AUDIT1 frozen dataset segmentation review

## 목적

현재 official v0.1 계열 실험의 기준인 frozen split을 대상으로, 모델 성능 개선을 위해 데이터셋을 더 세분화할 후보와 제거/정리할 feature 후보를 점검했다.

이 감사는 모델을 새로 학습하지 않는다. 데이터셋 구조, 분포, 누수 가능성, 세그먼트 차이를 확인하는 사전 진단이다.

## 기준 데이터

`models/track6/price_prediction_v0.1/data/training/track6_split`

## 1. Split 요약

| split | rows | artist_key_n | artist_name_ko_n | ln_price_mean | ln_price_std | price_median | price_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | 26914 | 1773 | 1713 | 15.01577 | 1.381571 | 3008400.0 | 42429740.0 |
| val_warm | 519 | 178 | 178 | 15.003348 | 1.324387 | 3036000.0 | 34721426.0 |
| test_warm | 607 | 207 | 205 | 14.976376 | 1.362833 | 2829000.0 | 39229260.0 |
| val_cold | 2753 | 172 | 168 | 14.804036 | 1.173045 | 2622000.0 | 19449996.0 |
| test_cold | 3099 | 200 | 189 | 15.090755 | 1.314497 | 3450000.0 | 32307180.0 |

## 2. 무결성 검사

| check | status | detail |
| --- | --- | --- |
| val_warm_warm_min_history_gte5 | PASS | min=5 |
| test_warm_warm_min_history_gte5 | PASS | min=5 |
| val_cold_cold_artist_key_overlap_train | PASS | 0 |
| val_cold_cold_artist_name_overlap_train | PASS | 0 |
| val_cold_cold_artist_name_orig_overlap_train | PASS | 0 |
| test_cold_cold_artist_key_overlap_train | PASS | 0 |
| test_cold_cold_artist_name_overlap_train | PASS | 0 |
| test_cold_cold_artist_name_orig_overlap_train | PASS | 0 |
| cold_feature_no_same_artist_leakage_columns | PASS |  |

## 3. 결측률이 높은 train 컬럼

| column | missing_rate | nunique | top_value | top_share |
| --- | --- | --- | --- | --- |
| cleaning_exclude_reasons | 1.0 | 0 |  | 0.0 |
| artist_meta_career_age | 1.0 | 0 |  | 0.0 |
| artist_entity_suffix | 0.977335 | 3 | A | 0.018318 |
| artist_meta_nationality_ko | 0.94345 | 32 | 대한민국 | 0.040054 |
| artist_meta_birth_year | 0.698373 | 84 | 1973.0 | 0.023557 |
| artist_meta_for_sale_works | 0.692502 | 88 | 10.0 | 0.018503 |
| artist_meta_nationality | 0.612581 | 49 | South Korean | 0.255146 |

## 4. 고유값이 많거나 희소 level이 많은 범주형 컬럼

희소 level이 많으면 모델이 의미 있는 패턴보다 개별 값에 끌릴 수 있다. 이 경우 bucket화, 상위 level만 유지, 또는 제거 실험 대상이다.

| column | nunique_train | top_value | top_share | rare_level_row_share_lt10 | review_hint |
| --- | --- | --- | --- | --- | --- |
| source_artwork_id | 26914 | 13458973 | 3.7e-05 | 1.0 | bucket_or_remove |
| artwork_url | 26713 | missing | 0.007505 | 0.992495 | bucket_or_remove |
| image_url | 24548 | missing | 0.087947 | 0.912053 | bucket_or_remove |
| title_raw | 21710 | Untitled | 0.006911 | 0.902504 | bucket_or_remove |
| collected_material_raw | 2642 | acrylic | 0.19841 | 0.183919 | bucket_or_remove |
| artist_name_standardized | 1820 | hyera lee | 0.025972 | 0.166307 | bucket_or_remove |
| artist_key | 1773 | hyera lee | 0.025972 | 0.161366 | bucket_or_remove |
| artist_name_ko | 1713 | 이혜라 | 0.025972 | 0.15635 | bucket_or_remove |
| artist_name_ko_orig | 1693 | 이혜라 | 0.025972 | 0.154009 | bucket_or_remove |
| medium_support_bucket | 77 | acrylic__canvas | 0.252805 | 0.002564 | ok |
| artist_meta_nationality | 50 | missing | 0.612581 | 0.003455 | ok |
| artist_meta_nationality_ko | 33 | missing | 0.94345 | 0.001858 | ok |
| medium_category | 18 | mixed_media | 0.347217 | 0.0 | ok |
| nant_tool | 17 | 아크릴 | 0.367021 | 0.0 | ok |
| support_category | 9 | canvas | 0.649476 | 0.0 | ok |
| nant_support | 9 | 캔버스 | 0.680204 | 0.0 | ok |
| price_band_train_q | 5 | price_q1 | 0.201196 | 0.0 | ok |
| area_band_train_q | 5 | area_q2 | 0.201271 | 0.0 | ok |
| history_count_band | 5 | 30_plus | 0.589284 | 0.0 | ok |
| track4_source | 4 | saatchi | 0.605075 | 0.0 | ok |
| artist_entity_suffix | 4 | missing | 0.977335 | 7.4e-05 | ok |
| artist_meta_source | 4 | saatchi | 0.605075 | 0.0 | ok |
| artist_meta_is_p1 | 3 | False | 0.902876 | 0.0 | ok |
| nant_material_note | 3 | rule_based_material_parse | 0.792487 | 0.0 | ok |
| nant_material_match_method | 3 | rule_material_parse | 0.792487 | 0.0 | ok |
| aspect_band | 3 | balanced | 0.967006 | 0.0 | ok |
| is_homonym | 2 | False | 0.977335 | 0.0 | ok |
| has_depth | 2 | True | 0.733782 | 0.0 | ok |
| is_3d_candidate | 2 | False | 0.980605 | 0.0 | ok |
| is_high_price_candidate | 2 | False | 0.966783 | 0.0 | ok |

## 5. Train 대비 평가셋 분포 차이가 큰 세그먼트

`max_abs_share_diff`는 특정 값의 train 비중과 평가셋 비중 차이의 최댓값이다. 차이가 큰 컬럼은 별도 평가/라우팅/보정 후보가 된다.

| target_split | segment_column | max_abs_share_diff | largest_shift_value | train_share | target_share |
| --- | --- | --- | --- | --- | --- |
| test_cold | history_count_band | 1.0 | 0_cold | 0.0 | 1.0 |
| test_warm | history_count_band | 0.366879 | 30_plus | 0.589284 | 0.222405 |
| test_warm | track4_source | 0.15038 | saatchi | 0.605075 | 0.454695 |
| test_warm | artist_meta_source | 0.15038 | saatchi | 0.605075 | 0.454695 |
| test_warm | artist_meta_career_stage | 0.15038 | missing | 0.394925 | 0.545305 |
| test_warm | artist_meta_has_international | 0.15038 | True | 0.605075 | 0.454695 |
| test_warm | artist_meta_nationality | 0.148001 | missing | 0.612581 | 0.46458 |
| test_warm | has_depth | 0.10281 | False | 0.266218 | 0.369028 |
| val_cold | history_count_band | 1.0 | 0_cold | 0.0 | 1.0 |
| val_cold | artist_meta_career_stage | 0.132946 | 1.3257423551397811 | 0.0 | 0.132946 |
| val_warm | history_count_band | 0.35229 | 30_plus | 0.589284 | 0.236994 |
| val_warm | track4_source | 0.185037 | saatchi | 0.605075 | 0.420039 |
| val_warm | artist_meta_source | 0.185037 | saatchi | 0.605075 | 0.420039 |
| val_warm | artist_meta_career_stage | 0.185037 | missing | 0.394925 | 0.579961 |
| val_warm | artist_meta_has_international | 0.185037 | True | 0.605075 | 0.420039 |
| val_warm | artist_meta_nationality | 0.159787 | missing | 0.612581 | 0.452794 |
| val_warm | has_depth | 0.124918 | False | 0.266218 | 0.391137 |
| val_warm | nant_material_match_method | 0.100772 | rule_material_parse | 0.792487 | 0.691715 |

## 6. 세분화 후보 컬럼

`median_price_spread`가 크면 같은 컬럼 안의 값별 가격대 차이가 크다는 뜻이다. 이런 컬럼은 모델 입력으로 유지하거나 별도 bucket/세그먼트 기준으로 검토할 가치가 있다.

| segment_column | segment_count | max_segment_rows | median_price_spread | max_iqr |
| --- | --- | --- | --- | --- |
| artist_meta_career_stage | 20 | 1397 | 4.148188 | 1.951324 |
| price_band_train_q | 5 | 688 | 3.544576 | 1.163301 |
| nant_tool | 13 | 1232 | 3.092724 | 2.968905 |
| area_band_train_q | 5 | 834 | 2.777043 | 1.267604 |
| medium_support_bucket | 19 | 806 | 2.51743 | 3.994929 |
| medium_category | 9 | 1126 | 2.47015 | 2.003268 |
| artist_meta_nationality | 5 | 1756 | 1.86796 | 2.040221 |
| support_category | 8 | 1849 | 1.333684 | 3.442019 |
| artist_meta_source | 4 | 1702 | 1.172108 | 2.713809 |
| track4_source | 4 | 1702 | 1.172108 | 2.713809 |
| nant_support | 7 | 1900 | 0.966726 | 2.479949 |
| nant_material_match_method | 2 | 2296 | 0.80866 | 1.973952 |
| has_depth | 2 | 2148 | 0.68213 | 2.079442 |
| artist_meta_has_international | 2 | 1702 | 0.68208 | 1.951324 |
| is_3d_candidate | 2 | 3057 | 0.678758 | 1.797474 |
| history_count_band | 4 | 3099 | 0.380703 | 1.925303 |
| artist_meta_is_p1 | 2 | 2887 | 0.336862 | 1.868064 |
| aspect_band | 2 | 2978 | 0.250515 | 1.890634 |
| is_extreme_aspect_ratio | 1 | 3099 | 0.198451 | 1.802213 |

## 7. 1차 판단

- Warm/Cold split 무결성과 Cold 누수 차단은 통과했다.
- 작가 메타 컬럼 중 결측이 큰 항목은 운영 입력 가능성과 함께 별도 검토가 필요하다.
- `artist_name_standardized`, `title_raw`, URL류, raw material 문자열처럼 고유값이 큰 컬럼은 직접 feature로 쓰기보다 정규화/bucket/embedding/검수 큐 대상이다.
- `track4_source`, 재료/지지체 계열, 면적/가격 band, 작가 메타 source 계열은 평가셋 분포 차이가 있는지 확인해 세그먼트별 성능 비교 후보로 삼는다.
- 다음 단계는 이 감사 결과에서 나온 후보 컬럼을 기준으로 feature 제거/추가/세분화 실험을 작은 실험군으로 나누어 실제 MdAPE, MAPE, p95 APE 변화를 확인하는 것이다.

## 산출물

| 파일 | 내용 |
|---|---|
| `outputs/split_summary.csv` | split별 row, 작가 수, 가격 분포 |
| `outputs/column_missing_cardinality.csv` | 컬럼별 결측률/고유값 수 |
| `outputs/feature_file_audit.csv` | Warm/Cold feature 파일 누수/상수/결측 점검 |
| `outputs/segment_target_summary.csv` | 세그먼트별 가격 분포 |
| `outputs/train_eval_segment_shift.csv` | train 대비 val/test 분포 차이 |
| `outputs/high_cardinality_review.csv` | 고유값/희소 level 많은 컬럼 |
| `outputs/candidate_split_columns.csv` | 세분화 후보 컬럼 요약 |
