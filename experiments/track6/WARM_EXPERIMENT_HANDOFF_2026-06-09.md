# Warm 가격 예측 실험 핸드오프

작성일: 2026-06-09

## 현재 목표

기존 Warm 가격 예측 모델의 운영 성능을 개선한다.

주요 판단 기준은 아래와 같다.

- 기본 데이터셋 기준으로 비교한다. 제출용 고신뢰 100건 실험은 제외한다.
- 기존 Warm validation OOF 519건 + fixed test 607건을 사용한다.
- fixed test 성능만 보지 않고 repeated validation 안정성을 같이 본다.
- 핵심 지표는 MAPE, p95 APE, repeated MAPE win rate, replacement score다.

## 2026-06-13 최신 업데이트: PP-WMIN8B / PP-WMIN9B / PP-WMIN10 official v0.1 WMIN8 API parity 완료

WMIN4에서 선택된 Warm 운영 1순위 후보 `min1_huber_refit_partial`을 먼저 0604 stress로 확인한 뒤, EB shrinkage, 70:30 결합 비율 재탐색, 조건부 라우팅을 순서대로 검증했다.

현재 Warm 5건 이상 운영 1순위는 WMIN8 조건부 라우팅 후보 `min1_route_w850_risk_q50_altlower_gap005`다. PP-WMIN8B에서는 이 후보 위에 잔차 구간 보정을 추가로 검증했지만 p95 안정성 trade-off가 남아 보류했다. PP-WMIN9에서는 WMIN8 후보를 아티팩트로 패키징하고 official v0.1 exact adapter 연결 상태를 확인했다. PP-WMIN9B에서는 1~4건 Warm-lite / 5건 이상 WMIN8 라우팅 경계가 현재 검증 결과와 일치하는지 확인했다. PP-WMIN10에서는 official v0.1 HTTP API endpoint로 fixed test 607건을 재생해 WMIN8 실험 산출물과 endpoint 출력이 row-level로 일치함을 확인했다.

위치:

```text
scripts/track6/run_pp_wmin5_warm_min1_0604_stress.py
experiments/track6/PP-WMIN5_warm_min1_0604_stress/
docs/track6/experiments/pp_wmin5_warm_min1_0604_stress_summary.md

scripts/track6/run_pp_wmin6_warm_min1_eb_shrinkage_decision.py
experiments/track6/PP-WMIN6_warm_min1_eb_shrinkage_decision/
docs/track6/experiments/pp_wmin6_warm_min1_eb_shrinkage_decision_summary.md

scripts/track6/run_pp_wmin7_warm_min1_weight_retuning.py
experiments/track6/PP-WMIN7_warm_min1_weight_retuning/
docs/track6/experiments/pp_wmin7_warm_min1_weight_retuning_summary.md

scripts/track6/run_pp_wmin8_warm_min1_weight_router.py
experiments/track6/PP-WMIN8_warm_min1_weight_router/
docs/track6/experiments/pp_wmin8_warm_min1_weight_router_summary.md

scripts/track6/run_pp_wmin8b_warm_min1_residual_rediagnosis.py
experiments/track6/PP-WMIN8B_warm_min1_residual_rediagnosis/
docs/track6/experiments/pp_wmin8b_warm_min1_residual_rediagnosis_summary.md

scripts/track6/run_pp_wmin9_warm_route_integration.py
experiments/track6/PP-WMIN9_warm_route_integration/
docs/track6/experiments/pp_wmin9_warm_route_integration_summary.md
models/track6/warm_wmin8_operational_candidate/

scripts/track6/run_pp_wmin9b_warm_lite_boundary_comparison.py
experiments/track6/PP-WMIN9B_warm_lite_boundary_comparison/
docs/track6/experiments/pp_wmin9b_warm_lite_boundary_comparison_summary.md

scripts/track6/verify_official_v0_1_warm_lite_api_routing.py
docs/track6/experiments/price_prediction_official_v0_1_warm_lite_api_route_validation.md

scripts/track6/audit_official_v0_1_wmin8_exact_adapter_gap.py
scripts/track6/build_wmin8_exact_runtime_candidate_artifact.py
models/track6/warm_wmin8_exact_runtime_candidate/
docs/track6/experiments/price_prediction_official_v0_1_wmin8_exact_adapter_gap_audit.md
docs/track6/experiments/price_prediction_official_v0_1_wmin8_exact_runtime_candidate.md

scripts/track6/run_pp_wmin10_warm_wmin8_api_fixed_test_parity.py
experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity/
docs/track6/experiments/pp_wmin10_warm_wmin8_api_fixed_test_parity_summary.md
```

PP-WMIN5 stress 판단:

| 비교 | n | MdAPE | MAPE | p95 APE | 해석 |
|---|---:|---:|---:|---:|---|
| WMIN4 선택 후보 | 829 | 0.2147 | 0.3197 | 0.9026 | 0604 stress 적용 |
| PP258 report-layer proxy | 829 | 0.2779 | 0.3774 | 0.9871 | exact upstream raw adapter 부재로 proxy 기준 |
| WMIN4 - PP258 proxy | - | -0.0632 | -0.0577 | -0.0845 | stress gate 통과 |

PP-WMIN6 EB shrinkage 판단:

| 후보 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | WMIN4 대비 판단 |
|---|---:|---:|---|
| WMIN4 선택 후보 `min1_huber_refit_partial` | 0.1016 / 0.1784 / 0.5713 | 0.1066 / 0.2393 / 0.7792 | 계속 1순위 |
| EB Huber refit k5 | 0.1007 / 0.1785 / 0.5696 | 0.1051 / 0.2392 / 0.7850 | MdAPE/MAPE는 근접하나 fixed test p95 `+0.0058` 악화 |
| EB 70:30 k2 | 0.1067 / 0.1804 / 0.5871 | 0.1104 / 0.2393 / 0.7827 | p95가 WMIN4보다 높음 |

PP-WMIN7 결합 비율 재탐색 판단:

| 후보 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | WMIN4 대비 판단 |
|---|---:|---:|---|
| WMIN4 선택 후보 `min1_huber_refit_partial` | 0.1016 / 0.1784 / 0.5713 | 0.1066 / 0.2393 / 0.7792 | 이전 1순위 |
| WMIN7 선택 후보 `min1_w800_huber_refit_partial` | 0.0953 / 0.1774 / 0.5762 | 0.1052 / 0.2406 / 0.7614 | p95는 개선되지만 fixed test MAPE `+0.0013` 악화 |
| WMIN7 p95 강한 후보 `min1_w750_huber_refit_partial` | 0.0982 / 0.1777 / 0.5783 | 0.1050 / 0.2400 / 0.7479 | p95는 크게 개선되지만 fixed test MAPE `+0.0007` 악화 |

PP-WMIN8 조건부 라우팅 판단:

| 후보 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | WMIN4 대비 판단 |
|---|---:|---:|---|
| WMIN4 선택 후보 `min1_huber_refit_partial` | 0.1016 / 0.1784 / 0.5713 | 0.1066 / 0.2393 / 0.7792 | 라우팅 전 기준 |
| WMIN8 선택 후보 `min1_route_w850_risk_q50_altlower_gap005` | 0.0940 / 0.1751 / 0.5713 | 0.1043 / 0.2358 / 0.7394 | MdAPE `-0.0023`, MAPE `-0.0035`, p95 `-0.0398` |

PP-WMIN8B 잔차 재진단 판단:

| 후보 | validation MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 | WMIN8 대비 판단 |
|---|---:|---:|---|
| WMIN8 선택 후보 `min1_route_w850_risk_q50_altlower_gap005` | 0.0940 / 0.1751 / 0.5713 | 0.1043 / 0.2358 / 0.7394 | 현재 1순위 |
| 최상위 잔차 보정 후보 `min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p5` | 0.0963 / 0.1749 / 0.5743 | 0.1045 / 0.2360 / 0.7427 | validation MAPE는 소폭 개선되지만 fixed test 전 지표 악화 |

PP-WMIN9 운영 통합 판단:

| 항목 | 상태 | 해석 |
|---|---|---|
| WMIN8 후보 아티팩트 | 완료 | `models/track6/warm_wmin8_operational_candidate/manifest.json` 생성 |
| Warm-lite 아티팩트 | 준비됨 | `models/track6/warm_lite_v0.1/` 존재 |
| official v0.1 Warm 5건 이상 경로 | 존재 | match score 0.80 이상, history 5건 이상에서 Warm |
| official v0.1 Warm-lite 1~4건 경로 | 완료 | match score 0.80 이상, history 1~4건에서 Warm-lite |
| official v0.1 WMIN8 호출 | 완료 | 5건 이상 Warm 경로에서 WMIN8 runtime adapter 적용 |
| WMIN8 Huber pipeline replay | 완료 | WMIN7 예측 CSV 대비 최대 로그 차이 `3.55e-15` |
| WMIN8 API fixed-test parity | 통과 | 607/607 성공, wrong route `0`, wrong adapter `0`, 최대 로그 차이 `5.33e-15`, 가격 차이 `0원` |
| boundary API repeat | 완료 | 0/1/4/5건 경계 케이스 3회 반복 deterministic 검증 통과 |

PP-WMIN9B Warm-lite 경계 판단:

| 경로 | 검증 데이터 | MdAPE/MAPE/p95 | 판단 |
|---|---|---:|---|
| Warm-lite 1~4건 | 실존 저이력 leave-one-out 1,947행 | 0.1092 / 0.2866 / 0.8765 | Cold `0.5429/0.9946/2.5358` 대비 압도 개선, bootstrap gate 1.0/1.0/1.0 |
| Warm WMIN8 5건 이상 | fixed test 607행 | 0.1043 / 0.2358 / 0.7394 | WMIN4와 PP258 대비 개선된 5건 이상 1순위 |
| WMIN8 저이력 동일행 직접 비교 | 채택 근거로 사용하지 않음 | - | WMIN8은 5건 이상 동일 작가 이력 경로로 선택된 모델이므로 1~4건 행에 강제 적용하면 운영 라우팅 조건을 벗어남 |

official v0.1 서비스 연결 상태:

| 항목 | 상태 | 검증 |
|---|---|---|
| `warm_lite` route schema | 완료 | `Route`에 `warm_lite`, `DisplayRoute`에 `저이력 기반 예측` 추가 |
| 라우팅 경계 | 완료 | match score `0.80` 이상 기준: 0건 Cold, 1~4건 Warm-lite, 5건 이상 Warm |
| Warm-lite raw adapter | 완료 | `models/track6/warm_lite_v0.1/predict/predict_warm_lite_v0_1.py` 호출 |
| Boundary smoke test | 통과 | unknown→Cold, n=1→Warm-lite, n=4→Warm-lite, n=5→Warm |
| Deterministic repeat | 통과 | 같은 n=4 입력 3회 반복 결과 `(warm_lite, 1,383,465원, 899,252~2,144,371원)` 동일 |
| Warm WMIN8 exact raw adapter | 완료 | WMIN8 base/alternative Huber runtime + risk gate 연결 |
| Warm WMIN8 endpoint parity | 통과 | fixed test 607건 API 재생 결과 실험 CSV와 최대 로그 차이 `5.33e-15` |

판단:

- PP-WMIN5: WMIN4 선택 후보는 0604 stress에서 PP258 proxy 대비 명확한 악화가 없어 후속 실험 진행 가능.
- PP-WMIN6: EB shrinkage는 단독 SVC MdAPE를 낮추지만 MAPE/p95가 악화되고, 70:30 및 Huber refit 이후에도 WMIN4 선택 후보를 안정적으로 넘지 못했다.
- PP-WMIN7: SVC 비중을 0.80~0.85로 높이면 p95 방어가 좋아지지만 단독 교체 시 MAPE trade-off가 남는다.
- PP-WMIN8: validation-only 조건부 라우팅으로 WMIN4 기본 후보와 WMIN7 고 SVC 후보를 섞으면 fixed test에서도 MdAPE/MAPE/p95가 동시에 개선된다.
- Warm 5건 이상 운영 1순위는 `min1_route_w850_risk_q50_altlower_gap005`로 갱신한다.
- PP-WMIN8B: WMIN8 위에 구간별 잔차 중앙값 보정을 추가하면 validation MAPE는 작게 좋아지지만 fixed test에서 WMIN8보다 MdAPE/MAPE/p95가 모두 악화되어 운영 교체하지 않는다.
- PP-WMIN9: WMIN8 후보 아티팩트는 준비됐고 official v0.1 모델 상태에서 선택 후보로 노출된다.
- PP-WMIN9B: history 0건=Cold, 1~4건=Warm-lite, 5건 이상=WMIN8 조건부 라우팅 경계는 현재 검증 결과와 일치한다.
- official v0.1: Warm-lite 1~4건 라우팅과 저장 모델 adapter 호출은 연결 완료. WMIN8 5건 이상 경로도 WMIN8 runtime adapter로 연결 완료.
- WMIN8 runtime: base 70% SVC Huber 후보와 85% SVC 방어 후보 pipeline replay는 WMIN7 CSV와 사실상 동일하며, official API endpoint fixed-test parity도 607건 전부 통과했다.
- EB shrinkage와 WMIN7 단독 후보는 현재 운영 교체 후보가 아니라 보류 후보로 둔다.

