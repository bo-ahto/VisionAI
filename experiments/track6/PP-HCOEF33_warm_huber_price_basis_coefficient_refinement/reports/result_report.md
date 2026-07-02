# PP-HCOEF33 Warm Huber HCOEF32 extended validation

- 작성일: 2026-06-08 07:39
- 목적: HCOEF32의 tiny p95 개선 후보가 반복 split/artist-level split에서도 안정적인지 확장 검증.
- 새 후보 생성 없음: HCOEF32 주요 후보만 좁혀서 재검증.
- fixed test와 0604는 확인용이며, 후보 선택 기준으로 사용하지 않음.

## 1. 실행 결론

- 핵심 확인 후보 `hcoef32_s03_all3_dir_top2_w0p025_cap0p001` 판단: fixed/0604 확인 후보.
- 확장 반복 검증 min any2/all3: `0.8085 / 0.2785`.
- 운영 후보 승격 기준은 repeated all3 `0.90` 이상, fixed/0604 p95 방어, fixed 2개 이상 개선.
- 기준을 넘지 못하면 `hcoef_stable`을 현재 안정 후보로 유지하고 HCOEF32는 p95-first 확인 후보로만 관리.

## 2. 검증 대상 후보

| candidate |
| --- |
| hcoef_stable |
| current_70_30 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 |
| hcoef29_risk_guarded_component_s0p5_cap0p08 |
| hcoef29_core_component_delta_s0p5_cap0p08 |

## 3. 후보별 판단 요약

| candidate | decision | test_MdAPE | test_MAPE | test_p95_APE | stress0604_MdAPE | stress0604_MAPE | stress0604_p95_APE | repeated_min_any2_improve_prob | repeated_min_all3_improve_prob | repeated_mean_mean_delta_MdAPE_vs_stable | repeated_mean_mean_delta_MAPE_vs_stable | repeated_mean_mean_delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | 현재 안정 후보 | 0.1388 | 0.2730 | 0.8064 | 0.2731 | 0.3744 | 0.9835 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | fixed/0604 확인 후보 | 0.1388 | 0.2729 | 0.8062 | 0.2727 | 0.3744 | 0.9834 | 0.8085 | 0.2785 | -0.0001 | -0.0000 | -0.0003 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | fixed/0604 확인 후보 | 0.1388 | 0.2729 | 0.8062 | 0.2726 | 0.3744 | 0.9834 | 0.8085 | 0.2785 | -0.0001 | -0.0000 | -0.0003 |
| current_70_30 | 서비스 v0.1 기준 | 0.1405 | 0.2748 | 0.8331 | 0.2779 | 0.3774 | 0.9871 | 0.0010 | 0.0000 | 0.0037 | 0.0028 | 0.0112 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 보류 | 0.1381 | 0.2729 | 0.8064 | 0.2719 | 0.3744 | 0.9834 | 0.8410 | 0.3360 | -0.0003 | -0.0001 | -0.0006 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 보류 | 0.1381 | 0.2729 | 0.8065 | 0.2731 | 0.3744 | 0.9834 | 0.8300 | 0.3030 | -0.0002 | -0.0001 | -0.0006 |
| hcoef29_risk_guarded_component_s0p5_cap0p08 | 보류 | 0.1442 | 0.2718 | 0.8081 | 0.2789 | 0.3678 | 0.9446 | 0.8370 | 0.4245 | -0.0015 | -0.0011 | -0.0064 |
| hcoef29_core_component_delta_s0p5_cap0p08 | 보류 | 0.1453 | 0.2731 | 0.8288 | 0.2641 | 0.3742 | 0.9833 | 0.8525 | 0.4670 | -0.0032 | -0.0006 | -0.0036 |

## 4. Scope별 고정 지표

| scope | split | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | hcoef_stable | 829 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | current_70_30 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 829 | 0.2727 | 0.3744 | 0.9834 | 1.3076 | -0.0004 | -0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 829 | 0.2726 | 0.3744 | 0.9834 | 1.3076 | -0.0004 | -0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 829 | 0.2719 | 0.3744 | 0.9834 | 1.3074 | -0.0012 | -0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 829 | 0.2731 | 0.3744 | 0.9834 | 1.3075 | 0.0000 | 0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | 829 | 0.2789 | 0.3678 | 0.9446 | 1.3281 | 0.0058 | -0.0065 | -0.0389 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | 829 | 0.2641 | 0.3742 | 0.9833 | 1.2996 | -0.0090 | -0.0002 | -0.0001 |
| fixed_confirmation | test | hcoef_stable | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| fixed_confirmation | test | current_70_30 | 607 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 |
| fixed_confirmation | test | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 607 | 0.1388 | 0.2729 | 0.8062 | 0.3988 | 0.0000 | -0.0000 | -0.0001 |
| fixed_confirmation | test | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 607 | 0.1388 | 0.2729 | 0.8062 | 0.3988 | 0.0000 | -0.0000 | -0.0001 |
| fixed_confirmation | test | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 607 | 0.1381 | 0.2729 | 0.8064 | 0.3988 | -0.0007 | -0.0001 | 0.0000 |
| fixed_confirmation | test | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 607 | 0.1381 | 0.2729 | 0.8065 | 0.3988 | -0.0007 | -0.0000 | 0.0001 |
| fixed_confirmation | test | hcoef29_risk_guarded_component_s0p5_cap0p08 | 607 | 0.1442 | 0.2718 | 0.8081 | 0.3974 | 0.0054 | -0.0012 | 0.0018 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | 607 | 0.1453 | 0.2731 | 0.8288 | 0.3991 | 0.0065 | 0.0001 | 0.0224 |
| validation_oof_artist | validation | hcoef_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | validation | current_70_30 | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 |
| validation_oof_artist | validation | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 519 | 0.1260 | 0.2082 | 0.6472 | 0.3251 | 0.0000 | -0.0000 | -0.0008 |
| validation_oof_artist | validation | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 519 | 0.1260 | 0.2082 | 0.6472 | 0.3251 | 0.0000 | -0.0000 | -0.0008 |
| validation_oof_artist | validation | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 519 | 0.1260 | 0.2081 | 0.6464 | 0.3251 | 0.0000 | -0.0001 | -0.0015 |
| validation_oof_artist | validation | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 519 | 0.1260 | 0.2081 | 0.6464 | 0.3251 | 0.0000 | -0.0001 | -0.0015 |
| validation_oof_artist | validation | hcoef29_risk_guarded_component_s0p5_cap0p08 | 519 | 0.1239 | 0.2071 | 0.6392 | 0.3229 | -0.0021 | -0.0011 | -0.0088 |
| validation_oof_artist | validation | hcoef29_core_component_delta_s0p5_cap0p08 | 519 | 0.1233 | 0.2075 | 0.6438 | 0.3235 | -0.0027 | -0.0007 | -0.0041 |
| validation_oof_row | validation | hcoef_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | validation | current_70_30 | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 |
| validation_oof_row | validation | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 519 | 0.1260 | 0.2082 | 0.6468 | 0.3251 | 0.0000 | -0.0000 | -0.0011 |
| validation_oof_row | validation | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 519 | 0.1260 | 0.2082 | 0.6468 | 0.3251 | 0.0000 | -0.0000 | -0.0011 |
| validation_oof_row | validation | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 519 | 0.1260 | 0.2081 | 0.6457 | 0.3251 | 0.0000 | -0.0001 | -0.0022 |
| validation_oof_row | validation | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 519 | 0.1260 | 0.2081 | 0.6457 | 0.3251 | 0.0000 | -0.0001 | -0.0022 |
| validation_oof_row | validation | hcoef29_risk_guarded_component_s0p5_cap0p08 | 519 | 0.1242 | 0.2071 | 0.6347 | 0.3220 | -0.0018 | -0.0011 | -0.0133 |
| validation_oof_row | validation | hcoef29_core_component_delta_s0p5_cap0p08 | 519 | 0.1208 | 0.2077 | 0.6448 | 0.3233 | -0.0052 | -0.0005 | -0.0032 |

