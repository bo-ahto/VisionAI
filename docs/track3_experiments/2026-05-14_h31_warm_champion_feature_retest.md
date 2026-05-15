# H31 Warm champion 기준 호수/3D 피처 재검증 기록

- 실험 ID: `H31_warm_champion_feature_retest`
- 날짜: 2026-05-14
- 상태: 종결
- 관련 가설: H17, H19, H20, H21, H22, H24, H29
- 실행 스크립트: [`scripts/track3/h31_warm_champion_feature_retest.py`](/Users/bo/VisionAI/scripts/track3/h31_warm_champion_feature_retest.py:1)
- 결과 파일: [`data/track3_h31_warm_champion_feature_retest_results.json`](/Users/bo/VisionAI/data/track3_h31_warm_champion_feature_retest_results.json:1)

## 1. 재실험 이유

- 기존 H19-H30 실험의 Warm 기준값은 `0.1958`이었음
- 현재 안정성 검증 기준 Warm 최적 후보는 H17의 `0.1147`임
- 따라서 H19-H30에서 좋았던 호수/3D 피처가 H17 최적 후보 위에서도 추가 개선을 주는지 다시 확인해야 함

## 2. 비교 기준

- 기준 모델
- `V0_h17_champion`
- 모델: tuned LightGBM
- 기본 피처: 작품 구조 피처 + `artist_name_ko` + 작가 이력 피처
- 작가 이력 피처
- `artist_works_log`
- `artist_ln_price_median`
- `artist_ln_price_mean`
- `artist_ln_price_iqr`
- 평가 방식
- Warm test 기준
- 3개 seed 평균 median APE

## 3. 비교 피처

| variant | 추가 피처 |
|---|---|
| `V0_h17_champion` | 추가 없음 |
| `V1_plus_refined_ho_bucket` | 세분화 호수 구간 |
| `V2_plus_large_ho_flags` | 대형/초대형 호수 여부 |
| `V3_plus_all_ho_features` | 세분화 호수, 대형 flag, 호수-면적 관계 피처 |
| `V4_plus_3d_features` | 3D 여부, 부피, 긴 변/짧은 변 |
| `V5_plus_all_ho_and_3d` | 호수 피처 전체 + 3D 피처 전체 |

## 4. 결과

| variant | Warm mean median APE | std | H17 기준 대비 |
|---|---:|---:|---:|
| `V0_h17_champion` | `0.1147` | `0.0051` | `+0.0000` |
| `V1_plus_refined_ho_bucket` | `0.1107` | `0.0047` | `-0.0040` |
| `V2_plus_large_ho_flags` | `0.1153` | `0.0015` | `+0.0006` |
| `V3_plus_all_ho_features` | `0.1121` | `0.0065` | `-0.0026` |
| `V4_plus_3d_features` | `0.1094` | `0.0060` | `-0.0053` |
| `V5_plus_all_ho_and_3d` | `0.1090` | `0.0065` | `-0.0057` |

## 5. 해석

- H17 기준으로 다시 봐도 호수/3D 파생 피처는 Warm에서 추가 개선을 만듦
- 가장 좋은 후보는 `V5_plus_all_ho_and_3d`
- Warm median APE는 `0.1147 -> 0.1090`으로 개선됨
- 단독 대형 호수 flag는 개선이 없어 단독 채택 근거가 약함
- 세분화 호수 구간은 단독으로도 `0.1147 -> 0.1107` 개선되어 유지 가치가 있음

## 6. 결론

- 결론: 채택 후보
- Warm 최적 후보는 기존 H17에서 `H17 + 호수 전체 + 3D 피처`로 갱신 가능
- 현재 Warm 안정성 기준 최고 후보
- `V5_plus_all_ho_and_3d`
- Warm mean median APE `0.1090`

## 7. 다음 할 일

- PR7의 Warm 최고 탐색 기록 `0.1031`을 같은 release split / 운영 가능 피처 기준으로 재확인
- 최종 Warm 후보는 아래 둘을 비교해야 함
- H31 `V5_plus_all_ho_and_3d`
- PR7 운영 가능 피처 재확인 후보
