# 공식 v0.1 외부 피처 승격 전 예측 영향 감사

- 작성일: 2026-06-12T17:38:23+09:00
- 실행 모드: `all`
- 평가 row 수: 1,773

## 1. 결론

- 운영 cache는 수정하지 않았다.
- 현재 cache와 승인 후보 cache를 각각 사용해 같은 Cold 입력을 예측했다.
- 승인 후보 cache에서 제외되는 작가는 전시/갤러리 외부 피처가 missing/default로 바뀔 수 있으므로, 실제 적용 전 전체 영향 감사를 먼저 봐야 한다.

## 2. 영향 요약

| 항목 | 값 |
|---|---:|
| 예측값 변화 row | 1,134 |
| 외부 피처 coverage 상실 row | 1,135 |
| 평균 절대 변화율 | 0.0140 |
| 중앙 절대 변화율 | 0.0012 |
| p95 절대 변화율 | 0.0558 |
| 최대 절대 변화율 | 0.6227 |
| 1% 초과 변화 row | 322 |
| 5% 초과 변화 row | 296 |

## 3. 판단

- 이 감사는 품질 낮은 외부 피처를 제거할 때 예측 가격이 얼마나 움직이는지 보는 사전 점검이다.
- 변화폭이 크면 승인 후보 cache를 바로 적용하지 않고, 차단된 1,135건 중 실제로 개선 수집 가능한 작가를 먼저 보강한다.
- 변화폭이 작고 안정적이면 `--apply` 적용 전 전체 작가 감사로 확장한다.

## 4. 산출물

- 상세 결과 CSV: `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion_impact/promotion_impact_rows.csv`
- 감사 JSON: `docs/track6/experiments/price_prediction_official_v0_1_external_feature_promotion_impact.json`
