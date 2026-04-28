# VisionAI 1차 시장 가격 예측 모델 기술 보고서 v2

> **작성일**: 2026-04-28
> **모델 버전**: v3-tuned-cal (`integrated_v3_filtered_tuned` + cell calibration)
> **학습 데이터**: 28,376건 (29,361건에서 입체/3D 985건 제외) / 1,551명 작가 (warm 930명, ≥5건)
> **대상**: 한국 회화 작품의 1차 시장(갤러리) 가격 예측
>
> **⚠ 본 문서의 위치**: v1 보고서([`model_technical_report.html`](model_technical_report.html))의 **개선 후속편**. v1의 이론·아키텍처 본문은 그대로 유효하며, 본 문서는 2026-04-07~28 사이 협력자 피드백 24건(기술보고서 10건 + 실험계획서 14건) → 4건의 모델 PR(#19·#20·#21·#22) → **32회 코덱스 리뷰**를 거쳐 적용된 **변경 사항·실험·실패한 시도**를 자세히 정리한다. 처음 읽는 독자는 v1을 먼저 보고 본 문서로 이어 보길 권한다.
>
> **📌 범위**: 1차 시장 예측 모델(A, `primary_predictor` + `integrated_v3_filtered_tuned_*`) 전용. 경매 낙찰가 모델(B)은 별도 문서.
>
> **📐 명칭 표기 정책**: 협력자 피드백 Q9(2026-04-24)에 따라 작가 분류 시 "신진/중견/원로" 같은 시장 통념적 라벨은 사용하지 않는다. 모든 분류는 **수치형 점수(`career_stage` 0~8)** 또는 **운영 등급(A/B/C/D)** 으로만 표기한다. 본 문서 본문도 같은 정책을 따른다.
>
> **출처(Provenance)**: 본 문서가 인용하는 모든 수치는 머지된 산출물 기준이다.
> - 핵심 metrics: [`model_test_results/integrated_v3_filtered_tuned_metrics.json`](../model_test_results/integrated_v3_filtered_tuned_metrics.json)
> - 셀 캘리브레이션: [`model_test_results/integrated_v3_filtered_tuned_source_calibration.json`](../model_test_results/integrated_v3_filtered_tuned_source_calibration.json)
> - 등급 마진: [`model_test_results/grade_margin_calibration.json`](../model_test_results/grade_margin_calibration.json)
> - 워밍 작가 셋: [`model_test_results/integrated_v3_filtered_tuned_warm_artists.json`](../model_test_results/integrated_v3_filtered_tuned_warm_artists.json) (930명 / 27,062건)
> - 갤러리 티어 매핑: [`model_test_results/gallery_tier_coverage_report.md`](../model_test_results/gallery_tier_coverage_report.md)

---

## 0. 한 문단 요약

협력자가 v1 모델에 던진 24개 질문(기술보고서 10건 + 실험계획서 14건)을 **데이터로 검증**한 결과, "단순 피처 추가"보다 **train/serve 정합**이 더 큰 병목임이 드러났다. 4건의 PR로 (1) `career_stage`를 사문화 분기에서 **연속 0~8 다요인 점수**로 재설계(라벨은 수치형으로만), (2) **학습엔 분포가 있지만 서빙엔 0으로 하드코딩되던 5개 피처(drift)**를 모델에서 제거, (3) `source × target_market` 셀 단위 **교차 검증 캘리브레이션**(per-cell guard)으로 cold path MdAPE를 39.4 → 38.3%로 끌어내리고, (4) `source` 정규화·등급 마진 production-time 재캘리브레이션으로 **A 등급 9.8% / warm Artsy 8.3%** 를 달성했다. 코덱스 리뷰 **32회**가 평가-라우팅 불일치·cross-fit leakage·폴드 멤버십 어긋남 같은 잡음을 차단했다.

---

## 1. v1 → v2 핵심 지표 변화

> **읽는 법**: v1 라인은 `integrated_v3_metrics.json` (29,361건 전체 학습), v2 라인은 `integrated_v3_filtered_tuned_metrics.json` (입체 985건 제외 후 28,376건, Optuna n_trials=30 튜닝, cell calibration 적용)을 옮긴 것이다.

| 지표 | v1 (2026-04-17) | v2 (2026-04-28) | Δ |
|---|---:|---:|---:|
| 피처 수 (모델 입력) | 37 | **32** | -5 (drift 제거) |
| 학습 건수 | 29,361 | 28,376 | -985 (입체 제외) |
| Warm 작가 (≥5건) | 명시 안됨 | **930명 / 27,062건** | 라우팅 정합 확보 |
| **Warm 전체 MdAPE (KFold)** | 11.7% (XGB) / 17.1% (CB) | **9.7% (XGB) / 11.9% (CB) / 10.5% (앙상블)** | -2.0%p (XGB) |
| Warm Artsy MdAPE (KFold) | 명시 안됨 | **8.3% (XGB) / 8.7% (앙상블)** | A 목표(8%) 도달 |
| **Cold 전체 MdAPE (GroupKFold)** — production path = CatBoost | 38.9% (CB) / 39.4% (XGB) | **CatBoost 39.4% (보정 전) → 38.3% (보정 후, cross-fit guarded)** | -1.1%p |
| Cold 전체 — offline ensemble (참고용, production 경로 아님) | — | 38.7% | — |
| Cold Artsy MdAPE — offline ensemble (참고용) | ≈40% | 33.2% (앙상블) | -7%p |
| Production-time A 등급 MdAPE | 보고 없음 | **9.8%** | 신규 측정 |
| Source 보정 방식 | 단일 상수 -0.075 (online) | **셀별 ratio (artsy_online=0.943, saatchi_online=0.957)** | per-cell guard 도입 |

**해석**: 단일 매개변수 보정에서 **source × target_market 셀별 보정**으로 갈아탔다. **production cold path는 CatBoost 단일 경로**이므로 보정 전후 비교는 CatBoost OOF 기준(`source_calibration.json` `cold_overall`): 39.38 → 38.29 (-1.09%p, cross-fit guarded). 앙상블/Artsy 슬라이스 수치는 offline 비교용이며 운영 경로와 다르므로 별도 표기. **artsy_gallery 셀은 cross-fit에서 보정이 회귀를 일으켜 factor=1.0 (skip)** — 자동 가드로 안정성 확보.

---

## 2. 협력자 피드백 24건 → 모델 변경 매트릭스

협력자 피드백은 두 차례에 걸쳐 들어왔다.
1. **2026-04-07~08 실험계획서 피드백 14건** ([`실험계획서_피드백_답변.md`](실험계획서_피드백_답변.md)) — 모델 설계 단계
2. **2026-04-24~26 기술보고서 피드백 10건** ([`기술보고서_피드백_답변_20260427.md`](기술보고서_피드백_답변_20260427.md)) — production 모델 평가 단계

본 v2는 이 24건이 어떻게 처리됐는지를 트레이서빌리티 표로 정리한다.

### 2.1 기술보고서 피드백 10건 (Q1~Q10)

| # | 협력자 질문 (요약) | 데이터 검증 결과 | 적용된 변경 | PR |
|:-:|---|---|---|:-:|
| Q1 | "profile_completeness 8.41%는 운영 정책에 반영해야" | 사실 — 프로필 충실도가 작가 전문성 프록시 | 운영 가이드 작성 의제로 분리 (모델 변경 없음) | (운영) |
| Q2 | "갤러리 티어 v3 리스트 89개 공유. 모델에 반영해달라" | Artsy 갤러리 66개 중 11개만 매칭 (13.2%) | **PR #19에서 매칭 분석 → Top 30 미매칭 명단 산출** | #19 |
| Q3 | "원작/에디션 0.00% 중요도는 데이터 편향 의심" | 99.9% Unique (Saatchi=100%, Artsy=99.5%, Edition=34건/0.1%) | 분산 부족 → printbakery 별 모델로 분리 검토 | (정책) |
| Q4 | "한국 갤러리 직접 등록 작가는 어떻게 처리?" | Cold path (CatBoost) 분기 + manual_overrides API 존재 | Cold-start 데이터 보강(갤러리 입력 UX) — 운영 협조 의제 | (운영) |
| Q5 | "외부 플랫폼 등록 작품수는 시장 활동 0.2%만" | 사실 — `artist_total_works`는 온라인 활동성 + 데이터 소스 식별 시그널 혼합 | 갤러리 직접 입력 데이터 수집 의제 | (운영) |
| Q6 | "플랫폼은 Artsy + Saatchi만?" | v3-filtered-tuned 기준 정확히 두 개. printbakery/Artue/manual은 카테고리 슬롯만 | 보고서 정정. v2 본문 §3 명시. | (문서) |
| Q7 | "C/D 가격 범위 너무 넓음 (50%/70%)" | A 등급 m=0.20에서 80% 커버리지 71.5% (좁음) | **PR #22 production-time m 권장치 산출** (적용은 정책 결정) | #22 |
| Q8 | "개인전/단체전 직접 피처에 있나?" | `solo_count`/`group_count`/`fair_count`는 학습 데이터에 컬럼은 있지만 모델 입력 37개에 미포함 | **PR #20에서 `career_stage_v2_score` 입력으로 통합** (직접 피처화는 v4 실험에서 과적합 사례 있어 보류) | #20 |
| Q9 | "career_stage 명칭 변경. 신진/중견/원로 같은 시장 통념 라벨 부적절" | Stage 3=0건으로 사문화. 명명도 시장 합의 없음 | **PR #20에서 v2 정의(연속 0~8 점수) 도입 + 라벨 수치형으로 통일** | #20 |
| Q10 | "갤러리 유형/서울 가중치/해외 갤러리 합리성" | 단순 휴리스틱(`has_seoul`, `has_international` 등 합 2.5%) | PR #19 갤러리 티어 분석 + Phase 1B(협력자 검수 대기) | #19 |

### 2.2 실험계획서 피드백 14건 (P-Q1~P-Q14)

| # | 협력자 제안 | 처리 |
|:-:|---|---|
| P-Q1 | "Career Age 추가 (첫 개인전 후 경과 연수)" | 초안에 포함 → 학습/서빙 drift 발견(서빙은 0 하드코딩, DB 스키마 컬럼 없음) → **PR #20에서 제거**. age는 birth_year 기반 `age_score`만 유지. |
| P-Q2 | "전시 갤러리 티어 가중 합산 (국제갤러리 vs 카페갤러리)" | PR #19 갤러리 티어 v3 분석에 반영. 협력자 리스트 매칭 11/66, Phase 1B 대기. |
| P-Q3 | "1호 작품 점당 가격 (호당가 아님)" | 작가별 소품 케이스. v1 `is_small` 피처(중요도 0.73%)로 부분 반영. 향후 작가별 점당가 룩업 도입 검토. |
| P-Q4 | "3호 미만 = 10호 가격의 50~60%" | v1 `support_factor` + `ho_x_support` 교차항으로 일부 반영. 명시 룩업은 미반영. |
| P-Q5 | "F/P/M/S 호수 변환 면적 차이" | v1 면적 → F형 호수 매칭(24개 표준 캔버스). aspect_ratio로 타입 추정 가능하나 미반영. |
| P-Q6 | "지지체(canvas/paper) + 유니크/에디션 구분 필수" | `support_factor` 5단계 + `is_unique`/`is_edition` 피처. 단 99.9% Unique로 분산 부족(Q3). |
| P-Q7 | "서울옥션 크롤러 활용?" | B 모델(경매 낙찰가) 영역. 본 1차 시장 모델은 갤러리 데이터 전용. |
| P-Q8 | "갤러리 명성 ↔ 가격(+) 한국 시장 방향" | v1 보고서 §2.3에 한국 시장 맥락 추가. PR #19에서 갤러리 티어 매칭 분석. |
| P-Q9 | "전시 갤러리/아트페어 티어" | Q2/Q10과 동일 — 갤러리 티어 v3 Phase 1B에 통합. |
| P-Q10 | "서울옥션 크롤러" | P-Q7과 동일. |
| P-Q11 | "비평(전문가 평가) 정량화" | Phase 2+ 의제. 본 v2 미반영. |
| P-Q12 | "김윤신 1명 작가 편향" | 갤러리 데이터 확장 의제. v2 미반영. |
| P-Q13 | "작품 연식 × 경력 인터랙션" | v1 `vintage_premium`, `freshness_discount` 피처 시도 → **PR #20에서 train/serve drift로 제거**. |
| P-Q14 | "레지던시 선정 횟수" | 데이터 수집 미완. v2 미반영. |

---

## 3. PR #19 — 갤러리 티어 v3 매핑 분석 (Phase 1A, 1회 코덱스 리뷰)

### 3.1 배경

협력자(2026-04-26)가 갤러리/기관 티어 리스트 v3 (`data/art_gallery_tier_list_v3.xlsx`, 89개)를 공유. v1 모델의 `gallery_tier`는 도시 수·평균가·작품 수 휴리스틱(중요도 0.30%)이었기에 협력자 리스트로 대체 가능성을 탐색.

### 3.2 매핑 결과 (Artsy-only)

| 항목 | 값 |
|---|---:|
| 협력자 리스트 | 88개 |
| Artsy 학습 데이터 갤러리 | 66개 |
| 매칭된 갤러리 | **11/66 (17%)** |
| 매칭된 작품 | 965 / 7,289 (**13.2%**) |
| 미매칭 Top 30 | 5,937건 = 미매칭의 **93.9%** / Artsy 전체의 **81.5%** |

### 3.3 Tier 분포 (Default 매핑)

| Tier | n | % |
|:-:|---:|---:|
| Tier A | 0 | 0.0% |
| Tier B | 114 | 1.6% |
| Tier C | 851 | 11.7% |
| Tier D | 0 | 0.0% |
| Tier E (미매칭) | 6,324 | 86.8% |

### 3.4 가격 분리도 — Phase 1B 진행 여부의 결정적 지표

매칭률(13.2%)이 낮아도 매칭된 Tier가 가격을 의미 있게 분리하면 가치가 있다. 측정 결과:

| Tier | n | 중앙값 (KRW) | Q25 | Q75 | ln_std |
|:-:|---:|---:|---:|---:|---:|
| Tier B | 114 | 8,457,500 | 5.5M | 15.3M | 0.870 |
| Tier C | 851 | 3,864,000 | 1.7M | 9.6M | 1.320 |
| Tier E (미매칭) | 6,324 | 4,140,000 | 1.8M | 10.9M | 1.317 |

**해석**: Tier B vs C는 중앙값 2배 차이로 의미 있는 분리. Tier E (미매칭)와 Tier C는 중앙값이 거의 같아 분리도 약함 → **Top 30 미매칭 검수가 Phase 1B 효과의 결정적 변수**.

### 3.5 PR #19 결론 (분석 only)

- **매핑 13.2%만으로는 학습 적용 비추천** — Tier E가 86.8%로 사실상 단일 카테고리.
- **Top 30 미매칭 명단을 협력자에게 송부** → 검수 후 Phase 1B 진입 판정.
- 정확도 영향 0 (분석 PR). 다만 후속 PR의 의사결정 근거 제공.

### 3.6 코덱스 리뷰 1차 (1회 만에 GO)

- **차단 항목**: 초안에서 Saatchi 21,087건을 강제로 Tier E로 재코딩한 게 발견 → 가격 분리도가 인위적으로 부풀려진 상태였음. Saatchi는 별도 source로 분리 처리하도록 수정.
- 가격 분리도 측정을 별도로 추가(초안에는 매칭률만 있었음).

---

## 4. PR #20 — career_stage v2 + 5개 train/serve drift 제거 (15회 코덱스 리뷰)

### 4.1 출발: 액션 플랜 P0-2

[`MdAPE_개선_액션플랜_20260427.md`](MdAPE_개선_액션플랜_20260427.md)에서 두 가지 목표로 시작:
1. **개인전·페어 직접 피처화** (Q8) — `solo_count`/`group_count`/`fair_count`를 직접 모델 입력에 추가
2. **`career_stage` v2 재정의** (Q9) — 다요인 점수로 대체

진행하면서 **코덱스 리뷰가 단계적으로 더 본질적인 문제**(평가-라우팅 불일치, train/serve contract drift)를 발견 → PR 범위가 처음 의도보다 훨씬 커짐.

### 4.2 죽은 피처 발견: `career_stage` v1

v1 정의:

```
stage = 4: age ≥ 60 ∧ solo ≥ 5
stage = 3: solo ≥ 3
stage = 2: solo ≥ 1 ∨ group ≥ 5
stage = 1: otherwise
```

학습 데이터(28,376건) 실제 분포:

| stage (v1) | 건수 | 비율 |
|:-:|---:|---:|
| 1 | 14,205 | 50.1% |
| 2 | 14,156 | 49.9% |
| **3** | **0** | **0.0%** |
| 4 | 0 | 0.0% |

**원인**: `solo_count`/`group_count`가 학습 데이터에서 거의 비어 있음(Artsy shows 데이터 한계). 그 결과 stage=3 분기 조건(`solo ≥ 3`)이 만족되지 않아 사문화. 4단계 분류가 사실상 1↔2 binary로 압축. v1 보고서 importance 1.77%는 binary 신호에서 나온 것.

### 4.3 `career_stage` v2 — 연속 다요인 점수

실제 구현 ([`primary_feature_builder.py:48-82`](../src/visionai/price_engine/api/primary_feature_builder.py)):

```python
def career_stage_v2_score(birth_year, solo, group, fair, ln_followers, current_year=2026):
    score = 0.0
    # age_score: birth_year → 30+ 기준 + 12년당 +1, [0, 3] cap
    if birth_year and birth_year > 0:
        age = current_year - birth_year
        score += min(max((age - 30) / 12, 0), 3)
    # activity_score: solo + 0.7×fair + 0.3×group, log1p, cap 3
    activity = solo + 0.7 * fair + 0.3 * group
    score += min(math.log1p(activity), 3)
    # market_presence: ln_followers / 6, cap 2
    if ln_followers is not None:
        score += min(ln_followers / 6, 2)
    return score   # 최종: [0, 8]
```

**왜 합산인가**: 단일 분기는 한 축이 결측되면 0으로 무너진다. 합산은 **부분 신호도 살린다**. 예) 생년 없는 작가도 작품 수와 팔로워가 있으면 score>0.

