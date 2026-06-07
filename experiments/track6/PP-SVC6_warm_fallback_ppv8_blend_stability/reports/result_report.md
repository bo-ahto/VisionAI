# PP-SVC6 Warm fallback 비교군 + PP-V8 결합 비율 안정성 검증

- 작성일: 2026-06-04 00:59
- 목적: `fallback_numeric + PP-V8` 결합 비율을 반복 holdout으로 재검증
- 입력: PP-SVC5 validation/test 예측값
- 선택 데이터: validation selection subset
- 확인 데이터: validation holdout subset과 test
- 반복 횟수: row/artist holdout 각 `200`회
- weight 후보: `0.400`부터 `0.900`까지 `0.025` 간격

## 1. 고정 후보 test 성능

| 후보 | weight | MdAPE | MAPE | p95_APE | PP-SVC3 대비 MdAPE 변화 | PP-SVC3 대비 MAPE 변화 |
|---|---:|---:|---:|---:|---:|---:|
| `blend_fallback_numeric_ppv8_wfallback_0.575` | 0.575 | 0.1348 | 0.2711 | 0.8362 | 0.0057 | 0.0037 |
| `blend_fallback_numeric_ppv8_wfallback_0.600` | 0.600 | 0.1362 | 0.2717 | 0.8329 | 0.0043 | 0.0031 |
| `blend_fallback_numeric_ppv8_wfallback_0.625` | 0.625 | 0.1374 | 0.2725 | 0.8378 | 0.0031 | 0.0023 |
| `blend_fallback_numeric_ppv8_wfallback_0.550` | 0.550 | 0.1376 | 0.2706 | 0.8414 | 0.0028 | 0.0042 |
| `blend_fallback_numeric_ppv8_wfallback_0.650` | 0.650 | 0.1382 | 0.2733 | 0.8432 | 0.0023 | 0.0015 |
| `blend_fallback_numeric_ppv8_wfallback_0.700` | 0.700 | 0.1401 | 0.2751 | 0.8351 | 0.0004 | -0.0003 |
| `blend_fallback_numeric_ppv8_wfallback_0.500` | 0.500 | 0.1402 | 0.2699 | 0.8472 | 0.0003 | 0.0049 |
| `blend_svcnum_ppv8_wsvc_0.70` |  | 0.1405 | 0.2748 | 0.8331 | 0.0000 | 0.0000 |
| `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 0.1430 | 0.2774 | 0.8669 | -0.0025 | -0.0026 |
| `fallback_numeric` |  | 0.1528 | 0.2956 | 0.9694 | -0.0123 | -0.0208 |
| `pp_v8_compact_blend_mape_guarded` |  | 0.1632 | 0.2816 | 0.9311 | -0.0227 | -0.0068 |

## 2. 반복 선택 빈도

| holdout 방식 | 선택 기준 | 후보 | weight | 선택 횟수 | 선택 비율 |
|---|---|---|---:|---:|---:|
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.850` | 0.850 | 63 | 0.315 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.875` | 0.875 | 52 | 0.260 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.900` | 0.900 | 47 | 0.235 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 11 | 0.055 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.775` | 0.775 | 9 | 0.045 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 7 | 0.035 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.825` | 0.825 | 6 | 0.030 |
| artist_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 2 | 0.010 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 49 | 0.245 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 46 | 0.230 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.700` | 0.700 | 38 | 0.190 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.775` | 0.775 | 28 | 0.140 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.675` | 0.675 | 26 | 0.130 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.650` | 0.650 | 9 | 0.045 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 3 | 0.015 |
| artist_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.600` | 0.600 | 1 | 0.005 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 49 | 0.245 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 49 | 0.245 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.700` | 0.700 | 46 | 0.230 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.775` | 0.775 | 29 | 0.145 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.675` | 0.675 | 12 | 0.060 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 6 | 0.030 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.650` | 0.650 | 5 | 0.025 |
| artist_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.825` | 0.825 | 2 | 0.010 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.900` | 0.900 | 85 | 0.425 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.875` | 0.875 | 62 | 0.310 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.850` | 0.850 | 44 | 0.220 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.475` | 0.475 | 2 | 0.010 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 2 | 0.010 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.500` | 0.500 | 1 | 0.005 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 1 | 0.005 |
| artist_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 1 | 0.005 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.850` | 0.850 | 59 | 0.295 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.875` | 0.875 | 53 | 0.265 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.900` | 0.900 | 46 | 0.230 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 12 | 0.060 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.825` | 0.825 | 12 | 0.060 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.775` | 0.775 | 9 | 0.045 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 4 | 0.020 |
| row_holdout | balanced_reference | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 2 | 0.010 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 52 | 0.260 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 40 | 0.200 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.700` | 0.700 | 39 | 0.195 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.675` | 0.675 | 34 | 0.170 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.775` | 0.775 | 24 | 0.120 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.650` | 0.650 | 6 | 0.030 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 3 | 0.015 |
| row_holdout | mape_guarded_ppv8 | `blend_fallback_numeric_ppv8_wfallback_0.600` | 0.600 | 1 | 0.005 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.725` | 0.725 | 54 | 0.270 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.700` | 0.700 | 48 | 0.240 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.750` | 0.750 | 42 | 0.210 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.775` | 0.775 | 26 | 0.130 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.675` | 0.675 | 20 | 0.100 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 5 | 0.025 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.650` | 0.650 | 3 | 0.015 |
| row_holdout | mape_guarded_reference | `blend_fallback_numeric_ppv8_wfallback_0.525` | 0.525 | 1 | 0.005 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.900` | 0.900 | 88 | 0.440 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.875` | 0.875 | 60 | 0.300 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.850` | 0.850 | 41 | 0.205 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.800` | 0.800 | 6 | 0.030 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.825` | 0.825 | 3 | 0.015 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.450` | 0.450 | 1 | 0.005 |
| row_holdout | mdape_primary | `blend_fallback_numeric_ppv8_wfallback_0.500` | 0.500 | 1 | 0.005 |

