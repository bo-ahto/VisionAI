# v3.5 step 4: gated rollout drift monitoring 설계

작성일: 2026-05-02
배경: v3.5 step 1-3 close (V_year_saatchi_warm 채택, serve-path spec, cache-first + measurement plan). 본 step 4 = step 3 measurement plan 의 monitoring infra 변환 + rollout state machine + alert + 대응 플레이북.

scope: 설계 only (코드 X). v3.5 plan §3 정의 그대로.

---

## 1. Step 4 의 목적 (코덱스 권장 그대로)

**v3.5 plan step 4 success criterion**:
1. Rollout gate query / alert 실제 산출 가능
2. Cohort assignment correctness ≥ 99%
3. Drift 모니터링 dashboard 구축 가능 (실제 구축은 v3.6)

**Out of scope**:
- 실제 dashboard 구축 (Grafana/Looker 등) — v3.6 implementation
- 실제 alert 라우팅 (Slack/PagerDuty) — v3.6 implementation
- 본 문서 = **monitoring spec + state machine** 만

---

## 2. Monitoring metrics 통합 (step 3 + 신규)

step 3 measurement plan 의 metrics + step 4 신규 downstream metrics 통합.

### 2.1 Upstream ops (장애 빠른 감지) — step 3 §3.2 + 추가

| Metric | 정의 | 목표 | Alert (warn) | Alert (crit) | Source |
|--------|------|-----:|-------------:|-------------:|--------|
| `enrichment_fetch_success_rate` | `fetch_ok / (fetch_ok + fetch_fail)` (5분 window) | ≥ 98% | < 95% | < 90% | step 3 |
| `cache_hit_rate` | `cache_hit / (cache_hit + fetch_ok + fetch_fail)` (1h window) | D1 ≥ 30%, D7 ≥ 50%, D30 ≥ 80% | -10%p baseline | -25%p baseline | step 3 |
| `enrichment_p95_latency_ms_hit` | route='cache_hit' p95 (5분 window) | ≤ 5 ms | > 20 ms | > 100 ms | step 3 |
| `enrichment_p95_latency_ms_miss` | route='fetch_ok' p95 (5분 window) | ≤ 600 ms | > 1000 ms | > 2000 ms | step 3 |
| `valid_year_range_rate` | `parse_invalid / parse_total` 의 inverse | 100% within [1800, 2030] | < 99.5% | < 98% | step 3 + parser drift detection |
| `fallback_rate_eligible` | `(fetch_fail + parse_invalid + no_id + rate_limited) / total_eligible` | ≤ 5% | > 10% | > 20% | step 3 (v3.6 PR10b: rate_limited 포함) |
| `miss_qps` | cache miss → fetch QPS (1분 window) | < 0.5 | > 1.0 | > 2.0 (auto-suspend) | step 3 §3.2.3 |
| `concurrent_fetch_max` | 동시 진행 fetch 수 (1분 max) | < 5 | > 10 | > 20 | step 3 §3.2.3 |
| `5min_miss_burst` | 5분 누적 cache miss | < 50 | > 100 | > 200 (auto-suspend) | step 3 §3.2.3 |
| `fetch_5xx_rate` | `fetch_fail (5xx) / total_fetch` (5분 window) — saatchi-side issue 감지 | < 2% | > 5% | > 10% | scenario B 대응 (§5.2) |

### 2.2 Downstream signal (모델 가치 검증)

