# PP-HCOEF27 Warm Huber HCOEF26 반복 split/artist holdout 재검증

- 작성일: 2026-06-08 05:39
- 목적: HCOEF26 low-risk fallback 후보가 validation 반복 표본에서도 안정적인지 확인.
- 새 보정식 생성 여부: 없음. HCOEF26 후보 예측값을 재사용해 반복 검증만 수행.
- 후보 선택 기준: validation OOF 상위 후보 + HCOEF26 보고서 상위 후보를 분리 기록.
- fixed test와 0604는 후보 경계값 선택에 사용하지 않고 확인 지표로만 사용.

## 1. 실행 결론

- 상위 재검증 후보: `hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1` (판단: fixed 확인 후보, fixed test `0.1371/0.2727/0.8064`, repeated min any2 `0.4800`, min all3 `0.1080`).
- 현재 기준 후보 `hcoef_stable` fixed test: `0.1388/0.2730/0.8064`.
- HCOEF27에서 반복 all3 gate를 통과하지 못하면 HCOEF26은 운영 기본 후보가 아니라 MAPE/MdAPE 연구 후보로 유지.

## 2. 후보 선택 근거

| candidate | selection_basis |
| --- | --- |
| hcoef_stable | baseline_or_component |
| current_70_30 | baseline_or_component |
| ppv8_service_proxy | baseline_or_component |
| svc_numeric_seed_mean | baseline_or_component |
| l10_seq_full_generated_bucket | baseline_or_component |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | validation_top |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | validation_top |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | validation_top |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | validation_top |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | validation_top |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef26_report_top_audit |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | hcoef26_report_top_audit |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef26_report_top_audit |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | hcoef26_report_top_audit |

## 3. 최종 선택표

| candidate | selection_basis | decision | row_oof_MdAPE | row_oof_MAPE | row_oof_p95_APE | artist_oof_MdAPE | artist_oof_MAPE | artist_oof_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | repeated_min_any2_improve_prob | repeated_min_all3_improve_prob | fixed_test_p95_guard | stress0604_p95_guard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | baseline_or_component | 현재 기준 후보 | 0.1260 | 0.2082 | 0.6479 | 0.1260 | 0.2082 | 0.6479 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef26_report_top_audit | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4560 | 0.1160 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | hcoef26_report_top_audit | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4560 | 0.1160 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4800 | 0.1080 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef26_report_top_audit | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4560 | 0.1160 | True | True |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | hcoef26_report_top_audit | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6453 | 0.1260 | 0.2082 | 0.6453 | 0.1371 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.4560 | 0.1160 | True | True |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.5060 | 0.1180 | True | True |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.5060 | 0.1180 | True | True |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.5060 | 0.1180 | True | True |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6425 | 0.1260 | 0.2082 | 0.6416 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.5060 | 0.1180 | True | True |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6416 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.5000 | 0.1020 | True | True |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | validation_top | fixed 확인 후보 | 0.1260 | 0.2082 | 0.6430 | 0.1260 | 0.2082 | 0.6416 | 0.1373 | 0.2727 | 0.8064 | 0.2731 | 0.3745 | 0.9835 | 0.5000 | 0.1020 | True | True |
| current_70_30 | baseline_or_component | 최소 비교 기준 | 0.1305 | 0.2110 | 0.6580 | 0.1305 | 0.2110 | 0.6580 | 0.1405 | 0.2748 | 0.8331 | 0.2779 | 0.3774 | 0.9871 | 0.0000 | 0.0000 | False | False |
| svc_numeric_seed_mean | baseline_or_component | component 대조군 | 0.1272 | 0.2176 | 0.6504 | 0.1272 | 0.2176 | 0.6504 | 0.1520 | 0.2942 | 0.9381 | 0.3072 | 0.4318 | 0.9998 | 0.0640 | 0.0000 | False | False |
| ppv8_service_proxy | baseline_or_component | component 대조군 | 0.1544 | 0.2544 | 0.8084 | 0.1544 | 0.2544 | 0.8084 | 0.1632 | 0.2816 | 0.9311 | 0.2298 | 0.3359 | 0.9273 | 0.0000 | 0.0000 | False | True |
| l10_seq_full_generated_bucket | baseline_or_component | component 대조군 | 0.1685 | 0.2981 | 0.8769 | 0.1685 | 0.2981 | 0.8769 | 0.1743 | 0.3265 | 0.9818 | 0.3207 | 0.4598 | 1.2569 | 0.0000 | 0.0000 | False | False |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | validation_top | 보류 | 0.1247 | 0.2081 | 0.6471 | 0.1253 | 0.2080 | 0.6397 | 0.1410 | 0.2726 | 0.8064 | 0.2775 | 0.3749 | 0.9835 | 0.7760 | 0.3500 | True | True |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | validation_top | 보류 | 0.1247 | 0.2081 | 0.6471 | 0.1253 | 0.2080 | 0.6397 | 0.1410 | 0.2726 | 0.8064 | 0.2775 | 0.3749 | 0.9835 | 0.7760 | 0.3500 | True | True |

