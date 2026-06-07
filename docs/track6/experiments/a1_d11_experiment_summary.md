# Track6 A1-D11 실험 종합 정리

- 생성일: 2026-05-27
- 목적: A1부터 D11까지의 실험 결과를 지표 해석 기준에 맞춰 종합
- 해석 기준 문서: `docs/track6/experiments/metric_interpretation_standard.md`
- 1순위 지표: `MdAPE`
- 2순위 지표: `p95_APE`
- 3순위 지표: `Within_30`
- 보조 지표: `R2`, `RMSE_log`, `MAPE`

## 핵심 해석 원칙

- Warm과 Cold는 따로 본다.
- 피처 효과는 같은 실험 안에서 같은 모델 기준으로 비교한다.
- 작가명 교차항은 Warm 중심으로 해석한다.
- Cold는 운영에서 작가명이 없는 상황을 가정하므로 작품 변수와 작가 메타 중심으로 본다.
- `RMSE_log`는 일부 실험에 없으므로 전체 결론의 1순위 기준으로 쓰지 않는다.


## A1-D11 기준 1차 결론

### Warm 결론

- Warm에서는 `작가명 + 크기` 계열이 가장 강한 결과를 보였다.
- `C1 작가명 + 크기`는 Warm `MdAPE 0.1569`로 매우 낮고, `D8 작가명 x 면적`도 Warm `MdAPE 0.1565`로 비슷하게 좋았다.
- 다만 `D8`은 교차항이라 복잡도가 높고 `p95_APE`가 `C1`보다 약간 높아, 우선 후보는 단순한 `C1` 쪽이 더 안정적이다.
- `C6 작가명 + 작품 기본 피처`는 Warm `MdAPE 0.1801`로, 작가명과 작품 기본 변수를 함께 쓰는 운영 후보로 볼 수 있다.
- `C7`, `C8`, `C9`, `C10`은 C6 이후 추가 피처를 붙인 실험이지만 Warm 대표 오차는 크게 더 좋아지지 않았다.
- 따라서 Warm 1차 후보는 `작가명 + 크기`, 보조 후보는 `작가명 + 작품 기본 피처`로 정리한다.

### Cold 결론

- Cold에서는 Warm만큼 낮은 오차가 나오지 않았다.
- Cold는 작가명을 직접 사용할 수 없기 때문에 작품 자체 변수의 한계가 분명하다.
- `A12 작품 정보 전체 확장`은 Cold `MdAPE 0.4727`로 가장 낮았다.
- `C9 C8 + 깊이/3D`는 Cold `MdAPE 0.4745`로 근접했고, `D2 면적 x 지지체`도 Cold `MdAPE 0.4745` 수준이었다.
- 다만 Cold의 `p95_APE`는 여전히 큰 편이라 단일 가격 예측만으로 서비스하기에는 위험 구간이 남아 있다.
- 따라서 Cold 1차 후보는 `작품 정보 전체 확장` 또는 `깊이/3D 포함 작품 피처`, 보조 후보는 `면적 x 지지체` 교차항으로 둔다.

### Group A 결론

- 작품 변수만 사용할 때는 단일 피처보다 크기, 재료, 지지체, 유형, 깊이 등을 묶은 조합이 더 낫다.
- `A9`, `A9-6`은 Warm에서 가장 좋은 작품-only 후보였고, `A12`는 Cold에서 가장 좋은 작품-only 후보였다.
- 단일 재료, 단일 지지체, 단일 제작연도만으로는 예측력이 제한적이다.
- 작품 변수는 하나씩 단독 채택하기보다 기본 피처 묶음으로 관리하는 것이 더 적절하다.

### Group B 결론

- 작가명만으로도 Warm에서는 일정한 설명력이 있다.
- 하지만 작품 조건을 통제하지 않은 결과이므로, 작가 효과 확정 근거로는 부족하다.
- Cold에서는 작가명이 직접 의미를 가지지 않으므로 B그룹 결과를 Cold 운영 근거로 쓰면 안 된다.
- B그룹은 “작가명이 중요할 가능성이 있다”는 탐색 근거로만 사용한다.

### Group C 결론

