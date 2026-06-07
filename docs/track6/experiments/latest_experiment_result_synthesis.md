# Track6 최신 실험 결과 기반 정리

- 작성일: 2026-06-04
- 기준 실험:
  - Warm: `PP-V1~PP-V8`, `PP-L10`
  - Cold: `PP-Y1~PP-Y21`, `PP-W4`, `PP-H9`, `PP-QR1~PP-QR3`
  - 최종 통합 감사: `PP-I6`, `PP-I7`
- 목적: 최근 실행 결과를 반영해 현재 채택 후보, 보류 후보, 추가 검증이 필요한 후보를 다시 정리한다.

## 1. 전체 결론

- Warm은 추가 실험을 통해 실제 개선 후보가 나왔다.
- 기존 Warm 대표 후보였던 `PP-V1 fine_blend_mape_guarded`보다 `PP-V6 fine_blend_mape_guarded`가 MdAPE, MAPE, p95_APE 모두 개선됐다.
- Warm 서비스 배포 관점에서는 `PP-V8 compact_blend_mape_guarded`도 의미가 있다. 성능은 대표 후보와 거의 비슷하면서 평균 오차와 큰 오차 방어가 더 좋다.
- Cold는 라우팅을 복잡하게 늘리는 방식보다, `qwidth_bin` 기반의 단순 segment 보정 후보가 더 유망했다.
- Cold의 현재 유망 후보는 `PP-Y18 qwidth_bin_oof_min30_cap0.25` 계열이다. `PP-Y21` 반복 holdout 검증에서 평가 구성 안정성은 추가로 확인됐다. 다만 `PP-Y21`은 기존 예측값을 고정한 검증이므로, 완전한 재학습 split 검증과는 구분해 설명한다.
- `PP-QR2`에서 `PP-Y18` 후보에 Quantile q40/q50 신호를 결합했을 때 test MdAPE `0.4175` 후보가 나왔다. `PP-QR3` OOF/holdout 재검증 결과, 복잡한 Ridge residual meta 후보는 test에서 재현되지 않았고 qwidth+pred_gap 제한 보정 후보만 추가 개선 후보로 유지한다.
- `PP-Y10` 불확실성 라우팅과 `PP-Y20` 3-way 목적별 라우팅은 validation 고정 기준에서 재현성이 약해 현재는 보류한다.

## 2. Warm 결과 정리

### 2.1 기존 후보와 신규 후보 비교

| 구분 | 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---|---:|---:|---:|---:|---|
| 기존 대표 | `PP-V1 fine_blend_mape_guarded` | 0.1621 | 0.3044 | 1.0335 | 0.4220 | 기존 Warm 대표 |
| 기존 방어 | `PP-V2 huber_component_range_clipped` | 0.1680 | 0.2873 | 0.9287 | 0.4102 | 평균/큰 오차 방어 |
| 신규 대표 | `PP-V6 fine_blend_mape_guarded` | 0.1613 | 0.2889 | 0.9314 | 0.4079 | 대표 후보 교체 검토 |
| 신규 방어 | `PP-V7 huber_component_range_clipped` | 0.1712 | 0.2803 | 0.8990 | 0.4053 | MAPE/p95는 좋지만 MdAPE 악화 |
| 배포 단순화 | `PP-V8 compact_blend_mape_guarded` | 0.1632 | 0.2816 | 0.9311 | 0.4028 | 서비스 후보로 유효 |

### 2.2 Warm 해석

- `PP-L10` 후보는 단독으로는 기존 최종 후보를 넘지 못했다.
- 하지만 `PP-V6` fine blend에 넣었을 때 validation에서 가중치를 받았다.
- `PP-V6 mape_guarded` 선택 가중치:
  - `l9_seq`: 0.1
  - `e1_history`: 0.3
  - `k3_similar`: 0.2
  - `l10_meta_external_search_seq`: 0.2
  - `l10_generated_bucket_seq`: 0.2
