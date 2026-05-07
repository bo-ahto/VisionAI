# Feature Track Axis A.3 — Geometry Pre-registration

> **작성일**: 2026-05-07 (freeze)
> **위치**: 새 Phase 2'' Axis A 의 **A.3 cheap falsification step (escalation from A.2 FAIL)**
> **연계**: `docs/feature_track_axis_a2_results_20260507.md` (A.2 FAIL → A.3 escalation, Step gate B안) / `docs/feature_track_axis_a1_prereg_20260507.md` (Step sequence + α=0.01 99% CI operationalization) / `docs/feature_track_design_20260507.md` (axis 설계)

> ⚠️ **연구 목적**: A.2 FAIL (Hard gate +0.05%p) 후 step gate B안에 따라 **artwork-level geometry features 추가 시 cold-start LAO 개선 가능?** 평가. **Cheap falsification step continuation** + working hypothesis "cross-artist applicable signal 이 cold-start LAO 에서 유효 가능성" 의 더 직접적 falsification.

> **본 prereg freeze**: 가설 / metric / family / PASS 기준 / per-step freeze 6항목 = **2026-05-07 freeze**. 결과 본 후 변경 X (HARK 회피).

> **A.1/A.2 v2 lessons 사전 반영**:
> 1. Cluster bootstrap 진짜 구현 (artist 별 indices 사전 매핑 + with replicas)
> 2. α=0.01 (Bonferroni 5 step) operationalization = 99% CI 상한 ≤ 0 (95% CI 참고만)
> 3. Per-step freeze 6항목 (a-f) — encoding spec 한 줄씩
> 4. 운영 spec 인용 정확성 (§1-§16 cold rollout default + §3 guardrail_low_price, §17 warm-only 와 분리)
> 5. Framing 톤 — "promising/FAIL" but **메커니즘 결론은 working hypothesis** (다음 step 에서 재시험)

## 1. Input / Hypothesis

### 1.1 A.2 결과 input
- A.2 100-seed mean: overall -0.21%p / 저가 +0.05%p ✗ hard gate (즉시 FAIL) / mid-high -0.47%p / newly-warm -0.81%p
- A.2 99% CI 상한 +4.47%p — α=0.01 미달
- 코덱스 framing: "A.2 bundle failed under cold-start LAO; broader mechanism claims remain provisional"
- → A.3 escalation, A.2 features drop (alternative hypothesis sequence)

### 1.2 A.3 Hypothesis
> **운영 모델 F4 + spline 에 artwork-level geometry features 3종 추가 시 cold-start LAO MdAPE 개선 + 저가 segment harm 0?**
>
> **A.3 가 추가하는 신호**: 작품의 형태 (aspect ratio = 가로/세로 비율) / 차원성 (2D vs 3D) / 깊이 (3D 작품의 depth). **모두 artwork-level cross-artist applicable signal** — A.1 working hypothesis ("cross-artist signal 이 cold-start LAO 에서 유효 가능성") 의 더 직접적 falsification step.

### 1.3 시점 정합성 (코덱스 P1)
- `width_cm` / `height_cm` / `depth_cm` = **작품의 본질 attribute** (작품 자체 기록 시점에 결정, scrape/sale 시점 무관) → **시점 정합성 명확 OK**
- A.2 의 single-snapshot caveat 무관 (artist-binding 아닌 artwork-binding)

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Per-step freeze 6항목

#### (a) Feature set — 3종 final

| Feature | Type | Missing | 비고 |
|---|---|---|---|
| `log_aspect_ratio` | numeric | 0% | 모든 작품 적용 (가로/세로 비율) |
| `is_3d` | boolean | 0% | 2D (depth NaN or 0) vs 3D (depth ≥ 1) indicator |
| `log_depth_3d` | numeric | 71.7% missing → 0 (2D) | 3D 작품에만 의미, 2D 는 0 (is_3d=0 와 정합) |

> **Inventory 분포 (사전 freeze)**: 2D = 6,088 (71.7%), 3D = 2,407 (28.3%) — full data set 기반.

#### (b) Encoding — spec freeze (한 줄씩)

- **`log_aspect_ratio`**: `np.log(width_cm) - np.log(height_cm)` — 모든 작품 적용. width_cm / height_cm 가 1 이상 (data range min=1) 이므로 log safe / numeric column 1개
- **`is_3d`**: `(depth_cm.notna() & (depth_cm > 0))` → boolean → float (1.0/0.0) / numeric column 1개
- **`log_depth_3d`**: `np.log(depth_cm)` if `is_3d else 0.0` (2D 작품 = 0, 3D 작품 = log_depth) / numeric column 1개
  - 효과적으로 `is_3d × log_depth` interaction 형태 — but **본 spec 은 single column 으로 명시**, 별도 interaction 추가 X