다음 작업:

1. `scripts/track6/verify_official_v0_1_warm_lite_api_routing.py --repeat 3`을 Warm routing 회귀 테스트로 유지한다.
2. `scripts/track6/run_pp_wmin10_warm_wmin8_api_fixed_test_parity.py --no-resume`을 WMIN8 endpoint parity 회귀 테스트로 유지한다.
3. Cold 쪽도 동일한 방식으로 exact endpoint parity 가능 범위를 점검한다.
4. 운영 신규 입력에서는 fixed-test feature store가 없을 수 있으므로, raw-input fallback 경로의 예측값/설명 품질은 별도 live-input audit으로 관리한다.

## 2026-06-12 이전 업데이트: PP-WMIN4 완료

Warm SVC 본체의 작가 포함 비교군 ladder 최소 표본 기준을 `5건`에서 `1건`으로 낮춘 뒤, 새 기준가 위에서 Huber 잔차 보정 계층을 다시 결합하고, 기존 PP258 운영 후보와 같은 validation/test 기준으로 운영 교체 판단까지 완료했다.

위치:

```text
scripts/track6/run_pp_wmin2_warm_artist_min1_svc_numeric.py
experiments/track6/PP-WMIN2_warm_artist_min1_svc_numeric/
docs/track6/experiments/pp_wmin2_warm_artist_min1_svc_numeric_summary.md

scripts/track6/run_pp_wmin3_warm_min1_hcoef_refit.py
experiments/track6/PP-WMIN3_warm_min1_hcoef_refit/
docs/track6/experiments/pp_wmin3_warm_min1_hcoef_refit_summary.md

scripts/track6/run_pp_wmin4_warm_min1_operational_decision.py
experiments/track6/PP-WMIN4_warm_min1_operational_decision/
docs/track6/experiments/pp_wmin4_warm_min1_operational_decision_summary.md
```

변경 범위:

- PP-WMIN2: `artist_key`가 포함된 비교군 단계만 `min_n=1`로 변경
- PP-WMIN2 유지: Warm 기본 피처, Huber 학습 방식, SVC numeric 피처, PP-V8 참조 후보, 70:30 결합식
- PP-WMIN2 누수 방어: train 피처는 seed별 5-fold cross-fit으로 생성, source/holdout row id 중복 합계 `0`
- PP-WMIN2 fallback 규칙: fold 제외 후 해당 작가 비교군 source가 0건이면 다음 ladder 단계로 이동
- PP-WMIN3: min1 SVC로 `70:30` 기준가를 재계산하고, 기존 Huber 잔차 보정 계층을 새 기준가에 맞춰 재적합
- PP-WMIN4: 기존 PP258 운영 후보를 기준으로 두고 WMIN3 후보군의 validation 반복 안정성과 replacement score를 비교

핵심 결과:

| 비교 | validation artist OOF MdAPE/MAPE/p95 | validation row OOF MdAPE/MAPE/p95 | fixed test MdAPE/MAPE/p95 |
|---|---:|---:|---:|
| 기존 70:30 min5 | 0.1305 / 0.2110 / 0.6580 | 0.1305 / 0.2110 / 0.6580 | 0.1405 / 0.2748 / 0.8331 |
| 기존 hcoef 안정 후보 | 0.1260 / 0.2082 / 0.6479 | 0.1260 / 0.2082 / 0.6479 | 0.1388 / 0.2730 / 0.8064 |
| min1 SVC 단독 | 0.0948 / 0.1856 / 0.6060 | 0.0948 / 0.1856 / 0.6060 | 0.1116 / 0.2537 / 0.8032 |
| min1 70:30 기준가 | 0.1075 / 0.1806 / 0.5819 | 0.1075 / 0.1806 / 0.5819 | 0.1083 / 0.2397 / 0.7826 |
| min1 Huber 재적합 partial | 0.1026 / 0.1795 / 0.5733 | 0.1021 / 0.1794 / 0.5727 | 0.1066 / 0.2393 / 0.7792 |

PP-WMIN4 운영 교체 판단:

| 후보 | validation MdAPE/MAPE/p95 | validation MAPE/p95 win rate | validation replacement score | fixed test MdAPE/MAPE/p95 |
|---|---:|---:|---:|---:|
| 기존 PP258 운영 후보 | 0.1227 / 0.2056 / 0.6379 | 기준값 | 0.0000 | 0.1410 / 0.2699 / 0.8073 |
| min1 Huber 재적합 partial | 0.1016 / 0.1784 / 0.5713 | 0.9968 / 0.9808 | -0.0272 | 0.1066 / 0.2393 / 0.7792 |

판단:

- PP-WMIN1 proxy 개선 신호가 운영형 `svc_numeric_seed_mean`, 기존 70:30 기준가, Huber 잔차 보정 stack, PP258 기준 운영 비교까지 유지됐다.
- fixed test에서도 같은 방향으로 개선됐지만, fixed test는 채택 기준이 아니라 최종 확인용으로만 둔다.
- `min1 Huber 재적합 partial`은 validation gate를 통과했고 fixed test 확인에서도 기존 PP258 운영 후보보다 MdAPE/MAPE/p95가 모두 낮다.
- 운영 교체 후보로 채택 가능하다. 다만 실제 서비스 반영 전 artifact/adapter 갱신과 재현 패키지 검증이 필요하다.

다음 작업:

1. `min1_huber_refit_partial`을 Warm 운영 1순위 후보로 동결한다.
2. artifact/adapter 갱신안을 작성한다.
3. 운영 재현 패키지를 만든 뒤 같은 입력에서 같은 출력이 나오는지 결정성 테스트를 수행한다.
4. 다음 실험은 p95가 더 낮은 `min1_huber_delta_transplant`와 MAPE가 낮은 `min1_huber_refit_partial`을 validation-only 조건부 라우팅으로 결합할 수 있는지 검증한다.

## 2026-06-12 이전 업데이트: PP-WMIN2 완료

Warm SVC 본체에서 작가 포함 비교군 ladder의 최소 표본 기준을 `5건`에서 `1건`으로 낮추는 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_wmin2_warm_artist_min1_svc_numeric.py
experiments/track6/PP-WMIN2_warm_artist_min1_svc_numeric/
docs/track6/experiments/pp_wmin2_warm_artist_min1_svc_numeric_summary.md
```

변경 범위:

- 변경: `artist_key`가 포함된 비교군 단계만 `min_n=1`로 변경
- 유지: Warm 기본 피처, Huber 학습 방식, SVC numeric 피처, PP-V8 참조 후보, 70:30 결합식
- 누수 방어: train 피처는 seed별 5-fold cross-fit으로 생성, source/holdout row id 중복 합계 `0`
- fallback 규칙: fold 제외 후 해당 작가 비교군 source가 0건이면 다음 ladder 단계로 이동

핵심 결과:

| 비교 | validation 기존 | validation min1 | fixed test 기존 | fixed test min1 |
|---|---:|---:|---:|---:|
| SVC 단독 MdAPE/MAPE/p95 | 0.1272 / 0.2176 / 0.6504 | 0.0948 / 0.1856 / 0.6060 | 0.1520 / 0.2942 / 0.9381 | 0.1116 / 0.2537 / 0.8032 |
| 70:30 MdAPE/MAPE/p95 | 0.1305 / 0.2110 / 0.6580 | 0.1075 / 0.1806 / 0.5819 | 0.1405 / 0.2748 / 0.8331 | 0.1083 / 0.2397 / 0.7826 |

validation bootstrap:

| 비교 | row MdAPE/MAPE/p95 개선확률 | artist MdAPE/MAPE/p95 개선확률 |
|---|---:|---:|
| SVC 단독 min5 → min1 | 1.000 / 0.996 / 0.864 | 1.000 / 1.000 / 0.864 |
| 70:30 min5 → min1 | 0.996 / 1.000 / 0.966 | 0.998 / 1.000 / 0.968 |

판단:

- PP-WMIN1 proxy 개선 신호가 운영형 `svc_numeric_seed_mean`과 기존 70:30 기준가까지 유지됐다.
- fixed test에서도 같은 방향으로 개선됐지만, fixed test는 채택 기준이 아니라 최종 확인용으로만 둔다.
- 아직 운영 교체 확정은 아니다. 기존 hcoef/잔차 보정 stack과 decision layer까지 다시 결합해야 한다.

다음 작업:

1. PP-WMIN3: min1 SVC basis로 기존 70:30과 hcoef/잔차 보정 stack을 재계산한다.
2. PP-WMIN3 selection은 validation OOF 기준으로만 판단한다.
3. PP-WMIN4: PP148/166/PP258 계열 decision layer를 min1 basis 위에서 재학습하고 repeated win rate와 replacement score를 확인한다.
4. 두 단계 모두 통과하면 svc replacement와 artifact update를 제안한다.

## 2026-06-10 업데이트: PP-OPT161~166 완료

`PP-OPT161~166 Warm PP157 negative gate rollback` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt161_166_warm_pp157_negative_gate_rollback.py
experiments/track6/PP-OPT161_166_warm_pp157_negative_gate_rollback/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP126 운영 기준 | 0.270114 | 0.807490 | 0.919231 | 0.494231 | -0.017219 |
| PP148 운영 후보 | 0.270140 | 0.807231 | 0.925962 | 0.531090 | -0.017463 |
| PP166 운영 후보 | 0.269997 | 0.807231 | 0.946795 | 0.601923 | -0.018439 |

선택된 운영 후보:

```text
ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006
```

해석:

- PP166은 PP148 대비 MAPE를 `-0.000143` 낮추고 p95는 동일하게 유지한다.
- PP126 대비 MAPE는 `-0.000117`, p95는 `-0.000259` 개선된다.
- repeated validation 기준의 MAPE win rate가 PP148 `0.925962`에서 PP166 `0.946795`로 상승했다.
- 따라서 현재 운영 1순위는 PP148에서 PP166으로 갱신한다.
- p95 전용 후보는 여전히 `reference_pp148_p95`가 가장 적합하다.

다음 실험 방향:

1. PP166의 segment outcome rollback 구조를 기본 운영 후보로 고정한다.
2. PP162/PP164 계열에서 p95가 더 낮았던 후보를 PP166 위에 아주 약하게 얹는 tail-only 개선을 검증한다.
3. PP166이 PP148보다 나빠지는 row만 다시 분석해 second-stage rollback 또는 calibration gate를 시도한다.

## 2026-06-10 업데이트: PP-OPT167~172 완료

`PP-OPT167~172 Warm PP166 second-stage tail calibration` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt167_172_warm_pp166_second_stage_tail_calibration.py
experiments/track6/PP-OPT167_172_warm_pp166_second_stage_tail_calibration/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP166 운영 후보 | 0.269997 | 0.807231 | 0.946795 | 0.601923 | -0.018439 |
| PP172 운영 후보 | 0.269997 | 0.807231 | 0.947115 | 0.605449 | -0.018451 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

선택된 PP172 운영 후보:

```text
ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004
```

해석:

- PP172는 PP166 대비 fixed test MAPE가 `+0.00000043`로 사실상 동일하고 p95도 동일하다.
- 반복 MAPE win rate는 `0.946795`에서 `0.947115`로, 반복 p95 win rate는 `0.601923`에서 `0.605449`로 소폭 개선됐다.
- replacement score도 `-0.018439`에서 `-0.018451`로 미세하게 개선됐다.
- 개선폭이 극히 작기 때문에 PP172를 단독 확정 모델로 과장하면 안 된다.
- 운영 후보 표기는 `PP172 잠정 1순위 / PP166 실질 동급 fallback`으로 둔다.

다음 실험 방향:

1. PP166/PP172가 거의 포화된 상태이므로 같은 방식의 작은 보정은 수익이 작다.
2. 다음은 row별 미세 cap보다 `새 기준가 후보` 또는 `모델 구조 변화`가 더 의미 있다.
3. 그래도 보정 축을 이어간다면, PP172가 선택한 `PP162 p95 gate + price_conf segment router`를 고정하고 아주 작은 threshold 주변만 검증한다.

## 2026-06-10 업데이트: PP-OPT173~180 완료

`PP-OPT173~180 Warm basis-generation challenger` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt173_180_warm_basis_generation_challenger.py
experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP172 운영 후보 | 0.269997 | 0.807231 | 0.947115 | 0.605449 | -0.018451 |
| PP180 운영 후보 | 0.269933 | 0.807326 | 0.952244 | 0.754487 | -0.018721 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

선택된 PP180 운영 후보:

```text
ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004
```

해석:

- PP180은 PP172 대비 MAPE를 `-0.000065` 개선한다.
- p95는 PP172보다 `+0.000095` 나빠지지만, PP126보다는 여전히 `-0.000165` 좋다.
- repeated MAPE win rate는 `0.947115`에서 `0.952244`로 개선된다.
- repeated p95 win rate도 `0.605449`에서 `0.754487`로 개선된다.
- 따라서 MAPE/overall replacement 기준 운영 후보는 PP180이 우세하다.
- p95를 PP172 수준으로 절대 유지해야 한다면 PP172를 fallback으로 둔다.
- 이번 결과는 “미세 보정”보다 `stack_huber_weighted` 기준가 후보를 제한적으로 쓰는 방식이 더 큰 개선 여지가 있음을 보여준다.

다음 실험 방향:

1. PP180의 `stack_huber_weighted` 기준가 라우팅을 고정하고 p95 악화를 줄이는 narrow 실험을 진행한다.
2. p95가 커진 후보는 제외하고, `p95 <= PP172 + 0.00003` 수준의 더 엄격한 guard를 둔다.
3. `stack_huber_weighted` 외에 `direct_cat_plain`, `direct_xgb_weighted`는 p95 유지형 후보로 다시 좁게 볼 만하다.

## 2026-06-10 업데이트: PP-OPT181~186 완료

`PP-OPT181~186 Warm Huber basis p95-guard refinement` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt181_186_warm_huber_basis_p95_guard_refinement.py
experiments/track6/PP-OPT181_186_warm_huber_basis_p95_guard_refinement/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP172 운영 후보 | 0.269997 | 0.807231 | 0.947115 | 0.605449 | -0.018451 |
| PP180 운영 후보 | 0.269933 | 0.807326 | 0.952244 | 0.754487 | -0.018721 |
| PP186 p95-guard 운영 후보 | 0.269961 | 0.807231 | 0.949359 | 0.598718 | -0.018578 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

선택된 PP186 후보:

```text
ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045
```

선택 후보의 실제 내부 조합:

```text
PP172 운영 예측을 기준 예측으로 둔다.

