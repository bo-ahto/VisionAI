# PP-OPT71~75 Warm PP70 안정성 검증 결과

- 작성일: 2026-06-09 12:59
- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건
- 검증 방식: 후보 추가 튜닝 없이 PP65~70 산출 후보를 반복 holdout/bootstrap으로 비교
- 결론: PP64를 운영 기준으로 유지하고 PP70은 보조 후보로 두는 것이 더 안전하다.
- 근거: PP70의 fixed test 개선폭이 매우 작거나 반복 검증 승률이 충분히 우세하지 않다. PP70 vs PP64 fixed test delta: MAPE -0.000003, p95 -0.000009. 반복 검증 평균 승률: MAPE 0.787, p95 0.398, all3 0.054.

## 후보 라벨
| label | candidate |
| --- | --- |
| hcoef_stable_source | hcoef_stable |
| incumbent_pp7 | incumbent_operational_pp_opt7 |
| pp20_p95_reference | previous_challenger_pp20 |
| pp48_stability_reference | reference_pp48_score |
| pp52_quantile_reference | reference_pp52_challenger |
| pp58_mape_reference | reference_pp58_challenger |
| pp64_current_best | reference_pp64_current_best |
| pp70_refinement_candidate | ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78 |
| pp67_best_mape_non_operational | ppopt67_quantile_micro__guard=risk_discount__s=0p1__cap=0p014 |
| pp_opt65_best | ppopt65_local_threshold__helper=pp48_score__base=0p4__vh=0p04__lowconf=0p02__width=0p48__s=0p76 |
| pp_opt66_best | ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p44 |
| pp_opt68_best | ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=1p0 |
| pp_opt69_best | ppopt69_dynamic_blend__low=pp52__high=pp48_score__lows=0p0__highs=0p32 |

## 전체 후보 안정성 순위
| candidate_label | fixed_test_MAPE | fixed_test_p95_APE | fixed_test_delta_vs_pp64_MAPE | fixed_test_delta_vs_pp64_p95_APE | avg_delta_vs_pp64_MAPE | avg_delta_vs_pp64_p95_APE | avg_pp64_MAPE_win_rate | avg_pp64_p95_win_rate | avg_pp64_all3_win_rate | avg_delta_vs_incumbent_MAPE | avg_delta_vs_incumbent_p95_APE | avg_incumbent_MAPE_win_rate | avg_incumbent_p95_win_rate | replacement_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp_opt68_best | 0.270562 | 0.807491 | -0.000002 | -0.000007 | -0.000001 | -0.000003 | 0.833333 | 0.415064 | 0.052564 | -0.000750 | -0.001949 | 0.997756 | 0.535256 | -0.013336 |
| pp67_best_mape_non_operational | 0.270518 | 0.807499 | -0.000046 | 0.000000 | -0.000073 | -0.000234 | 0.819231 | 0.058654 | 0.005449 | -0.000822 | -0.002180 | 0.987500 | 0.522115 | -0.012815 |
| pp70_refinement_candidate | 0.270561 | 0.807490 | -0.000003 | -0.000009 | -0.000001 | -0.000001 | 0.786859 | 0.398077 | 0.054167 | -0.000750 | -0.001946 | 0.997756 | 0.533974 | -0.011477 |
| pp_opt66_best | 0.270577 | 0.807512 | 0.000013 | 0.000014 | 0.000007 | -0.000030 | 0.398718 | 0.142308 | 0.002885 | -0.000742 | -0.001976 | 0.997115 | 0.534295 | 0.004077 |
| pp48_stability_reference | 0.270816 | 0.807385 | 0.000252 | -0.000113 | 0.000116 | -0.000387 | 0.405449 | 0.722756 | 0.204487 | -0.000632 | -0.002332 | 0.954487 | 0.835577 | 0.004092 |
| pp_opt69_best | 0.270571 | 0.807509 | 0.000007 | 0.000011 | 0.000004 | -0.000016 | 0.326282 | 0.181731 | 0.008333 | -0.000744 | -0.001961 | 0.997115 | 0.536538 | 0.006965 |
| pp58_mape_reference | 0.270572 | 0.807811 | 0.000008 | 0.000312 | 0.000014 | 0.000109 | 0.250321 | 0.158333 | 0.013462 | -0.000734 | -0.001837 | 0.997756 | 0.535577 | 0.010259 |
| pp52_quantile_reference | 0.270598 | 0.807660 | 0.000034 | 0.000161 | 0.000024 | 0.000132 | 0.219872 | 0.152564 | 0.011218 | -0.000724 | -0.001813 | 0.997436 | 0.529487 | 0.011411 |
| pp_opt65_best | 0.270586 | 0.807613 | 0.000022 | 0.000114 | 0.000019 | 0.000110 | 0.188782 | 0.152885 | 0.008013 | -0.000729 | -0.001836 | 0.997436 | 0.530769 | 0.012598 |
| pp64_current_best | 0.270564 | 0.807499 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | -0.000748 | -0.001946 | 0.997756 | 0.535577 | 0.020000 |
| pp20_p95_reference | 0.271182 | 0.806472 | 0.000618 | -0.001026 | 0.000535 | 0.000973 | 0.005769 | 0.461538 | 0.001603 | -0.000214 | -0.000973 | 0.964103 | 0.592949 | 0.020995 |
| incumbent_pp7 | 0.271395 | 0.808130 | 0.000831 | 0.000631 | 0.000748 | 0.001946 | 0.002244 | 0.450641 | 0.000641 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.022238 |
| hcoef_stable_source | 0.272989 | 0.806366 | 0.002425 | -0.001133 | 0.002013 | 0.005297 | 0.002244 | 0.403526 | 0.000641 | 0.001265 | 0.003351 | 0.002564 | 0.400321 | 0.025195 |

