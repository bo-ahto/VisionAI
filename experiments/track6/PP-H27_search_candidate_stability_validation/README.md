# PP-H27 H23/H26 검색 보정 후보 안정성 검증

## 목적

- PP-H23 전시 문맥 보정과 PP-H26 위험 구간 fallback 후보가 test 단일 결과에서만 좋아진 것인지 확인한다.
- row bootstrap은 작품 단위 안정성을 확인한다.
- artist bootstrap은 특정 작가 구성에 의존하는지 확인한다.
- delta는 `기준 모델 점수 - 후보 점수`다. 오차 지표에서는 양수일수록 후보가 좋다.

## 실행 설정

| 항목 | 값 |
| --- | --- |
| experiment_id | PP-H27 |
| title | H23/H26 검색 보정 후보 안정성 검증 |
| started_at | 2026-06-03T16:08:44 |
| finished_at | 2026-06-03T16:08:52 |
| predictions | experiments/track6/PP-H20_H26_search_feature_expansion/outputs/candidate_predictions.csv |
| bootstrap_iterations | 800 |
| seed | 20260603 |
| candidates | h23_gallery_museum_median_cap0.1, h23_gallery_museum_median_cap0.2, h23_exhibition_median_cap0.1, h23_exhibition_median_cap0.2, h23_news_median_cap0.1, h23_news_median_cap0.2, h23_social_blog_median_cap0.1, h23_social_blog_median_cap0.2, h26_risk_qwidth_action_median_cap0.1, h26_risk_qwidth_action_median_cap0.2, h26_confidence_only_lower_q10_blend0.5 |

## Test 전체 점수

| experiment_id | family | candidate | split | slice | description | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H27 | PP-H23 | h23_news_median_cap0.2 | test | overall | 뉴스 소스군 보정 cap0.2 | 3099 | 0.425322 | 0.95342 | 3.15419 | 0.833754 | 0.36657 | 0.579864 |
| PP-H27 | PP-H23 | h23_news_median_cap0.1 | test | overall | 뉴스 소스군 보정 cap0.1 | 3099 | 0.428314 | 0.989039 | 3.21959 | 0.843963 | 0.349468 | 0.576638 |
| PP-H27 | PP-H23 | h23_gallery_museum_median_cap0.2 | test | overall | 갤러리/미술관 소스군 보정 cap0.2 | 3099 | 0.431277 | 0.928508 | 3.13899 | 0.837833 | 0.359793 | 0.570184 |
| PP-H27 | PP-H23 | h23_social_blog_median_cap0.1 | test | overall | 블로그/소셜 소스군 보정 cap0.1 | 3099 | 0.432786 | 0.976556 | 3.21959 | 0.847065 | 0.338174 | 0.575024 |
| PP-H27 | PP-H23 | h23_social_blog_median_cap0.2 | test | overall | 블로그/소셜 소스군 보정 cap0.2 | 3099 | 0.434409 | 0.927026 | 3.13899 | 0.840021 | 0.339142 | 0.576638 |
| PP-H27 | PP-H23 | h23_gallery_museum_median_cap0.1 | test | overall | 갤러리/미술관 소스군 보정 cap0.1 | 3099 | 0.434833 | 0.977021 | 3.21959 | 0.84598 | 0.34979 | 0.570184 |
| PP-H27 | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | test | overall | 위험 action x q-width 보정 cap0.1 | 3099 | 0.435175 | 1.00941 | 3.18215 | 0.857119 | 0.32817 | 0.565021 |
| PP-H27 | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | test | overall | 위험 action x q-width 보정 cap0.2 | 3099 | 0.435175 | 1.00941 | 3.18215 | 0.857119 | 0.32817 | 0.565021 |
| PP-H27 | baseline | pp_y2_base | test | overall | PP-Y2 기준 예측 | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H27 | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | test | overall | 위험 action q10 방향 블렌딩 0.5 | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 | 0.324944 | 0.560181 |
| PP-H27 | PP-H23 | h23_exhibition_median_cap0.1 | test | overall | 전시 문맥 소스군 보정 cap0.1 | 3099 | 0.445202 | 1.07556 | 2.93942 | 0.873313 | 0.337851 | 0.558245 |
| PP-H27 | PP-H23 | h23_exhibition_median_cap0.2 | test | overall | 전시 문맥 소스군 보정 cap0.2 | 3099 | 0.45019 | 1.13823 | 2.76354 | 0.891847 | 0.349468 | 0.556631 |

