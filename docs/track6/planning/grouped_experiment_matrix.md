# Track6 그룹형 실험 설계표

## 목적

- 작품 가격 예측 실험을 빠뜨리지 않기 위해 실험군을 먼저 나눈다.
- 각 실험군 안에서 단일 변수, 변수 묶음, 변수 조합을 순서대로 검증한다.
- 기존 Track6 실험 일지를 아래 그룹 구조에 연결해 어떤 실험이 이미 준비됐고, 어떤 실험이 추가로 필요한지 확인한다.

## 실험 평가 방식

| 평가 방식 | 의미 | 확인하려는 것 |
|---|---|---|
| Random Split | 작품 단위로 train/test를 나누는 방식 | 전체 평균 성능과 일반적인 예측 가능성 확인 |
| GroupKFold by artist | 같은 작가가 train/test에 동시에 들어가지 않게 나누는 방식 | 작가명이 섞여서 성능이 좋아 보이는 문제를 방지하고, 신규 작가 상황에 가까운 성능 확인 |

## 모델군 통제 기준

- 피처 효과를 확인하는 실험은 모델군을 고정한다.
- 기본 Warm 모델군: `Huber`, `Linear Regression`, `Ridge`
- 기본 Cold 모델군: `Huber`, `Quantile-LAD`, `LightGBM`
- 이 기준은 피처 추가, 피처 제거, 피처 조합, 단일 변수 확인 실험에 적용한다.
- 예외는 모델 자체를 비교하는 실험이다. 예: `T6-E014`, `T6-E015`, `T6-E016`, `T6-E017`, `T6-E034`, `T6-E035`
- 가격 범위, 라우팅, 최종 정책 실험은 선정된 최종 후보 모델을 사용하므로 기본 모델군 통제 대상에서 제외한다.

## 실험군 요약

| 실험군 | 피처 구성 | 목적 | 핵심 질문 |
|---|---|---|---|
| Group A | 작품 변수만 | 작품 자체 정보의 설명력 확인 | 작가명을 모르는 상태에서도 작품 정보만으로 가격을 어느 정도 설명할 수 있는가? |
| Group B | 작가 변수만 | 작가 변수의 단독 설명력 탐색 | 작품 조건을 통제하지 않은 상태에서도 작가 변수만으로 가격대가 어느 정도 구분되는가? |
| Group C | 작품 기본 피처 묶음 + 작가 변수 | 작품 조건을 통제한 뒤 작가 변수의 추가 설명력 확인 | 호수·재료·지지체 등 작품 조건을 넣은 뒤에도 작가 변수가 성능을 개선하는가? |
| Group D | 작품 기본 피처 묶음 + 작가명 x 작품 변수 교차항 | 작가명에 따라 작품 변수 효과가 달라지는지 확인 | 같은 크기·재료·지지체라도 작가명에 따라 가격 프리미엄이 달라지는가? |
| Group E | 작가 메타 묶음/정보량 | 작가명 없이 작가 메타 묶음의 설명력 확인 | 단일 작가 메타 실험을 반복하지 않고, 생년·경력·국적·활동량·인지도 묶음 또는 결측 정보가 가격 예측에 도움 되는가? |
| Group F | 작품 변수 + 작가 메타 묶음 | 작가명을 쓰지 않는 운영 가능 변수 조합 확인 | 작품 정보와 작가 메타 묶음을 함께 쓰면 Warm/Cold 예측 성능을 개선할 수 있는가? |
| Group G | 작품 기본 피처 묶음 + 작가 메타 묶음 x 작품 변수 교차항 | 작가 메타 조건에 따라 작품 변수 효과가 달라지는지 확인 | 같은 크기·재료·지지체의 작품이라도 작가의 경력, 활동량, 인지도에 따라 가격 효과가 달라지는가? |

## 작가 중심 신규 실험 가설 리스트

- 이 표는 상사 예시를 참고해 새로 만드는 Track6 작가 중심 실험 설계안이다.
- 작품 변수만 보는 `A` 그룹은 우선순위를 낮추는 것이 아니라, 작가 효과를 검증하기 위한 기본 피처 묶음을 정하는 단계로 사용한다.
- 작가 영향 검증은 `작품 조건을 통제한 뒤 작가 변수를 추가했을 때 성능이 좋아지는가`를 기준으로 판단한다.
- `B`는 작가 변수만 단독으로 넣어 보는 탐색 실험이다. 작품 조건을 통제하지 않으므로 이것만으로 작가 영향이 확정되지는 않는다.
- `C`는 작품 기본 피처 묶음에 작가 변수를 추가하는 실험이다. 작가 영향 판단의 핵심 그룹이다.
- `D`는 작품 기본 피처 묶음에 작가명과 작품 변수의 교차항을 추가하는 실험이다.
- `G`는 작품 기본 피처 묶음에 작가 메타 묶음과 작품 변수의 교차항을 추가하는 실험이다.
- `+`는 피처를 함께 넣는다는 뜻이고, `x`는 두 피처의 조합 효과를 만든다는 뜻이다.
- 작가명 한글화와 동명이인 처리는 이미 데이터셋 정제 단계에서 반영된 전제 조건으로 두고, 신규 실험 번호에서는 제외한다.
- 기존 `T6-E###` 일지가 있으면 연결하고, 없으면 신규 실험 후보로 둔다.
- `only` 단일 변수 실험은 `Group B`에서만 관리한다. `Group E/F`는 단일 변수를 반복하지 않고, 작가 메타 묶음과 작품 변수 결합 효과만 확인한다.
- `Group D`는 작가명 자체와 작품 변수의 교차항만 다룬다.
- `Group G`는 `Group D`와 겹치지 않도록 작가명 자체가 아니라 작가 메타 묶음과 작품 변수의 교차항만 다룬다.
- 작가 영향 검증의 비교 기준은 `작품 기본 피처 묶음`으로 둔다. 즉, 호수·난트 재료·난트 지지체를 먼저 넣고 작가 변수를 추가한다.
- 작품 기본 피처 묶음에 쓰는 실제 피처는 `ln_estimated_ho`, `nant_material_idx`, `nant_tool`, `nant_support`다.
- `support_category`는 `nant_support`와 중복되는 지지체 대분류 성격이므로 기준선에서는 제외한다. 필요하면 A14 하위 실험에서만 참고한다.

### A 그룹 참조 정의

| 참조 라벨 | 제목 | 사용 피처 | 의미 |
|---|---|---|---|
| A1 | 호수 변수 영향 확인 | ln_estimated_ho | 호수 단독 영향 확인 |
| A2 | 실제 크기 정보 추가 실험 | width_cm, height_cm, log_area, aspect_ratio | 호수 외 실제 크기 효과 확인 |
| A3 | 크기 대표값 vs 전체 크기 피처 실험 | ln_estimated_ho vs width/height/log_area/aspect_ratio | 대표 크기와 전체 크기 비교 |
| A4 | 긴 변/짧은 변 크기 피처 실험 | max_side_cm, min_side_cm | 면적 대비 긴 변/짧은 변 효과 확인 |
| A5 | 가로/세로 변수 영향 확인 | width_cm, height_cm | 가로/세로 단독 추가 효과 확인 |
| A6 | 면적/로그면적 변수 영향 확인 | area_cm2, log_area | 면적 표현 방식 효과 확인 |
| A7 | 가로세로 비율 변수 영향 확인 | aspect_ratio | 형태 비율 효과 확인 |
| A8 | 재료 정보 추가 실험 | nant_material_idx, nant_tool | 재료 효과 확인 |
| A9 | 난트 재료 분류 그룹화 실험 | nant_material_idx, nant_material_group | 난트 세분화/그룹화 비교 |
| A10 | 재료 대분류 변수 영향 확인 | medium_category | 난트 재료 변수와 중복되어 제외 |
| A11 | 난트 재료 번호 변수 영향 확인 | nant_material_idx | 난트 재료 번호 추가 효과 확인 |
| A12 | 원본 재료 문구 변수 영향 확인 | collected_material_raw keyword flags | 원본 재료 문구 키워드 효과 확인 |
| A13 | 지지체 정보 후보 비교 실험 | support_category, nant_support | 기본 지지체와 난트 지지체 중 최종 후보 확인 |
| A14 | 지지체 대분류 변수 영향 확인 | support_category | 난트 지지체와 중복되므로 기준선에서는 제외하고 참고용으로만 확인 |
| A15 | 난트 지지체 변수 영향 확인 | nant_support | 난트 지지체 추가 효과 확인 |
| A16 | 작품 제목 키워드 피처 실험 | title_raw keyword flags | 작품 유형/에디션 키워드 효과 확인 |
| A17 | 깊이/3D 정보 추가 실험 | depth_cm, has_depth, is_3d_candidate | 입체성 정보 효과 확인 |
| A18 | 깊이 구간화 피처 실험 | depth_bucket | 깊이 구간화 효과 확인 |
| A19 | 깊이 변수 영향 확인 | depth_cm | 깊이 단독 효과 확인 |
| A20 | 3D 후보 플래그 변수 영향 확인 | has_depth, is_3d_candidate | 3D 여부 플래그 효과 확인 |
| A21 | 재료 x 호수 조합 피처 실험 | nant_material_idx_x_ho_bucket | 같은 호수 내 재료 차이 확인 |
| A22 | 단계적 피처 선택 절차 실험 | size, material, support, depth 계열 후보 | 작품 변수 후보 축소 절차 확인 |
| A23 | Warm/Cold 작품 피처 분리 실험 | Warm/Cold feature sets | 작품 피처셋 분리 필요성 확인 |
| A24 | 지지체 x 재료 조합 실험 | nant_material_support_bucket, nant_support_nant_tool_bucket | 재료와 지지체 조합 효과 확인 |
| A25 | 재료+지지체 조합 변수 영향 확인 | nant_material_support_bucket | 재료+지지체 조합 단독 효과 확인 |

