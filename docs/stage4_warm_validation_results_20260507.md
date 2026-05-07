# Stage 4 Warm Path Validation — 결과 보고

> **작성일**: 2026-05-07 (Stage 4 v3 실행 결과)
> **연계**: `docs/stage4_확장검증계획_20260507.md` (사전등록 §6.0) / `experiments/structural_v1/results/stage4_warm_validation.json`
> **데이터**: `data/curated/stage4_full.parquet` (Artsy cleansed 8,495 / 807 작가 — 2026+ 사전등록 외 제외) / SHA-16 = `b7b51b81d3a033b5`
> **사전등록 freeze**: `experiments/structural_v1/results/stage4_dataset_freeze.json`

## 0. 판정 (사전등록 §6.1)

> **BORDERLINE — 보류** (Stage 4 leading candidate 검증 부분 통과)

| 조건 | 결과 | 판정 |
|---|---|---|
| Primary CI 상한 ≤ 0 (cluster bootstrap n=2000) | CI [-16.01, +5.30] | ✗ |
| Primary practical Δ ≤ -0.8%p | -6.22%p (점추정) / -5.74%p (boot mean) | ✓ |
| Seed std ≤ 0.5%p (10 seed × n=500) | 0.252 | ✓ |
| Segment harm 0 violations | 2 violations (저가 / depth 15-24) | ✗ |

**근거 종합**: 통계적 유의성 미달 (CI 0 포함, P(diff≥0)=15.05%) + 저가 / depth 15-24 segment 악화 → **운영 채택 보류**. 단, 점추정 효과 -5.74%p + seed 안정 + depth 25+ 강한 효과 → **방향성은 보존** (코덱스 권고대로 power 보다 effect stability 가 진짜 위험이었던 것 정확히 입증).

## 1. Primary 결과 (FE only vs baseline)

| 항목 | 값 |
|---|---|
| Test-eligible warm artists | **40 명** (가용 모집단 100%) |
| Test rows | **431** (n≥3 작가 한정) |
| Baseline MdAPE | 33.30% |
| FE only MdAPE | **27.08%** |
| 점추정 Δ | **-6.22%p** |
| Cluster bootstrap (n=2000) mean | -5.74%p |
| 95% CI | [-16.01%p, +5.30%p] |
| 1-sided p (P(diff ≥ 0)) | 0.1505 |
| Seed stability (10 seeds × n=500 mean) | -5.84%p (std 0.252) |

**해석**:
- 점추정 + seed 안정성 모두 명확한 개선 방향
- CI 0 포함 → 통계적 유의성 미달 (사전등록 합격 기준 미달)
- Cluster pool 40 의 한계 — 사전 power simulation v2 (44.9% power) 결과 정확히 적중

## 2. Secondary (Holm m=5, primary 와 별도 family)

| Secondary 비교 | mean | CI lo | CI hi | p_raw | Holm reject |
|---|---|---|---|---|---|
| Combined vs baseline | -5.09 | -15.56 | +5.60 | 0.189 | no |
| Combined-shrunk vs baseline | -5.13 | -15.69 | +5.65 | 0.180 | no |
| FE only @ depth 10-14 | +3.92 | -29.99 | +54.05 | 0.531 | no |
| FE only @ depth 15-24 | +2.19 | -19.49 | +13.35 | 0.683 | no |
| **FE only @ depth 25+** | **-17.10** | **-39.53** | **-3.91** | **0.009** | **YES** |

**핵심 발견**: depth 25+ 만 Holm 보정 후 유의 (CI 0 배제). FE only 의 효과가 **고-depth artist 에 집중** 되고 10-14, 15-24 에서는 효과 없음 또는 소폭 악화.

## 3. Composition-shift (Stage 3 vs Stage 4)

| 분류 | n | baseline MdAPE | FE only MdAPE | Δ |
|---|---|---|---|---|
| 신규 warm (Stage 3 외, 79 작가) | 251 | 31.06% | 31.31% | **+0.25%p** |
| 기존 warm (Stage 3 100명 중 41명) | 180 | 36.89% | 23.91% | **-12.98%p** ⭐ |

**해석**: FE only 의 효과는 **기존 작가 (Stage 3 학습 시 충분히 본 작가) 에 집중**. 신규 warm 작가에서는 사실상 효과 없음. 이는 **Artist FE 의 근본적 한계** — train 에서 학습된 dummy 가 신규 작가에 정의상 무력. composition-shift 가 v3 의 핵심 위험이었음 정확히 입증.

## 4. Segment Harm Budget (사전등록 §6.1)

| Segment | n | baseline | FE only | Δ | 임계 | 결과 |
|---|---|---|---|---|---|---|
| price 저가 (P33↓) | 144 | 46.70% | 52.33% | **+5.63%p** | +1.0 | **⚠️ violation** |
| price 중가 (P33-67) | 151 | 24.46% | 23.91% | -0.55%p | +0.5 | ✓ |
| price 고가 (P67↑) | 136 | 38.88% | 18.25% | -20.63%p | +1.0 | ✓ |
| depth 10-14 | 141 | 31.97% | 28.24% | -3.73%p | +1.5 | ✓ |
| depth 15-24 | 127 | 24.55% | 31.31% | **+6.76%p** | +1.0 | **⚠️ violation** |
| depth 25+ | 163 | 36.89% | 22.71% | -14.18%p | +0.5 | ✓ |

