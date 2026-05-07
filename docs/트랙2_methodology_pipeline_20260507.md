# 트랙 2 실험 방법론 — Curated Exploratory → Full Confirmatory Pipeline

> **작성일**: 2026-05-07
> **목적**: 트랙 2 모든 후속 실험의 방법론 골격 + curated → full 2단계 pipeline + pre-registered analysis 규율
> **연계**: `docs/트랙2_최종보고서_20260506.md` §6 / `docs/트랙2_production_통합_spec_20260507.md` §17 / `docs/stage4_확장검증계획_20260507.md`
> **사전 자문**: 코덱스 (D + curated→full pipeline 자문, 2026-05-07)

## 0. 핵심 원칙

| 원칙 | 의미 |
|---|---|
| **Phase 분리** | Stage 1-4 = curated exploratory / Phase 2 = full confirmatory replication |
| **Pre-registration** | 가설 / metric / 임계 / 다중비교 보정 사전 고정 |
| **Single primary hypothesis** | 채택 결정은 단일 비교 (baseline vs champion) — 다중비교 부담 최소화 |
| **Practical significance 사전 고정** | 통계 유의성만으로 채택 X — 최소 실용 효과 미리 정의 |
| **Segment harm budget** | overall 개선이어도 특정 segment 악화 허용치 사전 정의 |
| **Threshold/feature freeze** | curated 에서 선택한 모든 것은 full 진입 전 동결 — 변경 시 새 exploratory cycle |
| **Deviation log** | 사전등록 vs 실제 진행 차이 모두 기록 |
| **Single source of truth** | 사전등록 / 결과 / deviation log 3 문서 분리 |

