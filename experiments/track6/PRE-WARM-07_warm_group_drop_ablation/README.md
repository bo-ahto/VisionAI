# Track6 PRE-WARM-07 Warm 기준 후보 group-drop ablation

- 목적: Warm 기준 모델 후보 3개에서 피처 그룹을 제거했을 때 성능이 어떻게 변하는지 확인하여 후처리 기준 모델과 보정 구간의 근거를 만든다.
- 최고 결과: `GDA-05-DROP-aspect` + `Huber`
- MdAPE: `0.2208`
- p95_APE: `1.9234`
- Within_30: `0.6063`
- 결과 HTML: `outputs/result_sheet.html`
- 결과 CSV: `outputs/metrics_long.csv`

## 피처 조합별 실제 피처명

- `GDA-01-BASE: final artifact base_existing_combo`: `artist_key, width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio`
- `GDA-01-DROP-artist`: `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio`
- `GDA-01-DROP-aspect`: `artist_key, width_cm, height_cm, depth_cm, area_cm2, log_area, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket`
- `GDA-01-DROP-depth3d`: `artist_key, width_cm, height_cm, area_cm2, log_area, aspect_ratio, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio`
- `GDA-01-DROP-medium_support`: `artist_key, width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, is_extreme_aspect_ratio`
- `GDA-01-DROP-size`: `artist_key, depth_cm, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio`
- `GDA-05-BASE: compact artist_name size + artist works`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, artist_works_log, artist_works_log_is_missing`
- `GDA-05-DROP-artist_name`: `width_cm, height_cm, log_area, aspect_ratio, artist_works_log, artist_works_log_is_missing`
- `GDA-05-DROP-artist_works`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio`
- `GDA-05-DROP-aspect`: `artist_name_ko, width_cm, height_cm, log_area, artist_works_log, artist_works_log_is_missing`
- `GDA-05-DROP-size`: `artist_name_ko, aspect_ratio, artist_works_log, artist_works_log_is_missing`
- `GDA-06C-BASE: compact artist_key size + ho interaction`: `artist_key, width_cm, height_cm, log_area, aspect_ratio, ln_estimated_ho, ln_ho_x_artist_key_01, ln_ho_x_artist_key_02, ln_ho_x_artist_key_03, ln_ho_x_artist_key_04, ln_ho_x_artist_key_05, ln_ho_x_artist_key_06, ln_ho_x_artist_key_07, ln_ho_x_artist_key_08, ln_ho_x_artist_key_09, ln_ho_x_artist_key_10`
- `GDA-06C-DROP-artist_key`: `width_cm, height_cm, log_area, aspect_ratio, ln_estimated_ho`
- `GDA-06C-DROP-aspect`: `artist_key, width_cm, height_cm, log_area, ln_estimated_ho, ln_ho_x_artist_key_01, ln_ho_x_artist_key_02, ln_ho_x_artist_key_03, ln_ho_x_artist_key_04, ln_ho_x_artist_key_05, ln_ho_x_artist_key_06, ln_ho_x_artist_key_07, ln_ho_x_artist_key_08, ln_ho_x_artist_key_09, ln_ho_x_artist_key_10`
- `GDA-06C-DROP-ho_interaction`: `artist_key, width_cm, height_cm, log_area, aspect_ratio`
- `GDA-06C-DROP-size`: `artist_key, aspect_ratio, ln_estimated_ho, ln_ho_x_artist_key_01, ln_ho_x_artist_key_02, ln_ho_x_artist_key_03, ln_ho_x_artist_key_04, ln_ho_x_artist_key_05, ln_ho_x_artist_key_06, ln_ho_x_artist_key_07, ln_ho_x_artist_key_08, ln_ho_x_artist_key_09, ln_ho_x_artist_key_10`

## 핵심 결과

