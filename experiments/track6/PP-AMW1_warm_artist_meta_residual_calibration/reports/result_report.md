# PP-AMW1 Warm 작가 메타 기반 잔차 보정 실험 결과

## 1. 실행 요약

- 기준 후보: PP-V8 compact_blend_mape_guarded
- 방식: validation 잔차 중앙값 또는 Ridge 잔차 모델로 작가 메타 기반 보정값 생성
- test 정답은 보정값 생성에 사용하지 않음

핵심 결과:
- 기준 test MdAPE 0.1632, MAPE 0.2816, p95_APE 0.9311
- 전체 후보 중 test MAPE 최선: seg_for_sale_bin_min30_cap0p05_k20 / MdAPE 0.1619, MAPE 0.2797, p95_APE 0.9288
- validation 선택 후보 중 test 최선: seg_for_sale_bin_min30_cap0p05_k20 / MdAPE 0.1619, MAPE 0.2797, p95_APE 0.9288

판단:
- 작가 메타 기반 보정은 일부 구간에서 개선 신호가 있는지 확인한다.
- validation에서 선택한 후보가 test에서도 개선되면 후속 반복 split 검증 대상으로 둔다.
- 개선이 test에서만 나타나거나 p95가 악화되면 운영 후보가 아니라 분석 근거로만 둔다.

## 2. 작가 메타 커버리지

| split | n | artist_meta_birth_year_coverage | artist_meta_total_works_coverage | artist_meta_for_sale_works_coverage | artist_meta_followers_coverage | artist_meta_for_sale_ratio_coverage | artist_meta_career_age_coverage | artist_meta_career_stage_coverage | artist_meta_total_works_log_coverage | artist_meta_for_sale_works_log_coverage | artist_meta_followers_log_coverage | artist_meta_available_count_coverage | artist_meta_completeness_score_coverage | artist_meta_source_coverage | artist_meta_nationality_coverage | artist_meta_nationality_ko_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 519 | 0.2023 | 0.5915 | 0.1715 | 0.5915 | 0.4200 | 0.0000 | 0.4200 | 0.5915 | 0.1715 | 0.5915 | 0.5915 | 0.5915 | 0.5915 | 0.5915 | 0.5915 |
| test | 607 | 0.1845 | 0.6409 | 0.1862 | 0.6409 | 0.4547 | 0.0000 | 0.4547 | 0.6409 | 0.1862 | 0.6409 | 0.6409 | 0.6409 | 0.6409 | 0.6409 | 0.6409 |

## 3. validation 선택 후보의 validation/test 지표

