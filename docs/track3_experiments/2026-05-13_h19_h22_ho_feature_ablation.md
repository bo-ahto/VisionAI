# H19-H22 호수 피처 추가 실험 기록

- 실험 ID: `H19_H22_ho_feature_ablation`
- 날짜: 2026-05-13
- 상태: 종결
- 관련 가설: H19, H20, H21, H22
- 실행 스크립트: [`scripts/track3/h19_h22_ho_feature_ablation.py`](/Users/bo/VisionAI/scripts/track3/h19_h22_ho_feature_ablation.py:1)
- 결과 파일: [`data/track3_h19_h22_ho_feature_ablation_results.json`](/Users/bo/VisionAI/data/track3_h19_h22_ho_feature_ablation_results.json:1)

## 1. 실험 목적

- H26-H28에서 확인한 축소 크기 기준 위에 호수 관련 피처를 추가했을 때 Warm / Cold 성능이 좋아지는지 확인
- 호수 구간 세분화, 대형 호수 flag, 면적-호수 일관성, 로그 호수 표현이 실제 개선을 만드는지 검증
- 공통 입력 피처이므로 Cold만 보지 않고 Warm도 같은 변수 구성으로 함께 확인

## 2. 사용 데이터

- 학습 데이터: `data/release_split/track3_train.csv`
- Warm 평가: `data/release_split/track3_test_warm.csv`
- Cold 평가: `data/release_split/track3_test_cold.csv`
- 학습 데이터 수: `34,629`
- Warm 평가 데이터 수: `1,685`
- Cold 평가 데이터 수: `3,823`

## 3. 기준 피처

- H26-H28 결과를 반영한 축소 기준 사용
- 기본 범주형 피처
- `medium_category`
- `support_category`
- `orientation`
- `medium_ho_bucket`
- 기본 수치 피처
- `artist_works_log`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `aspect_ratio`
- Warm 전용 추가 피처
- `artist_name_ko`

## 4. 비교 variant

| variant | 설명 |
|---|---|
| `V0_reduced_base` | H26-H28 이후 축소 기준 |
| `V1_refined_ho_bucket` | 더 세분화한 호수 구간 추가 |
| `V2_large_ho_flags` | 대형/초대형 호수 여부 추가 |
| `V3_area_ho_consistency` | 면적과 호수의 불일치 정도 추가 |
| `V4_log_ho_add` | 기존 호수 원값에 `log_ho` 추가 |
| `V5_log_ho_replace_estimated` | `estimated_ho`를 `log_ho + ho_bucket_refined`로 대체 |
| `V6_all_ho_features` | 위 호수 피처를 모두 추가 |

## 5. 평가 결과

| variant | Cold median APE | Cold 변화 | Warm median APE | Warm 변화 |
|---|---:|---:|---:|---:|
| `V0_reduced_base` | `0.3207` | `+0.0000` | `0.2056` | `+0.0000` |
| `V1_refined_ho_bucket` | `0.3184` | `-0.0023` | `0.2039` | `-0.0017` |
| `V2_large_ho_flags` | `0.3178` | `-0.0030` | `0.2056` | `+0.0000` |
| `V3_area_ho_consistency` | `0.3370` | `+0.0163` | `0.2047` | `-0.0009` |
| `V4_log_ho_add` | `0.3364` | `+0.0157` | `0.2056` | `+0.0000` |
| `V5_log_ho_replace_estimated` | `0.3195` | `-0.0013` | `0.2039` | `-0.0017` |
| `V6_all_ho_features` | `0.3163` | `-0.0045` | `0.1958` | `-0.0098` |

## 6. 결과 해석

- `V6_all_ho_features`가 Warm / Cold 모두에서 가장 좋음
- Cold median APE는 `0.3207 -> 0.3163`으로 개선
- Warm median APE는 `0.2056 -> 0.1958`로 개선
- `ho_bucket_refined`는 단독으로도 Warm / Cold를 모두 소폭 개선함
- `is_large_ho`, `is_extra_large_ho`는 Cold를 소폭 개선하고 Warm에는 거의 영향 없음
- `area_per_ho_log`, `ho_per_area_log`, `ho_area_gap_abs`는 단독으로는 Cold를 악화시킴
- `log_ho`를 단순 추가하는 것은 Cold를 악화시킴
- 단, `estimated_ho`를 `log_ho + ho_bucket_refined`로 대체하는 방식은 성능을 거의 유지하거나 소폭 개선함

## 7. 가설별 판단

- H19
- 호수 구간 세분화는 성능 개선 신호가 있으므로 채택 후보
- H20
- 대형/초대형 호수 flag는 Cold 개선 신호가 있으므로 채택 후보
- H21
- 면적-호수 일관성 피처는 단독으로 Cold를 악화시켜 단독 채택은 보류
- 다만 전체 조합에서는 개선에 기여했을 가능성이 있어 H30 slice 분석에서 재확인 필요
- H22
- `estimated_ho` 원값만 고집할 필요는 없음
- `log_ho + ho_bucket_refined` 대체안은 성능 유지 가능성이 있음
- 최종 후보는 `V6_all_ho_features`이지만, 피처 수 증가 대비 안정성은 후속 반복 검증 필요

## 8. 결론

- 결론: 부분 채택
- H19, H20은 채택 후보
- H21은 단독 채택 보류
- H22는 대체 표현 가능성 확인
- 다음 단계에서는 `V6_all_ho_features`를 H23-H25 또는 H29-H30에서 기준 후보로 두되, 반복 안정성과 slice별 개선 여부를 확인해야 함

## 9. 다음 할 일

- H23-H25 크기 구간/3D/재료 내 상대 크기 실험 진행
- H29에서 Warm과 Cold의 피처 채택 기준이 달라야 하는지 종합
- H30에서 전체 median APE가 아니라 약점 slice 개선 여부 확인
