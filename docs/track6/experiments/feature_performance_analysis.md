# Track6 피처별 성과 분석

## 정리 방식

- 1단계: 실험을 피처군 기준으로 묶는다.
- 2단계: 각 피처군에서 Warm/Cold 최고 피처 블록과 모델을 따로 뽑는다.
- 3단계: 해당 피처군에서 어떤 모델이 1위를 자주 했는지 본다.
- 4단계: 성능 수치만 보지 않고, 운영 가능성/Cold 사용 가능성/해석 가능성을 함께 판단한다.
- 5단계: 최종 후보, 보조 후보, 보류 후보로 나눈다.

## 지표 해석 우선순위

- 1순위: `MdAPE`가 낮은지 확인한다. 대표적인 예측 오차를 가장 안정적으로 보여준다.
- 2순위: `p95_APE`가 낮은지 확인한다. 큰 오차가 얼마나 위험한지 보여준다.
- 3순위: `Within_30`이 높은지 확인한다. 실제 가격 대비 30% 이내로 맞춘 비율이다.
- 4순위: `RMSE_log`, `R2`를 보조로 본다. 로그 가격 공간에서 모델이 안정적인지 확인한다.
- `MAPE`는 이상치 영향을 크게 받으므로 결론에는 보조로만 사용한다.

## 피처군별 성과 요약
| 그룹 | 피처군 | 분석 목적 | Warm 최고 피처 | Warm 최고 모델 | Warm MdAPE | Warm p95_APE | Warm Within_30 | Warm 1위 모델 패턴 | Cold 최고 피처 | Cold 최고 모델 | Cold MdAPE | Cold p95_APE | Cold Within_30 | Cold 1위 모델 패턴 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Group A | 작품 변수만 | 작가명을 모르더라도 작품 자체 정보로 가격을 얼마나 설명할 수 있는지 확인 | A8-2 Warm 최고 크기/재료 조합 + NANT 지지체 | Huber | 0.4277 | 2.7593 | 0.3888 | Huber 100회, Ridge 2회 | A11 기준 피처 묶음 + depth/3D | LightGBM | 0.4727 | 6.0589 | 0.3020 | Quantile-LAD 41회, LightGBM 38회, Huber 22회 |
| Group B | 작가명/작가 식별 변수 | 작가 효과가 가격 예측에 얼마나 큰지 확인 | artist_name_ko only | Huber | 0.4352 | 2.8612 | 0.3707 | Huber 3회, Linear Regression 1회, Ridge 1회 | smoothed_target_mean_log | LightGBM | 0.7016 | 7.8928 | 0.2072 | LightGBM 3회, Quantile-LAD 2회 |
| Group C | 작가명 + 작품 변수 | 작가를 통제한 뒤 작품 변수가 추가 설명력을 갖는지 확인 | 작가명 + 전체 크기 묶음 | Huber | 0.1569 | 1.0464 | 0.7364 | Huber 45회 | C8 + 깊이 존재 여부 | LightGBM | 0.4745 | 3.9747 | 0.3059 | LightGBM 40회, Quantile-LAD 5회 |
| Group D | 작품/작가 교차항 | 특정 조건 조합에서 가격 프리미엄이 생기는지 확인 | D8 교차항: 작가명 x 면적 | Huber | 0.1565 | 1.0765 | 0.7282 | Huber 25회 | D2 교차항: 면적 x 난트 지지체 | Quantile-LAD | 0.4745 | 3.3958 | 0.2830 | Quantile-LAD 13회, LightGBM 9회, Huber 3회 |
| Group E | 작가 메타 변수 단독 | 작가명 없이 생년/국적/활동량 같은 작가 메타가 가격을 설명하는지 확인 | 작가명 only | Huber | 0.4352 | 2.8612 | 0.3707 | Huber 14회, Ridge 2회, Linear Regression 1회 | 활동량 + 판매 노출량 + 결측 | Quantile-LAD | 0.6961 | 5.9873 | 0.1965 | Huber 8회, Quantile-LAD 6회, LightGBM 3회 |
| Group F | 작가 메타 묶음 | 여러 작가 메타를 묶었을 때 단독 메타보다 좋아지는지 확인 | 전체 작가 메타 묶음 | Ridge | 0.7311 | 6.7563 | 0.1895 | Ridge 4회, Huber 2회, Linear Regression 2회 | 전체 작가 메타 묶음 | Huber | 0.6956 | 6.6926 | 0.1804 | Quantile-LAD 6회, Huber 2회 |
| Group G | 작품 기본 피처 + 작가 메타 | 작품 조건을 통제한 뒤 작가 메타가 추가로 도움이 되는지 확인 | 작품 기본 피처 + 작가명 | Huber | 0.1831 | 0.9854 | 0.6853 | Huber 24회 | 작품 기본 피처 + 활동량 + 결측 | LightGBM | 0.4577 | 2.9056 | 0.3246 | Quantile-LAD 17회, LightGBM 7회 |
| Group H | 작가명 x 작품 변수 | 같은 작품 조건이라도 작가별 가격 프리미엄이 다른지 확인 | H1 교차항: 작가명 x 호수 | Huber | 0.1762 | 1.0038 | 0.6903 | Huber 4회 | H1 기준: 작가명 + 호수 | LightGBM | 0.5062 | 3.7913 | 0.2646 | LightGBM 4회 |
| Group I | Cold 후보용 작품+메타 조합 | 신규 작가 예측에서 운영 가능한 작가 메타 조합을 찾기 | I6 후보: 실제 크기 확장 + 전체 작가 메타 | Huber | 0.4156 | 2.6607 | 0.3921 | Huber 10회 | I5 후보: 작품 기본 피처 + 시장 노출/정보량 | LightGBM | 0.4598 | 3.0662 | 0.2988 | Quantile-LAD 6회, LightGBM 3회, Huber 1회 |
| Group J | 작가 메타 x 작품 변수 | 작가 메타 수준에 따라 작품 변수 효과가 달라지는지 확인 | J5 교차항: 활동량/인지도 x 면적 | Huber | 0.4754 | 2.5575 | 0.3311 | Huber 13회, Ridge 1회 | J5 교차항: 활동량/인지도 x 면적 | LightGBM | 0.4516 | 3.1609 | 0.3153 | LightGBM 7회, Quantile-LAD 6회, Huber 1회 |