### 작가 실험 전제 조건

| 항목 | 현재 처리 | 실험 번호 부여 여부 |
|---|---|---|
| 작가명 한글화 | `artist_name_ko` 기준으로 정제 완료 | 별도 실험 번호 제외 |
| 동명이인 처리 | 작가 식별 안정화를 위해 정제 단계에서 반영 | 별도 실험 번호 제외 |
| 작가 ID | 운영 입력값이 아니므로 최종 피처 후보에서 제외 | 별도 실험 번호 제외 |
| 작가명 encoding 방식 | 상사 예시의 모델 구현 방식 검토 항목이며, 피처 효과 가설은 아님 | 별도 실험 번호 제외 |


### Group B: 작가 변수만

- 목적: 작가 변수만으로 가격대가 어느 정도 구분되는지 보는 탐색 실험이다.
- 주의: 작품 조건을 통제하지 않으므로 `B` 결과만으로 작가 효과를 확정하지 않는다.
- 작가 영향의 본 판단은 `Group C`에서 작품 기본 피처 묶음을 통제한 뒤 확인한다.

| 신규 라벨 | 피처 구성 | 실험 가설 | 목적 | 기존 일지 | 상태 |
|---|---|---|---|---|---|
| B1 | artist_name_ko only | 작가명만으로도 작품 가격대의 일부를 설명할 수 있다 | 작가명 단독 설명력 탐색 | T6-E012, T6-E054 | 기존 일지 있음 |
| B2 | artist_works_log | 학습 데이터 안에 작품 수가 많은 작가일수록 예측이 안정적일 수 있다 | 작가별 데이터 보유량 단독 효과 탐색 | T6-E067 | 기존 일지 있음 |
| B3 | artist_meta_birth_year | 작가의 생년 또는 세대 정보가 가격 차이를 설명할 수 있다 | 세대별 가격대 차이 탐색 | T6-E073 | 기존 일지 있음 |
| B4 | artist_meta_career_stage | 작가의 경력 단계가 가격 차이를 설명할 수 있다 | 신진/중견/원로 등 경력 단계 단독 효과 탐색 | T6-E075 | 기존 일지 있음 |
| B5 | artist_meta_nationality | 작가 국적 정보가 가격 차이를 설명할 수 있다 | 국적별 가격대 차이 탐색 | T6-E076 | 기존 일지 있음 |
| B6 | artist_meta_total_works / for_sale_works | 작가의 활동량과 판매 노출량이 가격 예측에 도움 될 수 있다 | 등록 작품 수와 판매 중 작품 수 단독 효과 탐색 | T6-E078, T6-E079 | 기존 일지 있음 |
| B7 | artist_meta_followers / is_p1 | 작가의 플랫폼 인지도 정보가 가격 예측에 도움 될 수 있다 | 팔로워 수와 주요 작가 여부 단독 효과 탐색 | T6-E081, T6-E082 | 기존 일지 있음 |

### Group C: 작품 기본 피처 묶음 + 작가 변수

