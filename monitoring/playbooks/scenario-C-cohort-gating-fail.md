# Scenario C — cohort gating fail (학습/서빙 mismatch)

**Severity**: crit (T2 pause) / rollback (T6) / crit (T2a NO_BASELINE)
**Trigger**: T2, T2a, T6
**Spec**: `docs/v3_5_step4_drift_monitoring.md` §5.3

## Detection signals

- **T2** (`vai-trigger-2-cohort-discrepancy`): `cohort_assignment_discrepancy_pct > 5%`, 10m for
- **T2a** (`vai-trigger-2a-no-baseline`): `cohort_baselines` 의 active artifact row 부재, 1m for
- **T6** (`vai-trigger-6-cold-disabled`): `cold_year_made_disabled_rate < 95%`, 30m for

dashboard:
- Panel 3 (cohort discrepancy) — train_dist vs prod_dist diff 확인

## NO_BASELINE 분기 (T2a) {#no-baseline}

**증상**: T2a fire — `cohort_baselines` 에 active artifact 의 row 없음.
discrepancy metric 자체를 계산 불가 → silent OK 차단 (PR14b'' fix).

**원인**:
1. **artifact build pipeline 누락**: 새 artifact_version deploy 했는데
   pipeline 이 `cohort_baselines` INSERT 안 함.
2. **새 variant 추가**: code 만 deploy + artifact_version 변경 + baseline 갱신 안 함.
3. **DB migration 누락**: `cohort_baselines` table 자체가 production 에 없음.

**즉시 대응**:
```bash
# 현재 active artifact 확인
psql -c "SELECT artifact_version, COUNT(*) FROM predict_logs
         WHERE timestamp > NOW() - INTERVAL '1 hour'
             AND rollout_cohort = 'treatment_5pct'
         GROUP BY 1 ORDER BY 2 DESC LIMIT 1;"

# baseline row 존재 확인
psql -c "SELECT * FROM cohort_baselines
         WHERE artifact_version = '<active_version>';"
```

**복구**:
1. **case 1**: build pipeline 재실행 — 새 artifact 의 ablation 결과 (학습 row 의
   cohort 분포) 를 `INSERT INTO cohort_baselines ... ON CONFLICT DO UPDATE`.
   `monitoring/sql/003_cohort_baselines.sql` 참고.
2. **case 2**: variant 별 baseline INSERT.
3. **case 3**: `\i monitoring/sql/003_cohort_baselines.sql` (DDL + 초기 row).

baseline INSERT 후 T2a 1분 안에 auto-resolve.

## T2 (discrepancy > 5%) 분기

**증상**: production 의 cohort 분포 (saatchi_warm / saatchi_cold / artsy_warm /
unmatched) 가 학습 시 분포와 5%p 이상 차이.

**가능한 원인**:
- 일부 artist 가 미매칭 → unmatched rate 증가 (artist_matcher 설정 변경?)
- `slug_in_warm_set` 가 false 로 떨어진 saatchi artist 증가 (warm_artist_slugs
  artifact race condition / load 실패)
- traffic 자체가 cohort 별로 unbalance (외부 traffic source 변화)

**Diagnosis**:
```sql
-- production cohort 분포 (Panel 3 query 와 동일)
WITH active_artifact AS (...),
prod_dist AS (...)
SELECT cohort, COUNT(*), AVG(slug_in_warm_set::int) AS warm_set_hit_rate
FROM ... GROUP BY cohort;
```

`warm_set_hit_rate` 가 saatchi_warm cohort 에서 < 100% 면 warm_artist_slugs
artifact load 누락 가능성.

## T6 (cold disabled rate < 95%) 분기

**증상**: cold artist 요청 중 `year_made_route='disabled'` 비율 95% 미만.
즉 일부 cold 요청에 year_made 가 활성화됨 → gating logic 실패.

**가능한 원인**:
- cohort 결정 helper `_decide_saatchi_warm_cohort` 가 잘못된 분기 (PR8/PR9 helper)
- profile.source 가 'saatchi' 인데 warm_artist_slugs set 미로드 (false negative)
- external_collector 가 채운 profile 이 의도치 않게 cohort=True 로 평가 (PR10b
  fix 후에는 차단됨)

**Diagnosis**:
```sql
-- cold artist 인데 disabled 아닌 case sample
SELECT request_id, artist_id, match_profile_source, slug_in_warm_set,
       is_saatchi_warm, year_made_route, year_made_used
FROM predict_logs
WHERE rollout_cohort = 'treatment_5pct'
    AND is_saatchi_warm = false  -- cohort=False 인데
    AND year_made_route != 'disabled'  -- disabled 아님
ORDER BY timestamp DESC LIMIT 20;
```

## Remediation

T2 / T6 모두 5% / 95% 임계 위반 1h 지속이면 manual rollback to prev stage
(state machine).

복구 후:
1. helper logic 단위 test 추가 / 재실행
2. warm_artist_slugs artifact 재로드 검증 (predictor restart)
3. ramp-up 신중하게 — T2 / T6 1주 baseline 안정 확인 후만.

## Resolution

- T2 / T2a / T6 alert auto-resolve
- Panel 3 의 모든 cohort diff < 1%
- Slack #ml-alerts 자동 resolve

## Post-mortem

- artifact build pipeline 의 `cohort_baselines` INSERT 단계 자동화 검증.
- new variant 추가 절차 RUNBOOK 업데이트 (baseline INSERT 의무).
- T2a 가 fire 한 시점 vs deploy 시점 — race condition 진단.
