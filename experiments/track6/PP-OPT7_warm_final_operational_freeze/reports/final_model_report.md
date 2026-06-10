# PP-OPT7 Warm 최종 운영 후보 고정

- 작성일: 2026-06-09 09:18
- 최종 모델 ID: `warm_catboost_artist_qcap_risk_strict_v1`
- 기준 후보: `hcoef_stable`
- 최종 후보: `p95guard__seed=combo_cat=cb_tier=same__qmult=same__cap=0p02__caprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__guard=risk_strict_cap0p020`
- 원 seed 후보: `combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025`

## 1. 선정 이유

- PP-OPT6 운영 조건을 통과했다.
- fixed test에서 MdAPE와 MAPE가 개선됐다.
- fixed test p95 악화가 0.002 이하로 제한됐다.
- 반복 validation에서 MAPE 개선률이 100%였고 p95 비악화율이 65% 수준이었다.
- OPT5 seed 대비 p95 악화 폭을 줄이면서 실사용 가능한 성능 개선을 유지했다.

## 2. 최종 성능

| model_id | eval_split | n | MdAPE | MAPE | p95_APE | delta_MdAPE | delta_MAPE | delta_p95_APE | guarded_test_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_hcoef_stable | test | 607 | 0.138803 | 0.272989 | 0.806366 | 0.000000 | 0.000000 | 0.000000 | False |
| reference_current_70_30 | test | 607 | 0.140484 | 0.274799 | 0.833074 | 0.001680 | 0.001810 | 0.026708 | False |
| warm_catboost_artist_qcap_risk_strict_v1 | test | 607 | 0.136893 | 0.271395 | 0.808130 | -0.001911 | -0.001594 | 0.001764 | True |
| baseline_hcoef_stable | validation_oof | 519 | 0.125993 | 0.208206 | 0.647948 | 0.000000 | 0.000000 | 0.000000 | False |
| reference_current_70_30 | validation_oof | 519 | 0.130522 | 0.211028 | 0.658041 | 0.004530 | 0.002822 | 0.010093 | False |
| warm_catboost_artist_qcap_risk_strict_v1 | validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | -0.000070 | -0.001183 | -0.011353 | True |

## 3. 반복 검증 안정성

| model_id | mean_delta_MAPE | mean_delta_p95_APE | mean_MAPE_improve_rate | mean_p95_not_worse_rate | mean_strict_all3_rate | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE | operational_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm_catboost_artist_qcap_risk_strict_v1 | -0.001171 | -0.003830 | 1.000000 | 0.650000 | 0.400000 | -0.001911 | -0.001594 | 0.001764 | True |

## 4. Guard 적용 전 seed 성능

| model_id | mean_delta_MAPE | mean_delta_p95_APE | mean_MAPE_improve_rate | mean_p95_not_worse_rate | mean_all3_improve_rate | test_delta_MdAPE | test_delta_MAPE | test_delta_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unguarded_seed_before_risk_strict_guard | -0.002730 | -0.002500 | 1.000000 | 0.583333 | 0.470833 | -0.000603 | -0.003516 | 0.003967 |

## 5. 예측값 요약

| model_id | eval_split | rows | mean_pred_price | median_pred_price | mean_abs_correction_log | p95_abs_correction_log |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_hcoef_stable | test | 607 | 8481120.526716 | 2973628.193062 | 0.000000 | 0.000000 |
| baseline_hcoef_stable | validation_oof | 519 | 7909417.583119 | 2979253.355991 | 0.000000 | 0.000000 |
| warm_catboost_artist_qcap_risk_strict_v1 | test | 607 | 8473533.378875 | 2971896.677880 | 0.006690 | 0.019949 |
| warm_catboost_artist_qcap_risk_strict_v1 | validation_oof | 519 | 7917350.639507 | 2993772.169515 | 0.006264 | 0.014770 |

## 6. 최종 예측 로직

