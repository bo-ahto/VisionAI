# 가격 예측 엔진 — 개발 실행 계획서 v2.1

> **기반 문서**: `price_prediction_engine_plan.md` v3.1 (Codex 12회 Ready)
> **개발 주체**: Claude (직접 구현)
> **작성일**: 2026-03-26
> **Codex 리뷰**: 3회차 (6 Pass / 1 Partial → 수정 반영)

---

## 0. 착수 전 준비

### 0.1 의존성 추가 (pyproject.toml) — Phase별 분리

```toml
[project.optional-dependencies]
# Phase 1: 전처리 + Baseline + 검증
price-engine-core = [
    "pandas>=2.1",
    "pyarrow>=14.0",           # parquet 출력
    "scikit-learn>=1.3",
    "catboost>=1.2",
]

# Phase 2: 모델 비교 실험
price-engine-exp = [
    "lightgbm>=4.0",
    "xgboost>=2.0",
    "optuna>=3.4",
    "shap>=0.43",
]

# Phase 2 Sprint 3: API 서비스
price-engine-api = [
    "fastapi>=0.104",
    "uvicorn>=0.24",
]
```

설치 명령:
```bash
pip install -e ".[price-engine-core]"          # Phase 1 착수 시
pip install -e ".[price-engine-core,price-engine-exp]"  # Phase 2 착수 시
pip install -e ".[price-engine-core,price-engine-exp,price-engine-api]"  # Sprint 3
```

### 0.2 디렉토리 구조

```
src/visionai/price_engine/
├── __init__.py
├── preprocessing/          # Sprint 0 — 파싱
│   ├── __init__.py
│   ├── dimension_parser.py
│   ├── medium_parser.py
│   └── year_parser.py
├── features/               # Sprint 0 — 피처 생성 + 누수 방지
│   ├── __init__.py
│   ├── splits.py               # 시계열 분할 스펙
│   ├── artist_stats_snapshot.py # fold별 작가 통계 스냅샷
│   ├── cold_start.py            # Cold Start fallback 로직
│   ├── estimate_features.py     # 추정가 파생 피처
│   └── dataset_builder.py       # 전체 피처 조립 → parquet
├── models/                 # Sprint 1 — 학습/추론
│   ├── __init__.py
│   ├── trainer.py
│   └── predictor.py
├── validation/             # Sprint 1 — 검증 도구
│   ├── __init__.py
│   ├── metrics.py              # MAPE, MdAPE, R², Within-K%
│   ├── confidence_grade.py     # 규칙 기반 신뢰도 등급
│   ├── calibration.py          # grade별 coverage 테이블
│   ├── bias_check.py           # 재변환 편향 검증
│   ├── backtest.py             # 워크포워드 백테스트 러너
│   ├── interval_backtest.py    # Prediction Interval coverage 검증
│   ├── latency_check.py        # 추론 latency 측정 (< 100ms)
│   └── time_proxy_check.py     # 회차→시간 proxy 타당성 검증
├── reporting/              # Sprint 1.5 — 리포트 생성
│   ├── __init__.py
│   ├── segment_report.py       # 세그먼트별 MAPE 리포트
│   ├── cold_start_report.py    # D등급 slice 리포트
│   └── ablation_report.py      # 피처 그룹 ablation
├── reliability/            # Phase 2 Sprint 3 — Calibration 기반 신뢰도
│   ├── __init__.py
│   ├── reliability_model.py    # Pr(APE ≤ 0.2) 예측 모델
│   └── reliability_features.py # 메타피처 추출 (5개 기본 + 2개 확장)
├── experiments/            # Phase 2 Sprint 2 — 모델 비교
│   ├── __init__.py
│   ├── champion_challenger.py  # 모델 비교 프레임워크
│   └── shadow_runner.py        # Shadow mode retrospective scoring
└── api/                    # Phase 2 Sprint 3 — 서비스 (착수 보류)
    ├── __init__.py
    ├── server.py
    └── schemas.py

scripts/
├── run_pipeline.py             # Sprint 0 실행
├── train_model.py              # Sprint 1 실행
├── validate_model.py           # Sprint 1 검증 일괄 실행
├── generate_predictions.py     # Sprint 1.5 정적 JSON 생성
└── check_gate.py               # Phase 1→2 전환 게이트 자동 판정

tests/price_engine/
├── __init__.py
├── test_dimension_parser.py
├── test_medium_parser.py
├── test_year_parser.py
├── test_parser_robustness.py   # 오타/혼합언어/특수 패턴
├── test_splits.py
├── test_artist_stats_snapshot.py
├── test_cold_start.py
├── test_leakage_snapshot.py    # fold별 미래 데이터 검증
├── test_confidence_grade.py
├── test_calibration.py
└── test_backtest.py
```

