# v3.6 Production Swap — Readiness Report (2026-05-08)

> **본 문서 성격**: 잔존 작업 6번 (운영 swap = production rollout) 의 LLM 영역 evidence + readiness check 정리.
> **Owner**: archive cycle (`feature/gallery-tier-v4-research`) → main 적재 후 운영 swap 결정 영역.
> **판정**: 🟡 **Blocked** (LLM 영역 검증 통과 / 사용자 영역 prerequisite 미충족 → 즉시 production rollout 부적절)
> **Authority boundary**: 본 보고서 = LLM 영역 (정적/dev 검증 + 보고서). 실제 swap trigger / staging deploy / rollback 결정 = **사용자 권한 영역**.
> **사용자 영역 standalone view**: `docs/v3_6_swap_user_action_checklist_20260508.md` — §5 안전선 + §6 11 step checklist + reviewer signoff matrix + rollback 시나리오 분리 (사용자 / DevOps / 운영팀 reference).

## 0. 한 줄 요약

| 영역 | 상태 |
|---|---|
| **DEV TEST 실행** | ✅ PASS (fallback_cases_fail=0 / gating_correctness=1.0 / passed=true) |
| **Baseline artifact bundle** (`integrated_v3_filtered_tuned`, 5 file) | ✅ 모두 존재 + 로더 통과 |
| **Swap target artifact bundle** (`v3_5_v_year_saatchi_warm`, 5 file) | ❌ **모두 부재** (Blocker) |
| **CI primary lane** (ruff + mypy + pytest) | ✅ PASS (PR #27 merge 시) |
| **psycopg 의존** (ETL DB ingest) | ❌ 로컬 미설치 (운영 환경 별도 점검 의무) |
| **Staging / production monitor wiring** | ⚠️ 미검증 (LLM 영역 외) |
| **종합** | 🟡 **Blocked** — Swap target bundle 확보 + 운영 환경 prerequisite 충족 후만 진행 |

## 1. 배경

archive cycle (`feature/gallery-tier-v4-research`) 의 v3.6 production server bundle 을 main 에 적재 (PR #27, 65 files / +16,330 lines). main = code / monitoring / ETL / docs ready 상태이지만 **운영 swap = 별개 의사결정 gate**.

- PR #27 merge ≠ 운영 swap trigger
- 코덱스 권고: `cold_rollout_shadow_runbook` + Phase 3 pre-rollout 통과 후만 staged rollout
- deploy contract signoff 의무 (사용자 권한 영역)

## 2. LLM 영역 검증 결과 (PASS / Blocked)

### 2.1 DEV TEST 실행 결과 (✅ PASS)

`scripts/v3_6_phase3_dev_test.py` 로컬 실행:
- `fallback_cases_fail = 0`
- `gating_correctness = 1.0`
- `passed = true`

DEV 환경에서 cohort gating + fallback path 의 정상 작동 확인.

### 2.2 Baseline artifact bundle 정합 (✅ PASS)

운영 현재 baseline `integrated_v3_filtered_tuned` 의 5 runtime file 모두 존재:

| File | 위치 | 상태 |
|---|---|---|
| `integrated_v3_filtered_tuned_catboost.cbm` | `model_test_results/` | ✅ 존재 |
| `integrated_v3_filtered_tuned_xgboost.json` | `model_test_results/` | ✅ 존재 |
| `integrated_v3_filtered_tuned_xgboost_label_maps.json` | `model_test_results/` | ✅ 존재 |
| `integrated_v3_filtered_tuned_warm_artists.json` | `model_test_results/` | ✅ 존재 |
| `integrated_v3_filtered_tuned_source_calibration.json` | `model_test_results/` | ✅ 존재 |

Loader (`primary_predictor.py:load_models()`) 통과.

### 2.3 Swap target artifact bundle 부재 (❌ Blocker)

`SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]` (`primary_predictor.py:79-83`) 의 prefix `integrated_v3_5_v_year_saatchi_warm_*` 5 runtime file **모두 부재**:

| File | 상태 | 영향 |
|---|---|---|
| `integrated_v3_5_v_year_saatchi_warm_catboost.cbm` | ❌ MISSING | swap target loader fail |
| `integrated_v3_5_v_year_saatchi_warm_xgboost.json` | ❌ MISSING | swap target loader fail |
| `integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json` | ❌ MISSING | swap target loader fail |
| `integrated_v3_5_v_year_saatchi_warm_warm_artists.json` | ❌ MISSING | swap target loader fail |
| `integrated_v3_5_v_year_saatchi_warm_source_calibration.json` | ❌ MISSING | swap target loader fail |

→ **현재 main 에서는 `MODEL_VARIANT=v3_5_v_year_saatchi_warm` 환경변수로 production load 시도 시 즉시 fail**.

### 2.4 MODEL_VARIANT / prefix / model_target 일관성 (✅ 정합)

코드 (`primary_predictor.py:73-83`) 의 variant config:

```python
SUPPORTED_VARIANTS = {
    "v3_filtered_tuned": {
        "prefix": "integrated_v3_filtered_tuned",
        "expected_target": "v3_filtered_tuned",
        ...
    },
    "v3_5_v_year_saatchi_warm": {
        "prefix": "integrated_v3_5_v_year_saatchi_warm",
        "expected_target": "v3_5_v_year_saatchi_warm",
        ...
    },
}
DEFAULT_VARIANT = "v3_filtered_tuned"
```

→ DEFAULT (현재 운영) = `v3_filtered_tuned`. SWAP TARGET = `v3_5_v_year_saatchi_warm`.

### 2.5 Provenance manifest 정합 (⚠️ Caveat)

- `model_test_results/integrated_v3_filtered_tuned.provenance.json` 존재 + 구조 유효
- **Caveat (코덱스 P1)**: manifest 의 `git_dirty=true` 기록 — canonical evidence 로 사용 시 해석 주의 (uncommitted change 가 manifest 생성 시점에 있었음 시사)
- **Caveat (코덱스 P2)**: 파일명 규약 mismatch — 본 manifest 는 `*.provenance.json` / 코드 생성 규칙은 `*_provenance.json` (확장자 prefix 차이) — 실제 loader 영향은 없으나 hygiene 권고
- swap target variant 의 provenance manifest 부재 (artifact bundle 부재의 부수 효과)

### 2.6 Logging schema / monitor payload 정합 (✅ 정적 검증 통과)

- `scripts/etl_predict_logs.py` ↔ `monitoring/sql/001_predict_logs_ddl.sql` 의 schema 정합 확인
- `/monitor` endpoint payload (PR #12 + PR13 의 worker_instance_id + fetch_gate stats) 정합
- API reference (`docs/api_reference.html`) PR13b /monitor 신규 필드 반영 확인

## 3. 사용자 영역 prerequisite (LLM 비권한)

### 3.1 Critical (Blocker — 충족 의무)

1. **Swap target artifact bundle 적재** (`v3_5_v_year_saatchi_warm` 5 runtime file)
   - 학습 source: `scripts/saatchi_year_made_merger.py` + 학습 pipeline 수동 실행 → bundle 생성
   - 적재 위치: `model_test_results/integrated_v3_5_v_year_saatchi_warm_*`
   - 검증: 5 file 모두 존재 + loader 통과
2. **Provenance manifest 동반** (`integrated_v3_5_v_year_saatchi_warm.provenance.json`)
   - manifest 의 `git_dirty=false` 보장 (clean state 학습 의무)
   - canonical artifact manifest (README §canonical artifact manifest) 의 reference anchor

### 3.2 Required (운영 환경)

3. **psycopg[binary] 운영 환경 install** (cron 운영 환경)
   - `pip install -e .[etl]` 또는 `pip install psycopg[binary]>=3.1`
   - ETL `scripts/etl_predict_logs.py` cron schedule 등록
4. **PostgreSQL `predict_logs` schema 적재**
   - `monitoring/sql/001_predict_logs_ddl.sql` 운영 DB 적재
   - `monitoring/sql/002_v_d7_predict_sold_pairs.sql` ~ `monitoring/sql/020_alert_rollback_triggers.sql` 적용
5. **Grafana / Prometheus / Slack 운영 환경 wiring**
   - `monitoring/grafana/dashboard_v3_6_rollout.json` import
   - `monitoring/prometheus/scrape_config.yaml` 적용
   - `monitoring/alerting/grafana_*` (Slack / PagerDuty contact + notification policies) 운영 적용
6. **Connection string / secrets / cron schedule** 운영 환경 별도 설정 (LLM 절대 비권한)

### 3.3 Recommended (코덱스 review signoff)

7. **Reviewer 1 (API/serving)**: `primary_server.py` / `primary_predictor.py` / Dockerfile.api / logging schema
8. **Reviewer 2 (infra/deploy)**: artifact bundle naming / env contract / rollback path / runbook 정합
9. **Reviewer 3 (data/ML contract)**: metrics.json / provenance / calibration / source bundle 정합

## 4. Swap 실행 절차 (사용자 영역, runbook reference)

`docs/cold_rollout_shadow_runbook_20260507.md` + `docs/v3_6_phase3_runbook.md` 의 step 별 실행 (LLM 비권한 / 사용자 영역):

| 단계 | 영역 | 의무 |
|---|---|---|
| Phase 3 STAGING | 사용자 + 운영팀 | DEV TEST 결과를 staging 환경에서 재현 |
| Pre-canary smoke | 사용자 + 운영팀 | 0.3 qps cap / TestClient warmup-mode 검증 |
| Phase A cold shadow | 사용자 + 운영팀 + 트래픽 routing | shadow inference / 실제 prediction 비교 / drift monitoring |
| D+7 판정 | 사용자 + reviewer signoff | 7-day shadow 결과 → staged rollout 결정 |
| Staged rollout 10% → 50% → 100% | 사용자 + 운영팀 | 점진 트래픽 routing / monitor + alert wiring |
| Rollback gate | 사용자 (긴급 운영) | drift / regression 감지 시 rollback 권한 |
| Deploy contract signoff | 사용자 (최종 승인) | reviewer 1+2+3 signoff 후만 swap 확정 |

## 5. LLM 단독 진행 금지 항목 (안전선)

본 readiness report 의 boundary:

❌ **LLM 단독 production rollout 절대 X**
❌ **LLM 단독 staging deploy 절대 X**
❌ **LLM 단독 secrets / connection string 설정 절대 X**
❌ **LLM 단독 traffic routing 절대 X**
❌ **LLM 단독 rollback 결정 절대 X**

✅ LLM 가능: 정적 검증 / DEV TEST 실행 / readiness 보고서 / runbook 평가 / code review 의견 / artifact 정합 점검

## 6. 사용자 swap 전 checklist (실행형)

본 checklist 를 위에서 아래로 확인 후 swap 진행:

```
[ ] 1. Swap target artifact bundle 5 file 적재 확인:
       /bin/ls model_test_results/ | grep "integrated_v3_5_v_year_saatchi_warm_"
       (catboost.cbm / xgboost.json / xgboost_label_maps.json / warm_artists.json / source_calibration.json)

[ ] 2. Provenance manifest 적재 + git_dirty=false 확인:
       jq .git_dirty model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json
       → 결과: false

[ ] 3. 운영 환경 의존성 설치:
       pip install psycopg[binary]>=3.1
       또는 uv sync --all-extras

[ ] 4. PostgreSQL predict_logs schema 적재:
       psql $DB_URL -f monitoring/sql/001_predict_logs_ddl.sql
       (그 후 002~020 순차 적용)

[ ] 5. Grafana dashboard + alerting + Prometheus wiring:
       monitoring/grafana/dashboard_v3_6_rollout.json import
       monitoring/prometheus/scrape_config.yaml 적용
       monitoring/alerting/grafana_alerts.yaml 적용

[ ] 6. Phase 3 STAGING 환경에서 DEV TEST 재실행:
       MODEL_VARIANT=v3_5_v_year_saatchi_warm python scripts/v3_6_phase3_dev_test.py
       → fallback_cases_fail=0 / gating_correctness=1.0 / passed=true

[ ] 7. Pre-canary smoke (0.3 qps cap):
       cold_rollout_shadow_runbook §Phase 3 Pre-canary 절 따라 실행

[ ] 8. Phase A cold shadow (D+0 ~ D+7):
       Shadow inference 활성화 / drift monitoring / 실제 prediction 비교

[ ] 9. D+7 판정 + reviewer 1+2+3 signoff:
       shadow 결과 + drift report → staged rollout 결정

[ ] 10. Staged rollout (10% → 50% → 100%):
       각 단계에서 monitor / alert wiring 검증 + rollback path 확보

[ ] 11. Final swap (MODEL_VARIANT env var production 적용):
       export MODEL_VARIANT=v3_5_v_year_saatchi_warm
       (DEFAULT_VARIANT 변경 시 별도 PR 의무)
```

## 7. 잠재 risk (코덱스 caveat)

| Risk | 대응 |
|---|---|
| 문서상 "v3.6 준비 완료" vs 실제 rollout artifact 부재 혼선 | 본 readiness report 로 명확화 |
| Provenance 파일명 규약 mismatch (`.provenance.json` vs `_provenance.json`) | hygiene 권고 / 실제 loader 영향 X |
| Provenance manifest `git_dirty=true` | swap target manifest 는 clean state 의무 |
| Runbook 의 staging/prod 증적 필수 항목을 문서 검토만으로 PASS 처리 | 실제 staging 환경 evidence 만 PASS |
| LLM 단독 rollout = production incident 위험 | §5 안전선 + §6 checklist 사용자 권한 강제 |

## 8. 코덱스 자문 history

| 차수 | 내용 |
|---|---|
| 잔존 작업 6번 사전 자문 (2026-05-08) | LLM 가능 / 사용자 영역 분리 + 판정 = Blocked + readiness report 권고 |
| 본 보고서 사후 검수 (예정) | 본 commit 직후 |

## 9. 참조

- `docs/v3_6_plan.md` — v3.6 plan
- `docs/v3_6_phase3_runbook.md` — Phase 3 pre-rollout runbook
- `docs/v3_6_summary_report.md` / `.html` — v3.6 종합 보고서
- `docs/cold_rollout_shadow_runbook_20260507.md` — cold rollout shadow 운영 runbook
- `docs/phase_a_monitoring_spec_20260507.md` — Phase A monitoring spec
- `docs/api_reference.html` — API contract reference (PR13b /monitor 필드 반영)
- `README.md` §Canonical artifact manifest — 운영 v3 모델 reference anchor
- `docs/archive/2026-05-08-gallery-tier-v4-research-closeout.md` — archive cycle closeout
- `src/visionai/price_engine/api/primary_predictor.py:73-83` — SUPPORTED_VARIANTS config
- `scripts/v3_6_phase3_dev_test.py` — DEV TEST 실행 entry

## 10. 결정 이력 요약

| 항목 | 결정 |
|---|---|
| **본 readiness report 의 의미** | LLM 영역 evidence 정리 / Blocked 판정 / 사용자 권한 swap 영역 분리 |
| **현 상태** | DEV TEST PASS / Baseline 검증 통과 / Swap target bundle 부재 |
| **즉시 production rollout** | ❌ 부적절 (Swap target bundle 확보 + 운영 환경 prerequisite 충족 의무) |
| **LLM 추가 작업 가능 영역** | 정적 검증 / 추가 DEV TEST / runbook hygiene / code review |
| **사용자 영역 시작 시점** | swap target artifact bundle 적재 + 운영 환경 prerequisite 충족 후 |
| **본 cycle 종결** | 본 readiness report = 잔존 작업 6번의 LLM 영역 종결 / 후속 swap = 사용자 의사결정 |
