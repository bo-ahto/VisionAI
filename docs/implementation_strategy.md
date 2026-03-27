# K-Auction 가격 예측 모델 — 실제 구현 전략서

> **데이터 기준**: k-auction-works-20260325.csv (43,866건), k-auction-artists-20260325.csv (3,286명)
> **작성일**: 2026-03-25
> **목적**: 실제 데이터 분석 결과를 바탕으로 한 단계별 구현 로드맵

---

## 1. 데이터 현황 진단

### 1.1 데이터 규모

| 항목 | 수량 | 비고 |
|------|------|------|
| 총 작품 | 43,866건 | 전부 낙찰 건 (유찰 데이터 없음) |
| 총 작가 | 3,289명 (works 기준) | artists 테이블과 3,250명 교집합 |
| 경매 타입 | 위클리 28,554 / 프리미엄 8,485 / 메이저 6,827 | 3개 세그먼트 |
| 회차 범위 | 위클리 1~486 / 프리미엄 55~224 / 메이저 98~195 | 시간축으로 활용 |

### 1.2 가격 분포 — 핵심 특성

```
가격대별 건수:
  <100만          15,828건 (36.1%)   ████████████████████
  100만~500만     16,554건 (37.7%)   █████████████████████
  500만~3000만     8,094건 (18.4%)   ██████████
  3000만~1억       2,485건 ( 5.7%)   ███
  1억~10억           875건 ( 2.0%)   █
  10억+               30건 ( 0.1%)   ▏

  → 73.8%가 500만 원 이하
  → 상위 2.1%가 1억 원 이상
  → 극단적 우편향 분포 → log 변환 필수
```

**타입별 가격 수준이 완전히 다름**:

| 타입 | 중앙값 | 평균 | 구성비 |
|------|--------|------|--------|
| 위클리 | 100만 | 151만 | 65.1% |
| 프리미엄 | 550만 | 839만 | 19.3% |
| 메이저 | 2,800만 | 6,658만 | 15.6% |

→ **타입이 사실상 가격 세그먼트를 나눔** — 중요한 피처

### 1.3 결측률 현황

```
피처별 결측률:
  ██                                     0.0%   추정가(최저/최고), 낙찰가, 타입, 회차, Lot
  █████                                  6.2%   재료
  ██████                                 9.2%   작가
  ████████████████                      31.5%   제작연도 ← 가장 큰 갭
  ████                                   2.7%   크기
```

### 1.4 추정가 대비 낙찰가 비율 — 핵심 발견

```
추정가 중앙값 대비 낙찰가 비율:
  중앙값:    0.600 (추정가의 60% 수준에서 낙찰)
  추정가 이상 낙찰: 13.3%
  추정가 50% 이하 낙찰: 30.2%

  → K-Auction 데이터는 추정가 대비 할인 낙찰이 지배적
  → 추정가는 "상한 앵커"로 작동 (서양 경매소와 다른 패턴)
  → 모델이 이 할인 패턴을 학습하는 것이 핵심
```

### 1.5 작가 데이터 분포

```
작가별 출품 건수:
  1건만 있는 작가:   1,511명 (45.9%)   ← Cold Start 문제
  2~5건:             914명 (27.8%)
  6~20건:            486명 (14.8%)
  21~100건:          294명 ( 8.9%)
  100건 초과:          84명 ( 2.6%)   ← 이 84명이 전체의 상당 부분

  → 45.9%가 1건뿐 — 작가 통계 피처가 의미 없는 그룹
  → Cold Start 전략이 반드시 필요
```

---

## 2. 구현 전략: 4개 스프린트

### Sprint 0: 데이터 전처리 파이프라인 (1주)

모든 모델의 기반이 되는 피처 엔지니어링 파이프라인을 먼저 구축한다.

