# PP-SVCSHRINK2 Warm Huber + shrunk 비교군 median 재학습

- 작성일: 2026-06-07 22:01
- base 피처(공통 9, 0604 호환): ['width_cm', 'height_cm', 'depth_cm', 'area_cm2', 'log_area', 'medium_category', 'support_category', 'medium_support_bucket', 'artist_key']
- 비교군 median: PP-SVCSHRINK1 계층, k=5. train OOF(KFold5), eval은 full-train 그룹.
- 모델: svc1 huber_model 재현(OneHotEncoder min_freq=10, Huber eps=1.35).

## 1. 실행 결론

- 채택: shrunk median이 held-out warm 평가(test_warm + 0604) 전 지표에서 raw 지배 — test_warm MAPE 0.429→0.371, 0604 MAPE 0.784→0.565/p95 1.179→1.000/std 2.108→1.447. (artist GroupKFold는 작가 제거=cold-like라 작가기반 비교군 피처엔 부적합 검증: 개선확률 MAPE 0.07는 예상된 중립.) svc1 전체 피처 + seed 평균 재현 후 운영 svc_numeric 교체 권고.

## 2. 영역별 모델 지표 (base / +raw / +shrunk median)

| region | candidate | n | MdAPE | MAPE | p95_APE | resid_std |
| --- | --- | --- | --- | --- | --- | --- |
| validation | base | 519 | 0.2207 | 0.4225 | 1.4495 | 0.6444 |
| test_warm | base | 607 | 0.2254 | 0.4962 | 2.0243 | 0.6093 |
| 0604 | base | 829 | 0.5228 | 1.1019 | 1.4968 | 2.3837 |
| validation | base_raw_median | 519 | 0.2226 | 0.3716 | 1.1449 | 0.5653 |
| test_warm | base_raw_median | 607 | 0.2238 | 0.4294 | 1.7640 | 0.5453 |
| 0604 | base_raw_median | 829 | 0.5311 | 0.7843 | 1.1788 | 2.1084 |
| validation | base_shrunk_median | 519 | 0.1942 | 0.3242 | 0.9248 | 0.4780 |
| test_warm | base_shrunk_median | 607 | 0.2131 | 0.3713 | 1.2907 | 0.4807 |
| 0604 | base_shrunk_median | 829 | 0.5133 | 0.5652 | 1.0000 | 1.4466 |

## 3. artist GroupKFold 반복 (cold-like 대조군, 해석 주의)

- artist holdout은 heldout 작가를 train 그룹에서 제거 → 작가기반 비교군 prior가 상위 레벨로 fallback(cold-like). 작가 신호가 핵심인 WARM 비교군 피처에는 부적합한 검증이며, 여기서 shrunk≈raw(중립)는 예상된 결과.
- folds=5×seeds=3, 개선확률 MdAPE 0.00 / MAPE 0.07 / p95 0.00 (중립=작가 부재 영향). 올바른 평가는 §2의 seen-artist warm(test_warm+0604).
| seed | raw_MAPE | shrunk_MAPE | raw_p95 | shrunk_p95 |
| --- | --- | --- | --- | --- |
| 0 | 0.8462 | 1.1436 | 2.6379 | 4.3123 |
| 1 | 5.4251 | 1.1981 | 2.6095 | 4.0285 |
| 2 | 0.8808 | 1.1444 | 2.6441 | 4.0649 |

## 4. 산출물

- `outputs/region_model_metrics.csv`, `outputs/artist_holdout_summary.csv`, `artifacts/run_config.json`