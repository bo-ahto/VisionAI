# price_prediction v0.1 운영용 artifact

## 상태

- 생성일: 2026-06-05T11:50:26
- Warm: 운영 추론 가능
- Cold: reference/low confidence, 별도 qwidth artifact화 필요

## Warm 운영 예측식

```text
service_primary_log = pp_v8_compact_blend_mape_guarded

pp_v8_compact_blend_mape_guarded
          = 0.75 * pp_v2_defensive_component
          + 0.25 * l10_generated_bucket_seq

report_70_30_log = 0.70 * svc_numeric_seed_mean
                 + 0.30 * pp_v8_compact_blend_mape_guarded
```

## 운영 기본 후보

- 서비스 출력 기본값: `service_primary_pred_price_krw`
- 서비스 주 후보: `pp_v8_compact_blend_mape_guarded`
- 70:30 결합 후보: `v01_operational_pred_price_krw` 컬럼으로 유지
- 판단 근거: 0604 신규 Warm 라벨 평가에서 `pp_v8_compact_blend_mape_guarded`가 70:30 결합보다 MdAPE, MAPE, p95_APE가 낮음

## 0604 신규 라벨 검증

- 입력 전체: 6,873건
- Warm: 6,873건
- 숫자 가격 라벨: 837건
- 50달러 미만 검수 라벨 제외 기준 service_primary MdAPE: `0.2298`
- 50달러 미만 검수 라벨 제외 기준 service_primary MAPE: `0.3359`
- 50달러 미만 검수 라벨 제외 기준 service_primary p95_APE: `0.9273`
- 상세 평가: `reports/operational_0604_evaluation.md`
- 운영 릴리스 문서: `reports/operational_release_v0_1.md`

## 저장 artifact

- `artifacts/warm_svc_numeric_seed_huber_ensemble.joblib`
- `artifacts/warm_pp_v2_defensive_component.cbm`
- `artifacts/warm_l10_generated_q10.cbm`
- `artifacts/warm_l10_generated_q50.cbm`
- `artifacts/warm_l10_generated_q90.cbm`
- `artifacts/warm_l10_generated_huber_centerline.joblib`
- `artifacts/warm_l10_generated_residual_catboost.cbm`
- `artifacts/operational_policy_manifest.json`

## 검증 메모

- L10 생성 bucket 순차 component test MdAPE: `0.1743`
- PP-V2 방어 component distillation fidelity RMSE_log: `0.3534`
- PP-V2 방어 component distillation fidelity MdAE_log: `0.1590`

## 실행

피처 추출:

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \
  --input data/test_new_artworks_test_noprice_0604.csv \
  --output-dir models/track6/price_prediction_v0.1/operational/outputs/0604_features
```

운영 예측:

```bash
python3 models/track6/price_prediction_v0.1/operational/scripts/predict_operational_v0_1.py \
  --feature-dir models/track6/price_prediction_v0.1/operational/outputs/0604_features \
  --output-dir models/track6/price_prediction_v0.1/operational/outputs/0604_predictions
```
