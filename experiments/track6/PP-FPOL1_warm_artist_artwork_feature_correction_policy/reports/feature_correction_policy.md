# PP-FPOL1 Warm 작가+작품 피처 계수 보정 정책

- 작성일: 2026-06-08 15:15
- 목적: 지금까지의 Warm/Huber/작품/작가 실험 결과를 종합해 다음 Huber residual 보정 실험의 피처군과 보정값 후보를 고정
- 기준: 현재 Warm 1순위 `blend_svcnum_ppv8_wsvc_0.70` 위에 잔차 보정을 얹는 정책

## 1. 채택 피처군

| korean_name | decision | role | recommended_cap | recommended_strength | risk |
| --- | --- | --- | --- | --- | --- |
| 작품 크기/형태 | adopt_core | 모든 Warm residual Huber 보정의 기본 작품 축 | 0.06 또는 0.08 | 0.25 또는 0.35 | 면적 단독 구간 보정은 MdAPE 악화 가능. Huber residual 안에서만 사용. |
| 작품 재료/지지체 | adopt_conditional | 크기 피처와 결합할 때만 작품 보정축으로 사용 | 0.03 또는 0.06 | 0.25 또는 0.35 | 단독 재료/지지체는 악화. 범주 수가 많아 과보정 방지 필요. |
| 작가 생년/세대 | adopt_core_artist | 작가 가격대 내부의 시대/세대 편향 보정 | 0.03 | 0.50 | career/activity까지 전부 묶으면 test MAPE 악화 가능. |
| 작가 팔로워/판매중 작품 수 | adopt_light | 작가 활동/노출의 작은 잔차 편향 보정 | 0.03 | 0.50 | activity bundle 전체는 test에서 MAPE/p95 악화. |
| 유사작품/비교군 신뢰도 | adopt_gate | 작품 보정값 적용 강도와 tail guard 결정 | 0.06 또는 0.08 | 0.25 또는 0.35 | 비교군 품질이 낮은 구간은 큰 보정 금지. |

## 2. 보류/보조 피처군

| korean_name | decision | role | recommended_cap | recommended_strength | risk |
| --- | --- | --- | --- | --- | --- |
| 작품 제작연도/연식 | diagnostic_or_guard | 작품 시기 신호 및 신뢰도 gate | 0.02 또는 0.03 | 0.25 | 제작연도 입력 신뢰도에 민감하고 개선 폭이 작음. |
| 작품 깊이/3D | guard_only | 3D/깊이 특수 케이스의 tail guard | 0.02 | 0.25 | Warm에서는 평균 효과 작고 tail 악화 위험. |
| 에디션 정보 | holdout_diagnostic | 에디션 작품 slice 진단 | 0.00 | 0.00 | 에디션 표본이 작고 MAPE 악화 신호. |
| 갤러리/전시 외부 메타 | guard_or_auxiliary | 외부 메타 보유 여부와 신뢰도 gate | 0.00 또는 0.02 | 0.00 또는 0.25 | 커버리지가 낮고 gate 적용 시 효과가 거의 사라짐. |

## 3. 피처별 근거

| korean_name | columns | evidence | correction_policy |
| --- | --- | --- | --- |
| 작품 크기/형태 | width_cm,height_cm,area_cm2,log_area,aspect_ratio,is_extreme_aspect_ratio | 크기 추가 MdAPE delta -0.0145; 작가명+전체크기 MdAPE delta -0.2783; size 제거 test MdAPE/MAPE/p95 delta 0.3233/0.8025/3.2143; 기여도 rank 1 | include_in_residual_model; pred_price_bin tail guard 적용 |
| 작품 재료/지지체 | medium_category,support_category,medium_support_bucket,nant_support | 크기+재료+지지체 MdAPE delta -0.0155; medium_support 제거 test MdAPE/MAPE/p95 delta -0.0021/0.0035/-0.0202; medium_support 기여도 rank 2 | size/SVC/artist 신호와 함께 약한 residual 보정에만 포함 |
| 작가 생년/세대 | artist_meta_birth_year,artist_birth_generation_bin | PP-AMW10 생년+세대 best test delta MdAPE/MAPE/p95 -0.0028/-0.0001/-0.0195 | 작품 보정축과 별도 후보 및 결합 후보 모두 유지 |
| 작가 팔로워/판매중 작품 수 | artist_meta_followers_log1p,artist_meta_followers_missing,artist_meta_for_sale_works_log1p,artist_meta_for_sale_works_missing | 팔로워 best test delta MdAPE/MAPE/p95 -0.0030/-0.0005/-0.0196; 판매중 작품 수 best test delta MdAPE/MAPE/p95 -0.0019/-0.0004/-0.0212 | 생년/세대와 함께 소규모 Huber 보정 |
| 작품 제작연도/연식 | artwork_year,has_artwork_year,artwork_year_missing,artwork_year_source,artwork_year_match_method | 작가명+제작연도 MdAPE delta -0.0052 | 직접 보정값보다 year availability/source guard로 우선 사용 |
| 작품 깊이/3D | depth_cm,has_depth,is_3d_candidate | depth_3d 제거 test MdAPE/MAPE/p95 delta 0.0001/0.0021/0.0128; 기여도 rank 6 | 보정 모델 핵심 피처 제외. 큰 오차 원인 분류/gate로 사용. |
| 에디션 정보 | edition_class,is_edition,is_limited_edition,is_open_edition,is_unknown_edition,edition_info_available | C8+limited edition Huber MdAPE delta -0.0033; MAPE delta 0.0323 | 메인 계수 보정 후보에서 제외. 충분 표본 확보 후 slice 보정 재검증. |
| 갤러리/전시 외부 메타 | gallery_tier_raw_numeric,gallery_feature_source,gallery_city_count_log,artist_exhibition_total_count_log,artist_exhibition_available_count | 갤러리 best test delta MdAPE/MAPE/p95 0.0005/0.0000/-0.0179; 전시 best test delta MdAPE/MAPE/p95 0.0005/0.0002/-0.0209 | 메인 보정 계수에서 제외. 외부 신뢰도 gate나 리포팅 설명 피처로 사용. |
| 유사작품/비교군 신뢰도 | svc_group_n,svc_spread,quantile_width,l10_price_range_ratio,model_prediction_gap | PP-WCOEF/PP-WHUBER7에서 pred_size_svc 또는 pred_size_material_svc_artist 후보가 p95/MAPE 방어에 반복적으로 유효 | 보정 모델 피처 또는 reliability shrink/gate로 사용 |

