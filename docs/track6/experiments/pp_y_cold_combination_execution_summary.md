# PP-Y Cold 피처/모델 조합 확장 실행 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y_cold_combination_experiments.py`
- 통합 결과 파일: `experiments/track6/PP-Y_cold_combination_summary_metrics.csv`
- 실행 실험:
  - `PP-Y1` LightGBM Quantile + 전시/갤러리 + 작가 메타
  - `PP-Y2` LightGBM Quantile + 검색 + 전시/갤러리
  - `PP-Y3` CatBoost Quantile + 갤러리 단독/검색 품질
  - `PP-Y6` LightGBM Quantile 선행 + CatBoost residual
  - `PP-Y7` CatBoost Quantile 선행 + LightGBM residual
  - `PP-Y8` CatBoost Quantile + Huber residual + 품질 cap
  - `PP-Y10` 불확실성 폭 기반 모델 라우팅

## 1. 결론

- Cold 추가 개선 신호가 확인됐다.
- 기존 Cold 대표 정확도 후보였던 `PP-X3 lightgbm_quantile_exhibition_gallery`의 test MdAPE `0.4451`보다 더 낮은 후보가 나왔다.
- 가장 좋은 test MdAPE 후보는 `PP-Y10 route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.454`로 test MdAPE `0.4302`다.
- 단일 모델 기준으로는 `PP-Y2 lgbq_search_all_external_interaction`이 test MdAPE `0.4421`, MAPE `1.0484`, p95 `3.3537`로 가장 균형이 좋다.
- p95 기준으로는 `PP-Y10 route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.861`이 test p95 `2.9656`으로 가장 좋고, MdAPE도 `0.4460`으로 유지된다.
- 다만 `PP-Y10`은 여러 threshold를 비교한 라우팅 실험이므로 최종 후보로 확정하기 전 validation 선택 기준 또는 OOF 기반 재검증이 필요하다.

## 2. 기존 강한 후보 대비 결과

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | 해석 |
|---|---:|---:|---:|---|
| 기존 `PP-X3` 전시/갤러리 MdAPE 후보 | 0.4451 | 1.1277 | 3.8935 | 기존 Cold 대표 정확도 기준 |
| 기존 `PP-W2` CatBoost 작가 메타 | 0.4497 | 1.1111 | 4.1587 | 기존 CatBoost 대표 후보 |
| 기존 `PP-H9` 검색 p95 후보 | 0.4773 | 1.0308 | 2.9954 | 검색 기반 큰 오차 방어 후보 |
| 기존 `PP-W4` LightGBM Quantile 기준 | 0.4766 | 1.0847 | 3.0322 | 안정적 범위 후보 |
| `PP-Y2` 검색+전시/갤러리 단일 모델 | 0.4421 | 1.0484 | 3.3537 | 단일 모델 기준 추가 개선 |
| `PP-Y6` LightGBM Quantile -> CatBoost residual | 0.4327 | 1.0514 | 3.8486 | MdAPE는 크게 개선, p95는 약함 |
| `PP-Y10` 전시/갤러리 -> 검색 p95 라우팅 | 0.4302 | 1.0551 | 3.1004 | 대표 정확도 최고 후보 |
| `PP-Y10` 검색+전시/갤러리 -> W4 p95 라우팅 | 0.4460 | 1.0489 | 2.9656 | p95 최고 후보 |

## 3. 실험별 판단

### PP-Y1

- best test MdAPE: `lgbq_meta_external_core` `0.4444`
- 전시/갤러리 피처를 q10/q50/q90 구조로 다시 학습했을 때 기존 `PP-X3` 수준의 개선이 재현됐다.
- 상호작용 후보는 MdAPE는 약간 낮지만 MAPE/p95 균형이 더 낫다.
- 판단: 유지. `PP-Y10` 라우팅 입력 후보로 유효하다.

### PP-Y2

- best test MdAPE/MAPE: `lgbq_search_all_external_interaction` `0.4421 / 1.0484 / 3.3537`
- 검색 피처와 전시/갤러리 피처를 같이 넣었을 때 단일 모델 기준으로 기존 `PP-X3`보다 좋아졌다.
- 검색 피처가 MAPE와 p95를 일부 방어하고, 전시/갤러리가 MdAPE를 낮춘 것으로 해석된다.
- 판단: 강한 단일 모델 후보. 후속 OOF meta stacking 입력으로 유지.

