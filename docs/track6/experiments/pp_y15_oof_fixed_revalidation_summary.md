# PP-Y16 PP-Y15 OOF 고정 재검증 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_y15_oof_fixed_revalidation.py`
- 실험 폴더: `experiments/track6/PP-Y16_cold_y15_oof_fixed_revalidation`
- 기준 1차 예측값: `PP-Y2_cold_lgbq_search_external_combo` / `lgbq_search_all_external_interaction`
- 목적: `PP-Y15`에서 test 기준으로 좋아 보였던 segment/cap 보정이 validation 내부 OOF 기준으로도 채택 가능한지 확인한다.

## 1. 왜 다시 검증했는가

- `PP-Y15` closure 실험에서는 segment 종류, 최소 표본 수, cap 조합을 많이 비교했다.
- 이 방식은 test에서 좋은 후보를 찾는 데에는 도움이 되지만, 후보가 많을수록 test에 우연히 잘 맞은 설정을 고를 위험이 있다.
- 따라서 이번 `PP-Y16`에서는 test를 보고 고르지 않고 validation 내부 5-fold OOF 결과로 설정을 먼저 고른 뒤, 그 설정만 test에 적용했다.

## 2. 검증 방식

- validation 예측값으로 예측 가격 bin과 quantile width bin의 경계를 고정했다.
- test에는 validation에서 만든 같은 bin 경계를 적용했다.
- 각 후보는 validation 내부 5-fold로 다음 절차를 반복했다.
  - 4개 fold로 segment별 residual 중앙값 보정표를 만든다.
  - 남은 1개 fold에 보정표를 적용한다.
  - 전체 validation OOF 예측값을 모아 후보 성능을 계산한다.
- 최종 test는 full validation으로 보정표를 다시 만든 뒤 1회 적용했다.

## 3. validation OOF 기준 선택 결과

| 선택 기준 | 선택 후보 | Validation OOF MdAPE | Validation OOF MAPE | Validation OOF p95 | Test MdAPE | Test MAPE | Test p95 |
|---|---|---:|---:|---:|---:|---:|---:|
| MdAPE 우선 | `pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |
| MAPE 우선 | `pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |
| p95 우선 | `pred_x_qwidth_oof_min30_cap0.15` | 0.3701 | 0.5517 | 1.3791 | 0.4382 | 1.0981 | 3.3512 |
| 균형 rank | `pred_x_qwidth_oof_min30_cap0.35` | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |

## 4. 기준 후보와 비교

| 후보 | Test MdAPE | Test MAPE | Test p95 | 해석 |
|---|---:|---:|---:|---|
| `PP-Y2` 단일 모델 | 0.4421 | 1.0484 | 3.3537 | 보정 전 기준 |
| `PP-Y15` closure 최고 MdAPE | 0.4245 | 1.0668 | 3.4110 | test 탐색상 최고이나 고정 선택 근거 부족 |
| `PP-Y16` validation OOF MdAPE/균형 선택 | 0.4438 | 1.1083 | 2.8025 | 대표 정확도는 유지/소폭 악화, 큰 오차 방어는 뚜렷하게 개선 |
| `PP-Y16` validation OOF p95 선택 | 0.4382 | 1.0981 | 3.3512 | MdAPE는 소폭 개선, p95 개선은 약함 |

## 5. 판단

- `PP-Y15`의 test 최고 MdAPE `0.4245`는 최종 후보로 바로 채택하기 어렵다.
- validation OOF 기준으로 고르면 test MdAPE가 `0.4438`로 `PP-Y2`의 `0.4421`보다 약간 나빠진다.
- 대신 p95는 `3.3537`에서 `2.8025`로 크게 좋아진다.
- 따라서 `PP-Y15/PP-Y16` 보정은 대표 가격 정확도를 높이는 최종 보정이라기보다, 큰 오차 방어용 위험 구간 보정으로 보는 것이 맞다.

## 6. 후속 판단

- Cold 대표 가격 후보는 여전히 `PP-Y2` 또는 `PP-Y10/PP-Y15`의 추가 split 재검증 후보로 유지한다.
- 서비스에서 큰 오차 방어가 중요한 표시 구간에는 `PP-Y16 pred_x_qwidth_oof_min30_cap0.35`를 p95 방어 정책 후보로 둘 수 있다.
- `PP-Y15` test 최고 MdAPE 후보를 다시 보고 싶다면 같은 설정을 다른 random split 또는 시간 기준 split에서 한 번 더 확인해야 한다.
