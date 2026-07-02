# Warm Huber HCOEF19 완료 메모

PP-HCOEF19는 이미 실행 완료된 실험이다.

- 실험 내용: 연구 산출물과 운영 v0.1 Warm 피처 파이프라인 산출물이 같은 component를 생성하는지 감사.
- 주요 결과:
  - 0604 공통 Warm 829건에서 `svc`, `current_70_30`, `ppv8`, `l10`, `quantile_width`, `price_range_ratio`가 연구 산출물과 운영 산출물 사이에서 모두 로그 차이 `0.0`으로 일치.
  - 운영 공식 `ppv8 = 0.75 * pp_v2 + 0.25 * l10`, `v01 = 0.70 * svc + 0.30 * ppv8`, `service_primary = ppv8` 모두 통과.
  - 운영 Warm 입력 필수 피처 누락 `0`개.
- 판단: 새 점 예측 후보는 채택하지 않음. 다음 HCOEF 실험은 피처 파이프라인 mismatch 걱정 없이 진행 가능.

최신 `/goal` 프롬프트는 아래 문서를 사용한다.

- `docs/track6/experiments/warm_huber_hcoef20_continuation_goal_prompt.md`
- `docs/track6/experiments/warm_huber_continuous_max_performance_goal_prompt.md`
