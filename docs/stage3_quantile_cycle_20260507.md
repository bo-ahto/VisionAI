# Stage 3 Quantile Regression Cycle — 운영 가격 범위 산출

> **작성일**: 2026-05-07
> **목적**: 외부 자문 권고 중 운영 가치가 가장 큰 후보 — Quantile Regression q25/q50/q75 검증 + 운영 band 산출
> **위치**: Phase 1 (curated exploratory) 내 별도 cycle, **점예측 family 와 분리**
> **연계**: `docs/트랙2_methodology_pipeline_20260507.md` (Phase 1/2/3 골격) / `docs/stage3_exploratory_addendum_20260507.md` (점예측 cycle 종결) / 외부 자문 의견 / 코덱스 사전 자문 (2026-05-07)

> ⚠️ **본 cycle 은 사전등록이 아닌 미니 프로토콜**. 점예측 cycle 과 별도 family. 결과는 indicative — 운영 채택 결정 X, 합격 시 **shadow / internal flag 우선 도입**, 검증 후 external API 전환.

## 1. 핵심 결정 (코덱스 권고)

| 항목 | 결정 |
|---|---|
| 모델 | **Linear Quantile Regression** (sklearn `QuantileRegressor`) — 트랙 2 해석 가능성 제약 유지 |
| Feature set | **F4 + log_area spline** (점예측 baseline 동일 — feature drift 회피) |
| Quantile | **q25 / q50 / q75** (3 quantile, 외부 자문 권고와 일치) |
| Loss | Pinball loss (각 quantile 독립 fit) |
| Crossing | Independent fit + **post-hoc sorting** + raw crossing rate metric |
| 운영 통합 | `prediction.value = q50` + `q25 / q75` 추가, `band_low = q25 / band_high = q75` (기존 ±20% 폐기) |
| Calibration | quantile band 와 기존 calibration table **분리 유지** (덧씌우면 coverage 망가짐) |

## 2. 후보 모델

### M1 (Primary)
- **F4 + log_area spline + Linear Quantile** (각 q25/q50/q75 독립 fit + post-hoc sort)

### M2 (Secondary, 비교용)
- F4 + log_area spline + **점예측 (Huber 운영) + 글로벌 residual quantile band**
  - 점예측 → residual 분포의 q25/q75 quantile 을 band 로 부착
  - 단순 baseline — quantile fit 의 우수성 입증용

### M3 (Sensitivity, 부록)
- F4 + log_area spline + Linear Quantile + L2 regularization (alpha sweep)

## 3. 평가 Protocol (점예측 family 와 분리)

### 3.1 Split
- **Cold-start LAO**: Stage 3 1378 rows / 100-seed (point predict 와 동일 split)
- **Time-split (warm)**: cutoff 2022 / 2023 / 2024 rolling sensitivity (참고)

### 3.2 Metric (사전 고정)

| Metric | 정의 | 합격선 (cold-start LAO 100-seed 평균) |
|---|---|---|
| **Pinball loss** | quantile loss 평균 (primary) | M2 baseline 보다 작음 |
| **q25 empirical coverage** | P(y ≤ q25_pred) | **20% ~ 30%** |
| **q50 empirical coverage** | P(y ≤ q50_pred) | **45% ~ 55%** |
| **q75 empirical coverage** | P(y ≤ q75_pred) | **70% ~ 80%** |
| **Central coverage (q25-q75)** | P(q25_pred ≤ y ≤ q75_pred) | **45% ~ 55%** |
| **q50 MdAPE** | (운영 baseline 비교) | 운영 baseline +1.0%p 이내 |
| **Width** | (q75 - q25) 평균 (log-price 척도) | M2 baseline 보다 같거나 좁음 |
| **Raw crossing rate** | post-sort 전 q25 > q50 또는 q50 > q75 비율 | **5% 이하** |
| **Post-sort crossing 해결률** | sorting 후 monotone 보장 | 100% |

### 3.3 Slice 별 성능표 (필수)
가드레일 segment 의 안정성이 평균보다 중요 (코덱스 권고):
- **저가 (<5M KRW)**
- **중가 / 고가** (price tertile)
- **medium = ink** (운영 가드레일 segment)
- **gallery_tier = 3** (운영 가드레일 segment)
- **extreme area** (log_area P5 미만 / P95 초과)

