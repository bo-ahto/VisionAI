# Claude Code용 가격 예측 실험 인수인계

- 작성일: 2026-06-07
- 목적: Claude Code가 Track6 가격 예측 실험을 바로 파악하고, 성능 개선 실험을 추가로 설계/실행할 수 있게 하는 요약 문서
- 핵심 원칙: validation/OOF에서 후보를 선택하고, test는 최종 확인용으로만 사용

## 1. 먼저 봐야 할 파일

| 구분 | 경로 | 용도 |
|---|---|---|
| 전체 후처리 실험 매트릭스 | `docs/track6/experiments/postprocessing_experiment_matrix.md` | 실험군, 실행 순서, 완료/보류 상태 확인 |
| v0.1 모델 정책 | `models/track6/price_prediction_v0.1/config/model_policy_v0.1.json` | 중간 동결 기준 Warm/Cold 후보 확인 |
| v0.1 README | `models/track6/price_prediction_v0.1/README.md` | v0.1 번들 구조와 재현 기준 |
| 운영 릴리스 문서 | `models/track6/price_prediction_v0.1/operational/reports/operational_release_v0_1.md` | 실제 운영 기본값과 0604 평가 결과 |
| 중간 피처/모델 리포트 | `models/track6/price_prediction_v0.1/evidence/reports/model_feature_selection_midterm_report.md` | Warm/Cold 피처와 모델 선정 근거 |
| 최신 Huber 원인 보정 실험 | `docs/track6/experiments/PP-WHUBER10_warm_artwork_error_cause_correction.md` | 작품별 오차 원인 기반 보정 결과 |
| Cold Quantile 재검증 | `docs/track6/experiments/pp_qr3_cold_quantile_oof_holdout_revalidation_summary.md` | Cold qwidth/pred_gap 후속 후보 |
| 최신 통합 감사 | `docs/track6/experiments/pp_i6_latest_final_control_integration_summary.md` | Warm/Cold 최신 후보를 한 표로 비교 |

## 2. 현재 기준 후보를 혼동하지 말 것

### 2.1 중간 동결 기준 v0.1

`models/track6/price_prediction_v0.1/config/model_policy_v0.1.json` 기준.

| 구분 | 후보 | test MdAPE | test MAPE | test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| Warm 중간 동결 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | 0.1405 | 0.2748 | 0.8331 | 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30% |
| Cold reference | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | 0.4247 | 0.9910 | 3.3053 | LightGBM Quantile + qwidth 구간 보정 |

### 2.2 운영 v0.1 릴리스 기준

`models/track6/price_prediction_v0.1/operational/reports/operational_release_v0_1.md` 기준.

| 구분 | 운영 판단 | 이유 |
|---|---|---|
| Warm 운영 기본값 | `service_primary_pred_price_krw` = `pp_v8_compact_blend_mape_guarded` | 0604 신규 라벨 평가에서 70:30 후보보다 MdAPE/MAPE/p95가 낮았음 |
| Warm 70:30 후보 | `v01_operational_pred_price_krw`로 비교용 유지 | 중간 리포트 기준 최고 후보였지만 0604 신규 데이터에서는 일부 구간 과대 보정 |
| Cold 운영 자동 적용 | 보류 | artifact 고정과 신뢰도/범위 정책 추가 필요 |

정리:
- 실험 성능 기준으로는 `PP-SVC3 70:30`이 Warm 중간 최고 후보.
- 운영 릴리스 기준으로는 0604 신규 라벨에서 `pp_v8_compact_blend_mape_guarded`가 더 안정적이어서 서비스 기본값.
- 다음 실험은 “중간 실험 최고 후보를 더 개선할지”와 “운영 기본값을 더 안정화할지”를 분리해서 진행해야 함.

## 3. Warm 실험 요약

### 3.1 Warm의 현재 강한 신호

