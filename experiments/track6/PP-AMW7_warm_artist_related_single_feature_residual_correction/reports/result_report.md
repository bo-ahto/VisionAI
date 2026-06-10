# PP-AMW7 Warm 작가 관련 단일 피처 잔차 보정 실험

- 작성일: 2026-06-08 14:22
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 목적: 작가 관련 컬럼을 묶음이 아니라 단일 컬럼별로 독립 보정해 실제 잔차 설명력과 영향도를 확인
- validation: 작가 키 기준 5-fold OOF 보정
- test: validation 전체로 만든 보정맵을 고정 test에 1회 적용
- 보정 방식: 단일 피처 구간별 validation median residual을 shrink 후 cap으로 제한

## 1. 기준 성능

| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.3292 | 0.1305 | 0.2110 | 0.6580 | 0.7746 | 0.9075 |
| test | 0.3996 | 0.1405 | 0.2748 | 0.8331 | 0.7628 | 0.8781 |

## 2. 실행 결론

- 단일 피처 단위로 보면 validation OOF 개선과 test 개선이 항상 일치하지 않는다.
- 따라서 validation OOF 기준 상위 후보와 test 진단 상위 후보를 분리해서 본다.
- 직접 식별자 성격의 `artist_key`/작가명 계열은 test에서는 좋아 보일 수 있어도 OOF 안정성 기준으로 해석해야 한다.
- 운영 후보 판단은 `validation_delta_*`와 `test_delta_*`, 평균 보정폭, 커버리지를 함께 확인한다.

## 3. 피처별 validation 기준 최선 후보

