# v3.5 plan — saatchi year_made enrichment 채택 검증 + 안전 배포

작성일: 2026-05-02
배경: v3.4-2 step 5 (full ablation) 결과 — `V_year_only` 가 overall MdAPE Δ-0.74%p 통계 유의 개선 (CI95 [-1.144, -0.324], artist p=0.018), 단 cold cohort 에서 +0.99~+2.98%p worse. 코덱스 권장 채택안: **V_year_only + cold cohort 차단**.

---

## 1. v3.5 의 목적 (research → safe deployment path)

v3.4-2 는 *research ablation* — "year signal upper-bound 측정". 본 v3.5 는 그 결과를 **production 안전 배포 가능 형태로 검증**하는 trail. 채택 결정 근거가 아니라 채택 path 의 검증.

핵심 질문 3개:
1. **Cohort gating 으로 cold downside 제거 가능?** (offline)
2. **Production scrape 가 year_made 를 안정 공급 가능?** (ops)
3. **Gated rollout 시 drift 감지 가능?** (monitoring)

---

## 2. 결정된 framing (v3.5 step 1 결과 후 갱신)

| 채택안 | 결정 |
|--------|------|
| Variant | **V_year_saatchi_warm** (saatchi & warm intersect gating, step 1 unique pass) |
| Cohort gating | **saatchi & warm intersect** — `is_saatchi=True AND warm_artist=True` 만 활성 |
| Drift 회피 | production scrape 가 detail page year_made stable 공급 (saatchi 만 가능, artsy 별도 트랙) |
| Rollout | gated (cohort) + monitored (drift) — global on 금지 |

기대 효과 (v3.5 step 1 정량 근거, n_splits=5 full):
- Overall MdAPE: **-0.738%p** (CI95 [-1.140, -0.337], artist p=0.00028)
- saatchi_online: -1.05%p
- saatchi_online 10+ warm 작가 (n=19,423): **-1.002%p**
- Cold cohort (n=1,314): **+0.028% ≈ 0** (gating 으로 noise 차단 성공)

### v3.4-2 step 5 → v3.5 step 1 채택안 변경 history
- v3.4-2 step 5: `V_year_only` 권장 (단 cold +0.99% 손실)
- v3.5 step 1: gating 검증 후 **`V_year_saatchi_warm`** (cold +0.03% ≈ 0)
- 코덱스 R2 해석: warm-only gating 의 cold +3.12% counterintuitive 결과 → "비활성=0 sentinel" 이 cold leaf 악화. saatchi&warm intersect 만 source 축 + warm 축 교호작용으로 cold 보호.

---

## 3. 4-step backlog

### Step 1 — V_year_only + cohort gating 오프라인 검증 (research)

**목표**: cold cohort 의 +0.99%p worse 를 cohort gating 으로 제거 가능한지 입증.

**variants (3개 추가 ablation)**:
- `V_year_saatchi_only`: saatchi rows 만 year_made/has_year_made/work_age, 비-saatchi = NaN/disabled
- `V_year_warm_only`: wmask rows 만 year_made, cold = NaN/disabled
- `V_year_saatchi_warm`: saatchi & warm 둘 다 만족 (saatchi cold + non-saatchi 모두 disabled)

**평가** (코덱스 P0 R2 수치 명시):
- Primary: overall MdAPE — `Δ ≤ -0.5%p` (CI95 0 미포함, V0 baseline 대비)
- Guardrail 1: cold MdAPE — `Δ ≤ +0.3%p`
- Guardrail 2: saatchi_online 10+ MdAPE 보존 — `Δ ≤ -0.8%p`

**Variant selection rule** (코덱스 P0):
1. 우선: `V_year_saatchi_only` (코덱스 1순위 cohort gating 대상)
2. 차선: `V_year_warm_only` 또는 `V_year_saatchi_warm` 중 cold guardrail 더 안전한 variant
3. 동률 (overall Δ 차이 ≤ 0.1%p) 시: cold ΔMdAPE 절댓값 작은 variant 선택
4. 셋 중 어떤 variant 도 primary 또는 guardrail 1 충족 못하면 → **abort** (v3.5 close, v3.6 보류)

**산출물**: `scripts/v35_step1_cohort_gating_ablation.py` + JSON

**비용**: ~1 hr (3 variant × 5-fold OOF, full mode 비슷)

---

### Step 2 — Production feature availability 정리 (ops review)

**목표**: production scrape 가 year_made 를 어떻게 / 언제 / 어떤 latency 로 공급할지 결정.

**입력 자료**:
- v3.4-1 Phase 1 manual 검증: saatchi detail page Year Created 100% 검출 (5/5 stratified)
- v3.4-2 step 4 전수 결과: 97.90% fill, anti-bot 0, rate 0.88 req/s
- `src/visionai/price_engine/api/external_collector.py` 현 상태: artsy GraphQL 작가 정보만, saatchi enrichment 미호출

