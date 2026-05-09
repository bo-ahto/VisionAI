# Operational Adoption PR2A — Source Router (default OFF / decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle` (또는 별도 PR2A branch)
> **연계**: PR1 commit `f74f73b` (artifact bundle 산출 완료)
> **Decision binding**: ✅ YES (inference code 변경 / 다만 default OFF / 운영 영향 X 영역 의 의무 영역 의 의무 영역 의 의무)
>
> ⚠️ **본 cycle scope = PR2A** (code change + tests / default OFF / deploy 영역 의 의무 영역 의 의무 X). PR2B (deploy/env wiring + shadow/canary rollout) = 별도 cycle.

## 1. Goal

Source-conditional CHAMPION (commit `8dcc588`) → 운영 적용 PR2A:
1. **Multi-predictor loader/router** (3 predictor eager-load: artsy / saatchi / unified fallback)
2. **Source routing logic** (matched profile.source 권위적 / unmatched → unified)
3. **Rollout flags** (default `OFF` / serving 영향 X)
4. **Observability**: `routing_source`, `routing_reason`, `routed_variant`
5. **Regression tests**: matched routing / unmatched fallback / fail-closed / single+batch parity

⚠️ **default OFF**: PR2A merge → 운영 동작 영역 의 의무 영역 의 의무 영역 의 의무 변경 X (current `MODEL_VARIANT=v3_filtered_tuned` 영역 의 의무 영역 의 의무 영역 의 의무 정합). **PR2B** 별도 cycle 영역 의 의무 영역 의 의무 = `SOURCE_ROUTER_MODE=shadow/canary/on` 영역 의 의무 영역 의 의무 활성화.

## 2. Method (코덱스 사전 자문 권고안 정합)

### 2.1 SUPPORTED_VARIANTS 추가

`primary_predictor.py:73`:
```python
SUPPORTED_VARIANTS: dict[str, dict] = {
    "v3_filtered_tuned": {  # 기존 unified (운영 default + fallback)
        "prefix": "integrated_v3_filtered_tuned",
        "cb_features": CB_FEATURES_BASE,
        "expected_target": "integrated_v3_filtered_tuned",
    },
    "v3_5_v_year_saatchi_warm": {  # 기존 (변경 X)
        ...
    },
    # PR2A 추가 (source-conditional / 32f / 운영 best_params)
    "source_conditional_v1_artsy": {
        "prefix": "source_conditional_v1_artsy",
        "cb_features": CB_FEATURES_BASE,
        "expected_target": "source_conditional_v1_artsy",
    },
    "source_conditional_v1_saatchi": {
        "prefix": "source_conditional_v1_saatchi",
        "cb_features": CB_FEATURES_BASE,
        "expected_target": "source_conditional_v1_saatchi",
    },
}
```

### 2.2 Source Router (server-side / 신규 module)

**위치**: `src/visionai/price_engine/api/source_router.py` (신규)

**Spec**:
```python
class SourceRouter:
    """3 predictor eager-load + row-level dispatch + flag-gated rollout."""

    def __init__(self, model_dir: Path):
        self.unified = PrimaryPredictor()
        self.unified.load_models(model_dir, variant="v3_filtered_tuned")
        self.artsy = None
        self.saatchi = None
        # source-conditional bundle 영역 의 의무 영역 의 의무 = optional load (mode=off 영역 의 의무 영역 의 의무 X)
        if os.environ.get("SOURCE_ROUTER_MODE", "off") != "off":
            self.artsy = PrimaryPredictor()
            self.artsy.load_models(model_dir, variant="source_conditional_v1_artsy")
            self.saatchi = PrimaryPredictor()
            self.saatchi.load_models(model_dir, variant="source_conditional_v1_saatchi")
        self.mode = os.environ.get("SOURCE_ROUTER_MODE", "off")
        self.percent = int(os.environ.get("SOURCE_ROUTER_PERCENT", "0"))
        self.rule_version = os.environ.get("SOURCE_ROUTER_RULE_VERSION", "v1")

    def route(self, match_result: MatchResult, request_id: str) -> tuple[Predictor, str, str]:
        """Returns (predictor, routed_variant, routing_reason)."""
        if self.mode == "off":
            return self.unified, "v3_filtered_tuned", "router_off"
        # ... cohort hash + match source 권위 분기 + fallback
```

### 2.3 Rollout flags (locked / default OFF)

| Env var | Values | Default | 의미 |
|---|---|---|---|
| `SOURCE_ROUTER_MODE` | `off / shadow / canary / on` | **`off`** | router 활성화 단계 |
| `SOURCE_ROUTER_PERCENT` | `0-100` | `0` | canary % (mode=canary 영역 의 의무 영역 의 의무) |
| `SOURCE_ROUTER_RULE_VERSION` | `v1` (default) | `v1` | rule pinning |

**Cohort assignment** (deterministic):
- key = `request.artist_slug or request.fingerprint`
- hash = SHA-256 % 100
- routed if hash < `SOURCE_ROUTER_PERCENT`

### 2.4 Routing logic (locked)

