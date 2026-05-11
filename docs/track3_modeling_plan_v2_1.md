# Track 3 — 가격 예측 모델링 Plan v2.1

**작성일**: 2026-05-11
**작성자**: Bo + Claude
**검수**: Codex R1 (v1) + R2 (v2) + R3 (v2.1) 통과
**Status**: ✅ Phase 0 진행 가능 (Codex R3 통과)

---

## 변경 이력 (v2 → v2.1)

Codex R2 fix 8건 + R3 추가 지적 12건 반영:
1. **outer holdout 위치 제한** — 최초 1회 격리 + Phase 5 최종 1회 (Phase 0~4 모델 선택은 5-fold GroupKFold OOF만)
2. **Cold "25 runs" 정의 명확화** — GroupKFold deterministic이므로 `고정 5-fold × 모델 seed 3회 = 15 runs`
3. **Price-band 용어 수정** — "분위수" → "business-defined fixed bands (고정 가격 구간)"
4. **"Mixture-of-experts" 재명명** — learned gating 아님 → **"Segmented experts"** (regime-specific)
5. **3-way 운영 라우팅** — Warm (≥3건) / Blend (1-2건) / Cold (unseen)
6. **Source-balanced weighting stress test** — inverse-frequency weight with cap (downsampling 아님) — Phase 5 체크리스트
7. **Conformal coverage 분해 보고** — source × price-band 12 셀 (3 × 4)
8. **Phase 4.5 조건부 trigger** — B4 median APE >50% 또는 **>100M median APE >70%** (mean→median, R3 권장)
9. **listing-price prediction caveat 강화** — "시장가치 예측 아님" 못 박기
10. **실제 데이터 통계 명시** — singleton 299 / ≤2건 516 / >100M 925건 / >10M 작가 844명
11. **Blend 비율 산출 — artist-weighted 24.2% + listing-weighted 1.83%** 둘 다 명시 (R3 권장)
12. **Phase 4.5 "선택" → "조건부 실행"** 표기 변경

---

## 1. 목표

### Primary (cold-start)
**학습되지 않은 신규 작가의 신규 작품에 대한 예측 정확도 향상**
- 시나리오: 처음 보는 작가가 새 작품을 올릴 때 가격 추정
- 데이터 조건: `artist_name_ko` 없음 (모름) → **artist-agnostic feature**만으로 예측

### Secondary (warm-start)
**학습된 작가의 신규 작품 예측 정확도 향상**
- 시나리오: 이미 등록된 작가의 새 작품 가격 추정
- 데이터 조건: `artist_name_ko` 사용 가능 → artist FE / target encoding 활용

### 운영 시점 라우팅 (3-way)

운영 환경에서 들어온 작품의 `artist_name_ko` 학습 데이터 매칭 상태에 따라:

| 조건 | 라우팅 | 비고 |
|---|---|---|
| 학습 데이터에 **≥3건** 등장 | **Warm 모델** | artist signal 안정 |
| 학습 데이터에 **1~2건만** 등장 (rare) | **Blend** | Warm features + strong smoothing / fallback mixing |
| 학습 데이터에 없음 (unseen) | **Cold 모델** | artist-agnostic 예측 |

**Blend 비율 통계** (R3 권장 — artist-weighted vs listing-weighted 분리 표기):
- **Artist-weighted mix**: 1,616 (≥3건) / 217 (2건) / 299 (1건) → warm **75.8%** / blend **24.2%** / cold (운영 비율)
- **Listing-weighted mix**: 학습 셋 40,137건 중 blend 후보 (1-2건 작가의 작품) = `299×1 + 217×2 = 733` → **blend rows 1.83%**
- 의미 차이: artist 단위는 모델 학습 시 영향력, listing 단위는 운영 시 예측 비중

**Blend 비율 산출 (Phase 5 최적화)**:
- 예시: 1건 작가 = `0.7 Cold + 0.3 Warm`, 2건 작가 = `0.5 Cold + 0.5 Warm`
- 실제 비율은 Phase 5에서 train fold OOF 기반 grid search로 결정

→ **2개 모델 별도 학습 + 3-way 라우팅 규칙**. (Codex R1 + R2 + R3 핵심 지적)

---

## 2. 데이터

