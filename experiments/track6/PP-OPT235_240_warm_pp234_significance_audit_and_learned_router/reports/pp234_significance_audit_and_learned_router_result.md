# PP-OPT235~240 Warm PP234 significance audit and learned router 결과

- 작성일: 2026-06-10 12:41
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP234 미세 개선의 의미 검증과 learned router 기반 구조적 개선 탐색
- 결론: 운영 후보 MAPE 0.269889, p95 win rate 0.747115. PP234 대비 MAPE 변화 -0.000000390, p95 win rate 변화 -0.000641.

## Bootstrap Audit
| comparison | test_mean_delta_MAPE | bootstrap_ci05 | bootstrap_ci50 | bootstrap_ci95 | bootstrap_improvement_rate | rows_improved | rows_worsened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pp234_minus_pp228_balanced | -0.000000 | -0.000000 | -0.000000 | 0.000000 | 0.680000 | 6 | 3 |
| pp234_minus_pp228_operational | 0.000000 | -0.000001 | 0.000000 | 0.000002 | 0.330500 | 3 | 6 |
| pp234_minus_pp228_mape | 0.000001 | -0.000003 | 0.000001 | 0.000005 | 0.370500 | 3 | 6 |

## Leave-Group-Out Audit
| group | comparison | group_n | group_delta_MAPE | leave_group_out_delta_MAPE | group_improved_rows | group_worsened_rows |
| --- | --- | --- | --- | --- | --- | --- |
| high_price × high_confidence | pp234_minus_pp228_balanced | 60 | 0.000000 | -0.000000 | 0 | 0 |
| high_price × high_confidence | pp234_minus_pp228_operational | 60 | 0.000000 | 0.000000 | 0 | 0 |
| high_price × high_confidence | pp234_minus_pp228_mape | 60 | 0.000000 | 0.000001 | 0 | 0 |
| high_price × low_confidence | pp234_minus_pp228_balanced | 78 | 0.000000 | -0.000000 | 0 | 0 |
| high_price × low_confidence | pp234_minus_pp228_operational | 78 | 0.000000 | 0.000000 | 0 | 0 |
| high_price × low_confidence | pp234_minus_pp228_mape | 78 | 0.000000 | 0.000001 | 0 | 0 |
| high_price × medium_confidence | pp234_minus_pp228_balanced | 108 | 0.000000 | -0.000000 | 0 | 0 |
| high_price × medium_confidence | pp234_minus_pp228_operational | 108 | 0.000000 | 0.000000 | 0 | 0 |
| high_price × medium_confidence | pp234_minus_pp228_mape | 108 | 0.000000 | 0.000001 | 0 | 0 |
| low_price × high_confidence | pp234_minus_pp228_balanced | 1 | 0.000000 | -0.000000 | 0 | 0 |
| low_price × high_confidence | pp234_minus_pp228_operational | 1 | 0.000000 | 0.000000 | 0 | 0 |
| low_price × high_confidence | pp234_minus_pp228_mape | 1 | 0.000000 | 0.000001 | 0 | 0 |
| low_price × low_confidence | pp234_minus_pp228_balanced | 11 | 0.000000 | -0.000000 | 0 | 0 |
| low_price × low_confidence | pp234_minus_pp228_operational | 11 | 0.000000 | 0.000000 | 0 | 0 |
| low_price × low_confidence | pp234_minus_pp228_mape | 11 | 0.000000 | 0.000001 | 0 | 0 |
| low_price × medium_confidence | pp234_minus_pp228_balanced | 20 | -0.000000 | 0.000000 | 6 | 3 |
| low_price × medium_confidence | pp234_minus_pp228_operational | 20 | 0.000012 | 0.000000 | 3 | 6 |
| low_price × medium_confidence | pp234_minus_pp228_mape | 20 | 0.000020 | 0.000000 | 3 | 6 |
| mid_price × high_confidence | pp234_minus_pp228_balanced | 32 | 0.000000 | -0.000000 | 0 | 0 |
| mid_price × high_confidence | pp234_minus_pp228_operational | 32 | 0.000000 | 0.000000 | 0 | 0 |
| mid_price × high_confidence | pp234_minus_pp228_mape | 32 | 0.000000 | 0.000001 | 0 | 0 |
| mid_price × low_confidence | pp234_minus_pp228_balanced | 47 | 0.000000 | -0.000000 | 0 | 0 |
| mid_price × low_confidence | pp234_minus_pp228_operational | 47 | 0.000000 | 0.000000 | 0 | 0 |
| mid_price × low_confidence | pp234_minus_pp228_mape | 47 | 0.000000 | 0.000001 | 0 | 0 |
| mid_price × medium_confidence | pp234_minus_pp228_balanced | 117 | 0.000000 | -0.000000 | 0 | 0 |
| mid_price × medium_confidence | pp234_minus_pp228_operational | 117 | 0.000000 | 0.000000 | 0 | 0 |
| mid_price × medium_confidence | pp234_minus_pp228_mape | 117 | 0.000000 | 0.000001 | 0 | 0 |
| very_high_price × high_confidence | pp234_minus_pp228_balanced | 7 | 0.000000 | -0.000000 | 0 | 0 |
| very_high_price × high_confidence | pp234_minus_pp228_operational | 7 | 0.000000 | 0.000000 | 0 | 0 |
| very_high_price × high_confidence | pp234_minus_pp228_mape | 7 | 0.000000 | 0.000001 | 0 | 0 |
| very_high_price × low_confidence | pp234_minus_pp228_balanced | 85 | 0.000000 | -0.000000 | 0 | 0 |
| very_high_price × low_confidence | pp234_minus_pp228_operational | 85 | 0.000000 | 0.000000 | 0 | 0 |
| very_high_price × low_confidence | pp234_minus_pp228_mape | 85 | 0.000000 | 0.000001 | 0 | 0 |
| very_high_price × medium_confidence | pp234_minus_pp228_balanced | 41 | 0.000000 | -0.000000 | 0 | 0 |
| very_high_price × medium_confidence | pp234_minus_pp228_operational | 41 | 0.000000 | 0.000000 | 0 | 0 |
| very_high_price × medium_confidence | pp234_minus_pp228_mape | 41 | 0.000000 | 0.000001 | 0 | 0 |

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt228_mape_challenger_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt228_operational_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt240_operational_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5 | pp234_learned_router_operational_selection | PP-OPT240 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5 | pp234_learned_router_mape_selection | PP-OPT240 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt234_operational_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt240_balanced_pp234_learned_router__source=ppopt235_pp234_significance_audit_anchor | pp234_learned_router_balanced_selection | PP-OPT240 | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92 | reference_prior | REFERENCE | 0.140975 | 0.269890 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt240_p95_recovery_pp234_learned_router__source=ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001 | pp234_learned_router_p95_win_selection | PP-OPT240 | 0.140941 | 0.269890 | 0.807323 | 0.397456 | -0.001505 | -0.000807 |
| ppopt240_p95_guarded_pp234_learned_router__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p | pp234_learned_router_p95_guarded_selection | PP-OPT240 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | segment winner router | 144 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | pp234_segment_winner_router | ppopt236_segment_winner__seg=price_conf__minn=15__gain=0p0__cap=0p00045__shrink=0p5 |
| 6 | final PP234 learned-router decision | 6 | 0.269889 | 0.807326 | 0.270269 | 0.805949 | pp234_learned_router_mape_selection | ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5 |
| 4 | pairwise uplift router | 64 | 0.269889 | 0.807326 | 0.269891 | 0.807319 | pp234_pairwise_uplift_router | ppopt238_pairwise_uplift__target=pp228_mape__c=0p6__thr=0p55__s=0p7__cap=0p00028 |
| 1 | PP234 significance audit | 1 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | pp234_significance_audit_anchor | ppopt235_pp234_significance_audit_anchor |
| 3 | learned multiclass candidate router | 72 | 0.269890 | 0.807324 | 0.269891 | 0.807310 | pp234_learned_multiclass_router | ppopt237_multiclass_router__c=0p6__seed=29__thr=0p32__cap=0p0001__shrink=0p8 |
| 5 | probability blend router | 72 | 0.269890 | 0.807323 | 0.269893 | 0.807315 | pp234_probability_blend_router | ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p8__cap=0p0001 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt240_p95_guarded_pp234_learned_router__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p | PP-OPT240 | pp234_learned_router_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001427 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001427 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001427 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001427 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p58__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269892 | 0.807310 | -0.001503 | -0.000820 | -0.001421 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p45__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269892 | 0.807310 | -0.001503 | -0.000820 | -0.001421 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p32__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269892 | 0.807310 | -0.001503 | -0.000820 | -0.001420 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p58__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807310 | -0.001504 | -0.000820 | -0.001420 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p32__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807310 | -0.001504 | -0.000820 | -0.001420 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p45__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807310 | -0.001504 | -0.000820 | -0.001420 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p58__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269892 | 0.807310 | -0.001503 | -0.000820 | -0.001419 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p32__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807310 | -0.001504 | -0.000820 | -0.001419 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p45__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807310 | -0.001504 | -0.000820 | -0.001419 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p58__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807310 | -0.001504 | -0.000820 | -0.001419 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p32__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269892 | 0.807310 | -0.001503 | -0.000820 | -0.001418 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p45__cap=0p00045__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269892 | 0.807310 | -0.001503 | -0.000820 | -0.001418 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001413 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001413 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001413 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001413 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p65__s=0p35__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001408 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p65__s=0p7__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001408 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p55__s=0p35__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269891 | 0.807319 | -0.001503 | -0.000811 | -0.001408 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p55__s=0p7__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001408 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p65__s=0p35__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269891 | 0.807319 | -0.001503 | -0.000811 | -0.001407 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p65__s=0p7__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001407 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p55__s=0p35__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001407 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p55__s=0p7__cap=0p00028 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001407 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p5__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p35__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p35__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001405 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p5__s=0p2__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807315 | -0.001504 | -0.000815 | -0.001404 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p5__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807315 | -0.001503 | -0.000815 | -0.001403 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807315 | -0.001503 | -0.000815 | -0.001403 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001403 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p5__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001403 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001403 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p35__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001403 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807315 | -0.001502 | -0.000815 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p5__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p8__cap=0p0001 | PP-OPT239 | pp234_probability_blend_router | 0.269890 | 0.807323 | -0.001505 | -0.000807 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p8__cap=0p0001 | PP-OPT239 | pp234_probability_blend_router | 0.269890 | 0.807323 | -0.001505 | -0.000807 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p8__cap=0p0001 | PP-OPT239 | pp234_probability_blend_router | 0.269890 | 0.807323 | -0.001505 | -0.000807 | -0.001402 |
| ppopt240_p95_recovery_pp234_learned_router__source=ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001 | PP-OPT240 | pp234_learned_router_p95_win_selection | 0.269890 | 0.807323 | -0.001505 | -0.000807 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p8__cap=0p0001 | PP-OPT239 | pp234_probability_blend_router | 0.269890 | 0.807323 | -0.001505 | -0.000807 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p5__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p35__s=0p5__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807315 | -0.001502 | -0.000815 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p35__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001402 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p35__s=0p8__cap=0p00045 | PP-OPT239 | pp234_probability_blend_router | 0.269893 | 0.807315 | -0.001502 | -0.000815 | -0.001401 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p58__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001398 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p45__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001398 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p32__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001398 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p58__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001398 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p32__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p45__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p58__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p32__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p45__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p58__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p58__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p45__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p32__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p45__cap=0p00025__shrink=0p5 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001397 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p58__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001396 |
| ppopt237_multiclass_router__c=0p2__seed=29__thr=0p32__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001396 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p65__s=0p35__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269890 | 0.807323 | -0.001504 | -0.000807 | -0.001396 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p65__s=0p7__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269891 | 0.807323 | -0.001504 | -0.000807 | -0.001396 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p32__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001396 |
| ppopt237_multiclass_router__c=0p6__seed=29__thr=0p45__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001396 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p55__s=0p35__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269890 | 0.807323 | -0.001505 | -0.000807 | -0.001396 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p58__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001396 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p6__thr=0p55__s=0p7__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269890 | 0.807323 | -0.001504 | -0.000807 | -0.001396 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p65__s=0p35__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269891 | 0.807323 | -0.001504 | -0.000807 | -0.001396 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p65__s=0p7__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269891 | 0.807323 | -0.001504 | -0.000807 | -0.001396 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p32__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001396 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p45__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001396 |
| ppopt237_multiclass_router__c=0p6__seed=17__thr=0p58__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269890 | 0.807317 | -0.001505 | -0.000813 | -0.001395 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p55__s=0p35__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269890 | 0.807323 | -0.001504 | -0.000807 | -0.001395 |
| ppopt238_pairwise_uplift__target=pp228_p95_guarded__c=0p2__thr=0p55__s=0p7__cap=0p00012 | PP-OPT238 | pp234_pairwise_uplift_router | 0.269890 | 0.807323 | -0.001504 | -0.000807 | -0.001395 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p32__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001395 |
| ppopt237_multiclass_router__c=0p2__seed=17__thr=0p45__cap=0p00045__shrink=0p8 | PP-OPT237 | pp234_learned_multiclass_router | 0.269891 | 0.807317 | -0.001504 | -0.000813 | -0.001395 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p5__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p5__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p35__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001389 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p35__s=0p2__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p5__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p5__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p5__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p5__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed17__thr=0p35__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p5__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p35__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p5__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001388 |
| ppopt239_probability_blend__probs=multiclass_c0p2_seed29__thr=0p35__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269892 | 0.807319 | -0.001503 | -0.000811 | -0.001387 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p35__s=0p5__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001387 |
| ppopt239_probability_blend__probs=multiclass_c0p6_seed29__thr=0p35__s=0p8__cap=0p00025 | PP-OPT239 | pp234_probability_blend_router | 0.269891 | 0.807319 | -0.001504 | -0.000811 | -0.001387 |
| ppopt235_pp234_significance_audit_anchor | PP-OPT235 | pp234_significance_audit_anchor | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=2em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=2em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=2em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=2em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=2em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=2em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=5em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=5em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=5em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=5em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=5em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=15__gain=5em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=2em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=2em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=2em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=2em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=2em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=2em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=5em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=5em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=5em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=5em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=5em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf__minn=8__gain=5em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=0p0__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=0p0__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=0p0__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=0p0__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=0p0__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=0p0__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=2em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=2em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=2em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=2em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=2em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=2em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=5em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=5em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=5em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=5em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=5em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=15__gain=5em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=2em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=2em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=2em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=2em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=2em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=2em05__cap=0p00045__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=5em05__cap=0p00012__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=5em05__cap=0p00012__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=5em05__cap=0p00025__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=5em05__cap=0p00025__shrink=0p8 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |
| ppopt236_segment_winner__seg=price_conf_medium__minn=8__gain=5em05__cap=0p00045__shrink=0p5 | PP-OPT236 | pp234_segment_winner_router | 0.269889 | 0.807326 | -0.001505 | -0.000804 | -0.001387 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5__0e1d316316 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p8__6f80dc595d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_0p0__cap_0p00045__shrink_0p5__9cef56ec24 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_0p0__cap_0p00045__shrink_0p8__702978eff4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp228_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp240_mape_pp234_learned_router_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp240_operational_pp234_learned_router_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00025__shrink_0p5__05136ee71e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_0p0__cap_0p00025__shrink_0p5__fce38c53dc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_0p0__cap_0p00025__shrink_0p5__f1bee68939 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_2em05__cap_0p00025__shrink_0p5__78161409da | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_5em05__cap_0p00025__shrink_0p5__2b880d9e12 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_0p0__cap_0p00025__shrink_0p8__578c5cfc4b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_2em05__cap_0p00025__shrink_0p8__9bf33f7393 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_5em05__cap_0p00025__shrink_0p8__36bc77f5e9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_0p0__cap_0p00012__shrink_0p5__b97a4a540f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_2em05__cap_0p00012__shrink_0p5__02e154ed8a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_5em05__cap_0p00012__shrink_0p5__2175978594 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_0p0__cap_0p00012__shrink_0p8__00ad4ad4f4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_2em05__cap_0p00012__shrink_0p8__b8093b1624 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_5em05__cap_0p00012__shrink_0p8__0dc9bbcc31 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018841 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00025__shrink_0p8__adfe36b548 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_0p0__cap_0p00025__shrink_0p8__8b95fec5ed | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_0p0__cap_0p00045__shrink_0p8__be5b1790cc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_0p0__cap_0p00045__shrink_0p8__8d229312d4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_0p0__cap_0p00045__shrink_0p8__42534fc54b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p55__s_0p7__cap_0p00028__fd20d05946 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p65__s_0p7__cap_0p00028__8b73a41c92 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p55__s_0p7__cap_0p00028__340e9b8308 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p65__s_0p7__cap_0p00028__33184f8199 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_0p0__cap_0p00045__shrink_0p5__5089c00f3d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_0p0__cap_0p00045__shrink_0p5__38adc954da | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_0p0__cap_0p00045__shrink_0p5__c29c133fea | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_0p0__cap_0p00025__shrink_0p5__786764ff72 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_0p0__cap_0p00025__shrink_0p5__0c202e8afa | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_0p0__cap_0p00025__shrink_0p5__cff75acfdb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_0p0__cap_0p00025__shrink_0p8__5a25a95e12 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_0p0__cap_0p00025__shrink_0p8__db9eb07dc9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_0p0__cap_0p00025__shrink_0p8__1195dba7c2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p55__s_0p7__cap_0p00028__bc4b8d076f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p65__s_0p7__cap_0p00028__9b6f33deb4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p55__s_0p7__cap_0p00028__91cb2771c6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p65__s_0p7__cap_0p00028__fc43b77786 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_0p0__cap_0p00045__shrink_0p8__81538c2837 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_2em05__cap_0p00045__shrink_0p8__ad329ffccc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_5em05__cap_0p00045__shrink_0p8__712a79d69a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00012__shrink_0p5__c53b9713ef | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_0p0__cap_0p00012__shrink_0p5__7b45104180 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p55__s_0p7__cap_0p00012__54c6f53aeb | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p65__s_0p7__cap_0p00012__6ed8d3952c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p55__s_0p7__cap_0p00012__c09b15bc8a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p65__s_0p7__cap_0p00012__b2f745c1e7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p55__s_0p7__cap_0p00012__4229a19cf5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p65__s_0p7__cap_0p00012__7745ae435c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p55__s_0p7__cap_0p00012__ab638acc03 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p65__s_0p7__cap_0p00012__8fb80730c8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_0p0__cap_0p00012__shrink_0p5__d380120b54 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_0p0__cap_0p00012__shrink_0p5__5d5c03808e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_0p0__cap_0p00012__shrink_0p5__7dc2873289 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p55__s_0p35__cap_0p00028__9507830d63 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p65__s_0p35__cap_0p00028__0f72363d7e | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p55__s_0p35__cap_0p00028__2566e51871 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00012__shrink_0p8__d1b73cd851 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_0p0__cap_0p00012__shrink_0p8__2411c73b10 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p65__s_0p35__cap_0p00028__8190ddd73f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_0p0__cap_0p00045__shrink_0p5__a48346e182 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_2em05__cap_0p00045__shrink_0p5__fd814131dc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_8__gain_5em05__cap_0p00045__shrink_0p5__eb9a38cc32 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p55__s_0p35__cap_0p00012__6936bc6b2b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p6__thr_0p65__s_0p35__cap_0p00012__8acd17fbca | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p55__s_0p35__cap_0p00012__5aa0c6f138 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_mape__c_0p2__thr_0p65__s_0p35__cap_0p00012__21a5f30728 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_0p0__cap_0p00012__shrink_0p8__3380445de3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_0p0__cap_0p00012__shrink_0p8__e2f6c66629 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_0p0__cap_0p00012__shrink_0p8__d2ce587766 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p55__s_0p35__cap_0p00012__46c58952a9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p55__s_0p35__cap_0p00028__9f0a6db9e4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p65__s_0p35__cap_0p00012__339ef4bd44 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p2__thr_0p65__s_0p35__cap_0p00028__e7af30d235 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p55__s_0p35__cap_0p00012__020c54b037 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p55__s_0p35__cap_0p00028__2f6b12843f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p65__s_0p35__cap_0p00012__0db7ec2476 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt238_pairwise_uplift__target_pp228_operational__c_0p6__thr_0p65__s_0p35__cap_0p00028__eedd4d306c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747115 | -0.018829 |
| candidate_ppopt235_pp234_significance_audit_anchor__47f2cd9b74 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_2em05__cap_0p00012__shrink_0p5__71221836d3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_2em05__cap_0p00012__shrink_0p8__7fdf9b14cc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_2em05__cap_0p00025__shrink_0p5__214e9b8dcd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_2em05__cap_0p00025__shrink_0p8__e11a61ad66 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_2em05__cap_0p00045__shrink_0p5__b7399e0c12 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_2em05__cap_0p00045__shrink_0p8__fc43117986 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_5em05__cap_0p00012__shrink_0p5__8ba9e1b29d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_5em05__cap_0p00012__shrink_0p8__c408aaff0d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_5em05__cap_0p00025__shrink_0p5__b6dd8ea849 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_5em05__cap_0p00025__shrink_0p8__a6648c5195 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_5em05__cap_0p00045__shrink_0p5__d0d26a7591 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_5em05__cap_0p00045__shrink_0p8__57b103895a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_2em05__cap_0p00012__shrink_0p5__2cad0a85d7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_2em05__cap_0p00012__shrink_0p8__63daf57393 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_2em05__cap_0p00025__shrink_0p5__7f9665e38b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_2em05__cap_0p00025__shrink_0p8__041f089625 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_2em05__cap_0p00045__shrink_0p5__a931db9869 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_2em05__cap_0p00045__shrink_0p8__5163ff1d41 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_5em05__cap_0p00012__shrink_0p5__310da83284 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_5em05__cap_0p00012__shrink_0p8__210c7a88f6 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_5em05__cap_0p00025__shrink_0p5__26606bb134 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_5em05__cap_0p00025__shrink_0p8__d1b7a81ee4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_5em05__cap_0p00045__shrink_0p5__e1f16408ae | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf__minn_8__gain_5em05__cap_0p00045__shrink_0p8__ee85d2ab84 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_0p0__cap_0p00012__shrink_0p5__50f0fb7e2f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_0p0__cap_0p00012__shrink_0p8__1e887b6c98 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_0p0__cap_0p00025__shrink_0p5__754d04973c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_0p0__cap_0p00025__shrink_0p8__03f2cb7be8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_0p0__cap_0p00045__shrink_0p5__17bc686242 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_0p0__cap_0p00045__shrink_0p8__26d371e360 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_2em05__cap_0p00012__shrink_0p5__9c6b9c3fbe | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_2em05__cap_0p00012__shrink_0p8__acb44774d1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_2em05__cap_0p00025__shrink_0p5__05d15dd614 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_2em05__cap_0p00025__shrink_0p8__1bca971bf1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_2em05__cap_0p00045__shrink_0p5__94631796cf | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_2em05__cap_0p00045__shrink_0p8__5efcd0cffc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_5em05__cap_0p00012__shrink_0p5__adc6dfbc4d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_5em05__cap_0p00012__shrink_0p8__a517f55d0c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_5em05__cap_0p00025__shrink_0p5__6b1a195887 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_5em05__cap_0p00025__shrink_0p8__fce5afe3c8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_5em05__cap_0p00045__shrink_0p5__5603512c05 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_15__gain_5em05__cap_0p00045__shrink_0p8__090e769c3f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_2em05__cap_0p00012__shrink_0p5__f329559fbc | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_2em05__cap_0p00012__shrink_0p8__a44c256999 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_2em05__cap_0p00025__shrink_0p5__c13770bb2a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_2em05__cap_0p00025__shrink_0p8__6f427ab888 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_2em05__cap_0p00045__shrink_0p5__b630d0d12c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_2em05__cap_0p00045__shrink_0p8__f883fa5fa3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_5em05__cap_0p00012__shrink_0p5__790920bc01 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_5em05__cap_0p00012__shrink_0p8__a4a7ae5798 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_5em05__cap_0p00025__shrink_0p5__8132340d26 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_5em05__cap_0p00025__shrink_0p8__fe4f863a02 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_5em05__cap_0p00045__shrink_0p5__3cbdbcd24f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_medium__minn_8__gain_5em05__cap_0p00045__shrink_0p8__78a8699649 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_0p0__cap_0p00012__shrink_0p5__c90f4fbef2 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_0p0__cap_0p00012__shrink_0p8__ea3b7187e8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_0p0__cap_0p00025__shrink_0p5__a34418d65d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_0p0__cap_0p00025__shrink_0p8__22ac296619 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_0p0__cap_0p00045__shrink_0p5__3b6d8fb0ed | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_0p0__cap_0p00045__shrink_0p8__5f0dd17e56 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_2em05__cap_0p00012__shrink_0p5__319af204fe | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_2em05__cap_0p00012__shrink_0p8__52dadba70a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_2em05__cap_0p00025__shrink_0p5__cdf54b7eaf | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_2em05__cap_0p00025__shrink_0p8__56cf87d85c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_2em05__cap_0p00045__shrink_0p5__cea3bc6603 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_2em05__cap_0p00045__shrink_0p8__672976c7d4 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_5em05__cap_0p00012__shrink_0p5__bf7d12a663 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_5em05__cap_0p00012__shrink_0p8__40f54b5ed7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_5em05__cap_0p00025__shrink_0p5__046465b287 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_5em05__cap_0p00025__shrink_0p8__63ad03ee51 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_5em05__cap_0p00045__shrink_0p5__fa218a528d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_conf_qwidth__minn_15__gain_5em05__cap_0p00045__shrink_0p8__7ee5357cb1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_2em05__cap_0p00012__shrink_0p5__c0c3b643b8 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_2em05__cap_0p00012__shrink_0p8__bbde2ee0d9 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_2em05__cap_0p00025__shrink_0p5__5b720a04cf | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_2em05__cap_0p00025__shrink_0p8__394ee142fa | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_2em05__cap_0p00045__shrink_0p5__1dcb36e4c5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_2em05__cap_0p00045__shrink_0p8__53223483c7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_5em05__cap_0p00012__shrink_0p5__a70917045c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_5em05__cap_0p00012__shrink_0p8__40d2e157e7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_5em05__cap_0p00025__shrink_0p5__3ebec739c1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_5em05__cap_0p00025__shrink_0p8__f0769ae3a7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_5em05__cap_0p00045__shrink_0p5__31328296ba | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_15__gain_5em05__cap_0p00045__shrink_0p8__d50e7c098b | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_2em05__cap_0p00012__shrink_0p5__a934fb6ff7 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_2em05__cap_0p00012__shrink_0p8__590805fb04 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_2em05__cap_0p00025__shrink_0p5__78e68611bd | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_2em05__cap_0p00025__shrink_0p8__393a950a3f | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_2em05__cap_0p00045__shrink_0p5__13926bace5 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_2em05__cap_0p00045__shrink_0p8__c01ace235d | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_5em05__cap_0p00012__shrink_0p5__10ae56692a | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_5em05__cap_0p00012__shrink_0p8__5cce09b3c1 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_5em05__cap_0p00025__shrink_0p5__09800e1ff3 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_5em05__cap_0p00025__shrink_0p8__2fe3253339 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_5em05__cap_0p00045__shrink_0p5__b608990996 | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |
| candidate_ppopt236_segment_winner__seg_price_medium__minn_8__gain_5em05__cap_0p00045__shrink_0p8__c6f82d4c6c | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.953846 | 0.747756 | -0.018828 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT235-240",
  "experiment_slug": "PP-OPT235_240_warm_pp234_significance_audit_and_learned_router",
  "created_at": "2026-06-10T12:40:53",
  "previous_experiment": "experiments/track6/PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 384,
  "prediction_rows": 432384,
  "support_candidates": {
    "pp166_operational": "ppopt166_operational_pp157_negative_gate_challenger__source=ppopt163_segment_outcome__target_pp157_price_qwidth_q084_s100_cap008__seg_price_conf__hw_1p2__thr_0p0__s_1p0__cap_0p006",
    "pp166_p95": "ppopt166_p95_pp157_negative_gate_challenger__source=reference_pp148_p95",
    "pp148_operational": "reference_pp148_operational",
    "pp148_p95": "reference_pp148_p95",
    "pp161_p95_guard": "ppopt161_harm_rollback__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p3__w=0p14__rb=1p0__s=1p0__cap=0p006",
    "pp162_p95_gate": "ppopt162_gain_harm_adopt__target=pp157_price_qwidth_q084_s100_cap008__thr=0p18__w=0p1__hpen=0p5__s=1p0__cap=0p006",
    "pp164_p95_block": "ppopt164_hard_block__target=pp157_price_qwidth_q084_s100_cap008__hthr=0p45__gthr=0p12__s=1p0__cap=0p006",
    "pp172_operational": "ppopt172_operational_pp166_tail_calibration_challenger__source=ppopt169_segment_router__source_pp162_p95_gate__seg_price_conf__thr_m0p04__s_0p5__cap_0p004",
    "pp172_p95": "ppopt172_p95_pp166_tail_calibration_challenger__source=reference_pp148_p95",
    "pp180_operational": "ppopt180_operational_basis_generation_challenger__source=ppopt174_direct_basis__source_stack_huber_weighted__thr_0p08__s_0p3__cap_0p004",
    "pp180_p95": "ppopt180_p95_basis_generation_challenger__source=reference_pp148_p95",
    "pp186_operational": "ppopt186_operational_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045",
    "pp186_strict": "ppopt186_strict_guarded_huber_basis_p95_guard__source=ppopt184_huber_p95_blend__partner_cat_plain__hshare_0p65__thr_0p04__s_0p42__cap_0p0045",
    "pp186_p95": "ppopt186_p95_huber_basis_p95_guard__source=reference_pp148_p95",
    "pp192_operational": "ppopt192_operational_pp180_pp186_risk_router__source=ppopt189_segment_router__seg_price_gap__scorethr_0p02__mix_0p75__s_0p95__cap_0p0025",
    "pp192_p95_guarded": "ppopt192_p95_guarded_pp180_pp186_risk_router__source=ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w_0p06__s_0p75",
    "pp192_p95_extreme": "ppopt192_p95_extreme_pp180_pp186_risk_router__source=reference_pp148_p95",
    "pp198_operational": "ppopt198_operational_segment_router_refinement__source=ppopt194_price_conf_refine__scorethr_0p02__mix_0p25__s_1p05__cap_0p006",
    "pp198_p95_guarded": "ppopt198_p95_guarded_segment_router_refinement__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
    "pp198_p95_extreme": "ppopt198_p95_extreme_segment_router_refinement__source=reference_pp148_p95",
    "pp204_operational": "ppopt204_operational_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8",
    "pp204_mape": "ppopt204_mape_challenger_pp192_pp198_winner_router__source=ppopt201_p95_guarded_winner__seg_price_conf__thr_0p08__s_1p0__basecap_0p006__shrink_0p8",
    "pp204_p95_guarded": "ppopt204_p95_guarded_pp192_pp198_winner_router__source=ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_hard_risk_router__risk_uncertainty__mode_hard__thr_0p78__w",
    "pp204_p95_extreme": "ppopt204_p95_extreme_pp192_pp198_winner_router__source=reference_pp148_p95",
    "pp210_operational": "ppopt210_operational_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0055__shrink_0p9",
    "pp210_mape": "ppopt210_mape_challenger_pp204_local_refinement__source=ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap_0p0065__shrink_0p65",
    "pp210_p95_guarded": "ppopt210_p95_guarded_pp204_local_refinement__source=ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_guarded_pp180_pp186_risk_router__source_ppopt187_har",
    "pp210_p95_extreme": "ppopt210_p95_extreme_pp204_local_refinement__source=reference_pp148_p95",
    "pp216_operational": "ppopt216_operational_pp210_p95_recovery__source=ppopt211_segment_recovery__seg_price_conf__thr_0p08__s_0p25__cap_0p0005",
    "pp216_p95_recovery": "ppopt216_p95_recovery_pp210_p95_recovery__source=ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0p005__shrink_1p2",
    "pp216_mape": "ppopt216_mape_challenger_pp210_p95_recovery__source=ppopt210_mape_challenger_pp204_local_refinement__source_ppopt205_local_price_conf__thr_0p04__width_0p22__s_1p16__basecap",
    "pp216_p95_guarded": "ppopt216_p95_guarded_pp210_p95_recovery__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "pp216_p95_extreme": "ppopt216_p95_extreme_pp210_p95_recovery__source=reference_pp148_p95",
    "pp222_operational": "ppopt222_operational_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0056__shrink_0p9",
    "pp222_balanced": "ppopt222_balanced_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p0052__shrink_0p9",
    "pp222_p95_recovery": "ppopt222_p95_recovery_p95_regularized_rebuild__source=ppopt216_p95_recovery_pp210_p95_recovery__source_ppopt215_p95_aware_rebuild__thr_0p02__p95thr_m0p0001__s_1p16__basecap_0",
    "pp222_mape": "ppopt222_mape_challenger_p95_regularized_rebuild__source=ppopt217_p95_regularized_rebuild__thr_0p02__p95thr_m0p00014__p95width_0p00012__s_1p24__basecap_0p006__shrink_0p9",
    "pp222_p95_guarded": "ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "pp222_p95_extreme": "ppopt222_p95_extreme_p95_regularized_rebuild__source=reference_pp148_p95"
  },
  "prior_decision": {
    "operational_label": "candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94__f45db05a1a",
    "operational_candidate": "ppopt224_risk_shaped_cap__curve=1p25__s=1p26__basecap=0p0052__shrink=0p94",
    "operational_fixed_test_MAPE": 0.26988910777837405,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp222_balanced_MAPE": -8.899573992748877e-07,
    "operational_delta_vs_pp222_balanced_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp222_aggressive_MAPE": -3.8992606044008227e-07,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018841600803952974,
    "balanced_label": "candidate_ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__545ef9d07f",
    "balanced_candidate": "ppopt223_neighborhood__thr=0p015__p95thr=m0p00012__p95width=0p00012__s=1p26__basecap=0p00545__shrink=0p92",
    "balanced_fixed_test_MAPE": 0.26988950282542246,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745390902379023,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp222_balanced_MAPE": -4.949103508677943e-07,
    "balanced_delta_vs_pp222_balanced_p95_win_rate": 0.0,
    "balanced_delta_vs_pp222_aggressive_MAPE": 5.120987967011104e-09,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.018828385244084058,
    "mape_challenger_label": "candidate_ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86__69ab40e036",
    "mape_challenger_candidate": "ppopt224_risk_shaped_cap__curve=1p25__s=1p26__basecap=0p0054__shrink=0p86",
    "mape_challenger_fixed_test_MAPE": 0.26988883720393,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006752047117303817,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp222_balanced_MAPE": -1.16053184334719e-06,
    "mape_challenger_delta_vs_pp222_balanced_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp222_aggressive_MAPE": -6.605005045123846e-07,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.953525641025641,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.018816230352756022,
    "p95_guarded_label": "pp222_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt222_p95_guarded_p95_regularized_rebuild__source=ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_guarded_pp192_pp198_winner_router__source_ppopt192_p95_",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp222_balanced_MAPE": 5.920340631432319e-05,
    "p95_guarded_delta_vs_pp222_balanced_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp222_aggressive_MAPE": 5.9703437653158e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp148_p95_reference",
    "p95_extreme_candidate": "reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp222_balanced_MAPE": 0.00037892817333462503,
    "p95_extreme_delta_vs_pp222_balanced_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp222_aggressive_MAPE": 0.00037942820467345983,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt228_operational_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0052__shrink_0p94",
    "balanced_protocol_candidate": "ppopt228_balanced_pp222_narrow_balance__source=ppopt223_neighborhood__thr_0p015__p95thr_m0p00012__p95width_0p00012__s_1p26__basecap_0p00545__shrink_0p92",
    "mape_challenger_protocol_candidate": "ppopt228_mape_challenger_pp222_narrow_balance__source=ppopt224_risk_shaped_cap__curve_1p25__s_1p26__basecap_0p0054__shrink_0p86",
    "p95_guarded_protocol_candidate": "ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu",
    "p95_extreme_protocol_candidate": "ppopt228_p95_extreme_pp222_narrow_balance__source=reference_pp148_p95"
  },
  "pp234_decision": {
    "operational_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "operational_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "operational_fixed_test_MAPE": 0.2698894975680414,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "operational_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "operational_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "operational_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "operational_avg_pp64_p95_win_rate": 0.7477564102564102,
    "operational_replacement_score": -0.01882839050146509,
    "balanced_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "balanced_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "balanced_fixed_test_MAPE": 0.2698894975680414,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "balanced_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "balanced_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839050146509,
    "mape_challenger_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "mape_challenger_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "mape_challenger_fixed_test_MAPE": 0.2698894975680414,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "mape_challenger_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "mape_challenger_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7477564102564102,
    "mape_challenger_replacement_score": -0.01882839050146509,
    "p95_recovery_label": "candidate_ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve___49fa782c9b",
    "p95_recovery_candidate": "ppopt229_aggressive_gated_lift__seg=price_conf__s=0p75__basecap=0p00018__shrink=0p55__curve=1p25",
    "p95_recovery_fixed_test_MAPE": 0.2698894975680414,
    "p95_recovery_fixed_test_p95_APE": 0.8073255046591389,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "p95_recovery_delta_vs_pp228_balanced_MAPE": -5.257381030521202e-09,
    "p95_recovery_delta_vs_pp228_balanced_p95_win_rate": 0.0,
    "p95_recovery_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.7477564102564102,
    "p95_recovery_replacement_score": -0.01882839050146509,
    "p95_guarded_label": "pp228_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt228_p95_guarded_pp222_narrow_balance__source=ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guarded_pp204_local_refinement__source_ppopt204_p95_gu",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp228_balanced_MAPE": 5.969831666519099e-05,
    "p95_guarded_delta_vs_pp228_balanced_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp228_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp228_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt228_p95_extreme_pp222_narrow_balance__source=reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp228_balanced_MAPE": 0.0003794230836854928,
    "p95_extreme_delta_vs_pp228_balanced_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp228_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt234_operational_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "balanced_protocol_candidate": "ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "mape_challenger_protocol_candidate": "ppopt234_mape_challenger_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "p95_recovery_protocol_candidate": "ppopt234_p95_recovery_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25",
    "p95_guarded_protocol_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_extreme_protocol_candidate": "ppopt234_p95_extreme_pp228_p95_recovery__source=ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95"
  },
  "selection_decision": {
    "operational_label": "candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5__0e1d316316",
    "operational_candidate": "ppopt236_segment_winner__seg=price_conf__minn=15__gain=0p0__cap=0p00045__shrink=0p5",
    "operational_fixed_test_MAPE": 0.26988910777837405,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "operational_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp228_operational_MAPE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018841600803952974,
    "balanced_label": "candidate_ppopt235_pp234_significance_audit_anchor__47f2cd9b74",
    "balanced_candidate": "ppopt235_pp234_significance_audit_anchor",
    "balanced_fixed_test_MAPE": 0.2698894975680414,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745443476189328,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp234_MAPE": 0.0,
    "balanced_delta_vs_pp234_p95_win_rate": 0.0,
    "balanced_delta_vs_pp228_operational_MAPE": 3.8978966737657217e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839050146509,
    "mape_challenger_label": "candidate_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5__0e1d316316",
    "mape_challenger_candidate": "ppopt236_segment_winner__seg=price_conf__minn=15__gain=0p0__cap=0p00045__shrink=0p5",
    "mape_challenger_fixed_test_MAPE": 0.26988910777837405,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "mape_challenger_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp228_operational_MAPE": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.018841600803952974,
    "p95_recovery_label": "candidate_ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001__f511ed44fa",
    "p95_recovery_candidate": "ppopt239_probability_blend__probs=multiclass_c0p6_seed17__thr=0p35__s=0p8__cap=0p0001",
    "p95_recovery_fixed_test_MAPE": 0.26989020449203693,
    "p95_recovery_fixed_test_p95_APE": 0.8073230727405295,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006738374236234246,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017577956558034735,
    "p95_recovery_delta_vs_pp234_MAPE": 7.069239955082018e-07,
    "p95_recovery_delta_vs_pp234_p95_win_rate": 0.07916666666666683,
    "p95_recovery_delta_vs_pp228_operational_MAPE": 1.096713662884774e-06,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "p95_recovery_avg_pp64_p95_win_rate": 0.826923076923077,
    "p95_recovery_replacement_score": -0.01882768357746958,
    "p95_guarded_label": "pp234_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp234_MAPE": 5.970357404622151e-05,
    "p95_guarded_delta_vs_pp234_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp228_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp234_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt234_p95_extreme_pp228_p95_recovery__source=ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp234_MAPE": 0.00037942834106652334,
    "p95_extreme_delta_vs_pp234_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp228_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt240_operational_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "balanced_protocol_candidate": "ppopt240_balanced_pp234_learned_router__source=ppopt235_pp234_significance_audit_anchor",
    "mape_challenger_protocol_candidate": "ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "p95_recovery_protocol_candidate": "ppopt240_p95_recovery_pp234_learned_router__source=ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001",
    "p95_guarded_protocol_candidate": "ppopt240_p95_guarded_pp234_learned_router__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p",
    "p95_extreme_protocol_candidate": "ppopt240_p95_extreme_pp234_learned_router__source=ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95"
  },
  "items": [
    {
      "item_id": "PP-OPT235",
      "priority": "1",
      "title": "PP234 significance audit",
      "description": "PP234의 PP228 대비 미세 개선이 bootstrap과 그룹 제외에서도 유지되는지 검증."
    },
    {
      "item_id": "PP-OPT236",
      "priority": "2",
      "title": "segment winner router",
      "description": "validation OOF의 구간별 APE winner를 기반으로 후보를 선택하되 작은 cap으로 제한."
    },
    {
      "item_id": "PP-OPT237",
      "priority": "3",
      "title": "learned multiclass candidate router",
      "description": "row 피쳐로 PP234/PP228 공격형/MAPE/p95 후보 중 APE winner를 cross-fit 분류."
    },
    {
      "item_id": "PP-OPT238",
      "priority": "4",
      "title": "pairwise uplift router",
      "description": "각 후보가 PP234보다 row APE를 낮출 확률을 binary cross-fit으로 학습."
    },
    {
      "item_id": "PP-OPT239",
      "priority": "5",
      "title": "probability blend router",
      "description": "multiclass winner 확률을 이용해 후보 로그가격을 확률 가중 혼합하되 PP234 기준 cap 적용."
    },
    {
      "item_id": "PP-OPT240",
      "priority": "6",
      "title": "final PP234 learned-router decision",
      "description": "PP234 기준 MAPE/p95/replacement 하한을 만족하는 후보만 운영 교체 대상으로 선택."
    }
  ],
  "router_formula": {
    "base": "PP234 balanced log price",
    "segment_router": "For each validation segment, choose the candidate with lower mean APE than PP234, then cap movement from PP234.",
    "multiclass_router": "Cross-fit logistic classifier predicts row-level APE winner among PP234, PP228 operational, PP228 MAPE, PP228 p95-guarded, PP216 p95-recovery.",
    "pairwise_router": "Binary uplift classifier estimates whether a target candidate beats PP234, then moves toward target with capped probability weight.",
    "probability_blend": "Blend candidate log prices by multiclass winner probabilities, then cap movement from PP234.",
    "selection_goal": "Beat PP234 MAPE without reducing repeated p95 win rate or worsening replacement score materially."
  }
}
```