## 4. Scope별 point metrics

| scope | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | mask_applied_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_row | hcoef_stable | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| validation_oof_row | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 | 1.0000 |
| validation_oof_row | ppv8_service_proxy | 0.1544 | 0.2544 | 0.8084 | 0.3721 | 0.0284 | 0.0462 | 0.1604 | 1.0000 |
| validation_oof_row | svc_numeric_seed_mean | 0.1272 | 0.2176 | 0.6504 | 0.3367 | 0.0012 | 0.0094 | 0.0024 | 1.0000 |
| validation_oof_row | l10_seq_full_generated_bucket | 0.1685 | 0.2981 | 0.8769 | 0.4112 | 0.0425 | 0.0899 | 0.2290 | 1.0000 |
| validation_oof_row | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0055 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0055 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0055 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0055 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6425 | 0.3251 | 0.0000 | -0.0000 | -0.0054 | 0.2775 |
| validation_oof_row | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | 0.1247 | 0.2081 | 0.6471 | 0.3250 | -0.0013 | -0.0001 | -0.0008 | 0.2775 |
| validation_oof_row | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | 0.1247 | 0.2081 | 0.6471 | 0.3250 | -0.0013 | -0.0001 | -0.0008 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6430 | 0.3251 | 0.0000 | -0.0000 | -0.0049 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6430 | 0.3251 | 0.0000 | -0.0000 | -0.0049 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_row | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_artist | hcoef_stable | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| validation_oof_artist | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 | 1.0000 |
| validation_oof_artist | ppv8_service_proxy | 0.1544 | 0.2544 | 0.8084 | 0.3721 | 0.0284 | 0.0462 | 0.1604 | 1.0000 |
| validation_oof_artist | svc_numeric_seed_mean | 0.1272 | 0.2176 | 0.6504 | 0.3367 | 0.0012 | 0.0094 | 0.0024 | 1.0000 |
| validation_oof_artist | l10_seq_full_generated_bucket | 0.1685 | 0.2981 | 0.8769 | 0.4112 | 0.0425 | 0.0899 | 0.2290 | 1.0000 |
| validation_oof_artist | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | 0.1253 | 0.2080 | 0.6397 | 0.3249 | -0.0007 | -0.0002 | -0.0083 | 0.2775 |
| validation_oof_artist | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | 0.1253 | 0.2080 | 0.6397 | 0.3249 | -0.0007 | -0.0002 | -0.0083 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1260 | 0.2082 | 0.6416 | 0.3251 | 0.0000 | -0.0000 | -0.0064 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| validation_oof_artist | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.1260 | 0.2082 | 0.6453 | 0.3251 | 0.0000 | 0.0000 | -0.0027 | 0.2775 |
| fixed_confirmation | hcoef_stable | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| fixed_confirmation | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 | 1.0000 |
| fixed_confirmation | ppv8_service_proxy | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.0244 | 0.0086 | 0.1247 | 1.0000 |
| fixed_confirmation | svc_numeric_seed_mean | 0.1520 | 0.2942 | 0.9381 | 0.4179 | 0.0132 | 0.0212 | 0.1317 | 1.0000 |
| fixed_confirmation | l10_seq_full_generated_bucket | 0.1743 | 0.3265 | 0.9818 | 0.4396 | 0.0355 | 0.0535 | 0.1755 | 1.0000 |
| fixed_confirmation | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1373 | 0.2727 | 0.8064 | 0.3987 | -0.0015 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1373 | 0.2727 | 0.8064 | 0.3987 | -0.0015 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1373 | 0.2727 | 0.8064 | 0.3987 | -0.0015 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1373 | 0.2727 | 0.8064 | 0.3987 | -0.0015 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | 0.1410 | 0.2726 | 0.8064 | 0.3985 | 0.0022 | -0.0004 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | 0.1410 | 0.2726 | 0.8064 | 0.3985 | 0.0022 | -0.0004 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.1373 | 0.2727 | 0.8064 | 0.3987 | -0.0015 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.1373 | 0.2727 | 0.8064 | 0.3987 | -0.0015 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| fixed_confirmation | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.1371 | 0.2727 | 0.8064 | 0.3987 | -0.0017 | -0.0003 | 0.0000 | 0.3031 |
| 0604_stress | hcoef_stable | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 0604_stress | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 | 1.0000 |
| 0604_stress | ppv8_service_proxy | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 | 1.0000 |
| 0604_stress | svc_numeric_seed_mean | 0.3072 | 0.4318 | 0.9998 | 1.6906 | 0.0342 | 0.0575 | 0.0163 | 1.0000 |
| 0604_stress | l10_seq_full_generated_bucket | 0.3207 | 0.4598 | 1.2569 | 1.0793 | 0.0477 | 0.0854 | 0.2734 | 1.0000 |