### 0.3 착수 전 리스크 대응 준비

설계 문서 8장의 리스크를 착수 전 태스크로 환원:

| # | 리스크 (설계 8장) | 실행 태스크 | 소유 Sprint |
|---|--------|-------------------|------------|
| 1 | 추정가 지배력 | `log(price/estimate_mid)` 타깃 변환 실험 포함 (4.2절 ②) | Phase 2 Sprint 2 |
| 2 | 저가 MAPE 과대 | `segment_report.py`에 가격대별 분리 보고 + MdAPE 병행 | Sprint 1 |
| 3 | Cold Start | `cold_start.py`에 그룹 크기 ≥ 10 검증 + D등급 리포트 | Sprint 0 + 1.5 |
| 4 | 유찰 데이터 부재 | 프론트/리포트에 "낙찰 기준" 면책 문구 삽입 | Sprint 1.5 |
| 5 | 회차 ≠ 시간 | `time_proxy_check.py` Sprint 1 초반 실행 | Sprint 1 |
| 6 | 고가 서프라이즈 | Two-Step 실험 포함 (4.2절 ④) | Phase 2 Sprint 2 |
| 7 | Schema Drift | parser failure rate 3단계 로깅 인터페이스 | Sprint 0 |
| 8 | Distribution Shift | Phase 2에서 PSI/KS 모니터링 모듈 구축 | Phase 2 Sprint 3 |
| 9 | Calibration Drift | Phase 2에서 grade별 coverage 주간 계산 자동화 | Phase 2 Sprint 3 |
| 10 | Feedback Loop | 운영 문서에 "모델 예측→추정가 설정 금지" 정책 명시 | Sprint 1.5 |
| 11 | Fairness | D등급 UX에 "데이터 부족으로 인한 근사치" 면책 문구 | Sprint 1.5 |
| 12 | Re-training Policy | 모델 버전 태깅 (`model_v{날짜}_{MAPE}.cbm`) + champion/challenger 기준 | Sprint 1 + Phase 2 |
| 13 | 데이터 개정 | CSV SHA256 체크섬 기록, `data/VERSION` 파일 생성 | 준비 |

### 0.4 engine_test.html 정합성 수정 (선행 작업)

현재 테스트 페이지가 설계 문서 v3.1과 불일치:

| 불일치 | 수정 내용 |
|--------|----------|
| `artist_sell_rate` 참조 | 삭제 (전량 낙찰 데이터에서 계산 불가) |
| "22개 피처" 표기 | → "21개 피처" |
| "낙찰률" 문구 | 삭제 |
| 피처 기여도 차트 | `artist_sell_rate` 항목 제거 |

---

## 1. Sprint 0: 데이터 전처리 + 피처 파이프라인

### 1.1 작업 목록 (세부 분해)

