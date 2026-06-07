# OP-0604 신규 테스트 데이터 현재 정책 적용 전 점검

- 작성일: 2026-06-04 16:03
- 입력 파일: `data/test_new_artworks_test_0604.csv`
- 목적: 2026-06-04 신규 운영형 데이터를 가격 라벨과 입력 데이터로 분리하고, 중간 리포트 기준 후보를 그대로 적용할 수 있는지 확인

## 1. 결론

- 새 데이터는 가격 라벨을 분리한 뒤 운영 입력 형태로 평가하는 방식이 맞음
- 명시 가격 라벨 행: 837/6,873건, 라벨 파싱 성공률: 0.122
- `Sold`, `Price on request`, 빈값 등은 가격 평가 라벨로 사용할 수 없고 운영 입력 샘플로만 사용
- 현재 `matched_train_artist` 기준 라우팅: Warm 6,873건, Cold 0건
- 중간 리포트의 Warm 1순위 후보를 기준으로 평가하는 것이 맞지만, 현재 저장소에는 해당 결합 후보의 신규 데이터용 단일 추론 artifact가 없음
- 따라서 예전 `track6_warm_huber.joblib` 결과를 현재 Warm 1순위 결과로 보고하면 안 됨
- 다음 실행은 PP-SVC3와 PP-Y18을 신규 데이터에 적용 가능한 artifact 또는 재현 스크립트로 고정한 뒤 진행하는 것이 맞음

## 2. 생성 파일

| 파일 | 의미 |
|---|---|
| `experiments/track6/OP-0604_new_artworks_current_policy_readiness/data/raw_input_with_id.csv` | 원본 데이터에 내부 행 ID를 붙인 파일 |
| `experiments/track6/OP-0604_new_artworks_current_policy_readiness/data/operational_input.csv` | 가격 라벨 컬럼을 제거한 운영 입력용 파일 |
| `experiments/track6/OP-0604_new_artworks_current_policy_readiness/data/labels.csv` | 가격 평가용 라벨 파일 |
| `experiments/track6/OP-0604_new_artworks_current_policy_readiness/outputs/model_policy_readiness.csv` | 중간 리포트 기준 후보 실행 가능성 점검표 |
| `experiments/track6/OP-0604_new_artworks_current_policy_readiness/outputs/route_summary.csv` | Warm/Cold 라우팅 요약 |

## 3. 라우팅/라벨 요약

| metric | value |
| --- | --- |
| total_rows | 6873.0 |
| label_parsed_rows | 837.0 |
| warm_route_rows | 6873.0 |
| cold_route_rows | 0.0 |
| matched_train_artist_nonempty_rows | 6873.0 |
| matched_artist_in_train_key_rows | 6873.0 |
| median_label_price_krw | 2760000.0 |
| p10_label_price_krw | 600000.0 |
| p90_label_price_krw | 23675999.99999999 |

## 4. 세부 분포

| group_type | price_currency | rows | route_by_current_match | price_label_status | matched_train_artist |
| --- | --- | --- | --- | --- | --- |
| currency | EUR | 108 |  |  |  |
| currency | GBP | 8 |  |  |  |
| currency | HKD | 42 |  |  |  |
| currency | JPY | 3 |  |  |  |
| currency | KRW | 2090 |  |  |  |
| currency | USD | 4622 |  |  |  |
| route |  | 6873 | warm |  |  |
| price_label_status |  | 837 |  | explicit_price |  |
| price_label_status |  | 9 |  | inquire_no_price |  |
| price_label_status |  | 683 |  | missing_sale_message |  |
| price_label_status |  | 42 |  | on_hold_no_price |  |
| price_label_status |  | 7 |  | on_loan_no_price |  |
| price_label_status |  | 2076 |  | price_on_request |  |
| price_label_status |  | 3219 |  | sold_no_price |  |
| top_artist |  | 269 | warm |  | qwaya |
| top_artist |  | 226 | warm |  | cha young seok |
| top_artist |  | 189 | warm |  | hye eun kang |
| top_artist |  | 131 | warm |  | seongbin gam |
| top_artist |  | 127 | warm |  | hyunsoo kim |
| top_artist |  | 125 | warm |  | sooyoung chung |
| top_artist |  | 122 | warm |  | hyunsik kim |
| top_artist |  | 121 | warm |  | kwon kisoo |
| top_artist |  | 108 | warm |  | junyoung kang |
| top_artist |  | 85 | warm |  | yeji seo |
| top_artist |  | 82 | warm |  | kang yehsine |
| top_artist |  | 81 | warm |  | eunju kim |
| top_artist |  | 75 | warm |  | zikseong jeong |
| top_artist |  | 74 | warm |  | jieun lee |
| top_artist |  | 73 | warm |  | hur boree |
| top_artist |  | 72 | warm |  | seong joon hong |
| top_artist |  | 69 | warm |  | seontae hwang |
| top_artist |  | 67 | warm |  | taehoon park |
| top_artist |  | 65 | warm |  | jihoon ha |
| top_artist |  | 63 | warm |  | jae ho jung |
| top_artist |  | 60 | warm |  | inhye jeong |
| top_artist |  | 59 | warm |  | wongi sul |
| top_artist |  | 58 | warm |  | hanna kim |
| top_artist |  | 53 | warm |  | gyomyung shin |
| top_artist |  | 52 | warm |  | han unsung |
| top_artist |  | 52 | warm |  | jaeyeon yoo |
| top_artist |  | 50 | warm |  | junseok kang |
| top_artist |  | 48 | warm |  | inhee jang |
| top_artist |  | 46 | warm |  | beom jun |
| top_artist |  | 44 | warm |  | gyul e kim |

