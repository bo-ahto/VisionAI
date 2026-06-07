# PP-P2 Quantile width 기반 모델 선택 라우팅

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `baseline_component_baseline_lgb` | `routing_component` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |  |
| `cold` | `quantile_width_model_routing` | `width_segment_selected_model` | `0.3875` | `0.6737` | `1.8166` | `0.6786` |  |
| `cold` | `baseline_component_pp_o2_hgb` | `routing_component` | `0.3921` | `0.7016` | `1.9836` | `0.6872` |  |
| `cold` | `baseline_component_pp_n1_q50` | `routing_component` | `0.3972` | `0.6618` | `1.7709` | `0.6798` |  |
| `warm` | `baseline_component_pp_d4` | `routing_component` | `0.1687` | `0.3053` | `0.9460` | `0.4440` |  |
| `warm` | `quantile_width_model_routing` | `width_segment_selected_model` | `0.1697` | `0.3063` | `0.9460` | `0.4452` |  |
| `warm` | `baseline_component_pp_l8` | `routing_component` | `0.1808` | `0.3152` | `0.9341` | `0.4285` |  |
| `warm` | `baseline_component_baseline_huber` | `routing_component` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |  |
