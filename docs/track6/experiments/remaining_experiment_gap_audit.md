# Track6 남은 실험 Gap 감사

- 작성일: 2026-06-03
- 목적: 지금까지 실행한 후처리/모델 조합 실험을 되돌아보고, 해볼 만한데 아직 완전히 닫히지 않은 실험 축을 정리한다.
- 기준 파일:
  - `docs/track6/experiments/postprocessing_experiment_matrix.md`
  - `experiments/track6/*summary_metrics.csv`
  - `docs/track6/experiments/warm_cold_feature_model_selection_summary.md`
  - `docs/track6/experiments/pp_y_cold_combination_execution_summary.md`
  - `docs/track6/experiments/pp_y_cold_closure_execution_summary.md`
  - `docs/track6/experiments/pp_y15_oof_fixed_revalidation_summary.md`
  - `docs/track6/experiments/pp_l10_warm_l8_feature_variant_execution_summary.md`

## 1. 현재 실행 상태 요약

대부분의 큰 실험군은 실행 폴더와 요약 CSV가 존재한다.

| 구분 | 실행 상태 | 비고 |
|---|---|---|
| 기본 후보정 `PP-A~PP-I` | 실행 완료 | `PP-C2`는 중복 목적이라 보류, `PP-C4`는 조건부 미실행 |
| 모델별 커스텀 `PP-J` | 실행 완료 | Huber/CatBoost/LightGBM 보정 축 확인 |
| 보조 조합 `PP-K` | 실행 완료 | 추천 보조 조합 기준선 확인 |
| 순차 구조 `PP-L1~PP-L10` | 실행 완료 | 최근 `PP-L10`으로 Warm PP-L8 피처 변형까지 확인 |
| 신규 모델/분포/라우팅 `PP-M~PP-S` | 실행 완료 | Warm/Cold 추가 모델군 확인 |
| Warm 조합 `PP-T~PP-Z` | 실행 완료 | Cold형 피처의 Warm 적용까지 확인 |
| Cold 고도화 `PP-W~PP-Y16` | 실행 완료 | 다만 일부 후보는 OOF/다른 split 재검증 필요 |

단순히 실험 폴더가 없는 항목은 많지 않다. 현재 남은 것은 “완전 미실행”보다 “좋은 신호가 있었는데 최종 검증 또는 통합 단계가 남은 실험”이다.

## 2. 우선순위 높은 미완료 축

### 2.1 Warm `PP-L10` 후보를 최종 블렌딩에 다시 넣는 실험

- 현재 상태:
  - `PP-L10`에서 `PP-L8` 순차 구조를 피처셋별로 재실행했다.
  - best MdAPE: `l8_seq__warm_base_meta_external_search_all`, test MdAPE `0.1708`, MAPE `0.3363`, p95 `1.1432`.
  - best MAPE/p95 균형: `l8_seq__full_plus_generated_buckets`, test MdAPE `0.1743`, MAPE `0.3265`, p95 `0.9818`.
- 아직 안 한 것:
  - 이 두 신규 component를 `PP-V1/PP-V2`류 fine blend/meta stacking 입력 후보로 다시 넣어보지 않았다.
- 왜 해볼 만한가:
  - 기존 `PP-V1/PP-V2`는 `PP-L8`, `PP-L9`, `PP-U1` 후보를 component로 넣어 최종 성능을 만들었다.
  - `PP-L10`은 기존 `PP-L8`보다 피처 변형 후보가 생겼으므로, 단독으로는 최종 후보를 못 넘더라도 조합 안에서 가중치를 받을 가능성이 있다.
- 제안 실험:
  - `PP-V6` Warm refreshed fine blend with PP-L10 components.
  - `PP-V7` Warm refreshed meta stacking with PP-L10 components.
- 성공 기준:
  - `PP-V1` MdAPE `0.1621` 유지 또는 개선.
  - 또는 `PP-V2` MAPE `0.2873`, p95 `0.9287` 중 하나 개선하면서 MdAPE 악화 제한.
- 우선순위: 높음.

### 2.2 Cold `PP-Y10` 불확실성 폭 라우팅의 OOF/validation 고정 재검증

- 현재 상태:
  - `PP-Y10` test 기준 best MdAPE 후보가 `0.4302`까지 개선됐다.
  - p95 후보도 `2.9656`으로 좋았다.