```
목표: 43,866건 raw CSV → 학습 가능한 피처 테이블 변환
산출물: preprocessed_features.parquet

[Step 0-1] 크기 파싱
─────────────────────────────────────
  입력: "81×116cm", "31×13×22(h)cm", "高48", "diameter 6.5cm"

  파싱 결과:
    2D 성공:   39,004건 (88.9%)   → height, width 추출
    3D 성공:    3,141건 ( 7.2%)   → 첫 두 값 사용
    원형:         534건 ( 1.2%)   → diameter로 정사각 가정
    결측:       1,172건 ( 2.7%)   → 조건부 대체
    파싱실패:       15건 ( 0.0%)   → 수동 검토 후 결측 처리

  파생 피처:
    height_cm     FLOAT   높이
    width_cm      FLOAT   너비
    surface_area  FLOAT   height × width
    aspect_ratio  FLOAT   height / width
    is_3d         BOOL    3D 작품 여부

  결측 대체 (1,172 + 15건):
    1순위: 동일 작가 + 동일 매체 중앙값
    2순위: 동일 매체 전체 중앙값
    3순위: 전체 중앙값 (약 2,800 cm²)
    + is_size_imputed = 1 플래그


[Step 0-2] 재료 파싱
─────────────────────────────────────
  현재 고유값: 2,154개 → 아래 분류 체계로 정규화

  medium_category (10개):
    유화         9,748건   "유채", "오일" 포함
    수묵         8,637건   "수묵", "먹" 포함
    판화         6,626건   "석판화", "실크스크린", "오프셋" 포함
    아크릴       4,385건   "아크릴" 포함
    혼합재료     2,665건   "혼합", "미디어" 포함
    채색           865건   "채색", "담채" 포함
    조각/공예      724건   "Bronze", "도자", "Ceramic" 포함
    사진/디지털    515건   "사진", "C-print" 포함
    기타         7,003건   위에 해당 없는 경우
    unknown     2,698건   재료 결측

  support_category (6개):
    캔버스      13,639건
    종이        12,568건
    기타        11,539건
    unknown     2,698건
    목재         1,899건
    비단           994건
    패널           529건


[Step 0-3] 제작연도 파싱
─────────────────────────────────────
  파싱 성공: 26,953건 (61.4%)  → 4자리 연도 추출
  결측:     16,913건 (38.6%)

  파생 피처 (성공 건만):
    year_created   INT     제작 연도
    work_age       INT     경매연도 - 제작연도 (작품 나이)

  결측 대체:
    → NaN 유지 + is_year_missing = 1 플래그
    → CatBoost가 NaN을 자동 처리하도록 위임
    → 제작연도 결측률이 38.6%로 높아, 무리한 대체보다 결측 자체를 정보로 활용


[Step 0-4] 추정가 파생 피처
─────────────────────────────────────
  결측률: 0% → 모든 건에서 사용 가능 ✅

  estimate_low      INT     추정가 최저 (원본)
  estimate_high     INT     추정가 최고 (원본)
  estimate_mid      FLOAT   (최저 + 최고) / 2
  estimate_range    FLOAT   최고 - 최저
  estimate_ratio    FLOAT   최고 / 최저 (불확실성 지표)
  ln_estimate_mid   FLOAT   log(estimate_mid) — 핵심 피처

  ⚠️ 주의: 추정가(최저) = 0인 건이 존재할 수 있음
  → estimate_ratio 계산 시 0 나누기 방지 필요
  → 최저 = 0인 경우 estimate_ratio = NaN 처리


[Step 0-5] 작가 통계 조인
─────────────────────────────────────
  artists 테이블 조인 키: works.작가 = artists.작가명

  조인 성공 예상: 39,840건 (작가 결측 9.2% 제외 후 대부분)
  조인 실패: 39건 (works에만 있는 작가) → Cold Start 처리

  추가 피처:
    artist_total_sold      INT     총 낙찰 건수
    artist_total_amount    INT     총 낙찰액
    artist_max_price       INT     최고 낙찰가
    artist_avg_price       INT     평균 낙찰가
    artist_sell_rate       FLOAT   낙찰률
    artist_price_tier      CAT     가격 등급 (하위/중하/중상/상위/최상)

  Cold Start (작가 결측 또는 신규 작가):
    → 동일 타입 + 동일 추정가 구간의 작가 평균으로 대체
    → is_new_artist = 1 플래그


[Step 0-6] 시간/경매 피처
─────────────────────────────────────
  ⚠️ 현재 데이터에 auction_date가 없음
  → "회차(session number)"가 시간 순서의 proxy

  피처:
    auction_type     CAT    위클리/프리미엄/메이저
    session_number   INT    회차 (시간 순서 proxy)
    lot_number       INT    LOT 번호 (출품 순서)
    bid_count        INT    입찰 수 (사후 정보 — 학습에만 사용, 예측 시 불가)

  ⚠️ bid_count 처리:
    학습 시: 사용 가능 (과거 데이터이므로)
    예측 시: 사용 불가 (아직 입찰이 시작되지 않음)
    → 두 가지 모델 버전 유지:
       model_with_bid: 사후 분석용 (입찰 수 포함)
       model_no_bid:   사전 예측용 (입찰 수 제외) ← 메인
```

