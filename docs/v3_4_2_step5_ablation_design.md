# v3.4-2 step 5: year_made enrichment ablation 설계 (사전 작성)

작성일: 2026-05-01
배경: step 4 (21,087 전수 enrichment) 진행 중. 완료 후 모델 재학습 ablation. 본 문서는 ablation 설계 사전 정리 (코드 skeleton 미작성, 코덱스 review 후 implement).

---

## 1. 결정적 finding: 현재 CB_FEATURES 에서 year_made 의존 feature 가 이미 제거됨

`src/visionai/price_engine/api/primary_predictor.py:46-71`:
```python
CB_FEATURES = [
    "ho", ..., "artist_birth_year", "has_birth_year", "career_stage", ...
    # career_age / work_age / vintage_premium / freshness_discount 제거됨
]
# Removed for train/serve drift consistency (Codex 4차 P1, 2026-04-28):
# - career_age, work_age, vintage_premium, freshness_discount
#   학습 데이터는 정상 계산, 서빙은 0 하드코딩.
```

**의미**:
- 현재 production 은 `year_made` 의존 feature 를 **전혀 사용 안 함**
- saatchi 의 year_made 가 NaN 이어도 모델 입장에선 무의미
- step 5 ablation 의 핵심 질문이 **reverse**: "년도 feature 재도입 시 ROI vs train/serve drift 위험"

---

## 2. Train/Serve drift caveat (코덱스 4차 P1 재검토)

년도 feature 재도입 시:
- **학습 시**: saatchi enrichment 로 75% → ~99% year_made 보충 (step 4 결과 기준)
- **서빙 시**: production primary predictor 가 year_made 어떻게 받는지?
  - artsy: production scrape 가 year_made 가져오는지 확인 필요
  - saatchi: production scrape 가 detail page enrichment 호출하는지 확인 필요
  - 둘 다 X 면 → 학습 정상, 서빙 0 하드코딩 = 4차 P1 와 동일 drift

→ **Train/Serve drift 정합 우선**. enrichment 도입 = 서빙도 동시에 detail page 호출해야

---

## 3. Ablation variants (3개 — 코덱스 P0 R2 축소)

코덱스 권장: monotonic ladder (5개) → MVP 3개. `year presence 자체의 가치` 와 `derived bundle 추가 가치` 만 분리.

**V0 — current production (no year_made feature)**
- CB_FEATURES 그대로 (year_made 의존 feature 0개)
- 단순 비교 anchor

**V_year_only — year_made + has_year_made + work_age**
- CB_FEATURES 에 `year_made`, `has_year_made`, `work_age = 2026 - year_made` 추가
- saatchi enrichment 적용 (~99% saatchi 보충), artsy 기존
- `work_age` 정의는 `prepare_primary_market_dataset.py:254` 와 동일 (코덱스 P0 R4: source-conditional 조정 금지)
- year presence 자체의 model 신호 가치 측정

**V_full — V_year_only + vintage_premium + freshness_discount + career_age**
- V_year_only 위에 derived bundle 추가
- year_made + birth_year 결합 effect (career_age) + career_stage_int 결합 (vintage/freshness)
- bundle 추가 가치 (incremental over V_year_only) 측정

---

## 4. Cohort 분리 평가 (코덱스 P1 축소 — primary 1개 + guardrail)

코덱스 권장: 다중 비교 줄이려면 primary endpoint 1개로 고정 + guardrail.

### Primary endpoint
| Cohort | 설명 |
|--------|------|
| **overall MdAPE** | 28,376 (의사결정 기준) |

### Guardrail
| Cohort | 설명 |
|--------|------|
| Cold | 1,314 (warm 미포함) — sparse artist-history |
| Low work_count | 작가별 row 1-4 — v3.3-2 strong KT cold catastrophic cohort 후보 |
| Saatchi_online | n=21,087 의 online 부분 — D10 보다 안정 |

