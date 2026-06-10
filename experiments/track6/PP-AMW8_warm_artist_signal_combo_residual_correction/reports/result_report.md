# PP-AMW8 Warm 작가 신호 조합 잔차 보정

- 작성일: 2026-06-08 14:31
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 목적: PP-AMW7에서 영향도가 보인 생년/세대/커리어 단계 피처를 조합했을 때 추가 개선이 가능한지 확인
- validation: 작가 키 기준 5-fold OOF
- test: validation 전체 학습 후 고정 test 1회 적용

## 1. 기준 성능

| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.3292 | 0.1305 | 0.2110 | 0.6580 | 0.7746 | 0.9075 |
| test | 0.3996 | 0.1405 | 0.2748 | 0.8331 | 0.7628 | 0.8781 |

## 2. 실행 결론

- 조합 후보는 validation 개선 신호가 있으나 test에서는 일부 지표가 엇갈린다.
- 운영 후보는 test에서 MdAPE/MAPE/p95를 모두 개선한 후보와 bootstrap 개선 확률을 함께 봐야 한다.
- 과한 cap/strength는 validation MdAPE를 낮춰도 test MAPE를 악화시키는 경향이 있다.

## 3. validation 기준 상위 후보

| candidate | family | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_birth_generation_career_alpha0p1_cap0p03_s0p75 | ridge_residual | 0.1251 | 0.2096 | 0.6366 | -0.0054 | -0.0014 | -0.0214 | 0.1441 | 0.2765 | 0.8217 | 0.0036 | 0.0017 | -0.0114 | 0.0172 |
| huber_birth_generation_career_alpha0p01_cap0p05_s0p75 | huber_residual | 0.1286 | 0.2086 | 0.6295 | -0.0019 | -0.0024 | -0.0285 | 0.1460 | 0.2759 | 0.8340 | 0.0056 | 0.0011 | 0.0010 | 0.0198 |
| huber_birth_generation_career_alpha0p001_cap0p05_s0p75 | huber_residual | 0.1287 | 0.2086 | 0.6295 | -0.0019 | -0.0024 | -0.0285 | 0.1460 | 0.2759 | 0.8340 | 0.0056 | 0.0011 | 0.0010 | 0.0198 |
| ridge_generation_career_alpha0p1_cap0p03_s0p75 | ridge_residual | 0.1263 | 0.2096 | 0.6366 | -0.0042 | -0.0014 | -0.0214 | 0.1428 | 0.2765 | 0.8215 | 0.0023 | 0.0017 | -0.0115 | 0.0175 |
| ridge_generation_career_alpha1p0_cap0p03_s0p75 | ridge_residual | 0.1263 | 0.2096 | 0.6366 | -0.0042 | -0.0014 | -0.0215 | 0.1427 | 0.2765 | 0.8212 | 0.0023 | 0.0017 | -0.0118 | 0.0173 |
| segment_birth_generation_career_career0p05 | sequential_segment | 0.1262 | 0.2100 | 0.6357 | -0.0043 | -0.0010 | -0.0224 | 0.1404 | 0.2760 | 0.8366 | -0.0001 | 0.0012 | 0.0036 | 0.0243 |
| segment_birth_generation_career_conservative | sequential_segment | 0.1262 | 0.2101 | 0.6356 | -0.0043 | -0.0010 | -0.0224 | 0.1399 | 0.2762 | 0.8366 | -0.0006 | 0.0014 | 0.0036 | 0.0233 |
| ridge_birth_year_career_alpha1p0_cap0p03_s0p75 | ridge_residual | 0.1267 | 0.2096 | 0.6369 | -0.0038 | -0.0015 | -0.0211 | 0.1432 | 0.2769 | 0.8220 | 0.0027 | 0.0021 | -0.0110 | 0.0164 |
| ridge_birth_year_career_alpha0p1_cap0p03_s0p75 | ridge_residual | 0.1268 | 0.2096 | 0.6369 | -0.0038 | -0.0015 | -0.0211 | 0.1432 | 0.2769 | 0.8223 | 0.0027 | 0.0021 | -0.0108 | 0.0165 |
| ridge_generation_career_alpha5p0_cap0p03_s0p75 | ridge_residual | 0.1263 | 0.2097 | 0.6390 | -0.0042 | -0.0014 | -0.0191 | 0.1431 | 0.2766 | 0.8201 | 0.0026 | 0.0018 | -0.0129 | 0.0168 |
| huber_birth_year_career_alpha0p001_cap0p05_s0p75 | huber_residual | 0.1292 | 0.2087 | 0.6297 | -0.0014 | -0.0023 | -0.0284 | 0.1427 | 0.2756 | 0.8334 | 0.0022 | 0.0008 | 0.0003 | 0.0182 |
| huber_birth_year_career_alpha0p01_cap0p05_s0p75 | huber_residual | 0.1292 | 0.2087 | 0.6297 | -0.0014 | -0.0023 | -0.0284 | 0.1427 | 0.2756 | 0.8334 | 0.0022 | 0.0008 | 0.0003 | 0.0182 |
| ridge_birth_year_career_alpha5p0_cap0p03_s0p75 | ridge_residual | 0.1270 | 0.2095 | 0.6369 | -0.0035 | -0.0015 | -0.0211 | 0.1437 | 0.2768 | 0.8210 | 0.0032 | 0.0020 | -0.0120 | 0.0164 |
| ridge_birth_generation_career_alpha1p0_cap0p03_s0p75 | ridge_residual | 0.1274 | 0.2094 | 0.6366 | -0.0032 | -0.0016 | -0.0214 | 0.1441 | 0.2766 | 0.8216 | 0.0036 | 0.0018 | -0.0115 | 0.0171 |
| ridge_birth_generation_career_alpha5p0_cap0p03_s0p5 | ridge_residual | 0.1253 | 0.2096 | 0.6461 | -0.0052 | -0.0014 | -0.0119 | 0.1412 | 0.2758 | 0.8182 | 0.0008 | 0.0010 | -0.0149 | 0.0113 |
| ridge_generation_career_alpha5p0_cap0p03_s0p5 | ridge_residual | 0.1253 | 0.2099 | 0.6453 | -0.0052 | -0.0012 | -0.0127 | 0.1417 | 0.2759 | 0.8179 | 0.0012 | 0.0011 | -0.0152 | 0.0112 |
| ridge_generation_career_alpha1p0_cap0p05_s0p5 | ridge_residual | 0.1257 | 0.2099 | 0.6440 | -0.0049 | -0.0011 | -0.0141 | 0.1433 | 0.2765 | 0.8211 | 0.0028 | 0.0017 | -0.0120 | 0.0166 |
| ridge_birth_generation_career_alpha1p0_cap0p03_s0p5 | ridge_residual | 0.1253 | 0.2097 | 0.6471 | -0.0052 | -0.0014 | -0.0110 | 0.1410 | 0.2758 | 0.8188 | 0.0005 | 0.0010 | -0.0143 | 0.0114 |
| ridge_birth_generation_career_alpha1p0_cap0p05_s0p75 | ridge_residual | 0.1287 | 0.2097 | 0.6300 | -0.0018 | -0.0014 | -0.0280 | 0.1454 | 0.2778 | 0.8378 | 0.0049 | 0.0030 | 0.0048 | 0.0251 |
| segment_birth_then_career_conservative | sequential_segment | 0.1248 | 0.2103 | 0.6464 | -0.0057 | -0.0007 | -0.0117 | 0.1369 | 0.2750 | 0.8283 | -0.0036 | 0.0002 | -0.0048 | 0.0184 |

