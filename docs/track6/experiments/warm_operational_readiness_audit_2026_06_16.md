# Warm/Warm-lite 운영 확정 전 검증 감사

- 작성일: 2026-06-16
- 목적: Warm 계열 운영 모델 확정 전에 재현성, API parity, 수치 일관성, 남은 검증 필요 여부를 점검한다.
- 대상:
  - 현재 official 0.1v API Warm 경로: `5건 이상 -> Warm WMIN8`
  - 현재 official 0.1v API Warm-lite 경로: `1~4건 -> Warm-lite current`
  - 최근 권장안: `1건 이상 -> Warm-lite unified + route_gap_q50`

## 1. 결론

현재 0.1v API에 이미 연결된 Warm/Warm-lite 모델은 재현성 검증을 통과했다.

후속 검증으로 최근 리포트의 권장안인 `1건 이상 -> Warm-lite unified + route_gap_q50`도 후보 번들 동결, 실험 산출물 대비 replay parity, official 0.1v HTTP API parity를 통과했다. 이에 따라 기본 official 0.1v Warm 라우팅을 `route_gap_q50` 통합 Warm-lite 정책으로 승격했다. 기존 split 정책은 환경변수 `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split`로 되돌릴 수 있다.

완료된 항목:

1. Warm-lite unified/route_gap_q50 후보 번들 동결
2. 1건 이상 전체 이력 입력을 허용하는 predictor 구현
3. CF9 validation/test 1,126행 replay parity 통과
4. official 0.1v API adapter 연결
5. CF9 validation/test 1,126행 HTTP API parity 통과
6. 기본 라우팅 deterministic check 통과
7. 기본 정책을 `1건 이상 -> Warm-lite unified route_gap_q50`로 승격

남은 항목:

1. 1~4건 native/LOO 운영 영향 재확인
2. 발표자료와 외부 문서의 `current official 0.1v route` 표기 갱신

따라서 운영 결정은 두 선택지로 분리해야 한다.

| 선택지 | 상태 | 판단 |
|---|---|---|
| 이전 split 정책: 1~4건 Warm-lite current, 5건 이상 Warm WMIN8 | 재현성/parity 통과, env fallback 보존 | rollback 가능 |
| 현재 기본 정책: 1건 이상 Warm-lite unified + route_gap_q50 | 후보 번들 동결/replay/API parity 통과, 기본 정책 승격 | 운영 기본값 |

## 2. 현재 0.1v API 재현성 검증

### 2.1 Warm-lite current 번들 파일 무결성

명령:

```bash
shasum -c models/track6/warm_lite_quantile_residual_v0.1/manifest/MANIFEST.sha256
```

결과:

- `README.md`: OK
- `config/warm_lite_quantile_residual_params_v0_1.json`: OK
- `config/warm_lite_quantile_residual_policy_v0_1.json`: OK
- `manifest.json`: OK
- `models/lgbq_full_q10.joblib`: OK
- `models/lgbq_full_q50.joblib`: OK
- `models/lgbq_full_q90.joblib`: OK
- `models/lgbq_lean_q50.joblib`: OK
- `models/lightgbm_huber_residual.joblib`: OK
- `predict/predict_warm_lite_quantile_residual_v0_1.py`: OK
- `reports/warm_lite_quantile_residual_release_v0_1.md`: OK

판단: 동결 번들 파일은 manifest와 일치한다.

### 2.2 Warm-lite current replay parity

명령:

```bash
python3 scripts/track6/verify_warm_lite_quantile_residual_bundle_parity.py
```

결과:

| 항목 | 값 |
|---|---:|
| reference rows | 7,284 |
| replay rows | 7,284 |
| merged rows | 7,284 |
| max abs log diff | 3.552713678800501e-15 |
| mean abs log diff | 4.0848403432117237e-16 |
| passed | true |

판단: 동결 Warm-lite current 번들은 PP-WLITE-Q3 기준 예측을 사실상 완전 재현한다.

### 2.3 Warm-lite current HTTP API parity

명령:

```bash
python3 scripts/track6/verify_official_v0_1_warm_lite_quantile_residual_api_parity.py --max-cases 24
```

결과:

| 항목 | 값 |
|---|---:|
| cases | 24 |
| max abs log diff | 0.0 |
| price mismatch | 0 |
| route mismatch | 0 |
| adapter mismatch | 0 |
| passed | true |

판단: official 0.1v API의 Warm-lite endpoint 출력은 내부 adapter 계산과 일치한다.

### 2.4 official 0.1v 라우팅 deterministic check

명령:

```bash
python3 scripts/track6/verify_official_v0_1_warm_lite_api_routing.py --repeat 3
```

