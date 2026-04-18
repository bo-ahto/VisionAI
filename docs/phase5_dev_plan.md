# Phase 5 개발 기획서 (v6.0)

> **기반 문서**: `phase5_accuracy_plan.md` v2.0 (Codex PASS)
> **작성일**: 2026-03-29 | **개정일**: 2026-03-29 (v6.0 — Codex 5차 리뷰 MAJOR 1건 반영)
> **목표**: Test MdAPE ≤ 31~32%, Val-Test gap ≤ 2.5%p, Cold MdAPE ≤ 55~58%
> **핵심 원칙**: Test-first KPI, ablation 기반, Strict/Distilled 2-트랙

---

## 0. 착수 전 준비

### 0.1 신규 의존성

```toml
# pyproject.toml — 기존 dependencies 배열에 추가
dependencies = [
    # ... 기존 torch, torchvision, opencv, pillow, numpy ...
    "requests>=2.31",        # 공공 API (ECOS, KOSIS)
    "rapidfuzz>=3.0",        # 작가명 fuzzy matching
    "beautifulsoup4>=4.12",  # Seoul Auction HTML 파싱
]

[project.optional-dependencies]
dev = [
    # ... 기존 ruff, mypy, pytest ...
    "scipy>=1.11",      # paired t-test (ablation)
    "shap>=0.43",       # feature attribution drift
    "matplotlib>=3.8",  # 진단 플롯
]
```

### 0.2 디렉토리 구조 (신규 파일)

```
src/visionai/price_engine/
├── features/
│   ├── macro_indicators.py          # Sprint 1
│   ├── artist_similarity.py         # Sprint 2
│   └── track_config.py              # Sprint 0: Strict/Distilled 피처 분리
├── estimate_generator/
│   ├── conformal_calibrator.py      # Sprint 3: CQR
│   └── distillation.py              # Sprint 3: Knowledge Distillation
scripts/
├── diagnose_gap.py                  # Sprint 0
├── collectors/
│   ├── collect_macro_data.py        # Sprint 1
│   ├── scrape_seoul_auction.py      # Sprint 1
│   └── collect_namuwiki.py          # Sprint 1
├── train_distilled_model.py         # Sprint 3
tests/price_engine/
├── test_gap_diagnosis.py            # Sprint 0
├── test_gap_leak_audit.py           # Sprint 0: leak audit
├── test_macro_indicators.py         # Sprint 1
├── test_entity_resolution.py        # Sprint 1: ER 규칙
├── test_artist_similarity.py        # Sprint 2
├── test_conformal_calibrator.py     # Sprint 3
├── test_distillation.py             # Sprint 3
├── test_track_isolation.py          # Sprint 3: 2-트랙 격리
├── test_gate_report.py              # Sprint 4: Gate 1:1
├── test_holdout_windows.py          # Sprint 4: 3-윈도우
```

### 0.3 Phase 1-4 통합 지점 (실제 파일 기준)

| 기존 파일 (실제 경로) | 관계 | Phase 5 대응 | Artifact 규칙 |
|---------------------|------|-------------|-------------|
| `features/hedonic_stats.py` (714 lines) | 확장 | cross_market, profile 함수 추가 | 기존 유지, 함수만 추가 |
| `estimate_generator/hedonic_features.py` (15.8KB) | 확장 | HEDONIC_FEATURES 리스트 확장 | 기존 49개 유지 + 신규 추가 |
| `estimate_generator/cold_start.py` (6.8KB) | 확장 | `get_cold_start_fallback_v2()` 추가 | 기존 `get_cold_start_fallback()` 유지 (하위 호환) |
| `estimate_generator/quantile_calibrator.py` (6.8KB) | **유지** | 신규 `conformal_calibrator.py` 병행 | 기존 유지, generator.py에서 선택 |
| `estimate_generator/generator.py` (8.4KB) | 확장 | `calibrator_type` 파라미터 추가 | "additive" (기본) / "cqr" 선택 |
| `api/server.py:_build_estimate_input()` (L282~L349) | 확장 | 신규 피처 컬럼 추가 | 기존 49개 기본값 유지 + 신규 |
| `scripts/collectors/integrate_external.py` | **유지** | 신규 `integrate_external_v2.py` 병행 | 기존 유지, v2가 확장 |
| `models/predictor.py:BASELINE_FEATURES` | **변경 없음** | Phase 1-2 모델 불변 | Teacher artifact 고정 |

