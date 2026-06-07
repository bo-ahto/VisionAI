# Track6 가격 예측 정확도 실험 결과 종합 보고서

- 작성일: 2026-06-02
- 대상: Track6 Warm / Cold 가격 예측 모델 및 후처리 실험
- 기준 문서:
  - `experiments/track6/postprocessing_execution_progress.md`
  - `docs/track6/experiments/postprocessing_experiment_matrix.md`
  - `docs/track6/experiments/track6_feature_influence_with_results.md`
  - `docs/track6/experiments/model_structure_based_interpretation_report.md`
  - `docs/track6/experiments/pp_u_feature_swap_execution_summary.md`
- 핵심 기준: 가격 예측 정확도를 `MdAPE`, `MAPE`, `p95_APE`, `RMSE_log`, `Within_30`, `Within_50`로 평가한다.

## 1. 결론 요약

### 1.1 최종 판단

| 구분 | 권장 후보 | test MdAPE | test MAPE | test p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| Warm 대표 점 예측 | `PP-T1 fine_blend_mape_guarded` | `0.1621` | `0.3044` | `1.0335` | 대표 정확도와 평균 오차 균형이 가장 좋음 |
| Warm 큰 오차 방어 | `PP-T1 fine_blend_mdape` 또는 `PP-T2 huber_crossfit_component_range_clipped` | `0.1668` / `0.1705` | `0.3067` / `0.2916` | `0.9580` / `0.9582` | p95와 MAPE 방어가 강함 |
| Cold 대표 점 예측 | `PP-S1 n2_catboost_quantile_huber_cap0.2_s1` | `0.4744` | `1.2095` | `3.4731` | Cold MdAPE 최저 후보 |
| Cold 큰 오차 방어 | `PP-S1 n2_catboost_quantile_huber_cap0.5_s1` 또는 `PP-S4 huber_crossfit_component_range_clipped` | `0.4765` / `0.4765` | `1.2067` / `1.2079` | `3.2824` / `3.2827` | p95 방어와 안정성 균형이 가장 좋음 |
| Cold MAPE 최적화 | `PP-Q2 weighted_blend_mape_objective` | `0.4811` | `1.1797` | `3.7925` | 평균 오차 감소 목적에는 가장 강함 |
| Cold 가격 범위/신뢰도 | `PP-N3 90% conformal range` | 점 예측 후보 아님 | 점 예측 후보 아님 | 범위 정책 | test coverage `0.8061`, 범위비 중앙값 `8.38배` |

### 1.2 정확도 개선폭

Warm 기준 모델은 `Warm Huber(base_existing_combo)`이고, Cold 기준 모델은 현재 test 기준으로 가장 안정적인 `Cold LightGBM(base_support_size)`를 사용했다.

| 구분 | 기준 후보 | 최종 후보 | MdAPE 개선 | MAPE 개선 | p95_APE 개선 |
|---|---|---|---:|---:|---:|
| Warm 대표 점 예측 | Warm Huber `0.2274 / 0.4952 / 2.0130` | PP-T1 mape `0.1621 / 0.3044 / 1.0335` | `28.7%` | `38.5%` | `48.7%` |
| Warm p95 방어 | Warm Huber `0.2274 / 0.4952 / 2.0130` | PP-T1 mdape `0.1668 / 0.3067 / 0.9580` | `26.7%` | `38.1%` | `52.4%` |
| Cold 대표 점 예측 | Cold LightGBM `0.4909 / 1.4131 / 4.8212` | PP-S1 cap0.2 `0.4744 / 1.2095 / 3.4731` | `3.4%` | `14.4%` | `28.0%` |
| Cold p95 방어 | Cold LightGBM `0.4909 / 1.4131 / 4.8212` | PP-S1 cap0.5 `0.4765 / 1.2067 / 3.2824` | `2.9%` | `14.6%` | `31.9%` |
| Cold MAPE 최적화 | Cold LightGBM `0.4909 / 1.4131 / 4.8212` | PP-Q2 MAPE blend `0.4811 / 1.1797 / 3.7925` | `2.0%` | `16.5%` | `21.3%` |