결과:

| case | expected | actual | deterministic |
|---|---|---|---|
| unknown artist | cold | cold | true |
| 1건 이력 | warm_lite | warm_lite | true |
| 4건 이력 | warm_lite | warm_lite | true |
| 5건 이상 | warm | warm | true |

판단: 현재 official 0.1v 라우팅은 반복 호출에서 안정적이다.

### 2.5 Warm WMIN8 HTTP API fixed-test parity

명령:

```bash
python3 scripts/track6/run_pp_wmin10_warm_wmin8_api_fixed_test_parity.py --no-resume
```

결과:

| 항목 | 값 |
|---|---:|
| total rows | 607 |
| success rows | 607 |
| error rows | 0 |
| wrong route | 0 |
| wrong adapter | 0 |
| max abs log diff | 5.3290705182007506e-15 |
| p95 abs log diff | 3.552713678800501e-15 |
| price diff pct max | 0.0 |

판단: official 0.1v API의 Warm WMIN8 endpoint 출력은 PP-WMIN8 실험 산출물과 row-level로 일치한다.

## 3. 최근 권장안 성능 근거

최근 권장안은 다음 구조다.

```text
if same_artist_history_n == 0:
    Cold
else:
    if abs(q50_full_log - q50_lean_log) >= 0.0252975:
        Warm-lite CF7 tail guard
    else:
        Warm-lite current
```

### 3.1 fixed-test 607행 동일 조건 비교

출처: `PP-ROUTE-CF9_conditional_cf7_router`

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| Warm WMIN8 operational | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| Warm-lite current | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |
| Warm-lite CF7 all | 607 | 0.089227 | 0.223920 | 0.745513 | 0.379962 |
| route_gap_q50 | 607 | 0.086405 | 0.223590 | 0.758056 | 0.380030 |

해석:

- route_gap_q50은 Warm WMIN8보다 MdAPE/MAPE가 좋다.
- Warm WMIN8은 p95/RMSE가 아직 더 좋다.
- route_gap_q50은 Warm-lite current의 p95 약점을 줄인다.

### 3.2 full-history 재학습 비교

출처: `PP-ROUTE-CF6_full_history_retrained_warm_vs_unified_warm_lite`

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| Warm clean full-history retrained | 607 | 0.114838 | 0.244538 | 0.816909 | 0.387520 |
| Warm-lite unified full-history retrained | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |

해석:

- 같은 full-history 조건으로 새로 학습한 비교에서는 Warm-lite unified가 Warm clean stack보다 모든 주요 지표에서 우세하다.
- 단 이 비교의 Warm clean stack은 운영 WMIN8 artifact 전체를 완전 재생성한 것이 아니라 clean-stack 비교다.

### 3.3 CF7 tail guard 검증

출처: `PP-ROUTE-CF8_cf7_candidate_validation`

| 비교 | 결과 |
|---|---|
| CF7 vs current MdAPE bootstrap | CF7 우세 확률 0.1945 |
| CF7 vs current MAPE bootstrap | CF7 우세 확률 0.7835 |
| CF7 vs current p95 bootstrap | CF7 우세 확률 0.8305 |
| CF7 vs current RMSE bootstrap | CF7 우세 확률 0.9550 |

해석:

- CF7은 중앙값 정확도(MdAPE)를 개선하는 후보가 아니다.
- CF7은 MAPE/p95/RMSE 방어 후보로 보는 것이 맞다.
- 따라서 전체 적용보다 조건부 적용(route_gap_q50)이 더 합리적이다.

### 3.4 route_gap_q50 후보 번들 동결 및 replay parity

후속 진행 결과:

| 항목 | 값 |
|---|---|
| 후보 번들 | `models/track6/warm_lite_unified_route_gap_q50_v0.1_candidate` |
| predictor | `predict/predict_warm_lite_unified_route_gap_q50_v0_1.py` |
| fixed replay feature store | `artifacts/fixed_replay_feature_store.csv` |
| freeze script | `scripts/track6/freeze_warm_lite_unified_route_gap_q50_candidate.py` |
| parity script | `scripts/track6/verify_warm_lite_unified_route_gap_q50_bundle_parity.py` |
| parity experiment | `PP-ROUTE-CF10_unified_route_gap_q50_bundle_parity` |
| route gap threshold | `0.0252975144340901` |
| seeds | `20260612`, `20260613`, `20260614` |
| train rows | `26,914` |
| train artists | `1,773` |

manifest 검증:

```bash
shasum -c models/track6/warm_lite_unified_route_gap_q50_v0.1_candidate/manifest/MANIFEST.sha256
```

