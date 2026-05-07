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

## Phase 2 (폐지, 2026-05-07)

> Phase 2 (Artsy-only full confirmatory) 는 Stage 4 가 사실상 Artsy 전체 모집단 활용 → 동일 데이터 반복 분석 의미 없음. 코덱스 권고로 **폐지**.
> 새 Phase 2 = Stage 5 (외부 source 보강 + OOD/drift/sensitivity confirmatory) 로 재정의 예정.
