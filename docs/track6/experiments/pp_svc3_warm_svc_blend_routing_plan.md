# PP-SVC3 Warm 비교군 통계 후보 결합/라우팅 계획

- 작성일: 2026-06-03
- 실험 ID: `PP-SVC3`
- 실험명: Warm 비교군 통계 후보와 기존 Warm 후보 결합/라우팅
- 선행 실험: `PP-SVC1`, `PP-SVC2`

## 1. 실험 배경

- `PP-SVC2`에서 Warm 비교군 통계 피처 후보는 MdAPE 기준으로 기존 `PP-V6/PP-V8`보다 좋았다.
- 반대로 MAPE 기준은 `PP-V6/PP-V8`이 비교군 통계 후보보다 좋았다.
- 따라서 단일 후보 하나를 고르는 것보다 목적별 장점을 섞거나 조건별로 후보를 선택하는 방식이 필요하다.

## 2. 핵심 질문

- 비교군 통계 후보의 MdAPE 장점과 `PP-V6/PP-V8`의 MAPE 장점을 함께 가져올 수 있는가?
- 비교군이 충분한 구간은 `svc` 후보를 쓰고, 불안정한 구간은 기존 `PP-V6/PP-V8`을 쓰는 방식이 더 안정적인가?
- validation에서 정한 가중치/라우팅 기준이 test에서도 유지되는가?

## 3. 입력 후보

| 후보 | 역할 |
|---|---|
| `svc_numeric_seed_mean` | 비교군 숫자 통계 기반 Warm Huber seed 평균 |
| `svc_full_seed_mean` | 비교군 숫자+범주 통계 기반 Warm Huber seed 평균 |
| `pp_v6_fine_blend_mape_guarded` | 기존 Warm 대표 후보 |
| `pp_v8_compact_blend_mape_guarded` | 기존 Warm 배포 단순화/MAPE 방어 후보 |

## 4. 생성 후보

| 후보군 | 생성 방식 | 목적 |
|---|---|---|
| 단순 가중 평균 | `w * svc + (1-w) * pp_v6/v8`, `w=0.00~1.00` | MdAPE와 MAPE의 균형점 탐색 |
| 비교군 level 라우팅 | `svc_group_level`별 validation 최적 후보 선택 | 작가/작가+크기/작가+재료 구간별 후보 분리 |
| coverage tier 라우팅 | `svc_coverage_tier`별 validation 최적 후보 선택 | 표본 수 안정성에 따라 후보 선택 |
| disagreement 라우팅 | `abs(svc - pp_v8)` 구간별 validation 최적 후보 선택 | 두 후보가 크게 다를 때만 다른 후보 사용 |

## 5. 선택 기준

| 목적 | 선택 방식 |
|---|---|
| `mdape_primary` | validation MdAPE가 가장 낮은 후보 |
| `mape_guarded` | validation MdAPE가 기준 후보보다 나쁘지 않은 후보 중 MAPE가 가장 낮은 후보 |
| `p95_guarded` | validation MdAPE가 기준 후보보다 나쁘지 않은 후보 중 p95_APE가 가장 낮은 후보 |
| `balanced` | validation MdAPE, MAPE, p95_APE를 기준 후보 대비 정규화해 합산한 점수가 가장 낮은 후보 |

## 6. 성공 기준

- test에서 `PP-V6` 대비 MdAPE를 유지 또는 개선하면서 MAPE 악화를 줄이면 후보로 유지한다.
- `PP-V8` 대비 MAPE가 크게 나쁘지 않으면서 MdAPE가 개선되면 운영 후보로 검토한다.
- validation에서 선택된 후보와 test 상위 후보가 크게 다르면 최종 채택은 보류하고 추가 split 검증으로 넘긴다.

## 7. 결과물

- `experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/all_candidate_metrics.csv`
- `experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/selected_candidate_metrics.csv`
- `experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/predictions.csv`
- `experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/bootstrap_summary.csv`
- `experiments/track6/PP-SVC3_warm_svc_blend_routing/reports/result_report.md`
- `experiments/track6/PP-SVC3_warm_svc_blend_routing/reports/result_report.html`
- `docs/track6/experiments/pp_svc3_warm_svc_blend_routing_summary.md`
