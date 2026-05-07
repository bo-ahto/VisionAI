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
| **A1: Quick-win categorical** | `category` | 0% | 14 | 낮음 | 즉시 |
| | `medium_type` | 0.4% | 13 | 낮음 | 즉시 |
| | `attribution_class` | 0% | 4 | 낮음 | 즉시 |
| | `gallery_name` | 0% | 76 | 낮음 | 즉시 (target encoding) |
| | `gallery_cities` | 1.8% | 30 | 낮음 | 즉시 (city dummy) |
| **A2: Numeric / artist popularity** | `artist_followers` | 0% | 157 | 낮음 | 즉시 (log transform) |
| | `artist_for_sale` | 0% | 89 | 낮음 | 즉시 |
| | `artist_is_p1` | 0% | 2 | 낮음 | 즉시 (boolean) |
| | `year_made` | 0% | 65 | 낮음 | 즉시 (작품 - 작가 시간차) |
| **A3: Geometry** | `width_cm / height_cm` | 0% | — | 낮음 | aspect ratio / shape feature |
| **A4: Text embedding (heavier)** | `title` | 0% | 6,614 | 중간 | multilingual BERT (KR/EN) |
| | `medium` | 0% | 1,434 | 중간 | medium 의 text 임베딩 (medium_type 으로 압축 안 되는 정보) |
| **A5: Vision embedding (heaviest)** | `image_url` | 0% | — | 높음 | CLIP / ResNet — image fetch 필요 |
| **배제 (단일값/거의 결측)** | `availability`, `gallery_type`, `is_auction`, `artist_nationality`, `depth_cm (71.7% miss)` | — | — | — | useless |

### 3.2 단계별 우선순위 (코덱스 권고 — quick-win 우선)

> Axis A 는 **단계적 추가** (Stage 3 P3 / Stage 4 처럼 family addition cycle). 한 번에 모든 feature 추가 X — 각 단계 PASS 검증 후 진행.

| Step | Feature 추가 | 가설 | 비용 |
|---|---|---|---|
| **A.1** | A1 (Quick-win categorical 5종) | 갤러리 / 작품 분류 신호 추가 → 저가 식별력 ↑ | 1주 |
| A.2 | A2 (Artist popularity 4종) | 인기도 / P1 / 가용성 신호 추가 | 1주 |
| A.3 | A3 (Geometry — aspect ratio + 2D vs 3D) | 작품 모양 신호 추가 | 0.5주 |
| A.4 | A4 (Title text embedding, multilingual BERT) | 제목 의미 신호 추가 (작품 / 시리즈명 differentiation) | 2-3주 |
| A.5 | A5 (Image embedding, CLIP/ResNet) | 시각적 신호 추가 (heaviest, image fetch + storage) | 4주+ |

> **각 step 사이 stop rule**: 특정 step 의 PASS 조건 미달 (Δ ≤ -1.0%p AND hard gate Δ_low ≤ 0%p) 시 다음 step **추가 시도 X — 가설 update + 재설계** (HARK 회피).

### 3.3 Axis A 의 한계 (사전 정직 보고)
- Internal feature = current curated data 의 새 column 활용일 뿐. **새 정보 source 자체는 추가 안 됨**.
- Stage 4 단기 트랙 작업 3 의 시그니처 = "현재 inputs 로는 feature space 가 분리력 부족" → Axis A 도 본질적 information bottleneck 미해결 가능성.
- → Axis A.1-A.3 fail 시 Axis B (external acquisition) 또는 A.4-A.5 (representation embedding) 로 escalation.

## 4. Axis B — External Acquisition (Phase A pre-screen 통과 시만)

> **사전 조건 (코덱스 권고)**: Stage 5 의 compliance blocker (auction cohort mismatch / Artsy CV 자동화 prohibition) 우회 가능한 **새 합법적 source path** 발견 시에만 진입.

### 4.1 Acquisition Feasibility Phase A — 0단계 pre-screen (4항목)

| 항목 | 평가 method | PASS 기준 |
|---|---|---|
| **Legal** | TOS 명시 / 한국법 / GDPR | 자동화 / data extraction / AI 사용 명시 허용 |
| **TOS 자동화 조항** | 약관 검토 (한국어 원문 우선) | scraping / data mining / API 자동 사용 명시 허용 |
| **Access** | API 가용성 / robots.txt / anti-bot 실측 | API 또는 합법적 자동화 path 가용 |
| **Anti-bot** | WebFetch / Playwright sample 실측 | 차단 X (Stage 5 처럼 403 = REJECT) |

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

