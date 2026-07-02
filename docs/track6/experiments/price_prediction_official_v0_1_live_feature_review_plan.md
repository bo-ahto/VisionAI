# 공식 v0.1 외부 데이터 검수 및 승격 계획

- 작성일: 2026-06-12
- 적용 범위: 가격 예측 공식 테스트 v0.1의 Cold 신규 입력 외부 피처 수집 경로
- 현재 상태: 검수 큐 구축 완료, 승인 후보만 feature cache로 승격하는 정책 확정 필요

## 1. 결론

- 외부 검색/전시/갤러리/판매가 데이터는 수집 즉시 예측 feature cache에 넣지 않는다.
- 모든 신규 수집 후보는 먼저 `external_feature_review_queue`에 저장한다.
- 검수 상태가 `approved_baseline` 또는 검수자가 `approved`로 확정한 후보만 운영 feature cache 승격 대상이다.
- `needs_human_review`, `needs_improvement`, `needs_review`, `auto_reject_duplicate` 상태의 후보는 예측 계산에 사용하지 않는다.
- 중복 데이터와 개선 데이터는 같은 큐에서 구분하되, 승격 기준은 분리한다.
- 작가 식별자가 잘못 분리된 상태에서는 외부 피처 승격 판단도 흔들리므로, `artist_identity_review_queue`의 동일 작가 분리 후보 검수를 외부 피처 승격보다 먼저 처리한다.

## 2. 전체 검수 흐름

```text
1. 외부 데이터 수집
   - 작가명, 전시, 갤러리, 검색 결과, 실제 판매가 후보 수집

2. 정규화
   - 작가명 공백/기호/대소문자 제거
   - URL fragment 제거
   - source payload를 정렬된 JSON으로 변환 후 hash 생성

3. 작가 식별자 이관 품질 확인
   - 같은 정규화 작가명이 여러 `artist_key`로 분리됐는지 확인
   - 생년, 국적, 가격 이력 수, 대표 작품을 비교해 잘못 분리된 동일 작가 후보를 선별
   - 생년이 충돌하는 후보는 자동 병합하지 않고 사람 검수 대상으로 유지

4. 중복 판정
   - 같은 작가 안에서 같은 URL 반복 여부 확인
   - 여러 작가에 같은 URL이 반복되는지 확인
   - 같은 정규화 작가명이 여러 artist_key에 매핑되는지 확인
   - 같은 source hash가 이미 존재하는지 확인

5. 개선 판정
   - 기존 cache보다 전시/갤러리/출처 수가 늘었는지 확인
   - 검색 품질 점수와 evidence 수가 개선됐는지 확인
   - 실제 판매가처럼 학습에 직접 도움이 되는 신규 정보인지 확인
   - 동명이인/출처 충돌/품질 부족 여부 확인

6. 검수 큐 저장
   - `external_feature_review_queue`에 후보와 판정 사유 저장
   - 자동 승인, 개선 필요, 사람 검수 필요, 자동 중복 제외로 분류

7. 검수 결정
   - 검수자가 승인/반려/보류 결정
   - 결정 이력은 `external_feature_review_decisions`에 저장

8. 운영 cache 승격
   - 승인 후보만 artist external feature cache 또는 학습 후보로 승격
   - 반려/중복/개선 필요 후보는 운영 예측에 반영하지 않음
```

## 3. 작가 식별자 이관 품질 감사

```text
python3 scripts/track6/audit_official_v0_1_artist_identity_migration.py
```

| 항목 | 건수 |
|---|---:|
| 충돌 alias 그룹 | 92 |
| 높은 확률의 잘못 분리 후보 | 68 |
| 추가 확인 필요한 분리 후보 | 3 |
| 분리 유지 또는 확인 전 보류 후보 | 5 |
| 전체 분리 손실 가격 이력 수 | 603 |
| 높은 확률의 잘못 분리 후보 분리 손실 가격 이력 수 | 476 |