| # | 모듈 | 파일 | 내용 | 입력 → 출력 | 기획서 |
|---|------|------|------|------------|--------|
| 0-1 | preprocessing | `dimension_parser.py` | 크기 문자열 파싱 5개 패턴 | `"81×116cm"` → `{h:81, w:116, area:9396, ratio:0.70, is_3d:F}` | 3.2.1 |
| 0-2 | preprocessing | `medium_parser.py` | 재료 → 매체 10종 + 지지체 7종 | `"캔버스에 유채"` → `{medium:유화, support:캔버스}` | 3.2.2 |
| 0-3 | preprocessing | `year_parser.py` | 제작연도 추출 + 결측 플래그 | `"1937"` → `{year:1937, is_missing:0}` | 3.2.3 |
| 0-4 | features | `splits.py` | 시계열 분할 스펙 정의 | auction_type별 train/valid/test 회차 범위 | 3.3 규칙 2 |
| 0-5 | features | `artist_stats_snapshot.py` | fold별 작가 통계 동적 계산 | works DataFrame + cutoff → snapshot stats | 3.3 규칙 1 |
| 0-6 | features | `cold_start.py` | Cold Start fallback (그룹 평균) | estimate_tier + auction_type → 대체값 | 3.2.4 |
| 0-7 | features | `estimate_features.py` | 추정가 파생 (mid, range, ratio, ln_mid) | estimate_low/high → 4개 피처 | 3.2.3 |
| 0-8 | features | `dataset_builder.py` | 전체 피처 조립 → parquet | CSV + 파서 + 스냅샷 → 21개 피처 parquet | 3.1 |
| 0-9 | tests | `test_dimension_parser.py` | 5개 패턴 + 경계 케이스 | — | — |
| 0-10 | tests | `test_medium_parser.py` | 10종 매체 + 7종 지지체 | — | — |
| 0-11 | tests | `test_year_parser.py` | 정상/결측/이상값 | — | — |
| 0-12 | tests | `test_parser_robustness.py` | 오타, 혼합언어, 특수문자, 빈값 | — | 9장 #6 |
| 0-13 | tests | `test_splits.py` | 분할 경계 + 누수 없음 확인 | — | 3.3 |
| 0-14 | tests | `test_artist_stats_snapshot.py` | fold별 미래 데이터 미포함 검증 | — | 3.3 규칙 1 |
| 0-15 | tests | `test_leakage_snapshot.py` | 전체 피처에 대한 leakage unit test | — | 3.3 규칙 4 |
| 0-16 | tests | `test_cold_start.py` | fallback 그룹 크기 ≥ 10 검증 | — | 5.2 |
| 0-17 | scripts | `run_pipeline.py` | Sprint 0 전체 실행 + 검증 | — | — |

### 1.2 Sprint 0 완료 조건

```
□ 크기 파싱 성공률 ≥ 97%
□ 재료 분류: 10종 매체 + 7종 지지체 커버
□ 전체 43,866건 처리 완료 (누락 0건)
□ Parser robustness test 통과 (오타/혼합언어 20개+ 케이스)
□ Leakage unit test 전체 통과
□ Cold Start fallback 그룹 크기 ≥ 10 (모든 그룹)
□ data/preprocessed_features.parquet 생성
□ data/VERSION 파일 생성 (CSV 체크섬 기록)
□ ruff check + mypy 통과
□ 전체 테스트 통과 (pytest)
```

### 1.3 병렬화 가능 작업

```
병렬 가능:
  0-1(dimension) | 0-2(medium) | 0-3(year)  ← 파서 3종 독립
  0-4(splits) | 0-7(estimate_features)       ← 서로 독립

순차 필수:
  파서 3종 → 0-5(artist snapshot) → 0-6(cold start) → 0-8(dataset builder)
  모든 모듈 → 0-15(leakage test)
```

---

## 2. Sprint 1: Baseline 재현 + 검증 도구

### 2.1 작업 목록

| # | 모듈 | 파일 | 내용 | 기획서 |
|---|------|------|------|--------|
| 1-1 | validation | `time_proxy_check.py` | 회차 단조증가 + 날짜 힌트 샘플 검증 | 3.3 time proxy |
| 1-2 | validation | `confidence_grade.py` | 규칙 기반 A/B/C/D 등급 산정 | 5.2 Phase 1 |
| 1-3 | validation | `metrics.py` | MAPE, MdAPE, R², Within-K% | 6.1 |
| 1-4 | validation | `calibration.py` | grade별 ±20%/30% coverage 테이블 | 5.2 필수 검증 |
| 1-5 | validation | `bias_check.py` | 가격대별 median(P̂/P) + smearing correction | 2.2 재변환 편향 |
| 1-6 | validation | `backtest.py` | 워크포워드 백테스트 (4개 cutoff) | 9장 #1 |
| 1-7 | models | `trainer.py` | CatBoost 학습 (시계열 split, early stopping) | 4.1 |
| 1-8 | models | `predictor.py` | 모델 로드 + 추론 + exp() 복원 | 5.1 |
| 1-9 | reporting | `segment_report.py` | 타입별/가격대별/grade별 MAPE 리포트 | 6.2 |
| 1-10 | scripts | `train_model.py` | 학습 실행 | — |
| 1-11 | scripts | `validate_model.py` | 검증 일괄 실행 (아래 체크리스트 전체) | — |
| 1-12 | tests | `test_confidence_grade.py` | 등급 경계 테스트 (0/1/5/6/19/20건) | — |
| 1-13 | tests | `test_calibration.py` | coverage 계산 정확성 | — |
| 1-14 | tests | `test_backtest.py` | backtest fold 구성 검증 | — |