### Sentinel only (의사결정 X)
| Cohort | 설명 |
|--------|------|
| has_year_made=1 vs 0 | flag 단독 기여 (interpretation only) |
| D10 saatchi_online | n=27 cold cohort, 검정력 약함 — sentinel slice |

`career_age recompute slice` = V_full 이 의미 있을 때만 2차 진단으로 미룸 (코덱스 P1).

---

## 5. Paired comparison

각 V_x vs V0 paired bootstrap CI:
- `np.log(actual / pred)` per-row residual
- artist-cluster bootstrap (within-artist correlation 보존, v3.2-1 패턴)
- 10K iter, paired Wilcoxon p-value

Effect size 기준:
- 통과: 95% CI 가 0 미포함 + |median Δ MdAPE| > 0.5%p
- 의미있는 개선: |median Δ MdAPE| > 1%p (D10 saatchi 등 catastrophic cohort 에서)

---

## 6. Train/Serve drift 검증 (코덱스 P0 R1 핵심)

**현재 production scrape 는 작품 year_made/year_created 미수집** (`src/visionai/price_engine/api/external_collector.py:18` — 작가 프로필만):
- artsy: GraphQL 로 작가 정보만 가져오고 작품 year 안 가져옴
- saatchi: 별도 enrichment 안 호출 (Constructor.io 1차 데이터만)

→ **본 ablation 자체는 deployable 여부와 분리** (research only):
- **research ablation**: year signal upper-bound 측정 (학습 데이터 보충 시 model 의 best-case ROI)
- **deployable ablation**: production scrape 설계 변경 후 별도 (v3.5 backlog)

**Drift 회피 옵션 정리** (코덱스 P0):
- conditional feature (`year_made_if_saatchi`) 도 drift 회피 X — 학습 시 saatchi rows 가 채워지지만 production scrape 에 없음 → mismatch 그대로
- **유일한 drift 회피 = production scrape 가 detail page year_made 를 stable 하게 채우게 변경**
- 그 변경 자체가 v3.5 의 별도 ops review (latency / cost)

---

## 7. 진행 순서 (코덱스 권장 6-step)

이번 ablation = **research / "year signal upper-bound 측정"**. 배포 후보 검증 X.

1. **step 4 완료 후 fill rate / unresolved 패턴 확정** (~6.5 hr 후)
2. **production feasibility 표 고정**: year_made 를 Artsy/Saatchi 서빙에서 언제, 어떤 latency 로 채울 수 있는지 — 별도 ops review (현재 production scrape 는 작품 year_created/year_made 수집 X, `external_collector.py:18` 가 작가 프로필만)
3. **3 variant 학습**: V0 / V_year_only / V_full (paired OOF)
4. **primary 평가**: overall MdAPE (artist-cluster bootstrap CI + paired Wilcoxon). guardrail = cold / low_work_count / saatchi_online
5. **V_year_only 의미 X → 중단** (year signal 자체가 ROI 적음)
6. **V_year_only + V_full 추가 이득 → v3.5 backlog 의사결정 (production scrape 설계 review)**

merge module + ablation runner 코드는 step 4 완료 + fill rate 확정 후 작성. 본 시점은 설계 문서만 + 코덱스 P0/P1/P2 반영 완료.

---

## 8. Risk track

- **Train/serve drift**: 채택 전 production scrape 변경 plan 필수
- **Saatchi-only enrichment 한계**: artsy 의 7,640 행 중 ~5% 결측 그대로
- **D10 saatchi cohort 검정력**: n=27 (cold path) 너무 작아 통계적 검정 어려움
- **본 ablation 의 enrichment data**: step 4 의 ~99% fill rate 추정. ~80~200 unresolved 는 has_year_made=0 으로 분류

---

## 9. 산출물 (예정)
- `scripts/saatchi_year_made_merger.py` — merge 함수 + 단위 테스트
- `scripts/v34_2_step5_year_made_ablation.py` — ablation runner
- `model_test_results/v3_diagnostics/v34_2_step5_year_made_ablation.json`
- `docs/v3_4_2_step5_ablation_results.md`
