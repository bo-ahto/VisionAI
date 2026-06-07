# Cold 외부 검색 데이터 확인 메모

- 작성일: 2026-06-04
- 기준 모델: `price_prediction_v0.1`
- 목적: Cold 모델 실험에서 사용한 외부 검색 정보가 어떤 파일에서 왔고, 현재 서비스 적용 기준에서는 어떻게 해석해야 하는지 정리

## 1. 결론

- Cold v0.1 성능표의 검색 피처는 실시간 검색 API 호출값이 아니라, 실험 시점에 저장된 작가 단위 검색 피처 캐시를 사용
- v0.1 Cold 기준 후보의 뿌리인 `PP-Y2`는 최신 H11 운영형 스냅샷이 아니라 아래 파일을 사용
  - `data/track6/external_search/track6_artist_search_pilot_features.csv`
  - `data/track6/external_search/track6_artist_search_pilot_raw.jsonl`
- 최신 운영형 검색 스냅샷은 이후 H11~H27 검증/보정 실험에서 사용
  - `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv`
  - `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv`
- Google Custom Search는 현재 Cold v0.1 실험 피처로 사용된 상태가 아님
- Naver 공식 API 결과는 최신 운영형 스냅샷에는 포함되어 있으나, v0.1 기준 Cold 후보의 원 실험 파일은 pilot DuckDuckGo 기반 캐시
- 2026-06-04 신규 테스트 데이터는 전부 Warm으로 라우팅되어, 해당 테스트에서는 Cold 외부 검색 피처가 실제 예측에 적용된 행이 없음

## 2. Cold v0.1 기준 후보와 검색 피처 흐름

```text
검색 피처 pilot 수집
  -> PP-H7 외부 검색 피처 파일럿
  -> PP-Y2 Cold LightGBM Quantile 검색 + 전시/갤러리 결합
  -> PP-Y16/PP-Y18 qwidth 구간 보정 안정성 검증
  -> price_prediction_v0.1 Cold 기준 후보
```

v0.1 정책 파일의 Cold 기준:

- 후보: `PP-Y18 qwidth_bin_oof_min30_cap0.25`
- 모델 구조: LightGBM Quantile + qwidth 구간 보정
- 원 후보 계열: `lgbq_search_all_external_interaction`

즉 Cold v0.1은 작품 조건만 보는 모델이 아니라, 아래 정보를 함께 사용한 후보를 기반으로 함.

- 작품 크기/재료/지지체 피처
- 작가 메타 피처
- 전시/갤러리 피처
- 검색 피처
- Quantile width 기반 예측 불확실성 피처

## 3. v0.1 Cold 원 실험에 사용된 검색 파일

파일:

- `data/track6/external_search/track6_artist_search_pilot_features.csv`
- `data/track6/external_search/track6_artist_search_pilot_raw.jsonl`

확인 결과:

| 항목 | 값 |
|---|---:|
| 작가 단위 검색 피처 row | 120 |
| 검색 결과 원문 파일 | JSONL |
| 검색 품질 low | 113명 |
| 검색 품질 medium | 7명 |
| 검색 품질 high | 0명 |
| 동명이인 위험 clear | 76명 |
| 동명이인 위험 watch | 13명 |
| 동명이인 위험 risk | 31명 |

pilot 피처의 의미:

- `search_result_count`: 검색 엔진 전체 결과 수가 아니라 수집 스크립트가 가져온 상위 결과 수
- `search_source_count`: 검색 결과 URL의 고유 도메인 수
- `search_art_context_count`: 제목/요약/URL에 미술 관련 문맥이 감지된 결과 수
- `search_exhibition_context_count`: 전시/개인전/아트페어 등 전시 문맥 결과 수
- `search_gallery_context_count`: 갤러리/미술관 문맥 결과 수
- `search_market_context_count`: 경매/판매/가격 문맥 결과 수
- `search_homonym_context_count`: 동명이인 또는 무관 인물 위험 문맥 결과 수
- `search_quality_score`: 미술 문맥, 출처 다양성, 동명이인 위험을 합산한 품질 점수
- `search_quality_grade`: `high`, `medium`, `low`, `missing`

## 4. 최신 운영형 검색 스냅샷

파일:

- `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv`
- `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv`

확인 결과:

| 항목 | 값 |
|---|---:|
| 작가 단위 snapshot row | 428 |
| 표준화 검색 결과 row | 30,910 |
| 검색 품질 low | 416명 |
| 검색 품질 medium | 12명 |
| 검색 품질 high | 0명 |
| 동명이인 위험 clear | 354명 |
| 동명이인 위험 watch | 36명 |
| 동명이인 위험 risk | 38명 |

provider별 표준화 검색 결과 수:

| provider | row 수 |
|---|---:|
| `python_ddg_art_context` | 12,833 |
| `python_ddg` | 12,818 |
| `naver_api_webkr` | 1,900 |
| `naver_api_blog` | 1,760 |
| `naver_api_news` | 1,599 |

source group 분포:

| source group | row 수 |
|---|---:|
| other | 18,401 |
| social_blog | 4,233 |
| gallery_museum | 2,733 |
| art_general | 2,405 |
| news | 1,674 |
| market | 998 |
| exhibition | 344 |
| missing | 122 |

## 5. 검색 품질 점수 산식

최신 운영형 스냅샷 기준 `search_quality_score`는 아래 요소를 조합해 계산.

```text
search_quality_score =
  0.30 * 미술 문맥 비율
+ 0.20 * 신뢰 도메인 비율
+ 0.15 * 전시 문맥 비율
+ 0.15 * 시장/거래 문맥 비율
+ 0.10 * 최근 결과 비율
+ 0.10 * provider 커버리지 점수
+ 0.10 * 작가명 일치 비율
- 0.30 * 동명이인 위험 비율
```

