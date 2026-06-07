# PP-WHUBER8 Warm residual Huber 반복 split/OOF 재검증

- 작성일: 2026-06-06 23:39
- 반복 검증: `8` repeats x `5` folds
- 목적: PP-WHUBER7 목적별 후보가 validation 내부 반복 OOF에서도 안정적으로 개선되는지 확인
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`

## 1. 실행 결론

- 반복 OOF 기준 최상위 후보: `PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard`
- 최상위 후보 평균 delta MdAPE/MAPE/p95: `-0.00641` / `-0.00209` / `-0.00797`
- 최상위 후보 개선 확률 MdAPE/MAPE/p95: `1.000` / `1.000` / `1.000`
- 안정성 기준 통과 후보 수: `3`
- 운영 후보는 하나로 바로 교체하지 않고 목적별로 분리해서 판단한다. 같은 Huber 잔차 보정이라도 대표 정확도, 평균 오차, 큰 오차 방어 중 어떤 지표를 우선하느냐에 따라 적합 후보가 다르기 때문이다.
- 반복 OOF 안정성 1순위: `PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard`. OOF 평균 delta MdAPE/MAPE/p95 `-0.00641` / `-0.00209` / `-0.00797`, 개선 확률 `1.000` / `1.000` / `1.000`. test MdAPE/MAPE/p95 `0.1403` / `0.2741` / `0.8158`, delta `-0.00021` / `-0.00069` / `-0.01724`. 반복 검증은 가장 안정적이지만 test 1회 개선폭은 작아 보수형 안정성 후보로 둔다.
- test 세 지표 균형 후보: `PP-WHUBER7_balanced_all_metric_predbin_mid_open_tail_guard`. OOF 평균 delta MdAPE/MAPE/p95 `-0.00324` / `-0.00097` / `-0.00580`, 개선 확률 `1.000` / `1.000` / `0.500`. test MdAPE/MAPE/p95 `0.1334` / `0.2745` / `0.8288`, delta `-0.00712` / `-0.00027` / `-0.00428`. test에서는 MdAPE/MAPE/p95가 모두 개선됐지만 반복 OOF p95 개선 확률이 낮아 artist-level split 또는 추가 holdout 확인 후 반영한다.
- 큰 오차 방어 후보: `PP-WHUBER7_tail_guard_directional_under`. OOF 평균 delta MdAPE/MAPE/p95 `-0.00474` / `-0.00274` / `-0.00806`, 개선 확률 `1.000` / `1.000` / `1.000`. test MdAPE/MAPE/p95 `0.1396` / `0.2733` / `0.8016`, delta `-0.00091` / `-0.00155` / `-0.03142`. 대표값 개선은 작지만 p95와 MAPE 방어력이 가장 명확하므로 서비스에서 큰 오차를 줄이는 보조 정책 후보로 본다.
- MdAPE 우선 후보: `PP-WHUBER7_mdape_best_predbin_mid_open_tail_guard`. test MdAPE/MAPE/p95 `0.1328` / `0.2743` / `0.8447`, delta `-0.00770` / `-0.00046` / `0.01160`. 중앙 정확도는 가장 좋지만 p95_APE가 악화되어 운영 기본 후보로 바로 쓰지 않는다.

## 2. 반복 OOF 요약

| 후보 | 역할 | 방식 | 평균 delta MdAPE | MdAPE 개선 확률 | 평균 delta MAPE | MAPE 개선 확률 | 평균 delta p95 | p95 개선 확률 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard` | validation 균형 선택 후보 | pred_bin_cap | -0.00641 | 1.000 | -0.00209 | 1.000 | -0.00797 | 1.000 |
| `PP-WHUBER7_validation_mdape_predbin_mid_open_tail_guard` | validation MdAPE 선택 후보 | pred_bin_cap | -0.00578 | 1.000 | -0.00239 | 1.000 | -0.00581 | 0.875 |
| `PP-WHUBER7_tail_guard_directional_under` | 큰 오차 방어 후보 | directional_strength | -0.00474 | 1.000 | -0.00274 | 1.000 | -0.00806 | 1.000 |
| `PP-WHUBER7_balanced_all_metric_predbin_mid_open_tail_guard` | 세 지표 균형 후보 | pred_bin_cap | -0.00324 | 1.000 | -0.00097 | 1.000 | -0.00580 | 0.500 |
| `PP-WHUBER7_mdape_best_predbin_mid_open_tail_guard` | MdAPE 우선 후보 | pred_bin_cap | -0.00298 | 1.000 | -0.00089 | 1.000 | -0.00632 | 0.500 |

## 3. Test 1회 확인

- 기준 test MdAPE/MAPE/p95: `0.1405` / `0.2748` / `0.8331`

| 후보 | 역할 | MdAPE | MAPE | p95_APE | delta MdAPE | delta MAPE | delta p95 |
|---|---|---:|---:|---:|---:|---:|---:|
| `PP-WHUBER7_mdape_best_predbin_mid_open_tail_guard` | MdAPE 우선 후보 | 0.1328 | 0.2743 | 0.8447 | -0.00770 | -0.00046 | 0.01160 |
| `PP-WHUBER7_balanced_all_metric_predbin_mid_open_tail_guard` | 세 지표 균형 후보 | 0.1334 | 0.2745 | 0.8288 | -0.00712 | -0.00027 | -0.00428 |
| `PP-WHUBER7_validation_mdape_predbin_mid_open_tail_guard` | validation MdAPE 선택 후보 | 0.1388 | 0.2739 | 0.8118 | -0.00165 | -0.00086 | -0.02125 |
| `PP-WHUBER7_tail_guard_directional_under` | 큰 오차 방어 후보 | 0.1396 | 0.2733 | 0.8016 | -0.00091 | -0.00155 | -0.03142 |
| `PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard` | validation 균형 선택 후보 | 0.1403 | 0.2741 | 0.8158 | -0.00021 | -0.00069 | -0.01724 |
| `blend_svcnum_ppv8_wsvc_0.70` | 기준 후보 | 0.1405 | 0.2748 | 0.8331 | 0.00000 | 0.00000 | 0.00000 |

## 4. 산출물

- `outputs/repeated_oof_summary.csv`
- `outputs/repeated_oof_metrics.csv`
- `outputs/repeated_oof_fold_metrics.csv`
- `outputs/repeated_oof_predictions.csv`
- `outputs/test_once_metrics.csv`
