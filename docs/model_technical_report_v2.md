# VisionAI 1차 시장 가격 예측 모델 기술 보고서 v2

> **작성일**: 2026-04-28
> **모델 버전**: v3-tuned-cal (`integrated_v3_filtered_tuned` + cell calibration)
> **학습 데이터**: 28,376건 (29,361건에서 입체/3D 985건 제외) / 1,551명 작가 (warm 930명, ≥5건)
> **대상**: 한국 신진/중견 작가 회화 작품의 1차 시장(갤러리) 가격 예측
>
> **⚠ 본 문서의 위치**: v1 보고서([`model_technical_report.html`](model_technical_report.html))의 **개선 후속편**. v1의 이론·아키텍처 본문은 그대로 유효하며, 본 문서는 2026-04-17~28 사이 협력자 피드백 → 4건의 PR(#20·#21·#22 모델·#19 분석) → 32회 코덱스 리뷰를 거쳐 적용된 **변경 사항만** 정리한다. 처음 읽는 독자는 v1을 먼저 보고 본 문서로 이어 보길 권한다.
>
> **📌 범위**: 1차 시장 예측 모델(A, `primary_predictor` + `integrated_v3_filtered_tuned_*`) 전용. 경매 낙찰가 모델(B)은 별도 문서.
>
> **출처(Provenance)**: 본 문서가 인용하는 모든 수치는 머지된 산출물 기준이다.
> - 핵심 metrics: [`model_test_results/integrated_v3_filtered_tuned_metrics.json`](../model_test_results/integrated_v3_filtered_tuned_metrics.json)
> - 셀 캘리브레이션: [`model_test_results/integrated_v3_filtered_tuned_source_calibration.json`](../model_test_results/integrated_v3_filtered_tuned_source_calibration.json)
> - 등급 마진: [`model_test_results/grade_margin_calibration.json`](../model_test_results/grade_margin_calibration.json)
> - 워밍 작가 셋: [`model_test_results/integrated_v3_filtered_tuned_warm_artists.json`](../model_test_results/integrated_v3_filtered_tuned_warm_artists.json) (930명 / 27,062건)

---

## 0. 한 문단 요약

협력자가 v1 모델에 던진 10개 질문(고가 작품 미흡·생년 결측·갤러리 등급·신진 작가 등)을 **데이터로 검증**한 결과, "단순 피처 추가"보다 **train/serve 정합**이 더 큰 병목임이 드러났다. 4건의 PR로 (1) `career_stage`를 사문화 분기에서 **연속 0~8 다요인 점수**로 재설계, (2) **학습엔 있지만 서빙엔 0인 5개 피처(드리프트)**를 모델에서 제거, (3) `source × target_market` 셀 단위 **교차 검증 캘리브레이션**(per-cell guard)으로 콜드 MdAPE를 39.4 → 38.3%로 끌어내리고, (4) `source` 정규화·등급 마진 재캘리브레이션으로 **production-time** A 등급 9.8% / 워밍 Artsy 8.3%를 달성했다. 코덱스 리뷰 **32회**가 공정 누수·정규화 불일치·폴드 멤버십 어긋남 같은 잡음을 차단했다.

---

## 1. v1 → v2 핵심 지표 변화

> **읽는 법**: v1 라인은 `integrated_v3_metrics.json` (29,361건 전체 학습), v2 라인은 `integrated_v3_filtered_tuned_metrics.json` (입체 985건 제외 후 28,376건, Optuna n_trials=30 튜닝, cell calibration 적용)을 옮긴 것이다.

| 지표 | v1 (2026-04-17) | v2 (2026-04-28) | Δ |
|---|---:|---:|---:|
| 피처 수 (모델 입력) | 37 | **32** | -5 (drift 제거) |
| 학습 건수 | 29,361 | 28,376 | -985 (입체) |
| Warm 작가 (≥5건) | 명시 안됨 | **930명 / 27,062건** | 라우팅 정합 확보 |
| **Warm 전체 MdAPE (KFold)** | 11.7% (XGB) / 17.1% (CB) | **9.7% (XGB) / 11.9% (CB) / 10.5% (앙상블)** | -2.0%p (XGB) |
| Warm Artsy MdAPE (KFold) | 명시 안됨 | **8.3% (XGB) / 8.7% (앙상블)** | A 목표(8%) 도달 |
| **Cold 전체 MdAPE (GroupKFold)** — production path = CatBoost | 38.9% (CB) / 39.4% (XGB) | **CatBoost 39.4% (보정 전) → 38.3% (보정 후, cross-fit guarded)** | -1.1%p |
| Cold 전체 — offline ensemble (참고용, production 경로 아님) | — | 38.7% | — |
| Cold Artsy MdAPE — offline ensemble (참고용) | ≈40% | 33.2% (앙상블) | -7%p |
| Production-time A 등급 MdAPE | 보고 없음 | **9.8%** | 신규 측정 |
| Source 보정 방식 | 단일 상수 -0.075 (online) | **셀별 ratio (artsy_online=0.943, saatchi_online=0.957)** | per-cell guard 도입 |

**해석**: 단일 매개변수 보정에서 **source × target_market 셀별 보정**으로 갈아탔다. **production cold path는 CatBoost 단일 경로**이므로 보정 전후 비교는 CatBoost OOF 기준(`source_calibration.json` `cold_overall`): 39.38 → 38.29 (-1.09%p, cross-fit guarded). 앙상블/Artsy 슬라이스 수치는 offline 비교용이며 운영 경로와 다르므로 별도 표기. **artsy_gallery 셀은 cross-fit에서 보정이 회귀를 일으켜 factor=1.0 (skip)** — 자동 가드로 안정성 확보.

---

## 2. 협력자 피드백 → 모델 변경 매트릭스

협력자가 v1 보고서에 제기한 10개 질문이 어떻게 처리됐는지 한눈에 정리한다 (자세한 액션은 [`docs/MdAPE_개선_액션플랜_20260427.md`](MdAPE_개선_액션플랜_20260427.md) 참조).

| # | 협력자 질문 | 데이터 검증 결과 | 적용된 변경 | PR |
|:-:|---|---|---|:-:|
| Q1 | "고가(3천만+) 예측이 약하다" | 학습 분포 1,678건(5.7%)으로 데이터 구조 한계 — 피처 추가로 해결 불가 | 알림: 등급별 m 재캘리브레이션으로 **가격 범위**를 더 정직하게 표시 | #22 |
| Q2 | "생년 결측 72%가 너무 크다" | 사실 — 외부 수집 보강 필요 | Cold-start 자동 수집 강화 항목으로 운영팀 협조 요청 (대기) | (운영) |
| Q3 | "career_stage가 너무 거칠다" | Stage 3=0건 (사문화) — 분기 자체가 작동 안 함 | **career_stage v2** 도입: 연속 0~8 다요인 점수 (생년·활동성·시장 진입) | #20 |
| Q4 | "갤러리 등급이 1.5%만 기여하나" | 협력자 리스트 88개 vs Artsy 갤러리 66개 중 11개만 매칭 | Top 30 미매칭 명단 산출 → 협력자 검수 대기 (Phase 1B) | #19 |
| Q5 | "Saatchi가 가격을 끌어내린다" | 사실 — source × target_market 4셀 모두 다른 편향 | **셀별 cross-fit calibration** (per-cell guard) | #21 |
| Q6 | "신진(20대) 작가 예측이 튄다" | career_age=0 결측 비율 높음 + has_birth_year sentinel | career_age는 **train/serve drift로 분류 → 제거**, 신진 보강은 cold-start 운영 의제 | #20 |
| Q7 | "디지털/프린트 케이스 분류가 모호" | 24건(0.08%) — MdAPE 영향 미미 | 정책 결정 사안으로 협력자 협의 항목에 등록 | (정책) |
| Q8 | "에디션 vs 원작 분류가 섞여 있다" | 99.9% 원작 (Edition 34건) | printbakery 별 모델 후보로 분리 검토 | (정책) |
| Q9 | "예측 가격이 좁은 구간에 회귀한다" | 사실 — 등급 마진이 실제 분포보다 좁음 | **production-time MdAPE 기반 m 권장치 산출** (A 0.20→0.286 등). 적용은 정책 결정 대기 | #22 |
| Q10 | "여러 학습 코드 중 어느 게 진짜인가" | `train_primary_market_v3_filtered.py` + `tune_*` 단일 경로 | leakage 방지(`eval_set`/early stopping 제거), warm slug JSON 산출, fail-closed 아티팩트 검증 | #20 |

---

## 3. PR #20 — career_stage v2 + 학습/서빙 드리프트 정리 (15회 코덱스 리뷰)

### 3.1 Dead feature: career_stage v1

v1 정의: `if age≥60 ∧ solo≥5 → 4 else if solo≥3 → 3 else if solo≥1 ∨ group≥5 → 2 else 1`.

학습 데이터 실제 분포:

| stage | 건수 | 비율 |
|:-:|---:|---:|
| 1 (신진) | 14,205 | 50.1% |
| 2 (신진후기) | 14,156 | 49.9% |
| **3 (중견)** | **0** | **0.0%** |
| 4 (원로) | 0 | 0.0% |

`solo`/`group` 횟수 정보가 28,376건 학습 데이터에 거의 비어 있어 **분기 자체가 작동하지 않았다.** 중요도 1.77%는 사실상 1↔2 이진 신호에서 나온 것.

### 3.2 career_stage v2 — 연속 다요인 점수

실제 구현 ([`primary_feature_builder.py:48-82`](../src/visionai/price_engine/api/primary_feature_builder.py)):

```
score = age_score + activity_score + market_presence    ∈ [0, 8]

age_score        = clip((birth_year_to_age - 30) / 12, 0, 3)            # 0~3, 연속
activity_score   = min(log1p(solo + 0.7*fair + 0.3*group), 3)           # 0~3, 연속
market_presence  = min(ln_followers / 6, 2)                             # 0~2, 연속
```

**왜 합산인가**: 단일 분기는 한 축이 결측되면 0으로 무너진다. 합산은 **부분적 신호도 살린다.** 예) 생년 없는 작가도 작품 수와 팔로워가 있으면 score>0.

