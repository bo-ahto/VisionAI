# V5 Cycle Plan — Image Retrieval Prior + GPBoost Mixed-Effects (2026-05-04)

> **다음 cycle (V5) 의 2주 실험 계획 + 사전등록 템플릿**
>
> 목적: v4 cycle 에서 도출된 "재현성 부족" 문제를 사전등록으로 방지하면서 cold-start 약점 (holdout MdAPE 40+) 을 직접 공략
>
> 코덱스 6차/7차 자문 채택. 우선순위 재조정: A (image retrieval prior) + C-lite (GPBoost) 조합.

## 1. 배경 — V4 cycle 에서 학습한 것

| Lesson | V5 적용 |
|---|---|
| Selection bias (탐색+평가 같은 fold) | Inner Optuna 5-fold + outer holdout 분리 표준화 |
| Capacity vs feature effect 혼재 | Fixed hyperparameter incremental baseline 의무화 |
| KFold artist leakage | LAO (leave-artist-out) split 표준 |
| Single split 비재현 | Repeated 3-seed holdout 표준 |
| Cherry-picking 위험 | **사전등록** (pre-registration) 의무화 |

## 2. 우선순위 (코덱스 6차 자문 결과)

1. **A. 이미지 retrieval prior** (visual kNN prior, end-to-end CV 아님)
2. **C-lite. GPBoost / mixed-effects** (sequential residualization)
3. ~~D. 텍스트 embedding~~ — 다음 cycle
4. ~~E. Conformal~~ — 별도 트랙
5. ~~B. TabPFN~~ — challenger only (28K 는 sweet spot 아님)
6. ~~F. Multi-task~~ — 다음 cycle
7. ~~G. Active learning~~ — 다음 cycle

## 3. 핵심 운영 원칙 (코덱스 권고)

> 1. A와 C-lite 를 **독립적으로 kill/pass** (동시에 키우지 않음)
> 2. A는 **cold-start 개선이 없으면 즉시 중단**
> 3. C-lite는 **seen-artist 개선이 있어도 cold-start 깎으면 보류**

## 4. 2주 실험 계획표

### Week 1 — Image Retrieval Prior 진단 + PoC

| Day | 작업 | Pass | Fail (Stop) |
|---|---|---|---|
| 1 | LAO split 구축 + DINOv2-base embedding 추출 | artist_slug overlap=0 (**hard gate**) | overlap 1건이라도 있으면 즉시 재설계 |
| 2 | Embedding 인덱스 + retrieval pipeline 구축 | extraction/runtime 현실적 | 비현실적 → 2일 내 PoC 불가, cut |
| 3 | image-only / retrieval-stat-only 평가 + NN sanity check (50-100건 수기) | image-only 또는 retrieval-stat-only ≥ 1개가 baseline 대비 개선, NN 무관 비율 ≤ 20%, duplicate ≤ 2% | 둘 다 무신호 + duplicate/leakage 의심 |
| 4 | Memorization audit + cluster-conditional variance | same-artist 제거 후 gain 50%+ 유지, n≥30 cluster 과반에서 IQR -10%+ | gain 대부분이 same-artist 의존 / cluster 분산 무차이 |
| 5 | Retrieval 통계 features → baseline 통합 (NN_median, NN_IQR, distance-weighted, same-medium share, local density) | cold-start 3 seeds 모두 같은 방향, mean ≥ 3% 또는 ≥ 0.8pp | 방향 불일치 / noise / segment fairness 악화 |
| 6-7 | A gate 결정 + 문서화 | 사전 정의 gate 충족 → PR-data-feature 준비 | gate 미충족 → cut + Week 2를 C-lite 단독 검증으로 전환 |

### Week 2 — C-lite + 통합 Ablation

| Day | 작업 | Pass | Fail (Stop) |
|---|---|---|---|
| 8-9 | C-lite sequential residualization PoC (`y_hat_baseline + b_artist`) | seen-artist 안정적 개선, unseen 거의 무영향 | seen-artist gain noise 또는 cold-start 악화 |
| 10 | C-lite tuning 최소화 검증 | 3 seeds 같은 방향, std 낮음 | seed 민감도 큼, runtime > 4x baseline |
| 11-12 | 통합 ablation (후보 1: A 단독, 후보 2: C-lite 단독, 후보 3: A+C 결합) | full 이 단독 best 보다 추가 가치, fairness 악화 X | full 무가치 / 복잡도 대비 gain 부족 |
| 13 | Confirmatory run (finalist 1-2개 동일 budget 재평가) | gate 재충족 | 재현 실패 |
| 14 | merge / go / no-go 결정 | data PR / eval PR / model PR 각각 merge 조건 충족 | 미통과 PR 보류 |

## 5. Pass/Fail Gates (사전 확정)

### A Pass
- Cold-start mean ΔMdAPE ≤ **-max(0.8pp, baseline의 3%)**
- 3/3 seeds 같은 방향
- Seed std ≤ 0.6pp
- 다른 segment 악화 ≤ +1.0pp

