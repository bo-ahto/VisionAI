# Track 1 Audit 4 — Drift Fix Variant OOF Rerun Results

> **작성일**: 2026-05-07
> **Amendment**: `docs/track1_amendment_drift_fix_20260507.md` (drift fix freeze)
> **실험**: `scripts/audit4_drift_fix_eval.py` / `model_test_results/audit4_drift_fix_v1_metrics.json`
> **본 단계 범위**: Audit 4 (단일 candidate OOF rerun) — 코덱스 권고 마지막 audit 단계

> ⚠️ **본 결과 framing (코덱스)**: exploratory diagnostic only / Phase 0 §1.8 decision-binding 분리 / 운영 spec 변경 단독 trigger X / Stage 4 confirmatory holdout 진입 전 단계.

## 0. 한 줄 요약

> **Audit 4 판정 (Phase 0 §4 stop criteria)**: **FAIL (primary) + Hard gate 2 violation** — drift_fix_v1 (23f) 의 Overall MdAPE 가 baseline 32f 대비 **+0.70%p 악화** (Ensemble) + **Saatchi slice +1.80%p 악화** (hard gate 2 비대칭 violation).
>
> **핵심 시사 (코덱스 P1 톤 정정)**: drift features 9개 중 7개 (severe drift 카테고리 A) 가 **학습 분포 OOF 에서 유의미한 예측 기여를 강하게 시사** (특히 Saatchi slice). 서빙 시 hardcoded 0 으로 받는 = **production 시 학습된 informative weight 가 inference 시 무효화** 가능 → reported offline metric (38.3% calibrated production-cold reference) 이 actual serving behavior 보다 **낙관적일 가능성을 강하게 시사** (단정 X — Stage 4 holdout / 서빙 log 비교 후만 정량).
>
> **운영 영향 X (현 시점)**: 본 audit 단독 = 운영 spec 변경 trigger X. Production reality gap 평가 = Stage 4 confirmatory holdout + 운영 inquiry (서빙 측 actual value 추출 가능성) 후 결정.

## 1. 결과 표 (3-split 정합 비교)

> 두 variant 모두 동일 spec: 입체 필터 적용 (28,376 rows / 1,551 artists) / 운영 best params (`integrated_v3_filtered_tuned_best_params.json`) / GroupKFold 3-split / KFold 3-split / random_state=42.

| Metric | baseline 32f | drift_fix_v1 23f | Δ | Practical flag |
|---|---|---|---|---|
| **Overall CatBoost** (GroupKFold) | 40.20% | 41.30% | **+1.10%p** | ✗ **FAIL** (Δ > 0) |
| **Overall XGBoost** (GroupKFold) | 41.10% | 41.60% | **+0.50%p** | ✗ **FAIL** (Δ > 0) |
| **Overall Ensemble** (GroupKFold) | **40.20%** | **40.90%** | **+0.70%p** | ✗ **FAIL** (Phase 0 primary: Δ ≤ -0.7%p 미달) |
| Artsy Ensemble (GroupKFold) | 35.40% | 35.30% | -0.10%p | ≈ 동등 |
| **Saatchi Ensemble** (GroupKFold) | 42.50% | **44.30%** | **+1.80%p** | ✗ **Hard gate 2 violation** (source slice 비대칭 악화) |
| Warm slice XGBoost (KFold) | 10.30% | 10.30% | +0.00%p | ✓ non-regression OK (Hard gate 3) |

> **Hard gates 평가** (Phase 0 §1.4):
> - Hard gate 1 (low-price cold harm): 본 audit 미측정 (price segment 분리 X — Stage 1B/2 영역)
> - **Hard gate 2 (source slice 비대칭): violation** — Saatchi +1.80%p / Artsy -0.10%p
> - Hard gate 3 (Warm KFold non-regression): ✓ pass (Warm slice 동등)

## 2. 해석 (코덱스 framing 톤 — exploratory diagnostic)

