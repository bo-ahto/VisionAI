# PP-WMIN8B Warm min1 잔차 재진단 및 보정 스택 재구축

- 작성일: 2026-06-12 23:36
- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건
- 선택 기준: validation OOF에서 생성한 segment 보정 후보 + WMIN4 decision layer
- fixed test: 확인용
- 0604: 사용하지 않음
- 결론: validation_pass_fixed_hold / `min1_route_w850_risk_q50_altlower_gap005`
- 판단 근거: validation gate는 통과했지만 fixed test에서 WMIN8 대비 일부 지표 trade-off가 있어 보류

## 1. 후보별 교체 판단
| candidate_label | passes_validation_gate | passes_fixed_confirmation | fixed_validation_MdAPE | fixed_validation_MAPE | fixed_validation_p95_APE | validation_avg_MAPE_win_rate | validation_avg_p95_win_rate | validation_replacement_score | fixed_test_MdAPE | fixed_test_MAPE | fixed_test_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p5 | True | True | 0.096295 | 0.174901 | 0.574278 | 0.998077 | 0.981410 | -0.030727 | 0.104517 | 0.235974 | 0.742681 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p5 | True | True | 0.096295 | 0.174901 | 0.574278 | 0.998077 | 0.981410 | -0.030727 | 0.104517 | 0.235974 | 0.742681 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p5 | True | True | 0.096295 | 0.174901 | 0.574278 | 0.998077 | 0.981410 | -0.030727 | 0.104517 | 0.235974 | 0.742681 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p35 | True | True | 0.096295 | 0.174906 | 0.574278 | 0.998077 | 0.981410 | -0.030723 | 0.104517 | 0.235974 | 0.742681 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p35 | True | True | 0.096295 | 0.174906 | 0.574278 | 0.998077 | 0.981410 | -0.030723 | 0.104517 | 0.235974 | 0.742681 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p35 | True | True | 0.096295 | 0.174906 | 0.574278 | 0.998077 | 0.981410 | -0.030723 | 0.104517 | 0.235974 | 0.742681 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p35_riskq50 | True | True | 0.094033 | 0.174975 | 0.571291 | 0.998077 | 0.982051 | -0.030654 | 0.104517 | 0.235940 | 0.739622 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p5_riskq50 | True | True | 0.094033 | 0.174975 | 0.571291 | 0.998077 | 0.982051 | -0.030654 | 0.104517 | 0.235940 | 0.739622 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p35_riskq50 | True | True | 0.094033 | 0.174975 | 0.571291 | 0.998077 | 0.982051 | -0.030654 | 0.104517 | 0.235940 | 0.739622 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p5_riskq50 | True | True | 0.094033 | 0.174975 | 0.571291 | 0.998077 | 0.982051 | -0.030654 | 0.104517 | 0.235940 | 0.739622 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p35_riskq50 | True | True | 0.094033 | 0.174975 | 0.571291 | 0.998077 | 0.982051 | -0.030654 | 0.104517 | 0.235940 | 0.739622 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p5_riskq50 | True | True | 0.094033 | 0.174975 | 0.571291 | 0.998077 | 0.982051 | -0.030654 | 0.104517 | 0.235940 | 0.739622 |
| min1_wmin8b_seg_route_flag_min20_cap0p005_s0p5_riskq70 | True | True | 0.094033 | 0.174980 | 0.573670 | 0.998077 | 0.982051 | -0.030649 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p005_s0p5_riskq70 | True | True | 0.094033 | 0.174980 | 0.573670 | 0.998077 | 0.982051 | -0.030649 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p005_s0p5_riskq70 | True | True | 0.094033 | 0.174980 | 0.573670 | 0.998077 | 0.982051 | -0.030649 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min20_cap0p01_s0p5_riskq70 | True | True | 0.094033 | 0.174986 | 0.573670 | 0.998077 | 0.982051 | -0.030642 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min20_cap0p02_s0p5_riskq70 | True | True | 0.094033 | 0.174986 | 0.573670 | 0.998077 | 0.982051 | -0.030642 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p01_s0p5_riskq70 | True | True | 0.094033 | 0.174986 | 0.573670 | 0.998077 | 0.982051 | -0.030642 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p02_s0p5_riskq70 | True | True | 0.094033 | 0.174986 | 0.573670 | 0.998077 | 0.982051 | -0.030642 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p01_s0p5_riskq70 | True | True | 0.094033 | 0.174986 | 0.573670 | 0.998077 | 0.982051 | -0.030642 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p02_s0p5_riskq70 | True | True | 0.094033 | 0.174986 | 0.573670 | 0.998077 | 0.982051 | -0.030642 | 0.106547 | 0.235784 | 0.740586 |
| min1_wmin8b_seg_route_flag_min20_cap0p0025_s0p5_riskq60 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.981410 | -0.030641 | 0.104951 | 0.235844 | 0.739553 |
| min1_wmin8b_seg_route_flag_min35_cap0p0025_s0p5_riskq60 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.981410 | -0.030641 | 0.104951 | 0.235844 | 0.739553 |
| min1_wmin8b_seg_route_flag_min50_cap0p0025_s0p5_riskq60 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.981410 | -0.030641 | 0.104951 | 0.235844 | 0.739553 |
| min1_wmin8b_seg_route_flag_min20_cap0p0025_s0p5_riskq50 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.981410 | -0.030641 | 0.104951 | 0.235804 | 0.739553 |
| min1_wmin8b_seg_route_flag_min35_cap0p0025_s0p5_riskq50 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.981410 | -0.030641 | 0.104951 | 0.235804 | 0.739553 |
| min1_wmin8b_seg_route_flag_min50_cap0p0025_s0p5_riskq50 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.981410 | -0.030641 | 0.104951 | 0.235804 | 0.739553 |
| min1_wmin8b_seg_route_flag_min20_cap0p0025_s0p5_riskq70 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.982051 | -0.030640 | 0.105624 | 0.235772 | 0.739553 |
| min1_wmin8b_seg_route_flag_min35_cap0p0025_s0p5_riskq70 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.982051 | -0.030640 | 0.105624 | 0.235772 | 0.739553 |
| min1_wmin8b_seg_route_flag_min50_cap0p0025_s0p5_riskq70 | True | True | 0.094033 | 0.174988 | 0.571291 | 0.998077 | 0.982051 | -0.030640 | 0.105624 | 0.235772 | 0.739553 |
| min1_wmin8b_seg_route_flag_min20_cap0p0025_s0p35_riskq60 | True | True | 0.094033 | 0.174989 | 0.571291 | 0.998077 | 0.981410 | -0.030639 | 0.104951 | 0.235844 | 0.739553 |
| min1_wmin8b_seg_route_flag_min35_cap0p0025_s0p35_riskq60 | True | True | 0.094033 | 0.174989 | 0.571291 | 0.998077 | 0.981410 | -0.030639 | 0.104951 | 0.235844 | 0.739553 |
| min1_wmin8b_seg_route_flag_min50_cap0p0025_s0p35_riskq60 | True | True | 0.094033 | 0.174989 | 0.571291 | 0.998077 | 0.981410 | -0.030639 | 0.104951 | 0.235844 | 0.739553 |
| min1_wmin8b_seg_route_flag_min20_cap0p0025_s0p35_riskq50 | True | True | 0.094033 | 0.174990 | 0.571291 | 0.998077 | 0.981410 | -0.030639 | 0.104951 | 0.235804 | 0.739553 |
| min1_wmin8b_seg_route_flag_min35_cap0p0025_s0p35_riskq50 | True | True | 0.094033 | 0.174990 | 0.571291 | 0.998077 | 0.981410 | -0.030639 | 0.104951 | 0.235804 | 0.739553 |
| min1_wmin8b_seg_route_flag_min50_cap0p0025_s0p35_riskq50 | True | True | 0.094033 | 0.174990 | 0.571291 | 0.998077 | 0.981410 | -0.030639 | 0.104951 | 0.235804 | 0.739553 |
| min1_wmin8b_seg_route_flag_min20_cap0p0025_s0p35_riskq70 | True | True | 0.094033 | 0.174990 | 0.571291 | 0.998077 | 0.982051 | -0.030639 | 0.105624 | 0.235772 | 0.739553 |
| min1_wmin8b_seg_route_flag_min35_cap0p0025_s0p35_riskq70 | True | True | 0.094033 | 0.174990 | 0.571291 | 0.998077 | 0.982051 | -0.030639 | 0.105624 | 0.235772 | 0.739553 |
| min1_wmin8b_seg_route_flag_min50_cap0p0025_s0p35_riskq70 | True | True | 0.094033 | 0.174990 | 0.571291 | 0.998077 | 0.982051 | -0.030639 | 0.105624 | 0.235772 | 0.739553 |
| min1_wmin8b_seg_route_flag_min20_cap0p005_s0p5_riskq60 | True | True | 0.094407 | 0.174997 | 0.573670 | 0.998077 | 0.981410 | -0.030631 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p005_s0p5_riskq60 | True | True | 0.094407 | 0.174997 | 0.573670 | 0.998077 | 0.981410 | -0.030631 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p005_s0p5_riskq60 | True | True | 0.094407 | 0.174997 | 0.573670 | 0.998077 | 0.981410 | -0.030631 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p35_riskq60 | True | True | 0.094033 | 0.175003 | 0.571291 | 0.998077 | 0.982051 | -0.030625 | 0.104517 | 0.235912 | 0.739622 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p5_riskq60 | True | True | 0.094033 | 0.175003 | 0.571291 | 0.998077 | 0.982051 | -0.030625 | 0.104517 | 0.235912 | 0.739622 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p35_riskq60 | True | True | 0.094033 | 0.175003 | 0.571291 | 0.998077 | 0.982051 | -0.030625 | 0.104517 | 0.235912 | 0.739622 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p5_riskq60 | True | True | 0.094033 | 0.175003 | 0.571291 | 0.998077 | 0.982051 | -0.030625 | 0.104517 | 0.235912 | 0.739622 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p35_riskq60 | True | True | 0.094033 | 0.175003 | 0.571291 | 0.998077 | 0.982051 | -0.030625 | 0.104517 | 0.235912 | 0.739622 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p5_riskq60 | True | True | 0.094033 | 0.175003 | 0.571291 | 0.998077 | 0.982051 | -0.030625 | 0.104517 | 0.235912 | 0.739622 |
| min1_wmin8b_seg_spread_band_min20_cap0p005_s0p5 | True | True | 0.095261 | 0.175004 | 0.572077 | 0.998077 | 0.981410 | -0.030625 | 0.105229 | 0.236216 | 0.746974 |
| min1_wmin8b_seg_spread_band_min35_cap0p005_s0p5 | True | True | 0.095261 | 0.175004 | 0.572077 | 0.998077 | 0.981410 | -0.030625 | 0.105229 | 0.236216 | 0.746974 |
| min1_wmin8b_seg_spread_band_min50_cap0p005_s0p5 | True | True | 0.095261 | 0.175004 | 0.572077 | 0.998077 | 0.981410 | -0.030625 | 0.105229 | 0.236216 | 0.746974 |
| min1_wmin8b_seg_route_flag_min20_cap0p01_s0p5_riskq60 | True | True | 0.094407 | 0.175011 | 0.573670 | 0.998077 | 0.981410 | -0.030618 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min20_cap0p02_s0p5_riskq60 | True | True | 0.094407 | 0.175011 | 0.573670 | 0.998077 | 0.981410 | -0.030618 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p01_s0p5_riskq60 | True | True | 0.094407 | 0.175011 | 0.573670 | 0.998077 | 0.981410 | -0.030618 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p02_s0p5_riskq60 | True | True | 0.094407 | 0.175011 | 0.573670 | 0.998077 | 0.981410 | -0.030618 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p01_s0p5_riskq60 | True | True | 0.094407 | 0.175011 | 0.573670 | 0.998077 | 0.981410 | -0.030618 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p02_s0p5_riskq60 | True | True | 0.094407 | 0.175011 | 0.573670 | 0.998077 | 0.981410 | -0.030618 | 0.106547 | 0.235915 | 0.740586 |
| min1_wmin8b_seg_spread_band_min20_cap0p005_s0p5_riskq50 | True | True | 0.094033 | 0.175013 | 0.571291 | 0.998077 | 0.982051 | -0.030616 | 0.105229 | 0.236096 | 0.740849 |
| min1_wmin8b_seg_spread_band_min35_cap0p005_s0p5_riskq50 | True | True | 0.094033 | 0.175013 | 0.571291 | 0.998077 | 0.982051 | -0.030616 | 0.105229 | 0.236096 | 0.740849 |
| min1_wmin8b_seg_spread_band_min50_cap0p005_s0p5_riskq50 | True | True | 0.094033 | 0.175013 | 0.571291 | 0.998077 | 0.982051 | -0.030616 | 0.105229 | 0.236096 | 0.740849 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p35_riskq70 | True | True | 0.094033 | 0.175015 | 0.571291 | 0.998077 | 0.982692 | -0.030614 | 0.104951 | 0.235871 | 0.739622 |
| min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p5_riskq70 | True | True | 0.094033 | 0.175015 | 0.571291 | 0.998077 | 0.982692 | -0.030614 | 0.104951 | 0.235871 | 0.739622 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p35_riskq70 | True | True | 0.094033 | 0.175015 | 0.571291 | 0.998077 | 0.982692 | -0.030614 | 0.104951 | 0.235871 | 0.739622 |
| min1_wmin8b_seg_spread_band_min35_cap0p0025_s0p5_riskq70 | True | True | 0.094033 | 0.175015 | 0.571291 | 0.998077 | 0.982692 | -0.030614 | 0.104951 | 0.235871 | 0.739622 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p35_riskq70 | True | True | 0.094033 | 0.175015 | 0.571291 | 0.998077 | 0.982692 | -0.030614 | 0.104951 | 0.235871 | 0.739622 |
| min1_wmin8b_seg_spread_band_min50_cap0p0025_s0p5_riskq70 | True | True | 0.094033 | 0.175015 | 0.571291 | 0.998077 | 0.982692 | -0.030614 | 0.104951 | 0.235871 | 0.739622 |
| min1_wmin8b_seg_route_flag_min20_cap0p005_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min20_cap0p01_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min20_cap0p02_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min35_cap0p005_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min35_cap0p01_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min35_cap0p02_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min50_cap0p005_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min50_cap0p01_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min50_cap0p02_s0p35_riskq70 | True | True | 0.094033 | 0.175021 | 0.571666 | 0.998077 | 0.982051 | -0.030608 | 0.105666 | 0.235792 | 0.739888 |
| min1_wmin8b_seg_route_flag_min20_cap0p005_s0p5_riskq50 | True | True | 0.094407 | 0.175021 | 0.573670 | 0.998077 | 0.981410 | -0.030607 | 0.106547 | 0.235846 | 0.740586 |
| min1_wmin8b_seg_route_flag_min35_cap0p005_s0p5_riskq50 | True | True | 0.094407 | 0.175021 | 0.573670 | 0.998077 | 0.981410 | -0.030607 | 0.106547 | 0.235846 | 0.740586 |
| min1_wmin8b_seg_route_flag_min50_cap0p005_s0p5_riskq50 | True | True | 0.094407 | 0.175021 | 0.573670 | 0.998077 | 0.981410 | -0.030607 | 0.106547 | 0.235846 | 0.740586 |
| min1_wmin8b_seg_route_flag_min20_cap0p005_s0p35_riskq60 | True | True | 0.094327 | 0.175038 | 0.571666 | 0.998077 | 0.981410 | -0.030591 | 0.105666 | 0.235883 | 0.739888 |
| min1_wmin8b_seg_route_flag_min20_cap0p01_s0p35_riskq60 | True | True | 0.094327 | 0.175038 | 0.571666 | 0.998077 | 0.981410 | -0.030591 | 0.105666 | 0.235883 | 0.739888 |

