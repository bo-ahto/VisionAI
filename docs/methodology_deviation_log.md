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

### 2026-05-07 — [Stage 6B 결과] Partial pooling FAIL + sparse-warm 측정 불가 (none / minor)
- **사전등록 §3.3**: 🔴 Hard gate Δ_low ≤ 0%p
- **실측 (100-seed LAO)**:
  * Overall: baseline 38.05% → mixed 37.96% (-0.09%p, 사실상 동등)
  * Low: +1.29%p 악화 (hard gate 위반)
  * Mid/high: -1.04%p 개선
  * ICC mechanism: 0.81 (CI [0.77, 0.84]) — partial pooling 작동 ✓
- **결론**: Partial pooling FAIL (사전등록 §3.3 즉시). **Architecture-only remedies under fixed-feature cold-start LAO scope** (6A + 6B) 모두 종료.
- **분류**: **none (정상 흐름)** + **minor (sparse-warm 측정 불가)** + **minor (frozen spec 통일 — 코덱스 P0)**
- **Sparse-warm deviation (사전등록 §2.8.1 #3)**: LAO 평가에서 test artists 정의상 train 에 0 작품 → "sparse-warm (train ≤ 5)" 자체 정의 모순. 100/100 seeds 측정 불가. **사후 인정**: prereg 시점 design 오류, 결과 본 후 변경 X = HARK 회피 정상 흐름. Time-split (warm threshold) 평가에서만 의미.
- **Frozen spec 통일 (코덱스 P0 — minor 정정)**: prereg v2 본문 §1.3 / §2.11 에 잔존하던 `is_low_price fixed effect` / `low/high group fixed effect` 표현 = 6B v2 freeze 시점에 이미 삭제된 spec → 결과 본 후 prereg / deviation log / results report 전부 단일 line 으로 통일 ("v2 frozen spec = Stage 3 ME identical, `is_low_price` fixed effect 제거"). 결과 변경 X / 통계 결정 변경 X.
- **Cycle 일관성 확정 (코덱스 P0 분리)**: **3-cycle empirical** (Stage 4 단기 트랙 작업 3 / Stage 6A / Stage 6B) + **1-cycle acquisition infeasibility** (Stage 5 — 준법적 자동화 불가, empirical 반증 X). 본질 = "fixed-feature cold-start LAO scope 의 architecture-only remedies 가 1차 병목 해결 X"
- **운영 영향 X**: Spec §17 변경 X / 운영 모델 유지 / 분기 B 그대로 진행
- **승인**: 사용자 검토 + 코덱스 사후 자문 (P0/P1/P2 검수 통과)

### 2026-05-07 — [Feature Track A.2 결과] Artist popularity FAIL → A.3 escalation (none, 정상 흐름)
- **사전등록 §3 적용 결과** (100-seed LAO):
  * Overall: baseline 38.03% → A.2 37.82% (-0.21%p, 사실상 동등)
  * Low: +0.05%p ⚠️ Hard gate 위반
  * Mid-high: -0.47%p
  * Newly-warm: -0.81%p
  * Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap A.1 v2 fix): mean -0.39%p, 95% CI [-3.85, +3.03], 99% CI [-5.40, +4.47]
  * Seed-level low violation rate: 45/100 = 45.0% (A.1 의 41/100 보다 4%p 높음)
- **판정**: **FAIL (🔴 Hard gate Δ_low > 0 위반)** — 즉시 FAIL
- **분류**: **none (정상 흐름)** — 사전등록 §3.3 hard gate 적용
- **Step gate B안 적용**: A.2 FAIL → A.3 (geometry — aspect ratio + 2D vs 3D) escalation, A.2 features drop (alternative hypothesis sequence)
- **메커니즘 해석 (코덱스 framing)**: Single-snapshot artist features (followers/for_sale/is_p1) = **cold-start LAO 에서 무력** — Stage 6B partial pooling random intercept 무력화 패턴 반복. Artist-binding signal 은 LAO 평가 구조의 본질적 한계 (artist holdout = 학습된 effect 가 unseen artist 에 적용 X).
- **A.1 vs A.2 대조**: A.1 cross-artist signal (작품 분류 + 갤러리) = 약한 개선 / A.2 artist-binding signal (popularity) = 무력 → "Cold-start LAO 에서 유효한 features 는 cross-artist applicable" 가설 입증
- **운영 영향 X**: 운영 spec §1-§16 변경 X / 분기 B calibration only 그대로 유지
- **승인**: 사용자 검토 + 코덱스 사후 자문 (예정)

