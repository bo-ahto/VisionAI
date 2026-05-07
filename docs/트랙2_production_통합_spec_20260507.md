# 트랙 2 Production 통합 Spec

> **작성일**: 2026-05-07
> **대상**: 운영 / 인프라 담당자
> **연계**: `docs/트랙2_최종보고서_20260506.md`, `docs/트랙2_수식_프로세스_상세_20260506.html`
> **상태**: 코덱스 자문 반영 v1

## 0. 목표 / KPI (문서 상단 고정)

### 0.1 적용 범위
- **Warm 작가** (학습량 ≥ 10건): **V3 운영 모델 유지** (정확도 12-18%)
- **Cold 작가** (학습량 < 10건): **트랙 2 도입** (F4 + log_area spline + Huber)

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
- `route_reason`: "warm_artist" / "cold_artist" / "missing_required_features" / "guardrail_fallback" / "fallback_active"

### 1.3 Warm/Cold 임계 freeze
- **현재 임계: `n_train ≥ 10`**
- 운영 중 5/10/15 sensitivity 함께 추적 (대시보드)
- 임계 변경은 별도 의사결정 + 학습 데이터 재산출

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

## 11. 참조 문서

- 모델 결과: `docs/트랙2_최종보고서_20260506.md`
- 수식 / 알고리즘: `docs/트랙2_수식_프로세스_상세_20260506.html`
- 일반 설명: `docs/트랙2_쉬운설명_20260506.html`
- 비전공자 풀이: `docs/트랙2_프로세스_쉬운버전_20260506.html`
- 임원 1페이지: `docs/임원보고_트랙2_요약_20260506.html`
- 데이터 plan: `docs/데이터클렌징_단계계획_20260506.md`
- 실험 코드: `experiments/structural_v1/stage*.py`
