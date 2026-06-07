# PP-H12~H18 검색 신뢰도/q-width 후속 실행 요약

- 실행일: 2026-06-03
- 목적: PP-H11에서 만든 운영형 검색 피처를 실제 Cold 예측 후처리 정책에 연결할 수 있는지 확인한다.
- 결론: 검색 피처는 점 예측 직접 입력보다 `작가 검색 신뢰도`, `가격 범위`, `q-width 잔차 보정`에 사용하는 편이 더 적합하다.

## 1. PP-H12 작가 일치/동명이인 판정

### 실행 내용

- 입력: PP-H11 최신 snapshot과 표준 검색 결과
- 검색 결과 row: 2,000건
- 작가 수: 80명
- 산출물:
  - `search_result_auto_labels.csv`
  - `artist_match_review_queue.csv`
  - `manual_review_template.csv`

### 결과

| 구분 | 수치 | 해석 |
|---|---:|---|
| `match_artist` 검색 결과 | 719건 | 작가명과 미술/전시/시장 문맥이 함께 확인됨 |
| `partial_match` 검색 결과 | 479건 | 일부 문맥은 맞지만 수동 검수 필요 |
| `irrelevant` 검색 결과 | 786건 | 무관 결과 가능성 높음 |
| `homonym` 검색 결과 | 16건 | 동명이인 위험 |
| H14/H18 후보 작가 | 37명 | 검색 피처를 신뢰도/범위/q-width 보정에 제한적으로 사용 가능 |
| 수동 검수 또는 제외 작가 | 43명 | 점 예측 직접 투입 보류 |

해석:

- H11의 `medium` 등급 37명은 H12에서도 `candidate_for_h14_h18`로 분리됐다.
- 나머지 43명은 검색 결과가 있어도 작가 본인 여부가 약하거나 무관 결과가 많아 점 예측 피처로 직접 넣기 어렵다.

## 2. PP-H14 검색 신뢰도 기반 가격 범위

### 기준

- 기준 예측: `PP-Y2 lgbq_search_all_external_interaction`
- 기준 가격 범위: LightGBM Quantile의 `q10_log`~`q90_log`
- 보완 방식:
  - 단순 배율 range
  - validation 기준 conformal buffer range

### Test 결과

| 후보 | range coverage | median range ratio | 해석 |
|---|---:|---:|---|
| 기존 q10~q90 범위 | 0.6089 | 3.8452 | 포함률 부족 |
| 단순 배율 정책 | 0.7541 | 7.3457 | 포함률 개선, 등급별 안정성은 약함 |
| conformal80 | 0.7899 | 7.6368 | 80% 목표에 가장 가까움 |
| conformal90 | 0.8751 | 11.3506 | 포함률은 높지만 범위가 넓음 |

해석:

- 서비스 표시용 가격 범위는 고정 배율보다 validation conformal 방식이 더 타당하다.
- `conformal80`은 포함률 78.99%로 80% 목표에 가깝고, 범위 폭도 `conformal90`보다 덜 과도하다.
- `conformal90`은 보수적 표시에는 가능하지만 범위가 넓어 서비스 UX에서 과하게 보일 수 있다.

## 3. PP-H18 q-width x 검색 신뢰도 잔차 보정

### 기준

- 기준 모델: `PP-Y2 lgbq_search_all_external_interaction`
- 보정 기준:
  - validation `quantile_width_log` 33/66 분위로 `stable/caution/risk` 구간 정의
  - H12 추천 액션과 q-width bin을 결합해 segment 생성
  - validation segment별 `median residual_log`를 보정값으로 사용
  - test에는 validation에서 만든 보정맵만 적용

### Test 전체 결과

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 해석 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| H18 best `min80_cap0.2` | 0.4239 | 1.0328 | 3.0077 | 0.8598 | MdAPE/MAPE/p95 개선, RMSE_log 소폭 악화 |

개선폭:

| 지표 | 변화 |
|---|---:|
| MdAPE | -0.0183 |
| MAPE | -0.0156 |
| p95_APE | -0.3460 |
| RMSE_log | +0.0031 |

해석:

- 검색 신뢰도와 q-width를 결합한 segment 보정은 Cold 대표 정확도와 큰 오차 방어를 동시에 개선하는 신호가 있다.
- 다만 H12 라벨이 아직 자동 판정이므로, 최종 채택 전 수동 검수 라벨 기반 재실행이 필요하다.
- 결과가 기존 PP-Y18의 좋은 후보와 유사한 수준까지 올라왔으므로, PP-H 검색 피처는 “점 예측 직접 입력”이 아니라 “불확실성 기반 보정축”으로 쓰는 방향이 맞다.

## 4. PP-H12B 보수 라벨 보정

### 실행 내용

