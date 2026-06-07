# PP-X 갤러리 티어/전시 활동 피처 재검증 실행 요약

- 작성일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_x_gallery_exhibition_revalidation.py`
- 통합 결과 파일: `experiments/track6/PP-X_gallery_exhibition_summary_metrics.csv`
- 목적: 과거 확장 split에서만 일부 검증됐던 전시 활동 피처와, Track6 최종 split에 들어오지 않았던 갤러리 티어 피처를 현재 최신 Cold 후보 구조에서 다시 검증한다.

## 1. 실행 기준

- 데이터 나누기 기준은 기존 `data/track6_split`을 그대로 유지했다.
- 학습/검증/test row는 바꾸지 않고, `_track6_row_id`를 기준으로 원천 데이터의 전시/갤러리 정보를 추가했다.
- join key는 `track4_source + track4_source_row_index`를 함께 사용했다.
- `track4_source_row_index`는 source별로 중복될 수 있으므로 row index 단독 join은 사용하지 않았다.

## 2. 사용 피처

| 구분 | 피처 | 해석 |
|---|---|---|
| 전시 활동 | 개인전 수, 단체전 수, 아트페어 수, 전시 총합, 전시 정보 가용 개수, 결측 flag, log 변환 | 작가의 활동 이력과 시장 노출 정도 |
| 갤러리 티어 | raw tier, validated tier score, tier 가용 여부, gallery ref/audit 상태 | 작가 또는 작품이 연결된 갤러리 신뢰도 |
| 상호작용 | 전시 총합 x 작품 크기, 전시 총합 x 팔로워, 갤러리 tier x 팔로워, 전시/크기 bucket | 전시/갤러리 정보가 작품 조건과 결합될 때 생기는 효과 |

## 3. 데이터 커버리지

| split | rows | 개인전 커버리지 | 단체전 커버리지 | 아트페어 커버리지 | raw 갤러리 tier | 검증 tier | tier 전체 |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 26,914 | 57.7% | 58.6% | 60.4% | 60.5% | 0.1% | 60.6% |
| validation | 2,753 | 68.0% | 66.9% | 69.1% | 69.1% | 0.0% | 69.1% |
| test | 3,099 | 52.5% | 52.3% | 54.6% | 54.9% | 1.0% | 56.0% |

- 전시 활동 피처는 재검증에 사용할 수 있을 정도의 커버리지가 있다.
- 검증된 갤러리 tier는 validation에 사실상 없고 test에도 1.0% 수준이라 단독 핵심 피처로 보기 어렵다.
- raw 갤러리 tier는 커버리지는 있으나 값의 변별력이 낮을 수 있어, 실제 효과는 모델 성능으로 확인해야 한다.

## 4. CatBoost 재검증 결과

비교 기준은 `PP-W2 generated_all_meta_all`과 동일한 CatBoost 최신 기준선이다.

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | Test RMSE_log | 기준 대비 판단 |
|---|---:|---:|---:|---:|---|
| 기준선 | 0.4497 | 1.1111 | 4.1587 | 0.8817 | 비교 기준 |
| CatBoost + 갤러리 | 0.4490 | 1.1102 | 3.9976 | 0.8768 | 아주 소폭 개선 |
| CatBoost + 전시 | 0.4505 | 1.1500 | 4.0686 | 0.8911 | 대표 오차/MAPE 악화 |
| CatBoost + 전시 + 갤러리 | 0.4511 | 1.1363 | 4.0477 | 0.8862 | 대표 오차 악화 |
| CatBoost + 전시/갤러리 상호작용 | 0.4508 | 1.1623 | 3.7278 | 0.8860 | p95는 개선, MdAPE/MAPE 악화 |

해석:

- CatBoost에서는 갤러리 피처만 추가한 후보가 기준선보다 MdAPE를 0.0007 줄였고, p95도 0.1611 줄였다.
- 전시 피처를 같이 넣으면 p95는 일부 낮아질 수 있으나 MdAPE와 MAPE가 악화됐다.
- CatBoost는 조건 조합을 잘 나누지만, 전시 피처가 작품 조건/작가 메타와 섞일 때 과도한 분기 또는 불안정한 조합을 만들 가능성이 있다.
- 따라서 CatBoost 기준으로는 `갤러리 피처 단독 추가`만 보수적으로 후속 후보로 남기고, 전시 피처 결합은 바로 채택하지 않는다.

## 5. LightGBM Quantile 재검증 결과

비교 기준은 `PP-W4 base_lightgbm_quantile_meta_all`과 동일한 LightGBM Quantile 최신 기준선이다.

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | Test RMSE_log | 기준 대비 판단 |
|---|---:|---:|---:|---:|---|
| 기준선 | 0.4766 | 1.0847 | 3.0322 | 0.8907 | 비교 기준 |
| LightGBM Quantile + 전시 | 0.4522 | 1.0825 | 3.0667 | 0.8850 | MdAPE 개선, p95 소폭 악화 |
| LightGBM Quantile + 갤러리 | 0.4682 | 1.0669 | 3.6635 | 0.8850 | MdAPE/MAPE 개선, p95 악화 |
| LightGBM Quantile + 전시 + 갤러리 | 0.4451 | 1.1277 | 3.8935 | 0.8918 | MdAPE 최고, MAPE/p95 악화 |
| LightGBM Quantile + 전시/갤러리 상호작용 | 0.4487 | 1.0807 | 3.6800 | 0.8827 | MdAPE/MAPE/RMSE 개선, p95 악화 |

해석:

- LightGBM Quantile은 전시/갤러리 피처를 활용했을 때 대표 오차인 MdAPE가 뚜렷하게 개선됐다.
- 가장 좋은 MdAPE는 `전시 + 갤러리` 후보의 0.4451이며, 기준선 대비 0.0315 낮다.
- 다만 p95_APE가 3.0322에서 3.8935로 악화되어 큰 오차 방어 후보로는 부적합하다.
- `전시/갤러리 상호작용` 후보는 MdAPE 0.4487, MAPE 1.0807, RMSE_log 0.8827로 균형은 좋지만 p95가 여전히 악화된다.

## 6. Huber 잔차 보정 결과

`LightGBM Quantile + 전시/갤러리 상호작용` 예측값을 1차 예측으로 두고, validation residual을 Huber로 학습해 cap/strength별 보정을 적용했다.

| 후보 | Test MdAPE | Test MAPE | Test p95_APE | Test RMSE_log | 판단 |
|---|---:|---:|---:|---:|---|
| 1차 기준 | 0.4487 | 1.0807 | 3.6800 | 0.8827 | 비교 기준 |
| Huber cap0.15 strength0.5 | 0.4512 | 1.0645 | 3.6861 | 0.8853 | MAPE 개선, MdAPE 악화 |
| Huber cap0.15 strength1.0 | 0.4588 | 1.0564 | 3.6780 | 0.8925 | MAPE 최고, MdAPE 악화 |
| Huber cap0.5 strength0.75 | 0.4733 | 1.0981 | 3.5860 | 0.9155 | p95 일부 개선, 전체 악화 |

해석:

- Huber 잔차 보정은 validation에서는 크게 개선됐지만 test에서는 MdAPE가 악화됐다.
- 이는 전시/갤러리 residual 패턴이 validation에만 강하게 맞춰졌을 가능성을 시사한다.
- 현 단계에서는 Huber 잔차 보정을 최종 후보로 채택하지 않고, OOF 기반 residual 학습 또는 segment 최소 표본 기준을 강화한 뒤 다시 검증해야 한다.

## 7. 결론

- 갤러리/전시 피처는 최신 Cold 구조에서 다시 학습해본 결과, 일부 조합에서 성능 개선 신호가 확인됐다.
- 가장 좋은 대표 정확도 후보는 `LightGBM Quantile + 전시 + 갤러리`로 Test MdAPE 0.4451이다.
- 기존 Cold CatBoost 대표 후보인 `PP-W2 generated_all_meta_all`의 Test MdAPE 0.4497보다 낮다.
- 그러나 이 후보는 MAPE와 p95_APE가 악화되므로 서비스 단일 후보로 바로 채택하기 어렵다.
- 큰 오차 방어까지 고려하면 기존 `PP-W4 base_lightgbm_quantile_meta_all`의 p95_APE 3.0322가 여전히 가장 안정적이다.

## 8. 다음 판단

- 대표 가격 1개를 맞추는 목적이면 `LightGBM Quantile + 전시 + 갤러리`를 추가 후보로 유지한다.
- 평균 오차와 큰 오차 방어를 함께 보려면 `LightGBM Quantile + 전시/갤러리 상호작용`을 보조 후보로 유지한다.
- CatBoost는 `갤러리 피처 단독 추가` 후보만 후속 검증 가치가 있다.
- 전시 피처는 CatBoost보다 LightGBM Quantile에서 더 잘 작동했다.
- 후속 실험은 test 반복 선택을 피하기 위해 OOF 기반으로 전시/갤러리 residual 또는 모델 라우팅 기준을 다시 만들어야 한다.

