# PP-CSRCH2 검색 수집 확대 runbook (Cold Phase 2-3b)

- 착수: 2026-06-10 사용자 결정. 근거: PP-CSRCH1 — per-artist delta는 실수집으로만 획득 가능, 기대 효과 = 미커버 작가 MAPE 0.938→0.849 방향.
- 수집기: 기존 운영 수집기 `scripts/track6/run_pp_h11_operational_search_experiments.py` (resume 캐시 지원, provider: naver_html + ddgs fallback).

## 3단계 계획

1. **파일럿 수집 (실행 중)**: `--artist-scope warm --selection-policy train_frequency --limit-artists 150 --max-results 5`
   - 시스템 python(requests/duckduckgo_search 보유)으로 실행. 라이브 연결 검증 완료.
   - 산출: `data/track6/external_search/operational/` 캐시 + features CSV.
2. **delta 파생**: 수집된 warm 작가에 PP-H23 `gallery_museum_median cap0.2` 보정 공식 적용(`run_pp_h20_h26_search_feature_expansion.py` 파이프라인 재사용) → 작가단위 delta → v0.3 lookup 확장본 생성.
3. **pseudo-cold 검증 (채택 게이트)**: PP-PCOLD1 마스크 작가 중 신규 커버된 작가에서 "real per-artist delta vs 상수 fallback(-0.0313) vs guard-only" 3자 비교. **real delta가 상수 대비 MAPE/p95 개선 + seed 방향 일치 시** 전량 수집(잔여 warm 작가) 확정 및 lookup v0.4/v0.5 정책 갱신(ARTIFACT 갱신).

## 주의

- 0604 사용 금지(전 단계). 수집 자체는 라벨 미사용이라 leakage 없음.
- 외부 수집은 rate limit/차단 가능 — 수집기 resume 캐시로 중단/재개.
- 신규 작가 서빙 경로: 수집 확정 시 "작가 온보딩 시 1회 검색 수집 → delta 계산 → lookup 등록" 운영 절차 문서화 필요.