### 2.1 Drift features 의 실제 informative 정도 (가설 강하게 시사)
- Stage 1 audit 의 위험 신호 가설: "drift features 가 학습 시 informative 가능성"
- Audit 4 결과: **9 features 제거 시 Overall +0.70%p / Saatchi +1.80%p 악화** → drift features 가 학습 분포 OOF 에서 **noise 가 아닌 informative signal 임을 강하게 시사**
- 특히 Saatchi 큰 악화 = `has_seoul` / `has_international` / `has_depth` 등이 Saatchi 분포에 strongly informative 추정 (별도 ablation 필요 — 본 cycle 비목표)

### 2.2 학습-서빙 gap 의 의미
- 학습 시 informative features 가 서빙 시 hardcoded 0 = **production model 의 학습된 weight 가 inference 시 무효화** 가능
- Reported offline metric (calibrated 38.3% cold) 이 production reality 보다 **낙관적일 가능성을 강하게 시사** (단정 X — Stage 4 holdout / 서빙 log 비교 후만 정량)
- production reality gap 의 정량 측정 = Stage 4 confirmatory holdout + 서빙 log 비교 영역 (본 audit 비목표)

### 2.3 Drift fix 옵션 재평가 (Audit 4 결과 후)

| 옵션 | 의미 | Audit 4 결과 영향 |
|---|---|---|
| **A.1** (학습 측 제거) | 9 features 제거 후 재학습 | Overall +0.70%p / Saatchi +1.80%p 악화 확인 — **OOF metric 손실** / production reality 와 **정합 가능성** (학습-서빙 일관성 회복, but 정량 미검증) |
| **A.2** (서빙 측 actual 추출) | request contract 확장 / 서빙 측 actual value 입력 | **Audit 4 미측정** — request contract 확장 가능성 평가 = 운영팀 영역 (LLM 외) |
| **A.3** (현 상태 유지) | drift 인지 + production-time monitoring | OOF metric 유지 but production 시 잠재적 gap 인지 |

> **코덱스 권고 (사전 자문)**: A.1 권고 — 단 Audit 4 OOF metric 손실 확인 후 **A.2 (서빙 측 actual 추출 가능성 평가)** 우선순위 ↑ 재평가 필요. 본 cycle 결과 = "drift features 의 informative 정도 강하게 시사" → A.2 path 의 ROI 재산정 (운영팀 inquiry 영역).

## 3. Stop criteria 적용 (Phase 0 §4)

| Criteria | 본 결과 | 결론 |
|---|---|---|
| `pass`: Overall 개선 + hard gate 무위반 | ✗ Overall +0.70%p 악화 | 비충족 |
| `soft fail`: Overall 개선 but slice/warm 악화 | ✗ (Overall 도 악화) | 비해당 |
| `fail`: Overall 비개선/악화 | ✓ Overall +0.70%p / Saatchi +1.80%p | **trigger** |

→ **Audit 4 = FAIL** (Overall 악화 + Saatchi slice 비대칭 악화). Phase 0 §4 stop rule "Overall 비개선/악화" 정확히 trigger.

## 4. 운영 영향 (코덱스 framing — 운영 spec 변경 단독 trigger X)

- **현 시점 운영 spec 변경 X**: `v3_filtered_tuned` 32f 운영 그대로 유지
- 본 audit 결과 = **drift fix path 의 OOF metric 손실 확인** + **drift features 가 production-time 학습-서빙 gap 의 잠재 source 임을 강하게 시사** (단정 X — Stage 4 holdout / 서빙 log 비교 후만 정량)
- Production trigger = Stage 4 confirmatory holdout + shadow / staged rollout 별도 의사결정 gate

## 5. 다음 단계 (사용자 결정 영역)