결론적으로 Warm은 모델 조합과 후처리로 대표 정확도와 큰 오차가 모두 크게 개선됐다. Cold는 개선폭이 Warm보다 작지만, CatBoost Quantile, Huber residual, meta stacking을 조합하면 p95와 MAPE는 뚜렷하게 줄일 수 있다.

## 2. 평가 지표 해석

| 지표 | 의미 | 이번 보고서에서의 사용 방식 |
|---|---|---|
| `MdAPE` | 예측 오차율의 중앙값 | 일반적인 대표 정확도 판단 기준 |
| `MAPE` | 예측 오차율의 평균 | 큰 오차까지 포함한 평균 체감 오차 |
| `p95_APE` | 오차 상위 5% 지점 | 크게 틀리는 위험, 서비스 신뢰도 판단 기준 |
| `RMSE_log` | 로그 가격 기준 평균 제곱 오차 | 전체 로그 가격 적합도 |
| `Within_30` | 실제 가격 대비 30% 이내 예측 비율 | 실무적으로 “가까운 예측” 비율 |
| `Within_50` | 실제 가격 대비 50% 이내 예측 비율 | 넓은 허용 범위 내 예측 비율 |

이 프로젝트에서는 `MdAPE`만 낮추는 후보를 바로 채택하지 않았다. 가격 예측 서비스에서는 대표 정확도도 중요하지만, p95처럼 크게 틀리는 위험이 사용자 신뢰도에 직접 영향을 주기 때문이다. 따라서 최종 후보는 `MdAPE`, `MAPE`, `p95_APE`의 균형으로 판단했다.

## 3. Warm 모델 결과와 원인 분석

### 3.1 Warm 기준 모델의 특성

Warm은 학습 데이터 안에 같은 작가의 작품 이력이 있는 경우다. 따라서 가격 예측에서 가장 중요한 축은 “작가 기준 가격대”와 “작품 크기”다.

Warm Huber의 기본 예측 구조는 다음과 같다.

```text
pred_log_price
= intercept
+ 작가 기준선 효과
+ 크기 효과
+ 깊이/입체 효과
+ 형태 효과
+ 재료/지지체 효과

pred_price = exp(pred_log_price)
```

Huber는 선형 모델이지만, 큰 오차 샘플의 학습 영향력을 낮추는 손실 함수를 사용한다. 그래서 Warm처럼 작가 이력이 있고 일부 고가/저가 이상치가 섞인 데이터에서 기준선 모델로 안정적이다.

### 3.2 Warm 피처 근거

| 피처 축 | 실험 근거 | 해석 |
|---|---|---|
| 작가 정보 | Warm group-drop에서 작가 제거 시 MdAPE가 약 `0.48~0.49`로 악화 | Warm 가격 예측은 작가 기준선이 없으면 급격히 약해짐 |
| 크기 정보 | `PRE-PP-W`에서 size 제거 시 MdAPE `0.2126 -> 0.5671` | 작품 크기는 작가 기준선 다음으로 핵심 가격 축 |
| 재료/지지체 | 일부 Warm 후보에서 제거해도 성능 유지 또는 소폭 개선 | Warm에서는 재료/지지체가 핵심축이라기보다 보조 또는 노이즈 가능성 |
| depth/aspect | 제거 영향이 작거나 test에서 후보별 방향이 다름 | 단독 핵심 피처가 아니라 크기/작가와 함께 볼 때만 의미 |
| 생성 bucket | `PP-U1`에서 `full_plus_generated_buckets` test MdAPE `0.2274 -> 0.2131` | 선형 Huber가 직접 표현하지 못한 구간 효과를 보완할 가능성 |

