# Track6 가격예측 운영 서빙 설계 (official 0.1v)

- 작성일: 2026-06-22
- 대상: Track6 art-price prediction 신규 운영 서비스
- 기준 산출물
  - Warm (확정): `models/track6/warm_lite_unified_current_joblib_v0.1_candidate`
  - Cold (후보): `resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05` (k80 보수적 운영)
- 상위 참조
  - `docs/track6/experiments/warm_cold_final_operational_model_readiness_20260622.md`
  - `docs/track6/experiments/cold_official_v0_1_k80_operational_model_report.md`
- 서빙 아키텍처: 독립 joblib 번들 2개 + 얇은 FastAPI 라우팅 서비스 (Approach A)

---

## 1. 범위 & Non-goals

### 1.1 목적

기존 테스트 운영 서비스(`operational_v0_2_server` / `operational_v0_2_service`)를 폐기하고,
Warm/Cold 두 모델을 실제 서비스에 올릴 수 있는 신규 운영 서비스를 설계한다.
프론트는 작가 이름 검색 후 `artist_key`를 고르는 방식이며, 소스별로 추가 데이터를 주기적으로
수집·클린징해 학습용 데이터로 전환하고, 그 데이터로 모델 버전을 올린다.

### 1.2 In-scope

- 두 모델(Warm/Cold)을 각각 독립 joblib 번들로 동결하고, 한 FastAPI 서비스가 기동 시 둘 다 로드.
- 작가 해석 → 라우팅 → predictor 호출 → 응답.
- **소스별 데이터 수집·클린징·학습데이터 전환 파이프라인** (Saatchi/Artsy/Artue/gallery_primary).
- 모델 레지스트리(버전형 아티팩트 + active 포인터), 하이브리드 재학습/프로모션.
- 학습↔서빙 feature parity, strict-Cold 불변식, 실패 모드, 모니터링/피드백.

### 1.3 Non-goals (이번 설계 제외)

- 검색 피처 기반 Cold 연구 라인(v0.3 guard+search) 운영화 — strict-Cold 위배이므로 제외.
- 이미지/멀티모달 가격 모델.
- 프론트엔드 UI 구현 자체(여기서는 입력 계약/검색 흐름만 정의).
- 신규 외부 소스 추가/스크래퍼 신규 구축 — 기존 4개 소스 기준. (확장은 §7.1 규칙 따름)
- k40 후보 운영화(별도 실험에서 재검증 후 판단).

### 1.4 불변식 (Invariants)

이 서비스가 항상 지켜야 하는 규칙. 위반 시 배포 차단.

1. **미지 작가를 Warm으로 보내지 않는다.** 작가 매칭 실패·동명이인 위험·이력 부족이면 Cold.
2. **strict-Cold.** Cold 경로는 입력 작가의 `artist_key`로 같은 작가 가격 이력을 lookup하지 않는다.
   검색 피처·외부 live 검색·artist_key 기반 후처리 lookup을 사용하지 않는다.
3. **번들 자급.** predictor는 DB·외부 CSV·검색 API 없이 `runtime_store.joblib` 내부 산출물만으로 동작.
4. **불변 아티팩트.** 배포된 버전 아티팩트는 덮어쓰지 않는다. 새 학습은 새 버전으로 만들고 포인터만 교체.
5. **결정성.** 동일 입력 + 동일 아티팩트 → 동일 출력(부동소수 허용오차 이내).
6. **소스 추적성.** 모든 학습 행은 `track4_source` + `track4_source_row_index`로 원천까지 역추적 가능.

---

## 2. 표준 데이터 계약 (Canonical Data Contracts)

라우팅·predictor·API·학습이 모두 같은 스키마를 참조한다. 단위/통화/변환은 여기서 단일 정의한다.

### 2.1 공통 규칙

| 항목 | 규칙 |
|---|---|
| 크기 단위 | cm. 호(號) 단위로 직접 계산하지 않음 |
| 가격 단위 | KRW (원), 정수 |
| 가격 변환 | 모델은 log 공간에서 예측, 응답은 `exp()` 후 원 단위 |
| 면적 | `area_cm2 = width_cm * height_cm`, `log_area = log(area_cm2)` |
| 비율 | `aspect_ratio = width_cm / height_cm` |
| 결측 깊이 | `depth_cm` 없으면 0으로 처리, `has_depth=false` |
| enum | `medium_category`, `support_category`, `nationality`, `career_stage`는 고정 enum (번들에 동결) |
| 날짜 cutoff | 각 버전은 학습 데이터 cutoff 일자를 manifest에 기록. 라벨 누수 방지 기준 |