- 이 결과는 `PP-L10`이 단독 모델 교체용은 아니지만, 기존 후보가 놓치는 구간을 보완하는 component로는 의미가 있음을 보여준다.
- Warm은 작가 이력이 있는 데이터라서 작가 기준선과 작품 크기/재료 조건이 비교적 안정적으로 작동한다.
- 따라서 단일 모델을 계속 바꾸는 것보다, 이미 강한 후보를 조합하고 약한 구간을 보완하는 방식이 효과적이었다.

### 2.3 Warm 현재 추천 후보

| 용도 | 추천 후보 | 이유 |
|---|---|---|
| 대표 점 예측 | `PP-V6 fine_blend_mape_guarded` | MdAPE 0.1613으로 현재 Warm 최고 |
| 평균 오차 최소화 | `PP-V8 compact_blend_mape_guarded` 또는 `PP-V7 huber_component_range_clipped` | MAPE 0.2816 또는 0.2803으로 가장 낮은 축 |
| 큰 오차 방어 | `PP-V7 huber_component_range_clipped` | p95 0.8990으로 가장 낮음 |
| 서비스 배포 단순화 | `PP-V8 compact_blend_mape_guarded` | 성능과 구조 단순성의 균형이 좋음 |

## 3. Cold 결과 정리

### 3.1 기존 기준 후보와 신규 후보 비교

| 구분 | 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 판단 |
|---|---|---:|---:|---:|---:|---|
| 기존 기준 | `PP-Y2 lgbq_search_all_external_interaction` | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 보수적 기준선 |
| MdAPE 최고 | `PP-Y18 external_x_qwidth_oof_min30_cap0.25` | 0.4239 | 1.0003 | 3.3553 | 0.8557 | test MdAPE 최고, p95 개선은 약함 |
| 균형 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 0.8575 | 대표/평균/큰오차 균형 후보 |
| 추가 개선 후보 | `PP-QR2/QR3 segment_y18_qwidth_pred_gap_min30_cap0.15_s0.50` | 0.4175 | 1.0029 | 3.0018 | 0.8586 | test 기준 추가 개선. PP-QR3에서 확인 후보로 유지 |
| MAPE/p95 방어 후보 | `PP-QR2/QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0.50` | 0.4178 | 0.9640 | 2.5377 | 0.8691 | q40 방어 신호 강함. MdAPE/MAPE/p95 균형 후보 |
| 메타 보정 보류 | `PP-QR3 meta_ridge_resid_predonly_a0.1_cap0.15_s1.00` | 0.4345 | 1.0844 | 3.4669 | 0.8705 | holdout 1위였지만 test에서 PP-Y18보다 악화 |
| p95 방어 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | 0.4438 | 1.1083 | 2.8025 | 0.8905 | 큰 오차 방어 전용 |
| 라우팅 보류 | `PP-Y17 validation fixed routing` | 0.4620~0.4763 | 1.0369~1.0786 | 2.9954~3.0322 | 0.8628~0.8905 | 대표 후보 부적합 |
| 3-way 라우팅 보류 | `PP-Y20 purpose routing` | 0.4494~0.4603 | 1.0552~1.0783 | 3.6483~3.8973 | 0.8956~0.8982 | 단일 후보보다 약함 |

### 3.2 Cold 해석

