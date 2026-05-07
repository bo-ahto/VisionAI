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

### 2026-05-07 — [Track 1 Phase 0 + Stage 1 feature integrity audit] 사전등록 method 도입 진입 (none + critical finding)
- **사용자 명시**: 트랙 1 비선형 모델 사전등록 method 도입 + 피처 수 조정 재검수
- **코덱스 사전 자문**: 조건부 GO + Phase 0 freeze 우선 (feature selection 자체보다 평가 protocol freeze 가 1순위) + 4 P0 (baseline ambiguity / evaluation redesign / cold-warm gate 분리 / feature integrity recheck)
- **Phase 0 freeze 적용**:
  * Baseline 확정: **`v3_filtered_tuned` 32 features** (현재 서빙, 트랙 2 와 별개) — 사용자 inventory 의 historical v3 37f ambiguity 해소
  * 8항목 freeze (baseline / dataset / feature dictionary / primary metric / hard gates / stop rule / family cap / locked holdout 봉인 / decision-binding 분리)
  * 트랙 2 → 트랙 1 governance 이식 (locked holdout / family prereg / stage-wise retain / cluster bootstrap / decision-binding 분리) + threshold 재설계 (α=0.01 99% CI = confirmatory holdout 만 / 운영 hard gate 추가: low + source slice + warm non-regression)
- **Stage 1 (feature integrity audit) 핵심 finding (critical)**:
  * 32 features 중 **9 features (28%) 학습-서빙 drift severe**
  * 카테고리 A (7): is_unique / is_edition / has_depth / gallery_city_count / has_seoul / has_international / attribution_class — 서빙 시 hardcoded constant
  * 카테고리 B (2): ho_price_level / medium_price_level — 서빙 시 placeholder 0.0
  * 카테고리 C (이미 fix): work_age / career_age / vintage_premium / freshness_discount / gallery_name (Codex 4차 / 14차 P1 fix 이력)
  * Stage 1 결과 = exploratory diagnostic only / 운영 spec 변경 단독 trigger X
- **사용자 결정 영역**:
  * Option A: Drift fix 우선 + baseline 재산출 (코덱스 권고)
  * Option B: 평행 진행 (Stage 1B importance + stability)
  * Option C: 분리 cycle (drift fix = 별도 prereg)
- **분류**: **none (정상 흐름)** + **critical finding** (잔존 drift 위험 9 features, 별도 fix cycle 필요)
- **운영 영향 X (현 시점)**: 운영 spec §1-§16 변경 X / v3_filtered_tuned 운영 그대로 유지 / 본 finding 의 fix = 별도 confirmatory cycle 후 production gate
- **승인**: 사용자 검토 + 코덱스 사후 검수 (예정)

### 2026-05-07 — [Progressive sampling cycle 종결 + sub-report HTML] A 결정 / Axis B 우선 (none, 정상 흐름)
- **사용자 결정**: A 옵션 (본 cycle 종결) + Axis B license-first 우선 진행 + Progressive Sampling test sub-HTML 외부 보고용 별도 정리
- **본 cycle 종결 사유 (코덱스 사후 검수 종합)**: Stage 1 family-level retain 0건 / advancement evidence X / Stage 1 noise std 9.41% = decision-grade 승급 근거 부적합 / pruning 근거는 충분
- **Phase 0 holdout 봉인 유지**: cancel X — `data/curated/progressive_sampling_locked_holdout_v1.parquet` (SHA-16 1933a0947a918fc9) governance-preserving stop / future preregistered cycle 또는 Axis B 결과 후 재사용 가능
- **Sub-report HTML** (`docs/progressive_sampling_subreport_20260507.html`): 코덱스 사전 자문 (8 sections + measured tone) 적용. 외부 보고용 (1-2 page executive). FAIL framing 회피 / "exploratory cycle concluded under stopping logic" / Axis B 우선 동일 decision logic 으로 framing
- **분류**: **none (정상 흐름)** — Phase 0 freeze 의 stop logic 정상 적용
- **운영 영향 X**: 운영 spec §1-§16 변경 X / 분기 B calibration only 유지
- **다음 단계**: Axis B license-first lane 우선 (handoff packet `docs/axis_b_handoff_packet_20260507.md` 그대로 활용 — Artprice + Kukje + Pace + PKM + Arko inquiry 즉시 outreach)
- **승인**: 사용자 (2026-05-07)

