# PP-CCORR1 Cold 잔여 보정 직교 결합 요약

- 실험 ID: `PP-CCORR1` (Cold 로드맵 Phase 3)
- 실행일: 2026-06-10
- 목적: 연구 base(v0.3 guard+search)의 남은 잔차를 보수적 보정 2계열(저차원 Huber residual / CDIAG1 위험 구간 segment median)로 줄일 수 있는지, 기존 방어층과의 직교성 감사와 함께 검증.
- 스크립트: `scripts/track6/run_pp_ccorr1_cold_residual_orthogonal_correction.py`
- 폴더: `experiments/track6/PP-CCORR1_cold_residual_orthogonal_correction/`
- 제약: row-level router 금지(segment까지만), 0604 미사용, test 최종 1회.

## 설계

- 신호(정답 미사용): qwidth, 모델 gap, 검색 delta 크기, guard 발동, log_area, mixed_media
- segment: qwidth bin(4, val q33/q67/q90) × gap bin(2, val q50), min_rows 40
- 격자: cap {0.05/0.1/0.2} × strength {0.25/0.5/1.0} × 마스크(all/qwidth_high+/extreme)
- validation artist-grouped 5-fold OOF → (p95 비악화+MAPE 개선) 후보만 artist 반복 holdout 게이트 → fixed test

## 결과: 기각 — OOF 통과 후보 0개

- 전 격자에서 **validation OOF MAPE 개선 후보 0개** (최선이 +0.00205 악화). 게이트 진입·fixed test 보고 대상 없음.
- **신호 예측력**: OOF 보정값 vs 실제 잔차 상관 = Huber **-0.109**, segment median **-0.090** — 작가 경계를 넘으면 보정이 잔차를 *역예측*. CIMG1(0.06~0.08)보다도 나쁨.
- **직교성 감사**: 보정값과 guard 이동량 상관 **-0.31/-0.25** — 학습된 보정의 상당 부분이 새 정보가 아니라 **기존 guard 층을 되돌리려는 방향**. 검색 delta와의 상관도 0.08~0.15로 부분 중복. 즉 이 신호들(qwidth 등)이 가진 정보는 이미 guard/search/tier 층이 소진했고, 남은 잔차에는 현재 피처로 추출 가능한 구조가 없다.

## Phase 3 종결 결론

1. **Cold 점 예측의 추가 보정 경로는 현재 피처 집합에서 닫혔다.** Warm(HCOEF 35연속 기각)과 동일한 saturation 패턴이며, Cold는 보정 층이 2개(guard/search)뿐인데도 이미 잔차가 무구조 — 작가 일반화의 본질적 한계.
2. 남은 점 예측 개선 경로는 **새 정보뿐**: ① 검색 수집 확대(PP-CSRCH1에서 가치 정량화: 미커버 MAPE 0.938→0.849 방향), ② 거래 시점 등 신규 데이터 과제(로드맵 §3 비고).
3. 운영 관점 현 상태가 Cold의 합리적 종착점: **v0.3(점 예측) + v0.4(신뢰도 tier/표시/2단 검수 + 미커버 상수 fallback 활성)**. 추가 트래픽/데이터 확보 전까지 Cold 실험 트랙은 휴면 권고.

## 산출물

- `outputs/oof_candidate_metrics.csv`, `outputs/gate_results.csv`(빈 결과), `outputs/fixed_test_metrics.csv`
- `artifacts/run_config.json` (동결 경계·직교성 감사 수치), `reports/result_report.md`
