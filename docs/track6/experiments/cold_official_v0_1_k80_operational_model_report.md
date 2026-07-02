# Cold official 0.1v k80 운영 모델 설명서

- 작성일: 2026-06-22
- 문서 목적: Cold 가격 예측 운영 기준안을 `k80 보수적 운영` 후보로 고정하고, 모델의 목적, 입력, 학습/검증 흐름, 사용 단계, 성능, 운영 주의사항을 한 문서에서 설명한다.
- 기준 후보: `resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05`
- 기준 실험: `PP-CSIM24`, `PP-CSIM25`, `PP-CSIM26`
- 기준 버전 표기: official 0.1v

## 1. 운영 결론

Cold 운영 모델은 같은 작가 가격 이력을 직접 사용할 수 없는 경우에 쓰는 가격 예측 경로다. 따라서 입력 작가를 내부 `artist_key`에 매칭한 뒤 같은 작가의 과거 가격을 가져오면 안 된다. 이번 기준안은 이 조건을 지키기 위해 `artist_key`, 동일 작가 가격 이력, 검색 캐시, 외부 live 검색, artist_key 기반 lookup 후처리를 쓰지 않는다.

현재 운영 기준안은 `k80 보수적 운영` 후보로 둔다. 이 후보는 validation에서 가장 안정적으로 우세했고, test에서도 base 대비 MAPE, p95 APE, APE > 5를 모두 줄였다. test 성능만 보면 k40 후보가 더 좋지만, validation과 test에서 우위가 바뀌었기 때문에 운영 기준안은 validation 선택 논리가 더 방어 가능한 k80 후보로 둔다.

| 후보 | split | MdAPE | MAPE | p95 APE | APE > 5 | 선택 비율 |
|---|---|---:|---:|---:|---:|---:|
| base | validation | 0.424537 | 0.606746 | 1.808312 | 10 | 0.00% |
| k80 보수적 운영 | validation | 0.404411 | 0.565875 | 1.638585 | 8 | 52.85% |
| base | test | 0.481850 | 0.746296 | 2.398009 | 35 | 0.00% |
| k80 보수적 운영 | test | 0.479052 | 0.720187 | 2.231840 | 33 | 46.10% |

해석은 다음과 같다.

- validation: k80 후보가 base보다 MdAPE, MAPE, p95 APE, APE > 5 모두 개선됐다.
- test: k80 후보도 base보다 개선된다. MAPE는 `0.746296 -> 0.720187`, p95 APE는 `2.398009 -> 2.231840`, APE > 5는 `35 -> 33`으로 줄었다.
- k40 후보는 test에서 더 좋지만, validation에서는 k80보다 약하다. 운영 모델 설명과 배포 기준은 검증셋 선택 논리가 더 명확한 k80을 우선한다.

## 2. Cold 모델의 역할

Cold는 “같은 작가 가격 이력을 직접 쓸 수 없는 입력”을 위한 모델이다. Warm은 같은 작가의 과거 거래/판매 가격 통계를 기준가격으로 사용할 수 있지만, Cold는 그럴 수 없다. 그래서 Cold는 아래 정보를 이용해 가격을 예측한다.

| 정보 그룹 | 사용 여부 | 설명 |
|---|---|---|
| 작품 크기/형태 | 사용 | 가로, 세로, 깊이, 면적, 로그면적, 비율, 입체 여부 |
| 작품 조건 | 사용 | 매체, 지지체, 매체+지지체 조합 |
| 사용자 입력 가능 작가 메타 | 사용 | 출생연도, 경력단계, 국적 등 비가격성 작가 정보 |
| 유사 이웃 통계 | 사용 | 비슷한 작품/작가 메타를 가진 학습 데이터의 예측 잔차 경향 |
| 입력 작가의 artist_key | 미사용 | Cold에서는 입력 작가를 내부 artist_key에 매칭해 가격 이력을 가져오지 않음 |
| 같은 작가 가격 이력 | 미사용 | Warm 전용 정보이므로 Cold에서는 금지 |
| 검색 캐시/live 검색 | 미사용 | 운영 안정성과 재현성을 위해 이번 기준안에서는 제외 |

여기서 중요한 점은 “작가 메타를 쓴다”와 “artist_key로 같은 작가 가격 이력을 쓴다”는 서로 다르다는 점이다. Cold에서 허용되는 작가 메타는 사용자가 입력할 수 있거나 운영에서 독립적으로 검수 가능한 비가격성 정보다. 반대로 `artist_key`로 과거 가격을 조회하는 순간 Cold가 아니라 Warm 방식이 된다.

## 3. 모델 이름과 구성 요소

기준 후보명은 다음과 같다.

```text
resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05
```