### 2026-05-07 — [Progressive sampling Checkpoint 1 v2] 코덱스 사후 검수 P1×4 + P2×3 적용 → Stage 2 HOLD / 종결 권고 (minor)
- **코덱스 사후 검수 (Stage 2 진입): HOLD** — operational decision = 종결
- **P1 fix**:
  1. Literal stop-rule (모든 family near-null + Low non-harm 미달) = 비트리거 / Operational reading (family-level retain 0건) = 종결
  2. Sub-signal (artist_popularity Low -3.33%p) = artifact prior 더 높음 / transferability 근거 X
  3. HARK risk: Stage 2 진입 reasoning = "all-family triage" → "Family D rescue" 변경 = reasoning drift (Family D = 원래 negative control prereg)
  4. Stage 1 noise (std 9.41%) = decision-grade evidence X — 승급 근거 부적합 / 종결 근거는 충분
- **P2 caveat 추가**:
  1. SKIP variants 존재 (geom_depth_spline / cat_attribution_x_3d / miss_depth) — "모든 preregistered variant 공정 평가" X / "평가 가능한 variant 들에서 advancement evidence 없음" 이 정확
  2. Family D = 원래 negative control prereg / re-test only
  3. A.2 FAIL (full-like) vs Stage 1 median_proxy 완전 동일 가설 X (bundle vs subset 차이)
- **사용자 보고 framing (코덱스)**: "decision-grade 승급 근거 X / family-level retain 0건 + Stage 1 noise → operational decision HOLD/종결 / sub-signal 은 별도 exploratory low-slice 가설로만 보존"
- **분류**: **minor (framing 톤 다운, 결과 변경 X)**
- **운영 영향 X**: 운영 spec §1-§16 변경 X / 분기 B calibration only 유지

### 2026-05-07 — [Progressive sampling Phase 0 + Stage 1 Checkpoint 1] HARK-safe variant 진입 (none + minor)
- **사용자 명시**: A 옵션 (progressive sampling) 메인 진입 + 체크포인트 + 코덱스 활용
- **코덱스 사전 자문**: 조건부 GO — 3 조건 (Stage 3 transfer filter / holdout decision-binding / family cap·tie·stop rule)
- **Phase 0 mini-prereg freeze** (`docs/progressive_sampling_phase0_freeze_20260507.md`): 6항목 (Primary KPI / Locked holdout split / 가설 family roster / Stage 별 pruning / 불변 pipeline / Decision-binding 분리)
- **Locked holdout 봉인 완료**: 161 artists / 1,680 rows / SHA-16 hash `1933a0947a918fc9` / random_state=42 / stratify (depth × price × low_share) / Phase 4 final 1회만 access
- **Stage 1 (stage1_200x20) 결과**:
  * 5 family × 18 variants 평가 — 모든 variant retain 미달 (Overall Δ ≤ -0.3%p AND Low Δ ≤ +0.2%p)
  * Sub-signal (decision-grade X — exploratory only): artist_popularity Low -3.33%p but Overall +0.68%p / artist_median_proxy Low -1.59%p but Overall +1.61%p — small sample noise / segment heterogeneity 가능
  * 18 variants 중 17 Overall positive (small sample overfitting 일반 패턴)
- **Checkpoint 1 결과**: 코덱스 stop rule trigger 가능성 (Stage 1 모든 family near-null + low non-harm 미달) — 단 Stage 1 200x20 sample noise (std 9.41%) caveat 적용 시 Stage 2 진입 가능
- **분류**: **none (정상 흐름)** — Phase 0 freeze 적용 + 정상 cycle 진행 / **minor** (Stage 1 schema 차이로 일부 variant SKIP — depth_cm 부재)
- **운영 영향 X**: 운영 spec §1-§16 변경 X / 분기 B calibration only 유지
- **사용자 의사결정 영역**: A 본 cycle 종결 / B Stage 2 진입 / C HARK 위반 / D 코덱스 사후 검수 후 결정

### 2026-05-07 — [Sample size sensitivity descriptive analysis] 운영 baseline stability 관찰 (none, 정상 흐름)
- **사용자 요청**: data/curated 의 200/500/1000 데이터 기준 모델 검증
- **코덱스 사전 자문**: 조건부 GO — "baseline 검증" → "sample size + composition sensitivity descriptive analysis" framing 정정 / mini-freeze 6항목 (목적 / 데이터 / 모델 / split / metric / 해석 rule)
- **결과 (운영 baseline F4 + spline + Huber, 100-seed LAO)**:
  * stage1_200x20: Overall 25.95% / std 9.41% (가장 unstable, floor)
  * stage2_500x50: Overall 27.21% / std 6.30%
  * stage3_1000x100: Overall 24.30% / std 4.30% (가장 stable curated)
  * stage4_full: Overall 38.03% / std 4.23% (운영 baseline)
