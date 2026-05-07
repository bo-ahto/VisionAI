# 트랙 2 (Interpretable Challenger) — 통합 README

> **작성일**: 2026-05-07
> **상태**: 분석/검증 100% 완료 / Production Phase A (shadow 1주) 착수 승인 가능 / Phase B (5% canary) 는 shadow 7개 게이트 PASS 후 별도 승인 필요
> **연계 plan**: `docs/1개월_병행일정_V5_Structural.html` Week 1-4

## 0. 한 줄 요약

**3개 변수 (작품 면적 + 작가 출생년 + 작가 총 작품수) + 면적 spline + Huber loss 로 V3 (32 features GBM) 의 신규 작가 약점 (28-48%) 을 약 24% 까지 개선한 해석 가능 모델.**

---

## 1. 산출물 인덱스 (핵심 8종 — 본 README 제외)

### 1.1 청중별 권장 시작 문서

| 대상 | 시작 문서 | 분량 |
|---|---|---|
| **대표 / 임원** | `docs/임원보고_트랙2_요약_20260506.html` | 1페이지 |
| **일반 독자** | `docs/트랙2_쉬운설명_20260506.html` | 9 섹션 (비유 위주) |
| **비전공 실무자** | `docs/트랙2_프로세스_쉬운버전_20260506.html` | 7 섹션 + 용어풀이 |
| **분석가 / 실무자** | `docs/트랙2_최종보고서_20260506.md` | 12 섹션 상세 |
| **모델 구현 담당** | `docs/트랙2_수식_프로세스_상세_20260506.html` | 11 섹션 + 수식 |
| **운영 / 인프라** | `docs/트랙2_production_통합_spec_20260507.md` | 17 섹션 (운영 spec) |
| **데이터 엔지니어** | `docs/데이터클렌징_단계계획_20260506.md` | Stage 1-3 plan |
| **결정 메모** | `docs/트랙2_Stage2_freeze_20260506.md` | GATE 2 freeze |

### 1.2 권장 읽기 순서

```
의사결정자 → 임원 1페이지 → (필요 시) 최종보고서
일반 독자  → 쉬운설명 → 프로세스 쉬운버전
구현/운영  → 최종보고서 → 수식 상세 → Production spec
신규 입문  → README (본 문서) → 쉬운설명 → 최종보고서
```

---

## 2. 핵심 결과 요약

### 2.1 운영 채택 모델

```
log_price = β₀ + β₁·log_area + β₂·birth_year_centered + β₃·log_artist_total_works
            + β₄·spline₁(log_area) + ε

손실함수: Huber loss (eps=1.35)
```

### 2.2 정확도 비교 (Stage 3 100-seed LAO)

| 시나리오 | V3 (32 feat GBM) | 트랙 2 (3 feat + spline + Huber) |
|---|---|---|
| Warm 작가 (학습 ≥ 10건) | 12-18% | 21-22% |
| **Cold 작가 (신규)** | 28-48% | **24.07±4.18%** ⭐ |
| Bootstrap 95% CI | — | [21.68, 25.08] |

→ **신규 작가 cold-start 정확도가 V3 대비 약 -4 ~ -24%p 우수**

### 2.3 누적 개선 단계

| 단계 | MdAPE | 개선 |
|---|---|---|
| F4 OLS baseline | 26.46±4.69% | (기준) |
| + log_area spline | 25.22±4.36% | -1.24%p |
| **+ Huber regression** ⭐ | **24.07±4.18%** | **-2.39%p 누적** |

### 2.4 취약 segment 방어력 (Huber 의 진짜 가치)

| Segment | OLS | Huber | 개선 |
|---|---|---|---|
| 저가 (<20%) | 34.27% | **28.46%** | **+5.81%p** ⭐⭐⭐ |
| 고가 (>80%) | 31.87% | **28.22%** | **+3.65%p** ⭐⭐ |
| Tier 3 (worst) | 26.74% | 24.56% | +2.18%p |

---

## 3. 진행 상황 (Week 1-4 plan 기준)

