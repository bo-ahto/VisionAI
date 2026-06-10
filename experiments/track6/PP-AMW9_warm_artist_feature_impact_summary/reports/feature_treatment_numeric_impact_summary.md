# Track6 피처/조합/처리별 수치 영향도 종합

- 작성일: 2026-06-08
- 목적: 작가 메타뿐 아니라 작품 관련 피처까지 포함해, 피처 단독/피처 조합/후처리 방식의 성능 영향도를 수치로 비교한다.
- 해석 기준: `delta_MdAPE`, `delta_MAPE`, `delta_p95_APE`는 기준 대비 변화량이다. 음수는 개선, 양수는 악화다.
- 주의: 아래 표는 서로 다른 실험군의 결과를 한 문서에 모은 것이다. 기준선이 다른 표끼리는 직접 순위 비교하지 않고, 같은 표 안에서만 비교한다.

## 1. 결론 먼저

작품 관련 피처까지 포함하면 현재까지의 구조는 다음처럼 보인다.

| 우선순위 | 피처/처리 축 | 수치 근거 | 판단 |
| ---: | --- | --- | --- |
| 1 | 작품 크기 | Warm 그룹 제거 시 test MdAPE가 `0.2274 -> 0.5508`로 악화, `+0.3233` | 필수 축 |
| 2 | 작가명 + 작품 크기 조합 | Warm 초기 조합에서 MdAPE `0.4352 -> 0.1569`, `-63.95%` | Warm 핵심 조합 |
| 3 | 작가 세대 Huber 보정 | 최신 Warm 기준 test MdAPE/MAPE/p95가 `-0.0023/-0.0010/-0.0191` 개선 | 최신 보정 1순위 |
| 4 | 작품 크기+비교군 신뢰도 약한 Huber 보정 | 최신 Warm 기준 p95 `-0.0217`, MAPE `-0.0004` | p95 방어 후보 |
| 5 | 깊이/3D | Cold 초기 실험 MdAPE `0.5083 -> 0.4468`, `-12.10%` | Cold에서 강한 작품 축 |
| 6 | 재료/지지체 | 단독은 악화, 크기와 결합하면 Warm `-3.50%`, Cold `-2.53%` | 조합 피처로만 의미 |

즉, “작가별 보정”만 보면 그림이 좁아진다. 작품 자체에서는 크기가 가장 강하고, 재료/지지체/깊이/작품유형은 단독보다는 조합 또는 트리/세그먼트 처리에서 의미가 커진다.

## 2. 모델 내부 영향도 수치

이 표는 성능 변화가 아니라 모델이 실제 예측값을 얼마나 움직였는지에 가까운 해석 지표다.

### Warm Huber 그룹 contribution

| feature_group | mean_abs_centered_contribution_sum | 순위 | 해석 |
| --- | ---: | ---: | --- |
| size | 1.2222 | 1 | 작품 크기가 Warm 예측값을 가장 크게 움직임 |
| medium_support | 0.5625 | 2 | 재료+지지체 조합이 가격대 보정 역할 |
| support | 0.5121 | 3 | 지지체 단독도 일정 영향 |
| medium | 0.4920 | 4 | 재료 단독 영향 |
| artist | 0.4353 | 5 | Warm에서 작가 가격대 반영 |
| depth_3d | 0.0320 | 6 | Warm 선형 구조에서는 영향 작음 |
| shape | 0.0067 | 7 | Warm에서는 보조 수준 |

### Cold CatBoost SHAP/Interaction

| 구분 | 피처/조합 | 수치 | 순위 | 해석 |
| --- | --- | ---: | ---: | --- |
| SHAP | width_cm | 0.2629 | 1 | Cold에서 크기 분기 핵심 |
| SHAP | area_cm2 | 0.2217 | 2 | 크기 축 |
| SHAP | log_area | 0.1974 | 3 | 크기 축 |
| SHAP | height_cm | 0.1266 | 4 | 크기 축 |
| SHAP | depth_cm | 0.0940 | 5 | 3D/입체성 신호 |
| interaction | width_cm x depth_cm | 5.5493 | 1 | 큰 입체/오브제 구간 분리 |
| interaction | height_cm x depth_cm | 5.2242 | 2 | 크기와 깊이 조합 효과 |
| interaction | depth_cm x aspect_ratio | 5.1604 | 3 | 형태와 입체성 조합 |
| interaction | depth_cm x medium_category | 4.8243 | 4 | 재료에 따라 깊이 의미 변화 |

## 3. 작품 피처 단독/추가 영향도

초기 피처 추가 실험 기준이다. 같은 표 안에서 기준선과 후보를 비교한다.

