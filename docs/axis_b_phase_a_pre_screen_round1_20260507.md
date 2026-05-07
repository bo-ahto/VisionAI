# Axis B Phase A Pre-screen — Round 1 Report (Source Discovery + Access)

> **작성일**: 2026-05-07
> **위치**: 새 Phase 2'' Axis B (External Acquisition) 의 **Phase A pre-screen project — Round 1 (Source Discovery + Access)**
> **연계**: `docs/feature_track_axis_a5_results_20260507.md` (Axis A 5 step 종결, B 진입 권고) / `docs/feature_track_design_20260507.md` (Phase A 7항목 정의) / `docs/stage5a_week2_results_20260507.md` (Stage 5 acquisition infeasibility — 5/5 REJECT)

> ⚠️ **본 round 의 범위**: **LLM 가능 영역만** — Source discovery + 1차 access 실측 (Phase A 7항목 중 Access / Anti-bot 부분). Legal / TOS 검토 + License 협상 = 운영팀 / 법무팀 영역, 본 round 외.

> **목적**: Stage 5 의 5/5 source REJECT 이후 **새 lawful path 발견** — Phase A 7항목 중 LLM 가능 부분 (Access / Anti-bot / robots.txt) 을 1차 screening 하여 다음 round (Legal/TOS 검토) 진입 후보 추리기.

## 1. 한 줄 요약 (의사결정자용)

> **Round 1 = LLM 가능 영역 1차 screening 완료** — 후보 10개 중 **5개 (정부/공공)** 가 Access / Anti-bot 통과 likely / **1개 (Frieze) REJECT** (AI training 명시 금지) / **2개 (KIAF / 한국화랑협회)** 부분 PASS, TOS 추가 검토 필요 / **2개 (Korea Foundation / KOSARC) 추가 확인 필요** (SSL / DNS).
>
> **핵심 finding**: 정부/공공 통계 source (KOSIS / MCST / Arko / KAMS / MMCA) = robots.txt 자동화 친화적 → **다음 round 진입 후보**.
>
> **Stage 5 패턴 반복 (1건)**: Frieze Seoul = AI training 명시 금지 (`Content-Signal: ai-train=no`, EU Article 4 권리 보유) → REJECT.
>
> **다음 단계 (사용자 결정)**: (a) LLM 추가 screening (Data availability / Labelability·Joinability — 각 source 의 art market 실제 데이터 존재 여부) / (b) 운영팀·법무팀 cycle (Legal / TOS 검토 + License 협상).

## 2. Round 1 결과 (Access / Anti-bot 1차 실측)

### 2.1 후보 10 source 1차 결과

| 순번 | Source | Domain | Access | robots.txt 자동화 | AI/training 명시 | 1차 평가 |
|---|---|---|---|---|---|---|
| 1 | **KOSIS (통계청)** | kosis.kr | 200 | `Allow: /` 전체 허용 | (정부 공식, TOS public) | ✓ **PASS likely** |
| 2 | **MCST (문체부)** | mcst.go.kr | 200 | `Allow: /` (search 만 disallow) | (정부 공식) | ✓ **PASS likely** |
| 3 | **KAMS (예술경영지원센터)** | gokams.or.kr | 200 | 부분 disallow (`/admin/`, `/01_news/`) | (공공기관, TOS 검토 필요) | ✓ **PASS likely** |
| 4 | **Arko (한국문화예술위원회)** | arko.or.kr | 200 | Googlebot 만 일부 disallow | (공공기관, TOS 검토 필요) | ✓ **PASS likely** |
| 5 | **MMCA (국립현대미술관)** | mmca.go.kr | 200 | (간단 spec 152 bytes) | (정부 공식) | ✓ **PASS likely** |
| 6 | 한국화랑협회 | koreagalleries.or.kr | 200 | `wp-admin/` 만 disallow | (협회, TOS 검토 필요) | ⚠️ **부분 PASS** (TOS 검토) |
| 7 | KIAF | kiaf.org | 200 | `Allow : /` 전체 허용 | (협회, TOS 검토 필요) | ⚠️ **부분 PASS** (TOS 검토) |
| 8 | **Frieze Seoul** | frieze.com | 200 | Content-Signal 5KB | **`ai-train=no` 명시** (EU Article 4 권리) | ❌ **REJECT** (AI training prohibition) |
| 9 | Korea Foundation | koreafoundation.or.kr | SSL 에러 | — | — | ❓ 추가 확인 필요 |
| 10 | KOSARC (한국미술시가감정협회) | kpriceart.or.kr | DNS FAIL | — | — | ❓ 도메인 확인 필요 (다른 host name) |

### 2.2 Frieze Seoul REJECT 상세 (Stage 5 Artsy CV 패턴 반복)

