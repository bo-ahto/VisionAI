# Track6 CM1 Cold 상위 피처 조합별 모델군 비교

- 목적: Cold 상위 피처 조합을 고정한 뒤 모델만 바꿔 신규 작가 예측에 가장 적합한 모델군을 검증한다.
- 종합 점수 1위: `CM1-F2: 작품 기본 피처 + 활동량/인지도` + `CatBoost` / `94.0240`
- 정확도 최고: `CM1-F2: 작품 기본 피처 + 활동량/인지도` + `CatBoost` / MdAPE `0.4488`
- 큰 오차 안정성 최고: `CM1-F4: F3 + 활동량/인지도 x 면적` + `CatBoost` / p95_APE `2.8895`
- Cold 원칙: `artist_name_ko` 미사용
- 실행 모드: `full_split_no_sampling`

## 피처 조합별 실제 피처명

- `CM1-F1: 작품 기본 피처`: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support`
- `CM1-F2: 작품 기본 피처 + 활동량/인지도`: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1`
- `CM1-F3: F2 + 정보량/결측`: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing`
- `CM1-F4: F3 + 활동량/인지도 x 면적`: `ln_estimated_ho, log_area, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing, total_works_x_log_area, followers_x_log_area, for_sale_works_x_log_area`
- `CM1-F5: F3 + 활동량/인지도 x 호수`: `ln_estimated_ho, log_area, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1, artist_meta_available_count, artist_meta_completeness_score, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing, total_works_x_ln_ho, followers_x_ln_ho, for_sale_works_x_ln_ho`

## 주요 결과 파일

- HTML: `outputs/result_sheet.html`
- 전체 지표: `outputs/metrics_long.csv`
- 종합 점수 지표: `outputs/metrics_scored.csv`
- 사용 데이터: `data/`
- 원본 복사본: `source_data/`
