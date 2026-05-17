# Track 4 최종 결과 요약 보고서

- 작성일: 2026-05-17
- 보완일: 2026-05-18
- 목적: 작품 1건의 정보를 보고 가격을 예측하는 Track 4 모델 후보를 정리
- 기준: Warm / Cold를 합치지 않고 분리 평가
- 최종 판단 기준: 성능, 운영 가능성, 설명 가능성, 재현 가능성

## 1. 최종 결론

- Warm은 서비스 후보로 사용할 수 있는 수준의 1차 후보가 만들어졌다.
- 추가 검증에서 Warm 비선형 모델 중 RandomForest가 기존 Ridge 후보보다 좋은 성능을 보였고 artifact 생성까지 완료했다.
- 기존 Warm test가 137건으로 작다는 한계가 있어, 5개 seed 반복 Warm 재검증 split을 추가로 만들고 성능을 다시 확인했다.
- 생성 조합 피처는 최종 모델 기준에서 test 성능을 개선하지 못해 최종 입력 피처로 채택하지 않는다.
- Cold는 단일 가격만 제시하기에는 아직 위험이 크다.
- Cold는 낮은 위험 구간만 가격 범위와 함께 제한적으로 사용하는 방향이 적절하다.
- Warm / Cold는 하나의 모델로 합치기보다 분리해서 운영하는 것이 현재 결과 기준으로 더 안전하다.
- 최종 모델은 입력 작가가 학습 데이터에 있으면 Warm 모델, 없으면 Cold 모델을 사용한다.

## 2. 사용 데이터

- 학습 데이터: `track4_train`
- Warm 평가 데이터: `track4_test_warm`
- Cold 평가 데이터: `track4_test_cold`
- Warm 기준: 입력 작가가 학습 데이터에 등장한 경우
- Cold 기준: 입력 작가가 학습 데이터에 등장하지 않은 경우
- 평가 원칙: Warm / Cold median APE를 따로 기록

## 3. 최종 모델과 피처

### Warm 최종 후보

- 최종 권장 모델: RandomForest
- 기존 artifact 모델: Ridge
- 최종 권장 artifact: `data/track4/models/track4_warm_final_conditional_stats_random_forest.joblib`
- 사용 피처:
  - `artist_key`
  - `artist_works_log`
  - `artist_works_count_train`
  - `artist_train_median_log_price`
  - `artist_train_mean_log_price`
  - `artist_train_iqr_log_price`
  - `medium_category`
  - `support_category`
  - `log_area`
  - `aspect_ratio`
- 조건:
  - 작가 가격 통계 피처는 예측 대상 작품 가격을 포함하면 안 된다.
  - 예측 시점 이전의 학습/거래 데이터로만 계산해야 한다.
  - RandomForest artifact dry-run은 완료되었다.

### Cold 최종 후보

- 모델: Quantile
- artifact: `data/track4/models/track4_cold_final_full_size_quantile.joblib`
- 사용 피처:
  - `medium_category`
  - `width_cm`
  - `height_cm`
  - `log_area`
  - `aspect_ratio`
  - `has_depth`
  - `is_3d_candidate`
- 조건:
  - 작가명, 작가 과거 가격, 작가 이력 피처는 사용하지 않는다.
  - 처음 보는 작가 상황에서도 만들 수 있는 작품 구조 정보만 사용한다.

## 4. 최종 성능

| 구분 | rows | median APE | p95 APE | Within-30% | Within-50% |
|---|---:|---:|---:|---:|---:|
| Warm final RF | 137 | 0.1970 | 0.9219 | 0.6715 | 0.8613 |
| Warm RF repeated recheck 평균 | 534.4 | 0.1687 | 0.9379 | 0.6879 | 0.8313 |
| Warm previous Ridge | 137 | 0.2201 | 1.1118 | 0.6131 | 0.8321 |
| Cold final | 3,277 | 0.4199 | 2.7609 | 0.3699 | 0.5917 |

### Warm 추가 모델 비교 결과

| 후보 | test median APE 평균 | test p95 APE 평균 | 해석 |
|---|---:|---:|---|
| Ridge 기존 artifact | 0.2201 | 1.1118 | 기존 최종 artifact |
| RandomForest 최종 권장 | 0.1970 | 0.9219 | artifact 생성 완료 |
| RandomForest 반복 Warm recheck | 0.1687 ± 0.0103 | 0.9379 ± 0.0379 | 기존 137건 test 보완 검증 |

- median APE는 낮을수록 좋다.
- p95 APE는 큰 오차 구간을 보는 지표이며 낮을수록 좋다.
- Within-30% / Within-50%는 높을수록 좋다.
- Warm 최종 성능은 기존 fixed test 1회 수치와 반복 recheck 평균을 함께 보고한다.

## 5. 구간별 해석

### Warm