### 2.2 작가 식별 스키마 (Artist Identity)

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| `artist_key` | string | yes | 내부 식별자. 프론트가 검색 후 선택. 미등록 작가는 null |
| `artist_name_query` | string | yes | 사용자가 입력한 검색어(해석 단계에서만 사용) |
| `artist_match_score` | float | no | 0~1, 해석 결과 신뢰도 |
| `homonym_risk` | float | no | 0~1, 동명이인 위험 |
| `same_artist_training_history_count` | int | no | 같은 작가 학습 이력 수 (Warm 자격 판단) |

### 2.3 작품 입력 스키마 (Artwork Input)

| 필드 | 타입 | 필수 | 사용처 |
|---|---|---|---|
| `width_cm` | float | 필수 | Warm/Cold |
| `height_cm` | float | 필수 | Warm/Cold |
| `depth_cm` | float | 선택 | Warm/Cold (입체 판단) |
| `medium_category` | enum | 필수 | Warm/Cold |
| `support_category` | enum | 필수 | Warm/Cold |

### 2.4 수동 메타 스키마 (Cold 신규작가 입력, 모두 선택)

strict-Cold 원칙상 "사용자가 입력 가능하거나 운영에서 독립 검수 가능한 비가격성 정보"만 허용.
입력 오류를 줄이기 위해 enum 드롭다운으로 유도하고, 미입력 시 결측 상태로 예측한다.

| 필드 | 타입 | nullable | 비고 |
|---|---|---|---|
| `artist_meta_birth_year` | int | yes | 연도 |
| `artist_meta_nationality` | enum | yes | 드롭다운 리스트 |
| `artist_meta_career_stage` | enum/int | yes | 드롭다운 리스트 |

> 금지: 위 메타가 hidden `artist_key` 가격 이력 lookup으로 이어지면 안 됨 (불변식 2).

### 2.5 Predictor I/O 계약

**Warm predictor**
- 입력: 작가 식별(확정 `artist_key`) + 작품 입력
- 내부 생성: `area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, size_bucket, shape_bucket, medium_support_bucket` + 같은 작가 가격/면적단가 통계(`grp_*`) + Quantile 출력(`lgbq_*`) + residual 보정
- 출력: `pred_log_price, pred_price, q10/q50/q90, qwidth, residual_correction_log, grp_match_level, grp_n_log`

**Cold predictor (k80)**
- 입력: 작품 입력 + (선택) 수동 메타. `artist_key` 가격 이력 미사용
- 내부 생성: 작품 피처 + 비작가 그룹 통계(`grp_*`) + Quantile 출력(q10/q40/q50/q90) + 유사 작가-메타 이웃 80건 OOF 잔차 중앙값
- 출력: `pred_log_price, pred_price, base_log_price, correction_log, route(base|residual_correction), neighbor_k(=80), selected_neighbor_count, neighbor_similarity_mean, q-band, strict_cold_compliant(=true)`

### 2.6 공통 응답 스키마

모호한 단일 "confidence"를 쓰지 않고 명시 필드로 분해한다.

| 필드 | 설명 |
|---|---|
| `predicted_price_krw` | 최종 예측 가격(원) |
| `price_low_krw`, `price_high_krw` | 가격 범위(Warm: q10/q90, Cold: q10/q90 또는 방어밴드) |
| `predicted_log_price` | 최종 로그가격 |
| `route` | `warm` \| `cold_registered` \| `cold_new_artist` |
| `route_reason` | 라우팅 근거(예: `history_ge_5`, `match_below_threshold`, `no_artist_key`) |
| `model_version` | 적용된 아티팩트 버전(warm/cold 각각) |
| `review_flags` | 검수 필요 신호 배열(예: `homonym_risk`, `low_neighbor_similarity`) |
| `diagnostics` | `artist_match_score`, `feature_missing`, `guard_applied`, `correction_log`, `grp_match_level` 등 |

---

## 3. 아티팩트 & 번들 계약

### 3.1 번들 구조 (Warm/Cold 동일 형태)

```text
models/track6/<bundle_name>/
  artifacts/
    runtime_store.joblib
  config/
    <policy>.json
  predict/
    <predictor>.py
  test_data/
    track6_test_<route>.csv
  test_outputs/
    fixed_test/
      summary.json
      predictions.csv
      predictions_with_diagnostics.csv
  manifest.json
  README.md
```

### 3.2 `runtime_store.joblib` 내용

