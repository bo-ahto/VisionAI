# Track6 가격 예측 모델 상세 해석 및 후처리 계획 발표 스크립트

- 예상 발표 시간: 25~30분
- 대상: 상사 및 임원
- 톤: 의사결정 중심이지만 계산 로직과 영향도 산출 방식까지 설명

---

## 1. 오늘 보고의 목적

오늘은 Track6 가격 예측 모델을 단순히 성능 수치로만 보고드리는 것이 아니라, 가격이 어떤 로직으로 계산되는지, 그리고 각 피처가 모델 안에서 어떤 방식으로 영향을 주는지까지 설명드리겠습니다.

기존 요약 발표보다 시간을 더 쓰는 이유는, 임원진 관점에서 “이 모델을 신뢰할 수 있는가”, “왜 이런 피처 조합을 쓰는가”, “후처리를 왜 이렇게 해야 하는가”를 판단하려면 계산 로직과 영향도 산출 방식이 분명해야 하기 때문입니다.

오늘 결론은 Warm은 선형 Huber 특성상 피처별 기여도를 직접 설명할 수 있고, Cold는 CatBoost와 LightGBM이 모두 트리형 모델이지만 구조가 다르기 때문에 서로 다른 방식으로 해석하고 보정해야 한다는 것입니다.

---

## 2. 전체 가격 예측 흐름

전체 흐름은 작품 정보가 들어오면 먼저 Warm인지 Cold인지 조건을 나눕니다.

Warm은 같은 작가가 과거 데이터에 있는 경우이고, Cold는 처음 보는 작가이거나 작가 이력이 부족한 경우입니다.

그 다음 모델별로 원 가격을 바로 예측하는 것이 아니라 로그 가격을 먼저 예측합니다. 이유는 미술품 가격의 범위가 매우 넓기 때문입니다. 원 가격을 그대로 예측하면 고가 작품 몇 개가 모델을 과하게 흔들 수 있습니다.

그래서 `log(price)`를 예측하고 마지막에 `exp` 변환으로 원 가격으로 복원합니다.

이후 모델별 후처리 보정을 적용하고, 최종적으로 가격과 함께 신뢰도 또는 위험 구간을 표시하는 방향입니다.

---

## 3. Warm과 Cold를 분리한 이유

Warm과 Cold를 분리한 이유는 가격 판단에 사용할 수 있는 정보가 다르기 때문입니다.

Warm에서는 같은 작가의 과거 데이터가 있으므로, “이 작가는 보통 어느 가격대였는가”가 중요한 기준선이 됩니다.

반면 Cold에서는 작가의 과거 가격대를 알 수 없습니다. 따라서 작품의 크기, 재료, 지지체, 형태 같은 작품 자체 정보가 가격 기준선 역할을 합니다.

이 차이 때문에 같은 피처라도 Warm과 Cold에서 영향도가 다르게 나타나는 것이 정상입니다. 예를 들어 depth는 Warm Huber에서는 영향이 낮지만, Cold CatBoost에서는 size와 결합되면서 중요한 interaction으로 나타납니다.

---

## 4. 최종 모델과 피처 조합

최종 모델은 Warm에 HuberRegressor, Cold에 CatBoost와 LightGBM을 사용했습니다.

Warm Huber는 `size`, `medium_support`, `artist_key` 조합입니다. Warm에서는 작가 이력을 활용할 수 있으므로 artist_key가 가격 기준선 역할을 하고, 크기와 재료/지지체 조합이 그 기준선을 조정합니다.

Cold CatBoost는 `size`, `depth_3d`, `medium/shape` 조합입니다. CatBoost에서는 size가 가격 기준선을 만들고, depth와 medium/shape가 작품 유형을 더 세분화합니다.

Cold LightGBM은 `area/size`, `support_size_bucket` 조합입니다. LightGBM은 면적 의존도가 크고, 대형 캔버스 같은 support-size 구간에서 큰 오차 위험이 확인됐습니다.

---

## 5. 성능 지표를 어떻게 읽는가

이번 보고에서는 MdAPE와 p95 APE를 중심으로 설명드리겠습니다.

MdAPE는 중앙값 기준 절대 비율 오차입니다. 쉽게 말하면 일반적인 예측 오차 수준입니다.

