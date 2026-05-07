# Phase A Shadow D-1 Final Check

> **작성일**: 2026-05-07
> **목적**: Phase A shadow 배치 전일 (D-1) 운영팀이 직접 읽고 체크하는 최종 점검
> **연계**: `docs/cold_rollout_shadow_runbook_20260507.md` §1 사전 준비, `scripts/phase_a_preflight.py` (offline 점검)
> **승인**: 본 체크 PASS 시 담당자 단독 Phase A 배치 승인 (spec §11.3)

> **사용법**: 본 문서를 1페이지 출력하거나 PR 체크리스트로 복사. 모든 항목 ☐ → ☑ 후 §6 서명.

## 1. 모델 / Pipeline Artifact (변경 X 보장)

- ☐ 운영 모델 hash 일치: `track2_v1_20260507`
- ☐ Feature pipeline version 일치: `f4_spline_v1_20260506`
- ☐ Train data hash 기록: `data/curated/stage3_1000x100.parquet` SHA = `__________________`
- ☐ Stage 4 baseline 해시와 동일 (`docs/stage4_데이터수집계획_20260507.md` §6.0)

> ⚠️ **Hash mismatch 발견 시**: 본 §6 서명 금지 + 배치 보류 + Stage 4 baseline 정의 재확인 (runbook §4.1). hash 일치 회복 후 본 D-1 재실행.

## 2. Offline Preflight (LLM 사전 검증 — 본 D-1 에 재실행)

```bash
python3 scripts/phase_a_preflight.py
```

- ☐ Self-parity test: ✓ PASS (max diff ≤ 1e-6)
- ☐ Feature pipeline 일관성: ✓ PASS (deterministic)
- ☐ Latency baseline 측정 완료 (offline single row predict p95 = ___ μs)
- ☐ Fail-closed 3종 test cases 운영팀 인지 확인

## 3. In-environment 점검 (운영팀 직접 실행)

- ☐ 운영 모델 artifact hash = §1 hash 일치
- ☐ Dependency lock (requirements.txt / poetry.lock) 학습 환경과 동일
- ☐ Runtime flag / config 학습 시 가정과 동일 (KRW 환율 기준일 등)
- ☐ Shadow log stream 분리 생성 (`track2_shadow.log`)
- ☐ Slack alert 채널 연결 (핵심 4종: schema / latency / guardrail / fallback — 전체 8 rules 는 monitoring spec §2)
- ☐ Latency p95 측정 baseline (V3 운영 환경) 산출 완료 — V3 p95 = ___ ms

## 4. Fail-closed E2E (운영팀 in-environment 실행)

- ☐ **NO_BASELINE**: 학습 hash 와 다른 hash 의도적 배포 → 자동 fallback 발동 + reason="NO_BASELINE" log
- ☐ **MODEL_ERROR**: 예측 endpoint 강제 종료 → V3 fallback 5초 이내 발동 + reason="MODEL_ERROR" log
- ☐ **PARITY_BREACH**: area_cm2=None 또는 birth_year=None 입력 → fallback 발동 + reason="PARITY_BREACH" log

## 5. Sample Parity 30 건 (운영팀 in-environment 실행)

- ☐ Sample dataset 사용: `experiments/structural_v1/results/phase_a_sample_parity_30.json` (preflight 자동 산출, 30 건 input + expected_log_prediction)
- ☐ 각 sample 의 expected vs 운영 환경 재예측 비교
- ☐ 30/30 max diff ≤ 1e-6 (요구) — 결과 첨부: `__________________`
- ☐ 차이 발생 row 0 건 확인

## 6. 배치 승인 (담당자 단독, spec §11.3)

| 항목 | 결과 |
|---|---|
| §1 모든 ☑ | __ |
| §2 offline preflight ✓ PASS | __ |
| §3 in-environment 6 항목 ☑ | __ |
| §4 fail-closed 3종 ☑ | __ |
| §5 sample parity 30/30 ☑ | __ |

- 담당자 이름 / 직책: ___________________
- 배치 일시 (예정): ___________________
- 서명: ___________________

→ 모든 ☑ + 서명 후 Phase A shadow 배치 진행 (`docs/cold_rollout_shadow_runbook_20260507.md` §2 일일 점검 시작)

## 7. 사전 공유 (운영 매니저 / 의사결정자, 인지 목적)

- ☐ Phase A shadow 배치 사실 Slack 알림 (사전 공유, 승인 X)
- ☐ D+7 합격 판정 시점 공지

## 8. 트러블슈팅

- 본 §1-§5 중 ☐ 하나라도 PASS 못하면 배치 보류
- §3 / §4 / §5 운영팀 직접 실행 항목 FAIL 시 → 인프라 팀 협의
- §1 / §2 offline 항목 FAIL 시 → 모델 / 학습 데이터 재점검 (운영 인프라 X)
- Rollback 명령: `docs/cold_rollout_shadow_runbook_20260507.md` §6 참조
