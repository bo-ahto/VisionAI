# PP-CSRCH1 검색 delta 그룹 일반화 선행 검증 요약 (수집 없음)

- 실험 ID: `PP-CSRCH1` (Cold 로드맵 Phase 2-3a)
- 실행일: 2026-06-10
- 목적: PP-PCOLD1에서 신규 작가의 검색 lookup 커버리지 0.0이 확인됨에 따라, **수집 확대 없이** 기존 372작가 frozen delta를 작가 속성으로 일반화해 미커버 fallback(guard-only)을 대체할 수 있는지 검증.
- 스크립트: `scripts/track6/run_pp_csrch1_cold_search_delta_generalization.py`
- 폴더: `experiments/track6/PP-CSRCH1_cold_search_delta_generalization/`
- 비교 기준 = guard-only(현행 fallback), 상한 = true per-artist delta(v0.3). test는 작가 전원 미커버 가정(validation 작가로만 적합) 1회. 0604 미사용.

## 사전 발견: 검색 delta의 정체

- lookup delta 분포: **25/50/75 분위가 전부 -0.0313** — 사실상 "전역 하향 bias 보정 상수 + 소수 outlier"(|delta|>0.05인 작가 5.6%, cap ±0.2).
- 즉 v0.3 검색층의 상당 부분은 작가별 신호가 아니라 **Cold base의 전반적 과대예측에 대한 bias 보정**이다.

## 결과 (test, 미커버 시나리오, MdAPE/MAPE/p95)

| 후보 | MdAPE | MAPE | p95 | 검색층 이득 회수율 |
| --- | ---: | ---: | ---: | --- |
| guard-only (현행 fallback) | 0.4178 | 0.9640 | 2.5377 | — |
| **상수 delta(-0.0313) 적용** | 0.4262 | **0.9381** | **2.4287** | MAPE 22.5% / **p95 ~57%** |
| true per-artist delta (v0.3 상한) | 0.4098 | 0.8493 | 2.3465 | 100% |

- validation OOF: MAPE -0.0133 / p95 -0.0721 개선, MdAPE +0.0025 악화.
- artist 반복 holdout: **MAPE 개선확률 0.975~1.00, p95 0.985~1.00으로 강함. 그러나 MdAPE 비악화 확률 0.41~0.46 < 0.50 → 게이트 미통과.**
- **그룹/메타 후보(매체·가격대·저차원 Huber+작가메타)는 전부 상수와 동일한 예측으로 수렴** — 작가 속성으로는 per-artist delta를 전혀 설명하지 못함.

## 판정: 보류 (목적별 후보로만 유지)

- 상수 delta는 Warm에서 반복된 것과 같은 **center-vs-tail 트레이드오프**: MAPE/p95 방어는 강하고 재현적이지만 중앙(MdAPE)을 일관되게 조금 희생. 기본 fallback 교체는 게이트 기준 불가.
- 단, **"미커버 작가 + p95 방어 우선" 목적의 운영 옵션**으로는 근거가 강함(개선확률 0.99~1.00). v0.3 정책의 fallback을 "guard-only" → "guard + 상수 delta(p95 방어 모드)"로 바꾸는 선택지는 서비스 목적(큰 오차 회피)에 따라 채택 가능 — 의사결정 사항으로 이관.

## 수집 확대(Phase 2-3b)의 가치 정량화

이 실험의 가장 중요한 산출은 수집 의사결정 근거다:

- 상수만으로 회수: MAPE 이득의 22.5%, p95 이득의 ~57%.
- **나머지 MAPE 이득 77.5%는 outlier 작가(5.6%)의 per-artist delta에서 나옴** — 작가 속성으로 추정 불가(그룹 후보 전멸)이므로, 이를 얻는 유일한 방법은 신규 작가에 대한 실제 검색 수집이다.
- 즉 수집 확대의 기대 효과 = "미커버 작가 MAPE 0.9381 → 0.8493 방향" (단 수집 품질이 기존과 동일하다는 가정). cold 운영 트래픽 전망과 함께 판단할 것.

## 산출물

- `outputs/oof_candidate_metrics.csv`, `outputs/gate_results.csv`, `outputs/fixed_test_metrics.csv`
- `artifacts/run_config.json` (delta 분포 통계·게이트 정의 동결), `reports/result_report.md`

## 다음

- Phase 2 완료 (CCONF1 채택 권고 / CIMG1 기각 / CSRCH1a 보류+수집 가치 정량화).
- 의사결정 대기: ① 상수 delta를 미커버 p95 방어 모드로 운영 정책에 반영할지, ② 검색 수집 확대(2-3b) 착수 여부, ③ Phase 3(PP-CCORR, 보정 직교 결합) 진행 여부.