_Only first 80 of 1300 rows shown._

## 2. WMIN8 선택 후보 대비 변화량
| candidate_label | eval_split | delta_MdAPE_vs_wmin8_selected | delta_MAPE_vs_wmin8_selected | delta_p95_APE_vs_wmin8_selected |
| --- | --- | --- | --- | --- |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p5_riskq70 | test | -0.000465 | -0.000207 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p5_riskq50 | test | -0.000656 | -0.000182 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p5_riskq60 | test | -0.000656 | -0.000171 | 0.000136 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p35_riskq70 | test | -0.000465 | -0.000145 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p35_riskq50 | test | -0.000465 | -0.000128 | 0.000095 |

_Only first 120 of 2600 rows shown._

## 3. fixed validation/test 지표
| candidate_label | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p5_riskq70 | test | 607 | 0.103861 | 0.235607 | 0.739552 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p5_riskq50 | test | 607 | 0.103670 | 0.235633 | 0.739552 | 0.377192 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p5_riskq60 | test | 607 | 0.103670 | 0.235643 | 0.739552 | 0.377212 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p0025_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p005_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p01_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min35_cap0p02_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p0025_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p005_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p01_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min50_cap0p02_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p0025_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p005_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p01_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min20_cap0p02_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p0025_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p005_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p01_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min35_cap0p02_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p0025_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p005_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p01_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_svc_conf_min50_cap0p02_s0p35_riskq70 | test | 607 | 0.103861 | 0.235669 | 0.739511 | 0.377190 |
| min1_wmin8b_seg_confidence_min20_cap0p0025_s0p35_riskq50 | test | 607 | 0.103861 | 0.235686 | 0.739511 | 0.377191 |
| min1_wmin8b_seg_confidence_min20_cap0p005_s0p35_riskq50 | test | 607 | 0.103861 | 0.235686 | 0.739511 | 0.377191 |
| min1_wmin8b_seg_confidence_min20_cap0p01_s0p35_riskq50 | test | 607 | 0.103861 | 0.235686 | 0.739511 | 0.377191 |
| min1_wmin8b_seg_confidence_min20_cap0p02_s0p35_riskq50 | test | 607 | 0.103861 | 0.235686 | 0.739511 | 0.377191 |

