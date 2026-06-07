# PP-L Huber / Quantile / CatBoost 후처리 실험 종합 요약

- 실행 시각: `2026-06-02T13:51:10`
- 목적: MdAPE를 유지하거나 개선하면서 MAPE와 p95_APE를 낮추는 조합을 검증
- 기준 모델: Warm `Huber`, Cold `CatBoost`
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`
- 판단 기준: validation 우선, test는 최종 확인 보조 자료

## Scope별 Validation Best

| scope | 실험 | 후보 | MdAPE | MAPE | p95_APE | MdAPE delta | MAPE delta | p95 delta |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `cold` | `PP-L4` | `PP-L4_cold_Huber_quantile_width_segment_median` | `0.4026` | `0.6063` | `1.8607` | `-0.0344` | `-0.1543` | `-0.6532` |
| `cold` | `PP-L2` | `PP-L2_depth8_lr0.05_cold` | `0.4121` | `0.7398` | `2.3233` | `-0.0249` | `-0.0208` | `-0.1906` |
| `cold` | `PP-L1` | `PP-L1_D_MAE_loss_cold` | `0.4162` | `0.7038` | `2.3873` | `-0.0208` | `-0.0568` | `-0.1267` |
| `cold` | `PP-L6` | `B2_cold_Quantile_q50` | `0.4188` | `0.7164` | `2.4828` | `-0.0182` | `-0.0443` | `-0.0312` |
| `cold` | `PP-L7-0` | `PP-L7_0_cold_quantile_q50_segment_view` | `0.4188` | `0.7164` | `2.4828` | `-0.0182` | `-0.0443` | `-0.0312` |
| `cold` | `PP-L7-CB` | `PP-L7-CB_cold_segment_catboost_refit` | `0.4263` | `0.7485` | `2.3748` | `-0.0107` | `-0.0121` | `-0.1392` |
| `cold` | `PP-L8` | `PP-L8_cold_quantile_features_huber_catboost_residual` | `0.4277` | `0.7485` | `2.3124` | `-0.0093` | `-0.0121` | `-0.2016` |
| `cold` | `PP-L3` | `B1_Cold_CatBoost` | `0.4370` | `0.7606` | `2.5140` | `0.0000` | `0.0000` | `0.0000` |
| `cold` | `PP-L5` | `B1_Cold_CatBoost` | `0.4370` | `0.7606` | `2.5140` | `0.0000` | `0.0000` | `0.0000` |
| `cold` | `PP-L7-H` | `B1_Cold_CatBoost` | `0.4370` | `0.7606` | `2.5140` | `0.0000` | `0.0000` | `0.0000` |
| `cold` | `PP-L7-HCB` | `B1_Cold_CatBoost` | `0.4370` | `0.7606` | `2.5140` | `0.0000` | `0.0000` | `0.0000` |
| `cold` | `PP-L9` | `B1_Cold_CatBoost` | `0.4370` | `0.7606` | `2.5140` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L8` | `PP-L8_warm_quantile_features_huber_catboost_residual` | `0.1808` | `0.3152` | `0.9341` | `-0.0318` | `-0.1015` | `-0.3852` |
| `warm` | `PP-L9` | `PP-L9_warm_huber_quantile_residual_catboost_remaining` | `0.1824` | `0.3294` | `1.1614` | `-0.0302` | `-0.0872` | `-0.1580` |
| `warm` | `PP-L6` | `PP-L6_warm_validation_weighted_ensemble` | `0.1930` | `0.3563` | `1.1304` | `-0.0196` | `-0.0603` | `-0.1889` |
| `warm` | `PP-L1` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L2` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L3` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L4` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L5` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L7-0` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L7-H` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L7-CB` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |
| `warm` | `PP-L7-HCB` | `B0_Warm_Huber` | `0.2126` | `0.4167` | `1.3194` | `0.0000` | `0.0000` | `0.0000` |

## 1차 판단

- Warm에서는 `PP-L8 Quantile -> Huber -> CatBoost`와 `PP-L9 Huber -> Quantile residual -> CatBoost`가 기준 대비 MdAPE, MAPE, p95_APE를 함께 낮춘 후보로 나타났다.
- Cold에서는 `PP-L1`의 저가 가중/MAE/Quantile 계열 CatBoost와 `PP-L6`의 Quantile q50/가중 앙상블이 MAPE 완화 후보로 보인다.
- Cold `PP-L9`는 기준 대비 MAPE와 MdAPE가 악화되어 보류 후보로 기록한다.
- Huber fold 일부에서 수렴 경고가 발생했으므로 Warm 후보 확정 전 max_iter/수렴 상태 재확인이 필요하다.

## 결과 해석 코멘터리

### 전체 해석

- 이번 PP-L 실험의 가장 중요한 결과는 Warm과 Cold가 같은 후처리 구조에 같은 방식으로 반응하지 않았다는 점이다.
- Warm은 이미 `artist_key`를 포함한 Huber 기준선이 가격 중심선을 비교적 안정적으로 잡고 있기 때문에, Quantile로 예측 불확실성을 먼저 읽고 CatBoost가 잔여 오차만 보정하는 순차 구조가 잘 맞았다.
- Cold는 작가 식별 정보 없이 크기/재료/지지체/형태 정보만으로 예측해야 하므로, 전체 순차 구조보다 구간별 중앙 residual 보정이나 CatBoost 목적 함수 조정처럼 단순하고 국소적인 보정이 더 안정적으로 보였다.
- 따라서 PP-L 결과만 보면 Warm은 `순차 모델 결합`, Cold는 `구간별 보정 + CatBoost 목적 함수 조정`을 분리해서 가져가는 방향이 타당하다.

### Warm 결과 분석

- Warm 기준 모델 `B0_Warm_Huber`는 validation MdAPE `0.2126`, MAPE `0.4167`, p95_APE `1.3194`였다.
- `PP-L8_warm_quantile_features_huber_catboost_residual`은 validation에서 MdAPE `0.1808`, MAPE `0.3152`, p95_APE `0.9341`로 모두 개선됐다.
- test에서도 PP-L8은 MdAPE `0.1777`, MAPE `0.3383`, p95_APE `1.1047`로 기준 Warm Huber test MdAPE `0.2274`, MAPE `0.4952`, p95_APE `2.0130` 대비 같은 방향으로 개선됐다.
- 이 결과는 Quantile이 먼저 가격 범위의 불확실성을 알려주고, Huber가 중심 가격선을 잡은 뒤, CatBoost가 비선형 잔여 오차를 보정하는 구조가 Warm 데이터에서 유효하다는 의미다.
- `PP-L9_warm_huber_quantile_residual_catboost_remaining`도 validation/test 모두 개선됐지만 PP-L8보다 p95 개선폭이 작다. Warm 최우선 후보는 PP-L8, 보조 후보는 PP-L9로 보는 것이 적절하다.
- `PP-L6_warm_validation_weighted_ensemble`은 validation에서는 개선됐지만 test MdAPE가 기준보다 소폭 나빠졌다. MAPE와 p95는 좋아졌으나 대표 오차 안정성 기준에서는 PP-L8보다 우선순위가 낮다.
- Warm에서 CatBoost 단독 목적 함수 변경인 PP-L1/PP-L2는 Huber 기준선을 이기지 못했다. 이는 Warm에서는 선형 Huber가 작가별 기준 가격선을 직접 설명하는 장점이 있고, CatBoost 단독은 이 구조를 충분히 대체하지 못했다는 해석이 가능하다.

### Cold 결과 분석

- Cold 기준 모델 `B1_Cold_CatBoost`는 validation MdAPE `0.4370`, MAPE `0.7606`, p95_APE `2.5140`였다.
- `PP-L4_cold_Huber_quantile_width_segment_median`은 validation에서 MdAPE `0.4026`, MAPE `0.6063`, p95_APE `1.8607`로 가장 크게 개선됐다.
- test에서도 PP-L4는 MdAPE `0.4778`, MAPE `1.0404`, p95_APE `3.3145`로 Cold CatBoost 기준 test MdAPE `0.5001`, MAPE `1.4341`, p95_APE `4.1815` 대비 같은 방향으로 개선됐다.
- PP-L4의 구간별 bootstrap을 보면 high uncertainty 구간은 mean APE delta `-0.4188`로 크게 좋아졌고, low 구간도 `-0.0772`로 좋아졌다. 반면 mid 구간은 `+0.0316`으로 악화됐다.
- 따라서 Cold PP-L4는 전체 적용 후보라기보다, high/low 구간에는 적용하고 mid 구간에는 기존 CatBoost를 유지하는 선택형 보정으로 고도화하는 것이 더 적합하다.
- PP-L1의 MAE/Quantile CatBoost는 validation/test 모두 기준 CatBoost보다 개선됐다. 이는 Cold에서 평균제곱오차 계열 RMSE보다 절대오차/중앙값 계열 목적 함수가 큰 가격 outlier 영향을 덜 받기 때문으로 해석된다.
- PP-L2 depth8/lr0.05는 validation MdAPE를 낮췄지만 test에서는 MAPE와 p95 개선이 제한적이다. CatBoost 옵션 조정은 후보이지만, 단독 채택보다는 PP-L4 보정과 함께 비교해야 한다.
- Cold PP-L8은 MdAPE와 MAPE는 낮췄지만 test p95가 기준보다 악화됐다. 큰 오차를 줄이는 목적에는 맞지 않으므로 보류가 맞다.
- Cold PP-L9는 validation/test 모두 기준 대비 악화되어 중단 후보로 보는 것이 맞다. Cold에서는 Huber residual을 다시 Quantile과 CatBoost로 나누는 구조가 데이터 수와 정보량 대비 과도한 단계로 보인다.

### 실험군별 코멘터리

- `PP-L1`: Cold CatBoost의 목적 함수를 MAE/Quantile 계열로 바꾸면 MAPE와 MdAPE가 개선된다. Warm에서는 Huber 기준선보다 나빠져 Warm에는 부적합하다.
- `PP-L2`: Cold CatBoost option 중 depth를 키운 후보가 validation에서는 개선됐다. 다만 test 안정성이 PP-L4보다 약하므로 단독 채택보다는 보조 후보로 둔다.
- `PP-L3`: Huber 선행 + CatBoost residual은 Warm에서 MAPE/p95를 일부 낮췄지만 MdAPE는 악화됐다. Cold에서는 악화되어 채택 가치가 낮다.
- `PP-L4`: Cold에서 가장 강한 후보다. 단, mid uncertainty 구간 악화가 확인되어 전체 적용보다 구간 선택 적용이 필요하다.
- `PP-L5`: 현재 라우팅 규칙은 baseline을 이기지 못했다. PP-L4의 segment bootstrap 결과를 반영해 high/low만 보정하는 방식으로 다시 설계해야 한다.
- `PP-L6`: Warm에서는 MAPE/p95 완화 효과가 있으나 test MdAPE가 기준보다 소폭 악화됐다. Cold에서는 Quantile q50 효과가 있으나 PP-L4보다 약하다.
- `PP-L7-0`: Quantile 구간 자체는 해석 가치가 있다. 구간별로 어디서 보정이 먹히는지 보여주는 진단용 실험으로 유지한다.
- `PP-L7-H`: 구간별 Huber 상세 학습은 기준 모델 대비 뚜렷한 이득이 없었다.
- `PP-L7-CB`: Cold에서 소폭 개선됐지만 PP-L4/PP-L1보다 약하다. 구간별 CatBoost 분기 학습은 추가 조정 없이는 우선순위가 낮다.
- `PP-L7-HCB`: Huber와 CatBoost의 단순 구간 결합은 현재 라우팅 기준에서 이득이 없다.
- `PP-L8`: Warm 최우선 후보다. Quantile의 불확실성 정보, Huber 중심선, CatBoost residual 보정이 역할 분담을 잘 했다.
- `PP-L9`: Warm 보조 후보지만 Cold에서는 중단 후보다. residual을 다시 여러 단계로 나누는 방식은 Cold 정보량에서는 불안정하다.

### 채택/보류 판단

- Warm 1순위 채택 후보: `PP-L8_warm_quantile_features_huber_catboost_residual`
- Warm 2순위 후보: `PP-L9_warm_huber_quantile_residual_catboost_remaining`
- Warm 보류 후보: `PP-L6_warm_validation_weighted_ensemble`
- Cold 1순위 채택 후보: `PP-L4_cold_Huber_quantile_width_segment_median`, 단 mid 구간 제외/완화 조건 필요
- Cold 2순위 후보: `PP-L1_D_MAE_loss_cold` 또는 `PP-L1_D_Quantile_050_cold`
- Cold 보조 후보: `PP-L2_depth8_lr0.05_cold`
- Cold 중단 후보: `PP-L9_cold_huber_quantile_residual_catboost_remaining`

### 후속 작업 제안

- Warm PP-L8은 Huber 수렴 경고를 먼저 해소한 뒤, 동일 split에서 seed 반복과 test 재현성을 다시 확인한다.
- Cold PP-L4는 high/low 구간만 보정하고 mid 구간은 CatBoost 기준값을 유지하는 `선택형 segment 보정`으로 재실험한다.
- Cold PP-L1은 MAE/Quantile loss를 PP-L4 보정 전후에 각각 붙여, 목적 함수 조정과 구간 보정이 함께 쓸 수 있는지 확인한다.
- PP-L5 라우팅은 현재 규칙을 폐기하고 PP-L4 segment bootstrap 결과를 기준으로 다시 정의한다.
- 최종 후보는 Warm PP-L8, Cold PP-L4 선택형 보정, Cold PP-L1 MAE/Quantile을 같은 validation/test 기준에서 비교한 뒤 확정한다.

## 산출물

- 전체 best CSV: `experiments/track6/PP-L_summary_metrics.csv`
- scope별 summary CSV: `experiments/track6/PP-L_summary_by_scope.csv`
- 각 실험 폴더의 `reports/result_report.html`에서 후보별 상세 결과와 통계 검증을 확인한다.
