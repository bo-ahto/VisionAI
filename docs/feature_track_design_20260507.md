# Feature Track Design (Draft) — Architecture-Only Close 후속

> **작성일**: 2026-05-07
> **상태**: **Draft** — 의사결정자 우선순위 결정 + axis 선택 후 prereg 진입
> **연계**: `docs/stage6b_results_20260507.md` (6B FAIL → architecture-only close), `docs/stage5a_week2_results_20260507.md` (Stage 5 acquisition infeasibility), `docs/stage4_short_term_track_results_20260507.md` (feature 부족 시그니처 3/3)
> **위치**: 새 Phase 2'' (Stage 6 architecture cycle 종료 후 feature/information cycle)

## 0. 의사결정 한 줄

> **본 design 의 목적**: 6B FAIL 후 확정된 "fixed-feature cold-start LAO scope 의 architecture-only remedies 종료" 결정에 따라, **feature/information shortage 1차 병목 직접 공략 트랙** 의 axis / 후보 / 우선순위 / 의사결정 sequence 를 사전 설계.
>
> **핵심 결정 영역 (의사결정자)**:
> 1. Axis 우선순위 — **A (Internal feature engineering, compliance 무관)** vs **B (External acquisition, Phase A pre-screen 후)**
> 2. Axis A 내 후보 우선순위 (quick-win categorical → text embedding → vision embedding 단계적)
> 3. Axis B 진입 조건 — Stage 5 compliance blocker 우회 가능한 새 source 발견 시에만

## 1. Architecture close 확정 (2026-05-07 의사결정자 승인)

- ✅ Stage 6B FAIL 승인 (Hard gate Δ_low +1.29%p, 100 seed 중 66 violation)
- ✅ **Architecture-only remedies under fixed-feature cold-start LAO scope** 종료
- ✅ 운영 모델 = baseline (F4 + spline + Huber) **+ calibration only (분기 B)** 유지
- ⏸️ 6C (architecture 추가) 보류 — 새 식별 가설 발견 시에만 reopen
- ⏸️ Representation learning / multimodal / non-artist hierarchy = 본 close 범위 외, 별도 axis (본 트랙에서 다루지 않음)

## 2. 가설 (program-level)

> **6B program hypothesis update (코덱스)**: "Routing not bottleneck → Segmentation reduced sample efficiency → Feature/information shortage under current inputs"
>
> **Feature track 의 reformulation**: 운영 모델 F4 (`log_area + birth_year_centered + log_artist_total_works + spline`) 가 사용 안 한 정보 (current data 또는 external source) 를 추가하면 **저가 segment 의 식별력** 이 보강될 수 있는가?
>
> **저가 systematic harm 패턴 (Stage 6A +3.54%p / 6B +1.29%p)** = 저가 작품의 가격 신호가 F4 feature space 에서 **충분히 분리되지 않음** → 새 feature 가 분리력 추가해야 hypothesis 성립.

## 3. Axis A — Internal Feature Engineering (compliance 무관, 우선)

> **즉시 시작 가능** — 외부 source 의존 X / Stage 5 compliance blocker 무관 / current curated data 만 활용.

### 3.1 후보 inventory (`stage4_full.parquet` 의 운영 F4 외 column)