Warm에서 가장 중요한 결론은 “작가와 크기는 반드시 유지하되, 나머지 피처는 후처리/조합 후보로 검증해야 한다”는 점이다. 피처를 무조건 많이 넣는 것보다, 선형 모델이 안정적으로 설명할 수 있는 축과 구간형 보조 정보를 분리해서 쓰는 편이 더 안전하다.

### 3.3 Warm 후처리와 모델 조합 결과

| 단계 | 후보 | test MdAPE | test MAPE | test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| 기준 | Warm Huber baseline | `0.2274` | `0.4952` | `2.0130` | 작가+크기 기준선은 안정적이나 큰 오차가 남음 |
| 단순 tail 보정 | PP-C5 Warm tail strength `0.50` | `0.2211` | 확인 필요 | `1.9055` | 단순 보정만으로는 개선폭 제한 |
| 순차/조합 | PP-D4 Warm integrated | `0.1760` | `0.3293` | `1.1248` | Huber + PP-L8 중심 결합이 큰 개선 |
| 잔차 안정화 | PP-R5 p95 guarded | `0.1707` | `0.3278` | `1.1107` | 강한 후보에 약한 residual 안정화 적용 |
| 최종 fine blend | PP-T1 mape guarded | `0.1621` | `0.3044` | `1.0335` | 대표 정확도와 평균 오차 균형 최선 |
| p95 목적 | PP-T1 mdape | `0.1668` | `0.3067` | `0.9580` | 큰 오차 방어 최선권 |
| meta stacking | PP-T2 Huber meta clipped | `0.1705` | `0.2916` | `0.9582` | MAPE/p95 방어 최강권 |

### 3.4 Warm 개선이 크게 나온 이유

Warm에서 개선폭이 큰 이유는 모델과 피처 역할이 서로 잘 분리됐기 때문이다.

| 구성 요소 | 역할 | 개선에 기여한 이유 |
|---|---|---|
| Huber | 작가+크기 기반 중심 가격선 | 이상치 영향을 줄이면서 Warm의 기본 가격대를 안정적으로 잡음 |
| Quantile 계열 | 예측 불확실성 또는 중앙 예측 보조 | 불확실한 구간을 찾아 조합/라우팅에 활용 가능 |
| CatBoost residual | Huber가 놓친 비선형 조건 조합 보정 | 작가 x 크기 x 재료/구간의 잔차 패턴을 일부 학습 |
| fine blend | 여러 후보의 예측값을 목적별로 가중 결합 | 단일 모델의 약점을 서로 보완 |
| Huber meta | 후보 예측값 간 차이를 다시 안정적으로 조합 | 큰 오차를 무리하게 따라가지 않고 평균/p95를 낮춤 |

즉 Warm 최종 개선은 “Huber를 버리고 다른 모델로 대체해서” 나온 결과가 아니다. Huber가 만든 안정적인 중심선 위에 Quantile과 CatBoost가 각각 불확실성, 잔차 조합을 보완했기 때문에 성능이 좋아졌다.

## 4. Cold 모델 결과와 원인 분석

### 4.1 Cold 기준 모델의 특성

Cold는 같은 작가의 학습 이력이 없거나 약한 경우다. Warm과 달리 작가 기준 가격선을 직접 쓸 수 없으므로, 작품 자체 피처로 가격대를 추정해야 한다.

Cold에서는 모델별 역할이 다음처럼 달랐다.

| 모델 | 구조적 특성 | 잘하는 부분 | 약한 부분 |
|---|---|---|---|
| LightGBM | leaf-wise 트리 | 크기/지지체 구간을 세밀하게 나눔 | 일부 leaf에서 tail risk가 커질 수 있음 |
| CatBoost | 대칭 트리 | 범주형 조합과 반복 split 해석이 좋음 | 원 RMSE 모델은 대표 정확도와 MAPE가 제한적 |
| CatBoost Quantile | 분위 손실 기반 트리 | MAPE와 tail 방어에 강함 | 단독으로는 p95가 아직 남음 |
| Huber residual | 잔차 안정화 선형 모델 | 큰 residual을 과도하게 따라가지 않음 | 단독 모델보다 보정/메타 역할이 적합 |

