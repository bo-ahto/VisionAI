# PP-HCOEF16 Warm PP-V8/service component OOF 재검증

- 작성일: 2026-06-08 01:45
- 목적: HCOEF15에서 0604 성능이 좋았던 PP-V8/service component를 validation OOF 기준 Huber 입력 피처로 재검증
- 기준 후보: `hcoef2_size_reliability_cap005_s050`
- 0604 라벨은 stress test로만 사용하고 후보 선택에는 사용하지 않음
- PP-V8 component는 validation/test에서 `PP-SVC3`와 `PP-V8` 산출물이 동일함을 감사함
  - validation/test PP-V8 proxy 일치율: `1.0000`
  - validation/test PP-V8 proxy 최대 차이: `0.000000`

## 1. 실행 결론

- PP-V8/service component 단독은 0604에서는 강하지만 validation/test에서는 HCOEF 안정 후보보다 약함.
- HCOEF 안정 후보에 PP-V8을 작은 비율로 섞거나 Huber residual 피처로 넣는 후보를 반복 OOF로 검증함.
- 채택 여부는 0604가 아니라 row OOF, artist OOF, fixed test p95 guard로 판단함.

## 2. fixed validation/test/0604 주요 후보

| split | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 |
| validation | hcoef_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 |
| validation | ppv8_service_proxy | 519 | 0.1544 | 0.2544 | 0.8084 | 0.3721 | 0.0284 | 0.0462 | 0.1604 |
| test | current_70_30 | 607 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 |
| test | hcoef_stable | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| test | ppv8_service_proxy | 607 | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.0244 | 0.0086 | 0.1247 |
| 0604_ex50 | current_70_30 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |
| 0604_ex50 | hcoef_stable | 829 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 |
| 0604_ex50 | ppv8_service_proxy | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | -0.0433 | -0.0385 | -0.0561 |
| validation | hcoef16_stable_ppv8_blend_w010 | 519 | 0.1272 | 0.2094 | 0.6567 | 0.3260 | 0.0012 | 0.0012 | 0.0087 |
| test | hcoef16_stable_ppv8_blend_w010 | 607 | 0.1415 | 0.2707 | 0.8308 | 0.3961 | 0.0027 | -0.0023 | 0.0245 |
| 0604_ex50 | hcoef16_stable_ppv8_blend_w010 | 829 | 0.2582 | 0.3638 | 0.9784 | 1.2247 | -0.0148 | -0.0106 | -0.0051 |
| validation | hcoef16_stable_ppv8_blend_w025 | 519 | 0.1319 | 0.2125 | 0.6723 | 0.3289 | 0.0059 | 0.0043 | 0.0244 |
| test | hcoef16_stable_ppv8_blend_w025 | 607 | 0.1436 | 0.2691 | 0.8392 | 0.3934 | 0.0048 | -0.0039 | 0.0328 |
| 0604_ex50 | hcoef16_stable_ppv8_blend_w025 | 829 | 0.2542 | 0.3507 | 0.9669 | 1.1054 | -0.0189 | -0.0237 | -0.0165 |

## 3. fixed test 상위 후보