p95 APE는 상위 5%의 큰 오차 수준입니다. 운영 관점에서는 이 수치가 매우 중요합니다. 평균적으로는 괜찮아 보여도 p95가 크면 일부 케이스에서 가격이 크게 틀릴 수 있기 때문입니다.

RMSE_log는 로그 가격 기준 평균 오차이고, Within_30은 30% 이내로 맞춘 비율입니다.

즉, 모델을 볼 때 대표 오차와 큰 오차 위험을 함께 봐야 합니다.

---

## 6. 기준 성능 요약

기준 성능은 최종 artifact를 직접 재해석한 test 기준입니다.

Warm Huber의 MdAPE는 0.2241로 가장 안정적입니다. 이는 Warm 조건에서는 작가 이력을 활용할 수 있기 때문입니다.

Cold CatBoost의 MdAPE는 0.4843이고 p95는 4.4183입니다.

Cold LightGBM의 MdAPE는 0.4797로 CatBoost와 비슷하지만 p95는 5.0569로 더 높습니다.

따라서 Cold LightGBM은 대표 오차는 괜찮아 보이지만, 크게 틀리는 위험은 더 크다고 해석해야 합니다.

---

## 7. Warm Huber 가격 계산 공식

Warm Huber는 선형식으로 로그 가격을 계산합니다.

숫자형 피처는 StandardScaler로 표준화하고, 범주형 피처는 OneHotEncoder로 0과 1 형태로 변환합니다.

그 다음 `intercept + beta × feature`를 모두 더해서 `pred_log_price`를 만듭니다.

마지막으로 `exp(pred_log_price)`를 적용해 원 가격으로 되돌립니다.

이 구조의 장점은 피처별 영향을 직접 계산할 수 있다는 점입니다. 각 피처가 `beta_j × z_j`만큼 로그 가격을 올리거나 내리기 때문입니다.

---

## 8. Huber 손실 함수와 모델 특성

Huber 모델의 핵심은 손실 함수입니다.

일반 선형 회귀는 오차가 커질수록 제곱으로 손실이 커지기 때문에, 특이하게 비싸거나 싼 작품에 강하게 끌려갈 수 있습니다.

Huber는 작은 오차는 제곱 손실로 정밀하게 학습하지만, 일정 기준을 넘는 큰 오차는 선형 손실로 완화합니다.

즉 이상치가 있어도 모델 전체가 과하게 흔들리지 않습니다.

미술품 가격 데이터에는 고가/저가 이상 사례가 존재하기 때문에, Warm에서는 Huber가 안정적인 설명 모델로 적합합니다.

---

## 9. Warm Huber 피처 영향도 계산 방법

Warm Huber에서는 영향도를 다섯 단계로 계산했습니다.

첫째, 계수 `beta_j`를 봅니다. 이 값은 해당 피처가 로그 가격을 올리는 방향인지 내리는 방향인지 보여줍니다.

둘째, 숫자형 피처는 표준화되어 있으므로 원 단위 환산 계수를 봅니다. 예를 들어 cm 단위 기준으로 어느 정도 영향을 주는지 확인합니다.

셋째, 샘플별 기여도를 계산합니다. 계산식은 `beta_j × z_ij`입니다. 이 값은 특정 작품에서 해당 피처가 예측 로그 가격을 얼마나 움직였는지를 뜻합니다.

넷째, 평균 절대 기여도를 봅니다. 전체 test 데이터에서 해당 피처가 실제로 얼마나 자주, 크게 예측값을 움직였는지 확인합니다.

다섯째, 범주형 피처는 one-hot 원계수만 보면 기준 범주 문제로 왜곡될 수 있어 centered contribution으로 해석했습니다.

---

## 10. Warm Huber 피처 영향 결과

Warm에서 가장 큰 영향은 size 그룹이었습니다. 같은 작가라도 큰 작품과 작은 작품은 가격대가 다르기 때문에, size가 가격을 조정하는 기본 축이 됩니다.

두 번째는 medium_support입니다. 같은 크기라도 캔버스인지 종이인지, 어떤 재료인지에 따라 시장에서 받아들이는 가격대가 다릅니다.