- 목적: 작품 조건을 통제한 뒤 작가 변수를 추가했을 때 성능이 좋아지는지 확인한다.
- 기본 비교 방식: `작품 기본 피처 묶음` vs `작품 기본 피처 묶음 + 작가 변수`.
- 작품 기본 피처 묶음: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support`.
- 작가 영향 판단은 `B`보다 `C` 결과를 우선한다.

| 신규 라벨 | 피처 구성 | 실험 가설 | 목적 | 기존 일지 | 상태 |
|---|---|---|---|---|---|
| C1 | 기본 피처 묶음 vs 기본 피처 묶음 + B1 | 호수·재료·지지체를 통제한 뒤에도 작가명이 가격 예측력을 높일 수 있다 | 작품 조건 통제 후 작가명 효과 확인 | T6-E010, T6-E017 | 기존 일지 있음 |
| C2 | 기본 피처 묶음 vs 기본 피처 묶음 + B2 | 작품 조건을 통제한 뒤에도 작가별 데이터 보유량이 예측 안정성에 도움 될 수 있다 | 작품 조건 통제 후 작가 이력량 효과 확인 | T6-E067 | 기존 일지 있음 |
| C3 | 기본 피처 묶음 vs 기본 피처 묶음 + B3 | 작품 조건을 통제한 뒤에도 작가 생년/세대 정보가 가격 차이를 설명할 수 있다 | 작품 조건 통제 후 세대 효과 확인 | T6-E073 | 기존 일지 있음 |
| C4 | 기본 피처 묶음 vs 기본 피처 묶음 + B4 | 작품 조건을 통제한 뒤에도 작가 경력 단계가 가격 차이를 설명할 수 있다 | 작품 조건 통제 후 경력 단계 효과 확인 | T6-E075 | 기존 일지 있음 |
| C5 | 기본 피처 묶음 vs 기본 피처 묶음 + B5 | 작품 조건을 통제한 뒤에도 작가 국적 정보가 가격 차이를 설명할 수 있다 | 작품 조건 통제 후 국적 효과 확인 | T6-E076 | 기존 일지 있음 |
| C6 | 기본 피처 묶음 vs 기본 피처 묶음 + B6 | 작품 조건을 통제한 뒤에도 작가 활동량/판매 노출량이 가격 예측에 도움 될 수 있다 | 작품 조건 통제 후 활동량 효과 확인 | T6-E078, T6-E079 | 기존 일지 있음 |
| C7 | 기본 피처 묶음 vs 기본 피처 묶음 + B7 | 작품 조건을 통제한 뒤에도 작가 인지도 정보가 가격 예측에 도움 될 수 있다 | 작품 조건 통제 후 인지도 효과 확인 | T6-E081, T6-E082 | 기존 일지 있음 |
| C8 | 기본 피처 묶음 vs 기본 피처 묶음 + E3 | 작품 조건을 통제한 뒤에도 기본 작가 프로필 묶음이 예측력을 높일 수 있다 | 작품 조건 통제 후 기본 메타 묶음 효과 확인 | [T6-E088](../../experiments/track6/T6-E088_artwork_basic_profile_meta_combo/experiment_log.html) | 일지 있음 |
| C9 | 기본 피처 묶음 vs 기본 피처 묶음 + E5 | 작품 조건을 통제한 뒤에도 전체 작가 메타 묶음이 예측력을 높일 수 있다 | 작품 조건 통제 후 전체 메타 묶음 효과 확인 | [T6-E091](../../experiments/track6/T6-E091_artist_meta_full_bundle/experiment_log.html) | 일지 있음 |
| C10 | 기본 피처 묶음 + B2 구간별 라우팅 | 학습 작품 수가 적은 작가는 Warm보다 Cold 방식이 더 안정적일 수 있다 | 저이력 작가 fallback 기준 확인 | [T6-E101](../../experiments/track6/T6-E101_low_history_artist_routing/experiment_log.html) | 일지 있음 |

### Group D: 작품 기본 피처 묶음 + 작가명 x 작품 변수 교차항

- 목적: 작품 조건을 통제한 뒤, 작가명에 따라 작품 변수 효과가 달라지는지 확인한다.
- 기본 비교 방식: `작품 기본 피처 묶음 + B1` vs `작품 기본 피처 묶음 + B1 + 교차항`.
- `D`는 작가명 자체와 작품 변수의 교차항만 다룬다.
- 작가 메타와 작품 변수의 교차항은 `Group G`에서 관리한다.

| 신규 라벨 | 교차항 | 실험 가설 | 목적 | 기존 일지 | 상태 |
|---|---|---|---|---|---|
| D1 | B1 x A1 | 같은 호수라도 작가명에 따라 가격대가 다를 수 있다 | 작가별 호수 프리미엄 확인 | T6-E025 | 기존 일지 있음 |
| D2 | B1 x A6 | 같은 면적이라도 작가명에 따라 가격대가 다를 수 있다 | 작가별 면적 프리미엄 확인 | [T6-E102](../../experiments/track6/T6-E102_artist_log_area_interaction/experiment_log.html) | 일지 있음 |
| D3 | B1 x A8 | 같은 재료라도 작가명에 따라 가격 프리미엄이 다를 수 있다 | 작가별 재료 프리미엄 확인 | [T6-E103](../../experiments/track6/T6-E103_artist_material_interaction/experiment_log.html) | 일지 있음 |
| D4 | B1 x A15 | 같은 난트 지지체라도 작가명에 따라 가격 프리미엄이 다를 수 있다 | 작가별 난트 지지체 프리미엄 확인 | [T6-E104](../../experiments/track6/T6-E104_artist_support_interaction/experiment_log.html) | 일지 있음 |
| D5 | B1 x A17 | 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다를 수 있다 | 작가별 입체성 프리미엄 확인 | [T6-E105](../../experiments/track6/T6-E105_artist_depth_interaction/experiment_log.html) | 일지 있음 |

### Group E: 작가 메타 조합별 묶음

| 신규 라벨 | 피처 구성 | 실험 가설 | 목적 | 기존/신규 일지 | 상태 |
|---|---|---|---|---|---|
| E1 | B3 + B4 | 작가 생년과 경력 단계를 함께 쓰면 세대/경력 가격대 차이를 더 잘 설명할 수 있다 | 세대+경력 조합 효과 확인 | [T6-E083](../../experiments/track6/T6-E083_artist_meta_generation_career_bundle/experiment_log.html) | 일지 있음 |
| E2 | B6 + B7 | 작가 활동량과 인지도 정보를 함께 쓰면 시장 노출 효과를 더 잘 설명할 수 있다 | 활동량+인지도 조합 효과 확인 | [T6-E084](../../experiments/track6/T6-E084_artist_meta_activity_popularity_bundle/experiment_log.html) | 일지 있음 |
| E3 | B3 + B4 + B5 | 작가 생년, 경력, 국적을 함께 쓰면 기본 작가 프로필 효과를 설명할 수 있다 | 기본 작가 프로필 조합 확인 | [T6-E089](../../experiments/track6/T6-E089_artist_meta_basic_profile_bundle/experiment_log.html) | 일지 있음 |
| E4 | B6 + B7 + artist_meta_missing_flags + artist_meta_completeness_score | 활동량/인지도 정보와 정보량 피처를 함께 쓰면 신뢰도 판단에 도움이 될 수 있다 | 시장 노출+정보량 조합 확인 | [T6-E090](../../experiments/track6/T6-E090_artist_meta_market_info_bundle/experiment_log.html) | 일지 있음 |
| E5 | B3 + B4 + B5 + B6 + B7 | 작가명 없이 전체 작가 메타 묶음만으로 가격 예측력이 생길 수 있다 | 작가명 대체 가능성 최종 확인 | [T6-E091](../../experiments/track6/T6-E091_artist_meta_full_bundle/experiment_log.html) | 일지 있음 |

### Group F: 작품 변수 + 작가 메타 조합

| 신규 라벨 | 피처 구성 | 실험 가설 | 목적 | 기존/신규 일지 | 상태 |
|---|---|---|---|---|---|
| F1 | A1 + E1 | 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아질 수 있다 | 최소 크기+기본 메타 조합 확인 | [T6-E085](../../experiments/track6/T6-E085_ho_generation_career_meta_combo/experiment_log.html) | 일지 있음 |
| F2 | 작품 기본 피처 묶음 + E1 | 호수, 난트 재료, 난트 지지체, 세대/경력 메타를 함께 쓰면 Cold 예측력이 개선될 수 있다 | 작품 기본 변수+기본 메타 조합 확인 | [T6-E086](../../experiments/track6/T6-E086_artwork_basic_generation_career_meta_combo/experiment_log.html) | 일지 있음 |
| F3 | 작품 기본 피처 묶음 + E2 | 작품 기본 변수와 활동량/인지도 메타를 함께 쓰면 시장 노출 효과를 반영할 수 있다 | 작품 기본 변수+시장 노출 메타 조합 확인 | [T6-E087](../../experiments/track6/T6-E087_artwork_basic_activity_popularity_meta_combo/experiment_log.html) | 일지 있음 |
| F4 | 작품 기본 피처 묶음 + E3 | 작품 기본 변수와 기본 작가 프로필을 함께 쓰면 운영 가능한 Cold 후보가 될 수 있다 | 운영 가능 기본 프로필 조합 확인 | [T6-E088](../../experiments/track6/T6-E088_artwork_basic_profile_meta_combo/experiment_log.html) | 일지 있음 |
| F5 | 작품 기본 피처 묶음 + E4 | 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄일 수 있다 | 신뢰도/결측 보정 후보 확인 | [T6-E092](../../experiments/track6/T6-E092_artwork_basic_market_info_combo/experiment_log.html) | 일지 있음 |
| F6 | A2 + A5 + A6 + A7 + E5 | 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적일 수 있다 | 크기 확장+전체 메타 효과 확인 | [T6-E093](../../experiments/track6/T6-E093_full_size_full_artist_meta_combo/experiment_log.html) | 일지 있음 |

### Group G: 작품 기본 피처 묶음 + 작가 메타 묶음 x 작품 변수 교차항

- 목적: 작품 조건과 작가 메타를 함께 넣은 뒤, 특정 작가 메타 조건에서 작품 변수 효과가 달라지는지 확인한다.
- 기본 비교 방식: `작품 기본 피처 묶음 + E묶음` vs `작품 기본 피처 묶음 + E묶음 + 교차항`.
- `G`는 작가명 자체를 쓰지 않고 작가 메타와 작품 변수의 조합 효과만 본다.

| 신규 라벨 | 교차항 | 실험 가설 | 목적 | 기존/신규 일지 | 상태 |
|---|---|---|---|---|---|
| G1 | E1 x A1 | 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타날 수 있다 | 세대/경력별 호수 프리미엄 확인 | [T6-E094](../../experiments/track6/T6-E094_generation_career_x_ho_interaction/experiment_log.html) | 일지 있음 |
| G2 | E1 x A8 | 작가의 세대/경력 단계에 따라 재료 효과가 다르게 나타날 수 있다 | 세대/경력별 재료 프리미엄 확인 | [T6-E095](../../experiments/track6/T6-E095_generation_career_x_material_interaction/experiment_log.html) | 일지 있음 |
| G3 | E1 x A15 | 작가의 세대/경력 단계에 따라 난트 지지체 효과가 다르게 나타날 수 있다 | 세대/경력별 난트 지지체 프리미엄 확인 | [T6-E096](../../experiments/track6/T6-E096_generation_career_x_support_interaction/experiment_log.html) | 일지 있음 |
| G4 | E2 x A1 | 작가의 활동량/인지도에 따라 호수 효과가 다르게 나타날 수 있다 | 활동량/인지도별 호수 프리미엄 확인 | [T6-E097](../../experiments/track6/T6-E097_activity_popularity_x_ho_interaction/experiment_log.html) | 일지 있음 |
| G5 | E2 x A6 | 작가의 활동량/인지도에 따라 면적 효과가 다르게 나타날 수 있다 | 활동량/인지도별 대형작 프리미엄 확인 | [T6-E098](../../experiments/track6/T6-E098_activity_popularity_x_area_interaction/experiment_log.html) | 일지 있음 |
| G6 | E3 x A8 | 작가 기본 프로필에 따라 재료 효과가 다르게 나타날 수 있다 | 기본 프로필별 재료 프리미엄 확인 | [T6-E099](../../experiments/track6/T6-E099_profile_meta_x_material_interaction/experiment_log.html) | 일지 있음 |
| G7 | E4 x A17 | 작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타날 수 있다 | 정보량별 3D/깊이 효과 확인 | [T6-E100](../../experiments/track6/T6-E100_market_info_x_depth_interaction/experiment_log.html) | 일지 있음 |

## 상사 예시 기준 기존 일지 참고 매핑표

- 아래 표의 `A1`, `B1`, `C1`, `D1`은 상사가 작성한 예시 기준을 참고한 매핑이다.
- 기존 `T6-E###`는 실제 생성된 Track6 실험 일지 번호이다.
- 한 상사 예시 라벨에 여러 `T6-E###`가 연결될 수 있다.
- 정확히 맞지 않는 실험은 `부분 매칭` 또는 `기타 실험`으로 분리한다.

### Group A: 작품 변수만