**왜 연속값인가**: GBDT 트리가 임계값을 자유롭게 학습 → v1의 4단계처럼 분기가 사문화되지 않는다.

**왜 명칭이 수치형인가** (Q9 반영): "신진/중견/원로" 같은 시장 통념 라벨은 정의가 사람마다 다르고, 협력자 지적대로 나이 기준만으로는 시장 인식과 어긋난다 → **수치형 `career_stage` (0~8)** 만 노출. 운영 등급은 별도 A/B/C/D 체계 사용.

**`career_age`(첫 활동 연도 기반) 의도적 제외**: 초안 v2에는 `career_duration` 항이 있었으나 학습 데이터(`prepare_primary_market_dataset.py`)와 서빙 프로필(`artist_matcher.py`는 항상 0 고정, DB 스키마에 컬럼 없음) 간 drift → 코덱스 3차에서 제거하고 0~8 스케일 확정.

### 4.4 5개 피처 train/serve drift 제거

**증상**: 학습 데이터에는 분포가 있지만, `primary_feature_builder.build_features()`가 서빙 시 **상수(주로 0)를 하드코딩**하던 피처 5개. 모델은 분포를 가진 신호로 학습됐고, 서빙 시 모든 요청이 같은 값으로 들어가면서 **silent하게 다른 패턴을 적용**했다.