각 부분의 의미는 다음과 같다.

| 이름 부분 | 의미 |
|---|---|
| `resid` | 기준 예측값에서 남은 오차, 즉 residual을 보정에 사용 |
| `artist_meta` | 유사 이웃을 찾을 때 작가 메타 기반 유사도를 사용 |
| `k80` | 예측 대상과 유사한 학습 데이터 80건을 참고 |
| `s1p0` | 이웃 잔차 중앙값을 1.0배로 반영 |
| `cap0p25` | 보정값은 최대 ±0.25 log 안으로 제한 |
| `route_neg_corr_ge_0p05` | 하향 보정값이 0.05 log 이상일 때만 보정 후보를 선택 |

`k80`은 “가장 비슷한 이웃 80건”이라는 뜻이다. k가 작으면 가까운 사례만 보므로 민감하고, k가 크면 더 넓은 사례를 보므로 안정적이다. 이번 검증에서는 k40이 test에서 더 강했지만, k80이 validation에서 더 안정적이었다.

## 4. 학습/검증 단계

Cold k80 운영 기준안은 한 번에 만든 단일 모델이 아니라, 여러 단계의 후보를 검증하면서 선택한 운영 규칙이다. 핵심 흐름은 다음과 같다.

```text
[학습 데이터 준비]
  - 가격 라벨이 있는 과거 작품
  - 작품 크기/매체/지지체 피처
  - 사용자가 입력 가능하거나 운영 검수 가능한 작가 메타
  - artist_key는 식별/분리 관리용으로만 존재할 수 있으나 모델 피처로 쓰지 않음
        |
        v
[base Cold 모델 학습]
  - LightGBM Quantile 기반 기준 예측
  - 작품 피처 + 사용자 입력 가능 작가 메타 + 유사 작품 통계 사용
  - 같은 작가 가격 이력은 사용하지 않음
        |
        v
[OOF 잔차 생성]
  - train 내부에서 fold를 나눔
  - 각 hold-out row는 자신을 학습하지 않은 모델의 예측값을 받음
  - residual = 실제 로그가격 - OOF 예측 로그가격
        |
        v
[유사 이웃 잔차 후보 생성]
  - 예측 대상과 작가 메타가 비슷한 train 이웃 80건을 찾음
  - 그 이웃들의 OOF residual 중앙값을 계산
  - 보정 후보 = base 예측 + clip(1.0 * 이웃 residual 중앙값, -0.25, +0.25)
        |
        v
[규칙 라우터 검증]
  - 모든 row에 보정을 적용하지 않음
  - 하향 보정값이 0.05 log 이상일 때만 보정 후보를 선택
  - 그 외에는 base 예측 유지
        |
        v
[운영 후보 선택]
  - validation 안정성 우선
  - test에서 base 대비 개선 유지 확인
  - strict Cold 조건 통과 여부 확인
```

OOF는 out-of-fold의 약자다. 쉽게 말하면 “각 학습 row를 직접 학습한 모델로 다시 맞히지 않고, 그 row를 잠시 빼고 만든 예측값으로 잔차를 계산한다”는 뜻이다. 이렇게 해야 train 내부에서도 자기 가격을 본 예측값이 보정 통계에 섞이지 않는다.

## 5. 사용 단계

운영에서 Cold 입력이 들어오면 다음 순서로 계산한다.

```text
[Cold 입력]
  - 작품 크기: width_cm, height_cm, depth_cm
  - 작품 조건: medium_category, support_category
  - 작가 메타: 출생연도, 경력단계, 국적 등 입력 가능한 비가격 정보
  - 같은 작가 가격 이력은 없음
        |
        v
[기본 피처 생성]
  - area_cm2 = width_cm * height_cm
  - log_area = log(area_cm2)
  - aspect_ratio = width_cm / height_cm
  - has_depth, is_3d_candidate
  - size_bucket, medium_support_bucket 등 구간 피처
        |
        v
[base Cold 예측]
  - 작품 피처와 작가 메타를 모델에 입력
  - base_pred_log 생성
        |
        v
[유사 이웃 80건 찾기]
  - artist_key가 아니라 작가 메타/작품 조건 유사도 기준으로 찾음
  - train reference pool에서 가장 비슷한 80건 선택
        |
        v
[이웃 잔차 중앙값 계산]
  - 선택된 80건의 OOF residual 중앙값 계산
  - residual_median_log 생성
        |
        v
[보정 후보 계산]
  - correction_log = clip(1.0 * residual_median_log, -0.25, +0.25)
  - corrected_pred_log = base_pred_log + correction_log
        |
        v
[라우터 선택]
  - correction_log <= -0.05이면 corrected_pred_log 사용
  - 그 외에는 base_pred_log 유지
        |
        v
[최종 가격]
  - final_price = exp(final_pred_log)
```

