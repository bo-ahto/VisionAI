# 가격 예측 서비스 공식 테스트 v0.1 DB 생성 결과

- 생성일: 2026-06-12T00:00:00+09:00
- 공식 버전: `price_prediction_v0.1`
- DB 파일: `data/track6/service_v0_1/price_prediction_v0_1.sqlite`
- cache snapshot: `official_v0_1_initial_cache`

## 1. 생성 목적

- 보고서 기준 Warm/Cold 모델을 raw 입력 서비스에 연결하기 전 필요한 조회 기반 생성
- 작가 매칭, 가격 이력, 검색 피처, 유사작품 통계, 유사작가 후보, 모델 레지스트리 저장
- 모델 학습 또는 모델 교체는 수행하지 않음

## 2. 원천 파일

- schema: `docs/track6/experiments/price_prediction_official_v0_1_schema.sql`
- train: `models/track6/price_prediction_v0.1/data/training/track6_split/track6_train.csv`
- search_features: `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv`
- search_results: `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv`

## 3. 적재 결과

| 테이블 | row 수 |
|---|---:|
| `artist_registry` | 1,773 |
| `artist_aliases` | 3,600 |
| `artist_profile_snapshots` | 1,773 |
| `artwork_price_observations` | 26,914 |
| `artist_search_feature_snapshots` | 150 |
| `artist_search_results` | 2,526 |
| `similar_artwork_stats_cache` | 9,421 |
| `similar_artist_cache` | 8,388 |
| `model_artifact_registry` | 2 |

## 4. 다음 단계

- `/api/v1/artists/resolve`에서 `artist_aliases`와 `artist_registry`를 사용해 작가 후보를 반환
- `/api/v1/artworks/price-estimate`에서 `artwork_price_observations`, `similar_artwork_stats_cache`, `artist_search_feature_snapshots`를 조회
- Warm/Cold 중간 피처 생성 adapter를 추가한 뒤 fixed-test parity와 동일 입력 반복 검증 수행