| 옵션 | 본질 | 코덱스 권고 |
|---|---|---|
| **A. 본 cycle 종결 (Phase 0 §4 fail trigger)** | drift fix path 의 OOF 손실 확인 / Stage 1B 진입 X / Axis B license-first 우선 | **권고** — 동일 logic (정보 부족 1차 병목) |
| B. Stage 1B (importance + stability) 진입 | drift_fix_v1 23f baseline 기준 importance / stability 평가 / 새 hypothesis family 발굴 | 보류 — drift fix path 자체가 OOF 손실 |
| C. A.2 path 진입 (운영팀 inquiry) | request contract 확장 가능성 평가 / 9 drift features 의 서빙 측 actual 추출 | LLM 외 영역 (운영팀 / API 변경 의사결정) |
| D. 별도 axis 진입 (HP tuning / ensemble redesign) | Phase 0 §1.8 권고 순서 (feature subset 안정 후) — 본 결과 = feature subset 미안정 | 비추천 (현 시점) |

## 6. Honesty caveats (코덱스 P1)

- **OOF metric 손실 ≠ production reality 더 나쁨 단정**: drift features 가 학습 분포 OOF 에서 informative 였음을 강하게 시사 (단정 X). Production-time actual gap = Stage 4 holdout + 서빙 log 비교 후만 정량 가능
- **본 audit 단독 = 운영 spec 변경 trigger X**: Phase 0 §1.8 decision-binding 분리 그대로
- **Saatchi 큰 악화 (+1.80%p) 의 attribution 미수행**: 9 features 중 어느 것이 main driver 인지 별도 ablation 필요 (본 cycle 비목표 — `has_seoul` / `has_international` / `has_depth` 가 Saatchi 분포에 informative 가설)
- **3-split caveat**: 본 audit 의 baseline 32f 3-split 결과 (40.20% Ensemble) ≠ 운영 metrics.json 의 38.7% Ensemble. 차이 = **(a) 본 audit 3-split rerun vs prior 5-fold offline ensemble + (b) production-path calibrated 38.3% (CatBoost) vs offline ensemble 38.7% 차이** (`docs/model_technical_report_v2.md:53` 참조). 본 audit = 두 variant 정합 비교 only / 운영 reported metric 직접 비교 부적합

## 7. 코덱스 자문 이력 (내부 governance 메타)

> 본 섹션은 외부 보고 본문 외 내부 governance 추적 메타. 외부 독자는 §0-§6 + §8 만 참조해도 충분.

| 차수 | 내용 |
|---|---|
| Track 1 사전 자문 (2026-05-07) | 조건부 GO + Phase 0 freeze 우선 |
| Stage 1 사후 검수 | Option A first 권고 |
| Option A drift fix 사전 자문 | mini-prereg 불필요 / amendment memo 필요 / 7 drift + 2 dead 재분류 / A.1 권고 |
| Audit 4 사전 자문 | 옵션 B (별도 script) / 운영 best params / 3-split / audit4 prefix |
| Audit 4 결과 검수 (round 1-3) | FAIL trigger 정당성 / Source 비대칭 해석 / 톤 정정 (P1×3 + P2×2) |

> 누적 카운트 (트랙 2 + 트랙 1 합산, 본 cycle 시점): 트랙 2 P0×17 + P1×80 + P2×40 / 트랙 1 P0×12 + P1×14 + P2×10. 내부 추적 only.

## 8. 참조

- Phase 0 freeze: `docs/track1_phase0_freeze_20260507.md`
- Stage 1 results v3: `docs/track1_stage1_results_20260507.md`
- Amendment memo: `docs/track1_amendment_drift_fix_20260507.md`
- Audit 4 script: `scripts/audit4_drift_fix_eval.py`
- Audit 4 metrics: `model_test_results/audit4_drift_fix_v1_metrics.json`
- Audit 4 OOF dump: `model_test_results/audit4_drift_fix_v1_oof_groupkfold.parquet`
- 운영 spec / Methodology pipeline / Deviation log