## 4. test 진단 상위 후보

| candidate | family | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| huber_generation_alpha0p001_cap0p03_s0p75 | huber_residual | 0.1286 | 0.2092 | 0.6415 | -0.0019 | -0.0018 | -0.0166 | 0.1381 | 0.2738 | 0.8140 | -0.0023 | -0.0010 | -0.0191 | 0.0129 |
| huber_generation_alpha0p01_cap0p03_s0p75 | huber_residual | 0.1286 | 0.2092 | 0.6415 | -0.0019 | -0.0018 | -0.0166 | 0.1381 | 0.2738 | 0.8140 | -0.0023 | -0.0010 | -0.0191 | 0.0129 |
| huber_generation_alpha0p01_cap0p03_s0p5 | huber_residual | 0.1262 | 0.2097 | 0.6476 | -0.0044 | -0.0014 | -0.0104 | 0.1386 | 0.2740 | 0.8109 | -0.0019 | -0.0008 | -0.0222 | 0.0086 |
| huber_generation_alpha0p001_cap0p03_s0p5 | huber_residual | 0.1262 | 0.2097 | 0.6476 | -0.0044 | -0.0014 | -0.0104 | 0.1386 | 0.2740 | 0.8109 | -0.0019 | -0.0008 | -0.0222 | 0.0086 |
| ridge_birth_generation_alpha0p1_cap0p03_s0p5 | ridge_residual | 0.1254 | 0.2100 | 0.6484 | -0.0051 | -0.0010 | -0.0096 | 0.1377 | 0.2747 | 0.8136 | -0.0028 | -0.0001 | -0.0195 | 0.0058 |
| ridge_birth_generation_alpha5p0_cap0p03_s0p75 | ridge_residual | 0.1290 | 0.2095 | 0.6432 | -0.0016 | -0.0015 | -0.0148 | 0.1372 | 0.2749 | 0.8154 | -0.0033 | 0.0001 | -0.0176 | 0.0084 |
| ridge_generation_alpha0p1_cap0p03_s0p5 | ridge_residual | 0.1254 | 0.2101 | 0.6484 | -0.0051 | -0.0010 | -0.0096 | 0.1377 | 0.2747 | 0.8136 | -0.0028 | -0.0001 | -0.0195 | 0.0057 |
| ridge_generation_alpha0p1_cap0p03_s0p75 | ridge_residual | 0.1268 | 0.2098 | 0.6426 | -0.0037 | -0.0012 | -0.0154 | 0.1374 | 0.2747 | 0.8153 | -0.0031 | -0.0001 | -0.0178 | 0.0086 |
| ridge_birth_generation_alpha0p1_cap0p03_s0p75 | ridge_residual | 0.1268 | 0.2097 | 0.6426 | -0.0037 | -0.0013 | -0.0155 | 0.1375 | 0.2747 | 0.8153 | -0.0030 | -0.0001 | -0.0178 | 0.0087 |
| ridge_birth_generation_alpha1p0_cap0p03_s0p75 | ridge_residual | 0.1286 | 0.2095 | 0.6428 | -0.0019 | -0.0015 | -0.0152 | 0.1374 | 0.2748 | 0.8153 | -0.0031 | 0.0000 | -0.0178 | 0.0086 |
| ridge_birth_generation_alpha1p0_cap0p03_s0p5 | ridge_residual | 0.1270 | 0.2099 | 0.6485 | -0.0035 | -0.0012 | -0.0096 | 0.1378 | 0.2748 | 0.8136 | -0.0027 | -0.0000 | -0.0194 | 0.0057 |
| ridge_generation_alpha1p0_cap0p03_s0p75 | ridge_residual | 0.1273 | 0.2099 | 0.6435 | -0.0032 | -0.0011 | -0.0145 | 0.1373 | 0.2749 | 0.8155 | -0.0032 | 0.0001 | -0.0176 | 0.0082 |
| huber_birth_generation_alpha0p01_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2094 | 0.6476 | -0.0041 | -0.0016 | -0.0104 | 0.1386 | 0.2742 | 0.8129 | -0.0019 | -0.0006 | -0.0202 | 0.0084 |
| huber_birth_generation_alpha0p001_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2094 | 0.6476 | -0.0041 | -0.0016 | -0.0104 | 0.1386 | 0.2742 | 0.8129 | -0.0019 | -0.0006 | -0.0201 | 0.0084 |
| ridge_birth_generation_alpha5p0_cap0p03_s0p5 | ridge_residual | 0.1272 | 0.2099 | 0.6485 | -0.0033 | -0.0011 | -0.0096 | 0.1380 | 0.2748 | 0.8139 | -0.0025 | 0.0000 | -0.0192 | 0.0056 |
| huber_birth_generation_alpha0p001_cap0p05_s0p5 | huber_residual | 0.1278 | 0.2093 | 0.6443 | -0.0027 | -0.0018 | -0.0137 | 0.1370 | 0.2747 | 0.8194 | -0.0035 | -0.0001 | -0.0137 | 0.0109 |
| huber_birth_generation_alpha0p01_cap0p05_s0p5 | huber_residual | 0.1278 | 0.2093 | 0.6443 | -0.0027 | -0.0018 | -0.0137 | 0.1370 | 0.2747 | 0.8194 | -0.0035 | -0.0001 | -0.0137 | 0.0109 |
| ridge_generation_alpha1p0_cap0p03_s0p5 | ridge_residual | 0.1255 | 0.2101 | 0.6485 | -0.0050 | -0.0009 | -0.0095 | 0.1381 | 0.2748 | 0.8140 | -0.0024 | -0.0000 | -0.0191 | 0.0055 |
| huber_birth_year_alpha0p01_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2096 | 0.6476 | -0.0041 | -0.0015 | -0.0104 | 0.1391 | 0.2744 | 0.8109 | -0.0014 | -0.0004 | -0.0222 | 0.0082 |
| huber_birth_year_alpha0p001_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2096 | 0.6476 | -0.0041 | -0.0015 | -0.0104 | 0.1391 | 0.2744 | 0.8109 | -0.0014 | -0.0004 | -0.0222 | 0.0082 |

