# 트랙 2 Cold Validation Cycle 1 — Pre-Registered Analysis Plan (2026-05-08)

> **작성일**: 2026-05-08 (cycle 1 freeze)
> **위치**: 트랙 2 (해석 가능 cold-start 모델) 의 cold 영역 운영 readiness 추가 검증 새 cycle
> **사용자 결정 근거**: 외부 보고서 (`docs/external/external_track1_track2_status_20260508.md`) 의 "신규 작가 영역 (cold) 1주 평가 단계 검토 가능" 결정 + 사용자 의문 "cold = 트랙 2 우위" 확인 후 추가 검증 의무 (Stage 4 BORDERLINE 의 cold readiness 보강)
> **본 cycle 의 본질**: archive cycle 종결 후 새 cycle (새 baseline + 새 hypothesis family + 새 prereg)
> **사전 자문**: 코덱스 (cold validation cycle 우선순위 + LLM/사용자 분리 자문, 2026-05-08)

> ⚠️ **본 cycle 의 환경 제약 (사용자 명시)**: shadow 평가 환경 X / 운영 트래픽 적용 X. **LLM 영역 = offline 검증 + 결과 해석 + readiness 보고서 + 외부 (콜론30) 의사결정 요청 자료 까지**. Production rollout / shadow / canary 영역 = 외부 의사결정 영역.

## 1. Cycle 1 Freeze 항목 (코덱스 권고 prereg 의무)

### 1.1 Baseline 고정 (단일 비교, 다중비교 부담 최소화)

| 항목 | 값 |
|---|---|
| Baseline 모델 | **트랙 2 Stage 3 운영 채택 모델** = F4 + log_area spline + Huber regression |
| Baseline metric (curated, Stage 3 100-seed) | Cold MdAPE **24.07% (±4.18%)** |
| Baseline source | `docs/트랙2_Stage2_freeze_20260506.md` §2 / `docs/stage3_*` Stage 3 100-seed 결과 |
| Comparator (트랙 1) | `v3_filtered_tuned` 32 features (운영 main, gradient boosting) |

> **Intersection-union confirmatory gate**: 트랙 2 의 Stage 3 cold signal (24.07%) 이 Stage 4 v3 broader 모집단 (Primary 1) + out-of-time split (Primary 2) 모두에서 유지되는가 — 두 gate 모두 충족 시 PASS / 둘 중 하나라도 미충족 시 BORDERLINE 또는 FAIL.

### 1.2 데이터셋 freeze

| Dataset | 사용 |
|---|---|
| Stage 4 v3 모집단 | `data/curated/stage4_full.parquet` — 8,495 rows / 807 artists / Artsy cleansed (`year_made` / F4 핵심 변수 모두 존재) |
| Stage 3 reference | `data/curated/stage3_1000x100.parquet` (1,378 / 100, baseline reference) |
| Saatchi 모집단 | **본 cycle 미포함** (Cycle 2 source-expansion 영역 — `year_made` provenance 봉인 의무 후만) |
| 외부 prediction (artue / printbakery) | **본 cycle 미포함** (decision-grade X) |
| 경매 데이터 (k-auction) | **본 cycle 미포함** (도메인 차이 — selection bias / target shift) |

### 1.3 Feature freeze

| Feature | 정의 |
|---|---|
| `log_area` | log(width_cm × height_cm) |
| `birth_year_centered` | artist_birth_year - mean(birth_year) |
| `log_artist_total_works` | log(artist 별 total works count) |
| `log_area` 의 3-knot restricted cubic spline | 추가 항 (-1.24%p) |
| **Loss** | **Huber** (sklearn HuberRegressor `epsilon = 1.35` — Stage 3 운영 채택 spec, `stage3_huber_validation.py:72` 일치) |
| **Train target** | `log(price_krw)` |

> 변경 X — Stage 3 운영 채택 spec 그대로 freeze.

### 1.4 Cold/Warm 영역 정의

| 영역 | 정의 |
|---|---|
| **Cold** | 학습 데이터 작가 이력 < 10건 (train-time 작가 별 작품 수 미만) |
| **Warm** | 학습 데이터 작가 이력 ≥ 10건 |

Stage 3 baseline 의 영역 정의와 동일.

### 1.5 Primary metric + Hard gates (코덱스 권고)

#### Primary 1 (B family) — Stage 4 v3 모집단 cold 재평가

| 영역 | Metric | 사전 임계 |
|---|---|---|
| **Primary 1 point estimate** | Stage 4 v3 모집단 cold MdAPE (point) | **≤ 26.07%** (Stage 3 baseline 24.07% + 2.0%p tolerance) |
| **Primary 1 CI** | Stage 4 cold MdAPE 의 **절대 95% CI 상한** (paired bootstrap X — Stage 3 와 Stage 4 모집단/artist universe 다름 / 본 cycle = Stage 4 cold MdAPE 의 절대 CI 만 고정) | **≤ 26.07%** (CI 상한 사전 고정 — 단일 임계) |

