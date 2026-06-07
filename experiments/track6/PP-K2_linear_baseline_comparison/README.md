# PP-K2 Ridge/ElasticNet 선형 기준선 비교

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `huber` | `linear_baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `ridge` | `linear_baseline` | `0.2981` | `0.4933` | `1.5369` | `0.6449` |
| `warm` | `elasticnet` | `linear_baseline` | `0.3706` | `0.5740` | `1.6702` | `0.7124` |