### 2026-05-07 — [Feature Track A.2 prereg freeze] Artist popularity 4종 (none + minor)
- **사전등록 시점 정합성 평가 (코덱스 design draft P1 권고 적용)**:
  * artist_followers / artist_for_sale / artist_is_p1: artist 당 unique 1.00 = single snapshot (운영 F4 의 artist_total_works 와 동등 spec)
  * year_made: 작품 본질 attribute, 시점 정합성 명확 OK
- **Honesty caveat 명시**: historical reconstruction 불가 (Artsy historical API 부재 / Stage 5 acquisition 종료) → deployment-time consistency 가정 의존. 운영 F4 가 이미 동등 spec (artist_total_works) 사용 중 = 자기모순 X
- **A.1 v2 lessons 사전 반영**:
  1. Cluster bootstrap 진짜 구현 (artist 별 indices 사전 매핑 + with replicas)
  2. α=0.01 = 99% CI 상한 ≤ 0 decision rule (95% CI 참고만)
  3. Per-step freeze 6항목 spec 그대로
- **분류**: **none (정상 흐름)** — Step gate B안 escalation
- **승인**: 사용자 (2026-05-07) — A.1 BORDERLINE → A.2 진입 결정, 시점 정합성 평가 후 caveat 인정 진입

### 2026-05-07 — [Feature Track A.1 v2] 코덱스 결과 검수 P0×2 fix (minor / 사후 정정)
- **코덱스 결과 검수 1차 (2026-05-07)**: HOLD — A.2 진입 보류 권고
- **P0 #1 (Implementation bug)**: cluster_bootstrap_diff 의 `np.isin()` 가 `replace=True` 중복 draw 를 collapse → 진짜 cluster bootstrap 가중치 미반영. 본 fix = artist 별 indices 사전 매핑 + sample 별 concatenate (with replicas). Stage 6B 코드도 동일 bug 보유 (recurring pattern, 향후 cycle 에서 동일 fix 적용 의무). **fix 후 95% CI [-9.41, +1.94] (이전 [-8.31, +1.04] 대비 wider)** — bootstrap 가중치 정합 반영. 결과 본 후 fix 이지만 **결과 변경 X** (BORDERLINE → BORDERLINE 유지, 95% / 99% 둘 다 미달).
- **P0 #2 (Spec operationalization 미흡)**: prereg §2.10 declared α=0.01 (Bonferroni 5 step) 그러나 PASS 조건 §2.7 = "95% CI 상한 ≤ 0" 만 명시 → operationalization 부재. **사후 정정**: §2.7 = **99% CI 상한 ≤ 0 (α=0.01 decision rule)** 추가. 사후 정정 risk 인정 — 결과 본 후 spec 보강 = HARK 잠재 risk / 본 cycle 은 95% / 99% 둘 다 미달 → BORDERLINE 결정 영향 X / 향후 step 에서는 prereg 시점부터 99% CI 명시 의무.
- **P1 fix (보고서 톤 다운)**:
  * "Stage 4 시그니처 부분 반박" → "기존 운영 입력 부족 가설 유지 + cheap metadata 확장 일부 완화 가능성"
  * "gallery_name 핵심 기여" → "likely driver 추정" (effect attribution 미수행)
  * "저가 harm 해결" → "평균상 비악화 + 분포상 불안정"
  * Single seed CI vs 100-seed mean discrepancy 문서 첫머리 명시
- **분류**: **minor (사후 정정 — 결과 변경 X)** + **minor (implementation bug — 결과 변경 X)**
- **Framing 정정 (코덱스)**: "promising but not decision-grade" — 운영 변경 없이 A.2 escalation
- **승인**: 코덱스 결과 검수 v1 → fix 적용 후 결과 보고서 v2 commit

### 2026-05-07 — [Feature Track A.1 결과] Cheap categorical BORDERLINE → A.2 escalation (none, 정상 흐름)
- **사전등록 §3 적용 결과** (100-seed LAO):
  * Overall: baseline 38.03% → A.1 36.70% (-1.34%p) ✓ practical
  * Low: -0.98%p ✓ hard gate
  * Mid-high: -1.67%p ✓
  * Newly-warm: -4.06%p (큰 개선)
  * Cluster bootstrap (rep seed=0, n=2000): mean -3.54%p, 95% CI [-8.31, +1.04] — **CI 상한 +1.04%p 0 걸침**
  * Seed-level low violation rate: 41/100 = 41.0% (6B 의 66/100 대비 25%p 감소)