- 입력: PP-H12 자동 판정 결과
- 목적: Naver 검색 UI/프로필/결제/무관 링크처럼 운영 피처로 쓰기 어려운 결과를 더 보수적으로 제외한다.
- 성격: 사람이 최종 검수한 라벨은 아니며, 수동 검수 전 단계의 보수 자동 라벨이다.
- 산출물:
  - `experiments/track6/PP-H12B_search_match_review_label_refinement/outputs/artist_match_review_queue_refined.csv`
  - `experiments/track6/PP-H12B_search_match_review_label_refinement/reports/result_report.html`

### 결과

| 구분 | H12 자동 라벨 | H12B 보수 라벨 | 해석 |
|---|---:|---:|---|
| H14/H18 후보 작가 | 37명 | 31명 | 노이즈 가능성이 있는 작가 6명을 후보에서 제외 |
| 수동 검수/신뢰도 보조 | 21명 | 21명 | 불확실한 작가는 유지 |
| 점 예측 직접 사용 보류 | 22명 | 28명 | 보수 라벨에서 제외 대상 증가 |

검색 결과 row 기준 라벨은 다음과 같이 바뀌었다.

| 라벨 | 결과 수 | 해석 |
|---|---:|---|
| `match_artist` | 715 | 작가 본인과 미술 문맥이 비교적 명확한 결과 |
| `partial_match` | 116 | 일부 정보는 맞지만 수동 확인 필요 |
| `irrelevant` | 1,153 | UI 링크/무관 결과/검색 노이즈 가능성 |
| `homonym` | 16 | 동명이인 위험 |

해석:

- H12B는 검색 피처를 더 엄격하게 쓰기 위한 안전장치다.
- 자동 H12에서 후보였던 일부 작가는 수동 검수 또는 제외 대상으로 이동했다.
- 최종 운영 적용 전에는 H12B도 사람 검수를 대체할 수 없으며, `manual_review_template.csv` 기반 최종 라벨이 필요하다.

## 5. H12B 기반 PP-H14/H18 재실행

### H14 가격 범위

| 후보 | H12 자동 라벨 coverage | H12B 보수 라벨 coverage | H12B median range ratio | 해석 |
|---|---:|---:|---:|---|
| 기존 q10~q90 | 0.6089 | 0.6089 | 3.8452 | 기준 범위는 동일 |
| 단순 배율 정책 | 0.7541 | 0.7573 | 7.3457 | 보수 라벨에서도 유사 |
| `conformal80` | 0.7899 | 0.7861 | 7.0679 | 포함률은 약간 낮지만 범위는 더 좁음 |
| `conformal90` | 0.8751 | 0.8758 | 11.2632 | 보수 범위 후보 |

해석:

- H12B로 후보 작가를 줄여도 H14 가격 범위 정책은 유지된다.
- `conformal80`은 H12 자동 라벨보다 coverage가 약간 낮지만 median range ratio가 줄어 서비스 표시 범위 측면에서는 더 실용적이다.

### H18 q-width x 검색 신뢰도 보정

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 해석 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `min80_cap0.2` | 0.4253 | 1.0471 | 3.0077 | 0.8621 | MdAPE 최우선 후보 |
| `min30_cap0.2` | 0.4347 | 0.9602 | 3.0077 | 0.8437 | MAPE/RMSE 균형 후보 |
| `min30_cap0.1` | 0.4316 | 0.9832 | 3.0077 | 0.8504 | 보정 강도 낮춘 안정 후보 |

해석:

- MdAPE만 보면 `min80_cap0.2`가 가장 좋다.
- MAPE와 RMSE_log까지 함께 보면 `min30_cap0.2`가 더 균형적이다.
- p95_APE는 주요 후보 모두 3.3537에서 3.0077로 개선되어 큰 오차 방어 신호는 유지된다.

## 6. PP-H19 보정 안정성 검증

### 실행 내용

- 목적: H18 후보가 특정 test 표본에서만 우연히 좋아진 것인지 확인한다.
- 기준 모델: `PP-Y2 lgbq_search_all_external_interaction`
- 입력 결과: H12B 기반 H14/H18 산출물
- 방법:
  - row bootstrap 600회: 작품 row를 다시 뽑아 개별 작품 단위 안정성을 확인
  - artist bootstrap 600회: 작가 단위로 다시 뽑아 특정 작가 구성에 민감한지 확인
  - delta 계산: `기준 모델 점수 - 보정 후보 점수`
  - MdAPE/MAPE/p95_APE/RMSE_log는 delta가 양수일수록 보정 후보가 좋다.
- 산출물:
  - `experiments/track6/PP-H19_search_qwidth_policy_stability/outputs/bootstrap_summary.csv`
  - `experiments/track6/PP-H19_search_qwidth_policy_stability/reports/result_report.html`

### 핵심 결과