**검토 항목**:
| 항목 | Saatchi | Artsy |
|------|:-------:|:-----:|
| 현재 production 수집 | X | X |
| Detail page year_made 노출 | ✅ 97.90% | (anti-bot 차단) |
| 추가 fetch 가능 | ✅ ~0.6-1 sec/req | ❌ 별도 partnership |
| 추가 latency 영향 | 가격 예측 0.6-1s 증가 | n/a |
| Cache 가능 | ✅ artwork_id 단위 | n/a |

**의사결정 산출물**: `docs/v3_5_step2_feature_availability.md`
- artsy: separate track (out-of-scope for v3.5)
- saatchi: cache-first enrichment, miss 시 fallback (has_year_made=0)

**Cache 단위 결정** (코덱스 P1 R3 fix):
- 현재 `external_collector.py:11-13` 의 `_cache` 는 `artist_name` 단위 (작품 X)
- 본 enrichment 는 **`artwork_id` 단위 cache** 신설 (in-memory LRU + DB 영구)
- 단순 lookup: 같은 artwork 재조회 시 hit, 첫 fetch 만 miss

**Step 2 success criterion** (코덱스 P0 R1 수치화):
1. Serve-path integration spec 확정 (parser → cache → fallback 순서)
2. Fallback semantics 확정: enrichment 실패 시 `year_made=NaN, has_year_made=0` 강제
3. Latency p95 budget 수치 결정: cache miss `≤ 600 ms`, hit `≤ 5 ms` 목표
4. Cohort assignment correctness ≥ 99% (saatchi vs 비-saatchi gating 정확성)

**비용**: ~2-3 hr (설계 문서 + serve-path integration spec)

---

### Step 3 — Enrichment / latency / coverage trade-off 검토

**목표**: production 변경 비용 vs ROI 정량화.

**시나리오 비교**:
| 시나리오 | Latency 증가 | Cache hit 후 | year_made coverage | 기대 MdAPE |
|----------|-------------:|-------------:|-------------------:|-----------:|
| baseline (현재) | 0 ms | n/a | 0% | 10.358% |
| sync enrichment (no cache) | +600-1000 ms | n/a | ~98% | 9.62% |
| **cache-first** (recommended) | +600 ms (miss only) | +0 ms | ~98% | 9.62% |
| async backfill (preload) | +0 ms | +0 ms | ~98% (preload 후) | 9.62% (v3.6+ optimization) |

**결정**: cache-first 가 latency vs ROI optimal.

**Cache hit rate = 측정 태스크** (코덱스 P1 R3 — 예상치가 아님):
- `artwork_id` 단위 캐시 → 같은 작품 재조회 빈도가 hit rate 결정
- v3.5 step 3 산출: rollout 5% 단계에서 실제 cache hit/miss 측정 → 이후 단계 latency budget 검증

**산출물**: `docs/v3_5_step3_enrichment_tradeoff.md` + 측정 plan (rollout 5% 단계 hit rate 수집 query)

**비용**: ~1 hr (분석 + 측정 plan 문서)

---

### Step 4 — Gated rollout drift 모니터링 설계

**목표**: gated rollout 시 train/serve drift 감지 + cold cohort 보호 검증.

**모니터링 metrics** (코덱스 P1 R4 — upstream + downstream 분리):

### Upstream ops (장애 빠른 감지)
| Metric | 목표 | 알림 임계 |
|--------|-----:|----------:|
| Enrichment fetch success rate | ≥ 98% | < 95% (parser break / anti-bot) |
| Cache miss rate | (측정용 baseline) | spike > 2× (warm-up issue) |
| Enrichment latency p95 (miss) | ≤ 600 ms | > 1000 ms (saatchi 응답 지연) |
| Valid year range rate | 100% within [1850, 2030] | < 99.5% (parser drift) |
| Fallback rate (eligible saatchi) | ≤ 5% | > 10% (enrichment broken) |

### Downstream signal (모델 가치 검증)
| Metric | 목표 | 알림 임계 |
|--------|-----:|----------:|
| `has_year_made` 활성률 (saatchi rollout cohort) | ≥ 95% | < 90% |
| Cold artist year_made 비활성 (gating correctness) | 100% | < 99% (gating fail) |
| p50 predicted price ratio (D7 vs D-7) | 0.97 ~ 1.03 | drift > ±10% |
| p90 predicted price ratio (D7 vs D-7) | 0.95 ~ 1.05 | drift > ±15% |
| MdAPE D7 (saatchi_online rollout) | ≤ 9.7% | > 10.5% |
| MdAPE D7 (cold cohort) | ≤ 43% | > 44% (cold protect fail) |