- **핵심 finding**: curated cohort (1/2/3) 24-27% vs full 38% gap = **sample size 가 아닌 composition 효과** (작가당 작품 수 uniform vs heavy variance, cold artist 비율 차이) — 코덱스 P0 framing 정확
- **Stability**: sample size 증가 시 std 개선 (200x20 9.41% → full 4.23%), 1000x100 ≈ full 포화
- **Newly-warm**: stage4_full only (46.11% mean) — Stage 1/2/3 = curated cohort, Stage 3 cohort 기준 정의 부적합 → N/A 처리
- **분류**: **none (정상 흐름)** — descriptive sensitivity, decision-binding X
- **운영 영향 X**: 본 분석 단독 spec 변경 trigger 금지 (코덱스 P0) / 운영 spec §1-§16 변경 X / 분기 B calibration only 유지

### 2026-05-07 — [Axis B Round 3 v2] 코덱스 사후 검수 P1×5 + P2×1 framing 톤 다운 (minor)
- **코덱스 사후 검수**: Round 3 continue / 운영팀 outreach GO (단 범위 한정 = Artprice + Kukje/Pace/PKM + Arko inquiry / Sotheby's·Christie's·Hyundai HOLD = Round 4 pool)
- **P1 fix**:
  1. Artprice "paid license 확인" → "paid subscription/API hint strong (운영 확인 전 단정 X)"
  2. Decision Table 의 즉시 outreach 범위 vs Round 4 pool 충돌 fix — Sotheby's/Christie's = Round 4 pool 분리 명시 (HARK 회피)
  3. Arko inquiry draft 8항목 → 12항목 보완 (정확 endpoint URL / schema sample / sample file or API response / auth 방식 추가)
  4. Lane 1 method-gate 미검증 caveat (Round 2 freeze 3축 cover ≥70 / join ≥80 / time-safe 평가 미수행) A continue GO 옆에 명시
  5. A continue GO = "decision-grade GO" 톤 → "협상 착수 GO, source adequacy 판정 미정"
- **P2 fix**: MCST endpoint = "google search 외부 검색" → "운영팀 직접 inquiry 또는 외부 검색 담당 배정" (LLM/운영팀 역할 경계 명확화)
- **분류**: **minor (framing 톤 다운, 결과 변경 X)**

### 2026-05-07 — [Axis B Round 3] A pre-assessment + Arko ops + MCST side-queue (3 lane, none + minor)
- **사용자 명시 instruction**: 우선순위에 맞춰 진행 + 코덱스 활용
- **코덱스 사전 자문**: 조건부 GO + 3 lane 분리 (Lane 1 A 본선 / Lane 2 Arko ops / Lane 3 MCST side-queue) + reporting 5 구조
- **Lane 1 (A 본선) 결과**:
  * Top 3 paid vendor: Artprice (subscription/API hint strong, 1순위) / Sotheby's (455KB main, 2순위) / Christie's (152KB, 3순위) / Artnet (1KB only, 보류)
  * Top 5 한국 갤러리 access OK 3개: Kukje / Pace / PKM (자동화 access 가능) / Hyundai 0KB dynamic / Hakgojae connection refused / Gana SSL 에러
  * 갤러리 가격 공개 hint = 0 (코덱스 사전 자문 — gallery direct = "데이터 richness 보다 협상 가능성 screening" 입증)
- **Lane 2 (Arko ops) 결과**:
  * Arko retry 2차: main `/` = 200 ✓ (이전 sub-path 만 5xx, main 정상) → **partial PASS — access recovery only** (sub-path / dataset endpoint 미확인)
  * Round 2 freeze §3.3 spec 3회 중 2회 완료 (Round 2B 1차 + 본 round 2차) / 추가 1회 = 다음 cycle
  * Arko 운영팀 inquiry draft 8항목 작성 (목적 / 데이터 범위 / access / historical / cadence / license / AI 사용 / 회신 요청)
- **Lane 3 (MCST side-queue) 결과**:
  * sub-path 4종 (sitemap / search / 통계 / policy main) 모두 404 → endpoint discovery 실패 → 운영팀 inquiry / 외부 search engine 영역