## 피처 관점별 해석
| 피처 관점 | 성과 요약 | 해석 | 판단 | 후속 적용 |
| --- | --- | --- | --- | --- |
| 작품 크기/면적 | Warm/Cold 모두 기본 설명력 있음 | 단독으로는 부족하지만 작가명 또는 재료/지지체와 결합하면 성능 개선 | 유지 | Warm은 전체 크기(width/height/log_area/aspect_ratio), Cold는 로그 호수/로그 면적을 후보로 유지 |
| 재료/지지체 | 단독 성능은 약함 | 작품 물성만으로는 가격 설명력이 제한적이나 조합 피처에서는 보조 설명력 있음 | 조건부 유지 | NANT 재료/지지체 중심으로 사용하고 수집 원문 변수는 비교 후보로 둠 |
| 제작연도/작품 연한 | 단독 성능 약함 | 단독 피처로는 가격대 설명력이 낮고, 작품 기본 피처에 붙여도 개선폭 제한적 | 보류 | 운영 입력 가능성은 있으나 최종 핵심 피처는 아님 |
| 작품 유형/에디션/깊이 | 부분 개선 | Cold 일부 구간에서 LightGBM이 반응하지만 p95가 커 안정성 확인 필요 | 보조 후보 | 신뢰도/위험 구간 태깅에 우선 활용 |
| 작가명 | Warm에서 압도적 | Warm은 작가명이 들어가면 MdAPE가 크게 낮아짐. Cold에서는 신규 작가라 직접 활용 어려움 | Warm 핵심 | Warm 모델에는 artist_name_ko 유지, Cold 모델에는 직접 사용하지 않음 |
| 작가명 + 작품 크기 | Warm 최상위 | 작가 효과에 크기 정보를 더하면 Warm 최고 성능권 형성 | Warm 최종 후보 | Warm Huber 후보의 중심 피처 조합 |
| 작가 메타 | Cold에서 가능성 있음 | 활동량/인지도/정보량 조합이 Cold 상위권에 반복 등장 | Cold 후보 | 추가 수집 품질 검증 후 CatBoost/LightGBM 비교 |
| 교차항 | Warm은 일부 개선, Cold는 제한적 | 작가명 x 면적은 Warm에서 소폭 개선. Cold는 복잡한 교차항이 항상 안정적이지 않음 | 선별 적용 | Warm은 작가명 x 면적/호수 후보, Cold는 활동량 x 크기 후보 중심 |