- Group C는 Warm에서 가장 중요한 검증 구간이다.
- 작가명을 넣은 뒤에도 크기 정보가 강한 추가 설명력을 보였다.
- `C1`이 가장 강하고, `C6`도 실무적으로 해석 가능한 후보이다.
- 제작연도, 작품 유형, 깊이, 에디션을 순차 추가한 C7-C10은 큰 개선은 제한적이었다.
- 따라서 Warm 피처 후보는 `artist_name_ko + size 계열`을 우선하고, 확장 피처는 보조로 둔다.

### Group D 결론

- 교차항은 일부 신호가 있으나 복잡도 대비 전면 채택 근거는 제한적이다.
- `D8 작가명 x 면적`은 Warm 성능이 좋지만, `C1`과 성능 차이가 작고 구조가 복잡하다.
- `D2 면적 x 지지체`는 Cold에서 의미 있는 후보로 볼 수 있다.
- `D9`, `D10`, `D11`은 작가명 교차항이라 Warm 중심으로만 해석하고, Cold 운영 근거로 보기는 어렵다.
- 교차항은 최종 모델의 기본 피처가 아니라 후속 후보 또는 약점 구간 보완 후보로 둔다.

### 현재 추천 방향

- Warm 1차 후보: `C1 작가명 + 크기`
- Warm 운영 후보: `C6 작가명 + 작품 기본 피처`
- Cold 1차 후보: `A12 작품 정보 전체 확장`
- Cold 보조 후보: `C9 깊이/3D 포함`, `D2 면적 x 지지체`
- 보류 후보: 복잡도가 높은 작가명 교차항 전반
- 중단 또는 낮은 우선순위: 단일 재료, 단일 지지체, 단일 제작연도만 사용하는 모델

### 다음 확인 필요 사항

- Warm에서는 `C1`과 `C6`을 같은 최종 후보 모델군에서 다시 비교한다.
- Cold에서는 `A12`, `C9`, `D2`를 같은 모델군과 같은 데이터 기준에서 다시 비교한다.
- 최종 후보 비교 단계에서는 누락된 `RMSE_log`를 일괄 계산해 보조 지표로 맞춘다.
- p95 오차가 큰 작품 slice를 확인해 서비스 경고 조건을 설계한다.


## 최적 피처 조합 탐색 결과

### 실험 목적 재정의

- A1-D11의 목적은 개별 피처의 효과를 보는 것에 그치지 않는다.
- 최종 목적은 예측 정확도를 높이는 피처 조합을 찾는 것이다.
- 따라서 A1-D11에서 유망했던 피처를 다시 묶어 `OPT-W1`, `OPT-C1` 추가 실험을 진행했다.
- `OPT-W1`은 Warm 최적 조합 탐색이다.
- `OPT-C1`은 Cold 최적 조합 탐색이다.
- 두 실험은 최신 `artist_name` 포함 split 기준으로 실행했으므로, 예전 split에서 나온 일부 수치와 직접 비교하지 않고 같은 OPT 실험 안에서 비교한다.

### OPT-W1 Warm 최적 조합 결과

| 순위 | 피처 조합 | 모델 | MdAPE | p95 APE | Within-30 | 해석 |
|---:|---|---|---:|---:|---:|---|
| 1 | W1: 작가명 + 전체 크기 | Huber | 0.1566 | 1.0434 | 0.7315 | Warm 최우선 후보 |
| 2 | W8: W3 + 작가명 x 면적 | Huber | 0.1583 | 1.1342 | 0.7100 | 보조 후보 |
| 3 | W7: W4 + 깊이/3D + 에디션 | Huber | 0.1614 | 1.0976 | 0.7117 | 보조 후보 |
| 4 | W5: W4 + 깊이/3D | Huber | 0.1615 | 1.0525 | 0.7100 | 확장 후보 |
| 5 | W4: W3 + 제작연도 + 작품 유형 | Huber | 0.1643 | 1.0617 | 0.7133 | 확장 후보 |