### C-lite Pass
- Seen-artist mean ΔMdAPE ≤ **-max(0.5pp, baseline의 2%)**
- 3/3 seeds 같은 방향
- Cold-start 악화 ≤ +0.5pp
- Tail (P90 APE) 악화 없음
- Runtime ≤ 4x baseline

### 통합 Pass
- Overall ΔMdAPE ≤ -max(0.8pp, 3%)
- Cold-start gain ≥ 80% of A 단독 유지
- Seen-artist gain ≥ 80% of C-lite 단독 유지
- Max segment degradation ≤ +1.0pp

## 6. 모델 / 도구 선택 (코덱스 권고)

### 이미지 Embedding
1순위: **DINOv2-base** (M2 Mac MPS 적합, retrieval 직접적, 텍스트 의존 X)
2순위 challenger: CLIP
3순위 challenger: CLIP-Art (CVPRW 2021)

→ DINOv2-base 시작, fail 시만 CLIP-Art

### C-lite
- **GPBoost** (Sigrist 2022, JMLR) — Native Python API, scikit wrapper 비추천
- **Sequential residualization** (joint optimization 보류)
- CPU 기준 (GPU/MPS 기대 X)
- Runtime budget: 1.5x ~ 4x CatBoost

## 7. 검증 Framework (V4 학습 + 코덱스 추가)

| 항목 | 정의 |
|---|---|
| Split | Artist-level GroupShuffleSplit 80/20 |
| Repeats | 3 seeds (사전 고정) |
| Inner CV | KFold 5-fold (Optuna 시) |
| Outer eval | Holdout 80%-trained → 20% holdout |
| Modality leakage | PCA / tokenizer / embedding norm / neighbor index 전부 split 내 train fit only |
| Incremental baseline | (1) production candidate (2) same learner same hparams without new modality |
| 사전등록 segment | 0-shot/1-3/4-10/10+ × Artsy/Saatchi × price tercile × career_stage avail (4×2×3×2 = 48 cell) |
| Cell drop rule | n < X 시 underpowered 표시 + pass/fail 해석 제외 (X 는 첫 run 전 확정) |

## 8. PR 분할 + Merge 순서 (코덱스 권고)

| 순서 | PR | 내용 | Merge 조건 |
|---|---|---|---|
| 1 | **PR-eval-framework** | LAO split + cold-start segment + repeated 3-seed + 사전등록 markdown | 모델 성능 무관, 평가 일관성 개선이면 즉시 merge |
| 2 | **PR-data-feature** | image embedding + retrieval index + retrieval stats | A pass 시만, leakage audit 통과 |
| 3 | **PR-model** | GPBoost / C-lite integration | C-lite pass + unseen artist degradation 제한 + runtime acceptable + fallback off-switch |

## 9. 사전등록 템플릿 (PR-eval-framework merge 시 함께 commit)

> **사용 방법**: V5 cycle 시작 시 빈칸 채워서 `docs/v5_cycle_사전등록_확정.md` 으로 commit. 이후 변경은 deviation log 에 기록.