라우터가 하향 보정만 적용하는 이유는 Cold에서 큰 오차가 주로 과대 예측 구간에서 문제가 되었기 때문이다. 이 후보는 “비슷한 이웃들이 base보다 낮아져야 한다는 신호를 줄 때만” 보수적으로 가격을 낮춘다. 상향 보정이나 작은 보정은 운영 기준안에서는 적용하지 않는다.

## 6. 계산 예시

아래 숫자는 계산 흐름을 설명하기 위한 예시다.

```text
[입력]
  width_cm = 60
  height_cm = 72
  depth_cm = 0
  medium_category = painting
  support_category = canvas
  artist_meta_birth_year = 1981
  artist_meta_career_stage = 15

[base Cold 예측]
  base_pred_log = 15.40
  base_price = exp(15.40) = 약 4,872,000원

[유사 이웃 80건]
  artist_meta/작품 조건이 비슷한 train 이웃 80건 선택
  이웃들의 OOF residual 중앙값 = -0.08 log

[보정 후보]
  correction_log = clip(1.0 * -0.08, -0.25, +0.25)
                 = -0.08
  corrected_pred_log = 15.40 + (-0.08)
                     = 15.32
  corrected_price = exp(15.32) = 약 4,500,000원

[라우터]
  correction_log = -0.08
  -0.08 <= -0.05 이므로 하향 보정 신호가 충분함
  최종 로그가격 = corrected_pred_log = 15.32
  최종 가격 = 약 4,500,000원
```

반대로 이웃 잔차 중앙값이 `-0.02 log`라면 보정값이 너무 작으므로 base 예측을 유지한다. 이 경우 최종 로그가격은 `15.40`이다.

## 7. 성능 비교

### 7.1 base 대비 k80 운영 기준안

| 후보 | split | MdAPE | MAPE | p95 APE | APE > 2 | APE > 5 | APE > 10 |
|---|---|---:|---:|---:|---:|---:|---:|
| base | validation | 0.424537 | 0.606746 | 1.808312 | 97 | 10 | 1 |
| k80 보수적 운영 | validation | 0.404411 | 0.565875 | 1.638585 | 77 | 8 | 1 |
| base | test | 0.481850 | 0.746296 | 2.398009 | 212 | 35 | 8 |
| k80 보수적 운영 | test | 0.479052 | 0.720187 | 2.231840 | 200 | 33 | 8 |

### 7.2 k40 후보와의 비교

| 후보 | split | MdAPE | MAPE | p95 APE | APE > 5 | 선택 비율 |
|---|---|---:|---:|---:|---:|---:|
| k40 성능 우선 | validation | 0.414052 | 0.591879 | 1.771392 | 8 | 28.35% |
| k80 보수적 운영 | validation | 0.404411 | 0.565875 | 1.638585 | 8 | 52.85% |
| k40 성능 우선 | test | 0.474181 | 0.711229 | 2.161091 | 30 | 25.67% |
| k80 보수적 운영 | test | 0.479052 | 0.720187 | 2.231840 | 33 | 46.10% |

k40은 test에서 더 좋다. 그러나 validation에서는 k80이 더 강하다. 운영 모델은 test 최상위 하나를 고르는 것보다 validation에서 선택된 규칙이 test에서도 개선을 유지하는지가 중요하므로, 현재 기준안은 k80으로 둔다.

### 7.3 paired bootstrap 요약

`PP-CSIM26`에서 base와 paired bootstrap을 수행했다. k80 후보는 validation에서 base 대비 MdAPE, MAPE, p95 APE가 모두 안정적으로 개선됐다. test에서도 MAPE와 p95 APE는 안정적으로 개선됐고, MdAPE 개선은 작지만 방향은 개선이다.

| 비교 | split | delta MdAPE | delta MAPE | delta p95 APE |
|---|---|---:|---:|---:|
| k80 운영 후보 - base | validation | -0.020488 | -0.040809 | -0.157453 |
| k80 운영 후보 - base | test | -0.001118 | -0.026117 | -0.132280 |

음수는 후보가 base보다 낮은 오차를 냈다는 뜻이다.

## 8. strict Cold 조건 확인

`PP-CSIM26` run summary 기준 strict Cold 조건은 다음과 같이 기록되어 있다.

| 항목 | 값 | 의미 |
|---|---:|---|
| `strict_cold_compliant` | 1 | strict Cold 조건 충족 |
| `uses_search_features` | 0 | 검색 피처 미사용 |
| `uses_external_live_search` | 0 | 외부 live 검색 미사용 |
| `uses_artist_key_lookup_postprocess` | 0 | artist_key 기반 후처리 lookup 미사용 |
| `uses_rule_router` | 1 | 규칙 라우터 사용 |
| `router_uses_actual_price` | 0 | 라우터가 실제 가격을 보지 않음 |

