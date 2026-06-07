# PP-Z Warm Cold형 피처/모델 확장 실험 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_z_warm_coldstyle_extension_experiments.py`
- 요약 지표: `experiments/track6/PP-Z_warm_coldstyle_extension_summary_metrics.csv`
- 목적: Cold에서 검증한 작가 메타, 전시/갤러리, 검색 피처와 LightGBM Quantile/CatBoost 모델 축을 Warm에도 적용하면 기존 Warm 후보보다 성능을 더 올릴 수 있는지 확인한다.

## 1. 기존에 이미 있던 Warm 관련 실험

| 실험 | 내용 | 결론 |
|---|---|---|
| `PP-U1` | Warm Huber 피처 교환/축소/확장 | `full_plus_generated_buckets` test MdAPE `0.2131`로 Huber baseline `0.2274`보다 개선됐지만, 최종 후보 `PP-V1/PP-V2`보다 약함 |
| `PP-U2` | Warm CatBoost 피처 교환/축소/확장 | CatBoost는 p95 일부 개선 가능성이 있었지만 test MdAPE가 `0.31~0.35`대로 Warm 주모델로는 부적합 |
| `PP-L8/PP-L9` | Huber, Quantile, CatBoost 순차 조합 | Warm 조합 후보를 만들었지만 최종적으로 `PP-T/PP-V` 후보가 더 강함 |
| `PP-T1~T4` | Warm fine blend, meta, second-pass 안정화 | `PP-T1 fine_blend_mape_guarded` test MdAPE `0.1621`로 Warm 대표 후보 형성 |
| `PP-V1~V5` | `PP-U` 피처 후보를 포함한 Warm 최종 조합 재검증 | `PP-V1` 대표 후보, `PP-V2` MAPE/p95 방어 후보로 유지 |

기존 Warm 실험은 Huber 중심선, CatBoost 보조, Quantile/메타 조합까지는 확인했다.

다만 Cold의 `PP-W/PP-X/PP-Y`처럼 작가 메타, 전시/갤러리, 검색 피처를 Warm에 직접 넣고 같은 모델 축으로 재학습한 실험은 부족했다.

## 2. 이번에 추가한 실험 리스트

| 실험 ID | 실험명 | 적용 모델 | 사용 피처/처리 | 확인 질문 |
|---|---|---|---|---|
| `PP-Z1` | Warm Huber Cold형 확장 피처 재학습 | Huber | Warm 기준 피처에 작가 학습량, 작가 메타, 전시/갤러리, 검색 피처를 조합별로 추가 | 선형 Huber가 Cold식 확장 피처를 받아도 대표 정확도가 좋아지는가? |
| `PP-Z2` | Warm LightGBM Quantile Cold형 확장 피처 재학습 | LightGBM Quantile q10/q50/q90 | `PP-Z1`과 같은 피처 묶음을 분위수 모델로 학습 | Warm에서도 분위수 중앙값 모델이 Huber보다 더 좋은 중심 예측을 만드는가? |
| `PP-Z3` | Warm CatBoost Cold형 확장 피처 재학습 | CatBoost RMSE | `PP-Z1`과 같은 피처 묶음을 CatBoost로 학습 | CatBoost의 범주형/조합 처리 장점이 Warm에서도 Huber보다 유리한가? |
| `PP-Z4` | Warm LightGBM Quantile q-width 구간 보정 | LightGBM Quantile + segment median correction | `PP-Z2` 후보 중 validation MdAPE가 가장 좋은 후보를 기준으로 q-width/pred/size 구간 보정 | 분위수 예측 폭을 이용하면 큰 오차나 중심 오차를 더 줄일 수 있는가? |

## 3. 사용한 피처 묶음

| 피처 묶음 | 설명 |
|---|---|
| `baseline_warm_base_existing_combo` | 현재 Warm final artifact와 같은 `base_existing_combo` |
| `warm_base_artist_volume` | 기준 피처 + `artist_works_log`, `artist_works_count_train` |
| `warm_base_artist_meta_all` | 기준 피처 + 작가 메타 전체 |
| `warm_base_exhibition_gallery` | 기준 피처 + 전시 활동/갤러리 tier |
| `warm_base_external_interaction` | 기준 피처 + 작가 메타 + 전시/갤러리 상호작용 |
| `warm_base_search_context` | 기준 피처 + 작가 메타 + 검색 핵심 문맥 피처 |
| `warm_base_search_all` | 기준 피처 + 작가 메타 + 검색 전체 피처 |
| `warm_base_meta_external_search_all` | 기준 피처 + 작가 메타 + 전시/갤러리 + 검색 전체 |

## 4. 주요 결과

