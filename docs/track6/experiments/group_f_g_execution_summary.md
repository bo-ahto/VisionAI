# Track6 Group F/G 실행 결과 종합

- 생성일: `2026-05-27`
- Group F: 작가 메타 변수 조합을 작가명 없이 단독으로 검증
- Group G: 작품 기본 피처 묶음(`ln_estimated_ho + nant_material_idx + nant_tool + nant_support`)을 기준선으로 두고 작가명/작가 메타 추가 효과 검증
- G10: 작가별 학습 작품 수 구간별 Warm 모델과 Cold 방식 모델 라우팅 비교

## 핵심 결론

- Warm에서는 `작품 기본 피처 + 작가명`이 가장 강한 개선을 보였다. 작가명은 Warm 최종 후보에서 핵심 피처로 유지할 근거가 있다.
- Cold에서는 작가명이 직접 도움이 되지 않으므로 `작품 기본 피처 + 활동량/판매 노출량` 또는 `전체 작가 메타`를 후보로 두되, 메타 수집 재현성과 결측률을 같이 봐야 한다.
- 작가 메타 단독(Group F)은 최종 모델 후보라기보다 보조 피처 후보를 고르는 사전 검증 성격이 강하다.
- G10 기준 공식 Warm test의 5~9개 작가 구간에서도 Warm 작가 모델이 Cold 방식보다 안정적이었다. 다만 Track6 공식 Warm test에는 5개 미만 구간이 없어 1~4개 저이력 작가 정책은 별도 split이 필요하다.

## Warm 상위 후보

| 실험 ID | 실험명 | 범위 | 최고 변수 블록 | 최고 모델 | MdAPE | p95_APE | 기준선 대비 MdAPE 개선 | 해석 | 결과 HTML |
|---|---|---|---|---|---|---|---|---|---|
| G1 | 작품 기본 피처 + 작가명 | Warm | 작품 기본 피처 + 작가명 | Huber | 0.1831 | 0.9854 | 0.3131 | Warm에서 기준선 대비 개선 | experiments/track6/G1_basic_artwork_plus_artist_name/outputs/result_sheet.html |
| G9 | 작품 기본 피처 + 전체 작가 메타 | Warm | 작품 기본 피처 + 전체 작가 메타 | Huber | 0.4390 | 2.9010 | 0.0572 | Warm에서 기준선 대비 개선 | experiments/track6/G9_basic_artwork_plus_full_artist_meta/outputs/result_sheet.html |
| G6 | 작품 기본 피처 + 작가 활동량 | Warm | 작품 기본 피처 + 활동량 | Huber | 0.4630 | 2.6617 | 0.0332 | Warm에서 기준선 대비 개선 | experiments/track6/G6_basic_artwork_plus_activity/outputs/result_sheet.html |
| G8 | 작품 기본 피처 + 기본 작가 프로필 | Warm | 작품 기본 피처 + 기본 작가 프로필 + 결측 | Huber | 0.4711 | 3.0398 | 0.0252 | Warm에서 기준선 대비 개선 | experiments/track6/G8_basic_artwork_plus_basic_profile/outputs/result_sheet.html |
| G2 | 작품 기본 피처 + 작가별 학습 작품 수 | Warm | 작품 기본 피처 + 작가별 학습 작품 수 | Huber | 0.4752 | 2.7386 | 0.0210 | Warm에서 기준선 대비 개선 | experiments/track6/G2_basic_artwork_plus_artist_work_count/outputs/result_sheet.html |

## Cold 상위 후보