## 위험 구간 점수

- 없음

## Bootstrap 안정성 요약

| experiment_id | bootstrap_type | slice | family | candidate | metric | median_delta | ci_low_2_5 | ci_high_97_5 | prob_improvement_gt_0 | n_bootstrap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_MAPE | -0.0239614 | -0.144372 | 0.0502466 | 0.33375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_MdAPE | -0.000112608 | -0.0282736 | 0.0312509 | 0.49625 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_RMSE_log | -0.016285 | -0.0331815 | 0.00189611 | 0.0475 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_p95_APE | 0.101448 | -0.711612 | 0.441025 | 0.635 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_MAPE | -0.0272474 | -0.040683 | -0.0132583 | 0 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_MdAPE | -0.00327972 | -0.015715 | 0.0107234 | 0.355 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_RMSE_log | -0.0167021 | -0.0197931 | -0.0135338 | 0 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.1 | delta_p95_APE | 0.414145 | -0.0970058 | 0.457016 | 0.96625 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_MAPE | -0.0840259 | -0.336484 | 0.0626129 | 0.26 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_MdAPE | -0.00456362 | -0.049148 | 0.041901 | 0.4175 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_RMSE_log | -0.034162 | -0.0671758 | -0.00167296 | 0.0175 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_p95_APE | 0.0774081 | -1.50608 | 0.590351 | 0.55125 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_MAPE | -0.0902455 | -0.118013 | -0.062471 | 0 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_MdAPE | -0.00763245 | -0.0228938 | 0.00842965 | 0.17 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_RMSE_log | -0.0352457 | -0.0403072 | -0.0301615 | 0 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_exhibition_median_cap0.2 | delta_p95_APE | 0.529532 | 0.0785392 | 0.590623 | 0.97875 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_MAPE | 0.0700905 | 0.0133401 | 0.173196 | 1 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_MdAPE | 0.00714328 | -0.0113564 | 0.0304198 | 0.75125 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_RMSE_log | 0.00999574 | -0.005515 | 0.0272738 | 0.86875 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_p95_APE | 0.142759 | 0.0837019 | 0.693085 | 0.99875 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_MAPE | 0.0717251 | 0.0603806 | 0.0822701 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_MdAPE | 0.0075614 | -0.00293939 | 0.0187669 | 0.9375 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_RMSE_log | 0.0107761 | 0.00849159 | 0.013063 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.1 | delta_p95_APE | 0.134142 | 0.125584 | 0.447473 | 1 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_MAPE | 0.117425 | 0.00875175 | 0.314776 | 0.9925 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_MdAPE | 0.00919309 | -0.0170639 | 0.0438109 | 0.71 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_RMSE_log | 0.0178366 | -0.0105532 | 0.0512689 | 0.83375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_p95_APE | 0.22299 | 0.084772 | 1.28976 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_MAPE | 0.120448 | 0.0993575 | 0.140889 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_MdAPE | 0.0124157 | 0.000570478 | 0.0248861 | 0.98125 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_RMSE_log | 0.018898 | 0.0145323 | 0.0231993 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_gallery_museum_median_cap0.2 | delta_p95_APE | 0.229384 | 0.125584 | 0.855791 | 1 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.1 | delta_MAPE | 0.0556336 | -0.00111758 | 0.169893 | 0.97 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.1 | delta_MdAPE | 0.0133245 | -0.00620037 | 0.0350343 | 0.90375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.1 | delta_RMSE_log | 0.0121741 | -0.00209529 | 0.02865 | 0.93125 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.1 | delta_p95_APE | 0.125584 | -0.181448 | 0.693085 | 0.78625 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.1 | delta_MAPE | 0.0592888 | 0.047633 | 0.0705906 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.1 | delta_MdAPE | 0.0137973 | 0.00309216 | 0.0248335 | 0.99375 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.1 | delta_RMSE_log | 0.0127648 | 0.0103208 | 0.0149909 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.1 | delta_p95_APE | 0.134142 | -0.0279263 | 0.447473 | 0.96375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.2 | delta_MAPE | 0.0881136 | -0.0200472 | 0.307892 | 0.895 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.2 | delta_MdAPE | 0.0180658 | -0.00876135 | 0.0479297 | 0.89375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.2 | delta_RMSE_log | 0.0216656 | -0.00518405 | 0.0538775 | 0.91375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_news_median_cap0.2 | delta_p95_APE | 0.143284 | -0.306799 | 1.27952 | 0.7075 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.2 | delta_MAPE | 0.0948365 | 0.0723186 | 0.116513 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.2 | delta_MdAPE | 0.0187286 | 0.00702911 | 0.030907 | 0.99875 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.2 | delta_RMSE_log | 0.023008 | 0.0185114 | 0.0271635 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_news_median_cap0.2 | delta_p95_APE | 0.206062 | -0.0364109 | 0.854345 | 0.94375 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_MAPE | 0.0701336 | 0.0149687 | 0.172842 | 0.99875 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_MdAPE | 0.00770684 | -0.0123288 | 0.0308387 | 0.75625 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_RMSE_log | 0.00872671 | -0.00662683 | 0.0255018 | 0.83 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_p95_APE | 0.142759 | 0.0837019 | 0.693085 | 0.99875 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_MAPE | 0.0721885 | 0.0607222 | 0.0829347 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_MdAPE | 0.00921119 | -0.00208579 | 0.0210284 | 0.9525 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_RMSE_log | 0.00971381 | 0.0073952 | 0.0120443 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.1 | delta_p95_APE | 0.134142 | 0.125584 | 0.447473 | 1 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_MAPE | 0.117572 | 0.0128765 | 0.315059 | 0.9925 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_MdAPE | 0.00762146 | -0.0239544 | 0.0409714 | 0.67875 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_RMSE_log | 0.0153176 | -0.0139343 | 0.0496887 | 0.77625 | 800 |
| PP-H27 | artist | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_p95_APE | 0.223982 | 0.084772 | 1.28976 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_MAPE | 0.12207 | 0.100004 | 0.14231 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_MdAPE | 0.00917358 | -0.00312713 | 0.0229717 | 0.90625 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_RMSE_log | 0.0167905 | 0.0124515 | 0.0213819 | 1 | 800 |
| PP-H27 | row | overall | PP-H23 | h23_social_blog_median_cap0.2 | delta_p95_APE | 0.229384 | 0.125584 | 0.855791 | 1 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_MAPE | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_MdAPE | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_RMSE_log | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_p95_APE | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_MAPE | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_MdAPE | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_RMSE_log | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_confidence_only_lower_q10_blend0.5 | delta_p95_APE | 0 | 0 | 0 | 0 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_MAPE | 0.0382306 | 0.0140749 | 0.0824191 | 1 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_MdAPE | 0.00291819 | -0.0132917 | 0.0228465 | 0.6525 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_RMSE_log | -0.000747918 | -0.00913526 | 0.00870692 | 0.42875 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_p95_APE | 0.171587 | 0.101142 | 0.29392 | 1 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_MAPE | 0.0390097 | 0.0340888 | 0.0438695 | 1 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_MdAPE | 0.00718962 | -0.00362784 | 0.0168768 | 0.90375 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_RMSE_log | -0.000463624 | -0.00193132 | 0.000947795 | 0.2825 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.1 | delta_p95_APE | 0.171587 | 0.155377 | 0.197451 | 1 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_MAPE | 0.0382306 | 0.0140749 | 0.0824191 | 1 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_MdAPE | 0.00291819 | -0.0132917 | 0.0228465 | 0.6525 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_RMSE_log | -0.000747918 | -0.00913526 | 0.00870692 | 0.42875 | 800 |
| PP-H27 | artist | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_p95_APE | 0.171587 | 0.101142 | 0.29392 | 1 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_MAPE | 0.0390097 | 0.0340888 | 0.0438695 | 1 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_MdAPE | 0.00718962 | -0.00362784 | 0.0168768 | 0.90375 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_RMSE_log | -0.000463624 | -0.00193132 | 0.000947795 | 0.2825 | 800 |
| PP-H27 | row | overall | PP-H26 | h26_risk_qwidth_action_median_cap0.2 | delta_p95_APE | 0.171587 | 0.155377 | 0.197451 | 1 | 800 |

## 해석 기준

- 전체 slice에서 안정적이면 운영 후보로 볼 수 있다.
- 위험 구간 slice에서만 안정적이면 전체 모델 보정이 아니라 위험 구간 전용 정책으로 남긴다.
- artist bootstrap 개선 확률이 낮으면 특정 작가 구성에 민감하므로 수동 검수 후 재실행해야 한다.
