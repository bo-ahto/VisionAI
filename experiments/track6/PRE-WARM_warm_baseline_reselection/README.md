# Track6 PRE-WARM Warm 기준 모델 재선정 실험

- 목적: 후처리 전에 Warm Huber 기준 모델을 재선정하기 위해 현재 final artifact 피처셋과 기존 고성능 compact 후보를 같은 split과 평가 방식으로 비교한다.
- 최고 결과: `PRE-WARM-05: compact artist_name size + artist works` + `Huber`
- MdAPE: `0.2221`
- p95_APE: `1.9218`
- Within_30: `0.6046`
- 결과 HTML: `outputs/result_sheet.html`
- 결과 CSV: `outputs/metrics_long.csv`

## 피처 조합별 실제 피처명

- `PRE-WARM-01: final artifact base_existing_combo`: `artist_key, width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, medium_support_bucket, is_extreme_aspect_ratio`
- `PRE-WARM-02: compact artist_name size`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio`
- `PRE-WARM-03: compact artist_name size + area interaction`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, log_area_x_artist_name_ko_01, log_area_x_artist_name_ko_02, log_area_x_artist_name_ko_03, log_area_x_artist_name_ko_04, log_area_x_artist_name_ko_05, log_area_x_artist_name_ko_06, log_area_x_artist_name_ko_07, log_area_x_artist_name_ko_08, log_area_x_artist_name_ko_09, log_area_x_artist_name_ko_10`
- `PRE-WARM-04: compact artist_name size + ho interaction`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, ln_estimated_ho, ln_ho_x_artist_name_ko_01, ln_ho_x_artist_name_ko_02, ln_ho_x_artist_name_ko_03, ln_ho_x_artist_name_ko_04, ln_ho_x_artist_name_ko_05, ln_ho_x_artist_name_ko_06, ln_ho_x_artist_name_ko_07, ln_ho_x_artist_name_ko_08, ln_ho_x_artist_name_ko_09, ln_ho_x_artist_name_ko_10`
- `PRE-WARM-05: compact artist_name size + artist works`: `artist_name_ko, width_cm, height_cm, log_area, aspect_ratio, artist_works_log, artist_works_log_is_missing`
- `PRE-WARM-06A: compact artist_key size`: `artist_key, width_cm, height_cm, log_area, aspect_ratio`
- `PRE-WARM-06B: compact artist_key size + area interaction`: `artist_key, width_cm, height_cm, log_area, aspect_ratio, log_area_x_artist_key_01, log_area_x_artist_key_02, log_area_x_artist_key_03, log_area_x_artist_key_04, log_area_x_artist_key_05, log_area_x_artist_key_06, log_area_x_artist_key_07, log_area_x_artist_key_08, log_area_x_artist_key_09, log_area_x_artist_key_10`
- `PRE-WARM-06C: compact artist_key size + ho interaction`: `artist_key, width_cm, height_cm, log_area, aspect_ratio, ln_estimated_ho, ln_ho_x_artist_key_01, ln_ho_x_artist_key_02, ln_ho_x_artist_key_03, ln_ho_x_artist_key_04, ln_ho_x_artist_key_05, ln_ho_x_artist_key_06, ln_ho_x_artist_key_07, ln_ho_x_artist_key_08, ln_ho_x_artist_key_09, ln_ho_x_artist_key_10`

## 실험 해석

- 이번 실험은 운영 기준 Warm Huber 방식에 맞춰 `OneHotEncoder(min_frequency=10)`과 `HuberRegressor(max_iter=3000)`을 사용했다.
- 기존 WM1/OPT-W3에서 확인된 MdAPE `0.154~0.157`대 결과는 전체 one-hot에 가까운 실험 방식에서 나온 값이다.
- 운영 기준 전처리로 다시 비교하면 compact 후보의 성능은 MdAPE `0.222~0.225` 수준으로 내려온다.
- 현재 final artifact 피처셋은 MdAPE `0.2274`, p95_APE `2.0128`로 재현됐다.
- 가장 낮은 MdAPE는 `PRE-WARM-05`이며, final artifact 대비 MdAPE는 약 `0.0053p` 개선됐다.
- p95_APE는 `PRE-WARM-06C`, `PRE-WARM-04`, `PRE-WARM-06B`, `PRE-WARM-03`, `PRE-WARM-05`가 final artifact보다 낮다.

## 판단

- Warm 기준 모델을 바로 교체할 정도의 큰 차이는 아니다.
- 다만 final artifact의 `base_existing_combo`는 p95_APE가 가장 나쁜 축에 속하므로, 후처리 전에 compact 후보를 기준 모델 후보로 유지해야 한다.
- `artist_name_ko` 후보가 `artist_key` 후보보다 MdAPE가 낮지만, 운영 적용성은 `artist_key`가 더 적합하다.
- 최종 판단은 validation/OOF 기준에서 `PRE-WARM-01`, `PRE-WARM-05`, `PRE-WARM-06C`를 다시 비교한 뒤 확정한다.
- 후처리 실험의 Warm 기준은 당장은 `base_existing_combo` 단독으로 고정하지 말고, `PRE-WARM-05` 또는 `PRE-WARM-06C`를 함께 후보로 둔다.

## 다음 작업

- `PRE-WARM-07`: 상위 후보 3개에 대해 group-drop ablation 실행
  - `PRE-WARM-01`: final artifact base_existing_combo
  - `PRE-WARM-05`: compact artist_name size + artist works
  - `PRE-WARM-06C`: compact artist_key size + ho interaction
- `PRE-WARM-08`: validation/OOF 기준으로 Warm 기준 모델 최종 확정
- Warm 후처리 `PP-A1-W`는 `PRE-WARM-08` 이후 확정된 기준 모델로 다시 계산
