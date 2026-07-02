# Warm/Cold 최종 모델 운영 정리

- 작성일: 2026-06-22
- 목적: 현재 운영 후보인 Warm 모델과 Cold 모델을 실제 서비스에 올리기 위해 필요한 모델 방식, 입력 조건, 번들 구조, 검증 기준, 남은 작업을 같은 기준으로 정리한다.
- 기준 버전 표기: official 0.1v
- Warm 기준 산출물: `models/track6/warm_lite_unified_current_joblib_v0.1_candidate`
- Cold 기준안: `resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05`
- Cold 상세 문서: `docs/track6/experiments/cold_official_v0_1_k80_operational_model_report.md`

## 1. 운영 결론

| 구분 | 현재 판단 | 운영 상태 | 핵심 이유 |
|---|---|---|---|
| Warm | 운영 후보로 가장 앞서 있음 | joblib-only 독립 번들 후보 | DB, 외부 CSV lookup, fixed replay CSV 없이 `runtime_store.joblib` 하나와 predictor로 예측 가능 |
| Cold | k80 보수적 운영 기준안으로 확정 | strict Cold 유사 이웃 잔차 라우터 기준 | artist_key, 동일 작가 가격 이력, 검색 lookup 없이 validation 안정성이 가장 좋은 k80 후보를 기준으로 문서화 |

현재 Warm은 운영 배포 형식이 비교적 명확하다. 모델 객체, 작가 registry, alias, 같은 작가 학습 이력, feature 생성 규칙이 `runtime_store.joblib` 안에 들어 있고, 예측 코드는 이 파일만 읽도록 정리되어 있다.

Cold는 기존 `cold_prediction_v0.5_operational` 대신 `k80 보수적 운영` 기준안을 운영 설명 기준으로 둔다. 이 기준안은 `artist_key`, 동일 작가 가격 이력, 검색 캐시, 외부 live 검색, artist_key 기반 lookup 후처리를 쓰지 않는 strict Cold 후보이며, 세부 로직과 수치는 `cold_official_v0_1_k80_operational_model_report.md`를 기준으로 한다. 아직 Warm처럼 독립 `runtime_store.joblib` 번들로 잠긴 상태는 아니므로, 실제 API 배포 전에는 bundle 생성과 parity 검증이 필요하다.

## 2. Warm 최종 모델 운영 정리

### 2.1 모델 역할

Warm은 같은 작가의 과거 가격 이력을 사용할 수 있는 경우의 가격 예측 모델이다. 사용자가 입력한 작가명 또는 내부 artist_key를 frozen registry/alias 기준으로 확인하고, 같은 작가의 학습 이력이 존재할 때만 Warm 예측을 수행한다.

현재 운영 후보는 기존의 복잡한 Warm/Warm-lite 분기를 단순화한 `Warm-lite unified current joblib-only` 모델이다. 이 모델은 같은 작가 가격 이력 통계와 작품 피처를 함께 사용해 기준가격을 만들고, LightGBM Huber residual 보정으로 최종 로그가격을 산출한다.

### 2.2 운영 입력

| 입력 | 필수 여부 | 사용 목적 |
|---|---|---|
| `artist_key` 또는 작가명 | 필수 | 같은 작가 학습 이력 조회 및 Warm 가능 여부 판단 |
| `width_cm` | 필수 | 면적, 로그면적, 크기 구간 생성 |
| `height_cm` | 필수 | 면적, 로그면적, 크기 구간 생성 |
| `depth_cm` | 선택 | 입체 작품 여부 판단. 없으면 0으로 처리 |
| `medium_category` | 필수 | 매체/재료 조건, 유사 이력 통계 매칭 |
| `support_category` | 필수 | 지지체 조건, 유사 이력 통계 매칭 |

Warm 예측은 호당 가격으로 직접 계산하지 않는다. cm 단위 크기와 작품 조건, 같은 작가 가격 이력을 바탕으로 로그가격을 예측한 뒤 `exp()`로 원 가격을 산출한다.

