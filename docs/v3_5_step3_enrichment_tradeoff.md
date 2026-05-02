# v3.5 step 3: enrichment / latency / coverage trade-off

작성일: 2026-05-02
배경: v3.5 step 2 (serve-path integration spec close, V_year_saatchi_warm). 본 step 3 = scenario 비교 + cache hit rate **측정 plan** (코덱스 P1: 추정 → 측정 격하).

---

## 1. Step 3 의 scope

**목적**:
1. enrichment 시나리오 4종 비교 (latency vs coverage vs ROI)
2. cache hit rate 측정 plan 확정 (rollout 5% 단계에서 실측)
3. step 4 monitoring 이 검증할 SLA 수치 결정

**Out of scope** (코드 변경 X):
- 실제 cache 구현 → v3.6 implementation checklist (step 2 §10)
- async preload 로직 → v3.6+ optimization backlog

---

## 2. 시나리오 비교 (4종)

| 시나리오 | Latency 추가 | Cache | Coverage | 기대 MdAPE | 비용/복잡도 |
|----------|-------------:|-------|---------:|-----------:|:----------:|
| baseline (현재 production) | 0 ms | n/a | 0% | 10.358% | 0 |
| sync enrichment (no cache) | +600~1000 ms | X | ~98% | 9.620% | 낮음 |
| **cache-first (recommended)** | +600 ms (miss only) | in-memory LRU | ~98% | 9.620% | 중간 |
| async backfill (preload) | +0 ms | preload + LRU | ~98% (preload 후) | 9.620% | 높음 (v3.6+) |
| manual-only (요청 year_made 만) | 0 ms | n/a | <10% (client 의존) | ~9.95% (추정, partial) | 낮음 |

### 2.1 시나리오 별 분석

#### A. baseline (현재 production)
- year_made 사용 X (CB_FEATURES 미포함)
- p95 latency 변화 0
- v3.4-2 step 5 결과 = 10.358% MdAPE
- 채택 변수 도입 시 fallback 옵션 (rollout 0% / abort)

#### B. sync enrichment (no cache)
- 모든 saatchi-warm 요청에 detail page fetch
- p95 latency +600~1000 ms (saatchi 응답 시간 + parsing)
- **rate limit 위험**: 동시 요청 N → saatchi rate limit 초과 가능 (v3.4-2 step 4 의 0.6 sec/req 추정)
- coverage 98% (step 4 fill rate 일관)
- → ❌ rate limit + latency 문제로 채택 불가

#### C. cache-first (코덱스 권장)
- artwork_id 단위 in-memory LRU cache (TTL 7d, capacity 50K)
- cache hit → ≤5 ms, miss → ≤600 ms
- v3.4-2 step 4 의 saatchi raw 30,607 작품 / 약 800 작가 → cache 채워질수록 hit rate 상승
- 평균 latency 추정 = `hit_rate × 5ms + (1 - hit_rate) × 600ms`
  - 50% hit → ~302 ms
  - 80% hit → ~124 ms
  - 95% hit → ~35 ms
- → ✅ **채택**. 단 hit rate 는 **측정 후 검증** (코덱스 P1 — 추정치 X)

#### D. async backfill (preload)
- saatchi 21,087 row 를 background 에서 미리 fetch → cache 사전 채움
- p95 latency +0 ms (모두 cache hit)
- 비용: background worker + DB 영구 cache + preload schedule
- 복잡도 큼, v3.5 scope 밖
- → v3.6+ optimization backlog (step 2 §10)

#### E. manual-only (year_made client 직접 제공)
- PredictRequest 의 `year_made` 만 사용 (enrichment X)
- p95 latency +0 ms
- coverage = client 가 year_made 제공한 비율 (saatchi UI 통합 시 ≥80% 추정, public API 사용 시 <10%)
- → 부분 적용 (manual override 우선, fallback 으로 cache-first)

### 2.2 결정: cache-first + manual override

```
year_made 결정 우선순위 (V_year_saatchi_warm gating 통과 후):
1. req.year_made (manual, client 제공) → 우선 사용
2. cache hit → 즉시 사용
3. cache miss → fetch (≤600 ms p95)
4. fetch fail → fallback 0/0/0
```

→ 시나리오 C + E hybrid. step 2 spec 의 flow (§3) 와 정합.

### 2.3 Manual override cache 정책 (코덱스 P1 fix)

**채택**: **valid manual year = cache write-through**.