| 그룹 | Feature | Missing | Unique | 검증 비용 | 운영 적합성 |
|---|---|---|---|---|---|
| **A1: Cheap categorical** | `category` | 0% | 14 | 낮음 | 즉시 |
| | `medium_type` | 0.4% | 13 | 낮음 | 즉시 |
| | `attribution_class` | 0% | 4 | 낮음 | 즉시 |
| | `gallery_name` | 0% | 76 | 낮음 | **leakage-safe target encoding 필수** (코덱스 P2 — cross-fitting / out-of-fold 명시 prereg 의무) |
| | `gallery_cities` | 1.8% | 30 | 낮음 | 즉시 (city dummy) |
| **A2: Numeric / artist popularity** | `artist_followers` | 0% | 157 | 낮음 | **시점 정합성 검증 필수** (코덱스 P1 — sale 시점 이전 정보 재현 가능 확인 후 진입) |
| | `artist_for_sale` | 0% | 89 | 낮음 | **시점 정합성 검증 필수** (동일) |
| | `artist_is_p1` | 0% | 2 | 낮음 | **시점 정합성 검증 필수** (동일) |
| | `year_made` | 0% | 65 | 낮음 | 즉시 (작품 - 작가 시간차, 시점 정합성 명확) |
| **A3: Geometry** | `width_cm / height_cm` | 0% | — | 낮음 | aspect ratio / shape feature |
| **A4: Text embedding (heavier)** | `title` | 0% | 6,614 | 중간 | multilingual BERT (KR/EN) |
| | `medium` | 0% | 1,434 | 중간 | medium 의 text 임베딩 (medium_type 으로 압축 안 되는 정보) |
| **A5: Vision embedding (heaviest)** | `image_url` | 0% | — | 높음 | CLIP / ResNet — image fetch 필요 |
| **배제 (단일값/거의 결측)** | `availability`, `gallery_type`, `is_auction`, `artist_nationality`, `depth_cm (71.7% miss)` | — | — | — | useless |

### 3.2 단계별 우선순위 (코덱스 P0 — escalation ladder, "cheap falsification → representation escalation")

> Axis A = **cheap falsification ladder** (코덱스 P1 framing 정정). "quick-win 기대" 가 아닌 **저비용 가설 반증 → 비용 증가 family escalation** 의 사전순서형 gatekeeping sequence.
>
> Stage 4 단기 트랙 작업 3 결과 = "현재 inputs 로는 feature space 분리력 부족" + 6A/6B 의 저가 systematic harm (구조적 + 100seed 66/100 violation) → **A.1-A.3 만으로 충분할 가능성은 낮음** (코덱스 P1). A.4 (text) / A.5 (vision) 까지 escalation 사실상 유력 — 의사결정자에게 정직 보고.

| Step | Feature family | 가설 | 비용 | 결과별 다음 행동 |
|---|---|---|---|---|
| **A.1** | A1 (Cheap categorical 5종) | 갤러리 / 작품 분류 신호 추가로 저가 식별력 보강? | 1주 | PASS → 운영 채택 / FAIL or BORDERLINE → A.2 진입 |
| A.2 | A2 (Artist popularity 4종, 시점 정합성 검증 후) | 인기도 / P1 / 가용성 신호 추가? | 1주 | PASS → 운영 채택 / FAIL or BORDERLINE → A.3 진입 |
| A.3 | A3 (Geometry — aspect ratio + 2D vs 3D) | 작품 모양 신호 추가? | 0.5주 | PASS → 운영 채택 / FAIL or BORDERLINE → A.4 진입 (heavy escalation) |
| A.4 | A4 (Title text embedding, multilingual BERT) | 제목 의미 신호 추가? | 2-3주 | PASS → 운영 채택 / FAIL or BORDERLINE → A.5 진입 |
| A.5 | A5 (Image embedding, CLIP/ResNet) | 시각적 신호 추가? | 4주+ | PASS → 운영 채택 / FAIL → Axis A 전체 종료, Axis B 또는 새 cycle |