### 2.3 실행 단계

```text
[사용자 입력]
  - 작가명 또는 artist_key
  - 가로/세로/깊이 cm
  - 매체, 지지체
        |
        v
[작가 확인]
  - artist_key 직접 입력 확인
  - alias 테이블 매칭
  - registry 한글명/영문명 매칭
  - 동명이인 또는 학습 이력 없음이면 Warm 차단
        |
        v
[작품 피처 생성]
  - area_cm2
  - log_area
  - aspect_ratio
  - has_depth
  - is_3d_candidate
  - size_bucket, shape_bucket
  - medium_support_bucket
        |
        v
[같은 작가 가격 이력 통계 생성]
  - 같은 작가 + 매체/지지체 + 크기 구간
  - 없으면 같은 작가 + 크기 구간
  - 없으면 같은 작가 전체
  - median, q25, q75, IQR, 면적단가 통계, 표본 수 생성
        |
        v
[LightGBM Quantile 기준가격 계산]
  - full 피처 q10/q50/q90 예측
  - lean 피처 q50 예측
  - full q50과 lean q50 평균을 기준 로그가격으로 사용
        |
        v
[LightGBM Huber residual 보정]
  - 기준 로그가격에서 남은 오차를 예측
  - 0.50 * residual을 -0.10~+0.10 log 범위로 제한
        |
        v
[seed 평균]
  - 3개 seed 모델 결과 평균
        |
        v
[최종 Warm 가격]
  - 최종 로그가격 = 기준 로그가격 + 제한된 residual 보정
  - 최종 가격 = exp(최종 로그가격)
```

### 2.4 사용 피처

| 피처 그룹 | 예시 | 의미 |
|---|---|---|
| 작품 크기 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` | 작품 물리 크기와 형태 |
| 작품 조건 | `medium_category`, `support_category`, `has_depth`, `is_3d_candidate` | 매체, 지지체, 입체 여부 |
| 버킷 | `size_bucket`, `shape_bucket`, `medium_support_bucket` | 학습 당시 고정한 구간화 기준 |
| 같은 작가 가격 통계 | `grp_log_price_median`, `grp_log_price_q25`, `grp_log_price_q75`, `grp_log_price_iqr` | 같은 작가 과거 가격 분포 |
| 같은 작가 면적단가 통계 | `grp_unit_area_median`, `grp_unit_area_iqr` | 크기를 감안한 같은 작가 가격 수준 |
| 통계 신뢰 보조 | `grp_n_log`, `grp_match_level` | 참고한 이력 수와 비교군 매칭 단계 |
| Quantile 출력 | `lgbq_full_q10`, `lgbq_full_q50`, `lgbq_full_q90`, `lgbq_lean_q50` | 모델이 예측한 가격 분포와 기준가격 |
| residual 출력 | `lgb_huber_residual_log`, `current_residual_correction_log` | 기준가격 위에 더하는 제한된 보정값 |

### 2.5 운영 번들 구조

```text
models/track6/warm_lite_unified_current_joblib_v0.1_candidate/
  artifacts/
    runtime_store.joblib
  config/
    warm_lite_unified_current_joblib_policy_v0_1.json
  predict/
    predict_warm_lite_unified_current_joblib_v0_1.py
  test_data/
    track6_test_warm.csv
  test_outputs/
    fixed_test/
      summary.json
      joblib_predictions.csv
      joblib_predictions_with_diagnostics.csv
  manifest.json
  README.md