**왜 연속값인가**: GBDT 트리가 임계값을 자유롭게 학습 → v1의 4단계처럼 분기가 사문화되지 않는다.

**career_age는 의도적으로 제외**: 초안에는 `career_duration` 항이 있었으나 학습 데이터(`prepare_primary_market_dataset.py`의 artist shows에서 도출)와 서빙 프로필(`artist_matcher.py`는 항상 0 고정, DB 스키마에 컬럼 없음) 간 드리프트 → 코덱스 후속 P1에서 제거하고 0~8 스케일 확정.

### 3.3 5개 피처 train/serve 드리프트 제거

**증상**: 학습 데이터에는 값이 들어가 있지만, `primary_feature_builder.build_features()`가 서빙 시 **상수(주로 0)를 하드코딩**하던 피처 5개. 모델은 "분포 있는 신호"로 학습됐고, 서빙 시 모든 요청이 같은 값으로 들어가면서 **silent하게 다른 패턴**을 적용했다.

| 제거된 피처 | 카테고리 | 학습 데이터 | 서빙 시 값 | 근거 |
|---|---|---|---|---|
| `career_age` | 작가 | `2026 - first_show_year` | 0 (DB에 컬럼 없음) | Codex 4차 P1 |
| `work_age` | 작품 | `2026 - work_year` | 0 (요청에 미포함) | Codex 4차 P1 |
| `vintage_premium` | 갤러리/시점 | 학습 시 계산 | 0 | Codex 4차 P1 |
| `freshness_discount` | 갤러리/시점 | 학습 시 계산 | 0 | Codex 4차 P1 |
| `gallery_name` | categorical | 학습 vocab 59개 (예: "Kukje Gallery") | `'Gallery'`/`'Saatchi Art'` 2개로 하드코딩 → 매번 sentinel | Codex 14차 P1 |