## Warm 상위 피처/모델 후보
| 실험ID | 그룹 | 피처/변수 블록 | Warm 1위 모델 | Warm MdAPE | Warm p95_APE | Warm Within_30 | Warm 사용 피처 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D8 | D | D8 교차항: 작가명 x 면적 | Huber | 0.1565 | 1.0765 | 0.7282 | artist_name_ko, log_area, log_area_x_artist_name_ko_01, log_area_x_artist_name_ko_02, log_area_x_artist_name_ko_03, log_area_x_artist_name_ko_04, log_area_x_artist_name_ko_05, log_area_x_artist_name_ko_06, log_area_x_artist_name_ko_07, log_area_x_artist_name_ko_08, log_area_x_artist_name_ko_09, log_area_x_artist_name_ko_10, log_area_x_artist_name_ko_11, log_area_x_artist_name_ko_12, log_area_x_artist_name_ko_13, log_area_x_artist_name_ko_14, log_area_x_artist_name_ko_15, log_area_x_artist_name_ko_16, log_area_x_artist_name_ko_17, log_area_x_artist_name_ko_18, log_area_x_artist_name_ko_19, log_area_x_artist_name_ko_20, log_area_x_artist_name_ko_21, log_area_x_artist_name_ko_22, log_area_x_artist_name_ko_23, log_area_x_artist_name_ko_24, log_area_x_artist_name_ko_25, log_area_x_artist_name_ko_26, log_area_x_artist_name_ko_27, log_area_x_artist_name_ko_28, log_area_x_artist_name_ko_29, log_area_x_artist_name_ko_30, log_area_x_artist_name_ko_31, log_area_x_artist_name_ko_32, log_area_x_artist_name_ko_33, log_area_x_artist_name_ko_34, log_area_x_artist_name_ko_35, log_area_x_artist_name_ko_36, log_area_x_artist_name_ko_37, log_area_x_artist_name_ko_38, log_area_x_artist_name_ko_39, log_area_x_artist_name_ko_40, log_area_x_artist_name_ko_41, log_area_x_artist_name_ko_42, log_area_x_artist_name_ko_43, log_area_x_artist_name_ko_44, log_area_x_artist_name_ko_45, log_area_x_artist_name_ko_46, log_area_x_artist_name_ko_47, log_area_x_artist_name_ko_48, log_area_x_artist_name_ko_49, log_area_x_artist_name_ko_50, log_area_x_artist_name_ko_51, log_area_x_artist_name_ko_52, log_area_x_artist_name_ko_53, log_area_x_artist_name_ko_54, log_area_x_artist_name_ko_55, log_area_x_artist_name_ko_56, log_area_x_artist_name_ko_57, log_area_x_artist_name_ko_58, log_area_x_artist_name_ko_59, log_area_x_artist_name_ko_60, log_area_x_artist_name_ko_61, log_area_x_artist_name_ko_62, log_area_x_artist_name_ko_63, log_area_x_artist_name_ko_64, log_area_x_artist_name_ko_65, log_area_x_artist_name_ko_66, log_area_x_artist_name_ko_67, log_area_x_artist_name_ko_68, log_area_x_artist_name_ko_69, log_area_x_artist_name_ko_70, log_area_x_artist_name_ko_71, log_area_x_artist_name_ko_72, log_area_x_artist_name_ko_73, log_area_x_artist_name_ko_74, log_area_x_artist_name_ko_75, log_area_x_artist_name_ko_76, log_area_x_artist_name_ko_77, log_area_x_artist_name_ko_78, log_area_x_artist_name_ko_79, log_area_x_artist_name_ko_80 |
| C1 | C | 작가명 + 전체 크기 묶음 | Huber | 0.1569 | 1.0464 | 0.7364 | artist_name_ko, width_cm, height_cm, log_area, aspect_ratio |
| C1 | C | 작가명 + 로그 면적 | Huber | 0.1578 | 1.0161 | 0.7265 | artist_name_ko, log_area |
| D8 | D | D8 기준: 작가명 + 면적 | Huber | 0.1578 | 1.0161 | 0.7265 | artist_name_ko, log_area |
| H1 | H | H1 교차항: 작가명 x 호수 | Huber | 0.1762 | 1.0038 | 0.6903 | artist_name_ko, ln_estimated_ho, ln_ho_x_artist_name_ko_01, ln_ho_x_artist_name_ko_02, ln_ho_x_artist_name_ko_03, ln_ho_x_artist_name_ko_04, ln_ho_x_artist_name_ko_05, ln_ho_x_artist_name_ko_06, ln_ho_x_artist_name_ko_07, ln_ho_x_artist_name_ko_08, ln_ho_x_artist_name_ko_09, ln_ho_x_artist_name_ko_10, ln_ho_x_artist_name_ko_11, ln_ho_x_artist_name_ko_12, ln_ho_x_artist_name_ko_13, ln_ho_x_artist_name_ko_14, ln_ho_x_artist_name_ko_15, ln_ho_x_artist_name_ko_16, ln_ho_x_artist_name_ko_17, ln_ho_x_artist_name_ko_18, ln_ho_x_artist_name_ko_19, ln_ho_x_artist_name_ko_20, ln_ho_x_artist_name_ko_21, ln_ho_x_artist_name_ko_22, ln_ho_x_artist_name_ko_23, ln_ho_x_artist_name_ko_24, ln_ho_x_artist_name_ko_25, ln_ho_x_artist_name_ko_26, ln_ho_x_artist_name_ko_27, ln_ho_x_artist_name_ko_28, ln_ho_x_artist_name_ko_29, ln_ho_x_artist_name_ko_30, ln_ho_x_artist_name_ko_31, ln_ho_x_artist_name_ko_32, ln_ho_x_artist_name_ko_33, ln_ho_x_artist_name_ko_34, ln_ho_x_artist_name_ko_35, ln_ho_x_artist_name_ko_36, ln_ho_x_artist_name_ko_37, ln_ho_x_artist_name_ko_38, ln_ho_x_artist_name_ko_39, ln_ho_x_artist_name_ko_40, ln_ho_x_artist_name_ko_41, ln_ho_x_artist_name_ko_42, ln_ho_x_artist_name_ko_43, ln_ho_x_artist_name_ko_44, ln_ho_x_artist_name_ko_45, ln_ho_x_artist_name_ko_46, ln_ho_x_artist_name_ko_47, ln_ho_x_artist_name_ko_48, ln_ho_x_artist_name_ko_49, ln_ho_x_artist_name_ko_50, ln_ho_x_artist_name_ko_51, ln_ho_x_artist_name_ko_52, ln_ho_x_artist_name_ko_53, ln_ho_x_artist_name_ko_54, ln_ho_x_artist_name_ko_55, ln_ho_x_artist_name_ko_56, ln_ho_x_artist_name_ko_57, ln_ho_x_artist_name_ko_58, ln_ho_x_artist_name_ko_59, ln_ho_x_artist_name_ko_60, ln_ho_x_artist_name_ko_61, ln_ho_x_artist_name_ko_62, ln_ho_x_artist_name_ko_63, ln_ho_x_artist_name_ko_64, ln_ho_x_artist_name_ko_65, ln_ho_x_artist_name_ko_66, ln_ho_x_artist_name_ko_67, ln_ho_x_artist_name_ko_68, ln_ho_x_artist_name_ko_69, ln_ho_x_artist_name_ko_70, ln_ho_x_artist_name_ko_71, ln_ho_x_artist_name_ko_72, ln_ho_x_artist_name_ko_73, ln_ho_x_artist_name_ko_74, ln_ho_x_artist_name_ko_75, ln_ho_x_artist_name_ko_76, ln_ho_x_artist_name_ko_77, ln_ho_x_artist_name_ko_78, ln_ho_x_artist_name_ko_79, ln_ho_x_artist_name_ko_80 |
| C1 | C | 작가명 + 로그 호수 | Huber | 0.1801 | 0.9846 | 0.7051 | artist_name_ko, ln_estimated_ho |
| C6 | C | 작가명 + 호수 | Huber | 0.1801 | 0.9846 | 0.7051 | artist_name_ko, ln_estimated_ho |
| H1 | H | H1 기준: 작가명 + 호수 | Huber | 0.1801 | 0.9846 | 0.7051 | artist_name_ko, ln_estimated_ho |
| C7 | C | C6 + 작품 연한 | Huber | 0.1821 | 0.9811 | 0.6837 | artist_name_ko, ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artwork_age |
| C6 | C | 작가명 + 작품 기본 피처 묶음 | Huber | 0.1828 | 0.9845 | 0.6870 | artist_name_ko, ln_estimated_ho, nant_material_idx, nant_tool, nant_support |
| C7 | C | C6 기준: 작가명 + 작품 기본 피처 묶음 | Huber | 0.1828 | 0.9845 | 0.6870 | artist_name_ko, ln_estimated_ho, nant_material_idx, nant_tool, nant_support |
| C7 | C | C6 + 제작연도 + 작품 연한 | Huber | 0.1828 | 0.9782 | 0.6870 | artist_name_ko, ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artwork_year, artwork_age |
| C8 | C | C7 기준: C6 + 제작연도 + 작품 연한 | Huber | 0.1828 | 0.9782 | 0.6870 | artist_name_ko, ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artwork_year, artwork_age |
| G1 | G | 작품 기본 피처 + 작가명 | Huber | 0.1831 | 0.9854 | 0.6853 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_name_ko |
| C6 | C | 작가명 + 호수 + NANT 재료 | Huber | 0.1839 | 0.9871 | 0.6853 | artist_name_ko, ln_estimated_ho, nant_material_idx, nant_tool |

