# T6-E005 피처 조합 ablation

- 날짜: `2026-05-29`
- 관련 가설: `T6-H5`
- 상태: 검증 완료
- 목적: 운영에서 만들 수 있는 크기/재료/지지체 조합 피처가 Warm/Cold 성능을 개선하는지 확인
- 사용 데이터: Track6 name-corrected feature/label split
- 사용 스크립트: `scripts/track6/run_t6_e005_feature_combo_ablation.py`
- 결과 JSON: `data/track6/results/t6_e005_feature_combo_ablation.json`
- 예측 CSV: `data/track6/predictions/t6_e005_feature_combo_ablation_predictions.csv`

## 1. 실험 방법

- Warm: `Huber + artist_key one-hot` 구조를 고정하고 피처 조합만 변경
- Cold: `CatBoost`와 `LightGBM`을 사용해 대표 오차와 큰 오차를 같이 확인
- size bucket은 train 기준 `log_area` 분위수로 만들고 validation에는 같은 기준을 적용
- 정답 가격은 feature 생성에 사용하지 않고 평가 단계에서만 label 파일을 결합

## 2. validation 결과

| split | model | feature set | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |
|---|---|---|---:|---:|---:|---:|---:|
| `val_cold` | `lightgbm_cold` | `base_support_size` | `0.3848` | `2.0207` | `0.3603` | `0.5979` | `0.6873` |
| `val_cold` | `lightgbm_cold` | `base_existing_combo` | `0.3861` | `1.9909` | `0.3560` | `0.5975` | `0.6912` |
| `val_cold` | `lightgbm_cold` | `all_operational_combos` | `0.3910` | `2.0164` | `0.3454` | `0.6055` | `0.6925` |
| `val_cold` | `lightgbm_cold` | `base` | `0.3911` | `2.0401` | `0.3767` | `0.5975` | `0.6910` |
| `val_cold` | `lightgbm_cold` | `base_large_flags` | `0.3938` | `1.9783` | `0.3698` | `0.5946` | `0.6916` |
| `val_cold` | `lightgbm_cold` | `base_size_shape` | `0.3939` | `1.9831` | `0.3992` | `0.5972` | `0.6886` |
| `val_cold` | `lightgbm_cold` | `base_medium_size` | `0.3952` | `2.0032` | `0.3905` | `0.6062` | `0.6867` |
| `val_cold` | `lightgbm_cold` | `base_medium_shape` | `0.3973` | `2.0014` | `0.3861` | `0.5957` | `0.6891` |
| `val_cold` | `catboost_cold` | `base_medium_shape` | `0.4251` | `2.4420` | `0.3364` | `0.5547` | `0.7133` |
| `val_cold` | `catboost_cold` | `base_existing_combo` | `0.4266` | `2.3177` | `0.3444` | `0.5561` | `0.7100` |
| `val_cold` | `catboost_cold` | `base_support_size` | `0.4282` | `2.3586` | `0.3385` | `0.5601` | `0.7099` |
| `val_cold` | `catboost_cold` | `base_medium_size` | `0.4287` | `2.2506` | `0.3447` | `0.5598` | `0.7071` |
| `val_cold` | `catboost_cold` | `base_large_flags` | `0.4321` | `2.3452` | `0.3418` | `0.5561` | `0.7102` |
| `val_cold` | `catboost_cold` | `base_size_shape` | `0.4328` | `2.4044` | `0.3338` | `0.5539` | `0.7166` |
| `val_cold` | `catboost_cold` | `base` | `0.4368` | `2.3984` | `0.3255` | `0.5536` | `0.7152` |
| `val_cold` | `catboost_cold` | `all_operational_combos` | `0.4375` | `2.3636` | `0.3400` | `0.5532` | `0.7138` |
| `val_warm` | `huber_warm_artist` | `base_existing_combo` | `0.2126` | `1.3194` | `0.5954` | `0.7322` | `0.6446` |
| `val_warm` | `huber_warm_artist` | `base_large_flags` | `0.2171` | `1.3576` | `0.5954` | `0.7380` | `0.6512` |
| `val_warm` | `huber_warm_artist` | `base` | `0.2180` | `1.3353` | `0.5877` | `0.7322` | `0.6519` |
| `val_warm` | `huber_warm_artist` | `base_support_size` | `0.2192` | `1.3271` | `0.6050` | `0.7399` | `0.6488` |
| `val_warm` | `huber_warm_artist` | `all_operational_combos` | `0.2202` | `1.3483` | `0.6012` | `0.7341` | `0.6395` |
| `val_warm` | `huber_warm_artist` | `base_size_shape` | `0.2210` | `1.3866` | `0.5934` | `0.7341` | `0.6519` |
| `val_warm` | `huber_warm_artist` | `base_medium_size` | `0.2228` | `1.5188` | `0.5934` | `0.7303` | `0.6475` |
| `val_warm` | `huber_warm_artist` | `base_medium_shape` | `0.2259` | `1.4534` | `0.5819` | `0.7322` | `0.6564` |

## 3. 핵심 해석

- Warm 최저 median APE: `0.2126` (`base_existing_combo`)
- Cold 최저 median APE: `0.3848` (`lightgbm_cold`, `base_support_size`)
- Cold 최저 p95 APE: `1.9783` (`lightgbm_cold`, `base_large_flags`)
- Warm과 Cold에서 같은 조합 피처가 항상 같은 방향으로 작동하지 않으므로 모델별 피처셋 분리 관리가 필요

## 4. 결론

- T6-H5는 validation 기준 검증 완료
- 피처 조합은 후보 선정에 포함하되, Warm/Cold 최종 피처셋은 별도로 고정해야 함
- 다음 단계는 validation 기준 최종 후보 선정(T6-E006)