37 → **32 피처**. **train/serve contract drift는 모델이 침묵으로 잘못된 패턴을 학습**하므로 정확도 하락보다 더 위험하다 (운영 후 디버깅 비용 폭발). `solo_count`/`group_count`/`fair_count`/`followers` 등은 CB_FEATURES에 직접 들어가지 않고 **`career_stage_v2_score` 입력으로만** 사용한다 — 단일 점수로 합쳐지면 부분 결측 영향이 분산된다.

### 3.4 Warm artist routing 정합

**문제**: `artist_matcher.py`는 DB의 `training_count` 컬럼으로 warm 판정 → 학습 시 fold-local 카운트와 불일치. 32명 작가가 production에서 잘못 라우팅됐다.

**수정**: 학습 파이프라인이 `integrated_v3_filtered_tuned_warm_artists.json`(930개 slug)을 산출 → 서빙은 이 JSON을 권위 있는 set으로 사용.

```python
# primary_predictor.py
WARM_ARTIST_SLUGS = load_warm_set(...)
def is_warm_artist(slug): return slug in WARM_ARTIST_SLUGS  # 학습 정의와 1:1
```

### 3.5 그 외 코덱스 리뷰 15회에서 막은 잡음

- **`eval_set` / early stopping**: 학습/검증 폴드 누수 → 제거 후 `iterations`는 Optuna 튜닝값 고정.
- **categorical 정규화 비대칭**: 학습 시 `nan`/`None`/`''`을 `unknown` bucket으로 모아 학습했지만 서빙은 raw 값을 그대로 모델에 넘김 → 서빙 측에 동일한 `astype(str).fillna("unknown").replace({...})` 룰 적용 (자세한 룰은 §5.1).
- **`gallery_name` vocab 불일치**: 학습 vocab 59개, 서빙은 `'Gallery'`/`'Saatchi Art'` 2개 하드코딩 → 피처에서 제거(차후 PredictRequest에 optional 추가 예정).
- **`load_models` 부분 실패**: 5개 아티팩트 중 1개라도 실패하면 partial 상태 → fail-closed (`RuntimeError`).
- **label_maps fallback**: 학습 시 사용한 vocab을 매번 산출 가능한 path가 없어 mandatory 아티팩트로 승격.