Huber basis 이동분 =
  stack_huber_weighted 로그가격 - PP172 운영 로그가격

CatBoost p95-preserving basis 이동분 =
  direct_cat_plain 로그가격 - PP172 운영 로그가격

혼합 이동분 =
  0.65 * Huber basis 이동분
  + 0.35 * CatBoost p95-preserving basis 이동분

최종 로그가격 =
  PP172 운영 로그가격
  + clip(혼합 이동분 * segment gate * 0.42, -0.0045, +0.0045)
```

해석:

- PP186은 PP180보다 MAPE가 `+0.000028` 나빠진다.
- 대신 PP180보다 p95를 `-0.000095` 낮춰 PP172와 같은 p95 수준으로 되돌린다.
- PP172 대비 MAPE는 `-0.000037` 개선되고 p95는 동일하다.
- 따라서 `순수 MAPE/overall replacement` 기준 1순위는 아직 PP180이다.
- 다만 `p95를 PP172와 동일 수준으로 고정해야 하는 운영 모드`에서는 PP186이 PP172보다 더 좋은 후보가 된다.
- `strict Huber basis` 단독 후보는 MAPE가 더 낮은 row가 있었지만 p95가 커져 운영 후보로는 제외했다.
- `Huber basis + CatBoost p95-preserving basis`를 섞는 방식이 이번 실험에서 가장 균형이 좋았다.

다음 실험 방향:

1. PP180은 MAPE 중심 운영 1순위로 유지한다.
2. PP186은 p95 고정 운영 후보로 유지한다.
3. 다음 개선은 PP180과 PP186을 row별로 라우팅하는 방식이 적합하다.
4. 라우팅 기준은 `p95 hazard`, `price band`, `confidence tier`, `quantile width`, `PP180-PP186 예측 gap`을 쓴다.
5. 목표는 PP180의 MAPE 장점은 유지하고, p95 위험 row만 PP186 쪽으로 되돌리는 것이다.

## 2026-06-10 업데이트: PP-OPT187~192 완료

`PP-OPT187~192 Warm PP180/PP186 risk router` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt187_192_warm_pp180_pp186_risk_router.py
experiments/track6/PP-OPT187_192_warm_pp180_pp186_risk_router/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP172 운영 후보 | 0.269997 | 0.807231 | 0.947115 | 0.605449 | -0.018451 |
| PP180 운영 후보 | 0.269933 | 0.807326 | 0.952244 | 0.754487 | -0.018721 |
| PP186 p95-guard 후보 | 0.269961 | 0.807231 | 0.949359 | 0.598718 | -0.018578 |
| PP192 운영 후보 | 0.269914 | 0.807326 | 0.953526 | 0.750962 | -0.018791 |
| PP222 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

선택된 PP192 운영 후보:

```text
ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP180 운영 로그가격
안정 예측 = PP186 p95-guard 로그가격

segment hazard =
  validation OOF에서
  stable_price_band × medium_support_bucket 구간별로
  PP180이 PP186보다 오차/p95를 키우는 정도

router weight =
  segment hazard와 p95 delta를 섞은 값
  * 0.95

최종 로그가격 =
  PP180 운영 로그가격
  + clip((PP186 로그가격 - PP180 로그가격) * router weight, -0.0025, +0.0025)
```

해석:

- PP192 운영 후보는 PP180 대비 MAPE를 `-0.000018` 개선한다.
- p95는 PP180과 동일한 `0.807326`으로 유지된다.
- repeated MAPE win rate도 PP180 `0.952244`에서 PP192 `0.953526`으로 개선된다.
- replacement score도 PP180 `-0.018721`에서 PP192 `-0.018791`로 개선되어 현재 운영 1순위로 갱신한다.
- p95를 낮추는 목적의 후보는 `PP192 p95-guarded`가 좋다. PP180 대비 MAPE는 `+0.000017` 나빠지지만 p95는 `-0.000071` 낮아진다.
- p95를 PP172와 완전히 같은 수준으로 고정해야 하면 PP186을 유지한다.
- 가장 큰 신호는 단순 row risk score보다 `validation segment outcome router`가 더 잘 작동했다는 점이다.

다음 실험 방향:

1. PP192 운영 후보를 새 MAPE/overall 운영 1순위로 고정한다.
2. PP189 segment router 계열만 좁게 재탐색한다.
3. 특히 `stable_price_band × medium_support_bucket`, `stable_price_band × confidence_tier` 구간에서 cap/strength/mix를 더 세밀하게 본다.
4. 목표는 PP192의 p95를 유지하면서 MAPE `0.26990` 이하 후보가 repeated stability에서도 살아남는지 확인하는 것이다.
5. p95-guarded 모드는 PP192 p95-guarded와 PP186을 둘 다 유지하고, 허용 p95 차이를 기준으로 선택한다.

## 2026-06-10 업데이트: PP-OPT193~198 완료

`PP-OPT193~198 Warm segment outcome router refinement` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt193_198_warm_segment_outcome_router_refinement.py
experiments/track6/PP-OPT193_198_warm_segment_outcome_router_refinement/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP180 운영 후보 | 0.269933 | 0.807326 | 0.952244 | 0.754487 | -0.018721 |
| PP192 운영 후보 | 0.269914 | 0.807326 | 0.953526 | 0.750962 | -0.018791 |
| PP198 MAPE challenger | 0.269894 | 0.807326 | 0.952885 | 0.747756 | -0.018785 |
| PP192 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |
| PP186 p95-guard 후보 | 0.269961 | 0.807231 | 0.949359 | 0.598718 | -0.018578 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

PP198 MAPE challenger:

```text
ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP180 운영 로그가격
안정 예측 = PP186 p95-guard 로그가격

segment hazard =
  validation OOF에서
  stable_price_band × confidence_tier 구간별로
  PP180이 PP186보다 오차/p95를 키우는 정도

router weight =
  segment hazard와 p95 delta를 섞은 값
  * 1.05

최종 로그가격 =
  PP180 운영 로그가격
  + clip((PP186 로그가격 - PP180 로그가격) * router weight, -0.006, +0.006)
```

해석:

- PP198은 PP192 대비 MAPE를 `-0.000020` 낮췄고 p95는 동일하게 유지했다.
- 다만 repeated MAPE win rate는 PP192 `0.953526`에서 PP198 `0.952885`로 낮아졌다.
- replacement score도 PP192 `-0.018791`이 PP198 `-0.018785`보다 아주 근소하게 좋다.
- PP199 이전 기준에서는 `고정 test MAPE 우선`이면 PP198이 최고 MAPE 후보였다.
- 그러나 당시 `성능 + 안정성 + replacement` 종합 운영 기준에서는 PP192를 1순위로 유지하는 편이 더 보수적이었다.
- 이번 실험은 `stable_price_band × confidence_tier`가 MAPE를 더 낮추는 방향이고, `stable_price_band × medium_support_bucket`은 안정성이 더 좋다는 차이를 확인했다.

다음 실험 방향:

1. PP192를 안정성 운영 기준으로 유지한다.
2. PP198을 MAPE 개선 challenger로 유지한다.
3. 다음은 PP192와 PP198을 row별로 다시 라우팅한다.
4. 목표는 PP198이 이기는 row만 가져오고, repeated stability가 떨어지는 row는 PP192로 되돌리는 것이다.
5. 판단 기준은 `PP192 대비 PP198 row-level APE 개선 여부`, `confidence_tier`, `stable_price_band`, `medium_support_bucket`, `PP192-PP198 log gap`을 사용한다.

## 2026-06-10 업데이트: PP-OPT199~204 완료

`PP-OPT199~204 Warm PP192/PP198 winner router` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt199_204_warm_pp192_pp198_winner_router.py
experiments/track6/PP-OPT199_204_warm_pp192_pp198_winner_router/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP192 운영 후보 | 0.269914 | 0.807326 | 0.953526 | 0.750962 | -0.018791 |
| PP198 MAPE challenger | 0.269894 | 0.807326 | 0.952885 | 0.747756 | -0.018785 |
| PP204 winner-router 운영 후보 | 0.269894 | 0.807326 | 0.953846 | 0.747756 | -0.018824 |
| PP192 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |
| PP186 p95-guard 후보 | 0.269961 | 0.807231 | 0.949359 | 0.598718 | -0.018578 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

선택된 PP204 운영 후보:

```text
ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP192 운영 로그가격
MAPE 후보 = PP198 로그가격

winner score =
  validation OOF에서
  stable_price_band × confidence_tier 구간별로
  PP198이 PP192보다 APE를 낮추는 정도
  - p95 손상 페널티

row cap =
  기본 cap
  × row별 위험도 shrink 계수

최종 로그가격 =
  PP192 운영 로그가격
  + clip((PP198 로그가격 - PP192 로그가격) * winner weight, -row cap, +row cap)