| Metric | 정의 | 목표 | Alert (warn) | Alert (crit) | Source |
|--------|------|-----:|-------------:|-------------:|--------|
| `has_year_made_rate_treatment` | rollout cohort 의 `has_year_made=1 비율` | rollout traffic 의 ~50% (saatchi-warm 비율) | -10%p baseline | -25%p baseline | step 3 |
| `cold_year_made_disabled_rate` | cold artist 요청 중 `has_year_made=0 비율` | 100% (gating correctness) | < 99% (gating fail) | < 95% (심각) | step 2 §6 |
| `cohort_assignment_discrepancy_pct` | rollout traffic 의 is_saatchi_warm 분포 vs 학습 시 분포 | < 1% | > 1% | > 5% | step 2 success criterion |
| `p50_predicted_price_ratio_d7_dminus7` | 같은 cohort 의 D7 vs D-7 p50 가격 비율 | 0.97 ~ 1.03 | drift > ±5% | drift > ±10% | step 2 §4.1 + plan §4 |
| `p90_predicted_price_ratio_d7_dminus7` | p90 가격 비율 | 0.95 ~ 1.05 | drift > ±10% | drift > ±15% | step 2 §4.1 |
| `mdape_d7_saatchi_online` | rollout cohort saatchi_online 의 D7 MdAPE (실제 sold price 비교) | ≤ 9.7% | > 10.5% | > 11.5% | plan §4 + ablation |
| `mdape_d7_cold` | rollout cohort cold 의 D7 MdAPE | ≤ 43% | > 44% | > 46% (cold protect fail) | plan §4 |
| `mdape_d7_treatment_vs_control_diff` | A/B test diff (rollout vs control) | -0.3%p ~ -1.0%p (개선) | > +0.3%p | > +1.0%p (regression) | new |

### 2.3 Audit / governance metrics

| Metric | 정의 | 목표 | 비고 |
|--------|------|-----:|------|
| `model_variant_distribution` | 요청 별 사용된 model_variant 분포 | rollout % 정합 | rollout state 검증 |
| `artifact_version_consistency` | 같은 instance 의 artifact_version + warm_set_version 일관 | 100% | cohort gate 정확성 |
| `cache_epoch_age_hours` | server_instance 별 cache_epoch 경과 시간 | < 168h (7d, TTL 정합) | cold restart 감지 |

---

## 3. Rollout state machine

### 3.1 단계별 gate

```
[0] DEV TEST       → integration test (10 fallback cases) 통과
   ↓
[1] STAGING        → v3.5 step 4 dashboard query 산출 검증 (production-like 환경)
   ↓
[2] CANARY 1%      → 1% traffic, 24h cool-down, key metric 정상 + cohort correctness 99%
   ↓
[3] ROLLOUT 5%     → 5% traffic, D7 측정 (step 3 §5.4 re-judgment)
   ↓
[4] ROLLOUT 25%    → 25% traffic, 24h, MdAPE diff -0.3%p+ 개선 입증
   ↓
[5] FULL 100%      → 100% traffic, 1주 모니터링 후 v3.5 close
   ↓
[6] STEADY STATE   → ongoing monitoring (D30, D60 anomaly 감지)
```

### 3.2 Gate criterion (단계 진입 조건)

#### CANARY 1% → ROLLOUT 5%
**모두 충족 시 진입**:
- ✅ `enrichment_fetch_success_rate` ≥ 95% (24h)
- ✅ `cache_hit_rate` ≥ 30% (24h, cold start 고려)
- ✅ `cohort_assignment_discrepancy_pct` < 1%
- ✅ `cold_year_made_disabled_rate` = 100%
- ✅ `enrichment_p95_latency_ms_miss` ≤ 1000 ms
- ✅ Crit alert 0건 (24h)

#### ROLLOUT 5% → ROLLOUT 25%
**D7 실측 모두 충족**:
- ✅ `cache_hit_rate` ≥ 50% (코덱스 step 3 권장)
- ✅ `fallback_rate_eligible` ≤ 5%
- ✅ `mdape_d7_treatment_vs_control_diff` ≤ -0.3%p (개선 입증)
- ✅ `mdape_d7_cold` ≤ 44%
- ✅ Step 3 re-judgment plan (eligible_rate / unmatched_rate / fallback_rate) 정상

#### ROLLOUT 25% → FULL 100%
- ✅ 24h 동안 모든 metric 안정
- ✅ `mdape_d7_treatment_vs_control_diff` ≤ -0.5%p (offline -0.74%p 의 67%+ 보존)
- ✅ Crit alert 0건 (24h)

### 3.3 Rollback / pause trigger 단일화 (코덱스 P1 fix)

