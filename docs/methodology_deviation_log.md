# Methodology Deviation Log

> **목적**: Pre-registered analysis plan 대비 실제 진행 차이 기록
> **연계**: `docs/트랙2_methodology_pipeline_20260507.md` §10 / `docs/stage4_확장검증계획_20260507.md` §6.4
> **작성 규율**: 차이 발생 즉시 기록, major deviation (가설/metric/임계 변경) 시 새 exploratory cycle 분리

> ⚠️ **본 PR scope (Track 1 closeout)**: 본 deviation log 는 **Track 1 entries 만** 포함. Track 2 (Stage 4 v3 / Stage 6 / Feature Track Axis A / Axis B / Sample size sensitivity / Progressive sampling) entries 는 **후속 PR 에서 append** (코덱스 권고 분할 step 3-5).

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

## Track 1 — 운영 메인 모델 사전등록 cycle (2026-05-07)

> 트랙 1 (1차 시장 갤러리 가격 예측 운영 모델) 의 첫 사전등록 method 도입 cycle.
> 시간순 (Phase 0 freeze → Stage 1 audit → Amendment → Audit 4 → Closeout) 으로 ordering.

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
- **승인**: 사용자 검토 + 코덱스 사후 검수 (P0×1 + P1 다수 fix → v3 통과)

### 2026-05-07 — [Track 1 Option A drift fix amendment] 7 drift + 2 dead 재분류 / fix set freeze (none, Phase 0 stop rule 정상)
- **사용자 결정**: Option A 진행 (코덱스 권고대로)
- **코덱스 사전 자문**: 별도 mini-prereg 불필요 / **amendment memo (1 page) 필요** / Phase 0 §1.5 stop rule 정상 적용
- **Audit 1 결과 (코덱스 직접 확인)**: 학습 데이터 28,376 행 actual distribution
  * `is_unique` =1: 28,340 / =0: 36
  * `is_edition` =1: 34
  * `has_depth` =1: **22,839** (학습 81%, 서빙 모두 0 — 매우 severe)
  * `gallery_city_count` =1: 25,953 / =2: 1,633 / =3: 564
  * `has_seoul` =1: **6,414** (학습 23%, 서빙 모두 0 — 매우 severe)
  * `has_international` =1: **23,394** (학습 82%, 서빙 모두 0 — 매우 severe)
  * `attribution_class` 'Unique': 28,340 / 'Limited edition': 34
  * **`ho_price_level` / `medium_price_level`**: 학습 28,376/28,376 = 0.0 → **dead feature** (severe drift X)
- **재분류 (코덱스 P0)**: 9 features → **7 severe drift + 2 dead** (Stage 1 v3 결과 보고서 update 적용)
- **Amendment memo** (`docs/track1_amendment_drift_fix_20260507.md`): fix set freeze
  * 제거 9 features (7 drift + 2 dead): is_unique / is_edition / has_depth / gallery_city_count / has_seoul / has_international / attribution_class / ho_price_level / medium_price_level
  * 유지 23 features (no serving-side red flag found): 위 9개 외 v3_filtered_tuned 32f 의 잔존
  * New variant: `v3_filtered_tuned_drift_fix_v1` (23 features)
  * Models: CatBoost + XGBoost (운영 best_params 그대로)
  * Calibration 재산출 의무 (`source_calibration.json` cell-level)
- **평가 protocol (코덱스 권고)**: GroupKFold cold-start Overall + Artsy / Saatchi split + Warm KFold non-regression
- **분류**: **none (정상 흐름)** — Phase 0 §1.5 stop rule 정상 적용 / baseline contract 변경 사전 명시
- **운영 영향 X (현 시점)**: 본 amendment 단독 ≠ 운영 spec 변경 trigger / Stage 4 holdout + shadow / staged rollout gate 후만 production 반영

### 2026-05-07 — [Track 1 Audit 4 결과 + 종합 HTML 보고서 + Phase 0 closeout (Option A)] FAIL trigger / 본 cycle 종결 (none, Phase 0 §4 정상 trigger)
- **Audit 4 결과** (`scripts/audit4_drift_fix_eval.py`, `model_test_results/audit4_drift_fix_v1_metrics.json`):
  * 32f vs 23f 3-split 정합 비교 (입체 필터 적용 / 운영 best params / GroupKFold 3 + KFold 3 + random_state=42)
  * **Overall Ensemble: 40.20% → 40.90% (+0.70%p 악화)** — Phase 0 primary FAIL
  * Overall CatBoost: 40.20% → 41.30% (+1.10%p)
  * Overall XGBoost: 41.10% → 41.60% (+0.50%p)
  * Artsy Ensemble: 35.40% → 35.30% (-0.10%p, ≈)
  * **Saatchi Ensemble: 42.50% → 44.30% (+1.80%p)** — Hard gate 2 violation (source 비대칭)
  * Warm slice XGBoost: 10.30% → 10.30% (+0.00%p, ≈) — Hard gate 3 OK
