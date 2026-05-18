# Track 5 실험 리스크 점검

- 작성일: 2026-05-18
- 목적: Track3/Track4에서 지적된 평가 방식 문제와 유사한 리스크가 Track5에도 남아 있는지 점검
- 기준: 현재 Track5 split, 실험 스크립트, 실험 결과 문서
- 결론: Track5는 1작가 1작품 문제를 상당 부분 보완했고, 추가 감사 실험 T5-E022~T5-E025로 주요 리스크를 재검증함

## 1. 요약 결론

- Track5는 Track3/Track4보다 split 구조가 개선됨
  - Warm test가 `511건 / 215명`
  - Warm test 작가당 평가 row 중앙값 `3건`
  - Cold test가 `2,896건 / 216명`
  - Cold test 작가당 평가 row 중앙값 `6건`
- 그러나 아래 리스크는 남아 있음
  - Warm test에도 작가당 1작품만 평가된 작가가 일부 있음
  - Warm/Cold 모두 고정 split 1회 기준 결과가 많음
  - Cold는 `artist_key` 기준으로는 분리됐지만 한글 작가명 중복이 일부 있음
  - test 결과를 사용해 정책/후처리 결론을 만든 실험이 있음
  - 작가 가격 통계 피처는 날짜 기준 temporal-safe 검증이 아직 아님

## 2. split 구조 점검

| split | rows | artists | 작가당 rows min | 중앙값 | 평균 | max | 1작품 작가 수 |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 29,216 | 1,844 | 1 | 6.0 | 15.84 | 696 | 264 |
| val_warm | 221 | 86 | 1 | 3.0 | 2.57 | 3 | 5 |
| test_warm | 511 | 215 | 1 | 3.0 | 2.38 | 3 | 30 |
| val_cold | 1,278 | 97 | 1 | 6.0 | 13.18 | 218 | 10 |
| test_cold | 2,896 | 216 | 1 | 6.0 | 13.41 | 153 | 33 |

### 판단

- Track5는 “전체 Warm 평가가 작가당 1작품”인 구조는 아님
- 다만 Warm test 내 `30명`은 평가 작품이 1건뿐임
- 최종 보고에서는 아래를 함께 표시해야 함
  - 전체 Warm 성능
  - 작가당 평가 row 수별 성능
  - train에 남은 작품 수별 성능

## 3. Warm low-history 리스크

| split | 최소 train 작품 수 | train 작품 수 중앙값 | train 2건 이하 rows | train 5건 이하 rows | train 5건 이하 작가 수 |
|---|---:|---:|---:|---:|---:|
| val_warm | 3 | 16.0 | 0 | 17 | 11 |
| test_warm | 2 | 12.0 | 3 | 97 | 63 |

### 판단

- Track5는 Warm 평가 작가도 train에 최소 2작품 이상 남기도록 구성됨
- 하지만 test_warm의 `97건`은 train 작품 수가 5건 이하인 저이력 구간임
- Warm 전체 성능이 좋아도 저이력 작가 구간에서 별도 성능 확인이 필요함

### 보완 필요

- Warm 성능을 train 작품 수 구간별로 분해
  - `2~5건`
  - `6~10건`
  - `11~30건`
  - `31건 이상`
- 저이력 구간에서 작가명/작가 통계 피처가 과하게 작동하는지 확인

## 4. Cold 작가 분리와 이름 중복 리스크

| split | artist_key train 겹침 | artist_name_ko 겹침 | artist_name_ko_orig 겹침 |
|---|---:|---:|---:|
| val_cold | 0 | 8 | 12 |
| test_cold | 0 | 9 | 14 |

### 판단

- Cold는 `artist_key` 기준으로 train과 완전히 분리됨
- 그러나 한글 표시명 기준으로는 일부 겹침이 있음
- 원인은 동명이인/표기 통합 가능성이 있음
- 운영에서는 artist_key 없이 이름 입력을 받을 가능성이 있으므로, `artist_key`만 기준으로 Cold를 정의하면 운영 시나리오와 차이가 날 수 있음

### 보완 필요

