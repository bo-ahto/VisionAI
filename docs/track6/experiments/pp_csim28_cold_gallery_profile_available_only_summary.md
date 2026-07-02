# Cold 갤러리/전시 정보 보유 입력 전용 검증

- 작성일: 2026-06-22T15:39:46
- 목적: 갤러리 또는 전시 정보가 실제로 있는 입력만 대상으로 학습/검증/테스트했을 때 해당 문맥 피처가 도움이 되는지 확인한다.
- 엄격 조건: `artist_key`, 동일 작가 가격 이력, artist_key lookup, `search_*`, 외부 live 검색 미사용.
- 필터 조건: `gallery_tier_any_available_flag > 0 OR artist_exhibition_available_count > 0`.

## 1. 필터 후 평가 행 수
| split | before_n | after_n | kept_rate |
| --- | --- | --- | --- |
| train | 26914 | 16304 | 0.605781 |
| validation | 2753 | 1902 | 0.690883 |
| test | 3099 | 1734 | 0.559535 |

## 2. Test 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_model_features | n_similarity_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_profile_available_artwork_similarity_k80 | test | 0.451528 | 1.431171 | 4.135090 | 0.877505 | 189 | 65 | 54 | 37 | 12 | 정보 보유 행만 사용하되 모델 구조는 기본 작품/작가 메타 + 작품 유사 이웃 |
| direct_gallery_profile_available_k80 | test | 0.446871 | 1.432107 | 3.492727 | 0.876979 | 189 | 65 | 54 | 63 | 12 | 정보 보유 행에서 갤러리/전시 문맥을 모델 입력에 직접 추가 |
| direct_and_similarity_gallery_profile_available_k80 | test | 0.561278 | 1.881783 | 7.560964 | 1.005674 | 223 | 123 | 43 | 63 | 44 | 정보 보유 행에서 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용 |
| similarity_gallery_profile_available_k80 | test | 0.587363 | 2.005294 | 6.706754 | 1.025646 | 264 | 125 | 43 | 37 | 44 | 정보 보유 행에서 갤러리/전시 문맥은 유사 이웃 선택에만 사용 |

## 3. Validation 결과
| candidate | split | MdAPE | MAPE | p95_APE | RMSE_log | APE_gt_2 | APE_gt_5 | APE_gt_10 | n_model_features | n_similarity_features | policy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_profile_available_artwork_similarity_k80 | validation | 0.335991 | 0.400802 | 1.044769 | 0.529104 | 13 | 0 | 0 | 37 | 12 | 정보 보유 행만 사용하되 모델 구조는 기본 작품/작가 메타 + 작품 유사 이웃 |
| direct_gallery_profile_available_k80 | validation | 0.328267 | 0.411849 | 0.963054 | 0.518745 | 27 | 0 | 0 | 63 | 12 | 정보 보유 행에서 갤러리/전시 문맥을 모델 입력에 직접 추가 |
| similarity_gallery_profile_available_k80 | validation | 0.424388 | 1.522871 | 6.313166 | 0.922238 | 296 | 131 | 43 | 37 | 44 | 정보 보유 행에서 갤러리/전시 문맥은 유사 이웃 선택에만 사용 |
| direct_and_similarity_gallery_profile_available_k80 | validation | 0.435887 | 1.662664 | 6.249298 | 0.938795 | 278 | 115 | 48 | 63 | 44 | 정보 보유 행에서 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용 |

## 4. 필터 후 갤러리/전시 커버리지
| split | n | gallery_any_n | gallery_any_rate | gallery_validated_n | gallery_validated_rate | exhibition_available_n | exhibition_available_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | 16304 | 16304 | 1.000000 | 19 | 0.001165 | 16284 | 0.998773 |
| validation | 1902 | 1902 | 1.000000 | 0 | 0.000000 | 1902 | 1.000000 |
| test | 1734 | 1734 | 1.000000 | 32 | 0.018454 | 1693 | 0.976355 |

