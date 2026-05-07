# Phase A Shadow 배치 승인서

> **승인 권한**: 담당자 단독 (spec §11.3)
> **연계**: D-1 final check (`docs/phase_a_d1_final_check_20260507.md`) 완료 후 작성
> **사용**: 본 문서 1페이지 출력 또는 PR description 으로 사용

## 배치 정보

| 항목 | 값 |
|---|---|
| 배치 일시 | YYYY-MM-DD HH:MM (KST) |
| 승인자 (담당자) | 이름 / 직책 |
| Shadow 대상 범위 | cold artist (학습 데이터 < 10 작품) 트래픽 100% (운영 영향 0%) |
| Shadow 기간 | D+0 ~ D+7 (1주, spec §11.1) |
| Phase B 진입 조건 | spec §11.1 7개 합격 기준 모두 PASS |

## 모델 / Pipeline (변경 X 보장)

| 항목 | 값 |
|---|---|
| Model hash | `track2_v1_20260507` (F4 + log_area spline + Huber eps=1.35 alpha=1e-4) |
| Feature pipeline version | `f4_spline_v1_20260506` |
| Train data hash | `data/curated/stage3_1000x100.parquet` SHA = ___________________ |
| Stage 4 baseline 일치성 | ☐ 확인 (`docs/stage4_데이터수집계획_20260507.md` §6.0 동일 hash) — **mismatch 시 서명 금지, 배치 보류** |

## 사전 점검 결과

| 항목 | 결과 |
|---|---|
| D-1 final check (`docs/phase_a_d1_final_check_20260507.md`) §1-§5 모두 ☑ | ☐ |
| Offline preflight (`scripts/phase_a_preflight.py`) ✓ PASS | ☐ |
| In-environment fail-closed 3종 (NO_BASELINE / MODEL_ERROR / PARITY_BREACH) ☐ | ☐ |
| Sample parity 30/30 max diff ≤ 1e-6 | ☐ |
| Known risk / exception | ☐ 없음 / 또는 명시: __________________ |

## Alert / Rollback

| 항목 | 값 |
|---|---|
| Alert 채널 | Slack `#track2-shadow` (또는 운영팀 정의) |
| Alert rules | 핵심: 가드레일 hit > 2% / fallback > 5% / latency p95 > V3×2 / schema < 99% / parity_breach 즉시 (전체 8 rules: monitoring spec §2) |
| Rollback 정식 경로 (spec §15.1 canonical) | `ops cli model.disable --name track2_v1 --reason "manual_rollback: <사유>"` (이후 traffic.verify + notify 3-step) |
| Rollback 대안 경로 (ops cli 장애 시만) | `kubectl set env deployment/track2-shadow ENABLED=false` |

## 사전 공유 (인지 목적, 승인 X)

- ☐ 운영 매니저 Slack 사전 공유 (`#track2-shadow` 채널)
- ☐ 의사결정자 Slack 사전 공유 (D+7 합격 판정 시점 공지)

## 승인

본인은 위 사전 점검을 모두 확인했으며, spec §11.3 단독 승인 권한으로 Phase A shadow 배치를 승인한다.

- 서명: ___________________
- 일시: YYYY-MM-DD HH:MM (KST)

---

## 후속 일정 (참고)

| 시점 | 액션 |
|---|---|
| D+0 | 배치 + Slack 알림 |
| D+1 ~ D+7 | 일일 점검 (`docs/cold_rollout_shadow_runbook_20260507.md` §2) |
| D+7 | 합격 판정 (spec §11.1 7개 기준) → Phase B 5% canary 진입 검토 (담당자 + 운영 매니저 동반 승인) |
| D+7 + α | 결과 보고서 작성 (`docs/phase_a_results_YYYYMMDD.md`) |
