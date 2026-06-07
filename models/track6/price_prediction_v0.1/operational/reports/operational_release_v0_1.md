# 가격 예측 모델 v0.1 운영 릴리스

- 릴리스 일자: 2026-06-05
- 릴리스 범위: Warm 예측 운영 적용
- 운영 패키지 위치: `models/track6/price_prediction_v0.1/operational`
- 서비스 기본 출력 컬럼: `service_primary_pred_price_krw`

## 1. 운영 적용 모델

### 1.1 Warm 모델

- 적용 상태: 운영 적용 가능
- 적용 조건: 입력 작가가 v0.1 학습 작가 목록과 매칭되어 `warm_cold_route = warm`으로 분류되는 경우
- 서비스 주 후보: `pp_v8_compact_blend_mape_guarded`
- 서비스 출력 기본값: `service_primary_pred_price_krw`
- 보고서 기준 70:30 결합 후보: `v01_operational_pred_price_krw`
- 판단 근거: 0604 신규 Warm 라벨 평가에서 서비스 주 후보가 70:30 결합 후보보다 MdAPE, MAPE, p95_APE가 낮음

### 1.2 Cold 모델

- 적용 상태: 운영 자동 적용 보류
- 현재 상태: 실험 근거는 있으나 운영용 qwidth artifact 고정이 아직 필요함
- 서비스 처리: `prediction_status = cold_reference_pending_full_artifact`로 반환
- 운영 판단: v0.1 실서비스 1차 배포는 Warm만 자동 가격 예측 대상으로 제한

## 2. Warm 운영 예측 로직

### 2.1 서비스 주 예측값

```text
service_primary_log = pp_v8_compact_blend_mape_guarded
service_primary_price_krw = exp(service_primary_log)
```

- 로그 가격으로 모델을 계산한 뒤 원화 가격으로 되돌림
- 서비스 화면과 API에서는 `service_primary_pred_price_krw`를 기본 예측 가격으로 사용

### 2.2 서비스 주 후보 구성

```text
pp_v8_compact_blend_mape_guarded
  = 0.75 * pp_v2_defensive_component
  + 0.25 * l10_generated_bucket_seq
```

- `pp_v2_defensive_component`: 큰 오차를 줄이는 방향으로 안정화한 Warm 예측 구성
- `l10_generated_bucket_seq`: 생성 bucket 피처와 quantile 범위를 이용한 순차 보정 구성
- 두 값을 로그 가격 기준으로 결합

### 2.3 보고서 기준 70:30 후보

```text
v01_operational_log
  = 0.70 * svc_numeric_seed_mean
  + 0.30 * pp_v8_compact_blend_mape_guarded
```

- 기존 중간 리포트에서 1순위로 보던 70:30 결합 후보
- 0604 신규 라벨에서는 서비스 주 후보보다 낮은 성능을 보여 운영 기본값에서는 제외
- 비교와 추적을 위해 결과 CSV에는 계속 저장

## 3. 운영 산출물

### 3.1 모델 artifact

- `artifacts/warm_svc_numeric_seed_huber_ensemble.joblib`
- `artifacts/warm_pp_v2_defensive_component.cbm`
- `artifacts/warm_l10_generated_q10.cbm`
- `artifacts/warm_l10_generated_q50.cbm`
- `artifacts/warm_l10_generated_q90.cbm`
- `artifacts/warm_l10_generated_huber_centerline.joblib`
- `artifacts/warm_l10_generated_residual_catboost.cbm`
- `artifacts/operational_policy_manifest.json`

### 3.2 실행 스크립트

- artifact 생성: `scripts/build_operational_v0_1_artifacts.py`
- 운영 예측: `scripts/predict_operational_v0_1.py`
- 0604 라벨 평가: `scripts/evaluate_operational_v0_1_0604.py`

## 4. 운영 입력과 출력

### 4.1 입력

- 입력 파일: 운영형 작품 CSV
- 필수 입력: 작가명, 작품명, 작품 크기, 재료/지지체, URL 등 v0.1 피처 추출 스크립트가 요구하는 컬럼
- 작가 매칭: 운영단에서 작가명을 입력하면 작가 후보를 선택하게 하고, 내부적으로 `artist_key`와 연결하는 방식 권장

