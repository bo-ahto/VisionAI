# Warm Huber HCOEF25 이후 최고 성능 탐색 /goal 프롬프트

이 문서는 Codex의 `/goal` 기능으로 Warm Huber 계열 성능 개선 실험을 계속 이어가기 위한 붙여넣기용 프롬프트다.

- 사용 방식: `/goal` 명령어 뒤에 아래 **붙여넣기용 프롬프트** 전체를 붙여 넣음.
- 기준: `hcoef_stable`을 현재 1순위 기준 후보로 두고, `current_70_30`을 최소 비교 기준으로 둠.
- 목표: fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 큰 오차 방어까지 통과하는 운영 후보를 찾음.
- 후보 관리: 운영 기본 후보, MAPE 특화 후보, p95 방어 후보, 연구 후보를 분리함.

## 1. 기준 후보

| 구분 | 후보 | fixed test | 0604 stress test | 역할 |
| --- | --- | --- | --- | --- |
| 최소 비교 기준 | `current_70_30` | MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`, RMSE_log `0.3996` | MdAPE `0.2779`, MAPE `0.3774`, p95_APE `0.9871` | 새 실험이 최소한 넘어야 할 서비스 설명 가능 기준 |
| 현재 1순위 기준 | `hcoef2_size_reliability_cap005_s050` / `hcoef_stable` | MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988` | MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835` | 새 운영 후보가 넘어야 할 기준 |
| HCOEF24 목적별 후보 | `hcoef24_default_risk_basis_k8_cap0p05_s0p75` | MdAPE `0.1383`, MAPE `0.2729`, p95_APE `0.8079`, RMSE_log `0.3993` | MdAPE `0.2734`, MAPE `0.3736`, p95_APE `0.9835` | MAPE 특화 연구 후보, p95 guard 미통과 |

## 2. 기준을 이렇게 잡는 이유

- `current_70_30`
  - 유사 작품 기반 가격 피처 70%와 오차 안정화 후보 30%를 결합한 기준.
  - 설명 가능성이 높고 서비스 v0.1 기준으로 이해하기 쉬움.
  - 새 후보가 이 기준도 넘지 못하면 실험 의미가 낮음.

- `hcoef_stable`
  - `current_70_30` 위에 작은 Huber 잔차 보정을 더한 현재 Warm 1순위 후보.
  - row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률이 강하게 확인된 후보.
  - 새 운영 후보는 이 후보보다 안정적으로 좋아야 함.

- `hcoef24_default_risk_basis_k8_cap0p05_s0p75`
  - HCOEF23에서 확인한 위험 구간을 반영해 기준가 이동을 줄인 후보.
  - fixed test MdAPE/MAPE는 소폭 좋아졌지만 p95_APE가 `0.8064`에서 `0.8079`로 악화됨.
  - 운영 기본 후보가 아니라 다음 실험에서 참고할 MAPE 특화 신호로만 사용.

## 3. 성능 판단 기준

| 우선순위 | 기준 | 통과 기준 |
| --- | --- | --- |
| 1 | row OOF와 artist OOF 반복 검증 | MdAPE/MAPE/p95 동시 개선 확률 `>= 0.90` |
| 2 | fixed test | `hcoef_stable` 대비 MdAPE/MAPE/p95 동등 또는 개선 |
| 3 | 큰 오차 방어 | fixed test p95_APE `0.8064` 초과 시 운영 기본 후보 미채택 |
| 4 | 0604 stress test | p95_APE `0.9835` 초과 시 운영 승격 보류 |
| 5 | 해석 가능성 | Huber 계수, 기준가, 보정 강도, cap 의미가 설명 가능해야 함 |

## 4. 후보 분류 기준

| 후보 유형 | 의미 | 판단 |
| --- | --- | --- |
| 운영 기본 후보 | MdAPE/MAPE/p95가 반복 검증과 fixed test에서 모두 안정적으로 개선 | v0.1 교체 후보 |
| MAPE 특화 후보 | MAPE는 개선되지만 MdAPE 또는 p95 위험이 남음 | 평균오차 개선 연구 후보 |
| p95 방어 후보 | 큰 오차는 줄지만 MdAPE/MAPE 개선폭이 작음 | 위험 구간 보조 정책 후보 |
| 신뢰도/범위 정책 후보 | 점 예측은 크게 바꾸지 않고 가격 범위와 신뢰도 표시를 개선 | 서비스 표시 정책 후보 |
| 연구 후보 | 일부 데이터에서만 좋거나 반복 검증이 약함 | 문서화만 하고 운영 반영 보류 |

## 5. 다음 실험 축

| 실험 축 | 목적 | 핵심 기준 |
| --- | --- | --- |
| HCOEF25 보수적 계수 조정 | HCOEF24의 좋은 MAPE 신호를 더 작은 cap과 risk guard로 안정화 | p95 `0.8064` 방어 우선 |
| HCOEF26 기준가 생성 재설계 | 유사 작품 기반 가격 피처를 더 안정적으로 생성 | 작가/크기/재료/표본 수/fallback별 비교 |
| HCOEF27 작가 메타 피처 계수 검증 | 생년, 활동성, 갤러리/전시 정보가 Warm에서도 추가 설명력을 주는지 확인 | 기존 artist_key 효과와 중복/과적합 여부 확인 |
| HCOEF28 목적별 라우팅 | 기본값은 `hcoef_stable`로 두고 특정 구간에만 다른 후보 제한 적용 | validation OOF에서만 경계 정의 |
| HCOEF29 신뢰도/가격 범위 정책 | 점 예측보다 예측 범위와 신뢰도 표시 고도화 | qwidth, price_range_ratio, tier별 실제 오차 검증 |

## 6. 붙여넣기용 프롬프트

```text
Warm Huber 계열 가격 예측 모델에서 HCOEF25 이후 최고 성능 탐색 실험을 계속 진행해줘.