## fixed validation/test metric
| candidate_label | eval_split | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_vs_incumbent_MAPE | delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp67_best_mape_non_operational | test | 607 | 0.139573 | 0.270518 | 0.807499 | 0.397976 | -0.000877 | -0.000631 |
| pp70_refinement_candidate | test | 607 | 0.137878 | 0.270561 | 0.807490 | 0.397991 | -0.000834 | -0.000640 |
| pp_opt68_best | test | 607 | 0.137878 | 0.270562 | 0.807491 | 0.397991 | -0.000833 | -0.000639 |
| pp64_current_best | test | 607 | 0.137878 | 0.270564 | 0.807499 | 0.397991 | -0.000831 | -0.000631 |
| pp_opt69_best | test | 607 | 0.137878 | 0.270571 | 0.807509 | 0.397997 | -0.000824 | -0.000621 |
| pp58_mape_reference | test | 607 | 0.137878 | 0.270572 | 0.807811 | 0.397997 | -0.000823 | -0.000319 |
| pp_opt66_best | test | 607 | 0.137878 | 0.270577 | 0.807512 | 0.397999 | -0.000818 | -0.000618 |
| pp_opt65_best | test | 607 | 0.137878 | 0.270586 | 0.807613 | 0.397988 | -0.000809 | -0.000517 |
| pp52_quantile_reference | test | 607 | 0.137878 | 0.270598 | 0.807660 | 0.397987 | -0.000797 | -0.000470 |
| pp48_stability_reference | test | 607 | 0.136800 | 0.270816 | 0.807385 | 0.398121 | -0.000579 | -0.000745 |
| pp20_p95_reference | test | 607 | 0.136835 | 0.271182 | 0.806472 | 0.398134 | -0.000213 | -0.001658 |
| incumbent_pp7 | test | 607 | 0.136893 | 0.271395 | 0.808130 | 0.398341 | 0.000000 | 0.000000 |
| hcoef_stable_source | test | 607 | 0.138803 | 0.272989 | 0.806366 | 0.398822 | 0.001594 | -0.001764 |
| pp48_stability_reference | validation_oof | 519 | 0.122610 | 0.206179 | 0.636376 | 0.323684 | -0.000844 | -0.000219 |
| pp67_best_mape_non_operational | validation_oof | 519 | 0.123934 | 0.206185 | 0.637922 | 0.323772 | -0.000838 | 0.001327 |
| pp_opt66_best | validation_oof | 519 | 0.122635 | 0.206278 | 0.637922 | 0.323770 | -0.000745 | 0.001327 |
| pp_opt68_best | validation_oof | 519 | 0.122635 | 0.206280 | 0.637897 | 0.323780 | -0.000743 | 0.001302 |
| pp70_refinement_candidate | validation_oof | 519 | 0.122635 | 0.206280 | 0.637897 | 0.323781 | -0.000743 | 0.001302 |
| pp_opt69_best | validation_oof | 519 | 0.122635 | 0.206281 | 0.637922 | 0.323778 | -0.000742 | 0.001327 |
| pp64_current_best | validation_oof | 519 | 0.122635 | 0.206281 | 0.637922 | 0.323780 | -0.000742 | 0.001327 |
| pp52_quantile_reference | validation_oof | 519 | 0.122430 | 0.206301 | 0.638550 | 0.323793 | -0.000722 | 0.001955 |
| pp_opt65_best | validation_oof | 519 | 0.122635 | 0.206303 | 0.638537 | 0.323790 | -0.000720 | 0.001943 |
| pp58_mape_reference | validation_oof | 519 | 0.122635 | 0.206304 | 0.638224 | 0.323798 | -0.000719 | 0.001629 |
| pp20_p95_reference | validation_oof | 519 | 0.125408 | 0.206777 | 0.638367 | 0.324048 | -0.000246 | 0.001773 |
| incumbent_pp7 | validation_oof | 519 | 0.125923 | 0.207023 | 0.636595 | 0.324133 | 0.000000 | 0.000000 |
| hcoef_stable_source | validation_oof | 519 | 0.125993 | 0.208206 | 0.647948 | 0.325185 | 0.001183 | 0.011353 |