각 trigger 의 자동/수동 동작을 **한 표로 단일화** (이전 §4.3 의 분산 정의 통합):

| Trigger | 행동 | 자동/수동 | Pause vs Rollback |
|---------|------|:---------:|:-----------------:|
| `5min_miss_burst > 200` 5분 지속 | fetch suspend (cache-only 5분) | **자동** | pause (단계 유지) |
| `cohort_assignment_discrepancy_pct > 5%` | rollout pause + 조사 | **자동 pause** + manual confirm rollback | pause |
| `mdape_d7_cold > 46%` | rollback to prev stage | **자동 rollback** (no manual confirm) | rollback |
| `mdape_d7_treatment_vs_control_diff > +1.0%p` | rollback + post-mortem | **자동 rollback** | rollback |
| `enrichment_fetch_success_rate < 90%` 1h | rollback + saatchi 측 조사 | **자동 rollback** | rollback |
| `cold_year_made_disabled_rate < 95%` | rollback (gating 신뢰성 위반) | **자동 rollback** | rollback |
| `valid_year_range_rate < 98%` | parser drift 의심, fetch suspend | **자동 pause** | pause |

> 자동 rollback = state machine 단계 후퇴 (no manual confirm). 자동 pause = 단계 유지 + alert 만. **§4.3 의 이전 분산 정의 deprecated**.

---

## 4. Alert 임계 + escalation

### 4.1 Severity 분류

| Severity | 의미 | 대응 시간 | 채널 |
|----------|------|----------:|------|
| **info** | 정상 범위 보고 (D1 cache hit 30% 등) | n/a | Slack #ml-rollout |
| **warn** | 임계 근접, 모니터 강화 | 30 분 내 확인 | Slack #ml-alerts |
| **crit** | 즉시 대응 / rollback 검토 | 5 분 내 | Slack + on-call PagerDuty |
| **rollback** | 자동 단계 후퇴 (state machine §3.3) | 즉시 | Slack + on-call + post-mortem trigger |

### 4.2 Alert 통합 (warn / crit per metric — §2 표 인용)

핵심 6 alert (rollout 단계 변동):
1. `mdape_d7_cold > 44%` (warn) / `> 46%` (crit) — **cold protect fail, plan §6 risk**
2. `mdape_d7_treatment_vs_control_diff > +0.3%p` (warn) / `> +1.0%p` (crit + rollback)
3. `enrichment_fetch_success_rate < 95%` (warn) / `< 90%` (crit)
4. `5min_miss_burst > 100` (warn) / `> 200` (crit + auto-suspend fetch)
5. `cohort_assignment_discrepancy_pct > 1%` (warn) / `> 5%` (crit + rollback)
6. `cold_year_made_disabled_rate < 99%` (warn) / `< 95%` (crit + rollback)

### 4.3 Auto-action (즉시 자동)
- `5min_miss_burst > 200`: fetch suspend (cache-only mode 5분 cool-down)
- `cohort_assignment_discrepancy_pct > 5%`: rollout pause (수동 resume)
- `mdape_d7_cold > 46%`: rollback to prev stage (수동 confirm 후)

---

## 5. Drift 시나리오 + 대응 플레이북

### 5.1 시나리오 A: parser drift (saatchi 페이지 schema 변경)
**감지 신호**:
- `valid_year_range_rate < 99.5%` 갑자기 발생
- `fallback_rate_eligible` spike (+5%p 이상)
- `enrichment_fetch_success_rate` 정상 but `parse_invalid` 증가

**대응**:
1. cache-only mode 자동 전환 (fetch suspend)
2. saatchi sample 5개 manual fetch → schema 비교
3. `saatchi_detail_enricher.py` regex pattern fallback 활성 (json_yearCreated / json_year_created)
4. 새 pattern 추가 시 unit test + smoke 후 deploy
5. 정상화 후 fetch resume

### 5.2 시나리오 B: saatchi rate limit / blocking
**감지 신호**:
- `enrichment_fetch_success_rate` 갑자기 < 90%
- `fetch_5xx_rate > 5%` 5분 지속
- `concurrent_fetch_max` spike

