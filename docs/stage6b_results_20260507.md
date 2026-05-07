# Stage 6B 결과 보고서 — Partial Pooling FAIL

> **작성일**: 2026-05-07
> **사전등록 v2 freeze**: `docs/stage6b_partial_pooling_prereg_20260507.md` (2026-05-07)
> **실험**: `experiments/structural_v1/stage6b_partial_pooling.py` / `results/stage6b_partial_pooling.json`
> **판정**: **FAIL (🔴 Hard gate Δ_low > 0 위반)**

## 0. 한 줄 요약 (의사결정자용)

> **Stage 6B FAIL** (사전등록 §3.3 hard gate 위반). Overall **-0.09%p (사실상 동등)** + 저가 **+1.29%p 악화** + Mid/high -1.04%p 개선. 즉 6B partial pooling 은 mid/high 만 부분 개선하고 저가에서 악화 — **6A 와 동일 패턴 (저가 segment harm)**.
>
> **4 cycle 일관성 확정**: Stage 4 작업 3 (feature 부족 시그니처) → Stage 5 (acquisition 미개시) → Stage 6A (segmentation +5.23%p) → **Stage 6B (partial pooling -0.09%p, 저가 +1.29%p)** — 모두 **feature shortage 본질** 입증.
>
> **단, Mechanism 작동 ✓**: ICC 0.81 (CI [0.77, 0.84]) — partial pooling 자체는 강하게 작동. 그러나 예측 효과 미미 = **cold-start LAO 에서 random intercept 무력화** (Stage 3 ME 패턴 반복, 코덱스 사전 권고 정확).
>
> → **Architecture-only 트랙 (6A + 6B) 모두 종료**. 후속 = **6C (new-information, pre-screen 후)** 또는 **calibration only 운영 유지** (분기 B).

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

| 조건 | 결과 |
|---|---|
| Primary CI 상한 ≤ 0 | ✗ (+1.42%p) |
| Primary practical Δ ≤ -1.0%p | ✗ (-0.09%p) |
| 🔴 **Hard gate Δ_low ≤ 0%p** | **✗ (+1.29%p 악화)** |
| ICC mechanism CI 하한 > 0 | ✓ (0.7719) — **mechanism 작동 ✓** |

→ **🔴 Hard gate 위반 → 즉시 FAIL** (사전등록 §3.3).

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

## 5. 후속 cycle (코덱스 권고)

### 5.1 Architecture-only 트랙 종료 (확정)
- 6A (segmentation) + 6B (partial pooling) 모두 FAIL
- → Architecture 변경만으로는 feature shortage 해결 X 입증 완료

### 5.2 다음 후보 (2 축)
| 옵션 | 사전 조건 | 가치 |
|---|---|---|
| **6C — new-information** (외부 source) | 4항목 pre-screen (Legal / TOS / Access / Anti-bot) 통과 | feature 추가 = 본질 해결 가능 |
| **운영 calibration only** (분기 B 그대로) | 즉시 가능 | 단기 안전장치 (low -3.11%p 가능) |

> 코덱스 권고: 6C 진행 시 **새 source 발견** 우선 (Stage 5 종료 후 LLM 외 운영팀 / 법무팀 / 데이터팀 작업 영역). Calibration only 는 분기 B 그대로 진행.

## 6. Limitations / 정직 보고

- **Sparse-warm 측정 불가**: LAO 정의상 모순 (사전등록 §2.8.1 #3 deviation, minor)
- **100-seed mean vs single seed cluster bootstrap 차이**: single seed 가 운 좋은 결과 가능 — 100-seed 평균이 더 신뢰할 만함
- **ICC 높음 ↔ 예측 효과 무력**: cold-start LAO 평가의 본질적 한계 (warm-start time-split 평가 시 다를 가능성)
- **Newly-warm subgroup +0.31%p**: 사실상 동등 — Stage 4 의 +0.25%p 패턴 (composition shift) 반복

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