## Cold 상위 피처/모델 후보
| 실험ID | 그룹 | 피처/변수 블록 | Cold 1위 모델 | Cold MdAPE | Cold p95_APE | Cold Within_30 | Cold 사용 피처 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| J5 | J | J5 교차항: 활동량/인지도 x 면적 | LightGBM | 0.4516 | 3.1609 | 0.3153 | log_area, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_total_works_x_log_area, artist_meta_for_sale_works_x_log_area, artist_meta_followers_x_log_area, artist_meta_is_p1_x_log_area |
| J4 | J | J4 교차항: 활동량/인지도 x 호수 | LightGBM | 0.4544 | 3.1807 | 0.3211 | ln_estimated_ho, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_total_works_x_ln_ho, artist_meta_for_sale_works_x_ln_ho, artist_meta_followers_x_ln_ho, artist_meta_is_p1_x_ln_ho |
| G6 | G | 작품 기본 피처 + 활동량 + 결측 | LightGBM | 0.4577 | 2.9056 | 0.3246 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing |
| G6 | G | 작품 기본 피처 + 활동량 | LightGBM | 0.4580 | 3.0833 | 0.3243 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works |
| I5 | I | I5 후보: 작품 기본 피처 + 시장 노출/정보량 | LightGBM | 0.4598 | 3.0662 | 0.2988 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score |
| J5 | J | J5 기준: 활동량/인지도 + 면적 | LightGBM | 0.4608 | 3.0955 | 0.3266 | log_area, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 |
| I2 | I | I2 후보: 작품 기본 피처 + 세대/경력 | Quantile-LAD | 0.4643 | 3.4924 | 0.3104 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count |
| G8 | G | 작품 기본 피처 + 기본 작가 프로필 | LightGBM | 0.4645 | 6.0347 | 0.3443 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality |
| J4 | J | J4 기준: 활동량/인지도 + 호수 | LightGBM | 0.4673 | 3.1003 | 0.3088 | ln_estimated_ho, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 |
| G9 | G | 작품 기본 피처 + 전체 작가 메타 | LightGBM | 0.4684 | 3.5812 | 0.3462 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_exhibition_available_count, artist_meta_birth_year_is_missing, artist_exhibition_solo_count_is_missing, artist_exhibition_group_count_is_missing, artist_exhibition_fair_count_is_missing, artist_meta_nationality_is_missing, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing |
| G8 | G | 작품 기본 피처 + 기본 작가 프로필 + 결측 | Quantile-LAD | 0.4690 | 3.5573 | 0.3204 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year, artist_exhibition_solo_count, artist_exhibition_group_count, artist_exhibition_fair_count, artist_meta_nationality, artist_meta_birth_year_is_missing, artist_exhibition_solo_count_is_missing, artist_exhibition_group_count_is_missing, artist_exhibition_fair_count_is_missing, artist_meta_nationality_is_missing |
| G3 | G | 작품 기본 피처 + 생년 | Quantile-LAD | 0.4716 | 3.3639 | 0.3146 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_birth_year |
| I3 | I | I3 후보: 작품 기본 피처 + 활동량/인지도 | LightGBM | 0.4720 | 2.9687 | 0.3191 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 |
| A12 | A | A11 기준 피처 묶음 + depth/3D | LightGBM | 0.4727 | 6.0589 | 0.3020 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artwork_year, artwork_age, artwork_type_final, depth_cm, has_depth, is_3d_candidate |
| D2 | D | D2 교차항: 면적 x 난트 지지체 | Quantile-LAD | 0.4745 | 3.3958 | 0.2830 | log_area, nant_support, log_area_x_nant_support_01, log_area_x_nant_support_02, log_area_x_nant_support_03, log_area_x_nant_support_04, log_area_x_nant_support_05, log_area_x_nant_support_06, log_area_x_nant_support_07, log_area_x_nant_support_08 |

## 결론

- Warm은 `작가명 + 전체 크기` 계열에서 성능이 가장 강하게 나온다.
- Warm 모델은 `Huber`가 대부분의 피처군에서 1위를 차지해 1차 후보로 적합하다.
- Cold는 작가명을 직접 쓸 수 없으므로 `작품 기본 피처 + 작가 메타/활동량/인지도` 조합을 중심으로 봐야 한다.
- Cold 모델은 `LightGBM`이 많은 피처군에서 1위를 차지하지만, 별도 모델군 비교에서 `CatBoost`가 강했으므로 최종 후보군에는 둘 다 유지한다.
- Cold `CatBoost` 실행 시점과 성능 근거는 `cold_catboost_performance_summary.md/html`에 별도로 정리했다.
- 재료/지지체/제작연도/에디션/깊이 등은 단독 핵심 피처라기보다 조합 또는 위험 구간 판단용 보조 피처로 보는 것이 적절하다.