- Cold는 작가 이력이 없는 작품이 많아, Warm처럼 작가 기준선이 강하게 작동하지 않는다.
- 그래서 작품 크기, 재료, 지지체, 작가 메타, 전시/갤러리, 검색 피처를 조합해도 성능 변동이 크다.
- `PP-Y19` bootstrap 결과에서도 작가 단위로 묶어 다시 뽑으면 MdAPE 95% 구간이 `0.3751~0.5252`까지 넓어졌다.
- 즉 Cold는 test 전체 평균 수치 하나만 보고 후보를 확정하면 위험하다.
- 반면 `qwidth_bin`은 모델이 스스로 만든 불확실성 폭을 구간화한 값이다.
- `qwidth_bin_oof_min30_cap0.25` 후보가 좋은 이유는, 불확실성이 큰 구간과 작은 구간의 반복 오차를 단순하게 보정했기 때문이다.
- 복잡한 3-way 라우팅은 validation에서는 좋아 보였지만 test에서는 악화됐다.
- 따라서 Cold는 복잡한 모델 선택 정책보다, 단순하고 설명 가능한 구간 보정이 현재 더 안정적이다.
- `PP-QR1`에서는 CatBoost/LightGBM Quantile q40/q50을 단독으로 쓰는 것보다 기존 `PP-Y18` 후보에 제한적으로 결합하는 방식이 더 유효했다.
- `PP-QR2`의 핵심 신호는 q40 자체가 좋은 최종 모델이라는 뜻이 아니라, `qwidth`와 `기존 예측값 - q40/q50 예측값`의 차이가 반복 오차를 설명하는 보정축이 될 수 있다는 점이다.
- `PP-QR3`에서 validation 내부 row 5-fold와 artist 5-fold를 함께 돌린 결과, 예측값만으로 다시 학습하는 Ridge residual meta는 holdout에서는 좋아 보였지만 test에서는 악화됐다.
- 이 결과는 Cold에서 복잡한 2단계 meta 모델이 validation 구성에 과하게 맞을 위험이 있음을 보여준다.
- 반면 `qwidth`와 `기존 예측값 - q40/q50 예측값` 차이를 제한적으로 쓰는 guard/segment 보정은 test 개선 신호가 유지됐다.
- 따라서 Cold는 현재 “복잡한 메타 모델”보다 “설명 가능한 qwidth+pred_gap 제한 보정”을 추가 후보로 관리하는 것이 더 타당하다.

### 3.3 Cold bootstrap 해석

`PP-Y18 qwidth_bin_oof_min30_cap0.25`는 기존 `PP-Y2` 대비 다음과 같은 안정성 신호가 있었다.

| 기준 | MdAPE 개선 확률 | MAPE 개선 확률 | p95 개선 확률 | 해석 |
|---|---:|---:|---:|---|
| row bootstrap | 0.9938 | 1.0000 | 0.9988 | 개별 샘플 기준으로는 개선 방향이 매우 강함 |
| artist bootstrap | 0.8488 | 0.9988 | 0.9513 | 작가 구성 변동을 고려해도 MAPE/p95 개선 신호가 강함 |

추가 검증 결과:

- `PP-Y21`에서 row/artist holdout을 80회 반복 구성해 확인했다.
- `qwidth_bin_oof_min30_cap0.25`는 artist holdout 기준 MdAPE 개선확률 `0.8625`, MAPE 개선확률 `0.9875`, p95 개선확률 `0.9625`였다.
- 따라서 현재 단계에서는 “Cold 개선 후보”로 올릴 수 있다.
- 단, `PP-Y21`은 모델 재학습이 아니라 기존 예측값을 고정한 평가 구성 안정성 검증이다. 최종 서비스 확정 문서에는 이 제한을 함께 적는다.

### 3.4 Cold 현재 추천 후보

| 용도 | 추천 후보 | 이유 |
|---|---|---|
| 보수적 기준선 | `PP-Y2 lgbq_search_all_external_interaction` | 구조가 단순하고 기존 기준으로 설명하기 쉬움 |
| 대표 개선 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | MdAPE/MAPE/p95 균형이 가장 좋음 |
| 추가 개선 후보 | `PP-QR2/QR3 qwidth+pred_gap 제한 보정 후보` | test에서 MdAPE 0.4175까지 개선. 복잡한 meta 보정보다 설명 가능성과 성능 균형이 좋음 |
| MdAPE 최고 참고 | `PP-Y18 external_x_qwidth_oof_min30_cap0.25` | MdAPE 0.4239로 가장 낮지만 p95 개선은 제한적 |
| 큰 오차 방어 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | p95 2.8025로 가장 낮지만 MAPE/MdAPE 악화 |
| 보류 | `PP-Y17`, `PP-Y20` | validation 고정 기준에서 test 재현성 약함 |