## PP70 시나리오별 PP64 대비 안정성
| candidate_label | eval_split | scenario | repeats | mean_delta_vs_pp64_MAPE | mean_delta_vs_pp64_p95_APE | pp64_MAPE_win_rate | pp64_p95_win_rate | pp64_all3_win_rate | mean_delta_vs_incumbent_MAPE | mean_delta_vs_incumbent_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pp70_refinement_candidate | test | artist_group_holdout | 260 | -0.000003 | -0.000004 | 0.984615 | 0.326923 | 0.119231 | -0.000834 | -0.004679 |
| pp70_refinement_candidate | test | confidence_stratified_rows | 260 | -0.000003 | -0.000003 | 1.000000 | 0.442308 | 0.107692 | -0.000834 | -0.003421 |
| pp70_refinement_candidate | test | full_split | 1 | -0.000003 | -0.000009 | 1.000000 | 1.000000 | 0.000000 | -0.000834 | -0.000640 |
| pp70_refinement_candidate | test | price_band_stratified_rows | 260 | -0.000003 | -0.000003 | 0.980769 | 0.376923 | 0.115385 | -0.000835 | -0.004186 |
| pp70_refinement_candidate | test | risk_focus_bootstrap | 260 | -0.000002 | -0.000018 | 0.823077 | 0.161538 | 0.000000 | -0.000591 | -0.002317 |
| pp70_refinement_candidate | test | row_bootstrap | 260 | -0.000003 | -0.000012 | 0.876923 | 0.346154 | 0.073077 | -0.000809 | -0.005854 |
| pp70_refinement_candidate | validation_oof | artist_group_holdout | 260 | -0.000000 | 0.000002 | 0.611538 | 0.280769 | 0.069231 | -0.000753 | -0.001061 |
| pp70_refinement_candidate | validation_oof | confidence_stratified_rows | 260 | -0.000001 | 0.000003 | 0.688462 | 0.288462 | 0.076923 | -0.000741 | -0.000621 |
| pp70_refinement_candidate | validation_oof | full_split | 1 | -0.000001 | -0.000025 | 1.000000 | 1.000000 | 0.000000 | -0.000743 | 0.001302 |
| pp70_refinement_candidate | validation_oof | price_band_stratified_rows | 260 | -0.000001 | 0.000000 | 0.665385 | 0.319231 | 0.046154 | -0.000737 | -0.000599 |
| pp70_refinement_candidate | validation_oof | risk_focus_bootstrap | 260 | 0.000003 | 0.000048 | 0.257692 | 0.000000 | 0.000000 | -0.000531 | -0.000166 |
| pp70_refinement_candidate | validation_oof | row_bootstrap | 260 | -0.000000 | 0.000012 | 0.553846 | 0.234615 | 0.042308 | -0.000753 | -0.001114 |

## 해석
- PP70은 fixed test에서 PP64보다 MAPE와 p95가 모두 낮지만 개선폭은 1e-5 미만이다.
- 반복 검증에서 PP64 대비 승률이 압도적이지 않으면, PP70은 구조적 개선이라기보다 PP64의 미세 튜닝으로 해석해야 한다.
- p95를 더 크게 낮추려면 PP20/PP48 계열 안정 후보를 위험 row에만 쓰는 tail 라우팅을 다시 별도 탐색해야 한다.

