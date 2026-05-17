# T4-E048 실험 누락 점검

- 날짜: 2026-05-17
- 관련 가설: T4-H36, T4-H37, T4-H38
- 상태: 완료
- 목적: 피처 조합을 찾은 뒤 모델 비교 또는 artifact 검증이 빠진 유사 사례가 있는지 점검

## 1. 점검 기준

- 피처 후보를 정한 뒤 같은 피처셋에서 모델군을 비교했는가
- validation에서 고른 후보를 test에서도 확인했는가
- 최종 후보가 바뀌면 artifact dry-run까지 연결했는가
- Warm / Cold를 같은 기준으로 판단했는가
- 운영 불가 피처가 포함되지 않도록 manifest 검사를 했는가

## 2. 점검 결과

| 항목 | 현재 상태 | 판단 | 필요한 후속 |
|---|---|---|---|
| Warm 최종 피처셋 모델 비교 | T4-E047로 보완 완료 | RandomForest가 Ridge보다 우세 | Warm artifact 교체 dry-run 필요 |
| Cold 최종 피처셋 모델 비교 | 일부만 수행 | E025는 구조-only 기준, 최종 full-size 피처셋 기준 전체 모델 비교는 부족 | Cold final 피처셋으로 Quantile/Huber/Ridge/Tree 재비교 필요 |
| Warm 최종 artifact | T4-E049로 RandomForest 생성 완료 | Ridge보다 성능 개선 | 최종 보고서 반영 |
| Cold 최종 artifact | Quantile 기준 생성 완료 | T4-E050 재비교 후 유지 판단 | 최종 보고서 반영 |
| 가격 범위 정책 | Warm/Cold 각각 검증 | Warm은 가능, Cold는 low_risk 한정 | 모델 교체 후 범위 재계산 필요 |
| 금지 피처 manifest | 자동 검사 존재 | 유지 | 새 artifact 생성 시 필수 실행 |

## 3. 누락으로 보는 항목

- Warm:
  - 최종 피처셋 기준 비선형 비교가 누락되어 있었음
  - T4-E047로 보완 완료
  - 후속으로 RandomForest artifact dry-run 필요
- Cold:
  - 최종 full-size 피처셋 기준 전체 모델군 비교가 아직 부족함
  - E025는 Cold 모델군 비교였지만, 최종 피처셋이 확정되기 전 구조-only 기준이었다.
  - 따라서 Cold도 최종 피처셋 기준 모델 재비교가 필요함
- 최종 보고서:
  - T4-E047 결과를 반영하면 Warm 최종 후보가 바뀔 수 있음
  - 최종 보고서는 artifact 재생성 후 업데이트해야 함

## 4. 추가 가설

| 가설 ID | 세부 목표 | 가설 요약 | 연구 방법 | 성공 기준 | 상태 |
|---|---|---|---|---|---|
| T4-H36 | T4-G2, T4-G6 | Warm 최종 피처셋에서는 비선형 모델이 Ridge보다 성능을 개선할 수 있다 | 같은 Warm 최종 피처셋으로 Ridge/Tree 모델군을 반복 비교 | test median APE 개선, p95 APE 악화 없음 | 검증 완료 |
| T4-H37 | T4-G3, T4-G6 | Cold 최종 피처셋에서도 모델군을 다시 비교해야 최종 모델을 확정할 수 있다 | Cold full-size 피처셋으로 Quantile/Huber/Ridge/Tree 모델군 비교 | Cold median APE 또는 p95 APE 개선 | 검증 완료 |
| T4-H38 | T4-G8 | Warm 모델이 바뀌면 artifact와 가격 범위 정책도 다시 생성해야 한다 | RandomForest Warm artifact 생성 후 manifest, test 성능, 범위 정책 재계산 | artifact 생성, manifest 통과, 기존보다 성능 유지 | 검증 완료 |

## 5. 권장 진행 순서

- 1순위:
  - 가격 범위 정책 재계산
  - 상태: Warm은 T4-E049에서 재계산 완료, Cold는 Quantile 유지라 기존 정책 유지 가능
- 2순위:
  - 최종 보고서 갱신
  - 이유: artifact와 정책이 확정된 뒤 보고서에 반영해야 함

## 6. 결론

- Warm 비선형 모델 비교 누락은 T4-E047로 보완되었다.
- Cold 최종 피처셋 기준 모델 재비교와 Warm RandomForest artifact dry-run도 T4-E049/T4-E050으로 보완되었다.
- 현재 남은 작업은 최종 보고서와 대시보드에서 운영 후보 표기를 최신 결과 기준으로 정돈하는 것이다.
