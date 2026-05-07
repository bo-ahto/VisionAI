# Feature Track Axis A.5 — Image Embedding Pre-registration

> **작성일**: 2026-05-07 (freeze)
> **위치**: 새 Phase 2'' Axis A 의 **A.5 heaviest escalation step (마지막 step in Axis A)**
> **연계**: `docs/feature_track_axis_a4_results_20260507.md` (A.4 FAIL → A.5 진입 — 사용자 명시 instruction, 코덱스 권고 = HOLD) / `docs/feature_track_axis_a1_prereg_20260507.md` (Step sequence + α=0.01 99% CI operationalization) / `docs/feature_track_design_20260507.md` (axis 설계)

> ⚠️ **A.5 진입 의사결정 근거 (코덱스 권고와 분리 명시)**:
> - **코덱스 권고 (A.4 결과 검수)**: A.5 HOLD / Axis A 종료 — A.4 가 axis 내 최악 (전체 악화 + low hard-gate 위반 + 75/100 violation), heavier-dim image embedding 의 기대값 낮음
> - **본 prereg 진행 근거**: 사용자 명시 instruction (2026-05-07) — "코덱스 검수 후 A.5 진행"
> - **Procedural vs Management recommendation 분리** (A.4 v2 코덱스 P1 권고): 본 prereg = procedural Axis A 종결 step, hypothesis 자체를 끝까지 닫기 위함 / management recommendation 으로는 HOLD 가 더 ROI 적합 가능

> **연구 목적**: A.4 FAIL 후 image embedding (CLIP-ViT-B-32) 추가 시 cold-start LAO 개선 가능? 평가. **Heaviest escalation** + **Axis A 마지막 step** — 결과에 따라 Axis A 전체 종결.

> **A.1-A.4 v2 lessons 사전 반영**: cluster bootstrap 진짜 구현 / α=0.01 99% CI decision / per-step freeze 6항목 / 운영 spec 인용 정확성 / framing 톤 (working hypothesis, frozen spec fails 명시) / procedural vs management recommendation 분리

## 1. Input / Hypothesis

### 1.1 A.4 결과 input
- A.4 FAIL: overall +0.66%p / low +1.22%p (hard gate 위반) / 75/100 violation
- A.3 strongest / A.4 worst — working hypothesis "artwork-level cross-artist signal 일반 유효" 단순 확장 미지지 (반증 X)
- Provisional gap: A.3 의 signal 이 geometry-specific 가능성 / 또는 dim 증가 risk
- → A.5 = image (heavier dim) 으로 hypothesis 끝까지 시험

### 1.2 A.5 Hypothesis
> **운영 모델 F4 + spline 에 image embedding (CLIP-ViT-B-32, PCA top-K) 추가 시 cold-start LAO MdAPE 개선 + 저가 segment harm 0?**
>
> **A.5 가 추가하는 신호**: 작품의 시각 정보 (색상 / 구성 / 매체 특성 / 추상도 등). **artwork-level cross-artist applicable signal** — A.3 working hypothesis 의 final confirmation step.

### 1.3 시점 정합성 (코덱스 P1)
- `image_url` = 작품 본질 attribute, scrape/sale 시점 무관 → **시점 정합성 명확 OK** (A.3/A.4 동일)

### 1.4 사전 expectation (정직 보고)
- 코덱스 권고 = A.5 GO ROI 의문 (A.4 dim sensitivity 가설 적용 시 heavier dim 도 유사 FAIL risk)
- A.5 의 사전 expectation = **FAIL/BORDERLINE 가능성 ↑**
- 본 prereg 진입 = hypothesis 끝까지 시험하는 procedural step (HARK 회피 — 결과 본 후 변경 X)

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Per-step freeze 6항목

#### (a) Feature set — image embedding PCA top-K

| Feature | Source | Encoding |
|---|---|---|
| `image_emb_pca_0` ~ `image_emb_pca_K-1` | `image_url` column | CLIP-ViT-B-32 embedding → PCA top-K |

> **K = 10 final** (A.4 동일 — consistency, conservative dim).

#### (b) Encoding — spec freeze (한 줄씩)

- **Embedding model**: `sentence-transformers/clip-ViT-B-32`
  - Version pin: sentence-transformers 5.4.1 / transformers 5.8.0
  - Embedding dim: 512
  - Pretrained, fine-tuning X
  - Multimodal (image + text), image-only encoding 사용
- **Image fetch**:
  - Source: `image_url` (Artsy CloudFront CDN)
  - Method: `urllib.request` with User-Agent header / 10s timeout
  - Concurrent: ThreadPoolExecutor (max_workers=20) — single CDN, conservative
  - Cache: `data/curated/images_cache/{artwork_id}.jpg` (skip if exists)
  - Failure handling: 13 null URLs + fetch failures → **zero embedding (512-dim 0 vector)** 명시 spec
- **CLIP encode**:
  - Batch size 64
  - PIL Image (RGB conversion)
  - Output: `data/curated/image_embeddings_clipvitb32_v1.npy` (8,495 × 512)
- **PCA**:
  - K = 10 (A.4 동일)
  - Fit on train fold only (LAO 별)
  - Apply to test fold (transform with train PCA components)
  - Implementation: `sklearn.decomposition.PCA(n_components=10, random_state=42)`

#### (c) Preprocessing
- Missing imputation:
  - 13 null `image_url` → zero 512-dim embedding
  - Fetch failures → zero 512-dim embedding (failed_image_count 보고 의무)
- Outlier handling: Huber regression (운영 모델과 동일)
- Standardization: 운영 모델과 동일

