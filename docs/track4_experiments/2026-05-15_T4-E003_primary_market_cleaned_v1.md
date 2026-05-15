# T4-E003 1차 시장 cleaned v1 생성

- 실험 ID: `T4-E003_primary_market_cleaned_v1`
- 연결 가설: `T4-H0`
- 날짜: 2026-05-15
- 상태: 완료

## 1. 목적

- raw 통합본을 바로 학습에 쓰지 않고, 컬럼 감사 결과를 바탕으로 학습 후보와 제외 후보를 구분함
- 갤러리명과 갤러리 티어 값도 함께 검증함

## 2. 사용 데이터

- 입력: `data/track4_primary_market_raw_unified.csv`
- 갤러리 티어 기준표: `data/art_gallery_tier_list_v3.xlsx - 전체 리스트.csv`

## 3. 실행 명령

```bash
python3 scripts/track4/build_primary_market_cleaned_v1.py
```

## 4. 생성 파일

- `data/track4_primary_market_cleaned_v1.csv`
- `data/track4_primary_market_cleaned_v1_summary.json`
- 보고서: `docs/track4_primary_market_cleaned_v1_report.md`

## 5. 주요 결과

| 항목 | 값 |
|---|---:|
| 전체 rows | `33,276` |
| 학습 후보 rows | `32,343` |
| 제외 rows | `933` |
| 학습 후보 가격 중앙값 | `3,036,000원` |
| 학습 후보 최대 가격 | `997,150,000원` |

## 6. 갤러리 검증 결과

| 항목 | rows |
|---|---:|
| 기준표 매칭 | `1,231` |
| Tier A | `74` |
| Tier B | `125` |
| Tier C | `1,032` |
| 미매칭 | `145` |
| 플랫폼 기본값 또는 유형값 | `29,301` |
| 갤러리명 결측 | `2,599` |

## 7. 해석

- 원본 `gallery_tier`는 대부분 실제 티어가 아님
- Saatchi의 `3`은 플랫폼 기본값으로 보고, Artsy의 `Gallery`는 유형값으로 봄
- 실제 티어는 별도 기준표 매칭으로만 인정함
- 따라서 갤러리 티어는 cleaned v1에 남기되, 학습 피처로는 아직 사용하지 않음

## 8. 결론

- 판정: `채택`
- cleaned v1을 Track 4 split 생성 전 기준 데이터로 사용 가능
- 단, 다음 단계에서 작가명 정규화와 동명이인 후보 검토가 필요함

