# PR-WARM-B Stage 3-5 Activation Runbook

> **작성일**: 2026-05-11
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: PR-WARM-B Stage 1+2 commit (`d68a794` + `d4861a3`) — artifact + variant 등록 완료
> **운영팀 의존**: ✅ — 본 runbook은 ops 활성화 가이드 / 본 세션 scope = code + docs prep

## 0. 사전 조건 (Stage 3 진입 전 확인)

| 항목 | 상태 | 확인 방법 |
|---|---|---|
| Artifact bundle 7 file `integrated_v3_filtered_tuned_b_warm_*` 존재 | ✅ commit d68a794 | `ls model_test_results/integrated_v3_filtered_tuned_b_warm_*` |
| Variant `v3_filtered_tuned_b_warm` 등록 (SUPPORTED_VARIANTS) | ✅ commit d68a794 | `grep v3_filtered_tuned_b_warm src/visionai/price_engine/api/primary_predictor.py` |
| `predict_logs` DDL with `variant` 컬럼 | ✅ commit 2d3af98 (PR2B-prereq.1) | `\d predict_logs` in psql |
| PR2B-prereq.1 dual-logging 인프라 | ✅ commit 2d3af98 | `_run_shadow_inference` 함수 존재 |
| PR2B-prereq.2 Prometheus per-route metrics | ✅ commit c60708a | Prometheus endpoint 확인 |
| 22 variant tests passing | ✅ commit d4861a3 | `pytest tests/price_engine/test_primary_predictor_variants.py` |

**모든 prereq ✅ → Stage 3 활성화 ready**

## 1. Stage 3: Shadow Activation (1주)

### 1.1 활성화 방식

본 PR-WARM-B는 **전체 variant 비교** (default `v3_filtered_tuned` vs B-retuned `v3_filtered_tuned_b_warm`) — 기존 PR2B-prereq.1 source_router shadow와 다른 axis.

**활성화 옵션** (운영팀 선택):

**옵션 A (권고 / 작은 코드 변경)**: `VARIANT_SHADOW` env var 신설
- `primary_server.py`에 `VARIANT_SHADOW=v3_filtered_tuned_b_warm` env var 처리 추가
- Shadow predictor instance load (별도 prefix)
- Primary inference 후 shadow inference (fail-open) 추가 호출
- `predict_logs.variant` 컬럼에 primary + shadow 모두 기록 (별도 row 또는 별도 컬럼)
- ⚠️ 코드 변경 필요 (별도 PR / R1 codex review 권고)

**옵션 B (코드 변경 없음 / read-only metric)**: offline 비교
- Primary 그대로 `MODEL_VARIANT=v3_filtered_tuned` (현행)
- Daily: 운영 traffic의 request features 별도 store
- Background process: `MODEL_VARIANT=v3_filtered_tuned_b_warm` 환경으로 stored features 위 prediction
- Compare side-by-side: 운영 prediction vs b_warm prediction
- ⚠️ Real-time shadow가 아님 / batch comparison only

**옵션 C (가장 단순 / 운영 영향 없음)**: 운영 환경 외부 shadow
- 별도 staging instance: `MODEL_VARIANT=v3_filtered_tuned_b_warm` 활성화
- 운영 traffic 일부 mirror (또는 sample request set replay)
- Compare staging output vs production output
- ⚠️ Traffic mirroring infra 필요 / SRE 협의

### 1.2 권고 활성화 절차 (옵션 A 기준)

**Step 1**: 코드 변경 (별도 PR)
1. `primary_server.py`에 `VARIANT_SHADOW` env var 처리 추가 (예시 코드는 §4 참조)
2. Tests 추가
3. Codex R1 사전 검수
4. Commit + merge

**Step 2**: Staging 검증
1. Staging instance: `MODEL_VARIANT=v3_filtered_tuned` + `VARIANT_SHADOW=v3_filtered_tuned_b_warm`
2. Smoke test: 10 request 위 primary + shadow 모두 출력 확인
3. predict_logs에 shadow_prediction_price_krw / shadow_variant 컬럼 기록 확인
4. Latency overhead 측정 (~10-30ms 추가 예상)

**Step 3**: 운영 활성화
1. 운영 instance: `VARIANT_SHADOW=v3_filtered_tuned_b_warm` env var 활성화 (rolling restart)
2. Prometheus dashboard 모니터링 (latency / error rate)
3. predict_logs 새 row 비율 모니터링

**Step 4**: 1주 모니터링 (sign-off 기준 / R1 amendment 정합)
- ✅ 7-day aggregate Δ_warm ≤ -0.8pp
- ✅ 5/7 daily medians Δ_warm ≤ -0.5pp
- ✅ no day Δ_warm > +0.3pp
- ✅ no latency degradation (>+5%) / no error rate spike

**Step 5**: Stage 4 진입 결정 (codex R4 사후 검수)
- 모든 sign-off 기준 충족 → Stage 4 canary 진입
- 미달 → 재분석 / rollback / 추가 모니터링

### 1.3 Daily Monitoring Query (옵션 A 기준)

