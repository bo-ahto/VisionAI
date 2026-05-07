# Axis B Phase A — Handoff Packet (운영팀 / 법무팀 인계)

> **작성일**: 2026-05-07 (코덱스 권고 7-document 구조 통합)
> **인계 대상**: 운영팀 / 법무팀 / 의사결정자
> **목적**: Axis B Phase A pre-screen project 의 운영팀/법무팀 cycle 시작용 packet (LLM 외 영역 작업 의뢰)

---

## §0 Executive Summary (1 page)

### Why Axis B
- Stage 6 architecture cycle (6A FAIL + 6B FAIL) → Architecture-only close 확정
- Feature Track Axis A 5 step (A.1-A.5) 종결 — 운영 채택 후보 0 (5 step 모두 adoption-grade 미달, A.3 만 promising but non-decision-grade)
- 코덱스 종합 검수 권고: 다음 투자 1순위 = **B (Axis B pre-screen project)**
- 현재 evidence 기반 1차 병목 = **feature/information shortage (현재 curated internal feature ladder + frozen specs 한정)**
- Axis B = **새 lawful external source** 확보 → information bottleneck 정면 대응

### Why Now
- Axis A 5 step 모두 검증 완료 → 내부 feature 한계 확정
- Stage 5 acquisition 종료 후 **새 lawful path 발견 시에만** Axis B 진입 가능 (Stage 5 = 5/5 source REJECT)
- LLM Round 1 (Source Discovery + Access) 완료 — 정부/공공 5개 source = PASS likely
- C 동시 진행 (LLM Round 2 + 운영팀/법무팀 cycle 병렬) 결정

### Decision Ask (의사결정자 + 운영팀 + 법무팀)

> **Round 2 narrowing 결과 반영 (post-Round-2 update, 코덱스 P1)**: Round 2 LLM cycle 결과 (`docs/axis_b_round2_results_20260507.md`) — **0 confirmed joinable / 2 unresolved (transport error) / 3 confirmed aggregate-level** → **A (license-first lane) 가 실질 1순위** (코덱스 사후 검수).

**우선순위 (코덱스 사후 검수, A > E > B > C > D)**:
1. **A. License-first lane 즉시 진입** (1순위): paid vendor scoping (Artprice/Artnet) + gallery direct shortlist (Kukje/학고재/현대) **병렬** — 속도 우선 = vendor / 한국 로컬 적합도 우선 = gallery direct
2. **E. MCST/Arko 재시도** (2순위, 병행): transport error retry protocol 적용 (24-72시간 간격 3회 + alternative URL)
3. **법무팀**: 5개 source 의 Legal / TOS 검토 (§3 의뢰서) — 즉시 병렬 시작 가능 (단 Round 2 결과 후 우선순위는 license 검토 우선)
4. **운영팀**: 5개 source 의 inquiry (§4 inquiry sheet) — license 협상 우선 + KOSIS/KAMS aggregate API 보조
5. **License 협상**: 즉시 시작 (Round 2 narrowing 완료, 사전 자문 권고와 다른 path)
6. **의사결정자**: handoff packet 승인 + 운영팀 / 법무팀 capacity 확정 + license budget 권한

---

## §1 Round 1 결과 요약 (참조 — 본문 = `docs/axis_b_phase_a_pre_screen_round1_20260507.md`)

| 평가 | 개수 | Source |
|---|---|---|
| **PASS likely** (정부/공공) | 5 | KOSIS / MCST / KAMS / Arko / MMCA |
| **부분 PASS** (TOS 검토 필요) | 2 | KIAF / 한국화랑협회 (본선 비포함, side-queue) |
| **REJECT** (AI 명시 금지) | 1 | Frieze Seoul (Content-Signal: ai-train=no, EU Article 4) |
| 추가 확인 필요 | 2 | Korea Foundation (SSL) / KOSARC (DNS) |

---

## §2 Round 2 Scorecard Freeze (참조 — 본문 = `docs/axis_b_round2_scorecard_freeze_20260507.md`)