## 5. 반복 split/artist holdout 요약

| source_scope | validation_scheme | candidate | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | any2_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0010 | -0.0002 | -0.0016 | 0.6760 | 0.9160 | 0.6360 | 0.8320 | 0.4060 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | -0.0010 | -0.0002 | -0.0016 | 0.6760 | 0.9160 | 0.6360 | 0.8320 | 0.4060 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.0001 | -0.0000 | -0.0017 | 0.3220 | 0.6780 | 0.6360 | 0.5740 | 0.1360 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.0001 | -0.0000 | -0.0017 | 0.3220 | 0.6780 | 0.6360 | 0.5740 | 0.1360 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3860 | 0.5980 | 0.6400 | 0.5660 | 0.1380 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3860 | 0.5980 | 0.6400 | 0.5660 | 0.1380 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3860 | 0.5980 | 0.6400 | 0.5660 | 0.1380 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3860 | 0.5980 | 0.6400 | 0.5660 | 0.1380 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0017 | 0.3920 | 0.5240 | 0.6360 | 0.5120 | 0.1400 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.0000 | 0.0000 | -0.0011 | 0.4380 | 0.4060 | 0.6360 | 0.4940 | 0.1160 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.0000 | 0.0000 | -0.0011 | 0.4380 | 0.4060 | 0.6360 | 0.4940 | 0.1160 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.0000 | 0.0000 | -0.0011 | 0.4380 | 0.4060 | 0.6360 | 0.4940 | 0.1160 |
| validation_oof_artist | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.0000 | 0.0000 | -0.0011 | 0.4380 | 0.4060 | 0.6360 | 0.4940 | 0.1160 |
| validation_oof_artist | artist_holdout_80pct | svc_numeric_seed_mean | 0.0007 | 0.0095 | 0.0235 | 0.4020 | 0.0000 | 0.2700 | 0.0880 | 0.0000 |
| validation_oof_artist | artist_holdout_80pct | current_70_30 | 0.0038 | 0.0028 | 0.0129 | 0.0700 | 0.0000 | 0.1340 | 0.0040 | 0.0000 |
| validation_oof_artist | artist_holdout_80pct | hcoef_stable | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | artist_holdout_80pct | ppv8_service_proxy | 0.0267 | 0.0458 | 0.1450 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | artist_holdout_80pct | l10_seq_full_generated_bucket | 0.0446 | 0.0897 | 0.2397 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0008 | -0.0002 | -0.0016 | 0.6540 | 0.9020 | 0.5980 | 0.7960 | 0.3760 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | -0.0008 | -0.0002 | -0.0016 | 0.6540 | 0.9020 | 0.5980 | 0.7960 | 0.3760 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | 0.0000 | -0.0000 | -0.0016 | 0.2880 | 0.6100 | 0.5980 | 0.5060 | 0.1180 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.0000 | -0.0000 | -0.0016 | 0.2880 | 0.6100 | 0.5980 | 0.5060 | 0.1180 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | 0.0000 | -0.0000 | -0.0016 | 0.2880 | 0.6100 | 0.5980 | 0.5060 | 0.1180 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.0000 | -0.0000 | -0.0016 | 0.2880 | 0.6100 | 0.5980 | 0.5060 | 0.1180 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | 0.0001 | -0.0000 | -0.0016 | 0.2060 | 0.6740 | 0.5980 | 0.5000 | 0.1020 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | 0.0001 | -0.0000 | -0.0016 | 0.2060 | 0.6740 | 0.5980 | 0.5000 | 0.1020 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.0000 | 0.0000 | -0.0009 | 0.3960 | 0.4580 | 0.5980 | 0.4940 | 0.1240 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.0000 | 0.0000 | -0.0009 | 0.3960 | 0.4580 | 0.5980 | 0.4940 | 0.1240 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | 0.0000 | 0.0000 | -0.0009 | 0.3960 | 0.4580 | 0.5980 | 0.4940 | 0.1240 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | 0.0000 | 0.0000 | -0.0009 | 0.3960 | 0.4580 | 0.5980 | 0.4940 | 0.1240 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0000 | -0.0000 | -0.0016 | 0.2980 | 0.5460 | 0.5980 | 0.4800 | 0.1080 |
| validation_oof_artist | row_subsample_80pct | svc_numeric_seed_mean | 0.0010 | 0.0096 | 0.0209 | 0.3840 | 0.0000 | 0.2400 | 0.0940 | 0.0000 |
| validation_oof_artist | row_subsample_80pct | hcoef_stable | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | row_subsample_80pct | current_70_30 | 0.0039 | 0.0028 | 0.0142 | 0.0360 | 0.0000 | 0.0900 | 0.0000 | 0.0000 |
| validation_oof_artist | row_subsample_80pct | ppv8_service_proxy | 0.0271 | 0.0464 | 0.1420 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | row_subsample_80pct | l10_seq_full_generated_bucket | 0.0441 | 0.0898 | 0.2333 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0016 | -0.0001 | -0.0006 | 0.8660 | 0.6500 | 0.6000 | 0.7760 | 0.3540 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | -0.0016 | -0.0001 | -0.0006 | 0.8660 | 0.6500 | 0.6000 | 0.7760 | 0.3540 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0003 | -0.0000 | -0.0010 | 0.5280 | 0.6200 | 0.6000 | 0.6120 | 0.2260 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0003 | -0.0000 | -0.0010 | 0.5280 | 0.6200 | 0.6000 | 0.6120 | 0.2260 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5340 | 0.5860 | 0.6000 | 0.5980 | 0.2180 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5340 | 0.5860 | 0.6000 | 0.5980 | 0.2180 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5340 | 0.5860 | 0.6000 | 0.5980 | 0.2180 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5340 | 0.5860 | 0.6000 | 0.5980 | 0.2180 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0004 | -0.0000 | -0.0010 | 0.5400 | 0.5200 | 0.6000 | 0.5700 | 0.1960 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | -0.0002 | 0.0000 | -0.0007 | 0.4520 | 0.3740 | 0.6000 | 0.4560 | 0.1260 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | -0.0002 | 0.0000 | -0.0007 | 0.4520 | 0.3740 | 0.6000 | 0.4560 | 0.1260 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | -0.0002 | 0.0000 | -0.0007 | 0.4520 | 0.3740 | 0.6000 | 0.4560 | 0.1260 |
| validation_oof_row | artist_holdout_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | -0.0002 | 0.0000 | -0.0007 | 0.4520 | 0.3740 | 0.6000 | 0.4560 | 0.1260 |
| validation_oof_row | artist_holdout_80pct | svc_numeric_seed_mean | 0.0008 | 0.0094 | 0.0236 | 0.4020 | 0.0000 | 0.2700 | 0.0920 | 0.0000 |
| validation_oof_row | artist_holdout_80pct | current_70_30 | 0.0037 | 0.0028 | 0.0121 | 0.0440 | 0.0000 | 0.1780 | 0.0040 | 0.0000 |
| validation_oof_row | artist_holdout_80pct | hcoef_stable | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | artist_holdout_80pct | ppv8_service_proxy | 0.0270 | 0.0462 | 0.1451 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | artist_holdout_80pct | l10_seq_full_generated_bucket | 0.0435 | 0.0897 | 0.2368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | -0.0016 | -0.0001 | -0.0006 | 0.8120 | 0.6680 | 0.6400 | 0.7880 | 0.3500 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | -0.0016 | -0.0001 | -0.0006 | 0.8120 | 0.6680 | 0.6400 | 0.7880 | 0.3500 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0004 | -0.0000 | -0.0012 | 0.4940 | 0.6900 | 0.6400 | 0.6540 | 0.2320 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0004 | -0.0000 | -0.0012 | 0.4940 | 0.6900 | 0.6400 | 0.6540 | 0.2320 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6600 | 0.6400 | 0.6460 | 0.2280 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6600 | 0.6400 | 0.6460 | 0.2280 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6600 | 0.6400 | 0.6460 | 0.2280 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6600 | 0.6400 | 0.6460 | 0.2280 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | -0.0005 | -0.0000 | -0.0013 | 0.5120 | 0.6040 | 0.6400 | 0.6200 | 0.2080 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | -0.0003 | 0.0000 | -0.0008 | 0.4600 | 0.4480 | 0.6400 | 0.5080 | 0.1480 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | -0.0003 | 0.0000 | -0.0008 | 0.4600 | 0.4480 | 0.6400 | 0.5080 | 0.1480 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | -0.0003 | 0.0000 | -0.0008 | 0.4600 | 0.4480 | 0.6400 | 0.5080 | 0.1480 |
| validation_oof_row | row_subsample_80pct | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | -0.0003 | 0.0000 | -0.0008 | 0.4600 | 0.4480 | 0.6400 | 0.5080 | 0.1480 |
| validation_oof_row | row_subsample_80pct | svc_numeric_seed_mean | 0.0011 | 0.0096 | 0.0201 | 0.3280 | 0.0000 | 0.2380 | 0.0640 | 0.0000 |
| validation_oof_row | row_subsample_80pct | current_70_30 | 0.0039 | 0.0028 | 0.0130 | 0.0280 | 0.0000 | 0.1200 | 0.0020 | 0.0000 |
| validation_oof_row | row_subsample_80pct | hcoef_stable | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | row_subsample_80pct | ppv8_service_proxy | 0.0267 | 0.0457 | 0.1386 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | row_subsample_80pct | l10_seq_full_generated_bucket | 0.0446 | 0.0895 | 0.2320 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 6. 정책/계수 해석

