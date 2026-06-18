# PP-H11 외부 live 검색 스모크 검증 요약

- 실행일: 2026-06-18
- 목적: PP-CMETA3에서 사용한 외부 검색 피처가 단순 cache 개념이 아니라, 운영에서 실제 외부 live 검색 수집으로 생성 가능한지 확인한다.
- 실행 스크립트: `scripts/track6/run_pp_h11_operational_search_experiments.py`

## 1. 실행 명령

```bash
MPLCONFIGDIR=/private/tmp python3 scripts/track6/run_pp_h11_operational_search_experiments.py \
  --artist-scope cold \
  --selection-policy test_frequency \
  --limit-artists 3 \
  --providers python_ddg_art_context \
  --query-template-ids name_artist_ko name_exhibition_ko \
  --max-results 3 \
  --sleep-seconds 0 \
  --timeout 10 \
  --snapshot-month 2026-06-live-smoke
```

샌드박스 안에서는 외부 검색 라이브러리가 macOS system configuration 접근에서 중단되어, 승인된 권한 상승 실행으로 live 검색을 확인했다.

## 2. 실행 결과

| 항목 | 값 |
|---|---:|
| collector_run_id | `pp_h11_20260618_101143` |
| selected_artist_n | 3 |
| provider | `python_ddg_art_context` |
| query_template_n | 2 |
| request_n | 6 |
| raw result rows | 18 |
| standardized rows | 18 |
| artist success rate | 1.000000 |
| request success rate | 1.000000 |

## 3. 생성 파일

| 파일 | 용도 |
|---|---|
| `data/track6/external_search/operational/artist_search_collection_run_pp_h11_20260618_101143.json` | live 검색 실행 설정과 run id |
| `data/track6/external_search/operational/artist_search_result_raw_pp_h11_20260618_101143.jsonl` | live 검색 원본 결과 |
| `data/track6/external_search/operational/artist_search_result_standardized_pp_h11_20260618_101143.csv` | 표준화된 검색 결과 |
| `data/track6/external_search/operational/artist_search_feature_snapshot_2026-06-live-smoke_pp_h11_20260618_101143.csv` | 모델 입력 schema에 맞춘 작가 단위 검색 피처 |

## 4. 샘플 결과

| artist_search_name | quality | homonym risk | quality score | result count |
|---|---|---|---:|---:|
| 임미량 | low | clear | 0.166667 | 6 |
| 윤주 | low | risk | 0.000000 | 3 |
| 이준희 | low | watch | 0.200000 | 3 |

검색은 실제로 수행됐지만, 소량 샘플에서는 품질 등급이 모두 low였다. 특히 `윤주`, `이준희`처럼 동명이인 위험이 있는 작가가 포함되어 있어, 운영에서는 외부 live 검색 결과를 그대로 신뢰하지 않고 동명이인 위험/검색 품질 flag를 함께 사용해야 한다.

## 5. PP-CMETA3와의 관계

PP-CMETA3 자체는 동결 cache 기반 실험이다. 이 스모크 검증은 같은 계열의 외부 검색 피처를 실제 live 수집 경로로 생성할 수 있는지 확인한 것이다.

따라서 현재 결론은 아래처럼 구분한다.

- 성능 수치: PP-CMETA3 동결 cache 기준
- live 수집 가능성: PP-H11 `20260618_101143` 스모크 기준
- 운영 승격 전 필요 조건: 더 큰 작가 표본에서 live 검색 수집 성공률, 품질 등급, 동명이인 위험, cache 대비 schema parity를 검증해야 한다.

## 6. 운영 latest 복구

스모크 실행 직후 `track6_artist_search_operational_snapshot_latest.csv`와 `track6_artist_search_operational_standardized_latest.csv`가 소량 샘플로 갱신되어, 기존 2026-06-10 대량 수집본으로 복구했다.

복구 기준 파일:

- `artist_search_feature_snapshot_2026-06_pp_h11_20260610_142533.csv`
- `artist_search_result_standardized_pp_h11_20260610_142533.csv`
