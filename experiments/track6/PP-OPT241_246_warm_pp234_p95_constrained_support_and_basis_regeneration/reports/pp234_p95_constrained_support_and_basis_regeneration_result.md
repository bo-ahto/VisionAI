# PP-OPT241~246 Warm PP234 p95-constrained support and basis regeneration 결과

- 작성일: 2026-06-10 12:54
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 목적: PP234를 기준으로 p95-support tiny cap과 residual/basis 재생성 후보를 검증
- 결론: 운영 후보 MAPE 0.269889, p95 win rate 0.747115. PP234 대비 MAPE 변화 -0.000000390, p95 win rate 변화 -0.000641.

## 주요 후보 test 비교
| candidate | family | item_id | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt240_operational_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt246_operational_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p | pp234_p95_constrained_operational_selection | PP-OPT246 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt246_mape_challenger_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p | pp234_p95_constrained_mape_selection | PP-OPT246 | 0.140975 | 0.269889 | 0.807326 | 0.397455 | -0.001506 | -0.000804 |
| ppopt246_balanced_pp234_p95_constrained__source=ppopt241_p95_support__src_s3__seg_price_conf__s_0p22__cap_0p0001__shrink_0p5 | pp234_p95_constrained_balanced_selection | PP-OPT246 | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt234_balanced_pp228_p95_recovery__source=ppopt229_aggressive_gated_lift__seg_price_conf__s_0p75__basecap_0p00018__shrink_0p55__curve_1p25 | reference_prior | REFERENCE | 0.140975 | 0.269889 | 0.807326 | 0.397456 | -0.001505 | -0.000804 |
| ppopt240_p95_recovery_pp234_learned_router__source=ppopt239_probability_blend__probs_multiclass_c0p6_seed17__thr_0p35__s_0p8__cap_0p0001 | reference_prior | REFERENCE | 0.140941 | 0.269890 | 0.807323 | 0.397456 | -0.001505 | -0.000807 |
| ppopt246_p95_recovery_pp234_p95_constrained__source=ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5 | pp234_p95_constrained_p95_support_selection | PP-OPT246 | 0.140990 | 0.269890 | 0.807321 | 0.397455 | -0.001505 | -0.000809 |
| ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar | reference_prior | REFERENCE | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| ppopt246_p95_guarded_pp234_p95_constrained__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p | pp234_p95_constrained_p95_guarded_selection | PP-OPT246 | 0.140094 | 0.269949 | 0.807255 | 0.397482 | -0.001446 | -0.000875 |
| reference_pp64_current_best | reference_prior | REFERENCE | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |

## 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | p95_test_MAPE | p95_test_p95_APE | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | final PP234 p95-constrained support decision | 6 | 0.269889 | 0.807326 | 0.270269 | 0.805949 | pp234_p95_constrained_mape_selection | ppopt246_mape_challenger_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p |
| 1 | p95 support from learned-router candidates | 256 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | pp234_p95_constrained_support | ppopt241_p95_support__src=s3__seg=price_conf__s=0p22__cap=0p0001__shrink=0p5 |
| 2 | p95 guarded/recovery ultra support | 64 | 0.269889 | 0.807326 | 0.269889 | 0.807326 | pp234_guarded_recovery_ultra_support | ppopt242_guarded_recovery_support__target=guarded__s=0p02__cap=1p5em05__shrink=0p65 |
| 3 | Huber/Ridge residual regeneration | 192 | 0.269890 | 0.807321 | 0.269894 | 0.807297 | pp234_linear_residual_regeneration | ppopt243_linear_residual__model=huber_1p15__s=0p22__cap=3em05__shrink=0p5 |
| 4 | tree residual regeneration | 256 | 0.269890 | 0.807324 | 0.269913 | 0.807302 | pp234_tree_residual_regeneration | ppopt244_tree_residual__model=lgbm_80__s=0p16__cap=2em05__shrink=0p85 |
| 5 | residual plus p95 support ensemble | 216 | 0.269890 | 0.807322 | 0.269892 | 0.807315 | pp234_residual_plus_p95_support | ppopt245_residual_support__resid=huber_1p15__support=s1__rs=0p1__ps=0p04__cap=3em05 |