```

`runtime_store.joblib` 안에는 아래 내용이 함께 들어 있다.

| 내용 | 현재 수량 또는 상태 |
|---|---:|
| 작가 registry | 1,773 rows |
| 작가 alias | 3,600 rows |
| 같은 작가 학습 이력 | 26,914 rows |
| 학습 이력 작가 수 | 1,773 artists |
| seed 수 | 3 |
| feature 생성 규칙 내장 | true |

### 2.6 Warm 성능 기준

| 평가셋 | n | MdAPE | MAPE | p95 APE | RMSE log | 비고 |
|---|---:|---:|---:|---:|---:|---|
| Warm fixed test | 607 | 0.086970 | 0.223682 | 0.820366 | 0.382823 | joblib-only 번들 실행 결과 |

이 607건은 전체 운영 입력이 아니라, 같은 작가 학습 이력을 사용할 수 있는 Warm 평가셋이다. 따라서 Cold와 직접 난이도 비교를 하면 안 되고, Warm 경로 안에서의 운영 성능 기준으로 사용한다.

### 2.7 Warm 운영 체크리스트

| 항목 | 상태 | 설명 |
|---|---|---|
| DB 없이 실행 | 완료 | SQLite DB를 읽지 않음 |
| 외부 CSV lookup 없이 실행 | 완료 | CSV history/lookup 파일을 읽지 않음 |
| fixed replay CSV 없이 실행 | 완료 | `fixed_replay_feature_store.csv` 미사용 |
| feature 생성 규칙 번들 내장 | 완료 | size/shape bucket 기준을 `runtime_store.joblib`에 포함 |
| 작가명 alias/동명이인 처리 | 완료 | predictor 안에서 작가 매칭 및 검수 필요 상태 반환 |
| 학습 이력 row id 중복 점검 | 완료 | 최신 joblib store 기준 중복 없음 |
| API 연결 | 필요 | 현재 predictor를 서비스 API adapter로 연결하고 parity 검증 필요 |
| 모니터링 | 필요 | 예측 가격, qwidth, residual 보정량, 작가 매칭 상태 저장 필요 |

## 3. Cold 최종 모델 운영 정리

### 3.1 모델 역할

Cold는 같은 작가 가격 이력을 직접 사용할 수 없는 경우의 가격 예측 모델이다. Warm과 달리 특정 작가의 과거 가격을 기준가로 삼지 않는다. 대신 작품 크기, 매체, 지지체, 비작가 그룹 가격 통계, Quantile 예측 구간을 이용해 가격을 추정한다.

현재 Cold 운영 설명 기준은 `k80 보수적 운영` 후보이다. 이 모델은 base Cold 예측 위에 유사 작가 메타 이웃 80건의 out-of-fold 잔차 중앙값을 이용한 보정 후보를 만들고, 하향 보정 신호가 충분할 때만 보정 후보를 선택한다. 검색 피처 없이 실행 가능했던 v0.5는 이전 후보로 보관하고, 현재 운영 설명과 후속 번들화 기준은 k80 기준안으로 둔다.

### 3.2 운영 입력

| 입력 | 필수 여부 | 사용 목적 |
|---|---|---|
| `width_cm` | 필수 | 면적, 로그면적, 크기 구간 생성 |
| `height_cm` | 필수 | 면적, 로그면적, 크기 구간 생성 |
| `depth_cm` | 선택 | 입체 작품 여부 판단 |
| `area_cm2` | 선택 | 없으면 `width_cm * height_cm`로 계산 |
| `log_area` | 선택 | 없으면 면적에서 계산 |
| `aspect_ratio` | 선택 | 없으면 가로/세로에서 계산 |
| `medium_category` | 필수 | 매체별 가격 차이 반영 |
| `support_category` | 필수 | 지지체별 가격 차이 반영 |
| `size_bucket` | 실행 방식에 따라 선택 | 운영 predictor가 직접 생성하거나 입력에서 받음 |
| `medium_support_bucket` | 실행 방식에 따라 선택 | 운영 predictor가 직접 생성하거나 입력에서 받음 |

Cold 운영 원칙은 `예측 대상 작가의 artist_key 매칭을 필요로 하지 않는 것`이다. Cold는 원래 같은 작가 가격 이력을 확정해서 쓸 수 없을 때 사용하는 경로이므로, 운영 입력에서 artist_key가 매칭되어야만 가격이 나오는 구조라면 Cold 로직으로 성립하지 않는다.

따라서 Cold 가격 산식에서는 `입력 작가의 artist_key로 같은 작가 가격 이력을 lookup`하면 안 된다. k80 보수적 운영 기준안의 유사 이웃과 보정 라우터도 입력 작가의 artist_key가 아니라 작가 메타/작품 조건/보정 신호를 기준으로 동작한다. 즉 학습 데이터 안에 artist_key가 존재하더라도, 그것은 train/test 분리와 데이터 관리용 식별자일 뿐이며, Cold 사용 단계에서 입력 작가를 특정 artist_key로 매칭해 가격 이력을 가져오는 용도가 아니다.

작가 메타를 쓰는 별도 Cold 모델을 만들 경우에도 기준은 같다. 사용자가 입력 가능하거나 운영 DB에서 검수된 작가 정보는 사용할 수 있지만, 그 정보가 hidden artist_key 가격 이력 lookup으로 이어지면 안 된다. 예를 들어 사용자가 입력한 출생연도, 국적, 학력, 소속 갤러리, 활동 지역 같은 메타로 유사 그룹을 만들거나 모델 피처로 쓰는 것은 가능하다. 반면 입력 작가명을 내부 artist_key에 매칭한 뒤 그 artist_key의 과거 가격 통계를 가져오는 것은 Warm 방식이므로 Cold에서는 금지한다.

### 3.3 실행 단계

```text
[Cold 입력 작품]
  - 가로/세로/깊이 cm
  - 매체, 지지체
  - 같은 작가 가격 이력은 사용하지 않음
        |
        v
