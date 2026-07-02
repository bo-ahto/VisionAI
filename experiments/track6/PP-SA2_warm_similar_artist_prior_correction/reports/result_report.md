# PP-SA2 Warm 유사 작가 기준가 보정 검증

- 작성일: 2026-06-11 16:35
- 기준 모델: Warm 운영 1순위 후보 `PP258 operational`
- 목적: 유사 작가+작품 기준가를 최종 예측값 대체가 아니라 작은 로그 보정값으로 사용할 수 있는지 검증한다.
- 선택 방식: validation_oof에서 보정식과 강도를 고르고 fixed test에서 한 번 평가한다.

## 1. 보정식

```text
후보_보정예측로그가격
  = 기존_Warm_운영예측로그가격
  + strength * clip(유사작가_기준로그가격 - 비교기준로그가격, -cap, +cap)
```

- `strength`: 유사 작가 기준을 얼마나 반영할지 정하는 보정 강도
- `cap`: 한 row에서 움직일 수 있는 최대 로그 보정 폭
- `gate`: 모든 row가 아니라 특정 조건 row에만 보정을 적용하는 규칙

## 2. Validation 선택 후보

- 선택 후보: `sa2__similar_minus_base__gate=low_svc_and_strict__s=0.2__cap=0.05`
- source: `similar_minus_base`
- gate: `low_svc_and_strict`
- strength: 0.2000
- cap: 0.0500
- validation MdAPE/MAPE/p95: 0.122656 / 0.205408 / 0.625114
- validation baseline MdAPE/MAPE/p95: 0.122707 / 0.205629 / 0.637888

## 3. 보수적 서비스 후보

- 선택 후보: `sa2__similar_minus_same_artist__gate=strict_similar_artwork__s=0.08__cap=0.01`
- source: `similar_minus_same_artist`
- gate: `strict_similar_artwork`
- strength: 0.0800
- cap: 0.0100
- validation MdAPE/MAPE/p95: 0.122219 / 0.205617 / 0.636710
- 선택 기준: 유사 작가 기준과 같은 작가 기준의 차이만 사용하고, 유사 작가+작품 조건이 중간 이상인 row에만 평균 0.001 로그 이하로 보정

## 4. Fixed Test 결과

| 후보 | n | MdAPE | MAPE | p95_APE | RMSE_log | 평균 보정폭 |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 607 | 0.140976 | 0.269888 | 0.807325 | 0.397454 | 0.000000 |
| selected correction | 607 | 0.141161 | 0.269503 | 0.808285 | 0.396931 | 0.004162 |
| conservative service candidate | 607 | 0.140976 | 0.269835 | 0.807218 | 0.397412 | 0.000467 |

## 5. 해석
- validation에서 선택한 유사 작가 보정이 fixed test에서는 baseline을 안정적으로 넘지 못했다.
- 공격적 선택 후보는 최종 예측 보정으로 채택하지 않는다.
- 보수적 서비스 후보는 MdAPE를 유지하면서 MAPE, p95, RMSE_log를 소폭 개선했다.
- 다만 개선 폭이 작으므로 운영 채택보다는 다음 반복 검증 후보로 둔다.

## 6. Validation 상위 후보

