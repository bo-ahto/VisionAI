# PP-CF3 Warm CatBoost 보정값 강도 튜닝

- 실험 ID: `PP-CF3`
- 실행 시각: 2026-06-08T14:03:14
- 목적: CatBoost 모델 구조를 크게 바꾸지 않고, CatBoost residual 보정값의 배율과 상한만 조정해 과보정 여부를 확인한다.
- 기준가: `hcoef_stable` from `PP-HCOEF20`
- 선택 원칙: 후보 선택은 `validation_oof/all` 또는 목적별 `validation_oof/high_confidence` 기준이다. test는 진단용이다.

## 보정 공식

```text
raw_catboost_correction_log = CatBoost(features) -> actual_log - hcoef_stable 예측
tier_multiplier = 신뢰도 구간별 배율
final_correction_log = clip(raw_catboost_correction_log * global_strength * tier_multiplier, -cap, +cap)
final_pred_log = hcoef_stable + final_correction_log
```

즉, 이번 실험은 가격 모델 본체를 새로 바꾸는 것이 아니라 CatBoost가 만든 보정값만 조절한다.

## 신뢰도 기준

- 고신뢰: `{"quantile_width_max": 1.2, "component_prediction_spread_max": 0.1, "l10_price_range_ratio_max": 2.0, "svc_group_n_min": 5, "current_vs_stable_gap_abs_max": 0.025}`
- 저신뢰: `{"quantile_width_min": 1.6, "component_prediction_spread_min": 0.18, "l10_price_range_ratio_min": 2.5, "svc_group_n_max": 4, "current_vs_stable_gap_abs_min": 0.05}`
- 그 외: 중신뢰

## 신뢰도별 보정 배율 후보

| tier_profile | high_confidence | medium_confidence | low_confidence |
| --- | --- | --- | --- |
| same | 1.0000 | 1.0000 | 1.0000 |
| confidence_weighted_apply | 1.0000 | 0.4500 | 0.1500 |
| low_guarded | 1.0000 | 0.6000 | 0.2500 |
| low_off | 1.0000 | 1.0000 | 0.0000 |
| high_mid_guarded_low_off | 1.0000 | 0.5000 | 0.0000 |
| high_only | 1.0000 | 0.0000 | 0.0000 |

## 핵심 결과

| summary | candidate | model_policy | tier_profile | correction_cap_log | global_strength | split | slice | n | MdAPE | MAPE | p95_APE | RMSE_log | within_30 | over_50pct_error_rate | p95_abs_correction_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 기준가 validation 전체 | hcoef_stable | source | none | 0.0000 | 0.0000 | validation_oof | all | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.7784 | 0.0886 | 0.0000 |
| 기준가 test 전체 | hcoef_stable | source | none | 0.0000 | 0.0000 | test | all | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.7743 | 0.1186 | 0.0000 |
| validation 전체 1위 | cf3_cb_confidence_weighted_same_cap0p03_s1p15 | confidence_weighted | same | 0.0300 | 1.1500 | validation_oof | all | 519 | 0.1259 | 0.2061 | 0.6480 | 0.3228 | 0.7881 | 0.0867 | 0.0300 |
| validation 전체 1위 test | cf3_cb_confidence_weighted_same_cap0p03_s1p15 | confidence_weighted | same | 0.0300 | 1.1500 | test | all | 607 | 0.1388 | 0.2687 | 0.8119 | 0.3978 | 0.7825 | 0.1153 | 0.0300 |
| validation 고신뢰 1위 | cf3_cb_confidence_weighted_confidence_weighted_apply_cap0p03_s1p15 | confidence_weighted | confidence_weighted_apply | 0.0300 | 1.1500 | validation_oof | high_confidence | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| validation 고신뢰 1위 test | cf3_cb_confidence_weighted_confidence_weighted_apply_cap0p03_s1p15 | confidence_weighted | confidence_weighted_apply | 0.0300 | 1.1500 | test | high_confidence | 100 | 0.1063 | 0.1261 | 0.3367 | 0.1668 | 0.9100 | 0.0100 | 0.0300 |

## 결론

