# PP-A1-W Warm Huber 전체 예측 오차 보정 실험 계획서

- 작성일: `2026-05-29`
- 실험 ID: `PP-A1-W`
- 실험명: Warm Huber 전체 median residual 보정
- 대상 모델: `Warm Huber`
- 대상 피처셋: `base_existing_combo` + Warm 작가 식별 피처 `artist_key`
- 실험 목적: Warm Huber 모델의 전체 예측 치우침을 확인하고, 검증 데이터에서 산출한 전역 residual 보정값이 테스트 데이터에서도 성능을 안정적으로 개선하는지 검증한다.

## 1. 실험 배경

- 본 실험은 후처리 실험군 `PP-A1`의 Warm 세부 실험으로 진행한다.
- `PP-A1`은 모델 예측값이 전체적으로 과대 또는 과소 예측되는지 확인하는 실험이다.
- Warm 모델은 최종 기준 모델을 `Huber`로 고정한다.
- Cold 모델은 CatBoost와 LightGBM을 별도 실험으로 분리한다.
- Warm Huber는 선형 회귀 기반의 robust 모델이다.
- 따라서 leaf 기반 세부 보정보다, 먼저 전체 residual bias를 하나의 값으로 보정하는 방식이 적합하다.
- 본 실험은 PP-A1의 기준 실험으로 두며, 가격대별/구간별 보정은 PP-A2 이후 실험에서 별도 검증한다.

## 2. 이전 실험에서 확인된 근거

- `T6-E005`에서 Warm 후보 모델과 피처 조합을 비교했다.
- `T6-E006`에서 Warm Huber 기준 후보를 `huber_warm_artist__base_existing_combo`로 선정했다.
- `T6-E007`에서 동일 후보를 테스트 데이터에 적용해 기준 성능을 확인했다.
- `T6-PP residual calibration`에서 validation residual 기반 보정을 사전 실행했다.
- 사전 실행 결과, Warm Huber의 전체 median residual 보정은 테스트 성능을 소폭 개선했다.
- 따라서 PP-A1-W는 신규 피처 탐색 실험이 아니다.
- 본 실험은 이미 관찰된 전체 residual 보정 효과를 정식 후처리 후보로 검증하고 문서화하는 실험이다.

## 3. 기준 피처셋 정의

- Warm 기준 피처셋은 `base_existing_combo`로 고정한다.
- `base_existing_combo`는 작품의 기본 크기, 형태, 재료/지지체 범주, 기존 조합 피처를 포함한다.
- Warm Huber는 작가 이력이 있는 작가를 대상으로 한다.
- 실제 Warm 학습 입력에는 `base_existing_combo`에 `artist_key`를 추가한다.
- 본 실험의 실제 입력 피처는 아래와 같이 고정한다.

