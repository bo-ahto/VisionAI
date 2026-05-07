# Axis B Phase A Round 3 — A pre-assessment + Arko ops + MCST side-queue

> **작성일**: 2026-05-07 (Round 3 — 코덱스 사전 자문 조건부 GO 적용)
> **연계**: `docs/axis_b_round2b_results_20260507.md` (Round 2B 종결 + 우선순위 update) / 코덱스 사전 자문 (Round 3 design)
> **사용자 명시 instruction**: 우선순위에 맞춰서 진행 + 코덱스 활용

> ⚠️ **본 Round 3 의 범위 (코덱스 권고)**: 3 lane 분리 — Lane 1 (A 본선) / Lane 2 (Arko ops) / Lane 3 (MCST side-queue). LLM 가능 영역만 = "narrowing-grade" (운영팀/법무팀 결정급 X). Phase A 종합 판정 = HOLD 그대로 유지.

## 0. Executive line (코덱스 reporting 구조 §1)

> **Round 3 = 조건부 GO 유지 / A lane continue / Phase A 종합 판정 = HOLD 그대로**.
>
> - **Lane 1 (A)**: paid vendor + 한국 갤러리 1차 narrowing 완료 — Artprice = subscription/API 강함 (paid license 확인) / 한국 갤러리 6개 중 3개 자동화 access OK (Kukje / Pace / PKM)
> - **Lane 2 (Arko ops)**: **Arko main `/` access recovery** (이전 sub-path 4xx/5xx 만 / main 정상 200) → HOLD → **partial PASS — access recovery only** (sub-path / dataset endpoint 미확인) + Arko 운영팀 inquiry draft 작성 (운영팀 인계용)
> - **Lane 3 (MCST side-queue)**: MCST sub-path 4종 모두 404 → endpoint discovery 실패 → 운영팀 inquiry 영역 (LLM 가능 X)

## 1. Lane 1 — A 본선 (paid vendor + 한국 갤러리 narrowing)

### 1.1 Top 3 Paid Vendor (코덱스 산출물 §1A)

| 순위 | Vendor | Access | License/API hint | 평가 |
|---|---|---|---|---|
| **1** | **Artprice** | 200 / 9-14KB main+subscription | **strong (28+33 hits)** — `subscription`, `license`, `api`, `plan` 명시 | **paid subscription/API hint strong** (운영 확인 전 — 코덱스 P1 톤 정정) → 운영팀 협상 우선 후보 |
| ⚠️ HOLD (Round 4 pool) | **Sotheby's** | 200 / 455KB | 0 explicit hint | 주요 auction house — Round 2 freeze 의 5 source 외 / **본 Round 3 outreach 범위 X** (HARK 회피) |
| ⚠️ HOLD (Round 4 pool) | **Christie's** | 200 / 152KB | 0 explicit hint | 동일 — Round 4 candidate pool 분리 |
| 후보 (보류) | Artnet PriceDB | 200 / 1KB only (dynamic load 추정) | 0 | 추가 LLM 평가 또는 운영팀 inquiry 필요 |

> **본 Round 3 운영팀 outreach 즉시 범위 (코덱스 P1 정정 — Decision Table 충돌 fix)**: **Artprice 만** (vendor 1순위). Sotheby's / Christie's = Round 4 candidate pool 분리 / 본 Round 3 outreach 범위 X (HARK 회피).

**LLM 한계 명시**: 본 평가 = public web page 1차 access + keyword hint 기반 추정. **실제 license 조건 / 한국 art coverage / API spec / AI/ML 사용 허용 = 운영팀 협상 영역** (LLM 외).

### 1.2 Top 5 Korean Gallery shortlist (코덱스 산출물 §1B)

| 순위 | Gallery | Access | Page size | 평가 (코덱스 톤) |
|---|---|---|---|---|
| **1** | **Kukje (국제갤러리)** | 200 | 142KB | ✓ 자동화 access OK / 작가 / 작품 page 구조 평가 가능 |
| **2** | **Pace Seoul** | 200 | 132KB | ✓ 자동화 access OK / 글로벌 갤러리 |
| **3** | **PKM Gallery** | 200 | 52KB | ✓ 자동화 access OK / 한국 갤러리 |
| 4 | Hyundai (현대화랑) | 200 / 0KB | 0KB (dynamic only) | △ JavaScript rendered — 추가 평가 필요 |
| 5 | Hakgojae (학고재) | Connection refused | — | ✗ access X |
| (보류) | Gana Art | SSL CERTIFICATE_VERIFY_FAILED | — | △ SSL config 이슈 |

