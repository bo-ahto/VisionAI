# Track6 Group H/I/J 실행 결과 종합

- 생성일: `2026-05-27`
- Group H: 작가명과 작품 변수의 교차항 검증
- Group I: 작가명 없이 작품 기본 변수와 작가 메타를 결합한 Cold 후보 검증
- Group J: 작가 메타와 작품 변수의 교차항 검증
- 중복 실험은 재실행하지 않고 기존 D/G 실험으로 매핑

## 핵심 결론

- Warm에서는 `H1 작가명 x 호수`가 작가명+호수 기준선보다 MdAPE를 낮췄지만 p95가 일부 악화되어 보류 후보이다.
- Cold MdAPE만 보면 `J5 활동량/인지도 x 면적`이 가장 낮지만, p95는 `I3/I5 작품 기본 피처 + 활동량/인지도/정보량` 계열이 더 안정적이다.
- J 그룹은 `활동량/인지도 x 호수/면적` 외에는 복잡도 대비 개선이 약하다. 기본 프로필 x 재료/지지체 계열은 현재 최종 후보로 보기 어렵다.
- H2/H3/H4/I4는 기존 D8/D9/D10/G8과 실험 목적이 겹쳐 중복 실행하지 않았다.

## Warm 상위 후보

| 실험 ID | 실험명 | 범위 | 기준 MdAPE | 최고 변수 블록 | 최고 모델 | MdAPE | p95_APE | 기준선 대비 MdAPE 개선 | 해석 | 결과 HTML |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 같은 호수라도 작가명에 따라 가격대가 다른지 확인 | Warm | 0.1801 | H1 교차항: 작가명 x 호수 | Huber | 0.1762 | 1.0038 | 0.0038 | Warm에서 개선폭이 작아 보류 | experiments/track6/H1_artist_name_x_ln_ho/outputs/result_sheet.html |
| I6 | 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인 | Warm | 0.4779 | I6 후보: 실제 크기 확장 + 전체 작가 메타 | Huber | 0.4156 | 2.6607 | 0.0623 | Warm에서 명확한 개선 후보 | experiments/track6/I6_extended_size_full_artist_meta/outputs/result_sheet.html |
| H5 | 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인 | Warm | 0.4270 | H5 교차항: 작가명 x 깊이 | Huber | 0.4225 | 2.8961 | 0.0045 | Warm에서 개선폭이 작아 보류 | experiments/track6/H5_artist_name_x_depth/outputs/result_sheet.html |
| I5 | 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인 | Warm | 0.4962 | I5 후보: 작품 기본 피처 + 시장 노출/정보량 | Huber | 0.4727 | 2.7022 | 0.0235 | Warm에서 소폭 개선 후보 | experiments/track6/I5_basic_artwork_market_exposure_information/outputs/result_sheet.html |
| J5 | 작가의 활동량/인지도에 따라 면적 효과가 다르게 나타나는지 확인 | Warm | 0.4793 | J5 교차항: 활동량/인지도 x 면적 | Huber | 0.4754 | 2.5575 | 0.0038 | Warm에서 개선폭이 작아 보류 | experiments/track6/J5_activity_popularity_x_log_area/outputs/result_sheet.html |
| I3 | 작품 기본 변수와 활동량/인지도 메타를 함께 쓰면 시장 노출 정도가 가격 예측에 도움 되는지 확인 | Warm | 0.4962 | I3 후보: 작품 기본 피처 + 활동량/인지도 | Huber | 0.4819 | 2.6597 | 0.0143 | Warm에서 소폭 개선 후보 | experiments/track6/I3_basic_artwork_activity_popularity_cold_candidate/outputs/result_sheet.html |
| J4 | 작가의 활동량/인지도에 따라 호수 효과가 다르게 나타나는지 확인 | Warm | 0.5264 | J4 교차항: 활동량/인지도 x 호수 | Huber | 0.4902 | 2.6768 | 0.0362 | Warm에서 명확한 개선 후보 | experiments/track6/J4_activity_popularity_x_ln_ho/outputs/result_sheet.html |

## Cold 상위 후보

