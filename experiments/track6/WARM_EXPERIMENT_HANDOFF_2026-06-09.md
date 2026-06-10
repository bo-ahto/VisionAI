# Warm 가격 예측 실험 핸드오프

작성일: 2026-06-09

## 현재 목표

기존 Warm 가격 예측 모델의 운영 성능을 개선한다.

주요 판단 기준은 아래와 같다.

- 기본 데이터셋 기준으로 비교한다. 제출용 고신뢰 100건 실험은 제외한다.
- 기존 Warm validation OOF 519건 + fixed test 607건을 사용한다.
- fixed test 성능만 보지 않고 repeated validation 안정성을 같이 본다.
- 핵심 지표는 MAPE, p95 APE, repeated MAPE win rate, replacement score다.

## 현재 운영 1순위

현재 운영 후보 1순위는 `PP148 row-level tail router`다.

정확한 후보명:

```text
reference_pp148_operational
```

PP148은 PP126을 기본 예측으로 유지하고, 일부 tail-risk row에만 direct LightGBM meta 후보를 제한적으로 적용하는 방식이다.

주요 수치:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | replacement score |
|---|---:|---:|---:|---:|
| PP126 운영 기준 | 0.270114 | 0.807490 | 0.919231 | -0.017219 |
| PP148 운영 후보 | 0.270140 | 0.807231 | 0.925962 | -0.017463 |

해석:

- PP126보다 MAPE는 `+0.000026` 나빠진다.
- 대신 p95는 `-0.000259` 좋아진다.
- repeated MAPE win rate와 replacement score가 좋아진다.
- 따라서 순수 MAPE만 보면 PP126, 운영 안정성과 tail 방어를 같이 보면 PP148이 현재 우세하다.

## p95 전용 후보

p95 방어 전용 후보는 `reference_pp148_p95`다.

주요 수치:

| 후보 | MAPE | p95 APE | 반복 MAPE win rate | replacement score |
|---|---:|---:|---:|---:|
| PP148 p95 후보 | 0.270269 | 0.805949 | 0.598397 | -0.004079 |

해석:

- p95는 PP126 대비 약 `-0.001541` 개선된다.
- 하지만 MAPE 반복 안정성이 낮아서 운영 기본값으로 쓰면 안 된다.
- tail-risk 전용 모드 또는 별도 안정성 옵션으로만 고려한다.

## 최근 실험 흐름

### PP127~134: learned stack correction

위치:

```text
scripts/track6/run_pp_opt127_134_warm_learned_stack_correction.py
experiments/track6/PP-OPT127_134_warm_learned_stack_correction/
```

결론:

- fixed test MAPE는 `0.270033`까지 내려갔다.
- p95는 `0.807490`으로 PP126과 동일했다.
- 그러나 repeated stability가 PP126보다 약했다.
- 운영 교체 후보는 아니고 challenger로 유지한다.

### PP135~138: p95-aware correction

위치:

```text
scripts/track6/run_pp_opt135_138_warm_p95_aware_correction.py
experiments/track6/PP-OPT135_138_warm_p95_aware_correction/
```

결론:

- hard guard, tail-harm rollback, row-level cap으로는 PP127 계열의 p95 손상을 충분히 해결하지 못했다.
- 최종 선택은 PP126으로 fallback됐다.

### PP139~142: direct meta stack

위치:

```text
scripts/track6/run_pp_opt139_142_warm_direct_meta_stack.py
experiments/track6/PP-OPT139_142_warm_direct_meta_stack/
```

결론:

- direct LightGBM meta-stack은 p95를 낮추는 힘이 있었다.
- 하지만 전역 적용하면 MAPE가 나빠진다.
- p95 후보는 MAPE `0.270699`, p95 `0.805930`.
- 운영 후보는 아님. tail-risk 보조 후보로 의미가 있다.

### PP143~148: row-level tail router

위치:

```text
scripts/track6/run_pp_opt143_148_warm_row_level_tail_router.py
experiments/track6/PP-OPT143_148_warm_row_level_tail_router/
```

결론:

- 현재 운영 1순위가 된 실험이다.
- PP126 기본 예측을 유지하고, 일부 row에만 direct meta p95 후보를 제한 적용한다.
- 운영 후보 PP148:
  - MAPE `0.270140`
  - p95 `0.807231`
  - replacement score `-0.017463`
- PP126보다 MAPE는 아주 조금 나쁘지만, p95와 반복 안정성은 좋아졌다.

### PP149~154: Huber adoption stabilization

위치:

```text
scripts/track6/run_pp_opt149_154_warm_huber_adoption_stabilization.py
experiments/track6/PP-OPT149_154_warm_huber_adoption_stabilization/
```

결론:

- direct LightGBM Huber 보정은 fixed test MAPE를 크게 낮추는 신호가 있다.
- 최고 fixed MAPE 후보는 대략 MAPE `0.269795`, p95 `0.806813`.
- 하지만 repeated MAPE win rate가 `0.86`대까지 떨어진다.
- 운영 후보로는 불안정하다.
- 최종 선택은 PP148 fallback.

### PP155~160: strict Huber gate

위치:

```text
scripts/track6/run_pp_opt155_160_warm_strict_huber_gate.py
experiments/track6/PP-OPT155_160_warm_strict_huber_gate/
```

결론:

- PP149의 낮은 MAPE 신호를 더 엄격한 gate로 안정화하려고 했다.
- 최종 운영 선택은 여전히 PP148이다.
- 의미 있는 후보는 PP157 segment quantile strict Huber gate다.

PP157 주요 후보:

| 후보 계열 | MAPE | p95 APE | 반복 MAPE win rate | replacement score |
|---|---:|---:|---:|---:|
| PP157 price_qwidth segment | 0.269983 | 0.806851 | 0.886538 | -0.016042 |

해석:

- PP157은 MAPE/p95를 동시에 낮추지만 반복 안정성이 PP148보다 부족하다.
- PP149보다 보수적으로 안정화됐지만, 운영 기준에는 아직 부족하다.

## 현재 판단

운영 모델 후보:

```text
1순위: PP148 row-level tail router
2순위: PP126 operational
보류: PP157 segment quantile strict Huber gate
보류: PP149 direct LightGBM Huber small-cap 후보
```

정리하면:

- 운영 안정성 기준: PP148이 현재 최고다.
- 순수 fixed MAPE 개선 가능성: PP149/PP157 쪽에 있다.
- 하지만 PP149/PP157은 repeated validation에서 적용 row 선택이 아직 불안정하다.

## 다음에 이어서 할 작업

다음 실험은 PP157을 더 세게 쪼개는 것보다, PP157이 실패하는 row를 분석해서 적용 제외 조건을 찾는 방향이 맞다.

추천 다음 단계:

1. PP157 후보 중 `price_qwidth segment` 계열 상위 후보를 고정한다.
2. 해당 후보가 PP148보다 나빠지는 row를 validation OOF에서 라벨링한다.
3. 나빠지는 row의 공통 특성을 분석한다.
   - 가격대
   - quantile width
   - confidence tier
   - artist/sample count
   - 예측 후보 간 gap
   - meta quantile width
   - tail harm probability
4. 그 row를 제외하는 negative gate를 학습한다.
5. `PP148 기본값 + PP157 적용 + negative gate rollback` 구조로 새 실험을 만든다.

추천 실험명:

```text
PP-OPT161~166 Warm PP157 negative gate rollback
```

예상 구조:

```text
기준 예측 = PP148 운영 예측

PP157 보정 후보 = direct LightGBM Huber small-cap / segment quantile gate

적용 점수 =
  PP157 gain probability
  * (1 - PP157 harm probability)
  * segment allow gate
  * negative rollback gate

최종 로그가격 =
  PP148 로그가격
  + clip((PP157 로그가격 - PP148 로그가격) * 적용 점수 * 보정강도, row별 cap)
```

## 재시작 후 바로 확인할 파일

가장 먼저 아래 파일을 열면 된다.

```text
experiments/track6/PP-OPT155_160_warm_strict_huber_gate/reports/strict_huber_gate_result.html
experiments/track6/PP-OPT155_160_warm_strict_huber_gate/outputs/selected_stability_candidate_aggregate.csv
experiments/track6/PP-OPT155_160_warm_strict_huber_gate/artifacts/strict_huber_gate_signal_detail.csv
```

다음 실험 작성 시 참고할 스크립트:

```text
scripts/track6/run_pp_opt155_160_warm_strict_huber_gate.py
scripts/track6/run_pp_opt149_154_warm_huber_adoption_stabilization.py
scripts/track6/run_pp_opt143_148_warm_row_level_tail_router.py
```

## 재시작 후 첫 명령 후보

핵심 지표를 다시 확인하려면:

```bash
python3 - <<'PY'
import pandas as pd
p='experiments/track6/PP-OPT155_160_warm_strict_huber_gate/outputs/selected_stability_candidate_aggregate.csv'
df=pd.read_csv(p)
cols=['candidate','candidate_label','fixed_test_MAPE','fixed_test_p95_APE','avg_pp64_MAPE_win_rate','avg_pp64_p95_win_rate','replacement_score']
print(df.sort_values('replacement_score').head(20)[cols].to_string(index=False))
PY
```

다음 실험의 시작점은 PP157 best MAPE 후보와 PP148 reference의 row별 오차 차이를 분석하는 것이다.