- 원인: DB 구축 시 원본 `artist_key`를 그대로 사용하면서 영문 표기 순서, 띄어쓰기, 한글/영문 혼합 표기 차이가 canonical artist_key로 합쳐지지 않았다.
- 예시: `전영진`이 `youngjin jun`, `youngjin jun 전영진`으로 분리됐고, 생년 1983년과 가격 이력 172건 기준으로 동일 작가 병합 검수 후보에 해당한다.
- 반례: `김한나`, `구자현`처럼 생년이 서로 다른 후보는 실제 동명이인 가능성이 있으므로 자동 병합하지 않는다.
- 현재 처리: 자동 병합 없이 `artist_identity_review_queue`에 후보와 근거만 저장했다.
- 운영 순서: 이 큐에서 동일 작가 병합 여부를 먼저 확정한 뒤, 외부 피처 cache 승격과 live 수집 보강을 진행한다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_artist_identity_migration_audit/artist_identity_review_queue.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_migration_audit.md`
- DB table: `artist_identity_review_queue`, `artist_identity_review_decisions`

### 3.1 작가 식별자/외부 피처 검수 우선순위

```text
python3 scripts/track6/prioritize_official_v0_1_identity_and_external_review.py
```

| 우선순위 | 건수 | 의미 |
|---|---:|---|
| `P0_identity_merge_first` | 40 | 동일 작가 분리 가능성이 높고 이력 손실 또는 예측 영향이 커서 먼저 검수 |
| `P1_identity_merge_review` | 19 | 동일 작가 분리 가능성이 높아 병합 검수 필요 |
| `P2_human_review_before_promotion` | 22 | 실제 동명이인/출처 충돌 가능성이 있어 외부 피처 승격 전 사람 검수 필요 |
| `P3_keep_or_low_impact_review` | 1 | 영향이 낮거나 분리 유지 가능성이 높아 후순위 |

- 우선순위 단위: alias 충돌 row가 아니라 같은 작가키 묶음을 공유하는 alias를 합친 고유 작가키 묶음.
- 최우선 순서: `P0_identity_merge_first` 40건 검수 → canonical artist_key dry-run → 외부 피처 승격 후보 재산정.
- 이유: 동일 작가가 분리된 상태에서 외부 피처를 승격하면 같은 작가의 이력과 전시/갤러리 피처가 서로 다른 artist_key에 흩어진 상태로 유지된다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_identity_external_review_priority/identity_external_review_priority.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_identity_external_review_priority.md`

### 3.2 canonical artist_key 병합 dry-run

```text
python3 scripts/track6/build_official_v0_1_artist_identity_merge_dry_run.py
```

| 항목 | 건수 |
|---|---:|
| 병합 component | 57 |
| 병합 대상 source artist_key | 60 |
| 재배치될 가격 이력 수 | 425 |
| 재배치될 관측 row 수 | 425 |
| 예상 `artist_registry` row 수 | 1,773 -> 1,713 |

- 실제 DB는 수정하지 않았다.
- P0/P1 후보 중 겹치는 그룹은 연결 component로 합쳐 한 artist_key가 여러 canonical으로 이동하지 않게 했다.
- dry-run 결과 생년 충돌 component는 없지만, 실제 적용 전 대표 작품/국적/외부 출처 확인은 필요하다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_dry_run/artist_identity_merge_components_dry_run.csv`
- `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_dry_run/artist_identity_merge_map_dry_run.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_merge_dry_run.md`

### 3.3 병합 shadow DB 영향 감사

```text
python3 scripts/track6/build_official_v0_1_artist_identity_merge_shadow_db.py
```

| 항목 | 값 |
|---|---:|
| 평가 병합 component | 57 |
| 단일 작가 후보로 정리되는 component | 57 |
| 작가 후보 수가 감소하는 component | 57 |
| 기존 최대 이력 대비 증가 이력 합계 | 425 |
| 운영 DB 수정 여부 | 미수정 |

- shadow DB에만 병합 map을 적용했다.
- 작가 후보 중복은 P0/P1 component 57건 모두 단일 후보로 정리된다.
- 같은 작가 가격 이력은 기존 대표 artist_key 기준보다 총 425건 증가한다.
- 단, 유사작품 통계 cache는 병합 후 완전 재집계가 필요하므로 이 결과는 최종 예측값 영향이 아니라 작가 식별자와 이력 수 영향 확인 결과다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_shadow/price_prediction_v0_1_identity_merge_shadow.sqlite`
- `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_shadow/artist_identity_merge_shadow_impact.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_merge_shadow.md`

### 3.4 병합 후 cache 재집계 dry-run

```text
python3 scripts/track6/rebuild_official_v0_1_artist_identity_post_merge_caches.py
```

| 항목 | 병합 전 | 재집계 후 | 변화 |
|---|---:|---:|---:|
| `artist_registry` | 1,773 | 1,713 | -60 |
| `artist_aliases` | 3,600 | 3,530 | -70 |
| `artist_profile_snapshots` | 1,773 | 1,713 | -60 |
| `similar_artwork_stats_cache` | 9,421 | 9,285 | -136 |
| `similar_artist_cache` | 8,388 | 8,212 | -176 |

