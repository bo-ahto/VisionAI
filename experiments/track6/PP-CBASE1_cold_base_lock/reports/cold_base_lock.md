# PP-CBASE1 Cold 이중 base lock

- 목적: 이후 Cold 실험의 기준 base, residual target, 채택 게이트를 고정한다.
- 연구 base: `COLD_BASE_RESEARCH_V1` = v0.3 guard+search 체인 (`research_base_pred_log`)
- 운영 base: `COLD_BASE_OPERATIONAL_V1` = v0.2 search-free 방어 서빙값 (`v02_defense_pred_log`)
- 0604는 Warm 시험 제출 전용 — Cold 실험 전 단계에서 사용 금지.

## 고정 base 성능

| candidate | split | n | MdAPE | MAPE | p95_APE | RMSE_log | within_30 | over_50pct_error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COLD_BASE_RESEARCH_V1 (v0.3 guard+search) | test | 3099 | 0.4098 | 0.8493 | 2.3465 | 0.8503 | 0.3743 | 0.4153 |
| guard_only_v0_1 | test | 3099 | 0.4178 | 0.9640 | 2.5377 | 0.8691 | 0.3469 | 0.4247 |
| component_pp_y18_qwidth_bin | test | 3099 | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 0.3462 | 0.4221 |
| component_pp_y2_baseline | test | 3099 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 0.3249 | 0.4398 |
| COLD_BASE_OPERATIONAL_V1 (v0.2 defense) | test | 3099 | 0.4852 | 1.1771 | 4.1223 | 0.9371 | 0.2875 | 0.4814 |
| v02_representative_q50 | test | 3099 | 0.4823 | 1.2424 | 4.3806 | 0.9411 | 0.2862 | 0.4837 |
| COLD_BASE_RESEARCH_V1 (v0.3 guard+search) | validation | 2753 | 0.3553 | 0.4978 | 1.4996 | 0.6370 | 0.4159 | 0.3033 |
| guard_only_v0_1 | validation | 2753 | 0.3650 | 0.5182 | 1.3392 | 0.6393 | 0.3963 | 0.3433 |
| component_pp_y18_qwidth_bin | validation | 2753 | 0.3656 | 0.5460 | 1.4000 | 0.6388 | 0.3977 | 0.3531 |
| component_pp_y2_baseline | validation | 2753 | 0.4129 | 0.5887 | 1.5042 | 0.6556 | 0.3360 | 0.4017 |
| COLD_BASE_OPERATIONAL_V1 (v0.2 defense) | validation | 2753 | 0.3881 | 0.6169 | 1.6482 | 0.6675 | 0.3549 | 0.3375 |
| v02_representative_q50 | validation | 2753 | 0.3962 | 0.6633 | 1.7910 | 0.6789 | 0.3436 | 0.3629 |

## 작가 단위 구성

{
  "test": {
    "rows": 3099,
    "artists": 200,
    "rows_per_artist_median": 6.0,
    "rows_per_artist_max": 275,
    "search_covered_rate": 1.0
  },
  "validation": {
    "rows": 2753,
    "artists": 172,
    "rows_per_artist_median": 5.0,
    "rows_per_artist_max": 366,
    "search_covered_rate": 1.0
  }
}

## 정책 JSON 재현 검증 (test, 절대 오차)

{
  "v0_3_representative": {
    "MdAPE": 0.0,
    "MAPE": 0.0,
    "p95_APE": 0.0
  },
  "v0_3_guard_only": {
    "MdAPE": 0.0,
    "MAPE": 0.0,
    "p95_APE": 0.0
  },
  "v0_3_defense": {
    "MdAPE": 0.0,
    "MAPE": 0.0,
    "p95_APE": 0.0
  },
  "v0_2_representative": {
    "MdAPE": 0.0,
    "MAPE": 0.0,
    "p95_APE": 0.0
  },
  "v0_2_defense": {
    "MdAPE": 0.0,
    "MAPE": 0.0,
    "p95_APE": 0.0
  }
}

## 다음 실험 규칙

- base prediction은 항상 `fixed_cold_base_rows.csv`의 고정 컬럼을 사용한다.
- 후보는 두 base 대비 개선폭을 모두 보고한다.
- 채택 게이트는 artist 반복 holdout(80%/70%, 각 >=200회) MAPE/p95 >=0.90이 1차다.
- 상세 로드맵: `docs/track6/experiments/cold_improvement_roadmap.md`