- Warm 최저 MdAPE는 `W1: 작가명 + 전체 크기`였다.
- 확장 피처를 많이 붙인 `W3~W7`은 R2/RMSE_log는 일부 좋아졌지만, MdAPE 기준으로는 W1보다 좋지 않았다.
- `W8: W3 + 작가명 x 면적`은 D8의 교차항 아이디어를 확장했지만 W1보다 MdAPE와 p95가 모두 불리했다.
- 따라서 Warm은 현재 단계에서 `작가명 + 전체 크기`가 가장 단순하고 정확한 후보이다.

### OPT-C1 Cold 최적 조합 결과

| 순위 | 피처 조합 | 모델 | MdAPE | p95 APE | Within-30 | 해석 |
|---:|---|---|---:|---:|---:|---|
| 1 | COLD3: C9형 깊이/3D 포함 작품 피처 | LightGBM | 0.4671 | 6.0962 | 0.3130 | Cold 최우선 후보 |
| 2 | COLD5: A9-6 단순 Cold 후보 | Huber | 0.4795 | 4.5028 | 0.2953 | 큰 오차 안정 후보 |
| 3 | COLD4: C9형 + 에디션 | LightGBM | 0.4796 | 5.9967 | 0.3001 | 보조 후보 |
| 4 | COLD1: A12 작품 정보 전체 확장 | LightGBM | 0.4805 | 5.9262 | 0.2975 | 보조 후보 |
| 5 | COLD5: A9-6 단순 Cold 후보 | Quantile-LAD | 0.4843 | 3.3545 | 0.2833 | 큰 오차 안정 후보 |
| 6 | COLD2: A12 + 면적 x 지지체 | Quantile-LAD | 0.4866 | 3.8171 | 0.2965 | 큰 오차 안정 후보 |


- Cold 최저 MdAPE는 `COLD3: C9형 깊이/3D 포함 작품 피처 + LightGBM`이었다.
- 다만 이 조합은 p95 APE가 높아 큰 오차 위험이 남아 있다.
- `COLD5: A9-6 단순 Cold 후보 + Huber/Quantile-LAD`는 MdAPE는 조금 나쁘지만 p95 APE가 더 안정적이다.
- 따라서 Cold는 단일 최적 후보를 바로 확정하기보다 `정확도 우선 후보`와 `큰 오차 안정 후보`를 나눠 관리하는 것이 맞다.

### 최적 조합 기준 결론

- Warm 최적 후보: `W1: 작가명 + 전체 크기` / `Huber` / MdAPE `0.1566`
- Warm 보조 후보: `W7: W4 + 깊이/3D + 에디션` / `Huber` / MdAPE `0.1614`
- Cold 정확도 후보: `COLD3: C9형 깊이/3D 포함 작품 피처` / `LightGBM` / MdAPE `0.4671`
- Cold 안정성 후보: `COLD5: A9-6 단순 Cold 후보` / `Quantile-LAD` / p95 APE `3.3545`
- 추가 피처를 많이 넣는 것이 항상 성능을 올리지는 않았다.
- Warm은 크기 피처가 핵심이고, Cold는 깊이/3D 포함 작품 피처와 단순 안정 후보를 함께 관리해야 한다.

### 다음 추가 실험 제안

- `OPT-W2`: Warm에서 W1을 기준으로 크기 표현을 줄이는 실험
- `OPT-W2` 목적: `width_cm`, `height_cm`, `log_area`, `aspect_ratio` 중 어떤 조합만 남겨도 성능이 유지되는지 확인
- `OPT-C2`: Cold에서 COLD3와 COLD5를 결합한 하이브리드 실험
- `OPT-C2` 목적: Cold 정확도 후보와 큰 오차 안정 후보를 결합하거나 조건부 라우팅할 수 있는지 확인
- `OPT-C3`: Cold p95 APE 축소 실험
- `OPT-C3` 목적: MdAPE보다 큰 오차 위험을 줄이는 피처/모델 조합을 찾기

## Group A

