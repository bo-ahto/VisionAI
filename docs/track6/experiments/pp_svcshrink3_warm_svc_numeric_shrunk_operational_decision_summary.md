# PP-SVCSHRINK3 svc_numeric 전체 재현 + shrunk median 운영 교체 결정

- 작성일: 2026-06-07 22:16
- 피처: svc1 svc_numeric(warm base 13 + SVC_NUMERIC). 모델: svc1 Huber. k=5, crossfit single-seed.
- shrunk: svc_group_log_price_median만 SVCSHRINK1 EB-shrunk로 교체(다른 svc stats raw 유지). train OOF, eval full-train.
- 선택: validation 반복 holdout(PP-SVC4식, 고정 예측 subsample). test_warm + 0604 확인.

## 1. 실행 결론

- 조건부 채택: shrunk가 held-out test_warm+0604 전 지표 지배(test_warm MAPE 0.296→0.281, 0604 raw→shrunk MAPE 0.451→0.434/p95 1.000→0.999/std 1.640→1.379). 단 validation MdAPE 소폭 악화(예) + 반복 holdout 중립(MAPE 0.53/p95 0.51, artist scheme는 우세) = center-vs-tail 트레이드오프. 운영 반영 전 svc_numeric_seed_mean 전체 재현 + 고정 split 최종 확인 권고.

## 2. 영역별 지표 (baseline / svc_numeric raw / shrunk)

| region | candidate | n | MdAPE | MAPE | p95_APE | resid_std |
| --- | --- | --- | --- | --- | --- | --- |
| validation | baseline | 519 | 0.2126 | 0.4167 | 1.3194 | 0.6438 |
| test_warm | baseline | 607 | 0.2274 | 0.4952 | 2.0130 | 0.6080 |
| 0604 | baseline | 829 | 0.5546 | 0.7334 | 2.2939 | 2.2170 |
| validation | svc_numeric_raw | 519 | 0.1212 | 0.2170 | 0.6502 | 0.3389 |
| test_warm | svc_numeric_raw | 607 | 0.1528 | 0.2956 | 0.9694 | 0.4252 |
| 0604 | svc_numeric_raw | 829 | 0.3574 | 0.4510 | 1.0000 | 1.6401 |
| validation | svc_numeric_shrunk | 519 | 0.1363 | 0.2171 | 0.6544 | 0.3370 |
| test_warm | svc_numeric_shrunk | 607 | 0.1464 | 0.2813 | 0.9329 | 0.4068 |
| 0604 | svc_numeric_shrunk | 829 | 0.3427 | 0.4336 | 0.9986 | 1.3789 |

## 3. validation 반복 holdout: shrunk vs raw 개선확률

- 전체: MdAPE 0.45 / MAPE 0.53 / p95 0.51
- scheme별: {"artist": {"MdAPE": 0.475, "MAPE": 0.625, "p95": 0.575}, "row": {"MdAPE": 0.425, "MAPE": 0.425, "p95": 0.45}}

## 4. 산출물

- `outputs/region_metrics.csv`, `outputs/repeated_holdout_summary.csv`, `artifacts/run_config.json`