- validation 전체 기준으로는 `cf3_cb_confidence_weighted_same_cap0p03_s1p15`가 1위다. 기준가 MAPE `0.2082`에서 `0.2061`로 낮아졌다.
- 같은 후보의 test 전체 진단값은 기준가 MAPE `0.2730`에서 `0.2687`로 낮아진다. 다만 p95는 `0.8064`에서 `0.8119`로 약간 커진다.
- test 전체 진단 1위는 `cf3_cb_confidence_weighted_same_cap0p12_s1p15`이고 MAPE `0.2681`다. 하지만 이 후보는 test를 보고 고른 값이므로 운영 후보로 바로 선택하지 않는다.
- 고신뢰 기준 CatBoost 후보는 validation MAPE `0.1360`, test 고신뢰 MAPE `0.1261`다. 기준가보다는 낮지만 개선폭은 작다.
- 따라서 이 실험의 결론은 `CatBoost 보정값은 작게(cap 0.02~0.03) 제한하면 방어적으로 개선 가능하지만, 큰 cap을 허용하면 validation 안정성이 약해진다`이다.

## Validation 전체 기준 상위 후보

| candidate | model_policy | tier_profile | correction_cap_log | global_strength | n | MdAPE | MAPE | p95_APE | RMSE_log | within_30 | over_50pct_error_rate | p95_abs_correction_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cf3_cb_confidence_weighted_same_cap0p03_s1p15 | confidence_weighted | same | 0.0300 | 1.1500 | 519 | 0.1259 | 0.2061 | 0.6480 | 0.3228 | 0.7881 | 0.0867 | 0.0300 |
| cf3_cb_confidence_weighted_same_cap0p02_s1p15 | confidence_weighted | same | 0.0200 | 1.1500 | 519 | 0.1251 | 0.2062 | 0.6472 | 0.3231 | 0.7823 | 0.0886 | 0.0200 |
| cf3_cb_confidence_weighted_same_cap0p02_s1 | confidence_weighted | same | 0.0200 | 1.0000 | 519 | 0.1254 | 0.2062 | 0.6476 | 0.3231 | 0.7823 | 0.0886 | 0.0200 |
| cf3_cb_confidence_weighted_same_cap0p03_s1 | confidence_weighted | same | 0.0300 | 1.0000 | 519 | 0.1254 | 0.2062 | 0.6481 | 0.3230 | 0.7881 | 0.0867 | 0.0300 |
| cf3_cb_confidence_weighted_same_cap0p02_s0p9 | confidence_weighted | same | 0.0200 | 0.9000 | 519 | 0.1258 | 0.2063 | 0.6478 | 0.3233 | 0.7823 | 0.0886 | 0.0200 |
| cf3_cb_confidence_weighted_same_cap0p03_s0p9 | confidence_weighted | same | 0.0300 | 0.9000 | 519 | 0.1259 | 0.2063 | 0.6481 | 0.3231 | 0.7881 | 0.0886 | 0.0300 |
| cf3_cb_confidence_weighted_same_cap0p015_s1p15 | confidence_weighted | same | 0.0150 | 1.1500 | 519 | 0.1262 | 0.2064 | 0.6464 | 0.3234 | 0.7823 | 0.0886 | 0.0150 |
| cf3_cb_confidence_weighted_same_cap0p02_s0p75 | confidence_weighted | same | 0.0200 | 0.7500 | 519 | 0.1267 | 0.2065 | 0.6481 | 0.3234 | 0.7823 | 0.0886 | 0.0200 |
| cf3_cb_confidence_weighted_same_cap0p015_s1 | confidence_weighted | same | 0.0150 | 1.0000 | 519 | 0.1262 | 0.2065 | 0.6467 | 0.3235 | 0.7823 | 0.0886 | 0.0150 |
| cf3_cb_confidence_weighted_same_cap0p03_s0p75 | confidence_weighted | same | 0.0300 | 0.7500 | 519 | 0.1265 | 0.2065 | 0.6482 | 0.3232 | 0.7842 | 0.0886 | 0.0300 |
| cf3_cb_confidence_weighted_same_cap0p015_s0p9 | confidence_weighted | same | 0.0150 | 0.9000 | 519 | 0.1262 | 0.2065 | 0.6470 | 0.3235 | 0.7823 | 0.0886 | 0.0150 |
| cf3_cb_all_rows_same_cap0p05_s0p9 | all_rows | same | 0.0500 | 0.9000 | 519 | 0.1236 | 0.2066 | 0.6505 | 0.3223 | 0.7842 | 0.0906 | 0.0500 |
| cf3_cb_confidence_weighted_same_cap0p015_s0p75 | confidence_weighted | same | 0.0150 | 0.7500 | 519 | 0.1265 | 0.2066 | 0.6473 | 0.3236 | 0.7823 | 0.0886 | 0.0150 |
| cf3_cb_confidence_weighted_same_cap0p03_s0p65 | confidence_weighted | same | 0.0300 | 0.6500 | 519 | 0.1274 | 0.2066 | 0.6482 | 0.3233 | 0.7842 | 0.0886 | 0.0300 |
| cf3_cb_all_rows_same_cap0p05_s0p75 | all_rows | same | 0.0500 | 0.7500 | 519 | 0.1239 | 0.2066 | 0.6502 | 0.3227 | 0.7842 | 0.0906 | 0.0500 |