| 실험 ID | 실험명 | 범위 | 최고 변수 블록 | 최고 모델 | MdAPE | p95_APE | 기준선 대비 MdAPE 개선 | 해석 | 결과 HTML |
|---|---|---|---|---|---|---|---|---|---|
| G6 | 작품 기본 피처 + 작가 활동량 | Cold | 작품 기본 피처 + 활동량 + 결측 | LightGBM | 0.4577 | 2.9056 | 0.0551 | Cold에서 기준선 대비 개선 | experiments/track6/G6_basic_artwork_plus_activity/outputs/result_sheet.html |
| G8 | 작품 기본 피처 + 기본 작가 프로필 | Cold | 작품 기본 피처 + 기본 작가 프로필 | LightGBM | 0.4645 | 6.0347 | 0.0483 | Cold에서 기준선 대비 개선 | experiments/track6/G8_basic_artwork_plus_basic_profile/outputs/result_sheet.html |
| G9 | 작품 기본 피처 + 전체 작가 메타 | Cold | 작품 기본 피처 + 전체 작가 메타 | LightGBM | 0.4684 | 3.5812 | 0.0443 | Cold에서 기준선 대비 개선 | experiments/track6/G9_basic_artwork_plus_full_artist_meta/outputs/result_sheet.html |
| G3 | 작품 기본 피처 + 작가 생년 | Cold | 작품 기본 피처 + 생년 | Quantile-LAD | 0.4716 | 3.3639 | 0.0411 | Cold에서 기준선 대비 개선 | experiments/track6/G3_basic_artwork_plus_birth_year/outputs/result_sheet.html |
| G5 | 작품 기본 피처 + 작가 국적 | Cold | 작품 기본 피처 + 국적 + 결측 | Quantile-LAD | 0.4888 | 3.2427 | 0.0240 | Cold에서 기준선 대비 개선 | experiments/track6/G5_basic_artwork_plus_nationality/outputs/result_sheet.html |

## 전체 F/G 결과