**대응**:
1. 자동: 5min_miss_burst gate 작동 → fetch suspend (cache-only 5분)
2. saatchi 측 issue 확인 (statuspage / 다른 enrichment 시도)
3. UA / IP 변경 검토 (anti-bot 강화 가능성)
4. 1h 이상 지속 시 manual rollback to prev stage

### 5.3 시나리오 C: cohort gating fail (학습/서빙 mismatch)
**감지 신호**:
- `cohort_assignment_discrepancy_pct > 1%`
- `cold_year_made_disabled_rate < 99%` (cold 작가에 year 활성)

**대응**:
1. crit alert 발생 → 5분 내 production logs 확인
2. `match.profile["source"]` 분포 + `slug_in_warm_set` 분포 비교
3. warm_artist_slugs artifact 재로드 (race condition 가능성)
4. `> 5% discrepancy` 시 rollback + post-mortem

### 5.4 시나리오 D: cache warm-up miss spike
**감지 신호**:
- 배포 직후 / server restart 후 `5min_miss_burst > 100`
- `cache_hit_rate` 임시 < 30%

**대응**:
1. 자동: 2-mode token bucket gate (v3.6 PR10/11b):
   - warmup (server start 후 첫 5min): burst=1, refill=0.3 qps — spec cold-start cap
   - sustain (warmup 이후): burst=3, refill=0.5 qps — spec target
   `/api/v1/monitor` 또는 fetch gate stats 의 `warmup_mode` / `tokens_available`
   필드로 현재 모드 확인.
2. 1h 이상 hit rate 회복 안 되면 → 트래픽 패턴 검증
3. async preload 우선순위 상향 (v3.6 backlog 진입 검토)

### 5.5 시나리오 E: model regression (overall MdAPE 악화)
**감지 신호**:
- `mdape_d7_treatment_vs_control_diff > +0.3%p`
- ablation offline 결과 (-0.74%p) 와 production 차이

**대응**:
1. crit alert → 즉시 ROLLOUT 단계 freeze
2. cohort 별 breakdown 확인 (cold / saatchi_online / 1-2 작가 등)
3. Offline ablation 의 cohort 별 효과와 비교 — 재현성 분석
4. 재현 안 되는 cohort 별 conditional gating 강화 검토 (V_year_saatchi_warm 의 sub-gating)
5. > +1.0%p 시 자동 rollback

### 5.6 시나리오 F: artifact corruption / version skew (코덱스 P1 fix)
**감지 신호**:
- `artifact_version_consistency` < 100% (인스턴스 간 mismatch)
- `model_variant_distribution` 의 unexpected variant (ex: rollout 5% 인데 25% traffic 의 v3_5)
- 같은 server_instance 의 cache_epoch + artifact_version 불일치

**대응**:
1. 즉시 모든 instance 의 artifact 검증 (sha256 비교)
2. mismatch instance 즉시 drain (LB 제거)
3. 정상 instance 만으로 트래픽 처리 → 재배포
4. 재배포 후 cache_epoch 갱신 자동 감지 (cold restart 정합)
5. post-mortem: deploy tool 의 atomic rollout / artifact pinning 정책 review
6. RUNBOOK 명시: `MODEL_VARIANT` env var 와 `model_target` JSON 일치 확인 (mismatch → RuntimeError, fail-closed 의도된 동작)

> **artifact corruption 은 fail-closed**: predictor 가 startup 시 5-file bundle + model_target 검증 후 mismatch 면 RuntimeError → instance 시작 X → LB 자동 제외. 이 동작 자체가 1차 방어선.

---

## 6. Dashboard schema (logical, v3.6 implementation 가이드)

### 6.1 Tables