| 상사 라벨 | 피처 구성 | 목적 | 매칭된 Track6 일지 | 매칭 판단 |
|---|---|---|---|---|
| A1 | 크기만 | 작품 크기 효과 확인 | T6-E039, T6-E040, T6-E047, T6-E053, T6-E055, T6-E056, T6-E057 | 매칭 |
| A2 | 재료만 | 재료 효과 확인 | T6-E041, T6-E052, T6-E063, T6-E065 | 매칭 |
| A3 | 지지체만 | 지지체 효과 확인 | T6-E042, T6-E059, T6-E064 | 매칭 |
| A4 | 제작연도만 | 제작 시기 효과 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| A5 | 작품 유형만 | 회화/판화/조각 차이 확인 | T6-E049, T6-E066 | 부분 매칭, 제목 키워드 기반 |
| A6 | depth / has_depth | 입체성 정보 효과 확인 | T6-E043, T6-E051, T6-E061, T6-E062 | 매칭 |
| A7 | edition / signed | 에디션·서명 효과 확인 | T6-E049, T6-E066 | 부분 매칭, 구조화 필요 |
| A8 | 크기 + 재료 | 물리 크기와 재료 결합 효과 확인 | T6-E044, T6-E024 | 매칭, 일부 통합 검토 |
| A9 | 작품 기본 피처 묶음 | 호수 + 난트 재료 + 난트 지지체 기준의 기본 작품 물성 모델 | T6-E045, T6-E046, T6-E026, T6-E060 | 매칭 |
| A10 | 작품 기본 피처 묶음 + 제작연도 | 제작 시기 반영 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| A11 | 작품 기본 피처 묶음 + 제작연도 + 작품 유형 | 작품 자체 정보 전체 모델 | 없음 | 제작연도/작품유형 구조화 필요 |
| A12 | 작품 기본 피처 묶음 + 제작연도 + 작품 유형 + depth/has_depth + edition/signed | 작품 정보 전체 모델 확장 | T6-E043, T6-E049, T6-E066 | 부분 매칭 |

### Group B: 작가명만 / 작가 변수만

| 상사 라벨 | 피처 구성 | 목적 | 매칭된 Track6 일지 | 매칭 판단 |
|---|---|---|---|---|
| B1 | artist_name only | 작가명 하나로 가격이 얼마나 설명되는지 확인 | T6-E012, T6-E054 | 매칭, Warm 전용 |
| B2 | artist_works_log | 데이터 내 작가 작품 수가 예측에 도움 되는지 확인 | T6-E067 | 매칭, 생성 변수 |
| B3 | artist_meta_birth_year | 작가 생년/세대 효과 확인 | T6-E073 | 매칭 |
| B4 | artist_meta_career_stage | 작가 경력 단계 효과 확인 | T6-E075 | 매칭 |
| B5 | artist_meta_nationality | 국적 정보 효과 확인 | T6-E076 | 매칭 |
| B6 | total_works / for_sale_works | 작가 활동량·시장 노출 효과 확인 | T6-E078, T6-E079 | 매칭 |
| B7 | followers / is_p1 | 작가 인지도/플랫폼 주요 작가 효과 확인 | T6-E081, T6-E082 | 매칭 |

### Group C: 작품 기본 피처 묶음 + 작가 변수

| 상사 라벨 | 피처 구성 | 목적 | 매칭된 Track6 일지 | 매칭 판단 |
|---|---|---|---|---|
| C1 | 작가명 + 크기 | 작가 통제 후 크기 효과 확인 | T6-E010, T6-E017, T6-E040, T6-E047, T6-E055, T6-E056, T6-E057 | 매칭 |
| C2 | 작가명 + 재료 | 작가 통제 후 재료 효과 확인 | T6-E041, T6-E052, T6-E063, T6-E065 | 부분 매칭, 작가명 포함 여부 확인 필요 |
| C3 | 작가명 + 지지체 | 작가 통제 후 지지체 효과 확인 | T6-E042, T6-E059, T6-E064 | 부분 매칭, 작가명 포함 여부 확인 필요 |
| C4 | 작가명 + 제작연도 | 작가 통제 후 제작연도 효과 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| C5 | 작가명 + 작품 유형 | 작가 통제 후 작품 유형 효과 확인 | T6-E049, T6-E066 | 부분 매칭 |
| C6 | 작가명 + 작품 기본 피처 묶음 | 작가 통제 후 기본 물성 효과 확인 | T6-E046, T6-E032 | 매칭 |
| C7 | C6 + 제작연도 | 제작 시기 추가 효과 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| C8 | C7 + 작품 유형 | 작품 정보 전체 모델 | 없음 | 구조화 필요 |
| C9 | C8 + depth/has_depth | 입체성 추가 효과 확인 | T6-E043, T6-E051, T6-E061, T6-E062 | 부분 매칭 |
| C10 | C8 + edition/signed | 에디션·서명 추가 효과 확인 | T6-E049, T6-E066 | 부분 매칭 |

### Group D: 교차항

| 상사 라벨 | 교차항 | 목적 | 매칭된 Track6 일지 | 매칭 판단 |
|---|---|---|---|---|
| D1 | log_area x material | 큰 유화, 큰 아크릴 등의 프리미엄 확인 | T6-E044, T6-E024 | 부분 매칭, 현재는 ho_bucket 중심 |
| D2 | log_area x support | 큰 캔버스, 큰 종이 작품 차이 확인 | [T6-E107](../../experiments/track6/T6-E107_log_area_support_interaction/experiment_log.html) | 일지 있음 |
| D3 | material x support | oil on canvas, ink on paper 조합 효과 확인 | T6-E026, T6-E060 | 매칭 |
| D4 | artwork_age x material | 오래된 특정 재료의 가치 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| D5 | artwork_age x support | 오래된 종이/캔버스의 차이 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| D6 | depth x artwork_type | 조각/입체작에서 depth 효과 확인 | T6-E043, T6-E062 | 부분 매칭 |
| D7 | 비워둠 | 상사 표 기준 미정 항목 | 없음 | 보류 |
| D8 | artist_name x log_area | 작가별 대형작 프리미엄 확인 | T6-E025 | 부분 매칭, 현재는 작가명 x 호수 |
| D9 | artist_name x material | 특정 작가의 특정 재료 프리미엄 확인 | [T6-E103](../../experiments/track6/T6-E103_artist_material_interaction/experiment_log.html) | 일지 있음 |
| D10 | artist_name x support | 특정 작가의 특정 지지체 프리미엄 확인 | [T6-E104](../../experiments/track6/T6-E104_artist_support_interaction/experiment_log.html) | 일지 있음 |
| D11 | artist_name x artwork_age | 작가별 특정 시기 작품 가치 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |

### 기타 실험

| 구분 | Track6 일지 | 기타로 분리한 이유 |
|---|---|---|
| 모델 비교 | T6-E014, T6-E015, T6-E016, T6-E017, T6-E034, T6-E035 | 상사 라벨은 피처 실험 중심이고, 해당 일지는 모델군 비교/선정 목적 |
| Cold 전용 모델 | T6-E029, T6-E033, T6-E035 | 작가명 없이 신규 작가를 예측하는 Cold 전용 실험이라 A/B/C/D 피처표와 목적이 다름 |
| 라우팅/정책 | T6-E030, T6-E031, T6-E036, T6-E037 | 피처 효과보다 Warm/Cold 분기, 위험 구간, 가격 범위 정책 확인 목적 |
| 데이터 품질/운영 리스크 | AX1~AX8 | 작가명 정제, 동명이인, 작가 DB 커버리지 등 실험 운영 품질 검증 목적 |

## Group A: 작품 변수만

| 실험 | 사용 피처 | 목적 | 기존 일지 | 현재 상태 |
|---|---|---|---|---|
| A1 | 호수, 가로, 세로, 면적, 로그면적, 가로세로 비율, 긴 변/짧은 변 | 작품 크기 효과 확인 | T6-E039, T6-E040, T6-E047, T6-E053, T6-E055, T6-E056, T6-E057 | 일지 있음 |
| A2 | 재료, 난트 재료 번호, 난트 도구, 원본 재료 문구 | 재료 효과 확인 | T6-E041, T6-E052, T6-E058, T6-E063, T6-E065 | 일지 있음 |
| A3 | 지지체, 난트 지지체 | 지지체 효과 확인 | T6-E042, T6-E059, T6-E064 | 일지 있음 |
| A4 | 제작연도 | 제작 시기 효과 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| A5 | 작품 유형, 제목 기반 유형 키워드 | 회화/판화/조각/에디션 등 유형 차이 확인 | T6-E049, T6-E066 | 부분 일지 있음, 구조화 피처 정의 필요 |
| A6 | 깊이, 깊이 존재 여부, 3D 후보 여부 | 입체성 정보 효과 확인 | T6-E043, T6-E051, T6-E061, T6-E062 | 일지 있음 |
| A7 | edition, signed | 에디션/서명 효과 확인 | T6-E049, T6-E066 | 부분 일지 있음, 제목/재료 문구에서 파생 필요 |
| A8 | 크기 + 재료 | 물리 크기와 재료 결합 효과 확인 | T6-E044, T6-E024 | 일지 있음 |
| A9 | 작품 기본 피처 묶음 | 호수 + 난트 재료 + 난트 지지체 기준의 기본 작품 물성 모델 확인 | T6-E045, T6-E046, T6-E026, T6-E060 | 일지 있음 |
| A10 | 작품 기본 피처 묶음 + 제작연도 | 제작 시기 반영 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 보류 일지 있음 |
| A11 | 작품 기본 피처 묶음 + 제작연도 + 작품 유형 | 작품 자체 정보 전체 모델 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | 제작연도 보류 일지 있음 |
| A12 | 작품 기본 피처 묶음 + 제작연도 + 작품 유형 + depth/has_depth + edition/signed | 작품 정보 전체 모델 확장 | T6-E043, T6-E049, T6-E066 일부 연결 | depth는 가능, edition/signed는 파생 필요 |

