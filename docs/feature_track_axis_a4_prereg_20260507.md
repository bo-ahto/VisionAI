# Feature Track Axis A.4 — Title Text Embedding Pre-registration

> **작성일**: 2026-05-07 (freeze)
> **위치**: 새 Phase 2'' Axis A 의 **A.4 first heavy escalation step (escalation from A.3 BORDERLINE)**
> **연계**: `docs/feature_track_axis_a3_results_20260507.md` (A.3 BORDERLINE 99% CI very close miss → A.4 escalation, Step gate B안) / `docs/feature_track_axis_a1_prereg_20260507.md` (Step sequence + α=0.01 99% CI operationalization) / `docs/feature_track_design_20260507.md` (axis 설계)

> ⚠️ **연구 목적**: A.3 BORDERLINE (Axis A strongest signal, 99% CI +0.41%p miss) 후 step gate B안에 따라 **artwork-level title text embedding 추가 시 cold-start LAO 개선 가능?** 평가. **First heavy escalation** (compute / storage 비용 ↑) + working hypothesis "artwork-level cross-artist applicable signal 이 cold-start LAO 에 유효" 의 **text axis 재시험**.

> **본 prereg freeze**: 가설 / metric / family / PASS 기준 / per-step freeze 6항목 / embedding model = **2026-05-07 freeze**.

> **A.1/A.2/A.3 v2 lessons 사전 반영**: cluster bootstrap 진짜 구현 / α=0.01 99% CI decision / per-step freeze 6항목 / 운영 spec 인용 정확성 / framing 톤 (working hypothesis 입증 X)

## 1. Input / Hypothesis

### 1.1 A.3 결과 input
- A.3 100-seed mean: overall -2.11%p / 저가 -2.65%p ✓ hard gate / mid-high -1.79%p / newly-warm -3.15%p — **Axis A strongest signal**
- 95% CI [-9.54, -0.36] ✓ / 99% CI [-11.37, +0.41] ✗ very close miss
- Seed-level violation 13/100 = 13% (Axis A min)
- 코덱스 framing: "strongest Axis A signal, but not decision-grade under pre-registered α=0.01 rule"
- → A.4 escalation, A.3 features drop (alternative hypothesis sequence)

### 1.2 A.4 Hypothesis
> **운영 모델 F4 + spline 에 multilingual title embedding (PCA top-K) 추가 시 cold-start LAO MdAPE 개선 + 저가 segment harm 0?**
>
> **A.4 가 추가하는 신호**: 작품 제목의 의미 신호 (시리즈명 / 추상도 / 다국어 제목 의미) — multilingual sentence embedding 으로 capture. **모두 artwork-level cross-artist applicable signal** — A.3 working hypothesis 와 정합 axis (text 차원의 confirmation).

### 1.3 시점 정합성 (코덱스 P1)
- `title` = 작품의 본질 attribute, scrape/sale 시점 무관 → **시점 정합성 명확 OK** (A.3 동일)

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Per-step freeze 6항목

#### (a) Feature set — text embedding PCA top-K

| Feature | Source | Encoding |
|---|---|---|
| `title_emb_pca_0` ~ `title_emb_pca_K-1` | `title` column | multilingual BERT embedding → PCA top-K |

> **K = 10 final** (prereg freeze): conservative dim — 8,495 작품 / A.1+A.2+A.3 combined columns (≈22) 대비 controlled ratio. PCA 가 384-dim embedding 의 분산 majority capture.

#### (b) Encoding — spec freeze (한 줄씩)

- **Embedding model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - **Version pin**: sentence-transformers 5.4.1 / transformers 5.8.0 (실험 시작 시점, freeze)
  - **Embedding dim**: 384
  - **Pretrained, fine-tuning X** (운영 spec 의 freeze 정신과 정합)
  - **Multilingual**: 50+ 언어 지원 (KR/EN/mixed 모두 적용)
- **Title preprocessing**:
  - NaN → `""` (empty string, 1 row only)
  - No additional normalization (lowercase / punctuation 등 X — model 자체가 처리)
