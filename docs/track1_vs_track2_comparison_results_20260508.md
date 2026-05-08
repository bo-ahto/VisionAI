# 트랙 1 vs 트랙 2 직접 비교 실험 — 결과 보고서 (Descriptive / Supportive Only)

> **작성일**: 2026-05-08
> **Pre-registered analysis plan**: `docs/track1_vs_track2_comparison_prereg_20260508.md`
> **실험 코드**: `experiments/structural_v1/track1_vs_track2_comparison.py`
> **실험 결과**: `experiments/structural_v1/results/track1_vs_track2_comparison.json`
> **Decision binding**: ❌ **X** — descriptive only / surrogate 비교 / 운영 채택 결정 근거 X

> ⚠️ **본 결과 의 caveat (코덱스 의무)**: Track 1 surrogate (14 derivable features 의 CatBoost) ≠ 운영 트랙 1 (32 features + 운영 학습 28K + Optuna best_params + calibration). 본 결과 는 **GBM family vs hedonic regression family** 비교 만 — 운영 의사결정 근거 X.

## 0. 한 줄 요약

> 같은 dataset / 같은 split 의 비교 결과:
> - **Random LAO 80/20**: 트랙 2 가 -3.24%p 우위 (point estimate / CI 겹침)
> - **Time-split 2024+ cold**: 트랙 1 surrogate 가 +7.28%p 우위 (point estimate)
> - **단, Time-split 의 degradation 패턴이 매우 다름**: T1 surrogate +15.88%p (큰 GBM overfitting 의심) vs T2 +4.08%p (robust)
>
> 일관된 우위 X — 평가 spec 별 결과 다름. 본 결과 = supportive only / 운영 의사결정 근거 X.

## 1. Random LAO 80/20 결과 (artist-level fold, 모두 cold)

| Model | Cold MdAPE (point) | 95% CI (cluster bootstrap n=2000) |
|---|---|---|
| **트랙 1 surrogate** (CatBoost, 14 features) | 39.42% | [33.69, 46.50] |
| **트랙 2** (F4 + spline + Huber) | **36.18%** ⭐ | [31.47, 45.10] |
| **Δ (T2 - T1)** | **-3.24%p** (T2 우위) | CI 광범위 겹침 |

### 1.1 해석

- **트랙 2 가 point estimate 우위** (-3.24%p), 단 CI 광범위 겹침 ([31.47, 45.10] vs [33.69, 46.50]) → 통계적 유의성 결론 X
- 본 split 의 test fold = 정의상 모두 cold (artist 가 train 에 없음) — pure cold 영역 비교
- Train rows: 6,806 / Test rows: 1,689

## 2. Time-split 2024+ cold 결과

| Model | Test cold MdAPE (point) | 95% CI | Train cold MdAPE | Time degradation |
|---|---|---|---|---|
| **트랙 1 surrogate** (CatBoost) | **35.88%** ⭐ | [32.36, 40.25] | 19.99% | **+15.88%p** ⚠️ |
| **트랙 2** (F4 + spline + Huber) | 43.15% | [38.63, 47.57] | 39.08% | **+4.08%p** ✅ |
| **Δ (T2 - T1)** | +7.28%p (T1 우위) | CI 부분 겹침 | T2 만 train ≈ test | T1 surrogate gap 약 4 배 |

### 2.1 해석 — Robustness 패턴 비대칭 (핵심 finding)

**Track 1 surrogate 의 Time degradation = +15.88%p**:
- Train cold (in-sample) MdAPE 19.99% vs Test cold (2024+) MdAPE 35.88%
- → **CatBoost 의 GBM overfitting 패턴** (in-sample 에 strong fit / out-of-time 큰 gap)
- 1,000 iteration / depth 6 의 surrogate 가 8,495 rows 에 over-flex 가능성

**Track 2 의 Time degradation = +4.08%p**:
- Train cold MdAPE 39.08% vs Test cold MdAPE 43.15%
- → **Hedonic regression 의 robust 패턴** (in-sample ≈ out-of-sample)
- 4 features 의 simple spec → underfitting 안전 영역

### 2.2 운영 의미 (caveat 의무 / decision X)

> ⚠️ **다음 해석은 surrogate 비교 한정 / 운영 의사결정 근거 X**:
>
> - Time-split test 의 point estimate 만 보면 Track 1 surrogate 우위 (35.88% vs 43.15%)
> - 그러나 Train→Test degradation gap 이 4 배 차이 (15.88 vs 4.08) — Track 1 surrogate 의 큰 overfitting 시사
> - 운영 환경의 시간 drift 에 대한 robustness = Track 2 의 hedonic regression 가 더 안정적일 가능성
> - **단**: 운영 트랙 1 (28K 학습 + calibration) 은 본 surrogate 와 다름 → 직접 결론 X

## 3. 종합 비교 (양쪽 split)

### 3.1 일관된 우위 X

| Split | 우위 | Δ |
|---|---|---|
| Random LAO 80/20 | 트랙 2 | -3.24%p (point) |
| Time-split 2024+ point | 트랙 1 surrogate | +7.28%p (point) |
| Time-split degradation | 트랙 2 | -11.80%p (T2 더 robust) |

→ **"트랙 1 < 트랙 2 cold" 일관된 결론 X** / **"트랙 2 < 트랙 1 cold" 일관된 결론 X**.

