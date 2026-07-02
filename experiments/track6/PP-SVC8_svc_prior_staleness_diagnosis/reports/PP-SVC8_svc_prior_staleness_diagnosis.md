# PP-SVC8 svc 비교가격 prior의 0604 악화 원인 분해

- 작성일: 2026-06-07 20:23
- 목적: svc 비교가격 prior가 0604 신규 라벨에서 악화된 원인을 편향/분산/매칭이동으로 분해
- 주의: oracle bias 보정은 해당 영역 라벨을 사용한 상한 진단이며 배포 후보가 아님

## 1. 진단 결론

- 원인 귀속: **편향 아님(전역 bias 제거가 0604 MdAPE를 개선하지 못함); 매칭 이동(coverage shift) 주도(53%)**
- 0604 svc MdAPE 악화 0.1552 중 매칭이동 0.0827(53%), 그룹내 분산 0.0725(47%)
- 전역 bias 제거 후 0604 svc MdAPE: 0.3399 (원본 0.3072) → 편향 보정으로 회복 불가
- 함의: svc prior는 신규 작품에서 거친 매칭+고분산으로 점예측 직접 반영이 위험. 운영 기본값 pp_v8 유지가 타당. 개선은 비교군 prior 갱신/신뢰도 약화 후속 실험에서.

## 2. 영역 residual 요약 (svc vs pp_v8)

| region | model | n | bias_median | IQR | std | MdAPE | MAPE | p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | svc | 607 | -0.0027 | 0.3049 | 0.4175 | 0.1520 | 0.2942 | 0.9381 |
| test | ppv8 | 607 | 0.0034 | 0.3236 | 0.4028 | 0.1632 | 0.2816 | 0.9311 |
| 0604 | svc | 829 | 0.0829 | 0.7351 | 1.6404 | 0.3072 | 0.4318 | 0.9998 |
| 0604 | ppv8 | 829 | 0.0703 | 0.4954 | 0.6921 | 0.2298 | 0.3359 | 0.9273 |

## 3. 편향 제거 oracle (상한 진단, 비배포)

| region | svc_MdAPE | svc_MAPE | global_bias | svc_plus_global_bias_MdAPE | svc_plus_global_bias_MAPE | svc_plus_level_bias_MdAPE | svc_plus_level_bias_MAPE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 0.1520 | 0.2942 | -0.0027 | 0.1524 | 0.2934 | 0.1518 | 0.2950 |
| 0604 | 0.3072 | 0.4318 | 0.0829 | 0.3399 | 0.4610 | 0.3082 | 0.4839 |

## 4. 매칭 레벨/커버리지 이동

| field | category | test_pct | 0604_pct |
| --- | --- | --- | --- |
| svc_group_level | artist | 48.6000 | 49.7000 |
| svc_group_level | artist_medium_support_size | 40.6900 | 10.9800 |
| svc_group_level | artist_size | 10.7100 | 27.0200 |
| svc_group_level | global | 0.0000 | 2.1700 |
| svc_group_level | medium_size | 0.0000 | 2.1700 |
| svc_group_level | medium_support_size | 0.0000 | 7.9600 |
| svc_coverage_tier | fallback_global | 0.0000 | 2.1700 |
| svc_coverage_tier | high_n | 2.8000 | 10.4900 |
| svc_coverage_tier | low_n | 78.9100 | 68.6400 |
| svc_coverage_tier | medium_n | 18.2900 | 18.7000 |

## 5. 레벨 통제 분산 (매칭 이동 통제 후 staleness)

| svc_group_level | test_n | test_svc_IQR | test_svc_std | test_svc_MdAPE | 0604_n | 0604_svc_IQR | 0604_svc_std | 0604_svc_MdAPE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist | 295 | 0.3885 | 0.4860 | 0.1927 | 412 | 0.7271 | 2.0505 | 0.3378 |
| artist_medium_support_size | 247 | 0.2064 | 0.2605 | 0.0980 | 91 | 0.2977 | 0.7667 | 0.1429 |
| artist_size | 65 | 0.4279 | 0.5442 | 0.2158 | 224 | 0.7065 | 1.2081 | 0.2475 |

## 6. mix vs within 분해

| fixed_test_svc_MdAPE | ops_0604_svc_MdAPE | ops_0604_svc_at_fixed_mix_MdAPE | ops_0604_svc_at_fixed_mix_MAPE | total_gap_MdAPE | mix_shift_part_MdAPE | within_level_part_MdAPE | mix_share_pct | within_share_pct | resample_draws |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1520 | 0.3072 | 0.2245 | 0.3568 | 0.1552 | 0.0827 | 0.0725 | 53.3000 | 46.7000 | 200 |

## 7. 0604 레벨별 svc vs pp_v8 강건성

| svc_group_level | n | svc_std | ppv8_std | svc_over_ppv8_std | svc_MdAPE | ppv8_MdAPE |
| --- | --- | --- | --- | --- | --- | --- |
| artist | 412 | 2.0505 | 0.6934 | 2.9573 | 0.3378 | 0.2547 |
| artist_size | 224 | 1.2081 | 0.5187 | 2.3294 | 0.2475 | 0.1887 |
| artist_medium_support_size | 91 | 0.7667 | 0.7925 | 0.9674 | 0.1429 | 0.1709 |
| medium_support_size | 66 | 0.9551 | 0.8191 | 1.1660 | 0.4847 | 0.2496 |
| global | 18 | 0.7826 | 0.8905 | 0.8789 | 0.7138 | 0.6931 |
| medium_size | 18 | 0.9043 | 0.6234 | 1.4505 | 0.8031 | 0.6110 |

## 8. 산출물

- `outputs/region_residual_summary.csv`, `outputs/bias_removal_oracle.csv`, `outputs/coverage_mix_shift.csv`
- `outputs/level_controlled_dispersion.csv`, `outputs/mix_within_decomposition.csv`, `outputs/svc_vs_ppv8_robustness_by_level.csv`
- `artifacts/run_config.json`