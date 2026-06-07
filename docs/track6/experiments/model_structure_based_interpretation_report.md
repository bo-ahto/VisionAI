# 모델 구조 기반 피처 영향 해석 보고서

- 작성일: `2026-05-31`
- 목적: Warm Huber, Cold CatBoost, Cold LightGBM의 모델 구조 차이에 맞춰 피처 영향도를 해석한다.
- 기준 산출물:
  - `docs/track6/experiments/warm_huber_interpretability_audit_report.html`
  - `docs/track6/experiments/cold_models_interpretability_audit_report.html`

## 1. 전체 결론

- 기존 해석 산출물은 최종 artifact와 피처셋이 달라 최종 모델 설명 자료로 그대로 쓰기 어렵다.
- Warm Huber는 최종 artifact 기준으로 계수와 실제 기여도를 다시 산출했다.
- Cold CatBoost는 최종 `.cbm` 기준으로 SHAP, interaction, leaf segment 잔차를 다시 산출했다.
- Cold LightGBM은 최종 pipeline 기준으로 split importance, permutation, leaf-wise, tail slice 진단을 다시 산출했다.
- 세 모델 모두 크기 계열 피처가 가장 강한 가격 설명 축이다.
- CatBoost는 크기 단독보다 `크기 × 깊이`, `깊이 × 재료`, `크기 × 재료/지지체` interaction이 중요하다.
- LightGBM은 크기 피처, 특히 `area_cm2`에 매우 민감하며 p95 tail risk가 CatBoost보다 크다.

## 2. Warm Huber 구조 기반 해석

| 항목 | 내용 |
|---|---|
| 모델 구조 | 선형 회귀 기반 HuberRegressor |
| 손실 특성 | 작은 오차는 제곱 손실, 큰 오차는 선형 손실로 처리 |
| 해석 단위 | 계수, 원 단위 환산 계수, 입력값 × 계수, Huber outlier 여부 |
| 최종 피처셋 | `base_existing_combo + artist_key` |
| test 성능 | MdAPE `0.2241`, p95_APE `2.0209`, RMSE_log `0.6093` |
| outlier 비율 | test 기준 `48.9%` |

### 해석

- Huber는 선형 모델이므로 피처 영향은 직접 계수로 해석할 수 있다.
- 숫자형 피처는 표준화 후 모델에 들어가므로, 계수 해석 시 원 단위 환산 계수를 함께 봐야 한다.
- 범주형 one-hot 피처는 원계수를 그대로 비교하면 기준 범주 문제와 공선성 때문에 과대 해석될 수 있다.
- 따라서 범주형은 같은 원본 피처 안의 평균 범주 효과를 뺀 `centered_coef`와 `mean_abs_centered_contribution`을 우선 해석 기준으로 사용했다.
- 최종 artifact 기준 피처 그룹 기여도는 `size > medium_support > support > medium > artist > depth_3d > shape` 순서다.
- Huber outlier 비율이 높기 때문에, 큰 오차 구간에서는 “피처가 가격을 설명하지 못했다”기보다 “Huber가 해당 샘플의 학습 영향력을 낮췄다”는 관점도 같이 봐야 한다.

### 후처리 연결

- Warm Huber는 전체적인 선형 편향이 남아 있을 때 median residual 보정이 자연스럽다.
- 개별 범주 계수보다 그룹별 실제 기여도와 outlier slice를 기준으로 보정 대상을 잡는 편이 안전하다.
- `epsilon=1.1`은 validation MdAPE가 낮지만 수렴 실패와 test p95 악화가 있어 바로 대체하지 않고 안정성 실험 후보로 둔다.

## 3. Cold CatBoost 구조 기반 해석

| 항목 | 내용 |
|---|---|
| 모델 구조 | CatBoost 대칭 트리, Oblivious Tree |
| 최종 피처셋 | `base_medium_shape` |
| tree 수 | `500` |
| inferred depth | `6` |
| leaf count | 트리당 중앙값 `64` |
| test 성능 | MdAPE `0.4843`, p95_APE `4.4183`, RMSE_log `0.9549` |

### SHAP 기준 단독 영향

| 순위 | 피처 | mean_abs_SHAP | 해석 |
|---:|---|---:|---|
| 1 | `width_cm` | `0.2629` | 크기 축 중 가장 강한 단독 영향 |
| 2 | `area_cm2` | `0.2217` | 면적 기반 가격대 분리 |
| 3 | `log_area` | `0.1974` | 로그 크기 기반 가격대 안정화 |
| 4 | `height_cm` | `0.1266` | 세로 크기 보조 |
| 5 | `depth_cm` | `0.0940` | 입체/깊이 조건에서 가격대 분기 |

### 대칭 트리 구조에 맞춘 해석

- CatBoost는 같은 depth의 노드들이 동일한 split 조건을 공유하는 대칭 트리 구조다.
- 따라서 “특정 피처가 단독으로 가격을 올렸다”보다 “반복 split과 interaction으로 가격 구간을 나눴다”는 해석이 더 적합하다.
- 최종 모델의 interaction 상위는 다음과 같다.