### Source
- **`data/track3_unified_v1_train.csv`** — 40,137 rows (is_outlier=0)
- Artsy 10,584 / Saatchi 26,844 / Artue 2,709

### 작가 통계 (Codex R2가 직접 확인한 값)
- **Unique artists**: 2,132명
- **Singleton** (1건만): 299명
- **≤2건**: 516명 (24%) — blend 대상
- **≥3건**: 1,616명 (76%) — warm 대상

### 가격 분포 통계
- Median: 2.76M KRW
- Q25 / Q75: 1.19M / 6.74M
- **>10M 작품**: 6,586건 (16%)
- **>100M 작품**: 925건 (2.3%) — 63 작가
- **>10M 작가**: 844명

### Feature 셋 (2계열 분리 적용)

**Cold 모델 input** (artist-agnostic, 6개 ★):
- `medium_category` (categorical, 9 values)
- `support_category` (categorical, 7)
- `has_depth` (binary, missing indicator)
- `log_area` (continuous, heavy-tail 안정화)
- `estimated_ho` (한국 호수, log_area와 중복 가능성 → Phase 0 ablation 필수)
- `orientation` (categorical, 3 values)
- (선택 △): `width_cm`, `height_cm`, `depth_cm`

**Warm 모델 input** (Cold + artist 정보, 7~8개 ★):
- Cold features 전체 +
- `artist_name_ko` (categorical, 2,132 unique) — target encoding 또는 native categorical

**Target** (양쪽 공통):
- `ln_price_krw_unified` (학습) → `exp()` 복원 (평가)

---

## 3. 평가 설계

### 3.1 Split 전략

**1단계: Outer holdout 격리 (최초 1회만)**
- 전체 2,132 작가 중 **20% (≈426명)을 outer holdout으로 격리**
- 격리된 작가의 모든 작품은 Phase 0~4에서 절대 사용 X
- 남은 80% 작가 (≈1,706명)의 작품으로만 모델 개발
- **outer holdout 평가는 Phase 5 최종 1회만** (감사용)

**2단계: 모델 개발용 split (남은 80% 안에서)**

**Cold-start (PRIMARY)**:
- **`GroupKFold(groups=artist_name_ko, n_splits=5)`** — fold 간 작가 겹침 0%
- 5-fold OOF로 fold-median MdAPE 산출
- **모델 seed 3회 반복** (초기화 분산 측정) → **5-fold × 3-seed = 15 runs**
  - `GroupKFold`는 deterministic이라 fold는 동일, 모델 학습 seed만 변동
  - 목적: 모델 초기화/배치 셔플 등에 따른 분산만 측정
  - split uncertainty 별도 측정 원하면 `RepeatedGroupShuffleSplit` 추가 실험

**Warm-start (SECONDARY)**:
- **80/10/10 random split** (작품 단위, 작가는 train/val/test 양쪽 가능)
- multi-seed N=20 (분포 측정 + 95% CI)

### 3.2 Source-stratified 보고 (필수)

학습은 전체 데이터로 (train all), **결과는 source 별 분해**:
```
Cold (GroupKFold):
  All:     median_APE = XX.X%
  Artsy:   median_APE = XX.X% (n=...)
  Saatchi: median_APE = XX.X% (n=...)
  Artue:   median_APE = XX.X% (n=...)
```
→ Saatchi 편향 (67%) 감지 + source 간 일반화 능력 확인

### 3.3 Metric

| Metric | 정의 | 우선순위 |
|---|---|---|
| **median APE (cold-start)** | median(\|y - ŷ\| / y) | **★★ Primary** |
| **log-RMSE** | sqrt(mean((ln y - ln ŷ)²)) | ★ Secondary primary |
| **Within-30%** | \|ŷ/y - 1\| < 0.3 비율 (실용 정확도) | ★ Business |
| MAPE | mean(\|y - ŷ\| / y) | △ Reference |
| Within-50% | \|ŷ/y - 1\| < 0.5 비율 | △ |
| R² (log) | 학습 공간 적합도 | △ |
| **Price-band stratified median APE** | 고정 가격 구간 별 별도 측정 | ★ Coverage |
| Coverage@P80 | 80% 신뢰구간 actual coverage (quantile reg.) | ★ Calibration |

