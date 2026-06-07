# PP-SVCSHRINK1 Warm 비교군 prior shrinkage 갱신

- 작성일: 2026-06-07 21:45
- source pool: warm train 26914, 계층 ['L1_artist', 'L2_artist_size', 'L3_artist_medium_support_size'] (nested), size_bin 5분위
- k 선택(validation MdAPE): k=5
- 거래 시점 데이터 부재로 recency 갱신 불가 → EB 계층 shrinkage로 분산 완화 검증. raw 비교군 prior 컴포넌트 수준.

## 1. 실행 결론

- 채택: shrinkage(k=5)가 0604 staleness 완화 — residual std 1.097→0.949, MAPE 0.955→0.812, p95 4.017→3.358, MdAPE 0.394→0.384 (test 비악화). svc 비교군 feature를 shrunk median으로 교체해 Warm Huber 재학습+반복검증 후속 권고.

## 2. raw vs shrunk prior (영역별)

| region | candidate | n | MdAPE | MAPE | p95_APE | resid_std |
| --- | --- | --- | --- | --- | --- | --- |
| validation | raw_prior | 519 | 0.2834 | 0.6961 | 3.2884 | 0.7848 |
| validation | shrunk_prior_k5 | 519 | 0.2692 | 0.4693 | 1.5279 | 0.5849 |
| test_warm | raw_prior | 607 | 0.3100 | 0.7320 | 2.2931 | 0.7679 |
| test_warm | shrunk_prior_k5 | 607 | 0.2617 | 0.4898 | 1.5545 | 0.6102 |
| 0604 | raw_prior | 829 | 0.3943 | 0.9549 | 4.0169 | 1.0969 |
| 0604 | shrunk_prior_k5 | 829 | 0.3841 | 0.8123 | 3.3577 | 0.9489 |

## 3. k validation 선택

| k | val_MdAPE |
| --- | --- |
| raw | 0.2834 |
| 5 | 0.2692 |
| 20 | 0.4638 |
| 50 | 0.5709 |
| 100 | 0.6692 |

## 4. 비교군 레벨 해소 분포 (raw, %)

| region | global | L1_artist | L2_artist_size | L3_artist_medium_support_size |
| --- | --- | --- | --- | --- |
| validation | 0.0000 | 48.2000 | 12.7000 | 39.1000 |
| test_warm | 0.0000 | 48.6000 | 10.4000 | 41.0000 |
| 0604 | 12.3000 | 49.0000 | 27.1000 | 11.6000 |

## 5. 산출물

- `outputs/region_prior_metrics.csv`, `outputs/k_validation_selection.csv`, `outputs/level_coverage.csv`, `artifacts/run_config.json`