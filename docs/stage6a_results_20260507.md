# Stage 6A 결과 보고서 — Segmented Architecture FAIL

> **작성일**: 2026-05-07
> **사전등록**: `docs/stage6a_segmented_prereg_20260507.md` (2026-05-07 freeze)
> **실험**: `experiments/structural_v1/stage6a_segmented.py` / `results/stage6a_segmented.json`
> **판정**: **FAIL (🔴 저가 harm hard gate 위반)**

## 0. 한 줄 요약 (의사결정자용)

> **Stage 6A FAIL** — Segmented architecture 가 baseline 대비 overall +5.23%p / 저가 +3.54%p / mid-high +6.97%p **모두 악화**. Router 품질은 좋음 (recall 0.87 / balanced acc 0.85). 코덱스 권고대로 **"segmenting 으로 자동 해결 X / feature shortage 본질"** 정확히 입증.
>
> → **6B Bayesian / hierarchical 우선 검토**, segmented 폐기.

## 1. 핵심 결과 (사전등록 §3 적용)

### 1.1 100-seed LAO MdAPE

| Metric | Baseline (운영 채택) | Segmented (Meta-router + L + H) | Δ |
|---|---|---|---|
| **Overall** | 38.05% | **43.28%** | **+5.23%p** ⚠️ |
| Low (price < 5M) | 38.49% | 42.03% | **+3.54%p** ⚠️ |
| Mid/high (≥ 5M) | 37.79% | 44.76% | **+6.97%p** ⚠️ |

> 본 평가의 baseline 38.05% 는 8,495 cleansed 전체 cold-start LAO 결과. Stage 3 의 24.07% (curated 1,378) 와 다른 — baseline 정의 동일하나 population 다름. **본 6A 의 비교 단위 = baseline ↔ segmented 동일 population 의 Δ**.

### 1.2 Cluster bootstrap (n=2000, seed=42)
- Δ overall mean: **+3.60%p (악화 방향)**
- 95% CI: **[-0.19, +7.19]**
- P(diff ≥ 0) = **0.97** (악화 신뢰도 매우 높음)

### 1.3 Router 품질 (100-seed mean)
| 지표 | 결과 | 임계 | 판정 |
|---|---|---|---|
| Low recall | 0.871 | ≥ 0.85 | ✓ |
| Balanced acc | 0.852 | ≥ 0.75 | ✓ |
| Brier score | 0.113 | ≤ 0.20 | ✓ |

→ **Router 자체는 양호** (LogisticRegression on F4+spline, threshold 0.5). 문제는 segmentation 후 학습된 Model L / Model H 의 성능.

### 1.4 사전등록 §3 PASS / BORDERLINE / FAIL 판정

| 조건 | 결과 |
|---|---|
| Primary CI 상한 ≤ 0 | ✗ (+7.19%p) |
| Practical Δ ≤ -1.0%p | ✗ (+5.23%p 악화) |
| 🔴 **Hard gate 저가 harm = 0** | **✗ 83/100 seeds 저가 악화** |
| Mid/high 비악화 (≤ +0.5%p) | ✗ 93/100 악화 |
| Router low recall ≥ 0.85 | ✓ (0.871) |
| Router balanced acc ≥ 0.75 | ✓ (0.852) |

→ **🔴 Hard gate 위반 + Primary CI/practical 둘 다 미달 → FAIL** (사전등록 §3.3).

## 2. 원인 분석 (코덱스 권고 사전 명시)

### 2.1 코덱스 사전 권고 (prereg §1.3)
> "Segmentation 만으로 feature 부족 (Stage 4 결과) 자동 해결 가정 X — feature shortage 가 본질, segmentation = pooled bias 감소만"

### 2.2 실측 입증
- **Router 품질 충분** (recall 0.87 / balanced acc 0.85) — router 가 segment 분류 잘 함
- **하지만 Model L + Model H 모두 baseline 보다 큰 폭 악화** — segmentation 후 각 segment 의 sample 절반으로 감소 (Train n=4,207 → low 1,906 / mid-high 2,301)
- **Feature 동일** (F4 + spline) → segment 분리 후 정보량 감소
- → "Segmentation 으로 pooled bias 감소" 가설 자체 X — pooled bias 가 컸지만 sample 풍부한 baseline 이 더 강건

