# v3.6 plan — V_year_saatchi_warm production rollout 실행

작성일: 2026-05-02
배경: v3.5 close (research + spec). v3.5 step 1 ablation 결과 — `V_year_saatchi_warm` 채택 (overall -0.74%p, cold +0.03%, saatchi_online 10+ -1.00%p).

본 v3.6 = **spec → production code → infra → gated rollout 실행** trail.

---

## 1. v3.6 의 목적

v3.5 까지 = research + offline validation + spec.
v3.6 = **production 적용 실행**.

핵심 질문 3개:
1. **v3.5 spec 11건 implementation 이 production safety 충족?** (Phase 1)
2. **Monitoring infra 가 v3.5 step 4 의 17 metric / 6 scenario / state machine 을 정확히 구현?** (Phase 2)
3. **Gated rollout 1%→100% 가 v3.5 의사결정 기준대로 진행 + offline -0.74%p 가 production 에서 재현?** (Phase 3-4)

---

## 2. v3.5 입력 산출물 (reference)

| Source | 내용 |
|--------|------|
| `docs/v3_5_step1_cohort_gating_results.md` | V_year_saatchi_warm 채택 결정 + ablation 결과 |
| `docs/v3_5_step2_serve_path_spec.md` | Implementation checklist 11건 (§10), serve-path flow, 10 fallback cases, artifact bundle 규약 |
| `docs/v3_5_step3_enrichment_tradeoff.md` | Cache-first + manual override hybrid, rate-limit gate, version 분리 logging |
| `docs/v3_5_step4_drift_monitoring.md` | State machine, 17 metrics, 6 scenarios, 12 dashboard panels, rollback trigger 단일 표 |
| `scripts/saatchi_year_made_merger.py` | build_variant("V_year_saatchi_warm") + 25 unit tests |
| `scripts/saatchi_detail_enricher.py` | parse_saatchi_detail_html + 18 unit tests |
| `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl` | enrichment seed data (20,644 artwork_id → year_created) |

---

## 3. Phase 1 — Implementation (코드 PR 11건)

v3.5 step 2 §10 implementation checklist 그대로. 각 항목 = 별도 PR.

### 3.1 PR 분리 (commit-able 단위)

코덱스 P0 fix: PR5+6 통합, PR8/9 의 PR4 선행 dependency 명시, 각 PR 별 unit test 강제.

| # | PR scope | 변경 file | Per-PR tests | 추정 시간 |
|---|----------|-----------|--------------|----------|
| 1 | PredictRequest schema 확장 (artwork_id/url/year_made + validation) | `primary_schemas.py` | schema validation tests (10 invalid cases) | 0.5d |
| 2 | BatchPredictRequest 동일 schema | `primary_schemas.py` | batch schema tests | 0.5d |
| 3 | artwork-level cache + get_artwork_year | `external_collector.py` | **cache unit tests** (hit/miss/TTL/LRU/alias) | 1.5d |
| 4 | feature builder year 3종 + 옵션 B disable | `primary_feature_builder.py` | **builder parity tests** (옵션 B 0/0/0 + activation matrix) | 1d |
| 5+6 | predictor 35 features + 5-file bundle + MODEL_VARIANT env + model_target 검증 (통합) | `primary_predictor.py` | **predictor startup/variant tests** (fail-closed + atomic load + variant 정합) | 1.5d |
| 7 | metrics.json variant prefix 정합 | `primary_server.py:431` | model_info variant test | 0.5d |
| 8 | 단건 predict cohort gating 통합 | `primary_server.py:575` | **cohort-gating request tests** (5 case: warm saatchi / cold saatchi / artsy / unmatched / external 충돌) | 1d |
| 9 | Batch predict cohort gating 통합 | `primary_server.py:703` | batch gating + 작가 중복 처리 tests | 1d |
| 10 | logging schema 확장 (15 필드, version 분리 포함) | `primary_server.py` + log infra | logging schema validation (DB write + 모든 필드 정합) | 1d |
| 11 | **Cross-path integration tests** (10 fallback cases + smoke benchmark) | `tests/` | full request → response e2e + cache + feature → predict 결합 | 1.5d |

총 **~10 영업일** (1 engineer, sequential). 병렬 가능: PR1+2 / PR3 / PR7. PR4 → PR8/9 (강제 dependency).