| 실험 | 핵심 결과 | 판단 |
|---|---|---|
| `PP-SVC3` | `blend_svcnum_ppv8_wsvc_0.70` test `0.1405 / 0.2748 / 0.8331` | 중간 리포트 기준 Warm 1순위 |
| `PP-SVC4` | 70:30 결합이 반복 선택에서도 자주 선택됨 | 70:30 방향성은 안정 신호 있음 |
| `PP-SVC5` | `wsvc=0.60`에서 test MdAPE `0.1362`, MAPE `0.2717`, p95 `0.8329` | test 관찰상 개선이나 반복 안정성 부족 |
| `PP-SVC6` | 고정 test는 `0.575~0.600`이 좋지만 반복 holdout은 `0.725` 또는 `0.850~0.875` 중심 | 단일 test만 보고 비율 교체하면 위험 |
| `PP-WHUBER9` | 큰 오차 방어 후보 test `0.1396 / 0.2733 / 0.8016` | 기본 교체보다 보조 정책 후보 |
| `PP-WHUBER10` | 원인 기반 보정 test 최상위 `0.1374 / 0.2774 / 0.8292` | MdAPE/p95 개선, MAPE 악화. 기본 반영 보류 |
| `PP-AMW5` | 작가 메타 핵심 Huber 잔차 보정 test `0.1368 / 0.2746 / 0.8323` | 생년/작품 수/판매중 작품 수/팔로워가 남은 Warm 오차를 소폭 설명. 반복 split 검증 후보 |
| `PP-AMW6` | 작가 메타 Huber test `0.1368 / 0.2746 / 0.8323`, 생년 구간 median test `0.1381 / 0.2740 / 0.8191` | 대표 정확도와 큰 오차 방어 후보를 분리. 운영 반영 전 0604/운영 artifact 재검증 필요 |

### 3.2 Warm에서 중요한 피처/구조

- `artist_key`: Warm에서 가장 중요한 작가 기준선.
- 크기 피처: `width_cm`, `height_cm`, `area_cm2`, `log_area`.
- 재료/지지체: `medium_category`, `support_category`, `medium_support_bucket`.
- 유사 작품 기반 가격 피처: 작가/크기/재료 조건으로 만든 가격 prior.
- Huber 구조: 선형 중심선을 만들고 큰 오차는 완전히 따라가지 않도록 눌러 학습.
- 결론: Warm은 “작가 기준선 + 크기 + 유사 작품 가격 prior + 약한 방어 보정” 조합이 강함.

### 3.3 Warm에서 바로 해볼 만한 추가 실험

| 우선순위 | 실험 아이디어 | 이유 | 주의 |
|---:|---|---|---|
| 1 | `PP-SVC6` 비율 재검증 확장: `wsvc=0.50~0.75`를 artist holdout/0604로 재검증 | test상 `0.575~0.600` 개선 신호가 있음 | test로 비율 선택 금지 |
| 2 | `PP-WHUBER10` 원인 보정에 MAPE guard 추가 | 기존 원인 보정은 MdAPE/p95 개선 대신 MAPE 악화 | validation에서 MAPE 악화 없는 후보만 선택 |
| 3 | 과대예측 구간 전용 보정 | 0604와 PP-WHUBER10 모두 일부 유사작품 표본 부족 구간 과대예측이 큼 | 과소예측 작품까지 같이 내리면 p95 악화 가능 |
| 4 | `pp_v8` 운영 기본값과 `PP-SVC3` 70:30 후보의 조건부 라우팅 | 0604에서는 pp_v8, 기존 test에서는 PP-SVC3가 강함 | 라우팅 기준은 validation/OOF에서만 선택 |
| 5 | `PP-AMW6` 목적별 후보를 0604 신규 데이터와 운영 artifact 형태로 재검증 | 작가 메타 Huber는 대표 정확도, 생년 구간 median은 MAPE/p95 방어 신호 | 기존 test만으로 운영 기본값 교체 금지 |
| 6 | Huber residual 보정 후보를 운영 artifact로 고정 가능한 형태로 재구현 | 실험 후보와 운영 코드 사이 차이를 줄일 수 있음 | component chain 재현성 필요 |

## 4. Cold 실험 요약

### 4.1 Cold의 현재 강한 신호

