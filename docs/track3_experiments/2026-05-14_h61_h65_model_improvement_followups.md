# H61-H65 모델 성능 개선 후속 실험 기록

- 실험 ID: `H61_H65_model_improvement_followups`
- 날짜: 2026-05-14
- 목적:
- H31/H32 후보를 기준으로 모델 성능 개선 가능성을 추가 확인
- 실행 스크립트:
- [`scripts/track3/h61_h65_model_improvement_followups.py`](/Users/bo/VisionAI/scripts/track3/h61_h65_model_improvement_followups.py:1)
- 결과 파일:
- [`data/track3_h61_h65_model_improvement_followups_results.json`](/Users/bo/VisionAI/data/track3_h61_h65_model_improvement_followups_results.json:1)

## 1. 기준 모델

- Warm 기준:
- H31 LightGBM 후보
- 3 seed 평균 예측 기준 median APE `0.1084`
- Cold 기준:
- H32 LAD 조건부 fallback
- median APE `0.2786`

## 2. H62 결과: H31 피처셋 기준 LightGBM 재튜닝

- 가설:
- Warm에서는 LightGBM 튜닝을 H31 피처 기준으로 다시 하면 성능이 개선될 것이다
- 실험 방법:
- H31 피처셋을 유지하고 LightGBM 설정 3종 비교
- 결과:
- `h31_current_like`: `0.1002`
- `smaller_regularized`: `0.1234`
- `larger_low_lr`: `0.1027`
- 해석:
- 단일 seed 기준으로는 H31 평균 기준 `0.1084`보다 낮은 결과가 나옴
- 특히 `h31_current_like`, `larger_low_lr`는 개선 신호가 있음
- 판단:
- 부분 검증
- 바로 채택하지 않고 multi-seed 재검증 필요

## 3. H63 결과: Cold LAD alpha 튜닝

- 가설:
- Cold LAD의 규제 강도 alpha를 조정하면 성능과 안정성이 개선될 것이다
- 실험 방법:
- `alpha = 0, 0.0001, 0.001, 0.01` 비교
- 결과:
- `alpha=0`: `0.3163`
- `alpha=0.0001`: `0.3343`
- `alpha=0.001`: `0.3561`
- `alpha=0.01`: `0.3901`
- 판단:
- alpha를 키우면 성능이 악화됨
- Cold LAD alpha 튜닝은 기각

## 4. H65 결과: Warm 저이력 작가 blending

- 가설:
- Warm 예측값과 작가별 기준가격을 blending하면 저이력 작가 성능이 개선될 것이다
- 실험 방법:
- 저이력 작가일수록 H31 예측을 작가 중앙값 쪽으로 일부 섞음
- 결과:
- H31 전체 Warm: `0.1084`
- 20% blend: `0.1099`
- 35% blend: `0.1101`
- graded blend: `0.1083`
- 저이력 1~3건:
- H31 `0.1608`
- graded blend `0.1699`
- 해석:
- 전체 Warm은 아주 소폭 개선됐지만 저이력 구간은 악화됨
- 판단:
- 미채택
- 저이력 보완책으로는 부족함

## 5. H61 결과: Cold slice별 tree expert

- 가설:
- Cold에서는 비선형 모델이 전체는 약해도 특정 slice에서는 선형보다 우세할 것이다
- 실험 방법:
- Cold H32를 기준으로 3D, 대형, 3D 또는 대형 구간에 tree expert를 적용
- 결과:
- H32 base: `0.2786`
- tree for 3D: `0.4776`
- tree for large: `0.3007`
- tree for 3D or large: `0.4795`
- tree for very large: `0.3052`
- 판단:
- tree expert는 전체와 target slice 모두 악화
- H61 기각

## 6. H64 결과: Cold robust ensemble

- 가설:
- Cold 예측값을 robust ensemble로 결합하면 tail risk가 줄어들 것이다
- 실험 방법:
- LAD, Huber, Ridge, 평균 ensemble, 중앙값 ensemble 비교
- 결과:
- LAD base: `0.3163`
- Huber: `0.3257`
- Ridge: `0.3061`
- LAD+Huber 평균: `0.3296`
- LAD/Huber/Ridge 중앙값: `0.3132`
- 해석:
- Ridge 단독은 LAD base보다 median APE와 p90/p95가 개선됨
- 다만 H32 조건부 fallback `0.2786`보다 좋지는 않음
- 판단:
- 검증 완료
- H32 조건부 fallback을 대체할 성능 근거가 없어 미채택

## 7. 결론

- H62:
- 개선 신호 있음
- multi-seed 재검증 필요
- H63:
- 기각
- alpha 튜닝은 악화
- H65:
- 미채택
- 전체 개선은 미미하고 저이력 구간 개선 실패
- H61:
- 기각
- tree expert 악화
- H64:
- 검증 완료
- Ridge base는 H32를 대체하지 못해 미채택

## 8. 다음 할 일

- H62 후속:
- `h31_current_like`, `larger_low_lr`를 3개 이상 seed로 재검증
- H65 후속:
- 저이력 Warm은 blending보다 신뢰도/가격 범위 정책으로 우선 관리