## 5. PASS / FAIL 기준 (candidate, freeze 전)

> 각 step 의 prereg 작성 시 finalize. 본 draft 는 candidate.

| 조건 | 임계 (candidate) |
|---|---|
| Primary metric | Cold-start LAO 100-seed MdAPE |
| Practical Δ | ≤ -1.0%p (운영 채택) / ≤ -0.3%p (BORDERLINE) |
| Primary CI | Cluster bootstrap 95% CI 상한 ≤ 0 |
| 🔴 Hard gate | Δ_low ≤ 0%p (저가 segment harm 절대 금지 — 운영 spec §17 동일) |
| Secondary | Holm m=4 (low / mid-high / sparse-warm time-split / newly-warm) |
| Newly-warm | 사실상 동등 또는 개선 |

## 6. 일정 후보 (의사결정자 결정)

| 단계 | 일정 (LLM-only 추정) | 산출물 |
|---|---|---|
| 본 design draft 의사결정자 검토 | 1주 | axis / 우선순위 결정 |
| Axis A.1 prereg freeze | 1주 | 별도 prereg 문서 |
| Axis A.1 실험 + 코덱스 검토 | 2-3주 | 결과 보고서 |
| (조건부) A.2 진입 | A.1 결과 본 후 결정 | 별도 prereg |
| (조건부 / 병렬) Axis B Phase A pre-screen | 운영팀 / 법무팀 일정에 의존 | Source-별 4항목 평가 |

## 7. 의사결정자 결정 사항 (본 draft 의 목적)

1. **Axis 우선순위** — Axis A 우선 진행 동의?
   - 추천 (코덱스 + 본 design): A 우선 / B 는 새 source 발견 시 병렬
2. **Axis A 내 step 우선순위** — A.1 (Quick-win categorical) 부터 단계적 진행 동의?
   - 추천: A.1 → A.2 → A.3 단계적, 각 step PASS 후 진행
3. **A.4 (text) / A.5 (vision) 진입 조건** — A.1-A.3 모두 FAIL 시? 또는 A.1 부터 병렬?
   - 추천: A.1-A.3 모두 FAIL 시 escalation (자원 효율성)
4. **Axis B 진입** — 새 합법적 source 후보 발견 시 운영팀 / 법무팀 파일럿 가능?
   - 결정 영역: 비-LLM 작업 자원 배분
5. **Cold Phase A shadow (코덱스)** — 모델 개선 cycle 이 아닌 **data availability / labelability / compliance feasibility 검증 shadow** 로 정의 동의?
   - 추천: yes — feature track 과 분리

## 8. 위험 / Honest Caveats

- **Axis A 도 본질 미해결 가능성**: Stage 4 단기 트랙 결과 = "current inputs 로는 feature space 분리력 부족" → A.1-A.3 도 `is_low_price` 와 무관한 generic 신호일 뿐. **저가 specific 분리 신호 발견은 sample 자체가 부족** 가능.
- **Multiple comparisons inflation**: Axis A 내 5 step 진행 = 가설 family 5개 → step-level Holm 보정 필요.
- **HARK 회피**: 각 step 결과 본 후 다음 step 의 가설 / 임계 변경 X. 새 가설 = 새 cycle 명시.
- **Compute cost (A.4 / A.5)**: text/vision embedding 은 GPU + storage 필요. A.1-A.3 quick-win 대비 ROI 미리 검증.

## 9. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B 결과 최종 검수 (2026-05-07) | "Architecture-only close → feature/acquisition track 1순위 / Cold Phase A 는 모델 개선 X 정의" |
| 본 design draft 검수 (예정) | axis 우선순위 / step 단계화 / Phase A 분리 정당성 |

## 10. 참조

- 6B 결과: `docs/stage6b_results_20260507.md`
- 6A 결과: `docs/stage6a_results_20260507.md`
- Stage 5 acquisition 종료: `docs/stage5a_week2_results_20260507.md`
- Stage 4 단기 트랙 (저가 진단): `docs/stage4_short_term_track_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
