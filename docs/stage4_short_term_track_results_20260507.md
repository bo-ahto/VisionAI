# Stage 4 단기 후속 트랙 — 통합 결과 보고

> **작성일**: 2026-05-07 (단기 트랙 작업 2/3/4 종합)
> **연계**: `docs/stage4_warm_validation_results_20260507.md` §8 (코덱스 7개 액션 중 단기 3개)
> **트랙 목표 / 비목표** (코덱스 명시):
> - 목표: 원인 분류 + 운영 완화 가능성 평가
> - **비목표**: 즉시 새 모델 우월성 주장 / 재학습 결정 (별도 후속 decision gate)

## 0. 종합 결론

> **운영 권고**: 본 단기 트랙은 **진단 + 운영 안전장치 보강**까지 닫음. 재학습 / 모델 변경 = 별도 후속 트랙.

| 작업 | 결과 | 운영 영향 |
|---|---|---|
| **2. Slice-conditional shadow spec** | `docs/slice_conditional_shadow_spec_20260507.md` 별도 문서, 5단계 + 보호 guardrail | spec §17.6 canonical + shadow 운영 분리 / 별도 승인 |
| **3. 저가 error decomposition** | **Feature 부족 가설 3/3 시그니처** (코덱스 1순위 정확 입증) | feature 추가 필요 (외부 source) — 본 트랙 비목표 |
| **4. Calibration 독립 검증** | **Global additive ✓ PASS** (low -3.11%p, overall +0.30%p) / 기타 FAIL | 후처리 운영 후보 (spec §4 후처리 규칙) |

## 1. 작업 2 — Slice-conditional Shadow Spec

### 1.1 산출물
- `docs/slice_conditional_shadow_spec_20260507.md` (10 섹션)
- spec §17.6 canonical 라우팅 로직 ↔ 별도 shadow 운영 spec 분리

### 1.2 핵심 설계 (코덱스 권고 반영)
- 5단계 (W-SC-S1 / S2 / W-SC-C1 / C2 / W-SC-F)
- **보호 guardrail (필수)**: low-price 강제 차단 + depth 15-24 보호 + composition-shift 자동 비활성
- **3축 coverage**: traffic / GMV / artist (단순 트래픽 % 가 아닌)
- Cold rollout 과 독립 (운영팀 capacity 분리 권고)

### 1.3 운영 의사결정
- W-SC-S1 진입 = 운영 미승인 (Stage 4 BORDERLINE 후 검토)
- 본 cycle 종결 = spec 작성 완료, **운영 승인은 별도 의사결정 gate**

## 2. 작업 3 — 저가 Error Decomposition

### 2.1 사전등록 (HARK 회피)
`docs/stage4_low_price_decomp_prereg_20260507.md` — low-price 정의 / 지표 / 판정 fix

### 2.2 핵심 결과 (Bias / Spread / Support)

| 모델 | slice | n | bias log (%) | residual std | residual IQR |
|---|---|---|---|---|---|
| **baseline** | low | 250 | **+0.322 (+38.0% 과대)** | 0.532 | 0.667 |
| baseline | mid_high | 181 | -0.265 (-23.3% 과소) | 0.439 | 0.661 |
| **fe_only** | low | 250 | +0.203 (+22.5% 과대) | 0.561 | 0.555 |
| fe_only | mid_high | 181 | -0.067 (-6.5%) | 0.449 | 0.453 |

→ **Bias structural** (low/high 양/음 구조적), **spread 큼** (저가 std 0.561 > 고가 0.449), **calibration 만으로 부족** 시그니처

### 2.3 Artist Support
- Low-price test artists (35명): train works median **18.0** / P25 13 / P75 27
- Mid-high test artists (33명): train works median **18.0** / P25 12 / P75 27
- → **Support 동일** (가설 3 기각) — 저가 작가의 데이터 부족이 원인 아님

### 2.4 Proxy 변수 (현재 모델 미사용)
| 컬럼 | low / high 분포 차이 |
|---|---|
| `medium_type` | Painting 72.8% vs 80.7% — 미세 |
| `category` | 동일 패턴 |
| `availability` | 모두 'for sale' 100% — 정보 X |
| `gallery_type` | 모두 'Gallery' 100% — 정보 X |
| `attribution_class` | Unique 91.6% vs 93.4% — 미세 |

→ **현 Artsy 메타데이터 범위 내 추가 feature 신호 미확인**. Feature 부족이 본질, **외부 source (Stage 5)** 가 다음 단계 (사전등록 §8.5 의 미수행 corr/bootstrap 으로 추가 검증 가능)

### 2.5 가설 시그니처 판정