[Cold 기본 피처 생성]
  - area_cm2
  - log_area
  - aspect_ratio
  - has_depth
  - is_3d_candidate
  - size_bucket
  - support_size_bucket
  - medium_support_bucket
        |
        v
[LightGBM Quantile 예측]
  - q10 로그가격
  - q40 로그가격
  - q50 로그가격
  - q90 로그가격
  - 5개 seed 평균
        |
        v
[비작가 그룹 통계 생성]
  - 입력 작가의 artist_key 매칭 없이 계산
  - 매체/지지체/크기 조건별 과거 가격 통계
  - 조건이 희소하면 더 넓은 그룹으로 fallback
  - 입력 작가의 artist_key별 가격 이력 lookup은 사용하지 않음
        |
        v
[Huber 그룹통계 예측]
  - 작품 피처 + 비작가 그룹 통계
  - 6개 Huber 구성 평균
        |
        v
[대표 Cold 로그가격]
  - 0.70 * LightGBM q50
  - 0.30 * Huber 그룹통계 예측
        |
        v
[p95 방어 조건 판단]
  - q90 - q10이 임계값 이상인지 확인
  - 대표 로그가격이 q40보다 충분히 높은지 확인
        |
        v
[방어 Cold 로그가격]
  - 조건 미충족: 대표 로그가격 유지
  - 조건 충족: 0.50 * 대표 로그가격 + 0.50 * q40 로그가격
        |
        v
[최종 Cold 가격]
  - 최종 가격 = exp(방어 Cold 로그가격)
```

### 3.4 사용 피처

| 피처 그룹 | 예시 | 의미 |
|---|---|---|
| 작품 크기 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` | 물리 크기와 형태 |
| 작품 조건 | `medium_category`, `support_category`, `has_depth`, `is_3d_candidate` | 매체, 지지체, 입체 여부 |
| 버킷 | `size_bucket`, `support_size_bucket`, `medium_support_bucket` | 비작가 그룹 통계와 Quantile 모델 입력 |
| 비작가 그룹 통계 | `grp_log_price_median`, `grp_log_price_q25`, `grp_log_price_q75`, `grp_log_price_iqr` | 같은 작가가 아니라 같은 조건 그룹의 가격 분포 |
| 비작가 면적단가 통계 | `grp_unit_area_median`, `grp_unit_area_iqr` | 크기를 감안한 조건별 가격 수준 |
| 통계 보조 | `grp_n_log`, `grp_match_level`, `grp_price_proxy` | 그룹 표본 수, fallback 단계, 면적 기반 가격 proxy |
| Quantile 출력 | `q10_pred_log`, `q40_pred_log`, `q50_pred_log`, `q90_pred_log` | 낮은/보수/중앙/높은 로그가격 |
| 방어 판단 | `qwidth_log`, `representative_pred_log - q40_pred_log` | 큰 오차 위험이 높은지 판단 |

