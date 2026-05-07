# Slice-conditional Warm Path — Shadow 운영 Spec

> **작성일**: 2026-05-07
> **대상**: 운영팀 / 인프라 담당자
> **연계**: `docs/트랙2_production_통합_spec_20260507.md` §17.6 (canonical 라우팅) / `docs/stage4_warm_validation_results_20260507.md` (근거)
> **분리 사유** (코덱스 권고): spec §17.6 = canonical rule만 / 본 문서 = shadow 운영 세부

> ⚠️ **본 spec 은 운영 미승인 단계**. Stage 4 BORDERLINE 보류 결과의 후속 — `depth ≥25 + seen-in-training` 제한적 라우팅 정책의 shadow 검증.

## 1. 적용 범위

### 1.1 Slice-conditional 라우팅 (spec §17.6 의 `route_v3`)
```
warm artist (train ≥10) AND depth ≥25 (train) AND seen-in-training
  → track2_warm_fe (FE only)
그 외 warm artist (얕은 / 신규)
  → V3 (자동 fallback)
```

### 1.2 적용 트래픽 추정
- Stage 4 기준: train warm 120명 중 depth ≥25 = 33명 (27.5%)
- Test 평가 가능 = 12명 (35명 중 34%)
- **운영 트래픽 cover 추정** (Stage 4 분포 가정): 전체 cold/warm 합산 트래픽의 **약 5-10%** (warm 트래픽의 25-35%)
- ⚠️ 운영 분포가 다를 수 있음 — shadow 단계에서 실측

## 2. Shadow 단계 정의

| 단계 | 기간 | 트래픽 | 비교 | 승격 조건 |
|---|---|---|---|---|
| **W-SC-S1** Shadow Observation | 1주 | 0% (live decision X, 병렬 예측 로깅만) | warm V3 vs slice-conditional 동일 입력 | 전체 guardrail PASS + low-price/depth 15-24 보호 PASS + sample ≥ 200 slice-eligible |
| **W-SC-S2** Shadow Extended | 2주 | 0% (계속 로깅만) | 동일 | 1주 추가 안정 + composition-shift caveat 평가 |
| **W-SC-C1** Limited Canary | 1% (slice-eligible 트래픽만) | online A/B | win rate ≥ 55% + 별도 segment harm 0건 + 2주 |
| **W-SC-C2** Expanded Canary | 5% | online A/B | warm-slice MdAPE 악화 없음 + 2주 |
| **W-SC-F** Full slice rollout | 100% (slice-eligible 만) | — | W-SC-C2 통과 + 의사결정 회의 |

> **비-slice 작가 (얕은 + 신규 warm) 는 모든 단계에서 V3 유지** (변경 X)

## 3. Guardrail 정책 (Stage 4 결과 반영)

### 3.1 일반 guardrail (spec §2.1 + §17.3.4 동일)
- 예측가 < 5,000,000 KRW → V3 강제 (`guardrail_low_price`)
- medium = ink / gallery_tier = 3 / 극단 면적 / birth 비정상 / 결측 → V3
- 자동 fallback (latency / parity / model error)

### 3.2 **Slice-conditional 전용 보호 guardrail** (코덱스 권고 필수)

> Stage 4 결과: 저가 +5.63%p / depth 15-24 +6.76%p violation. Slice-conditional 도 진입 시 동일 위험 존재 → 별도 guardrail 의무.

| Guardrail | 조건 | 동작 |
|---|---|---|
| **Low-price 강제 차단** | 예측가 < 5,000,000 KRW (slice path 진입 시 사전 점검) | V3 강제 (slice path 미진입) |
| **Depth 15-24 보호** | depth_train ∈ [15, 24] | V3 강제 (slice path 미진입 — depth ≥25 만 허용) |
| **Composition-shift 자동 비활성** | 신규 warm 진입 작가 (`seen=False`) 비율 1주 > 30% | slice-conditional 자동 off + 운영팀 review |
| **Slice-specific MdAPE 감시** | slice-eligible 트래픽 MdAPE > Stage 4 baseline +5%p (24h) | 슬라이스 자동 fallback |

## 4. Coverage 측정 (3축, 코덱스 권고)

> 단순 트래픽 % 가 아닌 3축 동시 측정

| 축 | 정의 | 임계 (도입 가치 평가용) |
|---|---|---|
| **Traffic coverage** | slice-eligible 트래픽 / 전체 트래픽 | 5-15% 예상 |
| **GMV coverage** | slice-eligible 거래 GMV / 전체 GMV | (실측 — 운영 가치) |
| **Artist coverage** | slice-eligible 작가 unique / 전체 cover 작가 | (실측 — segment 일반화) |