`scripts/pr_warm_b_daily_shadow_report.sql`:
```sql
-- Daily Δ_warm distribution: primary (default) vs shadow (b_warm)
SELECT
    DATE(timestamp) AS day,
    COUNT(*) AS n_requests,
    AVG(ABS(price_krw - shadow_prediction_price_krw)) AS mean_abs_diff,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_krw - shadow_prediction_price_krw) AS median_diff,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY ABS(price_krw - shadow_prediction_price_krw) / price_krw * 100
    ) AS median_pct_diff,
    -- Δ_warm proxy: shadow MdAPE - primary MdAPE (warm subset only)
    COUNT(CASE WHEN is_warm_artist = true THEN 1 END) AS n_warm,
    COUNT(CASE WHEN is_warm_artist = false THEN 1 END) AS n_cold
FROM predict_logs
WHERE shadow_variant = 'v3_filtered_tuned_b_warm'
  AND timestamp >= NOW() - INTERVAL '7 days'
  AND price_krw IS NOT NULL
  AND shadow_prediction_price_krw IS NOT NULL
GROUP BY DATE(timestamp)
ORDER BY day DESC;
```

**Daily report script**: `scripts/pr_warm_b_daily_shadow_metric.py` (본 commit 산출 / §3 참조)

## 2. Stage 4: Canary 10% → 50% → 100% (3일)

### 2.1 Cohort key (R1 amendment 정합)

`artist_slug` hash → 0-9 bucket / mod 10:
- bucket 0 → canary (B-warm)
- bucket 1-9 → control (default)

Fallback (artist 미매칭 시): `request_id` hash → mod 10.

**Code**: `scripts/canary_cohort.py` (본 commit 산출 / §3 참조)

### 2.2 Canary 활성화 절차

**Stage 4.1 (10% / 24시간)**:
1. `primary_server.py`에 cohort 기반 variant 분기 추가:
   - Cohort bucket 0 → `MODEL_VARIANT=v3_filtered_tuned_b_warm`
   - Cohort bucket 1-9 → `MODEL_VARIANT=v3_filtered_tuned` (default)
2. 운영 활성화 / 24시간 모니터링
3. Metric: canary MdAPE vs control MdAPE / latency / error rate / 95% CI

**Stage 4.2 (50% / 24시간)** — Stage 4.1 sign-off 후:
1. Cohort bucket 0-4 → canary / bucket 5-9 → control
2. 24시간 모니터링

**Stage 4.3 (100% / 24시간)**:
1. 모든 cohort → canary
2. 24시간 안정 모니터링

**Sign-off 기준 (각 stage)**:
- ✅ canary MdAPE ≤ control MdAPE + 0.3pp (strict non-inferiority)
- ✅ latency p95 ≤ control p95 × 1.05 (5% degradation 한계)
- ✅ error rate ≤ control error rate + 0.5%

**Codex R5 사후 검수** (Stage 4 종료 후 / Stage 5 full migration 결정)

### 2.3 Rollback (Stage 4 단계)

Metric degradation 감지 시:
1. **`MODEL_VARIANT` env var revert** (또는 cohort 비율 0%로 rollback)
2. Process restart / reload — predictor cached model swap 보장
3. Smoke check: `predictor.variant == "v3_filtered_tuned"` 확인
4. Artifact retention: `integrated_v3_filtered_tuned_b_warm_*` 파일 보존 (rollback 가능 상태)
5. DB / metrics schema 변경 X / no schema rollback 필요

## 3. Stage 5: Full Migration + Cleanup (1주)

### 3.1 Full migration

1. **`DEFAULT_VARIANT` 변경**: `primary_predictor.py`에서 `DEFAULT_VARIANT = "v3_filtered_tuned_b_warm"` (commit)
2. `MODEL_VARIANT` env var 미설정 시도 b_warm load (default flip)
3. 운영 instance rolling restart
4. 100% traffic이 b_warm 받음
5. 1주 안정 모니터링

### 3.2 Cleanup 결정 (1주 후)

- **Artifact retention**: `integrated_v3_filtered_tuned_*` (default) 그대로 유지 / rollback path 보존 권고
- **Variant deregister**: `v3_filtered_tuned` SUPPORTED_VARIANTS에서 제거 결정 (별도 PR)
- **Warm calibration re-fit**: B-retuned XGB 위에서 warm_factors 재추정 (별도 cycle / 본 cycle scope 외 / 단 운영 routing은 warm_factors 미적용이라 immediate impact X)

### 3.3 후속 cycle 후보 (별도 PR / 본 cycle scope 외)

- Warm calibration re-fit (B-retuned XGB 위)
- Source-conditional cycle 재검토 (D1.SC FAIL 후 / cold path 변경 없이 진행)
- D1 cold path 후속 (non-GBDT axis / 본 세션 결과 정합)

## 4. 옵션 A 코드 변경 (참고 / 별도 PR 권고)

`primary_server.py` 추가 (예시 / Codex R1 사전 검수 후 finalize):

