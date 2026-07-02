# Warm Huber HCOEF18 완료 메모

PP-HCOEF18은 이미 실행 완료된 실험이다.

- 실험 내용: quantile width를 위험도 신호로 사용해 HCOEF 안정 후보의 점 예측을 제한적으로 이동하는 방식 검증.
- 주요 결과: fixed test MdAPE는 `0.1361`까지 개선됐지만 MAPE가 `0.2731~0.2732`로 현재 기준 후보 `0.2730`보다 소폭 악화됐고, 반복 검증 gate를 통과하지 못했다.
- 판단: 운영 기본 후보로 채택하지 않고 보류한다.
- 활용 방향: quantile width는 점 예측 이동보다는 가격 범위, 신뢰도, 큰 오차 위험 표시용 피처로 우선 사용한다.

최신 `/goal` 프롬프트는 아래 문서를 사용한다.

- `docs/track6/experiments/warm_huber_hcoef19_continuation_goal_prompt.md`
- `docs/track6/experiments/warm_huber_continuous_max_performance_goal_prompt.md`