| experiment_id | candidate | source | gate | strength | cap | split | gated_rows | mean_abs_correction_log | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_confidence__s=0.2__cap=0.05 | similar_minus_same_artist | low_confidence | 0.200000 | 0.050000 | validation | 172 | 0.003187 | 519 | 0.322876 | 0.120855 | 0.205220 | 0.638239 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.2__cap=0.05 | similar_minus_same_artist | all | 0.200000 | 0.050000 | validation | 519 | 0.009545 | 519 | 0.322457 | 0.121193 | 0.205328 | 0.625723 | 0.780347 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_confidence__s=0.15__cap=0.05 | similar_minus_same_artist | low_confidence | 0.150000 | 0.050000 | validation | 172 | 0.002390 | 519 | 0.322982 | 0.121317 | 0.205316 | 0.638152 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__blend15_minus_base__gate=low_svc_and_strict__s=0.2__cap=0.05 | blend15_minus_base | low_svc_and_strict | 0.200000 | 0.050000 | validation | 229 | 0.004073 | 519 | 0.323285 | 0.121322 | 0.205054 | 0.644753 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__blend15_minus_base__gate=low_svc_and_strict__s=0.15__cap=0.05 | blend15_minus_base | low_svc_and_strict | 0.150000 | 0.050000 | validation | 229 | 0.003055 | 519 | 0.323287 | 0.121322 | 0.205182 | 0.647226 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_svc_or_low_confidence__s=0.2__cap=0.05 | similar_minus_same_artist | low_svc_or_low_confidence | 0.200000 | 0.050000 | validation | 438 | 0.008031 | 519 | 0.322679 | 0.121537 | 0.205449 | 0.625723 | 0.780347 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_svc__s=0.2__cap=0.05 | similar_minus_same_artist | low_svc | 0.200000 | 0.050000 | validation | 421 | 0.007706 | 519 | 0.322712 | 0.121537 | 0.205574 | 0.625723 | 0.780347 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_confidence__s=0.2__cap=0.03 | similar_minus_same_artist | low_confidence | 0.200000 | 0.030000 | validation | 172 | 0.001968 | 519 | 0.323046 | 0.121857 | 0.205383 | 0.638099 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.2__cap=0.03 | similar_minus_same_artist | all | 0.200000 | 0.030000 | validation | 519 | 0.005847 | 519 | 0.322773 | 0.121857 | 0.205388 | 0.629287 | 0.782274 | 0.911368 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_svc__s=0.2__cap=0.03 | similar_minus_same_artist | low_svc | 0.200000 | 0.030000 | validation | 421 | 0.004731 | 519 | 0.322931 | 0.121857 | 0.205561 | 0.629287 | 0.782274 | 0.911368 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_svc_and_strict__s=0.2__cap=0.03 | similar_minus_same_artist | low_svc_and_strict | 0.200000 | 0.030000 | validation | 229 | 0.002568 | 519 | 0.323263 | 0.121857 | 0.205735 | 0.629075 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__blend15_minus_base__gate=low_svc_and_strict__s=0.2__cap=0.03 | blend15_minus_base | low_svc_and_strict | 0.200000 | 0.030000 | validation | 229 | 0.002536 | 519 | 0.323292 | 0.121876 | 0.205238 | 0.646754 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.15__cap=0.005 | similar_minus_same_artist | all | 0.150000 | 0.005000 | validation | 519 | 0.000745 | 519 | 0.323257 | 0.122163 | 0.205574 | 0.636810 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=medium_or_strict_similar_artwork__s=0.15__cap=0.005 | similar_minus_same_artist | medium_or_strict_similar_artwork | 0.150000 | 0.005000 | validation | 368 | 0.000529 | 519 | 0.323291 | 0.122163 | 0.205606 | 0.636784 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.2__cap=0.02 | similar_minus_same_artist | all | 0.200000 | 0.020000 | validation | 519 | 0.003925 | 519 | 0.322944 | 0.122170 | 0.205428 | 0.632148 | 0.782274 | 0.911368 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.08__cap=0.05 | similar_minus_same_artist | all | 0.080000 | 0.050000 | validation | 519 | 0.003818 | 519 | 0.322950 | 0.122170 | 0.205440 | 0.632148 | 0.782274 | 0.911368 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_svc__s=0.2__cap=0.02 | similar_minus_same_artist | low_svc | 0.200000 | 0.020000 | validation | 421 | 0.003179 | 519 | 0.323052 | 0.122170 | 0.205560 | 0.632148 | 0.782274 | 0.911368 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=low_svc__s=0.08__cap=0.05 | similar_minus_same_artist | low_svc | 0.080000 | 0.050000 | validation | 421 | 0.003083 | 519 | 0.323059 | 0.122170 | 0.205566 | 0.632148 | 0.782274 | 0.911368 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.15__cap=0.01 | similar_minus_same_artist | all | 0.150000 | 0.010000 | validation | 519 | 0.001484 | 519 | 0.323180 | 0.122176 | 0.205527 | 0.635733 | 0.782274 | 0.909441 |
| PP-SA2 | sa2__similar_minus_same_artist__gate=all__s=0.05__cap=0.03 | similar_minus_same_artist | all | 0.050000 | 0.030000 | validation | 519 | 0.001462 | 519 | 0.323186 | 0.122176 | 0.205540 | 0.635733 | 0.782274 | 0.909441 |
