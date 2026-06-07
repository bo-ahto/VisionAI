# PP-Y Cold 추가 closure 실험 실행 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y_closure_experiments.py`
- closure 결과 파일: `experiments/track6/PP-Y_closure_summary_metrics.csv`
- 통합 결과 파일: `experiments/track6/PP-Y_cold_combination_summary_metrics.csv`
- 실행 실험:
  - `PP-Y4` Cold LightGBM 피처 교환 + 목적함수 closure
  - `PP-Y5` Cold 피처 가용성/품질 기반 라우팅
  - `PP-Y9` Cold 목적함수 커스텀 closure
  - `PP-Y11` Cold validation meta stacking closure
  - `PP-Y12` Cold 전시/갤러리 사용 여부 라우팅
  - `PP-Y13` Cold 검색 품질 기반 fallback
  - `PP-Y14` Cold 예측 가격대별 모델 선택
  - `PP-Y15` Cold segment 최소 표본 수/cap 보정

## 1. 결론

- 추가 closure 실험에서도 개선 후보가 나왔다.
- 기존 `PP-Y10` 최고 MdAPE 후보 `0.4302`보다 더 낮은 `PP-Y15` 후보가 확인됐다.
- 최고 test MdAPE 후보는 `PP-Y15 y2_search_external_interaction_external_x_qwidth_min30_cap0.1`로 test MdAPE `0.4245`다.
- 최고 test p95 후보는 `PP-Y15 y2_search_external_interaction_pred_x_qwidth_min150_cap0.35`로 test p95_APE `2.8025`다.
- 단, `PP-Y15`는 segment/cap 후보를 많이 비교한 실험이므로 최종 채택 전에는 segment와 cap을 validation 또는 OOF 기준으로 고정한 재검증이 필요하다.

## 2. 기존 PP-Y 강한 후보 대비

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---:|---:|---:|---|
| `PP-Y2` 단일 모델 | 0.4421 | 1.0484 | 3.3537 | 단일 모델 강한 후보 |
| `PP-Y10` MdAPE 라우팅 | 0.4302 | 1.0551 | 3.1004 | 기존 라우팅 최고 후보 |
| `PP-Y10` p95 라우팅 | 0.4460 | 1.0489 | 2.9656 | 기존 p95 최고 후보 |
| `PP-Y15` MdAPE 보정 | 0.4245 | 1.0668 | 3.4110 | 대표 정확도 최고 후보, p95는 약함 |
| `PP-Y15` 균형 후보 | 0.4337 | 1.0467 | 2.9371 | MdAPE/MAPE/p95 균형 우수 |
| `PP-Y15` p95 보정 | 0.4464 | 1.0743 | 2.8025 | 큰 오차 방어 최고 후보 |

## 3. 실험별 판단

### PP-Y4

- best MdAPE: `lgbq_medium_size_meta_external_core` test MdAPE `0.4460`
- best p95: `lgb_mape_generated_meta_search_external` test p95 `3.6262`
- LightGBM 피처 교환과 목적함수 변경은 기존 `PP-Y2/Y10/Y15`보다 약했다.
- 판단: 보류. 새로운 최종 후보로는 부족하다.

### PP-Y5

- best MAPE: `route_y2_by_feature_quality_to_h9_search_p95_1.010` test MAPE `1.0338`
- best p95: `route_y2_by_feature_quality_to_w4_p95_0.650` test p95 `2.9656`
- 피처 품질 점수 기반 라우팅은 MAPE/p95 방어에는 도움이 됐다.
- 판단: 보조 정책 후보로 유지.

### PP-Y9

- best MAPE: `lgb_mape_support_size_search_external` test MAPE `1.0357`
- objective를 MAPE로 바꾸면 평균 오차는 줄어들지만 MdAPE/p95 균형은 `PP-Y15`보다 약하다.
- 판단: MAPE 목적 참고 후보로 유지하되 최종 후보는 아님.

### PP-Y11

- best MdAPE: `huber_validation_meta_component_range_clipped` test MdAPE `0.4560`
- validation meta stacking은 강한 후보들을 단순히 섞는 것만으로는 개선되지 않았다.
- 판단: 보류. 정식 OOF meta를 하더라도 입력 구조를 더 제한해야 한다.

### PP-Y12