| step | name | formula | description |
| --- | --- | --- | --- |
| 1 | 기준 로그가격 생성 | 기준로그가격 = HCOEF_안정기준로그가격 | Warm/HCOEF 계열에서 선택한 안정 기준가를 사용한다. 이 값은 최종 예측의 중심값이다. |
| 2 | CatBoost 잔차 보정 생성 | CatBoost보정 = clip(CatBoost원시잔차보정, -CatBoost동적상한, +CatBoost동적상한) | confidence_weighted CatBoost 잔차 모델을 사용한다. qcap_balanced cap 0.02이므로 quantile_width가 1.6 이하이면 상한 0.02, 1.6 초과이면 상한 0.01을 적용한다. |
| 3 | 작가 생년/세대 보정 생성 | 작가보정 = clip(Huber(작가생년/세대 잔차), -0.03, +0.03) * 0.75 | 작가 생년과 세대 구간 기반 Huber 보정이다. 게이트 없이 전체 구간에 적용하며 alpha 0.01, cap 0.03, strength 0.75 조건을 사용한다. 실제 적용은 Huber 잔차를 먼저 cap으로 제한한 뒤 strength를 곱한다. |
| 4 | 1차 합산 보정 | 1차보정 = clip(1.0 * CatBoost보정 + 0.5 * 작가보정, -0.025, +0.025) | 작품/신뢰도 기반 CatBoost 보정을 주 보정으로 쓰고, 작가 메타 보정은 절반 가중치로 보조한다. |
| 5 | 위험 구간 판정 | 고위험 = low_confidence OR quantile_width >= 1.65 OR component_spread >= 0.13 OR stable_gap >= 0.05 OR svc_group_n < 4 | 저신뢰, 넓은 가격구간, 모델 간 큰 불일치, 작은 유사작품 표본 수를 고위험으로 본다. |
| 6 | 중위험 구간 판정 | 중위험 = medium_confidence OR quantile_width >= 1.28 OR component_spread >= 0.08 OR stable_gap >= 0.025 OR svc_group_n < 8 | 고위험이 아니지만 불확실성이 있는 구간을 중위험으로 본다. 고위험 조건이 먼저 적용된다. |
| 7 | risk_strict 보정 축소 | 위험계수 = 0.15 if 고위험 else 0.55 if 중위험 else 0.90 | p95 악화를 줄이기 위해 불확실성이 클수록 보정값을 강하게 줄인다. |
| 8 | 최종 보정 | 최종보정 = clip(1차보정 * 위험계수, -0.020, +0.020) | 최종 로그 보정값은 절대값 0.02 이내로 제한한다. |
| 9 | 최종 가격 산출 | 최종로그가격 = 기준로그가격 + 최종보정; 최종KRW가격 = exp(최종로그가격) | 로그공간에서 보정 후 원화 가격으로 변환한다. |

## 7. 핵심 수식

```text
CatBoost보정 = clip(CatBoost원시잔차보정, -CatBoost동적상한, +CatBoost동적상한)

작가보정 = clip(Huber(작가생년/세대 잔차), -0.03, +0.03) * 0.75

1차보정 = clip(1.0 * CatBoost보정 + 0.5 * 작가보정, -0.025, +0.025)

고위험 = low_confidence
      OR quantile_width >= 1.65
      OR component_prediction_spread >= 0.13
      OR current_vs_stable_gap_abs >= 0.05
      OR svc_group_n < 4

중위험 = medium_confidence
      OR quantile_width >= 1.28
      OR component_prediction_spread >= 0.08
      OR current_vs_stable_gap_abs >= 0.025
      OR svc_group_n < 8

위험계수 = 0.15 if 고위험 else 0.55 if 중위험 else 0.90

최종보정 = clip(1차보정 * 위험계수, -0.020, +0.020)

최종로그가격 = 기준로그가격 + 최종보정

최종KRW가격 = exp(최종로그가격)
```

## 8. 재현 실행

```bash
python3 scripts/track6/run_pp_opt7_warm_final_operational_freeze.py
```

## 9. 산출물

- `outputs/final_candidate_predictions.csv`
- `outputs/final_candidate_metrics.csv`
- `outputs/final_candidate_stability.csv`
- `outputs/final_logic_steps.csv`
- `outputs/final_prediction_summary.csv`
- `reports/final_model_report.md`
- `reports/final_model_report.html`
- `artifacts/final_model_config.json`