```markdown
# V5 Cycle Pre-registration

## 0) Metadata
- Cycle: V5
- Date: ____
- Owners: ____
- Related PR:
  - Eval framework PR: ____
  - Experiment PR(s): ____
- Baseline (fixed): v3-filtered_tuned (CatBoost+XGBoost ensemble, 32 features)
- Scope (pre-registered): A (image retrieval prior), C-lite (GPBoost mixed-effects), A+C-lite
- Out of scope unless deviation logged: 새 model family / 새 segment 정의 / 추가 tuning round / 새 holdout scheme

## 1) Hypotheses
### A. Image Retrieval Prior
- H_A1: ____
- H_A2: ____
- H_A3: ____

### C-lite. Mixed-effects
- H_C1: ____
- H_C2: ____
- H_C3: ____

### Full Integration
- H_Full1: ____
- H_Full2: ____
- H_Full3: ____

## 2) Validation Setup
- Primary split: artist-level 80/20 holdout
- Repeats: 3 seeds, pre-fixed: seed_1=____, seed_2=____, seed_3=____
- Hyperparameter policy:
  - Baseline: fixed
  - A: pre-specified only
  - C-lite: pre-specified only
  - 평가 후 추가 튜닝 금지 (deviation 로그 시만 허용)
- Comparison units:
  - Baseline vs A
  - Baseline vs C-lite
  - Baseline vs A + C-lite

## 3) Metrics
### Primary
- Cold-start MdAPE (artist-level holdout)

### Secondary
- Overall MdAPE / Seen-artist MdAPE / W30 / W50 / MAE
- Segment-wise MdAPE for all pre-registered segments
- Optional diagnostic-only:
  - prediction variance across seeds
  - coverage / missingness-sensitive subgroup counts

## 4) Pre-registered Segments
- Exposure: 0-shot, 1-3, 4-10, 10+
- Marketplace: Artsy, Saatchi
- Price: tercile 1/2/3
- Career stage: available, missing
- Full grid: 4×2×3×2 = 48 cells
- Cell drop: n < X = ____ 시 dropped (underpowered) 표시 + pass/fail 제외
- Mandatory aggregates:
  - By exposure
  - By marketplace
  - By price tercile
  - By career stage
- Post-hoc segment 추가/경계 변경 금지 (deviation 로그 시만 허용)

## 5) Pass / Fail Gates
[§5 위 표 그대로]

## 6) Stop Conditions
- A cut: Day 4 진단 ≥2 fail
- A cut: seed instability
- C-lite cut: seed 민감도 큼 / direction 불안정
- C-lite cut: 추가 튜닝 후만 개선 (사전등록 외)
- Integration cut: 단독 gain 결합 후 사라짐 / segment 악화 초과
- 모든 결과 관찰 후 retry/retune/re-split 은 post-hoc

## 7) Analysis Plan
- Main comparisons: Baseline vs A / vs C-lite / vs A+C-lite
- Estimands:
  - Mean ΔMdAPE across 3 seeds
  - Segment-wise ΔMdAPE
- Uncertainty:
  - 95% bootstrap CI on primary metric Δ
  - Paired seed-wise (descriptive)
- Decision rule: 사전등록 gate 우선, 통계 검증 supportive
- Mandatory: primary + secondary + mandatory aggregates + all 48 cells (dropped 포함, 이유 명시)
- Forbidden post-hoc:
  - best seed cherry-pick
  - baseline 결과 본 후 교체
  - 좋은 segment 만 보고
  - bucket 경계 사후 변경

## 8) Deviation Log
| Date | Item changed | Why | Pre-registered/Post-hoc | Expected impact | Approved by |
|---|---|---|---|---|---|
| YYYY-MM-DD | | | | | |

## 9) Governance / Review Linkage
- 본 사전등록 파일은 PR-eval-framework 와 함께 merge
- merge 후 변경 시:
  - PR diff (markdown)
  - linked commit
  - short ADR / decision note
- Result write-up:
  - Pre-registered findings 와 Post-hoc exploration 분리

## 10) Deviation Risk Controls
- A 가 unexpectedly 큰 gain → 추가 ablation 은 post-hoc only, pass/fail 변경 X
- C-lite fail → 추가 hyperparameter search 는 사전등록 결과로 X (새 cycle 시 가능)
- Segment 정의 missingness 로 비현실 → 원 정의 보고 유지, fallback 은 additive 로만
```

## 10. References (코덱스 7차 자문)

| 영역 | 출처 |
|---|---|
| TabPFN Nature 2025 | https://www.nature.com/articles/s41586-024-08328-6 |
| TabPFN GitHub | https://github.com/PriorLabs/TabPFN |
| GPBoost JMLR 2022 | https://www.jmlr.org/papers/v23/20-322.html |
| GPBoost Python docs | https://gpboost.readthedocs.io/en/latest/Python_package.html |
| GPBoost Parameters | https://gpboost.readthedocs.io/en/latest/Parameters.html |
| Conformalized Quantile (NeurIPS'19) | https://papers.neurips.cc/paper/2019/hash/5103c3584b063c431bd12689b5e76fb-Abstract.html |
| DINOv2 (TMLR'24) | https://openreview.net/forum?id=a68SUt6zFt |
| DINOv2 base model | https://huggingface.co/facebook/dinov2-base |
| CLIP-Art (CVPRW'21) | https://huggingface.co/papers/2204.14244 |
| Visual feature 한계 (Sci Reports'24) | https://www.nature.com/articles/s41598-024-60957-z |

## 11. Cycle 시작 시점 (TBD)

본 plan 은 다음 시점에 시작:
- 박지연님 본 마이그레이션 데이터 도착 + 신규 미매칭 갤러리 검수 일괄 완료
- 또는 별도 일정 블록 (2주 연속 가용)

선행 가능 작업:
- DINOv2 환경 setup (Python 패키지 설치)
- GPBoost 환경 setup
- LAO split 코드 (eval framework PR 사전 작성)

## 12. 코덱스 자문 기록

| 회차 | 주제 | 결론 |
|---|---|---|
| 1차 | V4 plan 적정성 | Selection bias 우려, CSV 외부화 |
| 2차 | Mixed ablation | Source proxy (가설 D) — 후속 부정 |
| 3차 | 5개 검증 추가 | XGBoost 후보 변경 → fairness 재검증 |
| 4차 | Reversal 결과 | repeated holdout 1순위 |
| 5차 | Repeated holdout | **P + Saatchi veto** (V4 종결) |
| 6차 | V5 방향 리서치 | A + C-lite 권고 (B 하락) |
| 7차 | V5 2주 plan + 사전등록 | 본 문서 |
