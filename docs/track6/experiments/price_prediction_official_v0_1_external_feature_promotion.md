# 공식 v0.1 외부 피처 승인 후보 승격 리포트

- 작성일: 2026-06-12T17:18:03+09:00
- 실행 모드: `dry-run`
- 기존 운영 cache row 수: 1,773
- 승인 후보 cache row 수: 638
- 승격 gate 통과 여부: `True`

## 1. 결론

- 승인된 외부 피처 후보만 승격 후보 cache에 포함됐다.
- 중복 URL, 동명이인 충돌, 추가 수집 필요 후보는 승격 후보에서 제외됐다.
- 기본 실행은 dry-run이므로 기존 운영 cache는 수정하지 않았다.

## 2. 후보 선별 결과

| 항목 | 건수 |
|---|---:|
| review queue 외부 피처 후보 | 1,773 |
| 승인 조건 통과 후보 | 638 |
| 작가키 중복 제거 후 후보 | 638 |
| 승격 차단 후보 | 1,135 |
| 작가키 중복으로 제외 | 0 |

## 3. 기존 cache 대비 차이

| 구분 | 건수 |
|---|---:|
| `kept` | 638 |
| `candidate_only` | 0 |
| `current_only` | 1,135 |
| `changed` | 0 |

## 4. 차단 사유

| 사유 | 건수 |
|---|---:|
| `not_approved_status` | 1,135 |

## 5. 산출물

- 승인 후보 cache CSV: `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion/approved_external_feature_cache_candidate.csv`
- 기존 cache 대비 diff CSV: `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion/external_feature_promotion_diff.csv`
- 감사 JSON: `docs/track6/experiments/price_prediction_official_v0_1_external_feature_promotion.json`
