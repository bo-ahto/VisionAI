# PP-E2E1 라우팅 end-to-end replay

{
 "clean": {
  "routing_accuracy": 0.7991,
  "eligible_leak_to_cold": 0.6377,
  "cold_leak_to_upper": 0.0,
  "wrong_key_in_upper_route": 0.0198,
  "expected_MAPE": 0.9232,
  "confusion": {
   "cold": {
    "cold": 3099,
    "warm": 415,
    "warm_lite": 386
   },
   "warm": {
    "cold": 0,
    "warm": 189,
    "warm_lite": 71
   },
   "warm_lite": {
    "cold": 0,
    "warm": 3,
    "warm_lite": 192
   }
  }
 },
 "dirty": {
  "routing_accuracy": 0.7759,
  "eligible_leak_to_cold": 0.7293,
  "cold_leak_to_upper": 0.0,
  "wrong_key_in_upper_route": 0.0206,
  "expected_MAPE": 0.9414,
  "confusion": {
   "cold": {
    "cold": 3099,
    "warm": 464,
    "warm_lite": 452
   },
   "warm": {
    "cold": 0,
    "warm": 140,
    "warm_lite": 57
   },
   "warm_lite": {
    "cold": 0,
    "warm": 3,
    "warm_lite": 140
   }
  }
 }
}