| 번들 | 포함 산출물 |
|---|---|
| Warm | 작가 registry(1,773), alias(3,600), 같은 작가 학습 이력(26,914), LightGBM Quantile(full/lean), Huber residual 모델(3 seed), size/shape/medium_support bucket 규칙, feature schema |
| Cold | base Cold LightGBM Quantile(5 seed), Huber 그룹통계 모델, train reference pool, OOF residual 배열, 유사도 전처리기, 비작가 그룹통계 ladder + global fallback, size/support bucket 규칙, feature schema, 라우터 정책(k80, cap0.25, route≤-0.05) |

### 3.3 `manifest.json` 필드

```json
{
  "bundle_name": "...",
  "route": "warm|cold",
  "model_version": "official_0.1v",
  "schema_version": "1",
  "created_at": "2026-06-22T00:00:00Z",
  "training_data_cutoff": "YYYY-MM-DD",
  "source_snapshot": {"saatchi": "<rev/date>", "artsy": "...", "artue": "...", "gallery_primary": "..."},
  "git_sha": "<commit>",
  "dependency_lock": {"python": "3.11", "lightgbm": "x.y.z", "scikit-learn": "x.y.z", "joblib": "x.y.z"},
  "artifact_sha256": "<checksum of runtime_store.joblib>",
  "feature_schema_ref": "config/<policy>.json#features",
  "fixed_test_metrics": {"n": 607, "mdape": 0.086970, "mape": 0.223682, "p95_ape": 0.820366, "rmse_log": 0.382823}
}
```

### 3.4 로드 시 검증 (load-time validation)

기동 시 각 번들에 대해 아래를 검사하고, 하나라도 실패하면 해당 route를 **unavailable**로 표시(서비스는 뜨되 해당 경로 차단)하고 알림.

- `artifact_sha256`가 실제 파일 체크섬과 일치
- `schema_version`이 서비스가 지원하는 버전과 호환
- `dependency_lock`의 핵심 라이브러리 major 버전 일치
- predictor가 fixed_test 1행을 실행해 manifest 지표 범위 내 재현(스모크)

### 3.5 버전 분리

Warm 아티팩트 버전, Cold 아티팩트 버전, 라우팅 서비스 버전을 각각 독립 관리한다.
한쪽 모델만 재학습/롤백할 수 있어야 한다.

---

## 4. 컴포넌트 분해

책임·의존성 중심. 상세 I/O는 §2(데이터 계약)·§10(API)를 참조.

| 컴포넌트 | 책임 | 의존성 |
|---|---|---|
| Artist Resolution | 이름 검색 → 후보 리스트(key, 이력 보유, 동명이인 위험). 확정 key 검증 | registry/alias (Warm 번들 내 또는 별도 인덱스) |
| Router | 확정 입력으로 warm/cold_registered/cold_new_artist 판정 | Artist Resolution 결과, 라우팅 정책 |
| Warm Predictor | Warm 번들 호출, §2.5 출력 반환 | Warm `runtime_store.joblib` |
| Cold Predictor | Cold 번들 호출, strict-Cold 보장, §2.5 출력 반환 | Cold `runtime_store.joblib` |
| Model Registry | 버전형 아티팩트 + active 포인터 관리, 로드/스왑/롤백 | manifest, 디스크/스토리지 |
| Data Pipeline | 소스별 수집·클린징·학습데이터 전환 (§7) | 4개 소스, quality override, manifest |
| Feedback Logger | 예측·진단·실판매가 적재(재학습 입력) | 로그 스토어 |
| Monitoring | route/feature 가용성/예측분포/레이턴시/에러 집계 | 로그 스토어 |

각 컴포넌트는 단일 책임을 가지며, 인터페이스(§2/§10)로만 통신해 독립 테스트가 가능해야 한다.

---

## 5. 추론 순서도

### 5.1 작가 이름 검색 → 해석

```text
[프론트: 이름 입력]
        |
        v
[POST /artists:search  { name_query }]
        |
        v
[registry/alias 매칭]
  - exact (key/한글명/영문명) → score 1.0
  - alias slug → score 0.95
  - fuzzy(token_sort) → score ~0.80
  - 동명이인 후보 수로 homonym_risk 계산
        |
        v
[후보 리스트 반환(최대 N)]
  각 후보: artist_key, name, birth_year, nationality,
           same_artist_training_history_count, homonym_risk
        |
        v
[프론트: 사용자 후보 선택]
  - 목록에 없음(신규/미등록) → artist_key 없이 Cold-new-artist로 진행
        |
        v
[선택된 artist_key를 예측 요청에 첨부]
```

### 5.2 가격 예측 요청 → 라우팅 → 분기 → 응답

