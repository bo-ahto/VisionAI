# v3.5 step 1: cohort gating ablation 결과 + V_year_saatchi_warm 채택

작성일: 2026-05-02
배경: v3.4-2 step 5 (V_year_only Δ-0.74%p, cold +0.99%p worse) → v3.5 step 1 cohort gating 검증.
설정: n_splits=5, CB iter=1000, XGB iter=3000, n_boot=10K. 약 13분 소요.

---

## 1. 결과 — 5 variant cohort breakdown

| Variant | overall | cold | cold_le2 | warm_5_9 | sa_online | sa_10p |
|---------|--------:|-----:|---------:|---------:|----------:|-------:|
| V0 | 10.358% | 42.575% | 39.462% | 17.150% | 10.668% | 9.902% |
| V_year_only | 9.619% | 43.570% | 41.644% | 16.881% | 9.626% | 8.920% |
| V_year_saatchi_only | 9.614% | 43.379% | 41.651% | 16.493% | 9.620% | 8.900% |
| V_year_warm_only | 9.625% | 45.693% | 43.203% | 16.881% | 9.642% | 8.920% |
| **V_year_saatchi_warm** | **9.620%** | **42.603%** | 40.370% | 16.493% | 9.620% | **8.900%** |

## 2. Paired vs V0 (artist-cluster CI95 + Wilcoxon artist p)

| 비교 | Δ overall | CI95 | excludes_zero | artist p |
|------|----------:|-----:|:-------------:|---------:|
| V_year_only | -0.739% | [-1.144, -0.324] | TRUE | 0.018 |
| V_year_saatchi_only | -0.744% | [-1.142, -0.341] | TRUE | 0.021 |
| V_year_warm_only | -0.733% | [-1.140, -0.318] | TRUE | 0.087 |
| **V_year_saatchi_warm** | -0.738% | [-1.140, -0.337] | TRUE | **0.00028** |

## 3. Selection decision (코덱스 v3.5 plan thresholds)

임계: overall Δ ≤ -0.5%p, cold Δ ≤ +0.3%p, sa_10p Δ ≤ -0.8%p

| Variant | Δoverall | Δcold | Δsa_10p | all pass |
|---------|---------:|------:|--------:|:--------:|
| V_year_saatchi_only | -0.744 ✓ | +0.804 ✗ | -1.002 ✓ | ❌ |
| V_year_warm_only | -0.733 ✓ | **+3.118 ✗** | -0.982 ✓ | ❌ |
| **V_year_saatchi_warm** | **-0.738 ✓** | **+0.028 ✓** | **-1.002 ✓** | **✅ unique pass** |

**Chosen**: `V_year_saatchi_warm` (saatchi & warm intersect gating)

---

## 4. 핵심 finding

### 4.1 V_year_saatchi_warm 만 cold guardrail 통과
- overall -0.738%p (V_year_only 와 사실상 동일)
- cold +0.028% ≈ 0 (gating 으로 cold cohort spurious 차단 성공)
- saatchi_online 10+ -1.002%p 보존
- artist p = **0.00028** (가장 robust statistical signal)

### 4.2 V_year_warm_only 의 counterintuitive cold +3.12%
코덱스 P0 R2 해석 (가장 강한 가설 = (b)):
- 본 실험에서 "비활성" 은 진짜 missing 취급 X, 숫자형 `fillna(0)` 으로 모델 입력
- V0 "컬럼 없음" vs V_year_warm_only "컬럼 있는데 cold=0/0/0" 은 다른 표현
- warm slice 가 year split 학습 → cold (year=0) 가 sentinel-like 0 leaf 로 밀려 악화
- saatchi & warm intersect (V_year_saatchi_warm) 시 source 축 추가로 cold 보호
- → **source 축 + warm 축 교호작용** 이 실제로 있음

### 4.3 V_year_saatchi_only 도 cold worse (+0.804)
- saatchi-only gating 만으로는 saatchi cold (n=628) 의 spurious overfit 차단 X
- saatchi & warm intersect 까지 가야 cold 정상화

### 4.4 모든 4 enrichment variants 가 overall -0.7~-0.74%p (CI 0 미포함)
- year_made signal 자체는 강함
- gating 차이는 cold/cohort distribution 보호에 있음

---

## 5. Production semantics 정합 (코덱스 P1 R3)

V_year_saatchi_warm 의 production gating:
- **`is_saatchi=True AND warm_artist=True`** 만 year_made / has_year_made / work_age 활성
- 그 외 (artsy / saatchi cold / 비-saatchi cold) → `year_made=NaN, has_year_made=0, work_age=0`
- 학습 vs 서빙 정의 일치 (코덱스 검증: build_variant 와 server semantics 정합)

### 5.1 Step 2 에서 변경 필요 사항 (코덱스 P1)
1. **요청/collector 에 `artwork_id` 또는 `artwork_url` 추가** (현재 없음, `primary_schemas.py:7`)
2. **collector cache 를 artwork 기반으로 분리** (현재 `artist_name` 기반, `external_collector.py:11`)
3. **feature builder 에 year 3종 추가 + disable semantics 구현** (`primary_feature_builder.py:117`)
4. **predictor 의 feature contract + model artifact 교체** (`primary_predictor.py:23, 301`)

### 5.2 Cohort assignment risk (코덱스 P1)
- 현재 serve warm 판정 = `artist_slug ∈ warm_artist_slugs`
- unmatched / external-only 요청 → warm 자동 false → year off (안전 측면 좋음)
- coverage 감소 → step 2 에서 "매칭 실패 saatchi 요청은 무조건 year off" 명시 필요

---

## 6. v3.5 step 2 진행 권장 (코덱스)

step 1 종료 = **offline selection 종료**, **production deploy 가능 ≠**.

step 2 에서 검증할 항목:
1. Production scrape 가 artwork year_made 안정 공급 가능?
2. cache key 단위 (artwork_id 신설) + invalidation 정책
3. serve-path integration spec (parser → cache → fallback)
4. cohort assignment correctness ≥ 99% 보장 가능?

**framing 정정 (코덱스 P2)**: 
- ❌ "free win" (잘못)
- ✅ "**near-free risk reduction**" — overall 손실 없이 cold 보호. 단 serve-path 구현 / cache miss latency / source 판정 리스크는 step 2~4 에서 닫아야

---

## 7. 산출물

- `scripts/saatchi_year_made_merger.py` (cohort gating 추가, +25 unit tests)
- `scripts/v35_step1_cohort_gating_ablation.py`
- `model_test_results/v3_diagnostics/v35_step1_cohort_gating_ablation.json`
- `docs/v3_5_step1_cohort_gating_results.md` (본 문서)

---

## 8. v3.5 plan 갱신

- 이전 plan: `V_year_only` 중심
- 이번 step 1 결과 후: **`V_year_saatchi_warm` 중심**
- v3.5 plan 의 채택 framing / step 2-4 의 variant 명시 / production semantics 갱신 필요 (코덱스 P2)

→ 별도 commit 으로 `docs/v3_5_plan.md` 갱신.

---

## 9. v3.5 진행도

- ✅ **Step 1: cohort gating ablation** (V_year_saatchi_warm 채택, unique pass)
- ⏭️ Step 2: production feature availability + serve-path integration spec
- Step 3: enrichment / latency / coverage trade-off
- Step 4: gated rollout drift monitoring
