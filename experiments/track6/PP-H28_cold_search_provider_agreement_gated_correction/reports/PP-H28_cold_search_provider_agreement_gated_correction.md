# PP-H28 Cold 검색 provider agreement 기반 제한 보정 검증

- 작성일: 2026-06-07 21:19
- 데이터: precomputed 검색 보정 예측 + provider agreement (live 검색 불필요)
- 주의: h23 검색 보정은 상류 고정 예측값. 반복 subsample은 fold refit이 아니라 고정 후보 robustness 평가.

## 1. 실행 결론

- 검색 보정은 유효한 MAPE/p95 방어 후보이나, provider agreement 게이팅은 현 데이터로 비현실(high 등급 0, 커버리지 극소). 안전장치는 cap 기반 방어층 + 저신뢰 검수 플래그로, agreement 커버리지 확대는 별도 데이터 과제.
- 검색 보정(`ungated_gallery_museum_cap0.1`) 방어 유효: True (artist subsample MAPE/p95 개선확률 0.88/0.97)
- provider agreement 게이팅 실행 가능: False (high 등급 0개, agreement 보유 작가 18명, test gate 변경행 {'gate_not_risk': 0, 'gate_medium': 0})

## 2. provider agreement 커버리지 사실

- agreement 보유 작가: 18명, grade 분포(전 행): {'missing': 3279, 'low': 2207, 'medium': 366}
- **high(≥0.70) 등급: 0개** → 'high에서만 적용' 게이트 실행 불가
- test에서 gate 변경 행수: {'gate_not_risk': 0, 'gate_medium': 0} (전체 test 3099행)

## 3. validation 반복 subsample 요약 (base 대비 개선확률)

| candidate | mean_MdAPE | mean_MAPE | mean_p95_APE | prob_MdAPE_improve | prob_MAPE_improve | prob_p95_improve |
| --- | --- | --- | --- | --- | --- | --- |
| ungated_exhibition_cap0.2 | 0.4025 | 0.5587 | 1.4421 | 0.6500 | 0.7750 | 0.7750 |
| ungated_exhibition_cap0.1 | 0.4058 | 0.5679 | 1.4558 | 0.6250 | 0.9000 | 0.8500 |
| ungated_gallery_museum_cap0.2 | 0.4007 | 0.5778 | 1.4982 | 0.5500 | 0.7500 | 0.9500 |
| ungated_art_general_cap0.2 | 0.3840 | 0.5820 | 1.6027 | 0.7000 | 0.7250 | 0.6750 |
| ungated_social_blog_cap0.2 | 0.3933 | 0.5825 | 1.5855 | 0.6500 | 0.6250 | 0.7500 |
| ungated_gallery_museum_cap0.1 | 0.4063 | 0.5857 | 1.5188 | 0.5750 | 0.8750 | 0.9750 |
| ungated_art_general_cap0.1 | 0.3980 | 0.5869 | 1.5697 | 0.7500 | 0.8250 | 0.7750 |
| ungated_social_blog_cap0.1 | 0.4011 | 0.5877 | 1.5589 | 0.7000 | 0.7500 | 0.8250 |
| base_pp_y2 | 0.4211 | 0.6123 | 1.6296 | 0.0000 | 0.0000 | 0.0000 |

## 4. test 확인

| candidate | test_MdAPE | test_MAPE | test_p95_APE |
| --- | --- | --- | --- |
| base_pp_y2 | 0.4421 | 1.0484 | 3.3537 |
| ungated_gallery_museum_cap0.1 | 0.4348 | 0.9770 | 3.2196 |
| ungated_gallery_museum_cap0.2 | 0.4313 | 0.9285 | 3.1390 |
| ungated_social_blog_cap0.1 | 0.4328 | 0.9766 | 3.2196 |
| ungated_social_blog_cap0.2 | 0.4344 | 0.9270 | 3.1390 |
| ungated_exhibition_cap0.1 | 0.4452 | 1.0756 | 2.9394 |
| ungated_exhibition_cap0.2 | 0.4502 | 1.1382 | 2.7635 |
| ungated_art_general_cap0.1 | 0.4503 | 1.1025 | 3.2196 |
| ungated_art_general_cap0.2 | 0.4577 | 1.1802 | 3.2196 |
| gate_not_risk(on gallery_museum_cap0.1) | 0.4421 | 1.0484 | 3.3537 |
| gate_medium(on gallery_museum_cap0.1) | 0.4421 | 1.0484 | 3.3537 |

## 5. agreement grade별 보정 효과 (선정 source)

- 선정 source: `gallery_museum_cap0.1`
| split | grade | n | base_MdAPE | corr_MdAPE | base_MAPE | corr_MAPE | base_p95 | corr_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | low | 1192 | 0.3800 | 0.3567 | 1.5782 | 1.4257 | 4.6289 | 4.0932 |
| test | missing | 1907 | 0.4817 | 0.4765 | 0.7172 | 0.6966 | 2.3454 | 2.2423 |
| validation | low | 1015 | 0.3516 | 0.3558 | 0.3863 | 0.3808 | 0.6956 | 0.8740 |
| validation | medium | 366 | 0.4817 | 0.3532 | 0.6300 | 0.5201 | 1.4465 | 1.2137 |
| validation | missing | 1372 | 0.4907 | 0.4750 | 0.7275 | 0.7047 | 2.1473 | 2.0503 |

## 6. 산출물

- `outputs/repeated_subsample_summary.csv`, `outputs/agreement_grade_breakdown.csv`, `outputs/test_metrics.csv`, `artifacts/run_config.json`