### 0.4 Artifact 명명 규칙

| Artifact | 파일명 | 트랙 | 로더 |
|---------|--------|------|------|
| Phase 1-2 Teacher | `target_transform_v1.cbm` | (teacher) | `predictor.py` |
| Strict Student | `strict_student.cbm` | Strict | `distillation.py` |
| Distilled Student | `distilled_student.cbm` | Distilled | `distillation.py` |
| Teacher OOF | `teacher_oof.parquet` | Distilled train only | `distillation.py` |
| CQR Calibrator | `conformal_calibrator.pkl` | 공통 | `conformal_calibrator.py` |
| 기존 Quantile Calibrator | `quantile_calibrator.pkl` | 공통 (fallback) | `quantile_calibrator.py` |

### 0.5 Strict / Distilled 2-트랙 코드 분리

```python
# features/track_config.py
from __future__ import annotations
from enum import Enum

class Track(str, Enum):
    STRICT = "strict"
    DISTILLED = "distilled"

# Strict: 추정가 파생 신호 일체 금지
STRICT_FEATURES: list[str] = [
    # Phase 3 hedonic 49개 + Phase 5 매크로/외부/similarity
    # global_estimate_avg 제외
]

# Distilled: Strict + teacher soft target (train only)
DISTILLED_TRAIN_ONLY_FEATURES: list[str] = [
    "teacher_pred_oof",     # OOF teacher prediction (train only)
    "global_estimate_avg",  # 외부 추정가 통계 (train only)
]

# Inference: 두 트랙 모두 동일 (추정가/teacher 신호 없음)
INFERENCE_FEATURES: list[str] = STRICT_FEATURES  # 동일
```

### 0.6 데이터 분할 전략

기존 4-way split 유지 + 3개 홀드아웃 윈도우:
- Train: 회차 ≤ 453 (36,751건)
- Calib: 454~462 (1,625건)
- Valid: 463~474 (2,588건)
- Test: 475~486 (2,902건)
- Window 1: Train ≤ 462, Test 463~470
- Window 2: Train ≤ 470, Test 471~478
- Window 3: Train ≤ 478, Test 479~486

---

## 1. Sprint 0: Val-Test Gap 진단 (1주)

### 1.1 작업 목록

| # | File | Content | 기획서 |
|---|------|---------|--------|
| 0-1 | `scripts/diagnose_gap.py` | 시점별/세그먼트별 MdAPE 곡선 | S0 |
| 0-2 | `scripts/diagnose_gap.py` | Feature PSI 계산 (valid→test) | S0 |
| 0-3 | `scripts/diagnose_gap.py` | Missingness drift | S0 |
| 0-4 | `scripts/diagnose_gap.py` | Cold 비중/가격대 drift | S0 |
| 0-5 | `scripts/diagnose_gap.py` | Leak audit (feature lineage 포함) | S0 |
| 0-6 | `features/track_config.py` | STRICT/DISTILLED 피처 상수 정의 | S0 |
| 0-7 | `test_gap_diagnosis.py` | PSI/drift 단위 테스트 (6개) | — |
| 0-8 | `test_gap_leak_audit.py` | Leak audit 테스트 (4개) | — |

### 1.2 파일 상세 명세

```python
# scripts/diagnose_gap.py
def compute_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float: ...
def compute_missingness_drift(df_valid, df_test, features) -> pd.DataFrame: ...
def compute_segment_performance(df, y_pred, y_true, segment_col) -> dict: ...
def compute_time_performance_curve(df, y_pred, y_true, session_col="회차") -> pd.DataFrame: ...
def run_leak_audit(
    df: pd.DataFrame, feature_builders: dict[str, Callable],
    session_col: str = "회차",
) -> list[dict[str, str]]:
    """각 피처 빌더의 cutoff 준수 여부를 검증. feature_builders에 빌더 함수 전달."""
def main() -> None:
    """→ model_test_results/gap_diagnosis.json"""
```

### 1.3 테스트 명세 (Gate 매핑 포함)