이유:
- manual year_made 가 client 측에서 검증된 (saatchi UI 통합 등) 정확한 값일 가능성 높음
- artwork_id 또는 artwork_url 이 함께 제공되면 cache 등록 가치 있음 (다른 요청 시 hit)
- 충돌 시 truth: **manual override = same-source-of-truth as fetched**. 동일 artwork_id 의 cache hit 가 있어도 manual 우선 사용 (단 cache 갱신 X — race 회피)

**규칙**:
1. `req.year_made` valid + `req.artwork_id` 제공 → 결과는 manual 사용 + cache write `(artwork_id → year_made, source='manual_seed')`
2. `req.year_made` valid + `req.artwork_id` 없음 → manual 사용 + cache write 없음
3. 동일 `artwork_id` 의 cache 와 manual 충돌 → manual 우선 사용, cache 항목은 그대로 유지 (다음 fetch 시 자연 갱신)

**근거**:
- 추후 fetch 비용 절감 (manual 이 seed 역할)
- TTL 7d 내 같은 artwork_id 재요청 시 immediate hit
- "manual = cache 등록 X" 가정 (이전 코덱스 review 답변) 은 **revoke**

---

## 3. Cache hit rate 측정 plan (코덱스 P1 — 추정 → 측정)

### 3.1 가정 / 추정 (검증 대상)
- saatchi raw 작품 수: 30,607 (전체) / 21,087 (학습 데이터)
- saatchi warm 작가: 약 521 명 (warm_artist_slugs ∩ saatchi 추정)
- 작품 별 fetch 빈도 분포: 알 수 없음 (production traffic 의존)
- 일반적인 art price API: 인기 작품에 traffic 집중 → Pareto 80/20 가설

**추정 hit rate**:
- 첫 1주: cache 채우는 단계 → hit rate 30~50% 추정
- 1주 후: 작품 누적 → 70~85% 추정
- 1개월 후: 80~95% (작품 lifecycle 도 고려)

→ **추정에 의존하지 말고 measure** (코덱스 권장).

### 3.2 측정 plan (rollout 5% 단계)

#### 3.2.1 logging schema (코덱스 P0 fix — version 분리 추가)
```json
{
  "request_id": "uuid",
  "timestamp": "2026-XX-XX HH:MM:SSZ",

  // 트래픽 분석
  "rollout_cohort": "treatment_5pct" | "control",
  "matched": true,
  "match_profile_source": "saatchi" | "artsy" | null,
  "slug_in_warm_set": true,
  "is_saatchi_warm": true,
  "external_collector_source": "saatchi" | "artsy" | "web" | "manual" | "none",
  "year_made_route": "manual" | "manual_seed_cache_write" | "cache_hit" | "fetch_ok" | "fetch_fail" | "no_id" | "parse_invalid" | "disabled" | "rate_limited",
  "year_made_used": 2020,
  "enrichment_latency_ms": 4.2,
  "predict_total_latency_ms": 78.5,
  "artwork_id": "13458973",
  "artwork_url": "https://www.saatchiart.com/art/.../view",

  // 배포/설정 분리 (코덱스 P0 — D7/D30 hit rate 해석에서 트래픽 변화 vs 설정 변화 분리)
  "model_variant": "v3_5_v_year_saatchi_warm",
  "artifact_version": "20260502_001",  // 모델 artifact build ID
  "warm_artist_slugs_version": "20260502_001",  // warm set artifact ID
  "rollout_rule_version": "5pct_v1",  // rollout 정책 버전
  "server_instance": "primary-server-pod-3",
  "cache_epoch": "20260502T0830Z"  // cold-restart 시 새 epoch (cache 영향 분리)
}
```

#### 3.2.2 측정 metrics
| Metric | 정의 | 목표 |
|--------|------|------|
| **cache_hit_rate** | `cache_hit / (cache_hit + fetch_ok + fetch_fail)` | rollout 1주 ≥50%, 1개월 ≥80% |
| **fetch_success_rate** | `fetch_ok / (fetch_ok + fetch_fail)` | ≥95% (saatchi 정상 응답률) |
| **enrichment_p95_latency_ms** | route 별 enrichment 단계 p95 | hit ≤5, miss ≤600 |
| **fallback_rate** | `(fetch_fail + parse_invalid + no_id + rate_limited) / total_eligible` | ≤5% |
| **rate_limited_rate** | `rate_limited / total_eligible` | < 1% (정상 운영). 1% 초과 시 traffic burst / saatchi 응답 지연 진단 |
| **manual_override_rate** | `manual / is_saatchi_warm_eligible` | (client 측정, 정책 결정 input) |
| **disabled_rate** | `disabled / total_predict` | ≈ 1 - saatchi_warm_ratio (학습 데이터 기준 70% 가량) |