### 3.5 Cold 성능 기준

| 후보 | 평가셋 | n | MdAPE | MAPE | p95 APE | APE > 5 | 해석 |
|---|---|---:|---:|---:|---:|---:|---|
| base Cold similarity | validation | 2,575 | 0.424537 | 0.606746 | 1.808312 | 10 | 보정 전 기준 |
| k80 보수적 운영 | validation | 2,575 | 0.404411 | 0.565875 | 1.638585 | 8 | 운영 설명 기준안 |
| base Cold similarity | test | 3,000 | 0.481850 | 0.746296 | 2.398009 | 35 | 보정 전 기준 |
| k80 보수적 운영 | test | 3,000 | 0.479052 | 0.720187 | 2.231840 | 33 | 운영 설명 기준안 |

k80 보수적 운영 후보는 validation에서 base 대비 MdAPE, MAPE, p95 APE, APE > 5가 모두 개선됐고, test에서도 MAPE와 p95 APE 및 APE > 5가 개선됐다. test 단일 수치만 보면 k40 후보가 더 좋지만, validation 선택 안정성을 기준으로 운영 설명 기준안은 k80으로 둔다.

### 3.6 Cold 운영 번들 구조

```text
models/track6/cold_k80_conservative_official_v0.1_candidate/
  artifacts/
    runtime_store.joblib
      - base Cold 모델
      - train reference pool
      - OOF residual 배열
      - 유사도 전처리기
      - feature schema
      - 라우터 정책
  config/
    cold_k80_conservative_policy_v0_1.json
  predict/
    predict_cold_k80_conservative_v0_1.py
  test_outputs/
    fixed_test/
      summary.json
      predictions.csv
```

현재 k80 기준안은 실험 산출물로 검증된 운영 기준안이며, 아직 Warm처럼 단일 `runtime_store.joblib` 방식으로 묶인 배포 번들은 아니다. 실제 운영 배포 전에는 위 구조로 재동결해야 한다.

### 3.7 Cold 운영 체크리스트

| 항목 | 현재 상태 | 운영 전 권장 조치 |
|---|---|---|
| 검색 피처 없이 실행 | 검증됨 | k80 기준안은 검색 피처와 외부 live 검색 미사용 |
| DB 없이 실행 | 부분 확인 필요 | predictor가 모델/config 외부 경로를 읽지 않는지 parity 검증 필요 |
| artist_key 가격 이력 미사용 | 검증됨 | CSIM26 run summary 기준 `uses_artist_key_lookup_postprocess=0` |
| feature 생성 규칙 내장 | 부분 | size bucket 생성 기준을 config/store에 명시적으로 동결 |
| 단일 번들 | 미완료 | Warm처럼 `runtime_store.joblib`로 재동결 |
| API adapter | 필요 | Cold input schema, output schema, error handling 확정 |
| 성능 parity | 필요 | freeze 전후 3,099 fixed test 예측 diff 0 검증 |
| 모니터링 | 필요 | qwidth, guard 적용 여부, group match level, 가격 범위 저장 |

## 4. Warm과 Cold 운영 차이

| 항목 | Warm | Cold |
|---|---|---|
| 사용 조건 | 같은 작가 가격 이력이 있음 | 같은 작가 가격 이력을 직접 쓰기 어려움 |
| 작가키 사용 | 내부 artist_key를 확정해 같은 작가 이력 조회 | 가격 산식에서 artist_key별 가격 이력 lookup 금지 |
| 기준가격 | 같은 작가 가격 통계 + 작품 피처 | 작품 피처 + 비작가 그룹 통계 + Quantile |
| 보정 | LightGBM Huber residual 보정 | q40 방어 guard |
| 출력 | 단일 가격 + q10/q50/q90 진단값 | 단일 가격 + 가격 범위 + 방어 적용 여부 |
| 현재 운영화 수준 | 높음 | 모델 후보는 있으나 운영 계약 보강 필요 |

