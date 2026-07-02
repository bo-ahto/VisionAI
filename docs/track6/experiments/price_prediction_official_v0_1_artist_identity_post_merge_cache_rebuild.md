# 공식 v0.1 작가 병합 후 cache 재집계 dry-run

- 작성일: 2026-06-12T19:53:38+09:00
- 운영 DB 수정 여부: 수정하지 않음
- 재집계 Shadow DB: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild/price_prediction_v0_1_post_merge_cache_rebuild_shadow.sqlite`
- 외부 피처 cache 후보: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild/official_v0_1_artist_external_feature_cache_post_merge_candidate.csv`

## 1. 결론

- 작가 식별자 병합 후보를 적용한 shadow DB에서 운영 적용 전 필요한 cache 재집계를 수행했다.
- 재집계 대상은 alias, 작가 프로필, 유사작품 통계, 유사작가 cache, 작가 단위 외부 피처 cache다.
- 운영 DB와 운영 외부 피처 cache 파일은 수정하지 않았다.
- 실제 적용 전에는 이 dry-run 결과를 기준으로 P0/P1 병합 승인 여부를 확정하고, 재집계된 cache로 예측 영향 감사를 다시 실행해야 한다.

## 2. 재집계 순서

```text
1. 검수 승인된 canonical artist_key 병합 map 적용
2. artist_aliases 중복 제거
3. artist_registry 집계 확인 및 artist_profile_snapshots 재생성
4. artwork_price_observations 기준 similar_artwork_stats_cache 재집계
5. 갱신된 artist_registry 기준 similar_artist_cache 재집계
6. row-level 전시/갤러리 피처를 canonical artist_key 기준으로 재집계
7. 외부 피처 검수 큐와 promotion impact 감사 재실행
```

## 3. 주요 수치

- alias 중복 제거: 3,600 -> 3,530
- 작가 프로필 재생성: 1,773 -> 1,713
- 유사작품 통계 cache: 9,421 -> 9,285
- 유사작가 cache: 8,388 -> 8,212
- 외부 피처 cache 작가 수: 1,713

## 4. 테이블 row 변화

| table | before | after | delta |
| --- | --- | --- | --- |
| artist_aliases | 3600 | 3530 | -70 |
| artist_profile_snapshots | 1773 | 1713 | -60 |
| artist_registry | 1773 | 1713 | -60 |
| artist_search_feature_snapshots | 150 | 150 | 0 |
| external_feature_review_queue | 2982 | 2982 | 0 |
| similar_artist_cache | 8388 | 8212 | -176 |
| similar_artwork_stats_cache | 9421 | 9285 | -136 |


## 5. 산출물

- Shadow DB: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild/price_prediction_v0_1_post_merge_cache_rebuild_shadow.sqlite`
- External cache CSV: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild/official_v0_1_artist_external_feature_cache_post_merge_candidate.csv`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_post_merge_cache_rebuild.json`