| Test File | Test | 기대 결과 | Gate |
|-----------|------|----------|------|
| test_gap_diagnosis.py | test_psi_identical | PSI < 0.01 | — |
| test_gap_diagnosis.py | test_psi_shifted | PSI > 0.1 | — |
| test_gap_diagnosis.py | test_missingness_no_change | drift ≈ 0 | — |
| test_gap_diagnosis.py | test_missingness_increase | drift > 0 | — |
| test_gap_diagnosis.py | test_segment_keys | mdape, r2, n | — |
| test_gap_diagnosis.py | test_time_curve_sorted | session 오름차순 | — |
| test_gap_leak_audit.py | test_leak_audit_clean | 의심 피처 0개 | G7 |
| test_gap_leak_audit.py | test_leak_audit_detects_future | 의심 피처 ≥ 1 | G7 |
| test_gap_leak_audit.py | test_holdout_windows_gap | Gap < valid × 1.1 | — |
| test_gap_leak_audit.py | test_track_config_no_estimate | STRICT에 estimate 0개 | G10 |

### 1.4 Sprint 0 완료 조건
- □ `gap_diagnosis.json` 생성 (PSI, drift, leak 결과)
- □ 원인-해결 매핑 작성
- □ `track_config.py` 정의 완료
- □ 10개 테스트 통과
- □ **Gate G7** (test_g7_leakage)

### 1.5 병렬화

```
0-1 성능곡선 ─┐
0-2 PSI      ─┤─→ 0-5 Leak audit
0-3 Drift    ─┤
0-4 분포분석  ─┘
0-6 track_config (독립)
0-7, 0-8 테스트 (0-1~0-6 완료 후)
```

---

## 2. Sprint 1: 외부 데이터 수집 + 매크로 통합 (2~3주)

### 2.1 작업 목록

| # | File | Content | 기획서 |
|---|------|---------|--------|
| 1-1 | `collectors/collect_macro_data.py` | ECOS/KOSIS API 수집 | 전략1 |
| 1-2 | `collectors/scrape_seoul_auction.py` | Seoul Auction 스크래핑 | 전략1 |
| 1-3 | `scrape_artsy_auctions.py` 확장 | Artsy 100+ 작가 | 전략1 |
| 1-4 | `collectors/collect_namuwiki.py` | NamuWiki 프로필 | 전략1 |
| 1-5 | `features/macro_indicators.py` | 매크로 피처 함수 | 전략5 |
| 1-6 | `features/hedonic_stats.py` 확장 | 외부 데이터 피처 | 전략3 |
| 1-7 | `hedonic_features.py` 확장 | HEDONIC_FEATURES 확장 | — |
| 1-8 | `collectors/integrate_external_v2.py` | Entity Resolution | 5.4 |
| 1-9 | `test_macro_indicators.py` | 매크로 테스트 | — |
| 1-10 | `test_entity_resolution.py` | ER 테스트 | — |
| 1-11 | 재학습 + Strict ablation | metrics | — |

### 2.2 Entity Resolution 상세 명세

```python
# scripts/collectors/integrate_external_v2.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ResolvedArtistMatch:
    """작가명 매칭 결과."""
    artist_id_canonical: str     # K-Auction 기준 정규화명
    source_name: str             # 소스 원본명
    source: str                  # "artsy" | "seoul_auction" | "namuwiki"
    match_type: str              # "exact" | "fuzzy"
    confidence: float            # 0.0~1.0

@dataclass
class ExternalLotRecord:
    """외부 경매 lot 정규화 결과."""
    artist_id_canonical: str
    artwork_title: str
    hammer_price_krw: float      # 통일된 KRW hammer price
    currency_original: str
    fx_rate_at_sale_month: float
    premium_included: bool
    unsold_flag: bool
    auction_house_norm: str
    auction_date: str
    source_url: str
    scrape_timestamp: str
    name_match_confidence: float

def resolve_artist_identity(
    source_name: str, source: str,
    kauction_names: list[str], slug_mapping: dict[str, str],
) -> ResolvedArtistMatch | None:
    """소스별 작가명 매칭.
    - Artsy: slug exact → fuzzy (rapidfuzz, threshold 0.85)
    - Seoul Auction: 한글 exact only
    - NamuWiki: exact → fuzzy 보완
    """

def deduplicate_external_lots(lots: list[ExternalLotRecord]) -> list[ExternalLotRecord]:
    """중복 제거. composite key: (artist_id_canonical, artwork_title, auction_date, auction_house_norm)."""

def build_manual_review_queue(
    matches: list[ResolvedArtistMatch], threshold_low: float = 0.85, threshold_high: float = 0.95,
) -> list[ResolvedArtistMatch]:
    """confidence 0.85~0.95 구간의 매칭을 수동 검토 큐로 분리."""

def normalize_hammer_price(
    price: float, currency: str, auction_date: str,
    fx_df: pd.DataFrame, premium_included: bool = False,
) -> float:
    """KRW hammer price 통일. premium_included면 /1.15 차감."""
```