## 4. 다음 실험 후보 grid

| feature_set | correction_policy | correction_cap | correction_strength | guard | expected_role |
| --- | --- | --- | --- | --- | --- |
| artist_core | hard_clip | 0.03 | 0.5 | small_global | 안정 baseline 보정 후보 |
| artist_core_activity_light | hard_clip | 0.03 | 0.5 | small_global | 작가 메타 약한 추가 보정 후보 |
| artwork_size_shape | hard_clip | 0.03 | 0.5 | small_global | 작품 크기 중심 p95/MAPE 방어 후보 |
| artwork_size_shape | hard_clip | 0.06 | 0.25 | medium_global | 작품 크기 중심 p95/MAPE 방어 후보 |
| artwork_size_shape | soft_tanh_cap | 0.06 | 0.35 | medium_soft | 작품 크기 중심 p95/MAPE 방어 후보 |
| artwork_size_shape | pred_bin_tail_guard | 0.06 | 0.35 | mid_open_tail_guard | 작품 크기 중심 p95/MAPE 방어 후보 |
| artwork_size_shape | pred_bin_tail_guard | 0.08 | 0.25 | wide_low_strength | 작품 크기 중심 p95/MAPE 방어 후보 |
| artwork_size_material_support | hard_clip | 0.03 | 0.5 | small_global | 작품 크기+재료/지지체 결합 보정 후보 |
| artwork_size_material_support | hard_clip | 0.06 | 0.25 | medium_global | 작품 크기+재료/지지체 결합 보정 후보 |
| artwork_size_material_support | soft_tanh_cap | 0.06 | 0.35 | medium_soft | 작품 크기+재료/지지체 결합 보정 후보 |
| artwork_size_material_support | pred_bin_tail_guard | 0.06 | 0.35 | mid_open_tail_guard | 작품 크기+재료/지지체 결합 보정 후보 |
| artwork_size_material_support | pred_bin_tail_guard | 0.08 | 0.25 | wide_low_strength | 작품 크기+재료/지지체 결합 보정 후보 |
| artist_artwork_core | hard_clip | 0.03 | 0.5 | small_global | 작가+작품 통합 잔차 보정 주 후보 |
| artist_artwork_core | hard_clip | 0.06 | 0.25 | medium_global | 작가+작품 통합 잔차 보정 주 후보 |
| artist_artwork_core | soft_tanh_cap | 0.06 | 0.35 | medium_soft | 작가+작품 통합 잔차 보정 주 후보 |
| artist_artwork_core | pred_bin_tail_guard | 0.06 | 0.35 | mid_open_tail_guard | 작가+작품 통합 잔차 보정 주 후보 |
| artist_artwork_core | pred_bin_tail_guard | 0.08 | 0.25 | wide_low_strength | 작가+작품 통합 잔차 보정 주 후보 |
| artist_artwork_core_year_guard | hard_clip | 0.03 | 0.5 | small_global | 제작연도 신뢰도 guard 포함 진단 후보 |
| artist_artwork_core_year_guard | hard_clip | 0.06 | 0.25 | medium_global | 제작연도 신뢰도 guard 포함 진단 후보 |
| artist_artwork_core_year_guard | soft_tanh_cap | 0.06 | 0.35 | medium_soft | 제작연도 신뢰도 guard 포함 진단 후보 |
| artist_artwork_core_year_guard | pred_bin_tail_guard | 0.06 | 0.35 | mid_open_tail_guard | 제작연도 신뢰도 guard 포함 진단 후보 |
| artist_artwork_core_year_guard | pred_bin_tail_guard | 0.08 | 0.25 | wide_low_strength | 제작연도 신뢰도 guard 포함 진단 후보 |

## 5. 결정 요약

- 크기/면적은 작품 피처의 핵심 보정축으로 유지한다.
- 재료/지지체는 단독 계수 보정 금지, 크기와 결합한 Huber residual 보정에서만 허용한다.
- 작가 생년/세대와 팔로워/판매중 작품 수는 작가 메타의 안정 보정축으로 유지한다.
- 갤러리/전시/에디션/깊이/제작연도는 메인 계수 보정보다 guard 또는 진단 피처로 우선 사용한다.
- 다음 실험은 `artist_artwork_core`와 `artwork_size_material_support`를 중심으로 cap 0.06, strength 0.25~0.35, pred-bin tail guard를 검증한다.

## 6. 산출물

- `outputs/feature_group_correction_policy.csv`
- `outputs/candidate_correction_grid.csv`
- `outputs/policy_manifest.json`