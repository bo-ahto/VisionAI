# PP-Y16 Cold PP-Y15 segment/cap OOF 고정 재검증

- 목적: `PP-Y15`에서 찾은 segment/cap 보정 후보가 test 반복 선택이 아니라 validation 내부 OOF 기준으로도 유지되는지 확인한다.
- 1차 예측값: `PP-Y2_cold_lgbq_search_external_combo` / `lgbq_search_all_external_interaction`.
- 선택 원칙: validation 내부 5-fold OOF 성능으로 후보를 고르고, full validation correction map을 test에 1회 적용한다.
- bin 기준: 예측 가격 bin과 quantile width bin은 validation 예측값으로 경계를 만들고 test에는 같은 경계를 적용한다.

## 선택 후보

| 선택 기준 | 후보 | validation OOF MdAPE | validation OOF MAPE | validation OOF p95 | test MdAPE | test MAPE | test p95 |
|---|---|---:|---:|---:|---:|---:|---:|
| `validation_oof_best_mdape` | `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |
| `validation_oof_best_mape` | `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |
| `validation_oof_best_p95` | `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15` | 0.3701 | 0.5517 | 1.3791 | 0.4382 | 1.0981 | 3.3512 |
| `validation_oof_balanced_rank` | `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |

## Validation OOF 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.6266 |
| `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min50_cap0.35` | 0.3501 | 0.5389 | 1.4564 | 0.6258 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.35` | 0.3562 | 0.5565 | 1.4491 | 0.6397 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min50_cap0.35` | 0.3562 | 0.5565 | 1.4491 | 0.6397 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min100_cap0.35` | 0.3562 | 0.5565 | 1.4491 | 0.6397 |
| `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.25` | 0.3574 | 0.5400 | 1.4357 | 0.6250 |
| `lgbq_search_all_external_interaction_pred_x_qwidth_oof_min50_cap0.25` | 0.3574 | 0.5425 | 1.4473 | 0.6246 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min150_cap0.35` | 0.3586 | 0.5632 | 1.4540 | 0.6413 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.35` | 0.3621 | 0.5475 | 1.4355 | 0.6418 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.35` | 0.3621 | 0.5475 | 1.4355 | 0.6418 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.35` | 0.3621 | 0.5475 | 1.4355 | 0.6418 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.35` | 0.3621 | 0.5475 | 1.4355 | 0.6418 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25` | 0.3648 | 0.5548 | 1.4282 | 0.6383 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min50_cap0.25` | 0.3648 | 0.5548 | 1.4282 | 0.6383 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min100_cap0.25` | 0.3648 | 0.5548 | 1.4282 | 0.6383 |

## Test 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25` | 0.4239 | 1.0003 | 3.3553 | 0.8557 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.15` | 0.4254 | 1.0016 | 3.3553 | 0.8523 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min50_cap0.25` | 0.4254 | 1.0042 | 3.4110 | 0.8539 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min100_cap0.25` | 0.4254 | 1.0042 | 3.4110 | 0.8539 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min150_cap0.25` | 0.4254 | 1.0042 | 3.4110 | 0.8539 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.1` | 0.4272 | 1.0084 | 3.4110 | 0.8513 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min50_cap0.15` | 0.4276 | 1.0055 | 3.4110 | 0.8505 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min100_cap0.15` | 0.4276 | 1.0055 | 3.4110 | 0.8505 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min150_cap0.15` | 0.4276 | 1.0055 | 3.4110 | 0.8505 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min50_cap0.1` | 0.4281 | 1.0119 | 3.4110 | 0.8497 |
| `lgbq_search_all_external_interaction_external_x_qwidth_oof_min100_cap0.1` | 0.4281 | 1.0119 | 3.4110 | 0.8497 |

## 판단

- 이 실험의 test 상위표는 탐색 참고용이고, 채택 판단은 `선택 후보` 표의 validation OOF 선택 결과를 우선한다.
- validation OOF 선택 후보가 closure의 test 최고 후보보다 낮게 나오면 closure 결과는 test 탐색 효과가 있었던 것으로 해석한다.
- validation OOF 선택 후보가 test에서도 개선을 유지하면 PP-Y15 보정 구조는 최종 후보로 재검증 가치가 높다.

## Bin 설정

```json
{
  "pred_edges": [
    -Infinity,
    13.98637485253728,
    14.554191460274637,
    14.98658227504755,
    15.666102312149368,
    Infinity
  ],
  "qwidth_edges": [
    -Infinity,
    0.6356332928881212,
    1.0924550438252805,
    1.7279045674222449,
    Infinity
  ]
}
```
