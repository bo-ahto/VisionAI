# 모델 선정·피처 영향도·커스텀 조합 종합 리포트

- 작성일: 2026-06-03
- 최종 검수일: 2026-06-04
- 목적: 가격 예측 모델의 최종 후보 선정 이유, 피처 영향도 해석, 모델 특성에 맞춘 조합/보정 방식, 서비스 적용 판단 정리
- 읽는 대상: 실험 ID를 모르는 상사, 임원, 신규 합류자도 이 문서만 보고 전체 흐름을 이해할 수 있는 문서
- 주요 기준 문서:
  - `latest_experiment_result_synthesis.md`
  - `track6_feature_influence_with_results.md`
  - `warm_cold_feature_model_selection_summary.md`
  - `pp_svc1~pp_svc6` 실행 요약
  - `service_api_summary_for_collaboration.md`

## 1. 리포트 읽는 법

이 문서의 작성 기준:

- 실험 ID보다 한글 설명명 우선 표기
- `PP-SVC3`, `PP-Y18` 같은 이름은 실험 산출물을 다시 찾기 위한 내부 추적 ID
- 각 실험은 “왜 했는지, 어떻게 했는지, 결과가 무엇인지, 다음 판단이 무엇인지” 순서로 설명

| 표기 | 의미 |
|---|---|
| 설명명 | 실험의 목적과 역할을 사람이 이해하기 쉽게 적은 이름 |
| 내부 추적 ID | 실험 폴더, 실행 로그, 산출물을 찾기 위한 코드명 |
| 후보 | 실제 서비스 또는 후속 검증 대상으로 고려한 모델/조합 |
| 산출물 | 학습된 모델, 예측값 파일, 검증 결과, 리포트 등 실험 결과물 |
| holdout 검증 | 후보 선택에 쓰지 않은 데이터를 남겨두고, 선택된 후보가 그 데이터에서도 유지되는지 확인하는 검증 |
| OOF 예측 | 학습 데이터 안에서 자기 자신을 직접 맞히지 않게 만든 교차검증 예측값. 후처리 보정값이 과적합되지 않게 쓰는 안전장치 |
| seed | 학습/검증 반복 시 난수 시작점을 고정하는 값. 같은 조건에서 결과가 흔들리는지 보기 위한 반복 기준 |
| fold | 데이터를 여러 묶음으로 나눠 번갈아 검증하는 교차검증 묶음 |
| split | 학습용, 후보 선택용, 확인용 데이터로 나누는 분할 방식 |
| bootstrap | 데이터를 반복적으로 다시 뽑아 결과 안정성을 보는 검증 방식 |
| leaf | 트리 모델에서 최종적으로 샘플이 도착하는 끝 노드. 같은 leaf에 모인 샘플은 모델이 비슷한 조건으로 본 샘플 |
| tail risk | 일반 샘플보다 훨씬 크게 틀리는 끝단 오차 위험. 이 문서에서는 주로 p95_APE로 확인 |
| MdAPE | 절대 비율 오차의 중앙값. 대표적인 일반 샘플의 정확도 확인 지표 |
| MAPE | 절대 비율 오차의 평균. 큰 오차 샘플의 영향이 더 크게 반영되는 지표 |
| p95_APE | 절대 비율 오차 상위 5% 지점. 아주 크게 틀리는 위험 확인 지표 |
| 비교군 통계 | 같은 작가, 같은 크기, 같은 재료/지지체처럼 비슷한 조건의 과거 거래 가격을 요약한 값 |
| 비교군 중앙값 | 비교군 가격을 낮은 값부터 높은 값까지 정렬했을 때 가운데 있는 값. 평균보다 극단값 영향이 작음 |
| 비교군 범위 | 비교군 가격의 하위/상위 분위값 차이. 가격대가 좁은지 넓은지 확인하는 값 |
| 표본 수 N | 비교군 계산에 실제로 들어간 유효 거래 수. N이 작으면 통계 신뢰도가 낮음 |
| fallback 비교군 | 가장 세밀한 비교군이 부족할 때 더 넓은 비교군으로 순서대로 물러나는 구조 |
| compact blend | 여러 후보를 전부 쓰지 않고, 운영에 필요한 핵심 후보만 남겨 단순하게 섞은 결합 후보 |
| fine blend | 여러 후보를 촘촘한 가중치 후보로 넓게 섞어 본 탐색형 결합 후보 |
| 평균오차 방어 | MAPE가 커지지 않게 막는 성격. 일부 샘플에서 크게 틀리는 영향이 평균에 번지는 것을 줄이는 목적 |
| 큰 오차 방어 | p95_APE가 커지지 않게 막는 성격. 최악에 가까운 샘플의 가격 오류를 줄이는 목적 |
| `mape_guarded` | MdAPE가 과하게 나빠지지 않는 조건에서 MAPE가 낮은 후보를 고르는 선택 기준 |
| `p95_guarded` | MdAPE가 과하게 나빠지지 않는 조건에서 p95_APE가 낮은 후보를 고르는 선택 기준 |
| `wsvc` | 결합식에서 비교군 통계 후보가 차지하는 비율. 예: `wsvc_0.70`은 비교군 후보 70% |
| `wfallback` | 결합식에서 fallback 비교군 후보가 차지하는 비율. 예: `wfallback_0.600`은 fallback 후보 60% |
| `seed_mean` | 여러 seed로 반복 학습한 예측값의 평균. 우연한 난수 영향 완화 목적 |

## 2. 실험 ID 용어표

| 설명명 | 내부 추적 ID | 이 문서에서의 의미 |
|---|---|---|
| 비교군 통계 피처 검증 | `PP-SVC1` | 서비스 화면에 필요한 비교군 통계가 모델 성능에도 도움이 되는지 확인 |
| 비교군 통계 후보 안정성 검증 | `PP-SVC2` | 비교군 통계 후보가 seed와 fold가 바뀌어도 유지되는지 확인 |
| Warm 비교군 통계 70% + 평균오차 방어 30% 결합 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | Warm 최종 서비스 1순위 후보 |
| Warm 결합 후보 반복 holdout 검증 | `PP-SVC4` | `PP-SVC3`의 70:30 결합이 우연이 아닌지 row/artist holdout으로 200회씩 확인 |
| Warm 다층 비교군 통계 피처 실험 | `PP-SVC5` | 비교군을 더 세밀하게 여러 수준으로 동시에 넣는 방식이 유효한지 확인 |
| Warm fallback 비교군 + PP-V8 결합 비율 재검증 | `PP-SVC6` | PP-SVC5에서 좋아 보인 0.55~0.60 결합 비율이 반복 holdout에서도 안정적인지 확인 |
| 기존 Warm fine blend 후보 | `PP-V6` | 기존 Warm 후보 중 대표 오차가 낮았던 결합 후보 |
| 기존 Warm compact blend 후보 | `PP-V8` | 기존 Warm 후보 중 MAPE와 p95 방어가 좋았던 보조 후보 |
| Cold 검색/전시/갤러리 통합 기준 후보 | `PP-Y2` | Cold에서 작가 메타, 전시/갤러리, 검색 피처를 함께 쓴 LightGBM Quantile 기준 후보 |
| Cold 불확실성 폭 구간 보정 후보 | `PP-Y18` | quantile width 구간별 반복 오차를 OOF 기반으로 보정한 후보 |
| Cold 보정 후보 holdout 안정성 검증 | `PP-Y21` | `PP-Y18` 계열 보정 후보가 평가 구성 변화에도 유지되는지 확인 |
| Cold 큰 오차 방어 후보 | `PP-Y16` | p95_APE를 줄이기 위해 예측값 구간과 불확실성 구간을 함께 보정한 후보 |
| Warm에 Cold식 트리/확장 피처 적용 | `PP-Z1`, `PP-Z3`, `PP-Z4` | Warm에서도 CatBoost/LightGBM/Cold식 확장 피처가 도움이 되는지 확인 |
| 검색/갤러리 조건 보정 | `PP-I7` | 외부 검색/갤러리 조건을 활용한 제한적 보정 실험 |

### 2.1 내부 후보명 읽는 법

내부 후보명은 사람이 읽기 쉬운 이름이 아니라 실험 조건을 짧게 붙인 코드명:

| 후보명 조각 | 풀어쓴 의미 | 예시 |
|---|---|---|
| `svc` | service comparable stats. 서비스 비교군 통계 사용 | `svc_numeric` |
| `svcnum` | 비교군 통계 중 숫자 피처만 사용 | `blend_svcnum_ppv8_wsvc_0.70` |
| `svcfull` | 비교군 숫자 피처와 범주 피처를 함께 사용 | `svc_full_seed_mean` |
| `fallback_numeric` | 가장 적합한 비교군 하나를 fallback 순서로 고른 뒤 숫자 통계만 사용 | `fallback_numeric` |
| `ppv8` | PP-V8 compact blend 후보 | `blend_svcnum_ppv8_wsvc_0.70` |
| `blend_A_B` | A 후보와 B 후보를 로그 가격에서 가중 평균 | `blend_svcnum_ppv8_wsvc_0.70` |
| `wsvc_0.70` | 비교군 통계 후보 70%, 다른 후보 30% | `blend_svcnum_ppv8_wsvc_0.70` |
| `wfallback_0.600` | fallback 비교군 후보 60%, PP-V8 40% | `blend_fallback_numeric_ppv8_wfallback_0.600` |
| `qwidth` | quantile width. q90과 q10 예측 사이의 불확실성 폭 | `qwidth_bin_oof_min30_cap0.25` |
| `bin` | 연속값을 작은/중간/큰 구간으로 나눔 | `qwidth_bin` |
| `min30` | 해당 구간 표본이 최소 30개일 때만 보정 | `qwidth_bin_oof_min30_cap0.25` |
| `cap0.25` | 로그 보정값을 ±0.25 범위로 제한 | `qwidth_bin_oof_min30_cap0.25` |