- 운영 DB는 수정하지 않았다.
- 병합 후보를 반영한 shadow DB에서 alias 중복 제거, 작가 프로필 재생성, 유사작품 통계 재집계, 유사작가 cache 재집계, 외부 피처 cache 후보 재생성을 완료했다.
- 병합 후 외부 피처 cache 후보 작가 수는 1,713명이다.
- 다음 단계는 재집계 shadow DB 기준 예측 영향 감사와 외부 피처 promotion impact 재실행이다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild/price_prediction_v0_1_post_merge_cache_rebuild_shadow.sqlite`
- `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild/official_v0_1_artist_external_feature_cache_post_merge_candidate.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_post_merge_cache_rebuild.md`

### 3.5 재집계 shadow DB 기준 예측 영향 감사

```text
python3 scripts/track6/audit_official_v0_1_artist_identity_post_merge_prediction_impact.py
```

| 항목 | 값 |
|---|---:|
| 평가 component | 57 |
| 병합 후 alias 단일 resolve | 57 |
| alias review_required | 57 -> 0 |
| alias `review_required -> warm` | 51 |
| direct route 변경 | 2 |
| direct 가격 변동 row | 2 |
| direct 고영향 row | 1 |

- 운영 DB는 수정하지 않았다. 예측 호출은 감사용 복사 DB에서만 실행했다.
- 병합 후 작가명 기반 후보 중복은 57건 모두 단일 후보로 정리된다.
- 대부분의 direct 예측가격은 변하지 않았지만, route가 `cold -> warm`으로 바뀌는 2건은 가격이 변했다.
- `이재샘 / jae sam lee` component는 direct 가격 변화가 50% 이상으로 커서 자동 적용 대상에서 제외하고 별도 검수해야 한다.
- 병합 적용 gate에는 `direct_high_impact_rows_abs_delta_gte_50pct = 0` 조건을 추가하는 것이 안전하다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_prediction_impact/artist_identity_post_merge_prediction_impact.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_post_merge_prediction_impact.md`

## 4. 중복 데이터 판정 기준

| 기준 | 상태 | 처리 |
|---|---|---|
| 같은 작가 검색 결과 안에서 같은 URL 반복 | `same_artist_duplicate_url` | `auto_reject_duplicate` |
| 서로 다른 작가 검색 결과에 같은 URL 반복 | `cross_artist_duplicate_url` | `needs_human_review` |
| 정규화 작가명이 여러 artist_key에 매핑 | `artist_name_conflict` | `needs_human_review` |
| 같은 source payload hash가 이미 존재 | hash duplicate | 기존 승인 row와 비교 후 중복 제외 |
| 같은 작품 URL 또는 외부 작품 ID 반복 | source duplicate | 같은 작품이면 중복 제외, 다른 작품이면 사람 검수 |

### 4.1 정규화 기준

```text
정규화 작가명
  = lower(작가명)
  -> 공백 제거
  -> 괄호, 마침표, 따옴표, 하이픈 등 기호 제거

정규화 URL
  = lower(URL)
  -> 앞뒤 공백 제거
  -> #fragment 제거

source hash
  = 정렬된 JSON payload를 SHA1로 변환한 값
```

## 5. 개선 데이터 판정 기준

| 기준 | 상태 | 처리 |
|---|---|---|
| gallery tier, 전시 수, 출처 수가 기존보다 증가 | `baseline_enough` 또는 `needs_review` | 검수 후 승격 가능 |
| 검색 품질 점수 낮음 | `needs_live_collection` | 추가 수집 필요 |
| 전시/갤러리 evidence 없음 | `needs_live_collection` | 추가 수집 필요 |
| 실제 판매가 feedback 추가 | `adds_actual_sale_price` | 사람 검수 후 학습 후보 승격 |
| 동명이인 위험 또는 출처 충돌 | `needs_better_search_evidence` | 사람 검수 필요 |
| 같은 URL 반복으로 정보량 증가 없음 | `duplicate_noise` | 승격 제외 |

## 6. 검수 상태별 운영 정책

| 검수 상태 | 의미 | 운영 반영 |
|---|---|---|
| `approved_baseline` | 현재 cache 기준으로 품질이 충분한 baseline 후보 | 승격 가능 |
| `approved` | 검수자가 승인한 신규/개선 후보 | 승격 가능 |
| `needs_improvement` | 출처/검색 품질/전시 근거가 부족함 | 승격 불가 |
| `needs_human_review` | 동명이인, 작가 충돌, URL 충돌 가능성 있음 | 승격 불가 |
| `needs_review` | 실제 판매가 feedback 등 사람이 봐야 하는 후보 | 승격 불가 |
| `auto_reject_duplicate` | 같은 작가 내부 반복 URL 등 명백한 중복 | 승격 불가 |
| `rejected` | 검수자가 반려한 후보 | 승격 불가 |