**Price-band 정의 (business-defined fixed bands — 분위수 아님)**:
- B1 (저가): ≤ 1M KRW — 8,436건
- B2 (보급): 1M ~ 3M — 12,799건
- B3 (중가): 3M ~ 10M — 12,316건
- B4 (고가): > 10M — 6,586건 (>100M 925건 포함)
- 컷 선정 이유: **사업상 해석 가능성** (계약/할인 기준선 등)
- 참고: 실제 분위수 Q25/Q50/Q75 = 1.19M/2.76M/6.74M (위 cut-off와 별도)

### 3.4 통계적 유의성

- Warm: N=20 seed → bootstrapping으로 95% CI
- Cold: **15 runs (5-fold × 3-seed)** → bootstrapping 95% CI
- Paired Wilcoxon signed-rank test (모델 간 비교)
- Sign test 단독 사용 금지 (방향만 보고 크기 무시 → 잘못된 결론 위험)

---

## 4. 모델 후보

### 4.1 선형 모델 — 양쪽 (Phase 1)

**Cold 모델**:
- OLS hedonic baseline (artist 없이)
- Ridge / Lasso (정규화)
- **Huber regression** (long-tail outlier robust)
- **LAD (least absolute deviation)** regression
- **Quantile regression** (q=0.1, 0.5, 0.9) — 신뢰구간 산출

**Warm 모델**:
- 위 모델 + `target_encode(artist_name_ko, smoothing=20)`
- artist FE OneHot은 2K+ unique라 비현실적 → target encoding 또는 hash trick

### 4.2 비선형 모델 — 양쪽 (Phase 2)

**Cold 모델** (artist_name_ko 미사용):
- LightGBM (categorical native)
- XGBoost
- CatBoost
- 비교 + Optuna tuning

**Warm 모델** (artist_name_ko 사용):
- 위 모델 + `artist_name_ko` native categorical
- 또는 target encoding (cross-fit 적용 — 학습/예측 분리)

### 4.3 Hybrid (Phase 3) — Warm/Cold 각각

**Stacking**:
- Base: Linear hedonic + LightGBM
- Meta: Ridge / 가중 평균

**Residual learning**:
- Step 1: Linear baseline
- Step 2: 잔차를 트리로 학습

### 4.4 Cold-start 특화 (Phase 4) — Cold 모델만

- **Work-level prototype model** — 작품 feature 공간에서 K-means → 새 작품은 가장 가까운 prototype의 mean price
- **Segmented experts by medium × ho regime** — medium × ho 셀별 별도 작은 모델 + 셀별 가중합
  - (주의: learned gating MoE가 아니라 **고정 분할 + 셀별 전문가**)
- **KNN retrieval** — 새 작품의 feature 거리 기반 K-nearest 작품의 weighted mean price

### 4.5 2-stage 거장 long-tail 모델 (조건부 실행)

- Stage 1: 고가 분류기 (>100M KRW 여부 binary, 925건 / 63 작가)
- Stage 2: 분류 결과 별 별도 회귀 (일반 / 거장)
- 거장 작품 (P95+) 예측 정확도 향상 목적

**Trigger 조건** (둘 중 하나 충족 시 Phase 2 종료 직후 즉시 실행):
- **B4 (>10M) median APE > 50%**, 또는
- **>100M 작품 median APE > 70%** (mean 대신 **median 사용** — tail 흔들림 방지, R3 권장)

→ 그렇지 않으면 Phase 5에서 선택적 진행

### 4.6 Conformal prediction (Phase 5, 선택)

- 점추정 외 **calibrated 90% / 80% 신뢰구간** 산출
- Quantile regression 결과를 inductive conformal로 보정
- 운영에서 "가격 ± 30%" 같은 범위 제공 가능

**Coverage 분해 보고 (필수)**:
- 전체 80% coverage만 보면 위험 (이질적 데이터)
- **Source × Price-band 12 셀 (3 × 4) coverage** 분해
- 각 셀에서 목표 coverage ± 5%p 이내 유지 여부 확인

---

## 5. 단계별 진행 (Phase Gates)

### Phase 0: 데이터 분할 + Baseline
- [ ] `scripts/track3/split_data.py` — Outer holdout 격리 + Cold GroupKFold(5) + Warm 80/10/10
- [ ] **estimated_ho vs log_area ablation** — 둘 다 / log_area only / estimated_ho only 3-way
- [ ] Baseline: median(train ln_price) 단일 예측 → cold/warm MdAPE 기준선
- **Gate**: split reproducible (seed fix) + baseline MdAPE 측정 완료

