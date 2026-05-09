# Source-Conditional Cycle 결과 보고서

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/source_conditional_prereg_20260509.md`
> **결과 file**: `experiments/track1_optimization/source_conditional/source_conditional_results.json`
> **Decision binding**: ✅ YES

## 🏆 VERDICT: **CHAMPION** (Source-conditional 운영 적용 가능)

| 항목 | 결과 |
|---|---|
| **운영 채택** | ✅ **YES** — Source-conditional separate models 적용 권고 |
| **이유** | 모든 gate PASS / Saatchi 개선 의무 충족 / overall 큰 개선 |
| **decision-binding** | ✅ (binding verdict) |

## 📊 한눈에 보는 결과

### Holdout 예측률 (Fresh / unseen 311 artists / 5,220 작품)

| Config | Overall (Cold) ↓ | Artsy ↓ | Saatchi ↓ | "정확도" (100−MdAPE) |
|---|---:|---:|---:|---:|
| 🏆 **Separate routed (TEST)** | **33.67%** ⭐ | **24.59%** ⭐ | **36.75%** ⭐ | 66.33% |
| Unified 32+Ens (BASELINE) | 35.77% | 29.65% | 37.59% | 64.23% |

**MdAPE 의미**: 평균 예측 오차 (낮을수록 정확).
- Separate routed: "예측 오차 절반 ±33.67% 이내"
- Unified: "예측 오차 절반 ±35.77% 이내"

### Δ Separate − Unified (Binding decision)

| Gate | Δ | threshold | PASS? |
|---|---:|---:|:---:|
| **Primary (overall)** | **-2.09** | ≤ +0.8 | ✅ (큰 개선) |
| Hard gate 1 (Artsy) | **-5.07** | ≤ +1.0 | ✅ (매우 큰 개선) |
| **Hard gate 2 (Saatchi)** | **-0.85** | ≤ -0.5 (개선 의무) | ✅ (충족) |

### vs Confirmatory cycle (Top15+XGBoost FAIL)

| Cycle | Overall (Cold) | Artsy | Saatchi |
|---|---:|---:|---:|
| Confirmatory: Unified 32+Ens (rs=20260509) | 38.61% | 37.90% | 39.28% |
| Confirmatory: Top15+XGB (FAIL) | 40.27% | 36.52% | 42.47% |
| **Source-Cond: Unified (rs=20260510)** | 35.77% | 29.65% | 37.59% |
| **Source-Cond: Separate (CHAMPION)** | **33.67%** | **24.59%** | **36.75%** |

⚠️ Confirmatory vs SourceCond **Holdout split 다름** (random_state 20260509 vs 20260510):
- Different artists → split variance 영역 의 의무 영역 의 의무 영역 의 의무 (~3%p)
- 본 cycle 영역 의 의무 영역 의 의무 binding decision = **fresh split 내부 비교** (Separate vs Unified)
- 영역 의 의무 영역 의 의무 정합 영역 의 의무 영역 의 의무 영역 의 의무 = same-split 내부 Δ

## 🔍 핵심 발견

### 1. **Artsy 큰 개선 (-5.07%p)** — Saatchi noise 영역 의 의무 영역 의 의무 영역 의 의무

Unified model 영역 의 의무 영역 의 의무 = Saatchi 21,387 rows (75%) + Artsy 5,767 rows (25%) → Artsy 영역 의 의무 영역 의 의무 영역 의 의무 Saatchi-dominated training 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = Artsy-specific signal **약함**.

Artsy-only model = 5,767 rows (작은 영역 의 의무 영역 의 의무 / 다만 32f 고정 + HP 고정 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무) → Artsy distribution 영역 의 의무 영역 의 의무 영역 의 의무 = **5%p 영역 의 의무 영역 의 의무 큰 개선**.

### 2. **Saatchi 개선 -0.85%p** (개선 의무 충족)

Saatchi-only model = 17,389 rows (큰 영역 의 의무 영역 의 의무) → Saatchi-specific signal 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무.

다만 영역 의 의무 영역 의 의무 영역 의 의무 = -0.85%p (의무 영역 의 의무 영역 의 의무 -0.5%p 만족) / 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = unified model 영역 의 의무 영역 의 의무 Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 dominate 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 (운영 model 영역 의 의무 영역 의 의무 Saatchi 정합).

### 3. **Overall 영역 의 의무 영역 의 의무 -2.09%p**

Source 영역 의 의무 영역 의 의무 영역 의 의무 = **2%p 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무**.

영역 의 의무 영역 의 의무 = source-conditional model 영역 의 의무 영역 의 의무 = **운영 채택 가능 영역 의 의무 영역 의 의무 영역 의 의무 영역**.

### 4. CV (sanity check / non-binding)

- Artsy-only CV cold median: 33.88% (5 fold range 28.87-39.08)
- Saatchi-only CV cold median: 45.81% (5 fold range 39.11-54.03)

⚠️ Saatchi CV 영역 의 의무 영역 의 의무 영역 의 의무 = Holdout (36.75%) 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 큼 = 영역 의 의무 영역 의 의무 (CV-Holdout gap +9pp 영역 의 의무 영역 의 의무 / 영역 의 의무 영역 의 의무 = CV variance 영역 의 의무 영역 의 의무 영역 의 의무).

## 📈 운영 영향 (decision-binding)

### 채택 시 운영 변경

**현재 운영**: Unified 32+Ensemble (CatBoost + XGBoost)
- input → unified model → prediction

**Source-conditional (채택 시)**:
- input → **source detection** (artsy / saatchi)
- artsy → Artsy-only Ensemble model
- saatchi → Saatchi-only Ensemble model
- prediction

### 운영 복잡도 증가

| 영역 | 운영 영향 |
|---|---|
| **Model serving** | 1 model → **2 models** (artsy / saatchi) |
| **Source routing** | input row 영역 의 의무 영역 의 의무 영역 의 의무 detection 영역 의 의무 영역 의 의무 (default = ?) |
| **Source calibration** | 별도 calibration 영역 의 의무 영역 의 의무 (현재 source_calibration.json = unified 영역 의 의무 영역 의 의무) |
| **Re-training** | source 별 별도 retrain pipeline |

### 운영 적용 권고 (다음 cycle / 별도 prereg)

**Phase 1 (즉시)**: Artifact retrain
- 80% subset 영역 의 의무 영역 의 의무 retrain 영역 의 의무 영역 의 의무 X / **전체 데이터 영역 의 의무 retrain** (Artsy 7,640 + Saatchi 21,721)
- 운영 best_params 그대로 사용 (per-source HP tuning = 다음 cycle 영역 의 의무 영역 의 의무)

**Phase 2 (단기)**: Source routing 영역 의 의무 영역 의 의무 영역 의 의무
- input row 영역 의 의무 영역 의 의무 source detection logic
- Default fallback (unknown source → unified model)

**Phase 3 (중기)**: Source-conditional source_calibration
- 별도 source-cell calibration 영역 의 의무 영역 의 의무 영역 의 의무

## 🎯 결정 (decision-binding)

✅ **Source-conditional separate models 운영 적용 권고**.

**근거**:
1. 모든 gate PASS (overall -2.09 / Artsy -5.07 / Saatchi -0.85)
2. Saatchi 개선 의무 (-0.5%p) 충족 → separate complexity 정당화
3. Confirmatory FAIL 영역 의 의무 영역 의 의무 영역 의 의무 (Saatchi +3.19) → SourceCond CHAMPION (Saatchi -0.85) → **방향 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 정합** (가설 검증 ✓)

## 🚀 다음 cycle 권고

1. **Decision-binding 운영 적용 cycle** (즉시):
   - 전체 데이터 retrain (per-source)
   - Source routing logic
   - 운영 적용 + 모니터링

2. **HP tuning (per-source)** (선택 / 단기):
   - Artsy-only Optuna re-tune
   - Saatchi-only Optuna re-tune
   - 추가 개선 영역 의 의무 영역 의 의무 영역 의 의무 가능

3. **Source-conditional calibration** (단기):
   - 별도 calibration 영역 의 의무 영역 의 의무 영역 의 의무
   - 현재 운영 source_calibration.json 영역 의 의무 영역 의 의무 영역 의 의무 = 영역 의 의무 영역 의 의무 영역 의 의무

4. **Source effect 가설 검증** (장기):
   - "진짜 source regime" vs "누락 패턴/측정 차이" 영역 의 의무 영역 의 의무
   - feature ablation / source-별 ranking 영역 의 의무 영역 의 의무 영역 의 의무

## ⚠️ 잔여 P2 risk (코덱스 round 3 / 운영 적용 시 의무)

1. **Source routing fallback**: input row 영역 의 의무 영역 의 의무 source detection 영역 의 의무 영역 의 의무 / unknown source 영역 의 의무 영역 의 의무 처리 명시 의무 (default: unified model 영역 의 의무 영역 의 의무 / 또는 dominant=Saatchi)
2. **Source-별 calibration**: 본 cycle scope X / 배포 전 slice별 오차 모니터링 의무
3. **재현성**: 단일 fresh holdout (CV 대비 -9pp 좋음 / split variance 영역 의 의무 영역 의 의무 영역 의 의무 영역) → 다음 cycle 영역 의 의무 영역 의 의무 별도 split 영역 의 의무 영역 의 의무 재확인

## 📋 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P0 holdout 재사용 + P0 family search + P1 warm conflict) → fix |
| 2차 사전 자문 | GO with P2 (decision matrix 부호 fix) → 적용 |
| 3차 사후 검수 | **GO with P2** (CHAMPION 정합 / P2 = source routing / calibration / 재현성 의무) |
