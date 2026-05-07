# 트랙 2 Production 통합 Spec

> **작성일**: 2026-05-07
> **대상**: 운영 / 인프라 담당자
> **연계**: `docs/트랙2_최종보고서_20260506.md`, `docs/트랙2_수식_프로세스_상세_20260506.html`
> **상태**: 코덱스 자문 반영 v3 (P1+P2+Nit 모두 반영, 18 섹션 — §17 = warm-only 후보 추가)
> **본 spec 의 기본 운영 플로우** = **cold rollout 단계 + 가드레일 + fallback**. §17 (Warm-only Track 2 path 후보) 는 **연구 부록 — Stage 4 후 재평가, 즉시 도입 X**.

## 0. 목표 / KPI (문서 상단 고정)

### 0.1 적용 범위 (현재 운영)
- **Warm 작가** (학습량 ≥ 10건): **V3 운영 모델 유지** (정확도 12-18%) — 본 spec §1-§16 은 모두 cold rollout 기준
- **Cold 작가** (학습량 < 10건): **트랙 2 도입** (F4 + log_area spline + Huber)
- **Warm-only Track 2 path (FE only)**: §17 부록 — 연구 후보, **운영 미승인 / Stage 4 후 재평가**

### 0.2 1차 Soft Launch
- 비율: **5% (cold 트래픽 한정)**
- 기간: 2주
- 확대 단계: 5% → 10% → 25% (KPI 충족 시)

### 0.3 승격 / 중단 KPI

| 지표 | Soft launch (2주) 게이트 | 정착 후 (4주+) 임계 | 작동 |
|---|---|---|---|
| Rolling MdAPE | 1주: ≤ 28% / 2주: ≤ 28% (확대) | 4주: > 30% (fallback) | 단계 확대 / V3 복귀 |
| P90 APE | 2주: ≤ 60% | > 70% | 단계 확대 / 자동 fallback |
| Guardrail hit rate | ≤ 2% (정상) | > 2% (alert) | 모니터링 |
| p95 latency | V3 baseline × 2 이내 | 동일 | 자동 fallback |
| Fallback rate | ≤ 5% | ≤ 5% | 모니터링 |

> 2주 soft launch 종료 시점에 1주/2주 rolling 으로 게이트 판정 (4주 rolling 은 정착 후 적용).

---

## 1. 라우팅 로직 (Warm vs Cold 판정)

### 1.1 라우팅 키 (학습 시점 동일 규칙으로 freeze)

```
def route(artwork) → "warm" | "cold":
    artist = artwork.artist_slug
    
    # 학습 데이터 작가 작품 수 조회
    n_train = train_artist_counts.get(artist, 0)
    
    # 입력 변수 충족 여부
    has_required = all([
        artwork.area_cm2 is not None and artwork.area_cm2 > 0,
        artwork.artist_birth_year is not None,
        artwork.artist_total_works is not None,
    ])
    
    # 라우팅 결정
    if not has_required:
        return ("v3", "missing_required_features")
    
    if n_train >= 10:
        return ("v3", "warm_artist")
    
    return ("track2", "cold_artist")
```

### 1.2 라우팅 결과 응답/로그

응답 필드에 반드시 포함:
- `model_used`: "v3" or "track2"
- `route_reason` (enum): 
  - `warm_artist` — 학습량 ≥ 10
  - `cold_artist` — 학습량 < 10 (Track 2 정상 라우팅)
  - `missing_required_features` — 필수 변수 결측 (V3 fallback)
  - `guardrail_fallback` — 가드레일 트리거 (V3 fallback, §2)
  - `fallback_active` — auto-fallback 발동 중 (§3)
  - `NO_BASELINE` — Track 2 학습-서빙 parity 검증 실패 (V3 fallback, §11.2)
  - `MODEL_ERROR` — Track 2 응답 실패 / 의존성 장애 (V3 fallback)
  - `PARITY_BREACH` — 학습 시 사용한 변수 spec 과 운영 입력 불일치

### 1.3 Warm/Cold 임계 freeze
- **현재 임계: `n_train ≥ 10`** (= `WARM_ROUTING_MIN_WORKS`)
- 운영 중 5/10/15 sensitivity 함께 추적 (대시보드)
- 임계 변경은 별도 의사결정 + 학습 데이터 재산출
- **warm path (Track 2 FE only) 진입은 별도 임계** `WARM_PATH_MIN_DEPTH ≥ 15` 적용 — §17 참조 (현재 미활성)

---

## 2. 가드레일 자동 트리거 (V3 fallback)