## 5. 확장 반복 검증 요약

| source_scope | validation_scheme | candidate | n_repeats | all3_improve_prob | any2_improve_prob | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | worst_delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation_oof_artist | artist_holdout_70pct | current_70_30 | 2000 | 0.0000 | 0.0225 | 0.1245 | 0.0000 | 0.2285 | 0.0034 | 0.0029 | 0.0087 | 0.0414 |
| validation_oof_artist | artist_holdout_80pct | current_70_30 | 2000 | 0.0000 | 0.0050 | 0.0520 | 0.0000 | 0.1670 | 0.0038 | 0.0028 | 0.0120 | 0.0329 |
| validation_oof_artist | row_subsample_70pct | current_70_30 | 2000 | 0.0000 | 0.0115 | 0.0905 | 0.0000 | 0.1635 | 0.0037 | 0.0028 | 0.0108 | 0.0410 |
| validation_oof_artist | row_subsample_80pct | current_70_30 | 2000 | 0.0000 | 0.0010 | 0.0285 | 0.0000 | 0.1225 | 0.0039 | 0.0028 | 0.0138 | 0.0369 |
| validation_oof_row | artist_holdout_70pct | current_70_30 | 2000 | 0.0000 | 0.0240 | 0.1215 | 0.0000 | 0.2540 | 0.0034 | 0.0028 | 0.0080 | 0.0414 |
| validation_oof_row | artist_holdout_80pct | current_70_30 | 2000 | 0.0000 | 0.0060 | 0.0600 | 0.0000 | 0.1615 | 0.0037 | 0.0028 | 0.0124 | 0.0365 |
| validation_oof_row | row_subsample_70pct | current_70_30 | 2000 | 0.0000 | 0.0105 | 0.0875 | 0.0000 | 0.1580 | 0.0037 | 0.0028 | 0.0111 | 0.0410 |
| validation_oof_row | row_subsample_80pct | current_70_30 | 2000 | 0.0000 | 0.0030 | 0.0305 | 0.0000 | 0.1265 | 0.0039 | 0.0028 | 0.0132 | 0.0369 |
| validation_oof_artist | artist_holdout_70pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.4670 | 0.8525 | 0.8115 | 0.8525 | 0.6350 | -0.0027 | -0.0007 | -0.0035 | 0.0359 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.5665 | 0.9210 | 0.8770 | 0.9015 | 0.7015 | -0.0026 | -0.0007 | -0.0043 | 0.0230 |
| validation_oof_artist | row_subsample_70pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.4935 | 0.8815 | 0.8190 | 0.8710 | 0.6700 | -0.0027 | -0.0007 | -0.0038 | 0.0359 |
| validation_oof_artist | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.6265 | 0.9470 | 0.8965 | 0.9375 | 0.7330 | -0.0027 | -0.0007 | -0.0035 | 0.0278 |
| validation_oof_row | artist_holdout_70pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.4710 | 0.8535 | 0.9090 | 0.7485 | 0.6545 | -0.0038 | -0.0005 | -0.0035 | 0.0419 |
| validation_oof_row | artist_holdout_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.5410 | 0.9150 | 0.9655 | 0.8175 | 0.6690 | -0.0038 | -0.0005 | -0.0036 | 0.0190 |
| validation_oof_row | row_subsample_70pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.5155 | 0.8895 | 0.9315 | 0.7770 | 0.6890 | -0.0037 | -0.0005 | -0.0036 | 0.0362 |
| validation_oof_row | row_subsample_80pct | hcoef29_core_component_delta_s0p5_cap0p08 | 2000 | 0.5780 | 0.9280 | 0.9760 | 0.8340 | 0.6930 | -0.0037 | -0.0005 | -0.0031 | 0.0240 |
| validation_oof_artist | artist_holdout_70pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.4245 | 0.8370 | 0.7235 | 0.8675 | 0.6440 | -0.0017 | -0.0011 | -0.0040 | 0.0433 |
| validation_oof_artist | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.5470 | 0.9040 | 0.7505 | 0.9060 | 0.7845 | -0.0017 | -0.0010 | -0.0053 | 0.0318 |
| validation_oof_artist | row_subsample_70pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.4660 | 0.8650 | 0.7305 | 0.8930 | 0.6950 | -0.0018 | -0.0011 | -0.0050 | 0.0411 |
| validation_oof_artist | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.5805 | 0.9375 | 0.7385 | 0.9425 | 0.8290 | -0.0016 | -0.0010 | -0.0058 | 0.0286 |
| validation_oof_row | artist_holdout_70pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.4825 | 0.8730 | 0.7030 | 0.8705 | 0.7635 | -0.0016 | -0.0011 | -0.0072 | 0.0347 |
| validation_oof_row | artist_holdout_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.5780 | 0.9305 | 0.7015 | 0.9235 | 0.8780 | -0.0013 | -0.0011 | -0.0078 | 0.0238 |
| validation_oof_row | row_subsample_70pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.5030 | 0.8940 | 0.6840 | 0.9120 | 0.7920 | -0.0013 | -0.0011 | -0.0079 | 0.0305 |
| validation_oof_row | row_subsample_80pct | hcoef29_risk_guarded_component_s0p5_cap0p08 | 2000 | 0.6150 | 0.9560 | 0.7055 | 0.9610 | 0.9015 | -0.0011 | -0.0011 | -0.0086 | 0.0226 |
| validation_oof_artist | artist_holdout_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.3500 | 0.8345 | 0.5035 | 0.9990 | 0.6815 | -0.0001 | -0.0000 | -0.0003 | 0.0007 |
| validation_oof_artist | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.3280 | 0.8425 | 0.5055 | 1.0000 | 0.6650 | -0.0001 | -0.0000 | -0.0003 | 0.0002 |
| validation_oof_artist | row_subsample_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.2785 | 0.8240 | 0.3970 | 0.9995 | 0.7060 | -0.0001 | -0.0000 | -0.0003 | 0.0007 |
| validation_oof_artist | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.2830 | 0.8085 | 0.4180 | 1.0000 | 0.6735 | -0.0002 | -0.0000 | -0.0003 | 0.0002 |
| validation_oof_row | artist_holdout_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.3850 | 0.8735 | 0.4780 | 0.9995 | 0.7810 | -0.0001 | -0.0000 | -0.0003 | 0.0010 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.4495 | 0.9430 | 0.4980 | 1.0000 | 0.8945 | -0.0001 | -0.0000 | -0.0004 | 0.0001 |
| validation_oof_row | row_subsample_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.3185 | 0.8995 | 0.3755 | 1.0000 | 0.8425 | -0.0001 | -0.0000 | -0.0004 | 0.0009 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | 2000 | 0.3615 | 0.9515 | 0.3960 | 1.0000 | 0.9170 | -0.0001 | -0.0000 | -0.0004 | 0.0001 |
| validation_oof_artist | artist_holdout_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.3500 | 0.8345 | 0.5035 | 0.9990 | 0.6815 | -0.0001 | -0.0000 | -0.0003 | 0.0007 |
| validation_oof_artist | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.3280 | 0.8425 | 0.5055 | 1.0000 | 0.6650 | -0.0001 | -0.0000 | -0.0003 | 0.0002 |
| validation_oof_artist | row_subsample_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.2785 | 0.8240 | 0.3970 | 0.9995 | 0.7060 | -0.0001 | -0.0000 | -0.0003 | 0.0007 |
| validation_oof_artist | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.2830 | 0.8085 | 0.4180 | 1.0000 | 0.6735 | -0.0002 | -0.0000 | -0.0003 | 0.0002 |
| validation_oof_row | artist_holdout_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.3850 | 0.8735 | 0.4780 | 0.9995 | 0.7810 | -0.0001 | -0.0000 | -0.0003 | 0.0010 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.4495 | 0.9430 | 0.4980 | 1.0000 | 0.8945 | -0.0001 | -0.0000 | -0.0004 | 0.0001 |
| validation_oof_row | row_subsample_70pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.3185 | 0.8995 | 0.3755 | 1.0000 | 0.8425 | -0.0001 | -0.0000 | -0.0004 | 0.0009 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | 2000 | 0.3615 | 0.9515 | 0.3960 | 1.0000 | 0.9170 | -0.0001 | -0.0000 | -0.0004 | 0.0001 |
| validation_oof_artist | artist_holdout_70pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.3840 | 0.8525 | 0.5545 | 0.9990 | 0.6825 | -0.0003 | -0.0001 | -0.0005 | 0.0015 |
| validation_oof_artist | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.3635 | 0.8645 | 0.5630 | 1.0000 | 0.6650 | -0.0003 | -0.0001 | -0.0005 | 0.0004 |
| validation_oof_artist | row_subsample_70pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.3360 | 0.8500 | 0.4785 | 0.9995 | 0.7080 | -0.0003 | -0.0001 | -0.0005 | 0.0013 |
| validation_oof_artist | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.3585 | 0.8410 | 0.5260 | 1.0000 | 0.6735 | -0.0003 | -0.0001 | -0.0006 | 0.0003 |
| validation_oof_row | artist_holdout_70pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.4195 | 0.8830 | 0.5210 | 0.9995 | 0.7820 | -0.0002 | -0.0001 | -0.0007 | 0.0020 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.4870 | 0.9440 | 0.5365 | 1.0000 | 0.8945 | -0.0003 | -0.0001 | -0.0007 | 0.0002 |
| validation_oof_row | row_subsample_70pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.3615 | 0.9060 | 0.4240 | 1.0000 | 0.8435 | -0.0002 | -0.0001 | -0.0007 | 0.0018 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | 2000 | 0.4010 | 0.9550 | 0.4390 | 1.0000 | 0.9170 | -0.0003 | -0.0001 | -0.0007 | 0.0002 |
| validation_oof_artist | artist_holdout_70pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3495 | 0.8435 | 0.5105 | 0.9995 | 0.6825 | -0.0002 | -0.0001 | -0.0005 | 0.0015 |
| validation_oof_artist | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3425 | 0.8525 | 0.5300 | 1.0000 | 0.6650 | -0.0003 | -0.0001 | -0.0005 | 0.0004 |
| validation_oof_artist | row_subsample_70pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3030 | 0.8410 | 0.4365 | 0.9995 | 0.7080 | -0.0003 | -0.0001 | -0.0005 | 0.0013 |
| validation_oof_artist | row_subsample_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3390 | 0.8300 | 0.4955 | 1.0000 | 0.6735 | -0.0003 | -0.0001 | -0.0006 | 0.0003 |
| validation_oof_row | artist_holdout_70pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3785 | 0.8790 | 0.4755 | 1.0000 | 0.7820 | -0.0002 | -0.0001 | -0.0007 | 0.0020 |
| validation_oof_row | artist_holdout_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.4475 | 0.9445 | 0.4975 | 1.0000 | 0.8945 | -0.0002 | -0.0001 | -0.0007 | 0.0002 |
| validation_oof_row | row_subsample_70pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3185 | 0.9040 | 0.3790 | 1.0000 | 0.8435 | -0.0002 | -0.0001 | -0.0007 | 0.0018 |
| validation_oof_row | row_subsample_80pct | hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | 2000 | 0.3725 | 0.9540 | 0.4095 | 1.0000 | 0.9170 | -0.0003 | -0.0001 | -0.0007 | 0.0002 |
| validation_oof_artist | artist_holdout_70pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | artist_holdout_80pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | row_subsample_70pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | row_subsample_80pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | artist_holdout_70pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | artist_holdout_80pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | row_subsample_70pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | row_subsample_80pct | hcoef_stable | 2000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 6. Segment별 영향