| 순위 | interaction | score | 해석 |
|---:|---|---:|---|
| 1 | `width_cm × depth_cm` | `5.5493` | 크기와 깊이 조합으로 2D/3D 또는 대형작 조건을 구분 |
| 2 | `height_cm × depth_cm` | `5.2242` | 세로 크기와 깊이 조합으로 가격 구간 분화 |
| 3 | `depth_cm × aspect_ratio` | `5.1604` | 깊이와 형태 비율이 함께 작동 |
| 4 | `depth_cm × medium_category` | `4.8243` | 입체/깊이 효과가 재료에 따라 다르게 작동 |
| 5 | `depth_cm × area_cm2` | `4.6171` | 면적과 깊이 조합이 큰 작품 구간을 설명 |

### Leaf segment 해석

- CatBoost leaf pattern 50개 트리 기준 unique segment 수는 `1488`개다.
- top 10 leaf pattern coverage는 `7.68%`로 낮다.
- 이는 Cold 데이터에서 유사한 leaf pattern이 넓게 반복되기보다 세분화되어 있음을 의미한다.
- leaf segment별 잔차를 보면 일부 segment는 MdAPE와 p95가 매우 크다.
- 따라서 CatBoost 후처리는 전체 보정보다 `leaf pattern`, `medium_shape_bucket`, `shape/medium segment` 기반 residual 보정이 모델 구조와 더 잘 맞는다.

### 후처리 연결

- CatBoost에는 global correction보다 leaf/segment residual 보정이 더 자연스럽다.
- 단, leaf pattern coverage가 낮으므로 leaf 단독 보정보다는 fallback 구조가 필요하다.
- 권장 fallback:
  - leaf pattern
  - `medium_shape_bucket`
  - `shape_bucket` 또는 `medium_category`
  - overall residual

## 4. Cold LightGBM 구조 기반 해석

| 항목 | 내용 |
|---|---|
| 모델 구조 | leaf-wise gradient boosting tree |
| 최종 피처셋 | `base_support_size` |
| tree 수 | `350` |
| test 성능 | MdAPE `0.4797`, p95_APE `5.0569`, RMSE_log `0.9551` |

### LightGBM 해석 기준

- LightGBM은 leaf-wise 방식으로 손실을 크게 줄일 수 있는 leaf를 우선 확장한다.
- 따라서 split importance가 높다는 것은 전체적으로 많이 쓰였다는 뜻이지만, 일부 구간에서 깊게 분화된 영향일 수도 있다.
- permutation 영향과 tail slice를 함께 봐야 한다.

### 중요도와 permutation 결과

| 관점 | 핵심 피처 | 해석 |
|---|---|---|
| split importance | `depth_cm`, `aspect_ratio`, `area_cm2`, `width_cm`, `height_cm` | 깊이, 형태, 크기 피처를 많이 사용 |
| permutation MdAPE delta | `area_cm2` `+0.2542` | 면적 교란 시 대표 오차가 크게 악화 |
| permutation p95 delta | `area_cm2` `+7.5139` | 면적이 tail risk에도 매우 큰 영향 |
| tail slice | `canvas__q5`, `acrylic`, `q3`, `canvas__q3` | 특정 크기/지지체/재료 구간에서 큰 오차 발생 |

### leaf-wise 구조에 맞춘 해석

- LightGBM leaf 진단에서 tree별 worst leaf MdAPE가 매우 큰 구간이 확인됐다.
- 이는 평균 MdAPE는 CatBoost와 비슷하지만, 일부 leaf가 큰 오차를 만드는 구조일 가능성을 보여준다.
- 따라서 LightGBM은 CatBoost처럼 leaf pattern 보정보다 `size_bucket`, `support_size_bucket`, `pred_log bin` 기반 보정이 더 현실적이다.
- 특히 `area_cm2`, `width_cm`, `height_cm`, `log_area`가 동시에 들어가면서 크기 정보 중복이 생길 수 있다.

### 후처리 연결

- LightGBM은 p95 tail risk가 크므로 대표값 보정보다 tail 안정화가 우선이다.
- 권장 추가 실험:
  - `C-LGBM-size-ablation`: 크기 파생 피처 중복성 확인
  - `C-LGBM-tail-slice`: size/support/material slice별 p95 진단
  - `C-LGBM-pred-bin-calibration`: 예측값 구간별 residual 보정

## 5. 모델별 해석/보정 원칙

| 모델 | 해석 우선 기준 | 피해야 할 해석 | 적합한 보정 |
|---|---|---|---|
| Warm Huber | 계수, 원 단위 환산 계수, 실제 기여도, outlier 여부 | 범주형 one-hot 원계수 단순 비교 | global median residual, group residual |
| Cold CatBoost | SHAP, interaction, leaf segment residual | importance 순위만으로 단독 영향 단정 | leaf/segment residual + fallback |
| Cold LightGBM | permutation, tail slice, leaf-wise 진단 | split importance만으로 영향 단정 | pred bin, size/support bucket, tail 안정화 |

## 6. 다음 작업

- Warm Huber 보고서는 현재 최종 artifact 기준 해석 산출물로 교체한다.
- Cold CatBoost 보고서는 SHAP뿐 아니라 interaction과 leaf segment 잔차를 포함한 구조 기반 해석으로 교체한다.
- Cold LightGBM 보고서는 split importance보다 permutation과 tail slice 중심으로 설명한다.
- 최종 모델 비교 보고서에는 세 모델의 해석 기준이 서로 다르다는 점을 명시한다.
