# v3.5 step 2: serve-path integration spec (V_year_saatchi_warm)

작성일: 2026-05-02
배경: v3.5 step 1 결과 — V_year_saatchi_warm 채택 (overall -0.738%p, cold +0.028% ≈ 0). 본 문서 = 코드 변경 X, **production serve-path 변경 spec 만**.

---

## 1. 채택 variant 의 production semantics 재확인

V_year_saatchi_warm activation rule (학습/서빙 정합, 코덱스 P0 fix):
- **Cohort authority** = `match is not None AND match.profile["source"] == "saatchi" AND predictor warm_artist_slugs CONTAINS match.slug`
- **gating source = `match.profile["source"]` only** (external_collector 결과는 비권위)
- year_made 활성: 위 3 조건 동시 충족 시
- 그 외 (unmatched / artsy / saatchi cold / external saatchi/web) → builder output `year_made=0.0, has_year_made=0, work_age=0.0` (옵션 B, §2.3 단일 contract)

> 권위 source: `warm_artist_slugs` artifact (`integrated_v3_filtered_tuned_warm_artists.json`).
> training_count<5 같은 DB count fallback 은 비권위 (Codex 9차 P1 이미 정합 변경됨).

### 1.1 활성 cohort 정의 (학습 기준)
| cohort | n | is_saatchi | warm | year 활성 |
|--------|--:|:----------:|:----:|:---------:|
| saatchi warm | 19,773 | ✓ | ✓ | **✓** |
| saatchi cold | 1,314 | ✓ | ✗ | ✗ |
| artsy warm | 7,289 | ✗ | ✓ | ✗ |
| artsy cold | 0 | ✗ | ✗ | ✗ |

(saatchi cold 1,314 + saatchi warm 19,773 = 21,087 saatchi 전체)

---

## 2. 변경 필요 컴포넌트 4건 (코덱스 P1 R3)

### 2.1 `src/visionai/price_engine/api/primary_schemas.py` — PredictRequest 확장

**현재** (line 7-21):
```python
class PredictRequest(BaseModel):
    artist_name: str = Field(..., min_length=1)
    width_cm: float = Field(..., gt=0, le=500)
    height_cm: float = Field(..., gt=0, le=500)
    medium: str = Field(..., min_length=1)
    title: str | None = Field(None, max_length=200)
    target_market: str = Field("gallery")
    skip_external_lookup: bool = Field(False)
    artist_birth_year: int | None
    artist_total_works: int | None
    solo_count: int | None
    group_count: int | None
    followers: int | None
```

**변경 spec**:
```python
class PredictRequest(BaseModel):
    # ... 기존 필드 그대로 ...

    # NEW (v3.5 step 2): saatchi enrichment 후크
    artwork_id: str | None = Field(
        None,
        description="Saatchi artwork ID (year_made enrichment cache key). 매칭된 saatchi 작품의 ID, 없으면 None"
    )
    artwork_url: str | None = Field(
        None,
        max_length=500,
        description="Saatchi artwork URL (artwork_id 없을 때 fallback enrichment lookup)"
    )
    year_made: int | None = Field(
        None,
        ge=1800,
        le=2030,
        description="작품 제작년도. 클라이언트 직접 제공 시 enrichment fetch skip"
    )
```

**Validation 추가**:
- `year_made` 가 [1800, 2030] 범위 밖 → reject (코덱스 v3.5 plan parser/schema drift risk)
- `artwork_id` + `artwork_url` 둘 다 None 이면 → enrichment 시도 X, fallback (year_made=None)

### 2.2 `src/visionai/price_engine/api/external_collector.py` — artwork-level cache

**현재** (line 11-13):
```python
_cache: dict[str, dict] = {}  # artist_name 단위
_CACHE_MAX = 5000
```

**변경 spec — 별도 module 또는 같은 file 에 추가**:
```python
# Artwork-level year_made cache (v3.5 step 2)
_artwork_year_cache: dict[str, dict] = {}  # key = artwork_id, value = {year_made, fetched_at, ttl_expires_at}
_ARTWORK_CACHE_MAX = 50_000  # saatchi raw 30,607 + 여유
_ARTWORK_CACHE_TTL_SEC = 7 * 86400  # 7 days (year_made 는 거의 안 변함, 단 sold/제거 시 stale)


def get_artwork_year(
    artwork_id: str | None,
    artwork_url: str | None,
) -> tuple[int | None, str]:
    """artwork_id 또는 artwork_url 로 year_made 조회.

    Returns:
        (year_made, source) where source ∈ {'cache_hit', 'fetch_ok', 'fetch_fail',
                                            'no_id', 'parse_invalid'}
    """
    # 1. cache lookup (artwork_id 우선)
    # 2. cache miss → saatchi_detail_enricher.fetch_and_parse_saatchi_detail
    # 3. valid year range [1800, 2030] 검증 → 통과 시 cache 등록
    # 4. fail / invalid → fallback (None)
    ...
```

