# PP-WMIN9C Warm-lite vs WMIN8 svc-core (저이력 직접 비교)

     candidate   k    n  MdAPE   MAPE  p95_APE
     warm_lite   1  621 0.1207 0.3415   0.9559
wmin8_svc_core   1  621 0.1271 0.3406   0.9573
     warm_lite   2  489 0.1184 0.2707   0.8779
wmin8_svc_core   2  489 0.1448 0.2821   0.9478
     warm_lite   3  324 0.1060 0.2541   0.7142
wmin8_svc_core   3  324 0.1195 0.2661   0.7489
     warm_lite   4  513 0.0923 0.2557   0.7884
wmin8_svc_core   4  513 0.1190 0.2634   0.7682
     warm_lite all 1947 0.1092 0.2866   0.8765
wmin8_svc_core all 1947 0.1291 0.2932   0.9163

{
 "warm_lite_overall": {
  "MdAPE": 0.1092,
  "MAPE": 0.2866,
  "p95_APE": 0.8765
 },
 "wmin8_svc_core_overall": {
  "MdAPE": 0.1291,
  "MAPE": 0.2932,
  "p95_APE": 0.9163
 },
 "warm_lite_wins_MdAPE": true,
 "warm_lite_wins_MAPE": true,
 "warm_lite_wins_p95": true,
 "boundary_confirmed": true
}