| 라벨 | 실험 | 목적 | Warm 최고 | Warm MdAPE | Cold 최고 | Cold MdAPE | 해석 |
|---|---|---|---|---:|---|---:|---|
| A1 | [호수/크기 변수 영향 확인](../../../experiments/track6/A1_ho_size_sample_result_sheet/outputs/result_sheet.html) | 호수와 실제 크기 계열만으로 가격 예측력이 생기는지 확인 | Huber / ln Size | 0.5052 | Quantile-LAD / ln Size | 0.4980 | Warm 단독 효과 제한적 / Cold 후보 |
| A1-1 | [Warm Huber 호수 vs 로그 호수 비교](../../../experiments/track6/A1-1_warm_huber_ho_vs_ln_ho/outputs/result_sheet.html) | 같은 Huber 모델에서 원 호수와 로그 호수 중 어떤 표현이 더 안정적인지 확인 | Huber / ln Ho | 0.5244 | - / - | - | Warm 단독 효과 제한적 |
| A2 | [재료 정보 추가 실험](../../../experiments/track6/A2_material_only_collected_vs_nant/outputs/result_sheet.html) | 수집 재료와 NANT 재료 중 어떤 재료 표현이 더 유리한지 확인 | Huber / NANT 재료 번호 | 0.7177 | Huber / NANT 재료 번호 | 0.6977 | Warm 단독 효과 제한적 / Cold 보류 후보 |
| A3 | [지지체 정보 추가 실험](../../../experiments/track6/A3_support_only_collected_vs_nant/outputs/result_sheet.html) | 수집 지지체와 NANT 지지체 중 어떤 지지체 표현이 더 유리한지 확인 | Huber / 수집 지지체 대분류 | 0.7317 | LightGBM / 수집 지지체 대분류 + NANT 지지체 | 0.6843 | Warm 단독 효과 제한적 / Cold 보류 후보 |
| A4 | [제작연도 단독 실험](../../../experiments/track6/A4_artwork_year_only/outputs/result_sheet.html) | 제작연도/작품 연한이 단독으로 가격 설명에 도움이 되는지 확인 | Huber / 제작연도 + 작품 연한 | 0.7491 | LightGBM / 작품 연한 | 0.7119 | Warm 단독 효과 제한적 / Cold 효과 제한적 |
| A4-1 | [제작연도 numeric 전처리 검증](../../../experiments/track6/A4-1_artwork_year_age_standard_scaled/outputs/result_sheet.html) | 제작연도/연한을 숫자형으로 처리했을 때의 효과를 확인 | Huber / artwork_age 단독 | 0.7491 | LightGBM / artwork_age 단독 | 0.7119 | Warm 단독 효과 제한적 / Cold 효과 제한적 |
| A5 | [작품 유형 단독 실험](../../../experiments/track6/A5_artwork_type_only/outputs/result_sheet.html) | 작품 유형 정보가 가격 예측에 도움이 되는지 확인 | Ridge / 유형 보완 전체 구분 | 0.7396 | LightGBM / 작품 유형 전체 구분 | 0.6729 | Warm 단독 효과 제한적 / Cold 보류 후보 |
| A6 | [깊이/3D 단독 실험](../../../experiments/track6/A6_depth_has_depth_only/outputs/result_sheet.html) | 깊이와 3D 후보 정보가 가격 예측에 도움이 되는지 확인 | Huber / 깊이 수치 | 0.7458 | LightGBM / 깊이 수치 + 깊이 존재 여부 | 0.6761 | Warm 단독 효과 제한적 / Cold 보류 후보 |
| A7 | [에디션 정보 단독 실험](../../../experiments/track6/A7_edition_only/outputs/result_sheet.html) | 에디션 정보가 가격 예측에 도움이 되는지 확인 | Huber / 에디션 여부 | 0.7457 | LightGBM / 에디션 여부 | 0.7009 | Warm 단독 효과 제한적 / Cold 효과 제한적 |
| A8 | [크기 + 재료 조합 실험](../../../experiments/track6/A8_size_material_combo/outputs/result_sheet.html) | 크기 정보와 재료 정보를 함께 썼을 때의 효과 확인 | Huber / 로그면적 + NANT 재료 번호 | 0.4764 | Huber / 로그면적 + 수집 재료 대분류 | 0.4919 | Warm 단독 효과 제한적 / Cold 후보 |
| A8-1 | [호수 + 면적 조합 실험](../../../experiments/track6/A8-1_ho_area_combo/outputs/result_sheet.html) | 호수와 면적 계열을 같이 쓰는 것이 유리한지 확인 | Huber / 로그 호수 + 로그 면적 + 가로세로 | 0.4936 | Quantile-LAD / 로그 호수 + 로그 면적 | 0.4952 | Warm 단독 효과 제한적 / Cold 후보 |
| A8-2 | [크기 + 재료 표현 방식 비교](../../../experiments/track6/A8-2_material_representation_size_combo/outputs/result_sheet.html) | 크기에 수집 재료/NANT 재료 표현을 결합했을 때 차이를 확인 | Huber / A8-1 Warm 크기조합 + 수집 재료 원문 묶음 | 0.4432 | Huber / 로그면적 + 수집 재료 대분류 | 0.4919 | Warm 보조 후보 / Cold 후보 |
| A9 | [크기 + 재료 + 지지체 조합 실험](../../../experiments/track6/A9_size_material_support_combo/outputs/result_sheet.html) | 작품 기본 물성 묶음 후보 확인 | Huber / A8-2 Warm 최고 크기/재료 조합 + NANT 지지체 | 0.4277 | Huber / 로그면적 + 수집 재료 대분류 + 수집 지지체 대분류 | 0.4795 | Warm 보조 후보 / Cold 후보 |
| A9-1 | [작품 기본 피처 묶음](../../../experiments/track6/A9-1_basic_artwork_feature_bundle/outputs/result_sheet.html) | 호수, 재료, 지지체를 묶은 기본 작품 피처 후보 확인 | Huber / 호수 + 로그면적 + NANT 재료 + NANT 지지체 | 0.4688 | Quantile-LAD / 호수 + 로그면적 + NANT 재료 + NANT 지지체 | 0.4929 | Warm 단독 효과 제한적 / Cold 후보 |
| A9-2 | [지지체 표현 비교](../../../experiments/track6/A9-2_support_representation_compare/outputs/result_sheet.html) | 수집 지지체와 NANT 지지체 표현 차이 확인 | Huber / 로그면적 + NANT 재료 번호 + NANT 지지체 | 0.4766 | Quantile-LAD / 로그면적 + NANT 재료 번호 + 수집 지지체 + NANT 지지체 | 0.4890 | Warm 단독 효과 제한적 / Cold 후보 |
| A9-3 | [재료 표현 + 지지체](../../../experiments/track6/A9-3_material_representation_with_support/outputs/result_sheet.html) | 재료 표현 방식과 지지체를 함께 썼을 때 차이 확인 | Huber / 로그면적 + 수집 원문 재료 묶음 + NANT 지지체 | 0.4373 | Huber / 로그면적 + 수집 재료 대분류 + NANT 지지체 | 0.4811 | Warm 보조 후보 / Cold 후보 |
| A9-4 | [크기 표현 + 재료/지지체](../../../experiments/track6/A9-4_size_representation_with_material_support/outputs/result_sheet.html) | 크기 표현 방식이 작품 기본 피처 조합에 미치는 영향 확인 | Huber / 전체 크기 + NANT 재료 + NANT 지지체 | 0.4739 | Quantile-LAD / 로그면적 + NANT 재료 + NANT 지지체 | 0.4934 | Warm 단독 효과 제한적 / Cold 후보 |
| A9-5 | [재료+지지체 조합 버킷](../../../experiments/track6/A9-5_material_support_combo_bucket/outputs/result_sheet.html) | 재료와 지지체 조합 버킷의 추가 효과 확인 | Huber / 전체 크기 + 재료지지체 조합 | 0.4740 | Quantile-LAD / 로그면적 + NANT 재료 + NANT 지지체 | 0.4935 | Warm 단독 효과 제한적 / Cold 후보 |
| A9-6 | [Warm/Cold 피처셋 분리](../../../experiments/track6/A9-6_warm_cold_feature_set_split/outputs/result_sheet.html) | Warm과 Cold에 같은 작품 피처를 쓸지 분리할지 확인 | Huber / Warm 후보: 전체 크기 + 원문 재료 묶음 + NANT 지지체 | 0.4277 | Huber / Cold 후보: 로그면적 + 수집 재료 대분류 + 수집 지지체 대분류 | 0.4795 | Warm 보조 후보 / Cold 후보 |
| A10 | [작품 기본 피처 + 제작연도](../../../experiments/track6/A10_basic_artwork_features_plus_year/outputs/result_sheet.html) | 작품 기본 피처에 제작연도/연한을 추가했을 때 효과 확인 | Huber / 작품 기본 피처 묶음 | 0.4962 | LightGBM / 작품 기본 피처 묶음 + 작품 연한 | 0.4999 | Warm 단독 효과 제한적 / Cold 후보 |
| A11 | [작품 기본 피처 + 작품 유형](../../../experiments/track6/A11_basic_artwork_features_plus_type/outputs/result_sheet.html) | 작품 기본 피처에 작품 유형을 추가했을 때 효과 확인 | Huber / A10 기준 피처 묶음 + 작품 유형 전체 구분 | 0.4804 | LightGBM / A10 기준 피처 묶음 + 작품 유형 전체 구분 | 0.4816 | Warm 단독 효과 제한적 / Cold 후보 |
| A12 | [작품 정보 전체 확장](../../../experiments/track6/A12_full_artwork_features_expanded/outputs/result_sheet.html) | 작품 변수 확장 묶음이 최종 후보가 될 수 있는지 확인 | Huber / A11 기준 피처 묶음 + edition | 0.4733 | LightGBM / A11 기준 피처 묶음 + depth/3D | 0.4727 | Warm 단독 효과 제한적 / Cold 후보 |