- **Decision Table 핵심**: A continue GO (Artprice + Kukje/Pace/PKM 운영팀 협상 시작 충분) / Arko ops + MCST side-queue 분리
- **HARK 회피 (코덱스 P0)**: 새 source (Sotheby's / Christie's / Hyundai 추가 평가) = Round 3 본선 편입 X → **Round 4 candidate pool 분리** (deviation log entry)
- **Phase A 종합 = HOLD 그대로 유지** — 운영팀/법무팀 1차 회신 후 종결 (코덱스 — Round 3 직후 X)
- **분류**: **none (정상 흐름)** + **minor (Round 4 candidate pool 분리 — 새 source HARK 회피 정상 처리)**
- **운영 영향 X**: 운영 spec §1-§16 변경 X / 분기 B calibration only 유지

### 2026-05-07 — [Axis B Round 2B] E (MCST/Arko 재시도) + B (aggregate context) 동시 진행 (none, 정상 흐름)
- **사용자 명시 instruction**: E + B 동시 진행 (Round 2 v2 우선순위 A>E>B>C>D 의 E + B)
- **E: MCST 재시도 결과**: main page 200 (이전 정책 list URL = path deprecation, main 자체는 정상) → **partial PASS** (전반 자동화 access OK, art market endpoint 추가 발견 필요 — 운영팀 inquiry 영역)
- **E: Arko 재시도 결과**: alternative URL 모두 4xx/5xx persistent (server side issue) → **unresolved 그대로** (Round 2 의 HOLD 유지). 24-72h 추가 retry 또는 운영팀 inquiry (담당 부서 contact) 필요
- **B: KOSIS aggregate**: 미술시장 검색 hit 4 만 — 정부 공식 art market 통계 source 약함
- **B: KAMS aggregate**: 자료실 empty / artmarket sub-domain 500 / login 필요 추정 → 데이터 직접 access 어려움
- **종합 판정**: Phase A 종합 = HOLD 유지 (Round 2 v2 그대로). 코덱스 사전 자문 base hypothesis (Option B ROI 낮음 — label scarcity 미해결) **재확인**
- **우선순위 update (post-Round-2B, 코덱스 P1 톤 정정 v2)**: A (license-first) 1순위 변동 X / B (Round 2B) **3순위 격하** (실무 우선순위 하락 — A를 막을 정도의 ROI 아님 / B 구조적 ROI 입증 X / 탐색 깊이 부족) / E (MCST partial PASS = access recovery only, transport resolved but endpoint unconfirmed / Arko unresolved HOLD — freeze §3.3 24-72h × 3회 spec 미충족, 1차 retry 만 기록)
- **분류**: **none (정상 흐름)** — Round 2B 결과 freeze rule 그대로 적용
- **운영 영향 X**: Phase A HOLD 그대로 / 운영 spec §1-§16 변경 X / 분기 B 유지

### 2026-05-07 — [Axis B Round 2 v2] 코덱스 사후 검수 P0×2 + P1×4 + P2×2 fix (minor, 사후 정정)
- **코덱스 사후 검수**: 운영팀/법무팀 인계 GO (단 framing 정정 후). 다음 우선순위 = A > E > B > C > D
- **P0 fix**: framing 톤 정정 — "5/5 모두 aggregate / 5/5 가격 X / 입증" → "0 confirmed joinable, 2 unresolved (MCST/Arko transport error = evidence gap), 3 confirmed aggregate-level"
- **P1 fix**:
  1. Method 적용 부분 문서화 — cover numerator/denominator + publication date 기록 권고 일부만 적용 명시 (Round 2B / 운영팀 inquiry 시 보완)
  2. **Transport/Server Error Retry Protocol** Round 2 freeze §3.3 사후 추가 — HTTP 4xx/5xx 시 24-72시간 간격 3회 재시도 + alternative URL / 모두 실패 시 FAIL 전환 / minor deviation 명시 (source-level 판정 변경 X)
  3. Handoff packet narrowing 결과 (Round 2 결과 문서) 참조 추가 + 우선순위 update (KOSIS 우선 → A license-first 실질 1순위)
  4. License-first lane 의 새 risk caveat — coverage bias + cost risk
- **P2 fix**: Option B (aggregate context signal) ROI = 2순위 이하 (label scarcity 미해결) / Handoff packet 우선순위 pre-Round-2 → post-Round-2 update
- **분류**: **minor (사후 정정 — framing 톤 다운 / 결과 변경 X / source-level 판정 변경 X)**