### Sprint 1: CatBoost Baseline (1주)

```
목표: 첫 번째 예측 모델 구축 및 MAPE 기준선 확보
산출물: baseline_catboost_v1.cbm, evaluation_report_v1.html

[Step 1-1] 데이터 분할
─────────────────────────────────────
  시간축: "회차"를 기준으로 분할

  위클리:   Train: 회차 1~380 / Valid: 381~430 / Test: 431~486
  프리미엄: Train: 회차 55~180 / Valid: 181~200 / Test: 201~224
  메이저:   Train: 회차 98~160 / Valid: 161~175 / Test: 176~195

  또는 전체 통합 후 회차 기반 정렬 → 상위 70% Train / 15% Valid / 15% Test

  ❌ 금지: random shuffle split (시계열 누수)


[Step 1-2] 피처 목록 (Phase 1 — 22개)
─────────────────────────────────────
  범주형 (CatBoost 자동 인코딩):
    1.  artist_name           작가명 (3,289 카테고리)
    2.  medium_category       매체 (10 카테고리)
    3.  support_category      지지체 (6 카테고리)
    4.  auction_type          경매 타입 (3: 위클리/프리미엄/메이저)
    5.  is_3d                 3D 작품 여부
    6.  is_untitled           제목에 "무제" 또는 "Untitled" 포함

  수치형:
    7.  ln_estimate_mid       log(추정가 중앙값) ★ 핵심
    8.  estimate_ratio        추정가 최고/최저 비율
    9.  estimate_range        추정가 범위 (절대값)
    10. height_cm             높이
    11. width_cm              너비
    12. surface_area          면적
    13. aspect_ratio          종횡비
    14. lot_number            LOT 번호
    15. session_number        회차 (시간 proxy)
    16. artist_total_sold     작가 총 낙찰 건수
    17. artist_avg_price      작가 평균 낙찰가
    18. artist_max_price      작가 최고 낙찰가
    19. artist_sell_rate      작가 낙찰률
    20. is_size_imputed       크기 결측 대체 여부
    21. is_year_missing       제작연도 결측 여부
    22. is_new_artist         신규 작가 여부

  타겟:
    y = ln(낙찰가)


[Step 1-3] CatBoost 학습 설정
─────────────────────────────────────
  from catboost import CatBoostRegressor

  model = CatBoostRegressor(
      iterations=3000,
      depth=8,
      learning_rate=0.05,
      l2_leaf_reg=5,
      loss_function='RMSE',         # log price이므로 RMSE가 적합
      cat_features=[0,1,2,3,4,5],   # 범주형 인덱스
      random_seed=42,
      verbose=100,
      early_stopping_rounds=200,
      task_type='CPU',               # GPU 있으면 'GPU'
  )

  model.fit(
      X_train, y_train,
      eval_set=(X_valid, y_valid),
      use_best_model=True,
  )


[Step 1-4] 평가
─────────────────────────────────────
  # 예측 → 원래 스케일 복원
  y_pred_log = model.predict(X_test)
  y_pred = np.exp(y_pred_log)
  y_true = np.exp(y_test)

  # MAPE 계산
  mape = np.mean(np.abs(y_true - y_pred) / y_true) * 100

  # 가격대별 MAPE (세그먼트별 성능 파악)
  for tier in ['<100만', '100만~500만', '500만~3000만', ...]:
      mask = price_tier == tier
      mape_tier = np.mean(np.abs(y_true[mask] - y_pred[mask]) / y_true[mask]) * 100

  # Feature Importance (CatBoost 내장)
  importance = model.get_feature_importance()

  # SHAP 분석 (선택)
  import shap
  explainer = shap.TreeExplainer(model)
  shap_values = explainer.shap_values(X_test)

  기대 결과:
    전체 MAPE: 35~45% (추정가가 강력한 앵커이므로)
    메이저 MAPE: 30~40% (데이터 품질 좋음)
    위클리 MAPE: 40~50% (저가, 변동성 높음)
```