```text
[POST /price-predictions]
  { artist_key?, width_cm, height_cm, depth_cm?,
    medium_category, support_category, meta? }
        |
        v
[입력 검증]
  - 필수 필드/단위/enum 확인
  - 실패 → 422 (검증 에러)
        |
        v
[라우팅 판정]  (§6 규칙)
  artist_key != null
   AND artist_match_score >= 0.80
   AND homonym_risk < 0.60
   AND same_artist_training_history_count >= 5
        |
   +----+--------------------------------+
   | yes                                  | no
   v                                      v
[Warm Predictor]                  [artist_key != null 이고
  - 같은 작가 이력 사용             match>=0.80 이지만 이력<5?]
  - route=warm                         |
                                   +---+----------------------+
                                   | yes (등록작가, 이력부족) | no (미지/미등록/모호)
                                   v                          v
                            [Cold Predictor]          [Cold Predictor]
                              route=cold_registered      route=cold_new_artist
                              meta: 등록 메타 사용        meta: 사용자 입력(선택)
                                                          결측 허용
        |                          |                          |
        +-----------+--------------+--------------------------+
                    |
                    v
            [출력 정상성 검사]
              - price > 0, NaN/inf 아님
              - 범위 low<=p50<=high
              - 비정상 → review_flag + fallback(§6.5)
                    |
                    v
            [응답 반환]  (§2.6 스키마)
              predicted_price_krw, price_low/high,
              route, route_reason, model_version,
              review_flags, diagnostics
```

### 5.3 Cold 내부(신규작가·메타결측 포함)

```text
[Cold 입력]
        |
        v
[기본 피처 생성: area, log_area, aspect_ratio, buckets]
        |
        v
[base Cold 예측: LightGBM Quantile q10/q40/q50/q90 (5 seed 평균)
   + Huber 그룹통계, 대표 = 0.70*q50 + 0.30*Huber]
        |
        v
[유사 작가-메타 이웃 80건 검색]
  - artist_key 아님. 작가 메타/작품 조건 유사도 기준
  - 메타 결측 시: 가용 차원만으로 유사도 계산,
    similarity 낮으면 review_flag(low_neighbor_similarity)
        |
        v
[이웃 OOF 잔차 중앙값 → correction_log = clip(1.0*median, -0.25, +0.25)]
        |
        v
[라우터: correction_log <= -0.05 이면 corrected, 아니면 base]
        |
        v
[p95 방어(선택): qwidth 크고 대표가 q40 대비 높으면 0.5*대표+0.5*q40]
        |
        v
[final_price = exp(final_log)]
```

---

## 6. 라우팅 규칙 & 실패 모드

### 6.1 Warm 자격 술어 (모두 참이어야 Warm)

```text
artist_key != null
AND artist_match_score >= 0.80
AND homonym_risk < 0.60
AND same_artist_training_history_count >= 5
```

하나라도 거짓이면 Cold. 등록작가지만 이력<5 → `cold_registered`, 그 외 → `cold_new_artist`.

### 6.2 실패 모드 매트릭스

| 상황 | 처리 | 사용자 표시 |
|---|---|---|
| 검색 후보 없음 | Cold-new-artist 안내 | 메타 수동 입력 유도 |
| 모호(다수 고득점 매칭) | Warm 차단, `review_flag=homonym_risk` | 후보 재선택 요청 |
| match 높지만 오매칭 의심 | homonym_risk 기준 차단/검수 | 검수 필요 |
| artist_key 있으나 이력<5 | `cold_registered` | 정상 예측 + 낮은 신뢰 표시 |
| artist_key 있으나 메타 결측 | 결측 상태로 Cold 예측 | 선택 입력 안내 |
| Cold 메타 enum unknown/legacy | 결측 처리 + `feature_missing` 기록 | — |
| 번들 로드 실패(한쪽) | 해당 route unavailable, 다른 route 정상 | 503(해당 경로) + 알림 |
| 두 번들 모두 실패 | 서비스 unhealthy | health=red |
| active 포인터 깨짐 | 직전 정상 버전으로 자동 롤백 시도 | 알림 |
| 출력 NaN/음수/범위역전 | fallback(§6.5) + `review_flag=invalid_output` | 검수 필요 |
| 레이턴시 타임아웃 | 504 | 재시도 안내 |
| 피드백 실판매가 outlier | 적재하되 outlier 플래그(재학습서 필터) | — |

### 6.3 strict-Cold 코드 레벨 강제

- Cold predictor 함수 시그니처에 같은-작가 가격 이력 accessor를 **주입하지 않는다**.
- Cold 입력에 `artist_key`가 와도 가격 이력 lookup/유사도/라우터 조건에 사용하지 않는다.
- guard 테스트로 검증(§12): Cold 실행 중 history/search 의존성 호출 시 실패.

### 6.4 SLO / 운영 제약