```

해석:

- PP204는 PP192 대비 MAPE를 `-0.0000208` 낮췄고 p95는 동일하게 유지했다.
- PP204는 PP198 대비 MAPE도 `-0.0000005` 낮췄고 p95는 동일하게 유지했다.
- repeated MAPE win rate는 PP192 `0.953526`, PP198 `0.952885`보다 높은 `0.953846`이다.
- replacement score도 PP192 `-0.018791`, PP198 `-0.018785`보다 좋은 `-0.018824`다.
- 따라서 `성능 + 안정성 + replacement` 종합 운영 기준을 PP192에서 PP204로 갱신한다.
- p95를 낮추는 균형 모드는 여전히 `PP192 p95-guarded`가 좋고, p95를 강하게 낮추는 전용 모드는 `PP148 p95`가 유지된다.
- 이번 실험의 핵심은 PP198 전체 채택이 아니라, validation에서 PP198이 PP192보다 안정적으로 이기는 구간만 제한적으로 가져온 것이다.

다음 실험 방향:

1. PP204를 새 MAPE/overall 운영 1순위로 고정한다.
2. PP204의 선택 구조인 `stable_price_band × confidence_tier` winner router를 좁게 재탐색한다.
3. 현재 유효 후보는 `thr=0.08`, `strength=1.0`, `basecap=0.006`, `shrink=0.8`이다.
4. 다음은 주변값인 `thr 0.0/0.04/0.08/0.12`, `strength 0.90/1.00/1.08`, `basecap 0.004/0.005/0.006/0.007`, `shrink 0.65/0.8/0.9`를 보는 것이 맞다.
5. 목표는 PP204의 MAPE를 유지하거나 더 낮추면서 repeated p95 win rate 손상을 줄이는 것이다.

## 2026-06-10 업데이트: PP-OPT205~210 완료

`PP-OPT205~210 Warm PP204 local winner-router refinement` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt205_210_warm_pp204_local_winner_router_refinement.py
experiments/track6/PP-OPT205_210_warm_pp204_local_winner_router_refinement/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP204 운영 후보 | 0.269894 | 0.807326 | 0.953846 | 0.747756 | -0.018824 |
| PP210 운영 후보 | 0.269891 | 0.807326 | 0.953846 | 0.747115 | -0.018827 |
| PP210 MAPE challenger | 0.269890 | 0.807326 | 0.952885 | 0.747115 | -0.018789 |
| PP192 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |
| PP186 p95-guard 후보 | 0.269961 | 0.807231 | 0.949359 | 0.598718 | -0.018578 |
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | 0.500962 | -0.004079 |

선택된 PP210 운영 후보:

```text
ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP192 운영 로그가격
MAPE 후보 = PP198 로그가격

winner weight =
  validation OOF에서
  stable_price_band × confidence_tier 구간별
  PP198이 PP192보다 APE를 낮추는 신호
  × gain guard
  × p95 guard

row cap =
  0.0055
  × (1 - 0.90 × row_risk)
  단, 최소 cap은 0.0008

최종 로그가격 =
  PP192 운영 로그가격
  + clip((PP198 로그가격 - PP192 로그가격) * winner weight, -row cap, +row cap)
```

해석:

- PP210 운영 후보는 PP204 대비 MAPE를 `-0.0000025` 낮췄고 p95는 동일하게 유지했다.
- replacement score도 PP204 `-0.018824`에서 PP210 `-0.018827`로 아주 소폭 개선됐다.
- repeated MAPE win rate는 PP204와 같은 `0.953846`이다.
- 다만 repeated p95 win rate는 PP204 `0.747756`에서 PP210 `0.747115`로 `-0.000641` 낮아졌다.
- 따라서 MAPE/overall replacement 우선이면 PP210이 새 1순위다.
- p95 반복 안정성까지 조금 더 보수적으로 보려면 PP204를 fallback으로 유지한다.
- PP210 MAPE challenger는 MAPE `0.269890`으로 더 낮지만 repeated MAPE win rate와 replacement score가 운영 후보보다 약해 운영 기본값으로는 쓰지 않는다.

다음 실험 방향:

1. PP210을 MAPE/overall 운영 1순위로 고정하고 PP204를 안정 fallback으로 둔다.
2. 다음은 PP210의 MAPE 이득을 유지하면서 repeated p95 win rate를 PP204 수준으로 회복하는 방향이 맞다.
3. `p95 win-rate aware router`를 별도로 만들어 p95 반복 손상이 큰 row는 PP204 또는 PP192로 되돌린다.
4. 현재 PP210은 `strength=1.16`, `basecap=0.0055`, `shrink=0.9`가 유효했다. 다음은 이 강도는 유지하되 p95-risk row만 더 강하게 줄인다.
5. 목표는 MAPE `0.269891` 이하, p95 `0.807326` 이하, repeated p95 win rate `0.747756` 이상이다.

## 2026-06-10 업데이트: PP-OPT211~216 완료

`PP-OPT211~216 Warm PP210 p95-win recovery router` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt211_216_warm_pp210_p95_win_recovery_router.py
experiments/track6/PP-OPT211_216_warm_pp210_p95_win_recovery_router/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP210 운영 후보 | 0.269891 | 0.807326 | 0.953846 | 0.747115 | -0.018827 |
| PP216 운영 선택 후보 | 0.269891 | 0.807326 | 0.953846 | 0.747115 | -0.018827 |
| PP204 fallback 후보 | 0.269894 | 0.807326 | 0.953846 | 0.747756 | -0.018824 |
| PP216 p95-recovery 후보 | 0.269898 | 0.807326 | 0.952885 | 0.749679 | -0.018782 |
| PP192 운영 후보 | 0.269914 | 0.807326 | 0.953526 | 0.750962 | -0.018791 |
| PP192 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |

선택된 PP216 운영 후보:

```text
ppopt216_operational_pp210_p95_recovery__source=ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005
```

다만 이 후보는 지표상 PP210 운영 후보와 동일하게 나왔다. 즉, 운영 관점에서는 PP210을 대체하는 개선이 아니라 `PP210 유지`로 해석한다.

가장 p95 win rate를 회복한 후보:

```text
ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2
```

선택 후보의 실제 내부 구조:

```text
PP210 rollback 계열:

기준 예측 = PP210 운영 로그가격
안정 fallback = PP204 운영 로그가격 또는 PP192 운영 로그가격

p95 harm score =
  validation OOF에서
  PP210이 fallback보다 상단 오차를 키우는 segment 신호

최종 로그가격 =
  PP210 로그가격
  + clip((fallback 로그가격 - PP210 로그가격) * rollback weight, -row cap, +row cap)

p95-aware rebuild 계열:

기준 예측 = PP192 운영 로그가격
MAPE 후보 = PP198 로그가격

최종 로그가격 =
  PP192 로그가격
  + clip((PP198 로그가격 - PP192 로그가격) * p95-aware winner weight, -row cap, +row cap)
```

해석:

- PP210 rollback 계열은 대부분 PP210과 같은 결과가 나왔고, PP210을 의미 있게 개선하지 못했다.
- p95-aware rebuild 계열은 repeated p95 win rate를 PP210 `0.747115`에서 `0.749679`로 회복했다.
- 하지만 p95-aware rebuild의 MAPE는 PP210보다 `+0.0000066` 나빠졌고 replacement score도 `-0.018827`에서 `-0.018782`로 약해졌다.
- PP204의 repeated p95 win rate `0.747756`보다 더 좋은 p95 회복 후보는 나왔지만, 운영 점수 손상이 커서 운영 1순위로 올리기는 어렵다.
- 따라서 현재 운영 후보는 PP210을 유지한다.
- p95 반복 안정성을 더 중시하는 옵션은 순서대로 `PP192 p95-guarded`, `PP192 운영 후보`, `PP216 p95-recovery 후보`, `PP204 fallback`을 비교해 선택할 수 있다.

다음 실험 방향:

1. PP210을 운영 1순위로 유지한다.
2. PP216 결과상 단순 rollback은 개선 여지가 작다.
3. p95 회복은 rebuild 방식에서만 보였으므로, 다음은 `PP192 -> PP198` winner rebuild 자체를 p95-aware objective로 다시 설계하는 편이 낫다.
4. 단순 cap/rollback보다 `MAPE objective + p95 win-rate regularization`을 선택 기준에 직접 넣는다.
5. 목표는 PP210 MAPE `0.269891`에 가까운 수준을 유지하면서 repeated p95 win rate를 최소 `0.749` 이상으로 올리는 것이다.

## 2026-06-10 업데이트: PP-OPT217~222 완료

`PP-OPT217~222 Warm p95-regularized winner rebuild` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt217_222_warm_p95_regularized_winner_rebuild.py
experiments/track6/PP-OPT217_222_warm_p95_regularized_winner_rebuild/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP210 운영 후보 | 0.269891 | 0.807326 | 0.953846 | 0.747115 | -0.018827 |
| PP204 fallback 후보 | 0.269894 | 0.807326 | 0.953846 | 0.747756 | -0.018824 |
| PP216 p95-recovery 후보 | 0.269898 | 0.807326 | 0.952885 | 0.749679 | -0.018782 |
| PP222 공격형 MAPE 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747115 | -0.018828 |
| PP222 균형 운영 후보 | 0.269890 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP210 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |

PP222 균형 운영 후보:

```text
ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9
```

PP222 공격형 MAPE 후보:

```text
ppopt222_operational_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0056__shrink_0p9
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP192 운영 로그가격
MAPE 후보 = PP198 로그가격

p95-regularized winner weight =
  validation OOF에서
  stable_price_band × confidence_tier 구간별
  PP198이 PP192보다 MAPE를 줄이는 신호
  × p95 손상 억제 bonus
  × segment count guard

row cap =
  basecap × (1 - 0.90 × row_risk)
  단, 최소 cap은 0.0006

최종 로그가격 =
  PP192 운영 로그가격
  + clip((PP198 로그가격 - PP192 로그가격) * p95-regularized winner weight, -row cap, +row cap)
```

해석:

- PP222 공격형 MAPE 후보는 PP210 대비 MAPE를 `-0.0000015` 낮췄고 replacement score도 가장 좋다.
- 다만 PP222 공격형 MAPE 후보의 repeated p95 win rate는 PP210과 같은 `0.747115`에 머문다.
- PP222 균형 운영 후보는 PP210 대비 MAPE를 `-0.0000010` 낮추면서 repeated p95 win rate를 PP204와 같은 `0.747756`까지 회복했다.
- PP222 균형 운영 후보의 replacement score도 PP210 `-0.018827`보다 좋은 `-0.018828`이다.
- PP216 p95-recovery 후보는 repeated p95 win rate가 `0.749679`로 가장 높지만 MAPE와 replacement 손상이 커서 운영 1순위는 아니다.
- 따라서 성능과 안정성을 같이 보는 운영 기준에서는 PP222 균형 운영 후보를 새 1순위로 둔다.
- 순수 MAPE/overall replacement를 더 공격적으로 보면 PP222 공격형 MAPE 후보를 별도 challenger로 둘 수 있다.

다음 실험 방향:

1. PP222 균형 운영 후보를 운영 1순위로 고정한다.
2. PP222 공격형 MAPE 후보는 challenger로 유지한다.
3. 다음은 PP222 균형 후보 주변에서 `basecap 0.0050~0.0054`, `shrink 0.85~1.00`, `strength 1.20~1.28`을 좁게 탐색한다.
4. 목표는 PP222 균형 후보의 repeated p95 win rate `0.747756` 이상을 유지하면서 MAPE를 `0.2698895` 근처로 더 당기는 것이다.
5. p95 win rate를 더 끌어올리는 실험은 PP216 p95-recovery 후보의 신호를 쓰되, MAPE 손상 허용 폭을 `+0.000003` 안으로 제한해야 한다.

## 2026-06-10 업데이트: PP-OPT223~228 완료

`PP-OPT223~228 Warm PP222 narrow balance refinement` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt223_228_warm_pp222_narrow_balance_refinement.py
experiments/track6/PP-OPT223_228_warm_pp222_narrow_balance_refinement/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP222 균형 운영 후보 | 0.269890 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP222 공격형 MAPE 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747115 | -0.018828 |
| PP228 균형 운영 후보 | 0.269890 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP228 공격형 운영 후보 | 0.269889 | 0.807326 | 0.954167 | 0.747115 | -0.018842 |
| PP228 MAPE challenger | 0.269889 | 0.807326 | 0.953526 | 0.747115 | -0.018816 |
| PP222 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |

PP228 균형 운영 후보:

```text
ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92
```

PP228 공격형 운영 후보:

```text
ppopt228_operational_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94
```

PP228 MAPE challenger:

```text
ppopt228_mape_challenger_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP192 운영 로그가격
MAPE 후보 = PP198 로그가격

p95-regularized winner weight =
  validation OOF에서
  stable_price_band × confidence_tier 구간별
  PP198이 PP192보다 MAPE를 줄이는 신호
  × p95 손상 억제 signal
  × segment count guard

row risk =
  예측 불확실성, 가격 구간 위험도, 모델 간 gap이 큰 정도를 합친 row별 위험 점수

row cap =
  basecap × (1 - shrink × row_risk^curve)
  단, PP223 neighborhood 후보는 curve 없이 PP222 주변 threshold/p95width만 좁게 재탐색

최종 로그가격 =
  PP192 운영 로그가격
  + clip((PP198 로그가격 - PP192 로그가격) * p95-regularized winner weight, -row cap, +row cap)