## 4. 최종 후보 정리

| 구분 | 현재 1순위 | 보조 후보 | 비고 |
|---|---|---|---|
| Warm 대표 예측 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | `PP-V6 fine_blend_mape_guarded` | 비교군 통계 후보와 PP-V8 결합으로 MdAPE/MAPE/p95 모두 개선 |
| Warm 방어/배포 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | `PP-V8 compact_blend_mape_guarded` | PP-V8 단독보다 MAPE와 p95도 개선 |
| Cold 기준선 | `PP-Y2 lgbq_search_all_external_interaction` | - | 보수적 기준 |
| Cold 개선 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | `PP-Y18 external_x_qwidth_oof_min30_cap0.25` | `PP-Y21` 평가 구성 안정성 검증 통과, 최종 정책 후보 |
| Cold 추가 검증 후보 | `PP-QR2/QR3 segment_y18_qwidth_pred_gap_min30_cap0.15_s0.50` | `PP-QR2/QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0.50` | test 개선폭은 크고 PP-QR3에서 meta 후보 대비 더 안정적. 최종 교체 전 split 재학습 검증 필요 |
| Cold p95 방어 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | - | 대표 예측이 아니라 큰 오차 방어 목적 |

### 4.1 PP-I6 최신 통합 감사 반영

- 기존 `PP-I5` 최종 통합 실험은 실행됐지만 `PP-V6/V8/WMAPE`, `PP-Y21`, `PP-H27/H22` 등 최신 후보를 포함하지 못했다.
- `PP-I6`에서 최신 후보 지표를 정규화하고 validation 기준 objective별 후보와 서비스 추천 후보를 분리했다.
- Warm은 validation 최저값만 보면 `PP-WMAPE` CatBoost residual 보정 후보가 강하지만, validation-test 차이가 커서 대표 후보로 바로 교체하지 않는다.
- Warm 서비스 대표 후보는 현재 `PP-V6 fine_blend_mape_guarded`를 우선 유지한다. test 기준 MdAPE `0.1613`, MAPE `0.2889`, p95 `0.9314`다.
- Warm 보조 후보는 `PP-V8 compact_blend_mape_guarded`다. test 기준 MdAPE `0.1632`, MAPE `0.2816`, p95 `0.9311`로 구조 단순화와 평균오차 방어에 유리하다.
- Cold는 validation 최저 후보보다 반복 holdout 안정성과 test 균형을 더 중시해 `PP-Y21 qwidth_bin_oof_min30_cap0.25`를 대표 개선 후보로 유지한다. test 기준 MdAPE `0.4247`, MAPE `0.9910`, p95 `3.3053`다.
- Cold `pred_x_qwidth_oof_min30_cap0.35`는 p95 `2.8025`로 큰 오차 방어에는 좋지만, MdAPE/MAPE가 약해 대표 점 예측 후보가 아니라 위험 구간 방어 후보로 둔다.
- `PP-H27` 검색 보정은 MAPE/p95 개선 신호가 있으나 provider agreement 리스크가 있어 점 예측 직접 반영보다 신뢰도 하향/수동 검수 플래그로 우선 사용한다.

### 4.2 PP-I7 모델 구조별 커스텀 보정 후속 검증 반영

- `PP-I7`은 `PP-I6`에서 남긴 질문을 실제로 확인하기 위해 실행했다.
- Warm은 `PP-V6 fine_blend_mape_guarded`를 기준으로 `PP-V8` 단순화 후보와 `PP-WMAPE` CatBoost residual 후보를 test row/artist bootstrap으로 비교했다.
- Warm 결과:
  - `PP-V6 fine_blend_mape_guarded`: test MdAPE `0.1613`, MAPE `0.2889`, p95 `0.9314`
  - `PP-V8 compact_blend_mape_guarded`: test MdAPE `0.1632`, MAPE `0.2816`, p95 `0.9311`
  - `PP-WMAPE CatBoost residual v8`: test MdAPE `0.1670`, MAPE `0.2820`, p95 `0.8836`