## 7. 현재 검수 큐 산출물

```text
python3 scripts/track6/build_official_v0_1_feature_review_queue.py
```

| 항목 | 건수 |
|---|---:|
| 전체 후보 | 2,982 |
| 승인 baseline 후보 | 712 |
| 개선 수집 필요 후보 | 1,075 |
| 사람 검수 필요 후보 | 724 |
| 자동 중복 제외 후보 | 470 |
| 기타 검수 필요 후보 | 1 |

| 중복 판정 | 건수 |
|---|---:|
| unique | 1,789 |
| cross_artist_duplicate_url | 588 |
| same_artist_duplicate_url | 470 |
| artist_name_conflict | 135 |

## 8. API 상태 노출

`GET /api/v1/price-models/current`와 `GET /api/v1/admin/model-audit`에서 아래 항목을 노출한다.

| 항목 | 의미 |
|---|---|
| `artist_identity_review_queue_ready` | 작가 식별자 이관 감사 큐 존재 여부 |
| `artist_identity_conflict_groups` | 같은 정규화 alias에 여러 작가키가 연결된 그룹 수 |
| `artist_identity_likely_false_split_groups` | 잘못 분리됐을 가능성이 높은 동일 작가 병합 검수 후보 수 |
| `artist_identity_merge_review_rows` | 병합 검수 우선 후보 수 |
| `artist_identity_human_review_rows` | 실제 동명이인 가능성 등 사람 검수가 필요한 후보 수 |
| `artist_identity_auto_merge_applied` | 자동 병합 적용 여부. 현재는 항상 `false` |
| `cold_live_feature_review_queue_ready` | 검수 큐 존재 여부 |
| `cold_live_feature_review_queue_rows` | 검수 큐 전체 후보 수 |
| `cold_live_feature_review_pending_rows` | 승격 불가 상태의 검수 대기 후보 수 |
| `cold_live_feature_review_needs_human_rows` | 사람 검수 필요 후보 수 |
| `cold_live_feature_review_needs_improvement_rows` | 추가 수집/개선 필요 후보 수 |
| `cold_live_feature_review_auto_reject_duplicate_rows` | 자동 중복 제외 후보 수 |
| `cold_live_feature_promotion_requires_review` | 승인 없는 cache 승격 금지 여부 |

## 9. 아직 운영 반영하지 않는 이유

- live 외부 수집 pipeline은 아직 운영 cache에 직접 연결하지 않는다.
- 현재 완료된 것은 검수 큐 생성과 현재 DB/cache 기반 중복·개선 후보 분류다.
- 작가 식별자 이관 감사에서 동일 작가가 분리된 후보가 확인됐으므로, 이 후보를 먼저 검수하지 않으면 외부 피처 승격 대상과 Warm/Cold 라우팅 기준이 흔들릴 수 있다.
- 승격 gate 감사는 dry-run으로만 실행하며, 운영 cache를 수정하지 않는다.
- 다음 단계에서 수집기가 신규 후보를 이 큐에만 넣도록 연결한다.
- 그 다음 승인 후보만 cache로 승격하는 promotion script를 만들고, 승격 전후 예측값 변동 감사까지 통과해야 운영 반영한다.

## 10. 승격 gate dry-run 감사

```text
python3 scripts/track6/audit_official_v0_1_feature_review_gate.py
```

| 항목 | 건수 |
|---|---:|
| 승격 dry-run 후보 | 712 |
| 승격 차단 후보 | 2,270 |
| gate 위반 | 0 |

- 승격 후보 조건: `review_status = approved_baseline` 또는 검수 결정 `decision = approved`
- 차단 조건: 중복 URL, 작가명 충돌, 사람 검수 필요, 추가 수집 필요, 실제 판매가 검수 대기
- 산출물: `experiments/track6/PP-OFFICIAL-V01_feature_review_gate_audit/promotion_candidates_dry_run.csv`
- 감사 결과: `docs/track6/experiments/price_prediction_official_v0_1_feature_review_gate_audit.md`

## 11. 작가 단위 외부 피처 cache 승격 후보 생성

```text
python3 scripts/track6/promote_official_v0_1_approved_external_features.py
```

