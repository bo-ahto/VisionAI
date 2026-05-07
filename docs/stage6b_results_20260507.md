# Stage 6B 결과 보고서 — Partial Pooling FAIL

> **작성일**: 2026-05-07
> **사전등록 v2 freeze**: `docs/stage6b_partial_pooling_prereg_20260507.md` (2026-05-07)
> **실험**: `experiments/structural_v1/stage6b_partial_pooling.py` / `results/stage6b_partial_pooling.json`
> **판정**: **FAIL (🔴 Hard gate Δ_low > 0 위반)**

## 0. 한 줄 요약 (의사결정자용 — 코덱스 framing 강화)

> **Stage 6B FAIL** (사전등록 §3.3 hard gate 위반). 효과 없음 ≠ **목표 slice 에서 해로움**: aggregate parity (-0.09%p) but low-slice harm (+1.29%p) → 운영 부적합.
>
> **Mechanism 검증 성공, 제품 목표 실패** (코덱스):
> - ICC 0.81 [0.77, 0.84] — partial pooling 통계적으로 강하게 작동 ✓ (variance reduction 효과)
> - 그러나 LAO cold-start 에서 random intercept 무력화 → **식별 가능한 신규 신호를 만들지 못함**
> - "Hierarchical pooling 자체는 실패가 아니라 mis-targeted" (코덱스)
>
> **4-cycle 일관성 확정**: Stage 4 작업 3 → Stage 5 → Stage 6A → 6B 모두 동일 — **현재 evidence 범위 내 1차 병목 = feature / information shortage** (architecture 가 무가치 아님 / 단지 1차 병목 아님).
>
> **종결 사유** (코덱스): "실패해서 중단" 이 아닌 **"병목 식별 → 자본 배분 전환"**. Architecture-only 트랙 close → **feature / acquisition track** 로 의사결정 이관 (6C 도 architecture 추가 = 낮은 ROI).

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline | Mixed (6B) | Δ (낮을수록 좋음) |
|---|---|---|---|
| **Overall** | 38.05% | 37.96% | **-0.09%p** (사실상 동등) |
| **Low (price < 5M)** | 38.49% | 39.78% | **+1.29%p** ⚠️ Hard gate 위반 |
| Mid/high (≥ 5M) | 37.79% | 36.75% | **-1.04%p** (개선) |
| Newly-warm (Stage 3 외) | 46.03% | 46.34% | +0.31%p (사실상 동등) |
| **Sparse-warm (train ≤5)** | nan | nan | **측정 불가** (deviation, §1.4) |

### 1.2 Cluster bootstrap (rep seed=0, n=2000)
- Δ overall mean: **-1.60%p** (single seed 결과)
- 95% CI: **[-4.04, +1.42]** — 0 걸침
- P(diff ≥ 0) = 0.15

> ⚠️ Single seed 의 cluster bootstrap 점추정 (-1.60%p) 과 **100-seed 전체 평균 (-0.09%p)** 사이 큰 차이 — single seed=0 이 운 좋게 좋은 결과. **100-seed 전체 평균이 더 신뢰할 만한 effect size**.

### 1.3 ICC Mechanism (Holm 외 supportive — 사전등록 §2.8.2)
- ICC mean: **0.81** (Stage 3 의 0.541 보다 높음 — 전체 823 artists 의 이질성 더 큼)
- 95% CI: **[0.77, 0.84]** — CI 하한 > 0 ✓
- → **Partial pooling 자체는 강하게 작동** (artist-level variance 가 80% 이상 차지)

### 1.4 Sparse-warm 측정 불가 (사전등록 deviation)
- 사전등록 §2.8.1 #3: sparse-warm (train count ≤ 5) MdAPE improvement
- **실측 불가**: LAO 평가에서 test artists 는 정의상 train 에 0 작품 — "sparse-warm" 자체 정의 모순
- 100/100 seeds 에서 sparse-warm test sample = 0
- **사후 인정**: 본 항목은 사전등록 시점 design 오류. Time-split (warm threshold) 평가에서만 의미. LAO 에서는 측정 불가.
- **Deviation log entry 의무** (minor — 4-family Holm 중 1 항목 측정 불가, 결과 본 후 변경 X = 정상 흐름)

### 1.5 사전등록 §3 PASS / BORDERLINE / FAIL 판정