#### 3.2.3 Rate-limit 안전성 측정 (코덱스 P0 fix)

cache-first 가 cold start / cache flush / deploy 직후 짧은 구간에서 sync no-cache 처럼 동작 → saatchi rate limit 위험. 다음 metric 으로 검증:

| Metric | 정의 | 목표 | Rollout pause 임계 |
|--------|------|-----:|-------------------:|
| **miss_qps** | cache miss → fetch 시 1초당 발생 fetch 수 | < 0.5 qps (v3.4-2 step 4 의 0.88 req/s 안전 margin) | > 1.0 qps |
| **concurrent_fetch** | 동시 진행 중 fetch 수 (max) | < 5 | > 10 |
| **unique_artwork_miss_rate** | 5분 window 의 unique artwork miss 수 / 5분 window 의 전체 cache miss 수 | < 0.8 (낮을수록 cache hit 효율 좋음) | > 0.95 (= cache 의미 X) |
| **5min_miss_burst** | 5분 window 의 cumulative cache miss 수 | < 50 | > 200 |

**대응 정책**:
- `5min_miss_burst > 200` → **자동 fetch suspend** (5분 cool-down, fallback only)
- `miss_qps > 1.0` 지속 → rollout pause + saatchi 측 rate limit 확인
- cold start (server restart 직후 5분) → fetch rate cap 적용 (max 0.3 qps soft limit)

#### 3.2.4 측정 기간 (코덱스 P2 — D7 typo fix)
- **D1 (24h)**: cache 비어있는 cold start — 가장 noisy, rate-limit risk 최대
- **D7 (1주 누적)**: pareto 효과 검증, hit rate plateau 시점
- **D30 (1개월 누적)**: steady state hit rate 확정

#### 3.2.4 의사결정 기준
| Hit rate (1주 후) | 결정 |
|------:|------|
| ≥80% | cache-first 단독 충분, async preload 불필요 |
| 50~80% | cache-first 유지, async preload v3.6 backlog 검토 |
| <50% | async preload 우선순위 상향 (cache-first 만으론 latency 부담 큼) |

---

## 4. Latency budget 검증 plan

step 2 spec 에서 결정된 latency budget:
- cache hit p95 ≤ 5 ms
- cache miss p95 ≤ 600 ms

### 4.1 budget overshoot 임계
| 메트릭 | 목표 | 알림 임계 (rollout pause) |
|--------|-----:|-------------------------:|
| enrichment_p95 (hit) | 5 ms | > 20 ms |
| enrichment_p95 (miss) | 600 ms | > 1500 ms |
| total_predict_p95 (cache miss case) | < 800 ms | > 1200 ms |

### 4.2 saatchi 응답 시간 변동 모니터링
- v3.4-2 step 4 에서 0.88 req/s rate 안정 확인 (8.5h 동안)
- 단 시간대별 변동 가능 — rollout 중 saatchi 측 5xx spike 시 fallback rate 증가
- alert: `fetch_5xx_rate_per_5min > 5%` → 자동 cache-only mode 전환 (fetch 일시 중단)

---

## 5. Coverage trade-off 분석 — 초기 prior (D7 실측 후 재판정)

⚠️ **모든 수치는 학습 데이터/추정 기반의 초기 prior**. rollout gate 가 아니라 D7 실측 후 재계산 필요 (코덱스 P1 fix).

### 5.1 saatchi-warm cohort 의 coverage prior
- 학습 데이터 prior: 19,773 saatchi-warm rows / 28,376 total = **69.7%**
- production traffic 분포 다를 가능성 (unmatched 비율 / source mix / 시즌)
- D7 실측 `eligible_rate = is_saatchi_warm = True / total_predict` 으로 재계산

### 5.2 매칭 실패 영향 — 초기 prior (코덱스 P0 #2 / P1 약화)
- unmatched saatchi 요청: gating fail → year off (의도된 fallback)
- 추정 prior: unmatched 5% × eligible 70% ≈ **3.5% ROI 손실** (acceptable 가정)
- D7 실측 `unmatched_rate / matched_rate / external_collector_source 분포` 로 재계산
- 실측 후: unmatched 가 prior 보다 훨씬 높으면 (>15%) 채택 결정 재검토