### 2.3 테스트 명세 (Gate 매핑)

| Test File | Test | 기대 결과 | Gate |
|-----------|------|----------|------|
| test_macro_indicators.py | test_join_lag_1m | 3월→2월 지표 | — |
| test_macro_indicators.py | test_missing_month_ffill | forward-fill | — |
| test_macro_indicators.py | test_feature_count_7 | 7개 피처 | — |
| test_macro_indicators.py | test_macro_months_ge_12 | CSV 행 ≥ 12개월 | G16 |
| test_entity_resolution.py | test_artsy_slug_exact | slug exact match | — |
| test_entity_resolution.py | test_artsy_fuzzy_threshold | confidence ≥ 0.85 | — |
| test_entity_resolution.py | test_match_precision_ge_95 | 수동 검증 100건 대비 precision ≥ 95% | G15 |
| test_entity_resolution.py | test_seoul_exact_only | exact match only | — |
| test_entity_resolution.py | test_dedup_composite_key | unique 보장 | — |
| test_entity_resolution.py | test_manual_review_queue | 0.85~0.95 분리 | — |
| test_entity_resolution.py | test_hammer_usd_to_krw | 환율 × price | — |
| test_entity_resolution.py | test_premium_deduction | /1.15 | — |
| test_entity_resolution.py | test_unsold_flag_preserved | unsold 유지 | — |
| test_entity_resolution.py | test_required_fields | 필수 컬럼 존재 | — |

### 2.4 Sprint 1 완료 조건
- □ `macro_monthly.csv` (12개월+) → `model_test_results/macro_monthly.csv`
- □ 외부 수집 2개+ (Artsy/Seoul/NamuWiki)
- □ Entity resolution precision ≥ 95% (test_entity_resolution 통과)
- □ Cold artist fill-rate 측정 (매칭 성공률 ≥ 15%)
- □ HEDONIC_FEATURES 확장 (매크로 7 + 외부 5~8)
- □ Strict 트랙 ablation 보고 (전후 MdAPE 차이)
- □ 12개 테스트 통과
- □ **Gate G15** (precision ≥ 95%), **G16** (12개월+)

### 2.5 병렬화

```
1-1 ECOS ──────┐
1-2 Seoul ─────┤─→ 1-8 Entity Resolution ─→ 1-7 피처통합 ─→ 1-11 재학습
1-3 Artsy ─────┤
1-4 NamuWiki ──┘
1-5 macro_indicators (1-1 후)
1-6 hedonic_stats (1-8 후)
1-9, 1-10 테스트 (1-5, 1-6, 1-8 후)
```

---

## 3. Sprint 2: Artist Similarity + Cold Start 5-tier (2주)

### 3.1 작업 목록

| # | File | Content | 기획서 |
|---|------|---------|--------|
| 2-1 | `features/artist_similarity.py` | K-NN 유사 작가 | 전략2 |
| 2-2 | `estimate_generator/cold_start.py` 확장 | 5-tier fallback | 전략2 |
| 2-3 | `hedonic_features.py` 확장 | similarity 피처 통합 | — |
| 2-4 | `test_artist_similarity.py` | similarity 테스트 (7개) | — |
| 2-5 | `test_cold_start_estimate.py` 확장 | 5-tier 테스트 (5개) | — |
| 2-6 | Strict 트랙 재학습 | Cold MdAPE 측정 | — |

### 3.2 파일 명세 (v1.0 유지 + 보강)

`features/artist_similarity.py`: `SimilarArtist` dataclass, `build_artist_feature_vectors()`, `find_similar_artists()`, `compute_similarity_features()` — v1.0과 동일.

`cold_start.py` 확장: `get_cold_start_fallback_v2()` 5-tier — v1.0과 동일.

### 3.3 테스트 명세 (Gate 매핑)