- **판정**: **BORDERLINE (Primary CI 만 미달)** — Hard gate ✓ + practical Δ ✓ but CI 상한 > 0
- **분류**: **none (정상 흐름)** — 사전등록 §3.2 BORDERLINE 정상 적용
- **Step gate B안 적용**: A.1 BORDERLINE → A.2 (artist popularity 4종, 시점 정합성 검증 후) escalation, A.1 features drop (alternative hypothesis sequence)
- **사전 evidence vs 결과**: 사전 expectation (A.1 PASS 가능성 낮음 / A.4-A.5 escalation 사실상 유력) 의 **부분 반박** — cheap categorical 만으로 저가 식별력 일부 보강 가능
- **6B 와 정반대 패턴**: 6B = aggregate parity but low-slice harm / A.1 = aggregate 개선 + low-slice 비악화 + newly-warm 큰 개선
- **운영 영향 X**: 운영 spec §1-§16 cold rollout 변경 X / 분기 B calibration only 그대로 유지
- **승인**: 사용자 검토 + 코덱스 사후 자문 (예정)

### 2026-05-07 — [Feature Track A.1 prereg freeze] Cheap categorical 4종, 의사결정 8건 추천대로 승인 (none + minor)
- **의사결정 8건 모두 추천대로 승인** (사용자 2026-05-07):
  1. Axis A 우선 / B 조건부
  2. Cheap falsification ladder framing
  3. Step gate B안 (escalation 허용)
  4. LAO primary family vs warm/time-split supportive family 분리
  5. Phase A 7항목 확장 (labelability / joinability / as-of-time)
  6. A.2 시점 정합성 검증 원칙
  7. A.4 / A.5 escalation 진입 (B안)
  8. Cold Phase A shadow 정의 (data availability 검증 shadow)
- **A.1 features 4종 final** (design draft 5종 → 4종, **minor deviation**):
  * 제거: `medium_type` (`category` 와 분류 체계 거의 동일 — top 6 = Painting / Sculpture / Photography 등 동일, 0.4% 결측 더 많음)
  * 사유: redundancy + parsimonious spec
  * **사전 prereg freeze 전 결정** (결과 본 후 변경 X = HARK 회피 정상 흐름)
- **Per-step freeze 6항목** 명시 (코덱스 P1):
  (a) feature set 4종 / (b) encoding (one-hot + leakage-safe target encoding 5-fold OOF + multi-hot top-5 city) / (c) preprocessing (missing → 0 city dummy) / (d) interaction NONE (additive only) / (e) stop-go rule (LAO primary family) / (f) 다음 step alternative hypothesis (A.2 escalation, A.1 features drop)
- **Multiple comparisons**: 5 step gatekeeping sequence → A.1 step α=0.01 (Bonferroni 5 step, FWER ≤ 0.05). LAO secondary Holm m=3 (low / mid-high / newly-warm — sparse-warm 제외, 6B deviation 교훈)
- **분류**: **none (정상 흐름)** + **minor (medium_type 제거)**
- **승인**: 사용자 (2026-05-07) + 코덱스 사후 검수 권고

### 2026-05-07 — [의사결정] Architecture-only close 확정 + Feature track 시작 (none, 정상 흐름)
- **확정**:
  1. Stage 6B FAIL 승인
  2. Architecture-only remedies under fixed-feature cold-start LAO scope **종료**
  3. 운영 모델 = baseline (F4 + spline + Huber) + calibration only (분기 B) **유지**
  4. **Feature track 설계 시작** (`docs/feature_track_design_20260507.md`) — Axis A (internal feature engineering, compliance 무관, 즉시) 우선 / Axis B (external acquisition, Phase A pre-screen 후 조건부)
  5. 6C 보류 — 새 식별 가설 발견 시에만 reopen
- **분류**: **none (정상 흐름)** — methodology pipeline §3 Phase 2'' (feature/information cycle) 진입
- **운영 영향**: 없음 (운영 spec 변경 X)
- **승인**: 사용자 (2026-05-07) + 코덱스 사후 자문 권고

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