```

해석:

- PP228 균형 운영 후보는 PP222 균형 후보보다 fixed test MAPE를 `-0.0000005` 낮추고, repeated p95 win rate `0.747756`을 그대로 유지했다.
- PP228 공격형 운영 후보는 fixed test MAPE를 PP222 균형 후보보다 `-0.0000009` 낮추고 replacement score를 `-0.018842`까지 개선했다.
- 다만 PP228 공격형 운영 후보는 repeated p95 win rate가 `0.747115`라서 PP222/PP228 균형 후보보다 낮다.
- PP228 MAPE challenger는 MAPE만 보면 `0.269888837`로 가장 낮지만 replacement score가 공격형 운영 후보보다 약하다.
- 따라서 성능과 안정성을 같이 보는 운영 기준에서는 PP228 균형 운영 후보를 새 1순위로 둔다.
- 공격형 성능 비교에서는 PP228 공격형 운영 후보를 별도 challenger로 둔다.

다음 실험 방향:

1. PP228 균형 운영 후보를 운영 1순위로 고정한다.
2. PP228 공격형 운영 후보는 MAPE/replacement challenger로 유지한다.
3. 다음은 PP228 균형 후보의 p95 win rate `0.747756`을 하한으로 유지하면서, PP228 공격형 후보의 MAPE/replacement 개선 신호를 일부만 가져오는 p95 회복형 라우팅을 본다.
4. p95 win rate를 더 끌어올리는 후보는 PP222 p95-guarded 또는 PP216 p95-recovery 신호를 쓰되, MAPE 손상 허용 폭을 `+0.000001` 안으로 제한해야 한다.

## 2026-06-10 업데이트: PP-OPT229~234 완료

`PP-OPT229~234 Warm PP228 p95-win recovery without MAPE loss` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt229_234_warm_pp228_p95_recovery_without_mape_loss.py
experiments/track6/PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP228 균형 운영 후보 | 0.269890 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP228 공격형 운영 후보 | 0.269889 | 0.807326 | 0.954167 | 0.747115 | -0.018842 |
| PP228 MAPE challenger | 0.269889 | 0.807326 | 0.953526 | 0.747115 | -0.018816 |
| PP234 균형/운영 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP228 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |

PP234 균형/운영 후보:

```text
ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25
```

선택 후보의 실제 내부 구조:

```text
기준 예측 = PP228 균형 운영 로그가격
공격형 후보 = PP228 공격형 운영 로그가격

공격형 허용 weight =
  validation OOF에서
  stable_price_band × confidence_tier 구간별
  PP228 공격형 후보가 PP228 균형 후보보다 MAPE를 줄이는 신호
  × p95 손상 억제 signal
  × segment count guard
  × strength 0.75

row cap =
  basecap 0.00018 × (1 - 0.55 × row_risk^1.25)
  단, 최소 cap은 0.00004

최종 로그가격 =
  PP228 균형 운영 로그가격
  + clip((PP228 공격형 운영 로그가격 - PP228 균형 운영 로그가격) * 공격형 허용 weight, -row cap, +row cap)
```

정확한 개선 폭:

```text
PP228 균형 후보 MAPE = 0.2698895028254224
PP234 균형/운영 후보 MAPE = 0.2698894975680414
MAPE 개선 = -0.0000000052573810

PP228 균형 후보 repeated p95 win rate = 0.7477564102564102
PP234 균형/운영 후보 repeated p95 win rate = 0.7477564102564102
```

해석:

- PP234는 PP228 균형 후보의 repeated p95 win rate를 그대로 유지하면서 fixed test MAPE와 replacement score를 아주 작게 낮췄다.
- 개선 폭은 `5.3e-9` 수준이라 실질적으로는 PP228 균형 후보와 동급이다.
- 그래도 같은 안정성 조건에서 수치가 나빠진 항목이 없으므로, 엄격한 지표 기준의 최신 운영 후보는 PP234로 둘 수 있다.
- PP228 공격형 후보는 replacement score가 가장 좋지만 repeated p95 win rate가 낮아 운영 기본값보다는 challenger로 유지한다.
- PP228 p95-guarded는 p95 win rate가 더 높지만 MAPE/replacement 손상이 커서 p95 우선 모드에서만 사용한다.

다음 실험 방향:

1. 미세 cap 보정만으로는 개선 폭이 거의 바닥에 가까워졌다.
2. 다음은 PP234가 정말 의미 있는지 bootstrap/row 영향도 검증을 먼저 해야 한다.
3. 이후 추가 개선을 노리려면 단순 cap 조정보다 `row-level learned router`, `basis 재생성`, `보정 모델 재학습`처럼 한 단계 큰 구조를 검토하는 편이 낫다.

## 2026-06-10 업데이트: PP-OPT235~240 완료

`PP-OPT235~240 Warm PP234 significance audit and learned router jump` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt235_240_warm_pp234_significance_audit_and_learned_router.py
experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router/
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP234 균형/운영 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP240 균형 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP240 공격형 후보 | 0.269889 | 0.807326 | 0.954167 | 0.747115 | -0.018842 |
| PP228 MAPE challenger | 0.269889 | 0.807326 | 0.953526 | 0.747115 | -0.018816 |
| PP216 p95-recovery 후보 | 0.269898 | 0.807326 | 0.952885 | 0.749679 | -0.018782 |
| PP234 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |

PP234 유의성 검증:

| 비교 | test 평균 MAPE 차이 | bootstrap 5% | bootstrap 50% | bootstrap 95% | bootstrap 개선 비율 | 개선 row | 악화 row |
|---|---:|---:|---:|---:|---:|---:|---:|
| PP234 - PP228 균형 | -0.0000000053 | -0.0000000239 | -0.0000000055 | 0.0000000144 | 0.6800 | 6 | 3 |
| PP234 - PP228 공격형 | 0.0000003898 | -0.0000010556 | 0.0000004175 | 0.0000018121 | 0.3305 | 3 | 6 |
| PP234 - PP228 MAPE | 0.0000006604 | -0.0000032029 | 0.0000007507 | 0.0000046309 | 0.3705 | 3 | 6 |

해석:

- PP234는 PP228 균형 후보보다 평균 MAPE가 낮지만 bootstrap 90% 구간이 0을 포함한다.
- 차이가 난 row도 9건 수준이라, PP234 개선은 “수치상 최신 best”이지만 강한 통계적 개선이라고 보기는 어렵다.
- PP240 learned router는 validation OOF 기반으로 row별 후보를 선택했지만, 운영 제약을 만족하면서 PP234보다 좋아지지는 않았다.
- PP240 공격형 후보는 사실상 PP228 공격형 후보와 같은 성능이다. MAPE/replacement는 좋지만 repeated p95 win rate가 `0.747115`로 PP234보다 낮다.
- learned multiclass/probability blend 계열은 p95 APE를 `0.807310~0.807315`까지 낮추는 후보를 만들었지만 MAPE와 replacement score가 나빠졌고 repeated p95 win rate도 운영 하한을 만족하지 못했다.
- 따라서 운영 1순위는 PP234를 유지한다.

다음 실험 방향:

1. 단순 learned router는 PP234를 대체하지 못했다.
2. 다음은 learned router를 계속하더라도 `p95 win rate >= PP234`를 사후 필터가 아니라 학습/선택 목적함수에 직접 넣어야 한다.
3. p95 APE를 낮춘 PP237/PP239 계열의 신호는 버리지 말고, PP234 대비 MAPE 손상 `+0.000001` 이하인 초소형 p95-support로 다시 제한한다.
4. 더 큰 개선을 원하면 PP234 위의 라우팅보다 기준가 생성 자체를 다시 만드는 `basis regeneration` 또는 residual correction 재학습을 병행해야 한다.

## 2026-06-10 업데이트: PP-OPT241~246 완료

`PP-OPT241~246 Warm PP234 p95-constrained support and basis regeneration pilot` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt241_246_warm_pp234_p95_constrained_support_and_basis_regeneration.py
experiments/track6/PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration/
```

데이터 기준:

```text
제출용 제외
기존 Warm validation OOF 519건
기존 Warm fixed test 607건
총 후보 1020개
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP234 균형 기준 | 0.2698894976 | 0.8073255047 | 0.953846 | 0.747756 | -0.0188283905 |
| PP246 균형 후보 | 0.2698894903 | 0.8073255047 | 0.953846 | 0.747756 | -0.0188283978 |
| PP246 운영/공격형 후보 | 0.2698891078 | 0.8073255047 | 0.954167 | 0.747115 | -0.0188416008 |
| PP246 p95-recovery 후보 | 0.2698902775 | 0.8073212839 | 0.954167 | 0.814103 | -0.0188404311 |
| PP246 p95-guarded 후보 | 0.2699492011 | 0.8072545738 | 0.950962 | 0.751603 | -0.0186533023 |
| PP240 p95-recovery 기준 | 약 0.269890 | 0.807323 | 0.953846 | 0.827244 | -0.018828 |

실험별 최선 흐름:

| 실험 | 목적 | 결과 |
|---|---|---|
| PP241 | PP237/PP239 p95 신호를 PP234 위에 초소형 support로 얹기 | PP234 대비 MAPE `-0.0000000073`, p95/반복 안정성 유지 |
| PP242 | guarded/recovery 후보를 더 약하게 얹기 | PP241/PP234 수준을 넘지 못함 |
| PP243 | Huber/Ridge 잔차 재학습 | p95 APE와 p95 win rate 개선 후보 생성, 기본 MAPE는 소폭 악화 |
| PP244 | LightGBM/XGBoost/CatBoost/HistGradientBoosting 잔차 재학습 | 일부 p95 개선은 있었지만 PP243 Huber 잔차보다 운영 균형이 약함 |
| PP245 | 잔차 보정과 p95 support 앙상블 | p95는 개선되지만 PP246 균형 후보를 대체하지 못함 |
| PP246 | 최종 선택 layer | 균형 기준은 PP241 support, p95-recovery는 PP243 Huber 잔차 선택 |

해석:

- 엄격한 수치 기준의 최신 균형 후보는 `PP246 균형 후보`다. PP234보다 MAPE와 replacement score가 각각 약 `7.3e-9` 좋아지고 p95 관련 반복 안정성은 그대로 유지한다.
- 개선 폭은 PP234의 PP228 대비 개선보다도 작은 수준이라 실무적으로는 PP234와 같은 계열의 동급 후보로 봐야 한다.
- `PP246 운영/공격형 후보`는 PP240/PP228 공격형 계열을 다시 선택한다. MAPE와 replacement score는 좋지만 repeated p95 win rate가 PP234/PP246 균형 후보보다 낮아 안정 기본값으로 쓰기는 어렵다.
- `PP246 p95-recovery 후보`는 Huber 잔차 보정으로 p95 APE를 `0.807321`까지 낮추고 repeated p95 win rate를 `0.814103`까지 올렸다. 대신 PP234 대비 MAPE가 `+0.000000780` 나빠진다.
- LightGBM/XGBoost/CatBoost 잔차 보정은 이번 조건에서는 Huber/Ridge 잔차보다 강한 운영 개선을 만들지 못했다. 특히 트리 잔차는 p95 APE를 낮춰도 repeated p95 win rate나 replacement score가 불안정해지는 후보가 많았다.
- 따라서 운영 기본값은 PP246 균형 후보로 갱신할 수 있지만, 문서/설명에서는 “PP234 위의 극소 p95-support wrapper”라고 설명하는 편이 정확하다.

다음 실험 방향:

1. PP234/PP246 위의 tiny cap 보정은 거의 포화 상태다.
2. p95를 더 올리는 목적이면 PP243 Huber residual recovery를 별도 모드로 유지할 수 있다.
3. 운영 MAPE를 의미 있게 더 낮추려면 보정값의 cap만 조정하기보다 기준가 생성 또는 residual target 자체를 다시 잡아야 한다.
4. 다음 후보는 `validation 잔차의 방향성 분류 + 확신 있을 때만 이동`, `quantile residual band별 비대칭 cap`, `row-level objective를 MAPE와 p95 win rate 동시 최적화`하는 쪽이 적합하다.

## 2026-06-10 업데이트: PP-OPT247~252 완료

`PP-OPT247~252 Warm PP246 residual-direction gated correction and asymmetric quantile caps` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt247_252_warm_pp246_residual_direction_gated_correction.py
experiments/track6/PP-OPT247_252_warm_pp246_residual_direction_gated_correction/
```

데이터 기준:

```text
제출용 제외
기존 Warm validation OOF 519건
기존 Warm fixed test 607건
총 후보 1360개
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP246 균형 기준 | 0.2698894903 | 0.8073255047 | 0.953846 | 0.747756 | -0.0188283978 |
| PP252 균형 후보 | 0.2698887309 | 0.8073244865 | 0.953846 | 0.788782 | -0.0188291572 |
| PP252 운영/안정 후보 | 0.2698897744 | 0.8073255047 | 0.954167 | 0.816667 | -0.0188409342 |
| PP252 p95-recovery 후보 | 0.2698905666 | 0.8073206977 | 0.953846 | 0.789423 | -0.0188273215 |
| PP246 p95-recovery 기준 | 0.2698902775 | 0.8073212839 | 0.954167 | 0.814103 | -0.0188404311 |
| PP246 p95-guarded 기준 | 0.2699492011 | 0.8072545738 | 0.950962 | 0.751603 | -0.0186533023 |

실험별 최선 흐름:

| 실험 | 목적 | 결과 |
|---|---|---|
| PP247 | residual direction probability gate | 방향 분류만으로 후보 이동을 제한했지만 PP252 균형 후보를 넘지는 못함 |
| PP248 | asymmetric quantile residual cap | p95 APE를 낮추는 후보는 만들었지만 MAPE/반복 안정성 손상이 남음 |
| PP249 | direction-gated residual correction | p95 APE 최저권 후보를 만들었지만 p95 win rate는 PP252 균형보다 낮음 |
| PP250 | segment residual-direction router | p95 win rate를 크게 올리는 운영/안정 후보 생성, MAPE는 소폭 악화 |
| PP251 | direction residual plus p95 support ensemble | PP246 대비 MAPE, p95 APE, repeated p95 win rate를 동시에 개선 |
| PP252 | final selection layer | 균형 후보는 PP251 ensemble, 안정 후보는 PP250 segment router 선택 |

해석:

- 이번 실험은 이전 tiny cap 실험보다 개선 폭이 커졌다. PP252 균형 후보는 PP246 대비 MAPE를 `-0.0000007594`, p95 APE를 `-0.0000010181`, repeated p95 win rate를 `+0.041026` 개선했다.
- 핵심은 단순히 보정 cap을 키운 것이 아니라, `HistGradientBoosting direction classifier`가 과소/과대 예측 방향을 먼저 고르고 `Huber residual`과 p95 support를 같은 방향일 때만 합친 점이다.
- PP251의 최선 후보는 `hist35_seed17` 방향 확률 + `huber_1p15` 잔차 + p95 support ensemble이다.
- PP250 segment router는 p95 win rate를 `0.816667`까지 올렸지만, PP246 대비 MAPE가 `+0.000000284` 나빠져 운영 기본값보다는 안정성 우선 후보로 둔다.
- PP249는 p95 APE를 `0.8073207`까지 낮췄지만 MAPE 손상이 `+0.000001076`으로 커서 p95 회복 전용 후보로만 적합하다.
- 따라서 현재 운영 기본 후보는 PP246에서 PP252 균형 후보로 갱신한다.

다음 실험 방향:

1. 방향 gate + Huber residual + p95 support ensemble이 실제 개선 신호를 만들었다.
2. 다음은 PP252 균형 후보를 기준으로 같은 구조를 더 좁게 재탐색한다.
3. 특히 `hist35 direction classifier`, `huber_1p15 residual`, `p95 support cap 0.00006~0.00012`, `residual strength 0.04~0.07`, `support strength 0.03~0.06` 구간을 세밀화한다.
4. PP250의 높은 p95 win rate 신호는 별도 안정성 가중 후보로 유지하되, 균형 후보에는 너무 강하게 섞지 않는다.

## 2026-06-10 업데이트: PP-OPT253~258 완료

`PP-OPT253~258 Warm PP252 narrow direction-residual support refinement` 실험을 완료했다.

위치:

```text
scripts/track6/run_pp_opt253_258_warm_pp252_narrow_direction_residual_refinement.py
experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/
```

데이터 기준:

```text
제출용 제외
기존 Warm validation OOF 519건
기존 Warm fixed test 607건
총 후보 1610개
```

핵심 결과:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP252 균형 기준 | 0.2698887309 | 0.8073244865 | 0.953846 | 0.788782 | -0.0188291572 |
| PP258 균형 후보 | 0.2698881958 | 0.8073247073 | 0.953846 | 0.788782 | -0.0188296923 |
| PP258 p95-recovery 후보 | 0.2698891307 | 0.8073226276 | 0.953846 | 0.788782 | -0.0188287574 |
| PP258 안정성 우선 후보 | 0.2698897744 | 0.8073255047 | 0.954167 | 0.816667 | -0.0188409342 |
| PP252 p95-guarded 기준 | 0.2699492011 | 0.8072545738 | 0.950962 | 0.751603 | -0.0186533023 |

실험별 최선 흐름:

| 실험 | 목적 | 결과 |
|---|---|---|
| PP253 | PP252 위의 hist35 direction + Huber + p95 support 좁은 재탐색 | p95 APE를 더 낮추는 후보는 만들었지만 균형 후보 MAPE는 PP258 최종보다 약함 |
| PP254 | confidence threshold와 cap split 세분화 | PP252보다 좋은 후보가 있었지만 PP256 residual continuation이 더 우세 |
| PP255 | PP250 안정성 이동분 약한 추가 | 안정성 후보를 강화하지 못했고 균형 후보 개선에도 제한적 |
| PP256 | PP252 source residual continuation | PP252 예측의 잔차 방향을 한 번 더 약하게 이어 붙여 최종 균형 후보 생성 |
| PP257 | direction probability ensemble refinement | 일부 p95 후보는 개선됐지만 MAPE/replacement 종합에서 PP256을 넘지 못함 |
| PP258 | final selection layer | 균형 후보는 PP256 residual continuation, p95-recovery는 PP253 support 후보, 안정 후보는 PP252 운영/안정 후보 유지 |

해석:

- PP258 균형 후보는 PP252 대비 MAPE를 `-0.0000005351` 낮췄고 replacement score도 `-0.0188291572`에서 `-0.0188296923`으로 개선했다.
- repeated p95 win rate는 PP252와 같은 `0.788782`를 유지했다.
- fixed p95 APE는 PP252보다 `+0.0000002207` 나빠졌지만, PP246 이전 후보보다 여전히 좋은 수준이고 MAPE/replacement 이득이 있어 균형 후보로 채택할 수 있다.
- 개선의 핵심은 PP252의 방향 gate 구조를 크게 바꾼 것이 아니라, PP252 예측 잔차를 대상으로 `direction confidence`가 있는 row에만 매우 작은 2차 Huber 잔차 보정을 이어 붙인 점이다.
- 최종 보정 크기는 cap `0.00005` 로그 단위 안으로 제한된다. 즉, 가격을 크게 흔드는 모델이 아니라 PP252의 방향성 신호를 보존한 미세 보정이다.
- PP253 계열은 p95 APE를 더 낮출 수 있었지만 MAPE가 PP258 균형 후보보다 나빠 p95-recovery 모드로만 둔다.
- PP255의 안정성 add-on은 신규 개선을 만들지 못했다. 안정성 우선 후보는 기존 PP252 segment residual-direction router가 그대로 더 적합하다.

다음 실험 방향:

1. PP258 균형 후보를 최신 운영 기본 후보로 둔다.
2. 개선 폭이 다시 `5e-7` 수준으로 작아졌으므로, 다음은 무작정 추가 튜닝하기보다 PP258 개선이 특정 row 몇 개에 의존하는지 먼저 확인한다.
3. bootstrap, row impact, segment impact audit으로 PP258과 PP252/PP246/PP228 운영 후보를 비교한다.
4. audit에서 PP256 continuation이 안정적으로 이긴다면 residual strength `0.015~0.035`, cap `0.00003~0.00006`, threshold `0.10~0.16` 주변만 추가로 좁게 본다.
5. audit에서 특정 row 의존성이 크면 PP258을 운영 기본값으로 올리지 않고 PP252를 fallback으로 유지한다.

## 현재 운영 1순위

현재 운영 후보 1순위는 `PP258 PP252 residual continuation balanced`다. PP258 균형 후보는 PP252 균형 후보보다 fixed test MAPE를 `-0.0000005351` 낮추고, repeated p95 win rate `0.788782`를 유지했다. fixed p95 APE는 PP252보다 `+0.0000002207` 나빠졌지만, replacement score가 더 좋아져 성능과 안정성을 같이 보는 운영 기본 후보로는 PP258이 가장 앞선다. p95 win rate를 더 높이는 안정성 우선 모드에서는 `PP252 segment residual-direction router`를, p95 APE를 더 보수적으로 낮추는 모드에서는 `PP258 p95-recovery`와 기존 p95-guarded/extreme 후보를 별도 fallback으로 둔다.

정확한 후보명:

```text
ppopt258_balanced_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05
```

PP258 균형 후보는 PP252 균형 예측에서 출발한다. PP252는 PP246 균형 예측 위에 validation OOF 잔차 부호 기반 direction classifier, Huber residual correction, p95 support 이동량을 같은 방향일 때만 합치는 구조였다. PP258은 이 PP252 결과를 기준값으로 두고, PP252가 아직 남긴 잔차 방향을 Huber residual continuation으로 한 번 더 아주 약하게 보정한다. 최종 보정은 direction confidence가 기준을 넘는 row에만 적용하고, 이동량은 로그가격 기준 cap `0.00005` 안으로 제한한다. 핵심은 “이미 안정화된 PP252를 크게 흔들지 않고, 잔차 방향이 다시 확인되는 row만 미세 이동”하는 구조다.

주요 수치:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | 반복 p95 win rate | replacement score |
|---|---:|---:|---:|---:|---:|
| PP126 운영 기준 | 0.270114 | 0.807490 | 0.919231 | 0.494231 | -0.017219 |
| PP148 운영 후보 | 0.270140 | 0.807231 | 0.925962 | 0.531090 | -0.017463 |
| PP166 운영 후보 | 0.269997 | 0.807231 | 0.946795 | 0.601923 | -0.018439 |
| PP172 운영 후보 | 0.269997 | 0.807231 | 0.947115 | 0.605449 | -0.018451 |
| PP180 운영 후보 | 0.269933 | 0.807326 | 0.952244 | 0.754487 | -0.018721 |
| PP186 p95-guard 운영 후보 | 0.269961 | 0.807231 | 0.949359 | 0.598718 | -0.018578 |
| PP192 운영 후보 | 0.269914 | 0.807326 | 0.953526 | 0.750962 | -0.018791 |
| PP192 p95-guarded 후보 | 0.269949 | 0.807255 | 0.950962 | 0.751603 | -0.018653 |
| PP198 MAPE challenger | 0.269894 | 0.807326 | 0.952885 | 0.747756 | -0.018785 |
| PP204 운영 후보 | 0.269894 | 0.807326 | 0.953846 | 0.747756 | -0.018824 |
| PP210 운영 후보 | 0.269891 | 0.807326 | 0.953846 | 0.747115 | -0.018827 |
| PP222 균형 운영 후보 | 0.269890 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP222 공격형 MAPE 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747115 | -0.018828 |
| PP228 균형 운영 후보 | 0.269890 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP228 공격형 운영 후보 | 0.269889 | 0.807326 | 0.954167 | 0.747115 | -0.018842 |
| PP228 MAPE challenger | 0.269889 | 0.807326 | 0.953526 | 0.747115 | -0.018816 |
| PP234 균형/운영 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP246 균형 후보 | 0.269889 | 0.807326 | 0.953846 | 0.747756 | -0.018828 |
| PP252 균형 후보 | 0.269889 | 0.807324 | 0.953846 | 0.788782 | -0.018829 |
| PP252 안정성 우선 후보 | 0.269890 | 0.807326 | 0.954167 | 0.816667 | -0.018841 |
| PP258 균형 후보 | 0.269888 | 0.807325 | 0.953846 | 0.788782 | -0.018830 |
| PP258 p95-recovery 후보 | 0.269889 | 0.807323 | 0.953846 | 0.788782 | -0.018829 |

해석:

- PP192는 PP180보다 MAPE와 replacement score가 좋아졌고 p95는 동일하다.
- PP198은 PP192보다 MAPE는 좋지만 replacement score가 미세하게 낮았다.
- PP204는 PP198의 MAPE 개선분을 일부 가져오면서 PP192보다 repeated MAPE win rate와 replacement score까지 좋아졌다.
- PP210은 PP204 주변의 cap/strength/shrink를 조정해 MAPE와 replacement score를 한 번 더 아주 작게 개선했다.
- PP222는 PP210의 MAPE 개선 흐름을 유지하면서 PP204 수준의 p95 반복 안정성을 되찾았다.
- PP228은 PP222 균형 후보 주변을 더 좁게 탐색해 p95 반복 안정성을 유지한 상태에서 MAPE를 한 번 더 낮췄다.
- PP234는 PP228 균형 후보에서 PP228 공격형 후보로 극소량 이동해 p95 반복 안정성은 유지하고 MAPE를 `5.3e-9` 더 낮췄다.
- PP246은 PP234 위에 p95 support를 극소 cap으로 얹어 같은 p95 반복 안정성에서 MAPE를 `7.3e-9` 더 낮췄다.
- PP252는 방향 gate + Huber residual + p95 support ensemble로 PP246 대비 MAPE, p95 APE, repeated p95 win rate를 동시에 개선했다.
- PP258은 PP252 위에 residual continuation을 극소 cap으로 한 번 더 얹어 같은 repeated p95 win rate에서 MAPE와 replacement score를 추가 개선했다.
- 따라서 성능과 안정성 종합 운영 기준은 PP258 균형 후보로 갱신한다.
- 순수 MAPE와 replacement score까지 공격적으로 보면 PP228 공격형 운영 후보가 더 좋지만, p95 반복 win rate까지 보면 PP228 균형 후보가 운영 기본값에 더 적합하다.
- p95를 일부 낮춰야 하는 균형 모드라면 PP228 p95-guarded를 쓴다. 이 후보는 이전 PP192/PP210/PP222 p95-guarded 계열과 같은 성격의 p95 완화형 후보로 유지된다.
- p95를 PP172와 동일 수준으로 고정해야 하는 보수 모드라면 PP186을 쓴다.
- PP172는 PP186보다 MAPE가 높으므로 이제 보수 fallback으로만 둔다.

## p95 전용 후보

p95 방어 전용 후보는 `reference_pp148_p95`다.

주요 수치:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | replacement score |
|---|---:|---:|---:|---:|
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | -0.004079 |

해석:

- p95는 PP126 대비 약 `-0.001541` 개선된다.
- 하지만 MAPE 반복 안정성이 낮아서 운영 기본값으로 쓰면 안 된다.
- tail-risk 전용 모드 또는 별도 안정성 옵션으로만 고려한다.

## 최근 실험 흐름

### PP127~134: learned stack correction

위치:

```text
scripts/track6/run_pp_opt127_134_warm_learned_stack_correction.py
experiments/track6/PP-OPT127_134_warm_learned_stack_correction/
```

결론:

- fixed test MAPE는 `0.270033`까지 내려갔다.
- p95는 `0.807490`으로 PP126과 동일했다.
- 그러나 repeated stability가 PP126보다 약했다.
- 운영 교체 후보는 아니고 challenger로 유지한다.

### PP135~138: p95-aware correction

위치:

```text
scripts/track6/run_pp_opt135_138_warm_p95_aware_correction.py
experiments/track6/PP-OPT135_138_warm_p95_aware_correction/
```

결론:

- hard guard, tail-harm rollback, row-level cap으로는 PP127 계열의 p95 손상을 충분히 해결하지 못했다.
- 최종 선택은 PP126으로 fallback됐다.

### PP139~142: direct meta stack

위치:

```text
scripts/track6/run_pp_opt139_142_warm_direct_meta_stack.py
experiments/track6/PP-OPT139_142_warm_direct_meta_stack/
```

결론:

- direct LightGBM meta-stack은 p95를 낮추는 힘이 있었다.
- 하지만 전역 적용하면 MAPE가 나빠진다.
- p95 후보는 MAPE `0.270699`, p95 `0.805930`.
- 운영 후보는 아님. tail-risk 보조 후보로 의미가 있다.

### PP143~148: row-level tail router

위치:

```text
scripts/track6/run_pp_opt143_148_warm_row_level_tail_router.py
experiments/track6/PP-OPT143_148_warm_row_level_tail_router/
```

결론:

- 현재 운영 1순위가 된 실험이다.
- PP126 기본 예측을 유지하고, 일부 row에만 direct meta p95 후보를 제한 적용한다.
- 운영 후보 PP148:
  - MAPE `0.270140`
  - p95 `0.807231`
  - replacement score `-0.017463`
- PP126보다 MAPE는 아주 조금 나쁘지만, p95와 반복 안정성은 좋아졌다.

### PP149~154: Huber adoption stabilization

위치:

```text
scripts/track6/run_pp_opt149_154_warm_huber_adoption_stabilization.py
experiments/track6/PP-OPT149_154_warm_huber_adoption_stabilization/
```

결론:

- direct LightGBM Huber 보정은 fixed test MAPE를 크게 낮추는 신호가 있다.
- 최고 fixed MAPE 후보는 대략 MAPE `0.269795`, p95 `0.806813`.
- 하지만 repeated MAPE win rate가 `0.86`대까지 떨어진다.
- 운영 후보로는 불안정하다.
- 최종 선택은 PP148 fallback.

### PP155~160: strict Huber gate

위치:

```text
scripts/track6/run_pp_opt155_160_warm_strict_huber_gate.py
experiments/track6/PP-OPT155_160_warm_strict_huber_gate/
```

결론:

- PP149의 낮은 MAPE 신호를 더 엄격한 gate로 안정화하려고 했다.
- 최종 운영 선택은 여전히 PP148이다.
- 의미 있는 후보는 PP157 segment quantile strict Huber gate다.

PP157 주요 후보:

| 후보 계열 | MAPE | p95 APE | 반복 MAPE win rate | replacement score |
|---|---:|---:|---:|---:|
| PP157 price_qwidth segment | 0.269983 | 0.806851 | 0.886538 | -0.016042 |

해석:

- PP157은 MAPE/p95를 동시에 낮추지만 반복 안정성이 PP148보다 부족하다.
- PP149보다 보수적으로 안정화됐지만, 운영 기준에는 아직 부족하다.

### PP161~166: PP157 negative-gate rollback

위치:

```text
scripts/track6/run_pp_opt161_166_warm_pp157_negative_gate_rollback.py
experiments/track6/PP-OPT161_166_warm_pp157_negative_gate_rollback/
```

결론:

- PP157이 PP148보다 손해를 볼 가능성이 큰 row를 validation OOF에서 라벨링하고, 그 구간은 PP148로 되돌리는 구조다.
- 최종 운영 후보는 `PP163 segment outcome rollback`에서 나온 후보를 `PP166` decision layer가 선택했다.
- 운영 후보 PP166:
  - MAPE `0.269997`
  - p95 `0.807231`
  - repeated MAPE win rate `0.946795`
  - replacement score `-0.018439`
- PP148보다 MAPE가 좋아지고 p95는 유지되어 현재 운영 1순위로 올린다.

### PP167~172: PP166 second-stage tail calibration

위치:

```text
scripts/track6/run_pp_opt167_172_warm_pp166_second_stage_tail_calibration.py
experiments/track6/PP-OPT167_172_warm_pp166_second_stage_tail_calibration/
```

결론:

- PP166을 기준으로 두고 p95 후보의 이동분을 tail-risk row와 가격대/신뢰도 구간에만 아주 약하게 얹었다.
- 최종 운영 후보는 `PP169 segment p95 candidate router`에서 나온 후보를 `PP172` decision layer가 선택했다.
- 운영 후보 PP172:
  - MAPE `0.269997`
  - p95 `0.807231`
  - repeated MAPE win rate `0.947115`
  - repeated p95 win rate `0.605449`
  - replacement score `-0.018451`
- PP166 대비 fixed test 개선은 사실상 없고, repeated stability만 미세하게 개선됐다.
- 따라서 PP172는 잠정 운영 1순위로 둘 수 있지만, 실질적으로는 PP166과 같은 계열의 아주 작은 안정화 개선이다.

### PP173~180: basis-generation challenger

위치:

```text
scripts/track6/run_pp_opt173_180_warm_basis_generation_challenger.py
experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/
```

결론:

- PP172 위의 작은 보정이 아니라 기준가 후보 자체를 바꾸는 실험이다.
- validation OOF residual 기반 segment 기준가, direct LightGBM/CatBoost/XGBoost/Huber 기준가, quantile 기준가를 비교했다.
- 최종 운영 후보는 `PP174 direct model basis routing`에서 나온 `stack_huber_weighted` 기준가 제한 적용 후보를 `PP180` decision layer가 선택했다.
- 운영 후보 PP180:
  - MAPE `0.269933`
  - p95 `0.807326`
  - repeated MAPE win rate `0.952244`
  - repeated p95 win rate `0.754487`
  - replacement score `-0.018721`
- PP172 대비 MAPE와 repeated stability는 좋아졌지만 p95는 `+0.000095` 나빠졌다.
- p95가 PP126보다 좋으면 허용하는 운영 기준에서는 PP180이 현재 1순위다.
- p95를 PP172와 동일하게 유지해야 하면 PP172를 fallback으로 둔다.

## 현재 판단

운영 모델 후보:

```text
1순위: PP258 PP252 residual continuation balanced
직전 운영 후보/fallback: PP252 PP246 direction residual plus p95 support ensemble balanced
안정성 우선 후보: PP252 segment residual-direction router
p95 회복 후보: PP258 narrow hist35 Huber support p95-recovery
실질 동급 직전 기준 후보: PP246 PP234 p95-constrained balanced support
이전 최신 기준 후보: PP234 PP228 p95-win recovery balanced
실질 동급 기준 후보: PP228 PP222 narrow balance refinement balanced
공격형 MAPE/replacement challenger: PP240/PP228 PP222 narrow balance refinement operational
MAPE-only challenger: PP240/PP228 PP222 narrow balance refinement mape challenger
p95 win-rate 회복 이전 후보: PP246 Huber residual p95-recovery
p95 반복 안정 fallback: PP222 p95-regularized winner rebuild balanced
p95 win-rate 회복 분석 후보: PP216 p95-aware rebuild recovery
이전 운영 후보/fallback: PP210 PP204 local winner-router refinement
이전 장기 fallback: PP192 PP180/PP186 risk router
이전 MAPE challenger: PP198 segment router refinement
p95 완화형 운영 후보: PP228 p95-guarded risk router
p95 완전 고정 운영 후보: PP186 Huber basis p95-guard
p95 보수 fallback: PP172 PP166 second-stage tail calibration
6순위: PP166 PP157 negative-gate rollback
7순위: PP148 row-level tail router
8순위: PP126 operational
보조 후보: PP157 segment quantile strict Huber gate
보류: PP149 direct LightGBM Huber small-cap 후보
```

정리하면:

- 성능과 안정성 종합 운영 기준: PP258 균형 후보가 현재 최신 최고다.
- PP258의 PP252 대비 MAPE 개선은 `5.35e-7`이고, repeated p95 win rate는 `0.788782`로 유지된다.
- fixed p95 APE는 PP252보다 `2.21e-7` 나빠졌지만, PP246 이전 후보보다 여전히 좋고 replacement score가 더 좋아 운영 기본값으로 채택할 수 있다.
- fixed test MAPE 단일 기준에서도 PP258 균형 후보가 현재 최저권이다. 다만 개선 폭이 작으므로 bootstrap/row impact audit 전에는 “확정 대체”보다 “최신 1순위 후보”로 표현하는 편이 안전하다.
- 운영 기본값 기준: PP258은 PP252 균형 후보 대비 MAPE와 replacement score를 개선하면서 repeated p95 win rate를 유지했기 때문에 최신 후보로 둔다.
- 안정성 우선 기준: PP252 segment residual-direction router는 PP258 대비 MAPE를 손상시키지만 repeated p95 win rate를 `0.816667`까지 올린다.
- p95 회복 기준: PP258 narrow hist35 Huber support p95-recovery는 fixed p95 APE를 `0.807323`까지 낮추지만 MAPE 손상이 있어 별도 모드로 둔다.
- p95 고정 기준: PP186이 PP172보다 MAPE가 낮아 더 적합하다.
- 이번 결과에서 `stack_huber_weighted` 기준가를 약하게 라우팅하는 방식이 가장 의미 있는 개선 신호를 보였다.
- PP181~186 결과에서 `stack_huber_weighted`만 강하게 쓰면 MAPE는 더 좋아질 수 있지만 p95 손상이 생긴다.
- p95를 유지하려면 `stack_huber_weighted` 이동분과 `direct_cat_plain` 이동분을 섞고 cap을 작게 두는 방식이 가장 안정적이었다.
- PP187~192 결과에서는 단순 위험 점수보다 `validation segment outcome router`가 더 의미 있었다.
- 특히 `stable_price_band × medium_support_bucket` 구간별 rollback이 PP180의 p95를 유지하면서 MAPE를 낮췄다.
- PP193~198 결과에서는 `stable_price_band × confidence_tier` 구간이 MAPE를 더 낮췄지만 repeated stability가 PP192보다 아주 조금 낮아졌다.
- PP199~204 결과에서는 PP192와 PP198을 다시 row별로 라우팅해 PP204가 MAPE, repeated MAPE win rate, replacement score를 모두 개선했다.
- PP205~210 결과에서는 PP204 주변의 local cap/strength/shrink 조정으로 PP210이 MAPE와 replacement score를 더 낮췄지만 repeated p95 win rate는 아주 작게 낮아졌다.
- PP211~216 결과에서는 p95 win rate 회복 후보가 나왔지만 MAPE와 replacement 손상이 커서 PP210을 대체하지는 못했다.
- PP217~222 결과에서는 p95-regularized rebuild가 성공했고, PP222 균형 후보가 PP210보다 MAPE/replacement를 개선하면서 PP204 수준의 p95 win rate를 회복했다.
- PP223~228 결과에서는 PP222 균형 후보 주변의 아주 좁은 탐색이 성공했고, PP228 균형 후보가 같은 p95 win rate에서 MAPE를 추가로 낮췄다.
- PP229~234 결과에서는 PP228 균형 후보에서 공격형 후보 방향으로 극소량 이동하는 PP234가 같은 p95 win rate에서 MAPE를 `5.3e-9` 더 낮췄다.
- PP235~240 결과에서는 PP234의 미세 개선이 bootstrap상 강하지 않고, learned router도 PP234의 p95 win rate를 유지하면서 MAPE를 더 낮추지는 못했다.
- PP241~246 결과에서는 PP234 위에 p95-support를 극소 cap으로 얹은 PP246 균형 후보가 같은 repeated p95 win rate에서 MAPE를 `7.3e-9` 더 낮췄다. Huber residual p95-recovery는 p95 win rate를 크게 올렸지만 MAPE가 소폭 나빠져 별도 모드로 둔다.
- PP247~252 결과에서는 direction classifier + Huber residual + p95 support ensemble이 성공했고, PP252 균형 후보가 PP246 대비 MAPE, p95 APE, repeated p95 win rate를 동시에 개선했다.
- PP253~258 결과에서는 PP252 예측 잔차를 대상으로 residual continuation을 아주 약하게 이어 붙인 PP258 균형 후보가 PP252 대비 MAPE와 replacement score를 추가 개선했고, repeated p95 win rate는 유지했다.
- PP157의 순수 MAPE 개선 신호는 의미가 있었고, negative gate rollback, second-stage tail calibration, Huber basis routing으로 운영 안정성을 끌어올렸다.
- p95 전용 최저 후보는 여전히 PP148 p95 후보가 적합하다.

## 다음에 이어서 할 작업

다음 실험은 PP258 균형 후보를 최신 운영 후보로 두고, 먼저 개선 신호가 특정 row나 특정 segment에 과하게 의존하는지 확인하는 감사 실험이 맞다. PP253~258에서 MAPE는 추가 개선됐지만 개선 폭이 `5e-7` 수준으로 작아졌기 때문에, 곧바로 더 많은 튜닝을 하기보다 bootstrap/row impact/segment impact를 먼저 확인해야 한다.

추천 다음 단계:

1. PP258 균형 후보를 최신 운영 후보로 둔다.
2. 기준선은 PP258 MAPE `0.2698881958`, p95 APE `0.8073247073`, repeated p95 win rate `0.788782`, replacement score `-0.0188296923`로 둔다.
3. PP252, PP246, PP228 공격형/균형 후보와 PP258을 같은 bootstrap split에서 비교한다.
4. PP258의 MAPE 개선분을 row별로 분해해 상위 기여 row와 손상 row를 확인한다.
5. `stable_price_band`, `confidence_tier`, `quantile_width`, `medium_support_bucket`, `artist_support_bucket`별로 PP258이 PP252보다 일관되게 이기는지 확인한다.
6. 감사 결과가 안정적이면 PP256 residual continuation 주변만 좁게 재탐색한다. 탐색 범위는 residual strength `0.015~0.035`, cap `0.00003~0.00006`, threshold `0.10~0.16` 정도로 제한한다.
7. 감사 결과가 특정 row 의존적이면 PP258은 최신 후보로 보류하고 PP252 균형 후보를 실운영 fallback으로 둔다.

추천 실험명:

```text
PP-OPT259~264 Warm PP258 significance and row-impact audit
```

예상 구조:

```text
1단계: bootstrap significance audit
  - PP258 vs PP252/PP246/PP228 후보의 bootstrap MAPE, p95 APE, replacement score 비교
  - 평균 개선뿐 아니라 win rate와 신뢰구간 확인