| Week | 계획 | 진행 |
|---|---|---|
| Week 1 (5/6~5/12) | 데이터 plan + 후보 정의 + GATE 1 | ✅ 100% |
| Week 2 (5/13~5/19) | feature set freeze + GATE 2 | ✅ 100% |
| Week 3 (5/20~5/26) | shadow 검증 + 최종 선정 + GATE 3 | 🟡 분석 100% / shadow 0% |
| Week 4 (5/27~6/2) | rollout + 안정화 + GATE 4 | 🟡 보고서 100% / 운영 도입 0% |

**전체 진행률 (분석/연구/보고): ~100%** ✅
**전체 진행률 (운영 도입): ~0%** ⏳ (Phase A shadow 착수 승인 가능 / Phase B 미승인 — shadow PASS 후 별도 승인)

---

## 4. Production 도입 단계 (코덱스 권고)

```
[Phase A] Shadow (0% 트래픽, 1주)
  └─ 7개 합격 기준 PASS → Phase B 승인

[Phase B] Canary 5% (cold-only, 2주)
  └─ KPI 정상 → 단계 확대

[Phase C] 10% → 25% 점진 확대
  └─ 운영 매니저 + 의사결정자 승인

[Phase D] Cold 작가 100% (안정화)
  └─ 4-5일 모니터링 + 정기 재학습
```

상세: `docs/트랙2_production_통합_spec_20260507.md` §11-§17 참조.

---

## 5. 입력 요구사항 (운영)

### 5.1 필수 입력 (예측)

| 변수 | 단위 | 예시 |
|---|---|---|
| 작품 면적 | cm² | 100 × 80 = 8,000 |
| 작가 출생년 | 연도 | 1985 |
| 작가 총 작품수 | 정수 | 50 |

→ V3 (32 features) 대비 약 **1/10 입력 부담**.

### 5.2 라우팅 / 가드레일용 (예측 자체 X)

- 작가 학습 작품 수 (warm/cold 판정)
- medium / gallery_tier (가드레일 트리거)

---

## 6. 실험 코드 위치

```
experiments/structural_v1/
├── stage2_ols_hedonic.py            # Core 5 / Main 7 / Sensitivity 비교
├── stage2_feature_compare.py        # 6 set 비교
├── stage2_feature_extensive.py      # 22 set 확장 비교
├── stage2_career_age_test.py        # career_age 변형
├── stage2_advanced_tests.py         # Forward / Elastic Net / Interaction / Spline
├── stage2_final_candidates.py       # 최종 후보 검증
├── stage2_f4_validation.py          # F4 검증 4가지 (artist-CV / time / collapse / 잔차)
├── stage3_mixed_effects.py          # ME random intercept (cold-start 무력화 확인)
├── stage3_warm_calibration.py       # Warm-start + Calibration + 이원 전략
├── stage3_final_validation.py       # Time-split / warm threshold / drift
├── stage3_extra_validation.py       # Bootstrap / per-segment / sensitivity
├── stage3_p1_improvements.py        # P1: Spline / Interaction / Ridge / 전체 모집단
├── stage3_p2_robust.py              # P2: Huber / Weighted / Transform / Smearing
├── stage3_huber_tuning.py           # Huber eps/alpha + Winsorization + 100-seed
└── stage3_huber_validation.py       # Huber B 검증 (Bootstrap CI / per-segment / coef)

results/
├── stage2_*.json                    # Stage 2 실험 결과 (7개 JSON + 3개 coef CSV)
└── stage3_*.json                    # Stage 3 실험 결과 (8개 JSON)
```

데이터 생성: `scripts/build_curated_datasets.py`
검증: `scripts/verify_stage1_rules.py`

---

## 7. 데이터 위치

```
data/curated/
├── stage1_200x20.{parquet,csv}       # 데이터 규칙 검증용
├── stage2_500x50.{parquet,csv}       # OLS hedonic 1차 fit (실제 500/50)
├── stage3_1000x100.{parquet,csv}     # ME / 검증용 (파일명은 plan 명명, 실제 1,378 records / 100 artists)
├── stage_summary.json                # 단계별 통계 요약
└── stage1_verification_report.json   # 규칙 검증 리포트
```

