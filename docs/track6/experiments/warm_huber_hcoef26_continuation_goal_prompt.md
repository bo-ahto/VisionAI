# Warm Huber HCOEF26 이후 /goal 프롬프트

이 문서는 HCOEF25까지 실행한 뒤, Codex의 `/goal` 기능으로 다음 Warm Huber 실험을 이어가기 위한 붙여넣기용 프롬프트다.

## 1. 현재 기준

| 구분 | 후보 | fixed test | 0604 stress | 판단 |
| --- | --- | --- | --- | --- |
| 최소 비교 기준 | `current_70_30` | MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996` | MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871` | 기존 70:30 기준 |
| 현재 유지 기준 | `hcoef_stable` | MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988` | MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835` | Warm 기준 후보 유지 |
| HCOEF25 목적별 후보 | `hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25` | MdAPE `0.1366`, MAPE `0.2727`, p95_APE `0.8080`, RMSE_log `0.3987` | MdAPE `0.2726`, MAPE `0.3743`, p95_APE `0.9835` | MAPE 특화 후보, p95 guard 미통과 |

## 2. HCOEF25까지의 결론

- HCOEF24는 HCOEF23 위험 구간을 기준으로 risk-shrunk basis를 만들었지만 fixed p95 guard를 통과하지 못함.
- HCOEF25는 cap을 `0.01~0.03`까지 낮추고 `lowrisk_only`, `no_extreme`, `conservative`, `soft` guard를 적용했지만 p95가 계속 기준보다 소폭 악화됨.
- HCOEF24~25는 MdAPE/MAPE 개선 신호는 확인했지만 운영 기본 후보를 교체할 만큼 p95를 방어하지 못함.
- 따라서 다음 실험은 단순 cap/strength grid 반복이 아니라, p95 방어를 별도 목적처럼 다루는 구조가 필요함.

## 3. 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 HCOEF26 이후 실험을 계속 진행해줘.

현재 기준 후보는 `hcoef_stable`이다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 stress test: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835

최소 비교 기준은 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

HCOEF25까지의 실행 결과를 반드시 반영해줘.

- HCOEF24는 HCOEF23 위험 구간에서 risk-shrunk basis를 만들었지만 fixed p95 guard를 통과하지 못했다.
- HCOEF25는 더 작은 cap과 conservative/no-extreme guard를 적용했지만 fixed p95가 계속 `hcoef_stable`보다 소폭 악화됐다.
- HCOEF25 상위 목적별 후보는 `hcoef25_resid_huber_strict_conservative_guard_core_a0p001_cap0p01_s0p25`이다.
- 이 후보는 fixed test `0.1366/0.2727/0.8080`, 0604 `0.2726/0.3743/0.9835`로 MdAPE/MAPE는 개선됐지만 p95 guard와 bootstrap all3 gate를 통과하지 못했다.
- 따라서 이 후보는 운영 기본 후보가 아니라 MAPE 특화 연구 후보로만 유지한다.

후보 판단 기준은 아래처럼 유지해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 기본 후보가 되려면 `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
3. fixed test p95_APE가 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
4. 0604 p95_APE가 0.9835보다 악화되면 운영 후보 승격을 보류한다.
5. fixed test 또는 0604만 좋아지는 후보는 연구 후보로만 남긴다.
6. test residual이나 0604 residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.

HCOEF26은 아래 방향으로 설계해줘.

1. p95 hard fallback 실험
   - 기본값은 `hcoef_stable`로 둔다.
   - HCOEF24~25 목적별 후보는 validation OOF에서 p95 위험이 낮은 구간에만 제한 적용한다.
   - `qwidth_extreme`, `gap_020_plus`, `spread_extreme`, `hcoef23_risk_score>=2` 구간은 무조건 `hcoef_stable`로 fallback하는 후보를 포함한다.

2. low-risk MAPE 후보 제한 적용
   - HCOEF25 MAPE 특화 후보를 전체에 적용하지 않는다.
   - `hcoef25_low_risk_flag=1`, 충분한 `svc_group_n`, 낮은 `quantile_width`, 낮은 `pred_spread` 구간에서만 적용하는 후보를 만든다.
   - 적용률, 적용 구간별 MdAPE/MAPE/p95를 반드시 산출한다.

3. p95 방어 후보 분리
   - 점 예측 평균 성능 후보와 p95 방어 후보를 같은 기준으로 섞지 않는다.
   - p95 방어 후보는 MdAPE/MAPE 개선폭이 작아도 큰 오차율을 줄이면 별도 후보로 기록한다.

4. 신뢰도/범위 정책 후보
   - 점 예측 교체가 어려우면 quantile width, price_range_ratio, 표본 수, 후보 간 gap을 이용한 신뢰도/가격 범위 정책을 강화한다.
   - high/medium/low tier별 실제 MdAPE/MAPE/p95와 q10~q90 포함률을 확인한다.

실험 관리 규칙:

- 다음 실험은 PP-HCOEF26부터 시작한다.
- 실험 폴더는 `experiments/track6/PP-HCOEF##_warm_huber_price_basis_coefficient_refinement` 형식으로 만든다.
- 실행 스크립트는 `scripts/track6/run_pp_hcoef##_warm_huber_price_basis_coefficient_refinement.py`로 남긴다.
- `metrics.csv`, `candidate_predictions.csv`, `feature_coefficients.csv` 또는 `policy_map.csv`, `residual_analysis.csv`, `bootstrap_or_repeated_split_summary.csv`, `selected_candidates.csv`, `result_report.md/html`을 남긴다.
- 실험 후 `postprocessing_experiment_matrix.md`와 `pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md`를 업데이트한다.
```