### 4.1 기존 Warm 최종 후보와 비교

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---:|---:|---:|---|
| `PP-V1 / PP-T1 fine_blend_mape_guarded` | 0.1621 | 0.3044 | 1.0335 | Warm 대표 후보 유지 |
| `PP-V2 huber_component_range_clipped` | 0.1680 | 0.2873 | 0.9287 | Warm MAPE/p95 방어 후보 유지 |
| Warm Huber baseline | 0.2274 | 0.4952 | 2.0130 | 후처리 전 기준선 |
| `PP-Z1 warm_base_search_all` | 0.2195 | 0.4854 | 1.8119 | Huber baseline보다 개선, 최종 후보보다 약함 |
| `PP-Z3 warm_base_artist_meta_all` | 0.3186 | 0.4663 | 1.3889 | MAPE/p95는 일부 개선이나 MdAPE 악화가 큼 |
| `PP-Z4 pred_x_qwidth_min30_cap0.25` | 0.3171 | 0.5553 | 1.7701 | q-width 보정으로도 대표 후보 수준 미달 |

### 4.2 PP-Z 내부 test MdAPE 상위 후보

| 실험 | 후보 | Test MdAPE | Test MAPE | Test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| `PP-Z1` | `warm_base_search_all` | 0.2195 | 0.4854 | 1.8119 | 검색 피처 전체가 Huber baseline 대비 중심 오차를 줄임 |
| `PP-Z1` | `warm_base_artist_volume` | 0.2214 | 0.4813 | 1.9083 | 작가 학습량은 Warm Huber에 약한 개선 신호 |
| `PP-Z1` | `warm_base_exhibition_gallery` | 0.2260 | 0.4810 | 1.8871 | 전시/갤러리는 baseline과 유사, p95는 소폭 개선 |
| `PP-Z2` | `warm_base_external_interaction` | 0.3229 | 0.5732 | 1.9531 | LightGBM Quantile은 Warm 중심 예측에 부적합 |
| `PP-Z3` | `warm_base_artist_meta_all` | 0.3186 | 0.4663 | 1.3889 | CatBoost는 tail 일부 완화 가능, 대표 오차가 큼 |
| `PP-Z4` | `pred_x_qwidth_min30_cap0.25` | 0.3171 | 0.5553 | 1.7701 | 분위수 폭 보정은 Warm 최종 후보를 대체하지 못함 |

## 5. 해석

- Warm은 이미 `artist_key`가 강한 작가 기준선을 제공한다.
- Cold에서 유효했던 작가 메타, 전시/갤러리, 검색 피처는 Warm에서는 `artist_key`가 이미 설명하는 작가 기준선과 상당 부분 겹친다.
- 그래서 Huber에 확장 피처를 더하면 baseline 대비 소폭 개선은 생기지만, `PP-T/PP-V`의 조합/보정 후보만큼 큰 개선은 만들지 못했다.
- CatBoost는 MAPE와 p95를 일부 낮출 수 있으나 MdAPE가 크게 악화된다. 이는 Warm에서 작가별 기준선을 직접 잡는 Huber 구조가 CatBoost의 조건 분기보다 중심 예측에 더 맞기 때문이다.
- LightGBM Quantile은 Cold에서는 외부 피처와 잘 맞았지만, Warm에서는 같은 작가 이력이 있는 샘플을 세밀하게 나누면서 중심 예측이 흔들렸다.
- q-width 구간 보정도 최종 후보를 대체할 만큼 개선되지 않았다.

## 6. 결론

- Warm에도 Cold식 피처와 모델을 적용하는 실험은 이번 `PP-Z1~Z4`로 보완 완료했다.
- Warm Huber baseline 대비로는 `PP-Z1 warm_base_search_all`이 MdAPE `0.2274 -> 0.2195`로 개선됐다.
- 그러나 기존 Warm 운영 후보 `PP-V1` MdAPE `0.1621`, `PP-V2` MAPE `0.2873`, p95 `0.9287`보다 약하다.
- 따라서 Warm 최종 후보는 기존 `PP-V1/PP-V2`를 유지한다.
- `PP-Z`는 운영 후보 교체가 아니라, “Warm에서 Cold형 확장 피처를 직접 넣어도 최종 후보를 넘지 못했다”는 검증 근거로 남긴다.

## 7. 후속 판단

- Warm 추가 개선은 외부 피처를 더 넣는 방향보다 기존 `PP-V1/PP-V2` 조합의 운영 단순화, 안정성 검증, 배포 구조 정리가 우선이다.
- Warm에서 검색 피처는 Huber baseline 개선 신호가 있으므로, 추후 검색 품질이 개선된 데이터가 들어오면 `PP-Z1`만 재검증할 수 있다.
- Warm CatBoost는 주모델 후보가 아니라 residual 보조 또는 p95 방어 보조 후보로만 다루는 것이 적절하다.