---

## 8. 코덱스 자문 이력 (전체 11회 / 핵심 의사결정 6회 + 운영 도입 5회)

| 회차 | 주제 |
|---|---|
| 1차 | Stage 2 1차 fit 결과 (Core 5 winner) |
| 2차 | Forward selection (F4 채택) |
| 3차 | F4 검증 4가지 (옵션 A 결정) |
| 4차 | Stage 3 ME (옵션 A + 후처리 보정) |
| 5차 | Final 4 검증 (min_works_10 + 단계적 도입) |
| 6차 | Extra validation (Final report 진입 통과) |
| 7차 | P1+P2 추가 개선 (spline + Huber) |
| 8차 | Huber 튜닝 + Winsorization (최종 채택) |
| 9차 | Huber B 검증 (취약 segment 방어력) |
| 10차 | Production 통합 spec v1 (조건부 도입) |
| 11차 | Production spec v2 (Phase A 승인) |

모든 review **통과** ✅.

---

## 9. 한계 / 잔존 위험

| 항목 | 대응 |
|---|---|
| 표본 차이 (학습 1.3K vs 운영 28K) | Phase A shadow + D+7 actual linkage |
| Cold-start ME 무력화 | OLS + spline + Huber 사용 (운영 채택) |
| Calibration 시간 drift | 월 1회 재학습 |
| 신규 입력 채널 | default-off + 100건 shadow 후 활성화 |
| 가드레일 segment (저가 / ink / tier 3) | 자동 alert + 사람 검토 |

상세: 최종보고서 §6, Production spec §13.

---

## 10. 다음 액션

| 우선순위 | 작업 | 담당 | 기간 |
|---|---|---|---|
| 1 | Production spec 검토 + 승인 | 의사결정자 | 1-2일 |
| 2 | 라우팅 + 가드레일 + fallback 코드 구현 | 개발 | 3-5일 |
| 3 | 학습-서빙 parity 검증 | QA | 1-2일 |
| 4 | Phase A shadow 배치 | 운영 | 2-3일 |
| 5 | 5% canary 시작 | 운영 + 승인 | 즉시 |
| 6 | 단계 확대 (10% → 25%) | 운영 + 승인 | 점진 |
| 7 | (선택) 트랙 1 검증 시작 | 분석 | 별도 |

---

## 11. 핵심 메시지 (조직 공유용)

> **"3개 변수 + 면적 spline + Huber loss 로, V3 의 신규 작가 약점을 안전하게 보완.
> 운영상 가장 위험한 저가/고가/tier 3 segment 의 오차도 구조적으로 줄였습니다.
> 통계적 유의성 + 계수 안정성 + 부호 일관성 모두 입증.
> Phase A shadow 착수 승인 가능 수준."**

---

## 12. 참조 (전체 산출물 목록)

### 12.1 핵심 8종 (트랙 2 산출물)

| 카테고리 | 파일 |
|---|---|
| 1. 임원 1페이지 | `docs/임원보고_트랙2_요약_20260506.html` |
| 2. 일반 설명 | `docs/트랙2_쉬운설명_20260506.html` |
| 3. 비전공 프로세스 | `docs/트랙2_프로세스_쉬운버전_20260506.html` |
| 4. 최종 결과 보고서 | `docs/트랙2_최종보고서_20260506.md` |
| 5. 수식 + 절차 | `docs/트랙2_수식_프로세스_상세_20260506.html` |
| 6. Production 통합 spec | `docs/트랙2_production_통합_spec_20260507.md` |
| 7. 데이터 plan | `docs/데이터클렌징_단계계획_20260506.md` |
| 8. Stage 2 freeze 메모 | `docs/트랙2_Stage2_freeze_20260506.md` |

### 12.2 참고 (외부 / 통합 문서)

| 카테고리 | 파일 |
|---|---|
| **본 문서 (인덱스)** | `docs/트랙2_README.md` |
| 일정 (1개월 plan) | `docs/1개월_병행일정_V5_Structural.html` |