- 해석:
  - `PP-WMAPE` residual 후보는 MAPE/p95를 낮추지만 MdAPE가 악화된다.
  - 따라서 Warm 대표 점 예측은 `PP-V6` 유지가 맞고, `PP-V8/PP-WMAPE`는 평균오차 또는 큰 오차 방어 후보로 분리한다.
- Cold는 `PP-H23/H26` 검색 보정을 전체 적용하지 않고 `recommended_action`, `qwidth_bin` 조건으로 제한 적용해 비교했다.
- Cold test 기준 좋은 신호:
  - `news_cap0.2 + qwidth_caution_risk_only`: MdAPE `0.4179`, MAPE `0.9462`, p95 `3.1405`
  - `gallery_museum_cap0.2 + qwidth_caution_risk_only`: MdAPE `0.4240`, MAPE `0.9413`, p95 `3.1390`
  - 기준선 `PP-Y2`: MdAPE `0.4421`, MAPE `1.0484`, p95 `3.3537`
- 단, validation이 선택한 후보는 주로 `exhibition_cap0.2` 계열이고 test 상위 후보는 `news/gallery` 계열이라, test 결과만 보고 바로 최종 채택하면 test 선택 위험이 있다.
- 따라서 Cold 검색 제한 보정은 “강한 개선 신호가 있는 재검증 후보”로 올리고, OOF 또는 다른 split 기준으로 다시 선택 기준을 고정한 뒤 채택 여부를 판단한다.

### 4.3 PP-SVC1 서비스 비교군 통계 피처 검증 반영

- `PP-SVC1`은 서비스 API에서 필요한 비교군 중앙값/범위/N을 모델 피처로도 쓸 수 있는지 확인한 실험이다.
- 현재 Track6 split에는 `estimated_ho`가 없어 호당가 직접값은 만들지 못했고, 이번에는 `ln_price_krw - log(area_cm2)` 형태의 면적 기준 단가를 사용했다.
- 누수 방지를 위해 train 피처는 5-fold OOF 비교군 통계로 만들고, validation/test는 train 데이터만으로 만든 비교군 통계를 조회했다.
- 직접 비교군 중앙값을 예측값으로 쓰는 기준선은 Warm test MdAPE `0.3100`, Cold test MdAPE `0.5223`으로 좋지 않았다.
- 따라서 `PP-SVC1`의 개선은 “비교군 중앙값을 그대로 대체해서 생긴 효과”가 아니라, 모델이 기존 피처와 비교군 통계를 함께 사용하면서 가격 중심선을 보정한 효과로 해석한다.
- Warm Huber 결과:
  - baseline test MdAPE `0.2274`, MAPE `0.4952`, p95 `2.0130`
  - `svc_numeric` test MdAPE `0.1528`, MAPE `0.2956`, p95 `0.9694`
  - `svc_full` test MdAPE `0.1496`, MAPE `0.2965`, p95 `0.9499`
- Warm은 test의 `48.6%`가 작가 전체 비교군, `40.7%`가 작가+재료/지지체+크기 비교군으로 잡혔다.
- 이 결과는 Warm에서 작가 기반 가격 prior가 Huber의 선형 중심선을 크게 보완한다는 신호다.
- Cold 결과:
  - Cold CatBoost baseline test MdAPE `0.4808`, MAPE `1.4852`, p95 `5.9854`
  - Cold CatBoost `svc_numeric` test MdAPE `0.4885`, MAPE `1.1445`, p95 `3.4749`
  - Cold LightGBM baseline test MdAPE `0.4873`, MAPE `1.3920`, p95 `4.4602`
  - Cold LightGBM `svc_numeric` test MdAPE `0.4855`, MAPE `1.1844`, p95 `3.5868`