### 4.2 Cold 피처 근거

| 피처 축 | 실험 근거 | 해석 |
|---|---|---|
| 크기 | `PRE-PP-CB`, `PRE-PP-LGB`에서 size/depth 제거 시 악화 | Cold에서는 작가 기준선이 없으므로 크기가 가장 중요한 가격 신호 |
| depth/3D | CatBoost group-drop에서 제거 시 악화 | 입체/깊이 조건이 크기와 함께 가격 구간을 나눔 |
| `medium_shape_bucket` | Cold CatBoost 기준 피처셋, PRE-SPLIT-CCB에서 `medium_shape_bucket` 구분 학습 MdAPE `0.3784` | CatBoost 대칭 트리가 재료+형태 조합을 조건 구간으로 잘 활용 |
| `support_size_bucket` | PRE-CAL-LGB에서 support_size 보정 validation MdAPE `0.3614` | LightGBM은 지지체+크기 구간에서 반복 오차 보정 여지가 큼 |
| `medium_size_combo` | PP-U3 test MdAPE `0.4909 -> 0.4803` | LightGBM도 medium-size 조합을 추가 후보로 볼 가치가 있음 |

Cold는 Warm보다 “특정 한 피처가 가격을 정한다”고 설명하기 어렵다. 크기, 깊이, 재료, 지지체가 조합되어 가격 구간을 나누기 때문이다. 따라서 Cold 후처리도 전체 상수 보정보다 segment, quantile width, residual 안정화, meta 조합이 더 적합했다.

### 4.3 Cold 주요 후보 결과

| 단계 | 후보 | test MdAPE | test MAPE | test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| 기준 | Cold LightGBM baseline | `0.4909` | `1.4131` | `4.8212` | 대표 정확도는 기준이 되지만 tail risk 큼 |
| 기준 비교 | Cold CatBoost baseline | `0.4867` | `1.4803` | `4.6329` | MdAPE는 유사하나 MAPE가 더 큼 |
| Quantile q50 | CatBoost Quantile q50 | `0.4830` | `1.1514` | `4.2659` | MAPE를 크게 낮춤 |
| 가중 결합 | PP-Q2 Quantile LGBM + CatBoost Quantile | `0.4811` | `1.1797` | `3.7925` | MAPE 최적화 후보 |
| meta 보정 | PP-R4 Huber meta clipped | `0.4796` | `1.2148` | `3.4131` | p95 방어가 강함 |
| 순서 변경 | PP-S1 CatBoost Quantile -> Huber residual cap0.2 | `0.4744` | `1.2095` | `3.4731` | Cold MdAPE 최저 |
| p95 목적 | PP-S1 CatBoost Quantile -> Huber residual cap0.5 | `0.4765` | `1.2067` | `3.2824` | p95 최저권 |
| crossfit meta | PP-S4 Huber crossfit clipped | `0.4765` | `1.2079` | `3.2827` | p95와 재현성 균형 |

### 4.4 Cold 개선이 제한적인 이유

Cold는 Warm보다 성능 개선폭이 작다. 이유는 데이터 구조 때문이다.

- Warm은 `artist_key`가 작가 기준 가격대를 직접 제공한다.
- Cold는 작가 기준선 없이 작품 크기, 재료, 지지체, 형태로만 가격대를 추정한다.
- 같은 크기와 재료라도 작가의 시장 지위가 다르면 가격 차이가 크게 날 수 있다.
- 현재 외부 작가 DB, 검색/소셜 지표는 로컬 split에 없어 PP-G/PP-H는 성능 실험으로 진행하지 못했다.
- 따라서 Cold는 단일 점 예측만으로는 안정적인 가격을 제공하기 어렵고, 가격 범위와 신뢰도 정책이 필요하다.

