# PP-CCORR2 Warm식 모델 특성 보정의 Cold 이식 검증 요약

- 실험 ID: `PP-CCORR2` / 실행일: 2026-06-10
- 질문: Warm에서 성과를 낸 "모델 특성 활용 보정"(V2식 다중 후보 meta-stack, PP148식 위험 구간 제한 라우팅)이 Cold에서도 가능한가? (PP-Y11 meta는 구형 후보 pool 대상 보류 — 현행 v0.3 체인 후보 대상은 미검증이었음)
- 스크립트: `scripts/track6/run_pp_ccorr2_cold_model_characteristic_correction.py` / 폴더: `experiments/track6/PP-CCORR2_cold_model_characteristic_correction/`
- 설계: 후보 6종(y2/y18/guard/research/v02_rep/v02_def) + 합의도(평균·표준편차·범위) + qwidth → ① Huber meta(후보 범위 ±0.03 clip, 블렌드 w 0.25/0.5/1.0) ② 위험 구간(qwidth_extreme/gap_extreme) 한정 대안 후보 라우팅(w 0.25/0.5). validation artist-grouped OOF 선택 → artist holdout 게이트 → fixed test 1회. 0604 미사용.

## 결과: 기각 — 게이트 진입 후보 0

- **결정적 감사**: V2식 meta의 OOF 예측력(actual_log 상관 **0.824**)이 **research base 단독(0.844)보다 낮음** — 작가 경계를 넘으면 후보 조합이 최강 단일 체인을 이기지 못함.
- 라우팅: 전 격자 validation MAPE 악화(최선 +0.0003). p95만 미세 개선하는 후보(qwidth_extreme→v02_def w0.25/0.5, dp95 -0.009/-0.019) 있으나 MAPE 악화 + 미검증으로 채택 불가.
- fixed test 보고 대상 없음 (base 0.4098/0.8493/2.3465 유지).

## 해석: Warm과 Cold의 구조적 차이

Warm의 V2 meta·PP148 router가 작동한 전제는 **다양한 계열의 개별적으로 강한 후보들**(svc 통계 Huber, L10 quantile 체인, D4/R5 등)이 있어 의견차 자체가 정보였다는 것. Cold의 후보들은 같은 피처 집합·같은 계열(LGB Quantile 변형)에서 나와 상관이 높고, 최강 체인(guard+search)이 이미 지배적이라 조합·라우팅이 더할 정보가 없다. **"모델 특성 보정"은 후보 다양성이 전제 조건이며, Cold는 그 전제가 성립하지 않음** — 이 역시 새 정보(수집)로만 깨지는 제약.

## 산출물

`outputs/oof_candidate_metrics.csv`, `gate_results.csv`, `fixed_test_metrics.csv`, `artifacts/run_config.json`, `reports/result_report.md`