대표 후보명 예시:

```text
blend_svcnum_ppv8_wsvc_0.70
= svc_numeric_seed_mean 예측값 70%
+ PP-V8 compact_blend_mape_guarded 예측값 30%
+ 로그 가격에서 결합
```

```text
qwidth_bin_oof_min30_cap0.25
= quantile width 구간별 보정
+ 자기 자신을 직접 맞히지 않은 OOF 예측값 사용
+ 구간 표본 최소 30개 필요
+ 보정값은 로그 기준 ±0.25로 제한
```

후보 비교 시 주의할 점:

- `PP-SVC3 wsvc_0.70`: `svc_numeric_seed_mean` 후보 70% + PP-V8 후보 30%
- `PP-SVC6 wfallback_0.600`: `fallback_numeric` 후보 60% + PP-V8 후보 40%
- `wsvc`와 `wfallback`은 비율 숫자가 비슷해도 기준 후보가 다름
- `PP-SVC3 0.70`과 `PP-SVC6 0.600`을 “같은 후보의 비율 차이”로 직접 비교하면 안 됨
- `PP-SVC1`: 고정 split에서 비교군 통계 피처의 성능 확인
- `PP-SVC2`: seed 반복 평균으로 비교군 통계 후보의 안정성 확인
- `PP-Y18`: 하나의 실험 ID 안에 여러 보정 후보 존재
- `PP-Y18 qwidth_bin`: 균형형 Cold 검증 기준 후보
- `PP-Y18 external_x_qwidth`: MdAPE는 더 낮지만 p95와 운영 안정성은 제한적인 참고 후보

## 3. 최종 판단 한눈에

| 구분 | 사람이 읽는 최종 판단 | 내부 추적 ID | 핵심 수치와 근거 |
|---|---|---|---|
| Warm 최종 후보 | 비교군 통계 후보 70%와 기존 평균오차 방어 후보 30%를 로그 가격에서 결합한 모델 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | test MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331` |
| Warm 안정성 | 결합 비율 70:30의 반복 holdout 재선택 | `PP-SVC4` | `mape_guarded` 기준 0.70 선택: row 109/200, artist 91/200 |
| Warm 추가 검증 | fallback 비교군과 PP-V8의 결합 비율 재검토 | `PP-SVC5`, `PP-SVC6` | test에서는 0.575~0.600이 좋아 보였지만 반복 선택 안정성 부족, 기존 PP-SVC3 유지 |
| Warm 핵심 피처 | 작가 기준선, 작품 크기, 비교군 통계 | `base_existing_combo` + 비교군 통계 | 작가/크기 제거 시 성능 급락, 비교군 통계 추가 후 MdAPE 크게 개선 |
| Cold 검증 기준 후보 | 불확실성 폭을 기준으로 반복 오차를 보정한 LightGBM Quantile 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | MdAPE `0.4247`, MAPE `0.9910`, p95_APE `3.3053`. bootstrap/holdout 안정성 확인 |
| Cold 추가 개선 후보 | qwidth와 q40/q50 차이를 제한적으로 쓰는 guard/segment 보정 | `PP-QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`, `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | guard test MdAPE `0.4178`, MAPE `0.9640`, p95 `2.5377`. 최종 교체 전 split 재검증 필요 |
| Cold 서비스 판단 | 단일 확정 가격이 아니라 참고 예측가와 넓은 범위로 제공 | `PP-Y18`, `PP-Y21`, `PP-QR3`, `PP-Y16` | 개선 신호는 있으나 Warm 수준의 안정성은 아님 |
| 서비스 적용 | Warm은 점 예측과 범위, Cold는 참고값과 낮은 신뢰도 표시 | API 문서와 연동 | Cold는 p95와 구성 변동성이 커 예측 신뢰도 차이를 화면에 반영해야 함 |

보고용 핵심 문장:

> Warm은 같은 작가의 과거 거래가 있어 Huber 모델의 작가/크기 중심선이 잘 작동. 서비스 비교군 통계를 모델 피처로 넣어 대표 오차를 낮추고, PP-V8 compact blend를 30% 섞어 평균오차와 큰 오차를 방어. PP-SVC5/6에서 더 낮은 test 후보도 확인했지만 반복 선택 안정성이 부족해 기존 PP-SVC3 70:30 후보 유지. Cold는 같은 작가 기준선이 없어 단일 가격 확정 모델로 쓰기 어렵고, 안정성 검증이 된 PP-Y18을 기준 후보로 두되 PP-QR3 guard/segment 보정은 추가 개선 후보로 관리. 서비스에서는 참고 예측가, 가격 범위, 낮은 신뢰도로 제공 필요.

## 4. Warm/Cold를 분리한 이유

| 구분 | 데이터 조건 | 예측에서 어려운 점 | 적합한 모델 방향 |
|---|---|---|---|
| Warm | 학습 데이터에 같은 작가가 있음 | 작가별 기준 가격을 안정적으로 반영해야 함 | 작가 기준선과 크기 효과를 직접 설명할 수 있는 Huber 계열 |
| Cold | 학습 데이터에 같은 작가가 없거나 매칭이 불확실함 | 작가 시장 가격대를 직접 알 수 없음 | 작품 조건, 작가 메타, 외부 활동성, 불확실성 구간을 함께 쓰는 트리/분위수 계열 |

Warm과 Cold의 난이도 차이:

- Warm: 이미 본 작가의 새 작품 예측
- Cold: 처음 보는 작가 또는 매칭이 불확실한 작가의 작품 예측
- Warm/Cold 통합 지표만 볼 경우 모델의 실제 위험 은폐 가능

## 5. Warm 모델 선정 근거

### 5.1 Warm 기준 모델: Huber

Warm Huber의 가격 예측 방식:

- 실제 가격을 바로 예측하지 않고 로그 가격을 먼저 예측
- 고가 작품 때문에 크게 치우친 가격 분포를 로그 가격으로 완화
- 극단값에 대한 모델 흔들림 감소

```text
pred_log_price = intercept + Σ(coefficient_j * transformed_feature_j)
pred_price = exp(pred_log_price)
```

쉽게 풀어쓴 예측 순서:

```text
1. 작가, 크기, 재료, 지지체 같은 피처를 숫자로 변환
2. 각 피처에 모델이 학습한 계수 곱하기
3. 모두 더해서 로그 가격 생성
4. exp 적용 후 실제 가격 단위로 복원
```

Huber 손실의 핵심:

- 일반 선형 회귀보다 큰 오차 샘플을 과하게 따라가지 않는 구조
- 고가/저가 특이 작품에 대한 계수 흔들림 완화

```text
residual = actual_log_price - pred_log_price

if abs(residual) <= delta:
    loss = 0.5 * residual^2
else:
    loss = delta * (abs(residual) - 0.5 * delta)
```

Huber가 Warm에 적합한 이유:

| 이유 | 설명 |
|---|---|
| 작가 기준선 설명 가능 | `artist_key`가 작가별 평균 가격대를 계수로 반영 |
| 크기 효과 설명 가능 | `width_cm`, `height_cm`, `area_cm2`, `log_area`가 가격 중심선 조정 |
| 이상치 방어 | 고가/저가 특이 작품이 있어도 전체 계수의 과도한 흔들림 완화 |
| 후처리 연결성 | 잔차(`actual_log - pred_log`) 기반 구간 보정/결합 후보 생성 용이 |

### 5.2 Warm 기준 피처셋: base_existing_combo

`base_existing_combo`의 의미:

- Warm Huber 최종 모델 산출물의 기준 피처셋
- 모델 산출물: 학습된 모델, 피처 목록, 예측값, 평가 결과처럼 운영 재현에 필요한 결과 묶음
- 구성 축: 작가 기준 가격대 + 작품 크기 + 보조 물성 정보

