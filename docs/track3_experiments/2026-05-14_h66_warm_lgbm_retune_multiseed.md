# H66 Warm LightGBM 재튜닝 multi-seed 기록

- 실험 ID: `H66_warm_lgbm_retune_multiseed`
- 날짜: 2026-05-14
- 목적:
- H62에서 확인된 Warm LightGBM 재튜닝 개선 신호가 multi-seed에서도 유지되는지 확인
- 실행 스크립트:
- [`scripts/track3/h66_warm_lgbm_retune_multiseed.py`](/Users/bo/VisionAI/scripts/track3/h66_warm_lgbm_retune_multiseed.py:1)
- 결과 파일:
- [`data/track3_h66_warm_lgbm_retune_multiseed_results.json`](/Users/bo/VisionAI/data/track3_h66_warm_lgbm_retune_multiseed_results.json:1)

## 1. 사용 데이터

- 학습 데이터:
- `data/release_split/track3_train.csv`
- Warm 평가:
- `data/release_split/track3_test_warm.csv`

## 2. 비교 후보

- `h31_current_like`
- 기존 H31 current-like 설정
- `larger_low_lr`
- 더 낮은 learning rate와 더 큰 tree 용량을 둔 후보
- `smaller_regularized`
- 더 강한 규제와 작은 tree 용량을 둔 후보

## 3. 평가 방식

- seed:
- `11`
- `22`
- `33`
- 각 seed별 LightGBM 학습 후 Warm test 평가
- 주요 판단 지표:
- mean median APE
- std median APE
- mean p95 APE

## 4. 결과

| 후보 | mean median APE | std | mean p95 APE |
|---|---:|---:|---:|
| `h31_current_like` | `0.1090` | `0.0065` | `0.9866` |
| `larger_low_lr` | `0.1051` | `0.0059` | `0.9679` |
| `smaller_regularized` | `0.1284` | `0.0043` | `0.9814` |

## 5. 해석

- `larger_low_lr`가 평균 median APE 기준으로 가장 좋음
- 기존 `h31_current_like` 대비 `-0.0039` 개선
- p95 APE도 `0.9866 -> 0.9679`로 소폭 개선
- 표준편차도 `0.0065 -> 0.0059`로 조금 낮음
- `smaller_regularized`는 안정성은 있지만 median APE가 크게 악화되어 기각

## 6. 결론

- H62 개선 신호는 multi-seed에서도 유지됨
- Warm 최종 후보는 기존 H31 current-like 설정에서 `larger_low_lr` 설정으로 갱신하는 것이 타당함
- 결론 표기:
- `채택`

## 7. 다음 할 일

- production 학습 스크립트의 Warm LightGBM 설정을 `larger_low_lr` 기준으로 반영 검토
- 최종 운영안 문서에서 Warm 후보 성능을 `0.1051` 기준으로 업데이트
- H16 temporal-safe 문제가 해결되면 동일 설정으로 작가 이력 피처 안전성 재검증
