# Comprehensive Status Report — Track 1 + Track 2 + Archive Cycle (2026-05-08)

> **본 문서 성격**: archive cycle (`feature/gallery-tier-v4-research`) 의 **최종 관문 문서** + 트랙 1 (운영 main 모델) / 트랙 2 (cold-start 해석 가능 모델 연구) / v3.6 production server bundle / archive cycle decisions 종합 view.
> **Owner**: 의사결정자 / 운영팀 / 외부 보고 inheriting.
> **Authority**: 본 문서 = **결론 + 포인터** (canonical evidence 는 anchor 문서 reference). 본문 재서술 X / 새 주장 X.
> **연계**: HTML executive summary = `docs/comprehensive_status_report_20260508.html`.

## 1. Executive Summary (1 page)

| 영역 | 상태 | 근거 anchor |
|---|---|---|
| **Track 1 (운영 main 모델)** | ✅ **운영 기준선 유지 / cycle closed** — `v3_filtered_tuned` 32f 변경 X | [track1_phase0_closeout_20260507.md](track1_phase0_closeout_20260507.md) |
| **Track 2 (cold-start 해석 가능 모델 연구)** | ✅ **Architecture-only close 확정** (Stage 6B + Axis A 5 step 종결) / **일반 warm path 운영 미승인** / **Slice-conditional (depth ≥25) 제한 후보 + Phase A shadow 1주 착수 승인 가능** | [stage6b_results_20260507.md](stage6b_results_20260507.md) §종결 / [트랙2_종합보고서_axis_a_종결_20260507.html](트랙2_종합보고서_axis_a_종결_20260507.html) §결론 / [트랙2_README.md](트랙2_README.md) §99 (Phase A shadow) |
| **v3.6 production server bundle** | 🟡 **main 적재 / swap blocked** — code/monitoring/ETL ready, swap target artifact bundle 부재 + 운영 환경 prerequisite 미충족 | [v3_6_swap_readiness_report_20260508.md](v3_6_swap_readiness_report_20260508.md) |
| **archive cycle** | ✅ **closed + retained** — PR 16건 merged (#27~#42 분할 train + 잔존) + 본 PR (TBD) / frozen branch + tag / 잔존 작업 1-5 완료 / 잔존 6 LLM 영역 종결 | [archive closeout](archive/2026-05-08-gallery-tier-v4-research-closeout.md) (#27-#33) + 잔존 1-5 (#34-#40) + 잔존 6 (#41-#42) |
| **사전등록 governance** | ✅ **도입 cycle 정상 작동** — Track 1 fail-and-close / Track 2 architecture close 확정 / HARK 위험 실질적 저감 | [methodology_deviation_log.md](methodology_deviation_log.md) |

**한 줄 요약**: 운영 main 모델 (`v3_filtered_tuned` 32f) **그대로 유지**, 트랙 2 Architecture-only close 확정 (일반 warm 경로 운영 미승인 / Slice-conditional 제한 후보 + Phase A shadow 1주 착수 승인 가능), v3.6 server bundle main 적재 + swap **blocked** (사용자 권한 영역), archive cycle 정상 종결.

## 2. Track 1 — 운영 main 모델 사전등록 cycle

### 2.1 결정

**Option A cycle closed** (사용자 결정 / 코덱스 권고대로) — Phase 0 §4 fail trigger 정상 종결.

### 2.2 핵심 사실

- **운영 spec §1-§16 변경 X** / `v3_filtered_tuned` 32f 운영 그대로 유지
- **Audit 4 결과**: Overall Ensemble +0.70%p / Saatchi +1.80%p 악화 (Hard gate 2 violation)
- **Stage 1B / Stage 2 / Stage 3 / Stage 4 confirmatory holdout 모두 미진입** (confirmatory evidence 0건)
- **Stage 4 holdout 미봉인** (future winner 정해진 뒤에만)
- **A.2 path** (서빙 측 actual value 추출 / API contract 확장) = 별도 후속 path

### 2.3 핵심 finding (코덱스 P1 톤)

drift features 9개 중 7 (severe) 가 학습 분포 OOF 에서 **유의미한 예측 기여 (informative signal) 임을 강하게 시사** (특히 Saatchi slice). 서빙 시 hardcoded 0 = production 시 학습된 informative weight 무효화 가능 → reported offline metric (calibrated 38.3% cold) 이 actual serving behavior 보다 **낙관적일 가능성을 강하게 시사** (단정 X).

### 2.4 근거 anchor

- [track1_phase0_freeze_20260507.md](track1_phase0_freeze_20260507.md) — Phase 0 mini-prereg
- [track1_stage1_results_20260507.md](track1_stage1_results_20260507.md) — feature integrity audit
- [track1_amendment_drift_fix_20260507.md](track1_amendment_drift_fix_20260507.md) — fix set freeze
- [track1_audit4_results_20260507.md](track1_audit4_results_20260507.md) — FAIL trigger
- [track1_phase0_closeout_20260507.md](track1_phase0_closeout_20260507.md) — Option A closed decision artifact
- [트랙1_종합보고서_20260507.html](트랙1_종합보고서_20260507.html) — 외부 보고용 10 sections

## 3. Track 2 — cold-start 해석 가능 모델 연구 트랙

### 3.1 결정

**Architecture-only close 확정** — fixed-feature cold-start LAO scope 의 architecture-only remedies 가 1차 병목 해결 X 입증.

### 3.2 핵심 사실

- **3-cycle empirical** (Stage 4 단기 트랙 / Stage 6A / Stage 6B) + **1-cycle acquisition infeasibility** (Stage 5)
- **Stage 6A**: Segmented architecture FAIL (Hard gate 저가 harm 위반)
- **Stage 6B**: Partial pooling -0.09%p (사실상 동등) + 저가 +1.29%p hard gate 위반
- **Stage 5**: 4 source 중 Artsy CV 만 BORDERLINE PASS-ready / F1 (auction anchor) family 실현 가능성 X
- **Feature Track Axis A.1-A.5**: 모두 hard gate 통과 X (BORDERLINE 2건 + FAIL 3건) — fixed-feature + cheap-feature-only remedies 의 1차 병목 해결 X 입증
- **운영 영향 X**: Spec §17 변경 X / 운영 모델 유지 / 분기 B 그대로 진행
- **Axis B (license-first lane)**: Phase A HOLD — LLM 외 영역 (운영팀 / 법무팀 / 외부 source 회신 대기)

### 3.3 진행 cycle 종합

| Cycle | 결과 | 분류 |
|---|---|---|
| Stage 2 freeze (2026-05-06) | 5 family 확정 | 본질 |
| Stage 3 (Huber + spline + warm-start P3 + Holm 보정) | exploratory PASS | 정상 흐름 |
| Stage 4 v3 (Artsy 8,891 cleansed / 823 작가) | BORDERLINE 보류 / warm not advanced | major (사용자 지적 후 정정) |
| Stage 5 (External Acquisition) | 4 source REJECT + Artsy CV 1 BORDERLINE / acquisition infeasibility | major |
| Stage 6A (segmented) | FAIL — Hard gate 저가 harm | none |
| Stage 6B (partial pooling) | FAIL — 사실상 동등 + Hard gate | none |
| **Architecture-only close 확정** | 1차 병목 해결 X 입증 | 확정 |
| Feature Track Axis A.1-A.5 | hard gate 통과 X (BORDERLINE 2 + FAIL 3) | 정상 흐름 |
| Sample size sensitivity | descriptive analysis (운영 baseline stability) | 정상 흐름 |
| Progressive sampling | Stage 2 HOLD / 본 cycle 종결 | 정상 흐름 |
| Axis B Round 1-3 | Phase A HOLD (LLM 외 영역) | 정상 흐름 |

### 3.4 근거 anchor

- [트랙2_README.md](트랙2_README.md) — 트랙 2 인덱스 / 상태
- [트랙2_methodology_pipeline_20260507.md](트랙2_methodology_pipeline_20260507.md) — methodology
- [트랙2_production_통합_spec_20260507.md](트랙2_production_통합_spec_20260507.md) — production spec
- [트랙2_종합대시보드_20260507.html](트랙2_종합대시보드_20260507.html) — 종합 대시보드
- [트랙2_종합보고서_axis_a_종결_20260507.html](트랙2_종합보고서_axis_a_종결_20260507.html) — Axis A 종결
- [트랙2_종합보고서_axis_b_phase_a_round3_20260507.html](트랙2_종합보고서_axis_b_phase_a_round3_20260507.html) — Axis B Round 3

## 4. v3.6 Production Server Bundle (PR #27)

### 4.1 적재 상태

✅ **main 적재 완료** — FastAPI cohort gating + monitoring (Grafana 12 panel + 6 alert + Slack/PagerDuty alerting + Prometheus exporter) + ETL (PostgreSQL `predict_logs` schema + 5min cron) + drift scenarios playbook (6 markdown) + Phase 3 pre-rollout DEV TEST + STAGING runbook.

### 4.2 Swap 판정

🟡 **Blocked** — LLM 영역 검증 통과 / 사용자 영역 prerequisite 미충족.

| 항목 | 상태 |
|---|---|
| DEV TEST 실행 | ✅ PASS (fallback_cases_fail=0 / gating_correctness=1.0 / passed=true) |
| Baseline artifact bundle (`integrated_v3_filtered_tuned`, 5 file) | ✅ 모두 존재 + 로더 통과 |
| **Swap target artifact bundle** (`v3_5_v_year_saatchi_warm`, 5 file) | ❌ **모두 부재** |
| 운영 환경 prerequisite (psycopg / DB schema / monitoring wiring / secrets) | ⚠️ 미검증 (LLM 영역 외) |

### 4.3 사용자 권한 영역

본 archive cycle 의 LLM 가능 모든 작업 종결 후 남은 영역:
- Swap target artifact bundle 학습 + 적재 (P0 Blocker)
- 운영 환경 의존성 + DB schema + monitoring wiring + secrets (LLM 절대 비권한)
- STAGING 24h baseline → Pre-canary smoke → CANARY 1% → ROLLOUT 5% → 25% → FULL 100% (state machine 권위)
- Reviewer 1+2+3 signoff (D7 판정 시점 의무)
- Rollback 권한 (oncall)

### 4.4 근거 anchor

- [v3_6_swap_readiness_report_20260508.md](v3_6_swap_readiness_report_20260508.md) — Blocked 판정 + LLM 영역 evidence
- [v3_6_swap_user_action_checklist_20260508.md](v3_6_swap_user_action_checklist_20260508.md) — 사용자 권한 영역 standalone view (11 step + reviewer signoff matrix + rollback 환경별 명령)
- [v3_6_phase3_runbook.md](v3_6_phase3_runbook.md) — state machine 권위
- [v3_5_step4_drift_monitoring.md](v3_5_step4_drift_monitoring.md) — drift state machine
- [monitoring/playbooks/](../monitoring/playbooks/) — 6 drift scenario playbook (권위 대응)

## 5. Archive Cycle Decisions (PR 16건)

### 5.1 분할 PR train (Wave 1-3 + follow-up + 잔존 작업)

| Wave / 잔존 | PR | 본질 | 상태 |
|---|---|---|---|
| Wave 1 | #27 | v3.6 production server bundle | ✅ MERGED |
| Wave 1 | #28 | Track 1 Phase 0 closeout (governance only) | ✅ MERGED |
| Wave 2 | #29 | Track 2 core (Stage 2-6 + Architecture close + curated dataset) | ✅ MERGED |
| Wave 2 | #32 | Track 2 core bug fix (Stage 2 results + structural_pricing root + .gitignore) | ✅ MERGED |
| Wave 2 | #30 | Track 2 extensions (Feature Track Axis A.1-A.5 + Sample size + Progressive) | ✅ MERGED |
| Wave 2 | #31 | Axis B docs (Phase A pre-screen Round 1-3 + handoff packet) | ✅ MERGED |
| Wave 3 | #33 | Archive closeout note | ✅ MERGED |
| follow-up | #34 | repo hygiene + canonical asset adoption | ✅ MERGED |
| 잔존 1 | #35 | model_technical_report v2 anchor (PR #25 superseded) | ✅ MERGED |
| 잔존 2-A | #36 | deviation log Progressive + Sample size entries | ✅ MERGED |
| 잔존 2-B | #37 | deviation log Track 2 + Axis B + Feature Track + Stage 5 entries | ✅ MERGED |
| 잔존 3 | #38 | salvage `_v5_eval_framework.py` (archive-derived utility) | ✅ MERGED |
| 잔존 4 | #39 | salvage saatchi tests (regression label) | ✅ MERGED |
| 잔존 5 | #40 | archive retention policy §6 보강 | ✅ MERGED |
| 잔존 6 LLM | #41 | v3.6 swap readiness report (Blocked 판정) | ✅ MERGED |
| 잔존 6 split | #42 | v3.6 swap user action checklist (사용자 권한 영역 standalone) | ✅ MERGED |
| **(본 PR)** | TBD | Comprehensive status report (Track 1+2 통합 view) | ⏳ |

**Total**: 16 PR merged (#27~#42 archive train + 잔존 작업) + **본 PR (TBD, comprehensive status report)** / 230+ files / +52,000+ lines main 적재 (본 PR merge 후 확정).

### 5.2 Frozen archive

- **Branch**: `feature/gallery-tier-v4-research` — origin 그대로 보존 / rename X
- **Tag**: `archive/gallery-tier-v4-research-20260508` (HEAD `52ac44d`) — origin push 완료
- **Retention policy** (§6.1 archive closeout note): 최소 2026-05-22 보존 / cleanup review = 다음 cycle kickoff 또는 swap 방향 확정 후 / final deletion = 사용자 explicit 결정 (LLM 단독 X)

### 5.3 코덱스 자문 누적

| 차수 | 누적 |
|---|---|
| Track 2 cycle (Stage 2-6 + Axis A + Axis B + Progressive 등) | P0×17 + P1×80 + P2×40 |
| Track 1 cycle (Phase 0 + Stage 1 + Amendment + Audit 4 + closeout) | P0×12 + P1×14 + P2×10 |
| Archive cycle (Step 1-6 + 잔존 1-6 + comprehensive status) | P0×다수 + P1×다수 + P2×다수 (각 PR 별 사후 검수) |

## 6. 사전등록 Governance 도입 가치

### 6.1 본 archive cycle 의 governance signal

- **Track 1 fail-and-close 정상 작동**: drift fix path 의 OOF 개선 가설을 사전 freeze 후 평가 → 결과 반증 (악화) → Stage 1B 이상으로 decision drift 없이 종결
- **Track 2 Architecture-only close**: 3-cycle empirical + 1-cycle acquisition infeasibility / fixed-feature scope architecture-only remedy 의 1차 병목 해결 X 입증
- **HARK 위험 실질적 저감**: 사전등록 없이 결과 본 후 합리화 시 "fail / borderline 을 PASS 로 framing" risk → 본 cycle 은 정직 보고
- **운영 영향 분리**: decision-binding ≠ exploratory / production trigger 자격 X
- **운영 swap 안전선**: LLM 영역 evidence (readiness report) ↔ 사용자 영역 (user action checklist) 명확 분리 / authority boundary 명시

### 6.2 운영 적용 reference

- [트랙2_methodology_pipeline_20260507.md](트랙2_methodology_pipeline_20260507.md) — methodology pipeline (트랙 1 으로 이식 시 base)
- [methodology_deviation_log.md](methodology_deviation_log.md) — governance 누적 차이 기록 (Phase 1 종료 + Track 1 + Phase 1→2 전이 + Track 2 + Axis B + Progressive + Sample size 모든 entries)

## 7. Open Items + Authority Boundary

### 7.1 LLM 가능 영역 (모두 종결)

✅ archive cycle 의 모든 LLM 가능 작업 완료.

### 7.2 사용자 권한 영역 (open)

| 항목 | 영역 | 의사결정자 |
|---|---|---|
| **v3.6 swap target artifact bundle 학습 + 적재** | 학습 pipeline 수동 실행 | DevOps / 운영팀 |
| **v3.6 운영 환경 prerequisite 충족** | psycopg / PostgreSQL / Grafana wiring / secrets | DevOps / 운영팀 |
| **STAGING → Pre-canary → CANARY → ROLLOUT 실행** | state machine 권위 (v3_6_phase3_runbook §5) | 운영팀 + reviewer 1+2+3 signoff |
| **Final swap (DEFAULT_VARIANT 변경)** | governance rule (별도 PR) | 사용자 + reviewer signoff |
| **Rollback 결정 (긴급 운영)** | drift / regression 감지 시 | oncall / 운영팀 |
| **archive branch cleanup (2026-05-22 이후)** | retention policy §6.1 | 사용자 explicit 결정 |
| **외부 공유 산출물 처리** (심사위원 / 콜론30 / 정부 R&D 등) | 별도 archive lane / external-share 결정 | 사용자 |
| **A.2 path (Track 1 후속)** | 운영팀 inquiry / API contract 확장 feasibility | 운영팀 (LLM 외 영역) |
| **Axis B Phase A HOLD 해제** | 외부 source 회신 / 법무팀 검토 | 운영팀 + 법무팀 |

### 7.3 후속 cycle 진입 조건

새 cycle 진입 시 의무:
- 새 baseline / 새 hypothesis family 의 새 prereg cycle (same-cycle 재개 금지)
- Stage 4 confirmatory holdout 봉인 = future winner 정해진 뒤에만
- 별개 axis (HP tuning / ensemble redesign) = feature contract 안정화 후에만
- 새 mini-prereg + freeze + amendment 절차 의무

## 8. Reference Index

### 8.1 트랙 1
- [Phase 0 mini-prereg freeze](track1_phase0_freeze_20260507.md)
- [Stage 1 audit results v3](track1_stage1_results_20260507.md)
- [Drift fix amendment memo](track1_amendment_drift_fix_20260507.md)
- [Audit 4 OOF rerun results](track1_audit4_results_20260507.md)
- [Phase 0 Closeout Note (Option A)](track1_phase0_closeout_20260507.md)
- [트랙 1 종합 보고서 HTML](트랙1_종합보고서_20260507.html)

### 8.2 트랙 2
- [트랙 2 README](트랙2_README.md)
- [Stage 2 freeze (2026-05-06)](트랙2_Stage2_freeze_20260506.md)
- [Methodology pipeline](트랙2_methodology_pipeline_20260507.md)
- [Production 통합 spec](트랙2_production_통합_spec_20260507.md)
- [트랙 2 종합 대시보드](트랙2_종합대시보드_20260507.html)
- [트랙 2 종합 보고서 — Axis A 종결](트랙2_종합보고서_axis_a_종결_20260507.html)
- [트랙 2 종합 보고서 — Axis B Phase A Round 3](트랙2_종합보고서_axis_b_phase_a_round3_20260507.html)
- [Stage 3 exploratory addendum](stage3_exploratory_addendum_20260507.md) / [Stage 3 quantile cycle](stage3_quantile_cycle_20260507.md)
- [Stage 4 확장검증계획](stage4_확장검증계획_20260507.md) / [Stage 4 short-term track results](stage4_short_term_track_results_20260507.md) / [Stage 4 warm validation results](stage4_warm_validation_results_20260507.md) / [Stage 4 low-price decomp prereg](stage4_low_price_decomp_prereg_20260507.md)
- [Stage 5A acquisition prereg](stage5a_acquisition_prereg_20260507.md) / [Stage 5A source scorecard](stage5a_source_scorecard_20260507.md) / [Stage 5A week 2 results](stage5a_week2_results_20260507.md) / [Stage 5A week 3 decision memo](stage5a_week3_decision_memo_20260507.md) / [Stage 5C modeling prereg](stage5c_modeling_prereg_20260507.md)
- [Stage 6 prereg draft](stage6_prereg_draft_20260507.md) / [Stage 6A segmented prereg](stage6a_segmented_prereg_20260507.md) / [Stage 6A results](stage6a_results_20260507.md) / [Stage 6B partial pooling prereg](stage6b_partial_pooling_prereg_20260507.md) / [Stage 6B results](stage6b_results_20260507.md)

### 8.3 v3.6 production server bundle
- [v3.6 Plan](v3_6_plan.md)
- [v3.6 Phase 3 Runbook](v3_6_phase3_runbook.md) — **state machine 권위**
- [v3.6 Summary Report MD](v3_6_summary_report.md)
- [v3.6 Summary Report HTML](v3_6_summary_report.html)
- [Cold rollout shadow runbook](cold_rollout_shadow_runbook_20260507.md) — Track 2 영역 (v3.6 swap 권위 X)
- [Phase A monitoring spec](phase_a_monitoring_spec_20260507.md)
- [Swap Readiness Report](v3_6_swap_readiness_report_20260508.md) — Blocked 판정
- [Swap User Action Checklist](v3_6_swap_user_action_checklist_20260508.md) — 사용자 권한 영역 standalone
- [API Reference HTML](api_reference.html) — `/api/v1/model/info` / `/api/v1/monitor` payload

### 8.4 Archive cycle
- [Archive Closeout Note](archive/2026-05-08-gallery-tier-v4-research-closeout.md) — main PR 목록 + 잔존 자산 + retention policy §6.1
- Frozen branch: `feature/gallery-tier-v4-research` (origin 보존)
- Tag: `archive/gallery-tier-v4-research-20260508` (HEAD `52ac44d`)

### 8.5 Governance
- [Methodology deviation log](methodology_deviation_log.md) — Track 1 + Phase 1→2 전이 + Track 2 + Axis B + Progressive + Sample size entries (PR #28 + PR #36 + PR #37 누적 / 문서 상단 stale note 는 초기 PR #28 적재 시점 기준 — 후속 entries 본문 추가 적용)
- [README §canonical artifact manifest](../README.md) — 운영 v3 모델 reference anchor

### 8.6 Code reference
- `src/visionai/price_engine/api/primary_predictor.py:73-83` — SUPPORTED_VARIANTS config
- `src/visionai/price_engine/api/primary_server.py:441` — MODEL_DIR resolver
- `src/visionai/price_engine/api/primary_server.py:64-70` — required env vars
- `Dockerfile.api` — runtime image COPY contract
- `scripts/v3_6_phase3_dev_test.py` — DEV TEST 실행 entry

## 9. 코덱스 자문 history (본 종합 보고서)

| 차수 | 내용 |
|---|---|
| 종합 보고서 사전 자문 (2026-05-08) | 별도 통합 문서 권고 + Markdown canonical + HTML executive summary 분리 / 결론 + 포인터 / 본문 재서술 X |
| 본 보고서 사후 검수 (round 1, 예정) | 정합성 + 링크 + 판정 보수성 + 중복 제거 |

## 10. 본 cycle 종결

| 항목 | 상태 |
|---|---|
| **archive cycle (16 PR + 본 PR)** | ✅ 종결 |
| **트랙 1 cycle** | ✅ 종결 (Option A closed) |
| **트랙 2 cycle** | ✅ 종결 (Architecture close + Axis A 5 step + Axis B Phase A HOLD) |
| **v3.6 swap LLM 영역** | ✅ 종결 (readiness report Blocked 판정 + user action checklist) |
| **v3.6 swap 실제 실행** | ⏳ **사용자 권한 영역** (artifact bundle 학습 + 운영 환경 prerequisite + reviewer signoff 후) |
| **archive branch retention** | ⏳ 2026-05-22 이후 review 가능 (사용자 explicit 결정) |

**본 archive cycle 의 LLM 가능 모든 작업 완료.** 이후는 사용자 / DevOps / 운영팀 권한 영역.