**Cache key 결정** (코덱스 P1 R3 명시):
- **`artwork_id`** 기반 (artist_name 아님)
- TTL 7 days (sold / page 제거 대응 — 코덱스 v3.5 plan Risk track)
- LRU eviction (50K capacity)
- **artwork_url → artwork_id alias cache** (코덱스 P1): URL-only 요청 시 1차 fetch 결과로 alias 등록 → 같은 URL 재조회 시 cache hit
- **Persistent cache 는 v3.6+ scope** (코덱스 P1 plan 정합): v3.5 step 2 는 in-memory LRU only. DB 영구화는 v3.6 production rollout 직전 별도 PR.

### 2.3 `src/visionai/price_engine/api/primary_feature_builder.py` — year 3종 + disable semantics

**현재** (line 192-196):
```python
features = {
    # ...
    # 작품 (3) — work_age 제거 (서빙=0 드리프트, Codex 4차 P1)
    "is_unique": 1,
    "is_edition": 0,
    "has_depth": 0,
    # ...
}
```

**변경 spec**:
```python
def build_features(
    width_cm: float,
    height_cm: float,
    medium: str,
    artist_profile: dict | None = None,
    target_market: str = "gallery",
    manual_overrides: dict | None = None,
    # NEW (v3.5 step 2)
    is_saatchi_warm: bool = False,  # cohort gating: saatchi & warm 만 True
    year_made: int | None = None,  # enrichment 결과 또는 manual
) -> dict:

    # ... 기존 로직 ...

    # NEW: V_year_saatchi_warm cohort gating (옵션 B 단일 contract: builder=0)
    if is_saatchi_warm and year_made is not None and 1800 <= year_made <= 2030:
        feat_year_made = float(year_made)
        feat_has_year_made = 1
        feat_work_age = float(2026 - year_made)
    else:
        # disable semantics — 학습 시 fillna(0) 후 입력값과 동일 (model contract 고정)
        feat_year_made = 0.0
        feat_has_year_made = 0
        feat_work_age = 0.0

    features = {
        # ... 기존 ...
        # NEW
        "year_made": feat_year_made,
        "has_year_made": feat_has_year_made,
        "work_age": feat_work_age,
    }
```

**Disable semantics — 단일 model-input contract 고정** (코덱스 P0 fix):

**옵션 B 채택 (builder output = 0)**:
- builder 가 disabled cohort 의 출력값을 **명시적 0** 으로 생성
  - `year_made=0.0` (NaN 아님)
  - `has_year_made=0`
  - `work_age=0.0`
- 학습 정합: `prepare_features_with_extra` 가 numeric `fillna(0)` 거치는데, builder 단계에서 이미 0 이면 fillna 무관하게 동일
- predictor 직전 별도 fillna 불필요 → **계약 단순화**

> **Post-prepare model-input parity** (코덱스 fix wording 정정):
> - 학습 builder 출력: `_disable_year_for_mask` → `year_made=NaN, has_year_made=0, work_age=0.0`
> - 학습 prepare: numeric `fillna(0)` → 모델 입력 `year_made=0, has_year_made=0, work_age=0`
> - 서빙 builder 출력 (옵션 B): `year_made=0.0, has_year_made=0, work_age=0.0` 직접
> - **모델 입력 단계에서 정합 1:1 보장** (builder output 자체는 다르지만 model-input level 동일)

### 2.4 `src/visionai/price_engine/api/primary_predictor.py` — feature contract + model artifact

**현재** (line 23-34):
```python
CB_FEATURES = [
    "ho", "ho_power", ..., "source",
]
# 기존 32 features
```

**변경 spec**:
```python
CB_FEATURES = [
    "ho", "ho_power", ..., "source",
    # NEW (v3.5 step 2 V_year_saatchi_warm)
    "year_made",
    "has_year_made",
    "work_age",
]
# 35 features
```

**Model artifact 교체**:
- 새 학습 사이클 필요 (V_year_saatchi_warm 으로 prepare → 5-fold OOF + 전체 학습)
- 산출물: `integrated_v3_5_v_year_saatchi_warm_catboost.cbm` / `_xgboost.json`
- 기존 v3 filtered tuned artifact 와 분리 보관 (rollout 단계별 비교 용)
- model_loader 가 환경변수 또는 config 로 variant 선택