| 제거된 피처 | 카테고리 | 학습 데이터 | 서빙 시 값 | 모델 importance (XGB gain) | 근거 |
|---|---|---|---|---:|---|
| `career_age` | 작가 | `2026 - first_show_year` (Artsy 76% non-null, range 0~16) | 0 (DB에 컬럼 없음) | 2.03 | Codex 3차+4차 P1 |
| `work_age` | 작품 | `2026 - work_year` | 0 (요청에 미포함) | 0.40 | Codex 4차 P1 |
| `vintage_premium` | 갤러리/시점 | 학습 시 계산 | 0 | **1.53** | Codex 4차 P1 |
| `freshness_discount` | 갤러리/시점 | 학습 시 계산 | 0 | 0.19 | Codex 4차 P1 |
| `gallery_name` | categorical | 학습 vocab 59개 (예: "Kukje Gallery", "Gallery Hyundai") | `'Gallery'`/`'Saatchi Art'` 2개로 하드코딩 → 매번 sentinel | 0.5% (XGB warm) | Codex 14차 P1 |

37 → **32 피처**. 

**놀라운 발견**: 5개 drift 피처를 제거하니 metric이 **개선**됐다 (cold 40.6→39.4). 즉 학습한 신호가 서빙에서 활용 불가한 상태에서 노이즈로 작동하던 것 — production에선 도움이 되지 않거나 해를 끼치고 있었다.

