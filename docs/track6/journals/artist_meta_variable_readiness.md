# Track6 작가 변수 실험 가능성 점검

- 기준 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 점검 기준일: 2026-05-19
- 목적: 작가 관련 변수 중 학습/테스트를 바로 진행할 수 있는 변수만 실험 일지에 남김

## 판정 기준

- 사용 가능: 값 존재율 20% 이상, 고유값 2개 이상
- 보류: 값 존재율 20% 미만 또는 고유값 1개 이하
- 예외: `artist_works_log`는 수집값이 아니라 데이터셋에서 작가별 작품 수를 계산한 생성 변수이므로 Warm 전용으로 두고 Cold에서는 제외

## 사용 가능 변수

| 변수 | 값 존재율 | 고유값 수 | 판단 | 비고 |
|---|---:|---:|---|---|
| `artist_works_log` | 100.0% | 158 | 사용 가능 | 작가별 데이터 보유 작품 수 생성 변수, Warm 전용 |
| `artist_meta_birth_year` | 52.7% | 96 | 사용 가능 | 결측 구간 성능 별도 확인 필요 |
| `artist_meta_career_stage` | 39.6% | 412 | 사용 가능 | 구간값 품질 확인 필요 |
| `artist_meta_nationality` | 59.9% | 57 | 사용 가능 | 한글 국적 대신 원본 국적 사용 |
| `artist_meta_total_works` | 94.4% | 193 | 사용 가능 | 출처 편향 확인 필요 |
| `artist_meta_for_sale_works` | 54.8% | 104 | 사용 가능 | 시점 의존성 확인 필요 |
| `artist_meta_followers` | 94.4% | 304 | 사용 가능 | 플랫폼 의존성 확인 필요 |
| `artist_meta_is_p1` | 94.4% | 2 | 사용 가능 | 출처 편향 확인 필요 |

## 보류 변수

| 변수 | 값 존재율 | 고유값 수 | 보류 이유 | 후속 조치 |
|---|---:|---:|---|---|
| `artist_meta_career_age` | 0.0% | 0 | 값이 없음 | 생년 또는 활동 시작 연도 기준으로 재생성 필요 |
| `artist_meta_nationality_ko` | 3.7% | 49 | 결측이 너무 많음 | `artist_meta_nationality` 한글 변환 로직 보완 후 재검토 |
| `artist_meta_has_international` | 39.6% | 1 | 값 종류가 1개뿐임 | 생성 기준 재점검 필요 |
| `artist_meta_for_sale_ratio` | 39.6% | 1 | 값 종류가 1개뿐임 | 계산 로직 재점검 필요 |

## 현재 일지 반영 상태

- 진행 대상 인덱스: `docs/track6/journals/variable_screening.html`
- 진행 대상 작가 변수 일지:
  - `T6-E067`: `artist_works_log` - 작가별 데이터 보유 작품 수 생성 변수
  - `T6-E073`: `artist_meta_birth_year`
  - `T6-E075`: `artist_meta_career_stage`
  - `T6-E076`: `artist_meta_nationality`
  - `T6-E078`: `artist_meta_total_works`
  - `T6-E079`: `artist_meta_for_sale_works`
  - `T6-E081`: `artist_meta_followers`
  - `T6-E082`: `artist_meta_is_p1`

## 운영 판단 원칙

- 작가 메타는 성능 개선이 확인될 때만 결측 처리와 추가 수집을 검토한다.
- 메타 정보가 있는 작품만 골라 학습하거나 평가하지 않는다.
- 전체 / 메타 있음 / 메타 없음 구간을 나눠 성능을 기록한다.
- 출처 편향이 큰 변수는 성능이 좋아도 최종 채택 전에 운영 재현 가능성을 별도 확인한다.
