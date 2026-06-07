# 0604 테스트 정확/근접 적중 분석

## 1. 결론

- 운영 기본 예측값 기준 정확히 같은 원화 가격으로 맞춘 건수: `0`건.
- 원화 단위로 반올림해도 정확히 같은 가격으로 맞춘 건수: `0`건.
- 가장 가까운 사례의 오차율: `0.000390`.
- 따라서 0604 테스트에서는 실제 가격을 숫자 단위로 그대로 맞춘 사례는 없고, 예측 기준선과 실제 판매가가 매우 가까웠던 근접 적중 사례가 존재함.

## 2. 분석 기준

- 정확 일치: `예측 원화 가격 == 실제 원화 가격`.
- 반올림 정확 일치: `예측 원화 가격을 1원 단위로 반올림한 값 == 실제 원화 가격`.
- 근접 적중: 절대 퍼센트 오차가 0.1%, 0.5%, 1%, 2%, 3%, 5%, 10% 이내인 경우.
- 분석 대상: 0604 신규 테스트 중 실제 숫자 가격 라벨이 있는 837건.

## 3. 후보별 정확/근접 적중 현황

| candidate | n | exact_krw_count | rounded_exact_krw_count | min_ape | median_ape | mean_ape | p95_ape | 0.1% 이내 | 0.5% 이내 | 1.0% 이내 | 3.0% 이내 | 5.0% 이내 | 10.0% 이내 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| service_primary | 837 | 0 | 0 | 0.000390 | 0.234214 | 14.285219 | 0.984422 | 1 (0.12%) | 9 (1.08%) | 20 (2.39%) | 57 (6.81%) | 98 (11.71%) | 191 (22.82%) |
| pp_v8_compact_blend_mape_guarded | 837 | 0 | 0 | 0.000390 | 0.234214 | 14.285219 | 0.984422 | 1 (0.12%) | 9 (1.08%) | 20 (2.39%) | 57 (6.81%) | 98 (11.71%) | 191 (22.82%) |
| v01_operational | 837 | 0 | 0 | 0.000231 | 0.283547 | 32.287906 | 0.999616 | 2 (0.24%) | 6 (0.72%) | 15 (1.79%) | 57 (6.81%) | 106 (12.66%) | 206 (24.61%) |
| svc_numeric_seed_mean | 837 | 0 | 0 | 0.000184 | 0.317406 | 47.269649 | 1.088190 | 2 (0.24%) | 11 (1.31%) | 23 (2.75%) | 50 (5.97%) | 96 (11.47%) | 177 (21.15%) |
| pp_v2_defensive | 837 | 0 | 0 | 0.001380 | 0.230289 | 15.575276 | 1.151349 | 0 (0.00%) | 2 (0.24%) | 11 (1.31%) | 46 (5.50%) | 78 (9.32%) | 200 (23.89%) |
| l10_generated_bucket_seq | 837 | 0 | 0 | 0.000246 | 0.328269 | 13.310076 | 1.325841 | 1 (0.12%) | 6 (0.72%) | 24 (2.87%) | 68 (8.12%) | 95 (11.35%) | 173 (20.67%) |

## 4. 화면 표시 반올림 기준 참고

- 모델 원값 기준으로는 정확 일치가 없지만, 화면에서 가격을 만원/10만원 단위로 둥글게 보여주면 실제 가격과 같은 값처럼 보이는 사례가 발생할 수 있음.
- 이 표는 운영 기본값만 기준으로 계산한 참고 지표이며, 모델이 정확히 맞췄다는 의미는 아님.

| currency | rounding_unit | n | rounded_display_match_count | rounded_display_match_rate |
| --- | --- | --- | --- | --- |
| KRW | 1 | 837 | 0 | 0.00% |
| KRW | 10 | 837 | 0 | 0.00% |
| KRW | 100 | 837 | 0 | 0.00% |
| KRW | 1,000 | 837 | 0 | 0.00% |
| KRW | 10,000 | 837 | 11 | 1.31% |
| KRW | 100,000 | 837 | 66 | 7.89% |
| KRW | 1,000,000 | 837 | 349 | 41.70% |
| USD | 1 | 837 | 1 | 0.12% |
| USD | 10 | 837 | 11 | 1.31% |
| USD | 100 | 837 | 71 | 8.48% |
| USD | 1,000 | 837 | 345 | 41.22% |

## 5. 운영 기본값 기준 상위 근접 적중 사례