- Cold 평가를 두 기준으로 나누어 다시 확인
  - 엄격 Cold: `artist_key`도 없고 한글명도 train에 없음
  - 이름 중복 Cold: `artist_key`는 없지만 한글명이 train에 있음
- 이름 중복 Cold의 성능이 다르면 운영 routing 기준을 보완해야 함

## 5. 작가 피처 영향 분해 리스크

### 현재 상태

- T5-E003에서 작가 피처 ablation을 수행함
- T5-E008 이후 Warm 최종 후보는 작가 key, 작가 작품 수, 작가 가격 통계가 포함됨
- Warm 성능 개선의 상당 부분은 작품 구조 정보보다 작가 정보에서 나옴

### 문제 가능성

- 성능이 “작품 가격 예측”이라기보다 “작가별 평균 가격대 기억”에 가까울 수 있음
- 운영에서 해당 작가의 충분한 과거 가격 데이터가 없으면 성능이 약해질 수 있음
- 작가명 피처와 작가 가격 통계 피처의 기여도를 최종 후보 기준으로 다시 분리해야 함

### 보완 필요

- 최종 Warm 후보 기준으로 아래 모델을 같은 split에서 비교
  - 작품 구조 only
  - 구조 + artist_key
  - 구조 + artist_works_log
  - 구조 + artist 가격 통계
  - 최종 후보 전체
- 결과를 train 작품 수 구간별로 함께 확인

## 6. test 재사용 리스크

### 해당 실험

- T5-E010
  - 최종 후보 test 확인
  - 의도에 맞음
- T5-E012
  - test_cold 예측으로 위험 구간 분석
  - 진단용으로는 가능하지만 정책 선택 근거로 쓰면 test 재사용 위험
- T5-E013
  - validation 오차로 범위를 만들고 test coverage 확인
  - 의도에 맞음
- T5-E018
  - validation 보정값을 test에 적용
  - 의도에 맞음
- T5-E020
  - test_cold에서 standard/caution 정책을 비교하고 hybrid 정책을 선택
  - 정책 선택에 test를 사용한 형태라 최종 성능으로 그대로 보고하면 위험

### 판단

- T5-E020의 hybrid 정책은 좋은 신호지만, test에서 정책을 고른 결과이므로 최종 확정 전 validation 기반 정책으로 재정의해야 함

### 보완 필요

- 정책 정의는 validation에서 결정
- test는 validation에서 고정한 정책을 최종 확인하는 용도로만 사용
- 필요하면 새로운 holdout 또는 반복 split으로 정책 안정성 확인

## 7. 반복 split 부족 리스크

### 현재 상태

- Track5는 split 구조 자체는 개선됨
- 하지만 대부분의 성능 결론은 고정 validation/test 1회 기준임

### 문제 가능성

- 특정 Warm 작가 조합 또는 Cold 작가 조합에 성능이 의존할 수 있음
- Cold 성능이 작가 구성에 따라 튈 가능성이 여전히 있음

### 보완 필요

- Warm 반복 holdout
  - 여러 seed
  - 작가당 2~3작품 holdout
  - train 최소 2작품 유지
- Cold 반복 artist split
  - 여러 seed
  - cold artist set을 다시 구성
  - median APE 평균/표준편차 확인

## 8. temporal-safe 작가 통계 리스크

### 현재 상태

- 작가 가격 통계는 train 전체 기준으로 계산됨
- Track5 split에는 시간 순서 검증이 명확히 반영되어 있지 않음

### 문제 가능성

- 실제 운영에서는 예측 시점 이후 거래 정보가 작가 통계에 포함되면 안 됨
- 현재 방식은 split 기준 누수는 막지만 시간 기준 누수까지 보장하지는 않음

### 보완 필요

- 거래일/등록일 컬럼 확보 여부 확인
- 날짜가 있으면 예측 시점 이전 정보만 사용해 작가 통계 재계산
- 날짜가 없으면 작가 가격 통계는 “성능 후보”로 두고 운영 확정은 보류

## 9. 실험 관리상 보완 필요 항목