| 가설 | 시그니처 일치 | 우선순위 |
|---|---|---|
| **Feature space 부족** | **3/3** ⭐ | 1순위 (코덱스 예측 정확) |
| Loss 한계 | 2/3 | 2순위 |
| Support 부족 | 0/1 | 기각 |
| Calibration 가능 | 0/1 | 기각 |

→ **최우세 가설: Feature space 부족** (사전등록 §5 의 우선순위 1과 정확 매칭)

## 3. 작업 4 — Calibration 독립 검증

### 3.1 결과 (baseline 모델 기준, low-price = price < 5M KRW)

| Method | overall | low | high | ECE | 판정 |
|---|---|---|---|---|---|
| Baseline (no cal) | 33.30% | 31.03% | 36.89% | 0.2536 | 기준 |
| **1. Global additive** | 33.60% (+0.30) | **27.92% (-3.11)** | 38.40% (+1.51) | 0.2512 | **✓ PASS** |
| 2. Low-price only | 36.08% (+2.78) | 33.69% (+2.65) | 36.89% (+0.00) | 0.2699 | ✗ FAIL |
| 3. Slice tertile | 31.05% (-2.25) | 36.57% (+5.54) | 24.22% (-12.67) | — | ✗ FAIL |
| 4. Isotonic (보조) | 33.30% (-0.00) | 31.49% (+0.46) | 33.69% (-3.20) | ↑ 악화 | 참고 — 운영 후보 아님 |

### 3.2 코덱스 해석 규칙 적용
- **Global calibration ✓ PASS** → "후처리 가치 있음"
- 단, low-price 전용 calibration FAIL = train ≠ test bias 분포 차이 (over-correction)
- Slice tertile FAIL = train tertile bias 가 test 에 일반화 X
- Isotonic 미세 효과 = 저가 segment 특이성 못 잡음

### 3.3 운영 함의
- Global additive calibration → **spec §4 후처리 규칙 후보** (운영 모델 정확도 -3.11%p 가능)
- 단, overall +0.30%p trade-off (수용 가능 범위)
- low-price 전용 / slice 별 calibration = **운영 적용 X** (over-fit 위험)

## 4. 통합 의사결정

### 4.1 운영 안전장치 강화 권고
| 항목 | 근거 | 운영 spec 반영 |
|---|---|---|
| Slice-conditional shadow 별도 운영 | 작업 2 | spec §17.6 canonical + 별도 shadow spec |
| 신규 warm 자동 fallback | Stage 4 composition-shift | spec §17.7 (이미 적용) |
| Low-price + depth 15-24 보호 guardrail | Stage 4 segment harm | shadow spec §3.2 |
| **Global additive calibration 후처리** | 작업 4 | spec §4 / §5.2 (calibration_applied) **후보** — baseline cold path 한정 shadow/post-processing 단계 (즉시 운영 통합 X, 다음 gate 결정) |

### 4.2 본질 해결책 = 별도 후속 트랙
- **Feature 부족 (작업 3)** → 외부 source 필요 (provenance / auction / market data)
- **Stage 5 = 외부 source prereg** (코덱스 권고 5번)
- **재학습 / segment-aware modeling** = 별도 decision gate (코덱스 비목표 명시)

### 4.3 한계 (정직 보고)
- 본 트랙 = curated Stage 4 (Artsy only) 데이터 한정
- 외부 source 통합 시 결과 변동 가능
- Calibration 효과 (-3.11%p) 는 baseline 모델 한정 — FE only 또는 slice-conditional 에 적용 시 검증 별도

## 5. 다음 단계

### 5.1 즉시 가능 (LLM)
- spec §4 calibration 후처리 후보로 §5 API 갱신 (`calibration_applied: true`)
- spec §17.6 / §17.7 / shadow spec 일관성 점검

### 5.2 운영팀 결정 (사용자 검토)
- Slice-conditional shadow 운영 시작 여부 (W-SC-S1)
- Global calibration 운영 도입 시점 (cold rollout 일부로?)
- Stage 5 외부 source 보강 cycle 시작 여부

### 5.3 코덱스 최종 검토
- 본 통합 결과 일관성
- 운영 spec 통합 안전성
- Stage 5 prereg 권고

## 6. 산출물

- 사전등록: `docs/stage4_low_price_decomp_prereg_20260507.md`
- Shadow spec: `docs/slice_conditional_shadow_spec_20260507.md`
- 실험: `experiments/structural_v1/stage4_low_price_decomp.py` + `stage4_calibration_validation.py`
- 결과 JSON: `experiments/structural_v1/results/stage4_low_price_decomp.json` + `stage4_calibration_validation.json`
- 본 보고서: `docs/stage4_short_term_track_results_20260507.md`
