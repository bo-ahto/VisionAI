# PP-COLD-ARTIFACT3 Cold guard+search 2단 방어 artifact 고정 (설계서)

- 작성일: 2026-06-07
- 목적: PP-COLD-DEFENSE1이 가산(중복 아님) 검증한 guard+search 2단 방어를 운영 artifact로 고정한다. Cold 방어를 1단(guard, v0.1)에서 2단(guard+search)으로 확장.
- 성격: 엔지니어링(artifact 고정). v0.1 freeze 패턴 확장.
- 상태: 설계 완료 / 실행 완료
- 재현 규칙: 번들 `models/track6/cold_prediction_v0.3/` + freeze 스크립트.

## 1. 배경 / 전제

- PP-COLD-DEFENSE1: guard(PP-QR4) + search(PP-H28 gallery_museum cap0.2)가 PP-Y18 base에서 가산적(redundancy gap +0.0006≈0). guard_search_gm test 0.4098/0.849/2.347 = Cold 최고.
- 주의: 검색층은 분산 추가(val fold 개선확률 guard 1.00 vs 결합 0.72) + 커버리지 제한 → fallback + 검수 플래그 필수.

## 2. 고정 대상

| 구분 | 내용 |
|---|---|
| 대표 점예측 | PP-Y18 qwidth (유지) |
| 방어 1단 guard | qwidth/gap mask로 lgb_q40 하향 (PP-QR4 파라미터) |
| 방어 2단 search | 작가 단위 검색 delta lookup(=h23_gallery_museum_cap0.2 − pp_y2), 가산 적용 |
| fallback | 미커버 작가 → 검색 delta 0 (guard only) |
| 검수 플래그 | qwidth ≥ qwidth_q67 OR 작가 미커버 → review_flag=True |

직렬화: guard 파라미터(qwidth_q67/gap_q50/weight) + 작가 검색 delta lookup(372작가, 작가 내 상수) + 검수 정책.

## 3. 방법 / 검증

1. QR2 frame + H28 검색 delta join, 작가 단위 delta lookup(mean) 생성.
2. 독립 후처리기로 test 적용 → 독립 계산(guard+delta) 및 PP-COLD-DEFENSE1 guard_search_gm 지표와 1e-6 이내 일치 확인(실패 시 freeze 중단).
3. 정책/파라미터/lookup/릴리스/manifest 작성.

## 4. 산출물 (번들)

- `config/cold_model_policy_v0_3.json`, `cold_postprocess_params_v0_3.json`, `search_delta_lookup_v0_3.json`
- `predict/apply_cold_postprocess_v0_3.py` (component 예측 + artist_key → 대표/방어/검수플래그)
- `evidence/PP-COLD-DEFENSE1/`, `reproduction/upstream_sources.json`, `manifest/MANIFEST.sha256`, `README.md`, `reports/cold_artifact_release_v0_3.md`

## 5. 정직한 범위

- 후처리층만 실행 가능. 하부 Quantile/PP-Y18은 상류 search 의존(raw-input 불가 — 그건 v0.2_operational 담당).
- 검색 delta는 작가 단위 frozen snapshot(372작가). 신규 작가 → guard fallback.
- 0604는 전부 warm(0 cold) → cold 운영 트래픽 확보 후 재평가 필요.

## 6. 3종 cold artifact 비교

| 번들 | 방어 | 실행 | 정확도 |
|---|---|---|---|
| v0.1 | guard only | 후처리층 | guard test 0.4178/0.964/2.538 |
| v0.2_operational | q50 + q40 guard (search-free) | **raw-input** | 0.4823/1.242/4.381 (약함) |
| **v0.3** | **guard+search** | 후처리층 | **0.4098/0.849/2.347 (최고)** |

## 7. 다음 액션

- cold 운영 트래픽 확보 시 v0.1/v0.2/v0.3 0604-style 재평가.
- 검색 커버리지 확대(전 작가) → v0.3 fallback 비율 감소 + agreement 게이팅 실행 가능화(PP-H28 후속).
