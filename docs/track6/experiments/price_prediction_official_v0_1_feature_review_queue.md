# 공식 v0.1 외부 피처 검수 큐

- 작성일: 2026-06-12T17:08:24+09:00
- 큐 버전: `official_v0_1_feature_review_queue_20260612`
- 전체 후보 수: 2,982건

## 1. 결론

- 승인된 baseline 후보: 712건
- 개선 수집 필요 후보: 1,075건
- 사람 검수 필요 후보: 724건
- 자동 중복 제외 후보: 470건
- 운영 원칙: `approved_baseline` 또는 별도 검수 결정에서 `approved`가 된 후보만 feature cache 승격 대상

## 2. 검수 상태별 수량

| 상태 | 건수 |
|---|---:|
| `needs_improvement` | 1,075 |
| `needs_human_review` | 724 |
| `approved_baseline` | 712 |
| `auto_reject_duplicate` | 470 |
| `needs_review` | 1 |

## 3. 중복 판정 기준

| 기준 | 처리 |
|---|---|
| 같은 URL이 같은 작가 검색 내 반복 | `auto_reject_duplicate` |
| 같은 URL이 여러 작가 검색에 반복 | `needs_human_review` |
| 정규화 작가명이 여러 artist_key에 매핑 | `needs_human_review` |
| 동일 source hash 재수집 | 기존 승인 row와 비교 후 중복 제외 |

## 4. 개선 판정 기준

| 기준 | 처리 |
|---|---|
| 검색 품질 점수 낮음 또는 수집 실패 | `needs_improvement` |
| 전시/갤러리 evidence 없음 | `needs_improvement` |
| 실제 판매가 feedback | `needs_review` 후 학습 후보 승격 |
| gallery/exhibition/source_count 증가 | 기존 cache보다 개선된 후보로 검수 대상 |

## 5. 산출물

- CSV: `experiments/track6/PP-OFFICIAL-V01_feature_review_queue/outputs/feature_review_queue.csv`
- DB: `data/track6/service_v0_1/price_prediction_v0_1.sqlite` table `external_feature_review_queue`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_feature_review_queue.json`