## Validation 고신뢰 기준 상위 후보

| candidate | model_policy | tier_profile | correction_cap_log | global_strength | n | MdAPE | MAPE | p95_APE | RMSE_log | within_30 | over_50pct_error_rate | p95_abs_correction_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cf3_cb_confidence_weighted_confidence_weighted_apply_cap0p03_s1p15 | confidence_weighted | confidence_weighted_apply | 0.0300 | 1.1500 | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_high_mid_guarded_low_off_cap0p03_s1p15 | confidence_weighted | high_mid_guarded_low_off | 0.0300 | 1.1500 | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_high_only_cap0p03_s1p15 | confidence_weighted | high_only | 0.0300 | 1.1500 | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_low_guarded_cap0p03_s1p15 | confidence_weighted | low_guarded | 0.0300 | 1.1500 | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_low_off_cap0p03_s1p15 | confidence_weighted | low_off | 0.0300 | 1.1500 | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_same_cap0p03_s1p15 | confidence_weighted | same | 0.0300 | 1.1500 | 91 | 0.0726 | 0.1360 | 0.4795 | 0.2534 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_confidence_weighted_apply_cap0p02_s1p15 | confidence_weighted | confidence_weighted_apply | 0.0200 | 1.1500 | 91 | 0.0723 | 0.1361 | 0.4782 | 0.2550 | 0.8462 | 0.0549 | 0.0200 |
| cf3_cb_confidence_weighted_high_mid_guarded_low_off_cap0p02_s1p15 | confidence_weighted | high_mid_guarded_low_off | 0.0200 | 1.1500 | 91 | 0.0723 | 0.1361 | 0.4782 | 0.2550 | 0.8462 | 0.0549 | 0.0200 |
| cf3_cb_confidence_weighted_high_only_cap0p02_s1p15 | confidence_weighted | high_only | 0.0200 | 1.1500 | 91 | 0.0723 | 0.1361 | 0.4782 | 0.2550 | 0.8462 | 0.0549 | 0.0200 |
| cf3_cb_confidence_weighted_low_guarded_cap0p02_s1p15 | confidence_weighted | low_guarded | 0.0200 | 1.1500 | 91 | 0.0723 | 0.1361 | 0.4782 | 0.2550 | 0.8462 | 0.0549 | 0.0200 |
| cf3_cb_confidence_weighted_low_off_cap0p02_s1p15 | confidence_weighted | low_off | 0.0200 | 1.1500 | 91 | 0.0723 | 0.1361 | 0.4782 | 0.2550 | 0.8462 | 0.0549 | 0.0200 |
| cf3_cb_confidence_weighted_same_cap0p02_s1p15 | confidence_weighted | same | 0.0200 | 1.1500 | 91 | 0.0723 | 0.1361 | 0.4782 | 0.2550 | 0.8462 | 0.0549 | 0.0200 |
| cf3_cb_confidence_weighted_confidence_weighted_apply_cap0p03_s1 | confidence_weighted | confidence_weighted_apply | 0.0300 | 1.0000 | 91 | 0.0726 | 0.1361 | 0.4795 | 0.2536 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_high_mid_guarded_low_off_cap0p03_s1 | confidence_weighted | high_mid_guarded_low_off | 0.0300 | 1.0000 | 91 | 0.0726 | 0.1361 | 0.4795 | 0.2536 | 0.8571 | 0.0549 | 0.0300 |
| cf3_cb_confidence_weighted_high_only_cap0p03_s1 | confidence_weighted | high_only | 0.0300 | 1.0000 | 91 | 0.0726 | 0.1361 | 0.4795 | 0.2536 | 0.8571 | 0.0549 | 0.0300 |