## Group B: 작가 변수만

| 실험 | 사용 피처 | 목적 | 기존 일지 | 현재 상태 |
|---|---|---|---|---|
| B1 | 작가명 한글 | 작가명 자체 효과 확인 | T6-E012, T6-E054 | 일지 있음, Warm 전용 판단 |
| B2 | 작가별 데이터 보유 작품 수 | 데이터 내 작가 이력량 효과 확인 | T6-E067 | 일지 있음, 생성 변수 |
| B3 | 작가 생년 | 작가 세대/연령 효과 확인 | T6-E073 | 일지 있음, 결측 영향 확인 필요 |
| B4 | 작가 국적 | 국적 효과 확인 | T6-E076 | 일지 있음, 결측 영향 확인 필요 |
| B5 | 작가 경력 단계 | 경력 단계 효과 확인 | T6-E075 | 일지 있음, 결측 영향 확인 필요 |
| B6 | 등록 작품 수, 판매 중 작품 수, 팔로워 수, 플랫폼 주요 작가 여부 | 작가 활동량/인지도 효과 확인 | T6-E078, T6-E079, T6-E081, T6-E082 | 일지 있음, 수집 출처 편향 주의 |

## Group C: 작품 기본 피처 묶음 + 작가 변수

| 실험 | 사용 피처 | 목적 | 기존 일지 | 현재 상태 |
|---|---|---|---|---|
| C1 | 작가명 + 호수 | Warm 기본 예측 가능성 확인 | T6-E010, T6-E014, T6-E015, T6-E017 | 일지 있음 |
| C2 | 작품 기본 피처 묶음 + 작가명 + 크기 묶음 | 작품 조건 통제 후 크기 효과 확인 | T6-E040, T6-E047, T6-E055, T6-E056, T6-E057 | 일지 있음 |
| C3 | 작품 기본 피처 묶음 + 작가명 + 난트 재료/지지체 | 작품 조건 통제 후 작품 물성 효과 확인 | T6-E041, T6-E042, T6-E046 | 일지 있음 |
| C4 | 작가명 + 작품 변수 + 작가 메타 | 작가 메타가 Warm 성능을 추가 개선하는지 확인 | T6-E027, T6-E028, T6-E032, T6-E073~E082 | 일부 일지 있음 |
| C5 | Cold용 작품 변수 모델 | 작가명 없이 신규 작가를 예측하는 후보 확인 | T6-E016, T6-E029, T6-E033, T6-E035 | 일지 있음 |

## 작가 관련 실험 순서표

### 작가 실험 평가 방식

| 평가 방식 | 목적 | 주의점 |
|---|---|---|
| Random Split | 전체 평균 성능과 작가 정보의 단기 설명력 확인 | 같은 작가가 train/test에 섞이면 작가명 효과가 과대평가될 수 있음 |
| GroupKFold by artist | 작가명이 섞였을 때 생기는 착시 성능 방지 | 신규 작가 상황에 가까우므로 Warm 성능과 따로 해석 |
| Warm Test | 학습 데이터에 같은 작가가 있는 작품 예측 | 작가명, 작가별 학습 이력 수, 작가별 과거 패턴 사용 가능 |
| Cold Test | 학습 데이터에 없는 작가 작품 예측 | 작가명 자체는 사용하지 않고, 운영에서 확보 가능한 작가 메타만 별도 검토 |

### Group B: 작가 변수만

| 실험 | 사용 피처 | 목적 | 기존 일지 | 적용 범위 | 상태 |
|---|---|---|---|---|---|
| B1 | 작가명 한글 only | 작가명 하나만으로 가격대가 얼마나 설명되는지 확인 | T6-E012, T6-E054 | Warm 전용 | 일지 있음 |
| B2 | artist_works_log | 데이터 안에서 해당 작가 작품 수가 예측에 도움 되는지 확인 | T6-E067 | Warm 전용 생성 변수 | 일지 있음 |
| B3 | artist_meta_birth_year | 작가 생년/세대가 가격 설명에 도움 되는지 확인 | T6-E073 | Warm / Cold 모두 가능, 메타 필요 | 일지 있음 |
| B4 | career_stage | 작가 경력 단계가 가격 설명에 도움 되는지 확인 | T6-E075 | Warm / Cold 모두 가능, 메타 필요 | 일지 있음 |
| B5 | artist_meta_nationality | 국적 정보가 가격 차이를 설명하는지 확인 | T6-E076 | Warm / Cold 모두 가능, 메타 필요 | 일지 있음 |
| B6 | total_works, for_sale_works | 작가 활동량/시장 노출 정보가 가격 설명에 도움 되는지 확인 | T6-E078, T6-E079 | Warm / Cold 모두 가능, 외부 수집값 필요 | 일지 있음 |
| B7 | followers, is_p1 | 작가 인지도/플랫폼 주요 작가 여부가 가격 설명에 도움 되는지 확인 | T6-E081, T6-E082 | Warm / Cold 모두 가능, 외부 수집값 필요 | 일지 있음 |
| B8 | 작가 메타 결측 여부 flag | 메타 정보가 없는 작가 자체가 오차 증가와 관련 있는지 확인 | [T6-E106](../../experiments/track6/T6-E106_artist_meta_missing_flag_check/experiment_log.html) | Warm / Cold 모두 가능 | 일지 있음 |

### Group C: 작품 기본 피처 묶음 + 작가 변수

| 실험 | 사용 피처 | 목적 | 기존 일지 | 적용 범위 | 상태 |
|---|---|---|---|---|---|
| C1 | 작가명 + 호수 | 작가명과 호수 조합의 추가 효과 확인 | T6-E010, T6-E014, T6-E015, T6-E017 | Warm 중심 | 일지 있음 |
| C2 | 작품 기본 피처 묶음 + 작가명 + 크기 묶음 | 작품 조건을 통제한 뒤 실제 크기 표현의 효과 확인 | T6-E040, T6-E047, T6-E055~E057 | Warm 중심 | 일지 있음 |
| C3 | 작가명 + 난트 재료 | 특정 작가의 특정 재료가 가격 설명에 도움 되는지 확인 | T6-E041, T6-E052, T6-E063 | Warm 중심 | 일지 있음 |
| C4 | 작가명 + 지지체 | 특정 작가의 지지체 사용 차이가 가격 설명에 도움 되는지 확인 | T6-E042, T6-E059, T6-E064 | Warm 중심 | 일지 있음 |
| C5 | 작가명 + 제작연도 | 작가별 특정 시기 작품 가치 차이 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | Warm 중심, 제작연도 필요 | 보류 일지 있음 |
| C6 | 작가명 + 작품 유형 | 작가별 회화/판화/조각 등 유형 차이 확인 | T6-E049, T6-E066 일부 | Warm 중심, 유형 파생 필요 | 부분 준비 |
| C7 | 작가명 + 작품 기본 피처 묶음 | 작가를 통제한 기본 작품 물성 모델 확인 | T6-E046, T6-E032 | Warm 중심 | 일지 있음 |
| C8 | C7 + 작가 메타 | 작품 정보에 작가 메타를 추가했을 때 성능이 더 좋아지는지 확인 | T6-E027, T6-E028, T6-E073~E082 | Warm / Cold 메타 비교 | 일지 있음 |

### Group D: 작품 기본 피처 묶음 + 작가명 x 작품 변수 교차항