| 후보군 | 비교 | MdAPE | p95_APE | 해석 |
| --- | --- | ---: | ---: | --- |
| `GDA-05` | baseline | `0.2221` | `1.9218` | `artist_name_ko + size + artist_works` 기준 |
| `GDA-05` | drop aspect | `0.2208` | `1.9234` | aspect 제거 시 MdAPE 소폭 개선. aspect는 이 후보에서 필수 아님 |
| `GDA-05` | drop artist_works | `0.2223` | `1.9467` | artist_works 효과는 작고 p95 방어에 약간 도움 |
| `GDA-05` | drop artist_name | `0.4797` | `2.8258` | 작가 정보 제거 시 성능 급락 |
| `GDA-05` | drop size | `0.5559` | `5.3860` | 크기 정보 제거 시 성능 및 tail 급락 |
| `GDA-01` | baseline | `0.2274` | `2.0128` | final artifact 기준 |
| `GDA-01` | drop medium/support | `0.2254` | `1.9958` | medium/support 제거 시 오히려 소폭 개선 |
| `GDA-01` | drop aspect | `0.2262` | `2.0077` | aspect 제거 시 소폭 개선 |
| `GDA-01` | drop depth/3D | `0.2276` | `2.0259` | depth/3D 영향은 작음 |
| `GDA-01` | drop artist | `0.4843` | `2.9767` | 작가 정보 제거 시 성능 급락 |
| `GDA-01` | drop size | `0.5508` | `5.2275` | 크기 정보 제거 시 성능 및 tail 급락 |
| `GDA-06C` | baseline | `0.2271` | `1.8977` | 운영용 artist_key + ho interaction 후보 |
| `GDA-06C` | drop aspect | `0.2306` | `1.8847` | MdAPE는 악화, p95는 소폭 개선 |
| `GDA-06C` | drop ho interaction | `0.2311` | `1.9469` | ho interaction은 p95 방어에 기여 |
| `GDA-06C` | drop artist_key | `0.4921` | `2.8499` | 작가 정보 제거 시 성능 급락 |
| `GDA-06C` | drop size | `0.2596` | `1.9160` | size 제거 시 MdAPE 악화. 단 p95 악화는 제한적 |

## 모델 특성 기반 해석

- Warm Huber는 선형 모델이므로 가격 로그값을 `작가 효과 + 크기 효과 + 보조 피처 효과`의 합으로 계산한다.
- 이번 제거 실험에서 작가 그룹과 크기 그룹을 빼면 MdAPE가 `0.48~0.56`까지 급락했다.
- 따라서 Warm 가격 예측의 중심축은 `작가별 기본 가격대`와 `작품 크기`다.
- `medium/support`, `aspect`, `depth/3D`는 final artifact 후보에서 제거해도 성능이 유지되거나 소폭 좋아졌다.
- 이는 Huber 선형 모델에서 해당 보조 피처들이 작가/크기 신호만큼 강한 독립 설명력을 갖지 못하거나, 일부 중복/노이즈를 만들 수 있다는 뜻이다.
- `artist_works_log`는 전체 MdAPE 개선폭은 작지만 제거 시 p95가 악화되므로, 일반 정확도보다 안정성 보조 피처로 보는 편이 맞다.
- `artist_key x ho` 교차항은 MdAPE 개선폭은 제한적이지만 p95_APE 방어에 도움이 된다.

## 기준 모델 판단

- MdAPE 기준 1순위는 `GDA-05-DROP-aspect`다.
- 다만 이 후보는 `artist_name_ko`를 사용하므로 운영 최종 후보로 쓰려면 `artist_key` 버전에서 성능이 유지되는지 추가 확인이 필요하다.
- 운영 적용성까지 고려하면 `GDA-06C`는 p95_APE가 낮아 tail 안정성 후보로 남길 가치가 있다.
- final artifact `GDA-01`은 RMSE_log가 가장 낮지만 MdAPE와 p95_APE는 compact 후보보다 불리하다.
- Warm 후처리 기준 모델은 당장 `base_existing_combo` 단독으로 고정하지 말고 아래 3개를 최종 후보로 둔다.
  - `GDA-05-DROP-aspect`: MdAPE 최저 후보
  - `GDA-05-BASE`: 기존 PRE-WARM-05 기준 후보
  - `GDA-06C`: 운영용 artist_key 기반 p95 안정 후보

## 후처리 연결

- PP-A1-W 전체 residual 보정은 최종 Warm 후보별로 각각 계산해야 한다.
- PP-A3-W 크기 구간 보정은 필수 검토 대상이다. size 제거 시 성능이 가장 크게 악화됐기 때문이다.
- PP-A5-W 작가 학습량 구간 보정은 보조 검토 대상이다. artist_works 제거 시 p95가 악화됐다.
- medium/support 기반 Warm 보정은 우선순위를 낮춘다. final artifact에서 제거해도 성능이 나빠지지 않았다.
- aspect 기반 Warm 보정은 보류한다. 제거 시 성능이 개선되는 후보가 있었다.

## 다음 작업

- `PRE-WARM-08`: Warm 최종 기준 후보 3개를 validation/OOF 기준으로 다시 비교한다.
- 최종 Warm 후보 확정 후 `PP-A1-W`, `PP-A3-W`, `PP-A5-W`를 후보별로 재계산한다.