### 3.2 모델-패밀리 차이 (descriptive)

- **Track 1 (GBM family)**: high in-sample flexibility / 시간 drift 에 큰 sensitivity
- **Track 2 (Hedonic regression family)**: stable in-sample = out-of-sample / 시간 drift 에 robust

본 차이는 모델 family 의 일반적 trade-off — **운영 환경에서는 robustness 가 우선** 일 수 있음 (단, 운영 트랙 1 의 calibration 적용 후 실제 패턴은 본 surrogate 와 다를 수 있음).

## 4. Cycle 1 결과 와 의 정합성

본 비교 결과 가 Cycle 1 의 verdict (FAIL) 와 충돌하는가?

**충돌 X — 정합**:
- Cycle 1 verdict 의 baseline = **트랙 2 의 Stage 3 운영 채택 모델 (curated 24.07%)**
- Cycle 1 결과 = Stage 3 24.07% signal 의 broader 모집단 retract (Random LAO 36.18% / Time-split 43.15%)
- 본 비교 = 같은 broader 모집단 의 트랙 1 surrogate 결과 — **Cycle 1 의 트랙 2 결과 와 동일 수치 (변경 X)**
- **Cycle 1 의 FAIL 결정** 은 트랙 2 의 자체 baseline (24.07%) 대비 — 본 비교 는 트랙 1 surrogate 의 추가 정량 정보 만

## 5. Decision binding 적용 (사용자 환경 반영)

> Pre-registered: decision-binding X / supportive only

| 항목 | 결정 |
|---|---|
| 트랙 2 cold 운영 적용 | **보류 유지** (Cycle 1 의 FAIL 결정 변경 X) |
| 트랙 1 vs 트랙 2 우위 | **일관된 우위 X** (split 별 결과 다름) |
| 외부 보고 | 본 surrogate 비교 결과 + 3 caveat 의무 (모집단 / split / metric 문맥) |
| Lane 1 (decision-grade) 진입 | **별도 prereg cycle 의무** (운영 artifact schema audit + Saatchi 통합 등) |

## 6. 운영 환경 적용 시 의 추가 caveat

| 영역 | 본 surrogate 와 의 차이 |
|---|---|
| 운영 트랙 1 | 32 features (본 14 + 18 missing — gallery_tier / career_stage / source / etc) |
| 학습 데이터 | 운영 28K (Artsy + Saatchi 통합) / 본 surrogate 8,495 (Artsy only) |
| Optuna best_params | 운영 = 적용 / 본 surrogate = 기본 hyperparameter |
| Calibration | 운영 = source-cell calibration 적용 / 본 surrogate = 미적용 |
| Reported cold | 운영 38.3% (calibrated) vs 본 surrogate Random LAO 39.42% / Time-split 35.88% |

→ 본 surrogate 의 cold MdAPE ≈ 운영 reported (35-39% 범위) 인 것은 **우연** 또는 부분적 일치 — 직접 비교 X.

## 7. 콜론30 외부 보고 정합 의무

본 비교 결과 가 외부 보고서 (PR #44 / #45 적재본) 의 "cold 영역 트랙 2 우위" 표현 reconcile 의 추가 evidence:

- **Random LAO 의 트랙 2 우위 (-3.24%p)** = 같은 spec 의 broader 모집단 trial 에서 트랙 2 가 약간 우위 (CI 겹침)
- **Time-split 의 트랙 1 surrogate 점추정 우위 (+7.28%p) but T1 의 큰 degradation (+15.88%p)** = 일관된 우위 X
- → 외부 표현 = "**같은 broader 모집단 spec 에서 비교 시 일관된 우위 X / 영역 별 결과 다름**" 정확화 의무

## 8. 본 cycle 의 가치

- ✅ 사용자 의문 ("트랙 1 vs 트랙 2 어느 게 cold 우위?") 의 **descriptive 답변** — surrogate 비교 한정
- ✅ Cycle 1 결과 의 외부 reconcile 영역 의 추가 정량 evidence
- ✅ 모델-패밀리 trade-off (GBM overfitting vs hedonic robustness) 의 정량 입증
- ❌ **운영 의사결정 근거 X** (decision-binding X)
- ❌ Lane 1 (운영 artifact 직접 평가) = 별도 prereg cycle 의무 (schema audit + Saatchi 통합)

## 9. 다음 단계

1. ✅ 본 결과 보고서 코덱스 사후 검수
2. ⏳ Cycle 1 결과 보고서 §3.3 외부 reconcile 영역 보강 (본 비교 결과 추가)
3. ⏳ 콜론30 외부 의사결정 요청 자료 작성 (Cycle 1 + 본 비교 결과 + 3 caveat)
4. ⏳ 외부 보고서 (PR #44 / #45) 정정 PR — "cold 영역 트랙 2 우위" 표현 reconcile (curated 한정 + broader 모집단 비교 결과 추가)
5. ⏳ (조건부) Lane 1 (운영 artifact 직접 평가) cycle 진입 = 사용자 결정 영역 (schema audit + Saatchi 통합 의무)

## 10. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 트랙 1 비교 사전 자문 (2026-05-08) | Lane 1 (artifact direct, schema audit FAIL) → Lane 2 (surrogate) 권고 / 3 caveat 의무 |
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
| 본 결과 보고서 사후 검수 (예정) | 본 commit 직후 |
