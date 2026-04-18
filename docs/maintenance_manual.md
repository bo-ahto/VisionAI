# VisionAI 미술품 가격 예측 시스템 - 유지보수 매뉴얼

> **버전**: 1.0.0
> **최종 업데이트**: 2026-03-29

---

## 목차

1. [시스템 아키텍처](#1-시스템-아키텍처)
2. [모델 재학습 절차](#2-모델-재학습-절차)
3. [모델 Artifact 관리](#3-모델-artifact-관리)
4. [매크로 데이터 갱신](#4-매크로-데이터-갱신)
5. [외부 데이터 관리](#5-외부-데이터-관리)
6. [모니터링](#6-모니터링)
7. [테스트 실행 방법](#7-테스트-실행-방법)
8. [트러블슈팅 가이드](#8-트러블슈팅-가이드)
9. [배포 체크리스트](#9-배포-체크리스트)

---

## 1. 시스템 아키텍처

### 1.1 디렉토리 구조

```
VisionAI/
├── src/visionai/price_engine/
│   ├── api/
│   │   ├── server.py                  # FastAPI 서버 (6 엔드포인트)
│   │   └── schemas.py                 # Pydantic 요청/응답 스키마
│   ├── preprocessing/
│   │   ├── dimension_parser.py        # 작품 크기 파싱 (가로×세로)
│   │   ├── medium_parser.py           # 재료/기법 분류
│   │   └── year_parser.py             # 제작연도 파싱
│   ├── features/
│   │   ├── artist_stats_snapshot.py   # 작가별 통계 스냅샷
│   │   ├── cold_start.py             # Cold Start 피처
│   │   ├── dataset_builder.py         # 데이터셋 빌더
│   │   ├── estimate_features.py       # 추정가 관련 피처
│   │   ├── hedonic_stats.py           # Hedonic 통계
│   │   ├── splits.py                  # Train/Calib/Valid/Test 분할
│   │   ├── title_nlp.py              # 제목 NLP 피처 (7개)
│   │   ├── track_config.py           # Strict/Distilled 2-트랙 피처 설정
│   │   ├── macro_indicators.py       # 매크로 경제 피처 (7개)
│   │   └── artist_similarity.py      # K-NN 유사 작가 피처 (4개)
│   ├── models/
│   │   ├── predictor.py              # 예측기
│   │   ├── segment_calibrator.py     # 세그먼트별 보정
│   │   ├── target_transform.py       # Target Transform v1
│   │   ├── target_transform_v2.py    # Price Engine v2
│   │   └── trainer.py                # 학습기
│   ├── estimate_generator/
│   │   ├── generator.py              # EstimateGenerator (통합 파이프라인)
│   │   ├── quantile_model.py         # Model-A (MultiQuantile CatBoost)
│   │   ├── estimate_model.py         # Model-B (추정가 Regressor)
│   │   ├── hedonic_features.py       # Hedonic 피처 빌드 (49개)
│   │   ├── quantile_calibrator.py    # Quantile Calibrator
│   │   ├── estimate_calibrator.py    # Estimate Calibrator
│   │   ├── conformal_calibrator.py   # CQR (Conformalized Quantile Regression)
│   │   ├── cold_start.py            # 5-tier Cold Start fallback
│   │   ├── distillation.py          # Knowledge Distillation
│   │   ├── market_rounder.py        # 시장 관행 라운딩
│   │   └── selection_bias.py        # 선택 편향 보정
│   ├── validation/
│   │   ├── confidence_grade.py       # A/B/C/D 신뢰도 등급
│   │   ├── metrics.py               # 평가 지표
│   │   ├── calibration.py           # 보정 검증
│   │   ├── backtest.py              # 백테스트
│   │   ├── interval_backtest.py     # 구간 백테스트
│   │   ├── bias_check.py            # 편향 검사
│   │   ├── drift_monitor.py         # 드리프트 모니터
│   │   ├── time_proxy_check.py      # 시간 프록시 누수 검사
│   │   └── latency_check.py         # 지연 시간 체크
│   ├── reliability/
│   │   ├── reliability_features.py   # 신뢰성 피처
│   │   └── reliability_model.py     # 신뢰성 모델
│   ├── experiments/
│   │   ├── shadow_recorder.py       # Shadow 기록
│   │   └── shadow_scorer.py         # Shadow 스코어링
│   └── reporting/
│       ├── ablation_report.py       # Ablation 리포트
│       ├── cold_start_report.py     # Cold Start 리포트
│       └── segment_report.py        # 세그먼트 리포트
├── scripts/
│   ├── train_phase5_final.py        # 최종 학습 스크립트 ★
│   ├── train_estimate_models.py     # 추정가 모델 학습
│   ├── train_v2_engine.py           # v2 엔진 학습
│   ├── diagnose_gap.py             # Val-Test Gap 진단
│   ├── check_gate.py               # Gate 검증
│   ├── check_estimate_gate.py      # 추정가 Gate 검증
│   └── collectors/
│       ├── collect_macro_data.py    # K-Auction 내부 회차별 통계
│       ├── collect_ecos_data.py    # ECOS API (KOSPI, 환율, CPI)
│       └── integrate_external_v2.py # 외부 데이터 Entity Resolution
├── data/
│   ├── k-auction-works-20260325.csv  # 원본 경매 데이터 (43,866건)
│   ├── preprocessed_features.parquet # 전처리된 피처
│   ├── macro_session.csv            # K-Auction 회차별 통계
│   ├── macro_monthly.csv            # 월별 매크로 (내부+ECOS)
│   └── ecos_macro.csv               # ECOS 실데이터 (KOSPI, 환율, CPI)
├── model_test_results/
│   ├── model_a_quantile.cbm         # Model-A
│   ├── model_b_estimate.cbm         # Model-B
│   ├── target_transform_v1.cbm      # 낙찰가 예측 모델
│   ├── price_engine_v2.cbm          # v2 통합 엔진
│   ├── *.pkl                        # Calibrator 파라미터
│   └── *.json                       # 성능 메트릭
└── tests/                           # 86개 테스트
```

### 1.2 데이터 흐름

```
[K-Auction 원본 CSV]
       │
       ▼
[피처 빌드] ─── hedonic_features.py (49개 Hedonic 피처)
       │         ├── preprocessing/ (크기, 재료, 연도 파싱)
       │         ├── features/ (작가 통계, NLP, 매크로)
       │         └── artist_similarity.py (K-NN, Cold-only)
       │
       ▼
[데이터 분할] ─── splits.py (Train/Calib/Valid/Test, 시간 기반)
       │
       ▼
[모델 학습]
       ├── Model-A: HedonicQuantileModel (q25/q50/q75)
       ├── Model-B: EstimateRegressorModel (추정가 생성)
       └── v2 Engine: PriceEngineV2 (통합 예측)
       │
       ▼
[보정]
       ├── CQR: ConformalQuantileCalibrator (Coverage 보장)
       ├── Quantile Calibrator
       └── Estimate Calibrator
       │
       ▼
[API 서빙] ─── FastAPI (server.py)
       ├── /predict_price    ← 추정가 필요
       ├── /estimate         ← 추정가 불필요
       ├── /estimate/validate ← 추정가 비교
       └── /predict_v2       ← 통합
```

### 1.3 모델 구조

| 모델 | 파일명 | 알고리즘 | 입력 피처 | 출력 |
|------|--------|---------|----------|------|
| Model-A | model_a_quantile.cbm | CatBoost MultiQuantile | 49개 Hedonic | q25/q50/q75 (ln_price) |
| Model-B | model_b_estimate.cbm | CatBoost Regressor | 49개 Hedonic + Model-A 출력 | 추정가 low/mid/high |
| v1 Engine | target_transform_v1.cbm | CatBoost + Target Transform | 22개 Baseline | 낙찰가 예측 |
| v2 Engine | price_engine_v2.cbm | CatBoost | 22개 Baseline + 추정가 | 낙찰가 예측 |

---

## 2. 모델 재학습 절차

### 2.1 전체 파이프라인

```
① 데이터 업데이트 → ② 매크로 갱신 → ③ 피처 빌드 → ④ 학습 → ⑤ 검증 → ⑥ 배포
```

### 2.2 상세 절차

#### Step 1: 데이터 업데이트

K-Auction 신규 경매 결과를 `data/k-auction-works-{YYYYMMDD}.csv`에 추가합니다.

```bash
# CSV 컬럼 확인 (필수 컬럼)
# 회차, 작가, 작품명, 재료, 크기, 타입, 추정가(최저), 추정가(최고), 낙찰가, Lot
head -1 data/k-auction-works-20260325.csv
```

데이터 파일명을 `scripts/train_phase5_final.py`의 `DATA_PATH`에 반영합니다.

#### Step 2: 매크로 데이터 갱신

두 개의 스크립트를 순서대로 실행합니다.

```bash
# Step 2a: K-Auction 내부 회차별 통계 생성
PYTHONPATH=src python3 scripts/collectors/collect_macro_data.py
# → data/macro_session.csv (session, kauction_sold_rate, kauction_avg_price)
# → data/macro_monthly.csv (K-Auction 내부 통계)

# Step 2b: 공공 매크로 지표 수집 (KOSPI, 환율, CPI)
PYTHONPATH=src python3 scripts/collectors/collect_ecos_data.py
# → data/ecos_macro.csv (kospi_close, usd_krw, cpi)
# → data/macro_monthly.csv 갱신 (ECOS 실데이터 병합)
```

> **주의**: `collect_macro_data.py`는 K-Auction 내부 통계만 생성합니다. KOSPI/환율/CPI는 `collect_ecos_data.py`를 별도 실행해야 합니다.

#### Step 3: 피처 빌드 + 학습

```bash
# 최종 학습 스크립트 실행 (피처 빌드 포함)
PYTHONPATH=src python3 scripts/train_phase5_final.py
```

이 스크립트가 수행하는 작업:
1. Hedonic 피처 빌드 (49개)
2. 매크로 피처 조인 (7개)
3. Artist Similarity 피처 계산 (Cold-only, 4개)
4. High PSI 피처 정규화 (market_price_index, career_length, medium_avg_price)
5. Train/Calib/Valid/Test 분할
6. Model-A 학습 (CatBoost MultiQuantile, iterations=2000, depth=8, lr=0.05)
7. CQR 보정 (alpha=0.38)
8. 성능 평가 + Gate 판정

#### Step 4: 검증

학습 완료 후 출력되는 Gate 판정을 확인합니다.

```bash
# 메트릭 확인
cat model_test_results/phase5_final_metrics.json | python3 -m json.tool
```

핵심 Gate:
| Gate | 기준 | 확인 사항 |
|------|------|----------|
| G1 | Test MdAPE ≤ 32% | 전체 정확도 |
| G2 | Gap ≤ 2.5%p | 과적합 정도 |
| G3 | Test R² ≥ 0.40 | 설명력 |
| G4 | Cold MdAPE ≤ 58% | 신규 작가 성능 |
| G5 | Coverage ≥ 55% | 구간 포함률 |
| G8 | Monotonicity ≥ 0.99 | 단조성 |

#### Step 5: 추정가 모델 학습 (필요 시)

```bash
PYTHONPATH=src python3 scripts/train_estimate_models.py
PYTHONPATH=src python3 scripts/train_v2_engine.py
```

#### Step 6: 배포

모든 Gate 통과 확인 후, `model_test_results/` 디렉토리의 모델 파일을 서버에 배포합니다.

---

## 3. 모델 Artifact 관리

### 3.1 파일 목록 및 용도

| 파일 | 크기 (대략) | 용도 | 갱신 주기 |
|------|------------|------|----------|
| `model_a_quantile.cbm` | ~15MB | 가격 구간 예측 (핵심) | 신규 경매 데이터 추가 시 |
| `model_b_estimate.cbm` | ~10MB | 추정가 생성 | 동일 |
| `target_transform_v1.cbm` | ~12MB | 낙찰가 예측 (v1) | 동일 |
| `price_engine_v2.cbm` | ~12MB | 통합 예측 (v2) | 동일 |
| `quantile_calibrator.pkl` | ~1KB | Quantile 보정 파라미터 | 재학습 시 |
| `estimate_calibrator.pkl` | ~1KB | 추정가 보정 파라미터 | 재학습 시 |
| `conformal_calibrator.pkl` | ~1KB | CQR 파라미터 (Q값) | 재학습 시 |
| `phase5_final_metrics.json` | ~2KB | 성능 메트릭 기록 | 재학습 시 |
| `estimate_metrics.json` | ~2KB | 추정가 메트릭 | 재학습 시 |
| `gap_diagnosis.json` | ~3KB | Val-Test Gap 진단 | 재학습 시 |
| `baseline_results.json` | ~2KB | 베이스라인 결과 | 초기 1회 |

### 3.2 갱신 주기 권장사항

| 트리거 | 주기 | 설명 |
|--------|------|------|
| 신규 경매 완료 | 분기 1회 | 최소 3회차 이상 신규 데이터 축적 후 |
| 성능 저하 감지 | 즉시 | MdAPE 5%p 이상 악화 시 |
| 외부 데이터 갱신 | 반기 1회 | Artsy, Seoul Auction 등 |
| 매크로 지표 | 월 1회 | ECOS API 수집 |

### 3.3 Artifact 백업

재학습 전 기존 모델을 반드시 백업합니다.

```bash
# 백업 디렉토리 생성
mkdir -p model_test_results/backup/$(date +%Y%m%d)

# 현재 모델 백업
cp model_test_results/*.cbm model_test_results/*.pkl \
   model_test_results/backup/$(date +%Y%m%d)/
```

---

## 4. 매크로 데이터 갱신

### 4.1 ECOS API 설정

한국은행 경제통계시스템(ECOS) API를 사용하여 매크로 지표를 수집합니다.

```bash
# ECOS API 키 설정 (환경 변수)
export ECOS_API_KEY="your-api-key-here"
```

> ECOS API 키는 [한국은행 ECOS](https://ecos.bok.or.kr/)에서 무료로 발급받을 수 있습니다.

### 4.2 수집 지표 (7개)

| 지표 | ECOS 코드 | 설명 |
|------|----------|------|
| KOSPI | 802Y001/0001000 | 종합주가지수 |
| KRW/USD | 731Y001/0000001 | 원-달러 환율 |
| 기준금리 | 722Y001/0101000 | 한국은행 기준금리 |
| CPI | 901Y009/0 | 소비자물가지수 |
| M2 | 101Y003/BBGS00 | 통화량 |
| 소비자심리지수 | 511Y002/FME/CSCI | 소비자심리지수 |
| 건설투자 | 200Y002/10111 | 건설투자 (부동산 대리 변수) |

### 4.3 수집 절차

```bash
# Step 1: K-Auction 내부 통계 (sold_rate, avg_price)
PYTHONPATH=src python3 scripts/collectors/collect_macro_data.py
# → data/macro_session.csv, data/macro_monthly.csv (내부 통계)

# Step 2: ECOS 공공 매크로 (KOSPI, 환율, CPI)
PYTHONPATH=src python3 scripts/collectors/collect_ecos_data.py
# → data/ecos_macro.csv, data/macro_monthly.csv 갱신

# 출력 확인
head data/macro_monthly.csv
```

### 4.4 갱신 주기

- **월 1회** 수집 권장 (매월 초)
- 최소 12개월분의 히스토리가 필요 (Gate G16 기준)
- 현재 485세션(약 6년) 분량 축적

---

## 5. 외부 데이터 관리

### 5.1 Artsy 데이터

해외 미술 시장 데이터로, Cold Start 작가의 글로벌 가격 참조에 사용됩니다.

```bash
# Entity Resolution (작가명 매칭)
PYTHONPATH=src python3 scripts/collectors/integrate_external_v2.py
```

- 현재 100+ 작가 매핑 완료
- 매칭 정밀도(Match Precision) ≥ 95% (Gate G15)
- 반기 1회 갱신 권장

### 5.2 작가명 매핑 갱신

외부 데이터의 작가명과 K-Auction 작가명을 매핑하는 Entity Resolution은 `integrate_external_v2.py`에서 수행합니다.

주의사항:
- 동명이인 처리: 작가 생년 + 주요 매체로 구분
- 한글/영문 변환: K-Auction은 한글, Artsy는 영문
- 신규 작가 추가 시 매핑 테이블 업데이트 필요

---

## 6. 모니터링

### 6.1 성능 지표 확인

```bash
# 최신 메트릭 확인
cat model_test_results/phase5_final_metrics.json | python3 -m json.tool

# Gap 진단 결과
cat model_test_results/gap_diagnosis.json | python3 -m json.tool
```

### 6.2 핵심 모니터링 항목

| 항목 | 정상 범위 | 경고 기준 | 조치 |
|------|----------|----------|------|
| Test MdAPE | < 36% | > 40% | 재학습 검토 |
| Val-Test Gap | < 4%p | > 6%p | 과적합 진단 (diagnose_gap.py) |
| Cold MdAPE | < 50% | > 60% | Similarity 피처 점검 |
| Coverage | > 55% | < 50% | CQR alpha 조정 |
| Monotonicity | = 1.00 | < 0.99 | 피처 누수 점검 |
| API 응답 시간 | < 100ms | > 500ms | 서버 리소스 확인 |

### 6.3 Gap 진단

Val-Test Gap이 커지면 시간 변화에 따른 분포 이동(drift)을 의심합니다.

```bash
# Gap 진단 실행
PYTHONPATH=src python3 scripts/diagnose_gap.py
```

진단 항목:
- **PSI(Population Stability Index)**: 피처별 분포 이동 측정. PSI > 0.2인 피처는 정규화 필요.
- **Attribution Drift**: SHAP 기반 피처 기여도 변화. Gate G13 기준 < 0.3.
- **시간 역전 검사**: 미래 정보 누수 확인. 0건이어야 정상(Gate G7).

### 6.4 서버 헬스체크

```bash
# 주기적 헬스체크 (crontab 등록 권장)
curl -sf http://localhost:8001/health | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not data.get('model_loaded'):
    print('ALERT: Model not loaded!')
    sys.exit(1)
print('OK')
"
```

---

## 7. 테스트 실행 방법

### 7.1 전체 테스트

```bash
# 전체 테스트 실행
PYTHONPATH=src pytest tests/ -v

# 커버리지 포함
PYTHONPATH=src pytest tests/ --cov=src/visionai -v
```

### 7.2 카테고리별 테스트

```bash
# Gap 진단 테스트
PYTHONPATH=src pytest tests/price_engine/test_gap_diagnosis.py -v

# 누수 감사 테스트
PYTHONPATH=src pytest tests/price_engine/test_gap_leak_audit.py -v

# 매크로 피처 테스트
PYTHONPATH=src pytest tests/price_engine/test_macro_indicators.py -v

# Entity Resolution 테스트
PYTHONPATH=src pytest tests/price_engine/test_entity_resolution.py -v

# Artist Similarity 테스트
PYTHONPATH=src pytest tests/price_engine/test_artist_similarity.py -v

# Cold Start 테스트
PYTHONPATH=src pytest tests/price_engine/test_cold_start_estimate.py -v
```

### 7.3 린트 및 타입 체크

```bash
# 린트 검사
ruff check src/

# 코드 포매팅
ruff format src/

# 타입 체크
mypy src/
```

### 7.4 테스트 현황

| 범위 | 테스트 수 | 상태 |
|------|----------|------|
| Gap 진단 | 10 | 전체 통과 |
| 누수 감사 | 4 | 전체 통과 |
| 매크로 피처 | 6 | 전체 통과 |
| Entity Resolution | 10 | 전체 통과 |
| Artist Similarity | 11 | 전체 통과 |
| Cold Start | 19 + 6 | 전체 통과 |
| Distillation + CQR | 18 | 전체 통과 |
| **합계** | **86** | **81 pass, 5 skip** |

> 5개 skip은 전체 성능 Gate(G1~G3, G5, G6)로, 모델 성능 개선 시 자동 통과됩니다.

---

## 8. 트러블슈팅 가이드

### 8.1 서버 시작 실패

#### 증상: `ModuleNotFoundError: No module named 'visionai'`

**원인**: PYTHONPATH가 설정되지 않음.

**해결**:
```bash
# PYTHONPATH 설정 후 실행
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app --port 8001
```

또는 패키지를 editable 모드로 설치:
```bash
pip install -e .
```

#### 증상: `FileNotFoundError: model_test_results/target_transform_v1.cbm`

**원인**: 모델 파일 누락.

**해결**: 학습 스크립트를 먼저 실행하거나 백업에서 복원.
```bash
PYTHONPATH=src python3 scripts/train_phase5_final.py
```

#### 증상: `ModuleNotFoundError: No module named 'catboost'`

**원인**: price-engine-core 의존성 미설치.

**해결**:
```bash
pip install -e ".[price-engine-core,price-engine-api]"
```

### 8.2 API 오류

#### 증상: 503 "Model not loaded"

**원인**: 서버 시작 후 모델 로딩이 완료되지 않았거나 실패.

**해결**: 서버 로그를 확인하여 로딩 에러를 진단.
```bash
# 서버 로그에서 에러 확인
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app --port 8001 --log-level debug
```

#### 증상: 503 "Phase 3 모델 미로드"

**원인**: Model-A(`model_a_quantile.cbm`) 또는 Model-B(`model_b_estimate.cbm`) 파일 누락.

**해결**: 추정가 모델 학습 실행.
```bash
PYTHONPATH=src python3 scripts/train_estimate_models.py
```

#### 증상: 422 Validation Error

**원인**: 요청 파라미터 타입/값 오류.

**해결**: 스키마 확인.
- `auction_type`은 `위클리`, `프리미엄`, `메이저` 중 하나
- `estimate_low` ≤ `estimate_high`
- `width_cm`, `height_cm` ≥ 0
- `/predict_v2`에서 `estimate_low`와 `estimate_high`는 둘 다 있거나 둘 다 없어야 함

#### 증상: 500 Internal Server Error

**원인**: 예측 중 내부 오류 (보통 피처 불일치).

**해결**:
1. 서버 로그에서 상세 traceback 확인
2. 모델 학습 시의 피처 목록과 API 입력이 일치하는지 확인
3. 데이터 파일(`preprocessed_features.parquet`) 갱신 필요 여부 확인

### 8.3 학습 오류

#### 증상: 학습 시 `KeyError: 'ln_price'`

**원인**: 피처 빌드 과정에서 `ln_price` 컬럼이 생성되지 않음.

**해결**: 원본 CSV에 `낙찰가` 컬럼이 존재하고 양수 값인지 확인.

#### 증상: CQR Coverage가 너무 낮음

**원인**: alpha 값이 너무 높음.

**해결**: `ConformalQuantileCalibrator(alpha=0.38)` 에서 alpha를 낮춤 (예: 0.35). alpha가 낮을수록 구간이 넓어지고 coverage가 높아짐.

### 8.4 성능 저하

#### 증상: Test MdAPE가 이전 대비 5%p 이상 증가

**점검 순서**:
1. 신규 데이터에 이상치가 있는지 확인 (극단적 가격)
2. PSI 진단으로 분포 이동 확인 (`diagnose_gap.py`)
3. 피처 중요도 변화 확인 (SHAP)
4. Cold/Warm 분리 분석 — 어느 쪽이 악화됐는지 확인

---

## 9. 배포 체크리스트

모델 재학습 후 프로덕션 배포 전 아래 항목을 확인합니다.

### 9.1 사전 검증

- [ ] `scripts/train_phase5_final.py` 정상 완료
- [ ] Gate 판정 확인 (`phase5_final_metrics.json`)
  - [ ] G4 (Cold MdAPE ≤ 58%): PASS
  - [ ] G5 (Coverage ≥ 55%): PASS
  - [ ] G7 (Leakage 0건): PASS
  - [ ] G8 (Monotonicity ≥ 0.99): PASS
- [ ] 전체 테스트 통과: `PYTHONPATH=src pytest tests/ -v`
- [ ] 린트 통과: `ruff check src/`

### 9.2 모델 파일 확인

- [ ] `model_a_quantile.cbm` — 존재, 최신 날짜
- [ ] `model_b_estimate.cbm` — 존재, 최신 날짜
- [ ] `target_transform_v1.cbm` — 존재
- [ ] `price_engine_v2.cbm` — 존재
- [ ] `conformal_calibrator.pkl` — 존재, 최신 날짜
- [ ] `quantile_calibrator.pkl` — 존재
- [ ] `estimate_calibrator.pkl` — 존재
- [ ] `preprocessed_features.parquet` — 존재, 데이터 건수 확인

### 9.3 배포 절차

```bash
# 1. 기존 모델 백업
mkdir -p model_test_results/backup/$(date +%Y%m%d)
cp model_test_results/*.cbm model_test_results/*.pkl \
   model_test_results/backup/$(date +%Y%m%d)/

# 2. 서버 재시작 (Graceful)
# Docker/Dokploy 환경:
#   docker restart <container_name>
# 직접 실행 환경:
kill -TERM $(pgrep -f "uvicorn.*server:app") && \
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app \
  --host 0.0.0.0 --port 8001 --workers 4 &

# 3. 헬스체크 확인
sleep 10
curl -sf http://localhost:8001/health

# 4. Smoke Test
curl -X POST http://localhost:8001/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"artist":"김환기","width_cm":72.7,"height_cm":60.6,"medium":"캔버스에 유채"}'

# 5. 모델 정보 확인
curl http://localhost:8001/api/v1/model_info
```

### 9.4 롤백 절차

문제 발생 시 백업에서 복원합니다.

```bash
# 백업 복원
cp model_test_results/backup/{YYYYMMDD}/*.cbm model_test_results/
cp model_test_results/backup/{YYYYMMDD}/*.pkl model_test_results/

# 서버 재시작
kill -TERM $(pgrep -f "uvicorn.*server:app")
PYTHONPATH=src uvicorn visionai.price_engine.api.server:app \
  --host 0.0.0.0 --port 8001 --workers 4 &
```