> **Step gate (코덱스 P0 — 통일)**: B안 "**escalation 허용**" 채택. 각 step FAIL/BORDERLINE 시 **다음 step 으로 escalation** (이전 step 폐기 X — 누적 family 가 아닌 **대체 family hypothesis** sequence). PASS 시 즉시 운영 채택 후보 + 이후 step 진입 불필요.
>
> **Per-step freeze 의무 (코덱스 P1 — HARK 회피 강화)**: 각 step prereg 에서 **(a) feature set + (b) encoding (target encoding cross-fitting / one-hot / log transform 명시) + (c) preprocessing (missing imputation / outlier handling) + (d) interaction 허용 범위 (있으면 사전 명시) + (e) stop/go rule + (f) 다음 step 이 alternative hypothesis 임을 명시** 모두 동시 freeze. 결과 본 후 변경 X.
>
> **Multiple comparisons (코덱스 P1 — 정정)**: 5 step 동시 비교 X = "사전순서형 gatekeeping sequence" → step-level Holm 보정 부적절. 각 step 은 **prereg 시점 단일 가설 단일 metric 기준 PASS/FAIL** 만 적용. Step-간 family 보정은 program-level α 분배 (예: 5 step 각 α=0.01) 또는 sequential stop-when-significant 명시 — A.1 prereg 에서 결정.

### 3.3 Axis A 의 한계 (사전 정직 보고, 코덱스 P1 강화)
- Internal feature = current curated data 의 새 column 활용일 뿐. **새 정보 source 자체는 추가 안 됨**.
- Stage 4 단기 트랙 작업 3 시그니처 ("현재 inputs 로는 feature space 분리력 부족") + Stage 6A/6B 저가 systematic harm 패턴 → **A.1-A.3 cheap families 만으로 저가 specific harm 해결 가능성 사전 evidence 상 낮음** (코덱스 P1).
- A.4 / A.5 representation embedding 까지 escalation **사실상 유력** — 의사결정자 의식적 자원 배분 필요 (compute + storage 비용 사전 계획).
- **A.5 까지 모두 FAIL 시**: Axis A 전체 종료 → Axis B (external acquisition, Phase A pre-screen 통과 필요) 또는 program-level 재설계 (representation learning track 신설 / 재정의 등).

## 4. Axis B — External Acquisition (Phase A pre-screen 통과 시만)

> **사전 조건 (코덱스 권고)**: Stage 5 의 compliance blocker (auction cohort mismatch / Artsy CV 자동화 prohibition) 우회 가능한 **새 합법적 source path** 발견 시에만 진입.

### 4.1 Acquisition Feasibility Phase A — 0단계 pre-screen (코덱스 P1 — 7항목 확장)

> **확장 사유 (코덱스 P1)**: Stage 5 는 compliance 단계에서 막혔으나, 합법 source 가 생겨도 **작품-level 저가 harm 해결로 연결되지 않으면 Phase A 통과 후에도 무의미**. 특히 공공 / 정부 aggregate index 는 compliance 쉬워도 작품-level signal 로 연결 불명확.

| 항목 | 평가 method | PASS 기준 |
|---|---|---|
| **Legal** | TOS 명시 / 한국법 / GDPR | 자동화 / data extraction / AI 사용 명시 허용 |
| **TOS 자동화 조항** | 약관 검토 (한국어 원문 우선) | scraping / data mining / API 자동 사용 명시 허용 |
| **Access** | API 가용성 / robots.txt / anti-bot 실측 | API 또는 합법적 자동화 path 가용 |
| **Anti-bot** | WebFetch / Playwright sample 실측 | 차단 X (Stage 5 처럼 403 = REJECT) |
| **Data availability** (코덱스 P1) | 저가 segment 작품 / 작가 cover rate, missing rate | ≥ 70% cover (저가 segment 의 majority) |
| **Labelability / Joinability** (코덱스 P1) | `artist_slug` / `title` / `gallery` 등 join key 일치율 | ≥ 80% join 가능 (작품-level signal 연결 가능) |
| **As-of-time reproducibility** (코덱스 P1) | scrape / API 시점이 sale 시점 이전 정보로 재구성 가능 | sale 시점 이전 snapshot 확보 가능 (시점 정합성 — leakage 방지) |

### 4.2 후보 source (사전 등록 외 — 발견 시 deviation log 의무)

