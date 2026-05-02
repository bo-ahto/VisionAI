# v3.6 Phase 2 — Alerting Configuration

v3.5 step 4 §4 (alert 임계 + escalation) + §3.3 (rollback / pause trigger 단일 표) 의 실 구현.

## 디렉토리

```
alerting/
├── README.md                       # 이 파일 — 운영 가이드
├── grafana_alerts.yaml             # Grafana Alerting v10+ provisioning (rule group)
├── grafana_contact_points.yaml     # Slack webhook + PagerDuty integration
└── grafana_notification_policies.yaml  # severity → channel 라우팅
```

## 전제

- Grafana 10+ (Alerting v2 / Unified Alerting)
- Datasource: PostgreSQL (predict_logs + sold_actuals + cohort_baselines, view v_d7_predict_sold_pairs)
- Datasource UID 가 `postgres-prod` 라고 가정 (실제 deploy 시 환경별 UID 로 치환)

## Severity 매핑 (§4.1)

| severity | 의미 | 대응 시간 | 채널 |
|----------|------|----------|------|
| **info** | 정상 범위 보고 | n/a | Slack `#ml-rollout` |
| **warn** | 임계 근접 | 30 분 | Slack `#ml-alerts` |
| **crit** | 즉시 대응 / rollback 검토 | 5 분 | Slack `#ml-alerts` + PagerDuty on-call |
| **rollback** | 자동 단계 후퇴 | 즉시 | Slack `#ml-alerts` + PagerDuty + post-mortem |

## Trigger 매핑 (§3.3)

7 rollback / pause trigger 가 각각 Grafana alert rule. Action enum (`TRIGGER_PAUSE` / `TRIGGER_ROLLBACK`) 은 alert label 으로 노출 → notification policy 가 channel 결정.

| Trigger | SQL (monitoring/sql/020_alert_rollback_triggers.sql) | severity | Grafana for: |
|---------|------------------------------------------------------|----------|--------------|
| 1. 5min_miss_burst > 200 | trigger_1 | crit (pause) | **5m** (5분 지속 명시) |
| 2. cohort_discrepancy > 5% | trigger_2 | crit (pause) | 10m |
| 3. mdape_d7_cold > 46% | trigger_3 | rollback | 1h |
| 4. treatment_vs_control > +1.0%p | trigger_4 | rollback | 1h |
| 5. fetch_success < 90% | trigger_5 | rollback | 1h |
| 6. cold_disabled_rate < 95% | trigger_6 | rollback | 30m |
| 7. valid_year_range_rate < 98% | trigger_7 | crit (pause) | 30m |

## Special alerts (코덱스 P1 fix 후속)

- **NO_BASELINE alert**: trigger_2 가 `action = 'NO_BASELINE'` 반환 시 — cohort_baselines 미설정 / 새 artifact_version row 누락 → operator 즉시 조치. severity `crit` (Slack + PagerDuty).
- **Trigger 1 for: 5m**: SQL 자체는 단발 평가 (5분 누적값). Grafana `for: 5m` 로 5분 연속 임계 초과 시에만 fire — spec "5분 지속" 정합 (PR14b' Trigger 1 주석 참조).

## 적용 방법 (Grafana provisioning)

```bash
# 1. Grafana 10+ /etc/grafana/provisioning/alerting/ 에 YAML 복사
cp monitoring/alerting/*.yaml /etc/grafana/provisioning/alerting/

# 2. env: SLACK_WEBHOOK_ML_ALERTS / SLACK_WEBHOOK_ML_ROLLOUT / PAGERDUTY_INTEGRATION_KEY 주입
# 3. Grafana 재시작 / SIGHUP
systemctl reload grafana-server
```

## Slack / PagerDuty 환경변수

| Var | 설명 |
|-----|------|
| `SLACK_WEBHOOK_ML_ROLLOUT` | `#ml-rollout` 채널 incoming webhook URL |
| `SLACK_WEBHOOK_ML_ALERTS`  | `#ml-alerts` 채널 incoming webhook URL |
| `PAGERDUTY_INTEGRATION_KEY` | PagerDuty service integration key |

env 미주입 시 Grafana 가 alert 발사 못함 (alert log 에 error). 운영자 deploy 단계 검증 필수.

## 검증 절차 (코덱스 권장)

1. Grafana provisioning 적용 후 7 alert rule 모두 `OK` state 인지 (UI: Alerting → Rules)
2. Test fire: trigger 별로 임계값 인위 조정 후 실 alert 받는지 확인 (Slack + PagerDuty)
3. NO_BASELINE alert: cohort_baselines table 비우고 → 1분 내 alert
4. Trigger 1 for:5m: miss_burst 임계 초과 후 4분 안에 resolve 시 fire 안 되는지

## 후속 PR

- **PR14d**: Grafana dashboard JSON (12 panel) — 동일 datasource 사용
- **PR14e**: drift scenarios playbook (6) — alert 발사 시 운영자 절차

## 관련 문서

- spec: `docs/v3_5_step4_drift_monitoring.md` §3.3 + §4
- SQL: `monitoring/sql/020_alert_rollback_triggers.sql`
- baseline table: `monitoring/sql/003_cohort_baselines.sql`
