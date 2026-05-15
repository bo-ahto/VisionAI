# Track 4 1차 시장 cleaned v1 보고서

- 목적: raw 통합본의 컬럼 감사 결과를 바탕으로 1차 cleaned 데이터셋을 생성하고, 학습 후보/제외 후보를 구분함
- 기준일: 2026-05-15
- 입력 파일: `data/track4_primary_market_raw_unified.csv`
- 출력 파일: `data/track4_primary_market_cleaned_v1.csv`
- 생성 스크립트: `scripts/track4/build_primary_market_cleaned_v1.py`

## 1. 처리 원칙

- 원본 row를 바로 삭제하지 않고 `is_training_candidate`와 제외 사유를 추가함
- 이후 필요하면 학습 단계에서 `is_training_candidate = 1`만 사용함
- 가격, 크기, 연도, 중복, 원천 제외 플래그를 기준으로 학습 후보를 구분함
- 갤러리명과 갤러리 티어는 검증 메타데이터로 보존하되, 운영 입력 피처로는 아직 사용하지 않음

## 2. 전체 결과

| 항목 | 값 |
|---|---:|
| 전체 rows | `33,276` |
| 학습 후보 rows | `32,343` |
| 제외 rows | `933` |
| 학습 후보 가격 중앙값 | `3,036,000원` |
| 학습 후보 가격 Q25 | `1,255,800원` |
| 학습 후보 가격 Q75 | `7,399,250원` |
| 학습 후보 최대 가격 | `997,150,000원` |

## 3. 출처별 학습 후보

| 출처 | 전체 rows | 학습 후보 rows |
|---|---:|---:|
| Saatchi | `20,278` | `19,583` |
| Artsy | `10,111` | `9,903` |
| Artue | `2,599` | `2,575` |
| Gallery primary | `288` | `282` |

## 4. 제외 사유

| 제외 사유 | 건수 | 의미 |
|---|---:|---|
| `source_excluded_for_training` | `617` | 원천 데이터에서 이미 학습 제외로 표시된 row |
| `semantic_duplicate_drop` | `200` | 의미상 중복 후보 중 첫 row를 제외한 중복 row |
| `missing_width_height` | `93` | 가로/세로 결측 |
| `price_under_10000` | `50` | 1만 원 미만 가격 |
| `invalid_year_made` | `24` | 1000년 이전 또는 2026년 이후 제작연도 |
| `extreme_aspect_ratio` | `20` | 극단적 가로/세로 비율 |
| `width_height_over_1000cm` | `12` | 가로 또는 세로 1000cm 초과 |
| `price_over_1b` | `10` | 10억 원 초과 가격 |
| `depth_over_300cm` | `8` | 깊이 300cm 초과 |
| `missing_title` | `1` | 작품명 결측 |

## 5. 갤러리명 / 갤러리 티어 검증

- 참고 기준표
- `data/art_gallery_tier_list_v3.xlsx - 전체 리스트.csv`
- 원본 `gallery_tier` 값의 문제
- Saatchi의 `gallery_tier = 3`은 실제 A/B/C/D/E 티어가 아니라 플랫폼 내부값으로 보임
- Artsy의 `gallery_tier = Gallery`는 실제 티어가 아니라 갤러리 유형값임
- Artue는 갤러리명/티어가 없음
- Gallery primary는 갤러리명은 있으나 원본 티어가 없음

### 검증 결과

| 매칭 상태 | rows | 의미 |
|---|---:|---|
| `platform_default` | `20,278` | Saatchi 플랫폼 기본값, 실제 갤러리 티어 아님 |
| `raw_gallery_type_only` | `9,023` | Artsy의 Gallery 유형값만 있음 |
| `missing_gallery_name` | `2,599` | 갤러리명 없음 |
| `tier_reference` | `1,231` | 기준표 또는 alias로 Tier A/B/C 매칭 |
| `unmatched` | `145` | 갤러리명은 있으나 기준표 미매칭 |

### 검증된 티어 분포

| 검증 티어 | rows |
|---|---:|
| Tier A | `74` |
| Tier B | `125` |
| Tier C | `1,032` |
| unmatched | `32,045` |

### 매칭된 예시

- Tier A
- `타데우스 로팍`
- `리만머핀 갤러리`
- Tier B
- `Leehwaik Gallery`
- `CHOI&CHOI`
- Tier C
- `BHAK`
- `Gallery Planet`
- `Kimreeaa Gallery`
- `Art Sohyang`
- `갤러리기체`
- `야리라거 갤러리`
- `디스위켄드룸`
- `에이라운지`

### 아직 미매칭인 예시

- `워크스워크스`
- `갤러리 르롱`
- `이아 갤러리`
- `더써드갤러리`
- `제시카 실버맨`
- `갤러리 술타나`
- `리슨 갤러리`

## 6. 현재 판단

- cleaned v1은 Track 4 split 생성 전 기준 데이터로 사용할 수 있음
- 다만 갤러리 티어는 아직 학습 피처로 쓰기 어렵고, 감사/분포 확인용 메타데이터로만 유지해야 함
- Gallery primary의 일부 해외 갤러리명은 기준표 alias를 추가하면 추가 매칭 가능함
- 다음 단계는 cleaned v1 기준으로 작가명 정규화와 Warm / Cold split을 생성하는 것임