| 피처 그룹 | 실제 피처 | 모델에서의 영향 | 선정 근거 |
|---|---|---|---|
| 작가 기준선 | `artist_key` | 같은 작가의 과거 가격 수준 반영 | 제거 시 MdAPE 약 `0.48~0.49`로 급락 |
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품 규모에 따른 가격 차이 반영 | 제거 시 MdAPE 약 `0.55~0.56`, p95 약 `5.2~5.4`로 악화 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체/깊이 조건 보조 | 영향은 작지만 특이 작품 경고와 범위 정책에 유용 |
| 형태 | `aspect_ratio`, `is_extreme_aspect_ratio` | 극단적인 가로세로 비율 보조 | 단독 중요도 낮음, 보정 우선순위 낮음 |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` | 재료와 바탕 조합 차이 보조 | Warm에서는 작가/크기보다 약하지만 조건 설명에 필요 |

Warm 영향도 해석 기준:

- 모든 피처가 같은 비중이라는 의미 아님
- 작가 기준선과 크기를 핵심축으로 해석
- 보조 피처는 조건 설명과 위험 구간 판단에 활용

```text
1순위: artist_key
2순위: width/height/area/log_area
3순위: depth/aspect/medium/support 보조 피처
최종 조합 보강축: 비교군 통계 피처
```

주의:

- 위 1~3순위는 `base_existing_combo` 내부의 기본 피처 해석 순서
- 비교군 통계 피처는 `base_existing_combo` 이후 PP-SVC 실험에서 추가된 보강 피처
- 최종 후보에서는 비교군 통계가 단순 4순위 보조가 아니라 Warm 오차를 크게 줄인 핵심 보강축

## 6. Warm 비교군 통계와 최종 조합

### 6.1 비교군 통계 피처를 추가한 이유

비교군 통계의 쉬운 설명:

- 이 작품과 비슷한 조건의 과거 작품들이 보통 어느 가격대였는지 요약한 값
- 사람 감정사가 “같은 작가의 비슷한 크기 작품은 과거에 얼마였는가”를 먼저 보는 방식과 유사
- 단, 비교군 통계 하나만으로 최종 가격을 정하지 않음
- 모델이 작가, 크기, 재료 피처와 함께 참고하는 보조 가격 기준선

비교군을 찾는 순서:

| 순서 | 비교군 수준 | 풀어쓴 의미 | 최소 표본 기준 |
|---:|---|---|---:|
| 1 | `artist_medium_support_size` | 같은 작가 + 같은 재료/지지체 + 비슷한 크기 | 5 |
| 2 | `artist_size` | 같은 작가 + 비슷한 크기 | 5 |
| 3 | `artist` | 같은 작가 전체 | 5 |
| 4 | `medium_support_size` | 같은 재료/지지체 + 비슷한 크기 | 30 |
| 5 | `medium_category_support_size` | 같은 재료 + 같은 지지체 + 비슷한 크기 | 30 |
| 6 | `medium_size` | 같은 재료 + 비슷한 크기 | 50 |
| 7 | `global` | 위 조건이 부족할 때 전체 train 기준 | 전체 |

fallback 구조의 의미:

- 1번처럼 가장 세밀한 비교군이 충분하면 해당 통계 사용
- 표본 수가 부족하면 2번, 3번처럼 더 넓은 비교군으로 이동
- 목적: 너무 적은 표본에서 나온 불안정한 중앙값 사용 방지
- 서비스에서도 같은 원리로 “표본 수 N”과 “비교군 수준”을 함께 표시 가능

모델에 들어간 비교군 숫자 피처:

| 피처 | 쉬운 의미 | 모델에서의 역할 |
|---|---|---|
| `svc_group_log_price_median` | 같은 비교군의 로그 가격 중앙값 | 가격 중심선 |
| `svc_group_log_price_q25` | 비교군 하위 25% 가격 | 낮은 가격대 기준 |
| `svc_group_log_price_q75` | 비교군 상위 25% 가격 | 높은 가격대 기준 |
| `svc_group_log_price_iqr` | q75와 q25의 차이 | 가격 분산/불확실성 |
| `svc_group_log_unit_area_median` | 면적 단가 중앙값 | 크기 차이를 보정한 가격 기준 |
| `svc_group_log_unit_area_iqr` | 면적 단가 범위 | 단가 기준 가격 변동성 |
| `svc_group_n_log` | 표본 수 N의 로그값 | 통계 신뢰도 힌트 |

모델에 들어간 비교군 범주 피처:

| 피처 | 쉬운 의미 | 모델에서의 역할 |
|---|---|---|
| `svc_group_level` | 어떤 fallback 단계에서 비교군이 잡혔는지 | 비교군 신뢰 수준 |
| `svc_coverage_tier` | 표본 수가 high/medium/low인지 | 통계 안정성 |
| `svc_has_artist_level` | 작가 기반 비교군인지 여부 | 작가 기준선 포함 여부 |

후보명 차이:

| 내부 후보명 | 구성 | 해석 |
|---|---|---|
| `svc_numeric` | 비교군 숫자 피처만 추가 | 성능 개선의 핵심 후보 |
| `svc_full` | 숫자 피처 + 범주 피처 추가 | 비교군 수준 정보까지 모델에 제공 |
| `fallback_numeric` | PP-SVC5/6에서 같은 의미로 재사용한 선택형 비교군 숫자 후보 | 운영 설명과 결합 비율 재검증에 사용 |
| `direct median` | 비교군 중앙값 자체를 예측값으로 사용 | 모델 없이 비교군 가격만 보는 단순 기준선 |

비교군 통계 피처 검증 목적:

- 서비스 화면에 필요한 값: 비교군 가격 중앙값, 가격 범위, 매체별 분포, 표본 수 N
- 호당가 중앙값: 기존 `estimated_ho` 호수 산출식으로 서비스 제공 가능
- PP-SVC1 비교군 통계 실험 일부 split의 대체값: 면적 단가 중앙값과 면적 단가 범위
- 확인 내용: 해당 통계가 단순 표시값인지, 모델 성능에도 도움이 되는 피처인지 검증
- 내부 추적 ID: `PP-SVC1`

| 후보 설명 | 내부 후보명 | test MdAPE | test MAPE | test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| 비교군 통계 없는 Warm Huber 기준선 | baseline | 0.2274 | 0.4952 | 2.0130 | 후처리 전 기준선 |
| 비교군 숫자 통계 피처 추가 후보 | `svc_numeric` | 0.1528 | 0.2956 | 0.9694 | 비교군 통계 피처 추가로 큰 개선 |
| 비교군 숫자+범주 통계 피처 추가 후보 | `svc_full` | 0.1496 | 0.2965 | 0.9499 | MdAPE 최저 |
| 비교군 중앙값을 가격으로 직접 사용 | direct median | 0.3100 | - | - | 단순 중앙값 대체는 약함 |

해석:

- 비교군 중앙값 직접 대체 방식은 성능 약함
- 성능 개선 원인: “중앙값 대체”가 아닌 “비교군 통계 피처 추가”
- Huber가 작가/크기 피처와 비교군 통계를 함께 사용해 가격 중심선 개선
- 단순히 “비슷한 작품 중앙값으로 가격을 바꿈”이 아님
- Huber가 기존 작가/크기 계수와 비교군 통계의 관계를 다시 학습한 결과

### 6.2 비교군 통계 후보의 반복 안정성

비교군 통계 후보 안정성 검증:

- 목적: 비교군 통계 후보가 한 번의 split에서만 좋아진 것인지 확인
- 방법: seed 반복 검증
- 내부 추적 ID: `PP-SVC2`

| 후보 설명 | 내부 후보명 | test MdAPE | test MAPE | test p95_APE | 기존 Warm fine blend 대비 MdAPE 개선확률 |
|---|---|---:|---:|---:|---:|
| 비교군 숫자 통계 후보의 seed 평균 | `svc_numeric_seed_mean` | 0.1520 | 0.2942 | 0.9381 | row/artist `0.842/0.842` |
| 비교군 숫자+범주 통계 후보의 seed 평균 | `svc_full_seed_mean` | 0.1533 | 0.2956 | 0.9190 | row/artist `0.796/0.802` |
| 기존 Warm fine blend 후보 | `PP-V6` | 0.1613 | 0.2889 | 0.9314 | 기준 |
| 기존 Warm compact blend 후보 | `PP-V8` | 0.1632 | 0.2816 | 0.9311 | 기준 |

핵심 해석:

- 비교군 통계 후보: MdAPE 개선 강점
- 기존 Warm compact blend 후보: MAPE 방어 강점
- 결론: 단일 후보 선택보다 역할이 다른 후보 결합이 합리적

### 6.3 Warm 최종 후보: 비교군 통계 70% + 평균오차 방어 30%

Warm 최종 조합 실험:

- 목적: 비교군 통계 후보의 대표 정확도와 기존 compact blend 후보의 평균오차 방어력 결합
- 내부 추적 ID: `PP-SVC3`
- 최종 후보명: `blend_svcnum_ppv8_wsvc_0.70`

여기서 “평균오차 방어력”의 의미:

- MAPE가 낮아지는 성격
- 특정 샘플 몇 개가 크게 틀려 평균오차를 끌어올리는 문제를 줄이는 역할
- MdAPE만 낮은 후보는 일반 샘플에는 좋아도 큰 오차 샘플이 남을 수 있음
- 서비스에서는 사용자가 보는 개별 예측의 큰 실패를 줄여야 하므로 MAPE/p95 방어가 중요

PP-V8 compact blend의 쉬운 설명:

- 여러 Warm 보조 후보 중 운영에 쓸 수 있는 핵심 후보만 남긴 단순 결합 후보
- `compact` 의미: 후보 수와 구조를 줄여 배포/설명/재현이 쉬운 형태
- `blend` 의미: 한 모델만 쓰지 않고 로그 가격 예측값을 섞는 방식
- `mape_guarded` 의미: MdAPE를 크게 해치지 않는 범위에서 MAPE가 낮은 조합 선택

PP-V8 compact blend 내부 구성:

| 구성 요소 | 가중치 | 역할 |
|---|---:|---|
| `v2_defensive` | 0.75 | 평균오차와 큰 오차 방어 중심 |
| `l10_generated_bucket_seq` | 0.25 | 생성 구간 피처 기반 순차 보정 후보 |
| `v1_representative` | 0.00 | 대표 정확도 후보지만 해당 정책에서는 제외 |
| `l10_meta_external_search_seq` | 0.00 | 외부 검색/메타 후보지만 해당 정책에서는 제외 |

PP-V8 자체의 test 성능:

- MdAPE `0.1632`
- MAPE `0.2816`
- p95_APE `0.9311`
- 해석: 대표 정확도는 비교군 통계 후보보다 약하지만 MAPE와 p95 방어가 좋음

입력 후보:

| 사람이 읽는 후보명 | 내부 후보명 | 역할 |
|---|---|---|
| 비교군 숫자 통계 Warm 후보 | `svc_numeric_seed_mean` | MdAPE를 낮추는 중심선 후보 |
| 비교군 숫자+범주 통계 Warm 후보 | `svc_full_seed_mean` | 비교군 통계를 더 넓게 넣은 후보 |
| 기존 Warm fine blend 후보 | `PP-V6 fine_blend_mape_guarded` | 기존 평균오차 방어 후보 |
| 기존 Warm compact blend 후보 | `PP-V8 compact_blend_mape_guarded` | MAPE와 p95 방어가 좋은 보조 후보 |

PP-V6와 PP-V8의 차이:

| 구분 | PP-V6 fine blend | PP-V8 compact blend |
|---|---|---|
| 목적 | 후보를 넓게 섞어 성능 탐색 | 운영에 쓸 수 있게 후보 구조 단순화 |
| 후보 수 | 상대적으로 많음 | 핵심 후보 중심 |
| 장점 | 탐색 폭이 넓음 | 설명과 재현이 쉬움 |
| 이 리포트에서의 역할 | 기존 Warm 비교 기준 | 최종 70:30 결합의 30% 방어 후보 |

최종 계산 공식:

```text
pred_log_final = 0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8
price_krw = exp(pred_log_final)
```

공식 해석:

- `pred_log_svc_numeric`: 비교군 통계 피처를 사용한 Warm Huber 로그 가격 예측값
- `pred_log_pp_v8`: 기존 Warm compact blend 후보의 로그 가격 예측값
- 결합 위치: 실제 가격이 아닌 로그 가격
- 로그 가격 결합 이유: 고가 작품이 결합값을 과하게 흔드는 문제 완화
- 70:30 의미: 비교군 통계 후보를 주력으로 사용, 평균오차/큰 오차 방어 후보를 보조로 반영

test 결과:

| 후보 설명 | 내부 후보명 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| 기존 Warm fine blend 후보 | `PP-V6` | 0.1613 | 0.2889 | 0.9314 | 0.4079 |
| 기존 Warm compact blend 후보 | `PP-V8` | 0.1632 | 0.2816 | 0.9311 | 0.4028 |
| Warm 최종 70:30 결합 후보 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | 0.1405 | 0.2748 | 0.8331 | 0.3996 |

결합한 이유:

| 구성 요소 | 역할 |
|---|---|
| 비교군 숫자 통계 후보 70% | 작가/작품 조건과 비교군 통계를 반영한 대표 가격 중심선 개선 |
| 기존 compact blend 후보 30% | 평균오차와 p95 방어를 통한 과도한 치우침 완화 |
| 로그 가격 결합 | 가격 분포의 큰 치우침과 고가 작품 영향 완화 |

70:30을 단순하게 풀어쓴 설명:

- 70%: 비교군 통계 후보가 제시한 가격 중심선 반영
- 30%: PP-V8이 가진 평균오차/큰 오차 방어 성격 반영
- 비교군 통계 후보만 쓰면 대표 정확도는 좋지만 일부 큰 오차 방어가 약할 수 있음
- PP-V8만 쓰면 평균오차 방어는 좋지만 대표 정확도가 비교군 후보보다 약함
- 두 후보를 로그 가격에서 섞어 세 지표를 동시에 낮추는 목적

### 6.4 Warm 결합 후보 반복 holdout 검증

Warm 결합 후보 반복 holdout 검증:

- 목적: Warm 결합 후보가 validation 한 번의 우연인지 확인
- 내부 추적 ID: `PP-SVC4`

검증 방식:

- validation을 후보 선택용 데이터와 확인용 holdout 데이터로 재분할
- 일반 row holdout 200회 반복
- 작가 단위 artist holdout 200회 반복
- 후보 선택은 selection 데이터에서만 수행
- holdout/test는 선택 후 확인용으로만 사용

핵심 결과:

| 확인 항목 | 결과 | 의미 |
|---|---:|---|
| 고정 Warm 최종 후보 test MdAPE | 0.1405 | 기존 후보보다 낮은 대표 오차 |
| 고정 Warm 최종 후보 test MAPE | 0.2748 | 기존 후보보다 낮은 평균오차 |
| 고정 Warm 최종 후보 test p95_APE | 0.8331 | 낮아진 큰 오차 위험 |
| row holdout에서 70:30 비율 선택 | 109/200 | 일반 샘플 재분할에서도 잦은 재선택 |
| artist holdout에서 70:30 비율 선택 | 91/200 | 작가 단위 검증에서도 선택 신호 유지 |
| row holdout에서 같은 결합 계열 선택 비율 | 0.930 | 세부 비율이 달라도 결합 구조 자체의 강한 신호 |
| artist holdout에서 같은 결합 계열 선택 비율 | 0.950 | 작가 단위에서도 결합 구조 유지 |

`mape_guarded` 선택 기준:

- MdAPE만 낮은 후보가 아니라 MAPE가 악화되지 않는 후보 선택
- 서비스 관점에서 평균적으로 크게 틀리는 샘플 감소 목적
- Warm 최종 결합 비율 선택 기준으로 사용

쉽게 풀어쓴 `mape_guarded`:

- 1단계: 대표 정확도(MdAPE)가 너무 나빠지는 후보 제외
- 2단계: 남은 후보 중 평균오차(MAPE)가 낮은 후보 선택
- 이유: MdAPE만 보면 일반 샘플은 좋아도 큰 오차 샘플을 놓칠 수 있음
- 서비스 기준: “평균적으로 너무 크게 틀리지 않는 예측”도 함께 중요

| holdout 방식 | 선택 후 test MdAPE 평균 | 선택 후 test MAPE 평균 | 선택 후 test p95_APE 평균 | 기존 fine blend 대비 MAPE 개선확률 | 기존 compact blend 대비 MAPE 개선확률 |
|---|---:|---:|---:|---:|---:|
| row holdout | 0.1416 | 0.2756 | 0.8325 | 1.000 | 1.000 |
| artist holdout | 0.1414 | 0.2755 | 0.8326 | 1.000 | 1.000 |

최종 해석:

- 단순 MdAPE 기준: 비교군 통계 가중치 0.75~0.85도 선택 가능
- 서비스 기준: MAPE 방어 중요
- `mape_guarded` 기준: 0.70 결합이 가장 안정적
- Warm 서비스 후보: 비교군 통계 70% + 기존 compact blend 30% 결합 유지

### 6.5 추가 검증: 다층 비교군과 결합 비율 재검토

PP-SVC5를 추가로 진행한 이유:

- 질문: 비교군을 더 세밀하게 쪼개고 여러 수준을 동시에 넣으면 더 좋아지는가
- 내부 추적 ID: `PP-SVC5`
- 대상: Warm Huber
- 방식: 기존 fallback 비교군 통계, 다층 비교군 통계 default/loose/strict, PP-V8 결합 비율 비교

PP-SVC5 핵심 결과:

| 확인 내용 | 결과 | 해석 |
|---|---|---|
| 다층 비교군 원시 피처 직접 투입 | Huber 수렴 불안정 | 비교군 통계를 무조건 많이 넣는 방식은 부적합 |
| 기존 fallback 비교군 통계 | 안정적 | 가장 신뢰 가능한 비교군 하나를 고르는 구조가 더 적합 |
| `fallback_numeric + PP-V8` test 상위 | `w=0.55~0.60` | test 관찰값으로는 개선 가능성 |
| 바로 채택 여부 | 보류 | validation 반복 안정성 확인 필요 |

다층 비교군이 불안정했던 이유:

- 여러 비교군 수준의 중앙값/범위/N이 서로 강하게 겹침
- Huber는 선형 계수 모델이라 중복 피처가 많으면 계수 해석과 수렴이 흔들릴 수 있음
- 비교군 통계는 “여러 개를 다 넣기”보다 “신뢰 가능한 하나를 선택해 넣기”가 현재 데이터에서 더 안정적

PP-SVC6를 추가로 진행한 이유:

- 질문: PP-SVC5에서 test가 좋아 보인 0.55~0.60 결합 비율이 우연인지 확인
- 내부 추적 ID: `PP-SVC6`
- 대상 후보: `fallback_numeric`, `PP-V8 compact_blend_mape_guarded`, 기존 `PP-SVC3`
- 방식: validation을 selection/holdout으로 200회 반복 분할, row/artist 기준 모두 확인

PP-SVC3와 PP-SVC6의 비율 차이:

| 구분 | 결합 대상 | 비율 의미 |
|---|---|---|
| `PP-SVC3 wsvc_0.70` | `svc_numeric_seed_mean` + PP-V8 | 비교군 숫자 통계 후보를 70% 사용 |
| `PP-SVC6 wfallback_0.600` | `fallback_numeric` + PP-V8 | fallback 비교군 후보를 60% 사용 |

해석:

- 두 실험 모두 PP-V8을 보조 후보로 섞음
- 앞쪽 후보가 `svc_numeric_seed_mean`인지 `fallback_numeric`인지 다름
- 따라서 `0.70`과 `0.600`은 같은 기준의 단순 비율 비교가 아님

PP-SVC6 고정 test 결과:

| 후보 | MdAPE | MAPE | p95_APE | 해석 |
|---|---:|---:|---:|---|
| 기존 PP-SVC3 70:30 후보 | 0.1405 | 0.2748 | 0.8331 | 현재 서비스 1순위 |
| `fallback + PP-V8`, `w=0.575` | 0.1348 | 0.2711 | 0.8362 | MdAPE/MAPE 개선, p95 소폭 악화 |
| `fallback + PP-V8`, `w=0.600` | 0.1362 | 0.2717 | 0.8329 | 세 지표 모두 소폭 개선 |

PP-SVC6 반복 holdout 결과:

| 선택 기준 | row holdout 선택 중앙값 | artist holdout 선택 중앙값 | 해석 |
|---|---:|---:|---|
| `mape_guarded_ppv8` | 0.725 | 0.725 | MAPE 방어 기준은 0.55~0.60보다 높은 비율 선호 |
| `mape_guarded_reference` | 0.725 | 0.725 | 기존 PP-SVC3 기준으로도 0.725 중심 |
| `balanced_reference` | 0.850 | 0.850 | 균형 기준은 비교군 비중을 더 크게 선호 |
| `mdape_primary` | 0.875 | 0.875 | MdAPE만 보면 비교군 비중을 더 크게 선호 |

PP-SVC6 최종 해석:

- `0.575~0.600`은 test 관찰값으로는 매력적
- 그러나 validation 반복 선택에서는 안정적으로 선택되지 않음
- 선택 후 test 평균은 기존 PP-SVC3보다 안정 개선으로 보기 어려움
- 서비스 후보 갱신은 보류
- Warm 서비스 1순위 후보는 기존 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` 유지

