# T4-E016 컬럼별 값 정합성 재점검

- 날짜: 2026-05-15
- 상태: 완료
- 연결 가설: T4-C1~T4-C7
- 목적: `cleaned_v2` 전체 컬럼에서 값이 컬럼 의미에 맞게 들어갔는지 재검토

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_cleaned_v2.csv`
- 전체 rows: `54,842`
- 전체 columns: `94`
- 학습 후보 rows: `34,239`

## 2. 검증 방법

- 숫자형 컬럼 검증
  - 숫자로 변환 가능한지 확인
  - 음수, 0 이하, 과도한 크기 등 범위 이상 여부 확인
- 필수 컬럼 검증
  - 가격, 크기, 작가명, 재료, 제목 등 핵심 컬럼 결측 여부 확인
- 범주형 컬럼 검증
  - 출처, 통화, 재료 구분, 지지체 구분, 갤러리 감사 상태의 허용값 확인
- boolean 컬럼 검증
  - `true` / `false` 외 값이 들어갔는지 확인
- URL 컬럼 검증
  - `http://` 또는 `https://` 형식인지 확인
- 파생값 재계산 검증
  - `ln_price_krw = log(price_krw)`
  - `area_cm2 = width_cm * height_cm`
  - `log_area = log(area_cm2)`
  - `aspect_ratio = 긴 변 / 짧은 변`
  - `artist_works_log = log1p(artist_works_count_in_cleaned)`
  - `medium_support_bucket = medium_category + support_category`
  - `is_training_candidate`와 `cleaning_exclude_reasons` 일치 여부

## 3. 결과

- 이슈가 있는 컬럼: `8`
- 학습 후보 중 한글 작가명 누락: `0`
- 학습 후보 중 `medium_category=unknown`: `26`
- 학습 후보 중 `support_category=unknown`: `2,786`
- 파생값 계산 불일치: `0`

## 4. 주요 이슈

| 컬럼 | 이슈 | 해석 |
|---|---:|---|
| `price_krw` | `18,928` | 가격 없는 row이며 학습 후보에서는 제외됨 |
| `width_cm` | `133` | 결측 `97`, 1000cm 초과 `36` |
| `height_cm` | `132` | 결측 `93`, 1000cm 초과 `39` |
| `area_cm2` | `33` | 1,000,000cm2 초과 대형/단위 의심 row |
| `medium_raw` | `28` | 재료 원문 누락 |
| `depth_cm` | `15` | 1000cm 초과 깊이값 |
| `aspect_ratio` | `2` | 비율 100 초과 극단값 |
| `artist_name_ko` | `2` | 숫자형 작가명으로 한글명 매핑 불가 |

## 5. 판단

- 클렌징 후 파생값 계산은 재현 가능하게 정리됨
- 가격 결측 row는 학습 후보에서 제외되므로 모델 학습 오염 위험은 낮음
- 크기 1000cm 초과, 면적 과대, 극단 비율 row는 단위 오류 가능성이 있어 추가 샘플 리뷰 필요
- `support_category=unknown`이 학습 후보에 `2,786`건 남아 있어 지지체 피처 사용 시 별도 unknown 처리 또는 추가 매핑 필요
- 한글 작가명은 학습 후보 기준 누락이 없어 현재 split 사용에는 문제 없음

## 6. 산출물

- 컬럼별 감사 리포트: `docs/track4_column_value_consistency_audit.md`
- 컬럼별 요약 CSV: `data/track4_column_value_consistency_audit.csv`
- 이슈 샘플 CSV: `data/track4_column_value_issue_samples.csv`
- 실행 스크립트: `scripts/track4/audit_column_value_consistency.py`

## 7. 다음 작업

- 크기 1000cm 초과 샘플을 원본 URL/원문 기준으로 수동 확인
- `support_category=unknown` 감소를 위한 지지체 매핑 룰 보완
- 가격 결측 row는 예측 대상 후보로 남길지, 학습/평가 데이터에서 완전 제외할지 정책 고정