artist_key는 Warm 전용 주요 피처입니다. 같은 작가가 학습 데이터에 있으므로, 해당 작가의 과거 가격대가 기준선 역할을 합니다.

depth나 shape는 Warm에서는 낮게 나타났습니다. 이 피처가 무의미하다는 뜻이 아니라, 선형 Huber 구조에서는 depth가 size나 medium과 결합되어 나타나는 복잡한 효과를 직접 표현하기 어렵기 때문입니다.

---

## 11. Warm Huber 조합 판단

Warm의 최종 조합은 `size + medium_support + artist_key`입니다.

이 조합은 단순히 validation 성능이 좋았기 때문이 아니라, 최종 artifact 기준 contribution 분석에서도 핵심 축으로 확인됐기 때문에 타당합니다.

size는 전체 예측값을 가장 많이 움직였고, medium_support는 작품 유형 차이를 설명했으며, artist_key는 기존 작가의 가격 기준선을 제공했습니다.

따라서 Warm 후처리는 이 구조에 맞춰 전체 편향 또는 예측 구간별 로그 잔차 보정으로 가는 것이 자연스럽습니다.

---

## 12. Cold CatBoost 가격 계산 공식

CatBoost는 여러 개의 트리를 더해서 로그 가격을 예측합니다.

각 작품은 트리의 분기 조건을 따라 하나의 leaf에 도달합니다. 각 트리마다 도달한 leaf의 값이 있고, 이 leaf 값들을 모두 더하면 예측 로그 가격이 됩니다.

마지막으로 `exp` 변환을 통해 원 가격으로 복원합니다.

즉 CatBoost의 가격 예측은 “여러 조건 경로를 통과한 결과값의 합”이라고 이해하면 됩니다.

---

## 13. CatBoost 모델 특성

CatBoost의 중요한 특징은 대칭 트리 구조입니다.

같은 depth의 노드가 같은 split 조건을 사용하기 때문에, 단일 피처 하나보다 여러 피처가 어떤 경로에서 함께 작동했는지가 중요합니다.

또 CatBoost는 범주형 피처를 안정적으로 처리하는 장점이 있습니다. 재료나 지지체처럼 문자열 범주가 많은 데이터에서 유리합니다.

그래서 CatBoost 해석에서는 단순 feature importance만 보면 부족하고, SHAP과 interaction, leaf residual을 함께 봐야 합니다.

---

## 14. CatBoost 피처 영향도 계산 방법

CatBoost에서는 네 가지를 봤습니다.

첫째, PredictionValuesChange입니다. 피처 split이 예측값을 얼마나 바꿨는지 보는 전반적 중요도입니다.

둘째, SHAP입니다. 각 샘플 예측에서 피처가 로그 가격을 얼마나 올리거나 내렸는지 계산합니다.

셋째, mean_abs_shap입니다. test 전체에서 피처 영향의 평균 크기를 봅니다.

넷째, interaction score입니다. 두 피처가 같은 예측 경로에서 함께 예측값을 얼마나 바꿨는지 봅니다.

마지막으로 leaf residual을 봤습니다. 특정 leaf나 segment에서 실제값과 예측값의 차이가 반복되는지 확인하기 위한 후처리 후보입니다.

---

## 15. CatBoost 피처 영향 결과

CatBoost에서 SHAP 상위 1~4위는 width, area, log_area, height였습니다. 모두 size 계열입니다.

이는 Cold 조건에서 작가 이력이 없으므로, 작품 크기가 가격 기준선 역할을 하기 때문입니다.

depth_cm은 SHAP 5위이고 interaction 상위 대부분에 포함됐습니다. depth는 단순 치수가 아니라 2D와 3D, 오브제성, 설치 가능성을 구분하는 단서입니다.

특히 width × depth interaction이 1위였습니다. 넓은 작품에 깊이까지 있으면 일반 평면 작품과 다른 시장 분류가 되기 때문입니다.

---

## 16. CatBoost 조합 판단

CatBoost의 최종 조합은 `size + depth_3d + medium/shape`입니다.

size는 Cold에서 가격 기준선을 잡고, depth는 작품 유형을 나누며, medium과 shape는 depth의 의미를 바꿉니다.

예를 들어 같은 depth라도 어떤 재료인지, 어떤 형태인지에 따라 시장 가격 의미가 달라집니다.

