# Cold Rollout Shadow Runbook (Phase A)

> **작성일**: 2026-05-07
> **대상**: 운영팀 / 인프라 담당자
> **연계**: `docs/트랙2_production_통합_spec_20260507.md` §11.1 (Phase A 합격 기준), §15 (운영 Runbook), §6 (운영 안전 보장)
> **목적**: Phase A (0% shadow, 1주) 운영 시 매일 점검 체크리스트 + 트러블슈팅 가이드

> **코덱스 권고 핵심**: Phase A shadow 의 1차 목표는 **성능 측정이 아닌 파이프라인 parity / fallback / 로그 완전성** 검증. baseline 정체성 붕괴가 발견되면 Stage 4 freeze 보다 먼저 fix.

## 1. 사전 준비 (D-1, shadow 배치 전)

### 1.1 모델 / Pipeline 고정
- [ ] 운영 채택 model hash: `track2_v1_20260507` (F4 + log_area spline + Huber eps=1.35 alpha=1e-4)
- [ ] Feature pipeline version: `f4_spline_v1_20260506`
- [ ] Train data hash: `data/curated/stage3_1000x100.parquet` SHA (현 운영 학습 데이터, latest 사용 X — 명시적 freeze)
- [ ] **Stage 4 model/pipeline 동일 hash 보장** (Stage 4 의 train data 는 별개 — `data/curated/stage4_*.parquet`, Week 1 종료 시 별도 freeze)

### 1.2 인프라 점검
- [ ] Shadow log stream 분리 생성 (`track2_shadow.log`, V3 운영 로그와 분리)
- [ ] Shadow 응답 미반환 (운영 트래픽 영향 0% 보장)
- [ ] Latency monitoring (track2 별도, V3 와 비교용)
- [ ] Fail-closed 동작 E2E 테스트 (NO_BASELINE / MODEL_ERROR / PARITY_BREACH 3가지)

### 1.3 의사결정 / 알림
- [ ] **담당자 단독 shadow 배치 승인** (spec §11.3 기준 — Phase B 5% canary 부터 운영 매니저 동반 승인)
- [ ] Slack alert 채널 설정 (가드레일 hit > 2% / fallback > 5% / latency p95 > V3×2)
- [ ] D+7 actual price linkage 거래 DB 조인 사전 검증

## 2. 일일 점검 (D+1 ~ D+7)

### 2.1 매일 09:00 자동 리포트 항목
| 항목 | 임계 | 위반 시 |
|---|---|---|
| Shadow 표본 누적 | 일 70+ (목표 500/주) | 카운트 급감 → 인프라 점검 |
| Schema 검증 통과율 | ≥ 99% | <99% → 입력 변수 spec 점검 |
| Fail-closed 발동 | 0건 (정상 작동만) | 발생 시 사유 분석 (NO_BASELINE / MODEL_ERROR / PARITY_BREACH) |
| Latency p95 ratio | ≤ V3 × 2.0 | >2.0 → 모델 서빙 코드 / 의존성 점검 |
| 가드레일 hit rate | ≤ 2% | >2% → 사유 코드별 분포 + 학습-운영 분포 비교 |

### 2.2 Pipeline Parity 검증 (코덱스 P1)
> "성능 차이"가 아닌 **"baseline 정체성 붕괴"** 가 핵심 트리거.

매일 sample 30건 임의 추출 후 다음 점검:
- [ ] Feature 값이 학습 시 spec 과 일치 (log_area / birth_year_centered / log_artist_total_works 단위 / 결측 처리)
- [ ] Artist slug 정규화 동일 (대소문자 / 공백 / 특수문자)
- [ ] 가드레일 사전/사후 차단 로직 동일 (low_price / ink / tier 3 등)
- [ ] 학습-서빙 parity 검증: 동일 입력 → 동일 출력 (max diff ≤ 1e-6)

### 2.3 로그 완전성
- [ ] 응답 필드 누락 0% (model_used / route_reason / guardrail_flags / calibration_applied / fallback_active)
- [ ] Shadow log 와 V3 운영 log 의 request_id 매칭률 100%
- [ ] D+7 actual price linkage 가능한 거래 비율 ≥ 80%

## 3. D+7 종료 시 합격 판정 (spec §11.1)

다음 7개 모두 PASS 시 → Phase B (5% canary) 진입 승인:

| 항목 | 합격 기준 | 결과 |
|---|---|---|
| Shadow 표본 누적 | ≥ 500건 (cold) | __ |
| 실제 거래가 linkage | D+7 actual 매칭 | __ |
| Track 2 vs V3 MdAPE 격차 | ≤ +5%p | __ |
| 가드레일 hit rate | ≤ 2% | __ |
| Latency p95 | ≤ V3 × 2.0 | __ |
| Schema 검증 통과율 | ≥ 99% | __ |
| Fail-closed 동작 | NO_BASELINE 시 V3 자동 라우팅 | __ |

→ 7/7 PASS: Phase B 5% canary 승인 (담당자 + 운영 매니저)
→ 1-2 항목 FAIL: 원인 분석 + 1주 추가 shadow 후 재판정
→ 3+ 항목 FAIL: shadow 폐기 + 재학습 / 모델 재검토

## 4. Stage 4 와의 인터페이스

### 4.1 Baseline 일치성 보장
- Stage 4 의 baseline = 본 shadow 와 동일 모델 hash (`track2_v1_20260507`)
- Shadow 에서 baseline 구현 불일치 발견 시:
  - **즉시**: shadow 일시 중단 + 원인 분석
  - **Stage 4 freeze 전**: baseline 정의 재고정 (가설 / 임계 변경 X)
  - 영향 받는 Stage 4 항목: §6.0 Pre-registered Analysis Plan 의 baseline 모델 정의

### 4.2 Stage 4 진행 영향 X
- shadow 결과의 성능 차이 (예: Track 2 MdAPE 25% 관측 vs Stage 3 100-seed 24.07%) 자체는 Stage 4 합격 기준에 영향 X
- Stage 4 = warm-only path 검증, shadow = cold default 검증 — 통계 가설 분리

## 5. 트러블슈팅 (자주 발생 가능 케이스)

### 5.1 Schema 검증 통과율 < 99%
- 운영 입력 분포 변화 (PSI > 0.10) 가능성 — `docs/트랙2_production_통합_spec_20260507.md` §4 참조
- artist_slug 정규화 차이 (학습 시점 vs 운영 시점)
- area_cm2 단위 (cm² vs m²) 혼용

### 5.2 Latency p95 > V3 × 2
- 모델 로딩 / 메모리 / 의존성 (spline 계산) 점검
- Cold start 영향 (배포 직후 5분 평균 제외)

### 5.3 가드레일 hit rate > 2%
- 운영 분포가 학습 분포와 크게 다름 (특히 medium / gallery_tier)
- 신규 작가 비중 급증
- → 가드레일 임계 재조정 검토 (spec §2.1)

### 5.4 Fail-closed 발동
- NO_BASELINE: parity 검증 실패 — 위 §2.2 Pipeline Parity 점검
- MODEL_ERROR: 모델 응답 실패 — 모델 서빙 인프라 점검
- PARITY_BREACH: 학습 시 사용 변수 spec 과 운영 입력 불일치

## 6. Rollback (필요 시)

### 6.1 Manual Rollback (즉시, 담당자 단독)

**정식 경로** (spec §15.1 canonical):
```bash
# Step 1. Track 2 즉시 차단
ops cli model.disable --name track2_v1 --reason "manual_rollback: <사유>"

# Step 2. 자동 V3 라우팅 확인 (1분 내)
ops cli traffic.verify --model v3 --pct 100 --segment cold

# Step 3. 운영팀 알림
ops cli notify --channel #ops-alert --msg "Track 2 manual rollback: <사유>"
```

**대안 경로** (ops cli 장애 시만 fallback):
```bash
# kubectl 직접
kubectl set env deployment/track2-shadow ENABLED=false
# 또는 runtime config flip
config set track2.shadow.enabled false
```

> 정식 경로 사용 시 자동 audit log + Slack 알림 포함. 대안 경로는 운영팀 수동 알림 필요.

### 6.2 Auto-fallback (자동)
- spec §3.1 자동 트리거 발동 시 → Track 2 응답 100% V3 라우팅
- 운영팀 Slack 알림 + 24h 내 원인 분석

## 7. 산출물 (Phase A 종료 시)

- [ ] Phase A 1주 결과 보고서 (7개 합격 기준 결과)
- [ ] Pipeline parity 30 sample 검증 결과
- [ ] Stage 4 baseline 일치성 확인서
- [ ] Phase B 진입 승인서 (담당자 + 운영 매니저 서명)

## 8. 참조

- 운영 spec: `docs/트랙2_production_통합_spec_20260507.md` §11.1 / §15 / §6
- 모델 결과: `docs/트랙2_최종보고서_20260506.md`
- Stage 4 plan: `docs/stage4_확장검증계획_20260507.md` (baseline 일치성)
- Quantile shadow: `docs/stage3_quantile_cycle_20260507.md` (별도 shadow, 본 cold rollout 과 분리)