| Source | Pre-screen 가능성 | 메모 |
|---|---|---|
| **공공 / 정부** (KAMS, 문체부, Korea Foundation 통계) | 가장 높음 — public data 명시 | 작품-level X / 시장 지수 level (aggregate signal) |
| **갤러리 직접 license** (Kukje / 학고재 / 현대 등) | 협상 필요 | LLM 외 운영팀 / 법무팀 작업 영역 |
| **Artprice / Artnet (paid)** | License 비용 발생 | 비용 < ROI 검증 필요 |
| Artsy / Saatchi / Auction site 자동화 | **REJECT** (Stage 5 결론) | 본 axis 진입 X |

### 4.3 Phase A 책임 분담
- **Legal / TOS 검토**: 법무팀 (LLM 외)
- **Access / Anti-bot 실측**: LLM 가능 (Stage 5 와 동일 method)
- **License 협상**: 운영팀 (LLM 외)
- → **Phase A 자체가 LLM 단독 작업이 아님** — 운영팀 / 법무팀 협업 필수.

## 5. PASS / FAIL 기준 (candidate, freeze 전 — 코덱스 P0 family 분리)

> 각 step 의 prereg 작성 시 finalize. 본 draft 는 candidate.
>
> **Evaluation family 분리 (코덱스 P0)**: 6B 의 sparse-warm 측정 불가 deviation 교훈 적용 — **LAO primary family 와 warm/time-split supportive family 를 PASS/FAIL 표에서 분리**. LAO 는 primary 결정, warm/time-split 은 보조 해석 (운영 채택 결정 미관여).

### 5.1 LAO Primary Family (운영 채택 결정 — main)

| 조건 | 임계 (candidate) |
|---|---|
| Primary metric | Cold-start LAO 100-seed MdAPE |
| Practical Δ | ≤ -1.0%p (운영 채택) / ≤ -0.3%p (BORDERLINE) |
| Primary CI | Cluster bootstrap 95% CI 상한 ≤ 0 |
| 🔴 Hard gate | Δ_low ≤ 0%p (저가 segment harm 절대 금지 — 운영 spec §17 동일) |
| **LAO Secondary (Holm m=3)** | low MdAPE / mid-high MdAPE / newly-warm MdAPE — **3 family** (sparse-warm 제외 — LAO 정의상 측정 불가) |

### 5.2 Warm / Time-split Supportive Family (코덱스 P0 — 별도 분리, 운영 채택 결정 미관여)

> **목적**: LAO 의 cold-start 한계를 보완하는 supportive evidence (운영 채택 결정 X). 6B 의 sparse-warm 측정 불가 교훈 — sparse-warm 은 time-split 평가에서만 의미.

| 조건 | 임계 (candidate) |
|---|---|
| Time-split metric | Warm artist 의 train ≤ 2024 → test 2025 MdAPE |
| Sparse-warm subset | train count ≤ 5 (time-split 에서 의미 있음) |
| 해석 | LAO Primary PASS 시 supportive / LAO Primary FAIL 시 단독 PASS 결정 X |

## 6. 일정 후보 (의사결정자 결정)

| 단계 | 일정 (LLM-only 추정) | 산출물 |
|---|---|---|
| 본 design draft 의사결정자 검토 | 1주 | axis / 우선순위 결정 |
| Axis A.1 prereg freeze | 1주 | 별도 prereg 문서 |
| Axis A.1 실험 + 코덱스 검토 | 2-3주 | 결과 보고서 |
| (조건부) A.2 진입 | A.1 결과 본 후 결정 | 별도 prereg |
| (조건부 / 병렬) Axis B Phase A pre-screen | 운영팀 / 법무팀 일정에 의존 | Source-별 4항목 평가 |

## 7. 의사결정자 결정 사항 (본 draft 의 목적, 코덱스 검수 권고 반영)

1. **Axis 우선순위** — Axis A 우선 진행 동의?
   - 추천 (코덱스 + 본 design): A 우선 / B 는 새 source 발견 시 조건부