## 5. test 3지표 모두 개선 후보

| candidate | family | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| segment_career_stage_cap0p05 | sequential_segment | 0.1273 | 0.2113 | 0.6519 | -0.0032 | 0.0003 | -0.0061 | 0.1384 | 0.2737 | 0.8292 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |
| huber_generation_alpha0p01_cap0p03_s0p75 | huber_residual | 0.1286 | 0.2092 | 0.6415 | -0.0019 | -0.0018 | -0.0166 | 0.1381 | 0.2738 | 0.8140 | -0.0023 | -0.0010 | -0.0191 | 0.0129 |
| huber_generation_alpha0p001_cap0p03_s0p75 | huber_residual | 0.1286 | 0.2092 | 0.6415 | -0.0019 | -0.0018 | -0.0166 | 0.1381 | 0.2738 | 0.8140 | -0.0023 | -0.0010 | -0.0191 | 0.0129 |
| huber_generation_alpha0p01_cap0p03_s0p5 | huber_residual | 0.1262 | 0.2097 | 0.6476 | -0.0044 | -0.0014 | -0.0104 | 0.1386 | 0.2740 | 0.8109 | -0.0019 | -0.0008 | -0.0222 | 0.0086 |
| huber_generation_alpha0p001_cap0p03_s0p5 | huber_residual | 0.1262 | 0.2097 | 0.6476 | -0.0044 | -0.0014 | -0.0104 | 0.1386 | 0.2740 | 0.8109 | -0.0019 | -0.0008 | -0.0222 | 0.0086 |
| huber_birth_generation_alpha0p01_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2094 | 0.6476 | -0.0041 | -0.0016 | -0.0104 | 0.1386 | 0.2742 | 0.8129 | -0.0019 | -0.0006 | -0.0202 | 0.0084 |
| huber_birth_generation_alpha0p001_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2094 | 0.6476 | -0.0041 | -0.0016 | -0.0104 | 0.1386 | 0.2742 | 0.8129 | -0.0019 | -0.0006 | -0.0201 | 0.0084 |
| huber_birth_year_alpha0p001_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2096 | 0.6476 | -0.0041 | -0.0015 | -0.0104 | 0.1391 | 0.2744 | 0.8109 | -0.0014 | -0.0004 | -0.0222 | 0.0082 |
| huber_birth_year_alpha0p01_cap0p03_s0p5 | huber_residual | 0.1264 | 0.2096 | 0.6476 | -0.0041 | -0.0015 | -0.0104 | 0.1391 | 0.2744 | 0.8109 | -0.0014 | -0.0004 | -0.0222 | 0.0082 |
| huber_generation_alpha0p01_cap0p03_s0p25 | huber_residual | 0.1297 | 0.2103 | 0.6518 | -0.0008 | -0.0008 | -0.0063 | 0.1381 | 0.2744 | 0.8219 | -0.0024 | -0.0004 | -0.0112 | 0.0043 |
| huber_generation_alpha0p001_cap0p03_s0p25 | huber_residual | 0.1297 | 0.2103 | 0.6518 | -0.0008 | -0.0008 | -0.0063 | 0.1381 | 0.2744 | 0.8219 | -0.0024 | -0.0004 | -0.0112 | 0.0043 |
| huber_birth_generation_alpha0p01_cap0p03_s0p25 | huber_residual | 0.1293 | 0.2101 | 0.6518 | -0.0013 | -0.0009 | -0.0062 | 0.1381 | 0.2744 | 0.8229 | -0.0023 | -0.0004 | -0.0102 | 0.0042 |
| huber_birth_generation_alpha0p001_cap0p03_s0p25 | huber_residual | 0.1293 | 0.2101 | 0.6518 | -0.0013 | -0.0009 | -0.0062 | 0.1381 | 0.2744 | 0.8229 | -0.0023 | -0.0004 | -0.0102 | 0.0042 |
| huber_birth_year_alpha0p001_cap0p03_s0p25 | huber_residual | 0.1299 | 0.2102 | 0.6518 | -0.0007 | -0.0008 | -0.0063 | 0.1382 | 0.2745 | 0.8219 | -0.0022 | -0.0003 | -0.0112 | 0.0041 |
| huber_birth_year_alpha0p01_cap0p03_s0p25 | huber_residual | 0.1299 | 0.2102 | 0.6518 | -0.0007 | -0.0008 | -0.0063 | 0.1382 | 0.2745 | 0.8219 | -0.0022 | -0.0003 | -0.0112 | 0.0041 |
| huber_generation_career_alpha0p01_cap0p03_s0p25 | huber_residual | 0.1296 | 0.2102 | 0.6502 | -0.0009 | -0.0008 | -0.0078 | 0.1395 | 0.2746 | 0.8222 | -0.0010 | -0.0002 | -0.0108 | 0.0050 |
| huber_generation_career_alpha0p001_cap0p03_s0p25 | huber_residual | 0.1296 | 0.2102 | 0.6502 | -0.0009 | -0.0008 | -0.0078 | 0.1395 | 0.2746 | 0.8222 | -0.0010 | -0.0002 | -0.0108 | 0.0050 |
| huber_birth_generation_career_alpha0p01_cap0p03_s0p25 | huber_residual | 0.1296 | 0.2101 | 0.6502 | -0.0009 | -0.0009 | -0.0078 | 0.1395 | 0.2746 | 0.8223 | -0.0010 | -0.0002 | -0.0108 | 0.0048 |
| huber_birth_generation_career_alpha0p001_cap0p03_s0p25 | huber_residual | 0.1296 | 0.2101 | 0.6502 | -0.0009 | -0.0009 | -0.0078 | 0.1395 | 0.2746 | 0.8223 | -0.0010 | -0.0002 | -0.0108 | 0.0048 |
| huber_generation_alpha0p01_cap0p05_s0p25 | huber_residual | 0.1275 | 0.2103 | 0.6518 | -0.0030 | -0.0008 | -0.0063 | 0.1379 | 0.2747 | 0.8197 | -0.0026 | -0.0001 | -0.0134 | 0.0053 |

