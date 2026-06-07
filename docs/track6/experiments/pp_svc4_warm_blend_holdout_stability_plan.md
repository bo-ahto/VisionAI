# PP-SVC4 Warm 결합 후보 holdout 안정성 검증 계획

- 작성일: 2026-06-03
- 실험 ID: `PP-SVC4`
- 실험명: Warm 결합 후보 holdout 안정성 검증
- 선행 실험: `PP-SVC3`

## 1. 실험 배경

- `PP-SVC3`에서 `blend_svcnum_ppv8_wsvc_0.70` 후보가 Warm test 기준 MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`로 가장 유망했다.
- 이 후보는 validation에서 선택한 가중치다.
- 따라서 최종 서비스 후보로 올리기 전, validation 구성 변화에도 비슷한 결합 후보가 선택되는지 확인해야 한다.

## 2. 핵심 질문

- validation을 내부 선택셋/holdout셋으로 다시 나눠도 `svc_numeric + PP-V8` 계열 결합이 계속 선택되는가?
- 선택 가중치가 `0.70` 근처에서 안정적으로 반복되는가?
- 내부 holdout과 test에서 기존 `PP-V6/PP-V8` 대비 개선이 유지되는가?

## 3. 검증 방식

- 기존 `PP-SVC2` 예측값을 사용한다.
- 새 모델을 학습하지 않고, 예측값 결합 정책만 반복 검증한다.
- validation을 반복 분할한다.
  - row holdout: 개별 row 기준으로 selection/holdout 분할
  - artist holdout: 작가 단위로 selection/holdout 분할
- 각 반복에서 selection subset만 보고 후보를 선택한다.
- 선택된 후보를 같은 반복의 internal holdout과 고정 test에 적용해 성능을 기록한다.

## 4. 후보군

| 후보군 | 설명 |
|---|---|
| base | `svc_numeric_seed_mean`, `svc_full_seed_mean`, `PP-V6`, `PP-V8` |
| weighted blend | `w * svc + (1-w) * PP`, `w=0.00~1.00`, 0.05 간격 |

## 5. 선택 목적

| 목적 | 선택 기준 |
|---|---|
| `mdape_primary` | selection subset에서 MdAPE가 가장 낮은 후보 |
| `mape_guarded` | selection subset에서 PP-V6보다 MdAPE가 나쁘지 않은 후보 중 MAPE가 가장 낮은 후보 |
| `balanced` | PP-V6 대비 MdAPE/MAPE/p95를 정규화해 합산한 점수가 가장 낮은 후보 |

## 6. 성공 기준

- `mape_guarded` 또는 `balanced`에서 `blend_svcnum_ppv8` 계열이 반복적으로 선택되면 `PP-SVC3` 결합식의 선택 안정성이 높다고 본다.
- 선택 가중치가 `0.60~0.80` 범위에 집중되면 `wsvc=0.70`이 과도하게 특이한 값이 아니라고 본다.
- holdout/test에서 PP-V6 대비 MdAPE와 MAPE 개선확률이 높으면 최종 후보 유지가 가능하다.

## 7. 결과물

- `experiments/track6/PP-SVC4_warm_blend_holdout_stability/outputs/iteration_results.csv`
- `experiments/track6/PP-SVC4_warm_blend_holdout_stability/outputs/selection_frequency.csv`
- `experiments/track6/PP-SVC4_warm_blend_holdout_stability/outputs/summary_metrics.csv`
- `experiments/track6/PP-SVC4_warm_blend_holdout_stability/reports/result_report.md`
- `experiments/track6/PP-SVC4_warm_blend_holdout_stability/reports/result_report.html`
- `docs/track6/experiments/pp_svc4_warm_blend_holdout_stability_summary.md`