2단계: row impact audit
  - PP258 - PP252의 row별 APE 차이 계산
  - 개선분 상위 row와 손상분 상위 row를 분리
  - 특정 몇 개 row가 전체 개선을 대부분 만들면 과적합 위험으로 표시

3단계: segment impact audit
  - price band, confidence tier, quantile width, medium/support/artist support segment별 개선 방향 확인
  - PP258이 특정 segment에서만 이기면 해당 segment gate 후보를 다음 실험으로 분리

4단계: 다음 튜닝 여부 결정
  - 안정적이면 PP256 residual continuation local refinement
  - 불안정하면 PP252 fallback 유지
```

## 재시작 후 바로 확인할 파일

가장 먼저 아래 파일을 열면 된다.

```text
experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/reports/pp252_narrow_direction_residual_refinement_result.html
experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/reports/pp252_narrow_direction_residual_refinement_result.md
experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/artifacts/run_config.json
experiments/track6/PP-OPT247_252_warm_pp246_residual_direction_gated_correction/reports/pp246_residual_direction_gated_correction_result.html
experiments/track6/PP-OPT247_252_warm_pp246_residual_direction_gated_correction/reports/pp246_residual_direction_gated_correction_result.md
experiments/track6/PP-OPT247_252_warm_pp246_residual_direction_gated_correction/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT247_252_warm_pp246_residual_direction_gated_correction/artifacts/run_config.json
experiments/track6/PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration/reports/pp234_p95_constrained_support_and_basis_regeneration_result.html
experiments/track6/PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration/reports/pp234_p95_constrained_support_and_basis_regeneration_result.md
experiments/track6/PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration/artifacts/run_config.json
experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router/reports/pp234_significance_audit_and_learned_router_result.html
experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router/reports/pp234_significance_audit_and_learned_router_result.md
experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router/artifacts/run_config.json
experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router/artifacts/pp234_bootstrap_significance_audit.csv
experiments/track6/PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss/reports/pp228_p95_recovery_without_mape_loss_result.html
experiments/track6/PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss/reports/pp228_p95_recovery_without_mape_loss_result.md
experiments/track6/PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss/artifacts/run_config.json
experiments/track6/PP-OPT223_228_warm_pp222_narrow_balance_refinement/reports/pp222_narrow_balance_refinement_result.html
experiments/track6/PP-OPT223_228_warm_pp222_narrow_balance_refinement/reports/pp222_narrow_balance_refinement_result.md
experiments/track6/PP-OPT223_228_warm_pp222_narrow_balance_refinement/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT223_228_warm_pp222_narrow_balance_refinement/artifacts/run_config.json
experiments/track6/PP-OPT205_210_warm_pp204_local_winner_router_refinement/reports/pp204_local_winner_router_refinement_result.html
experiments/track6/PP-OPT205_210_warm_pp204_local_winner_router_refinement/reports/pp204_local_winner_router_refinement_result.md
experiments/track6/PP-OPT205_210_warm_pp204_local_winner_router_refinement/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT205_210_warm_pp204_local_winner_router_refinement/artifacts/run_config.json
experiments/track6/PP-OPT211_216_warm_pp210_p95_win_recovery_router/reports/pp210_p95_win_recovery_router_result.html
experiments/track6/PP-OPT211_216_warm_pp210_p95_win_recovery_router/reports/pp210_p95_win_recovery_router_result.md
experiments/track6/PP-OPT211_216_warm_pp210_p95_win_recovery_router/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT211_216_warm_pp210_p95_win_recovery_router/artifacts/run_config.json
experiments/track6/PP-OPT217_222_warm_p95_regularized_winner_rebuild/reports/p95_regularized_winner_rebuild_result.html
experiments/track6/PP-OPT217_222_warm_p95_regularized_winner_rebuild/reports/p95_regularized_winner_rebuild_result.md
experiments/track6/PP-OPT217_222_warm_p95_regularized_winner_rebuild/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT217_222_warm_p95_regularized_winner_rebuild/artifacts/run_config.json
experiments/track6/PP-OPT199_204_warm_pp192_pp198_winner_router/reports/pp192_pp198_winner_router_result.html
experiments/track6/PP-OPT199_204_warm_pp192_pp198_winner_router/reports/pp192_pp198_winner_router_result.md
experiments/track6/PP-OPT199_204_warm_pp192_pp198_winner_router/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT199_204_warm_pp192_pp198_winner_router/artifacts/run_config.json
experiments/track6/PP-OPT193_198_warm_segment_outcome_router_refinement/reports/segment_outcome_router_refinement_result.html
experiments/track6/PP-OPT193_198_warm_segment_outcome_router_refinement/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT193_198_warm_segment_outcome_router_refinement/artifacts/run_config.json
experiments/track6/PP-OPT187_192_warm_pp180_pp186_risk_router/reports/pp180_pp186_risk_router_result.html
experiments/track6/PP-OPT187_192_warm_pp180_pp186_risk_router/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT187_192_warm_pp180_pp186_risk_router/artifacts/run_config.json
experiments/track6/PP-OPT181_186_warm_huber_basis_p95_guard_refinement/reports/huber_basis_p95_guard_refinement_result.html
experiments/track6/PP-OPT181_186_warm_huber_basis_p95_guard_refinement/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT181_186_warm_huber_basis_p95_guard_refinement/artifacts/run_config.json
experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/reports/basis_generation_challenger_result.html
experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT173_180_warm_basis_generation_challenger/artifacts/basis_model_detail_aligned.csv
```

다음 실험 작성 시 참고할 스크립트:

```text
scripts/track6/run_pp_opt253_258_warm_pp252_narrow_direction_residual_refinement.py
scripts/track6/run_pp_opt247_252_warm_pp246_residual_direction_gated_correction.py
scripts/track6/run_pp_opt241_246_warm_pp234_p95_constrained_support_and_basis_regeneration.py
scripts/track6/run_pp_opt235_240_warm_pp234_significance_audit_and_learned_router.py
scripts/track6/run_pp_opt229_234_warm_pp228_p95_recovery_without_mape_loss.py
scripts/track6/run_pp_opt223_228_warm_pp222_narrow_balance_refinement.py
scripts/track6/run_pp_opt217_222_warm_p95_regularized_winner_rebuild.py
scripts/track6/run_pp_opt211_216_warm_pp210_p95_win_recovery_router.py
scripts/track6/run_pp_opt205_210_warm_pp204_local_winner_router_refinement.py
scripts/track6/run_pp_opt199_204_warm_pp192_pp198_winner_router.py
scripts/track6/run_pp_opt193_198_warm_segment_outcome_router_refinement.py
scripts/track6/run_pp_opt187_192_warm_pp180_pp186_risk_router.py
scripts/track6/run_pp_opt181_186_warm_huber_basis_p95_guard_refinement.py
scripts/track6/run_pp_opt173_180_warm_basis_generation_challenger.py
scripts/track6/run_pp_opt167_172_warm_pp166_second_stage_tail_calibration.py
scripts/track6/run_pp_opt161_166_warm_pp157_negative_gate_rollback.py
scripts/track6/run_pp_opt155_160_warm_strict_huber_gate.py
scripts/track6/run_pp_opt149_154_warm_huber_adoption_stabilization.py
```

## 재시작 후 첫 명령 후보

핵심 지표를 다시 확인하려면:

```bash
python3 - <<'PY'
import pandas as pd
p='experiments/track6/PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement/outputs/selected_stability_candidate_aggregate.csv'
df=pd.read_csv(p)
cols=['candidate','candidate_label','fixed_test_MAPE','fixed_test_p95_APE','avg_pp64_MAPE_win_rate','avg_pp64_p95_win_rate','replacement_score']
print(df.sort_values('replacement_score').head(20)[cols].to_string(index=False))
PY
```

다음 실험의 시작점은 PP258 균형 후보를 기준으로 유지하면서 PP259~264 significance/row-impact audit을 먼저 수행하는 것이다.
