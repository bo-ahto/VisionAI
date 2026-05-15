# H29-H30 Warm/Cold 피처 정책 및 slice 분석 기록

- 실험 ID: `H29_H30_feature_policy_slice_analysis`
- 날짜: 2026-05-14
- 상태: 종결
- 관련 가설: H29, H30
- 실행 스크립트: [`scripts/track3/h29_h30_feature_policy_slice_analysis.py`](/Users/bo/VisionAI/scripts/track3/h29_h30_feature_policy_slice_analysis.py:1)
- 결과 파일: [`data/track3_h29_h30_feature_policy_slice_results.json`](/Users/bo/VisionAI/data/track3_h29_h30_feature_policy_slice_results.json:1)

## 1. 실험 목적

- H19-H28 결과를 종합해 Warm과 Cold에 같은 피처 세트를 써도 되는지 확인
- 전체 median APE 개선이 실제로 어느 slice에서 발생하는지 확인
- 최종 후보 피처 정책을 Warm / Cold로 분리할 필요가 있는지 판단

## 2. 비교 피처 정책

| variant | 설명 |
|---|---|
| `V0_warm_policy_ho_enhanced` | H19-H22 기준 Warm 최적 후보 |
| `V1_cold_policy_3d` | 호수 강화 기준 + 3D 여부/부피/긴 변 피처 |
| `V2_cold_policy_relative` | 호수 강화 기준 + 재료 내 상대 크기 피처 |
| `V3_cold_policy_3d_relative` | 3D 피처와 상대 크기 피처를 함께 추가 |

## 3. 전체 성능 결과

| variant | Cold median APE | Cold 변화 | Warm median APE | Warm 변화 |
|---|---:|---:|---:|---:|
| `V0_warm_policy_ho_enhanced` | `0.3163` | `+0.0000` | `0.1958` | `+0.0000` |
| `V1_cold_policy_3d` | `0.2824` | `-0.0339` | `0.1993` | `+0.0035` |
| `V2_cold_policy_relative` | `0.3022` | `-0.0141` | `0.2017` | `+0.0058` |
| `V3_cold_policy_3d_relative` | `0.2835` | `-0.0328` | `0.2125` | `+0.0167` |

## 4. H29 판단

- Warm 최적 후보는 `V0_warm_policy_ho_enhanced`
- Cold 최적 후보는 `V1_cold_policy_3d`
- 같은 피처 세트를 Warm / Cold에 공통 적용하면 한쪽 성능이 손해를 봄
- Cold용 3D 피처는 Cold를 크게 개선하지만 Warm은 소폭 악화됨
- 따라서 Warm과 Cold는 피처 정책을 분리하는 것이 맞음

## 5. H30 slice 결과

| slice | 기준 Cold | 3D 후보 Cold | 변화 |
|---|---:|---:|---:|
| 전체 Cold | `0.3163` | `0.2824` | `-0.0339` |
| Cold 2D | `0.3767` | `0.6071` | `+0.2304` |
| Cold 3D | `0.2936` | `0.2364` | `-0.0572` |
| Cold 대형 호수 | `0.5130` | `0.4448` | `-0.0682` |
| Cold 초대형 호수 | `0.7432` | `0.5522` | `-0.1909` |
| Cold very large area | `0.4307` | `0.4448` | `+0.0141` |
| Cold oil | `0.2364` | `0.2023` | `-0.0341` |
| Cold acrylic | `0.3480` | `0.3738` | `+0.0258` |
| Cold other | `0.6035` | `0.4586` | `-0.1448` |
| Cold pencil | `0.2936` | `0.1611` | `-0.1325` |
| Cold ink | `0.1120` | `0.2346` | `+0.1226` |

## 6. 결과 해석

- Cold 전체 개선은 주로 3D, 대형/초대형 호수, `other`, `pencil` slice에서 발생함
- Cold 2D는 오히려 크게 악화됨
- 따라서 3D 피처를 Cold 전체에 무조건 적용하는 것은 위험함
- 운영 후보는 `Cold 3D 전용 보정` 또는 `Cold 3D 작품에만 3D 피처 적용` 방식이 더 적절함
- Warm에서는 3D 후보를 넣으면 전체는 소폭 악화되고, 2D와 대형 구간도 악화됨
- Warm은 기존 호수 강화 피처 세트를 유지하는 것이 현재 기준에서 가장 안정적임

## 7. 가설별 판단

- H29
- 검증 완료
- Warm과 Cold는 필요한 피처 구성이 다름
- Warm 후보: `V0_warm_policy_ho_enhanced`
- Cold 후보: `V1_cold_policy_3d`
- 단, Cold 2D 악화 때문에 Cold 전체 모델 교체가 아니라 Cold 3D 조건부 적용이 필요함
- H30
- 검증 완료
- 파생 피처 개선은 전체에 고르게 나타나지 않음
- 3D/대형/특정 재료 slice 개선과 2D/ink 악화가 함께 나타남
- 따라서 전체 median APE만으로 채택하면 안 되고 slice 기준 안전장치가 필요함

## 8. 결론

- 결론: 부분 채택
- Warm은 H19-H22 호수 강화 피처 세트 유지
- Cold는 3D 피처가 강한 개선 후보지만, 2D 악화 때문에 조건부 적용으로 제한
- 최종 운영안은 `Warm 모델`, `Cold 기본 모델`, `Cold 3D 보정 후보`를 분리해 검토해야 함

## 9. 다음 할 일

- Cold 3D 조건부 적용 실험 추가
- Cold 2D에는 기존 Cold 기본 모델을 유지하고, Cold 3D에만 3D 피처 후보를 적용하는 fallback 검증
- 최종 후보 모델 문서에 Warm/Cold/Cold 3D 정책을 분리해 정리
