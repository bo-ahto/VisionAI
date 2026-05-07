# VisionAI 트랙 1 + 트랙 2 종합 현황 보고서 (외부 공유용)

> **작성일**: 2026-05-08
> **대상**: 외부 협력자 / 의사결정자 / 외부 보고 inheriting
> **본 문서 성격**: VisionAI 1차 시장 가격 예측 모델 (트랙 1 = 운영 main 모델 / 트랙 2 = 해석 가능 cold-start 연구 모델) 의 cycle 종합 현황. **외부 공유 가능 수준**의 결과 요약 + 운영 영향 + 다음 단계.

## 1. 목적과 범위

본 보고서는 2026년 5월 시점의 **VisionAI 1차 시장 가격 예측 모델 두 트랙** 의 진행 현황을 외부 협력자 와 의사결정자 가 이해할 수 있도록 종합 정리한다.

**범위**:
- 트랙 1 (운영 main 모델 — `v3_filtered_tuned` 32 features): 사전 정의된 평가 cycle 결과 + 운영 영향
- 트랙 2 (해석 가능 cold-start 연구 모델): 연구 cycle 종결 결과 + 운영 채택 현황 + 제한 후속

**범위 외**:
- 모델 학습 / 학술 방법론 상세 (별도 기술 보고서 참조)
- 운영 환경 deploy / monitoring 인프라 상세
- 데이터 source 운영 협조 (별도 영역)

## 2. Executive Summary (한 페이지)

### 2.1 핵심 결과

| 트랙 | 결과 | 운영 영향 |
|---|---|---|
| **트랙 1** (운영 main 모델) | 사전 정의된 평가 cycle 완료 / **운영 변경 없이 종료** | `v3_filtered_tuned` 32 features 그대로 유지 / 핵심 metric 변화 없음 |
| **트랙 2** (해석 가능 cold-start 연구) | architecture-only 경로 종결 / 연구 학습 확보 / **운영 채택 없음** | 운영 spec 변경 X / 일부 제한적 후속 검토만 잔존 |

### 2.2 한 줄 요약

운영 main 모델 (`v3_filtered_tuned` 32f) 그대로 유지, 트랙 2 해석 가능 모델 연구 cycle 종결 (운영 채택 없음 / 일부 제한 후보 + 1주 shadow 평가 가능).

### 2.3 외부 공유 가능 핵심 metric (트랙 1)

| Metric | 값 |
|---|---|
| Cold-start CatBoost (calibrated) | **38.3%** MdAPE |
| Cold-start offline ensemble (참고용) | 38.7% MdAPE |
| Warm path KFold ensemble | **10.5%** MdAPE |

> **Caveat**: 본 metric 은 offline 평가 기준. 실 운영 시점의 정량은 별도 검증 영역.

## 3. 트랙 1 — 운영 main 모델 평가 cycle

### 3.1 진행 cycle

트랙 1 은 운영 main 모델 (`v3_filtered_tuned` 32 features) 에 대해 **사전 정의된 평가 protocol (pre-registered analysis plan)** 을 도입한 첫 cycle.

진행 단계:
- **Phase 0 freeze**: 평가 baseline / hard gates / locked holdout / decision-binding 사전 정의
- **Stage 1 audit**: feature integrity 점검 (학습-서빙 일관성)
- **Amendment**: 발견된 mismatch 후보 (9 features) 의 fix set 사전 정의
- **Audit 4**: drift fix variant (23 features) 의 OOF 평가

### 3.2 결과

평가 cycle 의 사전 정의된 stop criteria (운영 변경 의사결정 의 임계 조건) 이 정상 작동:

| 평가 항목 | 사전 임계 | 결과 | 판정 |
|---|---|---|---|
| Overall MdAPE 개선 | ≤ -0.7%p | +0.70%p 악화 | 미충족 |
| Source slice 비대칭 | ±0.5%p 이내 | Saatchi +1.80%p / Artsy -0.10%p | 미충족 |
| Warm path non-regression | ≤ +0%p | +0.00%p (동등) | 충족 |

→ 사전 임계 미충족 → **운영 변경 없이 cycle 종료** (사전 정의된 의사결정 logic 정상 작동).

### 3.3 부수적 finding