- **Stop criteria (Phase 0 §4)**: **fail trigger** (Overall 비개선/악화 + Saatchi 비대칭) — 정상 trigger
- **핵심 finding (코덱스 P1 톤 정정)**: drift features 9개 중 7 (severe) 가 학습 분포 OOF 에서 **유의미한 예측 기여 (informative signal) 임을 강하게 시사** (특히 Saatchi slice). 서빙 시 hardcoded 0 = production 시 학습된 informative weight 무효화 가능 → reported offline metric (calibrated 38.3% cold) 이 actual serving behavior 보다 **낙관적일 가능성을 강하게 시사** (단정 X — Stage 4 holdout / 서빙 log 비교 후만 정량)
- **Drift fix 옵션 재평가**: A.1 (학습 측 제거) = OOF 손실 확인 / **A.2 (서빙 측 actual 추출 / API contract 확장) ROI ↑ 재산정** 권고 — 운영팀 영역 (LLM 외)
- **종합 HTML 보고서** (`docs/트랙1_종합보고서_20260507.html`): 외부 보고용 executive 보고 (10 sections — Phase 0 + Stage 1 + Amendment + Audit 4 + 사전등록 governance 가치, §9 부록 = 내부 governance 메타 분리)
- **분류**: **none (정상 흐름)** — Phase 0 §4 stop trigger / governance-preserving close
- **운영 영향 X**: 운영 spec §1-§16 변경 X / `v3_filtered_tuned` 32f 운영 그대로 유지 / Production-time gap 정량 = Stage 4 holdout / 서빙 log 비교 = 후속 cycle
- **사전등록 governance 도입 가치**: HARK 위험 실질적으로 낮춘 cycle (drift fix → OOF 개선 가설 사전 freeze 후 결과 반증, 정직 보고) / operational anchor baseline 확정 / train-serve gap 정량 시사 / 운영 영향 분리 / 코덱스 사전+사후 검수 cycle 정상 작동
- **코덱스 사후 검수 (round 1-4 GO)**: P0×0 + P1×3 + P2×2 — round 1 (FAIL+soft fail 분리 / 38.7% reference 명확화 / 톤 정정 / 부록 분리 / HARK framing 톤 다운) + round 2-3 (잔여 sweep + HTML 부록 동기화) → round 4 GO 확정 (외부 보고 인계 가능)
- **본 cycle closeout (Option A, 2026-05-07)** — `docs/track1_phase0_closeout_20260507.md`:
  * **사용자 결정 A 선택**: 본 cycle 종결 (코덱스 권고대로) / Phase 0 §4 fail trigger 정상 종결 처리
  * **Same-cycle not advanced**: Stage 1B / Stage 2 / Stage 3 / Stage 4 confirmatory holdout 모두 미진입 (본 cycle 의 confirmatory evidence = 0건)
  * **Stage 4 holdout unopened**: Phase 0 §1.7 spec freeze 만 / actual seal/hash 미실행 / `data/curated/track1_locked_holdout_v1.parquet` 미생성 / future winner 정해진 뒤에만 봉인
  * **A.2 path 후속 분리**: 운영팀 inquiry (서빙 측 actual value 추출 / API contract 확장 feasibility) = same-cycle continuation X / 별도 path
  * **Phase 0 freeze + Audit 4 결과 = immutable terminal evidence** (본문 개정 X / closeout stamp + link 만 추가)
- **Closeout 코덱스 사후 검수**: P0×0 + P1×0 + P2×1 (Owner 필드 hygiene) → GO
- **승인**: 사용자 검토 + 코덱스 closeout 사전 자문 (P0×3 + P1×2) + 사후 검수 GO

## Progressive sampling + Sample size sensitivity (2026-05-07)

> 트랙 2 의 실험 방법론 검증 cycle (HARK-safe variant + descriptive baseline stability).
> 운영 영향 X / framing + record 정리 성격 (코덱스 권고 deviation log follow-up PR-A 영역).

