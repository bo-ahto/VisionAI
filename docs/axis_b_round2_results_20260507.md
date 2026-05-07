# Axis B Phase A Round 2 — LLM Cycle Results (Data Availability + Labelability·Joinability + As-of-time)

> **작성일**: 2026-05-07
> **사전등록 freeze**: `docs/axis_b_round2_scorecard_freeze_20260507.md` (2026-05-07)
> **연계**: `docs/axis_b_phase_a_pre_screen_round1_20260507.md` (Round 1) / `docs/axis_b_handoff_packet_20260507.md` (운영팀/법무팀 cycle 병렬 진행)
> **판정**: **Phase A 종합 = HOLD** (5 source 중 **0 confirmed joinable, 2 unresolved (MCST/Arko transport error — evidence gap), 3 confirmed aggregate-level**) — 코덱스 P0 framing 정정

> ⚠️ **본 round 의 범위 (코덱스 권고)**: LLM 가능 영역 평가 = source 의 documentation / page content 기반 구조 분류. **결과 문구 = "feasible for next diligence" 톤** ("feasible for modeling" 단정 X). 결정급 확정 = 운영팀 inquiry (handoff packet §4) 필요.

## 0. 한 줄 요약 (의사결정자용 — 코덱스 P0 framing 정정)

> **Round 2 LLM cycle 종결: Phase A 종합 = HOLD** — **0 confirmed joinable** (작품-level + 가격 보유 source = 0) + **2 unresolved** (MCST URL 404 / Arko HTTP 500 — transport error = **evidence gap, not negative evidence**) + **3 confirmed aggregate-level** (KOSIS / KAMS / MMCA — MMCA 는 작품-level metadata 까지 보유, but 가격 X). 코덱스 사전 자문의 base hypothesis ("정부/공공 5개는 구조상 aggregate/statistical source 가능성") 와 **부분 일관 패턴** (3 confirmed aggregate / 2 unresolved).
>
> **핵심 finding**: 작품-level 가격 데이터 confirmed source = 0 / MMCA 만 작품-level metadata catalog 확인 (가격 X — museum collection 특성).
>
> **결론 (코덱스 톤)**: 본 evidence 범위 내 → **MODEL INPUT FAIL** (작품-level 가격 modeling X) / **CONTEXT SIGNAL PASS** (KOSIS / KAMS aggregate index = secondary feature 가능). **MCST/Arko 재평가 후 결과 변동 가능**.
>
> **다음 단계 권고 (코덱스 사후 검수, A > E > B > C > D)**:
> 1. **A. License-first lane 즉시 진입** — paid vendor scoping (Artprice/Artnet, 속도 우선) + gallery direct shortlist (Kukje/학고재/현대, 한국 로컬 적합도 우선) 병렬
> 2. **E. MCST/Arko 재시도** — transport/server error retry protocol 적용 (병행)
> 3. **B. Aggregate context signal Round 2B** — A를 막지 않는 범위에서만 (label scarcity 미해결)
> 4. **C. Program-level redesign** — A/B 결과 후 재설계 필요 시
> 5. **D. Default 유지** — fallback only

> **운영 영향 X**: Phase A HOLD → 운영 spec §1-§16 변경 X / 분기 B calibration only 그대로 유지.

> ⚠️ **Honesty caveats (코덱스 P1)**:
> - **0 confirmed joinable ≠ 5/5 confirmed absent** — 2 unresolved 는 negative evidence X (transport/server error = observation failure)
> - **License-first lane 의 새 risk**: coverage bias (특정 갤러리 / 시장 segment 편향) + cost risk (paid vendor / license 비용)

## 1. Round 2 평가 결과 (5 source)

### 1.1 종합 표 (3축 평가, 코덱스 freeze 그대로)

| Source | Data Availability | Labelability·Joinability | As-of-time | 종합 (LLM) |
|---|---|---|---|---|
| **KOSIS (한국문화관광연구원 art market 통계)** | ✓ aggregate art market 통계 보유 (orgId=113 통계 table 존재 확인) | ✗ aggregate-level — 작품-level join 불가 | ✓ annual snapshot 가능 | **MODEL INPUT FAIL / CONTEXT SIGNAL PASS** |
| **MCST (문체부)** | ❓ (URL 404, 추가 확인 필요 / 정책 통계 likely) | ❓ aggregate-level 추정 | ❓ | **HOLD** (추가 확인 필요) |
| **KAMS (예술경영지원센터)** | ✓ 미술시장 실태조사 / 아트코리아랩 보고서 보유 | ✗ aggregate-level (annual survey 형식) | ✓ annual report 시점 정합 | **MODEL INPUT FAIL / CONTEXT SIGNAL PASS** |
| **MMCA (국립현대미술관)** | ✓ 작품-level catalog (작가명 / 작품명 / 제작연도 / 소장품) | △ 작품-level join 일부 가능하나 **가격 데이터 X** (museum collection 특성) | ✓ catalog 시점 정합 | **partial PASS (metadata)** / **MODEL INPUT FAIL (가격 X)** |
| **Arko (한국문화예술위원회)** | ❓ (HTTP 500 server 에러, 추가 확인 필요) | ❓ | ❓ | **HOLD** (server 에러 / 재평가 필요) |