### 2026-05-07 — [Axis B Phase A Round 2] LLM cycle (Data avail + Joinability + As-of-time) → Phase A HOLD (none, 정상 흐름)
- **위치**: Axis B Phase A pre-screen project — Round 2 (사용자 결정 = C 동시 진행)
- **사전등록 freeze (코덱스 P0)**: 4 freeze (대상 source 5개 / 평가축 3축 / threshold 70-80-time-safe / 판정 rule)
- **LLM cycle 결과 (5/5 source)**:
  * KOSIS (orgId=113 한국문화관광연구원 art market): aggregate-level 통계 (annual 거래액/평균가) → MODEL INPUT FAIL / CONTEXT SIGNAL PASS
  * KAMS: 미술시장 실태조사 / 아트코리아랩 보고서 → aggregate-level → MODEL INPUT FAIL / CONTEXT SIGNAL PASS
  * MMCA: 작품-level catalog (작가명/작품명/제작연도/소장품) but 가격 X (museum collection 특성) → partial metadata PASS / MODEL INPUT FAIL (가격 X)
  * MCST: URL 404, 추가 확인 필요 → HOLD
  * Arko: HTTP 500 server 에러, 재평가 필요 → HOLD
- **Phase A 종합 판정**: **HOLD** (joinable source 0 개 — 작품-level + 가격 보유 source = 0)
- **코덱스 base hypothesis 정확 입증**: "정부/공공 5개 = aggregate/statistical source 가능성 높음, joinability FAIL 다수" — 본 결과로 입증
- **다음 단계 (사용자 결정 영역)**:
  * A. License-first lane (갤러리 직접 / paid vendor) — 운영팀/법무팀 영역
  * B. Aggregate context signal 활용 (Round 2B LLM cycle)
  * C. Program-level redesign
  * D. Default 유지
  * E. Round 2B 추가 평가 (MCST + Arko 재확인 / KIAF / 한국화랑협회 side-queue)
- **운영팀/법무팀 cycle 동시 진행**: handoff packet (`docs/axis_b_handoff_packet_20260507.md`) 인계 가능 — 법무/TOS 검토 + 운영 inquiry 즉시 병렬 시작 가능
- **분류**: **none (정상 흐름)** — Round 2 freeze rule 그대로 적용
- **운영 영향 X**: Phase A HOLD → 운영 spec §1-§16 변경 X / 분기 B calibration only 그대로
- **승인**: 사용자 검토 + 코덱스 사후 검수 (예정)

### 2026-05-07 — [Axis B Phase A Round 2 freeze + handoff packet] Scorecard + 운영팀/법무팀 인계 packet 작성 (none, 정상 흐름)
- **코덱스 사전 자문 (2026-05-07)**: 조건부 GO — Round 2 시작 전 4 freeze 필수 (HARK 회피)
- **freeze 4항목**:
  1. 대상 source 5 (KOSIS/MCST/KAMS/MMCA/Arko) — KIAF/한국화랑협회 = side-queue 분리 / Frieze REJECT 유지 / 새 source = Round 2B 분리
  2. 평가축 3 (Data availability / Labelability·Joinability / As-of-time reproducibility)
  3. Threshold (cover ≥ 70% / join ≥ 80% / time-safe yes-no)
  4. 판정 rule (3축 중 1 fail = source FAIL / aggregate-only = 이원화 / 2 이상 PASS + 1 이상 joinable = 조건부 PASS)
- **Handoff packet** (`docs/axis_b_handoff_packet_20260507.md`): 코덱스 권고 7-document 통합 — Exec summary + Round 1 + scorecard freeze + 법무/TOS 의뢰서 (7항목) + 운영 inquiry sheet (8항목) + license fallback memo + cover memo
- **분류**: **none (정상 흐름)** — Round 2 사전 design + handoff packet 작성

### 2026-05-07 — [Axis B Phase A pre-screen Round 1] Source discovery + Access 1차 실측 (none, 정상 흐름)
- **위치**: 새 Phase 2'' Axis B (External Acquisition) Phase A pre-screen project — Round 1
- **본 round 의 범위**: LLM 가능 영역만 (Access / Anti-bot / robots.txt) — Legal / TOS / License = 운영팀/법무팀 영역
- **후보 10개 source 평가**:
  * **PASS likely 5개 (정부/공공)**: KOSIS / MCST / KAMS / Arko / MMCA — robots.txt 자동화 친화적, Allow: / 명시 또는 부분 disallow only
  * **부분 PASS 2개**: KIAF (Allow : / 전체 허용) + 한국화랑협회 (wp-admin 만 disallow) — TOS 추가 검토 필요
  * **REJECT 1개**: **Frieze Seoul** = `Content-Signal: ai-train=no` 명시 + EU Article 4 권리 보유 + AI scraper (Amazonbot/Bytespider/CCBot) 전체 Disallow → AI/ML 사용 명시 금지
  * **추가 확인 필요 2개**: Korea Foundation (SSL 에러) / KOSARC (DNS FAIL — 도메인 확인 필요)