- 아직 안 한 것:
  - `PP-Y10` threshold를 OOF 또는 validation 기준으로 고정하는 별도 정식 재검증은 아직 없다.
  - `PP-Y16`은 주로 `PP-Y15` segment/cap 보정을 OOF로 고정한 재검증이다.
- 왜 해볼 만한가:
  - Cold에서 서비스 적용 가능성이 높은 구조는 단일 모델보다 위험 구간 라우팅이다.
  - `PP-Y10`은 모델을 완전히 새로 만드는 것이 아니라, 예측 불확실성 폭으로 후보를 선택하는 정책이므로 운영 설명도 쉽다.
- 제안 실험:
  - `PP-Y17` Cold q-width routing OOF fixed validation.
  - 후보: `PP-Y2`, `PP-Y6`, `PP-H9`, `PP-W4`, `PP-Y10`의 대표/p95 후보.
  - q-width threshold는 validation 또는 validation 내부 OOF에서만 선택.
- 성공 기준:
  - `PP-Y2` MdAPE `0.4421`보다 개선 또는 유지.
  - p95는 `3.3537`보다 낮아야 함.
  - test threshold 직접 선택 금지.
- 우선순위: 높음.

### 2.3 Cold `PP-Y16`의 test 상위 후보 재현성 검증

- 현재 상태:
  - `PP-Y16` 결과 CSV에는 test MdAPE `0.4239~0.425` 수준의 후보가 존재한다.
  - 하지만 요약 문서에서 채택한 validation OOF 선택 후보는 MdAPE `0.4438`, p95 `2.8025`였다.
- 아직 안 한 것:
  - test 상위 PP-Y16 후보가 우연인지, 다른 split 또는 bootstrap에서 유지되는지 확인하지 않았다.
- 왜 해볼 만한가:
  - test 상위 후보가 재현되면 Cold 대표 정확도 개선 폭이 크다.
  - 반대로 재현되지 않으면 명확히 보류할 수 있어 보고 리스크가 줄어든다.
- 제안 실험:
  - `PP-Y18` Cold PP-Y16 top-candidate stability check.
  - 같은 설정을 random seed split 또는 time-like split에 적용.
  - 최소한 validation bootstrap/artist-group bootstrap으로 APE 차이 안정성 확인.
- 성공 기준:
  - `PP-Y2` 대비 MdAPE 개선 방향이 split/bootstrapping에서 유지.
  - p95 악화가 과하지 않아야 함.
- 우선순위: 높음.

## 3. 중간 우선순위 미완료 축

### 3.1 Cold 대표 후보 `PP-Y2`의 split 안정성 확인

- 현재 상태:
  - `PP-Y2 lgbq_search_all_external_interaction`은 단일 모델 기준 test MdAPE `0.4421`, MAPE `1.0484`, p95 `3.3537`.
  - 현재 Cold 대표 후보로 가장 설명이 단순하다.
- 아직 안 한 것:
  - 다른 split 또는 artist-group bootstrap에서 재현성 확인이 부족하다.
- 제안 실험:
  - `PP-Y19` Cold PP-Y2 stability / artist bootstrap.
- 우선순위: 중간~높음.

### 3.2 Cold `PP-W4` MAPE 후보와 `PP-Y2/Y16` 라우팅 결합

- 현재 상태:
  - `PP-W4 lightgbm_quantile_meta_all_huber_cap0.5_s1`은 Cold MAPE `0.9584`로 매우 낮지만 MdAPE `0.4949`가 약하다.
  - `PP-Y16`은 p95 방어가 강하지만 MAPE가 `1.1083`으로 악화된다.
- 아직 안 한 것:
  - MAPE가 강한 `PP-W4`를 전체 후보로 쓰지 않고, 특정 위험 구간에서만 fallback으로 쓰는 정책을 충분히 닫지 않았다.
- 제안 실험:
  - `PP-Y20` Cold MAPE/p95 purpose routing.
  - 안정 구간은 `PP-Y2`, 평균오차 위험 구간은 `PP-W4`, p95 위험 구간은 `PP-Y16` 사용.
- 우선순위: 중간.

### 3.3 Warm 최종 후보 배포 단순화 실험

- 현재 상태:
  - Warm 대표 후보 `PP-V1`, 방어 후보 `PP-V2`는 성능이 좋다.
  - 다만 meta/fine blend 구조가 서비스 배포에서 복잡할 수 있다.
