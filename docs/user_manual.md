# VisionAI 미술품 가격 예측 시스템 - 사용자 매뉴얼

> **버전**: 1.0.0
> **최종 업데이트**: 2026-03-29
> **모델**: Model-A CatBoost MultiQuantile + CQR Calibration

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [설치 방법](#2-설치-방법)
3. [서버 실행](#3-서버-실행)
4. [API 사용법](#4-api-사용법)
5. [결과 해석 가이드](#5-결과-해석-가이드)
6. [FAQ](#6-faq)

---

## 1. 시스템 개요

VisionAI 가격 예측 시스템은 **K-Auction 미술품 경매 낙찰가**를 예측하는 AI 엔진입니다.

### 주요 기능

| 기능 | 설명 |
|------|------|
| **낙찰가 예측** | 경매사 추정가 기반으로 낙찰가를 예측 |
| **추정가 생성** | 추정가 없이 작품 정보만으로 적정 가격대 산출 |
| **추정가 검증** | AI 예측과 경매사 추정가 간 괴리율 분석 |
| **통합 예측** | 추정가 자동 생성 + 낙찰가 예측을 한 번에 수행 |

### 기술 스택

- **모델**: CatBoost MultiQuantile Regression (q25, q50, q75)
- **보정**: Conformalized Quantile Regression (CQR, Romano et al. 2019)
- **데이터**: K-Auction 43,866건 경매 기록 (위클리/프리미엄/메이저)
- **API**: FastAPI + Uvicorn

### 성능 지표

| 지표 | 값 | 설명 |
|------|----|------|
| Test MdAPE | 35.5% | 중앙 절대 백분율 오차 |
| Test R² | 0.308 | 결정 계수 |
| Cold MdAPE | 48.7% | 신규 작가 예측 오차 |
| Coverage | 56.1% | 예측 구간 포함률 |
| Monotonicity | 1.00 | 단조성 (완벽) |

---

## 2. 설치 방법

### 2.1 시스템 요구사항

- **Python**: 3.11 이상
- **OS**: macOS, Linux, Windows
- **메모리**: 4GB 이상 권장 (모델 로딩 시 약 1.5GB 사용)

### 2.2 패키지 설치

```bash
# 저장소 클론
git clone <repository-url> VisionAI
cd VisionAI

# 가상 환경 생성 (권장)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 핵심 의존성 설치
pip install -e ".[price-engine-core,price-engine-api]"
```

### 2.3 의존성 목록

| 패키지 | 용도 | 최소 버전 |
|--------|------|----------|
| `pandas` | 데이터 처리 | >= 2.1 |
| `pyarrow` | Parquet 파일 I/O | >= 14.0 |
| `scikit-learn` | ML 유틸리티 | >= 1.3 |
| `catboost` | 핵심 모델 | >= 1.2 |
| `fastapi` | API 서버 | >= 0.104 |
| `uvicorn` | ASGI 서버 | >= 0.24 |
| `numpy` | 수치 연산 | >= 1.24 |

### 2.4 모델 파일 확인

서버 실행 전 아래 파일이 `model_test_results/` 디렉토리에 존재해야 합니다.

```
model_test_results/
├── model_a_quantile.cbm          # Model-A (Quantile Regression)
├── model_b_estimate.cbm          # Model-B (추정가 생성)
├── target_transform_v1.cbm       # 낙찰가 예측 모델
├── price_engine_v2.cbm           # v2 통합 엔진
├── quantile_calibrator.pkl       # Quantile Calibrator
├── estimate_calibrator.pkl       # Estimate Calibrator
└── conformal_calibrator.pkl      # CQR Calibrator
```

데이터 파일:
```
data/
└── preprocessed_features.parquet  # 전처리된 피처 데이터
```

---

## 3. 서버 실행

### 3.1 기본 실행

```bash
# 프로젝트 루트에서 실행
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app --host 0.0.0.0 --port 8001
```

### 3.2 개발 모드 (자동 리로드)

```bash
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app --host 0.0.0.0 --port 8001 --reload
```

### 3.3 프로덕션 모드 (워커 복수)

```bash
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 4
```

### 3.4 서버 정상 동작 확인

```bash
curl http://localhost:8001/health
```

정상 응답:
```json
{
  "status": "ok",
  "model_loaded": true
}
```

### 3.5 API 문서 (Swagger UI)

서버 실행 후 브라우저에서 접속:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## 4. API 사용법

### 4.1 POST /api/v1/predict_price - 낙찰가 예측

**용도**: 경매사 추정가가 있는 작품의 낙찰가를 예측합니다.

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `artist_name` | string | O | 작가명 | "김환기" |
| `auction_type` | string | O | 경매 타입: `위클리`, `프리미엄`, `메이저` | "메이저" |
| `width_cm` | float | O | 가로 (cm) | 72.7 |
| `height_cm` | float | O | 세로 (cm) | 60.6 |
| `medium` | string | X | 재료/기법 | "캔버스에 유채" |
| `estimate_low` | int | O | 추정가 최저 (원) | 50000000 |
| `estimate_high` | int | O | 추정가 최고 (원) | 80000000 |
| `year_created` | int | X | 제작연도 | 1970 |

#### curl 예시

```bash
curl -X POST http://localhost:8001/api/v1/predict_price \
  -H "Content-Type: application/json" \
  -d '{
    "artist_name": "김환기",
    "auction_type": "메이저",
    "width_cm": 72.7,
    "height_cm": 60.6,
    "medium": "캔버스에 유채",
    "estimate_low": 50000000,
    "estimate_high": 80000000,
    "year_created": 1970
  }'
```

#### 응답 예시

```json
{
  "predicted_price": 72000000,
  "price_range": [57600000, 86400000],
  "confidence_grade": "A",
  "estimate_vs_prediction": 110.8,
  "model_version": "target_transform_v1+calibration",
  "prediction_method": "target_transform+calibration"
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `predicted_price` | int | 예측 낙찰가 (원) |
| `price_range` | list[int] | [하한, 상한] - 신뢰도 등급에 따른 예측 구간 |
| `confidence_grade` | string | 예측 신뢰도: A(높음) / B / C / D(낮음) |
| `estimate_vs_prediction` | float | 추정가 중앙값 대비 예측가 비율 (%) |
| `model_version` | string | 사용된 모델 버전 |
| `prediction_method` | string | 예측 방법론 |

---

### 4.2 POST /api/v1/estimate - 추정가 생성

**용도**: 경매사 추정가 없이 작품 정보만으로 적정 가격대를 산출합니다. Model-A(Quantile)와 Model-B(Regressor)를 결합한 2단계 파이프라인입니다.

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `artist` | string | O | 작가명 | "이우환" |
| `medium` | string | X | 재료/기법 | "캔버스에 유채" |
| `width_cm` | float | O | 가로 (cm) | 72.7 |
| `height_cm` | float | O | 세로 (cm) | 60.6 |
| `year` | int | X | 제작연도 | 2015 |
| `title` | string | X | 작품 제목 (NLP 피처 추출용) | "Dialogue" |
| `auction_type` | string | X | 경매 타입 (기본값: 프리미엄) | "프리미엄" |

#### curl 예시

```bash
curl -X POST http://localhost:8001/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "이우환",
    "medium": "캔버스에 유채",
    "width_cm": 72.7,
    "height_cm": 60.6,
    "year": 2015,
    "title": "Dialogue",
    "auction_type": "프리미엄"
  }'
```

#### 응답 예시

```json
{
  "price_range": {
    "low": 35000000,
    "mid": 52000000,
    "high": 78000000
  },
  "estimate": {
    "low": 40000000,
    "mid": 55000000,
    "high": 80000000
  },
  "confidence_grade": "B",
  "cold_start_tier": null,
  "warnings": []
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `price_range` | object | Model-A의 연속 가격 구간 {low, mid, high} |
| `estimate` | object | Model-B의 라운딩된 추정가 {low, mid, high} |
| `confidence_grade` | string | 신뢰도 등급 A/B/C/D |
| `cold_start_tier` | int\|null | Cold Start tier (1~5, null이면 Warm 작가) |
| `warnings` | list[string] | 경고 메시지 목록 |

> **price_range vs estimate**: `price_range`는 모델의 원시 연속 예측값이고, `estimate`는 경매 관행에 맞게 라운딩된 추정가입니다. 실제 추정가로 사용할 때는 `estimate` 값을 참조하세요.

---

### 4.3 POST /api/v1/estimate/validate - 추정가 검증

**용도**: AI 추정가와 경매사(K-Auction) 추정가를 비교하여 괴리율을 분석합니다. 세그먼트별 차등 경고 기준이 적용됩니다.

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `artist` | string | O | 작가명 | "박서보" |
| `medium` | string | X | 재료/기법 | "캔버스에 유채" |
| `width_cm` | float | O | 가로 (cm) | 130.0 |
| `height_cm` | float | O | 세로 (cm) | 162.0 |
| `year` | int | X | 제작연도 | 2000 |
| `title` | string | X | 작품 제목 | "Ecriture" |
| `auction_type` | string | X | 경매 타입 | "메이저" |
| `kauction_estimate_low` | int | O | K-Auction 추정가 최저 (원) | 100000000 |
| `kauction_estimate_high` | int | O | K-Auction 추정가 최고 (원) | 150000000 |

#### curl 예시

```bash
curl -X POST http://localhost:8001/api/v1/estimate/validate \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "박서보",
    "medium": "캔버스에 유채",
    "width_cm": 130.0,
    "height_cm": 162.0,
    "year": 2000,
    "title": "Ecriture",
    "auction_type": "메이저",
    "kauction_estimate_low": 100000000,
    "kauction_estimate_high": 150000000
  }'
```

#### 응답 예시

```json
{
  "ai_estimate_mid": 118000000,
  "kauction_mid": 125000000,
  "divergence_rate": -5.6,
  "threshold_pct": 30.0,
  "warning": false,
  "message": ""
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `ai_estimate_mid` | int | AI 추정가 중앙값 (원) |
| `kauction_mid` | int | K-Auction 추정가 중앙값 (원) |
| `divergence_rate` | float | 괴리율 (%), 음수이면 AI가 낮게 산정 |
| `threshold_pct` | float | 경고 기준 괴리율 (%) |
| `warning` | bool | 괴리율이 기준을 초과하면 true |
| `message` | string | 추가 설명 메시지 |

> **경고 기준**: 괴리율(`divergence_rate`)의 절대값이 `threshold_pct`를 초과하면 `warning: true`가 됩니다. 이 경우 추정가 재검토를 권장합니다.

---

### 4.4 POST /api/v1/predict_v2 - 통합 예측

**용도**: 추정가가 있으면 그대로 사용하고, 없으면 Model-B가 자동 생성하여 낙찰가를 예측합니다. 추정가 입력이 선택사항인 통합 엔드포인트입니다.

#### 요청 파라미터

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `artist` | string | O | 작가명 | "이중섭" |
| `medium` | string | X | 재료/기법 | "종이에 유채" |
| `width_cm` | float | O | 가로 (cm) | 29.5 |
| `height_cm` | float | O | 세로 (cm) | 41.5 |
| `year` | int | X | 제작연도 | 1954 |
| `auction_type` | string | X | 경매 타입 | "메이저" |
| `estimate_low` | int | X | 추정가 최저 (미입력 시 자동 생성) | 200000000 |
| `estimate_high` | int | X | 추정가 최고 (미입력 시 자동 생성) | 300000000 |

> **주의**: `estimate_low`와 `estimate_high`는 반드시 함께 입력하거나 함께 생략해야 합니다.

#### curl 예시 - 추정가 미입력 (자동 생성)

```bash
curl -X POST http://localhost:8001/api/v1/predict_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "이중섭",
    "medium": "종이에 유채",
    "width_cm": 29.5,
    "height_cm": 41.5,
    "year": 1954,
    "auction_type": "메이저"
  }'
```

#### curl 예시 - 추정가 입력

```bash
curl -X POST http://localhost:8001/api/v1/predict_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "이중섭",
    "medium": "종이에 유채",
    "width_cm": 29.5,
    "height_cm": 41.5,
    "year": 1954,
    "auction_type": "메이저",
    "estimate_low": 200000000,
    "estimate_high": 300000000
  }'
```

#### 응답 예시

```json
{
  "predicted_price": 245000000,
  "estimate_used": {
    "low": 200000000,
    "mid": 250000000,
    "high": 300000000
  }
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `predicted_price` | int | 예측 낙찰가 (원) |
| `estimate_used.low` | int | 사용된 추정가 최저 (입력값 또는 자동 생성) |
| `estimate_used.mid` | int | 사용된 추정가 중앙값 |
| `estimate_used.high` | int | 사용된 추정가 최고 (입력값 또는 자동 생성) |

---

### 4.5 GET /api/v1/model_info - 모델 정보

**용도**: 현재 서버에 로드된 모델의 버전과 성능 지표를 확인합니다.

#### curl 예시

```bash
curl http://localhost:8001/api/v1/model_info
```

#### 응답 예시

```json
{
  "model_version": "target_transform_v1+calibration",
  "model_type": "CatBoost + Segment Calibration",
  "features_count": 22,
  "test_mape": 27.01,
  "test_r2": 0.936,
  "a_grade_within_20pct": 71.6,
  "gate_status": "9/9 passed"
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `model_version` | string | 모델 버전 식별자 |
| `model_type` | string | 모델 종류 |
| `features_count` | int | 사용 피처 수 |
| `test_mape` | float | 테스트 셋 MAPE (%) |
| `test_r2` | float | 테스트 셋 결정 계수 |
| `a_grade_within_20pct` | float | A등급 작품 중 20% 이내 적중률 (%) |
| `gate_status` | string | 품질 Gate 통과 현황 |

---

### 4.6 GET /health - 헬스체크

**용도**: 서버 상태와 모델 로딩 여부를 확인합니다. 로드밸런서, 모니터링 시스템 연동에 사용합니다.

#### curl 예시

```bash
curl http://localhost:8001/health
```

#### 응답 예시

```json
{
  "status": "ok",
  "model_loaded": true
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `status` | string | 서버 상태 ("ok") |
| `model_loaded` | bool | 모델 로딩 완료 여부 |

---

## 5. 결과 해석 가이드

### 5.1 신뢰도 등급 (confidence_grade)

예측 결과의 신뢰도를 A/B/C/D 4단계로 표시합니다. 등급에 따라 `price_range`의 마진이 달라집니다.

| 등급 | 조건 | 마진 | 해석 |
|------|------|------|------|
| **A** | 낙찰 20건 이상 + 추정가 3천만~10억 + 최근 10회차 내 거래 | ±20% | 높은 신뢰도. 예측을 적극 참고 가능 |
| **B** | 낙찰 6~19건 | ±30% | 보통 신뢰도. 참고용으로 활용 |
| **C** | 낙찰 1~5건 | ±50% | 낮은 신뢰도. 보조 지표로만 활용 |
| **D** | 낙찰 0건 (신규/미상) | ±70% | 매우 낮은 신뢰도. Cold Start 작가 |

#### 등급별 활용 권장사항

- **A등급**: 예측 낙찰가를 기준으로 의사결정 가능. 전체 작품 중 약 15%가 해당.
- **B등급**: 예측값을 참고하되, 시장 상황과 작가 최근 동향을 함께 고려.
- **C등급**: 가격 방향성(고가/저가) 판단 용도로만 활용.
- **D등급**: Cold Start 작가. `price_range`가 넓으므로 유사 작가 비교를 통한 크로스체크 필요.

### 5.2 가격 범위 (price_range)

`price_range`는 `[하한, 상한]`으로 구성됩니다.

```
price_range = [predicted_price * (1 - 마진), predicted_price * (1 + 마진)]
```

예시: 예측가 7,200만원, A등급(±20%)인 경우
- 하한: 7,200만 × 0.80 = 5,760만원
- 상한: 7,200만 × 1.20 = 8,640만원
- `price_range: [57600000, 86400000]`

### 5.3 추정가 대비 예측 비율 (estimate_vs_prediction)

```
estimate_vs_prediction = (predicted_price / estimate_mid) × 100
```

| 값 | 해석 |
|----|------|
| > 120% | AI가 추정가보다 20% 이상 높게 예측 → 낙찰가 상승 가능성 |
| 80~120% | 추정가와 유사한 수준 |
| < 80% | AI가 추정가보다 20% 이상 낮게 예측 → 낙찰가 하락 가능성 |

### 5.4 Cold Start Tier

`/api/v1/estimate` 응답의 `cold_start_tier`는 신규 작가의 데이터 풍부도에 따른 5단계 분류입니다.

| Tier | 설명 | 데이터 소스 |
|------|------|------------|
| 1 | 외부 경매 데이터 있음 | Artsy/Seoul Auction 등 |
| 2 | 유사 작가 매칭됨 (K-NN) | 동일 매체/가격대 작가 |
| 3 | 매체 평균 활용 | 동일 medium_category 통계 |
| 4 | Bayesian Shrinkage | 글로벌 사전 분포 |
| 5 | 글로벌 기본값 | 전체 시장 평균 |

Tier가 낮을수록 더 풍부한 데이터 기반의 예측이며, Tier 5는 정보가 가장 적은 경우입니다.

---

## 6. FAQ

### Q1. 서버 시작 시 "Model not loaded" 오류가 발생합니다.

`model_test_results/` 디렉토리에 모델 파일(.cbm, .pkl)이 있는지 확인하세요. 모델 파일이 없으면 학습 스크립트를 먼저 실행해야 합니다.

```bash
PYTHONPATH=src python3 scripts/train_phase5_final.py
```

### Q2. 지원하는 경매 타입은 무엇인가요?

3가지를 지원합니다: `위클리`, `프리미엄`, `메이저`. 그 외 값을 입력하면 422 Validation Error가 발생합니다.

### Q3. 추정가(estimate_low, estimate_high)를 모를 때는?

`/api/v1/estimate` 또는 `/api/v1/predict_v2` 엔드포인트를 사용하세요. 추정가 없이 작가명, 작품 크기, 재료만으로 가격 예측이 가능합니다.

### Q4. 작가명은 한글로 입력해야 하나요?

학습 데이터가 K-Auction 기준이므로 K-Auction에서 사용하는 작가명 형식으로 입력하세요. 대부분 한글(예: "김환기", "이우환")이며, 외국 작가의 경우 영문도 가능합니다.

### Q5. 제작연도를 모르는 경우는?

`year_created`(또는 `year`) 필드를 생략하거나 `null`로 전달하면 됩니다. 내부적으로 `is_year_missing` 피처로 처리됩니다.

### Q6. 재료(medium) 입력 형식은?

자연어로 입력합니다. 내부 파서가 자동 분류합니다.

- 예: "캔버스에 유채", "한지에 수묵", "브론즈", "판화", "종이에 혼합재료"
- 비워두면 기본 처리됩니다.

### Q7. API 응답이 503 에러를 반환합니다.

서버가 시작된 직후이거나 모델 파일이 누락된 상태입니다. `/health` 엔드포인트로 `model_loaded` 상태를 확인하세요.

### Q8. 예측 결과에 대한 법적 책임은?

본 시스템의 예측 결과는 참고용이며, 투자 자문이나 가격 보증이 아닙니다. 실제 낙찰가는 시장 상황, 경매 분위기, 컨디션 등 모델이 포착하지 못하는 요인에 의해 달라질 수 있습니다.

### Q9. 동시 요청(Concurrent Requests) 처리가 가능한가요?

Uvicorn의 `--workers` 옵션으로 멀티 프로세스를 사용할 수 있습니다. 단, 각 워커가 모델을 개별 로드하므로 메모리 사용량이 워커 수에 비례하여 증가합니다.

### Q10. 입력값의 단위는 무엇인가요?

- **크기**: cm (센티미터)
- **가격**: 원 (KRW), 정수 (소수점 없음)
- **연도**: 서기 (예: 1970, 2015)
