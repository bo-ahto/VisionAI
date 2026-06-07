# Cold prediction v0.2 (operational, search-free) release

- 작성일(고정): 2026-06-07T00:00:00
- 상태: search_free_runnable_artifact (외부 API 의존 0)

## 동기

- v0.1 대표 PP-Y18은 `search_all_external_interaction` 피처(외부 검색 API) 의존 → raw-input 직렬화 불가.
- v0.2는 운영 피처 12개만 사용하는 search-free 변형. 지표는 v0.1과 다름(검색 신호 제거).

## 운영 피처 (12)

- width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket

## 지표 (test, cold 3099행)

- 대표(q50): MdAPE 0.4823 / MAPE 1.2424 / p95 4.3806
- 방어(q50 기반 q40 guard, p95/MAPE 안전): MdAPE 0.4852 / MAPE 1.1771 / p95 4.1223 (적용 824행)

## 참고: v0.1(search 기반) 대표 PP-Y18 test = 0.4247 / 0.991 / 3.305

- v0.2 search-free 대표가 v0.1보다 낮으면 그 차이가 검색 신호 기여분(운영에서 안전하게 못 쓰는 부분)이다.

## 검증

- shipped 예측기 raw-input 재현 max abs diff = 0.00e+00

## 구성

- `models/lgbq_q10|q40|q50|q90.joblib` (LightGBM Quantile, 운영 피처)
- `config/cold_model_policy_v0_2.json`, `config/guard_params_v0_2.json`
- `predict/predict_cold_operational_v0_2.py` (raw 운영 피처 → 예측)
- `manifest/MANIFEST.sha256`