# H23-H25 크기 구간 / 3D / 상대 크기 실험 기록

- 실험 ID: `H23_H25_size_3d_relative_ablation`
- 날짜: 2026-05-13
- 상태: 종결
- 관련 가설: H23, H24, H25
- 실행 스크립트: [`scripts/track3/h23_h25_size_3d_relative_ablation.py`](/Users/bo/VisionAI/scripts/track3/h23_h25_size_3d_relative_ablation.py:1)
- 결과 파일: [`data/track3_h23_h25_size_3d_relative_results.json`](/Users/bo/VisionAI/data/track3_h23_h25_size_3d_relative_results.json:1)

## 1. 실험 목적

- H19-H22에서 가장 좋았던 호수 피처 조합을 기준으로 추가 크기 피처가 성능을 더 개선하는지 확인
- 크기 구간, 3D 부피/변 길이, 재료 내 상대 크기 순위를 각각 검증
- 공통 피처이므로 Warm / Cold를 같은 변수 구성으로 함께 평가

## 2. 사용 데이터

- 학습 데이터: `data/release_split/track3_train.csv`
- Warm 평가: `data/release_split/track3_test_warm.csv`
- Cold 평가: `data/release_split/track3_test_cold.csv`
- 학습 데이터 수: `34,629`
- Warm 평가 데이터 수: `1,685`
- Cold 평가 데이터 수: `3,823`

## 3. 기준 피처

- H19-H22 최고 조합인 `V6_all_ho_features`를 기준으로 사용
- 핵심 포함 피처
- `depth_cm`
- `log_area`
- `estimated_ho`
- `aspect_ratio`
- `ho_bucket_refined`
- `is_large_ho`
- `is_extra_large_ho`
- `area_per_ho_log`
- `ho_per_area_log`
- `ho_area_gap_abs`
- `log_ho`

## 4. 비교 variant

| variant | 설명 |
|---|---|
| `V0_ho_enhanced_base` | H19-H22 최고 호수 피처 조합 |
| `V1_area_size_bucket` | 크기 구간과 극단 크기 flag 추가 |
| `V2_3d_volume_sides` | 3D 여부, 부피, 가장 긴 변, 가장 짧은 변 추가 |
| `V3_medium_relative_size` | 재료별 면적/호수 상대 순위 추가 |
| `V4_all_size_3d_relative` | H23-H25 피처 전체 추가 |

## 5. 평가 결과

| variant | Cold median APE | Cold 변화 | Warm median APE | Warm 변화 | Cold 3D median APE |
|---|---:|---:|---:|---:|---:|
| `V0_ho_enhanced_base` | `0.3163` | `+0.0000` | `0.1958` | `+0.0000` | `0.2936` |
| `V1_area_size_bucket` | `0.3173` | `+0.0010` | `0.2080` | `+0.0122` | `0.2939` |
| `V2_3d_volume_sides` | `0.2824` | `-0.0339` | `0.1993` | `+0.0035` | `0.2364` |
| `V3_medium_relative_size` | `0.3022` | `-0.0141` | `0.2017` | `+0.0058` | `0.2651` |
| `V4_all_size_3d_relative` | `0.2830` | `-0.0332` | `0.2229` | `+0.0271` | `0.2431` |

## 6. 결과 해석

- Cold에서는 `V2_3d_volume_sides`가 가장 좋음
- Cold median APE가 `0.3163 -> 0.2824`로 크게 개선됨
- Cold 3D slice도 `0.2936 -> 0.2364`로 개선됨
- Warm에서는 기준 모델 `V0_ho_enhanced_base`가 가장 좋음
- 3D 피처와 상대 크기 피처는 Cold에는 도움이 되지만 Warm에는 소폭 악화됨
- 크기 구간 피처는 Warm / Cold 모두 개선하지 못함
- 전체 조합은 Cold는 좋지만 Warm 악화가 커서 공통 채택에는 부적합함

## 7. 가설별 판단

- H23
- 크기 구간/극단 크기 피처는 채택 기준을 넘지 못함
- H24
- 3D 부피/변 길이 피처는 Cold와 Cold 3D slice를 크게 개선하므로 Cold 채택 후보
- H25
- 재료 내 상대 크기 순위는 Cold를 개선하지만 Warm을 악화시켜 Cold 채택 후보
- Warm / Cold에서 필요한 피처 구성이 다를 가능성이 커졌으므로 H29에서 종합 필요

## 8. 결론

- 결론: 부분 채택
- H23은 중단
- H24는 Cold 채택 후보
- H25는 Cold 채택 후보
- Warm은 H19-H22의 `V0_ho_enhanced_base` 기준을 유지하는 것이 현재 최선
- Cold는 `V2_3d_volume_sides` 또는 `V4_all_size_3d_relative`를 추가 후보로 둠

## 9. 다음 할 일

- H29에서 Warm / Cold 피처 구성을 분리해야 하는지 종합 판단
- H30에서 전체 성능뿐 아니라 3D, 대형, 재료별 약점 slice 개선 여부 확인
- Cold 후보는 반복 안정성 검증 후 최종 채택 여부 결정
