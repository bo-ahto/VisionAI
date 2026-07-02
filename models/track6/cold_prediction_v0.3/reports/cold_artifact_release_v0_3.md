# Cold prediction v0.3 (guard + search 2-layer defense) release

- 작성일(고정): 2026-06-07T00:00:00
- 상태: validated_two_layer_defense_freeze

## 정책

- 대표 점예측: PP-Y18 qwidth — test MdAPE 0.4247 / MAPE 0.9910 / p95 3.3053
- 방어(guard+search): test MdAPE 0.4098 / MAPE 0.8493 / p95 2.3465
- 참고 guard 단독: test MdAPE 0.4178 / MAPE 0.9640 / p95 2.5377
- 검색 커버리지(test): 1.000, 검수 플래그율(test): 0.452

## 검증

- 후처리기 재현(vs 독립 계산) max abs diff = 3.55e-15
- PP-COLD-DEFENSE1 guard_search_gm MdAPE 재현: True (defense1 0.4098 vs artifact 0.4098)
- 두 방어 가산성: PP-COLD-DEFENSE1 redundancy gap ≈ 0 (evidence/PP-COLD-DEFENSE1).

## 정직한 범위

- 후처리층만 실행 가능(component 예측 + artist_key 입력). 하부 Quantile/PP-Y18은 상류 search 의존.
- 검색 delta는 작가 단위 frozen snapshot(372 작가). 신규 작가 → guard fallback. 검색층은 분산 추가 → review_flag 동반.
- 0604는 전부 warm(0 cold) → cold 운영 트래픽 확보 후 재평가 필요.
- 3종 비교: v0.1(guard only) / v0.2_operational(search-free raw-input) / v0.3(guard+search 최고 정확도).

## 구성

- `config/cold_model_policy_v0_3.json`, `cold_postprocess_params_v0_3.json`, `search_delta_lookup_v0_3.json`
- `predict/apply_cold_postprocess_v0_3.py`, `evidence/PP-COLD-DEFENSE1/`, `reproduction/upstream_sources.json`
- `manifest/MANIFEST.sha256`