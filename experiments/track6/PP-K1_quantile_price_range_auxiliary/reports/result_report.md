# PP-K1 Quantile 가격 범위 보조 모델

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `baseline` | `base_model` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold` | `quantile_q50` | `quantile_q50` | `0.3960` | `0.6610` | `1.7539` | `0.6795` |
| `warm` | `baseline` | `base_model` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `quantile_q50` | `quantile_q50` | `0.3700` | `0.5845` | `1.6368` | `0.7494` |
