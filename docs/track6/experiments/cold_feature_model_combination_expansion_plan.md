# Cold 피처/모델 조합 추가 실험 계획

- 작성일: 2026-06-03
- 목적: Cold 가격 예측에서 아직 충분히 검증하지 못한 피처 조합, 모델 순서, 모델별 커스텀 방식을 체계적으로 실험해 예측 정확도 개선 가능성을 더 찾는다.
- 기준 결과:
  - Cold 대표 정확도 기존 강한 후보: `PP-X3 lightgbm_quantile_exhibition_gallery` test MdAPE `0.4451`, MAPE `1.1277`, p95 `3.8935`
  - Cold CatBoost 작가 메타 기준: `PP-W2 generated_all_meta_all` test MdAPE `0.4497`, MAPE `1.1111`, p95 `4.1587`
  - Cold 평균 오차/큰 오차 방어 기준: `PP-W4 lightgbm_quantile_meta_all_huber_cap0.5_s1` test MdAPE `0.4949`, MAPE `0.9584`, p95 `3.0073`
  - Cold 모델 순서 변경 기준: `PP-S1 n2_catboost_quantile_huber_cap0.2_s1` test MdAPE `0.4744`, MAPE `1.2095`, p95 `3.4731`
  - 검색 피처 보조 후보: `PP-H9 lightgbm_quantile_search_all` test MdAPE `0.4773`, MAPE `1.0308`, p95 `2.9954`

## 1. 판단

- 추가 실험은 필요하다.
- Cold는 Warm처럼 작가 기준 가격선이 강하지 않기 때문에 단일 모델 하나로 크게 개선되기 어렵다.
- 대신 모델별 장점이 분명하게 갈린다.
  - CatBoost는 범주형/조건 조합을 잘 나눈다.
  - CatBoost Quantile은 평균 오차와 큰 오차 방어에 강한 신호가 있었다.
  - LightGBM Quantile은 전시/갤러리 피처를 넣었을 때 MdAPE가 가장 크게 개선됐다.
  - Huber residual은 단독 예측보다 2단계 안정화 역할에 적합하다.
  - 검색/전시/갤러리 피처는 단독 핵심 피처라기보다 불확실성, 신뢰도, 라우팅 기준으로 쓸 가능성이 높다.
- 따라서 다음 실험은 “피처 묶음 추가”와 “모델 순서 변경”을 따로 보지 말고 함께 설계해야 한다.

## 2. 실험 원칙

- test 결과를 반복해서 고르는 방식은 피한다.
- validation 또는 학습 내부 교차 예측으로 후보를 고르고 test는 최종 확인으로 사용한다.
- 같은 데이터 split, 같은 평가 지표, 같은 baseline을 유지한다.
- 실험별로 비교군을 반드시 둔다.
- 개선 판단은 MdAPE 하나만 보지 않는다.
  - 대표 가격 후보: MdAPE 우선, MAPE/p95 악화 제한
  - 서비스 안정 후보: p95_APE, MAPE 우선, MdAPE 악화 허용 범위 명시
  - 보조 정책 후보: 가격 범위, 신뢰도, 라우팅 안정성 중심

## 3. 우선순위 높은 실험군

## PP-Y1~Y5. Cold 피처 조합 재탐색

### PP-Y1. LightGBM Quantile + 전시/갤러리 + 작가 메타 목적별 재학습

- 비교군:
  - `PP-W4 base_lightgbm_quantile_meta_all`
  - `PP-X3 lightgbm_quantile_exhibition_gallery`
- 사용 피처:
  - 작품 기본 피처
  - 작가 메타 전체
  - 전시 활동 피처
  - 갤러리 raw/validated tier 및 가용 flag
- 실험 이유:
  - `PP-X3`에서 전시+갤러리가 MdAPE를 `0.4451`까지 낮췄지만 p95가 악화됐다.
  - LightGBM Quantile은 중앙값 예측에는 효과가 있었으므로 목적함수와 피처 조합을 조금 더 분리해볼 가치가 있다.
- 실행 방법:
  - q50 중앙 예측 모델을 기본으로 학습한다.
  - 같은 피처셋으로 q10/q90도 함께 학습해 예측 범위 폭을 만든다.
  - q90-q10 폭이 큰 구간에서 p95 악화가 집중되는지 확인한다.
