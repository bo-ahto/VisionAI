# 공식 v0.1 외부 피처 승격 gate 감사

- 작성일: 2026-06-12T17:12:17+09:00
- gate 통과 여부: `True`
- 승격 dry-run 후보 수: 712건
- 승격 차단 후보 수: 2,270건

## 1. 결론

- 승인 후보만 승격 대상으로 선별됐다.
- 중복 후보, 동명이인 충돌 후보, 추가 수집 필요 후보는 승격 대상에 포함되지 않았다.
- 이 감사는 cache를 수정하지 않는 dry-run 검증이다.

## 2. 검수 상태별 수량

| 상태 | 건수 |
|---|---:|
| `approved_baseline` | 712 |
| `auto_reject_duplicate` | 470 |
| `needs_human_review` | 724 |
| `needs_improvement` | 1,075 |
| `needs_review` | 1 |

## 3. 중복 상태별 수량

| 상태 | 건수 |
|---|---:|
| `artist_name_conflict` | 135 |
| `cross_artist_duplicate_url` | 588 |
| `same_artist_duplicate_url` | 470 |
| `unique` | 1,789 |

## 4. 승격 규칙

- `review_status = approved_baseline` 후보만 자동 승격 가능
- 검수 결정 테이블에서 `decision = approved`가 된 후보만 추가 승격 가능
- `same_artist_duplicate_url`, `cross_artist_duplicate_url`, `artist_name_conflict` 후보는 승격 불가
- 승인 후보의 최소 품질 점수 기준: `0.2` 이상
- 이 스크립트는 승인 후보 목록만 생성하고 운영 cache는 수정하지 않음

## 5. 위반 내역

- 위반 없음

## 6. 산출물

- 승격 dry-run CSV: `experiments/track6/PP-OFFICIAL-V01_feature_review_gate_audit/promotion_candidates_dry_run.csv`
- 감사 JSON: `docs/track6/experiments/price_prediction_official_v0_1_feature_review_gate_audit.json`