### 2.2 Sprint 1 필수 검증 체크리스트

```
□ Time proxy 검증:
  - 타입별 회차 단조증가 확인
  - 날짜 힌트 샘플 20건+ 일치율 ≥ 90%
□ Baseline 재현: MAPE 40.17% ± 0.5%p
□ 재변환 편향 검증:
  - 가격대별 median(P̂/P_actual) 산출
  - 모든 구간 ≥ 0.95 → Pass
  - 0.85~0.95 → smearing correction 적용 후 재검증
  - < 0.85 → 해당 구간 원인 분석 필수
□ 세그먼트별 MAPE 리포트 (타입 3개 + 가격대 5개 + grade 4개)
□ Calibration 테이블:
  - A등급 within-20% ≥ 65%
  - 각 grade별 within-20%/30% 수치 보고
□ 워크포워드 백테스트 4회 (cutoff 350/380/410/440)
  - 전체 MAPE 표준편차 < 3%p 이면 안정적
□ 모든 테스트 통과 (pytest)
□ 추론 latency 측정: `validation/latency_check.py` → 단건 < 100ms 확인
□ 모델 파일 저장: model_v{날짜}_{MAPE}.cbm
```

---

## 3. Sprint 1.5: 정적 JSON + 테스트 페이지 + 최종 검증

### 3.1 작업 목록

| # | 모듈 | 파일 | 내용 | 기획서 |
|---|------|------|------|--------|
| 1.5-1 | reporting | `cold_start_report.py` | D등급 slice 세부 분석 (4개 항목) | 5.2 D등급 |
| 1.5-2 | reporting | `ablation_report.py` | 피처 그룹 ablation (추정가/작가/크기) | 9장 #7 |
| 1.5-3 | scripts | `generate_predictions.py` | 작가별/호수별 예측 → JSON | 7.2 |
| 1.5-4 | frontend | `data/predictions.json` | 정적 예측 결과 | — |
| 1.5-5 | frontend | `engine_test.html` 수정 | predictions.json fetch 연동 | 7.1 |
| 1.5-6 | scripts | `check_gate.py` | 전환 게이트 자동 판정 (10개 조건) | 10장 |

### 3.2 Sprint 1.5 필수 검증 체크리스트

```
□ Cold Start / D등급 slice 리포트:
  - D등급 전체 MAPE/MdAPE/Within-20%
  - __UNKNOWN__ / __NEW_ARTIST__ 별도 분석
  - 1건 작가(C등급) 희소 데이터 검증
  - fallback 그룹 크기 및 대체값 품질
□ D등급 UX 결정:
  - Option A: 넓은 범위 + "참고용"
  - Option B: "예측 불가" 표시
  - Option C: 추정가 범위만 표시
  → MdAPE > 100% 하위그룹은 "예측 불가" 필수
□ Prediction Interval Backtest:
  - Phase 1 고정 margin의 grade별 실제 coverage 측정
  - A등급 ±20% coverage 보고
□ Ablation 재현 Test (동일 split):
  - 추정가 제거 → MAPE 변화
  - 작가 통계 제거 → MAPE 변화
  - 크기 피처 제거 → MAPE 변화
□ 주요 작가 10명 수동 검증 (예측 vs 실제)
□ Human Benchmark: 내부 전문가 추정 vs 모델 추정 비교 (최소 20건)
```

---

## 4. Phase 1→2 전환 게이트 (`check_gate.py`)

Sprint 1.5 완료 후 자동 판정. **필수 9개 조건 전체 충족 시 Phase 2 진행** (+ 권장 1개):