### 4.5 Cold에서 모델 조합이 효과 있었던 이유

Cold에서 단순 모델 교체보다 “모델 순서와 역할 분리”가 더 효과적이었다.

```text
CatBoost Quantile
-> 중앙 가격과 tail에 강한 기준 예측 생성

Huber residual
-> CatBoost가 남긴 residual을 과도하게 따라가지 않고 안정적으로 보정

component range clipping / meta stacking
-> 여러 후보 예측 범위 밖으로 튀지 않게 제한
```

이 구조가 효과적이었던 이유는 다음과 같다.

| 구성 | 데이터 근거 | 해석 |
|---|---|---|
| CatBoost Quantile | q50 test MAPE `1.4803 -> 1.1514` | RMSE CatBoost보다 평균 오차와 tail에 강함 |
| Huber residual | PP-S1 cap0.2 MdAPE `0.4744`, cap0.5 p95 `3.2824` | Quantile 예측의 residual을 안정적으로 조정 |
| LightGBM Quantile + CatBoost Quantile 결합 | PP-Q2 MAPE `1.1797` | 서로 다른 트리 구조의 중앙 예측을 섞어 MAPE 감소 |
| Huber meta clipped | PP-R4 p95 `3.4131`, PP-S4 p95 `3.2827` | 후보 조합이 과하게 튀는 것을 제한해 큰 오차 방어 |

Cold에서는 “정확도 1위 모델 하나”보다 목적별 후보를 나누는 것이 맞다. MdAPE는 PP-S1 cap0.2, p95는 PP-S1 cap0.5 또는 PP-S4, MAPE는 PP-Q2가 각각 강하다.

## 5. 피처 교환 실험의 의미

PP-U는 모델 설정을 고정하고 피처셋만 바꿔 성능을 비교한 실험이다. 이 실험은 최종 모델을 바로 바꾸기보다, 다음 조합 실험에 넣을 피처 후보를 찾기 위한 목적이다.

| 실험 | validation 1위 | test 1위 | 해석 |
|---|---|---|---|
| PP-U1 Warm Huber | `artist_size_depth` MdAPE `0.2093` | `full_plus_generated_buckets` MdAPE `0.2131` | 생성 bucket 확장은 가능성이 있으나 validation/test 1위가 달라 즉시 교체 보류 |
| PP-U2 Warm CatBoost | `artist_size_only` MdAPE `0.2778` | `artist_size_generated_buckets` MdAPE `0.3125` | CatBoost 내부 개선은 있으나 Warm 주모델로는 약함 |
| PP-U3 Cold LightGBM | `support_shape_combo` MdAPE `0.3834` | `medium_size_combo` MdAPE `0.4803` | LightGBM은 medium-size/support-shape 후보를 추가 검토할 가치 |
| PP-U4 Cold CatBoost | `baseline_base_medium_shape` MdAPE `0.4194` | `lightgbm_swap_support_size` MdAPE `0.4835` | CatBoost 기준 피처셋은 유지, support-size 교환은 보조 후보 |

핵심은 “피처를 바꾸면 성능이 좋아질 수 있다”가 아니라, “validation과 test 방향이 일치하는지 확인해야 한다”는 점이다. PP-U 결과는 즉시 기준 모델 교체 근거라기보다 후속 앙상블, meta stacking, CatBoost Quantile 재학습 후보로 보는 것이 적절하다.

## 6. 실패 또는 보류된 방향

성과가 있었던 후보뿐 아니라 보류된 실험도 의사결정에 중요하다.