### PP-Y3

- best test MdAPE: `catq_meta_baseline` `0.4671`
- CatBoost Quantile은 RMSE CatBoost보다 MAPE/p95는 좋아졌지만, LightGBM Quantile 계열보다 약하다.
- 갤러리 추가와 검색 품질 추가는 CatBoost Quantile에서 대표 정확도 개선으로 이어지지 않았다.
- 판단: 보류. CatBoost는 1차 모델보다 residual 또는 보조 조합 역할이 더 적합하다.

### PP-Y6

- best test MdAPE: `lgbq_search_external_interaction_catboost_oof_cap0.15_s1` `0.4327`
- LightGBM Quantile이 만든 중앙 예측 뒤에 CatBoost residual을 붙이는 순서는 MdAPE 개선에 효과가 있었다.
- 다만 p95는 `3.8486`으로 약해, 단독 서비스 후보보다는 대표 정확도 후보 또는 라우팅 입력 후보가 적합하다.
- 판단: 유지. p95 방어 후보와 결합 필요.

### PP-Y7

- best test MdAPE: `base_catq_gallery_search_quality` `0.4834`
- validation에서는 좋아 보였지만 test에서 개선이 재현되지 않았다.
- CatBoost Quantile 선행 뒤 LightGBM residual은 현재 피처 구성에서는 불안정하다.
- 판단: 보류.

### PP-Y8

- best test MdAPE: `base_catq_gallery_search_quality` `0.4834`
- 품질 cap을 붙인 Huber residual도 test에서는 개선되지 않았다.
- 품질 cap 아이디어는 유지할 수 있으나, 현재 CatBoost Quantile 기반 구조에는 효과가 약하다.
- 판단: 보류.

### PP-Y10

- best MdAPE 후보: `route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.454`
  - test MdAPE `0.4302`
  - test MAPE `1.0551`
  - test p95 `3.1004`
- best p95 후보: `route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.861`
  - test MdAPE `0.4460`
  - test MAPE `1.0489`
  - test p95 `2.9656`
- 불확실성 폭이 작은 구간에서는 전시/갤러리/검색 모델을 쓰고, 폭이 큰 구간에서는 검색 또는 W4 p95 후보로 넘기는 방식이 효과적이었다.
- 판단: 가장 유망한 정책 후보. 단, threshold 선택은 OOF/validation 기준으로 다시 고정해야 한다.

## 4. 후속 작업

- 이 문서는 `PP-Y1/Y2/Y3/Y6/Y7/Y8/Y10` 1차 실행 요약이다.
- 이후 `PP-Y4/Y5/Y9/Y11/Y12~Y15` closure 실험을 추가 실행했다.
- 최신 판단은 `docs/track6/experiments/pp_y_cold_closure_execution_summary.md`를 기준으로 본다.
- closure 실행 전 1차 판단은 아래와 같았다.
  - `PP-Y10`의 threshold를 test가 아니라 validation/OOF 기준으로 고정하는 재검증을 진행한다.
  - `PP-Y2`와 `PP-Y6`을 `PP-Y11` OOF meta stacking 입력 후보로 사용한다.
  - CatBoost Quantile 선행 구조인 `PP-Y7/Y8`은 현재 보류한다.
  - 서비스 후보는 단일 모델과 라우팅 후보를 분리한다.
  - 단일 모델 후보: `PP-Y2 lgbq_search_all_external_interaction`
  - 대표 정확도 라우팅 후보: `PP-Y10 route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.454`
  - 큰 오차 방어 라우팅 후보: `PP-Y10 route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.861`

## 5. 보고용 한 줄 결론

- Cold는 전시/갤러리, 검색 피처, LightGBM Quantile, CatBoost residual을 조합했을 때 추가 개선 가능성이 확인됐다.
- 특히 불확실성 폭 기반 라우팅은 test MdAPE를 `0.4302`까지 낮췄고, p95 목적 후보도 `2.9656`까지 낮아져 후속 검증 가치가 높다.