**설계 산출물**:
- `docs/v3_5_step4_drift_monitoring.md`
- 모니터링 SQL / dashboard 스펙
- 알림 트리거 (Slack / email)
- Rollout 단계: 5% → 25% → 100% (각 단계 24h 관찰)

**비용**: ~2-3 hr (설계 + 대시보드 query)

---

## 4. Timeline / Dependency

```
Step 1 (offline, 1 hr) ─┐
                        ├─> Step 2 (ops, 1-2 hr) ─> Step 3 (analysis, 1 hr) ─> Step 4 (monitoring, 2-3 hr)
v3.4-2 결과 ─────────────┘                                                       ↓
                                                                     v3.6 production rollout
```

총 v3.5 비용: ~5-7 hr (4 step 합)

---

## 5. Success / Abort criterion

### Success (v3.6 rollout 진행) — 코덱스 P0 R1 수치화
- ✅ **Step 1**: 어떤 gating variant 가 `overall Δ ≤ -0.5%p` + `cold Δ ≤ +0.3%p` + `saatchi_online 10+ Δ ≤ -0.8%p` 모두 충족
- ✅ **Step 2**: serve-path integration spec 확정 + fallback semantics 확정 + p95 budget `≤ 600 ms (miss) / ≤ 5 ms (hit)` 수치화 완료
- ✅ **Step 3**: cache key 결정 (artwork_id 단위) + 측정 plan 확정 (rollout 5% 단계에서 실제 hit/miss 수집)
- ✅ **Step 4**: rollout gate query / alert 실제 산출 가능 + cohort assignment correctness ≥ 99%

### Abort (v3.5 close, v3.6 보류)
- ❌ Step 1: 어떤 gating variant 도 primary + guardrail 1 미충족
- ❌ Step 2: production scrape 변경이 unfeasible (인프라 한계 / 인증 미해결)
- ❌ Step 3: artwork_id 캐시 단위에서 hit rate 측정 plan 합의 실패
- ❌ Step 4: cohort assignment correctness < 99% 또는 모니터링 alert 산출 불가

---

## 6. Risk track

| Risk | 영향 | 완화 |
|------|------|------|
| Gating variant 가 ROI 약화 | overall -0.74 → -0.4 ~ -0.5 | step 1 결과 보고 V_year_only global 채택 재검토 |
| Saatchi anti-bot 강화 | enrichment fetch 실패 | 1-2 일 stale cache fallback |
| Artist 작품 라이프사이클 (sold/제거) | year_made 캐시 stale | weekly cache refresh |
| Cold cohort 분포 변화 | gating 효과 약화 | 월간 rollout 재평가 |
| Train/serve year_made 정의 차이 | drift 재발 | 정의 단일 source 강제 (`prepare_primary_market_dataset.py:254` 그대로) |
| **Parser/schema drift** (코덱스 P2) | year_made 값 오염 (이상치 / 잘못된 파싱) | step 4 valid year range monitoring [1850, 2030] + parse_warnings tracking |
| **Cache warm-up miss spike** (코덱스 P2) | rollout 초기 latency 폭증 | rollout 5% 단계에서 cache miss rate 실측 + 단계별 ramp-up |

---

## 7. 산출물 (예정)

- `scripts/v35_step1_cohort_gating_ablation.py`
- `docs/v3_5_step2_feature_availability.md`
- `docs/v3_5_step3_enrichment_tradeoff.md`
- `docs/v3_5_step4_drift_monitoring.md`
- `model_test_results/v3_diagnostics/v35_step1_*.json`

---

## 8. Out of scope (v3.6+)

- Artsy partnership / API 도입 (별도 트랙)
- V_full 의 vintage_premium / freshness_discount / career_age 재도입 (saatchi 3-4 cohort -2.54%p 재현 후 결정)
- Sold ratio feature (코덱스 v3.4-2 step 4 부산물 — saatchi raw avail-only 제약 별도)
- Year_made 외 신호 (view_count / favorite_count / listing_date — saatchi detail page 미노출, v3.4-1 검증 결과)
- **Async preload / backfill** (코덱스 P2): v3.5 는 cache-first 만 결정. preload optimization 은 v3.6+ optimization backlog (cache hit rate 측정 결과 보고 결정)

---

## 9. v3.4-2 close → v3.5 begin 의 명확한 transition

- **v3.4-2** = research ablation. Year signal upper-bound 측정 완료 (V_year_only Δ-0.74%p 통계 유의).
- **v3.5** = safe deployment path validation. Cohort gating + production feasibility + drift monitoring.
- **v3.6** = production rollout (gated). v3.5 success criterion 통과 시.