종합 판단:

```text
비교군 통계를 더 많이 쪼개는 방향은 보류
결합 비율을 0.575~0.600으로 낮추는 방향도 안정성 부족으로 보류
기존 PP-SVC3 70:30 후보 유지
```

## 7. Warm에서 채택하지 않은 시도와 이유

| 시도 설명 | 내부 추적 ID | 결과 | 보류 이유 |
|---|---|---|---|
| Warm을 CatBoost 단독 또는 확장 피처로 다시 학습 | `PP-Z3` | MdAPE `0.3186` | 조건 조합은 가능하나 Warm 작가 기준선보다 불안정 |
| Warm을 LightGBM Quantile로 대체 | `PP-Z4` | MdAPE `0.3171` | Warm 최종 후보 대체 수준 미달 |
| Cold에서 쓰던 확장 피처를 Warm에 적용 | `PP-Z1` | Huber 기준선보다는 개선, 최종 후보보다는 약함 | `artist_key`가 이미 강해 외부 피처 효과 제한 |
| CatBoost로 Warm residual 보정 | `PP-I7` | PP-V6 대비 MAPE/p95 방어 신호는 있으나 PP-V8 대비 MAPE 우위가 약하고 MdAPE 악화 | 대표 점 예측 후보로 부적합 |
| 조건별 라우팅으로 Warm 후보 선택 | `PP-SVC3` 일부 route 후보 | 가중 결합보다 약함 | Warm에서는 복잡한 분기보다 단순 결합이 더 안정적 |
| 다층 비교군 통계 원시 피처 직접 투입 | `PP-SVC5` | Huber 수렴 불안정 | 중복 비교군 피처가 많아 선형 계수 모델과 맞지 않음 |
| fallback 비교군 + PP-V8 결합 비율 0.575~0.600 채택 | `PP-SVC6` | 고정 test는 좋지만 반복 holdout 선택 안정성 부족 | 서비스 후보 갱신은 보류, 기존 PP-SVC3 유지 |