---

## 4. PR #21 — Source × target_market 셀 캘리브레이션 (8회 코덱스 리뷰)

### 4.1 v1의 단일 상수 보정 한계

v1: `c = -0.075 if target_market=='online' else 0.0` — **모든 online을 같은 값으로** 보정.

문제: Artsy online과 Saatchi online은 다른 분포를 가진다.

| 셀 | n | baseline MdAPE | v2 cross-fit calibrated MdAPE | 적용 factor |
|---|---:|---:|---:|---:|
| artsy_gallery | 868 | 24.3 | **24.3 (skip)** ← guarded | 1.0 |
| artsy_online | 6,421 | 35.0 | **34.1** | 0.943 |
| saatchi_online | 21,087 | 41.7 | **40.1** | 0.957 |

(MdAPE는 cold GroupKFold OOF, [`integrated_v3_filtered_tuned_source_calibration.json`](../model_test_results/integrated_v3_filtered_tuned_source_calibration.json) `cold_breakdown` 기준.)

### 4.2 Cross-fit cell calibration with per-cell guard

```
factor[cell] = median(actual_price / predicted_price | cell)
```

**핵심 안전장치 3개**:

1. **Cross-fit (5-fold)**: 인-샘플로 factor를 추정하고 같은 데이터로 보정 → 평가가 부풀려짐. 따라서 train fold에서만 fit, OOF에서 평가.
2. **Per-cell guard**: cross-fit 평가가 baseline보다 **악화되는 셀**은 `factor=1.0` 적용 (skip). `artsy_gallery`가 여기 해당 (baseline 24.3 < calibrated 31.2).
3. **Schema validation**: `version`/`model_target`/허용 셀 키 일치 확인. 불일치 시 RuntimeError.

### 4.3 Production 적용 factor

```json
"cold_factors": {
  "artsy_gallery": 1.0,                  // skipped (regression cell)
  "artsy_online": 0.9425943416620021,    // -5.7%
  "saatchi_online": 0.9568847727800011   // -4.3%
}
```

**Cold 전체 효과**: baseline 39.38 → calibrated cross-fit guarded **38.29** (-1.09%p).

**Warm은 보정 미적용 효과 (factor≈1.0)**: warm은 이미 작가 패턴이 학습됐기에 셀별 편향이 작다 (8.7~10.3%).

### 4.4 코덱스 리뷰 8회에서 막은 잡음

- **In-sample evaluation**: 처음엔 같은 데이터로 fit/eval → cross-fit으로 전환.
- **Cell key parser 버그**: `split('_', 1)`이 `"artsy_artue"` 같은 셀에서 잘못 분할 → `rsplit` 으로 수정.
- **wording 혼란**: "True OOS guarded MdAPE" → guard cell selection이 같은 OOF 결과 보고 결정되어 post-hoc bias 잔존 → "production-time MdAPE"로 일관 정정.