### 4.2 주요 출력 컬럼

- `service_primary_pred_price_krw`: 서비스 기본 예측 가격
- `service_primary_pred_price_usd`: 고정 환율 기준 달러 환산 가격
- `service_range_low_price_krw`: 표시용 하한 가격
- `service_range_high_price_krw`: 표시용 상한 가격
- `service_confidence_tier`: `high`, `medium`, `low`
- `svc_group_n`: 유사 작품 기반 표본 수
- `svc_group_level`: 유사 작품 묶음 기준
- `l10_price_range_ratio`: quantile 기반 가격 범위 폭
- `prediction_status`: 예측 상태

### 4.3 환율

- USD: 1,380 KRW
- EUR: 1,530 KRW
- GBP: 1,780 KRW
- HKD: 178 KRW
- JPY: 9.5 KRW
- 현재 버전은 고정 환율을 사용
- 운영 DB에서는 환율 스냅샷 테이블로 관리하고 예측 시점 환율을 같이 저장하는 방식 권장

## 5. 0604 신규 라벨 평가

### 5.1 평가 데이터

- 전체 입력: 6,873건
- Warm 분류: 6,873건
- Cold 분류: 0건
- 숫자 가격 라벨: 837건
- 50달러 미만 검수 필요 라벨: 8건

### 5.2 50달러 미만 검수 라벨 제외 기준

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
| --- | ---: | ---: | ---: | ---: | --- |
| service_primary | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 운영 기본값 |
| v01_operational 70:30 | 0.2779 | 0.3774 | 0.9871 | 1.1628 | 비교용 유지 |
| svc_numeric_seed_mean | 0.3072 | 0.4318 | 0.9998 | 1.2810 | 단독 적용 제외 |
| l10_generated_bucket_seq | 0.3207 | 0.4598 | 1.2569 | 1.0793 | 단독 적용 제외 |

### 5.3 해석

- 70:30 결합은 유사 작품 기반 가격 피처를 강하게 반영해 안정적일 것으로 기대했으나, 0604 신규 데이터에서는 일부 작가/작품 구간에서 가격을 과하게 끌어올림
- `pp_v8` 단독은 오차 안정화 구성과 생성 bucket 기반 보정을 결합해 p95_APE가 더 낮음
- 운영 기본값은 신규 라벨 평가 기준으로 더 안정적인 `service_primary`를 사용
- 기존 70:30 후보는 모델 비교와 추후 재검증용 컬럼으로 유지

## 6. 재현 절차

### 6.1 피처 추출

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \
  --input data/test_new_artworks_test_noprice_0604.csv \
  --model-root models/track6/price_prediction_v0.1 \
  --output-dir models/track6/price_prediction_v0.1/operational/outputs/0604_features
```

### 6.2 운영 예측

```bash
python3 models/track6/price_prediction_v0.1/operational/scripts/predict_operational_v0_1.py \
  --feature-dir models/track6/price_prediction_v0.1/operational/outputs/0604_features \
  --output-dir models/track6/price_prediction_v0.1/operational/outputs/0604_predictions
```

### 6.3 라벨 평가

```bash
python3 models/track6/price_prediction_v0.1/operational/scripts/evaluate_operational_v0_1_0604.py
```

## 7. 운영 제한 사항

- Cold 자동 가격 예측은 v0.1 운영 범위에서 제외
- 50달러 미만 라벨은 실제 판매가보다 테스트/플레이스홀더 값일 가능성이 있어 별도 검수 대상으로 분리
- 가격 범위는 L10 quantile 모델의 q10/q90을 기준으로 한 표시용 범위
- 환율은 현재 고정값이므로 운영 적용 시 예측 시점 환율 스냅샷 저장 필요
- PP-V2 component는 기존 PP-V2 방어 후보의 고정 예측값을 재현하도록 학습한 운영 artifact

## 8. 최종 판단

- v0.1 운영 배포 기본값: `service_primary_pred_price_krw`
- Warm 예측: 배포 가능
- Cold 예측: 운영 자동 적용 보류
- 서비스 화면: 가격, 범위, 신뢰도, 유사 표본 수를 함께 표시
- 추가 개선: Cold artifact 고정, 환율 DB화, 작가명 선택/동명이인 처리 API 연동
