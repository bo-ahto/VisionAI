# PP-H11D Phase 1 — 검색 문맥 카운트 중복 부풀림 영향도 측정

- 작성일: 2026-06-14
- 데이터: `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv` (89작가, has_result 2,220행)
- 측정: 작가별 문맥 카운트를 raw / url_unique / domain_unique / title_cluster(토큰 Jaccard≥0.6) 4기준 재집계

## 핵심 결과

| 문맥 | url_unique 제거율 | title_cluster 제거율 | domain_unique 제거율 |
|---|---|---|---|
| art | 13.8% | 14.8% | 45.5% |
| **exhibition** | **12.7%** | **12.4%** | 37.1% |
| gallery | 12.0% | 14.1% | 43.6% |
| market | 4.7% | 10.2% | 29.3% |

- has_result 행의 **14.1%가 완전 동일 URL 중복**(같은 작가+URL). 같은 기사가 여러 query template/provider 결과로 중복 수집됨 (235 작가+URL 쌍이 2개 이상 템플릿에 등장).

## 해석 — 가설 일부 반전

1. **사용자 우려(서로 다른 언론사가 같은 전시를 다룸)는 실제로는 작은 효과.** title_cluster(의미적 군집) 제거율이 url_unique(단순 URL 중복)와 거의 동일(전시 12.4% vs 12.7%). 즉 **다른 출처가 같은 전시를 다뤄 추가로 부풀리는 양은 URL 중복 제거 이상으로는 거의 없음**.

2. **진짜 부풀림 원인은 "완전 동일 기사의 중복 수집"(exact-URL dup, ~14%)**. 현재 파이프라인은 이 중복을 `--merge-with-latest` 시에만 제거하고, 단일 스냅샷 빌드 시에는 제거하지 않음 → 카운트가 12~14% 과대.

3. **domain_unique(30~46% 제거)는 과교정.** 한 언론사가 서로 다른 전시 3건을 보도해도 1건으로 뭉개므로 신호를 깎아먹음. 채택 부적절.

## 권고

- **URL 단위 무조건 dedup**을 `build_snapshot` 카운팅 전에 적용 (작가+URL 중복 1건 처리). 명백히 옳고(같은 기사가 2~3번 세지는 건 오류), ~12~14% 과대 해소, 서로 다른 전시를 잘못 병합할 위험 없음.
- 의미적(같은 전시) 군집 dedup은 URL dedup 대비 추가 이득 미미 + 과병합 위험 → **비채택**.

## 다음 (Phase 2~3)

- Phase 2: `build_snapshot`에 URL dedup 반영 → operational/pilot 스냅샷 재생성, 피처 분포 비교.
- Phase 3: dedup 피처를 **동결 Cold 모델에 그대로 통과**시켜 예측 변화 validation에서 측정(재학습 전). 로그 압축+±0.2 cap 때문에 가격 영향은 작을 것으로 예상 — 유의하면 재학습 권고, 미미하면 파이프라인 정정만 유지.
