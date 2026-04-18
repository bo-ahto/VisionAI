# 2026-04-17~18 Estimate Generator 리팩터 종합 리포트

> **작성일**: 2026-04-18
> **대상**: VisionAI estimate_generator 파이프라인 (Hedonic, Model-A, Ensemble, API)
> **관련 PR**: [#7](https://github.com/bo-ahto/VisionAI/pull/7), [#8](https://github.com/bo-ahto/VisionAI/pull/8)
> **베이스 브랜치**: `main` (commit `c9a12b6`)

---

## 1. 개요

본 리팩터는 `main` 직전 상태 (commit `6473c3a`) 대비 두 단계 PR로 진행됐다.

| 단계 | PR | 머지 커밋 | 주된 변화 |
|---|---|---|---|
| Phase A | #7 | `105d2b1` | HEDONIC_FEATURES 재구성 + 10건 correctness fix + Cold Start ablation 실험 |
| Phase B | #8 | `c9a12b6` | 보조 모듈 정리 + 3라운드 코덱스 리뷰로 11건 추가 수정 |

**Total correctness 개선 21건** (commit 메시지 집계 기반: `759c20a` 6 + `953fcbf` 4 + `63beb4f` 3 + `e47988f` 3 + `ab387c8` 5 = 21). 일부 초기 커밋은 severity(P1/P2) 분류 없이 기록됐으므로 본 리포트는 심각도별 총계를 주장하지 않는다.

---

## 2. 문제 의식

리팩터의 트리거는 코덱스 리뷰가 최초로 감지한 다음 이슈들이었다.

1. **`price_segment_median` 데이터 누수** — 테스트 기간 가격까지 포함한 매체별 median을 train에 사용
2. **Ridge 메타학습기의 분위수 훼손** — 스택킹 결과가 조건부 평균으로 회귀되어 `price_low`/`price_high`가 `price_mid`로 수렴
3. **XGBoost 범주형 코드 불안정** — train/calib/inference마다 동일 값이 다른 정수 코드로 매핑
4. **HEDONIC_FEATURES 미반영** — 피처 확장 의도가 실제 학습에 연결 안 됨

이 4건을 포함해 최초 P1 × 3, P2 × 1으로 출발.

---

## 3. Phase A 변경 내역 (PR #7)

### 3.1 HEDONIC_FEATURES 재구성 (50 → 46)

- CAT 인덱스 계약: `[0, 1, 2, 3, 4, 35, 39, 40, 45]` (test 강제 검증)
- SHAP 분석에서 cold에 유해 판정된 4개 제거: `global_median_price`, `global_auction_count`, `medium_avg_price`, `artist_price_volatility`

### 3.2 `price_segment_median` 누수 수정 (최종: train-only broadcast)

**Ablation F** (3-seed Model-A 기준, cold = `artist_total_sold < 5`). 근거 아티팩트: [`model_test_results/ablation_f_psm.json`](../model_test_results/ablation_f_psm.json).

| Variant | Model-A cold | 판정 |
|---|---|---|
| V_expanding (per-cutoff past-only, 코덱스 최초 제안) | 62.48% | ❌ materially worse (+1.42pp) |
| **V_trainonly (train split broadcast)** | **61.06%** | ✅ 채택 |
| V_leaky (누수 포함, 옛 방식) | 61.37% | — V_trainonly와 차이 +0.32pp (seed 변동 범위 내, noisy) |

**별도 실험 (V_no_PSM, PSM 제거)**: Model-A 3-seed 60.20% (근거: [`model_test_results/step_12_comparison.json`](../model_test_results/step_12_comparison.json), 다른 cache/run).

Ens+Bias에서 V_no_PSM이 V_trainonly보다 불리하다고 판단한 근거는 **persist 되지 않은 일회성 측정**이었다. 따라서 "PSM 유지"는 **잠정 결정**(interim) 이며 audit 가능한 근거에 기반한 최종 결정이 아니다. **Follow-up 과제**: 동일 cache에서 HEDONIC_FEATURES를 45개로 바꿔 phase5_final을 한 번 더 돌려 Ens+Bias 결과를 persist하고 재확인 필요.

현재는 Model-A 차이 (+PSM 61.06% vs −PSM 60.20%) 와 Ensemble/Bias 층이 feature 분포에 민감할 수 있다는 이론적 우려 때문에 보수적으로 **잠정 유지**한 상태.

**Ablation F의 좁은 결론**: 이 설정(Model-A, 3 seed, 본 cache)에서 V_trainonly (61.06%) 와 V_leaky (61.37%) 의 cold_mdape 차이 0.32pp는 seed 변동 범위 내. **본 실험만으로는 PSM 누수의 영향이 명확히 감지되지 않았음** (다른 모델/설정/표본에서는 다를 수 있으므로 일반화하지 않는다). 초기 "3.27pp regression" 해석은 **Model-A vs Ens+Bias** 를 혼용한 apples-to-oranges 비교였으며, 이 점은 설정과 무관하게 방법론 오류.

### 3.3 QuantileRegressor 스택킹 메타학습기

Ridge(MSE) → `sklearn.linear_model.QuantileRegressor` 교체. pinball loss로 각 분위수 별도 학습.

**효과**: Ensemble 순수 test_mdape 43.16% → 41.53% (**−1.63pp**, 단일 최대 이득).

### 3.4 XGBoost 범주형 vocabulary 고정

`self._xgb_cat_vocab` 딕셔너리에 학습 시 categories 저장 → calib/inference에서 재사용. 카테고리 순서 바뀌어도 동일 값 = 동일 코드 보장.

### 3.5 API `_build_estimate_input` 스키마 동기화

50개 → 46개 피처 기본값 (대부분 NaN, cat은 `"unknown"` 또는 `False`). `ln_surface_area`, `short_side_cm`, `long_side_cm`, `size_ho` 등 파생 필드는 요청 크기로부터 직접 계산.

### 3.6 기타 edge case fix

- `sale_date` NaT 가드 (레거시 CSV 대응)
- `cold_start.get_cold_start_fallback` cutoff 타입 자동 coerce (session int vs date str)
- `artist_similarity` datetime64 `career_length` 처리
- XGBoost 선택 backend의 `XGBoostError` 포함 광역 예외
- cleansed 데이터의 `title`/`제목` 컬럼 fallback
- `two_step_model` fallback regressor를 **최빈 bin**으로 (기존: 최저가 label — premium 작품이 budget regressor로 붕괴되던 버그)
- `dimension_parser` 2D 원본 순서 보존 (WxH) — orientation landscape 감지 복원 (이전 max/min swap으로 landscape 0건)
- `splits.py` NaT `sale_date` 행을 `train` 강제 → `"unknown"` 변경
- `quantile_model._prepare_hedonic_features` extra_features 누락 시 NaN 채움 (silent column drop 방지)

---

## 4. Phase B 변경 내역 (PR #8)

### 4.1 주변 코드 정리

PR #7에서 작업 scope 밖이라 유보했던 파일들을 주제별로 9개 커밋으로 분할:

1. Phase 3 hedonic/parser 모듈 개선 (`hedonic_stats`, `medium_parser`, `artist_stats_snapshot`, `target_transform_v2`, `market_rounder`)
2. `.gitignore` 보강 (data, model_test_results, 툴 캐시)
3. docs 34개 정리 (연구노트, 기획서, 결과 보고, API 레퍼런스 등)
4. scripts 27개 추가 (크롤러, 학습, 진단, embeddings)
5. estimate_generator 신규 모듈 + 11개 테스트 (conformal, distillation, macro_indicators, track_config, data_cleanser 등)
6. `data/*.xlsx` gitignore 추가

### 4.2 코덱스 리뷰 3라운드 11건

PR #8 기간 동안 3회의 코덱스 리뷰가 개별 버그를 추가 발견.

#### 4.2.1 1차 리뷰 (P1 × 1, P2 × 2)

| # | 파일 | 문제 | 수정 |
|---|---|---|---|
| P1 | `features/macro_indicators.py:107-112` | `ffill()`이 입력 행 순서 의존 → 누락 session이 미래 값 상속 | session 기준 mergesort 정렬 후 ffill, 원본 인덱스 복원 |
| P2 | `scripts/train_phase5_final.py:37-40` | cache가 dataset 무관하게 재사용됨 | filename + mtime + size로 cache 파일명 키잉 |
| P2 | `scripts/train_phase5_final.py:95-98` | similarity donor vectors를 모든 train 행에 단일 unbounded cutoff로 사용 → train 내부 temporal leak | 월 단위 bucket별 vectors 캐시, 각 행의 bucket 이전 데이터로만 빌드 |

#### 4.2.2 2차 리뷰 (P1 × 1, P2 × 2)

| # | 파일 | 문제 | 수정 |
|---|---|---|---|
| P1 | `preprocessing/data_schema.py:157-170` | K-Auction 날짜 추론이 `artist|title`만 매칭 → "김환기\|무제" 같은 반복 제목이 여러 회차 동일 key로 묶여 오매칭 | 가격 포함 (`artist|title|price`) |
| P2 | `preprocessing/data_schema.py:283-295` | dedup key에 sale_date 미포함 → 재판매 이력이 duplicate로 제거 | key에 sale_date 추가 |
| P2 | `preprocessing/medium_parser.py:67-72` | "archival pigment print", "gelatin silver print" 등 영문 사진 용어가 사진/디지털이 아닌 아크릴/혼합재료/기타로 오분류 | 영문 regex 패턴 확장 |

#### 4.2.3 3차 리뷰 (P1 × 3, P2 × 2)

| # | 파일 | 문제 | 수정 |
|---|---|---|---|
| P1 | `preprocessing/data_schema.py:167-171` | 2차 수정 시 `ka['price_krw']` 하드코딩 — 실제 CSV는 `price` 컬럼 사용 | price/price_krw/낙찰가 자동 감지 |
| P1 | `estimate_generator/cold_start.py:151-152` | `get_cold_start_fallback_v2`가 session int 데이터에 str cutoff 기본값 → TypeError | v1과 동일하게 session dtype 체크 후 coerce |
| P1 | `scripts/train_phase5_v3.py:202-203` | 위 단계에서 macro/similarity/PSI 컬럼 추가하지만 Model-A는 기본 HEDONIC만 학습 → dead code | `extra_features=MACRO_FEATURES + sim_cols` 전달 |
| P2 | `scripts/train_phase5_v3.py:262-270` | `select_features_by_importance(top_n=35)`가 계산만 되고 student는 STRICT_FEATURES 전체 사용 | `distillation.fit_student`에 `features` 파라미터 추가 + `selected` 전달 |
| P2 | `tests/price_engine/test_gate_report.py:49-52` | gate 미달 시 `pytest.skip()` — CI green으로 regression 은폐 | `assert` + 현재 미달 게이트는 `@pytest.mark.xfail(strict=False, reason=...)` |

---

## 5. 실험 방법론 요약

### 5.1 Ablation F: PSM variant 비교

동일 cache + 3 seed × 3 variant (V_expanding, V_trainonly, V_leaky) → Model-A cold_mdape 측정 (cold = `artist_total_sold < 5`). **seed 표준편차 0.3~0.9pp** 대비 variant 간 차이:

- V_trainonly vs V_leaky: 0.32pp (seed 변동 범위 내, 결론 불가)
- V_expanding vs V_trainonly: +1.42pp (variant간 격차가 seed 변동 초과, materially worse로 판정)

3-seed는 통계적 유의성 검정에 부족한 표본이므로 "통계적으로 유의"라고 주장하지 않는다. 다만 seed별 결과가 V_expanding 내부 (62.21~62.83%)와 V_trainonly 내부 (60.68~61.51%)가 overlap하지 않을 만큼 분리되므로, **practical 관점에서는 V_expanding이 열등**하다고 결론.

### 5.2 Ens+Bias 최종 비교

Phase5 final pipeline (CatBoost MultiQuantile + LightGBM Quantile + XGBoost Quantile + QuantileRegressor meta + CQR + Bias correction).

**근거 아티팩트**: 양쪽 모두 `phase5_final_metrics.json` 필드 기준. cold 정의는 `artist_total_sold < _COLD_THRESHOLD` (5) — `train_phase5_final.py:454` 참조.
- Current: [`model_test_results/phase5_final_metrics.json`](../model_test_results/phase5_final_metrics.json)
- Archived: [`model_test_results/baseline_pre_retrain_20260417/phase5_final_metrics.json`](../model_test_results/baseline_pre_retrain_20260417/phase5_final_metrics.json)

| 지표 | Archived (pre-refactor) | Current (V_trainonly, 46f) | Δ |
|---|---|---|---|
| test_mdape | 40.87% | **40.89%** | +0.02pp (동일) |
| cold_mdape (총 test) | 57.90% | 59.60% | +1.70pp |
| warm_mdape (총 test) | 38.61% | 38.64% | +0.03pp (동일) |
| test_r2 (phase5 output) | 0.468 | **0.474** | +0.006 ✅ |
| test_within_30 | 38.13% | 37.64% | **−0.49pp** ❌ |
| valid_within_30 | 42.01% | **42.96%** | +0.95pp ✅ |
| **ensemble_test_mdape** (단일 앙상블, Bias 전) | **43.16%** | **41.53%** | **−1.63pp ✅** |
| model_a_test_mdape | 43.70% | **42.90%** | −0.80pp ✅ |

**G7 Leakage 게이트 (severe session-correlation 기준)**: FAIL → **PASS**. 참고: `gap_diagnosis.json`에는 여전히 7건의 drift-style 경고가 남아 있으며 이는 `test_g7_leakage`에서 의도적으로 허용된 범위. "모든 누수 종결"은 아님.

### 5.3 주요 통찰

- **"Cold 3.27pp regression"은 비교 오류였음**. Model-A vs Ens+Bias, 단일 seed vs 3-seed mean이 섞여 있었음.
- **Refactor 전체의 net effect** — archived vs current 비교는 **여러 변화가 동시에 바뀐 diff**이므로 개별 요인으로 귀속 불가. 관찰된 차이: test/warm 동일, cold +1.70pp, test_within_30 −0.49pp, R² +0.006, ensemble_test −1.63pp. 이를 "누수 제거의 비용"으로 단일 귀속할 수 없음 (Ablation F는 Model-A PSM variant만 격리했고 Ens+Bias 전체 refactor 영향은 격리 안 됨).
- **Ridge → QuantileRegressor가 단일 명확한 이득** (ensemble test −1.63pp).
- **코덱스의 첫 가설 반박 사례**: expanding-window가 cold를 회복한다는 주장이 실험으로 반증됨.

---

## 6. 최종 테스트 상태

```
=========== 411 passed, 4 xfailed in 3.83s ===========
```

- **411 passing** — HEDONIC contract, parser, quantile model, ensemble, CQR, two-step, cold start, similarity, macro indicators, entity resolution, calibration, conformal, distillation 등
- **4 xfailed** — 현재 모델이 목표 미달인 게이트들 (G1 MdAPE≤32, G2 gap≤2.5pp, G3 segment R²≥0.40, G6 W30≥53)를 명시적으로 기록. 달성 시 "unexpected pass" 알림.

게이트 PASS (test 판정):
- G4 Cold ≤ 58% — **주의**: [`tests/price_engine/test_gate_report.py:87-103`](../tests/price_engine/test_gate_report.py) 구현은 `gap_diagnosis.json`의 `segment_cold_test.True` (`is_new_artist` 기반 cohort, 49.82%) 를 본다. 반면 Section 5.2의 cold 59.60%는 `phase5_final_metrics.json` (`artist_total_sold < 5` cohort). **두 지표는 cohort 정의가 달라서 동일 "cold"가 아님**. 각자 정의에 맞춰 독립 해석 필요.
- G5 Coverage ≥ 55%
- G7 Leakage — **severe session-correlation 기준만 PASS**. drift warning 7건은 별도. `price_segment_median`의 split-wise 누수는 구조적으로 제거됨 — 이 부분만 "누수 closed".
- G8 Monotonicity ≥ 0.99
- G9~G14 구조 게이트 (Cold 생성, Strict 피처, CQR temporal, OOF split, attribution drift, holdout)
- G15~G17 참조 게이트 (match precision, macro months, cold subgroup coverage)

---

## 7. 미해결 / 후속 과제

1. **G1, G2, G3, G6 목표 미달** — 현재 xfail 표기. 개선 방향:
   - cold-specific 라우팅/expert 모델
   - 외부 작가 프로필 수집 확대 (Artsy/Saatchi/웹검색 필터 강화)
   - 매크로 지표 추가 수집 (ECOS 외)
2. **`model_test_results` tracked 상태** — 이진 모델 아티팩트가 여전히 git 추적 중. 장기적으로 untrack 권장.
3. **Distillation v3 student** — `selected` 피처셋 반영 후 재학습 필요 (스크립트 수정만 완료, 학습은 미실행).
4. **배포 연동** — 새로 재학습한 `model_a_quantile.cbm`을 운영 서버 (`visionai-api.ahto.city`)에 반영 필요.
5. **V_no_PSM Ens+Bias 재측정 + persist** — PSM 유지 결정의 audit 근거 확보. Section 3.2 각주 참조.

---

## 8. 요약 한 문단

> 2일에 걸친 리팩터로 price_segment_median 데이터 누수를 포함한 **correctness 21건**을 수정했고 (severity 분류는 commit 메시지 집계로만 제한됨), Ensemble 순수 test MdAPE를 **1.63pp 개선**했으며 (43.16% → 41.53%, Bias correction 전) 최종 Ens+Bias test 지표는 archived와 **사실상 동일** (test 40.89 vs 40.87, warm 38.64 vs 38.61). 대신 cold MdAPE는 57.90% → **59.60%** 로 이동, test_within_30은 −0.49pp 이동. 이 변화는 여러 refactor 변화가 동시에 들어간 비교이므로 **어느 단일 요인에 귀속하지 않는다** (Ablation F는 Model-A PSM variant만 격리 검증). G7 Leakage 게이트는 severe session-correlation 기준으로 FAIL → **PASS**, drift warning 7건은 여전하므로 "누수 종결" 선언은 아니다. 초기 "cold 3.27pp regression" 해석은 Model-A vs Ens+Bias apples-to-oranges 오류였으며 **Ablation F 및 seed 내부 확인**으로 교정됐다. PSM 유지 결정은 Ens+Bias 재측정 persist가 없어서 현재는 **잠정**.

---

## 9. Appendix A: Canonical artifact map

본 리포트의 각 수치가 어떤 파일에서 왔는지.

| 섹션 | 항목 | 원본 파일 | Cohort/field |
|---|---|---|---|
| 3.2 Ablation F 3 variant | V_expanding/V_trainonly/V_leaky cold | `model_test_results/ablation_f_psm.json` | `artist_total_sold < 5`, `cold` field |
| 3.2 V_no_PSM Model-A | 60.20% | `model_test_results/step_12_comparison.json` (별도 run, cache 공유) | Model-A only, 3-seed mean |
| 3.2 V_no_PSM Ens+Bias | — | **audit 불가** (persist 안 된 일회성 측정, follow-up에서 재측정 필요) | Ens+Bias |
| 5.2 Ens+Bias 비교 | 모든 지표 | `model_test_results/phase5_final_metrics.json` ↔ `baseline_pre_retrain_20260417/phase5_final_metrics.json` | cold = `artist_total_sold < 5` |
| 6. 게이트 판정 | G1~G8 | `tests/price_engine/test_gate_report.py` 실행 결과 | `gap_diagnosis.json` 기반, cold = `is_new_artist` (다른 cohort) |
| 6. G7 Leakage | PASS 여부 | `test_gate_report.py::test_g7_leakage` | severe session-correlation만. drift 경고 7건 별도 |

**중요**: cold MdAPE 수치가 59.60% (Section 5.2) 와 49.82% (Section 6 G4 판정 근거) 로 다른 것은 **서로 다른 cohort 정의 (`artist_total_sold<5` vs `is_new_artist`)** 때문이며 동일 지표가 아니다.

---

**Prepared by**: Claude Opus 4.7 (1M context) with codex review cross-checks
**Repository**: `bo-ahto/VisionAI` main @ `c9a12b6`