## Test 전체 상위 후보

진단용이다. 후보 선택에는 사용하지 않는다.

| candidate | model_policy | tier_profile | correction_cap_log | global_strength | n | MdAPE | MAPE | p95_APE | RMSE_log | within_30 | over_50pct_error_rate | p95_abs_correction_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cf3_cb_confidence_weighted_same_cap0p12_s1p15 | confidence_weighted | same | 0.1200 | 1.1500 | 607 | 0.1412 | 0.2681 | 0.8369 | 0.3981 | 0.7825 | 0.1120 | 0.0974 |
| cf3_cb_confidence_weighted_same_cap0p08_s1p15 | confidence_weighted | same | 0.0800 | 1.1500 | 607 | 0.1415 | 0.2682 | 0.8327 | 0.3983 | 0.7825 | 0.1104 | 0.0800 |
| cf3_cb_confidence_weighted_same_cap0p05_s1p15 | confidence_weighted | same | 0.0500 | 1.1500 | 607 | 0.1397 | 0.2682 | 0.8203 | 0.3981 | 0.7825 | 0.1137 | 0.0500 |
| cf3_cb_confidence_weighted_same_cap0p12_s1 | confidence_weighted | same | 0.1200 | 1.0000 | 607 | 0.1392 | 0.2683 | 0.8370 | 0.3979 | 0.7809 | 0.1104 | 0.0847 |
| cf3_cb_confidence_weighted_same_cap0p08_s1 | confidence_weighted | same | 0.0800 | 1.0000 | 607 | 0.1398 | 0.2684 | 0.8325 | 0.3980 | 0.7809 | 0.1087 | 0.0800 |
| cf3_cb_confidence_weighted_same_cap0p12_s0p9 | confidence_weighted | same | 0.1200 | 0.9000 | 607 | 0.1398 | 0.2685 | 0.8371 | 0.3978 | 0.7809 | 0.1104 | 0.0763 |
| cf3_cb_confidence_weighted_same_cap0p05_s1 | confidence_weighted | same | 0.0500 | 1.0000 | 607 | 0.1391 | 0.2685 | 0.8200 | 0.3981 | 0.7809 | 0.1120 | 0.0500 |
| cf3_cb_confidence_weighted_same_cap0p08_s0p9 | confidence_weighted | same | 0.0800 | 0.9000 | 607 | 0.1403 | 0.2685 | 0.8323 | 0.3979 | 0.7809 | 0.1087 | 0.0763 |
| cf3_cb_all_rows_low_off_cap0p12_s1p15 | all_rows | low_off | 0.1200 | 1.1500 | 607 | 0.1439 | 0.2686 | 0.8127 | 0.3965 | 0.7792 | 0.1137 | 0.0762 |
| cf3_cb_all_rows_same_cap0p12_s0p9 | all_rows | same | 0.1200 | 0.9000 | 607 | 0.1467 | 0.2686 | 0.8299 | 0.3975 | 0.7842 | 0.1137 | 0.0746 |
| cf3_cb_confidence_weighted_same_cap0p05_s0p9 | confidence_weighted | same | 0.0500 | 0.9000 | 607 | 0.1398 | 0.2686 | 0.8198 | 0.3981 | 0.7825 | 0.1120 | 0.0500 |
| cf3_cb_all_rows_same_cap0p12_s1 | all_rows | same | 0.1200 | 1.0000 | 607 | 0.1476 | 0.2687 | 0.8316 | 0.3976 | 0.7842 | 0.1153 | 0.0829 |
| cf3_cb_confidence_weighted_same_cap0p08_s0p75 | confidence_weighted | same | 0.0800 | 0.7500 | 607 | 0.1394 | 0.2687 | 0.8292 | 0.3977 | 0.7809 | 0.1120 | 0.0635 |
| cf3_cb_all_rows_low_off_cap0p08_s1p15 | all_rows | low_off | 0.0800 | 1.1500 | 607 | 0.1418 | 0.2687 | 0.8127 | 0.3966 | 0.7792 | 0.1137 | 0.0762 |
| cf3_cb_confidence_weighted_same_cap0p03_s1p15 | confidence_weighted | same | 0.0300 | 1.1500 | 607 | 0.1388 | 0.2687 | 0.8119 | 0.3978 | 0.7825 | 0.1153 | 0.0300 |