Warm 핵심 결론:

```text
Huber 중심선 유지
+ 비교군 통계 피처
+ 기존 compact blend의 평균오차 방어력
+ 로그 가격 70:30 결합
= Warm 최종 후보
```

## 8. Cold 모델과 피처 선정 근거

### 8.1 Cold의 기본 문제

Cold의 기본 문제:

- 같은 작가의 학습 이력 없음 또는 부족
- 같은 크기와 매체의 작품이라도 작가 시장 지위에 따라 큰 가격 차이 발생
- 작품 자체 정보와 작가 외부 정보의 동시 활용 필요

| 피처 축 | 주요 피처 | 역할 |
|---|---|---|
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area`, `size_bucket` | 가격대의 물리적 기준 |
| 깊이/3D | `depth_cm`, `has_depth`, `is_3d_candidate` | 평면/입체 후보 분리 |
| 재료/형태 | `medium_category`, `shape_bucket`, `medium_shape_bucket` | CatBoost가 조건 조합을 나누는 핵심 |
| 지지체/크기 | `support_category`, `support_size_bucket` | LightGBM이 세밀한 leaf 구간을 나누는 기준 |
| 작가 메타 | 작품 수, 팔로워, 출생연도, 국적, 판매 작품 수 | 작가 기준선 부족 보완 |
| 전시/갤러리 | 개인전/단체전/아트페어, 갤러리 tier | 작가 활동성과 시장 노출 |
| 검색 피처 | 검색 결과 수, 검색 품질, 문맥 count | 인지도와 정보 가용성의 보조 지표 |
| 불확실성 | `quantile_width`, `price_range_ratio` | 모델이 위험하게 보는 구간을 분리 |

Cold 피처 사용 구조 도표:

```text
작품 자체 정보
  - 크기, 깊이, 재료, 지지체, 형태
        |
        v
작가를 직접 본 적 없는 문제 보완
  - 작가 메타, 전시/갤러리, 외부 검색 활동성
        |
        v
LightGBM Quantile / CatBoost 후보 학습
  - 중앙 예측값
  - q10~q90 가격 범위
  - qwidth 기반 위험 구간
        |
        v
Cold 서비스 출력
  - 참고 예측가
  - 넓은 가격 범위
  - 낮은 신뢰도 또는 검수 필요 표시
```

### 8.2 Cold 외부 검색 데이터 생성 방법

Cold에서 외부 검색 데이터를 쓰는 이유:

- Cold는 같은 작가의 과거 학습 가격이 부족함
- 작품 크기/재료만으로 작가 시장 지위를 충분히 설명하기 어려움
- 전시, 갤러리, 뉴스, 미술 기관 노출은 작가 활동성과 정보 가용성을 보완하는 신호
- 단, 검색 결과는 동명이인, 홍보성 문서, 비미술 문맥이 섞일 수 있어 직접 가격으로 쓰면 위험
- 따라서 외부 검색값은 “가격을 직접 올리는 값”이 아니라 “작가 활동성/검색 신뢰도/불확실성 보조 피처”로 사용
- 실제 구현 기준: 현재 최종 스냅샷과 provider 일치도 검증은 Naver 공식 API와 Python/DDG 검색 계열을 기준으로 해석

외부 검색 수집 흐름도:

```text
작가명 준비
  - Cold 작가명 기준 목록
  - 한글명/영문명/별칭은 artist_search_name으로 추적
        |
        v
검색 질의문 생성
  - "{작가명} 미술 작가"
  - "{작가명} 작품 미술"
  - "{작가명} 전시 작가"
  - "{작가명} 갤러리 미술"
  - "{작가명} 작품 경매"
        |
        v
검색 제공자별 수집
  - Naver 공식 API: blog/news/webkr
  - Python/DDG 검색: python_ddg, python_ddg_art_context
        |
        v
검색 결과 정규화
  - 제목, 요약문, URL, 도메인, 순위, 제공자, 수집 시각 저장
        |
        v
미술 문맥/동명이인 필터
  - 작가명 일치
  - 미술 키워드 포함
  - 갤러리/미술관/옥션/뉴스 도메인 분류
  - 동명이인 위험 점수 계산
        |
        v
작가 단위 피처 집계
  - 검색 결과 수
  - 뉴스/갤러리/미술관/옥션 source 수
  - 검색 품질 등급
  - provider 일치도: Naver 공식 API와 Python/DDG 결과의 일관성
  - 수동 검수 필요 여부
        |
        v
