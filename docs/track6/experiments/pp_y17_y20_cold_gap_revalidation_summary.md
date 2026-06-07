# PP-Y17~PP-Y20 Cold 남은 Gap 재검증 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y17_y20_cold_gap_revalidation.py`
- 요약 지표: `experiments/track6/PP-Y17_Y20_cold_gap_summary_metrics.csv`
- 실험 폴더:
  - `experiments/track6/PP-Y17_cold_y10_oof_fixed_routing_revalidation`
  - `experiments/track6/PP-Y18_cold_y16_top_candidate_stability`
  - `experiments/track6/PP-Y19_cold_y2_artist_bootstrap_stability`
  - `experiments/track6/PP-Y20_cold_mape_p95_purpose_routing`

## 1. 실험 목적

- `PP-Y10` q-width 라우팅은 test 기준으로 0.4302 수준의 좋은 후보가 있었지만, validation 기준으로 고정했을 때도 유지되는지 확인이 필요했다.
- `PP-Y16`에는 test MdAPE 0.423~0.425 수준의 후보가 있었지만, 기존 요약에서 validation OOF 선택 후보는 0.4438 수준으로 내려왔다.
- 따라서 test 상위 후보를 바로 채택하지 않고, validation 고정 선택과 bootstrap 안정성으로 남은 gap을 확인했다.

## 2. PP-Y17 결과: PP-Y10 validation 고정 라우팅

| 선택 기준 | test MdAPE | test MAPE | test p95_APE | 판단 |
|---|---:|---:|---:|---|
| validation p95 guarded | 0.4620 | 1.0369 | 2.9954 | p95는 양호하지만 대표 정확도 약함 |
| validation best MdAPE / MAPE / balanced | 0.4763 | 1.0786 | 3.0322 | 기존 PP-Y2보다 약함 |

해석:

- `PP-Y10`의 test 상위 후보 0.4302는 validation 기준 고정 선택에서는 재현되지 않았다.
- q-width 라우팅은 큰 오차 방어 후보로는 참고할 수 있지만, 대표 점 예측 후보로 바로 채택하기 어렵다.

## 3. PP-Y18 결과: PP-Y16 test 상위 후보 안정성

| 후보 | test MdAPE | test MAPE | test p95_APE | 해석 |
|---|---:|---:|---:|---|
| `external_x_qwidth_oof_min30_cap0.25` | 0.4239 | 1.0003 | 3.3553 | test MdAPE 최고, MAPE도 개선 |
| `qwidth_bin_oof_min30/50/100/150_cap0.25` | 0.4247 | 0.9910 | 3.3053 | MAPE/p95 균형이 더 좋음 |
| 기존 `PP-Y2` | 0.4421 | 1.0484 | 3.3537 | 현재 단일 기준 후보 |
| validation OOF 선택 `pred_x_qwidth_oof_min30_cap0.35` | 0.4438 | 1.1083 | 2.8025 | p95 방어는 강하지만 MAPE 악화 |

Bootstrap 해석:

- `external_x_qwidth_oof_min30_cap0.25`
  - row bootstrap 기준 MdAPE 개선 확률 0.9975, MAPE 개선 확률 1.0000.
  - artist bootstrap 기준 MdAPE 개선 확률 0.8763, MAPE 개선 확률 0.9975.
  - p95는 중앙값 기준 개선이나 artist bootstrap 신뢰구간이 0을 걸쳐 최종 방어 후보로는 추가 확인이 필요하다.
- `qwidth_bin_oof_min30_cap0.25`
  - row bootstrap 기준 MdAPE/MAPE/p95 개선 확률이 각각 0.9938, 1.0000, 0.9988.
  - artist bootstrap 기준 MdAPE/MAPE/p95 개선 확률이 각각 0.8488, 0.9988, 0.9513.
  - 대표 정확도, 평균 오차, 큰 오차 방어의 균형이 가장 좋다.

## 4. PP-Y19 결과: PP-Y2 안정성 기준선

| 후보 | test MdAPE | test MAPE | test p95_APE |
|---|---:|---:|---:|
| `PP-Y2 lgbq_search_all_external_interaction` | 0.4421 | 1.0484 | 3.3537 |

Bootstrap 기준:

- row bootstrap MdAPE 95% 구간은 0.4212~0.4635.
- artist bootstrap MdAPE 95% 구간은 0.3751~0.5252로 더 넓다.
- Cold 성능은 작가 구성에 따라 흔들림이 크므로, 단일 test 수치만으로 후보를 확정하기 어렵다.

## 5. PP-Y20 결과: MAPE/p95 목적별 라우팅

| 후보 | test MdAPE | test MAPE | test p95_APE | 판단 |
|---|---:|---:|---:|---|
| `component_pp_y16_p95_pred` | 0.4382 | 1.0981 | 3.3512 | 단일 component 기준 |
| `component_pp_y2_pred` | 0.4421 | 1.0484 | 3.3537 | 기존 기준 |
| `component_pp_y16_defensive_pred` | 0.4438 | 1.1083 | 2.8025 | p95 방어용 |
| validation 선택 라우팅 best | 0.4494~0.4603 | 1.0552~1.0783 | 3.6483~3.8973 | 라우팅 보류 |

해석:

- PP-Y2, PP-W4, PP-Y16을 q-width 구간으로 나누는 3-way 라우팅은 test에서 단일 component보다 나빠졌다.
- 현재 Cold는 복잡한 다중 라우팅보다 `PP-Y16 qwidth_bin cap0.25` 같은 단순 segment 보정 후보가 더 유망하다.

## 6. 결론

- `PP-Y17` 결과상 `PP-Y10` 라우팅은 대표 후보로 채택하지 않는다.
- `PP-Y20` 목적별 라우팅도 보류한다.
- Cold에서 새롭게 가장 유망한 후보는 `PP-Y18`에서 확인한 `qwidth_bin_oof_min30_cap0.25` 계열이다.
- 이 후보는 test MdAPE 0.4247, MAPE 0.9910, p95 3.3053으로 기존 `PP-Y2`보다 균형이 좋고 bootstrap 개선 확률도 높다.
- 다만 이 후보는 test 상위 후보에서 출발했으므로, 최종 채택 전에는 별도 seed/split 재실행 또는 고정 holdout 검증을 한 번 더 거치는 것이 안전하다.