| experiment_id | candidate | scope | split | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW1 | baseline_ppv8_compact_blend_mape_guarded | warm | test | 607 | 0.4028 | 0.1632 | 0.2816 | 0.9311 | 0.7364 | 0.8600 | 6 | 7 | 0.9966 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| PP-AMW1 | baseline_ppv8_compact_blend_mape_guarded | warm | validation | 519 | 0.3721 | 0.1544 | 0.2544 | 0.8084 | 0.7225 | 0.8882 | 4 | 4 | 1.0051 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p05_k20 | warm | test | 607 | 0.4020 | 0.1693 | 0.2807 | 0.8948 | 0.7331 | 0.8600 | 6 | 7 | 0.9914 | 0.0061 | -0.0009 | -0.0363 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p05_k20 | warm | validation | 519 | 0.3713 | 0.1532 | 0.2526 | 0.7880 | 0.7187 | 0.8882 | 4 | 4 | 1.0004 | -0.0012 | -0.0018 | -0.0204 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p08_k20 | warm | test | 607 | 0.4020 | 0.1693 | 0.2807 | 0.8948 | 0.7331 | 0.8600 | 6 | 7 | 0.9914 | 0.0061 | -0.0009 | -0.0363 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p08_k20 | warm | validation | 519 | 0.3713 | 0.1532 | 0.2526 | 0.7880 | 0.7187 | 0.8882 | 4 | 4 | 1.0004 | -0.0012 | -0.0018 | -0.0204 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p15_k20 | warm | test | 607 | 0.4020 | 0.1693 | 0.2807 | 0.8948 | 0.7331 | 0.8600 | 6 | 7 | 0.9914 | 0.0061 | -0.0009 | -0.0363 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p15_k20 | warm | validation | 519 | 0.3713 | 0.1532 | 0.2526 | 0.7880 | 0.7187 | 0.8882 | 4 | 4 | 1.0004 | -0.0012 | -0.0018 | -0.0204 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p1_k20 | warm | test | 607 | 0.4020 | 0.1693 | 0.2807 | 0.8948 | 0.7331 | 0.8600 | 6 | 7 | 0.9914 | 0.0061 | -0.0009 | -0.0363 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min20_cap0p1_k20 | warm | validation | 519 | 0.3713 | 0.1532 | 0.2526 | 0.7880 | 0.7187 | 0.8882 | 4 | 4 | 1.0004 | -0.0012 | -0.0018 | -0.0204 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min30_cap0p05_k20 | warm | test | 607 | 0.4020 | 0.1693 | 0.2807 | 0.8948 | 0.7331 | 0.8600 | 6 | 7 | 0.9914 | 0.0061 | -0.0009 | -0.0363 | -0.0008 |
| PP-AMW1 | seg_birth_x_career_min30_cap0p05_k20 | warm | validation | 519 | 0.3713 | 0.1532 | 0.2526 | 0.7880 | 0.7187 | 0.8882 | 4 | 4 | 1.0008 | -0.0012 | -0.0018 | -0.0204 | -0.0008 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p03_k20 | warm | test | 607 | 0.4032 | 0.1634 | 0.2811 | 0.9286 | 0.7298 | 0.8600 | 6 | 7 | 0.9923 | 0.0002 | -0.0005 | -0.0025 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p03_k20 | warm | validation | 519 | 0.3716 | 0.1506 | 0.2523 | 0.7662 | 0.7245 | 0.8882 | 4 | 5 | 1.0000 | -0.0037 | -0.0021 | -0.0422 | -0.0005 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p05_k20 | warm | test | 607 | 0.4034 | 0.1641 | 0.2815 | 0.9288 | 0.7282 | 0.8600 | 6 | 7 | 0.9916 | 0.0010 | -0.0001 | -0.0023 | 0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p05_k20 | warm | validation | 519 | 0.3715 | 0.1511 | 0.2521 | 0.7662 | 0.7225 | 0.8882 | 4 | 5 | 1.0005 | -0.0033 | -0.0022 | -0.0422 | -0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p08_k20 | warm | test | 607 | 0.4034 | 0.1641 | 0.2815 | 0.9288 | 0.7282 | 0.8600 | 6 | 7 | 0.9916 | 0.0010 | -0.0001 | -0.0023 | 0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p08_k20 | warm | validation | 519 | 0.3715 | 0.1511 | 0.2521 | 0.7662 | 0.7225 | 0.8882 | 4 | 5 | 1.0005 | -0.0033 | -0.0022 | -0.0422 | -0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p15_k20 | warm | test | 607 | 0.4034 | 0.1641 | 0.2815 | 0.9288 | 0.7282 | 0.8600 | 6 | 7 | 0.9916 | 0.0010 | -0.0001 | -0.0023 | 0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p15_k20 | warm | validation | 519 | 0.3715 | 0.1511 | 0.2521 | 0.7662 | 0.7225 | 0.8882 | 4 | 5 | 1.0005 | -0.0033 | -0.0022 | -0.0422 | -0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p1_k20 | warm | test | 607 | 0.4034 | 0.1641 | 0.2815 | 0.9288 | 0.7282 | 0.8600 | 6 | 7 | 0.9916 | 0.0010 | -0.0001 | -0.0023 | 0.0006 |
| PP-AMW1 | seg_for_sale_bin_min20_cap0p1_k20 | warm | validation | 519 | 0.3715 | 0.1511 | 0.2521 | 0.7662 | 0.7225 | 0.8882 | 4 | 5 | 1.0005 | -0.0033 | -0.0022 | -0.0422 | -0.0006 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p03_k20 | warm | test | 607 | 0.4031 | 0.1617 | 0.2798 | 0.9286 | 0.7315 | 0.8616 | 6 | 7 | 0.9898 | -0.0014 | -0.0018 | -0.0025 | 0.0003 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p03_k20 | warm | validation | 519 | 0.3722 | 0.1511 | 0.2521 | 0.7662 | 0.7264 | 0.8882 | 4 | 5 | 0.9992 | -0.0033 | -0.0023 | -0.0422 | 0.0001 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p03_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p03_k50 | warm | validation | 519 | 0.3721 | 0.1508 | 0.2525 | 0.7667 | 0.7264 | 0.8882 | 4 | 4 | 1.0003 | -0.0036 | -0.0019 | -0.0416 | 0.0001 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p05_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p05_k20 | warm | validation | 519 | 0.3722 | 0.1525 | 0.2519 | 0.7662 | 0.7264 | 0.8882 | 4 | 5 | 0.9992 | -0.0019 | -0.0025 | -0.0422 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p05_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p05_k50 | warm | validation | 519 | 0.3721 | 0.1508 | 0.2525 | 0.7667 | 0.7264 | 0.8882 | 4 | 4 | 1.0003 | -0.0036 | -0.0019 | -0.0416 | 0.0001 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p08_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p08_k20 | warm | validation | 519 | 0.3722 | 0.1525 | 0.2519 | 0.7662 | 0.7264 | 0.8882 | 4 | 5 | 0.9992 | -0.0019 | -0.0025 | -0.0422 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p08_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p08_k50 | warm | validation | 519 | 0.3721 | 0.1508 | 0.2525 | 0.7667 | 0.7264 | 0.8882 | 4 | 4 | 1.0003 | -0.0036 | -0.0019 | -0.0416 | 0.0001 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p15_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p15_k20 | warm | validation | 519 | 0.3722 | 0.1525 | 0.2519 | 0.7662 | 0.7264 | 0.8882 | 4 | 5 | 0.9992 | -0.0019 | -0.0025 | -0.0422 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p15_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p15_k50 | warm | validation | 519 | 0.3721 | 0.1508 | 0.2525 | 0.7667 | 0.7264 | 0.8882 | 4 | 4 | 1.0003 | -0.0036 | -0.0019 | -0.0416 | 0.0001 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p1_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p1_k20 | warm | validation | 519 | 0.3722 | 0.1525 | 0.2519 | 0.7662 | 0.7264 | 0.8882 | 4 | 5 | 0.9992 | -0.0019 | -0.0025 | -0.0422 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p1_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p1_k50 | warm | validation | 519 | 0.3721 | 0.1508 | 0.2525 | 0.7667 | 0.7264 | 0.8882 | 4 | 4 | 1.0003 | -0.0036 | -0.0019 | -0.0416 | 0.0001 |