- 기대 결과:
  - MdAPE는 `PP-X3` 수준을 유지하면서 p95 악화 구간을 분리할 수 있는지 확인.
- 성공 기준:
  - MdAPE `0.445~0.455` 범위 유지.
  - p95가 `PP-X3`의 `3.8935`보다 낮아지거나, 악화 구간을 명확히 라우팅 가능.

### PP-Y2. LightGBM Quantile + 검색 피처 + 전시/갤러리 결합

- 비교군:
  - `PP-H9 lightgbm_quantile_search_all`
  - `PP-X3 lightgbm_quantile_exhibition_gallery`
- 사용 피처:
  - `PP-W4` 작가 메타 피처
  - `PP-H9` 검색 문맥/품질 피처
  - `PP-X3` 전시/갤러리 피처
- 실험 이유:
  - 검색 피처는 p95 `2.9954`로 큰 오차 방어에 강했다.
  - 전시/갤러리는 MdAPE `0.4451`로 대표 정확도에 강했다.
  - 두 피처군의 역할이 다르므로 결합 가치가 있다.
- 실행 방법:
  - 피처 묶음을 `검색만`, `전시/갤러리만`, `검색+전시/갤러리`로 나눠 LightGBM Quantile 재학습.
  - 검색 품질 low 구간은 별도 flag로 유지하고, 검색 피처 값 자체보다 품질/가용 여부를 함께 본다.
- 기대 결과:
  - 전시/갤러리의 MdAPE 장점과 검색 피처의 p95 장점을 같이 가져오는지 확인.
- 성공 기준:
  - MdAPE가 `0.46` 이하이고 p95가 `3.2` 이하이면 강한 후보.

### PP-Y3. CatBoost Quantile + 갤러리 단독/전시 제외 피처 재검증

- 비교군:
  - `PP-W2 generated_all_meta_all`
  - `PP-X2 catboost_gallery`
  - `PP-S1 CatBoost Quantile -> Huber residual`
- 사용 피처:
  - CatBoost 작가 메타 기준 피처
  - 갤러리 raw tier, tier 가용 여부, 검증 tier score
  - 전시 피처는 제외 또는 별도 후보로 분리
- 실험 이유:
  - `PP-X2`에서 CatBoost는 갤러리 단독 추가만 소폭 개선됐다.
  - 반면 전시 피처를 같이 넣으면 CatBoost에서 MdAPE/MAPE가 악화됐다.
  - 따라서 CatBoost에는 전시보다 갤러리/가용 여부 중심이 더 적합할 수 있다.
- 실행 방법:
  - RMSE CatBoost가 아니라 Quantile q50 CatBoost로 학습한다.
  - 이후 Huber residual cap `0.15~0.50`을 적용한다.
- 기대 결과:
  - CatBoost의 조건 조합 장점과 Quantile의 중앙값 안정성을 함께 확인.
- 성공 기준:
  - `PP-W2` 대비 MdAPE 개선.
  - `PP-S1` 대비 MAPE 또는 p95 개선.

### PP-Y4. Cold LightGBM 피처 교환 후보를 Quantile/Huber 구조에 재투입

- 비교군:
  - `PP-U3 medium_size_combo`
  - `PP-W4 base_lightgbm_quantile_meta_all`
- 사용 피처:
  - `support_size_bucket`
  - `medium_size_bucket`
  - `medium_shape_bucket`
  - `support_shape_combo`
  - 작가 메타 전체
- 실험 이유:
  - `PP-U3`에서 LightGBM은 `medium_size_combo`가 test MdAPE `0.4803`으로 기준보다 개선 신호가 있었다.
  - 그러나 이 피처 교환 후보를 Quantile/Huber 순차 구조에 아직 충분히 투입하지 않았다.
- 실행 방법:
  - LightGBM objective를 `quantile`, `huber`, `mape`, `regression_l1`로 나눠 재학습.
  - 가장 나은 1차 예측에 Huber residual을 약하게 적용한다.
- 기대 결과:
  - LightGBM의 leaf-wise 구간 분리 장점을 더 적합한 bucket 조합으로 강화.
- 성공 기준:
  - `PP-W4` p95 안정성을 유지하면서 MdAPE `0.46`대 진입.

### PP-Y5. 피처 가용성/품질 기반 라우팅 피처 실험

- 비교군:
  - `PP-W2`
  - `PP-W4`
  - `PP-X3`
  - `PP-H9`
