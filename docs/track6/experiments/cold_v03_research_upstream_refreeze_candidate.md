# Cold v0.3 연구 기준 상류 재동결 후보 감사

- 작성일: 2026-06-12T14:46:39
- 목적: 보고서 기준 Cold 최고 성능 경로를 raw 입력 서비스로 승격하기 위한 저장 가능 범위 확인
- 결론: PP-Y2 LightGBM Quantile과 QR1 LightGBM q40은 재학습/저장 가능 후보로 생성. 검색 피처 수집/표준화 파이프라인은 운영 입력용 별도 연결 필요

## 1. 저장한 후보 아티팩트

| 구분 | 파일 |
|---|---|
| pp_y2_lgbq_q10 | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/pp_y2_search_external_lgbq_q10.joblib` |
| pp_y2_lgbq_q50 | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/pp_y2_search_external_lgbq_q50.joblib` |
| pp_y2_lgbq_q90 | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/pp_y2_search_external_lgbq_q90.joblib` |
| qr1_lgb_q40 | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/qr1_lightgbm_q40.joblib` |
| pp_y16_segment_map | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/pp_y16_segment_map.json` |
| feature_schema | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/feature_schema.json` |
| candidate_predictions | `models/track6/cold_v03_research_upstream_refreeze_candidate/artifacts/cold_v03_refreeze_candidate_test_predictions.csv` |

## 2. 원본 예측 대비 차이

| 항목 | split | n | 최대 차이 | 평균 차이 | p95 차이 | 1e-9 일치 |
|---|---|---:|---:|---:|---:|---|
| PP-Y2 q10_log | validation | 2753 | 1.7763568394002505e-15 | 4.3360399421611637e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y2 pred_log | validation | 2753 | 1.7763568394002505e-15 | 3.271387277791235e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y2 q90_log | validation | 2753 | 3.552713678800501e-15 | 3.594009297297274e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y2 q10_log | test | 3099 | 1.7763568394002505e-15 | 4.849299406688002e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y2 pred_log | test | 3099 | 1.7763568394002505e-15 | 3.9035140614119736e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y2 q90_log | test | 3099 | 3.552713678800501e-15 | 2.8430880682236986e-16 | 1.7763568394002505e-15 | 예 |
| QR1 LightGBM q40 pred_log | validation | 2753 | 1.7763568394002505e-15 | 4.2779679786500767e-16 | 1.7763568394002505e-15 | 예 |
| QR1 LightGBM q40 pred_log | test | 3099 | 1.7763568394002505e-15 | 4.316220393896059e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y16 pred_log | test | 3099 | 3.552713678800501e-15 | 6.04156214497536e-16 | 1.7763568394002505e-15 | 예 |
| PP-Y16 correction_log | test | 3099 | 8.326672684688674e-17 | 3.4866878306435415e-17 | 8.326672684688674e-17 | 예 |
| PP-Y16 quantile_width_log | test | 3099 | 4.440892098500626e-16 | 2.43700939819704e-17 | 2.220446049250313e-16 | 예 |

## 3. v0.3 최종 후처리 재계산

| 항목 | 값 |
|---|---:|
| test n | 3099 |
| MdAPE | 0.409819977861 |
| MAPE | 0.849260008657 |
| p95 APE | 2.346465171577 |
| RMSE log | 0.850258512908 |
| 기록 지표 대비 최대 차이 | 6.217248937900877e-15 |

## 4. 운영 adapter 승격 판단

- 승격 가능 후보: PP-Y2 검색 포함 LightGBM Quantile, QR1 LightGBM q40, PP-Y16 qwidth segment 보정 map
- 추가 필요: 신규 입력에 대한 검색 피처 수집/표준화, 전시/갤러리 파생 피처 연결, 작가 key 매칭 후 검색 delta fallback 정책
- 현재 의미: 저장 모델 후보는 생성됐지만, 실제 서비스 raw 입력에서 같은 피처를 만들 수 있어야 exact adapter로 승격 가능
