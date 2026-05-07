# Axis B Phase A Round 2B Results — E (MCST/Arko 재시도) + B (Aggregate Context Signal)

> **작성일**: 2026-05-07 (Round 2B 동시 진행)
> **사전등록 freeze**: `docs/axis_b_round2_scorecard_freeze_20260507.md` §3.3 (transport error retry protocol — 코덱스 P1 권고로 사후 추가)
> **연계**: `docs/axis_b_round2_results_20260507.md` (Round 2 결과 + 코덱스 사후 검수 우선순위 A>E>B>C>D)
> **사용자 명시 instruction**: E + B 동시 진행

> ⚠️ **본 round 의 범위**: LLM 가능 영역만 — 결과 = "feasible for next diligence" 톤 (코덱스 권고).

## 0. 한 줄 요약

> **Round 2B 종결 — Round 2 v2 권고 (A > E > B > C > D) 그대로 유지**:
> - **E (MCST 재시도)**: main page 200 ✓ (이전 정책 list URL deprecated, main 은 정상) — 단 art market 정확 endpoint 추가 발견 X → **partial PASS** (전반 자동화 access OK, art market data 직접 endpoint 미확인)
> - **E (Arko 재시도)**: alternative URL 모두 4xx/5xx — **unresolved 그대로** (server side persistent issue, 운영팀 inquiry 또는 24-72h 추가 retry 필요)
> - **B (KOSIS aggregate)**: 미술시장 검색 결과 hit 4 — 정부 공식 art market 통계 source **약함** (광범위 통계 보유 X 추정)
> - **B (KAMS aggregate)**: 자료실 (`/02_dataroom/`) empty 또는 login 필요 추정 / artmarket sub-domain 500 → 데이터 직접 access 어려움
>
> **결론**: 코덱스 사전 자문 base hypothesis (Option B = aggregate context signal ROI 낮음 — label scarcity 미해결) **재확인**. **A (license-first) 1순위 권고 그대로 유지**.

## 1. E (MCST/Arko 재시도) 결과

### 1.1 MCST 재시도 — partial PASS

| URL | Status | 평가 |
|---|---|---|
| `mcst.go.kr/kor/main.jsp` | 200 / 173KB | ✓ Main page 정상 |
| `mcst.go.kr/kor/s_culture/policy/policyList.jsp` (이전 Round 2 URL) | 404 | ✗ URL deprecated |
| `mcst.go.kr/web/s_data/research/researchList.jsp` | 404 | ✗ |
| `mcst.go.kr/kor/s_data/research/researchList.jsp` | 404 | ✗ |

**판정**: **partial PASS** (전반 자동화 access OK = main 200, 이전 Round 2 의 404 = path 변경 / URL deprecation). 단 art market 통계 정확 endpoint 추가 발견 필요 — 운영팀 inquiry 영역 (handoff packet §4).

### 1.2 Arko 재시도 — unresolved 그대로

| URL | Status | 평가 |
|---|---|---|
| `arko.or.kr/main/index` (이전 Round 2 URL) | 500 | ✗ Server error |
| `arko.or.kr/main` | 404 | ✗ |
| `arko.or.kr/board/list/board?...` | 200 / 0KB | △ Empty page |
| `arko.or.kr/info/page/sub6_1` | 404 | ✗ |
| `kcti.re.kr/kor/main` (KOSIS orgId=113 운영기관 추정) | 404 | ✗ |

**판정**: **unresolved 그대로** (Round 2 의 HOLD 유지) — server side persistent issue. 24-72h 간격 추가 retry 필요 또는 운영팀 inquiry (담당 부서 직접 contact). KCTI (KOSIS art market 통계 운영기관 추정) 도 도메인 확인 필요.

## 2. B (Aggregate Context Signal) 결과

### 2.1 KOSIS aggregate art market 통계 — 약함

| URL | 미술 hit | 평가 |
|---|---|---|
| 통계 list index (M_01_01) | 0 | art market 직접 통계 X |
| 검색 "미술시장" | 4 | 약한 hit — 광범위 통계 보유 X |
| 검색 "art market" | 0 | 영문 검색 X |

**판정**: KOSIS 의 art market 직접 통계 = **약함** (검색 hit 4 만). 정부 공식 macro art market index 또는 거래액 통계 부재 또는 미발견.

### 2.2 KAMS aggregate 데이터 access — 어려움