### 3.2 PR 순서 / dependency (코덱스 P0 fix)

```
PR1 (schema) ─┐
              ├─> PR8 (단건 server gating)
PR4 (builder) ┤        │
              └─> PR9 (batch server gating)
                       │
PR2 (batch schema) ────┘
                       │
PR3 (cache) ──────────────> PR8/9 (활용)
                       │
PR5+6 (predictor 통합) → PR7 (metrics) ──┐
                                           │
                                           ├─> PR11 (cross-path integration tests)
                                           │       │
                                           │       └─> Phase 1 close gate
PR10 (logging) ─> Phase 3 gate 선행 ───────┘
```

**강제 dependency** (코덱스 P0 fix):
- PR4 (builder year 3종 + 옵션 B) → PR8/9 (server gating). PR4 가 `is_saatchi_warm` / disable contract 의 origin.
- PR3 (cache) → PR8/9 (cache hit/miss 처리 wiring 필요)
- PR5+6 (predictor) → PR7 (metrics.json variant prefix 검증)
- PR10 (logging) → **Phase 3 gate 선행** (이전 "independent" 표시는 잘못 — Phase 3/4 검증의 입력)

### 3.3 Phase 1 success criterion
- 11 PR 모두 main merge 완료
- All unit tests + integration tests PASS
- Smoke benchmark: cache hit p95 ≤ 5ms, miss ≤ 600ms 검증
- 10 fallback cases (v3.5 step 2 §4) 모두 정상 동작
- Static analysis (ruff/mypy) clean

---

## 4. Phase 2 — Monitoring Infra 구축

v3.5 step 4 의 spec 을 actual infra 로 변환.

### 4.1 작업 항목

| # | 작업 | 도구 | 추정 시간 |
|---|------|------|----------|
| 1 | predict_logs / sold_actuals 테이블 생성 | PostgreSQL DDL | 0.5d |
| 2 | logging pipeline (server → DB) 구축 | application logging | 1d |
| 3 | v_d7_predict_sold_pairs view + 12 panel SQL 검증 | DB query | 1d |
| 4 | Dashboard 12 panel 구축 | **Grafana** (코덱스 P2 — alert routing / state machine 운영성 우선) | 2d |
| 5 | Alert 라우팅 (6 핵심 alert) | Slack + PagerDuty integration | 1d |
| 6 | Rollout state machine 자동화 (deploy tool) | GitOps / FeatureFlag 시스템 | 2d |
| 7 | Drift playbook on-call training | 문서 + 시나리오 시뮬 | 0.5d |

총 **~8 영업일** (1 ML/SRE engineer).

### 4.2 Phase 2 success criterion
- 12 dashboard panel 실제 데이터 표시
- 6 핵심 alert 가 fired test 시 정상 라우팅
- State machine: CANARY 1% → 5% 자동 진입 (수동 confirm 옵션)
- v3.5 step 4 §3.3 trigger 표 자동 동작 검증 (synthetic test)

---

## 5. Phase 3 — Pre-rollout validation

### 5.1 DEV TEST
- 10 fallback cases (v3.5 step 2 §4) integration test 통과
- Cohort gating correctness 100% (synthetic 10K request)
- Latency budget: cache hit p95 ≤ 5ms, miss ≤ 600ms

### 5.2 STAGING (production-like 환경)
- Real saatchi traffic 일부 (1K request) → enrichment + dashboard query 산출 검증
- 12 panel 모두 정상 데이터 표시
- 6 alert 의 baseline 수치 확정 (D1 baseline)

### 5.3 Pre-canary smoke
- Internal team manual request 100건 → cache hit/miss 분포 확인
- artist_matcher 의 saatchi 매칭 정확성 (saatchi 작가 100명 sample)
- Year_made enrichment 의 D1 cache fill rate 추정

### 5.4 Phase 3 gate
- DEV TEST: 100% PASS
- STAGING: 24h 안정 동작
- Pre-canary smoke: cache hit ≥ 10건 (warm-up 동작 확인)

---

## 6. Phase 4 — Gated rollout 실행

v3.5 step 4 §3 state machine 그대로.

### 6.1 단계별 실행

