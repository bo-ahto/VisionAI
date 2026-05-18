# T6-E005 피처 조합 ablation

- 날짜: `2026-05-18`
- 관련 가설: `T6-H5`
- 상태: 검증 완료
- 목적: 운영에서 만들 수 있는 크기/재료/지지체 조합 피처가 Warm/Cold 성능을 개선하는지 확인
- 사용 데이터: Track6 name-corrected feature/label split
- 사용 스크립트: `scripts/track6/run_t6_e005_feature_combo_ablation.py`
- 결과 JSON: `data/track6/results/t6_e005_feature_combo_ablation.json`
- 예측 CSV: `data/track6/predictions/t6_e005_feature_combo_ablation_predictions.csv`

## 1. 실험 방법

- Warm: T6-E003에서 검증된 `CatBoost + artist_key` 구조를 고정하고 피처 조합만 변경
- Cold: T6-E004에서 확인한 `hist_quantile`과 `huber`를 사용해 대표 오차와 큰 오차를 같이 확인
- size bucket은 train 기준 `log_area` 분위수로 만들고 validation에는 같은 기준을 적용
- 정답 가격은 feature 생성에 사용하지 않고 평가 단계에서만 label 파일을 결합

## 2. validation 결과

| split | model | feature set | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |
|---|---|---|---:|---:|---:|---:|---:|
| `val_cold` | `hist_quantile_cold` | `base` | `0.3782` | `1.9444` | `0.3899` | `0.6169` | `0.6776` |
| `val_cold` | `hist_quantile_cold` | `base_large_flags` | `0.3793` | `1.9722` | `0.4182` | `0.6101` | `0.6760` |
| `val_cold` | `hist_quantile_cold` | `base_support_size` | `0.3817` | `1.9461` | `0.4114` | `0.6173` | `0.6785` |
| `val_cold` | `hist_quantile_cold` | `all_operational_combos` | `0.3826` | `1.9958` | `0.3878` | `0.6101` | `0.6854` |
| `val_cold` | `hist_quantile_cold` | `base_size_shape` | `0.3831` | `1.9443` | `0.3874` | `0.6130` | `0.6783` |
| `val_cold` | `huber_cold` | `base_support_size` | `0.3850` | `1.4394` | `0.4071` | `0.6119` | `0.6492` |
| `val_cold` | `hist_quantile_cold` | `base_medium_shape` | `0.3853` | `1.8629` | `0.4153` | `0.6165` | `0.6757` |
| `val_cold` | `hist_quantile_cold` | `base_medium_size` | `0.3888` | `1.8670` | `0.3913` | `0.6094` | `0.6789` |
| `val_cold` | `huber_cold` | `base_size_shape` | `0.3888` | `1.3835` | `0.4117` | `0.6026` | `0.6480` |
| `val_cold` | `hist_quantile_cold` | `base_existing_combo` | `0.3903` | `1.8895` | `0.3903` | `0.6151` | `0.6795` |
| `val_cold` | `huber_cold` | `base_large_flags` | `0.3908` | `1.3987` | `0.4071` | `0.6040` | `0.6477` |
| `val_cold` | `huber_cold` | `base_medium_shape` | `0.3909` | `1.4871` | `0.4053` | `0.6255` | `0.6538` |
| `val_cold` | `huber_cold` | `base` | `0.3956` | `1.4749` | `0.4032` | `0.6058` | `0.6485` |
| `val_cold` | `huber_cold` | `base_medium_size` | `0.3973` | `1.4585` | `0.4024` | `0.5994` | `0.6645` |
| `val_cold` | `huber_cold` | `all_operational_combos` | `0.4023` | `1.5297` | `0.3924` | `0.6233` | `0.6596` |
| `val_cold` | `huber_cold` | `base_existing_combo` | `0.4042` | `1.4773` | `0.3921` | `0.6140` | `0.6906` |
| `val_warm` | `catboost_warm_artist` | `base_medium_size` | `0.2665` | `1.1814` | `0.5468` | `0.7457` | `0.6135` |
| `val_warm` | `catboost_warm_artist` | `base_support_size` | `0.2676` | `1.1845` | `0.5507` | `0.7380` | `0.6179` |
| `val_warm` | `catboost_warm_artist` | `all_operational_combos` | `0.2705` | `1.1686` | `0.5411` | `0.7419` | `0.6180` |
| `val_warm` | `catboost_warm_artist` | `base_size_shape` | `0.2731` | `1.1628` | `0.5430` | `0.7380` | `0.6186` |
| `val_warm` | `catboost_warm_artist` | `base` | `0.2738` | `1.1571` | `0.5258` | `0.7380` | `0.6116` |
| `val_warm` | `catboost_warm_artist` | `base_large_flags` | `0.2740` | `1.2439` | `0.5315` | `0.7380` | `0.6192` |
| `val_warm` | `catboost_warm_artist` | `base_existing_combo` | `0.2829` | `1.1854` | `0.5124` | `0.7304` | `0.6191` |
| `val_warm` | `catboost_warm_artist` | `base_medium_shape` | `0.2880` | `1.2011` | `0.5143` | `0.7323` | `0.6190` |

## 3. 핵심 해석

- Warm 최저 median APE: `0.2665` (`base_medium_size`)
- Cold 최저 median APE: `0.3782` (`hist_quantile_cold`, `base`)
- Cold 최저 p95 APE: `1.3835` (`huber_cold`, `base_size_shape`)
- Warm과 Cold에서 같은 조합 피처가 항상 같은 방향으로 작동하지 않으므로 모델별 피처셋 분리 관리가 필요

## 4. 결론

- T6-H5는 validation 기준 검증 완료
- 피처 조합은 후보 선정에 포함하되, Warm/Cold 최종 피처셋은 별도로 고정해야 함
- 다음 단계는 validation 기준 최종 후보 선정(T6-E006)
