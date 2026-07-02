# Warm/Cold 테스트 방식 검증 감사

- 작성일: 2026-06-11 10:54:31
- 목적: 같은 입력에 대한 결과 변동, 재현 실패, row 순서 영향, label 누수, split 중복, 반복 OOF/holdout 안정성 의심 항목 점검

## 1. 결론

| 구분 | 결론 | 핵심 근거 |
|---|---|---|
| Warm | 통과 | fixed test/validation OOF 지표 재현, row shuffle diff `0.000e+00`, label 독립성 diff `0.000e+00` |
| Cold | 통과 | 기존 재현 all_passed `True`, row shuffle diff `0.000e+00`, label 독립성 diff `0.000e+00` |

- 현재 감사 기준: 같은 입력을 반복하거나 row 순서를 바꿔도 예측 로그가격은 변하지 않음
- 현재 감사 기준: 실제 가격 label을 임의 값으로 바꿔도 예측 로그가격은 변하지 않음
- 현재 감사 기준: validation/test row id 중복은 확인되지 않음
- 남는 주의점: 이 검증은 현재 고정된 artifact와 저장된 OOF/holdout 산출물 기준의 감사이며, 원천 데이터가 바뀌거나 재학습 정책이 바뀌면 같은 감사를 다시 수행해야 함

## 2. Warm 검증 결과

- 대상 모델: Warm PP258 기준가격 기반 미세 보정 모델
- row 수: 전체 `1126`, fixed test `607`, validation OOF `519`
- fixed test 지표 최대 재현 차이: `0.000e+00`
- validation OOF 지표 최대 재현 차이: `0.000e+00`
- row 순서 셔플 최대 예측 로그가격 차이: `0.000e+00`
- label 독립성 최대 예측 로그가격 차이: `0.000e+00`
- split 중복/중복 row id 점검: 통과

| 점검 항목 | 결과 |
|---|---|
| `fixed_test_metrics_reproduced` | 통과 |
| `validation_oof_metrics_reproduced` | 통과 |
| `same_input_same_output_under_row_shuffle` | 통과 |
| `prediction_does_not_use_labels` | 통과 |
| `split_row_ids_are_disjoint_and_unique` | 통과 |
| `all_passed` | 통과 |

### 2.1 Warm 반복 OOF/holdout 근거

- 근거 파일: `experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/outputs/selected_stability_repeated_summary.csv`
- 확인 시나리오: artist_group_holdout, confidence_stratified_rows, full_split, price_band_stratified_rows, risk_focus_bootstrap, row_bootstrap
- 반복 holdout/bootstrap 행 수: `10` (단일 full split 행 제외)
- 최종 후보의 incumbent MAPE win rate 최소값(full split 제외): `0.788462`
- 최종 후보의 incumbent p95 win rate 범위(full split 제외): `0.500000` ~ `0.857692`
- 반복 시나리오 평균 MAPE 범위: `0.205415` ~ `0.370475`
- 해석: Warm 최종 후보는 MAPE 안정성 중심 후보이며, p95는 fixed test 재현과 별도 안정성 후보 비교로 함께 관리

## 3. Cold 검증 결과

- 대상 모델: Cold 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정 모델
- row 수: 전체 `5852`, fixed test `3099`, validation `2753`
- 기록 지표와 재계산 지표 최대 차이: `1.110e-16`
- validation에서 재계산한 guard 임계값 최대 차이: `0.000e+00`
- 후처리기와 독립 계산식의 최대 예측 로그가격 차이: `0.000e+00`
- row 순서 셔플 최대 예측 로그가격 차이: `0.000e+00`
- label 독립성 최대 예측 로그가격 차이: `0.000e+00`
- split 중복/중복 row id 점검: 통과

| 점검 항목 | 결과 |
|---|---|
| `recorded_reproducibility_all_passed` | 통과 |
| `recorded_metric_diff_is_zero` | 통과 |
| `recorded_threshold_diff_is_zero` | 통과 |
| `postprocessor_matches_independent_formula` | 통과 |
| `same_input_same_output_under_row_shuffle` | 통과 |
| `prediction_does_not_use_labels` | 통과 |
| `split_row_ids_are_disjoint_and_unique` | 통과 |
| `all_passed` | 통과 |

### 3.1 Cold 반복 OOF/holdout 근거

- 근거 파일: `experiments/track6/PP-QR4_cold_qwidth_repeated_split_revalidation/outputs/holdout_summary.csv`
- `row_5fold` guard 후보: folds `60`, mean MdAPE `0.366469`, MAPE 개선확률 `1.000000`, p95 개선확률 `0.983333`
- `artist_5fold` guard 후보: folds `60`, mean MdAPE `0.374188`, MAPE 개선확률 `0.983333`, p95 개선확률 `0.850000`
- test bootstrap guard 후보: MdAPE 평균 `0.419174`, 95% CI `0.405054` ~ `0.436375`, baseline 대비 MdAPE 개선확률 `0.907500`

## 4. 의심 항목별 판단

| 의심 항목 | 확인 방법 | 판단 |
|---|---|---|
| 같은 입력인데 결과가 매번 달라지는가 | 같은 artifact 계산식을 여러 번 적용하고 row 순서도 셔플 | Warm/Cold 모두 차이 0 수준으로 통과 |
| row 순서가 바뀌면 결과가 바뀌는가 | 5개 seed로 입력 row 순서 랜덤 셔플 후 row id 기준 재정렬 비교 | Warm/Cold 모두 차이 0 수준으로 통과 |
| 실제 가격 label이 예측에 섞였는가 | actual_price/actual_log를 임의 값으로 바꾼 뒤 예측 로그가격 비교 | Warm/Cold 모두 예측값 변화 없음 |
| validation/test가 섞였는가 | split별 row id 중복과 split 간 overlap 확인 | Warm/Cold 모두 중복 없음 |
| 재현 지표가 기록과 맞는가 | 저장된 metrics와 재계산 metrics 비교 | Warm은 fixed test/validation OOF 재현, Cold는 기록 지표와 최대 차이 1e-16 수준 |
| 랜덤 OOF/holdout에서 값이 튀는가 | 기존 반복 holdout/OOF 산출물 확인 | Warm은 반복 시나리오에서 최종 후보 win rate 유지, Cold guard는 row/artist holdout에서 MAPE/p95 개선확률 유지 |

## 5. 운영 권고

- 현재 고정 artifact 기준 테스트 방식은 재현성과 결정성 관점에서 통과
- 외부 공유 시 fixed test 지표와 validation/OOF 지표를 구분해서 설명
- 새 데이터 수집, split 변경, 재학습, 검색 피처 재생성 시 동일 감사 스크립트를 다시 실행
- 최종 성능 주장에는 fixed test 기준 수치를 사용하고, OOF/holdout은 안정성 근거로 별도 표기