| feature | kind | min_n | cap | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_meta_birth_year | numeric | 30 | 0.0800 | 0.1231 | 0.2103 | 0.6456 | -0.0074 | -0.0007 | -0.0125 | 0.1446 | 0.2779 | 0.8361 | 0.0041 | 0.0031 | 0.0031 | 0.0185 |
| artist_birth_generation_bin | categorical | 20 | 0.0500 | 0.1263 | 0.2098 | 0.6440 | -0.0042 | -0.0012 | -0.0141 | 0.1389 | 0.2759 | 0.8268 | -0.0016 | 0.0011 | -0.0063 | 0.0126 |
| artist_exhibition_total_count_log | numeric | 30 | 0.0300 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1415 | 0.2753 | 0.8387 | 0.0010 | 0.0005 | 0.0056 | 0.0048 |
| artist_exhibition_solo_count_log | numeric | 20 | 0.0300 | 0.1271 | 0.2115 | 0.6503 | -0.0034 | 0.0004 | -0.0077 | 0.1395 | 0.2750 | 0.8362 | -0.0009 | 0.0002 | 0.0031 | 0.0048 |
| artist_meta_career_stage | numeric | 20 | 0.0500 | 0.1273 | 0.2113 | 0.6519 | -0.0032 | 0.0003 | -0.0061 | 0.1384 | 0.2737 | 0.8292 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |
| artist_exhibition_solo_count | numeric | 20 | 0.0500 | 0.1286 | 0.2112 | 0.6503 | -0.0019 | 0.0001 | -0.0078 | 0.1406 | 0.2738 | 0.8389 | 0.0002 | -0.0010 | 0.0058 | 0.0114 |
| artist_meta_followers | numeric | 20 | 0.0300 | 0.1292 | 0.2127 | 0.6459 | -0.0013 | 0.0016 | -0.0122 | 0.1435 | 0.2777 | 0.8334 | 0.0030 | 0.0029 | 0.0003 | 0.0097 |
| artist_meta_followers_log1p | numeric | 20 | 0.0300 | 0.1303 | 0.2126 | 0.6438 | -0.0002 | 0.0016 | -0.0142 | 0.1422 | 0.2755 | 0.8361 | 0.0018 | 0.0007 | 0.0031 | 0.0050 |
| artist_exhibition_available_count | categorical | 10 | 0.0300 | 0.1280 | 0.2115 | 0.6615 | -0.0025 | 0.0005 | 0.0035 | 0.1410 | 0.2759 | 0.8327 | 0.0005 | 0.0011 | -0.0004 | 0.0037 |
| gallery_feature_source | categorical | 10 | 0.0300 | 0.1276 | 0.2118 | 0.6627 | -0.0029 | 0.0007 | 0.0047 | 0.1397 | 0.2754 | 0.8333 | -0.0007 | 0.0006 | 0.0002 | 0.0037 |
| gallery_tier_any_available_flag | categorical | 10 | 0.0300 | 0.1276 | 0.2118 | 0.6628 | -0.0029 | 0.0007 | 0.0047 | 0.1397 | 0.2754 | 0.8334 | -0.0007 | 0.0006 | 0.0003 | 0.0037 |
| artist_exhibition_fair_count_missing | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| artist_meta_for_sale_ratio | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| artist_meta_for_sale_ratio_missing | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| artist_meta_has_international | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| gallery_city_count | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| gallery_city_count_log | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| gallery_tier_raw_available_flag | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| gallery_tier_raw_bucket | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| gallery_tier_raw_numeric | categorical | 10 | 0.0300 | 0.1280 | 0.2118 | 0.6627 | -0.0025 | 0.0008 | 0.0047 | 0.1401 | 0.2754 | 0.8337 | -0.0004 | 0.0006 | 0.0007 | 0.0035 |
| artist_meta_for_sale_works_log1p | numeric | 20 | 0.0300 | 0.1307 | 0.2128 | 0.6446 | 0.0002 | 0.0018 | -0.0134 | 0.1408 | 0.2759 | 0.8255 | 0.0004 | 0.0011 | -0.0076 | 0.0078 |
| artist_meta_market_depth_gap | numeric | 20 | 0.0300 | 0.1283 | 0.2126 | 0.6583 | -0.0022 | 0.0015 | 0.0003 | 0.1424 | 0.2758 | 0.8345 | 0.0019 | 0.0010 | 0.0014 | 0.0030 |
| artist_exhibition_fair_count_log | numeric | 30 | 0.0300 | 0.1291 | 0.2119 | 0.6588 | -0.0014 | 0.0009 | 0.0008 | 0.1420 | 0.2753 | 0.8349 | 0.0015 | 0.0005 | 0.0018 | 0.0020 |
| artist_meta_followers_missing | categorical | 10 | 0.0300 | 0.1285 | 0.2121 | 0.6618 | -0.0020 | 0.0010 | 0.0037 | 0.1449 | 0.2763 | 0.8362 | 0.0044 | 0.0015 | 0.0032 | 0.0063 |
| artist_meta_total_works_missing | categorical | 10 | 0.0300 | 0.1285 | 0.2121 | 0.6618 | -0.0020 | 0.0010 | 0.0037 | 0.1449 | 0.2763 | 0.8362 | 0.0044 | 0.0015 | 0.0032 | 0.0063 |
| artist_exhibition_fair_count | numeric | 20 | 0.0300 | 0.1280 | 0.2119 | 0.6655 | -0.0025 | 0.0009 | 0.0074 | 0.1415 | 0.2758 | 0.8355 | 0.0010 | 0.0010 | 0.0024 | 0.0042 |
| artist_entity_suffix | categorical | 20 | 0.0300 | 0.1298 | 0.2118 | 0.6573 | -0.0007 | 0.0008 | -0.0007 | 0.1421 | 0.2755 | 0.8351 | 0.0017 | 0.0007 | 0.0020 | 0.0022 |
| artist_key | categorical | 10 | 0.0300 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.1405 | 0.2748 | 0.8331 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_name_ko | categorical | 10 | 0.0300 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.1405 | 0.2748 | 0.8331 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| artist_name_standardized | categorical | 10 | 0.0300 | 0.1305 | 0.2110 | 0.6580 | 0.0000 | 0.0000 | 0.0000 | 0.1405 | 0.2748 | 0.8331 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 4. validation OOF 상위 후보