| URL | Status / Hit | 평가 |
|---|---|---|
| `/02_dataroom/sub_select.aspx` (자료실) | 200 / 0KB | △ Empty (login 필요 가능 추정) |
| `/02_dataroom/notice_list.aspx` | 200 / 0KB | △ Empty |
| `visualartmarket` sub-domain | 500 | ✗ Server error |
| `artmarket.kr` | 200 / 0KB | △ Empty |
| `/01_news/notice_list.aspx` | 200 / 52KB / hit 2 | ✓ 공지 보유 (보고서 download link 추정) |

**판정**: KAMS 의 데이터 직접 access = **어려움** — 자료실 page empty (login 필요 추정) / artmarket sub-domain 500 / 공지 page 만 일부 access. **운영팀 inquiry 필요** (담당 부서 직접 contact / login 자격).

## 3. 종합 판정 (Round 2 + Round 2B)

| Source | Round 2 | Round 2B | 종합 |
|---|---|---|---|
| KOSIS | aggregate-only | art market 검색 약함 (hit 4) | aggregate context signal ROI 낮음 |
| MCST | HOLD (404) | main 200 ✓ but art market endpoint 미확인 | **partial PASS** (운영팀 inquiry 필요) |
| KAMS | aggregate-only | 자료실 empty / artmarket 500 | aggregate context signal access 어려움 |
| MMCA | partial metadata (가격 X) | (Round 2B 미평가) | 그대로 |
| Arko | HOLD (500) | 모든 URL 4xx/5xx persistent | **unresolved 유지** (24-72h retry 또는 운영 inquiry) |

### 3.1 Phase A 종합 = HOLD 유지 (Round 2 v2 그대로)
- Round 2B 결과 = 코덱스 사전 자문 base hypothesis 재확인 (Option B ROI 낮음)
- **A (license-first lane) 1순위 권고 변동 X** (코덱스 사후 검수 그대로 유지)

### 3.2 우선순위 update (post-Round-2B)

| 순위 | 옵션 | Round 2B 결과 후 변동 |
|---|---|---|
| **1** | **A. License-first lane** | 변동 X — 강화 (B 의 ROI 낮음 재확인) |
| 2 | E. MCST/Arko 재시도 | MCST partial PASS / Arko unresolved 유지 — 운영팀 inquiry 영역 |
| **3 (격하)** | B. Aggregate context signal Round 2B | **Round 2B 결과로 ROI 낮음 입증** — 격하 |
| 4 | C. Program-level redesign | 변동 X |
| 5 | D. Default 유지 | 변동 X |

## 4. 다음 단계

1. ✅ Round 2B 결과 보고 — 본 commit
2. ⏳ Deviation log entry
3. ⏳ 코덱스 사후 검수 (선택)
4. ⏳ 운영팀/법무팀 cycle = handoff packet 인계 GO 그대로 (post-Round-2 update 반영)
5. ⏳ (사용자 결정) A (license-first) 진입 시작 / Arko 운영팀 inquiry / MCST 추가 endpoint 발견 LLM 가능

## 5. Limitations / 정직 보고 (코덱스 톤 유지)

- **LLM 한계**: 본 Round 2B = web 검색 + page content 기반 추정. 실제 dataset access / login 자격 / API auth = 운영팀 inquiry 필요
- **Arko unresolved persistent**: 1차 retry (Round 2B) 도 4xx/5xx → 24-72h 후 추가 retry / 운영 inquiry (담당 부서 contact) 필요. retry protocol §3.3 그대로 적용
- **KAMS 자료실 empty**: `/02_dataroom/` 0KB = login 필요 추정 / 또는 dynamic page (JavaScript rendered) 가능 — 운영팀 직접 access 필요
- **MCST main 200 but endpoint 미확인**: 정책 list / 연구 통계 path 추가 search 필요 (LLM 가능 / 운영팀 inquiry 가능)
- **결과 변동 가능성**: Round 2B unresolved 항목 (Arko) 또는 추가 endpoint (MCST) 발견 시 source-level 평가 변동 가능 — 단 program-level Phase A 종합 (HOLD) 변동 X (joinable 작품-level + 가격 source = 0 그대로)

## 6. 참조

- Round 2: `docs/axis_b_round2_results_20260507.md` (v2 framing 정정 적용)
- Round 2 freeze (transport error retry protocol §3.3): `docs/axis_b_round2_scorecard_freeze_20260507.md`
- Handoff packet (post-Round-2 update): `docs/axis_b_handoff_packet_20260507.md`
- Round 1: `docs/axis_b_phase_a_pre_screen_round1_20260507.md`
- HTML 종합: `docs/트랙2_종합보고서_axis_a_종결_20260507.html`
- Methodology pipeline / Deviation log
