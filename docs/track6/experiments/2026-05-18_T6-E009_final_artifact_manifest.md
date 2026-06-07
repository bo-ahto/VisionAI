# T6-E009 최종 artifact manifest

- 날짜: `2026-05-29`
- 관련 가설: `T6-H8`
- 상태: 검증 완료
- 목적: Track6 최종 후보 모델, 피처, 재현 파일을 manifest로 고정
- 사용 스크립트: `scripts/track6/run_t6_e009_build_final_artifacts.py`
- manifest: `data/track6/artifacts/track6_artifact_manifest.json`

## 1. 생성 원칙

- test 데이터는 artifact 학습에 사용하지 않음
- artifact 학습에는 `train + validation`만 사용
- Warm/Cold 모델은 분리 관리
- Cold는 CatBoost와 LightGBM 후보를 함께 남김
- 운영 입력에서 만들 수 없는 피처는 사용하지 않음

## 2. artifact 목록

| 구분 | 모델 | 피처셋 | 학습 row | 파일 |
|---|---|---|---:|---|
| `warm_price_model` | `HuberRegressor` | `base_existing_combo` | `27433` | `data/track6/artifacts/track6_warm_huber.joblib` |
| `cold_catboost_price_model` | `CatBoostRegressor` | `base_medium_shape` | `29667` | `data/track6/artifacts/track6_cold_catboost.cbm` |
| `cold_lightgbm_price_model` | `LGBMRegressor` | `base_support_size` | `29667` | `data/track6/artifacts/track6_cold_lightgbm.joblib` |

## 3. 운영 라우팅

- 입력 작가가 학습 artist_key/한글명 기준으로 확인되면 Warm 후보 사용
- 처음 보는 작가이면 Cold 후보 사용
- Cold 3D, 극단 형태, 비균형 형태는 신뢰도 경고 후보로 표시
- Warm 저이력 작가는 신뢰도 경고 후보로 표시

## 4. 결론

- T6-H8은 검증 완료
- Track6 기준 최종 후보 artifact와 manifest를 생성함
- 다음 작업은 서비스 입력 스키마와 추론 스크립트 연결