### Phase 1: 선형 모델 (Cold + Warm 병렬)
- [ ] OLS hedonic baseline (cold/warm 각각)
- [ ] Ridge / Lasso (cold/warm 각각)
- [ ] Huber / LAD regression (cold) — long-tail robust 효과 확인
- [ ] Quantile regression (cold, q=0.1/0.5/0.9) — 신뢰구간 baseline
- [ ] Target encoding for `artist_name_ko` (**warm 전용**, cross-fit)
- **Gate**: cold median APE < 75% (baseline 대비 의미 있는 향상)

### Phase 2: 비선형 모델 (Cold + Warm 병렬)
- [ ] LightGBM default → Optuna tuning (cold/warm 각각)
- [ ] XGBoost / CatBoost 비교 (cold/warm 각각)
- [ ] Loss 변형: squared / Huber / Pseudo-Huber
- [ ] **Phase 4.5 trigger 체크** — B4 / >100M median APE 측정
- **Gate**: cold median APE < 60% (선형 대비 +10pp 이상)

### Phase 3: Hybrid (Cold + Warm 병렬)
- [ ] Stacking (linear + lgbm) — cold/warm 각각
- [ ] Residual learning — cold/warm 각각
- **Gate**: cold median APE < 55% (단일 모델 best 대비 +3pp 이상)

### Phase 4: Cold-start 특화 (Phase 1과 병렬 가능)
- [ ] Work-level prototype (K-means + nearest cluster mean)
- [ ] **Segmented experts** by medium × ho regime
- [ ] KNN retrieval (k=5, 10, 20)
- **Gate**: cold median APE < 50% (Phase 3 cold 대비 향상)

### Phase 4.5: 2-stage 거장 모델 (조건부 실행)
- [ ] **Trigger 충족 시 Phase 2 종료 직후 즉시 실행** (Phase 5 이전)
- [ ] 고가 (>100M) 분류기 + 구간별 회귀
- **Gate**: B4 / >100M median APE 향상 확인

### Phase 5: 최종 평가 + 보고
- [ ] N=20 seed multi-run (Warm)
- [ ] **5-fold × 3-seed = 15 runs** (Cold, GroupKFold)
- [ ] **Source 별 breakdown** (Artsy / Saatchi / Artue)
- [ ] **Price-band stratified** 보고 (B1~B4 fixed bands)
- [ ] **Source-balanced weighting stress test** — inverse-frequency weight with cap (downsampling 아님). 메인라인 train-all 유지하면서 weighted loss로 같은 OOF split 비교
- [ ] **Outer holdout 평가** (격리해둔 20% 작가 — 최종 1회만)
- [ ] **Bootstrapping 95% CI** + Paired Wilcoxon
- [ ] **Rare artist fallback 규칙** 최적화 (1건/2건 시 blend 비율 grid search)
- [ ] **Conformal coverage by source × price-band** (3 × 4 = 12 셀) (선택)
- [ ] HTML 리포트

---

## 6. 위험 요소 / 가정

### 위험
1. **Cold-start 본질적 어려움** — artist 정보 없이 medium/size로만 → 50% MdAPE도 도전적
2. **Saatchi 67% 편향** — train all + source-stratified report + Phase 5 source-balanced stress test로 완화
3. **거장 long-tail** — >100M 925건 / 63 작가. B4 부진 시 Phase 4.5 조기 실행
4. **Singleton artist 299명, ≤2건 516명** — 운영은 3-way 라우팅 (Cold or Blend)
5. **`estimated_ho` vs `log_area` 정보 중복** — Phase 0에서 ablation으로 결정
6. **Target encoding leakage** — warm 모델에서 cross-fit (학습/예측 분리) 필수

### 가정
1. `artist_name_ko` 매칭 100% 정확 (v12 검증, manual overrides 32건 반영)
2. is_outlier=0 학습 셋 (40,137 rows)이 대표성 가짐
3. `ln_price` 학습 → `exp()` 복원이 합리적 (heavy-tail 정규화)