- 아직 안 한 것:
  - 성능을 거의 유지하면서 component 수를 줄이는 distillation 또는 단순화 실험이 없다.
- 제안 실험:
  - `PP-V8` Warm deployment simplification.
  - teacher: `PP-V1/PP-V2`, student: Huber/Ridge/LightGBM 또는 제한된 feature set.
- 성공 기준:
  - MdAPE `0.1621~0.1680` 근처 유지.
  - 운영 피처/모델 수 감소.
- 우선순위: 중간.

## 4. 낮은 우선순위 또는 조건부 실험

### 4.1 `PP-C4` 저가/고가 분리 예측값 재보정

- 상태:
  - 계획표에는 있으나 별도 실행 폴더가 없다.
  - `PP-A2`, `PP-C1/C3/C5`, `PP-Y15/Y16`과 목적이 일부 겹친다.
- 판단:
  - 현재 우선순위는 낮다.
  - 가격대별 오차가 서비스 리포트에서 다시 문제로 확인될 때 실행한다.

### 4.2 `PP-A1-W`, `PP-A1-CB` 계획 문서와 실행 폴더명 불일치

- 상태:
  - 계획 문서는 `PP-A1-W`, `PP-A1-CB`처럼 세부 ID로 작성됐다.
  - 실행 폴더는 `PP-A1_global_residual_calibration`처럼 통합 ID로 존재한다.
- 판단:
  - 실험 자체가 빠진 것은 아니고 문서/폴더 명명 체계가 다르다.
  - 보고용으로는 mapping 표를 추가하면 충분하다.

### 4.3 검색 피처 재수집/품질 개선 실험

- 상태:
  - `PP-H7~H10` 파일럿은 실행됐다.
  - 검색 품질이 낮아 CatBoost 대표 예측에는 보류됐고, LightGBM Quantile/p95 보조 후보로만 의미가 있었다.
- 판단:
  - 추가 데이터 수집 정책이 확정되기 전에는 모델 실험보다 데이터 품질 개선이 먼저다.
  - 신규 검색 API/수집 품질 개선 이후 `PP-H9`, `PP-Y2`, `PP-Z1` 계열만 재검증한다.

## 5. 지금 바로 추가할 실험 리스트

아래 순서가 현실적이다.

| 우선순위 | 제안 ID | 실험 | 이유 | 예상 산출물 |
|---:|---|---|---|---|
| 1 | `PP-V6` | Warm PP-L10 component refreshed fine blend | Warm에서 가장 가능성 높은 미완료 통합 실험 | PP-V1/V2 대비 개선 여부 |
| 2 | `PP-V7` | Warm PP-L10 component refreshed meta stacking | PP-V2 구조에 신규 PP-L10 component 반영 | MAPE/p95 추가 개선 여부 |
| 3 | `PP-Y17` | Cold q-width routing OOF fixed validation | PP-Y10 라우팅이 test 선택 효과인지 확인 | OOF 기준 라우팅 후보 |
| 4 | `PP-Y18` | Cold PP-Y16 test-top candidate stability | test상 0.423~0.425 후보의 재현성 확인 | 채택/보류 근거 |
| 5 | `PP-Y19` | Cold PP-Y2 stability / artist bootstrap | 대표 단일 모델의 안정성 확인 | 서비스 후보 신뢰도 |
| 6 | `PP-Y20` | Cold MAPE/p95 purpose routing | PP-W4 MAPE 장점과 PP-Y16 p95 장점 결합 | 목적별 라우팅 후보 |
| 7 | `PP-V8` | Warm deployment simplification | 서비스 배포 복잡도 감소 | 성능 유지형 단순 모델 |

## 6. 결론

- 큰 실험군 자체는 대부분 실행됐다.
- 빠진 핵심은 새로운 모델을 무작정 추가하는 것이 아니라, 이미 확인된 강한 후보의 통합/고정/재현성 검증이다.
- 우선 Warm은 `PP-L10` 후보를 `PP-V` 조합에 다시 넣는 `PP-V6/V7`이 가장 자연스럽다.
- Cold는 `PP-Y10` 라우팅과 `PP-Y16` test 상위 후보의 OOF/다른 split 검증이 가장 중요하다.
- 이 단계를 거치면 “해볼 만한데 안 해본 실험”은 상당히 줄어들고, 남는 작업은 서비스 적용/데이터 수집 품질/배포 단순화 쪽으로 넘어갈 수 있다.

