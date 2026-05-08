# 트랙 2 Cold Validation Cycle 1 — Stage 1 결과 보고서 (2026-05-08)

> **작성일**: 2026-05-08
> **Pre-registered analysis plan**: `docs/track2_cold_validation_cycle1_prereg_20260508.md`
> **실험 코드**: `experiments/structural_v1/track2_cold_validation_cycle1.py`
> **실험 결과**: `experiments/structural_v1/results/track2_cold_validation_cycle1_stage1.json`
> **Dataset**: `data/curated/stage4_full.parquet` (Artsy cleansed 8,495 / 807 작가, SHA-16 = `b7b51b81d3a033b5`)

## 0. 한 줄 요약

> **Cycle 1 Stage 1 판정: FAIL** — Stage 3 운영 채택 cold 모델 (F4 + log_area spline + Huber, curated 24.07%) 이 Stage 4 v3 broader 모집단 + 시간축 검증에서 **retract**:
> - Primary 1 (Random LAO 80/20): cold MdAPE **36.18%** (CI [31.47, 44.86]) — 임계 **26.07% 미충족**
> - Primary 2 (Time-split 2024+): cold MdAPE **43.15%** / degradation 4.08%p — 임계 + degradation **모두 미충족**
>
> **결론**: Stage 3 의 24.07% cold signal 은 1,378 작품 / 100 작가 curated dataset 의 특수 sample 에서만 관찰. broader 모집단 (8,495 / 807) + out-of-time 분할 시 cold MdAPE 36-43% 로 회복 — **트랙 2 cold 운영 적용 보류**.

## 1. Primary 결과

### 1.1 Primary 1 (B family) — Random LAO 80/20

| 항목 | 값 |
|---|---|
| Train rows | 6,806 (artists: 645) |
| Test rows | 1,689 (artists: 162, 정의상 모두 cold) |
| **Cold MdAPE (point)** | **36.18%** |
| **Cold MdAPE 95% CI** (artist-cluster bootstrap n=2,000) | **[31.47, 44.86]** |
| 사전 임계 (point + CI 상한) | ≤ 26.07% |
| 판정 | ✗ **FAIL** (point 36.18% > 26.07% / CI 상한 44.86% > 26.07%) |

### 1.2 Primary 2 (D family) — Time-split (≤2023 / 2024+)

| 항목 | 값 |
|---|---|
| Train rows | 4,207 (artists: 555) |
| Test rows | 4,288 (artists: 552) |
| Test cold rows | 3,260 (artists: 475) — train 작품 < 10건 |
| Test warm rows | 1,028 |
| **Cold MdAPE (point)** | **43.15%** |
| **Cold MdAPE 95% CI** | **[38.83, 47.35]** |
| Train cold MdAPE (in-sample) | 39.08% |
| **Time degradation** | **+4.08%p** |
| Warm MdAPE (supportive) | 35.33% |
| 사전 임계 (point) | ≤ 26.07% |
| 사전 임계 (degradation) | ≤ +3.0%p |
| 판정 | ✗ **FAIL** (point 43.15% > 26.07% / degradation 4.08%p > 3.0%p) |

### 1.3 Hard gates (Time-split base)

| Gate | Metric | 사전 임계 | 결과 | 판정 |
|---|---|---|---|---|
| Low-price (P25 이하 cold) | cold MdAPE | ≤ 28.07% | **63.67%** | ✗ **FAIL** |
| Cold sub-bin train_count=0 | cold MdAPE | ≤ 28.07% | 48.91% | ✗ FAIL |
| Cold sub-bin train_count=1-4 | cold MdAPE | ≤ 28.07% | 42.19% | ✗ FAIL |
| Cold sub-bin train_count=5-9 | cold MdAPE | ≤ 28.07% | 35.47% | ✗ FAIL |

→ **모든 hard gate 미충족** — cold 영역 내부 의 모든 분포 에서 임계 초과 (특히 저가 segment 63.67%).

## 2. Judgment (Intersection-union confirmatory gate)

| 항목 | 통과 여부 |
|---|---|
| Primary 1 point ≤ 26.07% | ✗ |
| Primary 1 CI 상한 ≤ 26.07% | ✗ |
| Primary 2 point ≤ 26.07% | ✗ |
| Primary 2 degradation ≤ +3.0%p | ✗ |
| Hard gate (low-price) | ✗ |
| Hard gate (cold sub-bin all) | ✗ |
| **Verdict** | **FAIL** (전 항목 미충족) |

> **Verdict 정의**: Primary 1 + 2 + 모든 hard gate 통과 시 PASS / 일부 통과 시 BORDERLINE / 전 항목 미충족 시 FAIL → **본 cycle = FAIL**.

## 3. 핵심 finding 해석

### 3.1 Stage 3 cold signal 의 retract

- Stage 3 (1,378 작품 / 100 작가, 100-seed): F4 + spline + Huber **24.07% (±4.18%)**
- Stage 4 v3 (8,495 / 807, Random LAO): **36.18%** — Stage 3 baseline 대비 **+12.11%p 회복**
- Stage 4 v3 (8,495 / 807, Time-split 2024+): **43.15%** — **+19.08%p 회복**