- Cold는 test의 `86.5%`가 `medium_support_size`, `8.9%`가 `medium_size`, `4.5%`가 global fallback으로 잡혔다.
- 즉 Cold에서는 작가 prior가 아니라 재료/지지체/크기 조건 기반 가격대 prior로 작동한다.
- 현재 판단:
  - Warm `svc_full`은 기존 Warm 대표 후보 `PP-V6`보다 test MdAPE가 낮아 보이므로, 별도 반복 split 또는 bootstrap 안정성 검증 후 대표 후보 편입을 검토한다.
  - Cold는 CatBoost/LightGBM 모두 MAPE와 p95를 줄이는 신호가 있으나 MdAPE 개선이 약하거나 악화되므로 대표 모델 교체보다는 방어 피처/API 표시 근거로 우선 사용한다.

### 4.4 PP-SVC2 Warm 비교군 통계 피처 안정성 검증 반영

- `PP-SVC2`는 `PP-SVC1-W`의 큰 개선폭이 OOF fold seed 우연인지 확인하기 위해 실행했다.
- Warm Huber에 비교군 통계 피처를 넣고 train OOF fold seed 10개로 반복 재학습했다.
- test 기준 seed 안정성:
  - `svc_full`: MdAPE 평균 `0.1532`, 표준편차 `0.0032`, 범위 `0.1476~0.1585`
  - `svc_numeric`: MdAPE 평균 `0.1531`, 표준편차 `0.0029`, 범위 `0.1475~0.1582`
- seed 평균 후보:
  - `svc_numeric_seed_mean`: MdAPE `0.1520`, MAPE `0.2942`, p95 `0.9381`
  - `svc_full_seed_mean`: MdAPE `0.1533`, MAPE `0.2956`, p95 `0.9190`
- 기존 Warm 후보와 비교:
  - `PP-V6 fine_blend_mape_guarded`: MdAPE `0.1613`, MAPE `0.2889`, p95 `0.9314`
  - `PP-V8 compact_blend_mape_guarded`: MdAPE `0.1632`, MAPE `0.2816`, p95 `0.9311`
- bootstrap 결과:
  - `svc_full_seed_mean`은 `PP-V6` 대비 MdAPE 개선확률이 row `0.796`, artist `0.802`였다.
  - `svc_numeric_seed_mean`은 `PP-V6` 대비 MdAPE 개선확률이 row `0.842`, artist `0.842`였다.
  - 반대로 MAPE 개선확률은 `0.264~0.344` 수준이라, 평균오차는 `PP-V6/PP-V8`이 더 유리했다.
- 해석:
  - 비교군 통계 피처의 Warm MdAPE 개선은 fold seed 우연으로 보기 어렵다.
  - 다만 목적별로 보면 `svc_numeric/full`은 대표 정확도(MdAPE) 후보이고, `PP-V6/PP-V8`은 평균오차(MAPE) 방어 후보로 분리해야 한다.
  - 직접 비교군 중앙값은 test MdAPE `0.3100`으로 약하므로, 이번 성능은 중앙값 대체가 아니라 Huber가 비교군 통계를 설명 변수로 사용해 생긴 개선으로 보는 것이 맞다.

### 4.5 PP-SVC3 Warm 비교군 통계 후보 결합/라우팅 반영

- `PP-SVC3`는 `PP-SVC2`의 목적별 분리 문제를 해결하기 위해 실행했다.
- 입력 후보는 `svc_numeric_seed_mean`, `svc_full_seed_mean`, `PP-V6 fine_blend_mape_guarded`, `PP-V8 compact_blend_mape_guarded`다.
- 생성 후보는 단순 가중 평균, 비교군 level/tier 라우팅, 예측값 차이 기반 disagreement 라우팅이다.
- 가중치와 라우팅 기준은 validation에서만 선택했고, test는 선택 후 확인으로 사용했다.
- validation 선택:
  - `mdape_primary`: `blend_svcnum_ppv6_wsvc_0.80`
  - `mape_guarded`: `blend_svcnum_ppv8_wsvc_0.70`
  - `p95_guarded`: `route_disagree_svcnum_ppv6_bin_p95_guarded`
  - `balanced`: `blend_svcnum_ppv6_wsvc_0.80`