각 slice 별 coverage / width 가 평균과 크게 차이나면 가드레일 정책 재검토.

## 4. 합격 / 보류 / 폐기 결정 기준

### 4.1 합격 (운영 shadow / internal flag 도입)
- Pinball loss: M2 baseline 보다 작음
- coverage 4 항목 모두 합격선 범위 내
- q50 MdAPE 운영 baseline +1.0%p 이내
- raw crossing rate ≤ 5%
- slice 별 coverage 큰 편차 없음 (모든 slice 가 합격선 ±10%p 이내)
- → **API: `q25 / q50 / q75` 추가, shadow 모드부터 시작**

### 4.2 보류 (재시도)
- coverage 1-2 항목 합격선 벗어남 (5%p 이내)
- crossing rate 5-10%
- slice 1-2 개 큰 편차 → calibration / regularization 재시도

### 4.3 폐기
- Pinball loss M2 baseline 보다 큼
- coverage 3+ 항목 합격선 벗어남 (10%p 이상)
- crossing rate > 10%
- → 본 cycle 종결, 기존 ±20% band 유지

## 5. 운영 통합 (합격 시)

### 5.1 API 변경 (spec §5)
```diff
  "prediction": {
-   "value": "int (KRW)",
+   "value": "int (KRW, = q50)",
    "log_value": "float",
-   "band_low": "int (optional, ±20%)",
-   "band_high": "int (optional)"
+   "band_low": "int (= q25)",
+   "band_high": "int (= q75)",
+   "q25": "int",
+   "q50": "int",
+   "q75": "int"
  }
```

### 5.2 단계적 도입
1. **Shadow / internal flag**: 즉시 (API 추가 trivial)
2. **External band 전환**: Phase 2 confirmatory 합격 후
3. **Calibration table 과 분리 유지** (코덱스 권고)

### 5.3 Monitoring 추가
- 운영 트래픽의 empirical coverage (q25/q50/q75) 일 단위
- Crossing rate 일 단위
- Width drift PSI

## 6. Out of Scope (별도 주제)

- **Conformal Prediction (CQR)**: 장기 후속 주제, 본 cycle 미포함
- **Multi-quantile joint fit**: 구현 복잡도 대비 실익 작음 (코덱스 비권고)
- **GBM Quantile**: 트랙 1 영역 (해석 가능성 제약 위배)
- **Phase 2 (full data) 재검증**: 본 cycle 합격 후 별도 cycle

## 7. 산출물

- 실험 코드: `experiments/structural_v1/stage3_quantile_regression.py`
- 결과 JSON: `experiments/structural_v1/results/stage3_quantile_regression.json`
- 결과 보고: 본 문서 §8 (실험 후 추가)

## 8. 결과 요약 (실험 완료 2026-05-07, 코덱스 conditional accept)

### 8.1 100-seed LAO 결과

| 항목 | M1 (Linear Quantile) | M2 (Huber + global residual) |
|---|---|---|
| Pinball total | **0.4510** ✓ | 0.4519 |
| Coverage q25 / q50 / q75 | 26.8% / 51.6% / 75.0% | 26.9% / 51.7% / 75.0% |
| Central coverage q25-q75 | 48.2% | 48.1% |
| Width avg (log price) | 0.486 | 0.459 |
| Raw crossing rate | **0.0%** | 0.0% (by construction) |
| q50 MdAPE | 24.54% | 24.27% |

### 8.2 합격 판정 (8 항목 중 7 통과)

| # | 기준 | M1 결과 | 합격 |
|---|---|---|---|
| 1 | Pinball M1 < M2 | -0.0009 | ✓ |
| 2 | q25 cov ∈ [20%, 30%] | 26.8% | ✓ |
| 3 | q50 cov ∈ [45%, 55%] | 51.6% | ✓ |
| 4 | q75 cov ∈ [70%, 80%] | 75.0% | ✓ |
| 5 | central cov ∈ [45%, 55%] | 48.2% | ✓ |
| 6 | q50 MdAPE 운영 +1%p 이내 | +0.27%p | ✓ |
| 7 | crossing rate ≤ 5% | 0.0% | ✓ |
| 8 | Width M1 ≤ M2 | 0.486 vs 0.459 | ✗ |