| row_id | 작품명 | 작가 | 실제 KRW | 예측 KRW | 절대오차 KRW | APE | 비교 묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6745 | Behold the Tilting Wings | Jeongeun Han | 993,600 | 993,212 | 388 | 0.000390 | artist | 5 | acrylic__canvas |
| 5369 | Encounter No.11 | Molly Kim | 1,131,600 | 1,130,274 | 1,326 | 0.001171 | artist | 19 | oil__canvas |
| 8 | Still Life_FACE | PARKHA | 966,000 | 964,820 | 1,180 | 0.001221 | artist | 9 | oil__canvas |
| 6 | Still Life_SEESAW | PARKHA | 966,000 | 964,820 | 1,180 | 0.001221 | artist | 9 | oil__canvas |
| 14 | Always There | Yuzu Kim | 731,400 | 732,490 | 1,090 | 0.001491 | artist | 5 | acrylic__canvas |
| 3161 | Still Life #49 | Jaehyug CHOI  최재혁 | 16,560,000 | 16,593,008 | 33,008 | 0.001993 | artist_medium_support_size | 7 | oil__canvas |
| 3164 | Still Life #51 | Jaehyug CHOI  최재혁 | 16,560,000 | 16,593,008 | 33,008 | 0.001993 | artist_medium_support_size | 7 | oil__canvas |
| 922 | After the Light | Eunhyea Choi | 1,380,000 | 1,382,891 | 2,891 | 0.002095 | artist | 20 | acrylic__canvas |
| 134 | The Gaze | Jason Ha | 469,200 | 470,608 | 1,408 | 0.003000 | artist | 6 | acrylic__canvas |
| 5385 | A Moment 2/2 | Young Jae | 1,725,000 | 1,715,911 | 9,089 | 0.005269 | artist | 7 | mixed__paper |

## 6. 가장 가까운 사례 해석

- 작품: `Behold the Tilting Wings`.
- 작가: `Jeongeun Han`.
- 실제 가격: `993,600`원.
- 예측 가격: `993,212`원.
- 차이: `388`원.
- 오차율: `0.000390`.
- 비교 묶음: `artist`, 표본수 `5`건.
- 해석: 같은 작가의 과거 가격 기준선과 작품 크기/재료 조건이 실제 신규 가격대와 거의 일치하면서 운영 기본 결합값이 실제 가격 근처에 위치한 사례.
- 주의: 신규 실제 라벨을 모델 입력으로 사용한 것이 아니므로, 실제 가격을 복사해서 맞춘 구조는 아님.

## 7. 어떻게 가까워졌는가

- 운영 기본값은 `pp_v8_compact_blend_mape_guarded`.
- 계산 구조: `0.75 * 오차 안정화 후보 + 0.25 * 생성 버킷 순차 후보`를 로그 가격 공간에서 결합.
- 오차 안정화 후보: 큰 오차를 줄이도록 학습한 방어형 가격 기준.
- 생성 버킷 순차 후보: 크기, 재료/지지체, 가격 구간 정보를 더 세밀하게 반영한 후보.
- 가까운 사례는 두 후보가 비슷한 방향의 가격대를 가리키거나, 한 후보의 치우침을 다른 후보가 보완한 경우.

## 8. 근접 적중 사례의 공통 특성

| group | n | median_actual_krw | median_actual_usd_equiv | median_area_cm2 | median_svc_group_n | median_quantile_width | median_price_range_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_numeric_labels | 837 | 2760000.00 | 2000.00 | 3660.25 | 9.00 | 1.58 | 4.84 |
| near_1pct | 20 | 1552500.00 | 1125.00 | 2398.25 | 7.00 | 1.34 | 3.83 |
| near_3pct | 57 | 1449000.00 | 1050.00 | 2411.50 | 7.00 | 1.46 | 4.31 |
| near_5pct | 98 | 2642000.00 | 1914.49 | 3350.15 | 8.50 | 1.38 | 3.99 |

