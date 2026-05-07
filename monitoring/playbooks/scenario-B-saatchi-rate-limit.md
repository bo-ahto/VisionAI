# Scenario B — saatchi rate limit / blocking

**Severity**: rollback
**Trigger**: T5 (`enrichment_fetch_success_rate < 90%`, 1h for)
**Spec**: `docs/v3_5_step4_drift_monitoring.md` §5.2

## Detection signals

- alert: T5 fire (`vai-trigger-5-fetch-success`)
- dashboard:
  - Panel 4 (miss_qps) — fetch 시도는 정상 빈도
  - Panel 5 (concurrent_fetch_max) — saatchi 응답 지연으로 in-flight 증가
  - cool_down activation: `/api/v1/monitor` 의 `fetch_gate.cool_down_remaining_sec > 0`
- log: `year_made_route='fetch_fail'` rate > 10%

## Immediate action (자동)

1. consecutive_fails ≥ 5 → 60s cool-down 자동 활성 (PR8a circuit breaker).
2. cool-down 동안 새 fetch 차단, cache-only mode.
3. T5 fire (1h 지속) → Slack + PagerDuty (severity=rollback).
4. state machine 이 자동 rollback 단계 후퇴 (1% → previous, 5% → 1%).

## Immediate action (수동, 5분 내)

1. on-call 이 saatchi statuspage 확인 (https://status.saatchiart.com 또는
   third-party 모니터).
2. UA / IP 변경 가능성 확인 (`scripts/saatchi_detail_enricher.py:60` 의 DEFAULT_UA).
3. 다른 enrichment source (artsy / web search) 로 일시 우회 가능성 진단.

## Diagnosis

**1. fetch_fail 분포**:
```sql
SELECT
    DATE_TRUNC('minute', timestamp) AS min,
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_fail') AS n_fail,
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_ok') AS n_ok
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '2 hours'
GROUP BY 1 ORDER BY 1;
```

급격한 spike 면 saatchi 측 변경, 점진적 증가면 traffic 증가 의심.

**2. saatchi 직접 호출**:
```bash
curl -A "$DEFAULT_UA" -I https://www.saatchiart.com/art/.../view
# expected: 200 OK
# observed: 403 / 429 / Access Denied page → rate limit confirmed
```

**3. server `/api/v1/monitor` 의 fetch_gate 상태**:
```bash
curl http://primary-server:8000/api/v1/monitor | jq .fetch_gate
# concurrent / consecutive_fails / cool_down_remaining_sec 확인
```

## Remediation

**A. saatchi-side issue (단기)**
1. UA rotate 또는 graceful backoff — `FETCH_TIMEOUT_SEC` 늘리기 (1.5s → 3s
   임시).
2. `FETCH_QPS_REFILL_PER_SEC` 0.5 → 0.2 (sustain qps 절반).
3. config-only change (재배포 없이 env override) 후 1h 모니터링.

**B. saatchi block 지속 (1h+)**
1. manual rollback to prev stage (state machine).
2. saatchi 측 contact (sales / support) — IP whitelisting 요청.
3. 대안 enrichment source 우선순위 상향 (artsy fallback).

## Resolution

- T5 alert auto-resolve (fetch_success_rate ≥ 90% 회복).
- cool_down_remaining_sec 0 으로 회복.
- rolled-back state machine 단계에서 정상 운영 → 다음 ramp-up은 신중하게.

## Post-mortem

- **Saatchi 측 rate limit policy 변경 시점 확인**.
- **token bucket 임계 재조정**: 우리 traffic 이 spec 기준 허용 안에 있었는가?
- **재발 방지**: monitoring/playbooks/scenario-B 내 manual rollback 절차를
  state machine 자동 trigger 로 승격 검토.