---

## 5. PR #22 — Source 정규화 + 등급 마진 재캘리브레이션 (8회 코덱스 리뷰)

### 5.1 source 결측값 정규화

`source` 등 categorical 피처가 서빙 시 `None`/`NaN`/`'None'`/`''`로 들어오면 학습 vocab 외 값이 되어 sentinel encoding으로 떨어졌다. 학습/서빙이 동일하게 처리되도록 **predictor에서 모든 CAT_FEATURES에 일괄 정규화** 적용 ([`primary_predictor.py:317-322`](../src/visionai/price_engine/api/primary_predictor.py)):

```python
for col in CAT_FEATURES:
    df[col] = df[col].astype(str).fillna("unknown").replace(
        {"nan": "unknown", "None": "unknown", "": "unknown"}
    )
```

추가로 cold calibration cell key 산출에서도 `source`만 동일 룰로 한 번 더 정규화 ([`primary_predictor.py:367-370`](../src/visionai/price_engine/api/primary_predictor.py)) — `cell = f"{src}_{target_market}"` 안정화. **`lower()`/`strip()`은 적용하지 않는다** (학습 vocab도 case-sensitive로 일관 유지).

### 5.2 등급 마진 production-time 재캘리브레이션

v1 마진은 **모델 OOS MdAPE**(38~39%)에서 도출 → 실제 라우팅된 등급별 분포와 어긋났다.

새 절차 ([`scripts/calibrate_grade_margins.py`](../scripts/calibrate_grade_margins.py)):

1. **5-fold CV의 OOF 모델 weights**로 가격 예측.
2. 라우팅(`warm_artist_slugs.json`)과 cold 보정(`source_calibration.json` `cold_factors`)은 **production full-data artifacts** 그대로 사용.
3. 등급(A/B/C/D)을 production 함수로 부여, 등급별 |APE| 분포에서 80% 커버리지 m을 산출.

**caveat (스크립트 [§해석](../scripts/calibrate_grade_margins.py) 그대로)**: "OOF model weights + full-data routing artifacts" 결합 평가이므로 **순수 OOF는 아니며**, 운영 시 메트릭의 **추정치**로 해석한다. Routing/calibration artifact 자체의 OOS 일반화는 PR #20+#21 산출물에서 별도 평가됐다.

**production-time per-grade 결과** (n=28,376):

| 등급 | n | MdAPE | 평균 APE | 현재 m | 현재 80% 커버리지 | 권장 m | Δ |
|:-:|---:|---:|---:|---:|---:|---:|---:|
| A | 27,062 | **9.8%** | 19.7% | 0.20 | 71.5% | 0.286 | +0.086 |
| B | 1,006 | **29.7%** | 44.9% | 0.30 | 50.6% | 0.609 | +0.309 |
| C | 128 | **39.0%** | 56.6% | 0.50 | 60.2% | 0.896 | +0.396 |
| D | 180 | **43.6%** | 64.6% | 0.70 | 72.8% | 0.827 | +0.127 |

**해석**:
- **A 등급은 현재 m=0.20에서 71.5%만 커버** → 80% 커버리지를 위해선 m=0.286 필요. 현재 가격 범위가 좁게 표시되고 있다는 뜻.
- **C/D는 m≈0.9** — 사실상 가격 범위 의미가 없을 정도로 넓어진다. 적용 여부는 정책 결정 사안 (사용자 신뢰도 영향).

**권장 m 적용은 보류 중** — 사용자 요청에 따라 적용 결정은 별도 정책 결정 후 진행 예정.

### 5.3 코덱스 리뷰 8회에서 막은 잡음

- **A/B 등급 폴드 멤버십 942건 차이**: warm slug JSON과 KFold 학습 슬라이스가 어긋남 → `warm_set` membership으로 통일.
- **Calibration factor leakage in grade margin**: 등급별 m 산출 시 production guarded factor를 그대로 사용 → 통일.
- **`loaded` vs empty dict**: 빈 JSON을 missing으로 처리 → tuple 반환 `(data, loaded)`로 명시적 분리.

---

## 6. 32회 코덱스 리뷰가 막아낸 것

