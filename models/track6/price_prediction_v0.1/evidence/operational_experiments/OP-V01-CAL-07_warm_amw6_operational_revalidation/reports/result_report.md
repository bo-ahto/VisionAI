# OP-V01-CAL-07 Warm 작가 메타 보정 운영 재검증 결과

## 1. 실행 요약

- 작성일: 2026-06-07T12:42:31
- 실험 목적: PP-AMW6 반복 재검증 후보를 v0.1 운영 0604 출력 기준으로 재확인
- 학습 데이터: 기존 Warm validation split
- 외부 확인 데이터: 0604 신규 라벨 Warm 행
- 0604 라벨 사용 방식: 보정 학습에는 사용하지 않고 평가에만 사용

## 2. 핵심 판단

- 0604 신규 라벨은 학습에 쓰지 않은 외부 확인용이다.
- service_primary 기준 baseline MdAPE/MAPE/p95: 0.2298/0.3359/0.9273.
- service_primary 기준 0604 최상위 후보: service_primary_ppv8__meta_core_test_twin MdAPE/MAPE/p95 0.2255/0.3323/0.9257.
- report_70_30 기준 0604 최상위 후보: report_70_30__birth_generation_segment_guard MdAPE/MAPE/p95 0.2774/0.3759/0.9872.
- 판단은 MdAPE 단독이 아니라 MAPE와 p95_APE 안정성을 함께 보고 내린다.


## 3. service_primary 기준 0604 후보 순위

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_excluding_under_50_usd:service_primary_ppv8 | service_primary_ppv8__meta_core_test_twin | 829 | 0.2255 | 0.3323 | 0.9257 | 0.7110 | -0.0043 | -0.0035 | -0.0017 | 4 | 56 |
| 0604_excluding_under_50_usd:service_primary_ppv8 | service_primary_ppv8__meta_core_validation_mdape | 829 | 0.2255 | 0.3323 | 0.9257 | 0.7110 | -0.0043 | -0.0035 | -0.0017 | 4 | 56 |
| 0604_excluding_under_50_usd:service_primary_ppv8 | service_primary_ppv8__birth_generation_segment_guard | 829 | 0.2280 | 0.3332 | 0.9228 | 0.7106 | -0.0018 | -0.0027 | -0.0046 | 4 | 58 |
| 0604_excluding_under_50_usd:service_primary_ppv8 | service_primary_ppv8__external_gallery_exhibition_diagnostic | 829 | 0.2275 | 0.3342 | 0.9263 | 0.7121 | -0.0023 | -0.0017 | -0.0010 | 4 | 55 |
| 0604_excluding_under_50_usd:service_primary_ppv8 | service_primary_ppv8__baseline | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.0000 | 0.0000 | 0.0000 | 4 | 58 |

## 4. report_70_30 기준 0604 후보 순위

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_excluding_under_50_usd:report_70_30 | report_70_30__birth_generation_segment_guard | 829 | 0.2774 | 0.3759 | 0.9872 | 1.3093 | -0.0005 | -0.0015 | 0.0001 | 8 | 81 |
| 0604_excluding_under_50_usd:report_70_30 | report_70_30__baseline | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 | 8 | 79 |
| 0604_excluding_under_50_usd:report_70_30 | report_70_30__meta_core_validation_mdape | 829 | 0.2849 | 0.3791 | 0.9874 | 1.3151 | 0.0069 | 0.0017 | 0.0003 | 8 | 82 |
| 0604_excluding_under_50_usd:report_70_30 | report_70_30__meta_core_test_twin | 829 | 0.2849 | 0.3791 | 0.9874 | 1.3150 | 0.0069 | 0.0018 | 0.0003 | 8 | 82 |
| 0604_excluding_under_50_usd:report_70_30 | report_70_30__external_gallery_exhibition_diagnostic | 829 | 0.2773 | 0.3798 | 0.9874 | 1.3156 | -0.0007 | 0.0024 | 0.0003 | 8 | 82 |

