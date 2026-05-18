# T6-E002 구조-only baseline

- 날짜: `2026-05-18`
- 관련 가설: `T6-H2`
- 상태: 검증 완료
- 목적: 작가 피처 없이 작품 구조 정보만으로 기본 예측 가능성 확인
- 사용 데이터: Track6 name-corrected feature/label split
- 사용 스크립트: `scripts/track6/run_t6_e002_structure_baseline.py`
- 결과 JSON: `data/track6/results/t6_e002_structure_only_baseline.json`
- 예측 CSV: `data/track6/predictions/t6_e002_structure_only_baseline_predictions.csv`

## 1. 사용 피처

- `width_cm`
- `height_cm`
- `depth_cm`
- `area_cm2`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`
- `medium_category`
- `support_category`
- `medium_support_bucket`
- `is_extreme_aspect_ratio`

## 2. 비교 모델

- `log_median_dummy`: train 로그가격 중앙값 예측
- `ridge_onehot`: one-hot + Ridge
- `huber_onehot`: one-hot + Huber robust regression
- `hist_gbdt_ordinal`: ordinal category + 기본 histogram GBDT
- `lightgbm_basic`: ordinal category + 기본 LightGBM

## 3. validation 결과

| split | model | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |
|---|---|---:|---:|---:|---:|---:|
| `val_cold` | `lightgbm_basic` | `0.4029` | `1.9981` | `0.3767` | `0.5879` | `0.6843` |
| `val_cold` | `huber_onehot` | `0.4037` | `1.4788` | `0.3953` | `0.6158` | `0.6657` |
| `val_cold` | `hist_gbdt_ordinal` | `0.4168` | `2.0140` | `0.3827` | `0.5918` | `0.6772` |
| `val_cold` | `ridge_onehot` | `0.4693` | `1.8339` | `0.3423` | `0.5199` | `0.6755` |
| `val_cold` | `log_median_dummy` | `0.9156` | `8.1951` | `0.1436` | `0.2732` | `1.3308` |
| `val_warm` | `hist_gbdt_ordinal` | `0.4579` | `2.3857` | `0.3270` | `0.5220` | `0.8486` |
| `val_warm` | `lightgbm_basic` | `0.4622` | `2.1337` | `0.3327` | `0.5315` | `0.8449` |
| `val_warm` | `huber_onehot` | `0.4702` | `1.8289` | `0.3250` | `0.5430` | `0.8819` |
| `val_warm` | `ridge_onehot` | `0.5451` | `2.2425` | `0.2753` | `0.4608` | `0.8895` |
| `val_warm` | `log_median_dummy` | `0.7701` | `7.0520` | `0.1759` | `0.3117` | `1.3428` |

## 4. 핵심 해석

- Warm 최저 median APE: `0.4579` (`hist_gbdt_ordinal`)
- Cold 최저 median APE: `0.4029` (`lightgbm_basic`)
- 중앙값 baseline보다 구조 피처 모델이 Warm/Cold 모두 개선되면 구조 정보 기반 예측 가능성이 있다고 판단
- 이 실험은 작가 피처를 넣기 전 기준점이므로, 이후 T6-E003/T6-E004의 비교 기준으로 사용

## 5. 결론

- T6-H2는 validation 기준 검증 완료
- Warm 구조-only 기준 후보: `hist_gbdt_ordinal`
- Cold 구조-only 기준 후보: `lightgbm_basic`
- 다음 단계는 Warm 작가 피처 ablation(T6-E003)과 Cold 모델 비교(T6-E004)