### 한계 (외부 보고 시 명시)
1. **시간 split 없음** — `listing year` 없어 temporal validation 불가
2. **Singleton artist** — GroupKFold에서 test에 들어가면 cold-start와 동치 (운영은 Cold 라우팅)
3. **🔴 본 모델은 "listing-price prediction"이지 "시장가치 예측 아님" (필수 명시)**
   - 학습/평가 target = **플랫폼 게시 가격**
   - 실제 거래가 ≠ 게시가 (미판매 / 협상 / 갤러리 마진)
   - Source별 가격 정책 차이 (Artsy 갤러리 마크업 vs Saatchi 직거래 등)
   - 절대가격 해석 보수적으로 — **"이 작품의 거래가는 X 원" 단정 금지**

---

## 7. 실행 계획 (timeline)

| Phase | 의존 | 예상 작업량 |
|---|---|---|
| Phase 0 | — | 0.5일 (split + outer holdout 격리 + ho/area ablation + baseline) |
| Phase 1 (Cold) | Phase 0 | 1일 |
| Phase 1 (Warm) | Phase 0 | 1일 (병렬 가능) |
| Phase 2 (Cold) | Phase 0 | 1.5일 |
| Phase 2 (Warm) | Phase 0 | 1.5일 (병렬 가능) |
| Phase 3 (Cold + Warm) | Phase 1, 2 | 1일 |
| Phase 4 (Cold 특화) | Phase 0 (병렬!) | 1.5일 |
| Phase 4.5 (조건부) | Phase 2 trigger | 1일 |
| Phase 5 | All | 1일 |
| **Total (순차)** | | ~9일 |
| **Total (병렬)** | | ~6일 |

병렬화 기회:
- Phase 1 Cold + Warm: 동시
- Phase 2 Cold + Warm: 동시
- Phase 4 (Phase 0 직후 시작 가능): Phase 1, 2와 병렬

---

## 8. 산출물

### 코드
- `scripts/track3/split_data.py` — Outer holdout + Cold/Warm split 함수
- `scripts/track3/baseline.py` — median baseline + ho/area ablation
- `scripts/track3/train_linear_cold.py` — Phase 1 Cold
- `scripts/track3/train_linear_warm.py` — Phase 1 Warm
- `scripts/track3/train_tree_cold.py` — Phase 2 Cold
- `scripts/track3/train_tree_warm.py` — Phase 2 Warm
- `scripts/track3/train_hybrid.py` — Phase 3
- `scripts/track3/train_coldstart.py` — Phase 4 (prototype/segmented experts/KNN)
- `scripts/track3/train_two_stage.py` — Phase 4.5 (조건부)
- `scripts/track3/eval_unified.py` — Source/Price-band stratified 평가

### 결과
- `experiments/track3_modeling_2026_05_11/`
  - Per-phase 결과 JSON
  - 모델 artifacts (joblib / native format)
  - 비교 표 (markdown)
- `docs/track3_modeling_results_v1.html` — 최종 리포트

---

## 9. Codex 검수 요청 사항 (R3)

R2 fix 8건 + R3 추가 지적 12건 반영 완료. R3 검증 항목:

1. **R2 fix 8건 정확 반영 검증** — outer holdout / 15 runs / Price-band 고정 구간 / segmented experts / 3-way 라우팅 / source-balanced stress test / conformal 12 셀 / Phase 4.5 trigger
2. **R3 추가 지적 반영 검증** — blend artist-weighted 24.2% + listing-weighted 1.83% / Phase 4.5 trigger mean→median / listing-price caveat 강화 / 데이터 통계 (516/925/844) 명시
3. **Phase 0 진행 준비도** — 추가 fix 없이 코딩 시작 가능한가?

R3에서 별 이슈 없으면 → **Phase 0 즉시 시작**

---

## 변경 이력
- v1 (2026-05-11 오전): 초안
- v2 (2026-05-11 오후): Codex R1 검수 반영 — Cold/Warm 2계열 / GroupKFold / source-stratified / Quantile + Huber / Phase 4 재정의 + 병렬 / 2-stage 거장 / Conformal
- v2.1 (2026-05-11 저녁): Codex R2 fix 8건 + R3 추가 지적 12건 — outer holdout 위치 / 15 runs / Price-band fixed bands / segmented experts / 3-way 라우팅 / source-balanced weighting / conformal 12 셀 / Phase 4.5 trigger median / blend artist+listing weighted / listing-price caveat
