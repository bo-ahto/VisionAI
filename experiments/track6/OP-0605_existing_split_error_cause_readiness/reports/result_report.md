# 기존 검증 데이터 기반 작품별 오차 원인 분석 가능성 확인

## 1. 확인 목적

- 0604 신규 데이터는 라벨/정합성 검증이 덜 끝난 운영 입력 데이터
- 최종 모델 커스텀 보정의 학습/검증 기준으로 바로 쓰기에는 위험
- 따라서 기존 검증 split 데이터로 작품별 오차 원인 분석이 가능한지 Warm/Cold 각각 확인

## 2. 결론

- Warm: 가능
- Cold: 가능
- 기준 조인 키: `_track6_row_id`
- 기존 예측 산출물과 기존 split 원본이 모두 `_track6_row_id` 기준으로 100% 매칭됨
- 0604 데이터는 운영 입력 검증/추가 확인용으로만 두고, 원인 분석과 보정 후보 검증은 기존 validation/test split 기준으로 진행하는 것이 안전

## 3. Warm 분석 가능 파일

| 용도 | 파일 | 사용 이유 |
|---|---|---|
| Warm 대표 후보 예측 | `models/track6/price_prediction_v0.1/evidence/experiments/PP-V8_warm_deployment_simplification/outputs/predictions.csv` | v0.1 운영 기본값의 뿌리인 PP-V8 계열 후보를 작품 단위로 확인 가능 |
| Warm 유사 작품 기반 예측 | `models/track6/price_prediction_v0.1/evidence/experiments/PP-SVC3_warm_svc_blend_routing/outputs/predictions.csv` | 유사 작품 묶음 수준, coverage tier, 표본 수가 포함되어 원인 분류에 유리 |
| Warm MAPE 개선 후보 | `experiments/track6/PP-WMAPE_warm_mape_optimization/outputs/candidate_predictions.csv` | MAPE/큰 오차 개선 후보를 작품 단위로 비교 가능 |
| Warm 원본 split | `data/track6_split_with_year_type_edition_size_artist_name/track6_val_warm.csv` | validation 작품 피처/정답 라벨 |
| Warm 원본 split | `data/track6_split_with_year_type_edition_size_artist_name/track6_test_warm.csv` | test 작품 피처/정답 라벨 |

## 4. Cold 분석 가능 파일

| 용도 | 파일 | 사용 이유 |
|---|---|---|
| Cold 대표 개선 후보 예측 | `models/track6/price_prediction_v0.1/evidence/experiments/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv` | PP-Y21에서 재사용한 Cold qwidth 안정화 후보의 row 단위 예측 포함 |
| Cold 반복 안정성 요약 | `experiments/track6/PP-Y21_cold_y18_split_seed_stability/outputs/metrics.csv` | 후보 선택 근거와 반복 split 안정성 확인 |
| Cold 원본 split | `data/track6_split_with_year_type_edition_size_artist_name/track6_val_cold.csv` | validation 작품 피처/정답 라벨 |
| Cold 원본 split | `data/track6_split_with_year_type_edition_size_artist_name/track6_test_cold.csv` | test 작품 피처/정답 라벨 |

## 5. 조인 검증 결과

| source | route | split | pred_rows | matched_rows | match_rate | feature_cols_available | feature_cols_needed |
|---|---|---:|---:|---:|---:|---:|---:|
| warm_pp_v8 | warm | test | 3,642 | 3,642 | 1.0 | 18 | 19 |
| warm_pp_v8 | warm | validation | 3,114 | 3,114 | 1.0 | 18 | 19 |
| warm_pp_svc3 | warm | test | 4,249 | 4,249 | 1.0 | 18 | 19 |
| warm_pp_svc3 | warm | validation | 3,633 | 3,633 | 1.0 | 18 | 19 |
| warm_wmape | warm | test | 52,809 | 52,809 | 1.0 | 18 | 19 |
| warm_wmape | warm | validation | 45,153 | 45,153 | 1.0 | 18 | 19 |
| cold_pp_y18 | cold | test | 24,792 | 24,792 | 1.0 | 18 | 19 |
| cold_pp_y18 | cold | validation | 22,024 | 22,024 | 1.0 | 18 | 19 |

참고:

- `warm_wmape`, `cold_pp_y18`은 후보가 여러 개라 행 수가 큼
- 작품 단위 분석에서는 분석 대상 후보를 하나 선택한 뒤 `_track6_row_id` 기준으로 보면 됨
- 누락된 확인 컬럼 1개는 `artist_exhibition_total_count`
- 원본 split에는 `artist_exhibition_available_count`, `artist_exhibition_solo/group/fair_count`가 있어 전시 활동 정보는 대체 가능

## 6. 기존 데이터로 가능한 오차 원인 분류

Warm에서 가능한 원인 분류:

- 같은 작가 표본 수 부족
- 유사 작품 묶음 수준 부족
- 작가 기준값이 소형/저가 작품에 과대 적용
- 고가 작품 상방 꼬리 과소 예측
- 재료/지지체/크기 조합별 잔차
- 제작연도/작품 유형/edition 정보에 따른 잔차
- Warm 후보 간 예측 차이

Cold에서 가능한 원인 분류:

- q10~q90 예측 폭이 큰 불확실 구간
- 외부/작가 메타 정보 부족 구간
- 크기/재료/지지체 조합의 데이터 부족
- 고가/저가 가격대별 과대/과소 예측
- LightGBM Quantile 보정 후보 간 예측 차이
- 신규 작가 특성상 작가 가격 기준선 부재로 발생하는 오차

## 7. 다음 실험 제안

실험명:

- `OP-0605_existing_split_error_cause_customization`

진행 방식:

- 0604 데이터 제외
- 기존 validation split에서 원인별 잔차 패턴 확인
- 기존 test split에서 보정 후보 검증
- Warm/Cold를 완전히 분리
- 정답 가격을 알아야만 가능한 사후 원인 설명과, 운영에서 사전에 알 수 있는 피처 기반 보정을 분리

검증 기준:

- baseline 후보 대비 MdAPE 개선
- MAPE 개선
- p95_APE 개선
- over 3x / under 1/3x 큰 오차 건수 감소
- 특정 구간만 좋아지고 전체 성능이 악화되는지 확인

## 8. 판단

- 기존 데이터만으로도 Warm/Cold 모두 작품별 오차 원인 분석은 가능
- 0604 데이터보다 기존 validation/test split이 보정 후보 실험 기준으로 더 적합
- 다음 단계는 기존 split 기준으로 실제 원인 분류표와 보정 후보 검증표를 생성하는 것
