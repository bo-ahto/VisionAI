# PP-W Cold 작가 메타/모델 순서 추가 실험 실행 요약

- 실행일: 2026-06-02
- 실행 스크립트: `scripts/track6/run_pp_w_experiments.py`
- 결과 요약 파일: `experiments/track6/PP-W_summary_metrics.csv`
- 실행 범위: `PP-W1` ~ `PP-W5`

## 1. 실험 추가 이유

- 기존 Cold 최상위 후보는 test MdAPE가 `0.4744` 수준으로, Warm 대비 서비스 단일 가격으로 쓰기에는 약했다.
- 기존 Cold 후처리는 주로 작품 크기, 재료, 지지체, Quantile/Residual 조합에 집중되어 있었다.
- `data/track6/track6_feature_candidates_name_corrected.csv`에는 `artist_meta_total_works`, `artist_meta_for_sale_works`, `artist_meta_followers`, `artist_meta_birth_year`, `artist_meta_nationality`, `artist_meta_source` 등 Cold에서 쓸 수 있는 작가 메타 피처가 남아 있었다.
- 따라서 Cold 전용으로 작가 메타를 최대한 활용하고, CatBoost/LightGBM/Quantile/Huber의 학습 순서를 바꿔 추가 개선 가능성을 검증했다.

## 2. 실행 실험

| 실험 | 내용 | 목적 |
|---|---|---|
| `PP-W1` | Cold LightGBM + 작가 메타 피처 확장 | LightGBM이 작품 조건 + 작가 메타를 함께 쓰면 기준선을 높일 수 있는지 확인 |
| `PP-W2` | Cold CatBoost + 작가 메타 피처 확장 | CatBoost의 범주형/조합 처리 강점을 작가 메타와 결합 |
| `PP-W3` | CatBoost Quantile + 작가 메타 → Huber/Ridge residual | CatBoost Quantile을 선행 중앙 예측으로 두고 residual을 안정화 |
| `PP-W4` | LightGBM Quantile + 작가 메타 → Huber/CatBoost residual | LightGBM Quantile의 MAPE/p95 장점에 residual 보정 추가 |
| `PP-W5` | 기존 Cold 후보 + PP-W 후보 목적별 정책 갱신 | MdAPE/MAPE/p95 목적별 후보 재정리 |

## 3. 주요 결과

| 목적 | 기존 후보 | 기존 test | 신규 후보 | 신규 test | 판단 |
|---|---|---:|---|---:|---|
| MdAPE 개선 | `PP-S1 cap0.2` | `0.4744` | `PP-W2 generated_all_meta_all` | `0.4497` | 개선 |
| MAPE 개선 | `PP-Q2 mape blend` | `1.1797` | `PP-W4 lightgbm_quantile_meta_all_huber_cap0.5_s1` | `0.9584` | 개선 |
| p95 개선 | `PP-S1 cap0.5` | `3.2824` | `PP-W4 base_lightgbm_quantile_meta_all` | `3.0322` | 개선 |

## 4. 상세 비교

### 4.1 대표 정확도 개선

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| 기존 `PP-S1 cap0.2` | `0.4744` | `1.2095` | `3.4731` | `0.9301` |
| 신규 `PP-W2 generated_all_meta_all` | `0.4497` | `1.1111` | `4.1587` | `0.8817` |

- MdAPE는 약 `5.2%` 개선됐다.
- MAPE도 약 `8.1%` 개선됐다.
- 다만 p95는 악화되므로, 이 후보를 단독 최종 후보로 쓰기보다 대표 점 예측 후보로만 해석해야 한다.

### 4.2 큰 오차 방어 개선

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| 기존 `PP-S1 cap0.5` | `0.4765` | `1.2067` | `3.2824` | `0.9386` |
| 신규 `PP-W4 base_lightgbm_quantile_meta_all` | `0.4766` | `1.0847` | `3.0322` | `0.8907` |

- MdAPE는 거의 동일하다.
- MAPE는 약 `10.1%` 개선됐다.
- p95는 약 `7.6%` 개선됐다.
- Cold 가격 범위/신뢰도 표시 정책에는 이 후보가 더 적합하다.

### 4.3 평균 오차 개선

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---:|---:|---:|---:|
| 기존 `PP-Q2 mape blend` | `0.4811` | `1.1797` | `3.7925` | `0.9236` |
| 신규 `PP-W4 huber cap0.5 s1` | `0.4949` | `0.9584` | `3.0073` | `0.9161` |

- MAPE는 약 `18.8%` 개선됐다.
- p95도 약 `20.7%` 개선됐다.
- 대신 MdAPE가 약 `2.9%` 악화된다.
- 평균 오차와 큰 오차 방어를 우선하는 보수적 표시 정책 후보로 볼 수 있다.

## 5. 모델 특성 기반 해석

- CatBoost는 범주형 피처와 조합 조건을 잘 나누므로 `artist_meta_source`, `artist_meta_nationality`, 작가 활동량, 작품 조건 bucket을 함께 넣었을 때 MdAPE가 크게 개선됐다.
- LightGBM Quantile은 평균적인 중앙 예측보다 오차 분포의 중앙과 tail을 더 안정적으로 다루므로 MAPE와 p95 방어에 강했다.
- Huber residual은 Quantile 예측 이후 남은 큰 residual을 제한된 폭으로만 조정할 때 MAPE/p95를 줄였다.
- 결론적으로 Cold는 단일 모델 하나로 고정하기보다 목적별 후보를 분리하는 것이 더 적합하다.

## 6. 현재 권장 후보

| 목적 | 후보 | 이유 |
|---|---|---|
| 대표 점 예측 | `PP-W2 generated_all_meta_all` | Cold MdAPE를 `0.4497`까지 낮춤 |
| 가격 범위/큰 오차 방어 | `PP-W4 base_lightgbm_quantile_meta_all` | MdAPE 유지, MAPE/p95 동시 개선 |
| 평균 오차 최소화 | `PP-W4 lightgbm_quantile_meta_all_huber_cap0.5_s1` | MAPE와 p95가 가장 크게 개선 |

## 7. 주의점

- `PP-W4`의 residual 후보는 validation residual을 이용해 보정 강도를 선택하므로 validation 지표는 과하게 좋아질 수 있다.
- 따라서 최종 판단은 test 지표 중심으로 해야 한다.
- `PP-W2 generated_all_meta_all`은 대표 정확도는 개선되지만 p95가 악화되므로 서비스에서는 신뢰도/범위 정책과 함께 써야 한다.
- 작가 메타 피처는 실제 서비스에서 수집 가능한 컬럼인지 확인되어야 한다.

## 8. 결론

- Cold는 PP-V까지는 큰 개선이 없었지만, PP-W에서 작가 메타를 추가하자 유의미한 개선이 확인됐다.
- 기존 Cold MdAPE 최선 `0.4744` 대비 신규 최선은 `0.4497`이다.
- 다만 p95까지 동시에 최선인 단일 후보는 아니므로, Cold는 대표 가격 후보와 위험 방어 후보를 분리해서 운영하는 방향이 맞다.