> **Hard gate 정의 (사전등록 §3.3 단일 line)**: `Δ_low ≤ 0%p` (100-seed LAO mean 점추정 기준, 운영 spec §17 저가 segment harm 절대 금지 원칙과 동일).
>
> **판정 rule**: Hard gate 위반 시 primary / secondary 결과 무관 **즉시 FAIL** (`사전등록 §3.3`). Hard gate 통과 후에만 primary CI 상한 ≤ 0 + practical Δ ≤ -1.0%p 동시 충족 → PASS / 하나만 충족 → BORDERLINE / 둘 다 미달 → FAIL.

| 조건 | 결과 |
|---|---|
| 🔴 **Hard gate Δ_low ≤ 0%p (단독 즉시 FAIL trigger)** | **✗ (+1.29%p 악화)** |
| Primary CI 상한 ≤ 0 | ✗ (+1.42%p) |
| Primary practical Δ ≤ -1.0%p | ✗ (-0.09%p) |
| ICC mechanism CI 하한 > 0 | ✓ (0.7719) — **mechanism 작동 ✓** |

→ **🔴 Hard gate 위반 → 즉시 FAIL** (사전등록 §3.3). Primary 와 secondary 모두 동시 미달 (Hard gate 무관 동일 결론) — **aggregate parity but low-slice harm** (코덱스 framing).

## 2. 4-Cycle 일관성 (의사결정자 압축)

> **본 6B 결과로 4 cycle 일관성 확정**: 현재 운영 모델 (F4 + spline + Huber) 의 한계는 **architecture / acquisition 의 결함이 아니라 input feature space 자체의 정보 부족**.

| Cycle | 가설 | 결과 | 저가 segment |
|---|---|---|---|
| Stage 4 작업 3 | Calibration 으로 해결? | ✗ Feature 부족 시그니처 3/3 | bias structural |
| Stage 5 (5A-5C) | External source 으로 해결? | ✗ 준법적 자동화 불가 미개시 종료 | (미실행) |
| Stage 6A | Segmentation 으로 해결? | ✗ +5.23%p 악화, hard gate 위반 | +3.54%p 악화 |
| **Stage 6B** | **Partial pooling 으로 해결?** | ✗ -0.09%p 동등, hard gate 위반 | **+1.29%p 악화** |

→ **Architecture-only 트랙 (6A + 6B) 모두 종료**. Information sharing 도 segmentation 도 저가 harm 해결 X.

## 3. 6B 의 Mechanism 가치 (정직 보고)

### 3.1 ICC 결과 의미
- ICC 0.81 = **artist-level heterogeneity 가 전체 분산의 80%** 차지
- partial pooling 자체는 매우 효과적 (artist random intercept 가 가격 분산 대부분 흡수)
- Stage 3 (ICC 0.541) 보다 높음 — 전체 823 artists pool 의 이질성 더 큼

### 3.2 그럼에도 LAO 예측 무력화 이유
- LAO = test artists 가 train 에 0 작품 (정의상 cold-start)
- u_j (artist random intercept) = 0 으로 수축 (Stage 3 ME 와 동일 패턴)
- 즉 partial pooling 의 "예측 효과" 는 warm artists (train 에 학습된 artist) 에게만 작동
- **LAO 평가는 partial pooling 의 generalization 효과를 측정하지 않음** (정직 보고)

### 3.3 코덱스 사전 권고 정확 입증
> 사전등록 §1.3: "Cold-start 대폭 개선 = 주가설 아님 (Stage 3 ME 패턴 인정)"
> §9: "정직한 기대 = variance reduction 기반 modest improvement (-0.5 ~ -1.5%p)"

→ 100-seed 평균 -0.09%p = **기대 범위 하한도 미달**. partial pooling 의 LAO 효과 = 사실상 0.

## 4. 운영 영향 X

### 4.1 운영 spec 변경 X
- 본 6B FAIL → **운영 spec §17 partial pooling fixed effect 추가 X**
- Cold rollout 운영 모델 (F4 + spline + Huber) 그대로 유지
- Spec §4.0 calibration 후처리 후보 (분기 B 결정) 그대로 진행

### 4.2 6B 폐기 정당성
- 사전등록 §3.3 "🔴 Hard gate 위반 시 즉시 FAIL" 적용
- 결과 본 후 임계 변경 X (HARK 회피)