- H5, H6, H7이 아직 `예정`으로 남아 있음
  - 실제 후속 실험 일부가 H10 이후에서 대체했으나 상태표 정리가 필요함
- E012, E020처럼 test 기반 진단/정책 실험은 문서에서 “진단용”과 “최종 검증용”을 구분해야 함
- 최종 artifact 생성 전 아래 세 실험을 먼저 수행하는 것이 안전함
  - T5-E022: Warm/Cold 반복 split 안정성 검증
  - T5-E023: Warm 작가 피처 영향 분해 및 저이력 구간 검증
  - T5-E024: Cold 이름 중복/엄격 Cold 분리 검증

## 10. 권장 보완 실험

| 우선순위 | 실험 | 목적 | 판단 기준 |
|---:|---|---|---|
| 1 | Warm 반복 holdout | Warm 성능이 특정 split에 의존하는지 확인 | median APE 평균/표준편차 안정 |
| 2 | Cold 반복 artist split | Cold 성능 튐 여부 확인 | median APE와 p95의 seed별 변동 확인 |
| 3 | Warm 작가 피처 영향 분해 | 작가명 때문에 나온 성능인지 분리 | 구조 only 대비 각 작가 피처 개선량 |
| 4 | Warm 저이력 구간 평가 | train 작품 수가 적은 작가의 성능 확인 | train count bucket별 median/p95 |
| 5 | Cold 엄격 이름 기준 평가 | 운영에서 이름만 입력될 때의 Cold 정의 확인 | 이름 중복 cold vs 엄격 cold 성능 차이 |
| 6 | validation 기반 정책 재선정 | test 재사용 리스크 제거 | validation에서 정책 고정 후 test 확인 |

## 11. 상사 피드백에 대한 현재 답변 방향

- Track5는 Track3/Track4의 1작가 1작품 문제를 줄이기 위해 split을 보완했음
- 그러나 최종 운영 후보 확정 전에는 아래를 추가 검증하겠다고 답하는 것이 맞음
  - 반복 split 안정성
  - 작가 피처 영향 분해
  - low-history Warm 성능
  - Cold 이름 기준 분리
  - test 재사용 없는 정책 검증

## 12. 보완 실험 실행 결과

- T5-E022 반복 split 안정성 검증
  - Warm median APE 평균 `0.1668`, 범위 `0.1496~0.1786`
  - Cold median APE 평균 `0.4144`, 범위 `0.3944~0.4416`
  - Warm/Cold 분리 방향은 유지 가능
  - Cold p95는 seed별 변동이 커서 tail risk가 남음
- T5-E023 Warm 작가 피처 영향 분해
  - 구조-only median APE `0.4517`
  - 작가 key 포함 median APE `0.1601`
  - full_size median APE `0.1617`
  - Warm 성능은 작가 식별 정보 의존이 크며, 운영에서는 작가명 매칭 품질이 중요함
- T5-E024 Cold 이름 중복 검증
  - artist_key 기준 train 겹침 `0`
  - 이름 중복 `126행 / 15명`
  - strict cold median APE `0.3928`
  - 이름 중복이 Cold 성능을 만든 주원인은 아님
- T5-E025 validation 기반 정책 재선정
  - test baseline median APE `0.3918`
  - validation 선택 hybrid median APE `0.4055`
  - T5-E020의 가격 보정 정책은 최종 미채택

## 13. 현재 결론

- Track5 결과는 Track3/Track4보다 신뢰도가 높음
- 1작가 1작품 문제는 Track5에서 상당 부분 완화됨
- Warm 모델은 작가 식별 정보 의존이 크므로 작가명 정규화/동명이인 처리가 운영 핵심 리스크임
- Cold 모델은 baseline 자체는 유지 가능하지만 tail risk가 크므로 단일 가격만 제시하는 방식은 위험함
- Cold 가격 보정 후처리는 validation 기반 재검증에서 실패했으므로 최종 정책에서 제외함
- 다음 단계는 최종 artifact 생성 전 `strict cold 병행 보고`, `작가명 매칭 검증`, `Cold 위험 경고 정책`을 명시하는 것임