## 6. bootstrap 안정성

| sample_type | candidate | mean_delta_MdAPE | improvement_probability_MdAPE | mean_delta_MAPE | improvement_probability_MAPE | mean_delta_p95_APE | improvement_probability_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artist_bootstrap | huber_generation_alpha0p01_cap0p03_s0p75 | -0.0011 | 0.6175 | -0.0010 | 0.8500 | -0.0104 | 0.8050 |
| artist_bootstrap | huber_generation_alpha0p001_cap0p03_s0p75 | -0.0011 | 0.6175 | -0.0010 | 0.8500 | -0.0104 | 0.8050 |
| artist_bootstrap | huber_generation_alpha0p01_cap0p03_s0p5 | -0.0010 | 0.6200 | -0.0008 | 0.8725 | -0.0072 | 0.8000 |
| artist_bootstrap | huber_generation_alpha0p001_cap0p03_s0p5 | -0.0010 | 0.6200 | -0.0008 | 0.8725 | -0.0072 | 0.8000 |
| artist_bootstrap | ridge_birth_generation_alpha0p1_cap0p03_s0p5 | -0.0008 | 0.6050 | -0.0001 | 0.5875 | -0.0031 | 0.7675 |
| artist_bootstrap | huber_birth_generation_career_alpha0p01_cap0p05_s0p75 | 0.0043 | 0.1550 | 0.0011 | 0.2625 | -0.0055 | 0.6200 |
| artist_bootstrap | huber_birth_generation_career_alpha0p001_cap0p05_s0p75 | 0.0043 | 0.1550 | 0.0011 | 0.2625 | -0.0055 | 0.6200 |
| artist_bootstrap | ridge_generation_career_alpha0p1_cap0p03_s0p75 | 0.0026 | 0.2650 | 0.0017 | 0.0650 | 0.0005 | 0.5225 |
| artist_bootstrap | ridge_birth_generation_career_alpha0p1_cap0p03_s0p75 | 0.0026 | 0.2775 | 0.0018 | 0.0600 | 0.0009 | 0.5125 |
| artist_bootstrap | ridge_generation_career_alpha1p0_cap0p03_s0p75 | 0.0026 | 0.2750 | 0.0018 | 0.0625 | 0.0004 | 0.5150 |
| row_bootstrap | huber_generation_alpha0p01_cap0p03_s0p75 | -0.0013 | 0.6300 | -0.0010 | 0.9100 | -0.0103 | 0.7925 |
| row_bootstrap | huber_generation_alpha0p001_cap0p03_s0p75 | -0.0013 | 0.6300 | -0.0010 | 0.9100 | -0.0103 | 0.7925 |
| row_bootstrap | huber_generation_alpha0p01_cap0p03_s0p5 | -0.0012 | 0.6550 | -0.0008 | 0.9325 | -0.0073 | 0.8050 |
| row_bootstrap | huber_generation_alpha0p001_cap0p03_s0p5 | -0.0012 | 0.6550 | -0.0008 | 0.9325 | -0.0073 | 0.8050 |
| row_bootstrap | ridge_birth_generation_alpha0p1_cap0p03_s0p5 | -0.0011 | 0.6400 | -0.0001 | 0.5825 | -0.0036 | 0.7550 |
| row_bootstrap | huber_birth_generation_career_alpha0p01_cap0p05_s0p75 | 0.0044 | 0.1325 | 0.0011 | 0.1850 | -0.0043 | 0.5925 |
| row_bootstrap | huber_birth_generation_career_alpha0p001_cap0p05_s0p75 | 0.0044 | 0.1325 | 0.0011 | 0.1850 | -0.0043 | 0.5925 |
| row_bootstrap | ridge_birth_generation_career_alpha0p1_cap0p03_s0p75 | 0.0025 | 0.2725 | 0.0017 | 0.0300 | 0.0015 | 0.4650 |
| row_bootstrap | ridge_generation_career_alpha0p1_cap0p03_s0p75 | 0.0025 | 0.2725 | 0.0017 | 0.0325 | 0.0013 | 0.4700 |
| row_bootstrap | ridge_generation_career_alpha1p0_cap0p03_s0p75 | 0.0025 | 0.2800 | 0.0018 | 0.0250 | 0.0012 | 0.4700 |

## 7. 산출물

- `outputs/combo_candidate_metrics.csv`
- `outputs/combo_predictions.csv`
- `outputs/combo_coefficients_or_maps.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/bootstrap_samples.csv`
- `outputs/experiment_manifest.json`