## 1. 2단계 Pipeline 구조

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1 — Curated Exploratory Program                   │
│   data/curated/stage{1,2,3,4}_*.parquet                 │
│                                                         │
│   Stage 1 (200/20)  — Rules verification                │
│   Stage 2 (500/50)  — OLS Hedonic exploration           │
│   Stage 3 (1378/100) — Final candidate (운영 채택)       │
│   Stage 4 (목표 200+)— Stage 4 leading candidate 검증 gate    │
│                                                         │
│   ▶ Pre-registered analysis plan (Stage 4 부터 적용)     │
│   ▶ Leading candidate 후보 압축 + 통계 검증                       │
└─────────────────────────────────────────────────────────┘
                       │
                       │ Gate 1: Stage 4 leading candidate 검증 통과
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2 — External Feature Acquisition + Validation     │
│   = Stage 5 (5A acquisition / 5B integration / 5C model) │
│   (v4 재정의 — Artsy-only confirmatory 폐지)             │
│                                                         │
│   Stage 5A: Source feasibility + acquisition prereg     │
│   Stage 5B: Entity resolution + feature construction    │
│   Stage 5C: Confirmatory modeling (별도 prereg)         │
│   Stage 5D: Deployment / legal / monitoring             │
│                                                         │
│   ▶ 5A-5B prereg ↔ 5C prereg 분리 (HARK 회피)            │
│   ▶ Stage 4 결과 (feature 부족 입증) 가 Stage 5 input    │
└─────────────────────────────────────────────────────────┘
                       │
                       │ Gate 2: Full pass
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3 — Production Validation (운영 검증)              │
│   Shadow → Canary → Full rollout                        │
│   spec §1-§17 정의                                       │
│                                                         │
│   ▶ Gate 3: 운영 검토 (segment harm + calibration + OOD)│
└─────────────────────────────────────────────────────────┘
```

## 2. Phase 1 — Curated Exploratory Program

### 2.1 데이터 (`data/curated/`)
| Stage | 표본 | 목적 | 산출물 |
|---|---|---|---|
| Stage 1 | 200/20 | rules verification | rules log |
| Stage 2 | 500/50 | OLS hedonic exploration | feature 후보 |
| Stage 3 | 1,378/100 | final candidate (운영 cold 모델) | F4+spline+Huber |
| Stage 4 | 200+ artists / warm 40+ / depth bin 균형 | Stage 4 leading candidate 검증 | FE only 확정 후보 |

### 2.2 Phase 1 의 자유도 (exploratory)
- 가설 추가 / 수정 가능
- Feature 변형 / hyperparameter 탐색 가능
- 모델 family 비교 가능
- **단**: 모든 결과는 "indicative", 운영 채택 결정 근거 X

### 2.3 Phase 1 결과 해석 규율
- 점추정 + CI 보고 시 항상 "exploratory, multiple comparisons unadjusted" caveat
- 채택 결정 시 Phase 2 replication 필수

## 3. Phase 2 — External Feature Acquisition + Validation (Stage 5)

> **v4 재정의 (2026-05-07, Stage 4 결과 후)**: 기존 v3 의 "Artsy-only confirmatory" 도 폐지. Stage 4 가 사실상 Artsy 전체 모집단 활용 → 동일 데이터 반복 의미 없음. **Phase 2 = Stage 5 = External Feature Acquisition + Validation** (코덱스 권고).
>
> **v3 정정 기록 (2026-05-07)**: 기존 "Artsy + Saatchi 통합 28K" 가정은 inventory 검증으로 반박됨. Saatchi 는 `year_made` 100% 결측 + `birth_year` 9% 만 → F4 + time-split 불가 → Phase 2 모집단에서 제외.

### 3.1 데이터 (Stage 5)
| Stage | 데이터 | 사전등록 | Phase 활용 |
|---|---|---|---|
| Stage 5A | External source candidate (auction / Artsy CV / 등) | `docs/stage5a_acquisition_prereg_20260507.md` | feasibility + acquisition |
| Stage 5B | Matched dataset + feature dictionary | (5A 산출물) | entity resolution + feature construction |
| Stage 5C | `data/curated/stage5_*.parquet` (Stage 4 + external 통합) | `docs/stage5c_modeling_prereg_20260507.md` | confirmatory modeling |
| Stage 5D | Production validation | (5C PASS 후) | deployment / monitoring |

> **Stage 4 (Artsy-only) 대비 Stage 5 의 가치**: feature 부족 본질 해결 (auction price anchor / provenance / market activity 등)

### 3.2 Stage 5C Confirmatory protocol (pre-registered)
- **Primary hypothesis**: External-feature model MdAPE < baseline MdAPE (1-sided)
- **Practical significance**: ≤ -2.0%p (baseline 24.07% → 22% 이내)
- **Pre-registered protocol** (`docs/stage5c_modeling_prereg_20260507.md`):
  - Baseline / metric / Holm family / PASS 기준 5A 결과 보기 전 freeze
  - 5A-5B 결과 dictionary 확정 시 placeholder re-freeze (deviation log 의무)
- **Curated (Stage 4) 와 차이 분석 protocol** (필수):

| 차이 유형 | 평가 항목 | 도구 |
|---|---|---|
| **Data quality** | external source 의 결측 / 매칭 실패율 / outlier | entity resolution audit |
| **Selection bias** | external cover artist vs Artsy-only artist 의 분포 차이 | PSI / KS |
| **Population effect** | external 통합 군 vs Artsy-only 군 성능 차이 | subgroup MdAPE |

### 3.3 Stage 5C 합격 기준 (사전 고정, `stage5c_modeling_prereg` §3)
- Primary CI 상한 ≤ 0
- Practical Δ ≤ -2.0%p (point estimate)
- Seed std ≤ 0.5%p
- Segment harm 0 violations
- 신규 warm 작가 generalization 개선 또는 동등

## 4. Pre-registered Analysis Plan (Phase 1 Stage 4 부터 적용)

### 4.1 사전 등록 항목 (Stage 4 시작 전 freeze)

| 항목 | 사전 고정 값 |
|---|---|
| Primary hypothesis | H₀: MdAPE(FE only) ≥ MdAPE(baseline) / H₁: MdAPE(FE only) < MdAPE(baseline) |
| Primary metric | warm-only MdAPE (artist-cluster bootstrap, n=2000) |
| Primary test | **1-sided 95% CI, 단일 비교 (unadjusted)** — 채택 결정의 유일한 통계 게이트 |
| Practical significance | MdAPE 차이 ≤ -0.8%p (상한) |
| Sample 분할 | Train ≤ 2023 / Val == 2024 / Test == 2025 (3-way) + rolling sensitivity cutoff (2022 / 2023 / 2024, 3개) |
| Stratification | warm artist depth bin (10-14 / 15-24 / 25+) |
| Bootstrap unit | artist cluster (row 단위 X) |
| Seed 안정성 | 10 seed 평균 + std (std ≤ 0.5%p 요구) |

### 4.2 Secondary hypotheses (descriptive, Holm m=5 별도 family)

> Secondary 5개 비교는 별도 family 로 Holm 보정 적용 — **Primary family 와 분리**, primary 통과 여부와 독립적으로 보고.

- Combined vs baseline
- Combined-shrunk vs baseline
- FE only @ depth bin 10-14 vs baseline
- FE only @ depth bin 15-24 vs baseline
- FE only @ depth bin 25+ vs baseline

### 4.3 Deviation rule
- 사전등록 vs 실제 차이 발생 시 별도 deviation log 작성
- 차이 > minor 시 새 exploratory cycle 로 분리 (re-confirm 필요)

## 5. 다중비교 보정 (Multi-comparison Correction)

### 5.1 보정 방법 선택 (Stage 4 부터, 2 family 분리)
- **Primary family**: 단일 비교 unadjusted (운영 채택 게이트 — Stage 4 § 6.0 / Stage 5C § 2.6)
- **Secondary family**: Holm-Bonferroni (sequential, less conservative) — primary 와 별도 family
- **Sensitivity**: Bonferroni (most conservative, 부록 보고)
- **Family-wise α = 0.05** (each family)

### 5.2 Stage 3 결과 재계산 (C)
- 별도 실험 `stage3_warm_holm_adjusted.py` 진행
- Phase 1 의 모든 모델 비교에 Holm 적용 후 95% CI 재계산
- 후속 의사결정에는 보정 후 CI 사용

### 5.3 Stage 4 적용 (코덱스 권고 반영, 2 family 분리)
- **Primary family** (운영 채택 게이트): primary 1개 단일 비교 (unadjusted) — 가장 깔끔
- **Secondary family** (descriptive 보고): secondary 5개에만 Holm 적용 — primary 와 독립
- 이 구조는 운영 결정 단순성 + descriptive 분석 풍부성 모두 확보

## 6. Sample Size Justification (v3 — 실측 기반)

### 6.1 Stage 4 가용 풀 (실측, `stage4_funnel.json` + `stage4_power_simulation_v2.json`)
- 모집단 = Artsy cleansed 100% 활용 (외부 source 없음)
- Test-eligible warm artist clusters: **40** (Stage 3 의 13 → 3.1×)
- Warm test rows: 450 total / 431 eligible (n≥3 작가)
- α = 0.05 (1-sided)
- **실측 power @ 40 clusters = 44.9%** (목표 0.80 미달)
- 0.8 power 도달 필요 clusters: 100 (외부 source 없이 도달 불가)

### 6.2 해석 초점 (코덱스 권고)
- Power 자체보다 **effect stability 우선** — heterogeneity / outlier / 2025 sparsity / bin imbalance 가 진짜 위험
- Stage 4 합격 기준 (CI 상한 ≤ 0) 통과는 매우 어려울 수 있음
- 본 cycle 의 정직한 기대: **effect 방향성 + segment harm 검증** (통계적 유의성 보장 X)

### 6.3 Phase 2 (Stage 5) 진입 전 추가 power 계산
- 기존 Artsy-only 풀 만으로는 추가 power 확보 X (Stage 4 결과로 입증)
- **Stage 5 = External feature acquisition (auction / provenance / 등) 보강 cycle** — 5C 시작 전 power simulation 의무

## 7. Calibration / OOD / Drift (추가 권고)

### 7.1 Calibration (Phase 2 부터 필수)
- 예측 가격 vs 실제 가격 quantile-quantile plot
- Predicted band coverage (band [-20%, +20%] 의 hit rate)
- 가격 quantile bin 별 calibration

### 7.2 OOD detection
- curated 분포 밖 sample (PSI > 0.25) 의 성능 별도 평가
- 새로운 작가 vs 기존 작가 분리

### 7.3 Drift monitoring
- Time bucket 별 (year_made / sale_year) 성능 추이
- Source mix shift 영향

## 8. Segment Harm Budget (사전 고정)

| Segment | 허용 악화 (vs baseline) |
|---|---|
| 가격 저가 (P33 미만) | +1.0%p |
| 가격 중가 (P33-P67) | +0.5%p |
| 가격 고가 (P67+) | +1.0%p |
| Source: Artsy (Stage 4 cycle) / Stage 5 = Artsy + external (auction 등) | +1.0%p |
| Medium: oil / acrylic | +0.5%p |
| Medium: 기타 | +1.5%p |
| Depth bin 10-14 | +1.5%p |
| Depth bin 15-24 | +1.0%p |
| Depth bin 25+ | +0.5%p |

→ 어떤 segment 라도 위 임계 초과 시 채택 거부

## 9. 운영 의사결정자 framing

### 9.1 의사소통 핵심 메시지
- "Phase 1 (curated) 에서 후보를 압축했고, 성능 개선 신호는 일관되게 관찰됐다."
- "현재 증거는 curated exploratory 결과 — 최종 운영 채택은 Phase 2 (full confirmatory) replication 후 결정한다."
- "Phase 2 는 보수적 절차가 아니라 **통제된 검증** — false positive 비용을 줄이는 의도적 단계."

### 9.2 단계별 신뢰도 레벨

| 단계 | 결과 신뢰도 | 의사결정 적합성 |
|---|---|---|
| Phase 1 Stage 1-3 | indicative (multiple comparisons unadjusted) | 후보 압축 only |
| Phase 1 Stage 4 | indicative + Holm 보정 | leading candidate 검증 통과 (운영 채택은 Phase 2 후) |
| Phase 2 Confirmatory Run 1 | confirmatory (pre-registered) | 운영 채택 후보 |
| Phase 3 Shadow / Canary | online verified | 점진 운영 도입 |

### 9.3 표현 규율
- "Phase 1 결과" → "기각되지 않은 유망 신호"
- "Phase 2 결과" → "재현된 개선 효과"
- "Phase 3 결과" → "운영 환경에서 확인된 개선"
- ❌ "Phase 1 에서 X% 개선 확인" (확정적 표현 금지)

## 10. Single Source of Truth — 3 문서 분리

| 문서 | 위치 | 갱신 시점 |
|---|---|---|
| **사전등록** | Stage 4 plan §pre-registration (신규) | Phase 1 Stage 3 종료 시점 freeze |
| **결과 보고** | 보고서 §12 부록 / Phase 2 결과 보고서 (신규) | 각 단계 종료 시 작성 |
| **Deviation log** | `docs/methodology_deviation_log.md` (신규) | 차이 발생 즉시 기록 |

## 11. 다음 액션 (코덱스 권고 8개)

| # | 액션 | 우선순위 | 담당 단계 |
|---|---|---|---|
| 1 | "Stage 1-4 = curated exploratory / Phase 2 = full confirmatory" 용어 고정 | 즉시 | 본 문서 |
| 2 | curated / full 각각 train/val/test 분리 split 표 추가 | 즉시 | 본 문서 / Stage 4 plan |
| 3 | Stage 4 primary hypothesis = baseline vs FE only 단일화 | 즉시 | Stage 4 plan |
| 4 | 사전등록 문서 작성 (gate / 다중비교 / deviation rule) | 즉시 | Stage 4 plan §pre-registration |
| 5 | Stage 3 결과 Holm 보정 재산출 | 즉시 | C 실험 |
| 6 | 보고서 §6 한계 추가 (test reuse / 3-way split / multi-comparison / external validity) | 즉시 | B |
| 7 | curated vs full 분포 비교 표 (source / price / exposure / missingness) Phase 2 필수 | Phase 2 진입 전 | 본 문서 §3.2 |
| 8 | full confirmatory 시작 전 sample size 숫자 고정 | Phase 2 진입 전 | Stage 4 plan |

## 12. 참조

- 트랙 2 최종보고서: `docs/트랙2_최종보고서_20260506.md` (§6 한계 / §12 부록)
- Production spec: `docs/트랙2_production_통합_spec_20260507.md` (§17 warm-only)
- Stage 4 plan: `docs/stage4_확장검증계획_20260507.md` (§pre-registration 신규)
- 데이터 클렌징: `docs/데이터클렌징_단계계획_20260506.md` (Stage 1-3 cleansing)
- Holm 보정 실험: `experiments/structural_v1/stage3_warm_holm_adjusted.py` (신규)