## 탐색 후보 상위
| candidate | item_id | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppopt246_p95_guarded_pp234_p95_constrained__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p | PP-OPT246 | pp234_p95_constrained_p95_guarded_selection | 0.269949 | 0.807255 | -0.001446 | -0.000875 | -0.001537 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269902 | 0.807298 | -0.001493 | -0.000832 | -0.001428 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269902 | 0.807298 | -0.001492 | -0.000832 | -0.001428 |
| ppopt243_linear_residual__model=huber_1p7__s=0p14__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269903 | 0.807298 | -0.001492 | -0.000832 | -0.001427 |
| ppopt243_linear_residual__model=huber_1p7__s=0p22__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269903 | 0.807298 | -0.001492 | -0.000832 | -0.001427 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p22__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269908 | 0.807299 | -0.001487 | -0.000831 | -0.001425 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p14__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269908 | 0.807299 | -0.001487 | -0.000831 | -0.001425 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p08__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269907 | 0.807299 | -0.001487 | -0.000831 | -0.001425 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p22__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269906 | 0.807299 | -0.001489 | -0.000831 | -0.001425 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p14__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269906 | 0.807299 | -0.001489 | -0.000831 | -0.001424 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p04__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269905 | 0.807299 | -0.001490 | -0.000831 | -0.001424 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p08__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269905 | 0.807299 | -0.001490 | -0.000831 | -0.001424 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p04__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269907 | 0.807299 | -0.001488 | -0.000831 | -0.001424 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269893 | 0.807317 | -0.001501 | -0.000813 | -0.001422 |
| ppopt243_linear_residual__model=huber_1p7__s=0p22__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807317 | -0.001501 | -0.000813 | -0.001422 |
| ppopt243_linear_residual__model=huber_1p7__s=0p14__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807317 | -0.001501 | -0.000813 | -0.001422 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807317 | -0.001501 | -0.000813 | -0.001422 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p08__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269909 | 0.807299 | -0.001486 | -0.000831 | -0.001422 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p22__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269909 | 0.807299 | -0.001485 | -0.000831 | -0.001422 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p14__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269909 | 0.807299 | -0.001486 | -0.000831 | -0.001422 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p04__cap=0p0002__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269908 | 0.807299 | -0.001487 | -0.000831 | -0.001421 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p22__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001500 | -0.000813 | -0.001421 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p14__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001500 | -0.000813 | -0.001421 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p08__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001500 | -0.000813 | -0.001421 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p04__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001500 | -0.000813 | -0.001421 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p04__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001499 | -0.000813 | -0.001420 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p08__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269896 | 0.807317 | -0.001499 | -0.000813 | -0.001420 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p14__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001499 | -0.000813 | -0.001420 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p22__cap=6em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269895 | 0.807317 | -0.001499 | -0.000813 | -0.001420 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269893 | 0.807319 | -0.001502 | -0.000811 | -0.001418 |
| ppopt243_linear_residual__model=huber_1p7__s=0p22__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269893 | 0.807319 | -0.001502 | -0.000811 | -0.001418 |
| ppopt243_linear_residual__model=huber_1p7__s=0p14__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269893 | 0.807319 | -0.001502 | -0.000811 | -0.001418 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269893 | 0.807319 | -0.001502 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p1__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p1__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p1__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p1__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p1__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p1__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p06__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p06__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p06__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p06__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p06__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p06__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p03__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p03__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p03__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p03__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p03__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p03__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p06__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p06__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p06__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p06__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p06__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p06__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p1__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p1__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p1__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p1__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p1__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p1__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001418 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p03__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p03__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p03__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p03__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p03__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p03__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001501 | -0.000811 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p22__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p14__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p08__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p04__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p08__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p14__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p22__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p04__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807320 | -0.001501 | -0.000810 | -0.001417 |
| ppopt243_linear_residual__model=huber_1p7__s=0p14__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269891 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=huber_1p7__s=0p22__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269891 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p03__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p03__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p03__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p03__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p03__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p03__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p06__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p06__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p06__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p06__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p06__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p06__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p1__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p1__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s1__rs=0p1__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p1__ps=0p04__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p1__ps=0p08__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt245_residual_support__resid=ridge_6p0__support=s2__rs=0p1__ps=0p14__cap=6em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269894 | 0.807319 | -0.001500 | -0.000811 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p14__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p22__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p08__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=ridge_2p0__s=0p04__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001417 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p04__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807319 | -0.001500 | -0.000810 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p08__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807319 | -0.001500 | -0.000810 | -0.001416 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p04__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p08__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p22__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_0p5__s=0p14__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001503 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p14__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807319 | -0.001500 | -0.000810 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p22__cap=6em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269894 | 0.807319 | -0.001500 | -0.000810 | -0.001416 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=0p0002__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269900 | 0.807305 | -0.001495 | -0.000825 | -0.001416 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=0p0002__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269901 | 0.807305 | -0.001494 | -0.000825 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p04__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269893 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p08__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p14__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=ridge_6p0__s=0p22__cap=3em05__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269892 | 0.807321 | -0.001502 | -0.000809 | -0.001416 |
| ppopt243_linear_residual__model=huber_1p7__s=0p14__cap=0p0002__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269901 | 0.807305 | -0.001494 | -0.000825 | -0.001416 |
| ppopt243_linear_residual__model=huber_1p7__s=0p22__cap=0p0002__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269901 | 0.807305 | -0.001494 | -0.000825 | -0.001416 |
| ppopt243_linear_residual__model=huber_1p7__s=0p14__cap=3em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269891 | 0.807322 | -0.001504 | -0.000808 | -0.001415 |
| ppopt243_linear_residual__model=huber_1p7__s=0p22__cap=3em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269891 | 0.807322 | -0.001504 | -0.000808 | -0.001415 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=3em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269891 | 0.807322 | -0.001504 | -0.000808 | -0.001415 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=3em05__shrink=0p8 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269891 | 0.807322 | -0.001504 | -0.000808 | -0.001415 |
| ppopt243_linear_residual__model=huber_1p7__s=0p04__cap=0p00012__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269897 | 0.807309 | -0.001498 | -0.000821 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p1__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p1__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p1__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p1__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p1__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p1__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p06__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p06__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p06__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p06__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p06__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p06__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p03__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p03__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s1__rs=0p03__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p03__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p03__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_2p0__support=s2__rs=0p03__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p03__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p03__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p03__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p03__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p03__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p03__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p06__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p06__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p06__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p06__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p06__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p06__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt243_linear_residual__model=huber_1p7__s=0p08__cap=0p00012__shrink=0p5 | PP-OPT243 | pp234_linear_residual_regeneration | 0.269897 | 0.807309 | -0.001497 | -0.000821 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p1__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p1__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s1__rs=0p1__ps=0p14__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p1__ps=0p04__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |
| ppopt245_residual_support__resid=ridge_0p5__support=s2__rs=0p1__ps=0p08__cap=3em05 | PP-OPT245 | pp234_residual_plus_p95_support | 0.269892 | 0.807322 | -0.001503 | -0.000808 | -0.001415 |