## 5. 서비스 라우팅 권장안

```text
[사용자 입력]
        |
        v
[작가 매칭]
  - artist_key 직접 확인 또는 작가명 alias/registry 매칭
  - 동명이인/저신뢰 매칭이면 Warm 자동 사용 금지
        |
        v
[Warm 가능 여부]
  - 내부 artist_key 확정
  - 같은 작가 학습 이력 존재
  - 동명이인 검수 필요 없음
        |
        +--------------------------+
        |                          |
        v                          v
[Warm 예측]                  [Cold 예측]
  - 같은 작가 이력 사용        - 같은 작가 이력 미사용
  - joblib runtime store       - 작품 조건/비작가 그룹 통계
        |                          |
        +------------+-------------+
                     |
                     v
[결과 반환]
  - 예측 가격
  - 가격 범위 또는 진단값
  - 모델 경로
  - 작가 매칭 상태
  - 검수 필요 여부
```

운영에서 가장 중요한 기준은 `모르는 작가를 Warm으로 보내지 않는 것`이다. 작가명이 매칭되지 않거나 동명이인 위험이 있거나 같은 작가 학습 이력이 없으면 Cold로 보내야 한다. 반대로 Warm에 들어온 경우에는 모델이 같은 작가 가격 이력을 직접 쓰므로, 작가 매칭 품질이 가격 품질의 핵심 전제다.

## 6. Cold를 Warm 수준으로 운영화하기 위한 작업

Cold는 다음 순서로 정리하는 것이 좋다.

### 6.1 Cold 운영 정책 확정

| 결정 항목 | 권장안 |
|---|---|
| 기본 Cold 후보 | k80 보수적 운영 |
| 검색 피처 포함 연구 기준 | 운영 기본에서는 제외. `artist_key` 기반 search delta lookup을 포함하는 기존 연구 수치는 strict Cold 운영 기준에서는 그대로 사용 금지 |
| artist_key 사용 | 운영 입력 작가의 artist_key 매칭을 요구하지 않음. 가격 이력 lookup에는 사용 금지 |
| 작가 메타 사용 | 사용자가 입력 가능하거나 운영 DB에서 검수된 메타만 사용 |
| 결과 표시 | 가격 단일값 + 가격 범위 + 낮은 신뢰도/검수 필요 표시 |

### 6.2 Cold bundle 재동결

Warm과 같은 방향으로 아래를 하나의 bundle contract로 고정한다.

```text
cold_operational_joblib_v0.1_candidate/
  artifacts/
    runtime_store.joblib
  config/
    cold_operational_policy_v0_1.json
  predict/
    predict_cold_operational_joblib_v0_1.py
  test_data/
    track6_test_cold.csv
  test_outputs/
    fixed_test/
      summary.json
      predictions.csv
      predictions_with_diagnostics.csv
  manifest.json
  README.md
```

`runtime_store.joblib`에는 LightGBM Quantile 모델, Huber 모델, 비작가 그룹통계 ladder, global fallback, feature 생성 규칙, guard 기준을 모두 포함한다.

### 6.3 Cold parity 검증

Cold 운영 번들을 만들면 아래를 반드시 검증한다.

| 검증 | 통과 기준 |
|---|---|
| CSIM26 실험 산출값 vs 신규 joblib store predictor | validation/test 예측 로그가격 diff 0 또는 부동소수 허용오차 이내 |
| DB/CSV 차단 | 실행 로그와 코드상 외부 DB/CSV lookup 없음 |
| artist_key 차단 | 입력에 artist_key가 있어도 예측 대상 작가의 가격 이력 lookup에 사용하지 않음 |
| 성능 재현 | MdAPE 0.482170, MAPE 1.179011, p95 APE 3.649028 재현 |
| output schema | 가격, 가격 범위, qwidth, guard 적용 여부, group match level 포함 |

