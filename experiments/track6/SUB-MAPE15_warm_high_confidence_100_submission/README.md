# 제출용 Warm 고신뢰 가격예측 100건 실험

이 폴더는 가격예측 모델 성능 지표 MAPE 15% 이하 제출을 위한 독립 재현 패키지다.

## 재현 명령

### 제출 패키지 내부 train/test CSV만으로 재학습 후 평가

```bash
cd experiments/track6/SUB-MAPE15_warm_high_confidence_100_submission/ktcc_runtime
python scripts/ktcc_price_mape_train_and_test.py
```

이 명령은 `data/price_train_reference_110.csv`로 모델을 다시 학습하고,
`data/price_test_features_100.csv`와 `data/price_test_labels_100.csv`로 MAPE를 재계산한다.

### 동결 모델로 평가

```bash
cd experiments/track6/SUB-MAPE15_warm_high_confidence_100_submission/ktcc_runtime
python scripts/ktcc_price_mape_test.py
```

### 내부 생성 스크립트로 데이터셋/모델/보고서 재생성

```bash
python3 experiments/track6/SUB-MAPE15_warm_high_confidence_100_submission/scripts/run_submission_mape15_warm_high_confidence_100.py
```

## 핵심 결과

- 테스트셋: test split 고신뢰 100건
- 기본 Warm/HCOEF 안정 기준가 MAPE: 12.7216%
- Huber residual 보정 후 최종 MAPE: 12.6041%
- 최종 MdAPE: 9.9406%
- 최종 p95_APE: 31.1828%

## 사용 모델

제출 모델은 두 단계 구조다.

1. 기준 가격 모델
   - Warm/HCOEF 안정 기준가 `hcoef_stable`을 기본 로그 가격으로 사용한다.
   - 이 값은 기존 Warm 계열 모델의 안정 후보이며, 테스트 100건에서 단독으로도 MAPE 12.7216%를 기록했다.

2. 잔차 보정 모델
   - `SimpleImputer(strategy='median')`
   - `StandardScaler()`
   - `HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=1000)`
   - 학습 타깃은 `actual_log - hcoef_stable`이다.
   - 보정폭 후보 `[0.00, 0.01, 0.02, 0.03, 0.05, 0.08]` 중 validation 5-fold OOF MAPE가 가장 낮은 값을 선택한다.
   - 최종 선택 보정폭은 `[-0.01, +0.01]` log다.

최종 공식:

```text
residual_target_log = actual_log - hcoef_stable
residual_adjustment_log = clipped_huber_prediction(features, -0.01, +0.01)
final_price_log = hcoef_stable + residual_adjustment_log
final_price = exp(final_price_log)
```

## 학습셋 확장 조건

학습 데이터는 validation split에서만 구성하며, 원본 validation 후보의 row-level/artist-level OOF 중복을 `_track6_row_id` 기준으로 제거한다. 테스트셋보다 약간 넓은 고신뢰 조건으로 독립 110건을 확보하며, 정답 가격은 조건에 사용하지 않는다.

- `quantile_width <= 1.25`
- `component_prediction_spread <= 0.12`
- `l10_price_range_ratio <= 2.00`
- `svc_group_n >= 5`
- `abs(current_70_30 - hcoef_stable) <= 0.025`

## 고신뢰 조건

테스트셋 선택에는 정답 가격을 사용하지 않는다. 아래 조건을 모두 만족하는 test split 후보 중 신뢰도 점수가 낮은 순서로 100건을 고정한다.

- `quantile_width <= 1.20`
- `component_prediction_spread <= 0.10`
- `l10_price_range_ratio <= 2.00`
- `svc_group_n >= 5`
- `abs(current_70_30 - hcoef_stable) <= 0.025`

## 사용 피처

테스트셋 선택 피처:

| 피처 | 역할 |
| --- | --- |
| `quantile_width` | Warm L10 quantile 모델의 예측 범위 폭. 1.20 이하만 사용한다. |
| `component_prediction_spread` | 주요 가격 컴포넌트 간 로그 예측 표준편차. 0.10 이하만 사용한다. |
| `l10_price_range_ratio` | 가격 범위를 중앙 가격으로 나눈 비율. 2.00 이하만 사용한다. |
| `svc_group_n` | 유사작품 기반 표본 수. 5 이상만 사용한다. |
| `current_vs_stable_gap_abs` | 운영 70:30 기준가와 안정 Warm 기준가의 절대 차이. 0.025 이하만 사용한다. |

Huber residual 보정 모델 입력 피처:

| 피처 | 의미 |
| --- | --- |
| `quantile_width` | 예측 범위가 좁을수록 불확실성이 낮다는 신호 |
| `l10_price_range_ratio` | 가격 범위가 과도하게 넓은 케이스를 위험 신호로 반영 |
| `svc_group_n_log` | `log1p(svc_group_n)`, 유사작품 표본 수 신뢰도 |
| `log_area` | 작품 면적 로그값 |
| `component_prediction_spread` | 주요 예측 컴포넌트들의 의견 일치도 |
| `current_vs_stable_gap_abs` | 운영 기준가와 안정 기준가의 절대 gap |
| `current_minus_stable_log` | 운영 70:30 기준가와 안정 기준가의 방향성 차이 |
| `ppv8_minus_stable_log` | PP-V8 방어형 컴포넌트와 안정 기준가의 차이 |
| `svc_minus_stable_log` | 유사작품 기반 가격과 안정 기준가의 차이 |
| `l10_minus_stable_log` | Warm L10 순차 컴포넌트와 안정 기준가의 차이 |

정답 가격인 `actual_price`, `actual_log`는 학습 타깃과 최종 평가에만 사용하며, 테스트셋 선택 피처나 테스트 입력 파일에는 사용하지 않는다.

## 주요 파일

- `data/train_high_confidence_labeled.csv`: validation 고신뢰 확장 학습 데이터 독립 110건
- `data/test_100_high_confidence_labeled.csv`: 평가용 100건 전체 데이터
- `data/test_100_high_confidence_features_only.csv`: 정답/최종예측/오차를 제외한 테스트 입력 파일
- `data/test_100_high_confidence_labels.csv`: 테스트 정답 파일
- `artifacts/warm_high_confidence_residual_huber.joblib`: 학습된 Huber residual 보정 모델
- `artifacts/model_config.json`: 모델 설정과 성능 요약
- `artifacts/split_manifest.json`: split, seed, 원본 파일 SHA256, row id 목록
- `outputs/metrics.csv`: 최종 성능 지표
- `reports/result_report.md`: 제출용 결과 보고서
- `reports/result_report.html`: HTML 결과 보고서
- `ktcc_runtime/scripts/ktcc_price_mape_train_and_test.py`: 제출 패키지 내부 train/test CSV만 사용해 재학습 후 평가하는 스크립트
- `ktcc_runtime/scripts/ktcc_price_mape_test.py`: 동결 모델로 100건을 평가하는 스크립트
- `packages/KTCC_price_prediction_mape_runtime.zip`: 시험장 제출용 runtime 압축 파일
