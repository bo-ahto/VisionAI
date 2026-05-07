# Methodology Deviation Log

> **목적**: Pre-registered analysis plan 대비 실제 진행 차이 기록
> **연계**: `docs/트랙2_methodology_pipeline_20260507.md` §10 / `docs/stage4_확장검증계획_20260507.md` §6.4
> **작성 규율**: 차이 발생 즉시 기록, major deviation (가설/metric/임계 변경) 시 새 exploratory cycle 분리

## Format

각 항목:
```
### YYYY-MM-DD — [단계] [요약]
- **사전등록**: 원래 계획
- **실제**: 변경 / 추가 / 생략된 사항
- **이유**: 변경 배경
- **분류**: minor (기록만) / major (재실험 필요)
- **영향**: 결과 신뢰도 / 후속 단계 영향
- **승인**: 승인자 / 코덱스 자문 차수
```

## Phase 1 (Curated Exploratory) — Pre-registration 부재 기간

> Stage 1-3 + warm 검증 (P2/P3/feature 재탐색/robustness/Holm 보정) 은 사전등록 적용 전 진행.
> Phase 1 의 모든 결과는 exploratory 로 분류되며, 운영 채택 결정 근거 X.
> 사전등록 본격 적용은 **Stage 4 시작 시점부터**.

### 2026-05-07 — [Phase 1 종료] 사전등록 적용 시점 명확화
- **사전등록**: Stage 1-3 시점에는 사전등록 부재 (전체 exploratory)
- **실제**: 코덱스 자문 11회 + warm 추가 4회로 분석 항목 결과 보고 추가됨
- **이유**: Phase 1 = exploratory program 의 자연스러운 진행
- **분류**: 본질적 (Phase 1 정의의 일부)
- **영향**: 모든 Phase 1 결과는 "indicative" — Phase 2 replication 필수
- **승인**: 본 methodology pipeline 문서 작성 (2026-05-07)

## Phase 1 → Phase 2 전이 (Stage 4)

### 2026-05-07 — [Stage 4 v3] Inventory 미검증 기반 source 가정 폐기 (major)
- **사전등록 v1/v2**: Artsy 추가 크롤 + Saatchi 추가 수집 + 갤러리 직접 제공 + Auction archives → 4주 수집형 일정. Stage 4 목표: warm artists 21→40+ / test 평가 가능 13→25+ / warm test rows 44→120+
- **실제 (v3 정정)**: 사용자 지적 후 데이터 inventory 검증. **신규 수집 불필요**. Artsy raw 30,046 → cleansing 8,891 / 823 작가만으로 충분. Saatchi 는 `year_made` 100% 결측 / `birth_year` 9% — F4 + time-split 불가 → Phase 2 모집단에서 제외.
- **새 목표 (v3)**: warm artists 120 (전수) / test 평가 가능 40 (전수) / warm test rows 450 (전수). 일정 4주 → 1-2주.
- **이유**: 이전 plan 작성 시 inventory 검증 누락 — `Don't assume` 원칙 위반
- **분류**: **major** — source / 일정 / 목표 모두 변경. 단, primary hypothesis / metric / 임계 / Holm family 등 통계 사전등록 항목은 **변경 없음** (목표는 floor → 더 쉽게 달성 가능).
- **영향**: 
  - Stage 4 plan 전면 정정 (`docs/stage4_확장검증계획_20260507.md`)
  - methodology pipeline §3.1 Phase 2 정의: "28K 통합 full" → "Artsy-only cleansed 8,891"
  - Power simulation 재실행 필요 (v1 outlier 영향 과대평가 → v2 실제 풀 기반)
  - Power v2 결과 (40 clusters @ 44.9% power) → 합격 기준 통과 어려울 수 있음 caveat
- **승인**: 사용자 지적 (2026-05-07) + 코덱스 자문 (Stage 4 plan 정정 자문)
- **프로세스 강화 (재발 방지)**: 향후 사전등록 freeze 전 의무 순서 = `inventory 검증 → cleansing pass → split viability → target setting`

### 2026-05-07 — [Stage 4 v3] Power simulation 재실행 결과 (minor 보정)
- **사전등록 v2**: 25 clusters @ 81.8% power (`stage4_power_simulation.py` v1) — Stage 3 cutoff 2023 의 10 artist effect 분포 기반
- **실제 (v3)**: 40 clusters @ 44.9% power (`stage4_power_simulation_v2.py`) — Artsy 전체 풀 train ≤2023 / test 2025 split 기반
- **이유**: v1 의 10 artists 분포 = outlier (youngnam-cho -196%p) 영향으로 mean/power 부풀려짐. v2 = 모집단 풀 사용으로 더 현실적.
- **분류**: **minor** (사전등록 합격 기준 변경 없음 — primary CI 상한 ≤ 0 그대로 유지)
- **영향**: 
  - Plan §4.4.1 갱신 (power 표 v2 결과로)
  - 해석 초점 변경: "0.8 power 보장" → "Power 자체보다 effect stability 우선" (코덱스 권고)
  - Stage 4 합격 기준 (CI 상한 ≤ 0) 통과는 매우 어려울 수 있음 명시
