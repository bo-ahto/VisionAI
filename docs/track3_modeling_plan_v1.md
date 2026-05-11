# Track 3 — 가격 예측 모델링 Plan v1

**작성일**: 2026-05-11
**작성자**: Bo + Claude
**검수 대상**: Codex R1 (사전)
**Status**: Draft

---

## 1. 목표

### Primary
**Cold-start (학습되지 않은 작가) 예측도 향상**
- 신규 작가의 신규 작품에 대한 가격 예측 정확도 (MAPE / median APE).
- Track 1 한계: 작가 정보 의존도 높아 cold-start 약함 → Track 3는 cold-start를 우선 설계.

### Secondary
**Warm-start (학습된 작가) 예측도 향상**
- 학습 작가의 신규 작품 예측 (artist FE / target encoding 활용).
- Cold-start보다 정확도 높아야 합리적 (artist 정보 활용 가치 입증).

---

## 2. 데이터

### Source
- **`data/track3_unified_v1_train.csv`** — 40,137 rows (is_outlier=0)
- Artsy 10,584 / Saatchi 26,844 / Artue 2,709
- Source: Artsy + Saatchi + Artue 통합

### Schema (학습 사용 마크 ★)
- **Feature 필수 (★ 7개)**:
  - `artist_name_ko` (categorical / 2,182 unique)
  - `medium_category` (8 categories)
  - `support_category` (7 categories)
  - `has_depth` (binary)
  - `log_area` (continuous, heavy-tail 안정화)
  - `estimated_ho` (한국 캔버스 호수 1~200)
  - `orientation` (4 categories)

- **Feature 선택 (△ 3개)** — 모델 비교 시 ablation:
  - `width_cm`, `height_cm`, `depth_cm`

- **Target**: `ln_price_krw_unified` (학습) → `exp()` 복원 (평가)

### 통계 (학습 셋)
- median 가격: 2,760,000원
- median 호수: 16.2호
- median 면적: 3,672 cm²

---

## 3. 평가 설계

### Split 전략 (2-track)

**Track A: Warm-start eval** (작품 단위 random split)
- 80% train / 10% val / 20% test
- 같은 작가가 train/test 양쪽 등장 가능
- 시나리오: 알려진 작가의 신규 작품 예측

**Track B: Cold-start eval** (작가 단위 holdout split) — **PRIMARY**
- 2,182 unique artists를 80/10/10으로 split (artist-level)
- Train artist의 작품 != Test artist의 작품 (artist 겹침 0%)
- 시나리오: 알려지지 않은 신규 작가 작품 예측

### Random seed
- 단일 seed (e.g. 42)로 시작, 결과 확정 후 multi-seed (N=10) 검증.

### Metrics
| Metric | 정의 | 우선순위 |
|---|---|---|
| **median APE** | median(\|y - ŷ\| / y) — Robust to outliers | ★ Primary |
| MAPE | mean(\|y - ŷ\| / y) | △ |
| RMSE (log) | sqrt(mean((ln y - ln ŷ)²)) | △ |
| R² (log) | 학습 공간 적합도 | △ |
| **Within-30%** | \|ŷ/y - 1\| < 0.3 비율 | ★ Business |
| Within-50% | \|ŷ/y - 1\| < 0.5 비율 | △ |
| Coverage@P80 | 80% 신뢰구간 actual coverage | △ (calibration) |

### 평가 시 보고 형식
```
Cold-start (Track B):
  median APE: XX.X% / MAPE: XX.X% / Within-30%: XX.X%
Warm-start (Track A):
  median APE: XX.X% / MAPE: XX.X% / Within-30%: XX.X%
```

---

## 4. 모델 후보

### 4.1 선형 모델 (Hedonic Regression)

**Phase 1A. OLS baseline**
```
ln_price ~ medium + support + has_depth + log_area + estimated_ho + orientation
         + C(artist_name_ko)  [warm-start만]
         + target_encode(artist_name_ko)  [cold-start은 train mean으로 fallback]
```

**Phase 1B. Ridge / Lasso**
- artist FE가 2K+ unique라 overfitting 위험 → Ridge 정규화
- Lasso로 sparse feature selection

**Phase 1C. ElasticNet**
- Ridge + Lasso 절충

### 4.2 비선형 모델 (Tree-based)

**Phase 2A. LightGBM** (default)
- categorical native 지원 (`artist_name_ko` 직접 input)
- 빠른 학습 + 검증된 성능

**Phase 2B. XGBoost**
- Track 1 운영 모델과 비교 baseline

**Phase 2C. CatBoost**
- artist_name_ko native categorical (target leak 방지 buffer)
- 작은 데이터에 강함

### 4.3 Hybrid (Phase 3)

**Phase 3A. Stacking**
- Base: Linear (hedonic) + LightGBM
- Meta: Ridge / simple weighted average

**Phase 3B. Residual Learning**
- Step 1: Linear로 base 예측 (artist-agnostic 부분)
- Step 2: 잔차를 트리로 학습 (artist-specific 보정)

### 4.4 Cold-start 특화 (Phase 4)

**Phase 4A. Smoothed Target Encoding**
- artist mean ln_price를 sample size로 shrinkage
- cold-start 시 global mean으로 fallback

**Phase 4B. Artist Embedding**
- Train artist를 (medium, support, ho, price) 4D로 clustering (K-means / GMM)
- Test artist → 가장 가까운 cluster의 mean으로 fallback