## 4. test 기준 상위 후보

| experiment_id | candidate | scope | split | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p05_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p08_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p1_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p15_k20 | warm | test | 607 | 0.4032 | 0.1619 | 0.2797 | 0.9288 | 0.7315 | 0.8616 | 6 | 7 | 0.9887 | -0.0013 | -0.0019 | -0.0023 | 0.0004 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p03_k20 | warm | test | 607 | 0.4031 | 0.1617 | 0.2798 | 0.9286 | 0.7315 | 0.8616 | 6 | 7 | 0.9898 | -0.0014 | -0.0018 | -0.0025 | 0.0003 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p03_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p05_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p08_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p1_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_for_sale_bin_min30_cap0p15_k50 | warm | test | 607 | 0.4030 | 0.1621 | 0.2801 | 0.9289 | 0.7315 | 0.8616 | 6 | 7 | 0.9901 | -0.0011 | -0.0016 | -0.0022 | 0.0002 |
| PP-AMW1 | seg_artist_meta_source_grouped_min20_cap0p03_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min20_cap0p05_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min20_cap0p08_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min20_cap0p1_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min20_cap0p15_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min30_cap0p03_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min30_cap0p05_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min30_cap0p08_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min30_cap0p1_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min30_cap0p15_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min50_cap0p03_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min50_cap0p05_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min50_cap0p08_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min50_cap0p1_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |
| PP-AMW1 | seg_artist_meta_source_grouped_min50_cap0p15_k20 | warm | test | 607 | 0.4025 | 0.1611 | 0.2804 | 0.9238 | 0.7331 | 0.8616 | 6 | 7 | 0.9905 | -0.0021 | -0.0013 | -0.0073 | -0.0003 |

## 5. 산출물

- `outputs/metrics.csv`
- `outputs/selected_candidate_metrics.csv`
- `outputs/test_top_candidates.csv`
- `outputs/artist_meta_coverage.csv`
- `outputs/correction_maps.csv`
- `outputs/predictions.csv`
- `reports/result_report.md`
- `reports/result_report.html`