- 사용 피처:
  - 작가 메타 결측 개수
  - 전시 정보 가용 개수
  - 갤러리 tier 가용 여부
  - 검색 품질 등급
  - q90-q10 예측 범위 폭
- 실험 이유:
  - Cold는 데이터가 충분한 작품과 부족한 작품의 오차 구조가 다를 가능성이 높다.
  - 피처 값을 직접 넣는 것보다 “이 정보를 믿을 수 있는지”를 기준으로 모델을 선택하는 방식이 더 안정적일 수 있다.
- 실행 방법:
  - 정보량 segment별로 후보 모델 성능을 비교한다.
  - 정보량 높은 구간은 MdAPE 강한 후보, 정보량 낮은 구간은 p95 강한 후보로 라우팅한다.
- 기대 결과:
  - 모든 Cold에 같은 모델을 쓰는 것보다 조건별 모델 선택이 유리한지 확인.
- 성공 기준:
  - 전체 MdAPE 악화 없이 p95 또는 MAPE 개선.

## PP-Y6~Y11. 모델 순서/커스텀 실험

### PP-Y6. LightGBM Quantile 선행 + CatBoost residual

- 1단계:
  - LightGBM Quantile q50
  - 피처: 작가 메타 + 전시/갤러리 + 검색 품질 후보
- 2단계:
  - CatBoost residual
  - target: `actual_log - pred_log`
  - 입력: 1단계 예측값, q90-q10 폭, 작품/작가/외부 피처
- 실험 이유:
  - LightGBM은 전시/갤러리 MdAPE 개선에 강했다.
  - CatBoost는 범주형 조합 residual을 나눌 수 있다.
- 주의:
  - residual은 반드시 OOF 기반으로 만든다.
  - validation residual만 직접 학습하면 과적합 위험이 크다.
- 성공 기준:
  - `PP-X3` 대비 p95 악화 완화.
  - `PP-W4` 대비 MdAPE 개선.

### PP-Y7. CatBoost Quantile 선행 + LightGBM residual

- 1단계:
  - CatBoost Quantile q50
  - 피처: CatBoost형 작품 bucket + 작가 메타 + 갤러리 단독 피처
- 2단계:
  - LightGBM residual
  - 입력: residual, pred_bin, q-width, size/support/medium bucket
- 실험 이유:
  - CatBoost Quantile은 Cold에서 모델 순서 변경 후보로 유효했다.
  - LightGBM은 tail/pred_bin 구간 보정에 강할 수 있다.
- 성공 기준:
  - `PP-S1` 대비 MdAPE 또는 p95 개선.

### PP-Y8. CatBoost Quantile 선행 + Huber residual + 외부 피처 quality cap

- 1단계:
  - CatBoost Quantile q50
- 2단계:
  - Huber residual
- 커스텀:
  - 외부 피처 품질이 낮은 경우 residual 보정 강도를 낮춘다.
  - 검색 품질 low, 검증 tier 없음, 전시 정보 결측 많음이면 cap을 작게 적용한다.
- 실험 이유:
  - `PP-S1`은 좋은 구조였지만 외부 피처 품질별 보정 강도 조정은 충분히 하지 않았다.
- 성공 기준:
  - `PP-S1 cap0.2`의 MdAPE 장점과 `cap0.5`의 p95 장점을 동시에 일부 확보.

### PP-Y9. 목적함수 커스텀 확장

- 대상 모델:
  - LightGBM
  - CatBoost
- 목적함수 후보:
  - RMSE
  - MAE 또는 L1
  - Huber
  - Quantile q50
  - MAPE 목적함수는 모델/라이브러리 지원 여부 확인 후 사용
- 피처셋:
  - `PP-W4` 작가 메타 기준
  - `PP-X3` 전시/갤러리 기준
  - `PP-H9` 검색 결합 기준
- 실험 이유:
  - Cold의 목표가 단순 RMSE가 아니라 MdAPE/MAPE/p95 균형이므로 loss를 바꿔볼 가치가 있다.
- 성공 기준:
  - 목적별 후보 분리:
    - MdAPE 후보
    - MAPE 후보
    - p95 후보

### PP-Y10. 불확실성 폭 기반 모델 선택

- 비교 후보:
  - MdAPE 강한 후보: `PP-X3 lightgbm_quantile_exhibition_gallery`
  - MAPE/p95 강한 후보: `PP-W4`, `PP-H9`, `PP-S1`