## Group B

| 라벨 | 실험 | 목적 | Warm 최고 | Warm MdAPE | Cold 최고 | Cold MdAPE | 해석 |
|---|---|---|---|---:|---|---:|---|
| B1 | [작가명 단독 실험](../../../experiments/track6/B1_artist_name_only/outputs/result_sheet.html) | 작가명만으로 가격대가 어느 정도 설명되는지 확인 | Huber / artist_name_ko only | 0.4352 | LightGBM / artist_name_ko only | 0.7018 | Warm 보조 후보 / Cold 효과 제한적 / 작품 조건 통제 전 탐색 결과 |
| B2 | [작가명 처리 방식 비교](../../../experiments/track6/B2_artist_name_encoding_compare/outputs/result_sheet.html) | 작가명 입력 방식에 따라 성능이 달라지는지 확인 | Huber / one_hot | 0.4352 | LightGBM / smoothed_target_mean_log | 0.7016 | Warm 보조 후보 / Cold 효과 제한적 / 작품 조건 통제 전 탐색 결과 |

## Group C

| 라벨 | 실험 | 목적 | Warm 최고 | Warm MdAPE | Cold 최고 | Cold MdAPE | 해석 |
|---|---|---|---|---:|---|---:|---|
| C1 | [작가명 + 크기](../../../experiments/track6/C1_artist_name_plus_size/outputs/result_sheet.html) | 작가명을 넣은 뒤에도 크기 정보가 추가 설명력을 가지는지 확인 | Huber / 작가명 + 전체 크기 묶음 | 0.1569 | LightGBM / 작가명 + 원 호수 | 0.5062 | Warm 성능 강함 / Cold 보류 후보 |
| C2 | [작가명 + 재료](../../../experiments/track6/C2_artist_name_plus_material/outputs/result_sheet.html) | 작가명을 넣은 뒤에도 재료 정보가 추가 설명력을 가지는지 확인 | Huber / 작가명 + NANT 재료 번호 + 도구명 | 0.4209 | Quantile-LAD / 작가명 + NANT 재료 번호 | 0.6999 | Warm 보조 후보 / Cold 보류 후보 |
| C3 | [작가명 + 지지체](../../../experiments/track6/C3_artist_name_plus_support/outputs/result_sheet.html) | 작가명을 넣은 뒤에도 지지체 정보가 추가 설명력을 가지는지 확인 | Huber / 작가명 + 수집 지지체 대분류 | 0.4209 | LightGBM / 작가명 + NANT 지지체 | 0.6891 | Warm 보조 후보 / Cold 보류 후보 |
| C4 | [작가명 + 제작연도](../../../experiments/track6/C4_artist_name_plus_year/outputs/result_sheet.html) | 작가명을 넣은 뒤에도 제작연도/연한이 추가 설명력을 가지는지 확인 | Huber / 작가명 + 제작연도 | 0.4300 | LightGBM / B1 기준: 작가명 only | 0.7018 | Warm 보조 후보 / Cold 효과 제한적 |
| C5 | [작가명 + 작품 유형](../../../experiments/track6/C5_artist_name_plus_type/outputs/result_sheet.html) | 작가명을 넣은 뒤에도 작품 유형이 추가 설명력을 가지는지 확인 | Huber / 작가명 + 작품 유형 3대 구분 | 0.4263 | LightGBM / 작가명 + 작품 유형 전체 + 3대 구분 | 0.6758 | Warm 보조 후보 / Cold 보류 후보 |
| C6 | [작가명 + 작품 기본 피처](../../../experiments/track6/C6_artist_name_plus_artwork_basic/outputs/result_sheet.html) | 작가명과 작품 기본 피처 묶음의 기준 성능 확인 | Huber / 작가명 + 호수 | 0.1801 | LightGBM / 작가명 + 작품 기본 피처 묶음 | 0.4956 | Warm 성능 강함 / Cold 후보 |
| C7 | [C6 + 제작연도](../../../experiments/track6/C7_artist_name_plus_artwork_basic_year/outputs/result_sheet.html) | C6에 제작연도/연한을 추가했을 때 효과 확인 | Huber / C6 + 작품 연한 | 0.1821 | LightGBM / C6 기준: 작가명 + 작품 기본 피처 묶음 | 0.4956 | Warm 성능 강함 / Cold 후보 |
| C8 | [C7 + 작품 유형](../../../experiments/track6/C8_artist_name_plus_artwork_basic_year_type/outputs/result_sheet.html) | C7에 작품 유형을 추가했을 때 효과 확인 | Huber / C7 기준: C6 + 제작연도 + 작품 연한 | 0.1828 | LightGBM / C7 + 작품 유형 전체 구분 | 0.4813 | Warm 성능 강함 / Cold 후보 |
| C9 | [C8 + 깊이/3D](../../../experiments/track6/C9_c8_plus_depth/outputs/result_sheet.html) | C8에 깊이/입체성 정보를 추가했을 때 효과 확인 | Huber / C8 + 깊이 존재 여부 | 0.1852 | LightGBM / C8 + 깊이 존재 여부 | 0.4745 | Warm 성능 강함 / Cold 후보 |
| C10 | [C8 + 에디션](../../../experiments/track6/C10_c8_plus_edition/outputs/result_sheet.html) | C8에 에디션 정보를 추가했을 때 효과 확인 | Huber / C8 + 리미티드 에디션 여부 | 0.1846 | LightGBM / C8 + 리미티드 에디션 여부 | 0.4799 | Warm 성능 강함 / Cold 후보 |