### Sprint 2: 피처 고도화 + 앙상블 (2주)

```
목표: MAPE를 Baseline 대비 5~10%p 개선
산출물: ensemble_v1.pkl, feature_importance_comparison.html

[Step 2-1] 고급 파생 피처 추가 (13개)
─────────────────────────────────────
  ⚠️ 핵심: 시계열 누수 방지 — 각 건의 "회차" 이전 데이터만 사용

  작가 동적 피처 (회차 기준 rolling):
    23. artist_recent_avg_3     해당 회차 이전 최근 3건 낙찰가 평균
    24. artist_recent_avg_10    해당 회차 이전 최근 10건 낙찰가 평균
    25. artist_price_trend      최근 10건 선형 회귀 기울기
    26. artist_price_volatility 최근 20건 낙찰가 표준편차
    27. artist_days_since_last  이전 낙찰 대비 회차 간격

  추정가 대비 과거 실적:
    28. artist_premium_avg      해당 작가의 추정가 대비 낙찰가 비율 이력 평균
    29. artist_premium_std      상동 표준편차

  시장 컨텍스트 (회차 기준 rolling):
    30. market_avg_premium_10   최근 10 회차 전체 추정가 대비 낙찰가 비율
    31. market_avg_price_10     최근 10 회차 전체 평균 낙찰가
    32. same_medium_avg_10      동일 매체 최근 10 회차 평균 낙찰가

  가격대 피처:
    33. estimate_tier           추정가 구간 (5단계)
    34. artist_price_rank       작가 가격 순위 백분위

  제작연도 파생 (결측 아닌 경우만):
    35. work_age                경매 시점 - 제작연도

  구현 주의사항:
    ─────────────────────────────────
    # 시계열 누수 방지 구현 예시
    works_sorted = works.sort_values('session_number')

    for idx, row in works_sorted.iterrows():
        past = works_sorted[
            (works_sorted['session_number'] < row['session_number']) &
            (works_sorted['작가'] == row['작가'])
        ]
        artist_recent_avg_3 = past.tail(3)['낙찰가'].mean()
        # ... (vectorized 구현 권장)


[Step 2-2] Stacking 앙상블
─────────────────────────────────────
  Base Models:
    1. CatBoost    (범주형 강점)
    2. LightGBM    (속도, leaf-wise)
    3. XGBoost     (정규화 강점)

  Meta-Learner: Ridge Regression

  학습 과정:
    1. 5-Fold Time Series CV로 각 Base Model의 OOF 예측값 생성
    2. OOF 예측값을 피처로 Meta-Learner 학습
    3. Test 데이터에 대해 각 Base Model 예측 → Meta-Learner 최종 예측

  ┌────────────────────────────────────────────────┐
  │  Fold 1: Train[──────] Valid[──]               │
  │  Fold 2: Train[────────] Valid[──]             │
  │  Fold 3: Train[──────────] Valid[──]           │
  │  Fold 4: Train[────────────] Valid[──]         │
  │  Fold 5: Train[──────────────] Valid[──]       │
  │                                                │
  │  각 Fold의 Valid 예측을 합쳐서 OOF 예측값 구성    │
  │  → OOF를 입력으로 Meta-Learner 학습              │
  └────────────────────────────────────────────────┘


[Step 2-3] 하이퍼파라미터 최적화
─────────────────────────────────────
  도구: Optuna (100 trials)

  CatBoost:
    iterations:      [1000, 8000]
    depth:           [4, 10]
    learning_rate:   [0.01, 0.2]
    l2_leaf_reg:     [1, 10]

  LightGBM:
    n_estimators:    [1000, 8000]
    num_leaves:      [31, 255]
    learning_rate:   [0.01, 0.2]
    min_child_samples: [5, 50]

  XGBoost:
    n_estimators:    [1000, 8000]
    max_depth:       [4, 10]
    learning_rate:   [0.01, 0.2]
    reg_alpha:       [0, 10]
    reg_lambda:      [0, 10]
```