#### Primary 2 (D family) — Out-of-time split

| 영역 | Metric | 사전 임계 |
|---|---|---|
| **Primary 2 metric** | Time-split cold MdAPE (train ≤ 2023 / test 2024+, cold = test 작가 의 train 작품 < 10건) | **≤ 26.07%** (Primary 1 임계와 동일 — 시간축 비열화) |
| **Time-split degradation** | Test cold MdAPE − Train cold MdAPE | **≤ +3.0%p** (out-of-time degradation 임계) |

#### Hard gates (Secondary — 한 gate 라도 fail = rollout 후보 X)

| Gate | Metric | 사전 임계 |
|---|---|---|
| **🔴 Low-price segment harm** | 저가 P25 이하 segment 의 cold MdAPE (Stage 4 v3 모집단) | ≤ **28.07%** (26.07% + 2.0%p / Stage 4 v3 BORDERLINE 의 저가 harm 재발 방지) |
| **🔴 Cold sub-bin harm** | Cold 하위 구간 (train_count `0 / 1-4 / 5-9`) 별 cold MdAPE | 각 ≤ **28.07%** (cold 영역 내 train 이력 분포 별 harm 점검) |
| **🔴 Source slice asymmetry** | Saatchi 미포함 — 본 cycle scope 외 | N/A (Cycle 2 영역) |
| **🟡 Calibration robustness (Supportive)** | calibration plot residual 의 quantile 별 분포 | exploratory (decision-binding X) |
| **🟡 Bootstrap robustness (Supportive)** | 100-seed cluster bootstrap 의 seed 별 stability | exploratory |

#### 임계 정당화 (Justification)

- **+2.0%p tolerance** (24.07% → 26.07%): Stage 3 100-seed 의 std (4.18%) 의 약 1/2 — broader 모집단 shift 허용폭으로 보수적 (1 std 의 절반).
- **time-split degradation +3.0%p**: 운영 환경에서 시간축 drift 의 자연 noise 추정 (Stage 3 std 4.18% 의 70% 수준).
- **Cold sub-bin harm +2.0%p (28.07%)**: Primary 임계 (+2.0%p) 와 동일 budget — cold 영역 내부 분포 별 harm 도 모집단 평균 임계 와 동일 수준 보수적.
- **95% CI**: confirmatory gate 의 표준 — Stage 3 prereg 와 동일 알파.

#### Bootstrap hygiene (사전 고정 — 코덱스 P1)

- **방법**: artist-cluster bootstrap (with replacement on artists, all rows of selected artists in each replica)
- **n_boot**: **2,000** (Stage 3 spec 동일)
- **CI 방식**: percentile (2.5% / 97.5%)
- **Seed policy**: base seed = **42** (Stage 3 동일) / Bootstrap 내부 seed = `range(2000)`

### 1.6 Stop rule (Stage 별 — 코덱스 권고)

| Stage | Stop trigger |
|---|---|
| Stage 1 (B+D 평가 실행) | Primary 1 + Primary 2 결과 산출 / hard gate 평가 |
| Stage 2 (BORDERLINE 시 Bootstrap robustness 추가) | Stage 1 BORDERLINE → Bootstrap robustness 만 추가 (cycle 확장 X) |
| Cycle 종결 | Primary + Hard gate 결과 + readiness 보고서 + 콜론30 외부 의사결정 요청 자료 |

### 1.7 Decision binding (사용자 환경 제약 반영)

> ⚠️ **본 cycle 의 decision binding 변경**: shadow 평가 환경 X → "PASS → shadow 진입 자격" 권고를 **"PASS → 콜론30 외부 의사결정 요청 자료"** 로 변경.

| 결과 | 의사결정 |
|---|---|
| **PASS** (Primary 1 + 2 임계 충족 + 모든 hard gate 충족) | **콜론30 외부 의사결정 요청 자료 작성** (운영 적용 결정 = 콜론30 영역) — 운영 적용은 외부 결정 |
| **BORDERLINE** (Primary 1 임계 충족 / Primary 2 미충족 또는 hard gate 1건 violation) | **운영 적용 보류** + 콜론30 외부 보고 (한계 명시) |
| **FAIL** (Primary 1 임계 미충족 또는 hard gate 2건 이상 violation) | **운영 적용 보류** + 외부 보고 (cold 영역 추가 검증 cycle 의무) |

본 cycle 의 PASS = "운영 적용" 결정 직접 권한 X (LLM 영역 외 / 콜론30 외부 결정).

### 1.8 Confirmatory vs Exploratory 분리

| 항목 | 분류 |
|---|---|
| Primary 1 (B) Stage 4 모집단 cold 재평가 | **Confirmatory** (decision-binding) |
| Primary 2 (D) Time-split cold | **Confirmatory** (decision-binding) |
| Hard gate (low-price / cold sub-bin / source) | **Confirmatory** (rollout 후보 자격 차단) |
| Calibration plot / Bootstrap robustness | **Supportive** (exploratory / decision-binding X) |