```
User-agent: *
Content-Signal: search=yes, ai-train=no
Allow: /

User-agent: Amazonbot / Applebot-Extended / Bytespider / CCBot
Disallow: /
```

> **Frieze REJECT 사유**: `Content-Signal: ai-train=no` 명시 + EU Article 4 of 2019/790 (Copyright in Digital Single Market) 권리 보유 + AI scraper (Amazonbot / Bytespider / CCBot 등) 전체 Disallow → **AI/ML 사용 = TOS 위반**. Stage 5 Artsy CV (Cloudflare 403 + TOS automation prohibition) 와 동일 패턴.

### 2.3 PASS likely 5개 정부/공공 source 우선순위 (다음 round)

| 우선순위 | Source | 강점 | 약점 | 다음 단계 priority |
|---|---|---|---|---|
| **1** | **KOSIS** | 정부 공식 통계 / `Allow: /` 명시 / API 가능성 큼 | art market 통계 직접 보유 여부 미확인 | **Data availability 평가 우선** |
| **2** | **MCST** | 문화체육관광부 = art market 정책 통계 보유 | 작품-level vs aggregate level 분리 필요 | Data availability 평가 |
| **3** | **KAMS (예술경영지원센터)** | art-specific 공공기관 / 미술 시장 분석 보고서 | TOS 추가 검토 / aggregate 위주 가능 | Data availability + TOS 검토 |
| **4** | **MMCA** | 국립현대미술관 = 소장품 / 거래 history 가능 | aggregate 위주 / 작품-level join 평가 필요 | Data availability + Labelability 평가 |
| **5** | **Arko** | 문화예술 진흥 통계 | art market 비핵심 (전반 문화) | 후순위 |

## 3. 다음 round 결정 영역 (사용자)

### 3.1 LLM 가능 cycle (Round 2 — Data availability + Labelability)
- **PASS likely 5개 source** 의 실제 art market 데이터 존재 여부 평가
- 각 source 의 작품-level signal vs aggregate index level 분리
- `artist_slug` / gallery / work_id join 가능성 평가
- LLM 가능 — 1-2주 추정

### 3.2 운영팀 / 법무팀 cycle (Round 2 동시 또는 후속)
- **Legal / TOS 검토** (5개 source 의 자동화 / data extraction / AI 사용 명시)
- License 협상 (필요 시)
- LLM 외 — 운영팀 / 법무팀 capacity 확정 필요

### 3.3 옵션
| 옵션 | 본질 | 비용 |
|---|---|---|
| **A. LLM Round 2 단독 진행** | Data availability + Labelability 우선 평가 → 결과 후 운영팀/법무팀 협업 | LLM 시간 만 |
| **B. 운영팀/법무팀 cycle 즉시 시작** | Legal / TOS 검토 병행 | 비-LLM 자원 |
| **C. 동시 진행** (권고) | LLM Round 2 + 운영팀/법무팀 cycle 병렬 | 양쪽 자원 |
| **D. Round 1 결과 보고만** | 사용자 결정 후 다음 단계 | 0 |

## 4. 한계 / 정직 보고

- **Round 1 = Access / Anti-bot 표면 평가만**: robots.txt + HTTP 200 만 확인 / **TOS 본문 / 한국법 / GDPR 검토 X** (LLM 외 영역)
- **Frieze REJECT 의미**: AI training 명시 금지 = Stage 5 Artsy CV 패턴 반복 → "private art market site 는 AI 사용 명시 금지 가능성 높음" plausible 가설 (Stage 5 + Frieze 2개 사례)
- **정부/공공 source 의 한계**: art market 통계 직접 보유 여부 미확인 / 작품-level vs aggregate index level 분리 필요 (Round 2 평가 영역)
- **Korea Foundation / KOSARC 추가 확인 필요**: SSL / DNS 에러 — 도메인 정확성 추가 검증 후 재평가 가능
- **Phase A 7항목 중 Access 만 평가 완료**: Legal / TOS / Data availability / Labelability·Joinability / As-of-time = Round 2+ 영역

## 5. 다음 단계

1. ✅ Round 1 보고 — 본 commit
2. ⏳ 사용자 의사결정 — Round 2 옵션 (A/B/C/D)
3. (조건부 / Option A or C) Round 2 LLM cycle: Data availability + Labelability 평가
4. (조건부 / Option B or C) 운영팀 / 법무팀 cycle: Legal / TOS 검토 + License 협상

## 6. 참조

- Feature track design: `docs/feature_track_design_20260507.md` (Phase A 7항목 정의)
- 종합 보고서: `docs/트랙2_종합보고서_axis_a_종결_20260507.html` (handoff packet)
- Stage 5 acquisition infeasibility: `docs/stage5a_week2_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
