# v3.6 Phase 2 — Drift Scenarios Playbook

v3.5 step 4 §5 의 6 drift scenarios 운영자 절차. Grafana alert 의 `runbook` annotation 이 이 markdown 파일들로 직접 link.

## scenario 매핑

| Scenario | Trigger | Severity | Playbook |
|----------|---------|----------|----------|
| A. parser drift | T7 (valid_year_range_rate < 98%) | crit (pause) | [scenario-A](scenario-A-parser-drift.md) |
| B. saatchi rate limit / blocking | T5 (fetch_success < 90%) | rollback | [scenario-B](scenario-B-saatchi-rate-limit.md) |
| C. cohort gating fail | T2/T6, T2a NO_BASELINE | crit/rollback | [scenario-C](scenario-C-cohort-gating-fail.md) |
| D. cache warm-up miss spike | T1 (5min_miss_burst > 200) | crit (pause) | [scenario-D](scenario-D-cache-warmup-spike.md) |
| E. model regression | T3 (cold > 46%), T4 (treatment-control > +1%p) | rollback | [scenario-E](scenario-E-model-regression.md) |
| F. artifact corruption / version skew | (없음 — fail-closed) | manual | [scenario-F](scenario-F-artifact-corruption.md) |

## 공통 절차

각 playbook 은 다음 구조를 가짐:

1. **Detection signals** — 감지 신호 (alert + dashboard panel)
2. **Immediate action** — 자동 (gate / state machine) + 수동 (5분 내)
3. **Diagnosis** — 원인 분석 (logs / Grafana / metrics)
4. **Remediation** — 복구 절차 (config rollback / artifact 교체 / saatchi-side 조사)
5. **Resolution** — 정상화 검증 (alert resolve / dashboard 회복)
6. **Post-mortem** — RCA + 재발 방지 (if applicable)

## 운영 절차

```
Slack/PagerDuty alert fire
   ↓ (annotation runbook URL)
playbook markdown
   ↓
Section "Diagnosis" 의 SQL / dashboard panel 식별
   ↓
Section "Remediation" 절차 수행
   ↓
alert resolve 확인 → Section "Resolution"
```

## Alert wire-up

`monitoring/alerting/grafana_alerts.yaml` 의 각 rule annotation:
```yaml
annotations:
  runbook: "monitoring/playbooks/scenario-A-parser-drift.md"
```

운영 deploy 단계에서 `monitoring/playbooks/` 를 GitHub blob URL 또는 internal
wiki 으로 변환하는 templating 도입 (PR14e+ 단계에서 정의).
