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

## Phase 2 (Full Confirmatory)

(Phase 2 진입 후 deviation 기록)