| candidate | method | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef_stable | baseline_stable | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2728 | 0.8091 | 0.3987 | 0.0006 | -0.0002 | 0.0027 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2728 | 0.8091 | 0.3987 | 0.0006 | -0.0002 | 0.0027 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | -0.0000 | 0.0027 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | -0.0000 | 0.0027 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | 0.0000 | 0.0027 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | residual_huber | 607 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | 0.0000 | 0.0027 |
| current_70_30 | baseline_reference | 607 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 |
| hcoef16_stable_ppv8_blend_w010 | direct | 607 | 0.1415 | 0.2707 | 0.8308 | 0.3961 | 0.0027 | -0.0023 | 0.0245 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p03_s0p25 | residual_huber | 607 | 0.1417 | 0.2726 | 0.8117 | 0.3987 | 0.0029 | -0.0004 | 0.0053 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p03_s0p25 | residual_huber | 607 | 0.1417 | 0.2726 | 0.8117 | 0.3987 | 0.0029 | -0.0004 | 0.0053 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p03_s0p25 | residual_huber | 607 | 0.1417 | 0.2729 | 0.8117 | 0.3989 | 0.0029 | -0.0001 | 0.0053 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p03_s0p25 | residual_huber | 607 | 0.1417 | 0.2729 | 0.8117 | 0.3989 | 0.0029 | -0.0001 | 0.0053 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | residual_huber | 607 | 0.1422 | 0.2729 | 0.8117 | 0.3989 | 0.0034 | -0.0001 | 0.0053 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | residual_huber | 607 | 0.1422 | 0.2729 | 0.8117 | 0.3989 | 0.0034 | -0.0001 | 0.0053 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p05_s0p25 | residual_huber | 607 | 0.1432 | 0.2728 | 0.8147 | 0.3988 | 0.0044 | -0.0002 | 0.0083 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p5 | residual_huber | 607 | 0.1433 | 0.2731 | 0.8150 | 0.3990 | 0.0045 | 0.0001 | 0.0086 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p5 | residual_huber | 607 | 0.1433 | 0.2731 | 0.8150 | 0.3990 | 0.0045 | 0.0001 | 0.0086 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | residual_huber | 607 | 0.1434 | 0.2727 | 0.8149 | 0.3988 | 0.0046 | -0.0002 | 0.0086 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p5 | residual_huber | 607 | 0.1436 | 0.2731 | 0.8313 | 0.3990 | 0.0048 | 0.0001 | 0.0249 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p25 | residual_huber | 607 | 0.1436 | 0.2728 | 0.8170 | 0.3988 | 0.0048 | -0.0002 | 0.0107 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p5 | residual_huber | 607 | 0.1436 | 0.2731 | 0.8313 | 0.3990 | 0.0048 | 0.0001 | 0.0249 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p25 | residual_huber | 607 | 0.1436 | 0.2728 | 0.8170 | 0.3988 | 0.0048 | -0.0002 | 0.0107 |
| hcoef16_stable_ppv8_blend_w025 | direct | 607 | 0.1436 | 0.2691 | 0.8392 | 0.3934 | 0.0048 | -0.0039 | 0.0328 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p05_s0p25 | residual_huber | 607 | 0.1437 | 0.2723 | 0.8124 | 0.3985 | 0.0049 | -0.0006 | 0.0060 |

_Only first 25 of 44 rows shown._

## 4. 반복 OOF 요약