- **PCA**:
  - **K = 10** (top-K principal components, freeze)
  - **Fit on train fold only** (LAO 별 train embedding 으로 PCA fit, leakage-safe)
  - **Apply to test fold** (transform with train PCA components)
  - **Implementation**: `sklearn.decomposition.PCA(n_components=10, random_state=42)`
- **Embedding cache**:
  - 모든 8,495 title 의 384-dim embedding 사전 계산 (deterministic) — `data/curated/title_embeddings_minilm_v1.npy` (선택, time saving)
  - LAO seed 별 train/test split 시 cache 에서 row indexing — embedding 자체 재계산 X (deterministic / leakage 무관)
  - **Cache hash**: SHA-16 of embedding npy file → canonical artifact

#### (c) Preprocessing
- Missing imputation: `title` 1 row NaN → `""` (zero embedding 가까움)
- Outlier handling: Huber regression (운영 모델과 동일)
- Standardization: 운영 모델과 동일

#### (d) Interaction 허용 범위 — **NONE** (additive only, A.1-A.3 동일)
- ❌ embedding × `is_low` interaction
- ❌ embedding × geometry / category 등 interaction
- ❌ Polynomial / spline of embedding components

#### (e) Stop/go rule (LAO primary family)
- **PASS**: Δ ≤ -1.0%p AND **99% CI 상한 ≤ 0 (α=0.01)** AND Hard gate Δ_low ≤ 0%p
- **BORDERLINE**: -1.0 < Δ ≤ -0.3%p AND Hard gate ✓ → A.5 escalation
- **FAIL**: Δ > -0.3%p OR Hard gate 위반 → A.5 escalation (B안)

#### (f) 다음 step (alternative hypothesis sequence)
- A.4 FAIL/BORDERLINE 시 → **A.5 (image embedding, CLIP/ResNet) 로 escalation**
- A.5 prereg 에서 A.4 features drop (alternative hypothesis sequence)
- A.5 의 baseline = 운영 모델 F4
- **A.5 = Axis A 마지막 step** — A.5 FAIL 시 Axis A 전체 종료 → Axis B (Phase A pre-screen 통과 시) 또는 program-level 재설계
- Inferential family = program-level cumulative (5 step Bonferroni α=0.01, FWER ≤ 0.05)

### 2.2 Primary Model

```
log_price_i = β0 + β1·log_area_i + β2·birth_year_centered_i + β3·log_artist_total_works_i
            + β4·spline(log_area_i)
            + β5..β14·title_emb_pca_0..9_i  (10 components)
            + ε_i
```

- Estimator: `sklearn.linear_model.HuberRegressor(epsilon=1.35, alpha=1e-4)` (운영 모델 동일)

### 2.3 Implementation
- 환경 pin: A.1-A.3 동일 + sentence-transformers 5.4.1 / transformers 5.8.0
- Random seed: 100-seed LAO + PCA random_state=42
- Code path: `experiments/structural_v1/feature_track_axis_a4.py` (신설)
- Embedding cache: `data/curated/title_embeddings_minilm_v1.npy` (8,495 × 384, ~13MB)
- Cluster bootstrap = A.1 v2 fix 그대로 사용

### 2.4 명시 배제 (HARK 회피)
- ❌ A.1/A.2/A.3 features (alternative hypothesis sequence)
- ❌ Interaction (위 §2.1.d)
- ❌ Per-segment encoding
- ❌ Embedding fine-tuning (pretrained 그대로)
- ❌ K 변경 (10 freeze)
- ❌ Hyperparameter tuning

### 2.5 Baseline 비교
- Baseline = `track2_v1_20260507` (F4 + spline + Huber, 운영 채택 모델)

### 2.6 Primary Hypothesis (단일, step-internal unadjusted)
- H₀: A.4 모델 overall MdAPE ≥ baseline
- H₁: A.4 모델 overall MdAPE < baseline AND 저가 harm 없음
- "unadjusted" = step-internal. Program-level cumulative = §2.10.

