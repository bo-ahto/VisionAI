# PP-H19 검색 신뢰도 x 예측 불확실성 보정 안정성 검증

## 목적

- H12B 보수 라벨 기반 H18 보정 후보가 test 단일 결과에서만 좋아진 것인지, 표본을 다시 뽑아도 개선 방향이 유지되는지 확인한다.
- row bootstrap은 개별 작품 단위의 흔들림을 본다.
- artist bootstrap은 작가 단위로 다시 뽑았을 때 특정 작가 몇 명 때문에 좋아진 결과인지 확인한다.
- delta 값은 `기준 모델 점수 - 후보 점수`다. MdAPE, MAPE, p95_APE, RMSE_log는 양수일수록 보정 후보가 더 좋다는 뜻이다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| experiment_id | PP-H19 |
| title | 검색 신뢰도 x 예측 불확실성 보정 안정성 검증 |
| started_at | 2026-06-03T14:47:09 |
| finished_at | 2026-06-03T14:47:21 |
| base_predictions | experiments/track6/PP-H14_H18_search_confidence_qwidth_policy_h12b/outputs/h14_confidence_range_predictions.csv |
| correction_maps | experiments/track6/PP-H14_H18_search_confidence_qwidth_policy_h12b/outputs/correction_maps.csv |
| bootstrap_iterations | 600 |
| seed | 20260603 |
| candidates | h18_qwidth_x_h12_median_min30_cap0.1, h18_qwidth_x_h12_median_min30_cap0.2, h18_qwidth_x_h12_median_min80_cap0.1, h18_qwidth_x_h12_median_min80_cap0.2 |
| note | H12B conservative automatic labels are used. This checks stability, not final production readiness. |

## Test 전체 점수

| experiment_id | split | slice | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H19 | test | overall | h18_qwidth_x_h12_median_min30_cap0.2 | 3099 | 0.426177 | 1.06112 | 3.00769 | 0.864339 | 0.345273 | 0.57212 |
| PP-H19 | test | overall | h18_qwidth_x_h12_median_min80_cap0.2 | 3099 | 0.426177 | 1.06112 | 3.00769 | 0.864339 | 0.345273 | 0.57212 |
| PP-H19 | test | overall | h18_qwidth_x_h12_median_min30_cap0.1 | 3099 | 0.428087 | 1.04827 | 3.00769 | 0.863555 | 0.337528 | 0.571475 |
| PP-H19 | test | overall | h18_qwidth_x_h12_median_min80_cap0.1 | 3099 | 0.428087 | 1.04827 | 3.00769 | 0.863555 | 0.337528 | 0.571475 |
| PP-H19 | test | overall | pp_y2_base | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |

## Bootstrap 안정성 요약

| experiment_id | bootstrap_type | candidate | metric | median_delta | ci_low_2_5 | ci_high_97_5 | prob_improvement_gt_0 | n_bootstrap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.1 | delta_MAPE | 0.00241473 | -0.0620816 | 0.0458924 | 0.535 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.1 | delta_MdAPE | 0.0159401 | -0.00416995 | 0.0388181 | 0.935 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.1 | delta_RMSE_log | -0.00677051 | -0.018135 | 0.00670048 | 0.168333 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.1 | delta_p95_APE | 0.0941046 | -0.456983 | 0.357569 | 0.648333 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.1 | delta_MAPE | 6.24892e-05 | -0.00772279 | 0.00826419 | 0.505 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.1 | delta_MdAPE | 0.0152858 | 0.00433197 | 0.0264992 | 0.995 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.1 | delta_RMSE_log | -0.0069039 | -0.00932516 | -0.00434636 | 0 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.1 | delta_p95_APE | 0.346047 | -0.14662 | 0.380716 | 0.961667 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.2 | delta_MAPE | -0.0089382 | -0.0840493 | 0.0454384 | 0.388333 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.2 | delta_MdAPE | 0.0183871 | -0.0076201 | 0.0442098 | 0.93 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.2 | delta_RMSE_log | -0.00756205 | -0.0196133 | 0.00893893 | 0.173333 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min30_cap0.2 | delta_p95_APE | 0.0176525 | -0.586789 | 0.357569 | 0.528333 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.2 | delta_MAPE | -0.0126089 | -0.0239362 | -0.00212009 | 0.00666667 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.2 | delta_MdAPE | 0.0180234 | 0.00558412 | 0.0287481 | 1 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.2 | delta_RMSE_log | -0.00773023 | -0.010618 | -0.00452523 | 0 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min30_cap0.2 | delta_p95_APE | 0.344678 | -0.169321 | 0.380716 | 0.961667 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.1 | delta_MAPE | 0.00241473 | -0.0620816 | 0.0458924 | 0.535 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.1 | delta_MdAPE | 0.0159401 | -0.00416995 | 0.0388181 | 0.935 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.1 | delta_RMSE_log | -0.00677051 | -0.018135 | 0.00670048 | 0.168333 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.1 | delta_p95_APE | 0.0941046 | -0.456983 | 0.357569 | 0.648333 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.1 | delta_MAPE | 6.24892e-05 | -0.00772279 | 0.00826419 | 0.505 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.1 | delta_MdAPE | 0.0152858 | 0.00433197 | 0.0264992 | 0.995 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.1 | delta_RMSE_log | -0.0069039 | -0.00932516 | -0.00434636 | 0 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.1 | delta_p95_APE | 0.346047 | -0.14662 | 0.380716 | 0.961667 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.2 | delta_MAPE | -0.0089382 | -0.0840493 | 0.0454384 | 0.388333 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.2 | delta_MdAPE | 0.0183871 | -0.0076201 | 0.0442098 | 0.93 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.2 | delta_RMSE_log | -0.00756205 | -0.0196133 | 0.00893893 | 0.173333 | 600 |
| PP-H19 | artist | h18_qwidth_x_h12_median_min80_cap0.2 | delta_p95_APE | 0.0176525 | -0.586789 | 0.357569 | 0.528333 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.2 | delta_MAPE | -0.0126089 | -0.0239362 | -0.00212009 | 0.00666667 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.2 | delta_MdAPE | 0.0180234 | 0.00558412 | 0.0287481 | 1 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.2 | delta_RMSE_log | -0.00773023 | -0.010618 | -0.00452523 | 0 | 600 |
| PP-H19 | row | h18_qwidth_x_h12_median_min80_cap0.2 | delta_p95_APE | 0.344678 | -0.169321 | 0.380716 | 0.961667 | 600 |

## 후보 해석

- `min80_cap0.2`: segment 표본 수 기준을 보수적으로 두고 보정 강도를 0.2 로그포인트까지 허용한 후보다. MdAPE 중심으로는 가장 좋지만, MAPE/RMSE에서는 덜 안정적일 수 있다.
- `min30_cap0.2`: 더 세분화된 segment 보정을 허용한 후보다. MdAPE 개선 폭은 조금 작지만 MAPE/RMSE까지 함께 낮추는 균형 후보로 볼 수 있다.
- bootstrap에서 artist 기준 개선 확률이 낮으면 특정 작가 구성에 민감하다는 뜻이므로 운영 적용 전 수동 검수 또는 보정 강도 축소가 필요하다.

## 검증 후보

- `h18_qwidth_x_h12_median_min30_cap0.1`
- `h18_qwidth_x_h12_median_min30_cap0.2`
- `h18_qwidth_x_h12_median_min80_cap0.1`
- `h18_qwidth_x_h12_median_min80_cap0.2`
