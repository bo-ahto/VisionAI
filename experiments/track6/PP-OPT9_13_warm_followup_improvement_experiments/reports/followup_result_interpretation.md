# PP-OPT9~13 Warm 후속 개선 실험 결과

- 작성일: 2026-06-09 11:12
- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건
- 기준 후보: PP-OPT7 운영 후보
- 전체 후보 수: 274

## 현재 운영 후보 성능
| eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 607 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.779242 | 0.883031 |
| validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | 0.324133 | 0.782274 | 0.911368 |

## 후속 실험별 최선 후보
| priority | title | tested_candidates | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | stable_validation_pass_vs_incumbent | operational_pass_vs_incumbent | best_family | best_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 게이트형 하이브리드 보정 | 54 | 0.271129 | 0.806282 | -0.000266 | -0.001848 | True | True | gated_hybrid | ppopt9_hybrid__artist=cat_price_band__tail=xgb_tail__as=0p3__ts=0p75 |
| 3 | p95 큰 오차 위험 라우터 | 32 | 0.271291 | 0.806545 | -0.000104 | -0.001585 | True | True | tail_risk_router | ppopt11_tail_router__src=xgb_tail__gate=lgbm__s=0p75 |
| 2 | 작가 메타 CatBoost 보정 안전 구간 분류 | 24 | 0.271388 | 0.808130 | -0.000007 | 0.000000 | True | True | artist_safety_gate | ppopt10_artist_safety__src=artist_mape__gate=logistic__s=0p8 |
| 4 | 다목적 cap/strength 탐색 | 108 | 0.270774 | 0.807553 | -0.000620 | -0.000577 | False | False | multiobjective_cap_strength | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p45__cap=0p022 |
| 5 | 작품 피쳐 shrinkage 보정 | 54 | 0.272204 | 0.807730 | 0.000809 | -0.000400 | False | False | artwork_shrinkage | ppopt13_artwork_shrinkage__group=medium_area__prior=8p0__s=0p35__cap=0p01 |

