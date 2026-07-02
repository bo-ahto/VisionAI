# PP-SVC9 Warm svc 최정밀 매칭 게이트 (fine-match-only)

- 작성일: 2026-06-07 20:32
- 게이트 레벨(구조적, PP-SVC8): `artist_medium_support_size`
- in-gate weight w_fine = 1.0 (고정 validation 최정밀 subset에서 선택)
- 비교 기준: 운영 기본값 pp_v8. (70:30은 0604에서 붕괴하므로 비교 목표 아님)

## 1. 실행 결론

- 판정: **중단: 한 영역에서 pp_v8 대비 악화**
- 게이트 vs pp_v8 — 고정 test: ΔMdAPE -0.0083, ΔMAPE -0.0070
- 게이트 vs pp_v8 — 0604: ΔMdAPE +0.0075, ΔMAPE +0.0062
- 핵심 해석: 0604 최정밀 subset에서 svc는 MdAPE(중앙값)는 개선하나 MAPE(평균)는 악화 = staleness가 최정밀 매칭에서도 꼬리(tail) 위험으로 잔존. 어떤 svc 가중치도 0604에서 pp_v8을 중앙값·평균 동시 지배 못함. 고정 test(과거)는 svc가 깨끗해 게이트가 pp_v8보다 개선되지만, 신규 0604에서는 median-vs-tail 트레이드오프라 순지배 실패.

## 2. 후보 × 영역 MdAPE

| candidate | validation | test | 0604 |
| --- | --- | --- | --- |
| blend_0.70 | 0.1305 | 0.1405 | 0.2779 |
| fine_gate_plus_artist_size_w1.00 | 0.1282 | 0.1518 | 0.2488 |
| fine_gate_w1.00 | 0.1296 | 0.1548 | 0.2373 |
| pp_v8 | 0.1544 | 0.1632 | 0.2298 |

## 3. 후보 × 영역 MAPE

| candidate | validation | test | 0604 |
| --- | --- | --- | --- |
| blend_0.70 | 0.2110 | 0.2748 | 0.3774 |
| fine_gate_plus_artist_size_w1.00 | 0.2353 | 0.2807 | 0.3705 |
| fine_gate_w1.00 | 0.2424 | 0.2746 | 0.3421 |
| pp_v8 | 0.2544 | 0.2816 | 0.3359 |

## 4. 게이트 적용 구간(최정밀 매칭) svc vs pp_v8

| region | fine_n | fine_share_pct | gate_MdAPE | ppv8_MdAPE | gate_MAPE | ppv8_MAPE |
| --- | --- | --- | --- | --- | --- | --- |
| validation | 202 | 38.9000 | 0.0755 | 0.1171 | 0.1487 | 0.1794 |
| test | 247 | 40.7000 | 0.0980 | 0.1226 | 0.1718 | 0.1891 |
| 0604 | 91 | 11.0000 | 0.1429 | 0.1709 | 0.2476 | 0.1912 |

## 5. w_fine validation 선택

| w_fine | val_fine_n | val_fine_MdAPE | val_fine_MAPE |
| --- | --- | --- | --- |
| 0.5000 | 202 | 0.0872 | 0.1477 |
| 0.7000 | 202 | 0.0781 | 0.1439 |
| 1.0000 | 202 | 0.0755 | 0.1487 |

## 6. 산출물

- `outputs/region_candidate_metrics.csv`, `outputs/gate_applied_subset_compare.csv`, `outputs/w_fine_validation_selection.csv`
- `artifacts/run_config.json`