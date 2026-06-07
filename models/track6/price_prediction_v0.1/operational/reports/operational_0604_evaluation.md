# operational v0.1 0604 평가

- 작성일: 2026-06-05T12:01:44
- 전체 행: 6,873
- 숫자 가격 라벨: 837
- 50달러 미만 검수 필요 라벨: 8

## 서비스 적용 판단

- 서비스 주 후보: `service_primary`
- 현재 구현: `pp_v8_compact_blend_mape_guarded`
- 이유: 0604 신규 Warm 라벨에서 70:30 결합보다 MdAPE, MAPE, p95_APE가 모두 낮음
- 50달러 미만 검수 라벨 제외 기준: MdAPE `0.2298`, MAPE `0.3359`, p95_APE `0.9273`
- 70:30 결합 후보는 보고서 기준 후보로 유지하되, 실제 서비스 출력 기본값은 `service_primary_pred_price_krw`를 사용

## 후보 성능

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| numeric_actual_all | pp_v2_defensive | 837 | 0.2303 | 15.5753 | 1.1513 | 0.9388 | 0.9368 | 18 | 42 |
| numeric_actual_all | pp_v8_compact_blend_mape_guarded | 837 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 0.9341 | 12 | 58 |
| numeric_actual_all | service_primary | 837 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 0.9341 | 12 | 58 |
| numeric_actual_all | v01_operational | 837 | 0.2835 | 32.2879 | 0.9996 | 1.3141 | 0.9295 | 16 | 79 |
| numeric_actual_all | svc_numeric_seed_mean | 837 | 0.3174 | 47.2696 | 1.0882 | 1.4258 | 0.9254 | 19 | 108 |
| numeric_actual_all | l10_generated_bucket_seq | 837 | 0.3283 | 13.3101 | 1.3258 | 1.1943 | 0.9576 | 20 | 108 |
| numeric_actual_excluding_under_50_usd | pp_v2_defensive | 829 | 0.2263 | 0.3623 | 1.0902 | 0.7131 | 0.9329 | 10 | 42 |
| numeric_actual_excluding_under_50_usd | pp_v8_compact_blend_mape_guarded | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 |
| numeric_actual_excluding_under_50_usd | service_primary | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 |
| numeric_actual_excluding_under_50_usd | v01_operational | 829 | 0.2779 | 0.3774 | 0.9871 | 1.1628 | 0.9248 | 8 | 79 |
| numeric_actual_excluding_under_50_usd | svc_numeric_seed_mean | 829 | 0.3072 | 0.4318 | 0.9998 | 1.2810 | 0.9204 | 11 | 108 |
| numeric_actual_excluding_under_50_usd | l10_generated_bucket_seq | 829 | 0.3207 | 0.4598 | 1.2569 | 1.0793 | 0.9536 | 14 | 108 |

## 추가 산출물

- 후보별 행 단위 오차: `outputs/0604_evaluation/operational_predictions_with_actual.csv`
- 서비스 주 후보 큰 오차 상위 100건: `outputs/0604_evaluation/service_primary_largest_errors_top100.csv`
- 50달러 미만 검수 라벨 제외 큰 오차 상위 100건: `outputs/0604_evaluation/service_primary_largest_errors_excluding_under_50_top100.csv`