## 학습 정책

| policy | description | weighted | train_n | high_confidence_n | medium_confidence_n | low_confidence_n | fold_train_n_min | fold_train_n_max | feature_count | categorical_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_rows | validation 전체 row로 CatBoost residual 학습 | 0 | 519 | 91 | 256 | 172 | 414 | 416 | 27 | 9 |
| confidence_weighted | 전체 row 학습 + 신뢰도별 sample weight | 1 | 519 | 91 | 256 | 172 | 414 | 416 | 27 | 9 |
| high_mid_only | 저신뢰 row 제외 후 고신뢰+중신뢰로 학습 | 0 | 347 | 91 | 256 | 0 | 274 | 283 | 27 | 9 |

## 신뢰도 구간별 기준가 성능

| split | confidence_tier | n | quantile_width_median | component_spread_median | l10_range_ratio_median | svc_group_n_median | gap_abs_median | base_MdAPE | base_MAPE | base_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | high_confidence | 100 | 1.0117 | 0.0400 | 1.1221 | 13.0000 | 0.0118 | 0.0950 | 0.1272 | 0.3187 |
| test | low_confidence | 221 | 1.7812 | 0.1489 | 2.3379 | 7.0000 | 0.0250 | 0.2104 | 0.3998 | 1.5476 |
| test | medium_confidence | 286 | 1.3629 | 0.0659 | 1.5582 | 8.0000 | 0.0247 | 0.1168 | 0.2260 | 0.7309 |
| validation | high_confidence | 91 | 1.0582 | 0.0420 | 1.1390 | 10.0000 | 0.0139 | 0.0722 | 0.1387 | 0.4876 |
| validation | low_confidence | 172 | 1.7710 | 0.1374 | 2.3479 | 7.0000 | 0.0250 | 0.1525 | 0.2658 | 0.9520 |
| validation | medium_confidence | 256 | 1.3206 | 0.0685 | 1.5129 | 8.0000 | 0.0250 | 0.1273 | 0.1942 | 0.5801 |

## 해석

- CatBoost 보정값은 validation 전체 MAPE를 낮추는 후보가 존재하는지 확인하는 용도다.
- `same` profile은 모든 구간에 같은 보정을 적용하므로 저신뢰 구간 과보정 여부를 반드시 확인해야 한다.
- `low_guarded`, `low_off`, `high_mid_guarded_low_off`, `high_only`는 저신뢰 보정을 줄이거나 끄는 보수적 후보군이다.
- validation 1위가 test에서 기준가보다 악화되면 보정값 튜닝 자체가 과적합된 것으로 해석해야 한다.

## 산출물

- `outputs/metrics.csv`
- `outputs/raw_catboost_corrections.csv`
- `outputs/top_candidate_predictions.csv`
- `outputs/validation_all_ranking.csv`
- `outputs/validation_high_confidence_ranking.csv`
- `outputs/test_all_ranking_diagnostic.csv`
- `outputs/confidence_tier_summary.csv`
- `outputs/training_policy_audit.csv`
- `artifacts/run_config.json`