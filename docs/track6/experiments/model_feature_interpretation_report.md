# Track6 모델별 개별 피처 영향 해석

- 작성일: `2026-05-31`
- 목적: 단순히 성능이 오른 피처가 아니라, 각 모델 내부에서 해당 피처가 왜 영향력을 가지는지 해석한다.
- 해석 순서: 개별 피처 해석 → 모델별 차이 확인 → 피처 조합 해석으로 확장.

## 해석 기준

| 모델 | 해석 기준 | 의미 |
|---|---|---|
| Warm Huber | 계수, 입력값 × 계수 | 피처가 로그 가격을 올리거나 낮추는 방향과 평균 기여도 |
| Cold CatBoost | feature importance, SHAP | 모델이 해당 피처를 사용한 정도와 개별 예측 기여 방향 |
| Cold LightGBM | 추가 필요 | 현재 동일 수준의 해석 산출물이 없어 별도 생성 필요 |

## 개별 피처 해석표

| 피처 | 도메인 의미 | 성능 근거 | Warm Huber 내부 근거 | Cold CatBoost 내부 근거 | 해석 | 주의점 | 해석 등급 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artist_key / artist_name | 작가 식별 정보 | 성능 판정 Warm=강한 개선, Cold=- / 최고 비교: A1 -> B1 (Warm) / 판단: Warm 핵심 피처입니다. Cold에는 신규 작가 때문에 직접 사용하지 않습니다. | 기여도 artist_name_ko_김상옥타부: 평균\|기여\| 0.0190, 방향 평균적으로 예측가격 상승 / artist_name_ko_김시안: 평균\|기여\| 0.0186, 방향 평균적으로 예측가격 상승 / artist_name_ko_김영성: 평균\|기여\| 0.0113, 방향 평균적으로 예측가격 상승 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | Warm에서는 동일 작가의 과거 가격 수준과 시장 포지션을 직접 반영하는 핵심 기준이다. 신규 작가 중심의 Cold에서는 직접 사용하기 어렵다. | 작가명 효과는 예측 모델의 가격 수준 보정에 가깝다. 작가 자체가 가격을 인과적으로 올린다고 단정하지 않는다. | A |
| log_area / ln_estimated_ho | 작품 크기 | 성능 판정 Warm=소폭 개선, Cold=거의 변화 없음 / 최고 비교: A1 -> A8-1 (Warm) / 판단: 기본 유지. 단독 성능은 제한적이지만 대부분 조합의 기준 축입니다. | 기여도 log_area: 평균\|기여\| 0.6323, 방향 평균적으로 예측가격 상승 / width_cm: 평균\|기여\| 0.0845, 방향 평균적으로 예측가격 상승 / height_cm: 평균\|기여\| 0.0623, 방향 평균적으로 예측가격 상승 / 계수 log_area: coef 0.7385, 예측가격 상승 방향 / width_cm: coef 0.1119, 예측가격 상승 방향 / height_cm: coef 0.0808, 예측가격 상승 방향 | SHAP ln_estimated_ho: mean\|SHAP\| 0.7776, 방향 평균적으로 예측가격 상승 / 중요도 ln_estimated_ho: importance 35.7919, rank 2 | 작품 크기는 가격 산정의 기본 축이다. Warm에서는 선형 계수와 평균 기여도 모두 가격 상승 방향으로 작동하고, Cold에서도 SHAP 상위 피처로 확인된다. | 크기 단독 효과는 제한적일 수 있다. 작가명, 재료, 지지체와 결합될 때 설명력이 커진다. | A |
| width_cm / height_cm | 가로/세로 실측 크기 | 성능 판정 Warm=강한 개선, Cold=- / 최고 비교: B1 -> C1 (Warm) / 판단: Warm 최우선 조합입니다. 작가 효과를 통제한 뒤 실제 크기가 강하게 개선했습니다. | 기여도 width_cm: 평균\|기여\| 0.0845, 방향 평균적으로 예측가격 상승 / height_cm: 평균\|기여\| 0.0623, 방향 평균적으로 예측가격 상승 / 계수 width_cm: coef 0.1119, 예측가격 상승 방향 / height_cm: coef 0.0808, 예측가격 상승 방향 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | Warm Huber에서 가로/세로는 로그면적과 함께 작품 스케일을 보완한다. 작가명으로 가격 수준을 잡은 뒤 실제 크기가 추가 설명력을 제공한다. | 면적과 중복 정보가 있으므로 개별 계수만으로 독립 효과를 과대 해석하지 않는다. | A |
| aspect_ratio / shape_bucket | 작품 형태 | 성능 판정 Warm=거의 변화 없음, Cold=- / 최고 비교: C1 -> D8 (Warm) / 판단: Warm 소폭 개선입니다. 작가별 대형작 프리미엄 후보입니다. | 기여도 aspect_ratio: 평균\|기여\| 0.0137, 방향 평균적으로 예측가격 상승 / 계수 aspect_ratio: coef 0.0260, 예측가격 상승 방향 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | 형태 비율은 가격을 직접 크게 움직이는 핵심 피처라기보다 크기 효과의 안정성을 보조한다. CatBoost 보정에서는 shape segment가 반복 오차를 나누는 후보가 된다. | 단독 영향은 약하다. extreme aspect ratio 같은 위험 구간 해석에 우선 활용한다. | B |
| medium_category / nant_material_idx / nant_tool | 재료 | 성능 판정 Warm=의미 있는 개선, Cold=소폭 개선 / 최고 비교: A1 -> A8 (Warm) / 판단: 작품 변수 조합에서는 의미가 있습니다. Warm/Cold 모두 단독 크기보다 낫습니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | SHAP nant_material_idx: mean\|SHAP\| 0.0422, 방향 평균적으로 예측가격 상승 / nant_tool_아크릴: mean\|SHAP\| 0.0162, 방향 평균적으로 예측가격 하락 / nant_tool_혼합재료: mean\|SHAP\| 0.0154, 방향 평균적으로 예측가격 상승 / 중요도 nant_material_idx: importance 3.2902, rank 5 / nant_tool_아크릴: importance 1.1612, rank 6 / nant_tool_유화: importance 0.5461, rank 8 | 재료는 단독 가격 설명력은 약하지만, Cold에서는 작가 정보가 부족할 때 작품 물성과 제작 방식의 보조 신호로 작동한다. CatBoost SHAP에서도 재료 계열이 상위 보조 피처로 확인된다. | 재료 단독으로 가격을 설명하면 위험하다. 크기/형태/지지체와 조합해 해석해야 한다. | B |
| support_category / nant_support | 지지체 | 성능 판정 Warm=의미 있는 개선, Cold=소폭 개선 / 최고 비교: A8-2 -> A9 (Warm) / 판단: Warm 개선 신호가 있습니다. Cold는 조합과 모델에 따라 제한적입니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | SHAP nant_support_없음: mean\|SHAP\| 0.0107, 방향 평균적으로 예측가격 상승 / nant_support_종이: mean\|SHAP\| 0.0066, 방향 평균적으로 예측가격 하락 / nant_support_캔버스: mean\|SHAP\| 0.0036, 방향 평균적으로 예측가격 상승 / 중요도 nant_support_없음: importance 0.7166, rank 7 / nant_support_종이: importance 0.1924, rank 13 / nant_support_금속: importance 0.1784, rank 15 | 지지체는 단독 영향은 약하지만, 재료 및 크기와 함께 작품의 물성을 구분하는 보조 신호다. Cold에서는 일부 지지체 SHAP 방향이 가격 상승/하락을 나누는 데 사용된다. | 표본 수가 작은 지지체는 해석 불안정성이 크다. 후처리에서는 최소 표본 수 기준이 필요하다. | B |
| artist_meta_total_works | 작가 전체 작품 수 | 성능 판정 Warm=-, Cold=소폭 개선 / 최고 비교: A9 -> G9 (Cold) / 판단: 일부 개선이 있지만 피처 수 대비 효율은 추가 검증 필요입니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | SHAP artist_meta_total_works: mean\|SHAP\| 0.0985, 방향 평균적으로 예측가격 하락 / 중요도 artist_meta_total_works: importance 39.7632, rank 1 | Cold CatBoost에서 높은 중요도를 보이며, 신규 작가의 시장 활동량 또는 데이터 축적 수준을 대체하는 신호로 작동한다. | SHAP 평균 방향이 하락일 수 있어 단순히 작품 수가 많을수록 비싸다고 해석하면 안 된다. 구간별 비선형 관계 확인이 필요하다. | A |
| artist_meta_for_sale_works | 판매 노출 작품 수 | 성능 판정 Warm=-, Cold=의미 있는 개선 / 최고 비교: A9 -> G6 (Cold) / 판단: Cold 핵심 메타 후보입니다. CatBoost와 결합 시 현재 Cold 1순위입니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | SHAP artist_meta_for_sale_works: mean\|SHAP\| 0.1552, 방향 평균적으로 예측가격 상승 / 중요도 artist_meta_for_sale_works: importance 4.3076, rank 4 | Cold SHAP 상위 피처로, 판매 시장에 노출된 작품 수가 신규 작가의 시장성 또는 거래 가능성을 보완하는 신호로 작동한다. | 판매 노출이 많다는 사실이 항상 가격 상승을 뜻하지는 않는다. 총 작품 수, 팔로워, 크기와 함께 해석해야 한다. | A |
| artist_meta_followers | 작가 팔로워/인지도 | 성능 판정 Warm=-, Cold=의미 있는 개선 / 최고 비교: A9 -> CM1-F2 (Cold) / 판단: Cold 현재 1순위 후보입니다. 범주형/비선형 관계를 CatBoost가 잘 처리했습니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | SHAP artist_meta_followers: mean\|SHAP\| 0.0764, 방향 평균적으로 예측가격 하락 / 중요도 artist_meta_followers: importance 11.8141, rank 3 | Cold CatBoost에서 중요도 상위에 있으며, 신규 작가의 대체 시장 인지도 신호로 작동한다. | SHAP 평균 방향이 약하거나 음수일 수 있어 팔로워 수를 선형 가격 프리미엄으로 해석하지 않는다. | B |
| depth_cm / has_depth / is_3d_candidate | 깊이/3D 여부 | 성능 판정 Warm=악화, Cold=소폭 개선 / 최고 비교: C8 -> C9 (Cold) / 판단: 단독 영향은 약하지만 Cold 약점 구간 보정 후보입니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | 단독 성능 개선은 약하지만, 3D/입체 작품은 일반 2D 작품과 오차 구조가 다를 수 있어 위험 구간 태깅과 후처리 후보로 의미가 있다. | 가격 상승 피처라기보다 모델 오차가 커질 수 있는 조건으로 해석하는 편이 안전하다. | C |
| artist_works_log | Warm 작가 학습 이력량 | 성능 판정 Warm=악화, Cold=- / 최고 비교: A9 -> G2 (Warm) / 판단: 작가명 대체는 어렵지만 Warm 신뢰도와 안정성 판단에 유용합니다. | 기여도 artist_works_log: 평균\|기여\| 0.0003, 방향 평균적으로 예측가격 하락 / 계수 artist_works_log: coef 0.0003, 예측가격 상승 방향 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | 작가명을 대체할 만큼의 가격 설명력은 없지만, Warm 모델의 신뢰도와 저이력 작가 위험 구간을 판단하는 데 유용하다. | 가격을 직접 올리는 핵심 피처로 해석하지 않고, 예측 안정성/후처리 조건으로 활용한다. | C |
| artwork_age / 제작연도 | 제작 시점 | 성능 판정 Warm=소폭 개선, Cold=- / 최고 비교: B1 -> C4 (Warm) / 판단: 단독 영향은 약합니다. 운영 입력값으로 받을 수 있으면 보조 후보입니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | 현재 실험에서는 단독 또는 추가 효과가 제한적이다. 운영 입력값으로 받을 수 있으면 보조 후보로 유지한다. | 작가 경력, 작품 시리즈, 재료와 결합하지 않으면 해석력이 약하다. | C |
| edition | 에디션 여부 | 성능 판정 Warm=악화, Cold=거의 변화 없음 / 최고 비교: C8 -> C10 (Cold) / 판단: 단독 영향은 약합니다. 최종 핵심 피처보다는 보조/후처리 후보입니다. | 직접 계수/기여도 근거 없음 또는 보조 해석 대상 | 직접 SHAP/importance 근거 없음 또는 보조 해석 대상 | 현재 결과에서는 핵심 가격 설명 피처로 보기 어렵다. 다만 edition 여부는 작품 유형과 시장 유통 방식의 보조 정보가 될 수 있다. | 단독 영향은 약하므로 최종 핵심 피처로 설명하지 않는다. | D |

## 다음 단계

- 개별 피처 해석 등급 A/B 피처를 중심으로 조합 해석을 진행한다.
- Warm은 `artist_key + 크기`, `artist_key + 크기 + 재료/지지체` 순서로 해석한다.
- Cold는 `크기 + 작가 메타`, `크기 + 재료/지지체`, `시장 노출 + 크기` 순서로 해석한다.
- LightGBM은 SHAP 또는 permutation importance 산출 후 동일 표에 추가한다.