- 선택 기준:
  - `quantile_width = q90_log - q10_log`
  - `price_range_ratio = exp(q90_log) / exp(q10_log)`
- 실험 이유:
  - LightGBM Quantile이 만든 범위가 넓은 작품은 점 예측 위험이 높을 가능성이 있다.
  - 이 구간에서는 p95 방어 후보로 전환하는 방식이 적합할 수 있다.
- 성공 기준:
  - 안정 구간에서는 MdAPE 개선.
  - 위험 구간에서는 p95 개선.

### PP-Y11. OOF 기반 meta stacking 정식화

- 입력 후보:
  - `PP-W2` CatBoost 작가 메타
  - `PP-W4` LightGBM Quantile/Huger residual
  - `PP-X3` 전시/갤러리 LightGBM Quantile
  - `PP-H9` 검색 LightGBM Quantile
  - `PP-S1` CatBoost Quantile -> Huber
- meta 모델:
  - Ridge
  - Huber
  - 제한된 LightGBM
- 입력 피처:
  - 후보별 `pred_log`
  - 후보 예측값 간 차이
  - quantile width
  - 정보량/품질 flag
- 실험 이유:
  - Cold에서 후보별 장점이 목적별로 분리되어 있어 meta 조합 가치가 높다.
- 주의:
  - 반드시 OOF 예측으로 meta train을 만든다.
  - validation/test 반복 선택을 피한다.
- 성공 기준:
  - MdAPE `0.445` 이하 또는 p95 `3.0` 근처를 유지하면서 MAPE 개선.

## PP-Y12~Y15. 서비스 안정성/보정 정책 실험

### PP-Y12. 전시/갤러리 사용 여부 라우팅

- 목적:
  - 전시/갤러리 피처가 있는 샘플에서만 `PP-X3` 계열을 쓰는 것이 나은지 확인.
- 방식:
  - 전시 정보 있음/없음
  - 갤러리 tier 있음/없음
  - 검증 tier 있음/없음
  - 구간별 최적 후보 비교
- 성공 기준:
  - 전체 성능뿐 아니라 정보 있음 구간에서 명확한 개선.

### PP-Y13. 검색 품질 기반 fallback

- 목적:
  - 검색 품질이 낮은 경우 검색 피처 모델을 쓰지 않고 기존 `PP-W4`로 fallback하는 것이 나은지 확인.
- 방식:
  - 검색 품질 `low/medium/high`
  - 동명이인 위험 flag
  - 검색 source count
- 성공 기준:
  - p95 개선 또는 검색 피처로 인한 MdAPE 악화 방지.

### PP-Y14. 가격대별 목적 모델 분리

- 목적:
  - 저가/중가/고가 예측에서 최적 모델이 다른지 확인.
- 기준:
  - 예측 가격 구간만 사용한다.
  - 실제 가격 구간은 운영 시 알 수 없으므로 보정 기준으로 쓰지 않는다.
- 후보:
  - 저가: MAPE 방어 후보
  - 중가: MdAPE 후보
  - 고가: p95 방어 후보
- 성공 기준:
  - 가격대별 성능 균형 개선.

### PP-Y15. segment 최소 표본 수와 보정 cap 재검증

- 목적:
  - 전시/갤러리/검색 segment 보정이 과보정되는 문제를 줄인다.
- 방식:
  - 최소 표본 수 `30/50/100/150`
  - 보정 cap `0.10/0.15/0.25/0.35`
  - fallback 순서: 세부 segment -> 상위 segment -> 전체
- 성공 기준:
  - validation 개선이 test에서 재현되는지 확인.

## 4. 실행 우선순위

| 우선순위 | 실험 | 이유 |
|---:|---|---|
| 1 | `PP-Y1` | `PP-X3`의 MdAPE 개선 신호를 가장 직접적으로 고도화 |
| 2 | `PP-Y2` | 전시/갤러리 MdAPE 장점과 검색 p95 장점을 결합 |
| 3 | `PP-Y6` | LightGBM Quantile의 강한 1차 예측에 CatBoost residual을 붙이는 미실험 핵심 순서 |
| 4 | `PP-Y3` | CatBoost에는 전시보다 갤러리 단독이 맞는지 Quantile 구조로 재검증 |
| 5 | `PP-Y10` | 점 예측 후보를 서비스 라우팅 후보로 전환할 수 있음 |
| 6 | `PP-Y11` | OOF 기반 meta stacking으로 목적별 후보를 통합 |
| 7 | `PP-Y4` | PP-U3 피처 교환 신호를 LightGBM Quantile/Huber 구조에 재투입 |
| 8 | `PP-Y8` | PP-S1 구조를 외부 피처 품질 기준으로 안정화 |
| 9 | `PP-Y12~Y15` | 서비스 적용 전 fallback/segment/cap 정책 검증 |

