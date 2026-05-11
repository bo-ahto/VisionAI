# Track 3 — 가격 예측 모델링 Plan v2

**작성일**: 2026-05-11
**작성자**: Bo + Claude
**검수**: Codex R1 (v1) 반영 / R2 검수 대기
**Status**: Draft v2

---

## 변경 이력 (v1 → v2)

Codex R1 Critical 4건 + Improvement 5건 반영:
1. **Cold/Warm 모델 2계열 분리** — Cold 모델은 `artist_name_ko` 미사용 (정의 정합성)
2. Warm split 비율 오류 수정 (80/10/20 = 110% → **80/10/10**)
3. Cold split robustness — **GroupKFold(artist, 5-fold)** 필수
4. Source 편향 대응 — train all, **report by source** 필수
5. Metric — `median APE` primary 유지 + **price-band stratified** + `log-RMSE` + `Within-30%` 세트
6. Target encoding 재배치 — **warm-start 전용**으로 이동 (cold-start에 효용 없음)
7. Artist embedding → **"work-level prototype"** / **"mixture-of-experts"**로 재명명
8. Phase 4 의존 — Phase 1과 병렬 가능 (KNN/retrieval은 tree에 의존 X)
9. **Quantile regression / Conformal prediction** 추가 (불확실성 대역)
10. **Huber/LAD loss** 추가 (long-tail robust)
11. **estimated_ho vs log_area ablation** 우선 실시 (정보 중복 가능성)

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

### 운영 시점 라우팅
운영 환경에서는 들어온 작품의 `artist_name_ko`가 학습 데이터에 있는지 확인 후:
- 매칭 ○ → **Warm 모델**
- 매칭 X → **Cold 모델**

→ **2개 모델을 별도 학습 + 평가**해야 함 (Codex R1 핵심 지적).

---

## 2. 데이터

### Source
- **`data/track3_unified_v1_train.csv`** — 40,137 rows (is_outlier=0)
- Artsy 10,584 / Saatchi 26,844 / Artue 2,709
- Unique artists: **2,132명** (singleton 299명 포함)

### Feature 셋 (2계열 분리 적용)

**Cold 모델 input** (artist-agnostic, 6개 ★):
- `medium_category` (categorical, 9 values)
- `support_category` (categorical, 7)
- `has_depth` (binary, missing indicator)
- `log_area` (continuous, heavy-tail 안정화)
- `estimated_ho` (한국 호수, log_area와 중복 가능성 → ablation 필수)
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

**Cold-start (PRIMARY)**:
- **`GroupKFold(groups=artist_name_ko, n_splits=5)`** — fold 간 작가 겹침 0%
- 5-fold OOF로 fold-median MdAPE 산출
- 추가: outer holdout (전체 작가의 20%)으로 최종 정직성 검증

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

### 3.3 Metric (Codex R1 권장 반영)

| Metric | 정의 | 우선순위 |
|---|---|---|
| **median APE (cold-start)** | median(\|y - ŷ\| / y) | **★★ Primary** |
| **log-RMSE** | sqrt(mean((ln y - ln ŷ)²)) | ★ Secondary primary |
| **Within-30%** | \|ŷ/y - 1\| < 0.3 비율 (실용 정확도) | ★ Business |
| MAPE | mean(\|y - ŷ\| / y) | △ Reference |
| Within-50% | \|ŷ/y - 1\| < 0.5 비율 | △ |
| R² (log) | 학습 공간 적합도 | △ |
| **Price-band stratified median APE** | 분위수 (Q1/Q2/Q3/Q4) 별 별도 측정 | ★ Coverage |
| Coverage@P80 | 80% 신뢰구간 actual coverage (quantile reg.) | ★ Calibration |

**Price-band 정의 (가격 분위수)**:
- Q1: ≤ 1M KRW (저가)
- Q2: 1M ~ 3M
- Q3: 3M ~ 10M
- Q4: > 10M (고가)
- 각 band별 median APE 보고 → 가격대 편향 확인

### 3.4 통계적 유의성