## 5. 후속 cycle (코덱스 권고 — Architecture close, Feature track 우선)

### 5.1 Architecture-only 트랙 close (확정)
- 6A (segmentation) + 6B (partial pooling) 모두 FAIL
- → "Architecture-only 트랙은 신호 부족 문제를 해결하지 못했으며, 병목은 feature/information shortage 에 있다" (코덱스)
- **Hierarchical pooling 자체는 실패가 아니라 mis-targeted** — 현재 문제의 1차 병목이 아님

### 5.2 다음 후보 우선순위 (코덱스)
| 순위 | 옵션 | 가치 |
|---|---|---|
| **1** | **Feature / acquisition track** (low 구간 식별력 보강) | 본질 해결 — 1차 병목 직접 공략 |
| 2 (보조) | Calibration only (분기 B) | 배포 안정성 / threshold tuning 목적만 — 핵심 개선 트랙 X |
| 3 (낮은 ROI) | 6C architecture 추가 | **새 식별 가설 있을 때만 reopen** — 현 evidence 상 낮은 ROI |

> 코덱스 권고: "특별한 새 가설 없이 6C 를 돌리면 지금까지 evidence 상 낮은 ROI 의 반복 가능성 큼". Feature / acquisition 우선 / 6C 보류.

## 6. Limitations / 정직 보고

- **Sparse-warm 측정 불가**: LAO 정의상 모순 (사전등록 §2.8.1 #3 deviation, minor) — 향후 sparse-warm 은 LAO 가 아닌 별도 metric/spec (time-split warm threshold) 으로 분리 필요
- **100-seed mean vs single seed cluster bootstrap 차이**: single seed 가 운 좋은 결과 가능 — 100-seed 평균이 더 신뢰할 만함
- **ICC 높음 ↔ 예측 효과 무력**: cold-start LAO 평가의 본질적 한계 (warm-start time-split 평가 시 다를 가능성)
- **Newly-warm subgroup +0.31%p**: 사실상 동등 — Overall Δ std (1.87%p) 대비 small effect → **noise 범위 내** (코덱스 권고 — transferable signal X)

### 6.1 Low (<5M) 악화 분해 (코덱스 P1 권고)
- Low pool: 4,635 작품 / 637 artists (전체 cleansed 의 절반 이상)
- 상위 5 작가 (do-you-hwang 126 / kyong-lee 74 / winter-gyeoul-kim 52 / kang-yehsine 46 / kwon-hye-jo 45) — **특정 작가 집중 X**, 분산 분포
- 즉 +1.29%p 악화는 특정 subslice 가 아닌 **저가 segment 전반의 systematic harm** — Stage 4 단기 트랙 작업 3 의 "feature shortage 시그니처 3/3" 입증과 일관

### 6.2 ICC 0.81 → ranking gain vs shrinkage 분리 (코덱스 P2)
- 본 cycle 측정 X (별도 decomposition 필요)
- 추후 권고: 추가 분석 시 (a) ranking AUC / Spearman corr 비교 (b) artist-level prediction gradient 분리
- 현재 evidence: ICC 자체가 ranking gain 보다 **variance suppression** 가능성 큼 (LAO 무력화 + low harm 패턴 일관)

## 7. 다음 단계

1. ✅ 본 6B 결과 보고 — 본 commit
2. ⏳ Deviation log: sparse-warm 측정 불가 (minor) + 4-cycle 일관성 확정 entry
3. ⏳ Stage 6 prereg draft v3: 6B FAIL 반영 + architecture-only 트랙 종료
4. ⏳ 종합 대시보드 갱신
5. ⏳ 코덱스 검토 — FAIL 정당성 + 6C 진행 우선순위 + 운영 framing
6. ⏳ (사용자 결정) 6C 진행 / Calibration only 운영 적용 / Cold Phase A 시작

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B prereg 사전 자문 (2026-05-07) | statsmodels MixedLM / Δ 6A 동일 / Holm m=4 + ICC mechanistic |
| Stage 6B prereg 검수 P1 (2026-05-07) | is_low_price 타깃 누수 → 삭제 / hard gate 단일화 / fallback canonical |
| **본 결과 보고 (2026-05-07)** | FAIL 판정 + 4 cycle 일관성 + sparse-warm deviation (예정) |