| Test File | Test | 기대 결과 | Gate |
|-----------|------|----------|------|
| test_artist_similarity.py | test_vectors_feature_count | 5개 피처 | — |
| test_artist_similarity.py | test_similar_medium_filter | 동일 매체만 | — |
| test_artist_similarity.py | test_similar_k_count | len ≤ K | — |
| test_artist_similarity.py | test_similarity_features_keys | 4개 키 | — |
| test_artist_similarity.py | test_distance_sorted | 오름차순 | — |
| test_artist_similarity.py | test_cold_artist_gets_similar | cold 작가 매칭 | — |
| test_artist_similarity.py | test_fallback_usage_rate | 사용률 < 40% | — |
| test_artist_similarity.py | test_cold_subgroup_coverage_ge_90 | cold subgroup별 tier 배정률 ≥ 90% | G17 |
| test_cold_start_estimate.py | test_tier0_warm | tier=0 | G9 |
| test_cold_start_estimate.py | test_tier1_external | tier=1 | G9 |
| test_cold_start_estimate.py | test_tier2_similar | tier=2 | G9 |
| test_cold_start_estimate.py | test_tier3_4_legacy | tier=3/4 | G9 |
| test_cold_start_estimate.py | test_coverage_100pct | 전체 100% | G9 |

### 3.4 Sprint 2 완료 조건
- □ similarity 피처 4개 추가
- □ 5-tier fallback 구현
- □ Cold MdAPE 측정 < 58% (bootstrap 95% CI 포함 보고)
- □ 12개 테스트 통과
- □ **Gate G4** (Cold ≤ 58%), **G9** (생성률 100%), **G17** (subgroup coverage)

### 3.5 병렬화

```
2-1 similarity.py ─┐
2-2 cold_start v2  ─┤─→ 2-3 hedonic 통합 ─→ 2-6 재학습
                    │
2-4 테스트 (2-1 후)─┘
2-5 테스트 (2-2 후)
```

---

## 4. Sprint 3: Knowledge Distillation + CQR (2주)

### 4.1 작업 목록

| # | File | Content | 기획서 |
|---|------|---------|--------|
| 3-1 | `estimate_generator/distillation.py` | OOF Teacher + Student | 전략3 |
| 3-2 | `estimate_generator/conformal_calibrator.py` | CQR | 전략4 |
| 3-3 | `scripts/train_distilled_model.py` | 학습 스크립트 | — |
| 3-4 | `test_distillation.py` | Distillation 테스트 (7개) | — |
| 3-5 | `test_conformal_calibrator.py` | CQR 테스트 (5개) | — |
| 3-6 | `test_track_isolation.py` | 2-트랙 격리 테스트 (4개) | — |
| 3-7 | Strict vs Distilled ablation | paired t-test | — |

### 4.2 파일 명세

`distillation.py`: `DistillationTrainer` — `generate_teacher_predictions_oof()`, `build_distilled_target()`, `fit_student()` — v1.0과 동일.

`conformal_calibrator.py`: `ConformalQuantileCalibrator` — `fit()`, `predict()`, `validate_coverage()`, `validate_temporal_coverage()` — v1.0과 동일. 추가: split-by-time calib set 제한 옵션.

### 4.3 테스트 명세 (Gate 매핑)

| Test File | Test | 기대 결과 | Gate |
|-----------|------|----------|------|
| test_distillation.py | test_oof_no_future_leak | predict > train session | G10, G12 |
| test_distillation.py | test_distilled_range | y_true~teacher 사이 | — |
| test_distillation.py | test_beta_1_equals_hard | y_distill == y_true | — |
| test_distillation.py | test_beta_0_equals_teacher | y_distill == teacher | — |
| test_distillation.py | test_student_no_estimate | estimate 컬럼 0 | G10 |
| test_distillation.py | test_shap_attribution_drift | drift < 0.3 | G13 |
| test_distillation.py | test_paired_ttest | p < 0.05 또는 Strict 복귀 | — |
| test_conformal_calibrator.py | test_cqr_coverage | ≥ 1-α | G11 |
| test_conformal_calibrator.py | test_cqr_adaptive_width | 고가 > 저가 | — |
| test_conformal_calibrator.py | test_temporal_3_windows | 3개 모두 pass | G11 |
| test_conformal_calibrator.py | test_width_not_excessive | < 기존 1.5x | — |
| test_conformal_calibrator.py | test_vs_additive | CQR ≥ additive | — |
| test_track_isolation.py | test_strict_no_estimate_cols | estimate-derived 0개 | G10 |
| test_track_isolation.py | test_distilled_train_only | teacher 컬럼 train only | G10 |
| test_track_isolation.py | test_distilled_infer_no_teacher | infer에 teacher 0개 | G10 |
| test_track_isolation.py | test_artifact_names | strict/distilled 분리 | — |