등급 기준:

| 등급 | 기준 | 해석 |
|---|---|---|
| high | 점수 0.70 이상, 동명이인 위험 0.20 미만 | 가격 피처로 비교적 안정적 |
| medium | 점수 0.45 이상, 동명이인 위험 0.40 미만 | 참고 가능하지만 검수 필요 |
| low | 위 기준 미달 | 직접 가격 보정 피처보다는 신뢰도 하향/검수용 |
| missing | 검색 결과 없음 | 검색 신호 없음 |

## 6. Cold 성능에 반영된 정도

Cold 주요 실험 결과:

| 실험 | 내용 | MdAPE | MAPE | p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| PP-Y2 | LightGBM Quantile + 검색 전체 + 전시/갤러리 상호작용 | 0.4421 | 1.0484 | 3.3537 | 검색/외부 피처 통합 기준선 |
| PP-Y18 | PP-Y2 기반 qwidth 구간 보정 안정성 후보 | 0.4247 | 0.9910 | 3.3053 | v0.1 Cold 기준 후보 |
| PP-H23 | 최신 운영형 검색 source group 보정, news cap0.2 | 0.4253 | 0.9534 | 3.1542 | 추가 개선 후보, v0.1 미반영 |
| PP-H23 | 최신 운영형 검색 source group 보정, gallery/museum cap0.2 | 0.4313 | 0.9285 | 3.1390 | MAPE 개선 후보, v0.1 미반영 |

해석:

- 검색 피처는 Cold 기준선 개선에 기여한 후보군에 포함됨
- 다만 검색 품질이 낮은 작가가 많아 검색값을 그대로 강하게 쓰기에는 위험
- v0.1은 검색 피처를 포함한 후보를 기반으로 하되, 최종 표시는 참고 가격/범위 중심이 적합
- 최신 H11/H22/H27 결과는 검색 피처를 운영형으로 더 고도화할 수 있다는 후속 근거로 보는 것이 맞음

## 7. Provider 일치도 검증

파일:

- `experiments/track6/PP-H22_provider_agreement_stability/outputs/provider_agreement_by_artist.csv`

확인 결과:

| 항목 | 값 |
|---|---:|
| 비교 작가 수 | 78 |
| agreement medium | 9명 |
| agreement low | 69명 |
| provider disagreement risk true | 71명 |
| provider disagreement risk false | 7명 |

해석:

- Naver와 Python 검색 provider가 항상 같은 신호를 주지는 않음
- agreement가 낮은 작가는 동명이인/무관 검색/검색엔진 편향 가능성이 큼
- 운영에서는 검색 피처를 단독 가격 보정 근거로 쓰기보다 신뢰도, 검수 우선순위, 가격 범위 확대 조건으로 쓰는 편이 안전

## 8. 서비스 적용 관점 정리

서비스 적용 시 권장 구조:

```text
작가명 확정
  -> 검색 provider별 결과 수집 또는 최신 snapshot 조회
  -> 검색 결과 표준화
  -> 작가 단위 검색 피처 생성
  -> 검색 품질/동명이인 위험 판정
  -> Cold 예측 또는 신뢰도/범위 정책에 반영
```

운영 DB에 저장할 추천 항목:

- `artist_search_name`
- `snapshot_month`
- `provider`
- `query_template_id`
- `query_text`
- `rank`
- `title`
- `snippet`
- `url`
- `domain`
- `source_group`
- `has_result`
- `is_art_context`
- `is_exhibition_context`
- `is_gallery_context`
- `is_market_context`
- `is_homonym_context`
- `is_trusted_domain`
- `is_recent_context`
- `artist_name_in_result`
- `search_quality_score`
- `search_quality_grade`
- `search_homonym_risk_grade`
- `provider_agreement_score`
- `provider_agreement_grade`

## 9. 주의할 점

- `search_result_count`는 전체 웹 검색량이 아니라 수집된 상위 결과 row 수
- 현재 검색 품질 high가 없고 low가 대부분이라, 검색 피처를 가격을 직접 올리고 내리는 강한 신호로 쓰면 위험
- Google Custom Search는 실험 피처로 활성 사용된 상태가 아니므로 서비스 문서에서 사용 중인 provider로 쓰면 안 됨
- Naver 공식 API는 최신 운영형 snapshot에는 포함되어 있으나, v0.1 Cold 기준 원 실험은 pilot 검색 캐시 기반
- `PP-H20_H26_search_feature_expansion` 리포트 하단에는 과거 blocked 해석 문구가 남아 있으나, 현재 `api_preflight.csv`와 최신 스냅샷 기준으로는 Naver/Python provider 결과가 존재함. 해당 리포트를 보고용으로 쓸 경우 문구 정정 필요

## 10. 현재 판단

- v0.1 Cold에 검색 피처가 전혀 없는 것은 아님
- 정확히는 “pilot 검색 캐시 + 전시/갤러리 외부 피처를 LightGBM Quantile에 넣고, qwidth 보정까지 한 후보”가 v0.1 Cold 기준
- 최신 운영형 검색 스냅샷은 v0.1 확정 후보의 원천은 아니지만, 후속 Cold 고도화와 서비스 신뢰도 정책에 사용할 수 있는 더 발전된 데이터
- 따라서 서비스 v0.1 문서에는 아래처럼 표현하는 것이 가장 정확

```text
Cold v0.1은 실험 당시 저장된 작가 단위 외부 검색 피처 캐시를 사용한 후보를 기반으로 한다.
운영 적용 시에는 최신 운영형 검색 스냅샷을 별도 테이블로 관리하고,
검색 피처는 단일 가격을 직접 결정하는 값이 아니라 신뢰도, 가격 범위, 수동 검수 우선순위에 우선 활용한다.
```
