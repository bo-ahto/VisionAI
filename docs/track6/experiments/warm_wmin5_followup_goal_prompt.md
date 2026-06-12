# Warm min1 후속 개선용 Codex /goal 프롬프트 (PP-WMIN5~)

PP-WMIN2~4 완주(채택 후보 `min1_huber_refit_partial`) 이후의 후속 작업용.
사용 방식: Codex `/goal` 뒤에 아래 블록 전체를 붙여넣는다.

---

## /goal 프롬프트 (여기부터 복사)

목표: PP-WMIN4 채택 후보(`min1_huber_refit_partial`)의 0604 stress 안전성을
확인한 뒤, min1 기준가 위에서 남은 개선 여지(EB shrinkage 결합, 70:30 가중
재탐색, 보정 스택 재구축, Warm-lite 통합)를 검증하고 운영 artifact 교체안을
확정한다.

현재 상태 (2026-06-12, PP-WMIN2~4 완료):
- 채택 후보 `min1_huber_refit_partial`: validation OOF 0.1016/0.1784/0.5713,
  artist holdout 260회 win rate 1.000/0.988/0.988, replacement score -0.027,
  fixed test 확인 0.1066/0.2393/0.7792 (현행 PP258 0.1410/0.2699/0.8073 대비
  MdAPE -24%/MAPE -11%/p95 -3.5%)
- **미수행 항목: 0604 stress test** — min1은 정밀 매칭 비중을 41%p 올리는
  변경이라 prior staleness 민감도가 커질 수 있음(PP-SVC8의 svc 0604 악화
  전례). 운영 교체 확정 전 필수 확인.
- 잔여 타겟: p95가 -3.5%로 가장 덜 개선됨 — min1 소표본(1~4건) 그룹의
  tail 분산이 원인 후보

기준 (변경 금지):
- 비교 기준 1: 현행 운영 PP258 (fixed test 0.140976/0.269888/0.807325)
- 비교 기준 2: PP-WMIN4 채택 후보 (fixed test 0.1066/0.2393/0.7792) —
  이후 모든 후보는 이 둘 모두와 비교
- 평가 체계: validation OOF 519 + fixed test 607, repeated win rate +
  replacement score (WBASE 체계 유지)

실험 단계 (각 단계 별도 실험 폴더, 순서 준수):
1. PP-WMIN5 — **0604 stress 확인 (필수 선행)**: 채택 후보와 PP258을 0604
   신규라벨 829건에서 비교. 0604는 선택 기준이 아니라 안전 확인 전용 —
   채택 후보가 0604에서 PP258 대비 명확히 악화하면(특히 p95) 채택을
   보류하고 악화 원인을 정밀 매칭 staleness 관점에서 분해. 0604 비악화
   확인 시에만 2단계 이후 진행.
2. PP-WMIN6 — min1 × EB shrinkage 결합: SVCSHRINK1~3(조건부 채택)의
   shrunk median을 min1 사다리의 소표본(1~4건) 그룹에 적용 — 1~4건 그룹
   중앙값을 상위 레벨로 EB 수축해 tail 분산 제어. 목표 지표는 p95
   (validation OOF 선택, p95 win rate 중심 + MdAPE/MAPE 비악화 게이트).
   참조: run_pp_svcshrink1/2/3 스크립트.
3. PP-WMIN7 — 70:30 가중 재탐색: min1 기준가에서 svc 가중 grid
   (0.60~0.90, 0.025 step). 0.70은 min5 기준 최적이었음(PP-SVC6에서
   0.725~0.875 신호). PP-SVC4식 반복 holdout으로 선택.
4. PP-WMIN8 — min1 잔차 재진단 + 보정 스택 재구축: 새 잔차의 위험 구간을
   HCOEF23 방법론(구간 분해 + 잔차 계수 감사)으로 재진단하고, 그 구간을
   노리는 라우터/게이트 후보를 PP148/166 방식으로 탐색. WMIN4는 기존
   layer 재적합만 했으므로 신규 탐색 여지가 있음.
5. PP-WMIN9 — Warm-lite 통합 검토: 이력 1~4건 작가가 min1 본체 체인
   (PPV8 blend 포함)을 탈 때와 warm_lite_v0.1(경량 Huber)을 탈 때를
   실존 저이력 평가셋(PP-WCUT4 leave-one-out 설계 재사용)에서 비교 —
   본체 우위면 라우팅 단순화안 제시.
6. 최종: 통과 후보들을 결합한 운영 svc 교체안 + Warm artifact 갱신안
   (동결 스크립트 + 재현 검증 + 정책 JSON) 제시.

금지 조건:
- fixed test로 후보/경계값 선택 금지(최종 확인 1회만). 보정/통계는 OOF로만
- 0604는 stress/안전 확인 전용 — 후보 선택에 사용 금지
- min1 소표본 그룹의 fold-제외 후 0건 fallback 규칙 유지(WMIN2 점검 방식)
- 결과 과장 금지: 게이트 미통과는 보류/기각 명시. 기대치 관리: MdAPE는
  한계수익 체감 구간(val-test gap 작음) — p95가 주 타겟

산출물 기준:
- 실험별 전용 폴더 experiments/track6/PP-WMIN<N>_<slug>/
  (artifacts/run_config.json, outputs/*.csv, reports/result_report.md)
- scripts/track6/run_pp_wmin<N>_*.py 단일 실행 스크립트 + 체크포인트
  (중단 시 재실행으로 재개)
- docs/track6/experiments/pp_wmin<N>_*_summary.md +
  postprocessing_experiment_matrix.md 갱신
- 종료 시 WARM 핸드오프 갱신 + WMIN2~4 미커밋 산출물 포함 라인별 커밋

재시작 시 먼저 확인할 파일:
- docs/track6/experiments/pp_wmin4_warm_min1_operational_decision_summary.md
- experiments/track6/PP-WMIN4_warm_min1_operational_decision/outputs/
- scripts/track6/run_pp_svcshrink1_warm_comparable_prior_shrinkage.py (EB 수축)
- scripts/track6/run_pp_svcshrink3_warm_svc_numeric_shrunk_operational_decision.py
  (0604 로딩 함수 load_0604 포함)
- docs/track6/experiments/pp_hcoef13... 계열 (잔차 진단 방법론)
- models/track6/warm_lite_v0.1/ (5단계 비교 대상)

## (복사 끝)