## 5. 기대 산출물

- Cold 추가 실험 통합 결과표
- 후보별 목적 분류:
  - 대표 가격 후보
  - 평균 오차 후보
  - 큰 오차 방어 후보
  - 가격 범위/신뢰도 후보
- 피처군별 판단:
  - 작품 구조 피처
  - 작가 메타 피처
  - 전시/갤러리 피처
  - 검색/소셜 피처
  - 피처 품질/가용성 flag
- 모델 순서별 판단:
  - LightGBM Quantile -> CatBoost residual
  - CatBoost Quantile -> LightGBM residual
  - CatBoost Quantile -> Huber residual
  - meta stacking
  - uncertainty routing

## 6. 초기 보고용 한 줄 결론

- Cold는 아직 단일 모델 교체보다 피처군과 모델 역할을 분리한 조합 실험의 여지가 크다.
- 특히 `전시/갤러리로 MdAPE를 낮추는 LightGBM Quantile`, `검색/Huber residual로 p95를 낮추는 후보`, `CatBoost Quantile의 조건 조합 장점`을 OOF 기반으로 결합하는 실험이 다음 우선순위다.

## 7. 1차 실행 업데이트

- 업데이트일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y_cold_combination_experiments.py`
- 실행 결과 파일: `experiments/track6/PP-Y_cold_combination_summary_metrics.csv`
- 실행 요약 문서: `docs/track6/experiments/pp_y_cold_combination_execution_summary.md`

| 실험 | 실행 상태 | best test 결과 | 판단 |
|---|---|---|---|
| `PP-Y1` | 실행 완료 | `lgbq_meta_external_core` MdAPE `0.4444`, MAPE `1.1295`, p95 `3.8496` | 전시/갤러리 개선 신호 재현 |
| `PP-Y2` | 실행 완료 | `lgbq_search_all_external_interaction` MdAPE `0.4421`, MAPE `1.0484`, p95 `3.3537` | 강한 단일 모델 후보 |
| `PP-Y3` | 실행 완료 | `catq_meta_baseline` MdAPE `0.4671`, MAPE `1.0586`, p95 `3.8201` | CatBoost Quantile 단독은 보류 |
| `PP-Y6` | 실행 완료 | `lgbq_search_external_interaction_catboost_oof_cap0.15_s1` MdAPE `0.4327`, MAPE `1.0514`, p95 `3.8486` | 대표 정확도 개선 후보, p95 보완 필요 |
| `PP-Y7` | 실행 완료 | `base_catq_gallery_search_quality` MdAPE `0.4834`, MAPE `1.1041`, p95 `3.6239` | test 재현성 부족, 보류 |
| `PP-Y8` | 실행 완료 | `base_catq_gallery_search_quality` MdAPE `0.4834`, MAPE `1.1041`, p95 `3.6239` | 품질 cap residual 효과 약함, 보류 |
| `PP-Y10` | 실행 완료 | MdAPE 후보 `0.4302`, p95 후보 `2.9656` | 가장 유망한 라우팅 후보, OOF threshold 재검증 필요 |

1차 실행 결과 기준으로 남은 축은 `PP-Y4/Y5/Y9/Y11/Y12~Y15`였고, 이를 closure 실험으로 추가 실행했다.

## 8. closure 실행 업데이트

- 업데이트일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y_closure_experiments.py`
- closure 결과 파일: `experiments/track6/PP-Y_closure_summary_metrics.csv`
- 통합 결과 파일: `experiments/track6/PP-Y_cold_combination_summary_metrics.csv`
- 실행 요약 문서: `docs/track6/experiments/pp_y_cold_closure_execution_summary.md`