목표는 fixed test 한 번의 점수를 좋게 만드는 것이 아니라, 반복 검증과 운영 안정성까지 통과하는 최고 성능 후보를 찾는 것이다.

먼저 아래 문서를 읽고 현재 후보, 이미 완료한 실험, 반복하면 안 되는 방식, 남은 실험 축을 파악해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/pp_hcoef23_warm_huber_price_basis_coefficient_refinement_summary.md
- docs/track6/experiments/pp_hcoef24_warm_huber_price_basis_coefficient_refinement_summary.md
- experiments/track6/PP-HCOEF20_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF21_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF22_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF23_warm_huber_price_basis_coefficient_refinement/reports/result_report.md
- experiments/track6/PP-HCOEF24_warm_huber_price_basis_coefficient_refinement/reports/result_report.md

현재 1순위 기준 후보는 `hcoef2_size_reliability_cap005_s050` 또는 `hcoef_stable`이다.

- fixed test: MdAPE 0.1388, MAPE 0.2730, p95_APE 0.8064, RMSE_log 0.3988
- 0604 stress test: MdAPE 0.2731, MAPE 0.3744, p95_APE 0.9835
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 개선 확률이 강하게 확인된 현재 Warm 기준 후보

최소 비교 기준은 `current_70_30`이다.

- fixed test: MdAPE 0.1405, MAPE 0.2748, p95_APE 0.8331, RMSE_log 0.3996
- 0604 stress test: MdAPE 0.2779, MAPE 0.3774, p95_APE 0.9871

HCOEF24의 상위 목적별 후보는 `hcoef24_default_risk_basis_k8_cap0p05_s0p75`이다.

- fixed test: MdAPE 0.1383, MAPE 0.2729, p95_APE 0.8079, RMSE_log 0.3993
- 0604 stress test: MdAPE 0.2734, MAPE 0.3736, p95_APE 0.9835
- 판단: MAPE 특화 후보. p95가 `hcoef_stable`보다 악화되어 운영 기본 후보로 채택하지 않는다.

후보 판단 기준은 아래처럼 고정해줘.

1. 새 후보는 최소한 `current_70_30`보다 좋아야 한다.
2. 운영 기본 후보가 되려면 `hcoef_stable` 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 한다.
3. row OOF와 artist OOF의 `all3_improve_prob >= 0.90`이면 개선 후보로 본다.
4. row OOF와 artist OOF의 `all3_improve_prob >= 0.95`이고 fixed test와 0604에서 악화가 없으면 강한 후보로 본다.
5. fixed test p95_APE가 0.8064보다 악화되면 운영 기본 후보로 채택하지 않는다.
6. 0604 p95_APE가 0.9835보다 악화되면 운영 후보 승격을 보류한다.
7. fixed test 또는 0604만 좋아지는 후보는 연구 후보로만 남긴다.
8. test residual이나 0604 residual을 보고 새 보정값, 경계값, 가중치를 만들지 않는다.
9. 실제 가격 구간은 원인 진단용으로만 쓰고 보정 기준으로 쓰지 않는다.

성능 판단 우선순위는 아래처럼 둬.

1. row OOF와 artist OOF 반복 검증의 MdAPE/MAPE/p95 안정성
2. fixed test MdAPE/MAPE/p95
3. fixed test p95_APE 방어
4. 0604 stress test 악화 여부
5. Huber 계수 또는 보정 정책의 해석 가능성