### 4.4 Sprint 3 완료 조건
- □ `strict_student.cbm` + `distilled_student.cbm` 생성
- □ `conformal_calibrator.pkl` 생성
- □ Strict vs Distilled ablation 보고 (paired t-test p-value)
- □ CQR coverage ≥ 55% (3개 윈도우 모두)
- □ 16개 테스트 통과
- □ **Gate G10~G13** 모두 통과

### 4.5 병렬화

```
3-1 Distillation ────┐
3-2 CQR 구현    ─────┤─→ 3-7 ablation + gate
3-4 distillation 테스트 (3-1 후)
3-5 CQR 테스트 (3-2 후)
3-6 track 테스트 (3-1 후)
```

---

## 5. Sprint 4: 통합 + 최종 검증 (1~2주)

### 5.1 작업 목록

| # | File | Content |
|---|------|---------|
| 4-1 | `generator.py` 확장 | CQR 옵션 + similarity 통합 |
| 4-2 | `server.py` 확장 | 신규 피처 + calibrator 선택 |
| 4-3 | 전 전략 통합 학습 | →최종 모델 |
| 4-4 | 3개 홀드아웃 윈도우 검증 | →final_metrics.json |
| 4-5 | `test_gate_report.py` | 17개 Gate 검증 (G1~G17) |
| 4-7 | API 회귀 테스트 | 기존 6 endpoint 동작 확인 |
| 4-8 | 최종 보고서 | →phase5_result_report.md |

### 5.2 테스트 명세 (Gate 매핑 — 17개 Gate)

> **주의**: Gate 1개당 대표 테스트 1개 지정. G14는 3개 윈도우를 1개 테스트 함수 내에서 검증.

| Gate | 대표 테스트 (canonical name) | Test File | 기준 |
|------|---------------------------|-----------|------|
| G1 | test_g1_test_mdape | test_gate_report.py | Test MdAPE ≤ 32% |
| G2 | test_g2_vt_gap | test_gate_report.py | Gap ≤ 2.5%p |
| G3 | test_g3_test_r2 | test_gate_report.py | Test R² ≥ 0.40 |
| G4 | test_g4_cold_mdape | test_gate_report.py | Cold ≤ 58% |
| G5 | test_g5_coverage | test_gate_report.py | Coverage ≥ 55% |
| G6 | test_g6_within_30 | test_gate_report.py | Within 30% ≥ 53% |
| G7 | test_g7_leakage | test_gate_report.py | ALL PASS |
| G8 | test_g8_monotonicity | test_gate_report.py | ≥ 0.99 |
| G9 | test_g9_cold_generation | test_gate_report.py | 100% |
| G10 | test_g10_no_estimate_in_strict | test_gate_report.py | Strict에 estimate 0개 |
| G11 | test_g11_cqr_temporal_coverage | test_gate_report.py | CQR 3-윈도우 모두 pass |
| G12 | test_g12_oof_time_split | test_gate_report.py | OOF teacher time-split |
| G13 | test_g13_attribution_drift | test_gate_report.py | drift < 0.3 |
| G14 | test_g14_holdout_windows | test_gate_report.py | 3개 윈도우 평균 < valid 1.1x |
| G15 | test_g15_match_precision | test_gate_report.py | precision ≥ 95% |
| G16 | test_g16_macro_months | test_gate_report.py | 12개월+ |
| G17 | test_g17_cold_subgroup_coverage | test_gate_report.py | subgroup ≥ 90% |

**추가 검증** (Gate 외):
| test_estimate_api.py (기존 13개) | 기존 API 회귀 | backward-compat |

### 5.3 Sprint 4 완료 조건
- □ 필수 Gate G1~G14 모두 통과
- □ Strict / Distilled 두 트랙 결과 보고
- □ 최종 보고서 `phase5_result_report.md`
- □ `ruff check src/` + `pytest tests/price_engine/ -v` 통과