| 구간 | rows | median APE | p95 APE | 해석 |
|---|---:|---:|---:|---|
| low_history | 37 | 0.3581 | 1.6149 | 작가 이력이 적어 경고와 넓은 범위 필요 |
| mid_history | 70 | 0.2068 | 0.9422 | 일반 Warm 후보로 사용 가능 |
| high_history | 30 | 0.1889 | 0.8449 | Warm 중 가장 안정적 |

- Warm은 작가 이력이 많을수록 성능이 좋아지는 경향이 있다.
- low_history는 단일 가격만 제시하기보다 신뢰도 경고를 붙이는 것이 안전하다.

### Cold

| 구간 | rows | median APE | p95 APE | 해석 |
|---|---:|---:|---:|---|
| low_risk | 2,738 | 0.4077 | 2.6384 | 제한적 가격 범위 후보 |
| mid_risk | 488 | 0.4274 | 4.1932 | 단일 가격 제시는 위험 |
| high_risk | 51 | 0.5672 | 4.2456 | 강한 경고 또는 보류 필요 |

- Cold는 전체적으로 Warm보다 오차가 크다.
- 특히 mid/high risk는 p95 오차가 커서 서비스에서 단일 가격처럼 보여주면 위험하다.
- Cold는 추가 작가 DB나 외부 이력 데이터가 확보되기 전까지 보수적으로 사용해야 한다.

## 6. 운영 적용 정책

- 라우팅:
  - 입력 작가가 학습 데이터 작가 집합에 있으면 Warm 모델 사용
  - 입력 작가가 학습 데이터 작가 집합에 없으면 Cold 모델 사용
- Warm 출력:
  - low_history: 예측 가격 + 경고 + 넓은 가격 범위
  - mid/high_history: 예측 가격 + 일반 가격 범위
- Cold 출력:
  - low_risk: 예측 가격 + 제한적 가격 범위 + 주의 문구
  - mid/high_risk: 단일 가격 보류 또는 강한 경고
- 금지 피처:
  - 데이터 출처
  - 갤러리명/갤러리 티어
  - URL
  - 이미지 URL
  - 예측 대상 작품의 가격에서 만들어진 값

## 7. 최종 후보를 선택한 근거

- Warm:
  - 작가 가격 통계 피처를 조건부 허용했을 때 성능 개선 폭이 컸다.
  - 보수 후보 대비 median APE가 약 21.69% 개선되었다.
  - p95 APE도 약 56.41% 개선되어 큰 오차 감소 효과가 있었다.
  - 추가 비선형 비교에서 RandomForest가 Ridge보다 test median APE와 p95 APE 모두 개선했다.
- Cold:
  - 범위 폭을 줄이는 실험을 했지만 coverage를 유지하면서 폭을 줄인 후보가 없었다.
  - 따라서 현재는 모델 자체 교체보다 위험 구간 분리 정책이 더 현실적이다.
- 공통:
  - feature manifest 검사를 통과한 피처만 최종 후보로 유지했다.
  - 운영에서 다시 만들 수 없는 피처는 제외했다.
  - `medium_size_bucket`, `support_size_bucket`, 재료-크기 rule flag는 최종 모델 기준에서 성능 개선이 없어 제외했다.

## 8. 재현 방법

- 피처 manifest 검사:
  - `python3 scripts/track4/check_feature_manifest.py`
- Warm 반복 재검증:
  - `python3 scripts/track4/run_t4_e053_warm_recheck_split_revalidation.py`
- 최종 artifact 재생성:
  - `python3 scripts/track4/run_t4_e045_final_artifact_dry_run.py`
- 대시보드 재생성:
  - `python3 scripts/track4/generate_experiment_dashboard.py`

## 9. 남은 리스크

- Warm 작가 가격 통계 피처를 실제 운영 DB에서 같은 방식으로 계산하는 파이프라인이 필요하다.
- Cold 최종 full-size 피처셋 기준 모델군 재비교 결과 Quantile 유지가 확인되었다.
- Cold는 단일 가격 예측 신뢰도가 낮으므로 외부 작가 DB나 이력 데이터 확보가 필요하다.
- 가격 범위 UI는 별도 정책 검증이 필요하다.
- 신규 데이터가 들어오면 같은 split 기준 또는 새 고정 split 기준으로 재검증해야 한다.
- Warm fixed test가 작기 때문에 최종 성능 보고에는 T4-E053 반복 recheck 결과를 함께 사용해야 한다.

## 10. 최종 산출물

- 최종 Warm artifact: `data/track4/models/track4_warm_final_conditional_stats_random_forest.joblib`
- 이전 Warm artifact: `data/track4/models/track4_warm_final_conditional_stats_ridge.joblib`
- 최종 Cold 모델: `data/track4/models/track4_cold_final_full_size_quantile.joblib`
- 최종 결과 JSON: `data/track4/results/t4_e045_final_artifact_dry_run.json`
- 피처 manifest: `configs/track4/feature_manifest.json`
- 실험 대시보드: `docs/track4/dashboard/experiment_dashboard.html`
- Warm 재검증 split: `data/track4_warm_recheck_split/`
