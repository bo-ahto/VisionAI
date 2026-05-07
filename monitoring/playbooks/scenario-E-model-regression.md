# Scenario E — model regression (overall MdAPE 악화)

**Severity**: rollback (T3, T4)
**Trigger**: T3 (`mdape_d7_cold > 46%`, 1h for) / T4 (`treatment_vs_control_diff > +1.0%p`, 1h for)
**Spec**: `docs/v3_5_step4_drift_monitoring.md` §5.5

## Detection signals

- alert:
  - T3 (`vai-trigger-3-mdape-cold`): cold cohort 보호 실패
  - T4 (`vai-trigger-4-treatment-vs-control`): A/B test diff > +1%p (regression)
- dashboard:
  - Panel 8 (MdAPE D7 cold) — treatment cohort > 46%
  - Panel 12 (treatment_vs_control_diff) — > +1%p (red threshold)
  - Panel 7 (MdAPE D7 overall) — treatment vs control 비교

## Immediate action (자동)

1. T3 또는 T4 fire → Slack `#ml-alerts` + PagerDuty + post-mortem trigger.
2. **state machine 자동 rollback**: rollout 단계 후퇴 (5% → 1% → previous).
3. treatment cohort traffic 즉시 감소 → 영향 최소화.

## Immediate action (수동, 5분 내)

1. on-call 이 alert + dashboard 확인.
2. ablation offline 결과 (overall -0.74%p / cold +0.03%) 와 production 차이 분석.
3. cohort 별 breakdown 즉시 확인.

## Diagnosis

**1. cohort 별 MdAPE 분해**:
```sql
SELECT
    rollout_cohort,
    CASE WHEN is_saatchi_warm THEN 'warm' ELSE 'cold' END AS sub_cohort,
    sold_source,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape,
    COUNT(*) AS n
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
GROUP BY 1, 2, 3
ORDER BY 1, 2;
```

`mdape` 가 어느 sub_cohort 에서 spike 했는지 식별.

**2. 1-2 작가 outlier 확인** (cold cohort 특히 N 작음 — 개별 작가 영향 큼):
```sql
SELECT artist_slug, COUNT(*) AS n,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
    AND rollout_cohort = 'treatment_5pct'
    AND is_saatchi_warm = false
GROUP BY 1
HAVING COUNT(*) >= 3
ORDER BY mdape DESC LIMIT 20;
```

**3. predicted_price_krw 분포 drift**:
```sql
-- D7 vs D-7 의 p50/p90 ratio (013_metrics_mdape.sql 의 query 와 동일)
WITH d7 AS (...), dminus7 AS (...)
SELECT ...;
```

p50 ratio 가 ±10% 초과 → 모델 자체 prediction 분포 drift.

## Remediation

**A. 1-2 작가 outlier 가 원인**
1. 그 작가들을 `warm_artist_slugs` 에서 임시 제외 (sub-gating 강화).
2. 신규 artifact build (warm set 갱신) → deploy → 재측정.

**B. cohort 전반 regression**
1. 즉시 manual rollback to previous variant (`MODEL_VARIANT=v3_filtered_tuned`).
2. ablation 재실행 (offline) — production traffic 의 cohort 분포로 simulate.
3. discrepancy 발견 시 V_year_saatchi_warm 의 sub-gating (예: birth_year 10년 단위
   bucket 별 활성/비활성) 도입 검토.

**C. saatchi-side issue (sold_actuals 이 부정확하거나 lag)**
1. sold_actuals ETL 점검 — 최근 7d 데이터 누락? 잘못된 source filter?
2. predict_logs 의 cohort 분포는 정상 → MdAPE 만 spike 면 sold_actuals 의심.

## Resolution

- T3 / T4 alert auto-resolve (cold ≤ 43% / diff ≤ +0.3%p 회복).
- state machine 이전 단계에서 안정 운영 확인 후 ramp-up 재개 (1주 baseline).

## Post-mortem (필수 — rollback severity)

1. **재발 방지**:
   - offline ablation 의 cohort coverage 가 production traffic 정합?
   - artifact build 의 cohort split 이 retrain 마다 자동 재계산?
   - 1-2 작가 outlier monitoring (artist 별 MdAPE D7) 별도 alert?
2. **롤아웃 procedure 검토**: 1% → 5% gate criterion 에 cold MdAPE 추가?
3. **incident timeline**: 첫 alert 시점 vs deploy 시점 vs sold lag.