### 2.1 트리거 조건 (실시간 차단 + V3 fallback)

| 조건 | 임계 | 사유 코드 |
|---|---|---|
| 예측가 < 5,000,000 KRW | 저가 구간 | `guardrail_low_price` |
| medium == "ink" | 학습/평가에서 OLS 대비 -0.94%p 악화 segment | `guardrail_medium_ink` |
| gallery_tier == 3 | 일반 등급 변동 큼 | `guardrail_tier_3` |
| log_area < P5 (학습 분포) or > P95 | 극단 면적 | `guardrail_extreme_size` |
| birth_year < 1900 or > 2026 | 비정상 출생년 | `guardrail_invalid_birth` |
| total_works > P99 (학습) | 극단 작품수 | `guardrail_extreme_works` |
| Feature missing | 필수 변수 결측 | `guardrail_missing_feature` |

### 2.2 가드레일 적용 로직

```
def apply_guardrails(artwork, prediction) → (action, reason):
    # 1. 사전 차단 (예측 전)
    for rule in pre_check_rules:
        if rule.matches(artwork):
            return ("v3_fallback", rule.reason_code)
    
    # 2. 사후 차단 (예측 후)
    if prediction.value < 5_000_000:
        return ("v3_fallback", "guardrail_low_price")
    
    return ("track2_continue", None)
```

### 2.3 가드레일 통계 (대시보드)
- Hit rate (전체 cold 트래픽 대비 가드레일 발동 비율)
- 사유 코드별 분포
- 일/주 단위 추이

---

## 3. Fallback (V3 자동 복귀) Spec

### 3.1 Soft Launch 중 자동 fallback 트리거

**Window 이중 구조**: 1h (단기) / 24h (중기)

| 조건 | 임계 | Window | 작동 |
|---|---|---|---|
| Track 2 MdAPE − V3 MdAPE | ≥ +5%p | 24h, n ≥ 200 | 100% V3 복귀 |
| High-APE rate (APE > 50%) 차이 | ≥ +3%p | 24h | 100% V3 복귀 |
| Guardrail hit rate | > 2% | 1h | alert + 검토 |
| Latency p95 ratio (트랙 2 / V3) | > 2.0× | 1h | 100% V3 복귀 |
| Fallback rate (자동) | > 50% | 1h | alert + 검토 |

### 3.2 자동 fallback 알고리즘

```
def auto_fallback_check():
    for window in [1h, 24h]:
        metrics_track2 = compute_kpi(window, model="track2")
        metrics_v3 = compute_kpi(window, model="v3")
        
        if metrics_track2.n < 200 and window == 24h:
            continue  # 표본 부족
        
        # MdAPE 비교
        if metrics_track2.mdape - metrics_v3.mdape >= 0.05:
            trigger_fallback(reason="mdape_degradation")
            return
        
        # P90 APE
        if metrics_track2.high_ape_rate - metrics_v3.high_ape_rate >= 0.03:
            trigger_fallback(reason="high_ape_increase")
            return
        
        # Latency
        if metrics_track2.latency_p95 / metrics_v3.latency_p95 > 2.0:
            trigger_fallback(reason="latency_degradation")
            return
```

### 3.3 Fallback 발동 시 동작
1. 자동 100% V3 복귀
2. 운영팀 알림 (Slack + email)
3. 24h 내 원인 분석 + 보고
4. 수동 재개는 별도 승인자 (담당자 + 1명)

---

## 4. Drift Monitoring Spec

### 4.1 PSI (Population Stability Index) 일 단위 계산

```
def compute_psi(reference_dist, current_dist):
    """
    reference: 학습 데이터 분포 (10 quantile bin)
    current: 최근 1d 운영 데이터 분포
    """
    psi = 0
    for bin in bins:
        ref_pct = reference_dist[bin]
        cur_pct = current_dist[bin]
        if cur_pct == 0 or ref_pct == 0:
            continue
        psi += (cur_pct - ref_pct) * log(cur_pct / ref_pct)
    return psi
```

### 4.2 PSI 알람 임계

| PSI 값 | 의미 | 작동 |
|---|---|---|
| < 0.10 | 안정 | 정상 |
| 0.10 ~ 0.25 | 경고 | 알람 + 모니터링 강화 |
| > 0.25 | 심각 | 재학습 검토 |

### 4.3 핵심 변수별 분리 계산
- `log_area` PSI
- `birth_year_centered` PSI  
- `log_artist_total_works` PSI
- `price_band` (예측가 quantile) PSI
- `medium_category` 분포 변화

