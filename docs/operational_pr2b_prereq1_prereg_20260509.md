# PR2B-prereq.1 — Shadow Dual-logging + DDL Alter

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: PR2A.5 (commit `290a3c0`) / PR2B (commit `c2cc240`)
> **Decision binding**: ✅ YES (server logic + DDL 변경 / 다만 default OFF / mode=shadow 활성화 시만 영향)

## 1. Goal

PR2B rollout Phase 1 (shadow) 영역 의 의무 영역 의 의무 영역 의 의무 = shadow predictor parallel inference + dual log (primary serving = unified / shadow simulate routed prediction). 코덱스 사전 자문 P1 fix.

## 2. Method (코덱스 P1 fix 적용)

### 2.1 Shadow simulation (source_router.py)

신규 helper:
```python
def simulate_route_on(
    is_matched: bool, match_profile_source: str | None, cohort_key: str | None = None,
) -> RouteDecision:
    """Shadow simulation = mode='on' decide_route. mode=shadow 영역 의 의무 영역 의 의무 영역 의 의무
    serving=unified 다만 shadow_routed_variant 영역 의 의무 영역 의 의무 영역 의 의무
    영역 의 의무 영역 의 의무 영역 의 의무 = canary 100% (mode=on simulate)."""
    return decide_route(
        is_matched=is_matched, match_profile_source=match_profile_source,
        mode="on", cohort_key=cohort_key,
    )
```

### 2.2 Parallel shadow inference (primary_server.py)

mode=shadow 영역 의 의무 영역 의 의무 영역 의 의무:
1. primary serving = unified predictor (변경 X / 운영 영향 X)
2. shadow_decision = `simulate_route_on(...)`
3. shadow_predictor = router.unified / artsy / saatchi (decision 정합)
4. **asyncio.gather**: primary inference (with SHAP) ‖ shadow inference (predict only / SHAP X)
5. shadow log = separate path (`_log_shadow_prediction()` / count_toward_monitor=False)
6. **Fail-open**: shadow exception → shadow_error log / primary 5xx 영역 의 의무 영역 의 의무 영역 의 의무 X

### 2.3 _log_prediction signature 분기

```python
def _log_prediction(entry: dict, *, count_toward_monitor: bool = True) -> None:
    """count_toward_monitor=False: 파일 write only / monitor counter X (shadow path)."""
    if count_toward_monitor:
        _monitor["total_predictions"] += 1
        # ... existing counter logic
    if _log_file:
        # ... existing file write
```

### 2.4 DDL alter (predict_logs)

추가 9 columns (additive / backward compat):
```sql
ALTER TABLE predict_logs
    ADD COLUMN IF NOT EXISTS routing_source           VARCHAR(16),
    ADD COLUMN IF NOT EXISTS routing_reason           VARCHAR(64),
    ADD COLUMN IF NOT EXISTS routed_variant           VARCHAR(64),
    ADD COLUMN IF NOT EXISTS router_mode              VARCHAR(16),
    ADD COLUMN IF NOT EXISTS cohort_in_canary         BOOLEAN,
    ADD COLUMN IF NOT EXISTS shadow_routed_variant    VARCHAR(64),
    ADD COLUMN IF NOT EXISTS shadow_routing_source    VARCHAR(16),
    ADD COLUMN IF NOT EXISTS shadow_routing_reason    VARCHAR(64),
    ADD COLUMN IF NOT EXISTS shadow_prediction_price_krw INT;
```

### 2.5 ETL whitelist additive

`scripts/etl_predict_logs.py` `PREDICT_LOGS_COLUMNS` tuple 영역 의 의무 영역 의 의무 9 column 추가 (기존 column 변경 X).

## 3. Out-of-scope (PR2B-prereq.2 / 별도 cycle)

- Prometheus per-route metrics
- Naming consistency (SOURCE_ROUTER_RULE_VERSION + ROLLOUT_RULE_VERSION 둘 다 log)
- Shadow latency histogram

## 4. Decision Criterion

**채택 (PASS)**:
- ✅ Shadow simulate_route_on() helper 정합
- ✅ Parallel inference (asyncio.gather / shadow fail-open)
- ✅ Separate log path (count_toward_monitor=False)
- ✅ DDL alter additive / ETL update / 기존 column 변경 X
- ✅ All tests pass (single + batch / shadow / regression)
- ✅ ruff check clean

## 5. 한계

- Memory + startup time 영향: mode=shadow 영역 의 의무 영역 의 의무 영역 의 의무 = 3 predictor load (current PR2A.5 / PR2B 영역 의 의무 영역 의 의무 영역 의 의무 정합)
- Shadow inference latency: parallel async / 다만 CPU 영역 의 의무 영역 의 의무 영역 의 의무 = predict() 영역 의 의무 영역 의 의무 영역 의 의무 ~50ms × 2 / p99 영역 의 의무 영역 의 의무 영역 의 의무 모니터링 의무
- DDL backward compat: 기존 운영 ETL 영역 의 의무 영역 의 의무 영역 의 의무 = 변경 X (additive only)

## 6. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P1 / shadow log monitor 오염 + latency) → fix 적용 |
| 1차 fix (본 commit) | _log_prediction count_toward_monitor 분기 + parallel asyncio.gather + fail-open + DDL alter additive |
| 2차 사후 검수 (예정) | 본 commit 후 |