| scope | split | candidate | segment | segment_value | n | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | delta_RMSE_log_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist_medium_support_size | 91 | -0.0142 | 0.0034 | 0.0388 | 0.0030 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | medium_support_size | 66 | 0.0298 | -0.0021 | -0.0226 | 0.0161 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_low | 101 | -0.0171 | 0.0017 | 0.0350 | -0.0053 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_010_020 | 128 | -0.0167 | -0.0022 | 0.0319 | -0.0055 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | stable_pred_price_band | (2979253.356, 7498463.56] | 156 | 0.0045 | 0.0022 | 0.0347 | -0.0044 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_003_005 | 55 | 0.0131 | -0.0002 | -0.0272 | -0.0033 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_50_plus | 105 | 0.0205 | -0.0006 | -0.0124 | 0.0078 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_000_003 | 119 | -0.0082 | -0.0031 | -0.0182 | -0.0034 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_020_plus | 402 | 0.0244 | 0.0021 | -0.0000 | -0.0110 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_mid | 242 | -0.0022 | 0.0018 | 0.0206 | -0.0051 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | global | 18 | -0.0079 | 0.0093 | 0.0073 | -0.0022 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | stable_pred_price_band | (7498463.56, inf] | 221 | 0.0064 | 0.0023 | 0.0145 | -0.0016 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_high | 124 | -0.0049 | 0.0002 | 0.0162 | -0.0017 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_low_mid | 267 | -0.0016 | -0.0004 | -0.0186 | -0.0010 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_10_19 | 199 | 0.0076 | 0.0019 | 0.0108 | -0.0100 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist | 412 | -0.0176 | 0.0015 | -0.0004 | -0.0106 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_20_49 | 90 | 0.0007 | 0.0067 | 0.0118 | -0.0045 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_extreme | 438 | 0.0184 | -0.0001 | -0.0000 | -0.0113 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | stable_pred_price_band | (1264575.052, 2979253.356] | 171 | 0.0111 | -0.0024 | 0.0036 | -0.0042 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_5_9 | 435 | -0.0091 | -0.0024 | -0.0004 | -0.0112 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_high | 185 | -0.0072 | -0.0031 | -0.0004 | -0.0042 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | stable_pred_price_band | (-inf, 1264575.052] | 281 | 0.0067 | -0.0020 | -0.0004 | -0.0137 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist_size | 224 | -0.0002 | -0.0045 | 0.0034 | -0.0140 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_005_010 | 125 | -0.0020 | -0.0024 | -0.0036 | -0.0040 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | medium_size | 18 | -0.0029 | -0.0042 | 0.0001 | -0.0008 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_extreme | 301 | 0.0030 | -0.0005 | -0.0002 | -0.0123 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | medium_support_size | 66 | 0.0389 | -0.0349 | -0.1078 | 0.0242 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | stable_pred_price_band | (2979253.356, 7498463.56] | 156 | -0.0138 | -0.0146 | -0.1454 | 0.0166 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_005_010 | 125 | 0.0176 | -0.0006 | -0.1385 | 0.0113 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_50_plus | 105 | 0.0359 | -0.0182 | -0.0896 | 0.0406 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | pred_spread_band | spread_high | 124 | -0.0348 | -0.0222 | -0.0844 | 0.0047 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_low | 101 | 0.0210 | -0.0141 | -0.0919 | -0.0024 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | artist_medium_support_size | 91 | -0.0088 | -0.0066 | -0.1017 | 0.0076 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_010_020 | 128 | 0.0187 | -0.0231 | -0.0630 | 0.0103 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_003_005 | 55 | 0.0610 | 0.0140 | -0.0263 | 0.0245 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | pred_spread_band | spread_low_mid | 267 | 0.0203 | 0.0040 | -0.0585 | 0.0144 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | stable_pred_price_band | (7498463.56, inf] | 221 | 0.0173 | -0.0063 | -0.0564 | 0.0235 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | stable_pred_price_band | (1264575.052, 2979253.356] | 171 | 0.0219 | -0.0073 | -0.0354 | 0.0230 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | artist_size | 224 | 0.0401 | 0.0037 | 0.0110 | 0.0247 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_high | 185 | 0.0345 | -0.0086 | -0.0089 | 0.0200 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | global | 18 | 0.0280 | 0.0069 | 0.0119 | 0.0658 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_000_003 | 119 | 0.0050 | 0.0073 | 0.0317 | 0.0213 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_extreme | 301 | 0.0157 | 0.0061 | -0.0096 | 0.0310 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | artist | 412 | -0.0225 | -0.0084 | -0.0003 | 0.0179 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_10_19 | 199 | -0.0031 | -0.0157 | 0.0097 | 0.0219 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_mid | 242 | -0.0027 | -0.0175 | -0.0083 | 0.0012 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_20_49 | 90 | -0.0059 | -0.0026 | -0.0184 | 0.0209 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | pred_spread_band | spread_extreme | 438 | 0.0142 | -0.0085 | -0.0029 | 0.0268 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_020_plus | 402 | 0.0080 | -0.0100 | -0.0009 | 0.0264 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | medium_size | 18 | 0.0032 | 0.0002 | -0.0138 | 0.0623 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | stable_pred_price_band | (-inf, 1264575.052] | 281 | -0.0059 | -0.0017 | 0.0005 | 0.0230 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_5_9 | 435 | 0.0045 | -0.0003 | -0.0003 | 0.0185 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | stable_pred_price_band | (2979253.356, 7498463.56] | 156 | 0.0005 | 0.0001 | 0.0009 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | gap_band | gap_003_005 | 55 | 0.0003 | -0.0001 | -0.0006 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | pred_spread_band | spread_high | 124 | 0.0004 | 0.0000 | 0.0004 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | qwidth_band | qwidth_extreme | 301 | -0.0006 | -0.0001 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | stable_pred_price_band | (-inf, 1264575.052] | 281 | -0.0006 | -0.0001 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | qwidth_band | qwidth_high | 185 | -0.0006 | 0.0000 | -0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_n_band | n_10_19 | 199 | 0.0005 | 0.0001 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | gap_band | gap_010_020 | 128 | -0.0003 | -0.0000 | 0.0004 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | gap_band | gap_000_003 | 119 | -0.0005 | -0.0000 | -0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | artist_size | 224 | -0.0005 | -0.0001 | 0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | stable_pred_price_band | (1264575.052, 2979253.356] | 171 | 0.0004 | -0.0000 | -0.0001 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | qwidth_band | qwidth_mid | 242 | 0.0004 | 0.0000 | -0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_n_band | n_5_9 | 435 | 0.0003 | -0.0001 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | artist | 412 | -0.0002 | 0.0000 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | gap_band | gap_005_010 | 125 | -0.0000 | -0.0000 | 0.0001 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_n_band | n_20_49 | 90 | 0.0000 | 0.0001 | -0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | qwidth_band | qwidth_low | 101 | 0.0000 | 0.0000 | 0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | stable_pred_price_band | (7498463.56, inf] | 221 | 0.0000 | 0.0000 | 0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | gap_band | gap_020_plus | 402 | 0.0000 | 0.0000 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | pred_spread_band | spread_extreme | 438 | 0.0000 | -0.0000 | -0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | artist_medium_support_size | 91 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | pred_spread_band | spread_low_mid | 267 | 0.0000 | -0.0000 | 0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_n_band | n_50_plus | 105 | 0.0000 | -0.0000 | 0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | global | 18 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | medium_size | 18 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | medium_support_size | 66 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | stable_pred_price_band | (2979253.356, 7498463.56] | 156 | 0.0010 | 0.0001 | 0.0017 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | gap_band | gap_003_005 | 55 | 0.0007 | -0.0001 | -0.0013 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_high | 124 | 0.0008 | 0.0001 | 0.0008 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_extreme | 301 | -0.0015 | -0.0001 | -0.0000 | -0.0005 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_high | 185 | -0.0013 | 0.0000 | -0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_10_19 | 199 | 0.0011 | 0.0002 | -0.0000 | -0.0004 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | gap_band | gap_000_003 | 119 | -0.0011 | -0.0001 | -0.0001 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | gap_band | gap_010_020 | 128 | -0.0005 | -0.0000 | 0.0007 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_level | artist_size | 224 | -0.0011 | -0.0001 | 0.0000 | -0.0004 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | stable_pred_price_band | (1264575.052, 2979253.356] | 171 | 0.0009 | -0.0000 | -0.0002 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_mid | 242 | 0.0008 | 0.0001 | -0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_5_9 | 435 | 0.0007 | -0.0001 | -0.0000 | -0.0004 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_level | artist | 412 | -0.0007 | 0.0000 | -0.0000 | -0.0004 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | gap_band | gap_005_010 | 125 | -0.0001 | -0.0001 | 0.0002 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_low_mid | 267 | -0.0004 | -0.0000 | 0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | stable_pred_price_band | (-inf, 1264575.052] | 281 | 0.0001 | -0.0001 | -0.0000 | -0.0005 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_20_49 | 90 | 0.0000 | 0.0001 | -0.0001 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | stable_pred_price_band | (7498463.56, inf] | 221 | 0.0000 | 0.0001 | 0.0000 | -0.0001 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | qwidth_band | qwidth_low | 101 | 0.0000 | 0.0001 | 0.0000 | -0.0002 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | gap_band | gap_020_plus | 402 | 0.0000 | 0.0000 | -0.0000 | -0.0004 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | pred_spread_band | spread_extreme | 438 | 0.0000 | -0.0000 | -0.0000 | -0.0004 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_level | artist_medium_support_size | 91 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_n_band | n_50_plus | 105 | 0.0000 | -0.0000 | 0.0000 | -0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_level | global | 18 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_level | medium_size | 18 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | svc_group_level | medium_support_size | 66 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_10_19 | 162 | 0.0019 | -0.0018 | -0.0650 | -0.0011 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_high | 107 | -0.0046 | -0.0064 | 0.0506 | -0.0010 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_extreme | 127 | -0.0157 | -0.0033 | 0.0381 | -0.0005 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_extreme | 145 | -0.0067 | -0.0026 | 0.0439 | 0.0004 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | stable_pred_price_band | (7498463.56, inf] | 159 | 0.0071 | 0.0016 | -0.0365 | 0.0032 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_20_49 | 62 | -0.0093 | -0.0005 | -0.0334 | 0.0002 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | stable_pred_price_band | (1264575.052, 2979253.356] | 145 | 0.0082 | -0.0040 | -0.0263 | -0.0045 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_5_9 | 366 | 0.0074 | 0.0010 | 0.0232 | 0.0009 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_low_mid | 373 | 0.0026 | 0.0031 | -0.0162 | 0.0012 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_020_plus | 111 | -0.0156 | -0.0012 | -0.0046 | -0.0008 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist_size | 65 | -0.0068 | -0.0068 | 0.0070 | -0.0006 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_003_005 | 77 | 0.0039 | 0.0031 | 0.0092 | 0.0013 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist | 295 | -0.0006 | 0.0005 | 0.0150 | 0.0001 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist_medium_support_size | 247 | 0.0023 | 0.0014 | 0.0120 | 0.0011 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_50_plus | 17 | 0.0108 | 0.0010 | 0.0037 | 0.0041 |
| fixed_confirmation | test | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_000_003 | 128 | -0.0008 | 0.0034 | 0.0107 | 0.0018 |

