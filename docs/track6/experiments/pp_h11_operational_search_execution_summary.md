# PP-H11 운영형 검색 피처 수집 실행 요약

- 실행일: 2026-06-03
- 목적: 외부 검색 결과를 운영에서 주기적으로 수집하고, 가격 예측 모델/서비스에서 사용할 수 있는 작가 단위 표준 피처로 변환 가능한지 검증한다.
- 결론: 수집은 가능하다. 다만 검색 피처는 가격점 예측에 직접 넣기보다 `검색 품질`, `작가 식별 신뢰도`, `가격 범위/신뢰도 보정`에 우선 활용하는 것이 적합하다.

## 1. 실행 전 문제

- 기존 PP-H7~H10은 `data/track6/external_search/track6_artist_search_pilot_features.csv` 기반의 단발 파일럿에 가까웠다.
- 기존 `duckduckgo_search` 패키지는 현재 환경에서 macOS 키체인/인증서 오류로 중단됐다.
- DuckDuckGo HTML 직접 호출은 네트워크 권한에서는 접근 가능했지만, 반복 호출 중 `403 Forbidden`이 발생했다.
- Naver/Google 공식 검색 API 키는 현재 환경 변수에 없었다.

따라서 PP-H11은 기존 파일을 덮어쓰지 않고, 별도 운영형 수집기로 분리했다.

## 2. 수정한 실행 방식

| 항목 | 적용 내용 |
|---|---|
| 신규 스크립트 | `scripts/track6/run_pp_h11_operational_search_experiments.py` |
| 기본 provider | `naver_html` |
| 공식 API 확장 | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`이 있으면 `naver_api_webkr` 사용 가능 |
| 저장 방식 | raw 결과, 표준화 결과, 월간 snapshot 분리 저장 |
| 기존 PP-H 파일 | 덮어쓰지 않음 |

실행 중 품질이 낮아 보여 수집기를 한 번 보정했다.

| 수정 전 문제 | 수정 내용 |
|---|---|
| 검색어가 `{작가명} 작가`, `{작가명} 갤러리`처럼 넓음 | `{작가명} 미술 작가`, `{작가명} 전시 작가`, `{작가명} 작품 경매`처럼 미술 문맥을 강화 |
| Naver HTML에서 `검색옵션`, `Keep`, 탭 링크가 결과로 잡힘 | UI 링크, help 링크, breadcrumb 링크 제외 |
| 중간 진행 상황 확인 어려움 | 10개 요청마다 flush 로그 출력 |

## 3. 최종 실행 설정

| 항목 | 값 |
|---|---|
| 실험 ID | `PP-H11` |
| 실행 ID | `pp_h11_20260603_131328` |
| 작가 수 | 80명 |
| provider | `naver_html` |
| 검색 템플릿 | 5개 |
| 요청 수 | 400개 |
| 요청당 결과 수 | 최대 5개 |
| 실행 시간 | 286.33초 |
| snapshot 기준 | `2026-06` |

사용한 검색 템플릿:

| template_id | 검색어 |
|---|---|
| `name_artist_ko` | `{작가명} 미술 작가` |
| `name_artwork_ko` | `{작가명} 작품 미술` |
| `name_exhibition_ko` | `{작가명} 전시 작가` |
| `name_gallery_ko` | `{작가명} 갤러리 미술` |
| `name_auction_ko` | `{작가명} 작품 경매` |

## 4. 결과 요약

| 지표 | 결과 |
|---|---:|
| 요청 성공률 | 1.0000 |
| 요청 오류율 | 0.0000 |
| 작가 성공률 | 1.0000 |
| high 비율 | 0.0000 |
| medium 비율 | 0.4625 |
| low 비율 | 0.5375 |
| 동명이인 risk 비율 | 0.0000 |
| 평균 결과 수/작가 | 25.0000 |
| 평균 unique domain/작가 | 12.7625 |
| 평균 검색 품질 점수 | 0.421175 |
| 평균 미술 문맥 비율 | 0.6225 |
| 평균 전시 문맥 비율 | 0.2475 |
| 평균 시장 문맥 비율 | 0.0990 |
| 평균 작가명 매칭률 | 0.4200 |

품질 등급:

| 등급 | 작가 수 | 해석 |
|---|---:|---|
| `medium` | 37 | 검색 보조 피처 후보 |
| `low` | 43 | 점 예측 직접 투입 보류 |
| `high` | 0 | 공식 API/수동 검수 전에는 보수적으로 없음 |

## 5. 수정 효과

| 실행 | medium 작가 수 | low 작가 수 | 평균 품질 점수 | 평균 작가명 매칭률 | 평균 미술 문맥 비율 |
|---|---:|---:|---:|---:|---:|
| 초기 템플릿 | 5 | 75 | 0.314850 | 0.1465 | 0.4110 |
| 강화 템플릿 + UI 링크 제거 | 37 | 43 | 0.421175 | 0.4200 | 0.6225 |

보정 후 검색 품질이 뚜렷하게 개선됐다. 특히 작가명 매칭률과 미술 문맥 비율이 상승했기 때문에, H11의 핵심인 “반복 수집 가능한 표준 피처 생성”은 가능하다고 판단한다.

## 6. 산출물

| 산출물 | 경로 |
|---|---|
| 실행 리포트 | `experiments/track6/PP-H11_operational_search_feature_standardization/reports/result_report.md` |
| HTML 리포트 | `experiments/track6/PP-H11_operational_search_feature_standardization/reports/result_report.html` |
| 실험 metrics | `experiments/track6/PP-H11_operational_search_summary_metrics.csv` |
| 최신 snapshot | `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv` |
| 최신 표준화 결과 | `data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv` |
| raw JSONL | `data/track6/external_search/operational/artist_search_result_raw_pp_h11_20260603_131328.jsonl` |
| raw CSV | `data/track6/external_search/operational/artist_search_result_raw_pp_h11_20260603_131328.csv` |
| snapshot CSV | `data/track6/external_search/operational/artist_search_feature_snapshot_2026-06_pp_h11_20260603_131328.csv` |

## 7. 해석

- 외부 검색 수집은 운영형 데이터로 만들 수 있다.
- 다만 현재는 단일 provider이고 HTML 폴백이므로, 운영 배포 시에는 공식 API 기반으로 전환하는 것이 맞다.
- `medium` 등급 37명은 검색 피처를 가격 범위/신뢰도 보정에 사용할 수 있는 후보군이다.
- `low` 등급 43명은 검색 결과가 있어도 작가 식별 신뢰도가 낮으므로 가격점 예측 모델에 직접 넣으면 노이즈가 될 가능성이 높다.
- 따라서 PP-H는 CatBoost/LightGBM 점 예측에 무조건 추가하는 실험보다, `search_quality_grade x quantile_width` 또는 `search_quality_grade x prediction_range` 보정 실험으로 연결하는 것이 더 타당하다.

## 8. 다음 단계

- `PP-H12`: 80명 중 상위/하위 샘플을 수동 검수해 `match_artist`, `partial_match`, `homonym`, `irrelevant` 라벨을 만든다.
- `PP-H14`: `search_quality_grade`를 서비스 신뢰도와 가격 범위 폭 조정에 연결한다.
- `PP-H18`: 최신 Cold 후보인 q-width 보정과 검색 품질 등급을 결합한다.
- 운영 준비: 공식 Naver API 키가 준비되면 같은 스키마로 `naver_api_webkr` provider를 재수집하고 HTML 폴백 결과와 품질 차이를 비교한다.
