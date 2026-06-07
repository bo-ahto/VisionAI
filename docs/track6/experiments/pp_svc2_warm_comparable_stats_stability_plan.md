# PP-SVC2 Warm 비교군 통계 피처 안정성 검증 계획

- 작성일: 2026-06-03
- 실험 ID: `PP-SVC2`
- 실험명: Warm 비교군 통계 피처 안정성 검증
- 선행 실험: `PP-SVC1`

## 1. 실험 배경

- `PP-SVC1`에서 Warm Huber에 비교군 통계 피처를 추가했을 때 test MdAPE가 `0.2274 -> 0.1496`으로 크게 개선됐다.
- 개선폭이 크기 때문에 바로 최종 후보로 채택하면 위험하다.
- 특히 train 피처는 자기 가격 누수를 막기 위해 5-fold OOF 방식으로 만들었고, fold 구성에 따라 학습 피처가 조금씩 달라진다.
- 따라서 다음 단계에서는 비교군 통계 피처가 fold seed 변화에도 안정적인지 확인한다.

## 2. 핵심 질문

- `PP-SVC1-W svc_full` 개선이 특정 OOF fold 구성에 의존한 결과인가?
- 비교군 통계 피처가 기존 Warm 최종 후보 `PP-V6`, 배포 단순화 후보 `PP-V8`보다 같은 test row에서 안정적으로 좋은가?
- 직접 비교군 중앙값이 아니라 Huber+비교군 통계 조합이 실제로 개선을 만든 것인가?

## 3. 실험 대상

| 후보 | 설명 |
|---|---|
| `baseline_huber` | Warm `Huber(base_existing_combo)` |
| `svc_numeric_seed_*` | Warm Huber + 숫자형 비교군 통계, OOF seed 반복 |
| `svc_full_seed_*` | Warm Huber + 숫자형/범주형 비교군 통계, OOF seed 반복 |
| `svc_numeric_seed_mean` | 여러 seed의 `svc_numeric` 예측 평균 |
| `svc_full_seed_mean` | 여러 seed의 `svc_full` 예측 평균 |
| `direct_group_median` | 비교군 중앙값을 그대로 예측값으로 사용 |
| `pp_v6_fine_blend_mape_guarded` | 현재 Warm 대표 후보 |
| `pp_v8_compact_blend_mape_guarded` | Warm 배포 단순화 후보 |

## 4. 반복 검증 방식

- validation/test 비교군 통계는 항상 train 전체 기준으로 계산한다.
- train 비교군 통계만 OOF fold seed를 바꿔 반복 생성한다.
- 각 seed마다 동일한 Warm Huber 설정으로 재학습한다.
- 기본 seed 후보는 10개로 둔다.

```text
seed = 202606030, 202606031, ..., 202606039
```

## 5. 비교 기준

| 기준 | 내용 |
|---|---|
| seed 안정성 | seed별 `svc_full` test MdAPE/MAPE/p95의 평균, 표준편차, 최소/최대 확인 |
| 기존 후보 비교 | `PP-V6`, `PP-V8`과 같은 test row에서 MdAPE/MAPE/p95 비교 |
| bootstrap 비교 | row bootstrap과 artist bootstrap으로 개선확률 산출 |
| coverage slice | `svc_group_level`, `svc_coverage_tier`별 성능 확인 |

## 6. 성공 기준

- `svc_full` seed 반복 test MdAPE 평균이 `PP-V6`보다 낮고 표준편차가 작으면 최종 후보 재검증 대상으로 유지한다.
- row bootstrap과 artist bootstrap에서 `PP-V6` 대비 MdAPE 개선 확률이 높으면 대표 후보 편입을 검토한다.
- 단, `svc_coverage_tier=low_n`에서만 개선이 집중되거나 특정 작가 bootstrap에서 흔들리면 추가 split 검증 후 채택한다.

## 7. 결과물

- `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/metrics.csv`
- `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/seed_stability.csv`
- `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/bootstrap_summary.csv`
- `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/slice_metrics.csv`
- `experiments/track6/PP-SVC2_warm_comparable_stats_stability/reports/result_report.md`
- `experiments/track6/PP-SVC2_warm_comparable_stats_stability/reports/result_report.html`
- `docs/track6/experiments/pp_svc2_warm_comparable_stats_stability_summary.md`