2. **Axis A framing 확정 (코덱스 권고 1)** — "**cheap falsification ladder**" (저비용 가설 반증 → 비용 증가 escalation, 정직) vs "quick-win 기대 ladder" (낙관적) 중 어느 framing 으로 승인?
   - 추천: cheap falsification ladder (현재 evidence 상 정직)
3. **Step gate 확정 (코덱스 권고 2 — P0)** — A안 (각 family fail 시 전체 Axis A 종료) vs B안 (A.1-A.3 cheap fail 시 A.4-A.5 heavier escalation 허용) 중 어느 gate 로 승인?
   - 추천: B안 (escalation 허용) — 본 draft 의도와 일치, A.4/A.5 사전 자원 계획 필요
4. **Evaluation family 분리 (코덱스 권고 3 — P0)** — LAO primary family 와 warm/time-split supportive family 를 별도 표로 분리 동의?
   - 추천: yes — 6B sparse-warm 측정 불가 교훈, LAO 단독으로 운영 채택 결정 / warm/time-split 은 supportive
5. **Axis B Phase A 확장 (코덱스 권고 4 — P1)** — labelability / joinability / as-of-time reproducibility 를 정식 gate 로 추가 동의?
   - 추천: yes — 합법 source 가 생겨도 작품-level 저가 harm 연결 불가 시 Phase A 통과 무의미
6. **A.2 시점 정합성 검증 원칙 (코덱스 권고 5 — P1)** — `artist_followers` / `artist_for_sale` / `artist_is_p1` 의 prediction-time availability 검증 없이 진입 X 원칙 추가 동의?
   - 추천: yes — sale 시점 이전 정보로 재현 가능 확인 후만 진입
7. **A.4 / A.5 진입 조건** — A.1-A.3 FAIL/BORDERLINE 시 escalation 동의 (B안)?
   - 추천: yes (B안)
8. **Cold Phase A shadow** — 모델 개선 cycle 이 아닌 **data availability / labelability / joinability / compliance feasibility 검증 shadow** 로 정의 동의?
   - 추천: yes — feature track 과 분리, screen 항목 명시화

## 8. 위험 / Honest Caveats

- **Axis A 도 본질 미해결 가능성**: Stage 4 단기 트랙 결과 = "current inputs 로는 feature space 분리력 부족" → A.1-A.3 도 `is_low_price` 와 무관한 generic 신호일 뿐. **저가 specific 분리 신호 발견은 sample 자체가 부족** 가능.
- **Multiple comparisons inflation**: Axis A 내 5 step 진행 = 가설 family 5개 → step-level Holm 보정 필요.
- **HARK 회피**: 각 step 결과 본 후 다음 step 의 가설 / 임계 변경 X. 새 가설 = 새 cycle 명시.
- **Compute cost (A.4 / A.5)**: text/vision embedding 은 GPU + storage 필요. A.1-A.3 quick-win 대비 ROI 미리 검증.

## 9. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B 결과 최종 검수 (2026-05-07) | "Architecture-only close → feature/acquisition track 1순위 / Cold Phase A 는 모델 개선 X 정의" |
| **본 design draft 검수 (2026-05-07)** | **P0 ×2** (step gate 자기모순 / secondary family 정의 충돌) + **P1 ×6** (cheap falsification framing / HARK 강화 / labelability gate / 시점 정합성 / Axis A 한계 강하게 / shadow screen 항목화) + **P2 ×1** (gallery_name target encoding cross-fitting) — 본 commit 일괄 반영 |

## 10. 참조

- 6B 결과: `docs/stage6b_results_20260507.md`
- 6A 결과: `docs/stage6a_results_20260507.md`
- Stage 5 acquisition 종료: `docs/stage5a_week2_results_20260507.md`
- Stage 4 단기 트랙 (저가 진단): `docs/stage4_short_term_track_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