| candidate | validation_scheme | n_repeats | mean_MdAPE | mean_MAPE | mean_p95_APE | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | all3_improve_prob | row_all3_improve_prob | artist_all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | row_oof | 20 | 0.1259 | 0.2078 | 0.6407 | -0.0001 | -0.0004 | -0.0073 | 0.9500 | 0.9500 | 0.7500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | row_oof | 20 | 0.1259 | 0.2078 | 0.6407 | -0.0001 | -0.0004 | -0.0073 | 0.9500 | 0.9500 | 0.7500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | artist_oof | 20 | 0.1260 | 0.2078 | 0.6408 | -0.0000 | -0.0004 | -0.0072 | 0.7500 | 0.9500 | 0.7500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | artist_oof | 20 | 0.1260 | 0.2078 | 0.6408 | -0.0000 | -0.0004 | -0.0072 | 0.7500 | 0.9500 | 0.7500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | row_oof | 20 | 0.1232 | 0.2072 | 0.6452 | -0.0028 | -0.0010 | -0.0027 | 0.9000 | 0.9000 | 0.7000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p05_s0p5 | row_oof | 20 | 0.1232 | 0.2072 | 0.6453 | -0.0027 | -0.0010 | -0.0027 | 0.9000 | 0.9000 | 0.7000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | artist_oof | 20 | 0.1238 | 0.2075 | 0.6465 | -0.0022 | -0.0007 | -0.0015 | 0.7000 | 0.9000 | 0.7000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p05_s0p5 | artist_oof | 20 | 0.1238 | 0.2075 | 0.6466 | -0.0022 | -0.0007 | -0.0014 | 0.7000 | 0.9000 | 0.7000 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p02_s0p25 | row_oof | 20 | 0.1259 | 0.2079 | 0.6412 | -0.0001 | -0.0003 | -0.0067 | 0.8500 | 0.8500 | 0.4500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p25 | row_oof | 20 | 0.1259 | 0.2079 | 0.6412 | -0.0001 | -0.0003 | -0.0067 | 0.8500 | 0.8500 | 0.4500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p02_s0p25 | artist_oof | 20 | 0.1261 | 0.2079 | 0.6411 | 0.0001 | -0.0003 | -0.0068 | 0.4500 | 0.8500 | 0.4500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p25 | artist_oof | 20 | 0.1261 | 0.2079 | 0.6411 | 0.0001 | -0.0003 | -0.0068 | 0.4500 | 0.8500 | 0.4500 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p25 | row_oof | 20 | 0.1260 | 0.2079 | 0.6408 | -0.0000 | -0.0003 | -0.0072 | 0.8000 | 0.8000 | 0.6500 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p25 | row_oof | 20 | 0.1260 | 0.2079 | 0.6408 | -0.0000 | -0.0003 | -0.0072 | 0.8000 | 0.8000 | 0.6500 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p25 | artist_oof | 20 | 0.1260 | 0.2080 | 0.6409 | 0.0000 | -0.0003 | -0.0071 | 0.6500 | 0.8000 | 0.6500 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p25 | artist_oof | 20 | 0.1260 | 0.2080 | 0.6409 | 0.0000 | -0.0003 | -0.0071 | 0.6500 | 0.8000 | 0.6500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p05_s0p5 | row_oof | 20 | 0.1237 | 0.2074 | 0.6460 | -0.0023 | -0.0008 | -0.0019 | 0.8000 | 0.8000 | 0.4500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p05_s0p5 | row_oof | 20 | 0.1237 | 0.2074 | 0.6460 | -0.0023 | -0.0008 | -0.0019 | 0.8000 | 0.8000 | 0.4500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p05_s0p5 | artist_oof | 20 | 0.1243 | 0.2077 | 0.6473 | -0.0016 | -0.0005 | -0.0006 | 0.4500 | 0.8000 | 0.4500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p05_s0p5 | artist_oof | 20 | 0.1243 | 0.2077 | 0.6473 | -0.0016 | -0.0005 | -0.0006 | 0.4500 | 0.8000 | 0.4500 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p5 | row_oof | 20 | 0.1241 | 0.2075 | 0.6472 | -0.0019 | -0.0007 | -0.0008 | 0.6500 | 0.6500 | 0.4000 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p5 | row_oof | 20 | 0.1241 | 0.2075 | 0.6472 | -0.0019 | -0.0007 | -0.0008 | 0.6500 | 0.6500 | 0.4000 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p5 | artist_oof | 20 | 0.1251 | 0.2079 | 0.6485 | -0.0008 | -0.0003 | 0.0006 | 0.4000 | 0.6500 | 0.4000 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p5 | artist_oof | 20 | 0.1251 | 0.2079 | 0.6485 | -0.0008 | -0.0003 | 0.0006 | 0.4000 | 0.6500 | 0.4000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | row_oof | 20 | 0.1259 | 0.2072 | 0.6410 | -0.0001 | -0.0010 | -0.0070 | 0.5500 | 0.5500 | 0.1500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | artist_oof | 20 | 0.1264 | 0.2074 | 0.6422 | 0.0004 | -0.0008 | -0.0057 | 0.1500 | 0.5500 | 0.1500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | row_oof | 20 | 0.1260 | 0.2073 | 0.6410 | -0.0000 | -0.0010 | -0.0070 | 0.4500 | 0.4500 | 0.1500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | artist_oof | 20 | 0.1265 | 0.2074 | 0.6423 | 0.0005 | -0.0008 | -0.0057 | 0.1500 | 0.4500 | 0.1500 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p05_s0p25 | row_oof | 20 | 0.1263 | 0.2076 | 0.6458 | 0.0003 | -0.0006 | -0.0021 | 0.3500 | 0.3500 | 0.2000 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p05_s0p25 | row_oof | 20 | 0.1263 | 0.2076 | 0.6458 | 0.0003 | -0.0006 | -0.0021 | 0.3500 | 0.3500 | 0.2000 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p05_s0p25 | artist_oof | 20 | 0.1269 | 0.2078 | 0.6458 | 0.0009 | -0.0004 | -0.0022 | 0.2000 | 0.3500 | 0.2000 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p05_s0p25 | artist_oof | 20 | 0.1269 | 0.2078 | 0.6458 | 0.0009 | -0.0004 | -0.0022 | 0.2000 | 0.3500 | 0.2000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | artist_oof | 20 | 0.1266 | 0.2077 | 0.6446 | 0.0006 | -0.0005 | -0.0034 | 0.2500 | 0.3000 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | row_oof | 20 | 0.1267 | 0.2075 | 0.6430 | 0.0007 | -0.0007 | -0.0050 | 0.3000 | 0.3000 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | artist_oof | 20 | 0.1264 | 0.2077 | 0.6437 | 0.0004 | -0.0005 | -0.0042 | 0.3000 | 0.2500 | 0.3000 |