### Sprint 3: 고도화 및 서비스화 (2주)

```
[Step 3-1] 타입별 전문 모델 vs 통합 모델 비교
─────────────────────────────────────
  가설: 위클리/프리미엄/메이저의 가격 패턴이 크게 다르므로
        세그먼트별 전문 모델이 더 나을 수 있다

  실험:
    A. 통합 모델 (전체 43,866건)
    B. 분리 모델 (위클리/프리미엄/메이저 각각)
    C. 하이브리드 (통합 모델 + 타입별 잔차 보정)

  → MAPE 비교 후 최적 전략 선택


[Step 3-2] Ablation Study 실행
─────────────────────────────────────
  각 피처 그룹 제거 후 MAPE 변화 측정:

  실험 1: 추정가 제거        → Δ MAPE = ?
  실험 2: 작가 통계 제거     → Δ MAPE = ?
  실험 3: 크기 피처 제거     → Δ MAPE = ?
  실험 4: 재료 피처 제거     → Δ MAPE = ?
  실험 5: 시장 컨텍스트 제거 → Δ MAPE = ?
  실험 6: 결측 플래그 제거   → Δ MAPE = ?

  → 결측 시 quality_score 가중치 실증적 보정
  → 데이터 수집 우선순위 재조정


[Step 3-3] 예측 API 구축
─────────────────────────────────────
  기술 스택:
    · FastAPI (비동기 API 서버)
    · CatBoost ONNX export (추론 최적화)
    · Redis (작가 통계 캐시)

  엔드포인트:
    POST /api/v1/predict_price
    POST /api/v1/batch_predict
    GET  /api/v1/model_info
    GET  /api/v1/feature_importance


[Step 3-4] 모니터링 및 리트레이닝
─────────────────────────────────────
  · 새 경매 결과 입수 시 MAPE 모니터링
  · MAPE가 기준선 대비 5%p 이상 악화 시 리트레이닝 트리거
  · 주기: 월 1회 정기 리트레이닝 + 이벤트 기반
```

---

## 3. 데이터별 구체적 결측 처리 매뉴얼

이 데이터에서 실제로 발생하는 결측 시나리오와 처리 방법이다.

### 3.1 작가명 결측 (9.2%, 4,026건)

```
현황: "작자미상", 빈값, NaN 등

처리 전략:
  ┌─────────────────────────────────────────────────────┐
  │  "작자미상" 또는 빈값                                  │
  │  → artist_name = "__UNKNOWN__" (단일 카테고리)         │
  │  → 작가 통계 피처: 전체 "작자미상" 그룹의 집계값 사용     │
  │  → is_new_artist = 1                                 │
  │                                                      │
  │  장점: "작자미상" 그룹의 가격 패턴 자체를 학습           │
  │  (고미술/골동품에서 작자미상은 특정 가격대를 형성)         │
  └─────────────────────────────────────────────────────┘
```

### 3.2 제작연도 결측 (38.6%, 16,913건)

```
현황: 고미술/공예품에서 특히 높은 결측률

처리 전략:
  ┌─────────────────────────────────────────────────────┐
  │  Option A (권장): NaN 유지 + 결측 플래그               │
  │  → year_created = NaN                                │
  │  → is_year_missing = 1                               │
  │  → work_age = NaN                                    │
  │  → CatBoost가 NaN을 최적 분기에 자동 할당              │
  │                                                      │
  │  근거: 결측률 38.6%는 무리한 대체보다                   │
  │        "결측 자체가 정보(고미술/공예품 시그널)"가         │
  │        더 유용할 수 있음                               │
  │                                                      │
  │  Option B: 조건부 대체 (실험적)                         │
  │  → 동일 작가 작품 제작연도 중앙값                       │
  │  → 동일 매체 + 유사 가격대 제작연도 중앙값               │
  │  → 두 Option의 MAPE 비교 후 선택                      │
  └─────────────────────────────────────────────────────┘
```