### 5.3 enrichment fail 영향 — 초기 prior
- step 4 결과 (offline): 97.90% fill, 2.10% (443/21,087) 영구 5xx
- 영구 5xx 작품 → has_year_made=0, fallback OK
- 추정 prior: saatchi_warm 의 0.5% × cohort effect ≈ 0.005% ROI 손실 (무시 가능)
- D7 실측 `fallback_rate (production)` 로 재계산. step 4 fill rate 와 다를 수 있음 (시간대 / saatchi-side 변동)

### 5.4 Re-judgment plan (D7 실측 후)
| Prior | D7 실측 임계 | 채택 결정 영향 |
|-------|:-----------:|---------------|
| eligible_rate ~70% | < 50% | 채택 ROI 절반으로 축소 → step 4 SLA 재검토 |
| unmatched_rate ~5% | > 15% | unmatched fallback 정책 재검토 |
| fallback_rate ~0.5% | > 5% | saatchi-side 안정성 별도 조사 |
| manual_override_rate (unknown) | > 30% | manual cache write-through 효율 확인 |

---

## 6. Step 4 monitoring 으로 input

### 6.1 dashboard query 요구사항
step 4 monitoring 에서 다음 query 가 가능해야:

```sql
-- Daily: cache hit rate
SELECT
  DATE_TRUNC('day', timestamp) AS day,
  COUNT(*) FILTER (WHERE year_made_route = 'cache_hit') * 1.0
    / NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('cache_hit', 'fetch_ok', 'fetch_fail')), 0) AS cache_hit_rate,
  COUNT(*) FILTER (WHERE year_made_route = 'cache_hit') AS hits,
  COUNT(*) FILTER (WHERE year_made_route IN ('fetch_ok', 'fetch_fail')) AS attempts
FROM predict_logs
WHERE rollout_cohort = 'treatment_5pct'
GROUP BY day;

-- p95 latency by route
SELECT
  year_made_route,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY enrichment_latency_ms) AS p95
FROM predict_logs WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY year_made_route;

-- fallback rate (v3.6 PR10b: rate_limited 포함 — §3.2.2 정의 정합)
SELECT
  COUNT(*) FILTER (WHERE year_made_route IN ('fetch_fail', 'parse_invalid', 'no_id', 'rate_limited'))
    * 1.0 / NULLIF(COUNT(*) FILTER (WHERE is_saatchi_warm), 0) AS fallback_rate,
  -- rate_limited 만 별도 집계 (§3.2.2 의 rate_limited_rate)
  COUNT(*) FILTER (WHERE year_made_route = 'rate_limited')
    * 1.0 / NULLIF(COUNT(*) FILTER (WHERE is_saatchi_warm), 0) AS rate_limited_rate
FROM predict_logs WHERE timestamp > NOW() - INTERVAL '24 hours';
```

### 6.2 측정 후 의사결정
- D7 결과 → cache-first 단독 vs async preload 결정
- p95 미달 → SLA 재검증 또는 timeout 조정
- fallback rate >5% → saatchi-side 안정성 별도 조사

---

## 7. Step 3 success criterion 충족 여부

| Criterion (v3.5 plan §3) | 상태 | 근거 |
|--------------------------|:----:|------|
| Cache key (artwork_id) 결정 | ✅ | step 2 §2.2 + 본 문서 §2.2 |
| Cache hit rate 측정 plan 확정 | ✅ | §3.2 logging + dashboard query |
| Latency vs ROI trade-off 정량화 | ✅ | §2.1 4 시나리오 + §4 budget |

→ **v3.5 step 3 close 가능**.

---

## 8. v3.5 진행도

- ✅ Step 1: cohort gating ablation (V_year_saatchi_warm 채택)
- ✅ Step 2: serve-path integration spec
- ✅ **Step 3: enrichment trade-off + 측정 plan** ← 본 문서
- ⏭️ Step 4: gated rollout drift monitoring (upstream + downstream metrics 설계)

---

## 9. Step 4 진행 input

step 4 가 본 step 3 의 측정 plan 을 monitoring infra 로 변환:
- 본 step 3 의 logging schema → step 4 의 dashboard schema
- 본 step 3 의 hit rate / fallback / latency 임계 → step 4 의 알림 임계
- 본 step 3 의 의사결정 기준 (D7 결과 → cache-first vs async preload) → step 4 의 rollout gate

step 3 의 측정 plan 자체가 step 4 의 monitoring 설계의 60% 차지. step 4 는 이를 dashboard / alert / rollout state machine 으로 구체화.