_Only first 35 of 80 rows shown._

## 5. 후보 선택 판단

| candidate | row_all3_improve_prob | artist_all3_improve_prob | test_MdAPE | test_MAPE | test_p95_APE | test_RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable | passes_repeat_gate | passes_fixed_p95_guard | passes_fixed_all3 | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p25 | 0.8500 | 0.4500 | 0.1394 | 0.2728 | 0.8091 | 0.3987 | 0.0006 | -0.0002 | 0.0027 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p02_s0p25 | 0.8500 | 0.4500 | 0.1394 | 0.2728 | 0.8091 | 0.3987 | 0.0006 | -0.0002 | 0.0027 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p25 | 0.8000 | 0.6500 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | -0.0000 | 0.0027 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p25 | 0.8000 | 0.6500 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | -0.0000 | 0.0027 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | 0.9500 | 0.7500 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | 0.0000 | 0.0027 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | 0.9500 | 0.7500 | 0.1394 | 0.2730 | 0.8091 | 0.3989 | 0.0006 | 0.0000 | 0.0027 | False | False | False | 보류 |
| hcoef16_stable_ppv8_blend_w010 | 0.0000 | 0.0000 | 0.1415 | 0.2707 | 0.8308 | 0.3961 | 0.0027 | -0.0023 | 0.0245 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p03_s0p25 | 0.0000 | 0.1000 | 0.1417 | 0.2726 | 0.8117 | 0.3987 | 0.0029 | -0.0004 | 0.0053 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p03_s0p25 | 0.0000 | 0.1000 | 0.1417 | 0.2726 | 0.8117 | 0.3987 | 0.0029 | -0.0004 | 0.0053 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p03_s0p25 | 0.0000 | 0.1000 | 0.1417 | 0.2729 | 0.8117 | 0.3989 | 0.0029 | -0.0001 | 0.0053 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p03_s0p25 | 0.0000 | 0.1000 | 0.1417 | 0.2729 | 0.8117 | 0.3989 | 0.0029 | -0.0001 | 0.0053 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | 0.2500 | 0.3000 | 0.1422 | 0.2729 | 0.8117 | 0.3989 | 0.0034 | -0.0001 | 0.0053 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | 0.2500 | 0.2500 | 0.1422 | 0.2729 | 0.8117 | 0.3989 | 0.0034 | -0.0001 | 0.0053 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p05_s0p25 | 0.2500 | 0.2500 | 0.1432 | 0.2728 | 0.8147 | 0.3988 | 0.0044 | -0.0002 | 0.0083 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p5 | 0.0000 | 0.0000 | 0.1433 | 0.2731 | 0.8150 | 0.3990 | 0.0045 | 0.0001 | 0.0086 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p5 | 0.0000 | 0.0000 | 0.1433 | 0.2731 | 0.8150 | 0.3990 | 0.0045 | 0.0001 | 0.0086 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | 0.3000 | 0.2500 | 0.1434 | 0.2727 | 0.8149 | 0.3988 | 0.0046 | -0.0002 | 0.0086 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p5 | 0.6500 | 0.4000 | 0.1436 | 0.2731 | 0.8313 | 0.3990 | 0.0048 | 0.0001 | 0.0249 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p25 | 0.1000 | 0.0500 | 0.1436 | 0.2728 | 0.8170 | 0.3988 | 0.0048 | -0.0002 | 0.0107 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p5 | 0.6500 | 0.4000 | 0.1436 | 0.2731 | 0.8313 | 0.3990 | 0.0048 | 0.0001 | 0.0249 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p25 | 0.1000 | 0.0500 | 0.1436 | 0.2728 | 0.8170 | 0.3988 | 0.0048 | -0.0002 | 0.0107 | False | False | False | 보류 |
| hcoef16_stable_ppv8_blend_w025 | 0.0000 | 0.0000 | 0.1436 | 0.2691 | 0.8392 | 0.3934 | 0.0048 | -0.0039 | 0.0328 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p05_s0p25 | 0.3500 | 0.2000 | 0.1437 | 0.2723 | 0.8124 | 0.3985 | 0.0049 | -0.0006 | 0.0060 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p05_s0p25 | 0.3500 | 0.2000 | 0.1437 | 0.2723 | 0.8124 | 0.3985 | 0.0049 | -0.0006 | 0.0060 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p03_s0p5 | 0.1500 | 0.0000 | 0.1444 | 0.2731 | 0.8216 | 0.3990 | 0.0056 | 0.0001 | 0.0153 | False | False | False | 보류 |
| hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p03_s0p5 | 0.1500 | 0.0000 | 0.1444 | 0.2731 | 0.8216 | 0.3990 | 0.0056 | 0.0001 | 0.0153 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p01_cap0p02_s0p5 | 0.0000 | 0.0000 | 0.1445 | 0.2727 | 0.8150 | 0.3987 | 0.0057 | -0.0003 | 0.0086 | False | False | False | 보류 |
| hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p02_s0p5 | 0.0000 | 0.0000 | 0.1445 | 0.2727 | 0.8150 | 0.3987 | 0.0057 | -0.0003 | 0.0086 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p5 | 0.0000 | 0.0000 | 0.1445 | 0.2732 | 0.8150 | 0.3991 | 0.0057 | 0.0002 | 0.0086 | False | False | False | 보류 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p5 | 0.0000 | 0.0000 | 0.1445 | 0.2732 | 0.8150 | 0.3991 | 0.0057 | 0.0002 | 0.0086 | False | False | False | 보류 |

