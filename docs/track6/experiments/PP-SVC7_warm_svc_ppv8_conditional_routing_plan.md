# PP-SVC7 Warm 70:30 vs 운영 pp_v8 조건부 라우팅 + 0604 동시 검증 (설계서)

- 작성일: 2026-06-07
- 작성 목적: Warm 보고 기준 후보(`PP-SVC3 70:30`)와 운영 기본값(`pp_v8 service_primary`)이 영역마다 우열이 뒤집히는 문제를, 운영 입력으로 계산 가능한 신호로 **조건부 라우팅**해서 두 영역 모두 잡을 수 있는지 검증한다.
- 성격: 신규 모델 학습이 아니라, 기존 두 후보의 **예측값 결합/라우팅** 실험.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 모든 산출물은 전용 폴더 `experiments/track6/PP-SVC7_warm_svc_ppv8_conditional_routing/` 아래에만 저장.

## 1. 배경 (데이터로 확인된 모순)

- `PP-SVC3 70:30` = `0.70 * svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded` (= 운영 `v01_operational`).
- `pp_v8` = `pp_v8_compact_blend_mape_guarded` (= 운영 `service_primary`).
- 두 영역의 MdAPE:

| 영역 | pp_v8 | 70:30 | 승자 |
|---|---:|---:|---|
| 고정 split test (607행) | 0.1632 | 0.1405 | 70:30 |
| 0604 신규 라벨 (<$50 제외, 829행) | 0.2298 | 0.2779 | pp_v8 |

- svc 신뢰도 segment별 승자(예비 분석):

| segment | 고정 test 승자 | 0604 승자 |
|---|---|---|
| low_n | 70:30 | pp_v8 |
| medium_n | 70:30 | pp_v8 |
| high_n | pp_v8 | pp_v8 |

- 즉 같은 svc-신뢰도 segment에서 승자가 영역마다 뒤집힌다 → 우열이 per-row 패턴이 아니라 **영역(distribution shift)** 일 가능성이 큼. 원인: `svc_numeric` 컴포넌트가 0604에서 전반적으로 악화(0604 MdAPE 0.3072).

## 2. 단일 가설

- H(PP-SVC7): "운영 입력으로 계산 가능한 신호(svc 신뢰도/모델 disagreement)로 70:30과 pp_v8을 조건부 라우팅하면, 고정 test에서는 70:30 수준, 0604에서는 pp_v8 수준을 **동시에** 달성하는 후보를 validation에서 선택할 수 있다."
- 귀무 입장: 라우팅 신호가 영역 간 전이되지 않으면, validation에서 고른 라우터는 한쪽 영역에서 반드시 열위가 된다(영역 선택 문제로 환원).
- 변수 축은 **라우팅 신호·가중치 1축**만 비교. 새 모델/피처는 추가하지 않는다.

## 3. 비교 후보 (세 영역 모두에서 평가)

평가 영역: 고정 validation / 고정 test / 0604(<$50 제외).

| 역할 | 후보 | 정의 |
|---|---|---|
| control A | `pp_v8` | service_primary (w=0.0) |
| control B | `blend_0.70` | 70:30 = v01_operational (w=0.70) |
| 참고 | `global_w_sweep` | 전역 고정 가중치 w∈{0.0,0.1,…,1.0} (영역별 tradeoff 시각화) |
| 라우터 | `router_svc_coverage_tier` | segment별 best weight 선택 |
| 라우터 | `router_svc_group_level` | segment별 best weight 선택 |
| 라우터 | `router_disagree_bin` | `|svc − pp_v8|` 로그 disagreement 구간별 best weight 선택 |

- weight grid: `{0.0, 0.3, 0.5, 0.7}` (0.0=pp_v8, 0.7=70:30).
- 모든 후보 예측: `pred_log = w * svc_numeric_seed_mean + (1−w) * pp_v8`.

## 4. 방법 (라우팅 규칙 선택 = 고정 validation 전용)