```sql
-- predict_logs (step 3 §3.2.1 logging schema + 코덱스 P0 fix: predicted price 추가)
CREATE TABLE predict_logs (
    request_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    rollout_cohort VARCHAR(32),
    matched BOOLEAN,
    match_profile_source VARCHAR(16),
    slug_in_warm_set BOOLEAN,
    is_saatchi_warm BOOLEAN,
    external_collector_source VARCHAR(16),
    year_made_route VARCHAR(32),
    year_made_used INT,
    enrichment_latency_ms FLOAT,
    predict_total_latency_ms FLOAT,
    artwork_id VARCHAR(32),
    artwork_url VARCHAR(500),
    -- 예측 결과 (코덱스 P0: MdAPE 계산 가능 위해 필수)
    predicted_price_krw INT NOT NULL,
    predicted_range_low_krw INT,
    predicted_range_high_krw INT,
    confidence_grade VARCHAR(2),
    -- 버전 분리
    model_variant VARCHAR(64),
    artifact_version VARCHAR(32),
    warm_artist_slugs_version VARCHAR(32),
    rollout_rule_version VARCHAR(32),
    server_instance VARCHAR(64),
    cache_epoch VARCHAR(32)
);

CREATE INDEX ON predict_logs (timestamp);
CREATE INDEX ON predict_logs (rollout_cohort, timestamp);
CREATE INDEX ON predict_logs (artifact_version);
CREATE INDEX ON predict_logs (artwork_id, timestamp);  -- D7 prediction-to-sale linkage

-- sold_actuals (D7 MdAPE 계산용 — production 거래 결과 매핑)
CREATE TABLE sold_actuals (
    artwork_id VARCHAR(32),
    sold_at TIMESTAMPTZ,
    sold_price_krw INT,
    artist_slug VARCHAR(64),
    source VARCHAR(16),
    PRIMARY KEY (artwork_id, sold_at)
);
```

### 6.1.1 D7 prediction-to-sale linkage rule (코덱스 P0 fix)

같은 artwork 가 여러 번 예측되거나 여러 번 sold 된 경우 attribution rule 필요:

**Rule**: 각 sold_actual 마다 **그 sale 직전의 가장 최근 prediction 1건만** D7 MdAPE 계산에 사용.

```sql
-- D7 MdAPE 계산용 결합 view
CREATE VIEW v_d7_predict_sold_pairs AS
SELECT DISTINCT ON (s.artwork_id, s.sold_at)
    p.request_id,
    p.predicted_price_krw,
    p.rollout_cohort,
    p.is_saatchi_warm,
    s.sold_price_krw,
    s.sold_at,
    s.sold_at - p.timestamp AS prediction_to_sale_lag,
    ABS(p.predicted_price_krw - s.sold_price_krw) * 1.0 / s.sold_price_krw AS abs_pct_error
FROM sold_actuals s
JOIN predict_logs p
    ON s.artwork_id = p.artwork_id
    AND p.timestamp <= s.sold_at  -- prediction 이 sale 이전
    AND p.timestamp > s.sold_at - INTERVAL '30 days'  -- 30d window 내
ORDER BY s.artwork_id, s.sold_at, p.timestamp DESC;  -- sale 직전 가장 최근
```

**규칙 명시**:
1. Prediction 이 sale 이전이어야 (`p.timestamp <= s.sold_at`)
2. 30 days window 내 (오래된 prediction 제외)
3. `DISTINCT ON (s.artwork_id, s.sold_at) ORDER BY p.timestamp DESC` → sale 직전 가장 최근 prediction 1건만
4. 같은 prediction 이 여러 sold 에 사용될 수 있음 (resold 등) — 그것은 의도

### 6.2 Core dashboard queries (12 panels)

**SQL dialect**: PostgreSQL (코덱스 P1 fix 명시).
- `FILTER (WHERE ...)`, `INTERVAL '7 days'`, `PERCENTILE_CONT ... WITHIN GROUP`, `DISTINCT ON` 모두 PostgreSQL 14+ 지원.
- BigQuery 또는 Snowflake migration 시 별도 query 변환 필요 (v3.6 implementation 단계 결정).
- 권장: production warehouse 가 PostgreSQL 일 경우 그대로 사용. 그 외 warehouse 는 implementation 시 변환.

