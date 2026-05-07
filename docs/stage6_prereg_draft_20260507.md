# Stage 6 Pre-registration (Draft) — Architecture Cycle

> **작성일**: 2026-05-07 (Stage 5 cycle 종료 후 초안)
> **상태**: **Draft** — Stage 5 종료 + 분기 B 운영 적용 후 사용자 / 의사결정자 검토 + freeze 결정 필요
> **연계**: `docs/stage4_warm_validation_results_20260507.md` (Stage 4 BORDERLINE) / `docs/stage4_short_term_track_results_20260507.md` (저가 feature 부족 입증) / `docs/stage5a_week2_results_20260507.md` (Stage 5 cycle 종료)

> ⚠️ **본 prereg 미목적**:
> - 새 모델 즉시 운영 도입 (재학습 X — 분기 B 결정 그대로 유지)
> - 본 prereg = **Stage 6 cycle 의 hypothesis / metric / PASS 기준 사전등록** (실험 시작 전 freeze)
> - Phase 위치: 새 Phase 2' (Stage 5 미개시 종료 후 architecture 검증 cycle)

## 1. Stage 6 목적

> **Stage 5 결론**: External feature acquisition 가설 = 준법적 접근 조건에서 검증 불가 → 가설 untested. 본질 = baseline F4 가 가격 결정 요인 부재 (저가 segment harm structural).
>
> **Stage 6 hypothesis**: **Architecture 변경** 으로 baseline 한계 해결 가능?
> - 1순위: Segmented architecture (low-vs-mid/high) — 코덱스 권고
> - 2순위: Bayesian / hierarchical
> - 3순위: 새 source (legal/access pre-screen 통과 후 별도)

## 2. Stage 6 구조 (v2 갱신 — 6A FAIL 후, 2 축으로 압축)

> **6A FAIL 후 갱신 (2026-05-07)**: 코덱스 권고 — "Architecture-only 개선 트랙 6A 에서 종료, 이후 **shared-modeling** 또는 **new-information** 두 축만". Segmentation 추가 실험 배제.

| Branch | 가설 | 상태 |
|---|---|---|
| ~~6A — Segmented architecture~~ | ~~Low-price 전용 모델 분리~~ | **FAIL** (`docs/stage6a_results_20260507.md`) |
| ~~6B — Partial pooling (shared-modeling)~~ | ~~Stage 3 ME 재사용 + sparse-warm/ICC mechanism~~ | **FAIL** (`docs/stage6b_results_20260507.md`) — ICC 0.81 ✓ but 저가 hard gate 위반 |
| **6C — 새 source 보강 (new-information)** | External source = 가격 anchor / market activity 통합 | 4항목 pre-screen 통과 후 본실험. **Architecture-only 종료 후 유일 후보** |

> **6A + 6B FAIL → Architecture-only 트랙 모두 종료**. 4-cycle 일관성 (Stage 4 작업 3 + Stage 5 + Stage 6A + Stage 6B) 으로 **feature shortage under current inputs** 본질 확정.

## 3. 6A (Segmented Architecture) — 1순위 prereg 초안

### 3.1 Primary hypothesis (단일, unadjusted)
- H₀: Segmented model overall MdAPE ≥ baseline (24.07%)
- H₁: Segmented model overall MdAPE < baseline + low-price segment harm 해결 (저가 violation 0건)

### 3.2 Architecture 후보
- 분리 기준: `price_krw < 5,000,000` (운영 guardrail 임계 동일)
- 모델 1 (low-price): F4 + spline + Huber, **저가 sample 만 학습**
- 모델 2 (mid/high): F4 + spline + Huber, **mid/high sample 만 학습**
- Routing: 예측가 quantile 기반 → 운영 시 first-pass 예측 후 segment 결정 (재귀 위험 — meta-router 검토)

### 3.3 Primary metric / Practical significance
- Cold-start LAO 100-seed MdAPE (Stage 3/4 동일)
- **Practical Δ ≤ -1.5%p** (baseline 24.07% → 22.5% 이내)
- **저가 segment harm 0 violations** (사전등록 §6.1 동일)

### 3.4 Secondary (Holm m=4 별도 family)
1. Low-price MdAPE 개선
2. Mid/high MdAPE 비악화
3. Routing 정확도 (segment 분류 정확도)
4. Composition shift 신규 warm 효과 (Stage 4 +0.25%p → 개선)

