# T6-E004 Cold 모델 비교

- 날짜: `2026-05-18`
- 관련 가설: `T6-H4`
- 상태: 검증 완료
- 목적: Cold에서 robust 계열과 트리 계열 중 어떤 방식이 안정적인지 확인
- 사용 데이터: Track6 name-corrected Cold feature/label split
- 사용 스크립트: `scripts/track6/run_t6_e004_cold_model_compare.py`
- 결과 JSON: `data/track6/results/t6_e004_cold_model_compare.json`
- 예측 CSV: `data/track6/predictions/t6_e004_cold_model_compare_predictions.csv`

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

## 2. validation 결과

| model | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |
|---|---:|---:|---:|---:|---:|
| `hist_quantile_ordinal` | `0.3903` | `1.8895` | `0.3903` | `0.6151` | `0.6795` |
| `lightgbm_basic` | `0.4029` | `1.9981` | `0.3767` | `0.5879` | `0.6843` |
| `huber_onehot` | `0.4052` | `1.4674` | `0.3938` | `0.6169` | `0.6671` |
| `catboost_basic` | `0.4058` | `1.7653` | `0.3752` | `0.5897` | `0.6665` |
| `xgboost_basic` | `0.4230` | `1.9331` | `0.3831` | `0.5678` | `0.6847` |
| `ridge_onehot` | `0.4693` | `1.8339` | `0.3423` | `0.5199` | `0.6755` |

## 3. 핵심 해석

- median APE 최저: `0.3903` (`hist_quantile_ordinal`)
- p95 APE 최저: `1.4674` (`huber_onehot`)
- median 기준과 p95 기준이 다르면 대표 오차와 큰 오차 위험을 분리해서 판단
- Cold는 작가 피처를 쓰지 않으므로 구조 피처 기반 일반화 성능이 핵심

## 4. 결론

- T6-H4는 validation 기준 검증 완료
- Cold 대표 오차 기준 후보는 `hist_quantile_ordinal`
- Cold 큰 오차 위험 보조 기준 후보는 `huber_onehot`
- 다음 단계는 피처 조합 실험(T6-E005)