| PR | 리뷰 회차 | 주요 차단 항목 |
|:-:|:-:|---|
| #20 | 15회 | career_stage v1 사문화, 5개 드리프트 피처, gallery_name vocab, eval_set 누수, label_maps fallback, categorical 정규화 비대칭, model_version 정적 |
| #21 | 8회 | in-sample calibration evaluation, cell key parser, schema validation, "True OOS" wording |
| #22 | 8회 | A/B 폴드 멤버십, calibration factor leakage, schema parity, empty artifact 분리 |
| #23·#24 | 1회 | 문서 정합 |

**공통 패턴**: 모델 정확도 그래프엔 안 잡히지만 production에서 **silent하게 다른 패턴을 학습**시킬 train/serve 정합 문제. 32회 리뷰 없이 머지됐다면 metrics는 그대로 38~39%였을 것이고, 운영 중 디버깅 비용이 폭발했을 것.

---

## 7. 최종 production 메트릭 (v3-tuned-cal)

> **측정 절차**: production 코드 경로 그대로 재현. `is_warm_artist`(930 slug JSON), source calibration cold factor, target_market 추론까지 동일.

### 7.1 Warm slice (KFold, 27,062건 / 930 작가, ≥5건)

| 분할 | 모델 | n | MdAPE | W30 | W50 |
|---|---|---:|---:|---:|---:|
| Warm 전체 | XGBoost | 27,062 | **9.7%** | 82.8% | 92.7% |
| Warm 전체 | CatBoost | 27,062 | 11.9% | 80.6% | 92.2% |
| Warm 전체 | 앙상블 | 27,062 | 10.5% | 82.4% | 92.7% |
| Warm Artsy | XGBoost | 6,603 | **8.3%** | 85.9% | 93.9% |
| Warm Artsy | 앙상블 | 6,603 | **8.7%** | 86.3% | 94.1% |
| Warm Saatchi | XGBoost | 20,459 | 10.3% | 81.9% | 92.3% |
| Warm Saatchi | 앙상블 | 20,459 | 11.1% | 81.2% | 92.3% |

**A 등급 8% 목표**: warm Artsy XGB 8.3% / 앙상블 8.7%로 사실상 도달. (A 목표는 "warm Artsy" 슬라이스 정의에서 8.0~9.0% 밴드.)

### 7.2 Cold slice (GroupKFold, 28,376건 / 1,551 작가)

> **production cold path = CatBoost 단일 경로**. 따라서 보정 전후 비교는 CatBoost OOF 기준이며 (`source_calibration.json` `cold_overall`), 앙상블/소스 슬라이스는 offline 비교 참고용이다.

| 분할 | 모델 | n | MdAPE | 비고 |
|---|---|---:|---:|---|
| **Cold 전체 (production path)** | **CatBoost (보정 전)** | 28,376 | **39.4%** | `cold_overall.baseline_mdape=39.38` |
| **Cold 전체 (production path)** | **CatBoost + cell calibration (cross-fit guarded)** | 28,376 | **38.3%** | `cold_overall.calibrated_mdape_cross_fit_guarded=38.29` (-1.09%p) |
| Cold 전체 — offline only | XGBoost | 28,376 | 39.1% | production cold path 아님 |
| Cold 전체 — offline only | 앙상블 | 28,376 | 38.7% | production cold path 아님 |
| Cold Artsy — offline only | 앙상블 | 7,289 | 33.2% | 슬라이스 비교 참고용 |
| Cold Saatchi — offline only | 앙상블 | 21,087 | 41.1% | 슬라이스 비교 참고용 |

### 7.3 Production-time grade MdAPE (전체 28,376)