## 5. 가격대별 Test 진단
| candidate | split | segment | n | MdAPE | MAPE | p95_APE | APE_gt_2 | APE_gt_5 | APE_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_profile_available_artwork_similarity_k80 | test | 1m_3m | 515 | 0.554709 | 0.798945 | 2.237519 | 41 | 5 | 0 |
| base_profile_available_artwork_similarity_k80 | test | 3m_10m | 637 | 0.343449 | 0.376515 | 0.877248 | 0 | 0 | 0 |
| base_profile_available_artwork_similarity_k80 | test | gt_10m | 175 | 0.428093 | 0.425661 | 0.755308 | 0 | 0 | 0 |
| base_profile_available_artwork_similarity_k80 | test | lt_1m | 407 | 1.100651 | 4.314160 | 29.075770 | 148 | 60 | 54 |
| direct_and_similarity_gallery_profile_available_k80 | test | 1m_3m | 515 | 0.679427 | 0.987948 | 2.530640 | 53 | 6 | 4 |
| direct_and_similarity_gallery_profile_available_k80 | test | 3m_10m | 637 | 0.411785 | 0.462403 | 1.080240 | 0 | 0 | 0 |
| direct_and_similarity_gallery_profile_available_k80 | test | gt_10m | 175 | 0.420219 | 0.417530 | 0.795934 | 0 | 0 | 0 |
| direct_and_similarity_gallery_profile_available_k80 | test | lt_1m | 407 | 1.282758 | 5.863880 | 43.587838 | 170 | 117 | 39 |
| direct_gallery_profile_available_k80 | test | 1m_3m | 515 | 0.513771 | 0.813207 | 2.530890 | 39 | 5 | 0 |
| direct_gallery_profile_available_k80 | test | 3m_10m | 637 | 0.346930 | 0.383873 | 0.914434 | 0 | 0 | 0 |
| direct_gallery_profile_available_k80 | test | gt_10m | 175 | 0.405258 | 0.418014 | 0.749918 | 0 | 0 | 0 |
| direct_gallery_profile_available_k80 | test | lt_1m | 407 | 1.064127 | 4.291874 | 30.108637 | 150 | 60 | 54 |
| similarity_gallery_profile_available_k80 | test | 1m_3m | 515 | 0.779322 | 1.112433 | 2.929327 | 79 | 6 | 4 |
| similarity_gallery_profile_available_k80 | test | 3m_10m | 637 | 0.405245 | 0.484828 | 1.200599 | 2 | 0 | 0 |
| similarity_gallery_profile_available_k80 | test | gt_10m | 175 | 0.374087 | 0.398878 | 0.813126 | 0 | 0 | 0 |
| similarity_gallery_profile_available_k80 | test | lt_1m | 407 | 1.402214 | 6.205496 | 46.814200 | 183 | 119 | 39 |

## 6. 후보 정의
### base_profile_available_artwork_similarity_k80
- 정책: 정보 보유 행만 사용하되 모델 구조는 기본 작품/작가 메타 + 작품 유사 이웃
- 모델 입력 피처 수: 37
- 유사 이웃 선택 피처 수: 12

### direct_gallery_profile_available_k80
- 정책: 정보 보유 행에서 갤러리/전시 문맥을 모델 입력에 직접 추가
- 모델 입력 피처 수: 63
- 유사 이웃 선택 피처 수: 12

### similarity_gallery_profile_available_k80
- 정책: 정보 보유 행에서 갤러리/전시 문맥은 유사 이웃 선택에만 사용
- 모델 입력 피처 수: 37
- 유사 이웃 선택 피처 수: 44

### direct_and_similarity_gallery_profile_available_k80
- 정책: 정보 보유 행에서 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용
- 모델 입력 피처 수: 63
- 유사 이웃 선택 피처 수: 44

## 7. 해석 기준

- 이 결과는 전체 Cold가 아니라 갤러리/전시 정보가 있는 입력에 한정된 성능이다.
- 운영에서 사용자가 갤러리/전시 정보를 안정적으로 입력하거나 DB에서 검증해 붙일 수 있을 때만 적용 가능하다.
- 전체 Cold 기본 모델과 직접 비교하지 말고, 동일한 profile-available cohort 안에서 후보끼리 비교해야 한다.