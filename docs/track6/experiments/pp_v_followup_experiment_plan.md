# PP-V 후속 정확도 개선 실험 계획

- 작성일: 2026-06-02
- 목적: 종합 보고서의 다음 실행 제안 중 바로 실행 가능한 후보를 실험으로 검증한다.
- 기준 보고서: `docs/track6/experiments/price_prediction_accuracy_experiment_result_report.md`
- 실행 스크립트: `scripts/track6/run_pp_v_experiments.py`

## 실험 배경

종합 보고서에서 남은 핵심 질문은 다음이다.

- Warm에서 PP-U1의 생성 bucket 확장 후보를 기존 PP-T 조합에 넣으면 `PP-T1`보다 더 좋아지는가?
- Cold에서 PP-U3/PP-U4의 피처 교환 후보를 기존 PP-S/PP-Q/PP-R 조합에 넣으면 MdAPE, MAPE, p95가 더 좋아지는가?
- Cold validation에서 0.3대 MdAPE까지 내려간 후보가 test에서 재현되지 않았는데, cross-fitted meta 구조로 재현성을 높일 수 있는가?
- 최종 후보를 MdAPE, MAPE, p95 목적별로 다시 정리하면 어떤 후보가 남는가?

## 상세 실험 리스트

| 실험 ID | 실험명 | 대상 | 사용 후보 | 목적 | 성공 기준 |
|---|---|---|---|---|---|
| `PP-V1` | Warm PP-U 피처 후보 추가 fine blend | Warm | 기존 PP-T 후보 + `PP-U1 full_plus_generated_buckets`, `PP-U1 artist_size_works` | Warm 생성 bucket/작가 학습량 후보가 기존 fine blend에 추가 이득을 주는지 확인 | `PP-T1 fine_blend_mape_guarded` 대비 test MdAPE/MAPE/p95 중 하나 이상 개선 |
| `PP-V2` | Warm PP-U 피처 후보 추가 meta stacking | Warm | 기존 PP-T 후보 + PP-U1 후보 | 후보 예측값 간 차이를 Ridge/Huber meta가 안정적으로 활용하는지 확인 | PP-T2 대비 MAPE 또는 p95 개선, MdAPE 악화 제한 |
| `PP-V3` | Cold PP-U 피처 후보 추가 fine blend | Cold | 기존 Cold 상위 후보 + `PP-U3 medium_size_combo`, `PP-U3 support_shape_combo`, `PP-U4 lightgbm_swap_support_size` | 피처 교환 후보가 기존 Cold 조합에 추가 설명력을 주는지 확인 | PP-S1/PP-Q2/PP-R4 대비 목적별 지표 개선 |
| `PP-V4` | Cold PP-U 피처 후보 추가 cross-fitted meta stacking | Cold | 기존 Cold 상위 후보 + PP-U 피처 후보 | validation 0.3대 후보의 test 재현성 문제를 meta 구조로 완화할 수 있는지 확인 | PP-S4 대비 p95 또는 MAPE 개선, MdAPE 유지 |
| `PP-V5` | Warm/Cold 목적별 정책 재정리 | Warm/Cold | PP-T, PP-S, PP-Q, PP-R, PP-V 후보 | 추가 후보를 포함해 MdAPE/MAPE/p95 목적별 선택 후보를 갱신 | 목적별 최종 후보와 보류 사유가 명확해짐 |

## 해석 기준

- validation에서 선택한 조합이 test에서 개선되지 않으면 기준 후보로 채택하지 않는다.
- test에서만 좋아진 후보는 후속 후보로 보류하고 즉시 교체하지 않는다.
- Warm은 기존 PP-T 후보가 이미 강하므로 작은 개선이라도 validation/test 방향이 맞는지 본다.
- Cold는 단일 지표 1위보다 MdAPE, MAPE, p95 목적별 후보를 분리해서 본다.