| 실험 | 교차항 | 목적 | 기존 일지 | 적용 범위 | 상태 |
|---|---|---|---|---|---|
| D1 | artist_name x ho_bucket | 작가별 크기 가격대 차이 확인 | T6-E025 | Warm 전용 | 일지 있음 |
| D2 | artist_name x log_area | 작가별 대형작 프리미엄 확인 | [T6-E102](../../experiments/track6/T6-E102_artist_log_area_interaction/experiment_log.html) | Warm 전용 | 일지 있음 |
| D3 | artist_name x nant_material_idx | 특정 작가의 특정 재료 프리미엄 확인 | [T6-E103](../../experiments/track6/T6-E103_artist_material_interaction/experiment_log.html) | Warm 전용 | 일지 있음 |
| D4 | artist_name x nant_support | 특정 작가의 특정 지지체 프리미엄 확인 | [T6-E104](../../experiments/track6/T6-E104_artist_support_interaction/experiment_log.html) | Warm 전용 | 일지 있음 |
| D5 | artist_name x artwork_age | 작가별 특정 시기 작품 가치 확인 | [BLOCK-A4](../../experiments/track6/BLOCK-A4_artwork_year_column_required/experiment_log.html) | Warm 전용, 제작연도 필요 | 보류 일지 있음 |
| D6 | career_stage x size | 작가 메타 x 작품 변수 교차항이므로 Group G로 이동 | T6-E094~E100 후보 | Warm / Cold 메타 가능 | G로 이동 |
| D7 | career_stage x material | 작가 메타 x 작품 변수 교차항이므로 Group G로 이동 | T6-E094~E100 후보 | Warm / Cold 메타 가능 | G로 이동 |
| D8 | artist_activity x size | 작가 메타 x 작품 변수 교차항이므로 Group G로 이동 | T6-E094~E100 후보 | Warm / Cold 메타 가능 | G로 이동 |
| D9 | artist_activity x material | 작가 메타 x 작품 변수 교차항이므로 Group G로 이동 | T6-E094~E100 후보 | Warm / Cold 메타 가능 | G로 이동 |

### 기존 실험과 겹치지 않는 추가 작가 실험

| 실험 | 확인 대상 | 목적 | 기존 실험과 다른 점 | 적용 범위 | 상태 |
|---|---|---|---|---|---|
| AX1 | 작가명 한글화 전/후 비교 | 영문/한글 표기 정리가 Warm 성능과 작가 매칭 안정성을 개선하는지 확인 | 작가명 자체 효과가 아니라 이름 정제 품질을 검증 | Warm 중심 | [일지 있음](../../experiments/track6/AX1_artist_name_normalization_before_after/experiment_log.html) |
| AX2 | 동명이인 분리 전/후 비교 | 같은 이름의 다른 작가가 섞일 때 성능이 왜곡되는지 확인 | 작가명 피처 성능이 실제 작가 효과인지 데이터 혼합 효과인지 분리 | Warm 중심 | [일지 있음](../../experiments/track6/AX2_homonym_split_before_after/experiment_log.html) |
| AX3 | 작가 DB 매칭 성공/실패 구간 비교 | 작가 메타를 확보할 수 있는 작가와 없는 작가의 오차 차이 확인 | 메타 변수 효과가 아니라 DB 커버리지 리스크 확인 | Warm / Cold | [일지 있음](../../experiments/track6/AX3_artist_db_match_success_slice/experiment_log.html) |
| AX4 | 작가별 학습 작품 수 기준 변경 | 1개 이상, 3개 이상, 5개 이상 등 Warm 기준에 따라 성능과 안정성이 어떻게 변하는지 확인 | artist_works_log 값을 피처로 쓰는 실험이 아니라 Warm 판단 기준을 검증 | Warm 라우팅 | [일지 있음](../../experiments/track6/AX4_warm_artist_count_threshold/experiment_log.html) |
| AX5 | 저이력 작가 전용 fallback | 학습 작품 수가 적은 작가를 Warm 모델로 볼지 Cold 모델로 볼지 비교 | Warm/Cold 모델 선택 정책 검증 | Warm / Cold 경계 | [일지 있음](../../experiments/track6/AX5_low_history_artist_fallback/experiment_log.html) |
| AX6 | 작가 메타 결측 패턴별 성능 | 생년/국적/활동량 정보가 비어 있는 작가군에서 오차가 커지는지 확인 | 메타 값을 넣는 실험이 아니라 결측 자체의 위험도 확인 | Warm / Cold | [일지 있음](../../experiments/track6/AX6_artist_meta_missing_pattern_slice/experiment_log.html) |
| AX7 | 작가 가격대 과적합 점검 | 작가명만으로 좋아진 성능이 실제 작품 정보 없이 가격대만 외운 결과인지 확인 | 작가명 효과의 신뢰성 검증 | Warm 중심, GroupKFold 필수 | [일지 있음](../../experiments/track6/AX7_artist_price_memorization_check/experiment_log.html) |
| AX8 | 신규 작가 메타만 사용한 Cold 모델 | 작가명 없이 생년/국적/활동량 같은 운영 가능 메타만으로 Cold 개선이 되는지 확인 | Cold에서 작가명은 쓰지 않고 작가 DB에서 얻을 수 있는 메타만 검증 | Cold 중심 | [일지 있음](../../experiments/track6/AX8_cold_artist_meta_only_model/experiment_log.html) |

## Group D: 교차항/조합 효과

| 실험 | 사용 피처 | 목적 | 기존 일지 | 현재 상태 |
|---|---|---|---|---|
| D1 | 재료 x 호수, 난트 재료 x 호수 | 같은 크기라도 재료에 따라 가격 증가 패턴이 다른지 확인 | T6-E024, T6-E044 | 일지 있음 |
| D2 | 재료 x 지지체 | 재료와 지지체 조합의 가격 차이 확인 | T6-E026, T6-E060 | 일지 있음 |
| D3 | 작가명 x 호수 | 작가별 크기 가격대 차이 확인 | T6-E025 | 일지 있음 |
| D4 | Warm/Cold 전용 피처 조합 | Warm과 Cold가 서로 다른 피처셋을 써야 하는지 확인 | T6-E046 | 일지 있음 |
| D5 | 단계적 피처 선택 | 단일 변수, 그룹 변수, 제거 실험 순서로 후보 축소 | T6-E045 | 일지 있음 |
| D6 | Cold 2D/3D 분기, 위험 구간 분석 | 약점 구간 보완과 신뢰도 정책 확인 | T6-E030, T6-E031, T6-E036, T6-E037 | 일지 있음 |

## 일지 단위 상세 매핑표