> **Implementation note**: log_depth_3d 의 (2D=0) 처리 시 log(0) 회피 — `np.where(is_3d, np.log(depth_cm), 0.0)` 사용 / NaN → 0.0 사전 처리

#### (c) Preprocessing
- Missing imputation:
  - `width_cm` / `height_cm` 0% missing — imputation 불필요
  - `depth_cm` 71.7% missing → `is_3d=0` 처리 (NaN 자체를 indicator 로 활용)
- Outlier handling: Huber regression 자체로 처리 (운영 모델과 동일)
- Standardization: 운영 모델과 동일 (raw numeric — Huber 가 robust)

#### (d) Interaction 허용 범위 — **NONE** (additive only)
- ❌ `is_low` × feature interaction
- ❌ feature × feature interaction (is_3d × log_aspect_ratio 등)
- ❌ Polynomial / spline of new features (log_area spline 은 운영 baseline 그대로)
- ❌ Per-segment encoding
- 단 `is_3d × log_depth` 의 효과 = log_depth_3d encoding 자체에 내포 (별도 항 X)

#### (e) Stop/go rule (LAO primary family)
- **PASS**: Δ ≤ -1.0%p AND **Cluster bootstrap 99% CI 상한 ≤ 0 (α=0.01 decision rule)** AND Hard gate Δ_low ≤ 0%p → 운영 채택 후보 (이후 A.4 진입 불필요)
- **BORDERLINE**: -1.0 < Δ ≤ -0.3%p AND Hard gate ✓ → A.4 escalation
- **FAIL**: Δ > -0.3%p OR Hard gate 위반 → A.4 escalation (B안)

#### (f) 다음 step (alternative hypothesis sequence)
- A.3 FAIL/BORDERLINE 시 → **A.4 (title text embedding, multilingual BERT) 로 escalation**
- **A.4 prereg 에서 A.3 features 전부 drop** (alternative hypothesis sequence)
- A.4 의 baseline = 운영 모델 F4
- **Inferential family = program-level cumulative** (5 step Bonferroni α=0.01, FWER ≤ 0.05)
- A.4 = first heavy escalation (text embedding compute / storage 비용 ↑) — 자원 계획 의무

### 2.2 Primary Model

```
log_price_i = β0 + β1·log_area_i + β2·birth_year_centered_i + β3·log_artist_total_works_i
            + β4·spline(log_area_i)
            + β5·log_aspect_ratio_i
            + β6·is_3d_i
            + β7·log_depth_3d_i
            + ε_i
```

- Estimator: `sklearn.linear_model.HuberRegressor(epsilon=1.35, alpha=1e-4)` (운영 모델 동일)
- Loss: Huber (운영 spec §1-§16 cold rollout default, §17 warm-only 와 분리)

### 2.3 Implementation
- 환경 pin: A.1/A.2 동일 (Python 3.14 / scikit-learn / numpy / pandas)
- Random seed: 100-seed LAO (Stage 3 / 6A / 6B / A.1 / A.2 동일 seed range 0-99)
- Code path: `experiments/structural_v1/feature_track_axis_a3.py` (신설)
- Train data: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5` (변경 X)
- **Cluster bootstrap = A.1 v2 fix 그대로 사용** (artist 별 indices 사전 매핑 + sample 별 concatenate with replicas)

### 2.4 명시 배제 (HARK 회피)
- ❌ A.1 features (category / attribution_class / gallery_name / gallery_cities) — alternative hypothesis sequence
- ❌ A.2 features (popularity / for_sale / is_p1 / year_made_centered) — alternative hypothesis sequence
- ❌ Interaction (위 §2.1.d)
- ❌ Per-segment encoding
- ❌ A.4 / A.5 features (text / image embedding)
- ❌ Hyperparameter tuning

### 2.5 Baseline 비교
- Baseline = `track2_v1_20260507` (F4 + spline + Huber, 운영 채택 모델, A.1/A.2 features 미사용)

### 2.6 Primary Hypothesis (단일, step-internal unadjusted)
- H₀: A.3 모델 overall MdAPE ≥ baseline (Stage 3 100-seed mean = 38.05%)
- H₁: A.3 모델 overall MdAPE < baseline AND 저가 harm 없음
- "unadjusted" = step-internal. Program-level cumulative = §2.10.

### 2.7 Practical Significance
- Δ ≤ -1.0%p (운영 채택 임계, 동일)
- **Cluster bootstrap 99% CI 상한 ≤ 0** (α=0.01 Bonferroni 5 step decision rule)

### 2.8 🔴 Hard Gate
- Δ_low ≤ 0%p (점추정 기준)
- 운영 spec §3 `guardrail_low_price` 와 정합
- 위반 시 즉시 FAIL

### 2.9 LAO Secondary Family (Holm m=3, supportive)
1. Low (`price_krw < 5,000,000`) MdAPE
2. Mid-high (`price_krw ≥ 5,000,000`) MdAPE
3. Newly-warm (Stage 3 cohort 외) MdAPE

### 2.10 Multiple Comparisons (program-level α 분배)
- 5 step gatekeeping sequence: A.1 → A.2 → A.3 → A.4 → A.5
- **A.3 step α = 0.01** (Bonferroni 5 step, FWER ≤ 0.05)
- 99% CI 상한 ≤ 0 = decision rule

### 2.11 Stratification + Subgroup
- Price segment: low / mid-high (§2.8 hard gate)
- Newly-warm: not in Stage 3 cohort

### 2.12 Canonical Artifact Triple
- Model hash (baseline): `track2_v1_20260507`
- Feature pipeline version: `f4_spline_v1_20260506` + A.3 features = `feature_track_a3_v1_20260507`
- Train data hash: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5`