| scope | 피처 | 비교 | 기준 MdAPE | 후보 MdAPE | delta | 개선율 | MAPE 변화 | p95 변화 | 판단 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Warm | 작품 크기 파생 | artist+호수 대비 all_size 추가 | 0.1946 | 0.1801 | -0.0145 | -7.45% | -0.0143 | -0.0550 | 강함 |
| Cold | 작품 크기 파생 | 호수 대비 width/height/aspect 추가 | 0.5083 | 0.5056 | -0.0027 | -0.53% | +0.0599 | +0.0583 | MdAPE만 소폭 |
| Warm | 지지체 | artist+호수 대비 support 추가 | 0.1946 | 0.1925 | -0.0021 | -1.08% | +0.0025 | -0.0448 | p95 방어 |
| Cold | 지지체 | 호수 대비 support 추가 | 0.5083 | 0.4812 | -0.0271 | -5.33% | +0.1395 | -0.0330 | MdAPE 개선, MAPE 악화 |
| Warm | 깊이/3D | artist+호수 대비 depth 추가 | 0.1946 | 0.1970 | +0.0024 | +1.23% | -0.0008 | -0.0099 | Warm 단독은 약함 |
| Cold | 깊이/3D | 호수 대비 depth 추가 | 0.5083 | 0.4468 | -0.0615 | -12.10% | +0.0075 | +0.1561 | Cold MdAPE 강함, tail 주의 |
| Warm | 재료 단독 | 크기 대비 material only | 0.5052 | 0.7177 | +0.2125 | +42.06% | - | - | 단독 부적합 |
| Cold | 재료 단독 | 크기 대비 material only | 0.4980 | 0.6977 | +0.1997 | +40.10% | - | - | 단독 부적합 |
| Warm | 작품 유형 | artist only 대비 type 추가 | 0.4352 | 0.4263 | -0.0089 | -2.06% | - | - | 보조 효과 |
| Cold | 작품 유형 | basic artwork 대비 type 추가 | 0.4956 | 0.4813 | -0.0143 | -2.87% | - | - | 보조 효과 |

## 4. 피처 조합 영향도

조합 실험 기준이다. “단독으로는 약한 피처가 조합에서 살아나는지”를 보기 위한 표다.

| scope | 피처 조합 | 기준 | 기준 MdAPE | 후보 | 후보 MdAPE | delta | 개선율 | 판단 |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| Warm | 작가명 + 전체 크기 | artist only | 0.4352 | artist + width/height/log_area/aspect | 0.1569 | -0.2783 | -63.95% | Warm 최강 조합 |
| Warm | 작가명 + 기본 작품 피처 | artist only | 0.4352 | artist + 호수/재료/지지체 | 0.1801 | -0.2551 | -58.62% | Warm 핵심 |
| Warm | 크기 + 재료 | ln_size only | 0.5052 | log_area + material | 0.4764 | -0.0288 | -5.70% | 재료는 조합에서 의미 |
| Warm | 크기/재료 + 지지체 | size + material | 0.4432 | size + material + support | 0.4277 | -0.0155 | -3.50% | 지지체 조합 효과 |
| Warm | 작가명 + 제작연도 | artist only | 0.4352 | artist + artwork_year | 0.4300 | -0.0052 | -1.20% | 보조 |
| Warm | 작가명 x 면적 | artist + size | 0.1569 | interaction | 0.1565 | -0.0004 | -0.25% | 거의 변화 없음 |
| Cold | 작품 기본 + 활동/인지도 CatBoost | basic artwork | 0.4795 | activity/popularity CatBoost | 0.4488 | -0.0307 | -6.40% | Cold 상위 |
| Cold | 작품 기본 + 활동/판매노출 | basic artwork | 0.4795 | activity/sales | 0.4577 | -0.0218 | -4.55% | Cold 핵심 메타 |
| Cold | 작품 기본 + 전체 작가 메타 | basic artwork | 0.4795 | full artist meta | 0.4684 | -0.0111 | -2.31% | 효율 재검증 필요 |
| Cold | 작품 유형 + 깊이/3D | basic artwork + type | 0.4813 | + depth/3D | 0.4745 | -0.0068 | -1.41% | Cold depth 조합 유효 |
| Cold | 활동/인지도 x 면적 | activity/sales | 0.4577 | activity x log_area | 0.4516 | -0.0061 | -1.33% | 시장 노출 x 대형작 |
| Cold | 면적 x 지지체 | basic artwork | 0.4795 | area x support | 0.4745 | -0.0050 | -1.04% | interaction 후보 |
| Cold | 크기/재료 + 지지체 | size + material | 0.4919 | size + material + support | 0.4795 | -0.0124 | -2.53% | Cold 기본 작품 조합 |

## 5. 최종 Warm 구조에서 작품 그룹 제거 영향

최종 Warm Huber 구조에 가까운 group drop ablation이다. 후보 값이 커질수록 해당 그룹을 제거했을 때 성능이 나빠진다는 뜻이다.