| 그룹 | 상세 실험 | 일지 ID | 제목 | 사용 피처 | 비교 모델군 | 목적 | 관계 | 상태 |
|---|---|---|---|---|---|---|---|---|
| Group A | A1 | [T6-E039](../../experiments/track6/T6-E039_ho_signal_baseline/experiment_log.html) | 호수 변수 영향 확인 | `ln_estimated_ho` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 호수 단독 영향 확인 | 기준 단일 | 일지 있음 |
| Group A | A1 | [T6-E040](../../experiments/track6/T6-E040_actual_size_feature_group/experiment_log.html) | 실제 크기 정보 추가 실험 | `width_cm, height_cm, log_area, aspect_ratio` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 호수 외 실제 크기 효과 확인 | 상위 묶음 | 일지 있음 |
| Group A | A1 | [T6-E047](../../experiments/track6/T6-E047_size_representative_vs_full/experiment_log.html) | 크기 대표값 vs 전체 크기 피처 실험 | `ln_estimated_ho vs width/height/log_area/aspect_ratio` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 대표 크기와 전체 크기 비교 | 비교 실험 | 일지 있음 |
| Group A | A1 | [T6-E053](../../experiments/track6/T6-E053_max_min_side_size_feature/experiment_log.html) | 긴 변/짧은 변 크기 피처 실험 | `max_side_cm, min_side_cm` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 면적 대비 긴 변/짧은 변 효과 확인 | 하위 표현 | 일지 있음 |
| Group A | A1 | [T6-E055](../../experiments/track6/T6-E055_width_height_variable_check/experiment_log.html) | 가로/세로 변수 영향 확인 | `width_cm, height_cm` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 가로/세로 단독 추가 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A1 | [T6-E056](../../experiments/track6/T6-E056_area_log_area_variable_check/experiment_log.html) | 면적/로그면적 변수 영향 확인 | `area_cm2, log_area` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 면적 표현 방식 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A1 | [T6-E057](../../experiments/track6/T6-E057_aspect_ratio_variable_check/experiment_log.html) | 가로세로 비율 변수 영향 확인 | `aspect_ratio` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 형태 비율 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A2 | [T6-E041](../../experiments/track6/T6-E041_material_feature_group/experiment_log.html) | 재료 정보 추가 실험 | `nant_material_idx, nant_tool` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 재료 효과 확인 | 상위 묶음 | 일지 있음 |
| Group A | A2 | [T6-E052](../../experiments/track6/T6-E052_nant_material_grouping/experiment_log.html) | 난트 재료 분류 그룹화 실험 | `nant_material_idx, nant_material_group` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 난트 세분화/그룹화 비교 | 표현 비교 | 일지 있음 |
| Group A | A2 | [T6-E058](../../experiments/track6/T6-E058_medium_category_variable_check/experiment_log.html) | 재료 대분류 변수 영향 확인 (중단) | `medium_category` | `실행 안 함` | 난트 재료 변수와 중복되어 제외 | 중단 | 중단 |
| Group A | A2 | [T6-E063](../../experiments/track6/T6-E063_nant_material_idx_variable_check/experiment_log.html) | 난트 재료 번호 변수 영향 확인 | `nant_material_idx` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 난트 재료 번호 추가 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A2 | [T6-E065](../../experiments/track6/T6-E065_raw_material_text_variable_check/experiment_log.html) | 원본 재료 문구 변수 영향 확인 | `collected_material_raw keyword flags` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 원본 재료 문구 키워드 효과 확인 | 보완 피처 | 일지 있음 |
| Group A | A3 | [T6-E042](../../experiments/track6/T6-E042_support_feature_group/experiment_log.html) | 지지체 정보 추가 실험 | `support_category, nant_support` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 지지체 효과 확인 | 상위 묶음 | 일지 있음 |
| Group A | A3 | [T6-E059](../../experiments/track6/T6-E059_support_category_variable_check/experiment_log.html) | 지지체 대분류 변수 영향 확인 | `support_category` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 지지체 대분류 단독 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A3 | [T6-E064](../../experiments/track6/T6-E064_nant_support_tool_variable_check/experiment_log.html) | 난트 지지체 변수 영향 확인 | `nant_support` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 난트 지지체 추가 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A5 | [T6-E049](../../experiments/track6/T6-E049_title_keyword_feature/experiment_log.html) | 작품 제목 키워드 피처 실험 | `title_raw keyword flags` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작품 유형/에디션 키워드 효과 확인 | 상위 파생 | 부분 일지 |
| Group A | A5 | [T6-E066](../../experiments/track6/T6-E066_title_text_variable_check/experiment_log.html) | 작품 제목 문구 변수 영향 확인 | `title_raw keyword flags` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | T6-E049의 하위 개별 변수 확인 | 하위/중복 | 하위 일지 |
| Group A | A6 | [T6-E043](../../experiments/track6/T6-E043_depth_3d_feature_group/experiment_log.html) | 깊이/3D 정보 추가 실험 | `depth_cm, has_depth, is_3d_candidate` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 입체성 정보 효과 확인 | 상위 묶음 | 일지 있음 |
| Group A | A6 | [T6-E051](../../experiments/track6/T6-E051_depth_bucket_feature/experiment_log.html) | 깊이 구간화 피처 실험 | `depth_bucket` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 깊이 구간화 효과 확인 | 하위 파생 | 일지 있음 |
| Group A | A6 | [T6-E061](../../experiments/track6/T6-E061_depth_variable_check/experiment_log.html) | 깊이 변수 영향 확인 | `depth_cm` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 깊이 단독 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A6 | [T6-E062](../../experiments/track6/T6-E062_three_d_flag_variable_check/experiment_log.html) | 3D 후보 플래그 변수 영향 확인 | `has_depth, is_3d_candidate` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 3D 여부 플래그 효과 확인 | 하위 단일 | 일지 있음 |
| Group A | A8 | [T6-E044](../../experiments/track6/T6-E044_material_size_interaction/experiment_log.html) | 재료 x 크기 조합 피처 실험 | `nant_material_idx_x_ho_bucket` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 크기와 재료 조합 효과 확인 | 상위 조합 | 일지 있음 |
| Group A | A8 | [T6-E024](../../experiments/track6/T6-E024_material_ho_interaction/experiment_log.html) | 재료 x 호수 조합 피처 실험 | `nant_material_idx_x_ho_bucket` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 같은 호수 내 재료 차이 확인 | 통합 검토 | 일지 있음 |
| Group A | A9 | [A9](../../experiments/track6/A9_size_material_support_combo/outputs/result_sheet.html) | 크기 + 재료 + 지지체 조합 실험 | `log_area, medium_category, collected_material_raw_bucket, nant_material_idx, nant_tool, support_category, nant_support` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작품 기본 피처 묶음에 지지체를 추가할 가치 확인 | 현행 실행 | 일지 있음 |
| Group A | A9 | [T6-E045](../../experiments/track6/T6-E045_staged_feature_selection/experiment_log.html) | 단계적 피처 선택 절차 실험 | `size, material, support, depth 계열 후보` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | 작품 변수 후보 축소 절차 확인 | 선택 절차 | 일지 있음 |
| Group A | A9 | [T6-E046](../../experiments/track6/T6-E046_warm_cold_feature_split/experiment_log.html) | Warm/Cold 작품 피처 분리 실험 | `Warm/Cold feature sets` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | 작품 피처셋 분리 필요성 확인 | 분리 검증 | 일지 있음 |
| Group A | A9 | [T6-E026](../../experiments/track6/T6-E026_support_material_interaction/experiment_log.html) | 지지체 x 재료 조합 실험 | `nant_material_support_bucket, nant_support_nant_tool_bucket` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 재료와 지지체 조합 효과 확인 | 상위 조합 | 일지 있음 |
| Group A | A9 | [T6-E060](../../experiments/track6/T6-E060_nant_material_support_bucket_variable_check/experiment_log.html) | 재료+지지체 조합 변수 영향 확인 | `nant_material_support_bucket` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 재료+지지체 조합 단독 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B1 | [T6-E012](../../experiments/track6/T6-E012_artist_only_warm_baseline/experiment_log.html) | 작가명 only Warm 기준 실험 | `artist_name_ko` | `Hedonic Ridge` | 작가명 자체 효과 확인 | 초기 기준 | 일지 있음 |
| Group B | B1 | [T6-E054](../../experiments/track6/T6-E054_artist_name_variable_check/experiment_log.html) | 작가명 변수 영향 확인 | `artist_name_ko` | `Warm: Huber/Linear/Ridge, Cold 제외` | 작가명 추가 효과 확인 | 현행 단일 | 일지 있음 |
| Group B | B2 | [T6-E067](../../experiments/track6/T6-E067_artist_works_log_variable_check/experiment_log.html) | 작가별 데이터 보유 작품 수 변수 영향 확인 | `artist_works_log` | `Warm: Huber/Linear/Ridge, Cold 제외` | 작가별 데이터 보유량 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B3 | [T6-E073](../../experiments/track6/T6-E073_artist_birth_year_variable_check/experiment_log.html) | 작가 생년 변수 영향 확인 | `artist_meta_birth_year` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작가 세대 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B4 | [T6-E076](../../experiments/track6/T6-E076_artist_nationality_variable_check/experiment_log.html) | 작가 국적 변수 영향 확인 | `artist_meta_nationality` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작가 국적 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B5 | [T6-E075](../../experiments/track6/T6-E075_artist_career_stage_variable_check/experiment_log.html) | 작가 경력 단계 변수 영향 확인 | `artist_meta_career_stage` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작가 경력 단계 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B6 | [T6-E078](../../experiments/track6/T6-E078_artist_total_works_variable_check/experiment_log.html) | 작가 등록 작품 수 변수 영향 확인 | `artist_meta_total_works` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작가 활동량 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B6 | [T6-E079](../../experiments/track6/T6-E079_artist_for_sale_works_variable_check/experiment_log.html) | 작가 판매 중 작품 수 변수 영향 확인 | `artist_meta_for_sale_works` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작가 판매 활동량 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B6 | [T6-E081](../../experiments/track6/T6-E081_artist_followers_variable_check/experiment_log.html) | 작가 팔로워 수 변수 영향 확인 | `artist_meta_followers` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 작가 인지도 효과 확인 | 하위 단일 | 일지 있음 |
| Group B | B6 | [T6-E082](../../experiments/track6/T6-E082_artist_p1_flag_variable_check/experiment_log.html) | 플랫폼 주요 작가 여부 변수 영향 확인 | `artist_meta_is_p1` | `Warm: Huber/Linear/Ridge, Cold: Huber/Quantile-LAD/LightGBM` | 주요 작가 여부 효과 확인 | 하위 단일 | 일지 있음 |
| Group C | C1 | [T6-E010](../../experiments/track6/T6-E010_hedonic_artist_ho_log/experiment_log.html) | 작가명 + 호수 / ln 변환 초기 실험 | `artist_name_ko, estimated_ho, ln_estimated_ho` | `Hedonic Linear Regression / log transform 비교` | 작가명+호수 기본 효과 확인 | 초기 기준 | 일지 있음 |
| Group C | C1 | [T6-E014](../../experiments/track6/T6-E014_linear_model_family_compare/experiment_log.html) | 헤도닉 선형 모델군 비교 | `artist_name_ko, ln_estimated_ho` | `선형/강건 선형: Linear/Ridge/Lasso/ElasticNet/Huber/Quantile` | 선형 계열 모델 비교 | 모델 비교 | 일지 있음 |
| Group C | C1 | [T6-E015](../../experiments/track6/T6-E015_warm_nonlinear_model_compare/experiment_log.html) | Warm 비선형 모델 비교 | `artist_name_ko, ln_estimated_ho` | `비선형/트리: LightGBM/CatBoost/XGBoost/HistGradientBoosting` | Warm 비선형 모델 효과 확인 | 모델 비교 | 일지 있음 |
| Group C | C1 | [T6-E017](../../experiments/track6/T6-E017_baseline_model_freeze/experiment_log.html) | 기본 피처 기반 후보 모델 선정 | `artist_name_ko, ln_estimated_ho, material 계열, support 계열` | `Linear/Ridge/Huber/Quantile-LAD + LightGBM/XGBoost/CatBoost/HistGradientBoosting` | 기준 모델 선정 | 모델 선정 | 일지 있음 |
| Group C | C4 | [T6-E027](../../experiments/track6/T6-E027_artist_meta_basic_features/experiment_log.html) | 작가 기본 메타 피처 추가 실험 | `artist metadata basic` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | 작가 메타 추가 효과 확인 | 상위 묶음 | 일지 있음 |
| Group C | C4 | [T6-E028](../../experiments/track6/T6-E028_artist_activity_features/experiment_log.html) | 작가 활동량 피처 실험 | `artist activity metadata` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | 작가 활동량 추가 효과 확인 | 상위 묶음 | 일지 있음 |
| Group C | C4 | [T6-E032](../../experiments/track6/T6-E032_warm_candidate_feature_set_compare/experiment_log.html) | Warm 후보 피처 조합 비교 | `Warm candidate feature sets` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | Warm 최종 후보 피처셋 비교 | 후보 조합 | 일지 있음 |
| Group C | C5 | [T6-E016](../../experiments/track6/T6-E016_cold_basic_model_compare/experiment_log.html) | Cold 기본 모델 비교 | `ln_estimated_ho` | `Ridge/Huber/Quantile/LightGBM/CatBoost` | Cold 기본 모델 후보 비교 | 모델 비교 | 일지 있음 |
| Group C | C5 | [T6-E029](../../experiments/track6/T6-E029_cold_material_size_model/experiment_log.html) | Cold 재료 + 크기 모델 실험 | `Cold material/size features` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | Cold 작품 변수 모델 확인 | 상위 묶음 | 일지 있음 |
| Group C | C5 | [T6-E033](../../experiments/track6/T6-E033_cold_candidate_feature_set_compare/experiment_log.html) | Cold 후보 피처 조합 비교 | `Cold candidate feature sets` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | Cold 최종 후보 피처셋 비교 | 후보 조합 | 일지 있음 |
| Group C | C5 | [T6-E035](../../experiments/track6/T6-E035_cold_final_model_compare/experiment_log.html) | Cold 최종 후보 모델 비교 | `selected Cold feature set` | `Ridge/Huber/Quantile/CatBoost/LightGBM` | Cold 최종 후보 모델 비교 | 최종 모델 | 일지 있음 |
| Group D | D3 | [T6-E025](../../experiments/track6/T6-E025_artist_ho_interaction/experiment_log.html) | 작가명 x 호수 조합 실험 | `artist_ho_bucket` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | 작가별 크기 가격대 차이 확인 | 교차항 | 일지 있음 |
| Group D | D6 | [T6-E030](../../experiments/track6/T6-E030_cold_2d_3d_branch/experiment_log.html) | Cold 2D/3D 분기 실험 | `Cold 2D/3D branch` | `Cold 전체 모델 / 2D 모델 / 3D 모델` | Cold 3D 약점 구간 보완 | 분기/정책 | 일지 있음 |
| Group D | D6 | [T6-E031](../../experiments/track6/T6-E031_cold_risk_slice_analysis/experiment_log.html) | Cold 위험 구간 분석 | `Cold risk slices` | `Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM` | Cold 큰 오차 조건 분석 | 위험 분석 | 일지 있음 |
| Group D | D6 | [T6-E036](../../experiments/track6/T6-E036_warm_cold_routing_policy/experiment_log.html) | Warm/Cold 라우팅 기준 실험 | `routing policy` | `Warm/Cold routing 후보` | Warm/Cold 모델 선택 기준 확인 | 정책 | 일지 있음 |
| Group D | D6 | [T6-E037](../../experiments/track6/T6-E037_price_interval_confidence_policy/experiment_log.html) | 가격 범위/신뢰도 정책 실험 | `interval/confidence policy` | `가격 범위/신뢰도 정책 후보` | 가격 범위와 신뢰도 표시 기준 확인 | 정책 | 일지 있음 |