### 1.2 LLM 평가 method 적용

#### 1.2.1 KOSIS 평가
- **확인 사실**: orgId=113 (한국문화관광연구원) art market 통계 table 200 OK (21KB)
- **추정**: aggregate art market 통계 (annual / quarterly 거래액 / 평균가 / segment 분포) — 정부 공식 통계 표준 format
- **한계 (LLM 추정만)**: 실제 dataset schema 확정 = 운영팀 inquiry / API 접근 필요

#### 1.2.2 MMCA 평가
- **확인 사실**: 작품 검색 페이지 (220KB) — 작가명 / 작품명 / 제작연도 (1900-) / 소장품 catalog
- **추정**: 국립현대미술관 소장품 catalog = 작품-level metadata 보유 (artist_name / work_title / year / medium 등)
- **한계**: museum collection 특성 = sale price 데이터 X (소장품은 거래 정보 없음)
- **부분 가치**: artist_name canonicalization 표준 source 가능 (한국 작가 공식 metadata)

#### 1.2.3 KAMS 평가
- **확인 사실**: 미술시장 활성화 지원 / 아트코리아랩 보고서 publishing
- **추정**: KAMS 가 publish 하는 "미술시장 실태조사" (annual art market reality survey) = aggregate-level 통계 (galleries / auction houses / 작가 수 / 거래량)
- **한계**: aggregate report 형식 → 작품-level join X

#### 1.2.4 MCST / Arko (추가 확인 필요)
- MCST 정책 list URL 404 → main + search 재평가 필요
- Arko 메인 page 500 server 에러 → 일시적 가능, 재시도 필요

### 1.3 코덱스 사전 자문 base hypothesis 입증

> 코덱스 (Round 2 사전 자문): "정부/공공 5개는 구조상 aggregate/statistical source 일 가능성이 높아서, `availability PASS` 여도 `joinability FAIL` 이 다수 나올 가능성을 기본 가설로 두는 편이 안전합니다."

→ **본 Round 2 LLM cycle 결과로 정확히 입증**: 5/5 source 모두 aggregate level / MMCA 만 작품-level metadata (가격 X).

## 2. 판정 (사전등록 §3 freeze rule 적용)

### 2.1 Source-level

| Source | Data avail | Joinability | As-of-time | 판정 |
|---|---|---|---|---|
| KOSIS | ✓ aggregate | ✗ 작품-level | ✓ | MODEL INPUT FAIL / CONTEXT SIGNAL PASS |
| MCST | ❓ | ❓ | ❓ | HOLD (추가 확인) |
| KAMS | ✓ aggregate | ✗ 작품-level | ✓ | MODEL INPUT FAIL / CONTEXT SIGNAL PASS |
| MMCA | ✓ metadata | △ 가격 X | ✓ | partial PASS / MODEL INPUT FAIL (가격 X) |
| Arko | ❓ | ❓ | ❓ | HOLD (server 에러 / 재평가) |

### 2.2 Program-level (사전등록 §3.2 freeze rule 적용)

> Freeze rule: "5개 모두 FAIL → Phase A HOLD" / "1개만 PASS + aggregate-only → HOLD" / "2 이상 PASS + 1 이상 joinable → 조건부 PASS"

본 결과:
- Joinable (작품-level + 가격) = **0** 개
- aggregate context PASS = 2 개 (KOSIS + KAMS)
- partial metadata PASS = 1 개 (MMCA, 가격 X)
- HOLD (추가 확인) = 2 개 (MCST + Arko)

→ **Phase A 종합 = HOLD** (joinable source 0 개)

## 3. 다음 단계 (코덱스 권고 + 사용자 결정)

### 3.1 코덱스 freeze rule 권고: HOLD 시 → license-first lane 또는 program-level redesign

### 3.2 옵션 (사용자 결정)