평가 cycle 진행 중 일부 입력 신호 (32 features 중 9개) 에서 **학습-서빙 정합성 mismatch 징후** 확인. 본 finding 은 reported offline metric 의 해석에 대한 추가 검증 필요성 시사 (정량 미확정).

본 finding 은 **운영 변경 trigger 가 아닌** exploratory diagnostic 으로 분류. 후속 정량 평가 = 운영 측 actual value 추출 가능성 검토 영역 (별도 운영팀 inquiry).

### 3.4 본 cycle 의 의미

- **사전 정의된 평가 protocol** 의 첫 cycle 정상 종료 (결과 본 후 합리화 회피)
- 운영 변경 없이 cycle 종료 = baseline 안전성 유지
- 부수 finding (학습-서빙 mismatch 징후) 은 별도 검증 영역으로 분리

### 3.5 외부 공유 가능 reference

- `docs/트랙1_종합보고서_20260507.html` — 트랙 1 상세 결과 보고서 (외부 공유 가능)

## 4. 트랙 2 — 해석 가능 cold-start 연구 모델

### 4.1 트랙 2 의 위치

트랙 2 는 운영 main 모델 (트랙 1, gradient boosting) 와 **별개의 연구 트랙** — cold-start (작가 신규 등) 영역 에서 **해석 가능한 hedonic 모델** 의 채택 가능성 평가.

### 4.2 진행 cycle 종합

| Cycle | 본질 | 결과 |
|---|---|---|
| Stage 2 freeze (2026-05-06) | 5 family (작가 / 작품 / 갤러리 / source / level) 확정 | 본질 |
| Stage 3 (Huber + spline + warm-start 검증) | exploratory 통과 | 정상 |
| Stage 4 v3 (Artsy 8,891 cleansed / 823 작가) | 보류 / 일반 warm 경로 진입 X | 보류 |
| Stage 5 (외부 데이터 source acquisition) | 4 source 평가 / Artsy CV 1 BORDERLINE / 다른 3 source REJECT | 미진입 |
| Stage 6A (Segmented architecture) | 미충족 (저가 segment harm) | 미채택 |
| Stage 6B (Partial pooling architecture) | 미충족 (사실상 동등 + 저가 harm) | 미채택 |
| **Architecture-only close 확정** | 3-cycle empirical + 1-cycle acquisition infeasibility | 확정 |

### 4.3 Feature Track Axis A (5 step 종결)

architecture close 후 후속 — Feature augmentation 5 axis 평가:

| Step | 가설 | 결과 |
|---|---|---|
| A.1 | Cheap categorical (4종) | BORDERLINE (보류) |
| A.2 | Artist popularity | 미충족 |
| A.3 | Gallery cluster embeddings | BORDERLINE (가장 강한 신호) |
| A.4 | Title text embedding (multilingual MiniLM) | 미충족 |
| A.5 | Image embedding (CLIP-ViT-B-32) | 미충족 (near-null) |

→ **Axis A 5 step 모두 운영 채택 임계 미충족** (BORDERLINE 2건 + 미충족 3건).

### 4.4 종합 결론

- **architecture-only 경로 종결**: 동일 feature set 안에서 architecture 만 변경하는 접근은 1차 병목 해결 X
- **cheap-feature-only 경로 종결**: Axis A 5 step 모두 hard gate 통과 X
- **운영 채택 없음**: 운영 spec 변경 X / 운영 main 모델 (트랙 1) 그대로 유지

### 4.5 제한 후속 (operational intake 후보)

- **Slice-conditional warm path** (depth ≥ 25 + seen-in-training): 제한 후보로 유지 / 깊이 25+ 작가 영역에서 -14.18%p 강한 개선 입증
- **Phase A shadow 1주 착수 승인 가능**: 일반 warm 경로 운영 미승인 / Slice-conditional 제한 후보 만 shadow 평가 가능
- **Phase B (full rollout)**: 미승인 / shadow PASS 후 별도 승인 영역

### 4.6 외부 데이터 source 영역 (별도 트랙)

외부 데이터 source 의 license / 운영 협조 영역은 운영팀 + 법무팀 회신 대기 (외부 공유 가능 결과 외 영역).

### 4.7 외부 공유 가능 reference

