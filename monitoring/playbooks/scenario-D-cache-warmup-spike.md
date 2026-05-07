# Scenario D — cache warm-up miss spike

**Severity**: crit (pause)
**Trigger**: T1 (`5min_miss_burst > 200`, 5m for)
**Spec**: `docs/v3_5_step4_drift_monitoring.md` §5.4

## Detection signals

- alert: T1 fire (`vai-trigger-1-miss-burst`)
- 일반적으로 deploy 직후 / server restart / cache flush 직후 5~10분에 발생.
- dashboard:
  - Panel 1 (cache_hit_rate) 임시 < 30%
  - Panel 6 (5min_miss_burst) > 200 spike
  - Panel 4 (miss_qps) 동시 spike
  - `/api/v1/monitor` 의 `fetch_gate.warmup_mode == true` (server start 후 5분 안)

## Immediate action (자동)

1. Server start 직후 첫 5min: `FetchGate` warmup mode 활성 (PR11b) — capacity=1,
   refill=0.3 qps. saatchi rate-limit 자동 보호.
2. consecutive_fails ≥ 5 시 cool_down 60s 활성 (circuit breaker).
3. T1 5분 지속 시 Slack `#ml-alerts` + PagerDuty (severity=crit, action=PAUSE).
4. fetch suspend (cache-only 5분) — spec §3.3 의 자동 정책.

## Immediate action (수동, 5분 내)

1. on-call 이 alert 확인 → 최근 deploy / restart timestamp 비교.
2. warmup mode 인지 확인:
   ```bash
   curl http://primary-server:8000/api/v1/monitor | jq .fetch_gate.warmup_mode
   ```
3. warmup 정상 → 정책대로 5분 대기, 자동 sustain mode 전환 후 회복.

## Diagnosis

**의도된 spike (정상)**:
- deploy 직후 5분 — warmup mode 자동 cap 으로 saatchi 보호되며 resolve.
- T1 alert 가 5분 안 resolve 면 정상 lifecycle.

**비정상 spike**:
- deploy 직후 X — 갑자기 traffic burst (예: 외부 client 의 batch job 시작).
- 1h 이상 지속 — cache hit rate 회복 안 됨 → cache 영구 손상 (TTL 임의 단축?
  artwork_year_cache singleton 누수?).

```sql
-- 1h 동안 cache hit rate trend
SELECT DATE_TRUNC('minute', timestamp) AS min,
    COUNT(*) FILTER (WHERE year_made_route = 'cache_hit') * 1.0 /
    NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('cache_hit','fetch_ok','fetch_fail')), 0)
        AS hit_rate
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1 ORDER BY 1;
```

회복 trend (점진 상승) 가 보여야 정상.

## Remediation

**A. 정상 lifecycle (deploy 직후)**
1. 자동: warmup mode → sustain mode 전환 후 cache 채워지면 hit_rate 회복.
2. 5~15분 대기 후 alert auto-resolve.

**B. 비정상 (1h 지속)**
1. 트래픽 패턴 검증: 갑작스런 외부 batch job? client 측 retry storm?
2. cache singleton 검증: `artwork_year_cache._global_cache` 가 reset 됐는지
   (process restart 흔적).
3. `MODEL_VARIANT` env / 새 deploy 가 cache key prefix 변경했는지.
4. async preload 우선순위 상향 (v3.6 backlog) — 신규 작업 trigger.

## Resolution

- T1 alert auto-resolve (5min_miss_burst < 100, 즉 회복).
- Panel 1 cache_hit_rate ≥ 50% 회복.

## Post-mortem

- **deploy 시점 spike 빈도**: deploy 별 정상 spike duration 평균 측정 → SLA 정의.
- **cache miss spike 1h 이상 지속한 case**: 트래픽 분석 + async preload backlog
  진입 결정.
- **warmup-mode duration 5분 이 적정**: 운영 데이터 1주 기준 재평가.