| 항목 | 건수 |
|---|---:|
| 기존 운영 외부 피처 cache | 1,773 |
| 검수 큐의 작가 단위 외부 피처 후보 | 1,773 |
| 승인 조건 통과 후보 | 638 |
| 승격 후보 cache row | 638 |
| 승격 차단 후보 | 1,135 |

- 기본 실행은 dry-run이다.
- 기존 운영 cache 파일은 수정하지 않는다.
- 승인 후보 cache 후보 파일만 생성한다.
- 실제 적용은 `--apply`를 명시한 경우에만 수행한다.
- `--apply` 실행 시 기존 cache를 backup 파일로 먼저 복사한 뒤 교체한다.
- 실제 적용 전에는 승격 전후 예측 영향 감사가 필요하다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion/approved_external_feature_cache_candidate.csv`
- `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion/external_feature_promotion_diff.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_external_feature_promotion.md`

## 12. 승격 전 예측 영향 전체 감사

```text
PYTHONPATH=src python3 scripts/track6/audit_official_v0_1_external_feature_promotion_impact.py --max-artists 0
```

| 항목 | 값 |
|---|---:|
| 평가 대상 | 1,773 |
| 예측값 변화 row | 1,134 |
| 외부 피처 coverage 상실 row | 1,135 |
| 평균 절대 변화율 | 1.40% |
| p95 절대 변화율 | 5.58% |
| 최대 절대 변화율 | 62.27% |
| 5% 초과 변화 row | 296 |

- 현재 운영 cache는 수정하지 않았다.
- 승인 후보 cache를 적용하면 차단된 후보 1,135건은 외부 피처가 missing/default로 바뀔 수 있다.
- 전체 감사에서 coverage 상실과 예측 변동이 확인됐으므로, 바로 `--apply`를 실행하지 않는다.
- 변화폭이 큰 작가는 외부 피처를 제거하기보다 추가 수집/사람 검수로 개선하는 것이 우선이다.

산출물:

- `experiments/track6/PP-OFFICIAL-V01_external_feature_promotion_impact/promotion_impact_rows.csv`
- `docs/track6/experiments/price_prediction_official_v0_1_external_feature_promotion_impact.md`

## 13. 작가명 fallback 오매칭 방어

- 작가키는 정확 매칭에만 사용한다.
- 이름 fallback은 한글 작가명과 영문 작가명에만 적용한다.
- `__MISSING__`, `missing`, `unknown`, `none`, `null`, `nan`, `미상`, `없음`은 이름 fallback 후보에서 제외한다.
- 이유: placeholder 이름이 여러 작가에 반복되면, 승인 후보 cache에 없는 작가가 다른 작가의 외부 피처에 잘못 붙을 수 있다.

## 14. 다음 작업

| 순서 | 작업 | 완료 기준 |
|---|---|---|
| 1 | 작가 식별자 이관 감사 큐 생성 | 완료. `artist_identity_review_queue` 92건 생성 |
| 2 | 동일 작가 분리 후보 검수 | 68건 병합 후보 승인/반려 결정이 `artist_identity_review_decisions`에 남음 |
| 3 | canonical artist_key 병합 적용 dry-run | 완료. 57개 component, 60개 source artist_key 이동 후보 생성 |
| 4 | 병합 shadow DB 영향 감사 | 완료. 57개 component 모두 단일 작가 후보로 정리, 운영 DB 미수정 |
| 5 | 병합 적용 전 cache 재집계 설계 | 완료. alias/profile/similar stats/similar artist/external cache dry-run 완료 |
| 6 | 재집계 shadow DB 기준 예측 영향 감사 | 완료. 57건 단일 resolve, 고영향 가격 변동 1건 별도 보류 필요 |
| 7 | live collector 출력 대상을 feature cache가 아니라 review queue로 고정 | 신규 수집 row가 `external_feature_review_queue`에만 저장 |
| 8 | 검수 UI 또는 CSV 검수 절차 정의 | 승인/반려/보류 결정이 `external_feature_review_decisions`에 남음 |
| 9 | 승인 후보 promotion script 구현 | 완료. 기본 dry-run으로 승인 후보 cache 생성 |
| 10 | 승격 전후 예측 영향 감사 | 완료. 전체 1,773건 기준 영향 확인, 실제 적용 보류 |
| 11 | 운영 배포 전 gate 자동화 | 작가 식별자 미검수/중복/검수 대기/고영향 가격 변동 row가 승격 대상에 포함되면 배포 실패 |