## 운영 후보 대체 가능 후보
| item_id | candidate | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | incumbent_MAPE_improve_rate | incumbent_p95_not_worse_rate | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT9 | ppopt9_hybrid__artist=cat_price_band__tail=xgb_tail__as=0p3__ts=0p75 | gated_hybrid | 0.271129 | 0.806282 | -0.000266 | -0.001848 | 0.966667 | 0.529167 | -0.000587 |
| PP-OPT9 | ppopt9_hybrid__artist=cat_price_band__tail=xgb_tail__as=0p3__ts=0p55 | gated_hybrid | 0.271150 | 0.806652 | -0.000245 | -0.001478 | 0.987500 | 0.520833 | -0.000545 |
| PP-OPT9 | ppopt9_hybrid__artist=cat_price_band__tail=xgb_tail__as=0p3__ts=0p35 | gated_hybrid | 0.271179 | 0.807210 | -0.000216 | -0.000920 | 0.991667 | 0.520833 | -0.000518 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail__gate=lgbm__s=0p75 | tail_risk_router | 0.271291 | 0.806545 | -0.000104 | -0.001585 | 0.862500 | 0.679167 | -0.000214 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail__gate=lgbm__s=1p0 | tail_risk_router | 0.271303 | 0.806513 | -0.000092 | -0.001617 | 0.837500 | 0.679167 | -0.000204 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail__gate=lgbm__s=0p55 | tail_risk_router | 0.271306 | 0.806713 | -0.000089 | -0.001417 | 0.929167 | 0.679167 | -0.000196 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail__gate=lgbm__s=0p35 | tail_risk_router | 0.271334 | 0.807230 | -0.000061 | -0.000900 | 0.941667 | 0.679167 | -0.000174 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail_guard_mean__gate=lgbm__s=0p35 | tail_risk_router | 0.271381 | 0.807600 | -0.000014 | -0.000529 | 0.704167 | 0.445833 | -0.000073 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail_guard_mean__gate=lgbm__s=0p55 | tail_risk_router | 0.271374 | 0.807297 | -0.000020 | -0.000833 | 0.704167 | 0.416667 | -0.000059 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_mape__gate=logistic__s=0p8 | artist_safety_gate | 0.271388 | 0.808130 | -0.000007 | 0.000000 | 0.833333 | 0.983333 | -0.000034 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_mape__gate=logistic__s=0p65 | artist_safety_gate | 0.271390 | 0.808130 | -0.000005 | 0.000000 | 0.833333 | 0.983333 | -0.000023 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_stable__gate=logistic__s=0p8 | artist_safety_gate | 0.271378 | 0.808130 | -0.000017 | 0.000000 | 0.937500 | 0.991667 | -0.000021 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_mape__gate=logistic__s=0p5 | artist_safety_gate | 0.271391 | 0.808130 | -0.000004 | 0.000000 | 0.833333 | 0.983333 | -0.000019 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_stable__gate=logistic__s=0p65 | artist_safety_gate | 0.271381 | 0.808130 | -0.000014 | 0.000000 | 0.937500 | 0.991667 | -0.000018 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_stable__gate=logistic__s=0p5 | artist_safety_gate | 0.271384 | 0.808130 | -0.000010 | 0.000000 | 0.937500 | 0.991667 | -0.000016 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_mape__gate=logistic__s=0p35 | artist_safety_gate | 0.271392 | 0.808130 | -0.000003 | 0.000000 | 0.833333 | 0.983333 | -0.000016 |
| PP-OPT10 | ppopt10_artist_safety__src=artist_stable__gate=logistic__s=0p35 | artist_safety_gate | 0.271388 | 0.808130 | -0.000007 | 0.000000 | 0.937500 | 0.991667 | -0.000014 |
| PP-OPT10 | ppopt10_artist_safety__src=cat_price_band__gate=logistic__s=0p8 | artist_safety_gate | 0.271388 | 0.808130 | -0.000007 | 0.000000 | 0.779167 | 0.991667 | -0.000004 |
| PP-OPT10 | ppopt10_artist_safety__src=cat_price_band__gate=logistic__s=0p65 | artist_safety_gate | 0.271389 | 0.808130 | -0.000006 | 0.000000 | 0.779167 | 0.991667 | -0.000003 |
| PP-OPT10 | ppopt10_artist_safety__src=cat_price_band__gate=logistic__s=0p5 | artist_safety_gate | 0.271391 | 0.808130 | -0.000004 | 0.000000 | 0.779167 | 0.991667 | -0.000002 |
| PP-OPT10 | ppopt10_artist_safety__src=cat_price_band__gate=logistic__s=0p35 | artist_safety_gate | 0.271392 | 0.808130 | -0.000003 | 0.000000 | 0.779167 | 0.991667 | -0.000002 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail_guard_mean__gate=lgbm__s=0p75 | tail_risk_router | 0.271373 | 0.806993 | -0.000022 | -0.001137 | 0.683333 | 0.416667 | 0.000008 |
| PP-OPT9 | ppopt9_hybrid__artist=cat_price_band__tail=tail_guard__as=0p3__ts=0p35 | gated_hybrid | 0.271281 | 0.808011 | -0.000114 | -0.000119 | 0.750000 | 0.320833 | 0.000039 |
| PP-OPT11 | ppopt11_tail_router__src=xgb_tail_guard_mean__gate=lgbm__s=1p0 | tail_risk_router | 0.271372 | 0.806612 | -0.000023 | -0.001518 | 0.608333 | 0.416667 | 0.000096 |