## 2. 진행 protocol (Stage 1 / 2 / 종결)

### 2.1 Stage 1 — B+D Primary 평가

1. Stage 4 v3 모집단 (`stage4_full.parquet`, 8,495 / 807) 의 train/test split:
   - **Random LAO (Leave-Artist-Out, 80/20)** — Primary 1 base (artist-level fold / test fold = 정의상 모두 cold)
   - **Out-of-time split** — train: `year_made` ≤ 2023 / test: `year_made` 2024+ — Primary 2 base (cold 정의 = test 작가 의 train 작품 < 10건)
2. F4 + log_area spline + Huber 학습 (Stage 3 spec 그대로)
3. 영역 별 평가:
   - **Random LAO**: test fold 가 정의상 모두 cold → Cold MdAPE only (warm 영역 평가 X)
   - **Time-split**: cold (train < 10건) + warm (train ≥ 10건) 분리 / cold 만 Primary 2 / warm = supportive
4. Primary 1 + Primary 2 metric 산출 + Cluster bootstrap CI (§1.5 hygiene)
5. Hard gates 평가:
   - Low-price (P25 이하) segment cold MdAPE
   - Cold sub-bin (train_count `0 / 1-4 / 5-9` — Time-split base) 별 cold MdAPE

### 2.2 Stage 2 — Bootstrap robustness (조건부)

Stage 1 BORDERLINE → 100-seed cluster bootstrap 추가:
- seed 별 cold MdAPE distribution
- seed 별 임계 충족 비율 (PASS rate)

### 2.3 종결 산출물

- 결과 보고서 (`docs/track2_cold_validation_cycle1_results_YYYYMMDD.md`)
- 콜론30 외부 의사결정 요청 자료 (`docs/external/cold_validation_handoff_YYYYMMDD.md`)
- (조건부) BORDERLINE 시 Bootstrap robustness appendix

## 3. 본 cycle 미포함 (사전 명시)

| 영역 | 분류 | 사유 |
|---|---|---|
| Saatchi 모집단 통합 | Cycle 2 (source-expansion) | provenance 봉인 + cleansing 재산출 + source harm budget 사전등록 의무 (코덱스) |
| Source slice 비대칭 분석 | Cycle 2 동반 | Saatchi 통합 시 의무 |
| Calibration analysis (decision-grade) | Cycle 2 보조 | 본 cycle = supportive only |
| Bootstrap cluster CI 재산정 (Stage 4 BORDERLINE) | Stage 2 조건부 | 본 cycle Stage 1 BORDERLINE 시만 |
| 경매 데이터 (k-auction) | 비추천 | 도메인 차이 (selection bias / target shift) |
| 외부 prediction (artue / printbakery / wikidata) | exploratory only | decision-grade X |
| Production rollout / shadow / canary | 사용자 환경 외 | 콜론30 외부 의사결정 영역 |

## 4. LLM 영역 / 사용자 (콜론30) 영역 분리

### 4.1 LLM 가능 (본 cycle 영역)

- Cycle 1 prereg freeze (본 문서) — 사전 정의 + 사후 검수
- Stage 1 / Stage 2 실험 실행 (offline)
- 결과 해석 + gate 판정
- Readiness 보고서 작성
- 콜론30 외부 의사결정 요청 자료 작성 (외부 친화 톤)

### 4.2 사용자 / 콜론30 권한 (본 cycle 영역 외)

- Hard gate 임계 / harm budget 최종 승인
- Source 포함 여부 확정 (Cycle 2 의 Saatchi 통합)
- 운영 적용 결정 (PASS 후만)
- Production rollout
- Shadow / canary 평가 (사용자 환경 외 — 콜론30 결정)
- Reviewer signoff
- Rollback 판단

## 5. Deviation log 의무

본 prereg 의 변경 / 추가 / 생략은 모두 `docs/methodology_deviation_log.md` 에 기록 의무.

## 6. 다음 단계 (cycle 1 진행 절차)

1. ⏳ **본 prereg 사후 검수** (코덱스 사후 검수 round) — GO 후 freeze
2. ⏳ Stage 1 실험 스크립트 작성 (`experiments/structural_v1/track2_cold_validation_cycle1.py`)
3. ⏳ Stage 1 실행 (B+D Primary)
4. ⏳ Stage 1 결과 분석 + Stage 2 진입 여부 결정
5. ⏳ (조건부) Stage 2 — Bootstrap robustness
6. ⏳ Cycle 1 종결 — 결과 보고서 + 콜론30 외부 의사결정 요청 자료

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Cold validation cycle 사전 자문 (2026-05-08) | 우선순위 (B + D > A + C + G > F > E + H) / 새 prereg cycle 의무 / LLM/사용자 분리 / Cycle 1 (B+D) + Cycle 2 (A+C+G) 분할 |
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
