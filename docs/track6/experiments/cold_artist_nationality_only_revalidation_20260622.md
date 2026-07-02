# Cold artist nationality 단일 피처 재검증

- 작성일: 2026-06-22
- 목적: Cold 작가 메타 피처에서 `artist_meta_nationality_ko`를 제거하고 `artist_meta_nationality`만 사용할 때 기존 k80 운영 후보 성능과 후보 선택이 유지되는지 확인한다.
- 기준 실험: `PP-CSIM24`, `PP-CSIM25`, `PP-CSIM26` 재실행
- strict Cold 조건: `artist_key`, 동일 작가 가격 이력, artist_key lookup 후처리, `search_*`, 외부 live 검색 미사용

## 1. 변경 내용

기존 Cold 사용자 입력 가능 작가 메타 후보에는 아래 두 국적 피처가 함께 들어가 있었다.

```text
artist_meta_nationality
artist_meta_nationality_ko
```

재검토 결과 `artist_meta_nationality_ko`는 현재 service feature store에서 대부분 결측이고, `artist_meta_nationality`와 의미가 중복된다. 따라서 모델 입력 피처와 유사 이웃 선택 피처에서는 `artist_meta_nationality`만 사용하도록 정리했다.

현재 작가 국적 피처는 다음 하나다.

```text
artist_meta_nationality
```

## 2. 반영된 주요 코드

- `scripts/track6/run_pp_cmeta4_user_input_meta_only.py`
- `scripts/track6/run_pp_w_experiments.py`
- `scripts/track6/run_pp_csim9_cold_enterable_meta_feature_audit.py`
- `scripts/track6/run_pp_csim10_cold_gallery_tier_feature_validation.py`
- `scripts/track6/run_pp_csim11_cold_gallery_tier_expanded_mapping_validation.py`
- `scripts/track6/run_pp_csim12_cold_enterable_grouping_sequential_variants.py`
- `scripts/track6/run_pp_csim13_cold_low_price_defense_variants.py`
- `scripts/track6/run_pp_csim14_cold_q35_selection_policy_search.py`
- `scripts/track6/run_pp_csim15_cold_q35_robustness_validation.py`
- `scripts/track6/run_pp_csim16_cold_improvement_suite.py`
- `scripts/track6/run_pp_csim17_cold_similarity_grouping_grid.py`
- `scripts/track6/run_pp_csim18_cold_k320_candidate_validation.py`
- `scripts/track6/run_pp_csim19_cold_k320_limited_policy.py`
- `scripts/track6/run_pp_csim20_cold_learned_router.py`
- `scripts/track6/run_pp_csim21_cold_rule_router_grid.py`
- `scripts/track6/run_pp_csim22_cold_adaptive_k_quantile_grid.py`
- `scripts/track6/run_pp_csim23_cold_threeway_k_router.py`
- `scripts/track6/run_pp_csim27_cold_gallery_profile_grouping.py`

검증 출력:

```text
user_meta_core_bucket nationality cols: ['artist_meta_nationality']
ARTIST_SIM_FEATURES nationality cols: ['artist_meta_nationality']
```

## 3. 재검증 결과

`artist_meta_nationality_ko` 제거 후 `PP-CSIM24 -> PP-CSIM25 -> PP-CSIM26`을 다시 실행했다.

| 후보 | split | MdAPE | MAPE | p95 APE | RMSE log | APE > 2 | APE > 5 | APE > 10 | 선택 비율 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | validation | 0.424537 | 0.606746 | 1.808312 | 0.809976 | 97 | 10 | 1 | 0.00% |
| k40 후보 | validation | 0.405266 | 0.564256 | 1.648824 | 0.807453 | 77 | 7 | 1 | 55.65% |
| k80 후보 | validation | 0.409345 | 0.586917 | 1.739339 | 0.806873 | 91 | 9 | 1 | 22.76% |
| base | test | 0.481850 | 0.746296 | 2.398009 | 0.802895 | 212 | 35 | 8 | 0.00% |
| k40 후보 | test | 0.475254 | 0.707336 | 2.161091 | 0.805736 | 184 | 30 | 7 | 55.77% |
| k80 후보 | test | 0.484487 | 0.733582 | 2.264398 | 0.806729 | 204 | 32 | 8 | 12.83% |

후보명:

```text
k40 후보:
resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05

k80 후보:
resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05
```

## 4. 해석

`artist_meta_nationality_ko`를 제거해도 base 대비 유사 이웃 잔차 보정 후보의 개선 방향은 유지된다. 다만 기존 문서에서 k80을 선택했던 근거였던 “validation에서 k80이 더 안정적”이라는 판단은 더 이상 맞지 않는다.

재검증 후에는 k40 후보가 validation과 test 모두에서 k80보다 낫다.

- validation MAPE: k40 `0.564256`, k80 `0.586917`
- validation p95 APE: k40 `1.648824`, k80 `1.739339`
- validation APE > 5: k40 `7`, k80 `9`
- test MAPE: k40 `0.707336`, k80 `0.733582`
- test p95 APE: k40 `2.161091`, k80 `2.264398`
- test APE > 5: k40 `30`, k80 `32`

## 5. 권장

`artist_meta_nationality`만 쓰는 기준으로는 기존 k80 운영 후보를 그대로 확정하기보다, `k40_s1p0_cap0p25__route_neg_corr_ge_0p05`를 새 운영 후보로 재검토하는 것이 합리적이다.

다만 이 변경은 작가 메타 피처 정리와 후보 재선택을 동시에 발생시킨다. 따라서 최종 운영 승격 전에는 다음을 추가 확인한다.

- k40 후보의 반복 split 안정성
- 저가 구간 APE > 5 발생 원인
- `artist_meta_nationality` 값 표준화 전후 비교
- API/번들 parity 검증
