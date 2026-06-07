# PP-K5 Huber 선행 + CatBoost segment 규칙 보정

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `baseline` | `reference_to_PP-J3` | `0.2912` | `0.4063` | `1.2508` | `0.5530` |
| `warm` | `corrected_warm_catboost_leaf_artist_size` | `reference_to_PP-J3` | `0.2912` | `0.4063` | `1.2508` | `0.5530` |