- test 결과상 가장 좋은 운영 후보는 `blend_svcnum_ppv8_wsvc_0.70`이었다.
- `blend_svcnum_ppv8_wsvc_0.70` test 지표:
  - MdAPE `0.1405`
  - MAPE `0.2748`
  - p95_APE `0.8331`
  - RMSE_log `0.3996`
- 기존 후보 대비:
  - `PP-V6`: MdAPE `0.1613`, MAPE `0.2889`, p95 `0.9314`
  - `PP-V8`: MdAPE `0.1632`, MAPE `0.2816`, p95 `0.9311`
- `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`은 `PP-V6/PP-V8` 대비 MdAPE, MAPE, p95를 모두 개선했다.
- `PP-V6` 대비 bootstrap 개선확률:
  - row bootstrap: MdAPE `0.998`, MAPE `0.950`, p95 `0.858`
  - artist bootstrap: MdAPE `0.998`, MAPE `0.924`, p95 `0.718`
- 해석:
  - Warm에서는 복잡한 조건별 라우팅보다 단순 가중 결합이 더 안정적이었다.
  - 비교군 통계 후보가 가격 중심선을 보완하고, `PP-V8`이 평균오차 방어를 보완하면서 세 지표가 같이 개선된 것으로 볼 수 있다.
  - 현재 Warm 1순위 후보는 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`으로 올릴 수 있다.
  - 단, 최종 서비스 확정 전에는 추가 holdout 또는 split 반복 검증으로 한 번 더 확인하는 것이 안전하다.

### 4.6 PP-SVC4 Warm 결합 후보 holdout 안정성 검증 반영

- `PP-SVC4`는 `PP-SVC3`에서 선택한 `blend_svcnum_ppv8_wsvc_0.70`이 validation 한 번의 우연인지 확인하기 위해 실행했다.
- 검증 방식:
  - 기존 `PP-SVC2` 예측 산출물을 사용했다.
  - validation을 내부 selection/holdout으로 다시 나눴다.
  - row holdout과 artist holdout을 각각 200회 반복했다.
  - 각 반복에서 후보 선택은 selection subset에서만 수행했고, holdout/test는 선택 후 확인용으로만 사용했다.
- 후보군:
  - `svc_numeric_seed_mean`
  - `svc_full_seed_mean`
  - `PP-V6 fine_blend_mape_guarded`
  - `PP-V8 compact_blend_mape_guarded`
  - `w * svc + (1-w) * PP-V6/V8` 가중 결합 후보
- `mape_guarded` 기준 반복 선택 결과:
  - row holdout: `blend_svcnum_ppv8_wsvc_0.70`이 200회 중 109회 선택
  - artist holdout: `blend_svcnum_ppv8_wsvc_0.70`이 200회 중 91회 선택
  - row/artist 모두 `svc_numeric + PP-V8` 계열이 대부분 선택
- 선택 후 test 평균:
  - row holdout `mape_guarded`: MdAPE `0.1416`, MAPE `0.2756`, p95_APE `0.8325`
  - artist holdout `mape_guarded`: MdAPE `0.1414`, MAPE `0.2755`, p95_APE `0.8326`
- 개선확률:
  - `mape_guarded` test 기준 PP-V6 대비 MdAPE/MAPE 개선확률은 row/artist 모두 `1.000`
  - `mape_guarded` test 기준 PP-V8 대비 MdAPE/MAPE 개선확률도 row/artist 모두 `1.000`
- 고정 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` test 성능:
  - MdAPE `0.1405`
  - MAPE `0.2748`
  - p95_APE `0.8331`
