# H32 Cold 3D 조건부 fallback 재검증 기록

- 실험 ID: `H32_cold_3d_conditional_fallback`
- 날짜: 2026-05-14
- 상태: 종결
- 관련 가설: H24, H29, H30
- 실행 스크립트: [`scripts/track3/h32_cold_3d_conditional_fallback.py`](/Users/bo/VisionAI/scripts/track3/h32_cold_3d_conditional_fallback.py:1)
- 결과 파일: [`data/track3_h32_cold_3d_conditional_fallback_results.json`](/Users/bo/VisionAI/data/track3_h32_cold_3d_conditional_fallback_results.json:1)

## 1. 재실험 이유

- H29-H30에서 Cold 3D 피처는 전체 Cold 성능을 개선했음
- 하지만 Cold 2D slice는 크게 악화됨
- 따라서 3D 피처를 Cold 전체에 일괄 적용하지 않고 3D 작품에만 적용하는 방식이 더 적절한지 확인함

## 2. 비교 방식

| variant | 설명 |
|---|---|
| `V0_base_for_all` | 모든 Cold 작품에 기존 호수 강화 Cold 모델 사용 |
| `V1_3d_features_for_all` | 모든 Cold 작품에 3D 피처 포함 모델 사용 |
| `V2_conditional_3d_fallback` | 2D는 기존 모델, 3D는 3D 피처 모델 사용 |

## 3. 결과

| variant | Cold median APE | 기준 대비 | Cold 2D | Cold 3D |
|---|---:|---:|---:|---:|
| `V0_base_for_all` | `0.3163` | `+0.0000` | `0.3767` | `0.2936` |
| `V1_3d_features_for_all` | `0.2824` | `-0.0339` | `0.6071` | `0.2364` |
| `V2_conditional_3d_fallback` | `0.2786` | `-0.0376` | `0.3767` | `0.2364` |

## 4. 해석

- 3D 피처를 전체 Cold에 적용하면 전체 성능은 좋아지지만 2D가 크게 나빠짐
- 조건부 fallback은 2D 성능을 기존과 동일하게 유지함
- 동시에 3D 성능은 `0.2936 -> 0.2364`로 개선됨
- 전체 Cold median APE도 `0.3163 -> 0.2786`으로 가장 좋음

## 5. 결론

- 결론: 채택 후보
- Cold 최적 후보는 단일 모델 교체가 아니라 조건부 정책이 더 적절함
- 운영 후보
- 2D Cold: 기존 호수 강화 Cold 모델
- 3D Cold: 3D 피처 포함 Cold 모델
- 전체 Cold 기준 현재 최고 후보
- `V2_conditional_3d_fallback`
- Cold median APE `0.2786`

## 6. 다음 할 일

- 조건부 정책을 production 후보 구조에 반영할 수 있는지 확인
- 최종 Cold 후보 확정 후 prediction interval calibration을 다시 수행
