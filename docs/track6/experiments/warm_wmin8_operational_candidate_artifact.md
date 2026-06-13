# PP-WMIN9 Warm 운영 라우팅 통합 검증

- 작성일: 2026-06-13T10:15:44+09:00
- 데이터 기준: WMIN8 산출물 + Warm-lite/routing policy 아티팩트 + official v0.1 서비스 코드
- 0604 사용: 없음
- 결론: `candidate_artifact_connected_api_parity_passed`
- 요약: WMIN8 후보 아티팩트, Warm-lite 경로, 0.80 매칭 임계값, 5건 이상 Warm 라우팅, 607건 API parity가 연결 완료 상태

## 1. 선택된 Warm 5건 이상 후보

- 문서용 모델명: 이력 기반 조건부 유사작품 보정 모델
- 내부 추적 ID: `WMIN8 conditional min1 SVC weight router`
- 선택 후보: `min1_route_w850_risk_q50_altlower_gap005`
- validation MdAPE/MAPE/p95: `0.094033 / 0.175114 / 0.571291`
- fixed test MdAPE/MAPE/p95: `0.104326 / 0.235814 / 0.739416`

## 2. WMIN8 라우팅 규칙

- 기본 후보: `min1_huber_refit_partial`
- 대안 후보: `min1_w850_huber_refit_partial`
- gate kind: `risk_ge_altlower_gap`
- risk threshold: `0.2534165869100283`
- alternative lower gap: `0.005`
- 적용 방식: 기본 후보를 사용하되, 위험도가 validation q50 이상이고 대안 후보가 기본 후보보다 0.005 log 이상 낮은 경우에만 대안 후보로 교체

## 3. Warm / Warm-lite / Cold 목표 라우팅

| history_count | current_official_v0_1_route | target_route_after_integration | target_artifact | condition |
|---|---|---|---|---|
| 0 | Cold | Cold | cold v0.3/v0.4 policy layer | match_score < 0.8 또는 usable_history = 0 |
| 1~4 | Warm-lite | Warm-lite | models/track6/warm_lite_v0.1 | match_score >= 0.8 AND 1 <= usable_history <= 4 |
| 5+ | Warm / WMIN8 exact adapter | Warm | models/track6/warm_wmin8_operational_candidate | match_score >= 0.8 AND usable_history >= 5 |

## 4. 준비 상태

- wmin8_outputs_exist: `True`
- wmin8_selected_candidate_packaged: `True`
- warm_lite_artifact_ready: `True`
- routing_policy_artifact_ready: `True`
- current_service_has_warm_5plus_route: `True`
- current_service_has_warm_lite_route: `True`
- current_service_mentions_wmin8: `True`
- current_service_threshold_matches_recommended_policy: `True`
- exact_raw_adapter_ready: `True`
- fixed_test_parity_through_api_ready: `True`

## 5. 남은 연결 작업

- 없음

## 6. 생성 파일

- 후보 아티팩트 manifest: `models/track6/warm_wmin8_operational_candidate/manifest.json`
- 후보 정책: `models/track6/warm_wmin8_operational_candidate/config/warm_model_policy_wmin8.json`
- 통합 검증 JSON: `experiments/track6/PP-WMIN9_warm_route_integration/outputs/readiness_checks.json`