**Phase 4C. Similar Work Retrieval**
- KNN on (log_area, estimated_ho, medium, support, orientation)
- Test 작품 → train의 K-nearest 작품의 weighted mean price

---

## 5. 단계별 진행 (Phase Gates)

### Phase 0: 데이터 분할 + Baseline
- [ ] Random split (warm) / artist-holdout split (cold) 코드
- [ ] Baseline: median(train ln_price) 단일 예측 → cold/warm MAPE 기준선
- **Gate**: split reproducible (seed fix) + baseline 결과 < 100% MAPE (sanity)

### Phase 1: 선형 모델
- [ ] OLS hedonic baseline (warm + cold)
- [ ] Ridge / Lasso 비교
- [ ] Target encoding for artist_name_ko
- **Gate**: cold-start median APE < 75% (baseline 대비 의미 있는 향상)

### Phase 2: 비선형 모델
- [ ] LightGBM default → tuning (Optuna)
- [ ] XGBoost / CatBoost 비교
- **Gate**: cold-start median APE < 60% (선형 대비 +10pp 이상 향상)

### Phase 3: Hybrid
- [ ] Stacking (linear + lgbm)
- [ ] Residual learning
- **Gate**: cold-start median APE < 55% (단일 모델 best 대비 +3pp 이상)

### Phase 4: Cold-start 특화
- [ ] Target encoding (smoothed)
- [ ] Artist embedding / KNN
- **Gate**: cold-start median APE < 50% (Phase 3 대비 추가 향상)

### Phase 5: 최종 평가 + 보고
- [ ] Multi-seed (N=10) variance 측정
- [ ] Source 별 (artsy/saatchi/artue) breakdown
- [ ] 호수/매체/orientation 별 segment analysis
- [ ] Track 1 baseline 대비 비교
- [ ] HTML 리포트 생성

---

## 6. 위험 요소 / 가정

### 위험
1. **Cold-start은 본질적으로 어려움** — 작가 정보 없이 medium/size로만 예측. 50% MAPE도 도전적일 수 있음.
2. **Artue 작품 적음** (2,709 rows) — source 간 imbalance.
3. **Outlier 처리** — is_outlier=0 필터해도 일부 의심 케이스 남아 있을 수 있음.
4. **거장 작품 (10억+)** — 학습 셋에 소수라 예측 어려움 (long-tail).
5. **Saatchi 비중 큼 (67%)** — saatchi-style 작품에 모델이 편향될 위험.

### 가정
1. `artist_name_ko` 매칭 100% 정확 (v12 검증 완료, 95%+ 신뢰).
2. `estimated_ho`는 면적의 monotonic 변환 → tree에서 동등 정보 (선형/NN에선 추가 가치).
3. is_outlier=0 학습 셋이 대표성 가짐 (Source 별 96-98% 유지).

### Open question (Codex 검수)
1. Cold-start과 Warm-start 평가를 분리 vs 통합 보고?
2. Random split + artist-holdout 외에 **시간 split** 필요? (현재 dataset에 listing year 없음)
3. Phase 4의 artist embedding 차원 수 (K) 적절한 cluster 수?
4. Hybrid 가격 (`was_converted`) 변수를 feature로 추가? (현재 미사용)

---

## 7. 실행 계획 (timeline)

| Phase | 예상 작업량 | 의존 |
|---|---|---|
| Phase 0 | 0.5일 (split + baseline) | — |
| Phase 1 | 1일 (linear 3종) | Phase 0 |
| Phase 2 | 1.5일 (tree 3종 + tuning) | Phase 0 |
| Phase 3 | 1일 (ensemble) | Phase 1, 2 |
| Phase 4 | 1.5일 (cold-start 특화) | Phase 2 |
| Phase 5 | 1일 (보고서) | All |
| **Total** | **~6.5일** | |

---

## 8. 산출물

- `scripts/track3/split_data.py` — train/val/test split (warm/cold)
- `scripts/track3/train_linear.py` — Phase 1
- `scripts/track3/train_tree.py` — Phase 2
- `scripts/track3/train_hybrid.py` — Phase 3
- `scripts/track3/train_coldstart.py` — Phase 4
- `scripts/track3/eval_unified.py` — 통합 평가
- `experiments/track3_modeling_2026_05_11/` — 모든 결과 + 모델 artifacts
- `docs/track3_modeling_results_v1.html` — 최종 리포트

---

## 9. Codex 검수 요청 사항

1. **목표 정합성**: cold-start primary가 옳은가? (track 1과 다른 우선순위)
2. **평가 split**: artist-holdout 외에 추가 split (예: source-holdout)?
3. **Metric**: median APE primary가 적절한가? (가격대별 균등 평가)
4. **모델 후보 누락**: 다른 비선형 모델 (Gradient Boosting Regression Tree, Neural Net 등) 시도?
5. **Phase 의존 관계**: Phase 3, 4 동시 진행 가능한가? (병렬화 기회)
6. **Cold-start 평가 robustness**: 단일 split이 noise 영향 큼 → K-fold artist holdout (e.g. 5-fold)?
7. **위험 mitigation**: 거장 작품 weighting / source balancing 필요한가?

---

## 변경 이력
- v1 (2026-05-11): 초안. Codex R1 검수 대기.