## 7. 계수/구간 해석

- PP-HCOEF33은 새 계수를 학습하지 않음.
- 아래 계수는 HCOEF32 후보가 사용한 방향 일치 segment 해석을 재첨부한 것.

| candidate | source_candidate | feature | coefficient | direction | interpretation | experiment_note |
| --- | --- | --- | --- | --- | --- | --- |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p025_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0319 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/0.0075, artist residual/move 0.0616/0.0111 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_all3_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & svc_group_n_band=n_5_9 | 0.0511 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0616/-0.0034, artist residual/move 0.0616/-0.0039 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level=artist | 0.0500 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0006, artist residual/move 0.0111/0.0022 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 0.0425 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0819/0.0062, artist residual/move 0.0819/0.0030 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | svc_group_level=artist | 0.0595 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p05 | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 0.0205 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0819/-0.0019, artist residual/move 0.0819/-0.0085 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level=artist | 0.0603 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0111/0.0003, artist residual/move 0.0111/-0.0015 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |
| hcoef32_s03_mape_dir_top2_w0p05_cap0p0025 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band=qwidth_extreme & gap_band=gap_010_020 | 0.0208 | 방향 일치 적용 구간 | stable 잔차 방향과 source 이동 방향이 row/artist OOF 양쪽에서 일치하고 중앙 절대 잔차가 줄어든 segment. row residual/move 0.0819/-0.0019, artist residual/move 0.0819/-0.0085 | PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증 |