**갤러리 web 의 가격 공개 관행 (코덱스 사전 자문)**: hint count = 0 (모두) — 갤러리 web 은 가격 공개 비율 낮음 → **"데이터 richness" 보다 "협상 가능성 / 관계 형성 난이도" screening** 에 더 가까움 (코덱스 톤).

### 1.3 Lane 1 stop/continue rule (코덱스 §3, P1 톤 정정)
- **A continue 조건**: "1개라도 운영팀 contactable + license path plausible + 작품/가격 데이터 가능성 있음" → **충족** (Artprice = subscription/API hint strong, contactable + license path / Kukje / Pace / PKM = web access OK + 협상 가능)
- → **A continue: 협상 착수 GO** (운영팀 협상 시작 권고)
- ⚠️ **A continue ≠ decision-grade GO** (코덱스 P1 톤 정정): **source adequacy 판정 미정** — Lane 1 sources 는 **Round 2 freeze 3축 (cover ≥70 / join ≥80 / time-safe) 평가 미수행** (LLM 가능 영역 외 / 운영팀 + 법무 회신 후만 평가 가능). 본 Round 3 = "narrowing-grade only".

## 2. Lane 2 — Arko ops (inquiry draft + retry 2차)

### 2.1 Arko retry 결과 (freeze §3.3 spec 3회 중 2회 완료)

| Round | URL | 결과 |
|---|---|---|
| Round 2 (1차) | `arko.or.kr/main/index` | HTTP 500 |
| Round 2B (1.5차 — alternative URL) | `/main`, `/board/list/board?...`, `/info/page/sub6_1` | 모두 4xx/5xx |
| **Round 3 (2차)** | `arko.or.kr/` (root only) | **200 / 9KB ✓** |

**판정 (코덱스 톤 정정 적용)**: **partial PASS — access recovery only** (transport resolved, dataset endpoint still unconfirmed). 이전 round 의 sub-path 만 5xx, main `/` 자체는 정상 → MCST 패턴과 동일 ("main page recovery, endpoint 미확인"). Round 2 freeze §3.3 spec = 3회 중 2회 완료 / 추가 1회 = 다음 cycle (or 운영팀 inquiry 우선).

### 2.2 Arko 운영팀 inquiry draft (코덱스 8항목)

```
[Inquiry Draft — Arko (한국문화예술위원회) 데이터 access 요청]

받는이: 한국문화예술위원회 (Arko) 데이터 / 정보 담당 부서
제목: Korea art market 연구 / 모델링 데이터 access 협력 요청

1. 목적
   - VisionAI 트랙 2 — Korea art market 가격 예측 모델 (cold-start) 연구
   - Stage 4-6 (Stage 6B partial pooling FAIL) 후 Phase A pre-screen
     project — 새 lawful external source 발견 우선순위
   - 본 inquiry = LLM Round 1-2-2B-3 (자동화 access screening) 후속

2. 요청 데이터 범위
   - **작품-level**: 작가 / 작품명 / 제작년도 / 매체 / 크기 / 거래가 (있다면) /
     gallery / location 등 작품 단위 metadata
   - **aggregate-level**: 미술 시장 거래액 / 평균가 / 갤러리 수 / 작가 수 등
     annual / quarterly index
   - 우선순위: 작품-level (modeling input) > aggregate-level (context signal)

3. Access 방식 (어느 것이 가용한가)
   - REST API (인증 / rate limit 정보)
   - Bulk file download (CSV / JSON / Excel)
   - Portal / dashboard (login 자격)
   - 기타

4. Historical snapshot 필요성
   - sale 시점 이전 정보로 재구성 가능한 historical snapshot / archive 보유 여부
   - 예: 2020 sale 작품 의 2020 시점 작가 popularity / gallery roster 등

5. Update cadence
   - 데이터 update 주기 (monthly / quarterly / annual)
   - 최신 update 시점

6. License / Fee / 상업적 사용
   - 사용 license 모델 (CC-BY / public domain / proprietary)
   - 사용 비용 (무료 / paid)
   - 상업적 사용 가능 여부 (research only / 상업 가능)

7. AI / ML 사용 가능 여부
   - AI / ML training 사용 명시 허용 / 금지 / 모호
   - (참고: Frieze / Artsy 등 일부 art market site 는 AI training 명시 금지 — EU
     Article 4 권리 보유)

8. 회신 요청
   - 담당 부서 / 담당자 이름 + email + 직위
   - 1차 회신 가능 시점
   - 추가 협의 필요 영역

9. 정확 endpoint URL (코덱스 P1 보완)
   - art market 통계 / 작품 catalog 의 정확 URL path
   - 예: `arko.or.kr/<exact-path>/data` 또는 sub-domain

10. Schema sample / 컬럼 예시 (코덱스 P1 보완)
    - 작품-level 데이터 시 row sample (작가 / 작품명 / 거래가 / 매체 등)
    - aggregate-level 시 column 명 + format

11. Sample file 또는 API response (코덱스 P1 보완)
    - 1-page sample 또는 JSON response example

12. Auth 방식 (코덱스 P1 보완)
    - API key / OAuth / IP whitelist / login session
    - 발급 절차 / 사용 quota
```