### 4.4 재학습 자동 trigger 조건

다음 중 하나 충족 시:
1. 핵심 변수 PSI > 0.25 (심각) 1일
2. 핵심 변수 PSI > 0.10 (경고) 3일 연속
3. 4주 rolling MdAPE 가 baseline (24.07%) 대비 +3%p 악화
4. 월 1회 정기 재학습 (default)

### 4.5 재학습 pipeline
- Trigger → 새 데이터 cleansing → 모델 재학습 → 검증 (LAO 30-seed) → A/B 비교 → 승인 → 배포

---

## 5. API 인터페이스 Spec

### 5.1 요청 (Request) 스키마

```json
{
  "request_id": "uuid",
  "artwork": {
    "artist_slug": "string",
    "area_cm2": "float (> 0)",
    "artist_birth_year": "int (1900-2026)",
    "artist_total_works": "int (>= 0)",
    "medium_category": "string (oil/acrylic/ink/...) — guardrail 용",
    "gallery_tier": "int (1-4) — guardrail 용"
  },
  "options": {
    "model_version": "string (optional, default: latest)",
    "force_model": "string (optional, debug 용: v3 / track2)",
    "include_band": "bool (optional)"
  }
}
```

### 5.2 응답 (Response) 스키마

```json
{
  "request_id": "uuid",
  "timestamp": "ISO8601",
  "prediction": {
    "value": "int (KRW)",
    "log_value": "float",
    "band_low": "int (optional, ±20%)",
    "band_high": "int (optional)"
  },
  "model_used": "string (v3 / track2)",
  "model_version": "string",
  "route_reason": "string",
  "guardrail_flags": ["string"],
  "calibration_applied": "bool",
  "fallback_active": "bool"
}
```

### 5.3 응답 예시

```json
{
  "request_id": "abc-123",
  "timestamp": "2026-05-27T14:32:00Z",
  "prediction": {
    "value": 8500000,
    "log_value": 15.95,
    "band_low": 6800000,
    "band_high": 10200000
  },
  "model_used": "track2",
  "model_version": "track2_v1_20260507",
  "route_reason": "cold_artist",
  "guardrail_flags": [],
  "calibration_applied": true,
  "fallback_active": false
}
```

---

## 6. 운영 안전 보장

### 6.1 Rollback Runbook

**Manual rollback (one-click)**
```bash
# Track 2 즉시 100% 차단
$ ops cli model.disable --name track2_v1
# → 모든 cold 트래픽도 V3 로
```

**Automatic rollback**: 위 §3 자동 fallback trigger

### 6.2 모델 / Feature Version Pinning
- Track 2 모델 = `track2_v1_20260507` (학습 데이터 / 코드 / 하이퍼파라미터 모두 hash 고정)
- Feature pipeline 도 동일 버전 (학습-서빙 parity)

### 6.3 Shadow Log 보관
- 최소 90일 (예측 / 입력 / route_reason / guardrail / 실제 거래가)
- 운영 사후 분석 / 재학습용

### 6.4 승인자
- Launch (5% → 10%): 담당자 + 1명
- Fallback 발동 (자동): 알림 + 24h 내 보고
- Manual rollback: 담당자 단독 가능
- 재배포 (rollback 후): 담당자 + 1명 승인

---

## 7. Production 인프라 요구사항

### 7.1 필수 인프라

| 항목 | 요구사항 |
|---|---|
| 실시간 feature 검증 | 입력 schema check — 결측 시 거부 X / **V3 fallback 으로 라우팅** (라우팅 §1 과 일치) |
| Deterministic routing | 같은 입력 → 같은 라우팅 결과 (재현성) |
| Model registry | 버전 관리 + rollback 즉시 |
| Canary config | 트래픽 비율 동적 변경 (5% → 10% → 25%) |
| Audit log | 모든 prediction 결정 기록 (감사용) |
| Latency monitoring | p50/p95/p99 추적 |

### 7.2 권장 stack
- 모델 서빙: Python (sklearn HuberRegressor + numpy)
- 라우팅: Feature flag + traffic split (예: LaunchDarkly / 자체)
- 모니터링: Prometheus + Grafana
- 알람: Slack + Email + PagerDuty

### 7.3 인프라 부담 평가

| 항목 | V3 | 트랙 2 추가 |
|---|---|---|
| 모델 크기 | ~50MB (GBM) | < 1KB (5개 계수) |
| 예측 latency | ~50ms | ~5ms (단순 곱셈) |
| 메모리 | ~200MB | < 10MB |
| CPU | 중간 | 매우 낮음 |