3축 평가 (코덱스 freeze):
- **Data availability**: cover ≥ 70%
- **Labelability·Joinability**: join success ≥ 80% (작품-level signal 연결)
- **As-of-time reproducibility**: time-safe yes (sale 시점 이전 snapshot)

판정 rule:
- 3축 중 1개라도 fail = source FAIL
- aggregate-only = `MODEL INPUT FAIL / CONTEXT SIGNAL PASS` 이원화
- 2 이상 PASS + 1 이상 joinable = Phase A 조건부 PASS

---

## §3 법무 / TOS 검토 의뢰서 (법무팀 즉시 인계)

### §3.1 검토 대상 5 source

| 순번 | Source | URL | 한국법 / GDPR 관할 |
|---|---|---|---|
| 1 | KOSIS (통계청) | https://kosis.kr | 한국법 (정부 공식) |
| 2 | MCST (문체부) | https://www.mcst.go.kr | 한국법 (정부 공식) |
| 3 | KAMS (예술경영지원센터) | https://www.gokams.or.kr | 한국법 (공공기관) |
| 4 | MMCA (국립현대미술관) | https://www.mmca.go.kr | 한국법 (정부 공식) |
| 5 | Arko (한국문화예술위원회) | https://www.arko.or.kr | 한국법 (공공기관) |

### §3.2 검토 항목

**각 source 별로 다음 7항목 평가**:

| 항목 | 평가 method | 판정 vocabulary |
|---|---|---|
| **Legal** | TOS / 약관 / 한국법 / GDPR 검토 | PASS / HOLD / REJECT |
| **TOS 자동화 조항** | scraping / data mining / API 자동 사용 명시 허용 여부 | PASS / HOLD / REJECT |
| **AI 사용 명시** | AI / ML training 사용 허용 여부 (Frieze 패턴 참고) | PASS / HOLD / REJECT |
| **GDPR / 개인정보** | 개인정보 처리 / 작가 personally identifiable info | PASS / HOLD / REJECT |
| **저작권** | 저작권 침해 risk (작품 image / metadata) | PASS / HOLD / REJECT |
| **상업적 사용** | 상업 / 비상업 구분 / license 필요 여부 | PASS / HOLD / REJECT |
| **재배포** | derivative work / re-distribution 허용 | PASS / HOLD / REJECT |

### §3.3 출력 형식 (법무팀 → LLM/의사결정자)

```
Source: <name>
1. Legal: PASS/HOLD/REJECT — <reason>
2. TOS 자동화: PASS/HOLD/REJECT — <reason>
3. AI 사용: PASS/HOLD/REJECT — <reason>
4. GDPR: PASS/HOLD/REJECT — <reason>
5. 저작권: PASS/HOLD/REJECT — <reason>
6. 상업적 사용: PASS/HOLD/REJECT — <reason>
7. 재배포: PASS/HOLD/REJECT — <reason>

종합: PASS / HOLD / REJECT
권고: <next action — license 협상 / 사용 가능 / 보류 / 거부>
```

### §3.4 우선순위 (코덱스 권고)
- KOSIS > MCST > KAMS > MMCA > Arko (공식성 + access 명시성 + 구조화 통계)
- **조속 검토 권고**: 1-2주 내 1차 결과 / 2-3주 내 종합

---

## §4 운영팀 Inquiry Sheet (운영팀 즉시 인계)

### §4.1 5 source 별 inquiry 항목

각 source 의 다음 정보 확인:

| 항목 | 내용 | LLM 추정 / 실측 필요 |
|---|---|---|
| **API 가용성** | 공식 API 존재 여부 / 인증 필요 / rate limit | 실측 필요 |
| **데이터 download** | 파일 download (CSV / JSON / Excel) 가용성 / format | 실측 필요 |
| **담당자 contact** | 데이터 담당자 이메일 / 부서 / 협력 방식 | 운영팀 inquiry |
| **Historical snapshot** | 과거 시점 데이터 보존 / archive / version 관리 | 운영팀 inquiry |
| **Update cadence** | 데이터 update 주기 (monthly / quarterly / annual) | LLM 추정 가능 |
| **License 비용** | 데이터 사용 비용 / 무료 / paid | 운영팀 inquiry |
| **Access 자격** | 일반 공개 / 연구 협력 / 회원 가입 / 정부 협력 필수 | 운영팀 inquiry |
| **데이터 schema sample** | 실제 row / column 구조 sample | 운영팀 / LLM 일부 가능 |

### §4.2 출력 형식 (운영팀 → LLM/의사결정자)

```
Source: <name>
- API: <Y/N, URL, auth requirement>
- Download: <Y/N, format, link>
- Contact: <name, email, dept>
- Historical snapshot: <Y/N, range, format>
- Update cadence: <frequency>
- License cost: <free / paid, KRW amount>
- Access: <public / research / membership / govt>
- Schema sample: <attached or link>
```

### §4.3 우선순위
- KOSIS API 우선 검색 (정부 통계 = 표준 API 가능성 큼)
- MCST / KAMS / MMCA / Arko 순차

---

## §5 License Fallback Memo

### §5.1 우선순위 (코덱스 권고)
1. **갤러리 직접 license** (Kukje / 학고재 / 현대 등 주요 한국 갤러리) — 협상 필요, 한국 갤러리 art market 직접 데이터
2. **공공기관 직접 요청** (KAMS / MMCA / 정부 통계 부서) — 연구 협력 형태 가능성
3. **Paid vendor** (Artprice / Artnet) — License 비용 발생, 글로벌 art market 데이터

### §5.2 갤러리 직접 license 후보 (참고)
- Kukje Gallery (국제갤러리)
- 학고재 갤러리
- 현대화랑
- 페이스 갤러리 서울
- PKM 갤러리
- 두산갤러리
- (기타 한국화랑협회 회원사)

### §5.3 협상 시점
- LLM Round 2 (Data availability 평가) 후 narrowing 결과 보고 후 시작
- 운영팀 / 법무팀 capacity 확정 후

---

## §6 Deviation Log Entry (참조)

본 handoff packet = `docs/methodology_deviation_log.md` 의 2026-05-07 entry "Axis B Phase A pre-screen Round 1" 후속.

새 source 발견 / 예외 / scope 변경 시:
- `deviation log` 즉시 entry
- `Round 2B` 또는 `Round 3 candidate pool` 분리
- 본 Round 2 본선 편입 X (HARK 회피)

---

## §7 Cover Memo (의사결정자용 한 줄)

> Stage 6B FAIL 후 architecture-only close, Axis A 5 step 종결 후 의사결정자 권고 1순위 = Axis B pre-screen project. Round 1 (Access) 완료 — 정부/공공 5개 PASS likely. **본 packet = Round 2 LLM cycle (Data availability 평가) 와 운영팀/법무팀 cycle (Legal/TOS + 운영 inquiry + License) 의 병렬 진행 입력**. 1-3주 내 종합 평가 후 Phase A 종합 판정 (조건부 PASS / HOLD).

---

## §8 참조 문서 (Round 2 결과 반영, 코덱스 P1 보완)

- **Round 2 결과 (post-narrowing, 1순위 권고 근거)**: `docs/axis_b_round2_results_20260507.md`
- Round 1: `docs/axis_b_phase_a_pre_screen_round1_20260507.md`
- Round 2 Scorecard freeze (transport error retry protocol 포함): `docs/axis_b_round2_scorecard_freeze_20260507.md`
- HTML 종합 보고서: `docs/트랙2_종합보고서_axis_a_종결_20260507.html`
- Feature track design: `docs/feature_track_design_20260507.md`
- Stage 6B close: `docs/stage6b_results_20260507.md`
- Stage 5 acquisition: `docs/stage5a_week2_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