후보 유형은 반드시 분리해줘.

- 운영 기본 후보: MdAPE/MAPE/p95가 모두 안정적으로 개선되는 후보.
- MAPE 특화 후보: MAPE는 개선되지만 MdAPE 또는 p95 위험이 남는 후보.
- p95 방어 후보: 큰 오차를 줄이지만 중앙 오차 개선폭은 작은 후보.
- 신뢰도/범위 정책 후보: 점 예측은 크게 바꾸지 않고 예측 범위와 신뢰도 표시를 개선하는 후보.
- 연구 후보: 일부 데이터에서는 좋지만 반복 OOF 또는 fixed test 안정성이 부족한 후보.

HCOEF23~HCOEF24까지의 결론은 아래처럼 반영해줘.

- HCOEF23은 새 보정값을 만들지 않고 현재 HCOEF 안정 후보의 남은 오차 원인을 validation/OOF 기준으로 분해했다.
- HCOEF23의 우선 위험 구간은 `qwidth_extreme`, `gap_020_plus`, `svc_group_n_band=n_10_19`, `svc_group_level=artist`, `pred_spread_band=spread_extreme`이다.
- HCOEF23의 잔차 크기 계수 감사에서는 `quantile_width`, `stable_ppv8_gap_abs`, `gap_020_plus`가 오차 위험 증가 방향으로 확인됐다.
- HCOEF24는 위 위험 구간에서 유사 작품 기반 기준가 이동을 줄인 risk-shrunk basis 후보와 residual Huber 후보를 검증했다.
- HCOEF24 상위 후보는 fixed test MdAPE/MAPE를 소폭 개선했지만 p95 guard와 bootstrap all3 gate를 통과하지 못했다.
- HCOEF24 direct Huber capped 후보는 validation/0604 개선 신호가 있었지만 fixed test p95가 악화되어 운영 기본 후보가 아니다.
- 따라서 HCOEF25 이후에는 HCOEF24의 좋은 MAPE 신호를 그대로 키우는 것이 아니라, 더 작은 cap, 더 보수적인 strength, p95-aware guard, low-risk 구간 제한 적용으로 안정화해야 한다.
- 현재 운영 기본 후보는 계속 `hcoef_stable`로 둔다.

다음 실험은 아래 순서로 계획하고 실행해줘.

1. HCOEF25: 보수적 Huber 계수 조정과 p95-aware cap
   - HCOEF24 direct Huber와 risk-shrunk basis의 좋은 MAPE 신호를 참고하되, 더 작은 cap으로 다시 검증한다.
   - cap 후보는 0.01, 0.015, 0.02, 0.03을 기본으로 둔다.
   - strength 후보는 0.10, 0.25, 0.50을 기본으로 둔다.
   - `qwidth_extreme`, `gap_020_plus`, `spread_extreme` 구간에서는 보정 강도를 줄이거나 `hcoef_stable`로 fallback한다.
   - Huber 계수는 표준화 계수와 원 피처 의미를 함께 저장해서 왜 가격을 올리거나 낮췄는지 설명 가능해야 한다.

2. HCOEF26: 기준가 생성 방식 재설계
   - 유사 작품 기반 가격 피처를 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 단위로 다시 비교한다.
   - 최소 표본 수, fallback 순서, 표본 수 기반 shrinkage, IQR 완화 기준을 validation 기준으로만 정한다.
   - 기준가가 부족한 경우 작가 전체 기준, medium/support bucket, 전체 Warm 기준 순서로 fallback하는 후보를 비교한다.
   - 기준가 자체를 크게 바꾸는 후보와 `hcoef_stable` 위에 작은 잔차 보정만 더하는 후보를 분리한다.

3. HCOEF27: Warm 작가 메타 피처 계수 검증
   - Warm에서도 생년, 작가 활동성, 갤러리/전시 정보, 검색/인지도 피처가 추가 설명력을 주는지 확인한다.
   - 기존 `artist_key`가 이미 작가별 기준선을 강하게 학습하므로, 작가 메타는 가격을 직접 크게 움직이는 피처가 아니라 잔차 보정 또는 신뢰도 보정 피처로 먼저 검증한다.
   - artist-level split에서 성능이 유지되는지 반드시 확인한다.
   - 작가 메타가 특정 작가 memorization으로 작동하면 운영 후보로 채택하지 않는다.