→ **트랙 2 추가 부담 거의 없음**.

---

## 8. 학습-서빙 Parity 체크리스트 (부록)

```
[ ] 변수 변환 코드가 학습/서빙에서 동일 (log / centering / spline knots)
[ ] log_area knots = 학습 데이터의 [10, 50, 90] percentile (고정)
[ ] birth_year_centered 의 BIRTH_MEAN = 학습 데이터 평균 (고정)
[ ] Huber regressor coefficients = 학습 결과 그대로 import
[ ] Calibration table = 학습 결과 그대로 import
[ ] 라우팅 룰 (n_train ≥ 10) = 학습 시 사용한 작가 카운트 기준
[ ] 가드레일 임계 (저가 < 5M, P5/P95) = 학습 데이터 기준
[ ] PSI reference = 학습 데이터 분포
```

---

## 9. 다음 액션 (개발 → 도입)

| 단계 | 담당 | 기간 |
|---|---|---|
| Spec 검토 + 승인 | 개발 + 운영 + 의사결정자 | 1-2일 |
| 라우팅 + 가드레일 + fallback 코드 구현 | 개발 | 3-5일 |
| 학습-서빙 parity 검증 | QA | 1-2일 |
| Shadow 환경 배치 (0% 트래픽) | 운영 | 2-3일 |
| 5% Soft launch 시작 | 운영 + 의사결정자 승인 | 즉시 |
| KPI 모니터링 (2주) | 운영 | 2주 |
| 단계 확대 (5% → 10% → 25%) | 운영 + 승인 | 점진 (위 §0.2 확대 단계와 일치) |

---

## 10. 잔존 위험 + 대응

| 위험 | 대응 |
|---|---|
| 표본 차이 (학습 1.3K vs 운영 28K) | Shadow 운영으로 사전 검증 + 자동 fallback |
| Cold artist 신규 case 분포 변화 | Drift monitoring + 월 재학습 |
| Calibration table 시간 drift | 월 1회 재학습 자동화 |
| 신규 입력 채널 (gallery_direct 등) | 채널별 100건 누적 후 활성화 (shadow) |
| 가드레일 hit 폭증 | Alert + 운영팀 검토 + 임계 조정 |

---

## 11. Shadow / Soft-launch 승인서 + 체크리스트

### 11.1 0% Shadow 합격 기준 (Phase A)

운영 트래픽 영향 없이 1주 shadow 운영 후 다음 모두 충족 시 5% canary 진입 승인:

| 항목 | 합격 기준 | 측정 방법 |
|---|---|---|
| Shadow 표본 누적 | 최소 500건 (cold) | 일별 누적 카운트 |
| 실제 거래가 linkage | D+7 거래 actual price 매칭 | 거래 DB 조인 |
| Track 2 vs V3 MdAPE 격차 | ≤ +5%p (V3 baseline 대비) | 동일 기간 동일 작품 |
| 가드레일 hit rate | ≤ 2% | log 집계 |
| Latency p95 | ≤ V3 × 2.0 | APM |
| Schema 검증 통과율 | ≥ 99% | API log |
| Fail-closed 동작 | NO_BASELINE 시 V3 자동 라우팅 | E2E 테스트 |

→ 위 7개 모두 PASS 시 Phase B (5% canary) 승인.

### 11.2 Fail-closed 절차

Track 2 모델 응답 실패 / 학습-서빙 parity 파괴 / 의존성 장애 시:
- 자동 V3 라우팅 (트랙 2 응답 X)
- 사유 코드: `NO_BASELINE` / `MODEL_ERROR` / `PARITY_BREACH`
- 운영팀 알림 (즉시) + 자동 fallback rate KPI 기록

### 11.3 단계별 승인권자

| 단계 | 승인 필요 |
|---|---|
| Shadow 배치 | 담당자 단독 |
| Phase B (5% canary) | 담당자 + 운영 매니저 |
| Phase C (10%/25% 확대) | 담당자 + 운영 매니저 + 의사결정자 |
| Manual rollback | 담당자 단독 가능 |
| Fallback 후 재개 | 담당자 + 운영 매니저 (24h 보고 후) |

### 11.4 D+7 Actual Linkage

운영 후 7일이 지나야 실제 거래가 확정 → 그 전까지는 KPI 관측치 부족 → **확대 금지**.
Phase B 5% 운영 시작 후 최소 D+14 (5% × 7일 누적) 까지는 확대 X.

---

## 12. Segment / Channel KPI 부록