```
[필수]
□ 전체 MAPE < 38% AND 메이저 < 19% AND 프리미엄 < 30%
□ Leakage unit test 전체 통과
□ Confidence calibration: A등급 within-20% ≥ 65%
□ Parser failure rate < 1%
□ Cold Start fallback 검증 완료
□ 워크포워드 백테스트 4회 안정적 (MAPE 표준편차 < 3%p)
□ 추론 latency < 100ms (단건)
□ D등급 품질 하한: MdAPE > 100% 하위그룹 "예측 불가" 처리
□ 재변환 편향: 모든 가격대 median(P̂/P) ≥ 0.95

[권장]
○ auction_date 확보 (미확보 시 time proxy 한계 문서화 후 진행 가능)
```

---

## 5. 설계 문서 9장 검증 10개 항목 → Sprint 매핑

| # | 검증 항목 | Sprint | 구현 모듈 | 완료 기준 |
|---|----------|--------|----------|----------|
| 1 | 워크포워드 백테스트 | 1 | `validation/backtest.py` | 4회 cutoff, MAPE 편차 < 3%p |
| 2 | Leakage Unit Test | 0 | `tests/test_leakage_snapshot.py` | 전체 통과 (CI 포함) |
| 3 | Calibration Test | 1 | `validation/calibration.py` | grade별 coverage 테이블 |
| 4 | Prediction Interval Backtest | 1.5 | `validation/interval_backtest.py` | Phase 1 고정 margin grade별 coverage |
| 5 | Cold Start Slice Test | 1.5 | `reporting/cold_start_report.py` | D등급 + C등급 희소 매체 |
| 6 | Parser Robustness Test | 0 | `tests/test_parser_robustness.py` | 오타/혼합언어 20개+ 케이스 |
| 7 | Ablation 재현 Test | 1.5 | `reporting/ablation_report.py` | 동일 split 3그룹 비교 |
| 8 | Champion/Challenger 비교 | Phase 2 Sprint 2 | `experiments/champion_challenger.py` | 5개 모델 동일 test set 비교, 전체/타입별 MAPE 테이블 |
| 9 | Human Benchmark | 1.5 | 수동 실행 + `reporting/segment_report.py`에 결과 포함 | 전문가 vs 모델 20건+ |
| 10 | Shadow Mode | Phase 2 Sprint 3 | `experiments/shadow_runner.py` | 실 경매 입력 기록 → 결과 확정 후 retrospective MAPE 산출 |

---

## 6. 실행 순서 + 의존성 그래프

```
준비 (0.1~0.4)
  ├── pyproject.toml 수정 (price-engine-core)
  ├── 디렉토리 구조 생성
  ├── data/VERSION (CSV 체크섬)
  └── engine_test.html 정합성 수정
      │
Sprint 0 ─────────────────────────────────────────
  │
  ├── [병렬] 0-1 dimension_parser
  ├── [병렬] 0-2 medium_parser
  ├── [병렬] 0-3 year_parser
  ├── [병렬] 0-4 splits
  ├── [병렬] 0-7 estimate_features
  │         │
  │         ▼
  ├── [순차] 0-5 artist_stats_snapshot (파서 + splits 필요)
  ├── [순차] 0-6 cold_start (snapshot 필요)
  ├── [순차] 0-8 dataset_builder (전체 필요)
  │         │
  │         ▼
  ├── [병렬] 0-9~0-16 테스트 코드 (모듈과 함께)
  └── [순차] 0-17 run_pipeline.py + 완료 조건 확인
      │
Sprint 1 ─────────────────────────────────────────
  │
  ├── [선행] 1-1 time_proxy_check (Sprint 1 첫 작업)
  ├── [선행] 1-2 confidence_grade (calibration의 선행 조건)
  ├── [병렬] 1-3 metrics
  ├── [병렬] 1-7 trainer
  ├── [병렬] 1-8 predictor
  │         │
  │         ▼
  ├── [순차] 1-4 calibration (grade + metrics 필요)
  ├── [순차] 1-5 bias_check (predictor 필요)
  ├── [순차] 1-6 backtest (trainer + splits 필요)
  ├── [순차] 1-9 segment_report (metrics + predictor 필요)
  ├── [순차] latency_check (predictor 필요)
  └── [순차] 1-10~1-14 스크립트 + 테스트
      │
Sprint 1.5 ───────────────────────────────────────
  │
  ├── [병렬] 1.5-1 cold_start_report
  ├── [병렬] 1.5-2 ablation_report
  ├── [병렬] interval_backtest (calibration + predictor 필요)
  ├── [순차] 1.5-3 generate_predictions (모델 + 피처 필요)
  ├── [순차] 1.5-4 predictions.json
  ├── [순차] 1.5-5 engine_test.html 연동
  └── [최종] 1.5-6 check_gate.py → 전환 게이트 자동 판정
```