- HCOEF27의 계수는 새로 학습된 Huber 계수가 아니라 HCOEF26 정책 가중치와 적용 mask를 의미함.
- `mask_name`은 HCOEF25 후보 이동분을 적용할 수 있는 구간임.
- mask를 만족하지 않는 행은 `hcoef_stable`로 fallback하므로 큰 오차 악화를 줄이는 구조임.

| candidate | method | source_candidate | mask_name | strength | cap | mean_mask_applied | mean_abs_move_log | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | source | hcoef_stable | all | 1.0000 |  | 1.0000 | 0.0000 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | no_extreme_reliable | 1.0000 | 0.0075 | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | no_extreme_reliable | 1.0000 |  | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | p95_defense_core | 1.0000 | 0.0075 | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | p95_defense_core | 1.0000 |  | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | no_extreme_reliable | 1.0000 | 0.0050 | 0.2425 | 0.0009 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p01_cap0p03_s0p25 | p95_defense_core | 1.0000 | 0.0050 | 0.2425 | 0.0009 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | no_extreme_reliable | 1.0000 | 0.0075 | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | no_extreme_reliable | 1.0000 |  | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | p95_defense_core | 1.0000 | 0.0075 | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | p95_defense_core | 1.0000 |  | 0.2425 | 0.0012 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | no_extreme_reliable | 1.0000 | 0.0050 | 0.2425 | 0.0009 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gated_h25_candidate | hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p03_s0p25 | p95_defense_core | 1.0000 | 0.0050 | 0.2425 | 0.0009 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 | no_extreme_reliable | 1.0000 | 0.0075 | 0.2425 | 0.0013 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 | no_extreme_reliable | 1.0000 |  | 0.2425 | 0.0013 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gated_h25_candidate | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 | p95_defense_core | 1.0000 | 0.0075 | 0.2425 | 0.0013 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_default_conservative_guard_core_a0p001_cap0p03_s0p25 | p95_defense_core | 1.0000 |  | 0.2425 | 0.0013 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p03_s0p25 | no_extreme_reliable | 1.0000 |  | 0.2425 | 0.0013 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_rh_loose_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_resid_huber_loose_conservative_guard_core_a0p001_cap0p03_s0p25 | p95_defense_core | 1.0000 |  | 0.2425 | 0.0013 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| current_70_30 | source | current_70_30 | all | 1.0000 |  | 1.0000 | 0.0190 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| svc_numeric_seed_mean | source | svc_numeric_seed_mean | all | 1.0000 |  | 1.0000 | 0.0853 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| ppv8_service_proxy | source | ppv8_service_proxy | all | 1.0000 |  | 1.0000 | 0.1897 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| l10_seq_full_generated_bucket | source | l10_seq_full_generated_bucket | all | 1.0000 |  | 1.0000 | 0.2473 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_no_extreme_reliable_nocap_s1 | gated_h25_candidate | hcoef25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5 | no_extreme_reliable | 1.0000 |  | 0.2425 | 0.0027 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |
| hcoef26_h25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5_p95_defense_core_nocap_s1 | gated_h25_candidate | hcoef25_direct_huber_guarded_strict_a0p01_cap0p03_s0p5 | p95_defense_core | 1.0000 |  | 0.2425 | 0.0027 | HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책. |