- **Stage 5 패턴 반복 (1건)**: Frieze REJECT = Stage 5 Artsy CV (Cloudflare 403 + TOS automation prohibition) 와 동일 패턴 → "private art market site 는 AI 사용 명시 금지 가능성 높음" plausible 가설 (Stage 5 + Frieze 2 사례)
- **다음 round 진입 후보**: 정부/공공 5개 source — Round 2 = (LLM) Data availability + Labelability 평가 / (운영팀/법무팀) Legal / TOS 검토 + License 협상
- **분류**: **none (정상 흐름)** — Phase A pre-screen project Round 1 정상 진행
- **운영 영향 X**: 운영 spec 변경 X / 분기 B calibration only 그대로
- **승인**: 사용자 검토 + 다음 round 옵션 결정 (A/B/C/D)

### 2026-05-07 — [Feature Track A.5 결과 + Axis A 5 step 종결] Image embedding FAIL near-null (none, 정상 흐름)
- **사전등록 §3 적용 결과** (100-seed LAO):
  * Overall: baseline 38.03% → A.5 38.25% (Δ +0.22%p, 사실상 동등 또는 미세 악화)
  * Low: Δ -0.06%p ✓ Hard gate (very close to 0)
  * Mid-high: Δ +0.43%p / Newly-warm: Δ +0.14%p
  * Cluster bootstrap (rep seed=0): mean -1.01%p, 95% CI [-4.35, +2.29], 99% CI [-5.39, +3.22]
  * Seed-level low violation: 54/100 = 54.0%
- **판정**: FAIL (Δ > -0.3%p, 개선 미달, 마지막 step) — Hard gate 통과 ✓ but practical Δ + CI 모두 미달
- **분류**: **none (정상 흐름)** — Step gate B안 마지막 step
- **Axis A 5 step 종결 확정**:
  * A.1 BORDERLINE (cross-artist artwork 분류+갤러리, 약한 신호)
  * A.2 FAIL (artist-binding popularity, near-null)
  * A.3 BORDERLINE strongest (pure artwork geometry, 3 cols low-dim)
  * A.4 FAIL worst (artwork text PCA K=10)
  * A.5 FAIL near-null (artwork image PCA K=10) — **마지막**
- **종합 결론 (코덱스 framing 톤, working hypothesis 보수적)**: A.3 만 유일 promising signal — geometry-specific 또는 low-dim 효과 가능성. "artwork-level cross-artist signal 일반이 cold-start LAO 유효" 단순 일반화 미지지. Plausible mechanism (단정 X) = cold-start LAO 에서 dim 증가 자체가 risk.
- **코덱스 권고 검증 (A.4 검수)**: A.5 HOLD / Axis A 종료 권고 = 본 A.5 결과로 정확히 입증 (FAIL near-null, image embedding 도 A.4 와 비슷 패턴)
- **운영 영향 X**: A.1-A.5 모두 운영 spec §1-§16 변경 X / 분기 B calibration only 유지 / A.3 단독 shadow = 별도 의사결정 gate (조건부 HOLD)
- **사용자 의사결정 영역**: 옵션 A (A.3 단독 shadow) / B (Axis B external acquisition + Phase A pre-screen) / C (program-level 재설계) / D (default — calibration only 유지)
- **승인**: 사용자 검토 + 코덱스 사후 검수 (예정)

### 2026-05-07 — [Feature Track A.5 prereg freeze] Image embedding (CLIP-ViT-B-32, PCA K=10), 사용자 명시 instruction
- **A.5 진입 의사결정 근거**: 사용자 명시 instruction (코덱스 권고 = HOLD / Axis A 종료) 와 분리. Procedural Axis A 종결 step 으로 진행 (hypothesis 끝까지 시험)
- **A.5 features**: clip-ViT-B-32 (512-dim) + PCA top-K=10
- **시점 정합성 명확 OK**: image_url = 작품 본질 attribute
- **Heaviest escalation**: image fetch (urllib + ThreadPoolExecutor max_workers=20) + cache to data/curated/images_cache/ + CLIP encode batch 64
- **Failed images**: 13 null URLs + fetch failures → zero 512-dim embedding (사전 spec)
- **A.1-A.4 v2 lessons 사전 반영**: cluster bootstrap 진짜 구현 / α=0.01 99% CI / per-step freeze 6항목 / framing 톤 / procedural vs management recommendation 분리
- **분류**: **none (정상 흐름)** — 사용자 명시 instruction
- **승인**: 사용자 (2026-05-07)