- **승인**: 코덱스 자문 (해석 초점 변경 권고)

### 2026-05-07 — [Stage 4 v3 실행 결과] BORDERLINE 보류 — 일반 warm 경로 `not advanced` (none)
- **사전등록 §6.1**: Primary CI 상한 ≤ 0 + practical Δ ≤ -0.8%p + seed std ≤ 0.5%p + segment harm 0건
- **실측 결과**:
  * Primary Δ -6.22%p (점추정) / -5.74%p (boot mean) — practical ✓
  * 95% CI [-16.01, +5.30] — CI 상한 0 포함 ✗
  * Seed std 0.252 ✓
  * Segment harm 2 violations: 저가 +5.63%p / depth 15-24 +6.76%p ✗
- **분류**: **none (deviation 아님)** — 사전등록 합격 기준 미달 = §6.2 보류 적용 (정상 흐름)
- **운영 영향**: 일반 warm-only 경로 종결 + slice-conditional (depth ≥25 + seen) 만 후보 유지
- **신규 발견 (사전등록 외)**:
  * Composition-shift: 신규 warm Δ +0.25%p / 기존 warm Δ -12.98%p — Artist FE 본질 입증
  * depth 25+ Holm 보정 후 reject (-17.10%p, p=0.009) — slice-conditional 근거
  * 저가 segment 일관 악화 (P2 Combined +3.36 / Stage 4 FE only +5.63%p) — F4 feature space 한계
- **승인**: 코덱스 자문 (BORDERLINE 판정 + slice-conditional 후보 유지 권고)
- **후속 cycle**: Stage 5 (외부 source 보강 + new prereg) — 별도 분리, Phase 2 (Artsy-only) 폐지

### 2026-05-07 — [Stage 4 단기 트랙] Prereg 적용 + 실행 차이 (minor)
- **사전등록**: `docs/stage4_low_price_decomp_prereg_20260507.md` (작업 3 = 저가 error decomp)
- **메타-방법론 가치**: Stage 4 v3 정정 이후 처음으로 **작은 진단 트랙에도 prereg 적용** — 향후 cycle 표준 자산 (코덱스 권고)
- **실행 vs 사전등록 차이 (minor deviation)**:
  * `gallery_cities` proxy 분석 미수행 (다른 5개 컬럼만)
  * Target corr 정량 측정 미수행 (분포 비교만 — top3 + missing rate)
  * Row-level bootstrap 1000 미수행 (시그니처 판정만)
- **분류**: minor — 결론 (Feature 부족 가설 3/3 시그니처 우세) 영향 X
- **운영 영향**: 없음 (본 트랙 비목표 = 재학습 / 모델 변경 X)
- **승인**: 코덱스 자문 (단기 트랙 종결 검수)
- **표준화 권고**: 향후 진단 트랙은 prereg 메모 (1페이지) 의무 + deviation log 동시 기록

### 2026-05-07 — [Stage 6B] Partial pooling prereg freeze (HARK 회피용 registered follow-up)
- **Disclosure (코덱스 의무)**: 6B 가설 = 6A 결과 (FAIL) 관찰 후 형성. 새 탐색 X — Stage 3 ME 재사용 + low/high fixed effect 만 추가. Sample fragmentation 가설 검증용 mechanism-targeted follow-up.
- **명시 배제**: 추가 segmentation / router / external feature / artist-segment interaction
- **Primary threshold**: 6A 동일 유지 (Δ ≤ -1.0%p, low-price harm 0 hard gate) — 완화 X
- **Secondary Holm m=5**: low / mid-high / sparse-warm / **ICC > 0** (mechanism) / existing-vs-new warm
- **Implementation fallback**: statsmodels MixedLM 수렴 실패 시 optimizer 변경 → re_formula 단순화 → R lme4
- **분류**: minor (정상 follow-up, HARK control 적용)
- **승인**: 코덱스 사전 자문 + 본 prereg freeze (`docs/stage6b_partial_pooling_prereg_20260507.md`)

### 2026-05-07 — [Stage 6A] Segmented architecture FAIL — Hard gate 저가 harm 위반 (none, 정상 흐름)
- **사전등록 §3.3**: 🔴 Hard gate 저가 harm = 0 violation. 1건이라도 발생 시 즉시 FAIL.
- **실측 (100-seed LAO)**:
  * Overall: baseline 38.05% → segmented 43.28% (+5.23%p 악화)
  * Low: +3.54%p / Mid/high: +6.97%p
  * 83/100 seeds 저가 악화 (hard gate 위반)
  * Cluster bootstrap CI [-0.19, +7.19], P(diff ≥ 0)=0.97 (악화 신뢰도 매우 높음)
  * Router 품질: low recall 0.87 / balanced acc 0.85 / Brier 0.11 (router 자체 OK)
