# PP-O1 Warm 설명 가능한 비선형 모델

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `warm` | `baseline_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |  |
| `warm` | `hist_gradient_boosting` | `explainable_nonlinear_candidate` | `0.3570` | `0.5833` | `1.5106` | `0.6527` |  |