### 2.7 Practical Significance
- Δ ≤ -1.0%p
- **Cluster bootstrap 99% CI 상한 ≤ 0** (α=0.01 decision rule)

### 2.8 🔴 Hard Gate
- Δ_low ≤ 0%p (점추정 기준)
- 위반 시 즉시 FAIL

### 2.9 LAO Secondary Family (Holm m=3, supportive)
1. Low / Mid-high / Newly-warm MdAPE

### 2.10 Multiple Comparisons
- 5 step gatekeeping sequence
- A.4 step α = 0.01 (Bonferroni 5 step, FWER ≤ 0.05)

### 2.11 Stratification + Subgroup
- Price segment (low / mid-high) / Newly-warm

### 2.12 Canonical Artifact Triple
- Model hash (baseline): `track2_v1_20260507`
- Feature pipeline version: `feature_track_a4_v1_20260507`
- Train data hash: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5`
- **Embedding cache hash**: 실험 시작 시 `title_embeddings_minilm_v1.npy` SHA-16 (canonical, freeze)

## 3. PASS / BORDERLINE / FAIL 결정

### 3.1 PASS (운영 채택 후보)
- **Primary**: Δ ≤ -1.0%p AND 99% CI 상한 ≤ 0
- **🔴 Hard gate**: Δ_low ≤ 0%p
- → Phase 3 cold shadow 진입 검토 / A.5 진입 불필요

### 3.2 BORDERLINE (A.5 escalation)
- Hard gate ✓ AND -1.0 < Δ ≤ -0.3%p
- 또는 99% CI 상한 > 0 (점추정 ≤ -1.0%p)

### 3.3 FAIL (A.5 escalation)
- Hard gate 위반 — 즉시 FAIL
- 또는 Δ > -0.3%p

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Title 의 의미 신호 약함 가능 (`Untitled` 164회 등 generic title) | 정직 보고 — multilingual model 의 zero-shot inference 한계 |
| 384-dim → PCA K=10 reduction 의 정보 손실 | conservative dim (overfitting 방지) / K 변경 X (HARK 회피) |
| Embedding cache leakage 가능성 | 모든 작품 embedding 은 deterministic + title 본질 attribute → leakage X (시점 정합성 OK) |
| Compute / storage 비용 (heavy escalation) | one-time embedding (~1분) + 13MB cache / LAO loop 자체는 가벼움 |
| K=10 fixed 의 power 손실 | 정직 보고 — A.4 FAIL 시 K 변경 ablation = 새 cycle 의무 |

## 5. Step Gate (B안 확정)

```
A.1 BORDERLINE → A.2 FAIL → A.3 BORDERLINE (strongest) → **A.4 (text)** → A.5 (image)
```

## 6. 일정 (LLM-only 추정)

| 단계 | 일정 | 산출물 |
|---|---|---|
| Embedding cache 생성 | 5-10분 (one-time) | `data/curated/title_embeddings_minilm_v1.npy` |
| 본 prereg 코덱스 검수 (선택) | 1-2일 | freeze 확정 |
| `feature_track_axis_a4.py` 구현 | 0.5-1일 | 100-seed LAO + cluster bootstrap |
| 실험 실행 | 0.5일 | `results/feature_track_axis_a4.json` |
| 결과 보고서 + 코덱스 검수 | 1-2일 | `docs/feature_track_axis_a4_results_20260507.md` |

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track / A.1 prereg+결과 / A.2 prereg+결과 / A.3 prereg+결과) | P0×6 + P1×27 + P2×7 적용 |
| **A.4 prereg freeze (2026-05-07)** | A.1-A.3 v2 lessons 사전 반영 + heavy escalation 환경 pin |

## 8. 참조

- A.3 결과: `docs/feature_track_axis_a3_results_20260507.md` (BORDERLINE → A.4 escalation)
- Feature track design: `docs/feature_track_design_20260507.md`
- Methodology pipeline / Deviation log