- N=20 seed → bootstrapping으로 95% CI
- Paired Wilcoxon signed-rank test (모델 간 비교)
- Sign test 단독 사용 금지 (방향만 보고 크기 무시 → 잘못된 결론 위험)

---

## 4. 모델 후보

### 4.1 선형 모델 — 양쪽 공통 (Phase 1)

**Cold 모델**:
- OLS hedonic baseline (artist 없이)
- Ridge / Lasso (정규화)
- **Huber regression** (long-tail outlier robust) ← 신규
- **LAD (least absolute deviation)** regression ← 신규
- **Quantile regression** (q=0.1, 0.5, 0.9) ← 신규 — 신뢰구간 산출

**Warm 모델**:
- 위 모델 + `target_encode(artist_name_ko, smoothing=20)`
- artist FE OneHot은 2K+ unique라 비현실적 → target encoding 또는 hash trick

### 4.2 비선형 모델 — 양쪽 공통 (Phase 2)

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

(Codex R1 권장: 명칭 재정의)

- **Work-level prototype model** — 작품 feature 공간에서 K-means → 새 작품은 가장 가까운 prototype의 mean price
- **Mixture-of-experts by medium/ho regime** — medium × ho 셀별 별도 작은 모델 + 가중합
- **KNN retrieval** — 새 작품의 feature 거리 기반 K-nearest 작품의 weighted mean price

### 4.5 2-stage 거장 long-tail 모델 (Phase 4.5, 선택)

(Codex R1 추가 제안)

- Stage 1: 고가 분류기 (>100M KRW 여부 binary)
- Stage 2: 분류 결과 별 별도 회귀 (일반 / 거장)
- 거장 작품 (P95+) 예측 정확도 향상 목적

### 4.6 Conformal prediction (Phase 5, 선택)

(Codex R1 추가 제안)

- 점추정 외 **calibrated 90% / 80% 신뢰구간** 산출
- Quantile regression 결과를 inductive conformal로 보정
- 운영에서 "가격 ± 30%" 같은 범위 제공 가능

---

## 5. 단계별 진행 (Phase Gates)

### Phase 0: 데이터 분할 + Baseline
- [ ] `scripts/track3/split_data.py` — Cold GroupKFold(5) + Warm 80/10/10 함수
- [ ] **estimated_ho vs log_area ablation** — 둘 다 / log_area only / estimated_ho only 3-way
  → tree에서 중복 확인 + feature 결정
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
- **Gate**: cold median APE < 60% (선형 대비 +10pp 이상)

### Phase 3: Hybrid (Cold + Warm 병렬)
- [ ] Stacking (linear + lgbm) — cold/warm 각각
- [ ] Residual learning — cold/warm 각각
- **Gate**: cold median APE < 55% (단일 모델 best 대비 +3pp 이상)

### Phase 4: Cold-start 특화 (Phase 1과 병렬 가능)
- [ ] Work-level prototype (K-means + nearest cluster mean)
- [ ] Mixture-of-experts by medium × ho regime
- [ ] KNN retrieval (k=5, 10, 20)
- **Gate**: cold median APE < 50% (Phase 3 cold 대비 향상)

### Phase 4.5: 2-stage 거장 모델 (선택)
- [ ] 고가 (P95+) 분류기
- [ ] 구간별 회귀
- **Gate**: Price-band Q4 (>10M) median APE 향상 확인

### Phase 5: 최종 평가 + 보고
- [ ] N=20 seed multi-run (Warm)
- [ ] 5-fold × N=5 = 25 runs (Cold, GroupKFold)
- [ ] **Source 별 breakdown** (Artsy / Saatchi / Artue)
- [ ] **Price-band stratified** 보고
- [ ] **Bootstrapping 95% CI** + Paired Wilcoxon
- [ ] Conformal prediction (선택) — 80% / 90% coverage
- [ ] HTML 리포트

---

## 6. 위험 요소 / 가정