따라서 CatBoost 후처리는 단순 전체 보정보다 leaf 또는 segment residual을 확인하고, 표본이 부족하면 medium_shape나 shape/medium 단위로 fallback하는 방식이 맞습니다.

---

## 17. Cold LightGBM 가격 계산 공식

LightGBM도 여러 트리를 더해 로그 가격을 예측합니다.

CatBoost와 마찬가지로 각 트리에서 leaf 값을 얻고, 이 값을 합산합니다. 차이는 learning_rate가 적용되고, 트리가 성장하는 방식이 다르다는 점입니다.

최종적으로는 `base_score + learning_rate × leaf 값의 합`으로 로그 가격을 만들고, `exp`로 원 가격을 복원합니다.

---

## 18. LightGBM 모델 특성

LightGBM은 leaf-wise 방식으로 트리를 성장시킵니다.

쉽게 말하면, 손실을 가장 많이 줄일 수 있는 leaf를 우선적으로 깊게 파고듭니다.

이 방식은 평균 성능을 높이는 데 도움이 될 수 있지만, 일부 좁은 구간에서 과하게 세분화되는 문제가 생길 수 있습니다.

그래서 LightGBM은 대표 오차만 보면 안 되고, p95와 tail slice, leaf-wise 진단을 반드시 봐야 합니다.

---

## 19. LightGBM 피처 영향도 계산 방법

LightGBM에서는 split importance, permutation delta, tail slice, leaf-wise 진단을 함께 봤습니다.

split importance는 트리에서 해당 피처가 얼마나 자주 split에 사용됐는지입니다.

하지만 자주 쓰였다고 실제 예측 의존도가 가장 높다는 뜻은 아닙니다. 그래서 permutation을 수행했습니다. 특정 피처 값을 섞었을 때 예측 오차가 얼마나 악화되는지 확인했습니다.

MdAPE_delta는 대표 오차가 얼마나 악화됐는지, p95_APE_delta는 큰 오차 위험이 얼마나 악화됐는지를 보여줍니다.

마지막으로 tail slice를 봤습니다. 특정 구간, 예를 들어 대형 캔버스에서 오차가 얼마나 커지는지 확인했습니다.

---

## 20. LightGBM 피처 영향 결과

LightGBM에서 가장 큰 영향은 area_cm2였습니다. area_cm2를 permutation했을 때 MdAPE와 p95가 크게 악화됐습니다.

이는 LightGBM이 면적 기준 split을 강하게 사용하고 있다는 뜻입니다.

다만 이것은 장점이자 위험입니다. 면적은 가격 구간을 잘 나누지만, 대형 작품처럼 가격 편차가 큰 구간에서는 큰 오차를 만들 수 있습니다.

실제로 support_size_bucket 중 canvas__q5, 즉 대형 캔버스 구간에서 p95 오차가 가장 높았습니다.

---

## 21. LightGBM 조합 판단

LightGBM의 최종 조합은 `area/size + support_size_bucket`입니다.

area와 size는 모델이 가장 강하게 의존하는 가격 기준선이고, support_size_bucket은 tail risk가 확인된 구간입니다.

따라서 LightGBM은 단순히 평균 정확도를 높이는 것보다, 위험 구간에서 p95를 줄이는 방향으로 후처리하는 것이 맞습니다.

보정도 leaf 자체를 직접 쓰기보다는, 사람이 이해할 수 있는 pred_log bin, size_bucket, support_size_bucket 기준으로 설계하는 것이 맞습니다.

---

## 22. 모델별 영향도 계산 방식 비교

세 모델은 모두 가격을 예측하지만, 피처 영향도를 계산하는 방식은 다릅니다.

Huber는 선형식이기 때문에 계수와 contribution으로 직접 설명합니다.

CatBoost는 대칭 트리이기 때문에 SHAP과 interaction, leaf residual로 설명합니다.

LightGBM은 leaf-wise 트리이기 때문에 permutation과 tail slice, leaf-wise 진단으로 설명합니다.

즉 같은 “크기” 피처라도 모델마다 의미가 다릅니다. Huber에서는 선형 기여도이고, CatBoost에서는 분기 경로이며, LightGBM에서는 leaf 분화와 tail risk입니다.