### 3.2 회복 사유 (가설 — 본 cycle 미검증)

- **Curated dataset 의 selection bias**: Stage 3 의 100 작가 = top works artists (충분 작품 수) — broader 모집단 의 long-tail 작가 (작품 수 적음) 미포함
- **Sample size effect**: Stage 3 의 100-seed std 4.18% 의 평균은 안정적이지만 모집단 의 systematic shift (selection 외) 미반영
- **Time drift**: 2024+ test 에서 추가 +6.97%p (43.15% vs 36.18%) — 2024+ 신규 작가 / 가격 분포 shift 가능성

### 3.3 외부 보고서 (PR #44, #45) 의 표현 reconcile

본 cycle 결과 = **외부 보고서의 "cold 영역 트랙 2 우위" 표현 reconsider 의무**:
- PR #44/#45 의 "Cold (학습 이력 부족 / 신규 작가) 트랙 1 28-48% / 트랙 2 24.07%" 표현은 **curated dataset 만 valid** — Stage 4 broader 모집단 에서는 트랙 2 36-43% 회복
- 트랙 1 의 28-48% 분포 vs 트랙 2 의 36-43% — 같은 평가 spec 의 직접 비교 미실행 (트랙 1 의 stage4_full.parquet 평가 X). 본 cycle 은 트랙 2 의 cold readiness 검증 만 / 트랙 1 비교는 별도 cycle.

## 4. Decision binding 적용 (사용자 환경 반영)

> Pre-registered: PASS → 콜론30 외부 의사결정 요청 자료 / FAIL → 운영 적용 보류 + 외부 보고

| 항목 | 결정 |
|---|---|
| Verdict | **FAIL** |
| 트랙 2 cold 운영 적용 | **보류** (코덱스 prereg + 본 결과 일치) |
| 콜론30 외부 보고 | **의무** (한계 + 후속 cycle 권고 명시) |
| 외부 보고서 (PR #44, #45) 정정 | **권고** (curated 24.07% vs broader 36-43% 차이 명시) |
| 후속 cycle (Cycle 2 source-expansion: A+C+G) | **재평가 의무** (Stage 4 v3 retract 후 Cycle 2 priority 변동 가능) |

## 5. Stage 2 (조건부) 진입 여부

> Pre-registered §2.2: Stage 1 BORDERLINE → Stage 2 (Bootstrap robustness 추가)

본 결과 = **FAIL** (BORDERLINE X) → **Stage 2 진입 X** (Bootstrap robustness 추가 의미 X — 이미 CI 광범위하게 임계 초과).

→ **Cycle 1 종결**.

## 6. 콜론30 외부 의사결정 요청 자료 (작성 권고)

본 결과 의 외부 보고 의무 항목:
1. **Cold 영역 트랙 2 우위 sub-claim 의 retract**: PR #44/#45 의 24.07% 는 curated dataset 한정 / broader 모집단 36-43%
2. **트랙 1 의 cold MdAPE 28-48% 분포 의 base**: 운영 reported (calibrated 38.3%) — 같은 spec 의 stage4_full.parquet 직접 비교 미실행
3. **운영 영향**: 트랙 1 (`v3_filtered_tuned` 32f) 그대로 유지 / 트랙 2 cold 적용 보류
4. **후속 의사결정 영역**:
   - 같은 spec 의 트랙 1 vs 트랙 2 직접 비교 (stage4_full.parquet) 별도 cycle 가능
   - Cycle 2 source-expansion (Saatchi 통합) priority 재평가
   - 외부 협력 (외부 데이터 source / API contract 확장) 으로 cold 영역 정확도 확보 우선순위 ↑

## 7. 본 cycle 의 의미 (positive framing)

> **본 cycle 의 가치 = 정직 보고**:
> - Stage 3 24.07% signal 의 retract 를 사전 정의 평가 protocol 로 정직하게 검증
> - "cold 영역 트랙 2 우위" sub-claim 의 한계 (curated dataset 한정) 명확화
> - 운영 main 모델 (트랙 1) 의 안전 유지 — 미검증 후속 모델 의 운영 적용 회피

## 8. 다음 단계

1. ⏳ **본 결과 보고서 코덱스 사후 검수**
2. ⏳ **콜론30 외부 의사결정 요청 자료** 작성 (외부 친화 톤 / 본 결과 + 후속 결정 요청)
3. ⏳ **외부 보고서 (PR #44, #45) 정정 권고** — "cold 영역 트랙 2 우위" 표현 reconcile
4. ⏳ (조건부) Cycle 2 source-expansion priority 재평가

## 9. Methodology deviation log entry 의무

본 cycle 의 결과는 `docs/methodology_deviation_log.md` 에 새 entry 로 기록 의무:
- Cycle 1 freeze + Stage 1 실행 + FAIL 결과 + 후속 cycle 권고

## 10. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Cold validation cycle 사전 자문 (2026-05-08) | B+D primary / Cycle 1+2 분할 / hard gate 권고 |
| Cycle 1 prereg 사후 검수 (round 1-3) | P0×2 + P1×3 + P2×1 fix → GO |
| 본 결과 보고서 사후 검수 (예정) | 본 commit 직후 |