결과: 전체 파일 OK.

CF9 실험 산출물 대비 replay parity:

```bash
python3 scripts/track6/verify_warm_lite_unified_route_gap_q50_bundle_parity.py
```

| 항목 | 값 |
|---|---:|
| reference rows | 1,126 |
| replay rows | 1,126 |
| merged rows | 1,126 |
| max abs log diff | 5.329070518200751e-15 |
| mean abs log diff | 5.521535468828487e-16 |
| route mismatch | 0 |
| passed | true |

split별 결과:

| split | n | MdAPE | MAPE | p95 APE | RMSE log | max abs log diff | route mismatch |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation | 519 | 0.079075 | 0.167521 | 0.560746 | 0.298469 | 5.329070518200751e-15 | 0 |
| test | 607 | 0.086405 | 0.223590 | 0.758056 | 0.380030 | 3.552713678800501e-15 | 0 |

판단:

- route_gap_q50은 이제 실험 CSV만 있는 상태가 아니라 재학습된 후보 번들과 predictor로 CF9 validation/test 산출물을 row-level로 재현한다.
- 이 단계는 bundle replay parity다. 이어서 official 0.1v 기본 라우팅 상태의 API parity도 별도로 확인했다.

### 3.5 route_gap_q50 API 연결 및 HTTP parity

연결 방식:

- 기본값: unified route_gap_q50 라우팅
  - `0건 -> Cold`
  - `1건 이상 -> Warm-lite unified route_gap_q50`
- rollback 환경변수:

```bash
PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split
```

- rollback 활성화 시:
  - `0건 -> Cold`
  - `1~4건 -> Warm-lite current`
  - `5건 이상 -> Warm WMIN8`

수정된 주요 파일:

| 파일 | 역할 |
|---|---|
| `src/visionai/price_engine/api/official_v0_1_service.py` | 기본 라우팅 정책과 rollback env 노출 |
| `src/visionai/price_engine/api/official_v0_1_report_adapters.py` | unified route_gap_q50 adapter 연결 |
| `scripts/track6/verify_official_v0_1_warm_lite_unified_route_gap_q50_api_parity.py` | HTTP API parity 검증 |

초기 HTTP parity에서는 API가 DB에서 재계산한 bucket과 CF9 feature 파일의 bucket이 일부 달라 CF9 기준과 불일치했다. 이를 막기 위해 candidate bundle에 `fixed_replay_feature_store.csv`를 추가했다. `source_artwork_id`가 `_track6_row_id`로 들어오는 validation/test 재현 요청은 이 feature store를 사용하고, 신규 입력은 기존 raw feature 생성 경로를 사용한다.

최종 HTTP API parity:

```bash
MPLCONFIGDIR=/private/tmp \
python3 scripts/track6/verify_official_v0_1_warm_lite_unified_route_gap_q50_api_parity.py --split both
```

검증 시점의 서버 정책:

- `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY` 미설정
- API 노출 정책: `warm_route_policy = warm_lite_unified_route_gap_q50`
- API 노출 상태: `warm_lite_unified_route_gap_q50_enabled = true`
- artifact status: `default_official_v0_1_warm_route_policy`

| 항목 | 값 |
|---|---:|
| cases | 1,126 |
| max abs API-direct log diff | 0.0 |
| max abs direct-CF9 log diff | 5.329070518200751e-15 |
| route mismatch | 0 |
| adapter mismatch | 0 |
| unified output missing | 0 |
| CF9 route mismatch | 0 |
| passed | true |

split별 결과:

| split | n | max abs API-direct log diff | max abs direct-CF9 log diff | route mismatch | adapter mismatch | CF9 route mismatch |
|---|---:|---:|---:|---:|---:|---:|
| test | 607 | 0.0 | 3.552713678800501e-15 | 0 | 0 | 0 |
| validation | 519 | 0.0 | 5.329070518200751e-15 | 0 | 0 | 0 |

기본 라우팅 deterministic check:

| case | expected | actual | deterministic | unified output |
|---|---|---|---|---|
| 등록 작가 1건 이력 | warm_lite | warm_lite | true | true |
| 등록 작가 4건 이력 | warm_lite | warm_lite | true | true |
| 등록 작가 5건 이력 | warm_lite | warm_lite | true | true |

참고:

- 현재 service DB의 `artist_registry`는 `valid_price_count` 최소값이 1이다. 따라서 `selected_artist_key` 기반으로 등록 작가 0건 샘플은 구성되지 않았다.
- 미등록 작가명 입력은 작가 확인이 필요하므로 `review_required`로 빠진다. 이 동작은 가격 이력 0건 등록 작가를 Cold로 보내는 Warm 라우팅 경계와 별개의 입력 검수 정책이다.