## 선택 후보 반복 안정성
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_0p0002__shrink_0p5__f7cc8f4a8e | 0.269894 | 0.807297 | -0.000670 | -0.000201 | 0.954808 | 0.665385 | -0.018862 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_0p0002__shrink_0p5__288f0488d4 | 0.269895 | 0.807297 | -0.000669 | -0.000201 | 0.954808 | 0.663782 | -0.018861 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_0p0002__shrink_0p5__67b2b8e443 | 0.269895 | 0.807297 | -0.000669 | -0.000201 | 0.954808 | 0.663782 | -0.018861 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_0p0002__shrink_0p8__8d080b81ea | 0.269895 | 0.807304 | -0.000669 | -0.000195 | 0.954808 | 0.667949 | -0.018861 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_0p0002__shrink_0p5__e352a54fe8 | 0.269895 | 0.807297 | -0.000669 | -0.000201 | 0.954808 | 0.663782 | -0.018861 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_0p00012__shrink_0p5__800af85a85 | 0.269893 | 0.807309 | -0.000671 | -0.000190 | 0.954487 | 0.683013 | -0.018851 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p04__cap_0p0001__77a7a9567c | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954487 | 0.691667 | -0.018851 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p08__cap_0p0001__56c0e127ea | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954487 | 0.691667 | -0.018851 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p14__cap_0p0001__d29f5c3386 | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954487 | 0.691667 | -0.018851 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p04__cap_0p0001__5cac19b08a | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954487 | 0.691667 | -0.018851 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p08__cap_0p0001__8385253565 | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954487 | 0.691667 | -0.018851 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p14__cap_0p0001__0a7a069f3b | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954487 | 0.691667 | -0.018851 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_0p00012__shrink_0p5__9c9ebf6d22 | 0.269893 | 0.807309 | -0.000671 | -0.000190 | 0.954487 | 0.683013 | -0.018851 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_0p00012__shrink_0p5__a79ae8e139 | 0.269893 | 0.807309 | -0.000671 | -0.000190 | 0.954487 | 0.683013 | -0.018851 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_0p00012__shrink_0p5__2839c49794 | 0.269893 | 0.807309 | -0.000671 | -0.000190 | 0.954487 | 0.683013 | -0.018851 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_0p00012__shrink_0p8__5153e67358 | 0.269893 | 0.807312 | -0.000671 | -0.000186 | 0.954487 | 0.683974 | -0.018850 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_0p00012__shrink_0p8__09124b94d1 | 0.269893 | 0.807312 | -0.000671 | -0.000186 | 0.954487 | 0.683974 | -0.018850 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_0p00012__shrink_0p8__a1ca9317b2 | 0.269894 | 0.807312 | -0.000671 | -0.000186 | 0.954487 | 0.683974 | -0.018850 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_0p00012__shrink_0p8__0cad3500b2 | 0.269894 | 0.807312 | -0.000670 | -0.000186 | 0.954487 | 0.683974 | -0.018850 |
| pp228_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp240_mape_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp240_operational_reference | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp246_mape_pp234_p95_constrained_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| pp246_operational_pp234_p95_constrained_candidate | 0.269889 | 0.807326 | -0.000675 | -0.000173 | 0.954167 | 0.747115 | -0.018842 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5__ddb3a8ef18 | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| pp246_p95_recovery_pp234_p95_constrained_candidate | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_3em05__shrink_0p5__769dd7bb3b | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_3em05__shrink_0p5__787708e505 | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_3em05__shrink_0p5__c5839bed63 | 0.269890 | 0.807321 | -0.000674 | -0.000178 | 0.954167 | 0.814103 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p04__cap_3em05__753462e662 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p08__cap_3em05__278d5ac86d | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p14__cap_3em05__de2bcaa44a | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p04__cap_3em05__fa135f256c | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p08__cap_3em05__6b0b261c8c | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p14__cap_3em05__fa5d096100 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p04__cap_3em05__60e552d542 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p08__cap_3em05__dcecab67df | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p14__cap_3em05__fff79aa8fd | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p04__cap_3em05__155d1bbcb1 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p08__cap_3em05__076a633522 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p14__cap_3em05__5ccbc13a9b | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p8__e6e7b34113 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816346 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_3em05__shrink_0p8__2cf859dc28 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816346 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_3em05__shrink_0p8__3336065031 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816346 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p04__cap_3em05__161207b3e7 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p08__cap_3em05__31a67b2b8c | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p14__cap_3em05__b5b0d1be79 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p04__cap_3em05__05f3fbc8ac | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p08__cap_3em05__d3e812520b | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p14__cap_3em05__e61bba2672 | 0.269890 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816026 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_3em05__shrink_0p8__d0503d2e68 | 0.269891 | 0.807322 | -0.000674 | -0.000177 | 0.954167 | 0.816346 | -0.018840 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p16__cap_2em05__shrink_0p85__eea85bacdf | 0.269891 | 0.807324 | -0.000673 | -0.000174 | 0.954167 | 0.827244 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_6em05__shrink_0p5__87b2627db2 | 0.269891 | 0.807317 | -0.000673 | -0.000182 | 0.954167 | 0.701923 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_6em05__shrink_0p5__c07830cb7e | 0.269891 | 0.807317 | -0.000673 | -0.000182 | 0.954167 | 0.701923 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p14__cap_3em05__shrink_0p8__aab37063c7 | 0.269891 | 0.807322 | -0.000673 | -0.000176 | 0.954167 | 0.799359 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p22__cap_3em05__shrink_0p8__d80c2ba5bd | 0.269891 | 0.807322 | -0.000673 | -0.000176 | 0.954167 | 0.799359 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_6em05__shrink_0p5__34c64262b3 | 0.269891 | 0.807317 | -0.000673 | -0.000182 | 0.954167 | 0.701923 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p08__cap_3em05__shrink_0p8__7d821ade18 | 0.269891 | 0.807322 | -0.000673 | -0.000176 | 0.954167 | 0.799359 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p04__cap_3em05__shrink_0p8__2d3e160220 | 0.269891 | 0.807322 | -0.000673 | -0.000176 | 0.954167 | 0.799359 | -0.018840 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_6em05__shrink_0p5__ccf9abad3a | 0.269891 | 0.807317 | -0.000673 | -0.000182 | 0.954167 | 0.701923 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p04__cap_6em05__26a3e0e11f | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p08__cap_6em05__b8f75ee01d | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p14__cap_6em05__1a762103f9 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p04__cap_6em05__e4a93a0e53 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p08__cap_6em05__b69c24266d | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p14__cap_6em05__e40da4971a | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p04__cap_6em05__e476b98c39 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p08__cap_6em05__62307ab44c | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p1__ps_0p14__cap_6em05__aa67afee73 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p04__cap_6em05__930dbdb89f | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p08__cap_6em05__f3b13b5050 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p1__ps_0p14__cap_6em05__d316353e28 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_6em05__shrink_0p8__0bc12e07b6 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p04__cap_6em05__f0d84db7f0 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p08__cap_6em05__fb634e2d72 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p14__cap_6em05__59241ce86c | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p04__cap_6em05__b09f74d0ee | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p08__cap_6em05__5c3db53dac | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p14__cap_6em05__54523fb597 | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p14__cap_6em05__shrink_0p8__cdfbb313ef | 0.269891 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p14__cap_3em05__shrink_0p5__b4fa82ff14 | 0.269891 | 0.807321 | -0.000673 | -0.000177 | 0.954167 | 0.808654 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p22__cap_3em05__shrink_0p5__528a42e8e7 | 0.269891 | 0.807321 | -0.000673 | -0.000177 | 0.954167 | 0.808654 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p04__cap_6em05__shrink_0p8__f8a7dd3e14 | 0.269892 | 0.807319 | -0.000673 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p08__cap_3em05__shrink_0p5__61339fba64 | 0.269892 | 0.807321 | -0.000673 | -0.000177 | 0.954167 | 0.808654 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p04__cap_3em05__shrink_0p5__7c9355e66c | 0.269892 | 0.807321 | -0.000673 | -0.000177 | 0.954167 | 0.808654 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p22__cap_3em05__shrink_0p8__0ce9d408d9 | 0.269892 | 0.807323 | -0.000673 | -0.000176 | 0.954167 | 0.788141 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p14__cap_3em05__shrink_0p8__31afdb0dc2 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.788141 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p15__s_0p08__cap_6em05__shrink_0p8__8e087348a1 | 0.269892 | 0.807319 | -0.000672 | -0.000180 | 0.954167 | 0.703846 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p08__cap_3em05__shrink_0p8__cc2aaa9ed2 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.788141 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p04__cap_3em05__shrink_0p8__40bc5def3c | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.788141 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p1__ps_0p04__cap_3em05__610260dfd2 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p1__ps_0p08__cap_3em05__09e74c938b | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p1__ps_0p14__cap_3em05__3dbdf6a452 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p1__ps_0p04__cap_3em05__3d0c7e606b | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p1__ps_0p08__cap_3em05__e1f45992ea | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p1__ps_0p14__cap_3em05__fa49cc559e | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p06__ps_0p04__cap_3em05__08cf292fd1 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p06__ps_0p08__cap_3em05__8531d73e91 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p06__ps_0p14__cap_3em05__7d1d5aec80 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p06__ps_0p04__cap_3em05__cca25d5023 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p06__ps_0p08__cap_3em05__335cd727c1 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p06__ps_0p14__cap_3em05__ef5fb9d772 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p03__ps_0p04__cap_3em05__936c8b443c | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p03__ps_0p08__cap_3em05__1f44b2b211 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p03__ps_0p14__cap_3em05__d3288ae964 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p03__ps_0p04__cap_3em05__e32526d332 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p03__ps_0p08__cap_3em05__0a11dd4532 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p03__ps_0p14__cap_3em05__17134388c0 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p14__cap_3em05__shrink_0p8__aaeca50718 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.799038 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p22__cap_3em05__shrink_0p8__0182c77ce4 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.799038 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p08__cap_3em05__shrink_0p8__7b6c31aecc | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.799038 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p1__ps_0p04__cap_3em05__673a63525d | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p1__ps_0p08__cap_3em05__c4183d4c2e | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p1__ps_0p14__cap_3em05__bdece6237e | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p1__ps_0p04__cap_3em05__edee16df5f | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p1__ps_0p08__cap_3em05__8d8b117f23 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p1__ps_0p14__cap_3em05__ba6194bb70 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p04__cap_3em05__shrink_0p8__1171ee109e | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.799038 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p04__cap_6em05__shrink_0p8__c134c5304a | 0.269892 | 0.807319 | -0.000672 | -0.000180 | 0.954167 | 0.685577 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p06__ps_0p04__cap_3em05__7502e51802 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p06__ps_0p08__cap_3em05__8c7902f0e4 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p06__ps_0p14__cap_3em05__af7c0c5f83 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p06__ps_0p04__cap_3em05__2060e22e9c | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p06__ps_0p08__cap_3em05__da8b22940c | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p06__ps_0p14__cap_3em05__c7a86239f1 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p03__ps_0p04__cap_3em05__4f141318e6 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p03__ps_0p08__cap_3em05__40d9c99556 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s1__rs_0p03__ps_0p14__cap_3em05__aee7faef5b | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p03__ps_0p04__cap_3em05__b59b027bf4 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p03__ps_0p08__cap_3em05__b3350418de | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt245_residual_support__resid_ridge_2p0__support_s2__rs_0p03__ps_0p14__cap_3em05__28e9a10300 | 0.269892 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.796474 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p08__cap_6em05__shrink_0p8__eba9e781f9 | 0.269892 | 0.807319 | -0.000672 | -0.000180 | 0.954167 | 0.685577 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p22__cap_6em05__shrink_0p8__025d9041b8 | 0.269892 | 0.807319 | -0.000672 | -0.000180 | 0.954167 | 0.685577 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p14__cap_6em05__shrink_0p8__c37f9720ce | 0.269892 | 0.807319 | -0.000672 | -0.000180 | 0.954167 | 0.685577 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p04__cap_6em05__shrink_0p5__34e30de5c8 | 0.269892 | 0.807317 | -0.000672 | -0.000182 | 0.954167 | 0.696795 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p08__cap_6em05__shrink_0p5__178fd4623d | 0.269892 | 0.807317 | -0.000672 | -0.000182 | 0.954167 | 0.696795 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p22__cap_6em05__shrink_0p5__6f5c853ced | 0.269892 | 0.807317 | -0.000672 | -0.000182 | 0.954167 | 0.696795 | -0.018839 |
| candidate_ppopt243_linear_residual__model_huber_1p35__s_0p14__cap_6em05__shrink_0p5__1003cb79f3 | 0.269892 | 0.807317 | -0.000672 | -0.000182 | 0.954167 | 0.696795 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p22__cap_3em05__shrink_0p5__a2a7ecd423 | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p14__cap_3em05__shrink_0p5__a54b9c493b | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p08__cap_3em05__shrink_0p5__c052545b8d | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p04__cap_3em05__shrink_0p5__42ed4f01d7 | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018839 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p05__cap_5em05__shrink_0p85__f877a6ffab | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.714423 | -0.018839 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p025__cap_5em05__shrink_0p85__6cfb8d9bd8 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.714423 | -0.018839 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p1__cap_5em05__shrink_0p85__56135ce8e5 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.714423 | -0.018839 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p16__cap_5em05__shrink_0p85__ffa52593f4 | 0.269892 | 0.807323 | -0.000672 | -0.000176 | 0.954167 | 0.714423 | -0.018839 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p14__cap_3em05__shrink_0p5__ef330fbfef | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018838 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p22__cap_3em05__shrink_0p5__c0a51354de | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018838 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p08__cap_3em05__shrink_0p5__5ba01d32d4 | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018838 |
| candidate_ppopt243_linear_residual__model_ridge_2p0__s_0p04__cap_3em05__shrink_0p5__af3b2cfe61 | 0.269892 | 0.807321 | -0.000672 | -0.000177 | 0.954167 | 0.794872 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p04__cap_0p0001__57d35dd732 | 0.269892 | 0.807315 | -0.000672 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p08__cap_0p0001__161dd1e84d | 0.269892 | 0.807315 | -0.000672 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p03__ps_0p14__cap_0p0001__7be1777b03 | 0.269892 | 0.807315 | -0.000672 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p04__cap_0p0001__b77d70b154 | 0.269892 | 0.807315 | -0.000672 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p08__cap_0p0001__48d1a8fe4d | 0.269892 | 0.807315 | -0.000672 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p03__ps_0p14__cap_0p0001__aa722de577 | 0.269892 | 0.807315 | -0.000672 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p05__cap_5em05__shrink_0p6__333c1cdf2f | 0.269893 | 0.807322 | -0.000672 | -0.000176 | 0.954167 | 0.714103 | -0.018838 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p025__cap_5em05__shrink_0p6__ef643a2f32 | 0.269893 | 0.807322 | -0.000671 | -0.000176 | 0.954167 | 0.714103 | -0.018838 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p1__cap_5em05__shrink_0p6__a6c4bd9d10 | 0.269893 | 0.807322 | -0.000671 | -0.000176 | 0.954167 | 0.714103 | -0.018838 |
| candidate_ppopt244_tree_residual__model_hist_gbr_70__s_0p16__cap_5em05__shrink_0p6__6806b8638b | 0.269893 | 0.807322 | -0.000671 | -0.000176 | 0.954167 | 0.714103 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p04__cap_0p0001__d4da75bb1b | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p08__cap_0p0001__7a46105614 | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s1__rs_0p06__ps_0p14__cap_0p0001__876c7c52be | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p04__cap_0p0001__3cf5423bbb | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p08__cap_0p0001__71bf6108b8 | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt245_residual_support__resid_huber_1p15__support_s2__rs_0p06__ps_0p14__cap_0p0001__cd8c233f58 | 0.269893 | 0.807315 | -0.000671 | -0.000184 | 0.954167 | 0.691667 | -0.018838 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p22__cap_6em05__shrink_0p8__5168add757 | 0.269893 | 0.807319 | -0.000671 | -0.000180 | 0.954167 | 0.685577 | -0.018838 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p04__cap_6em05__shrink_0p8__23eff6ffd4 | 0.269893 | 0.807319 | -0.000671 | -0.000180 | 0.954167 | 0.685577 | -0.018838 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p14__cap_6em05__shrink_0p8__2a194c6aee | 0.269893 | 0.807319 | -0.000671 | -0.000180 | 0.954167 | 0.685577 | -0.018838 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p08__cap_6em05__shrink_0p8__dfb031c9ae | 0.269893 | 0.807319 | -0.000671 | -0.000180 | 0.954167 | 0.685577 | -0.018838 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p04__cap_6em05__shrink_0p5__870b514fed | 0.269893 | 0.807317 | -0.000671 | -0.000182 | 0.954167 | 0.696795 | -0.018837 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p22__cap_6em05__shrink_0p5__0aa0bc2889 | 0.269894 | 0.807317 | -0.000671 | -0.000182 | 0.954167 | 0.696795 | -0.018837 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p14__cap_6em05__shrink_0p5__a0c97638d3 | 0.269894 | 0.807317 | -0.000671 | -0.000182 | 0.954167 | 0.696795 | -0.018837 |
| candidate_ppopt243_linear_residual__model_huber_1p7__s_0p08__cap_6em05__shrink_0p5__c7904f620c | 0.269894 | 0.807317 | -0.000670 | -0.000182 | 0.954167 | 0.696795 | -0.018837 |
| candidate_ppopt243_linear_residual__model_ridge_0p5__s_0p04__cap_6em05__shrink_0p8__aaf2dc166f | 0.269894 | 0.807320 | -0.000670 | -0.000179 | 0.954167 | 0.673397 | -0.018837 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p03__ps_0p04__cap_6em05__1fc1d26634 | 0.269894 | 0.807319 | -0.000670 | -0.000180 | 0.954167 | 0.684295 | -0.018837 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p03__ps_0p08__cap_6em05__d92fe1ef4f | 0.269894 | 0.807319 | -0.000670 | -0.000180 | 0.954167 | 0.684295 | -0.018837 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s1__rs_0p03__ps_0p14__cap_6em05__5ed1c3aeb0 | 0.269894 | 0.807319 | -0.000670 | -0.000180 | 0.954167 | 0.684295 | -0.018837 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p03__ps_0p04__cap_6em05__1051321d45 | 0.269894 | 0.807319 | -0.000670 | -0.000180 | 0.954167 | 0.684295 | -0.018837 |
| candidate_ppopt245_residual_support__resid_ridge_0p5__support_s2__rs_0p03__ps_0p08__cap_6em05__848cfff084 | 0.269894 | 0.807319 | -0.000670 | -0.000180 | 0.954167 | 0.684295 | -0.018837 |