### 12.1 Segment 별 alert threshold (자동 / 수동 조치 분리)

| Segment | n 최소 | MdAPE 임계 | P90 APE 임계 | 작동 |
|---|---|---|---|---|
| 전체 cold | 200 | > 30% | > 70% | **자동 fallback** |
| 저가 (예측가 < 5M) | 100 | > 35% | > 80% | **자동 사람 검토 라우팅** |
| medium = ink | 50 | > 33% | > 75% | **수동 alert** (운영팀 검토) |
| gallery_tier = 3 | 100 | > 28% | > 70% | **수동 alert** |
| 극단 면적 (P5 미만 / P95 초과) | 30 | — | — | **자동 V3 fallback** (가드레일) |

### 12.2 Channel 별 정책 (입력 출처)

| Channel | 활성화 조건 | 결측 정책 | 별도 KPI 추적 |
|---|---|---|---|
| Artsy crawl (학습 동일) | default ON | V3 fallback (필수 변수 결측 시) | 기본 모니터링 |
| Saatchi crawl | default ON | year_made 결측 → V3 fallback | year_made fill rate |
| **gallery_direct (신규)** | **default OFF** → shadow 100건 + MdAPE diff < +5%p 후 활성화 | V3 fallback | **채널별 MdAPE / fallback rate 별도** |
| **collector_input (신규)** | **default OFF** → 동일 조건 | V3 fallback | 동일 |
| 기타 (external) | default OFF | V3 fallback | 동일 |

### 12.3 신규 채널 활성화 단계

1. Channel 별 shadow 라우팅 enabled (트래픽 0%)
2. 100건 누적 + 7일 actual linkage 대기
3. 채널별 MdAPE 가 전체 대비 +5%p 이내 → activated
4. 활성화 후에도 채널별 KPI 별도 모니터링 지속

---

## 13. 학습-운영 표본 차이 Bridge Memo

### 13.1 표본 차이 명시

| 측면 | 학습 (Stage 3) | 운영 (production) |
|---|---|---|
| 규모 | 1,378 records / 100 artists | 28,376 records (전체 풀) |
| 출처 | Artsy curated only | Artsy + Saatchi + 신규 채널 |
| Cleansing | 엄격 (필수 변수 / 작가당 ≥10) | 다양 (결측 케이스 포함) |
| 평가 protocol | LAO 30/100-seed | 운영 4주 rolling |

### 13.2 Bridge — 운영 데이터에서의 정확도 추정 위험

학습 LAO MdAPE 24.07% → 운영 환경에서는:
- 표본 분포 차이로 ± 3-5%p 이동 가능 (낙관/비관)
- D+7 actual linkage 후 운영 실측치 확보까지 정확도 단정 X

### 13.3 Bridge 위험 완화

1. **Phase A shadow 1주** → 운영 표본 500건 + actual linkage 후 KPI 1차 검증
2. **5% canary 2주** → 추가 운영 데이터 확보
3. **단계 확대 전 KPI 충족 확인 필수**
4. 학습 데이터 분포와 운영 분포 PSI 추적 (§4 와 동일)

### 13.4 의사결정 시 caveat 승계

본 운영 도입 결정 시 다음을 의사결정자에게 명시:
- "학습 LAO MdAPE 24.07% 는 cleansed 1.3K 표본 기준. 운영 28K 분포에서 같은 정확도 보장 X."
- "Shadow + canary 단계로 운영 실측 확보 후 정착 정확도 판단."
- "단계 확대는 KPI gate 충족이 필수 조건."

---

## 14. Warm/Cold 임계 Sensitivity 부록 (5 / 10 / 15)

### 14.1 추적 항목 (대시보드)

3개 임계로 각각 별도 KPI 산출:

| 임계 (n_train) | warm % | cold % | warm MdAPE | cold MdAPE | 통합 MdAPE |
|---|---|---|---|---|---|
| ≥ 5 | (운영 측정) | — | — | — | — |
| **≥ 10** (현재 기본) | (운영 측정) | — | — | — | — |
| ≥ 15 | (운영 측정) | — | — | — | — |

### 14.2 임계 변경 승인 규칙

다음 모두 충족 시에만 임계 변경 검토:

1. 4주 이상 운영 데이터에서 다른 임계 (5 또는 15) 가 통합 MdAPE 기준 -1.5%p 이상 우수
2. 다른 임계의 warm/cold 비율이 운영 가능 범위 (warm 20-80% 사이)
3. 가드레일 hit rate 변화 ≤ 1%p
4. 의사결정자 + 담당자 + 운영 매니저 3자 승인