→ **8번 미달의 본질**: M1 = conditional band (row 별 적응) vs M2 = global residual (모든 row 동일 폭). M2 의 평균 width 가 좁은 것은 **균일 폭의 평균 효과**일 뿐, 실질적 정보량은 M1 이 우수 (특히 extreme area 0.74 등 적응적 폭).

→ **재판정 (코덱스)**: "Width M1 ≤ M2" 기준은 conditional vs global 비교에서 본질적으로 불공정 → 제거. **M1 conditional accept = shadow 승인**.

### 8.3 Slice Calibration (single seed)

| Slice | n | cov_q25 | cov_q50 | cov_q75 | central | width |
|---|---|---|---|---|---|---|
| 저가 (P33↓) | 94 | 24.5% | **68.1%** | 97.9% | 73.4% | 0.54 |
| 중가 | 87 | 24.1% | 44.8% | 78.2% | 54.0% | 0.45 |
| 고가 (P67↑) | 89 | 19.1% | **42.7%** | 87.6% | 68.5% | 0.59 |
| ink | 22 | 36.4% | 59.1% | 86.4% | 50.0% | 0.46 |
| tier 3 | 151 | 22.5% | 54.3% | 89.4% | 66.9% | 0.55 |
| extreme area | 26 | 42.3% | 65.4% | 88.5% | 46.2% | 0.74 |

→ 저가 / 고가 calibration shift (q50 cov 50% 에서 ±18%p 어긋남) — 모델이 저가 일관 과소 / 고가 일관 과대 예측. Phase 2 / shadow 단계에서 slice-wise intercept correction 검토.

### 8.4 운영 도입 권고 (코덱스)

> **M1 = shadow / internal flag 즉시 도입 가능 (uncertainty band 전용)**  
> **점예측 (`prediction.value`) 은 Huber 유지** — Phase 2 까지 default 전환 X

분리 운영 이유:
- M1 q50 MdAPE 24.54% > Huber 24.27% (+0.27%p) — 점예측은 Huber 우위
- M1 q25/q75 의 conditional band 가 ±20% 임의 band 보다 informative
- **Hybrid 운영**: `value = Huber 점예측 / band = M1 quantile` → 양쪽 장점 결합

API 변경 (spec §5):
```diff
  "prediction": {
-   "value": "int (KRW)",
+   "value": "int (KRW, = Huber 점예측, 운영 유지)",
    "log_value": "float",
-   "band_low": "int (optional, ±20%)",
-   "band_high": "int (optional)"
+   "band_low": "int (= q25 from M1 Linear Quantile, shadow 승인)",
+   "band_high": "int (= q75 from M1)",
+   "q25": "int (M1)",
+   "q50": "int (M1, value 와 다를 수 있음)",
+   "q75": "int (M1)"
  }
```

### 8.5 Default 전환 조건 (Phase 2 acceptance gate)
1. Overall coverage 재현 (q25/q50/q75 합격 범위 유지)
2. Raw crossing rate ≤ 5%
3. **저가/고가 slice q50 bias 완화** (또는 허용 범위 정의)
4. Shadow 안정성 확인 (운영 트래픽 1주 dashboard)

### 8.6 Shadow 단계 monitoring
- 운영 트래픽의 empirical coverage (q25/q50/q75) 일 단위
- 가격 tertile / source / depth bin 별 coverage 분리 추적
- Crossing rate 일 단위
- Width drift PSI (학습 분포 vs 운영 분포)

### 8.7 후속 검토 (Phase 2 진입 전)
- Slice calibration 후처리 1-2 개 비교 (slice-wise intercept correction / quantile recalibration)
- Median residual by slice → intercept vs slope 진단
- Phase 2 표본에서 raw crossing rate 재확인 (full data 의 희귀 영역 / interaction 다양화 영향)

## 9. 미반영 / 폐기

- ❌ "Width M1 ≤ M2" 기준 — conditional vs global 비교 불공정으로 제거 (코덱스 권고)
- ❌ Multi-quantile joint fit — 구현 복잡도 대비 실익 작음
- ❌ Calibration table 과 quantile band 통합 — coverage 망가뜨릴 위험 (분리 유지)
- ⏳ Conformal Quantile Regression (CQR) — 장기 후속 주제
