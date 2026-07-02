# PP-WMIN10 Warm WMIN8 API Fixed-Test Parity

- 작성일: 2026-06-16 16:42:08
- 실행 시간: 9.3s
- 비교 후보: `min1_route_w850_risk_q50_altlower_gap005`
- 목적: WMIN8 fixed test 607건을 official v0.1 HTTP API로 재생해 endpoint 출력과 실험 산출물의 row-level parity를 확인한다.

## 1. Summary

| n_total | n_success | n_error | n_wrong_route | n_wrong_adapter | max_abs_log_diff | mean_abs_log_diff | median_abs_log_diff | p95_abs_log_diff | max_abs_price_diff_pct | mean_abs_price_diff_pct | n_log_diff_le_1e_10 | n_log_diff_le_1e_3 | n_log_diff_le_1e_2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 607 | 607 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 607 | 607 | 607 |

## 2. Largest Absolute Log Differences

| _track6_row_id | artist_key | expected_wmin8_pred_log | api_final_log_price | log_diff | expected_wmin8_price_krw | api_price_krw | price_diff_pct | api_selected_runtime_role | expected_stable_price_band | api_stable_price_band |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24244 | seunghun sim | 13.1884252419877 | 13.188425241987703 | 5.3290705182007506e-15 | 534146 | 534146 | 0.0 | base_w700 | mid_price | mid_price |
| 11782 | ej koh | 13.349461392766624 | 13.34946139276662 | -5.3290705182007506e-15 | 627476 | 627476 | 0.0 | base_w700 | mid_price | mid_price |
| 16212 | jin taek | 15.869435235839967 | 15.869435235839973 | 5.3290705182007506e-15 | 7798448 | 7798448 | 0.0 | base_w700 | high_price | high_price |
| 52775 | sungju ham | 14.767377134203592 | 14.767377134203588 | -5.3290705182007506e-15 | 2590541 | 2590541 | 0.0 | base_w700 | high_price | high_price |
| 18594 | jaeho park | 15.5957637598233 | 15.595763759823305 | 5.3290705182007506e-15 | 5931358 | 5931358 | 0.0 | base_w700 | high_price | high_price |
| 25308 | kim tschang yeul | 15.481427006077626 | 15.48142700607762 | -5.3290705182007506e-15 | 5290520 | 5290520 | 0.0 | base_w700 | high_price | high_price |
| 6223 | dongju kim | 15.579530007304363 | 15.579530007304369 | 5.3290705182007506e-15 | 5835847 | 5835847 | 0.0 | base_w700 | high_price | high_price |
| 5798 | injung kwon | 12.800231621897478 | 12.80023162189748 | 3.552713678800501e-15 | 362301 | 362301 | 0.0 | base_w700 | low_price | low_price |
| 20286 | ouchul hwang | 15.950287414856067 | 15.95028741485607 | 3.552713678800501e-15 | 8455160 | 8455160 | 0.0 | base_w700 | high_price | high_price |
| 16303 | yona oh | 13.880057050073484 | 13.880057050073487 | 3.552713678800501e-15 | 1066675 | 1066675 | 0.0 | base_w700 | mid_price | mid_price |
| 25267 | kim tschang yeul | 15.409790684622743 | 15.409790684622749 | 3.552713678800501e-15 | 4924783 | 4924783 | 0.0 | base_w700 | high_price | high_price |
| 25307 | kim tschang yeul | 15.409790684622743 | 15.409790684622749 | 3.552713678800501e-15 | 4924783 | 4924783 | 0.0 | base_w700 | high_price | high_price |
| 16541 | eunjoo choi | 14.870913565419595 | 14.8709135654196 | 3.552713678800501e-15 | 2873133 | 2873133 | 0.0 | base_w700 | high_price | high_price |
| 48783 | aeri lee 이애리 | 16.940779350119332 | 16.940779350119335 | 3.552713678800501e-15 | 22766014 | 22766014 | 0.0 | base_w700 | very_high_price | very_high_price |
| 6172 | guem eye | 17.409832609944402 | 17.409832609944406 | 3.552713678800501e-15 | 36391020 | 36391020 | 0.0 | base_w700 | very_high_price | very_high_price |
| 6155 | sheean kim | 18.714018160276964 | 18.714018160276968 | 3.552713678800501e-15 | 134089515 | 134089515 | 0.0 | base_w700 | very_high_price | very_high_price |
| 35317 | yeonsoo kim 김연수 | 15.162804998169657 | 15.16280499816966 | 3.552713678800501e-15 | 3847003 | 3847003 | 0.0 | base_w700 | high_price | high_price |
| 53070 | junmin shin | 14.00061789273938 | 14.000617892739385 | 3.552713678800501e-15 | 1203348 | 1203348 | 0.0 | base_w700 | mid_price | mid_price |
| 16774 | seok young kim | 16.656044222019236 | 16.656044222019233 | -3.552713678800501e-15 | 17124902 | 17124902 | 0.0 | base_w700 | very_high_price | very_high_price |
| 53438 | tomotoshi hoshino | 15.24017951925937 | 15.240179519259366 | -3.552713678800501e-15 | 4156482 | 4156482 | 0.0 | base_w700 | high_price | high_price |

## 3. Interpretation

- `max_abs_log_diff`가 0에 가까우면 API endpoint가 WMIN8 실험 산출물과 동일한 계산 경로를 재현한다.
- 차이가 크면 우선 `stable_price_band`, `component_prediction_spread`, `current_vs_stable_gap_abs` 및 라우팅 선택 차이를 확인한다.