| 실험 ID | 실험명 | 범위 | 최고 변수 블록 | 최고 모델 | MdAPE | p95_APE | 기준선 대비 MdAPE 개선 | 해석 | 결과 HTML |
|---|---|---|---|---|---|---|---|---|---|
| F1 | 작가 생년 + 전시 경력 조합 | Warm | 생년 + 전시 경력 + 결측 | Ridge | 0.7482 | 6.9013 | nan | 단독 메타만으로는 약함 | experiments/track6/F1_artist_birth_exhibition_combo/outputs/result_sheet.html |
| F1 | 작가 생년 + 전시 경력 조합 | Cold | 생년 + 전시 경력 | Quantile-LAD | 0.7015 | 7.2887 | nan | 단독 메타만으로는 약함 | experiments/track6/F1_artist_birth_exhibition_combo/outputs/result_sheet.html |
| F2 | 작가 활동량 + 인지도 조합 | Warm | 활동량 + 인지도 + 결측 | Linear Regression | 0.7331 | 6.5421 | nan | 단독 메타만으로는 약함 | experiments/track6/F2_artist_activity_popularity_combo/outputs/result_sheet.html |
| F2 | 작가 활동량 + 인지도 조합 | Cold | 활동량 + 인지도 + 결측 | Quantile-LAD | 0.6991 | 6.1733 | nan | 단독 메타만으로는 약함 | experiments/track6/F2_artist_activity_popularity_combo/outputs/result_sheet.html |
| F3 | 작가 기본 프로필 조합 | Warm | 기본 작가 프로필 + 결측 | Ridge | 0.7625 | 6.9504 | nan | 단독 메타만으로는 약함 | experiments/track6/F3_artist_basic_profile_combo/outputs/result_sheet.html |
| F3 | 작가 기본 프로필 조합 | Cold | 기본 작가 프로필 | Quantile-LAD | 0.7059 | 6.2445 | nan | 단독 메타만으로는 약함 | experiments/track6/F3_artist_basic_profile_combo/outputs/result_sheet.html |
| F4 | 활동량/인지도 + 정보량 조합 | Warm | 활동량 + 인지도 + 정보량 | Linear Regression | 0.7372 | 6.5906 | nan | 단독 메타만으로는 약함 | experiments/track6/F4_artist_activity_popularity_information_combo/outputs/result_sheet.html |
| F4 | 활동량/인지도 + 정보량 조합 | Cold | 활동량 + 인지도 + 정보량 | Quantile-LAD | 0.6967 | 6.1940 | nan | 단독 메타만으로는 약함 | experiments/track6/F4_artist_activity_popularity_information_combo/outputs/result_sheet.html |
| F5 | 전체 작가 메타 묶음 | Warm | 전체 작가 메타 묶음 | Ridge | 0.7311 | 6.7563 | nan | 단독 메타만으로는 약함 | experiments/track6/F5_artist_full_meta_bundle/outputs/result_sheet.html |
| F5 | 전체 작가 메타 묶음 | Cold | 전체 작가 메타 묶음 | Huber | 0.6956 | 6.6926 | nan | 단독 메타만으로는 약함 | experiments/track6/F5_artist_full_meta_bundle/outputs/result_sheet.html |
| G1 | 작품 기본 피처 + 작가명 | Warm | 작품 기본 피처 + 작가명 | Huber | 0.1831 | 0.9854 | 0.3131 | Warm에서 기준선 대비 개선 | experiments/track6/G1_basic_artwork_plus_artist_name/outputs/result_sheet.html |
| G1 | 작품 기본 피처 + 작가명 | Cold | 작품 기본 피처 + 작가명 | LightGBM | 0.4956 | 3.4348 | 0.0172 | Cold에서 소폭 개선 | experiments/track6/G1_basic_artwork_plus_artist_name/outputs/result_sheet.html |
| G2 | 작품 기본 피처 + 작가별 학습 작품 수 | Warm | 작품 기본 피처 + 작가별 학습 작품 수 | Huber | 0.4752 | 2.7386 | 0.0210 | Warm에서 기준선 대비 개선 | experiments/track6/G2_basic_artwork_plus_artist_work_count/outputs/result_sheet.html |
| G2 | 작품 기본 피처 + 작가별 학습 작품 수 | Cold | 작품 기본 피처 + 작가별 학습 작품 수 | Quantile-LAD | 0.5076 | 2.8142 | 0.0052 | Cold에서 소폭 개선 | experiments/track6/G2_basic_artwork_plus_artist_work_count/outputs/result_sheet.html |
| G3 | 작품 기본 피처 + 작가 생년 | Warm | 작품 기본 피처 + 생년 + 결측 | Huber | 0.4870 | 2.9346 | 0.0092 | Warm에서 소폭 개선 | experiments/track6/G3_basic_artwork_plus_birth_year/outputs/result_sheet.html |
| G3 | 작품 기본 피처 + 작가 생년 | Cold | 작품 기본 피처 + 생년 | Quantile-LAD | 0.4716 | 3.3639 | 0.0411 | Cold에서 기준선 대비 개선 | experiments/track6/G3_basic_artwork_plus_birth_year/outputs/result_sheet.html |
| G4 | 작품 기본 피처 + 전시 경력 | Warm | 작품 기본 피처 + 전시 경력 | Huber | 0.4879 | 2.9180 | 0.0083 | Warm에서 소폭 개선 | experiments/track6/G4_basic_artwork_plus_exhibition_counts/outputs/result_sheet.html |
| G4 | 작품 기본 피처 + 전시 경력 | Cold | 작품 기본 피처 + 전시 경력 | LightGBM | 0.4980 | 4.6619 | 0.0147 | Cold에서 소폭 개선 | experiments/track6/G4_basic_artwork_plus_exhibition_counts/outputs/result_sheet.html |
| G5 | 작품 기본 피처 + 작가 국적 | Warm | 작품 기본 피처 + 국적 | Huber | 0.4899 | 2.9453 | 0.0063 | Warm에서 소폭 개선 | experiments/track6/G5_basic_artwork_plus_nationality/outputs/result_sheet.html |
| G5 | 작품 기본 피처 + 작가 국적 | Cold | 작품 기본 피처 + 국적 + 결측 | Quantile-LAD | 0.4888 | 3.2427 | 0.0240 | Cold에서 기준선 대비 개선 | experiments/track6/G5_basic_artwork_plus_nationality/outputs/result_sheet.html |
| G6 | 작품 기본 피처 + 작가 활동량 | Warm | 작품 기본 피처 + 활동량 | Huber | 0.4630 | 2.6617 | 0.0332 | Warm에서 기준선 대비 개선 | experiments/track6/G6_basic_artwork_plus_activity/outputs/result_sheet.html |
| G6 | 작품 기본 피처 + 작가 활동량 | Cold | 작품 기본 피처 + 활동량 + 결측 | LightGBM | 0.4577 | 2.9056 | 0.0551 | Cold에서 기준선 대비 개선 | experiments/track6/G6_basic_artwork_plus_activity/outputs/result_sheet.html |
| G7 | 작품 기본 피처 + 작가 인지도 | Warm | 작품 기본 피처 + 인지도 | Huber | 0.4948 | 2.9126 | 0.0014 | Warm에서 소폭 개선 | experiments/track6/G7_basic_artwork_plus_popularity/outputs/result_sheet.html |
| G7 | 작품 기본 피처 + 작가 인지도 | Cold | 작품 기본 피처 + 인지도 + 결측 | Quantile-LAD | 0.5121 | 3.2244 | 0.0006 | Cold에서 소폭 개선 | experiments/track6/G7_basic_artwork_plus_popularity/outputs/result_sheet.html |
| G8 | 작품 기본 피처 + 기본 작가 프로필 | Warm | 작품 기본 피처 + 기본 작가 프로필 + 결측 | Huber | 0.4711 | 3.0398 | 0.0252 | Warm에서 기준선 대비 개선 | experiments/track6/G8_basic_artwork_plus_basic_profile/outputs/result_sheet.html |
| G8 | 작품 기본 피처 + 기본 작가 프로필 | Cold | 작품 기본 피처 + 기본 작가 프로필 | LightGBM | 0.4645 | 6.0347 | 0.0483 | Cold에서 기준선 대비 개선 | experiments/track6/G8_basic_artwork_plus_basic_profile/outputs/result_sheet.html |
| G9 | 작품 기본 피처 + 전체 작가 메타 | Warm | 작품 기본 피처 + 전체 작가 메타 | Huber | 0.4390 | 2.9010 | 0.0572 | Warm에서 기준선 대비 개선 | experiments/track6/G9_basic_artwork_plus_full_artist_meta/outputs/result_sheet.html |
| G9 | 작품 기본 피처 + 전체 작가 메타 | Cold | 작품 기본 피처 + 전체 작가 메타 | LightGBM | 0.4684 | 3.5812 | 0.0443 | Cold에서 기준선 대비 개선 | experiments/track6/G9_basic_artwork_plus_full_artist_meta/outputs/result_sheet.html |

