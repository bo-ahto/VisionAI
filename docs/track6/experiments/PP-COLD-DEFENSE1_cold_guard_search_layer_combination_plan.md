# PP-COLD-DEFENSE1 Cold guard + 검색 방어층 결합 (설계서)

- 작성일: 2026-06-07
- 작성 목적: PP-QR4가 채택한 guard 방어와 PP-H28이 유효 판정한 검색 보정을 한 base 위에 결합해, 두 방어가 **가산적으로** MAPE/p95를 개선하는지 **중복**인지 검증한다.
- 성격: 검증(가설). 방어층 결합. 대표 점예측은 교체하지 않음.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 산출물은 전용 폴더 `experiments/track6/PP-COLD-DEFENSE1_cold_guard_search_layer_combination/`.

## 1. 배경

- PP-QR4 guard(`guard_y18_lgb_q40_qwidth67_gap50_down_w0.50`): base=PP-Y18, lgb_q40으로 하향. test 0.4178/0.964/2.538. 반복 holdout 견고.
- PP-H28 검색 보정(gallery_museum/social_blog cap0.2): base=pp_y2. test 0.4313/0.929/3.139(3지표 개선). agreement 게이팅은 비현실 판정.
- 두 후보의 base가 다름(guard=PP-Y18, 검색=pp_y2)이고 **PP-Y18 자체가 search 피처 기반** → 검색 보정을 PP-Y18 위에 얹으면 중복 가능성. 이를 데이터로 판정한다.
- 데이터 join 확인: 두 예측 소스(QR2 frame, H28 candidate_predictions)는 cold val/test 5852행 전부 join되고 pp_y2 base가 동일(diff 0.0).

## 2. 단일 가설 / 귀무

- H(PP-COLD-DEFENSE1): "PP-Y18 대표 위에 guard와 검색 보정을 함께 적용하면 guard 단독 대비 MAPE/p95가 추가 개선된다(가산)."
- 귀무: PP-Y18이 이미 search 기반이라 검색 보정이 중복 → guard+search ≈ guard 단독, 또는 악화.

## 3. 후보 (base = PP-Y18 대표, vs base 비교)

- `y18_base`: PP-Y18 qwidth (대표)
- `guard`: PP-QR4 guard (y18 → lgb_q40 하향, qwidth_q67/gap_q50/w0.5)
- `search_gm`, `search_sb`: y18 + 검색 delta(=h23_{gallery_museum,social_blog}_cap0.2 − pp_y2)
- `guard_search_gm`, `guard_search_sb`: guard + 검색 delta
- 참고: `pp_y2_search_gm`(=H28 native, pp_y2 + 검색) — 중복 진단 비교용

## 4. 방법

1. QR2 frame(y18, lgb_q40, cat_q40, quantile_width_log, actual) + H28 검색 delta를 (_track6_row_id, split)로 join.
2. guard 임계값은 validation에서 산출(PP-QR4와 동일: qwidth_q67≈1.4612, gap_q50≈0.0772). 검색 delta는 상류 고정값.
3. **반복 subsample 안정성**: validation row 5fold×8 + artist 5fold×8, 후보별 mean MdAPE/MAPE/p95 + y18_base 대비 개선확률.
4. **test 확인 1회**: 전 후보.
5. **가산성 진단**: guard_search vs guard, vs search 단독의 ΔMAPE/Δp95 분해. 검색 delta가 guard 위에서 추가 개선을 주는지.

## 5. 채택 / 중단 기준

- 결합 채택: `guard_search`가 validation 반복 subsample에서 guard 단독 대비 MAPE 또는 p95 개선확률 높고(≥0.6), test에서 guard 단독 대비 MAPE/p95 비악화·개선. MdAPE 비악화.
- 중복 판정: guard_search ≈ guard(개선 미미) 또는 악화 → 검색 보정은 PP-Y18 위에서 중복. cold 방어는 guard 단독 유지(=PP-COLD-ARTIFACT1), 검색 보정은 search-light base(v0.2 operational)에서만 가치 재검토.
- 주의: test로 후보 선택 금지. 결합 선택 기준은 validation.

## 6. 산출물 (전용 폴더)

- `outputs/repeated_subsample_summary.csv`, `outputs/test_metrics.csv`, `outputs/additivity_decomposition.csv`
- `reports/PP-COLD-DEFENSE1_...md/.html`, `artifacts/run_config.json`
- 요약 `docs/track6/experiments/pp_cold_defense1_..._summary.md`, INDEX/matrix 갱신

## 7. 데이터 소스

- QR2 frame: PP-Y18/PP-Y2/PP-QR1 예측 (qr2 loader).
- 검색 delta: `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/candidate_predictions.csv`.

## 8. 다음 액션 연결

- 결합 유효 → cold_prediction artifact 방어층을 guard+search 2단으로 갱신(저신뢰 검수 플래그 동반).
- 중복 → guard 단독 유지. 검색 보정은 search-free v0.2 operational에 적용해 search 손실분 회복 가능성 별도 검토.