### 5.4 병렬화

```
4-1 generator 확장 ─┐
4-2 server 확장    ─┤─→ 4-3 통합 학습 ─→ 4-4 검증 ─→ 4-8 보고서
4-5 gate 테스트 (4-4 후)
4-6 window 테스트 (4-4 후)
4-7 API 회귀 (4-2 후)
```

---

## 6. Quality Gate 전체 (17개)

| Gate | 기준 | 유형 | Sprint | 테스트 |
|------|------|------|--------|--------|
| G1 | Test MdAPE ≤ 32% | 필수 | 4 | test_g1_test_mdape |
| G2 | Val-Test Gap ≤ 2.5%p | 필수 | 4 | test_g2_vt_gap |
| G3 | Test R² ≥ 0.40 | 필수 | 4 | test_g3_test_r2 |
| G4 | Cold MdAPE ≤ 58% | 필수 | 2+ | test_g4_cold_mdape |
| G5 | Coverage ≥ 55% | 필수 | 3+ | test_g5_coverage |
| G6 | Within 30% ≥ 53% | 필수 | 4 | test_g6_within_30 |
| G7 | Leakage ALL PASS | 필수 | 매 | test_g7_leakage |
| G8 | Monotonicity ≥ 0.99 | 필수 | 4 | test_g8_monotonicity |
| G9 | Cold 생성률 = 100% | 필수 | 2+ | test_g9_cold_generation |
| G10 | Distillation test 미사용 | 필수 | 3 | test_g10_no_estimate_in_strict |
| G11 | CQR coverage ≥ (1-α) 3윈도우 | 필수 | 3 | test_g11_cqr_temporal_coverage |
| G12 | OOF teacher time-split | 필수 | 3 | test_g12_oof_time_split |
| G13 | Attribution drift < 0.3 | 필수 | 3 | test_g13_attribution_drift |
| G14 | 3윈도우 평균 < valid 1.1x | 필수 | 0,4 | test_g14_holdout_windows |
| G15 | Match precision ≥ 95% | 참조 | 1 | test_g15_match_precision |
| G16 | 매크로 12개월+ | 참조 | 1 | test_g16_macro_months |
| G17 | Cold subgroup coverage ≥ 90% | 참조 | 2 | test_g17_cold_subgroup_coverage |

---

## 7. 리스크 및 완화

| # | 리스크 | 완화 | Rollback |
|---|--------|------|---------|
| R1 | Distillation 효과 미미 | β grid, paired t-test | Strict 복귀 |
| R2 | Seoul Auction 차단 | Rate limit, robots.txt | Artsy+NamuWiki만 |
| R3 | CQR 구간 과도 확장 | Width gate (< 1.5x) | Additive shift 복귀 |
| R4 | 작가명 매칭 오류 | Confidence ≥ 0.85, top100 수동 | 외부 피처 제거 |
| R5 | Hammer/total 불일치 | Premium flag 통일 | Flag 필터 |
| R6 | 환율 보정 누락 | 경매월 fx 적용 | Inflation adj |
| R7 | Cold 표본 작음 | Bootstrap CI 보고 | 95% CI 포함 |
| R8 | Val-Test gap 미해소 | Sprint 0 원인별 대응 | Feature selection |
| R9 | Selection bias (미낙찰) | unsold_flag 분리 | Heckman 검토 |
| R10 | 스크래핑 ToS | robots.txt, rate limit | 수집 중단 |

---

## 8. 검증 명령어

```bash
# Sprint 0
PYTHONPATH=src python3 scripts/diagnose_gap.py
pytest tests/price_engine/test_gap_diagnosis.py tests/price_engine/test_gap_leak_audit.py -v

# Sprint 1
PYTHONPATH=src python3 scripts/collectors/collect_macro_data.py
pytest tests/price_engine/test_macro_indicators.py tests/price_engine/test_entity_resolution.py -v

# Sprint 2
pytest tests/price_engine/test_artist_similarity.py tests/price_engine/test_cold_start_estimate.py -v

# Sprint 3
PYTHONPATH=src python3 scripts/train_distilled_model.py
pytest tests/price_engine/test_distillation.py tests/price_engine/test_conformal_calibrator.py tests/price_engine/test_track_isolation.py -v

# Sprint 4 (전체)
ruff check src/
pytest tests/price_engine/ -v
```