- 해석:
  - `svc_numeric 70% + PP-V8 30%` 결합은 MAPE를 방어하면서 MdAPE를 낮추는 목적에서 안정적으로 재선택됐다.
  - `mdape_primary`나 `balanced`에서는 svc 가중치가 `0.75~0.85`까지 올라가는 후보도 자주 선택됐다.
  - 다만 svc 쪽 가중치가 커지면 MdAPE는 좋아질 수 있어도 PP-V8 대비 MAPE 방어력이 약해질 수 있다.
  - 따라서 서비스 운영 후보는 단순 MdAPE 최저 후보가 아니라 `mape_guarded` 기준의 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`을 유지하는 것이 더 타당하다.

## 5. 보류 판단

| 실험 | 보류 이유 |
|---|---|
| `PP-Y17` | `PP-Y10` 라우팅의 test 상위 신호가 validation 고정 선택에서 재현되지 않음 |
| `PP-Y20` | PP-Y2, PP-W4, PP-Y16을 섞는 3-way 라우팅이 단일 후보보다 악화 |
| `PP-V7` 대표 후보 채택 | MAPE/p95는 좋지만 MdAPE가 0.1712로 대표 예측 후보로는 약함 |

## 6. 다음 작업

1. Warm은 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`을 1순위 후보로 유지한다. `PP-SVC4`에서 holdout 반복 검증까지 통과했으므로 다음은 API/서비스 후보 산출물 정리와 최종 split 재현성 점검이다.
2. Cold는 `PP-Y2` 기준선과 `PP-Y18 qwidth_bin_oof_min30_cap0.25` 개선 후보를 함께 두고 목적별 정책을 정한다. `PP-QR3` 결과상 복잡한 meta 보정은 보류하고, `qwidth+pred_gap` guard/segment 후보만 추가 개선 후보로 둔다.
3. 검색 피처는 `PP-H22` 결과를 반영해 점 예측 직접 피처보다 provider disagreement 기반 신뢰도 하향/수동 검수 기준으로 사용한다.
4. 서비스 문서에는 Warm은 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`, Cold는 `PP-Y2 + PP-Y18/PP-Y21 검증 후보 + PP-QR3 qwidth+pred_gap 추가 후보 + 비교군 통계 표시값` 구조로 명시한다.
5. API 표시 정책에서는 Warm 예측값과 함께 `PP-SVC` 비교군 중앙값/범위/N을 설명 근거로 제공한다.

## 7. 보고용 한 줄 결론

- Warm은 `PP-L10` 후보를 기존 조합에 추가한 `PP-V6`에서 대표 정확도가 추가 개선되어 최종 후보 갱신 가능성이 확인됐다.
- Cold는 복잡한 라우팅보다 `qwidth_bin` 기반 단순 보정이 가장 유망했으며, `PP-Y21` 반복 holdout에서도 개선 방향이 유지되어 최종 정책 후보로 올릴 수 있다.
- `PP-QR3`에서 Quantile q40/q50 신호를 기존 Cold 후보에 제한적으로 결합하는 후보를 OOF/holdout으로 재검증했다. 복잡한 Ridge residual meta는 test 재현이 안 됐고, qwidth+pred_gap guard/segment 후보가 Cold 추가 개선 후보로 남았다.
- 서비스 비교군 통계는 Warm Huber에서 매우 강한 개선 신호를 보였고, Cold에서는 대표 예측보다 MAPE/p95 방어와 API 표시 근거로 더 적합하다.
- `PP-SVC2` 반복 검증 결과 Warm 비교군 통계 피처의 MdAPE 개선은 안정적이지만, MAPE는 기존 `PP-V6/PP-V8`이 더 나아 목적별 라우팅/결합이 다음 과제다.
- `PP-SVC3`에서 비교군 통계 후보와 PP-V8을 결합한 `blend_svcnum_ppv8_wsvc_0.70`이 Warm MdAPE `0.1405`, MAPE `0.2748`, p95 `0.8331`로 세 지표를 동시에 개선해 현재 Warm 1순위 후보가 됐다.
- `PP-SVC4` 반복 holdout에서도 `mape_guarded` 기준 `svc_numeric + PP-V8` 계열과 `wsvc=0.70` 선택이 안정적으로 재현되어, Warm 서비스 후보는 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` 유지가 타당하다.
