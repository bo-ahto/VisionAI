# PP-V6~PP-V8 Warm 남은 Gap 실행 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_v6_v8_warm_gap_experiments.py`
- 요약 지표: `experiments/track6/PP-V6_V8_warm_gap_summary_metrics.csv`
- 실험 폴더:
  - `experiments/track6/PP-V6_warm_l10_refreshed_fine_blend`
  - `experiments/track6/PP-V7_warm_l10_refreshed_meta_stacking`
  - `experiments/track6/PP-V8_warm_deployment_simplification`

## 1. 실험 목적

- 기존 Warm 최종 후보 `PP-V1/PP-V2`에는 최근 실행한 `PP-L10` 후보가 아직 component로 반영되지 않았다.
- `PP-L10` 단독 후보는 기존 최종 후보를 넘지는 못했지만, 순차 구조와 피처 변형이 달라 조합 안에서는 가중치를 받을 가능성이 있었다.
- 따라서 기존 `PP-V` 조합 구조를 유지하고 `PP-L10` 상위 후보 2개를 추가해 최종 Warm 성능 개선 여부를 확인했다.

## 2. 사용한 신규 component

| component | 원천 실험 | test MdAPE | test MAPE | test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| `l10_meta_external_search_seq` | `PP-L10 l8_seq__warm_base_meta_external_search_all` | 0.1708 | 0.3363 | 1.1432 | MdAPE 기준 PP-L10 내부 최고 |
| `l10_generated_bucket_seq` | `PP-L10 l8_seq__full_plus_generated_buckets` | 0.1743 | 0.3265 | 0.9818 | PP-L10 내부 MAPE/p95 균형 후보 |

## 3. Test 핵심 결과

| 후보 | MdAPE | MAPE | p95_APE | 판단 |
|---|---:|---:|---:|---|
| 기존 `PP-V1 fine_blend_mape_guarded` | 0.1621 | 0.3044 | 1.0335 | 기존 Warm 대표 후보 |
| 기존 `PP-V2 huber_component_range_clipped` | 0.1680 | 0.2873 | 0.9287 | 기존 MAPE/p95 방어 후보 |
| `PP-V6 fine_blend_mape_guarded` | 0.1613 | 0.2889 | 0.9314 | 대표 후보 개선 |
| `PP-V7 huber_component_range_clipped` | 0.1712 | 0.2803 | 0.8990 | MAPE/p95 방어는 개선, MdAPE 악화 |
| `PP-V8 compact_blend_mape_guarded` | 0.1632 | 0.2816 | 0.9311 | 배포 단순화 후보 |

## 4. 해석

- `PP-V6 fine_blend_mape_guarded`는 기존 대표 후보 대비 MdAPE, MAPE, p95_APE가 모두 개선됐다.
- `PP-L10` 후보는 단독으로는 최종 후보보다 약했지만, 조합 안에서는 validation에서 가중치를 받았다.
- `PP-V6`의 validation 선택 가중치에서 `l10_meta_external_search_seq`와 `l10_generated_bucket_seq`가 각각 0.2씩 들어갔다.
- 이는 Warm에서 `PP-L10` 피처 변형이 단독 모델 교체용은 아니지만, 기존 후보의 약한 구간을 보완하는 component로는 의미가 있음을 보여준다.
- `PP-V7`은 MdAPE가 0.1712로 악화되어 대표 후보로 쓰기는 어렵지만, MAPE 0.2803, p95 0.8990으로 방어 목적 후보로는 의미가 있다.
- `PP-V8 compact_blend_mape_guarded`는 4개 component만 사용하면서 MAPE 0.2816, p95 0.9311을 만들었다. 서비스 배포 복잡도를 줄이면서 성능을 유지하는 후보로 볼 수 있다.

## 5. 결론

- Warm 대표 후보는 기존 `PP-V1`에서 `PP-V6 fine_blend_mape_guarded`로 교체 검토할 가치가 있다.
- Warm 평균오차/큰오차 방어 후보는 `PP-V2`와 `PP-V7`, `PP-V8`을 함께 비교한다.
- 운영 단순화가 중요하면 `PP-V8 compact_blend_mape_guarded`가 가장 실용적인 후보가 될 수 있다.
- 후속으로는 `PP-V6`과 `PP-V8`의 bootstrap 안정성 또는 최종 API 산출물 기준 재현성 확인이 필요하다.