→ 3축 모두 1% 미만이면 Slice-conditional 도입 의미 X (의사결정자 검토)

## 5. Shadow 일일 점검 (W-SC-S1 / S2 단계)

### 5.1 매일 09:00 자동 리포트 추가 항목 (cold runbook §2 보강)
| 항목 | 임계 | 위반 시 |
|---|---|---|
| `slice_eligible_count` | ≥ 30/일 | 30 미달 → coverage 평가 재고 |
| `slice_traffic_pct` | 실측 (목표 X) | 1% 미만 1주 → coverage 평가 |
| `slice_mdape_vs_v3` | warm V3 와 비교 | +5%p 이상 → S1 종결 + review |
| `low_price_blocked_count` | low-price guardrail 발동 (slice path 미진입) | 비율 추적 |
| `depth_15_24_blocked_count` | depth 15-24 guardrail 발동 | 비율 추적 |
| `unseen_artist_rate_in_slice` | 신규 warm 진입 작가 비율 | > 30% 1주 → 자동 off |

### 5.2 Slice-eligible 트래픽 sample parity (D+1 / D+3 / D+7)
- depth ≥25 + seen 작가의 sample 30 건 추출
- offline preflight (`scripts/phase_a_preflight.py`) 와 동일 expected vs 운영 환경 비교
- max diff ≤ 1e-6

## 6. W-SC-S1 → S2 합격 판정 (1주)

다음 모두 PASS 시 W-SC-S2 진입:

| 항목 | 합격 기준 | 결과 |
|---|---|---|
| Slice-eligible sample 누적 | ≥ 200 | __ |
| Slice-conditional MdAPE vs V3 | 악화 없음 (D+7 actual linkage) | __ |
| Low-price guardrail 정상 작동 | sample 검증 | __ |
| Depth 15-24 guardrail 정상 작동 | sample 검증 | __ |
| Composition-shift caveat | unseen artist rate < 30% | __ |
| Slice-specific MdAPE | Stage 4 baseline +5%p 이내 | __ |

## 7. Rollback (cold runbook §6 동일 + slice 특화)

### 7.1 정식 경로 (spec §15.1)
```bash
ops cli model.disable --name track2_warm_slice --reason "manual_rollback: <사유>"
ops cli traffic.verify --model v3 --pct 100 --segment warm_slice
ops cli notify --channel #ops-alert --msg "Slice-conditional rollback: <사유>"
```

### 7.2 자동 fallback (slice 특화)
- §3.2 보호 guardrail 위반 시 즉시
- §5.1 자동 리포트 임계 위반 시
- 운영 매니저 1주일 review 후 재개 결정

## 8. Cold rollout 과의 인터페이스

### 8.1 독립성
- Slice-conditional = warm 트래픽 한정 (spec §17.6)
- Cold rollout = cold 트래픽 한정 (spec §1-§16)
- 두 path 간 통계 가설 분리 / 운영 결정 분리
- 단, **모델 hash + pipeline version 동일** (`track2_v1_20260507` / `f4_spline_v1_20260506`)

### 8.2 Phase 순서 (권고만, 강제 X)
- **Cold Phase A 완료 후 → Slice W-SC-S1 진입 권고** (운영 안정성 검증 후)
- 권고 사유: 운영팀 capacity 분리 + cold parity 검증 결과 활용
- 단, **공식 prerequisite 아님** — Slice W-SC-S1 의 합격 기준 (§6) 은 Slice path 자체 항목만 (cold 게이트 의존 X)

## 9. 산출물 (W-SC-S1 종료 시)

- [ ] Slice-conditional shadow 1주 결과 보고서
- [ ] 3축 coverage 실측 표
- [ ] Guardrail 발동 통계
- [ ] Composition-shift 진단
- [ ] W-SC-S2 진입 승인서 (담당자 단독)

## 10. 참조

- 운영 spec: `docs/트랙2_production_통합_spec_20260507.md` §17.6 (canonical) / §17.7 (신규 warm 정책)
- Stage 4 결과: `docs/stage4_warm_validation_results_20260507.md`
- Cold rollout runbook: `docs/cold_rollout_shadow_runbook_20260507.md` (parity 검증 / 일일 점검 동일 패턴)
- 저가 진단: `docs/stage4_low_price_decomp_prereg_20260507.md` (feature 부족 가설 검증 결과)