## 현재 기준으로 보완이 필요한 항목

- `제작연도`: 현재 `track6_feature_candidates_name_corrected.csv`에 명시 컬럼이 없어 A4, A10, A11은 바로 실험 불가.
- `작품 유형`: 명시 컬럼이 없어 제목/재료 문구에서 `painting`, `print`, `sculpture`, `edition` 등 키워드 파생이 필요.
- `edition/signed`: 명시 컬럼이 없어 제목/원본 문구 기반 파생 후 A7, A12에 연결해야 함.
- `Random Split`과 `GroupKFold by artist`: 같은 실험군을 두 평가 방식으로 반복해야 작가명으로 성능이 좋아 보이는 문제를 확인할 수 있음.
- `난트 변수`: 재료 최종 후보는 `medium_category`를 제외하고 `nant_material_idx + nant_tool`을 우선함. 지지체 최종 후보는 `support_category`를 제외하고 `nant_support`를 우선함.

## 중복 후보 검토표

| 구분 | 중복 후보 | 판단 | 정리 기준 |
|---|---|---|---|
| 완전 중복 후보 | T6-E049 작품 제목 키워드 피처 실험 / T6-E066 작품 제목 문구 변수 영향 확인 | 중복 가능성 높음 | T6-E049를 상위 실험으로 두고, T6-E066은 T6-E049의 하위 개별 변수 확인 일지로 표시 |
| 부분 중복 후보 | T6-E041 재료 정보 추가 실험 / T6-E058 재료 대분류 / T6-E063 난트 재료 번호 / T6-E065 원본 재료 문구 | T6-E058 중단 | T6-E041은 난트 재료 묶음 실험, T6-E058은 medium_category 중복으로 중단, T6-E063/E065는 난트 재료 후보와 원본 문구를 확인하는 하위 실험 |
| 부분 중복 후보 | T6-E042 지지체 정보 추가 실험 / T6-E059 지지체 대분류 / T6-E064 난트 지지체 | 중복 아님 | T6-E042는 지지체 묶음 실험, T6-E059/E064는 지지체 후보 변수를 하나씩 확인하는 하위 실험 |
| 부분 중복 후보 | T6-E040 실제 크기 정보 추가 / T6-E055 가로·세로 / T6-E056 면적·로그면적 / T6-E057 비율 / T6-E053 긴 변·짧은 변 | 중복 아님 | T6-E040은 크기 묶음 실험, 나머지는 크기 표현 방식별 하위 실험 |
| 통합 검토 후보 | T6-E044 재료 x 크기 조합 / T6-E024 재료 x 호수 조합 | 통합 검토 | 현재 둘 다 `nant_material_idx_x_ho_bucket` 중심이라 같은 실험으로 보일 수 있음. T6-E044를 상위 조합 실험으로 두고 T6-E024는 호수 구간 하위 확인으로 둘지 통합할지 결정 필요 |
| 초기/현행 구분 | T6-E012 작가명 only 초기 기준 / T6-E054 작가명 변수 영향 확인 | 중복 아님 | T6-E012는 초기 기준 실험, T6-E054는 현행 기본 모델군 기준의 단일 변수 확인 실험으로 구분 |
| 상위/하위 구분 | T6-E027 작가 기본 메타 묶음 / T6-E073, T6-E076, T6-E075 단일 변수 | 중복 아님 | 묶음 실험과 단일 변수 확인은 목적이 다르므로 상위/하위 관계로 유지 |
| 같은 피처, 다른 모델군 | T6-E014 헤도닉 선형 모델군 / T6-E015 Warm 비선형 모델 | 중복 아님 | 같은 피처로 선형 모델군과 비선형 모델군을 비교하는 모델 실험 |

## 중복 정리 원칙

- 같은 `사용 피처`, 같은 `비교 모델군`, 같은 `목적`이면 하나의 상위 실험으로 통합한다.
- 같은 피처를 쓰더라도 비교 모델군이 다르면 모델 비교 실험으로 유지한다.
- 상위 묶음 실험과 단일 변수 확인 실험은 중복으로 보지 않고, 상위/하위 관계로 표시한다.
- 표에서는 하위 실험의 상태를 `하위 일지` 또는 `부분 일지`로 표시해 중복처럼 보이지 않게 한다.

## 권장 진행 순서

1. Group A의 A1~A3, A6을 먼저 실행해 작품 변수의 기본 설명력을 확인한다.
2. A4, A5, A7은 현재 데이터에 구조화 컬럼이 없으므로 파생 규칙을 먼저 만든다.
3. Group B로 작가 변수만의 단독 설명력을 탐색한다.
4. Group C로 작품 기본 피처 묶음을 통제한 뒤 작가 변수를 추가했을 때 개선되는지 확인한다.
5. Group D/G로 작가명 또는 작가 메타와 작품 변수의 교차항 효과를 검증한다.
6. 모든 주요 실험은 Random Split과 GroupKFold by artist를 함께 기록한다.