```
input row + match result →
  if SOURCE_ROUTER_MODE == "off":
    → unified (v3_filtered_tuned)
  if SOURCE_ROUTER_MODE == "shadow":
    primary = unified (운영 영향 X)
    shadow = artsy / saatchi / unified (decision log only)
  if SOURCE_ROUTER_MODE == "canary":
    if cohort hash < PERCENT:
      → matched + profile.source==artsy → artsy bundle
      → matched + profile.source==saatchi → saatchi bundle
      → unmatched / unknown / manual / web / NaN → unified fallback
    else:
      → unified
  if SOURCE_ROUTER_MODE == "on":
    → 동일 routing matrix (cohort 100%)
```

⚠️ **Authority**: source = **`match_result.profile.source`** (권위적 / unmatched 영역 의 의무 영역 의 의무 X). external collector / `request.source` 영역 의 의무 영역 의 의무 영역 의 의무 X (PR2 사전 자문 정합).

### 2.5 Observability

Response/log 영역 의 의무 영역 의 의무 추가:
- `routing_source`: artsy / saatchi / unified
- `routing_reason`: matched_artsy / matched_saatchi / unmatched_fallback / router_off / cohort_skipped
- `routed_variant`: source_conditional_v1_artsy / source_conditional_v1_saatchi / v3_filtered_tuned
- `model_info`: response 영역 의 의무 영역 의 의무 routed bundle 영역 의 의무 영역 의 의무 식별

### 2.6 Regression tests (의무)

```python
def test_router_off_default():
    """default OFF / 모든 row → unified."""

def test_router_canary_artsy_matched():
    """matched + profile.source=artsy → artsy bundle."""

def test_router_canary_saatchi_matched():
    """matched + profile.source=saatchi → saatchi bundle."""

def test_router_canary_unmatched_fallback():
    """unmatched → unified fallback."""

def test_router_canary_manual_fallback():
    """match.profile.source=manual → unified fallback."""

def test_router_fail_closed_artsy_missing():
    """artsy bundle 누락 시 startup fail-closed."""

def test_router_fail_closed_saatchi_missing():
    """saatchi bundle 누락 시 startup fail-closed."""

def test_router_fail_closed_unified_missing():
    """unified fallback 누락 시 startup fail-closed."""

def test_router_no_op_calibration_parity():
    """no-op calibration → unified prediction과 동일 (parity check)."""

def test_router_batch_endpoint_consistency():
    """batch endpoint = single endpoint 동일 routing matrix."""

def test_router_logging_routed_variant():
    """response/log 영역 routing_source / routing_reason / routed_variant 포함."""

def test_router_cohort_deterministic():
    """동일 request_id → 동일 cohort hash (deterministic)."""

def test_router_shadow_mode_no_serving_change():
    """shadow mode = serving 영향 X / decision log only."""
```

## 3. Decision Criterion (locked)

**채택 (PASS / merge 가능)**:
- ✅ All regression tests PASS
- ✅ default OFF 동작 = current behavior 동일 (backward compat)
- ✅ ruff check + mypy 통과
- ✅ 코덱스 사후 검수 GO

**비채택 (FAIL / merge X)**:
- ❌ regression tests FAIL
- ❌ default OFF 영역 의 의무 영역 의 의무 영역 의 의무 current behavior 변경
- ❌ lint / mypy 실패

## 4. Out-of-scope (PR2B / 다음 cycle)

❌ **본 cycle scope X**:
- Deploy/env wiring (`SOURCE_ROUTER_MODE` 활성화)
- Shadow/canary rollout (실제 traffic 영향)
- Production monitoring (slice drift / oof 모니터링)
- Per-source calibration 재산출 (Phase 2 별도 prereg)
- Per-source HP tuning (Phase 3 별도 prereg)

## 5. 한계 / Risk

- **default OFF**: PR2A merge 영역 의 의무 영역 의 의무 영역 의 의무 = 운영 행동 변경 X
- **Memory + startup time**: 3 predictor eager-load 영역 의 의무 영역 의 의무 = ~3배 (다만 mode=off 영역 의 의무 영역 의 의무 영역 의 의무 unified만 load)
- **API schema**: routed_variant 등 추가 필드 = additive only (backward compat)
- **/api/v1/model/info**: 단일 predictor 가정 영역 의 의무 영역 의 의무 영역 의 의무 → router 도입 시 의미 재정의 의무 (P2)
- **재현성**: PR2B rollout 시 실제 운영 traffic 영역 의 의무 영역 의 의무 영역 의 의무 monitoring 의무

## 6. 진행 일정

| 단계 | 영역 | 시간 |
|---|---|---:|
| prereg doc + 코덱스 사전 자문 (round 1) | 본 doc | 0.5 시간 |
| Code: SUPPORTED_VARIANTS 추가 + source_router.py | predictor + router | 1 시간 |
| Code: primary_server.py routing integration | server endpoint 수정 | 1 시간 |
| Tests: regression suite | pytest | 1 시간 |
| ruff + mypy + 코덱스 사후 | | 1 시간 |
| commit + PR | | 0.5 시간 |
| **합계** | — | **~5 시간** |

## 7. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | GO with P2 (option b / phased PR2A) |
| 2차 사후 검수 (예정) | code 완료 + tests pass 후 |
