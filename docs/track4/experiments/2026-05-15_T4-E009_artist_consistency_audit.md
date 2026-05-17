# T4-E009 작가명/작가 메타데이터 정합성 감사

- 날짜: 2026-05-15
- 연결 가설: T4-C4
- 상태: 완료
- 목적: Track 4 원본 보존 통합본에서 Warm/Cold split 기준이 되는 작가 식별값과 작가 메타데이터 피처 후보를 분리해서 점검

## 1. 사용 데이터

- 입력 데이터: `data/track4_primary_market_raw_collected.csv`
- 입력 행 수: `54,842`
- 감사 결과 CSV: `data/track4_artist_consistency_audit.csv`
- 감사 요약 JSON: `data/track4_artist_consistency_audit_summary.json`
- 요약 문서: `docs/track4/audits/artist_consistency_audit.md`

## 2. 실행 방법

- 스크립트: `scripts/track4/audit_artist_consistency.py`
- 출처별 작가명 원본 컬럼을 읽어 `artist_name_standardized`와 `artist_key` 후보를 생성함
- 작가명 결측, 숫자만 있는 이름, URL/가격 문자열 후보, 출생연도 범위를 점검함
- 출처별 slug는 내부 식별 보조값으로만 관리함
- 여러 출처에 걸친 동일 작가 key는 오류가 아니라 `artist_master` 후보로 별도 표시함
- 작가 메타데이터는 모델 피처 후보가 아니라 커버리지와 운영 재현성 기준으로 먼저 평가함

## 3. 사용한 작가 컬럼

- Saatchi: `saatchi__artist_name`, `saatchi__artist_slug`, `saatchi__artist_birth_year`, `saatchi__artist_total_works`, `saatchi__ln_followers`
- Artsy: `artsy__artist_name`, `artsy__artist_slug`, `artsy__artist_nationality`, `artsy__artist_birth_year`, `artsy__artist_total_works`, `artsy__artist_followers`, `artsy__artist_for_sale`
- Artue: `artue__Artist`, `artue__Handle`, `artue__Nationality`, `artue__Nationality KO`
- Gallery primary: `gallery_primary__name_kor`, `gallery_primary__name_eng`, `gallery_primary__birth_year`, `gallery_primary__국적`

## 4. 주요 결과

- 전체 행: `54,842`
- 작가명 정상 후보: `54,840`
- 작가명 이슈 후보: `2`
- 표준 작가 key 수: `3,033`
- 한글 작가명 매핑 rows: `54,840`
- 한글 작가명 매핑 출처:
  - Track 3 매핑/음역 로직: `54,548`
  - 원본 한글명: `292`
  - 미매핑: `2`
- 여러 출처에 걸친 작가 key 수: `120`
- 여러 출처에 걸친 작가 row 수: `4,498`
- 작가명이 숫자만 있는 후보: `2`

## 5. 출처별 결과

| 출처 | 전체 | 정상 | 이슈 | 작가 key 수 | 출생연도 있음 | 국적 있음 |
|---|---:|---:|---:|---:|---:|---:|
| Artsy | `30,046` | `30,044` | `2` | `1,898` | `26,611` | `30,046` |
| Artue | `2,783` | `2,783` | `0` | `360` | `0` | `2,781` |
| Gallery primary | `292` | `292` | `0` | `78` | `292` | `292` |
| Saatchi | `21,721` | `21,721` | `0` | `820` | `1,975` | `0` |

## 6. 작가 메타데이터 판단

- `birth_year`
  - 값 있음: `28,878`
  - 운영 입력으로 받을 수 있으면 피처 후보
  - 결측이 많으므로 결측 flag와 함께 써야 함
- `nationality`
  - 값 있음: `33,119`
  - 표준화 전에는 모델 피처로 바로 쓰지 않음
- `artist_total_works`
  - 값 있음: `51,767`
  - 출처별 플랫폼 지표라 운영 재현성이 낮음
  - 학습 데이터에서 직접 계산하는 `artist_works_log`가 더 안전함
- `artist_followers`, `artist_for_sale`
  - Artsy/Saatchi 플랫폼 의존도가 큼
  - 기본 운영 피처에서 제외하고 실험 후보로만 보류
- `gallery_name`
  - 값 있음: `52,059`
  - 판매처/소속 정보 성격이 있어 누수와 운영 재현성 검토 전까지 기본 피처에서 제외

## 7. 해석

- 작가명 자체는 대부분 split 기준으로 사용할 수 있음
- `artist_name_ko`는 표시/리포트용 컬럼으로 사용할 수 있음
- `artist_name_ko`는 원본 한글명이 있으면 우선 사용하고, 없으면 Track 3 한글명 매핑 로직을 재사용함
- 출처 간 동일 작가 후보가 있어 향후 `artist_master` 테이블을 만들 가치가 있음
- 출처별 slug는 같은 플랫폼 내부에서는 유용하지만 전체 통합 artist id로 쓰기에는 부족함
- 작가 메타데이터는 커버리지가 출처별로 다르고 생성 방식도 달라 바로 모델에 넣으면 출처 누수 위험이 있음
- Track 4 초기 모델에서는 작가 DB 원본 메타보다 학습 데이터에서 계산 가능한 이력 피처를 우선하는 것이 안전함

## 8. 결론

- 채택: `artist_name_standardized`와 `artist_key`를 split 기준 후보로 사용
- 채택: `artist_name_ko`를 cleaned/feature/split 파일에 포함
- 채택: 여러 출처에 걸친 동일 작가 key는 오류가 아니라 `artist_master` 후보로 관리
- 보류: birth_year, nationality는 표준화와 결측 정책 확정 후 피처 후보로 검토
- 제외: followers, for_sale, 플랫폼 total works는 기본 운영 피처에서 제외하고 실험 후보로만 관리
- 제외: gallery_name은 운영 재현성과 누수 검토 전까지 기본 피처에서 제외

## 9. 다음 작업

- `T4-C3` 재료/지지체 정합성 감사 진행
- 이후 `cleaned_v2` 생성 시 `artist_name_standardized`, `artist_key`, `artist_meta_available_count`를 포함
- 작가 DB 확보 시 별도 `artist_master` 테이블 설계 문서 작성