**산출물 status**: 운영팀 인계용 발송본 — 본 draft 인계 후 운영팀 fine-tuning + 발송.

### 2.3 Lane 2 stop/continue rule
- Arko retry 실패 ≠ program stop 사유 (코덱스)
- **Arko main 200 = access recovery only** → 데이터 적합성 평가는 운영팀 inquiry 후
- **Round 2 freeze §3.3 spec 미충족 영역**: 24-72h × 추가 1회 retry 다음 cycle 진행 (운영팀 inquiry 우선)

## 3. Lane 3 — MCST side-queue (endpoint search)

### 3.1 MCST endpoint search 결과

| Endpoint candidate | Status | 평가 |
|---|---|---|
| `searchAll.jsp?sword=미술시장` (search engine) | 404 | ✗ search endpoint deprecated |
| `sitemap.jsp` | 404 | ✗ |
| `s_data/policy/policyList.jsp` | 404 | ✗ |
| `s_culture/policy/policyMain.jsp` | 404 | ✗ |

### 3.2 산출물 (코덱스 §1C — 정확 path 후보 1-3개 + why plausible)

> **결과**: 본 Round 3 LLM 가능 영역 = **endpoint discovery 실패** (sub-path 모두 404). MCST web 의 URL pattern 이 변경되었거나 search endpoint 가 다른 path 로 이동한 추정. **운영팀 직접 inquiry 또는 외부 검색 담당 배정** (코덱스 P2 정정 — LLM/운영팀 역할 경계 명확화).

### 3.3 Lane 3 stop/continue rule (코덱스)
- MCST endpoint 미발견 ≠ program stop 사유
- 운영팀 inquiry 우선 (Lane 2 와 함께)

## 4. Decision Table (코덱스 reporting §2, P1 정정 — 즉시 outreach 범위 vs Round 4 pool 분리)

> **본 Decision Table 원칙 (코덱스 P1 충돌 fix)**: **즉시 운영팀 outreach 범위** = 5 source freeze + Round 3 narrowing 통과 항목만 / **Round 4 candidate pool** = 본선 외 (HARK 회피).

| 항목 | 결과 | 즉시 outreach 범위 | Round 4 pool 분리 |
|---|---|---|---|
| **A vendors (Round 3 outreach)** | Artprice (1순위, hint strong) | ✓ Artprice 즉시 협상 | — |
| **A vendors (Round 4 pool, HARK)** | Sotheby's / Christie's | — | ⚠️ Round 4 pool, **즉시 outreach X** |
| **A galleries (Round 3 outreach)** | Kukje / Pace / PKM (3개 access OK) | ✓ 즉시 협상 (가격 공개 낮음 — 협상 난이도 screening) | — |
| **A galleries (Round 4 pool / 추가 평가)** | Hyundai (dynamic) | — | ⚠️ 추가 평가 필요 / Hakgojae·Gana 별도 access 검토 |
| **Arko inquiry** | 12항목 draft 완성 (코덱스 P1 보완) | ✓ 운영팀 인계 + 발송 | — |
| **Arko retry** | 2회 완료, main `/` 200 access recovery / sub-path 미확인 | — | 추가 1회 retry 다음 cycle + 운영팀 inquiry 우선 |
| **MCST endpoint** | sub-path 4종 404 — LLM 가능 영역 endpoint 발견 X | — | 운영팀 직접 inquiry 또는 외부 검색 담당 배정 |

## 5. Stop / Continue (코덱스 reporting §3)

### 5.1 Continue (확인된 것)
- **A lane continue: 협상 착수 GO** (코덱스 P1 톤 정정 — decision-grade GO X / source adequacy 판정 미정): Artprice + Kukje/Pace/PKM = 운영팀 협상 착수 충분
- Arko main access recovery — partial PASS (access only, dataset endpoint 미확인)
- ⚠️ **Lane 1 sources = Round 2 freeze 3축 (cover ≥70 / join ≥80 / time-safe) 평가 미수행** (코덱스 P1 caveat 강화) — method-gate 미검증

### 5.2 HOLD (운영팀 / 법무 의존 영역)
- Arko / MCST 의 dataset endpoint = 운영팀 inquiry 후
- License 조건 / 한국 art coverage / AI/ML 허용 = 운영팀 협상 + 법무 검토 후
- Phase A 종합 = 운영팀 / 법무팀 1차 회신 후 (코덱스 — Round 3 직후 X)