_Only first 100 of 2600 rows shown._

## 4. 잔차 위험 구간
| eval_split | segment_name | segment_value | n | MAPE | p95_APE | delta_MAPE_vs_overall | delta_p95_vs_overall | median_residual_log | over_50pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | price_qwidth | very_high_price|qwidth_q3 | 27 | 0.858643 | 6.149036 | 0.622829 | 5.409619 | 0.000636 | 0.222222 |
| test | price_band | very_high_price | 133 | 0.350749 | 1.340877 | 0.114935 | 0.601461 | 0.000636 | 0.112782 |
| test | confidence | low_confidence | 221 | 0.320799 | 1.173259 | 0.084985 | 0.433843 | -0.007628 | 0.135747 |
| test | svc_conf | missing|low_confidence | 221 | 0.320799 | 1.173259 | 0.084985 | 0.433843 | -0.007628 | 0.135747 |
| test | price_qwidth | very_high_price|qwidth_q4 | 78 | 0.264281 | 1.236116 | 0.028467 | 0.496700 | -0.019949 | 0.115385 |
| test | price_qwidth | high_price|qwidth_q4 | 64 | 0.313945 | 1.040428 | 0.078130 | 0.301012 | -0.032522 | 0.125000 |
| test | qwidth_band | qwidth_q4 | 176 | 0.282199 | 1.098220 | 0.046385 | 0.358803 | -0.026909 | 0.113636 |
| test | spread_band | spread_q4 | 165 | 0.258451 | 1.064738 | 0.022637 | 0.325321 | 0.016361 | 0.133333 |
| test | route_flag | routed_to_alt | 120 | 0.269290 | 0.931678 | 0.033476 | 0.192261 | -0.018605 | 0.158333 |
| test | price_qwidth | low_price|qwidth_q3 | 15 | 0.291387 | 0.879098 | 0.055573 | 0.139682 | 0.030448 | 0.200000 |
| test | qwidth_band | qwidth_q3 | 165 | 0.308812 | 0.798940 | 0.072998 | 0.059523 | 0.008229 | 0.151515 |
| test | spread_band | spread_q3 | 155 | 0.311192 | 0.790242 | 0.075378 | 0.050826 | -0.004156 | 0.103226 |
| test | price_qwidth | high_price|qwidth_q1 | 76 | 0.200868 | 0.879431 | -0.034946 | 0.140014 | -0.005451 | 0.092105 |
| test | price_band | high_price | 246 | 0.211056 | 0.839402 | -0.024759 | 0.099986 | -0.000653 | 0.093496 |
| test | price_qwidth | mid_price|qwidth_q3 | 69 | 0.221934 | 0.785632 | -0.013880 | 0.046216 | -0.016599 | 0.159420 |
| test | price_qwidth | mid_price|qwidth_q4 | 27 | 0.254942 | 0.459196 | 0.019128 | -0.280220 | -0.073618 | 0.037037 |
| test | price_band | low_price | 32 | 0.241279 | 0.631394 | 0.005465 | -0.108022 | 0.017422 | 0.156250 |
| test | confidence | high_confidence | 100 | 0.123087 | 0.372814 | -0.112727 | -0.366602 | -0.001065 | 0.040000 |
| test | confidence | medium_confidence | 286 | 0.209559 | 0.600933 | -0.026255 | -0.138483 | -0.001162 | 0.097902 |
| test | svc_level | missing | 607 | 0.235814 | 0.739416 | 0.000000 | 0.000000 | -0.002920 | 0.102142 |
| test | svc_n_band | n0_1 | 607 | 0.235814 | 0.739416 | 0.000000 | 0.000000 | -0.002920 | 0.102142 |
| test | qwidth_band | qwidth_q1 | 122 | 0.173715 | 0.535748 | -0.062099 | -0.203668 | -0.001995 | 0.081967 |
| test | qwidth_band | qwidth_q2 | 135 | 0.152671 | 0.469436 | -0.083144 | -0.269980 | 0.003759 | 0.051852 |
| test | spread_band | spread_q1 | 146 | 0.179142 | 0.579198 | -0.056672 | -0.160218 | -0.002087 | 0.082192 |
| test | spread_band | spread_q2 | 141 | 0.185144 | 0.585269 | -0.050670 | -0.154147 | -0.012301 | 0.085106 |
| test | price_band | mid_price | 196 | 0.188005 | 0.583846 | -0.047810 | -0.155570 | -0.011333 | 0.096939 |
| test | route_flag | kept_base | 487 | 0.227565 | 0.656612 | -0.008249 | -0.082804 | -0.000163 | 0.088296 |
| test | price_qwidth | high_price|qwidth_q2 | 48 | 0.168936 | 0.521717 | -0.066878 | -0.217699 | -0.001020 | 0.062500 |
| test | price_qwidth | high_price|qwidth_q3 | 54 | 0.149748 | 0.540412 | -0.086066 | -0.199005 | 0.020753 | 0.092593 |
| test | price_qwidth | mid_price|qwidth_q1 | 39 | 0.140101 | 0.526507 | -0.095713 | -0.212910 | -0.006841 | 0.076923 |
| test | price_qwidth | mid_price|qwidth_q2 | 58 | 0.154971 | 0.532211 | -0.080843 | -0.207205 | -0.004060 | 0.068966 |
| test | price_qwidth | very_high_price|qwidth_q2 | 20 | 0.112542 | 0.339895 | -0.123272 | -0.399522 | 0.045804 | 0.000000 |
| test | svc_conf | missing|high_confidence | 100 | 0.123087 | 0.372814 | -0.112727 | -0.366602 | -0.001065 | 0.040000 |
| test | svc_conf | missing|medium_confidence | 286 | 0.209559 | 0.600933 | -0.026255 | -0.138483 | -0.001162 | 0.097902 |
| validation_oof | price_qwidth | mid_price|qwidth_q4 | 15 | 0.282713 | 1.249597 | 0.107599 | 0.678305 | -0.110069 | 0.133333 |
| validation_oof | price_qwidth | high_price|qwidth_q4 | 43 | 0.298733 | 0.896696 | 0.123619 | 0.325405 | 0.032050 | 0.186047 |
| validation_oof | price_qwidth | high_price|qwidth_q3 | 33 | 0.248445 | 0.947997 | 0.073331 | 0.376706 | -0.061928 | 0.121212 |
| validation_oof | qwidth_band | qwidth_q4 | 129 | 0.227431 | 0.873854 | 0.052317 | 0.302563 | 0.010792 | 0.093023 |
| validation_oof | confidence | low_confidence | 172 | 0.213211 | 0.698434 | 0.038097 | 0.127143 | -0.003289 | 0.093023 |
| validation_oof | svc_conf | missing|low_confidence | 172 | 0.213211 | 0.698434 | 0.038097 | 0.127143 | -0.003289 | 0.093023 |
| validation_oof | spread_band | spread_q4 | 130 | 0.214390 | 0.653072 | 0.039276 | 0.081781 | -0.008513 | 0.076923 |
| validation_oof | price_band | high_price | 217 | 0.194550 | 0.632001 | 0.019436 | 0.060709 | 0.013361 | 0.096774 |
| validation_oof | qwidth_band | qwidth_q3 | 130 | 0.183029 | 0.611181 | 0.007915 | 0.039890 | 0.004366 | 0.076923 |
| validation_oof | route_flag | routed_to_alt | 109 | 0.182208 | 0.449187 | 0.007094 | -0.122105 | -0.007743 | 0.045872 |
| validation_oof | route_flag | kept_base | 410 | 0.173228 | 0.577726 | -0.001886 | 0.006435 | 0.008989 | 0.075610 |
| validation_oof | price_qwidth | very_high_price|qwidth_q4 | 66 | 0.176526 | 0.428435 | 0.001412 | -0.142856 | 0.028373 | 0.030303 |
| validation_oof | confidence | high_confidence | 91 | 0.137238 | 0.471298 | -0.037876 | -0.099993 | 0.009819 | 0.054945 |
| validation_oof | confidence | medium_confidence | 256 | 0.162982 | 0.556198 | -0.012132 | -0.015093 | 0.004366 | 0.058594 |
| validation_oof | svc_level | missing | 519 | 0.175114 | 0.571291 | 0.000000 | 0.000000 | 0.001711 | 0.069364 |
| validation_oof | svc_n_band | n0_1 | 519 | 0.175114 | 0.571291 | 0.000000 | 0.000000 | 0.001711 | 0.069364 |
| validation_oof | qwidth_band | qwidth_q1 | 131 | 0.147999 | 0.533841 | -0.027115 | -0.037450 | -0.011333 | 0.068702 |
| validation_oof | qwidth_band | qwidth_q2 | 129 | 0.142356 | 0.437016 | -0.032758 | -0.134275 | -0.008667 | 0.038760 |
| validation_oof | spread_band | spread_q1 | 130 | 0.173601 | 0.570476 | -0.001513 | -0.000816 | -0.009615 | 0.069231 |
| validation_oof | spread_band | spread_q2 | 130 | 0.161034 | 0.563225 | -0.014080 | -0.008066 | 0.010045 | 0.076923 |
| validation_oof | spread_band | spread_q3 | 129 | 0.151248 | 0.512167 | -0.023866 | -0.059125 | 0.012588 | 0.054264 |
| validation_oof | price_band | low_price | 22 | 0.152887 | 0.401285 | -0.022227 | -0.170006 | 0.000808 | 0.045455 |
| validation_oof | price_band | mid_price | 167 | 0.155204 | 0.506396 | -0.019910 | -0.064896 | -0.011158 | 0.053892 |
| validation_oof | price_band | very_high_price | 113 | 0.171542 | 0.486827 | -0.003572 | -0.084464 | 0.010650 | 0.044248 |
| validation_oof | price_qwidth | high_price|qwidth_q1 | 92 | 0.158118 | 0.550398 | -0.016996 | -0.020894 | 0.019323 | 0.086957 |
| validation_oof | price_qwidth | high_price|qwidth_q2 | 49 | 0.135231 | 0.437016 | -0.039883 | -0.134275 | 0.016131 | 0.020408 |
| validation_oof | price_qwidth | mid_price|qwidth_q1 | 35 | 0.101150 | 0.381299 | -0.073964 | -0.189992 | -0.047614 | 0.000000 |
| validation_oof | price_qwidth | mid_price|qwidth_q2 | 63 | 0.147014 | 0.399588 | -0.028100 | -0.171704 | 0.009441 | 0.047619 |
| validation_oof | price_qwidth | mid_price|qwidth_q3 | 54 | 0.164375 | 0.569825 | -0.010739 | -0.001467 | 0.023952 | 0.074074 |
| validation_oof | price_qwidth | very_high_price|qwidth_q3 | 33 | 0.153638 | 0.486827 | -0.021476 | -0.084464 | 0.010650 | 0.030303 |
| validation_oof | svc_conf | missing|high_confidence | 91 | 0.137238 | 0.471298 | -0.037876 | -0.099993 | 0.009819 | 0.054945 |
| validation_oof | svc_conf | missing|medium_confidence | 256 | 0.162982 | 0.556198 | -0.012132 | -0.015093 | 0.004366 | 0.058594 |