## G10 라우팅 결과

| case | scope | n | R2 | RMSE_log | MdAPE | p95_APE | Within_30 | Within_50 | MAPE |
|---|---|---|---|---|---|---|---|---|---|
| warm_artist_model_on_warm_test | Warm | 607 | 0.8248 | 0.5699 | 0.1846 | 0.9845 | 0.6853 | 0.8451 | 0.4620 |
| cold_style_model_on_warm_test | Warm | 607 | 0.3944 | 1.0597 | 0.5055 | 2.9971 | 0.3229 | 0.4959 | 0.7991 |
| cold_style_model_on_cold_test | Cold | 3099 | 0.4181 | 1.0026 | 0.5128 | 3.2103 | 0.2588 | 0.4873 | 1.1479 |

### Warm test 작가별 학습 작품 수 구간

| artist_count_bin | case | n | MdAPE | p95_APE | Within_30 | Within_50 |
|---|---|---|---|---|---|---|
| 5_to_9 | warm_artist_model | 244 | 0.1808 | 1.2916 | 0.6516 | 0.8197 |
| 5_to_9 | cold_style_model | 244 | 0.5616 | 3.4121 | 0.2746 | 0.4262 |
| 50_plus | warm_artist_model | 72 | 0.1570 | 0.4461 | 0.8194 | 0.9722 |
| 50_plus | cold_style_model | 72 | 0.5015 | 1.7435 | 0.3333 | 0.5000 |
| 10_to_19 | warm_artist_model | 150 | 0.1898 | 1.5450 | 0.6933 | 0.8267 |
| 10_to_19 | cold_style_model | 150 | 0.4435 | 2.4252 | 0.3600 | 0.5267 |
| 20_to_49 | warm_artist_model | 141 | 0.1945 | 0.8145 | 0.6667 | 0.8440 |
| 20_to_49 | cold_style_model | 141 | 0.4170 | 2.0000 | 0.3617 | 0.5816 |
