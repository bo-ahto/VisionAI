# PP-AMW2 Warm 작가 메타 + 검색 피처 잔차 결합 보정 결과

## 1. 실행 요약

- 기준 후보: PP-V8 compact_blend_mape_guarded
- 결합 방식: PP-AMW1 작가 메타 보정값 + PP-H29 검색 피처 보정값을 가중 결합
- 보정값 생성: 두 보정 모두 validation 잔차에서 생성된 기존 후보만 사용
- 가중치 선택: validation 성능 기준으로 후보를 고르고 test에는 같은 설정을 적용
- 운영 코드 변경: 없음

핵심 결과:
- 기준 test MdAPE 0.1632, MAPE 0.2816, p95_APE 0.9311
- validation 1순위 후보: stack_amw01_h2901_wa1_wh1_cap0p05 / validation MdAPE 0.1533, MAPE 0.2500, p95_APE 0.7458
- validation 선택 후보 중 test 최선: stack_amw01_h2901_wa1_wh1_cap0p05 / test MdAPE 0.1647, MAPE 0.2797, p95_APE 0.9261
- 보수 선택 후보 중 test 최선: stack_amw11_h2913_wa0.5_wh0.5_cap0p03 / test MdAPE 0.1624, MAPE 0.2805, p95_APE 0.9299
- 전체 grid 중 test MAPE 최선: stack_amw01_h2913_wa1_wh1_cap0p05 / test MdAPE 0.1635, MAPE 0.2791, p95_APE 0.9269
- test에서 MdAPE/MAPE/p95가 모두 개선된 후보 중 MAPE 최선: stack_amw05_h2913_wa1_wh1_cap0p05 / test MdAPE 0.1610, MAPE 0.2792, p95_APE 0.9264

판단 기준:
- validation 선택 후보가 test에서도 기준 대비 MdAPE/MAPE/p95를 함께 낮추면 후속 반복 검증 대상으로 둔다.
- 보수 선택 후보는 validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보를 우선한다.
- test에서만 좋아지는 후보는 탐색 결과로만 보고 바로 채택하지 않는다.

## 2. 사용한 입력 후보

- 작가 메타 보정 후보 수: 20
- 검색 피처 보정 후보 수: 24
- 결합 후보 수: 11520

## 3. validation 상위 후보

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw04_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw04_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw04_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |

## 4. validation 선택 후보의 validation/test 지표

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW2 | baseline_ppv8_compact_blend_mape_guarded | warm | test | baseline | 607 | 0.402820 | 0.163169 | 0.281619 | 0.931104 | 0.736409 | 0.859967 | 6 | 7 | 0.996625 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PP-AMW2 | baseline_ppv8_compact_blend_mape_guarded | warm | validation | baseline | 519 | 0.372063 | 0.154389 | 0.254387 | 0.808363 | 0.722543 | 0.888247 | 4 | 4 | 1.005064 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw01_h2901_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw01_h2902_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw01_h2903_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw02_h2901_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw02_h2902_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw02_h2903_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw03_h2901_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw03_h2902_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.404486 | 0.164669 | 0.279761 | 0.927172 | 0.738056 | 0.859967 | 6 | 7 | 0.984421 | 0.001500 | -0.001858 | -0.003933 | 0.001666 |
| PP-AMW2 | stack_amw03_h2903_wa1_wh1_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370943 | 0.153285 | 0.250043 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995198 | -0.001104 | -0.004344 | -0.062542 | -0.001121 |
| PP-AMW2 | stack_amw04_h2901_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw04_h2901_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw04_h2902_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw04_h2902_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |
| PP-AMW2 | stack_amw04_h2903_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.985425 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW2 | stack_amw04_h2903_wa1_wh1_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | 0.995623 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |

## 5. 보수 선택 후보의 validation/test 지표

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW2 | baseline_ppv8_compact_blend_mape_guarded | warm | test | baseline | 607 | 0.402820 | 0.163169 | 0.281619 | 0.931104 | 0.736409 | 0.859967 | 6 | 7 | 0.996625 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PP-AMW2 | baseline_ppv8_compact_blend_mape_guarded | warm | validation | baseline | 519 | 0.372063 | 0.154389 | 0.254387 | 0.808363 | 0.722543 | 0.888247 | 4 | 4 | 1.005064 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2913_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2914_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2915_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2916_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2917_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2918_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p08 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2919_wa0.5_wh0.5_cap0p1 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2920_wa0.5_wh0.5_cap0p03 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2920_wa0.5_wh0.5_cap0p03 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW2 | stack_amw11_h2920_wa0.5_wh0.5_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | 0.992337 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW2 | stack_amw11_h2920_wa0.5_wh0.5_cap0p05 | warm | validation | artist_meta_search_residual_stack | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | 1.001239 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |

## 6. test 기준 상위 후보

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW2 | stack_amw01_h2913_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2913_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2913_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2914_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2914_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2914_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2915_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2915_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2915_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2916_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2916_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2916_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2917_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2917_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2917_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2918_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2918_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2918_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2919_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2919_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2919_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2920_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2920_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2920_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2921_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2921_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2921_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2922_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2922_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW2 | stack_amw01_h2922_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.985814 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |

## 7. test에서 세 지표가 모두 개선된 후보

| experiment_id | candidate | scope | split | policy | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | median_ratio | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW2 | stack_amw05_h2913_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2913_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2913_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2914_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2914_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2914_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2915_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2915_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2915_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2916_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2916_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2916_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2917_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2917_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2917_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2918_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2918_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2918_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2919_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2919_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2919_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2920_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2920_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2920_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2921_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2921_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2921_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2922_wa1_wh1_cap0p05 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2922_wa1_wh1_cap0p08 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW2 | stack_amw05_h2922_wa1_wh1_cap0p1 | warm | test | artist_meta_search_residual_stack | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | 0.986963 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |

## 8. 후보 매핑 샘플

| candidate | artist_meta_candidate | search_candidate | artist_meta_weight | search_weight | total_correction_cap | mean_abs_artist_meta_correction | mean_abs_search_correction | mean_abs_combined_correction | max_abs_combined_correction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stack_amw01_h2901_wa1_wh1_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 1.000000 | 0.030000 | 0.007424 | 0.016481 | 0.016571 | 0.030000 |
| stack_amw01_h2901_wa1_wh1_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 1.000000 | 0.050000 | 0.007424 | 0.016481 | 0.019167 | 0.050000 |
| stack_amw01_h2901_wa1_wh1_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 1.000000 | 0.080000 | 0.007424 | 0.016481 | 0.019334 | 0.072409 |
| stack_amw01_h2901_wa1_wh1_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 1.000000 | 0.100000 | 0.007424 | 0.016481 | 0.019334 | 0.072409 |
| stack_amw01_h2901_wa1_wh0.75_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.750000 | 0.030000 | 0.007424 | 0.016481 | 0.014666 | 0.030000 |
| stack_amw01_h2901_wa1_wh0.75_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.750000 | 0.050000 | 0.007424 | 0.016481 | 0.015403 | 0.050000 |
| stack_amw01_h2901_wa1_wh0.75_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.750000 | 0.080000 | 0.007424 | 0.016481 | 0.015506 | 0.064480 |
| stack_amw01_h2901_wa1_wh0.75_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.750000 | 0.100000 | 0.007424 | 0.016481 | 0.015506 | 0.064480 |
| stack_amw01_h2901_wa1_wh0.5_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.500000 | 0.030000 | 0.007424 | 0.016481 | 0.010996 | 0.030000 |
| stack_amw01_h2901_wa1_wh0.5_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.500000 | 0.050000 | 0.007424 | 0.016481 | 0.011631 | 0.050000 |
| stack_amw01_h2901_wa1_wh0.5_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.500000 | 0.080000 | 0.007424 | 0.016481 | 0.011678 | 0.056550 |
| stack_amw01_h2901_wa1_wh0.5_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 1.000000 | 0.500000 | 0.100000 | 0.007424 | 0.016481 | 0.011678 | 0.056550 |
| stack_amw01_h2901_wa0.75_wh1_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.750000 | 1.000000 | 0.030000 | 0.007424 | 0.016481 | 0.016242 | 0.030000 |
| stack_amw01_h2901_wa0.75_wh1_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.750000 | 1.000000 | 0.050000 | 0.007424 | 0.016481 | 0.018242 | 0.050000 |
| stack_amw01_h2901_wa0.75_wh1_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.750000 | 1.000000 | 0.080000 | 0.007424 | 0.016481 | 0.018329 | 0.062236 |
| stack_amw01_h2901_wa0.75_wh1_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.750000 | 1.000000 | 0.100000 | 0.007424 | 0.016481 | 0.018329 | 0.062236 |
| stack_amw01_h2901_wa0.5_wh1_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 1.000000 | 0.030000 | 0.007424 | 0.016481 | 0.016004 | 0.030000 |
| stack_amw01_h2901_wa0.5_wh1_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 1.000000 | 0.050000 | 0.007424 | 0.016481 | 0.017425 | 0.050000 |
| stack_amw01_h2901_wa0.5_wh1_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 1.000000 | 0.080000 | 0.007424 | 0.016481 | 0.017440 | 0.052063 |
| stack_amw01_h2901_wa0.5_wh1_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 1.000000 | 0.100000 | 0.007424 | 0.016481 | 0.017440 | 0.052063 |
| stack_amw01_h2901_wa0.5_wh0.5_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 0.500000 | 0.030000 | 0.007424 | 0.016481 | 0.009623 | 0.030000 |
| stack_amw01_h2901_wa0.5_wh0.5_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 0.500000 | 0.050000 | 0.007424 | 0.016481 | 0.009667 | 0.036204 |
| stack_amw01_h2901_wa0.5_wh0.5_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 0.500000 | 0.080000 | 0.007424 | 0.016481 | 0.009667 | 0.036204 |
| stack_amw01_h2901_wa0.5_wh0.5_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p05 | 0.500000 | 0.500000 | 0.100000 | 0.007424 | 0.016481 | 0.009667 | 0.036204 |
| stack_amw01_h2902_wa1_wh1_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 1.000000 | 0.030000 | 0.007424 | 0.016481 | 0.016571 | 0.030000 |
| stack_amw01_h2902_wa1_wh1_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 1.000000 | 0.050000 | 0.007424 | 0.016481 | 0.019167 | 0.050000 |
| stack_amw01_h2902_wa1_wh1_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 1.000000 | 0.080000 | 0.007424 | 0.016481 | 0.019334 | 0.072409 |
| stack_amw01_h2902_wa1_wh1_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 1.000000 | 0.100000 | 0.007424 | 0.016481 | 0.019334 | 0.072409 |
| stack_amw01_h2902_wa1_wh0.75_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.750000 | 0.030000 | 0.007424 | 0.016481 | 0.014666 | 0.030000 |
| stack_amw01_h2902_wa1_wh0.75_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.750000 | 0.050000 | 0.007424 | 0.016481 | 0.015403 | 0.050000 |
| stack_amw01_h2902_wa1_wh0.75_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.750000 | 0.080000 | 0.007424 | 0.016481 | 0.015506 | 0.064480 |
| stack_amw01_h2902_wa1_wh0.75_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.750000 | 0.100000 | 0.007424 | 0.016481 | 0.015506 | 0.064480 |
| stack_amw01_h2902_wa1_wh0.5_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.500000 | 0.030000 | 0.007424 | 0.016481 | 0.010996 | 0.030000 |
| stack_amw01_h2902_wa1_wh0.5_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.500000 | 0.050000 | 0.007424 | 0.016481 | 0.011631 | 0.050000 |
| stack_amw01_h2902_wa1_wh0.5_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.500000 | 0.080000 | 0.007424 | 0.016481 | 0.011678 | 0.056550 |
| stack_amw01_h2902_wa1_wh0.5_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 1.000000 | 0.500000 | 0.100000 | 0.007424 | 0.016481 | 0.011678 | 0.056550 |
| stack_amw01_h2902_wa0.75_wh1_cap0p03 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 0.750000 | 1.000000 | 0.030000 | 0.007424 | 0.016481 | 0.016242 | 0.030000 |
| stack_amw01_h2902_wa0.75_wh1_cap0p05 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 0.750000 | 1.000000 | 0.050000 | 0.007424 | 0.016481 | 0.018242 | 0.050000 |
| stack_amw01_h2902_wa0.75_wh1_cap0p08 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 0.750000 | 1.000000 | 0.080000 | 0.007424 | 0.016481 | 0.018329 | 0.062236 |
| stack_amw01_h2902_wa0.75_wh1_cap0p1 | seg_for_sale_bin_min30_cap0p05_k20 | h29_v8_compact_mape_news_median_cap0p1 | 0.750000 | 1.000000 | 0.100000 | 0.007424 | 0.016481 | 0.018329 | 0.062236 |

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_map.csv`
- `outputs/selected_candidate_metrics.csv`
- `outputs/conservative_balanced_candidate_metrics.csv`
- `outputs/validation_top_candidates.csv`
- `outputs/test_top_candidates.csv`
- `outputs/test_all_metric_improved_candidates.csv`
- `outputs/prediction_samples.csv`
- `reports/result_report.md`
- `reports/result_report.html`