| 구분 | 사용 피처 |
|---|---|
| 기본 수치 피처 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` |
| 기본 범주 피처 | `has_depth`, `is_3d_candidate`, `medium_category`, `support_category` |
| 기존 조합 피처 | `medium_support_bucket`, `is_extreme_aspect_ratio` |
| Warm 작가 피처 | `artist_key` |

- 해당 피처셋은 후처리 전용 신규 피처셋이 아니다.
- 해당 피처셋은 기존 Warm 후보 선정 단계에서 성능이 가장 좋았던 기준 피처셋이다.
- `T6-E005` validation 결과에서 Warm Huber `base_existing_combo`는 Warm 후보 중 최저 MdAPE를 기록했다.
- `T6-E006`에서 해당 조합을 Warm 최종 후보로 선택했다.
- `T6-E007`에서 동일 조합으로 test confirmation을 진행했다.
- PP-A1-W에서는 위 피처 구성을 고정한다.
- PP-A1-W에서는 피처 변경 없이 보정값 적용 여부만 비교한다.

## 4. 실험에서 기대하는 값

- 기대 산출값은 Warm Huber의 전체 예측 치우침을 나타내는 하나의 로그 스케일 보정값이다.
- 해당 값을 `warm_global_correction`으로 정의한다.
- `warm_global_correction > 0`이면 Warm Huber가 validation에서 전체적으로 과소 예측한 것으로 해석한다.
- `warm_global_correction < 0`이면 Warm Huber가 validation에서 전체적으로 과대 예측한 것으로 해석한다.
- 보정 후 기대 방향은 MdAPE 개선이다.
- 보정 후 p95_APE와 RMSE_log는 악화되지 않아야 한다.
- 기대하는 개선은 큰 폭의 성능 향상이 아니라, 피처와 모델을 고정한 상태에서 남아 있는 전역 bias가 줄어드는지 확인하는 것이다.

## 5. 피처 및 실험 조건 통제

- 본 실험은 후처리 효과만 확인한다.
- 피처셋은 반드시 고정한다.
- Warm Huber 입력 피처는 `base_existing_combo + artist_key`로 고정한다.
- 피처 추가는 수행하지 않는다.
- 피처 제거는 수행하지 않는다.
- 피처 조합 변경은 수행하지 않는다.
- train / validation / test split은 기존 Track6 고정 split을 사용한다.
- Huber 모델 학습 설정은 기존 후보 선정 당시 설정을 유지한다.
- 실험 중 변경되는 값은 예측 후 적용하는 보정값뿐이다.

```text
고정: Warm 대상 데이터
고정: train / validation / test split
고정: Huber 모델
고정: base_existing_combo + artist_key 피처셋
고정: 모델 학습 설정
변경: pred_log에 warm_global_correction을 더하는지 여부
```

## 6. 모델 입력 전처리 기준

- 수치 피처는 결측값을 median으로 대체한다.
- 수치 피처는 결측 처리 후 `StandardScaler`로 표준화한다.
- 범주 피처는 결측값을 `__MISSING__`으로 대체한다.
- 범주 피처는 결측 처리 후 one-hot encoding을 적용한다.
- one-hot encoding에는 희소 범주 확장을 줄이기 위한 최소 빈도 기준을 적용한다.
- Huber 모델 설정은 기존 Warm 후보 선정 당시와 동일하게 유지한다.

```text
HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=3000)
```

- 이 전처리와 모델 설정을 고정해야 보정 전후 성능 차이를 후처리 효과로 해석할 수 있다.

## 7. 표준 보정식과 본 실험 적용식

- 본 실험은 회귀 모델에서 일반적으로 사용하는 residual bias correction 방식을 적용한다.
- 표준식은 아래와 같다.

```text
residual = actual - prediction
correction = median(residual)
corrected_prediction = prediction + correction
```

- `median(residual)`은 residual을 작은 값부터 큰 값까지 정렬했을 때 가운데에 있는 값, 즉 중앙값이다.
- 평균도 대표값으로 사용할 수 있지만, 가격 데이터는 큰 오차에 흔들릴 수 있으므로 본 실험에서는 중앙값을 우선 사용한다.
- 본 실험의 타깃은 가격 원값이 아니라 `log(price)`다.
- 따라서 표준식을 로그 스케일에 맞게 변환한다.

```text
residual_log = actual_log - pred_log
correction_log = median(residual_log)
corrected_pred_log = pred_log + correction_log
corrected_pred_price = exp(corrected_pred_log)
```

- Warm Huber 실험에서는 validation 전체의 로그 residual 중앙값을 전역 보정값으로 사용한다.

```text
warm_global_correction = median(actual_log - pred_log)
corrected_pred_log = pred_log + alpha * warm_global_correction
corrected_pred_price = exp(corrected_pred_log)
```

- 기본 실험에서는 `alpha = 1.0`을 사용한다.
- 안정성 확인 단계에서는 보정 강도 `alpha`를 함께 점검한다.

```text
alpha 후보 = {0.25, 0.5, 0.75, 1.0}
```

- median residual을 사용하는 이유는 극단 residual의 영향을 줄이기 위함이다.
- 미술품 가격 데이터에는 고가 작품, 희소 작가, 특이 매체로 인한 극단 residual이 존재할 수 있다.
- mean residual은 일부 극단값에 의해 보정값이 과하게 흔들릴 수 있다.
- Warm Huber의 전역 bias 확인에는 median residual이 더 안정적이다.
- `alpha = 1.0`에서 성능이 개선되더라도 특정 구간이 악화되면 `alpha < 1.0` 후보를 비교한다.

## 8. 보정 강도 및 안정성 기준

- 기본 채택 후보는 `alpha = 1.0`의 전체 median residual 보정이다.
- 단, 전역 보정은 모든 Warm 샘플에 동일한 값을 더하므로 일부 구간에서는 과보정이 발생할 수 있다.
- 따라서 보정 강도별 성능도 함께 확인한다.

| alpha | 의미 | 사용 목적 |
|---:|---|---|
| `0.25` | 보정값의 25%만 적용 | 과보정 위험이 큰 경우의 보수적 후보 |
| `0.50` | 보정값의 50%만 적용 | 중간 수준 보정 후보 |
| `0.75` | 보정값의 75%만 적용 | 기본 보정에 가까운 완화 후보 |
| `1.00` | 보정값 전체 적용 | 기본 PP-A1-W 후보 |

- `alpha = 1.0`이 MdAPE와 p95_APE를 모두 개선하면 기본 후보로 유지한다.
- `alpha = 1.0`이 MdAPE는 개선하지만 p95_APE 또는 특정 위험 구간을 악화시키면 `0.5` 또는 `0.75`를 후보로 비교한다.
- 모든 alpha에서 baseline보다 악화되면 PP-A1-W 보정은 적용하지 않는다.
- alpha 선택은 validation 성능 기준으로만 수행한다.
- test 데이터에는 validation에서 선택된 alpha를 고정 적용하고, 성능 확인만 수행한다.

## 9. 실험 절차

- 1단계: `base_existing_combo + artist_key`로 학습된 Warm Huber 모델의 validation 예측값을 생성한다.
- 2단계: validation에서 `actual_log - pred_log`를 계산해 `residual_log`를 생성한다.
- 3단계: validation 전체 `residual_log`의 중앙값을 계산해 `warm_global_correction`으로 저장한다.
- 4단계: validation에서 alpha 후보별 성능을 비교해 과보정 여부를 확인한다.
- 5단계: validation 기준으로 최종 alpha를 확정한다.
- 6단계: test 원본 예측값 `pred_log`에 확정된 `alpha * warm_global_correction`을 더해 `corrected_pred_log`를 생성한다.
- 7단계: `corrected_pred_log`를 가격 원 단위로 변환해 `corrected_pred_price`를 생성한다.
- 8단계: 보정 전 `pred_log` 기준 성능과 보정 후 `corrected_pred_log` 기준 성능을 비교한다.

## 10. 데이터 누수 방지 기준

- 보정값은 validation 데이터에서만 계산한다.
- test 데이터의 실제값은 보정값 계산에 사용하지 않는다.
- test 데이터는 보정식 고정 후 최종 확인 용도로만 사용한다.
- test 성능을 보고 `warm_global_correction`을 재조정하지 않는다.
- test 성능을 보고 alpha 후보를 새로 추가하지 않는다.

## 11. 평가 지표

- 주 지표: `MdAPE`
- 보조 지표: `p95_APE`, `RMSE_log`, `Within_30`, `Within_50`
- `MdAPE`는 일반적인 예측 오차의 중앙 수준을 확인하기 위해 사용한다.
- `p95_APE`는 큰 오차 위험이 악화되는지 확인하기 위해 사용한다.
- `RMSE_log`는 로그 스케일의 전체 오차가 악화되는지 확인하기 위해 사용한다.
- 추가 확인 지표: 주요 위험 구간별 MdAPE와 p95_APE
- 위험 구간은 아래 기준으로 고정한다.

| 위험 구간 | 기준 |
|---|---|
| 저이력 작가 | `artist_works_count_train` 하위 20% 또는 `artist_works_log` 하위 20% |
| 작은 작품 | `size_bucket = q1` 또는 `log_area` 하위 20% |
| 큰 작품 | `size_bucket = q5` 또는 `log_area` 상위 20% |
| 형태 위험 | `is_extreme_aspect_ratio = true` |
| 재료/지지체 위험 | validation 기준 p95_APE가 높은 `medium_category` / `support_category` 주요 구간 |

- 전역 보정은 전체 평균 성능이 좋아져도 특정 구간을 악화시킬 수 있으므로 구간별 악화 여부를 함께 확인한다.

## 12. 성공 및 보류 기준

- 채택 조건은 아래 채택 항목을 모두 만족하는 경우로 본다.

- 채택: 보정 후 MdAPE가 개선되고 p95_APE가 악화되지 않는 경우.
- 채택: RMSE_log가 기존 수준을 유지하는 경우.
- 채택: 주요 위험 구간 중 악화 구간 수가 개선 구간 수보다 많지 않은 경우.
- 보류: MdAPE가 개선되더라도 p95_APE가 크게 악화되는 경우.
- 보류: 전체 MdAPE는 개선되지만 주요 위험 구간의 p95_APE가 명확히 악화되는 경우.
- 중단: MdAPE가 baseline 대비 악화되는 경우.
- 후보 유지: 개선폭이 작더라도 p95_APE와 RMSE_log가 안정적으로 유지되는 경우.
- 미적용: 모든 alpha 후보에서 baseline 대비 개선이 없거나 위험 구간 악화가 큰 경우.

## 13. 현재 실행 결과 참고

- 결과 출처: `T6-PP residual calibration` 사전 실행 결과
- 실행 스크립트: `scripts/track6/run_t6_pp_residual_calibration.py`
- 결과 파일: `data/track6/results/t6_pp_residual_calibration_metrics.csv`
- 보정 규칙 파일: `data/track6/results/t6_pp_residual_calibration_rules.csv`
- 기준 모델: `huber_warm_artist`
- 기준 피처셋: `base_existing_combo + artist_key`
- 비교 방식: test baseline `pred_log`와 validation median residual 보정 후 `corrected_pred_log` 비교

- 기준 성능은 Warm Huber `huber_warm_artist__base_existing_combo`의 test baseline 결과다.
- 보정 후 성능은 validation에서 계산한 전체 median residual 보정값을 test 예측값에 고정 적용한 결과다.

| 구분 | method | MdAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|
| 보정 전 | `baseline` | `0.2274` | `2.0130` | `0.6081` |
| 보정 후 | `overall_median_residual` | `0.2221` | `1.9859` | `0.6080` |

- 현재 결과 기준으로 PP-A1-W는 Warm Huber에 적용 가능한 후처리 후보로 판단한다.
- MdAPE는 `0.2274`에서 `0.2221`로 개선됐다.
- p95_APE는 `2.0130`에서 `1.9859`로 개선됐다.
- RMSE_log는 `0.6081`에서 `0.6080`으로 거의 유지됐다.
- 전체 median residual 보정은 일반 오차와 큰 오차 위험을 동시에 해치지 않았다.
- 현재 실행 결과는 `alpha = 1.0` 기준이다.
- 최종 적용 전에는 주요 위험 구간에서 악화가 없는지 추가 확인한다.

## 14. 해석 시 주의점

- 본 결과는 `base_existing_combo + artist_key`를 사용한 현재 Warm Huber 설정에 한정된다.
- 피처셋을 변경하면 residual 분포도 달라진다.
- 피처셋 변경 시 `warm_global_correction`은 재계산해야 한다.
- 본 실험은 전체 보정만 검증한다.
- 본 실험은 가격대별 또는 예측 구간별 보정 효과까지 설명하지 않는다.
- 현재 Warm에서는 `pred_bin_median_residual`도 별도로 좋은 결과를 보였다.
- 단, `pred_bin_median_residual`은 PP-A1-W가 아니라 예측 구간별 보정 실험으로 분리 판단한다.
- PP-A1-W가 채택 기준을 충족하지 못하면 Warm Huber는 baseline 예측을 유지한다.
- PP-A1-W가 채택되더라도 PP-A2 이후 구간별 보정이 더 안정적이면 최종 후처리에서는 PP-A2 후보와 비교해 결정한다.

## 15. 실패 시 판단 기준

- PP-A1-W가 채택 기준을 충족하지 못하면 전체 residual 보정은 적용하지 않는다.
- 이 경우 Warm Huber baseline 예측을 유지한다.
- 전체 보정이 실패하더라도 특정 구간에서 반복 오차가 남아 있으면 PP-A2, PP-A3, PP-A5에서 구간별 보정을 별도로 검토한다.
- 전체 보정과 구간별 보정이 모두 후보가 되는 경우, 최종 적용은 validation 기준으로 정하고 test에는 고정 적용한다.

## 16. 결론

- PP-A1-W는 Warm Huber의 전역 residual bias를 하나의 median correction으로 보정하는 실험이다.
- 보정값은 validation 데이터에서만 계산한다.
- test 데이터에는 고정된 보정값만 적용한다.
- 피처셋과 모델을 고정하므로, 보정 전후 성능 차이는 후처리 효과로 해석할 수 있다.
- 현재 사전 실행 결과에서는 MdAPE, p95_APE, RMSE_log가 모두 악화되지 않았다.
- 따라서 PP-A1-W는 Warm Huber의 기본 후처리 후보로 유지할 근거가 있다.
- 단, 최종 채택 전에는 alpha별 안정성과 주요 위험 구간 악화 여부를 확인한다.
- 다음 단계에서는 PP-A1-W를 기준 실험으로 두고, Warm 예측 구간별 보정 실험과 비교해 최종 적용 방식을 결정한다.