4. HCOEF28: 목적별 후보 라우팅
   - 기본값은 `hcoef_stable`로 둔다.
   - validation OOF에서 명확히 좋아지는 구간에만 MAPE 특화 후보 또는 p95 방어 후보를 제한 적용한다.
   - 라우팅 기준은 운영 예측 시점에 알 수 있는 피처만 사용한다.
   - fixed test와 0604에서 MdAPE/MAPE/p95를 모두 비교하고, p95가 악화되면 운영 기본 후보로 채택하지 않는다.

5. HCOEF29: 가격 범위와 신뢰도 정책
   - 점 예측을 크게 바꾸지 않고 q10/q50/q90, quantile_width, price_range_ratio, confidence tier를 검증한다.
   - validation에서 경계를 정의하고 fixed test와 0604에서 실제 포함률, 큰 오차율, tier별 MdAPE/MAPE/p95를 확인한다.
   - 산출물은 서비스 화면에서 신뢰도와 예측 범위를 표시하는 기준으로 검토 가능해야 한다.

필요하면 추가 실험을 제안하되, 이미 한 실험과 무엇이 다른지 먼저 명시해줘.

반복하지 말아야 할 방식은 아래와 같다.

1. fixed test만 좋은 후보를 운영 후보로 승격하지 않는다.
2. 0604만 좋은 후보를 운영 후보로 승격하지 않는다.
3. test 또는 0604 residual을 보고 보정 경계와 가중치를 새로 만들지 않는다.
4. HCOEF20~HCOEF24에서 이미 검증한 같은 피처, 같은 cap, 같은 strength 조합을 반복하지 않는다.
5. quantile width나 후보 간 gap으로 점 예측을 크게 움직이는 방식은 p95 guard 없이 반복하지 않는다.
6. 작가 메타 피처는 artist-level split 검증 없이 운영 후보로 채택하지 않는다.

실험 관리 규칙은 아래처럼 지켜줘.

- 다음 실험은 PP-HCOEF25부터 시작한다.
- 실험 폴더는 `experiments/track6/PP-HCOEF##_짧은_설명` 형식으로 만든다.
- 실행 스크립트는 `scripts/track6/run_pp_hcoef##_짧은_설명.py`로 남긴다.
- 각 실험에는 최소한 아래 파일을 남긴다.
  - artifacts/experiment_config.json
  - outputs/metrics.csv
  - outputs/candidate_predictions.csv
  - outputs/feature_coefficients.csv 또는 outputs/policy_map.csv
  - outputs/residual_analysis.csv
  - outputs/bootstrap_or_repeated_split_summary.csv 또는 outputs/repeated_validation_summary.csv
  - reports/result_report.md
  - reports/result_report.html

실험 후 아래 문서를 업데이트해줘.

- docs/track6/experiments/postprocessing_experiment_matrix.md
- docs/track6/experiments/pp_hcoef_warm_huber_price_basis_coefficient_interpretation_report.md
- docs/track6/experiments/warm_huber_hcoef25_max_performance_goal_prompt.md
- 필요하면 최신 continuation goal prompt 문서

최종 응답에는 아래 내용을 정리해줘.

- 실행한 실험 ID와 폴더
- 새 후보명과 후보 유형
- `current_70_30` 대비 개선폭
- `hcoef_stable` 대비 개선폭
- row OOF와 artist OOF 반복 검증 결과
- fixed test와 0604 stress test 결과
- Huber 계수 또는 보정 정책 해석
- 운영 후보 / 목적별 후보 / 보류 후보 판단
- 다음 실험에서 반복하지 말아야 할 점
```

## 7. 짧은 버전

```text
Warm Huber HCOEF25 이후 실험을 이어서 진행해줘. 기준 후보는 `hcoef_stable`이고, 최소 비교 기준은 `current_70_30`이다. 운영 후보는 row OOF/artist OOF/fixed test에서 MdAPE/MAPE/p95가 모두 안정적으로 개선되어야 하며, fixed test p95 `0.8064`, 0604 p95 `0.9835`를 넘기면 운영 승격을 보류한다. test/0604 residual로 보정값을 만들지 말고, HCOEF23~24에서 확인된 `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme`, HCOEF24 MAPE 특화 신호를 기준으로 더 작은 cap, 보수적 strength, p95-aware guard, 기준가 생성 재설계, 작가 메타 피처 계수 검증, 목적별 라우팅, 신뢰도/범위 정책 순서로 실험을 계획하고 실행해줘. 다음 실험은 PP-HCOEF25부터 시작하고, 실험 폴더/스크립트/metrics/predictions/coefficients 또는 policy_map/residual_analysis/반복 검증 요약/result_report.md/html을 모두 남긴 뒤 관련 문서를 업데이트해줘.
```
