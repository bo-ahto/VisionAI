# PP-CDIAG1 Cold base 잔차 진단

- 위험 구간 선정: validation 기준만 사용. test ratio는 확인 표기.
- 0604 미사용 (Warm 시험 제출 전용).

## 전체 기준 (MdAPE/MAPE/p95)

{
  "test/research": {
    "n": 3099,
    "MdAPE": 0.4098,
    "MAPE": 0.8493,
    "p95_APE": 2.3465
  },
  "test/operational": {
    "n": 3099,
    "MdAPE": 0.4852,
    "MAPE": 1.1771,
    "p95_APE": 4.1223
  },
  "validation/research": {
    "n": 2753,
    "MdAPE": 0.3553,
    "MAPE": 0.4978,
    "p95_APE": 1.4996
  },
  "validation/operational": {
    "n": 2753,
    "MdAPE": 0.3881,
    "MAPE": 0.6169,
    "p95_APE": 1.6482
  }
}

## 위험 구간 (validation)

      segment_dim           segment        bases_flagged  n_validation max_MAPE_ratio max_p95_ratio resid_mean test_MAPE_ratio_research
    seg_model_gap       gap_extreme          operational           276          2.016         2.448     -0.212                    0.937
       seg_qwidth    qwidth_extreme operational,research           276          1.767         2.292      0.284                    0.897
seg_guard_applied          guard_on operational,research           573          1.666         1.991      0.131                    0.805
  seg_artist_rows   artist_rows_3_9 operational,research           333          1.372         2.078      0.166                    0.749
       seg_qwidth       qwidth_high operational,research           633          1.357         1.487      0.003                    0.714
       seg_medium       mixed_media operational,research           809          1.307         1.313      0.054                    0.803
  seg_artist_rows artist_rows_10_49          operational           786          1.166         1.353     -0.041                    0.721
         seg_size        size_small          operational           951          1.162         1.350      0.023                    0.600

## 잔차 크기 상관 (validation, 연구 base APE)

{
  "quantile_width_log": 0.2152,
  "model_gap_abs": -0.0021,
  "search_delta_abs": -0.1593,
  "log_area": -0.0683,
  "artist_rows_in_split": -0.1573
}