### 14.3 변경 절차

1. 1개월 운영 데이터 + 3개 임계 KPI 비교
2. 비교 메모 작성 + 권고
3. 의사결정 회의 + 3자 승인
4. Shadow 1주 검증 (새 임계로) → 변경 적용

---

## 15. 운영 Runbook (Rollback / Alert 대응)

### 15.1 Manual Rollback 절차

```bash
# Step 1. Track 2 즉시 차단
$ ops cli model.disable --name track2_v1 --reason "manual_rollback: <reason>"

# Step 2. 자동 V3 라우팅 확인 (1분 내)
$ ops cli traffic.verify --model v3 --pct 100 --segment cold

# Step 3. 운영팀 알림
$ ops cli notify --channel #ops-alert --msg "Track 2 manual rollback: <reason>"

# Step 4. 24h 내 보고서 작성
$ ops cli report.create --type rollback --model track2_v1
```

### 15.2 Auto-fallback 발동 시 대응 절차

1. **즉시 (≤ 5분)**: Slack alert 수신 + 트래픽 자동 100% V3 복귀 확인
2. **1h 내**: 발동 사유 분석 (KPI 로그 + 운영 metric)
3. **4h 내**: 1차 보고 (담당자 → 운영 매니저)
4. **24h 내**: 원인 분석 보고서 + 재개 가능 여부 판단
5. **재개 결정**: 담당자 + 운영 매니저 승인 → Phase A shadow 부터 재진입

### 15.3 Alert 대응 매트릭스

| Alert | 자동 조치 | 수동 조치 |
|---|---|---|
| Auto-fallback 발동 | V3 100% 복귀 | 24h 분석 보고 |
| Guardrail hit > 2% | 알람 | 운영팀 검토 (segment 분포 확인) |
| PSI > 0.10 (3일 연속) | 알람 | 재학습 검토 |
| PSI > 0.25 | 즉시 알람 | 긴급 재학습 트리거 |
| Latency p95 > V3 × 2 | 자동 fallback | 인프라 점검 |
| Schema 검증 통과율 < 99% | 알람 | 입력 채널 점검 |
| Channel 별 MdAPE > +5%p | 알람 | 채널 검토 / 필요 시 차단 |

### 15.4 Runbook 위치

본 spec 의 §15 + 별도 운영 wiki 링크 (운영팀 공유).

---

## 16. KPI 용어 통일 부록

| 용어 | 정의 | 단위 |
|---|---|---|
| **MdAPE** | Median Absolute Percentage Error (예측가 vs 실제가, 중앙값) | % |
| **High-APE rate** | APE > 50% 인 케이스 비율 | % |
| **P90 APE** | APE 의 90th percentile | % |
| **Fallback rate** | 자동/수동 fallback 발동된 cold 트래픽 비율 | % |
| **Guardrail hit rate** | 가드레일 트리거된 cold 트래픽 비율 | % |
| **PSI** | Population Stability Index (학습/운영 분포 차이) | 무차원 |
| **Latency p95** | 응답 시간 95 percentile | ms |
| **warm_mdape** *(scope: warm path, §17)* | warm path 트래픽 한정 MdAPE | % |
| **warm_low_price_mdape** *(scope: warm path, §17)* | warm path + 예측가 < 5M KRW MdAPE | % |
| **warm_artist_win_rate** *(scope: warm path, §17)* | artist 단위 warm V3 baseline 대비 개선 비율 | % |
| **warm_fallback_rate** *(scope: warm path, §17)* | warm path 트래픽 V3 fallback 발동 비율 | % |

본 spec 의 모든 임계 / KPI 는 위 정의 기준. **scope 라벨이 없는 KPI = cold rollout default (§1-§16) / scope: warm path = §17 (warm-only Track 2 후보) 한정**.

---

## 17. Warm-only Track 2 path 후보 (Stage 4 까지 보류)

> **상태**: 연구 후보 (Stage 3 P3 + feature 재탐색 + robustness 종결) / **운영 도입 보류** — §1-§16 의 cold rollout 과 분리 운용  
> **근거**: `experiments/structural_v1/results/stage3_warm_p3_validation.json` + `stage3_warm_feature_exploration.json` + `stage3_warm_fe_robustness.json` (3 차)  
> **승격 결정**: Stage 4 artist-cluster 증거 (`docs/stage4_데이터수집계획_20260507.md` §6.1) 확보 후 재평가  
> **본 §17 의 KPI / 게이트는 warm path 전용 scope override** — §16 (cold-default KPI glossary) 와 별도 운용