| 실험 ID | 실험명 | 범위 | 기준 MdAPE | 최고 변수 블록 | 최고 모델 | MdAPE | p95_APE | 기준선 대비 MdAPE 개선 | 해석 | 결과 HTML |
|---|---|---|---|---|---|---|---|---|---|---|
| J5 | 작가의 활동량/인지도에 따라 면적 효과가 다르게 나타나는지 확인 | Cold | 0.4608 | J5 교차항: 활동량/인지도 x 면적 | LightGBM | 0.4516 | 3.1609 | 0.0092 | Cold에서 개선폭이 작아 보류 | experiments/track6/J5_activity_popularity_x_log_area/outputs/result_sheet.html |
| J4 | 작가의 활동량/인지도에 따라 호수 효과가 다르게 나타나는지 확인 | Cold | 0.4673 | J4 교차항: 활동량/인지도 x 호수 | LightGBM | 0.4544 | 3.1807 | 0.0128 | Cold에서 소폭 개선 후보 | experiments/track6/J4_activity_popularity_x_ln_ho/outputs/result_sheet.html |
| I5 | 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인 | Cold | 0.5128 | I5 후보: 작품 기본 피처 + 시장 노출/정보량 | LightGBM | 0.4598 | 3.0662 | 0.0530 | Cold에서 명확한 개선 후보 | experiments/track6/I5_basic_artwork_market_exposure_information/outputs/result_sheet.html |
| I2 | 작품 기본 피처와 세대/경력 메타를 함께 쓰면 Cold 예측력이 개선되는지 확인 | Cold | 0.5128 | I2 후보: 작품 기본 피처 + 세대/경력 | Quantile-LAD | 0.4643 | 3.4924 | 0.0485 | Cold에서 명확한 개선 후보 | experiments/track6/I2_basic_artwork_birth_exhibition_cold_candidate/outputs/result_sheet.html |
| I3 | 작품 기본 변수와 활동량/인지도 메타를 함께 쓰면 시장 노출 정도가 가격 예측에 도움 되는지 확인 | Cold | 0.5128 | I3 후보: 작품 기본 피처 + 활동량/인지도 | LightGBM | 0.4720 | 2.9687 | 0.0408 | Cold에서 명확한 개선 후보 | experiments/track6/I3_basic_artwork_activity_popularity_cold_candidate/outputs/result_sheet.html |
| I1 | 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인 | Cold | 0.5070 | I1 후보: 호수 + 세대/경력 | Quantile-LAD | 0.4769 | 3.6565 | 0.0301 | Cold에서 명확한 개선 후보 | experiments/track6/I1_ho_birth_exhibition_cold_candidate/outputs/result_sheet.html |
| J1 | 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인 | Cold | 0.4769 | J1 기준: 호수 + 세대/경력 | Quantile-LAD | 0.4769 | 3.6565 | 0.0000 | 기준선 개선 없음 | experiments/track6/J1_profile_x_ln_ho/outputs/result_sheet.html |

## 중복 매핑

| 실험 ID | 대체 실험 | 처리 |
|---|---|---|
| H2 | D8 | 작가명 x 면적은 기존 D8 실험으로 대체 |
| H3 | D9 | 작가명 x 재료는 기존 D9 실험으로 대체 |
| H4 | D10 | 작가명 x 지지체는 기존 D10 실험으로 대체 |
| I4 | G8 | 작품 기본 피처 + 기본 작가 프로필은 기존 G8 실험으로 대체 |

## 전체 H/I/J 결과

