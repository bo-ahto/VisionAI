# 한글화와 동명이인 처리

## 1. 한글화 처리 요약

Track6 한글화는 두 층으로 나뉜다.

1. Track4 기본 한글명 생성
   - 원본 한글명이 있으면 원본 한글명을 우선 사용한다.
   - 원본 한글명이 없으면 Track3 작가명 매핑 로직을 재사용한다.
   - 관련 문서: `docs/track4/dataset/cleaning_pipeline.md`
2. Track6 수동 보정
   - 명백한 오표기만 `scripts/track6/artist_ko_overrides.csv`에 등록해 수정한다.
   - 자동 음역으로 다시 추정하지 않는다.
   - 보정 전 값은 `artist_name_ko_orig`에 보존한다.

실행 코드:

```bash
python3 scripts/track6/improve_artist_korean_names.py
```

검증/산출물:

| 항목 | 경로 |
|---|---|
| override 파일 | `scripts/track6/artist_ko_overrides.csv` |
| 적용 내역 | `data/track6/quality/track6_artist_name_ko_applied_overrides.csv` |
| 잔여 검토 후보 | `data/track6/quality/track6_artist_name_ko_review_candidates.csv` |
| 요약 JSON | `data/track6/quality/track6_artist_name_ko_improvement_summary.json` |
| 보고서 | `docs/track6/dataset/artist_name_ko_improvement_report.md` |

확인된 처리량:

| 항목 | 값 |
|---|---:|
| 적용 작가 key 수 | 144 |
| 적용 rows | 4,454 |
| 잔여 검토 후보 작가 key 수 | 506 |
| 잔여 검토 후보 rows | 3,109 |

## 2. Track4 단계 동명이인 표시

동명이인 1차 처리는 `scripts/track4/build_primary_market_cleaned_v2.py`의 `add_homonym_labels()`에서 수행한다.

처리 목적:

- 같은 한글명으로 여러 `artist_key`가 섞이는 문제를 표시/리포트/후속 피처 계산 단계에서 막기 위함이다.
- split 자체는 `artist_key` 기준이므로, 이름 suffix는 주로 표시와 감사 목적이다.

처리 기준:

```text
같은 artist_name_ko 안에 여러 artist_key가 있음
AND 보조 artist_key가 3건 이상
AND artist_key별 가격 중앙값 차이가 큼
    -> 동명이인 후보로 표시
```

구체 코드 기준:

| 기준 | 값 |
|---|---:|
| 보조 entity 최소 row 수 | 3 |
| 가격 중앙값 CV threshold | 0.5 |
| entity 기준 | `artist_key` |

처리 결과:

- `artist_name_ko_orig`: 원래 한글명 보존
- `artist_name_ko`: 동명이인일 경우 `_A`, `_B`, `_C` suffix 부여
- `is_homonym`: 동명이인 후보 여부
- `artist_entity_suffix`: suffix 값

예:

```text
김한나
  -> 김한나_A
  -> 김한나_B
```

## 3. Track6 split 단계 동명이인/이름 누수 차단

Track6 split은 Cold 평가셋을 먼저 고르고, Cold 이름이 train에 들어가지 않도록 막는다.

Cold 검증 기준:

| 기준 | 통과 조건 |
|---|---|
| `artist_key` | train과 겹침 0 |
| `artist_name_ko` | train과 겹침 0 |
| `artist_name_ko_orig` | train과 겹침 0 |
| `artist_works_log > 0` | Cold validation/test에서 0 rows |

관련 코드:

```bash
python3 scripts/track6/create_track6_splits.py
```

관련 산출물:

| 항목 | 경로 |
|---|---|
| split summary | `data/track6_split/track6_split_summary.json` |
| split report | `docs/track6/dataset/split_report.md` |

확인된 결과:

| 검증 | 결과 |
|---|---:|
| val_cold train artist_key 겹침 | 0 |
| test_cold train artist_key 겹침 | 0 |
| val_cold train artist_name_ko 겹침 | 0 |
| test_cold train artist_name_ko 겹침 | 0 |
| val_cold train artist_name_ko_orig 겹침 | 0 |
| test_cold train artist_name_ko_orig 겹침 | 0 |

## 4. 학습/테스트 데이터셋 공유 시 주의할 점

- `artist_name_ko`는 표시/검토와 split 이름 누수 차단에 사용된다.
- Cold 모델 feature에는 `artist_key`가 들어가지 않는다.
- 동명이인 suffix는 같은 한글명이 여러 `artist_key`로 나뉘는 경우를 표시하고, 이름 기준 누수를 막기 위한 장치다.
- 운영/API 연결 이후의 작가 식별자 감사는 이 문서 범위가 아니다.
