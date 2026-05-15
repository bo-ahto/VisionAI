# H67 Warm 피처 확장 multi-seed 검증 기록

- 날짜: 2026-05-14
- 실험 ID: `H67_warm_feature_extension_multiseed`
- 관련 가설: H57, H58, H66
- 실행 스크립트: `scripts/track3/h67_warm_feature_extension_multiseed.py`
- 결과 파일: `data/track3_h67_warm_feature_extension_multiseed_results.json`

## 1. 실험 목적

- H48-H60 실험에서 H57/H58 Warm 피처 확장이 단일 seed 기준 개선 신호를 보였음
- 단일 seed 결과만으로 Warm 후보 피처를 바꾸면 위험함
- 따라서 H66 기준 모델과 같은 조건에서 seed `11`, `22`, `33` 반복 검증을 수행함

## 2. 기준 모델

- 모델: LightGBM
- 기준 설정: H66 `larger_low_lr`
- 기준 피처: H31/H66 Warm 피처셋
- 평가 지표: Warm median APE
- 낮을수록 좋음

## 3. 비교 피처셋

- `h66_base`
- H66 기준 피처셋
- 추가 피처 없음
- `h57_extended_history`
- 작가 가격 min/max
- 작가 가격 p25/p75/p90
- 작가 high-price share
- 작가 가격 range
- `h58_interactions`
- 작가 중앙 가격대 × log_area
- 작가 중앙 가격대 × log_ho
- 작가 작품 수 × log_area
- 작가 작품 수 × 대형 호수 여부
- `h57_h58_combined`
- H57과 H58 피처를 모두 추가

## 4. 결과

| 피처셋 | mean median APE | std | mean p95 APE | H66 대비 |
|---|---:|---:|---:|---:|
| `h66_base` | `0.1051` | `0.0059` | `0.9679` | `+0.0000` |
| `h57_extended_history` | `0.1032` | `0.0034` | `0.9849` | `-0.0019` |
| `h58_interactions` | `0.1092` | `0.0076` | `0.9962` | `+0.0041` |
| `h57_h58_combined` | `0.1042` | `0.0044` | `0.9761` | `-0.0009` |

## 5. 해석

- H57은 평균 median APE가 가장 낮음
- 다만 H66 대비 개선 폭은 `-0.0019`로 채택 기준 `-0.003`에 미달함
- H57은 p95 APE도 `0.9679 -> 0.9849`로 소폭 악화됨
- H58 단독은 median APE와 p95가 모두 악화됨
- H57/H58 결합은 H66보다 약간 좋지만 H57 단독보다 약함

## 6. 결론

- H57은 개선 신호는 있으나 최종 Warm 후보를 교체할 만큼 강하지 않음
- H58은 기각
- H57/H58 결합도 채택하지 않음
- 현재 Warm 최종 후보는 H66 `larger_low_lr` 유지

## 7. 다음 작업

- H57 확장 이력 피처는 추후 데이터가 늘어난 뒤 재검토 가능
- 현재 운영 후보에는 H57/H58 추가 피처를 넣지 않음