## 실행 설정
```json
{
  "experiment_id": "PP-OPT71-75",
  "experiment_slug": "PP-OPT71_75_warm_pp70_stability_validation",
  "created_at": "2026-06-09T12:59:58",
  "seed": 20260609,
  "repeats_per_resample_scenario": 260,
  "sample_fraction": 0.72,
  "selected_candidates": {
    "hcoef_stable_source": "hcoef_stable",
    "incumbent_pp7": "incumbent_operational_pp_opt7",
    "pp20_p95_reference": "previous_challenger_pp20",
    "pp48_stability_reference": "reference_pp48_score",
    "pp52_quantile_reference": "reference_pp52_challenger",
    "pp58_mape_reference": "reference_pp58_challenger",
    "pp64_current_best": "reference_pp64_current_best",
    "pp70_refinement_candidate": "ppopt70_pp64_refinement_challenger__source=ppopt68_shrinkage__global_1p04__risk_0p7__vh_0p82__lowconf_0p78",
    "pp67_best_mape_non_operational": "ppopt67_quantile_micro__guard=risk_discount__s=0p1__cap=0p014",
    "pp_opt65_best": "ppopt65_local_threshold__helper=pp48_score__base=0p4__vh=0p04__lowconf=0p02__width=0p48__s=0p76",
    "pp_opt66_best": "ppopt66_tail_guard__helper=pp48_score__score=combined__thr=0p66__width=0p22__s=0p44",
    "pp_opt68_best": "ppopt68_shrinkage__global=1p04__risk=0p7__vh=0p82__lowconf=1p0",
    "pp_opt69_best": "ppopt69_dynamic_blend__low=pp52__high=pp48_score__lows=0p0__highs=0p32"
  },
  "candidate_count": 13,
  "validation_rows": 519,
  "test_rows": 607,
  "decision": {
    "verdict": "PP64를 운영 기준으로 유지하고 PP70은 보조 후보로 두는 것이 더 안전하다.",
    "reason": "PP70의 fixed test 개선폭이 매우 작거나 반복 검증 승률이 충분히 우세하지 않다. PP70 vs PP64 fixed test delta: MAPE -0.000003, p95 -0.000009. 반복 검증 평균 승률: MAPE 0.787, p95 0.398, all3 0.054."
  },
  "items": [
    {
      "item_id": "PP-OPT71",
      "priority": "1",
      "title": "fixed validation/test reference comparison",
      "description": "기존 fixed validation/test 전체 row에서 주요 후보를 다시 비교한다."
    },
    {
      "item_id": "PP-OPT72",
      "priority": "2",
      "title": "validation repeated holdout stability",
      "description": "validation OOF에서 confidence, price, artist, risk 기반 반복 부분표본 승률을 계산한다."
    },
    {
      "item_id": "PP-OPT73",
      "priority": "3",
      "title": "test bootstrap stress stability",
      "description": "fixed test를 재학습 없이 bootstrap/stratified resample하여 후보 간 승률을 계산한다."
    },
    {
      "item_id": "PP-OPT74",
      "priority": "4",
      "title": "PP70 vs PP64 replacement decision",
      "description": "PP70의 미세 개선이 PP64 교체 근거로 충분한지 판단한다."
    },
    {
      "item_id": "PP-OPT75",
      "priority": "5",
      "title": "next experiment recommendation",
      "description": "검증 결과를 바탕으로 다음 실험 방향을 정리한다."
    }
  ],
  "sources": {
    "pp65_config": "experiments/track6/PP-OPT65_70_warm_pp64_refinement_experiments/artifacts/run_config.json",
    "pp65_predictions": "experiments/track6/PP-OPT65_70_warm_pp64_refinement_experiments/outputs/candidate_predictions.csv",
    "pp65_aggregate": "experiments/track6/PP-OPT65_70_warm_pp64_refinement_experiments/outputs/aggregate_candidate_stability.csv",
    "pp65_item_summary": "experiments/track6/PP-OPT65_70_warm_pp64_refinement_experiments/outputs/experiment_item_summary.csv",
    "pp65_helper": "scripts/track6/run_pp_opt65_70_warm_pp64_refinement_experiments.py"
  }
}
```