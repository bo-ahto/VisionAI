# v0.1 70:30 재예측 산출물

- 생성일: 2026-06-05T11:30:33
- 입력 피처: `experiments/track6/OP-0605_v01_70_30_reprediction/data/features/features_all_v0_1.csv`
- 전체 행: 6,873
- Warm 행: 6,873
- Cold 행: 0

## 실행한 후보

- `svc_numeric_seed_mean_pred_log`: PP-SVC2 방식으로 seed 10개 Warm Huber를 재학습해 평균낸 예측 로그값
- `pp_v8_distilled_pred_log`: 기존 PP-V8 `compact_blend_mape_guarded` 예측값을 CatBoost로 모사한 재현용 component
- `v01_70_30_repred_log`: `0.70 * svc_numeric_seed_mean_pred_log + 0.30 * pp_v8_distilled_pred_log`

## exact 여부

- v0.1 정책 식 70:30은 그대로 적용했다.
- 단, PP-V8 30% 축은 원천 후보들을 모두 분해 실행한 값이 아니라 기존 PP-V8 예측을 모사한 distillation component다.
- 원천 후보별 단일 artifact가 준비되면 `pp_v8_distilled_pred_log`를 원천 PP-V8 예측값으로 교체해야 완전한 source-decomposed exact 실행이 된다.

## 생성 파일

- `predictions_all.csv`
- `component_diagnostics.csv`
- `prediction_summary.json`