---

## 7. 착수 첫 작업 (순서)

```
1. pyproject.toml에 price-engine-core 의존성 추가 + pip install
2. 디렉토리 구조 생성 (__init__.py 포함)
3. data/VERSION 파일 생성 (CSV SHA256 체크섬)
4. engine_test.html 정합성 수정 (artist_sell_rate 삭제, 21개 피처)
5. dimension_parser.py + test_dimension_parser.py + test_parser_robustness.py
6. medium_parser.py + test_medium_parser.py
7. year_parser.py + test_year_parser.py
8. splits.py + test_splits.py
9. estimate_features.py
10. artist_stats_snapshot.py + test_artist_stats_snapshot.py
11. cold_start.py + test_cold_start.py
12. dataset_builder.py + test_leakage_snapshot.py
13. run_pipeline.py → preprocessed_features.parquet 생성
14. Sprint 0 완료 조건 전체 확인
```

---

## 8. Phase 2 작업 분해 (전환 게이트 통과 후)

### Sprint 2 — 모델 비교 실험

비교 대상 5개 모델 (기획서 4.2절 우선순위):
```
① CatBoost 단일 고도화 (21→34개 피처)
② 타깃 변환: log(price/estimate_mid) — CatBoost
③ auction_type별 분리 모델 (위클리/프리미엄/메이저 각각 CatBoost)
④ Two-Step: 분류(추정가 초과 여부) → 조건부 회귀
⑤ 3-Model Stacking: CatBoost + LightGBM + XGBoost → Ridge
```

| # | 모듈 | 내용 | 기획서 |
|---|------|------|--------|
| 2-1 | features | Phase 2 동적 피처 13개 추가 (artist_premium_avg 등) | 3.1 |
| 2-2 | models | `trainer.py` 확장 — LightGBM/XGBoost 학습 지원 | 4.2 ①⑤ |
| 2-3 | models | 타깃 변환 모델 ② 구현 | 4.2 ② |
| 2-4 | models | auction_type별 분리 모델 ③ 구현 | 4.2 ③ |
| 2-5 | models | Two-Step ④ 구현 | 4.2 ④ |
| 2-6 | experiments | `champion_challenger.py` — 5개 모델 동일 test set 비교 | 9장 #8 |
| 2-7 | experiments | 최종 Champion 선택 + Optuna 최적화 (100 trials) | 4.3 |

### Sprint 3 — Reliability + API + 운영 배포

| # | 모듈 | 내용 | 기획서 |
|---|------|------|--------|
| 3-1 | reliability | `reliability_features.py` — 메타피처 추출 (기본 5개) | 5.2 |
| 3-2 | reliability | `reliability_model.py` — Pr(APE ≤ 0.2) 학습 | 5.2 |
| 3-3 | api | `server.py` — FastAPI 서버 | 7.2 |
| 3-4 | api | `schemas.py` — request/response 스키마 | — |
| 3-5 | experiments | `shadow_runner.py` — Shadow mode retrospective scoring | 9장 #10 |
| 3-6 | validation | 드리프트 모니터링 (PSI/KS, rolling MAPE) | 8.3 |
| 3-7 | frontend | engine_test.html → API 호출 전환 | 7.2 |

---

*본 계획서는 `price_prediction_engine_plan.md` v3.1의 마일스톤, 검증 전략 10개, 전환 게이트(필수 9 + 권장 1), 리스크 13건을 실행 가능한 태스크로 분해한 것이다. Phase 1(Sprint 0~1.5)은 Claude가 직접 구현하며, 각 Sprint 완료 시 git commit + 검증 결과를 보고한다.*
