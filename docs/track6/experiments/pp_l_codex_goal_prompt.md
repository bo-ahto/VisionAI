# Codex /goal Prompt: PP-L 실험 실행

아래 내용을 Codex `/goal`에 그대로 입력한다.

```text
Track6 가격 예측 프로젝트에서 Group PP-L 실험군을 실제로 실행할 수 있게 진행해줘.

목표는 Huber, Quantile, CatBoost를 조합해 MdAPE를 유지하거나 개선하는 범위 안에서 MAPE와 p95_APE를 낮출 수 있는지 검증하는 것이다.

반드시 아래 문서를 먼저 읽고 실험 의도와 실행 기준을 파악한 뒤 진행해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/huber_quantile_catboost_mape_optimization_plan.md
- docs/track6/experiments/supervisor_postprocessing_required_experiments.md
- docs/track6/experiments/pp_l_execution_goal_prompt.md

실행 대상은 아래 PP-L 실험군이다.

- PP-L1 CatBoost MAPE 목적 최적화
- PP-L2 CatBoost 옵션별 MAPE 민감도
- PP-L3 Huber 선행 + CatBoost residual 보정
- PP-L4 Huber + Quantile width 위험 구간 보정
- PP-L5 Huber + Quantile + CatBoost 라우팅
- PP-L6 Huber / Quantile / CatBoost 가중 앙상블
- PP-L7-0 Quantile 구간 생성 및 검증
- PP-L7-H Quantile 구간별 Huber 상세 학습
- PP-L7-CB Quantile 구간별 CatBoost 상세 학습
- PP-L7-HCB Quantile 구간별 Huber + CatBoost 결합
- PP-L8 Quantile-Huber-CatBoost 순차 학습
- PP-L9 Huber-Quantile-CatBoost residual 순차 학습

실험은 기존 Track6 실험 방식처럼 실험 ID별 독립 폴더로 관리해줘.

기본 폴더는 experiments/track6/ 아래에 만들고, 권장 폴더명은 아래 기준을 사용해줘.

- experiments/track6/PP-L1_catboost_mape_objective/
- experiments/track6/PP-L2_catboost_mape_sensitivity/
- experiments/track6/PP-L3_huber_catboost_residual/
- experiments/track6/PP-L4_huber_quantile_width_risk_calibration/
- experiments/track6/PP-L5_huber_quantile_catboost_routing/
- experiments/track6/PP-L6_huber_quantile_catboost_weighted_ensemble/
- experiments/track6/PP-L7_0_quantile_segment_validation/
- experiments/track6/PP-L7_H_quantile_segment_huber_refit/
- experiments/track6/PP-L7_CB_quantile_segment_catboost_refit/
- experiments/track6/PP-L7_HCB_quantile_segment_huber_catboost_combo/
- experiments/track6/PP-L8_quantile_huber_catboost_sequential/
- experiments/track6/PP-L9_huber_quantile_catboost_residual_sequential/

각 실험 폴더에는 최소한 아래 구조를 남겨줘.

- README.md
- experiment_config.json
- data/split_manifest.json
- data/feature_columns.json
- outputs/metrics.csv
- outputs/slice_metrics.csv
- outputs/predictions.csv
- outputs/oof_predictions.csv
- outputs/residuals.csv
- outputs/segment_definition.csv
- outputs/statistical_tests.csv
- outputs/complexity_report.csv
- reports/result_report.md
- reports/result_report.html
- artifacts/model_manifest.json
- artifacts/calibration_map.json
- artifacts/routing_policy.json
- logs/run_log.txt

실험 전 반드시 기존 코드와 데이터 구조를 먼저 파악해줘. 기존 Track6 실험 스크립트, metrics 계산 방식, split 파일, final artifact, baseline 모델 저장 위치를 확인한 뒤 재사용 가능한 코드를 우선 사용해줘. 새 스크립트를 만들더라도 기존 실험 패턴과 산출물 형식을 맞춰줘.

절대 지켜야 할 원칙:

1. train / validation / test 역할을 분리한다.
2. validation에서만 구간 경계, 보정값, 가중치, 라우팅 기준을 정한다.
3. test는 최종 후보 1회 확인에만 사용한다.
4. residual 모델 학습에는 반드시 OOF 예측 기반 residual을 사용한다.
5. PP-L8의 price_range_ratio와 PP-L9의 residual_range_ratio를 혼동하지 않는다.
6. 개선된 후보뿐 아니라 실패/보류 후보도 기록한다.
7. MdAPE가 악화되면 MAPE가 좋아져도 바로 채택하지 않는다.
8. 기존 사용자 변경사항이나 unrelated worktree 변경사항은 되돌리지 않는다.

실험 판단 기준:

- Primary metric: MdAPE
- Secondary metrics: MAPE, p95_APE, RMSE_log, Within_30, Within_50
- Slice metrics: Warm/Cold, 저가/중가/고가, stable/caution/risk, low/mid/high uncertainty

Quantile 구간 정의:

- Quantile 모델은 q10_log, q50_log, q90_log를 출력한다.
- quantile_width = q90_log - q10_log
- price_range_ratio = exp(quantile_width)
- 초기 탐색은 validation quantile_width 33% / 66% 기준으로 low/mid/high를 나눈다.
- 추가 민감도 기준으로 50%/80%, 70%/90%, price_range_ratio 1.5배/2.5배를 비교한다.
- 구간 기준은 validation에서만 확정하고 test에는 그대로 적용한다.

PP-L8과 PP-L9의 차이를 명확히 유지해줘.

PP-L8:
- 구조: Quantile → Huber → CatBoost
- Quantile은 가격 예측 범위의 불확실성을 먼저 진단한다.
- ratio는 price_range_ratio다.

PP-L9:
- 구조: Huber → Quantile residual → CatBoost remaining residual
- Quantile은 가격 자체가 아니라 Huber residual 범위를 추정한다.
- ratio는 residual_range_ratio다.

필수 baseline:

- B0 Warm Huber 단독
- B1 Cold CatBoost 단독
- B2 Quantile q50 단독
- B3 기준 모델 + 전체 median residual 보정
- B4 Huber + CatBoost residual
- B5 Huber + Quantile residual q50
- B6 PP-L8 Quantile → Huber → CatBoost
- B7 PP-L9 Huber → Quantile residual → CatBoost
- B8 Huber / Quantile / CatBoost 단순 가중 앙상블

통계 검증도 포함해줘.

- paired bootstrap 95% CI
- Wilcoxon signed-rank test
- seed 반복 평균/표준편차
- 구간별 bootstrap

최종 후보 채택 기준:

- MdAPE 유지 또는 개선
- MAPE 개선
- p95_APE 악화 없음
- stable 구간 악화 없음
- validation/test 방향 일치
- baseline 대비 통계적으로 안정적인 개선
- 복잡도 대비 개선폭이 충분함

보류 기준:

- MAPE만 개선되고 MdAPE 악화
- p95_APE 악화
- stable 구간 악화
- test 재현 실패
- 단순 baseline 대비 개선 불명확
- 복잡도 대비 개선폭 부족

진행 방식:

1. 먼저 관련 문서와 기존 Track6 코드/데이터 구조를 조사한다.
2. 실행 가능한 계획을 세우고 필요한 스크립트 또는 기존 스크립트 재사용 지점을 정리한다.
3. PP-L 실험을 폴더별로 실행한다.
4. 각 실험별 산출물을 지정 폴더에 저장한다.
5. 전체 결과를 비교해 최종 채택/보류/중단 판단을 작성한다.
6. reports/result_report.html과 종합 summary를 만들어 상사가 볼 수 있게 정리한다.

최종 응답에서는 아래를 보고해줘.

- 실행한 실험 목록
- 생성한 실험 폴더
- 핵심 metric 결과
- 채택/보류/중단 판단
- 통계 검증 결과 요약
- 실패하거나 실행하지 못한 실험과 이유
- 다음에 이어서 해야 할 작업
```
