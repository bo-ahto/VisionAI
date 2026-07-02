# PP-H11D ①②③ — 운영 반영 + 재학습 판정

- 작성일: 2026-06-14

## ① 패치 검증 + operational 스냅샷 재생성 (완료)

- 네트워크 의존성 스텁 후 **실제 패치된 `run_pp_h11.build_snapshot`**을 캐시
  standardized로 실행(검색 API 불필요). replica 측정과 일치, 스키마/행수/컬럼순서
  현행과 동일.
- 현행 서빙 스냅샷 대비: 전시 카운트 평균 −0.54(37/150 변동), 검색결과 −2.09,
  quality_score −0.0018(max 0.054). → 현행 서빙 스냅샷이 실제로 부풀려져 있었음 확인.
- **프로덕션 스냅샷 교체 완료**: `data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv`.
  재실행 멱등성 확인(delta 0).

## ② serving DB 검색 스냅샷 테이블 in-place 갱신 (완료)

- 표준 DB 빌더(`build_price_prediction_official_v0_1_db`)는 `connect_rebuilt`가 DB를
  통째로 unlink·재생성 → **런타임 누적 데이터 파괴**(prediction_events 641건=실서비스
  라우팅 로그, sale_price_feedback, 검수 큐 92+2982). 전체 재빌드 **사용 불가**.
- 대신 surgical 갱신: 런타임 테이블 미접촉, `artist_search_feature_snapshots` 150행만
  DELETE 후 빌더의 실제 `insert_search_features`로 재삽입(스키마/ID/로직 동일).
  DB 백업 후 적용. 갱신 후 런타임 테이블 카운트 전부 불변 확인(641→641 등).
- DB 전시 카운트 총합 정정(예: 김레이시 13→5). 백업: `data/track6/service_v0_1/_pp_h11d_backup_20260614/`.

## ③ 재학습 판정: **불필요** (+ 더 큰 구조 문제 발견)

### 학습 경로엔 dup 버그가 없음
- 학습된 Cold 모델 검색 피처 = `track6_artist_search_pilot_features.csv`,
  빌더 `run_pp_h_search_pilot.row_from_results`. **작가당 단일 검색 1회** 집계 →
  여러 query template 합산이 없어 **동일 URL 중복 부풀림이 구조적으로 불가능**.
- 따라서 dup 버그 때문에 모델을 재학습할 이유가 없고, 재학습은 동결 파이프라인의
  재현성 parity(diff<1e-15)를 무의미하게 깨뜨림 → **재학습 안 함이 옳음**.

### dup보다 훨씬 큰 train/serve 스케일 불일치 (신규 발견)

| 피처 | 학습(pilot) | 서빙(operational, dedup 후) |
|---|---|---|
| `search_exhibition_context_count` | max 1, mean 0.01 | max 11, mean 3.23 |
| `search_art_context_count` | max 5, mean 0.44 | max 21, mean 8.01 |
| `search_result_count` | max 6, mean 5.66 | max 25, mean 12.71 |

- 학습 데이터에서 전시 카운트는 **거의 항상 0**(단일 쿼리, max_results 상한)인데
  서빙은 평균 3.23을 받음 = 학습 분포 밖 외삽.
- **함의(가격 영향이 작은 진짜 이유)**: LightGBM이 학습 때 전시 카운트 ∈ {0,1}만
  봤으므로 split 경계는 최대 ~0.5~1. 서빙의 5든 13이든 전부 "> 경계"의 같은 쪽 →
  **모델이 5와 13을 구분하지 못함**. 따라서 dedup(13→5)은 예측에 사실상 0 영향.
  앞서 측정한 quality_score 0.012·±0.2 cap 논거에 더해, 이 해상도 한계가 가격 영향
  무시 가능을 독립적으로 뒷받침.

### 결론
- **dup 정정은 운영(CSV+DB)에 반영 완료** — 데이터는 이제 정직.
- 그러나 이 dup은 예측에 거의 영향이 없었음(모델 해상도 밖). 검색 카운트가 가격에
  의미 있게 작동하려면 dup이 아니라 **train/serve 수집 방식 정합**(서빙도 단일
  쿼리로 맞추거나, 모델을 operational 스케일로 재학습)이 필요 — 이는 별도의 더 큰
  의사결정 사안(현 공식 기준 Cold 트랙은 검색 수집 ROI 낮음으로 종결됨, PP-CSRCH2).

## 정리

| 단계 | 상태 |
|---|---|
| 원인 규명 | ✅ 진짜 원인 = 동일 URL 다중수집(serving 전용) |
| 코드 정정 | ✅ `build_snapshot` URL dedup |
| 운영 스냅샷 CSV | ✅ 교체 |
| 서빙 DB 테이블 | ✅ surgical 갱신(런타임 데이터 보존) |
| 재학습 | ✅ 불필요 판정(학습 경로 무관 + 모델 해상도 밖) |
| 잔여 | train/serve 스케일 불일치 = 별도 큰 과제(검색 수집 정합) |
