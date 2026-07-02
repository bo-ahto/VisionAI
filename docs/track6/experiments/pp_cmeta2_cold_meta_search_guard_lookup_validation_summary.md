# PP-CMETA2 Cold 비엄격 lookup 진단 요약

- 실행일: 2026-06-18
- 실험 폴더: `experiments/track6/PP-CMETA2_cold_meta_search_guard_lookup_validation`
- 선행 실험: `PP-CMETA1_cold_operational_meta_search_validation`
- 목적: 운영형 Cold 후보에 q40 보수 후보와 v0.3 작가별 `search_delta_lookup` 후처리를 붙이면 성능이 추가 개선되는지 확인
- 판정: 이 실험은 `artist_key` 기반 lookup을 후처리에 사용하므로 strict Cold 하네스 기준에는 맞지 않는다. 신규 작가 Cold 운영 성능으로 인용하면 안 되고, lookup 효과를 분리해 본 진단용 결과로만 사용한다.

## 1. 검증 방식

PP-CMETA1의 같은 후보 피처셋을 그대로 사용하되, q10/q50/q90에 더해 q40 모델을 추가 학습했다.

비교한 후처리 정책은 네 가지다.

| 정책 | 의미 |
|---|---|
| `base_q50` | LightGBM Quantile q50 예측값 그대로 사용 |
| `lookup_only` | q50에 v0.3 작가별 `search_delta_lookup`만 더함 |
| `guard_only` | q40, q50, q10/q90 폭으로 보수 후보 적용 조건만 사용 |
| `guard_plus_lookup` | guard 적용 후 v0.3 작가별 lookup까지 더함 |

이 실험도 아래 항목은 모델 피처로 쓰지 않았다.

- `artist_key`
- 같은 작가 가격 중앙값/평균/면적단가
- 같은 작가 학습 작품 수

다만 `lookup_only`와 `guard_plus_lookup`은 후처리 단계에서 frozen `search_delta_lookup[artist_key]`를 사용한다. 따라서 이 두 정책은 “artist_key가 매칭되지 않는 Cold”가 아니라 “artist_key lookup이 가능한 진단 조건”이다.

## 2. Test 결과 핵심

| 후보 | 정책 | MdAPE | MAPE | p95 APE | 해석 |
|---|---|---:|---:|---:|---|
| 작품+작가메타+전시/갤러리 | `base_q50` | 0.444391 | 1.129475 | 3.849633 | q50 기준 |
| 작품+작가메타+전시/갤러리 | `lookup_only` | 0.422821 | 0.993299 | 3.390348 | MdAPE 최상위 |
| 작품+작가메타+전시/갤러리 | `guard_plus_lookup` | 0.433833 | 0.964857 | 2.908443 | p95 방어 개선 |
| 작품+작가메타+검색+전시/갤러리 | `base_q50` | 0.442147 | 1.048405 | 3.353732 | q50 기준 |
| 작품+작가메타+검색+전시/갤러리 | `lookup_only` | 0.431277 | 0.928508 | 3.138994 | MAPE 개선 |
| 작품+작가메타+검색+전시/갤러리 | `guard_plus_lookup` | 0.435616 | 0.902715 | 2.876001 | MAPE/p95 최상위권 |

## 3. 결론

lookup 후처리는 fixed test 진단 조건에서는 추가 개선 효과가 있다.

`PP-CMETA1`의 최상위 순수 운영형 후보인 `작품+작가메타+검색+전시/갤러리` 기준으로 보면:

- `base_q50`: `0.442147 / 1.048405 / 3.353732`
- `lookup_only`: `0.431277 / 0.928508 / 3.138994`
- `guard_plus_lookup`: `0.435616 / 0.902715 / 2.876001`

즉 lookup만 더하면 MdAPE와 MAPE가 개선되고, guard까지 같이 쓰면 MdAPE는 lookup-only보다 조금 나빠지지만 MAPE와 p95 APE는 더 좋아진다.

단, 아래 선택 기준은 strict Cold 운영안이 아니라 lookup이 가능한 진단 조건 안에서만 유효하다.

- 중앙값 정확도 우선: `작품+작가메타+전시/갤러리 + lookup_only`
- MAPE/p95 큰 오차 방어 우선: `작품+작가메타+검색+전시/갤러리 + guard_plus_lookup`

## 4. 현재 v0.3과의 관계

PP-CMETA2 최상위 후보도 현재 v0.3 최종 성능에는 아직 못 미친다.

| 모델/정책 | MdAPE | MAPE | p95 APE |
|---|---:|---:|---:|
| 현재 Cold v0.3 guard+search | 0.409820 | 0.849260 | 2.346465 |
| PP-CMETA2 MdAPE 최상위 | 0.422821 | 0.993299 | 3.390348 |
| PP-CMETA2 MAPE/p95 균형 후보 | 0.435616 | 0.902715 | 2.876001 |

따라서 PP-CMETA2는 v0.3 즉시 대체 후보도, strict Cold 운영 후보도 아니다. v0.3의 lookup 의존 효과가 어느 정도인지 확인한 비엄격 진단 결과로만 보는 것이 맞다.

## 5. 운영상 주의

이번 fixed Cold test에서는 v0.3 lookup coverage가 `1.0`이다. 즉 평가 대상 작가가 모두 frozen lookup에 있었다.

실제 신규 작가 Cold에서는 lookup이 없을 수 있다. 이 경우 lookup delta는 0으로 fallback되므로, fixed test에서 본 lookup 개선이 그대로 재현되지 않을 수 있다.

운영 적용을 위해서는 아래 검증이 추가로 필요하다.

- 신규 작가 live search로 lookup과 동등한 보정값을 생성할 수 있는지 검증
- lookup 미커버 작가에서 `base_q50`, `guard_only`, `guard_plus_lookup` fallback 성능 검증
- live search 피처와 학습 피처의 분포 차이 검증
- 작가명 매칭 오류 또는 동명이인일 때 lookup을 적용하지 않는 차단 정책 검증

## 6. 권장안

현재 기준 권장안은 아래와 같다.

1. 공식 운영 Cold는 당장 v0.3을 대체하지 않는다.
2. strict Cold 운영 후보는 `PP-CMETA1` 및 lookup 없는 `base_q50`/`guard_only` 결과로만 판단한다.
3. PP-CMETA2는 lookup 효과 진단으로만 보관하고, 운영 후보 표에서는 제외하거나 “비엄격 진단”으로 표시한다.
4. 문서에서는 v0.3을 “artist_key lookup 가능한 보고 기준”으로, PP-CMETA1을 “작가 가격 이력 없이 메타/검색으로 예측하는 strict Cold 후보”로 분리 설명한다.
5. 다음 검증은 신규 작가 live search 수집 파이프라인을 붙인 뒤, artist_key lookup 없이 성능이 유지되는지 확인하는 것이다.
