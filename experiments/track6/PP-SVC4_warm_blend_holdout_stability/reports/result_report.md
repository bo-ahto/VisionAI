# PP-SVC4 Warm 결합 후보 holdout 안정성 검증

- 작성일: 2026-06-03 21:44
- 목적: `PP-SVC3`에서 선택된 Warm 결합 후보가 validation 분할 방식이 바뀌어도 안정적인지 확인한다.
- 선택 원칙: 각 반복에서 selection subset만 보고 후보를 고른다. holdout과 test는 후보 선택 후 확인용으로만 사용한다.
- 반복 횟수: holdout 방식별 `200`회.

## 1. 고정 PP-SVC3 후보 성능

| 후보 | split | MdAPE | MAPE | p95_APE | PP-V6 대비 MdAPE 개선 | PP-V6 대비 MAPE 개선 |
|---|---|---:|---:|---:|---:|---:|
| `blend_svcnum_ppv8_wsvc_0.70` | validation | 0.1305 | 0.2110 | 0.6580 | 0.0225 | 0.0456 |
| `blend_svcnum_ppv8_wsvc_0.70` | test | 0.1405 | 0.2748 | 0.8331 | 0.0208 | 0.0141 |

## 2. 반복 분할 선택 빈도

| holdout 방식 | 선택 목적 | 선택 후보 | 계열 | svc 가중치 | 선택 횟수 | 선택 비율 |
|---|---|---|---|---:|---:|---:|
| artist_holdout | balanced | `blend_svcnum_ppv8_wsvc_0.85` | blend_svcnum_ppv8 | 0.85 | 56 | 0.280 |
| artist_holdout | balanced | `blend_svcnum_ppv8_wsvc_0.80` | blend_svcnum_ppv8 | 0.80 | 44 | 0.220 |
| artist_holdout | balanced | `blend_svcnum_ppv8_wsvc_0.75` | blend_svcnum_ppv8 | 0.75 | 32 | 0.160 |
| artist_holdout | balanced | `blend_svcfull_ppv8_wsvc_0.80` | blend_svcfull_ppv8 | 0.80 | 12 | 0.060 |
| artist_holdout | balanced | `blend_svcnum_ppv6_wsvc_0.80` | blend_svcnum_ppv6 | 0.80 | 8 | 0.040 |
| artist_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.70` | blend_svcnum_ppv8 | 0.70 | 91 | 0.455 |
| artist_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.75` | blend_svcnum_ppv8 | 0.75 | 44 | 0.220 |
| artist_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.65` | blend_svcnum_ppv8 | 0.65 | 37 | 0.185 |
| artist_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.80` | blend_svcnum_ppv8 | 0.80 | 17 | 0.085 |
| artist_holdout | mape_guarded | `blend_svcfull_ppv8_wsvc_0.75` | blend_svcfull_ppv8 | 0.75 | 6 | 0.030 |
| artist_holdout | mdape_primary | `blend_svcnum_ppv8_wsvc_0.85` | blend_svcnum_ppv8 | 0.85 | 37 | 0.185 |
| artist_holdout | mdape_primary | `blend_svcfull_ppv8_wsvc_0.90` | blend_svcfull_ppv8 | 0.90 | 25 | 0.125 |
| artist_holdout | mdape_primary | `blend_svcnum_ppv6_wsvc_0.75` | blend_svcnum_ppv6 | 0.75 | 25 | 0.125 |
| artist_holdout | mdape_primary | `blend_svcnum_ppv6_wsvc_0.80` | blend_svcnum_ppv6 | 0.80 | 23 | 0.115 |
| artist_holdout | mdape_primary | `blend_svcnum_ppv8_wsvc_0.80` | blend_svcnum_ppv8 | 0.80 | 12 | 0.060 |
| row_holdout | balanced | `blend_svcnum_ppv8_wsvc_0.80` | blend_svcnum_ppv8 | 0.80 | 67 | 0.335 |
| row_holdout | balanced | `blend_svcnum_ppv8_wsvc_0.85` | blend_svcnum_ppv8 | 0.85 | 44 | 0.220 |
| row_holdout | balanced | `blend_svcfull_ppv8_wsvc_0.80` | blend_svcfull_ppv8 | 0.80 | 23 | 0.115 |
| row_holdout | balanced | `blend_svcnum_ppv8_wsvc_0.75` | blend_svcnum_ppv8 | 0.75 | 20 | 0.100 |
| row_holdout | balanced | `blend_svcnum_ppv6_wsvc_0.75` | blend_svcnum_ppv6 | 0.75 | 9 | 0.045 |
| row_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.70` | blend_svcnum_ppv8 | 0.70 | 109 | 0.545 |
| row_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.75` | blend_svcnum_ppv8 | 0.75 | 43 | 0.215 |
| row_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.65` | blend_svcnum_ppv8 | 0.65 | 20 | 0.100 |
| row_holdout | mape_guarded | `blend_svcnum_ppv8_wsvc_0.80` | blend_svcnum_ppv8 | 0.80 | 13 | 0.065 |
| row_holdout | mape_guarded | `blend_svcfull_ppv8_wsvc_0.75` | blend_svcfull_ppv8 | 0.75 | 10 | 0.050 |
| row_holdout | mdape_primary | `blend_svcnum_ppv8_wsvc_0.85` | blend_svcnum_ppv8 | 0.85 | 41 | 0.205 |
| row_holdout | mdape_primary | `blend_svcnum_ppv6_wsvc_0.75` | blend_svcnum_ppv6 | 0.75 | 30 | 0.150 |
| row_holdout | mdape_primary | `blend_svcfull_ppv8_wsvc_0.80` | blend_svcfull_ppv8 | 0.80 | 20 | 0.100 |
| row_holdout | mdape_primary | `blend_svcnum_ppv8_wsvc_0.80` | blend_svcnum_ppv8 | 0.80 | 19 | 0.095 |
| row_holdout | mdape_primary | `blend_svcnum_ppv6_wsvc_0.80` | blend_svcnum_ppv6 | 0.80 | 18 | 0.090 |

## 3. 내부 holdout 요약

| holdout 방식 | 선택 목적 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-V6 MdAPE 개선확률 | PP-V6 MAPE 개선확률 |
|---|---|---:|---:|---:|---:|---:|
| artist_holdout | balanced | 0.1279 | 0.2152 | 0.6737 | 0.950 | 0.995 |
| artist_holdout | mape_guarded | 0.1327 | 0.2141 | 0.6728 | 0.955 | 0.995 |
| artist_holdout | mdape_primary | 0.1304 | 0.2166 | 0.6775 | 0.940 | 0.995 |
| row_holdout | balanced | 0.1255 | 0.2127 | 0.6494 | 0.975 | 0.995 |
| row_holdout | mape_guarded | 0.1293 | 0.2116 | 0.6485 | 0.980 | 1.000 |
| row_holdout | mdape_primary | 0.1271 | 0.2138 | 0.6523 | 0.970 | 0.990 |

## 4. 선택 후 test 요약

| holdout 방식 | 선택 목적 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-V6 MdAPE 개선확률 | PP-V6 MAPE 개선확률 | PP-V8 MAPE 개선확률 |
|---|---|---:|---:|---:|---:|---:|---:|
| artist_holdout | balanced | 0.1463 | 0.2817 | 0.8625 | 1.000 | 0.955 | 0.485 |
| artist_holdout | mape_guarded | 0.1414 | 0.2755 | 0.8326 | 1.000 | 1.000 | 1.000 |
| artist_holdout | mdape_primary | 0.1481 | 0.2842 | 0.8737 | 1.000 | 0.850 | 0.200 |
| row_holdout | balanced | 0.1464 | 0.2815 | 0.8581 | 1.000 | 0.955 | 0.580 |
| row_holdout | mape_guarded | 0.1416 | 0.2756 | 0.8325 | 1.000 | 1.000 | 1.000 |
| row_holdout | mdape_primary | 0.1477 | 0.2838 | 0.8693 | 1.000 | 0.885 | 0.260 |

## 5. 해석

- `mape_guarded` 목적에서는 `blend_svcnum_ppv8` 계열이 반복적으로 선택됐다.
- row holdout 기준 `blend_svcnum_ppv8` 선택 비율은 0.930, artist holdout 기준 선택 비율은 0.950이다.
- 특히 `wsvc=0.70`은 row holdout `mape_guarded`에서 200회 중 109회, artist holdout `mape_guarded`에서 200회 중 91회 선택됐다.
- 따라서 PP-SVC3의 `svc_numeric 70% + PP-V8 30%` 결합은 validation 하나에만 맞춘 우연 후보라기보다, MAPE를 방어하면서 MdAPE를 낮추는 안정 후보로 해석할 수 있다.
- 반대로 `mdape_primary`나 `balanced`에서는 0.75~0.85처럼 svc 쪽 가중치가 더 높은 후보도 자주 선택됐다. 이 경우 MdAPE는 좋아질 수 있지만 PP-V8 대비 MAPE 방어가 약해질 수 있어, 서비스 1순위는 `mape_guarded` 기준을 우선한다.