| 방향 | 결과 | 보류 이유 |
|---|---|---|
| Warm 전체 residual 보정 | PP-A1 Warm은 MdAPE 악화 | Warm Huber는 이미 중심선이 안정적이라 전체 상수 보정이 과보정될 수 있음 |
| Warm CatBoost 단독 | PP-J3, PP-U2에서 Huber/PP-T보다 약함 | Warm은 작가 기준선이 강해 선형 Huber 중심 구조가 더 적합 |
| 단순 평균 앙상블 | PP-D1에서 MdAPE 악화 | 모델별 역할 분리 없이 평균하면 중심 정확도가 흐려짐 |
| PP-B residual 모델 | validation 개선이 test로 재현되지 않음 | residual 학습이 과적합되기 쉬움 |
| PP-C 직선/비선형 재보정 | validation 개선 대비 test 재현성 약함 | 예측값 재보정이 validation에 맞춰질 위험 |
| Cold segment 보정 단독 채택 | PP-A7/J4는 validation과 p95는 좋지만 test MdAPE 약함 | 점 예측보다 위험/신뢰도 보조 정책으로 적합 |
| 외부/검색 데이터 실험 | PP-G/PP-H 성능 실험 보류 | 신규 데이터 컬럼이 없어 재학습 불가 |

이 보류 결과를 보면, 이번 실험의 핵심 방향은 단순 보정이 아니라 모델별 장점을 나누어 조합하는 것이다.

## 7. 최종 운영 관점 제안

### 7.1 Warm 운영 제안

| 목적 | 추천 후보 | 이유 |
|---|---|---|
| 대표 가격 점 예측 | `PP-T1 fine_blend_mape_guarded` | MdAPE `0.1621`, MAPE `0.3044`로 균형 최상 |
| 큰 오차 방어 | `PP-T1 fine_blend_mdape` 또는 `PP-T2 huber_crossfit_component_range_clipped` | p95가 약 `0.958`까지 낮아짐 |
| 후속 피처 후보 | PP-U1 `full_plus_generated_buckets` | test 개선 확인, 단 validation 불일치로 바로 교체는 보류 |
| 설명 기준 | Huber 중심선 + Quantile/CatBoost 보조 | 작가+크기 기준선과 잔차 조합 구조가 설명 가능 |

Warm은 단일 가격 예측을 제공할 수 있는 수준으로 개선됐다. 다만 p95 방어 목적 후보와 대표 정확도 후보가 완전히 같지는 않으므로, 서비스 정책에서는 `대표 가격`과 `보수적 신뢰도/범위`를 분리해 관리하는 것이 좋다.

### 7.2 Cold 운영 제안

| 목적 | 추천 후보 | 이유 |
|---|---|---|
| 대표 점 예측 | `PP-S1 CatBoost Quantile -> Huber residual cap0.2` | Cold MdAPE 최저 `0.4744` |
| 큰 오차 방어 | `PP-S1 cap0.5` 또는 `PP-S4 Huber crossfit clipped` | p95 약 `3.282`로 최저권 |
| 평균 오차 감소 | `PP-Q2 Quantile LGBM + CatBoost Quantile` | MAPE `1.1797`로 최저권 |
| 가격 범위 표시 | `PP-N3 90% conformal range` | test coverage `0.8061`, 보수 범위 제공 가능 |
| 후속 피처 후보 | PP-U3 `medium_size_combo`, `support_shape_combo` | LightGBM 피처 구조 개선 가능성 확인 |

Cold는 Warm처럼 단일 후보 하나로 끝내기 어렵다. 점 예측 후보와 가격 범위 후보를 분리하고, 낮은 신뢰도 구간에서는 보수적인 범위 표시를 함께 제공하는 방향이 타당하다.

## 8. 최종 결론

### 8.1 가격 예측 정확도 관점 결론