## 7. 잔차/큰 오차 구간

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | median_residual_log | mean_residual_log | mean_abs_move_log | over_50pct_error_rate | over_100pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 0.2961 | 0.6185 | 0.0225 | 0.4328 | 0.0448 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 0.2799 | 0.6042 | 0.0000 | 0.4403 | 0.0423 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | -0.0556 | 0.0461 | 0.0217 | 0.3125 | 0.0391 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_010_020 | 128 | 0.2210 | 0.3397 | 0.8728 | -0.0540 | 0.0394 | 0.0010 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_010_020 | 128 | 0.2225 | 0.3396 | 0.8728 | -0.0515 | 0.0395 | 0.0007 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_010_020 | 128 | 0.2255 | 0.3393 | 0.8728 | -0.0465 | 0.0399 | 0.0000 | 0.3047 | 0.0234 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.0641 | 0.0905 | 0.0190 | 0.0880 | 0.0480 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1492 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_005_010 | 125 | 0.1487 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_005_010 | 125 | 0.1487 | 0.2517 | 0.9526 | 0.0403 | 0.0876 | 0.0012 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_005_010 | 125 | 0.1498 | 0.2516 | 0.9526 | 0.0403 | 0.0875 | 0.0010 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_005_010 | 125 | 0.1498 | 0.2514 | 0.9526 | 0.0403 | 0.0872 | 0.0000 | 0.0960 | 0.0400 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.0401 | 0.0761 | 0.0164 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.0305 | 0.0819 | 0.0227 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_000_003 | 119 | 0.0976 | 0.1891 | 0.5300 | 0.0267 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_000_003 | 119 | 0.0974 | 0.1891 | 0.5300 | 0.0265 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_000_003 | 119 | 0.0974 | 0.1891 | 0.5300 | 0.0265 | 0.0705 | 0.0016 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1890 | 0.5300 | 0.0267 | 0.0705 | 0.0014 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1890 | 0.5300 | 0.0267 | 0.0705 | 0.0014 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1890 | 0.5300 | 0.0267 | 0.0705 | 0.0014 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_000_003 | 119 | 0.0998 | 0.1890 | 0.5300 | 0.0267 | 0.0705 | 0.0014 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_000_003 | 119 | 0.1053 | 0.1886 | 0.5300 | 0.0272 | 0.0704 | 0.0000 | 0.0756 | 0.0084 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0076 | 0.0812 | 0.0020 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0076 | 0.0812 | 0.0020 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_nocap_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1849 | 0.5173 | 0.0078 | 0.0812 | 0.0021 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1846 | 0.5173 | 0.0078 | 0.0811 | 0.0017 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1846 | 0.5173 | 0.0078 | 0.0811 | 0.0017 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1846 | 0.5173 | 0.0078 | 0.0811 | 0.0017 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | gap_band | gap_003_005 | 55 | 0.0868 | 0.1846 | 0.5173 | 0.0078 | 0.0811 | 0.0017 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef_stable | gap_band | gap_003_005 | 55 | 0.0868 | 0.1845 | 0.5173 | 0.0125 | 0.0816 | 0.0000 | 0.0545 | 0.0000 |
| 0604_stress | 0604_ex50 | current_70_30 | hcoef23_risk_score | 4.0000 | 41 | 0.5862 | 0.6389 | 0.9788 | 0.3569 | 0.6749 | 0.0230 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_default_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_cap0p0075_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_no_extreme_reliable_nocap_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p005_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_cap0p0075_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p001_cap0p03_s0p25_p95_defense_core_nocap_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |
| 0604_stress | 0604_ex50 | hcoef26_h25_rh_strict_conservative_guard_core_a0p01_cap0p03_s0p25_no_extreme_reliable_cap0p005_s1 | hcoef23_risk_score | 4.0000 | 41 | 0.5757 | 0.6375 | 0.9793 | 0.3617 | 0.6574 | 0.0000 | 0.5610 | 0.0488 |

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/repeated_iteration_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/residual_analysis.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`