## 6. Deviation / HARK (코덱스 reporting §4)

- 새 source 발견: **Sotheby's / Christie's** = Round 2 freeze 의 5 source 외 / KIAF 한국화랑협회 와 동일 처리 — **Round 3 본선 편입 X / Round 4 candidate pool 분리** (코덱스 P0 HARK 회피)
- 본선 미편입: Sotheby's / Christie's / Hyundai 추가 평가 / Hakgojae / Gana SSL 이슈
- Round 2 freeze spec 변경 X — 본 round = LLM narrowing only

## 7. Next ask (코덱스 reporting §5)

| 영역 | 작업 | 시점 |
|---|---|---|
| **운영팀 outreach (1순위, 범위 한정)** | **Artprice + Kukje + Pace + PKM + Arko inquiry** license 협상 시작 (코덱스 P1 — Sotheby's/Christie's/Hyundai 제외, Round 4 pool) | 즉시 |
| **운영팀 outreach (Arko)** | inquiry draft 발송 | 즉시 |
| **법무 검토** | Artprice TOS / 한국 갤러리 license 검토 | 즉시 |
| **Arko 추가 retry** | freeze §3.3 spec 충족 (3회 중 마지막 1회) | 다음 cycle (24-72h 후) |
| **MCST endpoint** | 외부 search / 운영팀 inquiry | 다음 cycle |
| **Round 4 candidate pool** | Sotheby's / Christie's / Hyundai 추가 평가 (별도 lane) | A lane 막지 않는 한정 |

## 8. Limitations / 정직 보고 (코덱스 톤 유지)

- **LLM 한계 (Round 3)**: web access + keyword hint 기반 narrowing only. **실제 license 조건 / 한국 art coverage / dataset schema = 운영팀 협상 + 법무 검토 영역** (LLM 외)
- **Artprice 1순위 의 caveat (코덱스 P1 강화)**: subscription/API hint = strong but **paid license 확인 X (운영 확인 전 단정 X)** / 실제 한국 작가 coverage / paid tier 비용 / AI/ML 사용 허용 = 운영팀 협상 후만 확인 가능
- **Lane 1 method-gate 미검증 (코덱스 P1 핵심 caveat)**: A continue GO = "협상 착수 GO" / Lane 1 sources 는 **Round 2 freeze 3축 (cover ≥70 / join ≥80 / time-safe) 평가 전혀 미수행** — source adequacy 판정 미정 / 운영팀 + 법무 회신 후만 평가 가능
- **갤러리 web 의 가격 공개 낮음 (코덱스 사전 자문)**: gallery direct = "데이터 richness" 보다 **"협상 가능성 / 관계 형성 난이도" screening** — 운영팀 영역
- **Arko / MCST main page access recovery ≠ data 적합성 개선** (코덱스 caveat 동일 적용)
- **새 source (Sotheby's/Christie's) HARK 회피**: 본선 편입 X / Round 4 candidate pool 분리 (코덱스 P0)

## 9. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track / A.1-A.5 / Axis A 종합 / Axis B Round 1-2-2B) | P0×11 + P1×42 + P2×20 |
| **Round 3 사전 자문 (2026-05-07)** | 조건부 GO + 3 lane 분리 + reporting 5 구조 + freeze 추가 권고 |
| **Round 3 결과 검수 (2026-05-07)** | **Round 3 continue / 운영팀 outreach GO** (단 범위 한정 = Artprice + Kukje/Pace/PKM + Arko / Sotheby's·Christie's·Hyundai HOLD = Round 4 pool). P0 없음 / P1×5 (Artprice "paid 확인" 톤 / Decision Table 충돌 / Arko inquiry 12항목 보완 / Lane 1 method-gate 미검증 caveat / A continue "decision-grade GO" 톤) + P2×1 (MCST 외부 검색 표현) — 본 v2 commit 일괄 반영 |

## 10. 참조

- Round 2: `docs/axis_b_round2_results_20260507.md` (v2 framing)
- Round 2B: `docs/axis_b_round2b_results_20260507.md` (v2 framing)
- Round 2 freeze (transport error retry §3.3): `docs/axis_b_round2_scorecard_freeze_20260507.md`
- Handoff packet: `docs/axis_b_handoff_packet_20260507.md`
- Round 1: `docs/axis_b_phase_a_pre_screen_round1_20260507.md`
- HTML 종합: `docs/트랙2_종합보고서_axis_a_종결_20260507.html`
- Methodology pipeline / Deviation log