| 제거 그룹 | 기준 MdAPE | 제거 후 MdAPE | delta MdAPE | delta MAPE | delta p95 | 판단 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| size | 0.2274 | 0.5508 | +0.3233 | +0.8025 | +3.2143 | 크기 제거 시 붕괴. 필수 |
| medium_support | 0.2274 | 0.2253 | -0.0021 | +0.0035 | -0.0202 | 혼재. 대표오차는 개선, 평균오차는 악화 |
| depth_3d | 0.2274 | 0.2276 | +0.0001 | +0.0021 | +0.0128 | Warm에서는 영향 작음 |
| shape_aspect | 0.2274 | 0.2264 | -0.0011 | +0.0024 | -0.0056 | 보조 수준 |

이 결과는 작품 크기의 중요성을 가장 강하게 보여준다. 다만 이 그룹 제거 실험은 과거 Warm Huber artifact 기준이고, 최신 안정 후보 `blend_svcnum_ppv8_wsvc_0.70` 기준과는 직접 수치 비교하지 않는다.

## 6. 최신 Warm 안정 후보 기준 후처리 영향

기준 후보는 `blend_svcnum_ppv8_wsvc_0.70`이고 test 기준 성능은 `MdAPE 0.1405`, `MAPE 0.2748`, `p95_APE 0.8331`이다.

| 피처/조합 | 처리 방식 | 후보 MdAPE | delta MdAPE | 후보 MAPE | delta MAPE | 후보 p95 | delta p95 | 판단 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 작가 세대 구간 | Huber residual cap0.03 strength0.75 | 0.1381 | -0.0023 | 0.2738 | -0.0010 | 0.8140 | -0.0191 | 최신 보정 1순위 |
| 작가 세대 구간 | Huber residual cap0.03 strength0.50 | 0.1386 | -0.0019 | 0.2740 | -0.0008 | 0.8109 | -0.0222 | 보수형 후보 |
| 작가 생년 | Segment median cap0.03 | 0.1370 | -0.0035 | 0.2747 | -0.0001 | 0.8240 | -0.0091 | cap 제한 조건부 유효 |
| 작가 커리어 단계 | Segment median cap0.05 | 0.1384 | -0.0021 | 0.2737 | -0.0011 | 0.8292 | -0.0039 | 보조 후보 |
| 생년+세대+커리어 | Ridge residual cap0.03 strength0.75 | 0.1441 | +0.0036 | 0.2765 | +0.0017 | 0.8217 | -0.0114 | p95만 개선, 과조합 |
| 생년+세대+커리어 | Huber residual cap0.05 strength0.75 | 0.1460 | +0.0056 | 0.2759 | +0.0011 | 0.8340 | +0.0010 | 채택 보류 |
| 작품 크기+형태+비교군 신뢰도 | Weak Huber cap0.03 strength0.50 | 0.1397 | -0.0008 | 0.2744 | -0.0004 | 0.8114 | -0.0217 | p95 방어 후보 |
| 작품 면적 구간 | validation MAPE segment | 0.1691 | +0.0286 | 0.2744 | -0.0004 | 0.8268 | -0.0062 | MdAPE 악화로 기본값 부적합 |
| 예측 불확실성 구간 | quantile width segment | 0.1638 | +0.0233 | 0.2674 | -0.0074 | 0.8322 | -0.0009 | MAPE 목적 전용 |
| 크기 계수 재학습 | Huber retrain size coefficients | 0.2178 | +0.0773 | 0.4914 | +0.2166 | 1.8883 | +1.0552 | 직접 재학습 부적합 |

## 7. 해석

수치상으로 보면 세 가지 결론이 명확하다.

1. 작품 크기는 모든 실험군에서 가장 강한 작품 피처다. Warm에서는 작가 가격대 안에서 가격을 조정하고, Cold에서는 작가 정보가 없을 때 가격대 기준선 역할을 한다.
2. 재료/지지체/작품유형/깊이는 단독보다 조합에서 의미가 크다. 특히 Cold에서는 `size x depth`, `depth x medium`, `area x support`처럼 interaction으로 볼 때 영향이 커진다.
3. 최신 Warm 안정 후보 기준에서는 직접 계수 재학습보다 약한 잔차 보정이 안전하다. 작가 세대 Huber와 작품/SVC 기반 weak Huber는 p95 방어 신호가 있고, 강한 다중 조합이나 직접 재학습은 test에서 무너졌다.

## 8. 세부 CSV

- 피처 단독/추가 수치: `outputs/feature_level_numeric_impact.csv`
- 피처 조합 수치: `outputs/feature_combo_numeric_impact.csv`
- Warm 그룹 제거 수치: `outputs/warm_group_drop_numeric_impact.csv`
- 최신 Warm 후처리 수치: `outputs/latest_residual_treatment_numeric_impact.csv`