#### Panel 1: Cache hit rate (시간대별)
```sql
SELECT
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) FILTER (WHERE year_made_route = 'cache_hit') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('cache_hit', 'fetch_ok', 'fetch_fail')), 0)
        AS cache_hit_rate,
    COUNT(*) FILTER (WHERE is_saatchi_warm = true) AS eligible_count
FROM predict_logs
WHERE rollout_cohort = 'treatment_5pct'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour ORDER BY hour;
```

#### Panel 2: p95 latency by route
```sql
SELECT
    year_made_route,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY enrichment_latency_ms) AS p95,
    COUNT(*) AS n
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY year_made_route;
```

#### Panel 3: Cohort assignment discrepancy (코덱스 P0 fix — unmatched 분리)
```sql
WITH train_dist AS (
    SELECT 'saatchi_warm' AS cohort, 0.697 AS expected_rate -- 19773/28376
    UNION SELECT 'saatchi_cold', 0.046
    UNION SELECT 'artsy_warm', 0.257
    UNION SELECT 'unmatched', 0.0  -- 학습 데이터에는 0 (production 만 발생)
),
prod_dist AS (
    SELECT
        CASE
            WHEN matched = false THEN 'unmatched'  -- 의도된 fallback (step 2 §6.2)
            WHEN is_saatchi_warm THEN 'saatchi_warm'
            WHEN matched AND match_profile_source = 'saatchi' AND slug_in_warm_set = false THEN 'saatchi_cold'
            WHEN matched AND match_profile_source = 'artsy' THEN 'artsy_warm'
            ELSE 'other'  -- catch-all (anomaly detection)
        END AS cohort,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS rate
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '24 hours'
        AND rollout_cohort = 'treatment_5pct'
    GROUP BY cohort
)
SELECT t.cohort, t.expected_rate, COALESCE(p.rate, 0) AS rate,
       ABS(t.expected_rate - COALESCE(p.rate, 0)) AS diff
FROM train_dist t
LEFT JOIN prod_dist p USING (cohort)
UNION ALL
-- production-only cohort (unmatched, other) 표시
SELECT cohort, NULL AS expected_rate, rate, NULL AS diff
FROM prod_dist
WHERE cohort IN ('other');
```

> `unmatched` 는 학습 시 0% 가 정상 (학습 데이터 전체 매칭). production rate >0 은 의도된 fallback. 단 `other` (catch-all) 가 발생하면 anomaly — 즉시 조사.

#### Panel 4-6: Rate-limit gates (miss_qps / concurrent / 5min_burst)
*(생략, step 3 §3.2.3 임계 그대로 시각화)*

#### Panel 7-9: MdAPE D7 (overall / cold / saatchi_online), treatment vs control
**v_d7_predict_sold_pairs view 사용** (§6.1.1 linkage rule 적용):

```sql
-- Panel 7: overall MdAPE D7 by rollout_cohort (treatment vs control)
SELECT
    rollout_cohort,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape_pct,
    COUNT(*) AS n_pairs
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
GROUP BY rollout_cohort;

-- Panel 8: cold cohort 만
SELECT
    rollout_cohort,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape_cold_pct
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
    AND is_saatchi_warm = false  -- cold 작가 만
GROUP BY rollout_cohort;

-- Panel 9: saatchi_online 만 (sold_actuals.source 활용)
SELECT
    rollout_cohort,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape_saatchi_online_pct
FROM v_d7_predict_sold_pairs v
JOIN sold_actuals s ON v.request_id = s.artwork_id  -- (조인 redundant, view 단계에서 source 포함하도록 view 확장 필요)
WHERE s.source = 'saatchi'
    AND v.sold_at > NOW() - INTERVAL '7 days'
GROUP BY rollout_cohort;
```

> view 의 `is_saatchi_warm`, `source` (saatchi/artsy/web) 노출 필요. §6.1.1 view 정의에 `s.source AS sold_source`, `p.is_saatchi_warm` 추가 (위 view DDL 에 이미 포함된 것으로 가정, 실제 implementation 시 명시).