### 위험
1. **Cold-start 본질적 어려움** — artist 정보 없이 medium/size로만 → 50% MdAPE도 도전적
2. **Saatchi 67% 편향** — train all + source-stratified report로 완화. 추가 stress test: source-balanced training weights
3. **거장 long-tail** — 10억+ 작품 4건. P95+ 별도 모델로 처리 (Phase 4.5)
4. **Singleton artist 299명** — Cold split에서 자동 unseen으로 처리
5. **`estimated_ho` vs `log_area` 정보 중복** — Phase 0에서 ablation으로 결정
6. **Target encoding leakage** — warm 모델에서 cross-fit (학습/예측 분리) 필수

### 가정
1. `artist_name_ko` 매칭 100% 정확 (v12 검증, manual overrides 32건 반영)
2. is_outlier=0 학습 셋 (40,137 rows)이 대표성 가짐
3. `ln_price` 학습 → `exp()` 복원이 합리적 (heavy-tail 정규화)

### 한계 (외부 보고 시 명시)
1. **시간 split 없음** — `listing year` 없어 temporal validation 불가
2. **Singleton artist** — GroupKFold에서 test에 들어가면 cold-start와 동치 (Cold 모델로 라우팅)
3. **price ground truth 신뢰** — listing price 기준, 실제 거래가가 아닐 수 있음

---

## 7. 실행 계획 (timeline)

| Phase | 의존 | 예상 작업량 |
|---|---|---|
| Phase 0 | — | 0.5일 (split + ho/area ablation + baseline) |
| Phase 1 (Cold) | Phase 0 | 1일 |
| Phase 1 (Warm) | Phase 0 | 1일 (병렬 가능) |
| Phase 2 (Cold) | Phase 0 | 1.5일 |
| Phase 2 (Warm) | Phase 0 | 1.5일 (병렬 가능) |
| Phase 3 (Cold + Warm) | Phase 1, 2 | 1일 |
| Phase 4 (Cold 특화) | Phase 0 (병렬!) | 1.5일 |
| Phase 4.5 (2-stage, 선택) | Phase 2 | 1일 |
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
- `scripts/track3/split_data.py` — Cold/Warm split 함수
- `scripts/track3/baseline.py` — median baseline + ho/area ablation
- `scripts/track3/train_linear_cold.py` — Phase 1 Cold
- `scripts/track3/train_linear_warm.py` — Phase 1 Warm
- `scripts/track3/train_tree_cold.py` — Phase 2 Cold
- `scripts/track3/train_tree_warm.py` — Phase 2 Warm
- `scripts/track3/train_hybrid.py` — Phase 3
- `scripts/track3/train_coldstart.py` — Phase 4 (prototype/MoE/KNN)
- `scripts/track3/train_two_stage.py` — Phase 4.5 (선택)
- `scripts/track3/eval_unified.py` — Source/Price-band stratified 평가

### 결과
- `experiments/track3_modeling_2026_05_11/`
  - Per-phase 결과 JSON
  - 모델 artifacts (joblib / native format)
  - 비교 표 (markdown)
- `docs/track3_modeling_results_v1.html` — 최종 리포트

---

## 9. Codex 검수 요청 사항 (R2)

1. **2계열 분리 적절성** — Cold/Warm 별도 모델 설계가 깔끔한가? 운영 시 라우팅 안전한가?
2. **GroupKFold 5-fold + outer holdout** — 이중 검증 필요한가?
3. **Price-band 정의** (분위수 4단계) — 적절한 cut-off인가?
4. **2-stage 거장 모델** — Phase 4.5 우선순위 (Phase 5 이전에 할 가치?)
5. **Conformal prediction** — Phase 5 선택사항이 맞나? 운영 가치는?
6. **Phase 4 명칭** — "work-level prototype", "mixture-of-experts" 정확한가?
7. **N seed 수** — Warm N=20, Cold 5-fold × N=5 = 25 적절한가?
8. **Open question 미해결** — singleton artist 처리 (Cold 라우팅 자동), price ground truth caveat

---

## 변경 이력
- v1 (2026-05-11 오전): 초안
- v2 (2026-05-11 오후): Codex R1 검수 반영 — Cold/Warm 2계열 / GroupKFold / source-stratified / Quantile + Huber / Phase 4 재정의 + 병렬 / 2-stage 거장 / Conformal