## 5. 모델 정책 실행 가능성

| policy_area | candidate | midterm_role | intended_use | direct_runnable_status | reason | action_for_0604_test |
| --- | --- | --- | --- | --- | --- | --- |
| Warm current primary | PP-SVC3 blend_svcnum_ppv8_wsvc_0.70 | 현재 Warm 1순위 | Warm route의 주 예측가 | not_directly_runnable | svc_numeric_seed_mean과 pp_v8_compact_blend_mape_guarded 예측값을 70:30으로 결합한 정책이다. 현재 저장소에는 기존 validation/test 예측 CSV는 있으나 신규 데이터에 바로 적용할 단일 추론 artifact가 없다. | 정확한 현재 후보 평가 전 PP-SVC3 추론 artifact 재현/고정 필요 |
| Warm comparable-price component | svc_numeric_seed_mean | PP-SVC3의 70% 축 | 유사 작품 기반 가격 피처를 Huber에 넣은 Warm 예측 | runnable_by_refit_not_frozen | 학습 split에서 재학습하면 만들 수 있지만, 배포용으로 고정 저장된 artifact는 아직 없다. | 운영 실험에서는 artifact화 후 사용하거나 refit 결과임을 명시 |
| Warm error-stabilization component | pp_v8_compact_blend_mape_guarded | PP-SVC3의 30% 축 | 평균오차를 방어하는 Warm 보조 예측 | not_directly_runnable | 여러 이전 Warm 후보 예측 파일의 compact blend 결과이며 신규 데이터용 개별 component artifact가 없다. | PP-V8 component chain을 재현 가능한 추론 모듈로 고정 필요 |
| Cold current reference | PP-Y18 qwidth_bin_oof_min30_cap0.25 | Cold 참고 예측 정책 | Cold route의 참고 예측가와 넓은 가격 범위 | not_directly_runnable_as_single_artifact | LightGBM Quantile 예측과 qwidth 구간 보정 결과가 실험 예측 파일 중심으로 남아 있어 단일 신규 추론 artifact는 없다. | Cold 신규 샘플 평가 전 LightGBM Quantile + qwidth 보정 artifact 필요 |
| Legacy warm artifact | data/track6/artifacts/track6_warm_huber.joblib | 이전 baseline | 데이터 파이프라인 smoke test 또는 비교 기준 | runnable_baseline | 저장된 joblib artifact는 있으나 중간 리포트의 Warm 1순위 후보가 아니다. | 필요 시 baseline으로만 별도 표기 |
| Legacy cold artifacts | track6_cold_lightgbm.joblib / track6_cold_catboost.cbm | 이전 baseline | Cold baseline 비교 | runnable_baseline | 저장된 artifact는 있으나 중간 리포트의 Cold reference 정책과는 다르다. | 필요 시 baseline으로만 별도 표기 |

## 6. Artifact 점검

| artifact | exists | role | model | feature_set |
| --- | --- | --- | --- | --- |
| data/track6/artifacts/track6_artifact_manifest.json | True | legacy artifact manifest |  |  |
|  | True | warm_price_model | HuberRegressor | base_existing_combo |
|  | True | cold_catboost_price_model | CatBoostRegressor | base_medium_shape |
|  | True | cold_lightgbm_price_model | LGBMRegressor | base_support_size |
| experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/selected_candidate_metrics.csv | True | experiment prediction/metric source |  |  |
| experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/predictions.csv | True | experiment prediction/metric source |  |  |
| experiments/track6/PP-V8_warm_deployment_simplification/outputs/predictions.csv | True | experiment prediction/metric source |  |  |
| experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/metrics.csv | True | experiment prediction/metric source |  |  |
| experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv | True | experiment prediction/metric source |  |  |

## 7. 진행 판단

- exact_current_policy_runnable: `false`
- 지금 바로 성능표를 만들려면 두 가지를 분리해야 함
- 1안: 현재 중간 리포트 후보를 재현 가능한 추론 artifact로 먼저 고정한 뒤 신규 테스트 평가
- 2안: 기존 artifact를 baseline smoke test로만 실행하고, 결과명에 `legacy baseline`을 명확히 표기
