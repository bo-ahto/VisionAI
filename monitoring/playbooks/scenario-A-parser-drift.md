# Scenario A — saatchi parser drift

**Severity**: crit (pause)
**Trigger**: T7 (`valid_year_range_rate < 98%`, 30m for)
**Spec**: `docs/v3_5_step4_drift_monitoring.md` §5.1

## Detection signals

- alert: T7 fire (`vai-trigger-7-parser-drift`)
- dashboard:
  - Panel 2 (latency by route) 에서 `parse_invalid` row count 상승
  - Panel 3 (cohort discrepancy) 영향 가능 (year 활성 비율 떨어짐)
- sample log:
  ```
  year_made_route='parse_invalid' rate > 2% (1h)
  enrichment_fetch_success_rate 정상 (saatchi 응답 OK)
  ```

## Immediate action (자동)

1. T7 fire → Slack `#ml-alerts` + PagerDuty (severity=crit, action=TRIGGER_PAUSE).
2. saatchi fetch 자체는 계속 — parse 단계만 fail. fetch suspend X (parser 만 문제).

## Immediate action (수동, 5분 내)

1. on-call 이 alert 확인 (Slack 또는 PagerDuty incident).
2. `cohort_baselines` / `cache_epoch` / 최근 deploy 확인 — 우리 변경 측 가능성 차단.
3. saatchi 측 schema 변경 가능성 진단.

## Diagnosis

**1. parse_invalid sample 확인**:
```sql
SELECT request_id, artwork_id, artwork_url, timestamp
FROM predict_logs
WHERE year_made_route = 'parse_invalid'
    AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC
LIMIT 10;
```

**2. Manual fetch 5 sample**:
```bash
for url in $(...); do
    curl -s -A "$DEFAULT_UA" "$url" | grep -o 'yearCreated[^,]*' | head -3
done
```

기대 pattern: HTML `data-year-created`, JSON `"yearCreated": "..."`,
`"year_created": ...` 중 하나.

**3. 비교**:
- 기존 `saatchi_detail_enricher.py:55-65` 의 regex: `YEAR_CREATED_PATTERN`,
  `JSON_YEAR_CREATED_PATTERN`, `JSON_YEAR_CREATED_SNAKE_PATTERN`.
- 새 schema 가 위 pattern 으로 안 잡히면 → drift confirmed.

## Remediation

1. **즉시**: cache-only mode (fetch 일시 중단) 가 spec §5.1 권장이지만 PR16 의
   token bucket 으로 자연 backoff (consecutive_fails > 5 → cool_down 60s).
   alert 만 모니터링 중인 상태에서 즉각 우회 X.
2. **새 pattern 추가**: `scripts/saatchi_detail_enricher.py` 의 regex 에
   fallback 추가 (예: `data-year-published` 등 새 attribute).
3. **smoke test**: PR + unit test (`tests/test_saatchi_detail_enricher.py` 의
   sample HTML 5+ case 추가) → CI green.
4. **deploy**: standard release (rolling). 새 worker 부터 적용.

## Resolution

- T7 alert auto-resolve (valid_year_range_rate ≥ 98% 회복)
- Panel 2 의 parse_invalid 정상 0%
- Slack #ml-alerts 자동 resolve 메시지

## Post-mortem

- **Trigger 시점 식별**: deploy timestamp vs first parse_invalid spike.
- **Saatchi schema 변경 source 확인**: saatchi changelog / customer support.
- **재발 방지**: weekly automated `pytest tests/test_saatchi_detail_enricher.py`
  + saatchi sample (10개) regression — 5min_miss_burst 트리거 직전 알림.