#### (d) Interaction 허용 범위 — **NONE** (additive only, A.1-A.4 동일)

#### (e) Stop/go rule (LAO primary family)
- **PASS**: Δ ≤ -1.0%p AND **99% CI 상한 ≤ 0 (α=0.01)** AND Hard gate Δ_low ≤ 0%p
- **BORDERLINE**: -1.0 < Δ ≤ -0.3%p AND Hard gate ✓ → **Axis A 전체 종료** (마지막 step)
- **FAIL**: Δ > -0.3%p OR Hard gate 위반 → **Axis A 전체 종료** (마지막 step)

#### (f) 다음 step (alternative hypothesis sequence)
- A.5 PASS 시: 운영 채택 후보 / Axis A 종결
- A.5 FAIL/BORDERLINE 시: **Axis A 전체 종료** (마지막 step) → Axis B (Phase A pre-screen 통과 시) 또는 program-level 재설계 / A.3 단독 shadow 검토 (별도 의사결정 gate)
- Inferential family = program-level cumulative (5 step Bonferroni α=0.01, FWER ≤ 0.05) — A.5 가 마지막 step

### 2.2 Primary Model

```
log_price_i = β0 + β1·log_area_i + β2·birth_year_centered_i + β3·log_artist_total_works_i
            + β4·spline(log_area_i)
            + β5..β14·image_emb_pca_0..9_i  (10 components)
            + ε_i
```

- Estimator: `HuberRegressor(epsilon=1.35, alpha=1e-4)`
- Loss: Huber (운영 spec §1-§16 cold rollout default)

### 2.3 Implementation
- 환경 pin: A.4 동일 + image fetch (urllib) + PIL (Pillow)
- Random seed: 100-seed LAO + PCA random_state=42
- Code path: `experiments/structural_v1/feature_track_axis_a5.py`
- Cache: image jpg files + 512-dim embedding npy

### 2.4 명시 배제 (HARK 회피)
- ❌ A.1/A.2/A.3/A.4 features
- ❌ Interaction
- ❌ Per-segment encoding
- ❌ Embedding fine-tuning
- ❌ K 변경 (10 freeze)
- ❌ Hyperparameter tuning

### 2.5 - 2.12 (A.4 동일 spec)
- Baseline = `track2_v1_20260507`
- Primary hypothesis: 단일 step-internal unadjusted
- Practical Δ ≤ -1.0%p
- 🔴 Hard gate Δ_low ≤ 0%p (즉시 FAIL trigger)
- LAO Secondary Holm m=3 (low / mid-high / newly-warm)
- Multiple comparisons: α=0.01 (Bonferroni 5 step)
- Canonical artifact: `feature_track_a5_v1_20260507` + image cache hash

## 3. PASS / BORDERLINE / FAIL (Axis A 마지막 step)
- PASS → Axis A 종결, A.5 운영 채택 후보
- BORDERLINE → Axis A 종료, A.3 단독 shadow 검토 vs Axis B 진입 (의사결정 gate)
- FAIL → Axis A 종료, 동일 의사결정 gate

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Image fetch 실패 (Cloudflare 차단 등) | Stage 5 와 다른 path — image URL = CloudFront CDN 직접 / pilot test 통과 (1.11s, 79KB) / 실패 image = zero embedding (failed count 보고) |
| 8,482 image fetch 시간 (~25-30분) | concurrent download (max_workers=20) / one-time cache / 재실험 시 cache hit |
| 700MB image storage | gitignored / data/curated/images_cache/ 분리 / 사용자 환경 disk space 확인 |
| Heavy compute / dim 384→10 reduction (A.4 와 동일) | 정직 보고 — A.4 FAIL 패턴 반복 가능성 명시 |
| A.5 PASS 시 운영 spec 변경 부담 + image inference latency | offline PASS → Phase 3 cold shadow gate / inference latency 별도 평가 의무 |

## 5. Step Gate (B안 — A.5 마지막 step)

```
A.1 BORDERLINE → A.2 FAIL → A.3 BORDERLINE → A.4 FAIL → **A.5 (image, 마지막)**
  ↓ FAIL/BORDERLINE → Axis A 전체 종료 → Axis B 또는 A.3 단독 shadow / program-level 재설계
  ↓ PASS → A.5 채택 후보 / Axis A 종결
```

## 6. 일정 (LLM-only 추정)

| 단계 | 일정 | 산출물 |
|---|---|---|
| Image fetch + CLIP encode (one-time) | 30-60분 | `data/curated/image_embeddings_clipvitb32_v1.npy` (~17MB) |
| `feature_track_axis_a5.py` 구현 | 0.5-1일 | 100-seed LAO + cluster bootstrap |
| 실험 실행 | 0.5일 | `results/feature_track_axis_a5.json` |
| 결과 보고 + 코덱스 검수 | 1-2일 | `docs/feature_track_axis_a5_results_20260507.md` |
| Axis A 종합 결정 | 1일 | A.5 결과 + 사용자 의사결정 (운영 채택 / Axis B / shadow / 재설계) |

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track design / A.1-A.4 prereg+결과) | P0×6 + P1×33 + P2×10 적용 |
| **A.5 prereg freeze (2026-05-07)** | A.1-A.4 v2 lessons + procedural vs management recommendation 분리 명시 |

## 8. 참조

- A.4 결과: `docs/feature_track_axis_a4_results_20260507.md` (FAIL → A.5 진입 사용자 명시 / 코덱스 HOLD 권고)
- A.1-A.3 prereg+결과 / Feature track design / Stage 6B close
- Methodology pipeline / Deviation log