## 3. PASS / BORDERLINE / FAIL 결정

### 3.1 PASS (운영 채택 후보)
- **Primary**: Δ ≤ -1.0%p AND Cluster bootstrap **99% CI** 상한 ≤ 0
- **🔴 Hard gate**: Δ_low ≤ 0%p
- → Phase 3 cold shadow 진입 검토 / A.4 진입 불필요

### 3.2 BORDERLINE (A.4 escalation)
- 🔴 Hard gate ✓ AND Primary -1.0 < Δ ≤ -0.3%p
- 또는 Primary 점추정 ≤ -1.0%p but **99% CI** 상한 > 0
- → A.4 prereg 진입 (A.3 features drop)

### 3.3 FAIL (A.4 escalation)
- 🔴 Hard gate 위반 (Δ_low > 0) — 즉시 FAIL
- 또는 Primary Δ > -0.3%p
- → A.4 prereg 진입 (B안)

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| `log_aspect_ratio` 의 outlier (extreme aspect 작품) | Huber regression 자체로 robust / log transform 으로 약화 |
| 71.7% 2D 작품 — `is_3d` / `log_depth_3d` 의 informative 정도 약함 가능 | 정직 보고 (28.3% 3D 만 informative) — A.3 FAIL 시 cheap-feature ladder 종료 / A.4 escalation |
| `log_area` 와 redundancy (width × height ≈ area) | width / height = area 의 분해 / aspect ratio = area 와 직교 (shape signal) — informative |
| Step α=0.01 의 power 손실 | 정직 보고 (A.1 동일) |
| A.3 PASS but 운영 spec 변경 부담 | offline PASS → Phase 3 cold shadow gate (§4.0 calibration shadow KPI 형식) → canary |

## 5. Step Gate (B안 확정, A.1/A.2 동일)

```
A.1 (cheap categorical 4종) — BORDERLINE (2026-05-07)
  ↓
A.2 (artist popularity 4종) — FAIL (2026-05-07)
  ↓
**A.3 (geometry 3종)** — 본 prereg
  ↓ FAIL/BORDERLINE
A.4 (title text embedding, multilingual BERT) ← first heavy escalation
  ↓ FAIL/BORDERLINE
A.5 (image embedding, CLIP/ResNet)
  ↓ FAIL
Axis A 전체 종료 → Axis B 또는 program-level 재설계
```

## 6. 일정 (LLM-only 추정)

| 단계 | 일정 | 산출물 |
|---|---|---|
| 본 prereg 코덱스 검수 (선택) | 1-2일 | freeze 확정 |
| `feature_track_axis_a3.py` 구현 | 0.5일 (A.1/A.2 코드 기반 derivative) | 100-seed LAO + cluster bootstrap |
| 실험 실행 | 0.5일 | `results/feature_track_axis_a3.json` |
| 결과 보고서 + 코덱스 검수 | 1-2일 | `docs/feature_track_axis_a3_results_20260507.md` |
| 의사결정 | 1일 | A.4 escalation 또는 운영 채택 후보 |

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B / Feature track design / A.1 prereg / A.1 결과 / A.2 prereg / A.2 결과 | 누적 P0×6 + P1×24 + P2×6 적용 |
| **본 A.3 prereg freeze (2026-05-07)** | A.1/A.2 v2 lessons 사전 반영 + framing 톤 |

## 8. 참조

- A.1 prereg / 결과 / A.2 prereg / 결과 / Feature track design / Stage 6B close
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