| 항목 | 목표(초기 기준, 측정 후 보정) |
|---|---|
| startup 번들 로드 | 두 번들 1회 로드, 요청마다 재로딩 금지 |
| 메모리 | 두 `runtime_store.joblib` 상주 가능 용량 확보(번들 크기 + reference pool) |
| p95 추론 레이턴시 | 예측 엔드포인트 기준 목표치 설정 후 모니터링 |
| 가용성 | 한쪽 모델 장애 시 다른 경로는 계속 서비스 |

### 6.5 출력 비정상 fallback

대표 예측이 비정상이면: Warm은 같은 작가 통계 median(`grp_log_price_median`), Cold는 base q50로 대체하고
`review_flag=invalid_output`을 단다. 둘 다 불가하면 예측 거부(검수 대기).

---

## 7. 데이터 수집·클린징·학습데이터 전환 (소스별)

단순 주기 학습이 아니라, **소스별로 독립 수집·클린징한 뒤 학습용 데이터로 전환**하는 파이프라인을
명시한다. 이 파이프라인의 산출물(고정 cutoff snapshot)이 §8 재학습의 입력이 된다.

### 7.1 원칙

- **소스 4종**: `saatchi`, `artsy`, `artue`, `gallery_primary`. 원천 컬럼은 `<source>__<col>`로 네임스페이싱.
- **추적 키**: `track4_source` + `track4_source_row_index`로 모든 단계가 원천까지 역추적(불변식 6).
- **소스별 독립**: 한 소스만 재수집·재클린징해도 나머지를 건드리지 않고 병합·재빌드 가능.
- **원본 불변**: raw 레이어는 표준화/필터 없이 원본 보존. 표준화·파생은 하위 레이어에서만.
- **누수 차단**: 가격 라벨/추적 컬럼은 feature에서 분리, Cold 금지 컬럼은 Cold feature에서 제외(§7.4).
- **신규 소스 확장**: 동일한 `track4_source` 네임스페이싱 + 클린징 규칙 + manifest 등록 절차를 따른다.

### 7.2 레이어 (단계별 입출력)

| 단계 | 입력 | 출력 | 역할 |
|---|---|---|---|
| L0 Raw collected | 소스별 수집 원본 | `track4_primary_market_raw_collected.csv` (소스별 네임스페이싱, 표준화 없음) | 원본 보존·추적 |
| L1 Candidates v1 | L0 | `track4_primary_market_feature_candidates_v1.csv` | artist_key·가격(KRW)·크기·medium/support 표준화, `is_training_candidate` 판정 |
| L2 이름 보정 | L1 + `artist_ko_overrides.csv` | `track6/track6_feature_candidates_name_corrected.csv` | 작가 한글명 표준화(검토된 override만 적용, 원본 `_orig` 보존) |
| L3 Enrichment | L2 + L0 + 참조표 | (in-place 컬럼 추가) | 작가 메타(`artist_meta_*`), NANT 재료(`nant_*`) |
| L4 작품속성 | L3 | `_with_year`, `_with_year_type`, `_edition`, `_size` 순차 | 연도/타입/에디션/추정 호수(`estimated_ho`) |
| L5 Split | L2(또는 L4 enriched) | `track6_split/` (train/val_warm/test_warm/val_cold/test_cold) | Cold-first 분할, membership |
| L6 Feature/Label | L5 | `features/{warm,cold}/`, `labels/` | 가격 누수 차단 물리 분리 |
| L7 Manifest | L6 | `manifests/track6_feature_label_manifest.json` | 경로·행수·제외/금지 컬럼·cutoff 기록 |

### 7.3 소스별 수집·클린징 (순서도)

```text
[per-source 수집]  (각 소스 독립 실행)
   saatchi / artsy / artue / gallery_primary
        |
        v
[네임스페이싱: <source>__<col>, track4_source, track4_source_row_index]
        |
        v
[L0 raw_collected 병합/갱신]  - 해당 소스 파티션만 교체 가능
        |
        v
[L1 표준화: artist_key, price_krw, 크기, medium/support, is_training_candidate]
        |
        v
[소스별 클린징 규칙 적용]
   - artue: Medium(KO/EN) 파싱
   - saatchi: detail-page enrichment, attribution_class
   - artsy: category/medium_type, attribution_class
   - gallery_primary: materials, 연도, gallery tier
        |
        v
[L2~L3 품질 단계]
   - 이름 보정(override 적용 + review 큐)
   - 작가 메타 enrichment(+summary)
   - NANT 재료 분류(exact/keyword/inferred + unmatched 큐)
        |
        v
[L4 작품속성 enrichment(year/type/edition/size)]
        |
        v
[품질 게이트(§7.5) 통과?]
        |
   +----+--------------------+
   | yes                      | no
   v                          v
[학습데이터 전환(§7.4)]   [검토 큐로 보류, 소스 단위 재처리]
```

