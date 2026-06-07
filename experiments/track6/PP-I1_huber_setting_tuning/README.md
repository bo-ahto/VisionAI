# PP-I1 Huber 설정값 조정

- 목적: 최종 후보로 남길 설정, 보정 강도, 라우팅 기준, 통합 후보를 같은 기준으로 확인한다.
- 기준: validation 기준으로 선택하고 test 결과는 재현성 확인으로만 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `warm` | `eps1.35_alpha0.001` | `huber_setting_grid` | `0.2126` | `0.4167` | `1.3192` | `0.6446` |
| `warm` | `baseline_eps1.35_alpha0.0001` | `huber_setting_grid` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |
| `warm` | `eps1.35_alpha0.00001` | `huber_setting_grid` | `0.2127` | `0.4167` | `1.3193` | `0.6446` |
| `warm` | `eps1.20_alpha0.0001` | `huber_setting_grid` | `0.2134` | `0.4127` | `1.2934` | `0.6478` |
| `warm` | `eps1.50_alpha0.0001` | `huber_setting_grid` | `0.2190` | `0.4192` | `1.3315` | `0.6429` |
