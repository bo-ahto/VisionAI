# operational v0.1 예측 결과

- 생성일: 2026-06-05T11:59:58
- 입력 피처: `models/track6/price_prediction_v0.1/operational/outputs/0604_features/features_all_v0_1.csv`
- 전체 행: 6,873
- Warm 행: 6,873
- Cold 행: 0

## 주요 컬럼

- `svc_numeric_seed_mean_pred_price_krw`
- `pp_v2_defensive_pred_price_krw`
- `l10_generated_bucket_seq_pred_price_krw`
- `pp_v8_compact_blend_mape_guarded_pred_price_krw`
- `v01_operational_pred_price_krw`
- `service_primary_pred_price_krw`
- `service_range_low_price_krw`
- `service_range_high_price_krw`
- `service_confidence_tier`

## 예측식

```text
pp_v8 = 0.75 * pp_v2_defensive + 0.25 * l10_generated_bucket_seq
report_70_30 = 0.70 * svc_numeric_seed_mean + 0.30 * pp_v8
service_primary = pp_v8
```