## 7. API 운영 방식 권장안

### 7.1 번들 로딩

서비스 시작 시점에 Warm bundle과 Cold bundle을 각각 한 번 로드한다.

```text
API startup
  -> Warm runtime_store.joblib load
  -> Cold runtime_store.joblib load
  -> model_version registry 생성
```

요청마다 joblib 파일을 다시 읽지 않는다. 모델 객체는 메모리에 올려두고, API 요청은 입력 검증, route 판단, predictor 호출만 수행한다.

### 7.2 요청 처리

```text
POST /price-predictions
        |
        v
[입력 검증]
  - cm 크기
  - 매체/지지체
  - 작가명 또는 artist_key
        |
        v
[route 결정]
  - Warm 가능하면 Warm
  - 아니면 Cold
        |
        v
[모델 호출]
  - Warm predictor 또는 Cold predictor
        |
        v
[응답]
  - predicted_price_krw
  - model_route
  - model_version
  - confidence/review flags
  - diagnostics
```

### 7.3 버전 관리

운영 모델은 아래처럼 버전형 artifact로 관리한다.

```text
model_registry/
  official_0.1v/
    warm/
      artifact_id
      created_at
      sha256 manifest
      fixed_test_metrics
    cold/
      artifact_id
      created_at
      sha256 manifest
      fixed_test_metrics
```

새 학습 데이터가 쌓이면 기존 모델을 덮어쓰지 않고 새 버전으로 학습한다. 신규 버전은 fixed test, hold-out, parity 검증, shadow run을 통과한 뒤 운영 포인터만 바꾼다.

## 8. 운영 모니터링 항목

| 경로 | 저장할 항목 | 목적 |
|---|---|---|
| Warm | artist match basis, match score, homonym risk, artist_history_n | 작가 매칭 오류와 학습 이력 품질 감시 |
| Warm | q10/q50/q90, qwidth, residual 보정량 | 예측 불확실성 및 보정 과다 감시 |
| Warm | group match level, grp_n_log | 같은 작가 비교군 품질 감시 |
| Cold | q10/q40/q50/q90, qwidth | Cold 예측 범위와 불확실성 감시 |
| Cold | guard 적용 여부 | p95 방어가 어느 구간에서 발동되는지 확인 |
| Cold | group match level, grp_n_log | 비작가 그룹 통계 fallback 품질 감시 |
| 공통 | predicted_price_krw, actual_price_krw 후속 입력 | 재학습 후보 데이터 구축 |
| 공통 | model version, artifact sha | 결과 재현성 확보 |

## 9. 최종 권장 작업 순서

1. Warm joblib bundle을 official 0.1v Warm 운영 후보로 고정한다.
2. Warm predictor를 API adapter에 연결하고 fixed test parity를 다시 확인한다.
3. Cold k80 보수적 운영 기준안으로 `Cold 운영 정책`을 확정한다.
4. Cold를 Warm과 같은 방식의 독립 bundle로 재동결한다.
5. Cold validation/test parity와 외부 DB/CSV 미사용 검증을 수행한다.
6. Warm/Cold 통합 route 테스트를 만든다.
7. 운영 응답 schema와 모니터링 로그 schema를 확정한다.
8. 신규 학습 데이터가 쌓이면 재학습은 새 버전 artifact로 만들고, 기존 official 0.1v는 덮어쓰지 않는다.

## 10. 현재 기준 한 줄 정리

Warm은 `운영 가능한 joblib-only 후보`까지 정리되어 있다. Cold는 `k80 보수적 운영` 기준안으로 설명 기준을 갱신했으며, 실제 운영 모델로 확정하려면 Warm처럼 단일 번들 계약, artist_key 미사용 보장, API parity 검증, 모니터링 schema를 추가로 고정해야 한다.