주의할 점은 원본 데이터 안에 `artist_key` 컬럼이 존재할 수 있다는 것이다. 이것은 split 관리, 데이터 추적, Warm/Cold 구분을 위한 식별자일 수 있다. 하지만 이번 Cold 기준안에서는 `artist_key`를 모델 피처, 유사도 계산, 보정 lookup, 라우터 조건에 사용하지 않는다.

## 9. 운영 구현 시 필요한 산출물

현재 문서 기준 후보는 실험적으로 운영 기준안으로 정한 상태다. 실제 API 운영에 올리려면 Warm처럼 독립 번들로 구성해야 한다.

필요한 구성은 다음과 같다.

```text
models/track6/cold_k80_conservative_official_v0.1_candidate/
  artifacts/
    runtime_store.joblib
      - base Cold 모델
      - train reference pool
      - OOF residual 배열
      - 유사도 전처리기
      - size/shape bucket 규칙
      - feature schema
      - 라우터 정책
  config/
    cold_k80_conservative_policy_v0_1.json
  predict/
    predict_cold_k80_conservative_v0_1.py
  test_data/
    track6_test_cold.csv
  test_outputs/
    fixed_test/
      summary.json
      predictions.csv
      predictions_with_diagnostics.csv
  README.md
```

운영 predictor는 DB, 외부 CSV, 검색 API 없이 `runtime_store.joblib` 내부 산출물만으로 아래 값을 반환해야 한다.

| 반환값 | 설명 |
|---|---|
| `predicted_price` | 최종 예측 가격 |
| `predicted_log_price` | 최종 로그가격 |
| `route` | `base` 또는 `residual_correction` |
| `base_log_price` | base Cold 예측 로그가격 |
| `correction_log` | 적용된 보정값 |
| `neighbor_k` | 80 |
| `selected_neighbor_count` | 실제 참고한 이웃 수 |
| `strict_cold_compliant` | true |
| `diagnostics` | 유사도, 보정 여부, 입력 결측 상태 등 |

## 10. 운영 모니터링

Cold는 Warm보다 불확실성이 크다. 따라서 최종 가격만 저장하면 안 되고, 다음 진단값을 함께 저장해야 한다.

| 진단값 | 이유 |
|---|---|
| `route` | base를 썼는지 보정 후보를 썼는지 확인 |
| `correction_log` | 하향 보정이 얼마나 컸는지 확인 |
| `neighbor_k` | k80 정책이 적용됐는지 확인 |
| `neighbor_similarity_mean` | 이웃이 충분히 비슷했는지 확인 |
| `artist_meta_missing_count` | 작가 메타 입력 품질 확인 |
| `base_pred_price` | 보정 전 가격 확인 |
| `final_pred_price` | 최종 가격 확인 |
| `price_band` | 저가/중가/고가 구간별 성능 모니터링 |

운영 중 재학습이나 정책 변경을 할 때는 임계값과 k를 매번 재최적화하지 말고, 새 학습 데이터로 동일한 hold-out 검증과 parity 검증을 통과한 뒤 버전업해야 한다.

## 11. 현재 한계와 후속 작업

현재 k80 보수적 운영 기준안은 운영 후보로 설명 가능하지만, 아직 Warm joblib 번들처럼 완전 독립 배포 형태로 잠긴 것은 아니다.

남은 작업은 다음과 같다.

| 작업 | 필요성 |
|---|---|
| 독립 joblib runtime store 생성 | 실험 CSV 없이 API에서 재현 가능해야 함 |
| predictor 작성 | 입력 JSON/CSV에서 바로 Cold 예측 가능해야 함 |
| fixed test parity 검증 | 실험 산출값과 predictor 산출값 일치 확인 |
| API adapter 연결 | Warm/Cold 라우팅에서 Cold 경로로 연결 |
| 운영 로그 스키마 확정 | route, correction, neighbor 진단값 저장 |
| k40 후보 후속 검증 | test 성능 우위가 재현되는지 추가 split 또는 bootstrap 확장 |

따라서 현재 결론은 다음과 같다.

```text
Cold official 0.1v 운영 기준안:
  k80 보수적 운영 후보를 기준으로 문서화한다.

운영 적용 조건:
  독립 joblib bundle, predictor, fixed test parity, API 연결 검증을 완료한 뒤 배포한다.

후속 연구 후보:
  k40 성능 우선 후보는 별도 실험에서 재검증한다.
```
