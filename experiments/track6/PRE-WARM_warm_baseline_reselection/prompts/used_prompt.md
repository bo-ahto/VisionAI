# PRE-WARM Warm 기준 모델 재선정 실험

- 목적: 후처리 전 Warm Huber 기준 모델을 다시 선정한다.
- 비교 대상:
  - 현재 final artifact `base_existing_combo`
  - 기존 고성능 compact 후보 `artist_name_ko + size`
  - `artist_name_ko x log_area`, `artist_name_ko x ln_estimated_ho` 교차항 후보
  - 운영 적용성을 확인하기 위한 `artist_key` 변환 후보
- 통제 조건:
  - Track6 Warm split 고정
  - target `ln_price_krw` 고정
  - HuberRegressor 설정 고정
  - 평가 지표 고정: MdAPE, p95_APE, RMSE_log, R2, Within_30, Within_50