| 실험 | 핵심 결과 | 판단 |
|---|---|---|
| 기존 기준 `PP-Y2` | test MdAPE `0.4421`, MAPE `1.0484`, p95 `3.3537` | Cold 단일 기준선 |
| `PP-Y18` | qwidth bin 보정 test `0.4247 / 0.9910 / 3.3053` | Cold 대표 개선 후보 |
| `PP-Y21` | `PP-Y18` 후보 artist holdout 개선확률 MdAPE `0.8625`, MAPE `0.9875`, p95 `0.9625` | Cold 개선 후보 유지 가능 |
| `PP-QR3` | `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` test MdAPE `0.4175` | 더 개선된 test 신호, 추가 split 검증 필요 |
| `PP-I7` | Cold 검색 제한 보정 test MdAPE `0.4179~0.4240` | 개선 신호 있으나 validation/test 선택 불일치 |

### 4.2 Cold에서 중요한 피처/구조

- 기본 작품 피처: 크기, 면적, 비율, depth/3D, 재료, 지지체, bucket.
- 작가 메타: 작가 이력량, 팔로워, 전시/갤러리/검색 기반 보조 피처.
- LightGBM Quantile: Cold에서 q-width로 예측 불확실성 구간을 나누는 데 유효.
- CatBoost: 범주형/조합 처리에 유리하나 현재 최고 후보는 LightGBM Quantile 기반 qwidth 보정 계열.
- 검색 피처: DuckDuckGo/Python 검색 라이브러리 캐시와 네이버 API 방향. Google Custom Search는 현재 핵심 실험 로직이 아님.
- 결론: Cold는 점 예측 확정 모델보다 “참고 예측가 + 넓은 범위 + 낮은 신뢰도 + qwidth 기반 보정”이 현실적.

### 4.3 Cold에서 바로 해볼 만한 추가 실험

| 우선순위 | 실험 아이디어 | 이유 | 주의 |
|---:|---|---|---|
| 1 | `PP-QR3` test 개선 후보를 반복 split/artist holdout으로 재검증 | test MdAPE `0.4175` 신호가 있음 | test 상위 후보를 바로 채택하지 말 것 |
| 2 | `qwidth + pred_gap + search_quality` 수동 구간 보정 | Cold에서 자동 라우팅보다 구간 cap 보정이 더 안정적일 가능성 | min rows, cap, fallback 고정 필요 |
| 3 | 검색 보정 후보를 provider agreement 기준으로 제한 적용 | 검색 피처는 오염 가능성이 있어 점 예측 직접 반영 위험 | 낮은 agreement는 신뢰도 하향/검수 플래그 우선 |
| 4 | Cold artifact 고정 | 현재 Cold 운영 자동 적용이 보류된 핵심 이유 | qwidth 모델, correction map, fallback 정책을 한 번에 고정해야 함 |
| 5 | LightGBM Quantile alpha grid 재검증 | q40/q50/q60 중심선 차이가 Cold MAPE에 영향 가능 | validation OOF 기준으로 alpha 선택 |

## 5. 절대 지켜야 할 실험 규칙

- test set으로 후보를 고르지 않는다.
- residual 보정, stacking, meta model은 OOF 예측값으로만 학습한다.
- 보정값은 validation 또는 validation 내부 fold에서 만든다.
- test는 최종 후보 확인용으로 한 번만 사용한다.
- 검색/외부 데이터는 수집 시점, provider, query, match quality를 저장한다.
- 운영 입력에서 알 수 없는 값은 라우팅/보정 기준으로 쓰지 않는다.
- 실험은 반드시 `experiments/track6/<EXPERIMENT_ID>_<slug>/`에 저장한다.
- 실험 후 `docs/track6/experiments/postprocessing_experiment_matrix.md`를 업데이트한다.

## 6. 재현/실행 명령 모음

### 6.1 Warm 작품별 원인 보정 재실행

```bash
python3 scripts/track6/run_pp_whuber10_warm_artwork_error_cause_correction.py
```

주요 산출물:
- `experiments/track6/PP-WHUBER10_warm_artwork_error_cause_correction/outputs/test_artwork_error_diagnostics.csv`
- `experiments/track6/PP-WHUBER10_warm_artwork_error_cause_correction/outputs/test_once_metrics.csv`
- `docs/track6/experiments/PP-WHUBER10_warm_artwork_error_cause_correction.md`