## 7. 실행 결과 업데이트

- 실행일: 2026-06-03
- Warm 실행 요약: `docs/track6/experiments/pp_v6_v8_warm_gap_execution_summary.md`
- Cold 실행 요약: `docs/track6/experiments/pp_y17_y20_cold_gap_revalidation_summary.md`

| 제안 ID | 실행 상태 | 핵심 결과 | 판단 |
|---|---|---|---|
| `PP-V6` | 실행 완료 | `fine_blend_mape_guarded` test MdAPE `0.1613`, MAPE `0.2889`, p95 `0.9314` | 기존 Warm 대표 `PP-V1`보다 개선, 대표 후보 교체 검토 |
| `PP-V7` | 실행 완료 | `huber_component_range_clipped` test MdAPE `0.1712`, MAPE `0.2803`, p95 `0.8990` | MdAPE는 악화, MAPE/p95 방어 후보 |
| `PP-V8` | 실행 완료 | `compact_blend_mape_guarded` test MdAPE `0.1632`, MAPE `0.2816`, p95 `0.9311` | 배포 단순화 후보로 유효 |
| `PP-Y17` | 실행 완료 | validation 고정 선택 test MdAPE `0.4620~0.4763` | `PP-Y10` test 상위 라우팅은 재현 부족, 대표 후보 보류 |
| `PP-Y18` | 실행 완료 | `qwidth_bin_oof_min30_cap0.25` test MdAPE `0.4247`, MAPE `0.9910`, p95 `3.3053` | Cold 유망 후보. bootstrap 개선 확률 높음, 추가 split 검증 필요 |
| `PP-Y19` | 실행 완료 | `PP-Y2` artist bootstrap MdAPE 95% 구간 `0.3751~0.5252` | Cold는 작가 구성에 따른 변동성이 큼 |
| `PP-Y20` | 실행 완료 | validation 선택 라우팅 test MdAPE `0.4494~0.4603`, p95 `3.6483~3.8973` | 3-way 라우팅 보류 |

업데이트 후 남은 판단:

- Warm은 `PP-V6`과 `PP-V8`을 중심으로 최종 후보를 갱신할 수 있다.
- Cold는 `PP-Y18 qwidth_bin cap0.25` 계열을 가장 유망한 추가 후보로 보되, test 상위 후보에서 출발했기 때문에 seed/split 재검증을 한 번 더 거친다.
- `PP-Y10` 라우팅과 `PP-Y20` 3-way 라우팅은 현재 기준으로 추가 확장 우선순위가 낮다.

## 8. 추가 실행 결과 업데이트

- 실행일: 2026-06-03
- 실행 요약: `docs/track6/experiments/remaining_experiment_execution_update_20260603.md`

| 제안 ID | 실행 상태 | 핵심 결과 | 판단 |
|---|---|---|---|
| `PP-Y21` | 실행 완료 | `qwidth_bin_oof_min30_cap0.25` artist holdout MdAPE 개선확률 `0.8625`, MAPE 개선확률 `0.9875`, p95 개선확률 `0.9625` | Cold 개선 후보로 유지 가능 |
| `PP-H22` | 실행 완료 | Naver x Python agreement high 없음, medium 9명, low 69명 | 검색 provider agreement는 점 예측 직접 피처보다 수동 검수/신뢰도 하향 기준으로 사용 |

최신 판단:

- Cold `PP-Y18 qwidth_bin_oof_min30_cap0.25`는 `PP-Y21` 반복 holdout에서 개선 방향이 유지되어, `PP-Y2` 기준선 옆에 개선 후보로 보고할 수 있다.
- `PP-Y21`은 모델을 새로 재학습한 split 검증이 아니라, 기존 예측값의 평가 구성 안정성 검증이다. 따라서 서비스 확정 전 최종 정책 비교에는 포함하되, 완전한 재학습 split 검증과 구분해 설명한다.
- `PP-H22` 결과상 Python 검색 provider는 커버리지는 넓지만 일반 웹 노이즈가 커서 Naver 공식 API와 source group 일치도가 낮았다. 검색 provider agreement는 가격을 직접 조정하는 피처보다 위험 구간 식별과 수동 검수 우선순위에 적합하다.