---

## 3. Serve-path integration flow (parser → cache → fallback)

```
PredictRequest 도착
    │
    ├─ NEW: request validation
    │      year_made invalid (out of [1800,2030]) → 400 reject (P1 fix)
    │
    ├─ artist_matcher.match(artist_name)
    │      ├─ matched: predictor warm_artist_slugs CONTAINS slug?
    │      │      ├─ yes → is_warm=True, source=match.profile["source"] (권위)
    │      │      └─ no → is_warm=False, source=match.profile["source"]
    │      └─ not matched → match=None (이후 cohort gating 자동 fail)
    │
    ├─ external_collector.collect(artist_name)  # 작가 프로필 보강 (기존)
    │      └─ source 'saatchi' / 'artsy' / 'web' / 'manual' 반환
    │      └─ **gating 비권위** (코덱스 P0): cohort 결정에 사용 X
    │
    ├─ NEW: cohort gating (P0 fix — 권위 source 명시)
    │      is_saatchi_warm = (
    │          match is not None
    │          AND match.profile["source"] == "saatchi"
    │          AND match.slug IN predictor.warm_artist_slugs
    │      )
    │      # external_collector 의 source 결과는 무시 (권위 X)
    │
    ├─ NEW: year_made 결정 (is_saatchi_warm=True 일 때만 enrichment)
    │      if is_saatchi_warm and req.year_made is None:
    │          year_made, src = get_artwork_year(req.artwork_id, req.artwork_url)
    │          # cache_hit → 즉시
    │          # fetch_ok → ~600ms
    │          # fetch_fail / no_id / parse_invalid → year_made=None (fallback)
    │      else:
    │          year_made = req.year_made  # manual 또는 None
    │
    ├─ build_features(..., is_saatchi_warm=..., year_made=year_made)
    │      └─ disable semantics 자동 적용 (옵션 B: 모두 0 출력)
    │
    └─ predictor.predict(features) → PredictResponse
```

> 같은 cohort gating 로직이 `/api/v1/predict/batch` (코덱스 P0 — `primary_server.py:703`) 도 동일하게 적용. 배치 항목별 매칭 + warm 판정 + saatchi-and-warm intersect → year_made fetch.

---

## 4. Fallback semantics (코덱스 step 2 success criterion 2 + P1 추가)

builder output (옵션 B 채택, 모두 finite 0):

| 상황 | year_made | has_year_made | work_age | 비고 |
|------|----------:|--------------:|---------:|------|
| 매칭 X (unmatched) | 0.0 | 0 | 0.0 | gating fail 자동 |
| **unmatched + external returns saatchi/web profile** | **0.0** | **0** | **0.0** | **gating source = match.profile only, external 비권위 (P0 fix)** |
| Artsy artist (matched) | 0.0 | 0 | 0.0 | gating fail 자동 |
| Saatchi cold (matched) | 0.0 | 0 | 0.0 | gating fail 자동 |
| Saatchi warm + year_made manual valid | float(year_made) | 1 | 2026-year_made | happy path 1 |
| **Saatchi warm + year_made manual invalid (out of [1800,2030])** | **400 reject** | **-** | **-** | **request validation P1 fix** |
| Saatchi warm + cache hit | float(cached_year) | 1 | 2026-year | happy path 2 |
| Saatchi warm + fetch ok | float(parsed_year) | 1 | 2026-year | happy path 3 |
| Saatchi warm + fetch 5xx/timeout | 0.0 | 0 | 0.0 | graceful fallback |
| Saatchi warm + parse invalid (out of [1800,2030]) | 0.0 | 0 | 0.0 | graceful fallback |
| Saatchi warm + no artwork_id/url | 0.0 | 0 | 0.0 | graceful fallback |

**불변 조건** (학습/서빙 정합 보장, 옵션 B):
- `has_year_made=1 ⟺ year_made > 0 ⟺ work_age > 0` (모두 finite)
- `is_saatchi_warm=False ⟹ year_made=0, has_year_made=0, work_age=0` (강제)
- builder output 은 항상 finite (NaN 없음) — predictor 직전 별도 fillna 불필요

---

## 5. Latency budget (코덱스 step 2 success criterion 3)

| 단계 | p50 | p95 | 비고 |
|------|----:|----:|------|
| Cache hit | 0.5 ms | **5 ms** | in-memory dict lookup |
| Cache miss + fetch ok | 200 ms | **600 ms** | saatchi detail page (v3.4-2 step 4 검증) |
| Cache miss + fetch timeout | 1000 ms | 1500 ms | timeout=20s 가 아니라 enrichment 측 자체 timeout=1.5s 필요 |
| Disable (gating fail) | 0 ms | 0 ms | enrichment skip |