## 5. Huber 계수 감사
| target | feature | standardized_coefficient | direction |
| --- | --- | --- | --- |
| abs_residual_log | wmin8_alt_gap_abs | 0.064776 | 오차위험 증가 |
| abs_residual_log | risk_score | 0.062890 | 오차위험 증가 |
| abs_residual_log | quantile_width | -0.040137 | 오차위험 감소 |
| abs_residual_log | confidence_tier_low_confidence | -0.030758 | 오차위험 감소 |
| abs_residual_log | gap_band_gap_q3 | 0.030466 | 오차위험 증가 |
| abs_residual_log | current_vs_stable_gap_abs | -0.028965 | 오차위험 감소 |
| abs_residual_log | component_prediction_spread | -0.024937 | 오차위험 감소 |
| abs_residual_log | qwidth_band_qwidth_q4 | 0.023202 | 오차위험 증가 |
| abs_residual_log | gap_band_gap_q2 | 0.019462 | 오차위험 증가 |
| abs_residual_log | stable_price_band_very_high_price | -0.011150 | 오차위험 감소 |
| abs_residual_log | qwidth_band_qwidth_q3 | 0.010174 | 오차위험 증가 |
| abs_residual_log | qwidth_band_qwidth_q2 | 0.009628 | 오차위험 증가 |
| abs_residual_log | spread_band_spread_q4 | 0.007186 | 오차위험 증가 |
| abs_residual_log | stable_price_band_low_price | -0.006756 | 오차위험 감소 |
| abs_residual_log | stable_price_band_mid_price | -0.006702 | 오차위험 감소 |
| abs_residual_log | gap_band_gap_q4 | 0.006422 | 오차위험 증가 |
| abs_residual_log | wmin8_route_flag_routed_to_alt | -0.004609 | 오차위험 감소 |
| abs_residual_log | spread_band_spread_q3 | -0.003031 | 오차위험 감소 |
| abs_residual_log | confidence_tier_medium_confidence | 0.000281 | 오차위험 증가 |
| abs_residual_log | spread_band_spread_q2 | -0.000152 | 오차위험 감소 |
| signed_residual_log | risk_score | -0.102898 | 예측>실제 방향 |
| signed_residual_log | quantile_width | 0.071416 | 실제>예측 방향 |
| signed_residual_log | spread_band_spread_q4 | 0.051266 | 실제>예측 방향 |
| signed_residual_log | confidence_tier_low_confidence | -0.030946 | 예측>실제 방향 |
| signed_residual_log | confidence_tier_medium_confidence | -0.029584 | 예측>실제 방향 |
| signed_residual_log | gap_band_gap_q3 | 0.027905 | 실제>예측 방향 |
| signed_residual_log | spread_band_spread_q3 | 0.027749 | 실제>예측 방향 |
| signed_residual_log | qwidth_band_qwidth_q4 | 0.025994 | 실제>예측 방향 |
| signed_residual_log | current_vs_stable_gap_abs | -0.021270 | 예측>실제 방향 |
| signed_residual_log | stable_price_band_very_high_price | 0.018495 | 실제>예측 방향 |
| signed_residual_log | wmin8_alt_gap_abs | 0.014860 | 실제>예측 방향 |
| signed_residual_log | spread_band_spread_q2 | 0.011996 | 실제>예측 방향 |
| signed_residual_log | wmin8_route_flag_routed_to_alt | -0.010807 | 예측>실제 방향 |
| signed_residual_log | qwidth_band_qwidth_q3 | 0.008882 | 실제>예측 방향 |
| signed_residual_log | gap_band_gap_q4 | 0.008812 | 실제>예측 방향 |
| signed_residual_log | stable_price_band_mid_price | -0.008482 | 예측>실제 방향 |
| signed_residual_log | gap_band_gap_q2 | -0.008186 | 예측>실제 방향 |
| signed_residual_log | component_prediction_spread | -0.005534 | 예측>실제 방향 |
| signed_residual_log | stable_price_band_low_price | -0.001649 | 예측>실제 방향 |
| signed_residual_log | qwidth_band_qwidth_q2 | 0.000285 | 실제>예측 방향 |

