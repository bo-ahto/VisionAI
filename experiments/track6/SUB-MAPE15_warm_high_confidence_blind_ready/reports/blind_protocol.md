# Blind Test 대비 프로토콜

## 목적

내부 test 100건 제출 실험을 넘어, 시험기관이 별도 blind candidate pool을 제공하는 경우에도 같은 모델과 같은 고신뢰 조건을 그대로 적용할 수 있도록 준비한다.

## 고정 사항

- 모델: `warm_high_confidence_residual_huber_rowid_dedup`
- 기준가: `hcoef_stable`
- residual 보정폭: `[-0.01, +0.01]` log
- 고신뢰 rule:
  - `quantile_width <= 1.20`
  - `component_prediction_spread <= 0.10`
  - `l10_price_range_ratio <= 2.00`
  - `svc_group_n >= 5`
  - `abs(current_70_30 - hcoef_stable) <= 0.025`

## Blind 평가 절차

1. 시험기관 또는 내부 운영 pipeline이 blind candidate pool을 준비한다.
2. 정답 가격 없이 component prediction과 quantile/range 피처만 CSV로 만든다.
3. `predict_blind_high_confidence.py`를 실행한다.
4. 스크립트가 고신뢰 조건을 만족하는 row를 골라 feature-only risk score가 낮은 순서로 100건을 고정한다.
5. 고정 모델로 `final_price_log`, `final_price`를 출력한다.
6. label이 나중에 제공되면 `evaluate_blind_predictions.py`로 MAPE를 계산한다.

## 내부 Smoke 검증

내부 test split 전체 candidate pool을 label 없는 blind 입력처럼 사용해 스크립트 동작을 확인한다. 이 검증은 이미 기존 test 100건 제출 결과와 같은 row를 재현하는 smoke test이며, 신규 성능 주장으로 쓰지 않는다.

Smoke 검증 결과:

| 항목 | 값 |
| --- | ---: |
| 입력 candidate pool | 607건 |
| 고신뢰 eligible | 100건 |
| 최종 선택 | 100건 |
| MdAPE | 0.0994 |
| MAPE | 0.1260 |
| p95_APE | 0.3118 |
| RMSE_log | 0.1663 |
| within_30 | 0.9400 |

생성 파일:

- `data/internal_blind_smoke_candidate_pool_features.csv`
- `data/internal_blind_smoke_candidate_pool_labels.csv`
- `outputs/internal_blind_smoke_predictions.csv`
- `outputs/internal_blind_smoke_metrics.csv`

## 제출 문구

권장 표현:

> 본 모델은 Warm/HCOEF 가격예측 모델 중 고신뢰 조건을 만족하는 candidate pool에서 100건을 사전 고정하여 평가한다. 고신뢰 조건은 정답 가격을 사용하지 않고, 예측 범위 폭, 모델 컴포넌트 간 agreement, 유사작품 표본 수만으로 결정한다.

피해야 할 표현:

> 모든 작품 가격예측에서 MAPE 15% 이하를 보장한다.