### 17.1 후보 모델
- **FE only (Stage 4 champion)**: F4 + log_area spline + Huber + Artist Fixed Effects (warm 작가 dummy)
- 비채택: Combined (FE + time weight + history avg) — cutoff 2024 효과 약화 + 저가 segment +3.36%p 악화
- 비채택: Combined-shrunk (EB) — σ_b² > σ_w² 로 shrinkage 효과 미미 (Combined 와 거의 동일)
- 비채택: + gallery_tier dummy / + log_area×log_works interaction / + 결합 — feature 재탐색 결과 cutoff 2023/2024 baseline 보다 악화 또는 동등, **증분 가치 없음**
- Huber `eps` = **1.35 유지** (warm 전용 튜닝 결과 1.35 vs 1.5 차이 -0.14%p 수준 noise — 운영값 고정)

### 17.2 P3 검증 핵심 결과 (≤2023 train, ≥10 작품 warm 기준)

| cutoff | n_test | baseline | FE only | Δ (vs baseline) |
|---|---|---|---|---|
| 2022 | 19 | 17.50% | 10.24% | -7.26%p |
| 2023 | 44 | 23.15% | 19.18% | -3.97%p |
| 2024 | 62 | 26.13% | 21.90% | -4.23%p |

> **cutoff 2022 caveat**: n_test_artists=5 의 exploratory signal — 채택 결정의 주 근거는 아님. 주 근거는 cutoff 2023/2024 + robustness 30 실험 (3 cutoff × 10 seed 모두 음수 방향).

- Cluster bootstrap: FE only vs baseline mean **-2.68%p**, 95% CI [-14.33, +8.54], P(<0)=72%
- 3 cutoff 모두 동일 방향 개선 (강건성 확인)
- CI 0 포함 (n=44, 13 artist 한계) — Stage 4 표본 확장 후 재검증 필요
- Leakage 점검 0건 (artist history 변수의 train cutoff 분리 정상)

### 17.3 운영 정책 (도입 시 적용 예정)

#### 17.3.1 라우팅 (§1 확장)

> **분리 변수 (코덱스 P1)**: warm 라우팅 임계와 warm-path 진입 임계를 별도 정의해 분기 의도를 명확히 한다.
> - `WARM_ROUTING_MIN_WORKS = 10` — §1 의 warm/cold 라우팅 임계 (변경 X, 기존과 동일)
> - `WARM_PATH_MIN_DEPTH = 15` — warm-path (Track 2 FE only) 진입 추가 임계 (10 ≤ n_train < 15 인 얕은 warm 은 V3 유지)

```
def route_v2(artwork) → (model, reason):
    # 기존 §1 라우팅 통과 후 warm 판정 시
    base = route(artwork)
    if base != ("v3", "warm_artist"):
        return base  # cold / fallback 등 그대로

    n_train = train_artist_counts.get(artwork.artist_slug, 0)
    if n_train < WARM_PATH_MIN_DEPTH:
        return ("v3", "warm_shallow_fallback")  # 얕은 warm 은 V3
    if WARM_TRACK2_ENABLED:
        return ("track2_warm_fe", "warm_fe_path")
    return base  # warm path 비활성 시 V3
```

- **WARM_ROUTING_MIN_WORKS**: 10 (§1 임계, 변경 X)
- **WARM_PATH_MIN_DEPTH**: 초기 15 (Stage 4 결과로 10 / 15 / 20 sensitivity 평가)
- **WARM_TRACK2_ENABLED**: 기본 `False`. Shadow / Canary 단계에서만 `True`
- **모델 / 버전 분리**: cold Track 2 (`track2`) 와 warm FE (`track2_warm_fe`) 는 **독립 model_id / version pin / shadow log 로 배포** (§6.2 의 model registry 에서 별도 entry)

#### 17.3.2 도입 단계 (Shadow → Small Canary → Gated Rollout)

> **W-S 진입 prerequisite (코덱스 P2)**: `docs/stage4_데이터수집계획_20260507.md` §6.1 (오프라인 합격 기준 — cluster bootstrap CI 상한 ≤ 0 또는 P(diff<0) ≥ 95%) 통과 후에만 W-S 진입.