**핵심 발견**:
- **저가 (P33↓) +5.63%p 큰 폭 악화** — Stage 3 P2 의 Combined 모델 저가 +3.36%p 악화 패턴과 동일 → FE only 도 저가 segment 에 본질적 위험
- **depth 15-24 +6.76%p 악화** — depth 25+ 강한 개선과 대비. 중간 depth artist 의 FE 가 over-fit 가능성
- **고가 / depth 25+ 큰 폭 개선** — Combined 가 25+ depth 에 효과 집중되는 패턴 일관

## 5. 의사결정 권고

### 5.1 운영 채택
> **운영 채택 보류** — 사전등록 합격 기준 2/4 미달 (CI / harm).

### 5.2 후속 cycle 권고
3 가지 분기 가능:

#### A. Phase 2 (Artsy-only full confirmatory) 진입 보류
- 본 cycle 이 사실상 "Artsy 전체 모집단" 이라 별도 Phase 2 가 동일 데이터 → 결과 변동 X
- → Phase 2 분리 의미 없음, **Phase 2 정의 재검토 필요**

#### B. 외부 source 보강 cycle (auction archives 등)
- 40 cluster 한계 본질적 — 외부 source 없이 power 0.8 도달 불가 (필요 100+ clusters)
- 단, 신규 source = 새 cleansing rule 검증 + selection bias risk

#### C. **Slice-conditional warm path** (가장 실용적, 코덱스 추천 가능)
- depth 25+ 전용 FE only path (이 segment 만 -14.18%p 강한 개선 + Holm 유의)
- 저가 / depth 15-24 segment 는 V3 fallback 유지
- 운영 spec §17 의 라우팅 로직 확장: warm + depth ≥25 → FE only / 그 외 → V3

#### D. warm-only path 후보 폐기
- 사전등록 §6.3: "Segment harm 3개 이상 임계 초과" 미해당 (2건만)
- "depth bin 2개 이상 악화" 도 미해당 (1건만)
- → §6.3 폐기 기준 미달, **§6.2 보류** 적용

### 5.3 권고 (코덱스 자문 전 LLM 의견)
**B + C 병행** — 단기적으로 C (slice-conditional) 가 가장 실용적, 장기적으로 B 가 본질적. A 는 의미 없음, D 는 너무 보수적.

## 6. 코덱스 자문 사항 (다음 라운드)

1. 본 BORDERLINE 판정의 운영 의사결정 implication
2. C (slice-conditional warm path: depth ≥25 만 FE only) 운영 spec 통합 가치 — 추가 segment harm 위험?
3. 저가 segment 의 일관 악화 (P2 Combined +3.36 / 본 cycle FE only +5.63%p) — Huber loss 한계인가, F4 feature 한계인가?
4. composition-shift 결과 (신규 warm +0.25 / 기존 -12.98%p) 의 전략 implication — Artist FE = 사실상 "기존 작가 보너스" 만 작동?
5. Phase 2 정의 재검토 — Artsy 전체 모집단 활용 후 별도 confirmatory 의미?
6. 전체 cycle 종결 vs Stage 5 추가 검토

## 7. 코덱스 자문 결론 (2026-05-07)

> **운영 의사결정자 문구 (코덱스)**:
> "FE only 는 전체 warm 집단에 대한 **일반 해법으로는 입증 실패**. 다만 충분한 이력(depth ≥25)을 가진 기존 warm 작가에서는 강한 개선 신호가 있어, **제한적 라우팅 정책 후보**로는 가치가 있다."

### 7.1 결정 (코덱스 권고)
- **A**. ❌ Phase 2 진입 — 동일 데이터, 의미 없음
- **B**. ✅ Stage 5 = 외부 source 보강 + new prereg (장기)
- **C**. ✅ Slice-conditional warm path (`depth ≥25 + seen-in-training`) → 별도 가설로 분리, shadow mode 파일럿
- **D**. ❌ 완전 폐기 — slice-conditional 가치 살림

### 7.2 저가 segment 일관 악화 가설 우선순위 (코덱스)
1. **feature space 부족** (1순위) — F4 가 저가 결정 요인 못 담음
2. **loss 한계** (2순위) — Huber 가 평균 안정성 주지만 저가 비대칭 비용 못 맞춤
3. **calibration 부족** (3순위, 가장 약함) — segment-aware modeling 이 본질 해법

### 7.3 신규 warm 작가 정책 (코덱스 즉시 권고)
- `seen-in-training` 아닐 경우 자동 fallback
- 최소 support 기준 충족 전 FE 비활성
- 운영 spec §17 라우팅 로직에 즉시 반영

## 8. 다음 단계 (코덱스 7개 액션)

1. **warm-only 일반 경로 종료** 문서화 — 사전등록 §6.2 보류 + `not advanced`
2. **Slice-conditional 새 가설 분리** — spec §17.6 (신규) 에 `depth ≥25 + seen-in-training` 라우팅 명시
3. **저가 segment error decomposition** — price band 별 bias / residual / artist support / proxy 누락
4. **Calibration 독립 검증** — 전체 / 저가 전용 / slice 별 calibration → harm 해소 여부
5. **Stage 5 prereg** — 외부 source 보강 전제 (target cluster + subgroup power 명시)
6. **운영 파일럿** = shadow mode (live X, slice-conditional 추적, segment harm guardrail)
7. **신규 warm 작가 정책 즉시 보수화** — seen-in-training 자동 fallback (spec §17 라우팅 로직)

### 8.1 사용자 결정 우선순위
- **즉시** (LLM 가능): 1, 7 (문서 갱신)
- **단기** (다음 cycle): 2, 3, 4
- **장기** (Stage 5): 5, 6