### 7.4 학습데이터 전환 (Candidates → Train-ready)

- **Split(L5)**: `create_track6_splits.py` — Cold-first. Cold val/test artist 집합을 train과 분리(겹침 없음),
  Warm은 train 내 artist별 홀드아웃(최소 5 train + 2~3 holdout).
- **Feature/Label 분리(L6)**: `export_feature_label_splits.py` — feature 파일에서 가격/정답/출처 제외, label 파일에 `price_krw`/`ln_price_krw` + 평가 메타.
- **Manifest(L7)** 핵심 정책:
  - `target_columns`: `price_krw`, `ln_price_krw`
  - `tracking_only_columns`: `track4_source`, `track4_source_row_index`, `source_artwork_id`, `artwork_url`, ...
  - `model_exclude_columns`: 작가명/원본명/표준화명/`is_homonym` 등
  - `cold_forbidden_columns`: `artist_key`, `artist_works_log`, `artist_works_count_train` (strict-Cold 강제)
  - `price_leak_allowlist`: `estimated_ho`
- **추론 피처 정합(서빙)**: `extract_price_prediction_v0_1_features.py` — 가격 없는 운영 입력을 동일 규칙으로
  Warm/Cold feature set으로 변환. 학습과 동일한 bucket/파생 규칙을 사용해 parity 보장(§12 parity 테스트).

### 7.5 품질 게이트 & 검토 큐

| 산출물 | 의미 | 운영 처리 |
|---|---|---|
| `*_review_candidates.csv` (이름) | 미해결 한글명 후보 | 검토 후 `artist_ko_overrides.csv`에 반영 |
| `*_unmatched_review.csv` (NANT) | 미매칭 재료 | 규칙/참조표 보강 |
| `*_enrichment_summary.json` | 커버리지/매칭률 | 임계 미달 시 재학습 보류 |
| `cleaning_exclude_reasons` | 학습 제외 사유 | 제외율 급증 시 소스 점검 |

게이트 기준(예): 소스별 가격 파싱 성공률·메타 커버리지·재료 매칭률이 직전 snapshot 대비 비악화.
미달 소스는 해당 소스만 보류하고 나머지로 진행 가능.

### 7.6 주기적 운영 연결

```text
[고정 주기 도래 or 소스 갱신 이벤트]
        |
        v
[갱신 대상 소스만 재수집·재클린징(§7.3)]   - 미갱신 소스는 기존 파티션 유지
        |
        v
[병합 → L4 enriched → 품질 게이트(§7.5)]
        |
        v
[cutoff 고정 → train-ready snapshot 생성(§7.4)]
        |
        v
[§8 재학습 파이프라인 입력으로 전달]
```

> cutoff·소스 snapshot은 새 모델 manifest(`training_data_cutoff`, `source_snapshot`)에 기록해 재현성을 확보한다.

---

## 8. 학습·재학습 순서도

### 8.1 Warm 학습 파이프라인

```text
[train-ready snapshot(§7): 가격 라벨 + 작품 피처 + 같은 작가 이력]
        |
        v
[작가별 비교군 통계 생성: 같은 작가 + 매체/지지체 + 크기 구간 → fallback ladder]
        |
        v
[LightGBM Quantile 학습(full q10/q50/q90, lean q50)]
        |
        v
[기준 로그가격 = full q50 와 lean q50 평균]
        |
        v
[LightGBM Huber residual 학습 → 0.5*residual, clip ±0.10]
        |
        v
[3 seed 평균 → runtime_store.joblib 동결]
```

### 8.2 Cold 학습 파이프라인 (k80)

```text
[train-ready snapshot(§7): 가격 라벨 + 작품 피처 + 입력가능 작가 메타]
  (artist_key는 split/관리용. 모델 피처/유사도/라우터에 미사용)
        |
        v
[base Cold 학습: LightGBM Quantile q10/q40/q50/q90 + Huber 그룹통계]
        |
        v
[OOF 잔차 생성: train 내부 fold 분할, hold-out row는 자기 미학습 모델 예측,
   residual = 실제 log - OOF 예측 log]
        |
        v
[유사 작가-메타 이웃 검색기 + reference pool 동결]
        |
        v
[k80 보정 규칙: correction = clip(1.0*이웃 OOF 잔차 중앙값, -0.25, +0.25),
   route: correction <= -0.05 일 때만 적용]
        |
        v
[runtime_store.joblib 동결]
```