Cold 모델 입력 또는 신뢰도 정책 입력
```

주의:

- Google Custom Search는 함수와 키 검토는 했지만 현재 최종 외부 검색 스냅샷, provider 일치도 계산, 성능 해석에는 포함하지 않음
- 따라서 이 보고서에서 “외부 검색 피처”라고 할 때의 실제 기준은 Naver 공식 API와 Python/DDG 계열 검색 결과

검색 제공자별 역할:

| 제공자 | 실제 사용 상태 | 사용 목적 | 주의점 |
|---|---|---|---|
| Naver 공식 API `naver_api_blog`, `naver_api_news`, `naver_api_webkr` | 현재 사용 | 국내 작가명, 국내 뉴스/블로그/웹 노출 확인 | API 인증/쿼터 관리 필요. 검색량 자체가 가격 신호는 아님 |
| Python/DDG 검색 `python_ddg`, `python_ddg_art_context` | 현재 보조 사용 | Naver 결과와 다른 검색 경로에서도 같은 작가 문맥이 잡히는지 확인 | 무료/라이브러리 기반 수집은 결과 변동 가능. 캐시와 수집 시각 기록 필수 |
| Python/DDG art-domain 제한 검색 `python_ddg_art_domains` | 진단용 | 미술 도메인 제한 검색이 필요한지 확인 | 최신 최종 스냅샷과 provider 일치도 계산에는 기본 사용하지 않음 |
| Naver HTML, DuckDuckGo HTML | 파일럿/진단용 fallback | 공식 API가 비거나 연결 검증이 필요할 때 임시 확인 | 운영 기본값으로 두지 않음 |
| Google Custom Search | 현재 미사용 | 검토용 함수는 있으나 최신 실험 결과와 provider 일치도 계산에는 포함하지 않음 | 현재 보고서의 외부 검색 성능 근거로 사용하지 않음 |

검색 결과 원천 저장 컬럼:

| 컬럼 | 의미 | 쓰임 |
|---|---|---|
| `artist_key` | 내부 작가 식별자 | 모델 피처와 조인하는 기준 |
| `artist_search_name` | 검색에 사용한 작가명 | 한글명/영문명/별칭 차이 추적 |
| `provider` | Naver 공식 API 또는 Python/DDG 계열 provider | provider별 편향과 일치도 확인 |
| `query_template_id` | 어떤 질의문으로 검색했는지 | 전시/갤러리/옥션 문맥 구분 |
| `rank` | 검색 결과 순위 | 상위 노출 강도 |
| `title`, `snippet` | 제목과 요약문 | 미술 문맥, 동명이인 필터 |
| `url`, `domain` | 출처 URL과 도메인 | 갤러리/미술관/뉴스/옥션 도메인 분류 |
| `fetched_at` | 수집 시각 | 같은 시점 snapshot 재현 |

작가 단위로 변환한 검색 피처:

| 피처 | 계산 방법 | 해석 |
|---|---|---|
| `search_result_count` | `has_result=True`인 검색 결과 수 | 작가 정보량. 많을수록 정보가 풍부하지만, 동명이인 결과가 섞이면 오히려 위험 |
| `search_source_count` | 중복 제거한 출처 도메인 수 | 한 사이트에만 몰린 결과인지, 여러 출처에서 확인되는지 판단 |
| `source_group별 count/ratio` | 표준화된 결과의 `news`, `gallery_museum`, `market`, `exhibition`, `art_general`, `social_blog`, `other` 비율 | provider 일치도와 수동 검수 판단용 파생 집계. 모델 직접 입력은 별도 검증된 후보에서만 제한 사용 |
| `search_gallery_context_count` | 갤러리/미술관 문맥 결과 수 | 미술계 활동성, 전시 이력, 작가 검증 신호 |
| `search_market_context_count` | 옥션/마켓 문맥 결과 수 | 거래시장 노출 신호. 가격점 직접 반영보다 Cold 보조 신호로 사용 |
| `search_exhibition_context_count` | 전시 문맥 결과 수 | 최근 활동성, 기관/전시 노출 신호 |
| `search_art_context_count` | 제목/요약/URL에 미술 문맥 키워드가 포함된 결과 수 | 검색 결과가 실제 미술 작가 문맥인지 확인 |
| `search_homonym_risk_ratio` | 동명이인 위험 결과 비율 | 검색 피처 사용 제한 기준. 높으면 신뢰도 하향 또는 수동 검수 |
| `search_quality_score` | 미술 문맥, 신뢰 도메인, 전시/시장 문맥, provider 커버리지, 작가명 일치, 동명이인 위험을 합산 | 검색 결과를 모델 피처로 써도 되는지 판단하는 종합 점수 |
| `search_quality_grade` | `high`/`medium`/`low`/`missing` 등급 | `high/medium`은 제한적 피처 후보, `low/missing`은 신뢰도/검수 flag 중심 |
| `provider_agreement_score` | Naver 공식 API와 Python/DDG 결과의 source group, 문맥, 도메인 유사도 비교 | 두 검색 경로가 같은 작가 문맥을 주는지 확인 |
| `provider_disagreement_risk_flag` | provider 일치도가 낮거나 동명이인 위험이 큰 경우 True | 가격점 예측 직접 반영 제한, 수동 검수 또는 신뢰도 하향 |
| `recommended_action` | `candidate_for_h14_h18`, `manual_review_required`, `confidence_only_or_manual_review`, `do_not_use_for_point_prediction` | 운영 적용/검수 기준 |

검색 품질 점수 산식:

```text
search_quality_score =
    0.30 * 미술 문맥 비율
  + 0.20 * 신뢰 도메인 비율
  + 0.15 * 전시 문맥 비율
  + 0.15 * 시장/옥션 문맥 비율
  + 0.10 * 최근 결과 비율
  + 0.10 * provider 커버리지
  + 0.10 * 작가명 일치 비율
  - 0.30 * 동명이인 위험 비율

최종 점수는 0~1 사이로 제한
```

검색 품질 등급 기준:

| 등급 | 기준 | 의미 |
|---|---|---|
| `high` | 점수 0.70 이상, 동명이인 위험 0.20 미만 | 모델 피처 또는 보정 조건 후보로 사용 가능 |
| `medium` | 점수 0.45 이상, 동명이인 위험 0.40 미만 | 제한 조건을 걸어 보조 피처로 사용 가능 |
| `low` | 위 조건을 만족하지 않음 | 가격점 예측 직접 반영보다 신뢰도 하향/검수 대상으로 사용 |
| `missing` | 유효 검색 결과가 없거나 점수가 0에 가까움 | 검색 피처 미사용 |

provider 일치도 산식:

```text
provider_agreement_score =
    0.35 * source group 유사도
  + 0.25 * 미술/전시/갤러리/시장 문맥 유사도
  + 0.15 * 결과 수 균형
  + 0.15 * 도메인 겹침 비율
  + 0.10 * 동명이인 안전도
```

provider 일치도 비교 방식:

- 비교 대상: Naver 공식 API 계열과 Python/DDG 검색 계열
- Google Custom Search는 현재 provider 일치도 계산 대상이 아님
- `high`: 0.70 이상. 두 경로가 비슷한 작가 문맥을 반환
- `medium`: 0.50 이상. 제한적으로 참고 가능
- `low`: 0.50 미만. 검색 경로별 결과가 달라 오염 가능성이 큼
- 위험 flag: 일치도 0.50 미만, 동명이인 안전도 0.80 미만, 문맥 유사도 0.65 미만 중 하나라도 해당

Cold 모델에 넣는 방식:

```text
1. 검색 원본 결과를 먼저 저장
2. 원본 결과를 작가 단위 피처로 집계
3. 고정된 split과 같은 수집 snapshot 기준으로 train/validation/test에 조인
4. validation에서 검색 피처 사용 여부와 보정 조건 선택
5. test는 선택된 조건만 1회 확인
6. 서비스에서는 실시간 검색값이 아니라 캐시된 작가 검색 피처 DB를 사용
```

검색 피처를 비교하는 기준:

| 비교 항목 | 보는 이유 | 실제 판단 방식 |
|---|---|---|
| 검색 결과 수 | 작가에 대한 공개 정보량 확인 | 단독으로 크면 좋은 값이 아님. 미술 문맥 비율과 동명이인 위험을 같이 봄 |
| 뉴스 source 수 | 대중/언론 노출 확인 | 미술 문맥이 약한 뉴스만 많으면 가격 피처보다 검수 flag로 사용 |
| 갤러리/미술관 source 수 | 미술계 활동성과 검증 신호 확인 | Cold에서 작가 이력 부족을 보완하는 후보 피처 |
| 옥션/마켓 source 수 | 시장 거래 노출 확인 | 가격 직접 보정이 아니라 거래 노출이 있는 작가인지 확인 |
| 검색 품질 등급 | 결과가 실제 작가/미술 문맥인지 판단 | `high/medium`만 제한적으로 모델 후보, `low`는 신뢰도 하향 |
| provider 일치도 | 검색 경로가 달라도 같은 결론이 나오는지 확인 | Naver와 Python/DDG가 비슷하면 신뢰도 상승, 다르면 수동 검수 |
| 수동 검수 필요 여부 | 잘못된 작가 정보가 모델에 들어가는 것을 방지 | 동명이인, 낮은 작가명 일치, 약한 미술 문맥, 낮은 provider 일치도일 때 검수 |

수동 검수 action 기준:

| action | 기준 | 사용 방식 |
|---|---|---|
| `candidate_for_h14_h18` | 작가명 일치율 0.35 이상, 사용 가능 결과 비율 0.48 이상, 평균 confidence 0.42 이상 | 후속 검색 피처 실험 후보 |
| `confidence_only_or_manual_review` | 사용 가능 결과 비율 0.34 이상, 평균 confidence 0.28 이상이나 핵심 기준은 부족 | 가격점 예측보다 신뢰도/가격 범위 정책에 사용 |
| `manual_review_required` | 동명이인 위험 비율 0.20 이상 | 사람이 확인하기 전에는 모델 피처로 직접 사용하지 않음 |
| `do_not_use_for_point_prediction` | 위 기준을 만족하지 못해 작가/미술 문맥이 부족함 | 가격점 예측 피처에서 제외 |

운영에서 실시간 검색을 기본값으로 쓰지 않는 이유:

- 같은 질의어도 날짜와 검색 엔진 상태에 따라 결과가 달라질 수 있음
- 검색 결과에는 동명이인과 비미술 문맥이 섞일 수 있음
- 실시간 검색 실패가 바로 예측 실패로 이어질 수 있음
- 모델 학습 시점과 서비스 예측 시점의 검색 snapshot이 다르면 재현성이 약해짐

운영 권장 구조:

```text
정기 수집 배치
  -> 검색 결과 원본 저장
  -> 자동 품질 점수 계산
  -> low/review 대상 수동 검수
  -> artist_search_features 테이블 갱신
  -> 모델 재학습 또는 예측 API에서 캐시 피처 사용