## Group D

| 라벨 | 실험 | 목적 | Warm 최고 | Warm MdAPE | Cold 최고 | Cold MdAPE | 해석 |
|---|---|---|---|---:|---|---:|---|
| D1 | [면적 x 재료 교차항](../../../experiments/track6/D1_log_area_material_numeric_interaction/outputs/result_sheet.html) | 큰 특정 재료 작품의 프리미엄이 있는지 확인 | Huber / D1 교차항: 면적 x 난트 재료번호 | 0.4747 | Quantile-LAD / D1 기준: 면적 + 난트 재료 | 0.4979 | Warm 단독 효과 제한적 / Cold 후보 |
| D2 | [면적 x 지지체 교차항](../../../experiments/track6/D2_log_area_support_numeric_interaction/outputs/result_sheet.html) | 큰 특정 지지체 작품의 프리미엄이 있는지 확인 | Huber / D2 기준: 면적 + 난트 지지체 | 0.4892 | Quantile-LAD / D2 교차항: 면적 x 난트 지지체 | 0.4745 | Warm 단독 효과 제한적 / Cold 후보 |
| D3 | [재료 x 지지체 교차항](../../../experiments/track6/D3_material_support_categorical_interaction/outputs/result_sheet.html) | 재료와 지지체 조합 효과 확인 | Huber / D3 조합: 난트 재료번호 x 지지체 | 0.7177 | Huber / D3 조합: 난트 재료번호 x 지지체 | 0.6977 | Warm 단독 효과 제한적 / Cold 보류 후보 |
| D4 | [작품 연한 x 재료 교차항](../../../experiments/track6/D4_artwork_age_material_numeric_interaction/outputs/result_sheet.html) | 오래된 특정 재료의 가격 효과 확인 | Huber / D4 교차항: 연한 x 난트 도구명 | 0.7311 | LightGBM / D4 기준: 연한 + 난트 재료 | 0.7015 | Warm 단독 효과 제한적 / Cold 효과 제한적 |
| D5 | [작품 연한 x 지지체 교차항](../../../experiments/track6/D5_artwork_age_support_numeric_interaction/outputs/result_sheet.html) | 오래된 특정 지지체의 가격 효과 확인 | Huber / D5 교차항: 연한 x 난트 지지체 | 0.7390 | Quantile-LAD / D5 기준: 연한 + 난트 지지체 | 0.7028 | Warm 단독 효과 제한적 / Cold 효과 제한적 |
| D6 | [깊이 x 작품 유형 교차항](../../../experiments/track6/D6_depth_artwork_type_numeric_interaction/outputs/result_sheet.html) | 입체성 효과가 작품 유형별로 달라지는지 확인 | Huber / D6 교차항: 깊이 x 작품 유형 전체 | 0.7463 | LightGBM / D6 교차항: 깊이 x 작품 유형 전체 | 0.6467 | Warm 단독 효과 제한적 / Cold 보류 후보 |
| D8 | [작가명 x 면적 교차항](../../../experiments/track6/D8_artist_log_area_numeric_interaction/outputs/result_sheet.html) | 작가별 대형작 프리미엄 확인 | Huber / D8 교차항: 작가명 x 면적 | 0.1565 | Quantile-LAD / D8 교차항: 작가명 x 면적 | 0.5071 | Warm 성능 강함 / Cold 보류 후보 / 작가명 교차항은 Warm 중심 해석 |
| D9 | [작가명 x 재료 교차항](../../../experiments/track6/D9_artist_material_categorical_interaction/outputs/result_sheet.html) | 특정 작가의 특정 재료 프리미엄 확인 | Huber / D9 기준: 작가명 + 난트 재료 | 0.4209 | Quantile-LAD / D9 기준: 작가명 + 난트 재료 | 0.7025 | Warm 보조 후보 / Cold 효과 제한적 / 작가명 교차항은 Warm 중심 해석 |
| D10 | [작가명 x 지지체 교차항](../../../experiments/track6/D10_artist_support_categorical_interaction/outputs/result_sheet.html) | 특정 작가의 특정 지지체 프리미엄 확인 | Huber / D10 기준: 작가명 + 난트 지지체 | 0.4250 | LightGBM / D10 기준: 작가명 + 난트 지지체 | 0.6891 | Warm 보조 후보 / Cold 보류 후보 / 작가명 교차항은 Warm 중심 해석 |
| D11 | [작가명 x 작품 연한 교차항](../../../experiments/track6/D11_artist_artwork_age_numeric_interaction/outputs/result_sheet.html) | 작가별 특정 시기 작품 가치 확인 | Huber / D11 교차항: 작가명 x 작품 연한 | 0.4206 | LightGBM / D11 교차항: 작가명 x 작품 연한 | 0.7025 | Warm 보조 후보 / Cold 효과 제한적 / 작가명 교차항은 Warm 중심 해석 |

## 종합 메모

- Group A는 작가명 없이 작품 자체 변수의 기본 설명력을 확인하는 구간이다.
- Group B는 작가 변수의 단독 설명력을 보는 탐색 구간이며, 작품 조건을 통제하지 않으므로 단독 결론으로 확정하지 않는다.
- Group C는 작가명을 넣은 뒤에도 작품 변수가 추가 설명력을 가지는지 보는 핵심 Warm 검증 구간이다.
- Group D는 조합 프리미엄을 보는 구간이며 복잡도가 높으므로 작은 개선만으로 채택하지 않는다.
- 최종 피처 후보는 `MdAPE` 개선, `p95_APE` 악화 여부, `Within_30` 개선 여부를 함께 보고 결정한다.