- Warm은 `Huber 중심선 + Quantile/CatBoost 보조 + fine blend/meta` 구조가 가장 효과적이었다.
- Warm 최종 대표 후보는 `PP-T1 fine_blend_mape_guarded`이며, 기준 Huber 대비 MdAPE `28.7%`, MAPE `38.5%`, p95 `48.7%` 개선됐다.
- Cold는 모델 하나를 교체하는 방식보다 `CatBoost Quantile -> Huber residual` 순서가 가장 효과적이었다.
- Cold 최종 대표 후보는 `PP-S1 cap0.2`이며, 기준 LightGBM 대비 MdAPE `3.4%`, MAPE `14.4%`, p95 `28.0%` 개선됐다.
- Cold p95 방어는 `PP-S1 cap0.5` 또는 `PP-S4`가 더 적합하며, p95 개선폭은 약 `31.9%`다.

### 8.2 모델 특성 관점 결론

- Huber는 Warm에서 작가+크기 중심 가격선을 안정적으로 만든다.
- CatBoost는 Cold에서 재료/형태/깊이/크기 조합을 나누는 데 유리하지만, RMSE 단독보다 Quantile 또는 residual 조합으로 쓸 때 효과가 컸다.
- LightGBM은 Cold 기준선과 quantile/범위 생성에 유용하지만, leaf-wise 구조상 tail risk를 별도 관리해야 한다.
- Huber residual과 meta clipping은 후보 예측이 과하게 튀는 것을 줄여 큰 오차 방어에 기여했다.

### 8.3 피처 특성 관점 결론

- Warm 핵심 피처는 `artist_key`와 크기 계열이다.
- Cold 핵심 피처는 크기, depth/3D, material/shape/support 조합이다.
- Warm 생성 bucket, Cold medium-size/support-shape 피처는 후속 조합 후보로 가치가 있다.
- 다만 피처 교환 후보는 validation/test 선택이 일치하지 않는 경우가 있어 즉시 기준 피처셋을 교체하지 않는다.

### 8.4 다음 실행 제안

| 우선순위 | 작업 | 목적 |
|---:|---|---|
| 1 | Warm `PP-T1`과 `PP-T2`를 목적별 정책으로 정리 | 대표 가격과 큰 오차 방어 후보 분리 |
| 2 | Cold `PP-S1 cap0.2`, `PP-S1 cap0.5`, `PP-S4`, `PP-Q2`를 목적별로 비교 확정 | MdAPE, MAPE, p95 목적별 후보 고정 |
| 3 | PP-U 피처 후보를 PP-T/PP-S 후속 조합에 추가 | 피처 교환으로 확인된 개선 가능성 재검증 |
| 4 | Cold 가격 범위 API 정책에 PP-N3 conformal range 반영 | Cold 단일 가격의 위험을 보수적으로 표시 |
| 5 | 외부 작가 DB/검색/소셜 데이터 수집 여부 결정 | Cold의 근본적인 작가 기준선 부족 보완 |

## 9. 주요 수치 출처

| 내용 | 출처 파일 |
|---|---|
| Warm baseline, Warm 피처 교환 | `experiments/track6/PP-U_summary_metrics.csv` |
| Warm PP-D4, PP-R5 | `experiments/track6/PP-R_summary_metrics.csv` |
| Warm PP-T1, PP-T2, PP-T3 | `experiments/track6/PP-T_summary_metrics.csv` |
| Cold baseline, Cold 피처 교환 | `experiments/track6/PP-U_summary_metrics.csv` |
| Cold PP-Q2 test 참조 후보 | `experiments/track6/PP-R_summary_metrics.csv`의 `component_q2_mape_blend` |
| Cold PP-R4 meta | `experiments/track6/PP-R_summary_metrics.csv` |
| Cold PP-S1, PP-S4 | `experiments/track6/PP-S_summary_metrics.csv` |
| 피처 영향도 및 group-drop 근거 | `experiments/track6/PRE-PP_summary_metrics.csv`, `docs/track6/experiments/track6_feature_influence_with_results.md` |
| 모델 구조별 해석 근거 | `docs/track6/experiments/model_structure_based_interpretation_report.md` |