### 6.2 Warm 70:30 비율 안정성 계열

```bash
python3 scripts/track6/run_pp_svc6_fallback_ppv8_blend_stability.py
```

확인 포인트:
- `wsvc=0.55~0.60`이 정말 안정적인지.
- 반복 holdout에서 왜 `0.725` 또는 `0.850~0.875`가 선택되는지.
- 0604 신규 라벨에서도 같은 방향인지.

### 6.3 Cold qwidth 후보 재검증

```bash
python3 scripts/track6/run_pp_qr3_cold_quantile_oof_holdout_revalidation.py
```

확인 포인트:
- `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50`의 test 개선이 재현되는지.
- `PP-Y18 qwidth_bin_oof_min30_cap0.25`보다 안정적인지.

### 6.4 운영 v0.1 0604 평가

```bash
python3 models/track6/price_prediction_v0.1/operational/scripts/evaluate_operational_v0_1_0604.py
```

확인 포인트:
- `service_primary`와 `v01_operational 70:30`의 차이.
- 50달러 미만 라벨 제외 기준 유지 여부.
- 과대예측 작품군의 공통 원인.

## 7. Claude Code에게 줄 추가 실험 프롬프트 예시

```text
Track6 가격 예측 실험을 이어서 진행한다.

먼저 docs/track6/experiments/claude_code_experiment_handoff.md,
docs/track6/experiments/postprocessing_experiment_matrix.md,
models/track6/price_prediction_v0.1/config/model_policy_v0.1.json,
models/track6/price_prediction_v0.1/operational/reports/operational_release_v0_1.md 를 읽는다.

목표는 test 누수 없이 Warm/Cold 성능 개선 후보를 추가 검증하는 것이다.

우선순위:
1. Warm: PP-SVC3 70:30 후보와 operational service_primary 후보의 차이를 고정 split/0604 기준으로 비교하고, 조건부 라우팅 가능성을 검증한다.
2. Warm: PP-WHUBER10 원인 기반 보정에 MAPE guard를 추가해 MdAPE/p95 개선과 MAPE 악화 방지를 동시에 만족하는 후보를 찾는다.
3. Cold: PP-QR3의 qwidth+pred_gap 후보를 반복 split/artist holdout으로 재검증하고, 개선이 유지되면 artifact 고정 계획을 작성한다.
4. Cold: 검색 피처는 provider agreement와 수동 검수 필요 여부를 함께 써서 제한 보정 또는 신뢰도 하향 정책으로만 적용한다.

실험 산출물은 experiments/track6/<ID>_<slug>/에 저장하고,
요약 문서는 docs/track6/experiments/에 작성하며,
postprocessing_experiment_matrix.md도 업데이트한다.
```

## 8. 다음 실험 ID 제안

| ID | 대상 | 내용 |
|---|---|---|
| `PP-SVC7` | Warm | `PP-SVC3` vs `service_primary` 조건부 라우팅 및 0604 동시 검증 |
| `PP-WHUBER11` | Warm | PP-WHUBER10 원인 보정 + MAPE guard + 과대예측 전용 cap |
| `PP-QR4` | Cold | PP-QR3 qwidth+pred_gap 후보 반복 split/artist holdout 재검증 |
| `PP-H28` | Cold | 검색 provider agreement 기반 제한 보정 OOF 검증 |
| `PP-COLD-ARTIFACT1` | Cold | qwidth correction map과 LightGBM Quantile artifact 운영 고정 실험 |

## 9. 현재 결론

- Warm은 이미 실험 기준 성능이 높고, 추가 개선은 비율/조건부 라우팅/약한 보정의 안정성 검증이 핵심.
- Warm Huber 계열 보정은 성능을 올릴 수 있지만 MAPE 악화가 동반되기 쉬워 목적별 후보로 분리해야 함.
- Cold는 아직 운영 자동 적용 수준이 아니며, qwidth 기반 보정과 검색/외부 데이터 제한 적용이 가장 현실적인 개선 경로.
- Claude Code는 새 모델을 무작정 추가하기보다, 기존에 개선 신호가 있었던 후보를 OOF/반복 split/0604 기준으로 재검증하는 작업부터 시작하는 것이 효율적.
