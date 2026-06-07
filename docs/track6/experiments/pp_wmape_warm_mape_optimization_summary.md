# PP-WMAPE Warm MAPE 최적화 조합 실험 요약

- 실행일: 2026-06-03
- 실험 ID: `PP-WMAPE`
- 목적: Warm 모델에서 `MAPE`를 줄이는 것을 최우선 목표로 두고, 기존 Warm 후보 예측값의 조합/라우팅/구간 보정/잔차 보정 중 실제 개선 가능한 방식을 찾는다.
- 실행 스크립트: `scripts/track6/run_pp_wmape_warm_mape_optimization.py`
- HTML 리포트: `experiments/track6/PP-WMAPE_warm_mape_optimization/reports/result_report.html`

## 1. 실험 구성

| 구분 | 실험 내용 | 목적 |
|---|---|---|
| W-MAPE-01 | 기존 Warm 후보 예측값 통합 | `PP-V8`, `PP-H29`, `PP-R5`, `PP-L10`, `PP-D4` 후보를 같은 row 기준으로 비교 |
| W-MAPE-02 | 전역 가중 앙상블 | validation MAPE가 낮은 후보들을 log 예측값 기준으로 가중 평균 |
| W-MAPE-03 | MAPE+p95 방어 앙상블 | MAPE를 낮추되 MdAPE/p95 악화를 막는 가중 조합 탐색 |
| W-MAPE-04 | 구간별 모델 라우팅 | quantile width, routing width, 면적, 작가 학습량 구간별로 다른 후보 선택 |
| W-MAPE-05 | 예측 가격 구간 보정 | 예측 가격대별로 MAPE 최소 보정값 계산 |
| W-MAPE-06 | 작품 크기 구간 보정 | 작품 면적 구간별 반복 상대오차 보정 |
| W-MAPE-07 | 작가 학습량 구간 보정 | Warm 안에서도 학습량 차이에 따른 오차 보정 |
| W-MAPE-08 | 검색 피처 구간 보정 | 검색 품질, 뉴스/갤러리/소셜 비중별 MAPE 보정 |
| W-MAPE-09 | CatBoost 잔차 보정 | 기존 후보가 남긴 잔차를 CatBoost로 2차 보정 |
| W-MAPE-10 | Ridge/Huber 잔차 보정 | 선형 보정 모델로 잔차를 보정 |
| W-MAPE-11 | Quantile width 기반 처리 | 예측 불확실성 폭에 따라 보정 강도를 다르게 적용 |
| W-MAPE-12 | Bootstrap 안정성 검증 | row/artist 재표본추출로 MAPE 개선 안정성 확인 |

공통 원칙:

- 보정값과 조합 선택은 Warm validation에서만 계산한다.
- Warm test는 최종 평가에만 사용한다.
- MAPE를 최우선으로 보되 MdAPE와 p95_APE가 크게 악화되는 후보는 보류한다.

## 2. 기존 기준 후보

| 후보 | test MAPE | test MdAPE | test p95_APE | 해석 |
|---|---:|---:|---:|---|
| `h29__h29_v8_compact_mape_gallery_median_cap0p05` | 0.2809 | 0.1617 | 0.9309 | 기존 H29 최상위 Warm MAPE 후보 |
| `v8__compact_blend_mape_guarded` | 0.2816 | 0.1632 | 0.9311 | PP-V8 MAPE 방어 기준 |
| `v8__compact_blend_mdape` | 0.2868 | 0.1635 | 0.9190 | p95가 상대적으로 안정적인 후보 |
| `v8__deployment_single_mdape` | 0.3044 | 0.1621 | 1.0335 | MdAPE 단일 기준 후보 |

## 3. 최종 상위 결과

| 순위 | 후보 | 방식 | test MAPE | test MdAPE | test p95_APE | 해석 |
|---:|---|---|---:|---:|---:|---|
| 1 | `wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_quantile_width` | H29 후보 + quantile width 구간별 MAPE 보정 | 0.2674 | 0.1638 | 0.8322 | 최우선 후보 |
| 2 | `wmape_segment_v8_compact_blend_mape_guarded_quantile_width` | V8 MAPE 후보 + quantile width 구간별 MAPE 보정 | 0.2675 | 0.1626 | 0.8332 | 거의 동일한 대안 |
| 3 | `wmape_segment_v8_compact_blend_mdape_quantile_width` | V8 MdAPE 후보 + quantile width 구간별 MAPE 보정 | 0.2708 | 0.1610 | 0.8150 | p95 방어가 더 강한 대안 |
| 4 | `wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_artist_works_log` | H29 후보 + 작가 학습량 구간 보정 | 0.2716 | 0.1629 | 0.8565 | 작가 학습량 기반 보조 후보 |
| 5 | `wmape_segment_h29_h29_v8_compact_mape_gallery_median_cap0p05_search_quality_score` | H29 후보 + 검색 품질 구간 보정 | 0.2730 | 0.1670 | 0.8227 | 검색 피처 기반 보조 후보 |