위 [§5.2](#52-등급-마진-production-time-재캘리브레이션) 표 참조.

---

## 8. 알려진 제약·잔존 협조 사항

본 v2 모델이 **여전히 해결하지 못하는 것**과 후속 협조 필요 항목 ([`docs/협조_필요사항_정리_20260428.md`](협조_필요사항_정리_20260428.md) 전체 12건 중 핵심):

1. **Cold-start MdAPE 38%대 수렴**: 생년 결측 72%, 고가 1,678건(5.7%), 신진 작가 외부 수집 정확도 한계 — 데이터 구조적 한계로 모델만으론 추가 개선 어려움.
2. **DB schema 마이그레이션 (운영 협조)**: `artist_profiles.career_stage`가 INT(1..4) CHECK 제약 — career_stage v2(연속 0~8) 와 충돌. 현재는 학습/서빙이 JSON으로 우회 중.
3. **갤러리 티어 v3 매칭 81% 미해결 (협력자 협조)**: Artsy 갤러리 66개 중 11개만 협력자 리스트와 매칭. Top 30 미매칭 명단(영문명+한글 추정) 검수 필요 — 완료 시 Phase 1B에서 갤러리 등급 신호 회복.
4. **Cold-start 자동 수집 강화 (운영 협조)**: 한국 갤러리 사이트 크롤링 추가, 5단계→7단계 필터로 정확도 향상.
5. **PredictRequest에 optional `gallery_name`/`gallery_type` 추가 + 모델 재학습**: `gallery_name`은 v2 모델에서 **이미 제거**된 상태이므로 API 필드만 추가해도 신호가 살아나지 않는다. 회복하려면 (a) PredictRequest 스키마 추가, (b) feature builder에 `gallery_name` 재도입, (c) 모델 재학습이 모두 필요하다. `gallery_type`은 현재도 모델 입력이지만 서빙 vocab이 좁아 효과 제한적.
6. **m 값 정책 결정**: 권장치 적용 시 C/D는 m≈0.9 — 가격 범위 표시 정책 변경 영향 검토 필요.

---

## 9. 운영 변경 사항 (v1 대비)

### 9.1 모델 아티팩트 5종 (Dockerfile.api COPY 대상)

```
model_test_results/
├── integrated_v3_filtered_tuned_catboost.cbm
├── integrated_v3_filtered_tuned_xgboost.json
├── integrated_v3_filtered_tuned_xgboost_label_maps.json    # mandatory
├── integrated_v3_filtered_tuned_warm_artists.json          # 930 slug
└── integrated_v3_filtered_tuned_source_calibration.json    # cell factor
```

**fail-closed**: 5개 중 1개라도 누락·schema 불일치 시 서버 시작 시점에 `RuntimeError`. v1은 partial 로드 후 잘못된 예측을 침묵으로 반환할 수 있었음 — v2에서 차단.

### 9.2 model_version 동적화

```python
# primary_predictor.py
def model_version_label(self, base: str = "v3-tuned") -> str:
    if self._cold_calibration_factors:
        return f"{base}-cal"   # calibration JSON 로드된 경우만
    return base                # uncalibrated 상태도 거짓 보고하지 않음
```

v1은 하드코딩된 `"v3"` — 모델 업데이트 시 코드 수동 갱신 필요했음. v2는 **실제 로드된 artifact 기반**으로 라벨 산출 (calibration 누락 시 `v3-tuned`, 로드 시 `v3-tuned-cal`).

### 9.3 라우팅 경로 (변경 없음 + 명시화)

```
입력 → ArtistMatcher.match() → slug
       │
       ├─ slug ∈ WARM_ARTIST_SLUGS (930)?
       │   ├─ Yes → XGBoost (32 피처, label-encoded categorical)
       │   └─ No  → CatBoost (32 피처, native categorical)
       │
       └─ predict() 후 cold path만 cell calibration 적용
              (cell = source × target_market, factor JSON 참조)
```

---

## 10. 참고 문서

- v1 본문 (이론·아키텍처·SHAP): [`model_technical_report.html`](model_technical_report.html)
- 액션 플랜 전체 (10 항목): [`MdAPE_개선_액션플랜_20260427.md`](MdAPE_개선_액션플랜_20260427.md)
- PR #20 여정 (15회 리뷰): [`PR20_요약_및_코덱스리뷰_여정_20260428.md`](PR20_요약_및_코덱스리뷰_여정_20260428.md)
- 정확도 종합 리포트: [`예측정확도_종합리포트_20260428.md`](예측정확도_종합리포트_20260428.md)
- 협조 필요 사항: [`협조_필요사항_정리_20260428.md`](협조_필요사항_정리_20260428.md)
- PR 머지 완료: #19, #20, #21, #22, #23, #24

---

## 11. 변경 이력

- **2026-04-28** v2 초안 — career_stage v2, 5개 드리프트 피처 제거, source × target_market 셀 캘리브레이션, 등급 마진 production-time 재산출 반영. 32회 코덱스 리뷰 소화 후 머지된 산출물 기준.