| 후보 | 기준 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | RMSE 개선확률 | 판단 |
|---|---|---:|---:|---:|---:|---|
| `min30_cap0.1` | row | 0.9650 | 1.0000 | 1.0000 | 1.0000 | 작품 단위 매우 안정 |
| `min30_cap0.1` | artist | 0.8517 | 1.0000 | 0.9650 | 0.7600 | 작가 단위도 비교적 안정 |
| `min30_cap0.2` | row | 0.9050 | 1.0000 | 1.0000 | 1.0000 | MAPE/RMSE 개선 강함 |
| `min30_cap0.2` | artist | 0.7317 | 0.9417 | 0.8467 | 0.7583 | 작가 구성에 다소 민감 |
| `min80_cap0.2` | row | 1.0000 | 0.6233 | 0.9650 | 0.0000 | MdAPE는 안정, RMSE는 악화 |
| `min80_cap0.2` | artist | 0.9383 | 0.5400 | 0.5467 | 0.2100 | MdAPE 외 지표는 불안정 |

해석:

- `min80_cap0.2`는 MdAPE 개선 후보로는 유효하지만, 평균 오차와 RMSE가 안정적으로 좋아졌다고 보기 어렵다.
- `min30_cap0.2`는 MAPE/RMSE를 낮추는 힘이 가장 강하지만, 작가 단위 MdAPE 개선 확률이 0.7317로 상대적으로 낮다.
- `min30_cap0.1`은 개선 폭은 더 작지만 row/artist 기준 모두에서 MAPE와 p95 개선이 안정적이다.
- 운영 후보는 `min30_cap0.1`을 안전안으로 두고, 실험 후보는 `min30_cap0.2`와 `min80_cap0.2`를 목적 지표별로 분리해서 유지하는 것이 맞다.

## 7. 운영 적용 판단

| 항목 | 판단 |
|---|---|
| 검색 수집 | 가능 |
| 검색 결과 표준화 | 가능 |
| 작가 일치 자동 판정 | 1차 가능, 최종은 수동 검수 필요 |
| 점 예측 직접 입력 | 보류 |
| 가격 범위 표시 | H12B 기반 `conformal80` 후보 |
| q-width 보정 안전안 | H12B 기반 `H18 min30 cap0.1` |
| q-width 보정 공격안 | H12B 기반 `H18 min30 cap0.2` 또는 `min80 cap0.2` |
| 서비스 confidence | `medium/low` 2단계부터 시작 권장 |

## 8. 다음 작업

- `manual_review_template.csv`에 사람이 `match_artist`, `partial_match`, `homonym`, `irrelevant` 라벨을 채운다.
- 수동 라벨 반영 후 H12B threshold를 다시 보정한다.
- H18 `min30_cap0.1`, `min30_cap0.2`, `min80_cap0.2`를 수동 라벨 기반으로 재실행한다.
- PP-H19 bootstrap 안정성 검증도 수동 라벨 기반으로 다시 수행한다.
- H14 `conformal80` 가격 범위 정책을 서비스 API 응답 필드와 연결한다.
- Naver 공식 API 키가 준비되면 `naver_api_webkr` provider로 H11을 재수집하고 HTML 폴백 결과와 비교한다.

## 9. 주요 산출물

| 산출물 | 경로 |
|---|---|
| H12 리포트 | `experiments/track6/PP-H12_search_match_disambiguation_review/reports/result_report.html` |
| H12 수동 검수 템플릿 | `experiments/track6/PP-H12_search_match_disambiguation_review/outputs/manual_review_template.csv` |
| H14/H18 리포트 | `experiments/track6/PP-H14_H18_search_confidence_qwidth_policy/reports/result_report.html` |
| H14/H18 metrics | `experiments/track6/PP-H14_H18_search_confidence_qwidth_policy/outputs/metrics.csv` |
| H14 conformal buffer | `experiments/track6/PP-H14_H18_search_confidence_qwidth_policy/outputs/conformal_range_buffers.csv` |
| H18 best predictions | `experiments/track6/PP-H14_H18_search_confidence_qwidth_policy/outputs/h18_best_corrected_predictions.csv` |
| H12B 리포트 | `experiments/track6/PP-H12B_search_match_review_label_refinement/reports/result_report.html` |
| H12B 작가 큐 | `experiments/track6/PP-H12B_search_match_review_label_refinement/outputs/artist_match_review_queue_refined.csv` |
| H12B 기반 H14/H18 리포트 | `experiments/track6/PP-H14_H18_search_confidence_qwidth_policy_h12b/reports/result_report.html` |
| H19 안정성 리포트 | `experiments/track6/PP-H19_search_qwidth_policy_stability/reports/result_report.html` |
| H19 bootstrap summary | `experiments/track6/PP-H19_search_qwidth_policy_stability/outputs/bootstrap_summary.csv` |