개선 폭:

| 비교 기준 | 기준 MAPE | 최상위 MAPE | 개선폭 |
|---|---:|---:|---:|
| 기존 H29 Warm 최상위 | 0.2809 | 0.2674 | 0.0135 |
| 기존 V8 MAPE 기준 | 0.2816 | 0.2674 | 0.0143 |

## 4. 최상위 후보 보정 방식

최상위 후보는 `quantile_width`를 기준으로 validation을 3개 구간으로 나눈 뒤, 각 구간에서 MAPE가 가장 낮아지는 log 보정값을 적용했다.

| quantile width 구간 | validation row 수 | log 보정값 | 해석 |
|---|---:|---:|---|
| 낮은 구간 | 173 | -0.034 | 예측값을 약간 낮춤 |
| 중간 구간 | 173 | -0.052 | 예측값을 조금 더 낮춤 |
| 높은 구간 | 173 | -0.120 | 불확실성이 큰 구간은 과대 예측 위험이 커서 강하게 낮춤 |

해석:

- `quantile_width`는 예측 불확실성 폭이다.
- 폭이 넓다는 것은 해당 작품의 적정 가격 범위가 넓고 모델이 확신하기 어렵다는 뜻이다.
- Warm에서도 불확실성이 큰 구간은 상대오차가 커지기 쉬웠고, 이 구간의 예측값을 보수적으로 낮추는 것이 MAPE와 p95를 동시에 낮췄다.

## 5. Bootstrap 안정성

| 후보 | row 개선 확률 | artist 개선 확률 | 평균 MAPE 개선폭 | 판단 |
|---|---:|---:|---:|---|
| 최상위 `H29 + quantile_width 보정` | 1.0000 | 0.9988 | 0.0135 | 안정적 |
| `V8 MAPE + quantile_width 보정` | 1.0000 | 0.9975 | 0.0135 | 안정적 |
| `H29 + gallery ratio 보정` | 1.0000 | 0.9963 | 0.0081 | 보조 후보 |
| `H29 + search quality 보정` | 1.0000 | 0.9888 | 0.0079 | 보조 후보 |

## 6. 보류된 방식

| 방식 | 결과 | 판단 |
|---|---|---|
| 전역 가중 앙상블 | test MAPE 약 0.2820 | 기존 기준보다 개선되지 않아 보류 |
| CatBoost 잔차 보정 | validation MAPE는 크게 개선, test MAPE는 약 0.2820~0.2826 | validation 과적합 신호가 있어 보류 |
| Ridge/Huber 잔차 보정 | test MAPE 약 0.2829~0.2835 | 기준 대비 개선 없음 |
| 단순 라우팅 | 일부 MdAPE는 좋으나 MAPE 개선폭이 제한적 | 단독 채택 보류 |

## 7. 결론

- Warm에서 MAPE를 줄이는 데 가장 효과적인 방식은 새 모델을 추가 학습하는 것보다, 기존 강한 Warm 후보 위에 `quantile_width` 기반 구간별 MAPE 보정을 적용하는 방식이었다.
- 최상위 후보는 기존 H29 Warm 최상위 대비 MAPE를 `0.2809 -> 0.2674`로 낮췄고, p95_APE도 `0.9309 -> 0.8322`로 개선했다.
- MdAPE는 `0.1617 -> 0.1638`로 아주 소폭 악화됐지만, MAPE/p95 개선 폭이 더 크므로 “MAPE 최적화 후보”로는 채택 가능하다.
- MdAPE까지 더 보수적으로 보고 싶으면 `V8 compact_blend_mdape + quantile_width 보정` 후보를 대안으로 검토한다.

## 8. 산출물

| 산출물 | 경로 |
|---|---|
| HTML 리포트 | `experiments/track6/PP-WMAPE_warm_mape_optimization/reports/result_report.html` |
| metrics | `experiments/track6/PP-WMAPE_warm_mape_optimization/outputs/metrics.csv` |
| predictions | `experiments/track6/PP-WMAPE_warm_mape_optimization/outputs/candidate_predictions.csv` |
| 구간 보정값 | `experiments/track6/PP-WMAPE_warm_mape_optimization/outputs/segment_corrections.csv` |
| bootstrap 검증 | `experiments/track6/PP-WMAPE_warm_mape_optimization/outputs/bootstrap_summary.csv` |
| 실행 스크립트 | `scripts/track6/run_pp_wmape_warm_mape_optimization.py` |
