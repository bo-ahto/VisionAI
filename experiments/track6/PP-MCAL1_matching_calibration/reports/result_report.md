# PP-MCAL1 매칭 캘리브레이션

          bin    n  accuracy
   [0.0, 0.5) 2806  0.705631
   [0.5, 0.6)    1  1.000000
   [0.6, 0.7)  218  0.408257
  [0.7, 0.75)  208  1.000000
  [0.75, 0.8) 1535  1.000000
  [0.9, 0.93)   61  1.000000
[0.93, 0.951)  728  1.000000

 threshold  n_pass  accuracy_among_pass  expected_MAPE_if_warm  warm_beats_cold
      0.70    2532                  1.0                 0.2485             True
      0.75    2324                  1.0                 0.2485             True
      0.80     789                  1.0                 0.2485             True
      0.85     789                  1.0                 0.2485             True
      0.88     789                  1.0                 0.2485             True
      0.90     789                  1.0                 0.2485             True
      0.93     728                  1.0                 0.2485             True
      0.95     713                  1.0                 0.2485             True

{"min_threshold_where_warm_beats_cold": 0.7, "accuracy_at_0.90": 1.0, "required_accuracy_floor": 0.85}