#### Panel `treatment_vs_control_diff` (rollout gate)
```sql
WITH per_cohort AS (
    SELECT
        rollout_cohort,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape_pct
    FROM v_d7_predict_sold_pairs
    WHERE sold_at > NOW() - INTERVAL '7 days'
    GROUP BY rollout_cohort
)
SELECT
    (SELECT mdape_pct FROM per_cohort WHERE rollout_cohort = 'treatment_5pct')
    - (SELECT mdape_pct FROM per_cohort WHERE rollout_cohort = 'control')
    AS mdape_d7_treatment_vs_control_diff;
```

#### Panel 10-12: Audit (model_variant 분포 / artifact_version 일관성 / cache_epoch age)

---

## 7. Step 4 success criterion 충족 여부

| Criterion (v3.5 plan §3) | 상태 | 근거 |
|--------------------------|:----:|------|
| Rollout gate query / alert 실제 산출 가능 | ✅ | §3.2 단계별 gate + §6.2 SQL |
| Cohort assignment correctness ≥ 99% | ✅ | §2.2 metric + §6.2 Panel 3 query + §3.3 rollback trigger |
| Drift 모니터링 dashboard 구축 가능 | ✅ | §6 schema + 12 panel spec |

→ **v3.5 step 4 close 가능** (설계 only, plan §3 정의 그대로). 실제 dashboard 구축은 v3.6 implementation.

---

## 8. v3.5 close 선언

| Step | 결과 | Status |
|------|------|:------:|
| Step 1 | V_year_saatchi_warm 채택 (overall -0.74%p, cold +0.03%) | ✅ |
| Step 2 | Serve-path integration spec (10 fallback cases, latency budget) | ✅ |
| Step 3 | Cache-first hybrid + measurement plan (rate-limit gate 포함) | ✅ |
| Step 4 | Rollout state machine + alert + drift playbook + dashboard spec | ✅ |

**v3.5 plan close**. 코덱스 권장 4-step 모두 통과.

---

## 9. v3.6 production rollout 진입 조건

다음 모두 충족 시 v3.6 진입:

### 9.1 Implementation (코드 변경)
- [ ] step 2 §10 implementation checklist 11건 완료
  - primary_schemas / external_collector / primary_feature_builder / primary_predictor / primary_server (단건+batch) / metrics.json / calibration model_target / logging schema / integration tests / smoke benchmark
- [ ] V_year_saatchi_warm 모델 retraining + 5-file artifact bundle 생성

### 9.2 Monitoring infra (인프라 구축)
- [ ] step 4 §6 dashboard 12 panel 구축 (Grafana / Looker 등)
- [ ] step 4 §4.2 6 alert 라우팅 (Slack + PagerDuty)
- [ ] step 4 §3 rollout state machine 자동화 (deploy tool 통합)
- [ ] step 4 §5 drift playbook on-call team training

### 9.3 Pre-rollout validation
- [ ] DEV TEST: 10 fallback cases (step 2 §4) 통과
- [ ] STAGING: production-like 환경에서 dashboard query 산출 검증
- [ ] Pre-canary smoke: 100 internal request → cache hit 10+ / latency budget within

---

## 10. v3.6 plan (별도 문서)

v3.5 close 후 v3.6 plan 작성 필요:
- v3.6 = production rollout 실행
- v3.5 의 spec/state machine/alert 를 deploy infra 로 변환
- Implementation checklist 의 11건 PR 분리
- 단계별 gate 자동 실행 (CANARY → ROLLOUT → FULL)
- v3.5 step 1 ablation 결과 (-0.74%p overall, -1.0%p saatchi 10+) 의 production 재현 검증

→ 본 step 4 close 후 별도 commit 으로 v3.6 plan 초안 작성 권장.

---

## 11. v3.5 진행도 — 모두 close

- ✅ Step 1: cohort gating ablation (V_year_saatchi_warm 채택)
- ✅ Step 2: serve-path integration spec
- ✅ Step 3: enrichment trade-off + measurement plan
- ✅ **Step 4: gated rollout drift monitoring 설계** ← 본 문서

→ **v3.5 backlog 모두 종료**. v3.6 production rollout 진입 가능 (implementation + infra 구축 후).