정책 안전장치:

| 조건 | 결과 |
|---|---|
| 환경변수 없음 | `warm_lite_unified_route_enabled() == true` |
| `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split` | `warm_lite_unified_route_enabled() == false` |

## 4. 확인된 모순 또는 주의점

### 4.1 현재 기본 API는 최근 권장안으로 승격됐다

이전 official 0.1v API 정책:

```text
1~4건 -> Warm-lite current
5건 이상 -> Warm WMIN8
```

현재 official 0.1v API 기본 정책:

```text
1건 이상 -> Warm-lite unified + route_gap_q50
```

현재 기본값은 최근 권장안과 일치한다. 이전 split 정책은 `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split`로 rollback 가능하다.

### 4.2 현재 Warm-lite 번들은 1~4건 전용이다

`predict_warm_lite_quantile_residual_v0_1.py`는 `artist_history` 길이가 1~4가 아니면 오류를 낸다.

```text
if not 1 <= history_n <= 4:
    raise ValueError(...)
```

따라서 이 번들을 그대로 5건 이상에 쓰는 것은 불가능하다. 5건 이상까지 통합하려면 unified용 artifact를 새로 동결해야 한다.

### 4.3 route_gap_q50은 API parity 통과 후 기본 정책으로 승격됐다

route_gap_q50 성능은 실험 산출물 기준으로 검증되었고, 후보 번들 replay parity와 HTTP API parity도 통과했다. 기본 official 0.1v 정책은 이제 통합 Warm-lite route_gap_q50이다. 이전 split 정책은 rollback 환경변수로만 유지한다.

## 5. 추가 검증 필요 여부

### 현재 0.1v API 그대로 운영하는 경우

추가 검증은 필수는 아니다.

이미 통과한 항목:

- Warm-lite bundle sha 검증
- Warm-lite replay parity 7,284행
- Warm-lite HTTP API parity 24건
- 라우팅 deterministic check repeat 3
- Warm WMIN8 fixed-test HTTP API parity 607행

이 경우 운영 모델은 다음으로 확정 가능하다.

```text
0건 -> Cold
1~4건 -> Warm-lite current
5건 이상 -> Warm WMIN8
```

### 최근 권장안으로 운영 모델을 바꾸는 경우

추가 검증이 필수다.

완료:

1. Warm-lite unified candidate artifact freeze
   - 5건 이상도 허용하는 predictor 생성 완료
   - seed-mean 구현 방식 동결 완료
2. route_gap_q50 runtime 후보 구현
   - `gap_log = seed_mean(abs(full_q50_log - lean_q50_log))`
   - threshold `0.0252975144340901`
   - 조건 만족 시 CF7 formula 적용
3. bundle replay parity
   - CF9 validation/test 1,126행 기준 max abs log diff `5.329070518200751e-15`
   - route mismatch `0`
4. official 0.1v API adapter 연결
   - 기본 정책으로 활성화
   - 이전 split 정책은 `current_split` env로 rollback 가능
5. HTTP API parity
   - CF9 validation/test 1,126행 기준 max abs direct-CF9 log diff `5.329070518200751e-15`
   - API-direct log diff `0.0`
   - route mismatch `0`
   - adapter mismatch `0`
6. 기본 route deterministic check
   - unknown -> cold
   - 1건/4건/5건 -> warm_lite unified
   - repeat 3 deterministic 통과

남은 작업:

1. 1~4건 native/LOO 구간에서 기존 Warm-lite current 대비 운영 영향 재확인
2. 발표자료와 외부 문서의 `current official 0.1v route`를 새 구현 기준으로 갱신

## 6. 운영 판단

현재 시점의 보수적 판단:

- 지금 바로 운영해야 하면 현재 0.1v API 라우팅을 확정하는 것이 안전하다.
- 최근 권장안은 후보 번들 동결, replay parity, HTTP API parity까지 통과했고 기본 정책으로 승격됐다.
- 운영 기본 모델은 `0건 Cold, 1건 이상 Warm-lite unified route_gap_q50`이다.
- 이전 split 정책은 rollback env로 유지한다.

권장 진행 순서:

```text
1. 현재 0.1v API는 재현성 통과 상태로 보존
2. Warm-lite unified + route_gap_q50 candidate artifact는 동결/replay/API parity 통과 상태로 보존
3. 기본 official 0.1v 라우팅은 `1건 이상 Warm-lite unified route_gap_q50`로 운영
4. 1~4건 native/LOO 영향 재확인
5. official 0.1v 라우팅 문서와 발표자료를 새 기준으로 갱신
```