## 6. 보정 후보 설정
| candidate_label | segment_name | min_rows | cap | strength | risk_q | usable_segment_count | validation_mean_abs_applied | test_mean_abs_applied |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p5 | price_qwidth | 20 | 0.020000 | 0.500000 |  | 9 | 0.010530 | 0.010606 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p35 | price_qwidth | 20 | 0.020000 | 0.350000 |  | 9 | 0.008080 | 0.008129 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p02_s0p5 | price_qwidth | 35 | 0.020000 | 0.500000 |  | 7 | 0.007798 | 0.008704 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p01_s0p5 | price_qwidth | 20 | 0.010000 | 0.500000 |  | 9 | 0.007596 | 0.007676 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p01_s0p35 | price_qwidth | 20 | 0.010000 | 0.350000 |  | 9 | 0.006390 | 0.006683 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p01_s0p5 | price_qwidth | 35 | 0.010000 | 0.500000 |  | 7 | 0.006174 | 0.006664 |
| min1_wmin8b_seg_price_band_min20_cap0p01_s0p5 | price_band | 20 | 0.010000 | 0.500000 |  | 4 | 0.005775 | 0.005697 |
| min1_wmin8b_seg_price_band_min20_cap0p02_s0p5 | price_band | 20 | 0.020000 | 0.500000 |  | 4 | 0.005775 | 0.005697 |
| min1_wmin8b_seg_price_qwidth_min50_cap0p02_s0p5 | price_qwidth | 50 | 0.020000 | 0.500000 |  | 4 | 0.005722 | 0.005304 |
| min1_wmin8b_seg_price_band_min35_cap0p01_s0p5 | price_band | 35 | 0.010000 | 0.500000 |  | 3 | 0.005710 | 0.005721 |
| min1_wmin8b_seg_price_band_min35_cap0p02_s0p5 | price_band | 35 | 0.020000 | 0.500000 |  | 3 | 0.005710 | 0.005721 |
| min1_wmin8b_seg_price_band_min50_cap0p01_s0p5 | price_band | 50 | 0.010000 | 0.500000 |  | 3 | 0.005710 | 0.005721 |
| min1_wmin8b_seg_price_band_min50_cap0p02_s0p5 | price_band | 50 | 0.020000 | 0.500000 |  | 3 | 0.005710 | 0.005721 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p02_s0p35 | price_qwidth | 35 | 0.020000 | 0.350000 |  | 7 | 0.005606 | 0.006264 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p5_riskq50 | price_qwidth | 20 | 0.020000 | 0.500000 | 0.500000 | 9 | 0.005437 | 0.005839 |
| min1_wmin8b_seg_spread_band_min20_cap0p01_s0p5 | spread_band | 20 | 0.010000 | 0.500000 |  | 4 | 0.005149 | 0.005087 |
| min1_wmin8b_seg_spread_band_min20_cap0p02_s0p5 | spread_band | 20 | 0.020000 | 0.500000 |  | 4 | 0.005149 | 0.005087 |
| min1_wmin8b_seg_spread_band_min35_cap0p01_s0p5 | spread_band | 35 | 0.010000 | 0.500000 |  | 4 | 0.005149 | 0.005087 |
| min1_wmin8b_seg_spread_band_min35_cap0p02_s0p5 | spread_band | 35 | 0.020000 | 0.500000 |  | 4 | 0.005149 | 0.005087 |
| min1_wmin8b_seg_spread_band_min50_cap0p01_s0p5 | spread_band | 50 | 0.010000 | 0.500000 |  | 4 | 0.005149 | 0.005087 |
| min1_wmin8b_seg_spread_band_min50_cap0p02_s0p5 | spread_band | 50 | 0.020000 | 0.500000 |  | 4 | 0.005149 | 0.005087 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p01_s0p35 | price_qwidth | 35 | 0.010000 | 0.350000 |  | 7 | 0.005002 | 0.005707 |
| min1_wmin8b_seg_price_qwidth_min50_cap0p01_s0p5 | price_qwidth | 50 | 0.010000 | 0.500000 |  | 4 | 0.004850 | 0.004542 |
| min1_wmin8b_seg_price_band_min20_cap0p005_s0p5 | price_band | 20 | 0.005000 | 0.500000 |  | 4 | 0.004837 | 0.004758 |
| min1_wmin8b_seg_price_band_min35_cap0p005_s0p5 | price_band | 35 | 0.005000 | 0.500000 |  | 3 | 0.004797 | 0.004781 |
| min1_wmin8b_seg_price_band_min50_cap0p005_s0p5 | price_band | 50 | 0.005000 | 0.500000 |  | 3 | 0.004797 | 0.004781 |
| min1_wmin8b_seg_spread_band_min20_cap0p005_s0p5 | spread_band | 20 | 0.005000 | 0.500000 |  | 4 | 0.004686 | 0.004752 |
| min1_wmin8b_seg_spread_band_min35_cap0p005_s0p5 | spread_band | 35 | 0.005000 | 0.500000 |  | 4 | 0.004686 | 0.004752 |
| min1_wmin8b_seg_spread_band_min50_cap0p005_s0p5 | spread_band | 50 | 0.005000 | 0.500000 |  | 4 | 0.004686 | 0.004752 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p5_riskq60 | price_qwidth | 20 | 0.020000 | 0.500000 | 0.600000 | 9 | 0.004684 | 0.005086 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p2 | price_qwidth | 20 | 0.020000 | 0.200000 |  | 9 | 0.004679 | 0.004730 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p02_s0p5_riskq50 | price_qwidth | 35 | 0.020000 | 0.500000 | 0.500000 | 7 | 0.004659 | 0.004645 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p01_s0p2 | price_qwidth | 20 | 0.010000 | 0.200000 |  | 9 | 0.004520 | 0.004518 |
| min1_wmin8b_seg_route_flag_min20_cap0p01_s0p5 | route_flag | 20 | 0.010000 | 0.500000 |  | 2 | 0.004448 | 0.004371 |
| min1_wmin8b_seg_route_flag_min20_cap0p02_s0p5 | route_flag | 20 | 0.020000 | 0.500000 |  | 2 | 0.004448 | 0.004371 |
| min1_wmin8b_seg_route_flag_min35_cap0p01_s0p5 | route_flag | 35 | 0.010000 | 0.500000 |  | 2 | 0.004448 | 0.004371 |
| min1_wmin8b_seg_route_flag_min35_cap0p02_s0p5 | route_flag | 35 | 0.020000 | 0.500000 |  | 2 | 0.004448 | 0.004371 |
| min1_wmin8b_seg_route_flag_min50_cap0p01_s0p5 | route_flag | 50 | 0.010000 | 0.500000 |  | 2 | 0.004448 | 0.004371 |
| min1_wmin8b_seg_route_flag_min50_cap0p02_s0p5 | route_flag | 50 | 0.020000 | 0.500000 |  | 2 | 0.004448 | 0.004371 |
| min1_wmin8b_seg_route_flag_min20_cap0p005_s0p5 | route_flag | 20 | 0.005000 | 0.500000 |  | 2 | 0.004418 | 0.004371 |
| min1_wmin8b_seg_route_flag_min35_cap0p005_s0p5 | route_flag | 35 | 0.005000 | 0.500000 |  | 2 | 0.004418 | 0.004371 |
| min1_wmin8b_seg_route_flag_min50_cap0p005_s0p5 | route_flag | 50 | 0.005000 | 0.500000 |  | 2 | 0.004418 | 0.004371 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p005_s0p5 | price_qwidth | 20 | 0.005000 | 0.500000 |  | 9 | 0.004382 | 0.004331 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p02_s0p5_riskq60 | price_qwidth | 35 | 0.020000 | 0.500000 | 0.600000 | 7 | 0.004171 | 0.004244 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p005_s0p35 | price_qwidth | 20 | 0.005000 | 0.350000 |  | 9 | 0.004153 | 0.004100 |
| min1_wmin8b_seg_price_qwidth_min50_cap0p02_s0p35 | price_qwidth | 50 | 0.020000 | 0.350000 |  | 4 | 0.004132 | 0.003713 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p35_riskq50 | price_qwidth | 20 | 0.020000 | 0.350000 | 0.500000 | 9 | 0.004099 | 0.004403 |
| min1_wmin8b_seg_price_band_min20_cap0p01_s0p35 | price_band | 20 | 0.010000 | 0.350000 |  | 4 | 0.004042 | 0.003988 |
| min1_wmin8b_seg_price_band_min20_cap0p02_s0p35 | price_band | 20 | 0.020000 | 0.350000 |  | 4 | 0.004042 | 0.003988 |
| min1_wmin8b_seg_price_band_min20_cap0p005_s0p35 | price_band | 20 | 0.005000 | 0.350000 |  | 4 | 0.004037 | 0.003988 |
| min1_wmin8b_seg_price_band_min35_cap0p005_s0p35 | price_band | 35 | 0.005000 | 0.350000 |  | 3 | 0.003997 | 0.004004 |
| min1_wmin8b_seg_price_band_min35_cap0p01_s0p35 | price_band | 35 | 0.010000 | 0.350000 |  | 3 | 0.003997 | 0.004004 |
| min1_wmin8b_seg_price_band_min35_cap0p02_s0p35 | price_band | 35 | 0.020000 | 0.350000 |  | 3 | 0.003997 | 0.004004 |
| min1_wmin8b_seg_price_band_min50_cap0p005_s0p35 | price_band | 50 | 0.005000 | 0.350000 |  | 3 | 0.003997 | 0.004004 |
| min1_wmin8b_seg_price_band_min50_cap0p01_s0p35 | price_band | 50 | 0.010000 | 0.350000 |  | 3 | 0.003997 | 0.004004 |
| min1_wmin8b_seg_price_band_min50_cap0p02_s0p35 | price_band | 50 | 0.020000 | 0.350000 |  | 3 | 0.003997 | 0.004004 |
| min1_wmin8b_seg_qwidth_band_min20_cap0p01_s0p5 | qwidth_band | 20 | 0.010000 | 0.500000 |  | 4 | 0.003867 | 0.004273 |
| min1_wmin8b_seg_qwidth_band_min20_cap0p02_s0p5 | qwidth_band | 20 | 0.020000 | 0.500000 |  | 4 | 0.003867 | 0.004273 |
| min1_wmin8b_seg_qwidth_band_min35_cap0p01_s0p5 | qwidth_band | 35 | 0.010000 | 0.500000 |  | 4 | 0.003867 | 0.004273 |
| min1_wmin8b_seg_qwidth_band_min35_cap0p02_s0p5 | qwidth_band | 35 | 0.020000 | 0.500000 |  | 4 | 0.003867 | 0.004273 |
| min1_wmin8b_seg_qwidth_band_min50_cap0p01_s0p5 | qwidth_band | 50 | 0.010000 | 0.500000 |  | 4 | 0.003867 | 0.004273 |
| min1_wmin8b_seg_qwidth_band_min50_cap0p02_s0p5 | qwidth_band | 50 | 0.020000 | 0.500000 |  | 4 | 0.003867 | 0.004273 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p5_riskq70 | price_qwidth | 20 | 0.020000 | 0.500000 | 0.700000 | 9 | 0.003826 | 0.004065 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p01_s0p5_riskq50 | price_qwidth | 20 | 0.010000 | 0.500000 | 0.500000 | 9 | 0.003775 | 0.004005 |
| min1_wmin8b_seg_price_qwidth_min50_cap0p01_s0p35 | price_qwidth | 50 | 0.010000 | 0.350000 |  | 4 | 0.003753 | 0.003713 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p005_s0p5 | price_qwidth | 35 | 0.005000 | 0.500000 |  | 7 | 0.003714 | 0.003778 |
| min1_wmin8b_seg_price_qwidth_min35_cap0p02_s0p5_riskq70 | price_qwidth | 35 | 0.020000 | 0.500000 | 0.700000 | 7 | 0.003652 | 0.003745 |
| min1_wmin8b_seg_spread_band_min20_cap0p01_s0p35 | spread_band | 20 | 0.010000 | 0.350000 |  | 4 | 0.003605 | 0.003561 |
| min1_wmin8b_seg_spread_band_min20_cap0p02_s0p35 | spread_band | 20 | 0.020000 | 0.350000 |  | 4 | 0.003605 | 0.003561 |
| min1_wmin8b_seg_spread_band_min35_cap0p01_s0p35 | spread_band | 35 | 0.010000 | 0.350000 |  | 4 | 0.003605 | 0.003561 |
| min1_wmin8b_seg_spread_band_min35_cap0p02_s0p35 | spread_band | 35 | 0.020000 | 0.350000 |  | 4 | 0.003605 | 0.003561 |
| min1_wmin8b_seg_spread_band_min50_cap0p01_s0p35 | spread_band | 50 | 0.010000 | 0.350000 |  | 4 | 0.003605 | 0.003561 |
| min1_wmin8b_seg_spread_band_min50_cap0p02_s0p35 | spread_band | 50 | 0.020000 | 0.350000 |  | 4 | 0.003605 | 0.003561 |
| min1_wmin8b_seg_spread_band_min20_cap0p005_s0p35 | spread_band | 20 | 0.005000 | 0.350000 |  | 4 | 0.003600 | 0.003561 |
| min1_wmin8b_seg_spread_band_min35_cap0p005_s0p35 | spread_band | 35 | 0.005000 | 0.350000 |  | 4 | 0.003600 | 0.003561 |
| min1_wmin8b_seg_spread_band_min50_cap0p005_s0p35 | spread_band | 50 | 0.005000 | 0.350000 |  | 4 | 0.003600 | 0.003561 |
| min1_wmin8b_seg_qwidth_band_min20_cap0p005_s0p5 | qwidth_band | 20 | 0.005000 | 0.500000 |  | 4 | 0.003597 | 0.004025 |
| min1_wmin8b_seg_qwidth_band_min35_cap0p005_s0p5 | qwidth_band | 35 | 0.005000 | 0.500000 |  | 4 | 0.003597 | 0.004025 |
| min1_wmin8b_seg_qwidth_band_min50_cap0p005_s0p5 | qwidth_band | 50 | 0.005000 | 0.500000 |  | 4 | 0.003597 | 0.004025 |
| min1_wmin8b_seg_price_qwidth_min20_cap0p02_s0p35_riskq60 | price_qwidth | 20 | 0.020000 | 0.350000 | 0.600000 | 9 | 0.003523 | 0.003777 |