## 실행 설정
```json
{
  "experiment_id": "PP-OPT241-246",
  "experiment_slug": "PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration",
  "created_at": "2026-06-10T12:54:15",
  "previous_experiment": "experiments/track6/PP-OPT235_240_warm_pp234_significance_audit_and_learned_router",
  "validation_rows": 519,
  "test_rows": 607,
  "candidate_count": 1020,
  "prediction_rows": 1148520,
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
  "pp240_decision": {
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
  "selection_decision": {
    "operational_label": "pp240_mape_reference",
    "operational_candidate": "ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "operational_fixed_test_MAPE": 0.26988910777837405,
    "operational_fixed_test_p95_APE": 0.8073255046591389,
    "operational_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "operational_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "operational_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "operational_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "operational_delta_vs_pp240_operational_MAPE": 0.0,
    "operational_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "operational_avg_pp64_p95_win_rate": 0.7471153846153845,
    "operational_replacement_score": -0.018841600803952974,
    "balanced_label": "candidate_ppopt241_p95_support__src_s3__seg_price_conf__s_0p22__cap_0p0001__shrink_0p5__24d5cb2201",
    "balanced_candidate": "ppopt241_p95_support__src=s3__seg=price_conf__s=0p22__cap=0p0001__shrink=0p5",
    "balanced_fixed_test_MAPE": 0.26988949026577663,
    "balanced_fixed_test_p95_APE": 0.8073255046591389,
    "balanced_delta_vs_pp64_MAPE": -0.0006745516498837256,
    "balanced_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "balanced_delta_vs_pp234_MAPE": -7.302264792841129e-09,
    "balanced_delta_vs_pp234_p95_win_rate": 0.0,
    "balanced_delta_vs_pp240_operational_MAPE": 3.8248740258373104e-07,
    "balanced_avg_pp64_MAPE_win_rate": 0.9538461538461539,
    "balanced_avg_pp64_p95_win_rate": 0.7477564102564102,
    "balanced_replacement_score": -0.01882839780372988,
    "mape_challenger_label": "pp240_mape_reference",
    "mape_challenger_candidate": "ppopt240_mape_challenger_pp234_learned_router__source=ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p00045__shrink_0p5",
    "mape_challenger_fixed_test_MAPE": 0.26988910777837405,
    "mape_challenger_fixed_test_p95_APE": 0.8073255046591389,
    "mape_challenger_delta_vs_pp64_MAPE": -0.0006749341372863094,
    "mape_challenger_delta_vs_pp64_p95_APE": -0.00017334764697096716,
    "mape_challenger_delta_vs_pp234_MAPE": -3.8978966737657217e-07,
    "mape_challenger_delta_vs_pp234_p95_win_rate": -0.0006410256410256387,
    "mape_challenger_delta_vs_pp240_operational_MAPE": 0.0,
    "mape_challenger_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "mape_challenger_avg_pp64_p95_win_rate": 0.7471153846153845,
    "mape_challenger_replacement_score": -0.018841600803952974,
    "p95_recovery_label": "candidate_ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5__ddb3a8ef18",
    "p95_recovery_candidate": "ppopt243_linear_residual__model=huber_1p15__s=0p22__cap=3em05__shrink=0p5",
    "p95_recovery_fixed_test_MAPE": 0.2698902774922426,
    "p95_recovery_fixed_test_p95_APE": 0.8073212838975509,
    "p95_recovery_delta_vs_pp64_MAPE": -0.0006737644234177664,
    "p95_recovery_delta_vs_pp64_p95_APE": -0.00017756840855898126,
    "p95_recovery_delta_vs_pp234_MAPE": 7.799242011663488e-07,
    "p95_recovery_delta_vs_pp234_p95_win_rate": 0.06634615384615405,
    "p95_recovery_delta_vs_pp240_operational_MAPE": 1.169713868542921e-06,
    "p95_recovery_avg_pp64_MAPE_win_rate": 0.9541666666666666,
    "p95_recovery_avg_pp64_p95_win_rate": 0.8141025641025642,
    "p95_recovery_replacement_score": -0.01884043109008443,
    "p95_guarded_label": "pp234_p95_guarded_reference",
    "p95_guarded_candidate": "ppopt234_p95_guarded_pp228_p95_recovery__source=ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p95_regularized_rebuild__source_ppopt210_p95_guar",
    "p95_guarded_fixed_test_MAPE": 0.26994920114208765,
    "p95_guarded_fixed_test_p95_APE": 0.8072545738314347,
    "p95_guarded_delta_vs_pp64_MAPE": -0.0006148407735727113,
    "p95_guarded_delta_vs_pp64_p95_APE": -0.0002442784746751192,
    "p95_guarded_delta_vs_pp234_MAPE": 5.970357404622151e-05,
    "p95_guarded_delta_vs_pp234_p95_win_rate": 0.0038461538461540545,
    "p95_guarded_delta_vs_pp240_operational_MAPE": 6.009336371359808e-05,
    "p95_guarded_avg_pp64_MAPE_win_rate": 0.9509615384615384,
    "p95_guarded_avg_pp64_p95_win_rate": 0.7516025641025642,
    "p95_guarded_replacement_score": -0.01865330231203425,
    "p95_extreme_label": "pp240_p95_extreme_reference",
    "p95_extreme_candidate": "ppopt240_p95_extreme_pp234_learned_router__source=ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_pp222_narrow_balance__source_reference_pp148_p95",
    "p95_extreme_fixed_test_MAPE": 0.27026892590910795,
    "p95_extreme_fixed_test_p95_APE": 0.8059493758221674,
    "p95_extreme_delta_vs_pp64_MAPE": -0.00029511600655240944,
    "p95_extreme_delta_vs_pp64_p95_APE": -0.0015494764839424358,
    "p95_extreme_delta_vs_pp234_MAPE": 0.00037942834106652334,
    "p95_extreme_delta_vs_pp234_p95_win_rate": -0.2467948717948717,
    "p95_extreme_delta_vs_pp240_operational_MAPE": 0.0003798181307338999,
    "p95_extreme_avg_pp64_MAPE_win_rate": 0.5983974358974359,
    "p95_extreme_avg_pp64_p95_win_rate": 0.5009615384615385,
    "p95_extreme_replacement_score": -0.0040792899192624915,
    "operational_protocol_candidate": "ppopt246_operational_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p",
    "balanced_protocol_candidate": "ppopt246_balanced_pp234_p95_constrained__source=ppopt241_p95_support__src_s3__seg_price_conf__s_0p22__cap_0p0001__shrink_0p5",
    "mape_challenger_protocol_candidate": "ppopt246_mape_challenger_pp234_p95_constrained__source=ppopt240_mape_challenger_pp234_learned_router__source_ppopt236_segment_winner__seg_price_conf__minn_15__gain_0p0__cap_0p",
    "p95_recovery_protocol_candidate": "ppopt246_p95_recovery_pp234_p95_constrained__source=ppopt243_linear_residual__model_huber_1p15__s_0p22__cap_3em05__shrink_0p5",
    "p95_guarded_protocol_candidate": "ppopt246_p95_guarded_pp234_p95_constrained__source=ppopt234_p95_guarded_pp228_p95_recovery__source_ppopt228_p95_guarded_pp222_narrow_balance__source_ppopt222_p95_guarded_p",
    "p95_extreme_protocol_candidate": "ppopt246_p95_extreme_pp234_p95_constrained__source=ppopt240_p95_extreme_pp234_learned_router__source_ppopt234_p95_extreme_pp228_p95_recovery__source_ppopt228_p95_extreme_p"
  },
  "selected_p95_support_candidates": [
    "ppopt237_multiclass_router__c=0p6__seed=29__thr=0p32__cap=0p00045__shrink=0p5",
    "ppopt237_multiclass_router__c=0p6__seed=29__thr=0p45__cap=0p00045__shrink=0p5",
    "ppopt237_multiclass_router__c=0p6__seed=17__thr=0p32__cap=0p00045__shrink=0p5",
    "ppopt237_multiclass_router__c=0p6__seed=17__thr=0p45__cap=0p00045__shrink=0p5"
  ],
  "available_tree_models": {
    "lightgbm": true,
    "xgboost": true,
    "catboost": true,
    "hist_gradient_boosting": true
  },
  "items": [
    {
      "item_id": "PP-OPT241",
      "priority": "1",
      "title": "p95 support from learned-router candidates",
      "description": "PP237/PP239 중 p95 APE가 낮았던 후보를 PP234 위에 tiny cap으로만 얹음."
    },
    {
      "item_id": "PP-OPT242",
      "priority": "2",
      "title": "p95 guarded/recovery ultra support",
      "description": "PP234 p95-guarded와 PP216 p95-recovery 이동을 매우 작게 제한 적용."
    },
    {
      "item_id": "PP-OPT243",
      "priority": "3",
      "title": "Huber/Ridge residual regeneration",
      "description": "validation OOF에서 PP234 잔차를 Huber/Ridge로 재학습해 clipped residual correction 적용."
    },
    {
      "item_id": "PP-OPT244",
      "priority": "4",
      "title": "tree residual regeneration",
      "description": "LightGBM/XGBoost/CatBoost/HistGradientBoosting 소형 잔차 모델을 clipped correction으로 적용."
    },
    {
      "item_id": "PP-OPT245",
      "priority": "5",
      "title": "residual plus p95 support ensemble",
      "description": "작은 residual correction과 p95-support 이동을 동시에 적용하되 PP234 기준 cap으로 제한."
    },
    {
      "item_id": "PP-OPT246",
      "priority": "6",
      "title": "final PP234 p95-constrained support decision",
      "description": "PP234 대비 MAPE, repeated p95 win rate, replacement score 제약을 만족하는 후보만 선택."
    }
  ],
  "router_formula": {
    "base": "PP234 balanced log price",
    "p95_support": "PP234 + clip((p95-support log price - PP234) * segment_weight * strength, tiny row cap)",
    "residual_regeneration": "PP234 + clip(crossfit residual model prediction * strength, row cap)",
    "ensemble": "PP234 + clipped residual correction + clipped p95-support movement",
    "selection_goal": "Keep PP234 repeated p95 win-rate and replacement score while reducing fixed-test MAPE or p95 APE."
  }
}
```