### 8.3 하이브리드 재학습 (고정 주기 + 성능 게이트)

```text
[트리거: 고정 주기 도래]  (운영 합의 주기, 예: 분기)
        |
        v
[데이터 갱신: 소스별 수집·클린징·전환(§7) → train-ready snapshot]
        |
        v
[신버전 학습(8.1 / 8.2)]
        |
        v
[fixed test / hold-out 평가]
  - 누수 통제: cutoff 이후 라벨 미사용, OOF 규칙 준수
        |
        v
[parity 검증: 실험 산출값 == 신 joblib predictor 산출값 (diff ~0)]
        |
        v
[성능 게이트(§9.2): 신버전 >= 구버전 (전체 + 슬라이스)]
        |
   +----+-----------------+
   | pass               | fail
   v                    v
[shadow run]        [승격 보류, 구버전 유지, 원인 분석]
  - 실트래픽 복제, 신/구 예측 diff 로깅
        |
        v
[active 포인터 교체(승격)]  - 기존 버전 보존(롤백 가능)
```

---

## 9. 프로모션 · 레지스트리 · 롤백

### 9.1 레지스트리

```text
model_registry/
  official_0.1v/
    warm/  { artifact_id, created_at, sha256, fixed_test_metrics, cutoff }
    cold/  { artifact_id, created_at, sha256, fixed_test_metrics, cutoff }
  active_pointer.json  { warm: official_0.1v, cold: official_0.1v }
```

- 아티팩트는 불변. 재학습은 `official_0.2v` 등 새 디렉토리로 생성.
- active 포인터만 교체해 승격. Warm/Cold 포인터 독립.

### 9.2 성능 게이트 기준 (수치화)

신버전 승격은 아래를 모두 만족해야 한다. tie/소폭 악화는 보류.

| 지표 | 기준 |
|---|---|
| 전체 MdAPE / MAPE / p95 APE | 구버전 대비 비악화 (regression tolerance 내) |
| 슬라이스 | warm / cold / 고가 작품 / 메타결측 / 신규작가 슬라이스에서 비악화 |
| 안정성 | paired bootstrap CI로 개선/비악화 방향 확인 (구버전 대비) |
| 누수 | cutoff 이후 라벨 미사용, OOF 규칙 준수 확인 |
| parity | 실험 vs predictor 예측 diff 0 또는 부동소수 허용오차 이내 |

> Cold k80 기준선(참고): validation MdAPE 0.404411 / p95 1.638585, test MdAPE 0.479052 / p95 2.231840.
> Warm fixed test 기준선: MdAPE 0.086970 / p95 0.820366 (n=607).

### 9.3 롤백

- 트리거: 로드 검증 실패, 출력 비정상률 급증, 모니터링 지표 악화, shadow diff 이상.
- 동작: active 포인터를 직전 정상 버전으로 즉시 교체(아티팩트가 불변이라 무손실).
- audit log: 누가 언제 어떤 아티팩트를 승격/롤백했는지 기록.

### 9.4 보안 / 감사

- 버전 조회는 공개 가능, **포인터 스왑·롤백은 admin 전용**.
- 피드백 로그에 거래가/식별정보 포함 가능 → PII 정책·접근통제 적용.
- 모든 승격/롤백은 audit trail에 행위자·시각·아티팩트 sha 기록.

---

## 10. API 계약

| 엔드포인트 | 메서드 | 역할 |
|---|---|---|
| `/artists:search` | POST | 이름 검색 → 후보 리스트(key, 메타, 이력수, homonym_risk) |
| `/price-predictions` | POST | 작품 입력 → 가격 예측(라우팅 포함) |
| `/models/active` | GET | 현재 warm/cold active 버전·정책 조회 |
| `/feedback/sale-price` | POST | 실판매가 피드백 적재 |
| `/admin/models:promote` | POST | (admin) active 포인터 교체 |
| `/admin/models:rollback` | POST | (admin) 직전 버전 롤백 |
| `/health` | GET | 번들 로드/route 가용성 |

### 10.1 응답 예시

**Warm**
```json
{
  "predicted_price_krw": 5200000,
  "price_low_krw": 3100000, "price_high_krw": 8600000,
  "route": "warm", "route_reason": "history_ge_5",
  "model_version": {"warm": "official_0.1v"},
  "review_flags": [],
  "diagnostics": {"artist_match_score": 1.0, "grp_match_level": "artist_medium_size",
                  "qwidth": 0.51, "residual_correction_log": 0.012}
}
```