**SLA 결정**:
- 전체 predict 추가 latency: **p95 ≤ 600 ms (cache miss only)**, p50 ≤ 50 ms (cache hit dominant)
- Cache miss spike 대응 (코덱스 Risk track): rollout 5% 단계에서 실측 후 SLA 재검증

---

## 6. Cohort assignment correctness (코덱스 step 2 success criterion 4)

**임계 ≥ 99%**: production 의 `is_saatchi_warm` 결정이 학습 시 cohort 와 일치.

### 6.1 검증 가능한 cases (코덱스 P0 fix: cohort authority = warm_artist_slugs + match.profile.source)
| Case | 학습 시 | 서빙 시 | 정합? |
|------|---------|---------|:----:|
| matched + slug ∈ warm_artist_slugs + source='saatchi' | wmask=1, source='saatchi' | is_saatchi_warm=True | ✓ |
| matched + slug ∉ warm_artist_slugs + source='saatchi' | wmask=0, source='saatchi' | is_saatchi_warm=False (cold) | ✓ |
| matched + source='artsy' (warm/cold 무관) | source='artsy' | is_saatchi_warm=False | ✓ |
| **unmatched (외부 collector saatchi/web/artsy/manual 무관)** | n/a (학습 X) | match=None → is_saatchi_warm=False | ✓ (P0 의도된 fallback) |

### 6.2 Risk: unmatched 요청
- 매칭 실패 saatchi 요청 (artist_name 만 들어옴) → `is_saatchi_warm=False` 자동 (warm=False)
- year_made 비활성 = **안전 측면 정확** (코덱스 P1 명시)
- 단 coverage 감소 (saatchi enrichment 잠재 효과 X)
- → step 2 명시: **"매칭 실패 saatchi 요청은 무조건 year off"** (의도된 fallback)

### 6.3 측정 plan
- Rollout 5% 단계에서 logging:
  - `request_id, matched_bool, match_profile_source, slug_in_warm_set, is_saatchi_warm, external_collector_source, year_made_used, year_made_route` (route ∈ {manual, manual_seed_cache_write, cache_hit, fetch_ok, fetch_fail, no_id, parse_invalid, disabled, rate_limited} — v3.6 PR10 step3 spec 와 정합)
- `external_collector_source` 도메인: `artsy / saatchi / web / manual / none` (코덱스 P1 — `web` 포함)
- 일별 dashboard 에서 `is_saatchi_warm` 분포 + 학습 시 분포 비교
- Discrepancy > 1% → rollout pause + 원인 조사

---

## 6.4 Batch endpoint 정합 (코덱스 P0 fix)

`POST /api/v1/predict/batch` (`primary_server.py:703`) 도 동일 cohort gating + 동일 schema:
- 배치 입력 항목별 `artwork_id` / `artwork_url` / `year_made` 필드 (BatchPredictRequest 의 each item)
- 각 항목별 매칭 + slug ∈ warm_artist_slugs + source='saatchi' intersect 검증
- 작가 중복 시 외부 수집 1회만 (기존 정책 유지) + artwork enrichment 는 artwork 단위로 별도 cache
- batch 결과 logging 도 단건과 동일 schema (request_id 단위)

→ 단건 + 배치 모두 동일 contract. spec 단일.

---

## 6.5 Artifact bundle 규약 (코덱스 P0 fix)

V_year_saatchi_warm 채택 시 새 model artifact bundle (`primary_predictor.py:109` fail-closed):

| File | 현재 (v3 filtered tuned) | 신규 (v3.5 V_year_saatchi_warm) |
|------|--------------------------|----------------------------------|
| CatBoost model | `integrated_v3_filtered_tuned_catboost.cbm` | `integrated_v3_5_v_year_saatchi_warm_catboost.cbm` |
| XGBoost model | `integrated_v3_filtered_tuned_xgboost.json` | `integrated_v3_5_v_year_saatchi_warm_xgboost.json` |
| Warm artist set | `integrated_v3_filtered_tuned_warm_artists.json` | `integrated_v3_5_v_year_saatchi_warm_warm_artists.json` |
| XGB label maps | `integrated_v3_filtered_tuned_xgboost_label_maps.json` | `integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json` |
| Source calibration | `integrated_v3_filtered_tuned_source_calibration.json` | `integrated_v3_5_v_year_saatchi_warm_source_calibration.json` |