| feature | kind | min_n | cap | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_meta_birth_year | numeric | 30 | 0.0800 | 0.1231 | 0.2103 | 0.6456 | -0.0074 | -0.0007 | -0.0125 | 0.1446 | 0.2779 | 0.8361 | 0.0041 | 0.0031 | 0.0031 | 0.0185 |
| artist_birth_generation_bin | categorical | 20 | 0.0500 | 0.1263 | 0.2098 | 0.6440 | -0.0042 | -0.0012 | -0.0141 | 0.1389 | 0.2759 | 0.8268 | -0.0016 | 0.0011 | -0.0063 | 0.0126 |
| artist_birth_generation_bin | categorical | 10 | 0.0500 | 0.1261 | 0.2100 | 0.6440 | -0.0044 | -0.0010 | -0.0141 | 0.1389 | 0.2759 | 0.8268 | -0.0016 | 0.0011 | -0.0063 | 0.0126 |
| artist_meta_birth_year | numeric | 20 | 0.0500 | 0.1261 | 0.2099 | 0.6456 | -0.0044 | -0.0012 | -0.0125 | 0.1382 | 0.2757 | 0.8361 | -0.0023 | 0.0009 | 0.0031 | 0.0148 |
| artist_meta_birth_year | numeric | 30 | 0.0500 | 0.1261 | 0.2099 | 0.6456 | -0.0044 | -0.0012 | -0.0125 | 0.1382 | 0.2757 | 0.8361 | -0.0023 | 0.0009 | 0.0031 | 0.0148 |
| artist_meta_birth_year | numeric | 40 | 0.0500 | 0.1261 | 0.2099 | 0.6456 | -0.0044 | -0.0012 | -0.0125 | 0.1382 | 0.2757 | 0.8361 | -0.0023 | 0.0009 | 0.0031 | 0.0148 |
| artist_meta_birth_year | numeric | 20 | 0.0300 | 0.1263 | 0.2098 | 0.6456 | -0.0042 | -0.0013 | -0.0125 | 0.1370 | 0.2747 | 0.8240 | -0.0035 | -0.0001 | -0.0091 | 0.0116 |
| artist_meta_birth_year | numeric | 30 | 0.0300 | 0.1263 | 0.2098 | 0.6456 | -0.0042 | -0.0013 | -0.0125 | 0.1370 | 0.2747 | 0.8240 | -0.0035 | -0.0001 | -0.0091 | 0.0116 |
| artist_meta_birth_year | numeric | 40 | 0.0300 | 0.1263 | 0.2098 | 0.6456 | -0.0042 | -0.0013 | -0.0125 | 0.1370 | 0.2747 | 0.8240 | -0.0035 | -0.0001 | -0.0091 | 0.0116 |
| artist_birth_generation_bin | categorical | 30 | 0.0500 | 0.1263 | 0.2102 | 0.6437 | -0.0042 | -0.0008 | -0.0143 | 0.1389 | 0.2757 | 0.8268 | -0.0016 | 0.0009 | -0.0063 | 0.0111 |
| artist_birth_generation_bin | categorical | 10 | 0.0300 | 0.1272 | 0.2098 | 0.6440 | -0.0034 | -0.0012 | -0.0141 | 0.1376 | 0.2752 | 0.8239 | -0.0029 | 0.0004 | -0.0092 | 0.0107 |
| artist_birth_generation_bin | categorical | 20 | 0.0300 | 0.1294 | 0.2097 | 0.6440 | -0.0011 | -0.0013 | -0.0141 | 0.1376 | 0.2752 | 0.8239 | -0.0029 | 0.0004 | -0.0092 | 0.0107 |
| artist_exhibition_total_count_log | numeric | 30 | 0.0300 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1415 | 0.2753 | 0.8387 | 0.0010 | 0.0005 | 0.0056 | 0.0048 |
| artist_exhibition_total_count_log | numeric | 40 | 0.0300 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1415 | 0.2753 | 0.8387 | 0.0010 | 0.0005 | 0.0056 | 0.0048 |
| artist_exhibition_total_count_log | numeric | 30 | 0.0500 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1415 | 0.2753 | 0.8387 | 0.0010 | 0.0005 | 0.0056 | 0.0048 |
| artist_exhibition_total_count_log | numeric | 40 | 0.0500 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1415 | 0.2753 | 0.8387 | 0.0010 | 0.0005 | 0.0056 | 0.0048 |
| artist_exhibition_total_count_log | numeric | 30 | 0.0800 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1415 | 0.2753 | 0.8387 | 0.0010 | 0.0005 | 0.0056 | 0.0048 |
| artist_exhibition_total_count_log | numeric | 20 | 0.0300 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1407 | 0.2755 | 0.8316 | 0.0002 | 0.0007 | -0.0014 | 0.0042 |
| artist_exhibition_total_count_log | numeric | 20 | 0.0500 | 0.1264 | 0.2117 | 0.6509 | -0.0041 | 0.0007 | -0.0071 | 0.1407 | 0.2758 | 0.8316 | 0.0002 | 0.0010 | -0.0014 | 0.0047 |
| artist_birth_generation_bin | categorical | 30 | 0.0300 | 0.1296 | 0.2099 | 0.6437 | -0.0009 | -0.0011 | -0.0143 | 0.1376 | 0.2752 | 0.8239 | -0.0029 | 0.0004 | -0.0092 | 0.0098 |

