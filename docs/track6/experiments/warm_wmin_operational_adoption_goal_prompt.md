# Warm 사다리 min1 운영 반영용 Codex /goal 프롬프트

이 문서는 Codex `/goal`에 붙여넣어 PP-WMIN1(proxy 검증 통과)의 운영 반영
실험을 이어가기 위한 프롬프트다. 사용 방식: `/goal` 뒤에 아래 블록 전체를 붙여넣는다.

---

## /goal 프롬프트 (여기부터 복사)

목표: Warm 운영 파이프라인의 유사작품 매칭 사다리에서 작가 레벨(1~3순위)의
최소 표본을 5→1로 완화했을 때, Warm 전체 체인의 운영 성능이 개선되는지
검증하고 채택 여부를 판단한다.

배경 (PP-WMIN1, 2026-06-12 — `docs/track6/experiments/pp_wmin1_warm_ladder_min_relaxation_summary.md`):
- warm test 행의 41.2%가 최정밀 비교군(작가+재료/지지체+크기) 1~4건을 보유하나
  현행 min5에 걸려 거친 레벨로 fallback (PP-SVC8의 정밀 매칭률 40.7%와 일치)
- 선형 proxy(Huber 6구성+사다리 통계) 비교에서 min1이 게이트 통과:
  validation 0.1316/0.2336/0.7421 → 0.0932/0.1895/0.6322,
  artist-cluster bootstrap 1.0/1.0/0.98, fixed test 확인 0.1533→0.1087(-29%)
- min5→2→1 단조 개선 — 임계 제거(min1)가 최적. 소표본 분산 우려 기각
- 단 proxy 신호이므로 운영 svc 파이프라인 + 보정 스택에서의 재검증이 본 목표

기준 (변경 금지):
- 운영 1순위 비교 기준: 현행 Warm 운영 후보(PP258 계열,
  fixed test 607 기준 0.140976/0.269888/0.807325) 및 WBASE 평가 체계
  (validation OOF 519 + fixed test 607, repeated win rate + replacement score)
- WMIN proxy 참조: min1 proxy test 0.1087/0.2481/0.8378 (방향 상한 참고)

실험 단계 (PP-WMIN2부터 번호 부여, 각 단계 별도 실험 폴더):
1. PP-WMIN2 — svc 컴포넌트 재생성: `svc_numeric_seed_mean` 재현 파이프라인
   (`run_pp_svcshrink3_*` 계열 참조)에서 작가 사다리 min_n만 5→1로 변경해
   svc 컴포넌트를 다중 seed로 재생성. leakage 규칙 유지: train 내부 통계는
   자기 fold 제외 — **min1에서 fold 제외 후 그룹이 0건이 되면 다음 레벨로
   fallback** (자기 자신 1건짜리 그룹이 자기 가격을 보지 않도록 필수 확인).
   svc 단독 + 70:30 기준가 수준에서 현행 svc 대비 비교.
2. PP-WMIN3 — 70:30 기준가 교체 영향: 새 svc로 `current_70_30` 재계산,
   hcoef_stable 등 기존 안정 보정의 재적합 전/후 비교. validation OOF
   (row/artist 반복)로만 선택.
3. PP-WMIN4 — 보정 스택 재검증: 새 기준가 위에서 운영 후보 계열(PP148/166/
   PP258 decision layer)을 재적합하고 repeated win rate + replacement
   score로 현행 운영 1순위와 비교. fixed test는 최종 확인 1회.
4. 채택 판단: 전 단계 게이트 통과 시 운영 svc 교체안 + artifact 갱신안 제시,
   미통과 시 어느 층에서 신호가 소멸했는지 분해 보고.

금지 조건:
- fixed test로 후보/경계값 선택 금지(최종 확인 1회만). 보정/통계는 OOF로만
- 0604 라벨은 stress test 전용(선택 금지)
- min1 적용 시 자기가격 누설 점검을 1단계 산출물에 명시적으로 포함
  (fold-제외 후 그룹 크기 0 처리 검증)
- 결과 과장 금지: 게이트 미통과는 보류/기각으로 명시

산출물 기준:
- 실험별 전용 폴더 `experiments/track6/PP-WMIN<N>_<slug>/`
  (artifacts/run_config.json, outputs/*.csv, reports/result_report.md)
- `scripts/track6/run_pp_wmin<N>_*.py` 단일 실행 스크립트, 중간 산출물
  체크포인트(중단 시 재실행으로 재개)
- `docs/track6/experiments/pp_wmin<N>_*_summary.md` 요약 +
  `postprocessing_experiment_matrix.md` 갱신
- 종료 시 WARM 핸드오프 갱신 + 다음 실험 1개 제안

재시작 시 먼저 확인할 파일:
- docs/track6/experiments/pp_wmin1_warm_ladder_min_relaxation_summary.md
- scripts/track6/run_pp_wmin1_warm_ladder_min_relaxation.py (proxy 사다리 구현)
- experiments/track6/PP-WDOC1_warm_v01_four_model_training_logic/reports/
  warm_v01_final_model_base_correction_logic.md (사다리 7단 정의 §4.2)
- scripts/track6/run_pp_svcshrink3_warm_svc_numeric_shrunk_operational_decision.py
  (svc_numeric 전체 재현 파이프라인)

## (복사 끝)
