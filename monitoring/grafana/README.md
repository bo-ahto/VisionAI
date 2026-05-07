# v3.6 Phase 2 — Grafana Dashboard

v3.5 step 4 §6.2 의 12 panel rollout dashboard.

## 파일

```
grafana/
├── README.md                            # 이 파일 — 적용 가이드
├── dashboards_provider.yaml             # provisioning provider config
└── dashboard_v3_6_rollout.json          # 12 panel dashboard JSON (uid=visionai-v3-6-rollout)
```

## Datasource UID 가정

- **PostgreSQL**: `postgres-prod` (Panel 1-4, 6-12)
- **Prometheus**: `prometheus-prod` (Panel 5 — concurrent_fetch_max from `/api/v1/metrics`)

운영 환경에서 datasource UID 가 다르면 `dashboard_v3_6_rollout.json` 의
`datasource.uid` 값을 sed 또는 별도 templating 으로 치환.

## 12 Panel 구성

| Panel | Type | Datasource | spec | 임계 |
|-------|------|------------|------|-----|
| 1. cache_hit_rate by hour (7d) | timeseries | postgres | §2.1 | D1≥30%, D7≥50%, D30≥80% |
| 2. p95 latency by route (5min) | table | postgres | §2.1 | hit≤5ms, miss≤600ms |
| 3. cohort discrepancy (24h) | table | postgres | §2.2 | <1% |
| 4. miss_qps (5min smoothed) | stat | postgres | §2.1 | <0.5, warn>1.0, crit>2.0 |
| 5. concurrent_fetch_max (1min) | timeseries | **prometheus** | §2.1 | <5, warn>10, crit>20 |
| 6. 5min_miss_burst | stat | postgres | §2.1 | <50, warn>100, crit>200 |
| 7. MdAPE D7 overall | table | postgres | §2.2 | ≤9.7% |
| 8. MdAPE D7 cold (cold protect) | table | postgres | §2.2 | ≤43%, crit>46% |
| 9. MdAPE D7 saatchi_online | table | postgres | §2.2 | ≤9.7% |
| 10. model_variant distribution | piechart | postgres | §2.3 | rollout % |
| 11. artifact_version consistency | table | postgres | §2.3 | 100% |
| 12. treatment vs control diff | stat | postgres | §2.2 | <-0.3%p target, crit>+1.0%p |

## 적용 절차

```bash
# 1. Provider config 복사 (dashboard 자동 reload)
cp monitoring/grafana/dashboards_provider.yaml \
   /etc/grafana/provisioning/dashboards/visionai-provider.yaml

# 2. Dashboard JSON 복사
mkdir -p /etc/grafana/provisioning/dashboards/visionai
cp monitoring/grafana/dashboard_v3_6_rollout.json \
   /etc/grafana/provisioning/dashboards/visionai/

# 3. Grafana SIGHUP 또는 restart
systemctl reload grafana-server
```

## 수정 절차 (UI 편집 차단됨)

provisioning 에 `allowUiUpdates: false` 적용 — git source-of-truth. dashboard
변경은 다음 절차:

1. JSON 파일 직접 수정 (또는 dev Grafana 에서 export)
2. PR + review
3. merge 후 deploy pipeline 이 production Grafana 에 자동 sync (30s)

## Alert wire-up

각 alert rule (monitoring/alerting/grafana_alerts.yaml) 의 `runbook`
annotation 이 dashboard panel link 가 아니라 playbook markdown 경로 (PR14e).
alert fire 시 Slack/PagerDuty payload 의 runbook URL 을 통해 운영자가
playbook + dashboard 둘 다 접근.

Dashboard panel 자체는 alert 와 직접 연결 안 됨 (dashboard query 와 alert query
가 동일 SQL 일 뿐). 운영자 trace 절차:
```
Slack alert → playbook → 해당 panel 식별 → Grafana 에서 24h trend 확인
```

## 검증 절차

1. `grafana-cli admin reset-admin-password` (또는 dev 인스턴스)
2. provisioning copy + reload
3. UI: Dashboards → "VisionAI / v3.6 Rollout" 폴더에 1 dashboard 확인
4. 각 panel query 가 datasource 응답 (test DB / dev 환경) 으로 결과 표시
5. Panel 5 가 Prometheus datasource 사용하는지 (icon 색 / 옆 panel inspect)