### 2.3 정량 검증 — feature shortage 가 본질
| 단계 | 결과 |
|---|---|
| Stage 4 단기 트랙 작업 3 (feature decomp) | Feature 부족 시그니처 3/3 (코덱스 1순위 정확) |
| Stage 4 단기 트랙 작업 4 (calibration) | Global additive cold baseline -3.11%p (단순 후처리도 부분 효과) |
| Stage 5 (External acquisition) | 준법적 자동화 불가 → 미개시 종료 |
| **Stage 6A (Segmentation)** | **+5.23%p 악화** — segmentation = feature 추가 X / 학습 sample 감소 |

→ **3개 cycle 일관: feature 부족 = 본질, architecture 변경만으로 해결 X**

## 3. Hard Gate 위반 명세 (저가 harm)

- 100 seed 중 **83 seeds 에서 저가 segment Δ_low > 0** (악화)
- 단순 평균: low Δ +3.54%p
- 사전등록 §2.8 segment harm budget 의 "🔴 저가 0%p hard gate" 위반 → **즉시 FAIL** (사전등록 §3.3)

## 4. 운영 영향

### 4.1 운영 spec 변경 X
- 본 6A FAIL → **운영 spec §17 routing 로직 추가 X**
- Cold rollout 운영 모델 (F4 + spline + Huber) **그대로 유지**
- Spec §4.0 calibration 후처리 후보 (분기 B 결정) 그대로 진행

### 4.2 6A 폐기 정당성
- 사전등록 §3.3 "🔴 Hard gate 위반 시 즉시 FAIL" 적용
- 결과 본 후 임계 변경 X (HARK 회피)
- BORDERLINE 검토 X (저가 harm 0건이 hard gate)

## 5. 6B Bayesian / Hierarchical 우선 검토 권고 (코덱스)

### 5.1 6B 의 6A 와 차이
- 6A: segment 분리 학습 (sample 감소) + Meta-router (외부 분류)
- 6B: **partial pooling** (작가별 random intercept + global pool) — sample 통합 학습 + 작가별 보정
- 핵심: sample 감소 X / sparse artist 자동 처리 / cold-warm 경계 자동 보정

### 5.2 6B 가설
- artist-level partial pooling → 신규 작가 (Stage 4 의 +0.25%p 효과 없음 문제) 자동 처리
- Uncertainty-aware fallback (V3 자동 라우팅 시 신뢰도 기반)
- **Feature 부족 본질은 여전히 미해결** — 단, 통계적 처리로 부분 완화 시도

### 5.3 6B prereg 작성 시 주의
- 6A FAIL 의 본질 (feature shortage) 인식 명시
- "6B 만으로 자동 해결 가정 X" — 단, partial pooling 의 본질적 가치 (artist sparse handling) 검증
- 임계 완화 X — 6A 와 동일 PASS / BORDERLINE / FAIL 기준 유지

## 6. 사전등록 §7 후속 cycle 시나리오 적용

| 시나리오 | 적용 |
|---|---|
| FAIL (저가 harm) | **6A 폐기 + 6B 우선 검토** ✓ |

## 7. 다음 단계

1. ✅ 본 6A 결과 보고 — 본 commit
2. ⏳ **6B Bayesian prereg 작성** (hypothesis / metric / PASS 기준 사전 fix)
3. ⏳ 6B 실험 + 결과 보고
4. ⏳ 6C 새 source pre-screen (별도, 4 항목 통과 시)
5. ⏳ Cold Phase A shadow 시작 (운영 인계, 6A FAIL 영향 X)
6. ⏳ Calibration 운영 통합 (분기 B, 6A FAIL 영향 X)

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 2026-05-07 사전 자문 | Routing (b) Meta-router / Δ ≤ -1.0%p / Secondary 수정 / harm 0 hard gate |
| 2026-05-07 본 결과 보고 | FAIL 판정 정당성 + 6B 진입 권고 (예정) |

## 9. Limitations / 정직 보고

- 본 6A 평가 = cold-start LAO 100-seed (Stage 3/4 동일)
- Baseline 38.05% 는 8,495 cleansed 전체 분포 — Stage 3 24.07% (curated 1,378) 와 다름 (population 차이, 비교 단위 영향 X)
- Sensitivity (router threshold 0.4 / 0.6) = 본 보고 X (PASS 결정 영향 X — 이미 FAIL)
- 6B 검토 시 본 6A FAIL 의 본질 (feature shortage) 인식 의무
