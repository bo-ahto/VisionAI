# PP-PCOLD1 pseudo-cold 평가셋

- 용도: Cold 후보의 외부 검증 축 (0604는 Warm 시험 제출 전용이므로 사용 금지).
- 후보/경계값 선택에는 사용하지 않는다.

## seed별 구성

[
  {
    "seed": 20260610,
    "masked_artists": 212,
    "pseudo_rows": 1207,
    "train_rows_remaining": 25707,
    "search_lookup_coverage_pseudo": 0.0,
    "guard_width_q67": 1.7809204701507735,
    "guard_gap_q50": 0.12195837293848832
  },
  {
    "seed": 20260611,
    "masked_artists": 222,
    "pseudo_rows": 1206,
    "train_rows_remaining": 25708,
    "search_lookup_coverage_pseudo": 0.0,
    "guard_width_q67": 1.7938042283580735,
    "guard_gap_q50": 0.12372556893851083
  },
  {
    "seed": 20260612,
    "masked_artists": 206,
    "pseudo_rows": 1206,
    "train_rows_remaining": 25708,
    "search_lookup_coverage_pseudo": 0.0,
    "guard_width_q67": 1.758416335246686,
    "guard_gap_q50": 0.12721442345040934
  }
]

## 지표 (seed 평균/표준편차)

                                          MdAPE            MAPE         p95_APE        
                                           mean     std    mean     std    mean     std
eval_set             candidate                                                         
pseudo_cold          defense_guard       0.5772  0.0087  1.1877  0.1751  4.1654  1.5247
                     representative_q50  0.5853  0.0087  1.2742  0.2057  4.3326  1.4034
real_cold_test       defense_guard       0.4816  0.0006  1.2081  0.0184  3.9780  0.2303
                     representative_q50  0.4835  0.0032  1.2789  0.0093  4.2442  0.0668
real_cold_validation defense_guard       0.3840  0.0123  0.6227  0.0120  1.6734  0.0072
                     representative_q50  0.3905  0.0106  0.6653  0.0086  1.7842  0.0351

## 선택 bias 감사

                   set    n  price_median_krw  price_q90_krw  log_area_median  top3_medium_share  top_medium
pseudo_cold(all seeds) 2686         2760000.0     15935000.0         8.204229           0.824274 mixed_media
  real_cold_validation 2753         2622000.0     12249312.0         8.256633           0.924446     acrylic
        real_cold_test 3099         3450000.0     20087280.0         8.390636           0.855437 mixed_media