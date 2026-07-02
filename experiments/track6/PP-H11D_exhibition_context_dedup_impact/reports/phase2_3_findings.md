# PP-H11D Phase 2/3 — URL dedup 반영 + 모델 입력 영향 측정

- 작성일: 2026-06-14

## Phase 2 — 반영한 수정

`scripts/track6/run_pp_h11_operational_search_experiments.py`의 `build_snapshot`에
**작가 내 동일 URL 1건 처리** 로직 추가 (카운팅 직전). 같은 기사가 여러 query
template/provider 결과로 중복 수집돼 문맥 카운트가 부풀려지던 문제를 정정.
provider/query 커버리지는 dedup 전 group 기준으로 계산하므로 영향 없음.

- 선택 dedup 방식: **URL 단위**. 의미적(같은 전시) 군집은 Phase 1에서 URL dedup
  대비 추가 이득 미미(전시 12.4% vs 12.7%) + 서로 다른 전시 과병합 위험 → 비채택.
  도메인 단위는 30~46% 과교정(한 언론사의 서로 다른 전시도 뭉갬) → 비채택.

## Phase 3 — 모델 입력 피처 변화량 (동결 모델 입력 관점)

캐시 표준화 데이터에서 build_snapshot 산식을 raw vs URL-dedup으로 재계산해 비교
(89작가). 동결 Cold 모델이 입력으로 받는 검색 피처의 변화량:

| 모델 입력 피처 | 평균 절대변화 | 최대 | 변경작가 비율 | 방향 |
|---|---|---|---|---|
| `search_quality_score` (핵심 집계) | **0.0118** | 0.0535 | 83% | ↓ |
| `search_exhibition_ratio` | 0.026 | 0.187 | 73% | ↓ |
| `search_art_match_ratio` | 0.029 | 0.173 | 82% | ↓ |
| `search_exhibition_context_count_log` | 0.112 | 0.847 | 42% | ↓ |
| `search_art_context_count_log` | 0.144 | 0.747 | 75% | ↓ |
| `search_result_count_log` | 0.155 | 0.693 | 83% | ↓ |

### 해석

- **비율·품질점수는 거의 불변**(quality_score 평균 0.012). 분자·분모가 함께 줄어
  ratio가 안정적 → 모델이 가장 강하게 쓰는 집계 신호는 사실상 그대로.
- **직접 입력인 로그 카운트만 ~0.11~0.16 하향**. 로그 압축으로 이미 완화됨.
- 모든 변화가 음(−) 방향 = dedup이 과대 카운트를 일관되게 낮춤.

### 가격 영향 상한 판단

- 핵심 집계 신호(quality_score, ratio)가 거의 안 움직이고, 최종 작가별 검색 델타는
  ±0.2(log) cap이 걸려 있어, **재학습 없이도 가격 영향은 작을 것**으로 판단.
- 단, 이는 **피처 섭동(perturbation) 기반 상한**이며 동결 87피처 모델 full 재추론
  가격 델타(원화)는 미산출. 정확한 원화 델타가 필요하면 별도로 동결 pp_y2 q50에
  raw/dedup 피처 행을 통과시켜 측정 가능(선택).

## 결론

- **파이프라인 정정(URL dedup)은 명백히 옳고 안전** → 반영 완료. 향후 스냅샷은 정상화.
- **동결 서빙 스냅샷/학습 피처 재생성·재학습은 영향이 작아 필수 아님**. 다음 스냅샷
  수집 사이클부터 자동 정상화되며, 즉시 재동결이 필요하면 별도 결정 사안
  (프로덕션 official v0.1 동결 상태 고려).
