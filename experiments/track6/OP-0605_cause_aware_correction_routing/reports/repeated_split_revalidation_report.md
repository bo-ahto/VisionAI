# 원인별 보정/라우팅 반복 split 재검증 결과

## 1. 검증 범위

- 검증 대상: `expert_model_structure_guard`
- 검증 의미: 모델 재학습 검증이 아니라, validation에서 학습하는 보정값과 라우팅 정책의 안정성 검증
- 반복 방식
  - row repeated: validation 행을 여러 seed로 보정값 학습용/라우팅 확인용으로 재분할
  - artist repeated: validation 작가 단위로 보정값 학습용/라우팅 확인용으로 재분할
- 최종 평가는 기존 test split에서만 수행

## 2. 기준선

| route | policy | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm | baseline | 607 | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 0.9966 | 6 | 7 |
| cold | baseline | 3099 | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 0.9197 | 224 | 271 |

## 3. 반복 split 지표 분포

| route | split_mode | metric | mean | std | min | median | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold | artist_repeated | MAPE | 0.9798 | 0.0251 | 0.9550 | 0.9728 | 1.0317 |
| cold | artist_repeated | MdAPE | 0.4247 | 0.0076 | 0.4153 | 0.4229 | 0.4439 |
| cold | artist_repeated | RMSE_log | 0.8646 | 0.0074 | 0.8536 | 0.8615 | 0.8804 |
| cold | artist_repeated | p95_APE | 3.1129 | 0.1085 | 3.0306 | 3.0489 | 3.3053 |
| cold | row_repeated | MAPE | 0.9642 | 0.0019 | 0.9597 | 0.9641 | 0.9677 |
| cold | row_repeated | MdAPE | 0.4165 | 0.0020 | 0.4131 | 0.4165 | 0.4212 |
| cold | row_repeated | RMSE_log | 0.8578 | 0.0010 | 0.8557 | 0.8578 | 0.8600 |
| cold | row_repeated | p95_APE | 3.0316 | 0.0018 | 3.0306 | 3.0306 | 3.0357 |
| warm | artist_repeated | MAPE | 0.2816 | 0.0014 | 0.2789 | 0.2814 | 0.2838 |
| warm | artist_repeated | MdAPE | 0.1627 | 0.0021 | 0.1592 | 0.1638 | 0.1666 |
| warm | artist_repeated | RMSE_log | 0.4028 | 0.0007 | 0.4016 | 0.4030 | 0.4041 |
| warm | artist_repeated | p95_APE | 0.9310 | 0.0026 | 0.9226 | 0.9311 | 0.9373 |
| warm | row_repeated | MAPE | 0.2816 | 0.0016 | 0.2787 | 0.2816 | 0.2843 |
| warm | row_repeated | MdAPE | 0.1625 | 0.0027 | 0.1591 | 0.1625 | 0.1685 |
| warm | row_repeated | RMSE_log | 0.4029 | 0.0008 | 0.4013 | 0.4031 | 0.4042 |
| warm | row_repeated | p95_APE | 0.9300 | 0.0044 | 0.9239 | 0.9311 | 0.9373 |

## 4. 기준선 대비 변화량

| route | split_mode | delta_MdAPE_mean | delta_MdAPE_std | delta_MdAPE_min | delta_MdAPE_max | delta_MAPE_mean | delta_MAPE_std | delta_MAPE_min | delta_MAPE_max | delta_p95_APE_mean | delta_p95_APE_std | delta_p95_APE_min | delta_p95_APE_max | delta_RMSE_log_mean | delta_RMSE_log_std | delta_RMSE_log_min | delta_RMSE_log_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | artist_repeated | 0.0000 | 0.0078 | -0.0094 | 0.0192 | -0.0112 | 0.0257 | -0.0360 | 0.0407 | -0.1924 | 0.1113 | -0.2747 | 0.0000 | 0.0071 | 0.0076 | -0.0039 | 0.0229 |
| cold | row_repeated | -0.0082 | 0.0021 | -0.0116 | -0.0035 | -0.0269 | 0.0019 | -0.0313 | -0.0233 | -0.2737 | 0.0019 | -0.2747 | -0.2696 | 0.0003 | 0.0011 | -0.0018 | 0.0025 |
| warm | artist_repeated | -0.0004 | 0.0022 | -0.0040 | 0.0034 | -0.0000 | 0.0014 | -0.0027 | 0.0021 | -0.0001 | 0.0027 | -0.0085 | 0.0062 | 0.0000 | 0.0008 | -0.0012 | 0.0013 |
| warm | row_repeated | -0.0006 | 0.0028 | -0.0041 | 0.0054 | -0.0000 | 0.0016 | -0.0030 | 0.0027 | -0.0011 | 0.0045 | -0.0072 | 0.0062 | 0.0001 | 0.0008 | -0.0015 | 0.0014 |

## 5. 해석

- Warm은 row 반복 split과 artist-level split에서 평균 개선 폭이 매우 작고 일부 seed에서는 기준선보다 나빠질 수 있음
- Warm 보정은 최종 점가격 교체 후보라기보다 가격 범위/신뢰도 조정 후보로 보는 편이 안전함
- Cold는 row 반복 split에서 MdAPE/MAPE/p95_APE 개선이 안정적으로 유지됨
- Cold는 artist-level split에서 p95_APE와 MAPE 평균은 개선되지만, MdAPE와 RMSE_log는 일부 seed에서 기준선보다 나빠질 수 있음
- Cold 보정은 가능성이 있으나, artist 단위 일반화까지 최종 채택하려면 모델 재학습을 포함한 artist-level 반복 검증이 추가로 필요함
- Cold는 일부 split에서 과소 예측 건수가 늘어날 수 있으므로 가격 범위/신뢰도 정책과 함께 봐야 함
- 이 검증은 보정/라우팅 안정성 검증이며, 모델 자체의 재학습 안정성은 별도 반복 재학습 실험이 필요함

## 6. 산출물

- `outputs/repeated_split_revalidation_metrics.csv`
- `outputs/repeated_split_revalidation_summary.csv`
- `reports/repeated_split_revalidation_report.md`