### 2026-05-07 — [Feature Track A.4 결과 v2] 코덱스 검수 P1×3 + P2×2 framing 톤 다운 (minor)
- **코덱스 검수 1차 (2026-05-07)**: P0 없음. **A.5 의사결정 권고 = HOLD (Axis A 종료 권고)** — 사용자 명시 instruction 으로 A.5 진행
- **P1 fix**: working hypothesis 단순 일반화 반박 톤 다운 / procedural step vs management recommendation 분리 / "frozen A.4 spec fails" 톤
- **P2 fix**: negative information / dim 증가 risk 단정 → plausible mechanism 톤 / single-seed sign 충돌 = single split 불안정성
- **분류**: **minor (framing 톤 다운, 결과 변경 X)**

### 2026-05-07 — [Feature Track A.4 결과] Title text embedding FAIL → A.5 escalation 의사결정 영역 (none, 정상 흐름)
- **사전등록 §3 적용 결과** (100-seed LAO):
  * Overall: baseline 38.03% → A.4 38.69% (Δ +0.66%p, 악화)
  * Low: Δ +1.22%p ⚠️ Hard gate 위반 → 즉시 FAIL
  * Mid-high: Δ +0.00%p (사실상 동등) / Newly-warm: Δ +0.08%p (사실상 동등)
  * Cluster bootstrap (rep seed=0): mean -0.33%p, 95% CI [-2.04, +1.46], 99% CI [-2.35, +1.85]
  * Seed-level low violation rate: 75/100 = 75.0% (Axis A 최악, A.3 13/100 정반대)
- **판정**: FAIL (🔴 Hard gate Δ_low > 0, decisive) — Step gate B안 → A.5 escalation 또는 의사결정자 결정 영역
- **분류**: **none (정상 흐름)** — 사전등록 §3.3 hard gate 적용
- **메커니즘 (provisional, 코덱스 framing — 입증 X)**: Working hypothesis "artwork-level cross-artist signal 일반이 cold-start LAO 유효" 의 **단순 일반화 반박**. A.3 strongest / A.4 worst → A.3 의 강한 signal 이 geometry 특수 효과 가능성 / 또는 cold-start LAO 평가에서 dim 증가 자체가 noise / overfitting risk (A.4 PCA K=10 vs A.3 3 cols)
- **A.5 진입 의사결정 영역**: A.4 dim sensitivity 가설 적용 시 A.5 (image embedding, heavier dim) 도 유사 FAIL 가능 → 진입 ROI 의문. 사용자 결정 영역 (진입 vs 보류 / Axis A 종료 + A.3 단독 shadow 검토)
- **운영 영향 X**: 운영 spec §1-§16 변경 X / 분기 B 유지 / A.4 features 채택 X / A.3 단독 shadow 검토 가치 변동 X (HOLD 그대로)
- **승인**: 사용자 검토 + 코덱스 사후 검수 (예정)

### 2026-05-07 — [Feature Track A.4 prereg freeze] Title text embedding (multilingual MiniLM, PCA K=10)
- **A.4 features**: paraphrase-multilingual-MiniLM-L12-v2 (384-dim) + PCA top-K=10 (train fold fit, leakage-safe)
- **시점 정합성 명확 OK**: title = 작품 본질 attribute, scrape/sale 시점 무관
- **First heavy escalation**: compute / storage 비용 ↑ (sentence-transformers 5.4.1 / transformers 5.8.0 설치, 384-dim embedding cache ~13MB)
- **A.1-A.3 v2 lessons 사전 반영**: cluster bootstrap 진짜 구현 + α=0.01 99% CI decision + per-step freeze 6항목 + framing 톤 (working hypothesis)
- **분류**: **none (정상 흐름)** — Step gate B안 escalation
- **승인**: 사용자 (2026-05-07) — A.3 BORDERLINE 후 A.4 진입 결정

