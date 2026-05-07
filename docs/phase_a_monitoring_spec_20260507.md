# Phase A Shadow Monitoring Spec

> **작성일**: 2026-05-07
> **대상**: 운영팀 (Grafana / Datadog / Slack 구현)
> **연계**: spec §11.1 (Phase A 합격 기준), §3 (auto-fallback), §4 (drift), runbook §2 (일일 점검)
> **목적**: Phase A shadow 1주 운영 시 자동 모니터링 — metric catalog / alert rules / daily report 입력 schema 와 임계만 정의 (구현은 운영 인프라)

> **LLM 범위 한정**: 본 문서는 schema + 임계 정의만. 실제 Grafana panel / Datadog monitor / Slack webhook 구현은 운영팀 직접.

## 1. Metric Catalog

| Metric | 정의 | 단위 | 집계 빈도 |
|---|---|---|---|
| `shadow_request_count` | Phase A shadow 응답 누적 (cold artist) | 건 | 분 단위 |
| `schema_pass_rate` | API request schema 검증 통과 비율 | % | 분 단위 |
| `latency_p50_track2` | track2 응답 시간 p50 | ms | 분 단위 |
| `latency_p95_track2` | track2 응답 시간 p95 | ms | 분 단위 |
| `latency_p95_v3` | V3 응답 시간 p95 (비교 baseline) | ms | 분 단위 |
| `latency_p95_ratio` | `latency_p95_track2 / latency_p95_v3` | ratio | 분 단위 |
| `guardrail_hit_rate` | 가드레일 발동 비율 (전체 cold 대비) | % | 시간 단위 |
| `guardrail_hit_by_reason` | 가드레일 사유 코드별 분포 (low_price / ink / tier_3 / extreme_size 등) | dict | 시간 단위 |
| `fail_closed_count` | Fail-closed 발동 건수 (NO_BASELINE / MODEL_ERROR / PARITY_BREACH) | 건 | 시간 단위 |
| `fail_closed_by_reason` | 사유 코드별 분포 | dict | 시간 단위 |
| `fallback_rate` | 자동 fallback 발동 비율 | % | 시간 단위 |
| `request_id_match_rate` | shadow log ↔ V3 운영 log request_id 매칭률 | % | 일 단위 |
| `mdape_track2_vs_v3_diff` | (track2 MdAPE − V3 MdAPE) — D+7 actual linkage | %p | 일 단위 (D+7 부터) |

## 2. Alert Rules

| Alert | 조건 | Window | 채널 | 우선순위 |
|---|---|---|---|---|
| schema_pass_low | `schema_pass_rate < 99%` | 15분 | Slack `#track2-shadow` | P1 |
| latency_high | `latency_p95_ratio > 2.0` | 15분 | Slack `#track2-shadow` | P1 |
| guardrail_high | `guardrail_hit_rate > 2%` | 1시간 | Slack `#track2-shadow` | P2 |
| fallback_high | `fallback_rate > 5%` | 1시간 | Slack `#track2-shadow` | P2 |
| fail_closed_critical | `fail_closed_count > 0 AND reason = PARITY_BREACH` | 즉시 | Slack `#track2-shadow` + 담당자 직접 멘션 | P0 |
| fail_closed_other | `fail_closed_count > 5 in 1h` | 1시간 | Slack `#track2-shadow` | P1 |
| sample_low | `shadow_request_count < 50 in 24h` | 24시간 | Slack `#track2-shadow` | P2 |
| mdape_gap_high | `mdape_track2_vs_v3_diff > +5%p` (D+7+) | 24시간 | Slack `#track2-shadow` + 운영 매니저 cc | P1 |

## 3. Daily Report Schema (자동 09:00 KST)

```json
{
  "date": "YYYY-MM-DD",
  "phase": "A",
  "day": 1,
  "shadow_request_count_24h": 0,
  "shadow_request_count_cumulative": 0,
  "core_metrics": {
    "schema_pass_rate": "%",
    "latency_p95_ratio": "ratio",
    "guardrail_hit_rate": "%",
    "fail_closed_count_24h": 0,
    "fallback_rate": "%"
  },
  "fail_closed_by_reason": {
    "NO_BASELINE": 0,
    "MODEL_ERROR": 0,
    "PARITY_BREACH": 0
  },
  "guardrail_hit_by_reason": {
    "low_price": 0,
    "medium_ink": 0,
    "tier_3": 0,
    "extreme_size": 0,
    "missing_feature": 0
  },
  "vs_yesterday": {
    "schema_pass_rate_diff": "%p",
    "latency_p95_ratio_diff": "ratio",
    "guardrail_hit_rate_diff": "%p"
  },
  "alerts_fired_24h": ["alert names"],
  "action_required": false,
  "ops_memo": "장애/예외 메모"
}
```

## 4. D+7 합격 판정 자동 리포트

Day 7 종료 시 spec §11.1 7개 합격 기준 자동 집계:

```json
{
  "phase_a_d7_verdict": {
    "shadow_count_geq_500": true,
    "actual_price_linkage_ok": true,
    "mdape_gap_leq_5pct": true,
    "guardrail_hit_leq_2pct": true,
    "latency_p95_ratio_leq_2": true,
    "schema_pass_rate_geq_99": true,
    "fail_closed_works": true,
    "all_pass": true,
    "phase_b_eligible": true
  }
}
```

→ `all_pass: true` → Phase B 5% canary 승인 절차 시작 (담당자 + 운영 매니저)
→ `all_pass: false` → 실패 항목 분석 + 1주 추가 shadow 또는 모델 재검토

## 5. 구현 가이드라인 (운영팀)

- **Metric 수집**: APM (Datadog / New Relic 등) + 응답 로그 stream
- **저장**: 시계열 DB (Prometheus / InfluxDB) + log warehouse (Elasticsearch / BigQuery)
- **Alert**: Datadog Monitor / Grafana Alert / Slack webhook
- **Daily Report**: cron 09:00 KST, 자동 Slack post + 별도 archive
- **D+7 자동 판정**: 별도 스크립트 (운영팀 작성) → 합격 시 Phase B 승인 PR 자동 생성

## 6. 의존성

- spec §11.1 7개 합격 기준 (변경 X)
- spec §3 auto-fallback (latency / MdAPE / fallback rate)
- spec §4 drift monitoring (PSI 별도, Phase A 에서는 정보 수집만)
- runbook §2 일일 점검 (수동 확인 항목 포함)

## 7. 운영팀 in-environment 작업 항목 (참고)

- ☐ Metric catalog §1 모든 metric 수집 활성화
- ☐ Alert rules §2 8 항목 활성화
- ☐ Daily report cron 등록
- ☐ D+7 합격 판정 스크립트 작성
- ☐ Slack channel `#track2-shadow` 생성 + 담당자 / 운영 매니저 / 의사결정자 invite