#### CANARY 1% (24h)
- v3.5 step 4 §3.2 gate criterion 모두 충족 시 ROLLOUT 5% 진입
- Crit alert 0건 / cohort_assignment_discrepancy < 1%

#### ROLLOUT 5% (D7 측정 + D1/D3 ops 체크포인트, 코덱스 P1 fix)
- **D1 (24h)**: ops-only continue. 24h crit alert 0건 + cohort discrepancy < 1% 확인. 정상 시 자동 continue.
- **D3 (72h)**: early warning review. fetch_success / cache_hit / fallback rate trend 안정 확인. 이상 시 freeze + 조사. 정상 시 continue.
- **D7 (1주)**: 승급 결정. v3.5 step 3 §5.4 re-judgment plan 적용 (eligible_rate / unmatched_rate / fallback_rate / manual_override_rate). v3.5 step 4 §3.2 gate criterion (cache hit ≥ 50%, MdAPE diff ≤ -0.3%p) 만족 시 ROLLOUT 25% 진입.
- D7 미달 → 5% 단계 추가 1주 또는 abort.

#### ROLLOUT 25% (24h)
- 모든 metric 안정 + treatment-control diff ≤ -0.5%p
- crit alert 0건

#### FULL 100% (1주 모니터링)
- D7 정상 → v3.6 close + STEADY STATE 진입

### 6.2 Rollback 발생 시 대응
- v3.5 step 4 §3.3 rollback trigger 단일 표 그대로
- Auto rollback 4건 / Auto pause 3건
- 자동 rollback 후 post-mortem (RCA 24h 내) → 재발 방지 PR

### 6.3 Phase 4 success criterion
- FULL 100% 도달 + 1주 안정 동작
- offline -0.74%p overall 의 production 재현 (D7 MdAPE diff ≤ -0.5%p, target -0.74)
- saatchi_online 10+ -1.00%p 재현 (D7 cohort breakdown)
- Crit alert 누적 0건 (또는 1건 이내, 즉시 해결)

---

## 7. Timeline / Dependency

```
Phase 1 (10d) ─────────────┐
                            ├─> Phase 3 (3d) ─> Phase 4 (1+7+1+7 = 16d) ─> v3.6 close
Phase 2 (8d) ───────────────┘   (DEV/STAGING/Pre-canary)   (1%/5%/25%/100%)
```

총 v3.6 비용:
- Phase 1: ~10d (1 engineer, sequential / parallel 가능 시 6-7d)
- Phase 2: ~8d (parallel 가능)
- Phase 3: ~3d
- Phase 4: ~16d (rollout 단계 고정)
- **합 ~30-37d** (5-7 주, 부분 parallel)

---

## 8. Success / Abort criteria

### Success (v3.6 close, STEADY STATE 진입)
- ✅ Phase 1: 11 PR merge + tests PASS (per-PR + cross-path)
- ✅ Phase 2: 12 panel + 6 alert 동작
- ✅ Phase 3: DEV/STAGING/Pre-canary 통과
- ✅ Phase 4: FULL 100% 1주 안정 + offline ROI 재현
- ✅ Phase 4 의 모든 단계에서 **24h 내 crit alert ≤ 1건** 유지

### Abort (v3.6 보류, V_year_saatchi_warm 채택 무효화)

**Phase 1 / 3 abort**:
- ❌ Phase 1: PR5+6 통합 (predictor 35 features + model_target) 구현 불가능 (artifact 호환성)
- ❌ Phase 3 STAGING: Latency budget overshoot 30% 이상 (saatchi 응답 시간 변화)

**Phase 4 abort 기준 — 시간창 기반 (코덱스 P0 fix)**:
- ❌ **24h 내 crit alert 1건 발생 → 단계 hold** (조사 후 manual continue or rollback)
- ❌ **24h 내 crit alert 2건 또는 auto-rollback trigger 1건 → 단계 중단 + 자동 rollback**
- ❌ ROLLOUT 5% D7: MdAPE diff > +0.3%p (regression) → abort
- ❌ 어떤 단계에서 mdape_d7_cold > 46% (cold protect fail) → 자동 rollback (no manual confirm)
- ❌ 같은 crit 2회 반복 (다른 24h window) → 본질 문제 → v3.6 abort

> 이전 "누적 5건" 기준 deprecated — 16d rollout 에서 너무 관대.

