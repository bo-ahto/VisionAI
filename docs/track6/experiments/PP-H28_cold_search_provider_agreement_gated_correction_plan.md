# PP-H28 Cold 검색 provider agreement 기반 제한 보정 검증 (설계서)

- 작성일: 2026-06-07
- 작성 목적: 검색 기반 보정(PP-H23)을 provider agreement로 제한 적용하면 안전하게 Cold를 개선하는지 검증한다. PP-COLD-ARTIFACT2가 정량화한 "검색 신호 기여분"을 운영 안전 형태로 살릴 수 있는지 본다.
- 성격: 검증(가설). 검색 보정은 점예측 직접 대체가 아니라 제한 보정/방어/검수 플래그 후보로만 본다.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 산출물은 전용 폴더 `experiments/track6/PP-H28_cold_search_provider_agreement_gated_correction/`.

## 1. 배경 / 예비 데이터 점검

- 데이터(전부 precomputed, live 검색 불필요):
  - `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/candidate_predictions.csv` — base `pp_y2`(pred_log) + h23 검색 보정 14개(7 source group × cap 0.1/0.2), actual, artist_key, split.
  - `experiments/track6/PP-H22_provider_agreement_stability/outputs/provider_agreement_by_artist.csv` — per-artist agreement score/grade/risk flag.
- 예비 점검 결과(중요):
  - provider agreement은 **78 작가만** 산출. score 0.265~0.648 → **high(≥0.70) 등급 없음**(69 low / 9 medium). disagreement_risk_flag True 71 / False 7.
  - 병합 시 grade 분포: missing 3279 / low 2207 / medium 366 / high 0. test엔 medium도 0.
  - 검색 보정은 broad하게 개선(val base MdAPE 0.413 → 0.36~0.39; test gallery_museum/social_blog 3지표 개선). 효과가 high agreement에 집중되지 않음(low에서도 개선).

## 2. 단일 가설 (및 귀무)

- H(PP-H28): "검색 보정을 provider agreement 상위(고신뢰)에서만 제한 적용하면 base 대비 안전하게(저신뢰 구간 악화 없이) 개선된다."
- 귀무/현실: agreement 데이터가 high 등급 0 + 커버리지 78작가뿐 + 효과가 agreement에 집중되지 않으면, agreement 게이팅은 실행 불가하고 검색 보정의 안전 장치는 다른 것(cap/방어층/검수 플래그)이어야 한다.

## 3. 후보 (모두 base pp_y2 대비)

- base: `pp_y2` (pred_log)
- ungated 검색 보정: `h23_{gallery_museum, social_blog, exhibition, art_general}_median_cap{0.1,0.2}` (전 행 적용)
- gate 변형(실행 가능한 것만): 최상 ungated source 기준
  - `gate_not_risk`: disagreement_risk_flag==False 에서만 보정, 그 외 base (7작가)
  - `gate_medium`: grade==medium 에서만 보정, 그 외 base (9작가)

## 4. 방법

1. candidate_predictions + agreement 병합(artist_search_name).
2. **반복 subsample 안정성**(보정은 상류 고정값이라 fold refit 불가 → 고정 후보의 robustness 평가): validation row 5fold×8 seeds + artist 5fold×8 seeds. 후보별 mean MdAPE/MAPE/p95 + base 대비 개선확률.
3. **agreement 진단**: grade(low/medium/missing)·disagreement_flag별 보정 효과(base vs h23)를 val/test로 분해 → 게이팅 실행 가능성/유효성 판정.
4. **test 확인 1회**: base + 선정 ungated 보정 + gate 변형.
5. 선택 기준: 보정 source/cap은 validation에서 MAPE/p95 방어 우선(MdAPE 비악화)으로 선정. test는 확인 전용.

## 5. 채택 / 중단 기준

- 검색 보정 채택(방어 후보): validation 반복 subsample에서 MAPE/p95 개선확률 ≥0.7 + MdAPE 비악화, test에서 MAPE/p95 개선.
- agreement 게이팅 채택: gate 변형이 ungated 대비 저신뢰 구간 악화를 줄이거나 전체 안전성을 높일 때. (현 데이터로는 high 없음 → 사실상 기각 예상)
- 결론 분기:
  - 게이팅 실행 가능·유효 → 제한 보정 정책 제안.
  - 게이팅 비현실(예상) → 검색 보정은 cap 기반 방어층 + 저신뢰 검수 플래그(표시)로만, agreement 커버리지 확대를 후속 데이터 과제로 분리.

## 6. 산출물 (전용 폴더)

- `outputs/repeated_subsample_summary.csv` — 후보별 안정성/개선확률
- `outputs/agreement_grade_breakdown.csv` — grade/flag별 보정 효과(val/test)
- `outputs/test_metrics.csv` — base/ungated/gate test 확인
- `reports/PP-H28_...md/.html`, `artifacts/run_config.json`
- 요약 `docs/track6/experiments/pp_h28_cold_search_provider_agreement_gated_correction_summary.md`, INDEX/matrix 갱신

## 7. 누수/정직성 주의

- [ ] 보정 source/cap은 validation에서만 선택, test 확인 1회.
- [ ] 검색 보정은 상류 고정 예측값이며 fold refit이 아님을 명시(반복 subsample = robustness 평가).
- [ ] agreement 커버리지(78작가)·high 부재를 결론에 명시.
- [ ] 검색 보정은 점예측 직접 대체가 아니라 방어/표시 후보로 한정.

## 8. 다음 액션 연결

- 검색 보정이 방어로 유효하면 → cold_prediction artifact에 cap 기반 검색 방어층(저신뢰 검수 플래그 동반) 추가 검토.
- agreement 게이팅이 필요하면 → 검색 수집 커버리지 확대(전 작가 dual-provider) + high 등급 확보를 별도 데이터 과제로.