### 2026-05-07 — [Feature Track A.3 결과 v2] 코덱스 검수 P1×3 + P2×1 framing 톤 다운 (minor)
- **코덱스 검수 1차 (2026-05-07)**: A.4 GO + A.3 단독 shadow HOLD (P0 없음)
- **P1 fix**: "near-PASS" 표현 제거 / "부분 입증" → "부분 일치 (provisionally consistent — escalation rationale 강화)" / shadow 권고 좁힘 (즉시 검토 X, A.4 결과 후 또는 별도 business-driven 트랙으로만)
- **P2 fix**: Geometry 메커니즘 proxy 가능성 caveat 추가 (format/category/material proxy 가능)
- **분류**: **minor (framing 톤 다운, 결과 변경 X)**

### 2026-05-07 — [Feature Track A.3 결과] Geometry BORDERLINE near-PASS → A.4 escalation (none, 정상 흐름)
- **사전등록 §3 적용 결과** (100-seed LAO):
  * Overall: baseline 38.03% → A.3 35.92% (Δ -2.11%p) ✓ practical (Axis A max)
  * Low: Δ -2.65%p ✓ hard gate (큰 개선, A.1 -0.98%p 대비)
  * Mid-high: Δ -1.79%p
  * Newly-warm: Δ -3.15%p
  * Cluster bootstrap (rep seed=0, n=2000, 진짜 cluster bootstrap): mean -4.43%p, **95% CI [-9.54, -0.36]** ✓ / **99% CI [-11.37, +0.41]** ✗ very close miss
  * Seed-level low violation rate: 13/100 = 13.0% (Axis A min — A.1 41/100, A.2 45/100 대비 압도적 robust)
- **판정**: **BORDERLINE (Primary 99% CI 미달, α=0.01 Bonferroni 5 step decision rule)** — 95% CI 만으로는 PASS 가능했으나 사전등록 freeze 정합성 유지 의무
- **분류**: **none (정상 흐름)** — Step gate B안 BORDERLINE → A.4 escalation
- **메커니즘 (working hypothesis 부분 입증, 코덱스 framing — 입증 X)**: A.1 (cross-artist artwork-level: 분류/갤러리) 약한 / A.2 (artist-binding popularity) near-null / A.3 (pure artwork-level geometry) **strongest signal in Axis A** = "cold-start LAO 에서 유효한 신호 = artwork-level cross-artist applicable" 가설 일관 패턴. 단 A.4 (text) / A.5 (image) escalation 에서 재시험 필요.
- **운영 영향 X (본 cycle)**: 운영 spec 변경 X / 분기 B 유지 / A.3 features 채택 X (PASS 기준 미달)
- **추가 검증 가치 (의사결정자 영역)**: A.3 effect size + low harm decisive 통과 = Axis A 최강 / A.4 결과에 따라 (PASS 시 A.4 채택 / FAIL/BORDERLINE 시 A.3 단독 shadow 검토 가치)
- **승인**: 사용자 검토 + 코덱스 사후 검수 (예정)

### 2026-05-07 — [Feature Track A.3 prereg freeze] Geometry 3종 (none, 정상 흐름)
- **A.3 features 3종**: log_aspect_ratio + is_3d + log_depth_3d (2D=71.7% / 3D=28.3%)
- **시점 정합성 명확 OK**: width/height/depth = 작품 본질 attribute, scrape/sale 시점 무관
- **A.1/A.2 v2 lessons 사전 반영**: cluster bootstrap 진짜 구현 + α=0.01 99% CI decision + per-step freeze 6항목 + 운영 spec 인용 정확성 + framing 톤 (working hypothesis)
- **분류**: **none (정상 흐름)** — Step gate B안 escalation
- **승인**: 사용자 (2026-05-07) — A.2 FAIL 후 A.3 진입 결정

### 2026-05-07 — [Feature Track A.2 결과 v2] 코덱스 검수 P1×4 + P2×2 framing 톤 다운 (minor)
- **코덱스 검수 1차 (2026-05-07)**: A.3 GO + FAIL 정당성 OK (P0 없음)
- **P1 fix**: 메커니즘 결론 톤 다운 ("무력" → "near-null net effect under this spec") / artist_total_works inference jump 인정 (운영 F4 재평가 트리거 X) / A.1 vs A.2 = "입증" → "working hypothesis" / 의사결정자 framing
- **P2 fix**: 45/100 vs 41/100 robust difference X (CI [-9.7, +17.7]) / effect attribution 톤
- **분류**: **minor (framing 톤 다운, 결과 변경 X)**

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
