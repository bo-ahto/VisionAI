# PP-F4 신뢰도별 가격 범위 차등 적용

- 목적: 단일 가격 예측을 서비스에서 어떤 범위와 신뢰도 문구로 보여줄지 검증한다.
- 기준: 범위 폭과 등급 기준은 validation에서 정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | 포함률 | 범위비 중앙값 |
|---|---|---|---:|---:|---:|---:|---:|
| `cold` | `tiered_range_by_confidence` | `confidence_tiered_range` | `0.3851` | `0.7169` | `2.0250` | `0.8006` | `4.9696` |
| `warm` | `tiered_range_by_confidence` | `confidence_tiered_range` | `0.2126` | `0.4167` | `1.3194` | `0.8015` | `2.8457` |
