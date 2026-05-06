# 트랙 2 Stage 2 Freeze — Track 2 GATE 2 산출물

> **작성일**: 2026-05-06
> **연계**: `docs/1개월_병행일정_V5_Structural.html` Week 2 GATE 2
> **연계**: `docs/데이터클렌징_단계계획_20260506.md` Stage 2

## 1. 요약

**Stage 2 OLS Hedonic feature set freeze: F4 (3 features)**

```
log_price ~ log_area + birth_year_centered + log_artist_total_works
```

> **후속 개선 적용 (Stage 3 검증 후 결정)**:
> - log_area 의 3-knot restricted cubic spline 1개 항 추가 (-1.24%p)
> - 손실함수 OLS → Huber loss (eps=1.35) 변경 (-1.15%p)
> - **최종 운영 채택**: F4 + log_area spline + Huber regression (Stage 3 100-seed MdAPE 24.07%)
> - 본 freeze 결정 (F4 baseline) 은 변경 없음 — feature set 자체는 그대로, 보강 적용만 추가

| 지표 | F4 | 기존 baseline (Core 5) | 차이 |
|---|---|---|---|
| MdAPE (30-seed LAO) | **24.59 ± 5.96%** | 28.75 ± 6.39% | **-4.16%p** |
| W30 | 57.5% | 53.5% | +4.0%p |
| W50 | 76.6% | 74.4% | +2.2%p |
| R² | 0.869 | 0.840 | +0.029 |
| max VIF | 1.2 | 1.5 | 더 안정 |
| 변수 수 | 3 | 8 | -5 (parsimony) |

## 2. 결정 근거

### 2.1 Forward Selection (greedy)
| Step | 변수 추가 | MdAPE |
|---|---|---|
| 1 | log_area | 56.24% |
| 2 | birth_year_centered | 24.51% (-31.7%p) |
| 3 | log_artist_total_works | 22.69% (-1.82%p) |
| 4 | career_stage | 22.68% (no improvement) |

→ medium / gallery_tier 는 forward 단계에서 선택되지 않음.

### 2.2 Elastic Net 채택률 (30-seed)
| 변수 | 채택률 |
|---|---|
| log_area | 100% |
| birth_year_centered | 100% |
| ln_followers | 93% |
| career_age | 83% |
| year_made_centered | 77% |
| career_stage | < 50% (자동 제거) |

→ career_stage 는 birth_year 와 강한 collinear (-0.877) 라 자동 제거됨.

### 2.3 변수 부호 일관성 (30-seed)
| 변수 | 부호 일관 % | 해석 |
|---|---|---|
| log_area | 100% | 면적 ↑ → 가격 ↑ ✓ |
| birth_year_centered | 100% | 신예 → 가격 ↓ ✓ |
| log_artist_total_works | 100% | 생산성 ↑ → 가격 ↑ ✓ |

→ 모든 변수 부호 100% 일관, 경제적 해석 명확.

### 2.4 추가 검증 결과 (코덱스 권고)

**1. Artist-grouped 10-fold CV**
- MdAPE 29.59 ± 11.18% (artist cold-start 변동성)

**2. 시기 분할 CV**
- ≤2020 → 2021+: 31.59% / ≤2023 → 2024+: 27.75% (시간 drift 없음 ✓)

**3. Medium/tier collapse**
- F4 + tier_high binary: 24.49% (-0.10%p, 미미한 개선)
- → 추가 안 함 (parsimony 우선)

**4. 잔차 가격대별 편향**
- 저가 (<20%): median resid -0.234 (over-predict)
- 고가 (>80%): median resid +0.212 (under-predict)
- → 후처리 calibration 으로 Stage 3 단계에서 보정

## 3. 변수 정의

| 변수 | 정의 | 처리 |
|---|---|---|
| `log_area` | log(작품 면적 cm²) | log transform |
| `birth_year_centered` | (작가 출생년 - 평균 출생년) | center |
| `log_artist_total_works` | log(1 + 작가 총 작품 수) | log1p |

타겟: `log_price = log(price_krw)`