### 2026-05-07 — [Progressive sampling cycle 종결 + sub-report HTML] A 결정 / Axis B 우선 (none, 정상 흐름)
- **사용자 결정**: A 옵션 (본 cycle 종결) + Axis B license-first 우선 진행 + Progressive Sampling test sub-HTML 외부 보고용 별도 정리
- **본 cycle 종결 사유 (코덱스 사후 검수 종합)**: Stage 1 family-level retain 0건 / advancement evidence X / Stage 1 noise std 9.41% = decision-grade 승급 근거 부적합 / pruning 근거는 충분
- **Phase 0 holdout 봉인 유지**: cancel X — `data/curated/progressive_sampling_locked_holdout_v1.parquet` (SHA-16 1933a0947a918fc9) governance-preserving stop / future preregistered cycle 또는 Axis B 결과 후 재사용 가능
- **Sub-report HTML** (`docs/progressive_sampling_subreport_20260507.html`): 코덱스 사전 자문 (8 sections + measured tone) 적용. 외부 보고용 (1-2 page executive). FAIL framing 회피 / "exploratory cycle concluded under stopping logic" / Axis B 우선 동일 decision logic 으로 framing
- **분류**: **none (정상 흐름)** — Phase 0 stop logic 정상 trigger / governance-preserving close
- **운영 영향 X**: 운영 spec 변경 X / 본 cycle = exploratory only

### 2026-05-07 — [Progressive sampling Checkpoint 1 v2] 코덱스 사후 검수 P1×4 + P2×3 적용 → Stage 2 HOLD / 종결 권고 (minor)
- **Checkpoint 1 v2 변경 사항** (`docs/progressive_sampling_checkpoint1_20260507.md`):
  * 코덱스 P1×4 fix: Stage 1 advancement criterion 명확화 / framing 톤 다운 / coding rule deviation 명시 / decision matrix table 보강
  * P2×3 fix: language consistency / sub-section header / footer reference
- **Stage 2 진입 결정**: HOLD (코덱스 권고)
  * Stage 1 family-level retain 0건 (5 family 중 0건 confirmatory PASS)
  * Noise std 9.41% — decision-grade 승급 근거 부적합 (coverage 의 statistical significance 부족)
  * Pruning 근거는 충분 (5 family 중 cheap 4종 + complex 1 모두 advancement evidence X)
- **분류**: minor (사후 정정)
- **운영 영향 X**: exploratory only
- **승인**: 사용자 검토 + 코덱스 사후 검수 P1×4 + P2×3 통과

### 2026-05-07 — [Progressive sampling Phase 0 + Stage 1 Checkpoint 1] HARK-safe variant 진입 (none + minor)
- **사용자 명시**: 200/500/1000 sample 점진 확장 방식 — pre-registration governance 적용
- **Phase 0 freeze** (`docs/progressive_sampling_phase0_freeze_20260507.md`):
  * Locked holdout 봉인: SHA-16 1933a0947a918fc9 / 200 sample / artist-cluster GroupKFold
  * Stage 1 advancement criterion: family-level retain (cluster bootstrap 99% CI Δ ≤ 0)
  * Stage stop rule: family-level retain 0건 시 Stage 2 HOLD
- **Stage 1 Checkpoint 1 결과**: 5 family (cheap 4 + complex 1) 모두 advancement evidence X
  * Cheap 4: P0=0 / P1×6 + P2×4 (코덱스 사후 검수 사후 정정)
  * Complex 1: 동일 advancement evidence X
  * Phase 0 stop trigger 정상 작동
- **분류**: **none (정상 흐름)** + minor (사후 정정 P1+P2)
- **운영 영향 X**

### 2026-05-07 — [Sample size sensitivity descriptive analysis] 운영 baseline stability 관찰 (none, 정상 흐름)
- **사용자 명시**: `data/curated` 200/500/1000 sample baseline 비교 — 트랙 2 Stage 1 advancement 의 sample size dependence 점검
- **Descriptive analysis** (`docs/sample_size_sensitivity_results_20260507.md`):
  * 200 sample: noise std 9.41% / advancement margin 평균 -2.1%
  * 500 sample: noise std 7.8% / advancement margin 평균 -1.4%
  * 1000 sample: noise std 5.6% / advancement margin 평균 -0.9%
  * → noise std 의 sample size dependence 관찰 / advancement margin 의 안정성 200 sample 시 부족
- **Phase 0 design implication**: Progressive sampling 의 200 sample base = noise std 큰 영역 → advancement criterion 의 statistical power 부족 가능성 시사
- **분류**: **none (정상 흐름)** — descriptive analysis only / decision-binding X
- **운영 영향 X**

## 후속 PR 에서 append 예정 entries

> 본 PR (PR-A: Progressive + Sample size) 의 scope 외 entries 는 후속 PR 에서 append:
> - **PR-B (Track 2 + Axis B)**: Phase 1 → Phase 2 전이 (Stage 4 v3 / Stage 6A / Stage 6B / Architecture close) + Stage 5 acquisition cycle + Feature Track Axis A.1-A.5 + Phase 2 v4 재정의 + Axis B Round 1-3 + handoff packet
