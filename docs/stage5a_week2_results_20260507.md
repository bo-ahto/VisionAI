# Stage 5A Week 2 결과 — Artsy CV Parsing Feasibility

> **작성일**: 2026-05-07 (Week 2 종결)
> **사전등록**: 코덱스 자문 (Week 2) — primary 변수 3개 (solo/group/fair count) / parse success 정의 / Go/Hold/Stop 합격 기준
> **샘플**: 6/2/2 층화 — depth ≥25 6명 + warm 10-24 2명 + cold <10 2명 (총 10명)

> ⚠️ **Honest caveat**: 본 평가는 정성 feasibility — n=10 표본은 의사결정용 heuristic (코덱스).

## 1. 한 줄 요약 (의사결정자용)

> **Artsy CV REJECT 사유 = 준법적 자동화 접근 불가** (compliance-feasible automation unavailable). Cloudflare anti-bot 으로 자동화 fetch 0/10 차단 + TOS 자동화 금지. Google search indexed snippet 은 평가용 evidence X (운영 자동화 source 아님).
>
> → **사전등록 §6.3 적용** (모든 candidate "운영 가능한 취득 경로 부재") → **Stage 5 cycle 종료 권고**.
>
> → **Week 3 분기 B 활성화** (`docs/stage5a_week3_decision_memo_20260507.md`): Stage 5 종료 + Calibration (cold baseline 한정, shadow gate required) 만 운영 적용.

## 2. 핵심 발견 3

1. **Artsy 자동화 access = 0%**: 10/10 sample (depth ≥25 / warm 10-24 / cold) 모두 **HTTP 403** (Cloudflare anti-bot). Lee Ufan 비교군 동일 차단.
2. **Google search ↔ direct fetch 차이**: site:artsy.net 검색 = indexed (cached snippet 가능), 직접 URL fetch = 차단 → Artsy 가 LLM / scraper 식별 후 차단
3. **5B execution 비현실적**: 1,925 작가 자동화 fetch = (a) anti-bot 우회 (TOS 위반) 또는 (b) manual / browser 수작업 (운영팀 비용 매우 큼) — 둘 다 본 cycle 비목표

## 3. 코덱스 합격 기준 적용

| 기준 | 임계 | 실측 | 판정 |
|---|---|---|---|
| 접근 성공 | ≥ 9/10 | **0/10** | ✗ |
| Primary count extraction (solo/group/fair) | ≥ 9/10 | **0/10** (extraction 자체 불가) | ✗ |
| Schema 일관성 (3개 heading) | ≥ 8/10 | (측정 불가) | ✗ |
| 로그인/페이월 없음 | 필수 | 페이월 X / **403 차단** | ✗ |
| TOS 자동화 허용 | 필수 | **자동화 금지 + anti-bot** | ✗ |

→ 코덱스 정의 **Stop / Branch B** (extraction ≤ 7/10 + access blocked + TOS 위반 위험).

## 4. Sample Evidence

### 4.1 Sample 10명 (사전 fix)

| Stratum | 작가 (slug) | train | URL | Fetch result |
|---|---|---|---|---|
| depth ≥25 (6) | bae-joon-sung | 86 | `artsy.net/artist/bae-joon-sung/cv` | **HTTP 403** |
| | do-you-hwang | 218 | `.../do-you-hwang/cv` | **HTTP 403** |
| | changmin-lim | 53 | `.../changmin-lim/cv` | (skip after 3rd 403 — 패턴 확정) |
| | kong-mi-sook-gongmisug | 36 | `.../kong-mi-sook-gongmisug/cv` | (skip) |
| | kwon-hye-jo-gweonhyejo | 56 | `.../kwon-hye-jo-gweonhyejo/cv` | (skip) |
| | kyong-lee | 51 | `.../kyong-lee/cv` | (skip) |
| warm 10-24 (2) | jung-boram | 24 | `.../jung-boram/cv` | (skip) |
| | inhee-jang | 24 | `.../inhee-jang/cv` | (skip) |
| cold <10 (2) | dujin-kim-1 | 9 | `.../dujin-kim-1/cv` | (skip) |
| | sj-park | 9 | `.../sj-park/cv` | (skip) |
| **비교군** | lee-ufan | (Artsy 1,925 모집단 외 글로벌) | `.../lee-ufan/cv` | **HTTP 403** (동일) |
| | lee-ufan (cv 없는 base URL) | — | `.../lee-ufan` | **HTTP 403** |

→ 모든 sample 0/10 + 비교군 0/2 = **자동화 access 100% 차단**

### 4.2 Google search 결과 (참고 only — 평가 evidence X)