---

## 23. 피처 조합을 찾은 과정

피처 조합은 단순히 성능이 높은 조합을 고른 것이 아닙니다.

먼저 여러 feature set을 validation에서 비교했고, 후보 조합을 locked test에서 확인했습니다.

그 다음 최종 artifact 기준으로 해석 산출물을 다시 만들었습니다. 기존 해석 스크립트와 최종 피처셋이 불일치했기 때문에 이 과정이 중요했습니다.

마지막으로 모델별 특성에 맞는 영향도 지표를 사용해, 실제로 모델 안에서 예측값을 움직이는 피처 조합인지 확인했습니다.

---

## 24. 1차 후처리 실험 결과

1차 후처리 실험은 residual calibration 기준입니다. 앞의 최종 artifact 재해석 수치와 소폭 차이가 있으므로, 이 표는 보정 전후 방향성을 판단하는 용도로 보면 됩니다.

Warm은 MdAPE가 0.2274에서 0.2211로 개선됐고, p95도 2.0130에서 1.9736으로 개선됐습니다. 따라서 채택 후보입니다.

CatBoost는 p95는 줄었지만 MdAPE가 0.4839에서 0.4880으로 나빠졌습니다. 단순 보정은 보류하고 구조에 맞는 segment fallback 실험이 필요합니다.

LightGBM은 MdAPE가 소폭 나빠졌지만 p95는 4.7612에서 4.2199로 개선됐습니다. 따라서 tail 안정화 후보로 보는 것이 맞습니다.

---

## 25. 모델별 후처리 설계

후처리는 모델별로 다르게 가야 합니다.

Warm Huber는 선형 로그가격 모델이므로 전체 median residual이나 pred_bin별 median residual을 더하는 방식이 자연스럽습니다.

CatBoost는 대칭 트리 경로와 interaction이 중요하므로 leaf나 segment별 residual을 봐야 합니다. 다만 leaf coverage가 낮으면 medium_shape, shape/medium, overall 순서로 fallback해야 합니다.

LightGBM은 leaf-wise tail risk가 문제이므로 pred_log bin, size_bucket, support_size_bucket 기준으로 p95를 줄이는 방향이 맞습니다.

---

## 26. 후처리 보정식

보정은 공통적으로 로그 공간에서 진행합니다.

먼저 `residual_log = actual_log_price - pred_log_price`를 계산합니다.

그 다음 보정 그룹별 대표값을 잡습니다. 대표값은 평균보다 median을 우선합니다. 가격 데이터에는 큰 이상치가 있기 때문에 평균보다 중앙값이 안정적입니다.

이후 `corrected_pred_log = pred_log_price + correction`을 적용하고, 마지막에 `exp`로 가격을 복원합니다.

단, 이 보정값은 test 데이터에서 만들면 안 됩니다. validation 또는 OOF에서 만들고, test는 최종 확인에만 사용해야 합니다.

---

## 27. 향후 실행 계획

향후 실행은 네 단계입니다.

첫째, Warm PP-A1-W를 확정 검증합니다.

둘째, CatBoost segment fallback 실험을 진행합니다.

셋째, LightGBM tail 안정화 실험을 진행합니다.

넷째, 공통적으로 가격 범위와 신뢰도 표시를 검토합니다.

점예측 하나만 제공하면 위험 구간에서 오해가 생길 수 있기 때문에, 큰 오차 가능성이 있는 구간은 신뢰도나 범위 표시가 필요합니다.

---

## 28. 최종 의사결정 요청

최종 의사결정 요청은 네 가지입니다.

첫째, Warm Huber 후처리 보정을 적용 후보로 두고 검증하겠습니다.

둘째, Cold CatBoost는 단순 보정이 아니라 segment fallback 방식으로 재실험하겠습니다.

셋째, Cold LightGBM은 tail risk 완화 목적의 보정 실험을 진행하겠습니다.

넷째, 모델 설명 자료는 최종 artifact 기준 해석 리포트로 교체하겠습니다.

최종 목표는 단순 정확도 개선이 아니라, 크게 틀릴 수 있는 구간을 식별하고 신뢰도와 가격 범위 표시까지 포함해 운영 안정성을 높이는 것입니다.
