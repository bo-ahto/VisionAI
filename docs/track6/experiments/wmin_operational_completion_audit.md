# WMIN Warm 운영 후보 완료 감사

- 작성일: 2026-06-13
- 범위: PP-WMIN5부터 PP-WMIN10까지의 Warm 개선 흐름, 운영 artifact 연결, API 재현 검증
- 기준 데이터: 기존 Warm validation OOF 519건, fixed test 607건, 0604 stress 829건, PP-WCUT4 저이력 leave-one-out 1,947건
- 결론: 5건 이상 Warm 경로는 `이력 기반 조건부 유사작품 보정 모델`을 운영 1순위 후보로 연결 완료

## 1. 최종 결론

- 최종 Warm 5건 이상 후보: `min1_route_w850_risk_q50_altlower_gap005`
- 운영 artifact: `models/track6/warm_wmin8_operational_candidate`
- exact runtime artifact: `models/track6/warm_wmin8_exact_runtime_candidate`
- official v0.1 라우팅:
  - 동일 작가 학습 가격 0건: Cold
  - 동일 작가 학습 가격 1~4건: Warm-lite
  - 동일 작가 학습 가격 5건 이상: Warm WMIN8
- 현재 blocking item: 없음
- API fixed-test parity: 607건 전부 통과

## 2. 성능 요약

| 후보 | fixed test n | MdAPE | MAPE | p95 APE | RMSE log | 판단 |
|---|---:|---:|---:|---:|---:|---|
| 기존 운영 기준 PP258 | 607 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | 교체 기준 |
| WMIN4 min1 Huber 기준 후보 | 607 | 0.106598 | 0.239302 | 0.779196 | 0.376884 | 중간 기준 |
| WMIN8 조건부 라우팅 최종 후보 | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 | 채택 |

- WMIN8은 PP258 대비 MdAPE, MAPE, p95 APE가 모두 개선됨
- WMIN8은 WMIN4 대비 MdAPE, MAPE, p95 APE가 모두 개선됨
- WMIN8은 RMSE log가 WMIN4보다 0.000306 높지만, 운영 목표였던 p95 tail 방어 개선 폭이 더 큼

## 3. 실험별 판단

| 단계 | 목적 | 핵심 결과 | 판단 |
|---|---|---|---|
| PP-WMIN5 | 0604 stress 안전성 확인 | WMIN4 min1 Huber MAPE 0.319691, p95 0.902571. PP258 proxy MAPE 0.377354, p95 0.987056 | 0604에서 PP258 대비 명확한 악화 없음. 다음 단계 진행 |
| PP-WMIN6 | min1 기준가에 EB shrinkage 결합 | 일부 MdAPE는 개선됐지만 p95가 WMIN4보다 악화 | 채택하지 않음 |
| PP-WMIN7 | SVC와 안정 후보의 가중 재탐색 | 높은 SVC 가중이 p95 개선 신호를 보임 | 단독 채택하지 않고 WMIN8 대안 후보로 사용 |
| PP-WMIN8 | 위험 구간 라우팅과 보정 스택 재구축 | fixed test 0.104326 / 0.235814 / 0.739416 | 최종 Warm 5건 이상 후보로 채택 |
| PP-WMIN8B | 추가 segment 보정 재진단 | 일부 fixed MAPE가 0.0002 수준 좋아졌지만 p95가 WMIN8보다 악화 | 운영 안정성 기준으로 보류 |
| PP-WMIN9 | WMIN8 운영 artifact와 라우팅 통합 감사 | decision status `candidate_artifact_connected_api_parity_passed` | 연결 완료 |
| PP-WMIN9B | 저이력 Warm-lite 경계 확인 | 1~4건 Warm-lite MAPE 0.2866 vs Cold 0.9946, 5건 이상 WMIN8 검증 유지 | 경계 유지 |
| PP-WMIN10 | official API fixed-test parity | 607건 성공, wrong route 0, wrong adapter 0, max abs log diff 5.33e-15 | API 재현 통과 |