## 5. test 진단 상위 후보

| feature | kind | min_n | cap | validation_MdAPE | validation_MAPE | validation_p95_APE | validation_delta_MdAPE | validation_delta_MAPE | validation_delta_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | test_mean_abs_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_meta_birth_year | numeric | 20 | 0.0300 | 0.1263 | 0.2098 | 0.6456 | -0.0042 | -0.0013 | -0.0125 | 0.1370 | 0.2747 | 0.8240 | -0.0035 | -0.0001 | -0.0091 | 0.0116 |
| artist_meta_birth_year | numeric | 30 | 0.0300 | 0.1263 | 0.2098 | 0.6456 | -0.0042 | -0.0013 | -0.0125 | 0.1370 | 0.2747 | 0.8240 | -0.0035 | -0.0001 | -0.0091 | 0.0116 |
| artist_meta_birth_year | numeric | 40 | 0.0300 | 0.1263 | 0.2098 | 0.6456 | -0.0042 | -0.0013 | -0.0125 | 0.1370 | 0.2747 | 0.8240 | -0.0035 | -0.0001 | -0.0091 | 0.0116 |
| artist_birth_generation_bin | categorical | 10 | 0.0300 | 0.1272 | 0.2098 | 0.6440 | -0.0034 | -0.0012 | -0.0141 | 0.1376 | 0.2752 | 0.8239 | -0.0029 | 0.0004 | -0.0092 | 0.0107 |
| artist_birth_generation_bin | categorical | 20 | 0.0300 | 0.1294 | 0.2097 | 0.6440 | -0.0011 | -0.0013 | -0.0141 | 0.1376 | 0.2752 | 0.8239 | -0.0029 | 0.0004 | -0.0092 | 0.0107 |
| artist_birth_generation_bin | categorical | 30 | 0.0300 | 0.1296 | 0.2099 | 0.6437 | -0.0009 | -0.0011 | -0.0143 | 0.1376 | 0.2752 | 0.8239 | -0.0029 | 0.0004 | -0.0092 | 0.0098 |
| artist_meta_career_stage | numeric | 20 | 0.0300 | 0.1273 | 0.2115 | 0.6519 | -0.0032 | 0.0005 | -0.0061 | 0.1377 | 0.2740 | 0.8292 | -0.0028 | -0.0008 | -0.0039 | 0.0096 |
| artist_meta_career_stage | numeric | 30 | 0.0300 | 0.1273 | 0.2115 | 0.6519 | -0.0032 | 0.0005 | -0.0061 | 0.1377 | 0.2740 | 0.8292 | -0.0028 | -0.0008 | -0.0039 | 0.0096 |
| artist_meta_career_stage | numeric | 40 | 0.0300 | 0.1273 | 0.2115 | 0.6519 | -0.0032 | 0.0005 | -0.0061 | 0.1377 | 0.2740 | 0.8292 | -0.0028 | -0.0008 | -0.0039 | 0.0096 |
| artist_meta_career_stage | numeric | 20 | 0.0500 | 0.1273 | 0.2113 | 0.6519 | -0.0032 | 0.0003 | -0.0061 | 0.1384 | 0.2737 | 0.8292 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |
| artist_meta_career_stage | numeric | 30 | 0.0500 | 0.1273 | 0.2113 | 0.6519 | -0.0032 | 0.0003 | -0.0061 | 0.1384 | 0.2737 | 0.8292 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |
| artist_meta_career_stage | numeric | 40 | 0.0500 | 0.1273 | 0.2113 | 0.6519 | -0.0032 | 0.0003 | -0.0061 | 0.1384 | 0.2737 | 0.8292 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |
| artist_meta_career_stage | numeric | 30 | 0.0800 | 0.1273 | 0.2113 | 0.6519 | -0.0032 | 0.0003 | -0.0061 | 0.1384 | 0.2737 | 0.8292 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |
| artist_birth_generation_bin | categorical | 30 | 0.0500 | 0.1263 | 0.2102 | 0.6437 | -0.0042 | -0.0008 | -0.0143 | 0.1389 | 0.2757 | 0.8268 | -0.0016 | 0.0009 | -0.0063 | 0.0111 |
| artist_birth_generation_bin | categorical | 20 | 0.0500 | 0.1263 | 0.2098 | 0.6440 | -0.0042 | -0.0012 | -0.0141 | 0.1389 | 0.2759 | 0.8268 | -0.0016 | 0.0011 | -0.0063 | 0.0126 |
| artist_birth_generation_bin | categorical | 10 | 0.0500 | 0.1261 | 0.2100 | 0.6440 | -0.0044 | -0.0010 | -0.0141 | 0.1389 | 0.2759 | 0.8268 | -0.0016 | 0.0011 | -0.0063 | 0.0126 |
| artist_meta_birth_year | numeric | 20 | 0.0500 | 0.1261 | 0.2099 | 0.6456 | -0.0044 | -0.0012 | -0.0125 | 0.1382 | 0.2757 | 0.8361 | -0.0023 | 0.0009 | 0.0031 | 0.0148 |
| artist_meta_birth_year | numeric | 30 | 0.0500 | 0.1261 | 0.2099 | 0.6456 | -0.0044 | -0.0012 | -0.0125 | 0.1382 | 0.2757 | 0.8361 | -0.0023 | 0.0009 | 0.0031 | 0.0148 |
| artist_meta_birth_year | numeric | 40 | 0.0500 | 0.1261 | 0.2099 | 0.6456 | -0.0044 | -0.0012 | -0.0125 | 0.1382 | 0.2757 | 0.8361 | -0.0023 | 0.0009 | 0.0031 | 0.0148 |
| gallery_feature_source | categorical | 10 | 0.0300 | 0.1276 | 0.2118 | 0.6627 | -0.0029 | 0.0007 | 0.0047 | 0.1397 | 0.2754 | 0.8333 | -0.0007 | 0.0006 | 0.0002 | 0.0037 |