- **결론**: Segmented architecture 폐기. Stage 6A FAIL.
- **분류**: **none (deviation 아님)** — 사전등록 §3.3 정상 적용
- **운영 영향**: Spec §17 routing 로직 추가 X / 운영 모델 (F4+spline+Huber) 유지
- **본질 입증** (코덱스 사전 권고 정확): "Segmenting 만으로 feature shortage 해결 X" — Stage 4 작업 3 (feature decomp) → Stage 5 (acquisition 미개시) → Stage 6A (architecture FAIL) **3 cycle 일관**
- **후속 cycle**: 6B Bayesian / hierarchical 우선 검토 (partial pooling + sparse artist + cold-warm 경계)
- **승인**: 사용자 검토 + 코덱스 사후 자문 (예정)

### 2026-05-07 — [Stage 5A Week 2] Artsy CV REJECT + Stage 5 cycle 종료 (major)
- **Week 1 결과**: Auction 4 source REJECT (cohort mismatch), Artsy CV BORDERLINE (§6.2 보류)
- **Week 2 측정**: Artsy 자동화 fetch 0/10 (Cloudflare 403 차단) + TOS 자동화 금지 위험
- **결론**: 사전등록 §6.3 적용 — **모든 candidate REJECT 사유 = "준법적 자동화 접근 불가" (compliance-feasible automation unavailable)**, Stage 5 cycle 종료
- **분류**: **major** — Stage 5 cycle 자체 종료 결정
- **5C prereg 영향**: F1/F2/F3 family 모두 실현 불가 → **5C prereg = gate 미통과로 미개시 종료 (untested, 반증 X)**
- **분기 B 활성화** (`docs/stage5a_week3_decision_memo_20260507.md`):
  * Stage 5 종결 + Calibration only 운영 적용
  * Spec §4 후처리 후보 (Global additive cold baseline 한정)
  * 새 source / Stage 6 (segmented architecture) = 별도 decision gate
- **승인**: 사용자 검토 + 코덱스 자문 (Week 2 결과 검수 예정)

### 2026-05-07 — [Stage 5A Week 1] Auction-first 가정 폐기 (minor)
- **사전등록 §4.1**: 1순위 source = K-Auction / Seoul Auction (한국 전문, "한국 작가 cover 자연 높음" 가정)
- **실측 (Week 1)**: 모든 auction (Seoul / K / Sotheby's / Christie's) = **시장 확립 작가 (Lee Ufan / 김창열 등) 한정**. Stage 4 cohort (신진/중견) cover ~0%
- **사유**: Auction = secondary market (재판매), Stage 4 = primary market (신진/중견 1차 판매) 본질적 cohort mismatch
- **분류**: minor — 사전등록 §6.2 보류 적용 (정상 흐름)
- **결과**: Auction 4 source 모두 REJECT, Artsy CV 만 BORDERLINE PASS-ready
- **후속 액션**:
  * Week 2: Artsy CV 정량 feasibility 확장
  * 사전등록 외 source 후보 검토 (Galerie 직접 / Artsy 매출 history / Artprice 등)
  * 사전등록 외 source 추가 시 별도 deviation entry
- **5C 영향**: F1 (auction anchor) family 실현 가능성 ✗ — 5B 진행 시 F2/F3 만 가능. Primary Δ ≤ -2.0%p 어려울 수 있음.
- **승인**: 코덱스 자문 (Week 1 결과 검수 예정)

## Phase 2 (재정의 v4, 2026-05-07)

### 2026-05-07 — [Phase 2] v3 (Artsy-only) 폐지 + v4 재정의 (Stage 5 = External Acquisition)
- **v3 정의**: Phase 2 = Artsy-only full confirmatory (cleansed 8,891 / 823)
- **v4 재정의**: Phase 2 = Stage 5 = External Feature Acquisition + Validation (5A acquisition / 5B integration / 5C modeling / 5D deployment)
- **이유**: Stage 4 가 사실상 Artsy 전체 모집단 활용 → 동일 데이터 반복 의미 없음 (코덱스 권고)
- **분류**: major (Phase 2 정의 변경 — 새 cycle 분리)
- **신규 prereg**:
  * `docs/stage5a_acquisition_prereg_20260507.md` (5A-5B feasibility + acquisition, HARK 회피용 사전등록)
  * `docs/stage5c_modeling_prereg_20260507.md` (5C modeling, baseline/metric/Holm/PASS 사전 fix, 5A 결과 보기 전 freeze)
- **HARK control**: 5A-5B prereg ↔ 5C prereg 분리 (코덱스 권고)
- **Stage 4 결과 input**: Feature 부족 가설 3/3 시그니처 입증 → Stage 5 design 의 핵심 근거