## 4. 라우팅 정책 감사

| 입력 조건 | 운영 경로 | 근거 |
|---|---|---|
| 작가 매칭 불가 또는 동일 작가 학습 가격 0건 | Cold | Warm 계열의 동일 작가 이력 통계가 계산되지 않음 |
| 작가 매칭 점수 0.80 이상, 동일 작가 학습 가격 1~4건 | Warm-lite | PP-WCUT4 실존 저이력 leave-one-out 검증에서 Cold 대비 우세 |
| 작가 매칭 점수 0.80 이상, 동일 작가 학습 가격 5건 이상 | Warm WMIN8 | PP-WMIN8 fixed test와 PP-WMIN10 API parity 통과 |

- WMIN8을 1~4건 저이력 행에 강제로 적용하는 비교는 운영 판단 근거로 사용하지 않음
- 이유: WMIN8은 5건 이상 동일 작가 이력 경로로 선택된 모델이며, 1~4건 행에 강제 적용하면 학습 조건과 운영 라우팅 불변식을 깨는 비교가 됨

## 5. WMIN8 계산 개요

1. 동일 작가 및 유사 조건의 가격 이력으로 min1 기준 로그가격을 생성
2. 기준 후보를 계산
   - 식: `0.70 * SVC 기반 유사작품 로그가격 + 0.30 * PP-V8 안정 후보 로그가격`
   - 이후 Huber residual refit으로 작은 잔차 보정 적용
3. 방어 후보를 계산
   - 식: `0.85 * SVC 기반 유사작품 로그가격 + 0.15 * PP-V8 안정 후보 로그가격`
   - 이후 같은 Huber residual refit 구조 적용
4. 위험도 점수를 계산
   - 입력: quantile width, 모델 간 예측 spread, 현재 후보와 안정 후보의 gap, stable price band, confidence tier
5. 조건부 라우팅을 적용
   - 기본은 기준 후보 사용
   - 위험도 점수가 validation q50 이상이고 방어 후보가 기준 후보보다 0.005 log 이상 낮으면 방어 후보로 교체
6. 선택된 로그가격을 원화 가격으로 변환
   - 식: `예측가격(KRW) = exp(선택된 WMIN8 로그가격)`

## 6. 재현 검증

검증 명령:

```bash
python3 -m py_compile \
  scripts/track6/run_pp_wmin9_warm_route_integration.py \
  scripts/track6/run_pp_wmin9b_warm_lite_boundary_comparison.py

python3 scripts/track6/run_pp_wmin9_warm_route_integration.py
python3 scripts/track6/run_pp_wmin9b_warm_lite_boundary_comparison.py
python3 scripts/track6/run_pp_wmin10_warm_wmin8_api_fixed_test_parity.py --no-resume
python3 scripts/track6/verify_official_v0_1_warm_lite_api_routing.py --repeat 3
shasum -a 256 -c models/track6/warm_wmin8_operational_candidate/manifest/MANIFEST.sha256
```

검증 결과:

| 검증 | 결과 |
|---|---|
| WMIN9 readiness | blocking 0, decision status `candidate_artifact_connected_api_parity_passed` |
| WMIN9B route boundary | non-pass checks 0 |
| WMIN10 API parity | n 607, success 607, wrong route 0, wrong adapter 0 |
| WMIN10 max abs log diff | 5.3290705182007506e-15 |
| 반복 라우팅 검증 | Cold, Warm-lite 1건, Warm-lite 4건, Warm 5건 이상 모두 3회 반복 deterministic pass |
| manifest checksum | OK |

## 7. 후속 운영 감시 항목

- 작가 매칭 점수 분포
- 동일 작가 학습 가격 수 분포
- Warm-lite와 WMIN8 경로별 호출량
- WMIN8 route gate hit rate
- WMIN8 기본 후보와 방어 후보의 가격 차이
- 실거래 피드백 유입 후 경로별 MAPE, MdAPE, p95 APE