**Cold (신규작가, 메타 일부 결측)**
```json
{
  "predicted_price_krw": 4500000,
  "price_low_krw": 2300000, "price_high_krw": 9100000,
  "route": "cold_new_artist", "route_reason": "no_artist_key",
  "model_version": {"cold": "official_0.1v"},
  "review_flags": ["low_neighbor_similarity"],
  "diagnostics": {"feature_missing": ["artist_meta_nationality"],
                  "neighbor_k": 80, "selected_neighbor_count": 62,
                  "correction_log": -0.08, "route": "residual_correction"}
}
```

---

## 11. 모니터링 & 피드백 스키마

| 그룹 | 필드 |
|---|---|
| 공통 | request_id, ts, model_version(warm/cold), latency_ms, error_code |
| route | route, route_reason, artist_match_score, homonym_risk |
| feature 가용성 | feature_missing[], grp_match_level, grp_n_log |
| 예측 분포 | predicted_price_krw, price_low/high, q10/q50/q90, qwidth |
| Warm 전용 | residual_correction_log, artist_history_n |
| Cold 전용 | guard_applied, correction_log, neighbor_similarity_mean, selected_neighbor_count |
| 피드백 | actual_price_krw, sold_at, outlier_flag(재학습 필터용) |
| 데이터 | source snapshot rev, 소스별 커버리지/제외율(§7.5) |

용도: 작가 매칭 품질 감시, 보정 과다 감시, p95 방어 발동 구간 확인, 재학습 후보 데이터 구축, 재현성(version+sha) 확보.

---

## 12. 검증 · 테스트 플랜

| 분류 | 테스트 |
|---|---|
| schema | 입력 검증(필수/단위/enum), 응답 스키마 |
| route | Warm 술어 정확성, 경계(이력=4 vs 5), homonym 차단 |
| strict-Cold guard | Cold 실행 중 history/search/artist_key lookup 호출 시 실패 |
| invariant | 미지 작가 항상 Cold / 이력<5 항상 cold_registered / 동일 fixture offline==serving |
| 데이터 parity | 학습 feature 생성 vs 운영 추론 feature 생성 동일 규칙(§7.4) 검증 |
| 소스 추적 | track4_source+row_index 역추적, 소스별 부분 재빌드 후 비대상 소스 불변 |
| parity | 실험 산출값 vs predictor 산출값 diff 0(허용오차) — Warm 607행, Cold 3,099행 |
| golden fixture | 대표 입력 N건의 예측 스냅샷 회귀 |
| bundle | manifest 체크섬/스키마/dep 검증, 로드 실패 시 route unavailable |
| integration | 두 번들 동시 로드 후 end-to-end 라우팅 |
| shadow / replay | 과거 요청 재현, 신/구 버전 diff 로깅 |
| failure | §6.2 각 실패 모드 처리 확인 |

---

## 13. 구현 계획 (작업 순서)

1. **데이터 파이프라인 정리** — 소스별 수집·클린징·전환(§7)을 재실행 가능한 잡으로 묶고, cutoff/소스 snapshot 기록.
2. **Cold 번들 동결** — k80 기준안을 `cold_k80_conservative_official_v0.1_candidate`로 단일 `runtime_store.joblib` 화.
3. **manifest/schema 정의** — Warm/Cold manifest(§3.3), feature schema, enum 동결.
4. **Predictor adapter** — `predict(input)->output`(§2.5)로 Warm/Cold predictor 래핑, DB/CSV/검색 차단.
5. **Registry loader** — 버전 디렉토리 + active 포인터 로드/검증(§3.4), 스왑/롤백 API.
6. **Router** — Warm 술어(§6.1) + 실패 모드(§6.2) 구현, strict-Cold 코드 강제(§6.3).
7. **API 서비스** — §10 엔드포인트, 기동 시 두 번들 1회 로드.
8. **로깅/모니터링** — §11 스키마 적재.
9. **parity 테스트** — 데이터 parity(§7.4) + Warm 607 / Cold 3,099 fixed test diff 0 검증.
10. **integration / strict-Cold guard / invariant 테스트** — §12.
11. **shadow deploy** — 실트래픽 복제, 신/구 diff 로깅.
12. **포인터 승격** — 성능 게이트(§9.2) 통과 시 active 포인터 교체.

---

## 14. 한 줄 정리

Warm은 joblib-only 독립 번들로 운영 준비가 가장 앞서 있고, Cold는 strict-Cold k80 보수적 운영 후보를
같은 번들 계약·parity·strict-Cold 강제·모니터링으로 동결하면 운영 가능하다. 데이터는 소스별로 수집·클린징해
학습용으로 전환하고, 재학습은 그 snapshot으로 새 버전 아티팩트를 만들어 성능 게이트·shadow 통과 후
active 포인터만 교체한다.