| threshold | segment_column | segment_value | near_count | near_share | all_count | hit_rate_within_segment |
| --- | --- | --- | --- | --- | --- | --- |
| <=1% | svc_group_level | artist | 13 | 65.0% | 414 | 3.1% |
| <=1% | svc_group_level | artist_medium_support_size | 5 | 25.0% | 91 | 5.5% |
| <=1% | svc_group_level | artist_size | 2 | 10.0% | 226 | 0.9% |
| <=1% | medium_support_bucket | acrylic__canvas | 7 | 35.0% | 214 | 3.3% |
| <=1% | medium_support_bucket | oil__canvas | 7 | 35.0% | 130 | 5.4% |
| <=1% | medium_support_bucket | mixed__paper | 4 | 20.0% | 36 | 11.1% |
| <=1% | medium_support_bucket | acrylic__linen | 1 | 5.0% | 5 | 20.0% |
| <=1% | medium_support_bucket | mixed__canvas | 1 | 5.0% | 62 | 1.6% |
| <=3% | svc_group_level | artist | 39 | 68.4% | 414 | 9.4% |
| <=3% | svc_group_level | artist_medium_support_size | 10 | 17.5% | 91 | 11.0% |
| <=3% | svc_group_level | artist_size | 7 | 12.3% | 226 | 3.1% |
| <=3% | svc_group_level | medium_support_size | 1 | 1.8% | 66 | 1.5% |
| <=3% | medium_support_bucket | acrylic__canvas | 20 | 35.1% | 214 | 9.3% |
| <=3% | medium_support_bucket | oil__canvas | 14 | 24.6% | 130 | 10.8% |
| <=3% | medium_support_bucket | mixed__paper | 7 | 12.3% | 36 | 19.4% |
| <=3% | medium_support_bucket | mixed__canvas | 4 | 7.0% | 62 | 6.5% |
| <=3% | medium_support_bucket | other__paper | 2 | 3.5% | 62 | 3.2% |
| <=3% | medium_support_bucket | acrylic__linen | 1 | 1.8% | 5 | 20.0% |
| <=3% | medium_support_bucket | ink__other | 1 | 1.8% | 6 | 16.7% |
| <=3% | medium_support_bucket | other__other | 1 | 1.8% | 72 | 1.4% |
| <=3% | medium_support_bucket | acrylic__other | 1 | 1.8% | 9 | 11.1% |
| <=3% | medium_support_bucket | ink__paper | 1 | 1.8% | 15 | 6.7% |
| <=3% | medium_support_bucket | oil__linen | 1 | 1.8% | 40 | 2.5% |
| <=3% | medium_support_bucket | acrylic__panel | 1 | 1.8% | 8 | 12.5% |
| <=5% | svc_group_level | artist | 50 | 51.0% | 414 | 12.1% |
| <=5% | svc_group_level | artist_size | 33 | 33.7% | 226 | 14.6% |
| <=5% | svc_group_level | artist_medium_support_size | 12 | 12.2% | 91 | 13.2% |
| <=5% | svc_group_level | medium_support_size | 3 | 3.1% | 66 | 4.5% |
| <=5% | medium_support_bucket | acrylic__canvas | 40 | 40.8% | 214 | 18.7% |
| <=5% | medium_support_bucket | oil__canvas | 22 | 22.4% | 130 | 16.9% |
| <=5% | medium_support_bucket | mixed__paper | 7 | 7.1% | 36 | 19.4% |
| <=5% | medium_support_bucket | other__paper | 5 | 5.1% | 62 | 8.1% |
| <=5% | medium_support_bucket | mixed__canvas | 4 | 4.1% | 62 | 6.5% |
| <=5% | medium_support_bucket | pigment__paper | 3 | 3.1% | 33 | 9.1% |
| <=5% | medium_support_bucket | acrylic__linen | 2 | 2.0% | 5 | 40.0% |
| <=5% | medium_support_bucket | ink__other | 2 | 2.0% | 6 | 33.3% |
| <=5% | medium_support_bucket | pencil__paper | 2 | 2.0% | 14 | 14.3% |
| <=5% | medium_support_bucket | pigment__canvas | 2 | 2.0% | 16 | 12.5% |
| <=5% | medium_support_bucket | other__other | 1 | 1.0% | 72 | 1.4% |
| <=5% | medium_support_bucket | acrylic__other | 1 | 1.0% | 9 | 11.1% |

## 9. 보고용 해석

- 원값 기준으로 정확히 맞춘 가격은 없음.
- 화면 표시 반올림 기준으로 같아 보이는 값은 있을 수 있으므로, 보고 시 원값 기준과 표시값 기준을 구분해야 함.
- 1% 이내 근접 적중은 운영 기본값 기준 20건.
- 근접 적중은 주로 같은 작가 기준선이 확보된 작품에서 발생.
- 특히 oil/acrylic canvas처럼 학습 데이터에 반복적으로 등장하는 재료/지지체에서 가격 기준이 안정적으로 잡힘.
- 정확 일치가 없다는 점은 모델이 특정 정답 가격을 외운 것이 아니라 연속 가격을 예측하고 있음을 보여줌.
- 가까운 사례 분석은 이후 구간별 보정이나 작가별 가격 기준선 보정의 근거로 활용 가능.

## 10. 산출물

- 후보별 요약: `outputs/candidate_exact_near_match_summary.csv`.
- 운영 기본값 상위 근접 사례: `outputs/service_primary_top_near_matches.csv`.
- 근접 적중 구간 요약: `outputs/service_primary_near_match_segment_summary.csv`.
- 수치 프로파일: `outputs/service_primary_near_match_numeric_profile.csv`.
- 화면 표시 반올림 기준 요약: `outputs/service_primary_display_rounding_match_summary.csv`.