### 3.5 PASS / BORDERLINE / FAIL
| 시나리오 | 적용 |
|---|---|
| Primary CI 상한 ≤ 0 + 저가 harm 0 + practical Δ ≤ -1.5%p | PASS (Phase 3 shadow 진입) |
| 부분 통과 (Primary OR 저가 harm) | BORDERLINE (재검토) |
| 둘 다 미달 | FAIL (6B / 6C 검토) |

### 3.6 Risks
- Routing 재귀: first-pass 예측 → segment 분류 → 재예측 = circular
- Low-price sample 표본 부족 (Stage 4 저가 144건 / 125명 작가)
- 운영 spec §17 의 routing 로직 추가 복잡도

## 4. 6B (Bayesian / Hierarchical) — 2순위 (별도 prereg)

> Stage 6A 결과 후 별도 prereg 작성. 본 draft 에 hypothesis 만 명시.

- artist-level partial pooling
- Cold/warm 경계 자동 처리 (sparse artist 의 random intercept)
- Uncertainty-aware fallback (V3 자동 라우팅 시 신뢰도 기반)

## 5. 6C (새 source 보강) — 3순위, Pre-screen 필수

> ⚠️ **사전 조건 (코덱스 권고)**: Stage 6C 본실험 진입 전 **별도 0단계 feasibility/legal gate** 통과 필수. 하나의 Source 라도 4 항목 PASS 시 본 prereg 작성.

### 5.1 0단계 Pre-screen Template (4 항목)

| 항목 | 평가 method | PASS 기준 |
|---|---|---|
| **Legal** | TOS 명시 / 한국법 / GDPR | 자동화 / data extraction / AI 사용 명시 허용 또는 명시 금지 X (모호 시 LEGAL-REVIEW) |
| **TOS 자동화 조항** | 약관 검토 (한국어 원문 우선) | scraping / data mining / API 자동 사용 명시 허용 |
| **Access** | API 가용성 / robots.txt / anti-bot 실측 | API 또는 합법적 자동화 path 가용 |
| **Anti-bot** | WebFetch / Playwright sample 실측 | 차단 X (Stage 5 처럼 403 = REJECT) |

### 5.2 후보 (사전 등록 외 → deviation log 의무)
- Galerie 직접 데이터 (Kukje / 학고재 / 현대) — license 협상 필수
- Artprice / Artnet (paid) — license 비용 / API 사용
- 미술품 가격 지수 (KAMS / 정부 통계)

## 6. Phase 위치

> Phase 1 (curated) — Stage 1-4 종결
> Phase 2 (External Acquisition) = Stage 5 → 미개시 종료
> **새 Phase 2'** = Stage 6 (Architecture cycle)
> Phase 3 (Production) = Cold rollout 진행 중

## 7. 일정 / 산출물 (Draft)

| 단계 | 일정 | 산출물 |
|---|---|---|
| Stage 6A prereg freeze | (사용자 승인 후) | 본 §3 confirmatory prereg 별도 문서 |
| Stage 6A 실험 | 2-3주 (LLM 가능) | `experiments/structural_v1/stage6a_segmented.py` |
| Stage 6A 결과 보고 | 1주 | 보고서 + 코덱스 검토 |
| (조건부) 6B prereg | 6A FAIL 시 | 별도 |
| (조건부) 6C 0단계 pre-screen | 새 source 후보 발견 시 | Legal pre-screen 4 항목 |

## 8. 사용자 / 의사결정자 결정 사항

본 prereg = **Draft 상태**. 다음 결정 필요:

1. **Stage 6 시작 시점** — 분기 B (calibration only) 운영 적용 후? 또는 병행?
2. **6A primary hypothesis 임계** (Δ ≤ -1.5%p 적절?)
3. **Routing 재귀 처리 방식** (meta-router / quantile-based / heuristic)
4. **6C pre-screen 책임** (LLM / 운영팀 / 법무팀)

## 9. 코덱스 자문 이력 (Stage 6 관련)

| 차수 | 내용 |
|---|---|
| Stage 5 cycle 종료 자문 (2026-05-07) | Stage 6 1순위 = segmented / 2순위 = Bayesian / 3순위 = 새 source (pre-screen 선행) |
| 본 draft 검토 (예정) | 1순위 hypothesis 임계 + routing 처리 |
| 6A prereg freeze 시점 (예정) | confirmatory prereg 검수 |

## 10. 참조

- Stage 4 결과: `docs/stage4_warm_validation_results_20260507.md`
- 단기 트랙 (저가 진단): `docs/stage4_short_term_track_results_20260507.md`
- Stage 5 결과: `docs/stage5a_week2_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
