# Stage 5A Week 3 Decision Memo (초안)

> **작성일**: 2026-05-07 (Week 1 종료 후 미리 준비, 코덱스 권고 #5)
> **목적**: Week 2 (Artsy CV 정량 feasibility) 결과 후 의사결정자 1페이지 input
> **사용 시점**: Week 3 의사결정 회의 — 본 memo 의 분기 A 또는 B 선택

> **현 상태 (Week 1 종결)**: Auction-first 폐기 (사실상 REJECT) + Artsy CV BORDERLINE / 사전등록 §6.2 보류
>
> **Week 2 작업**: Artsy CV 5-10명 sample 의 `solo / group / fair / institution` count parsing 가능성 + 실패율

## 분기 A: Artsy CV 단독 5B 진입

### A.1 조건 (Week 2 합격)
- Artsy CV 5-10명 sample 의 단순 count parsing 성공률 ≥ 80%
- HTML 구조 안정성 확인 (1-2주 내 변경 없음)
- legal: artist 페이지 robots 허용 + TOS 명시 위반 없음
- → **Artsy CV BORDERLINE → PASS-ready 승격**

### A.2 5B Acquisition 작업
- 1,925 작가의 url_cv 페이지 fetch (Crawl-delay 고려, ~3-5일)
- Solo / group / fair / institution count parsing
- Feature dictionary 작성 (`docs/stage5b_feature_dictionary.md`)

### A.3 5C Re-freeze + Modeling
- 5C placeholder F3 (provenance / exhibition) 만 확정 (F1 = 폐기, F2 = market activity 도 별도 검토)
- 5C primary 가설 PASS 확률: **낮음** (코덱스) — F1 부재 시 -2.0%p 도달 어려움
- 사전등록 §6.1 PASS 미달 시 → BORDERLINE (-2.0 < Δ ≤ -0.8%p) 또는 FAIL

### A.4 위험
- 5C FAIL 시 외부 source 보강 효과 입증 X
- 운영 적용 X
- Stage 5 자체 재검토 (Stage 6 segmented architecture 등)

## 분기 B: Stage 5 종결 + Calibration only

### B.1 조건 (Week 2 실패)
- Artsy CV parsing 실패율 > 30% (HTML 불안정 또는 schema 차이)
- 또는 단순 count 외 추가 정보 추출 비용 매우 큼
- → **Artsy CV BORDERLINE → REJECT**

### B.2 Stage 5 종결 결정
- 사전등록 §6.3 적용 (모든 source REJECT)
- Stage 5 cycle 종결 + 운영 적용 X (재학습 X)
- 운영 spec 변경 = **단기 트랙 작업 4 (Global additive calibration)** 만 채택

### B.3 운영 channel
- Spec §4 (drift / 재학습) 후처리 후보 → Cold baseline 한정 shadow 도입
- Slice-conditional warm path 보류 (Stage 4 결과 그대로 유지)
- 다른 cycle (Stage 6 = segmented architecture / Bayesian / 새 모델 family) 별도 검토

### B.4 의사결정자 framing (코덱스)
> "Stage 5 = External feature acquisition 가설 검증 cycle. 본 cycle 결과 = 현 cohort + 가용 source 환경에서 acquisition 으로 가격 결정 요인 부재 해결 X. 단기 안전장치 (calibration) 만 운영 적용, 본질 해결은 Stage 6 (architecture / new family) 에서 검토."

## 분기 비교표

| 항목 | 분기 A (Artsy CV 단독 5B) | 분기 B (Stage 5 종결) |
|---|---|---|
| 운영 적용 가능성 | **낮음** (5C PASS 확률 낮음, 코덱스) | 즉시 (calibration shadow) |
| 일정 | 4-6주 (5B 3주 + 5C 2-3주) | 1주 (calibration spec 갱신) |
| 위험 | 5C FAIL 시 sunk cost | Stage 5 자체 종결 인정 |
| 다음 cycle | Stage 6 (실패 시) | Stage 6 직행 |
| 의사결정자 메시지 | "F3 단독 시도, PASS 확률 낮으나 진행" | "Acquisition 가설 검증 종결, calibration 만 운영" |

## 권고 (코덱스 우선순위)

> Week 2 결과 의존. Artsy CV parsing 실패율 < 20% + 안정성 확인 시 **분기 A 진행** (단, 5C PASS 기대 낮음 명시). 그 외 **분기 B 종결**.

### 즉시 가능 (의사결정 전 input)
- 5C prereg 에 "F1 부재 시 PASS 기대 낮음" 리스크 문구 추가 (코덱스 권고 #7)
- methodology log 5A minor / 5C 실질 제약 분리 (코덱스 권고 #4)

### Week 2 의무 (분기 결정용)
- Artsy CV 5-10명 sample parsing 측정
- HTML schema / robots / TOS 정량 검증
- 실패율 + 안정성 결과 → 분기 A/B 선택

## 참조

- Stage 5A prereg: `docs/stage5a_acquisition_prereg_20260507.md`
- Stage 5C prereg: `docs/stage5c_modeling_prereg_20260507.md`
- Week 1 결과: `docs/stage5a_source_scorecard_20260507.md`
- 단기 트랙 결과 (calibration): `docs/stage4_short_term_track_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