**train/serve contract drift는 정확도 하락보다 더 위험하다**: 모델 정확도 그래프엔 안 잡히지만 production에서 **silent하게 다른 패턴을 학습**시킨다. 운영 후 디버깅 비용이 폭발한다.

(`solo_count`/`group_count`/`fair_count`/`followers` 등은 CB_FEATURES에 직접 들어가지 않고 **`career_stage_v2_score` 입력으로만** 사용한다 — 단일 점수로 합쳐지면 부분 결측 영향이 분산된다. Q8에서 협력자가 직접 피처화를 요청했으나 v4 실험(`integrated_v4_metrics.json`)에서 피처 46개로 늘렸을 때 MdAPE 38.7→40.4 악화 사례가 있어 압축 형태 유지.)

### 4.5 평가-라우팅 불일치 정렬 (Codex 1차 P1)

**문제**: v1 보고서까지는 ensemble MdAPE만 보고됐지만, 실제 서빙은:
- cold (`training_count<5`) → CatBoost only
- warm (`training_count>=5`) → XGBoost only

Ensemble 평균으로 의사결정하면 **잘못된 목표를 최적화**하게 된다.

**수정**: `cv_kfold` 결과에 by-source(Artsy/Saatchi) + warm_slice 메트릭 추가. 실제 서빙 라우팅과 동일한 조건의 MdAPE를 보고. `cv_kfold_warm`은 **warm-only로 학습/평가** (이전엔 full로 학습 후 warm subset 평가 — post-hoc).

### 4.6 Warm artist routing 정합

**문제**: `artist_matcher.py`는 DB의 `training_count` 컬럼으로 warm 판정 → 학습 시 fold-local 카운트와 불일치. 32명 작가가 production에서 잘못 라우팅됐다.

**수정**: 학습 파이프라인이 `integrated_v3_filtered_tuned_warm_artists.json`(930개 slug)을 산출 → 서빙은 이 JSON을 권위 있는 set으로 사용.

```python
# primary_predictor.py
WARM_ARTIST_SLUGS = load_warm_set(...)  # 930 slug
def is_warm_artist(slug): return slug in WARM_ARTIST_SLUGS  # 학습 정의와 1:1
```

### 4.7 `followers` 컬럼명 버그 (Codex 2차 P1)

**문제**: `prepare_primary_market_dataset.py:334` 가 `row.get("followers", 0)` 로 호출했지만 실제 컬럼명은 `artist_followers` 또는 파생된 `ln_followers`. v2 score의 `market_presence` 항이 학습 데이터에서 항상 0. Saatchi prepare는 정상이었고 Artsy만 영향.

**수정**: `row.get("ln_followers", 0.0)` 로 통일. `market_presence` 항이 정상 작동하기 시작.

### 4.8 그 외 코덱스 리뷰 15회에서 막은 잡음

| Codex 회차 | 발견 | 수정 |
|:-:|---|---|
| 1차 | 평가 ensemble vs 서빙 분리 라우팅 불일치 | by-source + warm-slice 메트릭 추가 |
| 1차 | `career_stage` v1 사문화 (Stage 3=0건) | v2 연속 점수 도입 |
| 2차 | `followers` 컬럼명 버그 | `ln_followers` 로 정정 |
| 2차 | train/tune 최종 XGB slice 불일치 (full vs warm) | 두 스크립트 다 warm-only로 정렬 |
| 3차 | `career_age` train/serve drift | v2 공식에서 제거, 0~8 스케일 |
| 3차 | XGB warm CV (full로 학습 후 warm 평가는 post-hoc) | warm-only로 학습/평가 분리 |
| 4차 | `career_age`가 `CB_FEATURES`에는 잔존 | CB_FEATURES에서 제거 |
| 4차 | `work_age`/`vintage_premium`/`freshness_discount` drift | 모두 제거 |
| 5차~12차 | label_maps fallback, categorical 정규화 비대칭, eval_set 누수, sentinel encoding 등 | 단계적 정정 |
| 13차 | `predict()` 런타임 mapping mutation 위험 | 학습 시 만든 sentinel 인덱스 그대로 사용 |
| 14차 | `gallery_name` vocab 59 vs 서빙 2개 hardcoded → 매번 sentinel | 피처 자체에서 제거 |
| 15차 | `model_version` 정적 `"v3"` 하드코딩 | `model_version_label()` 동적화 (calibration 로드 여부 반영) |

**공통 패턴**: 모델 정확도 그래프엔 안 잡히지만 production에서 silent하게 다른 패턴을 학습시킬 정합 문제. 단순 코드 리뷰로는 발견 어려움 — 학습 데이터 분포와 서빙 코드를 동시에 봐야 잡힌다.

### 4.9 PR #20 결과 요약