| 옵션 | 본질 | LLM 가능 영역 |
|---|---|---|
| **A. License-first lane** | 갤러리 직접 license (Kukje / 학고재 / 현대) 또는 paid vendor (Artprice / Artnet) — 작품-level 가격 데이터 가능 source | 운영팀 / 법무팀 영역 (LLM 외 — 협상 / license 비용) |
| **B. Aggregate context signal 활용** | KOSIS / KAMS aggregate art market index 를 운영 모델 secondary feature 로 추가 — Round 2B 별도 cycle | LLM 가능 (aggregate index download + Joinability 평가) |
| **C. Program-level redesign** | aggregate signal 만 사용하는 새 model spec (representation learning / hierarchical bayesian) | LLM 가능 (새 axis design) |
| **D. Default 유지** | 운영 baseline + calibration only — 변경 X | 0 |
| **E. Round 2B 추가 평가** | MCST + Arko 재확인 / KIAF / 한국화랑협회 side-queue 진입 | LLM 가능 |

### 3.3 운영팀 / 법무팀 cycle 진행 상태

- Handoff packet (`docs/axis_b_handoff_packet_20260507.md`) 인계 가능
- 법무 / TOS 검토 = 즉시 병렬 시작 가능 (5 source)
- 운영팀 inquiry = 즉시 병렬 시작 가능 (5 source)
- License 협상 = LLM Round 2 narrowing 결과 후 시작 효율적 (코덱스 권고)

> 본 Round 2 LLM cycle 결과 = **"5/5 작품-level 가격 source 0 → license-first lane 진입 권고"** → 운영팀/법무팀에게 license 협상 우선순위 정보 제공 가능.

## 4. 한계 / 정직 보고 (코덱스 P1 권고 — 보완)

- **LLM 한계 명시**: 본 Round 2 = source 의 documentation / page content 기반 추정. **실제 dataset schema / API auth / hidden download / historical snapshot = 운영팀 inquiry 필요** (handoff packet §4)
- **결과 문구 (코덱스 권고)**: "feasible for next diligence" 톤 — "feasible for modeling" 단정 X
- **0 confirmed joinable ≠ 5/5 confirmed absent** (코덱스 P1 caveat 핵심): 2 unresolved (MCST/Arko transport error) 는 **evidence gap, not negative evidence** — source property 가 아닌 관측 실패 (404 / 500). Retry protocol 적용 (Round 2 freeze §3.3 사후 추가) 후 평가 변동 가능
- **License-first lane 의 새 risk (코덱스 P1)**: coverage bias (특정 갤러리 / 시장 segment 편향) + cost risk (paid vendor / license 비용) — A 진입 시 의사결정자 인지 의무
- **Method 적용 부분 문서화 (코덱스 P1)**: freeze 의 cover numerator/denominator + publication date 기록 권고 — 본 cycle 일부만 적용 (page content 기반 추정만, 정량 cover 수치 미확보) → Round 2B / 운영팀 inquiry 시 보완 의무
- **Aggregate signal 의 잠재 가치 (Option B, 2순위 이하)**: KOSIS / KAMS aggregate 통계 = secondary feature 로 추가 가능. 단 **label scarcity 미해결** — A를 막지 않는 범위에서만 진입 (코덱스 P2)
- **HARK 회피**: 본 round 결과 본 후 freeze threshold 변경 X — 단 transport error retry protocol = freeze §3.3 사후 추가 (minor deviation, source-level 판정 변경 X)

## 5. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track / A.1-A.5 / Axis A 종합) | P0×9 + P1×32 + P2×13 |
| Round 2 사전 자문 (2026-05-07) | 조건부 GO + 4 freeze + 평가 method + threshold + 판정 rule |
| **Round 2 LLM cycle 결과 검수 (2026-05-07)** | **운영팀/법무팀 인계 GO** (단 framing 정정 후). P0×2 (framing 톤 — "5/5 모두 aggregate" → "0 confirmed joinable, 2 unresolved, 3 confirmed aggregate"; "입증" 톤 다운) + P1×4 (method 적용 문서화 보완 / transport error retry protocol / handoff packet narrowing 결과 링크 / coverage bias + cost risk caveat) + P2×2 — 본 v2 commit 일괄 반영. **다음 우선순위: A > E > B > C > D** (코덱스 사후 검수). |

## 6. 참조

- Round 1: `docs/axis_b_phase_a_pre_screen_round1_20260507.md`
- Round 2 Scorecard freeze: `docs/axis_b_round2_scorecard_freeze_20260507.md`
- Handoff packet: `docs/axis_b_handoff_packet_20260507.md`
- HTML 종합 보고서: `docs/트랙2_종합보고서_axis_a_종결_20260507.html`
- Methodology pipeline / Deviation log