_Only first 30 of 40 rows shown._

## 6. 잔차 요약

| split | candidate | method | n | median_residual_log | ape_median | ape_mean | ape_p95 | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | ppv8_service_proxy | component | 829 | 0.0703 | 0.2298 | 0.3359 | 0.9273 | 31 | 89 |
| 0604_ex50 | hcoef16_ppv8_proxy_direct | direct | 829 | 0.0703 | 0.2298 | 0.3359 | 0.9273 | 31 | 89 |
| 0604_ex50 | hcoef16_stable_ppv8_blend_w050 | direct | 829 | 0.0589 | 0.2424 | 0.3376 | 0.9195 | 16 | 118 |
| 0604_ex50 | hcoef16_stable_ppv8_blend_w025 | direct | 829 | 0.0591 | 0.2542 | 0.3507 | 0.9669 | 20 | 131 |
| 0604_ex50 | hcoef16_stable_ppv8_blend_w010 | direct | 829 | 0.0614 | 0.2582 | 0.3638 | 0.9784 | 26 | 144 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p05_s0p5 | residual_huber | 829 | 0.0574 | 0.2647 | 0.3734 | 0.9793 | 22 | 150 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p5 | residual_huber | 829 | 0.0566 | 0.2648 | 0.3734 | 0.9760 | 22 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p5 | residual_huber | 829 | 0.0566 | 0.2648 | 0.3734 | 0.9760 | 22 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p03_s0p5 | residual_huber | 829 | 0.0612 | 0.2651 | 0.3734 | 0.9792 | 24 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | residual_huber | 829 | 0.0572 | 0.2651 | 0.3734 | 0.9793 | 22 | 150 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p03_s0p5 | residual_huber | 829 | 0.0612 | 0.2651 | 0.3734 | 0.9792 | 24 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p5 | residual_huber | 829 | 0.0586 | 0.2661 | 0.3737 | 0.9791 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p5 | residual_huber | 829 | 0.0586 | 0.2661 | 0.3737 | 0.9791 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p5 | residual_huber | 829 | 0.0609 | 0.2661 | 0.3736 | 0.9792 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p5 | residual_huber | 829 | 0.0609 | 0.2661 | 0.3736 | 0.9792 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p05_s0p25 | residual_huber | 829 | 0.0592 | 0.2677 | 0.3737 | 0.9792 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p05_s0p25 | residual_huber | 829 | 0.0592 | 0.2677 | 0.3737 | 0.9792 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | residual_huber | 829 | 0.0592 | 0.2679 | 0.3737 | 0.9792 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | residual_huber | 829 | 0.0579 | 0.2679 | 0.3734 | 0.9792 | 24 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | residual_huber | 829 | 0.0574 | 0.2679 | 0.3734 | 0.9792 | 24 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | residual_huber | 829 | 0.0587 | 0.2679 | 0.3738 | 0.9808 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p03_s0p25 | residual_huber | 829 | 0.0587 | 0.2679 | 0.3738 | 0.9808 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p03_s0p25 | residual_huber | 829 | 0.0587 | 0.2679 | 0.3738 | 0.9808 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | residual_huber | 829 | 0.0589 | 0.2681 | 0.3738 | 0.9808 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p05_s0p25 | residual_huber | 829 | 0.0592 | 0.2681 | 0.3737 | 0.9792 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | residual_huber | 829 | 0.0591 | 0.2694 | 0.3740 | 0.9835 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | residual_huber | 829 | 0.0591 | 0.2694 | 0.3740 | 0.9835 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p001_cap0p02_s0p25 | residual_huber | 829 | 0.0591 | 0.2698 | 0.3740 | 0.9835 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_core_reliability_alpha0p01_cap0p02_s0p25 | residual_huber | 829 | 0.0591 | 0.2698 | 0.3740 | 0.9835 | 26 | 151 |
| 0604_ex50 | hcoef16_resid_ppv8_gap_reliability_alpha0p001_cap0p02_s0p5 | residual_huber | 829 | 0.0612 | 0.2698 | 0.3734 | 0.9792 | 26 | 152 |