| 분할 | 모델 | n | MdAPE (PR #20 종착) |
|---|---|---:|---:|
| Cold 전체 | CatBoost | 28,376 | 39.4 |
| Cold Artsy | CatBoost | 7,289 | 33.3 |
| Cold Saatchi | CatBoost | 21,087 | 41.6 |
| Warm 전체 | XGBoost | 27,062 | 9.8 |
| **Warm Artsy** | XGBoost | 6,603 | **8.4** ← A 등급 8% 도달 |
| Warm Saatchi | XGBoost | 20,459 | 10.3 |

vs 직전 production: cold 40.6→39.4 (**-1.2%p**), warm 10.3→9.8 (**-0.5%p**).

---

## 5. PR #21 — Source × target_market 셀 캘리브레이션 (8회 코덱스 리뷰)

### 5.1 v1의 단일 상수 보정 한계

v1: `c = -0.075 if target_market=='online' else 0.0` — **모든 online을 같은 값으로** 보정.

문제: Artsy online과 Saatchi online은 분포가 다르다.

| 셀 | n | baseline MdAPE | v2 cross-fit calibrated MdAPE | 적용 factor |
|---|---:|---:|---:|---:|
| artsy_gallery | 868 | 24.3 | **24.3 (skip) ← guarded** | 1.0 |
| artsy_online | 6,421 | 35.0 | **34.1** | 0.943 |
| saatchi_online | 21,087 | 41.7 | **40.1** | 0.957 |

(MdAPE는 cold GroupKFold OOF, [`source_calibration.json`](../model_test_results/integrated_v3_filtered_tuned_source_calibration.json) `cold_breakdown` 기준.)

### 5.2 셀 정의

`cell = f"{source}_{target_market}"`. `target_market`은 `is_krw==1 → 'gallery'` (한국 갤러리), 그 외 → `'online'`. 학습 시점과 서빙 시점에 동일한 룰 적용.

가능한 셀:
- `artsy_gallery` (Artsy 데이터 중 KRW 표기) — 868건
- `artsy_online` (Artsy 데이터 중 USD/EUR/GBP 등) — 6,421건
- `saatchi_online` (Saatchi 데이터, 100% USD) — 21,087건
- `saatchi_gallery` — 0건 (Saatchi는 KRW 표기 거의 없음)

### 5.3 Cross-fit cell calibration with per-cell guard

```
factor[cell] = median(actual_price / predicted_price | cell)
```

**핵심 안전장치 3개**:

1. **Cross-fit (5-fold)** ([`scripts/calibrate_source_bias.py`](../scripts/calibrate_source_bias.py)): in-sample으로 factor를 추정하고 같은 데이터로 보정 → 평가가 부풀려진다. 따라서 train fold에서만 fit, OOF에서 평가.
2. **Per-cell guard**: cross-fit 평가가 baseline보다 **악화되는 셀은 `factor=1.0` 적용 (skip)**. `artsy_gallery`가 여기 해당:
   - baseline 24.3 < calibrated 31.2 → skip
   - 이유 추정: artsy_gallery는 KRW 표기 한국 1차 갤러리 작품 → 이미 모델이 잘 학습. 추가 보정이 오히려 오버슈트.
3. **Schema validation** ([`primary_predictor.py:233-262`](../src/visionai/price_engine/api/primary_predictor.py)): `version`/`model_target`/허용 셀 키 일치 확인. factor 값이 [0.1, 10.0] 범위 외이면 RuntimeError. 불일치 시 서버 시작 실패.

### 5.4 Production 적용 factor

```json
"cold_factors": {
  "artsy_gallery": 1.0,                  // skipped (regression cell)
  "artsy_online": 0.9425943416620021,    // -5.7%
  "saatchi_online": 0.9568847727800011   // -4.3%
}
```

**Cold 전체 효과** (`source_calibration.json` `cold_overall`): baseline **39.38** → calibrated cross-fit guarded **38.29** (-1.09%p).

**Warm은 보정 미적용**: warm path는 이미 작가 패턴이 학습됐기에 셀별 편향이 작다 (warm_factors 모두 1.0 근처: 0.99~1.005). `predict()` 함수에서 `not use_xgb and self._cold_calibration_factors:` 조건으로 cold path만 적용.

### 5.5 코덱스 리뷰 8회에서 막은 잡음

| 회차 | 발견 | 수정 |
|:-:|---|---|
| 1차 | In-sample evaluation (같은 데이터로 fit/eval) | cross-fit 5-fold 도입 |
| 2차 | source × target_market entanglement (단순 source factor만 추정) | 셀 단위로 분리 |
| 3차 | early stopping leakage 잔존 | 완전 제거, schema rsplit 정합 |
| 4차 | per-cell guard 부재 (회귀 cell 무조건 적용) | cross-fit 결과 보고 cell별 1.0 vs proposed 결정 |
| 5차 | True cross-fit guarded — guard cell selection이 같은 OOF 결과 보고 결정되어 post-hoc bias 잔존 | "production-time MdAPE"로 정정, caveat 명시 |
| 6차 | warm metric 계산 오류 | 정정 + OOS bias 명시 |
| 7차 | OOS bias caveat 산출물/스키마 미노출 | JSON `note` 필드에 명시 |
| 8차 | cell key parser 버그 (`split('_', 1)` → `"artsy_artue"` 잘못 분할) | `rsplit` 으로 수정 |

---

## 6. PR #22 — Source 정규화 + 등급 마진 production-time 재캘리브레이션 (8회 코덱스 리뷰)

### 6.1 source 결측값 정규화

`source` 등 categorical 피처가 서빙 시 `None`/`NaN`/`'None'`/`''`로 들어오면 학습 vocab 외 값이 되어 sentinel encoding으로 떨어졌다. 학습/서빙이 동일하게 처리되도록 **predictor에서 모든 CAT_FEATURES에 일괄 정규화** 적용 ([`primary_predictor.py:317-322`](../src/visionai/price_engine/api/primary_predictor.py)):

```python
for col in CAT_FEATURES:
    df[col] = df[col].astype(str).fillna("unknown").replace(
        {"nan": "unknown", "None": "unknown", "": "unknown"}
    )
```

추가로 cold calibration cell key 산출에서도 `source`만 동일 룰로 한 번 더 정규화 ([`primary_predictor.py:367-370`](../src/visionai/price_engine/api/primary_predictor.py)) — `cell = f"{src}_{target_market}"` 안정화. **`lower()`/`strip()`은 적용하지 않는다** (학습 vocab도 case-sensitive로 일관 유지).

### 6.2 등급 마진 production-time 재캘리브레이션

v1 마진은 **모델 OOS MdAPE**(38~39%)에서 도출 → 실제 라우팅된 등급별 분포와 어긋났다. 새로 production 라우팅·보정을 동일하게 재현하여 등급별 MdAPE를 측정.

새 절차 ([`scripts/calibrate_grade_margins.py`](../scripts/calibrate_grade_margins.py)):

1. **5-fold CV의 OOF 모델 weights**로 가격 예측.
2. 라우팅(`warm_artist_slugs.json`)과 cold 보정(`source_calibration.json` `cold_factors`)은 **production full-data artifacts** 그대로 사용.
3. 등급(A/B/C/D)을 production 함수로 부여, 등급별 |APE| 분포에서 80% 커버리지 m을 산출.

**caveat (스크립트 §해석 그대로)**: "OOF model weights + full-data routing artifacts" 결합 평가이므로 **순수 OOF는 아니며**, 운영 시 메트릭의 **추정치**로 해석한다. Routing/calibration artifact 자체의 OOS 일반화는 PR #20+#21 산출물에서 별도 평가됐다.

**production-time per-grade 결과** (n=28,376):

| 등급 | 정의 | n | MdAPE | 평균 APE | 현재 m | 현재 80% 커버리지 | 권장 m | Δ |
|:-:|---|---:|---:|---:|---:|---:|---:|---:|
| A | matched + warm artist (slug ∈ warm set) | 27,062 | **9.8%** | 19.7% | 0.20 | 71.5% | 0.286 | +0.086 |
| B | matched + warm 아님 (training_count≥1) | 1,006 | **29.7%** | 44.9% | 0.30 | 50.6% | 0.609 | +0.309 |
| C | unmatched + birth_year 또는 manual_profile 있음 | 128 | **39.0%** | 56.6% | 0.50 | 60.2% | 0.896 | +0.396 |
| D | unmatched + birth_year/manual_profile 모두 없음 | 180 | **43.6%** | 64.6% | 0.70 | 72.8% | 0.827 | +0.127 |

**해석**:
- **A 등급은 현재 m=0.20에서 71.5%만 커버** → 80% 커버리지를 위해선 m=0.286 필요. 현재 가격 범위가 좁게 표시되고 있다는 뜻 (사용자에게 신뢰도 낮은 약속).
- **B 등급은 현재 m=0.30에서 50.6%만 커버** — 절반 이상이 범위 밖. 권장 m=0.609로 두 배 가까이 넓어져야 함.
- **C/D는 m≈0.9** — 사실상 가격 범위 의미가 없을 정도로 넓어진다. 적용 여부는 정책 결정 사안 (사용자 신뢰도 영향).

**권장 m 적용은 보류 중** — 사용자 요청에 따라 적용 결정은 별도 정책 결정 후 진행 예정. 옵션:
- **옵션 1 (보수적 노출)**: A/B만 가격 범위 표시, C/D는 단일 참고가 + "정확도 낮음" 라벨, 또는 D는 미노출.
- **옵션 2 (정직한 범위)**: 권장 m 그대로 적용 → C/D는 ±90%대 → 사실상 무용.
- **옵션 3 (현재 유지)**: m을 안 바꾸고 coverage 부족을 알면서 노출.

### 6.3 코덱스 리뷰 8회에서 막은 잡음

| 회차 | 발견 | 수정 |
|:-:|---|---|
| 1차 | warm_set vs KFold slice 어긋남 (A/B 등급 폴드 멤버십 942건 차이) | warm slug JSON membership으로 통일 |
| 2차 | XGB train slice + production calibration factors 정합 미흡 | warm-only train + production guarded factor 적용 |
| 3차 | A 등급 matched 요구 누락 (factor leakage disclosure) | A는 matched + warm 둘 다 요구 |
| 4차 | wording 정리 ("실측" → production-time) + fail-closed validation | 일관 정정 |
| 5차 | calibration runtime 필수 + schema 검증 + "실측" 잔재 | 산출물에 caveat 명시 |
| 6차 | calibrate_grade_margins schema validator를 production과 동등화 | 동일 룰 적용 |
| 7차 | loaded vs empty 구분 (production 정합) | tuple 반환 `(data, loaded)` |
| 8차 | source 정규화 → cell key 안정화 | predict() 시 동일 룰 한 번 더 적용 |

---

## 7. 시도했지만 채택하지 않은 실험 (Negative Results)

정확도를 떨어뜨리거나 다른 비용이 컸던 실험. v1 보고서 §9.1과 액션 플랜에서 검증된 한계:

| 실험 | 결과 | 채택 여부 |
|---|---|---|
| **v4 — 피처 46개 확장** | MdAPE 38.7→40.4 (악화) | ❌ 과적합 — 피처 ≠ 정확도 |
| **v5 — 하이퍼파라미터 그리드 서치** | <0.5%p 개선 | ❌ 데이터가 병목, 튜닝은 한계 |
| **v6 — source별 분리 모델** (Artsy 모델 + Saatchi 모델) | 통합 모델 우수 | ❌ split 후 sample 반감으로 과적합. 액션 플랜 P1-2도 코덱스가 risky 평가 |
| **v6 — stacking** | 효과 없음 | ❌ 단일 GBDT가 충분 |
| **`career_age` 직접 피처** | XGB gain 2.03이지만 train/serve drift | ❌ DB 컬럼 없음 → drift |
| **`work_age`/`vintage_premium`/`freshness_discount`** | 학습 시 신호 있으나 서빙 0 하드코딩 | ❌ drift |
| **`gallery_name` 직접 피처** | 학습 vocab 59개 vs 서빙 2개 hardcoded | ❌ 매번 sentinel → drift |
| **5 카테고리 확장** (장르/스타일 등) | 계약 변경 위험 큼, -0.5%p 추정 | ❌ ROI 낮음 |
| **단일 상수 source 보정** (-0.075 ln) | 모든 online 동일 처리, 셀 분포 차이 미반영 | ❌ 셀별 보정으로 대체 (PR #21) |
| **In-sample calibration** | 평가 부풀려짐 | ❌ cross-fit으로 대체 |
| **개인전/페어 직접 피처화** | v4 실험에서 과적합 + warm 데이터 부족 | ❌ `career_stage_v2_score` 입력으로 통합 |

**시사점**: 1차 시장 가격 모델의 정확도 한계는 **모델 코드보다 데이터**에 있다. 액션 플랜의 큰 폭 개선 후보는 모두 협력자/운영 데이터 협조 의존(Phase 1B 갤러리 티어 검수, 갤러리 입력 UX, DB schema career_age 추가).

---

## 8. 최종 production 메트릭 (v3-tuned-cal)

> **측정 절차**: production 코드 경로 그대로 재현. `is_warm_artist`(930 slug JSON), source calibration cold factor, target_market 추론까지 동일.

### 8.1 Warm slice (KFold, 27,062건 / 930 작가, ≥5건)

| 분할 | 모델 | n | MdAPE | W30 | W50 |
|---|---|---:|---:|---:|---:|
| Warm 전체 | XGBoost | 27,062 | **9.7%** | 82.8% | 92.7% |
| Warm 전체 | CatBoost | 27,062 | 11.9% | 80.6% | 92.2% |
| Warm 전체 | 앙상블 | 27,062 | 10.5% | 82.4% | 92.7% |
| Warm Artsy | XGBoost | 6,603 | **8.3%** | 85.9% | 93.9% |
| Warm Artsy | 앙상블 | 6,603 | **8.7%** | 86.3% | 94.1% |
| Warm Saatchi | XGBoost | 20,459 | 10.3% | 81.9% | 92.3% |
| Warm Saatchi | 앙상블 | 20,459 | 11.1% | 81.2% | 92.3% |

**A 등급 8% 목표**: warm Artsy XGB 8.3% / 앙상블 8.7%로 사실상 도달. (A 목표는 "warm Artsy" 슬라이스 정의에서 8.0~9.0% 밴드.)

### 8.2 Cold slice (GroupKFold, 28,376건 / 1,551 작가)

> **production cold path = CatBoost 단일 경로**. 따라서 보정 전후 비교는 CatBoost OOF 기준이며 (`source_calibration.json` `cold_overall`), 앙상블/소스 슬라이스는 offline 비교 참고용이다.

| 분할 | 모델 | n | MdAPE | 비고 |
|---|---|---:|---:|---|
| **Cold 전체 (production path)** | **CatBoost (보정 전)** | 28,376 | **39.4%** | `cold_overall.baseline_mdape=39.38` |
| **Cold 전체 (production path)** | **CatBoost + cell calibration (cross-fit guarded)** | 28,376 | **38.3%** | `cold_overall.calibrated_mdape_cross_fit_guarded=38.29` (-1.09%p) |
| Cold 전체 — offline only | XGBoost | 28,376 | 39.1% | production cold path 아님 |
| Cold 전체 — offline only | 앙상블 | 28,376 | 38.7% | production cold path 아님 |
| Cold Artsy — offline only | 앙상블 | 7,289 | 33.2% | 슬라이스 비교 참고용 |
| Cold Saatchi — offline only | 앙상블 | 21,087 | 41.1% | 슬라이스 비교 참고용 |

### 8.3 Production-time grade MdAPE

위 [§6.2](#62-등급-마진-production-time-재캘리브레이션) 표 참조.

### 8.4 정직성 — 메트릭이 "진짜"인가

**학습/서빙 contract 정합 완료** (PR #20+#21+#22 효과):
- ✅ feature drift 5건 제거 (career_age, work_age, vintage, freshness, gallery_name)
- ✅ warm 라우팅 학습/서빙 동일 (`warm_artist_slugs.json` 권위)
- ✅ source calibration 학습 시점 fit, 서빙 적용 일관
- ✅ categorical 정규화 학습/서빙 동일

**잔존 post-hoc bias** (코덱스 검증·문서화):
- ⚠️ Cross-fit calibration: factor 추정은 OOF지만 **guard cell selection은 동일 OOF 결과 보고 결정** → post-hoc selection bias 잔존.
- ⚠️ Production-time MdAPE: 모델 OOF + full-data routing/calibration artifact → 순수 OOF 아님.
- 결론: **38.3% / 9.7%는 보수적 추정치**. 실제 production 정확도는 그 이상일 수도.
- 추가 검증 필요시: nested CV (outer fold guard 결정, inner fold factor 추정) — 미시행.

---

## 9. 32회 코덱스 리뷰가 막아낸 것 (요약)

| PR | 코덱스 회차 | 핵심 차단 항목 |
|:-:|:-:|---|
| #19 | 1회 | Saatchi 강제 Tier E 재코딩 (가격 분리도 부풀림 방지) + 가격 분리도 측정 추가 |
| #20 | **15회** | 평가-라우팅 불일치, career_stage v1 사문화, 5개 train/serve drift 피처(career_age/work_age/vintage_premium/freshness_discount/gallery_name), followers 컬럼명 버그, train/tune slice 정렬, warm artist routing JSON, label_maps fail-closed, categorical 정규화 비대칭, sentinel encoding, model_version 동적화 |
| #21 | 8회 | in-sample calibration, source × target_market entanglement, per-cell guard, true cross-fit guarded wording, schema validation, cell key parser 버그 |
| #22 | 8회 | warm_set 폴드 멤버십 942건 차이, calibration factor leakage, schema parity, "실측" → "production-time" wording, empty artifact 분리 |
| #23·#24 | 1회 | 문서 정합 |

**공통 패턴**: 모델 정확도 그래프엔 안 잡히지만 production에서 silent하게 다른 패턴을 학습시킬 train/serve 정합 문제. 32회 리뷰 없이 머지됐다면 metrics는 그대로 38~39%였을 것이고, 운영 중 디버깅 비용이 폭발했을 것.

**코덱스 기여 핵심 발견** (사람 리뷰만으로는 잡기 어려움):
- PR #19: ratio 분리 평가 (Saatchi 강제 Tier E 폐기)
- PR #20: career_age 학습/서빙 드리프트, gallery_name vocab mismatch, label_maps fail-closed
- PR #21: cross-fit leakage, source × target_market entanglement, per-cell guard
- PR #22: warm artist set vs train_count, factor in-sample bias, 빈 artifact vs missing 구분

→ **코덱스 없었다면 38.9% 메트릭은 misleading**이었을 것. 학습/서빙 드리프트로 실제 production은 다른 수치였을 것이고, 디버깅 후 metric은 더 악화됐을 가능성이 크다.

---

## 10. 알려진 제약·잔존 협조 사항

본 v2 모델이 **여전히 해결하지 못하는 것**과 후속 협조 필요 항목 ([`docs/협조_필요사항_정리_20260428.md`](협조_필요사항_정리_20260428.md) 전체 12건 중 핵심 6건):

1. **Cold-start MdAPE 38%대 수렴** (모델 한계): 생년 결측 72%, 고가 1,678건(5.7%), 신규 작가 외부 수집 정확도 한계 — 데이터 구조적 한계로 모델만으론 추가 개선 어려움.
2. **DB schema 마이그레이션** (운영 협조): `artist_profiles.career_stage`가 INT(1..4) CHECK 제약 — career_stage v2(연속 0~8)와 충돌. 현재는 학습/서빙이 JSON으로 우회 중. 또한 `career_age` 컬럼 신설 시 신호 회복 가능.
3. **갤러리 티어 v3 매칭 81% 미해결** (협력자 협조): Artsy 갤러리 66개 중 11개만 협력자 리스트와 매칭. PR #19 Top 30 미매칭 명단(영문명+한글 추정) 검수 필요 — 완료 시 Phase 1B에서 갤러리 등급 신호 회복(예상 -1~2%p A 등급 MdAPE 개선).
4. **Cold-start 자동 수집 강화** (운영 협조): 한국 갤러리 사이트 크롤링 추가, 5단계→7단계 필터로 정확도 향상. C/D 등급 인구 감소 + MdAPE 41~43% → 30~35% (5~10%p) 가능.
5. **PredictRequest에 optional `gallery_name`/`gallery_type` 추가 + 모델 재학습**: `gallery_name`은 v2 모델에서 **이미 제거**된 상태이므로 API 필드만 추가해도 신호가 살아나지 않는다. 회복하려면 (a) PredictRequest 스키마 추가, (b) feature builder에 `gallery_name` 재도입, (c) 모델 재학습이 모두 필요. `gallery_type`은 현재도 모델 입력이지만 서빙 vocab이 좁아 효과 제한적.
6. **m 값 정책 결정**: 권장치 적용 시 C/D는 m≈0.9 — 가격 범위 표시 정책 변경 영향 검토 필요. 옵션은 §6.2 참조.

---

## 11. 운영 변경 사항 (v1 대비)

### 11.1 모델 아티팩트 5종 (Dockerfile.api COPY 대상)

```
model_test_results/
├── integrated_v3_filtered_tuned_catboost.cbm
├── integrated_v3_filtered_tuned_xgboost.json
├── integrated_v3_filtered_tuned_xgboost_label_maps.json    # mandatory
├── integrated_v3_filtered_tuned_warm_artists.json          # 930 slug
└── integrated_v3_filtered_tuned_source_calibration.json    # cell factor
```

**fail-closed**: 5개 중 1개라도 누락·schema 불일치 시 서버 시작 시점에 `RuntimeError`. v1은 partial 로드 후 잘못된 예측을 침묵으로 반환할 수 있었음 — v2에서 차단.

### 11.2 model_version 동적화

```python
# primary_predictor.py
def model_version_label(self, base: str = "v3-tuned") -> str:
    if self._cold_calibration_factors:
        return f"{base}-cal"   # calibration JSON 로드된 경우만
    return base                # uncalibrated 상태도 거짓 보고하지 않음
```

v1은 하드코딩된 `"v3"` — 모델 업데이트 시 코드 수동 갱신 필요했음. v2는 **실제 로드된 artifact 기반**으로 라벨 산출 (calibration 누락 시 `v3-tuned`, 로드 시 `v3-tuned-cal`).

### 11.3 라우팅 경로 (변경 없음 + 명시화)

```
입력 → ArtistMatcher.match() → slug
       │
       ├─ slug ∈ WARM_ARTIST_SLUGS (930)?
       │   ├─ Yes → XGBoost (32 피처, label-encoded categorical)
       │   └─ No  → CatBoost (32 피처, native categorical)
       │
       └─ predict() 후 cold path만 cell calibration 적용
              (cell = source × target_market, factor JSON 참조)
```

### 11.4 grade 결정 (warm artist tri-state)

```python
# determine_confidence (primary_predictor.py:52)
# is_warm_artist: True / False / None (warm set 미로드 시)
if is_warm_artist is True and is_matched:  return ("A", 0.20)
if is_warm_artist is False:
    if is_matched and training_count >= 1:  return ("B", 0.30)
    if has_birth_year or has_manual_profile: return ("C", 0.50)
    return ("D", 0.70)
# is_warm_artist is None: 구 legacy fallback (training_count >= 5 → A)
```

PR #20 Codex 6차에서 발견: warm set 외부 + DB training_count≥5인 작가가 CatBoost+A 모순 발생할 수 있어 tri-state로 분리.

---

## 12. 한 줄 요약

> **v2 모델은 학습 작가의 작품 가격을 평균 9.7% 오차(warm Artsy는 8.3%)로 예측한다. 신규 작가는 38.3% 오차 — 데이터 부족으로 본질적 한계. 다음 큰 개선은 모델이 아니라 협력자 갤러리 정보 수집·DB schema 정합·갤러리 입력 UX에 달림.**

---

## 13. 참고 문서

### 협력자 피드백
- [`실험계획서_피드백_답변.md`](실험계획서_피드백_답변.md) — 2026-04-07~08, 14건 (모델 설계 단계)
- [`기술보고서_피드백_답변_20260427.md`](기술보고서_피드백_답변_20260427.md) — 2026-04-24~26, 10건 (production 평가 단계)

### v1 본문 (이론·아키텍처·SHAP)
- [`model_technical_report.html`](model_technical_report.html) — v1 보고서

### 액션 플랜·실행 기록
- [`MdAPE_개선_액션플랜_20260427.md`](MdAPE_개선_액션플랜_20260427.md) — 액션 매트릭스(P0~P3)
- [`PR20_요약_및_코덱스리뷰_여정_20260428.md`](PR20_요약_및_코덱스리뷰_여정_20260428.md) — PR #20 15회 리뷰 여정 상세
- [`예측정확도_종합리포트_20260428.md`](예측정확도_종합리포트_20260428.md) — 정확도 시작점→현재 비교
- [`협조_필요사항_정리_20260428.md`](협조_필요사항_정리_20260428.md) — 협력자/운영/정책 협조 12건

### 산출물 (수치 출처)
- `model_test_results/integrated_v3_filtered_tuned_metrics.json` — 핵심 metrics
- `model_test_results/integrated_v3_filtered_tuned_source_calibration.json` — cell calibration factor
- `model_test_results/grade_margin_calibration.json` — production-time 등급별 m
- `model_test_results/integrated_v3_filtered_tuned_warm_artists.json` — warm 930 slug
- `model_test_results/gallery_tier_coverage_report.md` — PR #19 매핑 분석

### 머지된 PR
- PR #19 (`52a0315`) — 갤러리 티어 v3 매핑 분석
- PR #20 (`71b363e`) — career_stage v2 + drift 정리
- PR #21 (`e1d033d`) — source × target_market 셀 캘리브레이션
- PR #22 (`6f47ec2`) — source 정규화 + grade margin 재캘리브레이션
- PR #23 (`4a3588a`) — 협조 필요 사항 문서화
- PR #24 (`cfce8a6`) — 정확도 종합 리포트

---

## 14. 변경 이력

- **2026-04-28 (v2 1차)** — career_stage v2, 5개 drift 피처 제거, source × target_market 셀 캘리브레이션, 등급 마진 production-time 재산출 반영. 32회 코덱스 리뷰 소화 후 머지된 산출물 기준.
- **2026-04-28 (v2 2차)** — 명칭 정책 반영(Q9: "신진/중견/원로" 라벨 제거 → 수치형 `career_stage` 0~8 + 운영 등급 A/B/C/D만 사용). 협력자 피드백 24건(기술보고서 10 + 실험계획서 14) 트레이서빌리티 표 추가. PR #19 갤러리 티어 분석, 코덱스 리뷰 회차별 발견 항목 상세, negative results 표 추가.