| 실험 ID | 실험명 | 범위 | 기준 MdAPE | 최고 변수 블록 | 최고 모델 | MdAPE | p95_APE | 기준선 대비 MdAPE 개선 | 해석 | 결과 HTML |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | 같은 호수라도 작가명에 따라 가격대가 다른지 확인 | Warm | 0.1801 | H1 교차항: 작가명 x 호수 | Huber | 0.1762 | 1.0038 | 0.0038 | Warm에서 개선폭이 작아 보류 | experiments/track6/H1_artist_name_x_ln_ho/outputs/result_sheet.html |
| H1 | 같은 호수라도 작가명에 따라 가격대가 다른지 확인 | Cold | 0.5062 | H1 기준: 작가명 + 호수 | LightGBM | 0.5062 | 3.7913 | 0.0000 | 기준선 개선 없음 | experiments/track6/H1_artist_name_x_ln_ho/outputs/result_sheet.html |
| H5 | 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인 | Warm | 0.4270 | H5 교차항: 작가명 x 깊이 | Huber | 0.4225 | 2.8961 | 0.0045 | Warm에서 개선폭이 작아 보류 | experiments/track6/H5_artist_name_x_depth/outputs/result_sheet.html |
| H5 | 같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인 | Cold | 0.6519 | H5 교차항: 작가명 x 깊이 | LightGBM | 0.6514 | 4.7926 | 0.0006 | Cold에서 개선폭이 작아 보류 | experiments/track6/H5_artist_name_x_depth/outputs/result_sheet.html |
| I1 | 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인 | Warm | 0.5244 | I1 후보: 호수 + 세대/경력 | Huber | 0.5169 | 2.9084 | 0.0075 | Warm에서 개선폭이 작아 보류 | experiments/track6/I1_ho_birth_exhibition_cold_candidate/outputs/result_sheet.html |
| I1 | 호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인 | Cold | 0.5070 | I1 후보: 호수 + 세대/경력 | Quantile-LAD | 0.4769 | 3.6565 | 0.0301 | Cold에서 명확한 개선 후보 | experiments/track6/I1_ho_birth_exhibition_cold_candidate/outputs/result_sheet.html |
| I2 | 작품 기본 피처와 세대/경력 메타를 함께 쓰면 Cold 예측력이 개선되는지 확인 | Warm | 0.4962 | I2 기준: 작품 기본 피처 | Huber | 0.4962 | 2.9236 | 0.0000 | 기준선 개선 없음 | experiments/track6/I2_basic_artwork_birth_exhibition_cold_candidate/outputs/result_sheet.html |
| I2 | 작품 기본 피처와 세대/경력 메타를 함께 쓰면 Cold 예측력이 개선되는지 확인 | Cold | 0.5128 | I2 후보: 작품 기본 피처 + 세대/경력 | Quantile-LAD | 0.4643 | 3.4924 | 0.0485 | Cold에서 명확한 개선 후보 | experiments/track6/I2_basic_artwork_birth_exhibition_cold_candidate/outputs/result_sheet.html |
| I3 | 작품 기본 변수와 활동량/인지도 메타를 함께 쓰면 시장 노출 정도가 가격 예측에 도움 되는지 확인 | Warm | 0.4962 | I3 후보: 작품 기본 피처 + 활동량/인지도 | Huber | 0.4819 | 2.6597 | 0.0143 | Warm에서 소폭 개선 후보 | experiments/track6/I3_basic_artwork_activity_popularity_cold_candidate/outputs/result_sheet.html |
| I3 | 작품 기본 변수와 활동량/인지도 메타를 함께 쓰면 시장 노출 정도가 가격 예측에 도움 되는지 확인 | Cold | 0.5128 | I3 후보: 작품 기본 피처 + 활동량/인지도 | LightGBM | 0.4720 | 2.9687 | 0.0408 | Cold에서 명확한 개선 후보 | experiments/track6/I3_basic_artwork_activity_popularity_cold_candidate/outputs/result_sheet.html |
| I5 | 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인 | Warm | 0.4962 | I5 후보: 작품 기본 피처 + 시장 노출/정보량 | Huber | 0.4727 | 2.7022 | 0.0235 | Warm에서 소폭 개선 후보 | experiments/track6/I5_basic_artwork_market_exposure_information/outputs/result_sheet.html |
| I5 | 작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인 | Cold | 0.5128 | I5 후보: 작품 기본 피처 + 시장 노출/정보량 | LightGBM | 0.4598 | 3.0662 | 0.0530 | Cold에서 명확한 개선 후보 | experiments/track6/I5_basic_artwork_market_exposure_information/outputs/result_sheet.html |
| I6 | 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인 | Warm | 0.4779 | I6 후보: 실제 크기 확장 + 전체 작가 메타 | Huber | 0.4156 | 2.6607 | 0.0623 | Warm에서 명확한 개선 후보 | experiments/track6/I6_extended_size_full_artist_meta/outputs/result_sheet.html |
| I6 | 실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인 | Cold | 0.5017 | I6 후보: 실제 크기 확장 + 전체 작가 메타 | Quantile-LAD | 0.4802 | 3.5526 | 0.0215 | Cold에서 소폭 개선 후보 | experiments/track6/I6_extended_size_full_artist_meta/outputs/result_sheet.html |
| J1 | 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인 | Warm | 0.5169 | J1 기준: 호수 + 세대/경력 | Huber | 0.5169 | 2.9084 | 0.0000 | 기준선 개선 없음 | experiments/track6/J1_profile_x_ln_ho/outputs/result_sheet.html |
| J1 | 작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인 | Cold | 0.4769 | J1 기준: 호수 + 세대/경력 | Quantile-LAD | 0.4769 | 3.6565 | 0.0000 | 기준선 개선 없음 | experiments/track6/J1_profile_x_ln_ho/outputs/result_sheet.html |
| J2 | 작가의 세대/경력 단계에 따라 재료 효과가 다르게 나타나는지 확인 | Warm | 0.7132 | J2 기준: 세대/경력 + 재료 | Huber | 0.7132 | 6.2264 | 0.0000 | 교차항 복잡도 대비 성능 약함 | experiments/track6/J2_profile_x_material/outputs/result_sheet.html |
| J2 | 작가의 세대/경력 단계에 따라 재료 효과가 다르게 나타나는지 확인 | Cold | 0.7047 | J2 기준: 세대/경력 + 재료 | Quantile-LAD | 0.7047 | 7.6066 | 0.0000 | 교차항 복잡도 대비 성능 약함 | experiments/track6/J2_profile_x_material/outputs/result_sheet.html |
| J3 | 작가의 세대/경력 단계에 따라 난트 지지체 효과가 다르게 나타나는지 확인 | Warm | 0.7401 | J3 교차항: 세대/경력 x 지지체 | Huber | 0.7284 | 5.9658 | 0.0117 | Warm에서 소폭 개선 후보 | experiments/track6/J3_profile_x_support/outputs/result_sheet.html |
| J3 | 작가의 세대/경력 단계에 따라 난트 지지체 효과가 다르게 나타나는지 확인 | Cold | 0.7022 | J3 기준: 세대/경력 + 지지체 | Quantile-LAD | 0.7022 | 7.2842 | 0.0000 | 교차항 복잡도 대비 성능 약함 | experiments/track6/J3_profile_x_support/outputs/result_sheet.html |
| J4 | 작가의 활동량/인지도에 따라 호수 효과가 다르게 나타나는지 확인 | Warm | 0.5264 | J4 교차항: 활동량/인지도 x 호수 | Huber | 0.4902 | 2.6768 | 0.0362 | Warm에서 명확한 개선 후보 | experiments/track6/J4_activity_popularity_x_ln_ho/outputs/result_sheet.html |
| J4 | 작가의 활동량/인지도에 따라 호수 효과가 다르게 나타나는지 확인 | Cold | 0.4673 | J4 교차항: 활동량/인지도 x 호수 | LightGBM | 0.4544 | 3.1807 | 0.0128 | Cold에서 소폭 개선 후보 | experiments/track6/J4_activity_popularity_x_ln_ho/outputs/result_sheet.html |
| J5 | 작가의 활동량/인지도에 따라 면적 효과가 다르게 나타나는지 확인 | Warm | 0.4793 | J5 교차항: 활동량/인지도 x 면적 | Huber | 0.4754 | 2.5575 | 0.0038 | Warm에서 개선폭이 작아 보류 | experiments/track6/J5_activity_popularity_x_log_area/outputs/result_sheet.html |
| J5 | 작가의 활동량/인지도에 따라 면적 효과가 다르게 나타나는지 확인 | Cold | 0.4608 | J5 교차항: 활동량/인지도 x 면적 | LightGBM | 0.4516 | 3.1609 | 0.0092 | Cold에서 개선폭이 작아 보류 | experiments/track6/J5_activity_popularity_x_log_area/outputs/result_sheet.html |
| J6 | 작가 기본 프로필에 따라 재료 효과가 다르게 나타나는지 확인 | Warm | 0.7222 | J6 교차항: 기본 프로필 x 재료 | Huber | 0.7003 | 6.4328 | 0.0218 | Warm에서 소폭 개선 후보 | experiments/track6/J6_profile_x_material/outputs/result_sheet.html |
| J6 | 작가 기본 프로필에 따라 재료 효과가 다르게 나타나는지 확인 | Cold | 0.6920 | J6 기준: 기본 프로필 + 재료 | Quantile-LAD | 0.6920 | 6.8645 | 0.0000 | 교차항 복잡도 대비 성능 약함 | experiments/track6/J6_profile_x_material/outputs/result_sheet.html |
| J7 | 작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타나는지 확인 | Warm | 0.7660 | J7 교차항: 시장 노출/정보량 x 깊이 | Huber | 0.7582 | 5.8385 | 0.0078 | Warm에서 개선폭이 작아 보류 | experiments/track6/J7_market_exposure_x_depth/outputs/result_sheet.html |
| J7 | 작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타나는지 확인 | Cold | 0.6793 | J7 기준: 시장 노출/정보량 + 깊이 | LightGBM | 0.6793 | 4.7550 | 0.0000 | 교차항 복잡도 대비 성능 약함 | experiments/track6/J7_market_exposure_x_depth/outputs/result_sheet.html |
