# v3.6 Prometheus Scrape (Panel 5 concurrent_fetch_max)

v3.5 step 4 §3.2.3 의 `concurrent_fetch_max` (1min max) metric 을 Prometheus 로 측정.
PostgreSQL 기반 SQL metric 은 instant 값을 잡기 어렵기 때문에 server runtime 에서 직접 노출.

## 흐름

```
┌──────────────┐  GET /api/v1/metrics  ┌─────────────┐    PromQL   ┌─────────┐
│ FastAPI      │ ────────────────────→ │ Prometheus  │ ──────────→ │ Grafana │
│ /api/v1/     │   PlainText (15s)     │ (scrape)    │             │ Panel 5 │
│ metrics      │                        └─────────────┘             └─────────┘
└──────────────┘
        ▲
        │ get_global_gate().stats()
        │ _monitor[...]
```

## endpoint 형식

`GET /api/v1/metrics` → `text/plain; version=0.0.4` (Prometheus exposition format).

11 metric (gauge 8 + counter 3):
- `visionai_fetch_gate_concurrent` (gauge)
- `visionai_fetch_gate_miss_5min` (gauge)
- `visionai_fetch_gate_consecutive_fails` (gauge)
- `visionai_fetch_gate_cool_down_remaining_sec` (gauge)
- `visionai_fetch_gate_tokens_available` (gauge)
- `visionai_fetch_gate_inflight` (gauge)
- `visionai_fetch_gate_warmup_mode` (gauge, 0/1)
- `visionai_fetch_gate_warmup_remaining_sec` (gauge)
- `visionai_predictions_total` (counter)
- `visionai_predictions_external_lookup_total` (counter)
- `visionai_predictions_known_artist_total` (counter)

모든 metric 의 label: `worker / server / variant`. multi-worker 환경에서 worker 별 분리 + Grafana variable 로 cohort 별 view.

## Grafana Panel 5 query

```promql
# 1min max — spec §2.1 concurrent_fetch_max 정의
max_over_time(visionai_fetch_gate_concurrent[1m])

# warm worker 수
count(visionai_fetch_gate_warmup_mode == 1)

# cool-down 중 worker 수 (alert 분기 가능)
count(visionai_fetch_gate_cool_down_remaining_sec > 0)
```

## 운영 적용

1. server: 별도 변경 없음 (FastAPI app 가 자동으로 `/api/v1/metrics` 노출)
2. Prometheus: `monitoring/prometheus/scrape_config.yaml` 의 scrape_configs 를 prometheus.yml 에 병합 (또는 ServiceMonitor / PodMonitor 로 변환)
3. Grafana: 동일 datasource UID 사용 (PR14d dashboard 의 Panel 5 로 wire-up)

## 의존성

server 측: 의존성 추가 X (단순 string format, `prometheus_client` 라이브러리 안 씀).
앞으로 metric 종류 늘면 `prometheus_client.exposition.generate_latest()` 도입 검토.