## 6. 커버리지

| feature | kind | validation_coverage | validation_non_null_n | validation_unique_n | test_coverage | test_non_null_n | test_unique_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artist_birth_generation_bin | categorical | 1.0000 | 519 | 8 | 1.0000 | 607 | 7 |
| artist_entity_suffix | categorical | 0.0289 | 15 | 2 | 0.0214 | 13 | 2 |
| artist_exhibition_available_count | categorical | 1.0000 | 519 | 4 | 1.0000 | 607 | 3 |
| artist_exhibition_fair_count | numeric | 0.4200 | 218 | 11 | 0.4547 | 276 | 12 |
| artist_exhibition_fair_count_log | numeric | 1.0000 | 519 | 11 | 1.0000 | 607 | 12 |
| artist_exhibition_fair_count_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_exhibition_group_count | categorical | 0.4027 | 209 | 8 | 0.4250 | 258 | 7 |
| artist_exhibition_group_count_log | categorical | 1.0000 | 519 | 8 | 1.0000 | 607 | 7 |
| artist_exhibition_group_count_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_exhibition_solo_count | numeric | 0.3854 | 200 | 13 | 0.4448 | 270 | 12 |
| artist_exhibition_solo_count_log | numeric | 1.0000 | 519 | 13 | 1.0000 | 607 | 12 |
| artist_exhibition_solo_count_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_exhibition_total_count | numeric | 0.4200 | 218 | 19 | 0.4547 | 276 | 20 |
| artist_exhibition_total_count_log | numeric | 1.0000 | 519 | 19 | 1.0000 | 607 | 20 |
| artist_key | categorical | 1.0000 | 519 | 178 | 1.0000 | 607 | 207 |
| artist_meta_birth_year | numeric | 0.4682 | 243 | 41 | 0.3509 | 213 | 39 |
| artist_meta_birth_year_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_meta_career_age_log1p | categorical | 1.0000 | 519 | 1 | 1.0000 | 607 | 1 |
| artist_meta_career_age_missing | categorical | 1.0000 | 519 | 1 | 1.0000 | 607 | 1 |
| artist_meta_career_stage | numeric | 0.4200 | 218 | 63 | 0.4547 | 276 | 76 |
| artist_meta_followers | numeric | 0.8651 | 449 | 48 | 0.8699 | 528 | 59 |
| artist_meta_followers_log1p | numeric | 1.0000 | 519 | 48 | 1.0000 | 607 | 59 |
| artist_meta_followers_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_meta_for_sale_ratio | categorical | 0.4200 | 218 | 1 | 0.4547 | 276 | 1 |
| artist_meta_for_sale_ratio_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_meta_for_sale_works | numeric | 0.4451 | 231 | 41 | 0.4152 | 252 | 39 |
| artist_meta_for_sale_works_log1p | numeric | 1.0000 | 519 | 42 | 1.0000 | 607 | 40 |
| artist_meta_for_sale_works_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_meta_has_international | categorical | 0.4200 | 218 | 1 | 0.4547 | 276 | 1 |
| artist_meta_is_p1 | categorical | 0.8651 | 449 | 2 | 0.8699 | 528 | 2 |
| artist_meta_market_depth_gap | numeric | 0.4451 | 231 | 24 | 0.4152 | 252 | 25 |
| artist_meta_market_depth_gap_log1p | numeric | 1.0000 | 519 | 24 | 1.0000 | 607 | 25 |
| artist_meta_nationality | categorical | 0.5472 | 284 | 9 | 0.5354 | 325 | 11 |
| artist_meta_nationality_ko | categorical | 0.0790 | 41 | 6 | 0.0857 | 52 | 3 |
| artist_meta_source | categorical | 1.0000 | 519 | 4 | 1.0000 | 607 | 4 |
| artist_meta_total_works | numeric | 0.8651 | 449 | 75 | 0.8699 | 528 | 79 |
| artist_meta_total_works_log1p | numeric | 1.0000 | 519 | 75 | 1.0000 | 607 | 79 |
| artist_meta_total_works_missing | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| artist_name_ko | categorical | 1.0000 | 519 | 178 | 1.0000 | 607 | 205 |
| artist_name_ko_orig | categorical | 1.0000 | 519 | 177 | 1.0000 | 607 | 205 |
| artist_name_standardized | categorical | 1.0000 | 519 | 185 | 1.0000 | 607 | 210 |
| artist_works_count_train | numeric | 1.0000 | 519 | 46 | 1.0000 | 607 | 55 |
| artist_works_count_train_log1p | numeric | 1.0000 | 519 | 46 | 1.0000 | 607 | 55 |
| artist_works_count_train_missing | categorical | 1.0000 | 519 | 1 | 1.0000 | 607 | 1 |
| artist_works_log | numeric | 1.0000 | 519 | 46 | 1.0000 | 607 | 55 |
| artist_works_log_log1p | numeric | 1.0000 | 519 | 46 | 1.0000 | 607 | 55 |
| artist_works_log_missing | categorical | 1.0000 | 519 | 1 | 1.0000 | 607 | 1 |
| gallery_audit_status | categorical | 1.0000 | 519 | 3 | 1.0000 | 607 | 2 |
| gallery_city_count | categorical | 0.4200 | 218 | 1 | 0.4547 | 276 | 1 |
| gallery_city_count_log | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| gallery_feature_source | categorical | 1.0000 | 519 | 3 | 1.0000 | 607 | 2 |
| gallery_ref_type | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 1 |
| gallery_tier_any_available_flag | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| gallery_tier_raw_available_flag | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| gallery_tier_raw_bucket | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 2 |
| gallery_tier_raw_numeric | categorical | 0.4200 | 218 | 1 | 0.4547 | 276 | 1 |
| gallery_tier_validated | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 1 |
| gallery_tier_validated_available_flag | categorical | 1.0000 | 519 | 2 | 1.0000 | 607 | 1 |
| gallery_tier_validated_score | categorical | 0.0058 | 3 | 1 | 0.0000 | 0 | 0 |

## 7. 산출물

- `outputs/single_feature_candidate_metrics.csv`
- `outputs/single_feature_best_by_feature.csv`
- `outputs/validation_top_candidates.csv`
- `outputs/test_top_candidates_diagnostic.csv`
- `outputs/feature_coverage.csv`
- `outputs/correction_maps.csv`
- `outputs/top_feature_test_predictions.csv`
- `outputs/experiment_manifest.json`