_Only first 80 of 1296 rows shown._

## 7. 실행 설정
```json
{
  "experiment_id": "PP-WMIN8B",
  "experiment_slug": "PP-WMIN8B_warm_min1_residual_rediagnosis",
  "created_at": "2026-06-12T23:36:52",
  "source_predictions": "experiments/track6/PP-WMIN8_warm_min1_weight_router/outputs/candidate_predictions.csv",
  "source_gate_audit": "experiments/track6/PP-WMIN8_warm_min1_weight_router/outputs/gate_audit.csv",
  "reference_candidate_label": "current_pp258_operational_reference",
  "wmin4_selected_candidate_label": "min1_huber_refit_partial",
  "wmin8_selected_candidate_label": "min1_route_w850_risk_q50_altlower_gap005",
  "candidate_count": 1300,
  "segment_sets": {
    "confidence": [
      "confidence_tier"
    ],
    "svc_level": [
      "svc_group_level"
    ],
    "svc_n_band": [
      "svc_group_n_band"
    ],
    "qwidth_band": [
      "qwidth_band"
    ],
    "spread_band": [
      "spread_band"
    ],
    "price_band": [
      "stable_price_band"
    ],
    "route_flag": [
      "wmin8_route_flag"
    ],
    "price_qwidth": [
      "stable_price_band",
      "qwidth_band"
    ],
    "svc_conf": [
      "svc_group_level",
      "confidence_tier"
    ]
  },
  "min_segment_rows": [
    20,
    35,
    50
  ],
  "caps": [
    0.0025,
    0.005,
    0.01,
    0.02
  ],
  "strengths": [
    0.2,
    0.35,
    0.5
  ],
  "risk_quantiles": [
    null,
    0.5,
    0.6,
    0.7
  ],
  "selection_policy": "validation OOF segment corrections only; fixed test confirmation; 0604 not used",
  "decision": {
    "decision_status": "validation_pass_fixed_hold",
    "selected_candidate_label": "min1_route_w850_risk_q50_altlower_gap005",
    "best_screened_candidate": "min1_wmin8b_seg_spread_band_min20_cap0p0025_s0p5",
    "reason": "validation gate는 통과했지만 fixed test에서 WMIN8 대비 일부 지표 trade-off가 있어 보류",
    "selected_fixed_validation_MdAPE": 0.09629526300553462,
    "selected_fixed_validation_MAPE": 0.17490130099891174,
    "selected_fixed_validation_p95_APE": 0.574277727142015,
    "selected_fixed_test_MdAPE": 0.10451713846921801,
    "selected_fixed_test_MAPE": 0.23597419886966486,
    "selected_fixed_test_p95_APE": 0.7426812124046098,
    "selected_validation_MAPE_win_rate": 0.9980769230769231,
    "selected_validation_p95_win_rate": 0.9814102564102565,
    "selected_validation_replacement_score": -0.03072725898072981
  }
}
```