**규약**:
- 5 파일 모두 fail-closed (하나 누락 → RuntimeError)
- 기존 v3 filtered tuned bundle 과 분리 보관 (rollout 5% 단계 비교 용)
- `model_loader` 가 환경변수 `MODEL_VARIANT=v3_filtered_tuned | v3_5_v_year_saatchi_warm` 으로 선택
- Atomic load: 5 파일 모두 검증 후 instance state swap (기존 패턴 그대로)

### Side artifact 규약 (코덱스 P0 #4)
- `metrics.json` (`primary_server.py:431` 의 `model_info` 참조): 같은 prefix 로 함께 관리
  - 신규: `integrated_v3_5_v_year_saatchi_warm_metrics.json`
  - 비-fail-closed (없으면 model_info 만 비어있음, 서비스 자체는 동작)
- `calibration JSON` 의 `model_target` field (`primary_predictor.py:208` 의 검증):
  - 현재 `integrated_v3_filtered_tuned` 고정 검증
  - 신규 variant 시 `model_target == "v3_5_v_year_saatchi_warm"` 정합 검증으로 교체 (variant-aware)
  - `MODEL_VARIANT` env var 와 calibration `model_target` 일치 확인 (mismatch → RuntimeError)

새 학습은 v3.5 step 4 monitoring 직전 별도 commit (out of scope §10).

---

## 7. Step 2 success criterion 충족 여부

| Criterion | 상태 | 비고 |
|-----------|:----:|------|
| 1. Serve-path integration spec 확정 | ✅ | §3 flow 명시 |
| 2. Fallback semantics 확정 | ✅ | §4 9 cases + 불변 조건 |
| 3. Latency p95 budget 수치 | ✅ | hit ≤ 5ms, miss ≤ 600ms |
| 4. Cohort assignment correctness ≥ 99% | ✅ | §6 측정 plan, unmatched 자동 fallback |

→ **v3.5 step 2 close 가능** (코드 변경 X, spec 완료).

---

## 8. v3.5 step 3 진행 권장 (코덱스 plan)

step 2 완료 → step 3 (enrichment / latency / coverage trade-off):
- Cache key 단위 결정됨 (artwork_id) — 추정 → 측정 plan 으로 격하 (코덱스 P1)
- 시나리오 비교 (cache-first vs sync vs async preload)
- 비용/효율 정량화 + step 4 monitoring 설계 input

---

## 9. v3.5 진행도

- ✅ Step 1: cohort gating ablation (V_year_saatchi_warm 채택)
- ✅ **Step 2: serve-path integration spec** ← 본 문서
- ⏭️ Step 3: enrichment / latency / coverage trade-off
- Step 4: gated rollout drift monitoring

---

## 10. Out of scope (다음 단계)

본 step 2 = **spec only close** (v3.5 plan §3 정의 그대로). 실제 구현은 별도 PR.

### v3.6 production rollout 직전 implementation checklist (코덱스 P0 #4 fix)
실제 코드 변경 PR 전 체크리스트:
- [ ] `primary_schemas.py`: `artwork_id`, `artwork_url`, `year_made` 필드 + validation
- [ ] `primary_schemas.py` BatchPredictRequest 도 동일 필드 추가
- [ ] `external_collector.py`: `_artwork_year_cache` (artwork_id key, URL alias) + `get_artwork_year`
- [ ] `primary_feature_builder.py`: `is_saatchi_warm`, `year_made` 인자 + 옵션 B (0.0 output)
- [ ] `primary_predictor.py`: CB_FEATURES + 3, 5-file fail-closed bundle, `MODEL_VARIANT` env var
- [ ] `primary_predictor.py`: `model_target` variant-aware 검증
- [ ] `primary_server.py:431` `model_info` 의 metrics.json prefix 정합
- [ ] `primary_server.py:575` (단건) + `:703` (batch) 의 cohort gating 통합
- [ ] 단건/배치 logging schema: `is_saatchi_warm`, `match_profile_source`, `slug_in_warm_set`, `year_made_route`, `external_collector_source`
- [ ] Integration tests: 10 fallback cases (§4) 통과
- [ ] Smoke benchmark: cache hit p95 ≤ 5ms, miss ≤ 600ms 검증

### v3.5 step 4 monitoring 직전 별도 commit
- Model retraining (V_year_saatchi_warm 새 5-file bundle + metrics.json 산출)
- Calibration JSON 의 `model_target = "v3_5_v_year_saatchi_warm"` 으로 재생성

### 그 외 out of scope
- Cache TTL invalidation 정책 세부 (sold 작품 처리) — Step 4 monitoring 에서 검토
- DB 영구 cache (Persistent layer) — v3.6+ optimization backlog (코덱스 P1)
