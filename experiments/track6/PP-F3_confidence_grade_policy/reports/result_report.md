# PP-F3 신뢰도 등급 기준

- 목적: 단일 가격 예측을 서비스에서 어떤 범위와 신뢰도 문구로 보여줄지 검증한다.
- 기준: 범위 폭과 등급 기준은 validation에서 정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | 포함률 | 범위비 중앙값 |
|---|---|---|---:|---:|---:|---:|---:|
| `cold` | `confidence_grade` | `quantile_width_grade` | `0.3851` | `0.7169` | `2.0250` | `nan` | `nan` |
| `cold` | `grade_high` | `quantile_width_grade` | `0.3074` | `0.4096` | `0.8490` | `nan` | `nan` |
| `cold` | `grade_low` | `quantile_width_grade` | `0.5576` | `1.0999` | `3.2765` | `nan` | `nan` |
| `cold` | `grade_medium` | `quantile_width_grade` | `0.3736` | `0.6297` | `2.0785` | `nan` | `nan` |
| `warm` | `confidence_grade` | `quantile_width_grade` | `0.2126` | `0.4167` | `1.3194` | `nan` | `nan` |
| `warm` | `grade_high` | `quantile_width_grade` | `0.1790` | `0.3462` | `1.0854` | `nan` | `nan` |
| `warm` | `grade_low` | `quantile_width_grade` | `0.2573` | `0.5167` | `1.7192` | `nan` | `nan` |
| `warm` | `grade_medium` | `quantile_width_grade` | `0.2126` | `0.3836` | `1.2185` | `nan` | `nan` |
