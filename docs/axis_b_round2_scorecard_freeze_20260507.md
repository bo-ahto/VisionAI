# Axis B Phase A Round 2 — Scorecard Freeze (Pre-registration)

> **작성일**: 2026-05-07 (freeze)
> **위치**: 새 Phase 2'' Axis B (External Acquisition) Phase A pre-screen project — **Round 2 (Data availability + Labelability·Joinability + As-of-time reproducibility 평가)**
> **연계**: `docs/axis_b_phase_a_pre_screen_round1_20260507.md` (Round 1) / `docs/feature_track_design_20260507.md` (Phase A 7항목 정의) / 코덱스 사전 자문 (2026-05-07)

> ⚠️ **freeze 의무 (코덱스 P0)**: Round 2 시작 전 4개 freeze 필수 — (1) 대상 source / (2) 평가축 / (3) threshold / (4) 판정 rule. 결과 본 후 변경 X (HARK 회피).

## 1. Round 2 Scope (freeze)

### 1.1 대상 5 source (Round 1 PASS likely 정부/공공)

| 우선순위 | Source | Domain | Round 1 결과 |
|---|---|---|---|
| 1 | KOSIS (통계청) | kosis.kr | Allow: / 전체 허용 |
| 2 | MCST (문체부) | mcst.go.kr | Allow: / (search 만 disallow) |
| 3 | KAMS (예술경영지원센터) | gokams.or.kr | 부분 disallow / art-specific 공공기관 |
| 4 | MMCA (국립현대미술관) | mmca.go.kr | 정부 공식 |
| 5 | Arko (한국문화예술위원회) | arko.or.kr | Googlebot 일부 disallow |

### 1.2 명시 배제 (HARK 회피, 코덱스 P2)
- ❌ KIAF / 한국화랑협회 — 본선 진입 비권고 / `parallel side-queue` (법무/TOS 선해결 후 재심)
- ❌ Frieze Seoul — REJECT 유지 (서면 허가 / 라이선스 확보 전 예외 path X)
- ❌ Korea Foundation / KOSARC — Round 1 SSL/DNS 에러 추가 확인 필요
- ❌ 새 source 발견 시 본 Round 2 본선 편입 X — `deviation log + Round 2B / Round 3 candidate pool` 분리

## 2. 평가축 3종 (코덱스 권고, freeze)

### 2.1 Data Availability
- **정의**: 본 cycle target cohort (Artsy 8,495 작품 / 807 artists) 대비 source 의 art market 데이터 cover 율
- **평가 method**:
  1. Source 의 documentation / public dataset list 조사
  2. art market 관련 데이터 존재 여부 (작품-level / 작가-level / gallery-level / aggregate-level) 분류
  3. target cohort 대비 cover numerator / denominator 명시
- **PASS threshold**: **cover ≥ 70%** (target cohort 의 majority)
- **단**: aggregate-only source 는 별도 분류 — `MODEL INPUT FAIL / CONTEXT SIGNAL PASS` 이원화

### 2.2 Labelability·Joinability
- **정의**: 본 cycle 의 baseline data (`stage4_full.parquet`) 와 join 가능성
- **평가 method**:
  1. Join key 우선순위: `artist_name canonicalization > work_title > institution/gallery > year/medium/size`
  2. exact match vs fuzzy match 분리 기록
  3. 작품-level vs aggregate-level signal 분리 기록
- **PASS threshold**: **join success ≥ 80%** (작품-level signal 연결 가능)
- **단**: aggregate signal 만 유효 시 `joinability FAIL but context-only PASS`

### 2.3 As-of-time Reproducibility
- **정의**: scrape / API 시점이 sale 시점 이전 정보로 재구성 가능 (시점 정합성 / leakage 방지)
- **평가 method**:
  1. Publication date / update cadence / snapshot / file archive 여부 기록
  2. ex-post aggregation 만 있는지 / 당시 시점 재현 가능한지 분리
- **PASS threshold**: **time-safe yes** (sale 시점 이전 snapshot 확보 가능)
- **단**: ex-post aggregation only 시 `As-of-time FAIL or HOLD`

## 3. 판정 rule (freeze, 코덱스 P0)

### 3.1 Source-level

| 조건 | 판정 |
|---|---|
| 3축 모두 PASS | source PASS (Phase A 통과 후보) |
| Data availability FAIL | source FAIL (3축 중 1개라도 P0 gate fail = FAIL) |
| Joinability FAIL | source FAIL (3축 중 1개라도 P0 gate fail = FAIL) |
| As-of-time FAIL | source FAIL (3축 중 1개라도 P0 gate fail = FAIL) |
| Aggregate-only PASS | `MODEL INPUT FAIL / CONTEXT SIGNAL PASS` (이원화 분류) |

### 3.2 Program-level (5 source 종합)

| 시나리오 | Phase A 종합 판정 |
|---|---|
| 5개 모두 FAIL | **Phase A HOLD** → license-first lane 또는 program-level redesign 검토 |
| 1개만 PASS + aggregate-only | **Phase A HOLD** |
| 2개 이상 PASS + 1개 이상 joinable | **Phase A 조건부 PASS** → 다음 round (Legal/TOS / License) 진입 |
| 모두 PASS + 모두 joinable | Phase A PASS |

## 4. LLM 가능 영역 / 한계 (코덱스 명시)

### 4.1 LLM 가능
- 문서/페이지/데이터셋 설명 기반 구조 분류 (작품-level vs aggregate-level)
- 예상 join key inventory 작성
- 평가표 / scorecard 설계
- source 별 작품-level vs aggregate-level risk 분류

### 4.2 LLM 한계
- 실제 live dataset schema 확정
- hidden download / API / auth 필요 여부 확정
- 약관 해석 확정 (법무팀 영역)
- historical snapshot 존재 여부의 법적 / 운영상 확정

→ **결정급 확정 = 운영 inquiry / 실제 dataset 접근 필요** (운영팀/법무팀 cycle 영역)

### 4.3 결과 문구 제한 (코덱스 권고)
- "feasible for modeling" 단정 X
- **"feasible for next diligence"** 톤 (다음 단계 진입 가능 여부 평가만)

## 5. C 동시 진행 dependency (코덱스 권고)

### 5.1 LLM Round 2 → 운영팀/법무팀 입력
- source 우선순위
- 예상 데이터 구조
- joinability risk
- 추가 inquiry 질문 리스트

### 5.2 법무 → LLM 입력
- 사용 가능 범위 downgrade / upgrade
- 협상 필요 여부

### 5.3 운영 → LLM 입력
- 실제 접근 경로 / API / 파일 / 담당자 확인

### 5.4 진행 순서
- **법무/TOS 검토**: 즉시 병렬 가능 (handoff packet 의 `03_legal_tos_request` 즉시 인계)
- **License outreach**: 조건부 병렬 — LLM Round 2 1차 narrowing 후 시작 효율적
- **LLM Round 2 cycle**: 본 freeze 후 즉시 진행 가능

## 6. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Feature track design / A.1-A.5) | P0×9 + P1×32 + P2×13 |
| **Round 2 사전 자문 (2026-05-07)** | 조건부 GO (4개 freeze 후) + 평가 method + threshold + 판정 rule + handoff packet 7-document 구조 권고 |

## 7. 참조

- Round 1 보고서: `docs/axis_b_phase_a_pre_screen_round1_20260507.md`
- Feature track design: `docs/feature_track_design_20260507.md` (Phase A 7항목)
- HTML 종합 보고서: `docs/트랙2_종합보고서_axis_a_종결_20260507.html` (cover memo)
- Methodology pipeline / Deviation log