1. 신호 segment(또는 disagreement 구간)별로 weight grid에서 **고정 validation MdAPE 최소** weight를 선택. segment rows `< 30`이면 validation 전역 best weight로 fallback.
2. disagreement 구간 경계는 validation의 `|svc−pp_v8|` 분위수(33/66)로 정하고 test/0604에 그대로 적용.
3. 선택된 segment→weight 맵을 고정 test와 0604에 동일 적용.
4. 0604는 **두 번째 확인 영역**이며 라우팅 규칙 선택에 사용하지 않는다(test도 마찬가지).
5. seed/grid/segment 정의는 `artifacts/run_config.json`에 저장.

## 5. 채택 / 중단 기준

- 채택(영역 통합 라우팅 성립): 어떤 라우터가 **고정 test MdAPE ≤ `blend_0.70` + 0.003** 이고 **0604 MdAPE ≤ `pp_v8` + 0.003** 을 동시에 만족(두 영역 모두에서 더 나은 고정 후보에 근접).
- 보조: 한 영역만 만족하고 다른 영역은 열위 → 라우팅은 부분적, 운영 기본값은 영역 신뢰 기준으로 별도 결정.
- 중단(가설 기각): 모든 라우터가 한 영역에서 명확히 열위 → "70:30 vs pp_v8 차이는 라우팅 불가한 영역 차이"로 결론. 운영 기본값은 최신 0604 기준 `pp_v8` 유지, 70:30은 보고/과거 test 기준 후보로 한정.

## 6. 산출물 (전용 폴더)

- `experiments/track6/PP-SVC7_warm_svc_ppv8_conditional_routing/`
  - `outputs/region_candidate_metrics.csv` — 후보 × 영역(val/test/0604) MdAPE/MAPE/p95
  - `outputs/global_weight_sweep.csv` — 전역 weight별 영역 성능(tradeoff 곡선)
  - `outputs/router_segment_weight_map.csv` — 신호 segment별 선택 weight + validation 근거
  - `outputs/router_0604_segment_breakdown.csv` — 0604에서 segment별 라우터 vs pp_v8 비교
  - `reports/PP-SVC7_warm_svc_ppv8_conditional_routing.md` / `.html`
  - `artifacts/run_config.json`
- 요약 문서: `docs/track6/experiments/pp_svc7_warm_svc_ppv8_conditional_routing_summary.md`
- INDEX/매트릭스 갱신.

## 7. 데이터 소스

- 고정 split 예측: `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/predictions.csv` (`svc_numeric_seed_mean`, `pp_v8_compact_blend_mape_guarded`, `svc_coverage_tier`, `svc_group_level`, `svc_group_n`).
- 0604 예측+실제: `models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/operational_predictions_with_actual.csv` (`svc_numeric_seed_mean_pred_log`, `pp_v8_..._pred_log`, `v01_operational_pred_log`, `actual_price_krw`, `actual_price_usd_equiv`, 동일 svc 신호).
- 0604는 `actual_price_usd_equiv >= 50` 필터(검수 라벨 제외, 운영 평가 기준과 동일).

## 8. 누수 방지 체크리스트

- [ ] 라우팅 weight/segment/disagreement 경계는 고정 validation에서만 산출했는가.
- [ ] 고정 test와 0604는 확인용으로만 사용했는가(라우팅 선택 금지).
- [ ] 라우팅 신호가 운영 입력으로 계산 가능한 값(svc 신뢰도, 모델 disagreement)인가.
- [ ] 0604 <$50 필터를 운영 평가와 동일하게 적용했는가.

## 9. 다음 액션 연결

- 채택 시 → 라우터를 v0.1 운영 정책 후보로 PP-I6 service_recommendation 표에 추가하고 artifact화 검토.
- 중단 시 → 운영 기본값 `pp_v8` 유지 근거를 "영역 차이(distribution shift)"로 문서화하고, 다음 Warm 실험은 0604 신규 라벨에서 svc 컴포넌트가 악화된 원인 분석(svc prior 갱신/staleness)으로 이동.