_Only first 30 of 88 rows shown._

## 7. 계수 해석

| candidate | feature_set | feature | coefficient_on_scaled_feature | abs_coefficient | direction | alpha | cap | strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | ppv8_pred_stack | hcoef_stable | 2.2452 | 2.2452 | 가격 보정값을 올리는 방향 | 0.0010 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9904 | 0.9904 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | ppv8_pred_stack | current_70_30 | -0.8260 | 0.8260 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p25 | ppv8_pred_stack | ppv8_service_proxy | -0.4224 | 0.4224 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p5 | ppv8_pred_stack | hcoef_stable | 2.2452 | 2.2452 | 가격 보정값을 올리는 방향 | 0.0010 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p5 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9904 | 0.9904 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p5 | ppv8_pred_stack | current_70_30 | -0.8260 | 0.8260 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p02_s0p5 | ppv8_pred_stack | ppv8_service_proxy | -0.4224 | 0.4224 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | ppv8_pred_stack | hcoef_stable | 2.2452 | 2.2452 | 가격 보정값을 올리는 방향 | 0.0010 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9904 | 0.9904 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | ppv8_pred_stack | current_70_30 | -0.8260 | 0.8260 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p25 | ppv8_pred_stack | ppv8_service_proxy | -0.4224 | 0.4224 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | ppv8_pred_stack | hcoef_stable | 2.2452 | 2.2452 | 가격 보정값을 올리는 방향 | 0.0010 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9904 | 0.9904 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | ppv8_pred_stack | current_70_30 | -0.8260 | 0.8260 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p03_s0p5 | ppv8_pred_stack | ppv8_service_proxy | -0.4224 | 0.4224 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | ppv8_pred_stack | hcoef_stable | 2.2452 | 2.2452 | 가격 보정값을 올리는 방향 | 0.0010 | 0.0500 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9904 | 0.9904 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0500 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | ppv8_pred_stack | current_70_30 | -0.8260 | 0.8260 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0500 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p25 | ppv8_pred_stack | ppv8_service_proxy | -0.4224 | 0.4224 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0500 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | ppv8_pred_stack | hcoef_stable | 2.2452 | 2.2452 | 가격 보정값을 올리는 방향 | 0.0010 | 0.0500 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9904 | 0.9904 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0500 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | ppv8_pred_stack | current_70_30 | -0.8260 | 0.8260 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0500 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p001_cap0p05_s0p5 | ppv8_pred_stack | ppv8_service_proxy | -0.4224 | 0.4224 | 가격 보정값을 낮추는 방향 | 0.0010 | 0.0500 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | ppv8_pred_stack | hcoef_stable | 2.1987 | 2.1987 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9696 | 0.9696 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | ppv8_pred_stack | current_70_30 | -0.8087 | 0.8087 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p25 | ppv8_pred_stack | ppv8_service_proxy | -0.4139 | 0.4139 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0200 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p5 | ppv8_pred_stack | hcoef_stable | 2.1987 | 2.1987 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p5 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9696 | 0.9696 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p5 | ppv8_pred_stack | current_70_30 | -0.8087 | 0.8087 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p02_s0p5 | ppv8_pred_stack | ppv8_service_proxy | -0.4139 | 0.4139 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0200 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | ppv8_pred_stack | hcoef_stable | 2.1987 | 2.1987 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9696 | 0.9696 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | ppv8_pred_stack | current_70_30 | -0.8087 | 0.8087 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p25 | ppv8_pred_stack | ppv8_service_proxy | -0.4139 | 0.4139 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0300 | 0.2500 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | ppv8_pred_stack | hcoef_stable | 2.1987 | 2.1987 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | ppv8_pred_stack | svc_numeric_seed_mean | -0.9696 | 0.9696 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | ppv8_pred_stack | current_70_30 | -0.8087 | 0.8087 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0300 | 0.5000 |
| hcoef16_resid_ppv8_pred_stack_alpha0p01_cap0p03_s0p5 | ppv8_pred_stack | ppv8_service_proxy | -0.4139 | 0.4139 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0300 | 0.5000 |

## 8. 해석

- PP-V8/service component는 0604 최신 라벨에서 HCOEF 안정 후보보다 낮은 MdAPE/MAPE/p95를 보였음.
- 그러나 validation/test의 기존 고정 split에서는 PP-V8 단독이 HCOEF 안정 후보보다 약함.
- 따라서 PP-V8을 전체 대체 모델로 쓰는 것보다, gap/coverage를 이용한 제한적 Huber 입력으로 검증하는 접근이 맞음.
- row OOF와 artist OOF gate를 통과하지 못한 후보는 0604 성능이 좋아도 운영 후보로 채택하지 않음.
- PP-V8 관련 계수는 service component를 얼마나 신뢰할지보다, stable 후보와 PP-V8의 차이가 남은 residual을 설명하는지를 확인하는 용도로 해석해야 함.

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/selected_candidates.csv`
- `outputs/input_component_audit.csv`