### 3.3 재료 결측 (6.2%, 2,698건)

```
처리 전략:
  → medium_category = "unknown"
  → support_category = "unknown"
  → CatBoost가 "unknown" 카테고리의 가격 패턴을 학습
```

### 3.4 크기 결측 (2.7%, 1,172건)

```
처리 전략:
  1순위: 동일 작가 + 동일 매체 작품 면적 중앙값
  2순위: 동일 매체 전체 면적 중앙값
  3순위: 전체 중앙값 (~2,800 cm²)
  + is_size_imputed = 1

  구현 (pandas):
    artist_medium_median = works.groupby(['작가','medium_category'])['surface_area'].median()
    medium_median = works.groupby('medium_category')['surface_area'].median()
    global_median = works['surface_area'].median()
```

### 3.5 Cold Start 작가 (1,511명, 1건만 보유)

```
문제: 작가 통계 피처가 해당 건 자체의 데이터뿐 → 누수 위험

처리 전략:
  학습 시:
    → 시계열 기준으로 해당 건 이전 데이터가 없으면
    → 작가 통계 = 동일 estimate_tier + auction_type 그룹 평균
    → is_new_artist = 1

  예측 시 (완전 신규 작가):
    → [LEGACY — 실제 구현은 is_new_artist 불리언 기반으로 변경됨]
    → 작가 통계 = 동일 estimate_tier + auction_type 그룹 평균 (cold_start fallback)
    → 모델은 주로 추정가, 크기, 재료에 의존하여 예측
    → confidence_grade = "D" (예측 불가) 표시
```

---

## 4. 핵심 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| **회차=시간이 아님** — 회차 번호가 정확한 시간 순서를 보장하지 않을 수 있음 | 시계열 분할 오류 | auction_date 필드 확보를 최우선으로 추진. 없으면 회차로 근사 |
| **유찰 데이터 부재** — 현재 100% 낙찰 건만 존재 | 선택 편향(낙찰된 것만 학습) | 유찰 데이터 수집 시 Heckman 보정 모델 도입 검토 |
| **추정가 지배력** — 추정가가 너무 강력해서 다른 피처 학습 방해 | 모델이 "추정가 복사기"가 됨 | 추정가 제외 모델도 병행 학습하여 다른 피처의 독립 기여도 확인 |
| **저가 작품 MAPE 과대** — 100만 원 이하 작품에서 MAPE가 100% 넘을 수 있음 | 전체 MAPE 왜곡 | 가격대별 MAPE 분리 보고, MdAPE(중앙값) 병행 사용 |
| **데이터 갱신 주기** — 새 경매 결과 반영 속도 | 모델 노후화 | 월간 리트레이닝 파이프라인 구축 |

---

## 5. 최종 산출물 체크리스트

```
Sprint 0:
  □ dimension_parser.py    — 크기 파싱 모듈
  □ medium_parser.py       — 재료 파싱 모듈
  □ feature_pipeline.py    — 전체 피처 생성 파이프라인
  □ preprocessed_features.parquet — 전처리 완료 데이터

Sprint 1:
  □ baseline_catboost_v1.cbm — 베이스라인 모델
  □ evaluation_report_v1.html — 평가 리포트 (MAPE, 분포, SHAP)
  □ feature_importance_v1.json — 피처 기여도

Sprint 2:
  □ ensemble_v1.pkl — 앙상블 모델
  □ optuna_study.db — 하이퍼파라미터 튜닝 결과
  □ ablation_results.json — Ablation Study 결과

Sprint 3:
  □ api_server.py — FastAPI 예측 서버
  □ model_card.md — 모델 카드 (성능, 한계, 사용법)
  □ monitoring_dashboard.html — 모니터링 대시보드
```

---

*본 문서는 K-Auction 실제 데이터 분석 결과를 기반으로 작성되었으며, 각 Sprint의 구현 착수 시점에 데이터 상태를 재확인할 것을 권장한다.*
