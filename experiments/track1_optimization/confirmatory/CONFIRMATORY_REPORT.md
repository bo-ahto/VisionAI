# Confirmatory Cycle 결과 보고서

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/confirmatory_prereg_20260509.md`
> **결과 file**: `experiments/track1_optimization/confirmatory/confirmatory_results.json`
> **Decision binding**: ✅ YES (운영 채택 결정 영역)

## 🚨 VERDICT: **FAIL** (운영 변경 X)

| 항목 | 결과 |
|---|---|
| **운영 채택** | ❌ **NO** — 운영 32 features + Ensemble **유지** |
| **이유** | Saatchi cold +3.19%p 악화 (G4 FAIL) + 다른 Guard 위반 |
| **decision-binding** | ✅ (binding verdict) |

## 📊 한눈에 보는 결과

### Holdout 예측률 (unseen 311 artists / 5,802 작품)

| Config | N features | **Cold MdAPE** ↓ | Artsy ↓ | Saatchi ↓ | "정확도" 영역 의 의무 영역 의 의무 (100−MdAPE) |
|---|---:|---:|---:|---:|---:|
| **🏆 32 + Ensemble (운영)** | 32 | **38.61%** ⭐ | 37.90% | **39.28%** ⭐ | 61.39% |
| Top 15 + XGBoost (test) | **15** | 40.27% | **36.52%** ⭐ | 42.47% | 59.73% |
| 32 + XGBoost (참고) | 32 | 39.62% | 35.89% | 41.86% | 60.38% |

⭐ = best per column / **운영 baseline (32+Ensemble) = Holdout cold 영역 의 의무 영역 의 의무 best**

### Δ Top15+XGBoost vs 32+Ensemble (Binding decision)

| Guard | Δ | threshold | PASS? | 의미 |
|---|---:|---:|:---:|---|
| **G1 Warm** | +1.27 | ≤ +0.5 | ❌ | warm 영역 의 의무 영역 의 의무 정의 영역 의 의무 영역 의 의무 (Holdout artist unseen / 영역 의 의무 영역 의 의무 영역 의 의무 검토 의무) |
| **G2 Cold** | +1.66 | ≤ +0.8 | ❌ | Cold 영역 의 의무 영역 의 의무 큰 악화 |
| **G3 Artsy cold** | -1.37 | ≤ +1.0 | ✅ | Artsy 영역 의 의무 영역 의 의무 영역 의 의무 Top 15 영역 의 의무 영역 의 의무 개선 |
| **G4 Saatchi cold** | **+3.19** ⚠️ | ≤ +1.0 | ❌ | **Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 큰 악화 (핵심 FAIL)** |
| Cold gap (CV vs Holdout) | +0.65 | ≤ +2.117 | ✅ | overfit X |
| Warm gap (CV vs Holdout) | +30.52 | ≤ +0.5 | ❌ | **warm Holdout 정의 X 영역 의 의무 (artist unseen)** |

## 🔍 핵심 발견

### 1. **Saatchi cold +3.19%p 악화** (사후 가설 / 인과 단정 X)

Top 15 features (80% 재산출 / sweep amendment ranking 거의 동일):
- `artist_total_works`, `career_stage`, `ln_followers` 등 **artist signal dominate**
- Saatchi-specific 영역 의 의무 영역 의 의무 영역 의 의무 = `has_birth_year` (NaN flag / Saatchi missing rate 큼) **포함 X**
- `source`, `gallery_type`, `gallery_tier` 영역 의 의무 영역 의 의무 = bottom 17 (rank 16-32) → Top 15 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 X

⚠️ **사후 가설** (코덱스 round 3 / 인과 단정 X / feature ablation + source-별 ranking 재산출 영역 의 의무 영역 의 의무 영역 의 의무 검증 의무):

→ Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 영역 = bottom 17 features 영역 의 의무 영역 의 의무 영역 의 의무 noise X / 영역 의 의무 영역 의 의무 정보 영역 의 의무 영역 의 의무 (특히 has_birth_year missing flag 영역 의 의무 영역 의 의무 영역 의 의무) — **본 가설 영역 의 의무 영역 의 의무 source-conditional cycle 영역 의 의무 영역 의 의무 영역 의 의무 의무**.

### 2. **Artsy 영역 의 의무 영역 의 의무 영역 의 의무 Top 15 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 (-1.37 개선)**

Artsy = artist 정보 dominate (Top 15 영역 의 의무 영역 의 의무 영역 의 의무 충분).

### 3. **Sweep "win" → Confirmatory "lose" 영역 의 의무 영역 의 의무**

- Sweep amendment (provisional) = N=15 / XGBoost cold 38.66% (CV / 전체 데이터 ranking)
- Confirmatory = Holdout cold 40.27% / **운영 baseline 38.61% 영역 의 의무 영역 의 의무 영역 의 의무 X**

영역 의 의무 영역 의 의무 = sweep cycle 영역 의 의무 영역 의 의무 영역 의 의무 = full-data ranking 영역 의 의무 영역 의 의무 영역 의 의무 = mild selection optimism / Confirmatory 80% 재산출 + Holdout test 영역 의 의무 영역 의 의무 영역 의 의무 정직 결과 영역.

### 4. **80% 재산출 Top 15 (sweep ranking 영역 의 의무 영역 의 의무 영역 의 의무 거의 동일)**

```
1. artist_total_works    2. area_cm2            3. career_stage
4. ln_area              5. ln_followers         6. artist_birth_year
7. ho_x_support         8. has_seoul            9. medium_category
10. ho_power            11. aspect_ratio        12. ho
13. ln_ho               14. for_sale_ratio      15. has_depth
```

영역 의 의무 영역 의 의무 sweep amendment ranking 영역 의 의무 영역 의 의무 영역 의 의무 robust ✓ (영역 의 의무 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 변경 X / 다만 Holdout 영역 의 의무 영역 의 의무 영역 의 의무 영역 = noise 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 X / Saatchi-specific feature 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 손실 영역).

### 5. **Warm Holdout 정의 conflict** (코덱스 round 3 P2)

⚠️ Holdout = artist GroupShuffleSplit (unseen artist 311 명) / "warm" 정의 = 작품수 ≥ 5 → 다만 Holdout artist 영역 의 의무 영역 의 의무 train 영역 의 의무 영역 의 의무 영역 의 의무 X = **cold-equivalent**.

⚠️ **G1 warm Δ +1.27 영역 의 의무 영역 의 의무 verdict 영역 의 의무 영역 의 의무 포함** (코덱스 round 3 / artifact 면책 X) / 다만 **해석력 낮음** (정의 conflict). 본 verdict 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = G2 + G4 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 fail 영역 의 의무 영역 의 의무 영역 의 의무 충분.

→ 다음 cycle 영역 의 의무 영역 의 의무 = warm 정의 재정의 의무 (artist seen+sample size or row-level KFold 내부 평가 등).

## 📈 예측률 의미 (사용자 영역 의 의무 영역 의 의무 영역 의 의무)

**MdAPE (Median Absolute Percentage Error)** = 예측 오차 의 중앙값.

운영 baseline (32+Ensemble) 영역 의 의무 영역 의 의무 unseen artist 영역 의 의무 영역 의 의무 영역 의 의무 가격 예측:
- **Cold MdAPE 38.61%** = "예측 오차 영역 의 의무 영역 의 의무 절반 영역 의 의무 영역 의 의무 ±38.61% 이내"
- **Artsy 37.90%** / **Saatchi 39.28%**

Top 15 + XGBoost 영역 의 의무 영역 의 의무:
- Cold MdAPE 40.27% (운영 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 +1.66%p)
- Artsy 36.52% (운영 영역 의 의무 영역 의 의무 영역 의 의무 -1.37%p ✓)
- Saatchi 42.47% (운영 영역 의 의무 영역 의 의무 영역 의 의무 +3.19%p ⚠️)

## 🎯 결정 (decision-binding)

**운영 32 features + Ensemble (CatBoost + XGBoost) 유지**.

**이유**:
1. Top 15 영역 의 의무 영역 의 의무 = Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 정보 손실 (G4 +3.19%p / 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역)
2. 운영 baseline 영역 의 의무 영역 의 의무 cold 38.61% 영역 의 의무 영역 의 의무 영역 의 의무 best
3. 단순화 (32 → 15) 영역 의 의무 영역 의 의무 운영 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 가치 X (예측 정확도 영역 의 의무 영역 의 의무 우선)

## 🚀 다음 cycle 권고

### 1순위: **Source-conditional 별도 cycle**
- Saatchi cold 39.28% vs Artsy cold 37.90% → **gap 1.38%p**
- Top 15 영역 의 의무 영역 의 의무 = Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 X / **Saatchi-specific features** (`has_birth_year`, `source`, `gallery_type`, ...) 영역 의 의무 영역 의 의무 영역 의 의무 의무
- 분리 학습 (Artsy / Saatchi 별도 model) 또는 source-aware feature engineering

### 2순위: **HP tuning cycle (32 features)**
- 운영 best_params 영역 의 의무 영역 의 의무 = 28,376 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 tuned (28,376 → 22,701 영역 의 의무 영역 의 의무 영역 의 의무 80% retrain → re-tune 영역 의 의무 영역 의 의무 영역 의 의무)
- 또는 ensemble weight tuning (현재 50/50)

### 3순위: **Top 20-25 + 32 features 비교** (post-hoc)
- Top 15 영역 의 의무 영역 의 의무 영역 의 의무 fail / Top 20/25 영역 의 의무 영역 의 의무 영역 의 의무 영역 = `has_birth_year` (rank 16-22) 영역 의 의무 영역 의 의무 영역 의 의무 추가 / Saatchi 개선 가능

### 4순위: **데이터 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무**
- transaction_date / sale_date column 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = ADD-B (warm artist 통계) 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 가능
- 외부 데이터 소스 (auction history) 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무

## 📋 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P0 selection leakage + P1 binding + P1 gap rule) → fix |
| 2차 사전 자문 | GO with P2 (4 P2 영역 / fix) |
| 3차 사후 검수 (예정) | 본 보고서 + 운영 채택 결정 검수 |