| 실험 | 실행 상태 | best test 결과 | 판단 |
|---|---|---|---|
| `PP-Y4` | 실행 완료 | best MdAPE `0.4460`, best p95 `3.6262` | LightGBM 피처 교환/목적함수 변경은 기존 상위 후보보다 약해 보류 |
| `PP-Y5` | 실행 완료 | best MAPE `1.0338`, best p95 `2.9656` | 피처 품질 기반 라우팅은 MAPE/p95 보조 정책으로 유지 |
| `PP-Y9` | 실행 완료 | best MAPE `1.0357` | MAPE 목적 참고 후보이나 대표 정확도 균형은 약함 |
| `PP-Y11` | 실행 완료 | best MdAPE `0.4560` | validation meta stacking은 개선 부족, 보류 |
| `PP-Y12` | 실행 완료 | best MdAPE `0.4344` | 전시/갤러리 정보 가용 여부 기반 서비스 라우팅 후보 |
| `PP-Y13` | 실행 완료 | best p95 `2.9656` | 검색 품질 fallback 보조 후보 |
| `PP-Y14` | 실행 완료 | best MdAPE `0.4344`, best MAPE `1.0478` | 예측 가격대별 모델 선택은 서비스 정책 후보 |
| `PP-Y15` | 실행 완료 | best MdAPE `0.4245`, 균형 `0.4337/1.0467/2.9371`, best p95 `2.8025` | 탐색상 최고 후보, PP-Y16에서 OOF 고정 재검증 |

## 9. closure 후 판단

- Cold 추가 실험의 남은 핵심 축은 대부분 확인했다.
- 새로운 조합을 계속 늘리기보다 `PP-Y15`에서 확인된 segment 최소 표본 수/cap 보정을 validation 또는 OOF 기준으로 고정해 재검증하는 단계가 우선이다.
- 목적별 후보는 아래와 같이 분리한다.

| 목적 | 후보 | 이유 |
|---|---|---|
| 대표 정확도 | `PP-Y15 external_x_qwidth_min30_cap0.1` | test MdAPE `0.4245` |
| 균형 후보 | `PP-Y15 pred_x_qwidth_min50_cap0.25` | MdAPE `0.4337`, MAPE `1.0467`, p95 `2.9371` |
| 큰 오차 방어 | `PP-Y15 pred_x_qwidth_min150_cap0.35` | p95 `2.8025` |

## 10. OOF 고정 재검증 업데이트

- 업데이트일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y15_oof_fixed_revalidation.py`
- 실행 결과 폴더: `experiments/track6/PP-Y16_cold_y15_oof_fixed_revalidation`
- 실행 요약 문서: `docs/track6/experiments/pp_y15_oof_fixed_revalidation_summary.md`

| 선택 기준 | 선택 후보 | Validation OOF | Test 결과 | 판단 |
|---|---|---|---|---|
| MdAPE/MAPE/균형 | `pred_x_qwidth_oof_min30_cap0.35` | MdAPE `0.3501`, MAPE `0.5358`, p95 `1.4493` | MdAPE `0.4438`, MAPE `1.1083`, p95 `2.8025` | 대표 정확도는 유지/소폭 악화, p95 방어는 강함 |
| p95 | `pred_x_qwidth_oof_min30_cap0.15` | MdAPE `0.3701`, MAPE `0.5517`, p95 `1.3791` | MdAPE `0.4382`, MAPE `1.0981`, p95 `3.3512` | MdAPE는 소폭 개선, p95 방어는 재현 약함 |

- `PP-Y15`의 test 최고 MdAPE `0.4245`는 validation OOF 선택 기준으로는 최종 채택하기 어렵다.
- `PP-Y16` 기준으로는 segment/cap 보정이 대표 가격 정확도 개선보다 큰 오차 방어에 더 적합하다고 해석한다.

## 11. 최종 보고용 한 줄 결론

- Cold는 피처 조합, 모델 순서, objective, 라우팅, fallback, segment/cap 보정까지 closure 실험을 확장한 결과 `PP-Y15`에서 test MdAPE `0.4245`, p95 `2.8025` 후보까지 확인됐다.
- 다만 OOF 고정 재검증(`PP-Y16`)에서는 대표 정확도 최고 후보가 재현되지 않았고, p95 방어 후보로는 test p95 `2.8025`가 유지됐다.
- 따라서 Cold 최종 정책은 `PP-Y2`를 대표 가격 기준선으로 두고, `PP-Y16`은 큰 오차 방어 또는 위험 구간 표시 정책으로 분리하는 방향이 적합하다.