## 4. 경제적 해석

| 변수 | β (full-sample) | 해석 |
|---|---|---|
| log_area | +0.78 | 면적 1% 증가 시 가격 +0.78% (size elasticity) |
| birth_year_centered | -0.05 | 출생년 1년 늦을수록 가격 -5% (작가 세대 효과) |
| log_artist_total_works | +0.15 ~ +0.25 | 작품 수 2배 증가 시 가격 +10~17% (생산성/시장 안정성) |

**한국 미술시장 가격 결정 = 작품 크기 + 작가 세대 + 작가 생산성**

## 5. 비교 대상

| 모델 | MdAPE (신규 작가) | 비고 |
|---|---|---|
| V3 운영 모델 (32 features GBM) | 28-48% | 현재 운영 |
| **F4 (3 features OLS)** | **24.59%** | 트랙 2 Stage 2 freeze |

→ 8x 적은 변수로 운영 모델 수준 정확도 + 해석 가능.

## 6. Stage 3 진입 조건

✅ Stage 2 GATE 2 통과 — Stage 3 진입 가능

**Stage 3 (Week 3) 진행 항목**
1. ME random intercept 추가: `log_price ~ F4 fixed effects + (1 | artist_slug)`
2. Within-artist 식별 (FE vs RE 비교 / Hausman test)
3. Variance decomposition (artist / 잔차 / 작품)
4. 가격대 calibration ablation

## 7. 한계 (운영 도입 caveat)

- **Cold-start 변동성**: 10-fold artist CV std 11.18% — 신규 작가 case 따라 편차 큼
- **가격대 편향**: 저가 over / 고가 under (log-price OLS 일반 한계)
- **표본 제약**: Stage 2 = 500 records / 50 artists (Stage 3 에서 1378/100 으로 확장 검증 필요)

→ Stage 3 단계에서 추가 검증 진행 후 최종 운영 모델 결정 (실제 결과: ME 는 cold-start 무력화 → 비채택, **F4 + log_area spline + Huber 채택**).

## 8. 산출물

- `experiments/structural_v1/stage2_ols_hedonic.py` — Core 5 / Main 7 / Sensitivity
- `experiments/structural_v1/stage2_feature_compare.py` — 6 set 비교
- `experiments/structural_v1/stage2_feature_extensive.py` — 22 set 확장 비교
- `experiments/structural_v1/stage2_career_age_test.py` — career_age 변형
- `experiments/structural_v1/stage2_advanced_tests.py` — Forward / Elastic Net / Interaction / Spline
- `experiments/structural_v1/stage2_final_candidates.py` — 최종 후보 검증
- `experiments/structural_v1/stage2_f4_validation.py` — 코덱스 Nit 4가지 검증
- `experiments/structural_v1/results/stage2_*.json` — 전체 결과 데이터

## 9. 코덱스 자문 결정 요약

| 차수 | 결론 |
|---|---|
| Stage 2 1차 자문 | Core 5 winner 판단 타당 (28.5%) |
| Forward 후 자문 | F4 채택 OK, 후처리 보정으로 가격대 편향 처리 |
| 검증 4 후 자문 | F4 freeze + Stage 3 ME 진입 |
| Stage 3 ME 자문 | ME 는 cold-start 무력화 → 비채택 |
| P1+P2 추가 실험 자문 | log_area spline + Huber 채택 권고 |
| B 단계 검증 자문 | **F4 + spline + Huber 운영 채택 — 취약 segment 방어력 입증** |

## 10. 다음 액션 (모두 완료)

- [x] Stage 2 freeze 결정 (5/6)
- [x] Stage 3 ME random intercept 검증 (cold-start 무력화 확인 → 비채택)
- [x] Calibration / 이원 전략 검증
- [x] log_area spline + Huber 추가 개선 실험
- [x] B 단계 검증 (Bootstrap CI / per-segment / coefficient stability)
- [x] 트랙 2 final report 업데이트 (Huber 채택 반영)
- [x] 임원 / 수식 / 쉬운설명 / freeze 보고서 4종 일괄 업데이트