| 단계 | 트래픽 | 비교 | 승격 조건 |
|---|---|---|---|
| **W-S** Shadow | 0% (병렬 예측 로깅) | warm V3 vs warm FE only 동일 입력 | **warm-only MdAPE diff ≤ 0%p (비열위)**, 1주 안정 |
| **W-C1** Small Canary | warm 트래픽 5% | online A/B | win rate ≥ 55%, 저가 악화 +1%p 이내, fallback rate ≤ 5%, 2주 |
| **W-C2** Canary | warm 트래픽 25% | online A/B | warm MdAPE 악화 없음, P90 APE 악화 +3%p 이내, 2주 |
| **W-F** Full warm rollout | warm 트래픽 100% | — | W-C2 통과 + 의사결정 회의 |

#### 17.3.3 Warm path 전용 Metric Gate

> **Scope override**: 본 메트릭들은 warm path (`track2_warm_fe`) 트래픽 한정 KPI 다. §16 KPI glossary 의 `MdAPE`, `Fallback rate` 등은 cold rollout default — warm path 는 본 §17 정의를 우선 적용한다 (§16 표에도 warm-scoped 항목 추가).

| 메트릭 | 정의 | 단위 | 알람 |
|---|---|---|---|
| `warm_mdape` | warm path 트래픽 MdAPE | % | warm V3 baseline 대비 악화 시 즉시 |
| `warm_high_ape` | warm path 트래픽 APE > 50% 비율 | % | +5%p 악화 시 |
| `warm_p90_ape` | warm path 트래픽 P90 APE | % | +3%p 악화 시 |
| `warm_low_price_mdape` | warm path + 예측가 < 5M KRW MdAPE | % | +1%p 악화 시 즉시 |
| `warm_artist_win_rate` | artist 단위 warm V3 baseline 대비 개선 비율 | % | < 50% 시 |
| `warm_fallback_rate` | warm path 트래픽 V3 fallback 발동 비율 | % | > 5% 시 |
| `warm_depth_distribution` | warm path 작가 history depth 분포 | hist | shift 시 검토 |

#### 17.3.4 자동 차단 / Kill Switch (Warm path 즉시 fallback)
- `warm_low_price_mdape` 1시간 +1%p 악화 → warm path 즉시 V3 fallback (`WARM_TRACK2_ENABLED=False`)
- `warm_artist_win_rate` 1일 < 50% → warm path 비활성
- 신규 warm 진입 작가 (Stage 3/4 학습에 없던 작가) 비율 1주 > 30% → 자동 비활성 + review
- **수동 kill switch**: 운영 매니저가 `WARM_TRACK2_ENABLED` 플래그 즉시 toggle 가능 (배포 X, runtime config flip)
- **모델 버전 분리**: cold Track 2 와 warm FE 는 독립 batch 로 평가 / 배포 — 한쪽 fallback 이 다른 쪽에 영향 X
- **Shadow log 분리**: warm path shadow log 는 `track2_warm_shadow.log` 별도 stream (cold 와 분리)

### 17.4 Stage 3 한계 (도입 보류 사유)
- Cluster bootstrap CI 0 포함 (n=44 / 13 artist)
- Depth bin 분해 불가 (모든 warm test 가 10-14 depth 에 집중, 15+ depth test 0건)
- 저가 segment 단일 cutoff 분석 (Combined 에서 +3.36%p 악화 — FE only 는 미검증)
- 2024 cutoff 신규 warm 작가 36명 추가 → composition shift 영향 큼

### 17.5 Stage 4 데이터 수집 의존
- `docs/stage4_데이터수집계획_20260507.md` 참조
- 핵심 목표: **warm artist cluster 21 → 40+** (≤2023 split 기준 / row 수 아님), 평가 가능 warm artists **13 → 25+**, warm test rows **44 → 120+**
- 부수 목표: depth bin (10-14 / 15-24 / 25+) 균형
- 재검증 합격 시 본 §17 의 W-S 단계부터 시작

---

## 18. 참조 문서

- 모델 결과: `docs/트랙2_최종보고서_20260506.md`
- 수식 / 알고리즘: `docs/트랙2_수식_프로세스_상세_20260506.html`
- 일반 설명: `docs/트랙2_쉬운설명_20260506.html`
- 비전공자 풀이: `docs/트랙2_프로세스_쉬운버전_20260506.html`
- 임원 1페이지: `docs/임원보고_트랙2_요약_20260506.html`
- 데이터 plan: `docs/데이터클렌징_단계계획_20260506.md`
- Stage 4 plan: `docs/stage4_데이터수집계획_20260507.md`
- 실험 코드: `experiments/structural_v1/stage*.py`
- Warm P2/P3 결과: `experiments/structural_v1/results/stage3_warm_{,p3_}validation.json`