- best MdAPE: `external_available_minexh1_else_h9_search_p95` test MdAPE `0.4344`
- 전시/갤러리 정보가 있는 경우 외부 피처 모델을 쓰고, 부족하면 검색 p95 후보로 넘기는 정책은 유효했다.
- 판단: 서비스 라우팅 후보로 유지.

### PP-Y13

- best p95: 검색 품질 fallback test p95 `2.9656`
- 검색 품질 점수 기준 fallback은 p95 방어에는 유효하지만 MdAPE 최고 후보는 아니다.
- 판단: 보조 fallback 후보.

### PP-Y14

- best MdAPE: `low_y10mdape_mid_y2_high_y10p95` test MdAPE `0.4344`
- best MAPE: `low_y10p95_mid_y10mdape_high_y2` test MAPE `1.0478`
- 예측 가격대별 모델 선택은 일정 부분 효과가 있었지만 `PP-Y15`보다 강하지는 않다.
- 판단: 서비스 정책 후보로 유지.

### PP-Y15

- best MdAPE: `external_x_qwidth_min30_cap0.1` test MdAPE `0.4245`
- best p95: `pred_x_qwidth_min150_cap0.35` test p95 `2.8025`
- best balance 후보: `pred_x_qwidth_min50_cap0.25` test MdAPE `0.4337`, MAPE `1.0467`, p95 `2.9371`
- segment 최소 표본 수와 cap을 조합한 보정이 Cold에서 가장 강한 추가 개선 신호를 냈다.
- 판단: 최우선 재검증 후보. segment/cap을 validation 또는 OOF에서 고정한 뒤 최종 test 확인 필요.

## 4. 정리

- 이제 Cold에서 남아 있던 주요 실험 축은 대부분 닫았다.
- 추가로 남은 것은 새로운 아이디어 탐색이 아니라, 이미 찾은 강한 후보의 검증 절차다.
- 최종 후보를 바로 고르기보다 아래 3개 목적 후보를 고정 검증하는 것이 맞다.

| 목적 | 후보 | 이유 |
|---|---|---|
| 대표 정확도 | `PP-Y15 external_x_qwidth_min30_cap0.1` | test MdAPE `0.4245` |
| 균형 후보 | `PP-Y15 pred_x_qwidth_min50_cap0.25` | MdAPE `0.4337`, MAPE `1.0467`, p95 `2.9371` |
| 큰 오차 방어 | `PP-Y15 pred_x_qwidth_min150_cap0.35` | p95 `2.8025` |

## 5. 보고용 한 줄 결론

- Cold는 추가 closure 실험을 통해 `PP-Y15` segment/cap 보정에서 test MdAPE `0.4245`, p95 `2.8025` 후보까지 확인됐다.
- 따라서 새로운 조합을 계속 늘리기보다는 `PP-Y15`의 segment와 cap을 OOF/validation 기준으로 고정해 최종 검증하는 단계로 넘어가는 것이 맞다.

## 6. OOF 고정 재검증 후 업데이트

- 업데이트일: 2026-06-03
- 재검증 실험: `PP-Y16`
- 실행 스크립트: `scripts/track6/run_pp_y15_oof_fixed_revalidation.py`
- 실행 결과 폴더: `experiments/track6/PP-Y16_cold_y15_oof_fixed_revalidation`
- 요약 문서: `docs/track6/experiments/pp_y15_oof_fixed_revalidation_summary.md`

| 선택 기준 | 후보 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| validation OOF MdAPE/MAPE/균형 선택 | `pred_x_qwidth_oof_min30_cap0.35` | 0.4438 | 1.1083 | 2.8025 | 대표 정확도 개선은 재현 약함, 큰 오차 방어는 강함 |
| validation OOF p95 선택 | `pred_x_qwidth_oof_min30_cap0.15` | 0.4382 | 1.0981 | 3.3512 | MdAPE는 소폭 개선, p95 방어는 약함 |

- 재검증 결과, `PP-Y15`의 test 최고 MdAPE `0.4245`는 validation OOF 기준으로 바로 채택하기 어렵다.
- `PP-Y16`에서 고정 선택된 후보는 `PP-Y2` 대비 p95를 `3.3537`에서 `2.8025`로 낮추는 효과가 뚜렷하다.
- 따라서 PP-Y15 계열 보정은 Cold 대표 가격 모델이 아니라, 큰 오차 방어용 위험 구간 보정 후보로 분리한다.
