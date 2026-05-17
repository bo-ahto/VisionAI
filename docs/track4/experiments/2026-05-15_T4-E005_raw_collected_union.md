# T4-E005 원본 보존 raw collected 통합

- 실험 ID: `T4-E005_raw_collected_union`
- 연결 가설: `T4-H0`
- 날짜: 2026-05-15
- 상태: 완료

## 1. 목적

- 표준화/파생값이 섞인 raw 통합본보다 앞단계의 원본 보존 통합본을 생성함
- 각 수집 파일의 원래 컬럼을 그대로 가져오고, 다른 출처에 없는 컬럼은 빈칸으로 둠
- 클렌징 전에 원본값을 직접 확인할 수 있게 함

## 2. 생성 파일

- `data/track4_primary_market_raw_collected.csv`
- `data/track4_primary_market_raw_collected_summary.json`

## 3. 실행 명령

```bash
python3 scripts/track4/build_primary_market_raw_collected.py
```

## 4. 포함한 원천 파일

| 출처 | 원천 파일 | rows |
|---|---|---:|
| Saatchi | `data/saatchi_cleaned.csv` | `21,721` |
| Artsy | `data/artsy_kr_artworks.csv` | `30,046` |
| Artue | `data/artue_테스트_가격포함.csv` | `2,783` |
| Gallery primary | `data/1차 시장 데이터 - 전달본_260504.csv` | `292` |

## 5. 결과

| 항목 | 값 |
|---|---:|
| 전체 rows | `54,842` |
| 전체 columns | `132` |
| 추가 메타 컬럼 | `3` |

## 6. 처리 방식

- 원천 컬럼을 `<source>__<original_column>` 형태로 보존함
- 예: `saatchi__artist_name`, `artsy__artist_name`, `artue__Artist`
- 없는 값은 빈칸으로 둠
- 가격 파싱을 하지 않음
- 크기 파싱을 하지 않음
- 재료/지지체 분류를 하지 않음
- 파생값을 만들지 않음

## 7. 추가한 추적용 컬럼

- `track4_source`
- `track4_source_file`
- `track4_source_row_index`

## 8. 결론

- 판정: `채택`
- Track 4 데이터 클렌징의 최상위 원본 보존 파일은 `track4_primary_market_raw_collected.csv`로 둠
- `track4_primary_market_raw_unified.csv`는 이 파일 이후의 표준화 중간 산출물로 재정의함

