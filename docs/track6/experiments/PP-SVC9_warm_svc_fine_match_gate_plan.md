# PP-SVC9 Warm svc 최정밀 매칭 게이트 (fine-match-only) (설계서)

- 작성일: 2026-06-07
- 작성 목적: PP-SVC8 진단(“svc는 최정밀 매칭에서만 pp_v8보다 강건”)을 운영 후보로 검증한다. 최정밀 매칭에서만 svc를 쓰고 나머지는 pp_v8을 쓰는 게이트가 **운영 기본값 pp_v8을 두 영역(고정 test + 0604)에서 모두 이기는지(순지배)** 확인한다.
- 성격: 기존 두 예측값(svc, pp_v8)의 구조적 게이트 결합. 새 모델/피처 없음.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 모든 산출물은 전용 폴더 `experiments/track6/PP-SVC9_warm_svc_fine_match_gate/` 아래에만 저장.

## 1. 배경 (PP-SVC8)

- svc residual std: 고정 test 0.42 → 0604 1.64(4배). pp_v8은 0.40→0.69.
- 0604 레벨별 svc vs pp_v8 MdAPE:

| svc_group_level | 0604 n | svc MdAPE | pp_v8 MdAPE | svc std / pp_v8 std |
|---|---:|---:|---:|---:|
| artist_medium_support_size (최정밀) | 91 | **0.143** | 0.171 | 0.97 |
| artist_size | 224 | 0.248 | 0.189 | 2.33 |
| artist | 412 | 0.338 | 0.255 | 2.96 |
| medium_support_size | 66 | 0.485 | 0.250 | 1.17 |

- 즉 svc는 **artist_medium_support_size(최정밀 작가-매체-지지체-크기 매칭)에서만** pp_v8보다 강건. 고정 test에서도 이 레벨에서 svc가 강함(svc MdAPE 0.098).

## 2. 단일 가설

- H(PP-SVC9): "svc를 최정밀 매칭(`artist_medium_support_size`)에서만 사용하고 나머지는 pp_v8을 사용하는 게이트는, 운영 기본값 pp_v8을 **고정 test와 0604 모두에서 MdAPE/MAPE 비악화로 이긴다**(순지배)."
- 근거: 최정밀 레벨에선 양 영역 모두 svc가 pp_v8보다 좋고, 그 외 레벨은 pp_v8 그대로이므로 두 영역 모두에서 pp_v8 이상이어야 한다.
- 누수 방지 핵심: **게이트 레벨 집합은 PP-SVC8 분산 논리에서 구조적으로 결정**(0604로 고르지 않음). 게이트 내부 가중치만 고정 validation에서 선택.

## 3. 후보 (세 영역 모두 평가: 고정 val / 고정 test / 0604)

| 역할 | 후보 | 정의 |
|---|---|---|
| control A | `pp_v8` | service_primary (전 영역 w=0) |
| control B | `blend_0.70` | 70:30 전역 (보고 기준) |
| 주 후보 | `fine_gate_w*` | level==artist_medium_support_size → `w_fine*svc+(1-w_fine)*pp_v8`, 그 외 → pp_v8 |
| 민감도 | `fine_gate_plus_artist_size` | 게이트 레벨에 artist_size 추가(거친 레벨 포함 시 악화 확인용) |

- `w_fine` 후보 grid: `{0.5, 0.7, 1.0}`, **고정 validation의 최정밀 레벨 subset에서 MdAPE 최소**로 선택.

## 4. 방법

1. 고정 validation에서 최정밀 레벨 subset만 보고 `w_fine` 선택(grid). 게이트 레벨 집합은 §2대로 고정.
2. 선택된 게이트를 고정 test와 0604에 동일 적용.
3. 0604는 `actual_price_usd_equiv >= 50` 필터(운영 평가 기준).
4. 각 영역에서 pp_v8/70:30/게이트의 MdAPE/MAPE/p95 + 게이트가 적용된 행 수(최정밀 비율) 기록.
5. 게이트 적용 행만의 svc vs pp_v8 비교(게이트가 실제로 그 구간을 개선하는지 직접 확인).

## 5. 채택 / 중단 기준

- 채택(운영 기본값 개선 후보): 게이트가 **고정 test와 0604 모두에서 pp_v8 대비 MdAPE 비악화 + 최소 한 영역 개선**, 그리고 두 영역 모두 MAPE 비악화.
- 강한 채택: 두 영역 모두 MdAPE/MAPE 개선(순지배).
- 보조: 0604만 개선하고 고정 test는 동률 → 0604(최근) 기준 운영 후보로 유지.
- 중단: 어느 영역에서 pp_v8 대비 악화 → 게이트도 부적합, pp_v8 단독 유지.
- 주의: 70:30을 이기는 것은 목표가 아님(70:30은 0604에서 붕괴). 비교 기준은 pp_v8.

## 6. 산출물 (전용 폴더)

- `experiments/track6/PP-SVC9_warm_svc_fine_match_gate/`
  - `outputs/region_candidate_metrics.csv`
  - `outputs/gate_applied_subset_compare.csv` (게이트 적용 행의 svc vs pp_v8)
  - `outputs/w_fine_validation_selection.csv`
  - `reports/PP-SVC9_warm_svc_fine_match_gate.md` / `.html`
  - `artifacts/run_config.json`
- 요약: `docs/track6/experiments/pp_svc9_warm_svc_fine_match_gate_summary.md`
- INDEX/매트릭스 갱신.

## 7. 데이터 소스 (PP-SVC7/8과 동일)

- 고정 split: `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/predictions.csv`
- 0604: `models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/operational_predictions_with_actual.csv`

## 8. 누수 방지 체크리스트

- [ ] 게이트 레벨 집합은 구조적(PP-SVC8)으로 결정, 0604로 고르지 않았는가.
- [ ] `w_fine`는 고정 validation 최정밀 subset에서만 선택했는가.
- [ ] 고정 test와 0604는 확인용으로만 사용했는가.
- [ ] 0604 <$50 필터를 적용했는가.

## 9. 다음 액션 연결

- 순지배 채택 시 → 게이트를 pp_v8 대체 운영 후보로 PP-I6 service_recommendation 표에 추가, artifact화(게이트 규칙 = svc_group_level 분기) 검토.
- 0604만 개선 시 → 최근 기준 운영 후보로 유지하고, 비교군 prior 최근거래 갱신(staleness 해소) 후속 실험과 결합.
- 중단 시 → pp_v8 단독 유지, svc는 표시/신뢰도 보조로만.