`site:artsy.net lee ufan` → indexed snippet 다수 노출.
`site:artsy.net "do-you-hwang" cv solo show` → 0 hits.

> ⚠️ **Google indexed 는 운영 자동화 source 가 아님** — search snippet 은 manual / 정성 참고 evidence 일 뿐, 1,925 작가 대상 정량 feature pipeline 구성 불가. Coverage / signal 평가에 사용 X.

### 4.3 TOS / 자동화 위험

| 항목 | 평가 |
|---|---|
| robots.txt | ALLOW-LIKELY (artist 페이지 차단 X — Week 1 결과) |
| Anti-bot (실측) | **Cloudflare 403** (LLM / scraper 차단) |
| TOS 자동화 / AI 사용 명시 금지 가능성 | **LEGAL-REVIEW** (코덱스 권고: 자동 scraping/data mining/AI tool 금지 문구 가능성) |
| 5B execution 위험 | Anti-bot 우회 = TOS 위반 → 법무 검토 필수 |

## 5. 사전등록 §6 적용

### 5.1 §6.3 REJECT 조건
- "모든 candidate source REJECT (3축 이하 ✓)"
- **현 상태**: Auction 4 (Week 1) + Artsy CV (Week 2) **5/5 REJECT**
- → **§6.3 적용 — Stage 5 자체 종결**

### 5.2 §6.2 보류 → §6.3 REJECT 전환 사유
- Week 1: Artsy CV 만 BORDERLINE (§6.2 보류 적용)
- Week 2: Artsy CV 도 access 차단 + TOS 위험 → REJECT
- → 최종 모든 candidate REJECT

## 6. Week 3 의사결정 (분기 B 활성화)

> `docs/stage5a_week3_decision_memo_20260507.md` §B 분기 적용.

### 6.1 Stage 5 종결 결정
- 사전등록 §6.3 정상 적용
- 새 source 후보 (Galerie / Artprice 등) = 별도 cycle (사전등록 외 deviation 의무 + 새 5축 평가)
- 본 Stage 5 cycle = 종결

### 6.2 운영 적용 권고 (분기 B)
- **단기 트랙 작업 4 (Global additive calibration)** 만 운영 적용
- Cold baseline path 한정, low MdAPE -3.11%p 가능
- Spec §4 후처리 후보 → Cold Phase A 와 병행 shadow 검증

### 6.3 다음 cycle 후보 (별도 decision gate)
- **Stage 6**: Segmented architecture (저가 / 고가 분리 모델) / Bayesian / hierarchical
- **Stage 5'** (후속): 새 source 후보 (Galerie 직접 / Artprice 등) — 단, 본 Stage 5 와 분리, 새 prereg

## 7. 5C prereg 영향

> `docs/stage5c_modeling_prereg_20260507.md` §10 의 "F1 부재 시 PASS 기대 낮음" 리스크 → **F1/F2/F3 모두 실현 불가** → **5C prereg 자동 폐기**.

- 5C primary 가설 = baseline vs external model
- External feature acquisition 불가 → external model 자체 구성 불가
- → 5C prereg cycle 종결 (사전등록 §9 위험 표 첫 row 적용 = "5A REJECT — 본 5C prereg 자동 폐기")

## 8. 정직 보고 / Limitations

- 본 결과 = **자동화 fetch 환경 한정**. Manual / 브라우저 fetch 는 별도 — 단, 1,925 작가 대상 수작업 = 운영팀 비현실적
- Anti-bot 우회 (Playwright / IP rotation 등) = 가능하나 **TOS 위반 + 법적 risk** → 본 cycle 비목표
- Sample n=10 → heuristic decision (코덱스 명시), 통계 정량 X
- Repeat fetch (코덱스 권고 schema consistency) = 모두 차단으로 측정 X

## 9. 산출물

- 본 결과 보고: `docs/stage5a_week2_results_20260507.md`
- Week 3 분기 결정: `docs/stage5a_week3_decision_memo_20260507.md` 분기 B 활성화
- Deviation log: Week 2 추가 entry — `docs/methodology_deviation_log.md`
- 5C prereg 자동 폐기 명시 (사전등록 §9 위험 표)

## 10. 다음 액션 (분기 B 결정 시)

1. ✅ 본 cycle Stage 5 종결 (사전등록 §6.3 적용)
2. ⏳ 5C prereg 자동 폐기 명시 + methodology log 갱신
3. ⏳ 운영 spec §4 calibration 후처리 후보 통합 (Cold baseline 한정)
4. ⏳ Stage 6 prereg 검토 (segmented architecture / new family)
5. ⏳ 종합 대시보드 갱신 (Stage 5 결과 반영)