- `docs/트랙2_종합대시보드_20260507.html` — 트랙 2 인덱스 / 상태 (외부 공유 가능)
- `docs/트랙2_종합보고서_axis_a_종결_20260507.html` — Axis A 5 step 종결 결과 보고서
- `docs/트랙2_최종보고서_20260506.html` — 트랙 2 최종 보고서
- `docs/임원보고_트랙2_요약_20260506.html` — 트랙 2 임원 요약

## 5. 운영 영향

### 5.1 현재 운영 상태

- **운영 main 모델**: `v3_filtered_tuned` 32 features (변경 없음)
- **운영 spec**: 트랙 2 영역의 spec §17 변경 없음
- **운영 metric**: 핵심 metric (Cold 38.3% / Warm 10.5%) 그대로 유지

### 5.2 본 두 cycle 의 운영 영향

✅ **즉시 운영 영향 없음** — 두 cycle 모두 운영 변경 없이 종료.

본 cycle 들의 가치:
- 운영 main 모델 의 안전성 검증 (변경 의사결정 의 임계 조건 정상 작동)
- 후속 cycle 의 의사결정 base 확보 (architecture-only / cheap-feature-only 경로 의 한계 입증)
- 외부 협력 영역 (외부 데이터 source / API contract 확장 등) 의 우선순위 재평가 evidence

## 6. 현재 결정 사항

| 항목 | 결정 |
|---|---|
| 트랙 1 운영 main 모델 | **`v3_filtered_tuned` 32 features 유지** |
| 트랙 2 해석 가능 모델 운영 채택 | **채택 없음** (운영 spec §17 변경 X) |
| 트랙 2 architecture 후속 cycle | **종결** (architecture-only 1차 병목 해결 X 입증) |
| 트랙 2 Feature Track Axis A | **5 step 모두 임계 미충족** (Axis A 종결) |
| 트랙 2 Slice-conditional 제한 후보 | **유지** (depth ≥ 25 영역 만 / Phase A shadow 1주 평가 가능) |
| 외부 데이터 source 영역 | **운영팀 + 법무팀 회신 대기** (외부 공유 가능 결과 외 영역) |

## 7. 다음 단계

### 7.1 즉시 가능 영역

1. **Slice-conditional warm path Phase A shadow** 1주 착수 (depth ≥ 25 작가 영역 만)
2. 트랙 1 부수 finding 의 후속 정량 검증 (운영 측 actual value 추출 가능성 검토)

### 7.2 별도 영역 (외부 협력)

1. 외부 데이터 source 의 license / acquisition 협조 (Stage 5 영역)
2. 운영 환경 의 API contract 확장 가능성 (트랙 1 부수 finding 후속)

### 7.3 조건부 후속 cycle

다음 cycle 진입 시 의무:
- 새 baseline / 새 hypothesis family 의 새 사전 정의된 평가 protocol
- 운영 변경 의사결정 = 별도 검증 영역 (현 cycle 의 결과 직접 적용 X)

## 8. 참고 문서 (외부 공유 가능)

### 트랙 1
- `docs/트랙1_종합보고서_20260507.html` — 트랙 1 상세 결과 보고서

### 트랙 2
- `docs/트랙2_종합대시보드_20260507.html` — 트랙 2 인덱스 / 상태
- `docs/트랙2_종합보고서_axis_a_종결_20260507.html` — Axis A 5 step 종결 결과
- `docs/트랙2_종합보고서_axis_b_phase_a_round3_20260507.html` — 외부 데이터 source 영역 Phase A 결과
- `docs/트랙2_최종보고서_20260506.html` — 트랙 2 최종 보고서
- `docs/임원보고_트랙2_요약_20260506.html` — 트랙 2 임원 요약
- `docs/트랙2_쉬운설명_20260506.html` / `docs/트랙2_프로세스_쉬운버전_20260506.html` — 비전공자 / 외부 협력자 친화 설명

### 모델 기술 보고서
- `docs/model_technical_report.md` / `.html` — v1 (이론·아키텍처 본문)
- `docs/model_technical_report_v2.md` / `.html` — v2 (피드백 적용 후속편)

---

**본 보고서의 위치**: 외부 공유용 standalone 종합 보고서 (executive HTML 요약본 = `docs/external/external_track1_track2_status_20260508.html`).