## 8. 잔차/큰 오차 구간

| scope | split | candidate | segment_col | segment_value | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 | over_2x_n | under_half_n | delta_MdAPE_vs_candidate_overall | delta_MAPE_vs_candidate_overall | delta_p95_APE_vs_candidate_overall | median_residual_log | over_50pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | medium_support_size | 66 | 0.4181 | 0.5088 | 1.1162 | 0.9316 | 0.3636 | 0.5909 | 12 | 14 | 0.1401 | 0.1315 | 0.1292 | -0.0715 | 0.4091 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_50_plus | 105 | 0.5325 | 0.5600 | 1.0880 | 1.0454 | 0.2667 | 0.4476 | 13 | 42 | 0.2546 | 0.1827 | 0.1009 | 0.5257 | 0.5524 |
| 0604_stress | 0604_ex50 | current_70_30 | service_confidence_tier | high | 22 | 0.5918 | 0.5668 | 1.0862 | 0.8226 | 0.3636 | 0.4545 | 5 | 4 | 0.3138 | 0.1895 | 0.0991 | 0.1379 | 0.5455 |
| 0604_stress | 0604_ex50 | current_70_30 | pred_spread_band | spread_extreme | 438 | 0.4488 | 0.5067 | 1.0206 | 1.7385 | 0.3333 | 0.5434 | 23 | 144 | 0.1709 | 0.1294 | 0.0336 | 0.3172 | 0.4566 |
| 0604_stress | 0604_ex50 | current_70_30 | service_confidence_tier | medium | 308 | 0.2812 | 0.3979 | 1.0085 | 0.7228 | 0.5357 | 0.7045 | 16 | 59 | 0.0032 | 0.0206 | 0.0214 | 0.0374 | 0.2955 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_020_plus | 402 | 0.4302 | 0.5054 | 1.0000 | 1.7996 | 0.3433 | 0.5672 | 18 | 129 | 0.1522 | 0.1280 | 0.0129 | 0.2961 | 0.4328 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_high | 185 | 0.2549 | 0.3810 | 0.9966 | 0.9949 | 0.5514 | 0.7514 | 9 | 28 | -0.0230 | 0.0037 | 0.0096 | 0.0782 | 0.2486 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_extreme | 301 | 0.3750 | 0.4420 | 0.9959 | 1.9726 | 0.4086 | 0.6279 | 7 | 100 | 0.0971 | 0.0646 | 0.0088 | 0.3569 | 0.3721 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_5_9 | 435 | 0.2484 | 0.3352 | 0.9871 | 1.6347 | 0.5701 | 0.7609 | 9 | 63 | -0.0296 | -0.0421 | 0.0000 | 0.0819 | 0.2391 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | artist | 412 | 0.3063 | 0.3774 | 0.9871 | 1.5835 | 0.4927 | 0.7403 | 13 | 63 | 0.0283 | 0.0000 | 0.0000 | 0.0866 | 0.2597 |
| 0604_stress | 0604_ex50 | current_70_30 | service_confidence_tier | low | 499 | 0.2689 | 0.3563 | 0.9726 | 1.5831 | 0.5291 | 0.7315 | 9 | 90 | -0.0090 | -0.0211 | -0.0145 | 0.1014 | 0.2685 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_005_010 | 125 | 0.1531 | 0.2572 | 0.9461 | 0.7607 | 0.7600 | 0.9120 | 6 | 3 | -0.1248 | -0.1201 | -0.0410 | 0.0641 | 0.0880 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | medium_size | 18 | 0.7774 | 0.6869 | 0.9043 | 1.2389 | 0.1111 | 0.2222 | 1 | 12 | 0.4995 | 0.3095 | -0.0827 | 1.3750 | 0.7778 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_20_49 | 90 | 0.1979 | 0.3351 | 0.8965 | 0.6260 | 0.6000 | 0.7667 | 3 | 13 | -0.0800 | -0.0423 | -0.0906 | 0.0328 | 0.2333 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_mid | 242 | 0.2432 | 0.3387 | 0.8870 | 0.4745 | 0.5950 | 0.7479 | 12 | 22 | -0.0348 | -0.0387 | -0.1001 | 0.0003 | 0.2521 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_n_band | n_10_19 | 199 | 0.2854 | 0.3922 | 0.8850 | 0.7570 | 0.5377 | 0.7286 | 5 | 35 | 0.0075 | 0.0149 | -0.1021 | 0.0401 | 0.2714 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_010_020 | 128 | 0.2248 | 0.3419 | 0.8656 | 0.5226 | 0.5469 | 0.6875 | 5 | 16 | -0.0531 | -0.0354 | -0.1214 | -0.0556 | 0.3125 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | artist_size | 224 | 0.2138 | 0.3533 | 0.8487 | 1.0062 | 0.6071 | 0.7098 | 4 | 49 | -0.0641 | -0.0240 | -0.1383 | 0.0782 | 0.2902 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | global | 18 | 0.6453 | 0.6603 | 0.8423 | 1.2349 | 0.0000 | 0.1667 | 0 | 14 | 0.3673 | 0.2830 | -0.1447 | 0.9898 | 0.8333 |
| 0604_stress | 0604_ex50 | current_70_30 | qwidth_band | qwidth_low | 101 | 0.1977 | 0.2707 | 0.7769 | 0.4180 | 0.6733 | 0.8218 | 2 | 3 | -0.0802 | -0.1067 | -0.2102 | 0.0214 | 0.1782 |
| 0604_stress | 0604_ex50 | current_70_30 | pred_spread_band | spread_high | 124 | 0.2182 | 0.2749 | 0.7671 | 0.7736 | 0.6452 | 0.8952 | 3 | 3 | -0.0598 | -0.1025 | -0.2199 | -0.0591 | 0.1048 |
| 0604_stress | 0604_ex50 | current_70_30 | svc_group_level | artist_medium_support_size | 91 | 0.1735 | 0.2238 | 0.7597 | 0.7716 | 0.7912 | 0.9011 | 0 | 1 | -0.1045 | -0.1535 | -0.2273 | 0.0077 | 0.0989 |
| 0604_stress | 0604_ex50 | current_70_30 | pred_spread_band | spread_low_mid | 267 | 0.1275 | 0.2127 | 0.6786 | 0.3262 | 0.7903 | 0.9101 | 4 | 6 | -0.1504 | -0.1646 | -0.3085 | 0.0281 | 0.0899 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_000_003 | 119 | 0.1066 | 0.1953 | 0.5444 | 0.3186 | 0.7983 | 0.9244 | 1 | 4 | -0.1713 | -0.1820 | -0.4427 | 0.0401 | 0.0756 |
| 0604_stress | 0604_ex50 | current_70_30 | gap_band | gap_003_005 | 55 | 0.0809 | 0.1908 | 0.5325 | 0.3080 | 0.7091 | 0.9455 | 0 | 1 | -0.1971 | -0.1865 | -0.4545 | 0.0305 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | medium_support_size | 66 | 0.4587 | 0.4940 | 1.0628 | 0.9488 | 0.3485 | 0.5909 | 8 | 14 | 0.1946 | 0.1198 | 0.0795 | -0.0274 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_50_plus | 105 | 0.5539 | 0.5499 | 1.0240 | 1.0477 | 0.2667 | 0.4286 | 9 | 42 | 0.2898 | 0.1757 | 0.0407 | 0.6034 | 0.5714 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | service_confidence_tier | high | 22 | 0.5646 | 0.5608 | 1.0227 | 0.7972 | 0.3636 | 0.4545 | 4 | 4 | 0.3004 | 0.1866 | 0.0394 | 0.1282 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_extreme | 438 | 0.4587 | 0.5029 | 1.0000 | 1.7219 | 0.3333 | 0.5479 | 19 | 135 | 0.1946 | 0.1287 | 0.0167 | 0.2706 | 0.4521 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_020_plus | 402 | 0.4587 | 0.5068 | 0.9999 | 1.7841 | 0.3234 | 0.5622 | 17 | 120 | 0.1946 | 0.1326 | 0.0166 | 0.2589 | 0.4378 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_extreme | 301 | 0.3816 | 0.4375 | 0.9958 | 1.9551 | 0.4186 | 0.6246 | 7 | 99 | 0.1175 | 0.0633 | 0.0125 | 0.3320 | 0.3754 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_high | 185 | 0.2293 | 0.3727 | 0.9863 | 0.9868 | 0.5514 | 0.7514 | 6 | 22 | -0.0348 | -0.0016 | 0.0030 | 0.0704 | 0.2486 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_5_9 | 435 | 0.2293 | 0.3286 | 0.9863 | 1.6194 | 0.5747 | 0.7586 | 9 | 61 | -0.0348 | -0.0456 | 0.0030 | 0.0576 | 0.2414 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist | 412 | 0.3017 | 0.3781 | 0.9863 | 1.5681 | 0.4903 | 0.7451 | 13 | 59 | 0.0376 | 0.0039 | 0.0030 | 0.0758 | 0.2549 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | service_confidence_tier | low | 499 | 0.2586 | 0.3507 | 0.9721 | 1.5696 | 0.5331 | 0.7255 | 9 | 88 | -0.0055 | -0.0235 | -0.0112 | 0.0964 | 0.2745 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | service_confidence_tier | medium | 308 | 0.2601 | 0.3989 | 0.9578 | 0.7136 | 0.5130 | 0.6981 | 13 | 53 | -0.0040 | 0.0247 | -0.0256 | 0.0208 | 0.3019 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_005_010 | 125 | 0.1478 | 0.2491 | 0.9489 | 0.7519 | 0.7840 | 0.9040 | 5 | 3 | -0.1163 | -0.1251 | -0.0344 | 0.0325 | 0.0960 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_20_49 | 90 | 0.2014 | 0.3471 | 0.9285 | 0.6211 | 0.5889 | 0.7444 | 3 | 12 | -0.0627 | -0.0271 | -0.0549 | 0.0688 | 0.2556 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_mid | 242 | 0.2359 | 0.3402 | 0.9047 | 0.4661 | 0.5579 | 0.7314 | 11 | 21 | -0.0282 | -0.0341 | -0.0786 | -0.0085 | 0.2686 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_010_020 | 128 | 0.2089 | 0.3371 | 0.9047 | 0.5119 | 0.5625 | 0.6719 | 3 | 16 | -0.0552 | -0.0371 | -0.0786 | -0.0323 | 0.3281 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | medium_size | 18 | 0.7688 | 0.6698 | 0.8790 | 1.2154 | 0.1111 | 0.2222 | 1 | 12 | 0.5047 | 0.2956 | -0.1043 | 1.3550 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_n_band | n_10_19 | 199 | 0.2938 | 0.3935 | 0.8749 | 0.7413 | 0.5075 | 0.7286 | 5 | 30 | 0.0297 | 0.0193 | -0.1084 | 0.0208 | 0.2714 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist_size | 224 | 0.1909 | 0.3435 | 0.8541 | 0.9887 | 0.5982 | 0.7143 | 4 | 44 | -0.0732 | -0.0307 | -0.1292 | 0.0576 | 0.2857 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | global | 18 | 0.6284 | 0.6743 | 0.8526 | 1.2269 | 0.0000 | 0.0556 | 0 | 14 | 0.3643 | 0.3000 | -0.1307 | 0.9384 | 0.9444 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | qwidth_band | qwidth_low | 101 | 0.1603 | 0.2700 | 0.8397 | 0.4093 | 0.6832 | 0.8218 | 2 | 3 | -0.1038 | -0.1042 | -0.1437 | 0.0019 | 0.1782 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_high | 124 | 0.2031 | 0.2771 | 0.8111 | 0.7707 | 0.6210 | 0.8387 | 3 | 3 | -0.0610 | -0.0971 | -0.1722 | -0.0510 | 0.1613 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | svc_group_level | artist_medium_support_size | 91 | 0.1603 | 0.2276 | 0.8094 | 0.7775 | 0.7802 | 0.8352 | 0 | 2 | -0.1038 | -0.1466 | -0.1739 | -0.0109 | 0.1648 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | pred_spread_band | spread_low_mid | 267 | 0.1169 | 0.2082 | 0.6400 | 0.3230 | 0.7828 | 0.9101 | 4 | 7 | -0.1472 | -0.1660 | -0.3433 | 0.0208 | 0.0899 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_000_003 | 119 | 0.0970 | 0.1855 | 0.5118 | 0.3112 | 0.7815 | 0.9244 | 1 | 5 | -0.1671 | -0.1887 | -0.4715 | 0.0208 | 0.0756 |
| 0604_stress | 0604_ex50 | hcoef29_core_component_delta_s0p5_cap0p08 | gap_band | gap_003_005 | 55 | 0.1000 | 0.1843 | 0.4901 | 0.2973 | 0.7091 | 0.9455 | 0 | 1 | -0.1641 | -0.1899 | -0.4932 | 0.0069 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_020_plus | 402 | 0.4424 | 0.4947 | 0.9990 | 1.8215 | 0.3358 | 0.5821 | 16 | 133 | 0.1635 | 0.1269 | 0.0544 | 0.3533 | 0.4179 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | pred_spread_band | spread_extreme | 438 | 0.4545 | 0.4945 | 0.9971 | 1.7600 | 0.3242 | 0.5731 | 15 | 149 | 0.1757 | 0.1266 | 0.0525 | 0.3722 | 0.4269 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_extreme | 301 | 0.3944 | 0.4442 | 0.9864 | 1.9983 | 0.4053 | 0.6246 | 5 | 103 | 0.1155 | 0.0763 | 0.0418 | 0.4334 | 0.3754 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_5_9 | 435 | 0.2428 | 0.3307 | 0.9864 | 1.6492 | 0.5816 | 0.7954 | 7 | 65 | -0.0361 | -0.0372 | 0.0418 | 0.1408 | 0.2046 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | artist | 412 | 0.2968 | 0.3682 | 0.9864 | 1.5965 | 0.5121 | 0.7621 | 11 | 67 | 0.0180 | 0.0003 | 0.0418 | 0.1447 | 0.2379 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_high | 185 | 0.2709 | 0.3671 | 0.9778 | 1.0110 | 0.5243 | 0.7730 | 5 | 29 | -0.0079 | -0.0007 | 0.0332 | 0.1531 | 0.2270 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | medium_support_size | 66 | 0.4678 | 0.4613 | 0.9776 | 0.9570 | 0.3485 | 0.5909 | 3 | 14 | 0.1889 | 0.0934 | 0.0330 | 0.0335 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | service_confidence_tier | low | 499 | 0.2708 | 0.3521 | 0.9741 | 1.6009 | 0.5391 | 0.7655 | 7 | 92 | -0.0081 | -0.0158 | 0.0295 | 0.1664 | 0.2345 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_50_plus | 105 | 0.5693 | 0.5323 | 0.9468 | 1.0804 | 0.2667 | 0.4476 | 4 | 42 | 0.2904 | 0.1644 | 0.0022 | 0.6307 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | service_confidence_tier | medium | 308 | 0.2831 | 0.3819 | 0.9274 | 0.7405 | 0.5325 | 0.7110 | 11 | 63 | 0.0042 | 0.0140 | -0.0172 | 0.0919 | 0.2890 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | service_confidence_tier | high | 22 | 0.5472 | 0.5290 | 0.9267 | 0.8115 | 0.3636 | 0.4545 | 1 | 4 | 0.2683 | 0.1612 | -0.0179 | 0.1759 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_20_49 | 90 | 0.1948 | 0.3378 | 0.8982 | 0.6465 | 0.5889 | 0.7778 | 3 | 13 | -0.0840 | -0.0301 | -0.0463 | 0.1249 | 0.2222 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_mid | 242 | 0.2354 | 0.3209 | 0.8758 | 0.4723 | 0.6157 | 0.7975 | 9 | 24 | -0.0435 | -0.0469 | -0.0688 | 0.0624 | 0.2025 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_n_band | n_10_19 | 199 | 0.2831 | 0.3760 | 0.8738 | 0.7733 | 0.5377 | 0.7437 | 5 | 39 | 0.0042 | 0.0081 | -0.0708 | 0.0939 | 0.2563 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | medium_size | 18 | 0.7750 | 0.6742 | 0.8652 | 1.2785 | 0.1111 | 0.2222 | 1 | 12 | 0.4961 | 0.3063 | -0.0794 | 1.4300 | 0.7778 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | artist_size | 224 | 0.2312 | 0.3517 | 0.8617 | 1.0274 | 0.5848 | 0.7545 | 4 | 50 | -0.0477 | -0.0161 | -0.0829 | 0.1262 | 0.2455 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | global | 18 | 0.6643 | 0.6718 | 0.8572 | 1.2949 | 0.0000 | 0.1667 | 0 | 14 | 0.3854 | 0.3040 | -0.0874 | 1.0448 | 0.8333 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_005_010 | 125 | 0.1674 | 0.2508 | 0.8141 | 0.7672 | 0.7840 | 0.9120 | 1 | 3 | -0.1115 | -0.1170 | -0.1305 | 0.1130 | 0.0880 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_010_020 | 128 | 0.2442 | 0.3162 | 0.8098 | 0.5277 | 0.5469 | 0.7812 | 1 | 16 | -0.0347 | -0.0516 | -0.1348 | 0.0335 | 0.2188 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | qwidth_band | qwidth_low | 101 | 0.1984 | 0.2542 | 0.7128 | 0.4122 | 0.7228 | 0.8614 | 0 | 3 | -0.0805 | -0.1137 | -0.2318 | 0.0517 | 0.1386 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | pred_spread_band | spread_high | 124 | 0.1732 | 0.2547 | 0.7105 | 0.7772 | 0.6935 | 0.9032 | 2 | 3 | -0.1056 | -0.1131 | -0.2341 | 0.0253 | 0.0968 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | svc_group_level | artist_medium_support_size | 91 | 0.1657 | 0.2176 | 0.6690 | 0.7821 | 0.8132 | 0.9011 | 0 | 2 | -0.1132 | -0.1503 | -0.2756 | 0.0513 | 0.0989 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | pred_spread_band | spread_low_mid | 267 | 0.1388 | 0.2126 | 0.6001 | 0.3384 | 0.7978 | 0.9288 | 2 | 7 | -0.1400 | -0.1552 | -0.3445 | 0.0834 | 0.0712 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_000_003 | 119 | 0.1103 | 0.1959 | 0.5617 | 0.3360 | 0.7983 | 0.9328 | 1 | 5 | -0.1686 | -0.1720 | -0.3829 | 0.0939 | 0.0672 |
| 0604_stress | 0604_ex50 | hcoef29_risk_guarded_component_s0p5_cap0p08 | gap_band | gap_003_005 | 55 | 0.1478 | 0.1985 | 0.4910 | 0.3252 | 0.7818 | 0.9455 | 0 | 2 | -0.1311 | -0.1693 | -0.4536 | 0.0716 | 0.0545 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_level | medium_support_size | 66 | 0.4289 | 0.4961 | 1.0854 | 0.9327 | 0.3485 | 0.5909 | 8 | 14 | 0.1562 | 0.1218 | 0.1020 | -0.0465 | 0.4091 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | svc_group_n_band | n_50_plus | 105 | 0.5334 | 0.5505 | 1.0364 | 1.0398 | 0.2667 | 0.4476 | 9 | 42 | 0.2608 | 0.1761 | 0.0530 | 0.5507 | 0.5524 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | service_confidence_tier | high | 22 | 0.5812 | 0.5579 | 1.0347 | 0.8120 | 0.3636 | 0.4545 | 4 | 4 | 0.3085 | 0.1835 | 0.0512 | 0.1321 | 0.5455 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | pred_spread_band | spread_extreme | 438 | 0.4403 | 0.5030 | 1.0000 | 1.7330 | 0.3196 | 0.5365 | 19 | 142 | 0.1676 | 0.1286 | 0.0165 | 0.2969 | 0.4635 |
| 0604_stress | 0604_ex50 | hcoef32_s03_all3_dir_top2_w0p025_cap0p001 | gap_band | gap_020_plus | 402 | 0.4344 | 0.5047 | 0.9999 | 1.7949 | 0.3159 | 0.5597 | 17 | 127 | 0.1617 | 0.1304 | 0.0165 | 0.2795 | 0.4403 |

## 9. 다음 방향

- HCOEF32 확인 후보가 repeated all3 기준을 넘지 못하면 점 예측용 ultra-micro 이동은 운영 기본값으로 올리지 않음.
- 다음 성능 개선은 fixed tiny improvement가 아니라 기준가 생성 방식 재탐색과 Huber 저차원 계수 재학습으로 이동.
- 방향 일치 segment는 가격 범위, 신뢰도, 수동 검수 정책에서 재사용 가능.

## 10. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/repeated_iteration_metrics.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/residual_analysis.csv`
- `outputs/segment_impact.csv`
- `outputs/selected_candidates.csv`
- `artifacts/experiment_config.json`