---

## 9. Risk track (v3.5 step 4 §5 scenario + 추가)

| Risk | Source | 완화 (v3.5 spec) |
|------|--------|------------------|
| Parser drift (saatchi schema 변경) | scenario A | valid_year_range_rate alert + cache-only mode 자동 전환 |
| Saatchi rate limit / blocking | scenario B | miss_qps + 5min_miss_burst gate + auto-suspend |
| Cohort gating fail | scenario C | discrepancy alert + auto pause |
| Cache warm-up miss spike | scenario D | cold start fetch rate cap (0.3 qps) |
| Model regression | scenario E | mdape_d7_treatment_vs_control_diff > +0.3%p alert |
| Artifact corruption / version skew | scenario F | predictor startup fail-closed + audit metric |
| **NEW: Phase 1 PR conflict** | v3.6 specific | PR dependency map (§3.2) 준수 + per-PR tests |
| **NEW: Phase 4 단계 stuck** | v3.6 specific | 각 단계 max 14d, 미달 시 v3.6 abort |
| **NEW: Mixed-version traffic split** (코덱스 P1) | feature-flag drift | model_variant_distribution audit metric (v3.5 step 4 §2.3). rollout 5% 인데 실 traffic 분포 다르면 즉시 alert + rollout pause |
| **NEW: D7 label join lag / sold_actuals 지연** (코덱스 P1) | Phase 4 gate input | sold_actuals 수신 latency 모니터 (D7 gate 직전 lag > 24h 시 D7 결정 연기). false abort/false pass 방지 |

---

## 10. v3.x progress summary (코덱스 P1 wording 정정)

| Version | 기간 | 핵심 결정 | 산출물 |
|---------|------|----------|--------|
| v3.0 | 진단 | 1.4 baseline cluster CI / cold path / D10 saatchi over-prediction | docs §1-13 |
| v3.1 | research | D10 calibration / paired Wilcoxon / cold path ablation / harness | scripts/v31_*.py |
| v3.2 | research | cluster CI redo / v1 historical paired / D10 conformal / margin redesign | scripts/v32_*.py |
| v3.3 | follow-up | warm saatchi 고가 진단 / KT 라벨 / external data inventory | scripts/v33_*.py |
| v3.4-1 | feasibility | saatchi/artsy detail page manual validation | scripts/saatchi_detail_enricher.py |
| v3.4-2 | enrichment | 21,087 saatchi 전수 enrichment (97.90% fill) + ablation V_year_only Δ-0.74%p | scripts/saatchi_*_enrichment*.py |
| **v3.5** | **plan + spec** | **V_year_saatchi_warm 채택 + serve-path spec + monitoring 설계** | **docs/v3_5_*.md** |
| v3.6 (본) | rollout | implementation + infra + gated rollout 실행 | (this plan) |

---

## 11. Out of scope (v3.7+)

- Artsy partnership / API 도입 (별도 트랙, v3.5 plan §8)
- V_full (vintage_premium / freshness_discount / career_age) 재도입 검토 (saatchi 3-4 cohort -2.54%p 재현 시)
- Sold ratio feature (saatchi avail-only 제약 해결 필요)
- Async preload / backfill (v3.6+ optimization, v3.5 plan §8)
- Year_made 외 신호 (view_count / favorite_count / listing_date — saatchi detail page 미노출, v3.4-1 검증)
- Persistent DB cache (현재 in-memory LRU only)

---

## 12. v3.6 close → STEADY STATE

v3.6 close 후 STEADY STATE:
- D30 monitoring 지속
- 월간 MdAPE 추세 (offline retrain trigger)
- v3.4-2 step 4 의 saatchi enrichment cache 갱신 (weekly TTL refresh)
- v3.7+ backlog 검토 (artsy / V_full / sold ratio)

---

## 13. 실행 순서 명확화

1. **본 plan close** → 코덱스 review + 사용자 confirm
2. **Phase 1 시작**: PR 1 (PredictRequest schema) — branch 생성 + draft PR
3. Phase 1 sequential 진행 (병렬 가능 부분)
4. Phase 2 준비 (Phase 1 완료 후 또는 parallel)
5. Phase 3 → 4 단계별 gate 통과
6. v3.6 close + post-mortem retrospective
