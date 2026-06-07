# PP-V 후속 정확도 개선 실험 실행 요약

- 실행일: 2026-06-02
- 실행 스크립트: `scripts/track6/run_pp_v_experiments.py`
- 결과 요약 파일: `experiments/track6/PP-V_summary_metrics.csv`
- 실행 범위: `PP-V1` ~ `PP-V5`

## 1. 실행 상태

- 최근 중단 원인은 실험 계산 실패가 아니라 보고서 생성 단계의 `tabulate` 의존성 누락이었다.
- `pandas.DataFrame.to_markdown()` 호출이 `tabulate` 미설치 환경에서 실패했다.
- 스크립트에 자체 Markdown table renderer를 추가해 외부 의존성 없이 실행되도록 수정했다.
- 수정 후 `PP-V1` ~ `PP-V5` 전체 실행을 완료했다.

## 2. 생성 산출물

| 실험 | 결과 폴더 |
|---|---|
| `PP-V1` | `experiments/track6/PP-V1_warm_ppu_feature_augmented_fine_blend` |
| `PP-V2` | `experiments/track6/PP-V2_warm_ppu_feature_augmented_meta_stacking` |
| `PP-V3` | `experiments/track6/PP-V3_cold_ppu_feature_augmented_fine_blend` |
| `PP-V4` | `experiments/track6/PP-V4_cold_ppu_feature_augmented_meta_stacking` |
| `PP-V5` | `experiments/track6/PP-V5_objective_policy_refresh` |

각 실험 폴더에는 `outputs/metrics.csv`, `outputs/predictions.csv`, `outputs/policy_map.csv`, `reports/result_report.md`, `reports/result_report.html`이 생성됐다.

## 3. Warm 결과

| 후보 | test MdAPE | test MAPE | test p95_APE | 판단 |
|---|---:|---:|---:|---|
| `PP-V1 fine_blend_mape_guarded` | `0.1621` | `0.3044` | `1.0335` | 기존 `PP-T1 fine_blend_mape_guarded`와 동일 수준. 대표 점 예측 후보 유지 |
| `PP-V1 fine_blend_mdape` | `0.1668` | `0.3067` | `0.9580` | 기존 `PP-T1 fine_blend_mdape`와 동일 수준. MdAPE/p95 균형 후보 |
| `PP-V2 huber_component_range_clipped` | `0.1680` | `0.2873` | `0.9287` | Warm 평균 오차와 큰 오차 방어에서 추가 개선 확인 |

### Warm 해석

- `PP-U1`의 생성 bucket 후보를 fine blend에 추가했지만, 선택된 validation 가중치에서 `u1_full_generated`, `u1_artist_size_works`의 직접 가중치는 0이었다.
- 즉 생성 bucket 피처는 단독 test 개선 가능성은 있었지만, 기존 `PP-T1` 조합 안에서는 추가 가중치를 받을 만큼 안정적인 신호로 선택되지는 않았다.
- 반면 `PP-V2`의 Huber meta stacking은 후보 예측값 사이의 차이를 다시 안정적으로 조정하면서 MAPE와 p95를 낮췄다.
- Warm 운영 관점에서는 대표 가격은 `PP-T1/PP-V1 fine_blend_mape_guarded`, 큰 오차 방어 또는 평균 오차 최소화는 `PP-V2 huber_component_range_clipped`를 같이 검토할 가치가 있다.

## 4. Cold 결과

| 후보 | test MdAPE | test MAPE | test p95_APE | 판단 |
|---|---:|---:|---:|---|
| 기존 `PP-S1 cap0.2` | `0.4744` | `1.2095` | `3.4731` | Cold MdAPE 최저 후보 유지 |
| 기존 `PP-S1 cap0.5` | `0.4765` | `1.2067` | `3.2824` | Cold p95 방어 최저권 유지 |
| 기존 `PP-Q2 mape blend` | `0.4811` | `1.1797` | `3.7925` | Cold MAPE 목적 후보 유지 |
| `PP-V4 huber_component_range_clipped` | `0.4771` | `1.2207` | `3.6200` | 신규 meta 후보이나 기존 PP-S1/PP-S4보다 약함 |
| `PP-V3 fine_blend_p95_guarded` | `0.4771` | `1.2073` | `3.4092` | p95는 개선됐지만 기존 `PP-S1 cap0.5`보다 약함 |
| `PP-V3 fine_blend_mape_guarded` | `0.4796` | `1.2148` | `3.4131` | MAPE 목적에서도 기존 `PP-Q2`보다 약함 |

### Cold 해석

- `PP-U3`/`PP-U4`의 피처 교환 후보를 기존 Cold 상위 후보 조합에 넣었지만, test 기준으로 기존 `PP-S1`, `PP-S4`, `PP-Q2`를 넘지는 못했다.
- validation에서는 `PP-V3`/`PP-V4`가 선택되는 구간이 있었지만, test에서는 재현성이 제한적이었다.
- 따라서 Cold는 현재 기준에서 새 PP-V 조합으로 교체하지 않고, 기존 목적별 후보를 유지하는 것이 안전하다.

## 5. 목적별 운영 후보 갱신

| 목적 | Warm 후보 | Cold 후보 |
|---|---|---|
| 대표 점 예측 | `PP-T1/PP-V1 fine_blend_mape_guarded` | `PP-S1 n2_catboost_quantile_huber_cap0.2_s1` |
| 평균 오차 최소화 | `PP-V2 huber_component_range_clipped` | `PP-Q2 weighted_blend_mape_objective` |
| 큰 오차 방어 | `PP-V2 huber_component_range_clipped` 또는 `PP-T1/PP-V1 fine_blend_mdape` | `PP-S1 n2_catboost_quantile_huber_cap0.5_s1` 또는 `PP-S4 huber_crossfit_component_range_clipped` |

## 6. 결론

- `PP-V`는 실행 완료됐다.
- Warm에서는 `PP-V2 huber_component_range_clipped`가 기존 `PP-T2` 대비 MAPE와 p95를 추가 개선했다.
- Warm 대표 점 예측은 여전히 `PP-T1/PP-V1 fine_blend_mape_guarded`가 가장 좋다.
- Cold에서는 신규 PP-V 조합이 기존 최상위 후보를 대체하지 못했다.
- Cold는 목적별로 `PP-S1 cap0.2`, `PP-S1 cap0.5`, `PP-Q2`, `PP-S4`를 유지하는 것이 현재 가장 안전하다.