## Test에서 MAPE와 p95를 동시에 개선한 후보
| item_id | candidate | family | test_MAPE | test_p95_APE | test_delta_vs_incumbent_MAPE | test_delta_vs_incumbent_p95_APE | recommendation_score_vs_incumbent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p45__cap=0p022 | multiobjective_cap_strength | 0.270774 | 0.807553 | -0.000620 | -0.000577 | -0.001510 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p45__cap=0p018 | multiobjective_cap_strength | 0.270822 | 0.807553 | -0.000573 | -0.000577 | -0.001509 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p45__cap=0p014 | multiobjective_cap_strength | 0.270878 | 0.807553 | -0.000516 | -0.000577 | -0.001496 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p3__cap=0p014 | multiobjective_cap_strength | 0.270868 | 0.807890 | -0.000526 | -0.000240 | -0.001437 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p3__cap=0p018 | multiobjective_cap_strength | 0.270814 | 0.807890 | -0.000581 | -0.000240 | -0.001430 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p0__tw=0p3__cap=0p022 | multiobjective_cap_strength | 0.270778 | 0.807890 | -0.000617 | -0.000240 | -0.001425 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_stable__tail=xgb_tail__as=0p6__ts=0p75 | gated_hybrid | 0.270951 | 0.806373 | -0.000444 | -0.001757 | -0.001389 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p45__cap=0p022 | multiobjective_cap_strength | 0.270840 | 0.807433 | -0.000554 | -0.000697 | -0.001368 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p45__cap=0p018 | multiobjective_cap_strength | 0.270878 | 0.807433 | -0.000517 | -0.000697 | -0.001364 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_stable__tail=xgb_tail__as=0p6__ts=0p55 | gated_hybrid | 0.270954 | 0.806885 | -0.000441 | -0.001245 | -0.001358 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p45__cap=0p014 | multiobjective_cap_strength | 0.270929 | 0.807433 | -0.000466 | -0.000697 | -0.001341 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p3__cap=0p014 | multiobjective_cap_strength | 0.270919 | 0.807770 | -0.000475 | -0.000360 | -0.001332 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p3__cap=0p018 | multiobjective_cap_strength | 0.270872 | 0.807770 | -0.000523 | -0.000360 | -0.001331 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p3__cap=0p022 | multiobjective_cap_strength | 0.270850 | 0.807770 | -0.000544 | -0.000360 | -0.001331 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_stable__tail=xgb_tail__as=0p6__ts=0p35 | gated_hybrid | 0.270969 | 0.807442 | -0.000426 | -0.000688 | -0.001316 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p2__tw=0p45__cap=0p022 | multiobjective_cap_strength | 0.270690 | 0.807513 | -0.000705 | -0.000617 | -0.001310 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p2__tw=0p45__cap=0p018 | multiobjective_cap_strength | 0.270743 | 0.807513 | -0.000652 | -0.000617 | -0.001305 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p15__cap=0p014 | multiobjective_cap_strength | 0.270916 | 0.808107 | -0.000479 | -0.000023 | -0.001303 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p15__cap=0p018 | multiobjective_cap_strength | 0.270882 | 0.808107 | -0.000513 | -0.000023 | -0.001298 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p0__tw=0p15__cap=0p022 | multiobjective_cap_strength | 0.270873 | 0.808107 | -0.000522 | -0.000023 | -0.001298 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p35__cw=0p2__tw=0p45__cap=0p014 | multiobjective_cap_strength | 0.270801 | 0.807513 | -0.000594 | -0.000617 | -0.001289 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p2__tw=0p45__cap=0p018 | multiobjective_cap_strength | 0.270693 | 0.807632 | -0.000702 | -0.000498 | -0.001265 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p2__tw=0p45__cap=0p022 | multiobjective_cap_strength | 0.270634 | 0.807632 | -0.000760 | -0.000498 | -0.001263 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_stable__tail=xgb_tail__as=0p45__ts=0p75 | gated_hybrid | 0.271027 | 0.806341 | -0.000368 | -0.001789 | -0.001260 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p2__tw=0p45__cap=0p014 | multiobjective_cap_strength | 0.270758 | 0.807632 | -0.000637 | -0.000498 | -0.001248 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_mape__tail=xgb_tail__as=0p6__ts=0p75 | gated_hybrid | 0.270544 | 0.806739 | -0.000851 | -0.001391 | -0.001248 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_mape__tail=xgb_tail__as=0p6__ts=0p55 | gated_hybrid | 0.270529 | 0.807297 | -0.000866 | -0.000833 | -0.001243 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_mape__tail=xgb_tail__as=0p6__ts=0p35 | gated_hybrid | 0.270530 | 0.807854 | -0.000864 | -0.000276 | -0.001216 |
| PP-OPT12 | ppopt12_multiobjective_grid__aw=0p45__cw=0p35__tw=0p45__cap=0p018 | multiobjective_cap_strength | 0.270599 | 0.807692 | -0.000796 | -0.000438 | -0.001198 |
| PP-OPT9 | ppopt9_hybrid__artist=artist_stable__tail=xgb_tail__as=0p45__ts=0p55 | gated_hybrid | 0.271036 | 0.806814 | -0.000359 | -0.001316 | -0.001197 |

## 해석
- 최우선 후보는 `ppopt9_hybrid__artist=cat_price_band__tail=xgb_tail__as=0p3__ts=0p75`이다.
- 이 후보의 fixed test MAPE 변화는 `-0.000266`, p95 변화는 `-0.001848`이다.
- 작가 보정 안전 라벨 양성률은 validation 기준 `0.355`이다.
- tail-risk 라벨 양성률은 validation 기준 `0.100`이다.

## 사용한 PP-OPT8 구성 요소
```json
{
  "artist_mape": "existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p03__capprof=fixed__s=1p15__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=1p0__totalcap=0p04",
  "artist_stable": "existing_opt5__combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=fixed__s=1p15__artist=am_h_birth_gen_total_works_gn_a01_c03_s075__cw=0p8__aw=0p75__totalcap=0p025",
  "cat_price_band": "catboost_price_band__cap_strength",
  "qwidth_mild": "qwidth_strength__continuous_mild",
  "qwidth_strict": "qwidth_strength__continuous_strict",
  "xgb_tail": "gap_routing__xgb_tail_else_incumbent__existing_opt5__xgb_xgboost_low_only_diagnostic_cap0p05__rout",
  "tail_guard": "tail_guard__logistic",
  "lightgbm_tail_guard": "lightgbm_tail_guard__classifier",
  "cat_lgb_equal": "correction_ensemble__cat_lgb_equal"
}
```