```python
# 신규 ENV: VARIANT_SHADOW
_variant_shadow_name = os.environ.get("VARIANT_SHADOW")
_shadow_predictor: PrimaryPredictor | None = None

def _init_shadow_predictor():
    global _shadow_predictor
    if not _variant_shadow_name or _variant_shadow_name == _predictor.variant:
        return
    if _variant_shadow_name not in SUPPORTED_VARIANTS:
        logger.warning("VARIANT_SHADOW=%r not in SUPPORTED_VARIANTS / disable",
                       _variant_shadow_name)
        return
    _shadow_predictor = PrimaryPredictor()
    _shadow_predictor.load_models(model_dir, variant=_variant_shadow_name)
    logger.info("Shadow predictor loaded: %s", _variant_shadow_name)


def _run_variant_shadow_inference(features, is_matched, training_count,
                                   target_market, has_manual_profile, artist_slug):
    """Variant shadow inference (fail-open / VARIANT_SHADOW only).

    Returns dict with shadow_variant / shadow_prediction_price_krw (or empty).
    """
    if _shadow_predictor is None:
        return {}
    try:
        result = _shadow_predictor.predict(
            features=features, is_matched=is_matched, training_count=training_count,
            target_market=target_market, has_manual_profile=has_manual_profile,
            artist_slug=artist_slug,
        )
        return {
            "shadow_variant": _shadow_predictor.variant,
            "shadow_prediction_price_krw": result["price_krw"],
        }
    except Exception as e:
        logger.warning("Variant shadow inference failed (fail-open): %s", e)
        return {"shadow_variant_error": str(e)[:200]}


# In main predict endpoint:
# After primary inference + before log:
shadow_data = _run_variant_shadow_inference(...)
log_entry.update(shadow_data)
_log_prediction(log_entry, count_toward_monitor=True)  # shadow는 monitor 오염 X
```

**Tests** (별도 PR):
- `test_variant_shadow_predictor_load` (env var set / unset)
- `test_variant_shadow_inference_fail_open` (shadow predictor fail → primary 영향 X)
- `test_variant_shadow_log_field` (predict_logs에 shadow_variant + shadow_prediction_price_krw 기록)

## 5. Stage 3-5 timeline (예상)

| Stage | 기간 | 운영 영향 | sign-off |
|---|---|---|---|
| Stage 3 shadow | 1주 (7일) | X (read-only) | R4 codex / 7-day aggregate Δ_warm ≤ -0.8pp |
| Stage 4.1 canary 10% | 24시간 | 10% user | latency / MdAPE non-regression |
| Stage 4.2 canary 50% | 24시간 | 50% user | latency / MdAPE non-regression |
| Stage 4.3 canary 100% | 24시간 | 100% user | latency / MdAPE non-regression |
| Stage 5 full migration | 1주 (7일) | 100% user / DEFAULT 변경 | post-migration 안정성 |

**Total**: ~2-3주 wall (운영팀 의존).

## 6. Risk + caveat

- **운영 영향 sequence**: Stage 3 read-only → Stage 4 점진 (10%-100%) → Stage 5 default flip / 각 단계 rollback path 보존
- **Latency overhead**: Stage 3 옵션 A에서 shadow inference 추가로 10-30ms 추가 / Stage 4부터 X (primary만)
- **Codex Q5 priority answer**: B deploy > non-GBDT exploration > no more GBDT cold retune (D1.Arch.tuned 후 confirmed)
- **본 runbook은 deliverable / 실제 활성화는 운영팀 결정**

## 7. 본 commit 산출물

- `docs/pr_warm_b_stage_3_5_activation_runbook_20260511.md` (본 문서 / activation runbook)
- `scripts/pr_warm_b_daily_shadow_metric.py` (daily metric report / Stage 3 monitoring)
- `scripts/canary_cohort.py` (Stage 4 cohort hash utility)
- (별도 PR 권고) `primary_server.py` VARIANT_SHADOW env var 추가 (옵션 A 활성화 / Codex R1 review)
- (별도 PR 권고) Stage 4 cohort routing wiring

## 8. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 (본 commit) | (예정) | runbook 구조 / 옵션 A 코드 변경 plan / monitoring script 검수 |
| R2 (Stage 3 활성화 후) | (예정) | 7-day shadow metric 검수 / Stage 4 진입 결정 |
| R3 (Stage 4 종료 후) | (예정) | canary metric 검수 / Stage 5 결정 |
| R4 (Stage 5 종료 후) | (예정) | post-migration 안정성 검수 |

## 9. 결론

PR-WARM-B Stage 3-5 활성화 deliverables 완료 (코드 + 문서 + monitoring script + canary cohort utility). 실제 활성화는 운영팀 결정 (별도 PR + Codex review + ops sign-off).

**Codex Q5 priority answer 재확인**: B deploy > non-GBDT exploration > no more GBDT cold retune.

**현 운영 stack** (commit `3c8ce32` HEAD):
- ✅ Default `v3_filtered_tuned` 그대로 serving (cold + warm)
- ✅ B-warm variant `v3_filtered_tuned_b_warm` artifact + 등록 완료 (commit d68a794) / default OFF
- ⏳ Stage 3-5 deploy = 운영팀 활성화 대기