## 3. 내부 holdout 요약

| holdout 방식 | 선택 기준 | weight 중앙값 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-SVC3 MAPE 개선확률 | PP-SVC3 p95 개선확률 |
|---|---|---:|---:|---:|---:|---:|---:|
| artist_holdout | balanced_reference | 0.850 | 0.1237 | 0.2123 | 0.6431 | 0.315 | 0.675 |
| artist_holdout | mape_guarded_ppv8 | 0.725 | 0.1281 | 0.2109 | 0.6427 | 0.465 | 0.760 |
| artist_holdout | mape_guarded_reference | 0.725 | 0.1277 | 0.2107 | 0.6418 | 0.480 | 0.770 |
| artist_holdout | mdape_primary | 0.875 | 0.1231 | 0.2126 | 0.6431 | 0.295 | 0.665 |
| row_holdout | balanced_reference | 0.850 | 0.1241 | 0.2153 | 0.6417 | 0.300 | 0.695 |
| row_holdout | mape_guarded_ppv8 | 0.725 | 0.1289 | 0.2140 | 0.6392 | 0.415 | 0.805 |
| row_holdout | mape_guarded_reference | 0.725 | 0.1288 | 0.2139 | 0.6391 | 0.470 | 0.805 |
| row_holdout | mdape_primary | 0.875 | 0.1233 | 0.2156 | 0.6417 | 0.275 | 0.680 |

## 4. 선택 후 test 요약

| holdout 방식 | 선택 기준 | weight 중앙값 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-SVC3 MdAPE 개선확률 | PP-SVC3 MAPE 개선확률 | PP-SVC3 p95 개선확률 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| artist_holdout | balanced_reference | 0.850 | 0.1441 | 0.2839 | 0.9243 | 0.010 | 0.015 | 0.000 |
| artist_holdout | mape_guarded_ppv8 | 0.725 | 0.1419 | 0.2763 | 0.8543 | 0.370 | 0.180 | 0.005 |
| artist_holdout | mape_guarded_reference | 0.725 | 0.1421 | 0.2766 | 0.8572 | 0.320 | 0.090 | 0.000 |
| artist_holdout | mdape_primary | 0.875 | 0.1448 | 0.2853 | 0.9323 | 0.005 | 0.015 | 0.000 |
| row_holdout | balanced_reference | 0.850 | 0.1442 | 0.2840 | 0.9248 | 0.010 | 0.015 | 0.005 |
| row_holdout | mape_guarded_ppv8 | 0.725 | 0.1418 | 0.2761 | 0.8524 | 0.405 | 0.210 | 0.005 |
| row_holdout | mape_guarded_reference | 0.725 | 0.1420 | 0.2763 | 0.8540 | 0.365 | 0.125 | 0.000 |
| row_holdout | mdape_primary | 0.875 | 0.1449 | 0.2854 | 0.9333 | 0.005 | 0.010 | 0.005 |

## 5. 해석

- test 고정 후보만 보면 `w=0.55~0.60` 구간이 기존 PP-SVC3보다 MdAPE/MAPE를 소폭 개선
- 반복 holdout에서 같은 구간이 안정적으로 선택되면 Warm 서비스 후보 갱신 가능
- 반복 holdout에서 `w=0.70~0.75`가 더 자주 선택되면 기존 PP-SVC3 계열 유지가 타당
- row holdout과 artist holdout 선택 weight가 다르면 작가 단위 일반화 관점에서 보수적으로 판단

## 6. 실행 결론

- 고정 test 기준 최상위 후보: `blend_fallback_numeric_ppv8_wfallback_0.575`
- 해당 후보 test MdAPE `0.1348`, MAPE `0.2711`, p95_APE `0.8362`
- 기존 PP-SVC3 대비 MdAPE `+0.0057`, MAPE `+0.0037` 개선
- 단, p95_APE는 기존 PP-SVC3보다 `0.0031` 악화
- `w=0.600`은 test MdAPE `0.1362`, MAPE `0.2717`, p95_APE `0.8329`
- `w=0.600`은 기존 PP-SVC3 대비 MdAPE/MAPE/p95를 모두 소폭 개선
- 하지만 반복 holdout 선택 중심은 `0.55~0.60`이 아님
- MAPE 방어 기준의 반복 선택 중앙값은 row/artist 모두 `0.725`
- balanced 또는 MdAPE 기준은 `0.850~0.875` 쪽으로 치우침
- 선택 후 test 평균은 기존 PP-SVC3 대비 안정 개선으로 보기 어려움
- `mape_guarded_ppv8` 기준 test 평균: MdAPE `0.1418~0.1419`, MAPE `0.2761~0.2763`, p95 `0.8524~0.8543`
- 기존 PP-SVC3 test: MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`
- 결론: `0.575~0.600`은 test 관찰값으로는 매력적이나 validation 반복 선택 안정성이 부족
- Warm 서비스 1순위 후보는 기존 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` 유지
- 후속으로 진행한다면 `0.575~0.600` 고정 후보를 별도 split 또는 artist holdout 재현 실험에서만 재검토