```

외부 검색 피처의 실험상 판단:

- 검색/전시/갤러리 통합 후보인 `PP-Y2`는 Cold 보수적 기준선으로 사용
- 검색 피처는 MAPE/p95 방어 신호가 있으나 동명이인/품질 오염 위험 존재
- `PP-H22`, `PP-H27`, `PP-I7` 계열 결과를 보면 전체 적용보다 `qwidth`, `recommended_action`, 검색 품질 등급으로 제한 적용하는 쪽이 안전
- Google Custom Search는 현재 결과 해석과 최종 외부 검색 피처 스냅샷에 포함하지 않음
- 최종 방향: 검색 피처는 가격을 직접 확정하는 핵심 피처가 아니라 Cold 신뢰도, 검수 필요 여부, 위험 구간 보정의 보조 신호로 사용

### 8.3 Cold CatBoost 해석

CatBoost 구조 해석:

- 대칭 트리 구조 사용
- 같은 깊이에서는 같은 분기 조건을 전체 샘플에 적용
- 단일 피처 하나보다 피처 조합을 규칙적으로 나누는 데 강점

```text
depth 1: 같은 split 조건으로 전체 샘플 1차 분리
depth 2: 같은 split 조건으로 다시 분리
depth 3: 같은 방식 반복
```

이 구조의 의미:

- 피처 하나가 독립적으로 가격을 결정한다고 보기 어려움
- 반복 split과 피처 조합이 가격 구간 형성
- CatBoost 해석 기준: `크기 x 깊이 x 재료/형태` 조합

Cold CatBoost에 적합했던 피처:

| 피처 | 이유 |
|---|---|
| `medium_shape_bucket` | 매체와 형태 조합을 대칭 트리 split에서 안정적으로 사용 |
| `shape_bucket` | 세로형/가로형/정방형 등 형태 구간 분기에 기여 |
| `depth_cm`, `has_depth`, `is_3d_candidate` | 평면/입체 후보 가격 구간 분리에 필요 |
| `medium_category`, `support_category` | 작품 유형과 재료 조건 분리 |
| 작가 메타 범주 | Cold에서 부족한 작가 시장 정보 간접 보완 |

Cold CatBoost 단독 판단:

| 후보 설명 | MdAPE | MAPE | p95_APE | 판단 |
|---|---:|---:|---:|---|
| Cold CatBoost 기준선 범위 | 0.4808~0.4867 | 1.4803~1.4852 | 4.6329~5.9854 | 초기 기준선과 PP-SVC1 기준선 범위. 단독 대표로 약함 |
| 비교군 통계 피처를 넣은 Cold CatBoost | 0.4885 | 1.1445 | 3.4749 | MdAPE는 약하지만 MAPE/p95 방어 신호가 있음 |

해석:

- CatBoost: 조합 구간 분리에는 강점
- 한계: Cold의 작가 기준선 부족을 단독 해결하지 못함
- 적합한 역할: 단독 최종 모델보다 residual 보정, segment 보정, 범주형 조합 보조 모델

### 8.4 Cold LightGBM / LightGBM Quantile 해석

LightGBM 구조 해석:

- leaf-wise 트리 구조
- 오차를 가장 많이 줄일 수 있는 leaf를 우선 확장
- 특정 조건 구간을 세밀하게 나누는 데 강점

```text
일반 균형 트리: 모든 가지를 비슷하게 확장
LightGBM leaf-wise: 오차를 가장 많이 줄일 수 있는 leaf를 우선 확장
```

LightGBM Quantile 산출값:

- 가격 하나만 내는 방식이 아니라 q10, q50, q90 같은 분위수 예측 생성
- 중앙 가격과 가격 범위, 불확실성 판단에 활용

- q50: 중앙 가격 예측
- q10~q90: 모델이 보는 낮은 가격대부터 높은 가격대까지의 범위
- 범위가 넓을수록 해당 작품의 예측 불확실성 증가

Cold에서 중요한 불확실성 지표:

```text
quantile_width = q90_log - q10_log
price_range_ratio = exp(q90_log) / exp(q10_log)
```

해석:

- `quantile_width`: 로그 가격에서 q90과 q10 사이의 폭
- `price_range_ratio`: 실제 가격 단위에서 상단 범위가 하단 범위의 몇 배인지 표시
- 활용 목적: 가격 직접 예측보다 위험 구간, 신뢰도, 후처리 구간 결정

## 9. Cold 실험 흐름과 최종 판단

Cold 실험 흐름:

- Warm처럼 단일 최종 가격 모델로 끝내기 어려운 구조
- 그래도 단계별 피처 추가와 보정으로 성능 개선 확인

| 단계 설명 | 내부 추적 ID/후보명 | MdAPE | MAPE | p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| Cold 초기 기준선 | LightGBM baseline | 0.4909 | 1.4131 | 4.8212 | 작품 조건만으로는 한계 큼 |
| 작가 메타 추가 | `PP-W2 generated_all_meta_all` | 0.4497 | 1.1111 | 4.1587 | 작가 메타로 대표 정확도 개선 |
| 전시/갤러리 활동성 추가 | `PP-X3 LightGBM Quantile + 전시/갤러리` | 0.4451 | 1.1277 | 3.8935 | 활동성 피처가 MdAPE 개선에 기여 |
| 검색+전시/갤러리 통합 기준 후보 | `PP-Y2 lgbq_search_all_external_interaction` | 0.4421 | 1.0484 | 3.3537 | 현재 Cold 보수적 기준선 |
| 불확실성 폭 구간 보정 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 대표/평균/큰오차 균형 우수 |
| qwidth+q40/q50 차이 기반 segment 보정 | `PP-QR3 segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | 0.4175 | 1.0029 | 3.0018 | MdAPE 추가 개선, p95도 완화 |
| qwidth+LightGBM q40 guard 보정 | `PP-QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` | 0.4178 | 0.9640 | 2.5377 | MdAPE/MAPE/p95 균형 후보 |
| 큰 오차 방어 후보 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | 0.4438 | 1.1083 | 2.8025 | p95 방어 우수, 대표 정확도는 약함 |

`PP-Y18 qwidth_bin_oof_min30_cap0.25` 이름 해석:

| 구성 | 의미 |
|---|---|
| `qwidth_bin` | q90과 q10 사이의 폭을 작음/중간/큼 같은 구간으로 분리 |
| `oof` | 교차검증 예측값으로 보정값 계산, 과적합 완화 |
| `min30` | 같은 구간에 최소 30개 샘플이 있을 때만 보정 |
| `cap0.25` | 로그 보정값이 너무 커지지 않게 ±0.25로 제한 |

PP-Y18 내부 후보 구분:

- `qwidth_bin_oof_min30_cap0.25`: 세 지표 균형이 좋은 Cold 검증 기준 후보
- `external_x_qwidth_oof_min30_cap0.25`: MdAPE는 `0.4239`로 더 낮지만 p95 개선과 운영 안정성은 제한적
- 최종 서비스 설명에서는 `qwidth_bin`을 중심 후보로 두고, `external_x_qwidth`는 참고 후보로 분리

PP-QR3 추가 검증의 의미:

- PP-QR1에서 만든 q40/q50 분위수 예측을 기존 PP-Y18 후보와 결합
- q40/q50 단독 모델을 최종 후보로 쓰는 것이 아니라, 기존 예측값과 q40/q50 예측값의 차이를 반복 오차 보정 신호로 사용
- validation 내부 row 5-fold와 artist 5-fold로 후보를 다시 고른 뒤 test에서 확인
- Ridge residual meta처럼 다시 학습하는 복잡한 meta 후보는 holdout에서는 좋아 보였지만 test에서 악화
- qwidth+pred_gap을 제한적으로 쓰는 guard/segment 보정만 Cold 추가 개선 후보로 유지

PP-QR3 보정 구조 도표:

```text
기존 Cold 기준 후보
  - PP-Y18 qwidth_bin 예측값
        |
        v
분위수 보조 예측
  - LightGBM/CatBoost q40, q50
        |
        v
차이 계산
  - pred_gap = 기존 예측값 - q40/q50 예측값
  - qwidth = q90 - q10
        |
        v
제한 보정
  - qwidth가 큰 구간
  - pred_gap이 큰 구간
  - 최소 표본 수와 cap 적용
        |
        v
최종 Cold 후보
  - segment 보정: MdAPE 개선
  - guard 보정: MAPE/p95 방어
```

Cold 최종 후보군:

| 목적 | 사람이 읽는 후보명 | 내부 후보명 | 판단 |
|---|---|---|---|
| 보수적 기준선 | 검색/전시/갤러리 통합 LightGBM Quantile | `PP-Y2 lgbq_search_all_external_interaction` | 구조와 설명이 비교적 명확 |
| 대표 개선 후보 | 불확실성 폭 구간 보정 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` | MdAPE/MAPE/p95 균형 우수 |
| 추가 개선 후보 | qwidth+q40/q50 차이 기반 segment 보정 | `PP-QR3 segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | MdAPE `0.4175`, p95도 기존보다 완화 |
| MAPE/p95 방어 후보 | qwidth+LightGBM q40 guard 보정 | `PP-QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` | MdAPE `0.4178`, MAPE `0.9640`, p95 `2.5377` |
| MdAPE 최고 참고 | 외부 피처와 불확실성 구간을 함께 본 보정 후보 | `PP-Y18 external_x_qwidth_oof_min30_cap0.25` | MdAPE `0.4239`, p95 개선은 제한적 |
| 큰 오차 방어 | 예측값 구간과 불확실성 구간 결합 보정 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | Y계열 기존 후보 중 p95 방어가 강했지만, PP-QR3 guard 후보가 p95를 더 낮춤 |
| 검색 제한 보정 | 뉴스/갤러리 조건부 보정 | `PP-I7` news/gallery 조건 보정 | 개선 신호는 있으나 OOF와 다른 split 재검증 필요 |

Cold 보정 후보 안정성:

| 검증 설명 | 내부 추적 ID | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |
|---|---|---:|---:|---:|
| row bootstrap 안정성 | `PP-Y18` | 0.9938 | 1.0000 | 0.9988 |
| artist bootstrap 안정성 | `PP-Y18` | 0.8488 | 0.9988 | 0.9513 |
| artist holdout 안정성 | `PP-Y21` | 0.8625 | 0.9875 | 0.9625 |
| OOF/holdout meta 검증 | `PP-QR3 Ridge residual meta` | holdout 0.9000 | holdout 0.6000 | holdout 0.7000 |

PP-QR3 안정성 해석:

- Ridge residual meta는 holdout MdAPE 개선확률이 높았지만 test MdAPE가 `0.4345`로 기존 PP-Y18보다 악화
- 따라서 복잡한 meta 보정은 보류
- qwidth+pred_gap guard/segment 보정은 test 개선 신호가 남아 있으나, 최종 교체 전에는 split 재학습 검증 필요

주의:

- Cold 개선 신호 존재
- Warm처럼 단일 점 예측 가격으로 확정하기에는 부족
- 서비스 제공 방식: “확정 예측 가격”이 아니라 “참고 예측가 + 넓은 가격 범위 + 낮은 신뢰도”

## 10. 모델 특성에 맞춘 커스텀/보정 방식

| 모델/후보 | 구조적 특성 | 사용한 커스텀 | 이유 |
|---|---|---|---|
| Warm Huber | 선형, 이상치 강건 | 비교군 통계 피처 추가 | 작가/크기 중심선에 시장 비교군 정보 추가 |
| Warm 비교군 통계 + compact blend | 두 후보의 강점이 다름 | 로그 예측 70:30 결합 | 비교군 통계 후보의 MdAPE 장점과 compact blend의 MAPE/p95 방어 결합 |
| Warm CatBoost residual | 비선형 조합 학습 가능 | residual 보조 후보 | PP-V6 대비 p95/MAPE 방어 신호는 있으나 PP-V8 대비 MAPE 우위가 약하고 MdAPE 악화로 보류 |
| Cold CatBoost | 대칭 트리, 조합 분기 | leaf/segment residual 후보 | 단일 피처보다 조건 조합별 반복 오차 보정에 적합 |
| Cold LightGBM Quantile | leaf-wise, q10/q50/q90 산출 | qwidth bin 보정 | 불확실성이 큰 구간의 반복 오차 단순 보정 |
| Cold qwidth+pred_gap 보정 | Quantile width와 q40/q50 차이를 함께 사용 | guard/segment 제한 보정 | 불확실성이 크고 q40/q50과 기존 예측이 크게 어긋나는 구간만 보정 |
| Cold meta residual | 예측값을 다시 학습하는 2단계 모델 | Ridge/Huber/QuantileRegressor residual meta | holdout에서는 좋아 보였지만 test 재현 실패로 보류 |
| Huber residual 보정 | 큰 residual 과추종 방지 | segment median residual + cap | 큰 오차 보정값의 과도한 확대 방지 |
| 외부 검색/갤러리 보정 | 데이터 품질 변동 큼 | qwidth/recommended_action 조건 제한 | 검색 오염과 동명이인 위험으로 전체 적용 보류 |

### 10.1 표준 보정식

후처리 보정의 기본 구조:

```text
residual_log = actual_log - pred_log
segment_correction = median(residual_log in same segment)
corrected_pred_log = pred_log + clipped(segment_correction)
corrected_price = exp(corrected_pred_log)
```

해석:

- `residual_log`: 모델이 반복적으로 높게 또는 낮게 예측한 방향
- `median`: 중앙값. 오차들을 작은 순서부터 큰 순서로 정렬했을 때 가운데 있는 값
- median 사용 이유: 평균보다 이상치에 덜 민감해 가격 데이터 보정에 적합
- `segment`: 보정값을 계산할 같은 조건의 그룹
- `clipped`: 보정값이 너무 커지지 않게 상한/하한을 자르는 처리

모델별 segment 설정:

| 모델 | 적합한 보정 segment |
|---|---|
| Warm Huber | 전체 residual, 작가 이력, 비교군 통계 coverage |
| Cold CatBoost | leaf, `medium_shape_bucket`, 재료/형태/깊이 조합 |
| Cold LightGBM Quantile | `pred_bin`, `qwidth_bin`, `support_size_bucket` |

### 10.2 왜 Warm은 단순 결합이 좋았는가

Warm 결합 방식 판단:

- 복잡한 leaf 라우팅보다 단순 가중 결합이 더 안정적

이유:

- Warm의 주된 정보: 작가 기준선과 크기
- Huber 역할: 작가/크기 중심선 안정화
- 비교군 통계 후보 강점: 대표 정확도
- 기존 compact blend 후보 강점: 평균오차와 tail 방어
- 결합 의미: 서로 다른 약점 보완

안정적이었던 결합:

```text
비교군 숫자 통계 후보 70% + 기존 compact blend 후보 30%
```

### 10.3 왜 Cold는 조건부 정책이 필요한가

Cold 조건부 정책이 필요한 이유:

- 작가 기준선 부족
- 특정 피처 조합이 항상 같은 효과를 내지 않는 구조

예를 들어:

- 전시/갤러리 피처: LightGBM Quantile에서는 MdAPE 개선에 기여
- CatBoost 적용 시: 조합 방식에 따라 악화 사례 존재
- 검색 피처: MAPE/p95 개선 신호와 동명이인/검색 품질 오염 위험 공존
- qwidth 큰 구간: 모델이 스스로 불확실하다고 본 구간, 가격 범위와 신뢰도 정책 연결 필요

Cold 권장 구조:

```text
대표 점 예측 후보
+ qwidth 기반 위험 구간 보정
+ 가격 범위 산출
+ 신뢰도 하향/수동 검수 flag
```

## 11. 피처 영향도를 어떻게 해석했는가

모델별 피처 영향도 해석 기준:

| 모델 | 해석 기준 | 이유 |
|---|---|---|
| Warm Huber | 계수, 실제 기여도, group-drop | 선형 모델이므로 피처별 방향과 기여도 해석 가능 |
| Cold CatBoost | SHAP, interaction, leaf/segment | 대칭 트리라 단일 피처보다 조합 효과가 중요 |
| Cold LightGBM | permutation, split importance, tail slice | leaf-wise 구조라 특정 구간 tail risk가 중요 |

이 문서의 피처 영향 판단 기준:

- 성능 개선 사실만으로 피처 원인 단정하지 않음
- 피처 제거 시 성능 악화 폭 확인
- 트리 모델은 feature importance만 보지 않고 조합, segment, tail 동시 확인
- 서비스 피처는 성능뿐 아니라 운영 생성 안정성도 판단 기준에 포함
- 외부 검색 피처는 실시간 사용보다 캐시, 검수, 신뢰도 flag 중심 사용 권장

## 12. 서비스 적용 판단

| 항목 | 적용 판단 |
|---|---|
| Warm 예측값 | `warm_pp_svc3_svcnum_ppv8_070`으로 서비스 1순위 적용 |
| Warm 표시 | 예측 가격 + 가격 범위 + 비교군 통계 |
| Cold 예측값 | 참고 예측가로 표시 |
| Cold 표시 | 넓은 가격 범위 + 낮은 신뢰도 + 비교군 통계 |
| 비교군 통계 | 비교군 중앙값, 범위, 매체별 분포, 표본 수 N을 API 응답에 포함 |
| 호당가 통계 | 기존 `estimated_ho` 호수 산출식 기준으로 API 응답에 포함 |
| 외부 검색 | 실시간 기본값 비활성화, 캐시/수동 검수 기반 권장 |
| 모델 정보 | API 응답에 `model_policy`, `postprocessing_policy`, `routing_reason` 포함 |

서비스 제공 비교군 통계 예시:

| 서비스 표시값 | 계산 의미 |
|---|---|
| 비교군 가격 중앙값 | 같은 비교군 표본들의 가격 median |
| 비교군 가격 범위 | 같은 비교군 표본들의 분위 범위 |
| 매체별 분포 | 매체별로 나눈 비교군 가격 또는 단가 median |
| 호당가 중앙값 | 기존 `estimated_ho` 호수 산출식 기준, 같은 비교군 표본들의 호당가 median |
| 표본 수 N | 비교군에 포함된 유효 표본 수 |

## 13. 남은 리스크와 다음 작업

| 리스크 | 이유 | 다음 작업 |
|---|---|---|
| Warm 산출물 재현성 | Warm 최종 결합은 저장된 예측 산출물 결합으로 검증 | 비교군 통계 후보와 compact blend 후보를 운영 산출물에서 다시 만들 수 있는지 간단 재현 테스트 필요 |
| 호당가 예외 정책 | PP-SVC1 일부 split은 면적 단가를 대체 사용 | 서비스에서는 기존 `estimated_ho` 호수 산출식을 쓰되, 3D/비표준 작품 표시 기준 필요 |
| Cold 단일 가격 오해 | Cold p95와 구성 변동성 큼 | 참고 예측가, 범위, 신뢰도 중심 화면 정책 적용 필요 |
| 외부 검색 품질 | 동명이인, 검색 provider 불일치 가능성 | 실시간보다 캐시, 검수, 신뢰도 flag로 사용 |
| 비교군 표본 부족 | 세부 segment에서 N 부족 가능성 | fallback 순서와 최소 N 기준 확정 |

## 14. 최종 보고 문장

- Warm: Huber의 작가/크기 중심선 강점 확인, 비교군 통계 피처 추가 후 대표 오차 크게 개선
- Warm 최종 결합: 비교군 통계 후보는 MdAPE 강점, 기존 compact blend 후보는 MAPE 방어 강점, 로그 가격 70:30 결합
- Warm 안정성: 반복 holdout 검증에서 MAPE 방어 기준으로 안정적 재선택
- Cold: 작가 기준선 부족, 작품 조건·작가 메타·전시/갤러리·검색 피처 동시 활용 필요
- Cold 서비스 방향: LightGBM Quantile과 qwidth 기반 보정 중심, 참고 예측가·넓은 가격 범위·낮은 신뢰도 표시 필요
- 모델 선정 기준: 가장 낮은 test 지표 하나가 아니라 모델 구조에 맞는 피처 해석과 반복 검증에서 재현되는 조합
