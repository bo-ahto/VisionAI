# PP-PCOLD1 pseudo-cold 평가셋 구축 요약

- 실험 ID: `PP-PCOLD1` (Cold 로드맵 Phase 0.5)
- 실행일: 2026-06-10
- 목적: 0604가 Warm 시험 제출 전용으로 분리되면서 Cold에 외부 검증 축이 없다. train의 거래량 하위 작가를 작가 단위로 마스킹해 unseen-artist 상황을 시뮬레이션하는 pseudo-cold 평가셋을 구축한다.
- 스크립트: `scripts/track6/run_pp_pcold1_pseudo_cold_eval_set.py`
- 폴더: `experiments/track6/PP-PCOLD1_pseudo_cold_eval_set/`
- 용도 제한: **외부 검증 축으로만 사용. 후보/경계값 선택에 사용 금지.**

## 구성 방식

- 마스킹 풀: train 작가 중 행수 3~10인 작가. seed별 무작위 선택(목표 1,200행).
- seed 3개(20260610~12): 각 206~222작가 / 1,206~1,207행 마스킹, 잔여 train ~25,707행.
- 파이프라인: v0.2 search-free LGB Quantile(q10/q40/q50/q90)을 마스킹 train으로 재학습. guard 임계값은 v0.2 방식 그대로 real cold validation 예측의 label-free 분위수로 재산정.
- 한계: v0.3/PP-Y18 체인은 상류 search 피처 의존으로 pseudo-cold 재학습 불가 → 검색 lookup 커버리지만 감사.

## 핵심 결과 (seed 3개 평균 ± 표준편차, MdAPE/MAPE/p95)

| eval_set | defense_guard | representative_q50 |
| --- | --- | --- |
| **pseudo_cold** | 0.5772±0.009 / 1.1877±0.175 / 4.1654±1.525 | 0.5853 / 1.2742 / 4.3326 |
| real_cold_test (재학습 모델) | 0.4816±0.001 / 1.2081±0.018 / 3.9780±0.230 | 0.4835 / 1.2789 / 4.2442 |
| real_cold_validation (재학습 모델) | 0.3840 / 0.6227 / 1.6734 | 0.3905 / 0.6653 / 1.7842 |

### 발견 1: pseudo-cold는 real cold보다 어렵다 (레벨 비교 금지, delta 비교 전용)

- pseudo-cold MdAPE 0.577 vs real cold test 0.482 — 거래량 하위 작가는 개별성이 커서 더 어려움.
- seed 간 MAPE/p95 분산도 큼(±0.175/±1.525, tail 의존) → **후보 평가 시 절대 레벨이 아니라 같은 pseudo 셋에서의 base 대비 delta로, seed 3개 전부에서 방향 일치를 요구**하는 방식으로 사용한다.

### 발견 2: 신규 작가의 검색 lookup 커버리지 = 0.0

- 마스킹 작가(3 seed 합계 ~640명)가 v0.3 검색 delta lookup(372작가, cold split 작가로 동결)에 **한 명도 없음**.
- 즉 v0.3의 guard+search 방어 이점(test p95 -29%)은 **현 frozen snapshot 구조에서 진짜 신규 작가에게 전혀 전이되지 않고 100% guard-only fallback**이 된다.
- 시사점: Phase 2의 검색 커버리지 확대는 "있으면 좋은 것"이 아니라 **신규 작가 서빙 품질의 전제 조건**. 그 전까지 신규 작가의 실효 기준은 운영 base(v0.2) 또는 guard-only다.

### 보조 확인

- 작가 마스킹(약 1,200행 제거)이 real cold 성능에 주는 영향은 미미(재학습 test defense 0.4816 vs 전체 train v0.2 0.4852) — 평가셋 구축이 기준을 흔들지 않음.

## 선택 bias 감사

| set | n | 가격 중앙값(KRW) | 가격 q90 | log_area 중앙값 | top3 medium 비중 |
| --- | --- | --- | --- | --- | --- |
| pseudo_cold(전 seed) | 2,686 | 2,760,000 | 15,935,000 | 8.20 | 0.82 |
| real_cold_validation | 2,753 | 2,622,000 | 12,249,312 | 8.26 | 0.92 |
| real_cold_test | 3,099 | 3,450,000 | 20,087,280 | 8.39 | 0.86 |

- 가격대/크기/매체 구성은 real cold와 대체로 유사. 단 pseudo-cold는 저거래 작가 편향(의도된 설계)이므로 "신규 작가" 시나리오에 가깝고, real cold 고거래 작가 구성과는 다름을 전제로 해석.

## 산출물

- `outputs/pseudo_cold_rows.csv` — seed별 평가행(예측/qwidth/lookup 커버리지 포함)
- `outputs/pseudo_cold_metrics.csv`, `outputs/bias_audit.csv`
- `artifacts/run_config.json`, `reports/result_report.md`

## 다음 실험

- **PP-CDIAG1 (Phase 1)**: PP-CBASE1 고정 base 잔차를 validation 기준으로 구간 분해(가격대/매체/크기/qwidth/검색 delta 크기/작가 행수)해 Cold 위험 구간 확정.