## 5. 50달러 미만 포함 지표

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_all_numeric:report_70_30 | report_70_30__birth_generation_segment_guard | 837 | 0.2816 | 31.9967 | 0.9996 | 1.4438 | -0.0020 | -0.2912 | -0.0000 |
| 0604_all_numeric:report_70_30 | report_70_30__baseline | 837 | 0.2835 | 32.2879 | 0.9996 | 1.4463 | 0.0000 | 0.0000 | 0.0000 |
| 0604_all_numeric:report_70_30 | report_70_30__meta_core_validation_mdape | 837 | 0.2863 | 33.0198 | 0.9996 | 1.4498 | 0.0028 | 0.7319 | -0.0000 |
| 0604_all_numeric:report_70_30 | report_70_30__meta_core_test_twin | 837 | 0.2863 | 33.0199 | 0.9996 | 1.4497 | 0.0028 | 0.7320 | -0.0000 |
| 0604_all_numeric:report_70_30 | report_70_30__external_gallery_exhibition_diagnostic | 837 | 0.2839 | 33.0206 | 0.9996 | 1.4502 | 0.0003 | 0.7327 | 0.0000 |
| 0604_all_numeric:service_primary_ppv8 | service_primary_ppv8__birth_generation_segment_guard | 837 | 0.2306 | 14.1482 | 0.9820 | 0.9179 | -0.0036 | -0.1370 | -0.0024 |
| 0604_all_numeric:service_primary_ppv8 | service_primary_ppv8__baseline | 837 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 0.0000 | 0.0000 | 0.0000 |
| 0604_all_numeric:service_primary_ppv8 | service_primary_ppv8__meta_core_test_twin | 837 | 0.2277 | 14.6082 | 0.9787 | 0.9198 | -0.0065 | 0.3230 | -0.0058 |
| 0604_all_numeric:service_primary_ppv8 | service_primary_ppv8__meta_core_validation_mdape | 837 | 0.2277 | 14.6083 | 0.9787 | 0.9199 | -0.0065 | 0.3230 | -0.0058 |
| 0604_all_numeric:service_primary_ppv8 | service_primary_ppv8__external_gallery_exhibition_diagnostic | 837 | 0.2299 | 14.6176 | 0.9785 | 0.9208 | -0.0043 | 0.3324 | -0.0059 |

## 6. 피처 커버리지

| feature | coverage | non_null_n | n | scope |
| --- | --- | --- | --- | --- |
| artist_meta_birth_year | 0.4185 | 742 | 1773 | historical_artist_lookup |
| artist_meta_total_works | 0.8291 | 1470 | 1773 | historical_artist_lookup |
| artist_meta_for_sale_works | 0.4653 | 825 | 1773 | historical_artist_lookup |
| artist_meta_followers | 0.8291 | 1470 | 1773 | historical_artist_lookup |
| artist_exhibition_total_count | 0.3790 | 672 | 1773 | historical_artist_lookup |
| gallery_tier_raw_numeric | 0.3796 | 673 | 1773 | historical_artist_lookup |
| gallery_tier_validated_score | 0.0028 | 5 | 1773 | historical_artist_lookup |
| artist_meta_birth_year | 0.8220 | 688 | 837 | 0604:service_primary_ppv8 |
| artist_meta_total_works | 0.9952 | 833 | 837 | 0604:service_primary_ppv8 |
| artist_meta_for_sale_works | 0.9892 | 828 | 837 | 0604:service_primary_ppv8 |
| artist_meta_followers | 0.9952 | 833 | 837 | 0604:service_primary_ppv8 |
| artist_exhibition_total_count | 0.0227 | 19 | 837 | 0604:service_primary_ppv8 |
| gallery_tier_raw_numeric | 0.0227 | 19 | 837 | 0604:service_primary_ppv8 |
| gallery_tier_validated_score | 0.0000 | 0 | 837 | 0604:service_primary_ppv8 |
| artist_meta_birth_year | 0.8220 | 688 | 837 | 0604:report_70_30 |
| artist_meta_total_works | 0.9952 | 833 | 837 | 0604:report_70_30 |
| artist_meta_for_sale_works | 0.9892 | 828 | 837 | 0604:report_70_30 |
| artist_meta_followers | 0.9952 | 833 | 837 | 0604:report_70_30 |
| artist_exhibition_total_count | 0.0227 | 19 | 837 | 0604:report_70_30 |
| gallery_tier_raw_numeric | 0.0227 | 19 | 837 | 0604:report_70_30 |
| gallery_tier_validated_score | 0.0000 | 0 | 837 | 0604:report_70_30 |

## 7. 산출물

- `outputs/0604_candidate_metrics.csv`
- `outputs/0604_predictions_with_amw6_candidates.csv`
- `outputs/feature_coverage.csv`
- `outputs/pp_amw6_historical_test_once_metrics.csv`
- `outputs/pp_amw6_historical_bootstrap_summary.csv`
